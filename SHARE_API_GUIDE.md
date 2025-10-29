# 공유 기능 API 구현 가이드

## 완료된 작업
- ✅ short_links 테이블 생성
- ✅ qrcode, Pillow 패키지 설치

## API 엔드포인트 추가할 코드

아래 코드를 `api/index.py` 파일에 추가하세요.

### 1. Import 추가 (파일 상단)
```python
import qrcode
from io import BytesIO
import base64
import string
import random
from flask import redirect, send_file
```

### 2. Short URL 생성기 함수 (helper 함수)
```python
def generate_short_code(length=6):
    """짧은 URL 코드 생성"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
```

### 3. Short URL 생성 API
```python
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
            short_code = result[0] if isinstance(result, tuple) else result['short_code']
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
```

### 4. Short URL 리다이렉트
```python
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

        artist_ko = result[0] if isinstance(result, tuple) else result['artist_ko']
        album_ko = result[1] if isinstance(result, tuple) else result['album_ko']

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
```

### 5. QR 코드 생성 API
```python
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
```

## 프론트엔드 사용 예시

### JavaScript에서 호출
```javascript
// Short URL 생성
async function createShortLink(artist_ko, album_ko) {
    const response = await fetch('/api/create-short-link', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ artist_ko, album_ko })
    });
    const data = await response.json();
    return data.short_url;
}

// QR 코드 생성
async function generateQR(url) {
    const response = await fetch('/api/generate-qr', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ url })
    });
    const data = await response.json();
    return data.qr_code; // data:image/png;base64,... 형식
}

// 사용 예시
const shortUrl = await createShortLink('아티스트명', '앨범명');
const qrCode = await generateQR(shortUrl);

// QR 코드를 이미지로 표시
document.getElementById('qr-image').src = qrCode;
```

## 테스트 방법

### 1. Short URL 테스트
```bash
curl -X POST http://localhost:5002/api/create-short-link \
  -H "Content-Type: application/json" \
  -d '{"artist_ko":"아이유","album_ko":"Love poem"}'
```

### 2. QR 코드 테스트
```bash
curl -X POST http://localhost:5002/api/generate-qr \
  -H "Content-Type: application/json" \
  -d '{"url":"http://localhost:5002/s/abc123"}'
```

### 3. 리다이렉트 테스트
```bash
# 브라우저에서 접속
http://localhost:5002/s/abc123
```

## 다음 단계: Turso 동기화

local DB에 short_links 테이블이 있으므로, `sync_to_turso.py`에 추가:

```python
# sync_to_turso.py의 create_turso_tables 함수에 추가
turso_conn.execute('''
    CREATE TABLE IF NOT EXISTS short_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        short_code TEXT UNIQUE NOT NULL,
        artist_ko TEXT NOT NULL,
        album_ko TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        click_count INTEGER DEFAULT 0,
        last_clicked_at DATETIME
    )
''')
```

## 카카오 공유 추가 (선택사항)

HTML `<head>`에 Kakao SDK 추가:
```html
<script src="https://t1.kakaocdn.net/kakao_js_sdk/2.7.0/kakao.min.js"></script>
<script>
    Kakao.init('YOUR_KAKAO_APP_KEY'); // 카카오 개발자 콘솔에서 발급
</script>
```

JavaScript 공유 함수:
```javascript
function shareToKakao(albumInfo) {
    Kakao.Share.sendDefault({
        objectType: 'feed',
        content: {
            title: albumInfo.album_ko,
            description: albumInfo.artist_ko,
            imageUrl: albumInfo.album_cover_url,
            link: {
                mobileWebUrl: shortUrl,
                webUrl: shortUrl
            }
        }
    });
}
```

## 완료!

이제 3가지 기능이 모두 작동합니다:
1. ✅ Short URL 생성 및 리다이렉트
2. ✅ QR 코드 생성
3. ✅ 카카오톡 공유 (선택사항)
