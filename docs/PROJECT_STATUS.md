# 음악 플랫폼 링크 통합 시스템 - 프로젝트 현황

## 📋 프로젝트 개요

**목적:** 17개 음악 플랫폼의 앨범 링크를 자동 수집하여 통합 제공

**위치:** `/Users/choejibin/release-album-link`

---

## 🎯 현재 상태

### 데이터베이스 현황
- **총 앨범:** 5,093개
- **발매일 설정 완료:** 5,093개 (100%)
- **링크 수집 완료:** 10개
- **앨범 커버 있음:** 10개
- **남은 작업:** 5,083개 앨범 링크/커버 수집 필요

### 시스템 구성
```
1. Flask API (db_api.py) - 포트 5002
   - 웹 UI 제공
   - SQLite DB 조회 API

2. n8n 워크플로우 - 포트 5678
   - 웹훅: /webhook/album-links
   - 17개 플랫폼 링크 자동 수집

3. SQLite DB (database/album_links.db)
   - 5,093개 앨범 데이터
   - 17개 플랫폼별 링크
```

---

## ✅ 완료된 작업

### 1. 데이터 정리 및 수정
- ✅ 중복 플랫폼 레코드 정리 (57개 삭제)
- ✅ 발매일 표시 문제 수정 (빈 문자열 처리)
- ✅ 미래 발매 앨범 필터링 (발매일/시간 기준)
- ✅ 날짜 표시 형식 변경 (YYYY-MM-DD)
- ✅ 발매일 없는 앨범 Excel에서 찾아서 업데이트 (10개 → 0개)

### 2. UI/UX 개선
- ✅ 무한 스크롤 구현 (50개씩)
- ✅ 앨범 커버 우선 표시
- ✅ TCT → QQ MUSIC 플랫폼 이름 변경
- ✅ 검색 기능 (아티스트/앨범)

### 3. 배치 처리 스크립트
- ✅ `batch_process_resume.py` - 중단/재개 지원
- ✅ 진행 상황 자동 저장 (`batch_progress.json`)
- ✅ 실패 앨범 별도 기록 (`batch_failed.json`)

---

## 📁 주요 파일

### 서버 파일
- `db_api.py` - Flask 웹 서버 + API
- `database/album_links.db` - SQLite 데이터베이스
- `workflows/release-album-link.json` - n8n 워크플로우

### 데이터 처리
- `import_excel.py` - Excel 데이터 import
- `auto_process_albums.py` - 자동 앨범 처리 (기존)
- `batch_process_resume.py` - 배치 처리 (중단/재개)
- `update_release_dates.py` - 발매일 업데이트

### 문서
- `README_BATCH.md` - 배치 처리 가이드
- `PROJECT_STATUS.md` - 이 파일

---

## 🚀 다음 단계

### 옵션 1: 로컬에서 데이터 완성 후 배포 (추천)

**단계:**
1. 컴퓨터 켜둘 수 있을 때 배치 처리 실행
   ```bash
   n8n start
   python3 batch_process_resume.py
   # 입력: 100 (배치 크기)
   # 입력: 2 (대기 시간)
   ```

2. 5,083개 앨범 모두 처리 (약 50회 반복)
   - 100개씩 처리: 5-10분/회
   - 언제든 중단 가능 (Ctrl+C)
   - 재실행 시 이어서 처리

3. 완료 후 서버 배포

**예상 소요 시간:**
- 여러 세션으로 나눠서: 약 1-2주
- 한 번에 처리: 3-10시간

### 옵션 2: 서버 배포 후 자동 처리

**서버리스 배포 추천 조합:**

#### 🏆 1순위: Vercel + Turso (무료)
- Frontend + API: Vercel
- Database: Turso (SQLite 호환, 500M rows 무료)
- 장점: 완전 무료, SQLite 코드 재사용, 글로벌 CDN
- 비용: $0/월

#### 2순위: Railway (간단)
- Flask + SQLite + n8n 그대로 배포
- 장점: 코드 변경 최소, 자동 처리 가능
- 비용: $5-10/월 (무료 크레딧 $5)

---

## 🔧 서버 시작 명령어

```bash
cd /Users/choejibin/release-album-link

# 1. Flask API 서버
python3 db_api.py

# 2. n8n 워크플로우
n8n start

# 3. 배치 처리 (선택)
python3 batch_process_resume.py
```

---

## 📊 지원 플랫폼 (17개)

### 국내 (5개)
- Melon, Genie, Bugs, FLO, VIBE

### 글로벌 (12개)
- Apple Music, Spotify, YouTube, Amazon Music
- Deezer, Tidal, KKBox, Anghami
- Pandora, LINE Music, AWA, Moov

### 추가 (1개)
- QQ MUSIC (구 TCT)

---

## 🐛 알려진 이슈

### 1. Excel 데이터 오류
- 일부 앨범의 발매일 연도 오류 (2032, 2203 등)
- 해결: 수동으로 2023으로 수정 완료

### 2. n8n 타임아웃
- 일부 앨범 처리 시 타임아웃 발생
- 해결: batch_failed.json에 기록 → 나중에 재처리

### 3. 터미널 폰트 깨짐
- Python 스크립트의 한글 출력 시 발생
- 해결: `reset` 명령어 또는 `export LANG=en_US.UTF-8`

---

## 💡 다음 채팅 시작 프롬프트

```
프로젝트 계속 진행합니다.

현재 상황:
- 총 앨범: 5,093개
- 링크 수집 완료: 10개
- 남은 작업: 5,083개

진행할 작업:
[ ] 로컬 배치 처리로 데이터 완성
[ ] 서버리스 배포 (Vercel + Turso)
[ ] 기타

어떤 작업부터 진행할까요?
```

---

## 📞 빠른 참조

### DB 통계 확인
```bash
sqlite3 database/album_links.db "
SELECT
  COUNT(DISTINCT artist_ko || album_ko) as total,
  SUM(CASE WHEN album_cover_url IS NOT NULL AND album_cover_url != '' THEN 1 ELSE 0 END) as has_cover
FROM (SELECT DISTINCT artist_ko, album_ko, album_cover_url FROM album_platform_links)
"
```

### 진행 상황 리셋
```bash
rm batch_progress.json
rm batch_failed.json
```

### 서버 재시작
```bash
lsof -ti:5002 | xargs kill -9
lsof -ti:5678 | xargs kill -9
python3 db_api.py &
n8n start &
```

---

**마지막 업데이트:** 2025-10-13
**프로젝트 경로:** `/Users/choejibin/release-album-link`
