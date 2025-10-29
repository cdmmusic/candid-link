# 🔄 재수집 가이드

> **작성일**: 2025-10-28
> **목적**: 다른 컴퓨터에서 재수집을 바로 실행할 수 있도록 단계별 가이드 제공

---

## 📋 목차
1. [빠른 시작](#빠른-시작)
2. [단계별 가이드](#단계별-가이드)
3. [재수집 시나리오](#재수집-시나리오)
4. [트러블슈팅](#트러블슈팅)

---

## 빠른 시작

### 전체 재수집 (원스텝)

```bash
cd /Users/choejibin/release-album-link

# 1. 환경 변수 설정
export TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io'
export TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA'
export COMPANION_USERNAME='candidmusic'
export COMPANION_PASSWORD='dkfvfk2-%!#'
export SELENIUM_HUB="http://localhost:4444"

# 2. Docker & Selenium 시작
open -a Docker
sleep 10
docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest
sleep 5

# 3. Companion API 시작
python3 companion_api.py &
sleep 3

# 4. 수집 시작
./auto_collect.sh 1 52
```

---

## 단계별 가이드

### 1단계: 환경 준비

#### 1.1 프로젝트 디렉토리로 이동
```bash
cd /Users/choejibin/release-album-link
```

#### 1.2 환경 변수 설정
```bash
# Turso 데이터베이스
export TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io'
export TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA'

# Companion.global 로그인 (FLUXUS 계정)
export COMPANION_USERNAME='candidmusic'
export COMPANION_PASSWORD='dkfvfk2-%!#'  # ⚠️ 백슬래시 없음!

# Selenium Grid
export SELENIUM_HUB="http://localhost:4444"
export COMPANION_API_PORT=5001
```

**⚠️ 주의**: 비밀번호에 백슬래시(`\`)를 넣지 마세요!
- ❌ `'dkfvfk2-\%\!#'`
- ✅ `'dkfvfk2-%!#'`

#### 1.3 Python 패키지 확인
```bash
pip install -r requirements.txt

# 또는 개별 설치
pip install libsql-experimental selenium flask requests
```

---

### 2단계: Docker & Selenium Grid 시작

#### 2.1 Docker 실행
```bash
open -a Docker
sleep 10  # Docker가 완전히 시작될 때까지 대기
```

#### 2.2 Selenium Grid 컨테이너 시작

**ARM Mac (M1/M2/M3)**:
```bash
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  seleniarm/standalone-chromium:latest
```

**Intel Mac**:
```bash
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  selenium/standalone-chrome:latest
```

#### 2.3 Selenium 상태 확인
```bash
sleep 5
curl http://localhost:4444/status

# 응답 예시:
# {"value":{"ready":true,"message":"Selenium Grid ready."}}
```

**문제 발생 시**:
```bash
# 컨테이너 재시작
docker stop selenium-standalone
docker rm selenium-standalone
# 다시 위의 docker run 명령 실행
```

---

### 3단계: Companion API 시작

#### 3.1 API 실행
```bash
python3 companion_api.py &
sleep 3
```

#### 3.2 API 상태 확인
```bash
curl http://localhost:5001/health

# 응답 예시:
# {"status":"ok","service":"companion-api","selenium_hub":"http://localhost:4444"}
```

**로그 확인**:
```bash
# API 프로세스 확인
ps aux | grep companion_api

# 로그 확인 (백그라운드 실행 시)
tail -f /tmp/companion_api.log  # (로그 파일이 있는 경우)
```

---

### 4단계: 재수집 실행

#### 옵션 A: 전체 자동 수집 (추천)
```bash
./auto_collect.sh 1 52

# 설명:
# - 배치 1~52 (CDMA00001 ~ CDMA05200)
# - 각 배치 100개 앨범
# - 예상 시간: 8~12시간
```

#### 옵션 B: 특정 배치만 수집
```bash
# 배치 10만 수집 (CDMA00901 ~ CDMA01000)
python3 collect_n8n_style.py 10

# 배치 20~30 수집
./auto_collect.sh 20 30
```

#### 옵션 C: 단일 앨범 테스트
```bash
# CDMA00001 앨범만 수집 (테스트용)
python3 collect_n8n_style.py 1
```

---

### 5단계: 진행 상황 모니터링

#### 5.1 실시간 로그 확인
```bash
# 수집 스크립트 출력 확인
tail -f auto_collect.log  # (자동화 스크립트가 로그를 생성하는 경우)
```

#### 5.2 데이터베이스 통계 확인
```bash
# 국내 플랫폼 성공률
sqlite3 album_links.db "
SELECT
    platform_name,
    COUNT(*) as total,
    SUM(found) as found,
    ROUND(SUM(found) * 100.0 / COUNT(*), 1) as rate
FROM album_platform_links
WHERE platform_type = 'kr'
GROUP BY platform_name
"

# 글로벌 플랫폼 성공률
sqlite3 album_links.db "
SELECT
    platform_name,
    COUNT(*) as total,
    SUM(found) as found,
    ROUND(SUM(found) * 100.0 / COUNT(*), 1) as rate
FROM album_platform_links
WHERE platform_type = 'global'
GROUP BY platform_name
LIMIT 15
"
```

#### 5.3 실패 앨범 분석
```bash
# 국내 플랫폼 실패 분석
python3 track_failures.py

# 결과 파일:
# - failures_kr_complete.txt (0/5)
# - failures_kr_partial.txt (1-4/5)

# 글로벌 플랫폼 실패 분석
python3 track_global_failures.py

# 결과 파일:
# - failures_global_complete.txt (0/12)
# - failures_global_partial.txt (1-11/12)
```

---

## 재수집 시나리오

### 시나리오 1: 국내 플랫폼만 재수집

**현재 상태**: 국내 25% → 목표 70%+

```bash
# 1. 환경 설정 (Turso만 필요, Selenium 불필요)
export TURSO_DATABASE_URL='...'
export TURSO_AUTH_TOKEN='...'

# 2. 수집 (글로벌 수집 비활성화)
# collect_n8n_style.py 수정 필요:
# - collect_global_links() 함수 호출 부분 주석 처리
# 또는
# - 환경 변수로 글로벌 수집 스킵 가능하도록 개선

python3 collect_n8n_style.py 1
```

**TODO**: 국내 플랫폼만 수집하는 옵션 추가 필요

### 시나리오 2: 글로벌 플랫폼만 재수집

**현재 상태**: 글로벌 34% → 목표 60%+

```bash
# 1. 플랫폼 코드 통일 (필수!)
sqlite3 album_links.db < fix_platform_codes.sql

# 2. Docker & Selenium 시작
open -a Docker
sleep 10
docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest

# 3. Companion API 시작
export SELENIUM_HUB="http://localhost:4444"
export COMPANION_USERNAME='candidmusic'
export COMPANION_PASSWORD='dkfvfk2-%!#'
python3 companion_api.py &

# 4. 글로벌 링크만 수집
python3 collect_global_links.py  # 전용 스크립트 사용
# 또는
python3 collect_n8n_style.py 1  # 국내 수집 스킵 옵션 추가
```

### 시나리오 3: 실패 앨범만 재수집

```bash
# 1. 실패 목록 생성
python3 track_failures.py
python3 track_global_failures.py

# 2. 실패 앨범 CDMA 코드 추출
cat failures_kr_complete.txt | cut -d' ' -f1 > failed_cdma_codes.txt

# 3. 재수집 (스크립트 작성 필요)
# TODO: failed_cdma_codes.txt 읽어서 재수집하는 스크립트
```

**TODO**: 실패 앨범만 재수집하는 스크립트 작성

### 시나리오 4: 특정 CDMA 범위 재수집

```bash
# CDMA03000 ~ CDMA03500만 재수집
./auto_collect.sh 30 35

# 배치 번호 계산:
# CDMA03000 = 배치 30 (3000 / 100)
# CDMA03500 = 배치 35 (3500 / 100)
```

---

## 트러블슈팅

### 문제 1: Companion API 응답 없음

**증상**:
```bash
curl: (7) Failed to connect to localhost port 5001
```

**해결**:
```bash
# API 프로세스 확인
ps aux | grep companion_api

# API 재시작
pkill -f companion_api
sleep 2
export SELENIUM_HUB="http://localhost:4444"
python3 companion_api.py &

# 로그 확인
tail -f /tmp/companion_api.log
```

---

### 문제 2: Selenium Grid 연결 실패

**증상**:
```
selenium.common.exceptions.WebDriverException:
Failed to connect to http://localhost:4444
```

**해결**:
```bash
# Selenium 컨테이너 확인
docker ps | grep selenium

# 없으면 재시작
docker stop selenium-standalone 2>/dev/null
docker rm selenium-standalone 2>/dev/null

docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  seleniarm/standalone-chromium:latest

# 상태 확인
curl http://localhost:4444/status
```

---

### 문제 3: Companion.global 로그인 실패

**증상**:
```
[Companion API] After login, URL: http://companion.global/login?error=true
```

**원인**: 비밀번호에 백슬래시가 들어갔을 가능성

**해결**:
```bash
# 환경 변수 재설정 (백슬래시 없이!)
export COMPANION_PASSWORD='dkfvfk2-%!#'

# API 재시작
pkill -f companion_api
python3 companion_api.py &

# 테스트
curl -X POST http://localhost:5001/search \
  -H 'Content-Type: application/json' \
  -d '{"artist":"이요운","album":"욕심이겠지만","upc":"CDMA05088"}'
```

---

### 문제 4: Turso 읽기/쓰기 제한

**증상**:
```
Error: Operation was blocked: SQL read operations are forbidden
```

**원인**: Turso 무료 플랜 제한

**해결 방법 A: 로컬 DB 사용**
```bash
# collect_n8n_style.py 수정
# Turso 연결 부분을 sqlite3 연결로 변경

import sqlite3
conn = sqlite3.connect('album_links.db')
```

**해결 방법 B: Turso 플랜 업그레이드**
- https://turso.tech/pricing
- Starter 플랜: $29/월 (더 많은 읽기/쓰기)

---

### 문제 5: "element not interactable" 오류

**증상**:
```
selenium.common.exceptions.ElementNotInteractableException
```

**원인**: Companion.global 페이지 구조 변경 또는 빈 아티스트명

**해결**:
```bash
# companion_api.py 코드 확인
# 빈 문자열 체크 로직이 있는지 확인 (Line 202, 256)

# 로그 확인
tail -f /tmp/companion_api.log

# API 재시작
pkill -f companion_api
python3 companion_api.py &
```

---

### 문제 6: 플랫폼 코드 불일치

**증상**:
- Companion API는 링크를 찾음
- 하지만 DB에 저장되지 않음

**원인**: 플랫폼 코드가 혼재 (`spo` vs `spotify`)

**해결**:
```bash
# 플랫폼 코드 통일
sqlite3 album_links.db < fix_platform_codes.sql

# 또는 수동으로
sqlite3 album_links.db "
UPDATE album_platform_links
SET platform_code = 'spo'
WHERE platform_code = 'spotify' AND platform_type = 'global'
"

# 다른 플랫폼도 동일하게 처리
```

---

### 문제 7: Docker가 시작되지 않음

**증상**:
```
Cannot connect to the Docker daemon
```

**해결**:
```bash
# Docker 앱 실행
open -a Docker

# 또는 시스템 재시작
sudo systemctl start docker  # Linux
# Mac: Docker Desktop 재설치
```

---

### 문제 8: 포트 이미 사용 중

**증상**:
```
Error: port 4444 is already allocated
Error: port 5001 is already in use
```

**해결**:
```bash
# 포트 4444 확인 (Selenium)
lsof -i :4444
docker stop selenium-standalone
docker rm selenium-standalone

# 포트 5001 확인 (Companion API)
lsof -i :5001
pkill -f companion_api
# 또는
kill -9 [PID]
```

---

## 성능 최적화

### 병렬 수집

현재는 순차 수집이지만, 병렬 처리로 속도 향상 가능:

```bash
# TODO: 병렬 수집 스크립트 작성
# - 배치 1~10: 프로세스 1
# - 배치 11~20: 프로세스 2
# - 배치 21~30: 프로세스 3
```

### Selenium Grid 스케일링

```bash
# 여러 개의 Selenium 노드 실행
docker run -d --name selenium-node-1 -p 5555:4444 ...
docker run -d --name selenium-node-2 -p 5556:4444 ...

# 로드 밸런싱 필요
```

---

## 체크리스트

재수집 시작 전 확인:

- [ ] Docker 실행됨
- [ ] Selenium Grid 컨테이너 실행 중 (`docker ps`)
- [ ] Selenium 상태 확인 (`curl http://localhost:4444/status`)
- [ ] Companion API 실행 중 (`ps aux | grep companion_api`)
- [ ] API 헬스체크 통과 (`curl http://localhost:5001/health`)
- [ ] 환경 변수 설정 (`echo $TURSO_DATABASE_URL`)
- [ ] 비밀번호 정확함 (`echo $COMPANION_PASSWORD` → `dkfvfk2-%!#`)
- [ ] 디스크 공간 충분 (최소 5GB)
- [ ] 네트워크 연결 안정적

---

## 예상 소요 시간

| 작업 | 앨범 수 | 예상 시간 |
|------|---------|----------|
| 전체 재수집 (KR + Global) | 5,103개 | 8~12시간 |
| 국내 플랫폼만 | 5,103개 | 3~5시간 |
| 글로벌 플랫폼만 | 5,103개 | 5~8시간 |
| 실패 앨범 재수집 (KR) | 3,410개 | 2~4시간 |
| 실패 앨범 재수집 (Global) | 3,284개 | 3~5시간 |
| 단일 배치 (100개) | 100개 | 10~15분 |

**참고**:
- 네트워크 속도와 API 응답 시간에 따라 변동
- Selenium 안정성에 따라 재시작 필요할 수 있음

---

## 다음 문서

- [PROJECT_STATUS.md](PROJECT_STATUS.md) - 현재 프로젝트 상태
- [GLOBAL_LINK_COLLECTION_GUIDE.md](GLOBAL_LINK_COLLECTION_GUIDE.md) - 글로벌 수집 상세
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - 초기 환경 설정

---

**작성자**: Claude Code
**최종 업데이트**: 2025-10-28
**문의**: 이 가이드로 재수집이 안 되면 PROJECT_STATUS.md 참고
