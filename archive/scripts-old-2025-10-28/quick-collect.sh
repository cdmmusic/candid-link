#!/bin/bash
# 빠른 링크 수집 스크립트
# 사용법: ./quick-collect.sh [앨범수]

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🎵 캔디드뮤직 링크 수집${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 환경 변수 로드
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} 환경 변수 로드 중..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}✗${NC} .env 파일이 없습니다"
    exit 1
fi

if [ -z "$TURSO_DATABASE_URL" ]; then
    echo -e "${RED}✗${NC} TURSO_DATABASE_URL 환경 변수 필요"
    exit 1
fi

echo -e "${GREEN}✓${NC} Turso DB: ${TURSO_DATABASE_URL:0:50}..."
echo ""

# Docker 서비스 확인
echo -e "${BLUE}🐳 Docker 서비스 확인...${NC}"
if ! docker ps --filter "name=album-links-companion-api" | grep -q "companion-api"; then
    echo -e "${YELLOW}⚠${NC}  Companion API 시작 중..."
    docker-compose up -d companion-api selenium-chrome
    echo -e "${YELLOW}⏳${NC} 초기화 대기 (20초)..."
    sleep 20
else
    echo -e "${GREEN}✓${NC} Companion API 실행 중"
fi
echo ""

# 수집 시작
BATCH_SIZE=${1:-10}
echo -e "${BLUE}📊 배치 크기: ${YELLOW}${BATCH_SIZE}개${NC} 앨범"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 수집 시작${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

python3 collect_n8n_style.py $BATCH_SIZE

echo ""
echo -e "${GREEN}✅ 완료!${NC}"
echo ""
echo -e "💡 다음 단계:"
echo -e "   더 수집: ${YELLOW}./quick-collect.sh 50${NC}"
echo -e "   정리: ${YELLOW}docker-compose down${NC}"
echo ""
