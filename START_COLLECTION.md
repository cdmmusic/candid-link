# 🚀 자동 수집 시작 가이드

## 사전 체크리스트

### 1. Docker 설치 확인
```bash
docker --version
docker-compose --version
```

### 2. 환경 변수 확인
`.env` 파일에 Turso 인증 정보가 있는지 확인:
```bash
cat .env | grep TURSO
```

### 3. 워크플로우 파일 확인
```bash
ls -la workflows/release-album-link.json
```

## 🎯 실행 단계

### Step 1: 서비스 시작

```bash
# 백그라운드에서 모든 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

예상 출력:
```
NAME                          STATUS          PORTS
album-links-collector         Up
album-links-companion-api     Up              0.0.0.0:5001->5001/tcp
album-links-n8n               Up              0.0.0.0:5678->5678/tcp
album-links-selenium          Up              0.0.0.0:4444->4444/tcp
```

### Step 2: n8n 워크플로우 설정

1. **n8n 접속**: http://localhost:5678
2. **로그인**:
   - Username: `admin`
   - Password: `album-links-2025`
3. **워크플로우 가져오기**:
   - 메뉴 → Import from File
   - `workflows/release-album-link.json` 선택
4. **워크플로우 활성화**: 우측 상단 토글 ON

### Step 3: 수집 모니터링

```bash
# 실시간 로그 확인
docker-compose logs -f collector

# 진행 상황 파일 확인
watch -n 5 cat .collection_progress.txt
```

## 📊 예상 진행 상황

```
현재 진행: 150/5089 (2.9%)
성공: 142
실패: 8
예상 소요 시간: 13.5시간
```

## ⚠️ 문제 해결

### 문제 1: Collector가 시작 직후 중단됨

**원인**: n8n이 완전히 시작되지 않음

**해결**:
```bash
# n8n 로그 확인
docker-compose logs n8n

# 30초 대기 후 collector 재시작
sleep 30
docker-compose restart collector
```

### 문제 2: "Connection refused" 에러

**원인**: 서비스 간 네트워크 연결 문제

**해결**:
```bash
# 모든 서비스 재시작
docker-compose restart
```

### 문제 3: Selenium 타임아웃

**원인**: Selenium Chrome이 느리거나 응답 없음

**해결**:
```bash
# Selenium 재시작
docker-compose restart selenium-chrome
docker-compose restart companion-api
```

### 문제 4: 진행이 멈춤

**원인**: 특정 앨범에서 멈춤

**해결**:
```bash
# 현재 진행 확인
cat .collection_progress.txt

# 로그에서 마지막 앨범 확인
docker-compose logs --tail=50 collector

# Collector 재시작 (자동으로 이어서 진행)
docker-compose restart collector
```

## 🛑 중지 방법

### 일시 정지 (진행 상황 유지)
```bash
docker-compose stop collector
```

### 재개
```bash
docker-compose start collector
```

### 완전 중지
```bash
docker-compose down
```

### 처음부터 다시 시작
```bash
# 진행 상황 파일 삭제
rm .collection_progress.txt

# Collector 재시작
docker-compose restart collector
```

## 📈 진행 상황 확인

### 방법 1: 로그 확인
```bash
docker-compose logs -f collector | grep "Progress:"
```

### 방법 2: 진행 파일 확인
```bash
watch -n 10 "cat .collection_progress.txt"
```

### 방법 3: 데이터베이스 직접 확인
```bash
~/.turso/turso db shell album-links "
SELECT
  COUNT(CASE WHEN found = 1 THEN 1 END) as collected,
  COUNT(CASE WHEN found = 0 OR found IS NULL THEN 1 END) as remaining,
  COUNT(DISTINCT artist_ko || '|||' || album_ko) as total
FROM album_platform_links"
```

## ✅ 수집 완료 후

### 1. 통계 확인
```bash
docker-compose logs collector | grep "Collection Complete" -A 10
```

### 2. 데이터 확인
```bash
~/.turso/turso db shell album-links "
SELECT COUNT(DISTINCT artist_ko || '|||' || album_ko)
FROM album_platform_links
WHERE found = 1"
```

### 3. 앨범 커버 업데이트
수집이 완료되면 앨범 커버는 자동으로 Bugs 플랫폼에서 생성됩니다.

### 4. 서비스 중지
```bash
docker-compose down
```

## 🔧 고급 옵션

### 배치 모드 (테스트용)
처음 10개 앨범만 처리:
```bash
docker-compose run --rm collector python3 scripts/auto_collect_all.py 10
```

### 로그 레벨 조정
더 자세한 로그:
```bash
docker-compose logs -f --tail=100 collector
```

### 리소스 모니터링
```bash
docker stats
```

## 📞 지원

문제가 지속되면:
1. 로그 전체 내용 확인: `docker-compose logs > logs.txt`
2. 시스템 상태 확인: `docker-compose ps`
3. GitHub Issues에 로그와 함께 보고

---

**예상 완료 시간**: 14시간
**처리 속도**: 분당 약 6개 앨범
**총 앨범 수**: 5,089개
