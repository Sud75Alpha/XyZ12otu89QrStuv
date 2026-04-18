"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        GOLD/DXY PRO DASHBOARD v3 — WebSocket Temps Réel                    ║
║                                                                              ║
║  Architecture : WebSocket principal + HTTP fallback                         ║
║  Technique    : st.empty() containers + update ciblé sans rerun global     ║
║  Lancement    : streamlit run dashboard.py                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os, time, json, threading, queue
import requests, websocket          # pip install websocket-client
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

try:
    API_URL = st.secrets["API_URL"]
    API_KEY = st.secrets["API_KEY"]
except Exception:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "gold_dxy_secret_2024")

# URL WebSocket dérivée de l'URL HTTP
WS_URL = API_URL.replace("https://", "wss://").replace("http://", "ws://")
WS_URL = f"{WS_URL}/ws?api_key={API_KEY}"

HTTP_HEADERS  = {"X-API-Key": API_KEY}
HTTP_TIMEOUT  = 4
UI_REFRESH_S  = 0.8   # Streamlit rerun (pour mettre à jour les containers)

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GOLD/DXY Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
#
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    display: block !important;
    width: 300px !important;
}

section[data-testid="stSidebar"] > div {
    display: block !important;
}
</style>
""", unsafe_allow_html=True)
with st.sidebar:
    st.title("⚙️ Settings")
    st.write("Timeframe")
    tf = st.selectbox("Choisir TF", ["M5", "M15", "H1"])
# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');
:root {
    --bg:#080b0f; --bg2:#0d1117; --bg3:#111820;
    --glass:rgba(255,255,255,0.025); --glass2:rgba(255,255,255,0.05);
    --border:rgba(255,255,255,0.055); --border-gold:rgba(247,181,41,0.3);
    --gold:#f7b529; --gold2:#ffd166; --green:#00d4aa; --red:#ff4d6a;
    --blue:#4da6ff; --purple:#a78bfa;
    --text:#dde3ee; --text2:#6b7a94; --text3:#2e3a4e;
    --mono:'JetBrains Mono',monospace; --display:'Syne',sans-serif;
}
html,body,[class*="css"] { font-family:var(--mono)!important; background:var(--bg)!important; color:var(--text)!important; }
.main .block-container { padding:0.6rem 1.2rem 1.5rem!important; max-width:100%!important; }
#MainMenu,footer,header,.stDeployButton { visibility:hidden!important; display:none!important; }
[data-testid="stSidebar"] { background:linear-gradient(175deg,#0c1018,#080b0f)!important; border-right:1px solid var(--border)!important; }
[data-testid="metric-container"] { background:var(--glass)!important; border:1px solid var(--border)!important; border-radius:10px!important; padding:10px 14px!important; }
[data-testid="metric-container"]:hover { border-color:var(--border-gold)!important; }
[data-testid="stMetricLabel"] { color:var(--text2)!important; font-size:.62rem!important; letter-spacing:.1em!important; text-transform:uppercase!important; }
[data-testid="stMetricValue"] { font-size:1.2rem!important; font-weight:700!important; }
[data-testid="stMetricDelta"] { font-size:.7rem!important; }
.stTabs [data-baseweb="tab-list"] { background:var(--glass)!important; border-radius:8px!important; padding:4px!important; gap:4px!important; border:1px solid var(--border)!important; }
.stTabs [data-baseweb="tab"] { background:transparent!important; border-radius:6px!important; color:var(--text2)!important; font-size:.72rem!important; letter-spacing:.06em!important; padding:5px 14px!important; }
.stTabs [aria-selected="true"] { background:rgba(247,181,41,0.12)!important; color:var(--gold)!important; }
.stRadio > div { gap:5px!important; }
.stRadio label { background:var(--glass)!important; border:1px solid var(--border)!important; border-radius:6px!important; padding:3px 11px!important; font-size:.72rem!important; color:var(--text2)!important; cursor:pointer!important; transition:all .15s!important; }
.stRadio label:hover { border-color:var(--border-gold)!important; color:var(--gold)!important; }
.stButton > button { background:rgba(247,181,41,0.08)!important; border:1px solid var(--border-gold)!important; color:var(--gold)!important; font-family:var(--mono)!important; font-size:.72rem!important; border-radius:6px!important; }
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }
.js-plotly-plot { border-radius:10px!important; overflow:hidden!important; }
.card { background:var(--glass); border:1px solid var(--border); border-radius:10px; padding:14px 16px; margin-bottom:10px; }
.badge-buy  { display:inline-block; background:rgba(0,212,170,.15); border:1px solid rgba(0,212,170,.4); color:#00d4aa; border-radius:5px; padding:2px 10px; font-size:.68rem; font-weight:700; }
.badge-sell { display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:5px; padding:2px 10px; font-size:.68rem; font-weight:700; }
.badge-wait { display:inline-block; background:rgba(107,122,148,.1); border:1px solid rgba(107,122,148,.25); color:#6b7a94; border-radius:5px; padding:2px 10px; font-size:.68rem; font-weight:700; }
.badge-ant  { display:inline-block; background:rgba(167,139,250,.12); border:1px solid rgba(167,139,250,.4); color:#a78bfa; border-radius:5px; padding:2px 10px; font-size:.65rem; font-weight:700; }
.lbl { font-size:.6rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--text3); margin-bottom:5px; }
.live-dot { display:inline-block; width:6px; height:6px; background:var(--green); border-radius:50%; box-shadow:0 0 7px var(--green); animation:pulse 1.4s infinite; margin-right:5px; }
.offline-dot { display:inline-block; width:6px; height:6px; background:var(--red); border-radius:50%; margin-right:5px; }
.ws-dot { display:inline-block; width:6px; height:6px; background:#a78bfa; border-radius:50%; box-shadow:0 0 7px #a78bfa; animation:pulse 1s infinite; margin-right:5px; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.4)} }
hr { border-color:rgba(255,255,255,0.055)!important; margin:8px 0!important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  DESIGN CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

C = {
    "bg": "#080b0f", "bg2": "#0d1117",
    "grid": "rgba(255,255,255,0.035)",
    "text": "#6b7a94", "text3": "#2e3a4e",
    "gold": "#f7b529", "dxy": "#4da6ff",
    "green": "#00d4aa", "red": "#ff4d6a", "purple": "#a78bfa",
}

# ─────────────────────────────────────────────────────────────────────────────
#  WEBSOCKET CLIENT — tourne dans un thread séparé
# ─────────────────────────────────────────────────────────────────────────────

def _ws_thread(data_queue: queue.Queue, stop_event: threading.Event):
    """
    Thread WebSocket :
    - Se connecte à l'API server
    - Met chaque message reçu dans data_queue
    - Se reconnecte automatiquement en cas de déconnexion
    """
    retry_delay = 2

    while not stop_event.is_set():
        try:
            ws = websocket.create_connection(WS_URL, timeout=10)
            data_queue.put({"type": "_ws_status", "connected": True})
            retry_delay = 2  # reset backoff

            while not stop_event.is_set():
                try:
                    ws.settimeout(35)
                    raw = ws.recv()
                    msg = json.loads(raw)
                    data_queue.put(msg)
                    # Répondre aux pings serveur
                    if msg.get("type") == "ping":
                        ws.send(json.dumps({"cmd": "ping"}))
                except websocket.WebSocketTimeoutException:
                    ws.send(json.dumps({"cmd": "ping"}))
                except Exception:
                    break

            ws.close()
        except Exception as e:
            data_queue.put({"type": "_ws_status", "connected": False, "error": str(e)})

        if not stop_event.is_set():
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 30)


# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE — structure centrale de données
# ─────────────────────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "tick":         0,
        "ws_connected": False,
        "ws_queue":     None,      # queue.Queue pour messages WS
        "ws_thread":    None,      # thread WS
        "ws_stop":      None,      # threading.Event
        "tf":           "M5",
        "show_zones":   True,
        # Données live
        "gold_price":   0.0,
        "dxy_price":    0.0,
        "gold_bid":     0.0,
        "gold_ask":     0.0,
        "gold_change":  0.0,
        "gold_pct":     0.0,
        "dxy_change":   0.0,
        "correlation":  -0.75,
        "corr_history": [],
        "signal":       {"direction":"WAIT","anticipation":None,"confidence":0,
                          "corr":-0.75,"gold_price":0.0,"dxy_price":0.0,
                          "entry":0.0,"tp":0.0,"sl":0.0,"rr":0.0,
                          "sl_source":"—","pipeline_state":"IDLE"},
        "signals":      [],
        "bot_logs":     [],
        "mtf_analysis": {"H1":{"signal":"WAIT","corr":0.0,"trend":"—"},
                          "M15":{"signal":"WAIT","corr":0.0,"trend":"—"},
                          "M5":{"signal":"WAIT","corr":0.0,"trend":"—"}},
        "ohlcv":        {"M5":[],"M15":[],"H1":[]},
        "zones":        {"support":0.0,"resistance":0.0,"fvg_bullish":[],
                          "fvg_bearish":[],"ob_buy":None,"ob_sell":None,
                          "swing_lows":[],"swing_highs":[],"atr":0.0},
        "winrate":      0.0,
        "wins":         0,
        "losses":       0,
        "bot_status":   "unknown",
        "mt5_connected":False,
        "gold_symbol":  "XAUUSD",
        "last_update":  "—",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ─────────────────────────────────────────────────────────────────────────────
#  DÉMARRAGE THREAD WS (une seule fois par session)
# ─────────────────────────────────────────────────────────────────────────────

def _start_ws():
    if st.session_state.ws_thread is not None and st.session_state.ws_thread.is_alive():
        return
    q     = queue.Queue(maxsize=200)
    stop  = threading.Event()
    t     = threading.Thread(target=_ws_thread, args=(q, stop), daemon=True)
    t.start()
    st.session_state.ws_queue  = q
    st.session_state.ws_thread = t
    st.session_state.ws_stop   = stop


_start_ws()

# ─────────────────────────────────────────────────────────────────────────────
#  TRAITEMENT DES MESSAGES WS → session_state
# ─────────────────────────────────────────────────────────────────────────────

def _process_ws_messages():
    """Vide la queue WS et met à jour session_state. Appelé à chaque rerun."""
    q = st.session_state.ws_queue
    if q is None:
        return

    processed = 0
    while not q.empty() and processed < 50:
        try:
            msg = q.get_nowait()
        except queue.Empty:
            break
        processed += 1
        t = msg.get("type", "")

        if t == "_ws_status":
            st.session_state.ws_connected = msg.get("connected", False)

        elif t == "snapshot":
            # Snapshot initial complet
            _apply_snapshot(msg)

        elif t == "price":
            # Mise à jour prix seulement
            st.session_state.gold_price  = msg.get("gold",  st.session_state.gold_price)
            st.session_state.dxy_price   = msg.get("dxy",   st.session_state.dxy_price)
            st.session_state.gold_bid    = msg.get("gold_bid", st.session_state.gold_bid)
            st.session_state.gold_ask    = msg.get("gold_ask", st.session_state.gold_ask)
            st.session_state.gold_change = msg.get("gold_change", 0.0)
            st.session_state.gold_pct    = msg.get("gold_pct",   0.0)
            st.session_state.dxy_change  = msg.get("dxy_change",  0.0)
            st.session_state.correlation = msg.get("corr", st.session_state.correlation)
            st.session_state.last_update = msg.get("ts", "")

        elif t == "signal":
            st.session_state.signal       = msg.get("signal", st.session_state.signal)
            st.session_state.mtf_analysis = msg.get("mtf",    st.session_state.mtf_analysis)
            stats = msg.get("stats", {})
            st.session_state.winrate  = stats.get("winrate", st.session_state.winrate)
            st.session_state.wins     = stats.get("wins",    st.session_state.wins)
            st.session_state.losses   = stats.get("losses",  st.session_state.losses)

        elif t == "ohlcv":
            tf = msg.get("timeframe", "M5")
            candles = msg.get("candles", [])
            if candles:
                st.session_state.ohlcv[tf] = candles

        elif t == "zones":
            z = msg.get("zones", {})
            if z:
                st.session_state.zones = z

        elif t == "logs":
            logs = msg.get("logs", [])
            if logs:
                st.session_state.bot_logs = logs


def _apply_snapshot(snap: Dict):
    """Applique un snapshot complet au session_state."""
    mapping = {
        "gold_price": "gold_price", "dxy_price": "dxy_price",
        "gold_bid": "gold_bid",     "gold_ask": "gold_ask",
        "gold_change": "gold_change","gold_pct": "gold_pct",
        "dxy_change": "dxy_change", "correlation": "correlation",
        "corr_history": "corr_history", "signal": "signal",
        "signals": "signals", "bot_logs": "bot_logs",
        "mtf_analysis": "mtf_analysis", "zones": "zones",
        "winrate": "winrate", "wins": "wins", "losses": "losses",
        "bot_status": "bot_status", "mt5_connected": "mt5_connected",
        "gold_symbol": "gold_symbol", "last_update": "last_update",
    }
    for src, dst in mapping.items():
        if src in snap:
            st.session_state[dst] = snap[src]
    if "ohlcv" in snap:
        for tf, candles in snap["ohlcv"].items():
            if candles:
                st.session_state.ohlcv[tf] = candles


# ─────────────────────────────────────────────────────────────────────────────
#  HTTP FALLBACK (si WS non connecté)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=2)
def _http_snapshot() -> Optional[Dict]:
    try:
        r = requests.get(f"{API_URL}/api/snapshot",
                          headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def _simulate_data():
    """Données simulées si API complètement indisponible."""
    np.random.seed(int(time.time()) % 9999)
    g = 2320.0 + np.random.normal(0, 1.5)
    d = 104.5  + np.random.normal(0, 0.04)
    st.session_state.gold_price  = round(g, 2)
    st.session_state.dxy_price   = round(d, 3)
    st.session_state.gold_bid    = round(g - 0.15, 2)
    st.session_state.gold_ask    = round(g + 0.15, 2)
    st.session_state.gold_change = round(np.random.normal(0, 0.8), 2)
    st.session_state.gold_pct    = round(np.random.normal(0, 0.04), 3)
    st.session_state.dxy_change  = round(np.random.normal(0, 0.02), 4)
    st.session_state.correlation = round(-0.72 + np.random.normal(0, 0.02), 4)
    st.session_state.bot_status  = "simulation"


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS OHLCV
# ─────────────────────────────────────────────────────────────────────────────

def _candles_to_df(candles: List[Dict]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df


def _simulate_ohlcv(n: int, interval_min: int, sym: str) -> List[Dict]:
    np.random.seed(hash(sym) % 9999)
    base = 2320.0 if "XAU" in sym.upper() else 104.5
    vol  = 0.0006 if "XAU" in sym.upper() else 0.0003
    closes = [base]
    for _ in range(n-1):
        closes.append(closes[-1] * (1 + np.random.normal(0, vol)))
    np.random.seed(int(time.time()*2) % 10000)
    closes[-1] *= (1 + np.random.normal(0, vol*0.3))
    result = []
    now = datetime.now()
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
#  CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _add_zones(fig, df: pd.DataFrame, zones: Dict, row=1):
    """Dessine S/R, FVG filtré, OB sur le graphique."""
    if df.empty:
        return

    sup = zones.get("support", 0)
    res = zones.get("resistance", 0)

    if sup:
        fig.add_hline(y=sup, row=row, col=1,
            line=dict(color="rgba(0,212,170,0.45)", width=1, dash="dot"),
            annotation_text="S", annotation_font=dict(color="#00d4aa", size=8))
    if res:
        fig.add_hline(y=res, row=row, col=1,
            line=dict(color="rgba(255,77,106,0.45)", width=1, dash="dot"),
            annotation_text="R", annotation_font=dict(color="#ff4d6a", size=8))

    # FVG Bullish
    for fvg in zones.get("fvg_bullish", []):
        fig.add_hrect(y0=fvg["low"], y1=fvg["high"],
            fillcolor="rgba(0,212,170,0.07)",
            line=dict(color="rgba(0,212,170,0.2)", width=0.5), row=row, col=1)

    # FVG Bearish
    for fvg in zones.get("fvg_bearish", []):
        fig.add_hrect(y0=fvg["low"], y1=fvg["high"],
            fillcolor="rgba(255,77,106,0.07)",
            line=dict(color="rgba(255,77,106,0.2)", width=0.5), row=row, col=1)

    # Order Blocks
    ob_buy  = zones.get("ob_buy")
    ob_sell = zones.get("ob_sell")
    if ob_buy:
        fig.add_hline(y=ob_buy, row=row, col=1,
            line=dict(color="rgba(0,212,170,0.6)", width=1.2),
            annotation_text="OB BUY", annotation_font=dict(color="#00d4aa", size=8))
    if ob_sell:
        fig.add_hline(y=ob_sell, row=row, col=1,
            line=dict(color="rgba(255,77,106,0.6)", width=1.2),
            annotation_text="OB SELL", annotation_font=dict(color="#ff4d6a", size=8))


def make_chart(candles: List[Dict], symbol: str, color: str, tf: str,
               signal: Dict = None, zones: Dict = None,
               show_zones: bool = True) -> go.Figure:
    """Construit le graphique candlestick complet."""
    df = _candles_to_df(candles)

    if df.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
                          height=420, font=dict(color=C["text"]))
        fig.add_annotation(text="Connexion en cours…", xref="paper", yref="paper",
                            x=0.5, y=0.5, font=dict(color=C["text"], size=14), showarrow=False)
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         vertical_spacing=0.015, row_heights=[0.78, 0.22])

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=symbol,
        increasing=dict(line=dict(color=C["green"], width=1.1), fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],   width=1.1), fillcolor=C["red"]),
        whiskerwidth=0.2,
    ), row=1, col=1)

    # EMAs
    ema20 = df["close"].ewm(span=20).mean()
    ema50 = df["close"].ewm(span=50).mean()
    fig.add_trace(go.Scatter(x=df["time"], y=ema20, name="EMA20",
        line=dict(color=color, width=1.1, dash="dot"), opacity=0.7), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=ema50, name="EMA50",
        line=dict(color="rgba(255,255,255,0.18)", width=0.9), opacity=0.5), row=1, col=1)

    # Zones techniques
    if show_zones and zones:
        _add_zones(fig, df, zones, row=1)

    # Prix courant
    last_p = float(df["close"].iloc[-1])
    fig.add_hline(y=last_p, row=1, col=1,
        line=dict(color=color, width=0.7, dash="dash"), opacity=0.4)
    tf_lbl = {"M5":"5 Min","M15":"15 Min","H1":"1 Hour"}.get(tf, tf)
    fig.add_annotation(
        x=df["time"].iloc[-1], y=last_p,
        text=f"  {last_p:,.2f}",
        font=dict(color=color, size=10.5, family="JetBrains Mono"),
        showarrow=False, xanchor="left",
        bgcolor="rgba(8,11,15,0.85)", bordercolor=color, borderwidth=1, borderpad=3,
        row=1, col=1,
    )

    # Signal markers + TP/SL
    if signal and signal.get("direction") in ("BUY", "SELL"):
        last_t = df["time"].iloc[-1]
        if signal["direction"] == "BUY":
            fig.add_trace(go.Scatter(
                x=[last_t], y=[last_p*0.9992], mode="markers+text",
                marker=dict(symbol="triangle-up", size=14, color=C["green"]),
                text=["▲ BUY"], textposition="bottom center",
                textfont=dict(color=C["green"], size=9),
                name="Signal", showlegend=False), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=[last_t], y=[last_p*1.0008], mode="markers+text",
                marker=dict(symbol="triangle-down", size=14, color=C["red"]),
                text=["▼ SELL"], textposition="top center",
                textfont=dict(color=C["red"], size=9),
                name="Signal", showlegend=False), row=1, col=1)
        if signal.get("tp"):
            fig.add_hline(y=signal["tp"], row=1, col=1,
                line=dict(color=C["green"], width=0.8, dash="dash"), opacity=0.5)
        if signal.get("sl"):
            fig.add_hline(y=signal["sl"], row=1, col=1,
                line=dict(color=C["red"], width=0.8, dash="dash"), opacity=0.5)

    # Volume
    vol_colors = [C["green"] if c>=o else C["red"]
                  for c,o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(x=df["time"], y=df["volume"],
        marker=dict(color=vol_colors, opacity=0.45),
        showlegend=False, name="Volume"), row=2, col=1)

    ax = dict(showgrid=True, gridcolor=C["grid"], gridwidth=1,
              zeroline=False, tickfont=dict(size=9,color=C["text"]), linecolor=C["grid"])
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        margin=dict(l=0, r=58, t=34, b=0), height=420,
        font=dict(family="JetBrains Mono", color=C["text"], size=9),
        legend=dict(orientation="h", x=0, y=1.05,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
        hovermode="x unified", xaxis_rangeslider_visible=False,
        title=dict(
            text=f'<b style="color:{color}">{symbol}</b>'
                 f'<span style="color:{C["text3"]};font-size:9px"> ● {tf_lbl}</span>',
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
        mode="gauge+number", value=corr,
        number=dict(font=dict(size=30, color=color, family="JetBrains Mono")),
        gauge=dict(
            axis=dict(range=[-1,1], tickwidth=1, tickcolor=C["text"],
                      tickfont=dict(size=8), nticks=9),
            bar=dict(color=color, thickness=0.2),
            bgcolor=C["bg"], bordercolor=C["grid"], borderwidth=1,
            steps=[
                dict(range=[-1,-0.6],  color="rgba(0,212,170,0.1)"),
                dict(range=[-0.6,0.6], color="rgba(247,181,41,0.05)"),
                dict(range=[0.6,1],    color="rgba(255,77,106,0.1)"),
            ],
            threshold=dict(line=dict(color=color, width=2), value=corr),
        ),
        title=dict(text="CORR GOLD/DXY",
                   font=dict(size=8, color=C["text"], family="JetBrains Mono")),
    ))
    fig.update_layout(paper_bgcolor=C["bg2"], height=160,
                      margin=dict(l=10,r=10,t=28,b=5), font=dict(color=C["text"]))
    return fig


def make_corr_history(history: List[Dict]) -> go.Figure:
    if not history:
        return go.Figure()
    times = [h["time"] for h in history]
    corrs = [h["corr"]  for h in history]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=corrs, name="Corr",
        line=dict(color=C["gold"], width=1.3),
        fill="tozeroy", fillcolor="rgba(247,181,41,0.05)"))
    for y, col in [(-0.6,C["green"]),(0,C["text"]),(0.6,C["red"])]:
        fig.add_hline(y=y, line=dict(color=col, width=0.7, dash="dash"), opacity=0.4)
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        height=160, margin=dict(l=0,r=10,t=10,b=0),
        font=dict(family="JetBrains Mono", color=C["text"], size=9),
        hovermode="x", showlegend=False, dragmode="pan",
        yaxis=dict(range=[-1.05,1.05], showgrid=True, gridcolor=C["grid"],
                   zeroline=False, tickfont=dict(size=8)),
        xaxis=dict(showgrid=False, tickfont=dict(size=8)),
    )
    return fig


def _render_plotly(fig, key=""):
    cfg = {"scrollZoom":True,"displaylogo":False,
           "modeBarButtonsToRemove":["lasso2d","select2d","autoScale2d"],
           "displayModeBar":True}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)


def _render_plotly_sm(fig, key=""):
    cfg = {"displayModeBar":False,"displaylogo":False}
    try:
        st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)


# ─────────────────────────────────────────────────────────────────────────────
#  TRAITEMENT DES DONNÉES (appel à chaque rerun)
# ─────────────────────────────────────────────────────────────────────────────

# 1. Vider la queue WS → mettre à jour session_state
_process_ws_messages()

# 2. Si WS non connecté → fallback HTTP ou simulation
if not st.session_state.ws_connected:
    snap = _http_snapshot()
    if snap:
        _apply_snapshot(snap)
    else:
        _simulate_data()

st.session_state.tick += 1

# Raccourcis locaux
S = st.session_state   # alias court
tf = S.tf

# OHLCV courant
tf_min = {"M5":5,"M15":15,"H1":60}[tf]
gold_candles = S.ohlcv.get(tf, [])
if not gold_candles:
    gold_candles = _simulate_ohlcv(200, tf_min, "XAUUSD")
dxy_candles = _simulate_ohlcv(200, tf_min, "DXY")

signal  = S.signal
zones   = S.zones
mtf     = S.mtf_analysis

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding:10px 0 16px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.1rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ⚡ GOLD/DXY PRO
        </div>
        <div style="font-size:.6rem;color:#2e3a4e;letter-spacing:.1em;text-transform:uppercase;margin-top:2px;">
            Algo Trading · WebSocket
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf_sel = st.radio("TF", ["M5","M15","H1"], horizontal=True,
                      label_visibility="collapsed",
                      index=["M5","M15","H1"].index(S.tf))
    if tf_sel != S.tf:
        st.session_state.tf = tf_sel
        if S.ws_queue:
            # Demander l'OHLCV du nouveau TF via WS
            pass

    st.markdown('<div class="lbl" style="margin-top:14px;">Zones</div>', unsafe_allow_html=True)
    show_zones = st.checkbox("S/R · FVG · Order Blocks", value=S.show_zones)
    st.session_state.show_zones = show_zones

    st.markdown('<div class="lbl" style="margin-top:14px;">FVG Filter</div>', unsafe_allow_html=True)
    fvg_strength = st.select_slider("FVG Strength", options=["Faible","Normal","Fort"],
                                     value="Normal", label_visibility="collapsed")
    st.markdown(f"""<div style="font-size:.6rem;color:#2e3a4e;margin-top:4px;">
        ATR×{"0.15" if fvg_strength=="Faible" else ("0.30" if fvg_strength=="Normal" else "0.50")}
        · FVG: {len(zones.get("fvg_bullish",[]))+len(zones.get("fvg_bearish",[]))} zones détectées
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Connexion status
    ws_ok  = S.ws_connected
    mt5_ok = S.mt5_connected
    ws_dot = '<span class="ws-dot"></span>'   if ws_ok  else '<span class="offline-dot"></span>'
    mt_dot = '<span class="live-dot"></span>' if mt5_ok else '<span class="offline-dot"></span>'
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.055);
                border-radius:7px;padding:8px 10px;font-size:.68rem;">
        <div style="margin-bottom:4px;color:{'#a78bfa' if ws_ok else '#ff4d6a'};">
            {ws_dot}WS {'Connecté' if ws_ok else 'Déconnecté'}
        </div>
        <div style="color:{'#00d4aa' if mt5_ok else '#f7b529'};">
            {mt_dot}MT5 {'Live' if mt5_ok else 'Simulation'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:.58rem;color:#2e3a4e;margin-top:6px;line-height:1.8;">
        Tick: #{S.tick} · {datetime.now().strftime('%H:%M:%S')}<br>
        {S.gold_symbol or 'XAUUSD'}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.metric("Winrate", f"{S.winrate}%", f"{S.wins}W / {S.losses}L")

    with st.expander("⚙️ Config"):
        st.text_input("API URL", value=API_URL, key="_api_url_disp")
        st.text_input("WS URL", value=WS_URL,  key="_ws_url_disp")

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────

hc1, hc2, hc3 = st.columns([3,1.5,1])
with hc1:
    ws_label = "WebSocket Live" if S.ws_connected else "HTTP Polling"
    ws_col   = "#a78bfa" if S.ws_connected else "#f7b529"
    dot      = '<span class="ws-dot"></span>' if S.ws_connected else '<span class="offline-dot"></span>'
    st.markdown(f"""
    <div style="padding:6px 0 10px;border-bottom:1px solid rgba(255,255,255,0.055);margin-bottom:10px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.35rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            GOLD / DXY PRO
        </div>
        <div style="font-size:.62rem;color:#6b7a94;margin-top:2px;">
            {dot}<span style="color:{ws_col};">{ws_label}</span>
            &nbsp;·&nbsp;{tf}&nbsp;·&nbsp;{S.gold_symbol or 'XAUUSD'}
        </div>
    </div>
    """, unsafe_allow_html=True)

with hc2:
    sig_dir = signal.get("direction","WAIT")
    ant     = signal.get("anticipation")
    badge_c = {"BUY":"badge-buy","SELL":"badge-sell","WAIT":"badge-wait"}[sig_dir]
    st.markdown(f"""
    <div style="padding-top:8px;">
        <div class="lbl">Signal Actif</div>
        <div style="display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-top:4px;">
            <span class="{badge_c}">{sig_dir}</span>
            {"<span class='badge-ant'>"+ant+"</span>" if ant else ""}
        </div>
        <div style="font-size:.62rem;color:#6b7a94;margin-top:4px;">
            Conf: <b style="color:#dde3ee;">{signal.get('confidence',0)}%</b>
            &nbsp;·&nbsp; {signal.get('pipeline_state','IDLE')}
        </div>
    </div>
    """, unsafe_allow_html=True)

with hc3:
    st.markdown(f"""
    <div style="text-align:right;padding-top:8px;">
        <div style="font-size:1.05rem;font-weight:700;color:#dde3ee;">
            {datetime.now().strftime('%H:%M:%S')}
        </div>
        <div style="font-size:.58rem;color:#2e3a4e;">{datetime.now().strftime('%a %d %b')}</div>
        <div style="font-size:.58rem;color:#2e3a4e;">Tick #{S.tick}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  METRICS
# ─────────────────────────────────────────────────────────────────────────────

mc = st.columns(7)
with mc[0]: st.metric("XAUUSD",      f"{S.gold_price:,.2f}", f"{S.gold_change:+.2f} ({S.gold_pct:+.2f}%)")
with mc[1]: st.metric("DXY",         f"{S.dxy_price:.3f}",   f"{S.dxy_change:+.4f}")
with mc[2]:
    cl = "● Forte Neg" if S.correlation<-0.6 else ("● Modérée" if S.correlation<0 else "● Positive")
    st.metric("Corrélation", f"{S.correlation:+.4f}", cl)
with mc[3]:
    emo = {"BUY":"🟢","SELL":"🔴","WAIT":"⚪"}
    st.metric("Signal", f"{emo[sig_dir]} {sig_dir}", f"Conf: {signal.get('confidence',0)}%")
with mc[4]: st.metric("Winrate",     f"{S.winrate}%",        f"{S.wins}W / {S.losses}L")
with mc[5]: st.metric("BID / ASK",   f"{S.gold_bid:.2f}",    f"ASK {S.gold_ask:.2f}")
with mc[6]:
    rr     = signal.get("rr",0)
    sl_src = signal.get("sl_source","—")
    st.metric("R/R", f"1 : {rr}", f"SL: {sl_src}")

st.markdown("")

# ─────────────────────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────────────────────

tab_charts, tab_signal, tab_mtf, tab_logs, tab_history = st.tabs([
    "📊  Graphiques", "🎯  Signal & Zones", "🔀  Multi-TF", "📋  Logs", "📜  Historique"
])

# ══════════════════════════════════════════════════════════════
#  TAB 1 — GRAPHIQUES
# ══════════════════════════════════════════════════════════════
with tab_charts:
    gc1, gc2 = st.columns(2)
    with gc1:
        fig_gold = make_chart(gold_candles, "XAUUSD", C["gold"], tf,
                               signal=signal, zones=zones, show_zones=show_zones)
        _render_plotly(fig_gold, key=f"gold_{S.tick}")
    with gc2:
        fig_dxy = make_chart(dxy_candles, "DXY", C["dxy"], tf,
                              zones=None, show_zones=False)
        _render_plotly(fig_dxy, key=f"dxy_{S.tick}")

    st.markdown('<div class="lbl" style="margin-top:4px;">Corrélation Rolling</div>',
                unsafe_allow_html=True)
    _render_plotly_sm(make_corr_history(S.corr_history), key=f"corr_{S.tick}")

# ══════════════════════════════════════════════════════════════
#  TAB 2 — SIGNAL & ZONES
# ══════════════════════════════════════════════════════════════
with tab_signal:
    sc1, sc2, sc3 = st.columns([1,1,1.3])

    with sc1:
        _render_plotly_sm(make_corr_gauge(S.correlation), key="gauge")
        corr = S.correlation
        if corr < -0.65:   ic, it = C["green"], "✅ Corrélation forte — signaux fiables"
        elif corr < -0.4:  ic, it = C["gold"],  "⚠️ Corrélation modérée — attendre"
        else:              ic, it = C["red"],   "❌ Corrélation faible — éviter trades"
        st.markdown(f"""<div style="font-size:.68rem;color:{ic};background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.05);border-radius:7px;padding:8px 10px;">{it}</div>""",
            unsafe_allow_html=True)

    with sc2:
        direction = signal.get("direction","WAIT")
        antici    = signal.get("anticipation")
        badge_cls = {"BUY":"badge-buy","SELL":"badge-sell","WAIT":"badge-wait"}[direction]
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
                <span class="{badge_cls}" style="font-size:.8rem;padding:4px 14px;">{direction}</span>
                {"<span class='badge-ant'>"+antici+"</span>" if antici else ""}
            </div>
            <div style="font-size:.68rem;color:#6b7a94;line-height:2.1;">
                Confiance: <b style="color:#dde3ee;">{signal.get('confidence',0)}%</b><br>
                Corr: <b style="color:#dde3ee;">{signal.get('corr',0):+.4f}</b><br>
                Gold: <b style="color:#f7b529;">{signal.get('gold_price',0):,.2f}</b><br>
                DXY:  <b style="color:#4da6ff;">{signal.get('dxy_price',0):.3f}</b><br>
                Pipeline: <b style="color:#dde3ee;">{signal.get('pipeline_state','IDLE')}</b>
            </div>
        </div>""", unsafe_allow_html=True)

        if direction in ("BUY","SELL"):
            entry=signal.get("entry",0); tp=signal.get("tp",0)
            sl=signal.get("sl",0);       rr=signal.get("rr",0)
            st.markdown(f"""
            <div class="card" style="border-color:rgba(247,181,41,0.2);">
                <div class="lbl" style="margin-bottom:8px;">Niveaux</div>
                <div style="font-size:.72rem;line-height:2.2;">
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
                <div style="font-size:.6rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:4px;">
                    MODE ANTICIPATION
                </div>
                <div style="font-size:.72rem;color:#c4b5fd;">{antici}</div>
                <div style="font-size:.63rem;color:#6b7a94;margin-top:4px;">
                    {"DXY↓ → anticiper BUY GOLD" if "BUY" in antici else "DXY↑ → anticiper SELL GOLD"}
                    <br>⏳ Attendre confirmation corrélation
                </div>
            </div>""", unsafe_allow_html=True)

    with sc3:
        st.markdown('<div class="lbl">Zones Techniques</div>', unsafe_allow_html=True)
        atr = zones.get("atr", 0)
        fvg_filter = zones.get("fvg_filter", 0)
        st.markdown(f"""
        <div class="card">
            <div class="lbl" style="margin-bottom:8px;">Support / Résistance</div>
            <div style="font-size:.72rem;line-height:2.2;">
                <span style="color:#6b7a94;">Support:</span>
                <b style="color:#00d4aa;float:right;">{zones.get('support',0):,.2f}</b><br>
                <span style="color:#6b7a94;">Résistance:</span>
                <b style="color:#ff4d6a;float:right;">{zones.get('resistance',0):,.2f}</b><br>
                <span style="color:#6b7a94;">ATR:</span>
                <b style="color:#f7b529;float:right;">{atr:.3f}</b><br>
                <span style="color:#6b7a94;">FVG Filter:</span>
                <b style="color:#a78bfa;float:right;">{fvg_filter:.3f}</b>
            </div>
        </div>
        <div class="card">
            <div class="lbl" style="margin-bottom:8px;">FVG & Order Blocks</div>
            <div style="font-size:.72rem;line-height:2.2;">
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
with tab_mtf:
    mc2 = st.columns(3)
    for col, tf_n in zip(mc2, ["H1","M15","M5"]):
        d    = mtf.get(tf_n, {})
        sig  = d.get("signal","WAIT")
        corr = d.get("corr", 0.0)
        trend= d.get("trend","—")
        ant  = d.get("anticipation")
        bc   = {"BUY":"badge-buy","SELL":"badge-sell","WAIT":"badge-wait"}.get(sig,"badge-wait")
        cc   = C["green"] if corr<-0.6 else (C["gold"] if corr<0 else C["red"])
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.05rem;
                            color:#dde3ee;margin-bottom:8px;">{tf_n}</div>
                <div style="margin-bottom:8px;"><span class="{bc}">{sig}</span></div>
                <div style="font-size:.68rem;color:#6b7a94;line-height:2.0;text-align:left;">
                    Corr: <b style="color:{cc};float:right;">{corr:+.4f}</b><br>
                    Trend: <b style="color:#dde3ee;float:right;">{trend}</b>
                    {f'<br><span style="color:#a78bfa;">{ant}</span>' if ant else ''}
                </div>
            </div>""", unsafe_allow_html=True)

    sigs = [mtf.get(t,{}).get("signal","WAIT") for t in ["H1","M15","M5"]]
    buys = sigs.count("BUY"); sells = sigs.count("SELL")
    if buys >= 2:   cons, cc = "🟢 CONSENSUS BUY", C["green"]
    elif sells >= 2: cons, cc = "🔴 CONSENSUS SELL", C["red"]
    else:            cons, cc = "⚪ PAS DE CONSENSUS", C["gold"]
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);
                border-radius:10px;padding:14px;text-align:center;margin-top:10px;">
        <div style="font-size:.72rem;color:{cc};font-weight:700;">{cons}</div>
        <div style="font-size:.6rem;color:#2e3a4e;margin-top:4px;">
            H1 {sigs[0]} · M15 {sigs[1]} · M5 {sigs[2]}
        </div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 4 — LOGS
# ══════════════════════════════════════════════════════════════
with tab_logs:
    lc1, lc2 = st.columns([3,1])
    with lc1:
        st.markdown('<div class="lbl">Logs Temps Réel</div>', unsafe_allow_html=True)
    with lc2:
        lf = st.selectbox("Filtre", ["ALL","SIGNAL","WARNING","ERROR"],
                          label_visibility="collapsed")

    logs = S.bot_logs
    filtered = [l for l in reversed(logs) if lf=="ALL" or l.get("level")==lf]
    log_html  = '<div style="background:#0d1117;border:1px solid rgba(255,255,255,0.055);border-radius:8px;padding:12px;height:320px;overflow-y:auto;font-size:.65rem;line-height:1.9;">'
    for entry in filtered[:80]:
        lvl = entry.get("level","INFO").upper()
        cls = {"INFO":"#6b7a94","WARNING":"#f7b529","ERROR":"#ff4d6a","SIGNAL":"#00d4aa"}.get(lvl,"#6b7a94")
        log_html += (f'<div><span style="color:#2e3a4e;">{entry.get("time","")}</span> '
                     f'<span style="color:{cls};font-weight:600;">[{lvl}]</span> '
                     f'<span style="color:#9ca3af;">{entry.get("msg","")}</span></div>')
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

    bs_map = {"running":("🟢",C["green"],"Bot actif"),
              "simulation":("🟡",C["gold"],"Simulation"),
              "starting":("🔵","#4da6ff","Démarrage")}
    em, sc, sl = bs_map.get(S.bot_status, ("⚪",C["text"],"Inconnu"))
    st.markdown(f"""<div style="margin-top:8px;font-size:.68rem;color:{sc};">
        {em} {sl} &nbsp;·&nbsp; MT5: {'✅' if S.mt5_connected else '⚠️'} &nbsp;·&nbsp;
        WS: {'🟣 Connecté' if S.ws_connected else '🔴 Déconnecté'} &nbsp;·&nbsp;
        Màj: {S.last_update[:19] if S.last_update and len(str(S.last_update))>10 else '—'}
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TAB 5 — HISTORIQUE
# ══════════════════════════════════════════════════════════════
with tab_history:
    h1,h2,h3,h4 = st.columns(4)
    with h1: st.metric("Total",    len(S.signals))
    with h2: st.metric("Winrate",  f"{S.winrate}%")
    with h3: st.metric("Victoires",S.wins)
    with h4: st.metric("Défaites", S.losses)
    st.markdown("")

    sigs = S.signals
    if sigs:
        df_s = pd.DataFrame(sigs[::-1][-50:])
        cols = [c for c in ["time","direction","tf","entry","tp","sl","rr","sl_source","result"]
                if c in df_s.columns]
        def _style(val):
            m = {"BUY":"color:#00d4aa;font-weight:700","SELL":"color:#ff4d6a;font-weight:700",
                 "WIN":"color:#00d4aa","LOSS":"color:#ff4d6a"}
            return m.get(val,"color:#6b7a94")
        try:
            styled = df_s[cols].style.map(_style, subset=[c for c in ["direction","result"] if c in cols])
            try:
                st.dataframe(styled, width="stretch", height=300)
            except TypeError:
                st.dataframe(styled, use_container_width=True, height=300)
        except Exception:
            st.dataframe(df_s[cols], use_container_width=True, height=300)
    else:
        st.markdown("""<div style="text-align:center;padding:40px;color:#2e3a4e;font-size:.75rem;">
            Aucun signal enregistré.<br>Lance le bot + api_server.py pour voir les signaux.
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER + RERUN
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="text-align:center;padding:8px 0 2px;font-size:.53rem;color:#1e293b;
            border-top:1px solid rgba(255,255,255,0.04);margin-top:8px;">
    Gold/DXY Pro v3 · WebSocket · Tick #{S.tick} ·
    {'🟣 WS' if S.ws_connected else '🟡 HTTP'} · {API_URL}
</div>
""", unsafe_allow_html=True)

# Rerun léger — les données arrivent par WS, le rerun sert juste à redessiner l'UI
time.sleep(UI_REFRESH_S)
st.rerun()
