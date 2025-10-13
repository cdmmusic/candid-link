#!/usr/bin/env python3
"""
CSV 파일에서 앨범 목록을 읽어서 n8n 워크플로우로 일괄 처리
"""

import csv
import requests
import time
import sys
from datetime import datetime

# n8n 웹훅 URL
WEBHOOK_URL = "http://localhost:5678/webhook/album-links"

# 진행 상황 출력 색상
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def process_album(artist, artist_en, album_ko, album_en):
    """
    개별 앨범을 n8n 워크플로우로 전송
    """
    payload = {
        "primary_artist": artist,
        "primary_artist_en": artist_en,
        "album_title_ko": album_ko,
        "album_title_en": album_en
    }

    try:
        print(f"{Colors.OKCYAN}  → Sending: {artist} - {album_ko}{Colors.ENDC}")
        response = requests.post(WEBHOOK_URL, json=payload, timeout=120)

        if response.status_code == 200:
            result = response.json()
            kr_found = result.get('summary', {}).get('kr_found', 0)
            global_found = result.get('summary', {}).get('global_found', 0)

            print(f"{Colors.OKGREEN}  ✓ Success: {kr_found} KR + {global_found} Global platforms{Colors.ENDC}")
            return True, kr_found + global_found
        else:
            print(f"{Colors.FAIL}  ✗ Error: {response.status_code} - {response.text[:100]}{Colors.ENDC}")
            return False, 0

    except requests.exceptions.Timeout:
        print(f"{Colors.WARNING}  ⚠ Timeout (120s exceeded){Colors.ENDC}")
        return False, 0
    except Exception as e:
        print(f"{Colors.FAIL}  ✗ Exception: {str(e)}{Colors.ENDC}")
        return False, 0

def main():
    """
    CSV 파일을 읽어서 모든 앨범 처리
    """
    csv_file = "albums.csv"

    if len(sys.argv) > 1:
        csv_file = sys.argv[1]

    print(f"\n{Colors.BOLD}{Colors.HEADER}========================================")
    print(f"  Album Links Batch Processor")
    print(f"========================================{Colors.ENDC}\n")
    print(f"CSV File: {csv_file}")
    print(f"Webhook: {WEBHOOK_URL}\n")

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            albums = list(reader)
    except FileNotFoundError:
        print(f"{Colors.FAIL}Error: File '{csv_file}' not found{Colors.ENDC}")
        return
    except Exception as e:
        print(f"{Colors.FAIL}Error reading CSV: {str(e)}{Colors.ENDC}")
        return

    total = len(albums)
    print(f"Total albums to process: {total}\n")

    success_count = 0
    fail_count = 0
    total_platforms = 0

    start_time = datetime.now()

    for idx, row in enumerate(albums, 1):
        artist = row.get('primary_artist', '').strip()
        artist_en = row.get('primary_artist_en', '').strip()
        album_ko = row.get('album_title_ko', '').strip()
        album_en = row.get('album_title_en', '').strip()

        if not artist or not album_ko:
            print(f"{Colors.WARNING}[{idx}/{total}] Skipping: Missing artist or album{Colors.ENDC}")
            fail_count += 1
            continue

        print(f"{Colors.BOLD}[{idx}/{total}] {artist} - {album_ko}{Colors.ENDC}")

        success, platform_count = process_album(artist, artist_en, album_ko, album_en)

        if success:
            success_count += 1
            total_platforms += platform_count
        else:
            fail_count += 1

        # 다음 요청 전 대기 (서버 부하 방지)
        if idx < total:
            wait_time = 2  # 2초 대기
            print(f"  Waiting {wait_time}s before next album...\n")
            time.sleep(wait_time)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{Colors.BOLD}{Colors.HEADER}========================================")
    print(f"  Processing Complete")
    print(f"========================================{Colors.ENDC}\n")
    print(f"Total albums: {total}")
    print(f"{Colors.OKGREEN}Success: {success_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {fail_count}{Colors.ENDC}")
    print(f"Total platforms found: {total_platforms}")
    print(f"Duration: {duration:.1f}s ({duration/60:.1f}m)")
    print(f"Average: {duration/total:.1f}s per album\n")

if __name__ == "__main__":
    main()
