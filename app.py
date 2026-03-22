import html
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

try:
    import FinanceDataReader as fdr
except ImportError:
    fdr = SimpleNamespace(DataReader=None)

try:
    import streamlit as st
    import streamlit.components.v1 as components
except ImportError:
    class _DummyStreamlit:
        session_state = {}
        query_params = {}

        @staticmethod
        def cache_data(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def __getattr__(self, name):
            raise RuntimeError("streamlit is required to render the app")

    st = _DummyStreamlit()
    components = SimpleNamespace(html=lambda *args, **kwargs: None)

try:
    import streamlit_shadcn_ui as ui
except ImportError:
    ui = None

try:
    from pyecharts import options as opts
    from pyecharts.charts import Bar, Line
except ImportError:
    opts = None
    Bar = None
    Line = None


BASE_DIR = Path(__file__).resolve().parent
TARGET_FILES = {
    "KR Stocks": BASE_DIR / "targets" / "kr_stocks.txt",
    "US Stocks": BASE_DIR / "targets" / "us_stocks.txt",
    "ETFs": BASE_DIR / "targets" / "etfs.txt",
}

CHART_COLORS = [
    "#5470c6",
    "#91cc75",
    "#fac858",
    "#ee6666",
    "#73c0de",
    "#3ba272",
    "#fc8452",
    "#9a60b4",
    "#ea7ccc",
    "#516b91",
]


class TargetConfigError(RuntimeError):
    pass


def load_target_records(file_path):
    path = Path(file_path)
    if not path.exists():
        raise TargetConfigError(f"종목 설정 파일이 없습니다: {path.name}")

    records = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) not in (2, 3) or not parts[0] or not parts[1]:
            raise TargetConfigError(
                f"{path.name}:{line_number} 형식 오류 - '코드|이름|보유수량' 형식을 사용해 주세요."
            )

        quantity_text = parts[2] if len(parts) >= 3 else ""
        if quantity_text == "":
            quantity = 1
        else:
            try:
                quantity = int(quantity_text)
            except ValueError as exc:
                raise TargetConfigError(
                    f"{path.name}:{line_number} 보유수량은 정수여야 합니다: {quantity_text}"
                ) from exc

        records.append({"code": parts[0], "name": parts[1], "quantity": quantity})

    if not records:
        raise TargetConfigError(f"종목 설정 파일이 비어 있습니다: {path.name}")

    return records


def load_all_targets():
    return {
        category: load_target_records(file_path)
        for category, file_path in TARGET_FILES.items()
    }


def configure_page() -> None:
    st.set_page_config(
        page_title="Stock Performance | Value Horizon",
        page_icon=":chart_with_upwards_trend:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }

    [data-testid="stHeader"] {
        display: none;
    }

    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
        font-family: 'Inter', sans-serif;
    }

    .hero-container {
        padding: 2rem 0;
        text-align: center;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 1.5rem;
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #111111;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        font-size: 1rem;
        font-weight: 400;
        color: #888888;
    }

    .metric-card {
        background: #ffffff;
        border: 1px solid #eaeaea;
        border-radius: 12px;
        padding: 0.75rem;
        text-align: center;
        width: 110px;
        min-height: 128px;
        transition: all 0.2s ease;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin: 0 auto;
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #888888;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111111;
        line-height: 1.2;
    }

    .metric-delta {
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.25rem;
    }

    .metric-meta {
        font-size: 0.68rem;
        color: #777777;
        margin-top: 0.25rem;
        line-height: 1.3;
    }

    .delta-positive { color: #eb4432; }
    .delta-negative { color: #1e88e5; }

    .card-on {
        border: 1px solid #007aff !important;
        background: #f0f7ff !important;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.05);
    }

    .card-off {
        border: 1px solid #f0f0f0 !important;
        opacity: 0.4;
        background: #fafafa !important;
        filter: grayscale(1);
    }

    .metric-grid-area {
        display: grid;
        grid-template-columns: repeat(6, 110px);
        justify-content: center;
        gap: 1rem;
        margin: 0.5rem 0 1.5rem 0;
    }

    @media (max-width: 840px) {
        .metric-grid-area {
            grid-template-columns: repeat(4, 110px);
        }
    }

    @media (max-width: 580px) {
        .metric-grid-area {
            grid-template-columns: repeat(2, 110px);
        }
    }

    .metric-link {
        text-decoration: none !important;
        color: inherit !important;
    }

    .metric-link:hover .metric-card {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(17, 17, 17, 0.08);
    }

    .stDateInput > label, .stRadio > label {
        font-weight: 600 !important;
        color: #111111 !important;
    }

    #MainMenu, footer, header, .stDeployButton {
        display: none !important;
    }
</style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=3600)
def fetch_stock_data(target_records, start_date):
    combined_df = pd.DataFrame()
    fetch_start = (
        datetime.combine(start_date, datetime.min.time()) - timedelta(days=15)
    ).strftime("%Y-%m-%d")
    for target in target_records:
        code = target["code"]
        name = target["name"]
        try:
            df = fdr.DataReader(code, fetch_start)
            if not df.empty:
                combined_df[name] = df["Close"]
        except Exception:
            continue
    return combined_df.sort_index()


def slice_period_data(prices_df, start_date, end_date):
    if prices_df.empty:
        return pd.DataFrame()

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    return prices_df[(prices_df.index >= start_dt) & (prices_df.index <= end_dt)].copy()


def calculate_period_summary(prices_df, start_date, end_date, target_records=None):
    df_period = slice_period_data(prices_df, start_date, end_date)
    if df_period.empty:
        return []

    results = []
    requested_start = pd.to_datetime(start_date)
    quantity_map = {
        target["name"]: target["quantity"] for target in (target_records or [])
    }

    for name in df_period.columns:
        series = df_period[name].dropna()
        if series.empty:
            continue

        base_date = series.index[0]
        current_date = series.index[-1]
        start_price = series.iloc[0]
        current_price = series.iloc[-1]

        if pd.isna(start_price) or pd.isna(current_price) or start_price == 0:
            continue

        period_return = ((current_price - start_price) / start_price) * 100
        results.append(
            {
                "name": name,
                "start_price": float(start_price),
                "current_price": float(current_price),
                "return": float(period_return),
                "date": current_date.strftime("%Y-%m-%d"),
                "base_date": base_date.strftime("%Y-%m-%d"),
                "is_delayed_start": base_date > requested_start,
                "quantity": quantity_map.get(name, 1),
            }
        )

    return sorted(results, key=lambda x: x["return"], reverse=True)


def normalize_prices_for_chart(prices_df, visible_names, start_date, end_date):
    df_period = slice_period_data(prices_df, start_date, end_date)
    if df_period.empty:
        return pd.DataFrame()

    actual_cols = [column for column in visible_names if column in df_period.columns]
    if not actual_cols:
        return pd.DataFrame(index=df_period.index)

    normalized = pd.DataFrame(index=df_period.index)
    for column in actual_cols:
        series = df_period[column]
        valid_series = series.dropna()
        if valid_series.empty:
            continue

        base_value = valid_series.iloc[0]
        if pd.isna(base_value) or base_value == 0:
            continue

        normalized[column] = (series / base_value) * 100

    return normalized.dropna(axis=1, how="all")


def get_axis_bounds(norm_df):
    finite_values = norm_df.stack(dropna=True)
    if finite_values.empty:
        return 95, 105

    y_min = float(finite_values.min())
    y_max = float(finite_values.max())
    y_buffer = max((y_max - y_min) * 0.05, 2)
    final_min = min(y_min - y_buffer, 95)
    final_max = max(y_max + y_buffer, 105)
    return int(final_min // 10 * 10), int(final_max // 10 * 10 + 20)


def calculate_portfolio_weights(summary, visible_names=None):
    visible_set = set(visible_names) if visible_names is not None else None
    portfolio = []

    for item in summary:
        if visible_set is not None and item["name"] not in visible_set:
            continue

        market_value = item["current_price"] * item.get("quantity", 1)
        if market_value <= 0:
            continue

        portfolio.append(
            {
                "name": item["name"],
                "quantity": item.get("quantity", 1),
                "current_price": item["current_price"],
                "market_value": float(market_value),
            }
        )

    total_value = sum(item["market_value"] for item in portfolio)
    if total_value == 0:
        return []

    weighted = []
    for item in portfolio:
        weighted.append(
            {
                **item,
                "weight": (item["market_value"] / total_value) * 100,
            }
        )

    return sorted(weighted, key=lambda x: x["weight"], reverse=True)


def render_metric_cards(summary):

    card_html = ['<div class="metric-grid-area">']
    for item in summary:
        name = item["name"]
        is_visible = st.session_state.visibility_map.get(name, True)
        state_class = "card-on" if is_visible else "card-off"
        color_class = "delta-positive" if item["return"] >= 0 else "delta-negative"
        prefix = "+" if item["return"] >= 0 else ""
        safe_name = html.escape(name)
        base_date_text = html.escape(item["base_date"])
        card_html.append(
            f'<div class="metric-link">'
            f'<div class="metric-card {state_class}">'
            f'<div class="metric-label">{safe_name}</div>'
            f'<div class="metric-value">{item["current_price"]:,.0f}</div>'
            f'<div class="metric-delta {color_class}">{prefix}{item["return"]:.2f}%</div>'
            f'<div class="metric-meta">비교기준일<br>{base_date_text}</div>'
            f"</div></div>"
        )
    card_html.append("</div>")
    st.markdown("".join(card_html), unsafe_allow_html=True)


def build_chart(norm_df):
    y_min, y_max = get_axis_bounds(norm_df)

    chart = (
        Line(init_opts=opts.InitOpts(width="100%", height="550px"))
        .add_xaxis(norm_df.index.strftime("%Y-%m-%d").tolist())
    )

    for index, column in enumerate(norm_df.columns):
        chart.add_yaxis(
            series_name=column,
            y_axis=norm_df[column].round(2).tolist(),
            is_symbol_show=False,
            is_connect_nones=False,
            label_opts=opts.LabelOpts(is_show=False),
            linestyle_opts=opts.LineStyleOpts(width=2),
            end_label_opts=opts.LabelOpts(
                is_show=True,
                formatter=column,
                position="right",
                font_size=12,
                font_weight="bold",
                color=CHART_COLORS[index % len(CHART_COLORS)],
            ),
        )

    chart.set_global_opts(
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        legend_opts=opts.LegendOpts(pos_top="top"),
        datazoom_opts=[opts.DataZoomOpts(type_="slider", range_start=0, range_end=100)],
        yaxis_opts=opts.AxisOpts(
            type_="value",
            name="Base 100",
            min_=y_min,
            max_=y_max,
            interval=20,
            splitline_opts=opts.SplitLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(opacity=0.3),
            ),
            axislabel_opts=opts.LabelOpts(formatter="{value}"),
        ),
        xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
    )

    chart.set_series_opts(
        markline_opts=opts.MarkLineOpts(
            data=[opts.MarkLineItem(y=100, name="Base")],
            label_opts=opts.LabelOpts(is_show=True, position="end", formatter="100"),
            linestyle_opts=opts.LineStyleOpts(color="#888", type_="dashed", width=1),
        )
    )

    return chart


def build_portfolio_chart(portfolio_weights):
    chart = Bar(init_opts=opts.InitOpts(width="100%", height="420px"))
    chart.add_xaxis([item["name"] for item in portfolio_weights])
    chart.add_yaxis(
        series_name="비중",
        y_axis=[round(item["weight"], 2) for item in portfolio_weights],
        category_gap="45%",
        label_opts=opts.LabelOpts(
            is_show=True,
            position="right",
            formatter="{c}%",
        ),
    )
    chart.reversal_axis()
    chart.set_series_opts(
        itemstyle_opts=opts.ItemStyleOpts(
            color=CHART_COLORS[0],
            border_radius=[0, 6, 6, 0],
        )
    )
    chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title="Portfolio Allocation",
            pos_left="center",
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            axis_pointer_type="shadow",
            formatter="{b}<br/>비중: {c}%",
        ),
        legend_opts=opts.LegendOpts(is_show=False),
        xaxis_opts=opts.AxisOpts(
            type_="value",
            max_=100,
            axislabel_opts=opts.LabelOpts(formatter="{value}%"),
            splitline_opts=opts.SplitLineOpts(
                is_show=True,
                linestyle_opts=opts.LineStyleOpts(opacity=0.3),
            ),
        ),
        yaxis_opts=opts.AxisOpts(type_="category"),
    )
    return chart


def render_app():
    if (
        ui is None
        or opts is None
        or Line is None
        or Bar is None
        or getattr(fdr, "DataReader", None) is None
    ):
        raise RuntimeError(
            "앱 실행에 필요한 의존성이 없습니다. requirements.txt의 패키지를 먼저 설치해 주세요."
        )

    configure_page()

    try:
        targets_by_category = load_all_targets()
    except TargetConfigError as exc:
        st.error(f"종목 설정을 불러오지 못했습니다: {exc}")
        return

    st.markdown(
        """
<div class="hero-container">
    <div class="hero-title">Stock Performance</div>
    <div class="hero-subtitle">Value Horizon's Advanced Investment Tracking Engine</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    col_cat, col_s, col_e = st.columns([2, 1, 1])

    with col_cat:
        st.markdown(
            '<p style="font-weight: 600; font-size: 0.9rem; margin-bottom: 0.5rem; color: #111;">'
            "Analysis Category"
            "</p>",
            unsafe_allow_html=True,
        )
        tabs = list(TARGET_FILES.keys())
        analysis_type = ui.tabs(options=tabs, default_value=tabs[0], key="analysis_tabs")

    with col_s:
        default_start = date(date.today().year, 1, 1)
        start_date = st.date_input("Start Date", value=default_start)

    with col_e:
        end_date = st.date_input("End Date", value=date.today())

    active_targets = targets_by_category[analysis_type]

    if "visibility_map" not in st.session_state:
        all_names = [
            target["name"]
            for target_list in targets_by_category.values()
            for target in target_list
        ]
        st.session_state.visibility_map = {name: True for name in all_names}

    with st.spinner("Fetching market data..."):
        daily_prices = fetch_stock_data(active_targets, start_date)
        summary = calculate_period_summary(
            daily_prices, start_date, end_date, active_targets
        )

    if not summary:
        st.warning("선택한 기간에 표시할 데이터가 없습니다. 날짜를 조정해 주세요.")
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            "Source: FinanceDataReader"
        )
        return



    st.info(
        "선택 기간 시작일에 가격이 없는 종목은 최초 가격 확인일을 비교기준일로 자동 사용합니다."
    )
    render_metric_cards(summary)
    st.markdown("---")

    visible_names = [
        item["name"]
        for item in summary
        if st.session_state.visibility_map.get(item["name"], True)
    ]
    portfolio_weights = calculate_portfolio_weights(summary, visible_names)

    if portfolio_weights:
        st.subheader("Current Portfolio Allocation")
        portfolio_chart = build_portfolio_chart(portfolio_weights)
        components.html(portfolio_chart.render_embed(), height=420)
        st.markdown("---")

    if not visible_names:
        st.info("최소 1개 이상의 종목을 선택해야 차트를 볼 수 있습니다.")
    else:
        st.subheader("Performance Trend (Base 100 from each symbol's first valid date)")

        norm_df = normalize_prices_for_chart(daily_prices, visible_names, start_date, end_date)
        if not norm_df.empty:
            chart = build_chart(norm_df)
            components.html(chart.render_embed(), height=650)
        else:
            st.warning("선택한 종목으로 그릴 수 있는 차트 데이터가 없습니다.")

    with st.expander("View Raw Data Details"):
        summary_df = pd.DataFrame(summary).rename(
            columns={
                "name": "종목명",
                "start_price": "비교기준일 가격",
                "current_price": "종료일 가격",
                "return": "수익률(%)",
                "date": "종료 기준일",
                "base_date": "비교기준일",
                "is_delayed_start": "후발 시작 종목",
                "quantity": "보유수량",
            }
        )
        st.dataframe(summary_df, use_container_width=True)

    st.caption(
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "Source: FinanceDataReader"
    )


if __name__ == "__main__":
    render_app()
