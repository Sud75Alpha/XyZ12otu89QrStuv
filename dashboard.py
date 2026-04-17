"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           GOLD/DXY PRO DASHBOARD — VERSION HÉBERGÉE                         ║
║   Streamlit · connexion API · style TradingView dark                        ║
║                                                                              ║
║   Config : définir API_URL et API_KEY dans les secrets Streamlit            ║
║   Lancement : streamlit run dashboard.py                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import json
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG — modifiable via Streamlit Secrets ou variables d'env
# ─────────────────────────────────────────────────────────────────────────────

try:
    API_URL = st.secrets["API_URL"]
    API_KEY = st.secrets["API_KEY"]
except Exception:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "gold_dxy_secret_2024")

API_TIMEOUT = 4   # secondes
API_KEY = st.secrets["API_KEY"]
HEADERS = {"X-API-Key": API_KEY}

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GOLD/DXY Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CSS GLOBAL — Dark TradingView Pro
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');

:root {
    --bg:          #080b0f;
    --bg2:         #0d1117;
    --bg3:         #111820;
    --glass:       rgba(255,255,255,0.025);
    --glass2:      rgba(255,255,255,0.05);
    --border:      rgba(255,255,255,0.055);
    --border-gold: rgba(247,181,41,0.3);
    --gold:        #f7b529;
    --gold2:       #ffd166;
    --green:       #00d4aa;
    --red:         #ff4d6a;
    --blue:        #4da6ff;
    --purple:      #a78bfa;
    --text:        #dde3ee;
    --text2:       #6b7a94;
    --text3:       #2e3a4e;
    --mono:        'JetBrains Mono', monospace;
    --display:     'Syne', sans-serif;
}

/* ── Base ── */
html, body, [class*="css"]          { font-family: var(--mono) !important; background: var(--bg) !important; color: var(--text) !important; }
.main .block-container               { padding: 0.75rem 1.25rem 2rem !important; max-width: 100% !important; }
#MainMenu, footer, header, .stDeployButton { visibility: hidden !important; display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"]            { background: linear-gradient(175deg, #0c1018 0%, #080b0f 100%) !important; border-right: 1px solid var(--border) !important; }

/* ── Metrics ── */
[data-testid="metric-container"]     { background: var(--glass) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; padding: 10px 14px !important; transition: border-color 0.2s; }
[data-testid="metric-container"]:hover { border-color: var(--border-gold) !important; }
[data-testid="stMetricLabel"]        { color: var(--text2) !important; font-size: 0.62rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }
[data-testid="stMetricValue"]        { font-size: 1.2rem !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"]        { font-size: 0.7rem !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]    { background: var(--glass) !important; border-radius: 8px !important; padding: 4px !important; gap: 4px !important; border: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"]         { background: transparent !important; border-radius: 6px !important; color: var(--text2) !important; font-size: 0.72rem !important; letter-spacing: 0.06em !important; padding: 5px 14px !important; }
.stTabs [aria-selected="true"]       { background: rgba(247,181,41,0.12) !important; color: var(--gold) !important; }

/* ── Radio ── */
.stRadio > div                       { gap: 5px !important; }
.stRadio label                       { background: var(--glass) !important; border: 1px solid var(--border) !important; border-radius: 6px !important; padding: 3px 11px !important; font-size: 0.72rem !important; color: var(--text2) !important; cursor: pointer !important; transition: all 0.15s !important; }
.stRadio label:hover                 { border-color: var(--border-gold) !important; color: var(--gold) !important; }

/* ── Buttons ── */
.stButton > button                   { background: rgba(247,181,41,0.08) !important; border: 1px solid var(--border-gold) !important; color: var(--gold) !important; font-family: var(--mono) !important; font-size: 0.72rem !important; border-radius: 6px !important; transition: all 0.2s !important; }
.stButton > button:hover             { background: rgba(247,181,41,0.18) !important; box-shadow: 0 0 14px rgba(247,181,41,0.15) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar                  { width: 3px; height: 3px; }
::-webkit-scrollbar-track            { background: var(--bg); }
::-webkit-scrollbar-thumb            { background: var(--border); border-radius: 2px; }

/* ── Plotly ── */
.js-plotly-plot                      { border-radius: 10px !important; overflow: hidden !important; }

/* ── Custom classes ── */
.card {
    background: var(--glass); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
}
.card:hover { border-color: var(--border-gold); }

.badge-buy  { display:inline-block; background:rgba(0,212,170,.15); border:1px solid rgba(0,212,170,.4); color:#00d4aa; border-radius:5px; padding:2px 10px; font-size:.68rem; font-weight:700; letter-spacing:.06em; }
.badge-sell { display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:5px; padding:2px 10px; font-size:.68rem; font-weight:700; letter-spacing:.06em; }
.badge-wait { display:inline-block; background:rgba(107,122,148,.1); border:1px solid rgba(107,122,148,.25); color:#6b7a94; border-radius:5px; padding:2px 10px; font-size:.68rem; font-weight:700; letter-spacing:.06em; }
.badge-ant  { display:inline-block; background:rgba(167,139,250,.12); border:1px solid rgba(167,139,250,.4); color:#a78bfa; border-radius:5px; padding:2px 10px; font-size:.65rem; font-weight:700; letter-spacing:.04em; }

.lbl { font-size:.6rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--text3); margin-bottom:5px; }
.live-dot { display:inline-block; width:6px; height:6px; background:var(--green); border-radius:50%; box-shadow:0 0 7px var(--green); animation:pulse 1.4s infinite; margin-right:5px; }
.offline-dot { display:inline-block; width:6px; height:6px; background:var(--red); border-radius:50%; margin-right:5px; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.4)} }

.log-info    { color: #6b7a94; }
.log-warning { color: #f7b529; }
.log-error   { color: #ff4d6a; }
.log-signal  { color: #00d4aa; font-weight: 600; }

hr { border-color: var(--border) !important; margin: 10px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

C = {
    "bg":     "#080b0f",
    "bg2":    "#0d1117",
    "grid":   "rgba(255,255,255,0.035)",
    "text":   "#6b7a94",
    "gold":   "#f7b529",
    "dxy":    "#4da6ff",
    "green":  "#00d4aa",
    "red":    "#ff4d6a",
    "purple": "#a78bfa",
    "text3": "#aaaaaa",
}

# ─────────────────────────────────────────────────────────────────────────────
#  API LAYER
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1)
def fetch_snapshot() -> Optional[Dict]:
    """Récupère le snapshot complet depuis l'API."""
    try:
        r = requests.get(f"{API_URL}/api/snapshot", headers=HEADERS, timeout=API_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=2)
def fetch_ohlcv(tf: str) -> List[Dict]:
    try:
        r = requests.get(f"{API_URL}/api/ohlcv/{tf}", headers=HEADERS, timeout=API_TIMEOUT)
        if r.status_code == 200:
            return r.json().get("candles", [])
    except Exception:
        pass
    return []


def api_connected() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def simulate_snapshot() -> Dict:
    """Snapshot simulé si l'API est hors ligne."""
    np.random.seed(int(time.time()) % 9999)
    gold = 2320.0 + np.random.normal(0, 2)
    dxy  = 104.5  + np.random.normal(0, 0.05)
    corr = -0.72  + np.random.normal(0, 0.03)
    return {
        "gold_price": round(gold, 2),
        "dxy_price":  round(dxy, 3),
        "gold_bid":   round(gold - 0.15, 2),
        "gold_ask":   round(gold + 0.15, 2),
        "gold_change": round(np.random.normal(0, 1), 2),
        "gold_pct":    round(np.random.normal(0, 0.05), 3),
        "dxy_change":  round(np.random.normal(0, 0.03), 4),
        "dxy_pct":     round(np.random.normal(0, 0.03), 3),
        "correlation": round(corr, 4),
        "corr_history": [{"time": (datetime.now() - timedelta(seconds=i)).isoformat(),
                          "corr": round(-0.72 + np.random.normal(0, 0.05), 4)}
                         for i in range(100, 0, -1)],
        "signal": {
            "direction": np.random.choice(["BUY", "SELL", "WAIT"], p=[0.3, 0.3, 0.4]),
            "anticipation": "ANTICIPATION BUY GOLD",
            "confidence": np.random.randint(60, 90),
            "corr": round(corr, 4),
            "gold_price": round(gold, 2),
            "dxy_price":  round(dxy, 3),
            "entry": round(gold, 2),
            "tp":    round(gold + 150, 2),
            "sl":    round(gold - 80, 2),
            "rr":    1.87,
            "sl_source": "Swing Low",
            "pipeline_state": "WAIT_M15",
        },
        "signals": [],
        "bot_logs": [
            {"time": datetime.now().strftime("%H:%M:%S"), "level": "WARNING", "msg": "API hors ligne — simulation active"},
            {"time": datetime.now().strftime("%H:%M:%S"), "level": "INFO",    "msg": "Lance api_server.py sur ton PC"},
        ],
        "mtf_analysis": {
            "H1":  {"signal": "BUY",  "corr": -0.78, "trend": "↑ Hausse", "anticipation": None},
            "M15": {"signal": "WAIT", "corr": -0.61, "trend": "→ Stable", "anticipation": "ANTICIPATION BUY GOLD"},
            "M5":  {"signal": "BUY",  "corr": -0.71, "trend": "↑ Hausse", "anticipation": None},
        },
        "winrate": 64.5, "wins": 23, "losses": 12,
        "bot_status": "simulation", "mt5_connected": False,
        "gold_symbol": "XAUUSD (sim)", "dxy_symbol": "DXY (sim)",
        "last_update": datetime.now().isoformat(),
        "server_time": datetime.now().isoformat(),
    }


def simulate_ohlcv(n: int, interval_min: int, seed_sym: str) -> List[Dict]:
    np.random.seed(hash(seed_sym) % 9999)
    base = 2320.0 if "XAU" in seed_sym.upper() else 104.5
    vol  = 0.0007 if "XAU" in seed_sym.upper() else 0.0004
    now  = datetime.now()
    closes = [base]
    for _ in range(n - 1):
        closes.append(closes[-1] * (1 + np.random.normal(0, vol)))
    # Live jitter
    seed = int(time.time() * 2) % 10000
    np.random.seed(seed)
    closes[-1] *= (1 + np.random.normal(0, vol * 0.4))
    result = []
    for i in range(n):
        t = now - timedelta(minutes=interval_min * (n - 1 - i))
        o = closes[i - 1] if i > 0 else closes[i]
        c = closes[i]
        rng = abs(c - o) * (1 + abs(np.random.normal(0, 0.5)))
        h = max(o, c) + rng * 0.4
        l = min(o, c) - rng * 0.4
        result.append({"time": t.isoformat(), "open": round(o,5), "high": round(h,5),
                       "low": round(max(l,0.1),5), "close": round(c,5),
                       "volume": int(np.random.exponential(2000))})
    return result

# ─────────────────────────────────────────────────────────────────────────────
#  CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def candles_to_df(candles: List[Dict]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df


def add_zones_to_fig(fig, df: pd.DataFrame, row=1):
    """Ajoute Support/Résistance, FVG et Order Blocks sur le graphique."""
    if df.empty or len(df) < 10:
        return

    # ── Support / Résistance ──
    recent = df.tail(30)
    support    = float(recent["low"].min())
    resistance = float(recent["high"].max())

    fig.add_hline(y=support,    line=dict(color="rgba(0,212,170,0.4)", width=1, dash="dot"),
                  annotation_text="S", annotation_font=dict(color="#00d4aa", size=8), row=row, col=1)
    fig.add_hline(y=resistance, line=dict(color="rgba(255,77,106,0.4)", width=1, dash="dot"),
                  annotation_text="R", annotation_font=dict(color="#ff4d6a", size=8), row=row, col=1)

    # ── FVG (Fair Value Gap) ──
    highs  = df["high"].values
    lows   = df["low"].values
    for i in range(2, min(len(df), 50)):
        gap = lows[i] - highs[i - 2]
        if gap > 0.5:   # FVG bullish
            fig.add_hrect(
                y0=highs[i-2], y1=lows[i],
                fillcolor="rgba(0,212,170,0.07)",
                line=dict(color="rgba(0,212,170,0.2)", width=0.5),
                row=row, col=1,
            )
        gap_bear = lows[i - 2] - highs[i]
        if gap_bear > 0.5:  # FVG bearish
            fig.add_hrect(
                y0=highs[i], y1=lows[i-2],
                fillcolor="rgba(255,77,106,0.07)",
                line=dict(color="rgba(255,77,106,0.2)", width=0.5),
                row=row, col=1,
            )

    # ── Order Block (simplifié) ──
    closes = df["close"].values
    opens  = df["open"].values
    n = len(df)
    for i in range(1, min(n - 1, 30)):
        move = abs(closes[i+1] - closes[i])
        atr  = float(np.mean(np.abs(np.diff(closes[-20:]))))
        if opens[i] > closes[i] and closes[i+1] > opens[i+1] and move > atr * 0.6:
            fig.add_hrect(
                y0=float(df["low"].iloc[i]), y1=float(df["high"].iloc[i]),
                fillcolor="rgba(0,212,170,0.1)",
                line=dict(color="rgba(0,212,170,0.3)", width=0.5),
                row=row, col=1,
            )
        elif closes[i] > opens[i] and closes[i+1] < opens[i+1] and move > atr * 0.6:
            fig.add_hrect(
                y0=float(df["low"].iloc[i]), y1=float(df["high"].iloc[i]),
                fillcolor="rgba(255,77,106,0.1)",
                line=dict(color="rgba(255,77,106,0.3)", width=0.5),
                row=row, col=1,
            )


def make_chart(candles: List[Dict], symbol: str, color: str, tf: str,
               signal: Dict = None, show_zones: bool = True) -> go.Figure:
    df = candles_to_df(candles)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
                          height=420, font=dict(color=C["text"]))
        fig.add_annotation(text="En attente des données…", xref="paper", yref="paper",
                            x=0.5, y=0.5, font=dict(color=C["text"], size=14), showarrow=False)
        return fig

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.018, row_heights=[0.78, 0.22],
    )

    # ── Candlesticks ──
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=symbol,
        increasing=dict(line=dict(color=C["green"], width=1.1), fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],   width=1.1), fillcolor=C["red"]),
        whiskerwidth=0.2,
    ), row=1, col=1)

    # ── EMAs ──
    ema20 = df["close"].ewm(span=20).mean()
    ema50 = df["close"].ewm(span=50).mean()
    fig.add_trace(go.Scatter(x=df["time"], y=ema20, name="EMA20",
        line=dict(color=color, width=1.1, dash="dot"), opacity=0.7), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=ema50, name="EMA50",
        line=dict(color="rgba(255,255,255,0.2)", width=0.9), opacity=0.5), row=1, col=1)

    # ── Zones ──
    if show_zones:
        add_zones_to_fig(fig, df, row=1)

    # ── Prix courant + annotation ──
    last_p = float(df["close"].iloc[-1])
    fig.add_hline(y=last_p, row=1, col=1,
                  line=dict(color=color, width=0.7, dash="dash"), opacity=0.45)
    fig.add_annotation(
        x=df["time"].iloc[-1], y=last_p,
        text=f"  {last_p:,.2f}",
        font=dict(color=color, size=10.5, family="JetBrains Mono"),
        showarrow=False, xanchor="left",
        bgcolor="rgba(8,11,15,0.85)", bordercolor=color, borderwidth=1, borderpad=3,
        row=1, col=1,
    )

    # ── Signal markers ──
    if signal and signal.get("direction") in ("BUY", "SELL"):
        last_time = df["time"].iloc[-1]
        last_close = float(df["close"].iloc[-1])
        if signal["direction"] == "BUY":
            fig.add_trace(go.Scatter(
                x=[last_time], y=[last_close * 0.9992],
                mode="markers+text",
                marker=dict(symbol="triangle-up", size=14, color=C["green"]),
                text=["▲ BUY"], textposition="bottom center",
                textfont=dict(color=C["green"], size=9),
                name="Signal", showlegend=False,
            ), row=1, col=1)
            # TP/SL lines
            if signal.get("tp"):
                fig.add_hline(y=signal["tp"], row=1, col=1,
                              line=dict(color=C["green"], width=0.8, dash="dash"), opacity=0.5)
                fig.add_annotation(x=last_time, y=signal["tp"], text=f" TP {signal['tp']}",
                                   font=dict(color=C["green"], size=8), showarrow=False,
                                   xanchor="left", row=1, col=1)
            if signal.get("sl"):
                fig.add_hline(y=signal["sl"], row=1, col=1,
                              line=dict(color=C["red"], width=0.8, dash="dash"), opacity=0.5)
                fig.add_annotation(x=last_time, y=signal["sl"], text=f" SL {signal['sl']}",
                                   font=dict(color=C["red"], size=8), showarrow=False,
                                   xanchor="left", row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=[last_time], y=[last_close * 1.0008],
                mode="markers+text",
                marker=dict(symbol="triangle-down", size=14, color=C["red"]),
                text=["▼ SELL"], textposition="top center",
                textfont=dict(color=C["red"], size=9),
                name="Signal", showlegend=False,
            ), row=1, col=1)

    # ── Volume ──
    vol_colors = [C["green"] if c >= o else C["red"]
                  for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df["time"], y=df["volume"],
        marker=dict(color=vol_colors, opacity=0.5),
        showlegend=False, name="Volume",
    ), row=2, col=1)

    TF_LABELS = {"M5": "5 Min", "M15": "15 Min", "H1": "1 Hour"}

    # ── Layout ──
    ax = dict(showgrid=True, gridcolor=C["grid"], gridwidth=1,
              zeroline=False, tickfont=dict(size=9, color=C["text"]), linecolor=C["grid"])
    tf3 = C.get("text3", "#2e3a4e")
    tf_label_str = TF_LABELS.get(tf, tf)
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        margin=dict(l=0, r=58, t=34, b=0), height=420,
        font=dict(family="JetBrains Mono", color=C["text"], size=9),
        legend=dict(orientation="h", x=0, y=1.05, bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
        hovermode="x unified", xaxis_rangeslider_visible=False,
        title=dict(
            text=f'<b style="color:{color}">{symbol}</b>'
                 f'  <span style="color:{tf3};font-size:9px">● {tf_label_str}</span>',
            x=0.01, font=dict(size=12, family="Syne"),
        ),
        dragmode="pan",
    )
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax, tickformat=".5g")
    return fig


def make_corr_gauge(corr: float) -> go.Figure:
    color = C["green"] if corr < -0.5 else (C["red"] if corr > 0.5 else C["gold"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=corr,
        number=dict(font=dict(size=30, color=color, family="JetBrains Mono"), suffix=""),
        gauge=dict(
            axis=dict(range=[-1,1], tickwidth=1, tickcolor=C["text"], tickfont=dict(size=8), nticks=9),
            bar=dict(color=color, thickness=0.2),
            bgcolor=C["bg"],
            bordercolor=C["grid"], borderwidth=1,
            steps=[
                dict(range=[-1, -0.6], color="rgba(0,212,170,0.1)"),
                dict(range=[-0.6, 0.6], color="rgba(247,181,41,0.05)"),
                dict(range=[0.6, 1],  color="rgba(255,77,106,0.1)"),
            ],
            threshold=dict(line=dict(color=color, width=2), value=corr),
        ),
        title=dict(text="CORR GOLD/DXY", font=dict(size=8, color=C["text"], family="JetBrains Mono")),
    ))
    fig.update_layout(
        paper_bgcolor=C["bg2"], height=160,
        margin=dict(l=10, r=10, t=28, b=5),
        font=dict(color=C["text"]),
    )
    return fig


def make_corr_history_chart(history: List[Dict]) -> go.Figure:
    if not history:
        return go.Figure()
    times = [h["time"] for h in history]
    corrs = [h["corr"] for h in history]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times, y=corrs, name="Corr",
        line=dict(color=C["gold"], width=1.3),
        fill="tozeroy", fillcolor="rgba(247,181,41,0.05)",
    ))
    for y, col in [(-0.6, C["green"]), (0, C["text"]), (0.6, C["red"])]:
        fig.add_hline(y=y, line=dict(color=col, width=0.7, dash="dash"), opacity=0.4)
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        height=170, margin=dict(l=0, r=10, t=10, b=0),
        font=dict(family="JetBrains Mono", color=C["text"], size=9),
        hovermode="x",
        yaxis=dict(range=[-1.05, 1.05], showgrid=True, gridcolor=C["grid"],
                   zeroline=False, tickfont=dict(size=8)),
        xaxis=dict(showgrid=False, tickfont=dict(size=8)),
        showlegend=False, dragmode="pan",
    )
    return fig


def _plotly(fig, key=""):
    cfg = {"scrollZoom": True, "displaylogo": False,
           "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
           "displayModeBar": True}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)


def _plotly_small(fig, key=""):
    cfg = {"displayModeBar": False, "displaylogo": False}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

for k, v in [("tick", 0), ("api_ok", False), ("last_data", None),
             ("tf", "M5"), ("show_zones", True)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding:10px 0 18px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.15rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ⚡ GOLD/DXY PRO
        </div>
        <div style="font-size:.6rem;color:#2e3a4e;letter-spacing:.1em;text-transform:uppercase;margin-top:2px;">
            Algo Trading Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf = st.radio("TF", ["M5", "M15", "H1"], horizontal=True, label_visibility="collapsed")
    st.session_state.tf = tf

    st.markdown('<div class="lbl" style="margin-top:14px;">Refresh</div>', unsafe_allow_html=True)
    refresh_s = st.select_slider("Refresh", options=[1, 2, 3, 5, 10],
                                  value=2, format_func=lambda x: f"{x}s",
                                  label_visibility="collapsed")

    st.markdown('<div class="lbl" style="margin-top:14px;">Affichage</div>', unsafe_allow_html=True)
    show_zones = st.checkbox("Zones (S/R · FVG · OB)", value=True)

    st.markdown("---")

    # ── Connexion status ───────────────────────────────────────────────────────
    st.markdown('<div class="lbl">Connexion API</div>', unsafe_allow_html=True)
    api_ok = st.session_state.api_ok
    dot = '<span class="live-dot"></span>' if api_ok else '<span class="offline-dot"></span>'
    status_color = "#00d4aa" if api_ok else "#ff4d6a"
    status_text  = "API Connectée" if api_ok else "API Hors Ligne"
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.055);
                border-radius:7px;padding:7px 10px;font-size:.7rem;color:{status_color};">
        {dot}{status_text}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:.6rem;color:#2e3a4e;margin-top:6px;line-height:1.8;">
        Endpoint : <span style="color:#4b5568;">{API_URL}</span><br>
        Tick : #{st.session_state.tick}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── API URL override ────────────────────────────────────────────────────────
    with st.expander("⚙️ Config API"):
        new_url = st.text_input("API URL", value=API_URL)
        new_key = st.text_input("API Key", value=API_KEY, type="password")
        if st.button("Appliquer"):
            st.rerun()

    st.markdown(f"""
    <div style="font-size:.55rem;color:#2e3a4e;text-align:center;margin-top:10px;line-height:2;">
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <span style="color:#1e293b;">Gold/DXY Pro v2.0</span>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  DATA FETCH
# ─────────────────────────────────────────────────────────────────────────────

snap = fetch_snapshot()
if snap:
    st.session_state.api_ok   = True
    st.session_state.last_data = snap
    data = snap
else:
    st.session_state.api_ok = False
    data = simulate_snapshot()

st.session_state.tick += 1

# OHLCV
tf_min = {"M5": 5, "M15": 15, "H1": 60}[tf]
gold_candles = fetch_ohlcv(tf) if st.session_state.api_ok else simulate_ohlcv(200, tf_min, "XAUUSD")
dxy_candles  = simulate_ohlcv(200, tf_min, "DXY")  # DXY toujours simulé sauf si proxy disponible

signal     = data.get("signal", {})
corr       = data.get("correlation", -0.75)
mtf        = data.get("mtf_analysis", {})
stats      = {"winrate": data.get("winrate", 0), "wins": data.get("wins", 0),
              "losses": data.get("losses", 0)}

gold_price  = data.get("gold_price", 0)
dxy_price   = data.get("dxy_price", 0)
gold_change = data.get("gold_change", 0)
gold_pct    = data.get("gold_pct", 0)
dxy_change  = data.get("dxy_change", 0)
dxy_pct     = data.get("dxy_pct", 0)

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────

hcol1, hcol2, hcol3 = st.columns([3, 1.5, 1])
with hcol1:
    mt5_tag = data.get("mt5_connected", False)
    dot_h   = '<span class="live-dot"></span>' if mt5_tag else '<span class="offline-dot"></span>'
    st.markdown(f"""
    <div style="padding:8px 0 12px;border-bottom:1px solid rgba(255,255,255,0.055);margin-bottom:12px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.4rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.2;">
            GOLD / DXY PRO
        </div>
        <div style="font-size:.63rem;color:#6b7a94;letter-spacing:.07em;margin-top:3px;">
            {dot_h}{'MT5 Live' if mt5_tag else 'Simulation'} &nbsp;·&nbsp; {tf} &nbsp;·&nbsp; {data.get('gold_symbol','XAUUSD')}
        </div>
    </div>
    """, unsafe_allow_html=True)

with hcol2:
    sig_dir = signal.get("direction", "WAIT")
    ant     = signal.get("anticipation")
    badge_c = {"BUY": "badge-buy", "SELL": "badge-sell", "WAIT": "badge-wait"}[sig_dir]
    st.markdown(f"""
    <div style="padding-top:10px;">
        <div class="lbl">Signal Actif</div>
        <div style="display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-top:4px;">
            <span class="{badge_c}">{sig_dir}</span>
            {"<span class='badge-ant'>" + ant + "</span>" if ant else ""}
        </div>
        <div style="font-size:.62rem;color:#6b7a94;margin-top:5px;">
            Conf: <b style="color:#dde3ee;">{signal.get('confidence',0)}%</b> &nbsp;
            Pipeline: <b style="color:#dde3ee;">{signal.get('pipeline_state','IDLE')}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

with hcol3:
    st.markdown(f"""
    <div style="text-align:right;padding-top:10px;">
        <div style="font-size:1.05rem;font-weight:700;color:#dde3ee;">
            {datetime.now().strftime('%H:%M:%S')}
        </div>
        <div style="font-size:.58rem;color:#2e3a4e;">{datetime.now().strftime('%a %d %b %Y')}</div>
        <div style="font-size:.58rem;color:#2e3a4e;margin-top:2px;">Tick #{st.session_state.tick}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  METRICS ROW
# ─────────────────────────────────────────────────────────────────────────────

mc = st.columns(7)
with mc[0]: st.metric("XAUUSD",      f"{gold_price:,.2f}",  f"{gold_change:+.2f} ({gold_pct:+.2f}%)")
with mc[1]: st.metric("DXY",         f"{dxy_price:.3f}",    f"{dxy_change:+.4f} ({dxy_pct:+.2f}%)")
with mc[2]:
    corr_lbl = "● Forte Neg" if corr < -0.6 else ("● Modérée" if corr < 0 else "● Positive")
    st.metric("Corrélation", f"{corr:+.4f}", corr_lbl)
with mc[3]:
    emo = {"BUY": "🟢", "SELL": "🔴", "WAIT": "⚪"}
    st.metric("Signal", f"{emo[sig_dir]} {sig_dir}", f"Conf: {signal.get('confidence',0)}%")
with mc[4]: st.metric("Winrate",     f"{stats['winrate']}%", f"{stats['wins']}W / {stats['losses']}L")
with mc[5]:
    bid = data.get("gold_bid", gold_price)
    ask = data.get("gold_ask", gold_price)
    st.metric("BID / ASK", f"{bid:.2f}", f"ASK {ask:.2f} · Spread {ask-bid:.2f}")
with mc[6]:
    rr = signal.get("rr", 0)
    sl_src = signal.get("sl_source", "—")
    st.metric("R/R Ratio", f"1 : {rr}", f"SL src: {sl_src}")

st.markdown("")

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN TABS
# ─────────────────────────────────────────────────────────────────────────────

tab_charts, tab_signal, tab_mtf, tab_logs, tab_history = st.tabs([
    "📊  Graphiques", "🎯  Signal & Zones", "🔀  Multi-TF", "📋  Logs Bot", "📜  Historique"
])

# ══════════════════════════════════════════════════════════════
#  TAB 1 — GRAPHIQUES
# ══════════════════════════════════════════════════════════════
with tab_charts:
    gc1, gc2 = st.columns(2)

    with gc1:
        fig_gold = make_chart(gold_candles, "XAUUSD", C["gold"], tf,
                              signal=signal, show_zones=show_zones)
        _plotly(fig_gold, key="chart_gold")

    with gc2:
        fig_dxy = make_chart(dxy_candles, "DXY", C["dxy"], tf, show_zones=show_zones)
        _plotly(fig_dxy, key="chart_dxy")

    # ── Corrélation rolling ──
    st.markdown('<div class="lbl" style="margin-top:6px;">Corrélation Rolling GOLD/DXY</div>',
                unsafe_allow_html=True)
    fig_corr_hist = make_corr_history_chart(data.get("corr_history", []))
    _plotly_small(fig_corr_hist, key="corr_history")

# ══════════════════════════════════════════════════════════════
#  TAB 2 — SIGNAL & ZONES
# ══════════════════════════════════════════════════════════════
with tab_signal:
    sc1, sc2, sc3 = st.columns([1, 1, 1.3])

    with sc1:
        st.markdown('<div class="lbl">Corrélation</div>', unsafe_allow_html=True)
        _plotly_small(make_corr_gauge(corr), key="gauge")

        # Interprétation
        if corr < -0.65:
            interp_c = C["green"]
            interp_t = "✅ Corrélation inverse forte — signaux fiables"
        elif corr < -0.4:
            interp_c = C["gold"]
            interp_t = "⚠️ Corrélation modérée — attendre confirmation"
        else:
            interp_c = C["red"]
            interp_t = "❌ Corrélation faible — éviter les trades"
        st.markdown(f"""<div style="font-size:.68rem;color:{interp_c};
                        background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);
                        border-radius:7px;padding:8px 10px;margin-top:4px;">{interp_t}</div>""",
                    unsafe_allow_html=True)

    with sc2:
        st.markdown('<div class="lbl">Signal Courant</div>', unsafe_allow_html=True)
        direction = signal.get("direction", "WAIT")
        antici    = signal.get("anticipation")
        badge_cls = {"BUY": "badge-buy", "SELL": "badge-sell", "WAIT": "badge-wait"}[direction]

        st.markdown(f"""
        <div class="card">
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
                <span class="{badge_cls}" style="font-size:.8rem;padding:4px 14px;">{direction}</span>
                {"<span class='badge-ant'>" + antici + "</span>" if antici else ""}
            </div>
            <div style="font-size:.68rem;color:#6b7a94;line-height:2.1;">
                Confiance:  <b style="color:#dde3ee;">{signal.get('confidence',0)}%</b><br>
                Corr:       <b style="color:#dde3ee;">{signal.get('corr',0):+.4f}</b><br>
                Gold:       <b style="color:#f7b529;">{signal.get('gold_price',0):,.2f}</b><br>
                DXY:        <b style="color:#4da6ff;">{signal.get('dxy_price',0):.3f}</b><br>
                Pipeline:   <b style="color:#dde3ee;">{signal.get('pipeline_state','IDLE')}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if direction in ("BUY", "SELL"):
            entry = signal.get("entry", 0)
            tp    = signal.get("tp", 0)
            sl    = signal.get("sl", 0)
            rr    = signal.get("rr", 0)
            st.markdown(f"""
            <div class="card" style="border-color:rgba(247,181,41,0.2);">
                <div class="lbl" style="margin-bottom:8px;">Niveaux de Trading</div>
                <div style="font-size:.72rem;line-height:2.2;">
                    <span style="color:#6b7a94;">Entrée :</span>
                    <b style="color:#dde3ee;float:right;">{entry:,.2f}</b><br>
                    <span style="color:#00d4aa;">TP :</span>
                    <b style="color:#00d4aa;float:right;">{tp:,.2f}</b><br>
                    <span style="color:#ff4d6a;">SL :</span>
                    <b style="color:#ff4d6a;float:right;">{sl:,.2f}</b><br>
                    <span style="color:#6b7a94;">R/R :</span>
                    <b style="color:#f7b529;float:right;">1 : {rr}</b><br>
                    <span style="color:#6b7a94;">SL Source :</span>
                    <b style="color:#a78bfa;float:right;">{signal.get('sl_source','—')}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Mode Anticipation ──────────────────────────────────────────────────
        if antici:
            st.markdown(f"""
            <div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.3);
                        border-radius:8px;padding:10px 12px;margin-top:6px;">
                <div style="font-size:.6rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:4px;">
                    MODE ANTICIPATION
                </div>
                <div style="font-size:.72rem;color:#c4b5fd;">{antici}</div>
                <div style="font-size:.63rem;color:#6b7a94;margin-top:4px;">
                    {"DXY baisse → anticiper BUY GOLD" if "BUY" in antici else "DXY monte → anticiper SELL GOLD"}
                    <br>⏳ Attendre confirmation corrélation
                </div>
            </div>
            """, unsafe_allow_html=True)

    with sc3:
        st.markdown('<div class="lbl">Zones Techniques (M5)</div>', unsafe_allow_html=True)
        if gold_candles:
            df_z = candles_to_df(gold_candles)
            if not df_z.empty:
                r = df_z.tail(30)
                sup = float(r["low"].min())
                res = float(r["high"].max())
                last = float(df_z["close"].iloc[-1])

                st.markdown(f"""
                <div class="card">
                    <div class="lbl" style="margin-bottom:8px;">Support / Résistance</div>
                    <div style="font-size:.72rem;line-height:2.3;">
                        <span style="color:#6b7a94;">Support :</span>
                        <b style="color:#00d4aa;float:right;">{sup:,.2f}</b><br>
                        <span style="color:#6b7a94;">Résistance :</span>
                        <b style="color:#ff4d6a;float:right;">{res:,.2f}</b><br>
                        <span style="color:#6b7a94;">Prix actuel :</span>
                        <b style="color:#f7b529;float:right;">{last:,.2f}</b><br>
                        <span style="color:#6b7a94;">Dist. Support :</span>
                        <b style="color:#dde3ee;float:right;">{last-sup:+.2f}</b><br>
                        <span style="color:#6b7a94;">Dist. Résistance :</span>
                        <b style="color:#dde3ee;float:right;">{last-res:+.2f}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # FVG count
                highs = df_z["high"].values
                lows  = df_z["low"].values
                fvg_bull = sum(1 for i in range(2, len(df_z)) if lows[i] - highs[i-2] > 0.5)
                fvg_bear = sum(1 for i in range(2, len(df_z)) if lows[i-2] - highs[i] > 0.5)

                st.markdown(f"""
                <div class="card">
                    <div class="lbl" style="margin-bottom:8px;">FVG & Order Blocks</div>
                    <div style="font-size:.72rem;line-height:2.2;">
                        <span style="color:#6b7a94;">FVG Bullish :</span>
                        <b style="color:#00d4aa;float:right;">{fvg_bull} zones</b><br>
                        <span style="color:#6b7a94;">FVG Bearish :</span>
                        <b style="color:#ff4d6a;float:right;">{fvg_bear} zones</b><br>
                        <span style="color:#6b7a94;">OB activés :</span>
                        <b style="color:#a78bfa;float:right;">visible sur chart</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 3 — MULTI-TIMEFRAME
# ══════════════════════════════════════════════════════════════
with tab_mtf:
    st.markdown('<div class="lbl" style="margin-bottom:10px;">Analyse Multi-Timeframe</div>',
                unsafe_allow_html=True)

    mtf_cols = st.columns(3)
    for col, tf_name in zip(mtf_cols, ["H1", "M15", "M5"]):
        tf_data    = mtf.get(tf_name, {})
        tf_sig     = tf_data.get("signal", "WAIT")
        tf_corr    = tf_data.get("corr", 0.0)
        tf_trend   = tf_data.get("trend", "→ Stable")
        tf_ant     = tf_data.get("anticipation")
        badge_c    = {"BUY": "badge-buy", "SELL": "badge-sell", "WAIT": "badge-wait"}.get(tf_sig, "badge-wait")
        corr_color = C["green"] if tf_corr < -0.6 else (C["gold"] if tf_corr < 0 else C["red"])

        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.05rem;
                            color:#dde3ee;margin-bottom:8px;">{tf_name}</div>
                <div style="margin-bottom:8px;"><span class="{badge_c}">{tf_sig}</span></div>
                <div style="font-size:.68rem;color:#6b7a94;line-height:2.0;text-align:left;">
                    Corr: <b style="color:{corr_color};float:right;">{tf_corr:+.4f}</b><br>
                    Tendance: <b style="color:#dde3ee;float:right;">{tf_trend}</b>
                    {f'<br><span style="color:#a78bfa;">{tf_ant}</span>' if tf_ant else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Résumé MTF ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    mtf_sigs = [mtf.get(t, {}).get("signal", "WAIT") for t in ["H1", "M15", "M5"]]
    buy_cnt  = mtf_sigs.count("BUY")
    sell_cnt = mtf_sigs.count("SELL")

    if buy_cnt >= 2:
        consensus = "🟢 CONSENSUS BUY — Setup favorable"
        cons_c    = C["green"]
    elif sell_cnt >= 2:
        consensus = "🔴 CONSENSUS SELL — Setup favorable"
        cons_c    = C["red"]
    else:
        consensus = "⚪ PAS DE CONSENSUS — Attendre alignement"
        cons_c    = C["gold"]

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
                border-radius:10px;padding:14px 18px;text-align:center;">
        <div style="font-size:.72rem;color:{cons_c};font-weight:700;letter-spacing:.05em;">{consensus}</div>
        <div style="font-size:.6rem;color:#2e3a4e;margin-top:4px;">
            H1 {mtf_sigs[0]} · M15 {mtf_sigs[1]} · M5 {mtf_sigs[2]}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 4 — LOGS BOT
# ══════════════════════════════════════════════════════════════
with tab_logs:
    logs = data.get("bot_logs", [])

    lc1, lc2 = st.columns([3, 1])
    with lc1:
        st.markdown('<div class="lbl">Logs Temps Réel</div>', unsafe_allow_html=True)
    with lc2:
        log_filter = st.selectbox("Filtre", ["ALL", "SIGNAL", "WARNING", "ERROR"],
                                  label_visibility="collapsed")

    # ── Affichage logs ──────────────────────────────────────────────────────────
    log_html = '<div style="background:#0d1117;border:1px solid rgba(255,255,255,0.055);border-radius:8px;padding:12px;height:320px;overflow-y:auto;font-size:.66rem;line-height:1.9;">'
    filtered = [l for l in reversed(logs) if log_filter == "ALL" or l.get("level") == log_filter]
    for entry in filtered[:80]:
        lvl = entry.get("level", "INFO").upper()
        cls = {"INFO": "log-info", "WARNING": "log-warning", "ERROR": "log-error",
               "SIGNAL": "log-signal"}.get(lvl, "log-info")
        log_html += (
            f'<div><span style="color:#2e3a4e;">{entry.get("time","")}</span> '
            f'<span class="{cls}">[{lvl}]</span> '
            f'<span style="color:#9ca3af;">{entry.get("msg","")}</span></div>'
        )
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

    # ── Status bot ─────────────────────────────────────────────────────────────
    bot_status = data.get("bot_status", "unknown")
    status_map = {
        "running":    ("🟢", C["green"], "Bot actif"),
        "simulation": ("🟡", C["gold"],  "Mode simulation"),
        "starting":   ("🔵", C["blue"],  "Démarrage…"),
    }
    emoji, sc, slabel = status_map.get(bot_status, ("⚪", C["text"], "Inconnu"))
    st.markdown(f"""
    <div style="margin-top:8px;font-size:.68rem;color:{sc};">
        {emoji} Bot Status : <b>{slabel}</b> &nbsp;·&nbsp;
        MT5: <b>{'✅ Connecté' if data.get('mt5_connected') else '⚠️ Non connecté'}</b> &nbsp;·&nbsp;
        Dernière maj: <b>{data.get('last_update','—')[:19]}</b>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 5 — HISTORIQUE SIGNAUX
# ══════════════════════════════════════════════════════════════
with tab_history:
    signals_hist = data.get("signals", [])

    hc1, hc2, hc3, hc4 = st.columns(4)
    with hc1: st.metric("Total Signaux", len(signals_hist))
    with hc2: st.metric("Winrate",  f"{stats['winrate']}%")
    with hc3: st.metric("Victoires", stats["wins"])
    with hc4: st.metric("Défaites",  stats["losses"])

    st.markdown("")

    if signals_hist:
        df_sig = pd.DataFrame(signals_hist[::-1][-50:])

        def style_row(val):
            if val == "BUY":   return "color: #00d4aa; font-weight:700"
            if val == "SELL":  return "color: #ff4d6a; font-weight:700"
            if val == "WIN":   return "color: #00d4aa"
            if val == "LOSS":  return "color: #ff4d6a"
            return "color: #6b7a94"

        cols_show = [c for c in ["time", "direction", "tf", "entry", "tp", "sl", "rr", "sl_source", "result"]
                     if c in df_sig.columns]
        df_view = df_sig[cols_show]
        try:
            styled = df_view.style.map(style_row, subset=[c for c in ["direction", "result"] if c in df_view.columns])
            try:
                st.dataframe(styled, width="stretch", height=300)
            except TypeError:
                st.dataframe(styled, use_container_width=True, height=300)
        except Exception:
            try:
                st.dataframe(df_view, width="stretch", height=300)
            except TypeError:
                st.dataframe(df_view, use_container_width=True, height=300)
    else:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#2e3a4e;font-size:.75rem;">
            Aucun signal enregistré pour l'instant.<br>
            Lance le bot MT5 et l'API server pour voir les signaux apparaître ici.
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER + AUTO REFRESH
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="text-align:center;padding:10px 0 4px;font-size:.55rem;color:#1e293b;border-top:1px solid rgba(255,255,255,0.04);margin-top:10px;">
    Gold/DXY Pro · Tick #{st.session_state.tick} · API: {'✅' if st.session_state.api_ok else '❌'} · {API_URL} · Refresh: {refresh_s}s
</div>
""", unsafe_allow_html=True)

time.sleep(refresh_s)
st.rerun()
