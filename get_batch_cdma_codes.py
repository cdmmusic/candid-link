#!/usr/bin/env python3
"""
배치별로 CDMA 코드 조회
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

def get_batch_cdma_codes(offset=0, limit=100):
    """배치별 CDMA 코드 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT album_code
        FROM albums
        ORDER BY album_code
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python3 get_batch_cdma_codes.py <batch_number> [batch_size]")
        print("Example: python3 get_batch_cdma_codes.py 1       # 1st batch (0-99)")
        print("Example: python3 get_batch_cdma_codes.py 2 200   # 2nd batch of 200 (200-399)")
        print()
        sys.exit(1)

    batch_number = int(sys.argv[1])
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    offset = (batch_number - 1) * batch_size

    print(f"# Batch {batch_number} (offset: {offset}, limit: {batch_size})")

    codes = get_batch_cdma_codes(offset, batch_size)

    if len(codes) == 0:
        print("# No more albums to process")
        sys.exit(0)

    print(f"# Found {len(codes)} albums")
    print(" ".join(codes))
