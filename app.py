import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, date, timedelta
import streamlit.components.v1 as components
from pyecharts import options as opts
from pyecharts.charts import Line

# Page Configuration
st.set_page_config(
    page_title="Stock Performance | Value Horizon",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Value Horizon Look & Feel
st.markdown("""
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
        font-size: 1.0rem;
        font-weight: 400;
        color: #888888;
    }

    /* Metric Card Wrapper */
    .metric-card {
        background: #ffffff;
        border: 1px solid #eaeaea;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        position: relative;
        height: 100%;
        transition: all 0.2s ease;
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #888888;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111111;
    }

    .metric-delta {
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.25rem;
    }

    .delta-positive { color: #eb4432; }
    .delta-negative { color: #1e88e5; }
    
    /* Toggle State Classes */
    .card-on {
        border: 2px solid #007aff !important;
        background: #f0f7ff !important;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.1);
    }
    
    .card-off {
        border: 1px solid #f0f0f0 !important;
        opacity: 0.5;
        background: #fafafa !important;
    }

    /* Ghost Button Overlay */
    div.stButton > button {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        padding: 0 !important;
        z-index: 10 !important;
    }
    
    div.stButton > button:hover {
        background: rgba(0, 122, 255, 0.03) !important;
    }

    /* Input Section Styling */
    .stDateInput > label, .stRadio > label {
        font-weight: 600 !important;
        color: #111111 !important;
    }

    /* Hide Streamlit components */
    #MainMenu, footer, header, .stDeployButton {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Analysis Targets
TARGET_STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "058470": "리노공업",
    "042700": "한미반도체",
    "196170": "알테오젠",
    "214150": "클래시스",
    "214450": "파마리서치",
    "278470": "에이피알"
}

TARGET_ETFS = {
    "226490": "KODEX 코스피",
    "277630": "TIGER 코스피",
    "229200": "KODEX 코스닥150",
    "232080": "TIGER 코스닥150"
}

@st.cache_data(ttl=3600)
def fetch_stock_data(target_dict, start_date):
    combined_df = pd.DataFrame()
    fetch_start = (datetime.combine(start_date, datetime.min.time()) - timedelta(days=15)).strftime('%Y-%m-%d')
    for code, name in target_dict.items():
        df = fdr.DataReader(code, fetch_start)
        if not df.empty:
            combined_df[name] = df['Close']
    return combined_df

def calculate_period_summary(prices_df, start_date, end_date):
    if prices_df.empty:
        return []
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    df_period = prices_df[(prices_df.index >= start_dt) & (prices_df.index <= end_dt)]
    
    if df_period.empty:
        return []

    base_prices = df_period.iloc[0]
    current_prices = df_period.iloc[-1]
    first_date = df_period.index[0].strftime('%Y-%m-%d')
    last_date = df_period.index[-1].strftime('%Y-%m-%d')

    results = []
    for name in prices_df.columns:
        start_price = base_prices[name]
        current_price = current_prices[name]
        period_return = ((current_price - start_price) / start_price) * 100
        
        results.append({
            "name": name,
            "start_price": start_price,
            "current_price": current_price,
            "return": period_return,
            "date": last_date,
            "base_date": first_date
        })
    
    return sorted(results, key=lambda x: x['return'], reverse=True)

# UI Header
st.markdown("""
<div class="hero-container">
    <div class="hero-title">📈 Stock Performance</div>
    <div class="hero-subtitle">Value Horizon's Advanced Investment Tracking Engine</div>
</div>
""", unsafe_allow_html=True)

# Controls Section
col_cat, col_s, col_e = st.columns([2, 1, 1])

with col_cat:
    analysis_type = st.radio(
        "Analysis Category",
        ["Individual Stocks", "ETFs"],
        horizontal=True
    )

with col_s:
    default_start = date(date.today().year, 1, 1)
    start_date = st.date_input("Start Date", value=default_start)

with col_e:
    end_date = st.date_input("End Date", value=date.today())

# Set target dictionary based on selection
active_targets = TARGET_STOCKS if analysis_type == "Individual Stocks" else TARGET_ETFS

# Initialize session state for toggles
if 'visibility_map' not in st.session_state:
    st.session_state.visibility_map = {name: True for name in list(TARGET_STOCKS.values()) + list(TARGET_ETFS.values())}

# Data Processing
with st.spinner("Fetching market data..."):
    daily_prices = fetch_stock_data(active_targets, start_date)
    summary = calculate_period_summary(daily_prices, start_date, end_date)

if not summary:
    st.warning("No data found for the selected period. Please adjust the dates.")
else:
    # Metric Grid
    st.markdown('<div style="margin-bottom: 0.5rem; font-size: 0.85rem; color: #888; text-align: center;">💡 Click a card to toggle chart visibility</div>', unsafe_allow_html=True)
    
    # Use a container to hold the cards and buttons
    cols = st.columns(len(summary))
    
    for idx, item in enumerate(summary):
        name = item['name']
        is_visible = st.session_state.visibility_map.get(name, True)
        
        # Determine card classes
        state_class = "card-on" if is_visible else "card-off"
        color_class = "delta-positive" if item['return'] >= 0 else "delta-negative"
        prefix = "+" if item['return'] >= 0 else ""
        
        with cols[idx]:
            # Container for Card UI + Button Overlay
            st.markdown(f"""
            <div class="metric-card {state_class}">
                <div class="metric-label">{name}</div>
                <div class="metric-value">{item['current_price']:,.0f}</div>
                <div class="metric-delta {color_class}">{prefix}{item['return']:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Absolute positioned ghost button
            if st.button(" ", key=f"toggle_{name}"):
                st.session_state.visibility_map[name] = not is_visible
                st.rerun()

    st.markdown("---")

    # Filter visible stocks for chart
    visible_names = [item['name'] for item in summary if st.session_state.visibility_map.get(item['name'], True)]
    
    if not visible_names:
        st.info("Select at least one stock to view the trend chart.")
    else:
        # Chart Section
        st.subheader(f"Performance Trend (Based on 100 on {summary[0]['base_date']})")
        
        df_period = daily_prices[(daily_prices.index >= pd.to_datetime(start_date)) & (daily_prices.index <= pd.to_datetime(end_date))].copy()
        
        if not df_period.empty:
            df_visible = df_period[visible_names]
            base_val = df_visible.iloc[0]
            norm_df = (df_visible / base_val * 100)
            
            y_min = float(norm_df.min().min())
            y_max = float(norm_df.max().max())
            y_buffer = (y_max - y_min) * 0.05
            final_min = min(y_min - y_buffer, 95)
            final_max = max(y_max + y_buffer, 105)

            chart = (
                Line(init_opts=opts.InitOpts(width="100%", height="550px"))
                .add_xaxis(norm_df.index.strftime('%Y-%m-%d').tolist())
            )
            
            for col in norm_df.columns:
                chart.add_yaxis(
                    series_name=col,
                    y_axis=norm_df[col].round(2).tolist(),
                    is_symbol_show=False,
                    label_opts=opts.LabelOpts(is_show=False),
                    linestyle_opts=opts.LineStyleOpts(width=2)
                )
                
            chart.set_global_opts(
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                legend_opts=opts.LegendOpts(pos_top="bottom"),
                yaxis_opts=opts.AxisOpts(
                    type_="value",
                    name="Base 100",
                    min_=int(final_min // 10 * 10),
                    max_=int(final_max // 10 * 10 + 20),
                    interval=20,
                    splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(opacity=0.3)),
                    axislabel_opts=opts.LabelOpts(formatter="{value}")
                ),
                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False)
            )
            
            chart.set_series_opts(
                markline_opts=opts.MarkLineOpts(
                    data=[opts.MarkLineItem(y=100, name="Base")],
                    label_opts=opts.LabelOpts(is_show=True, position="end", formatter="100"),
                    linestyle_opts=opts.LineStyleOpts(color="#888", type_="dashed", width=1)
                )
            )
            
            components.html(chart.render_embed(), height=600)

    # Raw Data Expander
    with st.expander("View Raw Data Details"):
        st.dataframe(
            pd.DataFrame(summary).rename(columns={
                "name": "종목명",
                "start_price": "기준일 가격",
                "current_price": "종료일 가격",
                "return": "수익률(%)",
                "date": "기준일",
                "base_date": "비교기준일"
            }),
            use_container_width=True
        )

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Source: FinanceDataReader")