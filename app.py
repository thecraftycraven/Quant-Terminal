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
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    th {{ text-align: left; color: #888; border-bottom: 1px solid #333; padding: 6px; font-weight: bold; text-transform: uppercase; }}
    td {{ padding: 6px; border-bottom: 1px solid #1A1A1A; }}
    .c-strong-buy {{ color: #00FF00; font-weight: bold; }}
    .c-buy {{ color: #4ADE80; font-weight: bold; }}
    .c-hold {{ color: #FBBF24; font-weight: bold; }}
    .c-sell {{ color: #F87171; font-weight: bold; }}
    .c-strong-sell {{ color: #FF0000; font-weight: bold; }}
    .c-halt {{ color: #D946EF; font-weight: bold; }}
    .ticker-tape {{ display: flex; justify-content: space-between; background-color: #000; border-top: 2px solid #FF6600; padding: 8px 15px; font-size: 12px; font-weight: bold; position: fixed; bottom: 0; left: 0; width: 100%; z-index: 100; }}
    .heatmap-grid {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 2px; }}
    .heat-cell {{ text-align: center; padding: 8px 0px; font-size: 10px; font-weight: 900; color: #000; }}
    .ledger-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #333; background: #000; margin-bottom: 15px; }}
    .ledger-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    .ledger-table th {{ position: sticky; top: 0; background-color: #111; color: #FF6600; z-index: 10; border-bottom: 2px solid #FF6600; padding: 8px; text-align: left; }}
    .ledger-table td {{ padding: 8px; border-bottom: 1px solid #222; text-align: left; font-family: monospace; font-size: 12px; }}
    .ledger-table td.num {{ text-align: right; }}
    .ledger-table tr:hover {{ background-color: #1A1A1A; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
    <div class="status-bar">
        <div class="status-left">● {market_status} | SYS.OP.NORMAL</div>
        <div class="status-right">{time_str} | <span style="font-size:10px; color:#888;">{date_str}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DEFINITIVE 46-ASSET SECTOR MAP
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
BENCHMARKS = ["SPY", "QQQ", "^VIX", "DIA"] 
ALL_SYMBOLS = TICKERS + BENCHMARKS

# ==========================================
# 3. DATA ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data():
    return yf.download(ALL_SYMBOLS, period="2y", progress=False)

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
            
            p_y = p[p.index.year == target_date.year]
            ytd = ((p.iloc[-1] - p_y.iloc[0]) / p_y.iloc[0]) * 100 if not p_y.empty else 0
            
            # Simplified for speed
            ret_1m = p.pct_change(21).iloc[-1]
            vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram = ret_1m / vol_1m if vol_1m != 0 else 0
            rel_str = p.pct_change(63).iloc[-1] - spy_p.pct_change(63).iloc[-1]
            sma_50 = p.rolling(50).mean()
            sma_50_slp = (sma_50.iloc[-1] - sma_50.iloc[-21]) / sma_50.iloc[-21]
            vol_cf = (v.rolling(20).mean().iloc[-1] / v.rolling(90).mean().iloc[-1])
            atr = (h-l).rolling(14).mean().iloc[-1]
            stop = p.tail(20).max() - (2.5 * atr)
            alloc = (0.01 / ((p.iloc[-1] - stop) / p.iloc[-1])) * 100 if p.iloc[-1] > stop else 0
            
            # ADX Calculation
            tr = pd.concat([h - l, np.abs(h - p.shift()), np.abs(l - p.shift())], axis=1).max(axis=1)
            up = h - h.shift(1); dw = l.shift(1) - l
            plus_dm = np.where((up > dw) & (up > 0), up, 0)
            minus_dm = np.where((dw > up) & (dw > 0), dw, 0)
            tr14 = tr.rolling(14).sum()
            plus_di = 100 * (pd.Series(plus_dm, index=p.index).rolling(14).sum() / tr14)
            minus_di = 100 * (pd.Series(minus_dm, index=p.index).rolling(14).sum() / tr14)
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(14).mean().iloc[-1]

            results.append({
                'TKR': t, 'SECTOR': TICKER_SECTORS[t], 'PRICE': p.iloc[-1], 'YTD': ytd,
                'RAM': ram, 'REL_STR': rel_str, '50D_SLP': sma_50_slp, 'VOL_CF': vol_cf,
                'ADX': adx, 'STOP_PRC': stop, 'ALLOC': min(alloc, 25.0),
                'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
            })
        except: continue
            
    df = pd.DataFrame(results).set_index('TKR')
    f = ['RAM', 'REL_STR', '50D_SLP', 'VOL_CF']
    z = (df[f] - df[f].mean()) / df[f].std()
    df['SCORE'] = (z['RAM']*.3 + z['REL_STR']*.3 + z['50D_SLP']*.2 + z['VOL_CF']*.2) * 100
    df = df.sort_values('SCORE', ascending=False)
    df['RNK'] = range(1, len(df) + 1)
    
    signals, reasons = [], []
    for _, row in df.iterrows():
        reason = ""
        if not row['Above_200']: reason = "Below 200DMA"
        elif row['ADX'] <= 25: reason = f"Choppy ({row['ADX']:.1f})"
        elif row['VOL_CF'] < 1.2: reason = "Low Vol"
        
        if vix_halt: signals.append("HALT"); reasons.append("VIX > 30")
        elif reason == "" and row['RNK'] <= 5: signals.append("STRONG BUY"); reasons.append("PASSED")
        elif reason == "" and row['RNK'] <= 10: signals.append("HOLD"); reasons.append("Buffer")
        else: signals.append("SELL"); reasons.append(reason if reason else f"Rank #{row['RNK']}")
            
    df['SIGNAL'] = signals; df['REASON'] = reasons
    return df, vix_halt, vix_close

@st.cache_data(ttl=3600)
def run_backtest(data):
    monthly = data['Close'].resample('ME').last()
    dates = monthly.index[-13:-1]
    log = []
    for i in range(len(dates)-1):
        s, e = dates[i], dates[i+1]
        snap, _, _ = calculate_snapshot(data, s)
        buys = snap[snap['SIGNAL'] == 'STRONG BUY'].head(5).index.tolist()
        if not buys: buys = ["BIL"]; ret = ((data['Close'].loc[e, "BIL"] / data['Close'].loc[s, "BIL"]) - 1) * 100
        else: ret = ((data['Close'].loc[e, buys].mean() / data['Close'].loc[s, buys].mean()) - 1) * 100
        log.append({"Month": s.strftime('%Y-%b'), "Targets": ", ".join(buys), "Return": ret})
    return pd.DataFrame(log)

# --- EXECUTION ---
with st.spinner('SYNCING ENGINES...'):
    raw_data = fetch_data()
    df, vix_halt, vix_close = calculate_snapshot(raw_data, raw_data.index[-1])
    backtest_df = run_backtest(raw_data)

# --- UI LAYOUT ---
col1, col2 = st.columns([1.2, 1.8])

with col1:
    v_c = "red" if vix_halt else "#00FF00"
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">ARCHITECTURE</div><table><tr><td>VIX REGIME</td><td style="text-align:right; color:{v_c};">{vix_close:.2f}</td></tr></table></div>', unsafe_allow_html=True)
    st.markdown('<div class="bbg-panel"><div class="bbg-header">ELITE RULES</div><table><tr><td class="c-strong-buy">STRONG BUY</td><td>Top 5 + Perfect Alignment</td></tr><tr><td class="c-hold">HOLD</td><td>Rank 6-10 + Perfect Alignment</td></tr></table></div>', unsafe_allow_html=True)
    top_5 = df.head(5).index.tolist()
    reg, r_c = ("RISK-OFF", "#FBBF24") if any(x in top_5 for x in ["BIL", "TLT", "IEF"]) else ("RISK-ON", "#00FF00")
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">REGIME ROTATION</div><div style="text-align:center; font-weight:bold; color:{r_c};">{reg}</div></div>', unsafe_allow_html=True)

with col2:
    sub1, sub2 = st.columns(2)
    with sub1:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">YTD STRATEGY VS SPY</div>', unsafe_allow_html=True)
        spy_y = (raw_data['Close']['SPY'] / raw_data['Close']['SPY'][raw_data['Close'].index.year == now_est.year][0] - 1) * 100
        st.line_chart(spy_y.tail(60), height=205)
        st.markdown('</div>', unsafe_allow_html=True)
    with sub2:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">LIVE BLOOMBERG TV</div>', unsafe_allow_html=True)
        components.html('<iframe width="100%" height="205" src="https://www.youtube.com/embed/iEpJwprxDdk?autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>', height=210)
        st.markdown('</div>', unsafe_allow_html=True)

    # 4F. THE HEATMAP (ALL 46 ASSETS)
    st.markdown('<div class="bbg-panel"><div class="bbg-header">ALL-ASSET YTD PERFORMANCE HEATMAP</div>', unsafe_allow_html=True)
    heat_df = df.sort_values('YTD', ascending=False)
    heatmap_html = '<div class="heatmap-grid">'
    for t, row in heat_df.iterrows():
        val = row['YTD']
        c = "#00FF00" if val > 10 else "#006600" if val > 0 else "#660000" if val > -5 else "#FF0000"
        tc = "#000" if c == "#00FF00" else "#FFF"
        heatmap_html += f'<div class="heat-cell" style="background-color:{c}; color:{tc};">{t}<br>{val:.1f}%</div>'
    st.markdown(heatmap_html + '</div></div>', unsafe_allow_html=True)

# --- THE LEDGER (RANK, TKR, SECTOR) ---
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)
ledger_html = '<div class="ledger-container"><table class="ledger-table"><thead><tr><th>RNK</th><th>TKR</th><th>SECTOR</th><th>SIGNAL</th><th>REASON</th><th>ALLOC</th><th>PRICE</th><th>STOP</th><th>ADX</th><th>SCORE</th><th>YTD</th></tr></thead><tbody>'
for t, row in df.iterrows():
    s_col = '#00FF00' if 'BUY' in row['SIGNAL'] else '#FBBF24' if 'HOLD' in row['SIGNAL'] else '#FF0000'
    ledger_html += f'<tr><td>{row["RNK"]}</td><td style="color:#FF6600; font-weight:bold;">{t}</td><td style="color:#888;">{row["SECTOR"]}</td><td style="color:{s_col}; font-weight:bold;">{row["SIGNAL"]}</td><td>{row["REASON"]}</td><td class="num">{row["ALLOC"]:.1f}%</td><td class="num">{row["PRICE"]:.2f}</td><td class="num">{row["STOP_PRC"]:.2f}</td><td class="num">{row["ADX"]:.1f}</td><td class="num">{row["SCORE"]:.1f}</td><td class="num">{row["YTD"]:.1f}%</td></tr>'
st.markdown(ledger_html + '</tbody></table></div>', unsafe_allow_html=True)

# --- BACKTEST CHARTS ---
st.markdown('<div class="bbg-panel"><div class="bbg-header">12-MONTH HISTORICAL PERFORMANCE</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    hist_html = '<div class="ledger-container" style="max-height:250px;"><table class="ledger-table"><thead><tr><th>MONTH</th><th>TARGETS</th><th>RETURN</th></tr></thead><tbody>'
    for _, r in backtest_df.iterrows():
        hist_html += f'<tr><td>{r["Month"]}</td><td style="color:#00FFFF;">{r["Targets"]}</td><td style="color:{"#00FF00" if r["Return"]>0 else "#FF0000"};">{r["Return"]:.1f}%</td></tr>'
    st.markdown(hist_html + '</tbody></table></div>', unsafe_allow_html=True)
with c2:
    st.bar_chart(backtest_df.set_index("Month")["Return"], color="#FF6600", height=250)
st.markdown('</div>', unsafe_allow_html=True)

# --- TICKER TAPE ---
tape_html = '<div class="ticker-tape">'
for b in BENCHMARKS:
    try:
        cur = raw_data['Close'][b].iloc[-1]; prev = raw_data['Close'][b].iloc[-2]; pct = ((cur-prev)/prev)*100
        tape_html += f'<span>{b.replace("^","")} <span style="color:#FFF;">{cur:.2f}</span> <span style="color:{"#00FF00" if pct>0 else "#FF0000"};">{pct:+.2f}%</span></span>'
    except: pass
st.markdown(tape_html + '</div>', unsafe_allow_html=True)

# ==========================================
# 5. CUSTOM HTML LEDGER
# ==========================================
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)

ledger_html = '<div class="ledger-container"><table class="ledger-table"><thead><tr><th>SECTOR</th><th>TKR</th><th>RNK</th><th>SIGNAL</th><th>REASON</th><th>ALLOC</th><th>PRICE</th><th>STOP</th><th>ADX</th><th>SCORE</th><th>YTD</th><th>RAM</th><th>VOL_CF</th></tr></thead><tbody>'

for tkr, row in df.iterrows():
    sig = row['SIGNAL']
    if 'STRONG BUY' in sig: s_col = '#00FF00'
    elif 'BUY' in sig: s_col = '#4ADE80'
    elif 'HOLD' in sig: s_col = '#FBBF24'
    elif 'HALT' in sig: s_col = '#D946EF'
    else: s_col = '#FF0000'
    
    ledger_html += f'<tr><td style="color:#888;">{row["SECTOR"]}</td><td style="font-weight:bold; color:#FFF;">{tkr}</td><td class="num">{row["RNK"]}</td><td style="color:{s_col}; font-weight:bold;">{sig}</td><td style="color:#aaa;">{row["REASON"]}</td><td class="num" style="color:#FF6600;">{row["ALLOC"]:.1f}%</td><td class="num">{row["PRICE"]:.2f}</td><td class="num">{row["STOP_PRC"]:.2f}</td><td class="num">{row["ADX"]:.1f}</td><td class="num">{row["SCORE"]:.1f}</td><td class="num" style="color:{"#00FF00" if row["YTD"]>0 else "#FF0000"};">{row["YTD"]:.1f}%</td><td class="num">{row["RAM"]:.2f}</td><td class="num">{row["VOL_CF"]:.2f}</td></tr>'

ledger_html += '</tbody></table></div></div>'
st.markdown(ledger_html, unsafe_allow_html=True)


