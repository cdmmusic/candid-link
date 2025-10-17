#!/bin/bash
# 자동 링크 수집 스크립트
# 사용법: ./auto_collect.sh [배치크기]
# 예시: ./auto_collect.sh 50  # 50개 앨범 수집

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 색상
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 로그 디렉토리
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# 로그 파일
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/auto_collect_$TIMESTAMP.log"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🤖 자동 링크 수집 시작${NC}"
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

# 배치 크기 (기본값: 20)
BATCH_SIZE=${1:-20}

echo -e "${BLUE}📊 수집 설정${NC}"
echo -e "   배치 크기: ${YELLOW}${BATCH_SIZE}개${NC} 앨범"
echo -e "   로그 파일: ${YELLOW}${LOG_FILE}${NC}"
echo ""

# 수집 시작
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 수집 실행${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Python 스크립트 실행 (stdout과 파일 모두 출력)
python3 collect_n8n_style.py $BATCH_SIZE 2>&1 | tee "$LOG_FILE"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 수집 완료!${NC}"
else
    echo -e "${RED}❌ 수집 실패 (Exit code: $EXIT_CODE)${NC}"
fi

echo ""
echo -e "💡 로그 파일: ${YELLOW}${LOG_FILE}${NC}"
echo ""
