# 앨범 배치 처리 가이드

## 현재 상황
- **총 앨범**: 5,093개
- **처리 완료**: 10개
- **남은 작업**: 5,083개

## 사용 방법

### 1. 중단/재개 가능한 배치 처리 (권장)

```bash
python3 batch_process_resume.py
```

**특징:**
- ✅ 언제든 중단 가능 (Ctrl+C)
- ✅ 중단한 곳부터 다시 시작
- ✅ 진행 상황 자동 저장 (`batch_progress.json`)
- ✅ 실패한 앨범 별도 기록 (`batch_failed.json`)

**사용 예시:**
```bash
# 첫 실행: 100개 처리
python3 batch_process_resume.py
# 입력: 100 (배치 크기)
# 입력: 2 (대기 시간)

# 중단 (Ctrl+C)

# 재실행: 이어서 처리
python3 batch_process_resume.py
# 질문: 이어서 처리? y
```

### 2. 기존 자동 처리 스크립트

```bash
python3 auto_process_albums.py
```

## 권장 전략

### 옵션 A: 여러 세션으로 나누기 (안전)
```bash
# 세션 1: 100개 처리
python3 batch_process_resume.py
# 입력: 100

# 컴퓨터 종료 가능

# 세션 2: 다음 100개 처리
python3 batch_process_resume.py
# 입력: 100

# ... 반복 (약 50회)
```

**예상 시간:**
- 100개: ~3-10분 (성공률에 따라)
- 1000개: ~30분-2시간
- 5000개: ~3-10시간

### 옵션 B: 한 번에 대량 처리
```bash
python3 batch_process_resume.py
# 입력: 5083 (전체)
```

## 주의사항

1. **n8n 서버 실행 필수**
   ```bash
   n8n start
   ```

2. **네트워크 안정성**
   - 외부 API 호출이 많으므로 안정적인 인터넷 필요

3. **실패 처리**
   - 실패한 앨범은 `batch_failed.json`에 기록됨
   - 나중에 수동으로 재처리 가능

## 진행 상황 파일

### `batch_progress.json`
```json
{
  "processed": ["artist1|||album1", "artist2|||album2"],
  "last_index": 100,
  "total_success": 85,
  "total_failed": 15
}
```

### `batch_failed.json`
```json
[
  {
    "artist": "아티스트명",
    "album": "앨범명",
    "error": "Timeout",
    "timestamp": "2025-10-13T21:30:00"
  }
]
```

## 처리 완료 후

1. **데이터베이스 확인**
   ```bash
   python3 -c "
   import sqlite3
   conn = sqlite3.connect('database/album_links.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(DISTINCT artist_ko || album_ko) FROM album_platform_links WHERE album_cover_url IS NOT NULL AND album_cover_url != \"\"')
   print(f'앨범 커버가 있는 앨범: {cursor.fetchone()[0]}개')
   conn.close()
   "
   ```

2. **서버 재시작**
   ```bash
   # Flask 재시작하여 새 데이터 반영
   python3 db_api.py
   ```

3. **배포 준비**
   - 모든 데이터 처리 완료
   - DB 파일 백업
   - 서버 배포

## 문제 해결

### n8n 타임아웃
```bash
# n8n 재시작
killall node
n8n start
```

### 진행 상황 초기화
```bash
rm batch_progress.json
rm batch_failed.json
```

### 특정 앨범만 재처리
```python
python3 -c "
import requests
result = requests.post('http://localhost:5678/webhook/album-links',
    json={'artist': '아티스트명', 'album': '앨범명'})
print(result.json())
"
```
