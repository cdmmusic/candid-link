#!/usr/bin/env python3
"""
관리자 페이지 API - 데이터베이스 관리 시스템
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, render_template_string
import sqlite3
from datetime import datetime
import os
from functools import wraps
import json
import qrcode
from io import BytesIO
import base64
import string
import random

# .env 파일 로드 시도
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않았습니다. 기본값을 사용합니다.")

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# 세션 보안 설정
app.secret_key = os.environ.get('ADMIN_SECRET_KEY', 'dev-secret-key-change-in-production')

# SQLite DB 경로
DB_PATH = os.path.join(os.path.dirname(__file__), 'album_links.db')

# 관리자 계정 (환경변수에서 로드, 없으면 기본값)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'cdm2025!@#')

def get_db_connection():
    """SQLite DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ===== 인증 관련 라우트 =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """관리자 로그인"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('로그인 성공!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('아이디 또는 비밀번호가 잘못되었습니다.', 'error')

    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """관리자 로그아웃"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('admin_login'))

# ===== 메인 사이트 =====

@app.route('/')
def index():
    """메인 페이지 - 링크 사이트"""
    return render_template('home.html')

# ===== 대시보드 =====

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """관리자 대시보드"""
    return render_template('admin/dashboard.html')

# ===== API 엔드포인트 =====

@app.route('/admin/api/stats')
@login_required
def admin_api_stats():
    """전체 통계 API"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 전체 앨범 수
        cursor.execute('''
            SELECT COUNT(DISTINCT artist_ko || '|||' || album_ko) as total_albums
            FROM album_platform_links
        ''')
        total_albums = cursor.fetchone()['total_albums']

        # 플랫폼별 링크 수
        cursor.execute('''
            SELECT platform_type, COUNT(*) as count
            FROM album_platform_links
            GROUP BY platform_type
        ''')
        platform_stats = [dict(row) for row in cursor.fetchall()]

        # 수집 완료율
        cursor.execute('''
            SELECT
                COUNT(*) as total_links,
                SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as found_links
            FROM album_platform_links
        ''')
        link_stats = cursor.fetchone()
        total_links = link_stats['total_links']
        found_links = link_stats['found_links']
        completion_rate = (found_links / total_links * 100) if total_links > 0 else 0

        # 최근 업데이트 (7일)
        cursor.execute('''
            SELECT COUNT(DISTINCT artist_ko || '|||' || album_ko) as recent_updates
            FROM album_platform_links
            WHERE datetime(created_at) >= datetime('now', '-7 days')
        ''')
        recent_updates = cursor.fetchone()['recent_updates']

        # 앨범 커버 있는 앨범 수
        cursor.execute('''
            SELECT COUNT(DISTINCT artist_ko || '|||' || album_ko) as albums_with_cover
            FROM album_platform_links
            WHERE album_cover_url IS NOT NULL AND album_cover_url != ''
        ''')
        albums_with_cover = cursor.fetchone()['albums_with_cover']

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_albums': total_albums,
                'total_links': total_links,
                'found_links': found_links,
                'completion_rate': round(completion_rate, 2),
                'recent_updates': recent_updates,
                'albums_with_cover': albums_with_cover,
                'platform_stats': platform_stats
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/recent-updates')
@login_required
def admin_api_recent_updates():
    """최근 업데이트된 앨범 목록"""
    try:
        limit = int(request.args.get('limit', 10))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT
                artist_ko, album_ko, album_cover_url, release_date,
                MAX(created_at) as last_updated
            FROM album_platform_links
            GROUP BY artist_ko, album_ko
            ORDER BY last_updated DESC
            LIMIT ?
        ''', (limit,))

        updates = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'updates': updates
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 앨범 관리 =====

@app.route('/admin/albums')
@login_required
def admin_albums():
    """앨범 목록 페이지"""
    return render_template('admin/albums_list.html')

@app.route('/admin/api/albums')
@login_required
def admin_api_albums():
    """앨범 목록 API (페이지네이션, 검색, 필터)"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', 'all')  # all, complete, partial, empty
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # 기본 쿼리 - albums 테이블과 조인하여 정확한 정보 가져오기
        base_query = '''
            SELECT
                apl.artist_ko,
                COALESCE(a.artist_en, MAX(apl.artist_en)) as artist_en,
                apl.album_ko,
                COALESCE(a.album_en, MAX(apl.album_en)) as album_en,
                MAX(apl.album_cover_url) as album_cover_url,
                COALESCE(a.release_date, MAX(apl.release_date)) as release_date,
                COUNT(*) as total_platforms,
                SUM(CASE WHEN apl.found = 1 THEN 1 ELSE 0 END) as found_platforms,
                MAX(apl.created_at) as last_updated
            FROM album_platform_links apl
            LEFT JOIN albums a ON apl.artist_ko = a.artist_ko AND apl.album_ko = a.album_ko
        '''

        # WHERE 조건
        where_conditions = []
        params = []

        if search:
            where_conditions.append('(apl.artist_ko LIKE ? OR apl.album_ko LIKE ?)')
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern])

        # WHERE 절 추가
        if where_conditions:
            base_query += ' WHERE ' + ' AND '.join(where_conditions)

        base_query += ' GROUP BY apl.artist_ko, apl.album_ko'

        # HAVING 조건 (상태 필터)
        if status_filter == 'complete':
            base_query += ' HAVING found_platforms = total_platforms'
        elif status_filter == 'partial':
            base_query += ' HAVING found_platforms > 0 AND found_platforms < total_platforms'
        elif status_filter == 'empty':
            base_query += ' HAVING found_platforms = 0'

        # 전체 개수 조회
        count_query = f'SELECT COUNT(*) as total FROM ({base_query})'
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']

        # 데이터 조회
        data_query = base_query + ' ORDER BY last_updated DESC LIMIT ? OFFSET ?'
        cursor.execute(data_query, params + [limit, offset])

        albums = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'albums': albums,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_more': (offset + len(albums)) < total_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/albums/<path:album_id>')
@login_required
def admin_album_detail(album_id):
    """앨범 상세/수정 페이지"""
    try:
        from urllib.parse import unquote
        decoded_id = unquote(album_id)
        parts = decoded_id.split('|||')

        if len(parts) != 2:
            flash('잘못된 앨범 ID입니다.', 'error')
            return redirect(url_for('admin_albums'))

        artist_ko, album_ko = parts

        return render_template('admin/album_edit.html',
                             artist_ko=artist_ko,
                             album_ko=album_ko)

    except Exception as e:
        flash(f'오류: {str(e)}', 'error')
        return redirect(url_for('admin_albums'))

@app.route('/admin/api/albums/<path:album_id>')
@login_required
def admin_api_album_detail(album_id):
    """앨범 상세 정보 API"""
    try:
        from urllib.parse import unquote
        decoded_id = unquote(album_id)
        parts = decoded_id.split('|||')

        if len(parts) != 2:
            return jsonify({'success': False, 'error': '잘못된 앨범 ID'}), 400

        artist_ko, album_ko = parts

        conn = get_db_connection()
        cursor = conn.cursor()

        # 앨범 기본 정보 - albums 테이블과 조인
        cursor.execute('''
            SELECT
                apl.artist_ko,
                COALESCE(a.artist_en, MAX(apl.artist_en)) as artist_en,
                apl.album_ko,
                COALESCE(a.album_en, MAX(apl.album_en)) as album_en,
                MAX(apl.album_cover_url) as album_cover_url,
                COALESCE(a.release_date, MAX(apl.release_date)) as release_date
            FROM album_platform_links apl
            LEFT JOIN albums a ON apl.artist_ko = a.artist_ko AND apl.album_ko = a.album_ko
            WHERE apl.artist_ko = ? AND apl.album_ko = ?
            GROUP BY apl.artist_ko, apl.album_ko
        ''', (artist_ko, album_ko))

        album_info = cursor.fetchone()
        if not album_info:
            return jsonify({'success': False, 'error': '앨범을 찾을 수 없습니다'}), 404

        # 플랫폼 링크 목록
        cursor.execute('''
            SELECT
                id, platform_type, platform_id, platform_code,
                platform_name, platform_url, found, status
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            ORDER BY platform_type, platform_name
        ''', (artist_ko, album_ko))

        platforms = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'album': dict(album_info),
            'platforms': platforms
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/albums/<path:album_id>', methods=['PUT'])
@login_required
def admin_api_update_album(album_id):
    """앨범 정보 수정 API"""
    try:
        from urllib.parse import unquote
        decoded_id = unquote(album_id)
        parts = decoded_id.split('|||')

        if len(parts) != 2:
            return jsonify({'success': False, 'error': '잘못된 앨범 ID'}), 400

        artist_ko, album_ko = parts
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        # 앨범 기본 정보 업데이트
        cursor.execute('''
            UPDATE album_platform_links
            SET artist_en = ?, album_en = ?, album_cover_url = ?, release_date = ?
            WHERE artist_ko = ? AND album_ko = ?
        ''', (
            data.get('artist_en'),
            data.get('album_en'),
            data.get('album_cover_url'),
            data.get('release_date'),
            artist_ko,
            album_ko
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '앨범 정보가 업데이트되었습니다'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/albums/<path:album_id>', methods=['DELETE'])
@login_required
def admin_api_delete_album(album_id):
    """앨범 삭제 API"""
    try:
        from urllib.parse import unquote
        decoded_id = unquote(album_id)
        parts = decoded_id.split('|||')

        if len(parts) != 2:
            return jsonify({'success': False, 'error': '잘못된 앨범 ID'}), 400

        artist_ko, album_ko = parts

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
        ''', (artist_ko, album_ko))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'{deleted_count}개의 레코드가 삭제되었습니다'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/platforms/<int:link_id>', methods=['PUT'])
@login_required
def admin_api_update_platform_link(link_id):
    """개별 플랫폼 링크 수정 API"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE album_platform_links
            SET platform_url = ?, found = ?
            WHERE id = ?
        ''', (
            data.get('platform_url'),
            1 if data.get('found') else 0,
            link_id
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '플랫폼 링크가 업데이트되었습니다'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 플랫폼 링크 관리 =====

@app.route('/admin/platforms')
@login_required
def admin_platforms():
    """플랫폼 링크 관리 페이지"""
    return render_template('admin/platforms.html')

@app.route('/admin/api/platforms')
@login_required
def admin_api_platforms():
    """플랫폼 링크 목록 API (필터링)"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        platform_filter = request.args.get('platform', 'all')  # all, melon, spotify, etc.
        status_filter = request.args.get('status', 'all')  # all, found, not_found
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # WHERE 조건
        where_conditions = []
        params = []

        if platform_filter != 'all':
            where_conditions.append('platform_name = ?')
            params.append(platform_filter)

        if status_filter == 'found':
            where_conditions.append('found = 1')
        elif status_filter == 'not_found':
            where_conditions.append('found = 0')

        where_clause = ' WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''

        # 전체 개수
        cursor.execute(f'SELECT COUNT(*) as total FROM album_platform_links{where_clause}', params)
        total_count = cursor.fetchone()['total']

        # 데이터 조회
        cursor.execute(f'''
            SELECT id, artist_ko, album_ko, platform_type, platform_name,
                   platform_url, found, created_at
            FROM album_platform_links
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [limit, offset])

        links = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'links': links,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_more': (offset + len(links)) < total_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/platforms/stats')
@login_required
def admin_api_platform_stats():
    """플랫폼별 통계"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                platform_name,
                COUNT(*) as total,
                SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as found_count
            FROM album_platform_links
            GROUP BY platform_name
            ORDER BY platform_name
        ''')

        stats = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/platforms/export')
@login_required
def admin_api_platforms_export():
    """플랫폼 링크 CSV 내보내기"""
    try:
        platform_filter = request.args.get('platform', 'all')
        status_filter = request.args.get('status', 'all')

        conn = get_db_connection()
        cursor = conn.cursor()

        # WHERE 조건
        where_conditions = []
        params = []

        if platform_filter != 'all':
            where_conditions.append('platform_name = ?')
            params.append(platform_filter)

        if status_filter == 'found':
            where_conditions.append('found = 1')
        elif status_filter == 'not_found':
            where_conditions.append('found = 0')

        where_clause = ' WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''

        cursor.execute(f'''
            SELECT artist_ko, album_ko, platform_name, platform_url, found
            FROM album_platform_links
            {where_clause}
            ORDER BY artist_ko, album_ko, platform_name
        ''', params)

        rows = cursor.fetchall()
        conn.close()

        # CSV 생성
        import csv
        from io import StringIO
        from flask import make_response

        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['아티스트', '앨범', '플랫폼', 'URL', '수집여부'])

        for row in rows:
            writer.writerow([
                row['artist_ko'],
                row['album_ko'],
                row['platform_name'],
                row['platform_url'] or '',
                '수집됨' if row['found'] else '미수집'
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=platform_links.csv"
        output.headers["Content-type"] = "text/csv; charset=utf-8-sig"
        return output

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 실패 추적 =====

@app.route('/admin/failures')
@login_required
def admin_failures():
    """실패 추적 페이지"""
    return render_template('admin/failures.html')

@app.route('/admin/api/failures')
@login_required
def admin_api_failures():
    """수집 실패 앨범 목록"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # 링크가 하나도 수집되지 않은 앨범
        cursor.execute('''
            SELECT
                artist_ko, album_ko, album_cover_url, release_date,
                COUNT(*) as total_platforms,
                SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as found_count
            FROM album_platform_links
            GROUP BY artist_ko, album_ko
            HAVING found_count = 0
            ORDER BY release_date DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        failures = [dict(row) for row in cursor.fetchall()]

        # 전체 실패 앨범 수
        cursor.execute('''
            SELECT COUNT(*) as total
            FROM (
                SELECT artist_ko, album_ko
                FROM album_platform_links
                GROUP BY artist_ko, album_ko
                HAVING SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) = 0
            )
        ''')
        total_count = cursor.fetchone()['total']

        conn.close()

        return jsonify({
            'success': True,
            'failures': failures,
            'total': total_count,
            'page': page,
            'limit': limit,
            'has_more': (offset + len(failures)) < total_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 일괄 작업 =====

@app.route('/admin/bulk-tools')
@login_required
def admin_bulk_tools():
    """일괄 작업 도구 페이지"""
    return render_template('admin/bulk_tools.html')

@app.route('/admin/api/bulk/import-excel', methods=['POST'])
@login_required
def admin_api_bulk_import_excel():
    """Excel 파일 업로드 및 import"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '파일이 없습니다'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다'}), 400

        # Excel 파일 읽기
        import pandas as pd
        df = pd.read_excel(file)

        # 필수 컬럼 확인
        required_columns = ['artist_ko', 'album_ko']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'success': False, 'error': '필수 컬럼이 없습니다 (artist_ko, album_ko)'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        imported_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            artist_ko = row.get('artist_ko')
            album_ko = row.get('album_ko')

            if not artist_ko or not album_ko:
                skipped_count += 1
                continue

            # 기존 데이터 확인
            cursor.execute('''
                SELECT COUNT(*) as count FROM album_platform_links
                WHERE artist_ko = ? AND album_ko = ?
            ''', (artist_ko, album_ko))

            if cursor.fetchone()['count'] > 0:
                skipped_count += 1
                continue

            # 17개 플랫폼 링크 생성 (기본값)
            platforms = [
                ('kr', 'melon', '멜론'),
                ('kr', 'genie', '지니뮤직'),
                ('kr', 'bugs', '벅스'),
                ('kr', 'flo', 'FLO'),
                ('kr', 'vibe', 'VIBE'),
                ('global', 'itm', 'Apple Music'),
                ('global', 'spotify', 'Spotify'),
                ('global', 'youtube', 'YouTube'),
                ('global', 'amazon', 'Amazon Music'),
                ('global', 'deezer', 'Deezer'),
                ('global', 'tidal', 'Tidal'),
                ('global', 'kkbox', 'KKBox'),
                ('global', 'anghami', 'Anghami'),
                ('global', 'pandora', 'Pandora'),
                ('global', 'linemusic', 'LINE Music'),
                ('global', 'awa', 'AWA'),
                ('global', 'moov', 'Moov')
            ]

            for platform_type, platform_id, platform_name in platforms:
                cursor.execute('''
                    INSERT INTO album_platform_links
                    (artist_ko, artist_en, album_ko, album_en, platform_type,
                     platform_id, platform_name, found, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                ''', (
                    artist_ko,
                    row.get('artist_en', artist_ko),
                    album_ko,
                    row.get('album_en', album_ko),
                    platform_type,
                    platform_id if platform_type == 'kr' else None,
                    platform_name
                ))

            imported_count += 1

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'message': f'{imported_count}개 앨범 추가, {skipped_count}개 건너뜀'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/bulk/clean-duplicates', methods=['POST'])
@login_required
def admin_api_bulk_clean_duplicates():
    """중복 데이터 정리"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 중복 레코드 찾기 (artist_ko, album_ko, platform_type, platform_id가 동일)
        cursor.execute('''
            SELECT artist_ko, album_ko, platform_type, platform_id, COUNT(*) as count
            FROM album_platform_links
            WHERE platform_type = 'kr'
            GROUP BY artist_ko, album_ko, platform_type, platform_id
            HAVING count > 1
        ''')

        kr_duplicates = cursor.fetchall()

        cursor.execute('''
            SELECT artist_ko, album_ko, platform_type, platform_code, COUNT(*) as count
            FROM album_platform_links
            WHERE platform_type = 'global'
            GROUP BY artist_ko, album_ko, platform_type, platform_code
            HAVING count > 1
        ''')

        global_duplicates = cursor.fetchall()

        deleted_count = 0

        # 국내 플랫폼 중복 제거
        for dup in kr_duplicates:
            cursor.execute('''
                DELETE FROM album_platform_links
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM album_platform_links
                    WHERE artist_ko = ? AND album_ko = ?
                      AND platform_type = 'kr' AND platform_id = ?
                )
                AND artist_ko = ? AND album_ko = ?
                AND platform_type = 'kr' AND platform_id = ?
            ''', (dup['artist_ko'], dup['album_ko'], dup['platform_id'],
                  dup['artist_ko'], dup['album_ko'], dup['platform_id']))
            deleted_count += cursor.rowcount

        # 글로벌 플랫폼 중복 제거
        for dup in global_duplicates:
            cursor.execute('''
                DELETE FROM album_platform_links
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM album_platform_links
                    WHERE artist_ko = ? AND album_ko = ?
                      AND platform_type = 'global' AND platform_code = ?
                )
                AND artist_ko = ? AND album_ko = ?
                AND platform_type = 'global' AND platform_code = ?
            ''', (dup['artist_ko'], dup['album_ko'], dup['platform_code'],
                  dup['artist_ko'], dup['album_ko'], dup['platform_code']))
            deleted_count += cursor.rowcount

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'deleted': deleted_count,
            'message': f'{deleted_count}개의 중복 레코드가 삭제되었습니다'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 메인 사이트 API =====

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

# ===== 링크 사이트 페이지 라우트 =====

@app.route('/top100')
def top100_page():
    """TOP 100 페이지"""
    return render_template('top100.html')

@app.route('/latest')
def latest_page():
    """최신 발매 페이지"""
    return render_template('latest.html')

@app.route('/search')
def search_page():
    """검색 페이지"""
    return render_template('search.html')

@app.route('/album/<path:album_id>')
def album_detail_page(album_id):
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
            ORDER BY platform_type, found DESC, platform_name
        ''', (artist_ko, album_ko))

        all_platforms = cursor.fetchall()

        # 중복 제거: 플랫폼명 기준 (대소문자 구분 없이)
        # 우선순위: found=1 > 대소문자 혼합 > 전체 대문자
        platform_dict = {}
        for p in all_platforms:
            platform_key = p['platform_name'].upper()

            # 아직 이 플랫폼을 보지 못한 경우
            if platform_key not in platform_dict:
                platform_dict[platform_key] = p
            else:
                # 이미 있는 경우, 더 좋은 것으로 교체할지 결정
                existing = platform_dict[platform_key]

                # 1순위: found 값이 큰 것 우선
                if p['found'] > existing['found']:
                    platform_dict[platform_key] = p
                elif p['found'] == existing['found']:
                    # 2순위: 대소문자 혼합(정상 표기)을 전체 대문자보다 우선
                    # 전체 대문자가 아닌 것을 선호
                    p_is_mixed = p['platform_name'] != p['platform_name'].upper()
                    existing_is_mixed = existing['platform_name'] != existing['platform_name'].upper()

                    if p_is_mixed and not existing_is_mixed:
                        platform_dict[platform_key] = p

        platforms = list(platform_dict.values())
        conn.close()

        # HTML 생성
        album_data = {
            'artist_ko': album_row['artist_ko'],
            'artist_en': album_row['artist_en'],
            'album_ko': album_row['album_ko'],
            'album_en': album_row['album_en'],
            'album_cover_url': album_row['album_cover_url'] or '',
            'release_date': album_row['release_date'] or '',
            'genre': 'K-Pop',
            'release_type': '정규'
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
    <title>{album_data["album_ko"]} - {album_data["artist_ko"]} | 캔디드뮤직 링크 - 모든 플랫폼의 음악 링크</title>

    <!-- CSS -->
    <link rel="stylesheet" href="/static/css/main.css">

    <!-- Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔗</text></svg>">

    <style>

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
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}

        .album-stats-detail {{
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

        .stat-icon-detail {{
            width: 18px;
            height: 18px;
            display: inline-block;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            vertical-align: middle;
            margin-right: 6px;
        }}

        .stat-icon-detail.view {{
            background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%236c757d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>');
        }}

        .stat-icon-detail.like {{
            background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23dc3545" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>');
        }}

        .stat-value-detail {{
            font-weight: 600;
            color: #6c757d;
            vertical-align: middle;
        }}

        .action-buttons {{
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }}

        .share-button {{
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .share-button:hover {{
            background: #0056b3;
            transform: translateY(-1px);
        }}

        .copy-link-button {{
            padding: 12px 24px;
            background: white;
            color: #007bff;
            border: 2px solid #007bff;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .copy-link-button:hover {{
            background: #f8f9fa;
        }}

        .copy-link-button.copied {{
            background: #28a745;
            color: white;
            border-color: #28a745;
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

        /* 공유 모달 스타일 */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.6);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}

        .modal-overlay.active {{
            display: flex;
        }}

        .share-modal {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}

        .modal-title {{
            font-size: 24px;
            font-weight: 700;
        }}

        .modal-close {{
            background: none;
            border: none;
            font-size: 28px;
            cursor: pointer;
            color: #6c757d;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .modal-close:hover {{
            color: #212529;
        }}

        .share-section {{
            margin-bottom: 24px;
        }}

        .share-section-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #495057;
        }}

        .short-url-container {{
            display: flex;
            gap: 8px;
        }}

        .short-url-input {{
            flex: 1;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            font-family: monospace;
        }}

        .copy-short-url-btn {{
            padding: 12px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .copy-short-url-btn:hover {{
            background: #0056b3;
        }}

        .copy-short-url-btn.copied {{
            background: #28a745;
        }}

        .loading-spinner {{
            padding: 20px;
            text-align: center;
            color: #6c757d;
        }}

        .qr-code-container {{
            display: flex;
            justify-content: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}

        .qr-code-container img {{
            max-width: 200px;
            height: auto;
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
    <!-- 헤더 -->
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">
                <span class="logo-icon">🔗</span>
                <span>캔디드뮤직</span>
            </a>

            <div class="search-container">
                <input
                    type="text"
                    id="search-input"
                    class="search-input"
                    placeholder="아티스트, 앨범 검색..."
                    autocomplete="off">
                <span class="search-icon">🔍</span>
            </div>

            <a href="https://pf.kakao.com/_azxkPn" target="_blank" class="report-button">
                오류제보
            </a>
        </div>
    </header>

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
                    <div class="meta-item">
                        <span class="meta-label">유형</span>
                        {album_data['release_type']}
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">장르</span>
                        {album_data['genre']}
                    </div>
                </div>
                <div class="album-stats-detail">
                    <div class="meta-item">
                        <span class="stat-icon-detail view"></span>
                        <span class="stat-value-detail">12.5K</span>
                    </div>
                    <div class="meta-item">
                        <span class="stat-icon-detail like"></span>
                        <span class="stat-value-detail">1.2K</span>
                    </div>
                </div>
                <div class="action-buttons">
                    <button class="share-button" onclick="shareAlbum()">
                        <span>📤</span>
                        <span>공유하기</span>
                    </button>
                    <button class="copy-link-button" onclick="copyLink()" id="copy-btn">
                        <span>🔗</span>
                        <span id="copy-btn-text">링크 복사</span>
                    </button>
                </div>
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

    <!-- 공유 모달 -->
    <div class="modal-overlay" id="share-modal-overlay" onclick="closeShareModal(event)">
        <div class="share-modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h3 class="modal-title">공유하기</h3>
                <button class="modal-close" onclick="closeShareModal()">&times;</button>
            </div>

            <div class="share-section">
                <div class="share-section-title">짧은 URL</div>
                <div id="short-url-loading" class="loading-spinner">
                    링크 생성 중...
                </div>
                <div id="short-url-content" style="display: none;">
                    <div class="short-url-container">
                        <input type="text" id="short-url-input" class="short-url-input" readonly>
                        <button class="copy-short-url-btn" id="copy-short-url-btn" onclick="copyShortUrl()">
                            복사
                        </button>
                    </div>
                </div>
            </div>

            <div class="share-section">
                <div class="share-section-title">QR 코드</div>
                <div id="qr-loading" class="loading-spinner">
                    QR 코드 생성 중...
                </div>
                <div id="qr-content" class="qr-code-container" style="display: none;">
                    <img id="qr-image" src="" alt="QR Code">
                </div>
            </div>
        </div>
    </div>

    <script>
        const platformsData = {platforms_json};
        const ARTIST_KO = '{album_data['artist_ko']}';
        const ALBUM_KO = '{album_data['album_ko']}';
        let shortUrl = '';

        // 검색 기능 초기화
        const searchInput = document.getElementById('search-input');
        const searchIcon = document.querySelector('.search-icon');

        // 검색 실행 함수
        const performSearchAction = () => {{
            const query = searchInput.value.trim();
            if (query) {{
                window.location.href = `/search?q=${{encodeURIComponent(query)}}`;
            }}
        }};

        // 엔터키로 검색
        searchInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                e.preventDefault();
                performSearchAction();
            }}
        }});

        // 검색 아이콘 클릭으로 검색
        if (searchIcon) {{
            searchIcon.addEventListener('click', () => {{
                performSearchAction();
            }});
        }}

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

        // 공유 모달 열기
        async function shareAlbum() {{
            const modal = document.getElementById('share-modal-overlay');
            modal.classList.add('active');

            // Short URL 생성
            try {{
                const response = await fetch('/api/create-short-link', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        artist_ko: ARTIST_KO,
                        album_ko: ALBUM_KO
                    }})
                }});

                const data = await response.json();

                if (data.success) {{
                    shortUrl = data.short_url;

                    // Short URL 표시
                    document.getElementById('short-url-loading').style.display = 'none';
                    document.getElementById('short-url-content').style.display = 'block';
                    document.getElementById('short-url-input').value = shortUrl;

                    // QR 코드 생성
                    generateQRCode(shortUrl);
                }} else {{
                    document.getElementById('short-url-loading').textContent = '링크 생성 실패';
                }}
            }} catch (error) {{
                console.error('Short URL 생성 오류:', error);
                document.getElementById('short-url-loading').textContent = '링크 생성 실패';
            }}
        }}

        // QR 코드 생성
        async function generateQRCode(url) {{
            try {{
                const response = await fetch('/api/generate-qr', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ url: url }})
                }});

                const data = await response.json();

                if (data.success) {{
                    document.getElementById('qr-loading').style.display = 'none';
                    document.getElementById('qr-content').style.display = 'block';
                    document.getElementById('qr-image').src = data.qr_code;
                }} else {{
                    document.getElementById('qr-loading').textContent = 'QR 생성 실패';
                }}
            }} catch (error) {{
                console.error('QR 코드 생성 오류:', error);
                document.getElementById('qr-loading').textContent = 'QR 생성 실패';
            }}
        }}

        // Short URL 복사
        function copyShortUrl() {{
            const input = document.getElementById('short-url-input');
            const btn = document.getElementById('copy-short-url-btn');

            input.select();
            navigator.clipboard.writeText(input.value).then(() => {{
                btn.textContent = '복사됨!';
                btn.classList.add('copied');

                setTimeout(() => {{
                    btn.textContent = '복사';
                    btn.classList.remove('copied');
                }}, 2000);
            }}).catch(() => {{
                document.execCommand('copy');
                btn.textContent = '복사됨!';
                btn.classList.add('copied');

                setTimeout(() => {{
                    btn.textContent = '복사';
                    btn.classList.remove('copied');
                }}, 2000);
            }});
        }}

        // 모달 닫기
        function closeShareModal(event) {{
            if (event && event.target !== event.currentTarget) return;

            const modal = document.getElementById('share-modal-overlay');
            modal.classList.remove('active');

            // 리셋
            document.getElementById('short-url-loading').style.display = 'block';
            document.getElementById('short-url-loading').textContent = '링크 생성 중...';
            document.getElementById('short-url-content').style.display = 'none';
            document.getElementById('qr-loading').style.display = 'block';
            document.getElementById('qr-loading').textContent = 'QR 코드 생성 중...';
            document.getElementById('qr-content').style.display = 'none';
        }}

        // 링크 복사 기능
        function copyLink() {{
            const url = window.location.href;
            const btn = document.getElementById('copy-btn');
            const btnText = document.getElementById('copy-btn-text');

            // Clipboard API 사용
            navigator.clipboard.writeText(url).then(() => {{
                // 성공 피드백
                btn.classList.add('copied');
                btnText.textContent = '복사 완료!';

                setTimeout(() => {{
                    btn.classList.remove('copied');
                    btnText.textContent = '링크 복사';
                }}, 2000);
            }}).catch(() => {{
                // 실패 시 fallback
                const textArea = document.createElement('textarea');
                textArea.value = url;
                textArea.style.position = 'fixed';
                textArea.style.opacity = '0';
                document.body.appendChild(textArea);
                textArea.select();

                try {{
                    document.execCommand('copy');
                    btn.classList.add('copied');
                    btnText.textContent = '복사 완료!';

                    setTimeout(() => {{
                        btn.classList.remove('copied');
                        btnText.textContent = '링크 복사';
                    }}, 2000);
                }} catch (err) {{
                    alert('링크 복사에 실패했습니다.');
                }}

                document.body.removeChild(textArea);
            }});
        }}

        renderPlatforms();
    </script>
</body>
</html>
    '''
    return render_template_string(html)

# ===== 링크 사이트 API 엔드포인트 =====

@app.route('/api/top100', methods=['GET'])
def api_top100():
    """TOP 100 앨범 조회 (기간별)"""
    try:
        period = request.args.get('period', 'weekly')  # daily, weekly, annual
        limit = int(request.args.get('limit', 100))

        conn = get_db_connection()
        cursor = conn.cursor()

        # 기간별 날짜 계산
        from datetime import datetime, timedelta
        now = datetime.now()

        if period == 'daily':
            start_date = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        elif period == 'weekly':
            start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        elif period == 'annual':
            start_date = (now - timedelta(days=365)).strftime('%Y-%m-%d')
        else:
            start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')

        # TOP 100 앨범 조회 (발매일이 기간 내이고 링크가 많은 순)
        cursor.execute('''
            SELECT
                apl.artist_ko,
                apl.artist_en,
                apl.album_ko,
                apl.album_en,
                apl.album_cover_url,
                apl.release_date,
                COUNT(CASE WHEN apl.found = 1 THEN 1 END) as found_count
            FROM album_platform_links apl
            WHERE apl.release_date IS NOT NULL
              AND apl.release_date != ''
              AND date(apl.release_date) >= date(?)
              AND (apl.release_date IS NULL OR apl.release_date = '' OR datetime(apl.release_date) <= datetime('now', 'localtime'))
            GROUP BY apl.artist_ko, apl.album_ko
            HAVING found_count > 0
            ORDER BY found_count DESC, apl.release_date DESC
            LIMIT ?
        ''', (start_date, limit))

        albums = []
        for idx, row in enumerate(cursor.fetchall(), 1):
            albums.append({
                'rank': idx,
                'artist_ko': row['artist_ko'],
                'artist_en': row['artist_en'] or '',
                'album_ko': row['album_ko'],
                'album_en': row['album_en'] or '',
                'album_cover_url': row['album_cover_url'] or '',
                'release_date': row['release_date'] or '',
                'found_count': row['found_count']
            })

        conn.close()

        return jsonify({
            'success': True,
            'period': period,
            'albums': albums,
            'total': len(albums)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/latest', methods=['GET'])
def api_latest():
    """최신 발매 앨범 조회 (페이지네이션)"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # 최신 발매 앨범 조회
        cursor.execute('''
            SELECT DISTINCT
                apl.artist_ko,
                apl.artist_en,
                apl.album_ko,
                apl.album_en,
                apl.album_cover_url,
                apl.release_date,
                COUNT(CASE WHEN apl.found = 1 THEN 1 END) as found_count
            FROM album_platform_links apl
            WHERE apl.release_date IS NOT NULL
              AND apl.release_date != ''
              AND (apl.release_date IS NULL OR apl.release_date = '' OR datetime(apl.release_date) <= datetime('now', 'localtime'))
            GROUP BY apl.artist_ko, apl.album_ko
            HAVING found_count > 0
            ORDER BY apl.release_date DESC, apl.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit + 1, offset))  # +1 to check if there are more

        rows = cursor.fetchall()
        has_more = len(rows) > limit
        albums = []

        for row in rows[:limit]:
            albums.append({
                'artist_ko': row['artist_ko'],
                'artist_en': row['artist_en'] or '',
                'album_ko': row['album_ko'],
                'album_en': row['album_en'] or '',
                'album_cover_url': row['album_cover_url'] or '',
                'release_date': row['release_date'] or '',
                'found_count': row['found_count']
            })

        conn.close()

        return jsonify({
            'success': True,
            'albums': albums,
            'page': page,
            'limit': limit,
            'has_more': has_more
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search', methods=['GET'])
def api_search():
    """앨범 검색"""
    try:
        query = request.args.get('q', '').strip()

        if not query:
            return jsonify({
                'success': True,
                'albums': []
            })

        conn = get_db_connection()
        cursor = conn.cursor()

        # 앨범 검색 (아티스트명 또는 앨범명에 검색어 포함)
        cursor.execute('''
            SELECT DISTINCT
                apl.artist_ko,
                apl.artist_en,
                apl.album_ko,
                apl.album_en,
                apl.album_cover_url,
                apl.release_date,
                COUNT(CASE WHEN apl.found = 1 THEN 1 END) as found_count
            FROM album_platform_links apl
            WHERE (apl.artist_ko LIKE ? OR apl.album_ko LIKE ? OR apl.artist_en LIKE ? OR apl.album_en LIKE ?)
              AND (apl.release_date IS NULL OR apl.release_date = '' OR datetime(apl.release_date) <= datetime('now', 'localtime'))
            GROUP BY apl.artist_ko, apl.album_ko
            HAVING found_count > 0
            ORDER BY found_count DESC, apl.release_date DESC
            LIMIT 100
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

        albums = []
        for row in cursor.fetchall():
            albums.append({
                'artist_ko': row['artist_ko'],
                'artist_en': row['artist_en'] or '',
                'album_ko': row['album_ko'],
                'album_en': row['album_en'] or '',
                'album_cover_url': row['album_cover_url'] or '',
                'release_date': row['release_date'] or '',
                'found_count': row['found_count']
            })

        conn.close()

        return jsonify({
            'success': True,
            'query': query,
            'albums': albums,
            'total': len(albums)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/album/<artist_ko>/<album_ko>', methods=['GET'])
def api_album_detail(artist_ko, album_ko):
    """앨범 상세 정보 및 플랫폼 링크 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 앨범 기본 정보 (albums 테이블에서 - album_cover_url 제외)
        cursor.execute('''
            SELECT artist_ko, artist_en, album_ko, album_en,
                   release_date, album_code
            FROM albums
            WHERE artist_ko = ? AND album_ko = ?
        ''', (artist_ko, album_ko))

        album_row = cursor.fetchone()

        # album_cover_url은 album_platform_links에서 가져오기
        cursor.execute('''
            SELECT DISTINCT album_cover_url
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
              AND album_cover_url IS NOT NULL
              AND album_cover_url != ''
            LIMIT 1
        ''', (artist_ko, album_ko))

        cover_row = cursor.fetchone()
        album_cover_url = cover_row['album_cover_url'] if cover_row else ''

        # albums 테이블에 없으면 album_platform_links에서 모든 정보 가져오기
        if not album_row:
            cursor.execute('''
                SELECT DISTINCT artist_ko, artist_en, album_ko, album_en,
                       album_cover_url, release_date
                FROM album_platform_links
                WHERE artist_ko = ? AND album_ko = ?
                LIMIT 1
            ''', (artist_ko, album_ko))
            album_row = cursor.fetchone()

            if not album_row:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Album not found'
                }), 404

            album_cover_url = album_row['album_cover_url'] or ''

        # 플랫폼 링크 조회
        cursor.execute('''
            SELECT platform_code, platform_name, platform_type,
                   platform_url, found
            FROM album_platform_links
            WHERE artist_ko = ? AND album_ko = ?
            ORDER BY
                CASE platform_type WHEN 'domestic' THEN 0 ELSE 1 END,
                platform_code
        ''', (artist_ko, album_ko))

        platforms = []
        for row in cursor.fetchall():
            platforms.append({
                'platform_code': row['platform_code'],
                'platform_name': row['platform_name'],
                'platform_type': row['platform_type'],
                'platform_url': row['platform_url'] or '',
                'found': bool(row['found'])
            })

        conn.close()

        album_data = {
            'artist_ko': album_row['artist_ko'],
            'artist_en': album_row['artist_en'] or '',
            'album_ko': album_row['album_ko'],
            'album_en': album_row['album_en'] or '',
            'album_cover_url': album_cover_url,
            'release_date': album_row['release_date'] or '',
            'album_code': album_row['album_code'] if 'album_code' in album_row.keys() else '',
            'platforms': platforms
        }

        return jsonify({
            'success': True,
            'album': album_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 공유 기능 API ====================

def generate_short_code(length=6):
    """짧은 URL 코드 생성"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.route('/api/create-short-link', methods=['POST'])
def create_short_link():
    """Short URL 생성"""
    try:
        data = request.get_json()
        artist_ko = data.get('artist_ko')
        album_ko = data.get('album_ko')

        if not artist_ko or not album_ko:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 기존 short link 확인
        cursor.execute('''
            SELECT short_code FROM short_links
            WHERE artist_ko = ? AND album_ko = ?
        ''', (artist_ko, album_ko))

        result = cursor.fetchone()

        if result:
            # 이미 존재하면 기존 코드 반환
            short_code = result['short_code']
        else:
            # 새 코드 생성
            while True:
                short_code = generate_short_code()
                cursor.execute('SELECT 1 FROM short_links WHERE short_code = ?', (short_code,))
                if not cursor.fetchone():
                    break

            # DB에 저장
            cursor.execute('''
                INSERT INTO short_links (short_code, artist_ko, album_ko)
                VALUES (?, ?, ?)
            ''', (short_code, artist_ko, album_ko))
            conn.commit()

        conn.close()

        # 짧은 URL 생성
        short_url = f"{request.host_url}s/{short_code}"

        return jsonify({
            'success': True,
            'short_code': short_code,
            'short_url': short_url
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/s/<short_code>')
def short_link_redirect(short_code):
    """Short URL 리다이렉트"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Short code로 앨범 정보 조회
        cursor.execute('''
            SELECT artist_ko, album_ko FROM short_links
            WHERE short_code = ?
        ''', (short_code,))

        result = cursor.fetchone()

        if not result:
            conn.close()
            return "링크를 찾을 수 없습니다", 404

        artist_ko = result['artist_ko']
        album_ko = result['album_ko']

        # 클릭 수 증가
        cursor.execute('''
            UPDATE short_links
            SET click_count = click_count + 1,
                last_clicked_at = CURRENT_TIMESTAMP
            WHERE short_code = ?
        ''', (short_code,))
        conn.commit()
        conn.close()

        # 원본 URL로 리다이렉트
        album_id = f"{artist_ko}|||{album_ko}"
        return redirect(f"/album/{album_id}")

    except Exception as e:
        return f"오류: {str(e)}", 500

@app.route('/api/generate-qr', methods=['POST'])
def generate_qr_code():
    """QR 코드 생성"""
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # 이미지 생성
        img = qr.make_image(fill_color="black", back_color="white")

        # BytesIO로 변환
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Base64 인코딩
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'success': True,
            'qr_code': f"data:image/png;base64,{img_base64}"
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 메인 =====

if __name__ == '__main__':
    print("=" * 60)
    print("🔐 관리자 페이지 서버 시작")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Admin Username: {ADMIN_USERNAME}")
    print(f"Admin Password: {'*' * len(ADMIN_PASSWORD)}")
    print("=" * 60)
    print("📍 관리자 로그인: http://localhost:5003/admin/login")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5002, debug=True)
