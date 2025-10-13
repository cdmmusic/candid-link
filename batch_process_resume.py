#!/usr/bin/env python3
"""
대량 앨범 배치 처리 (중단/재개 지원)
- 진행 상황 저장 (progress.json)
- 중단 후 재개 가능
- 실패한 앨범 별도 기록
"""

import requests
import sqlite3
import time
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'album_links.db')
N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/album-links'
PROGRESS_FILE = 'batch_progress.json'
FAILED_FILE = 'batch_failed.json'

def get_db_connection():
    """SQLite DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_progress():
    """진행 상황 로드"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'processed': [], 'last_index': 0, 'total_success': 0, 'total_failed': 0}

def save_progress(progress):
    """진행 상황 저장"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def load_failed():
    """실패 목록 로드"""
    if os.path.exists(FAILED_FILE):
        with open(FAILED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_failed(failed_list):
    """실패 목록 저장"""
    with open(FAILED_FILE, 'w', encoding='utf-8') as f:
        json.dump(failed_list, f, ensure_ascii=False, indent=2)

def get_albums_without_cover():
    """앨범 커버가 없는 앨범 목록 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT artist_ko, album_ko
        FROM album_platform_links
        WHERE album_cover_url IS NULL OR album_cover_url = ''
        ORDER BY artist_ko, album_ko
    ''')

    albums = [{'artist': row['artist_ko'], 'album': row['album_ko']} for row in cursor.fetchall()]
    conn.close()

    return albums

def process_album(artist, album):
    """단일 앨범 처리"""
    try:
        # n8n 웹훅 호출
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={'artist': artist, 'album': album},
            timeout=120  # 2분 타임아웃
        )

        if response.status_code == 200:
            data = response.json()

            # 앨범 커버가 수집되었는지 확인
            cover_url = data.get('album_cover_url', '')
            has_cover = cover_url and cover_url.strip() != ''

            return {
                'success': True,
                'has_cover': has_cover,
                'cover_url': cover_url
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}'
            }

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    print("=" * 60)
    print("대량 앨범 배치 처리 (중단/재개 지원)")
    print("=" * 60)

    # 진행 상황 로드
    progress = load_progress()
    failed_list = load_failed()

    # 처리할 앨범 목록
    all_albums = get_albums_without_cover()
    total = len(all_albums)

    if progress['last_index'] > 0:
        print(f"\n✓ 이전 진행 상황 발견!")
        print(f"  - 마지막 처리 인덱스: {progress['last_index']}/{total}")
        print(f"  - 성공: {progress['total_success']}개")
        print(f"  - 실패: {progress['total_failed']}개")

        choice = input(f"\n이어서 처리하시겠습니까? (y/n): ")
        if choice.lower() != 'y':
            print("처음부터 다시 시작합니다.")
            progress = {'processed': [], 'last_index': 0, 'total_success': 0, 'total_failed': 0}
            failed_list = []

    print(f"\n총 {total}개 앨범 중 {total - progress['last_index']}개 남음")

    # 배치 크기 설정
    batch_size = int(input("한 번에 처리할 앨범 수 (기본 100): ") or "100")
    delay = float(input("요청 간 대기 시간(초, 기본 2): ") or "2")

    print(f"\n설정:")
    print(f"  - 배치 크기: {batch_size}개")
    print(f"  - 대기 시간: {delay}초")
    print(f"  - 시작 인덱스: {progress['last_index']}")

    input("\nEnter를 눌러 시작...")

    start_time = datetime.now()
    success_count = progress['total_success']
    failed_count = progress['total_failed']

    # 처리할 앨범만 선택
    albums_to_process = all_albums[progress['last_index']:progress['last_index'] + batch_size]

    print(f"\n처리 시작: {len(albums_to_process)}개 앨범")
    print("-" * 60)

    try:
        for i, album_info in enumerate(albums_to_process, 1):
            current_index = progress['last_index'] + i
            artist = album_info['artist']
            album = album_info['album']

            print(f"\n[{current_index}/{total}] {artist} - {album}")

            result = process_album(artist, album)

            if result['success']:
                success_count += 1
                if result['has_cover']:
                    print(f"  ✓ 성공 (커버: {result['cover_url'][:50]}...)")
                else:
                    print(f"  ✓ 성공 (커버 없음)")
            else:
                failed_count += 1
                print(f"  ✗ 실패: {result['error']}")
                failed_list.append({
                    'artist': artist,
                    'album': album,
                    'error': result['error'],
                    'timestamp': datetime.now().isoformat()
                })

            # 진행 상황 저장
            progress['processed'].append(f"{artist}|||{album}")
            progress['last_index'] = current_index
            progress['total_success'] = success_count
            progress['total_failed'] = failed_count

            save_progress(progress)
            save_failed(failed_list)

            # 진행률 표시
            percent = (current_index / total) * 100
            print(f"  진행률: {percent:.1f}% | 성공: {success_count} | 실패: {failed_count}")

            # 대기
            if i < len(albums_to_process):
                time.sleep(delay)

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
        print(f"진행 상황이 저장되었습니다. (인덱스: {progress['last_index']})")
        return

    # 완료 통계
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 60)
    print("배치 처리 완료!")
    print("=" * 60)
    print(f"처리 시간: {elapsed}")
    print(f"총 처리: {len(albums_to_process)}개")
    print(f"성공: {success_count}개")
    print(f"실패: {failed_count}개")
    print(f"남은 앨범: {total - progress['last_index']}개")

    if progress['last_index'] < total:
        print(f"\n💡 아직 {total - progress['last_index']}개 앨범이 남았습니다.")
        print(f"   다시 실행하면 이어서 처리됩니다.")
    else:
        print("\n🎉 모든 앨범 처리 완료!")

        # 진행 상황 파일 삭제 (선택)
        choice = input("\n진행 상황 파일을 삭제하시겠습니까? (y/n): ")
        if choice.lower() == 'y':
            if os.path.exists(PROGRESS_FILE):
                os.remove(PROGRESS_FILE)
                print("진행 상황 파일 삭제됨")

    if failed_list:
        print(f"\n⚠️ 실패한 앨범 목록: {FAILED_FILE}")

if __name__ == '__main__':
    main()
