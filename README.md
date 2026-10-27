# Stock Query：Windows 與 Streamlit 網頁版

原本的 `stock_query_v13_6.py`、Windows 打包腳本、spec 與既有 EXE 檔案保持不變。
網頁版使用獨立的 `stock_core.py`（行情與數值計算）、`excel_export.py`（記憶體報表）及 `streamlit_app.py`（介面），不會匯入或啟動 Tkinter。

## Windows 本機安裝與啟動

建議使用 Python 3.12，在專案資料夾開啟 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

瀏覽器開啟 http://localhost:8501。使用上面的完整執行路徑，不必啟用虛擬環境或調整 PowerShell 執行原則。停止服務請在終端機按 Ctrl+C。

## 操作

1. 輸入 `2330, NVDA, 00905`，多筆可用逗號、中文逗號或空白分隔；也可輸入台積電等名稱。
2. 選擇最近一個月、指定年份或自訂日期區間，再按「查詢」。結束日期包含當天，休市日沒有交易資料。
3. 選擇股票及開高低收線條，滑鼠移動查看價格、拖曳縮放、使用下方時間軸調整區間。
4. 按「下載此股票 Excel」。報表直接下載至瀏覽器，不會寫入原桌面程式的 output 資料夾。
5. 行情快取最多保留五分鐘；要重新下載，勾選「本次重新下載行情」再查詢。

切換圖表與下載時保留上次查詢結果。修改輸入條件後須再按查詢；部分股票失敗不影響其他結果。
各股票分開畫圖，價格維持原交易幣別。使用 `auto_adjust=False`，漲跌依區間內相鄰交易日的收盤價計算，未對除權息調整；首筆網頁顯示 —，Excel 沿用原版的 0／0.00%。
Excel 保留原版八欄、日期星期、▲／▼、紅漲綠跌、凍結窗格與成交量格式。

## 驗證

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

自動測試以固定資料檢查日期驗證、數值計算、上市／上櫃備援、結束日期包含當天、Excel 樣式，以及 Streamlit 查詢與互動後的結果保留。
手動可查詢台股、美股、上櫃股、無效代碼及無交易日區間，確認圖表與 Excel 內容。
實際行情需網路連線，Yahoo Finance 資料可用性與限流可能影響查詢，無資料時可調整日期或稍後重試。
`lxml` 為台股名稱查找套件的解析依賴；`tzdata` 讓 Windows 及不同時區的主機均以台北日期判斷今天。
