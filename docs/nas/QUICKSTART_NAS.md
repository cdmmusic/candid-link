# ⚡ NAS 배포 빠른 시작 가이드

5분 안에 시작하는 앨범 링크 수집 시스템!

---

## 🎯 전제 조건

- Synology NAS (DSM 7.0+) 또는 Docker 지원 NAS
- Container Manager 설치됨
- SSH 접속 가능
- 인터넷 연결

---

## 🚀 5분 배포

### 1️⃣ 패키지 업로드 (1분)

**방법 A: File Station**
1. `nas-deploy.tar.gz` 다운로드
2. File Station → `docker` 폴더 생성
3. 파일 업로드

**방법 B: scp**
```bash
scp nas-deploy.tar.gz admin@YOUR_NAS_IP:/volume1/docker/
```

### 2️⃣ SSH 접속 및 압축 해제 (1분)

```bash
ssh admin@YOUR_NAS_IP
cd /volume1/docker
mkdir album-links && cd album-links
tar -xzf ../nas-deploy.tar.gz
```

### 3️⃣ 환경 변수 설정 (2분)

```bash
nano .env
```

**필수 3가지만 수정:**
```bash
# 1. Turso 데이터베이스 URL
TURSO_DATABASE_URL=libsql://album-links-cdmmusic.turso.io

# 2. Turso 인증 토큰
TURSO_AUTH_TOKEN=eyJhbGc...your-token-here

# 3. n8n 비밀번호 (보안!)
N8N_BASIC_AUTH_PASSWORD=StrongPassword123!
```

저장: `Ctrl + O`, `Enter`, `Ctrl + X`

### 4️⃣ 자동 설정 및 실행 (1분)

```bash
bash setup-nas.sh
docker-compose up -d
```

### 5️⃣ 접속 확인 (30초)

```bash
# 서비스 상태
docker-compose ps

# n8n 접속
# http://YOUR_NAS_IP:5678
```

---

## ✅ 완료!

**n8n 접속:**
- URL: `http://YOUR_NAS_IP:5678`
- 계정: `admin` / (설정한 비밀번호)

**다음 할 일:**
1. n8n에서 워크플로우 확인
2. 수집 작업 모니터링: `docker-compose logs -f collector`

---

## 🔧 포트 충돌 시

```bash
bash change-ports.sh
# → 옵션 1 선택 (추천 포트: 15678)
docker-compose down && docker-compose up -d
```

---

## 🆘 문제 발생 시

```bash
# 로그 확인
docker-compose logs -f

# 재시작
docker-compose restart

# 완전 재시작
docker-compose down
docker-compose up -d
```

---

## 📚 상세 가이드

전체 문서: `DEPLOYMENT_GUIDE.md`

문제 해결: Troubleshooting 섹션 참고

---

**소요 시간**: 5분
**난이도**: ⭐⭐☆☆☆ (쉬움)
**자동화**: 90% (setup-nas.sh가 대부분 처리)
