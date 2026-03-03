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
    
    /* Top Status Bar */
    .status-bar {{
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 2px solid #00FFFF; padding: 5px 0px; margin-top: -50px; margin-bottom: 10px;
    }}
    .status-left {{ color: {status_color}; font-weight: bold; font-size: 14px; text-transform: uppercase; }}
    .status-right {{ color: #00FFFF; text-align: right; font-weight: bold; font-size: 14px; }}
    
    /* Compact Panels */
    .bbg-panel {{
        border: 1px solid #444; background-color: #111; padding: 8px; margin-bottom: 10px; border-radius: 2px;
    }}
    .bbg-header {{
        color: #FFFFFF; font-weight: bold; font-size: 14px; text-transform: uppercase; 
        border-bottom: 1px solid #444; padding-bottom: 4px; margin-bottom: 8px;
    }}
    
    /* Tables */
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    th {{ text-align: left; color: #aaa; border-bottom: 1px solid #333; padding: 4px; }}
    td {{ padding: 4px; border-bottom: 1px solid #222; }}
    .td-right {{ text-align: right; }}
    
    /* Signal Colors */
    .c-strong-buy {{ color: #00FF00; font-weight: bold; }}
    .c-buy {{ color: #66FF66; font-weight: bold; }}
    .c-hold {{ color: #FFFF00; font-weight: bold; }}
    .c-sell {{ color: #FF6666; font-weight: bold; }}
    .c-strong-sell {{ color: #FF0000; font-weight: bold; }}
    
    /* Ticker Tape Bottom */
    .ticker-tape {{
        display: flex; justify-content: space-between; background-color: #111;
        border-top: 2px solid #333; padding: 5px 10px; font-size: 12px; font-weight: bold;
    }}
    
    /* Heatmap Grid */
    .heatmap-grid {{ display: grid; grid-template-columns: repeat(8, 1fr); gap: 1px; }}
    .heat-cell {{ text-align: center; padding: 4px 0px; font-size: 10px; font-weight: bold; }}
    
    /* Streamlit DataFrame Overrides */
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
    data = yf.download(ALL_SYMBOLS, period="1y", progress=False)
    return data['Close'], data['Volume']

def calculate_factors(prices, volumes, current_year):
    results = []
    spy_p = prices["SPY"].dropna()
    
    for ticker in TICKERS:
        try:
            p = prices[ticker].dropna()
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
            
            rolling_max = p.tail(126).cummax()
            max_dd = ((p.tail(126) - rolling_max) / rolling_max).min()
            
            results.append({
                'TKR': ticker, 'PRICE': p.iloc[-1], 'YTD': ytd_ret, 'RAM': ram, 
                'ROC_AC': roc_accel, 'REL_STR': rel_strength, '50D_SLP': sma_50_slope, 
                'VOL_CF': vol_conf, 'MAX_DD': max_dd, 'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
            })
        except: continue
            
    df = pd.DataFrame(results).set_index('TKR')
    f = ['RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF', 'MAX_DD']
    z = (df[f] - df[f].mean()) / df[f].std()
    
    df['SCORE'] = (z['RAM']*.25 + z['REL_STR']*.20 + z['ROC_AC']*.20 + z['50D_SLP']*.15 + z['VOL_CF']*.10 - z['MAX_DD']*.10) * 100
    df = df.sort_values(by='SCORE', ascending=False)
    df['RNK'] = range(1, len(df) + 1)
    
    signals = []
    for idx, row in df.iterrows():
        if not row['Above_200']: signals.append("STRONG SELL" if row['RNK'] > 15 else "SELL")
        elif row['RNK'] <= 10: signals.append("STRONG BUY")
        elif 10 < row['RNK'] <= 15: signals.append("HOLD")
        else: signals.append("SELL")
    df['SIGNAL'] = signals
    return df

with st.spinner('SYNCING GLOBAL DATA...'):
    raw_prices, raw_volumes = fetch_data()
    df = calculate_factors(raw_prices, raw_volumes, now_est.year)

# 4. Interface Layout: Top Panels (Visuals & Rules)
col1, col2 = st.columns([1.2, 1.8]) 

with col1:
    st.markdown("""
        <div class="bbg-panel">
            <div class="bbg-header">WEIGHTING THE FACTORS</div>
            <table>
                <tr><th>Factor</th><th class="td-right">Weight</th></tr>
                <tr><td>Risk-Adjusted Momentum (1M)</td><td class="td-right">25%</td></tr>
                <tr><td>Relative Strength vs SPY</td><td class="td-right">20%</td></tr>
                <tr><td>ROC Acceleration</td><td class="td-right">20%</td></tr>
                <tr><td>50DMA Slope</td><td class="td-right">15%</td></tr>
                <tr><td>Volume Confirmation</td><td class="td-right">10%</td></tr>
                <tr><td style="color:#00FFFF;">Drawdown Penalty</td><td class="td-right" style="color:#00FFFF;">-10%</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
        <div class="bbg-panel">
            <div class="bbg-header">ENTRY / EXIT SIGNALS</div>
            <table>
                <tr><th>Signal</th><th>Rule</th></tr>
                <tr><td class="c-strong-buy">STRONG BUY</td><td>Top 10 composite + Above 200DMA</td></tr>
                <tr><td class="c-buy">BUY</td><td>Ranks 11-15 + Above 200DMA</td></tr>
                <tr><td class="c-hold">HOLD</td><td>Was Top 10, slipped to 11-15</td></tr>
                <tr><td class="c-sell">SELL</td><td>Dropped out of top 15</td></tr>
                <tr><td class="c-strong-sell">STRONG SELL</td><td>Below 200DMA</td></tr>
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
                <span style="font-size:12px; color:#aaa;">Rank: #1 | Score: {df.loc[top_asset, 'SCORE']:.1f}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    chart_data = raw_prices[top_asset].dropna().tail(63)
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

# 5. Interface Layout: Bottom Panel (The Master Ledger)
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)

display_df = df[['RNK', 'SIGNAL', 'PRICE', 'SCORE', 'YTD', 'RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF', 'MAX_DD']].copy()

def style_signals(val):
    color = '#00FF00' if 'STRONG BUY' in val else '#66FF66' if 'BUY' in val else '#FFFF00' if 'HOLD' in val else '#FF0000'
    return f'color: {color}; font-weight: bold;'

st.dataframe(display_df.round(2).style.map(style_signals, subset=['SIGNAL']), use_container_width=True, height=350)
st.markdown('</div>', unsafe_allow_html=True)

# 6. Bottom Ticker Tape
tape_html = '<div class="ticker-tape">'
for b in BENCHMARKS:
    try:
        cur = raw_prices[b].dropna().iloc[-1]
        pct = ((cur - raw_prices[b].dropna().iloc[-2]) / raw_prices[b].dropna().iloc[-2]) * 100
        c_class = "c-strong-buy" if pct > 0 else "c-strong-sell"
        sym = b.replace("^", "")
        tape_html += f'<span>{sym} <span style="color:#FFF;">{cur:.2f}</span> <span class="{c_class}">{pct:+.2f}%</span></span>'
    except: pass
tape_html += '</div>'
st.markdown(tape_html, unsafe_allow_html=True)
