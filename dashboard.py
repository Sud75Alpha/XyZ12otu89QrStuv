"""
GOLD/DXY PRO — Dashboard v4
Fixes : graphes uniques · pas de flash · prix compact · sidebar fixe
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

WS_URL       = API_URL.replace("https://","wss://").replace("http://","ws://") + f"/ws?api_key={API_KEY}"
HTTP_HEADERS = {"X-API-Key": API_KEY}
REFRESH_S    = 2.5   # rerun toutes les 2.5s — assez lent pour zéro flash

# ─────────────────────────────────────────────────────────────────────────────
#  CSS GLOBAL
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');

:root {
    --bg:#080b0f; --bg2:#0d1117;
    --glass:rgba(255,255,255,0.03);
    --border:rgba(255,255,255,0.07);
    --gold:#f7b529; --green:#00d4aa; --red:#ff4d6a;
    --blue:#4da6ff; --purple:#a78bfa;
    --text:#dde3ee; --muted:#6b7a94; --dim:#2e3a4e;
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
    padding:0.4rem 0.9rem 1rem!important;
    max-width:100%!important;
}

/* ── Masquer chrome Streamlit ── */
#MainMenu,footer,header,.stDeployButton,
[data-testid="stToolbar"] { display:none!important; }

/* ── SIDEBAR forcée visible ── */
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#0c1018,#080b0f)!important;
    border-right:1px solid var(--border)!important;
}
/* Masquer TOUS les boutons collapse */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stBaseButton-headerNoPadding"],
button[kind="headerNoPadding"],
.st-emotion-cache-zq5wmm,
.st-emotion-cache-1rtdyuf,
.st-emotion-cache-hzo1qh {
    display:none!important;
    visibility:hidden!important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
    display:flex!important;
    transform:none!important;
    margin-left:0!important;
}

/* ── Onglets ── */
.stTabs [data-baseweb="tab-list"] {
    background:var(--glass)!important;
    border:1px solid var(--border)!important;
    border-radius:8px!important;
    padding:3px!important; gap:3px!important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent!important; border-radius:6px!important;
    color:var(--muted)!important; font-size:.7rem!important;
    padding:4px 12px!important; letter-spacing:.04em!important;
}
.stTabs [aria-selected="true"] {
    background:rgba(247,181,41,.12)!important;
    color:var(--gold)!important;
}
/* Flèche de scroll des tabs */
[data-testid="stTabScrollRight"],
[data-testid="stTabScrollLeft"] { display:none!important; }

/* ── Metrics COMPACTS — une seule ligne ── */
[data-testid="metric-container"] {
    background:var(--glass)!important;
    border:1px solid var(--border)!important;
    border-radius:8px!important;
    padding:7px 10px!important;
}
[data-testid="stMetricLabel"] {
    color:var(--muted)!important; font-size:.55rem!important;
    letter-spacing:.08em!important; text-transform:uppercase!important;
    margin-bottom:1px!important;
}
[data-testid="stMetricValue"] {
    font-size:.95rem!important; font-weight:700!important;
    line-height:1.2!important;
}
[data-testid="stMetricDelta"] { font-size:.6rem!important; }

/* ── Radio ── */
.stRadio > div { gap:4px!important; }
.stRadio label {
    background:var(--glass)!important; border:1px solid var(--border)!important;
    border-radius:6px!important; padding:3px 10px!important;
    font-size:.7rem!important; color:var(--muted)!important; cursor:pointer!important;
}
.stRadio label:hover { border-color:rgba(247,181,41,.4)!important; color:var(--gold)!important; }

/* ── Plotly — anti-flash ── */
.js-plotly-plot { border-radius:8px!important; overflow:hidden!important; }
/* Éviter le blanc/flash au rerun */
.element-container:has(iframe) { min-height:0!important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }

/* ── Cards ── */
.card {
    background:var(--glass); border:1px solid var(--border);
    border-radius:9px; padding:11px 13px; margin-bottom:8px;
}

/* ── Badges ── */
.bb  { display:inline-block; background:rgba(0,212,170,.15); border:1px solid rgba(0,212,170,.4); color:#00d4aa; border-radius:4px; padding:1px 8px; font-size:.65rem; font-weight:700; }
.bs  { display:inline-block; background:rgba(255,77,106,.15); border:1px solid rgba(255,77,106,.4); color:#ff4d6a; border-radius:4px; padding:1px 8px; font-size:.65rem; font-weight:700; }
.bw  { display:inline-block; background:rgba(107,122,148,.1); border:1px solid rgba(107,122,148,.25); color:#6b7a94; border-radius:4px; padding:1px 8px; font-size:.65rem; font-weight:700; }
.ba  { display:inline-block; background:rgba(167,139,250,.12); border:1px solid rgba(167,139,250,.4); color:#a78bfa; border-radius:4px; padding:1px 8px; font-size:.62rem; font-weight:700; }

/* ── Status dots ── */
.dot-g { display:inline-block;width:6px;height:6px;background:#00d4aa;border-radius:50%;box-shadow:0 0 5px #00d4aa;animation:p 1.4s infinite;margin-right:4px; }
.dot-r { display:inline-block;width:6px;height:6px;background:#ff4d6a;border-radius:50%;margin-right:4px; }
.dot-p { display:inline-block;width:6px;height:6px;background:#a78bfa;border-radius:50%;box-shadow:0 0 5px #a78bfa;animation:p 1.2s infinite;margin-right:4px; }
.dot-y { display:inline-block;width:6px;height:6px;background:#f7b529;border-radius:50%;margin-right:4px; }
@keyframes p { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(1.5)} }

.lbl { font-size:.55rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin-bottom:3px; }
hr { border-color:var(--border)!important; margin:7px 0!important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

C = {
    "bg":"#080b0f","bg2":"#0d1117",
    "grid":"rgba(255,255,255,0.03)",
    "text":"#6b7a94","dim":"#2e3a4e",
    "gold":"#f7b529","dxy":"#4da6ff",
    "green":"#00d4aa","red":"#ff4d6a",
}

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

_D = {
    "tick":0,"ws_connected":False,
    "ws_queue":None,"ws_thread":None,"ws_stop":None,
    "tf":"M5","show_zones":True,
    "gold_price":0.0,"dxy_price":0.0,
    "gold_bid":0.0,"gold_ask":0.0,
    "gold_change":0.0,"gold_pct":0.0,"dxy_change":0.0,
    "correlation":-0.75,"corr_history":[],
    "signal":{"direction":"WAIT","anticipation":None,"confidence":0,
               "corr":-0.75,"gold_price":0.0,"dxy_price":0.0,
               "entry":0.0,"tp":0.0,"sl":0.0,"rr":0.0,
               "sl_source":"—","pipeline_state":"IDLE"},
    "signals":[],"bot_logs":[{"time":"--:--","level":"INFO","msg":"Démarrage..."}],
    "mtf":{"H1":{"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None},
            "M15":{"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None},
            "M5":{"signal":"WAIT","corr":0.0,"trend":"—","anticipation":None}},
    "ohlcv":{"M5":[],"M15":[],"H1":[]},
    "zones":{"support":0.0,"resistance":0.0,"fvg_bullish":[],"fvg_bearish":[],
              "ob_buy":None,"ob_sell":None,"atr":0.0,"fvg_filter":0.0},
    "winrate":0.0,"wins":0,"losses":0,
    "bot_status":"unknown","mt5_connected":False,
    "gold_symbol":"XAUUSD","last_update":"—",
}
for k,v in _D.items():
    if k not in st.session_state:
        st.session_state[k] = v

ss = st.session_state  # alias global

# ─────────────────────────────────────────────────────────────────────────────
#  WEBSOCKET THREAD
# ─────────────────────────────────────────────────────────────────────────────

def _ws_fn(q, stop):
    if not HAS_WS:
        q.put({"type":"_ws_status","connected":False})
        return
    delay = 2
    while not stop.is_set():
        try:
            w = _ws.create_connection(WS_URL, timeout=10)
            q.put({"type":"_ws_status","connected":True})
            delay = 2
            while not stop.is_set():
                try:
                    w.settimeout(35)
                    q.put(json.loads(w.recv()))
                except _ws.WebSocketTimeoutException:
                    w.send(json.dumps({"cmd":"ping"}))
                except Exception:
                    break
            try: w.close()
            except: pass
        except Exception as e:
            q.put({"type":"_ws_status","connected":False,"error":str(e)})
        if not stop.is_set():
            time.sleep(delay); delay = min(delay*1.5, 20)


def _start_ws():
    if ss.ws_thread and ss.ws_thread.is_alive():
        return
    q = queue.Queue(maxsize=300)
    stop = threading.Event()
    t = threading.Thread(target=_ws_fn, args=(q,stop), daemon=True)
    t.start()
    ss.ws_queue=q; ss.ws_thread=t; ss.ws_stop=stop

_start_ws()

# ─────────────────────────────────────────────────────────────────────────────
#  TRAITEMENT WS MESSAGES
# ─────────────────────────────────────────────────────────────────────────────

def _snap(d):
    for k in ["gold_price","dxy_price","gold_bid","gold_ask","gold_change",
              "gold_pct","dxy_change","correlation","corr_history","signal",
              "signals","bot_logs","winrate","wins","losses","bot_status",
              "mt5_connected","gold_symbol","last_update","zones"]:
        if k in d: ss[k] = d[k]
    if "mtf_analysis" in d: ss["mtf"] = d["mtf_analysis"]
    if "ohlcv" in d:
        for tf,c in d["ohlcv"].items():
            if c: ss.ohlcv[tf] = c


def _process_ws():
    q = ss.ws_queue
    if not q: return
    n = 0
    while not q.empty() and n < 50:
        try: msg = q.get_nowait()
        except: break
        n += 1
        t = msg.get("type","")
        if   t == "_ws_status": ss.ws_connected = msg.get("connected",False)
        elif t == "snapshot":   _snap(msg)
        elif t == "price":
            for k in ["gold","dxy","gold_bid","gold_ask"]:
                if k in msg: ss[f"gold_price" if k=="gold" else (f"dxy_price" if k=="dxy" else k)] = msg[k]
            ss.gold_price  = msg.get("gold",  ss.gold_price)
            ss.dxy_price   = msg.get("dxy",   ss.dxy_price)
            ss.gold_bid    = msg.get("gold_bid",  ss.gold_bid)
            ss.gold_ask    = msg.get("gold_ask",  ss.gold_ask)
            ss.gold_change = msg.get("gold_change", 0.0)
            ss.gold_pct    = msg.get("gold_pct",    0.0)
            ss.dxy_change  = msg.get("dxy_change",  0.0)
            ss.correlation = msg.get("corr", ss.correlation)
        elif t == "signal":
            if "signal" in msg: ss.signal = msg["signal"]
            if "mtf" in msg:    ss.mtf    = msg["mtf"]
            if "stats" in msg:
                ss.winrate = msg["stats"].get("winrate", ss.winrate)
                ss.wins    = msg["stats"].get("wins",    ss.wins)
                ss.losses  = msg["stats"].get("losses",  ss.losses)
        elif t == "ohlcv":
            tf = msg.get("timeframe","M5")
            c  = msg.get("candles",[])
            if c: ss.ohlcv[tf] = c
        elif t == "zones":
            if msg.get("zones"): ss.zones = msg["zones"]
        elif t == "logs":
            if msg.get("logs"): ss.bot_logs = msg["logs"]


# ─────────────────────────────────────────────────────────────────────────────
#  HTTP FALLBACK + SIMULATION
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3)
def _http():
    if not HAS_REQ: return None
    try:
        r = _req.get(f"{API_URL}/api/snapshot", headers=HTTP_HEADERS, timeout=3)
        return r.json() if r.status_code==200 else None
    except: return None


def _sim():
    np.random.seed(int(time.time()) % 9999)
    if ss.gold_price == 0: ss.gold_price=2320.0; ss.dxy_price=104.5
    ss.gold_price  = round(ss.gold_price  + np.random.normal(0,.12), 2)
    ss.dxy_price   = round(ss.dxy_price   + np.random.normal(0,.006),3)
    ss.gold_change = round(np.random.normal(0,.7),  2)
    ss.gold_pct    = round(np.random.normal(0,.03), 3)
    ss.dxy_change  = round(np.random.normal(0,.015),4)
    ss.correlation = max(-1,min(1, ss.correlation+np.random.normal(0,.008)))
    ss.gold_bid    = round(ss.gold_price-.15,2)
    ss.gold_ask    = round(ss.gold_price+.15,2)
    ss.bot_status  = "simulation"


def _sim_ohlcv(n,interval_min,sym):
    np.random.seed(hash(sym)%9999)
    base=2320. if "XAU" in sym.upper() else 104.5
    vol =.0006  if "XAU" in sym.upper() else .0003
    cl=[base]
    for _ in range(n-1): cl.append(cl[-1]*(1+np.random.normal(0,vol)))
    np.random.seed(int(time.time()*2)%10000)
    cl[-1]*=(1+np.random.normal(0,vol*.3))
    out=[]; now=datetime.now()
    for i in range(n):
        t=now-timedelta(minutes=interval_min*(n-1-i))
        o=cl[i-1] if i>0 else cl[i]; c=cl[i]
        r=abs(c-o)*(1+abs(np.random.normal(0,.4)))
        h=max(o,c)+r*.35; l=min(o,c)-r*.35
        out.append({"time":t.isoformat(),"open":round(o,5),"high":round(h,5),
                     "low":round(max(l,.1),5),"close":round(c,5),
                     "volume":int(np.random.exponential(2000))})
    return out

# ─────────────────────────────────────────────────────────────────────────────
#  BUILDERS GRAPHES
# ─────────────────────────────────────────────────────────────────────────────

def _df(candles):
    if not candles: return pd.DataFrame()
    df=pd.DataFrame(candles)
    df["time"]=pd.to_datetime(df["time"])
    return df


def _zones_on(fig, zones, row=1):
    s=zones.get("support",0); r=zones.get("resistance",0)
    if s: fig.add_hline(y=s,row=row,col=1,line=dict(color="rgba(0,212,170,.4)",width=1,dash="dot"),annotation_text="S",annotation_font=dict(color="#00d4aa",size=8))
    if r: fig.add_hline(y=r,row=row,col=1,line=dict(color="rgba(255,77,106,.4)",width=1,dash="dot"),annotation_text="R",annotation_font=dict(color="#ff4d6a",size=8))
    for fvg in zones.get("fvg_bullish",[]): fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,fillcolor="rgba(0,212,170,.07)",line=dict(color="rgba(0,212,170,.18)",width=.5))
    for fvg in zones.get("fvg_bearish",[]): fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,fillcolor="rgba(255,77,106,.07)",line=dict(color="rgba(255,77,106,.18)",width=.5))
    ob=zones.get("ob_buy");   
    if ob: fig.add_hline(y=ob,row=row,col=1,line=dict(color="rgba(0,212,170,.6)",width=1.2),annotation_text="OB↑",annotation_font=dict(color="#00d4aa",size=8))
    ob=zones.get("ob_sell")
    if ob: fig.add_hline(y=ob,row=row,col=1,line=dict(color="rgba(255,77,106,.6)",width=1.2),annotation_text="OB↓",annotation_font=dict(color="#ff4d6a",size=8))


def build_chart(candles, symbol, color, tf, signal=None, zones=None, show_zones=True):
    df = _df(candles)
    tf_lbl = {"M5":"5 Min","M15":"15 Min","H1":"1 Hour"}.get(tf,tf)

    if df.empty:
        fig=go.Figure()
        fig.update_layout(paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],height=380,
                          margin=dict(l=0,r=8,t=28,b=0),font=dict(color=C["text"]))
        fig.add_annotation(text="⏳ En attente…",xref="paper",yref="paper",
                            x=.5,y=.5,font=dict(color=C["text"],size=12),showarrow=False)
        return fig

    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,
                       vertical_spacing=.012,row_heights=[.8,.2])

    # Candles
    fig.add_trace(go.Candlestick(
        x=df["time"],open=df["open"],high=df["high"],low=df["low"],close=df["close"],
        name=symbol,
        increasing=dict(line=dict(color=C["green"],width=1),fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],  width=1),fillcolor=C["red"]),
        whiskerwidth=.18,
    ),row=1,col=1)

    # EMAs
    e20=df["close"].ewm(span=20).mean()
    e50=df["close"].ewm(span=50).mean()
    fig.add_trace(go.Scatter(x=df["time"],y=e20,name="EMA20",
        line=dict(color=color,width=1,dash="dot"),opacity=.65),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=e50,name="EMA50",
        line=dict(color="rgba(255,255,255,.16)",width=.8),opacity=.5),row=1,col=1)

    # Zones
    if show_zones and zones:
        _zones_on(fig,zones,row=1)

    # Prix live
    lp=float(df["close"].iloc[-1])
    fig.add_hline(y=lp,row=1,col=1,line=dict(color=color,width=.7,dash="dash"),opacity=.4)
    fig.add_annotation(x=df["time"].iloc[-1],y=lp,
        text=f"  {lp:,.2f}",
        font=dict(color=color,size=9.5,family="JetBrains Mono"),
        showarrow=False,xanchor="left",
        bgcolor="rgba(8,11,15,.9)",bordercolor=color,borderwidth=1,borderpad=2,
        row=1,col=1)

    # Signal marker
    if signal and signal.get("direction") in ("BUY","SELL"):
        lt=df["time"].iloc[-1]
        if signal["direction"]=="BUY":
            fig.add_trace(go.Scatter(x=[lt],y=[lp*.9993],mode="markers+text",
                marker=dict(symbol="triangle-up",size=12,color=C["green"]),
                text=["▲ BUY"],textposition="bottom center",
                textfont=dict(color=C["green"],size=8),showlegend=False),row=1,col=1)
        else:
            fig.add_trace(go.Scatter(x=[lt],y=[lp*1.0007],mode="markers+text",
                marker=dict(symbol="triangle-down",size=12,color=C["red"]),
                text=["▼ SELL"],textposition="top center",
                textfont=dict(color=C["red"],size=8),showlegend=False),row=1,col=1)
        if signal.get("tp"):
            fig.add_hline(y=signal["tp"],row=1,col=1,line=dict(color=C["green"],width=.7,dash="dash"),opacity=.5)
        if signal.get("sl"):
            fig.add_hline(y=signal["sl"],row=1,col=1,line=dict(color=C["red"],  width=.7,dash="dash"),opacity=.5)

    # Volume
    vc=[C["green"] if c>=o else C["red"] for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df["time"],y=df["volume"],marker=dict(color=vc,opacity=.4),showlegend=False),row=2,col=1)

    ax=dict(showgrid=True,gridcolor=C["grid"],gridwidth=1,zeroline=False,
            tickfont=dict(size=8,color=C["text"]),linecolor=C["grid"])
    fig.update_layout(
        paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],
        margin=dict(l=0,r=52,t=28,b=0),
        height=380,   # hauteur réduite → plus de place pour les autres éléments
        font=dict(family="JetBrains Mono",color=C["text"],size=8),
        legend=dict(orientation="h",x=0,y=1.08,bgcolor="rgba(0,0,0,0)",font=dict(size=8)),
        hovermode="x unified",xaxis_rangeslider_visible=False,
        title=dict(
            text=f'<b style="color:{color}">{symbol}</b><span style="color:{C["dim"]};font-size:8px"> ● {tf_lbl}</span>',
            x=.01,font=dict(size=11,family="Syne"),
        ),
        dragmode="pan",
    )
    fig.update_xaxes(**ax)
    fig.update_yaxes(**ax,tickformat=".5g")
    return fig


def build_gauge(corr):
    col=C["green"] if corr<-.5 else (C["red"] if corr>.5 else C["gold"])
    fig=go.Figure(go.Indicator(
        mode="gauge+number",value=corr,
        number=dict(font=dict(size=26,color=col,family="JetBrains Mono")),
        gauge=dict(
            axis=dict(range=[-1,1],tickwidth=1,tickcolor=C["text"],tickfont=dict(size=7),nticks=9),
            bar=dict(color=col,thickness=.18),bgcolor=C["bg"],bordercolor=C["grid"],borderwidth=1,
            steps=[dict(range=[-1,-.6],color="rgba(0,212,170,.09)"),
                   dict(range=[-.6,.6], color="rgba(247,181,41,.04)"),
                   dict(range=[.6,1],   color="rgba(255,77,106,.09)")],
        ),
        title=dict(text="CORR",font=dict(size=7,color=C["text"],family="JetBrains Mono")),
    ))
    fig.update_layout(paper_bgcolor=C["bg2"],height=140,margin=dict(l=8,r=8,t=22,b=4))
    return fig


def build_corr_hist(history):
    if not history: return go.Figure()
    fig=go.Figure()
    fig.add_trace(go.Scatter(
        x=[h["time"] for h in history],y=[h["corr"] for h in history],
        line=dict(color=C["gold"],width=1.1),fill="tozeroy",fillcolor="rgba(247,181,41,.04)"))
    for y,c in [(-.6,C["green"]),(0,C["text"]),(.6,C["red"])]:
        fig.add_hline(y=y,line=dict(color=c,width=.6,dash="dash"),opacity=.4)
    fig.update_layout(
        paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],
        height=130,margin=dict(l=0,r=8,t=6,b=0),
        font=dict(family="JetBrains Mono",color=C["text"],size=8),
        hovermode="x",showlegend=False,dragmode="pan",
        yaxis=dict(range=[-1.05,1.05],showgrid=True,gridcolor=C["grid"],zeroline=False,tickfont=dict(size=7)),
        xaxis=dict(showgrid=False,tickfont=dict(size=7)),
    )
    return fig


def _plt(fig, key, small=False):
    """Rendu Plotly — clé STABLE = pas de flash."""
    cfg={"displaylogo":False,"scrollZoom":not small,"displayModeBar":not small,
         "modeBarButtonsToRemove":["lasso2d","select2d","autoScale2d","toImage"] if not small else []}
    try:    st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except: st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)


# ─────────────────────────────────────────────────────────────────────────────
#  FETCH DATA
# ─────────────────────────────────────────────────────────────────────────────

_process_ws()

if not ss.ws_connected:
    snap=_http()
    if snap: _snap(snap)
    else:    _sim()

ss.tick += 1

tf     = ss.tf
tf_min = {"M5":5,"M15":15,"H1":60}[tf]
gold_c = ss.ohlcv.get(tf,[]) or _sim_ohlcv(200,tf_min,"XAUUSD")
dxy_c  = _sim_ohlcv(200,tf_min,"DXY")
signal = ss.signal
zones  = ss.zones
mtf    = ss.mtf
ws_ok  = ss.ws_connected
mt5_ok = ss.mt5_connected
sig_dir= signal.get("direction","WAIT")
ant    = signal.get("anticipation") or ""

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding:10px 0 12px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.05rem;
                    background:linear-gradient(90deg,#f7b529,#ffd166);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            ⚡ GOLD/DXY PRO
        </div>
        <div style="font-size:.55rem;color:#2e3a4e;letter-spacing:.1em;text-transform:uppercase;margin-top:1px;">
            Algo Trading Dashboard
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf_sel = st.radio("TF",["M5","M15","H1"],horizontal=True,
                       label_visibility="collapsed",
                       index=["M5","M15","H1"].index(ss.tf))
    if tf_sel != ss.tf: ss.tf = tf_sel

    st.markdown('<div class="lbl" style="margin-top:10px;">Affichage</div>', unsafe_allow_html=True)
    show_zones = st.checkbox("S/R · FVG · Order Blocks", value=ss.show_zones)
    ss.show_zones = show_zones

    st.markdown('<div class="lbl" style="margin-top:10px;">FVG Strength</div>', unsafe_allow_html=True)
    fvg_s = st.select_slider("FVG",options=["Faible","Normal","Fort"],value="Normal",label_visibility="collapsed")
    atr_v = zones.get("atr",0)
    mult  = {"Faible":.15,"Normal":.30,"Fort":.50}[fvg_s]
    n_fvg = len(zones.get("fvg_bullish",[]))+len(zones.get("fvg_bearish",[]))
    st.markdown(f'<div style="font-size:.56rem;color:#3d4a5e;margin-top:2px;">ATR×{mult} · {n_fvg} zones</div>',
                unsafe_allow_html=True)

    st.markdown("---")

    # Connexion
    d1  = "dot-p" if ws_ok  else "dot-r"
    d2  = "dot-g" if mt5_ok else "dot-y"
    url_short = API_URL[:30]+("…" if len(API_URL)>30 else "")
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,.06);
                border-radius:7px;padding:8px 10px;font-size:.65rem;">
        <div style="color:{'#a78bfa' if ws_ok else '#ff4d6a'};margin-bottom:3px;">
            <span class="{d1}"></span>WS {'ON' if ws_ok else 'OFF'}
        </div>
        <div style="color:{'#00d4aa' if mt5_ok else '#f7b529'};">
            <span class="{d2}"></span>MT5 {'Live' if mt5_ok else 'Sim'}
        </div>
        <div style="font-size:.54rem;color:#2e3a4e;margin-top:4px;">{url_short}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("")
    c1,c2=st.columns(2)
    with c1: st.metric("Winrate",f"{ss.winrate}%")
    with c2: st.metric("Trades", f"{ss.wins}W/{ss.losses}L")

    st.markdown(f"""
    <div style="font-size:.54rem;color:#2e3a4e;text-align:center;margin-top:8px;line-height:1.8;">
        {ss.gold_symbol} · {tf} · Tick#{ss.tick}<br>
        {datetime.now().strftime('%H:%M:%S')}
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER — compact, ne cache pas les graphes
# ─────────────────────────────────────────────────────────────────────────────

bc_map = {"BUY":"bb","SELL":"bs","WAIT":"bw"}
bc = bc_map[sig_dir]
ant_html = f'<span class="ba">{ant}</span>' if ant else ""
ws_lbl   = "WS Live" if ws_ok else "HTTP"
ws_col   = "#a78bfa" if ws_ok else "#f7b529"
dot_ws   = "dot-p" if ws_ok else "dot-r"

# Header en UNE seule ligne compacte
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:5px 0 7px;border-bottom:1px solid rgba(255,255,255,.06);
            margin-bottom:8px;">
    <div style="display:flex;align-items:center;gap:12px;">
        <div>
            <span style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.15rem;
                         background:linear-gradient(90deg,#f7b529,#ffd166);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                ⚡ GOLD/DXY PRO
            </span>
            <span style="font-size:.58rem;color:#6b7a94;margin-left:10px;">
                <span class="{dot_ws}"></span>
                <span style="color:{ws_col};">{ws_lbl}</span>
                &nbsp;·&nbsp;{'MT5 Live' if mt5_ok else 'Simulation'}
                &nbsp;·&nbsp;{tf}
            </span>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <span class="{bc}">{sig_dir}</span>
        {ant_html}
        <span style="font-size:.6rem;color:#6b7a94;">
            Conf:<b style="color:#dde3ee;">{signal.get('confidence',0)}%</b>
        </span>
        <span style="font-size:.95rem;font-weight:700;color:#dde3ee;margin-left:8px;">
            {datetime.now().strftime('%H:%M:%S')}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  METRICS — compactes sur 7 colonnes
# ─────────────────────────────────────────────────────────────────────────────

m = st.columns(7)
with m[0]: st.metric("XAUUSD",     f"{ss.gold_price:,.2f}",  f"{ss.gold_change:+.2f}({ss.gold_pct:+.2f}%)")
with m[1]: st.metric("DXY",        f"{ss.dxy_price:.3f}",    f"{ss.dxy_change:+.4f}")
with m[2]:
    cl="●Neg" if ss.correlation<-.6 else ("●Mod" if ss.correlation<0 else "●Pos")
    st.metric("Corr",f"{ss.correlation:+.4f}",cl)
with m[3]: st.metric("Signal",     f"{'🟢' if sig_dir=='BUY' else '🔴' if sig_dir=='SELL' else '⚪'} {sig_dir}",f"Conf:{signal.get('confidence',0)}%")
with m[4]: st.metric("Winrate",    f"{ss.winrate}%",          f"{ss.wins}W/{ss.losses}L")
with m[5]: st.metric("BID/ASK",    f"{ss.gold_bid:.2f}",      f"ASK {ss.gold_ask:.2f}")
with m[6]:
    st.metric("R/R",f"1:{signal.get('rr',0)}",f"SL:{signal.get('sl_source','—')}")

# ─────────────────────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────────────────────

t1,t2,t3,t4,t5 = st.tabs(["📊 Graphiques","🎯 Signal & Zones","🔀 Multi-TF","📋 Logs","📜 Historique"])

# ══════════════════════════════════════════════════════════
#  TAB 1 — GRAPHIQUES
#  Clés stables → Plotly update en place → ZÉRO flash
# ══════════════════════════════════════════════════════════
with t1:
    # Les deux graphes côte à côte — UNE SEULE FOIS chacun
    col_g, col_d = st.columns(2)
    with col_g:
        _plt(build_chart(gold_c,"XAUUSD",C["gold"],tf,
                          signal=signal,zones=zones,show_zones=ss.show_zones),
              key="gold_chart")   # clé fixe!
    with col_d:
        _plt(build_chart(dxy_c,"DXY",C["dxy"],tf),
              key="dxy_chart")    # clé fixe!

    # Corrélation sous les graphes
    cc1,cc2 = st.columns([1,2])
    with cc1:
        _plt(build_gauge(ss.correlation), key="gauge_tab1", small=True)
    with cc2:
        st.markdown('<div class="lbl" style="margin-top:4px;">Corrélation Rolling</div>',
                    unsafe_allow_html=True)
        _plt(build_corr_hist(ss.corr_history), key="corr_hist_tab1", small=True)

# ══════════════════════════════════════════════════════════
#  TAB 2 — SIGNAL & ZONES
# ══════════════════════════════════════════════════════════
with t2:
    s1,s2,s3 = st.columns([1,1,1.2])

    with s1:
        _plt(build_gauge(ss.correlation), key="gauge_tab2", small=True)
        if ss.correlation<-.65:   ic,it=C["green"],"✅ Forte — fiable"
        elif ss.correlation<-.4:  ic,it=C["gold"], "⚠️ Modérée — attendre"
        else:                     ic,it=C["red"],  "❌ Faible — éviter"
        st.markdown(f'<div style="font-size:.65rem;color:{ic};background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);border-radius:7px;padding:7px 9px;margin-top:4px;">{it}</div>',
                    unsafe_allow_html=True)

    with s2:
        bc2     = bc_map[signal.get("direction","WAIT")]
        dir2    = signal.get("direction","WAIT")
        ant2    = signal.get("anticipation") or ""
        ant2_h  = f'<span class="ba">{ant2}</span>' if ant2 else ""
        conf2   = signal.get("confidence",0)
        pipe2   = signal.get("pipeline_state","IDLE")
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;gap:7px;align-items:center;margin-bottom:9px;">
                <span class="{bc2}" style="font-size:.75rem;padding:3px 12px;">{dir2}</span>
                {ant2_h}
            </div>
            <div style="font-size:.66rem;color:#6b7a94;line-height:2.1;">
                Confiance: <b style="color:#dde3ee;">{conf2}%</b><br>
                Corr: <b style="color:#dde3ee;">{signal.get('corr',0):+.4f}</b><br>
                Gold: <b style="color:#f7b529;">{signal.get('gold_price',0):,.2f}</b><br>
                DXY:  <b style="color:#4da6ff;">{signal.get('dxy_price',0):.3f}</b><br>
                Pipeline: <b style="color:#dde3ee;">{pipe2}</b>
            </div>
        </div>""", unsafe_allow_html=True)

        if dir2 in ("BUY","SELL"):
            entry=signal.get("entry",0);tp=signal.get("tp",0)
            sl=signal.get("sl",0);rr=signal.get("rr",0)
            st.markdown(f"""
            <div class="card" style="border-color:rgba(247,181,41,.2);">
                <div class="lbl" style="margin-bottom:7px;">Niveaux</div>
                <div style="font-size:.68rem;line-height:2.1;">
                    <span style="color:#6b7a94;">Entrée:</span><b style="color:#dde3ee;float:right;">{entry:,.2f}</b><br>
                    <span style="color:#00d4aa;">TP:</span><b style="color:#00d4aa;float:right;">{tp:,.2f}</b><br>
                    <span style="color:#ff4d6a;">SL:</span><b style="color:#ff4d6a;float:right;">{sl:,.2f}</b><br>
                    <span style="color:#6b7a94;">R/R:</span><b style="color:#f7b529;float:right;">1:{rr}</b>
                </div>
            </div>""", unsafe_allow_html=True)

        if ant2:
            st.markdown(f"""
            <div style="background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.3);
                        border-radius:8px;padding:9px 11px;margin-top:5px;">
                <div style="font-size:.56rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:3px;">MODE ANTICIPATION</div>
                <div style="font-size:.68rem;color:#c4b5fd;">{ant2}</div>
                <div style="font-size:.6rem;color:#6b7a94;margin-top:3px;">
                    {"DXY↓ → anticiper BUY" if "BUY" in ant2 else "DXY↑ → anticiper SELL"}<br>
                    ⏳ Attendre confirmation
                </div>
            </div>""", unsafe_allow_html=True)

    with s3:
        atr=zones.get("atr",0); ff=zones.get("fvg_filter",0)
        sup=zones.get("support",0); res=zones.get("resistance",0)
        ob_b=zones.get("ob_buy"); ob_s=zones.get("ob_sell")
        st.markdown(f"""
        <div class="card">
            <div class="lbl" style="margin-bottom:7px;">S/R</div>
            <div style="font-size:.68rem;line-height:2.1;">
                <span style="color:#6b7a94;">Support:</span><b style="color:#00d4aa;float:right;">{sup:,.2f}</b><br>
                <span style="color:#6b7a94;">Résistance:</span><b style="color:#ff4d6a;float:right;">{res:,.2f}</b><br>
                <span style="color:#6b7a94;">ATR:</span><b style="color:#f7b529;float:right;">{atr:.3f}</b><br>
                <span style="color:#6b7a94;">FVG Filter:</span><b style="color:#a78bfa;float:right;">{ff:.3f}</b>
            </div>
        </div>
        <div class="card">
            <div class="lbl" style="margin-bottom:7px;">FVG & OB</div>
            <div style="font-size:.68rem;line-height:2.1;">
                <span style="color:#6b7a94;">FVG Bull:</span><b style="color:#00d4aa;float:right;">{len(zones.get('fvg_bullish',[]))} zones</b><br>
                <span style="color:#6b7a94;">FVG Bear:</span><b style="color:#ff4d6a;float:right;">{len(zones.get('fvg_bearish',[]))} zones</b><br>
                <span style="color:#6b7a94;">OB Buy:</span><b style="color:#00d4aa;float:right;">{ob_b or '—'}</b><br>
                <span style="color:#6b7a94;">OB Sell:</span><b style="color:#ff4d6a;float:right;">{ob_s or '—'}</b>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  TAB 3 — MULTI-TF
# ══════════════════════════════════════════════════════════
with t3:
    mc = st.columns(3)
    for col,tf_n in zip(mc,["H1","M15","M5"]):
        d=mtf.get(tf_n,{})
        sig=d.get("signal","WAIT"); cr=d.get("corr",0.); tr=d.get("trend","—")
        at=d.get("anticipation") or ""
        bc3=bc_map.get(sig,"bw")
        cc=C["green"] if cr<-.6 else (C["gold"] if cr<0 else C["red"])
        at_html=f'<br><span style="color:#a78bfa;font-size:.6rem;">{at}</span>' if at else ""
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;color:#dde3ee;margin-bottom:7px;">{tf_n}</div>
                <span class="{bc3}">{sig}</span>
                <div style="font-size:.65rem;color:#6b7a94;line-height:2.1;margin-top:7px;text-align:left;">
                    Corr: <b style="color:{cc};float:right;">{cr:+.4f}</b><br>
                    Trend: <b style="color:#dde3ee;float:right;">{tr}</b>{at_html}
                </div>
            </div>""", unsafe_allow_html=True)

    sigs=[mtf.get(t,{}).get("signal","WAIT") for t in ["H1","M15","M5"]]
    buys=sigs.count("BUY"); sells=sigs.count("SELL")
    if buys>=2:    cons,cc2="🟢 CONSENSUS BUY",C["green"]
    elif sells>=2: cons,cc2="🔴 CONSENSUS SELL",C["red"]
    else:          cons,cc2="⚪ PAS DE CONSENSUS",C["gold"]
    st.markdown(f"""
    <div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);
                border-radius:9px;padding:12px;text-align:center;margin-top:8px;">
        <div style="font-size:.7rem;color:{cc2};font-weight:700;">{cons}</div>
        <div style="font-size:.58rem;color:#2e3a4e;margin-top:3px;">H1:{sigs[0]} · M15:{sigs[1]} · M5:{sigs[2]}</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  TAB 4 — LOGS
# ══════════════════════════════════════════════════════════
with t4:
    lc1,lc2=st.columns([3,1])
    with lc1: st.markdown('<div class="lbl">Logs Bot</div>', unsafe_allow_html=True)
    with lc2: lf=st.selectbox("Filtre",["ALL","SIGNAL","WARNING","ERROR"],label_visibility="collapsed")
    logs=ss.bot_logs
    filtered=[l for l in reversed(logs) if lf=="ALL" or l.get("level")==lf]
    html='<div style="background:#0d1117;border:1px solid rgba(255,255,255,.06);border-radius:7px;padding:10px;height:290px;overflow-y:auto;font-size:.62rem;line-height:1.85;">'
    for e in filtered[:80]:
        lvl=e.get("level","INFO").upper()
        col={"INFO":"#6b7a94","WARNING":"#f7b529","ERROR":"#ff4d6a","SIGNAL":"#00d4aa"}.get(lvl,"#6b7a94")
        html+=f'<div><span style="color:#2e3a4e;">{e.get("time","")}</span> <span style="color:{col};font-weight:600;">[{lvl}]</span> <span style="color:#9ca3af;">{e.get("msg","")}</span></div>'
    html+="</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown(f'<div style="margin-top:6px;font-size:.62rem;color:{"#00d4aa" if ss.bot_status=="running" else "#f7b529"};">Bot:{ss.bot_status} · MT5:{"✅" if mt5_ok else "⚠️"} · WS:{"🟣" if ws_ok else "🔴"}</div>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  TAB 5 — HISTORIQUE
# ══════════════════════════════════════════════════════════
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
            try:    st.dataframe(st2,width="stretch",height=280)
            except: st.dataframe(st2,use_container_width=True,height=280)
        except:
            try:    st.dataframe(df_s[cols],width="stretch",height=280)
            except: st.dataframe(df_s[cols],use_container_width=True,height=280)
    else:
        st.markdown('<div style="text-align:center;padding:35px;color:#2e3a4e;font-size:.72rem;">Aucun signal enregistré.</div>',
                    unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  FOOTER + RERUN
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="text-align:center;padding:5px 0 2px;font-size:.5rem;color:#1a2234;
            border-top:1px solid rgba(255,255,255,.04);margin-top:6px;">
    Gold/DXY Pro v4 · {'🟣WS' if ws_ok else '🟡HTTP'} · Tick#{ss.tick} · {API_URL[:35]}
</div>""", unsafe_allow_html=True)

time.sleep(REFRESH_S)
st.rerun()
