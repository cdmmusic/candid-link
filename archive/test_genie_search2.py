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

print(f"Searching for: {artist} - {album}")
print()

# 검색 결과 영역 찾기
if '<div class="list-wrap"' in html:
    print("Found <div class=\"list-wrap\"> - main search results area")
    # list-wrap 영역만 추출
    start_idx = html.find('<div class="list-wrap"')
    end_idx = html.find('</div><!-- //list-wrap -->', start_idx)

    if end_idx > start_idx:
        search_results_html = html[start_idx:end_idx]
        print(f"Search results section length: {len(search_results_html)} chars")
        print()

        # 이 영역에서만 fnViewAlbumLayer 찾기
        pattern = r"fnViewAlbumLayer\([\'\"]?([0-9]+)[\'\"]?\)"
        matches = list(re.finditer(pattern, search_results_html))

        print(f"Found {len(matches)} albums in search results")
        print()

        for i, match in enumerate(matches[:5], 1):
            album_id = match.group(1)
            # 주변 컨텍스트에서 앨범명과 아티스트명 찾기
            start_pos = max(0, match.start() - 500)
            end_pos = min(len(search_results_html), match.end() + 500)
            context = search_results_html[start_pos:end_pos]

            print(f"Result #{i}: Album ID = {album_id}")

            # 앨범명 찾기 (title 클래스)
            title_match = re.search(r'class="title"[^>]*>([^<]+)<', context)
            if title_match:
                print(f"  Album: {title_match.group(1).strip()}")

            # 아티스트명 찾기
            artist_match = re.search(r'class="artist"[^>]*>([^<]+)<', context)
            if artist_match:
                print(f"  Artist: {artist_match.group(1).strip()}")

            print()
else:
    print("WARNING: Could not find search results area!")
    print()
    print("Checking for 'no results' message...")
    if "검색 결과가 없습니다" in html or "검색결과가 없습니다" in html:
        print("  → Found 'no results' message")
    else:
        print("  → No 'no results' message found")

        # HTML 구조 샘플 출력
        if '<div id="body-cont"' in html:
            idx = html.find('<div id="body-cont"')
            print("\nHTML structure sample:")
            print(html[idx:idx+1000])
