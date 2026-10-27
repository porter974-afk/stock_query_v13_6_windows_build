"""UI-independent stock lookup, date validation and numeric price processing."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf


def taipei_today():
    return datetime.now(ZoneInfo("Asia/Taipei")).date()


def parse_symbols(text):
    return list(dict.fromkeys(s.strip().upper() for s in re.split(r"[,，;；\s]+", text) if s.strip()))


def resolve_symbol(text):
    symbol = text.strip().upper()
    if not symbol:
        raise ValueError("請輸入股票代碼或名稱")
    aliases = {"日月光": "3711", "鴻海": "2317", "台積電": "2330", "輝達": "NVDA", "特斯拉": "TSLA"}
    if symbol in aliases:
        return aliases[symbol]
    if re.fullmatch(r"[A-Z0-9.^=\-]+", symbol):
        return symbol
    import twstock
    exact = [code for code, info in twstock.codes.items() if symbol == info.name]
    matches = exact or [code for code, info in twstock.codes.items() if symbol in info.name]
    if len(matches) > 1:
        raise ValueError("名稱符合多檔股票，請改輸入完整名稱或股票代碼")
    if matches:
        return matches[0]
    raise ValueError(f"找不到股票名稱：{symbol}")


def selected_range(mode, year=None, start=None, end=None, today=None):
    today = today or taipei_today()
    if mode == "最近一個月":
        return None, None, "近一個月"
    if mode == "指定年份":
        if year is None or not 1990 <= year <= today.year:
            raise ValueError("年份必須介於 1990 年與今年之間")
        return date(year, 1, 1), min(date(year, 12, 31), today), str(year)
    if mode != "自訂日期區間":
        raise ValueError("未知的日期模式")
    if not isinstance(start, date) or not isinstance(end, date):
        raise ValueError("請選擇開始與結束日期")
    if start > end:
        raise ValueError("開始日期不能晚於結束日期")
    if end > today:
        raise ValueError("查詢日期不能晚於今天")
    return start, end, f"{start:%Y%m%d}-{end:%Y%m%d}"


@dataclass
class StockResult:
    symbol: str
    ticker: str
    name: str
    data: pd.DataFrame


def prepare_history(history):
    required = ["Open", "High", "Low", "Close", "Volume"]
    if history.empty or not set(required).issubset(history.columns):
        raise ValueError("查無完整股價資料")
    frame = history[required].copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    frame.index.name = "日期"
    frame = frame.sort_index().loc[lambda x: ~x.index.duplicated(keep="last")]
    for col in required:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["Close"])
    if frame.empty:
        raise ValueError("查無有效收盤價")
    frame = frame.rename(columns={"Open": "開盤價", "High": "最高價", "Low": "最低價", "Close": "收盤價", "Volume": "成交量"})
    frame["漲跌價"] = frame["收盤價"].diff()
    frame["漲跌幅(%)"] = frame["收盤價"].pct_change(fill_method=None).mul(100).round(2)
    frame["漲跌幅(%)"] = frame["漲跌幅(%)"].replace([float("inf"), -float("inf")], float("nan"))
    return frame.reset_index()


def fetch_stock(user_input, start=None, end=None):
    if (start is None) != (end is None):
        raise ValueError("開始與結束日期必須同時指定")
    if start is not None:
        selected_range("自訂日期區間", start=start, end=end)
    symbol = resolve_symbol(user_input)
    candidates = [f"{symbol}.TW", f"{symbol}.TWO"] if symbol.isdigit() else [symbol]
    errors = []
    for ticker in candidates:
        try:
            options = {"period": "1mo"} if start is None else {"start": start.isoformat(), "end": (end + timedelta(days=1)).isoformat()}
            history = yf.Ticker(ticker).history(**options, auto_adjust=False, timeout=20, raise_errors=True)
            if history.empty:
                errors.append(f"{ticker}：指定期間無資料")
                continue
            frame = prepare_history(history)
            name = symbol
            if ticker.endswith((".TW", ".TWO")):
                import twstock
                info = twstock.codes.get(symbol.split(".")[0])
                if info:
                    name = info.name
            return StockResult(symbol, ticker, name, frame)
        except Exception as exc:
            errors.append(f"{ticker}：{exc}")
    raise ValueError("無法取得股價，請確認代碼、交易日期或稍後重試。" + "；".join(errors))
