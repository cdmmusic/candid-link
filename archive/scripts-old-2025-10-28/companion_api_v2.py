#!/usr/bin/env python3
"""
Companion.global Selenium 자동화 API (V2 - 재작성)
Flask 서버로 앨범 검색 요청을 받아 Selenium으로 처리
"""

from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time
import os
import sys

app = Flask(__name__)

# Selenium 설정
SELENIUM_HUB = os.environ.get('SELENIUM_HUB', 'http://localhost:4444')

# Companion.global 로그인 정보
COMPANION_USERNAME = os.environ.get('COMPANION_USERNAME', 'candidmusic')
COMPANION_PASSWORD = os.environ.get('COMPANION_PASSWORD', 'dkfvfk2-%!#')

# 전역 드라이버 (로그인 상태 유지)
global_driver = None

def log(msg):
    """로그 출력 (즉시 flush)"""
    print(f"[Companion API V2] {msg}")
    sys.stdout.flush()

def get_driver():
    """Selenium WebDriver 생성"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    driver = webdriver.Remote(
        command_executor=SELENIUM_HUB,
        options=chrome_options
    )
    driver.set_page_load_timeout(30)
    return driver

def login_to_companion(driver):
    """Companion.global 로그인"""
    log("Starting login process...")

    # 로그인 페이지로 이동
    driver.get('http://companion.global/login')
    time.sleep(2)
    log(f"Loaded login page: {driver.current_url}")

    # 사용자명 입력
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'username'))
    )
    username_input.clear()
    username_input.send_keys(COMPANION_USERNAME)
    log(f"Entered username: {COMPANION_USERNAME}")

    # 비밀번호 입력
    password_input = driver.find_element(By.NAME, 'password')
    password_input.clear()
    password_input.send_keys(COMPANION_PASSWORD)
    log("Entered password")

    # 로그인 버튼 클릭
    login_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    login_btn.click()
    log("Clicked login button")

    # 대시보드 페이지 로딩 대기
    time.sleep(3)
    log(f"After login, URL: {driver.current_url}")
    log(f"Page title: {driver.title}")

    if 'dashboard' in driver.current_url.lower() or 'dashboard' in driver.title.lower():
        log("Login successful")
        return True
    else:
        log("Login may have failed")
        return False

def search_album(driver, cdma_code):
    """
    CDMA 코드로 앨범 검색
    매번 catalog 페이지를 새로 로드하여 깨끗한 상태에서 검색
    """
    log(f"="*60)
    log(f"Searching for CDMA code: {cdma_code}")

    # 1. Catalog 페이지 새로 로드 (캐시 방지)
    import random
    timestamp = int(time.time() * 1000) + random.randint(0, 999)
    catalog_url = f'http://companion.global/catalog?init=Y&t={timestamp}'
    log(f"Loading fresh catalog page: {catalog_url}")
    driver.get(catalog_url)
    time.sleep(3)

    # 2. 검색 입력 필드 찾기
    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'search_text'))
        )
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'search_text'))
        )
        log("Found search input field")
    except TimeoutException:
        log("ERROR: Could not find search input field")
        return None

    # 3. 검색어 입력 (기존 값 완전히 제거 후)
    log(f"Clearing search field and entering: {cdma_code}")
    search_input.click()
    search_input.send_keys(Keys.CONTROL + "a")  # 전체 선택
    search_input.send_keys(Keys.DELETE)  # 삭제
    time.sleep(0.3)

    # CDMA 코드 타이핑
    for char in cdma_code:
        search_input.send_keys(char)
        time.sleep(0.05)  # 천천히 타이핑

    time.sleep(0.5)

    # 실제 입력된 값 확인
    actual_value = search_input.get_attribute('value')
    log(f"Value in search field: '{actual_value}'")

    if actual_value != cdma_code:
        log(f"WARNING: Search value mismatch! Expected '{cdma_code}', got '{actual_value}'")

    # 4. 검색 버튼 클릭
    log("Clicking search button...")
    try:
        search_btn = driver.find_element(By.CSS_SELECTOR, '.btn_sch')
        search_btn.click()
        log("Clicked search button")
    except Exception as e:
        log(f"Could not click search button: {e}")
        log("Trying ENTER key instead...")
        search_input.send_keys(Keys.RETURN)

    # 5. 검색 결과 테이블이 업데이트될 때까지 대기
    log("Waiting for search results to update...")
    time.sleep(3)

    # 기존 테이블 행 개수 확인
    old_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
    log(f"Current rows before wait: {len(old_rows)}")

    # 테이블이 재로드될 때까지 대기 (최대 10초)
    for i in range(10):
        time.sleep(1)
        new_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        if len(new_rows) != len(old_rows):
            log(f"Table updated! New row count: {len(new_rows)}")
            break
        if i == 9:
            log("Warning: Table did not update after 10 seconds")

    time.sleep(2)  # 추가 안정화 대기

    # 6. 검색 결과에서 앨범 행 찾기
    try:
        album_rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        log(f"Found {len(album_rows)} result rows")

        if len(album_rows) == 0:
            log("No results found")
            return None

        # 7. 각 행의 UPC/CDMA 컬럼에서 정확한 매칭 찾기
        log(f"Searching for exact CDMA match: {cdma_code}")
        for idx, row in enumerate(album_rows, 1):
            try:
                tds = row.find_elements(By.TAG_NAME, 'td')
                if len(tds) < 4:
                    continue

                # UPC/Catalog No 컬럼 (보통 4번째 컬럼, index 3)
                upc_text = tds[3].text.strip()

                # 정확한 CDMA 매칭 체크
                if upc_text == cdma_code or upc_text.endswith(f" / {cdma_code}") or upc_text.endswith(f"/{cdma_code}"):
                    album_name = tds[1].text.strip() if len(tds) > 1 else ""
                    artist_name = tds[2].text.strip() if len(tds) > 2 else ""

                    log(f"✓ EXACT MATCH found at row {idx}")
                    log(f"  Artist: {artist_name}")
                    log(f"  Album: {album_name}")
                    log(f"  UPC: {upc_text}")

                    return row
            except Exception as e:
                log(f"Error checking row {idx}: {e}")
                continue

        log(f"ERROR: CDMA code '{cdma_code}' not found in search results")
        log("First 5 rows UPC values:")
        for idx, row in enumerate(album_rows[:5], 1):
            try:
                tds = row.find_elements(By.TAG_NAME, 'td')
                if len(tds) >= 4:
                    upc_text = tds[3].text.strip()
                    log(f"  Row {idx}: {upc_text}")
            except:
                pass

        return None

    except Exception as e:
        log(f"ERROR finding album rows: {e}")
        return None

def extract_platform_links(driver, album_row):
    """앨범 행에서 Smart Link 페이지로 이동하여 플랫폼 링크 추출"""
    # 플랫폼 코드 -> 이름 매핑
    PLATFORM_NAMES = {
        'spo': 'Spotify',
        'itm': 'Apple Music',
        'yat': 'YouTube Music',
        'ang': 'Anghami',
        'dee': 'Deezer',
        'pdx': 'Pandora',
        'lmj': 'LINE MUSIC (JP)',
        'lmt': 'LINE MUSIC (TW)',
        'lmk': 'LINE MUSIC (KR)',
        'lmu': 'LINE MUSIC',
        'asp': 'TIDAL',
        'ama': 'Amazon Music',
        'kkb': 'KKBOX',
        'awa': 'AWA',
        'awm': 'AWA',
        'qom': 'QQ Music',
        'tct': 'QQ Music',
        'mov': 'MOOV',
        'moo': 'MOOV'
    }

    try:
        # Smart Link 버튼 찾기
        smart_link = album_row.find_element(By.CSS_SELECTOR, 'a[href*="/catalog/platform/"]')
        smart_link_url = smart_link.get_attribute('href')
        log(f"Found Smart Link: {smart_link_url}")

        # Smart Link 페이지로 이동
        driver.get(smart_link_url)
        time.sleep(3)
        log(f"Loaded Smart Link page: {driver.current_url}")

        # 플랫폼 목록 추출
        platforms = []
        platform_items = driver.find_elements(By.CSS_SELECTOR, '#platList li')
        log(f"Found {len(platform_items)} platform list items")

        for idx, li_item in enumerate(platform_items, 1):
            try:
                # <a> 태그 찾기
                link_elem = li_item.find_element(By.CSS_SELECTOR, 'a')

                # onclick 속성에서 URL 추출
                onclick_attr = link_elem.get_attribute('onclick')

                if not onclick_attr:
                    continue

                # onclick="javascript:click_platform("https://...", "num", "191953332284");" 형태에서 URL 추출
                import re
                url_match = re.search(r'click_platform\("([^"]+)"', onclick_attr)
                if not url_match:
                    log(f"  Row {idx}: Could not extract URL from onclick: {onclick_attr[:100]}")
                    continue

                platform_url = url_match.group(1).replace('\\/', '/')  # Unescape slashes

                # 플랫폼 코드 추출 (class명에서)
                platform_code = None
                try:
                    platform_name_elem = li_item.find_element(By.CSS_SELECTOR, 'span[class*="logo_"]')
                    classes = platform_name_elem.get_attribute('class').split()
                    for cls in classes:
                        if cls.startswith('logo_'):
                            platform_code = cls.replace('logo_', '')
                            break
                except:
                    pass

                # 코드 기반으로 플랫폼 이름 찾기
                if platform_code and platform_code in PLATFORM_NAMES:
                    platform_name = PLATFORM_NAMES[platform_code]
                else:
                    # URL에서 플랫폼 추측
                    if 'spotify' in platform_url:
                        platform_code = 'spo'
                        platform_name = 'Spotify'
                    elif 'apple.com' in platform_url:
                        platform_code = 'itm'
                        platform_name = 'Apple Music'
                    elif 'youtube' in platform_url:
                        platform_code = 'yat'
                        platform_name = 'YouTube Music'
                    elif 'deezer' in platform_url:
                        platform_code = 'dee'
                        platform_name = 'Deezer'
                    elif 'tidal' in platform_url:
                        platform_code = 'asp'
                        platform_name = 'TIDAL'
                    elif 'amazon' in platform_url:
                        platform_code = 'ama'
                        platform_name = 'Amazon Music'
                    elif 'qq.com' in platform_url:
                        platform_code = 'qom'
                        platform_name = 'QQ Music'
                    elif 'line.me' in platform_url:
                        platform_code = 'lmj'
                        platform_name = 'LINE MUSIC'
                    else:
                        platform_code = 'unknown'
                        platform_name = 'Unknown'

                if platform_url:
                    platforms.append({
                        'platform_code': platform_code or 'unknown',
                        'platform_name': platform_name,
                        'platform_url': platform_url
                    })
                    log(f"  ✓ {platform_name} ({platform_code}): {platform_url}")
            except Exception as e:
                log(f"  Error extracting platform from row {idx}: {e}")
                continue

        return platforms

    except Exception as e:
        log(f"ERROR extracting platform links: {e}")
        return []

@app.route('/search', methods=['POST'])
def search():
    """앨범 검색 API 엔드포인트"""
    global global_driver

    try:
        data = request.get_json()
        artist = data.get('artist', '')
        album = data.get('album', '')
        upc = data.get('upc', '')  # CDMA 코드

        log(f"Received search request: artist={artist}, album={album}, upc={upc}")

        if not upc:
            return jsonify({
                'success': False,
                'error': 'CDMA code (upc) is required'
            })

        # 드라이버 초기화 (처음 한 번만)
        if global_driver is None:
            log("Initializing WebDriver...")
            global_driver = get_driver()
            if not login_to_companion(global_driver):
                return jsonify({
                    'success': False,
                    'error': 'Login failed'
                })

        # CDMA 코드로 검색
        album_row = search_album(global_driver, upc)

        if album_row is None:
            return jsonify({
                'success': False,
                'error': f'Album with CDMA code "{upc}" not found in search results',
                'data': None
            })

        # 플랫폼 링크 추출
        platforms = extract_platform_links(global_driver, album_row)

        if len(platforms) == 0:
            return jsonify({
                'success': False,
                'error': 'No platforms found for this album',
                'data': None
            })

        log(f"✓ Successfully collected {len(platforms)} platforms for {upc}")

        return jsonify({
            'success': True,
            'data': {
                'artist': artist,
                'album': album,
                'upc': upc,
                'platforms': platforms
            }
        })

    except Exception as e:
        log(f"ERROR in search endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("="*60)
    print("Starting Companion API V2...")
    print(f"Selenium Hub: {SELENIUM_HUB}")
    print("="*60)

    port = int(os.environ.get('COMPANION_API_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
