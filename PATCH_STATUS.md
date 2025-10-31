# 벅스 앨범 커버 수집 패치 상태

## 패치 진행 상황

### ✅ 완료된 작업

1. **extract_bugs_album_cover() 함수 추가** - 완료
   - 벅스 앨범 페이지에서 커버 이미지를 추출하는 함수
   - Line 79 이전에 추가됨
   - 3가지 패턴으로 앨범 커버 이미지 추출 시도:
     - Pattern 1: albumImgArea div 내의 img 태그
     - Pattern 2: og:image 메타 태그
     - Pattern 3: img 태그에서 album/cover 관련 이미지

2. **search_kr_platforms() 함수 수정** - 완료
   - `album_cover_url = None` 변수 초기화 추가
   - 벅스 플랫폼 처리 섹션에 `extract_bugs_album_cover()` 호출 추가
   - 반환값을 `return kr_results, album_cover_url`로 변경

### ⚠️ 남은 작업 (1단계)

**call site 수정** - api/companion_api.py line 594 근처
이 부분만 수정하면 패치 완료!

**현재 상태 (line 594):**
```python
kr_results = search_kr_platforms(artist, album_title)
if kr_results:
    result['kr_platforms'] = kr_results
    debug_steps.append(f"✓ KR platforms found: {len(kr_results)} ({', '.join(kr_results.keys())})")
    safe_print(f"KR platforms found: {len(kr_results)}")
```

**수정 필요:**
```python
kr_results, bugs_album_cover = search_kr_platforms(artist, album_title)
if kr_results:
    result['kr_platforms'] = kr_results
    debug_steps.append(f"✓ KR platforms found: {len(kr_results)} ({', '.join(kr_results.keys())})")
    safe_print(f"KR platforms found: {len(kr_results)}")
# 벅스에서 앨범 커버 가져오기
if bugs_album_cover and not album_cover_url:
    album_cover_url = bugs_album_cover
    debug_steps.append(f"✓ Album cover from Bugs: {bugs_album_cover[:100]}")
```

## 수동 수정 방법

1. 모든 Python 프로세스 종료:
```bash
taskkill /F /IM python.exe
```

2. 텍스트 에디터로 `api/companion_api.py` 파일 열기

3. Line 594 찾기: `kr_results = search_kr_platforms(artist, album_title)`

4. 위 "수정 필요" 섹션의 코드로 교체

5. 파일 저장

## 패치 검증

패치가 올바르게 적용되었는지 확인:

```bash
cd "//candidmusic/CANDID MUSIC/링크 사이트/release-album-link"
python -c "
with open('api/companion_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('Function', 'def extract_bugs_album_cover'),
    ('Variable', 'album_cover_url = None'),
    ('Bugs call', 'extract_bugs_album_cover(bugs_url)'),
    ('Return', 'return kr_results, album_cover_url'),
    ('Unpack', 'kr_platforms, bugs_album_cover')
]

for name, pattern in checks:
    status = 'OK' if pattern in content else 'FAIL'
    print(f'[{status}] {name}')
"
```

모든 항목이 `[OK]`이면 패치 완료!

## 테스트 방법

1. API 시작:
```bash
python api/companion_api.py
```

2. 테스트 실행:
```bash
python -c "
import sys, io
import requests
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

response = requests.post(
    'http://localhost:5001/search',
    json={'artist': '불꽃(FLAME)', 'album': '가을…그리고 추억', 'cdma': 'CDMA05110'},
    timeout=180
)
data = response.json()
print(f'Global: {len(data.get(\"data\", {}).get(\"platforms\", {}))}')
print(f'KR: {len(data.get(\"data\", {}).get(\"kr_platforms\", {}))}')
cover = data.get('data', {}).get('album_cover_url', None)
if cover:
    print(f'Album cover: {cover[:100]}...')
else:
    print('Album cover: Not found')
"
```

## 예상 결과

- Global 플랫폼: 12~13개
- KR 플랫폼: 3~5개
- Album cover: 벅스에서 가져온 이미지 URL (예: `https://image.bugs.co.kr/album/...`)

## 백업 파일

다음 백업 파일들이 생성되었습니다:
- `api/companion_api_backup_20251031_204250.py`
- `api/companion_api_backup_20251031_204455.py`

문제 발생시 이 백업 파일로 복원할 수 있습니다.

## 문제 해결

### 구문 오류 발생시
```bash
python -m py_compile api/companion_api.py
```

### API가 시작되지 않을 때
```bash
# 포트 5001 확인
netstat -ano | findstr :5001

# 프로세스 종료
taskkill /F /PID <PID>
```

### 앨범 커버가 수집되지 않을 때
- 벅스에 해당 앨범이 없을 수 있음
- 로그 파일 확인: `logs/companion_api_*.log`
- 다른 앨범으로 테스트해보기

## 최종 목표

이 패치가 완료되면:
- 모든 앨범 수집시 벅스에서 자동으로 앨범 커버 추출
- `album_cover_url` 필드에 커버 이미지 URL 저장
- companion.global과 벅스 두 곳에서 앨범 커버 수집 시도
- 데이터베이스에 앨범 커버 URL 저장하여 향후 활용 가능
