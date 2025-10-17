# 🚀 NAS 배포 가이드

앨범 링크 수집 시스템을 Synology NAS 또는 다른 NAS 환경에 배포하는 가이드입니다.

## 📋 시스템 요구사항

### 하드웨어
- **CPU**: ARM64 (Apple Silicon, Synology ARM NAS) 또는 x86_64
- **메모리**: 최소 4GB RAM (권장 8GB+)
- **디스크**: 최소 10GB 여유 공간

### 소프트웨어
- Docker 20.10+
- Docker Compose 1.29+
- 인터넷 연결

### Synology NAS 전용
- DSM 7.0 이상
- Container Manager 패키지 설치됨

---

## 📦 1단계: 배포 패키지 준비

### 로컬에서 패키지 생성
```bash
cd /Users/choejibin/release-album-link
bash prepare-nas-package.sh
```

생성된 파일: `nas-deploy.tar.gz` (약 24KB)

### NAS로 파일 전송

#### 방법 1: scp 사용
```bash
scp nas-deploy.tar.gz admin@192.168.1.100:/volume1/docker/
```

#### 방법 2: Synology File Station
1. File Station 열기
2. `docker` 폴더로 이동 (없으면 생성)
3. `nas-deploy.tar.gz` 업로드

#### 방법 3: SMB/CIFS
1. NAS 공유 폴더에 접속
2. `docker` 폴더에 파일 복사

---

## 🔧 2단계: NAS에서 설정

### SSH 접속
```bash
ssh admin@192.168.1.100
```

### 작업 디렉토리 이동
```bash
cd /volume1/docker
mkdir -p album-links
cd album-links
```

### 패키지 압축 해제
```bash
tar -xzf ../nas-deploy.tar.gz
ls -la
```

예상 파일 목록:
```
.env
README.md
setup-nas.sh
docker-compose.yml
Dockerfile.companion-api
Dockerfile.collector
companion_api.py
collect_n8n_style.py
requirements.txt
collect_all.sh
check_ready.sh
n8n_data/
workflows/
scripts/
```

---

## ⚙️ 3단계: 환경 변수 설정

### .env 파일 수정
```bash
vi .env
# 또는
nano .env
```

### 필수 수정 항목
```bash
# Turso 데이터베이스 (필수)
TURSO_DATABASE_URL=libsql://album-links-cdmmusic.turso.io
TURSO_AUTH_TOKEN=eyJh...your-token-here

# n8n 비밀번호 변경 (보안 필수!)
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your-secure-password-here

# NAS IP로 변경
WEBHOOK_URL=http://192.168.1.100:5678/
```

### 선택 항목 (포트 충돌 시)
```bash
N8N_PORT=5678          # 다른 서비스와 충돌 시 변경 (예: 15678)
COMPANION_API_PORT=5001
SELENIUM_PORT=4444
```

포트 변경 도우미 사용:
```bash
bash change-ports.sh
```

---

## 🚀 4단계: 자동 설정 실행

```bash
bash setup-nas.sh
```

이 스크립트는 다음 작업을 수행합니다:
- ✅ 필수 파일 확인
- ✅ 디렉토리 생성 (`n8n_data`, `workflows`, `scripts`)
- ✅ CPU 아키텍처 감지 (ARM64 자동 인식)
- ✅ Docker 환경 확인
- ✅ 실행 권한 설정

---

## 🐳 5단계: Docker Compose 실행

### 서비스 시작
```bash
docker-compose up -d
```

### 서비스 확인
```bash
docker-compose ps
```

예상 출력:
```
NAME                      STATUS    PORTS
album-links-n8n           Up        0.0.0.0:5678->5678/tcp
album-links-companion-api Up        0.0.0.0:5001->5001/tcp
album-links-selenium      Up        0.0.0.0:4444->4444/tcp
album-links-collector     Up
```

### 로그 확인
```bash
# 전체 로그
docker-compose logs -f

# 개별 서비스 로그
docker-compose logs -f n8n
docker-compose logs -f companion-api
docker-compose logs -f collector
```

---

## 🌐 6단계: 서비스 접속

### n8n 워크플로우 자동화
- URL: `http://192.168.1.100:5678`
- 계정: `.env`에 설정한 ID/PW
- 기본: `admin` / `changeme`

### Companion API (내부 서비스)
- URL: `http://192.168.1.100:5001/health`

### Selenium Grid (디버깅용)
- URL: `http://192.168.1.100:4444`

---

## 🔥 7단계: 방화벽 설정

### Synology DSM 방화벽
1. **제어판** → **보안** → **방화벽**
2. 규칙 편집
3. 포트 추가:
   - TCP: 5678 (n8n)
   - TCP: 5001 (Companion API)
   - TCP: 4444 (Selenium - 선택)

### 라우터 포트 포워딩 (외부 접속 시)
```
외부 포트 → 내부 IP:포트
5678      → 192.168.1.100:5678
```

⚠️ **보안 주의**: n8n에 강력한 비밀번호를 설정하세요!

---

## 📊 8단계: 수집 작업 실행

### 자동 수집 (권장)
collector 컨테이너가 자동으로 실행됩니다.

### 수동 수집 (테스트용)
```bash
# 100개 앨범만 수집
docker-compose run --rm collector python3 collect_n8n_style.py 100

# 전체 수집
docker-compose run --rm collector python3 collect_n8n_style.py
```

### 수집 진행 상황 확인
```bash
docker-compose logs -f collector
```

---

## 🛠️ 문제 해결 (Troubleshooting)

### 1. 포트 충돌 오류
```bash
Error: bind: address already in use
```

**해결:**
```bash
bash change-ports.sh
# 추천 포트로 변경 (15678, 15001, 14444)
docker-compose down
docker-compose up -d
```

### 2. ARM64 이미지 오류 (Apple Silicon, ARM NAS)
```bash
Error: no matching manifest for linux/arm64
```

**해결:** `docker-compose.yml` 수정
```yaml
selenium-chrome:
  image: seleniarm/standalone-chromium:latest
  platform: linux/arm64
```

### 3. Turso 연결 오류
```bash
Error: libsql connection failed
```

**해결:**
- `.env` 파일의 `TURSO_DATABASE_URL`과 `TURSO_AUTH_TOKEN` 확인
- 토큰 유효성 확인 (만료 여부)
- 인터넷 연결 확인

### 4. 메모리 부족
```bash
Error: OOMKilled
```

**해결:** `docker-compose.yml`에 메모리 제한 추가
```yaml
services:
  selenium-chrome:
    mem_limit: 2g
  n8n:
    mem_limit: 1g
  companion-api:
    mem_limit: 1g
```

### 5. n8n 접속 불가
```bash
Connection refused
```

**해결:**
1. 서비스 상태 확인: `docker-compose ps`
2. 로그 확인: `docker-compose logs n8n`
3. 포트 확인: `netstat -tulpn | grep 5678`
4. 방화벽 규칙 확인

### 6. Selenium 연결 실패
```bash
Error: selenium hub not reachable
```

**해결:**
```bash
docker-compose restart selenium-chrome
docker-compose logs selenium-chrome
```

### 7. 컨테이너 재시작 루프
```bash
Restarting (1) X seconds ago
```

**해결:**
```bash
# 상세 로그 확인
docker-compose logs --tail=100 [service-name]

# 이미지 재빌드
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔄 업데이트 및 유지보수

### 코드 업데이트
```bash
cd /volume1/docker/album-links
docker-compose down
# 새 nas-deploy.tar.gz 업로드 및 압축 해제
docker-compose build --no-cache
docker-compose up -d
```

### 데이터 백업
```bash
# n8n 워크플로우 백업
tar -czf n8n-backup-$(date +%Y%m%d).tar.gz n8n_data/

# 로그 백업
docker-compose logs > logs-$(date +%Y%m%d).txt
```

### 서비스 재시작
```bash
# 전체 재시작
docker-compose restart

# 개별 재시작
docker-compose restart n8n
docker-compose restart companion-api
```

### 서비스 중지
```bash
docker-compose down
```

### 완전 삭제 (데이터 포함)
```bash
docker-compose down -v
rm -rf n8n_data/ workflows/ scripts/
```

---

## 📈 모니터링

### 리소스 사용량 확인
```bash
docker stats
```

### 디스크 사용량
```bash
docker system df
du -sh n8n_data/
```

### 컨테이너 헬스 체크
```bash
# n8n
curl http://localhost:5678

# Companion API
curl http://localhost:5001/health

# Selenium
curl http://localhost:4444/status
```

---

## 🆘 지원 및 문의

### 로그 수집
문제 발생 시 다음 로그를 수집하세요:
```bash
docker-compose logs > debug-logs.txt
docker-compose ps > docker-status.txt
cat .env | grep -v "TOKEN\|PASSWORD" > env-info.txt
uname -a > system-info.txt

tar -czf debug-info.tar.gz debug-logs.txt docker-status.txt env-info.txt system-info.txt
```

### 체크리스트
- [ ] Docker 버전: `docker --version`
- [ ] Docker Compose 버전: `docker-compose --version`
- [ ] CPU 아키텍처: `uname -m`
- [ ] 메모리: `free -h`
- [ ] 디스크 공간: `df -h`
- [ ] 포트 확인: `netstat -tulpn | grep -E "5678|5001|4444"`

---

## 🎯 다음 단계

1. ✅ n8n에 로그인하여 워크플로우 확인
2. ✅ 첫 번째 앨범 수동 수집 테스트
3. ✅ 자동 수집 스케줄 설정
4. ✅ 외부 접속을 위한 도메인/DDNS 설정 (선택)
5. ✅ HTTPS 설정 (Nginx Reverse Proxy 권장)

---

## 📚 참고 자료

- n8n 공식 문서: https://docs.n8n.io/
- Turso 문서: https://docs.turso.tech/
- Docker Compose 문서: https://docs.docker.com/compose/
- Selenium 문서: https://www.selenium.dev/documentation/

---

**작성일**: 2025-10-14
**버전**: 1.0.0
**유지보수**: 정기적으로 Docker 이미지 업데이트 권장
