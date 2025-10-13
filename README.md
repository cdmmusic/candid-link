# 🎵 음악 플랫폼 링크 통합 시스템

17개 음악 스트리밍 플랫폼의 앨범 링크를 한 곳에서 제공하는 서비스입니다.

[![Deploy to Vercel](https://img.shields.io/badge/Deploy-Vercel-black)](https://vercel.com/import/project)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ✨ 주요 기능

- **17개 플랫폼 지원**: Melon, Spotify, Apple Music 등 주요 플랫폼
- **통합 검색**: 아티스트/앨범명으로 빠른 검색
- **반응형 디자인**: 모바일/데스크톱 최적화
- **무한 스크롤**: 5,000개 이상의 앨범을 부드럽게 탐색
- **실시간 링크**: 각 플랫폼으로 바로 이동
- **100% 무료**: Vercel + Turso 서버리스 배포

---

## 🚀 빠른 배포 (5분)

```bash
# 자동 배포 스크립트 실행
./deploy.sh
```

**또는 수동 배포:**

```bash
# 1. CLI 설치
curl -sSfL https://get.tur.so/install.sh | bash
npm install -g vercel

# 2. 로그인
turso auth login
vercel login

# 3. DB 생성 및 업로드
turso db create album-links
turso db upload album-links database/album_links.db

# 4. 환경 변수 설정
turso db show album-links --url
turso db tokens create album-links
vercel env add TURSO_DATABASE_URL
vercel env add TURSO_AUTH_TOKEN

# 5. 배포
vercel --prod
```

**상세 가이드**: [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## 📊 지원 플랫폼 (17개)

### 🇰🇷 국내 (5개)
- **Melon** | **Genie** | **Bugs** | **FLO** | **VIBE**

### 🌍 글로벌 (12개)
- **Apple Music** | **Spotify** | **YouTube** | **Amazon Music**
- **Deezer** | **Tidal** | **KKBox** | **Anghami**
- **Pandora** | **LINE Music** | **AWA** | **Moov** | **QQ MUSIC**

---

## 🏗️ 기술 스택

### 프론트엔드
- HTML5 + CSS3 + Vanilla JavaScript
- 반응형 디자인
- 무한 스크롤 + 실시간 검색

### 백엔드
- **Python 3.x** + **Flask 3.0**
- Vercel Serverless Functions

### 데이터베이스
- **Turso** (libSQL - SQLite 호환)
- 5,093개 앨범
- 86,581개 플랫폼 링크

### 인프라
- **Vercel** (호스팅 + CDN)
- **Turso** (데이터베이스)
- **n8n** (링크 수집 자동화)

---

## 💰 비용

**완전 무료** - $0/월

| 서비스 | 플랜 | 한도 | 비용 |
|--------|------|------|------|
| Vercel | Hobby | 100GB/월, 무제한 요청 | $0 |
| Turso | Starter | 9GB, 500M rows | $0 |

---

## 📂 프로젝트 구조

```
release-album-link/
├── api/
│   └── index.py                 # Vercel Serverless Function
├── database/
│   └── album_links.db           # SQLite DB (22MB, 5,093 앨범)
├── docs/                        # 문서
│   ├── QUICKSTART.md            # 5분 배포 가이드
│   ├── DEPLOYMENT_GUIDE.md      # 상세 배포 가이드
│   ├── DEPLOYMENT_SUMMARY.md    # 배포 체크리스트
│   ├── README_BATCH.md          # 배치 처리 가이드
│   ├── README_DEPLOYMENT.md     # 배포 메인 문서
│   └── PROJECT_STATUS.md        # 프로젝트 현황
├── scripts/
│   └── batch_process.py         # 배치 처리 스크립트
├── workflows/
│   └── release-album-link.json  # n8n 워크플로우
├── vercel.json                  # Vercel 설정
├── requirements.txt             # Python 의존성
├── deploy.sh                    # 자동 배포 스크립트
├── db_api.py                    # 로컬 개발 서버
├── batch_process_resume.py      # 배치 처리 (중단/재개)
├── import_excel.py              # Excel 데이터 import
└── README.md                    # 이 파일
```

---

## 📖 문서

### 배포 가이드
- **[빠른 시작 (5분)](docs/QUICKSTART.md)** - 가장 빠른 배포 방법
- **[상세 가이드](docs/DEPLOYMENT_GUIDE.md)** - 단계별 배포 설명
- **[배포 요약](docs/DEPLOYMENT_SUMMARY.md)** - 배포 준비 체크리스트

### 개발 가이드
- **[배치 처리](docs/README_BATCH.md)** - 앨범 링크 자동 수집
- **[프로젝트 현황](docs/PROJECT_STATUS.md)** - 데이터 현황 및 통계

---

## 🔧 로컬 개발

### 필요 사항
- Python 3.x
- SQLite3

### 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# Flask 서버 실행
python db_api.py

# 브라우저에서 접속
open http://localhost:5002
```

---

## 🔄 데이터 업데이트

### n8n 워크플로우로 링크 수집

1. **n8n 실행**
```bash
npx n8n
```

2. **워크플로우 import**
- `workflows/release-album-link.json` 파일을 n8n에 import
- 웹훅 활성화

3. **배치 처리 실행**
```bash
python batch_process_resume.py
```

**상세 가이드**: [docs/README_BATCH.md](docs/README_BATCH.md)

---

## 📊 데이터 현황

- **총 앨범**: 5,093개
- **총 링크**: 86,581개 (이론치)
- **링크 수집 완료**: 10개
- **남은 작업**: 5,083개 앨범
- **지원 플랫폼**: 17개

**업데이트**: 2025-10-13

---

## 🎯 로드맵

### ✅ Phase 1: 배포 (완료)
- [x] Vercel + Turso 서버리스 배포
- [x] 자동 배포 스크립트
- [x] 상세 문서 작성

### 🔄 Phase 2: 데이터 완성 (진행 중)
- [ ] 5,083개 앨범 링크 수집
- [ ] 배치 처리 자동화
- [ ] 에러 처리 개선

### 📅 Phase 3: 기능 개선
- [ ] 고급 검색 (장르, 발매일)
- [ ] 즐겨찾기 기능
- [ ] 공유 기능 개선
- [ ] 다국어 지원 (EN)

---

## 🤝 기여

이슈 및 PR은 환영합니다!

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

- **[Vercel](https://vercel.com)** - 무료 호스팅 및 CDN
- **[Turso](https://turso.tech)** - 무료 libSQL 데이터베이스
- **[n8n](https://n8n.io)** - 워크플로우 자동화
- **[Flask](https://flask.palletsprojects.com)** - 웹 프레임워크

---

## 📞 문의

- **GitHub Issues**: [이슈 생성](https://github.com/yourusername/release-album-link/issues)
- **프로젝트 현황**: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **배포 가이드**: [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

**만든 사람**: Candid Music Entertainment
**버전**: 2.0.0
**마지막 업데이트**: 2025-10-13
**비용**: $0/월 (영구 무료)

---

## 🚀 지금 시작하기

```bash
# 배포 스크립트 실행
./deploy.sh

# 또는 빠른 가이드 확인
cat docs/QUICKSTART.md
```

**배포 후 URL**: `https://your-project.vercel.app`
