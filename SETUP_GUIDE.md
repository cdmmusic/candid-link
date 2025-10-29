# 캔디드뮤직 링크 서비스 - 설정 가이드

## 📊 현재 상태 (2025-10-28)

### 데이터베이스 현황
- **전체 앨범 수**: 5,103개
- **글로벌 링크 수집 현황**:
  - 시도한 앨범: 3,596개
  - 성공(찾은 앨범): 23,499개 플랫폼 링크
  - 실패(못 찾은 앨범): 41,835개 플랫폼 링크
  - 아직 시도 안 한 앨범: 1,610개

### 실패 기록
- 실패한 앨범들은 `album_platform_links` 테이블에 `found = 0`으로 저장됨
- `error_message` 컬럼에 실패 사유 기록
- 실패한 앨범은 재수집 대상에서 제외됨 (중복 시도 방지)

---

## 🛠️ 시스템 아키텍처

### 1. 데이터베이스 (SQLite)
- **파일**: `album_links.db`
- **주요 테이블**:
  - `albums`: 앨범 기본 정보 (artist_ko, album_ko, album_code, release_date 등)
  - `album_platform_links`: 플랫폼별 링크 정보
    - platform_type: 'korea' 또는 'global'
    - found: 1 (성공) / 0 (실패)
    - error_message: 실패 시 에러 메시지

### 2. 웹 서버
- **포트**: 5002
- **파일**: `admin_api.py`
- **기능**:
  - 홈페이지 (/)
  - TOP 100 (/top100)
  - 최신 앨범 (/latest)
  - 검색 (/search)
  - 앨범 상세 (/album/<artist>/<album>)
  - 공유 기능 (Open Graph 메타태그)

### 3. 수집 시스템
- **Companion API**: 글로벌 링크 수집용 (localhost:5001)
- **Selenium Hub**: Chromium 브라우저 (localhost:4444)
- **수집 스크립트**: `collect_all_global_links.py`

---

## 🚀 새 컴퓨터에서 시작하기

### 1단계: 필수 파일 복사
다음 파일들을 새 컴퓨터로 복사:
```
album_links.db              # 데이터베이스 (필수!)
admin_api.py                # 웹 서버
collect_all_global_links.py # 수집 스크립트
companion_api.py            # Companion API 서버
static/                     # CSS, JS 파일
templates/                  # HTML 템플릿
```

### 2단계: 환경 설정

#### Python 환경
```bash
python3 --version  # Python 3.10.4 권장

# 필수 패키지 설치
pip3 install flask requests libsql-experimental selenium
```

#### Docker (Selenium용)
```bash
# Selenium Chromium 컨테이너 실행
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  seleniarm/standalone-chromium:latest

# 또는 ARM Mac이 아닌 경우:
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  selenium/standalone-chrome:latest
```

### 3단계: 서버 실행

#### Companion API 실행 (터미널 1)
```bash
export COMPANION_API_PORT="5001"
python3 companion_api.py
```

#### 웹 서버 실행 (터미널 2)
```bash
python3 admin_api.py
# http://localhost:5002 에서 접속 가능
```

### 4단계: 글로벌 링크 수집 시작 (터미널 3)
```bash
chmod +x collect_all_global_links.py
python3 -u collect_all_global_links.py 2>&1 | tee /tmp/global_collection.log &

# 실시간 로그 확인
tail -f /tmp/global_collection.log
```

---

## 📝 수집 프로세스 설명

### 수집 로직
1. `albums` 테이블에서 모든 앨범 조회
2. 이미 수집 시도한 앨범은 건너뜀 (성공/실패 모두)
3. 남은 앨범에 대해 Companion API로 글로벌 링크 검색
4. 결과를 `album_platform_links` 테이블에 저장:
   - 성공: `found = 1`, 플랫폼별 링크 저장
   - 실패: `found = 0`, `error_message` 저장

### 수집 재개
- 프로세스가 중단되어도 데이터베이스에 진행 상황 저장됨
- 동일한 명령어로 재실행하면 중단된 지점부터 이어서 수집

### 진행 상황 확인
```bash
# 로그 파일 확인
tail -f /tmp/global_collection.log

# 또는 데이터베이스 직접 쿼리
sqlite3 album_links.db "SELECT COUNT(*) FROM album_platform_links WHERE platform_type='global'"
```

---

## 🔧 주요 스크립트

### collect_all_global_links.py
- 글로벌 링크가 없는 앨범만 수집
- 중복 시도 방지 (이미 시도한 앨범 건너뜀)
- 실패 시 에러 메시지 기록

### companion_api.py
- Companion.global API 래퍼
- Selenium으로 웹 스크래핑
- 포트 5001에서 실행

### admin_api.py
- Flask 웹 애플리케이션
- SQLite 데이터베이스 연동
- 포트 5002에서 실행

---

## 🎯 향후 작업 계획

### 1. 남은 수집 (우선순위: 높음)
- 아직 시도 안 한 앨범: **1,610개**
- 예상 소요 시간: 약 13-16시간 (앨범당 30초 가정)

### 2. 실패 앨범 재시도 (우선순위: 중간)
- 실패한 41,835개 플랫폼 링크 중 일부는 재시도 가능
- 실패 사유 분석 후 재수집 전략 수립 필요

### 3. 데이터 정제 (우선순위: 낮음)
- 중복 링크 제거
- 잘못된 링크 검증
- 플랫폼별 링크 품질 확인

### 4. 성능 최적화 (우선순위: 낮음)
- 병렬 수집 (현재는 순차 처리)
- API 요청 캐싱
- 데이터베이스 인덱스 최적화

---

## 🐛 문제 해결

### Selenium 연결 실패
```bash
# Docker 컨테이너 상태 확인
docker ps | grep selenium

# 컨테이너 재시작
docker restart selenium-standalone
```

### Companion API 응답 없음
```bash
# 프로세스 확인
lsof -i :5001

# API 재시작
pkill -f companion_api.py
python3 companion_api.py
```

### 웹 서버 포트 충돌
```bash
# 5002 포트 사용 프로세스 확인
lsof -i :5002

# 강제 종료
lsof -ti :5002 | xargs kill -9

# 서버 재시작
python3 admin_api.py
```

### 수집 중단 후 재시작
```bash
# 수집 프로세스 중단
pkill -f collect_all_global_links.py

# 다시 시작 (자동으로 이어서 진행)
python3 -u collect_all_global_links.py 2>&1 | tee /tmp/global_collection.log &
```

---

## 📊 데이터베이스 쿼리 예제

### 수집 진행률 확인
```sql
SELECT
    COUNT(DISTINCT a.artist_ko || '||' || a.album_ko) as total_albums,
    COUNT(DISTINCT CASE WHEN apl.found = 1 THEN apl.artist_ko || '||' || apl.album_ko END) as collected,
    COUNT(DISTINCT CASE WHEN apl.found = 0 THEN apl.artist_ko || '||' || apl.album_ko END) as failed,
    COUNT(DISTINCT CASE WHEN apl.artist_ko IS NULL THEN a.artist_ko || '||' || a.album_ko END) as remaining
FROM albums a
LEFT JOIN album_platform_links apl
    ON a.artist_ko = apl.artist_ko
    AND a.album_ko = apl.album_ko
    AND apl.platform_type = 'global';
```

### 실패한 앨범 목록 조회
```sql
SELECT DISTINCT artist_ko, album_ko, error_message, created_at
FROM album_platform_links
WHERE platform_type = 'global'
  AND found = 0
ORDER BY created_at DESC
LIMIT 50;
```

### 플랫폼별 링크 수 확인
```sql
SELECT platform_name, COUNT(*) as link_count
FROM album_platform_links
WHERE platform_type = 'global' AND found = 1
GROUP BY platform_name
ORDER BY link_count DESC;
```

---

## 💡 추가 정보

### 로그 파일 위치
- 글로벌 수집 로그: `/tmp/global_collection.log`
- 모니터링 스크립트: `/tmp/monitor_collection.sh` (있는 경우)

### 백업 권장사항
1. `album_links.db` 파일 정기 백업
2. 중요한 작업 전 스냅샷 생성
3. Git으로 코드 버전 관리

### 환경 변수
```bash
export COMPANION_API_PORT="5001"  # Companion API 포트
export TURSO_DATABASE_URL="..."   # Turso 클라우드 DB (선택사항)
export TURSO_AUTH_TOKEN="..."     # Turso 인증 토큰 (선택사항)
```

---

## ✅ 체크리스트

새 컴퓨터에서 시작할 때:
- [ ] `album_links.db` 파일 복사
- [ ] Python 3.10+ 설치
- [ ] 필수 패키지 설치 (`pip3 install ...`)
- [ ] Docker 설치 및 Selenium 컨테이너 실행
- [ ] Companion API 실행 (포트 5001)
- [ ] 웹 서버 실행 (포트 5002)
- [ ] 브라우저에서 http://localhost:5002 접속 확인
- [ ] 수집 스크립트 실행
- [ ] 로그 파일 확인

---

**작성일**: 2025-10-28
**버전**: 1.0
**문의**: 오류 제보는 카카오톡 채널로
