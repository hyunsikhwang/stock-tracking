- [x] 포트폴리오 차트를 가로 막대 차트로 변경
- [x] 변경 검증 및 작업 기록 갱신

## Review
- 포트폴리오 비중 시각화를 도넛에서 horizontal bar 차트로 교체
- x축은 비중 퍼센트만 표시하고 툴팁도 종목명과 비중만 노출하도록 유지
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
