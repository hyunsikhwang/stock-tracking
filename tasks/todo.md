- [x] 포트폴리오 차트를 horizontal stacked bar로 변경
- [x] 변경 검증 및 작업 기록 갱신

## Review
- 포트폴리오 비중 차트를 단일 100% 막대 위에 종목별 세그먼트를 쌓는 horizontal stacked bar로 변경
- 라벨과 툴팁은 종목명과 비중만 표시하고, 작은 비중 세그먼트는 내부 라벨을 숨겨 가독성 유지
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
