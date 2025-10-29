#!/usr/bin/env python3
"""
전체 앨범 링크 자동 수집
- albums 테이블에서 모든 CDMA 코드 조회
- 각 앨범별로 링크 수집 실행
- 진행 상황 실시간 표시
"""

import subprocess
import sys
import os
from datetime import datetime

try:
    import libsql_experimental as libsql
except ImportError:
    print("Error: libsql not found. Please install: pip install libsql-experimental")
    sys.exit(1)

TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

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
    """Turso 데이터베이스 연결"""
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise Exception("Turso credentials not found in environment variables")

    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

def get_all_album_codes():
    """albums 테이블에서 모든 CDMA 코드 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT album_code, artist_ko, album_ko
        FROM albums
        ORDER BY album_code
    ''')

    albums = cursor.fetchall()
    conn.close()

    return albums

def get_albums_without_links():
    """링크가 없는 앨범만 조회 (album_platform_links에 없는 앨범)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT a.album_code, a.artist_ko, a.album_ko
        FROM albums a
        LEFT JOIN album_platform_links apl
            ON a.artist_ko = apl.artist_ko AND a.album_ko = apl.album_ko
        WHERE apl.artist_ko IS NULL
        ORDER BY a.album_code
    ''')

    albums = cursor.fetchall()
    conn.close()

    return albums

def main():
    """메인 실행"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}")
    print(f"  전체 앨범 링크 자동 수집")
    print(f"  Automatic Album Link Collection for All Albums")
    print(f"{'='*70}{Colors.ENDC}\n")

    # 명령줄 인자로 모드 선택 (기본값: 링크 없는 앨범만)
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "missing"

    if mode == "all":
        print(f"{Colors.OKCYAN}전체 앨범을 조회합니다...{Colors.ENDC}")
        albums = get_all_album_codes()
    else:
        print(f"{Colors.OKCYAN}링크가 없는 앨범을 조회합니다...{Colors.ENDC}")
        albums = get_albums_without_links()

    total = len(albums)

    if total == 0:
        print(f"{Colors.WARNING}수집할 앨범이 없습니다!{Colors.ENDC}\n")
        return

    print(f"{Colors.OKGREEN}총 {total}개 앨범을 찾았습니다{Colors.ENDC}")
    print(f"{Colors.BOLD}수집을 자동으로 시작합니다...{Colors.ENDC}\n")

    start_time = datetime.now()
    success_count = 0
    fail_count = 0

    # 앨범 목록 출력
    print(f"{Colors.BOLD}앨범 목록:{Colors.ENDC}")
    for idx, (code, artist, album) in enumerate(albums[:10], 1):
        print(f"  {idx}. {code} - {artist} - {album}")
    if total > 10:
        print(f"  ... 외 {total - 10}개\n")
    else:
        print()

    # 배치 크기 (한 번에 처리할 앨범 수)
    batch_size = 10

    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = albums[batch_start:batch_end]
        batch_codes = [album[0] for album in batch]

        print(f"{Colors.BOLD}[Batch {batch_start//batch_size + 1}/{(total + batch_size - 1)//batch_size}] ")
        print(f"Processing albums {batch_start + 1}-{batch_end} of {total}{Colors.ENDC}")

        # collect_from_db.py 실행
        cmd = [
            'python3', 'collect_from_db.py'
        ] + batch_codes

        env = os.environ.copy()
        env['TURSO_DATABASE_URL'] = TURSO_DATABASE_URL
        env['TURSO_AUTH_TOKEN'] = TURSO_AUTH_TOKEN
        env['COMPANION_API_PORT'] = os.environ.get('COMPANION_API_PORT', '8001')

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=False,
                text=True
            )

            if result.returncode == 0:
                success_count += len(batch)
            else:
                fail_count += len(batch)

        except Exception as e:
            print(f"{Colors.FAIL}Batch 처리 실패: {str(e)}{Colors.ENDC}")
            fail_count += len(batch)

        print()

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # 결과 요약
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}")
    print(f"  수집 완료")
    print(f"  Collection Complete")
    print(f"{'='*70}{Colors.ENDC}\n")
    print(f"총 앨범 수: {total}")
    print(f"{Colors.OKGREEN}성공: {success_count}{Colors.ENDC}")
    print(f"{Colors.FAIL}실패: {fail_count}{Colors.ENDC}")
    print(f"소요 시간: {duration:.1f}초")
    print(f"평균: {duration/total if total > 0 else 0:.1f}초/앨범\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}사용자에 의해 중단되었습니다.{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}오류 발생: {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
