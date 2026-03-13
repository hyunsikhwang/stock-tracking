- [x] 3월 11일 카드 출력 구간 확인
- [x] 현재 코드와 카드 CSS/마크업 차이 비교
- [x] 카드 출력 부분을 3월 11일 버전과 동일하게 반영
- [x] 클릭 반응 비활성화
- [x] 검증 및 결과 기록

## Review
- 카드 높이와 `비교기준일` 메타 정보를 3월 11일 카드 출력 기준으로 복원
- 카드 링크는 유지하되 `pointer-events: none`으로 클릭 반응을 제거
- 검증: `.venv/bin/python -m py_compile app.py test_app.py`, `.venv/bin/python -m unittest -q`
