import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="Quant Terminal", layout="wide", initial_sidebar_state="collapsed")

est_zone = ZoneInfo('America/New_York')
now_est = datetime.datetime.now(est_zone)
time_str = now_est.strftime("%I:%M %p ET")
date_str = now_est.strftime("%b %d, %Y").upper()

is_weekend = now_est.weekday() >= 5
is_open_hours = datetime.time(9, 30) <= now_est.time() <= datetime.time(16, 0)
market_status = "MARKET CLOSED" if is_weekend or not is_open_hours else "MARKET OPEN"
status_color = "#00FF00" if market_status == "MARKET OPEN" else "#FF0000"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; }}
    * {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; color: #E0E0E0; letter-spacing: 0.2px; }}
    .status-bar {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #FF6600; padding: 8px 15px; margin-top: -50px; margin-bottom: 15px; background: #000000; }}
    .status-left {{ color: {status_color}; font-weight: 900; font-size: 14px; text-transform: uppercase; }}
    .status-right {{ color: #FF6600; text-align: right; font-weight: bold; font-size: 14px; }}
    .bbg-panel {{ border: 1px solid #333; background-color: #0A0A0A; padding: 12px; margin-bottom: 15px; border-radius: 4px; box-shadow: 0 4px 10px rgba(0,0,0,0.8); }}
    .bbg-header {{ color: #FF6600; font-weight: 900; font-size: 13px; text-transform: uppercase; border-bottom: 1px solid #333; padding-bottom: 6px; margin-bottom: 10px; letter-spacing: 1px; }}
    .ledger-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #333; background: #000; margin-bottom: 15px; }}
    .ledger-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    .ledger-table th {{ position: sticky; top: 0; background-color: #111; color: #FF6600; z-index: 10; border-bottom: 2px solid #FF6600; padding: 8px; text-align: left; }}
    .ledger-table td {{ padding: 8px; border-bottom: 1px solid #222; text-align: left; font-family: monospace; font-size: 12px; }}
    .ledger-table td.num {{ text-align: right; }}
    .ledger-table tr:hover {{ background-color: #1A1A1A; }}
    .heatmap-grid {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 2px; }}
    .heat-cell {{ text-align: center; padding: 8px 0px; font-size: 10px; font-weight: 900; color: #000; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
    <div class="status-bar">
        <div class="status-left">● {market_status} | SYS.OP.NORMAL</div>
        <div class="status-right">{time_str} | <span style="font-size:10px; color:#888;">{date_str}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SECTOR-MAPPED UNIVERSE (46 ASSETS)
# ==========================================
TICKER_SECTORS = {
    "OIH": "Energy", "XLE": "Energy", "XLB": "Materials", "XME": "Materials", "WOOD": "Materials",
    "XLI": "Industrials", "IYT": "Industrials", "CARZ": "Cons Disc", "XLY": "Cons Disc", "PEJ": "Cons Disc",
    "XRT": "Cons Disc", "XLP": "Cons Staples", "PBJ": "Cons Staples", "IHI": "Health Care", "XBI": "Health Care",
    "KBE": "Financials", "IAI": "Financials", "KIE": "Financials", "IGV": "Info Tech", "SMH": "Info Tech",
    "IYZ": "Comm Services", "XLC": "Comm Services", "XLU": "Utilities", "FCG": "Utilities", "IDU": "Utilities",
    "PHO": "Utilities", "ICLN": "Utilities", "VNQ": "Real Estate", "REET": "Real Estate", "EFA": "Global Overlay",
    "VWO": "Global Overlay", "INDY": "Global Overlay", "KWEB": "Global Overlay", "DBA": "Uncorrelated",
    "PDBC": "Uncorrelated", "UUP": "Uncorrelated", "VIXY": "Uncorrelated", "SLV": "Uncorrelated", "TIP": "Uncorrelated",
    "DBB": "Uncorrelated", "CWB": "Uncorrelated", "IAU": "Macro", "FBTC": "Macro", "BIL": "Safe Harbor",
    "IEF": "Safe Harbor", "TLT": "Safe Harbor"
}
TICKERS = list(TICKER_SECTORS.keys())
BENCHMARKS = ["SPY", "^VIX"]

# ==========================================
# 3. CORE DATA ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data():
    return yf.download(TICKERS + BENCHMARKS, period="2y", progress=False)

def calculate_snapshot(data, target_date):
    closes = data['Close'].loc[:target_date]
    highs = data['High'].loc[:target_date]
    lows = data['Low'].loc[:target_date]
    vols = data['Volume'].loc[:target_date]
    if len(closes) < 200: return pd.DataFrame(), False, 0.0
    
    spy_p = closes["SPY"].dropna()
    vix_close = closes["^VIX"].dropna().iloc[-1]
    vix_halt = vix_close > 30 
    
    results = []
    for t in TICKERS:
        try:
            p, h, l, v = closes[t].dropna(), highs[t].dropna(), lows[t].dropna(), vols[t].dropna()
            if len(p) < 200: continue
            
            # FACTOR MATH
            ret_1m = p.pct_change(21).iloc[-1]
            vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram = ret_1m / vol_1m if vol_1m != 0 else 0
            roc_20 = p.pct_change(20).iloc[-1]
            roc_60 = p.pct_change(60).iloc[-1]
            roc_accel = roc_20 - (roc_60 / 3)
            rel_str = p.pct_change(63).iloc[-1] - spy_p.pct_change(63).iloc[-1]
            sma_50 = p.rolling(50).mean()
            sma_50_slp = (sma_50.iloc[-1] - sma_50.iloc[-21]) / sma_50.iloc[-21]
            vol_cf = (v.rolling(20).mean().iloc[-1] / v.rolling(90).mean().iloc[-1])
            atr = (h - l).rolling(14).mean().iloc[-1]
            stop = p.tail(20).max() - (2.5 * atr)
            alloc = (0.01 / ((p.iloc[-1] - stop) / p.iloc[-1])) * 100 if p.iloc[-1] > stop else 0
            
            # ADX Math
            tr = pd.concat([h-l, np.abs(h-p.shift()), np.abs(l-p.shift())], axis=1).max(axis=1)
            up, dw = h-h.shift(1), l.shift(1)-l
            pd_di = 100 * (pd.Series(np.where((up>dw)&(up>0),up,0), index=p.index).rolling(14).sum() / tr.rolling(14).sum())
            md_di = 100 * (pd.Series(np.where((dw>up)&(dw>0),dw,0), index=p.index).rolling(14).sum() / tr.rolling(14).sum())
            adx = (100 * np.abs(pd_di - md_di) / (pd_di + md_di)).rolling(14).mean().iloc[-1]

            results.append({
                'TKR': t, 'SECTOR': TICKER_SECTORS[t], 'PRICE': p.iloc[-1], 'YTD': ((p.iloc[-1]/p[p.index.year==target_date.year].iloc[0])-1)*100 if not p[p.index.year==target_date.year].empty else 0,
                'RAM': ram, 'REL_STR': rel_str, '50D_SLP': sma_50_slp, 'VOL_CF': vol_cf, 'ROC_AC': roc_accel,
                'ADX': adx, 'STOP': stop, 'ALLOC': min(alloc, 25.0), 'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
            })
        except: continue
            
    df = pd.DataFrame(results).set_index('TKR')
    f = ['RAM', 'REL_STR', '50D_SLP', 'VOL_CF', 'ROC_AC']
    z = (df[f] - df[f].mean()) / df[f].std()
    df['SCORE'] = (z['RAM']*.25 + z['REL_STR']*.2 + z['50D_SLP']*.2 + z['VOL_CF']*.2 + z['ROC_AC']*.15) * 100
    df = df.sort_values('SCORE', ascending=False)
    df['RNK'] = range(1, len(df) + 1)
    
    sig, res = [], []
    for _, row in df.iterrows():
        r = ""
        if not row['Above_200']: r = "Below 200DMA"
        elif row['ADX'] <= 25: r = f"Choppy({row['ADX']:.1f})"
        elif row['VOL_CF'] < 1.1: r = "Low Vol"
        
        if vix_halt: sig.append("HALT"); res.append("VIX>30")
        elif r == "" and row['RNK'] <= 5: sig.append("STRONG BUY"); res.append("PASSED")
        elif r == "" and row['RNK'] <= 10: sig.append("HOLD"); res.append("Buffer")
        else: sig.append("SELL"); res.append(r if r else f"Rank #{row['RNK']}")
            
    df['SIGNAL'], df['REASON'] = sig, res
    return df, vix_halt, vix_close

@st.cache_data(ttl=3600)
def run_bt(data):
    m = data['Close'].resample('ME').last(); d = m.index[-13:-1]; log = []
    for i in range(len(d)-1):
        s, e = d[i], d[i+1]; snap, _, _ = calculate_snapshot(data, s)
        buys = snap[snap['SIGNAL'] == 'STRONG BUY'].head(5).index.tolist()
        ret = ((data['Close'].loc[e, buys].mean() / data['Close'].loc[s, buys].mean()) - 1) * 100 if buys else 0
        log.append({"Month": s.strftime('%y-%b'), "Targets": ", ".join(buys) if buys else "CASH", "Return": ret})
    return pd.DataFrame(log)

# --- EXECUTION ---
raw = fetch_data(); df, v_h, v_c = calculate_snapshot(raw, raw.index[-1]); bt_df = run_bt(raw)

# --- UI ---
c1, c2 = st.columns([1.2, 1.8])
with c1:
    v_col = "red" if v_h else "#00FF00"
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">ARCHITECTURE</div><table><tr><td>VIX</td><td style="text-align:right; color:{v_col};">{v_c:.2f}</td></tr></table></div>', unsafe_allow_html=True)
    top5 = df.head(5).index.tolist(); reg, rc = ("RISK-OFF", "#FBBF24") if any(x in top5 for x in ["BIL", "TLT", "IAU"]) else ("RISK-ON", "#00FF00")
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">REGIME</div><div style="text-align:center; font-weight:bold; color:{rc};">{reg}</div></div>', unsafe_allow_html=True)

with c2:
    s1, s2 = st.columns(2)
    with s1:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">YTD EQUITY VS SPY</div>', unsafe_allow_html=True)
        spy_y = (raw['Close']['SPY'] / raw['Close']['SPY'][raw['Close'].index.year == now_est.year][0] - 1) * 100
        st.line_chart(spy_y.tail(60), height=205)
        st.markdown('</div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">BLOOMBERG TV</div>', unsafe_allow_html=True)
        components.html('<iframe width="100%" height="205" src="https://www.youtube.com/embed/iEpJwprxDdk?autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>', height=210)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="bbg-panel"><div class="bbg-header">HEATMAP</div><div class="heatmap-grid">' + "".join([f'<div class="heat-cell" style="background-color:{"#00FF00" if r["YTD"]>0 else "#FF0000"};">{t}</div>' for t, r in df.sort_values("YTD", ascending=False).iterrows()]) + '</div></div>', unsafe_allow_html=True)

# --- LEDGER ---
st.markdown('<div class="bbg-panel"><div class="bbg-header">LEDGER</div><div class="ledger-container"><table class="ledger-table"><thead><tr><th>RNK</th><th>TKR</th><th>SECTOR</th><th>SIGNAL</th><th>REASON</th><th>ALLOC</th><th>PRICE</th><th>STOP</th><th>ADX</th><th>SCORE</th><th>YTD</th><th>RAM</th><th>VOL_CF</th></tr></thead><tbody>' + 
            "".join([f'<tr><td>{r["RNK"]}</td><td style="color:#FF6600; font-weight:bold;">{t}</td><td style="color:#888;">{r["SECTOR"]}</td><td style="color:{"#00FF00" if "BUY" in r["SIGNAL"] else "#FF0000"}; font-weight:bold;">{r["SIGNAL"]}</td><td>{r["REASON"]}</td><td class="num">{r["ALLOC"]:.1f}%</td><td class="num">{r["PRICE"]:.2f}</td><td class="num">{r["STOP"]:.2f}</td><td class="num">{r["ADX"]:.1f}</td><td class="num">{r["SCORE"]:.1f}</td><td class="num">{r["YTD"]:.1f}%</td><td class="num">{r["RAM"]:.2f}</td><td class="num">{r["VOL_CF"]:.2f}</td></tr>' for t, r in df.iterrows()]) + '</tbody></table></div></div>', unsafe_allow_html=True)

# --- BT ---
st.markdown('<div class="bbg-panel"><div class="bbg-header">BACKTEST</div>', unsafe_allow_html=True)
bc1, bc2 = st.columns(2)
with bc1:
    st.markdown('<div class="ledger-container" style="max-height:250px;"><table class="ledger-table"><thead><tr><th>MONTH</th><th>TARGETS</th><th>RET</th></tr></thead><tbody>' + "".join([f'<tr><td>{r["Month"]}</td><td style="color:#00FFFF;">{r["Targets"]}</td><td style="color:{"#00FF00" if r["Return"]>0 else "#FF0000"};">{r["Return"]:.1f}%</td></tr>' for _, r in bt_df.iterrows()]) + '</tbody></table></div>', unsafe_allow_html=True)
with bc2: st.bar_chart(bt_df.set_index("Month")["Return"], color="#FF6600", height=250)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 4. INTERFACE LAYOUT
# ==========================================
col1, col2 = st.columns([1.2, 1.8]) 

with col1:
    v_color = "red" if vix_halt else "#00FF00"
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">SYSTEM ARCHITECTURE</div><table><tr><td>Macro Regime (VIX)</td><td class="td-right" style="color:{v_color};">{vix_close:.2f}</td></tr></table></div>', unsafe_allow_html=True)
    st.markdown('<div class="bbg-panel"><div class="bbg-header">ELITE ENTRY / EXIT</div><table><tr><td class="c-strong-buy">STRONG BUY</td><td>Perfect Alignment (Top 5)</td></tr><tr><td class="c-buy">BUY</td><td>Top 5, imperfect setup</td></tr><tr><td class="c-hold">HOLD</td><td>Buffer zone (Rank 6-10)</td></tr></table></div>', unsafe_allow_html=True)
    
    top_5 = df.head(5).index.tolist()
    safe_harbor = ["BIL", "TLT", "IEF", "IAU"]
    regime, r_color = ("RISK-OFF (DEFENSIVE)", "#FBBF24") if any(x in top_5 for x in safe_harbor) else ("RISK-ON (GROWTH)", "#00FF00")
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">REGIME ROTATION RADAR</div><div style="text-align:center; padding: 10px 0;"><span style="font-size:16px; font-weight:bold; color:{r_color};">{regime}</span></div></div>', unsafe_allow_html=True)

with col2:
    sub1, sub2 = st.columns(2)
    with sub1:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">YTD EQUITY CURVE VS SPY</div>', unsafe_allow_html=True)
        spy_c = (c['SPY'] / c['SPY'][c.index.year == now_est.year][0] - 1) * 100
        st.line_chart(spy_c.tail(60), height=205)
        st.markdown('</div>', unsafe_allow_html=True)
    with sub2:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">LIVE MACRO: BLOOMBERG TV</div>', unsafe_allow_html=True)
        components.html('<iframe width="100%" height="205" src="https://www.youtube.com/embed/iEpJwprxDdk?autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>', height=210)
        st.markdown('</div>', unsafe_allow_html=True)

    # 4F. THE HEATMAP (ALL 46 ASSETS)
    st.markdown('<div class="bbg-panel"><div class="bbg-header">ETF YTD PERFORMANCE HEATMAP</div>', unsafe_allow_html=True)
    heat_df = df.sort_values('YTD', ascending=False)
    heatmap_html = '<div class="heatmap-grid">'
    for ticker, row in heat_df.iterrows():
        val = row['YTD']
        color = "#00FF00" if val > 15 else "#006600" if val > 0 else "#660000" if val > -10 else "#FF0000"
        heatmap_html += f'<div class="heat-cell" style="background-color:{color}; color:{"#000" if color=="#00FF00" else "#FFF"};">{ticker}<br>{val:.1f}%</div>'
    st.markdown(heatmap_html + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 5. CUSTOM HTML LEDGER (RANK, TKR, SECTOR)
# ==========================================
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)
ledger_html = '<div class="ledger-container"><table class="ledger-table"><thead><tr><th>RNK</th><th>TKR</th><th>SECTOR</th><th>SIGNAL</th><th>REASON</th><th>PRICE</th><th>YTD</th><th>SCORE</th></tr></thead><tbody>'
for tkr, row in df.iterrows():
    sig = row['SIGNAL']
    s_col = '#00FF00' if 'BUY' in sig else '#FBBF24' if 'HOLD' in sig else '#FF0000'
    ledger_html += f'<tr><td>{row["RNK"]}</td><td style="font-weight:bold; color:#FF6600;">{tkr}</td><td style="color:#888;">{row["SECTOR"]}</td><td style="color:{s_col}; font-weight:bold;">{sig}</td><td>{row["REASON"]}</td><td class="num">{row["PRICE"]:.2f}</td><td class="num">{row["YTD"]:.1f}%</td><td class="num">{row["SCORE"]:.1f}</td></tr>'
st.markdown(ledger_html + '</tbody></table></div>', unsafe_allow_html=True)

# ==========================================
# 6. BOTTOM TICKER TAPE
# ==========================================
tape_html = '<div class="ticker-tape">'
for b in BENCHMARKS:
    try:
        cur = c[b].dropna().iloc[-1]; prev = c[b].dropna().iloc[-2]; pct = ((cur-prev)/prev)*100
        tape_html += f'<span>{b.replace("^","")} <span style="color:#FFF;">{cur:.2f}</span> <span style="color:{"#00FF00" if pct>0 else "#FF0000"};">{pct:+.2f}%</span></span>'
    except: pass
st.markdown(tape_html + '</div>', unsafe_allow_html=True)
