import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import timedelta

# 1. 頁面配置
st.set_page_config(page_title="全球股市 AI 投資助手", layout="wide", initial_sidebar_state="collapsed")

# --- 隱藏側邊欄與右上角工具列的 CSS ---
st.markdown("""
    <style>
    /* 隱藏側邊欄 */
    [data-testid="stSidebar"] {display: none;}
    /* 隱藏右側工具欄 */
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden;}
    /* 標題與按鈕的垂直對齊 */
    .stButton button {
        margin-top: 5px;
        border-radius: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 初始化 Session State ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
if 'search_input' not in st.session_state:
    st.session_state.search_input = "0050"
if 'market_type' not in st.session_state:
    st.session_state.market_type = "台股 (TW)"

# --- 3. 邏輯函數 (完全保留您的原始代碼) ---
@st.cache_data(ttl=3600)
def get_market_ranks():
    tw_list = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2881.TW", "2882.TW", 
               "0050.TW", "0056.TW", "00878.TW", "00919.TW", "00929.TW", "2603.TW", "2303.TW", "2412.TW"]
    us_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "TSM", "AVGO", "COST", "NFLX"]
    
    tw_names = {
        "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
        "2382.TW": "廣達", "2881.TW": "富邦金", "2882.TW": "國泰金", "0050.TW": "元大台灣50",
        "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息", "00919.TW": "群益台灣精選高息",
        "00929.TW": "復華台灣科技優息", "2603.TW": "長榮", "2303.TW": "聯電", "2412.TW": "中華電"
    }

    def fetch_data(symbols, name_map=None):
        try:
            data = yf.download(symbols, period="2d", progress=False)['Close']
            if len(data) < 2: return pd.DataFrame()
            pct_change = ((data.iloc[-1] - data.iloc[-2]) / data.iloc[-2] * 100)
            df = pct_change.reset_index()
            df.columns = ['代號', '漲跌幅(%)']
            if name_map:
                df['名稱'] = df['代號'].map(name_map).fillna("未知")
                df = df[['代號', '名稱', '漲跌幅(%)']]
            return df
        except:
            return pd.DataFrame()

    return fetch_data(tw_list, tw_names), fetch_data(us_list)

@st.cache_data(ttl=3600)
def get_full_analysis(input_str, market, i):
    target_symbol = input_str
    if market == "台股 (TW)":
        if input_str.isdigit(): target_symbol = f"{input_str}.TW"
        elif not input_str.upper().endswith(".TW"): target_symbol = f"{input_str.upper()}.TW"
    
    ticker_obj = yf.Ticker(target_symbol)
    tw_manual_names = {
        "2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "2308.TW": "台達電",
        "2382.TW": "廣達", "2881.TW": "富邦金", "2882.TW": "國泰金", "0050.TW": "元大台灣50",
        "0056.TW": "元大高股息", "00878.TW": "國泰永續高股息", "00919.TW": "群益台灣精選高息",
        "00929.TW": "復華台灣科技優息", "2603.TW": "長榮", "2303.TW": "聯電", "2412.TW": "中華電"
    }
    
    stock_name = tw_manual_names.get(target_symbol.upper(), "")
    if not stock_name:
        try:
            info = ticker_obj.info
            stock_name = info.get('longName', info.get('shortName', ''))
        except:
            stock_name = ""

    fx_history = yf.download("USDTWD=X", period="max", interval="1d", progress=False)
    if isinstance(fx_history.columns, pd.MultiIndex): fx_history.columns = fx_history.columns.get_level_values(0)
    fx_history.index = pd.to_datetime(fx_history.index).tz_localize(None)
    
    df_plot = ticker_obj.history(period="max", interval=i)
    if isinstance(df_plot.columns, pd.MultiIndex): df_plot.columns = df_plot.columns.get_level_values(0)
    df_plot.index = pd.to_datetime(df_plot.index).tz_localize(None)
    
    actions = ticker_obj.actions
    dividends = actions['Dividends'][actions['Dividends'] > 0] if not actions.empty and 'Dividends' in actions.columns else ticker_obj.dividends
    if not dividends.empty: dividends.index = pd.to_datetime(dividends.index).tz_localize(None)

    return target_symbol.upper(), stock_name, df_plot, dividends, fx_history

# --- 4. 頂部標題與導航按鈕列 ---
header_col, btn_home_col, btn_analysis_col = st.columns([5, 1, 1])

with header_col:
    st.title("🚀 全球股市 AI 投資助手")

with btn_home_col:
    if st.button("🏠 回首頁", use_container_width=True):
        st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
        st.rerun()

with btn_analysis_col:
    if st.button("📈 個股分析", use_container_width=True):
        st.session_state.app_mode = "📈 個股深度分析"
        st.rerun()

st.markdown("---")

# --- 5. 主頁面邏輯 (與原代碼一致) ---

if st.session_state.app_mode == "🏠 首頁 (漲跌排行榜)":
    st.subheader("🏠 市場即時漲跌排行榜")
    # ... (此處保留您的漲跌排行榜表格邏輯) ...
    with st.spinner('正在分析市場動態...'):
        tw_df, us_df = get_market_ranks()
        def show_clickable_table(df, title, is_us=False):
            st.subheader(title)
            event = st.dataframe(df.style.format({'漲跌幅(%)': '{:+.2f}%'}), use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
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
    # --- 彈出式參數設定區 ---
    with st.expander("🛠️ 點擊展開：投資參數設定", expanded=True):
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        with c1:
            st.session_state.market_type = st.radio("市場", ["美股 (US)", "台股 (TW)"], index=0 if st.session_state.market_type == "美股 (US)" else 1, horizontal=True)
        with c2:
            st.session_state.search_input = st.text_input("輸入代號", st.session_state.search_input).strip()
        with c3:
            interval = st.selectbox("週期", ["1d", "1wk", "1mo"])


