#!/usr/bin/env python3
"""
실패 케이스 분석 스크립트
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

def analyze_failures():
    """실패 케이스 분석"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 플랫폼별 실패 통계
    print("\n" + "="*60)
    print("  Platform Failure Analysis")
    print("="*60 + "\n")

    cursor.execute('''
        SELECT
            platform_id,
            platform_name,
            COUNT(*) as total,
            SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as success,
            SUM(CASE WHEN found = 0 THEN 1 ELSE 0 END) as failed
        FROM album_platform_links
        WHERE platform_type = 'kr'
        GROUP BY platform_id, platform_name
        ORDER BY platform_id
    ''')

    rows = cursor.fetchall()

    print("Korean Platforms:")
    print("-" * 60)
    for row in rows:
        platform_id, platform_name, total, success, failed = row
        success_rate = (success / total * 100) if total > 0 else 0
        print(f"{platform_name:10} | Total: {total:5} | Success: {success:5} ({success_rate:5.1f}%) | Failed: {failed:5}")

    # 실패한 앨범 목록 (각 플랫폼별)
    print("\n" + "="*60)
    print("  Failed Albums by Platform")
    print("="*60 + "\n")

    platforms = ['melon', 'genie', 'bugs', 'vibe', 'flo']

    for platform_id in platforms:
        cursor.execute('''
            SELECT artist_ko, album_ko
            FROM album_platform_links
            WHERE platform_type = 'kr'
              AND platform_id = ?
              AND found = 0
            LIMIT 10
        ''', (platform_id,))

        failed_albums = cursor.fetchall()

        if len(failed_albums) > 0:
            print(f"\n{platform_id.upper()} - Failed Albums (showing first 10):")
            print("-" * 60)
            for i, (artist, album) in enumerate(failed_albums, 1):
                print(f"  {i}. {artist} - {album}")

    # 모든 플랫폼에서 실패한 앨범 찾기
    print("\n" + "="*60)
    print("  Albums Failed on Multiple Platforms")
    print("="*60 + "\n")

    cursor.execute('''
        SELECT
            artist_ko,
            album_ko,
            SUM(CASE WHEN found = 0 THEN 1 ELSE 0 END) as failed_count
        FROM album_platform_links
        WHERE platform_type = 'kr'
        GROUP BY artist_ko, album_ko
        HAVING failed_count >= 3
        ORDER BY failed_count DESC
        LIMIT 20
    ''')

    multi_failed = cursor.fetchall()

    if len(multi_failed) > 0:
        print("Albums failed on 3+ platforms (showing first 20):")
        print("-" * 60)
        for artist, album, failed_count in multi_failed:
            print(f"  [{failed_count}/5 failed] {artist} - {album}")
    else:
        print("No albums failed on 3+ platforms!")

    conn.close()

if __name__ == "__main__":
    try:
        analyze_failures()
        print()
    except Exception as e:
        print(f"\nError: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
