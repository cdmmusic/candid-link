#!/usr/bin/env python3
import requests
import re
from urllib.parse import quote

artist = "디비치"
album = "타입감슙"
query = f"{artist} {album}"
encoded = quote(query)

# Genie 검색
url = f"https://www.genie.co.kr/search/searchAlbum?query={encoded}"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

response = requests.get(url, headers=headers, timeout=15)
html = response.text

print(f"Status: {response.status_code}")
print(f"Response length: {len(html)}")
print()

# fnViewAlbumLayer 패턴 찾기
pattern = r"fnViewAlbumLayer\([\'\"]?([0-9]+)[\'\"]?\)"
matches = list(re.finditer(pattern, html))

print(f"Found {len(matches)} matches for fnViewAlbumLayer")
print()

if len(matches) > 0:
    for i, match in enumerate(matches[:5], 1):
        album_id = match.group(1)
        start_pos = max(0, match.start() - 300)
        end_pos = min(len(html), match.end() + 300)
        context = html[start_pos:end_pos]

        print(f"Match #{i}: Album ID = {album_id}")
        print(f"Context (first 300 chars):")
        print(context[:300])
        print("-" * 80)
        print()
else:
    print("No matches found! Checking HTML content...")
    print()
    print("Checking if page contains album results:")
    if "검색 결과가 없습니다" in html or "검색결과가 없습니다" in html:
        print("  → No search results message found")
    elif "앨범" in html:
        print("  → Contains '앨범' text")

    # 다른 패턴 시도
    alt_patterns = [
        r"albumId[=:][\'\"]?([0-9]+)",
        r"axnm[=:][\'\"]?([0-9]+)",
        r"/detail/albumInfo\?axnm=([0-9]+)",
    ]

    for alt_pattern in alt_patterns:
        alt_matches = list(re.finditer(alt_pattern, html))
        if alt_matches:
            print(f"\nFound {len(alt_matches)} matches for alternative pattern: {alt_pattern}")
            for i, match in enumerate(alt_matches[:3], 1):
                print(f"  Match #{i}: {match.group(1)}")
