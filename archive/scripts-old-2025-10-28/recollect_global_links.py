#!/usr/bin/env python3
"""
글로벌 링크 재수집 스크립트
- DB 정규화 후 실패했던 앨범들을 다시 수집
- CDMA 코드가 있는 앨범만 수집
"""

import sqlite3
import requests
import time
import sys
from datetime import datetime

DB_PATH = 'album_links.db'
COMPANION_API_URL = 'http://localhost:5001'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_failed_albums():
    """글로벌 링크가 없는 앨범 목록 가져오기"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # albums 테이블에서 CDMA 코드가 있는 앨범만 가져오기
    cursor.execute('''
        WITH global_stats AS (
            SELECT
                apl.artist_ko,
                apl.album_ko,
                a.album_code as cdma_code,
                COUNT(CASE WHEN apl.found = 1 AND apl.platform_type = 'global' THEN 1 END) as global_found
            FROM album_platform_links apl
            LEFT JOIN albums a ON apl.artist_ko = a.artist_ko AND apl.album_ko = a.album_ko
            WHERE a.album_code IS NOT NULL AND a.album_code != ''
            GROUP BY apl.artist_ko, apl.album_ko
        )
        SELECT artist_ko, album_ko, cdma_code
        FROM global_stats
        WHERE global_found = 0
        ORDER BY artist_ko, album_ko
    ''')

    albums = cursor.fetchall()
    conn.close()

    return albums

def search_global_platforms(artist_ko, album_ko, cdma_code):
    """Companion API로 글로벌 플랫폼 검색"""
    try:
        response = requests.post(
            f'{COMPANION_API_URL}/search',
            json={
                'artist': artist_ko,
                'album': album_ko,
                'upc': cdma_code
            },
            timeout=90
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"  ❌ API 에러: {str(e)}")
        return None

def update_global_links(artist_ko, album_ko, platforms):
    """데이터베이스에 글로벌 링크 업데이트 또는 삽입"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # albums 테이블에서 추가 정보 가져오기
    cursor.execute('''
        SELECT artist_en, album_en, release_date
        FROM albums
        WHERE artist_ko = ? AND album_ko = ?
    ''', (artist_ko, album_ko))

    album_info = cursor.fetchone()
    if not album_info:
        conn.close()
        return 0

    artist_en = album_info['artist_en'] or ''
    album_en = album_info['album_en'] or ''
    release_date = album_info['release_date'] or ''

    updated_count = 0

    for platform in platforms:
        platform_code = platform['code']
        platform_name = platform['platform']
        platform_url = platform['url']

        # 1. 먼저 UPDATE 시도
        cursor.execute('''
            UPDATE album_platform_links
            SET platform_url = ?, found = 1, platform_name = ?
            WHERE artist_ko = ? AND album_ko = ?
              AND platform_type = 'global'
              AND platform_code = ?
        ''', (platform_url, platform_name, artist_ko, album_ko, platform_code))

        if cursor.rowcount > 0:
            updated_count += cursor.rowcount
        else:
            # 2. UPDATE 실패시 INSERT
            cursor.execute('''
                INSERT INTO album_platform_links
                (artist_ko, artist_en, album_ko, album_en, platform_type,
                 platform_name, platform_url, platform_code, found, release_date)
                VALUES (?, ?, ?, ?, 'global', ?, ?, ?, 1, ?)
            ''', (artist_ko, artist_en, album_ko, album_en,
                  platform_name, platform_url, platform_code, release_date))
            updated_count += 1

    conn.commit()
    conn.close()

    return updated_count

def main():
    print("=" * 80)
    print("🌐 글로벌 링크 재수집 시작")
    print("=" * 80)
    print()

    # 1. Companion API 상태 확인
    try:
        health = requests.get(f'{COMPANION_API_URL}/health', timeout=5).json()
        print(f"✅ Companion API: {health['status']}")
    except:
        print("❌ Companion API가 실행되지 않았습니다!")
        print("   다음 명령으로 시작하세요: python3 companion_api.py")
        sys.exit(1)

    # 2. 실패한 앨범 목록 가져오기
    failed_albums = get_failed_albums()
    total = len(failed_albums)

    print(f"📊 재수집 대상: {total}개 앨범 (CDMA 코드 있음)")
    print()

    if total == 0:
        print("✅ 재수집할 앨범이 없습니다!")
        return

    # 3. 재수집 시작
    start_time = time.time()
    success_count = 0
    fail_count = 0
    updated_links = 0

    for idx, album in enumerate(failed_albums, 1):
        artist_ko = album['artist_ko']
        album_ko = album['album_ko']
        cdma_code = album['cdma_code']

        print(f"[{idx}/{total}] {artist_ko} - {album_ko} ({cdma_code})")

        # Companion API 호출
        result = search_global_platforms(artist_ko, album_ko, cdma_code)

        if result and result.get('success'):
            platforms = result.get('data', {}).get('platforms', [])
            platform_count = len(platforms)

            if platform_count > 0:
                # DB 업데이트
                updated = update_global_links(artist_ko, album_ko, platforms)
                updated_links += updated
                success_count += 1
                print(f"  ✅ {platform_count}개 플랫폼 찾음, {updated}개 레코드 업데이트")
            else:
                fail_count += 1
                print(f"  ⚠️  플랫폼 없음")
        else:
            fail_count += 1
            error_msg = result.get('error', 'Unknown error') if result else 'API 응답 없음'
            print(f"  ❌ 실패: {error_msg}")

        # 진행률 표시
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            remaining = (total - idx) * avg_time
            print(f"\n  📈 진행률: {idx}/{total} ({idx/total*100:.1f}%) | "
                  f"성공: {success_count} | 실패: {fail_count} | "
                  f"예상 남은 시간: {remaining/60:.1f}분\n")

        # Rate limiting (1초 대기)
        time.sleep(1)

    # 4. 최종 결과
    elapsed_time = time.time() - start_time

    print()
    print("=" * 80)
    print("✅ 글로벌 링크 재수집 완료")
    print("=" * 80)
    print(f"총 처리: {total}개")
    print(f"성공: {success_count}개 ({success_count/total*100:.1f}%)")
    print(f"실패: {fail_count}개 ({fail_count/total*100:.1f}%)")
    print(f"업데이트된 링크: {updated_links}개")
    print(f"소요 시간: {elapsed_time/60:.1f}분")
    print("=" * 80)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
