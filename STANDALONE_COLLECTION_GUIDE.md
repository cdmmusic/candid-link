# 독립형 앨범 링크 수집 가이드

n8n 없이 Python만으로 앨범 링크를 수집하는 방법

## 시스템 구성

### 방법 1: 한국 플랫폼만 수집 (간단)
- **필요**: Python 3, libsql-experimental, requests
- **불필요**: Docker, n8n, Selenium
- **수집**: 멜론, 지니, 벅스, VIBE, FLO (5개)

### 방법 2: 한국 + 해외 플랫폼 수집 (추천)
- **필요**: Python 3 + Companion API (Selenium)
- **수집**: 한국 5개 + 해외 12개 (Spotify, Apple Music, YouTube 등)

---

## 설치 및 설정

### 1. Python 패키지 설치

```bash
pip3 install libsql-experimental requests
```

### 2. 환경 변수 설정

`.env` 파일에 Turso 인증 정보 필요:

```bash
TURSO_DATABASE_URL=libsql://album-links-cdmmusic.turso.io
TURSO_AUTH_TOKEN=your_auth_token_here
```

### 3. (선택) Companion API 실행

해외 플랫폼 수집을 원하면 Companion API 필요:

```bash
# Selenium Chrome 실행
docker run -d -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest

# Companion API 실행
export SELENIUM_HUB=http://localhost:4444
python3 companion_api.py
```

---

## 사용 방법

### 기본 실행

```bash
# 환경 변수 로드
source .env
export TURSO_DATABASE_URL TURSO_AUTH_TOKEN

# 1개 앨범 테스트
python3 collect_standalone.py 1

# 10개 앨범 수집
python3 collect_standalone.py 10

# 100개 앨범 수집
python3 collect_standalone.py 100

# 전체 앨범 수집 (5,089개)
python3 collect_standalone.py
```

### 실행 가능하게 만들기

```bash
chmod +x collect_standalone.py
./collect_standalone.py 10
```

---

## 작동 방식

### 1. 한국 플랫폼 검색

각 플랫폼의 API를 직접 호출:

- **멜론**: 웹 검색 URL (HTML 파싱 필요)
- **지니뮤직**: 웹 검색 URL (HTML 파싱 필요)
- **벅스**: 웹 검색 URL (HTML 파싱 필요)
- **VIBE**: Naver API 사용 (JSON 응답)
- **FLO**: 공개 API 사용 (JSON 응답)

### 2. 해외 플랫폼 검색

Companion.global을 통한 통합 검색:

1. Companion API에 앨범 정보 전송
2. Selenium으로 Companion.global 검색
3. 플랫폼 링크 추출 (Spotify, Apple Music, YouTube 등)
4. 앨범 커버 URL도 함께 수집

### 3. 데이터베이스 저장

- Turso (libSQL) 클라우드 데이터베이스
- 플랫폼별로 found=1 (찾음) / found=0 (못 찾음) 기록
- 중복 방지: 기존 레코드 삭제 후 삽입

---

## 진행 상황 추적

### 실시간 통계

10개마다 자동 출력:
- 성공/실패 개수
- 처리 속도 (albums/min)
- 예상 완료 시간 (ETA)

### 중단 후 재개

진행 상황이 `.collection_progress.txt`에 자동 저장됨:

```bash
# 중단 (Ctrl+C)
# 다시 실행하면 자동으로 이어서 진행
python3 collect_standalone.py
```

---

## 예상 소요 시간

### 테스트 결과

- **1개 앨범**: ~60초
  - 한국 플랫폼: ~15초
  - 해외 플랫폼: ~45초

### 전체 수집 예상

- **5,089개 앨범 × 60초 = 약 85시간 (3.5일)**

### 최적화 방법

1. **병렬 처리**: 여러 프로세스 동시 실행
2. **Companion API 없이**: 한국 플랫폼만 수집 (15초/앨범 → 21시간)
3. **Vercel Cron**: 서버 없이 자동 수집

---

## 출력 예시

```
============================================================
  Standalone Album Link Collector
  (No n8n Required)
============================================================

Turso Database: libsql://album-links-cdmmusic.turso.io...
Batch size: 100 albums

Fetching uncollected albums from Turso...
Found 100 albums to process

[1/100] 알레프 (ALEPH) - 기어코
  → Searching Korean platforms...
    [1/5] Melon... ✗
    [2/5] Genie... ✗
    [3/5] Bugs... ✗
    [4/5] VIBE... ✗
    [5/5] FLO... ✗
  → Searching Global platforms...
    Companion API: ✓ Found 9 platforms
  ✓ Success: KR 0/5, Global 9, Total 14 records saved

[2/100] Artist Name - Album Title
  → Searching Korean platforms...
    [1/5] Melon... ✓
    [2/5] Genie... ✓
    [3/5] Bugs... ✓
    [4/5] VIBE... ✓
    [5/5] FLO... ✓
  → Searching Global platforms...
    Companion API: ✓ Found 12 platforms
  ✓ Success: KR 5/5, Global 12, Total 17 records saved

--- Progress: 10/100 (10.0%) ---
Success: 10 | Failed: 0
Rate: 6.2 albums/min
ETA: 2.4 hours

============================================================
  Collection Complete
============================================================

Total albums processed: 100
Success: 98
Failed: 2
Total platforms found: 1,250
Duration: 1.7 hours
Average: 61.2s per album
```

---

## 문제 해결

### 1. Turso 인증 오류

```bash
Fatal error: Turso credentials not found in environment variables
```

**해결**:
```bash
source .env
export TURSO_DATABASE_URL TURSO_AUTH_TOKEN
```

### 2. Companion API 연결 실패

```
Companion API not available (is it running?)
```

**해결**:
- Companion API가 실행 중인지 확인
- 포트 5001이 사용 가능한지 확인
- 또는 해외 플랫폼 없이 실행 (검색 URL만 저장됨)

### 3. VIBE/FLO API 오류

```
VIBE error: Expecting value: line 1 column 1
```

**원인**: API 응답 형식 변경 또는 인증 문제

**임시 해결**: 해당 플랫폼은 found=0으로 기록됨

---

## 다음 단계

### 옵션 A: 로컬에서 계속 실행

```bash
# 밤새 실행
nohup python3 collect_standalone.py > collection.log 2>&1 &

# 진행 확인
tail -f collection.log
```

### 옵션 B: Vercel Cron으로 자동화

서버 없이 24시간 자동 수집:
- Vercel Cron Jobs (무료)
- 매시간 소량씩 처리
- 완전 자동화

### 옵션 C: 클라우드 서버 배포

- Oracle Cloud Free Tier (무료)
- AWS Lightsail ($3.50/월)
- DigitalOcean ($4/월)

---

## 성능 비교

| 방법 | 소요 시간 | 비용 | 자동화 |
|------|---------|------|--------|
| 로컬 실행 (한국만) | 21시간 | 무료 | ✗ |
| 로컬 실행 (전체) | 85시간 | 무료 | ✗ |
| Vercel Cron | 7일 | 무료 | ✓ |
| VPS 서버 | 85시간 | $4/월 | ✓ |
| Docker Compose (기존) | 14시간 | 무료 | ✗ |

---

## 결론

**추천 방식**:
1. **테스트**: `python3 collect_standalone.py 10` (10개만)
2. **소량 수집**: 로컬에서 100개씩 처리
3. **대량 수집**: VPS 서버 or Vercel Cron 자동화

**장점**:
- ✅ n8n 불필요
- ✅ Docker 불필요 (Companion API 제외)
- ✅ 진행 상황 추적
- ✅ 중단 후 재개 가능
- ✅ Vercel Cron으로 자동화 가능

**다음 작업**:
- [ ] 한국 플랫폼 HTML 파싱 구현 (멜론, 지니, 벅스)
- [ ] Vercel Cron 통합
- [ ] 앨범 커버 자동 업데이트
