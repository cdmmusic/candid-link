#!/usr/bin/env python3
"""
발매일이 없는 앨범의 발매일을 Excel 파일에서 찾아서 업데이트
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

def update_release_dates():
    """발매일 업데이트"""

    print(f"Excel 파일 읽는 중: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)

    # 앨범 단위로 그룹화
    albums = df.groupby(['앨범명', '아티스트명']).agg({
        '앨범 아티스트명': 'first',
        '발매일': 'first'
    }).reset_index()

    print(f"Excel에서 {len(albums)}개 앨범 로드 완료\n")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 발매일이 없는 앨범 조회
    cursor.execute('''
        SELECT DISTINCT artist_ko, album_ko
        FROM album_platform_links
        WHERE release_date IS NULL OR release_date = ''
    ''')

    albums_without_date = cursor.fetchall()
    print(f"발매일이 없는 앨범: {len(albums_without_date)}개\n")

    updated_count = 0
    not_found_count = 0

    for row in albums_without_date:
        artist_ko = row['artist_ko']
        album_ko = row['album_ko']

        # Excel에서 매칭되는 앨범 찾기
        # 아티스트명이나 앨범 아티스트명으로 매칭 시도
        matched = albums[
            (albums['앨범명'] == album_ko) &
            ((albums['아티스트명'] == artist_ko) | (albums['앨범 아티스트명'] == artist_ko))
        ]

        if len(matched) > 0:
            release_date = matched.iloc[0]['발매일']

            if pd.notna(release_date):
                release_date_str = str(release_date)[:10]  # YYYY-MM-DD 형식

                # DB 업데이트 (해당 앨범의 모든 플랫폼 레코드)
                cursor.execute('''
                    UPDATE album_platform_links
                    SET release_date = ?
                    WHERE artist_ko = ? AND album_ko = ?
                ''', (release_date_str, artist_ko, album_ko))

                updated_count += 1
                print(f"[OK] {artist_ko} - {album_ko} → {release_date_str}")
            else:
                print(f"[SKIP] {artist_ko} - {album_ko} (Excel에 발매일 없음)")
                not_found_count += 1
        else:
            print(f"[NOT FOUND] {artist_ko} - {album_ko}")
            not_found_count += 1

    conn.commit()
    conn.close()

    print(f"\n완료!")
    print(f"- 업데이트: {updated_count}개 앨범")
    print(f"- 찾지 못함/발매일 없음: {not_found_count}개 앨범")

if __name__ == '__main__':
    update_release_dates()
