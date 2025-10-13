# Vercel + Turso 배포 가이드

## 📋 개요
이 가이드는 음악 플랫폼 링크 통합 시스템을 Vercel + Turso로 배포하는 단계별 가이드입니다.

**목표**: 100% 무료 서버리스 배포 ($0/월)

---

## 1️⃣ Turso 설정

### 1-1. Turso CLI 설치

**macOS/Linux:**
```bash
curl -sSfL https://get.tur.so/install.sh | bash
```

**설치 확인:**
```bash
turso --version
```

### 1-2. Turso 계정 생성 및 로그인

```bash
# GitHub 계정으로 로그인
turso auth login
```

브라우저가 열리면 GitHub으로 인증합니다.

### 1-3. 데이터베이스 생성

```bash
# 데이터베이스 생성
turso db create album-links

# 데이터베이스 목록 확인
turso db list

# 데이터베이스 URL 확인
turso db show album-links

# 연결 토큰 생성
turso db tokens create album-links
```

**중요**: 출력된 `Database URL`과 `Token`을 메모장에 저장하세요!

```
Database URL: libsql://album-links-[your-username].turso.io
Token: eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
```

---

## 2️⃣ SQLite → Turso 데이터 마이그레이션

### 2-1. 로컬 SQLite를 Turso로 업로드

```bash
cd /Users/choejibin/release-album-link

# SQLite DB를 Turso로 직접 업로드
turso db upload album-links database/album_links.db
```

### 2-2. 데이터 확인

```bash
# Turso 셸 접속
turso db shell album-links

# SQL 쿼리 실행
SELECT COUNT(*) FROM album_platform_links;

# 최근 앨범 확인
SELECT artist_ko, album_ko, release_date
FROM album_platform_links
ORDER BY created_at DESC
LIMIT 5;

# 종료
.quit
```

---

## 3️⃣ Vercel 프로젝트 준비

### 3-1. 프로젝트 구조 변환

현재 Flask 앱을 Vercel Serverless로 변환해야 합니다. 다음 단계를 실행합니다:

1. **Next.js + API Routes** (추천) 또는
2. **Python Serverless Functions** (Flask 코드 재사용)

이 가이드에서는 **옵션 2 (Python Serverless)**를 사용합니다.

### 3-2. Vercel CLI 설치

```bash
# npm이 설치되어 있는지 확인
npm --version

# Vercel CLI 설치
npm install -g vercel

# 로그인
vercel login
```

### 3-3. 필요한 파일 생성

다음 명령어를 실행하여 Vercel 설정 파일을 자동 생성합니다:

```bash
cd /Users/choejibin/release-album-link
# 다음 단계에서 자동으로 생성됩니다
```

---

## 4️⃣ 환경 변수 설정

### 4-1. .env 파일 생성

```bash
cd /Users/choejibin/release-album-link

cat > .env.production << 'EOF'
# Turso Database
TURSO_DATABASE_URL=libsql://album-links-[your-username].turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
EOF
```

**주의**: 위의 값을 1-3단계에서 메모한 실제 값으로 변경하세요!

### 4-2. Vercel 환경 변수 설정

```bash
# Vercel 프로젝트 생성 (처음 한 번만)
vercel

# 환경 변수 추가
vercel env add TURSO_DATABASE_URL
vercel env add TURSO_AUTH_TOKEN
```

---

## 5️⃣ 배포

### 5-1. 프로덕션 배포

```bash
cd /Users/choejibin/release-album-link

# 프로덕션 배포
vercel --prod
```

### 5-2. 배포 확인

배포가 완료되면 URL이 출력됩니다:
```
🎉 Production: https://album-links.vercel.app
```

브라우저에서 접속하여 확인합니다.

---

## 6️⃣ 테스트

### 6-1. API 테스트

```bash
# Health Check
curl https://album-links.vercel.app/health

# 앨범 목록 조회
curl https://album-links.vercel.app/api/albums-with-links?page=1&limit=10
```

### 6-2. 웹 UI 테스트

브라우저에서 접속:
- 메인 페이지: https://album-links.vercel.app/
- 앨범 상세: https://album-links.vercel.app/album/...

---

## 📊 예상 비용

| 서비스 | 플랜 | 비용 |
|--------|------|------|
| Vercel | Hobby | **$0/월** |
| Turso | Starter | **$0/월** |
| **합계** | | **$0/월** |

### 무료 플랜 한도
- **Vercel**: 100GB 대역폭, 무제한 요청
- **Turso**: 9GB 저장, 500M rows, 1B reads

현재 데이터:
- DB 크기: 22MB (여유 충분)
- 앨범 수: 5,093개 (여유 충분)

---

## 🔧 문제 해결

### 문제 1: Turso 업로드 실패
```bash
# 데이터베이스 재생성
turso db destroy album-links
turso db create album-links
turso db upload album-links database/album_links.db
```

### 문제 2: Vercel 배포 실패
```bash
# 로그 확인
vercel logs

# 다시 배포
vercel --prod --force
```

### 문제 3: 환경 변수 오류
```bash
# 환경 변수 확인
vercel env ls

# 환경 변수 제거 후 재등록
vercel env rm TURSO_DATABASE_URL
vercel env add TURSO_DATABASE_URL
```

---

## 📚 다음 단계

배포가 완료되면:
1. 커스텀 도메인 연결 (선택)
2. 배치 처리로 남은 앨범 링크 수집
3. 성능 모니터링 및 최적화

---

**작성일**: 2025-10-13
**프로젝트**: 음악 플랫폼 링크 통합 시스템
