import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import timedelta

# 1. 頁面配置 (必須在最上方)
st.set_page_config(page_title="全球股市 AI 投資助手", layout="wide")

# --- 2. 初始化 Session State (防止 AttributeError) ---
# 確保這些變數在任何地方被調用前都已經存在
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
if 'search_input' not in st.session_state:
    st.session_state.search_input = "2330"
if 'market_type' not in st.session_state:
    st.session_state.market_type = "台股 (TW)"

# --- 3. 隱藏右上角與精簡樣式 CSS ---
st.markdown("""
    <style>
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden;}
    /* 讓水平選單按鈕更醒目 */
    div[data-testid="stSegmentedControl"] button {
        padding: 10px 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. 邏輯函數 (需放在主邏輯被呼叫之前) ---
@st.cache_data(ttl=600) # 縮短快取時間到10分鐘，讓資料更即時
def get_market_ranks():
    tw_list = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2881.TW", "2882.TW", 
               "0050.TW", "0056.TW", "00878.TW", "00919.TW", "00929.TW", "2603.TW", "2303.TW", "2412.TW"]
    us_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "TSM", "COST", "NFLX"]
    
    tw_names = {"2330.TW": "台積電", "2317.TW": "鴻海", "2454.TW": "聯發科", "0050.TW": "元大台灣50", "00878.TW": "國泰永續高股息"}

    def fetch_data(symbols, name_map=None):
        try:
            data = yf.download(symbols, period="2d", progress=False)['Close']
            if data.empty or len(data) < 2: return pd.DataFrame()
            pct_change = ((data.iloc[-1] - data.iloc[-2]) / data.iloc[-2] * 100)
            df = pct_change.reset_index()
            df.columns = ['代號', '漲跌幅(%)']
            if name_map:
                df['名稱'] = df['代號'].map(name_map).fillna(df['代號'])
                df = df[['代號', '名稱', '漲跌幅(%)']]
            return df
        except:
            return pd.DataFrame()

    return fetch_data(tw_list, tw_names), fetch_data(us_list)

@st.cache_data(ttl=600)
def get_full_analysis(input_str, market, i):
    target_symbol = input_str
    if market == "台股 (TW)":
        if input_str.isdigit(): target_symbol = f"{input_str}.TW"
        elif not input_str.upper().endswith(".TW"): target_symbol = f"{input_str.upper()}.TW"
    
    ticker_obj = yf.Ticker(target_symbol)
    df_plot = ticker_obj.history(period="max", interval=i)
    if isinstance(df_plot.columns, pd.MultiIndex): df_plot.columns = df_plot.columns.get_level_values(0)
    
    # 獲取配息
    dividends = ticker_obj.dividends
    return target_symbol.upper(), target_symbol, df_plot, dividends

# --- 5. 主標題與水平選單 ---
st.title("🚀 全球股市 AI 投資助手")

# 使用 segmented_control 取代側邊欄
st.session_state.app_mode = st.segmented_control(
    "功能導航",
    options=["🏠 首頁 (漲跌排行榜)", "📈 個股深度分析"],
    default=st.session_state.app_mode,
    label_visibility="collapsed"
)

st.markdown("---")

# --- 6. 頁面分流 ---
if st.session_state.app_mode == "🏠 首頁 (漲跌排行榜)":
    st.subheader("🏠 市場即時漲跌排行榜")
    tw_df, us_df = get_market_ranks() # 呼叫定義好的函數
    
    def show_table(df, title, is_us=False):
        st.write(f"### {title}")
        event = st.dataframe(
            df.style.format({'漲跌幅(%)': '{:+.2f}%'}),
            use_container_width=True, hide_index=True,
            on_select="rerun", selection_mode="single-row"
        )
        if event.selection and len(event.selection.rows) > 0:
            row_idx = event.selection.rows[0]
            st.session_state.search_input = df.iloc[row_idx]['代號']
            st.session_state.market_type = "美股 (US)" if is_us else "台股 (TW)"
            st.session_state.app_mode = "📈 個股深度分析"
            st.rerun()

    c1, c2 = st.columns(2)
    with c1: show_table(tw_df.sort_values(by='漲跌幅(%)', ascending=False).head(10), "🔥 台股漲幅")
    with c2: show_table(tw_df.sort_values(by='漲跌幅(%)', ascending=True).head(10), "❄️ 台股跌幅")

else:
    # 深度分析頁面參數
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            m_type = st.pills("市場", ["美股 (US)", "台股 (TW)"], default=st.session_state.market_type)
        with col2:
            s_input = st.text_input("代號", value=st.session_state.search_input)
        with col3:
            inv = st.selectbox("週期", ["1d", "1wk", "1mo"])
    
    # 獲取資料與繪圖
    t_sym, s_name, data, divs = get_full_analysis(s_input, m_type, inv)
    st.header(f"📈 {t_sym} 分析報告")
    
    if not data.empty:
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="K線"))
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("暫無數據，請確認代號正確。")
