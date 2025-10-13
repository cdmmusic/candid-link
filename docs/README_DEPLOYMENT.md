# 🚀 음악 플랫폼 링크 통합 시스템 - 배포 가이드

## 📋 개요

17개 음악 플랫폼의 앨범 링크를 통합 제공하는 서비스를 **Vercel + Turso**로 무료 배포합니다.

**배포 시간**: 5-10분
**비용**: $0/월 (영구 무료)
**난이도**: ⭐⭐☆☆☆

---

## ✨ 특징

- **100% 무료**: Vercel + Turso 무료 플랜 사용
- **글로벌 CDN**: 전 세계 어디서나 빠른 접속
- **자동 HTTPS**: 보안 연결 자동 설정
- **무제한 확장**: 서버리스 아키텍처
- **간편 배포**: 한 줄 명령어로 배포 완료

---

## 🏗️ 아키텍처

```
사용자 브라우저
    ↓
Vercel (글로벌 CDN + Serverless)
    ↓
Turso (libSQL Database)
    ↓
17개 플랫폼 링크 데이터
```

---

## 🎯 배포 옵션

### 옵션 1: 자동 스크립트 (추천)

```bash
cd /Users/choejibin/release-album-link
./deploy.sh
```

**자동으로 처리됨**:
1. ✅ Turso/Vercel CLI 확인
2. ✅ Turso DB 생성
3. ✅ 로컬 데이터 업로드 (22MB)
4. ✅ 환경 변수 설정
5. ✅ Vercel 배포

### 옵션 2: 빠른 수동 배포 (5분)

**상세 가이드**: `QUICKSTART.md` 참고

```bash
# 1. CLI 설치
curl -sSfL https://get.tur.so/install.sh | bash
npm install -g vercel

# 2. 로그인
turso auth login
vercel login

# 3. DB 생성 및 업로드
turso db create album-links
turso db upload album-links database/album_links.db

# 4. 환경 변수 설정
turso db show album-links --url
turso db tokens create album-links
vercel env add TURSO_DATABASE_URL
vercel env add TURSO_AUTH_TOKEN

# 5. 배포
vercel --prod
```

### 옵션 3: 상세 가이드

**전체 문서**: `DEPLOYMENT_GUIDE.md` 참고

---

## 📊 비용 분석

| 서비스 | 무료 한도 | 현재 사용 | 비용 |
|--------|-----------|----------|------|
| Vercel | 100GB/월 | ~1GB/월 | $0 |
| Turso | 9GB, 500M rows | 22MB, 5K | $0 |
| **합계** | | | **$0/월** |

**트래픽 예상**:
- 월 100만 요청: ✅ 무료
- 5,093개 앨범: ✅ 무료
- 글로벌 접속: ✅ 무료

---

## 🔧 기술 스택

### 프론트엔드
- HTML5, CSS3, Vanilla JavaScript
- 반응형 디자인 (모바일 최적화)
- 무한 스크롤, 실시간 검색

### 백엔드
- Python 3.x
- Flask 3.0
- Vercel Serverless Functions

### 데이터베이스
- Turso (libSQL)
- SQLite 호환
- 글로벌 복제

### 인프라
- Vercel Edge Network
- 자동 HTTPS
- GitHub 연동 (CI/CD)

---

## 📂 프로젝트 구조

```
release-album-link/
├── api/
│   └── index.py              # Vercel Serverless Function
├── database/
│   └── album_links.db        # SQLite DB (22MB, 5,093 앨범)
├── vercel.json              # Vercel 설정
├── requirements.txt         # Python 의존성
├── deploy.sh                # 자동 배포 스크립트
├── QUICKSTART.md            # 5분 빠른 가이드
├── DEPLOYMENT_GUIDE.md      # 상세 가이드
└── DEPLOYMENT_SUMMARY.md    # 배포 준비 요약
```

---

## ✅ 배포 후 확인

### 1. Health Check
```bash
curl https://your-project.vercel.app/health
```

**응답**:
```json
{
  "status": "ok",
  "service": "album-links-api",
  "version": "2.0.0",
  "database": "turso"
}
```

### 2. API 테스트
```bash
curl https://your-project.vercel.app/api/albums-with-links?page=1&limit=5
```

### 3. 웹 UI 접속
```bash
open https://your-project.vercel.app/
```

---

## 🎓 다음 단계

### 1단계: 커스텀 도메인 (선택)
Vercel 대시보드에서 도메인 연결:
```
example.com → your-project.vercel.app
```

### 2단계: 남은 앨범 링크 수집
```bash
# n8n 워크플로우 엔드포인트 변경
# 로컬: http://localhost:5002
# 배포: https://your-project.vercel.app

# 배치 처리 실행
n8n start
python3 batch_process_resume.py
```

### 3단계: 모니터링
Vercel 대시보드에서 확인:
- 요청 수
- 응답 시간
- 에러율

---

## 🆘 문제 해결

### Q1: `turso: command not found`
```bash
curl -sSfL https://get.tur.so/install.sh | bash
source ~/.bashrc  # 또는 ~/.zshrc
```

### Q2: `vercel: command not found`
```bash
npm install -g vercel
```

### Q3: Turso 업로드 느림
- 22MB → 30초~1분 소요 (정상)
- 네트워크 연결 확인

### Q4: Vercel 배포 실패
```bash
vercel logs           # 로그 확인
vercel --prod --force # 재배포
```

### Q5: 환경 변수 오류
```bash
vercel env ls                         # 확인
vercel env rm TURSO_DATABASE_URL      # 삭제
vercel env add TURSO_DATABASE_URL     # 재등록
```

---

## 📚 관련 문서

| 문서 | 설명 | 대상 |
|------|------|------|
| `QUICKSTART.md` | 5분 빠른 배포 | 초보자 |
| `DEPLOYMENT_GUIDE.md` | 단계별 상세 가이드 | 모든 사용자 |
| `DEPLOYMENT_SUMMARY.md` | 배포 준비 요약 | 확인용 |
| `README_BATCH.md` | 배치 처리 가이드 | 데이터 수집 |
| `PROJECT_STATUS.md` | 프로젝트 현황 | 전체 현황 |

---

## 🌟 지원 플랫폼 (17개)

### 국내 (5개)
- Melon, Genie, Bugs, FLO, VIBE

### 글로벌 (12개)
- Apple Music, Spotify, YouTube, Amazon Music
- Deezer, Tidal, KKBox, Anghami
- Pandora, LINE Music, AWA, Moov, QQ MUSIC

---

## 📞 지원

### 공식 문서
- **Vercel**: https://vercel.com/docs
- **Turso**: https://docs.turso.tech
- **Flask**: https://flask.palletsprojects.com

### 커뮤니티
- **Vercel Discord**: https://vercel.com/discord
- **Turso Discord**: https://discord.gg/turso

---

## 🎉 준비 완료!

모든 준비가 끝났습니다. 이제 배포하세요:

```bash
./deploy.sh
```

또는 빠른 가이드를 확인하세요:

```bash
cat QUICKSTART.md
```

---

**작성일**: 2025-10-13
**버전**: 2.0.0
**프로젝트**: 음악 플랫폼 링크 통합 시스템
**비용**: $0/월 (영구 무료)
