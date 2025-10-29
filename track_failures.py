#!/usr/bin/env python3
"""
실패 케이스 추적 및 리포트 생성
- 완전 실패 (KR 0/5): 삭제되었거나 아티스트명 변경 등의 이유
- 부분 실패 (KR 1-4/5): 일부 플랫폼에만 존재
"""
import sys
import os

try:
    import libsql_experimental as libsql
except ImportError:
    print("Error: libsql not found. Please install: pip install libsql-experimental")
    sys.exit(1)

TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

def get_db_connection():
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise Exception("Turso credentials not found in environment variables")

    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

def track_all_failures():
    """전체 데이터베이스의 실패 케이스 추적"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("  전체 실패 케이스 추적 리포트")
    print("="*80 + "\n")

    # 전체 앨범에 대한 실패 통계
    cursor.execute('''
        WITH album_stats AS (
            SELECT
                a.album_code,
                a.artist_ko,
                a.album_ko,
                COUNT(CASE WHEN apl.found = 1 AND apl.platform_type = 'kr' THEN 1 END) as kr_success_count
            FROM albums a
            LEFT JOIN album_platform_links apl ON a.artist_ko = apl.artist_ko AND a.album_ko = apl.album_ko
            GROUP BY a.album_code, a.artist_ko, a.album_ko
        )
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN kr_success_count = 5 THEN 1 ELSE 0 END) as perfect_success,
            SUM(CASE WHEN kr_success_count > 0 AND kr_success_count < 5 THEN 1 ELSE 0 END) as partial_failure,
            SUM(CASE WHEN kr_success_count = 0 THEN 1 ELSE 0 END) as complete_failure
        FROM album_stats
    ''')

    row = cursor.fetchone()
    total, perfect, partial, complete = row

    print(f"📊 전체 통계:")
    print(f"  - 총 앨범 수: {total:,}개")
    print(f"  - 완전 성공 (KR 5/5): {perfect:,}개 ({perfect/total*100:.1f}%)")
    print(f"  - 부분 실패 (KR 1-4/5): {partial:,}개 ({partial/total*100:.1f}%)")
    print(f"  - 완전 실패 (KR 0/5): {complete:,}개 ({complete/total*100:.1f}%)")
    print()

    # 완전 실패 케이스 저장
    print("\n" + "="*80)
    print("  🔴 완전 실패 케이스 (KR 0/5)")
    print("="*80 + "\n")

    cursor.execute('''
        WITH album_stats AS (
            SELECT
                a.album_code,
                a.artist_ko,
                a.album_ko,
                COUNT(CASE WHEN apl.found = 1 AND apl.platform_type = 'kr' THEN 1 END) as kr_success_count
            FROM albums a
            LEFT JOIN album_platform_links apl ON a.artist_ko = apl.artist_ko AND a.album_ko = apl.album_ko
            GROUP BY a.album_code, a.artist_ko, a.album_ko
        )
        SELECT album_code, artist_ko, album_ko
        FROM album_stats
        WHERE kr_success_count = 0
        ORDER BY album_code
    ''')

    complete_failures = cursor.fetchall()

    if complete_failures:
        print(f"총 {len(complete_failures)}개의 완전 실패 케이스:")
        print("(아티스트명 변경, 앨범 삭제, 또는 플랫폼 미등록 가능성)\n")

        # 파일로 저장
        with open('failures_complete.txt', 'w', encoding='utf-8') as f:
            f.write("# 완전 실패 케이스 (KR 0/5)\n")
            f.write(f"# 총 {len(complete_failures)}개\n")
            f.write("# 형식: CDMA코드 | 아티스트 | 앨범명\n\n")

            for code, artist, album in complete_failures:
                line = f"{code} | {artist} | {album}\n"
                f.write(line)

        print(f"✓ 완전 실패 케이스 저장: failures_complete.txt ({len(complete_failures)}개)")
    else:
        print("완전 실패 케이스 없음!")

    # 부분 실패 케이스 저장
    print("\n" + "="*80)
    print("  🟡 부분 실패 케이스 (KR 1-4/5)")
    print("="*80 + "\n")

    cursor.execute('''
        WITH album_stats AS (
            SELECT
                a.album_code,
                a.artist_ko,
                a.album_ko,
                COUNT(CASE WHEN apl.found = 1 AND apl.platform_type = 'kr' THEN 1 END) as kr_success_count
            FROM albums a
            LEFT JOIN album_platform_links apl ON a.artist_ko = apl.artist_ko AND a.album_ko = apl.album_ko
            GROUP BY a.album_code, a.artist_ko, a.album_ko
        )
        SELECT album_code, artist_ko, album_ko, kr_success_count
        FROM album_stats
        WHERE kr_success_count > 0 AND kr_success_count < 5
        ORDER BY kr_success_count ASC, album_code
    ''')

    partial_failures = cursor.fetchall()

    if partial_failures:
        print(f"총 {len(partial_failures)}개의 부분 실패 케이스:")
        print("(일부 플랫폼에만 존재하는 앨범)\n")

        # 파일로 저장
        with open('failures_partial.txt', 'w', encoding='utf-8') as f:
            f.write("# 부분 실패 케이스 (KR 1-4/5)\n")
            f.write(f"# 총 {len(partial_failures)}개\n")
            f.write("# 형식: CDMA코드 | KR성공수 | 아티스트 | 앨범명\n\n")

            for code, artist, album, kr_count in partial_failures:
                line = f"{code} | {kr_count}/5 | {artist} | {album}\n"
                f.write(line)

        print(f"✓ 부분 실패 케이스 저장: failures_partial.txt ({len(partial_failures)}개)")
    else:
        print("부분 실패 케이스 없음!")

    conn.close()

    print("\n" + "="*80)
    print("  리포트 생성 완료")
    print("="*80)
    print()

if __name__ == "__main__":
    try:
        track_all_failures()
    except Exception as e:
        print(f"\nError: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
