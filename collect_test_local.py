#!/usr/bin/env python3
"""
로컬 SQLite DB로 수집 테스트
- collect_n8n_style.py의 로컬 버전
- Turso 대신 album_links.db 사용
"""

import requests
import time
import sys
import os
import re
import sqlite3
from datetime import datetime
from urllib.parse import quote
import json

# 로컬 SQLite 사용
DB_PATH = 'album_links.db'

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
    """로컬 SQLite DB 연결"""
    return sqlite3.connect(DB_PATH)

def get_test_albums(limit=1):
    """테스트용 앨범 가져오기"""
    conn = get_db_connection()
    conn.text_factory = str
    cursor = conn.cursor()

    # albums 테이블에서 CDMA 코드와 함께 가져오기
    query = '''
        SELECT
            a.album_code as cdma_code,
            a.artist_ko,
            a.artist_en,
            a.album_ko,
            a.album_en
        FROM albums a
        WHERE a.album_code IS NOT NULL
        ORDER BY a.id
        LIMIT ?
    '''

    cursor.execute(query, (limit,))

    albums = []
    for row in cursor.fetchall():
        albums.append({
            'cdma_code': row[0],
            'artist_ko': row[1],
            'artist_en': row[2] if row[2] else '',
            'album_ko': row[3],
            'album_en': row[4] if row[4] else ''
        })

    conn.close()
    return albums

def normalize_text(text):
    """텍스트 정규화"""
    if not text:
        return ''
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            }

            # VIBE API용 추가 헤더
            if platform_id == 'vibe':
                headers['Referer'] = 'https://vibe.naver.com/'
                headers['Origin'] = 'https://vibe.naver.com'

            response = requests.get(platform['searchUrl'], headers=headers, timeout=15)

            if response.status_code == 200:
                album_url = None
                album_id = None

                # API 응답 처리 (FLO, VIBE)
                if platform['useApi']:
                    try:
                        json_data = json.loads(response.text)

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

                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        pass

                else:
                    # HTML 파싱 (멜론, 지니, 벅스)
                    html = response.text

                    if platform_id == 'melon':
                        match = re.search(r"goAlbumDetail\(['\"]([0-9]+)['\"]\)", html)
                        if match:
                            album_id = match.group(1)
                            album_url = f"https://www.melon.com/album/detail.htm?albumId={album_id}"

                    elif platform_id == 'genie':
                        # 지니: fnViewAlbumLayer('12345') 패턴
                        normalized_artist = normalize_text(artist)
                        normalized_album = normalize_text(album)

                        pattern = r"fnViewAlbumLayer\(['\"]?([0-9]+)['\"]?\)"
                        all_matches = []

                        for match in re.finditer(pattern, html):
                            album_id_candidate = match.group(1)
                            start_pos = max(0, match.start() - 500)
                            end_pos = min(len(html), match.end() + 500)
                            context = html[start_pos:end_pos]
                            all_matches.append({'id': album_id_candidate, 'context': context})

                        # 컨텍스트 기반 매칭
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

                        # Fallback: 첫 번째 결과 사용
                        if not album_id and len(all_matches) > 0:
                            album_id = all_matches[0]['id']
                            album_url = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"

                    elif platform_id == 'bugs':
                        # 벅스: /album/12345 패턴 + 컨텍스트 매칭
                        normalized_artist = normalize_text(artist)
                        normalized_album = normalize_text(album)

                        pattern = r"/album/(\d+)"
                        all_matches = []

                        for match in re.finditer(pattern, html):
                            album_id_candidate = match.group(1)
                            start_pos = max(0, match.start() - 500)
                            end_pos = min(len(html), match.end() + 500)
                            context = html[start_pos:end_pos]
                            all_matches.append({'id': album_id_candidate, 'context': context})

                        # 컨텍스트 기반 매칭
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

                        # Fallback: 첫 번째 결과 사용
                        if not album_id and len(all_matches) > 0:
                            album_id = all_matches[0]['id']
                            album_url = f"https://music.bugs.co.kr/album/{album_id}"

                results.append({
                    'platform_id': platform_id,
                    'platform_name': platform['name'],
                    'album_url': album_url,
                    'album_id': album_id,
                    'found': bool(album_url),
                    'status': 'success' if album_url else 'not_found'
                })

                if album_url:
                    print(f"[OK]")
                else:
                    print(f"[FAIL]")
            else:
                print(f"[FAIL] HTTP {response.status_code}")
                results.append({
                    'platform_id': platform_id,
                    'platform_name': platform['name'],
                    'found': False,
                    'album_url': None,
                    'album_id': None
                })

        except Exception as e:
            print(f"[ERROR] {str(e)[:20]}")
            results.append({
                'platform_id': platform_id,
                'platform_name': platform['name'],
                'found': False,
                'album_url': None,
                'album_id': None
            })

        time.sleep(0.5)

    return results

def search_global_platforms_via_companion(artist_ko, artist_en, album_ko, album_en, cdma_code=None):
    """Companion API 호출"""
    companion_api_port = os.environ.get('COMPANION_API_PORT', '5001')
    companion_api_url = f"http://localhost:{companion_api_port}"

    print(f"    Calling Companion API at {companion_api_url}...")

    try:
        response = requests.post(
            f"{companion_api_url}/search",
            json={
                'artist_ko': artist_ko,
                'artist_en': artist_en,
                'album_ko': album_ko,
                'album_en': album_en,
                'cdma_code': cdma_code
            },
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
        print(f"    [WARNING] Companion API not available")
        return {'success': False, 'platforms': {}, 'album_cover_url': None, 'count': 0}
    except Exception as e:
        print(f"    [ERROR] {str(e)}")
        return {'success': False, 'platforms': {}, 'album_cover_url': None, 'count': 0}

def process_album(artist_ko, artist_en, album_ko, album_en, cdma_code=None):
    """개별 앨범 처리"""
    print(f"  → Searching Korean platforms...")

    # 1. 한국 플랫폼 검색
    kr_results = search_korean_platforms(artist_ko, album_ko)

    kr_found_count = 0
    for result in kr_results:
        if result['found']:
            kr_found_count += 1

    # 2. 글로벌 플랫폼 검색
    print(f"  → Searching Global platforms...")
    if cdma_code:
        print(f"    CDMA Code: {cdma_code}")

    global_result = search_global_platforms_via_companion(
        artist_ko, artist_en, album_ko, album_en, cdma_code
    )

    global_found_count = global_result['count']

    if global_found_count > 0:
        print(f"    [OK] Found {global_found_count} global platforms")
    else:
        print(f"    [FAIL] No global platforms found")

    total_found = kr_found_count + global_found_count

    print(f"\n  Results: KR {kr_found_count}/5, Global {global_found_count}, Total {total_found}")

    return kr_found_count, global_found_count, total_found

def main():
    """메인 실행"""
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    print("=" * 60)
    print("  Local SQLite Collection Test")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Test albums: {limit}")
    print()

    # 테스트 앨범 가져오기
    print("Fetching test albums...")
    albums = get_test_albums(limit)

    if not albums:
        print("No albums found!")
        return

    print(f"Found {len(albums)} albums to test\n")

    for idx, album in enumerate(albums, 1):
        artist_ko = album['artist_ko']
        artist_en = album.get('artist_en') or ''
        album_ko = album['album_ko']
        album_en = album.get('album_en') or ''
        cdma_code = album.get('cdma_code') or None

        header = f"{artist_ko} - {album_ko}"
        if cdma_code:
            header += f" [{cdma_code}]"
        print(f"\n[{idx}/{len(albums)}] {header}")
        print("-" * 60)

        try:
            kr_found, global_found, total_found = process_album(
                artist_ko, artist_en, album_ko, album_en, cdma_code
            )
            print(f"\n  [OK] Test completed successfully!")
        except Exception as e:
            print(f"\n  [ERROR] Test failed: {str(e)}")

    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.\n")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
