import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from zoneinfo import ZoneInfo

# 1. Page Configuration
st.set_page_config(page_title="Quant Terminal", layout="wide", initial_sidebar_state="collapsed")

est_zone = ZoneInfo('America/New_York')
now_est = datetime.datetime.now(est_zone)
time_str = now_est.strftime("%I:%M %p ET")
date_str = now_est.strftime("%b %d, %Y").upper()

is_weekend = now_est.weekday() >= 5
is_open_hours = datetime.time(9, 30) <= now_est.time() <= datetime.time(16, 0)
market_status = "MARKET CLOSED" if is_weekend or not is_open_hours else "MARKET OPEN"
status_color = "#00FF00" if market_status == "MARKET OPEN" else "#FF0000"

# CSS Override: Sleek Black & Orange Terminal + Custom Table
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
    .td-right {{ text-align: right; }}
    
    .c-strong-buy {{ color: #00FF00; font-weight: bold; }}
    .c-buy {{ color: #4ADE80; font-weight: bold; }}
    .c-hold {{ color: #FBBF24; font-weight: bold; }}
    .c-sell {{ color: #F87171; font-weight: bold; }}
    .c-strong-sell {{ color: #FF0000; font-weight: bold; }}
    .c-halt {{ color: #D946EF; font-weight: bold; }}
    
    .ticker-tape {{ display: flex; justify-content: space-between; background-color: #000; border-top: 2px solid #FF6600; padding: 8px 15px; font-size: 12px; font-weight: bold; position: fixed; bottom: 0; left: 0; width: 100%; z-index: 100; }}
    .heatmap-grid {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 2px; }}
    .heat-cell {{ text-align: center; padding: 8px 0px; font-size: 10px; font-weight: 900; color: #000; }}
    
    /* Sleek Custom Ledger Table */
    .ledger-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #333; background: #000; }}
    .ledger-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    .ledger-table th {{ position: sticky; top: 0; background-color: #111; color: #FF6600; z-index: 10; border-bottom: 2px solid #FF6600; padding: 8px; text-align: right; }}
    .ledger-table th:first-child {{ text-align: left; }}
    .ledger-table td {{ padding: 8px; border-bottom: 1px solid #222; text-align: right; font-family: monospace; font-size: 12px; }}
    .ledger-table td:first-child {{ text-align: left; font-family: 'Helvetica', sans-serif; font-weight: bold; color: #FFF; }}
    .ledger-table tr:hover {{ background-color: #1A1A1A; }}
    
    #MainMenu, footer, header {{visibility: hidden;}}
    .stLineChart {{ margin-top: -15px; }} 
    </style>
    
    <div class="status-bar">
        <div class="status-left">● {market_status} | SYS.OP.NORMAL</div>
        <div class="status-right">{time_str} | <span style="font-size:10px; color:#888;">{date_str}</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. Universe Definition
BENCHMARKS = ["SPY", "QQQ", "^VIX", "DIA"] 
TICKERS = [
    "AMLP", "BDRY", "BJK", "COAL", "COPX", "CRAK", "CRUZ", "EATZ", "FINX", "FIW", 
    "GDX", "GERM", "GRID", "IAK", "IBB", "ICLN", "IEO", "IGV", "IHF", "IHI", 
    "INDS", "ITA", "ITB", "IYC", "IYF", "IYJ", "IYK", "IYM", "IYT", "IYW", "IYZ", 
    "JETS", "KBWB", "KRE", "MOO", "NERD", "OIH", "ONLN", "PAVE", "PBJ", "PEJ", 
    "PHO", "PICK", "REET", "REM", "REZ", "RTH", "RTM", "RWR", "SIL", "SKYY", "SLX", 
    "SOCL", "SOXX", "VEGI", "VIS", "VNQ", "WOOD", "XBI", "XLC", "XLI", "XLK", 
    "XLP", "XLU", "XLV", "XLY", "XME", "XOP", "XRT", "XSD", "XTN", "XT",
    "SH", "PSQ", "DOG", "TBF"
]
ALL_SYMBOLS = TICKERS + BENCHMARKS

# 3. Data Engine
@st.cache_data(ttl=3600)
def fetch_data():
    data = yf.download(ALL_SYMBOLS, period="1y", progress=False)
    return data['Close'], data['High'], data['Low'], data['Volume']

def calculate_factors(closes, highs, lows, volumes, current_year):
    results = []
    spy_p = closes["SPY"].dropna()
    vix_close = closes["^VIX"].dropna().iloc[-1]
    vix_halt = vix_close > 30 
    
    for ticker in TICKERS:
        try:
            p = closes[ticker].dropna()
            h = highs[ticker].dropna()
            l = lows[ticker].dropna()
            v = volumes[ticker].dropna()
            if len(p) < 200: continue
            
            p_year = p[p.index.year == current_year]
            ytd_ret = ((p.iloc[-1] - p_year.iloc[0]) / p_year.iloc[0]) * 100 if len(p_year) > 0 else 0
            ret_1m = p.pct_change(21).iloc[-1]
            vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram = ret_1m / vol_1m if vol_1m != 0 else 0
            
            roc_20 = p.pct_change(20).iloc[-1]
            roc_60 = p.pct_change(60).iloc[-1]
            roc_accel = roc_20 - (roc_60 / 3)
            rel_strength = p.pct_change(63).iloc[-1] - spy_p.pct_change(63).iloc[-1]
            
            sma_50 = p.rolling(50).mean()
            sma_50_slope = (sma_50.iloc[-1] - sma_50.iloc[-21]) / sma_50.iloc[-21]
            vol_90 = v.rolling(90).mean().iloc[-1]
            vol_conf = (v.rolling(20).mean().iloc[-1] / vol_90) if vol_90 != 0 else 1
            
            high_low = h - l
            high_close = np.abs(h - p.shift())
            low_close = np.abs(l - p.shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            
            peak_20d = p.tail(20).max()
            trailing_stop = peak_20d - (2.5 * atr)
            
            stop_dist_pct = (p.iloc[-1] - trailing_stop) / p.iloc[-1]
            alloc_pct = (0.01 / stop_dist_pct) * 100 if stop_dist_pct > 0 else 0
            alloc_pct = min(alloc_pct, 25.0) 
            
            up_move = h - h.shift(1)
            down_move = l.shift(1) - l
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            tr14 = tr.rolling(14).sum()
            plus_di = 100 * (pd.Series(plus_dm, index=p.index).rolling(14).sum() / tr14)
            minus_di = 100 * (pd.Series(minus_dm, index=p.index).rolling(14).sum() / tr14)
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(14).mean().iloc[-1]
            
            results.append({
                'TKR': ticker, 'PRICE': p.iloc[-1], 'YTD': ytd_ret, 'RAM': ram, 
                'ROC_AC': roc_accel, 'REL_STR': rel_strength, '50D_SLP': sma_50_slope, 
                'VOL_CF': vol_conf, 'ADX': adx, 'STOP_PRC': trailing_stop, 'ALLOC': alloc_pct, 
                'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
            })
        except: continue
            
    df = pd.DataFrame(results).set_index('TKR')
    f = ['RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF'] 
    z = (df[f] - df[f].mean()) / df[f].std()
    
    df['SCORE'] = (z['RAM']*.25 + z['REL_STR']*.20 + z['ROC_AC']*.20 + z['50D_SLP']*.20 + z['VOL_CF']*.15) * 100
    df = df.sort_values(by='SCORE', ascending=False)
    df['RNK'] = range(1, len(df) + 1)
    
    signals = []
    reasons = []
    
    for idx, row in df.iterrows():
        reason = ""
        if not row['Above_200']: reason = "Below 200DMA"
        elif row['ADX'] <= 25: reason = f"Choppy (ADX:{row['ADX']:.1f})"
        elif row['VOL_CF'] < 1.2: reason = f"Low Vol ({row['VOL_CF']:.2f}x)"
        elif row['RAM'] <= 0: reason = "Neg Momentum"
        elif row['REL_STR'] <= 0: reason = "Lagging SPY"
        elif row['ROC_AC'] <= 0: reason = "Decel ROC"
        elif row['50D_SLP'] <= 0: reason = "Neg 50DMA"
        
        fits_all = (reason == "")
        
        if vix_halt:
            signals.append("HALT")
            reasons.append("VIX > 30")
        elif not row['Above_200'] or row['PRICE'] < row['STOP_PRC']: 
            signals.append("STRONG SELL")
            reasons.append(reason if reason else "Hit ATR Stop")
        elif fits_all and row['RNK'] <= 10:
            signals.append("STRONG BUY")
            reasons.append("PASSED")
        elif row['RNK'] <= 10:
            signals.append("BUY")
            reasons.append(reason)
        elif 10 < row['RNK'] <= 15:
            signals.append("HOLD")
            reasons.append(reason)
        else: 
            signals.append("SELL")
            reasons.append(reason)
            
    df['SIGNAL'] = signals
    df['REASON'] = reasons
    return df, vix_halt, vix_close

with st.spinner('SYNCING QUANTITATIVE ENGINE...'):
    c, h, l, v = fetch_data()
    df, vix_halt, vix_close = calculate_factors(c, h, l, v, now_est.year)

# Regime Logic
top_5 = df.head(5).index.tolist()
inverse_etfs = ["SH", "PSQ", "DOG", "TBF"]
defensive_etfs = ["GLD", "SLV", "XLU", "TLT", "IEF"]
inv_count = sum(el in inverse_etfs for el in top_5)
def_count = sum(el in defensive_etfs for el in top_5)
if inv_count >= 2: regime, r_color = "BEAR MARKET (INVERSE LEADERSHIP)", "#FF0000"
elif def_count >= 2: regime, r_color = "RISK-OFF (DEFENSIVE LEADERSHIP)", "#FBBF24"
else: regime, r_color = "RISK-ON (EQUITY EXPANSION)", "#00FF00"

# 4. Interface Layout
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
                <tr><td class="c-strong-buy">STRONG BUY</td><td>Perfect Alignment + ADX>25</td></tr>
                <tr><td class="c-buy">BUY</td><td>Top 10, imperfect setup</td></tr>
                <tr><td class="c-hold">HOLD</td><td>Buffer zone (Rank 11-15)</td></tr>
                <tr><td class="c-sell">SELL</td><td>Drop out of Top 15</td></tr>
                <tr><td class="c-halt">HALT</td><td>VIX > 30 (Risk-Off)</td></tr>
                <tr><td class="c-strong-sell">STRONG SELL</td><td>Below 200DMA or Hit ATR Stop</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    # NEW PANEL: Regime Radar
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
    top_asset = df.index[0] if not df.empty else "SPY"
    st.markdown(f"""
        <div class="bbg-panel" style="padding-bottom: 0px;">
            <div class="bbg-header">TARGET ACQUISITION: {top_asset}</div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 5px;">
                <span style="font-size:24px; font-weight:bold; color:#FF6600;">${df.loc[top_asset, 'PRICE']:.2f}</span>
                <span style="font-size:12px; color:#aaa;">ATR Stop: ${df.loc[top_asset, 'STOP_PRC']:.2f} | Score: {df.loc[top_asset, 'SCORE']:.1f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    chart_data = c[top_asset].dropna().tail(63)
    st.line_chart(chart_data, height=140, use_container_width=True)

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

# 5. Interface Layout: Custom HTML Ledger
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)

ledger_html = """
<div class="ledger-container">
    <table class="ledger-table">
        <thead>
            <tr>
                <th>TKR</th><th>RNK</th><th>SIGNAL</th><th>REASON</th><th>ALLOC</th><th>PRICE</th>
                <th>STOP</th><th>ADX</th><th>SCORE</th><th>YTD</th><th>RAM</th><th>VOL_CF</th>
            </tr>
        </thead>
        <tbody>
"""
for tkr, row in df.iterrows():
    sig = row['SIGNAL']
    if 'STRONG BUY' in sig: s_col = '#00FF00'
    elif 'BUY' in sig: s_col = '#4ADE80'
    elif 'HOLD' in sig: s_col = '#FBBF24'
    elif 'HALT' in sig: s_col = '#D946EF'
    else: s_col = '#FF0000'
    
    ledger_html += f"""
        <tr>
            <td>{tkr}</td>
            <td>{row['RNK']}</td>
            <td style="color:{s_col}; font-weight:bold;">{sig}</td>
            <td style="color:#aaa;">{row['REASON']}</td>
            <td style="color:#FF6600;">{row['ALLOC']:.1f}%</td>
            <td>{row['PRICE']:.2f}</td>
            <td>{row['STOP_PRC']:.2f}</td>
            <td>{row['ADX']:.1f}</td>
            <td>{row['SCORE']:.1f}</td>
            <td style="color:{'#00FF00' if row['YTD']>0 else '#FF0000'};">{row['YTD']:.1f}%</td>
            <td>{row['RAM']:.2f}</td>
            <td>{row['VOL_CF']:.2f}</td>
        </tr>
    """
ledger_html += "</tbody></table></div></div>"
st.markdown(ledger_html, unsafe_allow_html=True)

# 6. Bottom Ticker Tape
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
# ==========================================
# 7. ADMINISTRATOR TOOLS: DEEP MARKET SCANNER
# ==========================================
st.markdown('<div class="bbg-panel"><div class="bbg-header">DEEP MARKET SCANNER (AUTHORIZED PERSONNEL ONLY)</div>', unsafe_allow_html=True)

if st.button("INITIATE AUTONOMOUS MARKET SCAN"):
    scan_container = st.empty()
    progress_bar = st.progress(0)
    
    with st.spinner("STEP 1: Bypassing commercial databases. Scraping official Nasdaq FTP..."):
        # 1. Scrape the Nasdaq Directory
        url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt"
        try:
            ftp_df = pd.read_csv(url, sep='|')
            etfs = ftp_df[(ftp_df['ETF'] == 'Y') & (ftp_df['Test Issue'] == 'N')]
            all_tickers = [t.replace('$', '-').replace('.', '-') for t in etfs['Symbol'].dropna().tolist()]
            scan_container.success(f"Located {len(all_tickers)} total ETFs in the US market.")
        except Exception as e:
            scan_container.error(f"FTP Scrape Failed: {e}")
            all_tickers = []

    if all_tickers:
        with st.spinner("STEP 2: Executing fundamental gatekeeper (AUM & Volume)..."):
            survivors = []
            test_batch = all_tickers[:100] # Limiting to 100 for live app stability
            
            for i, ticker in enumerate(test_batch):
                try:
                    # Update progress bar
                    progress_bar.progress((i + 1) / len(test_batch))
                    
                    # Fundamental Interrogation
                    info = yf.Ticker(ticker).info
                    aum = info.get('totalAssets', 0) or 0
                    vol = info.get('averageVolume', 0) or 0
                    weekly_vol = vol * 5
                    
                    if (3000000 <= aum <= 20000000) and (weekly_vol >= 100000):
                        survivors.append(ticker)
                except:
                    pass
            
            scan_container.success(f"Fundamental scan complete. {len(survivors)} ETFs survived the AUM/Volume gauntlet.")
            
            if survivors:
                st.write(f"**NEW UNIVERSE TARGETS:** {', '.join(survivors)}")
                st.info("Copy these targets into your master TICKERS array to permanently track them.")
st.markdown('</div>', unsafe_allow_html=True)
import streamlit.components.v1 as components

# Injects a 24/7 Live Financial Broadcast (e.g., Bloomberg TV live feed)
st.markdown('<div class="bbg-panel"><div class="bbg-header">LIVE GLOBAL SQUAWK</div>', unsafe_allow_html=True)
components.iframe("https://www.youtube.com/watch?v=iEpJwprxDdk", height=250)
st.markdown('</div>', unsafe_allow_html=True)
