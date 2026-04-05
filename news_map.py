import streamlit as st
import urllib.request
import xml.etree.ElementTree as ET
import pytz
from datetime import datetime

# ==================================
# PAGE CONFIG
# ==================================
st.set_page_config(
    page_title="Nifty Pre-Market Intelligence",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Syne:wght@700;800&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Mono', monospace; background:#0a0e17; color:#e0e6f0; }
.stApp { background:#0a0e17; }
.metric-card { background:linear-gradient(135deg,#111827,#1a2235); border:1px solid #1e3a5f; border-radius:12px; padding:20px 24px; margin-bottom:12px; }
.metric-card h4 { margin:0 0 4px 0; font-size:11px; color:#6b8cad; text-transform:uppercase; letter-spacing:2px; }
.metric-card .val { font-size:26px; font-weight:700; font-family:'Syne',sans-serif; }
.bull { color:#00e676; } .bear { color:#ff5252; } .neut { color:#ffca28; }
.news-item { padding:10px 14px; border-left:3px solid #1e3a5f; margin:6px 0; background:#111827; border-radius:0 8px 8px 0; font-size:13px; line-height:1.5; }
.news-item.geo { border-left-color:#7c3aed; }
.news-item.mkt { border-left-color:#0ea5e9; }
.impact-row { display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-bottom:1px solid #1a2235; font-size:13px; }
.badge { padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; white-space:nowrap; letter-spacing:1px; }
.badge-bull { background:#052e16; color:#00e676; border:1px solid #00e676; }
.badge-bear { background:#2d0a0a; color:#ff5252; border:1px solid #ff5252; }
.badge-neut { background:#2d2200; color:#ffca28; border:1px solid #ffca28; }
.stButton > button { background:linear-gradient(135deg,#1d4ed8,#0ea5e9) !important; color:white !important; border:none !important; border-radius:8px !important; font-family:'IBM Plex Mono',monospace !important; font-weight:600 !important; padding:12px 32px !important; font-size:14px !important; }
.section-title { font-family:'Syne',sans-serif; font-size:15px; font-weight:700; color:#94b4d4; text-transform:uppercase; letter-spacing:3px; margin:28px 0 14px 0; padding-bottom:8px; border-bottom:1px solid #1e3a5f; }
.heat-bar-wrap { margin:4px 0; }
.heat-label { font-size:12px; font-family:'IBM Plex Mono'; color:#c9d8e8; margin-bottom:3px; }
.verdict-box { border-radius:14px; padding:24px; text-align:center; margin:16px 0; }
.verdict-bull { background:linear-gradient(135deg,#052e16,#064e3b); border:1px solid #00e676; }
.verdict-bear { background:linear-gradient(135deg,#2d0a0a,#450a0a); border:1px solid #ff5252; }
.verdict-neut { background:linear-gradient(135deg,#2d2200,#422006); border:1px solid #ffca28; }
</style>
""", unsafe_allow_html=True)


# ==================================
# RSS FEEDS  (no API keys needed)
# ==================================
RSS_SOURCES = {
    "MARKET": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",
        "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "https://www.business-standard.com/rss/markets-106.rss",
        "https://news.google.com/rss/search?q=Nifty+Sensex+RBI+India+economy+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=RBI+repo+rate+inflation+India+budget+GDP&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "GEO": [
        "https://feeds.reuters.com/reuters/worldNews",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://news.google.com/rss/search?q=Iran+Israel+war+Middle+East+sanctions+conflict&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=crude+oil+brent+OPEC+energy+prices+petrol&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=US+Fed+interest+rate+dollar+FII+global+economy&hl=en&gl=US&ceid=US:en",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
    ],
}

@st.cache_data(ttl=600)
def get_market_news():
    headlines = []
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def fetch_rss(url):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read()
            root   = ET.fromstring(raw)
            titles = []
            for item in root.iter("item"):
                t = (item.findtext("title") or "").strip()
                if t and len(t) > 20:
                    titles.append(t)
                if len(titles) >= 4:
                    break
            if not titles:
                for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                    t = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                    if t and len(t) > 20:
                        titles.append(t)
                    if len(titles) >= 4:
                        break
            return titles
        except Exception:
            return []

    for tag, urls in RSS_SOURCES.items():
        for url in urls:
            for title in fetch_rss(url):
                headlines.append((tag, title))

    seen, unique = set(), []
    for tag, h in headlines:
        key = h[:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append((tag, h))
    return unique[:30]


# ==================================
# SECTOR DEFINITIONS
# ==================================
NIFTY_SECTORS = {
    "IT / Tech":         {"keywords": ["it", "tech", "software", "nasdaq", "infosys", "tcs", "wipro", "hcl", "tech mahindra"], "index": "NIFTY"},
    "Auto":              {"keywords": ["auto", "car", "vehicle", "ev", "maruti", "tata motors", "bajaj auto", "hero"],           "index": "NIFTY"},
    "FMCG":              {"keywords": ["fmcg", "consumer", "retail", "hul", "nestle", "dabur", "godrej"],                        "index": "NIFTY"},
    "Pharma":            {"keywords": ["pharma", "drug", "medicine", "sun pharma", "cipla", "dr reddy"],                         "index": "NIFTY"},
    "Metal / Mining":    {"keywords": ["metal", "steel", "iron", "tata steel", "jsw", "vedanta", "hindalco", "coal"],            "index": "NIFTY"},
    "Energy / Oil":      {"keywords": ["oil", "crude", "gas", "energy", "opec", "ongc", "reliance", "bpcl", "petrol", "brent"], "index": "NIFTY"},
    "Infra / Realty":    {"keywords": ["infra", "infrastructure", "realty", "real estate", "construction", "dlf", "cement"],     "index": "NIFTY"},
    "Chemicals":         {"keywords": ["chemical", "specialty", "atul", "basf", "upl", "agrochemical", "fertilizer"],            "index": "NIFTY"},
    "Capital Goods":     {"keywords": ["capital goods", "bhel", "engineering", "havells", "polycab", "bosch", "defence"],        "index": "NIFTY"},
    "Telecom / Media":   {"keywords": ["telecom", "airtel", "5g", "broadband", "media", "entertainment", "ott"],                 "index": "NIFTY"},
    "Textile":           {"keywords": ["textile", "apparel", "cotton", "yarn", "fabric", "garment"],                             "index": "NIFTY"},
    "Logistics":         {"keywords": ["logistics", "shipping", "freight", "cargo", "supply chain", "transport"],                "index": "NIFTY"},
    "Hospitality":       {"keywords": ["hotel", "hospitality", "tourism", "travel", "resort", "airline"],                        "index": "NIFTY"},
    "Agri":              {"keywords": ["agri", "agriculture", "fertilizer", "pesticide", "seeds", "sugar", "farm"],              "index": "NIFTY"},
    "BANKING (Private)": {"keywords": ["hdfc bank", "icici bank", "axis bank", "kotak", "indusind", "private bank"],             "index": "BANKNIFTY"},
    "BANKING (PSU)":     {"keywords": ["sbi", "pnb", "bank of baroda", "canara", "psu bank", "state bank"],                     "index": "BANKNIFTY"},
    "NBFC / Financial":  {"keywords": ["nbfc", "bajaj finance", "muthoot", "shriram", "financial", "loan", "microfinance"],      "index": "BANKNIFTY"},
    "BANKING (General)": {"keywords": ["bank", "rbi", "repo", "rate cut", "rate hike", "credit", "deposit", "npa", "banking"],  "index": "BANKNIFTY"},
}

POSITIVE_WORDS = ["gain","rise","surge","positive","growth","rally","jump","boost","strong",
                  "record","profit","recovery","optimism","peace","deal","ceasefire","easing",
                  "rate cut","gdp growth","inflow","fii buying"]
NEGATIVE_WORDS = ["fall","drop","decline","crash","negative","down","pressure","weak","sell",
                  "loss","war","tension","sanctions","conflict","attack","missile","tariff","ban",
                  "crisis","escalation","threat","recession","unrest","rate hike","outflow",
                  "fii selling","inflation rises","oil surges","crude up","petrol prices",
                  "fuel prices","energy shock","surging","shock","risk"]


# ==================================
# SECTOR SCORER
# ==================================
def analyze_sectors(news_list):
    scores = {s: 0 for s in NIFTY_SECTORS}
    for _, news in news_list:
        lower  = news.lower()
        is_pos = any(w in lower for w in POSITIVE_WORDS)
        is_neg = any(w in lower for w in NEGATIVE_WORDS)
        for sector, info in NIFTY_SECTORS.items():
            for kw in info["keywords"]:
                if kw in lower:
                    if is_pos and not is_neg:   scores[sector] += 2
                    elif is_neg and not is_pos: scores[sector] -= 2
                    elif is_pos and is_neg:     scores[sector] -= 1
                    break

    combined = " ".join(h for _, h in news_list).lower()

    if any(w in combined for w in ["crude up","oil surges","oil price up","brent rises","petrol prices","fuel prices","energy shock","strait of hormuz","persian gulf"]):
        scores["Energy / Oil"] += 5; scores["Auto"] -= 2; scores["FMCG"] -= 2; scores["BANKING (General)"] -= 1; scores["Metal / Mining"] -= 1
    if any(w in combined for w in ["crude falls","oil drops","oil price down","brent falls"]):
        scores["Energy / Oil"] -= 2; scores["Auto"] += 2; scores["FMCG"] += 1; scores["BANKING (General)"] += 1
    if any(w in combined for w in ["rate cut","repo rate cut","rbi cut"]):
        scores["BANKING (Private)"] += 3; scores["BANKING (PSU)"] += 3; scores["BANKING (General)"] += 2
        scores["NBFC / Financial"] += 3; scores["Auto"] += 2; scores["Infra / Realty"] += 2
    if any(w in combined for w in ["rate hike","repo rate hike","rbi hike"]):
        scores["BANKING (Private)"] -= 2; scores["BANKING (PSU)"] -= 2; scores["BANKING (General)"] -= 2
        scores["NBFC / Financial"] -= 3; scores["Auto"] -= 2; scores["Infra / Realty"] -= 2
    if any(w in combined for w in ["iran israel","iran war","us iran","war","missile attack","middle east conflict","strait of hormuz"]):
        for s in scores:
            if s != "Energy / Oil": scores[s] -= 2
        scores["Energy / Oil"] += 5
    if any(w in combined for w in ["fed rate cut","federal reserve cut","fed dovish"]):
        scores["IT / Tech"] += 2; scores["BANKING (Private)"] += 1; scores["NBFC / Financial"] += 1
    if any(w in combined for w in ["rupee falls","rupee weakens","inr down"]):
        scores["IT / Tech"] += 2; scores["Pharma"] += 1; scores["Auto"] -= 1; scores["FMCG"] -= 1
    if any(w in combined for w in ["fii buying","fii inflow","fpi buying"]):
        scores["BANKING (Private)"] += 2; scores["IT / Tech"] += 1
    if any(w in combined for w in ["fii selling","fii outflow","fpi selling"]):
        scores["BANKING (Private)"] -= 2; scores["IT / Tech"] -= 1
    return scores


# ==================================
# HEATMAP  (pure HTML — no plotly)
# ==================================
def score_color(score):
    if score >= 6:  return "#00c853", "🚀 Strong Buy"
    if score >= 3:  return "#4caf50", "⬆ Positive"
    if score >= 1:  return "#81c784", "↗ Mild +"
    if score == 0:  return "#455a64", "↔ Neutral"
    if score >= -2: return "#ef5350", "↘ Mild -"
    if score >= -4: return "#c62828", "⬇ Negative"
    return "#7f0000", "💥 Strong Sell"

def render_heatmap(scores, index_filter):
    items = sorted(
        [(s, v) for s, v in scores.items() if NIFTY_SECTORS[s]["index"] == index_filter],
        key=lambda x: -x[1]
    )
    MAX = 10
    html = ""
    for sector, score in items:
        color, label = score_color(score)
        pct = int(((score + MAX) / (2 * MAX)) * 100)
        pct = max(8, min(pct, 100))
        html += f"""
        <div class="heat-bar-wrap">
          <div class="heat-label">{sector}</div>
          <div style="background:#1a2235;border-radius:4px;height:26px;position:relative;">
            <div style="width:{pct}%;background:{color};height:26px;border-radius:4px;display:flex;align-items:center;padding:0 10px;font-size:11px;font-weight:600;font-family:'IBM Plex Mono';color:#fff;min-width:60px;">
              {score:+d} &nbsp; {label}
            </div>
          </div>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)


# ==================================
# INDIA IMPACT RULES
# ==================================
INDIA_IMPACT_RULES = [
    (["rbi rate cut","repo rate cut","rate cut"],        "BULLISH", "RBI rate cut → cheaper loans → Banking, Auto, Realty rally"),
    (["rbi rate hike","repo rate hike","rate hike"],     "BEARISH", "Rate hike → costly borrowing → rate-sensitive sectors under pressure"),
    (["inflation rises","cpi up","inflation high"],      "BEARISH", "Rising inflation → RBI may tighten → consumer stocks under pressure"),
    (["inflation eases","cpi down","inflation falls"],   "BULLISH", "Falling inflation → room for rate cuts → positive for all sectors"),
    (["crude rises","oil surges","oil price up","brent rises","crude up","petrol prices","fuel prices rise","energy shock"], "BEARISH", "Rising crude → India imports 85% oil → CAD widens → Rupee weakens"),
    (["crude falls","oil drops","oil price down","crude down","brent falls"], "BULLISH", "Falling crude → lower import bill → CAD improves → Rupee strengthens"),
    (["fed rate cut","us rate cut","federal reserve cut","fed dovish"], "BULLISH", "Fed rate cut → dollar weakens → FII inflows into Indian markets"),
    (["fed rate hike","us rate hike","federal reserve hike","fed hawkish"], "BEARISH", "Fed hike → stronger dollar → FII outflows from India"),
    (["iran israel","israel iran","iran missile","iran war","us iran","bomb iran"], "BEARISH", "Iran-Israel/US conflict → crude oil supply shock → global risk-off"),
    (["strait of hormuz","hormuz","persian gulf shipping"], "BEARISH", "Hormuz threat → India oil imports at risk → crude spikes"),
    (["middle east conflict","middle east war","opec cut","oil supply cut"], "BEARISH", "Middle East tension → crude supply disruption → India import costs rise"),
    (["ceasefire","peace deal","tension eases","conflict resolved"], "BULLISH", "Geopolitical easing → crude falls → risk-on → FII inflows → rally"),
    (["fii buying","fii inflow","fpi buying"],  "BULLISH", "FII buying → direct demand for Indian equities → Nifty rally"),
    (["fii selling","fii outflow","fpi selling"], "BEARISH", "FII selling → supply pressure on Indian equities → Nifty correction"),
    (["gdp growth","india gdp rises","strong gdp"], "BULLISH", "Strong GDP → earnings upgrade cycle → positive for all sectors"),
    (["gdp falls","gdp slowdown","recession"],    "BEARISH", "GDP slowdown → earnings pressure → broad market selloff"),
    (["rupee falls","rupee weakens","inr down"],  "BEARISH", "Weak Rupee → costlier imports → FII reduce India exposure"),
    (["rupee rises","rupee strengthens","inr up"], "BULLISH", "Strong Rupee → lower import costs → FII confidence → positive"),
    (["us china trade war","china tariff","us tariff","trade war"], "BEARISH", "US-China trade war → global slowdown → IT sector hit"),
    (["dow jones falls","nasdaq down","s&p falls","wall street falls"], "BEARISH", "US market fall → negative global cues → India likely gap-down"),
    (["dow jones rises","nasdaq up","s&p rises","wall street rises"], "BULLISH", "Positive US cues → FII optimism → India likely gap-up"),
]

def analyze_india_impact(news_list):
    results = []
    pos_wds = ["gain","rise","surge","growth","rally","boost","profit","recovery","deal","peace","easing","strong","positive","optimism"]
    neg_wds = ["fall","drop","decline","crash","war","tension","sanctions","conflict","crisis","loss","weak","threat","pressure","fear","attack","shock","risk"]
    for _, news in news_list:
        lower, matched = news.lower(), False
        for triggers, impact, reason in INDIA_IMPACT_RULES:
            for t in triggers:
                if t in lower:
                    results.append((news, impact, reason)); matched = True; break
            if matched: break
        if not matched:
            pos = any(w in lower for w in pos_wds)
            neg = any(w in lower for w in neg_wds)
            if pos and not neg:   results.append((news, "BULLISH", "Positive global/economic cues → supportive for Indian markets"))
            elif neg and not pos: results.append((news, "BEARISH", "Negative global/geopolitical cues → risk-off pressure on Indian markets"))
            elif neg and pos:     results.append((news, "BEARISH", "Mixed but risk-leaning cues → cautious stance"))
    return results


# ==================================
# OVERALL SENTIMENT
# ==================================
def overall_sentiment(news_list):
    pos_words = ["gain","rise","surge","positive","growth","rally","jump","boost","strong","record","profit","recovery","optimism","peace","deal","ceasefire","easing"]
    neg_words = ["fall","drop","decline","crash","negative","down","pressure","weak","sell","loss","war","tension","sanctions","conflict","attack","missile","tariff","crisis","escalation","threat","recession","surging","shock","risk","fear","petrol prices","fuel prices"]
    pos = neg = 0
    for _, news in news_list:
        lower = news.lower()
        pos  += sum(1 for w in pos_words if w in lower)
        neg  += sum(1 for w in neg_words if w in lower)
    total = pos + neg
    prob  = 50 if total == 0 else int((pos / total) * 100)
    if prob > 60:   return "🟢 Bullish", prob, "Buy on dips. Market likely positive."
    elif prob < 40: return "🔴 Bearish", prob, "Sell on rise. Market likely weak."
    return "🟡 Neutral", prob, "Wait for breakout confirmation."


# ==================================
# UI
# ==================================
ist     = pytz.timezone("Asia/Kolkata")
now_str = datetime.now(ist).strftime("%d %b %Y — %I:%M %p IST")

st.markdown("""
<div style="padding:24px 0 4px 0;">
  <div style="font-family:'Syne',sans-serif;font-size:30px;font-weight:800;color:#e0e6f0;">📊 NIFTY PRE-MARKET</div>
  <div style="font-family:'IBM Plex Mono',monospace;font-size:12px;color:#6b8cad;margin-top:4px;letter-spacing:2px;">SECTOR INTELLIGENCE DASHBOARD</div>
</div>
""", unsafe_allow_html=True)
st.markdown(f"<div style='color:#4a6a8a;font-size:12px;font-family:IBM Plex Mono;margin-bottom:20px;'>Last refresh: {now_str}</div>", unsafe_allow_html=True)

run_btn = st.button("⚡ RUN ANALYSIS")

if "ready" not in st.session_state:
    st.session_state.ready   = False
    st.session_state.news    = []
    st.session_state.impacts = []
    st.session_state.scores  = {}
    st.session_state.verdict = ""
    st.session_state.prob    = 50
    st.session_state.bias    = ""

if run_btn:
    with st.spinner("Fetching live news from free RSS feeds..."):
        news = get_market_news()
    if not news:
        st.error("RSS feeds temporarily unavailable. Please try again in a moment.")
    else:
        st.session_state.ready   = True
        st.session_state.news    = news
        st.session_state.impacts = analyze_india_impact(news)
        st.session_state.scores  = analyze_sectors(news)
        st.session_state.verdict, st.session_state.prob, st.session_state.bias = overall_sentiment(news)

if not st.session_state.ready:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;">
      <div style="font-size:56px;margin-bottom:16px;">📡</div>
      <div style="font-family:'Syne',sans-serif;font-size:20px;color:#4a6a8a;">Click ⚡ RUN ANALYSIS to fetch live market intelligence</div>
      <div style="font-size:12px;margin-top:8px;color:#2a3f5f;font-family:'IBM Plex Mono';">Free RSS feeds · No API keys · No login required</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

news    = st.session_state.news
impacts = st.session_state.impacts
scores  = st.session_state.scores
verdict = st.session_state.verdict
prob    = st.session_state.prob
bias    = st.session_state.bias

bull_cnt = sum(1 for _, i, _ in impacts if i == "BULLISH")
bear_cnt = sum(1 for _, i, _ in impacts if i == "BEARISH")
neut_cnt = sum(1 for _, i, _ in impacts if i == "NEUTRAL")
vc       = "bull" if prob > 60 else ("bear" if prob < 40 else "neut")

# Metric Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    color = "bull" if vc=="bull" else ("bear" if vc=="bear" else "neut")
    st.markdown(f'<div class="metric-card"><h4>Market Verdict</h4><div class="val {color}">{verdict}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><h4>Bullish Probability</h4><div class="val bull">{prob}%</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><h4>Headlines Fetched</h4><div class="val" style="color:#94b4d4">{len(news)}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><h4>Impact Signals</h4><div class="val" style="color:#94b4d4">🟢{bull_cnt} 🔴{bear_cnt} 🟡{neut_cnt}</div></div>', unsafe_allow_html=True)

# Heatmaps
st.markdown("<div class='section-title'>Sector Heatmaps</div>", unsafe_allow_html=True)
hc1, hc2 = st.columns([3, 2])
with hc1:
    st.markdown("**📊 NIFTY Sectors**")
    render_heatmap(scores, "NIFTY")
with hc2:
    st.markdown("**🏦 BANKNIFTY Sectors**")
    render_heatmap(scores, "BANKNIFTY")

st.markdown("""
<div style="display:flex;gap:16px;flex-wrap:wrap;font-size:11px;font-family:'IBM Plex Mono';margin:8px 0 24px 0;padding:10px 16px;background:#111827;border-radius:8px;border:1px solid #1e3a5f;">
  <span style="color:#00c853">● Strong Buy ≥+6</span>
  <span style="color:#4caf50">● Positive +3</span>
  <span style="color:#81c784">● Mild + +1</span>
  <span style="color:#455a64">● Neutral 0</span>
  <span style="color:#ef5350">● Mild - -1</span>
  <span style="color:#c62828">● Negative -3</span>
  <span style="color:#7f0000">● Strong Sell ≤-6</span>
</div>""", unsafe_allow_html=True)

# News Feed
st.markdown("<div class='section-title'>News Feed</div>", unsafe_allow_html=True)
nc1, nc2 = st.columns(2)
mkt_news = [(t, h) for t, h in news if t == "MARKET"]
geo_news = [(t, h) for t, h in news if t == "GEO"]
with nc1:
    st.markdown("**📈 Market & Economy**")
    for _, h in mkt_news:
        st.markdown(f'<div class="news-item mkt">{h}</div>', unsafe_allow_html=True)
with nc2:
    st.markdown("**🌍 Geopolitical & Global**")
    for _, h in geo_news:
        st.markdown(f'<div class="news-item geo">{h}</div>', unsafe_allow_html=True)

# India Impact
st.markdown("<div class='section-title'>India Market Impact</div>", unsafe_allow_html=True)
bull_imp = [(h, r) for h, i, r in impacts if i == "BULLISH"]
bear_imp = [(h, r) for h, i, r in impacts if i == "BEARISH"]
neut_imp = [(h, r) for h, i, r in impacts if i == "NEUTRAL"]
ic1, ic2 = st.columns(2)
with ic1:
    if bull_imp:
        st.markdown("**🟢 Bullish Signals**")
        for h, r in bull_imp[:4]:
            short = h[:70]+"..." if len(h)>70 else h
            st.markdown(f'<div class="impact-row"><span class="badge badge-bull">BULL</span><div><div style="color:#c9d8e8;margin-bottom:3px;">{short}</div><div style="color:#4a8a6a;font-size:11px;">↳ {r}</div></div></div>', unsafe_allow_html=True)
    if neut_imp:
        st.markdown("**🟡 Neutral**")
        for h, r in neut_imp[:2]:
            short = h[:70]+"..." if len(h)>70 else h
            st.markdown(f'<div class="impact-row"><span class="badge badge-neut">NEUT</span><div><div style="color:#c9d8e8;margin-bottom:3px;">{short}</div><div style="color:#7a6a2a;font-size:11px;">↳ {r}</div></div></div>', unsafe_allow_html=True)
with ic2:
    if bear_imp:
        st.markdown("**🔴 Bearish Signals**")
        for h, r in bear_imp[:5]:
            short = h[:70]+"..." if len(h)>70 else h
            st.markdown(f'<div class="impact-row"><span class="badge badge-bear">BEAR</span><div><div style="color:#c9d8e8;margin-bottom:3px;">{short}</div><div style="color:#8a3a3a;font-size:11px;">↳ {r}</div></div></div>', unsafe_allow_html=True)

# Verdict
st.markdown("<div class='section-title'>Trading Verdict</div>", unsafe_allow_html=True)
vcss   = {"bull":"verdict-bull","bear":"verdict-bear","neut":"verdict-neut"}[vc]
vcolor = {"bull":"#00e676","bear":"#ff5252","neut":"#ffca28"}[vc]
st.markdown(f"""
<div class="verdict-box {vcss}">
  <div style="font-family:'Syne',sans-serif;font-size:26px;font-weight:800;color:{vcolor};margin-bottom:8px;">{verdict}</div>
  <div style="font-size:14px;color:#c9d8e8;margin-bottom:12px;font-family:'IBM Plex Mono';">{bias}</div>
  <div style="font-size:13px;color:#6b8cad;font-family:'IBM Plex Mono';">
    📈 Bullish: <b style="color:#00e676;">{prob}%</b> &nbsp;|&nbsp;
    🔴 Bearish: <b style="color:#ff5252;">{100-prob}%</b> &nbsp;|&nbsp; Focus: NIFTY | BANKNIFTY
  </div>
</div>
<div style="height:32px"></div>
""", unsafe_allow_html=True)
