import warnings, time
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
import pytz
import streamlit as st

st.set_page_config(page_title="Index Intraday Screener", page_icon="📡", layout="wide")

st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size:1.3rem; font-weight:700; }
  thead tr th { background:#1e293b !important; color:#e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Universe ──────────────────────────────────────────────────────
INDEX_SYMBOLS = {
    "^NSEI"               : "NIFTY",
    "^NSEBANK"            : "BANKNIFTY",
    "^BSESN"              : "SENSEX",
    "NIFTY_FIN_SERVICE.NS": "FINNIFTY",
}

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Screener Config")
    indices_sel = st.multiselect(
        "Indices to scan",
        list(INDEX_SYMBOLS.keys()),
        default=list(INDEX_SYMBOLS.keys()),
        format_func=lambda x: INDEX_SYMBOLS[x],
    )
    tf       = st.selectbox("Candle interval", ["5m","15m","30m","60m"], index=1)
    period   = st.selectbox("Lookback period", ["2d","5d","7d"], index=1)
    rsi_buy  = st.slider("RSI buy level",  50, 65, 55)
    rsi_sel  = st.slider("RSI sell level", 35, 50, 45)
    vol_mult = st.slider("Volume multiplier (strict)", 1.0, 3.0, 1.5, 0.1)
    st.divider()
    auto_refresh = st.toggle("Auto-refresh", value=False)
    refresh_mins = st.slider("Refresh every (min)", 1, 60, 15, disabled=not auto_refresh)
    st.divider()
    run_btn  = st.button("▶  Run Screener", type="primary", use_container_width=True)
    save_csv = st.toggle("Save results to CSV", value=False)

# ── Config ────────────────────────────────────────────────────────
INTRADAY_INTERVAL = tf
INTRADAY_PERIOD   = period
RSI_BUY_LEVEL     = rsi_buy
RSI_SEL_LEVEL     = rsi_sel
VOLUME_MULTIPLIER = vol_mult
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9
RSI_PERIOD      = 14
ATR_PERIOD      = 14
TARGET_ATR_MULT = 1.5
SL_ATR_MULT     = 0.75
_HIGH_CONF      = 5
_MEDIUM_CONF    = 3

# ── Manual Indicators (no pandas-ta needed) ───────────────────────
def calc_rsi(close, period=14):
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast   = close.ewm(span=fast,   adjust=False).mean()
    ema_slow   = close.ewm(span=slow,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line= macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram

def calc_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

# ── Data fetch ────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True, multi_level_index=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).strip().title() for c in df.columns]
        required = ["Open","High","Low","Close","Volume"]
        if any(c not in df.columns for c in required):
            return None
        if len(df) < MACD_SLOW + MACD_SIGNAL + 5:
            return None
        df = df[required].copy()
        df.dropna(inplace=True)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return None

# ── Compute indicators ────────────────────────────────────────────
def compute_indicators(df):
    close = df["Close"].squeeze()
    high  = df["High"].squeeze()
    low   = df["Low"].squeeze()
    df["RSI"] = calc_rsi(close, RSI_PERIOD)
    df["ATR"] = calc_atr(high, low, close, ATR_PERIOD)
    ml, sl, mh = calc_macd(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
    df[f"MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"]  = ml
    df[f"MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"] = sl
    df[f"MACDh_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"] = mh
    return df

def _f(val):
    if isinstance(val, pd.Series): val = val.iloc[0]
    if hasattr(val, "item"): return float(val.item())
    return float(val)

# ── Candle pattern ────────────────────────────────────────────────
def detect_candle_pattern(o, h, l, c):
    body = abs(c - o)
    fr   = h - l
    if fr == 0: return "Doji"
    uw = h - max(c, o)
    lw = min(c, o) - l
    bp = body / fr
    ib = c >= o
    if bp < 0.05:  return "Doji"
    if bp >= 0.85: return "Bull Marubozu" if ib else "Bear Marubozu"
    if lw >= body*2 and uw <= body*0.4: return "Hammer"     if ib else "Hanging Man"
    if uw >= body*2 and lw <= body*0.4: return "Inv Hammer" if ib else "Shooting Star"
    if uw >= body*1.5 and lw >= body*1.5: return "Spinning Top"
    if bp >= 0.6: return "Bull Candle" if ib else "Bear Candle"
    return "Bull Small" if ib else "Bear Small"

# ── Next-candle bias ──────────────────────────────────────────────
_PATTERN_SCORE = {
    "Bull Marubozu": (3, 0, "Strong bull body — continuation likely"),
    "Bear Marubozu": (0, 3, "Strong bear body — continuation likely"),
    "Hammer":        (2, 0, "Hammer — bullish reversal"),
    "Hanging Man":   (0, 2, "Hanging Man — bearish reversal"),
    "Inv Hammer":    (1, 0, "Inv Hammer — possible bull reversal"),
    "Shooting Star": (0, 2, "Shooting Star — possible bear reversal"),
    "Bull Candle":   (2, 0, "Solid bull candle — continuation"),
    "Bear Candle":   (0, 2, "Solid bear candle — continuation"),
    "Bull Small":    (1, 0, "Small bull — mild bullish bias"),
    "Bear Small":    (0, 1, "Small bear — mild bearish bias"),
    "Spinning Top":  (0, 0, "Indecision — wait for confirmation"),
    "Doji":          (0, 0, "Doji — indecision / possible reversal"),
}

def next_candle_bias(sig):
    bias = dict(nc_bias="WAIT", nc_action="—", nc_confidence="—",
                nc_entry=None, nc_target=None, nc_stoploss=None, nc_reason="—")
    close   = sig.get("close")
    atr     = sig.get("atr")
    pattern = sig.get("candle_pattern", "Doji")
    rsi     = sig.get("rsi")
    hist    = sig.get("macd_hist")
    vol_r   = sig.get("vol_ratio", 0)
    candle  = sig.get("candle", "—")
    if any(v is None for v in [close, rsi, hist]):
        return bias
    ps         = _PATTERN_SCORE.get(pattern, (0, 0, "Unknown"))
    bull_score = ps[0]
    bear_score = ps[1]
    pat_desc   = ps[2]
    if   rsi > 60: bull_score += 2
    elif rsi > 55: bull_score += 1
    if   rsi < 40: bear_score += 2
    elif rsi < 45: bear_score += 1
    if   hist > 0: bull_score += 2
    elif hist < 0: bear_score += 2
    if vol_r >= VOLUME_MULTIPLIER:
        if candle == "ABOVE_HIGH": bull_score += 1
        if candle == "BELOW_LOW":  bear_score += 1
    if bull_score + bear_score == 0:
        return bias
    if bull_score > bear_score + 1:
        direction = "LONG"
        action    = "BUY CE (Call)"
        score     = bull_score
        conf      = "HIGH" if score >= _HIGH_CONF else "MEDIUM" if score >= _MEDIUM_CONF else "LOW"
        reason    = f"{pattern} | RSI {rsi:.1f} | MACD hist {hist:+.4f} | Vol {vol_r:.1f}x | {pat_desc}"
    elif bear_score > bull_score + 1:
        direction = "SHORT"
        action    = "BUY PE (Put)"
        score     = bear_score
        conf      = "HIGH" if score >= _HIGH_CONF else "MEDIUM" if score >= _MEDIUM_CONF else "LOW"
        reason    = f"{pattern} | RSI {rsi:.1f} | MACD hist {hist:+.4f} | Vol {vol_r:.1f}x | {pat_desc}"
    else:
        bias.update(nc_bias="WAIT", nc_action="No trade — conflicting signals",
                    nc_confidence="LOW",
                    nc_reason=f"Bull {bull_score} vs Bear {bear_score} — too close. {pat_desc}")
        return bias
    if atr and atr > 0:
        entry = round(close, 2)
        if direction == "LONG":
            target = round(close + atr * TARGET_ATR_MULT, 2)
            sl     = round(close - atr * SL_ATR_MULT,     2)
        else:
            target = round(close - atr * TARGET_ATR_MULT, 2)
            sl     = round(close + atr * SL_ATR_MULT,     2)
    else:
        pct   = close * 0.005
        entry = close
        if direction == "LONG":
            target = round(close + pct,       2)
            sl     = round(close - pct * 0.5, 2)
        else:
            target = round(close - pct,       2)
            sl     = round(close + pct * 0.5, 2)
    bias.update(nc_bias=direction, nc_action=action, nc_confidence=conf,
                nc_entry=entry, nc_target=target, nc_stoploss=sl, nc_reason=reason)
    return bias

# ── Signal classifier ─────────────────────────────────────────────
_IST          = pytz.timezone("Asia/Kolkata")
_interval_map = {"1m":1,"2m":2,"5m":5,"15m":15,"30m":30,"60m":60,"1h":60}

def classify_signal(df):
    mc = f"MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"
    ms = f"MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"
    mh = f"MACDh_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}"
    empty = dict(
        strict_signal="NEUTRAL", relaxed_signal="NEUTRAL",
        candle_time="—", next_candle_time="—",
        close=None, prev_high=None, prev_low=None, atr=None,
        vol_today=None, vol_ratio=None, candle="—", candle_pattern="—",
        rsi=None, macd=None, macd_signal_val=None, macd_hist=None,
        nc_bias="—", nc_action="—", nc_confidence="—",
        nc_entry=None, nc_target=None, nc_stoploss=None, nc_reason="—",
    )
    needed = ["RSI", mc, ms, mh, "Open", "Close", "High", "Low", "Volume"]
    if len(df) < 2 or any(c not in df.columns for c in needed):
        return empty
    clean = df.dropna(subset=needed)
    if len(clean) < 2:
        return empty
    t = clean.iloc[-1]
    p = clean.iloc[-2]
    rsi = _f(t["RSI"])
    mv  = _f(t[mc]);  msv = _f(t[ms]);  mhv = _f(t[mh])
    cn  = _f(t["Close"]);  on = _f(t["Open"])
    hn  = _f(t["High"]);   ln = _f(t["Low"])
    vn  = _f(t["Volume"])
    ph  = _f(p["High"]);   pl = _f(p["Low"]);  pv = _f(p["Volume"])
    av  = (_f(t["ATR"])
           if "ATR" in clean.columns and not pd.isna(t.get("ATR", float("nan")))
           else None)
    _mins = _interval_map.get(INTRADAY_INTERVAL, 15)
    _raw  = clean.index[-1]
    _li   = (pytz.utc.localize(_raw.to_pydatetime()).astimezone(_IST)
             if _raw.tzinfo is None
             else _raw.to_pydatetime().astimezone(_IST))
    ct    = _li.strftime("%d-%b %H:%M")
    _ni   = _li + timedelta(minutes=_mins)
    if (_ni.hour, _ni.minute) >= (15, 30) or (_ni.hour, _ni.minute) < (9, 15):
        _nd = _li + timedelta(days=1)
        while _nd.weekday() >= 5:
            _nd += timedelta(days=1)
        _ni = _nd.replace(hour=9, minute=15, second=0, microsecond=0)
    nct  = _ni.strftime("%d-%b %H:%M")
    vr   = (vn / pv) if pv > 0 else 0.0
    hv   = vr >= VOLUME_MULTIPLIER
    bc   = (cn > ph) and hv
    brc  = (cn < pl) and hv
    cl   = "ABOVE_HIGH" if bc else "BELOW_LOW" if brc else "—"
    cp   = detect_candle_pattern(on, hn, ln, cn)
    mb   = (mv > msv) and (mhv > 0)
    mbe  = (mv < msv) and (mhv < 0)
    if   rsi > RSI_BUY_LEVEL and mb  and bc:  strict = "BULLISH"
    elif rsi < RSI_SEL_LEVEL and mbe and brc: strict = "BEARISH"
    else:                                      strict = "NEUTRAL"
    if   rsi > RSI_BUY_LEVEL and mb:  relaxed = "BULLISH"
    elif rsi < RSI_SEL_LEVEL and mbe: relaxed = "BEARISH"
    else:                              relaxed = "NEUTRAL"
    sig = dict(
        strict_signal=strict, relaxed_signal=relaxed,
        candle_time=ct, next_candle_time=nct,
        close=round(cn, 2), prev_high=round(ph, 2), prev_low=round(pl, 2),
        atr=round(av, 2) if av else None,
        vol_today=int(vn), vol_ratio=round(vr, 2),
        candle=cl, candle_pattern=cp,
        rsi=round(rsi, 2), macd=round(mv, 4),
        macd_signal_val=round(msv, 4), macd_hist=round(mhv, 4),
    )
    sig.update(next_candle_bias(sig))
    return sig

# ── Run screener ──────────────────────────────────────────────────
def run_screener(tickers):
    rows, skipped = [], []
    prog = st.progress(0, text="Scanning indices…")
    for i, ticker in enumerate(tickers):
        name = INDEX_SYMBOLS.get(ticker, ticker)
        prog.progress((i + 1) / len(tickers), text=f"Fetching {name}…")
        df = fetch_data(ticker, INTRADAY_PERIOD, INTRADAY_INTERVAL)
        if df is None:
            skipped.append(name)
            continue
        df  = compute_indicators(df)
        sig = classify_signal(df)
        sig["ticker"] = name
        rows.append(sig)
        time.sleep(0.3)
    prog.empty()
    if skipped:
        st.warning(f"Could not fetch: {', '.join(skipped)}")
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ── Badge helpers ─────────────────────────────────────────────────
def sig_b(s):
    if s == "BULLISH": return "🟢 BULLISH"
    if s == "BEARISH": return "🔴 BEARISH"
    return "⚪ NEUTRAL"

def bias_b(b):
    if b == "LONG":  return "🟢 LONG"
    if b == "SHORT": return "🔴 SHORT"
    return "⏸ WAIT"

def conf_b(c):
    if c == "HIGH":   return "🔵 HIGH"
    if c == "MEDIUM": return "🟠 MEDIUM"
    if c == "LOW":    return "⚫ LOW"
    return c

def candle_b(c):
    if c == "ABOVE_HIGH": return "⬆ ABOVE HIGH"
    if c == "BELOW_LOW":  return "⬇ BELOW LOW"
    return "—"

# ── Render helpers ────────────────────────────────────────────────
def render_signals_table(df):
    d = df.copy()
    d["strict_signal"]  = d["strict_signal"].map(sig_b)
    d["relaxed_signal"] = d["relaxed_signal"].map(sig_b)
    d["candle"]         = d["candle"].map(candle_b)
    cols = ["ticker","candle_time","close","prev_high","prev_low",
            "candle","candle_pattern","vol_ratio","rsi","macd","macd_hist",
            "strict_signal","relaxed_signal"]
    hdrs = ["Index","Candle Time","Close","Prev High","Prev Low",
            "Breakout","Pattern",f"Vol x (>={VOLUME_MULTIPLIER})",
            "RSI","MACD","MACD Hist","Strict","Relaxed"]
    av = [c for c in cols if c in d.columns]
    ah = [hdrs[cols.index(c)] for c in av]
    st.dataframe(d[av].rename(columns=dict(zip(av, ah))),
                 use_container_width=True, hide_index=True)

def render_nc_table(df):
    d = df.copy()
    d["nc_bias"]       = d["nc_bias"].map(bias_b)
    d["nc_confidence"] = d["nc_confidence"].map(conf_b)
    cols = ["ticker","candle_time","next_candle_time","close",
            "nc_bias","nc_action","nc_confidence",
            "nc_entry","nc_target","nc_stoploss","atr","nc_reason"]
    hdrs = ["Index","Cur Candle","Next Candle","Close",
            "Bias","Action","Confidence","Entry","Target","Stop Loss","ATR","Reason"]
    av = [c for c in cols if c in d.columns]
    ah = [hdrs[cols.index(c)] for c in av]
    st.dataframe(d[av].rename(columns=dict(zip(av, ah))),
                 use_container_width=True, hide_index=True)

def show_tab(df, label):
    if df.empty:
        st.info(f"No {label} signals.")
    else:
        render_signals_table(df)
        st.markdown("##### 📅 Next Candle Prediction")
        render_nc_table(df)

# ── Main UI ───────────────────────────────────────────────────────
st.title("📡 Index Intraday Options Screener")
st.caption(
    f"Universe: {' | '.join(INDEX_SYMBOLS.values())}  ·  "
    f"Interval: {INTRADAY_INTERVAL}  ·  "
    f"RSI({RSI_PERIOD})  ·  MACD({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL})  ·  "
    f"Vol>={VOLUME_MULTIPLIER}x  ·  ATR({ATR_PERIOD})"
)

if auto_refresh:
    st.info(f"Auto-refresh every {refresh_mins} min — last run: "
            f"{datetime.now().strftime('%H:%M:%S')}")
    import streamlit.components.v1 as components
    components.html(
        f"<script>setTimeout(()=>window.location.reload(),"
        f"{refresh_mins * 60 * 1000})</script>",
        height=0,
    )

if run_btn or auto_refresh:
    if not indices_sel:
        st.error("Select at least one index in the sidebar.")
        st.stop()
    with st.spinner("Fetching live data…"):
        results = run_screener(indices_sel)
    if results.empty:
        st.warning("No data returned. Try a different timeframe.")
        st.stop()
    s_bull = results[results["strict_signal"] == "BULLISH"].copy()
    s_bear = results[results["strict_signal"] == "BEARISH"].copy()
    neutral_mask = results["strict_signal"] == "NEUTRAL"
    r_bull = results[neutral_mask & (results["relaxed_signal"] == "BULLISH")].copy()
    r_bear = results[neutral_mask & (results["relaxed_signal"] == "BEARISH")].copy()
    st.subheader("📊 Scan Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Scanned",         len(results))
    c2.metric("🟢 Strict Bull",  len(s_bull))
    c3.metric("🔴 Strict Bear",  len(s_bear))
    c4.metric("🟡 Relaxed Bull", len(r_bull))
    c5.metric("🟠 Relaxed Bear", len(r_bear))
    st.caption(f"Scan at {datetime.now().strftime('%d-%b-%Y  %H:%M:%S')} IST")
    st.divider()
    with st.expander("📋 All Indices — Full Detail", expanded=True):
        render_signals_table(results)
    st.divider()
    st.subheader("★ Strict Signals  (RSI + MACD + Candle Breakout + Volume)")
    tab1, tab2 = st.tabs(["🟢 Strict Bullish", "🔴 Strict Bearish"])
    with tab1:
        show_tab(s_bull, "strict bullish")
    with tab2:
        show_tab(s_bear, "strict bearish")
    st.divider()
    st.subheader("☆ Relaxed Signals  (RSI + MACD only)")
    tab3, tab4 = st.tabs(["🟡 Relaxed Bullish", "🟠 Relaxed Bearish"])
    with tab3:
        show_tab(r_bull, "relaxed bullish")
    with tab4:
        show_tab(r_bear, "relaxed bearish")
    st.divider()
    all_sig = pd.concat([s_bull, s_bear, r_bull, r_bear], ignore_index=True)
    all_sig = all_sig[all_sig["nc_bias"].isin(["LONG", "SHORT"])].copy()
    if not all_sig.empty:
        st.subheader("📊 Master Next-Candle Table — All Actionable Indices")
        conf_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        all_sig["_cs"] = all_sig["nc_confidence"].map(conf_order).fillna(3)
        all_sig["_bs"] = (all_sig["nc_bias"] == "SHORT").astype(int)
        all_sig = all_sig.sort_values(["_cs", "_bs"]).drop(columns=["_cs", "_bs"])
        render_nc_table(all_sig)
    if save_csv:
        csv = results.to_csv(index=False).encode()
        st.download_button("💾 Download Results CSV", data=csv,
                           file_name=f"signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                           mime="text/csv")
else:
    st.info("👈  Configure settings in the sidebar, then click **▶ Run Screener**.")
    st.markdown("""
| Signal Type | Conditions |
|---|---|
| **Strict Bullish** | RSI > threshold AND MACD bullish AND Close > Prev High AND Vol >= mult |
| **Strict Bearish** | RSI < threshold AND MACD bearish AND Close < Prev Low AND Vol >= mult |
| **Relaxed Bullish** | RSI > threshold AND MACD bullish *(no candle/vol filter)* |
| **Relaxed Bearish** | RSI < threshold AND MACD bearish *(no candle/vol filter)* |
    """)

st.caption("Built with yfinance · Streamlit  ·  Data: NSE / BSE")
 
    
