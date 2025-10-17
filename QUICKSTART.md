# 🚀 빠른 시작 가이드

## 📋 목차

1. [로컬 개발](#로컬-개발)
2. [링크 수집](#링크-수집)
3. [Vercel 배포](#vercel-배포)

---

## 🖥️ 로컬 개발

### 1. 환경 설정
```bash
# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일)
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-token
```

### 2. 로컬 서버 실행
```bash
# SQLite 사용 (로컬 개발)
python3 db_api.py

# 브라우저 접속
open http://localhost:5002
```

---

## 🔗 링크 수집

### 방법 1: 간단 실행
```bash
# Docker 서비스 시작
docker-compose up -d companion-api selenium-chrome

# 환경 변수 로드
export $(cat .env | grep -v '^#' | xargs)

# 10개 앨범 수집
python3 collect_n8n_style.py 10
```

### 방법 2: 자동 스크립트 (권장)
```bash
# 실행 권한 부여 (최초 1회)
chmod +x quick-collect.sh

# 수집 시작
./quick-collect.sh 10    # 10개
./quick-collect.sh 50    # 50개
./quick-collect.sh       # 전체
```

### 진행 상황 확인
```bash
# 실시간 로그 (수집 중)
tail -f logs/collection.log

# 데이터베이스 확인
turso db shell album-links
SELECT COUNT(*) FROM album_platform_links WHERE found = 1;
```

**자세한 가이드**: [STANDALONE_COLLECTION_GUIDE.md](STANDALONE_COLLECTION_GUIDE.md)

---

## ☁️ Vercel 배포

### 1. 자동 배포 (권장)
```bash
./deploy.sh
```

### 2. 수동 배포
```bash
# Vercel CLI 설치
npm install -g vercel

# 로그인
vercel login

# Turso 환경 변수 설정
vercel env add TURSO_DATABASE_URL
vercel env add TURSO_AUTH_TOKEN

# 배포
vercel --prod
```

**자세한 가이드**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 🔧 문제 해결

### Docker 서비스 연결 안 됨
```bash
docker-compose restart companion-api selenium-chrome
sleep 20  # 초기화 대기
```

### Turso 인증 오류
```bash
# 환경 변수 확인
echo $TURSO_DATABASE_URL
echo $TURSO_AUTH_TOKEN

# 수동 설정
export TURSO_DATABASE_URL="..."
export TURSO_AUTH_TOKEN="..."
```

### 수집 중단 후 재개
```bash
# 진행 상황이 자동 저장됩니다
# 다시 실행하면 이어서 수집
./quick-collect.sh 50
```

---

## 📚 추가 문서

- **배포 가이드**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **수집 가이드**: [STANDALONE_COLLECTION_GUIDE.md](STANDALONE_COLLECTION_GUIDE.md)
- **프로젝트 현황**: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **NAS 배포**: [docs/nas/NAS_SETUP_SIMPLE.md](docs/nas/NAS_SETUP_SIMPLE.md)

---

## 💬 문의

- GitHub Issues: [이슈 등록](https://github.com/yourusername/release-album-link/issues)
- 이메일: support@candidmusic.com
