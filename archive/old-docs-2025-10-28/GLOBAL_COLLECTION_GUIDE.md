# 🌐 글로벌 플랫폼 링크 수집 가이드

> **작성일**: 2025-10-21
> **목적**: 클로드 재시작 후에도 글로벌 수집을 실행할 수 있도록 전체 프로세스 문서화

---

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [환경 설정](#환경-설정)
3. [실행 방법](#실행-방법)
4. [중요 메모](#중요-메모)
5. [트러블슈팅](#트러블슈팅)

---

## 시스템 개요

### 아키텍처
```
┌─────────────────┐
│   collect_*.py  │ ← 메인 수집 스크립트
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│ companion_api.py│ ← Flask API (Port 5001)
│   (Selenium)    │
└────────┬────────┘
         │ WebDriver
         ▼
┌─────────────────┐
│ Selenium Grid   │ ← Docker (Port 4444)
│  (Headless)     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│companion.global │ ← 글로벌 링크 소스
└─────────────────┘
```

### 수집 방식 차이

| 플랫폼 타입 | 검색 방식 | 매칭 방식 |
|------------|----------|----------|
| **국내 (KR)** | 아티스트명/앨범명 | 텍스트 매칭 |
| **글로벌 (Global)** | **CDMA 코드** | CDMA 코드 우선 |

**⚠️ 중요**: 글로벌은 CDMA 코드로 검색하며, 검색 결과가 영문명으로 나와서 다른 앨범처럼 보일 수 있으나 정상입니다.

---

## 환경 설정

### 1. 필수 환경 변수 (.env)

```bash
# Turso Database
TURSO_DATABASE_URL=libsql://album-links-cdmmusic.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA

# Companion.global 로그인 (FLUXUS)
COMPANION_USERNAME=candidmusic
COMPANION_PASSWORD=dkfvfk2-%!#

# Selenium Grid
SELENIUM_HUB=http://localhost:4444

# Companion API
COMPANION_API_PORT=5001
```

### 2. 필수 서비스 시작

```bash
# 1. Docker 실행
open -a Docker

# 2. Selenium Grid 컨테이너 시작 (ARM Mac용)
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  seleniarm/standalone-chromium:latest

# 또는 Intel Mac용
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  selenium/standalone-chrome:latest

# 3. Companion API 시작
cd /Users/choejibin/release-album-link
export SELENIUM_HUB="http://localhost:4444"
python3 companion_api.py &
```

### 3. 서비스 상태 확인

```bash
# Selenium Grid 상태
curl http://localhost:4444/status

# Companion API 상태
curl http://localhost:5001/health

# 결과 예시:
# {"status":"ok","service":"companion-api","selenium_hub":"http://localhost:4444"}
```

---

## 실행 방법

### 옵션 1: 단일 앨범 테스트

```bash
cd /Users/choejibin/release-album-link

# 환경 변수 로드
source .env

# 특정 앨범 수집 (배치 번호로)
export SELENIUM_HUB="http://localhost:4444"
python3 collect_n8n_style.py 1
```

### 옵션 2: 전체 배치 수집

```bash
cd /Users/choejibin/release-album-link

# 모든 앨범 수집 (약 5,100개)
./auto_collect.sh 1 52

# 또는 특정 범위만
./auto_collect.sh 10 20  # Batch 10~20만 수집
```

### 옵션 3: 실패 케이스 재수집

```bash
# 1. 실패 케이스 분석
source .env
python3 track_failures.py

# 결과:
# - failures_complete.txt (KR 0/5)
# - failures_partial.txt (KR 1-4/5)

# 2. 글로벌 링크 실패 분석
python3 track_global_failures.py

# 결과:
# - failures_global_complete.txt (글로벌 0/12)
# - failures_global_partial.txt (글로벌 1-11/12)
```

---

## 중요 메모

### 🔑 핵심 사항

1. **글로벌 검색 방식**
   - ✅ **CDMA 코드로 검색** (예: CDMA05088)
   - ❌ 아티스트명/앨범명으로 검색하지 않음
   - 검색 결과가 영문명으로 나와도 정상 (예: 한글 "욕심이겠지만" → 영문 "Greed")

2. **Companion.global 로그인 이슈**
   - **비밀번호**: `dkfvfk2-%!#` (백슬래시 없음!)
   - 이전에 로그인 문제로 많은 시간 소요했던 부분
   - Docker 이미지에서 복구한 정상 코드 유지

3. **플랫폼 링크 추출**
   - `onclick` 속성에서 정규식으로 파싱
   - 예: `onclick="click_platform('http://music.apple.com/...', 'itm', ...)"`
   - `href` 속성은 `javascript:;`이므로 사용 불가

### 📊 현재 통계 (2025-10-21 기준)

#### 국내 플랫폼 (KR)
```
총 앨범: 5,200개
완전 성공 (5/5): 74.8%
부분 실패 (1-4/5): 18.5%
완전 실패 (0/5): 6.2% (324개)
```

#### 글로벌 플랫폼 (Global)
```
총 앨범: 5,200개
완전 성공 (12/12): 3.1% (161개)
글로벌 링크 없음: 96.9% (5,042개)
```

**해석**: 대부분의 앨범이 companion.global에 등록되지 않음. 이는 정상입니다.

---

## 트러블슈팅

### 문제 1: Companion API 응답 없음

**증상**:
```bash
curl: (7) Failed to connect to localhost port 5001
```

**해결**:
```bash
# API 재시작
pkill -f "companion_api"
sleep 2
export SELENIUM_HUB="http://localhost:4444"
python3 companion_api.py &

# 로그 확인
tail -f /tmp/companion_api.log
```

### 문제 2: Selenium Grid 연결 실패

**증상**:
```
selenium.common.exceptions.WebDriverException: Message:
Failed to connect to http://localhost:4444
```

**해결**:
```bash
# 컨테이너 재시작
docker stop selenium-standalone
docker rm selenium-standalone

docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  seleniarm/standalone-chromium:latest

# 상태 확인
curl http://localhost:4444/status
```

### 문제 3: 로그인 실패 (error=true)

**증상**:
```
[Companion API] After login, URL: http://companion.global/login?error=true
```

**해결**:
```bash
# companion_api.py 확인
grep "COMPANION_PASSWORD" companion_api.py

# 결과가 다음과 같아야 함:
# COMPANION_PASSWORD = os.environ.get('COMPANION_PASSWORD', 'dkfvfk2-%!#')
# ⚠️ 백슬래시 없음!
```

### 문제 4: 플랫폼 링크 0개 추출

**증상**:
```json
{
  "success": true,
  "data": {
    "platform_count": 0,
    "platforms": []
  }
}
```

**원인**: 해당 앨범이 companion.global에 없음 (96.9%의 앨범이 해당)

**확인**:
```bash
# 글로벌 링크 통계 확인
source .env
python3 track_global_failures.py
```

### 문제 5: "element not interactable" 오류

**증상**:
```
selenium.common.exceptions.ElementNotInteractableException
```

**원인**: 빈 아티스트명과 매칭되어 잘못된 행 선택

**해결**: 이미 수정됨 (companion_api.py:202, 256)
```python
# 빈 문자열은 스킵
if not normalized_artist or not normalized_row_artist:
    continue
```

---

## 파일 구조

### 주요 스크립트

| 파일 | 용도 | 포트/의존성 |
|------|------|-----------|
| `companion_api.py` | Flask API, Selenium 제어 | :5001, Selenium Grid |
| `collect_n8n_style.py` | 메인 수집 스크립트 | Companion API 호출 |
| `track_failures.py` | 국내 실패 케이스 분석 | Turso DB |
| `track_global_failures.py` | 글로벌 실패 케이스 분석 | Turso DB |
| `auto_collect.sh` | 배치 자동화 스크립트 | collect_n8n_style.py |

### 주요 디렉토리

```
/Users/choejibin/release-album-link/
├── companion_api.py          # Flask API (Selenium)
├── collect_n8n_style.py      # 수집 메인 스크립트
├── track_failures.py         # 국내 실패 분석
├── track_global_failures.py  # 글로벌 실패 분석
├── auto_collect.sh           # 배치 자동화
├── .env                      # 환경 변수
├── failures_complete.txt     # KR 0/5 앨범 목록
├── failures_partial.txt      # KR 1-4/5 앨범 목록
├── failures_global_complete.txt  # Global 0/12 앨범 목록
└── failures_global_partial.txt   # Global 1-11/12 앨범 목록
```

---

## API 엔드포인트

### POST /search

**Request**:
```bash
curl -X POST http://localhost:5001/search \
  -H 'Content-Type: application/json' \
  -d '{
    "artist": "이요운",
    "album": "욕심이겠지만",
    "upc": "CDMA05088"
  }'
```

**Response (성공)**:
```json
{
  "success": true,
  "data": {
    "album_cover_url": "https://...",
    "platform_count": 3,
    "platforms": [
      {
        "platform": "Spotify",
        "code": "spo",
        "url": "http://open.spotify.com/album/..."
      },
      {
        "platform": "Apple Music",
        "code": "itm",
        "url": "http://music.apple.com/us/album/..."
      },
      {
        "platform": "YouTube Music",
        "code": "yat",
        "url": "http://www.youtube.com/watch?v=..."
      }
    ]
  }
}
```

**Response (실패 - 앨범 없음)**:
```json
{
  "success": false,
  "error": "Album \"욕심이겠지만\" by \"이요운\" not found in search results",
  "data": null
}
```

### GET /health

**Request**:
```bash
curl http://localhost:5001/health
```

**Response**:
```json
{
  "status": "ok",
  "service": "companion-api",
  "selenium_hub": "http://localhost:4444"
}
```

---

## 검색 전략 (3단계)

companion_api.py의 검색 로직:

1. **1단계**: 앨범명으로 검색 → 아티스트명 매칭
   ```python
   # 검색어: "욕심이겠지만"
   # 결과에서 아티스트 "이요운" 찾기
   ```

2. **2단계**: 실패 시, 아티스트명으로 검색 → 앨범명 매칭
   ```python
   # 검색어: "이요운"
   # 결과에서 앨범 "욕심이겠지만" 찾기
   ```

3. **텍스트 정규화**
   ```python
   def normalize_text(text):
       # 공백, 특수문자 제거, 소문자 변환
       return re.sub(r'[\s\-_,.()\[\]{}]+', '', text.lower())
   ```

---

## 다음 작업

### 즉시 실행 가능한 명령어

```bash
# 전체 환경 시작
cd /Users/choejibin/release-album-link
open -a Docker
sleep 10

docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest
sleep 5

export SELENIUM_HUB="http://localhost:4444"
python3 companion_api.py &
sleep 3

# 수집 시작 (배치 1)
python3 collect_n8n_style.py 1
```

### 전체 배치 수집

```bash
# 모든 앨범 수집 (약 5,200개, 2-3시간 소요)
./auto_collect.sh 1 52
```

---

## 연락처 & 참고자료

- **Companion.global**: http://companion.global
- **Turso Dashboard**: https://turso.tech/app
- **Selenium Grid**: http://localhost:4444/ui

**작성자 메모**: 이 문서는 클로드가 재시작되어도 전체 프로세스를 이해하고 실행할 수 있도록 작성되었습니다.
