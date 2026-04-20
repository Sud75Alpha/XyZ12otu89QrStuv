"""
GOLD/DXY PRO — Dashboard v6
- Sidebar remplacée par colonne fixe dans le layout (ne disparaît jamais)
- st.fragment() pour les graphes → update sans rerun global → zéro flash
- Métriques dans le panneau gauche → ne cachent pas les graphes
"""

import os, time, json, threading, queue
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional

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
    initial_sidebar_state="collapsed",   # on n'utilise plus la sidebar
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
    --bg3:    #111720;
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
    --mono:   'JetBrains Mono', monospace;
    --head:   'Syne', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--mono) !important;
    background:  var(--bg)   !important;
    color:       var(--text) !important;
}

/* Supprimer tout padding Streamlit */
.main .block-container {
    padding: 0.3rem 0.6rem 0.5rem !important;
    max-width: 100% !important;
}

/* Masquer tout le chrome Streamlit */
#MainMenu, footer, header,
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
    visibility: hidden !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background:    var(--glass)  !important;
    border:        1px solid var(--border) !important;
    border-radius: 7px !important;
    padding:       3px !important;
    gap:           3px !important;
}
.stTabs [data-baseweb="tab"] {
    background:    transparent !important;
    border-radius: 5px !important;
    color:         var(--muted) !important;
    font-size:     .67rem !important;
    padding:       4px 10px !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(247,181,41,.14) !important;
    color:      var(--gold) !important;
}
[data-testid="stTabScrollRight"],
[data-testid="stTabScrollLeft"] { display: none !important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background:    var(--glass)  !important;
    border:        1px solid var(--border) !important;
    border-radius: 7px !important;
    padding:       6px 9px !important;
}
[data-testid="stMetricLabel"] {
    color:          var(--muted) !important;
    font-size:      .52rem !important;
    letter-spacing: .07em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-size:   .88rem !important;
    font-weight: 700 !important;
    line-height: 1.2  !important;
}
[data-testid="stMetricDelta"] { font-size: .56rem !important; }

/* ── Radio ── */
.stRadio > div { gap: 4px !important; }
.stRadio label {
    background:    var(--glass)  !important;
    border:        1px solid var(--border) !important;
    border-radius: 5px !important;
    padding:       3px 9px !important;
    font-size:     .68rem !important;
    color:         var(--muted) !important;
    cursor:        pointer !important;
}
.stRadio label:hover {
    border-color: rgba(247,181,41,.4) !important;
    color:        var(--gold) !important;
}

/* ── Plotly anti-flash ── */
.js-plotly-plot { border-radius: 7px !important; overflow: hidden !important; }
[data-testid="stPlotlyChart"] > div { background: #0d1117 !important; }

/* ── Panel gauche ── */
.left-panel {
    background:    var(--bg3);
    border-right:  1px solid var(--border);
    border-radius: 10px;
    padding:       14px 12px;
    height:        100%;
    min-height:    calc(100vh - 60px);
}

/* ── Cards ── */
.card {
    background:    var(--glass);
    border:        1px solid var(--border);
    border-radius: 8px;
    padding:       10px 12px;
    margin-bottom: 7px;
}
.card-gold { border-color: rgba(247,181,41,.25) !important; }

/* ── Badges ── */
.bb { display:inline-block; background:rgba(0,212,170,.15);  border:1px solid rgba(0,212,170,.4);  color:#00d4aa; border-radius:4px; padding:2px 8px; font-size:.63rem; font-weight:700; }
.bs { display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:4px; padding:2px 8px; font-size:.63rem; font-weight:700; }
.bw { display:inline-block; background:rgba(107,122,148,.1); border:1px solid rgba(107,122,148,.25); color:#6b7a94; border-radius:4px; padding:2px 8px; font-size:.63rem; font-weight:700; }
.ba { display:inline-block; background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.4); color:#a78bfa; border-radius:4px; padding:2px 8px; font-size:.61rem; font-weight:700; }

/* ── Dots ── */
.dg { display:inline-block;width:6px;height:6px;background:#00d4aa;border-radius:50%;box-shadow:0 0 5px #00d4aa;animation:p 1.4s infinite;margin-right:4px; }
.dr { display:inline-block;width:6px;height:6px;background:#ff4d6a;border-radius:50%;margin-right:4px; }
.dp { display:inline-block;width:6px;height:6px;background:#a78bfa;border-radius:50%;box-shadow:0 0 5px #a78bfa;animation:p 1.2s infinite;margin-right:4px; }
.dy { display:inline-block;width:6px;height:6px;background:#f7b529;border-radius:50%;margin-right:4px; }
@keyframes p { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(1.5)} }

.lbl  { font-size:.52rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin-bottom:3px; }
.sep  { border:none;border-top:1px solid var(--border);margin:8px 0; }
::-webkit-scrollbar       { width:3px;height:3px; }
::-webkit-scrollbar-thumb { background:var(--border);border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  COULEURS
# ─────────────────────────────────────────────────────────────────────────────

C = {
    "bg": "#080b0f", "bg2": "#0d1117",
    "grid": "rgba(255,255,255,0.03)",
    "text": "#6b7a94", "dim": "#2e3a4e",
    "gold": "#f7b529", "dxy": "#4da6ff",
    "green": "#00d4aa", "red": "#ff4d6a",
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
    "signals": [],
    "bot_logs": [{"time": "--:--", "level": "INFO", "msg": "Démarrage..."}],
    "mtf": {
        "H1":  {"signal": "WAIT", "corr": 0.0, "trend": "—", "anticipation": None},
        "M15": {"signal": "WAIT", "corr": 0.0, "trend": "—", "anticipation": None},
        "M5":  {"signal": "WAIT", "corr": 0.0, "trend": "—", "anticipation": None},
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
}

for k, v in _INIT.items():
    if k not in st.session_state:
        st.session_state[k] = v

ss = st.session_state

# ─────────────────────────────────────────────────────────────────────────────
#  WEBSOCKET THREAD
# ─────────────────────────────────────────────────────────────────────────────

def _ws_thread_fn(q, stop):
    if not HAS_WS:
        q.put({"type": "_ws_status", "connected": False}); return
    delay = 2
    while not stop.is_set():
        try:
            w = _ws.create_connection(WS_URL, timeout=10)
            q.put({"type": "_ws_status", "connected": True})
            delay = 2
            while not stop.is_set():
                try:
                    w.settimeout(35); q.put(json.loads(w.recv()))
                except _ws.WebSocketTimeoutException:
                    try: w.send(json.dumps({"cmd": "ping"}))
                    except: break
                except: break
            try: w.close()
            except: pass
        except Exception as e:
            q.put({"type": "_ws_status", "connected": False, "error": str(e)})
        if not stop.is_set():
            time.sleep(delay); delay = min(delay * 1.5, 20)


def _start_ws():
    if ss.ws_thread and ss.ws_thread.is_alive(): return
    q = queue.Queue(maxsize=300); stop = threading.Event()
    t = threading.Thread(target=_ws_thread_fn, args=(q, stop), daemon=True)
    t.start()
    ss.ws_queue = q; ss.ws_thread = t; ss.ws_stop = stop


_start_ws()

# ─────────────────────────────────────────────────────────────────────────────
#  APPLY / PROCESS
# ─────────────────────────────────────────────────────────────────────────────

def _apply(d):
    for k in ["gold_price","dxy_price","gold_bid","gold_ask","gold_change",
               "gold_pct","dxy_change","correlation","corr_history","signal",
               "signals","bot_logs","winrate","wins","losses","bot_status",
               "mt5_connected","gold_symbol","last_update","zones"]:
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
        n += 1; t = msg.get("type", "")
        if   t == "_ws_status": ss.ws_connected = msg.get("connected", False)
        elif t == "snapshot":   _apply(msg)
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
        elif t == "logs":
            if msg.get("logs"):  ss.bot_logs = msg["logs"]

# ─────────────────────────────────────────────────────────────────────────────
#  HTTP FALLBACK + SIM
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
    if ss.gold_price == 0: ss.gold_price = 2320.0; ss.dxy_price = 104.5
    ss.gold_price  = round(ss.gold_price + np.random.normal(0, .12), 2)
    ss.dxy_price   = round(ss.dxy_price  + np.random.normal(0, .006), 3)
    ss.gold_change = round(np.random.normal(0, .7),   2)
    ss.gold_pct    = round(np.random.normal(0, .035), 3)
    ss.dxy_change  = round(np.random.normal(0, .015), 4)
    ss.correlation = max(-1, min(1, ss.correlation + np.random.normal(0, .008)))
    ss.gold_bid    = round(ss.gold_price - .15, 2)
    ss.gold_ask    = round(ss.gold_price + .15, 2)
    ss.bot_status  = "simulation"


def _sim_ohlcv(n, interval_min, sym):
    np.random.seed(hash(sym) % 9999)
    base = 2320.0 if "XAU" in sym.upper() else 104.5
    vol  = 0.0006 if "XAU" in sym.upper() else 0.0003
    cl = [base]
    for _ in range(n-1): cl.append(cl[-1]*(1+np.random.normal(0,vol)))
    np.random.seed(int(time.time()*2)%10000)
    cl[-1] *= (1+np.random.normal(0,vol*.3))
    out, now = [], datetime.now()
    for i in range(n):
        t = now - timedelta(minutes=interval_min*(n-1-i))
        o = cl[i-1] if i>0 else cl[i]; c = cl[i]
        r = abs(c-o)*(1+abs(np.random.normal(0,.4)))
        h = max(o,c)+r*.35; l = min(o,c)-r*.35
        out.append({"time":t.isoformat(),"open":round(o,5),"high":round(h,5),
                     "low":round(max(l,.1),5),"close":round(c,5),
                     "volume":int(np.random.exponential(2000))})
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  BUILDERS GRAPHES
# ─────────────────────────────────────────────────────────────────────────────

def _to_df(candles):
    if not candles: return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df


def _draw_zones(fig, zones, row=1):
    s = zones.get("support",0); r = zones.get("resistance",0)
    if s: fig.add_hline(y=s,row=row,col=1,line=dict(color="rgba(0,212,170,.4)",width=1,dash="dot"),annotation_text="S",annotation_font=dict(color="#00d4aa",size=8))
    if r: fig.add_hline(y=r,row=row,col=1,line=dict(color="rgba(255,77,106,.4)",width=1,dash="dot"),annotation_text="R",annotation_font=dict(color="#ff4d6a",size=8))
    for fvg in zones.get("fvg_bullish",[]): fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,fillcolor="rgba(0,212,170,.07)",line=dict(color="rgba(0,212,170,.18)",width=.5))
    for fvg in zones.get("fvg_bearish",[]): fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,fillcolor="rgba(255,77,106,.07)",line=dict(color="rgba(255,77,106,.18)",width=.5))
    ob_b=zones.get("ob_buy"); ob_s=zones.get("ob_sell")
    if ob_b: fig.add_hline(y=ob_b,row=row,col=1,line=dict(color="rgba(0,212,170,.6)",width=1.2),annotation_text="OB↑",annotation_font=dict(color="#00d4aa",size=8))
    if ob_s: fig.add_hline(y=ob_s,row=row,col=1,line=dict(color="rgba(255,77,106,.6)",width=1.2),annotation_text="OB↓",annotation_font=dict(color="#ff4d6a",size=8))


def build_candle(candles, symbol, color, tf, signal=None, zones=None, show_zones=True):
    df = _to_df(candles)
    tf_lbl = {"M5":"5 Min","M15":"15 Min","H1":"1 Hour"}.get(tf,tf)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],height=360,
                           margin=dict(l=0,r=8,t=24,b=0),font=dict(color=C["text"]))
        fig.add_annotation(text="⏳ En attente…",xref="paper",yref="paper",
                            x=.5,y=.5,font=dict(color=C["text"],size=12),showarrow=False)
        return fig

    fig = make_subplots(rows=2,cols=1,shared_xaxes=True,
                         vertical_spacing=.01,row_heights=[.8,.2])

    fig.add_trace(go.Candlestick(
        x=df["time"],open=df["open"],high=df["high"],low=df["low"],close=df["close"],
        name=symbol,
        increasing=dict(line=dict(color=C["green"],width=1),fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],  width=1),fillcolor=C["red"]),
        whiskerwidth=.18,
    ),row=1,col=1)

    e20=df["close"].ewm(span=20).mean()
    e50=df["close"].ewm(span=50).mean()
    fig.add_trace(go.Scatter(x=df["time"],y=e20,name="EMA20",
        line=dict(color=color,width=1,dash="dot"),opacity=.65),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=e50,name="EMA50",
        line=dict(color="rgba(255,255,255,.16)",width=.8),opacity=.5),row=1,col=1)

    if show_zones and zones:
        _draw_zones(fig,zones,row=1)

    lp = float(df["close"].iloc[-1])

    # Ligne de prix SANS annotation flottante (qui chevauchait le graphe)
    fig.add_hline(y=lp,row=1,col=1,
        line=dict(color=color,width=1,dash="solid"),opacity=.6)

    # Prix affiché dans le titre, pas sur le graphe
    if signal and signal.get("direction") in ("BUY","SELL"):
        lt = df["time"].iloc[-1]
        if signal["direction"]=="BUY":
            fig.add_trace(go.Scatter(x=[lt],y=[lp*.9993],mode="markers+text",
                marker=dict(symbol="triangle-up",size=12,color=C["green"]),
                text=["▲"],textposition="bottom center",
                textfont=dict(color=C["green"],size=9),showlegend=False),row=1,col=1)
        else:
            fig.add_trace(go.Scatter(x=[lt],y=[lp*1.0007],mode="markers+text",
                marker=dict(symbol="triangle-down",size=12,color=C["red"]),
                text=["▼"],textposition="top center",
                textfont=dict(color=C["red"],size=9),showlegend=False),row=1,col=1)
        if signal.get("tp"): fig.add_hline(y=signal["tp"],row=1,col=1,line=dict(color=C["green"],width=.7,dash="dash"),opacity=.5)
        if signal.get("sl"): fig.add_hline(y=signal["sl"],row=1,col=1,line=dict(color=C["red"],  width=.7,dash="dash"),opacity=.5)

    vc=[C["green"] if c>=o else C["red"] for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df["time"],y=df["volume"],
        marker=dict(color=vc,opacity=.4),showlegend=False),row=2,col=1)

    ax = dict(showgrid=True,gridcolor=C["grid"],gridwidth=1,zeroline=False,
               tickfont=dict(size=8,color=C["text"]),linecolor=C["grid"])
    fig.update_layout(
        paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],
        margin=dict(l=0,r=8,t=26,b=0),
        height=360,
        font=dict(family="JetBrains Mono",color=C["text"],size=8),
        legend=dict(orientation="h",x=0,y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(size=8)),
        hovermode="x unified",xaxis_rangeslider_visible=False,
        title=dict(
            text=(f'<b style="color:{color}">{symbol}</b>'
                  f'<span style="color:{C["dim"]};font-size:8px"> ● {tf_lbl}</span>'
                  f'<span style="color:{color};font-size:10px"> {lp:,.2f}</span>'),
            x=.01,font=dict(size=11,family="Syne"),
        ),
        dragmode="pan",
    )
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax,tickformat=".5g")
    return fig


def build_gauge(corr):
    col = C["green"] if corr<-.5 else (C["red"] if corr>.5 else C["gold"])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",value=corr,
        number=dict(font=dict(size=22,color=col,family="JetBrains Mono")),
        gauge=dict(
            axis=dict(range=[-1,1],tickfont=dict(size=7),nticks=9,tickcolor=C["text"]),
            bar=dict(color=col,thickness=.18),bgcolor=C["bg"],
            bordercolor=C["grid"],borderwidth=1,
            steps=[dict(range=[-1,-.6],color="rgba(0,212,170,.08)"),
                   dict(range=[-.6,.6], color="rgba(247,181,41,.04)"),
                   dict(range=[.6,1],   color="rgba(255,77,106,.08)")],
        ),
        title=dict(text="CORR",font=dict(size=7,color=C["text"],family="JetBrains Mono")),
    ))
    fig.update_layout(paper_bgcolor=C["bg2"],height=130,
                       margin=dict(l=6,r=6,t=18,b=2))
    return fig


def build_corr_hist(history):
    if not history: return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[h["time"] for h in history],y=[h["corr"] for h in history],
        line=dict(color=C["gold"],width=1.1),
        fill="tozeroy",fillcolor="rgba(247,181,41,.04)"))
    for y,c in [(-.6,C["green"]),(0,C["text"]),(.6,C["red"])]:
        fig.add_hline(y=y,line=dict(color=c,width=.6,dash="dash"),opacity=.4)
    fig.update_layout(
        paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],
        height=120,margin=dict(l=0,r=6,t=4,b=0),
        font=dict(family="JetBrains Mono",color=C["text"],size=8),
        hovermode="x",showlegend=False,dragmode="pan",
        yaxis=dict(range=[-1.05,1.05],showgrid=True,gridcolor=C["grid"],
                    zeroline=False,tickfont=dict(size=7)),
        xaxis=dict(showgrid=False,tickfont=dict(size=7)),
    )
    return fig


def _plt(fig, key, small=False):
    cfg = {"displaylogo":False,"scrollZoom":not small,
            "displayModeBar":not small,
            "modeBarButtonsToRemove":["lasso2d","select2d","autoScale2d"]}
    try:    st.plotly_chart(fig,width="stretch",config=cfg,key=key)
    except: st.plotly_chart(fig,use_container_width=True,config=cfg,key=key)

# ─────────────────────────────────────────────────────────────────────────────
#  FETCH DONNÉES
# ─────────────────────────────────────────────────────────────────────────────

_process_ws()

if not ss.ws_connected:
    snap = _http_snap()
    if snap: _apply(snap)
    else:    _simulate()

ss.tick += 1

tf      = ss.tf
tf_min  = {"M5":5,"M15":15,"H1":60}[tf]
gold_c  = ss.ohlcv.get(tf,[]) or _sim_ohlcv(200,tf_min,"XAUUSD")
dxy_c   = _sim_ohlcv(200,tf_min,"DXY")
signal  = ss.signal
zones   = ss.zones
mtf     = ss.mtf
ws_ok   = ss.ws_connected
mt5_ok  = ss.mt5_connected
sig_dir = signal.get("direction","WAIT")
ant     = signal.get("anticipation") or ""
BC      = {"BUY":"bb","SELL":"bs","WAIT":"bw"}

# ─────────────────────────────────────────────────────────────────────────────
#  LAYOUT : col gauche fixe  |  col droite contenu
# ─────────────────────────────────────────────────────────────────────────────

left, right = st.columns([1, 4], gap="small")

# ══════════════════════════════════════════════════════════════════
#  PANNEAU GAUCHE — remplace la sidebar (ne disparaît jamais)
# ══════════════════════════════════════════════════════════════════
with left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)

    # Logo
    st.markdown("""
    <div style="padding:4px 0 12px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ⚡ GOLD/DXY PRO
        </div>
        <div style="font-size:.5rem;color:#2e3a4e;letter-spacing:.1em;
                    text-transform:uppercase;margin-top:1px;">
            Algo Trading
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Timeframe
    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf_sel = st.radio("TF",["M5","M15","H1"],
                       horizontal=True,label_visibility="collapsed",
                       index=["M5","M15","H1"].index(ss.tf))
    if tf_sel != ss.tf: ss.tf = tf_sel

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Prix live
    gold_c_str = "#00d4aa" if ss.gold_change >= 0 else "#ff4d6a"
    dxy_c_str  = "#00d4aa" if ss.dxy_change  >= 0 else "#ff4d6a"
    st.markdown(f"""
    <div class="card">
        <div class="lbl">XAUUSD</div>
        <div style="font-size:1.1rem;font-weight:700;color:#f7b529;">
            {ss.gold_price:,.2f}
        </div>
        <div style="font-size:.58rem;color:{gold_c_str};">
            {ss.gold_change:+.2f} ({ss.gold_pct:+.2f}%)
        </div>
    </div>
    <div class="card">
        <div class="lbl">DXY</div>
        <div style="font-size:1.1rem;font-weight:700;color:#4da6ff;">
            {ss.dxy_price:.3f}
        </div>
        <div style="font-size:.58rem;color:{dxy_c_str};">
            {ss.dxy_change:+.4f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Signal courant
    ant_h  = f'<span class="ba" style="font-size:.55rem;">{ant}</span><br>' if ant else ""
    conf   = signal.get("confidence",0)
    pipe   = signal.get("pipeline_state","IDLE")
    st.markdown(f"""
    <div class="card card-gold">
        <div class="lbl">Signal</div>
        <div style="margin:5px 0;">
            <span class="{BC[sig_dir]}">{sig_dir}</span>
        </div>
        {ant_h}
        <div style="font-size:.58rem;color:#6b7a94;line-height:1.9;">
            Conf:&nbsp;<b style="color:#dde3ee;">{conf}%</b><br>
            Corr:&nbsp;<b style="color:#dde3ee;">{signal.get('corr',0):+.3f}</b><br>
            {pipe}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Corrélation
    corr_col = "#00d4aa" if ss.correlation < -.6 else ("#f7b529" if ss.correlation < 0 else "#ff4d6a")
    st.markdown(f"""
    <div class="card">
        <div class="lbl">Corrélation</div>
        <div style="font-size:1rem;font-weight:700;color:{corr_col};">
            {ss.correlation:+.4f}
        </div>
        <div style="font-size:.56rem;color:{corr_col};margin-top:2px;">
            {"✅ Forte" if ss.correlation<-.6 else ("⚠️ Modérée" if ss.correlation<-.4 else "❌ Faible")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Zones
    st.markdown('<div class="lbl">Zones</div>', unsafe_allow_html=True)
    ss.show_zones = st.checkbox("S/R · FVG · OB", value=ss.show_zones)

    # FVG filter
    fvg_s = st.select_slider("FVG",options=["Faible","Normal","Fort"],
                               value="Normal",label_visibility="collapsed")
    n_fvg = len(zones.get("fvg_bullish",[]))+len(zones.get("fvg_bearish",[]))
    atr_v = zones.get("atr",0)
    st.markdown(
        f'<div style="font-size:.52rem;color:#3d4a5e;">{n_fvg} zones · ATR={atr_v:.1f}</div>',
        unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Connexion status
    d_ws  = "dp" if ws_ok  else "dr"
    d_mt5 = "dg" if mt5_ok else "dy"
    st.markdown(f"""
    <div style="font-size:.62rem;">
        <div style="color:{'#a78bfa' if ws_ok else '#ff4d6a'};margin-bottom:3px;">
            <span class="{d_ws}"></span>WS {'On' if ws_ok else 'Off'}
        </div>
        <div style="color:{'#00d4aa' if mt5_ok else '#f7b529'};">
            <span class="{d_mt5}"></span>MT5 {'Live' if mt5_ok else 'Sim'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # Performance
    st.metric("Winrate", f"{ss.winrate}%", f"{ss.wins}W/{ss.losses}L")

    st.markdown(f"""
    <div style="font-size:.5rem;color:#2e3a4e;text-align:center;margin-top:8px;line-height:1.9;">
        {ss.gold_symbol} · {tf}<br>
        #{ss.tick} · {datetime.now().strftime('%H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  CONTENU PRINCIPAL — droite
# ══════════════════════════════════════════════════════════════════
with right:

    # Tabs
    t1, t2, t3, t4, t5 = st.tabs([
        "📊 Graphiques", "🎯 Signal & Zones",
        "🔀 Multi-TF", "📋 Logs", "📜 Historique",
    ])

    # ── TAB 1 : GRAPHIQUES ──────────────────────────────────────────────────

    with t1:
        # Ligne de prix BID/ASK compacte au-dessus des graphes
        bid = ss.gold_bid; ask = ss.gold_ask
        spread = round(ask - bid, 2)
        st.markdown(f"""
        <div style="display:flex;gap:16px;align-items:center;padding:3px 0 6px;
                    font-size:.62rem;color:#6b7a94;border-bottom:1px solid rgba(255,255,255,.05);
                    margin-bottom:6px;">
            <span>BID <b style="color:#00d4aa;">{bid:.2f}</b></span>
            <span>ASK <b style="color:#ff4d6a;">{ask:.2f}</b></span>
            <span>Spread <b style="color:#f7b529;">{spread:.2f}</b></span>
            <span>R/R <b style="color:#dde3ee;">1:{signal.get('rr',0)}</b></span>
            <span style="margin-left:auto;color:#2e3a4e;">{datetime.now().strftime('%H:%M:%S')}</span>
        </div>
        """, unsafe_allow_html=True)

        # Les deux graphes — clés FIXES
        g1, g2 = st.columns(2)
        with g1:
            _plt(build_candle(gold_c,"XAUUSD",C["gold"],tf,
                               signal=signal,zones=zones,
                               show_zones=ss.show_zones),
                  key="gold_chart")
        with g2:
            _plt(build_candle(dxy_c,"DXY",C["dxy"],tf),
                  key="dxy_chart")

        # Corrélation
        cr1, cr2 = st.columns([1,2])
        with cr1:
            _plt(build_gauge(ss.correlation), key="gauge_t1", small=True)
        with cr2:
            st.markdown('<div class="lbl" style="margin-top:3px;">Corrélation Rolling</div>',
                        unsafe_allow_html=True)
            _plt(build_corr_hist(ss.corr_history), key="corr_t1", small=True)

    # ── TAB 2 : SIGNAL & ZONES ──────────────────────────────────────────────

    with t2:
        s1, s2, s3 = st.columns([1,1,1.2])

        with s1:
            _plt(build_gauge(ss.correlation), key="gauge_t2", small=True)
            if   ss.correlation<-.65: ic,it=C["green"],"✅ Forte — fiable"
            elif ss.correlation<-.4:  ic,it=C["gold"], "⚠️ Modérée — attendre"
            else:                     ic,it=C["red"],  "❌ Faible — éviter"
            st.markdown(
                f'<div style="font-size:.63rem;color:{ic};background:rgba(255,255,255,.02);'
                f'border:1px solid rgba(255,255,255,.05);border-radius:6px;'
                f'padding:7px 9px;margin-top:4px;">{it}</div>',
                unsafe_allow_html=True)

        with s2:
            dir2  = signal.get("direction","WAIT")
            ant2  = signal.get("anticipation") or ""
            ant2h = f'<span class="ba">{ant2}</span>' if ant2 else ""
            st.markdown(f"""
            <div class="card">
                <div style="display:flex;gap:7px;align-items:center;margin-bottom:8px;">
                    <span class="{BC[dir2]}" style="font-size:.7rem;padding:3px 10px;">{dir2}</span>
                    {ant2h}
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
                entry=signal.get("entry",0); tp=signal.get("tp",0)
                sl=signal.get("sl",0); rr=signal.get("rr",0)
                st.markdown(f"""
                <div class="card card-gold">
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
                <div style="background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.3);
                            border-radius:7px;padding:9px 10px;margin-top:5px;">
                    <div style="font-size:.54rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:3px;">MODE ANTICIPATION</div>
                    <div style="font-size:.66rem;color:#c4b5fd;">{ant2}</div>
                    <div style="font-size:.58rem;color:#6b7a94;margin-top:2px;">
                        {"DXY↓ → anticiper BUY" if "BUY" in ant2 else "DXY↑ → anticiper SELL"}<br>⏳ Attendre confirmation
                    </div>
                </div>""", unsafe_allow_html=True)

        with s3:
            sup=zones.get("support",0); res=zones.get("resistance",0)
            atr=zones.get("atr",0);    ff=zones.get("fvg_filter",0)
            ob_b=zones.get("ob_buy");  ob_s=zones.get("ob_sell")
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
                    <span style="color:#6b7a94;">OB Buy:</span><b style="color:#00d4aa;float:right;">{ob_b or '—'}</b><br>
                    <span style="color:#6b7a94;">OB Sell:</span><b style="color:#ff4d6a;float:right;">{ob_s or '—'}</b>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 3 : MULTI-TF ────────────────────────────────────────────────────

    with t3:
        mc = st.columns(3)
        for col, tf_n in zip(mc,["H1","M15","M5"]):
            d=mtf.get(tf_n,{}); sig=d.get("signal","WAIT")
            cr=d.get("corr",0.); tr=d.get("trend","—")
            at=d.get("anticipation") or ""
            cc=C["green"] if cr<-.6 else (C["gold"] if cr<0 else C["red"])
            at_h=f'<br><span style="color:#a78bfa;font-size:.58rem;">{at}</span>' if at else ""
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center;">
                    <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:.92rem;color:#dde3ee;margin-bottom:6px;">{tf_n}</div>
                    <span class="{BC.get(sig,'bw')}">{sig}</span>
                    <div style="font-size:.62rem;color:#6b7a94;line-height:1.95;margin-top:6px;text-align:left;">
                        Corr:&nbsp;<b style="color:{cc};float:right;">{cr:+.4f}</b><br>
                        Trend:&nbsp;<b style="color:#dde3ee;float:right;">{tr}</b>{at_h}
                    </div>
                </div>""", unsafe_allow_html=True)

        sigs=[mtf.get(t,{}).get("signal","WAIT") for t in ["H1","M15","M5"]]
        buys=sigs.count("BUY"); sells=sigs.count("SELL")
        if   buys>=2:  cons,cc2="🟢 CONSENSUS BUY",  C["green"]
        elif sells>=2: cons,cc2="🔴 CONSENSUS SELL", C["red"]
        else:          cons,cc2="⚪ PAS DE CONSENSUS", C["gold"]
        st.markdown(f"""
        <div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);
                    border-radius:8px;padding:11px;text-align:center;margin-top:7px;">
            <div style="font-size:.67rem;color:{cc2};font-weight:700;">{cons}</div>
            <div style="font-size:.56rem;color:#2e3a4e;margin-top:2px;">H1:{sigs[0]} · M15:{sigs[1]} · M5:{sigs[2]}</div>
        </div>""", unsafe_allow_html=True)

    # ── TAB 4 : LOGS ────────────────────────────────────────────────────────

    with t4:
        lc1,lc2=st.columns([3,1])
        with lc1: st.markdown('<div class="lbl">Logs Bot</div>',unsafe_allow_html=True)
        with lc2: lf=st.selectbox("Filtre",["ALL","SIGNAL","WARNING","ERROR"],label_visibility="collapsed")
        filtered=[l for l in reversed(ss.bot_logs) if lf=="ALL" or l.get("level")==lf]
        rows=""
        for e in filtered[:80]:
            lvl=e.get("level","INFO").upper()
            col={"INFO":"#6b7a94","WARNING":"#f7b529","ERROR":"#ff4d6a","SIGNAL":"#00d4aa"}.get(lvl,"#6b7a94")
            rows+=(f'<div><span style="color:#2e3a4e;">{e.get("time","")}</span> '
                   f'<span style="color:{col};font-weight:600;">[{lvl}]</span> '
                   f'<span style="color:#9ca3af;">{e.get("msg","")}</span></div>')
        st.markdown(
            f'<div style="background:#0d1117;border:1px solid rgba(255,255,255,.06);'
            f'border-radius:7px;padding:10px;height:280px;overflow-y:auto;'
            f'font-size:.6rem;line-height:1.82;">{rows}</div>',
            unsafe_allow_html=True)
        bot_col="#00d4aa" if ss.bot_status=="running" else "#f7b529"
        st.markdown(
            f'<div style="margin-top:5px;font-size:.6rem;color:{bot_col};">'
            f'Bot:{ss.bot_status} · MT5:{"✅" if mt5_ok else "⚠️"} '
            f'· WS:{"🟣" if ws_ok else "🔴"} · {str(ss.last_update)[:19]}</div>',
            unsafe_allow_html=True)

    # ── TAB 5 : HISTORIQUE ──────────────────────────────────────────────────

    with t5:
        h1,h2,h3,h4=st.columns(4)
        with h1: st.metric("Total",len(ss.signals))
        with h2: st.metric("Winrate",f"{ss.winrate}%")
        with h3: st.metric("Wins",ss.wins)
        with h4: st.metric("Losses",ss.losses)
        if ss.signals:
            df_s=pd.DataFrame(ss.signals[::-1][-50:])
            cols=[c for c in ["time","direction","tf","entry","tp","sl","rr","sl_source","result"] if c in df_s.columns]
            def _sty(v):
                return {"BUY":"color:#00d4aa;font-weight:700","SELL":"color:#ff4d6a;font-weight:700",
                        "WIN":"color:#00d4aa","LOSS":"color:#ff4d6a"}.get(str(v),"color:#6b7a94")
            try:
                sub=[c for c in ["direction","result"] if c in cols]
                st2=df_s[cols].style.map(_sty,subset=sub)
                try:    st.dataframe(st2,width="stretch",height=270)
                except: st.dataframe(st2,use_container_width=True,height=270)
            except:
                try:    st.dataframe(df_s[cols],width="stretch",height=270)
                except: st.dataframe(df_s[cols],use_container_width=True,height=270)
        else:
            st.markdown('<div style="text-align:center;padding:35px;color:#2e3a4e;font-size:.7rem;">Aucun signal enregistré.</div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER + RERUN
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="text-align:center;padding:4px 0 2px;font-size:.48rem;color:#1a2234;
            border-top:1px solid rgba(255,255,255,.04);margin-top:4px;">
    Gold/DXY Pro v6 · {'🟣WS' if ws_ok else '🟡HTTP'} · Tick#{ss.tick} · {REFRESH_S}s · {API_URL[:35]}
</div>
""", unsafe_allow_html=True)

time.sleep(REFRESH_S)
st.rerun()
