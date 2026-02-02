import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import timedelta

# 1. 頁面配置
st.set_page_config(page_title="全球股市 AI 投資助手", layout="wide", initial_sidebar_state="collapsed")

# --- CSS 樣式 ---
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

# --- 建立台股中文名稱對照表 (用於首頁與分析) ---
TW_NAMES_MAP = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
    "2382.TW": "廣達", "2881.TW": "富邦金", "2882.TW": "國泰金", "2303.TW": "聯電",
    "2412.TW": "中華電", "1301.TW": "台塑", "2603.TW": "長榮", "2002.TW": "中鋼",
    "2357.TW": "華碩", "3711.TW": "日月光", "2408.TW": "南亞科", "2886.TW": "兆豐金",
    "2891.TW": "中信金", "2884.TW": "玉山金", "2609.TW": "陽明", "2615.TW": "萬海",
    "0050.TW": "元大台灣50", "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息",
    "00919.TW": "群益台灣精選高息", "00929.TW": "復華台灣科技優息", "00940.TW": "元大台灣價值高息"
}

# --- 初始化 Session State ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
if 'search_input' not in st.session_state:
    st.session_state.search_input = "0050"
if 'market_type' not in st.session_state:
    st.session_state.market_type = "台股 (TW)"

# --- 2. 核心邏輯：獲取排行榜 (含中文處理) ---
@st.cache_data(ttl=3600)
def get_market_ranks():
    tw_list = [f"00{i}.TW" for i in range(50, 100)] + list(TW_NAMES_MAP.keys())
    # 去除重複並保持清單
    tw_list = list(set(tw_list))
    
    us_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "TSM", "AVGO", "COST"]

    def fetch_fast(symbols, is_tw=False):
        try:
            data = yf.download(symbols, period="2d", progress=False, threads=True)['Close']
            if data.empty or len(data) < 2: return pd.DataFrame()
            latest, prev = data.iloc[-1], data.iloc[-2]
            pct = ((latest - prev) / prev * 100)
            df = pct.dropna().reset_index()
            df.columns = ['代號', '漲跌幅(%)']
            
            if is_tw:
                # 優先從對照表找中文，找不到則顯示代號
                df['名稱'] = df['代號'].map(TW_NAMES_MAP).fillna(df['代號'].str.replace(".TW", "", regex=False))
            else:
                df['名稱'] = df['代號']
            return df[['代號', '名稱', '漲跌幅(%)']]
        except: return pd.DataFrame()

    return fetch_fast(tw_list, is_tw=True), fetch_fast(us_list)

# --- 3. 數據處理：個股深度分析 (含中文名稱抓取) ---
@st.cache_data(ttl=3600)
def get_full_analysis(input_str, market, i):
    target_symbol = input_str
    if market == "台股 (TW)":
        if input_str.isdigit(): target_symbol = f"{input_str}.TW"
        elif not input_str.upper().endswith(".TW"): target_symbol = f"{input_str.upper()}.TW"
    
    ticker_obj = yf.Ticker(target_symbol)
    df_plot = ticker_obj.history(period="max", interval=i)
    if isinstance(df_plot.columns, pd.MultiIndex): df_plot.columns = df_plot.columns.get_level_values(0)
    df_plot.index = pd.to_datetime(df_plot.index).tz_localize(None)
    
    # --- 中文名稱邏輯 ---
    stock_name = TW_NAMES_MAP.get(target_symbol.upper(), "") # 1. 先查對照表
    if not stock_name:
        try:
            # 2. 若對照表沒有，嘗試抓 info
            info = ticker_obj.info
            stock_name = info.get('shortName', target_symbol.upper())
        except:
            stock_name = target_symbol.upper()

    actions = ticker_obj.actions
    dividends = actions['Dividends'][actions['Dividends'] > 0] if not actions.empty and 'Dividends' in actions.columns else ticker_obj.dividends
    if not dividends.empty: dividends.index = pd.to_datetime(dividends.index).tz_localize(None)

    return target_symbol.upper(), stock_name, df_plot, dividends

# --- 4. 頂部導覽列 ---
h_col1, h_col2, h_col3 = st.columns([5, 1, 1])
with h_col1: st.title("🚀 全球股市 AI 投資助手")
with h_col2:
    if st.button("🏠 首頁", key="nav_home", use_container_width=True):
        st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"; st.rerun()
with h_col3:
    if st.button("📈 個股分析", key="nav_depth", use_container_width=True):
        st.session_state.app_mode = "📈 個股深度分析"; st.rerun()

st.markdown("---")

# --- 5. 主頁面邏輯 ---
if st.session_state.app_mode == "🏠 首頁 (漲跌排行榜)":
    st.subheader("🏠 市場即時漲跌排行榜")
    with st.spinner('數據同步中...'):
        tw_df, us_df = get_market_ranks()
        def show_table(df, title, is_us=False):
            st.markdown(f"#### {title}")
            event = st.dataframe(df.style.format({'漲跌幅(%)': '{:+.2f}%'}), use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if event.selection and len(event.selection.rows) > 0:
                selected_idx = event.selection.rows[0]
                st.session_state.search_input = df.iloc[selected_idx]['代號']
                st.session_state.market_type = "美股 (US)" if is_us else "台股 (TW)"
                st.session_state.app_mode = "📈 個股深度分析"; st.rerun()

        col1, col2 = st.columns(2)
        if not tw_df.empty:
            with col1: show_table(tw_df.sort_values(by='漲跌幅(%)', ascending=False).head(10), "🔥 台股漲幅榜")
            with col2: show_table(tw_df.sort_values(by='漲跌幅(%)', ascending=True).head(10), "❄️ 台股跌幅榜")
        st.markdown("---")
        col3, col4 = st.columns(2)
        if not us_df.empty:
            with col3: show_table(us_df.sort_values(by='漲跌幅(%)', ascending=False).head(10), "🔥 美股漲幅榜", is_us=True)
            with col4: show_table(us_df.sort_values(by='漲跌幅(%)', ascending=True).head(10), "❄️ 美股跌幅榜", is_us=True)

elif st.session_state.app_mode == "📈 個股深度分析":
    with st.expander("🛠️ 投資參數設定", expanded=True):
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        with c1: st.session_state.market_type = st.radio("市場", ["美股 (US)", "台股 (TW)"], index=0 if st.session_state.market_type == "美股 (US)" else 1, horizontal=True)
        with c2: st.session_state.search_input = st.text_input("輸入代碼", st.session_state.search_input).strip()
        with c3: interval = st.selectbox("週期", ["1d", "1wk", "1mo"])
        with c4: period_select = st.selectbox("範圍", ["1y", "2y", "5y", "max"], index=0)
        
        m_col1, m_col2 = st.columns(2)
        with m_col1: ma_s = st.slider("短均線", 5, 50, 20)
        with m_col2: ma_l = st.slider("長均線", 20, 200, 60)
        st.button("🚀 更新分析", use_container_width=True)

    with st.spinner('正在分析...'):
        symbol, name, data, divs = get_full_analysis(st.session_state.search_input, st.session_state.market_type, interval)
        st.subheader(f"📈 {symbol} {name}")
        
        if not data.empty:
            data['MA_S'] = data['Close'].rolling(ma_s).mean()
            data['MA_L'] = data['Close'].rolling(ma_l).mean()
            plot_data = data.tail(252) # 預設顯示一年
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.3, 0.7])
            fig.add_trace(go.Candlestick(x=plot_data.index, open=plot_data['Open'], high=plot_data['High'], low=plot_data['Low'], close=plot_data['Close'], name="K線"), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['MA_S'], name=f"MA{ma_s}", line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['MA_L'], name=f"MA{ma_l}", line=dict(color='cyan')), row=1, col=1)
            fig.add_trace(go.Bar(x=plot_data.index, y=plot_data['Volume'], name="成交量", marker_color="gray"), row=2, col=1)
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=700)
            st.plotly_chart(fig, use_container_width=True)
            
            if not divs.empty:
                st.subheader("💰 歷史配息")
                st.table(divs.sort_index(ascending=False).head(10))
        else:
            st.error("查無數據。")
