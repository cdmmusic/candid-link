#!/usr/bin/env python3
"""
Vercel Serverless Function - 음악 플랫폼 링크 API
Turso (libSQL) 데이터베이스 사용
"""

from flask import Flask, request, jsonify, render_template_string, render_template
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

app = Flask(__name__, template_folder='../templates', static_folder='../static')

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
    """웹 UI - 메인 페이지 (home_v2.html 사용)"""
    return render_template('home_v2.html')

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
            SELECT DISTINCT artist_ko, artist_en, album_ko, album_en, album_cover_url, release_date
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
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

        # 플랫폼 이름 변환 및 로고 매핑
        platform_name_map = {
            '멜론': 'Melon',
            '벅스': 'Bugs',
            '지니뮤직': 'Genie',
            'TCT': 'QQ MUSIC'
        }

        platform_logos = {
            'Melon': 'https://cdnimg.melon.co.kr/resource/image/web/common/logo_melon142x99.png',
            'FLO': 'https://www.music-flo.com/image/v2/icon/ico_flo_192.png',
            'Genie': 'https://www.genie.co.kr/resources/images/common/logo_genie_mo.png',
            'VIBE': 'https://music-phinf.pstatic.net/20200713_140/1594609570298EfHBo_PNG/vibe_app_icon.png',
            'Bugs': 'https://image.bugsm.co.kr/resource/web/common/logo_bugs.png',
            'Apple Music': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Apple_Music_icon.svg/200px-Apple_Music_icon.svg.png',
            'Spotify': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/200px-Spotify_logo_without_text.svg.png',
            'YouTube': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/YouTube_full-color_icon_%282017%29.svg/200px-YouTube_full-color_icon_%282017%29.svg.png',
            'Amazon Music': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Amazon_Music_logo.svg/200px-Amazon_Music_logo.svg.png',
            'Deezer': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Deezer_logo.svg/200px-Deezer_logo.svg.png',
            'Tidal': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Tidal_%28service%29_logo.svg/200px-Tidal_%28service%29_logo.svg.png',
            'KKBox': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/KKBOX_logo.svg/200px-KKBOX_logo.svg.png',
            'Anghami': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Anghami_logo.svg/200px-Anghami_logo.svg.png',
            'Pandora': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Pandora_wordmark.svg/200px-Pandora_wordmark.svg.png',
            'LINE Music': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/LINE_logo.svg/200px-LINE_logo.svg.png',
            'AWA': 'https://awa.fm/assets/img/icon_512x512.png',
            'Moov': 'https://www.moov.hk/static/img/moov_logo_512x512.png',
            'QQ MUSIC': 'https://y.qq.com/favicon.ico'
        }

        platforms_data = []
        for p in platforms:
            platform_name = platform_name_map.get(p['platform_name'], p['platform_name'])
            platforms_data.append({
                'platform_name': platform_name,
                'platform_url': p['platform_url'] or '',
                'platform_logo': platform_logos.get(platform_name, ''),
                'found': bool(p['found'])
            })

        platforms_json = json.dumps(platforms_data)

        # 앨범 데이터
        album_data = {
            'artist_ko': album_dict['artist_ko'],
            'artist_en': album_dict.get('artist_en') or '',
            'album_ko': album_dict['album_ko'],
            'album_en': album_dict.get('album_en') or '',
            'album_cover_url': album_dict.get('album_cover_url') or '',
            'release_date': album_dict.get('release_date') or ''
        }

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

@app.route('/api/save', methods=['POST'])
def save_album_links():
    """
    n8n에서 앨범 링크 데이터를 받아서 Turso DB에 저장
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        req_data = data.get('request', {})
        artist_ko = req_data.get('artist', '')
        album_ko = req_data.get('album', '')
        artist_en = artist_ko
        album_en = album_ko
        album_cover_url = data.get('album_cover_url', '')
        
        kr_platforms = data.get('kr_platforms', {})
        global_platforms = data.get('global_platforms', {})

        conn = get_db_connection()
        cursor = conn.cursor()

        # 기존 release_date 조회
        cursor.execute('''
            SELECT release_date FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            LIMIT 1
        ''', (artist_ko, album_ko))
        
        existing_row = cursor.fetchone()
        if existing_row:
            existing_dict = dict_from_row(existing_row, cursor)
            release_date = existing_dict['release_date']
        else:
            release_date = None

        saved_count = 0

        # 국내 플랫폼 저장 (UPDATE or INSERT)
        for platform_id, platform_data in kr_platforms.items():
            # 기존 레코드 확인
            cursor.execute('''
                SELECT id, found FROM album_platform_links
                WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'kr' AND platform_id = ?
            ''', (artist_ko, album_ko, platform_id))

            existing_record = cursor.fetchone()
            is_found = platform_data.get('found', False)

            if existing_record and is_found:
                # UPDATE: found를 1로 업데이트하고 URL 추가
                cursor.execute('''
                    UPDATE album_platform_links
                    SET platform_url = ?, album_id = ?, album_cover_url = ?, found = 1, status = ?
                    WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'kr' AND platform_id = ?
                ''', (
                    platform_data.get('album_url', ''), platform_data.get('album_id', ''),
                    album_cover_url, platform_data.get('status', ''),
                    artist_ko, album_ko, platform_id
                ))
            elif existing_record:
                # 기존 레코드가 있지만 못 찾은 경우: 그대로 유지 (found=0)
                pass
            else:
                # INSERT: 새 레코드
                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type, platform_id,
                     platform_name, platform_url, album_id, album_cover_url, release_date, found, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko, artist_en, album_ko, album_en, 'kr', platform_id,
                    platform_data.get('name', ''), platform_data.get('album_url', ''),
                    platform_data.get('album_id', ''), album_cover_url, release_date,
                    1 if is_found else 0, platform_data.get('status', '')
                ))
            saved_count += 1

        # 해외 플랫폼 저장 (UPDATE or INSERT)
        for platform_code, platform_data in global_platforms.items():
            # 기존 레코드 확인
            cursor.execute('''
                SELECT id, found FROM album_platform_links
                WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'global' AND platform_code = ?
            ''', (artist_ko, album_ko, platform_code))

            existing_record = cursor.fetchone()
            is_found = platform_data.get('found', False)

            if existing_record and is_found:
                # UPDATE: found를 1로 업데이트하고 URL 추가
                cursor.execute('''
                    UPDATE album_platform_links
                    SET platform_url = ?, upc = ?, album_cover_url = ?, found = 1
                    WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'global' AND platform_code = ?
                ''', (
                    platform_data.get('url', ''), platform_data.get('upc', ''),
                    album_cover_url,
                    artist_ko, album_ko, platform_code
                ))
            elif existing_record:
                # 기존 레코드가 있지만 못 찾은 경우: 그대로 유지
                pass
            else:
                # INSERT: 새 레코드
                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type, platform_code,
                     platform_name, platform_url, upc, album_cover_url, release_date, found, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko, artist_en, album_ko, album_en, 'global', platform_code,
                    platform_data.get('name', ''), platform_data.get('url', ''),
                    platform_data.get('upc', ''), album_cover_url, release_date,
                    1 if is_found else 0
                ))
            saved_count += 1

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'saved_count': saved_count,
            'message': f'Successfully saved {saved_count} platform links'
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
