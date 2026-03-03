import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# 1. Page & CSS Configuration (Bloomberg TV Aesthetic)
st.set_page_config(page_title="Quant Terminal", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Global Base */
    .stApp { background-color: #0c0c0c; }
    * { font-family: 'Helvetica', sans-serif !important; color: #FFFFFF; }
    
    /* Bloomberg Orange Panels */
    .bbg-panel {
        border: 2px solid #FF8C00;
        background-color: #000000;
        padding: 12px;
        margin-bottom: 16px;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
    }
    .bbg-header {
        background-color: #FF8C00;
        color: #000000 !important;
        font-weight: 900;
        padding: 6px 10px;
        margin: -12px -12px 12px -12px;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Data Highlights */
    .tkr-up { color: #00FF00 !important; font-weight: bold; }
    .tkr-down { color: #FF0000 !important; font-weight: bold; }
    .tkr-neutral { color: #FFFF00 !important; font-weight: bold; }
    
    /* Table Styling Overrides */
    .dataframe { font-size: 11px !important; text-align: right; }
    .dataframe th { background-color: #111111 !important; color: #FF8C00 !important; border-bottom: 2px solid #FF8C00 !important; }
    .dataframe td { border-bottom: 1px solid #333333 !important; }
    
    /* Hide Streamlit default UI elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
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
def fetch_and_calculate():
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
                
            ret_1m_raw = p.pct_change(21).iloc[-1] * 100
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
                'TKR': ticker, 'Ret_1M': ret_1m_raw, 'Day_Change': day_change, 'RAM': ram, 
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

@st.cache_data(ttl=3600)
def fetch_news(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        news = t.news[:3]
        return [{"title": n['title'], "publisher": n['publisher']} for n in news]
    except:
        return []

# Execute Data Fetch
with st.spinner('SYNCING GLOBAL DATA...'):
    df, bench_stats = fetch_and_calculate()
    top_ticker = df.index[0] if not df.empty else "SPY"
    news_feed = fetch_news(top_ticker)

# 4. App Layout (Vertical Mobile Optimization)

st.markdown('<div style="color:#FF8C00; font-size:18px; font-weight:900; margin-bottom:15px; border-bottom:2px solid #333; padding-bottom:5px;">SYS.OP.NORMAL // ACTIVE</div>', unsafe_allow_html=True)

# Panel 1: Benchmarks & Macro Breadth
st.markdown('<div class="bbg-panel"><div class="bbg-header">MACRO BENCHMARKS & BREADTH</div>', unsafe_allow_html=True)
b_cols = st.columns(4)
for i, b in enumerate(bench_stats):
    name = b['ticker'].replace("^", "")
    color = "tkr-up" if b['change'] > 0 else "tkr-down" if b['change'] < 0 else "tkr-neutral"
    sign = "+" if b['change'] > 0 else ""
    with b_cols[i % 4]:
        st.markdown(f"<div style='text-align:center;'><span style='font-size:12px; color:#aaa;'>{name}</span><br><span style='font-size:14px; font-weight:bold;'>{b['price']:.2f}</span><br><span class='{color}' style='font-size:11px;'>{sign}{b['change']:.2f}%</span></div>", unsafe_allow_html=True)

breadth = (df['Above_200'].sum() / len(df)) * 100
st.markdown(f"<div style='margin-top:10px; border-top:1px solid #333; padding-top:8px; text-align:center; font-size:12px;'>UNIVERSE > 200DMA: <span style='color:{'#00FF00' if breadth > 50 else '#FF0000'}; font-weight:bold;'>{breadth:.1f}%</span></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Panel 2: Intraday Velocity Movers
st.markdown('<div class="bbg-panel"><div class="bbg-header">INTRADAY VELOCITY MOVERS</div>', unsafe_allow_html=True)
movers_df = df.sort_values(by='Day_Change', ascending=False)
m_cols = st.columns(2)
with m_cols[0]:
    st.markdown("<span style='color:#00FF00; font-size:12px;'>▲ TOP GAINERS</span>", unsafe_allow_html=True)
    for t, row in movers_df.head(3).iterrows():
        st.markdown(f"<div style='font-size:12px;'>**{t}** <span class='tkr-up'>+{row['Day_Change']:.2f}%</span></div>", unsafe_allow_html=True)
with m_cols[1]:
    st.markdown("<span style='color:#FF0000; font-size:12px;'>▼ TOP LOSERS</span>", unsafe_allow_html=True)
    for t, row in movers_df.tail(3).iterrows():
        st.markdown(f"<div style='font-size:12px;'>**{t}** <span class='tkr-down'>{row['Day_Change']:.2f}%</span></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Panel 3: Performance Heatmap
st.markdown('<div class="bbg-panel"><div class="bbg-header">1-MONTH PERFORMANCE HEATMAP</div>', unsafe_allow_html=True)
h_cols = st.columns(6) 
heat_df = df.sort_values(by='Ret_1M', ascending=False)
for i, (ticker, row) in enumerate(heat_df.iterrows()):
    val = row['Ret_1M']
    color = "#00FF00" if val > 5 else "#006600" if val > 0 else "#660000" if val > -5 else "#FF0000"
    text_color = "#000000" if color == "#00FF00" else "#FFFFFF"
    with h_cols[i % 6]:
        st.markdown(f"""
        <div style="background-color: {color}; color: {text_color}; text-align: center; padding: 4px; margin-bottom: 4px; border-radius: 2px; font-size: 9px; font-weight:bold;">
            {ticker}<br>{val:.1f}%
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Panel 4: Algorithmic Top Picks & News
st.markdown(f'<div class="bbg-panel"><div class="bbg-header">TARGET ACQUISITION: {top_ticker}</div>', unsafe_allow_html=True)
st.markdown(f"<div style='font-size:13px; margin-bottom:8px;'>**{top_ticker}** is currently ranked #1 with a system score of {df.loc[top_ticker, 'SCORE']:.1f}.</div>", unsafe_allow_html=True)
if news_feed:
    for item in news_feed:
        st.markdown(f"<div style='font-size:11px; margin-bottom:4px; padding-left:8px; border-left:2px solid #FF8C00;'>**{item['publisher']}**: {item['title']}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Panel 5: Main Quant Ledger
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)
display_df = df[['RNK', 'SIGNAL', 'PRICE', 'SCORE', 'RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF', 'MAX_DD']].copy()
# Map colors to signals for the dataframe display
def style_signals(val):
    color = '#00FF00' if 'STRONG BUY' in val else '#66FF66' if 'BUY' in val else '#FFFF00' if 'HOLD' in val else '#FF0000'
    return f'color: {color}; font-weight: bold;'

st.dataframe(display_df.round(2).style.map(style_signals, subset=['SIGNAL']), use_container_width=True, height=400)
st.markdown('</div>', unsafe_allow_html=True)
