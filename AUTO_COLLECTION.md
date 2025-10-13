# 24/7 자동 앨범 링크 수집 가이드

## 개요

이 시스템은 Docker Compose를 사용하여 24시간 자동으로 앨범 링크를 수집합니다.

### 구성 요소

1. **n8n**: 워크플로우 자동화 엔진
2. **Companion API**: Selenium 기반 Companion.global 자동화
3. **Selenium Chrome**: 헤드리스 브라우저
4. **Collector**: Python 자동 수집 스크립트

## 시작하기

### 1. 환경 변수 설정

`.env` 파일에 Turso 데이터베이스 정보를 입력하세요:

```bash
TURSO_DATABASE_URL=libsql://your-database.turso.io
TURSO_AUTH_TOKEN=your-auth-token-here
```

### 2. Docker Compose 시작

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f collector
```

### 3. n8n 워크플로우 가져오기

1. 브라우저에서 `http://localhost:5678` 접속
2. 로그인: `admin / album-links-2025`
3. 워크플로우 가져오기: `workflows/release-album-link.json`

## 진행 상황 모니터링

### 실시간 로그 확인

```bash
# Collector 로그
docker-compose logs -f collector

# n8n 로그
docker-compose logs -f n8n

# Companion API 로그
docker-compose logs -f companion-api
```

### 진행률 확인

진행 상황은 `.collection_progress.txt` 파일에 자동 저장됩니다:

```bash
cat .collection_progress.txt
```

## 제어 명령어

### 일시 정지

```bash
docker-compose stop collector
```

### 재개

```bash
docker-compose start collector
```

### 재시작 (처음부터)

```bash
# 진행 상황 파일 삭제
rm .collection_progress.txt

# Collector 재시작
docker-compose restart collector
```

### 중지

```bash
docker-compose down
```

## 예상 소요 시간

- **총 앨범 수**: 5,089개
- **평균 처리 시간**: 앨범당 약 10초
- **예상 총 시간**: 약 14시간

처리 속도는 네트워크 상태와 서버 성능에 따라 달라질 수 있습니다.

## 문제 해결

### Collector가 시작되지 않음

```bash
# Collector 로그 확인
docker-compose logs collector

# n8n이 준비될 때까지 대기 후 재시작
docker-compose restart collector
```

### n8n 워크플로우 오류

```bash
# n8n 컨테이너 재시작
docker-compose restart n8n

# 브라우저에서 워크플로우 활성화 확인
```

### Selenium 오류

```bash
# Selenium 컨테이너 재시작
docker-compose restart selenium-chrome companion-api
```

## 수집 완료 후

### 1. 앨범 커버 업데이트

모든 링크 수집이 완료되면 앨범 커버를 업데이트합니다:

```bash
python3 scripts/update_album_covers_from_turso.py
```

### 2. Vercel 재배포

업데이트된 데이터가 웹사이트에 즉시 반영됩니다 (Turso 클라우드 DB 사용).

## 배치 처리 모드

일부 앨범만 처리하려면:

```bash
# 처음 100개만 처리
docker-compose run --rm collector python3 scripts/auto_collect_all.py 100
```

## 시스템 요구 사항

- Docker 및 Docker Compose
- 최소 4GB RAM
- 안정적인 인터넷 연결
- 충분한 디스크 공간 (로그용)

## 지원

문제가 발생하면 GitHub Issues에 보고하세요.
