# 자동화 프로세스 가이드

## 핵심 원칙

### 1. 데이터베이스 중심 아키텍처
- **엑셀 파일(발매앨범DB.xlsx)**: 데이터베이스 임포트 용도로만 사용
- **모든 자동화**: 데이터베이스에서 직접 조회하여 실행
- **CDMA 코드**: 앨범의 고유 식별자로 사용

### 2. 데이터 흐름
```
발매앨범DB.xlsx
    ↓ (1회성 임포트)
albums 테이블 (Turso)
    ↓ (자동화가 조회)
링크 수집 프로세스
    ↓
album_platform_links 테이블 (Turso)
```

---

## 데이터베이스 구조

### albums 테이블
```sql
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_code TEXT UNIQUE NOT NULL,        -- CDMA 코드 (예: CDMA05070)
    artist_ko TEXT NOT NULL,                -- 아티스트명
    artist_en TEXT,                         -- 영문 아티스트명
    album_ko TEXT NOT NULL,                 -- 앨범명
    album_en TEXT,                          -- 영문 앨범명
    release_date TEXT,                      -- 발매일 (YYYY-MM-DD)
    album_type TEXT,                        -- 앨범 타입
    label TEXT,                             -- 레이블/기획사
    distributor TEXT,                       -- 유통사
    genre TEXT,                             -- 장르
    uci TEXT,                               -- UCI
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### album_platform_links 테이블
```sql
CREATE TABLE album_platform_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_ko TEXT NOT NULL,
    artist_en TEXT,
    album_ko TEXT NOT NULL,
    album_en TEXT,
    platform_type TEXT,                     -- 'kr' or 'global'
    platform_id TEXT,                       -- 한국 플랫폼 ID
    platform_name TEXT,                     -- 플랫폼 이름
    platform_url TEXT,                      -- 플랫폼 링크
    platform_code TEXT,                     -- 글로벌 플랫폼 코드
    album_id TEXT,                          -- 플랫폼별 앨범 ID
    upc TEXT,                               -- UPC 코드
    found INTEGER DEFAULT 0,                -- 찾았는지 여부 (0/1)
    status TEXT,                            -- 상태
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    album_cover_url TEXT,                   -- 앨범 커버 URL
    release_date TEXT                       -- 발매일
);
```

---

## 자동화 스크립트

### 1. 엑셀 데이터 임포트 (1회성)

```bash
# 발매앨범DB.xlsx → albums 테이블
python3 import_albums_from_excel.py
```

**용도**:
- 초기 데이터 셋업
- 새 앨범 추가 시

**실행 시점**:
- 프로젝트 초기 설정 시
- 엑셀 파일이 업데이트되었을 때

### 2. CDMA 코드로 링크 수집

```bash
# 특정 CDMA 코드 리스트로 수집
python3 collect_from_db.py CDMA05070 CDMA05073 CDMA05074 ...
```

**동작 방식**:
1. albums 테이블에서 CDMA 코드로 앨범 정보 조회
2. 한국/글로벌 플랫폼에서 링크 검색
3. album_platform_links 테이블에 저장

### 3. 배치 자동 수집

```bash
# 아직 수집되지 않은 앨범 10개 수집
./auto_collect.sh 10

# 50개 수집
./auto_collect.sh 50
```

**동작 방식**:
1. albums 테이블에서 미수집 앨범 조회
   ```sql
   SELECT * FROM albums
   WHERE album_code NOT IN (
       SELECT DISTINCT artist_ko || '|||' || album_ko
       FROM album_platform_links
   )
   LIMIT 10
   ```
2. 각 앨범에 대해 링크 수집 실행
3. 결과를 album_platform_links에 저장

---

## 사용 시나리오

### 시나리오 1: 새 앨범 10개 추가
```bash
# 1. 엑셀 파일에 10개 앨범 추가
# 2. 데이터베이스에 임포트
python3 import_albums_from_excel.py

# 3. 새 앨범만 수집
./auto_collect.sh 10
```

### 시나리오 2: 특정 CDMA 코드로 수집
```bash
# 데이터베이스에서 직접 조회하여 수집
python3 collect_from_db.py CDMA05070 CDMA05073 CDMA05074
```

### 시나리오 3: 전체 미수집 앨범 수집
```bash
# 모든 미수집 앨범 수집 (시간이 오래 걸림)
./auto_collect.sh
```

---

## 데이터 업데이트 정책

### albums 테이블
- **업데이트 방법**: `import_albums_from_excel.py` 재실행
- **충돌 처리**: `INSERT OR REPLACE` 사용 (CDMA 코드 기준)
- **업데이트 시점**:
  - 새 앨범 발매 시
  - 앨범 정보 수정 시

### album_platform_links 테이블
- **업데이트 방법**: 수집 스크립트 재실행
- **충돌 처리**: 기존 레코드 삭제 후 새로 삽입
- **업데이트 시점**:
  - 플랫폼 링크 변경 시
  - 새 플랫폼 추가 시

---

## 환경 변수

### 필수
```bash
TURSO_DATABASE_URL=libsql://album-links-cdmmusic.turso.io
TURSO_AUTH_TOKEN=your_token_here
```

### 선택 (Companion API 사용 시)
```bash
COMPANION_API_PORT=8001
SELENIUM_HUB=http://localhost:4444
```

---

## 데이터베이스 조회 예시

### 1. CDMA 코드로 앨범 찾기
```sql
SELECT * FROM albums WHERE album_code = 'CDMA05070';
```

### 2. 아직 수집되지 않은 앨범
```sql
SELECT * FROM albums
WHERE album_code NOT IN (
    SELECT DISTINCT artist_ko || '|||' || album_ko
    FROM album_platform_links
)
LIMIT 10;
```

### 3. 특정 날짜 이후 발매 앨범
```sql
SELECT * FROM albums
WHERE release_date >= '2025-10-01'
ORDER BY release_date DESC;
```

### 4. 특정 아티스트의 앨범
```sql
SELECT * FROM albums
WHERE artist_ko LIKE '%김재흥%'
ORDER BY release_date DESC;
```

---

## 문제 해결

### 1. albums 테이블이 없음
```bash
# 임포트 스크립트 실행 (테이블 자동 생성)
python3 import_albums_from_excel.py
```

### 2. CDMA 코드를 찾을 수 없음
```bash
# 데이터베이스 확인
python3 -c "
import libsql_experimental as libsql
conn = libsql.connect('libsql://...', auth_token='...')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM albums')
print(f'Total albums: {cursor.fetchone()[0]}')
"
```

### 3. 엑셀 파일과 DB 동기화
```bash
# 엑셀 파일을 수정한 후
python3 import_albums_from_excel.py

# 변경된 앨범만 다시 수집하려면
python3 collect_from_db.py [CDMA코드들...]
```

---

## 모범 사례

### DO ✅
- albums 테이블에서 앨범 정보 조회
- CDMA 코드를 앨범 식별자로 사용
- 데이터베이스 중심 자동화
- 엑셀 파일은 임포트용으로만 사용

### DON'T ❌
- 자동화 스크립트에서 엑셀 파일 직접 읽기
- 엑셀 파일에 의존하는 로직 작성
- 데이터베이스 없이 엑셀로만 작업

---

## 성능 최적화

### 1. 인덱스 활용
```sql
-- CDMA 코드 검색 최적화
CREATE INDEX IF NOT EXISTS idx_album_code ON albums(album_code);

-- 발매일 필터링 최적화
CREATE INDEX IF NOT EXISTS idx_release_date ON albums(release_date);
```

### 2. 배치 크기 조절
```bash
# 작은 배치 (빠른 피드백)
./auto_collect.sh 5

# 큰 배치 (효율적)
./auto_collect.sh 100
```

### 3. 병렬 처리
```bash
# 여러 터미널에서 동시 실행 (다른 CDMA 코드)
python3 collect_from_db.py CDMA05070 CDMA05073 &
python3 collect_from_db.py CDMA05074 CDMA05075 &
```

---

## 다음 단계

1. ✅ albums 테이블 생성 및 데이터 임포트
2. ✅ CDMA 코드 기반 수집 스크립트 작성
3. ⏳ 자동화 프로세스 테스트
4. ⏳ 문서화 및 배포

---

## 참고 문서

- [STANDALONE_COLLECTION_GUIDE.md](./STANDALONE_COLLECTION_GUIDE.md) - 기존 수집 시스템
- [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) - 프로젝트 구조
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 배포 가이드
