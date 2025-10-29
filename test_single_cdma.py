#!/usr/bin/env python3
"""
특정 CDMA 코드로 테스트
"""
import sys
import sqlite3
sys.path.insert(0, '.')
from collect_test_local import process_album, get_db_connection

def test_single_cdma(cdma_code):
    """특정 CDMA 코드 테스트"""
    print("=" * 60)
    print(f"  Testing CDMA: {cdma_code}")
    print("=" * 60)

    conn = get_db_connection()
    conn.text_factory = str
    cursor = conn.cursor()

    cursor.execute('''
        SELECT album_code, artist_ko, album_ko, artist_en, album_en
        FROM albums
        WHERE album_code = ?
    ''', (cdma_code,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"Album with CDMA {cdma_code} not found!")
        return

    cdma, artist_ko, album_ko, artist_en, album_en = row
    artist_en = artist_en if artist_en else ''
    album_en = album_en if album_en else ''

    print(f"\nAlbum Info:")
    print(f"  CDMA: {cdma}")
    print(f"  Artist: {artist_ko}")
    print(f"  Album: {album_ko}")
    if artist_en:
        print(f"  Artist EN: {artist_en}")
    if album_en:
        print(f"  Album EN: {album_en}")
    print()
    print("-" * 60)

    try:
        kr_found, global_found, total_found = process_album(
            artist_ko, artist_en, album_ko, album_en, cdma
        )
        print("\n" + "=" * 60)
        print(f"  Test Complete!")
        print("=" * 60)
        print(f"Korean Platforms: {kr_found}/5")
        print(f"Global Platforms: {global_found}")
        print(f"Total: {total_found} platforms")
        print()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cdma = sys.argv[1] if len(sys.argv) > 1 else "CDMA00100"
    test_single_cdma(cdma)
