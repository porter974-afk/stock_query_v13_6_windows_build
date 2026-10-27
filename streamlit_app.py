"""Run with: python -m streamlit run streamlit_app.py"""
import plotly.graph_objects as go
import streamlit as st

from excel_export import display_frame, export_excel
from stock_core import fetch_stock, parse_symbols, selected_range, taipei_today


@st.cache_data(ttl=300, max_entries=128, show_spinner=False)
def cached_fetch(symbol, start, end, refresh_token):
    return fetch_stock(symbol, start, end)


def main():
    st.set_page_config(page_title="Stock Query 股票查詢", page_icon="📈", layout="wide")
    st.title("Stock Query 股票查詢")
    st.caption("台美股歷史行情 · 互動線圖 · Excel 報表")
    today = taipei_today()
    raw = st.text_input("股票代碼或名稱", "2330, NVDA, 00905", help="多筆可用中英文逗號或空白分隔；支援台股、美股及台股中文名稱。")
    mode = st.selectbox("查詢日期範圍", ["最近一個月", "指定年份", "自訂日期區間"])
    year, start, end = today.year, today.replace(month=1, day=1), today
    if mode == "指定年份":
        year = st.selectbox("年份", list(range(today.year, 1989, -1)))
    elif mode == "自訂日期區間":
        left, right = st.columns(2)
        start = left.date_input("開始日期", start, min_value=today.replace(year=1990, month=1, day=1), max_value=today)
        end = right.date_input("結束日期", end, min_value=today.replace(year=1990, month=1, day=1), max_value=today)
    refresh = st.checkbox("本次重新下載行情（略過快取）")
    if st.button("查詢", type="primary"):
        try:
            symbols = parse_symbols(raw)
            if not symbols:
                raise ValueError("請先輸入股票代碼")
            start, end, label = selected_range(mode, year, start, end)
        except ValueError as exc:
            st.error(str(exc))
        else:
            token = st.session_state.get("refresh_token", 0) + int(refresh)
            st.session_state.refresh_token = token
            results, failures = [], []
            progress = st.progress(0, text="準備下載行情")
            for index, symbol in enumerate(symbols):
                progress.progress(index / len(symbols), text=f"查詢中：{symbol}")
                try:
                    result = cached_fetch(symbol, start, end, token)
                    content, filename = export_excel(result, label)
                    results.append((result, content, filename))
                except Exception as exc:
                    failures.append(f"{symbol}：{exc}")
            progress.empty()
            st.session_state.query = {"results": results, "failures": failures, "label": label}
    query = st.session_state.get("query")
    if not query:
        st.info("輸入股票與日期後，按「查詢」開始。")
        return
    st.caption(f"以下為上次查詢結果：{query['label']}；變更條件後請再次按「查詢」。行情快取最多保留 5 分鐘。")
    for failure in query["failures"]:
        st.warning(failure)
    results = query["results"]
    if not results:
        st.error("本次查詢沒有成功取得資料。")
        return
    st.success(f"成功取得 {len(results)} 檔股票，失敗 {len(query['failures'])} 檔。")
    index = st.selectbox("選擇查看股票", range(len(results)), format_func=lambda i: f"{results[i][0].name} ({results[i][0].ticker})")
    result, content, filename = results[index]
    frame = result.data
    st.subheader(f"{result.name} · {result.ticker}")
    st.caption(f"實際資料期間：{frame['日期'].min():%Y/%m/%d} ～ {frame['日期'].max():%Y/%m/%d}，共 {len(frame)} 個交易日；價格為原交易幣別，未做匯率轉換。")
    latest = frame.iloc[-1]
    st.metric("最新收盤價", f"{latest['收盤價']:,.2f}")
    fields = st.multiselect("線圖價格", ["收盤價", "開盤價", "最高價", "最低價"], default=["收盤價"])
    if fields:
        fig = go.Figure()
        for field in fields:
            fig.add_trace(go.Scatter(x=frame["日期"], y=frame[field], name=field, mode="lines", hovertemplate="%{x|%Y/%m/%d}<br>%{y:,.2f}<extra>%{fullData.name}</extra>"))
        fig.update_layout(xaxis_title="日期", yaxis_title="價格（原交易幣別）", hovermode="x unified", xaxis_rangeslider_visible=True)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("請至少選擇一種價格以顯示線圖。")
    st.caption("漲跌依區間內前一筆收盤價計算；首筆無前值，以 — 顯示。▲ 表示上漲，▼ 表示下跌。")
    st.dataframe(display_frame(frame), width="stretch", hide_index=True)
    st.download_button("下載此股票 Excel", content, filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == "__main__":
    main()
