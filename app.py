import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components
import requests

st.set_page_config(page_title="NY LATINO FINANCIAL TERMINAL", layout="wide", initial_sidebar_state="collapsed")

est_zone = ZoneInfo("America/New_York")
now_est  = datetime.datetime.now(est_zone)
time_str = now_est.strftime("%H:%M:%S ET")
date_str = now_est.strftime("%d %b %Y").upper()
is_weekend   = now_est.weekday() >= 5
is_open      = datetime.time(9,30) <= now_est.time() <= datetime.time(16,0)
market_status = "OPEN" if (not is_weekend and is_open) else "CLOSED"
status_color  = "#FF8000" if market_status == "OPEN" else "#CC0000"

CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@300;400;500;600;700&display=swap");
*, *::before, *::after { font-family: "Source Code Pro", "Courier New", monospace !important; box-sizing: border-box; }
html, body, [class*="stApp"] { background-color: #000000 !important; color: #FFFFFF; margin: 0; padding: 0; }
.stApp { padding-bottom: 36px !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

.bbg-status { display:flex; justify-content:space-between; align-items:center; background:#000; border-bottom:2px solid #FF8000; padding:4px 12px; position:sticky; top:0; z-index:9999; height:28px; }
.bbg-status-l { font-size:11px; font-weight:700; letter-spacing:1.5px; }
.bbg-status-c { color:#FF8000; font-size:10px; letter-spacing:2px; font-weight:600; }
.bbg-status-r { color:#AAAAAA; font-size:10px; text-align:right; }

.bbg-macro-row { display:grid; grid-template-columns:repeat(13,1fr); border-bottom:1px solid #333; background:#050505; margin-top:10px; }
.bbg-macro-cell { padding:10px 6px; border-right:1px solid #1A1A1A; text-align:center; }
.bbg-macro-cell:last-child { border-right:none; }
.bbg-macro-lbl { color:#888; font-size:8px; letter-spacing:1px; text-transform:uppercase; margin-bottom:3px; }
.bbg-macro-val { font-size:14px; font-weight:700; line-height:1; }
.bbg-macro-sub { color:#555; font-size:8px; margin-top:2px; }

.yc-inline { display:flex; align-items:flex-end; gap:2px; height:26px; padding:0 2px; }
.yc-inline-col { flex:1; display:flex; flex-direction:column; align-items:center; }
.yc-inline-bar { background:#FF8000; border-radius:1px 1px 0 0; width:100%; min-height:2px; }
.yc-inline-lbl { color:#444; font-size:5px; margin-top:1px; }

.bbg-panel { border:1px solid #222; background:#0A0A0A; padding:0; margin-bottom:4px; }
.bbg-panel-hdr { background:#111; color:#FF8000; font-size:10px; font-weight:700; letter-spacing:2px; padding:4px 8px; border-bottom:1px solid #333; text-transform:uppercase; }
.bbg-panel-body { padding:4px 6px; }

.bbg-top5 { display:grid; grid-template-columns:repeat(5,1fr); }
.bbg-top5-wrap { margin-top: 35px; }
.bbg-tv-wrap { margin-top: 35px; display:flex; flex-direction:column; }
.bbg-tv-wrap .bbg-panel { flex:1; display:flex; flex-direction:column; }
.bbg-tv-wrap iframe { flex:1; width:100% !important; display:block; border:0; }
.bbg-t5c { padding:8px 10px; border-right:1px solid #1A1A1A; border-top:3px solid #333; background:#050505; }
.bbg-t5c:last-child { border-right:none; }
.bbg-t5c.strong { border-top-color:#FF8000; }
.bbg-t5c.buy    { border-top-color:#FFCC00; }
.bbg-t5-tkr   { color:#FF8000; font-size:18px; font-weight:700; line-height:1; }
.bbg-t5-sec   { color:#555; font-size:8px; letter-spacing:1px; margin:3px 0; text-transform:uppercase; }
.bbg-t5-price { color:#FFF; font-size:12px; font-weight:600; }
.ytd-pos { color:#00CC00; font-size:11px; }
.ytd-neg { color:#CC0000; font-size:11px; }
.bbg-t5-sig   { font-size:9px; font-weight:700; margin:4px 0 2px; letter-spacing:1px; }
.bbg-t5-alloc { color:#FF8000; font-size:13px; font-weight:700; }
.bar-bg  { background:#1A1A1A; height:3px; margin-top:4px; }
.bar-fill { height:3px; }
.bbg-t5-rsn { color:#444; font-size:8px; margin-top:3px; }

.bbg-tbl { width:100%; border-collapse:collapse; font-size:10px; }
.bbg-tbl th { background:#111; color:#FF8000; font-size:9px; font-weight:600; padding:5px 6px; border-bottom:1px solid #FF8000; text-align:right; letter-spacing:1px; white-space:nowrap; position:sticky; top:0; z-index:10; }
.bbg-tbl th.l { text-align:left; }
.bbg-tbl td { padding:4px 6px; border-bottom:1px solid #0D0D0D; text-align:right; color:#CCC; white-space:nowrap; }
.bbg-tbl td.l  { text-align:left; color:#FF8000; font-weight:700; }
.bbg-tbl td.sec { text-align:left; color:#555; font-size:9px; }
.bbg-tbl tr:hover td { background:#0D0D0D; }
.bbg-scroll { max-height:380px; overflow-y:auto; scrollbar-width:thin; scrollbar-color:#FF8000 #111; }

.sig-sb { color:#FF8000; font-weight:700; }
.sig-b  { color:#FFCC00; font-weight:600; }
.sig-h  { color:#888; }
.sig-s  { color:#CC3333; }
.sig-ss { color:#FF0000; font-weight:700; }
.sig-ht { color:#FF00FF; font-weight:700; }

/* HEATMAP: small squares, 9 columns */
.bbg-hm { display:grid; grid-template-columns:repeat(6,1fr); gap:2px; padding:6px; }
.bbg-hm-cell { display:flex; justify-content:space-between; align-items:center; padding:3px 6px; font-size:9px; font-weight:700; border-radius:2px; white-space:nowrap; }

.stTabs [data-baseweb="tab-list"] { background:#000 !important; border-bottom:1px solid #333 !important; gap:0 !important; padding:0 !important; }
.stTabs [data-baseweb="tab"] { background:#000 !important; color:#555 !important; font-size:10px !important; letter-spacing:1.5px !important; padding:6px 18px !important; border-radius:0 !important; border:none !important; }
.stTabs [aria-selected="true"] { background:#111 !important; color:#FF8000 !important; border-bottom:2px solid #FF8000 !important; }
.stTabs [data-baseweb="tab-panel"] { padding:0 !important; }

.notes-area { background:#050505; border:1px solid #222; color:#CCC; font-family:"Source Code Pro",monospace; font-size:11px; width:100%; min-height:300px; padding:10px; resize:vertical; outline:none; }
.notes-area:focus { border-color:#FF8000; }
textarea { background:#050505 !important; color:#CCC !important; border:1px solid #222 !important; border-radius:2px !important; font-family:"Source Code Pro",monospace !important; }
textarea:focus { border-color:#FF8000 !important; box-shadow:none !important; outline:none !important; }
[data-testid="stTextArea"] textarea { background:#050505 !important; color:#CCC !important; border:1px solid #333 !important; border-radius:2px !important; }
[data-testid="stTextArea"] textarea:focus { border-color:#FF8000 !important; box-shadow:none !important; }
[data-testid="stTextArea"] label { display:none !important; }
[data-testid="stTextArea"] { padding:0 !important; }

.bbg-tape { position:fixed; bottom:0; left:0; width:100%; background:#000; border-top:1px solid #FF8000; padding:4px 12px; font-size:10px; display:flex; gap:20px; z-index:9998; }
.tape-sym { color:#FF8000; font-weight:700; margin-right:4px; }
.tape-prc { color:#FFF; }
.tape-up  { color:#00CC00; }
.tape-dn  { color:#CC0000; }

[data-testid="stHorizontalBlock"] { gap:4px !important; padding:0 4px !important; }
[data-testid="stVerticalBlock"] { gap:0 !important; }
div[data-testid="column"] { padding:0 2px !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

STATUS_HTML = f"""<div class="bbg-status">
    <div class="bbg-status-l" style="color:{status_color};">■ MKT {market_status}</div>
    <div class="bbg-status-c">NEW YORK LATINO FINANCIAL TERMINAL &nbsp;·&nbsp; SOLOMON STRATEGY</div>
    <div class="bbg-status-r">{time_str}&nbsp;&nbsp;{date_str}</div>
</div>"""
st.markdown(STATUS_HTML, unsafe_allow_html=True)

# ── UNIVERSE ──────────────────────────────────────────────────────────────────
TICKER_SECTORS = {
    "OIH":"Energy","XLE":"Energy","XLB":"Materials","XME":"Materials","WOOD":"Materials",
    "XLI":"Industrials","IYT":"Industrials","CARZ":"Cons Disc","XLY":"Cons Disc",
    "PEJ":"Cons Disc","XRT":"Cons Disc","XLP":"Cons Staples","PBJ":"Cons Staples",
    "IHI":"Health Care","XBI":"Health Care","KBE":"Financials","IAI":"Financials",
    "KIE":"Financials","IGV":"Info Tech","SMH":"Info Tech","IYZ":"Comm Svcs",
    "XLC":"Comm Svcs","XLU":"Utilities","FCG":"Utilities","IDU":"Utilities",
    "PHO":"Utilities","ICLN":"Utilities","VNQ":"Real Estate","REET":"Real Estate",
    "EFA":"Global","VWO":"Global","INDY":"Global","KWEB":"Global",
    "DBA":"Uncorrelated","PDBC":"Uncorrelated","UUP":"Uncorrelated","VIXY":"Uncorrelated",
    "SLV":"Uncorrelated","TIP":"Uncorrelated","DBB":"Uncorrelated","CWB":"Uncorrelated",
    "IAU":"Macro","FBTC":"Macro","BIL":"Safe Harbor","IEF":"Safe Harbor","TLT":"Safe Harbor"
}
TICKERS    = list(TICKER_SECTORS.keys())
BENCHMARKS = ["SPY","QQQ","DIA","^VIX","^TNX","^TYX","GC=F","CL=F"]

# ── API KEYS ──────────────────────────────────────────────────────────────────
FRED_API_KEY = "93069da065d835f300947c9dd312c50d"
ALPHA_KEY    = "I7L9I79E7WRJGLFC"
FMP_KEY      = "JNYpveoF4uOcnTzewvlbRPkyJt1sEn8T"

YIELD_CURVE_IDS = {
    "DGS1MO":"1M","DGS3MO":"3M","DGS6MO":"6M",
    "DGS1":"1Y","DGS2":"2Y","DGS5":"5Y","DGS10":"10Y","DGS30":"30Y"
}
FRED_MACRO_IDS = {
    "DGS2":"2Y Yield","DGS10":"10Y Yield","DGS30":"30Y Yield",
    "T10YIE":"10Y BEI","BAMLH0A0HYM2":"HY Spread",
    "DEXUSEU":"EUR/USD","UMCSENT":"Cons Sent",
    "UNRATE":"Unemployment","CPIAUCSL":"CPI","T10Y2Y":"2s10s Spread",
}

@st.cache_data(ttl=3600)
def fred_latest(series_id):
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id":series_id,"api_key":FRED_API_KEY,"file_type":"json","sort_order":"desc","limit":5},
            timeout=6
        )
        if r.status_code == 200:
            obs = [o for o in r.json().get("observations",[]) if o["value"] != "."]
            return float(obs[0]["value"]) if obs else None
    except:
        return None

@st.cache_data(ttl=3600)
def fetch_yield_curve():
    return {lbl: fred_latest(sid) for sid, lbl in YIELD_CURVE_IDS.items()}

@st.cache_data(ttl=3600)
def fetch_fred_macro():
    return {lbl: fred_latest(sid) for sid, lbl in FRED_MACRO_IDS.items()}

@st.cache_data(ttl=7200)
def fetch_alpha_vantage_sector():
    try:
        r = requests.get("https://www.alphavantage.co/query",
            params={"function":"SECTOR","apikey":ALPHA_KEY}, timeout=8)
        if r.status_code == 200:
            return r.json().get("Rank A: Real-Time Performance", {})
    except:
        pass
    return {}

@st.cache_data(ttl=7200)
def fetch_bls_cpi():
    try:
        payload = {"seriesid":["CUSR0000SA0"],"startyear":str(now_est.year-1),"endyear":str(now_est.year)}
        r = requests.post("https://api.bls.gov/publicAPI/v2/timeseries/data/",
            json=payload, timeout=8, headers={"Content-type":"application/json"})
        if r.status_code == 200:
            series = r.json().get("Results",{}).get("series",[])
            if series:
                latest = series[0]["data"][0]
                return float(latest["value"]), latest["periodName"], latest["year"]
    except:
        pass
    return None, None, None

@st.cache_data(ttl=1800)
@st.cache_data(ttl=3600)
def fetch_fmp_macro_calendar():
    """FMP economic calendar — upcoming events"""
    try:
        today = now_est.strftime("%Y-%m-%d")
        future = (now_est + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        r = requests.get(
            f"https://financialmodelingprep.com/api/v3/economic_calendar",
            params={"from": today, "to": future, "apikey": FMP_KEY},
            timeout=8
        )
        if r.status_code == 200:
            return r.json()[:20]
    except:
        pass
    return []

@st.cache_data(ttl=3600)
def fetch_fmp_sector_pe():
    """FMP sector P/E ratios"""
    try:
        r = requests.get(
            "https://financialmodelingprep.com/api/v4/sector_price_earning_ratio",
            params={"date": now_est.strftime("%Y-%m-%d"), "exchange": "NYSE", "apikey": FMP_KEY},
            timeout=8
        )
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

@st.cache_data(ttl=1800)
def fetch_fmp_market_hours():
    """FMP market hours / status"""
    try:
        r = requests.get(
            "https://financialmodelingprep.com/api/v3/market-hours",
            params={"apikey": FMP_KEY}, timeout=6
        )
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def fetch_financial_news():
    """Alpha Vantage news sentiment"""
    try:
        r = requests.get("https://www.alphavantage.co/query",
            params={"function":"NEWS_SENTIMENT","apikey":ALPHA_KEY,"limit":"20","sort":"LATEST"},
            timeout=8)
        if r.status_code == 200:
            feed = r.json().get("feed", [])
            return feed[:20]
    except:
        pass
    return []

@st.cache_data(ttl=3600)
def fetch_market_data():
    return yf.download(TICKERS + BENCHMARKS, period="2y", progress=False, auto_adjust=True)

def calculate_factors(data, target_date):
    closes = data["Close"].loc[:target_date]
    highs  = data["High"].loc[:target_date]
    lows   = data["Low"].loc[:target_date]
    vols   = data["Volume"].loc[:target_date]
    if len(closes) < 200:
        return pd.DataFrame(), False, 0.0

    spy_p     = closes["SPY"].dropna()
    vix_close = data["Close"]["^VIX"].loc[:target_date].dropna().iloc[-1]
    vix_halt  = vix_close > 30
    tnx_val   = data["Close"]["^TNX"].loc[:target_date].dropna().iloc[-1] if "^TNX" in data["Close"].columns else None

    results = []
    for t in TICKERS:
        try:
            p = closes[t].dropna(); h = highs[t].dropna()
            l = lows[t].dropna();   v = vols[t].dropna()
            if len(p) < 200: continue

            ytd_px = p[p.index.year == target_date.year]
            ytd    = ((p.iloc[-1]/ytd_px.iloc[0])-1)*100 if not ytd_px.empty else 0

            ret_1m = p.pct_change(21).iloc[-1]
            ret_3m = p.pct_change(63).iloc[-1]
            ret_6m = p.pct_change(126).iloc[-1]
            ret_9m = p.pct_change(189).iloc[-1]

            vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram    = ret_1m / vol_1m if vol_1m != 0 else 0
            rel_str = ret_3m - spy_p.pct_change(63).iloc[-1]

            sma50  = p.rolling(50).mean()
            sma200 = p.rolling(200).mean()
            slp50  = (sma50.iloc[-1] - sma50.iloc[-21]) / sma50.iloc[-21]
            above200 = p.iloc[-1] > sma200.iloc[-1]

            v90    = v.rolling(90).mean().iloc[-1]
            vol_cf = (v.rolling(20).mean().iloc[-1] / v90) if v90 != 0 else 1

            tr   = pd.concat([h-l, np.abs(h-p.shift()), np.abs(l-p.shift())], axis=1).max(axis=1)
            atr  = tr.rolling(14).mean().iloc[-1]
            stop = p.tail(20).max() - (2.5 * atr)
            sd   = (p.iloc[-1] - stop) / p.iloc[-1]
            alloc_base = min((0.01/sd)*100, 25) if sd > 0 else 0

            up  = h-h.shift(1); dw = l.shift(1)-l
            tr14 = tr.rolling(14).sum()
            pdi = 100*(pd.Series(np.where((up>dw)&(up>0),up,0),index=p.index).rolling(14).sum()/tr14)
            mdi = 100*(pd.Series(np.where((dw>up)&(dw>0),dw,0),index=p.index).rolling(14).sum()/tr14)
            adx = (100*np.abs(pdi-mdi)/(pdi+mdi)).rolling(14).mean().iloc[-1]
            roc_ac = p.pct_change(20).iloc[-1] - (p.pct_change(60).iloc[-1]/3)

            rate_adj = 0
            if tnx_val and tnx_val > 4.5:
                if TICKER_SECTORS.get(t,"") in ["Safe Harbor","Utilities","Real Estate"]:
                    rate_adj = -0.3

            results.append({
                "TKR":t,"SECTOR":TICKER_SECTORS[t],"PRICE":p.iloc[-1],"YTD":ytd,
                "RET_1M":ret_1m*100,"RET_3M":ret_3m*100,"RET_6M":ret_6m*100,"RET_9M":ret_9m*100,
                "RAM":ram,"REL_STR":rel_str,"50D_SLP":slp50,"VOL_CF":vol_cf,"ADX":adx,
                "STOP":stop,"ROC_AC":roc_ac,"ALLOC_BASE":alloc_base,"Above_200":above200,"RATE_ADJ":rate_adj,
            })
        except:
            continue

    if not results:
        return pd.DataFrame(), vix_halt, vix_close

    df = pd.DataFrame(results).set_index("TKR")
    f  = ["RAM","REL_STR","50D_SLP","VOL_CF","ROC_AC"]
    z  = (df[f]-df[f].mean())/df[f].std()
    df["SCORE"] = (z["RAM"]*.25+z["REL_STR"]*.20+z["50D_SLP"]*.20+z["VOL_CF"]*.20+z["ROC_AC"]*.15)*100 + df["RATE_ADJ"]*10
    df = df.sort_values("SCORE",ascending=False)
    df["RNK"] = range(1,len(df)+1)

    sigs,ress,allocs=[],[],[]
    for idx,row in df.iterrows():
        fails=[]
        if not row["Above_200"]: fails.append("Below 200MA")
        if row["ADX"]<=25:       fails.append(f"ADX {row['ADX']:.0f}")
        if row["VOL_CF"]<1.2:    fails.append(f"Vol {row['VOL_CF']:.2f}x")
        if row["RAM"]<=0:        fails.append("Neg RAM")
        if row["REL_STR"]<=0:    fails.append("Lags SPY")
        if row["ROC_AC"]<=0:     fails.append("Decel ROC")
        if row["50D_SLP"]<=0:    fails.append("Neg 50D Slope")
        rnk=row["RNK"]; n=len(fails)

        if vix_halt:              sig,res,alloc="HALT","VIX > 30",0
        elif not row["Above_200"] or row["PRICE"]<row["STOP"]: sig,res,alloc="STRONG SELL",fails[0] if fails else "ATR Stop",0
        elif rnk<=5 and n==0:    sig,res,alloc="STRONG BUY","ALL CLEAR",min(row["ALLOC_BASE"],20)
        elif rnk<=5 and n<=2:    sig,res,alloc="BUY",", ".join(fails),min(row["ALLOC_BASE"]*.6,12)
        elif rnk<=5:             sig,res,alloc="BUY",", ".join(fails[:2]),min(row["ALLOC_BASE"]*.3,6)
        elif rnk<=10 and n==0:   sig,res,alloc="HOLD","Rank buffer",0
        elif rnk<=10:            sig,res,alloc="HOLD",", ".join(fails[:1]),0
        else:                    sig,res,alloc="SELL",", ".join(fails[:2]) if fails else f"Rank #{rnk}",0
        sigs.append(sig);ress.append(res);allocs.append(alloc)

    df["SIGNAL"]=sigs; df["REASON"]=ress; df["ALLOC"]=allocs
    return df,vix_halt,vix_close

@st.cache_data(ttl=3600)
def run_backtest(data):
    closes  = data["Close"]
    monthly = closes.resample("ME").last()
    months  = monthly.index[-13:-1]
    log=[]
    for i in range(len(months)-1):
        s_raw,e_raw=months[i],months[i+1]
        si=closes.index.get_indexer([s_raw],method="pad")[0]
        ei=closes.index.get_indexer([e_raw],method="pad")[0]
        s,e=closes.index[si],closes.index[ei]
        snap,_,_=calculate_factors(data,s)
        if snap.empty: continue
        buys=snap[snap["SIGNAL"].isin(["STRONG BUY","BUY"])].head(5).index.tolist()
        spy_r=((closes.loc[e,"SPY"]/closes.loc[s,"SPY"])-1)*100
        strat_r=((closes.loc[e,buys].mean()/closes.loc[s,buys].mean())-1)*100 if buys else 0
        log.append({"Month":s.strftime("%b %y"),"Targets":", ".join(buys) if buys else "CASH",
                    "Strategy":strat_r,"SPY":spy_r,"Alpha":strat_r-spy_r})
    return pd.DataFrame(log)

# ── FETCH ─────────────────────────────────────────────────────────────────────
with st.spinner(""):
    raw      = fetch_market_data()
    df,v_halt,v_close = calculate_factors(raw, raw["Close"].index[-1])
    bt_df    = run_backtest(raw)
    yc       = fetch_yield_curve()
    fred_mac = fetch_fred_macro()
    av_sec   = fetch_alpha_vantage_sector()
    cpi_val,cpi_per,cpi_yr = fetch_bls_cpi()
    news_feed = fetch_financial_news()
    fmp_calendar = fetch_fmp_macro_calendar()
    fmp_sector_pe = fetch_fmp_sector_pe()

closes = raw["Close"]
top5_df = df[df["RNK"]<=5]
top5_tickers = top5_df.index.tolist()

safe_e=["BIL","TLT","IEF","IAU","XLU","XLP"]
inf_e =["PDBC","XLE","XME","OIH","DBA","SLV","DBB"]
sc_cnt=sum(t in safe_e for t in top5_tickers)
ic_cnt=sum(t in inf_e  for t in top5_tickers)
if sc_cnt>=2:   regime,rc="RISK-OFF","#FFCC00"
elif ic_cnt>=2: regime,rc="INFLATIONARY","#FF8000"
else:           regime,rc="RISK-ON","#00CC00"

y2=fred_mac.get("2Y Yield"); y10=fred_mac.get("10Y Yield")
spread=(y10-y2) if (y2 and y10) else None
cs_lbl="INVERTED" if spread and spread<0 else "NORMAL"
cs_col="#CC0000" if cs_lbl=="INVERTED" else "#00CC00"

tnx_val=closes["^TNX"].dropna().iloc[-1] if "^TNX" in closes.columns else None
tyx_val=closes["^TYX"].dropna().iloc[-1] if "^TYX" in closes.columns else None
gc_val =closes["GC=F"].dropna().iloc[-1]  if "GC=F" in closes.columns else None
cl_val =closes["CL=F"].dropna().iloc[-1]  if "CL=F" in closes.columns else None
hy_val =fred_mac.get("HY Spread")
bei_val=fred_mac.get("10Y BEI")
eurusd =fred_mac.get("EUR/USD")
sent   =fred_mac.get("Cons Sent")
vix_col="#CC0000" if v_close>30 else "#FF8000" if v_close>20 else "#00CC00"

def mc(label, val, sub="", color="#FFFFFF", fmt="{:.2f}"):
    try:
        v = fmt.format(val) if (val is not None and not isinstance(val, str)) else (val if isinstance(val, str) else "N/A")
    except Exception:
        v = "N/A"
    return f'<div class="bbg-macro-cell"><div class="bbg-macro-lbl">{label}</div><div class="bbg-macro-val" style="color:{color};">{v}</div><div class="bbg-macro-sub">{sub}</div></div>'

# ── MACRO BAR — labelled assets ───────────────────────────────────────────────
macro_html = '<div class="bbg-macro-row">'
macro_html += mc("VIX INDEX", v_close, "CBOE Fear Index", vix_col)
macro_html += mc("10Y YIELD", tnx_val, "US Treasury Note", "#FF8000")
macro_html += mc("30Y YIELD", tyx_val, "US Treasury Bond", "#FF8000")
macro_html += mc("HY OAS", hy_val, "High Yield Spread bps", "#CC0000" if hy_val and hy_val>500 else "#FF8000" if hy_val and hy_val>350 else "#00CC00")
macro_html += mc("10Y BREAKEVEN", bei_val, "Inflation Expectation", "#FF8000")
macro_html += mc("GOLD FUTURES", gc_val, "$/oz  Comex GC=F", "#FFCC00", fmt="{:.0f}")
macro_html += mc("WTI CRUDE OIL", cl_val, "$/bbl  Nymex CL=F", "#FF8000", fmt="{:.2f}")
macro_html += mc("EUR/USD FX", eurusd, "Euro vs Dollar", "#FFFFFF")
macro_html += mc("UMICH SENT", sent, "Consumer Sentiment", "#00CC00" if sent and sent>80 else "#FF8000" if sent and sent>60 else "#CC0000")
cpi_sub = f"All Urban {cpi_per or chr(32)} {cpi_yr or chr(32)}"
macro_html += mc("BLS CPI", cpi_val, cpi_sub, "#FF8000")

if spread is not None:
    macro_html += f'''<div class="bbg-macro-cell"><div class="bbg-macro-lbl">2s10s SPREAD</div><div class="bbg-macro-val" style="color:{cs_col};">{spread:+.2f}%</div><div class="bbg-macro-sub">Yield Curve {cs_lbl}</div></div>'''
else:
    macro_html += mc("2s10s SPREAD","N/A","Yield Curve","#555")

macro_html += f'''<div class="bbg-macro-cell"><div class="bbg-macro-lbl">REGIME</div><div class="bbg-macro-val" style="color:{rc}; font-size:9px;">{regime}</div><div class="bbg-macro-sub">Capital Flow Signal</div></div>'''

yc_labels=["1M","3M","6M","1Y","2Y","5Y","10Y","30Y"]
yc_vals  =[yc.get(l) for l in yc_labels]
yc_valid =[(l,v) for l,v in zip(yc_labels,yc_vals) if v is not None]
macro_html += '<div class="bbg-macro-cell" style="padding-top:4px;"><div class="bbg-macro-lbl">YIELD CURVE</div>'
if yc_valid:
    mx_yc=max(v for _,v in yc_valid)
    macro_html += '<div class="yc-inline">'
    for lbl,val in yc_valid:
        bh=max(2,int((val/mx_yc)*22)) if mx_yc>0 else 2
        macro_html += f'''<div class="yc-inline-col"><div class="yc-inline-bar" style="height:{bh}px;"></div><div class="yc-inline-lbl">{lbl}</div></div>'''
    macro_html += '</div>'
else:
    macro_html += '<div style="color:#444;font-size:8px;padding-top:4px;">Loading...</div>'
macro_html += '</div></div>'
st.markdown(macro_html, unsafe_allow_html=True)

# ── TOP 5 + BLOOMBERG TV ──────────────────────────────────────────────────────
col_t5, col_tv = st.columns([3.8, 1.2])

with col_t5:
    cards = '<div class="bbg-top5-wrap"><div class="bbg-panel"><div class="bbg-panel-hdr">TOP 5 ROTATION TARGETS — SOLOMON STRATEGY</div><div class="bbg-top5">'
    for tkr,row in top5_df.iterrows():
        strong  = row["SIGNAL"]=="STRONG BUY"
        cclass  = "bbg-t5c strong" if strong else "bbg-t5c buy"
        sig_col = "#FF8000" if strong else "#FFCC00"
        sig_lbl = "◉ STRONG BUY" if strong else "◎ BUY"
        ytd_cls = "ytd-pos" if row["YTD"]>0 else "ytd-neg"
        aw      = min(row["ALLOC"]*5, 100)
        cards  += f'''<div class="{cclass}">
            <div class="bbg-t5-tkr">{tkr}</div>
            <div class="bbg-t5-sec">{row["SECTOR"]}</div>
            <div class="bbg-t5-price">${row["PRICE"]:.2f}</div>
            <div class="{ytd_cls}">YTD {row["YTD"]:+.1f}%</div>
            <div class="bbg-t5-sig" style="color:{sig_col};">{sig_lbl}</div>
            <div class="bbg-t5-alloc">ALLOC {row["ALLOC"]:.1f}%</div>
            <div class="bar-bg"><div class="bar-fill" style="width:{aw}%;background:{sig_col};"></div></div>
            <div class="bbg-t5-rsn">Score {row["SCORE"]:.1f} · ADX {row["ADX"]:.0f} · {row["REASON"]}</div>
        </div>'''
    cards += '</div></div></div>'
    st.markdown(cards, unsafe_allow_html=True)

with col_tv:
    st.markdown('<div class="bbg-tv-wrap"><div class="bbg-panel"><div class="bbg-panel-hdr">LIVE — BLOOMBERG TV</div>', unsafe_allow_html=True)
    components.html(
        '<iframe width="100%" height="160" src="https://www.youtube.com/embed/iEpJwprxDdk?autoplay=1&mute=1" frameborder="0" allowfullscreen style="display:block; margin-top:12px; margin-left:-8px; width:calc(100% + 16px);"></iframe>',
        height=165
    )
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs(["  CHART  ","  LEDGER  ","  HEATMAP  ","  BACKTEST  ","  NEWS & NOTES  ","  API STATUS  "])

# ── TAB 1: CHARTS ─────────────────────────────────────────────────────────────
with tab1:
    c1,c2=st.columns(2)
    with c1:
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">YTD — TOP 5 vs SPY</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        ytd_start=closes[closes.index.year==now_est.year]
        if not ytd_start.empty and top5_tickers:
            rows={}
            spy_s=closes["SPY"][closes.index>=ytd_start.index[0]].dropna()
            rows["SPY"]=((spy_s/spy_s.iloc[0])-1)*100
            for t in top5_tickers:
                if t in closes.columns:
                    s=closes[t][closes.index>=ytd_start.index[0]].dropna()
                    if not s.empty: rows[t]=((s/s.iloc[0])-1)*100
            cd=pd.DataFrame(rows).dropna()
            if not cd.empty: st.line_chart(cd,height=260,use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">6-MONTH ROLLING — TOP 5 vs SPY</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        six_mo=closes.index[-1]-pd.DateOffset(months=6)
        if top5_tickers:
            rows2={}
            for t in top5_tickers+["SPY"]:
                if t in closes.columns:
                    s=closes[t][closes.index>=six_mo].dropna()
                    if not s.empty: rows2[t]=((s/s.iloc[0])-1)*100
            rd=pd.DataFrame(rows2).dropna()
            if not rd.empty: st.line_chart(rd,height=260,use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
    if av_sec:
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">ALPHA VANTAGE — REAL-TIME SECTOR PERFORMANCE</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        av_html='<table class="bbg-tbl"><thead><tr><th class="l">SECTOR</th><th>PERFORMANCE</th></tr></thead><tbody>'
        for sec,perf in av_sec.items():
            try:
                val=float(perf.replace("%",""))
                c_=("#00CC00" if val>0 else "#CC0000")
                av_html+=f'<tr><td class="l">{sec}</td><td style="color:{c_};">{perf}</td></tr>'
            except:
                av_html+=f'<tr><td class="l">{sec}</td><td>{perf}</td></tr>'
        av_html+='</tbody></table>'
        st.markdown(av_html+'</div></div>', unsafe_allow_html=True)

# ── TAB 2: LEDGER ─────────────────────────────────────────────────────────────
with tab2:
    def sc_cls(s):
        if "STRONG BUY" in s: return "sig-sb"
        if "BUY"        in s: return "sig-b"
        if "HOLD"       in s: return "sig-h"
        if "HALT"       in s: return "sig-ht"
        if "STRONG SELL"in s: return "sig-ss"
        return "sig-s"
    hdrs=["RNK","TKR","SECTOR","SIGNAL","REASON","ALLOC","PRICE","STOP","ADX","SCORE","YTD","1M%","3M%","6M%","9M%","RAM","VOL_CF"]
    tbl='<div class="bbg-panel"><div class="bbg-panel-hdr">SOLOMON STRATEGY — QUANTITATIVE LEDGER — ALL 46 ASSETS</div>'
    tbl+='<div class="bbg-scroll"><table class="bbg-tbl"><thead><tr>'
    for h in hdrs:
        al="l" if h in ["TKR","SECTOR","SIGNAL","REASON"] else ""
        tbl+=f'<th class="{al}">{h}</th>'
    tbl+='</tr></thead><tbody>'
    for tkr,row in df.iterrows():
        c_=sc_cls(row["SIGNAL"])
        yc_=("#00CC00" if row["YTD"]>0 else "#CC0000")
        al_=f'{row["ALLOC"]:.1f}%' if row["ALLOC"]>0 else "—"
        tbl+=f'''<tr>
            <td>{row["RNK"]}</td><td class="l">{tkr}</td><td class="sec">{row["SECTOR"]}</td>
            <td class="l {c_}">{row["SIGNAL"]}</td>
            <td class="l" style="color:#444;font-size:9px;">{row["REASON"]}</td>
            <td style="color:#FF8000;">{al_}</td>
            <td>{row["PRICE"]:.2f}</td><td style="color:#CC0000;">{row["STOP"]:.2f}</td>
            <td>{row["ADX"]:.1f}</td><td style="color:#FF8000;">{row["SCORE"]:.1f}</td>
            <td style="color:{yc_};">{row["YTD"]:.1f}%</td>
            <td>{row["RET_1M"]:.1f}%</td><td>{row["RET_3M"]:.1f}%</td>
            <td>{row["RET_6M"]:.1f}%</td><td>{row["RET_9M"]:.1f}%</td>
            <td>{row["RAM"]:.2f}</td><td>{row["VOL_CF"]:.2f}</td>
        </tr>'''
    tbl+='</tbody></table></div></div>'
    st.markdown(tbl, unsafe_allow_html=True)

# ── TAB 3: HEATMAP ────────────────────────────────────────────────────────────
with tab3:
    h1,h2=st.columns(2)
    with h1:
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">YTD PERFORMANCE</div><div class="bbg-hm">', unsafe_allow_html=True)
        hm=""
        for tkr,row in df.sort_values("YTD",ascending=False).iterrows():
            v=row["YTD"]
            if v>20:    bg,fg="#004400","#00FF00"
            elif v>10:  bg,fg="#003300","#00CC00"
            elif v>0:   bg,fg="#001A00","#009900"
            elif v>-10: bg,fg="#1A0000","#CC3333"
            else:       bg,fg="#2A0000","#FF4444"
            bdr="border:1px solid #FF8000;" if "BUY" in row["SIGNAL"] else "border:1px solid #1A1A1A;"
            hm+=f'<div class="bbg-hm-cell" style="background:{bg};color:{fg};{bdr}"><span>{tkr}</span><span>{v:+.1f}%</span></div>'
        st.markdown(hm+'</div></div>', unsafe_allow_html=True)
    with h2:
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">MOMENTUM SCORE</div><div class="bbg-hm">', unsafe_allow_html=True)
        hm2=""
        mx_=df["SCORE"].max(); mn_=df["SCORE"].min()
        for tkr,row in df.sort_values("SCORE",ascending=False).iterrows():
            s=row["SCORE"]
            n=(s-mn_)/(mx_-mn_) if mx_!=mn_ else 0.5
            bg=f"rgb(0,{int(n*160)+20},0)" if n>0.5 else f"rgb({int((1-n)*130)},20,0)"
            fg="#FF8000" if n>0.7 else "#FFCC00" if n>0.4 else "#CC3333"
            bdr="border:1px solid #FF8000;" if "BUY" in row["SIGNAL"] else "border:1px solid #1A1A1A;"
            hm2+=f'<div class="bbg-hm-cell" style="background:{bg};color:{fg};{bdr}"><span>{tkr}</span><span>{s:.0f}</span></div>'
        st.markdown(hm2+'</div></div>', unsafe_allow_html=True)

# ── TAB 4: BACKTEST ───────────────────────────────────────────────────────────
with tab4:
    bc1,bc2,bc3=st.columns([1.3,1.7,1.0])
    with bc1:
        tbl2='<div class="bbg-panel"><div class="bbg-panel-hdr">MONTH-BY-MONTH (9M LOOKBACK)</div>'
        tbl2+='<div class="bbg-scroll"><table class="bbg-tbl"><thead><tr>'
        tbl2+='<th class="l">MONTH</th><th class="l">TARGETS</th><th>STRAT</th><th>SPY</th><th>ALPHA</th>'
        tbl2+='</tr></thead><tbody>'
        for _,r in bt_df.iterrows():
            sc_=("#00CC00" if r["Strategy"]>0 else "#CC0000")
            ac_=("#00CC00" if r["Alpha"]>0    else "#CC0000")
            tbl2+=f'<tr><td class="l">{r["Month"]}</td><td class="l" style="color:#666;font-size:9px;">{r["Targets"]}</td><td style="color:{sc_};">{r["Strategy"]:.1f}%</td><td style="color:#555;">{r["SPY"]:.1f}%</td><td style="color:{ac_};font-weight:700;">{r["Alpha"]:+.1f}%</td></tr>'
        tbl2+='</tbody></table></div></div>'
        st.markdown(tbl2, unsafe_allow_html=True)

        # ── CRITERIA LEGEND ─────────────────────────────────────────────────
        leg='<div class="bbg-panel" style="margin-top:4px;"><div class="bbg-panel-hdr">SOLOMON SIGNAL CRITERIA</div><div class="bbg-panel-body">'
        leg+='<table class="bbg-tbl"><thead><tr><th class="l">SIGNAL</th><th class="l">CRITERIA</th><th>ALLOC</th></tr></thead><tbody>'
        criteria=[
            ("STRONG BUY","Top 5 rank + ALL 7 criteria pass","Up to 20%","#FF8000"),
            ("BUY (strong)","Top 5 rank + 1-2 criteria fail","Up to 12%","#FFCC00"),
            ("BUY (weak)","Top 5 rank + 3+ criteria fail","Up to 6%","#FFAA00"),
            ("HOLD","Rank 6-10, all criteria pass","Watch only","#888"),
            ("SELL","Outside top 10 or criteria failed","Exit","#CC3333"),
            ("STRONG SELL","Below 200MA or hit ATR stop","Exit now","#FF0000"),
            ("HALT","VIX > 30","All cash","#FF00FF"),
        ]
        for sig,crit,alloc,col in criteria:
            leg+=f'<tr><td class="l" style="color:{col};font-weight:700;">{sig}</td><td class="l" style="color:#555;font-size:9px;">{crit}</td><td style="color:#FF8000;">{alloc}</td></tr>'
        leg+='</tbody></table></div></div>'
        st.markdown(leg, unsafe_allow_html=True)

    with bc2:
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">STRATEGY vs SPY — MONTHLY RETURNS</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        if not bt_df.empty:
            # Sort by calendar month order, not alphabetical
            bt_sorted = bt_df.copy()
            bt_sorted.index = range(len(bt_sorted))
            chart_data = bt_sorted.set_index("Month")[["Strategy","SPY"]]
            st.bar_chart(chart_data, height=220, use_container_width=True, color=["#FF8000","#444444"])
        st.markdown('</div></div>', unsafe_allow_html=True)

        # ── CUMULATIVE CURVE ────────────────────────────────────────────────
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">CUMULATIVE RETURNS</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        if not bt_df.empty:
            bt_cum=bt_df.copy()
            bt_cum["Strat Cumul"]=(1+bt_cum["Strategy"]/100).cumprod()*100-100
            bt_cum["SPY Cumul"]  =(1+bt_cum["SPY"]/100).cumprod()*100-100
            st.line_chart(bt_cum.set_index("Month")[["Strat Cumul","SPY Cumul"]], height=160, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    with bc3:
        # ── SUMMARY STATS ───────────────────────────────────────────────────
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">SUMMARY STATS</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        if not bt_df.empty:
            ts =bt_df["Strategy"].sum(); tsp=bt_df["SPY"].sum(); ta=bt_df["Alpha"].sum()
            wr =(bt_df["Strategy"]>bt_df["SPY"]).mean()*100
            pm =(bt_df["Strategy"]>0).sum()
            max_dd_strat=bt_df["Strategy"].min(); max_dd_spy=bt_df["SPY"].min()
            best_mo=bt_df.loc[bt_df["Strategy"].idxmax(),"Month"]
            best_rt=bt_df["Strategy"].max()
            worst_mo=bt_df.loc[bt_df["Strategy"].idxmin(),"Month"]
            worst_rt=bt_df["Strategy"].min()
            st.markdown(f'''<table class="bbg-tbl">
                <tr><td class="l">Strat Return</td><td style="color:#FF8000;">{ts:.1f}%</td></tr>
                <tr><td class="l">SPY Return</td>  <td style="color:#555;">{tsp:.1f}%</td></tr>
                <tr><td class="l">Total Alpha</td> <td style="color:#00CC00;">{ta:+.1f}%</td></tr>
                <tr><td class="l">Win Rate vs SPY</td><td style="color:#FF8000;">{wr:.0f}%</td></tr>
                <tr><td class="l">Positive Months</td><td>{pm}/{len(bt_df)}</td></tr>
                <tr><td class="l">Avg Alpha / Mo</td><td style="color:#00CC00;">{ta/len(bt_df):+.1f}%</td></tr>
                <tr><td class="l">Best Month</td>  <td style="color:#00CC00;">{best_mo} {best_rt:+.1f}%</td></tr>
                <tr><td class="l">Worst Month</td> <td style="color:#CC0000;">{worst_mo} {worst_rt:+.1f}%</td></tr>
                <tr><td class="l">Worst Strat Mo</td><td style="color:#CC0000;">{max_dd_strat:.1f}%</td></tr>
                <tr><td class="l">Worst SPY Mo</td><td style="color:#CC0000;">{max_dd_spy:.1f}%</td></tr>
            </table>''', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        # ── CURRENT ALLOCATION ──────────────────────────────────────────────
        st.markdown('<div class="bbg-panel" style="margin-top:4px;"><div class="bbg-panel-hdr">CURRENT ALLOCATION</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        alloc_html='<table class="bbg-tbl"><thead><tr><th class="l">ASSET</th><th class="l">SIGNAL</th><th>ALLOC</th></tr></thead><tbody>'
        for tkr,row in top5_df.iterrows():
            sig_col="#FF8000" if row["SIGNAL"]=="STRONG BUY" else "#FFCC00"
            alloc_html+=f'<tr><td class="l">{tkr}</td><td class="l" style="color:{sig_col};font-size:9px;">{row["SIGNAL"]}</td><td style="color:#FF8000;">{row["ALLOC"]:.1f}%</td></tr>'
        total_alloc=top5_df["ALLOC"].sum()
        cash_alloc=max(0, 100-total_alloc)
        alloc_html+=f'<tr><td class="l" style="color:#888;">CASH/BIL</td><td class="l" style="color:#888;font-size:9px;">Buffer</td><td style="color:#888;">{cash_alloc:.1f}%</td></tr>'
        alloc_html+=f'<tr style="border-top:1px solid #FF8000;"><td class="l" style="color:#FF8000;font-weight:700;">TOTAL</td><td></td><td style="color:#FF8000;font-weight:700;">100.0%</td></tr>'
        alloc_html+='</tbody></table>'
        st.markdown(alloc_html+'</div></div>', unsafe_allow_html=True)

        # ── FMP ECONOMIC CALENDAR ────────────────────────────────────────────
        st.markdown('<div class="bbg-panel" style="margin-top:4px;"><div class="bbg-panel-hdr">FMP — UPCOMING ECONOMIC EVENTS</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        if fmp_calendar:
            cal_html='<table class="bbg-tbl"><thead><tr><th class="l">DATE</th><th class="l">EVENT</th><th>ACTUAL</th><th>EST</th><th>IMPACT</th></tr></thead><tbody>'
            for ev in fmp_calendar[:10]:
                date_s = ev.get("date","")[:10]
                event  = ev.get("event","")[:35]
                actual = ev.get("actual","—") or "—"
                est    = ev.get("estimate","—") or "—"
                impact = ev.get("impact","")
                imp_col= "#CC0000" if impact=="High" else "#FF8000" if impact=="Medium" else "#555"
                cal_html+=f'<tr><td class="l" style="color:#555;font-size:9px;">{date_s}</td><td class="l">{event}</td><td>{actual}</td><td style="color:#888;">{est}</td><td style="color:{imp_col};font-size:9px;">{impact}</td></tr>'
            cal_html+='</tbody></table>'
            st.markdown(cal_html+'</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#555;font-size:9px;">No upcoming events or FMP calendar loading...</div></div></div>', unsafe_allow_html=True)

# ── TAB 5: NEWS & NOTES ───────────────────────────────────────────────────────
with tab5:
    n1,n2=st.columns([2.2,1.8])
    # Force both columns to equal height
    st.markdown('<style>[data-testid="stHorizontalBlock"]{align-items:stretch;} [data-testid="stTextArea"]{height:100%;} [data-testid="stTextArea"] textarea{height:100% !important; min-height:500px;}</style>', unsafe_allow_html=True)
    with n1:
        st.markdown('<div class="bbg-panel"><div class="bbg-panel-hdr">FINANCIAL NEWS — ALPHA VANTAGE SENTIMENT FEED</div>', unsafe_allow_html=True)
        if news_feed:
            news_html='<div class="bbg-scroll"><table class="bbg-tbl"><thead><tr><th class="l">HEADLINE</th><th class="l">SOURCE</th><th>SENTIMENT</th><th class="l">TIME</th></tr></thead><tbody>'
            for item in news_feed:
                title  =item.get("title","")[:80]
                source =item.get("source","")
                time_p =item.get("time_published","")[:12]
                overall_score=item.get("overall_sentiment_score",0)
                overall_label=item.get("overall_sentiment_label","Neutral")
                sc_col="#00CC00" if "Bullish" in overall_label else "#CC0000" if "Bearish" in overall_label else "#888"
                news_html+=f'<tr><td class="l" style="white-space:normal; max-width:400px; word-wrap:break-word;">{title}</td><td class="l" style="color:#555;font-size:9px;white-space:nowrap;">{source}</td><td style="color:{sc_col};font-size:9px;white-space:nowrap;">{overall_label}</td><td class="l" style="color:#444;font-size:9px;white-space:nowrap;">{time_p}</td></tr>'
            news_html+='</tbody></table></div>'
        else:
            news_html='<div style="padding:16px; color:#555; font-size:10px;">News feed requires Alpha Vantage premium plan for NEWS_SENTIMENT endpoint.<br><br>Alternative: Add NewsAPI.org key (free tier available) for live financial headlines.</div>'
        st.markdown(news_html+'</div>', unsafe_allow_html=True)

    with n2:
        st.markdown('<div class="bbg-panel" style="margin-top:0px;"><div class="bbg-panel-hdr">ANALYST NOTES — TRADE JOURNAL</div><div class="bbg-panel-body">', unsafe_allow_html=True)
        st.markdown('<div style="color:#555;font-size:9px;margin-bottom:4px;letter-spacing:1px;">TYPE YOUR NOTES BELOW — USE FOR TRADE RATIONALE, OBSERVATIONS, REMINDERS</div>', unsafe_allow_html=True)
        st.text_area(
            label="",
            placeholder="e.g.\n- OIH: Energy capex cycle looks strong. Hold through earnings.\n- Monitor 10Y yield — if breaks 4.8% rotate defensive.\n- FBTC halving cycle Q2 2025 setup. Scale in on dips.\n- Review positions end of month vs SMA filter.",
            height=500,
            label_visibility="collapsed",
            key="trade_notes"
        )
        st.markdown('</div></div>', unsafe_allow_html=True)

# ── TAB 6: API STATUS ─────────────────────────────────────────────────────────
with tab6:
    fred_ok=any(v is not None for v in fred_mac.values())
    av_ok  =bool(av_sec)
    bls_ok =cpi_val is not None
    apis=[
        ("FRED — St. Louis Fed",      "Treasury yields, inflation, HY spread, EUR/USD, CPI, unemployment",fred_ok,"Key active — fred.stlouisfed.org"),
        ("Yahoo Finance (yfinance)",   "All 46 ETF prices, OHLCV, benchmarks, gold/oil futures",          True,  "Active — no key required"),
        ("Alpha Vantage",              "Sector performance, news sentiment, fundamentals",                  av_ok, "Key active — premium plan needed for news"),
        ("BLS — Bureau of Labor Stats","CPI index, PPI, unemployment series",                              bls_ok,"Public API — bls.gov"),
        ("Nasdaq Data Link",           "COT reports, futures positioning, alternative data",               False, "Register at data.nasdaq.com"),
        ("CFTC",                       "Commitment of Traders — futures net positioning",                  False, "Free CSV — cftc.gov/MarketReports"),
        ("SEC EDGAR",                  "ETF 13F filings, institutional ownership flow",                    False, "Free REST — efts.sec.gov"),
        ("Financial Modeling Prep",    "Economic calendar, sector P/E, market hours, dividends",           bool(fmp_calendar or fmp_sector_pe), "Key active — financialmodelingprep.com"),
    ]
    tbl3='<div class="bbg-panel"><div class="bbg-panel-hdr">API CONNECTION STATUS</div>'
    tbl3+='<table class="bbg-tbl"><thead><tr><th class="l">API</th><th class="l">DATA</th><th>STATUS</th><th class="l">NOTES</th></tr></thead><tbody>'
    for name,desc,ok,how in apis:
        sc_=("#00CC00" if ok else "#CC0000"); stxt=("● LIVE" if ok else "○ OFFLINE")
        tbl3+=f'<tr><td class="l" style="color:#FF8000;">{name}</td><td class="l" style="color:#555;font-size:9px;">{desc}</td><td style="color:{sc_};font-size:9px;">{stxt}</td><td class="l" style="color:#444;font-size:9px;">{how}</td></tr>'
    tbl3+='</tbody></table>'
    tbl3+='<div class="bbg-panel-hdr" style="margin-top:8px;border-top:1px solid #333;">FRED LIVE VALUES</div>'
    tbl3+='<table class="bbg-tbl"><thead><tr><th class="l">SERIES</th><th>VALUE</th><th>STATUS</th></tr></thead><tbody>'
    for lbl,val in fred_mac.items():
        ok2=(val is not None); sc2=("#00CC00" if ok2 else "#444"); fmt=(f"{val:.3f}" if ok2 else "—")
        tbl3+=f'<tr><td class="l">{lbl}</td><td style="color:#FF8000;">{fmt}</td><td style="color:{sc2};font-size:9px;">{"● LIVE" if ok2 else "○ N/A"}</td></tr>'
    tbl3+='</tbody></table></div>'
    st.markdown(tbl3, unsafe_allow_html=True)

# ── TICKER TAPE ───────────────────────────────────────────────────────────────
tape_syms=["SPY","QQQ","DIA","^VIX","^TNX","GC=F","CL=F"]
tape='<div class="bbg-tape">'
for sym in tape_syms:
    try:
        col_=closes[sym].dropna(); cur,prv=col_.iloc[-1],col_.iloc[-2]
        pct=((cur-prv)/prv)*100; pc=("tape-up" if pct>=0 else "tape-dn")
        lbl=sym.replace("^","").replace("=F","")
        tape+=f'<span><span class="tape-sym">{lbl}</span> <span class="tape-prc">{cur:.2f}</span> <span class="{pc}">{pct:+.2f}%</span></span>'
    except: pass
tape+='</div>'
st.markdown(tape, unsafe_allow_html=True)
