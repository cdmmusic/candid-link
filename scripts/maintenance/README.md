# 유지보수 스크립트

DB 데이터 일괄 업데이트용 유틸리티 스크립트 모음

## 스크립트 목록

### update_genre_and_type.py
장르 및 발매 유형 일괄 업데이트

```bash
python3 scripts/maintenance/update_genre_and_type.py
```

### update_release_dates.py
발매일 일괄 업데이트

```bash
python3 scripts/maintenance/update_release_dates.py
```

---

**주의**: 이 스크립트들은 일회성 작업용입니다.
실행 전 DB 백업을 권장합니다.
