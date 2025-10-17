#!/usr/bin/env python3
"""
발매앨범DB.xlsx 파일의 데이터를 Turso 데이터베이스에 임포트
앨범 단위로 중복 제거하여 저장
"""

import pandas as pd
import libsql_experimental as libsql
import os
from datetime import datetime

# Turso 연결 정보
TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

def import_albums():
    """엑셀 파일에서 앨범 정보를 읽어 데이터베이스에 저장"""

    # 엑셀 파일 읽기
    print("📖 엑셀 파일 읽는 중...")
    df = pd.read_excel('발매앨범DB.xlsx')
    print(f"   총 {len(df)}개의 트랙 데이터 발견")

    # 앨범 단위로 그룹화 (앨범정산코드 기준)
    print("\n🔄 앨범 단위로 데이터 그룹화 중...")
    albums_df = df.groupby('앨범정산코드').first().reset_index()
    print(f"   총 {len(albums_df)}개의 고유 앨범 발견")

    # Turso 연결
    print("\n🔗 Turso 데이터베이스 연결 중...")
    conn = libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )
    cursor = conn.cursor()

    # albums 테이블이 없으면 생성
    print("📦 albums 테이블 생성 중...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_code TEXT UNIQUE NOT NULL,
            artist_ko TEXT NOT NULL,
            artist_en TEXT,
            album_ko TEXT NOT NULL,
            album_en TEXT,
            release_date TEXT,
            album_type TEXT,
            label TEXT,
            distributor TEXT,
            genre TEXT,
            uci TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_album_code ON albums(album_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_release_date ON albums(release_date)')

    # 데이터 삽입
    print("\n💾 앨범 데이터 저장 중...")
    inserted = 0
    skipped = 0

    for idx, row in albums_df.iterrows():
        try:
            album_code = row['앨범정산코드']
            artist_ko = row['아티스트명']
            album_ko = row['앨범명']

            # 필수 필드가 없으면 스킵
            if pd.isna(album_code) or pd.isna(artist_ko) or pd.isna(album_ko):
                skipped += 1
                continue

            # 발매일 처리
            release_date = None
            if not pd.isna(row['발매일']):
                try:
                    release_date = pd.to_datetime(row['발매일']).strftime('%Y-%m-%d')
                except:
                    pass

            # INSERT OR REPLACE
            cursor.execute('''
                INSERT OR REPLACE INTO albums
                (album_code, artist_ko, artist_en, album_ko, album_en,
                 release_date, album_type, label, distributor, genre, uci, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                str(album_code),
                str(artist_ko),
                str(row.get('영문 앨범아티스트명', '')) if not pd.isna(row.get('영문 앨범아티스트명')) else None,
                str(album_ko),
                str(row.get('영문 앨범명', '')) if not pd.isna(row.get('영문 앨범명')) else None,
                release_date,
                str(row.get('앨범타입', '')) if not pd.isna(row.get('앨범타입')) else None,
                str(row.get('기획사', '')) if not pd.isna(row.get('기획사')) else None,
                str(row.get('유통사', '')) if not pd.isna(row.get('유통사')) else None,
                str(row.get('장르', '')) if not pd.isna(row.get('장르')) else None,
                str(row.get('UCI', '')) if not pd.isna(row.get('UCI')) else None
            ))

            inserted += 1

            if (idx + 1) % 100 == 0:
                print(f"   진행중: {idx + 1}/{len(albums_df)} ({inserted}개 저장)")

        except Exception as e:
            print(f"   ⚠️  오류 ({album_code}): {e}")
            skipped += 1
            continue

    conn.commit()
    conn.close()

    print(f"\n✅ 완료!")
    print(f"   저장: {inserted}개")
    print(f"   스킵: {skipped}개")
    print(f"   총계: {inserted + skipped}개")

if __name__ == '__main__':
    import_albums()
