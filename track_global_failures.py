#!/usr/bin/env python3
"""
글로벌 플랫폼 링크 통계 및 실패 케이스 추적
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

def track_global_failures():
    """글로벌 플랫폼 링크 통계 추적"""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("  글로벌 플랫폼 링크 통계")
    print("="*80 + "\n")

    # 플랫폼별 통계
    cursor.execute('''
        SELECT
            platform_code,
            platform_name,
            COUNT(*) as total,
            SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as found,
            SUM(CASE WHEN found = 0 THEN 1 ELSE 0 END) as not_found
        FROM album_platform_links
        WHERE platform_type = 'global'
        GROUP BY platform_code, platform_name
        ORDER BY platform_code
    ''')

    rows = cursor.fetchall()

    header = f"{'플랫폼':<15} | {'총 개수':>8} | {'찾음':>8} | {'못찾음':>8} | {'성공률':>8}"
    print(header)
    print('-'*80)

    for row in rows:
        code, name, total, found, not_found = row
        rate = (found / total * 100) if total > 0 else 0
        line = f'{name:<15} | {total:>8,} | {found:>8,} | {not_found:>8,} | {rate:>7.1f}%'
        print(line)

    # 앨범별 글로벌 링크 통계
    print("\n" + "="*80)
    print("  앨범별 글로벌 링크 통계")
    print("="*80 + "\n")

    cursor.execute('''
        WITH global_stats AS (
            SELECT
                artist_ko,
                album_ko,
                COUNT(CASE WHEN found = 1 AND platform_type = 'global' THEN 1 END) as global_success_count,
                COUNT(CASE WHEN platform_type = 'global' THEN 1 END) as global_total_count
            FROM album_platform_links
            GROUP BY artist_ko, album_ko
        )
        SELECT
            COUNT(*) as total_albums,
            SUM(CASE WHEN global_success_count = global_total_count THEN 1 ELSE 0 END) as all_found,
            SUM(CASE WHEN global_success_count > 0 AND global_success_count < global_total_count THEN 1 ELSE 0 END) as partial_found,
            SUM(CASE WHEN global_success_count = 0 THEN 1 ELSE 0 END) as none_found,
            AVG(CAST(global_success_count AS FLOAT) / NULLIF(global_total_count, 0) * 100) as avg_success_rate
        FROM global_stats
    ''')

    row = cursor.fetchone()
    total, all_found, partial, none = row[0], row[1], row[2], row[3]
    avg_rate = row[4] if row[4] else 0

    print(f'📊 총 앨범 수: {total:,}개')
    print(f'  - 모든 글로벌 링크 찾음: {all_found:,}개 ({all_found/total*100:.1f}%)')
    print(f'  - 일부 글로벌 링크 찾음: {partial:,}개 ({partial/total*100:.1f}%)')
    print(f'  - 글로벌 링크 없음: {none:,}개 ({none/total*100:.1f}%)')
    print(f'  - 평균 글로벌 링크 성공률: {avg_rate:.1f}%')

    # 글로벌 링크가 전혀 없는 앨범 저장
    print("\n" + "="*80)
    print("  🔴 글로벌 링크 전혀 없는 앨범")
    print("="*80 + "\n")

    cursor.execute('''
        WITH global_stats AS (
            SELECT
                artist_ko,
                album_ko,
                COUNT(CASE WHEN found = 1 AND platform_type = 'global' THEN 1 END) as global_success_count
            FROM album_platform_links
            GROUP BY artist_ko, album_ko
        )
        SELECT artist_ko, album_ko
        FROM global_stats
        WHERE global_success_count = 0
        ORDER BY artist_ko, album_ko
    ''')

    no_global_links = cursor.fetchall()

    if no_global_links:
        print(f"총 {len(no_global_links)}개의 앨범에 글로벌 링크가 없습니다.\n")

        with open('failures_global_complete.txt', 'w', encoding='utf-8') as f:
            f.write("# 글로벌 링크 전혀 없는 앨범\n")
            f.write(f"# 총 {len(no_global_links)}개\n")
            f.write("# 형식: 아티스트 | 앨범명\n\n")

            for artist, album in no_global_links:
                line = f"{artist} | {album}\n"
                f.write(line)

        print(f"✓ 파일 저장: failures_global_complete.txt ({len(no_global_links)}개)")
    else:
        print("모든 앨범에 최소 1개 이상의 글로벌 링크가 있습니다!")

    # 글로벌 링크가 부분적인 앨범 저장
    print("\n" + "="*80)
    print("  🟡 글로벌 링크 부분 실패 앨범")
    print("="*80 + "\n")

    cursor.execute('''
        WITH global_stats AS (
            SELECT
                artist_ko,
                album_ko,
                COUNT(CASE WHEN found = 1 AND platform_type = 'global' THEN 1 END) as global_success_count,
                COUNT(CASE WHEN platform_type = 'global' THEN 1 END) as global_total_count
            FROM album_platform_links
            GROUP BY artist_ko, album_ko
        )
        SELECT artist_ko, album_ko, global_success_count, global_total_count
        FROM global_stats
        WHERE global_success_count > 0 AND global_success_count < global_total_count
        ORDER BY global_success_count ASC, artist_ko, album_ko
    ''')

    partial_global = cursor.fetchall()

    if partial_global:
        print(f"총 {len(partial_global)}개의 앨범에 일부 글로벌 링크만 있습니다.\n")

        with open('failures_global_partial.txt', 'w', encoding='utf-8') as f:
            f.write("# 글로벌 링크 부분 실패 앨범\n")
            f.write(f"# 총 {len(partial_global)}개\n")
            f.write("# 형식: 성공수/총개수 | 아티스트 | 앨범명\n\n")

            for artist, album, success, total_count in partial_global:
                line = f"{success}/{total_count} | {artist} | {album}\n"
                f.write(line)

        print(f"✓ 파일 저장: failures_global_partial.txt ({len(partial_global)}개)")
    else:
        print("부분 실패 앨범이 없습니다!")

    conn.close()

    print("\n" + "="*80)
    print("  글로벌 링크 통계 생성 완료")
    print("="*80)
    print()

if __name__ == "__main__":
    try:
        track_global_failures()
    except Exception as e:
        print(f"\nError: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
