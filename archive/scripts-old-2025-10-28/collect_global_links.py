#!/usr/bin/env python3
"""
글로벌 플랫폼 링크 수집 스크립트
- album_links.db에서 CDMA 코드가 있고 글로벌 링크가 없는 앨범 찾기
- companion_api_v2.py (port 5001)를 사용하여 글로벌 링크 수집
- album_platform_links 테이블에 저장
"""

import sqlite3
import requests
import time
import sys
from datetime import datetime

# 설정
DB_PATH = '/Users/choejibin/release-album-link/album_links.db'
COMPANION_API_URL = 'http://localhost:5001'

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

def get_db_connection():
    """SQLite 데이터베이스 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_albums_without_global_links(limit=50):
    """글로벌 링크가 없는 발매된 앨범 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 발매일이 지났고, 글로벌 링크가 없는 앨범 찾기
    cursor.execute('''
        SELECT a.id, a.artist_ko, a.artist_en, a.album_ko, a.album_en,
               a.album_code, a.release_date
        FROM albums a
        WHERE a.album_code LIKE 'CDMA%'
          AND datetime(a.release_date) <= datetime('now')
          AND NOT EXISTS (
              SELECT 1 FROM album_platform_links apl
              WHERE apl.artist_ko = a.artist_ko
                AND apl.album_ko = a.album_ko
                AND apl.platform_type = 'global'
                AND apl.found = 1
          )
        ORDER BY a.release_date DESC
        LIMIT ?
    ''', (limit,))

    albums = []
    for row in cursor.fetchall():
        albums.append({
            'id': row['id'],
            'artist_ko': row['artist_ko'],
            'artist_en': row['artist_en'],
            'album_ko': row['album_ko'],
            'album_en': row['album_en'],
            'album_code': row['album_code'],
            'release_date': row['release_date']
        })

    conn.close()
    return albums

def search_companion_api(artist, album, upc):
    """Companion API로 글로벌 링크 검색"""
    try:
        response = requests.post(
            f'{COMPANION_API_URL}/search',
            json={'artist': artist, 'album': album, 'upc': upc},
            timeout=90
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                return result['data']

        return None

    except requests.exceptions.ConnectionError:
        print(f"{Colors.FAIL}    ✗ Companion API 연결 실패{Colors.ENDC}")
        return None
    except requests.exceptions.Timeout:
        print(f"{Colors.FAIL}    ✗ Companion API 타임아웃{Colors.ENDC}")
        return None
    except Exception as e:
        print(f"{Colors.FAIL}    ✗ 에러: {str(e)[:50]}{Colors.ENDC}")
        return None

def save_global_platforms(artist_ko, artist_en, album_ko, album_en, album_code,
                         release_date, platforms):
    """글로벌 플랫폼 링크를 DB에 저장"""
    if not platforms or len(platforms) == 0:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    # 기존 글로벌 링크 삭제
    cursor.execute('''
        DELETE FROM album_platform_links
        WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'global'
    ''', (artist_ko, album_ko))

    saved_count = 0

    # 새 글로벌 링크 저장
    for platform in platforms:
        try:
            cursor.execute('''
                INSERT INTO album_platform_links
                (artist_ko, artist_en, album_ko, album_en, platform_type,
                 platform_code, platform_name, platform_url, found,
                 release_date, created_at)
                VALUES (?, ?, ?, ?, 'global', ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
            ''', (
                artist_ko,
                artist_en or '',
                album_ko,
                album_en or '',
                platform['platform_code'],
                platform['platform_name'],
                platform['platform_url'],
                release_date
            ))
            saved_count += 1
        except Exception as e:
            print(f"{Colors.WARNING}    경고: {platform['platform_name']} 저장 실패 - {str(e)[:30]}{Colors.ENDC}")

    conn.commit()
    conn.close()

    return saved_count

def process_album(album):
    """개별 앨범 처리"""
    artist_ko = album['artist_ko']
    artist_en = album['artist_en']
    album_ko = album['album_ko']
    album_en = album['album_en']
    album_code = album['album_code']
    release_date = album['release_date']

    # 검색에 사용할 아티스트/앨범명 (영문 우선)
    search_artist = artist_en if artist_en else artist_ko
    search_album = album_en if album_en else album_ko

    print(f"{Colors.OKCYAN}    검색: {search_artist} - {search_album} ({album_code}){Colors.ENDC}")

    # Companion API 호출
    data = search_companion_api(search_artist, search_album, album_code)

    if data is None:
        return 0, 0

    platforms = data.get('platforms', [])

    if len(platforms) == 0:
        print(f"{Colors.WARNING}    ⚠️  플랫폼 없음{Colors.ENDC}")
        return 0, 0

    # DB 저장
    saved_count = save_global_platforms(
        artist_ko, artist_en, album_ko, album_en,
        album_code, release_date, platforms
    )

    print(f"{Colors.OKGREEN}    ✓ {len(platforms)}개 플랫폼 발견, {saved_count}개 저장됨{Colors.ENDC}")

    return len(platforms), saved_count

def main():
    """메인 실행"""
    # 인자 처리
    limit = 50
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"{Colors.WARNING}경고: 잘못된 숫자, 기본값 50 사용{Colors.ENDC}")

    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}")
    print(f"  글로벌 플랫폼 링크 수집")
    print(f"{'='*70}{Colors.ENDC}\n")
    print(f"데이터베이스: {DB_PATH}")
    print(f"Companion API: {COMPANION_API_URL}")
    print(f"처리 제한: {limit}개 앨범\n")

    # Companion API 상태 확인
    print(f"{Colors.OKCYAN}Companion API 상태 확인 중...{Colors.ENDC}")
    try:
        response = requests.get(f'{COMPANION_API_URL}/health', timeout=5)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}✓ Companion API 정상 작동{Colors.ENDC}\n")
        else:
            print(f"{Colors.FAIL}✗ Companion API 응답 이상 (HTTP {response.status_code}){Colors.ENDC}\n")
            return
    except Exception as e:
        print(f"{Colors.FAIL}✗ Companion API 연결 실패: {str(e)}{Colors.ENDC}")
        print(f"{Colors.WARNING}companion_api_v2.py가 실행 중인지 확인하세요 (port 5001){Colors.ENDC}\n")
        return

    # 앨범 목록 가져오기
    print(f"{Colors.OKCYAN}글로벌 링크가 없는 앨범 조회 중...{Colors.ENDC}")
    albums = get_albums_without_global_links(limit)

    if len(albums) == 0:
        print(f"{Colors.OKGREEN}모든 앨범에 글로벌 링크가 있습니다!{Colors.ENDC}\n")
        return

    print(f"총 {len(albums)}개 앨범 발견\n")

    # 통계
    success_count = 0
    fail_count = 0
    total_platforms = 0
    total_saved = 0
    start_time = datetime.now()

    # 앨범 처리
    for idx, album in enumerate(albums, 1):
        print(f"{Colors.BOLD}[{idx}/{len(albums)}] {album['artist_ko']} - {album['album_ko']}{Colors.ENDC}")
        print(f"    발매일: {album['release_date'][:10] if album['release_date'] else 'N/A'}")

        try:
            platforms_found, saved_count = process_album(album)

            if platforms_found > 0:
                success_count += 1
                total_platforms += platforms_found
                total_saved += saved_count
            else:
                fail_count += 1

        except Exception as e:
            print(f"{Colors.FAIL}    ✗ 처리 실패: {str(e)}{Colors.ENDC}")
            fail_count += 1

        print()

        # 다음 요청 전 대기 (API 부하 방지)
        if idx < len(albums):
            time.sleep(3)

    # 결과 출력
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}")
    print(f"  수집 완료")
    print(f"{'='*70}{Colors.ENDC}\n")
    print(f"총 처리: {len(albums)}개 앨범")
    print(f"{Colors.OKGREEN}성공: {success_count}개{Colors.ENDC}")
    print(f"{Colors.FAIL}실패: {fail_count}개{Colors.ENDC}")
    print(f"발견된 플랫폼: {total_platforms}개")
    print(f"저장된 링크: {total_saved}개")
    print(f"소요 시간: {duration:.1f}초")
    print(f"평균: {duration/len(albums) if len(albums) > 0 else 0:.1f}초/앨범\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}사용자에 의해 중단되었습니다.{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}치명적 오류: {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
