- [x] pyecharts를 Streamlit에서 deprecated API 없이 렌더링할 경로 확인
- [x] Plotly 전환분을 철회하고 pyecharts 기반으로 렌더링 복구
- [x] 테스트 및 렌더링 검증 수행

## Review
- 원인: `pyecharts` 차트를 `st.components.v1.html`/`iframe` 경로로 붙이면서 deprecated 경고가 발생했고, 외부 JS 로딩 의존 때문에 렌더링이 불안정했다.
- 수정: `pyecharts`를 유지하되 `opts.RenderOpts(is_embed_js=True)`로 ECharts 스크립트를 HTML 안에 인라인 포함시키고, 이를 `st.html(..., unsafe_allow_javascript=True, width="stretch")`로 렌더링하도록 변경했다.
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py` (pass), `./.venv/bin/python -m unittest -q` (pass)
- 추가 확인: `build_chart(...).render_embed()` 결과에서 외부 `src="https://assets.pyecharts.org` 스크립트가 사라지고 인라인 ECharts 스크립트가 포함됨을 확인
