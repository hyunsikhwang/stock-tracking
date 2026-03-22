- [x] 포트폴리오 막대 차트 GridOpts 호환성 수정
- [x] 변경 검증 및 작업 기록 갱신

## Review
- `GridOpts(left/right/top/bottom)`를 배포 환경 호환 형식인 `pos_left/pos_right/pos_top/pos_bottom`으로 교체
- 포트폴리오 horizontal bar 차트 렌더 오류가 나지 않도록 pyecharts 옵션 호환성 수정
- 검증: `./.venv/bin/python -m py_compile app.py test_app.py`, `./.venv/bin/python -m unittest -q`
