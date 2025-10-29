#!/bin/bash

# Vercel + Turso 배포 스크립트

set -e

echo "🚀 Vercel + Turso 배포 시작..."
echo ""

# 1. Turso CLI 확인
echo "1️⃣ Turso CLI 확인 중..."
if ! command -v turso &> /dev/null; then
    echo "❌ Turso CLI가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  curl -sSfL https://get.tur.so/install.sh | bash"
    echo ""
    exit 1
fi
echo "✅ Turso CLI 설치됨"
echo ""

# 2. Vercel CLI 확인
echo "2️⃣ Vercel CLI 확인 중..."
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI가 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  npm install -g vercel"
    echo ""
    exit 1
fi
echo "✅ Vercel CLI 설치됨"
echo ""

# 3. Turso 로그인 확인
echo "3️⃣ Turso 로그인 확인 중..."
if ! turso db list &> /dev/null; then
    echo "⚠️  Turso 로그인이 필요합니다."
    echo ""
    echo "다음 명령어를 실행하세요:"
    echo "  turso auth login"
    echo ""
    exit 1
fi
echo "✅ Turso 로그인 확인됨"
echo ""

# 4. Turso DB 생성 확인
echo "4️⃣ Turso 데이터베이스 확인 중..."
DB_NAME="album-links"

if turso db show $DB_NAME &> /dev/null; then
    echo "ℹ️  데이터베이스 '$DB_NAME'가 이미 존재합니다."
    read -p "기존 DB를 사용하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 배포 중단"
        exit 1
    fi
else
    echo "📦 데이터베이스 '$DB_NAME' 생성 중..."
    turso db create $DB_NAME
    echo "✅ 데이터베이스 생성 완료"
fi
echo ""

# 5. 로컬 DB 업로드
echo "5️⃣ 로컬 SQLite DB를 Turso로 업로드 중..."
if [ -f "database/album_links.db" ]; then
    echo "📤 업로드 중... (22MB, 약 30초 소요)"
    turso db upload $DB_NAME database/album_links.db
    echo "✅ 업로드 완료"
else
    echo "⚠️  로컬 DB 파일을 찾을 수 없습니다: database/album_links.db"
    echo "계속하시겠습니까? (기존 Turso DB 사용)"
    read -p "(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# 6. Turso 연결 정보 가져오기
echo "6️⃣ Turso 연결 정보 확인 중..."
TURSO_URL=$(turso db show $DB_NAME --url)
echo "📝 Database URL: $TURSO_URL"
echo ""

# 7. Turso 토큰 생성
echo "7️⃣ Turso 인증 토큰 생성 중..."
TURSO_TOKEN=$(turso db tokens create $DB_NAME)
echo "✅ 토큰 생성 완료"
echo ""

# 8. Vercel 환경 변수 설정
echo "8️⃣ Vercel 환경 변수 설정 중..."
echo "TURSO_DATABASE_URL=$TURSO_URL"
echo "TURSO_AUTH_TOKEN=***"
echo ""

# .env.production 파일 생성
cat > .env.production << EOF
TURSO_DATABASE_URL=$TURSO_URL
TURSO_AUTH_TOKEN=$TURSO_TOKEN
EOF
echo "✅ .env.production 파일 생성 완료"
echo ""

# 9. Vercel에 환경 변수 추가
echo "9️⃣ Vercel에 환경 변수 등록 중..."
echo "⚠️  다음 명령어를 수동으로 실행하세요:"
echo ""
echo "vercel env add TURSO_DATABASE_URL"
echo "입력값: $TURSO_URL"
echo ""
echo "vercel env add TURSO_AUTH_TOKEN"
echo "입력값: $TURSO_TOKEN"
echo ""
read -p "환경 변수 등록을 완료했습니까? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 배포 중단"
    exit 1
fi
echo ""

# 10. Vercel 배포
echo "🔟 Vercel 배포 시작..."
echo ""
vercel --prod
echo ""

echo "✅ 배포 완료!"
echo ""
echo "📊 배포 정보:"
echo "  - 프론트엔드: Vercel"
echo "  - 데이터베이스: Turso (libSQL)"
echo "  - 비용: $0/월"
echo ""
echo "🔗 배포 URL은 위의 출력을 확인하세요."
echo ""
