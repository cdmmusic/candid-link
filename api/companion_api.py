#!/usr/bin/env python3
"""
Companion.global + 국내 플랫폼 통합 수집 API (수정 버전)
글로벌 플랫폼 추출 로직 개선
"""
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import requests
import json
import urllib.parse
import re
import sys

app = Flask(__name__)

# Selenium Hub URL (Docker)
SELENIUM_HUB = "http://localhost:4444"

# Global driver to reuse logged-in session
driver = None
logged_in = False

def safe_print(message):
    """안전한 출력 (인코딩 에러 방지)"""
    try:
        print(f"[Companion API] {message}")
    except UnicodeEncodeError:
        try:
            print(f"[Companion API] {message.encode('utf-8', errors='replace').decode('utf-8')}")
        except:
            print("[Companion API] [Unable to print message]")

def setup_driver():
    """Setup Selenium driver with Docker Hub"""
    global driver

    if driver is None:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        # JavaScript 실행 대기 시간 추가
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            driver = webdriver.Remote(
                command_executor=f'{SELENIUM_HUB}/wd/hub',
                options=chrome_options
            )
            # 페이지 로드 타임아웃 설정
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)

            safe_print("Driver initialized successfully")
            return True
        except Exception as e:
            safe_print(f"Failed to initialize driver: {e}")
            driver = None
            return False
    return True

def normalize_text(text):
    """텍스트 정규화 (비교용)"""
    if not text:
        return ""
    # 소문자 변환, 공백 제거, 특수문자 제거
    text = text.lower()
    text = re.sub(r'[^\w\s가-힣]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

def extract_bugs_album_cover(bugs_url):
    """Bugs album cover extraction"""
    try:
        safe_print(f"[Bugs Cover] Extracting from: {bugs_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9'
        }
        response = requests.get(bugs_url, headers=headers, timeout=10)
        if response.status_code == 200:
            html = response.text
            # Pattern 1: albumImgArea
            import re
            pattern1 = r'<div[^>]*class="[^"]*albumImgArea[^"]*"[^>]*>.*?<img[^>]+src="([^"]+)"'
            matches = re.findall(pattern1, html, re.DOTALL)
            if matches:
                cover_url = matches[0]
                if cover_url.startswith('//'):
                    cover_url = f"https:{cover_url}"
                elif cover_url.startswith('/'):
                    cover_url = f"https://music.bugs.co.kr{cover_url}"
                safe_print(f"[Bugs] Cover found: {cover_url[:80]}")
                return cover_url
            # Pattern 2: og:image
            pattern2 = r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"'
            matches = re.findall(pattern2, html)
            if matches:
                cover_url = matches[0]
                if cover_url.startswith('//'):
                    cover_url = f"https:{cover_url}"
                safe_print(f"[Bugs] Cover via OG: {cover_url[:80]}")
                return cover_url
    except Exception as e:
        safe_print(f"[Bugs Cover] Error: {e}")
    return None

def search_kr_platforms(artist, album):
    """국내 플랫폼 검색 (멜론, 지니, 벅스, FLO, VIBE)"""
    safe_print(f"Starting KR platform search: {artist} - {album}")

    kr_results = {}
    query = f"{artist} {album}"
    encoded = urllib.parse.quote(query)

    # 캐시 버스터 (타임스탬프)
    cache_buster = str(int(time.time() * 1000))

    # 공통 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
    }

    # 국내 플랫폼 검색 설정
    platforms = [
        {
            'id': 'melon',
            'name': '멜론',
            'searchUrl': f"https://www.melon.com/search/album/index.htm?q={encoded}&section=&searchGnbYn=Y&kkoSpl=Y&kkoDpType=&_={cache_buster}",
        },
        {
            'id': 'genie',
            'name': '지니',
            'searchUrl': f"https://www.genie.co.kr/search/searchAlbum?query={encoded}&_={cache_buster}",
        },
        {
            'id': 'bugs',
            'name': '벅스',
            'searchUrl': f"https://music.bugs.co.kr/search/album?q={encoded}&_={cache_buster}",
        },
        {
            'id': 'vibe',
            'name': 'VIBE',
            'searchUrl': f"https://apis.naver.com/vibeWeb/musicapiweb/v4/searchall?query={encoded}&sort=RELEVANCE&alDisplay=21",
            'headers': {
                'Accept': 'application/json',
                'Referer': 'https://vibe.naver.com/',
                'Origin': 'https://vibe.naver.com'
            }
        },
        {
            'id': 'flo',
            'name': 'FLO',
            'searchUrl': f"https://www.music-flo.com/api/search/v2/search?keyword={encoded}&searchType=ALBUM&sortType=ACCURACY&size=20&page=1",
        }
    ]

    normalized_artist = normalize_text(artist)
    normalized_album = normalize_text(album)

    for platform in platforms:
        try:
            platform_id = platform['id']
            platform_name = platform['name']

            safe_print(f"[KR Search] Searching {platform_name}...")

            # 플랫폼별 헤더 설정
            req_headers = headers.copy()
            if 'headers' in platform:
                req_headers.update(platform['headers'])

            # API 요청
            response = requests.get(platform['searchUrl'], headers=req_headers, timeout=10)

            if response.status_code != 200:
                safe_print(f"[KR Search] {platform_name} failed: {response.status_code}")
                continue

            # FLO와 VIBE는 JSON 응답
            if platform_id in ['flo', 'vibe']:
                try:
                    # JSON 응답 확인
                    if not response.text or response.text.strip().startswith('<'):
                        safe_print(f"[KR Search] {platform_name} returned HTML instead of JSON")
                        continue

                    json_data = response.json()

                    if platform_id == 'flo':
                        # FLO API 응답 구조 확인
                        if 'data' in json_data and 'list' in json_data['data']:
                            data_list = json_data['data']['list']
                            safe_print(f"[KR Search] FLO data_list length: {len(data_list)}")

                            for data_item in data_list:
                                # ALBUM 타입 찾기
                                if data_item.get('type') == 'ALBUM' and 'list' in data_item:
                                    album_items = data_item['list']
                                    if len(album_items) > 0:
                                        # 첫 번째 앨범 선택
                                        first_album = album_items[0]
                                        album_id = str(first_album.get('id', ''))
                                        album_title = first_album.get('title', '')
                                        artist_names = ', '.join([artist.get('name', '') for artist in first_album.get('artistList', [])])

                                        if album_id:
                                            kr_results[platform_id] = f"https://www.music-flo.com/detail/album/{album_id}"
                                            safe_print(f"[KR Search] {platform_name} found: {album_id} ({artist_names} - {album_title})")
                                            break
                                        else:
                                            safe_print(f"[KR Search] FLO album found but no ID")
                        else:
                            safe_print(f"[KR Search] FLO no data/list in response")

                    elif platform_id == 'vibe':
                        if 'response' in json_data and 'result' in json_data['response']:
                            result = json_data['response']['result']

                            # 먼저 trackResult 확인 (더 정확한 결과)
                            if 'trackResult' in result and 'tracks' in result['trackResult']:
                                tracks = result['trackResult']['tracks']

                                if len(tracks) > 0:
                                    first_track = tracks[0]
                                    if 'album' in first_track:
                                        album_id = str(first_track['album'].get('albumId', ''))
                                        album_title = first_track['album'].get('albumTitle', '')
                                        artist_names = ', '.join([artist.get('artistName', '') for artist in first_track.get('artists', [])])

                                        if album_id:
                                            kr_results[platform_id] = f"https://vibe.naver.com/album/{album_id}"
                                            safe_print(f"[KR Search] {platform_name} found via track: {album_id} ({artist_names} - {album_title})")

                            # trackResult가 없으면 albumResult 확인
                            elif 'albumResult' in result and 'albums' in result['albumResult']:
                                albums = result['albumResult']['albums']

                                if len(albums) > 0:
                                    first_album = albums[0]
                                    album_id = str(first_album.get('albumId', ''))
                                    album_title = first_album.get('albumTitle', '')
                                    artist_names = ', '.join([artist.get('artistName', '') for artist in first_album.get('artists', [])])

                                    if album_id:
                                        kr_results[platform_id] = f"https://vibe.naver.com/album/{album_id}"
                                        safe_print(f"[KR Search] {platform_name} found via album: {album_id} ({artist_names} - {album_title})")
                        else:
                            safe_print(f"[KR Search] VIBE invalid response structure")
                except json.JSONDecodeError as e:
                    safe_print(f"[KR Search] {platform_name} JSON decode error: {e}")
                except Exception as e:
                    safe_print(f"[KR Search] {platform_name} unexpected error: {e}")

            else:
                # 멜론, 지니, 벅스는 HTML 파싱
                html = response.text
                album_id = None

                if platform_id == 'melon':
                    # goAlbumDetail('10426648') 패턴 찾기
                    pattern = r'goAlbumDetail\([\'"](\d+)[\'"]\)'
                    matches = re.findall(pattern, html)
                    if matches:
                        album_id = matches[0]
                        kr_results[platform_id] = f"https://www.melon.com/album/detail.htm?albumId={album_id}"
                        safe_print(f"[KR Search] {platform_name} found: {album_id}")

                elif platform_id == 'genie':
                    # fnViewAlbumLayer('81867444'); 패턴 찾기
                    pattern = r'fnViewAlbumLayer\([\'"](\d+)[\'"]\)'
                    matches = re.findall(pattern, html)
                    if matches:
                        album_id = matches[0]
                        kr_results[platform_id] = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"
                        safe_print(f"[KR Search] {platform_name} found: {album_id}")

                elif platform_id == 'bugs':
                    # href="https://music.bugs.co.kr/album/4027185" 패턴 찾기
                    pattern = r'bugs\.co\.kr/album/(\d+)'
                    matches = re.findall(pattern, html)
                    if matches:
                        album_id = matches[0]
                        kr_results[platform_id] = f"https://music.bugs.co.kr/album/{album_id}"
                        safe_print(f"[KR Search] {platform_name} found: {album_id}")

        except requests.exceptions.RequestException as e:
            safe_print(f"[KR Search] {platform_name} request error: {e}")
        except Exception as e:
            safe_print(f"[KR Search] {platform_name} unexpected error: {e}")

    safe_print(f"[KR Search] Found {len(kr_results)} Korean platform links")
    return kr_results

def login_to_companion():
    """Login to companion.global"""
    global logged_in, driver

    if logged_in:
        return True

    if not setup_driver():
        return False

    try:
        safe_print("Starting login process...")
        driver.get("http://companion.global/login")
        time.sleep(3)

        safe_print(f"Loaded login page: {driver.current_url}")

        # Enter credentials
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")

        username_field.clear()
        username_field.send_keys("candidmusic")
        safe_print("Entered username: candidmusic")

        password_field.clear()
        password_field.send_keys("dkfvfk2-%!#")
        safe_print("Entered password")

        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button.btn_login")
        login_button.click()
        safe_print("Clicked login button")

        # Wait for redirect to dashboard
        time.sleep(3)
        safe_print(f"After login, URL: {driver.current_url}")

        # Check if login successful
        if "dashboard" in driver.current_url or driver.title:
            safe_print(f"Page title: {driver.title}")
            safe_print("Successfully reached dashboard")
            logged_in = True
            return True
        else:
            safe_print("Login may have failed - unexpected redirect")
            return False

    except Exception as e:
        safe_print(f"Login error: {e}")
        return False

def extract_album_cover():
    """앨범 커버 이미지 URL 추출 (plat_hd div의 background-image 우선)"""
    global driver
    album_cover_url = None

    safe_print("Extracting album cover...")

    try:
        # Method 1: plat_hd div의 background-image에서 추출
        try:
            cover_url = driver.execute_script("""
                var platHd = document.querySelector('div.plat_hd');
                if (platHd) {
                    var style = platHd.getAttribute('style');
                    if (style) {
                        var match = style.match(/background-image:\s*url\(([^)]+)\)/);
                        if (match) {
                            return match[1].replace(/['"]/g, '');
                        }
                    }
                }
                return null;
            """)

            if cover_url:
                album_cover_url = cover_url
                safe_print(f"[Method 1] Found album cover from plat_hd: {album_cover_url[:100]}")
                return album_cover_url
        except Exception as e:
            safe_print(f"[Method 1] Could not find plat_hd background-image: {e}")

        # Method 2: JavaScript로 모든 이미지 찾아서 가장 큰 이미지 선택 (fallback)
        try:
            largest_img = driver.execute_script("""
                var images = document.querySelectorAll('img');
                var largest = null;
                var maxSize = 0;

                for (var i = 0; i < images.length; i++) {
                    var img = images[i];
                    var size = img.naturalWidth * img.naturalHeight;

                    if (size > 10000 && size > maxSize) {
                        maxSize = size;
                        largest = img;
                    }
                }

                return largest ? largest.src : null;
            """)

            if largest_img:
                album_cover_url = largest_img
                safe_print(f"[Method 2] Found album cover from largest img: {album_cover_url[:100]}")
                return album_cover_url
        except Exception as e:
            safe_print(f"[Method 2] Could not find largest image: {e}")

    except Exception as e:
        safe_print(f"Error extracting album cover: {e}")

    return album_cover_url


def extract_global_platforms():
    """글로벌 플랫폼 링크 추출 (개선된 버전)"""
    global driver
    platforms = {}

    safe_print("Extracting global platform links...")

    # DEBUG: 현재 페이지 정보 로깅
    current_url = driver.current_url
    page_title = driver.title
    safe_print(f"[DEBUG] Current URL: {current_url}")
    safe_print(f"[DEBUG] Page title: {page_title}")

    # 페이지가 완전히 로드될 때까지 대기 (증가된 시간)
    safe_print("[DEBUG] Waiting for page to fully load (10 seconds)...")
    time.sleep(10)

    # DEBUG: 페이지 소스 저장
    try:
        page_html = driver.page_source
        safe_print(f"[DEBUG] Page HTML length: {len(page_html)} characters")

        # 디버그 파일 저장
        with open('debug_platform_page.html', 'w', encoding='utf-8') as f:
            f.write(page_html)
        safe_print("[DEBUG] Platform page HTML saved to debug_platform_page.html")

        # 페이지 내용 미리보기
        safe_print(f"[DEBUG] Page HTML preview (first 500 chars): {page_html[:500]}")
    except Exception as e:
        safe_print(f"[DEBUG] Could not save page HTML: {e}")

    # JavaScript 실행으로 모든 링크 수집
    try:
        all_links = driver.execute_script("""
            var links = [];
            var allElements = document.querySelectorAll('a, button, div[onclick], span[onclick]');

            for (var i = 0; i < allElements.length; i++) {
                var elem = allElements[i];
                var href = elem.href || elem.getAttribute('data-href') || '';
                var onclick = elem.getAttribute('onclick') || '';
                var text = elem.innerText || elem.textContent || '';

                // 플랫폼 링크 패턴 확인
                if (href || onclick) {
                    links.push({
                        href: href,
                        onclick: onclick,
                        text: text,
                        tagName: elem.tagName,
                        className: elem.className
                    });
                }
            }
            return links;
        """)

        safe_print(f"Found {len(all_links)} total clickable elements")

        # DEBUG: 첫 10개 요소 로깅
        safe_print(f"[DEBUG] First 10 elements found:")
        for i, link_info in enumerate(all_links[:10]):
            href = link_info.get('href', '')[:100]  # Truncate to 100 chars
            onclick = link_info.get('onclick', '')[:100]
            text = link_info.get('text', '')[:50]
            safe_print(f"  [{i+1}] tag={link_info.get('tagName')}, text='{text}', href='{href}', onclick='{onclick}'")

        # 플랫폼 매핑 (확장)
        platform_patterns = {
            'spotify': ['spotify.com', 'open.spotify', 'spo'],
            'applemusic': ['music.apple', 'apple.com', 'itm', 'apm'],
            'youtube': ['youtube.com', 'youtu.be', 'yat', 'ytb'],
            'youtubemusic': ['music.youtube', 'ytm'],
            'deezer': ['deezer.com', 'dee'],
            'tidal': ['tidal.com', 'asp', 'tid'],
            'amazonmusic': ['music.amazon', 'amazon.com', 'ama', 'amz'],
            'pandora': ['pandora.com', 'pdx', 'pan'],
            'anghami': ['anghami.com', 'ang'],
            'boomplay': ['boomplay.com', 'boo'],
            'kkbox': ['kkbox.com', 'kkb'],
            'linemusic': ['line.me', 'music.line', 'lmj', 'lnm'],
            'qqmusic': ['y.qq.com', 'qq.com', 'tct'],
            'moov': ['moov.hk', 'mov'],
            'awa': ['awa.fm', 'awm'],
            'qobuz': ['qobuz.com', 'qob']
        }

        # onclick 패턴에서 URL 추출
        for link_info in all_links:
            href = link_info.get('href', '')
            onclick = link_info.get('onclick', '')
            text = link_info.get('text', '').lower()

            # onclick에서 URL 추출
            if onclick and 'click_platform' in onclick:
                match = re.search(r"click_platform\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]", onclick)
                if match:
                    platform_url = match.group(1)
                    platform_code = match.group(2)

                    # 플랫폼 식별
                    for platform_name, patterns in platform_patterns.items():
                        for pattern in patterns:
                            if pattern in platform_url.lower() or platform_code.lower() in patterns:
                                platforms[platform_name] = platform_url
                                safe_print(f"Found {platform_name}: {platform_url}")
                                break

            # 직접 href 확인
            elif href:
                for platform_name, patterns in platform_patterns.items():
                    for pattern in patterns:
                        if pattern in href.lower():
                            platforms[platform_name] = href
                            safe_print(f"Found {platform_name}: {href}")
                            break

        # 추가 시도: iframe 확인
        try:
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            if iframes:
                safe_print(f"Found {len(iframes)} iframes")
                for iframe in iframes:
                    driver.switch_to.frame(iframe)
                    iframe_links = driver.find_elements(By.TAG_NAME, 'a')
                    for link in iframe_links:
                        href = link.get_attribute('href')
                        if href:
                            for platform_name, patterns in platform_patterns.items():
                                for pattern in patterns:
                                    if pattern in href.lower():
                                        platforms[platform_name] = href
                                        safe_print(f"Found in iframe - {platform_name}: {href}")
                                        break
                    driver.switch_to.default_content()
        except:
            pass

    except Exception as e:
        safe_print(f"Error extracting platforms: {e}")

    safe_print(f"Total global platforms found: {len(platforms)}")
    return platforms

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'companion-api-fixed',
        'selenium_hub': SELENIUM_HUB,
        'features': 'Global + KR platforms (Fixed)',
        'version': '2.0'
    })

@app.route('/search', methods=['POST'])
def search_album():
    """Search album on companion.global and Korean platforms"""
    global driver

    # Debug info
    debug_steps = []

    try:
        data = request.get_json()
        artist = data.get('artist', '')
        album_title = data.get('album', '')
        cdma_code = data.get('cdma', '')

        # Fix Korean encoding
        if isinstance(artist, str):
            artist = artist.encode('utf-8').decode('utf-8')
        if isinstance(album_title, str):
            album_title = album_title.encode('utf-8').decode('utf-8')

        debug_steps.append(f"✓ Received request: artist='{artist}', album='{album_title}', cdma='{cdma_code}'")
        safe_print(f"Searching: {artist} - {album_title} (CDMA: {cdma_code})")
    except Exception as e:
        debug_steps.append(f"✗ Request parsing failed: {e}")
        return jsonify({
            'success': False,
            'data': {},
            'debug': debug_steps,
            'error': f'Request parsing error: {e}'
        })

    result = {
        'success': False,
        'platforms': {},
        'kr_platforms': {},
        'album_cover_url': None,
        'platform_count': 0
    }

    # 1. 먼저 국내 플랫폼 검색
    try:
        debug_steps.append("→ Starting KR platform search...")
        kr_results = search_kr_platforms(artist, album_title)
        if kr_results:
            result['kr_platforms'] = kr_results
            debug_steps.append(f"✓ KR platforms found: {len(kr_results)} ({', '.join(kr_results.keys())})")
            safe_print(f"KR platforms found: {len(kr_results)}")
        else:
            debug_steps.append("✗ No KR platforms found")
    except Exception as e:
        debug_steps.append(f"✗ KR search error: {e}")

    # 2. Companion.global 검색 (Selenium 사용)
    try:
        debug_steps.append("→ Starting Companion.global login...")
        if login_to_companion():
            debug_steps.append("✓ Login successful")
            safe_print("Login successful")

            # Navigate to catalog page
            debug_steps.append("→ Navigating to catalog page...")
            safe_print("Navigating to catalog page...")
            driver.get("http://companion.global/catalog?init=Y")
            time.sleep(5)  # Increased wait time

            # Debug: Check current page
            current_url = driver.current_url
            page_title = driver.title
            debug_steps.append(f"→ Current URL: {current_url}")
            debug_steps.append(f"→ Page title: {page_title}")

            # Save page source for debugging
            try:
                with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                debug_steps.append("→ Page source saved to debug_page_source.html")
            except Exception as e:
                debug_steps.append(f"→ Could not save page source: {e}")

            debug_steps.append("✓ Catalog page loaded")

            # Find search input (updated selector)
            search_input = driver.find_element(By.ID, "search_text")
            debug_steps.append("✓ Found search input (#search_text)")
            safe_print("Found search input")

            # Enter search query - use CDMA code if available
            search_query = cdma_code if cdma_code else album_title
            search_input.clear()
            search_input.send_keys(search_query)
            debug_steps.append(f"✓ Entered search query: '{search_query}' {'(CDMA code)' if cdma_code else '(album title)'}")
            safe_print(f"Entered search query: {search_query}{' (CDMA)' if cdma_code else ''}")

            # Verify search input has value
            time.sleep(1)
            search_value = driver.execute_script("return document.getElementById('search_text').value;")
            debug_steps.append(f"→ Search input contains: '{search_value}'")
            safe_print(f"Search value: {search_value}")

            # Execute search using JavaScript function
            driver.execute_script("catalog.search();")
            debug_steps.append("✓ Executed catalog.search()")
            safe_print("Executed search")

            # Wait for loading indicator and search results
            safe_print("Waiting for search to complete (checking loading div)...")

            try:
                loading_div = driver.find_element(By.CSS_SELECTOR, "div.loading")
                debug_steps.append("→ Loading div found")

                # Step 1: Wait for loading to APPEAR (display not none)
                debug_steps.append("→ Waiting for loading to appear...")
                loading_appeared = False
                for i in range(10):  # Wait up to 10 seconds for loading to appear
                    try:
                        style_attr = loading_div.get_attribute("style")
                        if style_attr and not ("display: none" in style_attr or "display:none" in style_attr):
                            debug_steps.append(f"✓ Loading appeared after {i+1} seconds")
                            loading_appeared = True
                            break
                    except:
                        pass
                    time.sleep(1)

                if not loading_appeared:
                    debug_steps.append("⚠ Loading did not appear in 10s, maybe already finished")

                # Step 2: Wait for loading to DISAPPEAR (display none)
                debug_steps.append("→ Waiting for loading to disappear...")
                for i in range(30):  # Wait up to 30 seconds for loading to disappear
                    try:
                        style_attr = loading_div.get_attribute("style")
                        if style_attr and ("display: none" in style_attr or "display:none" in style_attr):
                            debug_steps.append(f"✓ Loading disappeared after {i+1} seconds")
                            safe_print(f"Loading completed in {i+1}s")
                            break
                    except:
                        # Element might be removed from DOM
                        debug_steps.append(f"✓ Loading element removed after {i+1} seconds")
                        break
                    time.sleep(1)
                else:
                    debug_steps.append("⚠ Loading did not disappear in 30s, continuing anyway...")

                # Wait for DOM to stabilize
                time.sleep(2)

            except:
                # No loading div found, use fixed wait
                debug_steps.append("→ No loading div found, using fixed 7s wait")
                time.sleep(7)

            debug_steps.append("✓ Search wait completed")

            # Find album rows
            album_rows = driver.find_elements(By.CSS_SELECTOR, "tr.album_row, table tbody tr")
            debug_steps.append(f"→ Found {len(album_rows)} album rows")
            safe_print(f"Found {len(album_rows)} album rows")

            if album_rows:
                debug_steps.append("→ Processing first album row...")
                # Get platforms from first matching album
                first_row = album_rows[0]

                # Find Platform Link - look for /catalog/platform/ href
                platform_link_element = None
                platform_link = None

                links = first_row.find_elements(By.TAG_NAME, 'a')
                debug_steps.append(f"→ Found {len(links)} links in first row")

                for idx, link in enumerate(links):
                    href = link.get_attribute('href')

                    if href:
                        debug_steps.append(f"  Link {idx+1}: {href[:100]}")

                        if '/catalog/platform/' in href:
                            platform_link_element = link
                            platform_link = href if href.startswith('http') else f"https://companion.global{href}"
                            debug_steps.append(f"✓ Found platform link: {platform_link}")
                            break

                if platform_link:
                    debug_steps.append(f"✓ Constructed platform link: {platform_link}")
                    safe_print(f"Found platform link: {platform_link}")
                    driver.get(platform_link)

                    # Wait for smart link page to load - use increased fixed wait
                    safe_print("Waiting for smart link page to fully load...")
                    time.sleep(7)  # Increased wait time for page and JavaScript to load
                    debug_steps.append("✓ Smart link page wait completed")

                    # 앨범 커버 추출
                    debug_steps.append("→ Extracting album cover...")
                    album_cover_url = extract_album_cover()
                    if album_cover_url:
                        result['album_cover_url'] = album_cover_url
                        debug_steps.append(f"✓ Album cover found: {album_cover_url[:100]}")
                    else:
                        debug_steps.append("✗ No album cover found")

                    # 글로벌 플랫폼 추출
                    debug_steps.append("→ Extracting global platforms...")
                    global_platforms = extract_global_platforms()
                    result['platforms'] = global_platforms
                    debug_steps.append(f"✓ Extracted {len(global_platforms)} global platforms")
                else:
                    debug_steps.append("✗ No platform link found in album row")
            else:
                debug_steps.append("✗ No album rows found in search results")

            result['platform_count'] = len(result['platforms']) + len(result['kr_platforms'])
            result['success'] = True
            debug_steps.append(f"✓ Search completed: {result['platform_count']} total platforms")

        else:
            debug_steps.append("✗ Login failed")
            safe_print("Login failed")
            result['error'] = 'Login failed'

    except Exception as e:
        debug_steps.append(f"✗ Error during search: {e}")
        safe_print(f"Error during search: {e}")
        result['error'] = str(e)

    safe_print(f"Found {len(result['platforms'])} global + {len(result['kr_platforms'])} KR platforms")

    # Return combined results with debug info
    response = {
        'success': result['success'],
        'data': {
            'platforms': result['platforms'],
            'kr_platforms': result['kr_platforms'],
            'album_cover_url': result['album_cover_url'],
            'platform_count': result['platform_count']
        },
        'request': {
            'artist': artist,
            'album': album_title
        },
        'debug': debug_steps
    }

    if 'error' in result:
        response['error'] = result['error']

    return jsonify(response)

if __name__ == '__main__':
    safe_print("Starting Fixed Companion API (Global + KR)...")
    safe_print(f"Selenium Hub: {SELENIUM_HUB}")
    safe_print("Version: 2.0 - Improved global platform extraction")

    # Flask 서버 시작 (포트 5001)
    app.run(host='0.0.0.0', port=5001, debug=False)