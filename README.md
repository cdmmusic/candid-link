# 🎵 캔디드뮤직 링크

17개 음악 스트리밍 플랫폼의 앨범 링크를 한 곳에서 제공하는 웹 서비스입니다.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)

---

## ✨ 주요 기능

- **17개 플랫폼 지원**: Melon, Spotify, Apple Music, YouTube Music 등
- **통합 검색**: 아티스트/앨범명으로 빠른 검색
- **반응형 디자인**: 모바일/데스크톱 최적화
- **앨범 상세**: 모든 플랫폼 링크를 한 눈에
- **공유 기능**: 짧은 URL + QR 코드 생성
- **TOP 100**: 주간/일간/연간 인기 차트
- **최신 발매**: 최신 앨범 탐색

---

## 📊 지원 플랫폼 (17개)

### 🇰🇷 국내 (5개)
- **Melon** | **Genie** | **Bugs** | **FLO** | **VIBE**

### 🌍 글로벌 (12개)
- **Apple Music** | **Spotify** | **YouTube** | **Amazon Music**
- **Deezer** | **Tidal** | **KKBox** | **Anghami**
- **Pandora** | **LINE Music** | **AWA** | **Moov** | **QQ MUSIC**

---

## 🚀 빠른 시작 (처음 세팅)

### 필수 요구사항

#### 공통
- **Python 3.10 이상**
- **SQLite3** (Python 설치 시 포함)
- **Git**

#### 추가 (데이터 수집용)
- **Docker** (Selenium Grid 실행용)

### 1️⃣ 저장소 클론

```bash
git clone https://github.com/yourusername/release-album-link.git
cd release-album-link
```

### 2️⃣ Python 환경 설정

<details>
<summary><b>🍎 macOS</b></summary>

```bash
# Homebrew로 Python 설치 (선택사항)
brew install python@3.10

# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

**macOS 전용 주의사항:**
- M1/M2 Mac의 경우 Selenium Grid는 `seleniarm/standalone-chromium` 이미지 사용
- Docker Desktop for Mac 필요 (데이터 수집 시)
</details>

<details>
<summary><b>🪟 Windows</b></summary>

```powershell
# Python 설치 확인
python --version

# 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

**Windows 전용 주의사항:**
- PowerShell 또는 CMD 사용
- 경로 구분자: `\` 사용 (예: `venv\Scripts\activate`)
- Docker Desktop for Windows 필요 (데이터 수집 시)
- WSL2 백엔드 권장
</details>

### 3️⃣ 로컬 서버 실행

```bash
# Flask 웹 서버 시작
python3 api/index.py
```

브라우저에서 접속: **http://localhost:5002**

---

## 🗂️ 프로젝트 구조

```
release-album-link/
├── api/
│   └── index.py                    # Flask 웹 서버 (메인)
├── templates/                      # HTML 템플릿
│   ├── header.html                 # 공통 헤더
│   ├── home.html                   # 홈 페이지
│   ├── search.html                 # 검색 페이지
│   ├── top100.html                 # TOP 100 페이지
│   └── latest.html                 # 최신 발매 페이지
├── static/
│   ├── css/main.css                # 메인 스타일시트
│   └── js/
│       ├── main.js                 # 공통 JavaScript
│       └── carousel.js             # 캐러셀 기능
├── collect_global_resume.py        # 글로벌 + 국내 링크 수집 (추천)
├── companion_api.py                # Companion API (글로벌 수집용)
├── album_links.db                  # SQLite 데이터베이스
├── collection.log                  # 수집 로그
└── README.md                       # 이 파일
```

---

## 🔄 데이터 수집 (선택사항)

데이터 수집은 선택사항입니다. 기본 데이터베이스(`album_links.db`)가 이미 포함되어 있습니다.

### 수집 환경 설정

#### 1. Docker 설치

<details>
<summary><b>🍎 macOS</b></summary>

```bash
# Homebrew로 Docker 설치
brew install --cask docker

# Docker Desktop 실행
open -a Docker

# Selenium Grid 시작 (M1/M2 Mac)
docker run -d --name selenium-standalone \
  -p 4444:4444 --shm-size=2g \
  seleniarm/standalone-chromium:latest
```
</details>

<details>
<summary><b>🪟 Windows</b></summary>

1. Docker Desktop for Windows 다운로드: https://www.docker.com/products/docker-desktop
2. WSL2 백엔드 활성화
3. PowerShell에서 실행:

```powershell
# Selenium Grid 시작
docker run -d --name selenium-standalone `
  -p 4444:4444 --shm-size=2g `
  selenium/standalone-chrome:latest
```

**주의**: Windows는 `selenium/standalone-chrome` 사용 (Intel/AMD)
</details>

#### 2. Companion API 시작

<details>
<summary><b>🍎 macOS / Linux</b></summary>

```bash
# 환경 변수 설정
export COMPANION_API_PORT="5001"

# Companion API 백그라운드 실행
python3 companion_api.py &
```
</details>

<details>
<summary><b>🪟 Windows</b></summary>

```powershell
# 환경 변수 설정
$env:COMPANION_API_PORT="5001"

# Companion API 백그라운드 실행 (별도 터미널)
Start-Process python -ArgumentList "companion_api.py"
```
</details>

#### 3. 수집 시작

<details>
<summary><b>🍎 macOS / Linux</b></summary>

```bash
# 백그라운드 수집 시작
python3 collect_global_resume.py > collection.log 2>&1 &

# 로그 확인
tail -f collection.log
```
</details>

<details>
<summary><b>🪟 Windows</b></summary>

```powershell
# 백그라운드 수집 시작
Start-Process python -ArgumentList "collect_global_resume.py" `
  -RedirectStandardOutput collection.log `
  -RedirectStandardError collection.log

# 로그 확인
Get-Content collection.log -Wait
```
</details>

---

## 🏗️ 기술 스택

### 프론트엔드
- **HTML5 + CSS3** - 시맨틱 마크업
- **Vanilla JavaScript** - 프레임워크 없는 순수 JS
- **반응형 디자인** - Mobile-first
- **모던 UI/UX** - 그라디언트, 애니메이션

### 백엔드
- **Python 3.10+**
- **Flask 3.0** - 경량 웹 프레임워크
- **SQLite3** - 로컬 데이터베이스

### 데이터 수집
- **Selenium WebDriver** - 웹 자동화
- **Docker** - Selenium Grid 컨테이너
- **Companion.global API** - 글로벌 링크 수집
- **직접 크롤링** - 국내 플랫폼 (Melon, Genie 등)

---

## 📂 데이터베이스 구조

### 테이블: `album_platform_links`

```sql
CREATE TABLE album_platform_links (
    artist_ko TEXT,           -- 아티스트 한글명
    artist_en TEXT,           -- 아티스트 영문명
    album_ko TEXT,            -- 앨범 한글명
    album_en TEXT,            -- 앨범 영문명
    album_cover_url TEXT,     -- 앨범 커버 이미지 URL
    release_date TEXT,        -- 발매일
    platform_type TEXT,       -- 플랫폼 타입 (국내/글로벌)
    platform_id TEXT,         -- 플랫폼 ID
    platform_code TEXT,       -- 플랫폼 코드
    platform_name TEXT,       -- 플랫폼 이름
    platform_url TEXT,        -- 플랫폼 링크
    found INTEGER,            -- 링크 발견 여부 (0/1)
    created_at TEXT,          -- 생성 시간
    cdma_code TEXT            -- CDMA 코드
);
```

---

## 🌐 API 엔드포인트

### 웹 페이지
- `GET /` - 홈 페이지
- `GET /search` - 검색 페이지
- `GET /top100` - TOP 100 페이지
- `GET /latest` - 최신 발매 페이지
- `GET /album/:id` - 앨범 상세 페이지

### REST API
- `GET /api/albums-with-links` - 앨범 목록 (페이지네이션)
- `GET /api/search` - 앨범 검색
- `GET /api/top100` - TOP 100 조회
- `GET /api/latest` - 최신 발매 조회
- `POST /api/generate-short-url` - 짧은 URL 생성
- `POST /api/generate-qr` - QR 코드 생성

---

## 🔧 환경별 차이점 요약

| 항목 | macOS | Windows |
|------|-------|---------|
| **Python 명령어** | `python3` | `python` |
| **가상환경 활성화** | `source venv/bin/activate` | `venv\Scripts\activate` |
| **경로 구분자** | `/` | `\` |
| **Selenium Grid 이미지** | `seleniarm/standalone-chromium` (M1/M2)<br>`selenium/standalone-chrome` (Intel) | `selenium/standalone-chrome` |
| **백그라운드 실행** | `command &` | `Start-Process` |
| **환경 변수 설정** | `export VAR="value"` | `$env:VAR="value"` |
| **로그 확인** | `tail -f log.txt` | `Get-Content log.txt -Wait` |

---

## 📊 현재 데이터 현황

- **총 앨범**: 4,400개 이상
- **수집 진행 중**: 백그라운드 자동 수집
- **업데이트**: 실시간

---

## 🎯 로드맵

### ✅ 완료
- [x] 웹 UI 구현 (홈, 검색, TOP100, 최신발매)
- [x] 앨범 상세 페이지
- [x] 공유 기능 (짧은 URL + QR 코드)
- [x] 반응형 디자인
- [x] 데이터 수집 시스템
- [x] 국내 + 글로벌 플랫폼 통합 수집

### 🔄 진행 중
- [ ] 데이터 완성 (4,400+ 앨범)
- [ ] 플랫폼 로고 이미지 추가
- [ ] 성능 최적화

### 📅 예정
- [ ] 관리자 페이지
- [ ] 통계 대시보드
- [ ] 사용자 피드백 시스템

---

## 🤝 기여

이슈 및 PR 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 라이선스

MIT License - 자유롭게 사용하세요!

---

## 🙏 감사

- **[Flask](https://flask.palletsprojects.com)** - 웹 프레임워크
- **[Selenium](https://www.selenium.dev)** - 웹 자동화
- **[Docker](https://www.docker.com)** - 컨테이너 플랫폼
- **[Companion.global](https://companion.global)** - 글로벌 링크 API

---

## 📞 문의

- **카카오톡**: [오류제보](https://pf.kakao.com/_azxkPn)
- **GitHub Issues**: [이슈 생성](https://github.com/yourusername/release-album-link/issues)

---

**만든 사람**: Candid Music Entertainment
**버전**: 3.0.0
**마지막 업데이트**: 2025-10-29

---

## 🚀 빠른 명령어 참고

### 로컬 서버 실행
```bash
python3 api/index.py
```

### 데이터 수집 시작
```bash
python3 collect_global_resume.py
```

### 수집 상태 확인
```bash
tail -f collection.log
```

### 데이터베이스 확인
```bash
sqlite3 album_links.db "SELECT COUNT(*) FROM album_platform_links;"
```

---

**🎵 캔디드뮤직 링크 - 모든 플랫폼의 음악을 한 곳에서**
