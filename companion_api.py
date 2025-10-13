#!/usr/bin/env python3
"""
Companion.global Selenium 자동화 API
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

app = Flask(__name__)

# Selenium 설정
SELENIUM_HUB = os.environ.get('SELENIUM_HUB', 'http://localhost:4444')

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

def search_album(artist, album):
    """Companion.global에서 앨범 검색"""
    driver = None

    try:
        driver = get_driver()

        # Companion.global 접속
        driver.get('https://companion.global')

        # 검색창 대기 및 입력
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"], input[placeholder*="search"], input.search-input'))
        )

        # 검색어 입력
        query = f"{artist} {album}"
        search_input.clear()
        search_input.send_keys(query)

        # 검색 버튼 클릭 또는 엔터
        try:
            search_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], button.search-button')
            search_button.click()
        except:
            from selenium.webdriver.common.keys import Keys
            search_input.send_keys(Keys.RETURN)

        # 결과 로딩 대기
        time.sleep(3)

        # 첫 번째 앨범 결과 클릭
        try:
            first_album = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.album-result, .search-result-album, div[data-type="album"]'))
            )
            first_album.click()
        except TimeoutException:
            return {
                'success': False,
                'error': 'No album results found',
                'data': None
            }

        # 플랫폼 링크 로딩 대기
        time.sleep(2)

        # 앨범 커버 추출
        album_cover_url = None
        try:
            cover_img = driver.find_element(By.CSS_SELECTOR, 'img.album-cover, img.cover-image, .album-art img')
            album_cover_url = cover_img.get_attribute('src')
        except:
            pass

        # 플랫폼 링크 추출
        platforms = []
        platform_elements = driver.find_elements(By.CSS_SELECTOR, 'a.platform-link, .streaming-links a, .platform-item a')

        for element in platform_elements:
            try:
                url = element.get_attribute('href')
                platform_name = element.get_attribute('title') or element.text.strip()

                # 플랫폼 코드 추출 (URL에서)
                platform_code = None
                if 'spotify.com' in url:
                    platform_code = 'spo'
                elif 'music.apple.com' in url or 'apple.com' in url:
                    platform_code = 'itm'
                elif 'youtube.com' in url or 'youtu.be' in url:
                    platform_code = 'yat'
                elif 'amazon' in url:
                    platform_code = 'ama'
                elif 'deezer.com' in url:
                    platform_code = 'dee'
                elif 'tidal.com' in url:
                    platform_code = 'asp'
                elif 'pandora.com' in url:
                    platform_code = 'pdx'
                elif 'soundcloud.com' in url:
                    platform_code = 'soc'
                elif 'awa.fm' in url:
                    platform_code = 'awm'
                elif 'kkbox.com' in url:
                    platform_code = 'kkb'
                elif 'anghami.com' in url:
                    platform_code = 'ang'
                elif 'music.line.me' in url:
                    platform_code = 'lmj'
                elif 'moov.hk' in url:
                    platform_code = 'mov'
                elif 'qq.com' in url or 'y.qq.com' in url:
                    platform_code = 'tct'

                if url and platform_code:
                    platforms.append({
                        'platform': platform_name,
                        'code': platform_code,
                        'url': url,
                        'upc': None  # UPC는 페이지에서 추출 가능하면 추가
                    })
            except:
                continue

        return {
            'success': True,
            'data': {
                'album_cover_url': album_cover_url,
                'platform_count': len(platforms),
                'platforms': platforms
            },
            'request': {
                'artist': artist,
                'album': album
            }
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
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

        artist = data.get('artist', '')
        album = data.get('album', '')

        if not artist or not album:
            return jsonify({
                'success': False,
                'error': 'Missing artist or album'
            }), 400

        print(f"[Companion API] Searching: {artist} - {album}")

        result = search_album(artist, album)

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
