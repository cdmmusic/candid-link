# 📁 프로젝트 파일 구조

> **최종 업데이트**: 2025-10-28
> **정리 완료**: 불필요한 파일 17개 archive로 이동

---

## 📊 루트 디렉토리 (정리 후)

### 🔧 메인 수집 스크립트 (3개)

**collect_n8n_style.py** (26KB)
- 메인 수집 스크립트
- Turso DB 연결
- 국내 5개 + 글로벌 13개 플랫폼 수집
- 배치 단위 처리 (100개 앨범)

**companion_api.py** (25KB)
- Flask API (:5001)
- Selenium 기반 Companion.global 크롤링
- 글로벌 플랫폼 링크 추출

**auto_collect.sh**
- 배치 자동화 스크립트
- `./auto_collect.sh [시작] [종료]`

---

### 📊 분석 & 유틸리티 (6개)

**track_failures.py**
- 국내 플랫폼 실패 분석
- 출력: failures_kr_complete.txt, failures_kr_partial.txt

**track_global_failures.py**
- 글로벌 플랫폼 실패 분석
- 출력: failures_global_complete.txt, failures_global_partial.txt

**sync_to_turso.py**
- 로컬 SQLite → Turso 동기화
- album_links.db → libsql://album-links-cdmmusic.turso.io

**get_batch_cdma_codes.py**
- 배치 번호로 CDMA 코드 범위 조회
- 예: batch 1 → CDMA00001~CDMA00100

**import_excel.py**
- Excel (발매앨범DB.xlsx) → SQLite 변환
- 초기 앨범 데이터 import용

**db_api.py**
- 로컬 개발 서버 (Flask)
- 포트: 5002
- Turso 없이 로컬 DB로 테스트

---

### 🌐 웹 & API (1개)

**admin_api.py** (76KB)
- 관리자 API
- 앨범 추가/수정/삭제
- 통계 조회

---

### 🚀 배포 (1개)

**deploy.sh**
- Vercel 배포 스크립트
- Turso DB 업로드
- 환경 변수 설정

---

### 📝 문서 (6개)

**PROJECT_STATUS.md** ⭐ 필수
- 현재 프로젝트 상태
- 데이터베이스 구조
- 수집 통계

**RECOLLECTION_GUIDE.md** ⭐ 필수
- 재수집 가이드
- 단계별 실행 방법
- 트러블슈팅

**README.md**
- 프로젝트 소개
- 빠른 시작
- 문서 인덱스

**GLOBAL_LINK_COLLECTION_GUIDE.md**
- 글로벌 링크 수집 상세
- Companion.global 사용법
- 검색 전략

**SETUP_GUIDE.md**
- 초기 환경 설정
- Docker, Selenium 설치

**SHARE_API_GUIDE.md**
- API 사용법
- 엔드포인트 설명

---

### 🗄️ 데이터베이스 & SQL (2개)

**album_links.db** (27MB)
- 로컬 SQLite DB
- 5,103개 앨범
- 91,345개 플랫폼 링크

**fix_platform_codes.sql**
- 플랫폼 코드 통일 스크립트
- 글로벌 수집률 향상용

---

### ⚙️ 설정 파일 (5개)

**.env**
- 환경 변수 (gitignore)
- Turso 인증 정보
- Companion.global 로그인

**.env.example**
- 환경 변수 템플릿

**requirements.txt**
- Python 패키지 목록

**vercel.json**
- Vercel 배포 설정

**docker-compose.yml**
- Docker Compose 설정

---

## 📂 디렉토리 구조

```
release-album-link/
│
├── 📄 메인 스크립트 (3개)
│   ├── collect_n8n_style.py          # 메인 수집
│   ├── companion_api.py              # Flask API (Selenium)
│   └── auto_collect.sh               # 배치 자동화
│
├── 📊 분석 & 유틸리티 (6개)
│   ├── track_failures.py             # 국내 실패 분석
│   ├── track_global_failures.py      # 글로벌 실패 분석
│   ├── sync_to_turso.py              # DB 동기화
│   ├── get_batch_cdma_codes.py       # CDMA 코드 조회
│   ├── import_excel.py               # Excel import
│   └── db_api.py                     # 로컬 개발 서버
│
├── 🌐 웹 & API (1개)
│   └── admin_api.py                  # 관리자 API
│
├── 🚀 배포 (1개)
│   └── deploy.sh                     # Vercel 배포
│
├── 📝 문서 (6개)
│   ├── PROJECT_STATUS.md             # ⭐ 프로젝트 현황
│   ├── RECOLLECTION_GUIDE.md         # ⭐ 재수집 가이드
│   ├── README.md                     # 프로젝트 소개
│   ├── GLOBAL_LINK_COLLECTION_GUIDE.md
│   ├── SETUP_GUIDE.md
│   └── SHARE_API_GUIDE.md
│
├── 🗄️ 데이터베이스 (2개)
│   ├── album_links.db                # SQLite DB (27MB)
│   └── fix_platform_codes.sql        # SQL 스크립트
│
├── ⚙️ 설정 파일 (5개)
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   ├── vercel.json
│   └── docker-compose.yml
│
├── 📁 api/
│   └── index.py                      # Vercel Serverless Function
│
├── 📁 templates/
│   ├── home.html                     # 홈페이지
│   ├── search.html                   # 검색 페이지
│   └── admin/                        # 관리자 페이지
│
├── 📁 static/
│   ├── css/
│   └── js/
│
├── 📁 archive/                       # 과거 파일 보관
│   ├── old-docs-2025-10-28/          # 옛날 문서 (3개)
│   ├── scripts-old-2025-10-28/       # 구버전 스크립트 (12개)
│   └── test-files-2025-10-28/        # 테스트 파일 (2개)
│
└── 📁 database/                      # (빈 폴더, 옛날 사용)
```

---

## 🗑️ 정리된 파일 (2025-10-28)

### Archive로 이동된 파일 (17개)

#### 옛날 문서 (3개)
```
archive/old-docs-2025-10-28/
├── COLLECTION_PROGRESS.md            # Batch 2까지만 기록
├── GLOBAL_COLLECTION_FAILURE_ANALYSIS.md  # 옛날 분석
└── GLOBAL_COLLECTION_GUIDE.md        # 중복 내용
```

#### 구버전 스크립트 (12개)
```
archive/scripts-old-2025-10-28/
├── collect_from_db.py                # 구버전 수집
├── collect_single_album.py           # 단일 앨범 수집
├── collect_all_albums.py             # 전체 앨범 수집
├── collect_global_links.py           # 글로벌 수집 v1
├── collect_all_global_links.py       # 글로벌 수집 v2
├── recollect_global_links.py         # 글로벌 재수집
├── companion_api_v2.py               # API v2
├── DEPLOY_NOW.sh                     # 배포 스크립트
├── quick-collect.sh                  # 빠른 수집
├── collect_service.sh                # 서비스 스크립트
├── start_collection_screen.sh        # Screen 세션
└── run_batch.sh                      # 배치 실행
```

#### 테스트 파일 (2개)
```
archive/test-files-2025-10-28/
├── 발매앨범DB.xlsx                   # 원본 Excel (2.1MB)
└── album_links.db-info               # DB 메타 정보
```

---

## 🎯 파일 사용 가이드

### 재수집 시작하기
```bash
# 1. 문서 확인
cat PROJECT_STATUS.md
cat RECOLLECTION_GUIDE.md

# 2. 환경 설정
source .env

# 3. 수집 시작
./auto_collect.sh 1 52
```

### 실패 분석
```bash
# 국내 플랫폼
python3 track_failures.py

# 글로벌 플랫폼
python3 track_global_failures.py
```

### DB 동기화
```bash
# 로컬 → Turso
python3 sync_to_turso.py
```

### 로컬 개발
```bash
# 개발 서버 시작
python3 db_api.py
# http://localhost:5002
```

---

## 📊 파일 통계

| 카테고리 | 개수 | 설명 |
|---------|------|------|
| Python 스크립트 | 9개 | 수집, 분석, API |
| Shell 스크립트 | 2개 | 자동화, 배포 |
| 문서 | 6개 | 가이드, 현황 |
| SQL | 1개 | 플랫폼 코드 통일 |
| 설정 파일 | 5개 | 환경 변수, Docker |
| 데이터베이스 | 1개 | album_links.db (27MB) |
| **총계** | **24개** | 루트 디렉토리 |

### Archive 통계
- 옛날 문서: 3개
- 구버전 스크립트: 12개
- 테스트 파일: 2개
- **총계**: 17개 정리

---

## 🔍 파일 찾기

### 수집 관련
- 메인 수집: `collect_n8n_style.py`
- 글로벌 API: `companion_api.py`
- 배치 자동화: `auto_collect.sh`

### 분석 관련
- 국내 실패: `track_failures.py`
- 글로벌 실패: `track_global_failures.py`

### 문서
- 프로젝트 현황: `PROJECT_STATUS.md`
- 재수집 가이드: `RECOLLECTION_GUIDE.md`
- 파일 구조: `FILE_STRUCTURE.md` (이 문서)

### 설정
- 환경 변수: `.env`
- Python 패키지: `requirements.txt`

---

## ⚠️ 주의사항

### 삭제하면 안 되는 파일
- ✅ `collect_n8n_style.py` - 메인 수집 스크립트
- ✅ `companion_api.py` - Flask API
- ✅ `album_links.db` - 데이터베이스
- ✅ `PROJECT_STATUS.md` - 현황 문서
- ✅ `RECOLLECTION_GUIDE.md` - 재수집 가이드

### 삭제 가능한 파일
- ⚠️ `archive/` 폴더 전체 (필요시)
- ⚠️ `database/` 폴더 (비어있음)
- ⚠️ `.env.example` (참고용)

### Git에서 제외되는 파일
- `.env` (환경 변수)
- `album_links.db` (DB는 Turso 사용)
- `album_links.db-*` (DB 백업)
- `*.pyc`, `__pycache__/` (Python 캐시)
- `node_modules/` (npm 패키지)

---

**작성자**: Claude Code
**목적**: 프로젝트 파일 구조 명확화
**정리 일자**: 2025-10-28
**다음 문서**: PROJECT_STATUS.md (프로젝트 현황)
