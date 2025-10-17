#!/usr/bin/env python3
"""
데이터베이스 기반 앨범 링크 수집
- CDMA 코드로 albums 테이블 조회
- 한국/글로벌 플랫폼 링크 수집
- album_platform_links 테이블에 저장
"""

import requests
import time
import sys
import os
import re
from datetime import datetime
from urllib.parse import quote
import json

# Turso 설정
try:
    import libsql_experimental as libsql
except ImportError:
    print("Error: libsql not found. Please install: pip install libsql-experimental")
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

def get_albums_by_cdma_codes(cdma_codes):
    """CDMA 코드로 albums 테이블에서 앨범 정보 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    albums = []
    for code in cdma_codes:
        cursor.execute('''
            SELECT album_code, artist_ko, artist_en, album_ko, album_en, release_date
            FROM albums
            WHERE album_code = ?
        ''', (code,))

        row = cursor.fetchone()
        if row:
            albums.append({
                'album_code': row[0],
                'artist_ko': row[1],
                'artist_en': row[2],
                'album_ko': row[3],
                'album_en': row[4],
                'release_date': row[5]
            })
        else:
            print(f"{Colors.WARNING}⚠️  CDMA {code}: Not found in database{Colors.ENDC}")

    conn.close()
    return albums

def normalize_text(text):
    """아티스트명/앨범명 정규화"""
    return text.lower().replace(' ', '').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('-', '').replace('_', '')

def search_korean_platforms(artist, album):
    """한국 플랫폼 검색"""
    query = f"{artist} {album}"
    encoded = quote(query)

    cache_buster = f"{int(time.time() * 1000)}_{os.urandom(4).hex()}"

    platforms = [
        {
            'id': 'melon',
            'name': '멜론',
            'searchUrl': f"https://www.melon.com/search/album/index.htm?q={encoded}&section=&searchGnbYn=Y&kkoSpl=Y&kkoDpType=&_={cache_buster}",
            'useApi': False
        },
        {
            'id': 'genie',
            'name': '지니뮤직',
            'searchUrl': f"https://www.genie.co.kr/search/searchAlbum?query={encoded}&_={cache_buster}",
            'useApi': False
        },
        {
            'id': 'bugs',
            'name': '벅스',
            'searchUrl': f"https://music.bugs.co.kr/search/integrated?q={encoded}&_={cache_buster}",
            'useApi': False
        },
        {
            'id': 'vibe',
            'name': 'VIBE',
            'searchUrl': f"https://apis.naver.com/vibeWeb/musicapiweb/v4/searchall?query={encoded}&sort=RELEVANCE&alDisplay=21",
            'useApi': True
        },
        {
            'id': 'flo',
            'name': 'FLO',
            'searchUrl': f"https://www.music-flo.com/api/search/v2/search?keyword={encoded}&searchType=ALBUM&sortType=ACCURACY&size=20&page=1",
            'useApi': True
        }
    ]

    results = []

    for platform in platforms:
        platform_id = platform['id']
        print(f"    [{platform_id}] ", end='', flush=True)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Referer': 'https://vibe.naver.com/',
                'Origin': 'https://vibe.naver.com'
            }

            response = requests.get(platform['searchUrl'], headers=headers, timeout=15)

            if response.status_code == 200:
                result = parse_platform_response(
                    platform_id=platform_id,
                    platform_name=platform['name'],
                    response_data=response.text,
                    use_api=platform['useApi'],
                    target_artist=artist,
                    target_album=album
                )

                results.append(result)

                if result['found']:
                    print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}✗{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}✗ (HTTP {response.status_code}){Colors.ENDC}")
                results.append({
                    'platform_id': platform_id,
                    'platform_name': platform['name'],
                    'found': False,
                    'album_url': None,
                    'album_id': None
                })

        except Exception as e:
            print(f"{Colors.FAIL}✗ ({str(e)[:20]}){Colors.ENDC}")
            results.append({
                'platform_id': platform_id,
                'platform_name': platform['name'],
                'found': False,
                'album_url': None,
                'album_id': None
            })

        time.sleep(0.5)

    return results

def parse_platform_response(platform_id, platform_name, response_data, use_api, target_artist, target_album):
    """플랫폼 응답 파싱"""
    album_url = None
    album_id = None

    if use_api and (platform_id == 'flo' or platform_id == 'vibe'):
        try:
            json_data = json.loads(response_data)

            if platform_id == 'flo':
                if 'data' in json_data and 'list' in json_data['data']:
                    data_list = json_data['data']['list']
                    if len(data_list) > 0:
                        album_list = data_list[0]
                        if album_list.get('type') == 'ALBUM' and 'list' in album_list:
                            items = album_list['list']
                            if len(items) > 0:
                                first_album = items[0]
                                album_id = str(first_album.get('id', ''))
                                if album_id:
                                    album_url = f"https://www.music-flo.com/detail/album/{album_id}"

            elif platform_id == 'vibe':
                if 'response' in json_data and 'result' in json_data['response']:
                    result = json_data['response']['result']
                    if 'trackResult' in result and 'tracks' in result['trackResult']:
                        tracks = result['trackResult']['tracks']
                        if len(tracks) > 0:
                            first_track = tracks[0]
                            if 'album' in first_track:
                                album_id = str(first_track['album'].get('albumId', ''))
                                if album_id:
                                    album_url = f"https://vibe.naver.com/album/{album_id}"

        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    else:
        html = response_data

        if len(html) < 1000:
            return {
                'platform_id': platform_id,
                'platform_name': platform_name,
                'found': False,
                'album_url': None,
                'album_id': None,
                'error': 'Invalid response'
            }

        if platform_id == 'melon':
            patterns = [
                r"goAlbumDetail\(['\"]([0-9]+)['\"]\)",
                r"albumId=([0-9]+)"
            ]

            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    album_id = match.group(1)
                    album_url = f"https://www.melon.com/album/detail.htm?albumId={album_id}"
                    break

        elif platform_id == 'genie':
            normalized_artist = normalize_text(target_artist)
            normalized_album = normalize_text(target_album)

            pattern = r"fnViewAlbumLayer\(['\"]?([0-9]+)['\"]?\)"
            all_matches = []

            for match in re.finditer(pattern, html):
                album_id_candidate = match.group(1)
                start_pos = max(0, match.start() - 500)
                end_pos = min(len(html), match.end() + 500)
                context = html[start_pos:end_pos]
                all_matches.append({'id': album_id_candidate, 'context': context})

            for item in all_matches:
                context_normalized = normalize_text(item['context'])
                has_artist = normalized_artist in context_normalized
                has_album = normalized_album in context_normalized

                if has_artist and has_album:
                    album_id = item['id']
                    album_url = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"
                    break

                if not album_id and has_artist:
                    album_id = item['id']
                    album_url = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"

            if not album_id and len(all_matches) > 0:
                album_id = all_matches[0]['id']
                album_url = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"

        elif platform_id == 'bugs':
            normalized_artist = normalize_text(target_artist)
            normalized_album = normalize_text(target_album)

            pattern = r"/album/(\d+)"
            all_matches = []

            for match in re.finditer(pattern, html):
                album_id_candidate = match.group(1)
                start_pos = max(0, match.start() - 500)
                end_pos = min(len(html), match.end() + 500)
                context = html[start_pos:end_pos]
                all_matches.append({'id': album_id_candidate, 'context': context})

            for item in all_matches:
                context_normalized = normalize_text(item['context'])
                has_artist = normalized_artist in context_normalized
                has_album = normalized_album in context_normalized

                if has_artist and has_album:
                    album_id = item['id']
                    album_url = f"https://music.bugs.co.kr/album/{album_id}"
                    break

                if not album_id and has_artist:
                    album_id = item['id']
                    album_url = f"https://music.bugs.co.kr/album/{album_id}"

            if not album_id and len(all_matches) > 0:
                album_id = all_matches[0]['id']
                album_url = f"https://music.bugs.co.kr/album/{album_id}"

    return {
        'platform_id': platform_id,
        'platform_name': platform_name,
        'artist': target_artist,
        'album': target_album,
        'album_url': album_url,
        'album_id': album_id,
        'found': bool(album_url),
        'status': 'success' if album_url else 'not_found'
    }

def search_global_platforms_via_companion(artist, album):
    """Companion API 호출"""
    companion_api_port = os.environ.get('COMPANION_API_PORT', '8001')
    companion_api_url = f"http://localhost:{companion_api_port}"

    try:
        response = requests.post(
            f"{companion_api_url}/search",
            json={'artist': artist, 'album': album},
            timeout=90
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                platforms = result.get('data', {}).get('platforms', [])
                album_cover_url = result.get('data', {}).get('album_cover_url')

                platforms_dict = {}
                for platform in platforms:
                    platforms_dict[platform['code']] = {
                        'name': platform['platform'],
                        'url': platform['url'],
                        'upc': platform.get('upc'),
                        'found': True
                    }

                return {
                    'success': True,
                    'platforms': platforms_dict,
                    'album_cover_url': album_cover_url,
                    'count': len(platforms)
                }

        return {'success': False, 'platforms': {}, 'album_cover_url': None, 'count': 0}

    except requests.exceptions.ConnectionError:
        print(f"  {Colors.WARNING}Companion API not available (해외 플랫폼 스킵){Colors.ENDC}")
        return {'success': False, 'platforms': {}, 'album_cover_url': None, 'count': 0}
    except Exception as e:
        return {'success': False, 'platforms': {}, 'album_cover_url': None, 'count': 0}

def save_to_database(album_code, artist_ko, artist_en, album_ko, album_en, release_date, kr_platforms, global_platforms, album_cover_url):
    """album_platform_links 테이블에 저장"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 기존 레코드 삭제 (CDMA 코드 기준)
        cursor.execute('''
            DELETE FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
        ''', (artist_ko, album_ko))

        saved_count = 0

        # 한국 플랫폼 저장
        for platform_id, data in kr_platforms.items():
            cursor.execute('''
                INSERT INTO album_platform_links
                (artist_ko, artist_en, album_ko, album_en, platform_type, platform_id,
                 platform_name, platform_url, album_id, album_cover_url, release_date, found, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                artist_ko, artist_en, album_ko, album_en,
                'kr', platform_id, data['platform_name'], data.get('album_url'),
                data.get('album_id'), album_cover_url, release_date,
                1 if data['found'] else 0, data.get('status', '')
            ))
            saved_count += 1

        # 글로벌 플랫폼 저장
        for platform_code, data in global_platforms.items():
            cursor.execute('''
                INSERT INTO album_platform_links
                (artist_ko, artist_en, album_ko, album_en, platform_type, platform_code,
                 platform_name, platform_url, upc, album_cover_url, release_date, found, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                artist_ko, artist_en, album_ko, album_en,
                'global', platform_code, data['name'], data['url'],
                data.get('upc'), album_cover_url, release_date, 1 if data['found'] else 0
            ))
            saved_count += 1

        conn.commit()
        conn.close()

        return saved_count
    except Exception as e:
        print(f"  {Colors.FAIL}DB Save error: {str(e)}{Colors.ENDC}")
        return 0

def process_album(album_data):
    """개별 앨범 처리"""
    album_code = album_data['album_code']
    artist_ko = album_data['artist_ko']
    artist_en = album_data.get('artist_en') or ''
    album_ko = album_data['album_ko']
    album_en = album_data.get('album_en') or ''
    release_date = album_data.get('release_date')

    print(f"{Colors.OKCYAN}  → Searching Korean platforms...{Colors.ENDC}")

    # 1. 한국 플랫폼 검색
    kr_results = search_korean_platforms(artist_ko, album_ko)

    kr_platforms = {}
    kr_found_count = 0
    bugs_album_id = None

    for result in kr_results:
        kr_platforms[result['platform_id']] = result
        if result['found']:
            kr_found_count += 1
        if result['platform_id'] == 'bugs' and result.get('album_id'):
            bugs_album_id = result['album_id']

    # 2. 글로벌 플랫폼 검색
    print(f"{Colors.OKCYAN}  → Searching Global platforms...{Colors.ENDC}")

    search_name = artist_en if artist_en else artist_ko
    search_album = album_en if album_en else album_ko

    global_result = search_global_platforms_via_companion(search_name, search_album)

    global_platforms = global_result['platforms']
    global_found_count = global_result['count']
    album_cover_url = global_result['album_cover_url']

    if global_found_count > 0:
        print(f"    Companion API: {Colors.OKGREEN}✓ Found {global_found_count} platforms{Colors.ENDC}")
    else:
        print(f"    Companion API: {Colors.FAIL}✗ No platforms found{Colors.ENDC}")

    # 3. 앨범 커버 Fallback
    if not album_cover_url and bugs_album_id and len(bugs_album_id) >= 6:
        folder = bugs_album_id[:6]
        album_cover_url = f"https://image.bugsm.co.kr/album/images/500/{folder}/{bugs_album_id}.jpg"

    # 4. DB 저장
    saved_count = save_to_database(
        album_code, artist_ko, artist_en, album_ko, album_en, release_date,
        kr_platforms, global_platforms, album_cover_url
    )

    total_found = kr_found_count + global_found_count
    return kr_found_count, global_found_count, total_found, saved_count

def main():
    """메인 실행"""
    if len(sys.argv) < 2:
        print(f"\n{Colors.FAIL}Usage: python3 collect_from_db.py CDMA05070 CDMA05073 ...{Colors.ENDC}")
        print(f"Example: python3 collect_from_db.py CDMA05070 CDMA05073 CDMA05074\n")
        sys.exit(1)

    cdma_codes = sys.argv[1:]

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  Database-Driven Album Link Collector")
    print(f"  CDMA Code Based Collection")
    print(f"{'='*60}{Colors.ENDC}\n")
    print(f"Turso Database: {TURSO_DATABASE_URL[:50]}...")
    print(f"CDMA Codes: {len(cdma_codes)} albums")
    print()

    # CDMA 코드로 앨범 정보 조회
    print(f"{Colors.OKCYAN}Fetching albums from database...{Colors.ENDC}")
    albums = get_albums_by_cdma_codes(cdma_codes)
    total = len(albums)

    if total == 0:
        print(f"{Colors.WARNING}No albums found for given CDMA codes!{Colors.ENDC}\n")
        return

    print(f"Found {total} albums to process\n")

    success_count = 0
    fail_count = 0
    total_found = 0
    start_time = datetime.now()

    for idx, album in enumerate(albums, 1):
        album_code = album['album_code']
        artist_ko = album['artist_ko']
        album_ko = album['album_ko']

        print(f"{Colors.BOLD}[{idx}/{total}] {album_code} - {artist_ko} - {album_ko}{Colors.ENDC}")

        try:
            kr_found, global_found, total_plat_found, saved_count = process_album(album)

            print(f"{Colors.OKGREEN}  ✓ Success: KR {kr_found}/5, Global {global_found}, Total {saved_count} records saved{Colors.ENDC}\n")
            success_count += 1
            total_found += total_plat_found
        except Exception as e:
            print(f"{Colors.FAIL}  ✗ Failed: {str(e)}{Colors.ENDC}\n")
            fail_count += 1

        # 다음 요청 전 대기
        if idx < total:
            time.sleep(2)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  Collection Complete")
    print(f"{'='*60}{Colors.ENDC}\n")
    print(f"Total albums processed: {total}")
    print(f"{Colors.OKGREEN}Success: {success_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {fail_count}{Colors.ENDC}")
    print(f"Total platforms found: {total_found}")
    print(f"Duration: {duration:.1f}s")
    print(f"Average: {duration/total if total > 0 else 0:.1f}s per album\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Collection interrupted by user.{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
