# Release Album Link Collection System

Companion.global 스마트 링크 자동 수집 시스템

## 프로젝트 개요

이 시스템은 앨범 메타데이터(CDMA 코드, 아티스트, 앨범명)를 사용하여 Companion.global에서 자동으로 글로벌 및 한국 음악 플랫폼 링크를 수집합니다.

## 주요 기능

- **CDMA 코드 기반 검색**: 정확한 앨범 식별을 위해 CDMA 코드로 검색
- **자동 로그인**: Companion.global에 자동 로그인
- **글로벌 플랫폼 링크 수집**: Spotify, Apple Music, Deezer, Anghami 등 12~13개 플랫폼
- **한국 플랫폼 링크 수집**: 멜론, 지니, VIBE, FLO 등 3~4개 플랫폼
- **SQLite 데이터베이스**: 수집된 링크를 `album_links.db`에 저장

## 시스템 구조

```
release-album-link/
├── api/
│   ├── companion_api.py      # Companion.global API (포트 5001)
│   ├── admin_api.py           # 관리자 API
│   ├── db_api.py              # 데이터베이스 API
│   ├── index.py               # 메인 API 라우터
│   └── web_server.py          # 웹 서버
├── collect_links.py           # 메인 수집 스크립트
├── album_links.db             # SQLite 데이터베이스
├── logs/                      # 로그 파일
├── archived/                  # 구버전/임시 파일 보관
│   └── old_scripts/
└── README.md                  # 이 문서
```

## 설치 및 요구사항

### 필수 패키지
```bash
pip install flask selenium requests beautifulsoup4
```

### Selenium Grid
Selenium Grid (Chrome/Firefox)가 `http://localhost:4444`에서 실행 중이어야 합니다.

```bash
# Selenium Grid 실행 예시
docker run -d -p 4444:4444 selenium/standalone-chrome
```

## 사용법

### 1. API 서버 시작
```bash
python api/companion_api.py
```
- 포트: `5001`
- API가 http://localhost:5001에서 실행됩니다.

### 2. 링크 수집 실행
```bash
python collect_links.py
```

수집 스크립트는:
1. `album_links.db`에서 CDMA 코드가 있는 앨범 읽기
2. 각 앨범에 대해 Companion API 호출 (`/search` 엔드포인트)
3. 수집된 링크를 데이터베이스에 저장
4. 진행 상황을 로그로 출력

### 3. 진행 상황 확인
```bash
# 데이터베이스 확인
sqlite3 album_links.db "SELECT COUNT(*) FROM album_platform_links WHERE companion_link IS NOT NULL"
```

## API 엔드포인트

### POST `/search`
앨범의 플랫폼 링크 검색

**요청 본문:**
```json
{
  "artist": "아티스트 이름",
  "album": "앨범 이름",
  "cdma": "CDMA00001"
}
```

**응답:**
```json
{
  "status": "success",
  "data": {
    "companion_link": "http://companion.global/catalog/platform/...",
    "platforms": {
      "spotify": "https://open.spotify.com/album/...",
      "apple_music": "https://music.apple.com/album/...",
      "deezer": "https://www.deezer.com/album/...",
      ...
    },
    "kr_platforms": {
      "melon": "https://www.melon.com/album/detail.htm?albumId=...",
      "genie": "https://www.genie.co.kr/detail/albumInfo?axnm=...",
      ...
    }
  },
  "debug": [...]
}
```

## 데이터베이스 스키마

### album_platform_links
```sql
CREATE TABLE album_platform_links (
    cdma_code TEXT NOT NULL,
    artist_ko TEXT,
    album_ko TEXT,
    platform_name TEXT NOT NULL,
    platform_url TEXT,
    companion_link TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 주요 변경 이력

### 2025-10-31
- **CDMA 코드 검색 구현**: 앨범 제목 대신 CDMA 코드로 검색하도록 변경
- **버그 수정**:
  - API에서 CDMA 코드 파라미터 추가 (`collect_links.py` line 112)
  - 검색 쿼리 로직 수정 (`api/companion_api.py` lines 561-566)
  - Python 캐시 및 포트 충돌 문제 해결
- **결과 개선**:
  - 이전: 0개 글로벌 플랫폼 (잘못된 검색 결과)
  - 현재: 12~13개 글로벌 플랫폼 (정확한 결과)

## 문제 해결

### API가 응답하지 않음
```bash
# 포트 5001이 사용 중인지 확인
netstat -ano | findstr :5001

# 프로세스 종료
taskkill /F /PID <프로세스_ID>

# API 재시작
python api/companion_api.py
```

### Python 캐시 문제
```bash
# 캐시 파일 삭제
find api -name "*.pyc" -delete
rm -rf api/__pycache__
```

### Selenium 연결 오류
```bash
# Selenium Grid 상태 확인
curl http://localhost:4444/status

# Grid 재시작
docker restart <selenium_container_id>
```

## 로그

로그 파일은 `logs/` 디렉토리에 저장됩니다:
- `collection_*.log`: 수집 프로세스 로그
- `companion_api_*.log`: API 서버 로그

## 주의사항

1. **CDMA 코드 필수**: 데이터베이스의 모든 앨범에 CDMA 코드가 있어야 합니다.
2. **Selenium Grid**: API 실행 전에 Selenium Grid가 실행 중이어야 합니다.
3. **네트워크**: Companion.global 접근을 위한 안정적인 인터넷 연결이 필요합니다.
4. **속도 제한**: 너무 많은 요청을 빠르게 보내지 않도록 주의하세요.

## 지원

문제가 발생하면 로그 파일을 확인하고 디버그 정보를 검토하세요.
