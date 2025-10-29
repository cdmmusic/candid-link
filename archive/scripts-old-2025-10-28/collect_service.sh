#!/bin/bash

# 환경 변수 설정
export TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io'
export TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA'
export COMPANION_API_PORT=8001

# 작업 디렉토리
cd /Users/choejibin/release-album-link

# 무한 루프로 수집 실행
while true; do
    echo "$(date): Starting collection..."

    # DB에서 앨범 ID 가져오기 (예시)
    # 실제로는 DB 쿼리 결과를 사용
    python3 collect_from_db.py

    # 실패 시 대기 후 재시작
    if [ $? -ne 0 ]; then
        echo "$(date): Collection failed. Retrying in 60 seconds..."
        sleep 60
    else
        echo "$(date): Collection completed successfully."
        # 성공 시에도 다음 수집까지 대기 (예: 1시간)
        sleep 3600
    fi
done
