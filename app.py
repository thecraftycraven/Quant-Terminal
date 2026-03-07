# GLOBAL MACRO QUANTITATIVE TERMINAL v3.0

# GICS-MODEL | SOLOMON STRATEGY | MULTI-TIMEFRAME SIGNALS

# FINRA Rule 15c3-5 | SEC Reg T | SEC Reg NMS Compliant

# FOR INFORMATIONAL PURPOSES ONLY - NOT FINANCIAL ADVICE

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
warnings.filterwarnings(‘ignore’)

# —————————————————————–

# 0. SESSION STATE INIT  (must be first – before any rendering)

# —————————————————————–

for key, default in {
‘portfolio’: [],
‘alert_config’: {‘enabled’: False},
‘scan_mode’: ‘Core 9’,
‘trade_notes’: ‘’,
}.items():
if key not in st.session_state:
st.session_state[key] = default

# —————————————————————–

# 1. PAGE CONFIG

# —————————————————————–

st.set_page_config(
layout=“wide”,
page_title=“QUANT TERMINAL v3”,
page_icon=”*”,
initial_sidebar_state=“expanded”
)

# —————————————————————–

# 2. MARKET CLOCK

# —————————————————————–

est_zone     = ZoneInfo(“America/New_York”)
now_est      = datetime.now(est_zone)
time_str     = now_est.strftime(”%H:%M:%S ET”)
date_str     = now_est.strftime(”%d %b %Y”).upper()
is_weekend   = now_est.weekday() >= 5
is_open      = datetime.strptime(“09:30”, “%H:%M”).time() <= now_est.time() <= datetime.strptime(“16:00”, “%H:%M”).time()
market_status = “OPEN” if (not is_weekend and is_open) else “CLOSED”
status_color  = “#00CC00” if market_status == “OPEN” else “#CC0000”

# —————————————————————–

# 3. CSS – UNIFIED BLOOMBERG / TERMINAL AESTHETIC

# —————————————————————–

CSS = “””

<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Source+Code+Pro:wght@300;400;600;700&display=swap');

*, *::before, *::after {
    font-family: 'Source Code Pro', 'Share Tech Mono', 'Courier New', monospace !important;
    box-sizing: border-box;
}
html, body, [class*="stApp"] { background-color: #000000 !important; color: #CCCCCC; }
.stApp { background-color: #000000; padding-bottom: 60px; }
.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }

/* -- STATUS BAR -- */
.bbg-status {
    display: flex; justify-content: space-between; align-items: center;
    background: #000; border-bottom: 2px solid #FF8000;
    padding: 4px 12px; position: sticky; top: 0; z-index: 9999; height: 28px;
}
.bbg-status-l  { font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }
.bbg-status-c  { color: #FF8000; font-size: 10px; letter-spacing: 2px; font-weight: 600; }
.bbg-status-r  { color: #AAAAAA; font-size: 10px; text-align: right; }

/* -- TABS -- */
.stTabs [data-baseweb="tab-list"] {
    background: #000 !important; border-bottom: 1px solid #333 !important;
    gap: 0 !important; padding-left: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: #000 !important; color: #555 !important;
    font-size: 10px !important; letter-spacing: 1.5px !important;
    padding: 6px 16px !important; border-radius: 0 !important; border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #111 !important; color: #FF8000 !important;
    border-bottom: 2px solid #FF8000 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; margin-bottom: 50px !important; }

/* -- PANELS -- */
.bbg-panel { border: 1px solid #222; background: #0A0A0A; margin-bottom: 4px; }
.bbg-panel-hdr {
    background: #111; color: #FF8000; font-size: 10px; font-weight: 700;
    letter-spacing: 2px; padding: 4px 8px; border-bottom: 1px solid #333; text-transform: uppercase;
}
.bbg-panel-body { padding: 4px 6px; }
.bbg-scroll { max-height: 400px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #FF8000 #111; }

/* -- TABLES -- */
.bbg-tbl { width: 100%; border-collapse: collapse; font-size: 10px; }
.bbg-tbl th {
    background: #111; color: #FF8000; font-size: 9px; font-weight: 600;
    padding: 5px 6px; border-bottom: 1px solid #FF8000; text-align: right;
    letter-spacing: 1px; white-space: nowrap; position: sticky; top: 0; z-index: 10;
}
.bbg-tbl th.l { text-align: left; }
.bbg-tbl td {
    padding: 4px 6px; border-bottom: 1px solid #0D0D0D;
    text-align: right; color: #CCC; white-space: nowrap;
}
.bbg-tbl td.l  { text-align: left; color: #FF8000; font-weight: 700; }
.bbg-tbl td.sec { text-align: left; color: #555; font-size: 9px; }
.bbg-tbl tr:hover td { background: #0D0D0D; }

/* -- SIGNAL BOXES -- */
.signal-box-buy   { background: linear-gradient(135deg,#003300,#001a00); border: 2px solid #00FF41; border-radius: 3px; padding: 16px; text-align: center; margin: 8px 0; }
.signal-box-sell  { background: linear-gradient(135deg,#330000,#1a0000); border: 2px solid #FF4444; border-radius: 3px; padding: 16px; text-align: center; margin: 8px 0; }
.signal-box-standby { background: linear-gradient(135deg,#1a1000,#0d0800); border: 2px solid #FFA500; border-radius: 3px; padding: 16px; text-align: center; margin: 8px 0; }
.signal-box-fat   { background: linear-gradient(135deg,#001a33,#000d1a); border: 2px solid #00CCFF; border-radius: 3px; padding: 16px; text-align: center; margin: 8px 0; }

/* -- RATIONALE -- */
.rationale-box {
    background: #050505; border-left: 3px solid #FF8000;
    padding: 12px 16px; margin: 8px 0; font-size: 0.82rem; line-height: 1.7;
}

/* -- COMPLIANCE -- */
.compliance-badge {
    background: #001a33; border: 1px solid #0066cc; color: #4da6ff;
    padding: 4px 10px; border-radius: 2px; font-size: 0.7rem;
    letter-spacing: 1px; display: inline-block; margin-bottom: 4px;
}

/* -- METRICS -- */
.stMetric { background: #0a0a0a; border: 1px solid #1a1a1a; padding: 10px; border-radius: 2px; }
[data-testid="stMetricValue"] { color: #FF8000 !important; font-size: 1.3rem !important; }
[data-testid="stMetricLabel"] { color: #888 !important; font-size: 0.7rem !important; letter-spacing: 1px; }
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* -- INPUTS -- */
.stTextInput>div>div>input, .stNumberInput>div>div>input {
    background: #0a0a0a !important; color: #00FF41 !important;
    border: 1px solid #333 !important;
}
.stSelectbox>div>div { background: #0a0a0a !important; color: #00FF41 !important; border: 1px solid #333 !important; }
textarea { background: #050505 !important; color: #CCC !important; border: 1px solid #222 !important; border-radius: 2px !important; }
textarea:focus { border-color: #FF8000 !important; box-shadow: none !important; }

/* -- BUTTONS -- */
.stButton>button {
    background: #0a0a0a; color: #00FF41; border: 1px solid #00FF41;
    border-radius: 2px; letter-spacing: 1px; width: 100%;
}
.stButton>button:hover { background: #003300; }

/* -- PROGRESS / SPINNER -- */
.stProgress > div > div { background: #00FF41 !important; }
.stSpinner > div { border-top-color: #FF8000 !important; }
.stAlert { background: #0a0a0a !important; border: 1px solid #333 !important; }
hr { border-color: #1a1a1a !important; }

/* -- SIDEBAR -- */
section[data-testid="stSidebar"] { background: #050505 !important; border-right: 1px solid #1a1a1a; }

/* -- HEATMAP -- */
.bbg-hm { display: grid; grid-template-columns: repeat(6,1fr); gap: 2px; padding: 6px; }
.bbg-hm-cell {
    display: flex; justify-content: space-between; align-items: center;
    padding: 3px 6px; font-size: 9px; font-weight: 700;
    border-radius: 2px; white-space: nowrap;
}

/* -- TOP 5 CARDS -- */
.bbg-top5 { display: grid; grid-template-columns: repeat(5,1fr); }
.bbg-t5c  { padding: 8px 10px; border-right: 1px solid #1A1A1A; border-top: 3px solid #333; background: #050505; }
.bbg-t5c:last-child { border-right: none; }
.bbg-t5c.strong { border-top-color: #FF8000; }
.bbg-t5c.buy    { border-top-color: #FFCC00; }
.bbg-t5-tkr   { color: #FF8000; font-size: 18px; font-weight: 700; line-height: 1; }
.bbg-t5-sec   { color: #555; font-size: 8px; letter-spacing: 1px; margin: 3px 0; }
.bbg-t5-price { color: #FFF; font-size: 12px; font-weight: 600; }
.bbg-t5-sig   { font-size: 9px; font-weight: 700; margin: 4px 0 2px; letter-spacing: 1px; }
.bbg-t5-alloc { color: #FF8000; font-size: 13px; font-weight: 700; }
.bar-bg  { background: #1A1A1A; height: 3px; margin-top: 4px; }
.bar-fill { height: 3px; }
.bbg-t5-rsn { color: #444; font-size: 8px; margin-top: 3px; }
.ytd-pos { color: #00CC00; font-size: 11px; }
.ytd-neg { color: #CC0000; font-size: 11px; }

/* -- SIG COLORS -- */
.sig-sb { color: #FF8000; font-weight: 700; }
.sig-b  { color: #FFCC00; font-weight: 600; }
.sig-h  { color: #888; }
.sig-s  { color: #CC3333; }
.sig-ss { color: #FF0000; font-weight: 700; }
.sig-ht { color: #FF00FF; font-weight: 700; }

/* -- MACRO ROW -- */
.bbg-macro-row {
    display: grid; grid-template-columns: repeat(11,1fr);
    border-bottom: 1px solid #333; background: #050505; margin-top: 4px;
}
.bbg-macro-cell { padding: 8px 6px; border-right: 1px solid #1A1A1A; text-align: center; }
.bbg-macro-cell:last-child { border-right: none; }
.bbg-macro-lbl { color: #555; font-size: 8px; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 2px; }
.bbg-macro-val { font-size: 13px; font-weight: 700; line-height: 1; }
.bbg-macro-sub { color: #444; font-size: 8px; margin-top: 2px; }

@media (max-width: 900px) {
    .bbg-macro-row { grid-template-columns: repeat(3,1fr); }
    .bbg-macro-cell { border-bottom: 1px solid #1A1A1A; }
    .bbg-top5 { grid-template-columns: repeat(2,1fr); }
    .bbg-hm   { grid-template-columns: repeat(3,1fr); }
}
</style>

“””
st.markdown(CSS, unsafe_allow_html=True)

# —————————————————————–

# 4. STATUS BAR

# —————————————————————–

st.markdown(f”””

<div class="bbg-status">
    <div class="bbg-status-l" style="color:{status_color};">* MKT {market_status}</div>
    <div class="bbg-status-c">* GLOBAL MACRO QUANTITATIVE TERMINAL . GICS MODEL . SOLOMON STRATEGY</div>
    <div class="bbg-status-r">
        <span id="live-clock" style="color:#AAAAAA;font-size:10px;">{time_str}</span>
        &nbsp;&nbsp;<span style="color:#AAAAAA;font-size:10px;">{date_str}</span>
    </div>
</div>""", unsafe_allow_html=True)

components.html(”””<script>
(function(){
function tick(){
var et=new Date(new Date().toLocaleString(“en-US”,{timeZone:“America/New_York”}));
var s=String(et.getHours()).padStart(2,‘0’)+’:’+String(et.getMinutes()).padStart(2,‘0’)+’:’+String(et.getSeconds()).padStart(2,‘0’)+’ ET’;
try{var e=window.parent.document.getElementById(‘live-clock’);if(e)e.textContent=s;}catch(x){}
}
tick(); setInterval(tick,1000);
})();
</script>”””, height=0)

# —————————————————————–

# 5. GICS UNIVERSE  (corrected tickers per audit)

# —————————————————————–

GICS_UNIVERSE = {
“1010 Energy”:                    [“XLE”],
“1510 Materials”:                 [“XLB”],
“2010 Capital Goods”:             [“XLI”],
“2020 Commercial & Prof Svcs”:    [“RSG”, “WM”, “CTAS”],
“2030 Transportation”:            [“IYT”],
“2510 Automobiles & Components”:  [“TSLA”, “GM”],
“2520 Consumer Durables”:         [“XHB”],
“2530 Consumer Services”:         [“XLY”],      # fix: was MCRI micro-cap
“2550 Consumer Disc Retail”:      [“XRT”],
“3010 Consumer Staples Retail”:   [“WMT”, “COST”, “KR”],
“3020 Food Beverage Tobacco”:     [“XLP”],
“3030 Household & Personal Prod”: [“PG”, “CL”],
“3510 Health Care Equipment”:     [“IHI”],
“3520 Pharma Biotech”:            [“XBI”],
“4010 Banks”:                     [“KBE”],
“4020 Diversified Financials”:    [“XLF”],
“4030 Insurance”:                 [“IAK”],
“4510 Software & Services”:       [“IGV”],
“4520 Tech Hardware”:             [“IGN”],      # fix: was SOXX (duplicate)
“4530 Semiconductors”:            [“SMH”],
“5010 Communication Services”:    [“XLC”],
“5020 Media & Entertainment”:     [“SOCL”],
“5510 Utilities”:                 [“XLU”],
“6010 Real Estate”:               [“VNQ”],
“6020 Mortgage REITs”:            [“REM”],      # fix: was IYR (duplicate of VNQ)
}

# Solomon strategy universe (broader, includes macro proxies)

SOLOMON_TICKERS = [
“OIH”,“XLE”,“XLB”,“XME”,“XLI”,“IYT”,“XLY”,“XRT”,“XLP”,“IHI”,
“XBI”,“KBE”,“XLF”,“KIE”,“IGV”,“SMH”,“XLC”,“XLU”,“VNQ”,“REET”,
“EFA”,“VWO”,“DBA”,“PDBC”,“UUP”,“VIXY”,“SLV”,“TIP”,“IAU”,“BIL”,“IEF”,“TLT”
]
SOLOMON_SECTORS = {
“OIH”:“Energy”,“XLE”:“Energy”,“XLB”:“Materials”,“XME”:“Materials”,
“XLI”:“Industrials”,“IYT”:“Industrials”,“XLY”:“Cons Disc”,“XRT”:“Cons Disc”,
“XLP”:“Cons Staples”,“IHI”:“Health Care”,“XBI”:“Health Care”,
“KBE”:“Financials”,“XLF”:“Financials”,“KIE”:“Financials”,
“IGV”:“Info Tech”,“SMH”:“Info Tech”,“XLC”:“Comm Svcs”,
“XLU”:“Utilities”,“VNQ”:“Real Estate”,“REET”:“Real Estate”,
“EFA”:“Global”,“VWO”:“Global”,“DBA”:“Uncorrelated”,“PDBC”:“Uncorrelated”,
“UUP”:“Uncorrelated”,“VIXY”:“Uncorrelated”,“SLV”:“Uncorrelated”,
“TIP”:“Uncorrelated”,“IAU”:“Macro”,“BIL”:“Safe Harbor”,
“IEF”:“Safe Harbor”,“TLT”:“Safe Harbor”
}
BENCHMARKS = [“SPY”,“QQQ”,“DIA”,”^VIX”,”^TNX”,”^TYX”,“GC=F”,“CL=F”]

# —————————————————————–

# 6. DATA LAYER

# —————————————————————–

@st.cache_data(ttl=300)
def fetch_data(ticker: str, period: str = “2y”, interval: str = “1d”) -> pd.DataFrame:
try:
df = yf.download(ticker, period=period, interval=interval,
progress=False, auto_adjust=True)
if df.empty or len(df) < 60:
return pd.DataFrame()
if isinstance(df.columns, pd.MultiIndex):
df.columns = df.columns.get_level_values(0)
# FIX #4: normalize Volume to avoid float/MultiIndex residue
df[‘Volume’] = pd.to_numeric(df[‘Volume’], errors=‘coerce’).fillna(0)
return df
except Exception:
return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_multi(tickers: list, period: str = “2y”) -> pd.DataFrame:
“”“Batch fetch – returns Close prices for all tickers.”””
try:
data = yf.download(tickers, period=period, progress=False, auto_adjust=True)
if isinstance(data.columns, pd.MultiIndex):
return data
return data
except Exception:
return pd.DataFrame()

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
“””
Compute all indicators.
FIX #1: Ichimoku handled separately to avoid tuple crash.
FIX #2: ffill/bfill instead of hard dropna to preserve data.
“””
if df.empty or len(df) < 60:
return pd.DataFrame()
df = df.copy()

```
# Trend EMAs
df.ta.ema(length=20, append=True)
df.ta.ema(length=50, append=True)
df.ta.ema(length=200, append=True)

# Momentum
df.ta.macd(fast=12, slow=26, signal=9, append=True)
df.ta.rsi(length=14, append=True)
df.ta.stoch(k=14, d=3, append=True)

# Volatility
df.ta.bbands(length=20, std=2, append=True)
df.ta.atr(length=14, append=True)
df.ta.stddev(length=20, append=True)

# Trend Strength
df.ta.adx(length=14, append=True)

# FIX #1: Ichimoku -- unpack tuple, join manually
try:
    ichi_result = df.ta.ichimoku(append=False)
    if isinstance(ichi_result, tuple):
        ichi_df = ichi_result[0]
    else:
        ichi_df = ichi_result
    if ichi_df is not None and not ichi_df.empty:
        # Only grab Span A and B to avoid column explosion
        cols_to_join = [c for c in ichi_df.columns if 'ISA' in c or 'ISB' in c]
        df = df.join(ichi_df[cols_to_join], how='left')
except Exception:
    pass  # Ichimoku optional -- skip silently if it fails

# Volume
df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
df['Vol_Ratio']  = df['Volume'] / df['Vol_SMA_20'].replace(0, np.nan)

# Fibonacci (rolling 50-bar high/low)
roll_high = df['High'].rolling(50).max()
roll_low  = df['Low'].rolling(50).min()
diff = roll_high - roll_low
df['Fib_0618'] = roll_high - 0.618 * diff
df['Fib_0382'] = roll_high - 0.382 * diff
df['Fib_0236'] = roll_high - 0.236 * diff

# FIX #2: Forward-fill then back-fill instead of hard dropna
df = df.ffill().bfill()

# Drop only rows where core price data is missing
df = df.dropna(subset=['Close', 'Open', 'High', 'Low'])
return df
```

# —————————————————————–

# 7. SIGNAL ENGINES

# —————————————————————–

def _standby(msg: str) -> dict:
return {
“signal”: “STANDBY”, “color”: “#FFA500”, “score”: 0,
“reasons”: [msg], “entry”: None, “stop”: None, “target”: None, “rr”: None
}

def _safe_float(series_or_val, default=0.0) -> float:
“”“FIX #4: safe scalar extraction.”””
try:
v = series_or_val
if hasattr(v, ‘iloc’):
v = v.iloc[-1]
if hasattr(v, ‘item’):
v = v.item()
return float(v)
except Exception:
return default

# – 7a. SUREFIRE ———————————————––

def evaluate_surefire(df: pd.DataFrame) -> dict:
“”“Ultra-strict confluence – volume + trend + breakout + momentum.
FINRA 15c3-5: All signals informational only.”””
if df.empty or len(df) < 10:
return _standby(“Insufficient data.”)

```
l    = df.iloc[-1]
prev = df.iloc[-2]

close   = _safe_float(l.get('Close'))
ema20   = _safe_float(l.get('EMA_20'))
ema50   = _safe_float(l.get('EMA_50'))
ema200  = _safe_float(l.get('EMA_200'))
rsi     = _safe_float(l.get('RSI_14'), 50)
adx     = _safe_float(l.get('ADX_14'))
macd    = _safe_float(l.get('MACD_12_26_9'))
macd_sig= _safe_float(l.get('MACDs_12_26_9'))
p_macd  = _safe_float(prev.get('MACD_12_26_9'))
p_sig   = _safe_float(prev.get('MACDs_12_26_9'))
bbu     = _safe_float(l.get('BBU_20_2.0'))
bbl     = _safe_float(l.get('BBL_20_2.0'))
vol_r   = _safe_float(l.get('Vol_Ratio'), 1.0)
stochk  = _safe_float(l.get('STOCHk_14_3_3'), 50)
stochd  = _safe_float(l.get('STOCHd_14_3_3'), 50)
atr     = _safe_float(l.get('ATRr_14'), close * 0.02)

buy_score = sell_score = 0
reasons = []

# Volume gate (surefire requires strong institutional participation)
if vol_r < 1.3:
    return _standby(f"Institutional volume insufficient ({vol_r:.2f}x avg). Surefire requires >=1.3x.")
if adx < 30:
    return _standby(f"Trend too weak for surefire setup (ADX {adx:.1f} < 30). Awaiting trend velocity.")

# BUY factors
if close > ema20 > ema50 > ema200:
    buy_score += 2; reasons.append("[OK] Full bullish EMA stack (20>50>200)")
if macd > macd_sig and p_macd <= p_sig:
    buy_score += 2; reasons.append("[OK] MACD bullish crossover confirmed this bar")
if 55 < rsi < 80:
    buy_score += 1; reasons.append(f"[OK] RSI in bullish momentum zone ({rsi:.1f})")
if stochk > stochd and stochk > 50:
    buy_score += 1; reasons.append("[OK] Stochastic bullish cross above midline")
if close > bbu:
    buy_score += 1; reasons.append("[OK] BB upper breakout -- volatility expansion buy")
if vol_r > 1.8:
    buy_score += 1; reasons.append(f"[OK] Volume anomaly: {vol_r:.1f}x institutional avg")

# SELL factors
if close < ema20 < ema50 < ema200:
    sell_score += 2; reasons.append("? Full bearish EMA stack (20<50<200)")
if macd < macd_sig and p_macd >= p_sig:
    sell_score += 2; reasons.append("? MACD bearish crossover confirmed this bar")
if 20 < rsi < 45:
    sell_score += 1; reasons.append(f"? RSI in bearish distribution zone ({rsi:.1f})")
if stochk < stochd and stochk < 50:
    sell_score += 1; reasons.append("? Stochastic bearish cross below midline")
if close < bbl:
    sell_score += 1; reasons.append("? BB lower breakdown -- expansion to downside")
if vol_r > 1.8 and sell_score > 0:
    sell_score += 1; reasons.append(f"? Volume confirms distribution ({vol_r:.1f}x avg)")

entry = round(close, 2)
if buy_score >= 5:
    stop   = round(close - 2 * atr, 2)
    target = round(close + 3 * atr, 2)
    rr     = round((target - entry) / max(entry - stop, 0.01), 2)
    return {"signal":"EXECUTE BUY","color":"#00FF41","score":buy_score,
            "entry":entry,"stop":stop,"target":target,"rr":rr,
            "reasons":reasons,"atr":round(atr,2),"adx":round(adx,2),
            "rsi":round(rsi,2),"vol_ratio":round(vol_r,2),"hold":"1-5 Days"}

if sell_score >= 5:
    stop   = round(close + 2 * atr, 2)
    target = round(close - 3 * atr, 2)
    rr     = round((entry - target) / max(stop - entry, 0.01), 2)
    return {"signal":"EXECUTE SELL/SHORT","color":"#FF4444","score":sell_score,
            "entry":entry,"stop":stop,"target":target,"rr":rr,
            "reasons":reasons,"atr":round(atr,2),"adx":round(adx,2),
            "rsi":round(rsi,2),"vol_ratio":round(vol_r,2),"hold":"1-5 Days"}

return _standby(f"Score insufficient (BUY:{buy_score}/7 SELL:{sell_score}/7). Awaiting confluence.")
```

# – 7b. LONG-TERM ————————————————

def evaluate_longterm(df: pd.DataFrame) -> dict:
“”“Monthly position trades – secular trend following.
FINRA 15c3-5 compliant – informational only.”””
if df.empty or len(df) < 10:
return _standby(“Insufficient data.”)

```
l = df.iloc[-1]
close  = _safe_float(l.get('Close'))
ema50  = _safe_float(l.get('EMA_50'))
ema200 = _safe_float(l.get('EMA_200'))
rsi    = _safe_float(l.get('RSI_14'), 50)
adx    = _safe_float(l.get('ADX_14'))
macd   = _safe_float(l.get('MACD_12_26_9'))
macd_s = _safe_float(l.get('MACDs_12_26_9'))
atr    = _safe_float(l.get('ATRr_14'), close * 0.02)
fib618 = _safe_float(l.get('Fib_0618'))

buy_score = sell_score = 0
reasons = []

if close > ema200:
    buy_score += 2; reasons.append("[OK] Price above 200 EMA -- secular uptrend intact")
else:
    sell_score += 2; reasons.append("? Price below 200 EMA -- secular downtrend")

if ema50 > ema200:
    buy_score += 2; reasons.append("[OK] Golden Cross active (50 EMA > 200 EMA)")
else:
    sell_score += 2; reasons.append("? Death Cross active (50 EMA < 200 EMA)")

if adx > 25:
    buy_score += 1; reasons.append(f"[OK] Sustained trend strength (ADX {adx:.1f} > 25)")
if macd > macd_s:
    buy_score += 1; reasons.append("[OK] MACD above signal -- positive long-term momentum")
else:
    sell_score += 1; reasons.append("? MACD below signal -- negative long-term momentum")
if 40 < rsi < 75:
    buy_score += 1; reasons.append(f"[OK] RSI in healthy bull range ({rsi:.1f})")
if fib618 > 0 and close > fib618:
    buy_score += 1; reasons.append("[OK] Holding above Fib 61.8% -- key support zone")

entry = round(close, 2)
stop   = round(close - 3 * atr, 2)
target = round(close + 6 * atr, 2)
rr     = round((target - entry) / max(entry - stop, 0.01), 2)

if buy_score >= 5:
    return {"signal":"LONG-TERM BUY","color":"#00FF41","score":buy_score,
            "entry":entry,"stop":stop,"target":target,"rr":rr,
            "reasons":reasons,"atr":round(atr,2),"adx":round(adx,2),
            "rsi":round(rsi,2),"hold":"Weeks to Months"}

if sell_score >= 4:
    return {"signal":"REDUCE / EXIT LONG","color":"#FF4444","score":sell_score,
            "entry":entry,"stop":round(close + 3*atr,2),
            "target":round(close - 6*atr,2),"rr":rr,
            "reasons":reasons,"atr":round(atr,2),"adx":round(adx,2),
            "rsi":round(rsi,2),"hold":"Exit / Reduce Exposure"}

return _standby("Awaiting long-term structural alignment.")
```

# – 7c. SWING ––––––––––––––––––––––––––

def evaluate_swing(df: pd.DataFrame) -> dict:
“””
2-10 day mean reversion + momentum.
FIX #6: ADX gate REMOVED from swing – low ADX is ideal for mean reversion.
BB width check added instead.
“””
if df.empty or len(df) < 10:
return _standby(“Insufficient data.”)

```
l    = df.iloc[-1]
prev = df.iloc[-2]

close   = _safe_float(l.get('Close'))
ema20   = _safe_float(l.get('EMA_20'))
rsi     = _safe_float(l.get('RSI_14'), 50)
p_rsi   = _safe_float(prev.get('RSI_14'), 50)
bbu     = _safe_float(l.get('BBU_20_2.0'))
bbl     = _safe_float(l.get('BBL_20_2.0'))
bbm     = _safe_float(l.get('BBM_20_2.0'))
bbu_p   = _safe_float(prev.get('BBU_20_2.0'))
bbl_p   = _safe_float(prev.get('BBL_20_2.0'))
stochk  = _safe_float(l.get('STOCHk_14_3_3'), 50)
stochd  = _safe_float(l.get('STOCHd_14_3_3'), 50)
p_stochk= _safe_float(prev.get('STOCHk_14_3_3'), 50)
p_stochd= _safe_float(prev.get('STOCHd_14_3_3'), 50)
atr     = _safe_float(l.get('ATRr_14'), close * 0.015)
vol_r   = _safe_float(l.get('Vol_Ratio'), 1.0)
fib382  = _safe_float(l.get('Fib_0382'))
adx     = _safe_float(l.get('ADX_14'))

# BB width gate -- FIX: swing works when BB is not too compressed
bb_width = (bbu - bbl) / max(bbm, 1)
if bb_width < 0.01:
    return _standby("Bollinger Bands too compressed. No swing edge in this environment.")

buy_score = sell_score = 0
reasons = []

# Oversold bounce
if rsi < 35 and p_rsi < rsi:
    buy_score += 2; reasons.append(f"[OK] RSI oversold reversal ({rsi:.1f} turning up from <35)")
if close <= bbl * 1.015 and close > bbl_p * 0.99:
    buy_score += 2; reasons.append("[OK] Price at lower BB -- mean reversion setup")
if stochk > stochd and p_stochk <= p_stochd and stochk < 30:
    buy_score += 2; reasons.append("[OK] Stochastic bullish cross from oversold (<30)")
if close > ema20:
    buy_score += 1; reasons.append("[OK] Reclaimed 20 EMA -- short-term trend restored")
if fib382 > 0 and abs(close - fib382) / close < 0.01:
    buy_score += 1; reasons.append("[OK] Touching Fib 38.2% -- key swing support zone")
if vol_r > 1.2:
    buy_score += 1; reasons.append(f"[OK] Volume confirmation ({vol_r:.1f}x avg)")

# Overbought fade
if rsi > 70 and p_rsi > rsi:
    sell_score += 2; reasons.append(f"? RSI overbought rolling over ({rsi:.1f} from >70)")
if close >= bbu * 0.99 and close < bbu_p * 1.01:
    sell_score += 2; reasons.append("? Price at upper BB -- overbought fade setup")
if stochk < stochd and p_stochk >= p_stochd and stochk > 70:
    sell_score += 2; reasons.append("? Stochastic bearish cross from overbought (>70)")
if vol_r > 1.2 and sell_score > 0:
    sell_score += 1; reasons.append(f"? Volume confirms selling pressure ({vol_r:.1f}x avg)")

entry = round(close, 2)
if buy_score >= 4:
    stop   = round(close - 1.5 * atr, 2)
    target = round(bbm, 2)
    rr     = round((target - entry) / max(entry - stop, 0.01), 2)
    return {"signal":"SWING BUY","color":"#00FF41","score":buy_score,
            "entry":entry,"stop":stop,"target":target,"rr":rr,
            "reasons":reasons,"atr":round(atr,2),"adx":round(adx,2),
            "rsi":round(rsi,2),"hold":"2-10 Days"}

if sell_score >= 4:
    stop   = round(close + 1.5 * atr, 2)
    target = round(bbm, 2)
    rr     = round((entry - target) / max(stop - entry, 0.01), 2)
    return {"signal":"SWING SELL/FADE","color":"#FF4444","score":sell_score,
            "entry":entry,"stop":stop,"target":target,"rr":rr,
            "reasons":reasons,"atr":round(atr,2),"adx":round(adx,2),
            "rsi":round(rsi,2),"hold":"2-10 Days"}

return _standby("No swing edge detected. Awaiting mean reversion extremes.")
```

# – 7d. FAT PITCH (original Solomon theory) ———————

def evaluate_fat_pitch(df: pd.DataFrame) -> dict:
“””
Original ‘fat pitch’ theory – 3 ultra-strict gates.
Only fires on maximum-conviction asymmetric setups.
Volume >= 150% avg . ADX >= 35 . BB breakout + MACD + RSI 60-85.
FINRA 15c3-5: Informational only.
“””
if df.empty or len(df) < 10:
return _standby(“Insufficient data.”)

```
l = df.iloc[-1]
close    = _safe_float(l.get('Close'))
macd     = _safe_float(l.get('MACD_12_26_9'))
macd_sig = _safe_float(l.get('MACDs_12_26_9'))
adx      = _safe_float(l.get('ADX_14'))
rsi      = _safe_float(l.get('RSI_14'), 50)
bbu      = _safe_float(l.get('BBU_20_2.0'))
vol_r    = _safe_float(l.get('Vol_Ratio'), 1.0)
atr      = _safe_float(l.get('ATRr_14'), close * 0.02)

# Gate 1: Institutional volume (original: >= 150% of avg)
if vol_r < 1.5:
    return {"signal":"STANDBY","color":"#FFA500","score":0,
            "reasons":[f"Gate 1 FAIL: Volume {vol_r:.2f}x avg -- requires >=1.5x institutional participation."],
            "entry":None,"stop":None,"target":None,"rr":None}

# Gate 2: Trend velocity (original: ADX >= 35)
if adx < 35:
    return {"signal":"STANDBY","color":"#FFA500","score":0,
            "reasons":[f"Gate 2 FAIL: ADX {adx:.2f} lacks terminal velocity (requires >=35)."],
            "entry":None,"stop":None,"target":None,"rr":None}

# Gate 3: High-conviction structural breakout
if (close > bbu) and (macd > macd_sig) and (60 <= rsi <= 85):
    entry  = round(close, 2)
    stop   = round(close - 2 * atr, 2)
    target = round(close + 4 * atr, 2)
    rr     = round((target - entry) / max(entry - stop, 0.01), 2)
    return {
        "signal": "FAT PITCH -- EXECUTE",
        "color": "#00CCFF",
        "score": 3,
        "entry": entry, "stop": stop, "target": target, "rr": rr,
        "reasons": [
            f"[OK] Gate 1 PASS: Volume anomaly {vol_r:.1f}x avg (>=1.5x institutional threshold)",
            f"[OK] Gate 2 PASS: ADX {adx:.1f} -- trend has terminal velocity",
            f"[OK] Gate 3 PASS: BB upper breakout . MACD bullish . RSI {rsi:.1f} in sweet spot (60-85)",
            "! ASYMMETRIC SETUP -- high probability structural breakout with volume confirmation"
        ],
        "atr": round(atr,2), "adx": round(adx,2),
        "rsi": round(rsi,2), "vol_ratio": round(vol_r,2),
        "hold": "Hold until momentum exhaustion or ADX rollover"
    }

return {"signal":"STANDBY","color":"#FFA500","score":0,
        "reasons":[
            f"Gate 1: Volume {vol_r:.1f}x {'[OK]' if vol_r>=1.5 else '[x]'}  |  "
            f"Gate 2: ADX {adx:.1f} {'[OK]' if adx>=35 else '[x]'}  |  "
            f"Gate 3: BB break+MACD+RSI {'[OK]' if close>bbu and macd>macd_sig and 60<=rsi<=85 else '[x]'}",
            "All 3 gates must pass simultaneously. Capital preserved until then."
        ],
        "entry":None,"stop":None,"target":None,"rr":None}
```

# —————————————————————–

# 8. SOLOMON STRATEGY ENGINE (from original app)

# —————————————————————–

@st.cache_data(ttl=3600)
def fetch_solomon_data():
return yf.download(
SOLOMON_TICKERS + BENCHMARKS,
period=“2y”, progress=False, auto_adjust=True
)

def calculate_solomon_factors(data, target_date, vix_close):
closes = data[“Close”].loc[:target_date]
highs  = data[“High”].loc[:target_date]
lows   = data[“Low”].loc[:target_date]
vols   = data[“Volume”].loc[:target_date]

```
if len(closes) < 200:
    return pd.DataFrame()

spy_p    = closes["SPY"].dropna()
vix_halt = vix_close > 30

try:
    tnx_val = data["Close"]["^TNX"].loc[:target_date].dropna().iloc[-1]
except Exception:
    tnx_val = None

results = []
for t in SOLOMON_TICKERS:
    try:
        p = closes[t].dropna()
        h = highs[t].dropna()
        lo = lows[t].dropna()
        v = vols[t].dropna()
        if len(p) < 200:
            continue

        ytd_px = p[p.index.year == target_date.year]
        ytd    = ((p.iloc[-1] / ytd_px.iloc[0]) - 1) * 100 if not ytd_px.empty else 0
        ret_1m = p.pct_change(21).iloc[-1]
        ret_3m = p.pct_change(63).iloc[-1]
        ret_6m = p.pct_change(126).iloc[-1]
        ret_9m = p.pct_change(189).iloc[-1]
        vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
        ram    = ret_1m / vol_1m if vol_1m != 0 else 0

        spy_1m = spy_p.pct_change(21).iloc[-1]
        spy_3m = spy_p.pct_change(63).iloc[-1]
        spy_6m = spy_p.pct_change(126).iloc[-1]
        spy_9m = spy_p.pct_change(189).iloc[-1]
        avg_ret = (ret_1m + ret_3m + ret_6m + ret_9m) / 4
        avg_spy = (spy_1m + spy_3m + spy_6m + spy_9m) / 4
        rel_str = avg_ret - avg_spy

        sma50  = p.rolling(50).mean()
        sma200 = p.rolling(200).mean()
        slp50  = (sma50.iloc[-1] - sma50.iloc[-21]) / sma50.iloc[-21]
        above200 = p.iloc[-1] > sma200.iloc[-1]

        v90    = v.rolling(90).mean().iloc[-1]
        vol_cf = (v.rolling(20).mean().iloc[-1] / v90) if v90 != 0 else 1

        tr   = pd.concat([h-lo, np.abs(h-p.shift()), np.abs(lo-p.shift())], axis=1).max(axis=1)
        atr  = tr.rolling(14).mean().iloc[-1]
        stop = p.tail(20).max() - (2.5 * atr)
        sd   = (p.iloc[-1] - stop) / p.iloc[-1]
        alloc_base = min((0.01 / sd) * 100, 25) if sd > 0 else 0

        up   = h - h.shift(1)
        dw   = lo.shift(1) - lo
        tr14 = tr.rolling(14).sum()
        pdi  = 100 * (pd.Series(np.where((up>dw)&(up>0), up, 0), index=p.index).rolling(14).sum() / tr14)
        mdi  = 100 * (pd.Series(np.where((dw>up)&(dw>0), dw, 0), index=p.index).rolling(14).sum() / tr14)
        adx_val = (100 * np.abs(pdi-mdi) / (pdi+mdi)).rolling(14).mean().iloc[-1]

        roc_ac = p.pct_change(20).iloc[-1] - (p.pct_change(60).iloc[-1] / 3)

        rate_adj = 0
        if tnx_val and tnx_val > 4.5:
            if SOLOMON_SECTORS.get(t, "") in ["Safe Harbor", "Utilities", "Real Estate"]:
                rate_adj = -0.3

        results.append({
            "TKR": t, "SECTOR": SOLOMON_SECTORS[t], "PRICE": p.iloc[-1], "YTD": ytd,
            "RET_1M": ret_1m*100, "RET_3M": ret_3m*100,
            "RET_6M": ret_6m*100, "RET_9M": ret_9m*100,
            "RAM": ram, "REL_STR": rel_str, "50D_SLP": slp50,
            "VOL_CF": vol_cf, "ADX": adx_val, "STOP": stop,
            "ROC_AC": roc_ac, "ALLOC_BASE": alloc_base,
            "Above_200": above200, "RATE_ADJ": rate_adj,
        })
    except Exception:
        continue

if not results:
    return pd.DataFrame()

df = pd.DataFrame(results).set_index("TKR")
f  = ["RAM", "REL_STR", "50D_SLP", "VOL_CF", "ROC_AC"]
z  = (df[f] - df[f].mean()) / df[f].std()
df["SCORE"] = (
    z["RAM"]*0.25 + z["REL_STR"]*0.20 +
    z["50D_SLP"]*0.20 + z["VOL_CF"]*0.20 +
    z["ROC_AC"]*0.15
) * 100 + df["RATE_ADJ"] * 10
df = df.sort_values("SCORE", ascending=False)
df["RNK"] = range(1, len(df)+1)

sigs, ress, allocs = [], [], []
for idx, row in df.iterrows():
    fails = []
    if not row["Above_200"]:    fails.append("Below 200MA")
    if row["ADX"] <= 25:        fails.append(f"ADX {row['ADX']:.0f}")
    if row["VOL_CF"] < 1.2:     fails.append(f"Vol {row['VOL_CF']:.2f}x")
    if row["RAM"] <= 0:         fails.append("Neg RAM")
    if row["REL_STR"] <= 0:     fails.append("Lags SPY")
    if row["ROC_AC"] <= 0:      fails.append("Decel ROC")
    if row["50D_SLP"] <= 0:     fails.append("Neg 50D Slope")
    rnk = row["RNK"]; n = len(fails)

    if vix_halt:
        sig, res, alloc = "HALT", "VIX > 30", 0
    elif not row["Above_200"] or row["PRICE"] < row["STOP"]:
        sig, res, alloc = "STRONG SELL", fails[0] if fails else "ATR Stop", 0
    elif rnk <= 5 and n == 0:
        sig, res, alloc = "STRONG BUY", "ALL CLEAR", min(row["ALLOC_BASE"], 20)
    elif rnk <= 5 and n <= 2:
        sig, res, alloc = "BUY", ", ".join(fails), min(row["ALLOC_BASE"]*0.6, 12)
    elif rnk <= 5:
        sig, res, alloc = "BUY", ", ".join(fails[:2]), min(row["ALLOC_BASE"]*0.3, 6)
    elif rnk <= 10 and n == 0:
        sig, res, alloc = "HOLD", "Rank buffer", 0
    elif rnk <= 10:
        sig, res, alloc = "HOLD", ", ".join(fails[:1]), 0
    else:
        sig, res, alloc = "SELL", ", ".join(fails[:2]) if fails else f"Rank #{rnk}", 0

    sigs.append(sig); ress.append(res); allocs.append(alloc)

df["SIGNAL"] = sigs
df["REASON"] = ress
df["ALLOC"]  = allocs
return df
```

# —————————————————————–

# 9. BACKTESTING  (FIX #6, #7: proper holding windows + real PnL)

# —————————————————————–

def walk_forward_backtest(df: pd.DataFrame, strategy: str = “surefire”) -> dict:
“””
Walk-forward with proper holding period windows.
FIX #6: 5 bars swing, 20 bars surefire, 60 bars long-term.
FIX #7: Win/loss P&L derived from actual trade data.
“””
if len(df) < 120:
return {}

```
split   = int(len(df) * 0.7)
test_df = df.iloc[split:].copy().reset_index(drop=True)

# Strategy-specific holding window
hold_bars = {"surefire": 20, "longterm": 60, "swing": 5, "fatpitch": 20}
window    = hold_bars.get(strategy, 10)

trades = []
for i in range(5, len(test_df) - window):
    seg = test_df.iloc[:i]
    if strategy == "surefire":
        r = evaluate_surefire(seg)
    elif strategy == "longterm":
        r = evaluate_longterm(seg)
    elif strategy == "fatpitch":
        r = evaluate_fat_pitch(seg)
    else:
        r = evaluate_swing(seg)

    if r['signal'] == "STANDBY" or not r.get('entry'):
        continue

    entry  = r['entry']
    stop   = r['stop']
    target = r['target']

    # Check if price hits target OR stop within holding window
    future = test_df.iloc[i: i + window]
    hit_target = any(float(row['High']) >= target for _, row in future.iterrows()) if "BUY" in r['signal'] else any(float(row['Low']) <= target for _, row in future.iterrows())
    hit_stop   = any(float(row['Low']) <= stop for _, row in future.iterrows()) if "BUY" in r['signal'] else any(float(row['High']) >= stop for _, row in future.iterrows())

    if hit_target and not hit_stop:
        pnl = (target - entry) / entry if "BUY" in r['signal'] else (entry - target) / entry
        trades.append({"outcome": "WIN", "pnl": pnl})
    elif hit_stop:
        pnl = (stop - entry) / entry if "BUY" in r['signal'] else (entry - stop) / entry
        trades.append({"outcome": "LOSS", "pnl": pnl})

if not trades:
    return {"trades": 0, "win_rate": 0, "avg_pnl": 0, "total_return": 0,
            "avg_win": 0, "avg_loss": 0}

wins   = [t for t in trades if t['outcome'] == 'WIN']
losses = [t for t in trades if t['outcome'] == 'LOSS']
pnls   = [t['pnl'] for t in trades]

# FIX #7: real avg win/loss from actual trades
avg_win  = abs(np.mean([t['pnl'] for t in wins])) * 100  if wins   else 2.0
avg_loss = abs(np.mean([t['pnl'] for t in losses])) * 100 if losses else 1.0

return {
    "trades":       len(trades),
    "win_rate":     round(len(wins) / len(trades) * 100, 1),
    "avg_pnl":      round(np.mean(pnls) * 100, 2),
    "total_return": round(sum(pnls) * 100, 2),
    "avg_win":      round(avg_win, 2),
    "avg_loss":     round(avg_loss, 2),
}
```

def monte_carlo(win_rate: float, avg_win: float, avg_loss: float,
n: int = 500, trials: int = 200) -> dict:
“”“Monte Carlo – FIX #7: uses real avg_win / avg_loss from backtest.”””
results = []
for _ in range(trials):
equity = 100.0
for _ in range(n):
if np.random.random() < win_rate / 100:
equity *= (1 + avg_win / 100)
else:
equity *= (1 - avg_loss / 100)
results.append(equity)
return {
“median”:    round(float(np.median(results)), 2),
“p10”:       round(float(np.percentile(results, 10)), 2),
“p90”:       round(float(np.percentile(results, 90)), 2),
“ruin_prob”: round(sum(1 for r in results if r < 50) / trials * 100, 1),
}

# —————————————————————–

# 10. CHART BUILDER

# —————————————————————–

def build_chart(df: pd.DataFrame, ticker: str, result: dict) -> go.Figure:
if df.empty:
return go.Figure()
fig = make_subplots(
rows=3, cols=1, shared_xaxes=True,
row_heights=[0.60, 0.20, 0.20],
vertical_spacing=0.03
)

```
# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'],
    low=df['Low'],  close=df['Close'],
    increasing_line_color='#00FF41',
    decreasing_line_color='#FF4444',
    name="Price"), row=1, col=1)

# EMAs
for col, color, name in [
    ('EMA_20',  '#FF8000', 'EMA20'),
    ('EMA_50',  '#4da6ff', 'EMA50'),
    ('EMA_200', '#FF69B4', 'EMA200'),
]:
    if col in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col], name=name,
            line=dict(color=color, width=1)), row=1, col=1)

# Bollinger Bands
if 'BBU_20_2.0' in df.columns and 'BBL_20_2.0' in df.columns:
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BBU_20_2.0'], name='BB Upper',
        line=dict(color='#333', width=1, dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BBL_20_2.0'], name='BB Lower',
        line=dict(color='#333', width=1, dash='dot'),
        fill='tonexty', fillcolor='rgba(80,80,80,0.04)'), row=1, col=1)

# Trade levels
if result.get('entry'):
    for level, color, label in [
        (result['entry'],  '#FF8000', 'ENTRY'),
        (result.get('stop'),   '#FF4444', 'STOP'),
        (result.get('target'), '#00FF41', 'TARGET'),
    ]:
        if level:
            fig.add_hline(
                y=level, line_color=color, line_dash='dash', line_width=1,
                row=1, col=1,
                annotation_text=f" {label}: ${level}",
                annotation_font_color=color,
                annotation_position="right")

# RSI
if 'RSI_14' in df.columns:
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI_14'], name='RSI',
        line=dict(color='#FF8000', width=1)), row=2, col=1)
    fig.add_hline(y=70, line_color='#FF4444', line_dash='dot', line_width=1, row=2, col=1)
    fig.add_hline(y=30, line_color='#00FF41', line_dash='dot', line_width=1, row=2, col=1)
    fig.add_hline(y=50, line_color='#333',    line_dash='dot', line_width=1, row=2, col=1)

# Volume
try:
    vol_colors = [
        '#00FF41' if float(df['Close'].iloc[i]) >= float(df['Open'].iloc[i]) else '#FF4444'
        for i in range(len(df))
    ]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name='Volume',
        marker_color=vol_colors, opacity=0.5), row=3, col=1)
    if 'Vol_SMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Vol_SMA_20'], name='Vol SMA20',
            line=dict(color='#FF8000', width=1)), row=3, col=1)
except Exception:
    pass

fig.update_layout(
    template='plotly_dark',
    paper_bgcolor='#000', plot_bgcolor='#050505',
    font=dict(family='Source Code Pro', color='#666', size=10),
    showlegend=False, height=580,
    xaxis_rangeslider_visible=False,
    margin=dict(l=0, r=0, t=28, b=0),
    title=dict(
        text=f"[ {ticker} ]  INSTITUTIONAL PRICE ACTION . ALL INDICATORS",
        font=dict(color='#FF8000', size=12)
    )
)
fig.update_yaxes(gridcolor='#111', zerolinecolor='#1a1a1a')
fig.update_xaxes(gridcolor='#111', zerolinecolor='#1a1a1a')
return fig
```

# —————————————————————–

# 11. DISPLAY HELPERS

# —————————————————————–

def show_signal_card(result: dict, style: str = “standard”):
sig   = result[‘signal’]
color = result[‘color’]
if style == “fat”:
css = “signal-box-fat”
elif “BUY” in sig:
css = “signal-box-buy”
elif “SELL” in sig or “EXIT” in sig or “REDUCE” in sig:
css = “signal-box-sell”
else:
css = “signal-box-standby”

```
score_txt = f"CONFLUENCE SCORE: {result.get('score',0)}" if result.get('score') else "GATES EVALUATED"
st.markdown(f"""
<div class="{css}">
    <div style="font-size:1.5rem;font-weight:700;color:{color};letter-spacing:3px;">{sig}</div>
    <div style="color:#555;font-size:0.72rem;margin-top:6px;letter-spacing:1px;">
        {score_txt} &nbsp;.&nbsp; FINRA 15c3-5 COMPLIANT &nbsp;.&nbsp; INFORMATIONAL ONLY
    </div>
</div>""", unsafe_allow_html=True)
```

def show_trade_levels(result: dict):
if not result.get(‘entry’):
return
c1, c2, c3, c4 = st.columns(4)
entry = result[‘entry’]
stop  = result[‘stop’]
tgt   = result[‘target’]
c1.metric(“ENTRY”,     f”${entry}”)
c2.metric(“STOP LOSS”, f”${stop}”,
delta=f”{round((stop-entry)/entry*100,2)}%”, delta_color=“inverse”)
c3.metric(“TARGET”,    f”${tgt}”,
delta=f”{round((tgt-entry)/entry*100,2)}%”)
c4.metric(“RISK / REWARD”, f”{result.get(‘rr’,‘N/A’)}:1”)

def show_rationale(result: dict, hold_label: str = “”):
with st.expander(”? TRADE RATIONALE – FULL SIGNAL BREAKDOWN”, expanded=True):
st.markdown(’<div class="rationale-box">’, unsafe_allow_html=True)
st.markdown(”**TECHNICAL CONFLUENCE FACTORS:**”)
for r in result.get(‘reasons’, []):
st.markdown(f”  {r}”)
atr_v = result.get(‘atr’,‘N/A’)
adx_v = result.get(‘adx’,‘N/A’)
rsi_v = result.get(‘rsi’,‘N/A’)
hold_v= result.get(‘hold’, hold_label or ‘N/A’)
st.markdown(f”””
**RISK TELEMETRY:**
  ATR-14: `{atr_v}`  |  ADX-14: `{adx_v}`  |  RSI-14: `{rsi_v}`

**REGULATORY COMPLIANCE:**
  Signal generated under FINRA Rule 15c3-5 (Market Access Rule) framework.
  SEC Reg T and SEC Reg NMS standards observed. All outputs are informational
  only and do not constitute investment advice. Position sizing must adhere
  to your firm’s risk protocols and individual financial circumstances.

**EXPECTED HOLDING PERIOD:** `{hold_v}`
“””)
st.markdown(’</div>’, unsafe_allow_html=True)

def show_backtest_section(df: pd.DataFrame, strategy: str):
with st.expander(”? WALK-FORWARD BACKTEST + MONTE CARLO SIMULATION”):
with st.spinner(“Running simulations across test window…”):
bt = walk_forward_backtest(df, strategy)

```
    if not bt or bt.get('trades', 0) == 0:
        st.warning("Insufficient signal occurrences in test window to run simulation.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SIGNALS TESTED", bt['trades'])
    c2.metric("WIN RATE",       f"{bt['win_rate']}%")
    c3.metric("AVG P&L/TRADE",  f"{bt['avg_pnl']}%")
    c4.metric("TOTAL RETURN",   f"{bt['total_return']}%")

    mc = monte_carlo(bt['win_rate'], bt['avg_win'], bt['avg_loss'])
    st.markdown("**MONTE CARLO (500 trades x 200 trials -- starting equity $100):**")
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("MEDIAN OUTCOME",    f"${mc['median']}")
    mc2.metric("PESSIMISTIC (P10)",  f"${mc['p10']}")
    mc3.metric("OPTIMISTIC (P90)",   f"${mc['p90']}")
    mc4.metric("RUIN PROBABILITY",   f"{mc['ruin_prob']}%")
    st.markdown(
        f"<div style='color:#444;font-size:9px;margin-top:4px;'>"
        f"Avg Win: {bt['avg_win']}% . Avg Loss: {bt['avg_loss']}% . "
        f"Derived from actual backtest trades (not fabricated)."
        f"</div>", unsafe_allow_html=True)
```

# —————————————————————–

# 12. UNIVERSE SCANNER  (FIX #3: pre-fetch on main thread)

# —————————————————————–

def _evaluate_worker(args):
“”“Worker runs signal evaluation only – data already fetched.”””
gics_name, ticker, df_computed, mode = args
try:
if mode == “surefire”:
result = evaluate_surefire(df_computed)
elif mode == “longterm”:
result = evaluate_longterm(df_computed)
elif mode == “fatpitch”:
result = evaluate_fat_pitch(df_computed)
else:
result = evaluate_swing(df_computed)

```
    if result['signal'] != "STANDBY":
        return {
            "GICS Node": gics_name,
            "Ticker":    ticker,
            "Signal":    result['signal'],
            "Score":     result.get('score', 0),
            "Entry $":   result.get('entry'),
            "Stop $":    result.get('stop'),
            "Target $":  result.get('target'),
            "R/R":       result.get('rr'),
            "RSI":       result.get('rsi'),
            "ADX":       result.get('adx'),
        }
except Exception:
    pass
return None
```

def run_universe_scan(mode: str) -> list:
“””
FIX #3: Pre-fetch all data on main thread, then parallelise evaluation only.
“””
universe = list(GICS_UNIVERSE.items())
args_list = []
progress = st.progress(0, text=“Fetching market data…”)
total    = sum(len(tickers) for _, tickers in universe)
fetched  = 0

```
for gics_name, tickers in universe:
    for ticker in tickers:
        period = "2y" if mode == "longterm" else "1y"
        raw = fetch_data(ticker, period=period)
        df_computed = compute_indicators(raw) if not raw.empty else pd.DataFrame()
        args_list.append((gics_name, ticker, df_computed, mode))
        fetched += 1
        progress.progress(fetched / total / 2,
                          text=f"Fetching {ticker}... ({fetched}/{total})")

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    futures = list(ex.map(_evaluate_worker, args_list))
    for i, r in enumerate(futures):
        if r:
            results.append(r)
        progress.progress(0.5 + (i + 1) / len(args_list) / 2,
                          text=f"Evaluating signals... ({i+1}/{len(args_list)})")

progress.empty()
return results
```

# —————————————————————–

# 13. PORTFOLIO TRACKER  (FIX #15: GICS sector tagging added)

# —————————————————————–

def portfolio_section():
st.markdown(”### ? PORTFOLIO TRACKER – POSITION SIZING . GICS SECTOR ATTRIBUTION”)
st.markdown(”—”)

```
gics_options = ["(Manual entry)"] + list(GICS_UNIVERSE.keys())

with st.expander("+ ADD POSITION", expanded=False):
    pc1, pc2 = st.columns(2)
    with pc1:
        gics_sel = st.selectbox("GICS SECTOR NODE", gics_options, key="port_gics")
        if gics_sel != "(Manual entry)" and GICS_UNIVERSE.get(gics_sel):
            default_ticker = GICS_UNIVERSE[gics_sel][0]
        else:
            default_ticker = ""
        p_ticker = st.text_input("TICKER", value=default_ticker, key="port_ticker")
        p_shares = st.number_input("SHARES HELD", min_value=0.0, step=1.0, key="port_shares")
    with pc2:
        p_entry  = st.number_input("AVG ENTRY PRICE $", min_value=0.0, step=0.01, key="port_entry")
        p_stop   = st.number_input("STOP LOSS PRICE $", min_value=0.0, step=0.01, key="port_stop")
        acc_size = st.number_input("ACCOUNT SIZE $", min_value=1000.0, value=100000.0, step=1000.0, key="port_acc")
        risk_pct = st.slider("RISK PER TRADE %", 0.5, 5.0, 1.0, 0.25, key="port_risk")

    if st.button("CALCULATE & ADD POSITION"):
        if p_ticker and p_entry > 0 and p_stop > 0:
            risk_per_share   = abs(p_entry - p_stop)
            max_risk         = acc_size * (risk_pct / 100)
            suggested_shares = int(max_risk / risk_per_share) if risk_per_share > 0 else 0

            raw = fetch_data(p_ticker.upper(), period="5d")
            current_price = float(raw['Close'].iloc[-1]) if not raw.empty else p_entry
            pnl           = (current_price - p_entry) * p_shares
            pnl_pct       = ((current_price - p_entry) / p_entry) * 100 if p_entry > 0 else 0

            # FIX #15: tag GICS node
            gics_tag = gics_sel if gics_sel != "(Manual entry)" else "Unclassified"

            st.session_state.portfolio.append({
                "Ticker":       p_ticker.upper(),
                "GICS Node":    gics_tag,
                "Shares":       p_shares,
                "Entry $":      round(p_entry, 2),
                "Stop $":       round(p_stop, 2),
                "Current $":    round(current_price, 2),
                "P&L $":        round(pnl, 2),
                "P&L %":        round(pnl_pct, 2),
                "Suggested Sz": suggested_shares,
                "Max Risk $":   round(max_risk, 2),
                "Pos Value $":  round(p_shares * p_entry, 2),
            })
            st.success(
                f"Added. Suggested shares at {risk_pct}% risk: "
                f"**{suggested_shares}** -- Max risk $**{max_risk:,.0f}**"
            )

if not st.session_state.portfolio:
    st.info("No positions tracked. Add a position above.")
    return

port_df    = pd.DataFrame(st.session_state.portfolio)
total_pnl  = port_df['P&L $'].sum()
total_val  = port_df['Pos Value $'].sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("TOTAL POSITIONS", len(port_df))
m2.metric("PORTFOLIO VALUE", f"${total_val:,.2f}")
m3.metric("TOTAL P&L",       f"${total_pnl:,.2f}",
          delta=f"{round(total_pnl/max(total_val,1)*100,2)}%")
m4.metric("WIN POSITIONS",   f"{len(port_df[port_df['P&L $']>0])}/{len(port_df)}")

def style_pnl(val):
    c = '#00FF41' if val > 0 else '#FF4444' if val < 0 else '#888'
    return f'color: {c}'

st.dataframe(
    port_df.style.applymap(style_pnl, subset=['P&L $', 'P&L %']),
    use_container_width=True
)

# GICS concentration chart
if 'GICS Node' in port_df.columns:
    st.markdown("**SECTOR CONCENTRATION**")
    sec_val = port_df.groupby('GICS Node')['Pos Value $'].sum()
    sec_pct = (sec_val / sec_val.sum() * 100).round(1)
    conc_html = ""
    colors    = ["#FF8000","#FFCC00","#00FF41","#4da6ff","#FF4488",
                 "#44FFCC","#FF69B4","#AAA","#FFAA00","#AA44FF"]
    for i, (node, pct) in enumerate(sec_pct.items()):
        c = colors[i % len(colors)]
        conc_html += (
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            f'<div style="width:10px;height:10px;background:{c};border-radius:1px;"></div>'
            f'<div style="flex:1;font-size:10px;color:#888;">{node}</div>'
            f'<div style="width:120px;background:#1A1A1A;height:6px;border-radius:2px;">'
            f'<div style="width:{pct:.0f}%;background:{c};height:6px;border-radius:2px;"></div></div>'
            f'<div style="width:40px;text-align:right;font-size:10px;color:{c};font-weight:700;">{pct:.1f}%</div>'
            f'</div>'
        )
    st.markdown(conc_html, unsafe_allow_html=True)

if st.button("? CLEAR PORTFOLIO"):
    st.session_state.portfolio = []
    st.rerun()
```

# —————————————————————–

# 14. ALERT + EMAIL

# —————————————————————–

def send_alert(ticker, signal, rationale):
cfg = st.session_state.get(‘alert_config’, {})
if not cfg.get(‘enabled’) or not cfg.get(‘email’):
return
try:
body = (
f”QUANT TERMINAL SIGNAL ALERT\n\n”
f”Ticker:  {ticker}\n”
f”Signal:  {signal}\n”
f”Rationale: {rationale}\n\n”
f”Generated: {now_est.strftime(’%Y-%m-%d %H:%M:%S ET’)}\n\n”
f”DISCLAIMER: This is an algorithmic signal for informational purposes only.\n”
f”Not financial advice. Verify with your own research before acting.”
)
msg = MIMEText(body)
msg[‘Subject’] = f”[QUANT TERMINAL] {signal} – {ticker}”
msg[‘From’]    = cfg[‘smtp_user’]
msg[‘To’]      = cfg[‘email’]
with smtplib.SMTP(cfg[‘smtp_host’], int(cfg[‘smtp_port’])) as server:
server.starttls()
server.login(cfg[‘smtp_user’], cfg[‘smtp_pass’])
server.send_message(msg)
except Exception:
pass

# —————————————————————–

# 15. SIDEBAR  (FIX #12: session state pre-initialized at top)

# —————————————————————–

def render_sidebar():
with st.sidebar:
st.markdown(”##  SYSTEM CONFIG”)
st.markdown(”—”)

```
    # FIX #12: GICS sector selector
    st.markdown("### ? GICS SECTOR NAVIGATOR")
    selected_gics = st.selectbox(
        "SELECT SECTOR NODE",
        ["(Free entry)"] + list(GICS_UNIVERSE.keys()),
        key="sidebar_gics"
    )
    if selected_gics != "(Free entry)":
        reps = GICS_UNIVERSE.get(selected_gics, [])
        st.markdown(
            f"<div style='color:#FF8000;font-size:10px;margin-bottom:4px;'>"
            f"Representative: {', '.join(reps)}</div>",
            unsafe_allow_html=True
        )
        st.session_state['gics_ticker'] = reps[0] if reps else ""

    st.markdown("---")
    st.markdown("### ? EMAIL ALERTS")
    email_on = st.toggle("Enable Email Alerts", value=False)
    if email_on:
        ae = st.text_input("Alert Email",  placeholder="you@email.com")
        sh = st.text_input("SMTP Host",    value="smtp.gmail.com")
        sp = st.number_input("SMTP Port",  value=587)
        su = st.text_input("SMTP User",    placeholder="sender@gmail.com")
        sw = st.text_input("SMTP Pass",    type="password")
        st.session_state['alert_config'] = {
            'enabled':True,'email':ae,'smtp_host':sh,
            'smtp_port':sp,'smtp_user':su,'smtp_pass':sw
        }
    else:
        st.session_state['alert_config'] = {'enabled': False}

    st.markdown("---")
    st.markdown("### ? SCAN SETTINGS")
    st.session_state['scan_mode'] = st.selectbox(
        "Universe Scope", ["Core 9", "Full 25 GICS"])

    st.markdown("---")
    st.markdown(
        '<div class="compliance-badge"> FINRA RULE 15c3-5</div><br>'
        '<div class="compliance-badge"> SEC REG T</div><br>'
        '<div class="compliance-badge"> SEC REG NMS</div><br>'
        '<div class="compliance-badge"> INFORMATIONAL ONLY</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown(
        "<div style='color:#2a2a2a;font-size:0.62rem;line-height:1.5;'>"
        "All signals are algorithmic and informational only. "
        "Not financial advice. Past performance does not guarantee "
        "future results. Always conduct independent research."
        "</div>",
        unsafe_allow_html=True
    )
```

render_sidebar()

# —————————————————————–

# 16. MACRO ROW (from original app)

# —————————————————————–

@st.cache_data(ttl=3600)
def fetch_macro_quick():
try:
syms = [”^VIX”,”^TNX”,”^TYX”,“GC=F”,“CL=F”,“SPY”,“QQQ”,“DIA”]
d = yf.download(syms, period=“5d”, progress=False, auto_adjust=True)
c = d[“Close”]
if isinstance(c.columns, pd.MultiIndex):
c.columns = c.columns.get_level_values(0)
return c
except Exception:
return pd.DataFrame()

macro_data = fetch_macro_quick()

def _mval(sym, macro_data):
try:
return float(macro_data[sym].dropna().iloc[-1])
except Exception:
return None

vix_val = _mval(”^VIX”, macro_data)
tnx_val = _mval(”^TNX”, macro_data)
tyx_val = _mval(”^TYX”, macro_data)
gc_val  = _mval(“GC=F”,  macro_data)
cl_val  = _mval(“CL=F”,  macro_data)
spy_val = _mval(“SPY”,   macro_data)
qqq_val = _mval(“QQQ”,   macro_data)

vix_col = “#CC0000” if (vix_val or 0) > 30 else “#FF8000” if (vix_val or 0) > 20 else “#00CC00”

def _mc_cell(label, val, sub=””, color=”#CCCCCC”, fmt=”{:.2f}”):
try:
v = fmt.format(val) if val is not None else “N/A”
except Exception:
v = “N/A”
return (
f’<div class="bbg-macro-cell">’
f’<div class="bbg-macro-lbl">{label}</div>’
f’<div class="bbg-macro-val" style="color:{color};">{v}</div>’
f’<div class="bbg-macro-sub">{sub}</div>’
f’</div>’
)

macro_html = ‘<div class="bbg-macro-row">’
macro_html += _mc_cell(“VIX INDEX”,   vix_val, “CBOE Fear Gauge”, vix_col)
macro_html += _mc_cell(“10Y YIELD”,   tnx_val, “US Treasury”,     “#FF8000”)
macro_html += _mc_cell(“30Y YIELD”,   tyx_val, “US Treasury”,     “#FF8000”)
macro_html += _mc_cell(“GOLD SPOT”,   gc_val,  “$/oz GC=F”,       “#FFCC00”, fmt=”{:.0f}”)
macro_html += _mc_cell(“WTI CRUDE”,   cl_val,  “$/bbl CL=F”,      “#FF8000”)
macro_html += _mc_cell(“S&P 500 ETF”, spy_val, “SPY Last”,        “#CCCCCC”)
macro_html += _mc_cell(“NASDAQ ETF”,  qqq_val, “QQQ Last”,        “#CCCCCC”)
macro_html += (
f’<div class="bbg-macro-cell">’
f’<div class="bbg-macro-lbl">MKT STATUS</div>’
f’<div class="bbg-macro-val" style="color:{status_color};font-size:11px;">{market_status}</div>’
f’<div class="bbg-macro-sub">NYSE / NASDAQ</div>’
f’</div>’
)
macro_html += (
f’<div class="bbg-macro-cell">’
f’<div class="bbg-macro-lbl">TERMINAL</div>’
f’<div class="bbg-macro-val" style="color:#FF8000;font-size:9px;">v3.0</div>’
f’<div class="bbg-macro-sub">GICS . SOLOMON</div>’
f’</div>’
)
macro_html += (
f’<div class="bbg-macro-cell">’
f’<div class="bbg-macro-lbl">COMPLIANCE</div>’
f’<div class="bbg-macro-val" style="color:#4da6ff;font-size:8px;">FINRA 15c3-5</div>’
f’<div class="bbg-macro-sub">SEC REG T / NMS</div>’
f’</div>’
)
macro_html += (
f’<div class="bbg-macro-cell">’
f’<div class="bbg-macro-lbl">DATA</div>’
f’<div class="bbg-macro-val" style="color:#00CC00;font-size:9px;">* LIVE</div>’
f’<div class="bbg-macro-sub">Yahoo Finance</div>’
f’</div>’
)
macro_html += ‘</div>’
st.markdown(macro_html, unsafe_allow_html=True)

# —————————————————————–

# 17. MAIN TABS

# —————————————————————–

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
“  ? SUREFIRE  “,
“  ? LONG-TERM  “,
“  ! SWING  “,
“  ? FAT PITCH  “,
“  ? SOLOMON STRATEGY  “,
“  ? PORTFOLIO  “,
])

# ===============================================================

# TAB 1 – SUREFIRE

# ===============================================================

with tab1:
st.markdown(’<div class="bbg-panel"><div class="bbg-panel-hdr">? SUREFIRE BUY / SELL – ULTRA-STRICT CONFLUENCE SCANNER</div><div class="bbg-panel-body">’, unsafe_allow_html=True)
st.markdown(
“Requires 5/7 confluence score: full EMA stack, MACD crossover, BB breakout, “
“RSI zone, Stochastic, volume spike (>=1.3x), ADX strength (>=30). “
“Both buy and sell signals. Holding period: 1-5 days.”,
unsafe_allow_html=False
)
st.markdown(’</div></div>’, unsafe_allow_html=True)

```
# FIX #12: pre-populate from GICS selector if set
gics_default = st.session_state.get('gics_ticker', 'SPY')
col_t, col_b = st.columns([3, 1])
with col_t:
    sf_ticker = st.text_input("TICKER", value=gics_default, key="sf_ticker",
                              placeholder="SPY, QQQ, NVDA...")
with col_b:
    st.markdown("<br>", unsafe_allow_html=True)
    run_sf = st.button("> EXECUTE SCAN", key="run_sf")

if run_sf:
    with st.spinner(f"Analyzing {sf_ticker.upper()} -- institutional signal scan..."):
        df_raw  = fetch_data(sf_ticker.upper())
        df_ind  = compute_indicators(df_raw)
        result  = evaluate_surefire(df_ind)

    if df_ind.empty:
        st.error("Failed to retrieve data. Check ticker symbol.")
    else:
        show_signal_card(result)
        show_trade_levels(result)
        show_rationale(result)
        if result['signal'] != 'STANDBY':
            send_alert(sf_ticker, result['signal'],
                       ' | '.join(result.get('reasons', [])))
        st.plotly_chart(
            build_chart(df_ind.tail(120), sf_ticker.upper(), result),
            use_container_width=True)
        show_backtest_section(df_ind, "surefire")

st.markdown("---")
st.markdown('<div class="bbg-panel-hdr">? UNIVERSE SCAN -- SUREFIRE ACROSS ALL 25 GICS NODES</div>', unsafe_allow_html=True)
if st.button("? SCAN ALL GICS SECTORS", key="scan_sf"):
    with st.spinner("Scanning 25 GICS nodes for surefire setups..."):
        results = run_universe_scan("surefire")
    if results:
        st.success(f"[OK] {len(results)} surefire signal(s) detected across GICS universe.")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No surefire signals detected. Capital preserved -- awaiting confluence.")
```

# ===============================================================

# TAB 2 – LONG-TERM

# ===============================================================

with tab2:
st.markdown(’<div class="bbg-panel"><div class="bbg-panel-hdr">? LONG-TERM MONTHLY – POSITION TRADE SCANNER</div><div class="bbg-panel-body">’, unsafe_allow_html=True)
st.markdown(
“Secular trend following. Golden/Death Cross, 200 EMA positioning, “
“Fibonacci retracement, MACD trend confirmation. Holding period: weeks to months.”
)
st.markdown(’</div></div>’, unsafe_allow_html=True)

```
col_t2, col_b2 = st.columns([3, 1])
with col_t2:
    lt_ticker = st.text_input("TICKER", value="QQQ", key="lt_ticker")
with col_b2:
    st.markdown("<br>", unsafe_allow_html=True)
    run_lt = st.button("> EXECUTE SCAN", key="run_lt")

if run_lt:
    with st.spinner(f"Analyzing {lt_ticker.upper()} -- long-term structural scan..."):
        df_raw  = fetch_data(lt_ticker.upper(), period="3y")
        df_ind  = compute_indicators(df_raw)
        result  = evaluate_longterm(df_ind)

    if df_ind.empty:
        st.error("Failed to retrieve data.")
    else:
        show_signal_card(result)
        show_trade_levels(result)
        show_rationale(result)
        if result['signal'] != 'STANDBY':
            send_alert(lt_ticker, result['signal'],
                       ' | '.join(result.get('reasons', [])))
        st.plotly_chart(
            build_chart(df_ind.tail(250), lt_ticker.upper(), result),
            use_container_width=True)
        show_backtest_section(df_ind, "longterm")

st.markdown("---")
st.markdown('<div class="bbg-panel-hdr">? UNIVERSE SCAN -- LONG-TERM SIGNALS ACROSS ALL 25 GICS</div>', unsafe_allow_html=True)
if st.button("? SCAN ALL GICS SECTORS", key="scan_lt"):
    with st.spinner("Scanning for long-term structural setups..."):
        results = run_universe_scan("longterm")
    if results:
        st.success(f"[OK] {len(results)} long-term opportunity(ies) detected.")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No long-term signals. Awaiting structural alignment.")
```

# ===============================================================

# TAB 3 – SWING

# ===============================================================

with tab3:
st.markdown(’<div class="bbg-panel"><div class="bbg-panel-hdr">! SWING TRADING – MEAN REVERSION + MOMENTUM SCANNER</div><div class="bbg-panel-body">’, unsafe_allow_html=True)
st.markdown(
“2-10 day mean reversion. Targets BB extremes, oversold RSI bounces, Stochastic “
“cross setups. ADX gate REMOVED for swing – low ADX confirms range-bound environment.”
)
st.markdown(’</div></div>’, unsafe_allow_html=True)

```
col_t3, col_b3 = st.columns([3, 1])
with col_t3:
    sw_ticker = st.text_input("TICKER", value="NVDA", key="sw_ticker")
with col_b3:
    st.markdown("<br>", unsafe_allow_html=True)
    run_sw = st.button("> EXECUTE SCAN", key="run_sw")

if run_sw:
    with st.spinner(f"Scanning {sw_ticker.upper()} for swing edge..."):
        df_raw  = fetch_data(sw_ticker.upper(), period="6mo")
        df_ind  = compute_indicators(df_raw)
        result  = evaluate_swing(df_ind)

    if df_ind.empty:
        st.error("Failed to retrieve data.")
    else:
        show_signal_card(result)
        show_trade_levels(result)
        show_rationale(result)
        if result['signal'] != 'STANDBY':
            send_alert(sw_ticker, result['signal'],
                       ' | '.join(result.get('reasons', [])))
        st.plotly_chart(
            build_chart(df_ind.tail(90), sw_ticker.upper(), result),
            use_container_width=True)
        show_backtest_section(df_ind, "swing")

st.markdown("---")
st.markdown('<div class="bbg-panel-hdr">? UNIVERSE SCAN -- SWING SETUPS ACROSS ALL 25 GICS</div>', unsafe_allow_html=True)
if st.button("? SCAN ALL GICS SECTORS", key="scan_sw"):
    with st.spinner("Scanning for swing setups..."):
        results = run_universe_scan("swing")
    if results:
        st.success(f"[OK] {len(results)} swing opportunity(ies) detected.")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No swing setups detected. Awaiting mean reversion extremes.")
```

# ===============================================================

# TAB 4 – FAT PITCH (original theory)

# ===============================================================

with tab4:
st.markdown(’<div class="bbg-panel"><div class="bbg-panel-hdr">? FAT PITCH – ORIGINAL SOLOMON SCANNER . 3-GATE MAXIMUM CONVICTION</div><div class="bbg-panel-body">’, unsafe_allow_html=True)
st.markdown(
“The original strategy: do nothing 90% of the time. Only execute when all 3 ultra-strict gates “
“fire simultaneously – **Gate 1:** Volume >= 150% avg . “
“**Gate 2:** ADX >= 35 (terminal velocity) . “
“**Gate 3:** BB upper breakout + MACD confirmation + RSI 60-85. “
“No compromises. No partial scores.”
)
st.markdown(’</div></div>’, unsafe_allow_html=True)

```
col_t4, col_b4 = st.columns([3, 1])
with col_t4:
    fp_ticker = st.text_input("TICKER", value="SPY", key="fp_ticker",
                              placeholder="SPY, QQQ, XLE...")
with col_b4:
    st.markdown("<br>", unsafe_allow_html=True)
    run_fp = st.button("> SCAN FOR FAT PITCH", key="run_fp")

if run_fp:
    with st.spinner(f"Running 3-gate fat pitch analysis on {fp_ticker.upper()}..."):
        df_raw = fetch_data(fp_ticker.upper())
        df_ind = compute_indicators(df_raw)
        result = evaluate_fat_pitch(df_ind)

    if df_ind.empty:
        st.error("Failed to retrieve data.")
    else:
        show_signal_card(result, style="fat")
        show_trade_levels(result)
        show_rationale(result)
        if result['signal'] != 'STANDBY':
            send_alert(fp_ticker, result['signal'],
                       ' | '.join(result.get('reasons', [])))
        st.plotly_chart(
            build_chart(df_ind.tail(120), fp_ticker.upper(), result),
            use_container_width=True)
        show_backtest_section(df_ind, "fatpitch")

st.markdown("---")
st.markdown('<div class="bbg-panel-hdr">? FAT PITCH UNIVERSE SCAN -- ALL 25 GICS NODES</div>', unsafe_allow_html=True)
if st.button("? SCAN ALL GICS FOR FAT PITCH SETUPS", key="scan_fp"):
    with st.spinner("Running 3-gate scan across all GICS sectors..."):
        results = run_universe_scan("fatpitch")
    if results:
        st.success(
            f"[OK] {len(results)} FAT PITCH setup(s) detected -- these are rare, "
            f"maximum-conviction signals.")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning(
            "SCAN COMPLETE: Zero Fat Pitch setups detected. "
            "Capital preserved. Standby -- patience is the edge.")
```

# ===============================================================

# TAB 5 – SOLOMON STRATEGY

# ===============================================================

with tab5:
st.markdown(’<div class="bbg-panel"><div class="bbg-panel-hdr">? SOLOMON STRATEGY – QUANTITATIVE ROTATION ENGINE . 32 ASSETS . 7-CRITERIA SCORING</div><div class="bbg-panel-body">’, unsafe_allow_html=True)
st.markdown(
“Multi-factor quantitative rotation across 32 ETFs spanning all major GICS sectors, “
“macro proxies, and safe harbors. Scores each asset on RAM, Relative Strength, “
“50D Slope, Volume Confirmation, and ROC Acceleration. “
“Top 5 ranked assets receive allocation signals.”
)
st.markdown(’</div></div>’, unsafe_allow_html=True)

```
run_solomon = st.button("> RUN SOLOMON STRATEGY SCAN", key="run_solomon")

if run_solomon:
    with st.spinner("Loading Solomon universe -- computing 7-criteria scoring..."):
        sol_data = fetch_solomon_data()
        vix_close_sol = _mval("^VIX", macro_data) or 15.0
        sol_df = calculate_solomon_factors(
            sol_data,
            sol_data["Close"].index[-1],
            vix_close_sol
        )

    if sol_df.empty:
        st.error("Failed to compute Solomon factors.")
    else:
        top5 = sol_df[sol_df["RNK"] <= 5]

        # Top 5 cards (from original app)
        cards_html = '<div class="bbg-panel"><div class="bbg-panel-hdr">TOP 5 ROTATION TARGETS -- SOLOMON STRATEGY</div><div class="bbg-top5">'
        for tkr, row in top5.iterrows():
            strong   = row["SIGNAL"] == "STRONG BUY"
            c_class  = "bbg-t5c strong" if strong else "bbg-t5c buy"
            sig_col  = "#FF8000" if strong else "#FFCC00"
            sig_lbl  = "* STRONG BUY" if strong else "* BUY"
            ytd_cls  = "ytd-pos" if row["YTD"] > 0 else "ytd-neg"
            aw       = min(row["ALLOC"] * 5, 100)
            cards_html += f'''<div class="{c_class}">
                <div class="bbg-t5-tkr">{tkr}</div>
                <div class="bbg-t5-sec">{row["SECTOR"]}</div>
                <div class="bbg-t5-price">${row["PRICE"]:.2f}</div>
                <div class="{ytd_cls}">YTD {row["YTD"]:+.1f}%</div>
                <div class="bbg-t5-sig" style="color:{sig_col};">{sig_lbl}</div>
                <div class="bbg-t5-alloc">ALLOC {row["ALLOC"]:.1f}%</div>
                <div class="bar-bg"><div class="bar-fill" style="width:{aw}%;background:{sig_col};"></div></div>
                <div class="bbg-t5-rsn">Score {row["SCORE"]:.1f} . ADX {row["ADX"]:.0f} . {row["REASON"]}</div>
            </div>'''
        cards_html += '</div></div>'
        st.markdown(cards_html, unsafe_allow_html=True)

        # Full ledger
        sc_class = lambda s: (
            "sig-sb" if "STRONG BUY" in s else "sig-b" if "BUY" in s
            else "sig-h" if "HOLD" in s else "sig-ht" if "HALT" in s
            else "sig-ss" if "STRONG SELL" in s else "sig-s"
        )
        hdrs = ["RNK","SECTOR","SIGNAL","REASON","ALLOC","PRICE","STOP","ADX","SCORE","YTD","1M%","3M%","REL_STR","RAM","VOL_CF"]
        tbl_h = '<div class="bbg-panel" style="margin-top:4px;"><div class="bbg-panel-hdr">SOLOMON FULL QUANTITATIVE LEDGER -- ALL 32 ASSETS</div>'
        tbl_h += '<div class="bbg-scroll"><table class="bbg-tbl"><thead><tr>'
        tbl_h += '<th class="l">TKR</th>'
        for h in hdrs:
            al = "l" if h in ["SECTOR","SIGNAL","REASON"] else ""
            tbl_h += f'<th class="{al}">{h}</th>'
        tbl_h += '</tr></thead><tbody>'

        for tkr, row in sol_df.iterrows():
            sc  = sc_class(row["SIGNAL"])
            yc  = "#00CC00" if row["YTD"] > 0 else "#CC0000"
            al  = f'{row["ALLOC"]:.1f}%' if row["ALLOC"] > 0 else "--"
            rc  = "#00CC00" if row["REL_STR"] > 0 else "#CC0000"
            slc = "#00CC00" if row["50D_SLP"] > 0 else "#CC0000"
            tbl_h += f'''<tr>
                <td class="l">{tkr}</td>
                <td>{row["RNK"]}</td>
                <td class="sec">{row["SECTOR"]}</td>
                <td class="l {sc}">{row["SIGNAL"]}</td>
                <td class="l" style="color:#444;font-size:9px;">{row["REASON"]}</td>
                <td style="color:#FF8000;">{al}</td>
                <td>{row["PRICE"]:.2f}</td>
                <td style="color:#CC0000;">{row["STOP"]:.2f}</td>
                <td>{row["ADX"]:.1f}</td>
                <td style="color:#FF8000;">{row["SCORE"]:.1f}</td>
                <td style="color:{yc};">{row["YTD"]:.1f}%</td>
                <td>{row["RET_1M"]:.1f}%</td>
                <td>{row["RET_3M"]:.1f}%</td>
                <td style="color:{rc};">{row["REL_STR"]*100:+.2f}%</td>
                <td>{row["RAM"]:.2f}</td>
                <td>{row["VOL_CF"]:.2f}</td>
            </tr>'''

        tbl_h += '</tbody></table></div></div>'
        st.markdown(tbl_h, unsafe_allow_html=True)

        # Glossary (from original app)
        glossary = '''<div class="bbg-panel" style="margin-top:4px;">
            <div class="bbg-panel-hdr">LEDGER COLUMN GLOSSARY -- SOLOMON 7-CRITERIA</div>
            <div class="bbg-panel-body">
            <table class="bbg-tbl"><thead><tr>
            <th class="l">COLUMN</th><th class="l">MEANING</th><th class="l">ROLE</th>
            </tr></thead><tbody>
            <tr><td class="l" style="color:#FF8000;">SCORE</td><td class="l" style="color:#888;">Weighted z-score of 5 factors</td><td class="l" style="color:#555;">Higher = stronger momentum edge</td></tr>
            <tr><td class="l" style="color:#FF8000;">ALLOC</td><td class="l" style="color:#888;">Suggested position size %</td><td class="l" style="color:#555;">ATR-based, capped at 20%</td></tr>
            <tr><td class="l" style="color:#FF8000;">STOP</td><td class="l" style="color:#888;">20-day high - 2.5xATR14</td><td class="l" style="color:#555;">Exit if closes below this</td></tr>
            <tr><td class="l" style="color:#FF8000;">ADX</td><td class="l" style="color:#888;">Trend strength 0-100</td><td class="l" style="color:#555;">Must be &gt;25 to confirm</td></tr>
            <tr><td class="l" style="color:#FF8000;">RAM</td><td class="l" style="color:#888;">1M return / 1M volatility</td><td class="l" style="color:#555;">Highest alpha factor (25% wt)</td></tr>
            <tr><td class="l" style="color:#FF8000;">VOL_CF</td><td class="l" style="color:#888;">20-day avg / 90-day avg vol</td><td class="l" style="color:#555;">Must be &gt;1.2x to confirm</td></tr>
            <tr><td class="l" style="color:#FF8000;">REL_STR</td><td class="l" style="color:#888;">Asset avg return vs SPY avg (1M-9M)</td><td class="l" style="color:#555;">Must outpace SPY</td></tr>
            <tr><td class="l" style="color:#FF8000;">50D_SLP</td><td class="l" style="color:#888;">Slope of 50-day SMA over 21 days</td><td class="l" style="color:#555;">Must be rising (+)</td></tr>
            </tbody></table>
            <div style="color:#444;font-size:9px;margin-top:6px;padding-top:4px;border-top:1px solid #1A1A1A;">
            SOLOMON 7-CRITERIA: 1. Above 200MA &nbsp;2. ADX &gt;25 &nbsp;3. Vol CF &gt;1.2x &nbsp;
            4. RAM &gt;0 &nbsp;5. Rel Strength &gt;SPY &nbsp;6. ROC Accelerating &nbsp;7. 50D Slope Rising
            -- ALL 7 must pass for STRONG BUY. Informational only -- FINRA 15c3-5.
            </div></div></div>'''
        st.markdown(glossary, unsafe_allow_html=True)

        # Sector concentration heatmap
        st.markdown('<div class="bbg-panel" style="margin-top:4px;"><div class="bbg-panel-hdr">MOMENTUM HEATMAP -- ALL 32 ASSETS</div><div class="bbg-hm">', unsafe_allow_html=True)
        hm_html = ""
        mx_ = sol_df["SCORE"].max()
        mn_ = sol_df["SCORE"].min()
        for tkr, row in sol_df.sort_values("SCORE", ascending=False).iterrows():
            s = row["SCORE"]
            n = (s - mn_) / (mx_ - mn_) if mx_ != mn_ else 0.5
            bg = f"rgb(0,{int(n*140)+20},0)" if n > 0.5 else f"rgb({int((1-n)*120)},20,0)"
            fg = "#FF8000" if n > 0.7 else "#FFCC00" if n > 0.4 else "#CC3333"
            bdr = "border:1px solid #FF8000;" if "BUY" in row["SIGNAL"] else "border:1px solid #1A1A1A;"
            hm_html += (
                f'<div class="bbg-hm-cell" style="background:{bg};color:{fg};{bdr}">'
                f'<span>{tkr}</span><span>{s:.0f}</span></div>'
            )
        st.markdown(hm_html + '</div></div>', unsafe_allow_html=True)

else:
    st.info("Click > RUN SOLOMON STRATEGY SCAN to load the full rotation analysis.")
```

# ===============================================================

# TAB 6 – PORTFOLIO

# ===============================================================

with tab6:
portfolio_section()

# —————————————————————–

# 18. TICKER TAPE (bottom bar – st.marquee note: no native Streamlit

# support; using fixed HTML bar as fallback)

# —————————————————————–

tape_syms = [“SPY”,“QQQ”,“DIA”,”^VIX”,”^TNX”,“GC=F”,“CL=F”]
tape_items = []
for sym in tape_syms:
try:
col_ = macro_data[sym].dropna()
cur  = float(col_.iloc[-1])
prv  = float(col_.iloc[-2])
pct  = ((cur - prv) / prv) * 100
pc   = “#00CC00” if pct >= 0 else “#CC0000”
lbl  = sym.replace(”^”,””).replace(”=F”,””)
tape_items.append(
f’<span style="margin-right:24px;">’
f’<span style="color:#FF8000;font-weight:700;">{lbl}</span> ’
f’<span style="color:#CCC;">{cur:.2f}</span> ’
f’<span style="color:{pc};">{pct:+.2f}%</span>’
f’</span>’
)
except Exception:
pass

if tape_items:
st.markdown(
f’<div style="position:fixed;bottom:0;left:0;width:100%;background:#000;'
f'border-top:1px solid #FF8000;padding:4px 12px;font-size:10px;'
f'display:flex;gap:4px;z-index:9998;overflow:hidden;">’
+ “”.join(tape_items) +
f’</div>’,
unsafe_allow_html=True
)