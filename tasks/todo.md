- [x] pyecharts를 Streamlit에서 deprecated API 없이 렌더링할 경로 확인
- [x] Plotly 전환분을 철회하고 pyecharts 기반으로 렌더링 복구
- [x] 테스트 및 렌더링 검증 수행

## Review
- 원인: 배포 환경에서 `pyecharts`가 ECharts 자산을 HTTPS로 가져오는 과정이 `SSLCertVerificationError`로 실패해 `render_embed()` 자체가 예외로 중단됐다.
- 수정: 공식 `echarts.min.js`를 [`assets/echarts.min.js`](/Users/hyunsikhwang/stock-tracking/assets/echarts.min.js)로 저장소에 포함시키고, `pyecharts`가 만든 HTML의 외부 `<script src=...echarts.min.js>` 태그를 제거한 뒤 로컬 자산을 `data:text/javascript;base64,...` 스크립트로 본문 fragment 앞에 붙여 `st.html(..., unsafe_allow_javascript=True)`로 렌더링하도록 변경했다.
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py` (pass), `./.venv/bin/python -m unittest -q` (pass)
- 추가 확인: `build_pyecharts_html(...)` 결과에서 `<html>/<body>` 래퍼 없이 `data:` URL 스크립트, 차트 div, `echarts.init(...)` 초기화 스크립트가 함께 포함됨을 확인
