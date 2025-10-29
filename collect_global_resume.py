#!/usr/bin/env python3
"""
글로벌 + 국내 링크 통합 수집 스크립트 (로컬 DB)
- 글로벌: Companion API
- 국내: 멜론/지니/FLO/벅스/VIBE 직접 검색
"""

import sqlite3
import requests
import time
import sys
from datetime import datetime
import os

# 출력 버퍼링 비활성화
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 설정
DB_PATH = '/Users/choejibin/release-album-link/album_links.db'
COMPANION_API_URL = 'http://localhost:5001/search'
START_FROM_ALBUM = None  # None이면 최신부터, 특정 코드 입력하면 그 앨범부터 과거로 수집

# 실패 로그 파일 경로
FAILURE_LOG_DIR = '/Users/choejibin/release-album-link/failure_logs'
os.makedirs(FAILURE_LOG_DIR, exist_ok=True)

# 색상
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_failure(failure_type, album, error_msg='', kr_platforms=None):
    """실패를 로그 파일에 기록"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = os.path.join(FAILURE_LOG_DIR, f'{failure_type}.txt')

    with open(log_file, 'a', encoding='utf-8') as f:
        line = f"[{timestamp}] {album['cdma_code']} | {album['artist_ko']} | {album['album_ko']}"
        if kr_platforms:
            line += f" | KR: {', '.join(kr_platforms.keys())}"
        if error_msg:
            line += f" | {error_msg}"
        f.write(line + '\n')

def parse_kr_platforms_from_api(kr_data):
    """Companion API 응답에서 KR 플랫폼 데이터 파싱"""
    if not kr_data or not isinstance(kr_data, dict):
        return {}

    # API가 반환하는 형식: {'melon': 'url', 'bugs': 'url', ...}
    return kr_data

def get_db_connection():
    """로컬 SQLite 연결"""
    return sqlite3.connect(DB_PATH)

def get_albums_to_collect(start_from_album=None):
    """수집할 앨범 목록 가져오기 (CDMA 역순: 큰 번호→작은 번호)

    수집 대상:
    - Global 미수집 앨범 (found=1인 global 레코드가 0개)
    - 또는 KR 미수집 앨범 (found=1인 kr 레코드가 5개 미만)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT
            a.album_code,
            a.artist_ko,
            a.album_ko,
            a.release_date,
            COUNT(CASE WHEN apl.found = 1 AND apl.platform_type = 'global' THEN 1 END) as global_found,
            COUNT(CASE WHEN apl.found = 1 AND apl.platform_type = 'kr' THEN 1 END) as kr_found
        FROM albums a
        LEFT JOIN album_platform_links apl ON a.artist_ko = apl.artist_ko AND a.album_ko = apl.album_ko
    '''

    if start_from_album:
        query += f" WHERE a.album_code <= '{start_from_album}'"

    query += '''
        GROUP BY a.album_code, a.artist_ko, a.album_ko, a.release_date
        HAVING global_found = 0 OR kr_found < 5
        ORDER BY a.album_code DESC
    '''

    cursor.execute(query)
    albums = cursor.fetchall()
    conn.close()

    return [
        {
            'cdma_code': row[0],
            'artist_ko': row[1],
            'album_ko': row[2],
            'release_date': row[3],
            'global_found': row[4],
            'kr_found': row[5]
        }
        for row in albums
    ]

def collect_global_links(album):
    """Companion API로 글로벌 링크 수집"""
    try:
        response = requests.post(
            COMPANION_API_URL,
            json={
                'artist': album['artist_ko'],
                'album': album['album_ko'],
                'upc': album['cdma_code']
            },
            timeout=120  # 타임아웃 120초 (companion.global 느림)
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result = data.get('data', {})
                error = data.get('error', '')

                # 에러 유형별 로깅
                if error:
                    if 'not found' in error.lower() or '앨범을 찾을 수 없습니다' in error:
                        log_failure('catalog_not_found', album, error)
                    elif 'smart link' in error.lower() and '없습니다' in error:
                        log_failure('smart_link_missing', album, error)
                    elif '500' in error or 'server error' in error.lower():
                        log_failure('smart_link_500_error', album, error)
                    elif 'platform' in error.lower() and '없습니다' in error:
                        log_failure('smart_link_no_platforms', album, error)
                    else:
                        log_failure('other_error', album, error)

                return result if result.get('platforms') else None
            else:
                # success=False인 경우
                error = data.get('error', 'Unknown error')
                log_failure('api_failed', album, error)
                return None

        return None

    except requests.exceptions.Timeout:
        print(f"{Colors.FAIL}  ✗ API 타임아웃{Colors.ENDC}")
        log_failure('api_timeout', album, 'Request timeout (120s)')
        return None
    except Exception as e:
        error_msg = str(e)
        print(f"{Colors.FAIL}  ✗ API 오류: {error_msg}{Colors.ENDC}")
        log_failure('api_exception', album, error_msg)
        return None

def save_kr_links(album, kr_results, album_cover_url=None):
    """국내 링크를 DB에 저장"""
    if not kr_results:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()
    saved_count = 0

    platform_mapping = {
        'melon': '멜론',
        'bugs': '벅스',
        'genie': '지니뮤직',
        'flo': 'FLO',
        'vibe': 'VIBE'
    }

    for code, url in kr_results.items():
        try:
            platform_name = platform_mapping.get(code, code)

            # UPDATE existing record
            if album_cover_url:
                cursor.execute('''
                    UPDATE album_platform_links
                    SET platform_url = ?,
                        found = 1,
                        album_cover_url = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE artist_ko = ? AND album_ko = ?
                      AND platform_type = 'kr'
                      AND platform_name = ?
                ''', (url, album_cover_url, album['artist_ko'], album['album_ko'], platform_name))
            else:
                cursor.execute('''
                    UPDATE album_platform_links
                    SET platform_url = ?,
                        found = 1,
                        created_at = CURRENT_TIMESTAMP
                    WHERE artist_ko = ? AND album_ko = ?
                      AND platform_type = 'kr'
                      AND platform_name = ?
                ''', (url, album['artist_ko'], album['album_ko'], platform_name))

            if cursor.rowcount > 0:
                saved_count += 1

        except Exception as e:
            print(f"{Colors.WARNING}  ⚠ KR DB 저장 오류 ({platform_name}): {e}{Colors.ENDC}")

    conn.commit()
    conn.close()

    return saved_count

def save_global_links(album, platforms_data):
    """글로벌 링크를 DB에 저장"""
    if not platforms_data or not platforms_data.get('platforms'):
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    platforms = platforms_data['platforms']
    album_cover_url = platforms_data.get('album_cover_url', '')
    saved_count = 0

    for platform in platforms:
        try:
            # INSERT OR IGNORE (UNIQUE 인덱스로 중복 방지)
            cursor.execute('''
                INSERT OR IGNORE INTO album_platform_links
                (artist_ko, album_ko, platform_type, platform_name,
                 platform_code, platform_url, found, album_cover_url)
                VALUES (?, ?, 'global', ?, ?, ?, 1, ?)
            ''', (album['artist_ko'], album['album_ko'],
                  platform['platform'], platform['code'],
                  platform['url'], album_cover_url))

            # 삽입되었는지 확인 (rowcount > 0이면 새로 삽입)
            if cursor.rowcount > 0:
                saved_count += 1

        except Exception as e:
            print(f"{Colors.WARNING}  ⚠ DB 저장 오류 ({platform['platform']}): {e}{Colors.ENDC}")

    conn.commit()
    conn.close()

    return saved_count

def main():
    """메인 실행"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  글로벌 + 국내 링크 수집 [{current_time}]")
    if START_FROM_ALBUM:
        print(f"  시작 지점: {START_FROM_ALBUM} 이하 (역순)")
    else:
        print(f"  시작 지점: 최신 앨범부터 (역순)")
    print(f"{'='*60}{Colors.ENDC}\n")

    # 수집할 앨범 가져오기
    albums = get_albums_to_collect(START_FROM_ALBUM)
    total = len(albums)

    print(f"{Colors.OKCYAN}수집할 앨범: {total}개{Colors.ENDC}\n")

    if total == 0:
        print(f"{Colors.OKGREEN}✓ 모든 앨범 수집 완료!{Colors.ENDC}")
        return

    # 수집 시작
    global_success = 0
    kr_success = 0
    skipped = 0
    global_failed = 0
    kr_only_partial = 0

    for idx, album in enumerate(albums, 1):
        print(f"{Colors.BOLD}[{idx}/{total}]{Colors.ENDC} {album['artist_ko']} - {album['album_ko']}")
        print(f"  코드: {album['cdma_code']} | 발매일: {album['release_date']}")

        # 이미 수집 완료 확인
        already_global = album.get('global_found', 0) > 0
        already_kr = album.get('kr_found', 0) >= 5

        if already_global and already_kr:
            print(f"{Colors.OKCYAN}  ⊙ 이미 수집 완료 (Global: ✓, KR: {album['kr_found']}/5){Colors.ENDC}")
            skipped += 1
            print()
            continue

        # Companion API 호출 (글로벌 + 국내 통합)
        result = collect_global_links(album)

        # 1. KR 플랫폼 저장 (5개 미만인 경우에만)
        kr_platforms = result.get('kr_platforms', {}) if result else {}
        kr_cover = result.get('album_cover_url', '') if result else ''

        if not already_kr and kr_platforms:
            kr_saved = save_kr_links(album, kr_platforms, kr_cover)
            if kr_saved > 0:
                total_kr = album.get('kr_found', 0) + kr_saved
                cover_info = f" + 커버" if kr_cover else ""
                print(f"{Colors.OKBLUE}  ✓ KR {kr_saved}개 저장 (총 {total_kr}/5): {', '.join(kr_platforms.keys())}{cover_info}{Colors.ENDC}")
                kr_success += 1
        elif already_kr:
            print(f"{Colors.OKCYAN}  ⊙ KR 이미 완료 ({album['kr_found']}/5){Colors.ENDC}")

        # KR 일부만 찾은 경우 로깅
        if kr_platforms and len(kr_platforms) < 5:
            kr_only_partial += 1
            log_failure('kr_partial', album, f"Found {len(kr_platforms)}/5 platforms", kr_platforms)

        # 2. Global 플랫폼 저장 (미수집인 경우에만)
        if not already_global:
            if result and result.get('platforms'):
                platform_count = len(result['platforms'])
                saved = save_global_links(album, result)

                if saved > 0:
                    platforms_list = ', '.join([p['platform'] for p in result['platforms'][:5]])
                    if platform_count > 5:
                        platforms_list += ' ...'

                    print(f"{Colors.OKGREEN}  ✓ Global {saved}개: {platforms_list}{Colors.ENDC}")
                    global_success += 1
                else:
                    print(f"{Colors.OKCYAN}  ⊙ Global 이미 저장됨{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}  ✗ Global 없음{Colors.ENDC}")
                global_failed += 1
                log_failure('global_not_found', album, 'No global platforms found', kr_platforms)
        else:
            print(f"{Colors.OKCYAN}  ⊙ Global 이미 완료{Colors.ENDC}")

        print()  # 빈 줄

        # 진행률 표시 (10개마다)
        if idx % 10 == 0:
            progress_pct = idx*100//total if total > 0 else 0
            print(f"{Colors.OKCYAN}━━━ 진행률: {idx}/{total} ({progress_pct}%) ━━━{Colors.ENDC}")
            print(f"  KR 신규: {kr_success} | Global 신규: {global_success}")
            print(f"  건너뜀: {skipped} | KR 일부: {kr_only_partial} | Global 실패: {global_failed}\n")

        # API 과부하 방지
        time.sleep(1)

    # 최종 결과
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}{'='*60}")
    print(f"  수집 완료! [{end_time}]")
    print(f"{'='*60}{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}✓ KR 신규 수집: {kr_success}개{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}✓ Global 신규 수집: {global_success}개{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}⊙ 이미 완료: {skipped}개{Colors.ENDC}")
    print(f"  {Colors.WARNING}⚠ KR 일부만: {kr_only_partial}개{Colors.ENDC}")
    print(f"  {Colors.FAIL}✗ Global 실패: {global_failed}개{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")

    # 실패 로그 요약
    print(f"\n{Colors.OKCYAN}━━━ 실패 로그 저장 위치: {FAILURE_LOG_DIR} ━━━{Colors.ENDC}")
    failure_files = {
        'kr_partial.txt': 'KR 일부만 찾음',
        'global_not_found.txt': 'Global 플랫폼 없음',
        'catalog_not_found.txt': 'Catalog에서 앨범 못 찾음',
        'smart_link_missing.txt': 'Smart Link 없음',
        'smart_link_500_error.txt': 'Smart Link 500 에러',
        'smart_link_no_platforms.txt': 'Smart Link에 플랫폼 없음',
        'api_timeout.txt': 'API 타임아웃',
        'api_failed.txt': 'API 실패',
        'api_exception.txt': 'API 예외',
        'other_error.txt': '기타 오류'
    }

    has_failures = False
    for filename, description in failure_files.items():
        filepath = os.path.join(FAILURE_LOG_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                count = len(f.readlines())
            if count > 0:
                has_failures = True
                print(f"  - {description}: {count}건 ({filename})")

    if not has_failures:
        print(f"  {Colors.OKGREEN}✓ 실패 없음!{Colors.ENDC}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}사용자가 중단했습니다.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}오류 발생: {str(e)}{Colors.ENDC}")
        sys.exit(1)
