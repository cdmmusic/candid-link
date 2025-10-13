#!/usr/bin/env python3
"""
Vercel Serverless Function - 음악 플랫폼 링크 API
Turso (libSQL) 데이터베이스 사용
"""

from flask import Flask, request, jsonify, render_template_string
import os
import json
from datetime import datetime

# Turso libsql 클라이언트 import
try:
    import libsql_experimental as libsql
    USE_TURSO = True
except ImportError:
    USE_TURSO = False
    print("Error: libsql_experimental required for Vercel deployment")

app = Flask(__name__)

# 환경 변수에서 Turso 설정 가져오기
TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

# 로컬 개발용 SQLite 경로
LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'album_links.db')

def get_db_connection():
    """데이터베이스 연결 (Turso)"""
    if not USE_TURSO:
        raise Exception("libsql_experimental is required for Vercel deployment")
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise Exception("Turso credentials not found in environment variables")

    # Turso 연결
    conn = libsql.connect(
        database=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )
    return conn

def dict_from_row(row, cursor=None):
    """Row 객체를 딕셔너리로 변환"""
    if USE_TURSO and cursor:
        # Turso: cursor.description을 사용하여 컬럼명 매핑
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    elif hasattr(row, 'keys'):
        # SQLite Row 객체
        return dict(row)
    else:
        # fallback: 그대로 반환
        return row

@app.route('/', methods=['GET'])
def index():
    """웹 UI - 메인 페이지 (앨범 목록)"""
    html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LINKSALAD - 음악 플랫폼 링크</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
            background: #f8f9fa;
            color: #212529;
        }

        /* Header */
        .header {
            background: white;
            border-bottom: 1px solid #e9ecef;
            padding: 16px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
        }

        .logo {
            font-size: 24px;
            font-weight: 700;
            color: #007bff;
            text-decoration: none;
        }

        .search-box {
            flex: 1;
            max-width: 500px;
            position: relative;
        }

        .search-input {
            width: 100%;
            padding: 10px 40px 10px 16px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-input:focus {
            border-color: #007bff;
        }

        .search-icon {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #adb5bd;
        }

        /* Main Content */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        .page-header {
            margin-bottom: 20px;
        }

        .page-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 15px;
        }

        /* Album List */
        .album-table {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .table-header {
            display: grid;
            grid-template-columns: 1fr 300px 100px;
            padding: 15px 20px;
            background: #f8f9fa;
            font-size: 13px;
            font-weight: 600;
            color: #6c757d;
            border-bottom: 1px solid #e9ecef;
        }

        .table-row {
            display: grid;
            grid-template-columns: 1fr 300px 100px;
            padding: 15px 20px;
            align-items: center;
            border-bottom: 1px solid #f1f3f5;
            cursor: pointer;
            transition: background 0.2s;
            text-decoration: none;
            color: inherit;
        }

        .table-row:hover {
            background: #f8f9fa;
        }

        .table-row:last-child {
            border-bottom: none;
        }

        .album-cell {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .album-cover {
            width: 60px;
            height: 60px;
            border-radius: 6px;
            object-fit: cover;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .album-info-cell {
            flex: 1;
            min-width: 0;
        }

        .album-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .album-date {
            font-size: 13px;
            color: #6c757d;
        }

        .artist-cell {
            font-size: 15px;
            color: #495057;
        }

        .date-cell {
            font-size: 14px;
            color: #6c757d;
            text-align: right;
        }

        .loading, .no-data {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
            font-size: 15px;
        }

        .error {
            background: #fff3cd;
            color: #856404;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }

        /* Mobile Responsive */
        @media (max-width: 768px) {
            .header-content {
                flex-wrap: wrap;
            }

            .search-box {
                order: 3;
                flex: 1 0 100%;
                max-width: 100%;
            }

            .table-header {
                display: none;
            }

            .table-row {
                grid-template-columns: 1fr;
                gap: 12px;
                padding: 15px;
            }

            .album-cell {
                grid-column: 1;
            }

            .artist-cell {
                padding-left: 75px;
                font-size: 14px;
            }

            .date-cell {
                padding-left: 75px;
                text-align: left;
                font-size: 13px;
            }

            .album-cover {
                width: 50px;
                height: 50px;
            }

            .page-title {
                font-size: 22px;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="header-content">
            <a href="/" class="logo">🔗 캔디드뮤직 링크</a>
            <div class="search-box">
                <input type="text" class="search-input" placeholder="아티스트, 앨범 검색" id="search-input">
                <span class="search-icon">🔍</span>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">신규 발매 앨범</h1>
        </div>

        <div class="album-table">
            <div class="table-header">
                <div>앨범</div>
                <div>아티스트</div>
                <div style="text-align: right;">발매일</div>
            </div>
            <div id="album-list">
                <div class="loading">앨범 목록 로딩 중...</div>
            </div>
        </div>
    </div>

    <script>
        let allAlbums = [];
        let currentPage = 1;
        let hasMore = true;
        let isLoading = false;
        let searchQuery = '';

        async function loadAlbums(append = false) {
            if (isLoading || !hasMore) return;

            isLoading = true;

            try {
                const response = await fetch(`/api/albums-with-links?page=${currentPage}&limit=50`);
                const data = await response.json();

                if (!data.success) {
                    throw new Error(data.error || '앨범 로드 실패');
                }

                if (append) {
                    allAlbums = [...allAlbums, ...data.albums];
                    appendAlbums(data.albums);
                } else {
                    allAlbums = data.albums;
                    displayAlbums(data.albums);
                }

                hasMore = data.has_more;
                currentPage++;

            } catch (error) {
                document.getElementById('album-list').innerHTML =
                    `<div class="error">⚠️ ${error.message}</div>`;
            } finally {
                isLoading = false;
            }
        }

        function displayAlbums(albums) {
            const albumList = document.getElementById('album-list');

            if (albums.length === 0) {
                albumList.innerHTML = '<div class="no-data">등록된 앨범이 없습니다</div>';
                return;
            }

            const html = albums.map(album => createAlbumHTML(album)).join('');
            albumList.innerHTML = html;
        }

        function appendAlbums(albums) {
            const albumList = document.getElementById('album-list');
            const html = albums.map(album => createAlbumHTML(album)).join('');
            albumList.insertAdjacentHTML('beforeend', html);
        }

        function createAlbumHTML(album) {
            const releaseDate = (album.release_date && album.release_date.trim() !== '') ?
                album.release_date.substring(0, 10) : '미정';

            const albumId = encodeURIComponent(album.artist_ko + '|||' + album.album_ko);

            return `
                <a href="/album/${albumId}" class="table-row">
                    <div class="album-cell">
                        ${album.album_cover_url ?
                            `<img src="${album.album_cover_url}" alt="${album.album_ko}" class="album-cover" onerror="this.style.display='none'">` :
                            '<div class="album-cover" style="background:#e9ecef;"></div>'}
                        <div class="album-info-cell">
                            <div class="album-title">${album.album_ko}</div>
                        </div>
                    </div>
                    <div class="artist-cell">${album.artist_ko}</div>
                    <div class="date-cell">${releaseDate}</div>
                </a>
            `;
        }

        // 무한 스크롤
        window.addEventListener('scroll', () => {
            if (searchQuery) return;
            if (!hasMore || isLoading) return;

            const scrollPosition = window.innerHeight + window.scrollY;
            const threshold = document.documentElement.offsetHeight - 200;

            console.log('Scroll:', {scrollPosition, threshold, hasMore, isLoading});

            if (scrollPosition >= threshold) {
                console.log('Loading more albums...');
                loadAlbums(true);
            }
        });

        // 검색 기능 - 엔터키로 검색 페이지 이동
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = e.target.value.trim();
                if (query) {
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
        });

        loadAlbums();
    </script>
</body>
</html>
    """
    return render_template_string(html)

@app.route('/api/albums-with-links', methods=['GET'])
def get_albums_with_links():
    """모든 앨범과 플랫폼 링크 조회 (웹 UI용) - 페이지네이션 지원"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # 전체 앨범 수 조회
        cursor.execute('''
            SELECT COUNT(DISTINCT artist_ko || '|||' || album_ko) as total
            FROM album_platform_links
        ''')
        # fetchone 전에 컬럼 정보 저장
        total_columns = [desc[0] for desc in cursor.description] if USE_TURSO else None
        total_row = cursor.fetchone()
        if USE_TURSO and total_columns:
            total_dict = dict(zip(total_columns, total_row))
        else:
            total_dict = dict(total_row)
        total_count = total_dict['total']

        # 앨범 목록 조회 (페이지네이션)
        # 서브쿼리로 앨범별 최신 레코드를 먼저 가져온 후 페이지네이션 적용
        cursor.execute('''
            SELECT artist_ko, artist_en, album_ko, album_en, album_cover_url, release_date
            FROM (
                SELECT
                    artist_ko,
                    artist_en,
                    album_ko,
                    album_en,
                    album_cover_url,
                    release_date,
                    MAX(created_at) as latest_created_at,
                    ROW_NUMBER() OVER (PARTITION BY artist_ko, album_ko ORDER BY created_at DESC) as rn
                FROM album_platform_links
                WHERE release_date IS NULL
                   OR release_date = ''
                   OR datetime(release_date) <= datetime('now', 'localtime')
                GROUP BY artist_ko, album_ko
            )
            WHERE rn = 1
            ORDER BY
                CASE WHEN album_cover_url IS NOT NULL AND album_cover_url != '' THEN 0 ELSE 1 END,
                release_date DESC,
                latest_created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        albums_data = []
        # fetchall 전에 컬럼 정보 저장
        albums_columns = [desc[0] for desc in cursor.description] if USE_TURSO else None
        for row in cursor.fetchall():
            if USE_TURSO and albums_columns:
                row_dict = dict(zip(albums_columns, row))
            else:
                row_dict = dict(row)

            albums_data.append({
                'artist_ko': row_dict['artist_ko'],
                'artist_en': row_dict['artist_en'],
                'album_ko': row_dict['album_ko'],
                'album_en': row_dict['album_en'],
                'album_cover_url': row_dict['album_cover_url'],
                'release_date': row_dict['release_date']
            })

        conn.close()

        return jsonify({
            'success': True,
            'count': len(albums_data),
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_more': (offset + len(albums_data)) < total_count,
            'albums': albums_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/album/<path:album_id>', methods=['GET'])
def album_detail(album_id):
    """앨범 상세 페이지"""
    try:
        # URL 디코딩 및 아티스트/앨범명 분리
        from urllib.parse import unquote
        decoded_id = unquote(album_id)
        parts = decoded_id.split('|||')

        if len(parts) != 2:
            return "잘못된 앨범 ID 형식입니다.", 400

        artist_ko, album_ko = parts

        # 데이터베이스에서 앨범 정보 조회
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT artist_ko, artist_en, album_ko, album_en, album_cover_url, release_date
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            LIMIT 1
        ''', (artist_ko, album_ko))

        # 앨범 정보 가져오기
        album_columns = [desc[0] for desc in cursor.description] if USE_TURSO else None
        album_row = cursor.fetchone()

        if not album_row:
            return "앨범을 찾을 수 없습니다.", 404

        if USE_TURSO and album_columns:
            album_dict = dict(zip(album_columns, album_row))
        else:
            album_dict = dict(album_row)

        # 플랫폼 링크 조회
        cursor.execute('''
            SELECT platform_type, platform_id, platform_code, platform_name,
                   platform_url, found
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            ORDER BY platform_type, platform_name
        ''', (artist_ko, album_ko))

        platforms_columns = [desc[0] for desc in cursor.description] if USE_TURSO else None
        platforms = []
        for p in cursor.fetchall():
            if USE_TURSO and platforms_columns:
                p_dict = dict(zip(platforms_columns, p))
            else:
                p_dict = dict(p)
            platforms.append(p_dict)

        conn.close()

        # HTML 생성
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{album_dict['album_ko']} - {album_dict['artist_ko']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
            background: #f8f9fa;
            color: #212529;
        }}

        .header {{
            background: white;
            border-bottom: 1px solid #e9ecef;
            padding: 16px 20px;
        }}

        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .back-button {{
            font-size: 24px;
            text-decoration: none;
            color: #6c757d;
        }}

        .logo {{
            font-size: 24px;
            font-weight: 700;
            color: #007bff;
            text-decoration: none;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }}

        .album-header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            display: flex;
            gap: 30px;
            align-items: flex-start;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        .album-cover-large {{
            width: 200px;
            height: 200px;
            border-radius: 12px;
            object-fit: cover;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        .album-info {{
            flex: 1;
        }}

        .album-title-large {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .artist-name-large {{
            font-size: 20px;
            color: #6c757d;
            margin-bottom: 15px;
        }}

        .release-date {{
            font-size: 16px;
            color: #868e96;
        }}

        .platforms-section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        .section-title {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
        }}

        .platforms-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }}

        .platform-card {{
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }}

        .platform-card.found {{
            background: #f8f9fa;
        }}

        .platform-card.found:hover {{
            background: #e9ecef;
            transform: translateY(-2px);
        }}

        .platform-card.not-found {{
            background: #fff;
            opacity: 0.5;
        }}

        .platform-name {{
            font-size: 15px;
            font-weight: 600;
        }}

        .platform-link {{
            text-decoration: none;
            color: #007bff;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .platform-link:hover {{
            text-decoration: underline;
        }}

        .not-found-text {{
            color: #adb5bd;
            font-size: 14px;
        }}

        @media (max-width: 768px) {{
            .album-header {{
                flex-direction: column;
                align-items: center;
                text-align: center;
            }}

            .album-cover-large {{
                width: 150px;
                height: 150px;
            }}

            .album-title-large {{
                font-size: 24px;
            }}

            .artist-name-large {{
                font-size: 18px;
            }}

            .platforms-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <a href="/" class="back-button">←</a>
            <a href="/" class="logo">🔗 캔디드뮤직 링크</a>
        </div>
    </div>

    <div class="container">
        <div class="album-header">
            {'<img src="' + album_dict['album_cover_url'] + '" alt="앨범 커버" class="album-cover-large">' if album_dict.get('album_cover_url') else '<div class="album-cover-large" style="background:#e9ecef;"></div>'}
            <div class="album-info">
                <h1 class="album-title-large">{album_dict['album_ko']}</h1>
                <div class="artist-name-large">{album_dict['artist_ko']}</div>
                <div class="release-date">발매일: {album_dict['release_date'][:10] if album_dict.get('release_date') else '미정'}</div>
            </div>
        </div>

        <div class="platforms-section">
            <h2 class="section-title">스트리밍 플랫폼 링크</h2>
            <div class="platforms-grid">
"""

        # 플랫폼 카드 생성
        for platform in platforms:
            found = platform['found']
            card_class = 'found' if found else 'not-found'

            if found:
                html += f"""
                <a href="{platform['platform_url']}" target="_blank" class="platform-card {card_class}" style="text-decoration: none; color: inherit;">
                    <div class="platform-name">{platform['platform_name']}</div>
                    <div class="platform-link">열기 →</div>
                </a>
"""
            else:
                html += f"""
                <div class="platform-card {card_class}">
                    <div class="platform-name">{platform['platform_name']}</div>
                    <div class="not-found-text">미등록</div>
                </div>
"""

        html += """
            </div>
        </div>
    </div>
</body>
</html>
"""

        return render_template_string(html)

    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}", 500

@app.route('/search', methods=['GET'])
def search():
    """검색 페이지"""
    query = request.args.get('q', '')

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>검색: {query} - 캔디드뮤직 링크</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
            background: #f8f9fa;
            color: #212529;
        }}
        .header {{
            background: white;
            border-bottom: 1px solid #e9ecef;
            padding: 16px 20px;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 700;
            color: #007bff;
            text-decoration: none;
        }}
        .search-box {{
            flex: 1;
            max-width: 500px;
            position: relative;
        }}
        .search-input {{
            width: 100%;
            padding: 10px 40px 10px 16px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
        }}
        .search-input:focus {{
            border-color: #007bff;
        }}
        .search-icon {{
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #adb5bd;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }}
        .page-header {{
            margin-bottom: 20px;
        }}
        .page-title {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .search-info {{
            font-size: 15px;
            color: #6c757d;
        }}
        .album-table {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .table-header {{
            display: grid;
            grid-template-columns: 1fr 300px 100px;
            padding: 15px 20px;
            background: #f8f9fa;
            font-size: 13px;
            font-weight: 600;
            color: #6c757d;
            border-bottom: 1px solid #e9ecef;
        }}
        .table-row {{
            display: grid;
            grid-template-columns: 1fr 300px 100px;
            padding: 15px 20px;
            align-items: center;
            border-bottom: 1px solid #f1f3f5;
            cursor: pointer;
            transition: background 0.2s;
            text-decoration: none;
            color: inherit;
        }}
        .table-row:hover {{
            background: #f8f9fa;
        }}
        .album-cell {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .album-cover {{
            width: 60px;
            height: 60px;
            border-radius: 6px;
            object-fit: cover;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .album-info-cell {{
            flex: 1;
            min-width: 0;
        }}
        .album-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .artist-cell {{
            font-size: 15px;
            color: #495057;
        }}
        .date-cell {{
            font-size: 14px;
            color: #6c757d;
            text-align: right;
        }}
        .loading, .no-data {{
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
            font-size: 15px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <a href="/" class="logo">🔗 캔디드뮤직 링크</a>
            <div class="search-box">
                <input type="text" class="search-input" placeholder="아티스트, 앨범 검색" id="search-input" value="{query}">
                <span class="search-icon">🔍</span>
            </div>
        </div>
    </div>
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">검색 결과</h1>
            <div class="search-info" id="search-info">"{query}" 검색 중...</div>
        </div>
        <div class="album-table">
            <div class="table-header">
                <div>앨범</div>
                <div>아티스트</div>
                <div style="text-align: right;">발매일</div>
            </div>
            <div id="album-list">
                <div class="loading">검색 중...</div>
            </div>
        </div>
    </div>
    <script>
        const searchQuery = '{query}';

        document.getElementById('search-input').addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                const query = e.target.value.trim();
                if (query) {{
                    window.location.href = `/search?q=${{encodeURIComponent(query)}}`;
                }}
            }}
        }});

        async function search() {{
            try {{
                const response = await fetch(`/api/search?q=${{encodeURIComponent(searchQuery)}}`);
                const data = await response.json();

                if (!data.success) {{
                    throw new Error(data.error || '검색 실패');
                }}

                document.getElementById('search-info').textContent =
                    `"${{searchQuery}}" 검색 결과: ${{data.count}}개`;

                const albumList = document.getElementById('album-list');

                if (data.albums.length === 0) {{
                    albumList.innerHTML = '<div class="no-data">검색 결과가 없습니다</div>';
                    return;
                }}

                const html = data.albums.map(album => {{
                    const releaseDate = (album.release_date && album.release_date.trim() !== '') ?
                        album.release_date.substring(0, 10) : '미정';
                    const albumId = encodeURIComponent(album.artist_ko + '|||' + album.album_ko);

                    return `
                        <a href="/album/${{albumId}}" class="table-row">
                            <div class="album-cell">
                                ${{album.album_cover_url ?
                                    `<img src="${{album.album_cover_url}}" alt="${{album.album_ko}}" class="album-cover" onerror="this.style.display='none'">` :
                                    '<div class="album-cover" style="background:#e9ecef;"></div>'}}
                                <div class="album-info-cell">
                                    <div class="album-title">${{album.album_ko}}</div>
                                </div>
                            </div>
                            <div class="artist-cell">${{album.artist_ko}}</div>
                            <div class="date-cell">${{releaseDate}}</div>
                        </a>
                    `;
                }}).join('');

                albumList.innerHTML = html;

            }} catch (error) {{
                document.getElementById('album-list').innerHTML =
                    `<div class="no-data">⚠️ ${{error.message}}</div>`;
            }}
        }}

        search();
    </script>
</body>
</html>
    """
    return render_template_string(html)

@app.route('/api/search', methods=['GET'])
def api_search():
    """검색 API"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': '검색어를 입력하세요'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # LIKE 검색 (대소문자 무시)
        search_pattern = f'%{query}%'

        cursor.execute('''
            SELECT DISTINCT artist_ko, artist_en, album_ko, album_en, album_cover_url, release_date
            FROM album_platform_links
            WHERE artist_ko LIKE ? OR artist_en LIKE ? OR album_ko LIKE ? OR album_en LIKE ?
            ORDER BY
                CASE WHEN album_cover_url IS NOT NULL AND album_cover_url != '' THEN 0 ELSE 1 END,
                release_date DESC
            LIMIT 200
        ''', (search_pattern, search_pattern, search_pattern, search_pattern))

        albums_columns = [desc[0] for desc in cursor.description] if USE_TURSO else None
        albums = []
        for row in cursor.fetchall():
            if USE_TURSO and albums_columns:
                row_dict = dict(zip(albums_columns, row))
            else:
                row_dict = dict(row)
            albums.append(row_dict)

        conn.close()

        return jsonify({
            'success': True,
            'count': len(albums),
            'query': query,
            'albums': albums
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    db_type = 'turso' if (USE_TURSO and TURSO_DATABASE_URL) else 'sqlite'
    return jsonify({
        'status': 'ok',
        'service': 'album-links-api',
        'version': '2.0.0',
        'database': db_type
    })

# Vercel은 app 객체를 직접 사용
# if __name__ == '__main__': 블록은 로컬 개발용
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
