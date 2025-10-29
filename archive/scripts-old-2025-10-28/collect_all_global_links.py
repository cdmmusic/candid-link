#!/usr/bin/env python3
"""
글로벌 링크가 없는 앨범의 링크를 Companion.global에서 수집
- 로컬 SQLite 데이터베이스 사용
- Companion API (localhost:5001) 사용
- 글로벌 링크가 없는 앨범만 수집
"""

import sqlite3
import requests
import time
import sys
from datetime import datetime

DB_PATH = 'album_links.db'
COMPANION_API_URL = 'http://localhost:5001'

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
    """로컬 SQLite 데이터베이스 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_albums(limit=None):
    """글로벌 링크가 없는 발매된 앨범 가져오기"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT a.artist_ko, a.album_ko, a.album_code, a.release_date
        FROM albums a
        WHERE a.album_code LIKE 'CDMA%'
          AND datetime(a.release_date) <= datetime('now')
          AND NOT EXISTS (
              SELECT 1 FROM album_platform_links apl
              WHERE apl.artist_ko = a.artist_ko
                AND apl.album_ko = a.album_ko
                AND apl.platform_type = 'global'
                AND apl.found = 1
          )
        ORDER BY a.release_date DESC
    '''

    if limit:
        query += f' LIMIT {limit}'

    cursor.execute(query)
    albums = cursor.fetchall()
    conn.close()

    return albums

def save_global_links(artist_ko, album_ko, platforms):
    """글로벌 플랫폼 링크를 데이터베이스에 저장"""
    conn = get_db_connection()
    cursor = conn.cursor()

    for platform in platforms:
        cursor.execute('''
            INSERT OR REPLACE INTO album_platform_links
            (artist_ko, album_ko, platform_code, platform_name, platform_url, platform_type, found)
            VALUES (?, ?, ?, ?, ?, 'global', 1)
        ''', (
            artist_ko,
            album_ko,
            platform['code'],
            platform['platform'],
            platform['url']
        ))

    conn.commit()
    conn.close()

def collect_global_links(artist_ko, album_ko, cdma_code):
    """Companion API로 글로벌 링크 수집"""
    try:
        response = requests.post(
            f'{COMPANION_API_URL}/search',
            json={
                'artist': artist_ko,
                'album': album_ko,
                'upc': cdma_code
            },
            timeout=120
        )

        result = response.json()

        if result.get('success') and result.get('data'):
            platforms = result['data'].get('platforms', [])
            return platforms
        else:
            return []

    except Exception as e:
        print(f"{Colors.FAIL}  ✗ API 에러: {str(e)[:50]}{Colors.ENDC}")
        return None

def main():
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  글로벌 링크 수집 (링크 없는 앨범만)")
    print("  Companion.global API 사용")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    # 인자로 limit 받기
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    print(f"{Colors.OKCYAN}수집 대상: {'글로벌 링크가 없는 모든 앨범' if not limit else f'글로벌 링크가 없는 {limit}개 앨범'}{Colors.ENDC}")
    print()
    sys.stdout.flush()  # 즉시 출력

    # Companion API 확인
    try:
        health = requests.get(f'{COMPANION_API_URL}/health', timeout=5).json()
        print(f"{Colors.OKGREEN}✓ Companion API 연결 성공{Colors.ENDC}")
        print(f"  Selenium Hub: {health.get('selenium_hub')}")
    except:
        print(f"{Colors.FAIL}✗ Companion API에 연결할 수 없습니다 (localhost:5001){Colors.ENDC}")
        print(f"  먼저 Companion API를 실행하세요: python3 companion_api.py")
        sys.exit(1)

    print()

    # 앨범 목록 가져오기
    print(f"{Colors.OKCYAN}앨범 목록 조회 중...{Colors.ENDC}")
    albums = get_all_albums(limit)
    total = len(albums)

    print(f"{Colors.OKGREEN}✓ {total}개 앨범 발견{Colors.ENDC}")
    print()

    # 통계
    success_count = 0
    fail_count = 0
    empty_count = 0
    total_platforms = 0

    start_time = time.time()

    # 수집 시작
    for idx, album in enumerate(albums, 1):
        artist_ko = album['artist_ko']
        album_ko = album['album_ko']
        cdma_code = album['album_code']
        release_date = album['release_date'][:10] if album['release_date'] else 'N/A'

        print(f"{Colors.BOLD}[{idx}/{total}]{Colors.ENDC} {artist_ko} - {album_ko}")
        print(f"  코드: {cdma_code} | 발매일: {release_date}")

        # 수집
        platforms = collect_global_links(artist_ko, album_ko, cdma_code)

        if platforms is None:
            # API 에러
            fail_count += 1
            print()
            continue

        if len(platforms) == 0:
            # 플랫폼 없음
            print(f"{Colors.WARNING}  ⚠ 플랫폼 없음{Colors.ENDC}")
            empty_count += 1
        else:
            # 수집 성공
            print(f"{Colors.OKGREEN}  ✓ {len(platforms)}개 플랫폼 수집{Colors.ENDC}")

            # 데이터베이스 저장
            save_global_links(artist_ko, album_ko, platforms)

            success_count += 1
            total_platforms += len(platforms)

            # 플랫폼 목록 출력
            platform_names = [p['platform'] for p in platforms]
            print(f"    {', '.join(platform_names[:5])}{' ...' if len(platform_names) > 5 else ''}")

        print()

        # 진행 상황 출력 (매 10개마다)
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            remaining = (total - idx) * avg_time

            print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
            print(f"{Colors.OKCYAN}진행: {idx}/{total} ({idx*100//total}%){Colors.ENDC}")
            print(f"{Colors.OKCYAN}성공: {success_count} | 실패: {fail_count} | 플랫폼 없음: {empty_count}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}예상 남은 시간: {int(remaining//60)}분 {int(remaining%60)}초{Colors.ENDC}")
            print(f"{Colors.OKCYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.ENDC}")
            print()

    # 최종 결과
    total_time = time.time() - start_time

    print()
    print(f"{Colors.BOLD}{Colors.OKGREEN}")
    print("=" * 70)
    print("  수집 완료")
    print("=" * 70)
    print(f"{Colors.ENDC}")

    print(f"전체 앨범: {total}개")
    print(f"수집 성공: {success_count}개 ({total_platforms}개 플랫폼)")
    print(f"플랫폼 없음: {empty_count}개")
    print(f"수집 실패: {fail_count}개")
    print(f"소요 시간: {int(total_time//60)}분 {int(total_time%60)}초")
    print()

    if success_count > 0:
        print(f"{Colors.OKGREEN}✓ 데이터가 로컬 데이터베이스에 저장되었습니다{Colors.ENDC}")
        print(f"  다음 명령어로 Turso에 동기화하세요:")
        print(f"  {Colors.OKCYAN}python3 sync_to_turso.py{Colors.ENDC}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}✗ 사용자가 중단했습니다{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}✗ 오류 발생: {e}{Colors.ENDC}")
        sys.exit(1)
