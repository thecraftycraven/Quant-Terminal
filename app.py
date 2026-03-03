import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. Page & CSS Configuration (Bloomberg TV Aesthetic)
st.set_page_config(page_title="Quant Terminal", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Global Base */
    .stApp { background-color: #0c0c0c; }
    * { font-family: 'Helvetica', sans-serif !important; color: #FFFFFF; }
    
    /* Bloomberg Orange Panels */
    .bbg-panel {
        border: 3px solid #FF8C00;
        background-color: #000000;
        padding: 10px;
        margin-bottom: 15px;
        border-radius: 2px;
    }
    .bbg-header {
        background-color: #FF8C00;
        color: #000000 !important;
        font-weight: bold;
        padding: 5px;
        margin: -10px -10px 10px -10px;
        font-size: 14px;
        text-transform: uppercase;
    }
    
    /* Ticker Text Styles */
    .tkr-up { color: #00FF00 !important; font-weight: bold; }
    .tkr-down { color: #FF0000 !important; font-weight: bold; }
    .tkr-neutral { color: #FFFFFF !important; }
    
    /* Hide Streamlit default UI elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Universes
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

@st.cache_data(ttl=3600)
def fetch_data():
    all_data = yf.download(TICKERS + BENCHMARKS, period="1y", progress=False)
    return all_data['Close'], all_data['Volume']

@st.cache_data(ttl=3600)
def fetch_news(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        news = t.news[:3] # Get top 3 articles
        return [{"title": n['title'], "publisher": n['publisher']} for n in news]
    except Exception:
        return [{"title": "News feed unavailable.", "publisher": "System"}]

# 3. Execution
with st.spinner('SYNCING GLOBAL DATA...'):
    prices, volumes = fetch_data()

# Process Benchmarks
bench_stats = []
for b in BENCHMARKS:
    try:
        current = prices[b].iloc[-1]
        prev = prices[b].iloc[-2]
        pct_change = ((current - prev) / prev) * 100
        bench_stats.append({'ticker': b, 'price': current, 'change': pct_change})
    except:
        pass

# Process Quant Engine (Simplified for UI Focus)
results = []
for t in TICKERS:
    try:
        p = prices[t].dropna()
        if len(p) < 200: continue
        current_p = p.iloc[-1]
        prev_p = p.iloc[-2]
        day_change = ((current_p - prev_p) / prev_p) * 100
        
        # 1M RAM approximation
        ret_1m = p.pct_change(21).iloc[-1]
        vol_1m = p.pct_change().tail(21).std() * np.sqrt(252)
        ram = ret_1m / vol_1m if vol_1m != 0 else 0
        
        results.append({'Ticker': t, 'Price': current_p, 'Day_Change': day_change, 'RAM': ram})
    except:
        continue

df = pd.DataFrame(results).set_index('Ticker')
df = df.sort_values(by='RAM', ascending=False)
top_signal = df.index[0] if not df.empty else "SPY"
news_feed = fetch_news(top_signal)

# 4. Bloomberg UI Layout Setup
col_main, col_right = st.columns([3, 1])

with col_right:
    # Top Right: Benchmarks
    st.markdown('<div class="bbg-panel"><div class="bbg-header">GLOBAL BENCHMARKS</div>', unsafe_allow_html=True)
    for b in bench_stats:
        color_class = "tkr-up" if b['change'] > 0 else "tkr-down" if b['change'] < 0 else "tkr-neutral"
        sign = "+" if b['change'] > 0 else ""
        name = b['ticker'].replace("^", "")
        st.markdown(f"""
            <div style="margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;">
                <span style="font-weight:bold; font-size:16px;">{name}</span><br>
                <span style="font-size:18px;">{b['price']:.2f}</span> 
                <span class="{color_class}" style="font-size:14px; float:right;">{sign}{b['change']:.2f}%</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    # Top Left: Position Movers
    st.markdown('<div class="bbg-panel"><div class="bbg-header">INTRADAY VELOCITY MOVERS</div>', unsafe_allow_html=True)
    movers_df = df.sort_values(by='Day_Change', ascending=False)
    
    m_cols = st.columns(2)
    with m_cols[0]:
        st.markdown("**TOP GAINERS**")
        for t, row in movers_df.head(3).iterrows():
            st.markdown(f"<span class='tkr-up'>{t}</span>: +{row['Day_Change']:.2f}%", unsafe_allow_html=True)
    with m_cols[1]:
        st.markdown("**TOP LOSERS**")
        for t, row in movers_df.tail(3).iterrows():
            st.markdown(f"<span class='tkr-down'>{t}</span>: {row['Day_Change']:.2f}%", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom Left: Top News
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">TOP NEWS: {top_signal} (HIGHEST QUANT SCORE)</div>', unsafe_allow_html=True)
    for item in news_feed:
        st.markdown(f"▶ **{item['publisher']}**: {item['title']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom Center: The Main Ledger
    st.markdown('<div class="bbg-panel"><div class="bbg-header">SYSTEMATIC ENGINE LEDGER</div>', unsafe_allow_html=True)
    display_df = df.copy()
    display_df['Price'] = display_df['Price'].round(2)
    display_df['Day_Change'] = display_df['Day_Change'].round(2)
    display_df['RAM Score'] = display_df['RAM'].round(2)
    st.dataframe(display_df[['Price', 'Day_Change', 'RAM Score']].head(20), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
