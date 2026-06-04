"""
GOLD/DXY PRO — Dashboard v12
Corrections :
- Prix Gold réel Exness (pas simulation)
- KeyError equity chart corrigé
- Signal & Zones confiance/lot corrects
- Onglet Backtest complet
- Sync WIN/LOSS automatique
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

st.set_page_config(page_title="GOLD/DXY Pro", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

API_URL   = "https://en-ligne-5wi6.onrender.com"
API_KEY   = "gold_dxy_secret_2024"
HEADERS   = {"X-API-Key": API_KEY}
REFRESH_S = 2

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Syne:wght@700;800&display=swap');
:root{--bg:#080b0f;--bg2:#0d1117;--glass:rgba(255,255,255,0.03);--border:rgba(255,255,255,0.07);
--gold:#f7b529;--green:#00d4aa;--red:#ff4d6a;--blue:#4da6ff;--purple:#a78bfa;
--text:#dde3ee;--muted:#6b7a94;--dim:#2e3a4e;}
html,body,[class*="css"]{font-family:'JetBrains Mono',monospace!important;background:var(--bg)!important;color:var(--text)!important;}
.main .block-container{padding:0.4rem 0.9rem 0.8rem!important;max-width:100%!important;}
#MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0c1018,#080b0f)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebarCollapseButton"]{display:none!important;}
[data-testid="metric-container"]{background:var(--glass)!important;border:1px solid var(--border)!important;border-radius:7px!important;padding:6px 10px!important;}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-size:.53rem!important;letter-spacing:.07em!important;text-transform:uppercase!important;}
[data-testid="stMetricValue"]{font-size:.9rem!important;font-weight:700!important;}
[data-testid="stMetricDelta"]{font-size:.57rem!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--glass)!important;border:1px solid var(--border)!important;border-radius:7px!important;padding:3px!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;border-radius:5px!important;color:var(--muted)!important;font-size:.68rem!important;padding:4px 12px!important;}
.stTabs [aria-selected="true"]{background:rgba(247,181,41,.14)!important;color:var(--gold)!important;}
.card{background:var(--glass);border:1px solid var(--border);border-radius:7px;padding:9px 11px;margin-bottom:6px;}
.card-gld{border-color:rgba(247,181,41,.3)!important;}
.bb{display:inline-block;background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:#00d4aa;border-radius:4px;padding:2px 8px;font-size:.64rem;font-weight:700;}
.bs{display:inline-block;background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:#ff4d6a;border-radius:4px;padding:2px 8px;font-size:.64rem;font-weight:700;}
.bw{display:inline-block;background:rgba(107,122,148,.1);border:1px solid rgba(107,122,148,.25);color:#6b7a94;border-radius:4px;padding:2px 8px;font-size:.64rem;font-weight:700;}
.ba{display:inline-block;background:rgba(167,139,250,.12);border:1px solid rgba(167,139,250,.4);color:#a78bfa;border-radius:4px;padding:2px 8px;font-size:.62rem;font-weight:700;}
.bwin{display:inline-block;background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:#00d4aa;border-radius:4px;padding:2px 8px;font-size:.62rem;font-weight:700;}
.bloss{display:inline-block;background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:#ff4d6a;border-radius:4px;padding:2px 8px;font-size:.62rem;font-weight:700;}
.bopen{display:inline-block;background:rgba(247,181,41,.12);border:1px solid rgba(247,181,41,.3);color:#f7b529;border-radius:4px;padding:2px 8px;font-size:.62rem;font-weight:700;}
.dg{display:inline-block;width:6px;height:6px;background:#00d4aa;border-radius:50%;box-shadow:0 0 5px #00d4aa;animation:pulse 1.4s infinite;margin-right:4px;}
.dr{display:inline-block;width:6px;height:6px;background:#ff4d6a;border-radius:50%;margin-right:4px;}
.dy{display:inline-block;width:6px;height:6px;background:#f7b529;border-radius:50%;margin-right:4px;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(1.6)}}
.lbl{font-size:.52rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin-bottom:3px;}
hr{border-color:var(--border)!important;margin:7px 0!important;}
::-webkit-scrollbar{width:3px;height:3px;}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
</style>
""", unsafe_allow_html=True)

C = {"bg":"#080b0f","bg2":"#0d1117","grid":"rgba(255,255,255,0.03)",
     "text":"#6b7a94","dim":"#2e3a4e","gold":"#f7b529","dxy":"#4da6ff",
     "green":"#00d4aa","red":"#ff4d6a","muted":"#6b7a94"}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
_INIT = {
    "tick":0,"tf":"M5","show_zones":True,
    "gold_price":0.0,"dxy_price":0.0,"gold_bid":0.0,"gold_ask":0.0,
    "gold_change":0.0,"gold_pct":0.0,"dxy_change":0.0,"correlation":-0.75,
    "signal":{"direction":"WAIT","anticipation":None,"confidence":0,"corr":-0.75,
              "gold_price":0.0,"dxy_price":0.0,"entry":0.0,"tp":0.0,"sl":0.0,
              "rr":0.0,"lot":0.0,"sl_source":"—","pipeline_state":"IDLE","result":""},
    "signals":[],"bot_logs":[{"time":"--:--","level":"INFO","msg":"Démarrage..."}],
    "mtf":{"H1":{"signal":"WAIT","corr":0.0,"trend":"—"},
           "M15":{"signal":"WAIT","corr":0.0,"trend":"—"},
           "M5":{"signal":"WAIT","corr":0.0,"trend":"—"}},
    "ohlcv":{"M5":[],"M15":[],"H1":[]},
    "zones":{"support":0.0,"resistance":0.0,"fvg_bullish":[],"fvg_bearish":[],
             "ob_buy":None,"ob_sell":None,"atr":0.0,"fvg_filter":0.0},
    "winrate":0.0,"wins":0,"losses":0,
    "bot_status":"unknown","mt5_connected":False,"gold_symbol":"XAUUSD","last_update":"—",
    "bt_stats":{},"bt_trades":[],"bt_equity":[],"bt_patterns":{},
}
for k,v in _INIT.items():
    if k not in st.session_state: st.session_state[k]=v
ss = st.session_state
if not isinstance(ss.signal, dict): ss.signal = _INIT["signal"]
if not isinstance(ss.zones,  dict): ss.zones  = _INIT["zones"]
if ss.tf not in ["M5","M15","H1"]:  ss.tf     = "M5"

# ── HTTP ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_S)
def _http_snap():
    if not HAS_REQ: return None
    try:
        r = _req.get(f"{API_URL}/api/snapshot", headers=HEADERS, timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def _apply(d: Dict):
    if not isinstance(d, dict): return
    for k in ["gold_price","dxy_price","gold_bid","gold_ask","gold_change","gold_pct",
               "dxy_change","correlation","signals","bot_logs","winrate","wins","losses",
               "bot_status","mt5_connected","gold_symbol","last_update","zones"]:
        if k in d: ss[k] = d[k]
    if "signal" in d and isinstance(d["signal"], dict):
        ss.signal = {**_INIT["signal"], **d["signal"]}
    if "mtf_analysis" in d: ss.mtf = d["mtf_analysis"]
    if "mtf" in d:          ss.mtf = d["mtf"]
    if "ohlcv" in d:
        for tf, c in d["ohlcv"].items():
            if c: ss.ohlcv[tf] = c
    if "backtest_stats"    in d and d["backtest_stats"]:    ss.bt_stats    = d["backtest_stats"]
    if "backtest_trades"   in d and d["backtest_trades"]:   ss.bt_trades   = d["backtest_trades"]
    if "backtest_equity"   in d and d["backtest_equity"]:   ss.bt_equity   = d["backtest_equity"]
    if "backtest_patterns" in d and d["backtest_patterns"]: ss.bt_patterns = d["backtest_patterns"]

def _sim_ohlcv(n, mins, sym, base_price=None):
    """Simulation OHLCV centrée sur le vrai prix reçu."""
    np.random.seed(hash(sym) % 9999)
    if base_price is None:
        base = 4613.0 if "XAU" in sym.upper() else 104.5
    else:
        base = base_price
    vol = 0.0006 if "XAU" in sym.upper() else 0.0003
    cl  = [base]
    for _ in range(n-1):
        cl.append(cl[-1]*(1+np.random.normal(0, vol)))
    # Ancre la dernière valeur au prix réel
    if base_price:
        offset = base_price - cl[-1]
        cl = [c + offset for c in cl]
    out, now = [], datetime.now()
    for i in range(n):
        t = now - timedelta(minutes=mins*(n-1-i))
        o = cl[i-1] if i>0 else cl[i]; c = cl[i]
        r = abs(c-o)*(1+abs(np.random.normal(0,.4)))
        h = max(o,c)+r*.35; l = min(o,c)-r*.35
        out.append({"time":t.isoformat(),"open":round(o,2),"high":round(h,2),
                    "low":round(max(l,.1),2),"close":round(c,2),
                    "volume":int(np.random.exponential(2000))})
    return out

def _rolling_corr(gold_c, dxy_c, window=50):
    n = min(len(gold_c), len(dxy_c))
    if n < window+5: return []
    g=[c["close"] for c in gold_c[-n:]]; d=[c["close"] for c in dxy_c[-n:]]
    t=[c["time"]  for c in gold_c[-n:]]
    out=[]
    for i in range(window, n):
        ga=np.array(g[i-window:i]); da=np.array(d[i-window:i])
        corr=float(np.corrcoef(ga,da)[0,1]) if np.std(ga)>1e-10 and np.std(da)>1e-10 else 0.0
        out.append({"time":t[i],"corr":round(corr,4)})
    return out

# ── FETCH ─────────────────────────────────────────────────────────────────────
snap = _http_snap()
if snap:
    _apply(snap)
    api_ok = True
else:
    api_ok = False
    # Simulation centrée sur le dernier prix connu
    if ss.gold_price == 0: ss.gold_price = 4613.0
    if ss.dxy_price  == 0: ss.dxy_price  = 104.5

ss.tick += 1
tf     = ss.tf
tf_min = {"M5":5,"M15":15,"H1":60}[tf]

# Prix Gold : toujours utilise le vrai prix de l'API si disponible
gold_price_real = ss.gold_price if ss.gold_price > 100 else 4613.0

# OHLCV Gold : utilise données API sinon simulation ancrée au vrai prix
gold_c = ss.ohlcv.get(tf, [])
if not gold_c:
    gold_c = _sim_ohlcv(200, tf_min, "XAUUSD", base_price=gold_price_real)

# DXY toujours simulé (pas dispo en OHLCV)
dxy_c = _sim_ohlcv(200, tf_min, "DXY", base_price=ss.dxy_price if ss.dxy_price > 0 else 104.5)

signal     = ss.signal if isinstance(ss.signal, dict) else _INIT["signal"]
zones      = ss.zones  if isinstance(ss.zones,  dict) else _INIT["zones"]
mtf        = ss.mtf
mt5_ok     = ss.mt5_connected
sig_dir    = signal.get("direction","WAIT")
sig_result = signal.get("result","")
ant        = signal.get("anticipation") or ""
BC         = {"BUY":"bb","SELL":"bs","WAIT":"bw"}
corr_data  = _rolling_corr(gold_c, dxy_c, window=50)

# Order Blocks
def _to_df(candles):
    if not candles: return pd.DataFrame()
    df = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    return df

def detect_obs(df, swing_len=5):
    if df.empty or len(df) < swing_len*2+1:
        return {"bullish_obs":[],"bearish_obs":[]}
    highs=df["high"].values; lows=df["low"].values
    opens=df["open"].values; closes=df["close"].values
    vols=df.get("volume",pd.Series(np.ones(len(df)))).values
    times=df["time"].values; n=len(df)
    def _sh(i): return (i>=swing_len and i<n-swing_len and
        all(highs[i]>=highs[i-j] for j in range(1,swing_len+1)) and
        all(highs[i]>=highs[i+j] for j in range(1,swing_len+1)))
    def _sl(i): return (i>=swing_len and i<n-swing_len and
        all(lows[i]<=lows[i-j]  for j in range(1,swing_len+1)) and
        all(lows[i]<=lows[i+j]  for j in range(1,swing_len+1)))
    shs=[i for i in range(swing_len,n-swing_len) if _sh(i)]
    sls=[i for i in range(swing_len,n-swing_len) if _sl(i)]
    bull_obs=[]; bear_obs=[]
    for sh in shs:
        win=range(max(0,sh-swing_len*2),sh)
        bc=[(i,vols[i]) for i in win if closes[i]>opens[i]]
        if not bc: continue
        idx=max(bc,key=lambda x:x[1])[0]
        avg=(highs[idx]+lows[idx])/2
        ob={"type":"bearish","top":float(highs[idx]),"bottom":float(lows[idx]),"avg":float(avg),
            "time":times[idx],"time_end":times[min(sh+swing_len,n-1)],"mitigated":False}
        ob["mitigated"]=bool(np.any(highs[sh:]>=avg))
        bear_obs.append(ob)
    for sl in sls:
        win=range(max(0,sl-swing_len*2),sl)
        bc=[(i,vols[i]) for i in win if closes[i]<opens[i]]
        if not bc: continue
        idx=max(bc,key=lambda x:x[1])[0]
        avg=(highs[idx]+lows[idx])/2
        ob={"type":"bullish","top":float(highs[idx]),"bottom":float(lows[idx]),"avg":float(avg),
            "time":times[idx],"time_end":times[min(sl+swing_len,n-1)],"mitigated":False}
        ob["mitigated"]=bool(np.any(lows[sl:]<=avg))
        bull_obs.append(ob)
    bull_obs=sorted([o for o in bull_obs if not o["mitigated"]],key=lambda x:str(x["time"]),reverse=True)[:3]
    bear_obs=sorted([o for o in bear_obs if not o["mitigated"]],key=lambda x:str(x["time"]),reverse=True)[:3]
    return {"bullish_obs":bull_obs,"bearish_obs":bear_obs}

gold_df  = _to_df(gold_c)
gold_obs = detect_obs(gold_df) if not gold_df.empty else {"bullish_obs":[],"bearish_obs":[]}
n_ob_b   = len(gold_obs.get("bullish_obs",[]))
n_ob_s   = len(gold_obs.get("bearish_obs",[]))

def result_badge(r):
    if r=="WIN":  return '<span class="bwin">✅ WIN</span>'
    if r=="LOSS": return '<span class="bloss">❌ LOSS</span>'
    if r=="OPEN": return '<span class="bopen">🔵 OPEN</span>'
    return ""

# ── GRAPHIQUES ────────────────────────────────────────────────────────────────
def draw_obs(fig, obs_data, row=1, col=1):
    for ob in obs_data.get("bullish_obs",[]):
        try:
            fig.add_shape(type="rect",x0=ob["time"],x1=ob["time_end"],
                y0=ob["bottom"],y1=ob["top"],row=row,col=col,
                line=dict(color="rgba(0,212,170,0.6)",width=1),fillcolor="rgba(0,212,170,0.08)")
            fig.add_annotation(x=ob["time_end"],y=ob["top"],text="OB↑",showarrow=False,
                font=dict(color="#00d4aa",size=8),xanchor="left",yanchor="bottom",row=row,col=col)
        except Exception: pass
    for ob in obs_data.get("bearish_obs",[]):
        try:
            fig.add_shape(type="rect",x0=ob["time"],x1=ob["time_end"],
                y0=ob["bottom"],y1=ob["top"],row=row,col=col,
                line=dict(color="rgba(255,77,106,0.6)",width=1),fillcolor="rgba(255,77,106,0.08)")
            fig.add_annotation(x=ob["time_end"],y=ob["bottom"],text="OB↓",showarrow=False,
                font=dict(color="#ff4d6a",size=8),xanchor="left",yanchor="top",row=row,col=col)
        except Exception: pass
    return fig

def draw_zones(fig, z, row=1):
    s=z.get("support",0); r=z.get("resistance",0)
    if s: fig.add_hline(y=s,row=row,col=1,line=dict(color="rgba(0,212,170,.45)",width=1,dash="dot"),
          annotation_text="S",annotation_font=dict(color="#00d4aa",size=8))
    if r: fig.add_hline(y=r,row=row,col=1,line=dict(color="rgba(255,77,106,.45)",width=1,dash="dot"),
          annotation_text="R",annotation_font=dict(color="#ff4d6a",size=8))
    for fvg in z.get("fvg_bullish",[]):
        try: fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,
             fillcolor="rgba(0,212,170,.08)",line=dict(color="rgba(0,212,170,.2)",width=.5))
        except: pass
    for fvg in z.get("fvg_bearish",[]):
        try: fig.add_hrect(y0=fvg["low"],y1=fvg["high"],row=row,col=1,
             fillcolor="rgba(255,77,106,.08)",line=dict(color="rgba(255,77,106,.2)",width=.5))
        except: pass
    if z.get("ob_buy"):  fig.add_hline(y=z["ob_buy"],  row=row,col=1,line=dict(color="rgba(0,212,170,.65)",width=1.2),annotation_text="OB↑",annotation_font=dict(color="#00d4aa",size=8))
    if z.get("ob_sell"): fig.add_hline(y=z["ob_sell"], row=row,col=1,line=dict(color="rgba(255,77,106,.65)",width=1.2),annotation_text="OB↓",annotation_font=dict(color="#ff4d6a",size=8))

def build_candle(candles, symbol, color, tf, signal=None, zones=None, show_zones=True, obs_data=None):
    df=_to_df(candles)
    tf_lbl={"M5":"5 Min","M15":"15 Min","H1":"1 Hour"}.get(tf,tf)
    if df.empty:
        fig=go.Figure()
        fig.update_layout(paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],height=360,margin=dict(l=0,r=8,t=26,b=0))
        fig.add_annotation(text="⏳ En attente…",xref="paper",yref="paper",x=.5,y=.5,font=dict(color=C["text"],size=12),showarrow=False)
        return fig
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.01,row_heights=[.8,.2])
    fig.add_trace(go.Candlestick(x=df["time"],open=df["open"],high=df["high"],low=df["low"],close=df["close"],name=symbol,
        increasing=dict(line=dict(color=C["green"],width=1),fillcolor=C["green"]),
        decreasing=dict(line=dict(color=C["red"],width=1),fillcolor=C["red"]),whiskerwidth=.18),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=df["close"].ewm(span=20).mean(),name="EMA20",line=dict(color=color,width=1,dash="dot"),opacity=.65),row=1,col=1)
    fig.add_trace(go.Scatter(x=df["time"],y=df["close"].ewm(span=50).mean(),name="EMA50",line=dict(color="rgba(255,255,255,.16)",width=.8),opacity=.5),row=1,col=1)
    if show_zones and zones: draw_zones(fig,zones,row=1)
    lp=float(df["close"].iloc[-1])
    fig.add_hline(y=lp,row=1,col=1,line=dict(color=color,width=.8,dash="dash"),opacity=.5)
    if signal and signal.get("direction") in ("BUY","SELL"):
        lt=df["time"].iloc[-1]; up=signal["direction"]=="BUY"
        fig.add_trace(go.Scatter(x=[lt],y=[lp*(.9993 if up else 1.0007)],mode="markers",
            marker=dict(symbol="triangle-up" if up else "triangle-down",size=12,color=C["green"] if up else C["red"]),showlegend=False),row=1,col=1)
        if signal.get("tp"): fig.add_hline(y=signal["tp"],row=1,col=1,line=dict(color=C["green"],width=.7,dash="dash"),opacity=.5)
        if signal.get("sl"): fig.add_hline(y=signal["sl"],row=1,col=1,line=dict(color=C["red"],width=.7,dash="dash"),opacity=.5)
    vol_col=df.get("volume",None)
    if vol_col is None and "tick_volume" in df.columns: vol_col=df["tick_volume"]
    if vol_col is None: vol_col=pd.Series(np.zeros(len(df)))
    vc=[C["green"] if c>=o else C["red"] for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df["time"],y=vol_col,marker=dict(color=vc,opacity=.4),showlegend=False),row=2,col=1)
    if show_zones and obs_data: fig=draw_obs(fig,obs_data,row=1,col=1)
    ax=dict(showgrid=True,gridcolor=C["grid"],gridwidth=1,zeroline=False,tickfont=dict(size=8,color=C["text"]),linecolor=C["grid"])
    fig.update_layout(paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],margin=dict(l=0,r=8,t=28,b=0),height=360,
        font=dict(family="JetBrains Mono",color=C["text"],size=8),
        legend=dict(orientation="h",x=0,y=1.1,bgcolor="rgba(0,0,0,0)",font=dict(size=8)),
        hovermode="x unified",xaxis_rangeslider_visible=False,
        title=dict(text=f'<b style="color:{color}">{symbol}</b><span style="color:{C["dim"]};font-size:8px"> ● {tf_lbl}</span>  <span style="color:{color};font-weight:700"> {lp:,.2f}</span>',
                   x=.01,font=dict(size=11,family="Syne")),dragmode="pan")
    fig.update_xaxes(**ax); fig.update_yaxes(**ax,tickformat=".5g")
    return fig

def build_gauge(corr):
    col=C["green"] if corr<-.5 else (C["red"] if corr>.5 else C["gold"])
    fig=go.Figure(go.Indicator(mode="gauge+number",value=corr,
        number=dict(font=dict(size=24,color=col,family="JetBrains Mono")),
        gauge=dict(axis=dict(range=[-1,1],tickfont=dict(size=7),nticks=9),
                   bar=dict(color=col,thickness=.18),bgcolor=C["bg"],bordercolor=C["grid"],borderwidth=1,
                   steps=[dict(range=[-1,-.6],color="rgba(0,212,170,.08)"),
                          dict(range=[-.6,.6],color="rgba(247,181,41,.04)"),
                          dict(range=[.6,1],color="rgba(255,77,106,.08)")]),
        title=dict(text="CORR",font=dict(size=7,color=C["text"]))))
    fig.update_layout(paper_bgcolor=C["bg2"],height=140,margin=dict(l=8,r=8,t=20,b=4))
    return fig

def build_corr_chart(corr_data):
    fig=go.Figure()
    if corr_data:
        times=[d["time"] for d in corr_data]; corrs=[d["corr"] for d in corr_data]
        fig.add_trace(go.Scatter(x=times,y=corrs,line=dict(color=C["gold"],width=1.5),
            fill="tozeroy",fillcolor="rgba(247,181,41,.06)"))
        for y,c,lbl in [(-.6,C["green"],"-0.6"),(0,C["text"],"0"),(.6,C["red"],"0.6")]:
            fig.add_hline(y=y,line=dict(color=c,width=.8,dash="dot"),opacity=.55,
                annotation_text=lbl,annotation_position="left",annotation_font=dict(color=c,size=8))
    else:
        fig.add_annotation(text="En attente OHLCV…",xref="paper",yref="paper",x=.5,y=.5,font=dict(color=C["text"],size=11),showarrow=False)
    fig.update_layout(paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],height=175,
        margin=dict(l=0,r=60,t=24,b=0),font=dict(family="JetBrains Mono",color=C["text"],size=8),
        title=dict(text='<span style="color:#6b7a94;font-size:8px">CORRÉLATION ROLLING GOLD/DXY (50 bougies)</span>',x=.01),
        hovermode="x unified",showlegend=False,dragmode="pan",
        yaxis=dict(range=[-1.05,1.05],showgrid=True,gridcolor=C["grid"],zeroline=False,
                   tickfont=dict(size=8),tickvals=[-1,-.6,-.2,0,.2,.6,1]),
        xaxis=dict(showgrid=False,tickfont=dict(size=8)))
    return fig

def build_equity_chart(equity_data, initial_balance=10000.0):
    """Courbe équité — corrigé KeyError."""
    fig = go.Figure()
    if not equity_data or len(equity_data) == 0:
        fig.add_annotation(text="Lance backtest.py pour voir la courbe",
            xref="paper",yref="paper",x=.5,y=.5,
            font=dict(color=C["text"],size=12),showarrow=False)
    else:
        try:
            times = [str(d.get("time","")) for d in equity_data]
            bals  = [float(d.get("balance", initial_balance)) for d in equity_data]
            if not bals: raise ValueError("bals vide")
            final  = bals[-1]
            color  = C["green"] if final >= initial_balance else C["red"]
            fig.add_trace(go.Scatter(x=times, y=bals,
                line=dict(color=color, width=2),
                fill="tozeroy",
                fillcolor="rgba(0,212,170,0.08)" if final >= initial_balance else "rgba(255,77,106,0.08)",
                hovertemplate="%{x}<br><b>$%{y:,.0f}</b><extra></extra>"))
            # Ligne capital initial — sécurisée
            if initial_balance and initial_balance > 0:
                fig.add_hline(y=initial_balance,
                    line=dict(color=C["muted"], width=.8, dash="dot"), opacity=.5)
        except Exception as e:
            fig.add_annotation(text=f"Erreur courbe: {e}",xref="paper",yref="paper",
                x=.5,y=.5,font=dict(color=C["red"],size=10),showarrow=False)
    fig.update_layout(
        paper_bgcolor=C["bg2"],plot_bgcolor=C["bg"],height=280,
        margin=dict(l=0,r=8,t=28,b=0),
        font=dict(family="JetBrains Mono",color=C["text"],size=8),
        title=dict(text='<span style="color:#6b7a94;font-size:9px">📈 COURBE D\'ÉQUITÉ</span>',x=.01),
        hovermode="x unified",showlegend=False,dragmode="pan",
        xaxis=dict(showgrid=False,tickfont=dict(size=8)),
        yaxis=dict(showgrid=True,gridcolor=C["grid"],tickfont=dict(size=8),
                   zeroline=False,tickformat="$,.0f"))
    return fig

def _plt(fig, key, small=False):
    cfg={"displaylogo":False,"scrollZoom":not small,"displayModeBar":not small,
         "modeBarButtonsToRemove":["lasso2d","select2d","autoScale2d"]}
    try:    st.plotly_chart(fig, width="stretch", config=cfg, key=key)
    except: st.plotly_chart(fig, use_container_width=True, config=cfg, key=key)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.markdown("""<style>
section[data-testid="stSidebar"]{display:flex!important;visibility:visible!important;
opacity:1!important;transform:none!important;margin-left:0!important;
width:21rem!important;min-width:21rem!important;}
.main{margin-left:21rem!important;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""<div style="padding:8px 0 12px;">
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1rem;
            background:linear-gradient(90deg,#f7b529,#ffd166);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">⚡ GOLD/DXY PRO</div>
        <div style="font-size:.5rem;color:#2e3a4e;letter-spacing:.1em;text-transform:uppercase;margin-top:1px;">
            Algo Trading Dashboard v12</div></div>""", unsafe_allow_html=True)

    st.markdown('<div class="lbl">Timeframe</div>', unsafe_allow_html=True)
    tf_sel = st.radio("TF",["M5","M15","H1"],horizontal=True,label_visibility="collapsed",
                       index=["M5","M15","H1"].index(ss.tf))
    if tf_sel != ss.tf: ss.tf = tf_sel

    st.markdown("<hr>", unsafe_allow_html=True)
    gc="#00d4aa" if ss.gold_change>=0 else "#ff4d6a"
    dc="#00d4aa" if ss.dxy_change>=0  else "#ff4d6a"
    st.markdown(
        f'<div class="card"><div class="lbl">XAUUSD</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:#f7b529;">{ss.gold_price:,.2f}</div>'
        f'<div style="font-size:.57rem;color:{gc};">{ss.gold_change:+.2f} ({ss.gold_pct:+.2f}%)</div></div>'
        f'<div class="card"><div class="lbl">DXY</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:#4da6ff;">{ss.dxy_price:.3f}</div>'
        f'<div style="font-size:.57rem;color:{dc};">{ss.dxy_change:+.4f}</div></div>',
        unsafe_allow_html=True)

    # Signal — données venant du bot
    conf = signal.get("confidence",0)
    pipe = signal.get("pipeline_state","IDLE")
    entry_p = signal.get("entry",0.0)
    tp_p    = signal.get("tp",0.0)
    sl_p    = signal.get("sl",0.0)
    rr_p    = signal.get("rr",0.0)
    lot_p   = signal.get("lot",0.0)
    corr_p  = signal.get("corr",ss.correlation)
    res_badge_html = result_badge(sig_result)
    ant_h = f'<div style="margin-top:3px;"><span class="ba" style="font-size:.55rem;">{ant}</span></div>' if ant else ""
    st.markdown(
        f'<div class="card card-gld"><div class="lbl">Signal</div>'
        f'<div style="margin:4px 0;display:flex;gap:6px;align-items:center;">'
        f'<span class="{BC[sig_dir]}">{sig_dir}</span>{res_badge_html}</div>'
        f'{ant_h}'
        f'<div style="font-size:.57rem;color:#6b7a94;line-height:1.9;margin-top:3px;">'
        f'Conf:&nbsp;<b style="color:#dde3ee;">{conf}%</b><br>'
        f'Corr:&nbsp;<b style="color:#dde3ee;">{corr_p:+.3f}</b><br>'
        f'<span style="color:#3d4a5e;">{pipe}</span></div></div>',
        unsafe_allow_html=True)

    cc="#00d4aa" if ss.correlation<-.6 else ("#f7b529" if ss.correlation<-.4 else "#ff4d6a")
    ct="✅ Forte" if ss.correlation<-.6 else ("⚠️ Modérée" if ss.correlation<-.4 else "❌ Faible")
    st.markdown(
        f'<div class="card"><div class="lbl">Corrélation</div>'
        f'<div style="font-size:1rem;font-weight:700;color:{cc};">{ss.correlation:+.4f}</div>'
        f'<div style="font-size:.55rem;color:{cc};margin-top:1px;">{ct}</div></div>',
        unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    ss.show_zones = st.checkbox("Zones (S/R · FVG · OB)", value=ss.show_zones)
    st.markdown(
        f'<div style="font-size:.52rem;color:#3d4a5e;line-height:1.8;margin-top:4px;">'
        f'{len(zones.get("fvg_bullish",[]))+len(zones.get("fvg_bearish",[]))} FVG · ATR={zones.get("atr",0):.2f}'
        f'<br>OB↑ {n_ob_b} · OB↓ {n_ob_s} actifs</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    api_color="#00d4aa" if api_ok else "#f7b529"
    dapi="dg" if api_ok else "dy"; dmt5="dg" if mt5_ok else "dy"
    st.markdown(
        f'<div style="font-size:.61rem;">'
        f'<div style="color:{api_color};margin-bottom:3px;"><span class="{dapi}"></span>{"API Live" if api_ok else "Simulation"}</div>'
        f'<div style="color:{"#00d4aa" if mt5_ok else "#f7b529"};"><span class="{dmt5}"></span>MT5 {"Live" if mt5_ok else "Off"}</div>'
        f'</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: st.metric("Winrate",f"{ss.winrate}%")
    with c2: st.metric("Trades", f"{ss.wins}W/{ss.losses}L")

    if ss.bt_stats:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="lbl">Backtest (résumé)</div>', unsafe_allow_html=True)
        bt=ss.bt_stats
        ret=bt.get("return_pct",0)
        rc="#00d4aa" if ret>=0 else "#ff4d6a"
        st.markdown(
            f'<div style="font-size:.58rem;color:#6b7a94;line-height:2.0;">'
            f'WR: <b style="color:#dde3ee;">{bt.get("winrate",0)}%</b><br>'
            f'PF: <b style="color:#dde3ee;">{bt.get("profit_factor",0)}</b><br>'
            f'DD: <b style="color:#ff4d6a;">{bt.get("max_drawdown",0)}%</b><br>'
            f'Ret: <b style="color:{rc};">{ret:+.1f}%</b></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="font-size:.49rem;color:#2e3a4e;text-align:center;margin-top:7px;line-height:2;">'
        f'{ss.gold_symbol} · {tf} · #{ss.tick}<br>{datetime.now().strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
dh="dg" if api_ok else "dy"; api_col="#00d4aa" if api_ok else "#f7b529"
ant_hd=f' <span class="ba">{ant}</span>' if ant else ""
res_hd=result_badge(sig_result)
st.markdown(f"""
<div style="display:flex;align-items:flex-start;justify-content:space-between;
            padding:4px 0 8px;border-bottom:1px solid rgba(255,255,255,.06);margin-bottom:8px;">
    <div>
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.4rem;
            background:linear-gradient(90deg,#f7b529,#ffd166);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.1;">
            GOLD / DXY PRO</div>
        <div style="font-size:.6rem;color:#6b7a94;margin-top:2px;">
            <span class="{dh}"></span><span style="color:{api_col};">{'HTTP Live' if api_ok else 'Simulation'}</span>
            &nbsp;·&nbsp;{'MT5 Live' if mt5_ok else 'Sim'}&nbsp;·&nbsp;{tf}&nbsp;·&nbsp;{ss.gold_symbol}</div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;padding-top:4px;">
        <span class="{BC[sig_dir]}">{sig_dir}</span>{ant_hd}{res_hd}
        <span style="font-size:.58rem;color:#6b7a94;">Conf&nbsp;<b style="color:#dde3ee;">{signal.get('confidence',0)}%</b></span>
        <span style="font-size:.95rem;font-weight:700;color:#dde3ee;margin-left:6px;">{datetime.now().strftime('%H:%M:%S')}</span>
    </div>
</div>""", unsafe_allow_html=True)

# Métriques
m=st.columns(7)
with m[0]: st.metric("XAUUSD",     f"{ss.gold_price:,.2f}",   f"{ss.gold_change:+.2f} ({ss.gold_pct:+.2f}%)")
with m[1]: st.metric("DXY",        f"{ss.dxy_price:.3f}",     f"{ss.dxy_change:+.4f}")
with m[2]: st.metric("Corrélation",f"{ss.correlation:+.4f}",  "Forte" if ss.correlation<-.6 else "Modérée")
with m[3]:
    emo={"BUY":"🟢","SELL":"🔴","WAIT":"⚪"}
    lbl=f"{emo[sig_dir]} {sig_dir}"
    if sig_result in ("WIN","LOSS"): lbl+=f" → {'✅' if sig_result=='WIN' else '❌'}"
    st.metric("Signal",lbl,f"Conf:{signal.get('confidence',0)}%")
with m[4]: st.metric("Winrate",    f"{ss.winrate}%",           f"{ss.wins}W/{ss.losses}L")
with m[5]: st.metric("BID/ASK",   f"{ss.gold_bid:.2f}",       f"ASK {ss.gold_ask:.2f}")
with m[6]: st.metric("R/R",       f"1:{signal.get('rr',0)}",  f"SL:{signal.get('sl_source','—')}")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
    "📊 Graphiques","🎯 Signal & Zones","🔀 Multi-TF",
    "📋 Logs Bot","📜 Historique","📈 Backtest"])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    g1,g2=st.columns(2)
    with g1: _plt(build_candle(gold_c,"XAUUSD",C["gold"],tf,signal=signal,zones=zones,
                               show_zones=ss.show_zones,obs_data=gold_obs),key="gold_chart")
    with g2: _plt(build_candle(dxy_c,"DXY",C["dxy"],tf,show_zones=False),key="dxy_chart")
    _plt(build_corr_chart(corr_data),key="corr_chart")
    if corr_data:
        lc=corr_data[-1]["corr"]
        zc="#00d4aa" if lc<-.6 else ("#f7b529" if lc<-.4 else "#ff4d6a")
        zt="Zone signal active" if lc<-.6 else ("Modérée" if lc<-.4 else "Hors zone")
        st.markdown(f'<div style="font-size:.57rem;color:{zc};margin-top:1px;">Corr: <b>{lc:+.4f}</b> · {zt}</div>',unsafe_allow_html=True)

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    s1,s2,s3=st.columns([1,1,1.2])
    with s1:
        _plt(build_gauge(ss.correlation),key="gauge_t2",small=True)
        if ss.correlation<-.65: ic,it=C["green"],"✅ Forte — signaux fiables"
        elif ss.correlation<-.4: ic,it=C["gold"],"⚠️ Modérée — attendre"
        else: ic,it=C["red"],"❌ Faible — éviter"
        st.markdown(f'<div style="font-size:.63rem;color:{ic};background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);border-radius:6px;padding:7px 9px;margin-top:4px;">{it}</div>',unsafe_allow_html=True)
    with s2:
        res_b=result_badge(sig_result)
        # Données directement depuis le signal du bot
        st.markdown(f"""
        <div class="card">
            <div style="display:flex;gap:7px;align-items:center;margin-bottom:8px;">
                <span class="{BC[sig_dir]}" style="font-size:.7rem;padding:3px 10px;">{sig_dir}</span>{res_b}
            </div>
            <div style="font-size:.64rem;color:#6b7a94;line-height:2.0;">
                Confiance:&nbsp;<b style="color:#dde3ee;">{conf}%</b><br>
                Corr:&nbsp;<b style="color:#dde3ee;">{corr_p:+.4f}</b><br>
                Entrée:&nbsp;<b style="color:#f7b529;">{entry_p:,.2f}</b><br>
                TP:&nbsp;<b style="color:#00d4aa;">{tp_p:,.2f}</b><br>
                SL:&nbsp;<b style="color:#ff4d6a;">{sl_p:,.2f}</b><br>
                R/R:&nbsp;<b style="color:#dde3ee;">1:{rr_p}</b><br>
                Lot:&nbsp;<b style="color:#dde3ee;">{lot_p}</b><br>
                Pipeline:&nbsp;<b style="color:#dde3ee;">{pipe}</b>
            </div>
        </div>""", unsafe_allow_html=True)
        if ant:
            st.markdown(f"""
            <div style="background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.3);border-radius:7px;padding:9px 10px;margin-top:5px;">
                <div style="font-size:.54rem;color:#a78bfa;font-weight:700;letter-spacing:.1em;margin-bottom:3px;">ANTICIPATION</div>
                <div style="font-size:.66rem;color:#c4b5fd;">{ant}</div>
            </div>""", unsafe_allow_html=True)
    with s3:
        sup=zones.get("support",0); res_z=zones.get("resistance",0); atr=zones.get("atr",0)
        st.markdown(f"""
        <div class="card">
            <div class="lbl" style="margin-bottom:6px;">Support / Résistance</div>
            <div style="font-size:.65rem;line-height:2.0;">
                <span style="color:#6b7a94;">Support:</span><b style="color:#00d4aa;float:right;">{sup:,.2f}</b><br>
                <span style="color:#6b7a94;">Résistance:</span><b style="color:#ff4d6a;float:right;">{res_z:,.2f}</b><br>
                <span style="color:#6b7a94;">ATR:</span><b style="color:#f7b529;float:right;">{atr:.3f}</b>
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
        if gold_obs.get("bullish_obs") or gold_obs.get("bearish_obs"):
            rows_ob=""
            for ob in gold_obs.get("bullish_obs",[]):
                rows_ob+=f'<div style="font-size:.58rem;color:#00d4aa;line-height:1.7;">↑ {ob["bottom"]:,.2f}–{ob["top"]:,.2f} <span style="color:#3d4a5e;">avg:{ob["avg"]:,.2f}</span></div>'
            for ob in gold_obs.get("bearish_obs",[]):
                rows_ob+=f'<div style="font-size:.58rem;color:#ff4d6a;line-height:1.7;">↓ {ob["bottom"]:,.2f}–{ob["top"]:,.2f} <span style="color:#3d4a5e;">avg:{ob["avg"]:,.2f}</span></div>'
            st.markdown(f'<div class="card"><div class="lbl" style="margin-bottom:4px;">Détail OB</div>{rows_ob}</div>',unsafe_allow_html=True)

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    mc=st.columns(3)
    for col,tf_n in zip(mc,["H1","M15","M5"]):
        d=mtf.get(tf_n,{}); sig=d.get("signal","WAIT"); cr=d.get("corr",0.); tr=d.get("trend","—")
        cc2=C["green"] if cr<-.6 else (C["gold"] if cr<0 else C["red"])
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;color:#dde3ee;margin-bottom:6px;">{tf_n}</div>
                <span class="{BC.get(sig,'bw')}">{sig}</span>
                <div style="font-size:.63rem;color:#6b7a94;line-height:2.0;margin-top:7px;text-align:left;">
                    Corr:&nbsp;<b style="color:{cc2};float:right;">{cr:+.4f}</b><br>
                    Trend:&nbsp;<b style="color:#dde3ee;float:right;">{tr}</b>
                </div>
            </div>""", unsafe_allow_html=True)
    sigs=[mtf.get(t,{}).get("signal","WAIT") for t in ["H1","M15","M5"]]
    buys=sigs.count("BUY"); sells=sigs.count("SELL")
    if   buys>=2:  cons,cc3="🟢 CONSENSUS BUY",  C["green"]
    elif sells>=2: cons,cc3="🔴 CONSENSUS SELL", C["red"]
    else:          cons,cc3="⚪ PAS DE CONSENSUS",C["gold"]
    st.markdown(f'<div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:12px;text-align:center;margin-top:8px;"><div style="font-size:.68rem;color:{cc3};font-weight:700;">{cons}</div><div style="font-size:.57rem;color:#2e3a4e;margin-top:3px;">H1:{sigs[0]} · M15:{sigs[1]} · M5:{sigs[2]}</div></div>',unsafe_allow_html=True)

# ── TAB 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    lc1,lc2=st.columns([3,1])
    with lc1: st.markdown('<div class="lbl">Logs Bot</div>',unsafe_allow_html=True)
    with lc2: lf=st.selectbox("Filtre",["ALL","SIGNAL","WARNING","ERROR"],label_visibility="collapsed")
    filtered=[l for l in reversed(ss.bot_logs) if lf=="ALL" or l.get("level")==lf]
    rows=""
    for e in filtered[:80]:
        lvl=e.get("level","INFO").upper()
        col={"INFO":"#6b7a94","WARNING":"#f7b529","ERROR":"#ff4d6a","SIGNAL":"#00d4aa"}.get(lvl,"#6b7a94")
        rows+=f'<div><span style="color:#2e3a4e;">{e.get("time","")}</span> <span style="color:{col};font-weight:600;">[{lvl}]</span> <span style="color:#9ca3af;">{e.get("msg","")}</span></div>'
    st.markdown(f'<div style="background:#0d1117;border:1px solid rgba(255,255,255,.06);border-radius:7px;padding:10px;height:285px;overflow-y:auto;font-size:.6rem;line-height:1.82;">{rows}</div>',unsafe_allow_html=True)

# ── TAB 5 ─────────────────────────────────────────────────────────────────────
with tab5:
    h1c,h2c,h3c,h4c=st.columns(4)
    with h1c: st.metric("Total",len(ss.signals))
    with h2c: st.metric("Winrate",f"{ss.winrate}%")
    with h3c: st.metric("Wins",ss.wins)
    with h4c: st.metric("Losses",ss.losses)
    if ss.signals:
        df_s=pd.DataFrame(ss.signals[::-1][-50:])
        def _rl(v): return {"WIN":"✅ WIN","LOSS":"❌ LOSS","OPEN":"🔵 OPEN"}.get(str(v),str(v))
        if "result" in df_s.columns: df_s["result"]=df_s["result"].apply(_rl)
        cols=[c for c in ["time","direction","tf","entry","tp","sl","rr","lot","sl_source","result"] if c in df_s.columns]
        def _sty(v): return {"BUY":"color:#00d4aa;font-weight:700","SELL":"color:#ff4d6a;font-weight:700","✅ WIN":"color:#00d4aa","❌ LOSS":"color:#ff4d6a","🔵 OPEN":"color:#f7b529"}.get(str(v),"color:#6b7a94")
        try:
            sub=[c for c in ["direction","result"] if c in cols]
            try:    st.dataframe(df_s[cols].style.map(_sty,subset=sub),width="stretch",height=300)
            except: st.dataframe(df_s[cols].style.map(_sty,subset=sub),use_container_width=True,height=300)
        except:
            try:    st.dataframe(df_s[cols],width="stretch",height=300)
            except: st.dataframe(df_s[cols],use_container_width=True,height=300)
    else:
        st.markdown('<div style="text-align:center;padding:35px;color:#2e3a4e;font-size:.7rem;">Aucun signal.<br>Lance le bot.</div>',unsafe_allow_html=True)

# ── TAB 6 : BACKTEST ──────────────────────────────────────────────────────────
with tab6:
    bt=ss.bt_stats
    if not bt:
        st.markdown("""
        <div style="text-align:center;padding:50px;color:#2e3a4e;">
            <div style="font-size:2rem;margin-bottom:12px;">📊</div>
            <div style="font-size:.8rem;color:#6b7a94;">Aucun résultat backtest disponible.</div>
            <div style="font-size:.65rem;color:#2e3a4e;margin-top:8px;">
                Lance <code style="color:#f7b529;">python backtest.py</code> sur ton PC.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="lbl" style="margin-bottom:8px;">Statistiques Globales</div>',unsafe_allow_html=True)
        b1,b2,b3,b4,b5,b6,b7,b8=st.columns(8)
        with b1: st.metric("Total trades",  bt.get("total",0))
        with b2: st.metric("Winrate",        f"{bt.get('winrate',0):.1f}%")
        with b3: st.metric("Profit Factor",  f"{bt.get('profit_factor',0):.2f}")
        with b4: st.metric("Max Drawdown",   f"{bt.get('max_drawdown',0):.1f}%")
        with b5: st.metric("Sharpe",         f"{bt.get('sharpe',0):.2f}")
        with b6:
            ret=bt.get("return_pct",0)
            st.metric("Rendement",f"{ret:+.1f}%",delta=f"{bt.get('final_balance',0)-bt.get('initial_balance',10000):+,.0f}$")
        with b7: st.metric("Capital final",  f"${bt.get('final_balance',0):,.0f}")
        with b8: st.metric("Gain moyen",     f"${bt.get('avg_win',0):,.0f}")
        st.markdown("<hr>",unsafe_allow_html=True)

        # Courbe équité — avec initial_balance sécurisé
        initial_bal = float(bt.get("initial_balance", 10000.0))
        _plt(build_equity_chart(ss.bt_equity, initial_balance=initial_bal), key="equity_chart")
        st.markdown("<hr>",unsafe_allow_html=True)

        col_a,col_b=st.columns(2)
        with col_a:
            st.markdown('<div class="lbl" style="margin-bottom:6px;">Détail Performance</div>',unsafe_allow_html=True)
            st.markdown(f"""
            <div class="card">
                <div style="font-size:.65rem;line-height:2.2;">
                    <span style="color:#6b7a94;">Wins:</span><b style="color:#00d4aa;float:right;">{bt.get('wins',0)}</b><br>
                    <span style="color:#6b7a94;">Losses:</span><b style="color:#ff4d6a;float:right;">{bt.get('losses',0)}</b><br>
                    <span style="color:#6b7a94;">Meilleur trade:</span><b style="color:#00d4aa;float:right;">+${bt.get('best_trade',0):,.0f}</b><br>
                    <span style="color:#6b7a94;">Pire trade:</span><b style="color:#ff4d6a;float:right;">${bt.get('worst_trade',0):,.0f}</b><br>
                    <span style="color:#6b7a94;">Gain moyen:</span><b style="color:#dde3ee;float:right;">+${bt.get('avg_win',0):,.0f}</b><br>
                    <span style="color:#6b7a94;">Perte moyenne:</span><b style="color:#dde3ee;float:right;">-${bt.get('avg_loss',0):,.0f}</b><br>
                    <span style="color:#6b7a94;">Capital initial:</span><b style="color:#dde3ee;float:right;">${bt.get('initial_balance',10000):,.0f}</b><br>
                    <span style="color:#6b7a94;">Capital final:</span><b style="color:{"#00d4aa" if bt.get("return_pct",0)>=0 else "#ff4d6a"};float:right;">${bt.get('final_balance',0):,.0f}</b>
                </div>
            </div>""", unsafe_allow_html=True)
        with col_b:
            patterns=ss.bt_patterns; rules=patterns.get("rules",{})
            if rules:
                st.markdown('<div class="lbl" style="margin-bottom:6px;">🧠 Règles Learning</div>',unsafe_allow_html=True)
                rows_r=""
                labels={"corr_h1_optimal":"Corr H1 optimal","min_atr":"ATR minimum",
                        "max_atr":"ATR maximum","rsi_mean_win":"RSI moyen (WIN)",
                        "best_trading_hours":"Meilleures heures UTC"}
                for key,label in labels.items():
                    val=rules.get(key)
                    if val is not None:
                        rows_r+=f'<div style="font-size:.62rem;line-height:2.0;"><span style="color:#6b7a94;">{label}:</span><b style="color:#a78bfa;float:right;">{val}</b></div>'
                st.markdown(f'<div class="card">{rows_r}</div>',unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:.58rem;color:#6b7a94;margin-top:4px;">Basé sur <b style="color:#dde3ee;">{patterns.get("total_wins",0)}</b> trades WIN · <code style="color:#f7b529;">learning.json</code></div>',unsafe_allow_html=True)
            else:
                st.markdown('<div class="card" style="color:#2e3a4e;font-size:.65rem;text-align:center;padding:20px;">Patterns après backtest.</div>',unsafe_allow_html=True)

        st.markdown("<hr>",unsafe_allow_html=True)
        st.markdown('<div class="lbl" style="margin-bottom:6px;">Trades Backtest</div>',unsafe_allow_html=True)
        if ss.bt_trades:
            df_bt=pd.DataFrame(ss.bt_trades[::-1])
            if "result" in df_bt.columns:
                df_bt["result"]=df_bt["result"].map({"WIN":"✅ WIN","LOSS":"❌ LOSS","OPEN":"🔵 OPEN"}).fillna(df_bt["result"])
            cols_bt=[c for c in ["time","direction","entry","tp","sl","rr","lot","result","pnl","balance","corr_h1","atr"] if c in df_bt.columns]
            def _bts(v): return {"BUY":"color:#00d4aa;font-weight:700","SELL":"color:#ff4d6a;font-weight:700","✅ WIN":"color:#00d4aa","❌ LOSS":"color:#ff4d6a"}.get(str(v),"color:#6b7a94")
            try:
                sub_bt=[c for c in ["direction","result"] if c in cols_bt]
                try:    st.dataframe(df_bt[cols_bt].style.map(_bts,subset=sub_bt),width="stretch",height=350)
                except: st.dataframe(df_bt[cols_bt].style.map(_bts,subset=sub_bt),use_container_width=True,height=350)
            except:
                try:    st.dataframe(df_bt[cols_bt],width="stretch",height=350)
                except: st.dataframe(df_bt[cols_bt],use_container_width=True,height=350)
        else:
            st.markdown('<div style="text-align:center;padding:20px;color:#2e3a4e;font-size:.65rem;">Pas encore de trades backtest.</div>',unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="text-align:center;padding:4px 0 2px;font-size:.48rem;color:#1a2234;'
    f'border-top:1px solid rgba(255,255,255,.04);margin-top:4px;">'
    f'Gold/DXY Pro v12 · {"🟢 Live" if api_ok else "🟡 Sim"} · Tick#{ss.tick} · {REFRESH_S}s</div>',
    unsafe_allow_html=True)

time.sleep(REFRESH_S)
st.rerun()
