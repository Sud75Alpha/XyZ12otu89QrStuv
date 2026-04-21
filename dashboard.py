"""
GOLD/DXY PRO — Dashboard v8
Page unique : Header + 2 graphes + Corrélation rolling
Sidebar fixe avec st.sidebar
Pas de tabs, pas de répétition
"""

import os, time, json, threading, queue
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Optional

try:
    import requests as _req
    HAS_REQ = True
except ImportError:
    HAS_REQ = False

try:
    import websocket as _ws
    HAS_WS = True
except ImportError:
    HAS_WS = False

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
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

try:
    API_URL = st.secrets["API_URL"]
    API_KEY = st.secrets["API_KEY"]
except Exception:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "gold_dxy_secret_2024")

WS_URL       = API_URL.replace("https://", "wss://").replace("http://", "ws://") + f"/ws?api_key={API_KEY}"
HTTP_HEADERS = {"X-API-Key": API_KEY}
REFRESH_S    = 3

# ─────────────────────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

:root {
    --bg:     #080b0f;
    --bg2:    #0d1117;
    --glass:  rgba(255,255,255,0.03);
    --border: rgba(255,255,255,0.07);
    --gold:   #f7b529;
    --green:  #00d4aa;
    --red:    #ff4d6a;
    --blue:   #4da6ff;
    --purple: #a78bfa;
    --text:   #dde3ee;
    --muted:  #6b7a94;
    --dim:    #2e3a4e;
}

html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace !important;
    background:  var(--bg) !important;
    color:       var(--text) !important;
}

/* Contenu principal — padding réduit */
.main .block-container {
    padding:   0.4rem 0.8rem 0.5rem !important;
    max-width: 100% !important;
}

/* Masquer chrome Streamlit */
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* Sidebar native */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1018 0%, #080b0f 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarCollapseButton"] { display: none !important; }

/* Metrics */
[data-testid="metric-container"] {
    background:    var(--glass) !important;
    border:        1px solid var(--border) !important;
    border-radius: 7px !important;
    padding:       6px 9px !important;
}
[data-testid="stMetricLabel"]  { color: var(--muted) !important; font-size: .53rem !important; letter-spacing: .07em !important; text-transform: uppercase !important; }
[data-testid="stMetricValue"]  { font-size: .88rem !important; font-weight: 700 !important; line-height: 1.2 !important; }
[data-testid="stMetricDelta"]  { font-size: .56rem !important; }

/* Radio */
.stRadio > div { gap: 4px !important; }
.stRadio label {
    background: var(--glass) !important; border: 1px solid var(--border) !important;
    border-radius: 5px !important; padding: 3px 9px !important;
    font-size: .68rem !important; color: var(--muted) !important; cursor: pointer !important;
}
.stRadio label:hover { border-color: rgba(247,181,41,.4) !important; color: var(--gold) !important; }

/* Plotly */
.js-plotly-plot { border-radius: 7px !important; overflow: hidden !important; }
[data-testid="stPlotlyChart"] > div { background: var(--bg2) !important; }

/* Cards */
.card { background: var(--glass); border: 1px solid var(--border); border-radius: 7px; padding: 9px 11px; margin-bottom: 6px; }
.card-g { border-color: rgba(247,181,41,.3) !important; }

/* Badges */
.bb { display:inline-block; background:rgba(0,212,170,.15);  border:1px solid rgba(0,212,170,.4);  color:#00d4aa; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.bs { display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.bw { display:inline-block; background:rgba(107,122,148,.1); border:1px solid rgba(107,122,148,.25); color:#6b7a94; border-radius:4px; padding:2px 8px; font-size:.64rem; font-weight:700; }
.ba { display:inline-block; background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.4); color:#a78bfa; border-radius:4px; padding:2px 8px; font-size:.62rem; font-weight:700; }

/* Dots */
.dg { display:inline-block;width:6px;height:6px;background:#00d4aa;border-radius:50%;box-shadow:0 0 5px #00d4aa;animation:pulse 1.4s infinite;margin-right:4px; }
.dr { display:inline-block;width:6px;height:6px;background:#ff4d6a;border-radius:50%;margin-right:4px; }
.dp { display:inline-block;width:6px;height:6px;background:#a78bfa;border-radius:50%;box-shadow:0 0 5px #a78bfa;animation:pulse 1.2s infinite;margin-right:4px; }
.dy { display:inline-block;width:6px;height:6px;background:#f7b529;border-radius:50%;margin-right:4px; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(1.6)} }

.lbl { font-size:.52rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--dim); margin-bottom:3px; }
hr   { border-color: var(--border) !important; margin: 7px 0 !important; }
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  COULEURS PLOTLY
# ─────────────────────────────────────────────────────────────────────────────

C = {
    "bg":    "#080b0f",
    "bg2":   "#0d1117",
    "grid":  "rgba(255,255,255,0.03)",
    "text":  "#6b7a94",
    "dim":   "#2e3a4e",
    "gold":  "#f7b529",
    "dxy":   "#4da6ff",
    "green": "#00d4aa",
    "red":   "#ff4d6a",
}

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

_INIT = {
    "tick": 0,
    "ws_connected": False,
    "ws_queue": None, "ws_thread": None, "ws_stop": None,
    "tf": "M5", "show_zones": True,
    "gold_price": 0.0, "dxy_price": 0.0,
    "gold_bid": 0.0,   "gold_ask": 0.0,
    "gold_change": 0.0,"gold_pct": 0.0, "dxy_change": 0.0,
    "correlation": -0.75, "corr_history": [],
    "signal": {
        "direction": "WAIT", "anticipation": None, "confidence": 0,
        "corr": -0.75, "gold_price": 0.0, "dxy_price": 0.0,
        "entry": 0.0, "tp": 0.0, "sl": 0.0, "rr": 0.0,
        "sl_source": "—", "pipeline_state": "IDLE",
    },
    "ohlcv": {"M5": [], "M15": [], "H1": []},
    "zones": {
        "support": 0.0, "resistance": 0.0,
        "fvg_bullish": [], "fvg_bearish": [],
        "ob_buy": None, "ob_sell": None,
        "atr": 0.0, "fvg_filter": 0.0,
    },
    "mtf": {
        "H1":  {"signal": "WAIT", "corr": 0.0, "trend": "—"},
        "M15": {"signal": "WAIT", "corr": 0.0, "trend": "—"},
        "M5":  {"signal": "WAIT", "corr": 0.0, "trend": "—"},
    },
    "winrate": 0.0, "wins": 0, "losses": 0,
    "bot_status": "unknown", "mt5_connected": False,
    "gold_symbol": "XAUUSD",
}

for k, v in _INIT.items():
    if k not in st.session_state:
        st.session_state[k] = v

ss = st.session_state

# ─────────────────────────────────────────────────────────────────────────────
#  WEBSOCKET THREAD
# ─────────────────────────────────────────────────────────────────────────────

def _ws_fn(q, stop):
    if not HAS_WS:
        q.put({"type": "_ws_status", "connected": False})
        return
    delay = 2
    while not stop.is_set():
        try:
            w = _ws.create_connection(WS_URL, timeout=10)
            q.put({"type": "_ws_status", "connected": True})
            delay = 2
            while not stop.is_set():
                try:
                    w.settimeout(35)
                    q.put(json.loads(w.recv()))
                except _ws.WebSocketTimeoutException:
                    try: w.send(json.dumps({"cmd": "ping"}))
                    except: break
                except: break
            try: w.close()
            except: pass
        except Exception as e:
            q.put({"type": "_ws_status", "connected": False})
        if not stop.is_set():
            time.sleep(delay)
            delay = min(delay * 1.5, 20)


def _start_ws():
    if ss.ws_thread and ss.ws_thread.is_alive():
        return
    q = queue.Queue(maxsize=300)
    stop = threading.Event()
    t = threading.Thread(target=_ws_fn, args=(q, stop), daemon=True)
    t.start()
    ss.ws_queue  = q
    ss.ws_thread = t
    ss.ws_stop   = stop


_start_ws()

# ─────────────────────────────────────────────────────────────────────────────
#  PROCESS WS + APPLY
# ─────────────────────────────────────────────────────────────────────────────

def _apply(d):
    for k in ["gold_price","dxy_price","gold_bid","gold_ask","gold_change",
               "gold_pct","dxy_change","correlation","corr_history","signal",
               "winrate","wins","losses","bot_status","mt5_connected",
               "gold_symbol","zones"]:
        if k in d: ss[k] = d[k]
    if "mtf_analysis" in d: ss.mtf = d["mtf_analysis"]
    if "mtf"          in d: ss.mtf = d["mtf"]
    if "ohlcv" in d:
        for tf, c in d["ohlcv"].items():
            if c: ss.ohlcv[tf] = c


def _process_ws():
    q = ss.ws_queue
    if not q: return
    n = 0
    while not q.empty() and n < 60:
        try: msg = q.get_nowait()
        except: break
        n += 1
        t = msg.get("type","")
        if   t == "_ws_status": ss.ws_connected = msg.get("connected", False)
        elif t in ("snapshot","price","signal","ohlcv","zones"):
            if t == "snapshot": _apply(msg)
            elif t == "price":
                ss.gold_price  = msg.get("gold",        ss.gold_price)
                ss.dxy_price   = msg.get("dxy",         ss.dxy_price)
                ss.gold_bid    = msg.get("gold_bid",     ss.gold_bid)
                ss.gold_ask    = msg.get("gold_ask",     ss.gold_ask)
                ss.gold_change = msg.get("gold_change",  0.0)
                ss.gold_pct    = msg.get("gold_pct",     0.0)
                ss.dxy_change  = msg.get("dxy_change",   0.0)
                ss.correlation = msg.get("corr",         ss.correlation)
            elif t == "signal":
                if "signal" in msg: ss.signal = msg["signal"]
                if "mtf"    in msg: ss.mtf    = msg["mtf"]
                if "stats"  in msg:
                    ss.winrate = msg["stats"].get("winrate", ss.winrate)
                    ss.wins    = msg["stats"].get("wins",    ss.wins)
                    ss.losses  = msg["stats"].get("losses",  ss.losses)
            elif t == "ohlcv":
                tf = msg.get("timeframe","M5"); c = msg.get("candles",[])
                if c: ss.ohlcv[tf] = c
            elif t == "zones":
                if msg.get("zones"): ss.zones = msg["zones"]

# ─────────────────────────────────────────────────────────────────────────────
#  HTTP FALLBACK + SIMULATION
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3)
def _http_snap():
    if not HAS_REQ: return None
    try:
        r = _req.get(f"{API_URL}/api/snapshot", headers=HTTP_HEADERS, timeout=3)
        return r.json() if r.status_code == 200 else None
    except: return None


def _simulate():
    np.random.seed(int(time.time()) % 9999)
    if ss.gold_price == 0:
        ss.gold_price = 2320.0; ss.dxy_price = 104.5
    ss.gold_price  = round(ss.gold_price + np.random.normal(0, .12), 2)
    ss.dxy_price   = round(ss.dxy_price  + np.random.normal(0, .006), 3)
    ss.gold_change = round(np.random.normal(0, .7),   2)
    ss.gold_pct    = round(np.random.normal(0, .035), 3)
    ss.dxy_change  = round(np.random.normal(0, .015), 4)
    ss.correlation = max(-1, min(1, ss.correlation + np.random.normal(0, .008)))
    ss.gold_bid    = round(ss.gold_price - .15, 2)
    ss.gold_ask    = round(ss.gold_price + .15, 2)
    ss.bot_status  = "simulation"


def _sim_ohlcv(n, mins, sym):
    np.random.seed(hash(sym) % 9999)
    base = 2320.0 if "XAU" in sym.upper() else 104.5
    vol  = 0.0006 if "XAU" in sym.upper() else 0.0003
    cl = [base]
    for _ in range(n - 1): cl.append(cl[-1] * (1 + np.random.normal(0, vol)))
    np.random.seed(int(time.time() * 2) % 10000)
    cl[-1] *= (1 + np.random.normal(0, vol * .3))
    out, now = [], datetime.now()
    for i in range(n):
        t = now - timedelta(minutes=mins * (n - 1 - i))
        o = cl[i-1] if i > 0 else cl[i]; c = cl[i]
        r = abs(c - o) * (1 + abs(np.random.normal(0, .4)))
        h = max(o, c) + r * .35; l = min(o, c) - r * .35
        out.append({"time": t.isoformat(), "open": round(o,5),
                     "high": round(h,5), "low": round(max(l,.1),5),
                     "close": round(c,5), "volume": int(np.random.exponential(2000))})
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  CORRÉLATION ROLLING — fenêtre glissante sur OHLCV
# ─────────────────────────────────────────────────────────────────────────────

def _rolling_corr(gold_c: List[dict], dxy_c: List[dict], window: int = 50) -> List[dict]:
    n = min(len(gold_c), len(dxy_c))
    if n < window + 5:
        return []
    g = [c["close"] for c in gold_c[-n:]]
    d = [c["close"] for c in dxy_c[-n:]]
    t = [c["time"]  for c in gold_c[-n:]]
    out = []
    for i in range(window, n):
        ga = np.array(g[i - window: i])
        da = np.array(d[i - window: i])
        if np.std(ga) < 1e-10 or np.std(da) < 1e-10:
            corr = 0.0
        else:
            corr = float(np.corrcoef(ga, da)[0, 1])
        out.append({"time": t[i], "corr": round(corr, 4)})
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  BUILDERS GRAPHES
# ─────────────────────────────────────────────────────────────────────────────

def _df(candles):
    if not candles: return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df


def _zones(fig, z, row=1):
    s = z.get("support",0); r = z.get("resistance",0)
    if s: fig.add_hline(y=s, row=row, col=1, line=dict(color="rgba(0,212,170,.45)", width=1, dash="dot"), annotation_text="S", annotation_font=dict(color="#00d4aa", size=8))
    if r: fig.add_hline(y=r, row=row, col=1, line=dict(color="rgba(255,77,106,.45)", width=1, dash="dot"), annotation_text="R", annotation_font=dict(color="#ff4d6a", size=8))
    for fvg in z.get("fvg_bullish",[]): fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,fillcolor="rgba(0,212,170,.08)",line=dict(color="rgba(0,212,170,.2)",width=.5))
    for fvg in z.get("fvg_bearish",[]): fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,fillcolor="rgba(255,77,106,.08)",line=dict(color="rgba(255,77,106,.2)",width=.5))
    ob_b = z.get("ob_buy"); ob_s = z.get("ob_sell")
    if ob_b: fig.add_hline(y=ob_b, row=row, col=1, line=dict(color="rgba(0,212,170,.65)",width=1.2), annotation_text="OB↑", annotation_font=dict(color="#00d4aa",size=8))
    if ob_s: fig.add_hline(y=ob_s, row=row, col=1, line=dict(color="rgba(255,77,106,.65)",width=1.2), annotation_text="OB↓", annotation_font=dict(color="#ff4d6a",size=8))


def build_candle(candles, symbol, color, tf, signal=None, zones=None, show_zones=True):
    df     = _df(candles)
    tf_lbl = {"M5":"5 Min","M15":"15 Min","H1":"1 Hour"}.get(tf, tf)

    if df.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
                           height=360, margin=dict(l=0,r=8,t=26,b=0))
        fig.add_annotation(text="⏳ En attente…", xref="paper", yref="paper",
                            x=.5, y=.5, font=dict(color=C["text"],size=12), showarrow=False)
        return fig

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         vertical_spacing=.01, row_heights=[.8,.2])

    # Bougies
    fig.add_trace(go.Candlestick(
        x=df["time"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name=symbol,
        increasing=dict(line=dict(color=C["green"],width=1), fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],  width=1), fillcolor=C["red"]),
        whiskerwidth=.18,
    ), row=1, col=1)

    # EMAs
    fig.add_trace(go.Scatter(x=df["time"], y=df["close"].ewm(span=20).mean(),
        name="EMA20", line=dict(color=color,width=1,dash="dot"), opacity=.65), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=df["close"].ewm(span=50).mean(),
        name="EMA50", line=dict(color="rgba(255,255,255,.16)",width=.8), opacity=.5), row=1, col=1)

    # Zones techniques
    if show_zones and zones:
        _zones(fig, zones, row=1)

    # Prix courant — ligne fine + valeur dans le titre
    lp = float(df["close"].iloc[-1])
    fig.add_hline(y=lp, row=1, col=1,
        line=dict(color=color, width=.8, dash="dash"), opacity=.5)

    # Signal marker
    if signal and signal.get("direction") in ("BUY","SELL"):
        lt = df["time"].iloc[-1]
        up = signal["direction"] == "BUY"
        fig.add_trace(go.Scatter(
            x=[lt], y=[lp*(.9993 if up else 1.0007)],
            mode="markers+text",
            marker=dict(symbol="triangle-up" if up else "triangle-down",
                        size=12, color=C["green"] if up else C["red"]),
            text=["▲" if up else "▼"],
            textposition="bottom center" if up else "top center",
            textfont=dict(color=C["green"] if up else C["red"], size=9),
            showlegend=False,
        ), row=1, col=1)
        if signal.get("tp"):
            fig.add_hline(y=signal["tp"], row=1, col=1, line=dict(color=C["green"],width=.7,dash="dash"), opacity=.5)
        if signal.get("sl"):
            fig.add_hline(y=signal["sl"], row=1, col=1, line=dict(color=C["red"],  width=.7,dash="dash"), opacity=.5)

    # Volume
    vc = [C["green"] if c >= o else C["red"] for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df["time"], y=df["volume"],
        marker=dict(color=vc,opacity=.4), showlegend=False), row=2, col=1)

    ax = dict(showgrid=True, gridcolor=C["grid"], gridwidth=1,
               zeroline=False, tickfont=dict(size=8,color=C["text"]),
               linecolor=C["grid"])
    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        margin=dict(l=0, r=8, t=28, b=0), height=360,
        font=dict(family="JetBrains Mono", color=C["text"], size=8),
        legend=dict(orientation="h", x=0, y=1.1, bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
        hovermode="x unified", xaxis_rangeslider_visible=False,
        title=dict(
            text=(f'<b style="color:{color}">{symbol}</b>'
                  f'<span style="color:{C["dim"]};font-size:8px"> ● {tf_lbl}</span>'
                  f'  <span style="color:{color};font-size:11px;font-weight:700"> {lp:,.2f}</span>'),
            x=.01, font=dict(size=11, family="Syne"),
        ),
        dragmode="pan",
    )
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax, tickformat=".5g")
    return fig


def build_corr_chart(corr_data: List[dict], current_corr: float) -> go.Figure:
    fig = go.Figure()

    if corr_data:
        times = [d["time"] for d in corr_data]
        corrs = [d["corr"]  for d in corr_data]

        fig.add_trace(go.Scatter(
            x=times, y=corrs, name="Corrélation",
            line=dict(color=C["gold"], width=1.5),
            fill="tozeroy", fillcolor="rgba(247,181,41,0.06)",
            hovertemplate="%{x|%H:%M}<br><b>%{y:.4f}</b><extra></extra>",
        ))
        # Zones colorées
        fig.add_hrect(y0=-1.05, y1=-0.6, fillcolor="rgba(0,212,170,.05)", line=dict(width=0))
        fig.add_hrect(y0= 0.6,  y1= 1.05, fillcolor="rgba(255,77,106,.05)", line=dict(width=0))
        # Seuils
        for y, col, lbl in [(-0.6, C["green"], "-0.6"), (0, C["text"], "0"), (0.6, C["red"], "0.6")]:
            fig.add_hline(y=y, line=dict(color=col, width=.8, dash="dot"), opacity=.5,
                           annotation_text=lbl, annotation_position="left",
                           annotation_font=dict(color=col, size=8))
    else:
        fig.add_annotation(text="En attente OHLCV…", xref="paper", yref="paper",
                            x=.5, y=.5, font=dict(color=C["text"],size=11), showarrow=False)

    fig.update_layout(
        paper_bgcolor=C["bg2"], plot_bgcolor=C["bg"],
        height=175, margin=dict(l=0, r=60, t=24, b=0),
        font=dict(family="JetBrains Mono", color=C["text"], size=8),
        title=dict(
            text=f'<span style="color:{C["text"]};font-size:8px">CORRÉLATION ROLLING GOLD/DXY  (fenêtre 50 bougies)</span>',
            x=.01,
        ),
        hovermode="x unified", showlegend=False, dragmode="pan",
        yaxis=dict(range=[-1.05,1.05], showgrid=True, gridcolor=C["grid"],
                    zeroline=False, tickfont=dict(size=8),
                    tickvals=[-1,-.6,-.2,0,.2,.6,1]),
        xaxis=dict(showgrid=False, tickfont=dict(size=8)),
    )
    return fig


def _plt(fig, key, small=False):
    cfg = {"displaylogo":False, "scrollZoom": not small,
            "displayModeBar": not small,
            "modeBarButtonsToRemove":["lasso2d","select2d","autoScale2d"]}
    try:    st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except: st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)

# ─────────────────────────────────────────────────────────────────────────────
#  FETCH DONNÉES
# ─────────────────────────────────────────────────────────────────────────────

_process_ws()

if not ss.ws_connected:
    snap = _http_snap()
    if snap: _apply(snap)
    else:    _simulate()

ss.tick += 1

tf     = ss.tf
tf_min = {"M5":5,"M15":15,"H1":60}[tf]
gold_c = ss.ohlcv.get(tf,[]) or _sim_ohlcv(200, tf_min, "XAUUSD")
dxy_c  = _sim_ohlcv(200, tf_min, "DXY")
signal = ss.signal
zones  = ss.zones
ws_ok  = ss.ws_connected
mt5_ok = ss.mt5_connected
sig_dir= signal.get("direction","WAIT")
ant    = signal.get("anticipation") or ""
BC     = {"BUY":"bb","SELL":"bs","WAIT":"bw"}

# Corrélation rolling calculée localement depuis OHLCV
corr_data = _rolling_corr(gold_c, dxy_c, window=50)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR — st.sidebar native
# ─────────────────────────────────────────────────────────────────────────────

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
    if tf_sel != ss.tf: ss.tf = tf_sel

    st.markdown("<hr>", unsafe_allow_html=True)

    # Prix live
    gc = "#00d4aa" if ss.gold_change >= 0 else "#ff4d6a"
    dc = "#00d4aa" if ss.dxy_change  >= 0 else "#ff4d6a"
    st.markdown(f"""
    <div class="card">
        <div class="lbl">XAUUSD</div>
        <div style="font-size:1.1rem;font-weight:700;color:#f7b529;">{ss.gold_price:,.2f}</div>
        <div style="font-size:.57rem;color:{gc};">{ss.gold_change:+.2f} ({ss.gold_pct:+.2f}%)</div>
    </div>
    <div class="card">
        <div class="lbl">DXY</div>
        <div style="font-size:1.1rem;font-weight:700;color:#4da6ff;">{ss.dxy_price:.3f}</div>
        <div style="font-size:.57rem;color:{dc};">{ss.dxy_change:+.4f}</div>
    </div>""", unsafe_allow_html=True)

    # Signal
    conf  = signal.get("confidence", 0)
    pipe  = signal.get("pipeline_state","IDLE")
    ant_h = f'<div style="margin-top:4px;"><span class="ba" style="font-size:.55rem;">{ant}</span></div>' if ant else ""
    st.markdown(f"""
    <div class="card card-g">
        <div class="lbl">Signal</div>
        <div style="margin:4px 0;"><span class="{BC[sig_dir]}">{sig_dir}</span></div>
        {ant_h}
        <div style="font-size:.57rem;color:#6b7a94;line-height:1.9;margin-top:3px;">
            Conf:&nbsp;<b style="color:#dde3ee;">{conf}%</b><br>
            Corr:&nbsp;<b style="color:#dde3ee;">{signal.get('corr',0):+.3f}</b><br>
            <span style="color:#3d4a5e;">{pipe}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Corrélation
    cc = "#00d4aa" if ss.correlation<-.6 else ("#f7b529" if ss.correlation<-.4 else "#ff4d6a")
    ct = "✅ Forte" if ss.correlation<-.6 else ("⚠️ Modérée" if ss.correlation<-.4 else "❌ Faible")
    st.markdown(f"""
    <div class="card">
        <div class="lbl">Corrélation</div>
        <div style="font-size:1rem;font-weight:700;color:{cc};">{ss.correlation:+.4f}</div>
        <div style="font-size:.55rem;color:{cc};margin-top:1px;">{ct}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Zones
    ss.show_zones = st.checkbox("S/R · FVG · OB", value=ss.show_zones)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Connexion
    dws  = "dp" if ws_ok  else "dr"
    dmt5 = "dg" if mt5_ok else "dy"
    st.markdown(f"""
    <div style="font-size:.61rem;">
        <div style="color:{'#a78bfa' if ws_ok else '#ff4d6a'};margin-bottom:3px;">
            <span class="{dws}"></span>WS {'Connecté' if ws_ok else 'Hors ligne'}
        </div>
        <div style="color:{'#00d4aa' if mt5_ok else '#f7b529'};">
            <span class="{dmt5}"></span>MT5 {'Live' if mt5_ok else 'Simulation'}
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1: st.metric("Winrate", f"{ss.winrate}%")
    with c2: st.metric("Trades",  f"{ss.wins}W/{ss.losses}L")

    st.markdown(f"""
    <div style="font-size:.49rem;color:#2e3a4e;text-align:center;margin-top:7px;line-height:2;">
        {ss.gold_symbol} · {tf} · #{ss.tick}<br>{datetime.now().strftime('%H:%M:%S')}
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CONTENU PRINCIPAL — UNE SEULE PAGE
# ─────────────────────────────────────────────────────────────────────────────

# ── Bandeau header ───────────────────────────────────────────────────────────
ws_col = "#a78bfa" if ws_ok else "#f7b529"
dh     = "dp" if ws_ok else "dr"
ant_hd = f' <span class="ba">{ant}</span>' if ant else ""

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:3px 0 5px;border-bottom:1px solid rgba(255,255,255,.06);
            margin-bottom:6px;">
    <div style="font-size:.6rem;color:#6b7a94;">
        <span class="{dh}"></span>
        <span style="color:{ws_col};">{'WS Live' if ws_ok else 'HTTP'}</span>
        &nbsp;·&nbsp;{'MT5' if mt5_ok else 'Sim'}
        &nbsp;·&nbsp;{tf}
        &nbsp;·&nbsp;<b style="color:#dde3ee;">{ss.gold_price:,.2f}</b>
    </div>
    <div style="display:flex;align-items:center;gap:7px;">
        <span class="{BC[sig_dir]}">{sig_dir}</span>{ant_hd}
        <span style="font-size:.58rem;color:#6b7a94;">
            Conf&nbsp;<b style="color:#dde3ee;">{signal.get('confidence',0)}%</b>
        </span>
        <span style="font-size:.88rem;font-weight:700;color:#dde3ee;margin-left:4px;">
            {datetime.now().strftime('%H:%M:%S')}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── BID / ASK / Spread ───────────────────────────────────────────────────────
bid    = ss.gold_bid; ask = ss.gold_ask
spread = round(ask - bid, 2)
st.markdown(f"""
<div style="display:flex;gap:16px;padding:2px 0 5px;font-size:.62rem;color:#6b7a94;
            border-bottom:1px solid rgba(255,255,255,.04);margin-bottom:5px;">
    <span>BID&nbsp;<b style="color:#00d4aa;">{bid:.2f}</b></span>
    <span>ASK&nbsp;<b style="color:#ff4d6a;">{ask:.2f}</b></span>
    <span>Spread&nbsp;<b style="color:#f7b529;">{spread:.2f}</b></span>
    <span>R/R&nbsp;<b style="color:#dde3ee;">1:{signal.get('rr',0)}</b></span>
    <span>SL&nbsp;<span style="color:#a78bfa;">{signal.get('sl_source','—')}</span></span>
</div>
""", unsafe_allow_html=True)

# ── 2 graphes côte à côte — clés FIXES ───────────────────────────────────────
g1, g2 = st.columns(2)
with g1:
    _plt(build_candle(gold_c, "XAUUSD", C["gold"], tf,
                       signal=signal, zones=zones, show_zones=ss.show_zones),
          key="gold_chart")   # ← CLÉ FIXE
with g2:
    _plt(build_candle(dxy_c, "DXY", C["dxy"], tf),
          key="dxy_chart")    # ← CLÉ FIXE

# ── Corrélation rolling pleine largeur ───────────────────────────────────────
_plt(build_corr_chart(corr_data, ss.correlation),
      key="corr_chart")       # ← CLÉ FIXE

# Légende sous la courbe
if corr_data:
    lc = corr_data[-1]["corr"]
    zc = "#00d4aa" if lc < -.6 else ("#f7b529" if lc < -.4 else "#ff4d6a")
    zt = "Zone signal active (corr < -0.6)" if lc < -.6 else ("Modérée" if lc < -.4 else "Hors zone signal")
    st.markdown(
        f'<div style="font-size:.57rem;color:{zc};margin-top:1px;">'
        f'Dernière valeur : <b>{lc:+.4f}</b> · {zt} · Fenêtre : 50 bougies</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER + RERUN
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="text-align:center;padding:4px 0 1px;font-size:.48rem;color:#1a2234;
            border-top:1px solid rgba(255,255,255,.04);margin-top:4px;">
    Gold/DXY Pro v8 · {'🟣WS' if ws_ok else '🟡HTTP'} · Tick#{ss.tick} · {REFRESH_S}s
</div>
""", unsafe_allow_html=True)

time.sleep(REFRESH_S)
st.rerun()
