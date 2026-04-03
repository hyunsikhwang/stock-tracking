- [x] Streamlit에서 사용할 정상적인 ECharts 통합 방식 확인
- [x] `pyecharts` 차트를 `streamlit-echarts` 기반으로 교체
- [x] 테스트 및 기록 갱신

## Review
- 원인: `st.html`에 HTML/스크립트를 우회 주입하는 방식이 Streamlit 렌더링 경로와 맞지 않아 차트가 안정적으로 표시되지 않았다.
- 수정: `pyecharts`는 유지하되 [`app.py`](/Users/hyunsikhwang/stock-tracking/app.py)의 렌더링을 `streamlit_echarts.st_pyecharts(...)` 기반으로 바꿔 Streamlit 전용 ECharts 컴포넌트를 사용하도록 정리했다.
- 의존성: [`requirements.txt`](/Users/hyunsikhwang/stock-tracking/requirements.txt)에 `streamlit-echarts==0.4.0`를 명시했다.
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py` (pass), `./.venv/bin/python -m unittest -q` (pass)
