# 수집 작업 현황

## 🔄 진행 중인 작업

### 수집 프로세스 정보
- **시작 시간**: 2025-10-28 22:20:51
- **프로세스 ID**: 53197
- **로그 파일**: `/Users/choejibin/release-album-link/collection.log`
- **실행 명령**: `python3 collect_global_resume.py`

### 수집 대상
- **총 앨범**: 4,922개
- **시작 지점**: CDMA05110 (최신 앨범부터 역순)
- **현재 진행**: 약 10개 완료

### 수집 내용
- **Global 플랫폼**: 13개 (Apple Music, Spotify, Deezer 등)
- **KR 플랫폼**: 5개 (멜론, 벅스, 지니, FLO, VIBE)
- **앨범 커버**: Bugs에서 수집

## 📊 현재 상태 확인

### 진행 상황 확인
```bash
# 최근 30줄 보기
tail -30 collection.log

# 실시간 로그
tail -f collection.log

# 진행률 요약
grep "진행률" collection.log | tail -5
```

### 프로세스 확인
```bash
# 실행 중인지 확인
ps aux | grep collect_global_resume | grep -v grep

# Companion API 확인
ps aux | grep companion_api | grep -v grep
```

### 실패 로그 확인
```bash
# 실패 로그 목록
ls -lh failure_logs/

# KR 일부만 찾은 앨범
cat failure_logs/kr_partial.txt | tail -10

# Global 못 찾은 앨범
cat failure_logs/global_not_found.txt | tail -10
```

## 🛠️ 필수 서비스

### 1. Companion API (포트 5001)
```bash
# 상태 확인
curl http://localhost:5001/health

# 재시작 (필요시)
pkill -f companion_api.py
nohup python3 companion_api.py > /tmp/companion_api.log 2>&1 &
```

### 2. Selenium Grid (포트 4444)
```bash
# 상태 확인
curl -I http://localhost:4444

# 재시작 (필요시)
docker restart selenium-standalone
# 또는
docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest
```

## 🚨 문제 발생 시

### 수집 중단된 경우
1. 프로세스 확인
   ```bash
   ps aux | grep collect_global_resume
   ```

2. 로그 확인
   ```bash
   tail -100 collection.log
   ```

3. 재시작
   ```bash
   nohup python3 collect_global_resume.py > collection.log 2>&1 &
   ```
   - 이미 수집된 앨범은 자동으로 건너뜀
   - 중단된 지점부터 다시 시작

### API 타임아웃 많이 발생하는 경우
- Companion API 재시작
- Selenium Grid 재시작
- 정상: 간헐적 타임아웃은 무시됨 (자동으로 다음 앨범 진행)

## ⚙️ 설정 파일

### collect_global_resume.py
- **DB 경로**: `/Users/choejibin/release-album-link/album_links.db`
- **API URL**: `http://localhost:5001/search`
- **시작점**: `START_FROM_ALBUM = None` (None = 최신부터)
- **실패 로그**: `/Users/choejibin/release-album-link/failure_logs/`

### companion_api.py
- **포트**: 5001
- **Selenium Hub**: `http://localhost:4444`
- **타임아웃**: 각 앨범당 약 30-50초

## 📈 예상 소요 시간

- **앨범당**: 30-50초
- **총 4,922개**: 약 41-68시간
- **권장**: screen 또는 tmux 세션에서 실행

## 🔍 실패 로그 파일 설명

| 파일명 | 설명 | 조치 |
|--------|------|------|
| `kr_partial.txt` | KR 5개 중 일부만 찾음 | 수동 확인 필요 (아티스트명 오타 등) |
| `global_not_found.txt` | Global 플랫폼 없음 | companion.global에 등록되지 않은 앨범 |
| `api_timeout.txt` | API 타임아웃 (120초) | 정상 (자동 건너뛰기) |
| `catalog_not_found.txt` | Catalog에서 앨범 못 찾음 | CDMA 코드로 못 찾은 경우 |

## ✅ 수집 완료 후

1. 최종 결과 확인
   ```bash
   tail -100 collection.log
   ```

2. 실패 로그 확인
   ```bash
   ls -lh failure_logs/
   ```

3. DB 통계 확인
   ```bash
   sqlite3 album_links.db "
   SELECT
     COUNT(DISTINCT artist_ko || album_ko) as total_albums,
     SUM(CASE WHEN found = 1 AND platform_type = 'global' THEN 1 ELSE 0 END) as global_links,
     SUM(CASE WHEN found = 1 AND platform_type = 'kr' THEN 1 ELSE 0 END) as kr_links
   FROM album_platform_links
   "
   ```

4. kr_partial.txt 수동 처리
   - 아티스트명 변경 확인
   - 플랫폼별 수동 검색
   - DB 직접 업데이트
