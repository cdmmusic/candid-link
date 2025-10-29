#!/usr/bin/env python3
"""
24시간 자동 앨범 링크 수집 시스템
- Turso 데이터베이스에서 미수집 앨범 가져오기
- n8n 워크플로우로 자동 전송
- 진행 상황 추적 및 재시도 로직
"""

import requests
import time
import sys
import os
from datetime import datetime
import libsql_experimental as libsql

# Turso 설정
TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

# n8n 웹훅 URL (Docker 내부 네트워크 or 로컬)
WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/album-links')

# 색상 출력
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def get_db_connection():
    """Turso 데이터베이스 연결"""
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise Exception("Turso credentials not found in environment variables")

    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

def get_uncollected_albums(limit=None):
    """수집되지 않은 앨범 목록 가져오기"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # found = 0 또는 NULL인 앨범 중 DISTINCT로 가져오기
    query = '''
        SELECT DISTINCT artist_ko, artist_en, album_ko, album_en
        FROM album_platform_links
        WHERE found = 0 OR found IS NULL
        ORDER BY created_at DESC
    '''

    if limit:
        query += f' LIMIT {limit}'

    cursor.execute(query)

    # 결과를 dict 리스트로 변환
    columns = [desc[0] for desc in cursor.description]
    albums = []
    for row in cursor.fetchall():
        album = dict(zip(columns, row))
        albums.append(album)

    conn.close()
    return albums

def process_album(artist_ko, artist_en, album_ko, album_en, retry=0):
    """개별 앨범을 n8n 워크플로우로 전송"""
    payload = {
        "primary_artist": artist_ko,
        "primary_artist_en": artist_en or "",
        "album_title_ko": album_ko,
        "album_title_en": album_en or ""
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=180)

        if response.status_code == 200:
            result = response.json()
            kr_found = result.get('summary', {}).get('kr_found', 0)
            global_found = result.get('summary', {}).get('global_found', 0)
            return True, kr_found + global_found, None
        else:
            return False, 0, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        if retry < 2:  # 최대 2번 재시도
            print(f"{Colors.WARNING}  ⚠ Timeout, retrying ({retry + 1}/2)...{Colors.ENDC}")
            time.sleep(5)
            return process_album(artist_ko, artist_en, album_ko, album_en, retry + 1)
        return False, 0, "Timeout (3 attempts)"

    except requests.exceptions.ConnectionError:
        return False, 0, "Connection error (n8n not running?)"

    except Exception as e:
        return False, 0, str(e)

def save_progress(current, total, success, fail):
    """진행 상황을 파일에 저장"""
    with open('.collection_progress.txt', 'w') as f:
        f.write(f"{current}/{total}\n")
        f.write(f"Success: {success}\n")
        f.write(f"Failed: {fail}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")

def load_progress():
    """이전 진행 상황 불러오기"""
    try:
        with open('.collection_progress.txt', 'r') as f:
            lines = f.readlines()
            current = int(lines[0].split('/')[0])
            return current
    except:
        return 0

def main():
    """메인 실행"""
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else None

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  24/7 Automatic Album Link Collector")
    print(f"{'='*60}{Colors.ENDC}\n")
    print(f"Turso Database: {TURSO_DATABASE_URL[:50]}...")
    print(f"n8n Webhook: {WEBHOOK_URL}")
    if batch_size:
        print(f"Batch size: {batch_size} albums")
    else:
        print(f"Batch size: ALL albums")
    print()

    # 미수집 앨범 가져오기
    print(f"{Colors.OKCYAN}Fetching uncollected albums from Turso...{Colors.ENDC}")
    albums = get_uncollected_albums(batch_size)
    total = len(albums)

    if total == 0:
        print(f"{Colors.OKGREEN}All albums have been collected!{Colors.ENDC}\n")
        return

    print(f"Found {total} albums to process\n")

    # 이전 진행 상황 확인
    start_idx = load_progress()
    if start_idx > 0:
        print(f"{Colors.WARNING}Resuming from album #{start_idx + 1}{Colors.ENDC}\n")
        albums = albums[start_idx:]

    success_count = 0
    fail_count = 0
    total_platforms = 0
    start_time = datetime.now()

    for idx, album in enumerate(albums, start_idx + 1):
        artist_ko = album['artist_ko']
        artist_en = album.get('artist_en') or ''
        album_ko = album['album_ko']
        album_en = album.get('album_en') or ''

        if not artist_ko or not album_ko:
            print(f"{Colors.WARNING}[{idx}/{total}] Skipping: Missing data{Colors.ENDC}\n")
            fail_count += 1
            continue

        print(f"{Colors.BOLD}[{idx}/{total}] {artist_ko} - {album_ko}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}  → Sending to n8n workflow...{Colors.ENDC}")

        success, platform_count, error = process_album(artist_ko, artist_en, album_ko, album_en)

        if success:
            print(f"{Colors.OKGREEN}  ✓ Success: {platform_count} platforms found{Colors.ENDC}")
            success_count += 1
            total_platforms += platform_count
        else:
            print(f"{Colors.FAIL}  ✗ Failed: {error}{Colors.ENDC}")
            fail_count += 1

        # 진행 상황 저장
        save_progress(idx, total, success_count, fail_count)

        # 통계 출력 (매 10개마다)
        if idx % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = (total - idx) / rate if rate > 0 else 0

            print(f"\n{Colors.OKCYAN}--- Progress: {idx}/{total} ({idx/total*100:.1f}%) ---")
            print(f"Success: {success_count} | Failed: {fail_count}")
            print(f"Rate: {rate*60:.1f} albums/min")
            print(f"ETA: {remaining/3600:.1f} hours{Colors.ENDC}\n")

        # 다음 요청 전 대기
        if idx < total:
            wait_time = 3  # 3초 대기
            time.sleep(wait_time)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  Collection Complete")
    print(f"{'='*60}{Colors.ENDC}\n")
    print(f"Total albums processed: {total}")
    print(f"{Colors.OKGREEN}Success: {success_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {fail_count}{Colors.ENDC}")
    print(f"Total platforms found: {total_platforms}")
    print(f"Duration: {duration/3600:.1f} hours")
    print(f"Average: {duration/total:.1f}s per album\n")

    # 진행 상황 파일 삭제
    if os.path.exists('.collection_progress.txt'):
        os.remove('.collection_progress.txt')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Collection interrupted by user.{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Progress saved. Run again to resume.{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)
