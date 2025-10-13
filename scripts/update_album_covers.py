#!/usr/bin/env python3
"""
앨범 커버 이미지 수집 및 업데이트
Bugs 음악 플랫폼에서 앨범 커버 URL을 가져와서 데이터베이스 업데이트
"""

import sqlite3
import time
import sys
from datetime import datetime

# 데이터베이스 경로
DB_PATH = "database/album_links.db"

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

def get_albums_without_covers(limit=None):
    """커버 이미지가 없는 앨범 목록 가져오기"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = '''
        SELECT DISTINCT artist_ko, album_ko
        FROM album_platform_links
        WHERE album_cover_url IS NULL OR album_cover_url = ''
        ORDER BY created_at DESC
    '''

    if limit:
        query += f' LIMIT {limit}'

    cursor.execute(query)
    albums = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return albums

def get_cover_url_from_bugs(artist_ko, album_ko):
    """Bugs 플랫폼에서 앨범 커버 URL 가져오기"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT album_cover_url
        FROM album_platform_links
        WHERE artist_ko = ? AND album_ko = ?
        AND platform_id = 'bugs'
        AND album_cover_url IS NOT NULL
        AND album_cover_url != ''
        LIMIT 1
    ''', (artist_ko, album_ko))

    row = cursor.fetchone()
    conn.close()

    if row:
        return row['album_cover_url']
    return None

def update_album_cover(artist_ko, album_ko, cover_url):
    """앨범 커버 URL 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE album_platform_links
        SET album_cover_url = ?
        WHERE artist_ko = ? AND album_ko = ?
        AND (album_cover_url IS NULL OR album_cover_url = '')
    ''', (cover_url, artist_ko, album_ko))

    updated = cursor.rowcount
    conn.commit()
    conn.close()

    return updated

def main():
    """메인 실행"""
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"{Colors.FAIL}Error: Invalid limit. Please provide a number.{Colors.ENDC}")
            return

    print(f"\n{Colors.BOLD}{Colors.HEADER}========================================")
    print(f"  Album Cover Updater")
    print(f"========================================{Colors.ENDC}\n")
    print(f"Database: {DB_PATH}")
    if limit:
        print(f"Limit: {limit} albums\n")
    else:
        print(f"Limit: All albums\n")

    # 커버가 없는 앨범 가져오기
    print(f"{Colors.OKCYAN}Fetching albums without covers...{Colors.ENDC}")
    albums = get_albums_without_covers(limit)
    total = len(albums)

    if total == 0:
        print(f"{Colors.OKGREEN}All albums already have cover images!{Colors.ENDC}\n")
        return

    print(f"Found {total} albums without covers\n")

    success_count = 0
    fail_count = 0
    start_time = datetime.now()

    for idx, album in enumerate(albums, 1):
        artist_ko = album['artist_ko']
        album_ko = album['album_ko']

        print(f"{Colors.BOLD}[{idx}/{total}] {artist_ko} - {album_ko}{Colors.ENDC}")

        # Bugs에서 커버 URL 찾기
        cover_url = get_cover_url_from_bugs(artist_ko, album_ko)

        if cover_url:
            # 데이터베이스 업데이트
            updated = update_album_cover(artist_ko, album_ko, cover_url)

            if updated > 0:
                print(f"{Colors.OKGREEN}  ✓ Updated {updated} records with cover: {cover_url[:60]}...{Colors.ENDC}\n")
                success_count += 1
            else:
                print(f"{Colors.WARNING}  ⚠ No records updated (already has cover){Colors.ENDC}\n")
                fail_count += 1
        else:
            print(f"{Colors.WARNING}  ⚠ No cover URL found in Bugs platform{Colors.ENDC}\n")
            fail_count += 1

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{Colors.BOLD}{Colors.HEADER}========================================")
    print(f"  Update Complete")
    print(f"========================================{Colors.ENDC}\n")
    print(f"Total albums: {total}")
    print(f"{Colors.OKGREEN}Success: {success_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {fail_count}{Colors.ENDC}")
    print(f"Duration: {duration:.1f}s ({duration/60:.1f}m)")
    if total > 0:
        print(f"Average: {duration/total:.2f}s per album\n")

if __name__ == "__main__":
    main()
