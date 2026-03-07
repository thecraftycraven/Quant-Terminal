import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import concurrent.futures
import requests
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components
import warnings
warnings.filterwarnings("ignore")

# -- SESSION STATE INIT --------------------------------------------
for _k, _v in {"portfolio": [], "alert_config": {"enabled": False}, "scan_mode": "Core 9", "trade_notes": ""}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# -- PAGE CONFIG ---------------------------------------------------
st.set_page_config(layout="wide", page_title="QUANT TERMINAL v3", page_icon="*")

# -- MARKET CLOCK -------------------------------------------------
est_zone      = ZoneInfo("America/New_York")
now_est       = datetime.now(est_zone)
time_str      = now_est.strftime("%H:%M:%S ET")
date_str      = now_est.strftime("%d %b %Y").upper()
is_weekend    = now_est.weekday() >= 5
is_open       = datetime.strptime("09:30", "%H:%M").time() <= now_est.time() <= datetime.strptime("16:00", "%H:%M").time()
market_status = "OPEN" if (not is_weekend and is_open) else "CLOSED"
status_color  = "#00CC00" if market_status == "OPEN" else "#CC0000"

# -- CSS -----------------------------------------------------------
st.markdown("""
<style>
@import url("https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;600;700&display=swap");
*, *::before, *::after { font-family: "Source Code Pro", "Courier New", monospace !important; }
html, body, [class*="stApp"] { background-color: #000000 !important; color: #CCCCCC; }
.stApp { background-color: #000000; padding-bottom: 60px; }
.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header, .stDeployButton { visibility: hidden !important; }
.bbg-status { display:flex; justify-content:space-between; align-items:center; background:#000; border-bottom:2px solid #FF8000; padding:4px 12px; position:sticky; top:0; z-index:9999; height:28px; }
.bbg-status-l { font-size:11px; font-weight:700; letter-spacing:1.5px; }
.bbg-status-c { color:#FF8000; font-size:10px; letter-spacing:2px; font-weight:600; }
.bbg-status-r { color:#AAAAAA; font-size:10px; text-align:right; }
.stTabs [data-baseweb="tab-list"] { background:#000 !important; border-bottom:1px solid #333 !important; gap:0 !important; }
.stTabs [data-baseweb="tab"] { background:#000 !important; color:#555 !important; font-size:10px !important; letter-spacing:1.5px !important; padding:6px 16px !important; border-radius:0 !important; border:none !important; }
.stTabs [aria-selected="true"] { background:#111 !important; color:#FF8000 !important; border-bottom:2px solid #FF8000 !important; }
.stTabs [data-baseweb="tab-panel"] { padding:0 !important; }
.bbg-panel { border:1px solid #222; background:#0A0A0A; margin-bottom:4px; }
.bbg-panel-hdr { background:#111; color:#FF8000; font-size:10px; font-weight:700; letter-spacing:2px; padding:4px 8px; border-bottom:1px solid #333; text-transform:uppercase; }
.bbg-panel-body { padding:6px 8px; }
.bbg-scroll { max-height:400px; overflow-y:auto; }
.bbg-tbl { width:100%; border-collapse:collapse; font-size:10px; }
.bbg-tbl th { background:#111; color:#FF8000; font-size:9px; font-weight:600; padding:5px 6px; border-bottom:1px solid #FF8000; text-align:right; letter-spacing:1px; white-space:nowrap; }
.bbg-tbl th.l { text-align:left; }
.bbg-tbl td { padding:4px 6px; border-bottom:1px solid #0D0D0D; text-align:right; color:#CCC; white-space:nowrap; }
.bbg-tbl td.l { text-align:left; color:#FF8000; font-weight:700; }
.bbg-tbl td.sec { text-align:left; color:#555; font-size:9px; }
.bbg-tbl tr:hover td { background:#0D0D0D; }
.sig-buy  { background:linear-gradient(135deg,#003300,#001a00); border:2px solid #00FF41; border-radius:3px; padding:16px; text-align:center; margin:8px 0; }
.sig-sell { background:linear-gradient(135deg,#330000,#1a0000); border:2px solid #FF4444; border-radius:3px; padding:16px; text-align:center; margin:8px 0; }
.sig-wait { background:linear-gradient(135deg,#1a1000,#0d0800); border:2px solid #FFA500; border-radius:3px; padding:16px; text-align:center; margin:8px 0; }
.sig-fat  { background:linear-gradient(135deg,#001a33,#000d1a); border:2px solid #00CCFF; border-radius:3px; padding:16px; text-align:center; margin:8px 0; }
.rat-box  { background:#050505; border-left:3px solid #FF8000; padding:12px 16px; margin:8px 0; font-size:0.82rem; line-height:1.7; }
.stMetric { background:#0a0a0a; border:1px solid #1a1a1a; padding:10px; border-radius:2px; }
[data-testid="stMetricValue"] { color:#FF8000 !important; font-size:1.3rem !important; }
[data-testid="stMetricLabel"] { color:#888 !important; font-size:0.7rem !important; }
.stButton>button { background:#0a0a0a; color:#00FF41; border:1px solid #00FF41; border-radius:2px; letter-spacing:1px; width:100%; }
.stButton>button:hover { background:#003300; }
.stProgress > div > div { background:#00FF41 !important; }
section[data-testid="stSidebar"] { background:#050505 !important; border-right:1px solid #1a1a1a; }
.stTextInput>div>div>input { background:#0a0a0a !important; color:#00FF41 !important; border:1px solid #333 !important; }
.stSelectbox>div>div { background:#0a0a0a !important; color:#00FF41 !important; border:1px solid #333 !important; }
.bbg-hm { display:grid; grid-template-columns:repeat(6,1fr); gap:2px; padding:6px; }
.bbg-hm-cell { display:flex; justify-content:space-between; align-items:center; padding:3px 6px; font-size:9px; font-weight:700; border-radius:2px; white-space:nowrap; }
.bbg-top5 { display:grid; grid-template-columns:repeat(5,1fr); }
.bbg-t5c { padding:8px 10px; border-right:1px solid #1A1A1A; border-top:3px solid #333; background:#050505; }
.bbg-t5c:last-child { border-right:none; }
.bbg-t5c.strong { border-top-color:#FF8000; }
.bbg-t5c.buy    { border-top-color:#FFCC00; }
.bbg-t5-tkr { color:#FF8000; font-size:18px; font-weight:700; line-height:1; }
.bbg-t5-sec { color:#555; font-size:8px; letter-spacing:1px; margin:3px 0; }
.bbg-t5-sig { font-size:9px; font-weight:700; margin:4px 0 2px; letter-spacing:1px; }
.bbg-t5-alloc { color:#FF8000; font-size:13px; font-weight:700; }
.bar-bg  { background:#1A1A1A; height:3px; margin-top:4px; }
.bar-fill { height:3px; }
.bbg-t5-rsn { color:#444; font-size:8px; margin-top:3px; }
.ytd-pos { color:#00CC00; font-size:11px; }
.ytd-neg { color:#CC0000; font-size:11px; }
.sig-sb { color:#FF8000; font-weight:700; }
.sig-b  { color:#FFCC00; font-weight:600; }
.sig-h  { color:#888; }
.sig-s  { color:#CC3333; }
.sig-ss { color:#FF0000; font-weight:700; }
.sig-ht { color:#FF00FF; font-weight:700; }
.bbg-macro-row { display:grid; grid-template-columns:repeat(10,1fr); border-bottom:1px solid #333; background:#050505; margin-top:4px; }
.bbg-macro-cell { padding:8px 6px; border-right:1px solid #1A1A1A; text-align:center; }
.bbg-macro-cell:last-child { border-right:none; }
.bbg-macro-lbl { color:#555; font-size:8px; letter-spacing:1px; text-transform:uppercase; margin-bottom:2px; }
.bbg-macro-val { font-size:13px; font-weight:700; line-height:1; }
.bbg-macro-sub { color:#444; font-size:8px; margin-top:2px; }
.cbadge { background:#001a33; border:1px solid #0066cc; color:#4da6ff; padding:4px 10px; border-radius:2px; font-size:0.7rem; letter-spacing:1px; display:inline-block; margin-bottom:4px; }
textarea { background:#050505 !important; color:#CCC !important; border:1px solid #222 !important; }
</style>
""", unsafe_allow_html=True)

# -- STATUS BAR ----------------------------------------------------
st.markdown(
    "<div class=\"bbg-status\">"
    "<div class=\"bbg-status-l\" style=\"color:" + status_color + ";\">MKT " + market_status + "</div>"
    "<div class=\"bbg-status-c\">QUANT TERMINAL v3 - GICS MODEL - SOLOMON STRATEGY</div>"
    "<div class=\"bbg-status-r\"><span id=\"live-clock\">" + time_str + "</span> &nbsp; " + date_str + "</div>"
    "</div>",
    unsafe_allow_html=True
)

components.html("""<script>
(function(){
  function tick(){
    var et=new Date(new Date().toLocaleString("en-US",{timeZone:"America/New_York"}));
    var s=String(et.getHours()).padStart(2,"0")+":"+String(et.getMinutes()).padStart(2,"0")+":"+String(et.getSeconds()).padStart(2,"0")+" ET";
    try{var e=window.parent.document.getElementById("live-clock");if(e)e.textContent=s;}catch(x){}
  }
  tick();setInterval(tick,1000);
})();
</script>""", height=0)

# -- GICS UNIVERSE -------------------------------------------------
GICS_UNIVERSE = {
    "1010 Energy":                   ["XLE"],
    "1510 Materials":                ["XLB"],
    "2010 Capital Goods":            ["XLI"],
    "2020 Commercial & Prof Svcs":   ["RSG", "WM", "CTAS"],
    "2030 Transportation":           ["IYT"],
    "2510 Automobiles":              ["TSLA", "GM"],
    "2520 Consumer Durables":        ["XHB"],
    "2530 Consumer Services":        ["XLY"],
    "2550 Consumer Disc Retail":     ["XRT"],
    "3010 Consumer Staples Retail":  ["WMT", "COST", "KR"],
    "3020 Food Beverage Tobacco":    ["XLP"],
    "3030 Household & Personal":     ["PG", "CL"],
    "3510 Health Care Equipment":    ["IHI"],
    "3520 Pharma Biotech":           ["XBI"],
    "4010 Banks":                    ["KBE"],
    "4020 Diversified Financials":   ["XLF"],
    "4030 Insurance":                ["IAK"],
    "4510 Software & Services":      ["IGV"],
    "4520 Tech Hardware":            ["IGN"],
    "4530 Semiconductors":           ["SMH"],
    "5010 Communication Services":   ["XLC"],
    "5020 Media & Entertainment":    ["SOCL"],
    "5510 Utilities":                ["XLU"],
    "6010 Real Estate":              ["VNQ"],
    "6020 Mortgage REITs":           ["REM"],
}

SOLOMON_TICKERS = [
    "OIH","XLE","XLB","XME","XLI","IYT","XLY","XRT","XLP","IHI",
    "XBI","KBE","XLF","KIE","IGV","SMH","XLC","XLU","VNQ","REET",
    "EFA","VWO","DBA","PDBC","UUP","VIXY","SLV","TIP","IAU","BIL","IEF","TLT"
]
SOLOMON_SECTORS = {
    "OIH":"Energy","XLE":"Energy","XLB":"Materials","XME":"Materials",
    "XLI":"Industrials","IYT":"Industrials","XLY":"Cons Disc","XRT":"Cons Disc",
    "XLP":"Cons Staples","IHI":"Health Care","XBI":"Health Care",
    "KBE":"Financials","XLF":"Financials","KIE":"Financials",
    "IGV":"Info Tech","SMH":"Info Tech","XLC":"Comm Svcs",
    "XLU":"Utilities","VNQ":"Real Estate","REET":"Real Estate",
    "EFA":"Global","VWO":"Global","DBA":"Uncorrelated","PDBC":"Uncorrelated",
    "UUP":"Uncorrelated","VIXY":"Uncorrelated","SLV":"Uncorrelated",
    "TIP":"Uncorrelated","IAU":"Macro","BIL":"Safe Harbor",
    "IEF":"Safe Harbor","TLT":"Safe Harbor"
}
BENCHMARKS = ["SPY","QQQ","DIA","^VIX","^TNX","^TYX","GC=F","CL=F"]

# -- DATA LAYER ----------------------------------------------------
@st.cache_data(ttl=300)
def fetch_data(ticker, period="2y", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty or len(df) < 60:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

def compute_indicators(df):
    if df.empty or len(df) < 60:
        return pd.DataFrame()
    df = df.copy()
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.stoch(k=14, d=3, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.adx(length=14, append=True)
    try:
        ichi = df.ta.ichimoku(append=False)
        if isinstance(ichi, tuple):
            ichi = ichi[0]
        if ichi is not None and not ichi.empty:
            cols = [c for c in ichi.columns if "ISA" in c or "ISB" in c]
            df = df.join(ichi[cols], how="left")
    except Exception:
        pass
    df["Vol_SMA_20"] = df["Volume"].rolling(20).mean()
    df["Vol_Ratio"]  = df["Volume"] / df["Vol_SMA_20"].replace(0, np.nan)
    rh = df["High"].rolling(50).max()
    rl = df["Low"].rolling(50).min()
    rd = rh - rl
    df["Fib_0618"] = rh - 0.618 * rd
    df["Fib_0382"] = rh - 0.382 * rd
    df = df.ffill().bfill()
    return df.dropna(subset=["Close","Open","High","Low"])

def _f(row, key, default=0.0):
    try:
        v = row.get(key, default)
        if hasattr(v, "iloc"):
            v = v.iloc[-1]
        if hasattr(v, "item"):
            v = v.item()
        return float(v)
    except Exception:
        return default

def _standby(msg):
    return {"signal":"STANDBY","color":"#FFA500","score":0,"reasons":[msg],
            "entry":None,"stop":None,"target":None,"rr":None}

# -- SIGNAL ENGINES ------------------------------------------------
def evaluate_surefire(df):
    if df.empty or len(df) < 10:
        return _standby("Insufficient data.")
    l    = df.iloc[-1]
    prev = df.iloc[-2]
    close  = _f(l, "Close")
    ema20  = _f(l, "EMA_20")
    ema50  = _f(l, "EMA_50")
    ema200 = _f(l, "EMA_200")
    rsi    = _f(l, "RSI_14", 50)
    adx    = _f(l, "ADX_14")
    macd   = _f(l, "MACD_12_26_9")
    macds  = _f(l, "MACDs_12_26_9")
    pmacd  = _f(prev, "MACD_12_26_9")
    pmacds = _f(prev, "MACDs_12_26_9")
    bbu    = _f(l, "BBU_20_2.0")
    bbl    = _f(l, "BBL_20_2.0")
    volr   = _f(l, "Vol_Ratio", 1.0)
    stochk = _f(l, "STOCHk_14_3_3", 50)
    stochd = _f(l, "STOCHd_14_3_3", 50)
    atr    = _f(l, "ATRr_14", close * 0.02)
    if volr < 1.3:
        return _standby("Volume insufficient (" + str(round(volr,2)) + "x). Requires 1.3x avg.")
    if adx < 30:
        return _standby("Trend too weak (ADX " + str(round(adx,1)) + " < 30).")
    bs = ss = 0
    br = []
    if close > ema20 > ema50 > ema200:
        bs += 2; br.append("[BUY] Full bullish EMA stack 20>50>200")
    if macd > macds and pmacd <= pmacds:
        bs += 2; br.append("[BUY] MACD bullish crossover confirmed")
    if 55 < rsi < 80:
        bs += 1; br.append("[BUY] RSI in bullish zone " + str(round(rsi,1)))
    if stochk > stochd and stochk > 50:
        bs += 1; br.append("[BUY] Stochastic bullish cross above 50")
    if close > bbu:
        bs += 1; br.append("[BUY] BB upper breakout - momentum expansion")
    if volr > 1.8:
        bs += 1; br.append("[BUY] Volume spike " + str(round(volr,1)) + "x avg")
    if close < ema20 < ema50 < ema200:
        ss += 2; br.append("[SELL] Full bearish EMA stack 20<50<200")
    if macd < macds and pmacd >= pmacds:
        ss += 2; br.append("[SELL] MACD bearish crossover confirmed")
    if 20 < rsi < 45:
        ss += 1; br.append("[SELL] RSI in bearish zone " + str(round(rsi,1)))
    if stochk < stochd and stochk < 50:
        ss += 1; br.append("[SELL] Stochastic bearish cross below 50")
    if close < bbl:
        ss += 1; br.append("[SELL] BB lower breakdown")
    entry = round(close, 2)
    if bs >= 5:
        stop = round(close - 2*atr, 2)
        tgt  = round(close + 3*atr, 2)
        rr   = round((tgt-entry)/max(entry-stop,0.01), 2)
        return {"signal":"EXECUTE BUY","color":"#00FF41","score":bs,"entry":entry,
                "stop":stop,"target":tgt,"rr":rr,"reasons":br,
                "atr":round(atr,2),"adx":round(adx,2),"rsi":round(rsi,2),"hold":"1-5 Days"}
    if ss >= 5:
        stop = round(close + 2*atr, 2)
        tgt  = round(close - 3*atr, 2)
        rr   = round((entry-tgt)/max(stop-entry,0.01), 2)
        return {"signal":"EXECUTE SELL","color":"#FF4444","score":ss,"entry":entry,
                "stop":stop,"target":tgt,"rr":rr,"reasons":br,
                "atr":round(atr,2),"adx":round(adx,2),"rsi":round(rsi,2),"hold":"1-5 Days"}
    return _standby("Score insufficient BUY:" + str(bs) + "/7 SELL:" + str(ss) + "/7")

def evaluate_longterm(df):
    if df.empty or len(df) < 10:
        return _standby("Insufficient data.")
    l      = df.iloc[-1]
    close  = _f(l, "Close")
    ema50  = _f(l, "EMA_50")
    ema200 = _f(l, "EMA_200")
    rsi    = _f(l, "RSI_14", 50)
    adx    = _f(l, "ADX_14")
    macd   = _f(l, "MACD_12_26_9")
    macds  = _f(l, "MACDs_12_26_9")
    atr    = _f(l, "ATRr_14", close*0.02)
    fib    = _f(l, "Fib_0618")
    bs = ss = 0
    br = []
    if close > ema200: bs += 2; br.append("[BUY] Above 200 EMA - secular uptrend")
    else:              ss += 2; br.append("[SELL] Below 200 EMA - secular downtrend")
    if ema50 > ema200: bs += 2; br.append("[BUY] Golden Cross active 50>200 EMA")
    else:              ss += 2; br.append("[SELL] Death Cross active 50<200 EMA")
    if adx > 25:       bs += 1; br.append("[BUY] Trend strength ADX " + str(round(adx,1)))
    if macd > macds:   bs += 1; br.append("[BUY] MACD positive momentum")
    else:              ss += 1; br.append("[SELL] MACD negative momentum")
    if 40 < rsi < 75:  bs += 1; br.append("[BUY] RSI healthy range " + str(round(rsi,1)))
    if fib > 0 and close > fib: bs += 1; br.append("[BUY] Above Fib 61.8% support")
    entry = round(close, 2)
    stop  = round(close - 3*atr, 2)
    tgt   = round(close + 6*atr, 2)
    rr    = round((tgt-entry)/max(entry-stop,0.01), 2)
    if bs >= 5:
        return {"signal":"LONG-TERM BUY","color":"#00FF41","score":bs,"entry":entry,
                "stop":stop,"target":tgt,"rr":rr,"reasons":br,
                "atr":round(atr,2),"adx":round(adx,2),"rsi":round(rsi,2),"hold":"Weeks to Months"}
    if ss >= 4:
        return {"signal":"REDUCE / EXIT","color":"#FF4444","score":ss,"entry":entry,
                "stop":round(close+3*atr,2),"target":round(close-6*atr,2),"rr":rr,"reasons":br,
                "atr":round(atr,2),"adx":round(adx,2),"rsi":round(rsi,2),"hold":"Exit/Reduce"}
    return _standby("Awaiting long-term structural alignment.")

def evaluate_swing(df):
    if df.empty or len(df) < 10:
        return _standby("Insufficient data.")
    l     = df.iloc[-1]
    prev  = df.iloc[-2]
    close  = _f(l, "Close")
    ema20  = _f(l, "EMA_20")
    rsi    = _f(l, "RSI_14", 50)
    prsi   = _f(prev, "RSI_14", 50)
    bbu    = _f(l, "BBU_20_2.0")
    bbl    = _f(l, "BBL_20_2.0")
    bbm    = _f(l, "BBM_20_2.0")
    pbbu   = _f(prev, "BBU_20_2.0")
    pbbl   = _f(prev, "BBL_20_2.0")
    stochk = _f(l, "STOCHk_14_3_3", 50)
    stochd = _f(l, "STOCHd_14_3_3", 50)
    pstochk= _f(prev, "STOCHk_14_3_3", 50)
    pstochd= _f(prev, "STOCHd_14_3_3", 50)
    atr    = _f(l, "ATRr_14", close*0.015)
    volr   = _f(l, "Vol_Ratio", 1.0)
    adx    = _f(l, "ADX_14")
    bbw    = (bbu - bbl) / max(bbm, 1)
    if bbw < 0.01:
        return _standby("Bollinger Bands too compressed. No swing edge.")
    bs = ss = 0
    br = []
    if rsi < 35 and prsi < rsi:   bs += 2; br.append("[BUY] RSI oversold reversal " + str(round(rsi,1)))
    if close <= bbl * 1.015:      bs += 2; br.append("[BUY] Price at lower BB - mean reversion")
    if stochk > stochd and pstochk <= pstochd and stochk < 30:
        bs += 2; br.append("[BUY] Stochastic cross from oversold")
    if close > ema20:              bs += 1; br.append("[BUY] Reclaimed 20 EMA")
    if volr > 1.2:                 bs += 1; br.append("[BUY] Volume confirmation " + str(round(volr,1)) + "x")
    if rsi > 70 and prsi > rsi:   ss += 2; br.append("[SELL] RSI overbought rolling " + str(round(rsi,1)))
    if close >= bbu * 0.99:       ss += 2; br.append("[SELL] Price at upper BB - fade setup")
    if stochk < stochd and pstochk >= pstochd and stochk > 70:
        ss += 2; br.append("[SELL] Stochastic cross from overbought")
    if volr > 1.2 and ss > 0:     ss += 1; br.append("[SELL] Volume confirms distribution")
    entry = round(close, 2)
    if bs >= 4:
        stop = round(close - 1.5*atr, 2)
        tgt  = round(bbm, 2)
        rr   = round((tgt-entry)/max(entry-stop,0.01), 2)
        return {"signal":"SWING BUY","color":"#00FF41","score":bs,"entry":entry,
                "stop":stop,"target":tgt,"rr":rr,"reasons":br,
                "atr":round(atr,2),"adx":round(adx,2),"rsi":round(rsi,2),"hold":"2-10 Days"}
    if ss >= 4:
        stop = round(close + 1.5*atr, 2)
        tgt  = round(bbm, 2)
        rr   = round((entry-tgt)/max(stop-entry,0.01), 2)
        return {"signal":"SWING SELL","color":"#FF4444","score":ss,"entry":entry,
                "stop":stop,"target":tgt,"rr":rr,"reasons":br,
                "atr":round(atr,2),"adx":round(adx,2),"rsi":round(rsi,2),"hold":"2-10 Days"}
    return _standby("No swing edge. Awaiting mean reversion extremes.")

def evaluate_fat_pitch(df):
    if df.empty or len(df) < 10:
        return _standby("Insufficient data.")
    l     = df.iloc[-1]
    close = _f(l, "Close")
    macd  = _f(l, "MACD_12_26_9")
    macds = _f(l, "MACDs_12_26_9")
    adx   = _f(l, "ADX_14")
    rsi   = _f(l, "RSI_14", 50)
    bbu   = _f(l, "BBU_20_2.0")
    volr  = _f(l, "Vol_Ratio", 1.0)
    atr   = _f(l, "ATRr_14", close*0.02)
    g1 = volr >= 1.5
    g2 = adx  >= 35
    g3 = close > bbu and macd > macds and 60 <= rsi <= 85
    if not g1:
        return _standby("Gate 1 FAIL: Volume " + str(round(volr,2)) + "x - requires 1.5x institutional.")
    if not g2:
        return _standby("Gate 2 FAIL: ADX " + str(round(adx,1)) + " - requires 35 terminal velocity.")
    if not g3:
        g1s = "PASS" if g1 else "FAIL"
        g2s = "PASS" if g2 else "FAIL"
        return _standby("Gate 3 FAIL: BB break+MACD+RSI not aligned. G1:" + g1s + " G2:" + g2s)
    entry = round(close, 2)
    stop  = round(close - 2*atr, 2)
    tgt   = round(close + 4*atr, 2)
    rr    = round((tgt-entry)/max(entry-stop,0.01), 2)
    return {
        "signal":"FAT PITCH - EXECUTE","color":"#00CCFF","score":3,
        "entry":entry,"stop":stop,"target":tgt,"rr":rr,
        "reasons":[
            "Gate 1 PASS: Volume " + str(round(volr,1)) + "x avg (>=1.5x institutional)",
            "Gate 2 PASS: ADX " + str(round(adx,1)) + " - trend has terminal velocity",
            "Gate 3 PASS: BB breakout + MACD bullish + RSI " + str(round(rsi,1)) + " in sweet spot",
            "ASYMMETRIC SETUP - maximum conviction signal"
        ],
        "atr":round(atr,2),"adx":round(adx,2),"rsi":round(rsi,2),"hold":"Hold until ADX rollover"
    }

# -- BACKTEST ------------------------------------------------------
def walk_forward_backtest(df, strategy="surefire"):
    if len(df) < 120:
        return {}
    split   = int(len(df) * 0.7)
    test_df = df.iloc[split:].copy().reset_index(drop=True)
    hold_bars = {"surefire":20,"longterm":60,"swing":5,"fatpitch":20}
    window = hold_bars.get(strategy, 10)
    trades = []
    for i in range(5, len(test_df) - window):
        seg = test_df.iloc[:i]
        if strategy == "surefire":   r = evaluate_surefire(seg)
        elif strategy == "longterm": r = evaluate_longterm(seg)
        elif strategy == "fatpitch": r = evaluate_fat_pitch(seg)
        else:                        r = evaluate_swing(seg)
        if r["signal"] == "STANDBY" or not r.get("entry"):
            continue
        entry = r["entry"]; stop = r["stop"]; tgt = r["target"]
        future = test_df.iloc[i:i+window]
        is_buy = "BUY" in r["signal"] or "FAT" in r["signal"]
        hit_t = any(float(row["High"]) >= tgt  for _, row in future.iterrows()) if is_buy else any(float(row["Low"]) <= tgt for _, row in future.iterrows())
        hit_s = any(float(row["Low"])  <= stop for _, row in future.iterrows()) if is_buy else any(float(row["High"]) >= stop for _, row in future.iterrows())
        if hit_t and not hit_s:
            trades.append({"outcome":"WIN",  "pnl":(tgt-entry)/entry if is_buy else (entry-tgt)/entry})
        elif hit_s:
            trades.append({"outcome":"LOSS", "pnl":(stop-entry)/entry if is_buy else (entry-stop)/entry})
    if not trades:
        return {"trades":0,"win_rate":0,"avg_pnl":0,"total_return":0,"avg_win":2.0,"avg_loss":1.0}
    wins   = [t for t in trades if t["outcome"]=="WIN"]
    losses = [t for t in trades if t["outcome"]=="LOSS"]
    pnls   = [t["pnl"] for t in trades]
    return {
        "trades":       len(trades),
        "win_rate":     round(len(wins)/len(trades)*100, 1),
        "avg_pnl":      round(np.mean(pnls)*100, 2),
        "total_return": round(sum(pnls)*100, 2),
        "avg_win":      round(abs(np.mean([t["pnl"] for t in wins]))*100, 2)  if wins   else 2.0,
        "avg_loss":     round(abs(np.mean([t["pnl"] for t in losses]))*100, 2) if losses else 1.0,
    }

def monte_carlo(win_rate, avg_win, avg_loss, n=500, trials=200):
    results = []
    for _ in range(trials):
        eq = 100.0
        for _ in range(n):
            if np.random.random() < win_rate/100:
                eq *= (1 + avg_win/100)
            else:
                eq *= (1 - avg_loss/100)
        results.append(eq)
    return {
        "median":    round(float(np.median(results)), 2),
        "p10":       round(float(np.percentile(results, 10)), 2),
        "p90":       round(float(np.percentile(results, 90)), 2),
        "ruin_prob": round(sum(1 for r in results if r < 50)/trials*100, 1),
    }

# -- CHART ---------------------------------------------------------
def build_chart(df, ticker, result):
    if df.empty:
        return go.Figure()
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.60,0.20,0.20], vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#00FF41", decreasing_line_color="#FF4444",
        name="Price"), row=1, col=1)
    for col, color, name in [("EMA_20","#FF8000","EMA20"),("EMA_50","#4da6ff","EMA50"),("EMA_200","#FF69B4","EMA200")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=name, line=dict(color=color,width=1)), row=1, col=1)
    if "BBU_20_2.0" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BBU_20_2.0"], name="BB Up",
            line=dict(color="#333",width=1,dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BBL_20_2.0"], name="BB Lo",
            line=dict(color="#333",width=1,dash="dot"),
            fill="tonexty", fillcolor="rgba(80,80,80,0.04)"), row=1, col=1)
    if result.get("entry"):
        for level, color, label in [(result["entry"],"#FF8000","ENTRY"),(result.get("stop"),"#FF4444","STOP"),(result.get("target"),"#00FF41","TARGET")]:
            if level:
                fig.add_hline(y=level, line_color=color, line_dash="dash", line_width=1,
                              row=1, col=1, annotation_text=" "+label+": $"+str(level),
                              annotation_font_color=color, annotation_position="right")
    if "RSI_14" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI_14"], name="RSI",
            line=dict(color="#FF8000",width=1)), row=2, col=1)
        fig.add_hline(y=70, line_color="#FF4444", line_dash="dot", line_width=1, row=2, col=1)
        fig.add_hline(y=30, line_color="#00FF41", line_dash="dot", line_width=1, row=2, col=1)
    try:
        vc = ["#00FF41" if float(df["Close"].iloc[i])>=float(df["Open"].iloc[i]) else "#FF4444" for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Vol", marker_color=vc, opacity=0.5), row=3, col=1)
        if "Vol_SMA_20" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["Vol_SMA_20"], name="Vol SMA",
                line=dict(color="#FF8000",width=1)), row=3, col=1)
    except Exception:
        pass
    fig.update_layout(template="plotly_dark", paper_bgcolor="#000", plot_bgcolor="#050505",
        font=dict(family="Source Code Pro", color="#666", size=10),
        showlegend=False, height=580, xaxis_rangeslider_visible=False,
        margin=dict(l=0,r=0,t=28,b=0),
        title=dict(text="[ "+ticker+" ]  PRICE ACTION", font=dict(color="#FF8000",size=12)))
    fig.update_yaxes(gridcolor="#111", zerolinecolor="#1a1a1a")
    fig.update_xaxes(gridcolor="#111", zerolinecolor="#1a1a1a")
    return fig

# -- DISPLAY HELPERS -----------------------------------------------
def show_signal_card(result, style="standard"):
    sig   = result["signal"]
    color = result["color"]
    if style == "fat":              css = "sig-fat"
    elif "BUY" in sig:              css = "sig-buy"
    elif "SELL" in sig or "EXIT" in sig or "REDUCE" in sig: css = "sig-sell"
    else:                           css = "sig-wait"
    score_txt = "SCORE: "+str(result.get("score",0)) if result.get("score") else "GATES EVALUATED"
    st.markdown(
        "<div class=\""+css+"\">"
        "<div style=\"font-size:1.5rem;font-weight:700;color:"+color+";letter-spacing:3px;\">"+sig+"</div>"
        "<div style=\"color:#555;font-size:0.72rem;margin-top:6px;\">"+score_txt+" | FINRA 15c3-5 | INFORMATIONAL ONLY</div>"
        "</div>", unsafe_allow_html=True)

def show_trade_levels(result):
    if not result.get("entry"):
        return
    c1,c2,c3,c4 = st.columns(4)
    entry = result["entry"]; stop = result["stop"]; tgt = result["target"]
    c1.metric("ENTRY",     "$"+str(entry))
    c2.metric("STOP LOSS", "$"+str(stop),   delta=str(round((stop-entry)/entry*100,2))+"%", delta_color="inverse")
    c3.metric("TARGET",    "$"+str(tgt),    delta=str(round((tgt-entry)/entry*100,2))+"%")
    c4.metric("RISK/REWARD", str(result.get("rr","N/A"))+":1")

def show_rationale(result):
    with st.expander("TRADE RATIONALE - FULL SIGNAL BREAKDOWN", expanded=True):
        st.markdown("<div class=\"rat-box\">", unsafe_allow_html=True)
        st.markdown("**TECHNICAL FACTORS:**")
        for r in result.get("reasons", []):
            st.markdown("  " + r)
        st.markdown(
            "**RISK METRICS:**  ATR: `"+str(result.get("atr","N/A"))+"` | "
            "ADX: `"+str(result.get("adx","N/A"))+"` | "
            "RSI: `"+str(result.get("rsi","N/A"))+"`\n\n"
            "**COMPLIANCE:** FINRA Rule 15c3-5 | SEC Reg T | SEC Reg NMS | "
            "All signals informational only. Not financial advice.\n\n"
            "**HOLD PERIOD:** `"+str(result.get("hold","N/A"))+"`"
        )
        st.markdown("</div>", unsafe_allow_html=True)

def show_backtest(df, strategy):
    with st.expander("WALK-FORWARD BACKTEST + MONTE CARLO"):
        with st.spinner("Running simulations..."):
            bt = walk_forward_backtest(df, strategy)
        if not bt or bt.get("trades",0) == 0:
            st.warning("Insufficient signals in test window.")
            return
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("SIGNALS TESTED", bt["trades"])
        c2.metric("WIN RATE",       str(bt["win_rate"])+"%")
        c3.metric("AVG P&L",        str(bt["avg_pnl"])+"%")
        c4.metric("TOTAL RETURN",   str(bt["total_return"])+"%")
        mc = monte_carlo(bt["win_rate"], bt["avg_win"], bt["avg_loss"])
        st.markdown("**MONTE CARLO (500 trades x 200 trials, $100 start):**")
        mc1,mc2,mc3,mc4 = st.columns(4)
        mc1.metric("MEDIAN",          "$"+str(mc["median"]))
        mc2.metric("PESSIMISTIC P10", "$"+str(mc["p10"]))
        mc3.metric("OPTIMISTIC P90",  "$"+str(mc["p90"]))
        mc4.metric("RUIN PROB",       str(mc["ruin_prob"])+"%")

# -- UNIVERSE SCANNER ----------------------------------------------
def _eval_worker(args):
    gics_name, ticker, df_computed, mode = args
    try:
        if mode == "surefire":   r = evaluate_surefire(df_computed)
        elif mode == "longterm": r = evaluate_longterm(df_computed)
        elif mode == "fatpitch": r = evaluate_fat_pitch(df_computed)
        else:                    r = evaluate_swing(df_computed)
        if r["signal"] != "STANDBY":
            return {"GICS Node":gics_name,"Ticker":ticker,"Signal":r["signal"],
                    "Score":r.get("score",0),"Entry":r.get("entry"),
                    "Stop":r.get("stop"),"Target":r.get("target"),
                    "R/R":r.get("rr"),"RSI":r.get("rsi"),"ADX":r.get("adx")}
    except Exception:
        pass
    return None

def run_universe_scan(mode):
    universe  = list(GICS_UNIVERSE.items())
    args_list = []
    total     = sum(len(t) for _, t in universe)
    prog      = st.progress(0, text="Fetching data...")
    fetched   = 0
    for gics_name, tickers in universe:
        for ticker in tickers:
            period = "2y" if mode == "longterm" else "1y"
            raw = fetch_data(ticker, period=period)
            dfc = compute_indicators(raw) if not raw.empty else pd.DataFrame()
            args_list.append((gics_name, ticker, dfc, mode))
            fetched += 1
            prog.progress(fetched/total/2, text="Fetching "+ticker+"...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futures = list(ex.map(_eval_worker, args_list))
    for i, r in enumerate(futures):
        if r:
            results.append(r)
        prog.progress(0.5 + (i+1)/len(args_list)/2, text="Evaluating...")
    prog.empty()
    return results

# -- SOLOMON STRATEGY ----------------------------------------------
@st.cache_data(ttl=3600)
def fetch_solomon_data():
    return yf.download(SOLOMON_TICKERS + BENCHMARKS, period="2y", progress=False, auto_adjust=True)

def calculate_solomon(data, target_date, vix_close):
    closes = data["Close"].loc[:target_date]
    highs  = data["High"].loc[:target_date]
    lows   = data["Low"].loc[:target_date]
    vols   = data["Volume"].loc[:target_date]
    if len(closes) < 200:
        return pd.DataFrame()
    spy_p    = closes["SPY"].dropna()
    vix_halt = vix_close > 30
    try:    tnx = data["Close"]["^TNX"].loc[:target_date].dropna().iloc[-1]
    except: tnx = None
    results = []
    for t in SOLOMON_TICKERS:
        try:
            p  = closes[t].dropna()
            h  = highs[t].dropna()
            lo = lows[t].dropna()
            v  = vols[t].dropna()
            if len(p) < 200: continue
            ytd_px = p[p.index.year == target_date.year]
            ytd    = ((p.iloc[-1]/ytd_px.iloc[0])-1)*100 if not ytd_px.empty else 0
            r1m = p.pct_change(21).iloc[-1]; r3m = p.pct_change(63).iloc[-1]
            r6m = p.pct_change(126).iloc[-1]; r9m = p.pct_change(189).iloc[-1]
            v1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram = r1m/v1m if v1m != 0 else 0
            s1m = spy_p.pct_change(21).iloc[-1]; s3m = spy_p.pct_change(63).iloc[-1]
            s6m = spy_p.pct_change(126).iloc[-1]; s9m = spy_p.pct_change(189).iloc[-1]
            rel = ((r1m+r3m+r6m+r9m)/4) - ((s1m+s3m+s6m+s9m)/4)
            sma50  = p.rolling(50).mean(); sma200 = p.rolling(200).mean()
            slp50  = (sma50.iloc[-1]-sma50.iloc[-21])/sma50.iloc[-21]
            above200 = p.iloc[-1] > sma200.iloc[-1]
            v90  = v.rolling(90).mean().iloc[-1]
            vcf  = (v.rolling(20).mean().iloc[-1]/v90) if v90 != 0 else 1
            tr   = pd.concat([h-lo,abs(h-p.shift()),abs(lo-p.shift())],axis=1).max(axis=1)
            atr  = tr.rolling(14).mean().iloc[-1]
            stop = p.tail(20).max() - 2.5*atr
            sd   = (p.iloc[-1]-stop)/p.iloc[-1]
            alloc = min((0.01/sd)*100, 25) if sd > 0 else 0
            up   = h-h.shift(1); dw = lo.shift(1)-lo
            tr14 = tr.rolling(14).sum()
            pdi  = 100*(pd.Series(np.where((up>dw)&(up>0),up,0),index=p.index).rolling(14).sum()/tr14)
            mdi  = 100*(pd.Series(np.where((dw>up)&(dw>0),dw,0),index=p.index).rolling(14).sum()/tr14)
            adx_v= (100*abs(pdi-mdi)/(pdi+mdi)).rolling(14).mean().iloc[-1]
            roc  = p.pct_change(20).iloc[-1] - (p.pct_change(60).iloc[-1]/3)
            radj = -0.3 if (tnx and tnx>4.5 and SOLOMON_SECTORS.get(t,"") in ["Safe Harbor","Utilities","Real Estate"]) else 0
            results.append({"TKR":t,"SECTOR":SOLOMON_SECTORS[t],"PRICE":p.iloc[-1],"YTD":ytd,
                "R1M":r1m*100,"R3M":r3m*100,"RAM":ram,"REL":rel,"SLP":slp50,
                "VCF":vcf,"ADX":adx_v,"STOP":stop,"ROC":roc,"ALLOC_B":alloc,
                "AB200":above200,"RADJ":radj})
        except Exception:
            continue
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame(results).set_index("TKR")
    f  = ["RAM","REL","SLP","VCF","ROC"]
    z  = (df[f]-df[f].mean())/df[f].std()
    df["SCORE"] = (z["RAM"]*0.25+z["REL"]*0.20+z["SLP"]*0.20+z["VCF"]*0.20+z["ROC"]*0.15)*100+df["RADJ"]*10
    df = df.sort_values("SCORE", ascending=False)
    df["RNK"] = range(1, len(df)+1)
    sigs,ress,allocs = [],[],[]
    for idx,row in df.iterrows():
        fails = []
        if not row["AB200"]:      fails.append("Below 200MA")
        if row["ADX"] <= 25:      fails.append("ADX "+str(round(row["ADX"],0)))
        if row["VCF"] < 1.2:      fails.append("Vol "+str(round(row["VCF"],2))+"x")
        if row["RAM"] <= 0:       fails.append("Neg RAM")
        if row["REL"] <= 0:       fails.append("Lags SPY")
        if row["ROC"] <= 0:       fails.append("Decel ROC")
        if row["SLP"] <= 0:       fails.append("Neg 50D Slope")
        rnk = row["RNK"]; n = len(fails)
        if vix_halt:                  sig,res,alloc = "HALT","VIX>30",0
        elif not row["AB200"]:        sig,res,alloc = "STRONG SELL",fails[0] if fails else "Stop",0
        elif rnk<=5 and n==0:         sig,res,alloc = "STRONG BUY","ALL CLEAR",min(row["ALLOC_B"],20)
        elif rnk<=5 and n<=2:         sig,res,alloc = "BUY",", ".join(fails),min(row["ALLOC_B"]*0.6,12)
        elif rnk<=5:                  sig,res,alloc = "BUY",", ".join(fails[:2]),min(row["ALLOC_B"]*0.3,6)
        elif rnk<=10 and n==0:        sig,res,alloc = "HOLD","Rank buffer",0
        elif rnk<=10:                 sig,res,alloc = "HOLD",", ".join(fails[:1]),0
        else:                         sig,res,alloc = "SELL",", ".join(fails[:2]) if fails else "Rank "+str(rnk),0
        sigs.append(sig); ress.append(res); allocs.append(alloc)
    df["SIGNAL"] = sigs; df["REASON"] = ress; df["ALLOC"] = allocs
    return df

# -- PORTFOLIO -----------------------------------------------------
def portfolio_section():
    st.markdown("### PORTFOLIO TRACKER - POSITION SIZING - GICS ATTRIBUTION")
    st.markdown("---")
    gics_opts = ["(Manual)"] + list(GICS_UNIVERSE.keys())
    with st.expander("ADD POSITION", expanded=False):
        pc1,pc2 = st.columns(2)
        with pc1:
            gsel = st.selectbox("GICS NODE", gics_opts, key="port_gics")
            dtk  = GICS_UNIVERSE.get(gsel,[""])[0] if gsel != "(Manual)" else ""
            ptk  = st.text_input("TICKER", value=dtk, key="port_ticker")
            psh  = st.number_input("SHARES", min_value=0.0, step=1.0, key="port_shares")
        with pc2:
            pen  = st.number_input("ENTRY $", min_value=0.0, step=0.01, key="port_entry")
            pst  = st.number_input("STOP $",  min_value=0.0, step=0.01, key="port_stop")
            pacc = st.number_input("ACCOUNT $", min_value=1000.0, value=100000.0, step=1000.0, key="port_acc")
            prsk = st.slider("RISK %", 0.5, 5.0, 1.0, 0.25, key="port_risk")
        if st.button("CALCULATE + ADD POSITION"):
            if ptk and pen > 0 and pst > 0:
                rps  = abs(pen-pst)
                mxr  = pacc * (prsk/100)
                sugg = int(mxr/rps) if rps > 0 else 0
                raw  = fetch_data(ptk.upper(), period="5d")
                cur  = float(raw["Close"].iloc[-1]) if not raw.empty else pen
                pnl  = (cur-pen)*psh
                pnlp = ((cur-pen)/pen)*100 if pen > 0 else 0
                gtag = gsel if gsel != "(Manual)" else "Unclassified"
                st.session_state.portfolio.append({
                    "Ticker":ptk.upper(),"GICS":gtag,"Shares":psh,
                    "Entry":round(pen,2),"Stop":round(pst,2),"Current":round(cur,2),
                    "P&L $":round(pnl,2),"P&L %":round(pnlp,2),
                    "Suggested":sugg,"Max Risk":round(mxr,2),"Value":round(psh*pen,2)
                })
                st.success("Added. Suggested shares at "+str(prsk)+"% risk: "+str(sugg))
    if not st.session_state.portfolio:
        st.info("No positions. Add one above.")
        return
    pdf   = pd.DataFrame(st.session_state.portfolio)
    tpnl  = pdf["P&L $"].sum()
    tval  = pdf["Value"].sum()
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("POSITIONS",   len(pdf))
    m2.metric("VALUE",       "$"+str(round(tval,2)))
    m3.metric("TOTAL P&L",   "$"+str(round(tpnl,2)), delta=str(round(tpnl/max(tval,1)*100,2))+"%")
    m4.metric("WINNERS",     str(len(pdf[pdf["P&L $"]>0]))+"/"+str(len(pdf)))
    def _style(v):
        c = "#00FF41" if v > 0 else "#FF4444" if v < 0 else "#888"
        return "color: "+c
    st.dataframe(pdf.style.applymap(_style, subset=["P&L $","P&L %"]), use_container_width=True)
    if "GICS" in pdf.columns:
        st.markdown("**SECTOR CONCENTRATION**")
        sv = pdf.groupby("GICS")["Value"].sum()
        sp = (sv/sv.sum()*100).round(1)
        cs = ["#FF8000","#FFCC00","#00FF41","#4da6ff","#FF4488","#44FFCC","#888","#FFAA00"]
        ch = ""
        for i,(node,pct) in enumerate(sp.items()):
            c = cs[i%len(cs)]
            ch += ("<div style=\"display:flex;align-items:center;gap:8px;margin-bottom:6px;\">"
                   "<div style=\"width:10px;height:10px;background:"+c+";\"></div>"
                   "<div style=\"flex:1;font-size:10px;color:#888;\">"+str(node)+"</div>"
                   "<div style=\"width:120px;background:#1A1A1A;height:6px;\">"
                   "<div style=\"width:"+str(pct)+"%;background:"+c+";height:6px;\"></div></div>"
                   "<div style=\"width:40px;text-align:right;font-size:10px;color:"+c+";font-weight:700;\">"+str(pct)+"%</div>"
                   "</div>")
        st.markdown(ch, unsafe_allow_html=True)
    if st.button("CLEAR PORTFOLIO"):
        st.session_state.portfolio = []
        st.rerun()

# -- SIDEBAR -------------------------------------------------------
with st.sidebar:
    st.markdown("## SYSTEM CONFIG")
    st.markdown("---")
    st.markdown("### GICS NAVIGATOR")
    sg = st.selectbox("SELECT SECTOR", ["(Free entry)"]+list(GICS_UNIVERSE.keys()), key="sidebar_gics")
    if sg != "(Free entry)":
        reps = GICS_UNIVERSE.get(sg, [])
        st.markdown("<div style=\"color:#FF8000;font-size:10px;\">Rep: "+", ".join(reps)+"</div>", unsafe_allow_html=True)
        st.session_state["gics_ticker"] = reps[0] if reps else ""
    st.markdown("---")
    st.markdown("### EMAIL ALERTS")
    eon = st.toggle("Enable Alerts", value=False)
    if eon:
        ae = st.text_input("Email", placeholder="you@email.com")
        sh = st.text_input("SMTP Host", value="smtp.gmail.com")
        sp = st.number_input("SMTP Port", value=587)
        su = st.text_input("SMTP User", placeholder="sender@gmail.com")
        sw = st.text_input("SMTP Pass", type="password")
        st.session_state["alert_config"] = {"enabled":True,"email":ae,"smtp_host":sh,"smtp_port":sp,"smtp_user":su,"smtp_pass":sw}
    else:
        st.session_state["alert_config"] = {"enabled":False}
    st.markdown("---")
    st.markdown("<div class=\"cbadge\">FINRA RULE 15c3-5</div><br>"
                "<div class=\"cbadge\">SEC REG T</div><br>"
                "<div class=\"cbadge\">SEC REG NMS</div><br>"
                "<div class=\"cbadge\">INFORMATIONAL ONLY</div>",
                unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style=\"color:#2a2a2a;font-size:0.62rem;\">All signals informational only. Not financial advice.</div>", unsafe_allow_html=True)

def send_alert(ticker, signal, rationale):
    cfg = st.session_state.get("alert_config", {})
    if not cfg.get("enabled") or not cfg.get("email"): return
    try:
        msg = MIMEText("QUANT TERMINAL ALERT\n\nTicker: "+ticker+"\nSignal: "+signal+"\nRationale: "+rationale+"\n\nINFORMATIONAL ONLY - NOT FINANCIAL ADVICE")
        msg["Subject"] = "[QUANT] "+signal+" -- "+ticker
        msg["From"]    = cfg["smtp_user"]
        msg["To"]      = cfg["email"]
        with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"])) as srv:
            srv.starttls(); srv.login(cfg["smtp_user"], cfg["smtp_pass"]); srv.send_message(msg)
    except Exception: pass

# -- MACRO ROW -----------------------------------------------------
@st.cache_data(ttl=300)
def fetch_macro():
    try:
        d = yf.download(["^VIX","^TNX","^TYX","GC=F","CL=F","SPY","QQQ"], period="5d", progress=False, auto_adjust=True)
        c = d["Close"]
        if isinstance(c.columns, pd.MultiIndex): c.columns = c.columns.get_level_values(0)
        return c
    except Exception: return pd.DataFrame()

macro = fetch_macro()
def _mv(sym):
    try: return float(macro[sym].dropna().iloc[-1])
    except: return None

vix_v = _mv("^VIX"); tnx_v = _mv("^TNX"); tyx_v = _mv("^TYX")
gc_v  = _mv("GC=F"); cl_v  = _mv("CL=F"); spy_v = _mv("SPY"); qqq_v = _mv("QQQ")
vix_c = "#CC0000" if (vix_v or 0)>30 else "#FF8000" if (vix_v or 0)>20 else "#00CC00"

def _mc(label, val, sub="", color="#CCCCCC", fmt="{:.2f}"):
    try: v = fmt.format(val) if val is not None else "N/A"
    except: v = "N/A"
    return ("<div class=\"bbg-macro-cell\"><div class=\"bbg-macro-lbl\">"+label+"</div>"
            "<div class=\"bbg-macro-val\" style=\"color:"+color+"\">"+v+"</div>"
            "<div class=\"bbg-macro-sub\">"+sub+"</div></div>")

mrow = "<div class=\"bbg-macro-row\">"
mrow += _mc("VIX INDEX",  vix_v, "CBOE Fear",    vix_c)
mrow += _mc("10Y YIELD",  tnx_v, "US Treasury",  "#FF8000")
mrow += _mc("30Y YIELD",  tyx_v, "US Treasury",  "#FF8000")
mrow += _mc("GOLD",       gc_v,  "GC=F $/oz",    "#FFCC00", fmt="{:.0f}")
mrow += _mc("WTI CRUDE",  cl_v,  "CL=F $/bbl",   "#FF8000")
mrow += _mc("SPY",        spy_v, "S&P 500 ETF",  "#CCCCCC")
mrow += _mc("QQQ",        qqq_v, "NASDAQ ETF",   "#CCCCCC")
mrow += ("<div class=\"bbg-macro-cell\"><div class=\"bbg-macro-lbl\">MARKET</div>"
         "<div class=\"bbg-macro-val\" style=\"color:"+status_color+";font-size:11px;\">"+market_status+"</div>"
         "<div class=\"bbg-macro-sub\">NYSE/NASDAQ</div></div>")
mrow += ("<div class=\"bbg-macro-cell\"><div class=\"bbg-macro-lbl\">COMPLIANCE</div>"
         "<div class=\"bbg-macro-val\" style=\"color:#4da6ff;font-size:8px;\">FINRA 15c3-5</div>"
         "<div class=\"bbg-macro-sub\">SEC REG T/NMS</div></div>")
mrow += ("<div class=\"bbg-macro-cell\"><div class=\"bbg-macro-lbl\">DATA</div>"
         "<div class=\"bbg-macro-val\" style=\"color:#00CC00;font-size:9px;\">LIVE</div>"
         "<div class=\"bbg-macro-sub\">Yahoo Finance</div></div>")
mrow += "</div>"
st.markdown(mrow, unsafe_allow_html=True)

# -- TABS ----------------------------------------------------------
tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "  SUREFIRE  ","  LONG-TERM  ","  SWING  ",
    "  FAT PITCH  ","  SOLOMON  ","  PORTFOLIO  "
])

gics_default = st.session_state.get("gics_ticker","SPY")

# -- TAB 1: SUREFIRE -----------------------------------------------
with tab1:
    st.markdown("<div class=\"bbg-panel\"><div class=\"bbg-panel-hdr\">SUREFIRE BUY/SELL - ULTRA-STRICT CONFLUENCE SCANNER</div><div class=\"bbg-panel-body\">Requires 5/7 score: EMA stack, MACD cross, BB breakout, RSI, Stochastic, volume 1.3x, ADX 30. FINRA 15c3-5 compliant.</div></div>", unsafe_allow_html=True)
    ct1,cb1 = st.columns([3,1])
    with ct1: sft = st.text_input("TICKER", value=gics_default, key="sf_ticker", placeholder="SPY, QQQ, NVDA...")
    with cb1: st.markdown("<br>", unsafe_allow_html=True); rsf = st.button("> SCAN", key="run_sf")
    if rsf:
        with st.spinner("Analyzing "+sft.upper()+"..."):
            drf = fetch_data(sft.upper()); dif = compute_indicators(drf); res = evaluate_surefire(dif)
        if dif.empty: st.error("Failed to retrieve data.")
        else:
            show_signal_card(res); show_trade_levels(res); show_rationale(res)
            if res["signal"] != "STANDBY": send_alert(sft, res["signal"], " | ".join(res.get("reasons",[])))
            st.plotly_chart(build_chart(dif.tail(120), sft.upper(), res), use_container_width=True)
            show_backtest(dif, "surefire")
    st.markdown("---")
    st.markdown("<div class=\"bbg-panel-hdr\">UNIVERSE SCAN - ALL 25 GICS NODES</div>", unsafe_allow_html=True)
    if st.button("SCAN ALL GICS SECTORS", key="scan_sf"):
        with st.spinner("Scanning..."): results = run_universe_scan("surefire")
        if results: st.success(str(len(results))+" signal(s) detected."); st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.warning("No signals. Capital preserved.")

# -- TAB 2: LONG-TERM ----------------------------------------------
with tab2:
    st.markdown("<div class=\"bbg-panel\"><div class=\"bbg-panel-hdr\">LONG-TERM MONTHLY - POSITION TRADE SCANNER</div><div class=\"bbg-panel-body\">Secular trend following. Golden/Death Cross, 200 EMA, Fibonacci, MACD. Hold weeks to months.</div></div>", unsafe_allow_html=True)
    ct2,cb2 = st.columns([3,1])
    with ct2: ltt = st.text_input("TICKER", value="QQQ", key="lt_ticker")
    with cb2: st.markdown("<br>", unsafe_allow_html=True); rlt = st.button("> SCAN", key="run_lt")
    if rlt:
        with st.spinner("Analyzing "+ltt.upper()+"..."):
            drf = fetch_data(ltt.upper(), period="3y"); dif = compute_indicators(drf); res = evaluate_longterm(dif)
        if dif.empty: st.error("Failed to retrieve data.")
        else:
            show_signal_card(res); show_trade_levels(res); show_rationale(res)
            if res["signal"] != "STANDBY": send_alert(ltt, res["signal"], " | ".join(res.get("reasons",[])))
            st.plotly_chart(build_chart(dif.tail(250), ltt.upper(), res), use_container_width=True)
            show_backtest(dif, "longterm")
    st.markdown("---")
    st.markdown("<div class=\"bbg-panel-hdr\">UNIVERSE SCAN - ALL 25 GICS NODES</div>", unsafe_allow_html=True)
    if st.button("SCAN ALL GICS SECTORS", key="scan_lt"):
        with st.spinner("Scanning..."): results = run_universe_scan("longterm")
        if results: st.success(str(len(results))+" signal(s) detected."); st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.warning("No signals.")

# -- TAB 3: SWING --------------------------------------------------
with tab3:
    st.markdown("<div class=\"bbg-panel\"><div class=\"bbg-panel-hdr\">SWING TRADING - MEAN REVERSION + MOMENTUM</div><div class=\"bbg-panel-body\">2-10 day mean reversion. BB extremes, oversold RSI, Stochastic cross. ADX gate removed for swing.</div></div>", unsafe_allow_html=True)
    ct3,cb3 = st.columns([3,1])
    with ct3: swt = st.text_input("TICKER", value="NVDA", key="sw_ticker")
    with cb3: st.markdown("<br>", unsafe_allow_html=True); rsw = st.button("> SCAN", key="run_sw")
    if rsw:
        with st.spinner("Analyzing "+swt.upper()+"..."):
            drf = fetch_data(swt.upper(), period="6mo"); dif = compute_indicators(drf); res = evaluate_swing(dif)
        if dif.empty: st.error("Failed to retrieve data.")
        else:
            show_signal_card(res); show_trade_levels(res); show_rationale(res)
            if res["signal"] != "STANDBY": send_alert(swt, res["signal"], " | ".join(res.get("reasons",[])))
            st.plotly_chart(build_chart(dif.tail(90), swt.upper(), res), use_container_width=True)
            show_backtest(dif, "swing")
    st.markdown("---")
    st.markdown("<div class=\"bbg-panel-hdr\">UNIVERSE SCAN - ALL 25 GICS NODES</div>", unsafe_allow_html=True)
    if st.button("SCAN ALL GICS SECTORS", key="scan_sw"):
        with st.spinner("Scanning..."): results = run_universe_scan("swing")
        if results: st.success(str(len(results))+" signal(s) detected."); st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.warning("No signals.")

# -- TAB 4: FAT PITCH ----------------------------------------------
with tab4:
    st.markdown("<div class=\"bbg-panel\"><div class=\"bbg-panel-hdr\">FAT PITCH - ORIGINAL 3-GATE MAXIMUM CONVICTION SCANNER</div><div class=\"bbg-panel-body\">Gate 1: Volume >= 1.5x avg | Gate 2: ADX >= 35 | Gate 3: BB breakout + MACD + RSI 60-85. All 3 must fire. No compromises.</div></div>", unsafe_allow_html=True)
    ct4,cb4 = st.columns([3,1])
    with ct4: fpt = st.text_input("TICKER", value="SPY", key="fp_ticker")
    with cb4: st.markdown("<br>", unsafe_allow_html=True); rfp = st.button("> SCAN FOR FAT PITCH", key="run_fp")
    if rfp:
        with st.spinner("Running 3-gate analysis on "+fpt.upper()+"..."):
            drf = fetch_data(fpt.upper()); dif = compute_indicators(drf); res = evaluate_fat_pitch(dif)
        if dif.empty: st.error("Failed to retrieve data.")
        else:
            show_signal_card(res, style="fat"); show_trade_levels(res); show_rationale(res)
            if res["signal"] != "STANDBY": send_alert(fpt, res["signal"], " | ".join(res.get("reasons",[])))
            st.plotly_chart(build_chart(dif.tail(120), fpt.upper(), res), use_container_width=True)
            show_backtest(dif, "fatpitch")
    st.markdown("---")
    st.markdown("<div class=\"bbg-panel-hdr\">FAT PITCH UNIVERSE SCAN - ALL 25 GICS NODES</div>", unsafe_allow_html=True)
    if st.button("SCAN ALL GICS FOR FAT PITCH", key="scan_fp"):
        with st.spinner("Running 3-gate scan..."): results = run_universe_scan("fatpitch")
        if results: st.success(str(len(results))+" FAT PITCH setup(s) - rare maximum-conviction signals."); st.dataframe(pd.DataFrame(results), use_container_width=True)
        else: st.warning("SCAN COMPLETE: Zero Fat Pitch setups. Capital preserved. Standby.")

# -- TAB 5: SOLOMON ------------------------------------------------
with tab5:
    st.markdown("<div class=\"bbg-panel\"><div class=\"bbg-panel-hdr\">SOLOMON STRATEGY - QUANTITATIVE ROTATION - 32 ASSETS - 7-CRITERIA SCORING</div><div class=\"bbg-panel-body\">Multi-factor rotation across 32 ETFs. Scores RAM, Relative Strength, 50D Slope, Volume CF, ROC. Top 5 get allocation signals.</div></div>", unsafe_allow_html=True)
    if st.button("> RUN SOLOMON STRATEGY SCAN", key="run_solomon"):
        with st.spinner("Loading Solomon universe..."):
            sol_data = fetch_solomon_data()
            sol_df   = calculate_solomon(sol_data, sol_data["Close"].index[-1], vix_v or 15.0)
        if sol_df.empty:
            st.error("Failed to compute Solomon factors.")
        else:
            top5 = sol_df[sol_df["RNK"] <= 5]
            ch = "<div class=\"bbg-panel\"><div class=\"bbg-panel-hdr\">TOP 5 ROTATION TARGETS</div><div class=\"bbg-top5\">"
            for tkr,row in top5.iterrows():
                strong  = row["SIGNAL"] == "STRONG BUY"
                cc      = "bbg-t5c strong" if strong else "bbg-t5c buy"
                sc      = "#FF8000" if strong else "#FFCC00"
                sl      = "STRONG BUY" if strong else "BUY"
                ytdc    = "ytd-pos" if row["YTD"]>0 else "ytd-neg"
                aw      = min(row["ALLOC"]*5,100)
                ch += ("<div class=\""+cc+"\">"
                       "<div class=\"bbg-t5-tkr\">"+str(tkr)+"</div>"
                       "<div class=\"bbg-t5-sec\">"+str(row["SECTOR"])+"</div>"
                       "<div class=\"bbg-t5-sig\" style=\"color:"+sc+"\">"+sl+"</div>"
                       "<div class=\"bbg-t5-alloc\">ALLOC "+str(round(row["ALLOC"],1))+"%</div>"
                       "<div class=\"bar-bg\"><div class=\"bar-fill\" style=\"width:"+str(aw)+"%;background:"+sc+";\"></div></div>"
                       "<div class=\"bbg-t5-rsn\">Score "+str(round(row["SCORE"],1))+" ADX "+str(round(row["ADX"],0))+" "+str(row["REASON"])+"</div>"
                       "</div>")
            ch += "</div></div>"
            st.markdown(ch, unsafe_allow_html=True)

            def sc_cls(s):
                if "STRONG BUY" in s: return "sig-sb"
                if "BUY" in s:        return "sig-b"
                if "HOLD" in s:       return "sig-h"
                if "HALT" in s:       return "sig-ht"
                if "STRONG SELL" in s:return "sig-ss"
                return "sig-s"

            th = ("<div class=\"bbg-panel\" style=\"margin-top:4px;\">"
                  "<div class=\"bbg-panel-hdr\">SOLOMON FULL LEDGER - 32 ASSETS</div>"
                  "<div class=\"bbg-scroll\"><table class=\"bbg-tbl\"><thead><tr>"
                  "<th class=\"l\">TKR</th><th>RNK</th><th class=\"l\">SECTOR</th>"
                  "<th class=\"l\">SIGNAL</th><th class=\"l\">REASON</th>"
                  "<th>ALLOC</th><th>PRICE</th><th>STOP</th><th>ADX</th>"
                  "<th>SCORE</th><th>YTD</th><th>1M%</th><th>3M%</th>"
                  "</tr></thead><tbody>")
            for tkr,row in sol_df.iterrows():
                sc  = sc_cls(row["SIGNAL"])
                yc  = "#00CC00" if row["YTD"]>0 else "#CC0000"
                al  = str(round(row["ALLOC"],1))+"%" if row["ALLOC"]>0 else "--"
                th += ("<tr>"
                       "<td class=\"l\">"+str(tkr)+"</td>"
                       "<td>"+str(row["RNK"])+"</td>"
                       "<td class=\"sec\">"+str(row["SECTOR"])+"</td>"
                       "<td class=\"l "+sc+"\">"+str(row["SIGNAL"])+"</td>"
                       "<td class=\"l\" style=\"color:#444;font-size:9px;\">"+str(row["REASON"])+"</td>"
                       "<td style=\"color:#FF8000;\">"+al+"</td>"
                       "<td>"+str(round(row["PRICE"],2))+"</td>"
                       "<td style=\"color:#CC0000;\">"+str(round(row["STOP"],2))+"</td>"
                       "<td>"+str(round(row["ADX"],1))+"</td>"
                       "<td style=\"color:#FF8000;\">"+str(round(row["SCORE"],1))+"</td>"
                       "<td style=\"color:"+yc+"\">"+str(round(row["YTD"],1))+"%</td>"
                       "<td>"+str(round(row["R1M"],1))+"%</td>"
                       "<td>"+str(round(row["R3M"],1))+"%</td>"
                       "</tr>")
            th += "</tbody></table></div></div>"
            st.markdown(th, unsafe_allow_html=True)

            st.markdown("<div class=\"bbg-panel\" style=\"margin-top:4px;\">"
                        "<div class=\"bbg-panel-hdr\">SOLOMON 7-CRITERIA CHECKLIST</div>"
                        "<div class=\"bbg-panel-body\" style=\"color:#555;font-size:9px;\">"
                        "1. Above 200MA &nbsp; 2. ADX > 25 &nbsp; 3. Vol CF > 1.2x &nbsp; "
                        "4. RAM > 0 &nbsp; 5. Rel Strength > SPY &nbsp; 6. ROC Accelerating &nbsp; 7. 50D Slope Rising -- "
                        "ALL 7 must pass for STRONG BUY. FINRA 15c3-5 compliant. Informational only."
                        "</div></div>", unsafe_allow_html=True)

            hm = "<div class=\"bbg-panel\" style=\"margin-top:4px;\">"
            hm += "<div class=\"bbg-panel-hdr\">MOMENTUM HEATMAP</div><div class=\"bbg-hm\">"
            mx_ = sol_df["SCORE"].max(); mn_ = sol_df["SCORE"].min()
            for tkr,row in sol_df.sort_values("SCORE",ascending=False).iterrows():
                s = row["SCORE"]
                n = (s-mn_)/(mx_-mn_) if mx_!=mn_ else 0.5
                bg = "rgb(0,"+str(int(n*140)+20)+",0)" if n>0.5 else "rgb("+str(int((1-n)*120))+",20,0)"
                fg = "#FF8000" if n>0.7 else "#FFCC00" if n>0.4 else "#CC3333"
                bd = "border:1px solid #FF8000;" if "BUY" in row["SIGNAL"] else "border:1px solid #1A1A1A;"
                hm += "<div class=\"bbg-hm-cell\" style=\"background:"+bg+";color:"+fg+";"+bd+"\"><span>"+str(tkr)+"</span><span>"+str(round(s,0))+"</span></div>"
            hm += "</div></div>"
            st.markdown(hm, unsafe_allow_html=True)
    else:
        st.info("Click RUN SOLOMON STRATEGY SCAN to load rotation analysis.")

# -- TAB 6: PORTFOLIO ----------------------------------------------
with tab6:
    portfolio_section()

# -- TICKER TAPE ---------------------------------------------------
tape_items = []
for sym in ["SPY","QQQ","DIA","^VIX","^TNX","GC=F","CL=F"]:
    try:
        col_ = macro[sym].dropna()
        cur  = float(col_.iloc[-1]); prv = float(col_.iloc[-2])
        pct  = ((cur-prv)/prv)*100
        pc   = "#00CC00" if pct>=0 else "#CC0000"
        lbl  = sym.replace("^","").replace("=F","")
        tape_items.append("<span style=\"margin-right:24px;\"><span style=\"color:#FF8000;font-weight:700;\">"+lbl+"</span> <span style=\"color:#CCC;\">"+str(round(cur,2))+"</span> <span style=\"color:"+pc+"\">"+str(round(pct,2))+"%</span></span>")
    except Exception: pass

if tape_items:
    st.markdown("<div style=\"position:fixed;bottom:0;left:0;width:100%;background:#000;border-top:1px solid #FF8000;padding:4px 12px;font-size:10px;display:flex;gap:4px;z-index:9998;\">"+"".join(tape_items)+"</div>", unsafe_allow_html=True)st.markdown(”<div style="position:fixed;bottom:0;left:0;width:100%;background:#000;border-top:1px solid #FF8000;padding:4px 12px;font-size:10px;display:flex;gap:4px;z-index:9998;">”+””.join(tape_items)+”</div>”, unsafe_allow_html=True)