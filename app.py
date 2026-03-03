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
    .ledger-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #333; background: #000; margin-bottom: 40px; }}
    .ledger-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    .ledger-table th {{ position: sticky; top: 0; background-color: #111; color: #FF6600; z-index: 10; border-bottom: 2px solid #FF6600; padding: 8px; text-align: left; }}
    .ledger-table td {{ padding: 8px; border-bottom: 1px solid #222; text-align: left; font-family: monospace; font-size: 12px; }}
    .ledger-table td.num {{ text-align: right; }}
    .ledger-table tr:hover {{ background-color: #1A1A1A; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .stLineChart {{ margin-top: -15px; }} 
    </style>
    
    <div class="status-bar">
        <div class="status-left">● {market_status} | SYS.OP.NORMAL</div>
        <div class="status-right">{time_str} | <span style="font-size:10px; color:#888;">{date_str}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DEFINITIVE SECTOR-MAPPED UNIVERSE
# ==========================================
TICKER_SECTORS = {
    # ENERGY
    "OIH": "Energy Services", "XLE": "Oil & Gas",
    # MATERIALS
    "XLB": "Chemicals", "XME": "Metals & Mining", "WOOD": "Timber & Forest",
    # INDUSTRIALS
    "XLI": "Capital Goods", "IYT": "Transportation",
    # CONSUMER DISCRETIONARY
    "CARZ": "Automobiles", "XLY": "Cons Durables", "PEJ": "Cons Services", "XRT": "Retailing",
    # CONSUMER STAPLES
    "XLP": "Food Retailing", "PBJ": "Food & Bev",
    # HEALTH CARE
    "IHI": "Health Equip", "XBI": "Biotech/Pharma",
    # FINANCIALS
    "KBE": "Banks", "IAI": "Diversified Fin", "KIE": "Insurance",
    # INFORMATION TECHNOLOGY
    "IGV": "Software/Services", "SMH": "Semiconductors",
    # COMMUNICATION SERVICES
    "IYZ": "Telecom Services", "XLC": "Media/Ent",
    # UTILITIES
    "XLU": "Electric Utilities", "FCG": "Gas Utilities", "IDU": "Multi-Utilities", "PHO": "Water Utilities", "ICLN": "Renewable Elec",
    # REAL ESTATE
    "VNQ": "Equity REITs", "REET": "RE Mgmt & Dev",
    # GLOBAL OVERLAYS
    "EFA": "Developed Markets", "VWO": "Emerging Markets", "INDY": "India", "KWEB": "China",
    # UNCORRELATED ASSETS
    "DBA": "Ag Commodities", "PDBC": "Broad Commodities", "UUP": "US Dollar Index", "VIXY": "Tail Risk", "SLV": "Silver", "TIP": "Inflation Bonds", "DBB": "Base Metals", "CWB": "Convertible Bonds",
    # MACRO
    "IAU": "Gold", "FBTC": "Bitcoin",
    # SAFE HARBORS
    "BIL": "Cash/T-Bills", "IEF": "Intermediate Bonds", "TLT": "Long Bonds"
}

TICKERS = list(TICKER_SECTORS.keys())
BENCHMARKS = ["SPY", "QQQ", "^VIX", "DIA"] 
ALL_SYMBOLS = TICKERS + BENCHMARKS

# ==========================================
# 3. DATA ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data():
    # pull 2y to ensure 200DMA works for older assets
    data = yf.download(ALL_SYMBOLS, period="2y", progress=False) 
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
            rel_strength = p.pct_change(63).iloc[-1] - spy_p.pct_change(63).iloc[-1]
            sma_50 = p.rolling(50).mean()
            sma_50_slope = (sma_50.iloc[-1] - sma_50.iloc[-21]) / sma_50.iloc[-21]
            vol_conf = (v.rolling(20).mean().iloc[-1] / v.rolling(90).mean().iloc[-1]) if v.rolling(90).mean().iloc[-1] != 0 else 1
            atr = (h - l).rolling(14).mean().iloc[-1]
            stop_prc = p.tail(20).max() - (2.5 * atr)
            
            tr = pd.concat([h - l, np.abs(h - p.shift()), np.abs(l - p.shift())], axis=1).max(axis=1)
            up = h - h.shift(1); dw = l.shift(1) - l
            tr14 = tr.rolling(14).sum()
            plus_di = 100 * (pd.Series(np.where((up > dw) & (up > 0), up, 0), index=p.index).rolling(14).sum() / tr14)
            minus_di = 100 * (pd.Series(np.where((dw > up) & (dw > 0), dw, 0), index=p.index).rolling(14).sum() / tr14)
            adx = (100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)).rolling(14).mean().iloc[-1]
            
            results.append({
                'TKR': ticker, 'SECTOR': TICKER_SECTORS[ticker], 'PRICE': p.iloc[-1], 'YTD': ytd_ret, 'RAM': ram, 
                'REL_STR': rel_strength, '50D_SLP': sma_50_slope, 'VOL_CF': vol_conf, 'ADX': adx, 'STOP_PRC': stop_prc, 
                'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
            })
        except: continue
            
    df = pd.DataFrame(results).set_index('TKR')
    f = ['RAM', 'REL_STR', '50D_SLP', 'VOL_CF'] 
    z = (df[f] - df[f].mean()) / df[f].std()
    df['SCORE'] = (z['RAM']*.25 + z['REL_STR']*.25 + z['50D_SLP']*.25 + z['VOL_CF']*.25) * 100
    df = df.sort_values(by='SCORE', ascending=False)
    df['RNK'] = range(1, len(df) + 1)
    
    signals, reasons = [], []
    for idx, row in df.iterrows():
        reason = ""
        if not row['Above_200']: reason = "Below 200DMA"
        elif row['ADX'] <= 25: reason = f"Choppy (ADX:{row['ADX']:.1f})"
        elif row['VOL_CF'] < 1.1: reason = "Low Vol"
        
        if vix_halt: signals.append("HALT"); reasons.append("VIX > 30")
        elif reason == "" and row['RNK'] <= 5: signals.append("STRONG BUY"); reasons.append("PASSED")
        elif row['RNK'] <= 10: signals.append("HOLD"); reasons.append("Buffer")
        else: signals.append("SELL"); reasons.append(reason if reason else f"Rank #{row['RNK']}")
            
    df['SIGNAL'] = signals; df['REASON'] = reasons
    return df, vix_halt, vix_close

with st.spinner('SYNCING QUANTITATIVE ENGINE...'):
    c, h, l, v = fetch_data()
    df, vix_halt, vix_close = calculate_factors(c, h, l, v, now_est.year)

# ==========================================
# 4. INTERFACE LAYOUT
# ==========================================
col1, col2 = st.columns([1.2, 1.8]) 

with col1:
    v_color = "red" if vix_halt else "#00FF00"
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">SYSTEM ARCHITECTURE</div><table><tr><td>Macro Regime (VIX)</td><td class="td-right" style="color:{v_color};">{vix_close:.2f}</td></tr></table></div>', unsafe_allow_html=True)
    st.markdown('<div class="bbg-panel"><div class="bbg-header">ELITE ENTRY / EXIT</div><table><tr><td class="c-strong-buy">STRONG BUY</td><td>Perfect Alignment (Top 5)</td></tr><tr><td class="c-buy">BUY</td><td>Top 5, imperfect setup</td></tr><tr><td class="c-hold">HOLD</td><td>Buffer zone (Rank 6-10)</td></tr></table></div>', unsafe_allow_html=True)
    
    top_5 = df.head(5).index.tolist()
    safe_harbor = ["BIL", "TLT", "IEF", "IAU"]
    regime, r_color = ("RISK-OFF (DEFENSIVE)", "#FBBF24") if any(x in top_5 for x in safe_harbor) else ("RISK-ON (GROWTH)", "#00FF00")
    st.markdown(f'<div class="bbg-panel"><div class="bbg-header">REGIME ROTATION RADAR</div><div style="text-align:center; padding: 10px 0;"><span style="font-size:16px; font-weight:bold; color:{r_color};">{regime}</span></div></div>', unsafe_allow_html=True)

with col2:
    sub1, sub2 = st.columns(2)
    with sub1:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">YTD EQUITY CURVE VS SPY</div>', unsafe_allow_html=True)
        spy_c = (c['SPY'] / c['SPY'][c.index.year == now_est.year][0] - 1) * 100
        st.line_chart(spy_c.tail(60), height=205)
        st.markdown('</div>', unsafe_allow_html=True)
    with sub2:
        st.markdown('<div class="bbg-panel" style="padding-bottom:0px;"><div class="bbg-header">LIVE MACRO: BLOOMBERG TV</div>', unsafe_allow_html=True)
        components.html('<iframe width="100%" height="205" src="https://www.youtube.com/embed/iEpJwprxDdk?autoplay=1&mute=1" frameborder="0" allowfullscreen></iframe>', height=210)
        st.markdown('</div>', unsafe_allow_html=True)

    # 4F. THE HEATMAP (ALL 46 ASSETS)
    st.markdown('<div class="bbg-panel"><div class="bbg-header">ETF YTD PERFORMANCE HEATMAP</div>', unsafe_allow_html=True)
    heat_df = df.sort_values('YTD', ascending=False)
    heatmap_html = '<div class="heatmap-grid">'
    for ticker, row in heat_df.iterrows():
        val = row['YTD']
        color = "#00FF00" if val > 15 else "#006600" if val > 0 else "#660000" if val > -10 else "#FF0000"
        heatmap_html += f'<div class="heat-cell" style="background-color:{color}; color:{"#000" if color=="#00FF00" else "#FFF"};">{ticker}<br>{val:.1f}%</div>'
    st.markdown(heatmap_html + '</div></div>', unsafe_allow_html=True)

# ==========================================
# 5. CUSTOM HTML LEDGER (RANK, TKR, SECTOR)
# ==========================================
st.markdown('<div class="bbg-panel"><div class="bbg-header">QUANTITATIVE FACTOR LEDGER</div>', unsafe_allow_html=True)
ledger_html = '<div class="ledger-container"><table class="ledger-table"><thead><tr><th>RNK</th><th>TKR</th><th>SECTOR</th><th>SIGNAL</th><th>REASON</th><th>PRICE</th><th>YTD</th><th>SCORE</th></tr></thead><tbody>'
for tkr, row in df.iterrows():
    sig = row['SIGNAL']
    s_col = '#00FF00' if 'BUY' in sig else '#FBBF24' if 'HOLD' in sig else '#FF0000'
    ledger_html += f'<tr><td>{row["RNK"]}</td><td style="font-weight:bold; color:#FF6600;">{tkr}</td><td style="color:#888;">{row["SECTOR"]}</td><td style="color:{s_col}; font-weight:bold;">{sig}</td><td>{row["REASON"]}</td><td class="num">{row["PRICE"]:.2f}</td><td class="num">{row["YTD"]:.1f}%</td><td class="num">{row["SCORE"]:.1f}</td></tr>'
st.markdown(ledger_html + '</tbody></table></div>', unsafe_allow_html=True)

# ==========================================
# 6. BOTTOM TICKER TAPE
# ==========================================
tape_html = '<div class="ticker-tape">'
for b in BENCHMARKS:
    try:
        cur = c[b].dropna().iloc[-1]; prev = c[b].dropna().iloc[-2]; pct = ((cur-prev)/prev)*100
        tape_html += f'<span>{b.replace("^","")} <span style="color:#FFF;">{cur:.2f}</span> <span style="color:{"#00FF00" if pct>0 else "#FF0000"};">{pct:+.2f}%</span></span>'
    except: pass
st.markdown(tape_html + '</div>', unsafe_allow_html=True)
