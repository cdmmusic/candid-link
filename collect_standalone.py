#!/usr/bin/env python3
"""
독립형 앨범 링크 수집 스크립트 (n8n 불필요)
- Turso 데이터베이스에서 미수집 앨범 가져오기
- 한국 플랫폼 (멜론, 지니, 벅스, VIBE, FLO) API 직접 호출
- Companion.global에서 해외 플랫폼 링크 수집 (선택)
- 진행 상황 추적 및 재시도 로직
"""

import requests
import time
import sys
import os
from datetime import datetime
from urllib.parse import quote
import json

# Turso 설정
try:
    import libsql_experimental as libsql
    USE_TURSO = True
except ImportError:
    print("Warning: libsql not found. Please install: pip install libsql-experimental")
    sys.exit(1)

TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

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

# ============================================================
# 한국 플랫폼 검색 함수들
# ============================================================

def search_melon(artist, album):
    """멜론 검색"""
    try:
        # 멜론 API (웹 크롤링 or 공개 API 없음, 직접 URL 패턴 사용)
        # 실제로는 검색 API가 막혀있어서 우회 방법 필요
        search_url = f"https://www.melon.com/search/album/index.htm?q={quote(artist + ' ' + album)}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            # 실제로는 HTML 파싱 필요 (BeautifulSoup 등)
            # 여기서는 간단히 URL만 반환
            return {
                'found': False,  # 실제 구현 필요
                'url': search_url,
                'album_id': None
            }
    except Exception as e:
        print(f"  Melon error: {str(e)}")

    return {'found': False, 'url': None, 'album_id': None}

def search_genie(artist, album):
    """지니뮤직 검색"""
    try:
        search_query = f"{artist} {album}"
        search_url = f"https://www.genie.co.kr/search/searchMain?query={quote(search_query)}"

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            return {
                'found': False,  # 실제 구현 필요
                'url': search_url,
                'album_id': None
            }
    except Exception as e:
        print(f"  Genie error: {str(e)}")

    return {'found': False, 'url': None, 'album_id': None}

def search_bugs(artist, album):
    """벅스 검색"""
    try:
        # Bugs API는 비교적 접근 가능
        search_query = f"{artist} {album}"
        search_url = f"https://music.bugs.co.kr/search/album?q={quote(search_query)}"

        headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            return {
                'found': False,  # 실제 구현 필요
                'url': search_url,
                'album_id': None
            }
    except Exception as e:
        print(f"  Bugs error: {str(e)}")

    return {'found': False, 'url': None, 'album_id': None}

def search_vibe(artist, album):
    """VIBE 검색 (Naver API 사용)"""
    try:
        search_query = f"{artist} {album}"
        # VIBE API - v3 버전 사용
        api_url = "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v3/search"
        params = {
            'query': search_query
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://vibe.naver.com/',
            'Origin': 'https://vibe.naver.com'
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            try:
                data = response.json()
                # albums 배열 찾기
                albums = data.get('response', {}).get('result', {}).get('album', {}).get('list', [])

                if not albums:
                    # 다른 구조 시도
                    albums = data.get('response', {}).get('result', {}).get('albums', [])

                if albums and len(albums) > 0:
                    first_album = albums[0]
                    album_id = first_album.get('albumId')
                    album_url = f"https://vibe.naver.com/album/{album_id}" if album_id else None

                    return {
                        'found': True,
                        'url': album_url,
                        'album_id': str(album_id)
                    }
            except (ValueError, KeyError) as e:
                pass

    except Exception as e:
        pass

    return {'found': False, 'url': None, 'album_id': None}

def search_flo(artist, album):
    """FLO 검색"""
    try:
        search_query = f"{artist} {album}"
        # FLO API
        api_url = "https://www.music-flo.com/api/search/v2/search"
        params = {
            'keyword': search_query,
            'searchType': 'ALBUM',
            'sortType': 'ACCURACY',
            'size': 20,
            'page': 1
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            try:
                data = response.json()
                albums = data.get('data', {}).get('list', [])

                if albums and len(albums) > 0:
                    first_album = albums[0]
                    album_id = first_album.get('id')

                    if album_id:
                        album_url = f"https://www.music-flo.com/detail/album/{album_id}"
                        return {
                            'found': True,
                            'url': album_url,
                            'album_id': str(album_id)
                        }
            except (ValueError, KeyError):
                pass

    except Exception as e:
        pass

    return {'found': False, 'url': None, 'album_id': None}

# ============================================================
# 해외 플랫폼 검색
# ============================================================

def search_global_platforms_via_companion(artist, album, companion_api_url="http://localhost:5001"):
    """
    Companion API를 통해 해외 플랫폼 검색
    companion_api_url: Companion API 서버 주소 (기본: http://localhost:5001)
    """
    try:
        response = requests.post(
            f"{companion_api_url}/search",
            json={'artist': artist, 'album': album},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                platforms = result.get('data', {}).get('platforms', [])
                album_cover_url = result.get('data', {}).get('album_cover_url')

                return {
                    'success': True,
                    'platforms': platforms,
                    'album_cover_url': album_cover_url
                }

        return {'success': False, 'platforms': [], 'album_cover_url': None}

    except requests.exceptions.ConnectionError:
        print(f"  {Colors.WARNING}Companion API not available (is it running?){Colors.ENDC}")
        return {'success': False, 'platforms': [], 'album_cover_url': None}
    except Exception as e:
        print(f"  Companion API error: {str(e)}")
        return {'success': False, 'platforms': [], 'album_cover_url': None}

def search_global_platforms_simple(artist, album):
    """
    간단한 해외 플랫폼 검색 (Selenium 없이)
    주요 플랫폼의 공개 API나 검색 URL 사용
    """
    platforms = []

    # Spotify (검색 URL만)
    spotify_search_url = f"https://open.spotify.com/search/{quote(artist + ' ' + album)}"
    platforms.append({
        'platform': 'Spotify',
        'code': 'spo',
        'url': spotify_search_url,
        'upc': None
    })

    # Apple Music (검색 URL만)
    apple_search_url = f"https://music.apple.com/search?term={quote(artist + ' ' + album)}"
    platforms.append({
        'platform': 'Apple Music',
        'code': 'itm',
        'url': apple_search_url,
        'upc': None
    })

    # YouTube Music (검색 URL만)
    youtube_search_url = f"https://music.youtube.com/search?q={quote(artist + ' ' + album)}"
    platforms.append({
        'platform': 'YouTube Music',
        'code': 'yat',
        'url': youtube_search_url,
        'upc': None
    })

    return {
        'success': True,
        'platforms': platforms,
        'album_cover_url': None
    }

# ============================================================
# 데이터베이스 저장
# ============================================================

def save_platform_links(artist_ko, artist_en, album_ko, album_en, platforms_data, album_cover_url=None):
    """플랫폼 링크를 Turso DB에 저장"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        saved_count = 0

        for platform in platforms_data:
            platform_type = platform.get('type')  # 'kr' or 'global'
            platform_id = platform.get('platform_id')
            platform_code = platform.get('platform_code') or platform.get('code')
            platform_name = platform.get('name') or platform.get('platform')
            platform_url = platform.get('url')
            album_id = platform.get('album_id')
            upc = platform.get('upc')
            found = 1 if platform.get('found') else 0

            # 기존 레코드 삭제 후 삽입 (중복 방지)
            if platform_type == 'kr':
                cursor.execute('''
                    DELETE FROM album_platform_links
                    WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'kr' AND platform_id = ?
                ''', (artist_ko, album_ko, platform_id))

                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type, platform_id,
                     platform_name, platform_url, album_id, album_cover_url, found, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko, artist_en, album_ko, album_en,
                    'kr', platform_id, platform_name, platform_url, album_id, album_cover_url, found
                ))
                saved_count += 1

            elif platform_type == 'global':
                cursor.execute('''
                    DELETE FROM album_platform_links
                    WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'global' AND platform_code = ?
                ''', (artist_ko, album_ko, platform_code))

                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type, platform_code,
                     platform_name, platform_url, upc, album_cover_url, found, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko, artist_en, album_ko, album_en,
                    'global', platform_code, platform_name, platform_url, upc, album_cover_url, found
                ))
                saved_count += 1

        conn.commit()
        conn.close()

        return saved_count
    except Exception as e:
        print(f"  DB Save error: {str(e)}")
        return 0

# ============================================================
# 메인 수집 프로세스
# ============================================================

def process_album(artist_ko, artist_en, album_ko, album_en, include_global=True):
    """개별 앨범 처리 - 한국 + 해외 플랫폼"""
    print(f"{Colors.OKCYAN}  → Searching Korean platforms...{Colors.ENDC}")

    platforms_data = []
    kr_found_count = 0
    album_cover_url = None

    # 멜론
    print("    [1/5] Melon...", end=" ")
    melon_result = search_melon(artist_ko, album_ko)
    platforms_data.append({
        'type': 'kr',
        'platform_id': 'melon',
        'name': '멜론',
        **melon_result
    })
    if melon_result['found']:
        print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
        kr_found_count += 1
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC}")

    # 지니
    print("    [2/5] Genie...", end=" ")
    genie_result = search_genie(artist_ko, album_ko)
    platforms_data.append({
        'type': 'kr',
        'platform_id': 'genie',
        'name': '지니뮤직',
        **genie_result
    })
    if genie_result['found']:
        print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
        kr_found_count += 1
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC}")

    # 벅스
    print("    [3/5] Bugs...", end=" ")
    bugs_result = search_bugs(artist_ko, album_ko)
    platforms_data.append({
        'type': 'kr',
        'platform_id': 'bugs',
        'name': '벅스',
        **bugs_result
    })
    if bugs_result['found']:
        print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
        kr_found_count += 1
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC}")

    # VIBE
    print("    [4/5] VIBE...", end=" ")
    vibe_result = search_vibe(artist_ko, album_ko)
    platforms_data.append({
        'type': 'kr',
        'platform_id': 'vibe',
        'name': 'VIBE',
        **vibe_result
    })
    if vibe_result['found']:
        print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
        kr_found_count += 1
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC}")

    # FLO
    print("    [5/5] FLO...", end=" ")
    flo_result = search_flo(artist_ko, album_ko)
    platforms_data.append({
        'type': 'kr',
        'platform_id': 'flo',
        'name': 'FLO',
        **flo_result
    })
    if flo_result['found']:
        print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
        kr_found_count += 1
    else:
        print(f"{Colors.FAIL}✗{Colors.ENDC}")

    # 해외 플랫폼 검색
    global_found_count = 0
    if include_global:
        print(f"{Colors.OKCYAN}  → Searching Global platforms...{Colors.ENDC}")

        # Companion API 시도
        search_name = artist_en if artist_en else artist_ko
        search_album = album_en if album_en else album_ko

        global_result = search_global_platforms_via_companion(search_name, search_album)

        if global_result['success'] and global_result['platforms']:
            print(f"    Companion API: {Colors.OKGREEN}✓ Found {len(global_result['platforms'])} platforms{Colors.ENDC}")

            # 해외 플랫폼 추가
            for platform in global_result['platforms']:
                platforms_data.append({
                    'type': 'global',
                    'found': True,
                    **platform
                })
                global_found_count += 1

            # 앨범 커버 URL
            if global_result['album_cover_url']:
                album_cover_url = global_result['album_cover_url']
        else:
            # Companion API 실패 시 간단한 검색 URL만 저장
            print(f"    {Colors.WARNING}Using fallback (search URLs only){Colors.ENDC}")
            simple_result = search_global_platforms_simple(search_name, search_album)

            for platform in simple_result['platforms']:
                platforms_data.append({
                    'type': 'global',
                    'found': False,  # 검색 URL만 있음
                    **platform
                })

    # DB 저장
    saved_count = save_platform_links(artist_ko, artist_en, album_ko, album_en, platforms_data, album_cover_url)

    total_found = kr_found_count + global_found_count
    return kr_found_count, global_found_count, total_found, saved_count

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
    print(f"  Standalone Album Link Collector")
    print(f"  (No n8n Required)")
    print(f"{'='*60}{Colors.ENDC}\n")
    print(f"Turso Database: {TURSO_DATABASE_URL[:50]}...")
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
    total_found = 0
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

        try:
            kr_found, global_found, total_plat_found, saved_count = process_album(artist_ko, artist_en, album_ko, album_en)

            print(f"{Colors.OKGREEN}  ✓ Success: KR {kr_found}/5, Global {global_found}, Total {saved_count} records saved{Colors.ENDC}")
            success_count += 1
            total_found += total_plat_found
        except Exception as e:
            print(f"{Colors.FAIL}  ✗ Failed: {str(e)}{Colors.ENDC}")
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
            wait_time = 2  # 2초 대기
            time.sleep(wait_time)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  Collection Complete")
    print(f"{'='*60}{Colors.ENDC}\n")
    print(f"Total albums processed: {total}")
    print(f"{Colors.OKGREEN}Success: {success_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {fail_count}{Colors.ENDC}")
    print(f"Total platforms found: {total_found}")
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
