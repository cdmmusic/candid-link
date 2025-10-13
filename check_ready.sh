#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "  자동 수집 시스템 준비 상태 체크"
echo "=================================="
echo ""

READY=true

# 1. Docker 설치 확인
echo -n "1. Docker 설치 확인... "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Docker가 설치되어 있지 않습니다${NC}"
    READY=false
fi

# 2. Docker Compose 설치 확인
echo -n "2. Docker Compose 설치 확인... "
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Docker Compose가 설치되어 있지 않습니다${NC}"
    READY=false
fi

# 3. .env 파일 확인
echo -n "3. .env 파일 존재 확인... "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ .env 파일이 없습니다${NC}"
    READY=false
fi

# 4. Turso 인증 정보 확인
echo -n "4. Turso 인증 정보 확인... "
if [ -f ".env" ] && grep -q "TURSO_DATABASE_URL" .env && grep -q "TURSO_AUTH_TOKEN" .env; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Turso 인증 정보가 .env에 없습니다${NC}"
    READY=false
fi

# 5. 워크플로우 파일 확인
echo -n "5. n8n 워크플로우 파일 확인... "
if [ -f "workflows/release-album-link.json" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ workflows/release-album-link.json 파일이 없습니다${NC}"
    READY=false
fi

# 6. 필수 디렉토리 확인
echo -n "6. 필수 디렉토리 확인... "
if [ -d "n8n_data" ] && [ -d "scripts" ] && [ -d "workflows" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}! 일부 디렉토리가 없습니다. 자동 생성합니다...${NC}"
    mkdir -p n8n_data scripts workflows
fi

# 7. 필수 파일 확인
echo -n "7. 필수 파일 확인... "
MISSING_FILES=""
[ ! -f "docker-compose.yml" ] && MISSING_FILES="${MISSING_FILES}docker-compose.yml "
[ ! -f "companion_api.py" ] && MISSING_FILES="${MISSING_FILES}companion_api.py "
[ ! -f "Dockerfile.companion-api" ] && MISSING_FILES="${MISSING_FILES}Dockerfile.companion-api "
[ ! -f "Dockerfile.collector" ] && MISSING_FILES="${MISSING_FILES}Dockerfile.collector "
[ ! -f "scripts/auto_collect_all.py" ] && MISSING_FILES="${MISSING_FILES}scripts/auto_collect_all.py "

if [ -z "$MISSING_FILES" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ 누락된 파일: $MISSING_FILES${NC}"
    READY=false
fi

# 8. Docker 데몬 실행 확인
echo -n "8. Docker 데몬 실행 확인... "
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Docker 데몬이 실행되고 있지 않습니다${NC}"
    READY=false
fi

echo ""
echo "=================================="

if [ "$READY" = true ]; then
    echo -e "${GREEN}✅ 모든 준비가 완료되었습니다!${NC}"
    echo ""
    echo "다음 명령어로 수집을 시작하세요:"
    echo -e "${YELLOW}  docker-compose up -d${NC}"
    echo ""
    echo "자세한 가이드는 START_COLLECTION.md를 참조하세요."
else
    echo -e "${RED}❌ 일부 항목이 준비되지 않았습니다.${NC}"
    echo ""
    echo "위의 체크 항목을 확인하고 해결한 후 다시 실행하세요."
    exit 1
fi

echo "=================================="
