#!/usr/bin/env python3
"""
로컬 SQLite 데이터를 Turso로 동기화하는 스크립트
- album_links.db (로컬) -> Turso (클라우드)
- albums 테이블: 5,103개
- album_platform_links 테이블: 72,148개
"""

import sqlite3
import libsql_experimental as libsql
import os
import sys
from datetime import datetime

# 설정
LOCAL_DB_PATH = '/Users/choejibin/release-album-link/album_links.db'
TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

# 색상
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def check_env():
    """환경 변수 확인"""
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        print(f"{Colors.FAIL}✗ Turso 환경 변수가 설정되지 않았습니다.{Colors.ENDC}")
        print(f"{Colors.WARNING}다음 환경 변수를 설정하세요:{Colors.ENDC}")
        print("  - TURSO_DATABASE_URL")
        print("  - TURSO_AUTH_TOKEN")
        sys.exit(1)

    print(f"{Colors.OKGREEN}✓ Turso 환경 변수 확인 완료{Colors.ENDC}")

def get_local_connection():
    """로컬 SQLite 연결"""
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_turso_connection():
    """Turso 연결"""
    return libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

def create_turso_tables(turso_conn):
    """Turso에 테이블 생성"""
    print(f"\n{Colors.OKCYAN}Turso에 테이블 생성 중...{Colors.ENDC}")

    # albums 테이블
    turso_conn.execute('''
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

    turso_conn.execute('CREATE INDEX IF NOT EXISTS idx_album_code ON albums (album_code)')
    turso_conn.execute('CREATE INDEX IF NOT EXISTS idx_release_date ON albums (release_date)')

    # album_platform_links 테이블
    turso_conn.execute('''
        CREATE TABLE IF NOT EXISTS album_platform_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_ko TEXT,
            artist_en TEXT,
            album_ko TEXT,
            album_en TEXT,
            platform_type TEXT,
            platform_id TEXT,
            platform_name TEXT,
            platform_url TEXT,
            platform_code TEXT,
            album_id TEXT,
            upc TEXT,
            found INTEGER DEFAULT 0,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            album_cover_url TEXT,
            release_date TEXT,
            UNIQUE(artist_ko, album_ko, platform_id, platform_type)
        )
    ''')

    turso_conn.execute('CREATE INDEX IF NOT EXISTS idx_album_artist ON album_platform_links(artist_ko, album_ko)')
    turso_conn.execute('CREATE INDEX IF NOT EXISTS idx_platform_type ON album_platform_links(platform_type)')
    turso_conn.execute('CREATE INDEX IF NOT EXISTS idx_found ON album_platform_links(found)')

    # short_links 테이블
    turso_conn.execute('''\n        CREATE TABLE IF NOT EXISTS short_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            artist_ko TEXT NOT NULL,
            album_ko TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            click_count INTEGER DEFAULT 0,
            last_clicked_at DATETIME
        )
    ''')

    turso_conn.execute('CREATE INDEX IF NOT EXISTS idx_short_code ON short_links(short_code)')

    turso_conn.commit()

    print(f"{Colors.OKGREEN}✓ 테이블 생성 완료{Colors.ENDC}")

def sync_albums(local_conn, turso_conn):
    """albums 테이블 동기화"""
    print(f"\n{Colors.BOLD}albums 테이블 동기화 중...{Colors.ENDC}")

    # 로컬에서 모든 앨범 가져오기
    local_cursor = local_conn.cursor()
    local_cursor.execute('SELECT * FROM albums')
    albums = local_cursor.fetchall()

    print(f"로컬: {len(albums)}개 앨범 발견")

    # Turso 기존 데이터 삭제
    print(f"{Colors.WARNING}Turso 기존 데이터 삭제 중...{Colors.ENDC}")
    turso_conn.execute('DELETE FROM albums')
    turso_conn.commit()

    # 배치 삽입
    batch_size = 100
    inserted_count = 0

    for i in range(0, len(albums), batch_size):
        batch = albums[i:i+batch_size]

        for album in batch:
            try:
                turso_conn.execute('''
                    INSERT OR REPLACE INTO albums
                    (album_code, artist_ko, artist_en, album_ko, album_en,
                     release_date, album_type, label, distributor, genre, uci,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    album['album_code'],
                    album['artist_ko'],
                    album['artist_en'],
                    album['album_ko'],
                    album['album_en'],
                    album['release_date'],
                    album['album_type'],
                    album['label'],
                    album['distributor'],
                    album['genre'],
                    album['uci'],
                    album['created_at'],
                    album['updated_at']
                ))
                inserted_count += 1
            except Exception as e:
                print(f"{Colors.WARNING}경고: {album['album_code']} 삽입 실패 - {str(e)[:50]}{Colors.ENDC}")

        turso_conn.commit()
        print(f"진행: {min(i+batch_size, len(albums))}/{len(albums)} ({inserted_count}개 삽입됨)")

    print(f"{Colors.OKGREEN}✓ albums 동기화 완료: {inserted_count}개{Colors.ENDC}")
    return inserted_count

def sync_platform_links(local_conn, turso_conn):
    """album_platform_links 테이블 동기화"""
    print(f"\n{Colors.BOLD}album_platform_links 테이블 동기화 중...{Colors.ENDC}")

    # 로컬에서 모든 플랫폼 링크 가져오기
    local_cursor = local_conn.cursor()
    local_cursor.execute('SELECT * FROM album_platform_links')
    links = local_cursor.fetchall()

    print(f"로컬: {len(links)}개 플랫폼 링크 발견")

    # Turso 기존 데이터 삭제
    print(f"{Colors.WARNING}Turso 기존 데이터 삭제 중...{Colors.ENDC}")
    turso_conn.execute('DELETE FROM album_platform_links')
    turso_conn.commit()

    # 배치 삽입
    batch_size = 100
    inserted_count = 0

    for i in range(0, len(links), batch_size):
        batch = links[i:i+batch_size]

        for link in batch:
            try:
                turso_conn.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type,
                     platform_id, platform_name, platform_url, platform_code,
                     album_id, upc, found, status, created_at, album_cover_url, release_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    link['artist_ko'],
                    link['artist_en'],
                    link['album_ko'],
                    link['album_en'],
                    link['platform_type'],
                    link['platform_id'],
                    link['platform_name'],
                    link['platform_url'],
                    link['platform_code'],
                    link['album_id'],
                    link['upc'],
                    link['found'],
                    link['status'],
                    link['created_at'],
                    link['album_cover_url'],
                    link['release_date']
                ))
                inserted_count += 1
            except Exception as e:
                # UNIQUE 제약 위반은 무시
                if 'UNIQUE constraint failed' not in str(e):
                    print(f"{Colors.WARNING}경고: 링크 삽입 실패 - {str(e)[:50]}{Colors.ENDC}")

        turso_conn.commit()
        print(f"진행: {min(i+batch_size, len(links))}/{len(links)} ({inserted_count}개 삽입됨)")

    print(f"{Colors.OKGREEN}✓ album_platform_links 동기화 완료: {inserted_count}개{Colors.ENDC}")
    return inserted_count

def verify_sync(turso_conn):
    """동기화 검증"""
    print(f"\n{Colors.OKCYAN}Turso 데이터 검증 중...{Colors.ENDC}")

    # albums 카운트
    result = turso_conn.execute('SELECT COUNT(*) as count FROM albums')
    row = result.fetchone()
    albums_count = row[0] if isinstance(row, tuple) else row['count']
    print(f"albums: {albums_count}개")

    # album_platform_links 카운트
    result = turso_conn.execute('SELECT COUNT(*) as count FROM album_platform_links')
    row = result.fetchone()
    links_count = row[0] if isinstance(row, tuple) else row['count']
    print(f"album_platform_links: {links_count}개")

    # 플랫폼 타입별 카운트
    result = turso_conn.execute('''
        SELECT platform_type, COUNT(*) as count
        FROM album_platform_links
        GROUP BY platform_type
    ''')

    for row in result.fetchall():
        platform_type = row[0] if isinstance(row, tuple) else row['platform_type']
        count = row[1] if isinstance(row, tuple) else row['count']
        print(f"  - {platform_type}: {count}개")

    print(f"{Colors.OKGREEN}✓ 검증 완료{Colors.ENDC}")

def main():
    """메인 실행"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}")
    print(f"  로컬 SQLite → Turso 동기화")
    print(f"{'='*70}{Colors.ENDC}\n")

    # 환경 변수 확인
    check_env()

    # 연결
    print(f"\n{Colors.OKCYAN}데이터베이스 연결 중...{Colors.ENDC}")
    local_conn = get_local_connection()
    turso_conn = get_turso_connection()
    print(f"{Colors.OKGREEN}✓ 연결 완료{Colors.ENDC}")

    start_time = datetime.now()

    try:
        # 테이블 생성
        create_turso_tables(turso_conn)

        # 동기화
        albums_synced = sync_albums(local_conn, turso_conn)
        links_synced = sync_platform_links(local_conn, turso_conn)

        # 검증
        verify_sync(turso_conn)

        # 결과
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}")
        print(f"  동기화 완료")
        print(f"{'='*70}{Colors.ENDC}\n")
        print(f"{Colors.OKGREEN}✓ albums: {albums_synced}개{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ album_platform_links: {links_synced}개{Colors.ENDC}")
        print(f"소요 시간: {duration:.1f}초\n")

    except Exception as e:
        print(f"\n{Colors.FAIL}✗ 동기화 실패: {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        local_conn.close()
        turso_conn.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}사용자에 의해 중단되었습니다.{Colors.ENDC}\n")
        sys.exit(0)
