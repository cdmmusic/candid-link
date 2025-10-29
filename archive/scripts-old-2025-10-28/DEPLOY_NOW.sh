#!/bin/bash

###############################################################################
# NAS 배포 자동화 스크립트 - 로컬에서 실행
# 사용법: bash DEPLOY_NOW.sh
###############################################################################

set -e

NAS_IP="192.168.0.33"
NAS_USER="candidmusic"
NAS_PORT="22"
DEPLOY_DIR="/volume1/docker/album-links"

echo "======================================================================"
echo "  NAS 자동 배포 시작"
echo "======================================================================"
echo ""
echo "NAS 주소: $NAS_IP"
echo "사용자: $NAS_USER"
echo "배포 경로: $DEPLOY_DIR"
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 파일 전송
echo -e "${YELLOW}[1/6] nas-deploy.tar.gz 파일 전송 중...${NC}"
scp -P $NAS_PORT nas-deploy.tar.gz $NAS_USER@$NAS_IP:/volume1/docker/
echo -e "${GREEN}✓ 파일 전송 완료${NC}"
echo ""

# 2. NAS에서 배포 실행
echo -e "${YELLOW}[2/6] NAS에 SSH 접속하여 배포 시작...${NC}"

ssh -p $NAS_PORT $NAS_USER@$NAS_IP << 'ENDSSH'
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DEPLOY_DIR="/volume1/docker/album-links"

echo -e "${YELLOW}[3/6] 디렉토리 설정...${NC}"
cd /volume1/docker
mkdir -p album-links
cd album-links

echo -e "${YELLOW}[4/6] 압축 해제...${NC}"
tar -xzf ../nas-deploy.tar.gz
echo -e "${GREEN}✓ 압축 해제 완료${NC}"
ls -la

echo ""
echo -e "${YELLOW}[5/6] 자동 설정 실행...${NC}"
bash setup-nas.sh

echo ""
echo -e "${YELLOW}[6/6] Docker Compose 시작...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}======================================================================"
echo "  배포 완료!"
echo "======================================================================${NC}"
echo ""
echo "서비스 상태:"
docker-compose ps

echo ""
echo "접속 정보:"
echo "  n8n: http://192.168.0.33:8678"
echo "  계정: admin / album-links-2025"
echo ""

ENDSSH

echo ""
echo -e "${GREEN}======================================================================"
echo "  로컬 배포 스크립트 완료!"
echo "======================================================================${NC}"
echo ""
echo "다음 명령어로 로그 확인:"
echo "  ssh candidmusic@192.168.0.33"
echo "  cd /volume1/docker/album-links"
echo "  docker-compose logs -f"
echo ""
