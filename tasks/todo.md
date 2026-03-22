- [x] 포트폴리오 막대 차트 set_global_opts 호환성 수정
- [x] 변경 검증 및 작업 기록 갱신

## Review
- 배포 환경 pyecharts에서 지원하지 않는 `set_global_opts(grid_opts=...)`를 제거
- horizontal bar 차트가 구버전 pyecharts에서도 렌더되도록 전역 옵션 호환성 정리
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
