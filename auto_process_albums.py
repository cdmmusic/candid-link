#!/usr/bin/env python3
"""
DB에 있는 앨범들을 자동으로 n8n 워크플로우로 처리
found=0인 앨범들을 순차적으로 처리
"""

import sqlite3
import requests
import time
import os
from datetime import datetime

# 설정
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'album_links.db')
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/album-links"  # n8n webhook URL
DELAY_BETWEEN_REQUESTS = 10  # 요청 간격 (초) - 각 앨범당 약 1분 소요
BATCH_SIZE = 10  # 한 번에 처리할 앨범 수

def get_db_connection():
    """SQLite DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_albums_without_links(limit=None):
    """링크가 없는 앨범 목록 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # found=0인 앨범들 (중복 제거)
    query = '''
        SELECT DISTINCT artist_ko, album_ko, release_date
        FROM album_platform_links
        WHERE found = 0
        GROUP BY artist_ko, album_ko
        ORDER BY release_date DESC
    '''

    if limit:
        query += f' LIMIT {limit}'

    cursor.execute(query)
    albums = cursor.fetchall()
    conn.close()

    return albums

def trigger_n8n_workflow(artist, album):
    """n8n 워크플로우 트리거"""
    try:
        # n8n 워크플로우가 기대하는 형식
        payload = {
            "primary_artist": artist,
            "album_title_ko": album
        }

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=300  # 5분 타임아웃
        )

        if response.status_code == 200:
            result = response.json()
            # 성공 여부 체크
            if result.get('success'):
                summary = result.get('summary', {})
                kr_found = summary.get('kr_found', 0)
                global_found = summary.get('global_found', 0)
                return True, f"KR: {kr_found}/5, Global: {global_found}"
            else:
                return False, result.get('error', 'Unknown error')
        else:
            return False, f"Status {response.status_code}: {response.text[:100]}"

    except requests.exceptions.Timeout:
        return False, "Timeout (5분 초과)"
    except Exception as e:
        return False, str(e)

def main():
    """메인 프로세스"""

    print("=" * 60)
    print("앨범 자동 처리 스크립트")
    print("=" * 60)

    # 처리할 앨범 수 선택
    print("\n처리할 앨범 수를 선택하세요:")
    print("1. 10개 (테스트)")
    print("2. 100개")
    print("3. 전체")

    choice = input("\n선택 (1-3): ").strip()

    if choice == "1":
        limit = 10
    elif choice == "2":
        limit = 100
    else:
        limit = None

    # 앨범 목록 가져오기
    print(f"\n링크가 없는 앨범 목록 조회 중...")
    albums = get_albums_without_links(limit)

    if not albums:
        print("✅ 모든 앨범에 링크가 있습니다!")
        return

    print(f"\n총 {len(albums)}개 앨범을 처리합니다.")
    print(f"예상 소요 시간: 약 {len(albums) * DELAY_BETWEEN_REQUESTS / 60:.1f}분")

    # 확인
    confirm = input("\n계속하시겠습니까? (y/n): ").strip().lower()
    if confirm != 'y':
        print("취소되었습니다.")
        return

    print("\n처리 시작...\n")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    for idx, album in enumerate(albums, 1):
        artist_ko = album['artist_ko']
        album_ko = album['album_ko']
        release_date = album['release_date']

        print(f"[{idx}/{len(albums)}] {artist_ko} - {album_ko}")
        print(f"  발매일: {release_date}")

        # n8n 워크플로우 트리거
        success, result = trigger_n8n_workflow(artist_ko, album_ko)

        if success:
            print(f"  ✅ 성공")
            success_count += 1
        else:
            print(f"  ❌ 실패: {result}")
            fail_count += 1

        print()

        # 다음 요청 전 대기
        if idx < len(albums):
            time.sleep(DELAY_BETWEEN_REQUESTS)

    print("-" * 60)
    print("\n처리 완료!")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📊 성공률: {success_count / len(albums) * 100:.1f}%")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
