#!/bin/bash

###############################################################################
# NAS 배포 패키지 생성 스크립트
# 사용법: bash prepare-nas-package.sh
# 결과: nas-deploy.tar.gz 파일 생성
###############################################################################

set -e

echo "======================================================================"
echo "  NAS 배포 패키지 생성"
echo "======================================================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 임시 디렉토리 생성
TEMP_DIR="nas-deploy-temp"
PACKAGE_NAME="nas-deploy.tar.gz"

echo -e "${YELLOW}[1/5] 임시 디렉토리 생성...${NC}"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# 필수 파일 복사
echo -e "${YELLOW}[2/5] 필수 파일 복사...${NC}"

# Docker 관련
cp docker-compose.yml $TEMP_DIR/
cp Dockerfile.companion-api $TEMP_DIR/
cp Dockerfile.collector $TEMP_DIR/
cp Dockerfile.db-api $TEMP_DIR/

# Python 스크립트
cp companion_api.py $TEMP_DIR/
cp collect_n8n_style.py $TEMP_DIR/
cp db_api.py $TEMP_DIR/
cp requirements.txt $TEMP_DIR/

# 환경 설정
cp .env.example $TEMP_DIR/.env
cp setup-nas.sh $TEMP_DIR/

# 쉘 스크립트
cp collect_all.sh $TEMP_DIR/ 2>/dev/null || true
cp check_ready.sh $TEMP_DIR/ 2>/dev/null || true

# 디렉토리 생성
mkdir -p $TEMP_DIR/n8n_data
mkdir -p $TEMP_DIR/workflows
mkdir -p $TEMP_DIR/scripts
mkdir -p $TEMP_DIR/database
mkdir -p $TEMP_DIR/templates
mkdir -p $TEMP_DIR/static

# scripts 복사 (있는 경우)
if [ -d "scripts" ]; then
    cp scripts/*.py $TEMP_DIR/scripts/ 2>/dev/null || true
fi

# workflows 복사 (있는 경우)
if [ -d "workflows" ]; then
    cp workflows/*.json $TEMP_DIR/workflows/ 2>/dev/null || true
fi

# templates 복사 (있는 경우)
if [ -d "templates" ]; then
    cp -r templates/* $TEMP_DIR/templates/ 2>/dev/null || true
fi

# static 복사 (있는 경우)
if [ -d "static" ]; then
    cp -r static/* $TEMP_DIR/static/ 2>/dev/null || true
fi

# database 초기화 스크립트 생성
cat > $TEMP_DIR/database/init_db.sql << 'SQLEOF'
CREATE TABLE IF NOT EXISTS album_platform_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_ko TEXT NOT NULL,
    artist_en TEXT,
    album_ko TEXT NOT NULL,
    album_en TEXT,
    platform_type TEXT NOT NULL,
    platform_id TEXT,
    platform_code TEXT,
    platform_name TEXT,
    platform_url TEXT,
    album_id TEXT,
    upc TEXT,
    album_cover_url TEXT,
    release_date TEXT,
    genre TEXT,
    release_type TEXT,
    found INTEGER DEFAULT 0,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(artist_ko, album_ko, platform_type, platform_id, platform_code)
);

CREATE INDEX IF NOT EXISTS idx_artist_album ON album_platform_links(artist_ko, album_ko);
CREATE INDEX IF NOT EXISTS idx_platform ON album_platform_links(platform_type, platform_id);
CREATE INDEX IF NOT EXISTS idx_found ON album_platform_links(found);
CREATE INDEX IF NOT EXISTS idx_release_date ON album_platform_links(release_date);
SQLEOF

echo -e "${GREEN}✓${NC} 파일 복사 완료"

# README 생성
echo -e "${YELLOW}[3/5] README 생성...${NC}"
cat > $TEMP_DIR/README.md << 'EOF'
# NAS 환경 배포 가이드

## 📦 포함된 파일
- `docker-compose.yml`: Docker Compose 설정
- `setup-nas.sh`: 자동 설정 스크립트
- `.env`: 환경 변수 (수정 필요)
- Python 스크립트 및 Dockerfile

## 🚀 빠른 시작

### 1. NAS에 파일 업로드
이 폴더를 NAS의 Docker 폴더로 복사합니다.

**Synology 예시:**
```bash
/volume1/docker/album-links/
```

### 2. .env 파일 수정
`.env` 파일을 열고 Turso 인증 정보를 입력:
```bash
TURSO_DATABASE_URL=libsql://your-database.turso.io
TURSO_AUTH_TOKEN=your-token-here
N8N_BASIC_AUTH_PASSWORD=your-secure-password
```

### 3. 자동 설정 실행
```bash
cd /volume1/docker/album-links
bash setup-nas.sh
```

### 4. Docker Compose 실행
```bash
docker-compose up -d
```

### 5. 서비스 확인
```bash
docker-compose ps
docker-compose logs -f
```

## 🌐 서비스 접속

- **n8n**: http://your-nas-ip:5678
- **Companion API**: http://your-nas-ip:5001
- **Selenium Grid**: http://your-nas-ip:4444
- **웹 UI (앨범 목록)**: http://your-nas-ip:5002

## 📝 수동 수집 실행

```bash
docker-compose run --rm collector python3 collect_n8n_style.py 100
```

## 🛠️ 문제 해결

### 포트 충돌
`docker-compose.yml`에서 포트 변경:
```yaml
ports:
  - "15678:5678"  # 5678 → 15678
```

### ARM64 NAS
자동으로 감지되지만, 수동으로 변경하려면:
```yaml
selenium-chrome:
  image: seleniarm/standalone-chromium:latest
  platform: linux/arm64
```

### 메모리 부족
각 서비스에 메모리 제한 추가:
```yaml
mem_limit: 1g
```

## 📞 지원

문제가 발생하면 로그를 확인하세요:
```bash
docker-compose logs -f n8n
docker-compose logs -f companion-api
```
EOF

echo -e "${GREEN}✓${NC} README.md 생성 완료"

# 권한 설정
echo -e "${YELLOW}[4/5] 권한 설정...${NC}"
chmod +x $TEMP_DIR/setup-nas.sh
chmod +x $TEMP_DIR/*.sh 2>/dev/null || true

# 압축
echo -e "${YELLOW}[5/5] 패키지 압축...${NC}"
tar -czf $PACKAGE_NAME -C $TEMP_DIR .
rm -rf $TEMP_DIR

# 완료
echo ""
echo "======================================================================"
echo -e "${GREEN}  패키지 생성 완료!${NC}"
echo "======================================================================"
echo ""
echo "생성된 파일: $PACKAGE_NAME"
echo "파일 크기: $(du -h $PACKAGE_NAME | awk '{print $1}')"
echo ""
echo "다음 단계:"
echo "1. $PACKAGE_NAME 파일을 NAS로 전송"
echo "2. NAS에서 압축 해제: tar -xzf $PACKAGE_NAME"
echo "3. setup-nas.sh 실행: bash setup-nas.sh"
echo "4. Docker Compose 시작: docker-compose up -d"
echo ""
