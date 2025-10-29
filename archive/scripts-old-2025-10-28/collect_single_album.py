#!/usr/bin/env python3
"""
단일 앨범 링크 수집 스크립트
사용법: python3 collect_single_album.py "아티스트명" "앨범명"
"""

import sys
import os

# collect_n8n_style.py의 함수들 임포트
sys.path.insert(0, os.path.dirname(__file__))
from collect_n8n_style import process_album, Colors

def main():
    if len(sys.argv) < 3:
        print("사용법: python3 collect_single_album.py <아티스트명> <앨범명>")
        sys.exit(1)

    artist_ko = sys.argv[1]
    album_ko = sys.argv[2]
    artist_en = sys.argv[3] if len(sys.argv) > 3 else ''
    album_en = sys.argv[4] if len(sys.argv) > 4 else ''

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print(f"  Single Album Link Collector")
    print(f"{'='*60}{Colors.ENDC}\n")
    print(f"Artist: {artist_ko}")
    print(f"Album: {album_ko}\n")

    try:
        kr_found, global_found, total_found, saved_count = process_album(
            artist_ko, artist_en, album_ko, album_en
        )

        print(f"\n{Colors.OKGREEN}{'='*60}")
        print(f"  Collection Complete")
        print(f"{'='*60}{Colors.ENDC}")
        print(f"Korean platforms found: {kr_found}/5")
        print(f"Global platforms found: {global_found}")
        print(f"Total platforms found: {total_found}")
        print(f"Records saved: {saved_count}\n")

    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
