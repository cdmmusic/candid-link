#!/usr/bin/env python3
"""
Excel 파일에서 앨범 데이터를 읽어서 DB에 저장
트랙별 데이터를 앨범 단위로 그룹화
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

# 파일 경로
EXCEL_PATH = '/Users/choejibin/Downloads/발매앨범DB.xlsx'
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'album_links.db')

def get_db_connection():
    """SQLite DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def import_excel_data():
    """Excel 파일에서 데이터 읽어서 DB에 저장"""

    print(f"Excel 파일 읽는 중: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)

    # 앨범 단위로 그룹화 (앨범명 + 아티스트명)
    albums = df.groupby(['앨범명', '아티스트명', '발매일']).first().reset_index()

    print(f"\n총 {len(df)} 트랙 → {len(albums)} 앨범")

    conn = get_db_connection()
    cursor = conn.cursor()

    imported_count = 0
    skipped_count = 0

    for idx, album in albums.iterrows():
        album_ko = str(album['앨범명']).strip()
        artist_ko = str(album['앨범 아티스트명']).strip() if pd.notna(album['앨범 아티스트명']) else str(album['아티스트명']).strip()
        album_en = str(album['영문 앨범명']).strip() if pd.notna(album['영문 앨범명']) else album_ko
        artist_en = str(album['영문 앨범아티스트명']).strip() if pd.notna(album['영문 앨범아티스트명']) else artist_ko
        release_date = str(album['발매일'])[:10] if pd.notna(album['발매일']) else None

        # 이미 존재하는 앨범인지 확인
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
        ''', (artist_ko, album_ko))

        exists = cursor.fetchone()['cnt'] > 0

        if exists:
            print(f"[SKIP] {artist_ko} - {album_ko} (이미 존재)")
            skipped_count += 1
            continue

        # 기본 플랫폼 데이터 생성 (found=0으로 초기화)
        platforms = [
            # 국내 플랫폼
            ('kr', 'melon', 'melon', '멜론'),
            ('kr', 'genie', 'genie', '지니뮤직'),
            ('kr', 'bugs', 'bugs', '벅스'),
            ('kr', 'flo', 'flo', 'FLO'),
            ('kr', 'vibe', 'vibe', 'VIBE'),
            # 글로벌 플랫폼
            ('global', None, 'itm', 'Apple Music'),
            ('global', None, 'spotify', 'Spotify'),
            ('global', None, 'youtube', 'YouTube'),
            ('global', None, 'amazon', 'Amazon Music'),
            ('global', None, 'deezer', 'Deezer'),
            ('global', None, 'tidal', 'Tidal'),
            ('global', None, 'kkbox', 'KKBox'),
            ('global', None, 'anghami', 'Anghami'),
            ('global', None, 'pandora', 'Pandora'),
            ('global', None, 'line', 'LINE Music'),
            ('global', None, 'awa', 'AWA'),
            ('global', None, 'moov', 'Moov'),
            ('global', None, 'tct', 'TCT'),
        ]

        for platform_type, platform_id, platform_code, platform_name in platforms:
            try:
                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en,
                     platform_type, platform_id, platform_code, platform_name,
                     platform_url, album_cover_url, release_date, found, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', '', ?, 0, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko, artist_en, album_ko, album_en,
                    platform_type, platform_id, platform_code, platform_name,
                    release_date
                ))
            except sqlite3.IntegrityError:
                # 중복 무시
                pass

        imported_count += 1
        print(f"[OK] {artist_ko} - {album_ko} (발매일: {release_date})")

    conn.commit()
    conn.close()

    print(f"\n완료!")
    print(f"- 임포트: {imported_count}개 앨범")
    print(f"- 스킵: {skipped_count}개 앨범")
    print(f"- 총 플랫폼 레코드: {imported_count * len(platforms)}개")

if __name__ == '__main__':
    import_excel_data()
