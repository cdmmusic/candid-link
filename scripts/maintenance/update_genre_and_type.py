#!/usr/bin/env python3
"""
Excel 파일에서 장르와 앨범타입을 읽어서 기존 DB 레코드 업데이트
"""

import pandas as pd
import sqlite3
import os

# 파일 경로
EXCEL_PATH = '/Users/choejibin/Downloads/발매앨범DB.xlsx'
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'album_links.db')

def get_db_connection():
    """SQLite DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def update_genre_and_type():
    """Excel 파일에서 장르와 앨범타입을 읽어서 DB 업데이트"""

    print(f"Excel 파일 읽는 중: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)

    # 앨범 단위로 그룹화 (앨범명 + 아티스트명)
    albums = df.groupby(['앨범명', '아티스트명']).first().reset_index()

    print(f"\n총 {len(albums)} 앨범")

    conn = get_db_connection()
    cursor = conn.cursor()

    updated_count = 0
    skipped_count = 0
    not_found_count = 0

    for idx, album in albums.iterrows():
        album_ko = str(album['앨범명']).strip()
        artist_ko = str(album['앨범 아티스트명']).strip() if pd.notna(album['앨범 아티스트명']) else str(album['아티스트명']).strip()
        genre = str(album['장르']).strip() if pd.notna(album['장르']) else ''
        release_type = str(album['앨범타입']).strip() if pd.notna(album['앨범타입']) else ''

        # DB에서 해당 앨범 찾기
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
        ''', (artist_ko, album_ko))

        exists = cursor.fetchone()['cnt'] > 0

        if not exists:
            print(f"[NOT FOUND] {artist_ko} - {album_ko}")
            not_found_count += 1
            continue

        # 장르와 앨범타입이 모두 비어있으면 스킵
        if not genre and not release_type:
            print(f"[SKIP] {artist_ko} - {album_ko} (장르/타입 데이터 없음)")
            skipped_count += 1
            continue

        # 업데이트
        cursor.execute('''
            UPDATE album_platform_links
            SET genre = ?, release_type = ?
            WHERE artist_ko = ? AND album_ko = ?
        ''', (genre, release_type, artist_ko, album_ko))

        updated_count += 1
        print(f"[OK] {artist_ko} - {album_ko} | 장르: {genre} | 타입: {release_type}")

    conn.commit()
    conn.close()

    print(f"\n완료!")
    print(f"- 업데이트: {updated_count}개 앨범")
    print(f"- 스킵: {skipped_count}개 앨범 (데이터 없음)")
    print(f"- 미발견: {not_found_count}개 앨범 (DB에 없음)")

if __name__ == '__main__':
    update_genre_and_type()
