#!/usr/bin/env python3
"""
간단한 수집 테스트 스크립트
- 로컬 SQLite DB 사용
- 국내 플랫폼 1개 앨범만 테스트
"""

import sqlite3
import requests
import re
from urllib.parse import quote
import time

def test_melon_search(artist, album):
    """멜론 검색 테스트"""
    print(f"\n=== Testing Melon Search ===")
    print(f"Artist: {artist}")
    print(f"Album: {album}")

    query = f"{artist} {album}"
    encoded = quote(query)
    url = f"https://www.melon.com/search/total/index.htm?q={encoded}&section=&searchGnbYn=Y&kkoSpl=N&kkoDpType="

    print(f"URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            # albumId 찾기
            matches = re.findall(r'goAlbumDetail\(\'(\d+)\'\)', response.text)
            if matches:
                album_id = matches[0]
                melon_url = f"https://www.melon.com/album/detail.htm?albumId={album_id}"
                print(f"[OK] Found: {melon_url}")
                return melon_url
            else:
                print("[FAIL] Album ID not found in response")
                return None
        else:
            print(f"[FAIL] HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return None

def test_bugs_search(artist, album):
    """벅스 검색 테스트"""
    print(f"\n=== Testing Bugs Search ===")
    print(f"Artist: {artist}")
    print(f"Album: {album}")

    query = f"{artist} {album}"
    encoded = quote(query)
    url = f"https://music.bugs.co.kr/search/integrated?q={encoded}"

    print(f"URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            # albumId 찾기
            matches = re.findall(r'/album/(\d+)', response.text)
            if matches:
                album_id = matches[0]
                bugs_url = f"https://music.bugs.co.kr/album/{album_id}"
                print(f"[OK] Found: {bugs_url}")
                return bugs_url
            else:
                print("[FAIL] Album ID not found in response")
                return None
        else:
            print(f"[FAIL] HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return None

def main():
    print("=" * 60)
    print("국내 플랫폼 수집 테스트")
    print("=" * 60)

    # 로컬 DB 연결
    conn = sqlite3.connect('album_links.db')
    conn.text_factory = str
    cursor = conn.cursor()

    # 테스트용 앨범 선택 (영문명이 있는 것으로)
    cursor.execute('''
        SELECT album_code, artist_ko, album_ko, artist_en, album_en
        FROM albums
        WHERE artist_en IS NOT NULL AND artist_en != ''
        LIMIT 1
    ''')

    row = cursor.fetchone()

    if not row:
        print("No albums found with English names. Using Korean only album...")
        cursor.execute('''
            SELECT album_code, artist_ko, album_ko, artist_en, album_en
            FROM albums
            LIMIT 1
        ''')
        row = cursor.fetchone()

    if row:
        cdma_code, artist_ko, album_ko, artist_en, album_en = row

        print(f"\nTest Album:")
        print(f"  CDMA: {cdma_code}")
        print(f"  Artist: {artist_ko}")
        print(f"  Album: {album_ko}")

        # 검색에 사용할 이름 결정
        artist = artist_en if artist_en else artist_ko
        album = album_en if album_en else album_ko

        # 멜론 테스트
        melon_url = test_melon_search(artist, album)
        time.sleep(1)  # Rate limiting

        # 벅스 테스트
        bugs_url = test_bugs_search(artist, album)

        print("\n" + "=" * 60)
        print("Test Results Summary:")
        print("=" * 60)
        print(f"Melon: {'[OK] Success' if melon_url else '[FAIL] Failed'}")
        print(f"Bugs:  {'[OK] Success' if bugs_url else '[FAIL] Failed'}")

    else:
        print("No albums found in database!")

    conn.close()

if __name__ == '__main__':
    main()
