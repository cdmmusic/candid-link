#!/bin/bash

# 배치 재수집 스크립트
# Usage: ./run_batch.sh 1    # 1번 배치 (0-99)
# Usage: ./run_batch.sh 2    # 2번 배치 (100-199)

if [ -z "$1" ]; then
    echo "Usage: ./run_batch.sh <batch_number>"
    echo "Example: ./run_batch.sh 1"
    exit 1
fi

BATCH_NUM=$1
BATCH_SIZE=100

echo "=========================================="
echo "  Batch $BATCH_NUM Collection"
echo "=========================================="
echo ""

# 1. CDMA 코드 조회
echo "Step 1: Getting CDMA codes for batch $BATCH_NUM..."
CDMA_CODES=$(TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io' \
TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA' \
python3 get_batch_cdma_codes.py $BATCH_NUM $BATCH_SIZE | tail -1)

if [ -z "$CDMA_CODES" ] || [ "$CDMA_CODES" == "# No more albums to process" ]; then
    echo "No albums to process for batch $BATCH_NUM"
    exit 0
fi

echo "Found codes: $(echo $CDMA_CODES | wc -w) albums"
echo ""

# 2. 수집 실행
echo "Step 2: Starting collection..."
TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io' \
TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA' \
python3 collect_from_db.py $CDMA_CODES

echo ""
echo "=========================================="
echo "  Batch $BATCH_NUM Complete"
echo "=========================================="
echo ""
echo "Run failure analysis:"
echo "  TURSO_DATABASE_URL='...' TURSO_AUTH_TOKEN='...' python3 analyze_failures.py"
