#!/bin/bash

# Screen 세션 이름
SESSION_NAME="album_collection"

# 이미 실행중인 세션이 있는지 확인
if screen -list | grep -q "$SESSION_NAME"; then
    echo "⚠️  '$SESSION_NAME' 세션이 이미 실행 중입니다."
    echo ""
    echo "다시 접속하려면: screen -r $SESSION_NAME"
    echo "강제 종료하려면: screen -X -S $SESSION_NAME quit"
    exit 1
fi

echo "🚀 Screen 세션 '$SESSION_NAME'을 시작합니다..."
echo ""
echo "📌 Screen 세션 조작법:"
echo "   - 세션에서 나가기 (Detach): Ctrl+A 누른 후 D"
echo "   - 다시 접속: screen -r $SESSION_NAME"
echo "   - 세션 종료: screen -X -S $SESSION_NAME quit"
echo ""
echo "⏳ 3초 후 시작됩니다..."
sleep 3

# Screen 세션 시작하고 자동으로 스크립트 실행
screen -dmS "$SESSION_NAME" bash -c "
    cd /Users/choejibin/release-album-link

    export TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io'
    export TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA'
    export COMPANION_API_PORT=8001

    echo '==============================================='
    echo '🎵 앨범 링크 자동 수집 시작'
    echo '시작 시간: \$(date)'
    echo '==============================================='
    echo ''

    python3 collect_all_albums.py

    echo ''
    echo '==============================================='
    echo '✅ 수집 완료'
    echo '종료 시간: \$(date)'
    echo '==============================================='
    echo ''
    echo '⏸️  세션을 종료하려면 exit를 입력하세요.'

    # 완료 후 쉘 유지 (로그 확인 가능)
    exec bash
"

echo "✅ Screen 세션이 백그라운드에서 시작되었습니다!"
echo ""
echo "📊 세션에 접속하려면:"
echo "   screen -r $SESSION_NAME"
echo ""
echo "📋 실행 중인 세션 목록:"
screen -ls
