import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import timedelta

# 1. 頁面配置 (內建參數設定)
st.set_page_config(page_title="全球股市 AI 投資助手", layout="wide", initial_sidebar_state="collapsed")

# --- CSS 樣式：美化介面 ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton button {
        margin-top: 5px;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 初始化 Session State (自定義記憶變數) ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
if 'search_input' not in st.session_state:
    st.session_state.search_input = "0050"
if 'market_type' not in st.session_state:
    st.session_state.market_type = "台股 (TW)"

# --- 2. 核心邏輯：自動獲取 150 檔排行榜 ---
@st.cache_data(ttl=3600)
def get_market_ranks():
    # A. 台股自動清單 (50檔熱門ETF + 50檔核心權值股)
    tw_etf = [f"00{i}.TW" for i in range(50, 100)] 
    tw_stocks = [
        "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2881.TW", "2882.TW", "2303.TW", "2412.TW", "1301.TW",
        "2603.TW", "2002.TW", "2357.TW", "3711.TW", "2408.TW", "2886.TW", "2891.TW", "2884.TW", "2609.TW", "2615.TW",
        "2324.TW", "2353.TW", "2376.TW", "3231.TW", "6669.TW", "3034.TW", "3037.TW", "2379.TW", "2345.TW", "1513.TW",
        "1504.TW", "1519.TW", "2409.TW", "3481.TW", "2301.TW", "2352.TW", "2356.TW", "2360.TW", "2449.TW", "2610.TW",
        "2618.TW", "2880.TW", "2883.TW", "2885.TW", "2887.TW", "2890.TW", "2892.TW", "5871.TW", "5880.TW", "9904.TW"
    ]
    
    # B. 美股熱門 50 檔清單
    us_stocks = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "TSM", "AVGO",
        "COST", "NFLX", "AMD", "INTC", "PYPL", "V", "MA", "JPM", "UNH", "LLY", "ORCL",
        "ADBE", "CRM", "ASML", "PEP", "KO", "CSCO", "TMO", "ABT", "DIS", "NKE", "PFE", 
        "VZ", "XOM", "CVX", "HD", "MCD", "WMT", "JNJ", "MRK", "BAC", "MS", "ABNB", 
        "UBER", "PANW", "SNOW", "PLTR", "SQ", "SHOP", "NOW"
    ]

    def fetch_fast(symbols, is_tw=False):
        try:
            # 使用 threads=True 加速下載，period="3d" 確保穩定性
            data = yf.download(symbols, period="3d", progress=False, threads=True)['Close']
            if data.empty or len(data) < 2: return pd.DataFrame()

            # 抓取最後兩個有效交易日的價格計算漲跌
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            pct = ((latest - prev) / prev * 100)
            
            df = pct.dropna().reset_index()
            df.columns = ['代號', '漲跌幅(%)']
            df['名稱'] = df['代號'].str.replace(".TW", "", regex=False) if is_tw else df['代號']
            return df[['代號', '名稱', '漲跌幅(%)']]
        except:
            return pd.DataFrame()

    return fetch_fast(tw_etf + tw_stocks, is_tw=True), fetch_fast(us_stocks)

# --- 3. 數據處理：個股深度分析 ---
@st.cache_data(ttl=3600)
def get_full_analysis(input_str, market, i):
    target_symbol = input_str
    if market == "台股 (TW)":
        if input_str.isdigit(): target_symbol = f"{input_str}.TW"
        elif not input_str.upper().endswith(".TW"): target_symbol = f"{input_str.upper()}.TW"
    
    ticker_obj = yf.Ticker(target_symbol)
    
    # 抓取 K 線數據
    df_plot = ticker_obj.history(period="max", interval=i)
    if isinstance(df_plot.columns, pd.MultiIndex): df_plot.columns = df_plot.columns.get_level_values(0)
    df_plot.index = pd.to_datetime(df_plot.index).tz_localize(None)
    
    # 抓取名稱
    try:
        info = ticker_obj.info
        stock_name = info.get('longName', info.get('shortName', target_symbol))
    except:
        stock_name = target_symbol

    # 抓取配息
    actions = ticker_obj.actions
    dividends = actions['Dividends'][actions['Dividends'] > 0] if not actions.empty and 'Dividends' in actions.columns else ticker_obj.dividends
    if not dividends.empty: dividends.index = pd.to_datetime(dividends.index).tz_localize(None)

    return target_symbol.upper(), stock_name, df_plot, dividends

# --- 4. 頂部導覽列 ---
h_col1, h_col2, h_col3 = st.columns([5, 1, 1])
with h_col1:
    st.title("🚀 全球股市 AI 投資助手")
with h_col2:
    if st.button("🏠 首頁", key="nav_home", use_container_width=True):
        st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
        st.rerun()
with h_col3:
    if st.button("📈 個股分析", key="nav_depth", use_container_width=True):
        st.session_state.app_mode = "📈 個股深度分析"
        st.rerun()

st.markdown("---")

# --- 5. 主頁面邏輯 ---
if st.session_state.app_mode == "🏠 首頁 (漲跌排行榜)":
    st.subheader("🏠 市場即時漲跌排行榜 (自動追蹤 150 檔熱門標的)")
    with st.spinner('正在分析市場動態...'):
        tw_df, us_df = get_market_ranks()
        
        def show_clickable_table(df, title, is_us=False):
            st.markdown(f"#### {title}")
            # 使用內建參數 hide_index 與 on_select 達成互動
            event = st.dataframe(
                df.style.format({'漲跌幅(%)': '{:+.2f}%'}), 
                use_container_width=True, 
                hide_index=True, 
                on_select="rerun", 
                selection_mode="single-row"
            )
            if event.selection and len(event.selection.rows) > 0:
                selected_idx = event.selection.rows[0]
                st.session_state.search_input = df.iloc[selected_idx]['代號']
                st.session_state.market_type = "美股 (US)" if is_us else "台股 (TW)"
                st.session_state.app_mode = "📈 個股深度分析"
                st.rerun()

        t_col1, t_col2 = st.columns(2)
        if not tw_df.empty:
            with t_col1: show_clickable_table(tw_df.sort_values(by='漲跌幅(%)', ascending=False).head(10), "🔥 台股漲幅榜")
            with t_col2: show_clickable_table(tw_df.sort_values(by='漲跌幅(%)', ascending=True).head(10), "❄️ 台股跌幅榜")
        
        st.markdown("---")
        u_col1, u_col2 = st.columns(2)
        if not us_df.empty:
            with u_col1: show_clickable_table(us_df.sort_values(by='漲跌幅(%)', ascending=False).head(10), "🔥 美股漲幅榜", is_us=True)
            with u_col2: show_clickable_table(us_df.sort_values(by='漲跌幅(%)', ascending=True).head(10), "❄️ 美股跌幅榜", is_us=True)

elif st.session_state.app_mode == "📈 個股深度分析":
    with st.expander("🛠️ 投資參數設定", expanded=True):
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        with c1:
            st.session_state.market_type = st.radio("市場", ["美股 (US)", "台股 (TW)"], index=0 if st.session_state.market_type == "美股 (US)" else 1, horizontal=True)
        with c2:
            st.session_state.search_input = st.text_input("輸入代碼 (例如: 2330 或 NVDA)", st.session_state.search_input).strip()
        with c3:
            interval = st.selectbox("K線週期", ["1d", "1wk", "1mo"])
        with c4:
            period_select = st.selectbox("時間範圍", ["6mo", "1y", "2y", "5y", "max"], index=1)
        
        m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
        with m_col1: ma_short_n = st.slider("短均線 (MA)", 5, 50, 20)
        with m_col2: ma_long_n = st.slider("長均線 (MA)", 20, 200, 60)
        with m_col3: st.markdown("<br>", unsafe_allow_html=True); st.button("🚀 更新分析", use_container_width=True)

    with st.spinner('讀取數據中...'):
        ticker_symbol, stock_name, full_data, dividends = get_full_analysis(st.session_state.search_input, st.session_state.market_type, interval)
        st.subheader(f"📈 {ticker_symbol} {stock_name}")
        
        if not full_data.empty:
            full_data['MA_Short'] = full_data['Close'].rolling(window=ma_short_n).mean()
            full_data['MA_Long'] = full_data['Close'].rolling(window=ma_long_n).mean()
            period_map = {"6mo": 126, "1y": 252, "2y": 504, "5y": 1260, "max": len(full_data)}
            plot_data = full_data.tail(period_map.get(period_select, 252)).copy()

            # 繪圖邏輯
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.3, 0.7])
            fig.add_trace(go.Candlestick(x=plot_data.index, open=plot_data['Open'], high=plot_data['High'], low=plot_data['Low'], close=plot_data['Close'], name="K線"), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['MA_Short'], name="短均線", line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['MA_Long'], name="長均線", line=dict(color='cyan')), row=1, col=1)
            fig.add_trace(go.Bar(x=plot_data.index, y=plot_data['Volume'], name="成交量", marker_color="rgba(100,100,100,0.5)"), row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=800)
            st.plotly_chart(fig, use_container_width=True)

            # 配息表格
            st.subheader("💰 歷史配息")
            if not dividends.empty:
                recent_divs = dividends.sort_index(ascending=False).head(10)
                st.table(recent_divs)
        else:
            st.error("查無數據，請確認代號是否正確。")
