- [x] 차트 렌더링 실패 원인 재현 및 확인
- [x] Streamlit deprecated API 교체 및 차트 렌더링 수정
- [x] 테스트/검증 수행 및 결과 기록

## Review
- 원인: `pyecharts.render_embed()`가 외부 `echarts.min.js`를 포함한 완전한 HTML 문서를 생성하는데, 이를 deprecated `st.components.v1.html`로 직접 주입하고 있어 Streamlit의 권장 렌더링 경로와 맞지 않아 차트가 비정상 렌더링될 수 있었다.
- 수정: 차트 HTML을 base64 data URL로 인코딩해 `components.iframe`으로 렌더링하도록 변경하고, `st.dataframe(..., use_container_width=True)`를 `width="stretch"`로 교체했다.
- 테스트: `./.venv/bin/python -m py_compile app.py test_app.py` (pass), `./.venv/bin/python -m unittest -q` (pass)
