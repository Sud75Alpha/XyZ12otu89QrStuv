"""
GOLD/DXY PRO DASHBOARD v3.1
Fixes : sidebar toujours visible · graphes sans flash · refresh fluide
"""

import os, time, json, threading, queue
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ── Imports optionnels ────────────────────────────────────────────────────────
try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import websocket as _websocket
    HAS_WS = True
except ImportError:
    HAS_WS = False

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG — DOIT ÊTRE EN PREMIER
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GOLD/DXY Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",   # sidebar toujours ouverte
)

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG API
# ─────────────────────────────────────────────────────────────────────────────

try:
    API_URL = st.secrets["API_URL"]
    API_KEY = st.secrets["API_KEY"]
except Exception:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "gold_dxy_secret_2024")

WS_URL       = API_URL.replace("https://","wss://").replace("http://","ws://") + f"/ws?api_key={API_KEY}"
HTTP_HEADERS = {"X-API-Key": API_KEY}
HTTP_TIMEOUT = 3
REFRESH_S    = 2.0   # intervalle rerun — assez lent pour éviter le flash

# ─────────────────────────────────────────────────────────────────────────────
#  CSS — sidebar forcée visible + anti-flash graphes
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

/* ── Variables ── */
:root {
    --bg:#080b0f; --bg2:#0d1117;
    --glass:rgba(255,255,255,0.025);
    --border:rgba(255,255,255,0.06);
    --border-gold:rgba(247,181,41,0.3);
    --gold:#f7b529; --green:#00d4aa; --red:#ff4d6a;
    --blue:#4da6ff; --purple:#a78bfa;
    --text:#dde3ee; --text2:#6b7a94; --text3:#2e3a4e;
    --mono:'JetBrains Mono',monospace;
    --display:'Syne',sans-serif;
}

/* ── Base ── */
html,body,[class*="css"] {
    font-family:var(--mono)!important;
    background:var(--bg)!important;
    color:var(--text)!important;
}
.main .block-container {
    padding:0.5rem 1rem 1.5rem!important;
    max-width:100%!important;
}

/* ── SIDEBAR — forcer visible, empêcher collapse ── */
[data-testid="stSidebar"] {
    background:linear-gradient(175deg,#0d1117,#080b0f)!important;
    border-right:1px solid var(--border)!important;
    min-width:240px!important;
    max-width:240px!important;
}
/* Cacher TOUTES les flèches de collapse sidebar */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarNavCollapseIcon"],
[data-testid="collapsedControl"],
button[kind="headerNoPadding"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
.st-emotion-cache-zq5wmm,
.st-emotion-cache-1rtdyuf,
section[data-testid="stSidebar"] > div > div > div:first-child > div > button {
    display:none!important;
    visibility:hidden!important;
    opacity:0!important;
    pointer-events:none!important;
}
/* Forcer sidebar toujours ouverte */
[data-testid="stSidebar"][aria-expanded="false"] {
    display:flex!important;
    transform:translateX(0)!important;
    margin-left:0!important;
    left:0!important;
}
section[data-testid="stSidebar"] {
    display:flex!important;
    visibility:visible!important;
}

/* ── Masquer chrome Streamlit ── */
#MainMenu,footer,header { display:none!important; visibility:hidden!important; }
.stDeployButton { display:none!important; }

/* ── ANTI-FLASH graphes : transition douce ── */
.js-plotly-plot {
    border-radius:10px!important;
    overflow:hidden!important;
    transition:opacity 0.15s ease!important;
}
/* Éviter le blanc entre les reruns */
.element-container { transition:none!important; }
iframe { border:none!important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background:var(--glass)!important;
    border:1px solid var(--border)!important;
    border-radius:10px!important;
    padding:10px 14px!important;
    transition:border-color 0.2s!important;
}
[data-testid="metric-container"]:hover { border-color:var(--border-gold)!important; }
[data-testid="stMetricLabel"] {
    color:var(--text2)!important; font-size:.62rem!important;
    letter-spacing:.1em!important; text-transform:uppercase!important;
}
[data-testid="stMetricValue"] { font-size:1.15rem!important; font-weight:700!important; }
[data-testid="stMetricDelta"] { font-size:.68rem!important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background:var(--glass)!important; border-radius:8px!important;
    padding:3px!important; gap:3px!important; border:1px solid var(--border)!important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent!important; border-radius:6px!important;
    color:var(--text2)!important; font-size:.7rem!important;
    letter-spacing:.05em!important; padding:4px 12px!important;
}
.stTabs [aria-selected="true"] {
    background:rgba(247,181,41,0.12)!important; color:var(--gold)!important;
}
/* Cacher la flèche de navigation des tabs */
.stTabs [data-testid="stTabBar"] + div > button,
[data-testid="stTabScrollRight"],
[data-testid="stTabScrollLeft"] {
    display:none!important;
}

/* ── Radio buttons ── */
.stRadio > div { gap:4px!important; }
.stRadio label {
    background:var(--glass)!important; border:1px solid var(--border)!important;
    border-radius:6px!important; padding:3px 10px!important;
    font-size:.7rem!important; color:var(--text2)!important;
    cursor:pointer!important; transition:all .15s!important;
}
.stRadio label:hover { border-color:var(--border-gold)!important; color:var(--gold)!important; }

/* ── Select slider ── */
.stSlider, [data-testid="stSelectSlider"] { padding:0!important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }

/* ── Cards ── */
.card {
    background:var(--glass); border:1px solid var(--border);
    border-radius:10px; padding:12px 14px; margin-bottom:8px;
}

/* ── Badges ── */
.badge-buy  { display:inline-block; background:rgba(0,212,170,.15); border:1px solid rgba(0,212,170,.4); color:#00d4aa; border-radius:5px; padding:2px 9px; font-size:.66rem; font-weight:700; }
.badge-sell { display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:5px; padding:2px 9px; font-size:.66rem; font-weight:700; }
.badge-wait { display:inline-block; background:rgba(107,122,148,.1); border:1px solid rgba(107,122,148,.25); color:#6b7a94; border-radius:5px; padding:2px 9px; font-size:.66rem; font-weight:700; }
.badge-ant  { display:inline-block; background:rgba(167,139,250,.12); border:1px solid rgba(167,139,250,.4); color:#a78bfa; border-radius:5px; padding:2px 9px; font-size:.63rem; font-weight:700; }

/* ── Labels ── */
.lbl {
    font-size:.58rem; font-weight:600; letter-spacing:.12em;
    text-transform:uppercase; color:var(--text3); margin-bottom:4px;
}

/* ── Dots status ── */
.live-dot   { display:inline-block; width:6px; height:6px; background:var(--green);  border-radius:50%; box-shadow:0 0 6px var(--green);  animation:pulse 1.4s infinite; margin-right:5px; }
.offline-dot{ display:inline-block; width:6px; height:6px; background:var(--red);    border-radius:50%; margin-right:5px; }
.ws-dot     { display:inline-block; width:6px; height:6px; background:var(--purple); border-radius:50%; box-shadow:0 0 6px var(--purple); animation:pulse 1.2s infinite; margin-right:5px; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.5)} }

hr { border-color:var(--border)!important; margin:8px 0!important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES DESIGN
# ─────────────────────────────────────────────────────────────────────────────

C = {
    "bg":"#080b0f", "bg2":"#0d1117",
    "grid":"rgba(255,255,255,0.03)",
    "text":"#6b7a94", "text3":"#2e3a4e",
    "gold":"#f7b529", "dxy":"#4da6ff",
    "green":"#00d4aa", "red":"#ff4d6a", "purple":"#a78bfa",
}

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE — initialisation
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULTS = {
    "tick":          0,
    "ws_connected":  False,
    "ws_queue":      None,
    "ws_thread":     None,
    "ws_stop":       None,
    "tf":            "M5",
    "show_zones":    True,
    # Données marché
    "gold_price":    0.0,
    "dxy_price":     0.0,
    "gold_bid":      0.0,
    "gold_ask":      0.0,
    "gold_change":   0.0,
    "gold_pct":      0.0,
    "dxy_change":    0.0,
    "correlation":   -0.75,
    "corr_history":  [],
    "signal": {
        "direction":"WAIT","anticipation":None,"confidence":0,
        "corr":-0.75,"gold_price":0.0,"dxy_price":0.0,
        "entry":0.0,"tp":0.0,"sl":0.0,"rr":0.0,
        "sl_source":"—","pipeline_state":"IDLE",
    },
    "signals":       [],
    "bot_logs":      [{"time":"--:--","level":"INFO","msg":"En attente de connexion..."}],
    "mtf_analysis": {
        "H1": {"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None},
        "M15":{"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None},
        "M5": {"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None},
    },
    "ohlcv":        {"M5":[],"M15":[],"H1":[]},
    "zones": {
        "support":0.0,"resistance":0.0,
        "fvg_bullish":[],"fvg_bearish":[],
        "ob_buy":None,"ob_sell":None,
        "swing_lows":[],"swing_highs":[],"atr":0.0,"fvg_filter":0.0,
    },
    "winrate":       0.0,
    "wins":          0,
    "losses":        0,
    "bot_status":    "unknown",
    "mt5_connected": False,
    "gold_symbol":   "XAUUSD",
    "last_update":   "—",
    # Cache graphes — clé pour éviter le re-render inutile
    "_gold_candles_hash": "",
    "_dxy_candles_hash":  "",
}

for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
#  WEBSOCKET CLIENT THREAD
# ─────────────────────────────────────────────────────────────────────────────

def _ws_thread_fn(q: queue.Queue, stop: threading.Event):
    """Thread WS — reconnexion automatique avec backoff."""
    if not HAS_WS:
        q.put({"type":"_ws_status","connected":False,"error":"websocket-client non installé"})
        return
    delay = 2
    while not stop.is_set():
        try:
            ws = _websocket.create_connection(WS_URL, timeout=10)
            q.put({"type":"_ws_status","connected":True})
            delay = 2
            while not stop.is_set():
                try:
                    ws.settimeout(35)
                    raw = ws.recv()
                    q.put(json.loads(raw))
                except _websocket.WebSocketTimeoutException:
                    ws.send(json.dumps({"cmd":"ping"}))
                except Exception:
                    break
            try: ws.close()
            except: pass
        except Exception as e:
            q.put({"type":"_ws_status","connected":False,"error":str(e)})
        if not stop.is_set():
            time.sleep(delay)
            delay = min(delay * 1.5, 20)


def _start_ws():
    """Démarre le thread WS une seule fois par session."""
    ss = st.session_state
    if ss.ws_thread is not None and ss.ws_thread.is_alive():
        return
    q    = queue.Queue(maxsize=300)
    stop = threading.Event()
    t    = threading.Thread(target=_ws_thread_fn, args=(q, stop), daemon=True)
    t.start()
    ss.ws_queue  = q
    ss.ws_thread = t
    ss.ws_stop   = stop


_start_ws()

# ─────────────────────────────────────────────────────────────────────────────
#  TRAITEMENT MESSAGES WS → session_state
# ─────────────────────────────────────────────────────────────────────────────

def _apply_snapshot(d: Dict):
    ss = st.session_state
    for k in ["gold_price","dxy_price","gold_bid","gold_ask","gold_change",
              "gold_pct","dxy_change","correlation","corr_history","signal",
              "signals","bot_logs","mtf_analysis","zones","winrate","wins",
              "losses","bot_status","mt5_connected","gold_symbol","last_update"]:
        if k in d:
            setattr(ss, k, d[k]) if hasattr(ss, k) else None
            ss[k] = d[k]
    if "ohlcv" in d:
        for tf, candles in d["ohlcv"].items():
            if candles:
                ss.ohlcv[tf] = candles


def _process_ws():
    """Vide la queue WS et met à jour session_state."""
    ss = st.session_state
    q  = ss.ws_queue
    if q is None:
        return
    n = 0
    while not q.empty() and n < 40:
        try:
            msg = q.get_nowait()
        except queue.Empty:
            break
        n += 1
        t = msg.get("type","")

        if t == "_ws_status":
            ss.ws_connected = msg.get("connected", False)

        elif t == "snapshot":
            _apply_snapshot(msg)

        elif t == "price":
            ss.gold_price  = msg.get("gold",  ss.gold_price)
            ss.dxy_price   = msg.get("dxy",   ss.dxy_price)
            ss.gold_bid    = msg.get("gold_bid",  ss.gold_bid)
            ss.gold_ask    = msg.get("gold_ask",  ss.gold_ask)
            ss.gold_change = msg.get("gold_change", 0.0)
            ss.gold_pct    = msg.get("gold_pct",    0.0)
            ss.dxy_change  = msg.get("dxy_change",  0.0)
            ss.correlation = msg.get("corr", ss.correlation)
            ss.last_update = msg.get("ts","")

        elif t == "signal":
            ss.signal       = msg.get("signal", ss.signal)
            ss.mtf_analysis = msg.get("mtf",    ss.mtf_analysis)
            s = msg.get("stats",{})
            ss.winrate = s.get("winrate", ss.winrate)
            ss.wins    = s.get("wins",    ss.wins)
            ss.losses  = s.get("losses",  ss.losses)

        elif t == "ohlcv":
            tf      = msg.get("timeframe","M5")
            candles = msg.get("candles",[])
            if candles:
                ss.ohlcv[tf] = candles

        elif t == "zones":
            z = msg.get("zones",{})
            if z: ss.zones = z

        elif t == "logs":
            logs = msg.get("logs",[])
            if logs: ss.bot_logs = logs


# ─────────────────────────────────────────────────────────────────────────────
#  HTTP FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=2)
def _http_snap() -> Optional[Dict]:
    if not HAS_REQUESTS:
        return None
    try:
        r = _requests.get(f"{API_URL}/api/snapshot",
                           headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  SIMULATION (API totalement hors ligne)
# ─────────────────────────────────────────────────────────────────────────────

def _sim_prices():
    ss = st.session_state
    np.random.seed(int(time.time()) % 9999)
    if ss.gold_price == 0:
        ss.gold_price = 2320.0
        ss.dxy_price  = 104.5
    ss.gold_price  += np.random.normal(0, 0.15)
    ss.dxy_price   += np.random.normal(0, 0.008)
    ss.gold_change  = round(np.random.normal(0, 0.8),  2)
    ss.gold_pct     = round(np.random.normal(0, 0.04), 3)
    ss.dxy_change   = round(np.random.normal(0, 0.02), 4)
    ss.correlation  = max(-1, min(1, ss.correlation + np.random.normal(0, 0.01)))
    ss.gold_bid     = round(ss.gold_price - 0.15, 2)
    ss.gold_ask     = round(ss.gold_price + 0.15, 2)
    ss.bot_status   = "simulation"


def _sim_ohlcv(n: int, interval_min: int, sym: str) -> List[Dict]:
    np.random.seed(hash(sym) % 9999)
    base = 2320.0 if "XAU" in sym.upper() else 104.5
    vol  = 0.0006 if "XAU" in sym.upper() else 0.0003
    closes = [base]
    for _ in range(n-1):
        closes.append(closes[-1]*(1+np.random.normal(0,vol)))
    np.random.seed(int(time.time()*2) % 10000)
    closes[-1] *= (1+np.random.normal(0,vol*0.3))
    result, now = [], datetime.now()
    for i in range(n):
        t = now - timedelta(minutes=interval_min*(n-1-i))
        o = closes[i-1] if i>0 else closes[i]; c = closes[i]
        rng = abs(c-o)*(1+abs(np.random.normal(0,0.4)))
        h = max(o,c)+rng*0.35; l = min(o,c)-rng*0.35
        result.append({"time":t.isoformat(),"open":round(o,5),"high":round(h,5),
                        "low":round(max(l,0.1),5),"close":round(c,5),
                        "volume":int(np.random.exponential(2000))})
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  BUILDERS GRAPHES
# ─────────────────────────────────────────────────────────────────────────────

def _candles_to_df(candles: List[Dict]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df


def _add_zones_to_fig(fig, zones: Dict, row=1):
    sup = zones.get("support", 0)
    res = zones.get("resistance", 0)
    if sup:
        fig.add_hline(y=sup, row=row, col=1,
            line=dict(color="rgba(0,212,170,0.4)",width=1,dash="dot"),
            annotation_text="S", annotation_font=dict(color="#00d4aa",size=8))
    if res:
        fig.add_hline(y=res, row=row, col=1,
            line=dict(color="rgba(255,77,106,0.4)",width=1,dash="dot"),
            annotation_text="R", annotation_font=dict(color="#ff4d6a",size=8))
    for fvg in zones.get("fvg_bullish",[]):
        fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,
            fillcolor="rgba(0,212,170,0.07)",
            line=dict(color="rgba(0,212,170,0.18)",width=0.5))
    for fvg in zones.get("fvg_bearish",[]):
        fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,
            fillcolor="rgba(255,77,106,0.07)",
            line=dict(color="rgba(255,77,106,0.18)",width=0.5))
    ob_buy  = zones.get("ob_buy")
    ob_sell = zones.get("ob_sell")
    if ob_buy:
        fig.add_hline(y=ob_buy, row=row, col=1,
            line=dict(color="rgba(0,212,170,0.55)",width=1.2),
            annotation_text="OB↑", annotation_font=dict(color="#00d4aa",size=8))
    if ob_sell:
        fig.add_hline(y=ob_sell, row=row, col=1,
            line=dict(color="rgba(255,77,106,0.55)",width=1.2),
            annotation_text="OB↓", annotation_font=dict(color="#ff4d6a",size=8))


def build_chart(candles: List[Dict], symbol: str, color: str, tf: str,
                signal: Dict = None, zones: Dict = None,
                show_zones: bool = True) -> go.Figure:
    """Construit le graphique candlestick — appelé seulement si candles changent."""
    df = _candles_to_df(candles)

    # Figure vide si pas de données
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"], height=400,
            font=dict(color=C["text"]),
            margin=dict(l=0,r=10,t=30,b=0),
        )
        fig.add_annotation(text="⏳  En attente des données…",
            xref="paper",yref="paper",x=0.5,y=0.5,
            font=dict(color=C["text"],size=13),showarrow=False)
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         vertical_spacing=0.015, row_heights=[0.78,0.22])

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"],  close=df["close"], name=symbol,
        increasing=dict(line=dict(color=C["green"],width=1),fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],  width=1),fillcolor=C["red"]),
        whiskerwidth=0.2,
    ), row=1, col=1)

    # EMA 20 + 50
    ema20 = df["close"].ewm(span=20).mean()
    ema50 = df["close"].ewm(span=50).mean()
    fig.add_trace(go.Scatter(x=df["time"],y=ema20,name="EMA20",
        line=dict(color=color,width=1,dash="dot"),opacity=0.65), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=ema50,name="EMA50",
        line=dict(color="rgba(255,255,255,0.18)",width=0.8),opacity=0.5), row=1, col=1)

    # Zones
    if show_zones and zones:
        _add_zones_to_fig(fig, zones, row=1)

    # Prix courant
    last_p   = float(df["close"].iloc[-1])
    tf_label = {"M5":"5 Min","M15":"15 Min","H1":"1 Hour"}.get(tf, tf)
    fig.add_hline(y=last_p, row=1, col=1,
        line=dict(color=color,width=0.7,dash="dash"), opacity=0.4)
    fig.add_annotation(
        x=df["time"].iloc[-1], y=last_p,
        text=f"  {last_p:,.2f}",
        font=dict(color=color,size=10,family="JetBrains Mono"),
        showarrow=False, xanchor="left",
        bgcolor="rgba(8,11,15,0.9)",
        bordercolor=color, borderwidth=1, borderpad=3,
        row=1, col=1,
    )

    # Signal marker + TP/SL
    if signal and signal.get("direction") in ("BUY","SELL"):
        lt = df["time"].iloc[-1]
        if signal["direction"] == "BUY":
            fig.add_trace(go.Scatter(
                x=[lt], y=[last_p*0.9993], mode="markers+text",
                marker=dict(symbol="triangle-up",size=13,color=C["green"]),
                text=["▲ BUY"], textposition="bottom center",
                textfont=dict(color=C["green"],size=9),
                showlegend=False), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=[lt], y=[last_p*1.0007], mode="markers+text",
                marker=dict(symbol="triangle-down",size=13,color=C["red"]),
                text=["▼ SELL"], textposition="top center",
                textfont=dict(color=C["red"],size=9),
                showlegend=False), row=1, col=1)
        if signal.get("tp"):
            fig.add_hline(y=signal["tp"],row=1,col=1,
                line=dict(color=C["green"],width=0.7,dash="dash"),opacity=0.5)
        if signal.get("sl"):
            fig.add_hline(y=signal["sl"],row=1,col=1,
                line=dict(color=C["red"],  width=0.7,dash="dash"),opacity=0.5)

    # Volume
    vol_c = [C["green"] if c>=o else C["red"]
              for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df["time"],y=df["volume"],
        marker=dict(color=vol_c,opacity=0.4),
        showlegend=False), row=2, col=1)

    ax = dict(showgrid=True,gridcolor=C["grid"],gridwidth=1,
              zeroline=False,tickfont=dict(size=9,color=C["text"]),
              linecolor=C["grid"])
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        margin=dict(l=0,r=55,t=32,b=0), height=400,
        font=dict(family="JetBrains Mono",color=C["text"],size=9),
        legend=dict(orientation="h",x=0,y=1.06,
                    bgcolor="rgba(0,0,0,0)",font=dict(size=9)),
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        title=dict(
            text=(f'<b style="color:{color}">{symbol}</b>'
                  f'<span style="color:{C["text3"]};font-size:9px"> ● {tf_label}</span>'),
            x=0.01, font=dict(size=12,family="Syne"),
        ),
        dragmode="pan",
    )
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax, tickformat=".5g")
    return fig


def build_gauge(corr: float) -> go.Figure:
    col = C["green"] if corr<-0.5 else (C["red"] if corr>0.5 else C["gold"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=corr,
        number=dict(font=dict(size=28,color=col,family="JetBrains Mono")),
        gauge=dict(
            axis=dict(range=[-1,1],tickwidth=1,tickcolor=C["text"],
                      tickfont=dict(size=8),nticks=9),
            bar=dict(color=col,thickness=0.18),
            bgcolor=C["bg"], bordercolor=C["grid"], borderwidth=1,
            steps=[
                dict(range=[-1,-0.6],  color="rgba(0,212,170,0.1)"),
                dict(range=[-0.6,0.6], color="rgba(247,181,41,0.05)"),
                dict(range=[0.6,1],    color="rgba(255,77,106,0.1)"),
            ],
        ),
        title=dict(text="CORR GOLD/DXY",
                   font=dict(size=8,color=C["text"],family="JetBrains Mono")),
    ))
    fig.update_layout(paper_bgcolor=C["bg2"],height=155,
                      margin=dict(l=10,r=10,t=28,b=5))
    return fig


def build_corr_history(history: List[Dict]) -> go.Figure:
    if not history:
        return go.Figure()
    times = [h["time"] for h in history]
    corrs = [h["corr"]  for h in history]
    fig   = go.Figure()
    fig.add_trace(go.Scatter(x=times,y=corrs,
        line=dict(color=C["gold"],width=1.2),
        fill="tozeroy",fillcolor="rgba(247,181,41,0.05)"))
    for y,c in [(-0.6,C["green"]),(0,C["text"]),(0.6,C["red"])]:
        fig.add_hline(y=y,line=dict(color=c,width=0.6,dash="dash"),opacity=0.4)
    fig.update_layout(
        paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],
        height=155,margin=dict(l=0,r=10,t=8,b=0),
        font=dict(family="JetBrains Mono",color=C["text"],size=9),
        hovermode="x",showlegend=False,dragmode="pan",
        yaxis=dict(range=[-1.05,1.05],showgrid=True,gridcolor=C["grid"],
                   zeroline=False,tickfont=dict(size=8)),
        xaxis=dict(showgrid=False,tickfont=dict(size=8)),
    )
    return fig


def _pltly(fig, key="", small=False):
    """Rendu Plotly sans flash — config optimisée."""
    cfg = {
        "displaylogo": False,
        "scrollZoom":  not small,
        "displayModeBar": not small,
        "modeBarButtonsToRemove": ["lasso2d","select2d","autoScale2d"],
        # staticPlot=False garde l'interactivité mais réduit le flash
        "staticPlot": False,
    }
    try:
        st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)


# ─────────────────────────────────────────────────────────────────────────────
#  FETCH DONNÉES (appelé à chaque rerun)
# ─────────────────────────────────────────────────────────────────────────────

# 1. Messages WebSocket
_process_ws()

# 2. HTTP fallback si WS déconnecté
if not st.session_state.ws_connected:
    snap = _http_snap()
    if snap:
        _apply_snapshot(snap)
    else:
        _sim_prices()

st.session_state.tick += 1
ss = st.session_state   # alias

# OHLCV courant
tf      = ss.tf
tf_min  = {"M5":5,"M15":15,"H1":60}[tf]
gold_c  = ss.ohlcv.get(tf, [])
if not gold_c:
    gold_c = _sim_ohlcv(200, tf_min, "XAUUSD")
dxy_c = _sim_ohlcv(200, tf_min, "DXY")

signal = ss.signal
zones  = ss.zones
mtf    = ss.mtf_analysis

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR — TOUJOURS VISIBLE
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding:12px 0 14px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.1rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ⚡ GOLD / DXY PRO
        </div>
        <div style="font-size:.58rem;color:#2e3a4e;letter-spacing:.1em;
                    text-transform:uppercase;margin-top:2px;">
            Algo Trading Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Timeframe ──────────────────────────────────────────────────────────────
    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf_sel = st.radio("Timeframe", ["M5","M15","H1"],
                       horizontal=True, label_visibility="collapsed",
                       index=["M5","M15","H1"].index(ss.tf))
    if tf_sel != ss.tf:
        st.session_state.tf = tf_sel

    st.markdown("")

    # ── Zones ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="lbl">Zones Techniques</div>', unsafe_allow_html=True)
    show_zones = st.checkbox("S/R · FVG · Order Blocks", value=ss.show_zones)
    st.session_state.show_zones = show_zones

    st.markdown("")

    # ── FVG Filter ─────────────────────────────────────────────────────────────
    st.markdown('<div class="lbl">FVG Filter Strength</div>', unsafe_allow_html=True)
    fvg_str = st.select_slider(
        "FVG Strength",
        options=["Faible","Normal","Fort"],
        value="Normal",
        label_visibility="collapsed",
    )
    fvg_mult = {"Faible":0.15,"Normal":0.30,"Fort":0.50}[fvg_str]
    atr_val  = zones.get("atr", 0)
    n_fvg    = len(zones.get("fvg_bullish",[])) + len(zones.get("fvg_bearish",[]))
    st.markdown(f"""
    <div style="font-size:.58rem;color:#3d4a5e;margin-top:3px;line-height:1.8;">
        Seuil : ATR × {fvg_mult} = {round(atr_val*fvg_mult,3)}<br>
        FVG détectés : <b style="color:#dde3ee;">{n_fvg}</b>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Connexion Status ───────────────────────────────────────────────────────
    st.markdown('<div class="lbl">Connexion</div>', unsafe_allow_html=True)

    ws_ok  = ss.ws_connected
    mt5_ok = ss.mt5_connected
    api_ok = ws_ok or (ss.bot_status not in ("unknown","simulation"))

    ws_dot  = '<span class="ws-dot"></span>'    if ws_ok  else '<span class="offline-dot"></span>'
    mt5_dot = '<span class="live-dot"></span>'  if mt5_ok else '<span class="offline-dot"></span>'

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
                border-radius:8px;padding:9px 11px;">
        <div style="font-size:.68rem;margin-bottom:5px;
                    color:{'#a78bfa' if ws_ok else '#ff4d6a'};">
            {ws_dot}WebSocket {'Connecté' if ws_ok else 'Hors ligne'}
        </div>
        <div style="font-size:.68rem;margin-bottom:5px;
                    color:{'#00d4aa' if mt5_ok else '#f7b529'};">
            {mt5_dot}MT5 {'Live' if mt5_ok else 'Simulation'}
        </div>
        <div style="font-size:.62rem;color:#3d4a5e;margin-top:4px;line-height:1.7;">
            Endpoint:<br>
            <span style="color:#4b5a72;word-break:break-all;">{API_URL[:35] + ('…' if len(API_URL)>35 else '')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # ── Stats ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="lbl">Performance</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1: st.metric("Winrate", f"{ss.winrate}%")
    with sc2: st.metric("Trades",  f"{ss.wins}W/{ss.losses}L")

    st.markdown("---")

    # ── Info ───────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="font-size:.57rem;color:#2e3a4e;line-height:1.9;text-align:center;">
        {ss.gold_symbol or 'XAUUSD'} · Tick #{ss.tick}<br>
        {datetime.now().strftime('%H:%M:%S')} · {tf}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────

hc1, hc2, hc3 = st.columns([3,1.5,1])
with hc1:
    ws_label = "WebSocket Live" if ws_ok else "HTTP Mode"
    ws_col   = "#a78bfa" if ws_ok else "#f7b529"
    dot_h    = '<span class="ws-dot"></span>' if ws_ok else '<span class="offline-dot"></span>'
    mt5_label = "MT5 Live" if mt5_ok else "Simulation"
    st.markdown(f"""
    <div style="padding:5px 0 10px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:10px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.3rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            GOLD / DXY PRO
        </div>
        <div style="font-size:.6rem;color:#6b7a94;margin-top:2px;">
            {dot_h}<span style="color:{ws_col};">{ws_label}</span>
            &nbsp;·&nbsp;{mt5_label}&nbsp;·&nbsp;{tf}
        </div>
    </div>
    """, unsafe_allow_html=True)

with hc2:
    sig_dir  = signal.get("direction", "WAIT")
    ant      = signal.get("anticipation") or ""
    conf     = signal.get("confidence", 0)
    pipe     = signal.get("pipeline_state", "IDLE")
    bc       = {"BUY":"badge-buy","SELL":"badge-sell","WAIT":"badge-wait"}[sig_dir]
    ant_html = f'<span class="badge-ant">{ant}</span>' if ant else ""
    st.markdown(
        f'<div style="padding-top:6px;">' +
        f'<div class="lbl">Signal Actif</div>' +
        f'<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:4px;">' +
        f'<span class="{bc}">{sig_dir}</span>' + ant_html + '</div>' +
        f'<div style="font-size:.6rem;color:#6b7a94;margin-top:4px;">' +
        f'Conf: <b style="color:#dde3ee;">{conf}%</b> &nbsp;·&nbsp; {pipe}' +
        '</div></div>',
        unsafe_allow_html=True,
    )

with hc3:
    st.markdown(f"""
    <div style="text-align:right;padding-top:6px;">
        <div style="font-size:1rem;font-weight:700;color:#dde3ee;">
            {datetime.now().strftime('%H:%M:%S')}
        </div>
        <div style="font-size:.57rem;color:#2e3a4e;">{datetime.now().strftime('%a %d %b %Y')}</div>
        <div style="font-size:.55rem;color:#1e293b;margin-top:2px;">tick #{ss.tick}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  METRICS
# ─────────────────────────────────────────────────────────────────────────────

m = st.columns(7)
with m[0]: st.metric("XAUUSD", f"{ss.gold_price:,.2f}", f"{ss.gold_change:+.2f} ({ss.gold_pct:+.2f}%)")
with m[1]: st.metric("DXY",    f"{ss.dxy_price:.3f}",   f"{ss.dxy_change:+.4f}")
with m[2]:
    cl = "● Forte Neg" if ss.correlation<-0.6 else ("● Modérée" if ss.correlation<0 else "● Positive")
    st.metric("Corrélation", f"{ss.correlation:+.4f}", cl)
with m[3]:
    emo = {"BUY":"🟢","SELL":"🔴","WAIT":"⚪"}
    st.metric("Signal", f"{emo[sig_dir]} {sig_dir}", f"Conf:{signal.get('confidence',0)}%")
with m[4]: st.metric("Winrate", f"{ss.winrate}%", f"{ss.wins}W/{ss.losses}L")
with m[5]: st.metric("BID/ASK", f"{ss.gold_bid:.2f}", f"ASK {ss.gold_ask:.2f}")
with m[6]:
    rr = signal.get("rr",0); sl_s = signal.get("sl_source","—")
    st.metric("R/R", f"1:{rr}", f"SL:{sl_s}")

st.markdown("")

# ─────────────────────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Graphiques", "🎯 Signal & Zones", "🔀 Multi-TF", "📋 Logs", "📜 Historique"
])

# ══════════════════════════════════════════════════════════════
#  TAB 1 — GRAPHIQUES (clé stable = pas de flash)
# ══════════════════════════════════════════════════════════════
with tab1:
    gc1, gc2 = st.columns(2)

    with gc1:
        fig_gold = build_chart(gold_c, "XAUUSD", C["gold"], tf,
                                signal=signal, zones=zones,
                                show_zones=show_zones)
        # Clé STABLE (sans tick) → Plotly met à jour en place sans flash
        _pltly(fig_gold, key="chart_gold")

    with gc2:
        fig_dxy = build_chart(dxy_c, "DXY", C["dxy"], tf,
                               show_zones=False)
        _pltly(fig_dxy, key="chart_dxy")

    # Corrélation
    st.markdown('<div class="lbl" style="margin-top:4px;">Corrélation Rolling</div>',
                unsafe_allow_html=True)
    _pltly(build_corr_history(ss.corr_history), key="corr_hist", small=True)

# ══════════════════════════════════════════════════════════════
#  TAB 2 — SIGNAL & ZONES
# ══════════════════════════════════════════════════════════════
with tab2:
    sc1, sc2, sc3 = st.columns([1,1,1.3])

    with sc1:
        _pltly(build_gauge(ss.correlation), key="gauge", small=True)
        corr = ss.correlation
        if corr < -0.65:   ic,it = C["green"],"✅ Forte — signaux fiables"
        elif corr < -0.4:  ic,it = C["gold"], "⚠️ Modérée — attendre"
        else:              ic,it = C["red"],  "❌ Faible — éviter trades"
        st.markdown(f"""<div style="font-size:.67rem;color:{ic};background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.05);border-radius:7px;padding:8px 10px;">{it}</div>""",
            unsafe_allow_html=True)

    with sc2:
        direction   = signal.get("direction","WAIT")
        antici      = signal.get("anticipation") or ""
        bc2         = {"BUY":"badge-buy","SELL":"badge-sell","WAIT":"badge-wait"}[direction]
        antici_html = f'<span class="badge-ant">{antici}</span>' if antici else ""
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
                <span class="{bc2}" style="font-size:.78rem;padding:4px 13px;">{direction}</span>
                f'<span class="badge-ant">{antici}</span>' if antici else ""
            </div>
            <div style="font-size:.67rem;color:#6b7a94;line-height:2.1;">
                Confiance: <b style="color:#dde3ee;">{signal.get('confidence',0)}%</b><br>
                Corr: <b style="color:#dde3ee;">{signal.get('corr',0):+.4f}</b><br>
                Gold: <b style="color:#f7b529;">{signal.get('gold_price',0):,.2f}</b><br>
                DXY:  <b style="color:#4da6ff;">{signal.get('dxy_price',0):.3f}</b><br>
                Pipeline: <b style="color:#dde3ee;">{signal.get('pipeline_state','IDLE')}</b>
            </div>
        </div>""", unsafe_allow_html=True)

        if direction in ("BUY","SELL"):
            entry=signal.get("entry",0); tp=signal.get("tp",0)
            sl=signal.get("sl",0); rr=signal.get("rr",0)
            st.markdown(f"""
            <div class="card" style="border-color:rgba(247,181,41,0.2);">
                <div class="lbl" style="margin-bottom:8px;">Niveaux de Trading</div>
                <div style="font-size:.7rem;line-height:2.2;">
                    <span style="color:#6b7a94;">Entrée:</span><b style="color:#dde3ee;float:right;">{entry:,.2f}</b><br>
                    <span style="color:#00d4aa;">TP:</span><b style="color:#00d4aa;float:right;">{tp:,.2f}</b><br>
                    <span style="color:#ff4d6a;">SL:</span><b style="color:#ff4d6a;float:right;">{sl:,.2f}</b><br>
                    <span style="color:#6b7a94;">R/R:</span><b style="color:#f7b529;float:right;">1:{rr}</b><br>
                    <span style="color:#6b7a94;">Source SL:</span><b style="color:#a78bfa;float:right;">{signal.get('sl_source','—')}</b>
                </div>
            </div>""", unsafe_allow_html=True)

        if antici:
            st.markdown(f"""
            <div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.3);
                        border-radius:8px;padding:10px 12px;margin-top:6px;">
                <div style="font-size:.58rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:4px;">
                    MODE ANTICIPATION
                </div>
                <div style="font-size:.7rem;color:#c4b5fd;">{antici}</div>
                <div style="font-size:.61rem;color:#6b7a94;margin-top:4px;">
                    {"DXY↓ → anticiper BUY GOLD" if "BUY" in antici else "DXY↑ → anticiper SELL GOLD"}
                    <br>⏳ Attendre confirmation corrélation
                </div>
            </div>""", unsafe_allow_html=True)

    with sc3:
        st.markdown('<div class="lbl">Zones Techniques (M5)</div>', unsafe_allow_html=True)
        atr = zones.get("atr",0); fvg_f = zones.get("fvg_filter",0)
        st.markdown(f"""
        <div class="card">
            <div class="lbl" style="margin-bottom:8px;">Support / Résistance</div>
            <div style="font-size:.7rem;line-height:2.2;">
                <span style="color:#6b7a94;">Support:</span>
                <b style="color:#00d4aa;float:right;">{zones.get('support',0):,.2f}</b><br>
                <span style="color:#6b7a94;">Résistance:</span>
                <b style="color:#ff4d6a;float:right;">{zones.get('resistance',0):,.2f}</b><br>
                <span style="color:#6b7a94;">ATR:</span>
                <b style="color:#f7b529;float:right;">{atr:.3f}</b><br>
                <span style="color:#6b7a94;">FVG Filter:</span>
                <b style="color:#a78bfa;float:right;">{fvg_f:.3f}</b>
            </div>
        </div>
        <div class="card">
            <div class="lbl" style="margin-bottom:8px;">FVG & Order Blocks</div>
            <div style="font-size:.7rem;line-height:2.2;">
                <span style="color:#6b7a94;">FVG Bullish:</span>
                <b style="color:#00d4aa;float:right;">{len(zones.get('fvg_bullish',[]))} zones</b><br>
                <span style="color:#6b7a94;">FVG Bearish:</span>
                <b style="color:#ff4d6a;float:right;">{len(zones.get('fvg_bearish',[]))} zones</b><br>
                <span style="color:#6b7a94;">OB Buy:</span>
                <b style="color:#00d4aa;float:right;">{zones.get('ob_buy') or '—'}</b><br>
                <span style="color:#6b7a94;">OB Sell:</span>
                <b style="color:#ff4d6a;float:right;">{zones.get('ob_sell') or '—'}</b>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 3 — MULTI-TF
# ══════════════════════════════════════════════════════════════
with tab3:
    mc3 = st.columns(3)
    for col, tf_n in zip(mc3, ["H1","M15","M5"]):
        d       = mtf.get(tf_n,{})
        sig     = d.get("signal","WAIT")
        cr      = d.get("corr",0.0)
        tr      = d.get("trend","—")
        at      = d.get("anticipation") or ""
        bc3     = {"BUY":"badge-buy","SELL":"badge-sell","WAIT":"badge-wait"}.get(sig,"badge-wait")
        at_html = f'<br><span style="color:#a78bfa;">{at}</span>' if at else ""
        cc  = C["green"] if cr<-0.6 else (C["gold"] if cr<0 else C["red"])
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;
                            color:#dde3ee;margin-bottom:8px;">{tf_n}</div>
                <div style="margin-bottom:8px;"><span class="{bc3}">{sig}</span></div>
                <div style="font-size:.67rem;color:#6b7a94;line-height:2.0;text-align:left;">
                    Corr: <b style="color:{cc};float:right;">{cr:+.4f}</b><br>
                    Trend: <b style="color:#dde3ee;float:right;">{tr}</b>
                    {at_html}
                </div>
            </div>""", unsafe_allow_html=True)

    sigs  = [mtf.get(t,{}).get("signal","WAIT") for t in ["H1","M15","M5"]]
    buys  = sigs.count("BUY"); sells = sigs.count("SELL")
    if buys>=2:   cons,cc2 = "🟢 CONSENSUS BUY — Setup favorable",  C["green"]
    elif sells>=2: cons,cc2 = "🔴 CONSENSUS SELL — Setup favorable", C["red"]
    else:          cons,cc2 = "⚪ PAS DE CONSENSUS — Attendre",       C["gold"]
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
                border-radius:10px;padding:14px;text-align:center;margin-top:10px;">
        <div style="font-size:.72rem;color:{cc2};font-weight:700;">{cons}</div>
        <div style="font-size:.6rem;color:#2e3a4e;margin-top:4px;">
            H1:{sigs[0]} · M15:{sigs[1]} · M5:{sigs[2]}
        </div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 4 — LOGS
# ══════════════════════════════════════════════════════════════
with tab4:
    lc1, lc2 = st.columns([3,1])
    with lc1:
        st.markdown('<div class="lbl">Logs Temps Réel</div>', unsafe_allow_html=True)
    with lc2:
        lf = st.selectbox("Filtre logs", ["ALL","SIGNAL","WARNING","ERROR"],
                           label_visibility="collapsed")

    logs = ss.bot_logs
    filtered = [l for l in reversed(logs) if lf=="ALL" or l.get("level")==lf]
    html  = '<div style="background:#0d1117;border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:12px;height:310px;overflow-y:auto;font-size:.63rem;line-height:1.9;">'
    for e in filtered[:80]:
        lvl = e.get("level","INFO").upper()
        col = {"INFO":"#6b7a94","WARNING":"#f7b529","ERROR":"#ff4d6a","SIGNAL":"#00d4aa"}.get(lvl,"#6b7a94")
        html += (f'<div><span style="color:#2e3a4e;">{e.get("time","")}</span>'
                 f' <span style="color:{col};font-weight:600;">[{lvl}]</span>'
                 f' <span style="color:#9ca3af;">{e.get("msg","")}</span></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    bs  = {"running":("🟢",C["green"],"Bot actif"),
           "simulation":("🟡",C["gold"],"Simulation"),
           "starting":("🔵",C["blue"] if "blue" in C else "#4da6ff","Démarrage")}
    em,sc,sl = bs.get(ss.bot_status,("⚪",C["text"],"Inconnu"))
    st.markdown(f"""<div style="margin-top:8px;font-size:.67rem;color:{sc};">
        {em} {sl} · MT5:{'✅' if mt5_ok else '⚠️'} · WS:{'🟣' if ws_ok else '🔴'}
        · Màj:{str(ss.last_update)[:19] if ss.last_update and ss.last_update!='—' else '—'}
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 5 — HISTORIQUE
# ══════════════════════════════════════════════════════════════
with tab5:
    h1,h2,h3,h4 = st.columns(4)
    with h1: st.metric("Total",     len(ss.signals))
    with h2: st.metric("Winrate",   f"{ss.winrate}%")
    with h3: st.metric("Victoires", ss.wins)
    with h4: st.metric("Défaites",  ss.losses)
    st.markdown("")

    if ss.signals:
        df_s  = pd.DataFrame(ss.signals[::-1][-50:])
        cols  = [c for c in ["time","direction","tf","entry","tp","sl","rr","sl_source","result"]
                 if c in df_s.columns]
        def _sty(val):
            m = {"BUY":"color:#00d4aa;font-weight:700","SELL":"color:#ff4d6a;font-weight:700",
                 "WIN":"color:#00d4aa","LOSS":"color:#ff4d6a"}
            return m.get(str(val),"color:#6b7a94")
        try:
            sub   = [c for c in ["direction","result"] if c in cols]
            styled = df_s[cols].style.map(_sty, subset=sub)
            try:    st.dataframe(styled, width="stretch", height=290)
            except: st.dataframe(styled, use_container_width=True, height=290)
        except:
            try:    st.dataframe(df_s[cols], width="stretch", height=290)
            except: st.dataframe(df_s[cols], use_container_width=True, height=290)
    else:
        st.markdown("""<div style="text-align:center;padding:40px;color:#2e3a4e;font-size:.75rem;">
            Aucun signal enregistré. Lance le bot + api_server.py.
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="text-align:center;padding:6px 0 2px;font-size:.52rem;color:#1e293b;
            border-top:1px solid rgba(255,255,255,0.04);margin-top:6px;">
    Gold/DXY Pro v3.1 · {'🟣 WebSocket' if ws_ok else '🟡 HTTP'} · Tick #{ss.tick} · {API_URL[:40]}
</div>
""", unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
# REFRESH_S à 1.5s → suffisamment lent pour que Plotly mette à jour
# en place sans recréer le DOM (= zéro flash)
time.sleep(REFRESH_S)
st.rerun()
