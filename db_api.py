#!/usr/bin/env python3
"""
간단한 Flask API - n8n에서 앨범 링크를 SQLite DB에 저장
"""

from flask import Flask, request, jsonify, render_template_string
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)

# SQLite DB 경로
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'album_links.db')

def get_db_connection():
    """SQLite DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
            // 검색 중이면 무한 스크롤 비활성화
            if (searchQuery) return;

            const scrollPosition = window.innerHeight + window.scrollY;
            const threshold = document.documentElement.offsetHeight - 500;

            if (scrollPosition >= threshold && hasMore && !isLoading) {
                loadAlbums(true);
            }
        });

        // 검색 기능
        document.getElementById('search-input').addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase().trim();

            if (searchQuery === '') {
                // 검색 해제 - 처음부터 다시 로드
                currentPage = 1;
                hasMore = true;
                allAlbums = [];
                loadAlbums(false);
                return;
            }

            const filtered = allAlbums.filter(album =>
                album.album_ko.toLowerCase().includes(searchQuery) ||
                album.artist_ko.toLowerCase().includes(searchQuery) ||
                (album.album_en && album.album_en.toLowerCase().includes(searchQuery)) ||
                (album.artist_en && album.artist_en.toLowerCase().includes(searchQuery))
            );

            displayAlbums(filtered);
        });

        // 페이지 로드 시 데이터 가져오기
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
        # 페이지네이션 파라미터
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
        total_count = cursor.fetchone()['total']

        # 앨범 목록 조회 (페이지네이션)
        # 발매일/서비스시간이 현재 시각 이전인 앨범만 표시
        # 빈 문자열(''), NULL은 미정으로 간주하여 표시
        # 앨범 커버가 있는 것을 우선 표시, 그 다음 최신 발매일 순
        cursor.execute('''
            SELECT DISTINCT artist_ko, artist_en, album_ko, album_en, album_cover_url, release_date
            FROM album_platform_links
            WHERE release_date IS NULL
               OR release_date = ''
               OR datetime(release_date) <= datetime('now', 'localtime')
            ORDER BY
                CASE WHEN album_cover_url IS NOT NULL AND album_cover_url != '' THEN 0 ELSE 1 END,
                release_date DESC,
                created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        albums_data = []
        for row in cursor.fetchall():
            artist_ko = row['artist_ko']
            album_ko = row['album_ko']

            # 각 앨범의 플랫폼 링크 조회
            cursor.execute('''
                SELECT platform_type, platform_id, platform_code, platform_name,
                       platform_url, album_id, upc, found, status
                FROM album_platform_links
                WHERE artist_ko = ? AND album_ko = ?
                ORDER BY platform_type, platform_name
            ''', (artist_ko, album_ko))

            platforms = []
            found_count = 0
            for p in cursor.fetchall():
                platforms.append({
                    'platform_type': p['platform_type'],
                    'platform_id': p['platform_id'],
                    'platform_code': p['platform_code'],
                    'platform_name': p['platform_name'],
                    'platform_url': p['platform_url'],
                    'found': bool(p['found'])
                })
                if p['found']:
                    found_count += 1

            albums_data.append({
                'artist_ko': artist_ko,
                'artist_en': row['artist_en'],
                'album_ko': album_ko,
                'album_en': row['album_en'],
                'album_cover_url': row['album_cover_url'],
                'release_date': row['release_date'],
                'platform_count': len(platforms),
                'found_count': found_count,
                'platforms': platforms
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
        # album_id 디코딩 (artist|||album 형식)
        decoded = album_id.replace('%7C%7C%7C', '|||')
        parts = decoded.split('|||')
        if len(parts) != 2:
            return "Invalid album ID", 400

        artist_ko, album_ko = parts

        conn = get_db_connection()
        cursor = conn.cursor()

        # 앨범 정보 조회
        cursor.execute('''
            SELECT DISTINCT artist_ko, artist_en, album_ko, album_en, album_cover_url, release_date
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
        ''', (artist_ko, album_ko))

        album_row = cursor.fetchone()
        if not album_row:
            conn.close()
            return "Album not found", 404

        # 플랫폼 링크 조회
        cursor.execute('''
            SELECT platform_type, platform_id, platform_code, platform_name,
                   platform_url, found
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            ORDER BY platform_type, platform_name
        ''', (artist_ko, album_ko))

        platforms = cursor.fetchall()
        conn.close()

        # HTML 생성
        album_data = {
            'artist_ko': album_row['artist_ko'],
            'artist_en': album_row['artist_en'],
            'album_ko': album_row['album_ko'],
            'album_en': album_row['album_en'],
            'album_cover_url': album_row['album_cover_url'] or '',
            'release_date': album_row['release_date'] or ''
        }

        # 플랫폼 이름 변환 (한글 → 영어)
        platform_name_map = {
            '멜론': 'Melon',
            '벅스': 'Bugs',
            '지니뮤직': 'Genie',
            'TCT': 'QQ MUSIC'
        }

        # 플랫폼 로고 매핑
        platform_logos = {
            # 한국 플랫폼
            'Melon': 'https://cdnimg.melon.co.kr/resource/image/web/common/logo_melon142x99.png',
            'FLO': 'https://www.music-flo.com/image/v2/icon/ico_flo_192.png',
            'Genie': 'https://www.genie.co.kr/resources/images/common/logo_genie_mo.png',
            'VIBE': 'https://music-phinf.pstatic.net/20200713_140/1594609570298EfHBo_PNG/vibe_app_icon.png',
            'Bugs': 'https://image.bugsm.co.kr/resource/web/common/logo_bugs.png',
            # 글로벌 플랫폼
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

        platforms_data = [{
            'platform_name': platform_name_map.get(p['platform_name'], p['platform_name']),
            'platform_url': p['platform_url'] or '',
            'platform_logo': platform_logos.get(platform_name_map.get(p['platform_name'], p['platform_name']), ''),
            'found': bool(p['found'])
        } for p in platforms]

        # JSON 데이터를 미리 변환
        platforms_json = json.dumps(platforms_data)

    except Exception as e:
        return f"Error: {str(e)}", 500

    html = f'''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{album_data["album_ko"]} - {album_data["artist_ko"]} | LINKSALAD</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
            background: #f8f9fa;
            color: #212529;
        }}

        /* Header */
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
            font-size: 20px;
            font-weight: 700;
            color: #007bff;
            text-decoration: none;
        }}

        /* Album Header */
        .album-header {{
            background: white;
            padding: 40px 20px;
            border-bottom: 1px solid #e9ecef;
        }}

        .album-header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            gap: 30px;
            align-items: flex-start;
        }}

        .album-cover-large {{
            width: 240px;
            height: 240px;
            border-radius: 12px;
            object-fit: cover;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            flex-shrink: 0;
        }}

        .album-info {{
            flex: 1;
            padding-top: 10px;
        }}

        .album-title-large {{
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 12px;
            line-height: 1.2;
        }}

        .album-artist {{
            font-size: 20px;
            color: #6c757d;
            margin-bottom: 20px;
        }}

        .album-meta {{
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            font-size: 14px;
            color: #6c757d;
        }}

        .meta-label {{
            font-weight: 600;
            color: #495057;
            margin-right: 8px;
        }}

        .share-btn {{
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}

        .share-btn:hover {{
            background: #0056b3;
        }}

        /* Platform Grid */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .section-title {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .platform-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }}

        .platform-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}

        .platform-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}

        .platform-card.disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            pointer-events: none;
        }}

        .platform-info {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }}

        .platform-logo {{
            width: 40px;
            height: 40px;
            object-fit: contain;
            flex-shrink: 0;
        }}

        .platform-name {{
            font-size: 16px;
            font-weight: 600;
            color: #212529;
        }}

        .play-icon {{
            width: 40px;
            height: 40px;
            background: #f8f9fa;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }}

        .platform-card:hover .play-icon {{
            background: #007bff;
            color: white;
        }}

        .share-modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}

        .share-modal.active {{
            display: flex;
        }}

        .share-content {{
            background: white;
            padding: 30px;
            border-radius: 16px;
            max-width: 400px;
            width: 90%;
        }}

        .share-content h3 {{
            margin-bottom: 20px;
            font-size: 20px;
        }}

        .share-url {{
            width: 100%;
            padding: 12px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 15px;
        }}

        .copy-btn {{
            width: 100%;
            padding: 12px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }}

        .copy-btn:hover {{
            background: #218838;
        }}

        .close-btn {{
            width: 100%;
            padding: 12px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
        }}

        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .album-header-content {{
                flex-direction: column;
                align-items: center;
                text-align: center;
            }}

            .album-cover-large {{
                width: 200px;
                height: 200px;
            }}

            .album-title-large {{
                font-size: 28px;
            }}

            .album-artist {{
                font-size: 18px;
            }}

            .album-meta {{
                justify-content: center;
            }}

            .platform-grid {{
                grid-template-columns: 1fr;
            }}

            .container {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="header-content">
            <a href="/" class="logo">🔗 캔디드뮤직 링크</a>
        </div>
    </div>

    <!-- Album Header -->
    <div class="album-header">
        <div class="album-header-content">
            <img src="{album_data['album_cover_url']}" alt="{album_data['album_ko']}" class="album-cover-large" onerror="this.style.display='none'">
            <div class="album-info">
                <h1 class="album-title-large">{album_data['album_ko']}</h1>
                <div class="album-artist">{album_data['artist_ko']}</div>
                <div class="album-meta">
                    <div class="meta-item">
                        <span class="meta-label">발매일</span>
                        {album_data['release_date'] if album_data['release_date'] else '미정'}
                    </div>
                </div>
                <button class="share-btn" onclick="openShareModal()">
                    <span>🔗</span> 공유하기
                </button>
            </div>
        </div>
    </div>

    <!-- Platform Links -->
    <div class="container">
        <h2 class="section-title">
            <span>🎵</span> 스트리밍 플랫폼
        </h2>
        <div class="platform-grid" id="platform-grid">
            <!-- Platform cards will be inserted here -->
        </div>
    </div>

    <!-- Share Modal -->
    <div class="share-modal" id="share-modal" onclick="closeShareModal(event)">
        <div class="share-content" onclick="event.stopPropagation()">
            <h3>링크 공유</h3>
            <input type="text" class="share-url" id="share-url" readonly value="{request.url}">
            <button class="copy-btn" onclick="copyToClipboard()">📋 링크 복사</button>
            <button class="close-btn" onclick="closeShareModal()">닫기</button>
        </div>
    </div>

    <script>
        const platformsData = {platforms_json};

        function renderPlatforms() {{
            const grid = document.getElementById('platform-grid');
            const html = platformsData.map(platform => {{
                const disabled = !platform.found || !platform.platform_url;
                const logoHtml = platform.platform_logo ?
                    `<img src="${{platform.platform_logo}}" alt="${{platform.platform_name}}" class="platform-logo" onerror="this.style.display='none'">` : '';

                return `
                    <a href="${{platform.platform_url}}"
                       target="_blank"
                       class="platform-card ${{disabled ? 'disabled' : ''}}">
                        <div class="platform-info">
                            ${{logoHtml}}
                            <div class="platform-name">${{platform.platform_name}}</div>
                        </div>
                        <div class="play-icon">▶</div>
                    </a>
                `;
            }}).join('');
            grid.innerHTML = html;
        }}

        function openShareModal() {{
            document.getElementById('share-modal').classList.add('active');
        }}

        function closeShareModal(event) {{
            if (!event || event.target.id === 'share-modal') {{
                document.getElementById('share-modal').classList.remove('active');
            }}
        }}

        function copyToClipboard() {{
            const input = document.getElementById('share-url');
            input.select();
            document.execCommand('copy');

            const btn = event.target;
            btn.textContent = '✓ 복사완료!';
            btn.style.background = '#28a745';

            setTimeout(() => {{
                btn.textContent = '📋 링크 복사';
            }}, 2000);
        }}

        renderPlatforms();
    </script>
</body>
</html>
    '''
    return render_template_string(html)

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'db-api',
        'version': '1.0.0'
    })

@app.route('/save', methods=['POST'])
def save_album_links():
    """
    n8n에서 앨범 링크 데이터를 받아서 DB에 저장

    요청 형식:
    {
      "request": {
        "artist": "이혁재",
        "album": "AGIT"
      },
      "kr_platforms": {
        "melon": { "name": "멜론", "album_url": "...", "found": true, "status": "success" }
      },
      "global_platforms": {
        "itm": { "name": "Apple Music", "url": "...", "upc": "...", "found": true }
      }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 앨범 정보 추출
        req_data = data.get('request', {})
        artist_ko = req_data.get('artist', '')
        album_ko = req_data.get('album', '')

        # artist_en, album_en은 global_platforms에서 추출 시도
        artist_en = artist_ko
        album_en = album_ko

        # 앨범 커버 URL
        album_cover_url = data.get('album_cover_url', '')

        kr_platforms = data.get('kr_platforms', {})
        global_platforms = data.get('global_platforms', {})

        conn = get_db_connection()
        cursor = conn.cursor()

        # 기존 레코드에서 release_date 조회 (있으면 유지)
        cursor.execute('''
            SELECT release_date FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            LIMIT 1
        ''', (artist_ko, album_ko))

        existing_row = cursor.fetchone()
        release_date = existing_row['release_date'] if existing_row else None

        saved_count = 0

        # 국내 플랫폼 저장 (중복 방지: 먼저 삭제 후 삽입)
        for platform_id, platform_data in kr_platforms.items():
            try:
                # 기존 데이터 삭제
                cursor.execute('''
                    DELETE FROM album_platform_links
                    WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'kr' AND platform_id = ?
                ''', (artist_ko, album_ko, platform_id))

                # 새 데이터 삽입 (release_date 보존)
                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type, platform_id,
                     platform_name, platform_url, album_id, album_cover_url, release_date, found, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko,
                    artist_en,
                    album_ko,
                    album_en,
                    'kr',
                    platform_id,
                    platform_data.get('name', ''),
                    platform_data.get('album_url', ''),
                    platform_data.get('album_id', ''),
                    album_cover_url,
                    release_date,
                    1 if platform_data.get('found') else 0,
                    platform_data.get('status', '')
                ))
                saved_count += 1
            except sqlite3.IntegrityError:
                # 중복 데이터는 무시
                pass

        # 해외 플랫폼 저장 (중복 방지: 먼저 삭제 후 삽입)
        for platform_code, platform_data in global_platforms.items():
            try:
                # 기존 데이터 삭제
                cursor.execute('''
                    DELETE FROM album_platform_links
                    WHERE artist_ko = ? AND album_ko = ? AND platform_type = 'global' AND platform_code = ?
                ''', (artist_ko, album_ko, platform_code))

                # 새 데이터 삽입 (release_date 보존)
                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type, platform_code,
                     platform_name, platform_url, upc, album_cover_url, release_date, found, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko,
                    artist_en,
                    album_ko,
                    album_en,
                    'global',
                    platform_code,
                    platform_data.get('name', ''),
                    platform_data.get('url', ''),
                    platform_data.get('upc', ''),
                    album_cover_url,
                    release_date,
                    1 if platform_data.get('found') else 0
                ))
                saved_count += 1
            except sqlite3.IntegrityError:
                # 중복 데이터는 무시
                pass

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'saved_count': saved_count,
            'message': f'Successfully saved {saved_count} platform links'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/query', methods=['GET'])
def query_album_links():
    """
    앨범 링크 조회

    Query params:
    - artist: 아티스트명 (필수)
    - album: 앨범명 (필수)
    """
    artist = request.args.get('artist', '')
    album = request.args.get('album', '')

    if not artist or not album:
        return jsonify({'error': 'artist and album parameters are required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            ORDER BY platform_type, platform_name
        ''', (artist, album))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'artist_ko': row['artist_ko'],
                'artist_en': row['artist_en'],
                'album_ko': row['album_ko'],
                'album_en': row['album_en'],
                'platform_type': row['platform_type'],
                'platform_id': row['platform_id'],
                'platform_code': row['platform_code'],
                'platform_name': row['platform_name'],
                'platform_url': row['platform_url'],
                'album_id': row['album_id'],
                'upc': row['upc'],
                'found': bool(row['found']),
                'status': row['status'],
                'created_at': row['created_at']
            })

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/list', methods=['GET'])
def list_albums():
    """저장된 모든 앨범 목록 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT artist_ko, album_ko,
                   COUNT(*) as platform_count,
                   SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as found_count
            FROM album_platform_links
            GROUP BY artist_ko, album_ko
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                'artist': row['artist_ko'],
                'album': row['album_ko'],
                'platform_count': row['platform_count'],
                'found_count': row['found_count']
            })

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Starting DB API server...")
    print(f"Database: {DB_PATH}")
    app.run(host='0.0.0.0', port=5002, debug=True)
