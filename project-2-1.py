import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import timedelta

# 頁面配置
st.set_page_config(page_title="全球股市 AI 投資助手", layout="wide")

# --- 精確 CSS 控制 ---
st.markdown("""
    <style>
    /* 隱藏右側工具欄與底部浮水印 */
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden;}
    
    /* 讓水平選單按鈕更醒目 */
    div[data-testid="stSegmentedControl"] button {
        padding: 10px 20px;
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- (此處保留您的 get_market_ranks 與 get_full_analysis 函數) ---

# --- 主標題 ---
st.title("🚀 全球股市 AI 投資助手")

# --- 🌟 關鍵修改：標題下方的水平選單 ---
# 使用 segmented_control 做出像導覽列的效果
app_mode = st.segmented_control(
    "功能導航",
    options=["🏠 首頁 (漲跌排行榜)", "📈 個股深度分析"],
    default="🏠 首頁 (漲跌排行榜)",
    label_visibility="collapsed" # 隱藏標籤，讓它看起來更像導覽列
)

st.markdown("---") # 分隔線

# --- 1. 首頁邏輯 ---
if app_mode == "🏠 首頁 (漲跌排行榜)":
    st.subheader("🏠 市場即時漲跌排行榜")
    st.info("💡 提示：點擊表格中的代號，系統會自動切換至深度分析頁面。")
    
    with st.spinner('正在分析市場動態...'):
        tw_df, us_df = get_market_ranks()
        
        def show_clickable_table(df, title, is_us=False):
            st.write(f"### {title}")
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
                # 切換狀態後提示用戶切換選單
                st.toast(f"已選取 {st.session_state.search_input}，請點選上方「個股深度分析」", icon="📈")

        col1, col2 = st.columns(2)
        with col1: show_clickable_table(tw_df.sort_values(by='漲跌幅(%)', ascending=False).head(10), "🔥 台股漲幅榜")
        with col2: show_clickable_table(tw_df.sort_values(by='漲跌幅(%)', ascending=True).head(10), "❄️ 台股跌幅榜")

# --- 2. 深度分析邏輯 ---
else:
    # 參數設定改為橫向排列的區塊
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 2])
        with c1:
            m_type = st.pills("市場", ["美股 (US)", "台股 (TW)"], default=st.session_state.market_type)
        with c2:
            s_input = st.text_input("代號", value=st.session_state.search_input).strip()
        with c3:
            inv = st.selectbox("週期", ["1d", "1wk", "1mo"])
        with c4:
            per = st.select_slider("範圍", options=["6mo", "1y", "2y", "5y", "max"], value="1y")

    # 執行數據分析
    ticker_symbol, stock_name, full_data, dividends, _ = get_full_analysis(s_input, m_type, inv)
    
    st.header(f"📈 {ticker_symbol} {stock_name} 深度報告")
    
    # ... (此處接續原本的 Plotly 繪圖代碼與配息表格) ...
