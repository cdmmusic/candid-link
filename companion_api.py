#!/usr/bin/env python3
"""
Companion.global Selenium 자동화 API + KR 플랫폼 수집
Flask 서버로 앨범 검색 요청을 받아 Selenium으로 처리
"""

from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import re
from urllib.parse import quote

app = Flask(__name__)

# Selenium 설정
SELENIUM_HUB = os.environ.get('SELENIUM_HUB', 'http://localhost:4444')

# Companion.global 로그인 정보
COMPANION_USERNAME = os.environ.get('COMPANION_USERNAME', 'candidmusic')
COMPANION_PASSWORD = os.environ.get('COMPANION_PASSWORD', 'dkfvfk2-%!#')

def get_driver():
    """Selenium WebDriver 생성"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    # Remote WebDriver 사용 (Selenium Hub)
    driver = webdriver.Remote(
        command_executor=SELENIUM_HUB,
        options=chrome_options
    )

    return driver

def login_to_companion(driver):
    """Companion.global (FLUXUS)에 로그인"""
    import sys

    def safe_flush():
        try:
            sys.stdout.flush()
        except (BrokenPipeError, OSError):
            pass

    try:
        print("[Companion API] Starting login process...")
        safe_flush()

        # 로그인 페이지 접속
        driver.get('http://companion.global')
        print(f"[Companion API] Loaded login page: {driver.current_url}")
        safe_flush()

        # Username 입력
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        username_input.clear()
        username_input.send_keys(COMPANION_USERNAME)
        print(f"[Companion API] Entered username: {COMPANION_USERNAME}")
        safe_flush()

        # Password 입력
        password_input = driver.find_element(By.ID, 'password')
        password_input.clear()
        password_input.send_keys(COMPANION_PASSWORD)
        print("[Companion API] Entered password")
        safe_flush()

        # 로그인 버튼 클릭
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], .btn_login')
        login_button.click()
        print("[Companion API] Clicked login button")
        safe_flush()

        # 로그인 완료 대기 (dashboard 페이지로 리다이렉트 확인)
        time.sleep(5)
        print(f"[Companion API] After login, URL: {driver.current_url}")
        print(f"[Companion API] Page title: {driver.title}")
        safe_flush()

        # 로그인 실패 체크 (error=true가 있거나 여전히 login 페이지면)
        if 'error=true' in driver.current_url or '/login' in driver.current_url:
            print("[Companion API] Login failed - still on login page or error detected")
            safe_flush()
            # DEBUG: Save error page
            with open('/tmp/login_error.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("[Companion API] Saved error page to /tmp/login_error.html")
            return False

        # Dashboard 페이지 확인
        if '/dashboard' in driver.current_url:
            print("[Companion API] Successfully reached dashboard")
        else:
            print(f"[Companion API] Unexpected page after login: {driver.current_url}")

        # DEBUG: Save page source
        with open('/tmp/after_login.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("[Companion API] Saved page source to /tmp/after_login.html")
        safe_flush()

        print("[Companion API] Login successful")
        safe_flush()
        return True

    except Exception as e:
        import traceback
        print(f"[Companion API] Login failed: {str(e)}")
        print(traceback.format_exc())
        safe_flush()
        return False

def search_kr_platforms(driver, artist, album):
    """한국 플랫폼에서 앨범 검색 (Selenium 사용)"""
    import sys

    def safe_flush():
        try:
            sys.stdout.flush()
        except (BrokenPipeError, OSError):
            pass

    results = {}
    album_cover_url = None
    query = f"{artist} {album}"

    print(f"[KR Search] Starting KR platform search: {query}")
    safe_flush()

    # 1. 멜론 (requests로 충분)
    try:
        print(f"[KR Search] Searching Melon...")
        safe_flush()
        url = f"https://www.melon.com/search/total/index.htm?q={quote(query)}&section=&searchGnbYn=Y&kkoSpl=N&kkoDpType="
        driver.get(url)
        time.sleep(2)

        page_source = driver.page_source
        matches = re.findall(r'goAlbumDetail\(\'(\d+)\'\)', page_source)
        if matches:
            results['melon'] = f"https://www.melon.com/album/detail.htm?albumId={matches[0]}"
            print(f"[KR Search] ✓ Melon: {results['melon']}")
        else:
            print(f"[KR Search] ✗ Melon: Not found")
        safe_flush()
    except Exception as e:
        print(f"[KR Search] ✗ Melon error: {str(e)}")
        safe_flush()

    # 2. 벅스 (+ 앨범 커버)
    try:
        print(f"[KR Search] Searching Bugs...")
        safe_flush()
        url = f"https://music.bugs.co.kr/search/integrated?q={quote(query)}"
        driver.get(url)
        time.sleep(2)

        page_source = driver.page_source
        matches = re.findall(r'/album/(\d+)', page_source)
        if matches:
            album_id = matches[0]
            results['bugs'] = f"https://music.bugs.co.kr/album/{album_id}"
            print(f"[KR Search] ✓ Bugs: {results['bugs']}")

            # 앨범 커버 가져오기
            try:
                driver.get(f"https://music.bugs.co.kr/album/{album_id}")
                time.sleep(1)
                cover_matches = re.findall(r'<meta property="og:image" content="([^"]+)"', driver.page_source)
                if cover_matches:
                    album_cover_url = cover_matches[0]
                    print(f"[KR Search] ✓ Album cover found")
            except Exception as e:
                print(f"[KR Search] ⚠ Album cover error: {str(e)}")
        else:
            print(f"[KR Search] ✗ Bugs: Not found")
        safe_flush()
    except Exception as e:
        print(f"[KR Search] ✗ Bugs error: {str(e)}")
        safe_flush()

    # 3. VIBE
    try:
        print(f"[KR Search] Searching VIBE...")
        safe_flush()
        url = f"https://vibe.naver.com/search?query={quote(query)}"
        driver.get(url)
        time.sleep(3)  # JavaScript 렌더링 대기

        # 앨범 링크 찾기
        try:
            album_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/album/"]')
            if album_links:
                href = album_links[0].get_attribute('href')
                if href:
                    results['vibe'] = href
                    print(f"[KR Search] ✓ VIBE: {results['vibe']}")
                else:
                    print(f"[KR Search] ✗ VIBE: Link found but no href")
            else:
                print(f"[KR Search] ✗ VIBE: Not found")
        except Exception as e:
            print(f"[KR Search] ✗ VIBE element error: {str(e)}")
        safe_flush()
    except Exception as e:
        print(f"[KR Search] ✗ VIBE error: {str(e)}")
        safe_flush()

    # 4. FLO
    try:
        print(f"[KR Search] Searching FLO...")
        safe_flush()
        url = f"https://www.music-flo.com/search/all?keyword={quote(query)}"
        driver.get(url)
        time.sleep(3)  # JavaScript 렌더링 대기

        # 앨범 링크 찾기
        try:
            album_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/detail/album/"]')
            if album_links:
                href = album_links[0].get_attribute('href')
                if href:
                    results['flo'] = href
                    print(f"[KR Search] ✓ FLO: {results['flo']}")
                else:
                    print(f"[KR Search] ✗ FLO: Link found but no href")
            else:
                print(f"[KR Search] ✗ FLO: Not found")
        except Exception as e:
            print(f"[KR Search] ✗ FLO element error: {str(e)}")
        safe_flush()
    except Exception as e:
        print(f"[KR Search] ✗ FLO error: {str(e)}")
        safe_flush()

    # 5. 지니뮤직
    try:
        print(f"[KR Search] Searching Genie...")
        safe_flush()
        url = f"https://www.genie.co.kr/search/searchMain?query={quote(query)}"
        driver.get(url)
        time.sleep(3)  # JavaScript 렌더링 대기

        # onclick 속성이 있는 앨범 링크 찾기
        try:
            album_links = driver.find_elements(By.CSS_SELECTOR, 'a[onclick*="fnViewAlbumLayer"]')
            if album_links:
                onclick = album_links[0].get_attribute('onclick')
                if onclick:
                    # fnViewAlbumLayer('앨범ID') 형식에서 ID 추출
                    match = re.search(r"fnViewAlbumLayer\('(\d+)'\)", onclick)
                    if match:
                        album_id = match.group(1)
                        results['genie'] = f"https://www.genie.co.kr/detail/albumInfo?axnm={album_id}"
                        print(f"[KR Search] ✓ Genie: {results['genie']}")
                    else:
                        print(f"[KR Search] ✗ Genie: onclick parsing failed")
                else:
                    print(f"[KR Search] ✗ Genie: No onclick attribute")
            else:
                print(f"[KR Search] ✗ Genie: Not found")
        except Exception as e:
            print(f"[KR Search] ✗ Genie element error: {str(e)}")
        safe_flush()
    except Exception as e:
        print(f"[KR Search] ✗ Genie error: {str(e)}")
        safe_flush()

    print(f"[KR Search] Completed: {len(results)} platforms found")
    safe_flush()

    return results, album_cover_url

def search_album(artist, album, upc=''):
    """Companion.global에서 앨범 검색"""
    import sys

    def safe_flush():
        try:
            sys.stdout.flush()
        except (BrokenPipeError, OSError):
            pass

    driver = None

    try:
        driver = get_driver()

        # 로그인
        if not login_to_companion(driver):
            return {
                'success': False,
                'error': 'Login failed',
                'data': None
            }

        # Catalog 페이지로 이동 (타임스탬프 추가로 캐시 방지)
        print(f"[Companion API] Navigating to catalog page...")
        import random
        cache_buster = int(time.time() * 1000) + random.randint(0, 9999)
        driver.get(f'http://companion.global/catalog?init=Y&t={cache_buster}')
        time.sleep(3)  # 페이지 로딩 대기 시간 증가
        print(f"[Companion API] Current URL: {driver.current_url}")

        # DEBUG: Save catalog page source
        with open('/tmp/catalog_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("[Companion API] Saved catalog page to /tmp/catalog_page.html")
        safe_flush()

        # 검색창 대기 및 입력
        search_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, 'search_text'))
        )
        # 검색창이 입력 가능한 상태가 될 때까지 대기
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, 'search_text'))
        )
        print(f"[Companion API] Found search input")
        safe_flush()

        # 글로벌 플랫폼 검색: CDMA 코드 우선
        # UPC가 있으면 CDMA 코드로 검색, 없으면 앨범명으로 검색
        target_row = None

        # 텍스트 정규화 함수 (공백, 특수문자 제거)
        def normalize_text(text):
            import re
            if not text:
                return ""
            # 공백과 특수문자 제거, 소문자 변환
            return re.sub(r'[\s\-_,.()\[\]{}]+', '', text.lower())

        # CDMA 코드로 검색 (UPC 파라미터 사용)
        search_query = upc if upc else album

        if search_query:
            print(f"[Companion API] Searching by: {search_query} ({'CDMA' if upc else 'Album'})")
            safe_flush()

            # JavaScript로 직접 검색 필드 값을 설정하고 검색 실행
            print(f"[Companion API] Setting search value via JavaScript: {search_query}")
            safe_flush()

            driver.execute_script("""
                var searchInput = document.getElementById('search_text');
                searchInput.value = arguments[0];
                // input 이벤트 트리거 (JavaScript가 input 변화를 감지하도록)
                var event = new Event('input', { bubbles: true });
                searchInput.dispatchEvent(event);
            """, search_query)

            time.sleep(1)

            # 실제로 입력된 값 확인
            actual_value = search_input.get_attribute('value')
            print(f"[Companion API] Value set in search field: {actual_value}")
            safe_flush()

            # JavaScript로 검색 실행
            driver.execute_script("catalog.search();")
            print(f"[Companion API] Executed catalog.search() via JavaScript")
            safe_flush()

            # 로딩창이 사라질 때까지 대기
            print(f"[Companion API] Waiting for loading screen to disappear...")
            safe_flush()
            try:
                # 로딩 div가 사라질 때까지 대기 (최대 20초)
                wait = WebDriverWait(driver, 20)
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.loading')))
                print(f"[Companion API] Loading screen disappeared")
                safe_flush()
            except TimeoutException:
                print(f"[Companion API] Timeout waiting for loading screen to disappear")
                safe_flush()

            # 로딩 완료 후 추가 2초 대기 (데이터 렌더링 완료)
            print(f"[Companion API] Waiting additional 2 seconds for data rendering...")
            safe_flush()
            time.sleep(2)

            print(f"[Companion API] Data loading completed, checking for results...")
            safe_flush()

            # DEBUG: Save search results
            with open('/tmp/search_results_primary.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            try:
                album_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
                print(f"[Companion API] Found {len(album_rows)} album rows")
                safe_flush()

                if len(album_rows) > 0:
                    # 1차: CDMA/UPC 코드로 검색한 경우 정확히 매칭되는 것 찾기
                    if upc:
                        print(f"[Companion API] Searching for exact CDMA match: {upc}")
                        safe_flush()
                        for row in album_rows:
                            try:
                                tds = row.find_elements(By.TAG_NAME, 'td')
                                if len(tds) > 3:
                                    # UPC/Catalog No 컬럼 (index 3)
                                    upc_cell = tds[3]
                                    upc_text = upc_cell.text.strip()

                                    print(f"[Companion API] Checking UPC: {upc_text}")
                                    safe_flush()

                                    # 정확한 CDMA 매칭: 전체가 일치하거나 "/ CDMA코드" 형태
                                    if upc == upc_text or upc_text.endswith(f" / {upc}") or upc_text.endswith(f"/ {upc}"):
                                        print(f"[Companion API] Exact match found: {upc_text}")
                                        safe_flush()
                                        target_row = row
                                        break
                            except:
                                continue

                    # 2차: 앨범명으로 검색하거나 CDMA 매칭 실패시 앨범명+아티스트명으로 매칭
                    if not target_row and album:
                        # 앨범명으로 검색한 경우, 아티스트명 매칭
                        normalized_artist = normalize_text(artist)
                        normalized_album = normalize_text(album)
                        for row in album_rows:
                            try:
                                tds = row.find_elements(By.TAG_NAME, 'td')
                                if len(tds) > 2:
                                    # TD[2]에서 앨범명과 아티스트명 추출
                                    album_cell = tds[2]

                                    # <p> 태그에서 앨범명 추출
                                    try:
                                        album_p = album_cell.find_element(By.TAG_NAME, 'p')
                                        row_album_text = album_p.text.strip()
                                    except:
                                        row_album_text = ""

                                    # catalog_album_title 내부의 <span>에서 아티스트명 추출
                                    try:
                                        title_span = album_cell.find_element(By.CLASS_NAME, 'catalog_album_title')
                                        artist_span = title_span.find_element(By.TAG_NAME, 'span')
                                        row_artist_text = artist_span.text.strip()
                                    except:
                                        row_artist_text = ""

                                    normalized_row_artist = normalize_text(row_artist_text)
                                    normalized_row_album = normalize_text(row_album_text)

                                    print(f"[Companion API] Checking: {row_album_text} / {row_artist_text}")
                                    safe_flush()

                                    # 아티스트와 앨범명 모두 매칭
                                    artist_match = (normalized_artist and normalized_row_artist and
                                                   (normalized_artist in normalized_row_artist or normalized_row_artist in normalized_artist))
                                    album_match = (normalized_album and normalized_row_album and
                                                  (normalized_album in normalized_row_album or normalized_row_album in normalized_album))

                                    if artist_match and album_match:
                                        print(f"[Companion API] Matched! Artist: {row_artist_text}, Album: {row_album_text}")
                                        safe_flush()
                                        target_row = row
                                        break
                            except Exception as e:
                                continue
            except:
                print(f"[Companion API] No results found")
                safe_flush()

        # Fallback: 앨범명 검색 실패 시 아티스트명으로 검색
        if not target_row and not upc and artist:
            print(f"[Companion API] Fallback: Searching by artist name: {artist}")
            safe_flush()

            search_input = driver.find_element(By.ID, 'search_text')
            search_input.clear()
            search_input.send_keys(artist)
            print(f"[Companion API] Entered search query: {artist}")
            safe_flush()

            from selenium.webdriver.common.keys import Keys
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)

            # DEBUG: Save search results
            with open('/tmp/search_results_fallback.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)

            try:
                album_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
                print(f"[Companion API] Found {len(album_rows)} album rows")
                safe_flush()

                normalized_album = normalize_text(album)
                for row in album_rows:
                    try:
                        tds = row.find_elements(By.TAG_NAME, 'td')
                        if len(tds) > 2:
                            album_cell = tds[2]

                            # <p> 태그에서 앨범명 추출
                            try:
                                album_p = album_cell.find_element(By.TAG_NAME, 'p')
                                row_album_text = album_p.text.strip()
                            except:
                                row_album_text = ""

                            normalized_row_album = normalize_text(row_album_text)

                            print(f"[Companion API] Checking: {row_album_text} vs {album}")
                            safe_flush()

                            if not normalized_album or not normalized_row_album:
                                continue

                            if normalized_album in normalized_row_album or normalized_row_album in normalized_album:
                                print(f"[Companion API] Matched album: {row_album_text}")
                                safe_flush()
                                target_row = row
                                break
                    except:
                        continue
            except:
                print(f"[Companion API] No results found in fallback")
                safe_flush()

        # DEBUG: Final search results
        with open('/tmp/search_results.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"[Companion API] Current URL after search: {driver.current_url}")
        safe_flush()

        # 결과 확인
        if not target_row:
            error_msg = f'Album "{album}" by "{artist}" not found in search results'
            print(f"[Companion API] {error_msg}")
            safe_flush()
            return {
                'success': False,
                'error': error_msg,
                'data': None
            }

        # Smart Link 컬럼에서 링크 찾기 (/catalog/platform/ URL)
        print(f"[Companion API] Looking for Smart Link in the row...")
        safe_flush()

        tds = target_row.find_elements(By.TAG_NAME, 'td')
        smart_link_url = None

        # /catalog/platform/ 링크 찾기
        for td in tds:
            try:
                links = td.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/catalog/platform/' in href:
                        smart_link_url = href
                        print(f"[Companion API] Found platform link: {href}")
                        safe_flush()
                        break
                if smart_link_url:
                    break
            except:
                continue

        if not smart_link_url:
            print(f"[Companion API] Smart Link not found, trying to click row...")
            safe_flush()
            # Smart Link를 못 찾으면 행 자체를 클릭
            target_row.click()
            time.sleep(2)
        else:
            print(f"[Companion API] Found Smart Link: {smart_link_url}")
            safe_flush()
            # 상대 경로를 절대 경로로 변환
            if smart_link_url.startswith('/'):
                smart_link_url = f"http://companion.global{smart_link_url}"
            # Smart Link 페이지로 이동
            print(f"[Companion API] Navigating to: {smart_link_url}")
            safe_flush()
            driver.get(smart_link_url)
            time.sleep(3)

        # DEBUG: Save smart link page
        with open('/tmp/smart_link_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"[Companion API] Saved smart link page to /tmp/smart_link_page.html")
        print(f"[Companion API] Current URL: {driver.current_url}")
        safe_flush()

        # 앨범 커버 추출
        album_cover_url = None
        try:
            cover_img = driver.find_element(By.CSS_SELECTOR, 'img.album-cover, img.cover-image, .album-art img, img[alt*="album"], img[alt*="cover"]')
            album_cover_url = cover_img.get_attribute('src')
            print(f"[Companion API] Found album cover: {album_cover_url}")
        except:
            print(f"[Companion API] Album cover not found")
        safe_flush()

        # 플랫폼 링크 추출 - onclick 속성에서 파싱
        platforms = []

        # platList 내의 li 요소들을 찾음
        try:
            platform_items = driver.find_elements(By.CSS_SELECTOR, '#platList li')
            print(f"[Companion API] Found {len(platform_items)} platform items in #platList")
            safe_flush()
        except:
            platform_items = []
            print(f"[Companion API] No #platList found, trying alternative selectors")
            safe_flush()

        # 중복 제거를 위한 set
        seen_urls = set()

        for item in platform_items:
            try:
                # li 안의 a 태그 찾기
                link = item.find_element(By.TAG_NAME, 'a')
                onclick_attr = link.get_attribute('onclick')

                if not onclick_attr:
                    continue

                # onclick="javascript:click_platform("http://music.apple.com/...", "itm", "...")"
                # 정규식으로 URL과 platform code 추출
                import re
                match = re.search(r'click_platform\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']', onclick_attr)
                if not match:
                    continue

                url = match.group(1).replace('\\/', '/')  # 이스케이프된 슬래시 복원
                platform_code = match.group(2)

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # span 태그에서 플랫폼 이름 추출
                try:
                    span = link.find_element(By.TAG_NAME, 'span')
                    span_class = span.get_attribute('class')
                    # class="logo_itm" -> platform_name from class
                except:
                    span_class = None

                # 플랫폼 이름 매핑
                platform_name = None
                if platform_code == 'spo':
                    platform_name = 'Spotify'
                elif platform_code == 'itm':
                    platform_name = 'Apple Music'
                elif platform_code == 'yat':
                    platform_name = 'YouTube Music'
                elif platform_code == 'ama':
                    platform_name = 'Amazon Music'
                elif platform_code == 'dee':
                    platform_name = 'Deezer'
                elif platform_code == 'asp':
                    platform_name = 'Tidal'
                elif platform_code == 'pdx':
                    platform_name = 'Pandora'
                elif platform_code == 'soc':
                    platform_name = 'SoundCloud'
                elif platform_code == 'awm':
                    platform_name = 'AWA'
                elif platform_code == 'kkb':
                    platform_name = 'KKBOX'
                elif platform_code == 'ang':
                    platform_name = 'Anghami'
                elif platform_code == 'lmj':
                    platform_name = 'LINE MUSIC'
                elif platform_code == 'mov':
                    platform_name = 'MOOV'
                elif platform_code == 'tct':
                    platform_name = 'QQ Music'
                else:
                    platform_name = platform_code.upper()  # Fallback

                platforms.append({
                    'platform': platform_name,
                    'code': platform_code,
                    'url': url,
                    'upc': None  # UPC는 페이지에서 추출 가능하면 추가
                })
                print(f"[Companion API] Added platform: {platform_name} ({platform_code}) - {url}")
                safe_flush()
            except Exception as e:
                print(f"[Companion API] Error parsing platform element: {str(e)}")
                safe_flush()
                continue

        print(f"[Companion API] Total platforms extracted: {len(platforms)}")
        safe_flush()

        # KR 플랫폼 검색 추가
        kr_platforms = {}
        kr_album_cover = album_cover_url  # 기본값은 Global에서 가져온 커버

        try:
            print(f"[Companion API] Starting KR platform search...")
            safe_flush()
            kr_platforms, kr_cover = search_kr_platforms(driver, artist, album)

            # 벅스에서 앨범 커버를 찾았으면 우선 사용
            if kr_cover:
                kr_album_cover = kr_cover

            print(f"[Companion API] KR search completed: {len(kr_platforms)} platforms")
            safe_flush()
        except Exception as e:
            print(f"[Companion API] KR search error: {str(e)}")
            safe_flush()

        return {
            'success': True,
            'data': {
                'album_cover_url': kr_album_cover,
                'platform_count': len(platforms),
                'platforms': platforms,
                'kr_platforms': kr_platforms
            },
            'request': {
                'artist': artist,
                'album': album
            }
        }

    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[Companion API] Error: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'data': None
        }

    finally:
        if driver:
            driver.quit()

@app.route('/health', methods=['GET'])
def health():
    """헬스 체크"""
    return jsonify({
        'status': 'ok',
        'service': 'companion-api',
        'selenium_hub': SELENIUM_HUB
    })

@app.route('/search', methods=['POST'])
def search():
    """앨범 검색 API"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        # 다양한 파라미터 형식 지원
        artist = data.get('artist') or data.get('artist_en') or data.get('artist_ko', '')
        album = data.get('album') or data.get('album_en') or data.get('album_ko', '')
        upc = data.get('upc', '')  # UPC 또는 Catalog No
        cdma_code = data.get('cdma_code', data.get('cdmaCode', ''))

        # CDMA 코드가 있으면 UPC로 사용
        if cdma_code and not upc:
            upc = cdma_code

        # artist + album 또는 upc 중 하나는 있어야 함
        if not ((artist and album) or upc):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: (artist + album) or upc'
            }), 400

        if upc:
            print(f"[Companion API] Searching by UPC/CDMA: {upc}")
        else:
            print(f"[Companion API] Searching: {artist} - {album}")

        result = search_album(artist, album, upc)

        if result['success']:
            print(f"[Companion API] Found {result['data']['platform_count']} platforms")
        else:
            print(f"[Companion API] Failed: {result.get('error')}")

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Companion API...")
    print(f"Selenium Hub: {SELENIUM_HUB}")
    app.run(host='0.0.0.0', port=5001, debug=False)
