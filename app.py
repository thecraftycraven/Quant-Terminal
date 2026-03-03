import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from zoneinfo import ZoneInfo

# 1. Page & CSS Configuration (Bloomberg TV Aesthetic)
st.set_page_config(page_title="Quant Terminal", layout="wide", initial_sidebar_state="collapsed")

# Calculate Market Time & Status
est_zone = ZoneInfo('America/New_York')
now_est = datetime.datetime.now(est_zone)
time_str = now_est.strftime("%I:%M %p ET")
date_str = now_est.strftime("%b %d, %Y")

is_weekend = now_est.weekday() >= 5
is_open_hours = datetime.time(9, 30) <= now_est.time() <= datetime.time(16, 0)
market_status = "MARKET CLOSED" if is_weekend or not is_open_hours else "MARKET OPEN"
status_color = "#00FF00" if market_status == "MARKET OPEN" else "#FF0000"

st.markdown(f"""
    <style>
    /* Global Base */
    .stApp {{ background-color: #0c0c0c; }}
    * {{ font-family: 'Helvetica', sans-serif !important; color: #FFFFFF; }}
    
    /* Top Status Bar */
    .status-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1a1a1a;
        border-bottom: 2px solid #00FFFF;
        padding: 5px 10px;
        margin-top: -40px;
        margin-bottom: 15px;
        font-size: 12px;
        font-weight: bold;
    }}
    .status-indicator {{ color: {status_color}; }}
    .status-clock {{ color: #00FFFF; text-align: right; }}
    
    /* Bloomberg Orange Panels */
    .bbg-panel {{
        border: 2px solid #FF8C00;
        background-color: #000000;
        padding: 10px;
        margin-bottom: 16px;
    }}
    .bbg-header {{
        background-color: #FF8C00;
        color: #000000 !important;
        font-weight: 900;
        padding: 4px 8px;
        margin: -10px -10px 10px -10px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* Data Highlights */
    .tkr-up {{ color: #00FF00 !important; font-weight: bold; }}
    .tkr-down {{ color: #FF0000 !important; font-weight: bold; }}
    .tkr-neutral {{ color: #FFFFFF !important; font-weight: bold; }}
    
    /* 8-Column Heatmap Grid */
    .heatmap-grid {{
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 2px;
    }}
    .heat-cell {{
        text-align: center;
        padding: 6px 0px;
        font-size: 10px;
        font-weight: bold;
    }}
    
    /* Table Styling Overrides */
    .dataframe {{ font-size: 10px !important; text-align: right; }}
    .dataframe th {{ background-color: #111111 !important; color: #FF8C00 !important; border-bottom: 2px solid #FF8C00 !important; }}
    .dataframe td {{ border-bottom: 1px solid #333333 !important; padding: 4px !important; }}
    
    /* Hide Streamlit default UI elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    
    <div class="status-bar">
        <div class="status-indicator">● {market_status}</div>
        <div style="color: #FFA500; font-size: 14px;">QUANT TERMINAL ENGINE</div>
        <div class="status-clock">{time_str}<br><span style="font-size:9px; color:#aaa;">{date_str}</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. Universe Definition
BENCHMARKS = ["SPY", "QQQ", "^VIX", "^TNX"] 
TICKERS = [
    "AMLP", "BDRY", "BIER", "BJK", "BNGE", "CARZ", "CCRD", "COAL", "COPX", "CRAK", 
    "CRUZ", "DTCR", "EATZ", "FINX", "FIW", "GDX", "GERM", "GRID", "IAI", "IAK", 
    "IBB", "ICLN", "IEO", "IGV", "IHF", "IHI", "INDS", "ITA", "ITB", "IYC", "IYF", 
    "IYJ", "IYK", "IYM", "IYT", "IYW", "IYZ", "JETS", "KBWB", "KBWM", "KBWP", "KRE", 
    "LUXE", "METL", "MOO", "MXI", "NERD", "NURE", "OIH", "ONLN", "PAVE", "PBJ", 
    "PBS", "PEJ", "PHO", "PICK", "REET", "REM", "REZ", "RLTY", "RTH", "RTM", "RWR", 
    "SIL", "SKYY", "SLX", "SOCL", "SOXX", "VEGI", "VIS", "VNQ", "WOOD", "XBI", 
    "XLC", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XME", "XOP", "XRT", "XSD", "XTN", "XT"
]
ALL_SYMBOLS = TICKERS + BENCHMARKS

# 3. Data Engine
@st.cache_data(ttl=3600)
def fetch_and_calculate(current_year):
    data = yf.download(ALL_SYMBOLS, period="1y", progress=False)
    prices = data['Close']
    volumes = data['Volume']
    
    results = []
    bench_stats = []
    
    # Process Benchmarks
    for b in BENCHMARKS:
        try:
            current = prices[b].dropna().iloc[-1]
            prev = prices[b].dropna().iloc[-2]
            pct_change = ((current - prev) / prev) * 100
            bench_stats.append({'ticker': b, 'price': current, 'change': pct_change})
        except:
            pass

    # Process Quant Engine
    for ticker in TICKERS:
        try:
            p = prices[ticker].dropna()
            v = volumes[ticker].dropna()
            spy_p = prices["SPY"].dropna()
            
            if len(p) < 200: continue
            
            # YTD Calculation
            p_year = p[p.index.year == current_year]
            if len(p_year) > 0:
                ytd_ret = ((p.iloc[-1] - p_year.iloc[0]) / p_year.iloc[0]) * 100
            else:
                ytd_ret = 0
                
            ret_1m = p.pct_change(21).iloc[-1]
            vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
            ram = ret_1m / vol_1m if vol_1m != 0 else 0
            
            roc_20 = p.pct_change(20).iloc[-1]
            roc_60 = p.pct_change(60).iloc[-1]
            roc_accel = roc_20 - (roc_60 / 3)
            
            ret_3m = p.pct_change(63).iloc[-1]
            spy_ret_3m = spy_p.pct_change(63).iloc[-1]
            rel_strength = ret_3m - spy_ret_3m
            
            sma_200 = p.rolling(200).mean().iloc[-1]
            sma_50 = p.rolling(50).mean()
            sma_50_slope = (sma_50.iloc[-1] - sma_50.iloc[-21]) / sma_50.iloc[-21]
            above_200 = p.iloc[-1] > sma_200
            
            vol_20 = v.rolling(20).mean().iloc[-1]
            vol_90 = v.rolling(90).mean().iloc[-1]
            vol_conf = vol_20 / vol_90 if vol_90 != 0 else 1
            
            rolling_max = p.tail(126).cummax()
            max_dd = ((p.tail(126) - rolling_max) / rolling_max).min()
            
            day_change = ((p.iloc[-1] - p.iloc[-2]) / p.iloc[-2]) * 100
            
            results.append({
                'TKR': ticker, 'YTD_Ret': ytd_ret, 'Day_Change': day_change, 'RAM': ram, 
                'ROC_AC': roc_accel, 'REL_STR': rel_strength, 
                '50D_SLP': sma_50_slope, 'VOL_CF': vol_conf, 
                'MAX_DD': max_dd, 'Above_200': above_200, 'PRICE': p.iloc[-1]
            })
        except Exception:
            continue
            
    df = pd.DataFrame(results).set_index('TKR')
    factors = ['RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF', 'MAX_DD']
    z_scores = (df[factors] - df[factors].mean()) / df[factors].std()
                
    df['SCORE'] = (
        (z_scores['RAM'] * 0.25) + (z_scores['REL_STR'] * 0.20) +
        (z_scores['ROC_AC'] * 0.20) + (z_scores['50D_SLP'] * 0.15) +
        (z_scores['VOL_CF'] * 0.10) + (z_scores['MAX_DD'] * -0.10)
    ) * 100
    
    df = df.sort_values(by='SCORE', ascending=False)
    df['RNK'] = range(1, len(df) + 1)
    
    signals = []
    for idx, row in df.iterrows():
        if not row['Above_200']: signals.append("STRONG SELL" if row['RNK'] > 15 else "SELL")
        elif row['RNK'] <= 10: signals.append("STRONG BUY")
        elif 10 < row['RNK'] <= 15: signals.append("HOLD")
        else: signals.append("SELL")
            
    df['SIGNAL'] = signals
    return df, bench_stats

# Execute Data Fetch
with st.spinner('SYNCING GLOBAL DATA...'):
    df, bench_stats = fetch_and_calculate(now_est.year)

# Panel 1: Benchmarks
st.markdown('<div class="bbg-panel"><div class="bbg-header">GLOBAL BENCHMARKS</div>', unsafe_allow_html=True)
b_cols = st.columns(4)
for i, b in enumerate(bench_stats):
    name = b['ticker'].replace("^", "")
    color = "tkr-up" if b['change'] > 0 else "tkr-down" if b['change'] < 0 else "tkr-neutral"
    sign = "+" if b['change'] > 0 else ""
    with b_cols[i % 4]:
        st.markdown(f"<div style='text-align:center;'><span style='font-size:12px; color:#aaa;'>{name}</span><br><span style='font-size:13px; font-weight:bold;'>{b['price']:.2f}</span><br><span class='{color}' style='font-size:11px;'>{sign}{b['change']:.2f}%</span></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Panel 2: 8-Column YTD Heatmap
st.markdown('<div class="bbg-panel"><div class="bbg-header">YTD PERFORMANCE HEATMAP</div>', unsafe_allow_html=True)
heat_df = df.sort_values(by='YTD_Ret', ascending=False)

heatmap_html = '<div class="heatmap-grid">'
for ticker, row in heat_df.iterrows():
    val = row['YTD_Ret']
    color = "#00FF00" if val > 15 else "#006600" if val > 0 else "#660000" if val > -10 else "#FF0000"
    text_color = "#000000" if color == "#00FF00" else "#FFFFFF"
    
    # FIX: Generating raw HTML string on a single line to bypass the Markdown code block trigger
    heatmap_html += f'<div class="heat-cell" style="background-color: {color}; color: {text_color};">{ticker}<br>{val:.1f}%</div>'
    
heatmap_html += '</div></div>'
st.markdown(heatmap_html, unsafe_allow_html=True)

# Panel 3: Main Quant Ledger
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)
display_df = df[['RNK', 'SIGNAL', 'PRICE', 'SCORE', 'YTD_Ret', 'RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF']].copy()

def style_signals(val):
    color = '#00FF00' if 'STRONG BUY' in val else '#66FF66' if 'BUY' in val else '#FFFF00' if 'HOLD' in val else '#FF0000'
    return f'color: {color}; font-weight: bold;'

st.dataframe(display_df.round(2).style.map(style_signals, subset=['SIGNAL']), use_container_width=True, height=500)
st.markdown('</div>', unsafe_allow_html=True)
