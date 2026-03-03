import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from zoneinfo import ZoneInfo

# 1. Page Configuration
st.set_page_config(page_title="Quant Terminal", layout="wide", initial_sidebar_state="collapsed")

# Market Time & Status
est_zone = ZoneInfo('America/New_York')
now_est = datetime.datetime.now(est_zone)
time_str = now_est.strftime("%I:%M %p ET")
date_str = now_est.strftime("%b %d, %Y").upper()

is_weekend = now_est.weekday() >= 5
is_open_hours = datetime.time(9, 30) <= now_est.time() <= datetime.time(16, 0)
market_status = "MARKET CLOSED" if is_weekend or not is_open_hours else "MARKET OPEN"
status_color = "#00FF00" if market_status == "MARKET OPEN" else "#FF0000"

# CSS Override for Extreme Density
# CSS Override for Modern Glassmorphism Density
st.markdown(f"""
    <style>
    /* Global Base */
    .stApp {{
        background: radial-gradient(circle at top right, #0B0E14, #050608);
        color: #E2E8F0;
    }}
    * {{ font-family: 'Inter', 'Segoe UI', sans-serif !important; letter-spacing: 0.5px; }}
    
    /* Top Status Bar */
    .status-bar {{
        display: flex; justify-content: space-between; align-items: center;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(0, 255, 255, 0.2);
        padding: 8px 15px; margin-top: -50px; margin-bottom: 15px;
        border-radius: 0 0 10px 10px;
        box-shadow: 0 4px 15px rgba(0, 255, 255, 0.05);
    }}
    .status-left {{ color: {status_color}; font-weight: 800; font-size: 13px; text-transform: uppercase; text-shadow: 0 0 8px {status_color}; }}
    .status-right {{ color: #38BDF8; text-align: right; font-weight: 600; font-size: 13px; }}
    
    /* Modern Glass Panels */
    .bbg-panel {{
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 12px; margin-bottom: 15px; border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }}
    .bbg-panel:hover {{ border: 1px solid rgba(56, 189, 248, 0.3); }}
    
    .bbg-header {{
        color: #38BDF8; font-weight: 800; font-size: 12px; text-transform: uppercase; 
        border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding-bottom: 6px; margin-bottom: 10px;
        letter-spacing: 1.5px;
    }}
    
    /* Tables */
    table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11px; }}
    th {{ text-align: left; color: #94A3B8; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 6px 4px; font-weight: 600; }}
    td {{ padding: 6px 4px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); color: #F8FAFC; }}
    .td-right {{ text-align: right; }}
    
    /* Signal Neon Colors */
    .c-strong-buy {{ color: #10B981; font-weight: 800; text-shadow: 0 0 5px rgba(16, 185, 129, 0.4); }}
    .c-buy {{ color: #34D399; font-weight: 700; }}
    .c-hold {{ color: #FBBF24; font-weight: 700; }}
    .c-sell {{ color: #F87171; font-weight: 700; }}
    .c-strong-sell {{ color: #EF4444; font-weight: 800; text-shadow: 0 0 5px rgba(239, 68, 68, 0.4); }}
    .c-halt {{ color: #D946EF; font-weight: 800; text-shadow: 0 0 5px rgba(217, 70, 239, 0.4); }}
    
    /* Ticker Tape Bottom */
    .ticker-tape {{
        display: flex; justify-content: space-between; 
        background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px);
        border-top: 1px solid rgba(0, 255, 255, 0.2); padding: 8px 15px; font-size: 11px; font-weight: 700;
        position: fixed; bottom: 0; left: 0; width: 100%; z-index: 100;
    }}
    
    /* Heatmap Grid */
    .heatmap-grid {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 2px; }}
    .heat-cell {{ text-align: center; padding: 6px 0px; font-size: 10px; font-weight: 700; border-radius: 4px; }}
    
    /* Streamlit DataFrame Overrides */
    .dataframe {{ font-size: 11px !important; text-align: right; }}
    .dataframe th {{ background-color: rgba(15, 23, 42, 0.8) !important; color: #38BDF8 !important; border-bottom: 1px solid #38BDF8 !important; }}
    .dataframe td {{ border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important; padding: 6px !important; }}
    
    #MainMenu, footer, header {{visibility: hidden;}}
    .stLineChart {{ margin-top: -15px; }} 
    </style>
    
    <div class="status-bar">
        <div class="status-left">● {market_status} | SYS.OP.NORMAL</div>
        <div class="status-right">{time_str} | <span style="font-size:10px; color:#94A3B8;">{date_str}</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. Universe Definition (INVERSE ETFs ADDED: SH, PSQ, DOG, TBF)
BENCHMARKS = ["SPY", "QQQ", "^VIX", "DIA"] 
TICKERS = [
    "AMLP", "BDRY", "BJK", "COAL", "COPX", "CRAK", "CRUZ", "EATZ", "FINX", "FIW", 
    "GDX", "GERM", "GRID", "IAK", "IBB", "ICLN", "IEO", "IGV", "IHF", "IHI", 
    "INDS", "ITA", "ITB", "IYC", "IYF", "IYJ", "IYK", "IYM", "IYT", "IYW", "IYZ", 
    "JETS", "KBWB", "KRE", "MOO", "NERD", "OIH", "ONLN", "PAVE", "PBJ", "PEJ", 
    "PHO", "PICK", "REET", "REM", "REZ", "RTH", "RTM", "RWR", "SIL", "SKYY", "SLX", 
    "SOCL", "SOXX", "VEGI", "VIS", "VNQ", "WOOD", "XBI", "XLC", "XLI", "XLK", 
    "XLP", "XLU", "XLV", "XLY", "XME", "XOP", "XRT", "XSD", "XTN", "XT",
    "SH", "PSQ", "DOG", "TBF" # Bear Market Mandate Inverse Exposure
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
    
    # Macro Kill Switch Check
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
            
            # ATR & Trailing Stop
            high_low = h - l
            high_close = np.abs(h - p.shift())
            low_close = np.abs(l - p.shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            
            peak_20d = p.tail(20).max()
            trailing_stop = peak_20d - (2.5 * atr)
            
            # VOLATILITY TARGETING (1% Account Risk Model)
            stop_dist_pct = (p.iloc[-1] - trailing_stop) / p.iloc[-1]
            alloc_pct = (0.01 / stop_dist_pct) * 100 if stop_dist_pct > 0 else 0
            alloc_pct = min(alloc_pct, 25.0) # Cap max single position weight at 25%
            
            # ADX Calculation
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
                'VOL_CF': vol_conf, 'ADX': adx, 'STOP_PRC': trailing_stop, 
                'ALLOC_%': alloc_pct, # Added Allocation Parameter
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
    fail_reasons = []
    
    for idx, row in df.iterrows():
        reason = ""
        if not row['Above_200']: reason = "Below 200DMA"
        elif row['ADX'] <= 25: reason = f"Choppy (ADX:{row['ADX']:.1f})"
        elif row['VOL_CF'] < 1.2: reason = f"Low Vol ({row['VOL_CF']:.2f}x)"
        elif row['RAM'] <= 0: reason = "Neg Momentum"
        elif row['REL_STR'] <= 0: reason = "Lagging SPY"
        elif row['ROC_AC'] <= 0: reason = "Decelerating"
        elif row['50D_SLP'] <= 0: reason = "50DMA Dropping"
        
        fits_all = (reason == "")
        
        if vix_halt:
            signals.append("HALT (VIX)")
            fail_reasons.append("MACRO RISK-OFF")
        elif not row['Above_200'] or row['PRICE'] < row['STOP_PRC']: 
            signals.append("STRONG SELL" if row['RNK'] > 15 else "SELL")
            fail_reasons.append(reason if reason else "Hit ATR Stop")
        elif fits_all and row['RNK'] <= 10:
            signals.append("STRONG BUY")
            fail_reasons.append("PASSED")
        elif row['RNK'] <= 10:
            signals.append("BUY")
            fail_reasons.append(reason)
        elif 10 < row['RNK'] <= 15:
            signals.append("HOLD")
            fail_reasons.append(reason)
        else: 
            signals.append("SELL")
            fail_reasons.append(reason)
            
    df['SIGNAL'] = signals
    df['FAIL_REASON'] = fail_reasons
    
    # Covariance Matrix Calculation for Top 5 Assets
    top_5_tickers = df.head(5).index.tolist()
    returns_3m = closes.pct_change().tail(63)
    if len(top_5_tickers) > 1:
        corr_matrix = returns_3m[top_5_tickers].corr()
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        avg_corr = corr_matrix.where(mask).mean().mean()
        if pd.isna(avg_corr): avg_corr = 0
    else:
        avg_corr = 0
        
    return df, vix_halt, vix_close, avg_corr

with st.spinner('SYNCING ELITE DATA...'):
    c, h, l, v = fetch_data()
    df, vix_halt, vix_close, avg_corr = calculate_factors(c, h, l, v, now_est.year)

# 4. Interface Layout: Top Panels
col1, col2 = st.columns([1.2, 1.8]) 

with col1:
    vix_display = f"<span style='color:red;'>HALT TRIGGERED ({vix_close:.2f})</span>" if vix_halt else f"<span style='color:#00FF00;'>SAFE ({vix_close:.2f})</span>"
    corr_display = f"<span style='color:red;'>{avg_corr:.2f} (OVERLAP RISK)</span>" if avg_corr > 0.75 else f"<span style='color:#00FF00;'>{avg_corr:.2f} (DIVERSIFIED)</span>"
    
    st.markdown(f"""
        <div class="bbg-panel">
            <div class="bbg-header">SYSTEM ARCHITECTURE</div>
            <table>
                <tr><th>Component</th><th class="td-right">Status</th></tr>
                <tr><td>Macro Regime (VIX < 30)</td><td class="td-right">{vix_display}</td></tr>
                <tr><td>Inverse Universe (Bear Exposure)</td><td class="td-right" style="color:#00FF00;">ACTIVE (4 ASSETS)</td></tr>
                <tr><td>Top 5 Correlation (Covariance)</td><td class="td-right">{corr_display}</td></tr>
                <tr><td>Vol Sizing (1% Account Risk)</td><td class="td-right" style="color:#00FF00;">ACTIVE</td></tr>
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
                <tr><td class="c-halt">HALT (VIX)</td><td>VIX > 30 (Risk-Off)</td></tr>
                <tr><td class="c-strong-sell">STRONG SELL</td><td>Below 200DMA or Hit ATR Stop</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

with col2:
    top_asset = df.index[0] if not df.empty else "SPY"
    st.markdown(f"""
        <div class="bbg-panel" style="padding-bottom: 0px;">
            <div class="bbg-header" style="color:#00FFFF !important;">TARGET ACQUISITION: {top_asset}</div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 5px;">
                <span style="font-size:24px; font-weight:bold; color:#00FF00;">${df.loc[top_asset, 'PRICE']:.2f}</span>
                <span style="font-size:12px; color:#aaa;">Target Size: {df.loc[top_asset, 'ALLOC_%']:.1f}% | Score: {df.loc[top_asset, 'SCORE']:.1f}</span>
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
        text_color = "#000000" if color == "#00FF00" else "#FFFFFF"
        heatmap_html += f'<div class="heat-cell" style="background-color:{color}; color:{text_color};">{ticker}<br>{val:.1f}%</div>'
    heatmap_html += '</div></div>'
    st.markdown(heatmap_html, unsafe_allow_html=True)

# 5. Interface Layout: Bottom Panel
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)

# 1. Explicitly copy the exact columns needed
cols_to_display = ['RNK', 'SIGNAL', 'FAIL_REASON', 'ALLOC_%', 'PRICE', 'STOP_PRC', 'ADX', 'SCORE', 'YTD', 'RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF']
display_df = df[cols_to_display].copy()

# 2. Explicitly round ONLY the numeric columns to prevent string corruption
numeric_cols = ['ALLOC_%', 'PRICE', 'STOP_PRC', 'ADX', 'SCORE', 'YTD', 'RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF']
for col in numeric_cols:
    display_df[col] = pd.to_numeric(display_df[col], errors='coerce').round(2)

# 3. Define strict color mapping
def style_signals(val):
    if not isinstance(val, str): return ''
    if 'STRONG BUY' in val: color = '#00FF00'
    elif 'BUY' in val: color = '#66FF66'
    elif 'HOLD' in val: color = '#FFFF00'
    elif 'HALT' in val: color = '#FF00FF'
    else: color = '#FF0000'
    return f'color: {color}; font-weight: bold;'

# 4. Apply style and render
styled_df = display_df.style.map(style_signals, subset=['SIGNAL'])
st.dataframe(styled_df, use_container_width=True, height=400)

st.markdown('</div>', unsafe_allow_html=True)
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
