# 앨범 링크 수집 시스템

## 🎯 Quick Start (3단계)

### 1️⃣ 서비스 시작
```bash
# Selenium Grid 실행
docker run -d --name selenium-standalone -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest

# Companion API 실행
cd /Users/choejibin/release-album-link
nohup python3 companion_api.py > /tmp/companion_api.log 2>&1 &
```

### 2️⃣ 수집 시작
```bash
# 백그라운드 실행
nohup python3 collect_global_resume.py > collection.log 2>&1 &
```

### 3️⃣ 진행 확인
```bash
# 실시간 로그
tail -f collection.log

# 진행률만 보기
grep "진행률" collection.log
```

---

## 📊 현재 수집 상태 (2025-10-28)

- **진행 중**: ✅ (프로세스 ID: 53197)
- **시작**: CDMA05110 (최신 앨범)
- **목표**: 4,922개 앨범
- **예상 완료**: 41-68시간 후
- **로그**: `collection.log`

---

## 📖 상세 문서

| 문서 | 설명 |
|------|------|
| `COLLECTION_STATUS.md` | 현재 수집 작업 현황 및 모니터링 |
| `SCRIPTS_GUIDE.md` | 모든 스크립트 설명 및 사용법 |
| `README_COLLECTION.md` | 이 파일 (빠른 시작) |

---

## 🔍 자주 사용하는 명령어

```bash
# 상태 확인
ps aux | grep -E "collect_global|companion_api" | grep -v grep

# 로그 확인
tail -30 collection.log

# 실패한 앨범 확인
cat failure_logs/kr_partial.txt

# 수집 재시작 (중단된 경우)
nohup python3 collect_global_resume.py > collection.log 2>&1 &
```

---

## ⚡ 중요 사항

1. **자동 재개**: 수집이 중단되어도 재실행하면 이미 수집된 앨범은 건너뜀
2. **실패 로그**: `failure_logs/kr_partial.txt`는 수동 확인 필요
3. **API 타임아웃**: 간헐적 타임아웃은 정상 (자동 건너뛰기)
4. **중복 실행 금지**: 한 번에 하나의 수집만 실행

---

## 📞 문제 해결

### 수집이 안 됨
```bash
# 1. 서비스 확인
curl http://localhost:5001/health
curl -I http://localhost:4444

# 2. 재시작
pkill -f companion_api.py
pkill -f collect_global_resume.py

# 3. 다시 시작
nohup python3 companion_api.py > /tmp/companion_api.log 2>&1 &
sleep 3
nohup python3 collect_global_resume.py > collection.log 2>&1 &
```

### 로그 분석
```bash
# 에러만 보기
grep -E "✗|오류" collection.log | tail -20

# 성공만 보기
grep "✓" collection.log | tail -20

# 통계 보기
grep "진행률" collection.log | tail -1
```

---

## 📁 주요 파일 위치

```
/Users/choejibin/release-album-link/
├── collect_global_resume.py  # 메인 수집 스크립트
├── companion_api.py           # API 서버
├── album_links.db             # 데이터베이스
├── collection.log             # 수집 로그
└── failure_logs/              # 실패 로그
    ├── kr_partial.txt         # KR 일부만 찾은 앨범
    └── global_not_found.txt   # Global 못 찾은 앨범
```

---

## 🎓 추가 학습

- **전체 스크립트 설명**: `SCRIPTS_GUIDE.md` 참고
- **현재 진행 상황**: `COLLECTION_STATUS.md` 참고
- **DB 구조**: `album_links.db` - SQLite 브라우저로 확인

---

## ✅ 체크리스트

수집 시작 전:
- [ ] Selenium Grid 실행 중 (포트 4444)
- [ ] Companion API 실행 중 (포트 5001)
- [ ] DB 파일 존재 (`album_links.db`)
- [ ] 로그 디렉토리 존재 (`failure_logs/`)

수집 중:
- [ ] `collection.log` 정상 업데이트 중
- [ ] 프로세스 실행 중 (`ps aux | grep collect_global`)
- [ ] 진행률 표시 (10개마다)

수집 완료 후:
- [ ] 최종 통계 확인 (`collection.log` 하단)
- [ ] 실패 로그 확인 (`failure_logs/`)
- [ ] `kr_partial.txt` 수동 처리
