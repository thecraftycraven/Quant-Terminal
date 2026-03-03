import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components
import requests

# ==========================================
# 1. PAGE CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="QUANT TERMINAL", layout="wide", initial_sidebar_state="collapsed")

est_zone = ZoneInfo('America/New_York')
now_est = datetime.datetime.now(est_zone)
time_str = now_est.strftime("%I:%M %p ET")
date_str = now_est.strftime("%b %d, %Y").upper()
is_weekend = now_est.weekday() >= 5
is_open_hours = datetime.time(9, 30) <= now_est.time() <= datetime.time(16, 0)
market_status = "CLOSED" if is_weekend or not is_open_hours else "OPEN"
status_color = "#00FF41" if market_status == "OPEN" else "#FF3131"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

* {{ font-family: 'IBM Plex Mono', monospace !important; }}
html, body, .stApp {{ background-color: #020408 !important; color: #C8D8E8; }}
.stApp {{ padding-bottom: 36px; }}

/* HIDE STREAMLIT CHROME */
#MainMenu, footer, header, .stDeployButton {{ visibility: hidden; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}
section[data-testid="stSidebar"] {{ display: none; }}

/* STATUS BAR */
.status-bar {{
    display: flex; justify-content: space-between; align-items: center;
    background: #020408; border-bottom: 1px solid #0D3B1E;
    padding: 5px 16px; position: sticky; top: 0; z-index: 1000;
}}
.s-left {{ color: {status_color}; font-size: 11px; font-weight: 700; letter-spacing: 2px; }}
.s-center {{ color: #4A8F6A; font-size: 10px; letter-spacing: 1px; }}
.s-right {{ color: #4A8F6A; font-size: 10px; text-align: right; }}

/* PANELS */
.panel {{
    border: 1px solid #0D2818; background: #040C0A;
    padding: 8px 10px; margin-bottom: 6px; border-radius: 2px;
}}
.panel-hdr {{
    color: #00FF41; font-size: 9px; font-weight: 700; letter-spacing: 2.5px;
    text-transform: uppercase; border-bottom: 1px solid #0D2818;
    padding-bottom: 5px; margin-bottom: 7px;
}}

/* TABLES */
.qt {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
.qt th {{ color: #3A6B4A; font-size: 9px; padding: 4px 6px; border-bottom: 1px solid #0D2818;
          text-align: right; letter-spacing: 1px; font-weight: 500; }}
.qt th:first-child {{ text-align: left; }}
.qt td {{ padding: 4px 6px; border-bottom: 1px solid #080F0A; text-align: right; color: #A8C4B0; }}
.qt td:first-child {{ text-align: left; color: #E0F0E8; font-weight: 500; }}
.qt tr:hover td {{ background: #060F08; }}

/* LEDGER */
.ledger-wrap {{ max-height: 340px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: #0D3B1E #020408; }}
.lt {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
.lt th {{
    position: sticky; top: 0; background: #040C0A; color: #00FF41;
    font-size: 9px; padding: 5px 6px; border-bottom: 1px solid #00FF41;
    text-align: right; letter-spacing: 1px; white-space: nowrap;
}}
.lt th:first-child, .lt th:nth-child(2), .lt th:nth-child(3) {{ text-align: left; }}
.lt td {{ padding: 4px 6px; border-bottom: 1px solid #060F08; text-align: right; font-size: 10px; white-space: nowrap; }}
.lt td:first-child {{ text-align: left; color: #00CC33; font-weight: 700; }}
.lt td:nth-child(2) {{ text-align: left; color: #5A8A6A; font-size: 9px; }}
.lt td:nth-child(3) {{ text-align: left; }}
.lt tr:hover td {{ background: #060F08; }}

/* SIGNALS */
.sig-sb {{ color: #00FF41; font-weight: 700; }}
.sig-b  {{ color: #66CC66; font-weight: 600; }}
.sig-h  {{ color: #FFCC00; font-weight: 600; }}
.sig-s  {{ color: #FF4444; font-weight: 600; }}
.sig-ss {{ color: #FF0000; font-weight: 700; }}
.sig-ht {{ color: #FF00FF; font-weight: 700; }}

/* HEATMAP */
.hm-grid {{ display: grid; grid-template-columns: repeat(10, 1fr); gap: 2px; }}
.hm-cell {{
    text-align: center; padding: 5px 2px; font-size: 9px; font-weight: 700;
    border-radius: 1px; line-height: 1.4;
}}

/* MACRO ROW */
.macro-row {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }}
.macro-card {{
    flex: 1; min-width: 80px; background: #040C0A; border: 1px solid #0D2818;
    padding: 5px 8px; border-radius: 2px; text-align: center;
}}
.macro-lbl {{ color: #3A6B4A; font-size: 8px; letter-spacing: 1px; margin-bottom: 2px; }}
.macro-val {{ color: #00FF41; font-size: 12px; font-weight: 700; }}
.macro-sub {{ color: #5A8A6A; font-size: 9px; }}

/* ALLOCATION BARS */
.alloc-bar-bg {{ background: #0D2818; height: 4px; border-radius: 2px; margin-top: 3px; }}
.alloc-bar-fill {{ height: 4px; border-radius: 2px; background: #00FF41; }}

/* TOP 5 CARDS */
.top5-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; margin-bottom: 6px; }}
.top5-card {{
    background: #040C0A; border: 1px solid #0D2818; padding: 8px 6px;
    border-radius: 2px; text-align: center;
}}
.top5-card.strong {{ border-color: #00FF41; }}
.top5-card.buy {{ border-color: #66CC66; }}
.top5-tkr {{ font-size: 14px; font-weight: 700; color: #00FF41; }}
.top5-sec {{ font-size: 8px; color: #3A6B4A; letter-spacing: 1px; margin: 2px 0; }}
.top5-score {{ font-size: 11px; color: #C8D8E8; }}
.top5-alloc {{ font-size: 10px; font-weight: 700; margin-top: 4px; }}

/* TICKER TAPE */
.tape {{
    position: fixed; bottom: 0; left: 0; width: 100%; background: #020408;
    border-top: 1px solid #0D3B1E; padding: 5px 16px; font-size: 10px;
    display: flex; gap: 24px; z-index: 999; overflow: hidden;
}}
.tape-item {{ white-space: nowrap; }}
.tape-sym {{ color: #4A8F6A; font-weight: 600; }}
.tape-prc {{ color: #C8D8E8; }}
.tape-up {{ color: #00FF41; }}
.tape-dn {{ color: #FF4444; }}

/* FRED CURVE */
.yield-curve {{ display: flex; align-items: flex-end; gap: 3px; height: 60px; padding-top: 8px; }}
.yc-bar-wrap {{ flex: 1; display: flex; flex-direction: column; align-items: center; }}
.yc-bar {{ background: linear-gradient(to top, #00FF41, #005520); border-radius: 1px 1px 0 0; width: 100%; }}
.yc-lbl {{ color: #3A6B4A; font-size: 7px; margin-top: 2px; }}
.yc-val {{ color: #00FF41; font-size: 8px; font-weight: 700; }}

/* TABS */
.stTabs [data-baseweb="tab-list"] {{ background: #020408; border-bottom: 1px solid #0D2818; gap: 0; }}
.stTabs [data-baseweb="tab"] {{ background: #020408; color: #3A6B4A; font-size: 10px; letter-spacing: 1px; padding: 6px 16px; border-radius: 0; }}
.stTabs [aria-selected="true"] {{ background: #040C0A !important; color: #00FF41 !important; border-bottom: 2px solid #00FF41; }}

div[data-testid="stMetric"] {{ display: none; }}
</style>

<div class="status-bar">
    <div class="s-left">◉ MKT {market_status}</div>
    <div class="s-center">QUANT ROTATION TERMINAL v2.0 — FABER MODEL + FRED MACRO OVERLAY</div>
    <div class="s-right">{time_str} &nbsp;|&nbsp; {date_str}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. UNIVERSE
# ==========================================
TICKER_SECTORS = {
    "OIH":"Energy","XLE":"Energy","XLB":"Materials","XME":"Materials","WOOD":"Materials",
    "XLI":"Industrials","IYT":"Industrials","CARZ":"Cons Disc","XLY":"Cons Disc","PEJ":"Cons Disc",
    "XRT":"Cons Disc","XLP":"Cons Staples","PBJ":"Cons Staples","IHI":"Health Care","XBI":"Health Care",
    "KBE":"Financials","IAI":"Financials","KIE":"Financials","IGV":"Info Tech","SMH":"Info Tech",
    "IYZ":"Comm Svcs","XLC":"Comm Svcs","XLU":"Utilities","FCG":"Utilities","IDU":"Utilities",
    "PHO":"Utilities","ICLN":"Utilities","VNQ":"Real Estate","REET":"Real Estate",
    "EFA":"Global","VWO":"Global","INDY":"Global","KWEB":"Global",
    "DBA":"Uncorrelated","PDBC":"Uncorrelated","UUP":"Uncorrelated","VIXY":"Uncorrelated",
    "SLV":"Uncorrelated","TIP":"Uncorrelated","DBB":"Uncorrelated","CWB":"Uncorrelated",
    "IAU":"Macro","FBTC":"Macro","BIL":"Safe Harbor","IEF":"Safe Harbor","TLT":"Safe Harbor"
}
TICKERS = list(TICKER_SECTORS.keys())
BENCHMARKS = ["SPY", "QQQ", "DIA", "^VIX", "^TNX", "^TYX", "GC=F", "CL=F"]

# ==========================================
# 3. FRED API
# ==========================================
FRED_API_KEY = "YOUR_FRED_API_KEY"  # ← Replace with your key from https://fred.stlouisfed.org/docs/api/api_key.html

FRED_SERIES = {
    "DGS1MO":  "1M",
    "DGS3MO":  "3M",
    "DGS6MO":  "6M",
    "DGS1":    "1Y",
    "DGS2":    "2Y",
    "DGS5":    "5Y",
    "DGS10":   "10Y",
    "DGS30":   "30Y",
    "T10YIE":  "10Y BEI",    # 10Y Breakeven Inflation
    "BAMLH0A0HYM2": "HY Spread",  # High Yield OAS
    "VIXCLS":  "VIX",
    "DCOILWTICO": "WTI Oil",
    "DEXUSEU": "EUR/USD",
    "DEXJPUS": "USD/JPY",
    "UMCSENT": "Cons Sentiment",
}

@st.cache_data(ttl=3600)
def fetch_fred(series_id):
    """Fetch a single FRED series. Returns latest value or None."""
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 5,
            "observation_start": (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        }
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            obs = [o for o in r.json().get("observations", []) if o["value"] != "."]
            if obs:
                return float(obs[0]["value"])
    except:
        pass
    return None

@st.cache_data(ttl=3600)
def fetch_fred_series(series_id, periods=252):
    """Fetch historical FRED series as a pandas Series."""
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": periods,
        }
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            obs = [o for o in r.json().get("observations", []) if o["value"] != "."]
            if obs:
                s = pd.Series(
                    {pd.to_datetime(o["date"]): float(o["value"]) for o in obs}
                ).sort_index()
                return s
    except:
        pass
    return pd.Series(dtype=float)

def fetch_all_fred():
    """Fetch all FRED macro data points."""
    data = {}
    for sid, label in FRED_SERIES.items():
        data[label] = fetch_fred(sid)
    return data

# Treasury curve structure for yield curve
YIELD_CURVE_SERIES = {
    "DGS1MO":"1M","DGS3MO":"3M","DGS6MO":"6M",
    "DGS1":"1Y","DGS2":"2Y","DGS5":"5Y","DGS10":"10Y","DGS30":"30Y"
}

@st.cache_data(ttl=3600)
def fetch_yield_curve():
    curve = {}
    for sid, label in YIELD_CURVE_SERIES.items():
        val = fetch_fred(sid)
        if val: curve[label] = val
    return curve

# ==========================================
# 4. MARKET DATA ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def fetch_market_data():
    all_tickers = TICKERS + BENCHMARKS
    data = yf.download(all_tickers, period="2y", progress=False, auto_adjust=True)
    return data

def calculate_factors(data, target_date):
    closes = data['Close'].loc[:target_date]
    highs  = data['High'].loc[:target_date]
    lows   = data['Low'].loc[:target_date]
    vols   = data['Volume'].loc[:target_date]
    if len(closes) < 200:
        return pd.DataFrame(), False, 0.0

    spy_p    = closes["SPY"].dropna()
    vix_close = data['Close']["^VIX"].loc[:target_date].dropna().iloc[-1]
    vix_halt  = vix_close > 30
    tnx       = data['Close']["^TNX"].loc[:target_date].dropna().iloc[-1] if "^TNX" in data['Close'].columns else None

    results = []
    for t in TICKERS:
        try:
            p = closes[t].dropna()
            h = highs[t].dropna()
            l = lows[t].dropna()
            v = vols[t].dropna()
            if len(p) < 200: continue

            # Core momentum factors
            ytd_base = p[p.index.year == target_date.year]
            ytd = ((p.iloc[-1] / ytd_base.iloc[0]) - 1) * 100 if not ytd_base.empty else 0
            ret_1m = p.pct_change(21).iloc[-1]
            ret_3m = p.pct_change(63).iloc[-1]
            ret_6m = p.pct_change(126).iloc[-1]
            ret_12m = p.pct_change(252).iloc[-1]
            vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram    = ret_1m / vol_1m if vol_1m != 0 else 0
            rel_str = ret_3m - spy_p.pct_change(63).iloc[-1]

            sma_50   = p.rolling(50).mean()
            sma_200  = p.rolling(200).mean()
            sma_50_slp = (sma_50.iloc[-1] - sma_50.iloc[-21]) / sma_50.iloc[-21]
            above_200  = p.iloc[-1] > sma_200.iloc[-1]
            above_50   = p.iloc[-1] > sma_50.iloc[-1]

            v90 = v.rolling(90).mean().iloc[-1]
            vol_cf = (v.rolling(20).mean().iloc[-1] / v90) if v90 != 0 else 1

            tr = pd.concat([h-l, np.abs(h-p.shift()), np.abs(l-p.shift())], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            stop = p.tail(20).max() - (2.5 * atr)
            stop_dist = (p.iloc[-1] - stop) / p.iloc[-1]
            alloc_base = (0.01 / stop_dist) * 100 if stop_dist > 0 else 0

            up = h - h.shift(1); dw = l.shift(1) - l
            tr14 = tr.rolling(14).sum()
            pd_di = 100*(pd.Series(np.where((up>dw)&(up>0),up,0),index=p.index).rolling(14).sum()/tr14)
            md_di = 100*(pd.Series(np.where((dw>up)&(dw>0),dw,0),index=p.index).rolling(14).sum()/tr14)
            adx   = (100*np.abs(pd_di-md_di)/(pd_di+md_di)).rolling(14).mean().iloc[-1]

            roc_20 = p.pct_change(20).iloc[-1]
            roc_60 = p.pct_change(60).iloc[-1]
            roc_ac = roc_20 - (roc_60 / 3)

            # Treasury rate adjustment — penalise low-yield assets when rates are high
            rate_adj = 0
            if tnx and tnx > 4.5:
                sector = TICKER_SECTORS.get(t, "")
                if sector in ["Safe Harbor", "Utilities", "Real Estate"]:
                    rate_adj = -0.3  # penalise bond proxies in high-rate regime

            results.append({
                'TKR': t, 'SECTOR': TICKER_SECTORS[t],
                'PRICE': p.iloc[-1], 'YTD': ytd,
                'RET_1M': ret_1m*100, 'RET_3M': ret_3m*100,
                'RET_6M': ret_6m*100, 'RET_12M': ret_12m*100,
                'RAM': ram, 'REL_STR': rel_str, '50D_SLP': sma_50_slp,
                'VOL_CF': vol_cf, 'ADX': adx, 'STOP': stop,
                'ROC_AC': roc_ac, 'ATR': atr, 'ALLOC_BASE': min(alloc_base, 25),
                'Above_200': above_200, 'Above_50': above_50,
                'RATE_ADJ': rate_adj,
            })
        except:
            continue

    df = pd.DataFrame(results).set_index('TKR')
    f  = ['RAM', 'REL_STR', '50D_SLP', 'VOL_CF', 'ROC_AC']
    z  = (df[f] - df[f].mean()) / df[f].std()
    df['SCORE'] = (
        z['RAM']    * 0.25 +
        z['REL_STR']* 0.20 +
        z['50D_SLP']* 0.20 +
        z['VOL_CF'] * 0.20 +
        z['ROC_AC'] * 0.15
    ) * 100 + df['RATE_ADJ'] * 10

    df = df.sort_values('SCORE', ascending=False)
    df['RNK'] = range(1, len(df)+1)

    # ── SIGNAL LOGIC ──────────────────────────────────────────────────────────
    # Criteria checklist — each adds/removes from STRONG BUY
    signals, reasons, allocs = [], [], []
    for idx, row in df.iterrows():
        fails = []
        if not row['Above_200']:   fails.append("Below 200MA")
        if row['ADX'] <= 25:       fails.append(f"ADX {row['ADX']:.0f}")
        if row['VOL_CF'] < 1.2:    fails.append(f"Vol {row['VOL_CF']:.2f}x")
        if row['RAM'] <= 0:        fails.append("Neg RAM")
        if row['REL_STR'] <= 0:    fails.append("Lags SPY")
        if row['ROC_AC'] <= 0:     fails.append("Decel ROC")
        if row['50D_SLP'] <= 0:    fails.append("Neg 50D")

        rnk = row['RNK']
        n_fail = len(fails)

        if vix_halt:
            sig = "HALT"; reason = "VIX>30"; alloc = 0
        elif not row['Above_200'] or row['PRICE'] < row['STOP']:
            sig = "STRONG SELL"; reason = fails[0] if fails else "ATR Stop"; alloc = 0
        elif rnk <= 5 and n_fail == 0:
            sig = "STRONG BUY"; reason = "ALL CLEAR"; alloc = min(row['ALLOC_BASE'], 20)
        elif rnk <= 5 and n_fail <= 2:
            sig = "BUY"; reason = ", ".join(fails); alloc = min(row['ALLOC_BASE'] * 0.6, 12)
        elif rnk <= 5 and n_fail > 2:
            sig = "BUY"; reason = ", ".join(fails[:2]); alloc = min(row['ALLOC_BASE'] * 0.3, 6)
        elif rnk <= 10 and n_fail == 0:
            sig = "HOLD"; reason = "Buffer zone"; alloc = 0
        elif rnk <= 10:
            sig = "HOLD"; reason = ", ".join(fails[:1]); alloc = 0
        else:
            sig = "SELL"; reason = ", ".join(fails[:2]) if fails else f"Rank #{rnk}"; alloc = 0

        signals.append(sig); reasons.append(reason); allocs.append(alloc)

    df['SIGNAL']  = signals
    df['REASON']  = reasons
    df['ALLOC']   = allocs
    return df, vix_halt, vix_close

@st.cache_data(ttl=3600)
def run_backtest(data):
    closes = data['Close']
    monthly = closes.resample('ME').last()
    months  = monthly.index[-13:-1]
    log = []
    for i in range(len(months)-1):
        s_raw, e_raw = months[i], months[i+1]
        s_idx = closes.index.get_indexer([s_raw], method='pad')[0]
        e_idx = closes.index.get_indexer([e_raw], method='pad')[0]
        s, e  = closes.index[s_idx], closes.index[e_idx]
        snap, _, _ = calculate_factors(data, s)
        if snap.empty: continue
        buys = snap[snap['SIGNAL'].isin(['STRONG BUY','BUY'])].head(5).index.tolist()
        spy_ret = ((closes.loc[e,'SPY'] / closes.loc[s,'SPY']) - 1) * 100
        strat_ret = ((closes.loc[e,buys].mean() / closes.loc[s,buys].mean()) - 1)*100 if buys else 0
        log.append({
            "Month": s.strftime('%b %y'),
            "Targets": ", ".join(buys) if buys else "CASH",
            "Strategy": strat_ret,
            "SPY": spy_ret,
            "Alpha": strat_ret - spy_ret
        })
    return pd.DataFrame(log)

# ==========================================
# 5. DATA FETCH & COMPUTE
# ==========================================
with st.spinner(''):
    raw_data  = fetch_market_data()
    df, v_halt, v_close = calculate_factors(raw_data, raw_data['Close'].index[-1])
    bt_df     = run_backtest(raw_data)
    fred_data = fetch_all_fred()
    yc_data   = fetch_yield_curve()

closes = raw_data['Close']

# ── TOP 5 ANALYSIS ────────────────────────────────────────────────────────────
top5_df = df[df['RNK'] <= 5]
top5_tickers = top5_df.index.tolist()

# ── REGIME ────────────────────────────────────────────────────────────────────
safe_etfs  = ["BIL","TLT","IEF","IAU","GLD","XLU","XLP"]
infla_etfs = ["PDBC","XLE","XME","OIH","DBA","SLV","DBB"]
safe_cnt   = sum(t in safe_etfs for t in top5_tickers)
inf_cnt    = sum(t in infla_etfs for t in top5_tickers)
if safe_cnt >= 2:   regime, rc = "RISK-OFF", "#FFCC00"
elif inf_cnt >= 2:  regime, rc = "INFLATIONARY", "#FF6600"
else:               regime, rc = "RISK-ON", "#00FF41"

# ── YIELD SPREAD (2s10s) ─────────────────────────────────────────────────────
y2  = fred_data.get("2Y")
y10 = fred_data.get("10Y")
spread_2s10s = (y10 - y2) if (y2 and y10) else None
curve_status = "INVERTED" if spread_2s10s and spread_2s10s < 0 else "NORMAL"
curve_color  = "#FF4444" if curve_status == "INVERTED" else "#00FF41"

# ==========================================
# 6. LAYOUT
# ==========================================

# ── ROW 1: MACRO CARDS ───────────────────────────────────────────────────────
macro_html = '<div class="macro-row">'

def macro_card(label, val, sub="", color="#00FF41"):
    fmt = f"{val:.2f}" if val is not None else "N/A"
    return f'<div class="macro-card"><div class="macro-lbl">{label}</div><div class="macro-val" style="color:{color};">{fmt}</div><div class="macro-sub">{sub}</div></div>'

# VIX
vix_col = "#FF4444" if v_close > 30 else "#FFCC00" if v_close > 20 else "#00FF41"
macro_html += macro_card("VIX", v_close, "Fear Index", vix_col)

# 10Y Treasury
tnx_val = closes["^TNX"].dropna().iloc[-1] if "^TNX" in closes else None
macro_html += macro_card("10Y YIELD", tnx_val, "Treasury", "#00FF41")

# 30Y Treasury
tyx_val = closes["^TYX"].dropna().iloc[-1] if "^TYX" in closes else None
macro_html += macro_card("30Y YIELD", tyx_val, "Treasury", "#00FF41")

# 2s10s Spread
if spread_2s10s is not None:
    macro_html += macro_card("2s10s", spread_2s10s, curve_status, curve_color)

# HY Spread
hy = fred_data.get("HY Spread")
hy_col = "#FF4444" if hy and hy > 500 else "#FFCC00" if hy and hy > 350 else "#00FF41"
macro_html += macro_card("HY OAS", hy, "bps", hy_col)

# Breakeven inflation
bei = fred_data.get("10Y BEI")
macro_html += macro_card("10Y BEI", bei, "Breakeven Inf", "#FF6600")

# Gold
gc_val = closes["GC=F"].dropna().iloc[-1] if "GC=F" in closes else None
macro_html += macro_card("GOLD", gc_val, "$/oz", "#FFCC00")

# Oil
cl_val = closes["CL=F"].dropna().iloc[-1] if "CL=F" in closes else None
macro_html += macro_card("WTI OIL", cl_val, "$/bbl", "#FF6600")

# EUR/USD
eurusd = fred_data.get("EUR/USD")
macro_html += macro_card("EUR/USD", eurusd, "FX", "#00FF41")

# Consumer sentiment
sent = fred_data.get("Cons Sentiment")
sent_col = "#00FF41" if sent and sent > 80 else "#FFCC00" if sent and sent > 60 else "#FF4444"
macro_html += macro_card("CONS SENT", sent, "UMich", sent_col)

# Regime
macro_html += f'<div class="macro-card"><div class="macro-lbl">REGIME</div><div class="macro-val" style="font-size:9px; color:{rc};">{regime}</div><div class="macro-sub">Capital Flow</div></div>'

macro_html += '</div>'
st.markdown(macro_html, unsafe_allow_html=True)

# ── ROW 2: TOP 5 CARDS + YIELD CURVE ─────────────────────────────────────────
r2c1, r2c2 = st.columns([3.5, 1.5])

with r2c1:
    st.markdown('<div class="panel"><div class="panel-hdr">TOP 5 ROTATION TARGETS</div>', unsafe_allow_html=True)
    cards_html = '<div class="top5-grid">'
    for tkr, row in top5_df.iterrows():
        is_strong = row['SIGNAL'] == 'STRONG BUY'
        card_class = "top5-card strong" if is_strong else "top5-card buy"
        alloc_w = min(row['ALLOC'] * 5, 100)
        alloc_col = "#00FF41" if is_strong else "#66CC66"
        ytd_col = "#00FF41" if row['YTD'] > 0 else "#FF4444"
        sig_label = "◉ STRONG BUY" if is_strong else "◎ BUY"
        sig_col   = "#00FF41" if is_strong else "#66CC66"
        cards_html += f"""
        <div class="{card_class}">
            <div class="top5-tkr">{tkr}</div>
            <div class="top5-sec">{row['SECTOR']}</div>
            <div class="top5-score">Score: {row['SCORE']:.1f}</div>
            <div style="color:{ytd_col}; font-size:10px;">YTD {row['YTD']:+.1f}%</div>
            <div class="top5-alloc" style="color:{sig_col};">{sig_label}</div>
            <div style="color:{alloc_col}; font-size:11px; font-weight:700;">ALLOC {row['ALLOC']:.1f}%</div>
            <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{alloc_w}%; background:{alloc_col};"></div></div>
            <div style="color:#3A6B4A; font-size:8px; margin-top:3px;">{row['REASON']}</div>
        </div>
        """
    cards_html += '</div></div>'
    st.markdown(cards_html, unsafe_allow_html=True)

with r2c2:
    # Yield Curve
    yc_html = '<div class="panel"><div class="panel-hdr">TREASURY YIELD CURVE</div>'
    if yc_data:
        labels = ["1M","3M","6M","1Y","2Y","5Y","10Y","30Y"]
        vals   = [yc_data.get(l) for l in labels]
        valid  = [(l,v) for l,v in zip(labels,vals) if v is not None]
        if valid:
            max_v = max(v for _,v in valid)
            yc_html += '<div class="yield-curve">'
            for lbl, val in valid:
                bar_h = max(4, int((val / max_v) * 52)) if max_v > 0 else 4
                yc_html += f'<div class="yc-bar-wrap"><div class="yc-val">{val:.1f}</div><div class="yc-bar" style="height:{bar_h}px;"></div><div class="yc-lbl">{lbl}</div></div>'
            yc_html += '</div>'
            if spread_2s10s is not None:
                yc_html += f'<div style="text-align:center; margin-top:6px; font-size:9px; color:{curve_color};">2s10s SPREAD: {spread_2s10s:+.2f}% &nbsp;|&nbsp; {curve_status}</div>'
    else:
        yc_html += '<div style="color:#3A6B4A; font-size:10px; padding:10px;">Add FRED API key to enable yield curve</div>'
    yc_html += '</div>'
    st.markdown(yc_html, unsafe_allow_html=True)

# ── ROW 3: TABS ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "  📊 CHART  ",
    "  📋 LEDGER  ",
    "  🔥 HEATMAP  ",
    "  ⏱ BACKTEST  ",
    "  🌐 MACRO API  "
])

# ── TAB 1: TOP 5 CHART ───────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="panel"><div class="panel-hdr">TOP 5 YTD PERFORMANCE vs SPY</div>', unsafe_allow_html=True)
    ytd_start = closes[closes.index.year == now_est.year]
    if not ytd_start.empty and top5_tickers:
        chart_rows = {}
        spy_base = closes['SPY'][closes.index >= ytd_start.index[0]].dropna()
        chart_rows['SPY'] = ((spy_base / spy_base.iloc[0]) - 1) * 100

        for t in top5_tickers:
            if t in closes.columns:
                s = closes[t][closes.index >= ytd_start.index[0]].dropna()
                if not s.empty:
                    chart_rows[t] = ((s / s.iloc[0]) - 1) * 100

        chart_df = pd.DataFrame(chart_rows).dropna()
        if not chart_df.empty:
            st.line_chart(chart_df, height=280, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 6-month rolling window chart
    st.markdown('<div class="panel"><div class="panel-hdr">6-MONTH ROLLING WINDOW</div>', unsafe_allow_html=True)
    six_mo_ago = closes.index[-1] - pd.DateOffset(months=6)
    if top5_tickers:
        roll_rows = {}
        for t in top5_tickers + ['SPY']:
            if t in closes.columns:
                s = closes[t][closes.index >= six_mo_ago].dropna()
                if not s.empty:
                    roll_rows[t] = ((s / s.iloc[0]) - 1) * 100
        roll_df = pd.DataFrame(roll_rows).dropna()
        if not roll_df.empty:
            st.line_chart(roll_df, height=220, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 2: FULL LEDGER ───────────────────────────────────────────────────────
with tab2:
    def sig_class(s):
        if 'STRONG BUY' in s: return 'sig-sb'
        if 'BUY' in s: return 'sig-b'
        if 'HOLD' in s: return 'sig-h'
        if 'HALT' in s: return 'sig-ht'
        if 'STRONG SELL' in s: return 'sig-ss'
        return 'sig-s'

    ledger = '<div class="panel"><div class="panel-hdr">QUANTITATIVE FACTOR LEDGER — ALL 46 ASSETS</div>'
    ledger += '<div class="ledger-wrap"><table class="lt"><thead><tr>'
    heads = ['RNK','TKR','SECTOR','SIGNAL','REASON','ALLOC','PRICE','STOP','ADX','SCORE','YTD','1M','3M','6M','12M','RAM','VOL_CF']
    for h in heads:
        ledger += f'<th>{h}</th>'
    ledger += '</tr></thead><tbody>'

    for tkr, row in df.iterrows():
        sc = sig_class(row['SIGNAL'])
        ytd_col = "#00FF41" if row['YTD'] > 0 else "#FF4444"
        alloc_str = f"{row['ALLOC']:.1f}%" if row['ALLOC'] > 0 else "—"
        ledger += f"""<tr>
            <td>{row['RNK']}</td>
            <td>{tkr}</td>
            <td>{row['SECTOR']}</td>
            <td class="{sc}">{row['SIGNAL']}</td>
            <td style="color:#5A8A6A; font-size:9px;">{row['REASON']}</td>
            <td style="color:#FF6600;">{alloc_str}</td>
            <td>{row['PRICE']:.2f}</td>
            <td>{row['STOP']:.2f}</td>
            <td>{row['ADX']:.1f}</td>
            <td style="color:#00FF41;">{row['SCORE']:.1f}</td>
            <td style="color:{ytd_col};">{row['YTD']:.1f}%</td>
            <td>{row['RET_1M']:.1f}%</td>
            <td>{row['RET_3M']:.1f}%</td>
            <td>{row['RET_6M']:.1f}%</td>
            <td>{row['RET_12M']:.1f}%</td>
            <td>{row['RAM']:.2f}</td>
            <td>{row['VOL_CF']:.2f}</td>
        </tr>"""

    ledger += '</tbody></table></div></div>'
    st.markdown(ledger, unsafe_allow_html=True)

# ── TAB 3: HEATMAP ───────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="panel"><div class="panel-hdr">YTD PERFORMANCE HEATMAP</div><div class="hm-grid">', unsafe_allow_html=True)
    hm_html = ""
    for tkr, row in df.sort_values('YTD', ascending=False).iterrows():
        v   = row['YTD']
        sig = row['SIGNAL']
        if v > 20:    bg, fg = "#005520", "#00FF41"
        elif v > 10:  bg, fg = "#003D18", "#00CC33"
        elif v > 0:   bg, fg = "#001A0A", "#009922"
        elif v > -10: bg, fg = "#1A0000", "#CC3333"
        else:         bg, fg = "#330000", "#FF4444"
        border = "border: 1px solid #00FF41;" if 'BUY' in sig else ""
        hm_html += f'<div class="hm-cell" style="background:{bg}; color:{fg}; {border}">{tkr}<br>{v:+.1f}%</div>'
    st.markdown(hm_html + '</div></div>', unsafe_allow_html=True)

    # Score heatmap
    st.markdown('<div class="panel"><div class="panel-hdr">MOMENTUM SCORE HEATMAP</div><div class="hm-grid">', unsafe_allow_html=True)
    score_html = ""
    max_score = df['SCORE'].max(); min_score = df['SCORE'].min()
    for tkr, row in df.sort_values('SCORE', ascending=False).iterrows():
        s = row['SCORE']
        norm = (s - min_score) / (max_score - min_score) if max_score != min_score else 0.5
        g = int(norm * 200)
        bg = f"rgb(0,{g+30},0)" if norm > 0.5 else f"rgb({int((1-norm)*150)},30,0)"
        fg = "#00FF41" if norm > 0.5 else "#FF6644"
        score_html += f'<div class="hm-cell" style="background:{bg}; color:{fg};">{tkr}<br>{s:.0f}</div>'
    st.markdown(score_html + '</div></div>', unsafe_allow_html=True)

# ── TAB 4: BACKTEST ──────────────────────────────────────────────────────────
with tab4:
    bc1, bc2, bc3 = st.columns([1.5, 1.5, 1])
    with bc1:
        st.markdown('<div class="panel"><div class="panel-hdr">12-MONTH MONTH-BY-MONTH</div>', unsafe_allow_html=True)
        if not bt_df.empty:
            bt_table = '<div class="ledger-wrap" style="max-height:280px;"><table class="lt"><thead><tr><th>MONTH</th><th>TARGETS</th><th>STRAT</th><th>SPY</th><th>ALPHA</th></tr></thead><tbody>'
            for _, r in bt_df.iterrows():
                sc = "#00FF41" if r['Strategy'] > 0 else "#FF4444"
                ac = "#00FF41" if r['Alpha'] > 0 else "#FF4444"
                bt_table += f'<tr><td>{r["Month"]}</td><td style="color:#00CCFF; font-size:9px;">{r["Targets"]}</td><td style="color:{sc};">{r["Strategy"]:.1f}%</td><td style="color:#888;">{r["SPY"]:.1f}%</td><td style="color:{ac}; font-weight:700;">{r["Alpha"]:+.1f}%</td></tr>'
            bt_table += '</tbody></table></div></div>'
            st.markdown(bt_table, unsafe_allow_html=True)

    with bc2:
        st.markdown('<div class="panel"><div class="panel-hdr">STRATEGY vs SPY RETURNS</div>', unsafe_allow_html=True)
        if not bt_df.empty:
            chart_bt = bt_df.set_index('Month')[['Strategy','SPY']]
            st.bar_chart(chart_bt, height=280, use_container_width=True, color=["#00FF41","#FF4444"])
        st.markdown('</div>', unsafe_allow_html=True)

    with bc3:
        st.markdown('<div class="panel"><div class="panel-hdr">SUMMARY STATS</div>', unsafe_allow_html=True)
        if not bt_df.empty:
            total_strat = bt_df['Strategy'].sum()
            total_spy   = bt_df['SPY'].sum()
            total_alpha = bt_df['Alpha'].sum()
            win_rate    = (bt_df['Strategy'] > bt_df['SPY']).mean() * 100
            pos_months  = (bt_df['Strategy'] > 0).sum()
            stats_html  = f"""<table class="qt">
                <tr><td>Total Return</td><td style="color:#00FF41;">{total_strat:.1f}%</td></tr>
                <tr><td>SPY Return</td><td style="color:#FF4444;">{total_spy:.1f}%</td></tr>
                <tr><td>Total Alpha</td><td style="color:#00FF41;">{total_alpha:+.1f}%</td></tr>
                <tr><td>Win Rate</td><td style="color:#00FF41;">{win_rate:.0f}%</td></tr>
                <tr><td>Pos Months</td><td style="color:#00FF41;">{pos_months}/{len(bt_df)}</td></tr>
                <tr><td>Avg Alpha</td><td style="color:#00FF41;">{total_alpha/len(bt_df):+.1f}%</td></tr>
            </table>"""
            st.markdown(stats_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 5: MACRO API STATUS ──────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="panel"><div class="panel-hdr">MACRO DATA API CONNECTIONS</div>', unsafe_allow_html=True)

    fred_connected = FRED_API_KEY != "YOUR_FRED_API_KEY" and any(v is not None for v in fred_data.values())

    api_table = '<table class="qt"><thead><tr><th>API</th><th>DATA</th><th>STATUS</th><th>HOW TO CONNECT</th></tr></thead><tbody>'

    apis = [
        ("FRED (St. Louis Fed)", "Treasury yields, inflation, spreads, FX, sentiment",
         fred_connected, "Get free key at fred.stlouisfed.org → replace FRED_API_KEY in code"),
        ("Yahoo Finance (yfinance)", "Price, volume, OHLC for all 46 ETFs + benchmarks",
         True, "Active — no key needed"),
        ("Alpha Vantage", "Fundamental data: P/E, EPS, revenue, earnings dates",
         False, "Get free key at alphavantage.co → add fetch_alpha_vantage() function"),
        ("Quandl / Nasdaq Data Link", "COT reports, futures positioning, economic data",
         False, "Get key at data.nasdaq.com → pip install nasdaq-data-link"),
        ("SEC EDGAR", "ETF holdings, 13F filings, institutional flow data",
         False, "Free API at efts.sec.gov — no key needed, add fetch_edgar() function"),
        ("CME / CFTC", "Commitment of Traders — futures positioning by asset class",
         False, "Free at cftc.gov/MarketReports → parse weekly COT CSV"),
        ("OpenBB / Financial Modeling Prep", "Macro calendar, earnings, dividends, analyst ratings",
         False, "Get key at financialmodelingprep.com → add fetch_fmp() function"),
        ("BLS (Bureau of Labor Stats)", "CPI, PPI, unemployment, jobs data",
         False, "Free API at api.bls.gov → register for key"),
    ]

    for name, data_desc, connected, how_to in apis:
        status_col = "#00FF41" if connected else "#FF4444"
        status_txt = "● CONNECTED" if connected else "○ NOT CONNECTED"
        api_table += f'<tr><td style="color:#00CC33; font-weight:700;">{name}</td><td style="color:#5A8A6A; font-size:9px;">{data_desc}</td><td style="color:{status_col}; font-size:9px;">{status_txt}</td><td style="color:#3A6B4A; font-size:9px;">{how_to}</td></tr>'

    api_table += '</tbody></table>'
    st.markdown(api_table, unsafe_allow_html=True)

    # FRED live data display
    st.markdown('<div style="margin-top:8px;"><div class="panel-hdr" style="margin-top:10px;">FRED LIVE DATA FEED</div>', unsafe_allow_html=True)
    fred_table = '<table class="qt"><thead><tr><th>SERIES</th><th>VALUE</th><th>STATUS</th></tr></thead><tbody>'
    for label, val in fred_data.items():
        status = "● LIVE" if val is not None else "○ NEEDS API KEY"
        sc = "#00FF41" if val is not None else "#FF4444"
        fmt = f"{val:.3f}" if val is not None else "—"
        fred_table += f'<tr><td>{label}</td><td style="color:#00FF41;">{fmt}</td><td style="color:{sc}; font-size:9px;">{status}</td></tr>'
    fred_table += '</tbody></table></div>'
    st.markdown(fred_table + '</div>', unsafe_allow_html=True)

# ── TICKER TAPE ───────────────────────────────────────────────────────────────
tape_syms = ["SPY", "QQQ", "DIA", "^VIX", "^TNX", "GC=F", "CL=F"]
tape_html = '<div class="tape">'
for sym in tape_syms:
    try:
        col = closes[sym].dropna()
        cur, prv = col.iloc[-1], col.iloc[-2]
        pct = ((cur - prv) / prv) * 100
        pc  = "tape-up" if pct >= 0 else "tape-dn"
        lbl = sym.replace("^","").replace("=F","")
        tape_html += f'<span class="tape-item"><span class="tape-sym">{lbl}</span> <span class="tape-prc">{cur:.2f}</span> <span class="{pc}">{pct:+.2f}%</span></span>'
    except:
        pass
tape_html += '</div>'
st.markdown(tape_html, unsafe_allow_html=True)
