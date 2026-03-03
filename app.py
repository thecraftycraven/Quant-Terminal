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
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0c0c0c; }}
    * {{ font-family: 'Helvetica', sans-serif !important; color: #FFFFFF; }}
    .status-bar {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00FFFF; padding: 5px 0px; margin-top: -50px; margin-bottom: 10px; }}
    .status-left {{ color: {status_color}; font-weight: bold; font-size: 14px; text-transform: uppercase; }}
    .status-right {{ color: #00FFFF; text-align: right; font-weight: bold; font-size: 14px; }}
    .bbg-panel {{ border: 1px solid #444; background-color: #111; padding: 8px; margin-bottom: 10px; border-radius: 2px; }}
    .bbg-header {{ color: #FFFFFF; font-weight: bold; font-size: 14px; text-transform: uppercase; border-bottom: 1px solid #444; padding-bottom: 4px; margin-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    th {{ text-align: left; color: #aaa; border-bottom: 1px solid #333; padding: 4px; }}
    td {{ padding: 4px; border-bottom: 1px solid #222; }}
    .td-right {{ text-align: right; }}
    .c-strong-buy {{ color: #00FF00; font-weight: bold; }}
    .c-buy {{ color: #66FF66; font-weight: bold; }}
    .c-hold {{ color: #FFFF00; font-weight: bold; }}
    .c-sell {{ color: #FF6666; font-weight: bold; }}
    .c-strong-sell {{ color: #FF0000; font-weight: bold; }}
    .c-halt {{ color: #FF00FF; font-weight: bold; }}
    .ticker-tape {{ display: flex; justify-content: space-between; background-color: #111; border-top: 2px solid #333; padding: 5px 10px; font-size: 12px; font-weight: bold; }}
    .heatmap-grid {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 1px; }}
    .heat-cell {{ text-align: center; padding: 4px 0px; font-size: 10px; font-weight: bold; }}
    .dataframe {{ font-size: 10px !important; text-align: right; }}
    .dataframe th {{ background-color: #111111 !important; color: #FF8C00 !important; border-bottom: 2px solid #FF8C00 !important; }}
    .dataframe td {{ border-bottom: 1px solid #333333 !important; padding: 4px !important; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .stLineChart {{ margin-top: -20px; }} 
    </style>
    
    <div class="status-bar">
        <div class="status-left">● {market_status} | SYS.OP.NORMAL</div>
        <div class="status-right">{time_str} | <span style="font-size:10px;">{date_str}</span></div>
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
    "XLP", "XLU", "XLV", "XLY", "XME", "XOP", "XRT", "XSD", "XTN", "XT"
]
ALL_SYMBOLS = TICKERS + BENCHMARKS

# 3. Data Engine
@st.cache_data(ttl=3600)
def fetch_data():
    # We now need High and Low data for ATR and ADX
    data = yf.download(ALL_SYMBOLS, period="1y", progress=False)
    return data['Close'], data['High'], data['Low'], data['Volume']

def calculate_factors(closes, highs, lows, volumes, current_year):
    results = []
    spy_p = closes["SPY"].dropna()
    
    # 1. Macro Kill Switch Check
    vix_close = closes["^VIX"].dropna().iloc[-1]
    vix_halt = vix_close > 30 # Trigger risk-off if VIX spikes
    
    for ticker in TICKERS:
        try:
            p = closes[ticker].dropna()
            h = highs[ticker].dropna()
            l = lows[ticker].dropna()
            v = volumes[ticker].dropna()
            if len(p) < 200: continue
            
            # Basic Returns
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
            
            # Advanced Risk: ATR & Trailing Stop
            high_low = h - l
            high_close = np.abs(h - p.shift())
            low_close = np.abs(l - p.shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            
            peak_20d = p.tail(20).max()
            trailing_stop = peak_20d - (2.5 * atr)
            
            # Advanced Risk: ADX (Trend Strength Proxy via Pandas)
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
                'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
            })
        except: continue
            
    df = pd.DataFrame(results).set_index('TKR')
    f = ['RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF'] # Excluded ADX from Z-score, it's a hard filter
    z = (df[f] - df[f].mean()) / df[f].std()
    
    df['SCORE'] = (z['RAM']*.25 + z['REL_STR']*.20 + z['ROC_AC']*.20 + z['50D_SLP']*.20 + z['VOL_CF']*.15) * 100
    df = df.sort_values(by='SCORE', ascending=False)
    df['RNK'] = range(1, len(df) + 1)
    
    signals = []
    for idx, row in df.iterrows():
        # Elite Absolute Alignment: Requires Trend (ADX > 25)
        fits_all_parameters = (
            row['Above_200'] and row['RAM'] > 0 and row['REL_STR'] > 0 and 
            row['ROC_AC'] > 0 and row['50D_SLP'] > 0 and row['VOL_CF'] >= 1.2 and
            row['ADX'] > 25
        )
        
        if vix_halt:
            signals.append("HALT (VIX)") # Macro Kill Switch
        elif not row['Above_200'] or row['PRICE'] < row['STOP_PRC']: 
            signals.append("STRONG SELL" if row['RNK'] > 15 else "SELL")
        elif fits_all_parameters and row['RNK'] <= 10:
            signals.append("STRONG BUY")
        elif row['RNK'] <= 10:
            signals.append("BUY")
        elif 10 < row['RNK'] <= 15:
            signals.append("HOLD")
        else: 
            signals.append("SELL")
            
    df['SIGNAL'] = signals
    return df, vix_halt, vix_close

with st.spinner('SYNCING ELITE DATA...'):
    c, h, l, v = fetch_data()
    df, vix_halt, vix_close = calculate_factors(c, h, l, v, now_est.year)

# 4. Interface Layout: Top Panels
col1, col2 = st.columns([1.2, 1.8]) 

with col1:
    vix_display = f"<span style='color:red;'>HALT TRIGGERED (VIX: {vix_close:.2f})</span>" if vix_halt else f"<span style='color:#00FF00;'>SAFE (VIX: {vix_close:.2f})</span>"
    st.markdown(f"""
        <div class="bbg-panel">
            <div class="bbg-header">SYSTEM ARCHITECTURE</div>
            <table>
                <tr><th>Component</th><th class="td-right">Status</th></tr>
                <tr><td>Macro Regime (VIX < 30)</td><td class="td-right">{vix_display}</td></tr>
                <tr><td>Chop Filter (ADX > 25)</td><td class="td-right">ACTIVE</td></tr>
                <tr><td>Dynamic Exit (2.5x ATR)</td><td class="td-right">ACTIVE</td></tr>
                <tr><td>Vol Confirmation (>1.2x)</td><td class="td-right">ACTIVE</td></tr>
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
        text_color = "#000000" if color == "#00FF00" else "#FFFFFF"
        heatmap_html += f'<div class="heat-cell" style="background-color:{color}; color:{text_color};">{ticker}<br>{val:.1f}%</div>'
    heatmap_html += '</div></div>'
    st.markdown(heatmap_html, unsafe_allow_html=True)

# 5. Interface Layout: Bottom Panel
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)

display_df = df[['RNK', 'SIGNAL', 'PRICE', 'STOP_PRC', 'ADX', 'SCORE', 'YTD', 'RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF']].copy()

def style_signals(val):
    if 'STRONG BUY' in val: color = '#00FF00'
    elif 'BUY' in val: color = '#66FF66'
    elif 'HOLD' in val: color = '#FFFF00'
    elif 'HALT' in val: color = '#FF00FF'
    else: color = '#FF0000'
    return f'color: {color}; font-weight: bold;'

st.dataframe(display_df.round(2).style.map(style_signals, subset=['SIGNAL']), use_container_width=True, height=350)
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
