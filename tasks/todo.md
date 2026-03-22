- [x] 포트폴리오 차트의 민감 정보 노출 문구 제거
- [x] 변경 검증 및 작업 기록 갱신

## Review
- 포트폴리오 도넛 차트의 툴팁에서 평가금액 노출을 제거하고 비중만 표시하도록 수정
- 차트 부제와 캡션에서 평가금액/보유수량을 직접 언급하던 문구 제거
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
