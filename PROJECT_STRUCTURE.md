# 📁 프로젝트 구조

```
release-album-link/
├── api/
│   └── index.py                      # Vercel Serverless Function (Turso)
│
├── database/
│   ├── album_links.db                # SQLite DB (24MB, 5,093 앨범)
│   └── album-links.db                # 백업
│
├── static/
│   ├── css/
│   │   └── main.css                  # 메인 스타일시트
│   ├── js/
│   │   ├── main.js                   # 메인 JavaScript
│   │   └── carousel.js               # 캐러셀 컴포넌트
│   └── img/                          # 이미지 리소스
│
├── templates/
│   └── home_v2.html                  # 홈페이지 템플릿
│
├── scripts/
│   ├── auto_collect_all.py           # 자동 수집 (Docker 전용)
│   ├── batch_process.py              # 배치 처리
│   ├── update_album_covers.py        # 커버 업데이트
│   └── maintenance/                  # 유지보수 스크립트
│       ├── update_genre_and_type.py
│       └── update_release_dates.py
│
├── workflows/
│   └── release-album-link.json       # n8n 워크플로우
│
├── docs/
│   ├── PROJECT_STATUS.md             # 프로젝트 현황
│   ├── QUICKSTART.md                 # 빠른 시작 가이드
│   ├── README_BATCH.md               # 배치 처리 가이드
│   ├── README_DEPLOYMENT.md          # 배포 가이드
│   └── nas/                          # NAS 배포 관련
│       ├── NAS_SETUP_SIMPLE.md
│       ├── QUICKSTART_NAS.md
│       └── setup-nas.sh
│
├── 📄 메인 스크립트
├── collect_n8n_style.py              # ⭐ 링크 수집 메인 스크립트
├── companion_api.py                  # Selenium API 서버
├── db_api.py                         # 로컬 개발 서버
├── import_excel.py                   # Excel 데이터 임포트
│
├── 📄 실행 스크립트
├── quick-collect.sh                  # ⭐ 빠른 수집 실행
├── deploy.sh                         # Vercel 배포
├── DEPLOY_NOW.sh                     # 간단 배포
│
├── 📄 문서
├── README.md                         # 프로젝트 메인 문서
├── QUICKSTART.md                     # 빠른 시작 가이드
├── DEPLOYMENT_GUIDE.md               # 배포 가이드
├── STANDALONE_COLLECTION_GUIDE.md    # 수집 가이드
├── PROJECT_STRUCTURE.md              # 이 파일
│
├── 📄 설정
├── requirements.txt                  # Python 의존성
├── docker-compose.yml                # Docker 서비스 구성
├── vercel.json                       # Vercel 설정
├── .gitignore                        # Git 무시 목록
├── .env                              # 환경 변수 (Turso 인증)
│
└── 📄 데이터
    └── 발매앨범DB.xlsx                # 원본 Excel 데이터 (2.1MB)
```

---

## 🎯 주요 파일 설명

### 실행 파일

| 파일 | 용도 | 사용법 |
|------|------|--------|
| `quick-collect.sh` | 링크 수집 간편 실행 | `./quick-collect.sh 10` |
| `collect_n8n_style.py` | 링크 수집 메인 스크립트 | `python3 collect_n8n_style.py 50` |
| `db_api.py` | 로컬 개발 서버 | `python3 db_api.py` |
| `companion_api.py` | Selenium API 서버 | Docker로 실행 |

### 설정 파일

| 파일 | 설명 |
|------|------|
| `.env` | Turso 데이터베이스 인증 정보 |
| `docker-compose.yml` | 5개 서비스 구성 (n8n, selenium 등) |
| `vercel.json` | Vercel 배포 설정 |
| `requirements.txt` | Python 패키지 의존성 |

### 문서

| 문서 | 내용 |
|------|------|
| `README.md` | 프로젝트 전체 개요 |
| `QUICKSTART.md` | 빠른 시작 가이드 |
| `DEPLOYMENT_GUIDE.md` | Vercel 배포 가이드 |
| `STANDALONE_COLLECTION_GUIDE.md` | 링크 수집 상세 가이드 |

---

## 🚀 빠른 시작

### 1. 링크 수집
```bash
./quick-collect.sh 10
```

### 2. 로컬 서버
```bash
python3 db_api.py
```

### 3. Vercel 배포
```bash
./deploy.sh
```

---

## 📊 현재 데이터

- **앨범 수**: 5,093개
- **플랫폼 링크**: 91,674개
- **DB 크기**: 24MB
- **지원 플랫폼**: 17개 (국내 5개, 글로벌 12개)

---

**업데이트**: 2025-10-16
