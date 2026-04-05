import streamlit as st
import feedparser
import pytz
import plotly.graph_objects as go
from datetime import datetime

# ==================================
# 🎨 PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="Nifty Pre-Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Syne:wght@700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'IBM Plex Mono', monospace;
    background-color: #0a0e17;
    color: #e0e6f0;
  }
  .stApp { background-color: #0a0e17; }

  h1, h2, h3 {
    font-family: 'Syne', sans-serif;
    letter-spacing: -0.5px;
  }

  .metric-card {
    background: linear-gradient(135deg, #111827 0%, #1a2235 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
  }
  .metric-card h4 { margin: 0 0 4px 0; font-size: 11px; color: #6b8cad; text-transform: uppercase; letter-spacing: 2px; }
  .metric-card .val { font-size: 28px; font-weight: 700; font-family: 'Syne', sans-serif; }
  .bull { color: #00e676; }
  .bear { color: #ff5252; }
  .neut { color: #ffca28; }

  .news-item {
    padding: 10px 14px;
    border-left: 3px solid #1e3a5f;
    margin: 6px 0;
    background: #111827;
    border-radius: 0 8px 8px 0;
    font-size: 13px;
    line-height: 1.5;
  }
  .news-item.geo { border-left-color: #7c3aed; }
  .news-item.mkt { border-left-color: #0ea5e9; }

  .impact-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 10px 0;
    border-bottom: 1px solid #1a2235;
    font-size: 13px;
  }
  .badge {
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    letter-spacing: 1px;
  }
  .badge-bull { background: #052e16; color: #00e676; border: 1px solid #00e676; }
  .badge-bear { background: #2d0a0a; color: #ff5252; border: 1px solid #ff5252; }
  .badge-neut { background: #2d2200; color: #ffca28; border: 1px solid #ffca28; }

  .stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #0ea5e9) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    padding: 12px 32px !important;
    font-size: 14px !important;
    letter-spacing: 1px !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(14,165,233,0.4) !important;
  }

  div[data-testid="stHorizontalBlock"] { gap: 16px; }
  .stPlotlyChart { border-radius: 12px; overflow: hidden; }
  
  .section-title {
    font-family: 'Syne', sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #94b4d4;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin: 28px 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e3a5f;
  }
  
  .verdict-box {
    border-radius: 14px;
    padding: 24px;
    text-align: center;
    margin: 16px 0;
  }
  .verdict-bull { background: linear-gradient(135deg, #052e16, #064e3b); border: 1px solid #00e676; }
  .verdict-bear { background: linear-gradient(135deg, #2d0a0a, #450a0a); border: 1px solid #ff5252; }
  .verdict-neut { background: linear-gradient(135deg, #2d2200, #422006); border: 1px solid #ffca28; }
</style>
""", unsafe_allow_html=True)


# ==================================
# 📰 FREE RSS NEWS FEEDS  (no API keys)
# ==================================

RSS_SOURCES = {
    # ── 🇮🇳 India Market / Economy ─────────────────────────────────────────────
    "MARKET": [
        # Economic Times — Markets
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        # Economic Times — Economy
        "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",
        # Moneycontrol — Top News
        "https://www.moneycontrol.com/rss/MCtopnews.xml",
        # Business Standard — Markets
        "https://www.business-standard.com/rss/markets-106.rss",
        # LiveMint — Markets
        "https://www.livemint.com/rss/markets",
        # Google News — Nifty / India markets
        "https://news.google.com/rss/search?q=Nifty+Sensex+RBI+India+economy+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
        # Google News — RBI / Inflation / Budget
        "https://news.google.com/rss/search?q=RBI+repo+rate+inflation+India+budget+GDP&hl=en-IN&gl=IN&ceid=IN:en",
    ],

    # ── 🌍 Geopolitics / Global / Crude ────────────────────────────────────────
    "GEO": [
        # Reuters — World News
        "https://feeds.reuters.com/reuters/worldNews",
        # Reuters — Business News
        "https://feeds.reuters.com/reuters/businessNews",
        # Google News — Iran / Israel / Middle East / War
        "https://news.google.com/rss/search?q=Iran+Israel+war+Middle+East+sanctions+conflict&hl=en&gl=US&ceid=US:en",
        # Google News — Crude oil / Energy / OPEC
        "https://news.google.com/rss/search?q=crude+oil+brent+OPEC+energy+prices+petrol&hl=en&gl=US&ceid=US:en",
        # Google News — US Fed / Global economy
        "https://news.google.com/rss/search?q=US+Fed+interest+rate+dollar+FII+global+economy&hl=en&gl=US&ceid=US:en",
        # Al Jazeera — Middle East
        "https://www.aljazeera.com/xml/rss/all.xml",
        # BBC — World
        "http://feeds.bbci.co.uk/news/world/rss.xml",
    ],
}

@st.cache_data(ttl=600)
def get_market_news():
    headlines = []

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for tag, urls in RSS_SOURCES.items():
        for url in urls:
            try:
                feed = feedparser.parse(url, request_headers=HEADERS)
                count = 0
                for entry in feed.entries:
                    title = (entry.get("title") or "").strip()
                    # Skip empty, very short, or duplicate titles
                    if title and len(title) > 20:
                        headlines.append((tag, title))
                        count += 1
                    if count >= 4:   # max 4 headlines per feed
                        break
            except Exception:
                pass

    # Deduplicate
    seen, unique = set(), []
    for (tag, h) in headlines:
        key = h[:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append((tag, h))

    return unique[:30]


# ==================================
# 🏦 SECTOR DEFINITIONS
# ==================================

NIFTY_SECTORS = {
    "IT / Tech":         {"keywords": ["it", "tech", "software", "nasdaq", "infosys", "tcs", "wipro", "hcl", "tech mahindra"], "index": "NIFTY"},
    "Auto":              {"keywords": ["auto", "car", "vehicle", "ev", "maruti", "tata motors", "bajaj auto", "hero"],           "index": "NIFTY"},
    "FMCG":              {"keywords": ["fmcg", "consumer", "retail", "hul", "nestle", "dabur", "godrej"],                        "index": "NIFTY"},
    "Pharma":            {"keywords": ["pharma", "drug", "medicine", "sun pharma", "cipla", "dr reddy"],                         "index": "NIFTY"},
    "Metal / Mining":    {"keywords": ["metal", "steel", "iron", "tata steel", "jsw", "vedanta", "hindalco", "coal"],            "index": "NIFTY"},
    "Energy / Oil":      {"keywords": ["oil", "crude", "gas", "energy", "opec", "ongc", "reliance", "bpcl", "iocl", "petrol",
                                       "fuel", "brent", "strait", "hormuz", "persian gulf", "energy shock"],                     "index": "NIFTY"},
    "Infra / Realty":    {"keywords": ["infra", "infrastructure", "realty", "real estate", "construction", "dlf", "cement"],     "index": "NIFTY"},
    "Chemicals":         {"keywords": ["chemical", "specialty chemical", "atul", "basf", "upl", "agrochemical", "fertilizer"],   "index": "NIFTY"},
    "Capital Goods":     {"keywords": ["capital goods", "bhel", "engineering", "havells", "polycab", "bosch", "defence"],        "index": "NIFTY"},
    "Telecom / Media":   {"keywords": ["telecom", "airtel", "5g", "broadband", "media", "entertainment", "ott"],                 "index": "NIFTY"},
    "Textile":           {"keywords": ["textile", "apparel", "cotton", "yarn", "fabric", "garment", "spinning"],                 "index": "NIFTY"},
    "Logistics":         {"keywords": ["logistics", "shipping", "freight", "cargo", "supply chain", "transport"],                "index": "NIFTY"},
    "Hospitality":       {"keywords": ["hotel", "hospitality", "tourism", "travel", "resort", "airline"],                        "index": "NIFTY"},
    "Agri":              {"keywords": ["agri", "agriculture", "fertilizer", "pesticide", "seeds", "sugar", "farm"],              "index": "NIFTY"},
    "BANKING (Private)": {"keywords": ["hdfc bank", "icici bank", "axis bank", "kotak", "indusind", "private bank"],             "index": "BANKNIFTY"},
    "BANKING (PSU)":     {"keywords": ["sbi", "pnb", "bank of baroda", "canara", "psu bank", "state bank"],                     "index": "BANKNIFTY"},
    "NBFC / Financial":  {"keywords": ["nbfc", "bajaj finance", "muthoot", "shriram", "financial", "loan", "microfinance"],      "index": "BANKNIFTY"},
    "BANKING (General)": {"keywords": ["bank", "rbi", "repo", "rate cut", "rate hike", "credit", "deposit", "npa", "banking"],  "index": "BANKNIFTY"},
}

POSITIVE_WORDS = [
    "gain", "rise", "surge", "positive", "growth", "rally", "jump", "boost",
    "high", "buy", "strong", "record", "profit", "recovery", "optimism",
    "peace", "deal", "agreement", "ceasefire", "easing", "up", "increase",
    "rate cut", "gdp growth", "inflow", "fii buying"
]

NEGATIVE_WORDS = [
    "fall", "drop", "decline", "crash", "negative", "down", "low", "pressure",
    "weak", "sell", "loss", "war", "tension", "sanctions", "conflict", "attack",
    "missile", "tariff", "ban", "crisis", "strike", "escalation", "threat",
    "recession", "default", "unrest", "rate hike", "outflow", "fii selling",
    "inflation rises", "oil surges", "crude up", "petrol prices", "fuel prices",
    "energy shock", "gas prices", "surging", "double", "shock", "risk"
]


# ==================================
# 📊 SECTOR ANALYZER
# ==================================

def analyze_sectors(news_list):
    news_texts    = [h for (_, h) in news_list]
    sector_scores = {sector: 0 for sector in NIFTY_SECTORS}

    for news in news_texts:
        lower       = news.lower()
        is_positive = any(w in lower for w in POSITIVE_WORDS)
        is_negative = any(w in lower for w in NEGATIVE_WORDS)
        for sector, info in NIFTY_SECTORS.items():
            for keyword in info["keywords"]:
                if keyword in lower:
                    if is_positive and not is_negative:
                        sector_scores[sector] += 2
                    elif is_negative and not is_positive:
                        sector_scores[sector] -= 2
                    elif is_positive and is_negative:
                        sector_scores[sector] -= 1
                    break

    combined = " ".join(news_texts).lower()

    # Macro rules
    if any(w in combined for w in [
        "crude up", "oil surges", "oil price up", "brent rises", "crude rises",
        "petrol prices", "fuel prices", "energy shock", "gas prices double",
        "oil prices set to rise", "strait of hormuz", "persian gulf"
    ]):
        sector_scores["Energy / Oil"]      += 5
        sector_scores["Auto"]              -= 2
        sector_scores["FMCG"]              -= 2
        sector_scores["BANKING (General)"] -= 1
        sector_scores["NBFC / Financial"]  -= 1
        sector_scores["Metal / Mining"]    -= 1

    if any(w in combined for w in ["crude falls", "oil drops", "oil price down", "brent falls"]):
        sector_scores["Energy / Oil"] -= 2
        sector_scores["Auto"]         += 2
        sector_scores["FMCG"]         += 1
        sector_scores["BANKING (General)"] += 1

    if any(w in combined for w in ["rate cut", "repo rate cut", "rbi cut"]):
        sector_scores["BANKING (Private)"] += 3
        sector_scores["BANKING (PSU)"]     += 3
        sector_scores["BANKING (General)"] += 2
        sector_scores["NBFC / Financial"]  += 3
        sector_scores["Auto"]              += 2
        sector_scores["Infra / Realty"]    += 2

    if any(w in combined for w in ["rate hike", "repo rate hike", "rbi hike"]):
        sector_scores["BANKING (Private)"] -= 2
        sector_scores["BANKING (PSU)"]     -= 2
        sector_scores["BANKING (General)"] -= 2
        sector_scores["NBFC / Financial"]  -= 3
        sector_scores["Auto"]              -= 2
        sector_scores["Infra / Realty"]    -= 2

    if any(w in combined for w in [
        "iran israel", "iran war", "us iran", "war", "missile attack",
        "middle east conflict", "strait of hormuz", "persian gulf"
    ]):
        for sector in sector_scores:
            if sector != "Energy / Oil":
                sector_scores[sector] -= 2
        sector_scores["Energy / Oil"] += 5

    if any(w in combined for w in ["fed rate cut", "federal reserve cut", "fed dovish"]):
        sector_scores["IT / Tech"]         += 2
        sector_scores["BANKING (Private)"] += 1
        sector_scores["NBFC / Financial"]  += 1

    if any(w in combined for w in ["rupee falls", "rupee weakens", "inr down"]):
        sector_scores["IT / Tech"] += 2
        sector_scores["Pharma"]    += 1
        sector_scores["Auto"]      -= 1
        sector_scores["FMCG"]      -= 1

    if any(w in combined for w in ["fii buying", "fii inflow", "fpi buying"]):
        sector_scores["BANKING (Private)"] += 2
        sector_scores["IT / Tech"]         += 1

    if any(w in combined for w in ["fii selling", "fii outflow", "fpi selling"]):
        sector_scores["BANKING (Private)"] -= 2
        sector_scores["IT / Tech"]         -= 1

    return sector_scores


# ==================================
# 🗺️ HEATMAP BUILDER
# ==================================

def build_heatmap(sector_scores):
    nifty_items   = [(s, v) for s, v in sector_scores.items() if NIFTY_SECTORS[s]["index"] == "NIFTY"]
    bnifty_items  = [(s, v) for s, v in sector_scores.items() if NIFTY_SECTORS[s]["index"] == "BANKNIFTY"]

    nifty_items.sort(key=lambda x: -x[1])
    bnifty_items.sort(key=lambda x: -x[1])

    def score_to_label(score):
        if score >= 6:   return "🚀 Strong Buy"
        if score >= 3:   return "⬆ Positive"
        if score >= 1:   return "↗ Mild +ve"
        if score == 0:   return "↔ Neutral"
        if score >= -2:  return "↘ Mild -ve"
        if score >= -4:  return "⬇ Negative"
        return "💥 Strong Sell"

    def make_chart(items, title, height=420):
        labels  = [s for s, _ in items]
        scores  = [v for _, v in items]
        texts   = [f"{s}<br><b>{score_to_label(v)}</b><br>Score: {v:+d}" for s, v in items]

        # Normalize to 0-1 for color
        mn, mx = -8, 8
        norm   = [(max(mn, min(mx, v)) - mn) / (mx - mn) for v in scores]

        fig = go.Figure(go.Bar(
            x=scores,
            y=labels,
            orientation="h",
            marker=dict(
                color=norm,
                colorscale=[
                    [0.00, "#7f0000"],
                    [0.20, "#c62828"],
                    [0.38, "#ef5350"],
                    [0.48, "#ff8a65"],
                    [0.50, "#37474f"],
                    [0.52, "#81c784"],
                    [0.65, "#4caf50"],
                    [0.82, "#00e676"],
                    [1.00, "#00c853"],
                ],
                cmin=0,
                cmax=1,
                line=dict(width=0),
            ),
            text=[f"{v:+d}" for v in scores],
            textposition="outside",
            textfont=dict(size=12, color="#e0e6f0", family="IBM Plex Mono"),
            hovertext=texts,
            hoverinfo="text",
        ))

        fig.add_vline(x=0, line_color="#4a5568", line_width=1.5)

        fig.update_layout(
            title=dict(
                text=title,
                font=dict(family="Syne, sans-serif", size=18, color="#94b4d4"),
                x=0.01,
            ),
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            height=height,
            margin=dict(l=10, r=60, t=50, b=20),
            xaxis=dict(
                range=[-12, 14],
                showgrid=True,
                gridcolor="#1e3a5f",
                gridwidth=0.5,
                zeroline=False,
                tickfont=dict(color="#6b8cad", family="IBM Plex Mono"),
                title=dict(text="Sentiment Score", font=dict(color="#6b8cad", size=11)),
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(color="#c9d8e8", family="IBM Plex Mono", size=12),
            ),
            showlegend=False,
        )
        return fig

    fig_nifty   = make_chart(nifty_items,  "📊 NIFTY — Sector Heatmap", height=460)
    fig_bnifty  = make_chart(bnifty_items, "🏦 BANKNIFTY — Sector Heatmap", height=300)
    return fig_nifty, fig_bnifty


# ==================================
# 🇮🇳 INDIA IMPACT RULES
# ==================================

INDIA_IMPACT_RULES = [
    (["rbi rate cut", "repo rate cut", "rate cut", "interest rate cut"],
     "BULLISH", "RBI rate cut → cheaper loans → Banking, Auto, Realty rally"),
    (["rbi rate hike", "repo rate hike", "rate hike", "interest rate hike"],
     "BEARISH", "Rate hike → costly borrowing → rate-sensitive sectors under pressure"),
    (["rbi pause", "rbi holds rate", "rate unchanged"],
     "NEUTRAL", "RBI holds rates → stability signal → market may consolidate"),
    (["inflation rises", "cpi up", "inflation high", "wpi up"],
     "BEARISH", "Rising inflation → RBI may tighten → consumer stocks under pressure"),
    (["inflation eases", "cpi down", "inflation falls"],
     "BULLISH", "Falling inflation → room for rate cuts → positive for all sectors"),
    (["crude rises", "oil surges", "oil price up", "brent rises", "crude up",
      "petrol prices", "fuel prices rise", "energy shock", "oil prices set to rise"],
     "BEARISH", "Rising crude → India imports 85% oil → CAD widens → Rupee weakens → Bearish"),
    (["crude falls", "oil drops", "oil price down", "crude down", "brent falls"],
     "BULLISH", "Falling crude → lower import bill → CAD improves → Rupee strengthens"),
    (["fed rate cut", "us rate cut", "federal reserve cut", "fed dovish"],
     "BULLISH", "Fed rate cut → dollar weakens → FII inflows into Indian markets"),
    (["fed rate hike", "us rate hike", "federal reserve hike", "fed hawkish"],
     "BEARISH", "Fed hike → stronger dollar → FII outflows from India"),
    (["iran israel", "israel iran", "iran missile", "iran war", "us iran", "bomb iran"],
     "BEARISH", "Iran-Israel/US conflict → crude oil supply shock → global risk-off → Very Bearish"),
    (["strait of hormuz", "hormuz", "persian gulf shipping"],
     "BEARISH", "Hormuz threat → India's oil imports at risk → crude spikes → INR weakens badly"),
    (["middle east conflict", "middle east war", "opec cut", "oil supply cut"],
     "BEARISH", "Middle East tension → crude supply disruption → India import costs rise"),
    (["ceasefire", "peace deal", "tension eases", "conflict resolved"],
     "BULLISH", "Geopolitical easing → crude falls → risk-on → FII inflows → rally"),
    (["fii buying", "fii inflow", "fpi buying"],
     "BULLISH", "FII buying → direct demand for Indian equities → Nifty & BankNifty rally"),
    (["fii selling", "fii outflow", "fpi selling"],
     "BEARISH", "FII selling → supply pressure on Indian equities → Nifty correction likely"),
    (["gdp growth", "india gdp rises", "strong gdp"],
     "BULLISH", "Strong GDP growth → earnings upgrade cycle → positive for all sectors"),
    (["gdp falls", "gdp slowdown", "recession"],
     "BEARISH", "GDP slowdown → earnings pressure → broad market selloff expected"),
    (["rupee falls", "rupee weakens", "inr down"],
     "BEARISH", "Weak Rupee → costlier imports → FII reduce India exposure"),
    (["rupee rises", "rupee strengthens", "inr up"],
     "BULLISH", "Strong Rupee → lower import costs → FII confidence → positive"),
    (["us china trade war", "china tariff", "us tariff", "trade war"],
     "BEARISH", "US-China trade war → global slowdown fears → IT sector hit → markets weak"),
    (["dow jones falls", "nasdaq down", "s&p falls", "wall street falls"],
     "BEARISH", "US market fall → negative global cues → India likely to open gap-down"),
    (["dow jones rises", "nasdaq up", "s&p rises", "wall street rises"],
     "BULLISH", "Positive US cues → FII optimism → India likely to open gap-up"),
]

def analyze_india_impact(news_list):
    results  = []
    pos_wds  = ["gain", "rise", "surge", "growth", "rally", "boost", "profit", "recovery",
                "record", "deal", "peace", "easing", "strong", "positive", "optimism"]
    neg_wds  = ["fall", "drop", "decline", "crash", "war", "tension", "sanctions", "conflict",
                "crisis", "loss", "weak", "threat", "pressure", "fear", "attack", "unrest",
                "surging", "shock", "risk", "concern", "worry"]

    for (_, news) in news_list:
        lower   = news.lower()
        matched = False
        for (triggers, impact, reason) in INDIA_IMPACT_RULES:
            for trigger in triggers:
                if trigger in lower:
                    results.append((news, impact, reason))
                    matched = True
                    break
            if matched:
                break
        if not matched:
            pos = any(w in lower for w in pos_wds)
            neg = any(w in lower for w in neg_wds)
            if pos and not neg:
                results.append((news, "BULLISH", "Positive global/economic cues → supportive for Indian markets"))
            elif neg and not pos:
                results.append((news, "BEARISH", "Negative global/geopolitical cues → risk-off pressure on Indian markets"))
            elif neg and pos:
                results.append((news, "BEARISH", "Mixed but risk-leaning cues → cautious stance"))
    return results


# ==================================
# 🧠 OVERALL SENTIMENT
# ==================================

def overall_sentiment(news_list):
    pos_words = ["gain", "rise", "surge", "positive", "growth", "rally", "jump", "boost",
                 "buy", "strong", "record", "profit", "recovery", "optimism", "peace", "deal",
                 "agreement", "ceasefire", "easing"]
    neg_words = ["fall", "drop", "decline", "crash", "negative", "down", "pressure", "weak",
                 "sell", "loss", "war", "tension", "sanctions", "conflict", "attack", "missile",
                 "tariff", "ban", "crisis", "strike", "escalation", "threat", "recession",
                 "surging", "shock", "risk", "concern", "fear", "petrol prices", "fuel prices"]
    pos = neg = 0
    for (_, news) in news_list:
        lower = news.lower()
        pos  += sum(1 for w in pos_words if w in lower)
        neg  += sum(1 for w in neg_words if w in lower)

    total = pos + neg
    prob  = 50 if total == 0 else int((pos / total) * 100)
    if prob > 60:
        return "🟢 Bullish", prob, "Buy on dips. Market likely positive."
    elif prob < 40:
        return "🔴 Bearish", prob, "Sell on rise. Market likely weak."
    return "🟡 Neutral", prob, "Wait for breakout confirmation."



# ==================================
# 🖥️ STREAMLIT UI
# ==================================

# Header
st.markdown("""
<div style="padding: 32px 0 8px 0;">
  <div style="font-family:'Syne',sans-serif; font-size:32px; font-weight:800; color:#e0e6f0; line-height:1.1;">
    📊 NIFTY PRE-MARKET
  </div>
  <div style="font-family:'IBM Plex Mono',monospace; font-size:13px; color:#6b8cad; margin-top:6px; letter-spacing:2px;">
    SECTOR INTELLIGENCE DASHBOARD
  </div>
</div>
""", unsafe_allow_html=True)

ist = pytz.timezone("Asia/Kolkata")
now_str = datetime.now(ist).strftime("%d %b %Y — %I:%M %p IST")
st.markdown(f"<div style='color:#4a6a8a; font-size:12px; font-family:IBM Plex Mono; margin-bottom:24px;'>Last refresh: {now_str}</div>", unsafe_allow_html=True)

run_btn = st.button("⚡ RUN ANALYSIS", use_container_width=False)

# Session state
if "report_ready" not in st.session_state:
    st.session_state.report_ready = False
    st.session_state.news         = []
    st.session_state.impacts      = []
    st.session_state.scores       = {}
    st.session_state.verdict      = ""
    st.session_state.prob         = 50
    st.session_state.bias         = ""

if run_btn:
    with st.spinner("Fetching live news from RSS feeds..."):
        news = get_market_news()
        if not news:
            st.error("⚠️ No news fetched — RSS feeds may be temporarily unavailable. Try again in a moment.")
        else:
            impacts               = analyze_india_impact(news)
            scores                = analyze_sectors(news)
            verdict, prob, bias   = overall_sentiment(news)

            st.session_state.report_ready = True
            st.session_state.news         = news
            st.session_state.impacts      = impacts
            st.session_state.scores       = scores
            st.session_state.verdict      = verdict
            st.session_state.prob         = prob
            st.session_state.bias         = bias


if not st.session_state.report_ready:
    st.markdown("""
    <div style="text-align:center; padding:80px 20px; color:#2a3f5f;">
      <div style="font-size:60px; margin-bottom:16px;">📡</div>
      <div style="font-family:'Syne',sans-serif; font-size:22px; color:#4a6a8a;">
        Click ⚡ RUN ANALYSIS to fetch live market intelligence
      </div>
      <div style="font-size:13px; margin-top:8px; color:#2a3f5f; font-family:'IBM Plex Mono';">
        Aggregates 7 free RSS feeds • Sector heatmap • India impact analysis
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Top Metrics ────────────────────────────────────────────────────────────────
news     = st.session_state.news
impacts  = st.session_state.impacts
scores   = st.session_state.scores
verdict  = st.session_state.verdict
prob     = st.session_state.prob
bias     = st.session_state.bias

bull_cnt = len([i for i in impacts if i[1] == "BULLISH"])
bear_cnt = len([i for i in impacts if i[1] == "BEARISH"])
neut_cnt = len([i for i in impacts if i[1] == "NEUTRAL"])

vc = "bull" if prob > 60 else ("bear" if prob < 40 else "neut")
vc_cls = {"bull": "verdict-bull", "bear": "verdict-bear", "neut": "verdict-neut"}[vc]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
      <h4>Market Verdict</h4>
      <div class="val {'bull' if vc=='bull' else 'bear' if vc=='bear' else 'neut'}">{verdict}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
      <h4>Bullish Probability</h4>
      <div class="val bull">{prob}%</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
      <h4>Headlines Analyzed</h4>
      <div class="val" style="color:#94b4d4">{len(news)}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
      <h4>Impact Signals</h4>
      <div class="val" style="color:#94b4d4">🟢{bull_cnt} 🔴{bear_cnt} 🟡{neut_cnt}</div>
    </div>""", unsafe_allow_html=True)

# ── Heatmaps ───────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Sector Heatmaps</div>", unsafe_allow_html=True)
fig_nifty, fig_bnifty = build_heatmap(scores)

hc1, hc2 = st.columns([3, 2])
with hc1:
    st.plotly_chart(fig_nifty,  use_container_width=True, config={"displayModeBar": False})
with hc2:
    st.plotly_chart(fig_bnifty, use_container_width=True, config={"displayModeBar": False})

# ── Score Legend ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; gap:12px; flex-wrap:wrap; font-size:11px; font-family:'IBM Plex Mono'; 
     margin:-8px 0 24px 0; padding:12px 16px; background:#111827; border-radius:8px; border:1px solid #1e3a5f;">
  <span style="color:#00c853">●  ≥ +6  Strong Buy</span>
  <span style="color:#4caf50">●  +3 to +5  Positive</span>
  <span style="color:#81c784">●  +1 to +2  Mild Positive</span>
  <span style="color:#546e7a">●  0  Neutral</span>
  <span style="color:#ef5350">●  -1 to -2  Mild Negative</span>
  <span style="color:#c62828">●  -3 to -5  Negative</span>
  <span style="color:#7f0000">●  ≤ -6  Strong Sell</span>
</div>
""", unsafe_allow_html=True)

# ── News Feed ──────────────────────────────────────────────────────────────────
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

# ── India Impact ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>India Market Impact</div>", unsafe_allow_html=True)

bull_imp = [(h, r) for h, i, r in impacts if i == "BULLISH"]
bear_imp = [(h, r) for h, i, r in impacts if i == "BEARISH"]
neut_imp = [(h, r) for h, i, r in impacts if i == "NEUTRAL"]

ic1, ic2 = st.columns(2)
with ic1:
    if bull_imp:
        st.markdown("**🟢 Bullish Signals**")
        for h, r in bull_imp[:4]:
            short = h[:70] + "..." if len(h) > 70 else h
            st.markdown(f"""
            <div class="impact-row">
              <span class="badge badge-bull">BULL</span>
              <div>
                <div style="color:#c9d8e8; margin-bottom:3px;">{short}</div>
                <div style="color:#4a8a6a; font-size:11px;">↳ {r}</div>
              </div>
            </div>""", unsafe_allow_html=True)
    if neut_imp:
        st.markdown("**🟡 Neutral**")
        for h, r in neut_imp[:2]:
            short = h[:70] + "..." if len(h) > 70 else h
            st.markdown(f"""
            <div class="impact-row">
              <span class="badge badge-neut">NEUT</span>
              <div>
                <div style="color:#c9d8e8; margin-bottom:3px;">{short}</div>
                <div style="color:#7a6a2a; font-size:11px;">↳ {r}</div>
              </div>
            </div>""", unsafe_allow_html=True)

with ic2:
    if bear_imp:
        st.markdown("**🔴 Bearish Signals**")
        for h, r in bear_imp[:5]:
            short = h[:70] + "..." if len(h) > 70 else h
            st.markdown(f"""
            <div class="impact-row">
              <span class="badge badge-bear">BEAR</span>
              <div>
                <div style="color:#c9d8e8; margin-bottom:3px;">{short}</div>
                <div style="color:#8a3a3a; font-size:11px;">↳ {r}</div>
              </div>
            </div>""", unsafe_allow_html=True)

# ── Verdict Box ────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Trading Verdict</div>", unsafe_allow_html=True)
vc_css = vc_cls
bull_pct = prob
bear_pct = 100 - prob

vcolor = "#00e676" if vc == "bull" else ("#ff5252" if vc == "bear" else "#ffca28")
st.markdown(f"""
<div class="verdict-box {vc_css}">
  <div style="font-family:'Syne',sans-serif; font-size:26px; font-weight:800; color:{vcolor}; margin-bottom:8px;">
    {verdict}
  </div>
  <div style="font-size:14px; color:#c9d8e8; margin-bottom:12px; font-family:'IBM Plex Mono';">
    {bias}
  </div>
  <div style="font-size:13px; color:#6b8cad; font-family:'IBM Plex Mono';">
    📈 Bullish: <b style="color:#00e676;">{bull_pct}%</b> &nbsp;|&nbsp; 
    🔴 Bearish: <b style="color:#ff5252;">{bear_pct}%</b> &nbsp;|&nbsp;
    Focus: NIFTY | BANKNIFTY
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
