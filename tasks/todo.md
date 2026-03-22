- [x] 보유수량 기반 포트폴리오 비중 계산 함수 추가
- [x] 종목별 비중을 보여주는 심플한 차트 UI 추가
- [x] 관련 단위 테스트와 검증 결과 갱신

## Review
- 현재가 x 보유수량으로 종목별 평가금액과 포트폴리오 비중을 계산하는 로직 추가
- 포트폴리오 비중을 도넛 차트로 렌더링하고, 툴팁에 비중과 평가금액 표시
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
