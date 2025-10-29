# 🎵 Release Album Link - 프로젝트 현황

> **최종 업데이트**: 2025-10-28
> **작성 목적**: 다른 컴퓨터에서도 정확한 현재 상태를 파악하고 작업을 이어갈 수 있도록

---

## 📊 현재 진행 상황

### 전체 통계 (2025-10-28 기준)

```
총 앨범: 5,103개 (CDMA00001 ~ CDMA05110)
마지막 수집: 2025-10-28 04:56:11
```

#### 국내 플랫폼 (KR) - 5개 플랫폼
```
✅ 완전 성공 (5/5):  1,276개 (25.0%)
🟨 부분 성공 (1-4/5):  417개 ( 8.2%)
❌ 미수집 (0/5):     3,410개 (66.8%) ← 주요 문제
```

**플랫폼별 성공률**:
| 플랫폼 | 성공 | 전체 | 성공률 |
|--------|------|------|--------|
| 멜론 | 1,465 | 5,203 | 28.2% |
| 지니뮤직 | 1,464 | 5,202 | 28.1% |
| FLO | 1,520 | 5,202 | 29.2% |
| 벅스 | 1,524 | 5,202 | 29.3% |
| VIBE | 1,546 | 5,202 | 29.7% |

#### 글로벌 플랫폼 (Global) - 13개 플랫폼
```
✅ 완전 성공 (12+/12): 1,739개 (34.1%)
🟨 부분 성공 (1-11/12):   80개 ( 1.6%)
❌ 미수집 (0/12):      3,284개 (64.3%)
```

**플랫폼별 성공률**:
| 플랫폼 | 성공 | 전체 | 성공률 |
|--------|------|------|--------|
| Spotify | 1,832 | 5,050 | 36.3% |
| Apple Music | 1,832 | 5,048 | 36.3% |
| YouTube Music | 1,837 | 5,054 | 36.3% |
| Amazon Music | 1,831 | 5,048 | 36.3% |
| Deezer | 1,836 | 5,053 | 36.3% |
| Anghami | 1,836 | 5,053 | 36.3% |
| Tidal | 1,827 | 5,044 | 36.2% |
| Pandora | 1,823 | 5,040 | 36.2% |
| LINE MUSIC | 1,819 | 5,036 | 36.1% |
| AWA | 1,816 | 5,036 | 36.1% |
| KKBox | 1,806 | 5,026 | 35.9% |
| Moov | 1,705 | 4,925 | 34.6% |
| TCT (QQ Music) | 228 | 3,450 | 6.6% |

**특이사항**:
- LMT (139/139, 100%): 특정 앨범만 해당
- QQ Music (1,332/1,332, 100%): 특정 앨범만 해당

---

## 🏗️ 시스템 아키텍처

### 데이터베이스 구조

**로컬 DB**: `/Users/choejibin/release-album-link/album_links.db`

#### 주요 테이블

**1. albums** (5,103개)
```sql
CREATE TABLE albums (
    id INTEGER PRIMARY KEY,
    album_code TEXT UNIQUE,  -- CDMA 코드
    artist_ko TEXT,
    artist_en TEXT,
    album_ko TEXT,
    album_en TEXT,
    release_date TEXT,
    album_type TEXT,
    label TEXT,
    distributor TEXT,
    genre TEXT,
    uci TEXT,
    created_at TEXT,
    updated_at TEXT
)
```

**2. album_platform_links** (91,345개)
```sql
CREATE TABLE album_platform_links (
    id INTEGER PRIMARY KEY,
    artist_ko TEXT,
    artist_en TEXT,
    album_ko TEXT,
    album_en TEXT,
    platform_type TEXT,  -- 'kr' 또는 'global'
    platform_id TEXT,
    platform_name TEXT,
    platform_url TEXT,
    platform_code TEXT,
    album_id TEXT,
    upc TEXT,
    found INTEGER DEFAULT 0,  -- 0: 미발견, 1: 발견
    status TEXT,
    created_at DATETIME,
    album_cover_url TEXT,
    release_date TEXT,
    UNIQUE(artist_ko, album_ko, platform_id, platform_type)
)
```

### 수집 방식

#### 국내 플랫폼 (KR)
- **방식**: 각 플랫폼 API 직접 호출
- **검색**: 아티스트명 + 앨범명
- **플랫폼**: 멜론, 지니뮤직, FLO, 벅스, VIBE

#### 글로벌 플랫폼 (Global)
- **방식**: Companion.global 웹사이트 크롤링 (Selenium)
- **검색**: CDMA 코드 (album_code)
- **중요**: CDMA 코드로 검색하므로 결과가 영문으로 나와도 정상
- **아키텍처**:
  ```
  collect_n8n_style.py (메인)
         ↓ HTTP POST
  companion_api.py (Flask :5001)
         ↓ WebDriver
  Selenium Grid (Docker :4444)
         ↓ HTTP
  companion.global
  ```

---

## 🔧 주요 스크립트

### 수집 스크립트

**1. collect_n8n_style.py** - 메인 수집 스크립트
```bash
# 사용법
export TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io'
export TURSO_AUTH_TOKEN='eyJhbGci...(생략)'
python3 collect_n8n_style.py [batch_number]
```

**기능**:
- albums 테이블에서 CDMA 코드로 앨범 조회
- 국내 5개 플랫폼 + 글로벌 13개 플랫폼 수집
- album_platform_links에 결과 저장
- Turso DB 사용 (원격)

**2. companion_api.py** - Selenium 기반 Flask API
```bash
# 실행
export SELENIUM_HUB="http://localhost:4444"
python3 companion_api.py &

# 상태 확인
curl http://localhost:5001/health
```

**엔드포인트**:
- `GET /health` - 헬스체크
- `POST /search` - 글로벌 플랫폼 링크 검색
  ```json
  {
    "artist": "아티스트명",
    "album": "앨범명",
    "upc": "CDMA00001"
  }
  ```

**3. auto_collect.sh** - 배치 자동화
```bash
# 사용법
./auto_collect.sh [시작_배치] [종료_배치]

# 예시: 배치 1~52 수집 (각 배치 100개 앨범)
./auto_collect.sh 1 52
```

### 분석 스크립트

**4. track_failures.py** - 국내 플랫폼 실패 분석
```bash
python3 track_failures.py

# 결과:
# - failures_kr_complete.txt (0/5 앨범 목록)
# - failures_kr_partial.txt (1-4/5 앨범 목록)
```

**5. track_global_failures.py** - 글로벌 플랫폼 실패 분석
```bash
python3 track_global_failures.py

# 결과:
# - failures_global_complete.txt (0/12 앨범 목록)
# - failures_global_partial.txt (1-11/12 앨범 목록)
```

**6. sync_to_turso.py** - 로컬 → Turso 동기화
```bash
export TURSO_DATABASE_URL='...'
export TURSO_AUTH_TOKEN='...'
python3 sync_to_turso.py
```

---

## 🚀 재수집 가이드

### 준비 사항

#### 1. 환경 변수 설정
```bash
export TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io'
export TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA'

# Companion.global 로그인 (FLUXUS 계정)
export COMPANION_USERNAME='candidmusic'
export COMPANION_PASSWORD='dkfvfk2-%!#'  # 백슬래시 없음!

export SELENIUM_HUB="http://localhost:4444"
export COMPANION_API_PORT=5001
```

#### 2. Docker & Selenium Grid 시작
```bash
# Docker 실행
open -a Docker
sleep 10

# Selenium Grid 시작 (ARM Mac)
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  seleniarm/standalone-chromium:latest

# Intel Mac인 경우
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  selenium/standalone-chrome:latest

# 상태 확인
curl http://localhost:4444/status
```

#### 3. Companion API 시작
```bash
cd /Users/choejibin/release-album-link
python3 companion_api.py &
sleep 3

# 상태 확인
curl http://localhost:5001/health
# 응답: {"status":"ok","service":"companion-api","selenium_hub":"http://localhost:4444"}
```

### 재수집 방법

#### 옵션 1: 특정 배치 수집
```bash
# 배치 번호로 수집 (1 배치 = 100개 앨범)
python3 collect_n8n_style.py 1   # CDMA00001 ~ CDMA00100
python3 collect_n8n_style.py 10  # CDMA00901 ~ CDMA01000
```

#### 옵션 2: 전체 자동 수집
```bash
# 전체 5,103개 앨범 수집
./auto_collect.sh 1 52

# 또는 특정 범위
./auto_collect.sh 10 20  # 배치 10~20만
```

#### 옵션 3: 실패 케이스만 재수집
```bash
# 1. 실패 목록 생성
python3 track_failures.py
python3 track_global_failures.py

# 2. 실패 목록 확인
cat failures_kr_complete.txt      # KR 0/5
cat failures_global_complete.txt  # Global 0/12

# 3. 수동 재수집 (스크립트 수정 필요)
# TODO: 실패 앨범만 재수집하는 스크립트 작성
```

---

## ⚠️ 중요 주의사항

### 1. Companion.global 로그인
```bash
# ❌ 잘못된 비밀번호 (백슬래시 들어감)
COMPANION_PASSWORD='dkfvfk2-\%\!#'

# ✅ 올바른 비밀번호 (백슬래시 없음)
COMPANION_PASSWORD='dkfvfk2-%!#'
```

과거에 이 문제로 많은 시간을 소비했습니다!

### 2. 글로벌 검색 방식
- CDMA 코드로 검색: `CDMA00001`
- 검색 결과가 영문명으로 나와도 정상
- 예: "욕심이겠지만" 검색 → "Greed" 결과 (정상)

### 3. 플랫폼 코드 불일치 문제
현재 DB에 플랫폼 코드가 혼재되어 있습니다:
```
API 반환:    spo, ama, dee (짧은 코드)
DB에 저장:   spotify, amazon, deezer (긴 코드)와 짧은 코드 둘 다
```

**해결**: `fix_platform_codes.sql` 실행으로 통일 필요
```bash
sqlite3 album_links.db < fix_platform_codes.sql
```

### 4. Turso DB 읽기 제한
현재 Turso 무료 플랜 제한으로 읽기가 차단될 수 있습니다:
```
Error: Operation was blocked: SQL read operations are forbidden
```

**해결**: 로컬 DB (`album_links.db`) 사용 또는 Turso 플랜 업그레이드

---

## 📁 파일 구조

```
/Users/choejibin/release-album-link/
├── album_links.db              # 로컬 SQLite DB (91,345 rows)
├── albums 테이블              # 5,103개 앨범 정보
├── album_platform_links 테이블 # 플랫폼 링크 정보
│
├── collect_n8n_style.py        # 메인 수집 스크립트
├── companion_api.py            # Flask API (Selenium)
├── auto_collect.sh             # 배치 자동화
├── track_failures.py           # 국내 실패 분석
├── track_global_failures.py    # 글로벌 실패 분석
├── sync_to_turso.py            # DB 동기화
│
├── api/
│   └── index.py                # Vercel API (웹 인터페이스)
│
├── templates/                  # HTML 템플릿
│   ├── home.html
│   ├── search.html
│   └── admin/
│
├── archive/                    # 과거 문서 보관
│   └── old-docs-2025-10-28/
│       ├── COLLECTION_PROGRESS.md (구버전)
│       ├── GLOBAL_COLLECTION_FAILURE_ANALYSIS.md (구버전)
│       └── GLOBAL_COLLECTION_GUIDE.md (구버전)
│
├── PROJECT_STATUS.md           # 🆕 이 파일 (최신 상태)
├── RECOLLECTION_GUIDE.md       # 🆕 재수집 가이드 (다음 작성)
├── GLOBAL_LINK_COLLECTION_GUIDE.md  # 글로벌 수집 상세
├── SETUP_GUIDE.md              # 초기 설정
└── SHARE_API_GUIDE.md          # API 사용법
```

---

## 🎯 다음 작업 우선순위

### 긴급 (High Priority)

1. **국내 플랫폼 재수집** (3,410개 앨범, 66.8% 미수집)
   - 예상 시간: 5-8시간
   - 성공률 향상: 25% → 70%+ 목표

2. **플랫폼 코드 통일** (글로벌 수집률 향상)
   ```bash
   sqlite3 album_links.db < fix_platform_codes.sql
   ```
   - 글로벌 성공률 향상: 34% → 60%+ 예상

### 일반 (Medium Priority)

3. **글로벌 플랫폼 재수집** (3,284개 앨범)
   - 코드 통일 후 진행
   - 예상 시간: 3-5시간

4. **실패 앨범 수동 분석**
   - Companion.global에 실제로 없는 앨범 확인
   - DB 업데이트 필요 여부 판단

### 선택 (Low Priority)

5. **관리자 페이지 개선**
   - 재수집 버튼 추가
   - 실시간 진행 상황 모니터링

6. **Turso 플랜 업그레이드 또는 로컬 DB 전환**

---

## 🔗 참고 자료

- **Companion.global**: http://companion.global
- **Turso Dashboard**: https://turso.tech/app
- **Selenium Grid UI**: http://localhost:4444/ui
- **로컬 API**: http://localhost:5001

---

## 📝 변경 이력

### 2025-10-28
- ✅ 전체 프로젝트 현황 파악
- ✅ 구버전 문서 `archive/old-docs-2025-10-28/`로 이동
- ✅ 최신 DB 통계 집계 (5,103개 앨범)
- ✅ PROJECT_STATUS.md 작성 (현재 문서)

### 2025-10-19
- 마지막 수집 실행 (CDMA05110까지)
- 국내: 1,276개 완료 (25%)
- 글로벌: 1,739개 완료 (34%)

---

**작성자**: Claude Code
**목적**: 프로젝트 중단 후 재시작 시 빠른 상황 파악
**다음 문서**: RECOLLECTION_GUIDE.md (재수집 상세 가이드)
