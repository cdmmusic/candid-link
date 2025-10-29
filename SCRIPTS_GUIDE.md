# 스크립트 가이드

## 🎯 현재 사용 중인 파일 (필수)

### 1. collect_global_resume.py ⭐
**용도**: Global + KR 통합 수집 (현재 실행 중)
**포트**: 없음 (API 클라이언트)
**의존성**: companion_api.py, Selenium Grid
**실행**: `python3 collect_global_resume.py`

**특징**:
- 최신 앨범부터 역순으로 수집
- 이미 수집된 앨범 자동 건너뛰기
- Global 13개 + KR 5개 플랫폼 동시 수집
- 실패 로그 자동 기록

**설정**:
```python
START_FROM_ALBUM = None  # None = 최신부터
COMPANION_API_URL = 'http://localhost:5001/search'
```

---

### 2. companion_api.py ⭐
**용도**: Selenium 기반 Global + KR 수집 API
**포트**: 5001
**의존성**: Selenium Grid (4444)
**실행**: `python3 companion_api.py`

**특징**:
- Flask API 서버
- Companion.global 자동 로그인/검색
- KR 5개 플랫폼 Selenium 수집
- 앨범 커버 자동 추출

**API 엔드포인트**:
```bash
# 헬스 체크
GET http://localhost:5001/health

# 앨범 검색
POST http://localhost:5001/search
{
  "artist": "아티스트명",
  "album": "앨범명",
  "upc": "CDMA코드"
}
```

---

## 📦 데이터베이스

### album_links.db ⭐
**용도**: 메인 데이터베이스
**경로**: `/Users/choejibin/release-album-link/album_links.db`
**크기**: ~45MB
**테이블**:
- `albums`: 5,103개 앨범 정보
- `album_platform_links`: 플랫폼 링크 (Global + KR)

---

## ⚠️ 사용하지 않는 파일 (참고용)

### collect_n8n_style.py
**용도**: 구 버전 수집 스크립트 (단일 앨범 테스트용)
**상태**: 사용 안 함 (collect_global_resume.py로 대체)
**특징**: n8n 스타일 단일 앨범 수집

### auto_collect.sh
**용도**: 자동 수집 셸 스크립트 (구 버전)
**상태**: 사용 안 함
**비고**: Python 스크립트로 대체됨

### deploy.sh
**용도**: 배포 스크립트
**상태**: 웹 앱 배포용 (수집과 무관)

---

## 🗂️ 디렉토리 구조

```
/Users/choejibin/release-album-link/
├── collect_global_resume.py    ⭐ 메인 수집 스크립트
├── companion_api.py            ⭐ API 서버
├── album_links.db              ⭐ 메인 DB
├── collection.log              ⭐ 수집 로그
├── failure_logs/               ⭐ 실패 로그 디렉토리
│   ├── kr_partial.txt          (KR 일부만 찾음)
│   ├── global_not_found.txt    (Global 없음)
│   └── api_timeout.txt         (API 타임아웃)
├── archive/                    (백업 파일)
├── templates/                  (웹 템플릿)
└── static/                     (웹 리소스)
```

---

## 🚀 빠른 시작 (새 세션)

### 1. 필수 서비스 확인
```bash
# Selenium Grid
curl -I http://localhost:4444

# Companion API
curl http://localhost:5001/health
```

### 2. 서비스 시작 (필요시)
```bash
# Selenium Grid
docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest

# Companion API
cd /Users/choejibin/release-album-link
nohup python3 companion_api.py > /tmp/companion_api.log 2>&1 &
```

### 3. 수집 시작
```bash
cd /Users/choejibin/release-album-link
nohup python3 collect_global_resume.py > collection.log 2>&1 &
```

### 4. 진행 확인
```bash
# 실시간 로그
tail -f collection.log

# 진행률
grep "진행률" collection.log | tail -5
```

---

## 🔧 설정 변경

### 시작 지점 변경
`collect_global_resume.py` 파일 수정:
```python
# 최신부터
START_FROM_ALBUM = None

# 특정 앨범부터
START_FROM_ALBUM = 'CDMA03000'
```

### API 타임아웃 변경
`companion_api.py` - 각 플랫폼별 `time.sleep()` 조정
`collect_global_resume.py` - `timeout=120` 조정

---

## ❌ 하지 말아야 할 것

1. **중복 실행 금지**: `collect_global_resume.py`를 여러 개 실행하면 DB 충돌
2. **DB 직접 수정 주의**: SQLite는 동시 쓰기 제한
3. **companion_api.py 중단 금지**: 수집 중 중단하면 타임아웃 발생
4. **Selenium Grid 재시작 주의**: 수집 중 재시작하면 현재 앨범 실패

---

## 📝 로그 파일 위치

| 로그 | 경로 |
|------|------|
| 수집 로그 | `/Users/choejibin/release-album-link/collection.log` |
| Companion API | `/tmp/companion_api.log` |
| 실패 로그 | `/Users/choejibin/release-album-link/failure_logs/*.txt` |

---

## 🆘 문제 해결

### "Connection refused" 에러
→ companion_api.py 또는 Selenium Grid가 실행 중이 아님

### 수집이 멈춤
→ `ps aux | grep collect_global` 확인 후 재시작 (자동으로 이어서 수집)

### API 타임아웃 계속 발생
→ companion_api.py 재시작, Selenium Grid 재시작

### KR 플랫폼 못 찾음
→ 정상 (일부 앨범은 특정 플랫폼에만 존재) - `kr_partial.txt` 확인
