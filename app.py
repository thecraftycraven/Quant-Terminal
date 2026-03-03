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
    
    .ledger-container {{ max-height: 400px; overflow-y: auto; border: 1px solid #333; background: #000; margin-bottom: 15px; }}
    .ledger-table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    .ledger-table th {{ position: sticky; top: 0; background-color: #111; color: #FF6600; z-index: 10; border-bottom: 2px solid #FF6600; padding: 8px; text-align: left; }}
    .ledger-table td {{ padding: 8px; border-bottom: 1px solid #222; text-align: left; font-family: monospace; font-size: 12px; }}
    .ledger-table td.num {{ text-align: right; }}
    .ledger-table tr:hover {{ background-color: #1A1A1A; }}
    
    #MainMenu, footer, header {{visibility: hidden;}}
    .stLineChart {{ margin-top: -15px; }} 
    .stBarChart {{ margin-top: -15px; }} 
    </style>
    
    <div class="status-bar">
        <div class="status-left">● {market_status} | SYS.OP.NORMAL</div>
        <div class="status-right">{time_str} | <span style="font-size:10px; color:#888;">{date_str}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 2. FULL 46-ASSET UNIVERSE DEFINITION
# ==========================================
BENCHMARKS = ["SPY", "QQQ", "^VIX", "DIA"] 

TICKER_SECTORS = {
    # Energy
    "OIH": "Energy", "XLE": "Energy",
    # Materials
    "XLB": "Materials", "XME": "Materials", "WOOD": "Materials",
    # Industrials
    "XLI": "Industrials", "IYT": "Industrials",
    # Consumer Discretionary
    "CARZ": "Cons Discretionary", "XLY": "Cons Discretionary", "PEJ": "Cons Discretionary", "XRT": "Cons Discretionary",
    # Consumer Staples
    "XLP": "Cons Staples", "PBJ": "Cons Staples",
    # Health Care
    "IHI": "Health Care", "XBI": "Health Care",
    # Financials
    "KBE": "Financials", "IAI": "Financials", "KIE": "Financials",
    # Information Technology
    "IGV": "Info Tech", "SMH": "Info Tech",
    # Communication Services
    "IYZ": "Comm Services", "XLC": "Comm Services",
    # Utilities
    "XLU": "Utilities", "FCG": "Utilities", "IDU": "Utilities", "PHO": "Utilities", "ICLN": "Utilities",
    # Real Estate
    "VNQ": "Real Estate", "REET": "Real Estate",
    # Global Overlays
    "EFA": "Global Overlay", "VWO": "Global Overlay", "INDY": "Global Overlay", "KWEB": "Global Overlay",
    # Uncorrelated Assets
    "DBA": "Uncorrelated", "PDBC": "Uncorrelated", "UUP": "Uncorrelated", "VIXY": "Uncorrelated", "SLV": "Uncorrelated", "TIP": "Uncorrelated", "DBB": "Uncorrelated", "CWB": "Uncorrelated",
    # Macro
    "IAU": "Macro", "FBTC": "Macro",
    # Safe Harbors
    "BIL": "Safe Harbor", "IEF": "Safe Harbor", "TLT": "Safe Harbor"
}

TICKERS = list(TICKER_SECTORS.keys())
ALL_SYMBOLS = TICKERS + BENCHMARKS

# ==========================================
# 3. CORE DATA ENGINE
# ==========================================
@st.cache_data(ttl=3600)
def fetch_data():
    # Fetch 2 years so historical 12-month backtest has enough data for 200DMA math
    data = yf.download(ALL_SYMBOLS, period="2y", progress=False) 
    return data['Close'], data['High'], data['Low'], data['Volume']

def calculate_snapshot(closes, highs, lows, volumes, target_date, is_current=True):
    # This engine runs math for any given day in history
    p_snap = closes.loc[:target_date]
    h_snap = highs.loc[:target_date]
    l_snap = lows.loc[:target_date]
    v_snap = volumes.loc[:target_date]
    
    if len(p_snap) < 200: return pd.DataFrame() # Needs 200 days of history
    
    spy_p = p_snap["SPY"].dropna()
    vix_close = p_snap["^VIX"].dropna().iloc[-1]
    vix_halt = vix_close > 30 
    current_year = target_date.year
    
    results = []
    
    for ticker in TICKERS:
        try:
            p = p_snap[ticker].dropna()
            h = h_snap[ticker].dropna()
            l = l_snap[ticker].dropna()
            v = v_snap[ticker].dropna()
            
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
                'TKR': ticker, 'SECTOR': TICKER_SECTORS[ticker], 'PRICE': p.iloc[-1], 'YTD': ytd_ret, 'RAM': ram, 
                'ROC_AC': roc_accel, 'REL_STR': rel_strength, '50D_SLP': sma_50_slope, 
                'VOL_CF': vol_conf, 'ADX': adx, 'STOP_PRC': trailing_stop, 'ALLOC': alloc_pct, 
                'Above_200': p.iloc[-1] > p.rolling(200).mean().iloc[-1]
            })
        except: continue
            
    df = pd.DataFrame(results).set_index('TKR')
    if df.empty: return df, vix_halt, vix_close
    
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
        rnk = row['RNK']
        
        if vix_halt:
            signals.append("HALT")
            reasons.append("VIX > 30")
        elif not row['Above_200'] or row['PRICE'] < row['STOP_PRC']: 
            signals.append("STRONG SELL")
            reasons.append(reason if reason else "Hit ATR Stop")
        elif fits_all and rnk <= 5:
            signals.append("STRONG BUY")
            reasons.append("PASSED (Top 5)")
        elif rnk <= 5:
            signals.append("BUY")
            reasons.append(reason)
        elif fits_all and 5 < rnk <= 10:
            signals.append("HOLD")
            reasons.append("PASSED (Rank Buffer)")
        else: 
            signals.append("SELL")
            if rnk > 10:
                reasons.append(f"{reason} [Rank #{rnk}]" if reason else f"Out of target zone [Rank #{rnk}]")
            else:
                reasons.append(reason)
            
    df['SIGNAL'] = signals
    df['REASON'] = reasons
    return df, vix_halt, vix_close

@st.cache_data(ttl=3600)
def run_historical_backtest(closes, highs, lows, volumes):
    # Finds the last trading day of each month for the last 12 months
    monthly_dates = closes.resample('M').last().index
    last_12_months = monthly_dates[-13:-1] # Exclude current incomplete month
    
    backtest_log = []
    
    for i in range(len(last_12_months) - 1):
        start_date = last_12_months[i]
        end_date = last_12_months[i+1]
        
        # Calculate algorithm state at the START of the month
        df_hist, v_h, v_c = calculate_snapshot(closes, highs, lows, volumes, start_date, is_current=False)
        if df_hist.empty: continue
        
        # Extract the Top 5 Strong Buys for that month
        strong_buys = df_hist[df_hist['SIGNAL'] == 'STRONG BUY'].head(5).index.tolist()
        
        # If no strong buys passed, hold cash (BIL)
        if not strong_buys:
            strong_buys = ["BIL"]
            basket_ret = ((closes.loc[end_date, "BIL"] / closes.loc[start_date, "BIL"]) - 1) * 100
        else:
            # Calculate actual return of those assets over the following month
            p_start = closes.loc[start_date, strong_buys].mean()
            p_end = closes.loc[end_date, strong_buys].mean()
            basket_ret = ((p_end / p_start) - 1) * 100
            
        month_label = start_date.strftime('%Y-%b')
        backtest_log.append({
            "Month": month_label,
            "Top 5 Allocation": ", ".join(strong_buys),
            "1-Month Return (%)": basket_ret
        })
        
    return pd.DataFrame(backtest_log)

with st.spinner('SYNCING CURRENT & HISTORICAL QUANTITATIVE ENGINES...'):
    c, h, l, v = fetch_data()
    # Current Engine
    df, vix_halt, vix_close = calculate_snapshot(c, h, l, v, c.index[-1], is_current=True)
    # Historical Engine
    backtest_df = run_historical_backtest(c, h, l, v)

# Chart Math
c_ytd = c[c.index.year == now_est.year]
if not c_ytd.empty:
    spy_ytd = (c_ytd['SPY'] / c_ytd['SPY'].iloc[0] - 1) * 100
    elite_targets = df[df['RNK'] <= 5].index.tolist()
    strat_prices = c_ytd[elite_targets].mean(axis=1)
    strat_ytd = (strat_prices / strat_prices.iloc[0] - 1) * 100
    chart_data = pd.DataFrame({"Strategy (Top 5)": strat_ytd, "S&P 500 (SPY)": spy_ytd}).dropna()
else:
    chart_data = pd.DataFrame()

# Updated Regime Logic 
top_5 = df.head(5).index.tolist()
safe_harbor_etfs = ["BIL", "TLT", "IEF", "IAU", "XLU", "XLP"]
inflation_etfs = ["PDBC", "DBA", "DBB", "XLE", "XME", "OIH"]
safe_count = sum(el in safe_harbor_etfs for el in top_5)
inf_count = sum(el in inflation_etfs for el in top_5)

if safe_count >= 2: regime, r_color = "RISK-OFF (DEFENSIVE/CASH LEADERSHIP)", "#FBBF24"
elif inf_count >= 2: regime, r_color = "INFLATIONARY (COMMODITY LEADERSHIP)", "#FF6600"
else: regime, r_color = "RISK-ON (EQUITY/GROWTH EXPANSION)", "#00FF00"

# ==========================================
# 4. INTERFACE LAYOUT
# ==========================================
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
