#!/bin/bash

###############################################################################
# NAS 환경 자동 설정 스크립트
# 사용법: bash setup-nas.sh
###############################################################################

set -e

echo "======================================================================"
echo "  NAS 환경 자동 설정 시작"
echo "======================================================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 현재 디렉토리 확인
echo -e "${YELLOW}[1/8] 현재 디렉토리 확인...${NC}"
CURRENT_DIR=$(pwd)
echo "작업 디렉토리: $CURRENT_DIR"
echo ""

# 2. 필수 파일 확인
echo -e "${YELLOW}[2/8] 필수 파일 확인...${NC}"
REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile.companion-api"
    "Dockerfile.collector"
    "companion_api.py"
    "collect_n8n_style.py"
    "requirements.txt"
    ".env"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (누락)"
        exit 1
    fi
done
echo ""

# 3. 필요한 디렉토리 생성
echo -e "${YELLOW}[3/8] 디렉토리 생성...${NC}"
mkdir -p n8n_data
mkdir -p workflows
mkdir -p scripts
echo -e "${GREEN}✓${NC} 디렉토리 생성 완료"
echo ""

# 4. scripts 파일 복사 (있는 경우)
echo -e "${YELLOW}[4/8] 스크립트 파일 복사...${NC}"
if [ -f "auto_process_albums.py" ]; then
    cp auto_process_albums.py scripts/ 2>/dev/null || true
    echo -e "${GREEN}✓${NC} auto_process_albums.py 복사"
fi
echo ""

# 5. .env 파일 확인
echo -e "${YELLOW}[5/8] 환경 변수 확인...${NC}"
if [ -f ".env" ]; then
    if grep -q "TURSO_DATABASE_URL" .env && grep -q "TURSO_AUTH_TOKEN" .env; then
        echo -e "${GREEN}✓${NC} .env 파일 설정됨"
    else
        echo -e "${RED}⚠${NC} .env 파일에 Turso 설정이 필요합니다"
        echo "   TURSO_DATABASE_URL과 TURSO_AUTH_TOKEN을 추가하세요"
    fi
else
    echo -e "${RED}✗${NC} .env 파일이 없습니다"
    exit 1
fi
echo ""

# 6. CPU 아키텍처 감지
echo -e "${YELLOW}[6/8] CPU 아키텍처 감지...${NC}"
ARCH=$(uname -m)
echo "감지된 아키텍처: $ARCH"

if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    echo -e "${YELLOW}→ ARM64 감지: docker-compose.yml에서 seleniarm 이미지 사용 필요${NC}"
    # docker-compose.yml 자동 수정
    if [ -f "docker-compose.yml" ]; then
        sed -i.bak 's|selenium/standalone-chrome:latest|seleniarm/standalone-chromium:latest|g' docker-compose.yml
        sed -i.bak '/seleniarm/a\    platform: linux/arm64' docker-compose.yml
        echo -e "${GREEN}✓${NC} docker-compose.yml 자동 수정 완료"
    fi
else
    echo -e "${GREEN}→ x86_64: 기본 selenium 이미지 사용${NC}"
fi
echo ""

# 7. Docker 및 Docker Compose 확인
echo -e "${YELLOW}[7/8] Docker 환경 확인...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker 설치됨 ($(docker --version))"
else
    echo -e "${RED}✗${NC} Docker가 설치되지 않았습니다"
    echo "   Synology: Container Manager 패키지 설치 필요"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose 설치됨 ($(docker-compose --version))"
else
    echo -e "${RED}✗${NC} Docker Compose가 설치되지 않았습니다"
    exit 1
fi
echo ""

# 8. 권한 설정
echo -e "${YELLOW}[8/8] 권한 설정...${NC}"
chmod +x collect_n8n_style.py 2>/dev/null || true
chmod +x collect_all.sh 2>/dev/null || true
chmod +x check_ready.sh 2>/dev/null || true
echo -e "${GREEN}✓${NC} 실행 권한 부여 완료"
echo ""

# 완료 메시지
echo "======================================================================"
echo -e "${GREEN}  설정 완료!${NC}"
echo "======================================================================"
echo ""
echo "다음 명령어로 서비스를 시작하세요:"
echo ""
echo -e "${GREEN}1. Docker Compose 실행:${NC}"
echo "   docker-compose up -d"
echo ""
echo -e "${GREEN}2. 서비스 확인:${NC}"
echo "   docker-compose ps"
echo ""
echo -e "${GREEN}3. n8n 접속:${NC}"
echo "   http://$(hostname -I | awk '{print $1}'):5678"
echo ""
echo -e "${GREEN}4. 로그 확인:${NC}"
echo "   docker-compose logs -f"
echo ""
echo -e "${YELLOW}주의:${NC}"
echo "- 방화벽에서 5678, 5001, 4444 포트를 개방하세요"
echo "- .env 파일에 Turso 인증 정보를 확인하세요"
echo ""
