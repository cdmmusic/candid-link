# 글로벌 링크 수집 가이드

## 개요
Companion.global에서 해외 플랫폼 링크를 수집하여 데이터베이스에 반영하는 절차입니다.

## 사전 준비

### 1. Companion API 서버 실행
```bash
# Selenium Hub가 실행 중인지 확인
docker ps | grep selenium

# 실행 중이 아니면 시작
docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest

# Companion API 실행
python3 companion_api.py
```

### 2. 메인 API 서버 실행
```bash
# Turso 환경변수 설정하고 실행
export TURSO_DATABASE_URL="libsql://album-links-cdmmusic.turso.io"
export TURSO_AUTH_TOKEN="your_token_here"
cd api && python3 index.py
```

## 수집 방법

### 방법 1: 단일 앨범 수집

#### Step 1: 데이터베이스에서 앨범 정보 확인
```bash
sqlite3 album_links.db "SELECT artist_ko, album_ko, album_code FROM albums WHERE album_code='CDMA00001'"
```

#### Step 2: Companion API로 검색
```bash
curl -X POST http://localhost:5001/search \
  -H "Content-Type: application/json" \
  -d '{
    "artist": "아이케이",
    "album": "Long Night",
    "upc": "CDMA00001"
  }' | python3 -m json.tool
```

#### Step 3: 수집된 링크를 데이터베이스에 저장
```python
import sqlite3
import requests

# 1. Companion API 호출
response = requests.post(
    'http://localhost:5001/search',
    json={
        'artist': '아이케이',
        'album': 'Long Night',
        'upc': 'CDMA00001'
    }
)
result = response.json()

# 2. 데이터베이스 저장
conn = sqlite3.connect('album_links.db')
cursor = conn.cursor()

if result['success']:
    platforms = result['data']['platforms']

    for platform in platforms:
        cursor.execute('''
            INSERT OR REPLACE INTO album_platform_links
            (artist_ko, album_ko, platform_code, platform_name, platform_url, platform_type, found)
            VALUES (?, ?, ?, ?, ?, 'global', 1)
        ''', (
            '아이케이',
            'Long Night',
            platform['code'],
            platform['platform'],
            platform['url']
        ))

    conn.commit()
    print(f"✓ {len(platforms)}개 플랫폼 저장 완료")

conn.close()
```

#### Step 4: Turso 동기화
```bash
export TURSO_DATABASE_URL="libsql://album-links-cdmmusic.turso.io"
export TURSO_AUTH_TOKEN="your_token_here"
python3 sync_to_turso.py
```

### 방법 2: 대량 수집 (collect_n8n_style.py 사용)

#### 사용법
```bash
# 1개 앨범 수집 테스트
python3 collect_n8n_style.py 1

# 10개 앨범 수집
python3 collect_n8n_style.py 10

# 모든 앨범 수집
python3 collect_n8n_style.py
```

#### 수집 대상
- `albums` 테이블에 있는 앨범 중
- 발매일이 지난 앨범 (`release_date <= now()`)
- 글로벌 링크가 없는 앨범 (`platform_type = 'global'` 레코드 없음)

## 중요 포인트

### Companion API의 핵심 로직

companion_api.py의 검색 프로세스:

```python
# 1. 로그인
driver.get('http://companion.global/login')
driver.find_element(By.ID, 'username').send_keys(username)
driver.find_element(By.ID, 'password').send_keys(password)
driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

# 2. Catalog 페이지 이동
driver.get('http://companion.global/catalog?init=Y&t=' + timestamp)

# 3. 검색어 입력
search_input = driver.find_element(By.ID, 'search_catalog')
driver.execute_script(f"arguments[0].value = '{cdma_code}';", search_input)

# 4. 검색 실행
driver.execute_script("catalog.search();")

# 5. ⭐ 로딩 화면이 사라질 때까지 대기 (핵심!)
wait = WebDriverWait(driver, 20)
wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.loading')))

# 6. 추가 대기 (데이터 렌더링)
time.sleep(2)

# 7. 결과에서 정확한 CDMA 코드 매칭
rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
for row in rows:
    upc_cdma = row.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    if cdma_code in upc_cdma:
        # 해당 row에서 Smart Link 찾기
        smart_link = row.find_element(By.CSS_SELECTOR, 'a[href*="/catalog/platform/"]')
        break

# 8. Smart Link 페이지에서 플랫폼 링크 수집
driver.get(smart_link_url)
platform_items = driver.find_elements(By.CSS_SELECTOR, '#platList li')
for item in platform_items:
    onclick = item.get_attribute('onclick')
    # onclick에서 URL 추출
```

### 주의사항

1. **로딩 대기 필수**
   - Companion.global은 AJAX로 데이터를 로드합니다
   - `div.loading`이 사라질 때까지 반드시 대기해야 합니다
   - 단순 `time.sleep()`은 불안정합니다

2. **CDMA 코드 정확히 매칭**
   - 검색 결과에 여러 앨범이 나올 수 있습니다
   - UPC/CDMA 컬럼에서 정확한 코드를 찾아야 합니다

3. **Smart Link 페이지 접근**
   - 검색 결과의 각 row에서 `/catalog/platform/xxx` 링크를 찾습니다
   - 이 페이지에 실제 플랫폼 링크들이 있습니다

4. **플랫폼 링크 파싱**
   - `#platList li` 요소의 `onclick` 속성에서 URL을 추출합니다
   - platform code와 platform name도 함께 저장합니다

## 수집 결과 확인

### 로컬 데이터베이스 확인
```bash
sqlite3 album_links.db "
  SELECT platform_code, platform_name, platform_url
  FROM album_platform_links
  WHERE artist_ko='아이케이'
    AND album_ko='Long Night'
    AND platform_type='global'
  ORDER BY platform_code
"
```

### 웹사이트 확인
```bash
# 앨범 페이지 접속
open "http://127.0.0.1:5002/album/아이케이|||Long%20Night"

# 또는 curl로 확인
curl -s "http://127.0.0.1:5002/album/%EC%95%84%EC%9D%B4%EC%BC%80%EC%9D%B4|||Long%20Night" | grep "글로벌 플랫폼"
```

## 트러블슈팅

### 문제: "Album not found in search results"
**원인**: 로딩 화면이 사라지기 전에 데이터를 읽으려고 시도
**해결**: `EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.loading'))` 사용

### 문제: 플랫폼 링크가 0개
**원인**: Smart Link 페이지를 찾지 못함
**해결**: 검색 결과에서 정확한 CDMA 코드 매칭 확인

### 문제: Turso 동기화 실패
**원인**: 환경변수 미설정
**해결**: `TURSO_DATABASE_URL`과 `TURSO_AUTH_TOKEN` 설정 확인

## 자동화 스크립트

### 전체 프로세스 자동화
```bash
#!/bin/bash
# collect_and_sync.sh

echo "🚀 글로벌 링크 수집 시작"

# 1. Selenium Hub 확인
if ! docker ps | grep -q selenium-standalone; then
    echo "⚠️  Selenium Hub 시작 중..."
    docker restart selenium-standalone || \
    docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest
    sleep 3
fi

# 2. Companion API 확인
if ! curl -s http://localhost:5001/health > /dev/null; then
    echo "⚠️  Companion API가 실행되지 않았습니다"
    echo "다음 명령어로 실행하세요: python3 companion_api.py"
    exit 1
fi

# 3. 수집 실행
echo "📥 앨범 링크 수집 중..."
python3 collect_n8n_style.py "$1"

# 4. Turso 동기화
echo "☁️  Turso 동기화 중..."
export TURSO_DATABASE_URL="libsql://album-links-cdmmusic.turso.io"
export TURSO_AUTH_TOKEN="your_token_here"
python3 sync_to_turso.py

echo "✅ 완료!"
```

### 사용법
```bash
# 실행 권한 부여
chmod +x collect_and_sync.sh

# 1개 수집
./collect_and_sync.sh 1

# 10개 수집
./collect_and_sync.sh 10

# 전체 수집
./collect_and_sync.sh
```

## 성공 사례

### CDMA00001 수집 결과
- **아티스트**: 아이케이
- **앨범**: Long Night
- **수집된 플랫폼**: 13개
  - Spotify, Deezer, Anghami, Pandora, KKBOX
  - AWA, YouTube Music, QQ Music, LINE MUSIC
  - LMT, MOOV, Tidal, Amazon Music

### 소요 시간
- 단일 앨범: 약 20-30초
- 로그인 + 검색 + 플랫폼 페이지 접근 포함

## 참고 파일

- `companion_api.py`: Selenium 기반 Companion.global 크롤러
- `collect_n8n_style.py`: 대량 수집 스크립트
- `sync_to_turso.py`: Turso 동기화 스크립트
- `album_links.db`: 로컬 SQLite 데이터베이스

---

**마지막 업데이트**: 2025-10-27
**작성자**: Claude Code
