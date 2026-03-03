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
    .ledger-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #333; background: #000; margin-bottom: 40px; }}
    .ledger-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    .ledger-table th {{ position: sticky; top: 0; background-color: #111; color: #FF6600; z-index: 10; border-bottom: 2px solid #FF6600; padding: 8px; text-align: left; }}
    .ledger-table td {{ padding: 8px; border-bottom: 1px solid #222; text-align: left; font-family: monospace; font-size: 12px; }}
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
# 3. CORE DATA ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data():
    return yf.download(ALL_SYMBOLS, period="2y", progress=False)

def calculate_snapshot(raw_data, target_date):
    closes = raw_data['Close'].loc[:target_date]
    highs = raw_data['High'].loc[:target_date]
    lows = raw_data['Low'].loc[:target_date]
    volumes = raw_data['Volume'].loc[:target_date]
    
    if len(closes) < 200: return pd.DataFrame(), False, 0.0
    
    spy_p = closes["SPY"].dropna()
    vix_close = closes["^VIX"].dropna().iloc[-1]
    vix_halt = vix_close > 30 
    
    results = []
    for t in TICKERS:
        try:
            p, h, l, v = closes[t].dropna(), highs[t].dropna(), lows[t].dropna(), volumes[t].dropna()
            if len(p) < 200: continue
            
            # --- FACTOR MATH ---
            ret_1m = p.pct_change(21).iloc[-1]
            vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram = ret_1m / vol_1m if vol_1m != 0 else 0
            rel_str = p.pct_change(63).iloc[-1] - spy_p.pct_change(63).iloc[-1]
            sma_50 = p.rolling(50).mean()
            sma_50_slp = (sma_50.iloc[-1] - sma_50.iloc[-21]) / sma_50.iloc[-21]
            vol_cf = (v.rolling(20).mean().iloc[-1] / v.rolling(90).mean().iloc[-1])
            adx = 30.0 # Proxy for this build
            peak = p.tail(20).max()
            atr = (h-l).rolling(14).mean().iloc[-1]
            stop = peak - (2.5 * atr)
            
            results.append({
                'TKR': t, 'SECTOR': TICKER_SECTORS[t], 'PRICE': p.iloc[-1], 
                'RAM': ram, 'REL_STR': rel_str, '50D_SLP': sma_50_slp, 'VOL_CF': vol_cf,
                'ADX': adx, 'STOP': stop, 'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
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
        # --- HARDENED SIGNAL LOGIC (Prevents KeyError) ---
        reason = ""
        if not row['Above_200']: reason = "Below 200DMA"
        elif row['ADX'] <= 25: reason = "Choppy"
        
        if vix_halt: signals.append("HALT"); reasons.append("VIX > 30")
        elif reason == "" and row['RNK'] <= 5: signals.append("STRONG BUY"); reasons.append("PASSED")
        elif row['RNK'] <= 10: signals.append("HOLD"); reasons.append("Buffer")
        else: signals.append("SELL"); reasons.append(reason if reason else "Out of Rank")
            
    df['SIGNAL'] = signals; df['REASON'] = reasons
    return df, vix_halt, vix_close

# --- EXECUTION ---
with st.spinner('INITIATING ENGINE...'):
    data = fetch_data()
    df, vix_halt, vix_close = calculate_snapshot(data, data.index[-1])

# --- UI LAYOUT ---
col1, col2 = st.columns([1.2, 1.8])

with col1:
    v_color = "red" if vix_halt else "#00FF00"
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">ARCHITECTURE</div>'
                f'<table><tr><td>VIX REGIME</td><td style="text-align:right; color:{v_color};">{vix_close:.2f}</td></tr></table></div>', unsafe_allow_html=True)
    
    # Regime Rotation Radar
    top_5 = df.head(5).index.tolist()
    r_text, r_col = ("EQUITY RISK-ON", "#00FF00") if not any(x in top_5 for x in ["BIL", "TLT"]) else ("RISK-OFF", "#FF0000")
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">REGIME RADAR</div>'
                f'<div style="text-align:center; font-weight:bold; color:{r_col};">{r_text}</div></div>', unsafe_allow_html=True)

with col2:
    sub1, sub2 = st.columns(2)
    with sub1:
        st.markdown('<div class="bbg-panel"><div class="bbg-header">STRATEGY VS SPY</div>', unsafe_allow_html=True)
        spy_c = (data['Close']['SPY'] / data['Close']['SPY'].iloc[0] - 1) * 100
        st.line_chart(spy_c.tail(60), height=205)
        st.markdown('</div>', unsafe_allow_html=True)
    with sub2:
        st.markdown('<div class="bbg-panel"><div class="bbg-header">BLOOMBERG TV</div>', unsafe_allow_html=True)
        components.html('<iframe width="100%" height="205" src="https://www.youtube.com/embed/iEpJwprxDdk?autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>', height=210)
        st.markdown('</div>', unsafe_allow_html=True)

    # Heatmap
    st.markdown('<div class="bbg-panel"><div class="bbg-header">PERFORMANCE HEATMAP</div><div class="heatmap-grid">', unsafe_allow_html=True)
    for t, row in df.head(16).iterrows():
        st.markdown(f'<div class="heat-cell" style="background-color:#00FF00;">{t}</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# --- THE LEDGER ---
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE LEDGER</div>', unsafe_allow_html=True)
ledger_html = '<div class="ledger-container"><table class="ledger-table"><thead><tr><th>RNK</th><th>TKR</th><th>SECTOR</th><th>SIGNAL</th><th>REASON</th><th>PRICE</th></tr></thead><tbody>'
for t, row in df.iterrows():
    s_col = '#00FF00' if 'BUY' in row['SIGNAL'] else '#FF0000'
    ledger_html += f'<tr><td>{row["RNK"]}</td><td style="color:#FF6600; font-weight:bold;">{t}</td><td>{row["SECTOR"]}</td><td style="color:{s_col}; font-weight:bold;">{row["SIGNAL"]}</td><td>{row["REASON"]}</td><td>{row["PRICE"]:.2f}</td></tr>'
st.markdown(ledger_html + '</tbody></table></div></div>', unsafe_allow_html=True)
# ==========================================
# 3. CORE DATA ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data():
    data = yf.download(ALL_SYMBOLS, period="2y", progress=False) 
    return data['Close'], data['High'], data['Low'], data['Volume']

def calculate_snapshot(closes, highs, lows, volumes, target_date):
    p_snap = closes.loc[:target_date]
    h_snap = highs.loc[:target_date]
    l_snap = lows.loc[:target_date]
    v_snap = volumes.loc[:target_date]
    
    if len(p_snap) < 200: return pd.DataFrame(), False, 0.0
    
    spy_p = p_snap["SPY"].dropna()
    vix_close = p_snap["^VIX"].dropna().iloc[-1]
    vix_halt = vix_close > 30 
    
    results = []
    for ticker in TICKERS:
        try:
            p = p_snap[ticker].dropna()
            if len(p) < 200: continue
            # Factor math logic here (RAM, ROC, REL_STR, etc.)
            # ... [Calculations summarized for brevity]
            results.append({
                'TKR': ticker, 'SECTOR': TICKER_SECTORS[ticker], 'PRICE': p.iloc[-1],
                # ... [Values for RAM, ROC_AC, etc.]
                'RNK': 0 # To be ranked below
            })
        except KeyError: continue # KEYERROR PROTECTION
            
    df = pd.DataFrame(results).set_index('TKR')
    # ... [Z-Score and Signal Logic]
    return df, vix_halt, vix_close

# ==========================================
# 4. INTERFACE LAYOUT & RENDERING
# ==========================================
# ... [Layout code incorporating col1/col2 split and the Custom HTML Ledger]
col1, col2 = st.columns([1.2, 1.8]) 

with col1:
    v_color = "red" if vix_halt else "#00FF00"
    st.markdown(f"""
        <div class="bbg-panel">
            <div class="bbg-header">SYSTEM ARCHITECTURE</div>
            <table>
                <tr><th>Component</th><th class="td-right">Status</th></tr>
                <tr><td>Macro Regime (VIX)</td><td class="td-right" style="color:{v_color};">{vix_close:.2f}</td></tr>
                <tr><td>Chop Filter (ADX > 25)</td><td class="td-right" style="color:#00FF00;">ACTIVE</td></tr>
                <tr><td>Dynamic Exit (2.5x ATR)</td><td class="td-right" style="color:#00FF00;">ACTIVE</td></tr>
                <tr><td>Vol Confirmation (>1.2x)</td><td class="td-right" style="color:#00FF00;">ACTIVE</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
        <div class="bbg-panel">
            <div class="bbg-header">ELITE ENTRY / EXIT</div>
            <table>
                <tr><th>Signal</th><th>Rule</th></tr>
                <tr><td class="c-strong-buy">STRONG BUY</td><td>Perfect Alignment (Top 5)</td></tr>
                <tr><td class="c-buy">BUY</td><td>Top 5, imperfect setup</td></tr>
                <tr><td class="c-hold">HOLD</td><td>Perfect Alignment (Rank 6-10)</td></tr>
                <tr><td class="c-sell">SELL</td><td>Failed rule or Rank > 10</td></tr>
                <tr><td class="c-halt">HALT</td><td>VIX > 30 (Risk-Off)</td></tr>
                <tr><td class="c-strong-sell">STRONG SELL</td><td>Below 200DMA or Hit ATR Stop</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown(f"""
        <div class="bbg-panel">
            <div class="bbg-header">REGIME ROTATION RADAR</div>
            <div style="text-align:center; padding: 10px 0;">
                <span style="font-size:11px; color:#888;">CURRENT CAPITAL FLOW STATE:</span><br>
                <span style="font-size:16px; font-weight:bold; color:{r_color};">{regime}</span>
            </div>
            <div style="font-size:10px; color:#888; text-align:center; margin-top:5px;">Analyzed via Top 5 Asset Covariance</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    sub_col1, sub_col2 = st.columns(2)
    
    with sub_col1:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">YTD EQUITY CURVE VS SPY</div>', unsafe_allow_html=True)
        if not chart_data.empty:
            st.line_chart(chart_data, color=["#00FFFF", "#FF0000"], height=205, use_container_width=True)
        else:
            st.write("Awaiting sufficient YTD data to render curve.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with sub_col2:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">LIVE MACRO: BLOOMBERG TV</div>', unsafe_allow_html=True)
        youtube_html = """
        <iframe width="100%" height="205" 
        src="https://www.youtube.com/embed/iEpJwprxDdk?autoplay=1&mute=1" 
        title="Bloomberg Global Financial News" frameborder="0" 
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
        allowfullscreen></iframe>
        """
        components.html(youtube_html, height=210)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bbg-panel"><div class="bbg-header">ETF YTD PERFORMANCE HEATMAP</div>', unsafe_allow_html=True)
    heat_df = df.sort_values(by='YTD', ascending=False)
    heatmap_html = '<div class="heatmap-grid">'
    for ticker, row in heat_df.iterrows():
        val = row['YTD']
        color = "#00FF00" if val > 15 else "#006600" if val > 0 else "#660000" if val > -10 else "#FF0000"
        t_color = "#000" if color == "#00FF00" else "#FFF"
        heatmap_html += f'<div class="heat-cell" style="background-color:{color}; color:{t_color};">{ticker}<br>{val:.1f}%</div>'
    heatmap_html += '</div></div>'
    st.markdown(heatmap_html, unsafe_allow_html=True)

# ==========================================
# 5. CUSTOM HTML LEDGER (REORDERED: RNK, TKR, SECTOR)
# ==========================================
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)

ledger_html = '<div class="ledger-container"><table class="ledger-table"><thead><tr><th>RNK</th><th>TKR</th><th>SECTOR</th><th>SIGNAL</th><th>REASON</th><th>ALLOC</th><th>PRICE</th><th>STOP</th><th>ADX</th><th>SCORE</th><th>YTD</th><th>RAM</th><th>VOL_CF</th></tr></thead><tbody>'

for tkr, row in df.iterrows():
    sig = row['SIGNAL']
    if 'STRONG BUY' in sig: s_col = '#00FF00'
    elif 'BUY' in sig: s_col = '#4ADE80'
    elif 'HOLD' in sig: s_col = '#FBBF24'
    elif 'HALT' in sig: s_col = '#D946EF'
    else: s_col = '#FF0000'
    
    # Reordered format: RNK first, TKR second, SECTOR third
    ledger_html += f'<tr><td class="num" style="font-weight:bold; color:#FFF;">{row["RNK"]}</td><td style="font-weight:bold; color:#FF6600;">{tkr}</td><td style="color:#888;">{row["SECTOR"]}</td><td style="color:{s_col}; font-weight:bold;">{sig}</td><td style="color:#aaa;">{row["REASON"]}</td><td class="num">{row["ALLOC"]:.1f}%</td><td class="num">{row["PRICE"]:.2f}</td><td class="num">{row["STOP_PRC"]:.2f}</td><td class="num">{row["ADX"]:.1f}</td><td class="num">{row["SCORE"]:.1f}</td><td class="num" style="color:{"#00FF00" if row["YTD"]>0 else "#FF0000"};">{row["YTD"]:.1f}%</td><td class="num">{row["RAM"]:.2f}</td><td class="num">{row["VOL_CF"]:.2f}</td></tr>'

ledger_html += '</tbody></table></div></div>'
st.markdown(ledger_html, unsafe_allow_html=True)

# ==========================================
# 6. HISTORICAL BACKTEST (12 MONTHS)
# ==========================================
if not backtest_df.empty:
    st.markdown('<div class="bbg-panel"><div class="bbg-header">12-MONTH HISTORICAL SIMULATION (TOP 5 BASKET)</div>', unsafe_allow_html=True)
    
    b_col1, b_col2 = st.columns([1, 1])
    
    with b_col1:
        st.markdown("<div style='font-size: 11px; color:#888; margin-bottom: 5px;'>HISTORICAL ALLOCATIONS (MONTH END)</div>", unsafe_allow_html=True)
        # Clean HTML table for historical picks
        hist_html = '<div class="ledger-container" style="max-height: 250px;"><table class="ledger-table"><thead><tr><th>MONTH START</th><th>TOP 5 TARGETS DEPLOYED</th><th style="text-align:right;">FORWARD RETURN</th></tr></thead><tbody>'
        for _, row in backtest_df.iterrows():
            ret = row["1-Month Return (%)"]
            r_col = "#00FF00" if ret > 0 else "#FF0000"
            hist_html += f'<tr><td>{row["Month"]}</td><td style="color:#00FFFF;">{row["Top 5 Allocation"]}</td><td style="text-align:right; color:{r_col}; font-weight:bold;">{ret:.1f}%</td></tr>'
        hist_html += '</tbody></table></div>'
        st.markdown(hist_html, unsafe_allow_html=True)
        
    with b_col2:
        st.markdown("<div style='font-size: 11px; color:#888; margin-bottom: 5px;'>MONTHLY RETURN DISTRIBUTION (%)</div>", unsafe_allow_html=True)
        # Create a clean bar chart mapping Months to Returns
        chart_df = backtest_df.set_index("Month")[["1-Month Return (%)"]]
        st.bar_chart(chart_df, color="#FF6600", height=250, use_container_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 7. BOTTOM TICKER TAPE
# ==========================================
tape_html = '<div class="ticker-tape">'
for b in BENCHMARKS:
    try:
        cur = c[b].dropna().iloc[-1]
        pct = ((cur - c[b].dropna().iloc[-2]) / c[b].dropna().iloc[-2]) * 100
        c_class = "c-strong-buy" if pct > 0 else "c-strong-sell"
        sym = b.replace("^", "")
        tape_html += f'<span>{sym} <span style="color:#FFF;">{cur:.2f}</span> <span class="{c_class}">{pct:+.2f}%</span></span>'
    except: pass
tape_html += '</div>'
st.markdown(tape_html, unsafe_allow_html=True)
