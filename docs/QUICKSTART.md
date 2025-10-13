# 🚀 빠른 배포 가이드 (5분)

## 준비사항 확인

다음 도구들이 설치되어 있는지 확인하세요:
- [ ] Node.js & npm
- [ ] Git

---

## 배포 단계

### 옵션 A: 자동 배포 스크립트 (추천)

```bash
cd /Users/choejibin/release-album-link
./deploy.sh
```

스크립트가 자동으로:
1. Turso/Vercel CLI 설치 확인
2. Turso DB 생성 및 데이터 업로드
3. 환경 변수 설정
4. Vercel 배포

---

### 옵션 B: 수동 배포 (단계별)

#### 1. Turso CLI 설치
```bash
curl -sSfL https://get.tur.so/install.sh | bash
```

#### 2. Vercel CLI 설치
```bash
npm install -g vercel
```

#### 3. Turso 로그인 & DB 생성
```bash
# GitHub으로 로그인
turso auth login

# DB 생성
turso db create album-links

# 로컬 데이터 업로드
turso db upload album-links database/album_links.db

# 연결 정보 확인
turso db show album-links --url
turso db tokens create album-links
```

**중요**: URL과 Token을 복사해두세요!

#### 4. Vercel 배포
```bash
cd /Users/choejibin/release-album-link

# Vercel 로그인
vercel login

# 환경 변수 설정
vercel env add TURSO_DATABASE_URL
# 입력: libsql://album-links-[your-username].turso.io

vercel env add TURSO_AUTH_TOKEN
# 입력: eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...

# 프로덕션 배포
vercel --prod
```

#### 5. 배포 완료!
```
✅ Production: https://your-project.vercel.app
```

---

## 테스트

### API 테스트
```bash
# Health Check
curl https://your-project.vercel.app/health

# 앨범 목록
curl https://your-project.vercel.app/api/albums-with-links?page=1&limit=5
```

### 웹 UI 테스트
브라우저에서 접속:
```
https://your-project.vercel.app/
```

---

## 문제 해결

### Turso 업로드 느림
- 22MB 파일 업로드에 30초~1분 소요 (정상)
- 네트워크 연결 확인

### Vercel 배포 실패
```bash
# 로그 확인
vercel logs

# 환경 변수 확인
vercel env ls

# 재배포
vercel --prod --force
```

### libsql 모듈 오류
- requirements.txt 확인
- Vercel이 자동으로 설치함 (수동 설치 불필요)

---

## 비용

| 서비스 | 무료 한도 | 현재 사용량 | 여유 |
|--------|-----------|-------------|------|
| Vercel | 100GB/월 | ~1GB/월 | ✅ |
| Turso | 9GB 저장 | 22MB | ✅ |
| Turso | 500M rows | 5,093개 | ✅ |

**총 비용**: $0/월

---

## 다음 단계

배포 완료 후:
1. [ ] 커스텀 도메인 연결 (선택)
2. [ ] 배치 처리로 남은 앨범 수집
3. [ ] 성능 모니터링

---

**소요 시간**: 약 5-10분
**난이도**: ⭐⭐☆☆☆
