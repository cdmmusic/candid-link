#!/bin/bash

# 전체 자동 수집 스크립트
# 배치 2부터 끝까지 순차적으로 실행

BATCH_SIZE=100
START_BATCH=${1:-2}  # 기본값 2 (배치 1은 이미 완료)
END_BATCH=${2:-52}   # 기본값 52 (총 5103개 앨범 ÷ 100)

echo "=========================================="
echo "  전체 자동 수집 시작"
echo "=========================================="
echo ""
echo "시작 배치: $START_BATCH"
echo "종료 배치: $END_BATCH"
echo "배치 크기: $BATCH_SIZE"
echo ""
echo "예상 총 배치 수: $((END_BATCH - START_BATCH + 1))"
echo ""
echo "자동 수집 모드: 모든 배치를 연속 실행합니다."
echo ""

# 시작 시간 기록
TOTAL_START=$(date +%s)

# 성공/실패 카운터
SUCCESS_COUNT=0
FAIL_COUNT=0

for batch in $(seq $START_BATCH $END_BATCH); do
    echo ""
    echo "=========================================="
    echo "  배치 $batch / $END_BATCH 실행 중..."
    echo "=========================================="
    echo ""

    # 배치 실행
    if ./run_batch.sh $batch; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo "✓ 배치 $batch 성공"
    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "✗ 배치 $batch 실패 (계속 진행)"
    fi

    # 진행률 표시
    PROGRESS=$((batch - START_BATCH + 1))
    TOTAL=$((END_BATCH - START_BATCH + 1))
    PERCENT=$((PROGRESS * 100 / TOTAL))
    echo ""
    echo "진행률: $PROGRESS / $TOTAL ($PERCENT%)"
    echo "성공: $SUCCESS_COUNT | 실패: $FAIL_COUNT"
    echo ""

    # 배치 간 대기 (서버 부하 방지)
    if [ $batch -lt $END_BATCH ]; then
        echo "다음 배치까지 5초 대기..."
        sleep 5
    fi
done

# 종료 시간 및 총 소요 시간
TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - TOTAL_START))
HOURS=$((TOTAL_DURATION / 3600))
MINUTES=$(((TOTAL_DURATION % 3600) / 60))
SECONDS=$((TOTAL_DURATION % 60))

echo ""
echo "=========================================="
echo "  전체 수집 완료"
echo "=========================================="
echo ""
echo "총 배치 수: $((SUCCESS_COUNT + FAIL_COUNT))"
echo "성공: $SUCCESS_COUNT"
echo "실패: $FAIL_COUNT"
echo "총 소요 시간: ${HOURS}시간 ${MINUTES}분 ${SECONDS}초"
echo ""
echo "실패 추적 리포트 생성:"
echo "  TURSO_DATABASE_URL='...' TURSO_AUTH_TOKEN='...' python3 track_failures.py"
echo ""
