- [x] requirements에 pyecharts 버전 고정
- [x] 변경 검증 및 작업 기록 갱신

## Review
- 로컬 `.venv` 기준 `pyecharts 2.0.9`를 확인하고 `requirements.txt`에 동일 버전으로 고정
- 배포환경도 로컬과 같은 pyecharts 버전으로 설치되도록 재현성 확보
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
