"""
GOLD/DXY PRO — Dashboard v13
Refonte visuelle style TradeHub (dark pro)
Corrections :
  - Prix réels affichés correctement (bid/ask/change depuis API)
  - Onglet Backtest supprimé
  - Layout épuré style screenshot
  - Sidebar compacte avec vraies données
"""

import os, time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    import requests as _req
    HAS_REQ = True
except ImportError:
    HAS_REQ = False

st.set_page_config(
    page_title="GOLD/DXY Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL   = "https://en-ligne-5wi6.onrender.com"
API_KEY   = "gold_dxy_secret_2024"
HEADERS   = {"X-API-Key": API_KEY}
REFRESH_S = 3

# ── CSS STYLE TRADEHUB ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
  --bg:     #0a0e17;
  --bg2:    #0f1623;
  --bg3:    #141c2e;
  --card:   #111827;
  --border: rgba(255,255,255,0.07);
  --gold:   #f7b529;
  --green:  #00d4aa;
  --red:    #ff4d6a;
  --blue:   #4da6ff;
  --purple: #a78bfa;
  --text:   #e2e8f0;
  --muted:  #64748b;
  --dim:    #1e2d42;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}

.main .block-container {
  padding: 0.5rem 1rem 1rem !important;
  max-width: 100% !important;
}

#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

/* SIDEBAR */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0c1322 0%, #080d18 100%) !important;
  border-right: 1px solid var(--border) !important;
  width: 260px !important;
}
[data-testid="stSidebarCollapseButton"] { display: none !important; }

/* METRICS */
[data-testid="metric-container"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
}
[data-testid="stMetricLabel"] {
  color: var(--muted) !important;
  font-size: .55rem !important;
  letter-spacing: .1em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
  font-size: 1rem !important;
  font-weight: 700 !important;
  font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stMetricDelta"] { font-size: .6rem !important; }

/* TABS */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 4px !important;
  gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 8px !important;
  color: var(--muted) !important;
  font-size: .68rem !important;
  font-weight: 600 !important;
  padding: 6px 14px !important;
  letter-spacing: .04em !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(247,181,41,.15) !important;
  color: var(--gold) !important;
}

/* CARDS */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 8px;
}
.card-gold { border-color: rgba(247,181,41,.25) !important; }
.card-green { border-color: rgba(0,212,170,.2) !important; }
.card-red { border-color: rgba(255,77,106,.2) !important; }

/* BADGES */
.bb { display:inline-block;background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:#00d4aa;border-radius:6px;padding:3px 10px;font-size:.65rem;font-weight:700;letter-spacing:.05em; }
.bs { display:inline-block;background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:#ff4d6a;border-radius:6px;padding:3px 10px;font-size:.65rem;font-weight:700;letter-spacing:.05em; }
.bw { display:inline-block;background:rgba(100,116,139,.1);border:1px solid rgba(100,116,139,.25);color:#64748b;border-radius:6px;padding:3px 10px;font-size:.65rem;font-weight:700; }
.ba { display:inline-block;background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.4);color:#a78bfa;border-radius:6px;padding:3px 10px;font-size:.62rem;font-weight:700; }
.bwin  { display:inline-block;background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:#00d4aa;border-radius:6px;padding:2px 8px;font-size:.6rem;font-weight:700; }
.bloss { display:inline-block;background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:#ff4d6a;border-radius:6px;padding:2px 8px;font-size:.6rem;font-weight:700; }
.bopen { display:inline-block;background:rgba(247,181,41,.12);border:1px solid rgba(247,181,41,.3);color:#f7b529;border-radius:6px;padding:2px 8px;font-size:.6rem;font-weight:700; }

/* LIVE DOT */
.dot-green { display:inline-block;width:7px;height:7px;background:#00d4aa;border-radius:50%;box-shadow:0 0 6px #00d4aa;animation:pulse 1.4s infinite;margin-right:5px;vertical-align:middle; }
.dot-yellow { display:inline-block;width:7px;height:7px;background:#f7b529;border-radius:50%;margin-right:5px;vertical-align:middle; }
.dot-red { display:inline-block;width:7px;height:7px;background:#ff4d6a;border-radius:50%;margin-right:5px;vertical-align:middle; }

@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(1.8)} }

/* PRICE DISPLAY */
.price-main { font-family:'JetBrains Mono',monospace;font-size:1.8rem;font-weight:700;color:#f7b529;line-height:1.1; }
.price-change-up { font-size:.7rem;color:#00d4aa;font-weight:600; }
.price-change-dn { font-size:.7rem;color:#ff4d6a;font-weight:600; }

/* LABEL */
.lbl { font-size:.52rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:4px; }

/* TABLE */
[data-testid="stDataFrame"] { border-radius: 10px !important; }

hr { border-color: var(--border) !important; margin: 8px 0 !important; }
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# Palette graphiques
C = {
    "bg":     "#0a0e17",
    "bg2":    "#0f1623",
    "bg3":    "#141c2e",
    "grid":   "rgba(255,255,255,0.04)",
    "gold":   "#f7b529",
    "dxy":    "#4da6ff",
    "green":  "#00d4aa",
    "red":    "#ff4d6a",
    "text":   "#64748b",
    "muted":  "#64748b",
}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
_INIT = {
    "tick": 0, "tf": "M5", "show_zones": True,
    # Prix réels — init à 0, rempli par l'API
    "gold_price": 0.0, "dxy_price": 0.0,
    "gold_bid": 0.0, "gold_ask": 0.0,
    "gold_change": 0.0, "gold_pct": 0.0,
    "dxy_change": 0.0, "correlation": 0.0,
    "signal": {
        "direction": "WAIT", "anticipation": None, "confidence": 0,
        "corr": 0.0, "gold_price": 0.0, "dxy_price": 0.0,
        "entry": 0.0, "tp": 0.0, "sl": 0.0, "rr": 0.0, "lot": 0.0,
        "sl_source": "—", "pipeline_state": "IDLE", "result": "",
    },
    "signals": [], "bot_logs": [{"time": "--:--", "level": "INFO", "msg": "Démarrage..."}],
    "mtf": {
        "H1":  {"signal": "WAIT", "corr": 0.0, "trend": "—"},
        "M15": {"signal": "WAIT", "corr": 0.0, "trend": "—"},
        "M5":  {"signal": "WAIT", "corr": 0.0, "trend": "—"},
    },
    "ohlcv": {"M5": [], "M15": [], "H1": []},
    "zones": {
        "support": 0.0, "resistance": 0.0,
        "fvg_bullish": [], "fvg_bearish": [],
        "ob_buy": None, "ob_sell": None,
        "atr": 0.0, "fvg_filter": 0.0,
    },
    "winrate": 0.0, "wins": 0, "losses": 0,
    "bot_status": "unknown", "mt5_connected": False,
    "gold_symbol": "XAUUSD", "last_update": "—",
    "api_ok": False,
}

for k, v in _INIT.items():
    if k not in st.session_state:
        st.session_state[k] = v

ss = st.session_state
if not isinstance(ss.signal, dict): ss.signal = _INIT["signal"]
if not isinstance(ss.zones,  dict): ss.zones  = _INIT["zones"]
if ss.tf not in ["M5", "M15", "H1"]: ss.tf = "M5"

# ── FETCH API ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_S)
def _http_snap():
    if not HAS_REQ:
        return None
    try:
        r = _req.get(f"{API_URL}/api/snapshot", headers=HEADERS, timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def _apply(d: dict):
    """Applique le snapshot API dans session_state."""
    if not isinstance(d, dict):
        return
    # Prix réels — clés directes
    for k in [
        "gold_price", "dxy_price", "gold_bid", "gold_ask",
        "gold_change", "gold_pct", "dxy_change", "correlation",
        "signals", "bot_logs", "winrate", "wins", "losses",
        "bot_status", "mt5_connected", "gold_symbol", "last_update", "zones",
    ]:
        if k in d:
            ss[k] = d[k]

    # Signal
    if "signal" in d and isinstance(d["signal"], dict):
        ss.signal = {**_INIT["signal"], **d["signal"]}
        # Sync prix gold depuis signal si gold_price manquant
        if ss.gold_price == 0 and ss.signal.get("gold_price", 0) > 0:
            ss.gold_price = ss.signal["gold_price"]

    # MTF
    if "mtf_analysis" in d: ss.mtf = d["mtf_analysis"]
    if "mtf"          in d: ss.mtf = d["mtf"]

    # OHLCV
    if "ohlcv" in d:
        for tf_k, candles in d["ohlcv"].items():
            if candles and len(candles) > 0:
                ss.ohlcv[tf_k] = candles
                # Extraire le prix réel depuis la dernière bougie OHLCV si non dispo
                if tf_k == "M5" and ss.gold_price == 0:
                    try:
                        ss.gold_price = float(candles[-1]["close"])
                    except Exception:
                        pass

# ── SIMULATION OHLCV (fallback) ───────────────────────────────────────────────
def _sim_ohlcv(n: int, mins: int, sym: str, base_price: float = None) -> list:
    """Génère des bougies simulées ancrées sur le vrai prix si disponible."""
    seed = hash(sym) % 9999
    rng  = np.random.default_rng(seed + int(time.time() // (mins * 60)))
    if base_price is None or base_price == 0:
        base = 3200.0 if "XAU" in sym.upper() else 104.5
    else:
        base = base_price

    vol = 0.0008 if "XAU" in sym.upper() else 0.0003
    closes = [base]
    for _ in range(n - 1):
        closes.append(closes[-1] * (1 + rng.normal(0, vol)))

    # Ancrage dernier prix au prix réel
    if base_price and base_price > 0:
        offset = base_price - closes[-1]
        closes = [c + offset for c in closes]

    out = []
    now = datetime.now()
    for i in range(n):
        t = now - timedelta(minutes=mins * (n - 1 - i))
        o = closes[i - 1] if i > 0 else closes[i]
        c = closes[i]
        spread = abs(rng.normal(0, abs(c) * vol * 0.5)) + abs(c) * vol * 0.2
        h = max(o, c) + spread * 0.4
        lo = min(o, c) - spread * 0.4
        out.append({
            "time":   t.isoformat(),
            "open":   round(o, 2),
            "high":   round(h, 2),
            "low":    round(max(lo, 0.1), 2),
            "close":  round(c, 2),
            "volume": int(rng.exponential(2000)),
        })
    return out

def _rolling_corr(gold_c: list, dxy_c: list, window: int = 50) -> list:
    n = min(len(gold_c), len(dxy_c))
    if n < window + 5:
        return []
    g = [c["close"] for c in gold_c[-n:]]
    d = [c["close"] for c in dxy_c[-n:]]
    t = [c["time"]  for c in gold_c[-n:]]
    out = []
    for i in range(window, n):
        ga = np.array(g[i - window:i])
        da = np.array(d[i - window:i])
        if np.std(ga) > 1e-10 and np.std(da) > 1e-10:
            corr = float(np.corrcoef(ga, da)[0, 1])
        else:
            corr = 0.0
        out.append({"time": t[i], "corr": round(corr, 4)})
    return out

# ── FETCH & INIT DATA ─────────────────────────────────────────────────────────
snap = _http_snap()
api_ok = False

if snap:
    _apply(snap)
    api_ok = True
    ss.api_ok = True
else:
    ss.api_ok = False

ss.tick += 1
tf     = ss.tf
tf_min = {"M5": 5, "M15": 15, "H1": 60}[tf]

# Prix Gold réel — priorité : gold_price > gold_bid > ohlcv
gold_price_real = float(ss.gold_price) if float(ss.gold_price) > 100 else 0.0

# OHLCV Gold
gold_c = ss.ohlcv.get(tf, [])
if not gold_c or len(gold_c) < 10:
    gold_c = _sim_ohlcv(200, tf_min, "XAUUSD", base_price=gold_price_real or 3200.0)
elif gold_price_real > 0:
    # Ancrage du dernier close au vrai prix
    try:
        gold_c[-1]["close"] = gold_price_real
    except Exception:
        pass

# DXY simulé
dxy_price_real = float(ss.dxy_price) if float(ss.dxy_price) > 0 else 104.5
dxy_c = _sim_ohlcv(200, tf_min, "DXY", base_price=dxy_price_real)

# Prix affichés — calcul depuis OHLCV si API manquante
if gold_price_real == 0 and gold_c:
    gold_price_real = float(gold_c[-1]["close"])
    ss.gold_price = gold_price_real

gold_bid  = float(ss.gold_bid)  if float(ss.gold_bid)  > 0 else round(gold_price_real - 0.15, 2)
gold_ask  = float(ss.gold_ask)  if float(ss.gold_ask)  > 0 else round(gold_price_real + 0.15, 2)
gold_chg  = float(ss.gold_change)
gold_pct  = float(ss.gold_pct)
dxy_chg   = float(ss.dxy_change)
corr_val  = float(ss.correlation)

signal    = ss.signal if isinstance(ss.signal, dict) else _INIT["signal"]
zones     = ss.zones  if isinstance(ss.zones,  dict) else _INIT["zones"]
mtf       = ss.mtf
mt5_ok    = bool(ss.mt5_connected)
sig_dir   = signal.get("direction", "WAIT")
sig_res   = signal.get("result", "")
ant       = signal.get("anticipation") or ""
conf      = int(signal.get("confidence", 0))
pipe      = signal.get("pipeline_state", "IDLE")
entry_p   = float(signal.get("entry",  0.0))
tp_p      = float(signal.get("tp",     0.0))
sl_p      = float(signal.get("sl",     0.0))
rr_p      = signal.get("rr", 0.0)
lot_p     = signal.get("lot", 0.0)
corr_p    = float(signal.get("corr",   corr_val))

BC = {"BUY": "bb", "SELL": "bs", "WAIT": "bw"}

corr_data = _rolling_corr(gold_c, dxy_c, window=50)

# ── DETECT ORDER BLOCKS ───────────────────────────────────────────────────────
def _to_df(candles: list) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df

def detect_obs(df: pd.DataFrame, swing_len: int = 5) -> dict:
    if df.empty or len(df) < swing_len * 2 + 1:
        return {"bullish_obs": [], "bearish_obs": []}
    highs  = df["high"].values
    lows   = df["low"].values
    opens  = df["open"].values
    closes = df["close"].values
    vols   = df["volume"].values if "volume" in df.columns else np.ones(len(df))
    times  = df["time"].values
    n      = len(df)

    def _sh(i):
        return (i >= swing_len and i < n - swing_len and
                all(highs[i] >= highs[i - j] for j in range(1, swing_len + 1)) and
                all(highs[i] >= highs[i + j] for j in range(1, swing_len + 1)))

    def _sl(i):
        return (i >= swing_len and i < n - swing_len and
                all(lows[i] <= lows[i - j] for j in range(1, swing_len + 1)) and
                all(lows[i] <= lows[i + j] for j in range(1, swing_len + 1)))

    shs = [i for i in range(swing_len, n - swing_len) if _sh(i)]
    sls = [i for i in range(swing_len, n - swing_len) if _sl(i)]
    bull_obs, bear_obs = [], []

    for sh in shs:
        win = range(max(0, sh - swing_len * 2), sh)
        bc  = [(i, vols[i]) for i in win if closes[i] > opens[i]]
        if not bc: continue
        idx = max(bc, key=lambda x: x[1])[0]
        avg = (highs[idx] + lows[idx]) / 2
        ob  = {"type": "bearish", "top": float(highs[idx]), "bottom": float(lows[idx]),
               "avg": float(avg), "time": times[idx],
               "time_end": times[min(sh + swing_len, n - 1)]}
        ob["mitigated"] = bool(np.any(highs[sh:] >= avg))
        bear_obs.append(ob)

    for sl in sls:
        win = range(max(0, sl - swing_len * 2), sl)
        bc  = [(i, vols[i]) for i in win if closes[i] < opens[i]]
        if not bc: continue
        idx = max(bc, key=lambda x: x[1])[0]
        avg = (highs[idx] + lows[idx]) / 2
        ob  = {"type": "bullish", "top": float(highs[idx]), "bottom": float(lows[idx]),
               "avg": float(avg), "time": times[idx],
               "time_end": times[min(sl + swing_len, n - 1)]}
        ob["mitigated"] = bool(np.any(lows[sl:] <= avg))
        bull_obs.append(ob)

    bull_obs = sorted([o for o in bull_obs if not o["mitigated"]],
                      key=lambda x: str(x["time"]), reverse=True)[:3]
    bear_obs = sorted([o for o in bear_obs if not o["mitigated"]],
                      key=lambda x: str(x["time"]), reverse=True)[:3]
    return {"bullish_obs": bull_obs, "bearish_obs": bear_obs}

gold_df  = _to_df(gold_c)
gold_obs = detect_obs(gold_df) if not gold_df.empty else {"bullish_obs": [], "bearish_obs": []}
n_ob_b   = len(gold_obs.get("bullish_obs", []))
n_ob_s   = len(gold_obs.get("bearish_obs", []))

# ── HELPERS UI ────────────────────────────────────────────────────────────────
def result_badge(r: str) -> str:
    if r == "WIN":  return '<span class="bwin">✅ WIN</span>'
    if r == "LOSS": return '<span class="bloss">❌ LOSS</span>'
    if r == "OPEN": return '<span class="bopen">🔵 OPEN</span>'
    return ""

def _plt(fig, key: str, small: bool = False):
    cfg = {
        "displaylogo": False,
        "scrollZoom": not small,
        "displayModeBar": not small,
        "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    }
    try:
        st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except Exception:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)

# ── GRAPHIQUES ────────────────────────────────────────────────────────────────
def draw_zones(fig, z: dict, row: int = 1):
    s = z.get("support",    0)
    r = z.get("resistance", 0)
    if s > 0:
        fig.add_hline(y=s, row=row, col=1,
            line=dict(color="rgba(0,212,170,.45)", width=1, dash="dot"),
            annotation_text="S", annotation_font=dict(color="#00d4aa", size=8))
    if r > 0:
        fig.add_hline(y=r, row=row, col=1,
            line=dict(color="rgba(255,77,106,.45)", width=1, dash="dot"),
            annotation_text="R", annotation_font=dict(color="#ff4d6a", size=8))
    for fvg in z.get("fvg_bullish", []):
        try:
            fig.add_hrect(y0=fvg["low"], y1=fvg["high"], row=row, col=1,
                fillcolor="rgba(0,212,170,.07)",
                line=dict(color="rgba(0,212,170,.2)", width=.5))
        except Exception:
            pass
    for fvg in z.get("fvg_bearish", []):
        try:
            fig.add_hrect(y0=fvg["low"], y1=fvg["high"], row=row, col=1,
                fillcolor="rgba(255,77,106,.07)",
                line=dict(color="rgba(255,77,106,.2)", width=.5))
        except Exception:
            pass
    if z.get("ob_buy"):
        fig.add_hline(y=z["ob_buy"],  row=row, col=1,
            line=dict(color="rgba(0,212,170,.65)", width=1.2),
            annotation_text="OB↑", annotation_font=dict(color="#00d4aa", size=8))
    if z.get("ob_sell"):
        fig.add_hline(y=z["ob_sell"], row=row, col=1,
            line=dict(color="rgba(255,77,106,.65)", width=1.2),
            annotation_text="OB↓", annotation_font=dict(color="#ff4d6a", size=8))

def draw_obs(fig, obs_data: dict, row: int = 1):
    for ob in obs_data.get("bullish_obs", []):
        try:
            fig.add_shape(type="rect",
                x0=ob["time"], x1=ob["time_end"],
                y0=ob["bottom"], y1=ob["top"],
                row=row, col=1,
                line=dict(color="rgba(0,212,170,0.5)", width=1),
                fillcolor="rgba(0,212,170,0.07)")
            fig.add_annotation(x=ob["time_end"], y=ob["top"],
                text="OB↑", showarrow=False,
                font=dict(color="#00d4aa", size=7),
                xanchor="left", yanchor="bottom", row=row, col=1)
        except Exception:
            pass
    for ob in obs_data.get("bearish_obs", []):
        try:
            fig.add_shape(type="rect",
                x0=ob["time"], x1=ob["time_end"],
                y0=ob["bottom"], y1=ob["top"],
                row=row, col=1,
                line=dict(color="rgba(255,77,106,0.5)", width=1),
                fillcolor="rgba(255,77,106,0.07)")
            fig.add_annotation(x=ob["time_end"], y=ob["bottom"],
                text="OB↓", showarrow=False,
                font=dict(color="#ff4d6a", size=7),
                xanchor="left", yanchor="top", row=row, col=1)
        except Exception:
            pass
    return fig

def build_candle(candles: list, symbol: str, color: str, tf_name: str,
                 signal=None, zones=None, show_zones=True, obs_data=None) -> go.Figure:
    df = _to_df(candles)
    tf_lbl = {"M5": "5 Min", "M15": "15 Min", "H1": "1 Hour"}.get(tf_name, tf_name)

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
            height=380, margin=dict(l=0, r=8, t=30, b=0))
        fig.add_annotation(text="⏳ En attente de données…",
            xref="paper", yref="paper", x=.5, y=.5,
            font=dict(color=C["text"], size=12), showarrow=False)
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=.01, row_heights=[.78, .22])

    # Chandeliers
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=symbol,
        increasing=dict(line=dict(color=C["green"], width=1), fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],   width=1), fillcolor=C["red"]),
        whiskerwidth=.2), row=1, col=1)

    # EMA
    fig.add_trace(go.Scatter(
        x=df["time"], y=df["close"].ewm(span=20).mean(),
        name="EMA20", line=dict(color=color, width=1.2, dash="dot"), opacity=.7),
        row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df["time"], y=df["close"].ewm(span=50).mean(),
        name="EMA50", line=dict(color="rgba(255,255,255,.18)", width=.9), opacity=.5),
        row=1, col=1)

    # Zones
    if show_zones and zones:
        draw_zones(fig, zones, row=1)
    if show_zones and obs_data:
        draw_obs(fig, obs_data, row=1)

    # Prix courant
    lp = float(df["close"].iloc[-1])
    fig.add_hline(y=lp, row=1, col=1,
        line=dict(color=color, width=.8, dash="dash"), opacity=.5)

    # Marqueur signal + TP/SL
    if signal and signal.get("direction") in ("BUY", "SELL"):
        lt  = df["time"].iloc[-1]
        up  = signal["direction"] == "BUY"
        fig.add_trace(go.Scatter(
            x=[lt], y=[lp * (.9992 if up else 1.0008)], mode="markers",
            marker=dict(symbol="triangle-up" if up else "triangle-down",
                        size=14, color=C["green"] if up else C["red"],
                        line=dict(color="white", width=1)),
            showlegend=False, name="Signal"), row=1, col=1)
        if signal.get("tp") and signal["tp"] > 0:
            fig.add_hline(y=signal["tp"], row=1, col=1,
                line=dict(color=C["green"], width=.8, dash="dash"), opacity=.6)
        if signal.get("sl") and signal["sl"] > 0:
            fig.add_hline(y=signal["sl"], row=1, col=1,
                line=dict(color=C["red"], width=.8, dash="dash"), opacity=.6)

    # Volume
    vol_col = df.get("volume", None)
    if vol_col is None and "tick_volume" in df.columns:
        vol_col = df["tick_volume"]
    if vol_col is None:
        vol_col = pd.Series(np.zeros(len(df)))
    vc = [C["green"] if c >= o else C["red"]
          for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df["time"], y=vol_col,
        marker=dict(color=vc, opacity=.45), showlegend=False),
        row=2, col=1)

    ax = dict(showgrid=True, gridcolor=C["grid"], gridwidth=1, zeroline=False,
              tickfont=dict(size=8, color=C["text"]), linecolor=C["grid"])
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        margin=dict(l=0, r=8, t=32, b=0), height=380,
        font=dict(family="JetBrains Mono", color=C["text"], size=8),
        legend=dict(orientation="h", x=0, y=1.08,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=7)),
        hovermode="x unified", xaxis_rangeslider_visible=False,
        title=dict(
            text=(f'<b style="color:{color};font-size:12px">{symbol}</b>'
                  f'<span style="color:#2e3a4e;font-size:9px"> ● {tf_lbl}</span>'
                  f'  <span style="color:{color};font-weight:700;font-size:13px">'
                  f'{lp:,.2f}</span>'),
            x=.01, font=dict(size=11, family="Inter")),
        dragmode="pan")
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax, tickformat=".5g")
    return fig

def build_corr_chart(corr_data: list) -> go.Figure:
    fig = go.Figure()
    if corr_data:
        times = [d["time"] for d in corr_data]
        corrs = [d["corr"]  for d in corr_data]
        # Zone colorée
        colors = ["rgba(0,212,170,.15)" if c < -.5 else
                  ("rgba(247,181,41,.1)" if c < 0 else "rgba(255,77,106,.1)")
                  for c in corrs]
        fig.add_trace(go.Scatter(
            x=times, y=corrs,
            line=dict(color=C["gold"], width=1.8),
            fill="tozeroy", fillcolor="rgba(247,181,41,.07)",
            hovertemplate="Corr: <b>%{y:.4f}</b><extra></extra>"))
        for y, c, lbl in [(-.6, C["green"], "-0.60"),
                          (-.52, "rgba(0,212,170,.4)", "-0.52"),
                          (0, C["text"], "0"),
                          (.52, "rgba(255,77,106,.4)", "+0.52"),
                          (.6, C["red"], "+0.60")]:
            fig.add_hline(y=y, line=dict(color=c, width=.7, dash="dot"),
                opacity=.6, annotation_text=lbl,
                annotation_position="left",
                annotation_font=dict(color=c, size=8))
    else:
        fig.add_annotation(text="En attente OHLCV…",
            xref="paper", yref="paper", x=.5, y=.5,
            font=dict(color=C["text"], size=11), showarrow=False)

    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"], height=180,
        margin=dict(l=0, r=65, t=28, b=0),
        font=dict(family="JetBrains Mono", color=C["text"], size=8),
        title=dict(
            text='<span style="color:#64748b;font-size:8px;font-weight:600;letter-spacing:.08em;">CORRÉLATION ROLLING GOLD/DXY — 50 bougies</span>',
            x=.01),
        hovermode="x unified", showlegend=False, dragmode="pan",
        yaxis=dict(range=[-1.05, 1.05], showgrid=True, gridcolor=C["grid"],
                   zeroline=False, tickfont=dict(size=8),
                   tickvals=[-1, -.6, -.2, 0, .2, .6, 1]),
        xaxis=dict(showgrid=False, tickfont=dict(size=8)))
    return fig

def build_gauge(corr: float) -> go.Figure:
    col = C["green"] if corr < -.5 else (C["red"] if corr > .5 else C["gold"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=corr,
        number=dict(font=dict(size=26, color=col, family="JetBrains Mono"),
                    valueformat="+.3f"),
        gauge=dict(
            axis=dict(range=[-1, 1], tickfont=dict(size=7), nticks=9),
            bar=dict(color=col, thickness=.2),
            bgcolor=C["bg"], bordercolor=C["grid"], borderwidth=1,
            steps=[
                dict(range=[-1, -.6], color="rgba(0,212,170,.1)"),
                dict(range=[-.6, .6], color="rgba(247,181,41,.04)"),
                dict(range=[.6,  1],  color="rgba(255,77,106,.1)"),
            ]),
        title=dict(text="CORRÉLATION",
                   font=dict(size=8, color=C["text"]))))
    fig.update_layout(
        paper_bgcolor=C["bg2"], height=155,
        margin=dict(l=8, r=8, t=24, b=4))
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding:10px 0 14px;">
        <div style="font-family:'Inter',sans-serif;font-weight:800;font-size:1.05rem;
            background:linear-gradient(90deg,#f7b529,#ffd166);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            letter-spacing:.02em;">⚡ GOLD/DXY PRO</div>
        <div style="font-size:.5rem;color:#1e2d42;letter-spacing:.15em;
            text-transform:uppercase;margin-top:2px;">Algo Trading Dashboard v13</div>
    </div>""", unsafe_allow_html=True)

    # Timeframe
    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf_sel = st.radio("TF", ["M5", "M15", "H1"], horizontal=True,
                      label_visibility="collapsed",
                      index=["M5", "M15", "H1"].index(ss.tf))
    if tf_sel != ss.tf:
        ss.tf = tf_sel

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── PRIX RÉELS ────────────────────────────────────────────────────────────
    gc = "#00d4aa" if gold_chg >= 0 else "#ff4d6a"
    dc = "#00d4aa" if dxy_chg  >= 0 else "#ff4d6a"
    gc_arrow = "▲" if gold_chg >= 0 else "▼"
    dc_arrow = "▲" if dxy_chg  >= 0 else "▼"

    st.markdown(f"""
    <div class="card card-gold">
        <div class="lbl">XAUUSD — OR</div>
        <div class="price-main">{gold_price_real:,.2f}</div>
        <div style="display:flex;gap:10px;margin-top:4px;">
            <span class="{'price-change-up' if gold_chg >= 0 else 'price-change-dn'}">
                {gc_arrow} {gold_chg:+.2f} ({gold_pct:+.2f}%)</span>
        </div>
        <div style="font-size:.57rem;color:#2e3a4e;margin-top:3px;">
            BID <b style="color:#dde3ee;">{gold_bid:,.2f}</b>
            &nbsp;|&nbsp;
            ASK <b style="color:#dde3ee;">{gold_ask:,.2f}</b>
        </div>
    </div>
    <div class="card">
        <div class="lbl">DXY — Dollar Index</div>
        <div style="font-family:'JetBrains Mono';font-size:1.4rem;font-weight:700;color:#4da6ff;">
            {dxy_price_real:.3f}</div>
        <div class="{'price-change-up' if dxy_chg >= 0 else 'price-change-dn'}" style="margin-top:3px;">
            {dc_arrow} {dxy_chg:+.4f}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── SIGNAL ────────────────────────────────────────────────────────────────
    ant_html = (f'<div style="margin-top:5px;"><span class="ba" style="font-size:.55rem;">'
                f'{ant}</span></div>') if ant else ""
    res_b    = result_badge(sig_res)

    pipe_color = {"IDLE": "#2e3a4e", "WAIT_M15": "#f7b529", "WAIT_M5": "#a78bfa"}.get(pipe, "#64748b")

    st.markdown(f"""
    <div class="card card-gold">
        <div class="lbl">Signal Actif</div>
        <div style="display:flex;gap:7px;align-items:center;margin:6px 0;">
            <span class="{BC[sig_dir]}" style="font-size:.72rem;padding:4px 12px;">{sig_dir}</span>
            {res_b}
        </div>
        {ant_html}
        <div style="font-size:.6rem;color:#64748b;line-height:2.0;margin-top:5px;">
            Confiance: <b style="color:#e2e8f0;">{conf}%</b><br>
            Corrélation: <b style="color:#e2e8f0;">{corr_p:+.4f}</b><br>
            Entrée: <b style="color:#f7b529;">{entry_p:,.2f if entry_p > 0 else "—"}</b><br>
            TP: <b style="color:#00d4aa;">{tp_p:,.2f if tp_p > 0 else "—"}</b><br>
            SL: <b style="color:#ff4d6a;">{sl_p:,.2f if sl_p > 0 else "—"}</b><br>
            R/R: <b style="color:#e2e8f0;">1:{rr_p}</b>&nbsp;|&nbsp;Lot: <b style="color:#e2e8f0;">{lot_p}</b><br>
            <span style="color:{pipe_color};font-weight:600;">{pipe}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Corrélation
    cc = "#00d4aa" if corr_val < -.6 else ("#f7b529" if corr_val < -.4 else "#ff4d6a")
    ct = "✅ Forte (signal possible)" if corr_val < -.6 else (
         "⚠️ Modérée (attendre)" if corr_val < -.4 else "❌ Faible (éviter)")
    st.markdown(f"""
    <div class="card">
        <div class="lbl">Corrélation</div>
        <div style="font-family:'JetBrains Mono';font-size:1.1rem;font-weight:700;color:{cc};">
            {corr_val:+.4f}</div>
        <div style="font-size:.57rem;color:{cc};margin-top:2px;">{ct}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Options
    ss.show_zones = st.checkbox("Afficher zones (S/R · FVG · OB)", value=ss.show_zones)
    fvg_count = len(zones.get("fvg_bullish", [])) + len(zones.get("fvg_bearish", []))
    st.markdown(f"""
    <div style="font-size:.52rem;color:#2e3a4e;line-height:1.9;margin-top:3px;">
        {fvg_count} FVG · ATR={zones.get("atr", 0):.2f}
        · OB↑ {n_ob_b} · OB↓ {n_ob_s}
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Statut connexion
    dot_api = "dot-green" if api_ok  else "dot-yellow"
    dot_mt5 = "dot-green" if mt5_ok else "dot-yellow"
    st.markdown(f"""
    <div style="font-size:.62rem;">
        <div style="margin-bottom:4px;">
            <span class="{dot_api}"></span>
            <span style="color:{'#00d4aa' if api_ok else '#f7b529'};">
                {'API Live' if api_ok else 'Simulation'}</span>
        </div>
        <div>
            <span class="{dot_mt5}"></span>
            <span style="color:{'#00d4aa' if mt5_ok else '#f7b529'};">
                MT5 {'Connecté' if mt5_ok else 'Déconnecté'}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Stats
    c1, c2 = st.columns(2)
    with c1: st.metric("Winrate",  f"{ss.winrate}%")
    with c2: st.metric("W / L",    f"{ss.wins}/{ss.losses}")

    st.markdown(f"""
    <div style="font-size:.49rem;color:#1e2d42;text-align:center;margin-top:8px;line-height:2.2;">
        {ss.gold_symbol} · {tf} · Tick #{ss.tick}<br>
        {datetime.now().strftime('%H:%M:%S')}
        {f"<br>Màj: {ss.last_update[-8:] if len(str(ss.last_update)) >= 8 else ss.last_update}" if ss.last_update != '—' else ''}
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
dot_h  = "dot-green" if api_ok else "dot-yellow"
api_lbl = "HTTP Live" if api_ok else "Simulation"
ant_hd  = f' <span class="ba">{ant}</span>' if ant else ""
res_hd  = result_badge(sig_res)
gc_hd   = "#00d4aa" if gold_chg >= 0 else "#ff4d6a"

st.markdown(f"""
<div style="display:flex;align-items:flex-start;justify-content:space-between;
    padding:4px 0 10px;border-bottom:1px solid rgba(255,255,255,.06);margin-bottom:10px;">
    <div>
        <div style="font-family:'Inter',sans-serif;font-weight:800;font-size:1.5rem;
            background:linear-gradient(90deg,#f7b529,#ffd166);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.1;">
            GOLD / DXY PRO</div>
        <div style="font-size:.58rem;color:#64748b;margin-top:3px;display:flex;gap:10px;align-items:center;">
            <span><span class="{dot_h}"></span>{api_lbl}</span>
            <span>·</span>
            <span>MT5 {'Live' if mt5_ok else 'Off'}</span>
            <span>·</span>
            <span style="color:#f7b529;">{tf}</span>
            <span>·</span>
            <span>{ss.gold_symbol}</span>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;padding-top:4px;flex-wrap:wrap;">
        <div style="text-align:right;">
            <div style="font-family:'JetBrains Mono';font-size:1.3rem;font-weight:700;color:#f7b529;">
                {gold_price_real:,.2f}</div>
            <div style="font-size:.6rem;color:{gc_hd};">{gold_chg:+.2f} ({gold_pct:+.2f}%)</div>
        </div>
        <div style="width:1px;height:32px;background:rgba(255,255,255,.08);"></div>
        <span class="{BC[sig_dir]}">{sig_dir}</span>{ant_hd}{res_hd}
        <span style="font-size:.62rem;color:#64748b;">
            Conf <b style="color:#e2e8f0;">{conf}%</b>
        </span>
        <span style="font-family:'JetBrains Mono';font-size:1rem;font-weight:600;
            color:#64748b;margin-left:4px;">
            {datetime.now().strftime('%H:%M:%S')}</span>
    </div>
</div>""", unsafe_allow_html=True)

# ── MÉTRIQUES HEADER ──────────────────────────────────────────────────────────
m = st.columns(7)
with m[0]:
    st.metric("XAUUSD", f"{gold_price_real:,.2f}",
              f"{gold_chg:+.2f} ({gold_pct:+.2f}%)")
with m[1]:
    st.metric("DXY", f"{dxy_price_real:.3f}", f"{dxy_chg:+.4f}")
with m[2]:
    corr_lbl = "Forte ✅" if corr_val < -.6 else ("Modérée ⚠️" if corr_val < -.4 else "Faible ❌")
    st.metric("Corrélation", f"{corr_val:+.4f}", corr_lbl)
with m[3]:
    emo  = {"BUY": "🟢", "SELL": "🔴", "WAIT": "⚪"}
    slbl = f"{emo[sig_dir]} {sig_dir}"
    if sig_res in ("WIN", "LOSS"):
        slbl += f" → {'✅' if sig_res == 'WIN' else '❌'}"
    st.metric("Signal", slbl, f"Conf: {conf}%")
with m[4]:
    st.metric("Winrate", f"{ss.winrate}%", f"{ss.wins}W / {ss.losses}L")
with m[5]:
    st.metric("BID / ASK", f"{gold_bid:,.2f}", f"ASK {gold_ask:,.2f}")
with m[6]:
    st.metric("R/R", f"1:{rr_p}", f"SL: {signal.get('sl_source','—')}")

# ══════════════════════════════════════════════════════════════════════════════
# TABS (sans Backtest)
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Graphiques",
    "🎯 Signal & Zones",
    "🔀 Multi-TF",
    "📋 Logs Bot",
    "📜 Historique",
])

# ── TAB 1 : GRAPHIQUES ────────────────────────────────────────────────────────
with tab1:
    g1, g2 = st.columns(2)
    with g1:
        _plt(build_candle(gold_c, "XAUUSD", C["gold"], tf,
                          signal=signal, zones=zones,
                          show_zones=ss.show_zones, obs_data=gold_obs),
             key="gold_chart")
    with g2:
        _plt(build_candle(dxy_c, "DXY", C["dxy"], tf,
                          show_zones=False),
             key="dxy_chart")

    _plt(build_corr_chart(corr_data), key="corr_chart")

    if corr_data:
        lc = corr_data[-1]["corr"]
        zc = "#00d4aa" if lc < -.6 else ("#f7b529" if lc < -.4 else "#ff4d6a")
        zt = "Zone signal active ✅" if lc < -.6 else (
             "Zone modérée ⚠️" if lc < -.4 else "Hors zone ❌")
        st.markdown(
            f'<div style="font-size:.6rem;color:{zc};margin-top:2px;">'
            f'Corrélation actuelle : <b>{lc:+.4f}</b> · {zt}</div>',
            unsafe_allow_html=True)

# ── TAB 2 : SIGNAL & ZONES ────────────────────────────────────────────────────
with tab2:
    s1, s2, s3 = st.columns([1, 1, 1.2])

    with s1:
        _plt(build_gauge(corr_val), key="gauge_t2", small=True)
        if corr_val < -.65:
            ic, it = C["green"], "✅ Forte — signaux fiables"
        elif corr_val < -.4:
            ic, it = C["gold"],  "⚠️ Modérée — attendre"
        else:
            ic, it = C["red"],   "❌ Faible — éviter"
        st.markdown(
            f'<div style="font-size:.63rem;color:{ic};background:rgba(255,255,255,.02);'
            f'border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:8px 10px;'
            f'margin-top:4px;">{it}</div>', unsafe_allow_html=True)

    with s2:
        res_b2 = result_badge(sig_res)
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
                <span class="{BC[sig_dir]}" style="font-size:.72rem;padding:4px 12px;">{sig_dir}</span>
                {res_b2}
            </div>
            <div style="font-size:.65rem;color:#64748b;line-height:2.2;">
                Confiance:&nbsp;<b style="color:#e2e8f0;">{conf}%</b><br>
                Corrélation:&nbsp;<b style="color:#e2e8f0;">{corr_p:+.4f}</b><br>
                Entrée:&nbsp;<b style="color:#f7b529;">{entry_p:,.2f if entry_p > 0 else "—"}</b><br>
                TP:&nbsp;<b style="color:#00d4aa;">{tp_p:,.2f if tp_p > 0 else "—"}</b><br>
                SL:&nbsp;<b style="color:#ff4d6a;">{sl_p:,.2f if sl_p > 0 else "—"}</b><br>
                R/R:&nbsp;<b style="color:#e2e8f0;">1:{rr_p}</b><br>
                Lot:&nbsp;<b style="color:#e2e8f0;">{lot_p}</b><br>
                Pipeline:&nbsp;<b style="color:#e2e8f0;">{pipe}</b>
            </div>
        </div>""", unsafe_allow_html=True)

        if ant:
            st.markdown(f"""
            <div style="background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.3);
                border-radius:8px;padding:10px 12px;margin-top:6px;">
                <div style="font-size:.54rem;color:#a78bfa;font-weight:700;
                    letter-spacing:.1em;margin-bottom:3px;">ANTICIPATION</div>
                <div style="font-size:.67rem;color:#c4b5fd;">{ant}</div>
            </div>""", unsafe_allow_html=True)

    with s3:
        sup   = zones.get("support",    0)
        res_z = zones.get("resistance", 0)
        atr   = zones.get("atr",        0)
        st.markdown(f"""
        <div class="card">
            <div class="lbl" style="margin-bottom:7px;">Support / Résistance</div>
            <div style="font-size:.66rem;line-height:2.2;">
                <span style="color:#64748b;">Support:</span>
                <b style="color:#00d4aa;float:right;">{sup:,.2f if sup > 0 else "—"}</b><br>
                <span style="color:#64748b;">Résistance:</span>
                <b style="color:#ff4d6a;float:right;">{res_z:,.2f if res_z > 0 else "—"}</b><br>
                <span style="color:#64748b;">ATR:</span>
                <b style="color:#f7b529;float:right;">{atr:.3f}</b>
            </div>
        </div>
        <div class="card">
            <div class="lbl" style="margin-bottom:7px;">FVG & Order Blocks</div>
            <div style="font-size:.66rem;line-height:2.2;">
                <span style="color:#64748b;">FVG Bullish:</span>
                <b style="color:#00d4aa;float:right;">{len(zones.get('fvg_bullish', []))} zones</b><br>
                <span style="color:#64748b;">FVG Bearish:</span>
                <b style="color:#ff4d6a;float:right;">{len(zones.get('fvg_bearish', []))} zones</b><br>
                <span style="color:#64748b;">OB↑ actifs:</span>
                <b style="color:#00d4aa;float:right;">{n_ob_b}</b><br>
                <span style="color:#64748b;">OB↓ actifs:</span>
                <b style="color:#ff4d6a;float:right;">{n_ob_s}</b>
            </div>
        </div>""", unsafe_allow_html=True)

        if gold_obs.get("bullish_obs") or gold_obs.get("bearish_obs"):
            rows_ob = ""
            for ob in gold_obs.get("bullish_obs", []):
                rows_ob += (f'<div style="font-size:.59rem;color:#00d4aa;line-height:1.8;">'
                            f'↑ {ob["bottom"]:,.2f} – {ob["top"]:,.2f}'
                            f'<span style="color:#2e3a4e;"> avg:{ob["avg"]:,.2f}</span></div>')
            for ob in gold_obs.get("bearish_obs", []):
                rows_ob += (f'<div style="font-size:.59rem;color:#ff4d6a;line-height:1.8;">'
                            f'↓ {ob["bottom"]:,.2f} – {ob["top"]:,.2f}'
                            f'<span style="color:#2e3a4e;"> avg:{ob["avg"]:,.2f}</span></div>')
            st.markdown(
                f'<div class="card"><div class="lbl" style="margin-bottom:5px;">'
                f'Détail OB</div>{rows_ob}</div>',
                unsafe_allow_html=True)

# ── TAB 3 : MULTI-TF ──────────────────────────────────────────────────────────
with tab3:
    mc = st.columns(3)
    for col, tf_n in zip(mc, ["H1", "M15", "M5"]):
        d   = mtf.get(tf_n, {})
        sig = d.get("signal", "WAIT")
        cr  = d.get("corr",   0.0)
        tr  = d.get("trend",  "—")
        cc2 = C["green"] if cr < -.6 else (C["gold"] if cr < 0 else C["red"])
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;padding:16px 14px;">
                <div style="font-family:'Inter';font-weight:800;font-size:1.1rem;
                    color:#e2e8f0;margin-bottom:8px;">{tf_n}</div>
                <span class="{BC.get(sig, 'bw')}">{sig}</span>
                <div style="font-size:.64rem;color:#64748b;line-height:2.1;
                    margin-top:8px;text-align:left;">
                    Corr:&nbsp;<b style="color:{cc2};float:right;">{cr:+.4f}</b><br>
                    Trend:&nbsp;<b style="color:#e2e8f0;float:right;">{tr}</b>
                </div>
            </div>""", unsafe_allow_html=True)

    sigs  = [mtf.get(t, {}).get("signal", "WAIT") for t in ["H1", "M15", "M5"]]
    buys  = sigs.count("BUY")
    sells = sigs.count("SELL")
    if   buys  >= 2: cons, cc3 = "🟢 CONSENSUS BUY",     C["green"]
    elif sells >= 2: cons, cc3 = "🔴 CONSENSUS SELL",    C["red"]
    else:            cons, cc3 = "⚪ PAS DE CONSENSUS",   C["gold"]
    st.markdown(f"""
    <div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.07);
        border-radius:10px;padding:14px;text-align:center;margin-top:10px;">
        <div style="font-size:.72rem;color:{cc3};font-weight:700;margin-bottom:4px;">{cons}</div>
        <div style="font-size:.58rem;color:#2e3a4e;">
            H1: {sigs[0]} · M15: {sigs[1]} · M5: {sigs[2]}</div>
    </div>""", unsafe_allow_html=True)

# ── TAB 4 : LOGS ──────────────────────────────────────────────────────────────
with tab4:
    lc1, lc2 = st.columns([3, 1])
    with lc1:
        st.markdown('<div class="lbl">Journal du Bot</div>', unsafe_allow_html=True)
    with lc2:
        lf = st.selectbox("Filtre", ["ALL", "SIGNAL", "WARNING", "ERROR"],
                          label_visibility="collapsed")

    filtered = [l for l in reversed(ss.bot_logs)
                if lf == "ALL" or l.get("level") == lf]
    rows = ""
    for e in filtered[:80]:
        lvl = e.get("level", "INFO").upper()
        col = {"INFO": "#64748b", "WARNING": "#f7b529",
               "ERROR": "#ff4d6a", "SIGNAL": "#00d4aa"}.get(lvl, "#64748b")
        rows += (f'<div style="padding:2px 0;border-bottom:1px solid rgba(255,255,255,.02);">'
                 f'<span style="color:#2e3a4e;">{e.get("time","")}</span> '
                 f'<span style="color:{col};font-weight:600;">[{lvl}]</span> '
                 f'<span style="color:#9ca3af;">{e.get("msg","")}</span></div>')
    st.markdown(
        f'<div style="background:#0f1623;border:1px solid rgba(255,255,255,.06);'
        f'border-radius:10px;padding:12px;height:290px;overflow-y:auto;'
        f'font-family:\'JetBrains Mono\',monospace;font-size:.6rem;line-height:1.9;">'
        f'{rows}</div>',
        unsafe_allow_html=True)

# ── TAB 5 : HISTORIQUE ────────────────────────────────────────────────────────
with tab5:
    h1c, h2c, h3c, h4c = st.columns(4)
    with h1c: st.metric("Total",   len(ss.signals))
    with h2c: st.metric("Winrate", f"{ss.winrate}%")
    with h3c: st.metric("Wins",    ss.wins)
    with h4c: st.metric("Losses",  ss.losses)

    if ss.signals:
        df_s = pd.DataFrame(ss.signals[::-1][-50:])

        def _rl(v):
            return {"WIN": "✅ WIN", "LOSS": "❌ LOSS", "OPEN": "🔵 OPEN"}.get(str(v), str(v))

        if "result" in df_s.columns:
            df_s["result"] = df_s["result"].apply(_rl)

        cols = [c for c in ["time", "direction", "tf", "entry", "tp", "sl",
                             "rr", "lot", "sl_source", "result"]
                if c in df_s.columns]

        def _sty(v):
            return {
                "BUY":      "color:#00d4aa;font-weight:700",
                "SELL":     "color:#ff4d6a;font-weight:700",
                "✅ WIN":   "color:#00d4aa",
                "❌ LOSS":  "color:#ff4d6a",
                "🔵 OPEN":  "color:#f7b529",
            }.get(str(v), "color:#64748b")

        try:
            sub = [c for c in ["direction", "result"] if c in cols]
            try:
                st.dataframe(df_s[cols].style.map(_sty, subset=sub),
                             width="stretch", height=310)
            except Exception:
                st.dataframe(df_s[cols].style.map(_sty, subset=sub),
                             use_container_width=True, height=310)
        except Exception:
            try:
                st.dataframe(df_s[cols], width="stretch", height=310)
            except Exception:
                st.dataframe(df_s[cols], use_container_width=True, height=310)
    else:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#2e3a4e;font-size:.7rem;">
            Aucun signal enregistré.<br>
            <span style="font-size:.6rem;color:#1e2d42;">Lance le bot pour voir l'historique.</span>
        </div>""", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:5px 0 2px;font-size:.48rem;color:#1a2234;
    border-top:1px solid rgba(255,255,255,.04);margin-top:6px;">
    Gold/DXY Pro v13 · {'🟢 Live' if api_ok else '🟡 Simulation'} ·
    Tick #{ss.tick} · Refresh {REFRESH_S}s ·
    {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
</div>""", unsafe_allow_html=True)

time.sleep(REFRESH_S)
st.rerun()
