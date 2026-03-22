- [x] 외부 TXT 기반 종목 설정 파일 추가 및 포맷 정의
- [x] `app.py`를 외부 설정 로더 + 보유수량 필드 구조로 변경
- [x] Raw Data 표와 요약 데이터에 보유수량 반영
- [x] 단위 테스트를 새 데이터 구조와 TXT 로더 기준으로 갱신
- [x] README 실행 방법 및 TXT 포맷 문서화
- [x] 검증 실행 후 결과 기록

## Review
- `targets/*.txt`를 추가해 `코드|이름|보유수량` 형식으로 종목을 외부 관리하도록 전환
- `app.py`에 TXT 로더와 형식 검증을 추가하고, 종목 데이터를 `code/name/quantity` 레코드 구조로 통일
- Raw Data 표에 `보유수량` 컬럼을 추가하고, 요약 데이터에도 수량 정보를 포함
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
