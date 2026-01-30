import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import timedelta

# 頁面配置 (預設收起側邊欄)
st.set_page_config(page_title="全球股市 AI 投資助手", layout="wide", initial_sidebar_state="collapsed")

# --- CSS 樣式：隱藏側邊欄並美化導航按鈕 ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    .stButton button {
        margin-top: 5px;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 初始化 Session State ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
if 'search_input' not in st.session_state:
    st.session_state.search_input = "0050"
if 'market_type' not in st.session_state:
    st.session_state.market_type = "台股 (TW)"

# --- 1. 邏輯函數：獲取排行榜 (完全保留) ---
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
        except: return pd.DataFrame()

    return fetch_data(tw_list, tw_names), fetch_data(us_list)

# --- 2. 數據處理核心 (完全保留) ---
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
        except: stock_name = ""

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

# --- 3. 頂部導航列 (新增：標題旁邊做按鈕) ---
h_col1, h_col2, h_col3 = st.columns([5, 1, 1])
with h_col1:
    st.title("🚀 全球股市 AI 投資助手")
with h_col2:
    if st.button("🏠 首頁", use_container_width=True):
        st.session_state.app_mode = "🏠 首頁 (漲跌排行榜)"
        st.rerun()
with h_col3:
    if st.button("📈 個股分析", use_container_width=True):
        st.session_state.app_mode = "📈 個股深度分析"
        st.rerun()

st.markdown("---")

# --- 4. 主頁面邏輯 ---

if st.session_state.app_mode == "🏠 首頁 (漲跌排行榜)":
    st.subheader("🏠 市場即時漲跌排行榜")
    st.info("💡 提示：點擊表格中的「代號」或任何位置，即可自動跳轉至該股深度分析。")
    
    with st.spinner('正在分析市場動態...'):
        tw_df, us_df = get_market_ranks()
        
        def show_clickable_table(df, title, is_us=False):
            st.markdown(f"#### {title}")
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
    # --- 頂部參數設定區 ---
    with st.expander("🛠️ 投資參數設定", expanded=True):
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        with c1:
            st.session_state.market_type = st.radio("市場", ["美股 (US)", "台股 (TW)"], index=0 if st.session_state.market_type == "美股 (US)" else 1, horizontal=True)
        with c2:
            st.session_state.search_input = st.text_input("輸入名稱或代號", st.session_state.search_input).strip()
        with c3:
            interval = st.selectbox("K線週期", ["1d", "1wk", "1mo"])
        with c4:
            period_select = st.selectbox("時間範圍", ["6mo", "1y", "2y", "5y", "max"], index=1)
        
        m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
        with m_col1: ma_short_n = st.slider("短均線 (MA)", 5, 50, 20)
        with m_col2: ma_long_n = st.slider("長均線 (MA)", 20, 200, 60)
        with m_col3: st.markdown("<br>", unsafe_allow_html=True); st.button("🚀 開始分析", use_container_width=True)

    ticker_symbol, stock_name, full_data, dividends, fx_history = get_full_analysis(
        st.session_state.search_input, st.session_state.market_type, interval)
    
    st.subheader(f"📈 {ticker_symbol} {stock_name} 深度分析報告")
    
    if not full_data.empty:
        full_data['MA_Short'] = full_data['Close'].rolling(window=ma_short_n).mean()
        full_data['MA_Long'] = full_data['Close'].rolling(window=ma_long_n).mean()
        
        period_map = {"6mo": 126, "1y": 252, "2y": 504, "5y": 1260, "max": len(full_data)}
        plot_data = full_data.tail(period_map.get(period_select, 252)).copy()

        hover_dates = []
        for d in plot_data.index:
            if interval == "1wk":
                start_w = d - timedelta(days=d.weekday()); end_w = start_w + timedelta(days=4)
                hover_dates.append(f"{start_w.strftime('%m/%d')} - {end_w.strftime('%m/%d')}")
            elif interval == "1mo": hover_dates.append(f"{d.strftime('%Y/%m')}")
            else: hover_dates.append(f"{d.strftime('%Y/%m/%d')}")

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.3, 0.7])
        
        # 1. K線 Trace (補回高低價)
        fig.add_trace(go.Candlestick(
            x=plot_data.index, 
            open=plot_data['Open'], high=plot_data['High'], 
            low=plot_data['Low'], close=plot_data['Close'], 
            name="K線",
            customdata=hover_dates,
            hovertemplate="<b>時間: %{customdata}</b><br>開盤: %{open:.2f}<br>最高: %{high:.2f}<br>最低: %{low:.2f}<br>收盤: %{close:.2f}<extra></extra>"
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['MA_Short'], name="短均線", line=dict(color='orange'), hoverinfo="skip"), row=1, col=1)
        fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['MA_Long'], name="長均線", line=dict(color='cyan'), hoverinfo="skip"), row=1, col=1)
        
        # 3. 成交量 Trace (同步日期顯示)
        fig.add_trace(go.Bar(
            x=plot_data.index, y=plot_data['Volume'], 
            name="成交量", marker_color="rgba(100,100,100,0.5)",
            customdata=hover_dates,
            hovertemplate="<b>時間: %{customdata}</b><br>成交量: %{y:,.0f}<extra></extra>"
        ), row=2, col=1)
        
        fig.update_xaxes(showspikes=True, spikemode='across', spikedash='dash', spikecolor="grey")
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=800, hovermode="x")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("💰 歷史配息與殖利率")
        if not dividends.empty:
            recent_divs = dividends.sort_index(ascending=False).head(13)
            curr_price = full_data['Close'].iloc[-1]
            rows = []
            for date, val in recent_divs.items():
                pay_offset = 28 if st.session_state.market_type == "台股 (TW)" else 20
                est_pay_date = (pd.to_datetime(date) + timedelta(days=pay_offset)).strftime('%Y-%m-%d')
                freq = 12 if "00929" in ticker_symbol else (2 if any(x in ticker_symbol for x in ["0050", "0056"]) else 4)
                rows.append({
                    "除息日期": date.strftime('%Y-%m-%d'),
                    "推估發放日": est_pay_date,
                    "配息": val,
                    "預估年化殖利率": f"{(val * freq / curr_price) * 100:.2f}%"
                })
            st.table(pd.DataFrame(rows))
    else:
        st.error("查無數據，請確認代號正確性。")

# 這裡保留您的註解內容
# D:\行銷科技\python\project\project-2-1.py
# streamlit run project/project-2-1.py
