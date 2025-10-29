# 🤖 다른 컴퓨터/Claude 세션에 전달할 프롬프트

> **작성일**: 2025-10-28
> **목적**: 새로운 Claude 세션이나 다른 컴퓨터에서 즉시 상황을 파악하고 작업 시작

---

## 📋 복사해서 붙여넣을 프롬프트

```
안녕하세요! Release Album Link 프로젝트에 참여하게 되었습니다.

이 프로젝트는 5,103개 앨범의 음악 스트리밍 플랫폼 링크를
수집하는 시스템입니다.

다음 3가지 문서를 먼저 읽어주세요:

1. PROJECT_STATUS.md - 현재 프로젝트 상태
2. RECOLLECTION_GUIDE.md - 재수집 가이드
3. FILE_STRUCTURE.md - 파일 구조

위 문서들을 읽은 후, 현재 상황을 요약해주시고
다음 작업을 제안해주세요.
```

---

## 🎯 빠른 상황 파악용 프롬프트

### 옵션 1: 전체 상황 파악
```
프로젝트 폴더: /Users/choejibin/release-album-link

다음 파일들을 읽고 현재 상황을 파악해주세요:
- PROJECT_STATUS.md
- RECOLLECTION_GUIDE.md
- FILE_STRUCTURE.md

그리고 다음을 알려주세요:
1. 현재 수집 진행률
2. 다음 우선순위 작업
3. 즉시 실행 가능한 명령어
```

### 옵션 2: 재수집 바로 시작
```
프로젝트 폴더: /Users/choejibin/release-album-link

재수집을 시작하고 싶습니다.
RECOLLECTION_GUIDE.md를 읽고 단계별로 안내해주세요.

현재 환경:
- OS: macOS (ARM/M1/M2/M3)
- Docker: 설치됨
- Python: 3.x
```

### 옵션 3: 특정 문제 해결
```
프로젝트 폴더: /Users/choejibin/release-album-link

다음 문제가 발생했습니다:
[문제 설명]

RECOLLECTION_GUIDE.md의 트러블슈팅 섹션을 참고해서
해결 방법을 알려주세요.
```

---

## 📚 핵심 문서 3종 세트

### 1️⃣ PROJECT_STATUS.md
**내용**:
- 현재 데이터베이스 상태 (5,103개 앨범)
- 글로벌 링크 수집 진행 중 (CDMA03418부터 역순)
- 시스템 아키텍처 (Turso, Selenium, Flask)
- 주요 스크립트 사용법

**언제 읽나**: 프로젝트에 처음 참여할 때

---

### 2️⃣ RECOLLECTION_GUIDE.md (13KB)
**내용**:
- 재수집 단계별 가이드
- 환경 설정 (Docker, Selenium, Companion API)
- 4가지 재수집 시나리오
- 8가지 트러블슈팅 케이스
- 예상 소요 시간

**언제 읽나**: 재수집을 시작하기 전에

---

### 3️⃣ FILE_STRUCTURE.md (9KB)
**내용**:
- 프로젝트 파일 구조 (24개 파일)
- 각 스크립트 용도
- Archive로 정리된 파일 (20개)
- 삭제하면 안 되는 파일 목록

**언제 읽나**: 파일이 너무 많아서 헷갈릴 때

---

## 🚀 즉시 실행 가능한 명령어

### 상황 파악
```bash
cd /Users/choejibin/release-album-link

# 현재 상태 확인
cat PROJECT_STATUS.md | head -50

# 수집 통계 확인
sqlite3 album_links.db "
SELECT
    '국내 완료' as type, COUNT(*) as cnt
FROM (
    SELECT artist_ko, album_ko
    FROM album_platform_links
    WHERE platform_type='kr' AND found=1
    GROUP BY artist_ko, album_ko
    HAVING COUNT(*)=5
)
UNION ALL
SELECT
    '글로벌 완료', COUNT(*)
FROM (
    SELECT artist_ko, album_ko
    FROM album_platform_links
    WHERE platform_type='global' AND found=1
    GROUP BY artist_ko, album_ko
    HAVING COUNT(*)>=12
)"
```

### 재수집 시작
```bash
cd /Users/choejibin/release-album-link

# 환경 변수 설정
export TURSO_DATABASE_URL='libsql://album-links-cdmmusic.turso.io'
export TURSO_AUTH_TOKEN='eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjMyOTAsImlkIjoiNGZhNDgwYzYtYzE2NS00YjU2LTlmNGItNjkyMTIxNmNlZmJmIiwicmlkIjoiMzUxMmUxNDUtODAzOS00ZjY1LTg5MWMtM2EyNjE5Yjg1YWRiIn0.cBDJFjEUNO4ePA6WcRhfuoKSJ5NAYhNnb4qWVRXd6yQxbmpP5eNtpEbQs0M17gLG6LuHxoRrP8cjmtCXR1Z5BA'
export COMPANION_USERNAME='candidmusic'
export COMPANION_PASSWORD='dkfvfk2-%!#'
export SELENIUM_HUB="http://localhost:4444"

# Docker 시작
open -a Docker
sleep 10

# Selenium Grid 시작
docker run -d --name selenium-standalone \
  -p 4444:4444 \
  --shm-size=2g \
  seleniarm/standalone-chromium:latest

# Companion API 시작
python3 companion_api.py &
sleep 3

# 수집 시작
./auto_collect.sh 1 52
```

---

## ⚠️ 중요 주의사항

### 1. 비밀번호 백슬래시 문제
```bash
# ❌ 잘못된 비밀번호 (백슬래시 들어감)
export COMPANION_PASSWORD='dkfvfk2-\%\!#'

# ✅ 올바른 비밀번호 (백슬래시 없음)
export COMPANION_PASSWORD='dkfvfk2-%!#'
```

### 2. 글로벌 검색 방식
- CDMA 코드로 검색 (예: CDMA00001)
- 검색 결과가 영문명으로 나와도 정상
- 예: "욕심이겠지만" → "Greed" (정상)

### 3. Turso DB 제한
- 현재 읽기가 차단될 수 있음 (무료 플랜)
- 로컬 DB (album_links.db) 사용 권장

### 4. 메인 스크립트
- **collect_n8n_style.py**: 메인 수집 스크립트
- **companion_api.py**: Flask API (Selenium)
- **auto_collect.sh**: 배치 자동화

---

## 📊 현재 상태 요약 (2025-10-28)

```
총 앨범: 5,103개 (CDMA00001 ~ CDMA05110)
마지막 수집: 2025-10-28 04:56:11

국내 플랫폼 (5개):
  ✅ 완료: 1,276개 (25.0%)
  🟨 부분: 417개 (8.2%)
  ❌ 미수집: 3,410개 (66.8%)

글로벌 플랫폼 (13개):
  ✅ 완료: 1,739개 (34.1%)
  🟨 부분: 80개 (1.6%)
  ❌ 미수집: 3,284개 (64.3%)

우선순위:
1. 국내 플랫폼 재수집 (3,410개) - 8~12시간
2. 플랫폼 코드 통일 (fix_platform_codes.sql)
3. 글로벌 플랫폼 재수집 (3,284개) - 5~8시간
```

---

## 🎯 작업 시나리오별 프롬프트

### 시나리오 1: 국내 플랫폼만 재수집
```
국내 플랫폼 링크를 재수집하고 싶습니다.
현재 25% 완료 상태이고, 3,410개 앨범이 미수집 상태입니다.

RECOLLECTION_GUIDE.md의 "시나리오 1: 국내 플랫폼만 재수집"을
참고해서 단계별로 안내해주세요.
```

### 시나리오 2: 글로벌 플랫폼만 재수집
```
글로벌 플랫폼 링크를 재수집하고 싶습니다.
현재 34% 완료 상태이고, 3,284개 앨범이 미수집 상태입니다.

먼저 fix_platform_codes.sql을 실행해서 플랫폼 코드를
통일해야 한다고 들었습니다.

RECOLLECTION_GUIDE.md의 "시나리오 2: 글로벌 플랫폼만 재수집"을
참고해서 단계별로 안내해주세요.
```

### 시나리오 3: 실패 앨범 분석
```
수집 실패한 앨범들을 분석하고 싶습니다.

track_failures.py와 track_global_failures.py를 실행해서
실패 목록을 생성하고, 실패 원인을 분석해주세요.
```

### 시나리오 4: 문서만 업데이트
```
코드나 수집은 건드리지 않고, 문서만 최신 상태로
업데이트하고 싶습니다.

PROJECT_STATUS.md의 통계를 최신 DB 상태로 갱신해주세요.
```

---

## 🔍 문제 해결 프롬프트

### Companion API 응답 없음
```
Companion API가 응답하지 않습니다.
curl http://localhost:5001/health 했을 때
"Connection refused" 에러가 납니다.

RECOLLECTION_GUIDE.md의 "문제 1: Companion API 응답 없음"을
참고해서 해결 방법을 알려주세요.
```

### Selenium Grid 연결 실패
```
Selenium Grid에 연결할 수 없습니다.
"Failed to connect to http://localhost:4444" 에러가 납니다.

RECOLLECTION_GUIDE.md의 "문제 2: Selenium Grid 연결 실패"를
참고해서 해결 방법을 알려주세요.
```

### 로그인 실패
```
Companion.global 로그인이 실패합니다.
URL에 "?error=true"가 붙어서 나옵니다.

RECOLLECTION_GUIDE.md의 "문제 3: Companion.global 로그인 실패"를
참고해서 해결 방법을 알려주세요.
```

---

## 📁 중요 파일 위치

```
/Users/choejibin/release-album-link/
├── PROJECT_STATUS.md          # ⭐ 필수: 현재 상황
├── RECOLLECTION_GUIDE.md      # ⭐ 필수: 재수집 방법
├── FILE_STRUCTURE.md          # ⭐ 필수: 파일 구조
├── HANDOVER.md                # 이 문서
│
├── collect_n8n_style.py       # 메인 수집 스크립트
├── companion_api.py           # Flask API (Selenium)
├── auto_collect.sh            # 배치 자동화
├── album_links.db             # SQLite DB (27MB)
│
└── archive/                   # 과거 파일 (무시 가능)
```

---

## 🤝 인계 체크리스트

다음 사항을 확인하고 새로운 세션에 전달하세요:

- [ ] PROJECT_STATUS.md 읽음
- [ ] RECOLLECTION_GUIDE.md 읽음
- [ ] FILE_STRUCTURE.md 읽음
- [ ] 현재 수집 진행률 파악 (국내 25%, 글로벌 34%)
- [ ] 우선순위 작업 파악 (국내 재수집 > 글로벌 재수집)
- [ ] 환경 변수 (.env) 위치 확인
- [ ] Docker 설치 확인
- [ ] Python 3.x 설치 확인
- [ ] 메인 스크립트 3개 파악 (collect_n8n_style.py, companion_api.py, auto_collect.sh)

---

## 💡 유용한 팁

### 빠른 통계 조회
```bash
# 국내 플랫폼 성공률
sqlite3 album_links.db "
SELECT platform_name, COUNT(*) as total, SUM(found) as found,
       ROUND(SUM(found)*100.0/COUNT(*),1) as rate
FROM album_platform_links WHERE platform_type='kr'
GROUP BY platform_name"

# 글로벌 플랫폼 성공률 (상위 10개)
sqlite3 album_links.db "
SELECT platform_name, COUNT(*) as total, SUM(found) as found,
       ROUND(SUM(found)*100.0/COUNT(*),1) as rate
FROM album_platform_links WHERE platform_type='global'
GROUP BY platform_name LIMIT 10"
```

### 서비스 상태 확인
```bash
# Docker 실행 중?
docker ps | grep selenium

# Companion API 실행 중?
ps aux | grep companion_api

# 포트 확인
lsof -i :4444  # Selenium Grid
lsof -i :5001  # Companion API
```

### 로그 확인
```bash
# 최근 수집 로그 (DB 타임스탬프)
sqlite3 album_links.db "
SELECT created_at, artist_ko, album_ko, platform_name, found
FROM album_platform_links
ORDER BY created_at DESC LIMIT 20"
```

---

## 🎓 학습 리소스

### 시스템 이해하기
1. **데이터베이스 구조**: PROJECT_STATUS.md → "데이터베이스 구조" 섹션
2. **수집 방식**: PROJECT_STATUS.md → "수집 방식" 섹션
3. **아키텍처**: PROJECT_STATUS.md → "시스템 아키텍처" 섹션

### 실습하기
1. **단일 앨범 테스트**: `python3 collect_n8n_style.py 1`
2. **실패 분석**: `python3 track_failures.py`
3. **API 테스트**: `curl http://localhost:5001/health`

---

## 📞 문제 발생 시

1. **RECOLLECTION_GUIDE.md** 트러블슈팅 섹션 확인
2. **FILE_STRUCTURE.md**에서 관련 스크립트 찾기
3. **PROJECT_STATUS.md**에서 시스템 구조 확인
4. 위 3가지 문서로 해결 안 되면 새로운 분석 시작

---

## 🎉 마지막 한 마디

**이 3가지 문서만 읽으면 됩니다:**
1. PROJECT_STATUS.md - 현재 뭐가 어떻게 되어있나?
2. RECOLLECTION_GUIDE.md - 어떻게 재수집하나?
3. FILE_STRUCTURE.md - 어떤 파일이 뭐하는 건가?

**나머지는 필요할 때 찾아보세요!**

---

**작성자**: Claude Code
**최종 업데이트**: 2025-10-28
**다음 Claude에게**: 위 프롬프트를 복사해서 시작하세요!

---

## 🔥 최신 업데이트 (2025-10-28)

### 글로벌 링크 수집 진행 중

**현재 스크립트**: `collect_global_resume.py`

**실행 중인 수집**:
- 시작점: CDMA03418 (Soh'uds - Uncharted Sea)
- 방향: CDMA03418 → CDMA00001 (역순)
- 남은 앨범: 3,240개
- 로그: `/tmp/global_collection.log`
- 실패 로그: `failure_logs/` 폴더

**수집 재개 방법**:
```bash
# 현재 진행 확인
tail -f /tmp/global_collection.log

# 프로세스 확인
ps aux | grep collect_global_resume

# 수집 재시작 (로그 이어쓰기)
python3 collect_global_resume.py >> /tmp/global_collection.log 2>&1 &

# 실패 로그 확인
ls -lh failure_logs/
cat failure_logs/smart_link_500_error.txt
```

**실패 로깅 시스템**:
- `failure_logs/catalog_not_found.txt` - 카탈로그에서 앨범 못 찾음
- `failure_logs/smart_link_missing.txt` - 스마트 링크 없음
- `failure_logs/smart_link_500_error.txt` - companion.global 서버 오류
- `failure_logs/smart_link_no_platforms.txt` - 플랫폼 리스트 비어있음
- `failure_logs/api_timeout.txt` - API 타임아웃 (120초)
- `failure_logs/api_failed.txt` - API 응답 실패
- `failure_logs/api_exception.txt` - 예외 발생

**주의사항**:
- Companion API는 **동시 요청 불가** (singleton WebDriver 사용)
- 타임아웃: 120초 (companion.global이 느림)
- 로그 append 모드: `>>` 사용해야 이전 로그 보존

**서비스 상태 확인**:
```bash
# Selenium Grid
curl -s http://localhost:4444/status | python3 -m json.tool

# Companion API
curl -s http://localhost:5001/health

# 서비스 재시작 필요시
docker restart selenium-standalone
python3 companion_api.py > /tmp/companion_api.log 2>&1 &
```


**collect_global_resume.py 핵심 로직**:
```python
# 설정
START_FROM_ALBUM = 'CDMA03418'  # 이 앨범부터 시작

# 쿼리
WHERE album_code <= 'CDMA03418'  # 이 코드 이하만
ORDER BY album_code DESC          # 큰 번호 → 작은 번호

# 타임아웃
timeout=120  # companion.global이 느림

# 로그
log_failure(failure_type, album, error_msg)  # 실시간 실패 기록
```

**다음 세션에서 수집 재개하려면**:
1. 로그에서 마지막 성공한 CDMA 코드 확인
2. `START_FROM_ALBUM`을 그 다음 코드로 변경
3. 실행: `python3 collect_global_resume.py >> /tmp/global_collection.log 2>&1 &`

