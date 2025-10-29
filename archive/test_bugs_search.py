#!/usr/bin/env python3
import requests
import re
from urllib.parse import quote

# 샘플 테스트에서 사용한 앨범 중 하나로 테스트
artist = "녹음"
album = "10월의 언어"
query = f"{artist} {album}"
encoded = quote(query)

# Bugs 검색
url = f"https://music.bugs.co.kr/search/album?q={encoded}"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

print(f"Searching for: {artist} - {album}")
print(f"URL: {url}")
print()

response = requests.get(url, headers=headers, timeout=15)
html = response.text

print(f"Status: {response.status_code}")
print(f"Response length: {len(html)}")
print()

# 검색 결과 영역 찾기
search_section_start = html.find('<section class="sectionPadding">')
if search_section_start != -1:
    print("Found <section class=\"sectionPadding\"> - main search results area")
    search_section_end = html.find('</section>', search_section_start)

    if search_section_end > search_section_start:
        search_results_html = html[search_section_start:search_section_end]
        print(f"Search results section length: {len(search_results_html)} chars")
        print()

        # 0 결과 체크
        if '검색 결과가 없습니다' in search_results_html or 'no_result' in search_results_html:
            print("  → Found 'no results' message")
        else:
            print("  → Has search results")

            # 앨범 ID 패턴 찾기
            patterns = [
                r"album/([0-9]+)",
                r"albumId[=:]([0-9]+)",
                r"data-album[=-]?id[=:]?['\"]?([0-9]+)",
            ]

            for pattern in patterns:
                matches = list(re.finditer(pattern, search_results_html))
                if matches:
                    print(f"\nFound {len(matches)} matches for pattern: {pattern}")
                    for i, match in enumerate(matches[:3], 1):
                        album_id = match.group(1)
                        print(f"  Match #{i}: Album ID = {album_id}")

                        # 주변 컨텍스트 확인
                        start_pos = max(0, match.start() - 300)
                        end_pos = min(len(search_results_html), match.end() + 300)
                        context = search_results_html[start_pos:end_pos]

                        # 아티스트/앨범명이 컨텍스트에 있는지 확인
                        has_artist = artist in context or artist.lower() in context.lower()
                        has_album = album in context or album.lower() in context.lower()

                        print(f"    Context has artist: {has_artist}, has album: {has_album}")

            # 패턴이 없으면 HTML 구조 샘플 출력
            all_matches_count = sum(len(list(re.finditer(p, search_results_html))) for p in patterns)
            if all_matches_count == 0:
                print("\nNo album ID patterns found!")
                print("\nHTML structure sample (first 1000 chars):")
                print(search_results_html[:1000])
else:
    print("WARNING: Could not find <section class=\"sectionPadding\">")
    print("\nChecking for alternative structures...")

    # 다른 구조 찾기
    if '<div class="resultWrap"' in html:
        print("  → Found <div class=\"resultWrap\">")
        idx = html.find('<div class="resultWrap"')
        print("\nHTML sample:")
        print(html[idx:idx+1000])
    elif 'searchResultList' in html:
        print("  → Found 'searchResultList' in HTML")
        idx = html.find('searchResultList')
        print("\nHTML sample:")
        print(html[max(0, idx-100):idx+900])
    else:
        print("  → Showing first 1000 chars of body:")
        body_idx = html.find('<body')
        if body_idx != -1:
            print(html[body_idx:body_idx+1000])
