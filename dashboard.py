"""
GOLD/DXY PRO — Dashboard v11
HTTP-only (no WebSocket) · Order Block module (LuxAlgo-inspired)
"""

import os, time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Optional, Dict

try:
    import requests as _req
    HAS_REQ = True
except ImportError:
    HAS_REQ = False

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GOLD/DXY Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CONFIG API ───────────────────────────────────────────────────────────────
try:
    API_URL = st.secrets["API_URL"]
    API_KEY = st.secrets["API_KEY"]
except Exception:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "gold_dxy_secret_2024")

HTTP_HEADERS = {"X-API-Key": API_KEY}
REFRESH_S    = 2

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');
:root {
    --bg:#080b0f; --bg2:#0d1117;
    --glass:rgba(255,255,255,0.03); --border:rgba(255,255,255,0.07);
    --gold:#f7b529; --green:#00d4aa; --red:#ff4d6a;
    --blue:#4da6ff; --purple:#a78bfa;
    --text:#dde3ee; --muted:#6b7a94; --dim:#2e3a4e;
}
html,body,[class*="css"]{ font-family:'JetBrains Mono',monospace!important; background:var(--bg)!important; color:var(--text)!important; }
.main .block-container{ padding:0.4rem 0.9rem 0.8rem!important; max-width:100%!important; }
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"],[data-testid="stDecoration"]{ display:none!important; }
[data-testid="stSidebar"]{ background:linear-gradient(180deg,#0c1018,#080b0f)!important; border-right:1px solid var(--border)!important; }
[data-testid="stSidebarCollapseButton"]{ display:none!important; }
[data-testid="metric-container"]{ background:var(--glass)!important; border:1px solid var(--border)!important; border-radius:7px!important; padding:6px 10px!important; }
[data-testid="stMetricLabel"]{ color:var(--muted)!important; font-size:.53rem!important; letter-spacing:.07em!important; text-transform:uppercase!important; }
[data-testid="stMetricValue"]{ font-size:.9rem!important; font-weight:700!important; line-height:1.2!important; }
[data-testid="stMetricDelta"]{ font-size:.57rem!important; }
.stRadio>div{ gap:4px!important; }
.stRadio label{ background:var(--glass)!important; border:1px solid var(--border)!important; border-radius:5px!important; padding:3px 9px!important; font-size:.68rem!important; color:var(--muted)!important; cursor:pointer!important; transition:all .15s!important; }
.stRadio label:hover{ border-color:rgba(247,181,41,.4)!important; color:var(--gold)!important; }
.stTabs [data-baseweb="tab-list"]{ background:var(--glass)!important; border:1px solid var(--border)!important; border-radius:7px!important; padding:3px!important; gap:3px!important; }
.stTabs [data-baseweb="tab"]{ background:transparent!important; border-radius:5px!important; color:var(--muted)!important; font-size:.68rem!important; padding:4px 12px!important; }
.stTabs [aria-selected="true"]{ background:rgba(247,181,41,.14)!important; color:var(--gold)!important; }
[data-testid="stTabScrollRight"],[data-testid="stTabScrollLeft"]{ display:none!important; }
.js-plotly-plot{ border-radius:7px!important; overflow:hidden!important; }
[data-testid="stPlotlyChart"]>div{ background:var(--bg2)!important; }
.stCheckbox label{ font-size:.68rem!important; color:var(--muted)!important; }
.card{ background:var(--glass); border:1px solid var(--border); border-radius:7px; padding:9px 11px; margin-bottom:6px; }
.card-gld{ border-color:rgba(247,181,41,.3)!important; }
.bb{ display:inline-block; background:rgba(0,212,170,.15); border:1px solid rgba(0,212,170,.4); color:#00d4aa; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.bs{ display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.bw{ display:inline-block; background:rgba(107,122,148,.1); border:1px solid rgba(107,122,148,.25); color:#6b7a94; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.ba{ display:inline-block; background:rgba(167,139,250,.12); border:1px solid rgba(167,139,250,.4); color:#a78bfa; border-radius:4px; padding:2px 8px; font-size:.62rem; font-weight:700; }
.bwin{ display:inline-block; background:rgba(0,212,170,.15); border:1px solid rgba(0,212,170,.4); color:#00d4aa; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.bloss{ display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.bopen{ display:inline-block; background:rgba(77,166,255,.15); border:1px solid rgba(77,166,255,.4); color:#4da6ff; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.dg{ display:inline-block;width:6px;height:6px;background:#00d4aa;border-radius:50%;box-shadow:0 0 5px #00d4aa;animation:pulse 1.4s infinite;margin-right:4px; }
.dr{ display:inline-block;width:6px;height:6px;background:#ff4d6a;border-radius:50%;margin-right:4px; }
.dp{ display:inline-block;width:6px;height:6px;background:#a78bfa;border-radius:50%;box-shadow:0 0 5px #a78bfa;animation:pulse 1.2s infinite;margin-right:4px; }
.dy{ display:inline-block;width:6px;height:6px;background:#f7b529;border-radius:50%;margin-right:4px; }
@keyframes pulse{ 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(1.6)} }
.lbl{ font-size:.52rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--dim); margin-bottom:3px; }
hr{ border-color:var(--border)!important; margin:7px 0!important; }
::-webkit-scrollbar{ width:3px; height:3px; }
::-webkit-scrollbar-thumb{ background:var(--border); border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ─── COULEURS PLOTLY ──────────────────────────────────────────────────────────
C = {"bg":"#080b0f","bg2":"#0d1117","grid":"rgba(255,255,255,0.03)",
     "text":"#6b7a94","dim":"#2e3a4e","gold":"#f7b529","dxy":"#4da6ff",
     "green":"#00d4aa","red":"#ff4d6a"}

# ─── SESSION STATE ────────────────────────────────────────────────────────────
_INIT: Dict = {
    "tick":0,
    "tf":"M5","show_zones":True,
    "gold_price":0.0,"dxy_price":0.0,"gold_bid":0.0,"gold_ask":0.0,
    "gold_change":0.0,"gold_pct":0.0,"dxy_change":0.0,
    "correlation":-0.75,"corr_history":[],
    "signal":{"direction":"WAIT","anticipation":None,"confidence":0,"corr":-0.75,
               "gold_price":0.0,"dxy_price":0.0,"entry":0.0,"tp":0.0,"sl":0.0,
               "rr":0.0,"sl_source":"—","pipeline_state":"IDLE"},
    "signals":[],"bot_logs":[{"time":"--:--","level":"INFO","msg":"Démarrage..."}],
    "mtf":{"H1":{"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None},
            "M15":{"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None},
            "M5":{"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None}},
    "ohlcv":{"M5":[],"M15":[],"H1":[]},
    "zones":{"support":0.0,"resistance":0.0,"fvg_bullish":[],"fvg_bearish":[],
              "ob_buy":None,"ob_sell":None,"atr":0.0,"fvg_filter":0.0},
    "winrate":0.0,"wins":0,"losses":0,
    "backtest_stats":{},"backtest_trades":[],"backtest_equity":[],"backtest_patterns":{},
    "bot_status":"unknown","mt5_connected":False,"gold_symbol":"XAUUSD","last_update":"—",
}
for k,v in _INIT.items():
    if k not in st.session_state: st.session_state[k]=v
ss = st.session_state
if not isinstance(ss.signal, dict): ss.signal = _INIT["signal"]
if not isinstance(ss.zones,  dict): ss.zones  = _INIT["zones"]
if ss.tf not in ["M5","M15","H1"]:  ss.tf     = "M5"

# ═══════════════════════════════════════════════════════════════════════
#  ORDER BLOCK ENGINE — LuxAlgo-inspired
# ═══════════════════════════════════════════════════════════════════════

def detect_order_blocks(df: pd.DataFrame, swing_len: int = 5, mitigation: str = "Wick") -> Dict:
    """
    Détecte les Order Blocks (bullish & bearish) inspiré de LuxAlgo.
    
    Logique :
    - Pivot volume : on cherche les bougies avec volume dominant sur N barres
    - Structure :
        Bearish OB = dernière bougie haussière avant un fort mouvement baissier
        Bullish OB = dernière bougie baissière avant un fort mouvement haussier
    - Mitigation :
        Wick  = le prix effleure la zone (high/low croise)
        Close = une bougie ferme à l'intérieur de la zone
    
    Returns dict with keys: bullish_obs, bearish_obs (list of dicts)
    """
    if df.empty or len(df) < swing_len * 2 + 1:
        return {"bullish_obs": [], "bearish_obs": []}

    highs  = df["high"].values
    lows   = df["low"].values
    opens  = df["open"].values
    closes = df["close"].values
    vols   = df["volume"].values if "volume" in df.columns else np.ones(len(df))
    times  = df["time"].values
    n      = len(df)

    bullish_obs: List[Dict] = []
    bearish_obs: List[Dict] = []

    def _is_swing_high(i):
        if i < swing_len or i >= n - swing_len:
            return False
        return all(highs[i] >= highs[i-j] for j in range(1, swing_len+1)) and \
               all(highs[i] >= highs[i+j] for j in range(1, swing_len+1))

    def _is_swing_low(i):
        if i < swing_len or i >= n - swing_len:
            return False
        return all(lows[i] <= lows[i-j] for j in range(1, swing_len+1)) and \
               all(lows[i] <= lows[i+j] for j in range(1, swing_len+1))

    # Détecte les swing points
    swing_highs = [i for i in range(swing_len, n-swing_len) if _is_swing_high(i)]
    swing_lows  = [i for i in range(swing_len, n-swing_len) if _is_swing_low(i)]

    # --- Bearish OB ---
    # Pour chaque swing high, on cherche en arrière la dernière bougie bullish
    # avec le plus fort volume avant le sommet
    for sh in swing_highs:
        # Cherche la bougie bullish (close > open) avec max volume dans la fenêtre précédant le swing
        window_start = max(0, sh - swing_len * 2)
        window = range(window_start, sh)
        bullish_candles = [(i, vols[i]) for i in window if closes[i] > opens[i]]
        if not bullish_candles:
            continue
        # Prend la bougie bullish avec le volume le plus élevé
        ob_idx = max(bullish_candles, key=lambda x: x[1])[0]
        ob = {
            "type":   "bearish",
            "top":    highs[ob_idx],
            "bottom": lows[ob_idx],
            "avg":    (highs[ob_idx] + lows[ob_idx]) / 2,
            "open":   opens[ob_idx],
            "close":  closes[ob_idx],
            "time":   times[ob_idx],
            "time_end": times[min(sh + swing_len, n-1)],
            "volume": vols[ob_idx],
            "mitigated": False,
        }
        bearish_obs.append(ob)

    # --- Bullish OB ---
    # Pour chaque swing low, on cherche la dernière bougie bearish avec max volume
    for sl in swing_lows:
        window_start = max(0, sl - swing_len * 2)
        window = range(window_start, sl)
        bearish_candles = [(i, vols[i]) for i in window if closes[i] < opens[i]]
        if not bearish_candles:
            continue
        ob_idx = max(bearish_candles, key=lambda x: x[1])[0]
        ob = {
            "type":   "bullish",
            "top":    highs[ob_idx],
            "bottom": lows[ob_idx],
            "avg":    (highs[ob_idx] + lows[ob_idx]) / 2,
            "open":   opens[ob_idx],
            "close":  closes[ob_idx],
            "time":   times[ob_idx],
            "time_end": times[min(sl + swing_len, n-1)],
            "volume": vols[ob_idx],
            "mitigated": False,
        }
        bullish_obs.append(ob)

    # --- Mitigation ---
    # Marque les OB mitigés (le prix est revenu dans la zone après formation)
    def _check_mitigation(obs, is_bullish):
        for ob in obs:
            # Cherche les bougies après la formation de l'OB
            ob_time = ob["time"]
            mask = times > ob_time
            if not np.any(mask):
                continue
            future_highs  = highs[mask]
            future_lows   = lows[mask]
            future_closes = closes[mask]
            if is_bullish:
                if mitigation == "Wick":
                    ob["mitigated"] = bool(np.any(future_lows <= ob["avg"]))
                else:  # Close
                    ob["mitigated"] = bool(np.any(future_closes <= ob["bottom"]))
            else:
                if mitigation == "Wick":
                    ob["mitigated"] = bool(np.any(future_highs >= ob["avg"]))
                else:
                    ob["mitigated"] = bool(np.any(future_closes >= ob["top"]))

    _check_mitigation(bullish_obs, is_bullish=True)
    _check_mitigation(bearish_obs, is_bullish=False)

    # Filtre les OB non mitigés, garde les N plus récents
    max_ob = 3
    bullish_obs = sorted([o for o in bullish_obs if not o["mitigated"]],
                          key=lambda x: x["time"], reverse=True)[:max_ob]
    bearish_obs = sorted([o for o in bearish_obs if not o["mitigated"]],
                          key=lambda x: x["time"], reverse=True)[:max_ob]

    return {"bullish_obs": bullish_obs, "bearish_obs": bearish_obs}


def draw_order_blocks(fig, obs_data: Dict, row: int = 1, col: int = 1):
    """Dessine les Order Blocks sur le graphique Plotly."""
    bullish_obs = obs_data.get("bullish_obs", [])
    bearish_obs = obs_data.get("bearish_obs", [])

    # Bullish OB — rectangles verts
    for ob in bullish_obs:
        fig.add_shape(
            type="rect",
            x0=ob["time"], x1=ob["time_end"],
            y0=ob["bottom"], y1=ob["top"],
            row=row, col=col,
            line=dict(color="rgba(0,212,170,0.6)", width=1),
            fillcolor="rgba(0,212,170,0.08)",
        )
        # Ligne médiane (average)
        fig.add_shape(
            type="line",
            x0=ob["time"], x1=ob["time_end"],
            y0=ob["avg"], y1=ob["avg"],
            row=row, col=col,
            line=dict(color="rgba(0,212,170,0.5)", width=1, dash="dot"),
        )
        # Label
        fig.add_annotation(
            x=ob["time_end"], y=ob["top"],
            text="OB↑", showarrow=False,
            font=dict(color="#00d4aa", size=8),
            xanchor="left", yanchor="bottom",
            row=row, col=col,
        )

    # Bearish OB — rectangles rouges
    for ob in bearish_obs:
        fig.add_shape(
            type="rect",
            x0=ob["time"], x1=ob["time_end"],
            y0=ob["bottom"], y1=ob["top"],
            row=row, col=col,
            line=dict(color="rgba(255,77,106,0.6)", width=1),
            fillcolor="rgba(255,77,106,0.08)",
        )
        # Ligne médiane
        fig.add_shape(
            type="line",
            x0=ob["time"], x1=ob["time_end"],
            y0=ob["avg"], y1=ob["avg"],
            row=row, col=col,
            line=dict(color="rgba(255,77,106,0.5)", width=1, dash="dot"),
        )
        # Label
        fig.add_annotation(
            x=ob["time_end"], y=ob["bottom"],
            text="OB↓", showarrow=False,
            font=dict(color="#ff4d6a", size=8),
            xanchor="left", yanchor="top",
            row=row, col=col,
        )

    return fig

# ═══════════════════════════════════════════════════════════════════════
#  HTTP DATA LAYER — remplace le WebSocket
# ═══════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=REFRESH_S)
def _http_snap():
    """Récupère le snapshot complet depuis l'API FastAPI."""
    if not HAS_REQ:
        return None
    try:
        r = _req.get(
            f"{API_URL}/api/snapshot",
            headers=HTTP_HEADERS,
            timeout=5,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def _apply(d: Dict):
    """Applique les données du snapshot à la session state."""
    if not isinstance(d, dict):
        return
    for k in ["gold_price","dxy_price","gold_bid","gold_ask","gold_change","gold_pct",
               "dxy_change","correlation","corr_history","signal","signals","bot_logs",
               "winrate","wins","losses","bot_status","mt5_connected","gold_symbol",
               "last_update","zones","backtest_stats","backtest_trades","backtest_equity","backtest_patterns"]:
        if k in d:
            ss[k] = d[k]
    if "mtf_analysis" in d: ss.mtf = d["mtf_analysis"]
    if "mtf"          in d: ss.mtf = d["mtf"]
    if "ohlcv" in d:
        for tf, c in d["ohlcv"].items():
            if c:
                ss.ohlcv[tf] = c


# ─── SIMULATION FALLBACK ──────────────────────────────────────────────────────
def _simulate():
    np.random.seed(int(time.time()) % 9999)
    if ss.gold_price == 0:
        ss.gold_price = 4613.0
        ss.dxy_price  = 104.5
    ss.gold_price   = round(ss.gold_price + np.random.normal(0, .12), 2)
    ss.dxy_price    = round(ss.dxy_price  + np.random.normal(0, .006), 3)
    ss.gold_change  = round(np.random.normal(0, .7),    2)
    ss.gold_pct     = round(np.random.normal(0, .035),  3)
    ss.dxy_change   = round(np.random.normal(0, .015),  4)
    ss.correlation  = max(-1, min(1, ss.correlation + np.random.normal(0, .008)))
    ss.gold_bid     = round(ss.gold_price - .15, 2)
    ss.gold_ask     = round(ss.gold_price + .15, 2)
    ss.bot_status   = "simulation"


def _sim_ohlcv(n, mins, sym):
    np.random.seed(hash(sym) % 9999)
    base = ss.gold_price if ("XAU" in sym.upper() and ss.gold_price > 0) else (4613.0 if "XAU" in sym.upper() else 104.5)
    vol  = 0.0006 if "XAU" in sym.upper() else 0.0003
    cl   = [base]
    for _ in range(n - 1):
        cl.append(cl[-1] * (1 + np.random.normal(0, vol)))
    np.random.seed(int(time.time() * 2) % 10000)
    cl[-1] *= (1 + np.random.normal(0, vol * .3))
    out, now = [], datetime.now()
    for i in range(n):
        t = now - timedelta(minutes=mins * (n - 1 - i))
        o = cl[i-1] if i > 0 else cl[i]
        c = cl[i]
        r = abs(c - o) * (1 + abs(np.random.normal(0, .4)))
        h = max(o, c) + r * .35
        l = min(o, c) - r * .35
        out.append({
            "time":   t.isoformat(),
            "open":   round(o, 5),
            "high":   round(h, 5),
            "low":    round(max(l, .1), 5),
            "close":  round(c, 5),
            "volume": int(np.random.exponential(2000)),
        })
    return out


# ─── CORRÉLATION ROLLING ─────────────────────────────────────────────────────
def _rolling_corr(gold_c, dxy_c, window=50):
    n = min(len(gold_c), len(dxy_c))
    if n < window + 5:
        return []
    g = [c["close"] for c in gold_c[-n:]]
    d = [c["close"] for c in dxy_c[-n:]]
    t = [c["time"]  for c in gold_c[-n:]]
    out = []
    for i in range(window, n):
        ga = np.array(g[i-window:i])
        da = np.array(d[i-window:i])
        corr = float(np.corrcoef(ga, da)[0, 1]) if np.std(ga) > 1e-10 and np.std(da) > 1e-10 else 0.0
        out.append({"time": t[i], "corr": round(corr, 4)})
    return out


# ─── BUILDERS GRAPHES ─────────────────────────────────────────────────────────
def _to_df(candles):
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df


def _draw_zones(fig, z, row=1):
    s = z.get("support", 0)
    r = z.get("resistance", 0)
    if s:
        fig.add_hline(y=s, row=row, col=1,
                      line=dict(color="rgba(0,212,170,.45)", width=1, dash="dot"),
                      annotation_text="S", annotation_font=dict(color="#00d4aa", size=8))
    if r:
        fig.add_hline(y=r, row=row, col=1,
                      line=dict(color="rgba(255,77,106,.45)", width=1, dash="dot"),
                      annotation_text="R", annotation_font=dict(color="#ff4d6a", size=8))
    for fvg in z.get("fvg_bullish", []):
        fig.add_hrect(y0=fvg["low"], y1=fvg["high"], row=row, col=1,
                      fillcolor="rgba(0,212,170,.08)",
                      line=dict(color="rgba(0,212,170,.2)", width=.5))
    for fvg in z.get("fvg_bearish", []):
        fig.add_hrect(y0=fvg["low"], y1=fvg["high"], row=row, col=1,
                      fillcolor="rgba(255,77,106,.08)",
                      line=dict(color="rgba(255,77,106,.2)", width=.5))
    # OB depuis les zones API (fallback)
    ob_b = z.get("ob_buy")
    ob_s = z.get("ob_sell")
    if ob_b:
        fig.add_hline(y=ob_b, row=row, col=1,
                      line=dict(color="rgba(0,212,170,.65)", width=1.2),
                      annotation_text="OB↑", annotation_font=dict(color="#00d4aa", size=8))
    if ob_s:
        fig.add_hline(y=ob_s, row=row, col=1,
                      line=dict(color="rgba(255,77,106,.65)", width=1.2),
                      annotation_text="OB↓", annotation_font=dict(color="#ff4d6a", size=8))


def build_candle(candles, symbol, color, tf, signal=None, zones=None,
                 show_zones=True, obs_data=None):
    df = _to_df(candles)
    tf_lbl = {"M5":"5 Min","M15":"15 Min","H1":"1 Hour"}.get(tf, tf)

    if df.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
                          height=360, margin=dict(l=0, r=8, t=26, b=0))
        fig.add_annotation(text="⏳ En attente…", xref="paper", yref="paper",
                            x=.5, y=.5, font=dict(color=C["text"], size=12), showarrow=False)
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=.01, row_heights=[.8, .2])

    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=symbol,
        increasing=dict(line=dict(color=C["green"], width=1), fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],   width=1), fillcolor=C["red"]),
        whiskerwidth=.18), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["time"], y=df["close"].ewm(span=20).mean(),
        name="EMA20", line=dict(color=color, width=1, dash="dot"), opacity=.65),
        row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["time"], y=df["close"].ewm(span=50).mean(),
        name="EMA50", line=dict(color="rgba(255,255,255,.16)", width=.8), opacity=.5),
        row=1, col=1)

    if show_zones and zones:
        _draw_zones(fig, zones, row=1)

    lp = float(df["close"].iloc[-1])
    fig.add_hline(y=lp, row=1, col=1,
                  line=dict(color=color, width=.8, dash="dash"), opacity=.5)

    if signal and signal.get("direction") in ("BUY","SELL"):
        lt = df["time"].iloc[-1]
        up = signal["direction"] == "BUY"
        fig.add_trace(go.Scatter(
            x=[lt], y=[lp * (.9993 if up else 1.0007)],
            mode="markers+text",
            marker=dict(symbol="triangle-up" if up else "triangle-down",
                        size=12, color=C["green"] if up else C["red"]),
            text=["▲" if up else "▼"],
            textposition="bottom center" if up else "top center",
            textfont=dict(color=C["green"] if up else C["red"], size=9),
            showlegend=False), row=1, col=1)
        if signal.get("tp"):
            fig.add_hline(y=signal["tp"], row=1, col=1,
                          line=dict(color=C["green"], width=.7, dash="dash"), opacity=.5)
        if signal.get("sl"):
            fig.add_hline(y=signal["sl"], row=1, col=1,
                          line=dict(color=C["red"], width=.7, dash="dash"), opacity=.5)

    # Volume
    vc = [C["green"] if c >= o else C["red"]
          for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df["time"], y=df["volume"],
        marker=dict(color=vc, opacity=.4), showlegend=False),
        row=2, col=1)

    # ─── ORDER BLOCKS ────────────────────────────────────────────────
    if show_zones and obs_data:
        fig = draw_order_blocks(fig, obs_data, row=1, col=1)

    ax = dict(showgrid=True, gridcolor=C["grid"], gridwidth=1, zeroline=False,
              tickfont=dict(size=8, color=C["text"]), linecolor=C["grid"])

    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        margin=dict(l=0, r=8, t=28, b=0), height=360,
        font=dict(family="JetBrains Mono", color=C["text"], size=8),
        legend=dict(orientation="h", x=0, y=1.1, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=8)),
        hovermode="x unified", xaxis_rangeslider_visible=False,
        title=dict(
            text=(f'<b style="color:{color}">{symbol}</b>'
                  f'<span style="color:{C["dim"]};font-size:8px"> ● {tf_lbl}</span>'
                  f'  <span style="color:{color};font-weight:700"> {lp:,.2f}</span>'),
            x=.01, font=dict(size=11, family="Syne")),
        dragmode="pan")
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax, tickformat=".5g")
    return fig


def build_gauge(corr):
    col = C["green"] if corr < -.5 else (C["red"] if corr > .5 else C["gold"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=corr,
        number=dict(font=dict(size=24, color=col, family="JetBrains Mono")),
        gauge=dict(
            axis=dict(range=[-1, 1], tickfont=dict(size=7), nticks=9, tickcolor=C["text"]),
            bar=dict(color=col, thickness=.18),
            bgcolor=C["bg"], bordercolor=C["grid"], borderwidth=1,
            steps=[dict(range=[-1, -.6], color="rgba(0,212,170,.08)"),
                   dict(range=[-.6, .6],  color="rgba(247,181,41,.04)"),
                   dict(range=[.6, 1],    color="rgba(255,77,106,.08)")]),
        title=dict(text="CORR", font=dict(size=7, color=C["text"]))))
    fig.update_layout(paper_bgcolor=C["bg2"], height=140, margin=dict(l=8, r=8, t=20, b=4))
    return fig


def build_corr_chart(corr_data):
    fig = go.Figure()
    if corr_data:
        times = [d["time"] for d in corr_data]
        corrs = [d["corr"] for d in corr_data]
        fig.add_trace(go.Scatter(
            x=times, y=corrs,
            line=dict(color=C["gold"], width=1.5),
            fill="tozeroy", fillcolor="rgba(247,181,41,.06)",
            hovertemplate="%{x|%H:%M}<br><b>%{y:.4f}</b><extra></extra>"))
        fig.add_hrect(y0=-1.05, y1=-.6, fillcolor="rgba(0,212,170,.05)", line=dict(width=0))
        fig.add_hrect(y0=.6, y1=1.05, fillcolor="rgba(255,77,106,.05)", line=dict(width=0))
        for y, c, lbl in [(-.6, C["green"], "-0.6 Signal"), (0, C["text"], "0"), (.6, C["red"], "0.6")]:
            fig.add_hline(y=y, line=dict(color=c, width=.8, dash="dot"), opacity=.55,
                          annotation_text=lbl, annotation_position="left",
                          annotation_font=dict(color=c, size=8))
    else:
        fig.add_annotation(text="En attente OHLCV…", xref="paper", yref="paper",
                            x=.5, y=.5, font=dict(color=C["text"], size=11), showarrow=False)
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"], height=175,
        margin=dict(l=0, r=60, t=24, b=0),
        font=dict(family="JetBrains Mono", color=C["text"], size=8),
        title=dict(text='<span style="color:#6b7a94;font-size:8px">CORRÉLATION ROLLING GOLD/DXY  (fenêtre 50 bougies)</span>', x=.01),
        hovermode="x unified", showlegend=False, dragmode="pan",
        yaxis=dict(range=[-1.05, 1.05], showgrid=True, gridcolor=C["grid"],
                   zeroline=False, tickfont=dict(size=8),
                   tickvals=[-1, -.6, -.2, 0, .2, .6, 1]),
        xaxis=dict(showgrid=False, tickfont=dict(size=8)))
    return fig


def _plt(fig, key, small=False):
    cfg = {"displaylogo": False, "scrollZoom": not small,
           "displayModeBar": not small,
           "modeBarButtonsToRemove": ["lasso2d","select2d","autoScale2d"]}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except Exception:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)


# ═══════════════════════════════════════════════════════════════════════
#  FETCH DONNÉES — HTTP only
# ═══════════════════════════════════════════════════════════════════════

snap = _http_snap()
if snap:
    _apply(snap)
    api_ok = True
else:
    _simulate()
    api_ok = False

ss.tick += 1
tf      = ss.tf
tf_min  = {"M5": 5, "M15": 15, "H1": 60}[tf]
gold_c  = ss.ohlcv.get(tf, []) or _sim_ohlcv(200, tf_min, "XAUUSD")
dxy_c   = ss.ohlcv.get(tf, []) or _sim_ohlcv(200, tf_min, "DXY")
# DXY toujours simulé si non fourni par l'API
if not ss.ohlcv.get(tf):
    dxy_c = _sim_ohlcv(200, tf_min, "DXY")
else:
    dxy_c = _sim_ohlcv(200, tf_min, "DXY")  # DXY simulé car rarement dans snapshot

signal   = ss.signal if isinstance(ss.signal, dict) else _INIT["signal"]
zones    = ss.zones  if isinstance(ss.zones,  dict) else _INIT["zones"]
mtf      = ss.mtf
mt5_ok   = ss.mt5_connected
sig_dir  = signal.get("direction", "WAIT")
ant      = signal.get("anticipation") or ""
BC       = {"BUY":"bb","SELL":"bs","WAIT":"bw"}
corr_data = _rolling_corr(gold_c, dxy_c, window=50)

# Calcul des Order Blocks depuis les données OHLCV
gold_df  = _to_df(gold_c)
gold_obs = detect_order_blocks(gold_df, swing_len=5, mitigation="Wick") if not gold_df.empty else {"bullish_obs":[],"bearish_obs":[]}

# ═══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    transform: none !important;
    margin-left: 0 !important;
    left: 0 !important;
    width: 21rem !important;
    min-width: 21rem !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    display: flex !important;
    transform: translateX(0) !important;
    margin-left: 0 !important;
}
button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stBaseButton-headerNoPadding"],
button[kind="headerNoPadding"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
.st-emotion-cache-zq5wmm,
.st-emotion-cache-1rtdyuf,
.st-emotion-cache-hzo1qh,
.st-emotion-cache-wnm74r,
.st-emotion-cache-ryys7r {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
}
.main { margin-left: 21rem !important; }
</style>
<script>
(function forceSidebar() {
    function fix() {
        var sb = document.querySelector('[data-testid="stSidebar"]');
        if (!sb) return;
        sb.style.display = 'flex';
        sb.style.transform = 'none';
        sb.style.marginLeft = '0';
        sb.style.visibility = 'visible';
        sb.style.opacity = '1';
        sb.setAttribute('aria-expanded', 'true');
        var btns = document.querySelectorAll('[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], button[aria-label="Close sidebar"], button[aria-label="Open sidebar"]');
        btns.forEach(function(b){ b.style.display='none'; });
    }
    fix();
    setInterval(fix, 500);
    var obs = new MutationObserver(fix);
    obs.observe(document.body, {childList:true, subtree:true, attributes:true});
})();
</script>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 12px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ⚡ GOLD/DXY PRO
        </div>
        <div style="font-size:.5rem;color:#2e3a4e;letter-spacing:.1em;text-transform:uppercase;margin-top:1px;">
            Algo Trading Dashboard
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf_sel = st.radio("TF", ["M5","M15","H1"], horizontal=True,
                       label_visibility="collapsed",
                       index=["M5","M15","H1"].index(ss.tf))
    if tf_sel != ss.tf:
        ss.tf = tf_sel

    st.markdown("<hr>", unsafe_allow_html=True)

    gc = "#00d4aa" if ss.gold_change >= 0 else "#ff4d6a"
    dc = "#00d4aa" if ss.dxy_change  >= 0 else "#ff4d6a"
    st.markdown(
        f'<div class="card"><div class="lbl">XAUUSD</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:#f7b529;">{ss.gold_price:,.2f}</div>'
        f'<div style="font-size:.57rem;color:{gc};">{ss.gold_change:+.2f} ({ss.gold_pct:+.2f}%)</div></div>'
        f'<div class="card"><div class="lbl">DXY</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:#4da6ff;">{ss.dxy_price:.3f}</div>'
        f'<div style="font-size:.57rem;color:{dc};">{ss.dxy_change:+.4f}</div></div>',
        unsafe_allow_html=True)


    conf = signal.get("confidence", 0)
    pipe = signal.get("pipeline_state", "IDLE")
    ant_h = f'<div style="margin-top:3px;"><span class="ba" style="font-size:.55rem;">{ant}</span></div>' if ant else ""
    st.markdown(
        f'<div class="card card-gld">'
        f'<div class="lbl">Signal</div>'
        f'<div style="margin:4px 0;"><span class="{BC[sig_dir]}">{sig_dir}</span></div>'
        f'{ant_h}'
        f'<div style="font-size:.57rem;color:#6b7a94;line-height:1.9;margin-top:3px;">'
        f'Conf:&nbsp;<b style="color:#dde3ee;">{conf}%</b><br>'
        f'Corr:&nbsp;<b style="color:#dde3ee;">{signal.get("corr",0):+.3f}</b><br>'
        f'<span style="color:#3d4a5e;">{pipe}</span>'
        f'</div></div>',
        unsafe_allow_html=True)

    cc = "#00d4aa" if ss.correlation < -.6 else ("#f7b529" if ss.correlation < -.4 else "#ff4d6a")
    ct = "✅ Forte" if ss.correlation < -.6 else ("⚠️ Modérée" if ss.correlation < -.4 else "❌ Faible")
    st.markdown(
        f'<div class="card"><div class="lbl">Corrélation</div>'
        f'<div style="font-size:1rem;font-weight:700;color:{cc};">{ss.correlation:+.4f}</div>'
        f'<div style="font-size:.55rem;color:{cc};margin-top:1px;">{ct}</div></div>',
        unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="lbl">Affichage</div>', unsafe_allow_html=True)
    ss.show_zones = st.checkbox("Zones (S/R · FVG · OB)", value=ss.show_zones)

    # OB summary
    n_ob_b = len(gold_obs.get("bullish_obs", []))
    n_ob_s = len(gold_obs.get("bearish_obs", []))
    n_fvg  = len(zones.get("fvg_bullish",[])) + len(zones.get("fvg_bearish",[]))
    st.markdown(
        f'<div style="font-size:.52rem;color:#3d4a5e;line-height:1.8;margin-top:4px;">'
        f'{n_fvg} FVG · ATR={zones.get("atr",0):.2f}<br>OB↑ {n_ob_b} · OB↓ {n_ob_s} actifs</div>',
        unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    api_color = "#00d4aa" if api_ok else "#f7b529"
    api_label = "API Connectée" if api_ok else "Simulation"
    dapi = "dg" if api_ok else "dy"
    dmt5 = "dg" if mt5_ok else "dy"
    url_s = API_URL[:26] + ("…" if len(API_URL) > 26 else "")
    mt5_color = '#00d4aa' if mt5_ok else '#f7b529'
    mt5_label = 'Live' if mt5_ok else 'Simulation'
    st.markdown(
        f'<div style="font-size:.61rem;">'
        f'<div style="color:{api_color};margin-bottom:3px;"><span class="{dapi}"></span>HTTP {api_label}</div>'
        f'<div style="color:{mt5_color};"><span class="{dmt5}"></span>MT5 {mt5_label}</div>'
        f'<div style="font-size:.5rem;color:#2e3a4e;margin-top:3px;">{url_s}</div>'
        f'</div>',
        unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.metric("Winrate", f"{ss.winrate}%")
    with c2: st.metric("Trades",  f"{ss.wins}W/{ss.losses}L")
    st.markdown(
        f'<div style="font-size:.49rem;color:#2e3a4e;text-align:center;margin-top:7px;line-height:2;">'
        f'{ss.gold_symbol} · {tf} · #{ss.tick}<br>{datetime.now().strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  CONTENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════

api_col = "#00d4aa" if api_ok else "#f7b529"
dh      = "dg" if api_ok else "dy"
ant_hd  = f' <span class="ba">{ant}</span>' if ant else ""

st.markdown(f"""
<div style="display:flex;align-items:flex-start;justify-content:space-between;
            padding:4px 0 8px;border-bottom:1px solid rgba(255,255,255,.06);margin-bottom:8px;">
    <div>
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.4rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.1;">
            GOLD / DXY PRO
        </div>
        <div style="font-size:.6rem;color:#6b7a94;margin-top:2px;">
            <span class="{dh}"></span><span style="color:{api_col};">{'HTTP Live' if api_ok else 'Simulation'}</span>
            &nbsp;·&nbsp;{'MT5 Live' if mt5_ok else 'Simulation'}&nbsp;·&nbsp;{tf}&nbsp;·&nbsp;{ss.gold_symbol}
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;padding-top:4px;">
        <span class="{BC[sig_dir]}">{sig_dir}</span>{ant_hd}
        <span style="font-size:.58rem;color:#6b7a94;">Conf&nbsp;<b style="color:#dde3ee;">{signal.get('confidence',0)}%</b></span>
        <span style="font-size:.95rem;font-weight:700;color:#dde3ee;margin-left:6px;">{datetime.now().strftime('%H:%M:%S')}</span>
    </div>
</div>""", unsafe_allow_html=True)

# Métriques
m = st.columns(7)
with m[0]: st.metric("XAUUSD",     f"{ss.gold_price:,.2f}",   f"{ss.gold_change:+.2f} ({ss.gold_pct:+.2f}%)")
with m[1]: st.metric("DXY",        f"{ss.dxy_price:.3f}",     f"{ss.dxy_change:+.4f}")
with m[2]:
    cl = "●Neg" if ss.correlation < -.6 else ("●Mod" if ss.correlation < 0 else "●Pos")
    st.metric("Corrélation", f"{ss.correlation:+.4f}", cl)
with m[3]:
    emo = {"BUY":"🟢","SELL":"🔴","WAIT":"⚪"}
    st.metric("Signal", f"{emo[sig_dir]} {sig_dir}", f"Conf:{signal.get('confidence',0)}%")
with m[4]: st.metric("Winrate",    f"{ss.winrate}%",           f"{ss.wins}W/{ss.losses}L")
with m[5]: st.metric("BID/ASK",   f"{ss.gold_bid:.2f}",       f"ASK {ss.gold_ask:.2f}")
with m[6]: st.metric("R/R",       f"1:{signal.get('rr',0)}",  f"SL:{signal.get('sl_source','—')}")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Graphiques","🎯 Signal & Zones","🔀 Multi-TF","📋 Logs Bot","📜 Historique", "🤖 Backtest"])

with tab1:
    g1, g2 = st.columns(2)
    with g1:
        _plt(build_candle(gold_c, "XAUUSD", C["gold"], tf,
                          signal=signal, zones=zones,
                          show_zones=ss.show_zones, obs_data=gold_obs),
             key="gold_chart")
    with g2:
        _plt(build_candle(dxy_c, "DXY", C["dxy"], tf,
                          show_zones=False, obs_data=None),
             key="dxy_chart")
    _plt(build_corr_chart(corr_data), key="corr_chart")
    if corr_data:
        lc = corr_data[-1]["corr"]
        zc = "#00d4aa" if lc < -.6 else ("#f7b529" if lc < -.4 else "#ff4d6a")
        zt = "Zone signal active" if lc < -.6 else ("Modérée" if lc < -.4 else "Hors zone signal")
        st.markdown(f'<div style="font-size:.57rem;color:{zc};margin-top:1px;">Corr: <b>{lc:+.4f}</b> · {zt} · fenêtre 50 bougies</div>',
                    unsafe_allow_html=True)

with tab2:
    s1, s2, s3 = st.columns([1, 1, 1.2])
    with s1:
        _plt(build_gauge(ss.correlation), key="gauge_t2", small=True)
        if   ss.correlation < -.65: ic, it = C["green"], "✅ Forte — signaux fiables"
        elif ss.correlation < -.4:  ic, it = C["gold"],  "⚠️ Modérée — attendre"
        else:                       ic, it = C["red"],   "❌ Faible — éviter"
        st.markdown(
            f'<div style="font-size:.63rem;color:{ic};background:rgba(255,255,255,.02);'
            f'border:1px solid rgba(255,255,255,.05);border-radius:6px;padding:7px 9px;margin-top:4px;">{it}</div>',
            unsafe_allow_html=True)
    with s2:
        dir2 = signal.get("direction", "WAIT")
        ant2 = signal.get("anticipation") or ""
        ant2h = f'<span class="ba">{ant2}</span>' if ant2 else ""
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;gap:7px;align-items:center;margin-bottom:8px;">
                <span class="{BC[dir2]}" style="font-size:.7rem;padding:3px 10px;">{dir2}</span>{ant2h}
            </div>
            <div style="font-size:.64rem;color:#6b7a94;line-height:2.0;">
                Confiance:&nbsp;<b style="color:#dde3ee;">{signal.get('confidence',0)}%</b><br>
                Corr:&nbsp;<b style="color:#dde3ee;">{signal.get('corr',0):+.4f}</b><br>
                Gold:&nbsp;<b style="color:#f7b529;">{signal.get('gold_price',0):,.2f}</b><br>
                DXY:&nbsp;<b style="color:#4da6ff;">{signal.get('dxy_price',0):.3f}</b><br>
                Pipeline:&nbsp;<b style="color:#dde3ee;">{signal.get('pipeline_state','IDLE')}</b>
            </div>
        </div>""", unsafe_allow_html=True)
        if dir2 in ("BUY","SELL"):
            entry = signal.get("entry", 0)
            tp    = signal.get("tp",    0)
            sl    = signal.get("sl",    0)
            rr    = signal.get("rr",    0)
            st.markdown(f"""
            <div class="card card-gld">
                <div class="lbl" style="margin-bottom:6px;">Niveaux</div>
                <div style="font-size:.65rem;line-height:2.0;">
                    <span style="color:#6b7a94;">Entrée:</span><b style="color:#dde3ee;float:right;">{entry:,.2f}</b><br>
                    <span style="color:#00d4aa;">TP:</span><b style="color:#00d4aa;float:right;">{tp:,.2f}</b><br>
                    <span style="color:#ff4d6a;">SL:</span><b style="color:#ff4d6a;float:right;">{sl:,.2f}</b><br>
                    <span style="color:#6b7a94;">R/R:</span><b style="color:#f7b529;float:right;">1:{rr}</b>
                </div>
            </div>""", unsafe_allow_html=True)
        if ant2:
            st.markdown(f"""
            <div style="background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.3);border-radius:7px;padding:9px 10px;margin-top:5px;">
                <div style="font-size:.54rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:3px;">MODE ANTICIPATION</div>
                <div style="font-size:.66rem;color:#c4b5fd;">{ant2}</div>
                <div style="font-size:.58rem;color:#6b7a94;margin-top:2px;">{"DXY↓ → anticiper BUY" if "BUY" in ant2 else "DXY↑ → anticiper SELL"}<br>⏳ Attendre confirmation</div>
            </div>""", unsafe_allow_html=True)
    with s3:
        sup  = zones.get("support",    0)
        res  = zones.get("resistance", 0)
        atr  = zones.get("atr",        0)
        ff   = zones.get("fvg_filter", 0)
        ob_b = zones.get("ob_buy")
        ob_s = zones.get("ob_sell")
        st.markdown(f"""
        <div class="card">
            <div class="lbl" style="margin-bottom:6px;">Support / Résistance</div>
            <div style="font-size:.65rem;line-height:2.0;">
                <span style="color:#6b7a94;">Support:</span><b style="color:#00d4aa;float:right;">{sup:,.2f}</b><br>
                <span style="color:#6b7a94;">Résistance:</span><b style="color:#ff4d6a;float:right;">{res:,.2f}</b><br>
                <span style="color:#6b7a94;">ATR:</span><b style="color:#f7b529;float:right;">{atr:.3f}</b><br>
                <span style="color:#6b7a94;">FVG Filter:</span><b style="color:#a78bfa;float:right;">{ff:.3f}</b>
            </div>
        </div>
        <div class="card">
            <div class="lbl" style="margin-bottom:6px;">FVG & Order Blocks</div>
            <div style="font-size:.65rem;line-height:2.0;">
                <span style="color:#6b7a94;">FVG Bull:</span><b style="color:#00d4aa;float:right;">{len(zones.get('fvg_bullish',[]))} zones</b><br>
                <span style="color:#6b7a94;">FVG Bear:</span><b style="color:#ff4d6a;float:right;">{len(zones.get('fvg_bearish',[]))} zones</b><br>
                <span style="color:#6b7a94;">OB↑ actifs:</span><b style="color:#00d4aa;float:right;">{n_ob_b}</b><br>
                <span style="color:#6b7a94;">OB↓ actifs:</span><b style="color:#ff4d6a;float:right;">{n_ob_s}</b>
            </div>
        </div>""", unsafe_allow_html=True)

        # Détail des OB
        if gold_obs.get("bullish_obs"):
            rows_ob = ""
            for ob in gold_obs["bullish_obs"]:
                rows_ob += (f'<div style="font-size:.58rem;color:#00d4aa;line-height:1.7;">'
                            f'↑ {ob["bottom"]:,.2f} – {ob["top"]:,.2f}'
                            f' <span style="color:#3d4a5e;">avg:{ob["avg"]:,.2f}</span></div>')
            for ob in gold_obs.get("bearish_obs",[]):
                rows_ob += (f'<div style="font-size:.58rem;color:#ff4d6a;line-height:1.7;">'
                            f'↓ {ob["bottom"]:,.2f} – {ob["top"]:,.2f}'
                            f' <span style="color:#3d4a5e;">avg:{ob["avg"]:,.2f}</span></div>')
            st.markdown(f'<div class="card"><div class="lbl" style="margin-bottom:4px;">Détail OB XAUUSD</div>{rows_ob}</div>',
                        unsafe_allow_html=True)

with tab3:
    mc = st.columns(3)
    for col, tf_n in zip(mc, ["H1","M15","M5"]):
        d   = mtf.get(tf_n, {})
        sig = d.get("signal", "WAIT")
        cr  = d.get("corr",   0.)
        tr  = d.get("trend",  "—")
        at  = d.get("anticipation") or ""
        cc2 = C["green"] if cr < -.6 else (C["gold"] if cr < 0 else C["red"])
        ath = f'<br><span style="color:#a78bfa;font-size:.58rem;">{at}</span>' if at else ""
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;color:#dde3ee;margin-bottom:6px;">{tf_n}</div>
                <span class="{BC.get(sig,'bw')}">{sig}</span>
                <div style="font-size:.63rem;color:#6b7a94;line-height:2.0;margin-top:7px;text-align:left;">
                    Corr:&nbsp;<b style="color:{cc2};float:right;">{cr:+.4f}</b><br>
                    Trend:&nbsp;<b style="color:#dde3ee;float:right;">{tr}</b>{ath}
                </div>
            </div>""", unsafe_allow_html=True)
    sigs  = [mtf.get(t, {}).get("signal","WAIT") for t in ["H1","M15","M5"]]
    buys  = sigs.count("BUY")
    sells = sigs.count("SELL")
    if   buys  >= 2: cons, cc3 = "🟢 CONSENSUS BUY",  C["green"]
    elif sells >= 2: cons, cc3 = "🔴 CONSENSUS SELL", C["red"]
    else:            cons, cc3 = "⚪ PAS DE CONSENSUS", C["gold"]
    st.markdown(
        f'<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);'
        f'border-radius:8px;padding:12px;text-align:center;margin-top:8px;">'
        f'<div style="font-size:.68rem;color:{cc3};font-weight:700;">{cons}</div>'
        f'<div style="font-size:.57rem;color:#2e3a4e;margin-top:3px;">H1:{sigs[0]} · M15:{sigs[1]} · M5:{sigs[2]}</div></div>',
        unsafe_allow_html=True)

with tab4:
    lc1, lc2 = st.columns([3, 1])
    with lc1: st.markdown('<div class="lbl">Logs Temps Réel</div>', unsafe_allow_html=True)
    with lc2: lf = st.selectbox("Filtre", ["ALL","SIGNAL","WARNING","ERROR"], label_visibility="collapsed")
    filtered = [l for l in reversed(ss.bot_logs) if lf == "ALL" or l.get("level") == lf]
    rows = ""
    for e in filtered[:80]:
        lvl = e.get("level","INFO").upper()
        col = {"INFO":"#6b7a94","WARNING":"#f7b529","ERROR":"#ff4d6a","SIGNAL":"#00d4aa"}.get(lvl,"#6b7a94")
        rows += (f'<div><span style="color:#2e3a4e;">{e.get("time","")}</span> '
                 f'<span style="color:{col};font-weight:600;">[{lvl}]</span> '
                 f'<span style="color:#9ca3af;">{e.get("msg","")}</span></div>')
    st.markdown(
        f'<div style="background:#0d1117;border:1px solid rgba(255,255,255,.06);border-radius:7px;'
        f'padding:10px;height:285px;overflow-y:auto;font-size:.6rem;line-height:1.82;">{rows}</div>',
        unsafe_allow_html=True)
    bot_col = "#00d4aa" if ss.bot_status == "running" else "#f7b529"
    st.markdown(
        f'<div style="margin-top:5px;font-size:.6rem;color:{bot_col};">'
        f'Bot:{ss.bot_status} · MT5:{"✅" if mt5_ok else "⚠️"} · '
        f'HTTP:{"🟢" if api_ok else "🟡"} · {str(ss.last_update)[:19]}</div>',
        unsafe_allow_html=True)

with tab5:
    h1, h2, h3, h4 = st.columns(4)
    with h1: st.metric("Total",   len(ss.signals))
    with h2: st.metric("Winrate", f"{ss.winrate}%")
    with h3: st.metric("Wins",    ss.wins)
    with h4: st.metric("Losses",  ss.losses)
    if ss.signals:
        df_s = pd.DataFrame(ss.signals[::-1][-50:])
        cols = [c for c in ["time","direction","tf","entry","tp","sl","rr","sl_source","result"]
                if c in df_s.columns]
        def _sty(v):
            return {"BUY":"color:#00d4aa;font-weight:700","SELL":"color:#ff4d6a;font-weight:700",
                    "WIN":"color:#00d4aa","LOSS":"color:#ff4d6a"}.get(str(v),"color:#6b7a94")
        try:
            sub = [c for c in ["direction","result"] if c in cols]
            st2 = df_s[cols].style.map(_sty, subset=sub)
            try:    st.dataframe(st2, width="stretch",           height=275)
            except: st.dataframe(st2, use_container_width=True,  height=275)
        except:
            try:    st.dataframe(df_s[cols], width="stretch",          height=275)
            except: st.dataframe(df_s[cols], use_container_width=True, height=275)
    else:
        st.markdown(
            '<div style="text-align:center;padding:35px;color:#2e3a4e;font-size:.7rem;">'
            'Aucun signal enregistré.<br>Lance le bot + api_server.py</div>',
            unsafe_allow_html=True)

with tab6:
    st.markdown('<div class="lbl">RÉSULTATS DU BACKTEST</div>', unsafe_allow_html=True)
    if ss.backtest_stats:
        b_winrate = ss.backtest_stats.get("winrate", 0)
        b_pf = ss.backtest_stats.get("profit_factor", 0)
        b_dd = ss.backtest_stats.get("max_drawdown", 0)
        
        bm1, bm2, bm3, bm4 = st.columns(4)
        with bm1: st.metric("Winrate", f"{b_winrate}%")
        with bm2: st.metric("Profit Factor", f"{b_pf:.2f}")
        with bm3: st.metric("Drawdown Max", f"{b_dd:.2f}%")
        with bm4: st.metric("Total Trades", ss.backtest_stats.get("total_trades", 0))

        if ss.backtest_equity:
            try:
                eq_df = pd.DataFrame(ss.backtest_equity)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=eq_df["time"], y=eq_df["equity"], fill="tozeroy", line=dict(color=C["gold"])))
                fig.update_layout(paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"], height=200, margin=dict(l=0, r=0, t=10, b=0))
                _plt(fig, key="equity_chart")
            except Exception as e:
                st.error(f"Erreur d'affichage de la courbe: {e}")
        
        if ss.backtest_patterns:
            st.markdown('<div class="lbl" style="margin-top:10px;">Règles Apprises (learning.json)</div>', unsafe_allow_html=True)
            st.json(ss.backtest_patterns)
    else:
        st.markdown(
            '<div style="text-align:center;padding:35px;color:#2e3a4e;font-size:.7rem;">'
            'Aucune donnée de backtest disponible.<br>Exécutez `python backtest.py` pour générer le modèle.</div>',
            unsafe_allow_html=True)

st.markdown(
    f'<div style="text-align:center;padding:4px 0 2px;font-size:.48rem;color:#1a2234;'
    f'border-top:1px solid rgba(255,255,255,.04);margin-top:4px;">'
    f'Gold/DXY Pro v11 · {"🟢HTTP" if api_ok else "🟡SIM"} · Tick#{ss.tick} · {REFRESH_S}s</div>',
    unsafe_allow_html=True)

time.sleep(REFRESH_S)
st.rerun()
