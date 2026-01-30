# stock-analysis-tool
🚀 全球股市 AI 投資助手 (Global Stock AI Assistant)
這是一個基於 Python 與 Streamlit 開發的即時股市分析工具。整合了 Yahoo Finance 數據，提供台股與美股的即時漲跌排行榜、動態 K 線圖、技術指標（均線）以及歷史配息分析。
https://stock-analysis-tool-2001.streamlit.app/

✨ 核心功能
📊 即時市場看板：自動抓取台股與美股的前十大漲、跌幅排行榜。

🔍 個股深度分析：支援輸入代號或名稱，自動匹配中文名稱。

📈 動態 K 線圖表：

整合成交量與移動平均線（MA）。

優化 Hover 提示：針對日、週、月不同週期自動格式化日期顯示。

成交量追蹤：同步顯示滑鼠游標處的成交數據。

💰 殖利率預估：自動計算歷史配息、推估發放日及年化殖利率。

📱 響應式設計：完美支援電腦與手機瀏覽。

🛠️ 快速上手
1. 複製儲存庫
Bash
git clone https://github.com/你的用戶名/你的專案名稱.git
cd 你的專案名稱
2. 安裝必要套件
請確保你的電腦已安裝 Python 3.8+，然後執行：

Bash
pip install -r requirements.txt
3. 啟動程式
Bash
streamlit run app.py
📦 依賴套件 (requirements.txt)
本專案使用了以下強大的開源庫：

streamlit: 網頁介面開發

yfinance: 金融數據抓取

pandas: 數據處理與分析

plotly: 高互動性 K 線圖表

numpy: 數值計算

