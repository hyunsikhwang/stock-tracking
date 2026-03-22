# stock-tracking

Streamlit 기반 주식/ETF 추적 앱입니다.

## 실행 방법

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 종목 설정 파일

- 종목 목록은 `targets/kr_stocks.txt`, `targets/us_stocks.txt`, `targets/etfs.txt`에서 관리합니다.
- 파일 인코딩은 UTF-8입니다.
- 한 줄에 하나의 종목을 `코드|이름|보유수량` 형식으로 작성합니다.
- 보유수량은 생략 가능하며, 비워두면 기본값 `1`이 적용됩니다.
- 빈 줄과 `#`로 시작하는 주석 줄은 무시합니다.

예시:

```txt
005930|삼성전자|1
TSLA|Tesla|
# 주석
```
