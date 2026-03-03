import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. Bloomberg Terminal UI Configuration
st.set_page_config(page_title="Quant Terminal", layout="wide", initial_sidebar_state="collapsed")

# Inject Custom CSS for Helvetica, Black Background, and Bloomberg Colors
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    * { font-family: 'Helvetica', sans-serif !important; font-weight: bold !important; color: #FFFFFF; }
    h1, h2, h3 { color: #FF9900 !important; text-transform: uppercase; }
    .dataframe { font-size: 12px !important; text-align: right; }
    .dataframe th { background-color: #000000 !important; color: #FF9900 !important; border-bottom: 2px solid #FF9900 !important; text-align: right !important; }
    .dataframe td { border-bottom: 1px solid #333333 !important; }
    .buy-signal { color: #00FF00 !important; }
    .sell-signal { color: #FF0000 !important; }
    .hold-signal { color: #FFFF00 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("SYS.OP.NORMAL // QUANT TERMINAL")

# 2. Universe Definition
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
BENCHMARK = "SPY"
ALL_SYMBOLS = TICKERS + [BENCHMARK]

# 3. Data Engine (Cached to prevent reloading on every tap)
@st.cache_data(ttl=3600) # Caches data for 1 hour
def fetch_and_calculate():
    data = yf.download(ALL_SYMBOLS, period="1y", progress=False)
    prices = data['Close']
    volumes = data['Volume']
    
    results = []
    for ticker in TICKERS:
        try:
            p = prices[ticker].dropna()
            v = volumes[ticker].dropna()
            spy_p = prices[BENCHMARK].dropna()
            
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
            sma_50_current = sma_50.iloc[-1]
            sma_50_past = sma_50.iloc[-21]
            sma_50_slope = (sma_50_current - sma_50_past) / sma_50_past
            above_200 = p.iloc[-1] > sma_200
            
            vol_20 = v.rolling(20).mean().iloc[-1]
            vol_90 = v.rolling(90).mean().iloc[-1]
            vol_conf = vol_20 / vol_90 if vol_90 != 0 else 1
            
            rolling_max = p.tail(126).cummax()
            max_dd = ((p.tail(126) - rolling_max) / rolling_max).min()
            
            results.append({
                'TKR': ticker, 'Ret_1M': ret_1m_raw, 'RAM': ram, 
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
    return df

# Run the engine
with st.spinner('Downloading Market Data...'):
    df = fetch_and_calculate()

# 4. Display Heatmap (Using Streamlit Columns)
st.subheader("1-MONTH PERFORMANCE HEATMAP")
cols = st.columns(6) # 6 columns for mobile screen fit
heat_df = df.sort_values(by='Ret_1M', ascending=False)

for i, (ticker, row) in enumerate(heat_df.iterrows()):
    val = row['Ret_1M']
    color = "#00FF00" if val > 5 else "#006600" if val > 0 else "#660000" if val > -5 else "#FF0000"
    text_color = "#000000" if color == "#00FF00" else "#FFFFFF"
    
    with cols[i % 6]:
        st.markdown(f"""
        <div style="background-color: {color}; color: {text_color}; text-align: center; padding: 5px; margin-bottom: 5px; border-radius: 3px; font-size: 10px;">
            {ticker}<br>{val:.1f}%
        </div>
        """, unsafe_allow_html=True)

# 5. Display Main Ledger
st.subheader("QUANTITATIVE FACTOR LEDGER")
# Format dataframe for clean display
display_df = df[['RNK', 'SIGNAL', 'PRICE', 'SCORE', 'RAM', 'ROC_AC', 'REL_STR', '50D_SLP', 'VOL_CF', 'MAX_DD']].copy()
display_df = display_df.round(2)

# Display the interactive dataframe
st.dataframe(display_df, use_container_width=True, height=600)
