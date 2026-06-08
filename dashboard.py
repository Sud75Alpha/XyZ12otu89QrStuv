import streamlit as st
import json
import streamlit.components.v1 as components

st.set_page_config(page_title="GOLD/DXY PRO v16", page_icon="⚡",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
html,body{margin:0!important;padding:0!important;overflow:hidden!important;}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="collapsedControl"],
[data-testid="stStatusWidget"],.stDeployButton{display:none!important;}
[data-testid="stAppViewContainer"]>section.main>div.block-container{
  padding:0!important;margin:0!important;max-width:100%!important;}
[data-testid="stAppViewContainer"]>section.main{padding:0!important;overflow:hidden!important;}
.main .block-container{padding:0!important;margin:0!important;max-width:100vw!important;}
iframe{border:none!important;display:block!important;position:fixed!important;
  top:0!important;left:0!important;width:100vw!important;height:100vh!important;z-index:9999!important;}
</style>""", unsafe_allow_html=True)

API_URL = "https://en-ligne-5wi6.onrender.com"
API_KEY = "gold_dxy_secret_2024"

import random, math
from datetime import datetime, timezone, timedelta

def gen_gold_candles(n=500, tf_mins=15, base=4328.92, seed=42):
    random.seed(seed)
    candles, price = [], base * 0.97
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=n*tf_mins)
    for i in range(n):
        t = start + timedelta(minutes=i*tf_mins)
        h = t.hour
        vol = 0.0011 if 13<=h<=20 else 0.0009 if 8<=h<=16 else 0.0004
        drift = (base - price) / (base * 0.15)
        chg = (random.gauss(drift*0.001, vol)) * price
        o, cl = round(price,2), round(price+chg,2)
        sp = abs(chg)*(0.4+random.random()*0.8)+price*0.0002
        hi = round(max(o,cl)+sp*random.random(),2)
        lo = max(round(min(o,cl)-sp*random.random(),2),1.0)
        candles.append({"time":int(t.timestamp()),"open":o,"high":hi,"low":lo,"close":cl,"volume":max(100,int(random.expovariate(1/5000)))})
        price = cl
    if candles:
        off = base - candles[-1]['close']
        ns = min(20, len(candles))
        for j in range(ns):
            ix = len(candles)-ns+j; f2 = j/ns
            for k in ('open','high','low','close'):
                candles[ix][k] = round(candles[ix][k]+off*f2, 2)
        candles[-1]['close'] = base
        candles[-1]['high']  = max(candles[-1]['high'], base)
    return candles

INIT_OHLCV = {
    'M5':  gen_gold_candles(500,  5,  4328.92),
    'M15': gen_gold_candles(500,  15, 4328.92),
    'H1':  gen_gold_candles(500,  60, 4328.92),
}
INIT_OHLCV_JSON = json.dumps(INIT_OHLCV)

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#0b0f1a;--bg2:#111827;--bg3:#141c2e;--card:#0f1623;
  --border:rgba(255,255,255,0.07);--gold:#f5a623;--green:#00d4aa;
  --red:#ff4d6a;--blue:#4da6ff;--purple:#a78bfa;
  --text:#e2e8f0;--muted:#4a5568;
}
html,body{width:100%;height:100%;overflow:hidden;background:var(--bg);
  color:var(--text);font-family:'Space Grotesk',sans-serif;}

/* ─── TOPBAR ─── */
#topbar{height:50px;background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 14px;gap:10px;flex-shrink:0;}
.logo{font-weight:700;font-size:.9rem;color:var(--gold);white-space:nowrap;}
.logo sub{font-size:.48rem;color:var(--muted);margin-left:3px;}
.nav{display:flex;gap:2px;background:var(--bg3);border:1px solid var(--border);
  border-radius:8px;padding:3px;}
.nav-btn{padding:4px 12px;border-radius:6px;font-size:.62rem;font-weight:600;
  color:var(--muted);cursor:pointer;border:none;background:transparent;transition:.15s;}
.nav-btn.active{background:rgba(245,166,35,.18);color:var(--gold);}
.nav-btn:hover:not(.active){color:var(--text);}
.tb-right{margin-left:auto;display:flex;align-items:center;gap:10px;}
.tb-price{font-family:'JetBrains Mono',monospace;font-size:1.25rem;
  font-weight:700;color:var(--gold);}
.tb-chg{font-size:.54rem;margin-top:1px;}
.badge{display:inline-flex;padding:3px 9px;border-radius:6px;
  font-size:.6rem;font-weight:700;letter-spacing:.04em;}
.badge.buy{background:rgba(0,212,170,.12);border:1px solid rgba(0,212,170,.3);color:var(--green);}
.badge.sell{background:rgba(255,77,106,.12);border:1px solid rgba(255,77,106,.3);color:var(--red);}
.badge.wait{background:rgba(100,116,139,.1);border:1px solid rgba(100,116,139,.2);color:var(--muted);}
.acct{display:flex;align-items:center;gap:7px;padding:3px 10px;
  background:var(--card);border:1px solid var(--border);border-radius:8px;}
.acct .b1{font-size:.66rem;font-weight:600;}
.acct .b2{font-size:.46rem;color:var(--muted);}
.av{width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#ff9f43);
  display:flex;align-items:center;justify-content:center;font-size:.5rem;font-weight:700;color:#000;}

/* ─── LAYOUT ─── */
#app{display:flex;height:calc(100vh - 50px - 26px);overflow:hidden;}

/* ─── ICON SIDEBAR ─── */
#isb{width:56px;background:var(--bg2);border-right:1px solid var(--border);
  display:flex;flex-direction:column;align-items:center;padding:8px 0;gap:3px;flex-shrink:0;}
.ib{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;
  justify-content:center;cursor:pointer;color:var(--muted);border:none;
  background:transparent;transition:.15s;position:relative;}
.ib:hover{background:rgba(255,255,255,.05);color:var(--text);}
.ib.active{background:rgba(245,166,35,.12);color:var(--gold);}
.ib svg{width:16px;height:16px;stroke:currentColor;fill:none;
  stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
.ib-sp{flex:1;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.1}}
.dlive{width:5px;height:5px;background:var(--green);border-radius:50%;
  position:absolute;top:5px;right:5px;box-shadow:0 0 5px var(--green);animation:blink 1.6s infinite;}

/* ─── INFO SIDEBAR ─── */
#sb{width:248px;background:var(--bg2);border-right:1px solid var(--border);
  overflow-y:auto;flex-shrink:0;display:flex;flex-direction:column;}
#sb::-webkit-scrollbar{width:2px;}
#sb::-webkit-scrollbar-thumb{background:var(--border);}
.ss{padding:10px 11px 0;}
.lbl{font-size:.44rem;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted);margin-bottom:5px;}
.tf-tabs{display:flex;gap:2px;background:var(--bg3);
  border:1px solid var(--border);border-radius:7px;padding:3px;}
.tf-tab{flex:1;text-align:center;padding:3px 0;border-radius:5px;
  font-size:.6rem;font-weight:600;color:var(--muted);cursor:pointer;
  border:none;background:transparent;transition:.15s;}
.tf-tab.active{background:rgba(245,166,35,.2);color:var(--gold);}
.card{background:var(--card);border:1px solid var(--border);border-radius:9px;
  padding:9px 11px;margin:5px 0;}
.card.gb{border-color:rgba(245,166,35,.2);}
.bv{font-family:'JetBrains Mono',monospace;font-size:1.35rem;
  font-weight:700;color:var(--gold);margin:2px 0;}
.bv.bl{color:var(--blue);}
.chg{font-size:.56rem;font-weight:600;}
.up{color:var(--green);}
.dn{color:var(--red);}
.ba{font-size:.48rem;color:var(--muted);margin-top:3px;}
.ba b{color:#9ca3af;}
.cbar{height:4px;border-radius:2px;background:#1e2d42;margin:5px 0 3px;overflow:hidden;}
.cbar-f{height:100%;border-radius:2px;transition:width .5s,background .5s;}
.sb-badge{display:inline-flex;padding:3px 10px;border-radius:6px;
  font-size:.62rem;font-weight:700;letter-spacing:.04em;margin-bottom:6px;}
.sb-badge.buy{background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:var(--green);}
.sb-badge.sell{background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:var(--red);}
.sb-badge.wait{background:rgba(100,116,139,.1);border:1px solid rgba(100,116,139,.2);color:var(--muted);}
.row{display:flex;justify-content:space-between;align-items:center;
  font-size:.56rem;line-height:1.9;}
.row .k{color:var(--muted);}
.row .v{font-weight:600;font-family:'JetBrains Mono',monospace;}
.sep{border:none;border-top:1px solid var(--border);margin:6px 11px;}
.mtf-row{display:flex;gap:4px;margin-bottom:5px;}
.mc{flex:1;background:var(--card);border:1px solid var(--border);
  border-radius:7px;padding:6px;text-align:center;}
.mc .tl{font-size:.46rem;font-weight:700;color:var(--muted);margin-bottom:3px;}
.mc .ts{font-size:.56rem;font-weight:700;}
.ts.buy{color:var(--green);} .ts.sell{color:var(--red);} .ts.wait{color:var(--muted);}
.sr{display:flex;gap:4px;margin-bottom:5px;}
.sb-box{flex:1;background:var(--card);border:1px solid var(--border);
  border-radius:7px;padding:6px 8px;}
.sb-box .sk{font-size:.44rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px;}
.sb-box .sv{font-size:.8rem;font-weight:700;font-family:'JetBrains Mono',monospace;}
.cr{display:flex;align-items:center;gap:5px;font-size:.54rem;margin-bottom:4px;}
.dot{width:5px;height:5px;border-radius:50%;flex-shrink:0;}
.dot.g{background:var(--green);box-shadow:0 0 4px var(--green);}
.dot.y{background:var(--gold);}
.dot.r{background:var(--red);box-shadow:0 0 4px var(--red);}

/* ─── CONTENT AREA ─── */
#content{flex:1;display:flex;overflow:hidden;position:relative;}

/* ─── TAB PANELS ─── */
.tab-panel{position:absolute;inset:0;display:none;flex-direction:column;overflow:hidden;}
.tab-panel.active{display:flex;}

/* ─── CHART PANEL ─── */
#p-chart{flex-direction:row;}
#chart-zone{flex:1;display:flex;flex-direction:column;overflow:hidden;}
#ctb{height:40px;background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 12px;gap:9px;flex-shrink:0;}
.ct-btn{padding:3px 8px;border-radius:5px;font-size:.58rem;font-weight:600;
  color:var(--muted);cursor:pointer;border:1px solid transparent;background:transparent;transition:.15s;}
.ct-btn.active{background:rgba(0,212,170,.12);border-color:rgba(0,212,170,.3);color:var(--green);}
.csep{width:1px;height:14px;background:var(--border);}
.tf-pill{padding:3px 7px;border-radius:5px;font-size:.56rem;font-weight:600;
  color:var(--muted);cursor:pointer;border:none;background:transparent;transition:.15s;}
.tf-pill.active{background:rgba(0,212,170,.12);color:var(--green);}
.tf-pill:hover:not(.active){color:var(--text);}
.dlive2{width:6px;height:6px;background:var(--green);border-radius:50%;display:inline-block;
  margin-right:4px;box-shadow:0 0 5px var(--green);animation:blink 1.6s infinite;vertical-align:middle;}
#chart-body{flex:1;display:flex;overflow:hidden;}
#cw{flex:1;display:flex;flex-direction:column;padding:6px 6px 0;gap:5px;overflow:hidden;}
#gc{flex:1;border-radius:9px;overflow:hidden;border:1px solid var(--border);min-height:0;}
#cc{height:88px;flex-shrink:0;border-radius:9px;overflow:hidden;border:1px solid var(--border);}

/* ─── RIGHT PANEL ─── */
#rp{width:278px;border-left:1px solid var(--border);background:var(--bg2);
  overflow-y:auto;flex-shrink:0;display:flex;flex-direction:column;}
#rp::-webkit-scrollbar{width:2px;}
#rp::-webkit-scrollbar-thumb{background:var(--border);}
.rps{padding:10px 11px;}
.obtn{display:flex;gap:5px;margin-bottom:9px;}
.ob{flex:1;padding:8px;border-radius:7px;font-size:.68rem;font-weight:700;
  cursor:pointer;border:none;letter-spacing:.04em;font-family:'Space Grotesk',sans-serif;transition:.15s;}
.ob.buy{background:var(--green);color:#000;}
.ob.buy:hover{background:#00bfa0;}
.ob.sell{background:var(--bg3);border:1px solid var(--border);color:var(--muted);}
.ob.sell.on{background:var(--red);color:#fff;border-color:var(--red);}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px;}
.mc2{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:7px 9px;}
.mc2.tp{border-color:rgba(0,212,170,.25);}
.mc2.sl{border-color:rgba(255,77,106,.25);}
.mc2.en{border-color:rgba(77,166,255,.2);}
.mc2 .mk{font-size:.44rem;color:var(--muted);font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;margin-bottom:2px;}
.mc2 .mv{font-family:'JetBrains Mono',monospace;font-size:.78rem;font-weight:700;}
.mc2 .ms{font-size:.46rem;color:var(--muted);margin-top:2px;}
/* ATR badge */
.atr-badge{font-size:.44rem;color:var(--purple);font-weight:700;
  background:rgba(167,139,250,.1);border:1px solid rgba(167,139,250,.25);
  border-radius:4px;padding:1px 5px;margin-left:4px;}
.rbar{height:4px;border-radius:2px;background:#1e2d42;overflow:hidden;margin:3px 0;}
.rbar-f{height:100%;border-radius:2px;transition:width .5s;}
.wr-bar{height:4px;border-radius:2px;background:#1e2d42;overflow:hidden;margin:4px 0 2px;}
.wr-f{height:100%;border-radius:2px;background:var(--green);}
.rdots{display:flex;gap:3px;margin:4px 0 3px;}
.rd{flex:1;height:4px;border-radius:2px;background:#1e2d42;}
.rd.g{background:var(--green);} .rd.y{background:var(--gold);} .rd.r{background:var(--red);}

/* ─── SIGNAL PANEL ─── */
#p-signal{background:var(--bg);overflow-y:auto;padding:14px;gap:10px;flex-direction:column;}
.sig-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:10px;}
.sig-grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
/* ATR TP/SL selector */
.atr-selector{display:flex;gap:5px;margin-bottom:8px;flex-wrap:wrap;}
.atr-btn{padding:4px 10px;border-radius:6px;font-size:.58rem;font-weight:600;
  border:1px solid var(--border);background:var(--bg3);color:var(--muted);cursor:pointer;transition:.15s;}
.atr-btn.active{background:rgba(167,139,250,.15);border-color:rgba(167,139,250,.4);color:var(--purple);}
.atr-info{font-size:.52rem;color:var(--muted);margin-top:4px;line-height:1.7;}
.atr-info b{color:var(--text);}

/* ─── MULTI-TF PANEL ─── */
#p-multitf{background:var(--bg);overflow-y:auto;padding:14px;gap:10px;flex-direction:column;}

/* ─── LOGS PANEL ─── */
#p-logs{background:var(--bg);flex-direction:column;}
.log-tb{padding:7px 10px;border-bottom:1px solid var(--border);
  display:flex;gap:5px;background:var(--bg2);flex-shrink:0;}
#logs-body{flex:1;overflow-y:auto;padding:10px;
  font-family:'JetBrains Mono',monospace;font-size:.58rem;line-height:1.9;}
#logs-body::-webkit-scrollbar{width:3px;}
#logs-body::-webkit-scrollbar-thumb{background:var(--border);}
.ll{padding:1px 0;border-bottom:1px solid rgba(255,255,255,.02);}
.ll.i{color:var(--muted);} .ll.s{color:var(--green);}
.ll.w{color:var(--gold);} .ll.e{color:var(--red);}

/* ─── HISTORIQUE PANEL ─── */
#p-hist{background:var(--bg);flex-direction:column;}
.hist-tb{padding:7px 10px;border-bottom:1px solid var(--border);
  background:var(--bg2);display:flex;gap:16px;align-items:center;flex-shrink:0;}
#hist-body-wrap{flex:1;overflow-y:auto;padding:10px;}
#hist-body-wrap::-webkit-scrollbar{width:3px;}
#hist-body-wrap::-webkit-scrollbar-thumb{background:var(--border);}
table.ht{width:100%;border-collapse:collapse;font-size:.56rem;}
table.ht th{padding:5px 7px;text-align:left;color:var(--muted);
  font-size:.46rem;letter-spacing:.08em;text-transform:uppercase;border-bottom:1px solid var(--border);}
table.ht td{padding:4px 7px;border-bottom:1px solid rgba(255,255,255,.03);
  font-family:'JetBrains Mono',monospace;}
table.ht tr:hover td{background:rgba(255,255,255,.02);}

/* ─── ALERT BANNER ─── */
#alert-banner{
  position:fixed;top:50px;left:0;right:0;z-index:9998;
  padding:10px 20px;display:none;align-items:center;gap:12px;
  background:linear-gradient(90deg,rgba(255,77,106,0.95),rgba(180,0,40,0.95));
  border-bottom:2px solid rgba(255,77,106,0.6);
  font-size:.72rem;font-weight:600;color:#fff;
  box-shadow:0 4px 20px rgba(255,77,106,0.4);
  animation:slideDown .3s ease;
}
@keyframes slideDown{from{transform:translateY(-100%)}to{transform:translateY(0)}}
#alert-banner .ab-icon{font-size:1.1rem;flex-shrink:0;}
#alert-banner .ab-msg{flex:1;}
#alert-banner .ab-time{font-size:.56rem;opacity:.8;white-space:nowrap;}
#alert-banner .ab-close{cursor:pointer;opacity:.7;font-size:.9rem;padding:2px 6px;
  border-radius:4px;background:rgba(255,255,255,.15);}
#alert-banner .ab-close:hover{opacity:1;background:rgba(255,255,255,.25);}

/* Trade result toast */
#trade-toast{
  position:fixed;top:70px;right:20px;z-index:9999;
  padding:12px 18px;border-radius:10px;font-size:.76rem;
  font-weight:700;display:none;flex-direction:column;gap:4px;
  box-shadow:0 8px 32px rgba(0,0,0,0.5);min-width:200px;
  animation:toastIn .3s ease;
}
@keyframes toastIn{from{transform:translateX(120%);opacity:0}to{transform:translateX(0);opacity:1}}
#trade-toast.win{background:rgba(0,212,170,.95);border:1px solid var(--green);color:#000;}
#trade-toast.loss{background:rgba(255,77,106,.95);border:1px solid var(--red);color:#fff;}
#trade-toast .tt-title{font-size:.9rem;}
#trade-toast .tt-sub{font-size:.6rem;font-weight:500;opacity:.85;}

/* Signal result badge dans sidebar */
.res-badge{display:inline-flex;padding:2px 8px;border-radius:5px;
  font-size:.56rem;font-weight:700;letter-spacing:.04em;margin-left:6px;}
.res-badge.win{background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:var(--green);}
.res-badge.loss{background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:var(--red);}
.res-badge.open{background:rgba(245,166,35,.12);border:1px solid rgba(245,166,35,.3);color:var(--gold);}

/* ─── TICKER ─── */
#ticker{height:26px;border-top:1px solid var(--border);background:var(--bg2);
  display:flex;align-items:center;padding:0 12px;gap:16px;overflow:hidden;flex-shrink:0;}
.ti{display:flex;gap:5px;align-items:center;white-space:nowrap;}
.ts2{font-size:.48rem;font-weight:700;color:var(--muted);}
.tv2{font-family:'JetBrains Mono',monospace;font-size:.54rem;font-weight:600;}
.tc2{font-size:.48rem;}
.tc2.up{color:var(--green);} .tc2.dn{color:var(--red);}
</style>
</head>
<body>

<!-- ALERT BANNER (TradeMonitor) -->
<div id="alert-banner">
  <span class="ab-icon">🚨</span>
  <span class="ab-msg" id="ab-msg">—</span>
  <span class="ab-time" id="ab-time">—</span>
  <span class="ab-close" onclick="dismissAlert()">✕</span>
</div>

<!-- TRADE RESULT TOAST -->
<div id="trade-toast">
  <div class="tt-title" id="tt-title">—</div>
  <div class="tt-sub" id="tt-sub">—</div>
</div>

<!-- TOPBAR -->
<div id="topbar">
  <div class="logo">⚡ GOLD/DXY PRO<sub>v16</sub></div>
  <div class="nav">
    <button class="nav-btn active" onclick="goTab('chart',this)">Chart</button>
    <button class="nav-btn" onclick="goTab('signal',this)">Signal & TP/SL</button>
    <button class="nav-btn" onclick="goTab('multitf',this)">Multi-TF</button>
    <button class="nav-btn" onclick="goTab('logs',this)">Logs</button>
    <button class="nav-btn" onclick="goTab('hist',this)">Historique</button>
  </div>
  <div class="tb-right">
    <div>
      <div class="tb-price" id="tp-p">—</div>
      <div class="tb-chg" id="tp-c">—</div>
    </div>
    <div style="width:1px;height:22px;background:var(--border)"></div>
    <div class="badge wait" id="tp-b">WAIT</div>
    <div style="font-size:.52rem;color:var(--muted)">Conf <b id="tp-cf" style="color:var(--text)">0%</b></div>
    <div class="acct">
      <div><div class="b1">XAUUSDm</div><div class="b2" id="acct-s">Live</div></div>
      <div class="av">GP</div>
    </div>
  </div>
</div>

<!-- APP -->
<div id="app">

  <!-- ICON SIDEBAR -->
  <div id="isb">
    <button class="ib active" onclick="goTab('chart',null)" title="Chart">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      <div class="dlive"></div>
    </button>
    <button class="ib" onclick="goTab('signal',null)" title="Signal & TP/SL">
      <svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
    </button>
    <button class="ib" onclick="goTab('multitf',null)" title="Multi-TF">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
    </button>
    <button class="ib" onclick="goTab('logs',null)" title="Logs">
      <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
    </button>
    <button class="ib" onclick="goTab('hist',null)" title="Historique">
      <svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><polyline points="18 9 12 15 9 12 3 18"/></svg>
    </button>
    <div class="ib-sp"></div>
    <button class="ib" title="Paramètres">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
    </button>
  </div>

  <!-- INFO SIDEBAR (toujours visible) -->
  <div id="sb">
    <div class="ss">
      <div class="lbl">Timeframe</div>
      <div class="tf-tabs">
        <button class="tf-tab" onclick="setTF('M5',this)">M5</button>
        <button class="tf-tab active" onclick="setTF('M15',this)">M15</button>
        <button class="tf-tab" onclick="setTF('H1',this)">H1</button>
      </div>
    </div>
    <div class="ss">
      <div class="card gb">
        <div class="lbl">XAUUSD — OR</div>
        <div class="bv" id="sb-g">—</div>
        <div class="chg" id="sb-gc">—</div>
        <div class="ba">BID <b id="sb-bid">—</b> | ASK <b id="sb-ask">—</b></div>
      </div>
      <div class="card">
        <div class="lbl">DXY</div>
        <div class="bv bl" id="sb-d">—</div>
        <div class="chg" id="sb-dc">—</div>
      </div>
    </div>
    <div class="sep"></div>
    <div class="ss">
      <div class="lbl">Corrélation</div>
      <div class="card">
        <div style="font-family:'JetBrains Mono',monospace;font-size:.95rem;font-weight:700" id="sb-cr">—</div>
        <div class="cbar"><div class="cbar-f" id="sb-crb" style="width:0"></div></div>
        <div style="font-size:.5rem;font-weight:600" id="sb-crt">—</div>
      </div>
    </div>
    <div class="ss">
      <div class="lbl">Signal</div>
      <div class="card gb">
        <span class="sb-badge wait" id="sb-sb">WAIT</span>
        <div class="row"><span class="k">Confiance</span><span class="v" id="sb-cf">—</span></div>
        <div class="row"><span class="k">Entrée</span><span class="v" id="sb-en" style="color:var(--gold)">—</span></div>
        <div class="row"><span class="k">TP <span class="atr-badge" id="sb-tp-mode">ATR</span></span><span class="v" id="sb-tp" style="color:var(--green)">—</span></div>
        <div class="row"><span class="k">SL <span class="atr-badge">ATR</span></span><span class="v" id="sb-sl" style="color:var(--red)">—</span></div>
        <div class="row"><span class="k">R/R</span><span class="v" id="sb-rr">—</span></div>
        <div class="row"><span class="k">Lot</span><span class="v" id="sb-lot">—</span></div>
        <div class="row"><span class="k">ATR</span><span class="v" id="sb-atr" style="color:var(--purple)">—</span></div>
        <div class="row"><span class="k">Pipeline</span><span class="v" id="sb-pipe" style="color:var(--gold)">IDLE</span></div>
      </div>
    </div>
    <div class="sep"></div>
    <div class="ss">
      <div class="lbl">Multi-TF</div>
      <div class="mtf-row">
        <div class="mc"><div class="tl">H1</div><div class="ts wait" id="mtf-h1">—</div></div>
        <div class="mc"><div class="tl">M15</div><div class="ts wait" id="mtf-m15">—</div></div>
        <div class="mc"><div class="tl">M5</div><div class="ts wait" id="mtf-m5">—</div></div>
      </div>
    </div>
    <div class="sep"></div>
    <div class="ss">
      <div class="lbl">Connexion</div>
      <div class="cr"><div class="dot y" id="dot-api"></div><span id="lbl-api" style="color:var(--gold)">Connexion...</span></div>
      <div class="cr"><div class="dot y" id="dot-mt5"></div><span id="lbl-mt5" style="color:var(--gold)">MT5...</span></div>
    </div>
    <div class="ss" style="padding-bottom:12px">
      <div class="lbl">Stats</div>
      <div class="sr">
        <div class="sb-box"><div class="sk">Winrate</div><div class="sv up" id="sb-wr">—</div></div>
        <div class="sb-box"><div class="sk">W / L</div><div class="sv" id="sb-wl">—</div></div>
      </div>
      <div style="font-size:.42rem;color:#1e2d42;text-align:center;margin-top:5px;line-height:2">
        Tick #<span id="sb-tk">0</span> · <span id="sb-tm">--:--:--</span>
      </div>
    </div>
  </div>

  <!-- CONTENT -->
  <div id="content">

    <!-- CHART -->
    <div id="p-chart" class="tab-panel active">
      <div id="chart-zone">
        <div id="ctb">
          <span style="font-weight:700;font-size:.74rem"><span class="dlive2"></span>XAUUSD · XAUUSDm</span>
          <div class="csep"></div>
          <button class="ct-btn active" id="btn-c" onclick="setChartType('candle')">Candle</button>
          <button class="ct-btn" id="btn-l" onclick="setChartType('line')">Line</button>
          <div class="csep"></div>
          <button class="tf-pill" onclick="setPill(this,'M5',5)">1m</button>
          <button class="tf-pill" onclick="setPill(this,'M5',5)">5m</button>
          <button class="tf-pill" onclick="setPill(this,'M5',5)">10m</button>
          <button class="tf-pill active" onclick="setPill(this,'M15',15)">15m</button>
          <button class="tf-pill" onclick="setPill(this,'H1',60)">1h</button>
          <button class="tf-pill" onclick="setPill(this,'H1',60)">5h</button>
          <button class="tf-pill" onclick="setPill(this,'H1',60)">All</button>
          <div class="csep"></div>
          <span style="font-size:.52rem;color:var(--muted)">EMA20<b style="color:var(--gold)"> ●</b> EMA50<b style="color:rgba(255,255,255,.2)"> ●</b></span>
          <span style="margin-left:auto;font-size:.52rem;color:var(--muted)" id="clock">--:--:--</span>
        </div>
        <div id="chart-body">
          <div id="cw">
            <div id="market-banner" style="display:none;align-items:center;justify-content:space-between;background:rgba(255,77,106,0.08);border:1px solid rgba(255,77,106,0.25);border-radius:9px;padding:8px 14px;margin-bottom:5px;flex-shrink:0;">
              <div>
                <div id="market-banner-txt" style="font-size:.72rem;font-weight:700;color:var(--red)">🔴 Marché FERMÉ</div>
                <div id="market-banner-sub" style="font-size:.54rem;color:var(--muted);margin-top:2px">Réouverture dim. 22:00 UTC</div>
              </div>
              <div style="text-align:right;font-size:.52rem;color:var(--muted)">Bougies en <b style="color:var(--gold)">simulation</b></div>
            </div>
            <div id="gc"></div>
            <div id="cc"></div>
          </div>
          <!-- RIGHT PANEL -->
          <div id="rp">
            <div class="rps">
              <div class="lbl">Ordre</div>
              <div class="obtn">
                <button class="ob buy" id="rp-buy" onclick="setSig('BUY')">Buy</button>
                <button class="ob sell" id="rp-sell" onclick="setSig('SELL')">Sell</button>
              </div>
              <div class="g2">
                <div class="mc2 tp">
                  <div class="mk">Take Profit <span class="atr-badge">ATR×2</span></div>
                  <div class="mv" id="rp-tp" style="color:var(--green)">—</div>
                  <div class="ms" id="rp-tp-d">—</div>
                </div>
                <div class="mc2 sl">
                  <div class="mk">Stop Loss <span class="atr-badge">ATR×1</span></div>
                  <div class="mv" id="rp-sl" style="color:var(--red)">—</div>
                  <div class="ms" id="rp-sl-d">—</div>
                </div>
                <div class="mc2 en">
                  <div class="mk">Entrée</div>
                  <div class="mv" id="rp-en" style="color:var(--blue)">—</div>
                </div>
                <div class="mc2">
                  <div class="mk">ATR(14) live</div>
                  <div class="mv" id="rp-atr" style="color:var(--purple)">—</div>
                  <div class="ms" id="rp-atr-m">×1/×2</div>
                </div>
              </div>
              <div style="margin-bottom:7px">
                <div style="display:flex;justify-content:space-between;font-size:.53rem;margin-bottom:3px">
                  <span style="color:var(--muted)">Risk Exposure</span>
                  <span id="rp-risk-l" style="color:var(--gold);font-weight:600">—</span>
                </div>
                <div class="rbar"><div class="rbar-f" id="rp-risk-b" style="width:0;background:var(--gold)"></div></div>
              </div>
            </div>
            <div class="sep" style="margin:0"></div>
            <div class="rps">
              <div class="lbl">Performance</div>
              <div class="g2">
                <div class="mc2">
                  <div class="mk">Winrate</div>
                  <div class="mv up" id="rp-wr">—</div>
                  <div class="wr-bar"><div class="wr-f" id="rp-wr-b" style="width:0"></div></div>
                </div>
                <div class="mc2">
                  <div class="mk">Trades</div>
                  <div class="mv" id="rp-tr">—</div>
                  <div style="font-size:.46rem;color:var(--muted);margin-top:2px" id="rp-wl">—</div>
                </div>
                <div class="mc2">
                  <div class="mk">Day High</div>
                  <div class="mv up" id="rp-hi">—</div>
                </div>
                <div class="mc2">
                  <div class="mk">Day Low</div>
                  <div class="mv dn" id="rp-lo">—</div>
                </div>
              </div>
              <div class="mc2" style="margin-bottom:6px">
                <div class="mk">Risk Level</div>
                <div class="rdots" id="rdots">
                  <div class="rd"></div><div class="rd"></div><div class="rd"></div><div class="rd"></div><div class="rd"></div>
                </div>
                <div style="font-size:.48rem;font-weight:600" id="risk-l">—</div>
              </div>
              <div class="mc2">
                <div class="lbl" style="margin-bottom:4px">OHLCV</div>
                <div class="row"><span class="k">Open</span><span class="v" id="oh-o">—</span></div>
                <div class="row"><span class="k">High</span><span class="v up" id="oh-h">—</span></div>
                <div class="row"><span class="k">Low</span><span class="v dn" id="oh-l">—</span></div>
                <div class="row"><span class="k">Close</span><span class="v" id="oh-c" style="color:var(--gold)">—</span></div>
                <div class="row"><span class="k">Volume</span><span class="v" id="oh-v" style="color:var(--blue)">—</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SIGNAL & TP/SL DYNAMIQUE -->
    <div id="p-signal" class="tab-panel">
      <div class="sig-grid">
        <div class="card gb">
          <div class="lbl" style="margin-bottom:6px">Signal Principal</div>
          <span class="sb-badge wait" id="sig-b">WAIT</span>
          <div class="row" style="margin-top:4px"><span class="k">Confiance</span><span class="v" id="sig-cf">—</span></div>
          <div class="row"><span class="k">Pipeline</span><span class="v" id="sig-pp" style="color:var(--gold)">IDLE</span></div>
          <div class="row"><span class="k">Corrélation</span><span class="v" id="sig-cr">—</span></div>
        </div>
        <div class="card">
          <div class="lbl" style="margin-bottom:6px">Prix Live</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:1.8rem;font-weight:700;color:var(--gold)" id="sig-pb">—</div>
          <div style="font-size:.58rem;margin-top:3px" id="sig-pc">—</div>
          <div class="row" style="margin-top:6px"><span class="k">BID</span><span class="v" id="sig-bid">—</span></div>
          <div class="row"><span class="k">ASK</span><span class="v" id="sig-ask">—</span></div>
          <div class="row"><span class="k">DXY</span><span class="v" id="sig-dxy" style="color:var(--blue)">—</span></div>
        </div>
        <div class="card">
          <div class="lbl" style="margin-bottom:6px">Zones</div>
          <div class="row"><span class="k">Support</span><span class="v up" id="sig-sup">—</span></div>
          <div class="row"><span class="k">Résistance</span><span class="v dn" id="sig-res">—</span></div>
          <div class="row"><span class="k">ATR(14)</span><span class="v" id="sig-atr" style="color:var(--purple)">—</span></div>
          <div class="row"><span class="k">FVG Bull</span><span class="v up" id="sig-fb">—</span></div>
          <div class="row"><span class="k">FVG Bear</span><span class="v dn" id="sig-fs">—</span></div>
        </div>
      </div>

      <!-- TP/SL DYNAMIQUE ATR -->
      <div class="card" style="border-color:rgba(167,139,250,.25)">
        <div class="lbl" style="margin-bottom:8px;color:var(--purple)">⚡ TP/SL DYNAMIQUE — Basé sur ATR(14)</div>
        <div style="font-size:.58rem;color:var(--muted);margin-bottom:8px">
          SL = Entrée ± ATR × multiplicateur | TP = SL × ratio R:R minimum 1:2
        </div>
        <div class="atr-selector">
          <button class="atr-btn" onclick="setATRMode('conservative',this)">🛡️ Conservateur<br><span style="font-size:.46rem">SL=1×ATR · TP=2×ATR</span></button>
          <button class="atr-btn active" onclick="setATRMode('balanced',this)">⚖️ Équilibré<br><span style="font-size:.46rem">SL=1.5×ATR · TP=3×ATR</span></button>
          <button class="atr-btn" onclick="setATRMode('aggressive',this)">🎯 Agressif<br><span style="font-size:.46rem">SL=2×ATR · TP=5×ATR</span></button>
          <button class="atr-btn" onclick="setATRMode('swing',this)">📈 Swing<br><span style="font-size:.46rem">SL=3×ATR · TP=6×ATR</span></button>
        </div>
        <div class="sig-grid2" style="margin-top:8px">
          <div class="mc2 tp" style="padding:10px 12px">
            <div class="mk">Take Profit ATR</div>
            <div class="mv" id="dyn-tp" style="color:var(--green);font-size:1rem">—</div>
            <div class="ms" id="dyn-tp-d">—</div>
          </div>
          <div class="mc2 sl" style="padding:10px 12px">
            <div class="mk">Stop Loss ATR</div>
            <div class="mv" id="dyn-sl" style="color:var(--red);font-size:1rem">—</div>
            <div class="ms" id="dyn-sl-d">—</div>
          </div>
          <div class="mc2 en">
            <div class="mk">Entrée</div>
            <div class="mv" id="dyn-en" style="color:var(--blue)">—</div>
          </div>
          <div class="mc2" style="border-color:rgba(167,139,250,.2)">
            <div class="mk">ATR(14) actuel</div>
            <div class="mv" id="dyn-atr" style="color:var(--purple)">—</div>
            <div class="ms" id="dyn-rr">R:R —</div>
          </div>
        </div>
        <div class="atr-info" id="atr-explain" style="margin-top:8px;padding:8px;background:rgba(167,139,250,.06);border:1px solid rgba(167,139,250,.15);border-radius:7px">
          <b>Mode Équilibré</b> — SL à <b id="atr-sl-dist">—</b> pts du prix · TP à <b id="atr-tp-dist">—</b> pts · Ratio 1:<b id="atr-ratio">2.0</b><br>
          Trailing stop activé si le prix dépasse <b id="atr-trail">—</b>
        </div>
      </div>
    </div>

    <!-- MULTI-TF -->
    <div id="p-multitf" class="tab-panel">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
        <div class="card">
          <div style="font-size:1rem;font-weight:700;margin-bottom:8px">H1</div>
          <span class="sb-badge wait" id="mtf-big-h1">WAIT</span>
          <div class="row" style="margin-top:5px"><span class="k">Corrélation</span><span class="v" id="mtf-cr-h1">—</span></div>
          <div class="row"><span class="k">Tendance</span><span class="v" id="mtf-tr-h1">—</span></div>
        </div>
        <div class="card">
          <div style="font-size:1rem;font-weight:700;margin-bottom:8px">M15</div>
          <span class="sb-badge wait" id="mtf-big-m15">WAIT</span>
          <div class="row" style="margin-top:5px"><span class="k">Corrélation</span><span class="v" id="mtf-cr-m15">—</span></div>
          <div class="row"><span class="k">Tendance</span><span class="v" id="mtf-tr-m15">—</span></div>
        </div>
        <div class="card">
          <div style="font-size:1rem;font-weight:700;margin-bottom:8px">M5</div>
          <span class="sb-badge wait" id="mtf-big-m5">WAIT</span>
          <div class="row" style="margin-top:5px"><span class="k">Corrélation</span><span class="v" id="mtf-cr-m5">—</span></div>
          <div class="row"><span class="k">Tendance</span><span class="v" id="mtf-tr-m5">—</span></div>
        </div>
      </div>
      <div class="card">
        <div class="lbl" style="margin-bottom:6px">Consensus</div>
        <div id="cons-txt" style="font-size:.8rem;font-weight:700;text-align:center;padding:10px">—</div>
        <div id="cons-sub" style="font-size:.56rem;color:var(--muted);text-align:center">H1: — · M15: — · M5: —</div>
      </div>
    </div>

    <!-- LOGS -->
    <div id="p-logs" class="tab-panel">
      <div class="log-tb">
        <button class="ct-btn active" onclick="filterLog('ALL',this)">ALL</button>
        <button class="ct-btn" onclick="filterLog('SIGNAL',this)">SIGNAL</button>
        <button class="ct-btn" onclick="filterLog('WARNING',this)">WARNING</button>
        <button class="ct-btn" onclick="filterLog('ERROR',this)">ERROR</button>
      </div>
      <div id="logs-body"><div style="color:var(--muted);padding:20px">Chargement...</div></div>
    </div>

    <!-- HISTORIQUE -->
    <div id="p-hist" class="tab-panel">
      <div class="hist-tb">
        <span class="ts2">Total: <b id="ht-tot" style="color:var(--text)">—</b></span>
        <span class="ts2">Winrate: <b id="ht-wr" style="color:var(--green)">—</b></span>
        <span class="ts2">Wins: <b id="ht-w" style="color:var(--green)">—</b></span>
        <span class="ts2">Losses: <b id="ht-l" style="color:var(--red)">—</b></span>
      </div>
      <div id="hist-body-wrap">
        <table class="ht">
          <thead><tr><th>Heure</th><th>Dir</th><th>TF</th><th>Entrée</th><th>TP</th><th>SL</th><th>R/R</th><th>Lot</th><th>Résultat</th></tr></thead>
          <tbody id="ht-body"><tr><td colspan="9" style="color:var(--muted);text-align:center;padding:20px">Aucun signal</td></tr></tbody>
        </table>
      </div>
    </div>

  </div><!-- /content -->
</div><!-- /app -->

<!-- TICKER -->
<div id="ticker">
  <div class="ti"><span class="ts2">XAUUSD</span><span class="tv2" id="tk-g">—</span><span class="tc2 up" id="tk-gc">—</span></div>
  <div class="ti"><span class="ts2">DXY</span><span class="tv2" id="tk-d">—</span><span class="tc2" id="tk-dc">—</span></div>
  <div class="ti"><span class="ts2">CORR</span><span class="tv2" id="tk-cr">—</span><span class="tc2" id="tk-crl">—</span></div>
  <div class="ti"><span class="ts2">ATR</span><span class="tv2" id="tk-atr" style="color:var(--purple)">—</span></div>
  <div class="ti"><span class="ts2">SIGNAL</span><span class="tv2" id="tk-sig" style="color:var(--muted)">—</span><span class="tc2" id="tk-cf2">—</span></div>
  <div class="ti"><span class="ts2">PIPE</span><span class="tv2" id="tk-pp" style="color:var(--gold)">IDLE</span></div>
  <div class="ti"><span class="ts2">MARCHÉ</span><span class="tv2" id="tk-mkt" style="color:var(--green)">● OUVERT</span></div>
  <div class="ti" style="margin-left:auto">
  <span class="ts2">SOURCE</span><span class="tv2" id="tk-api" style="color:var(--muted)">—</span>
</div>
<div class="ti">
  <span class="ts2">MARCHÉ</span><span class="tv2" id="tk-mkt" style="color:var(--muted)">—</span>
</div>
  <div class="ti"><span class="ts2">TICK#</span><span class="tv2" id="tk-n">0</span></div>
</div>

<script>
/* ══════════ CONFIG ══════════ */
const API_URL = 'APIURL_PLACEHOLDER';
const API_KEY = 'APIKEY_PLACEHOLDER';

/* ══════════ STATE ══════════ */
const S = {
  price:4328.92, prev:4328.92, dxy:104.23, corr:-0.65,
  chg:0, pct:0, dxyChg:0, bid:4328.77, ask:4329.07,
  sig:'WAIT', conf:0, entry:0, tp:0, sl:0, rr:0, lot:0,
  pipe:'IDLE', wins:0, losses:0, wr:0,
  atr:0, atrMode:'balanced', openPrice:0,
  lastAlert:null, lastAlertTime:0, tradeResult:'',
  apiOk:false, mt5Ok:false, tick:0, tf:'M15', logFilter:'ALL',
  ohlcv:"OHLCV_PLACEHOLDER", mtf:{H1:{},M15:{},M5:{}},
  zones:{}, logs:[], signals:[],
  hArr:[], lArr:[], chartTF:'', chartLoaded:false,
};

/* ATR modes */
const ATR_MODES = {
  conservative: {slMult:1.0, tpMult:2.0, label:'Conservateur'},
  balanced:     {slMult:1.5, tpMult:3.0, label:'Équilibré'},
  aggressive:   {slMult:2.0, tpMult:5.0, label:'Agressif'},
  swing:        {slMult:3.0, tpMult:6.0, label:'Swing'},
};

/* ══════════ ALERTS & TRADE RESULTS ══════════ */
let alertTimer = null;

function showAlert(msg) {
  const banner = document.getElementById('alert-banner');
  const msgEl  = document.getElementById('ab-msg');
  const timeEl = document.getElementById('ab-time');
  if (!banner || !msg) return;
  msgEl.textContent  = msg;
  timeEl.textContent = new Date().toLocaleTimeString('fr-FR');
  banner.style.display = 'flex';
  // Auto-dismiss après 30s
  clearTimeout(alertTimer);
  alertTimer = setTimeout(dismissAlert, 30000);
  // Notification son (bip discret)
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = 880;
    osc.type = 'sine';
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
    osc.start(); osc.stop(ctx.currentTime + 0.4);
  } catch(e){}
  // Faire clignoter le titre de la page
  let blink = 0;
  const origTitle = document.title;
  const blinkTimer = setInterval(() => {
    document.title = blink++ % 2 === 0 ? '🚨 ALERTE BOT — ' + origTitle : origTitle;
    if (blink > 10) { clearInterval(blinkTimer); document.title = origTitle; }
  }, 500);
}

function dismissAlert() {
  const banner = document.getElementById('alert-banner');
  if (banner) banner.style.display = 'none';
  clearTimeout(alertTimer);
}

function showTradeResult(result, profit) {
  const toast  = document.getElementById('trade-toast');
  const title  = document.getElementById('tt-title');
  const sub    = document.getElementById('tt-sub');
  if (!toast) return;
  if (result === 'WIN') {
    toast.className = 'win';
    title.textContent = '✅ TRADE GAGNANT';
    sub.textContent   = profit ? 'Profit: +' + (+profit).toFixed(2) + ' USD' : 'TP atteint';
  } else if (result === 'LOSS') {
    toast.className = 'loss';
    title.textContent = '❌ TRADE PERDANT';
    sub.textContent   = profit ? 'Perte: ' + (+profit).toFixed(2) + ' USD' : 'SL touché';
  }
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 8000);
}

/* Vérifier si TP/SL touché côté dashboard (si l'API ne le dit pas) */
function checkTPSL() {
  if (!S.entry || !S.tp || !S.sl || !S.price) return;
  if (S.tradeResult === 'WIN' || S.tradeResult === 'LOSS') return;
  if (S.sig !== 'BUY' && S.sig !== 'SELL') return;
  const isBuy = S.sig === 'BUY';
  let hit = null;
  if (isBuy) {
    if (S.price >= S.tp) hit = 'WIN';
    else if (S.price <= S.sl) hit = 'LOSS';
  } else {
    if (S.price <= S.tp) hit = 'WIN';
    else if (S.price >= S.sl) hit = 'LOSS';
  }
  if (hit) {
    S.tradeResult = hit;
    const profit = hit==='WIN' ? Math.abs(S.tp - S.entry) * (S.lot||0.1) * 100
                               : -Math.abs(S.entry - S.sl) * (S.lot||0.1) * 100;
    showTradeResult(hit, profit);
    // Alert aussi
    showAlert((hit==='WIN'?'✅ TP atteint':'🛑 SL touché') +
              ' — XAUUSD @ ' + S.price.toFixed(2));
    S.tp = 0; S.sl = 0; S.entry = 0;
  }
}

/* ══════════ MARKET HOURS ══════════ */
function isMarketClosed() {
  // Forex/Gold fermé : vendredi 22:00 UTC → dimanche 22:00 UTC
  const now = new Date();
  const day = now.getUTCDay();   // 0=dim, 1=lun, 5=ven, 6=sam
  const hour = now.getUTCHours();
  const min  = now.getUTCMinutes();
  const timeNum = hour * 100 + min;
  if (day === 6) return true;                          // Samedi entier
  if (day === 0 && timeNum < 2200) return true;        // Dimanche avant 22h UTC
  if (day === 5 && timeNum >= 2200) return true;       // Vendredi après 22h UTC
  return false;
}

function getMarketStatus() {
  const now = new Date();
  const day = now.getUTCDay();
  const hour = now.getUTCHours();
  const days = ['Dim','Lun','Mar','Mer','Jeu','Ven','Sam'];
  if (!isMarketClosed()) return {closed:false};
  // Calculer réouverture : prochain dim 22:00 UTC
  const reopen = new Date(now);
  // Avancer jusqu'au prochain dimanche 22:00 UTC
  let daysUntil = (7 - day + 0) % 7; // jours jusqu'au dim
  if (day === 0 && hour >= 22) daysUntil = 7; // si dim après 22h, attendre le suivant
  if (daysUntil === 0 && day !== 0) daysUntil = 7;
  reopen.setUTCDate(reopen.getUTCDate() + daysUntil);
  reopen.setUTCHours(22,0,0,0);
  const diffMs = reopen - now;
  const diffH  = Math.floor(diffMs/3600000);
  const diffM  = Math.floor((diffMs%3600000)/60000);
  return {closed:true, reopenIn: diffH+'h '+diffM+'m', reopenTime:'Dim 22:00 UTC'};
}

/* ══════════ CHARTS INIT ══════════ */
const gcEl = document.getElementById('gc');
const ccEl = document.getElementById('cc');

// ── Gold chart ──
const GC = LightweightCharts.createChart(gcEl, {
  layout: { background:{color:'#0f1623'}, textColor:'#4a5568' },
  grid:   { vertLines:{color:'rgba(255,255,255,0.03)'}, horzLines:{color:'rgba(255,255,255,0.03)'} },
  crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
  rightPriceScale: { borderColor:'rgba(255,255,255,0.06)', scaleMargins:{top:0.05,bottom:0.2} },
  timeScale: { borderColor:'rgba(255,255,255,0.06)', timeVisible:true, secondsVisible:false },
  handleScroll: { mouseWheel:true, pressedMouseMove:true },
  handleScale:  { mouseWheel:true, pinch:true },
});

// Séries gold — déclarées une seule fois, jamais recréées
let CSER = GC.addCandlestickSeries({
  upColor:'#00d4aa', downColor:'#ff4d6a',
  borderUpColor:'#00d4aa', borderDownColor:'#ff4d6a',
  wickUpColor:'rgba(0,212,170,0.8)', wickDownColor:'rgba(255,77,106,0.8)',
});
let LSER = null;   // Série ligne (créée à la demande)
let chartMode = 'candle';  // 'candle' | 'line'

const E20  = GC.addLineSeries({ color:'rgba(245,166,35,0.85)', lineWidth:1.5, lineStyle:0, priceLineVisible:false, lastValueVisible:false });
const E50  = GC.addLineSeries({ color:'rgba(255,255,255,0.2)',  lineWidth:1,   priceLineVisible:false, lastValueVisible:false });
const VOLS = GC.addHistogramSeries({ priceFormat:{type:'volume'}, priceScaleId:'vol', scaleMargins:{top:0.85,bottom:0} });
const TPL  = GC.addLineSeries({ color:'rgba(0,212,170,0.7)',  lineWidth:1, lineStyle:2, priceLineVisible:false, lastValueVisible:false });
const SLL  = GC.addLineSeries({ color:'rgba(255,77,106,0.7)', lineWidth:1, lineStyle:2, priceLineVisible:false, lastValueVisible:false });

// ── Corrélation chart ──
const CC = LightweightCharts.createChart(ccEl, {
  layout: { background:{color:'#0f1623'}, textColor:'#4a5568' },
  grid:   { vertLines:{color:'rgba(255,255,255,0.02)'}, horzLines:{color:'rgba(255,255,255,0.02)'} },
  rightPriceScale: { borderColor:'rgba(255,255,255,0.06)' },
  timeScale: { borderColor:'rgba(255,255,255,0.06)', visible:false },
  crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
});

// Séries corrélation — TOUTES créées une seule fois ici
const CRS  = CC.addLineSeries({ color:'#f5a623', lineWidth:2, priceLineVisible:false, lastValueVisible:true,
  autoscaleInfoProvider: () => { return {priceRange:{minValue:-1,maxValue:1}}; }
});
// Lignes de référence fixes (créées une fois, jamais recréées)
const REF_LINES = [-0.6, -0.3, 0, 0.3, 0.6].map(v =>
  CC.addLineSeries({
    color: v < 0 ? 'rgba(0,212,170,0.18)' : v === 0 ? 'rgba(255,255,255,0.1)' : 'rgba(255,77,106,0.18)',
    lineWidth:1, lineStyle:2, priceLineVisible:false, lastValueVisible:false,
    autoscaleInfoProvider: () => { return {priceRange:{minValue:-1,maxValue:1}}; }
  })
);

// Resize responsive
const ro = new ResizeObserver(() => {
  GC.resize(gcEl.offsetWidth, gcEl.offsetHeight);
  CC.resize(ccEl.offsetWidth, ccEl.offsetHeight);
});
ro.observe(gcEl); ro.observe(ccEl);

/* ══════════ TIMESTAMP PARSER ══════════ */
function parseTs(v) {
  if (!v && v!==0) return Math.floor(Date.now()/1000);
  if (typeof v === 'number') return v > 1e12 ? Math.floor(v/1000) : v;
  const s = String(v).trim().replace(' ','T');
  const ms = new Date(s).getTime();
  if (!isNaN(ms) && ms > 0) {
    const sec = Math.floor(ms/1000);
    // Sanity: timestamp must be within last 10 years and not in future
    const now = Math.floor(Date.now()/1000);
    if (sec > now - 315360000 && sec <= now + 86400) return sec;
  }
  const n = parseInt(v);
  if (!isNaN(n)) return n > 1e12 ? Math.floor(n/1000) : n;
  return Math.floor(Date.now()/1000);
}

/* ══════════ ATR CALCULATION ══════════ */
function calcATR(data, period=14) {
  if (data.length < period+1) return 0;
  let atr = 0;
  for (let i=1; i<=period; i++) {
    const d=data[data.length-period-1+i], p=data[data.length-period-1+i-1];
    const tr = Math.max(d.high-d.low, Math.abs(d.high-p.close), Math.abs(d.low-p.close));
    atr += tr;
  }
  atr /= period;
  // Smooth with last few
  for (let i=data.length-period; i<data.length; i++) {
    const d=data[i], p=data[i-1];
    const tr = Math.max(d.high-d.low, Math.abs(d.high-p.close), Math.abs(d.low-p.close));
    atr = (atr*(period-1)+tr)/period;
  }
  return atr;
}

/* ══════════ EMA ══════════ */
function calcEMA(data, span) {
  const k = 2/(span+1);
  const out = []; let ema = null;
  data.forEach((d,i) => {
    ema = ema===null ? d.close : d.close*k + ema*(1-k);
    if (i >= span-1) out.push({time:d.time, value:+ema.toFixed(3)});
  });
  return out;
}

/* ══════════ CORR SERIES ══════════ */
function buildCorrSeries(data, realCorr) {
  // Génère une courbe de corrélation réaliste ancrée sur la vraie valeur API
  if (!data || data.length < 2) return [];
  const n   = data.length;
  const out = [];
  const target = typeof realCorr === 'number' ? Math.max(-1, Math.min(1, realCorr)) : -0.65;
  // Départ aléatoire dans la plage opposée pour créer du mouvement
  let cv = Math.max(-1, Math.min(1, target + (Math.random() - 0.5) * 0.4));
  for (let i = 0; i < n; i++) {
    // Convergence progressive vers la vraie valeur sur les 20 dernières bougies
    const distFromEnd = n - 1 - i;
    if (distFromEnd < 20) {
      // Interpoler linéairement vers target
      cv = cv + (target - cv) * (1 / (distFromEnd + 1));
    } else {
      cv = Math.max(-1, Math.min(1, cv + (Math.random() - 0.5) * 0.008));
    }
    out.push({ time: data[i].time, value: +cv.toFixed(4) });
  }
  // Forcer la dernière valeur = vraie corrélation API
  if (out.length > 0) out[out.length - 1].value = target;
  return out;
}

function buildChart() {
  const tf   = S.tf;
  const raw  = S.ohlcv[tf];
  const base = S.price > 100 ? S.price : 4328.92;

  // ── 1. Données candles ──
  let data;
  if (raw && raw.length > 5) {
    data = parseAPICandles(raw, base);
  }
  if (!data || data.length < 5) {
    const mkt = getMarketStatus();
    if (mkt.closed) {
      data = simCandles(500, TF_MINS[tf], base);
      showMarketClosedOverlay(mkt);
    } else {
      data = simCandles(500, TF_MINS[tf], base);
      hideMarketClosedOverlay();
    }
  } else {
    hideMarketClosedOverlay();
  }

  // Sort + dédupliquer par timestamp
  data.sort((a, b) => a.time - b.time);
  const seen = new Set();
  data = data.filter(d => { if (seen.has(d.time)) return false; seen.add(d.time); return true; });
  if (!data.length) return;

  // ── 2. Calcul ATR, EMA ──
  S.atr = calcATR(data, 14);
  const ema20 = calcEMA(data, 20);
  const ema50 = calcEMA(data, 50);
  const vol   = data.map(d => ({
    time: d.time, value: d.vol || 500,
    color: d.close >= d.open ? 'rgba(0,212,170,0.4)' : 'rgba(255,77,106,0.4)'
  }));

  // ── 3. Corrélation ──
  const corrData = buildCorrSeries(data, S.corr);

  // ── 4. Alimenter les séries selon le mode candle/line ──
  if (chartMode === 'line') {
    // Cacher les chandeliers, montrer la ligne
    CSER.setData([]);          // vider les chandeliers
    VOLS.setData([]);
    if (!LSER) {
      LSER = GC.addLineSeries({ color:'#f5a623', lineWidth:2, priceLineVisible:false, crosshairMarkerVisible:true });
    }
    LSER.setData(data.map(d => ({ time:d.time, value:d.close })));
  } else {
    // Chandeliers
    if (LSER) { LSER.setData([]); }  // vider la ligne
    CSER.setData(data);
    VOLS.setData(vol);
  }

  E20.setData(ema20);
  E50.setData(ema50);

  // ── 5. Corrélation — setData sur les séries existantes (pas de addLineSeries) ──
  CRS.setData(corrData);
  // Lignes de référence : étendre sur toute la durée du chart
  const t0 = data[0].time, t1 = data[data.length - 1].time;
  const refVals = [-0.6, -0.3, 0, 0.3, 0.6];
  REF_LINES.forEach((ls, i) => {
    ls.setData([{ time: t0, value: refVals[i] }, { time: t1, value: refVals[i] }]);
  });

  // ── 6. TP/SL ──
  drawTPSL(t0, t1);

  // ── 7. Stats jour ──
  S.hArr = data.map(x => x.high);
  S.lArr = data.map(x => x.low);
  const lc = data[data.length - 1];
  setTxt('oh-o', fmt(lc.open));
  setTxt('oh-h', fmt(lc.high));
  setTxt('oh-l', fmt(lc.low));
  setTxt('oh-c', fmt(S.price > 0 ? S.price : lc.close));
  setTxt('oh-v', ((lc.vol || 0) / 1000).toFixed(1) + 'K');
  setTxt('rp-hi', fmt(Math.max(...S.hArr)));
  setTxt('rp-lo', fmt(Math.min(...S.lArr)));

  GC.timeScale().fitContent();
  S.chartTF     = tf;
  S.chartLoaded = true;
  computeATRLevels();
}


function parseAPICandles(raw, realPrice) {
  const data = [];
  raw.forEach(c => {
    const t  = parseTs(c.time);
    const o  = +c.open, h = +c.high, l = +c.low, cl = +c.close;
    if (isNaN(o)||isNaN(h)||isNaN(l)||isNaN(cl)) return;
    if (o<500||h<500||l<500||cl<500) return;   // pas XAUUSD
    if (o>12000||h>12000) return;
    if (h<l || h<Math.min(o,cl) || l>Math.max(o,cl)) return;
    data.push({time:t,open:+o.toFixed(2),high:+h.toFixed(2),
               low:+l.toFixed(2),close:+cl.toFixed(2),
               vol:+(c.volume||c.tick_volume||500)});
  });
  if (data.length>0 && realPrice>100) {
    const last = data[data.length-1];
    last.close = realPrice;
    last.high  = Math.max(last.high, realPrice);
    last.low   = Math.min(last.low,  realPrice);
  }
  return data;
}

function simCandles(n, mins, base) {
  const data=[]; const now=Math.floor(Date.now()/1000);
  let p = base * (1-(Math.random()*0.015+0.005));
  for (let i=0;i<n;i++) {
    const t   = now-(n-1-i)*mins*60;
    const chg = (Math.random()-0.485)*p*0.0015;  // ~$6 par bougie M15 pour XAUUSD
    const o=p, cl=+(p+chg).toFixed(2);
    const sp = Math.abs(chg)*0.6 + p*0.00025;
    const h  = +(Math.max(o,cl)+sp*(0.3+Math.random()*0.7)).toFixed(2);
    const l  = +(Math.min(o,cl)-sp*(0.3+Math.random()*0.7)).toFixed(2);
    data.push({time:t,open:+o.toFixed(2),high:h,low:Math.max(l,1),close:cl,vol:Math.floor(Math.random()*8000+300)});
    p=cl;
  }
  // Anchor to real price
  if (base>100) {
    const off = base - data[data.length-1].close;
    data.forEach(d=>{d.open=+(d.open+off).toFixed(2);d.high=+(d.high+off).toFixed(2);d.low=+(d.low+off).toFixed(2);d.close=+(d.close+off).toFixed(2);});
  }
  return data;
}

function drawTPSL(t0, t1) {
  if (S.tp>0) { try{TPL.setData([{time:t0,value:S.tp},{time:t1,value:S.tp}]);}catch(e){} }
  if (S.sl>0) { try{SLL.setData([{time:t0,value:S.sl},{time:t1,value:S.sl}]);}catch(e){} }
}

/* ══════════ ATR LEVELS ══════════ */
function computeATRLevels() {
  const atr  = S.atr;
  const mode = ATR_MODES[S.atrMode];
  const entry= S.entry>0 ? S.entry : S.price;
  const isBuy= S.sig==='BUY' || S.sig==='WAIT';

  if (!atr || !entry) return;

  const slDist = atr * mode.slMult;
  const tpDist = atr * mode.tpMult;
  const sl = isBuy ? +(entry - slDist).toFixed(2) : +(entry + slDist).toFixed(2);
  const tp = isBuy ? +(entry + tpDist).toFixed(2) : +(entry - tpDist).toFixed(2);
  const rr = (tpDist/slDist).toFixed(1);
  const trail= isBuy ? +(entry + slDist).toFixed(2) : +(entry - slDist).toFixed(2);

  // Update Signal tab
  setTxt('dyn-tp', fmt(tp));    setTxt('dyn-sl', fmt(sl));
  setTxt('dyn-en', fmt(entry)); setTxt('dyn-atr', atr.toFixed(3));
  setTxt('dyn-tp-d', '+'+(isBuy?tpDist:-tpDist).toFixed(2)+' pts ('+mode.tpMult+'×ATR)');
  setTxt('dyn-sl-d', (isBuy?'-':'+')+(slDist).toFixed(2)+' pts ('+mode.slMult+'×ATR)');
  setTxt('dyn-rr', 'R:R 1:'+rr);

  // Explain box
  setTxt('atr-sl-dist', slDist.toFixed(2));
  setTxt('atr-tp-dist', tpDist.toFixed(2));
  setTxt('atr-ratio', rr);
  setTxt('atr-trail', fmt(trail));

  // Update sidebar ATR values
  setTxt('sb-atr',  atr.toFixed(3));
  setTxt('rp-atr',  atr.toFixed(3));
  setTxt('sig-atr', atr.toFixed(3));
  setTxt('tk-atr',  atr.toFixed(3));
  setTxt('rp-atr-m', '×'+mode.slMult+'/×'+mode.tpMult);

  // Override TP/SL in chart & sidebar with ATR values if API signal doesn't have them
  if (S.tp===0 || S.sl===0) {
    S.tp=tp; S.sl=sl;
  }

  // Redraw TP/SL lines with ATR values
  const now=Math.floor(Date.now()/1000);
  const t0=now-250*TF_MINS[S.tf]*60;
  try{TPL.setData([{time:t0,value:tp},{time:now,value:tp}]);}catch(e){}
  try{SLL.setData([{time:t0,value:sl},{time:now,value:sl}]);}catch(e){}

  // Update right panel
  setTxt('rp-tp', fmt(tp)); setTxt('rp-sl', fmt(sl));
  setTxt('rp-tp-d', '+'+(isBuy?tpDist:-tpDist).toFixed(2)+' pts');
  setTxt('rp-sl-d', (isBuy?'-':'+')+(slDist).toFixed(2)+' pts');
  setTxt('sb-tp', fmt(tp)); setTxt('sb-sl', fmt(sl));
  setTxt('sb-rr', '1:'+rr);
}

/* ══════════ API FETCH ══════════ */
/* ══════════ WEBSOCKET BINANCE TEMPS RÉEL ══════════
 * wss://stream.binance.com → XAUUSDT tick + klines M15 réelles
 * Render API → synchro MT5 signal/corrélation toutes les 3s
 ═══════════════════════════════════════════════════════ */
let wsPrice = null, wsKline = null;
let lastBinancePrice = 0, binanceOk = false;
// Offset Binance→MT5 (calibré sur 1ère réponse API)
let priceOffset = 0;

function startBinanceWS() {
  // ── Flux 1 : prix tick par tick ──
  try {
    wsPrice = new WebSocket('wss://stream.binance.com:9443/ws/xauusdt@trade');
    wsPrice.onopen = () => {
      binanceOk = true;
      console.log('[WS] Binance trade stream connecté');
      updateConnStatus(true);
    };
    wsPrice.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data);
        const rawPrice = parseFloat(d.p);
        if (!rawPrice || rawPrice < 100) return;
        // Appliquer offset de calibration MT5
        const price = +(rawPrice + priceOffset).toFixed(2);
        S.prev  = S.price;
        S.price = price;
        S.bid   = +(price - 0.15).toFixed(2);
        S.ask   = +(price + 0.15).toFixed(2);
        S.chg   = +(price - (S.openPrice||price)).toFixed(2);
        S.pct   = +(S.chg / (S.openPrice||price) * 100).toFixed(3);
        // Mise à jour tick immédiate
        tickUpdate();
      } catch(e){}
    };
    wsPrice.onerror = () => { binanceOk=false; updateConnStatus(false); };
    wsPrice.onclose = () => {
      binanceOk=false;
      console.log('[WS] Binance déconnecté - reconnexion dans 5s');
      setTimeout(startBinanceWS, 5000);
    };
  } catch(e) { console.warn('[WS] Binance non disponible:', e.message); }

  // ── Flux 2 : klines M15 réelles ──
  try {
    const tfMap = {M5:'5m', M15:'15m', H1:'1h'};
    const interval = tfMap[S.tf] || '15m';
    wsKline = new WebSocket('wss://stream.binance.com:9443/ws/xauusdt@kline_'+interval);
    wsKline.onmessage = (ev) => {
      try {
        const d = JSON.parse(ev.data);
        const k = d.k;
        if (!k) return;
        const t  = Math.floor(k.t/1000);
        const o  = +(parseFloat(k.o)+priceOffset).toFixed(2);
        const h  = +(parseFloat(k.h)+priceOffset).toFixed(2);
        const l  = +(parseFloat(k.l)+priceOffset).toFixed(2);
        const cl = +(parseFloat(k.c)+priceOffset).toFixed(2);
        const v  = parseFloat(k.v);
        if (cl < 100 || cl > 12000) return;
        try {
          CSER.update({time:t, open:o, high:h, low:l, close:cl});
          VOLS.update({time:t, value:v, color:cl>=o?'rgba(0,212,170,0.4)':'rgba(255,77,106,0.4)'});
          if (S.hArr.length) {
            S.hArr[S.hArr.length-1] = Math.max(S.hArr[S.hArr.length-1], h);
            S.lArr[S.lArr.length-1] = Math.min(S.lArr[S.lArr.length-1], l);
          }
          if (k.x) {
            // Bougie fermée → nouvelle bougie
            S.hArr.push(h); S.lArr.push(l);
          }
        } catch(e){}
        setTxt('oh-o', fmt(o)); setTxt('oh-h', fmt(h));
        setTxt('oh-l', fmt(l)); setTxt('oh-c', fmt(cl));
        setTxt('oh-v', (v/1000).toFixed(1)+'K');
        setTxt('rp-hi', fmt(Math.max(...S.hArr)));
        setTxt('rp-lo', fmt(Math.min(...S.lArr)));
      } catch(e){}
    };
    wsKline.onerror = () => {};
    wsKline.onclose = () => { setTimeout(startBinanceWS, 5000); };
  } catch(e){}
}

function updateConnStatus(wsOk) {
  const da = document.getElementById('dot-api');
  const la = document.getElementById('lbl-api');
  if (da) da.className = 'dot ' + (wsOk||S.apiOk?'g':'y');
  if (la) { la.textContent = wsOk ? 'Binance WS Live ✓' : (S.apiOk?'API Live':'Simulation'); la.style.color=wsOk||S.apiOk?'var(--green)':'var(--gold)'; }
  // Ticker marché
  const tkm = document.getElementById('tk-mkt');
  if (tkm) { tkm.textContent = isMarketClosed()?'FERMÉ':wsOk?'LIVE WS':'API'; tkm.style.color=isMarketClosed()?'var(--red)':wsOk?'var(--green)':'var(--gold)'; }
}

function tickUpdate() {
  // Mise à jour légère sans rebuild chart
  const p=S.price, up=S.chg>=0;
  const CU='var(--green)', CD='var(--red)';
  setTxt('tp-p', fmt(p));
  const tc=document.getElementById('tp-c');
  if(tc){tc.textContent=(up?'▲ +':'▼ ')+Math.abs(S.chg).toFixed(2)+' ('+(up?'+':'')+S.pct.toFixed(2)+'%)';tc.style.color=up?CU:CD;}
  setTxt('sb-g', fmt(p));
  const sc=document.getElementById('sb-gc');
  if(sc){sc.textContent=(up?'▲ +':'▼ ')+Math.abs(S.chg).toFixed(2)+' ('+(up?'+':'')+S.pct.toFixed(2)+'%)';sc.className='chg '+(up?'up':'dn');}
  setTxt('sb-bid',fmt(S.bid)); setTxt('sb-ask',fmt(S.ask));
  setTxt('tk-g', p.toFixed(2));
  const tgc=document.getElementById('tk-gc');if(tgc){tgc.textContent=(up?'▲ +':'▼ ')+Math.abs(S.chg).toFixed(2);tgc.className='tc2 '+(up?'up':'dn');}
  setTxt('oh-c', fmt(p));
  // Update last candle via CS si pas de wsKline actif
  if (!wsKline || wsKline.readyState!==1) {
    const now=Math.floor(Date.now()/1000);
    try{ CSER.update({time:now,open:+(S.prev||p).toFixed(2),high:+Math.max(p,S.prev||p).toFixed(2),low:+Math.min(p,S.prev||p).toFixed(2),close:+p.toFixed(2)}); }catch(e){}
  }
}

/* ── Charger l'historique Binance REST au démarrage ── */
async function fetchBinanceHistory(tf) {
  const tfMap = {M5:'5m', M15:'15m', H1:'1h'};
  const interval = tfMap[tf]||'15m';
  try {
    const url = `https://api.binance.com/api/v3/klines?symbol=XAUUSDT&interval=${interval}&limit=500`;
    const r = await fetch(url, {signal:AbortSignal.timeout(8000)});
    if (!r.ok) return null;
    const raw = await r.json();
    // Format: [openTime, open, high, low, close, volume, ...]
    return raw.map(k => ({
      time:  Math.floor(k[0]/1000),
      open:  +(parseFloat(k[1])+priceOffset).toFixed(2),
      high:  +(parseFloat(k[2])+priceOffset).toFixed(2),
      low:   +(parseFloat(k[3])+priceOffset).toFixed(2),
      close: +(parseFloat(k[4])+priceOffset).toFixed(2),
      volume: parseFloat(k[5]),
    })).filter(d=>d.close>100&&d.close<12000);
  } catch(e) {
    console.warn('[Binance REST] Erreur:', e.message);
    return null;
  }
}

async function fetchSnap() {
  try {
    const r = await fetch(API_URL+'/api/snapshot',{
      headers:{'X-API-Key':API_KEY}, signal:AbortSignal.timeout(7000)
    });
    if (!r.ok) return null;
    return await r.json();
  } catch(e){ return null; }
}

function applySnap(d) {
  if (!d||typeof d!=='object') return;
  S.prev = S.price || +d.gold_price || 3284;
  if (d.gold_price  && +d.gold_price>100)  S.price  = +d.gold_price;
  if (d.dxy_price   && +d.dxy_price>0)     S.dxy    = +d.dxy_price;
  if (typeof d.correlation==='number')      S.corr   = +d.correlation;
  S.bid = d.gold_bid  && +d.gold_bid>0  ? +d.gold_bid  : S.price-0.15;
  S.ask = d.gold_ask  && +d.gold_ask>0  ? +d.gold_ask  : S.price+0.15;
  S.chg = typeof d.gold_change==='number' ? +d.gold_change : S.price-S.prev;
  S.pct = typeof d.gold_pct==='number'    ? +d.gold_pct    : (S.chg/(S.prev||S.price))*100;
  if (typeof d.dxy_change==='number')  S.dxyChg = +d.dxy_change;
  if (typeof d.winrate==='number')     S.wr     = +d.winrate;
  if (typeof d.wins==='number')        S.wins   = +d.wins;
  if (typeof d.losses==='number')      S.losses = +d.losses;
  // MT5 detection - plusieurs clés possibles selon api_server.py
  // ── MT5 : lecture stricte, pas d'inférence
  const mt5Raw = d.mt5_connected ?? d.mt5_status ?? d.connected ?? null;
  if (mt5Raw != null) {
    if (typeof mt5Raw === 'boolean') S.mt5Ok = mt5Raw;
    else if (typeof mt5Raw === 'number') S.mt5Ok = mt5Raw === 1;
    else if (typeof mt5Raw === 'string') {
      S.mt5Ok = ['true','connected','running','1','ok','active'].includes(mt5Raw.toLowerCase());
    }
  } else {
    S.mt5Ok = false;
  }
  // bot_status: 'sleeping'/'weekend' → veille planifiée (≠ erreur)
  S.botStatus = String(d.bot_status || '').toLowerCase();
  S.isWeekend = isMarketClosed();
  if (Array.isArray(d.bot_logs))       S.logs   = d.bot_logs;
  if (Array.isArray(d.signals))        S.signals= d.signals;
  if (d.zones&&typeof d.zones==='object') S.zones=d.zones;
  const sig=d.signal||{};
  if (sig.direction)  S.sig  = sig.direction;
  if (sig.confidence) S.conf = +sig.confidence;
  if (sig.entry&&+sig.entry>0) S.entry=+sig.entry;
  if (sig.tp &&+sig.tp>0)     S.tp   =+sig.tp;
  if (sig.sl &&+sig.sl>0)     S.sl   =+sig.sl;
  if (sig.rr)  S.rr  =+sig.rr;
  if (sig.lot) S.lot =+sig.lot;
  if (sig.pipeline_state) S.pipe=sig.pipeline_state;
  // Fallback prix depuis signal si gold_price manquant
  if ((!S.price||S.price<100) && sig.gold_price && +sig.gold_price>100) S.price=+sig.gold_price;
  const mtf=d.mtf_analysis||d.mtf||{};
  ['H1','M15','M5'].forEach(t=>{if(mtf[t])S.mtf[t]=mtf[t];});
  // Debug log
  console.log('[API] gold='+S.price+' mt5='+S.mt5Ok+' corr='+S.corr+' ohlcv_m15='+(S.ohlcv.M15?.length||0));
  const ohlcv=d.ohlcv||{};
  ['M5','M15','H1'].forEach(tf=>{
    if(ohlcv[tf]&&Array.isArray(ohlcv[tf])&&ohlcv[tf].length>5) {
      S.ohlcv[tf]=ohlcv[tf];
      if(tf===S.tf) S.chartTF='';
    }
  });
  // ── Monitor alert (TradeMonitor) ──
  const alert = sig.monitor_alert ?? d.monitor_alert ?? null;
  if (alert && alert !== S.lastAlert) {
    S.lastAlert     = alert;
    S.lastAlertTime = Date.now();
    showAlert(alert);
  }
  // ── Résultat trade (WIN/LOSS/OPEN) depuis le signal ──
  const res = sig.result ?? sig.trade_result ?? d.trade_result ?? null;
  if (res) {
    S.tradeResult = String(res).toUpperCase();
    if (S.tradeResult === 'WIN' || S.tradeResult === 'LOSS') {
      // Trade terminé → réinitialiser TP/SL affichés
      S.tp = 0; S.sl = 0; S.entry = 0;
      showTradeResult(S.tradeResult, sig.profit ?? 0);
    }
  } else {
    // Pas de résultat = trade potentiellement en cours ou WAIT
    if (S.sig !== 'BUY' && S.sig !== 'SELL') S.tradeResult = '';
    else if (!S.tradeResult) S.tradeResult = 'OPEN';
  }
}

/* ══════════ UI ══════════ */
function fmt(v){return (+v).toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2});}
function setTxt(id,v){const e=document.getElementById(id);if(e)e.textContent=v;}
function setCol(id,c){const e=document.getElementById(id);if(e)e.style.color=c;}

function updateUI() {
  const p=S.price, up=S.chg>=0;
  const C_UP='var(--green)', C_DN='var(--red)', C_MU='var(--muted)';

  // Topbar
  setTxt('tp-p', p>0?fmt(p):'—');
  const tpc=document.getElementById('tp-c');
  if(tpc){tpc.textContent=(up?'▲ +':'▼ ')+Math.abs(S.chg).toFixed(2)+' ('+(up?'+':'')+S.pct.toFixed(2)+'%)';tpc.style.color=up?C_UP:C_DN;}
  setTxt('tp-cf',S.conf+'%');
  const tpb=document.getElementById('tp-b');
  if(tpb){tpb.textContent='● '+S.sig;tpb.className='badge '+(S.sig==='BUY'?'buy':S.sig==='SELL'?'sell':'wait');}
  setTxt('acct-s',S.apiOk?'Live':'Simulation');

  // Sidebar Gold
  setTxt('sb-g',p>0?fmt(p):'—');
  const sgc=document.getElementById('sb-gc');
  if(sgc){sgc.textContent=(up?'▲ +':'▼ ')+Math.abs(S.chg).toFixed(2)+' ('+(up?'+':'')+S.pct.toFixed(2)+'%)';sgc.className='chg '+(up?'up':'dn');}
  setTxt('sb-bid',S.bid>0?fmt(S.bid):'—');setTxt('sb-ask',S.ask>0?fmt(S.ask):'—');

  // DXY
  setTxt('sb-d',S.dxy?S.dxy.toFixed(3):'—');
  const sdc=document.getElementById('sb-dc');
  const dup=S.dxyChg>=0;
  if(sdc){sdc.textContent=(dup?'▲ +':'▼ ')+Math.abs(S.dxyChg).toFixed(4);sdc.className='chg '+(dup?'up':'dn');}

  // Corr
  const cr=S.corr||0;
  const cc=cr<-0.6?C_UP:cr<-0.4?'var(--gold)':C_DN;
  const ct=cr<-0.6?'✅ Forte — signal possible':cr<-0.4?'⚠️ Modérée — attendre':'❌ Faible — éviter';
  ['sb-cr','sig-cr'].forEach(id=>{setTxt(id,cr.toFixed(4));setCol(id,cc);});
  const crb=document.getElementById('sb-crb');if(crb){crb.style.width=(Math.abs(cr)*100)+'%';crb.style.background=cc;}
  setTxt('sb-crt',ct);setCol('sb-crt',cc);

  // Signal everywhere
  const sig=S.sig;
  ['sb-sb','sig-b'].forEach(id=>{
    const e=document.getElementById(id);
    if(e){e.textContent=sig;e.className='sb-badge '+(sig==='BUY'?'buy':sig==='SELL'?'sell':'wait');}
  });
  ['sb-cf','sig-cf'].forEach(id=>setTxt(id,S.conf+'%'));
  setTxt('sb-en',S.entry>0?fmt(S.entry):'—');
  setTxt('sb-pipe',S.pipe||'IDLE');setTxt('sig-pp',S.pipe||'IDLE');
  setTxt('sb-lot',S.lot>0?S.lot.toFixed(2):'—');
  setTxt('rp-en',S.entry>0?fmt(S.entry):'—');

  // Perf
  const wr=S.wins+S.losses>0?Math.round(S.wins/(S.wins+S.losses)*100):(S.wr||0);
  setTxt('sb-wr',wr+'%');setTxt('sb-wl',S.wins+'/'+S.losses);
  setTxt('rp-wr',wr+'%');setTxt('rp-tr',S.wins+S.losses);setTxt('rp-wl',S.wins+'W · '+S.losses+'L');
  const rwb=document.getElementById('rp-wr-b');if(rwb)rwb.style.width=wr+'%';
  const risk=wr>65?'Low':wr>50?'Moderate':'High';
  const riskC=wr>65?C_UP:wr>50?'var(--gold)':C_DN;
  const riskP=wr>65?25:wr>50?50:80;
  setTxt('rp-risk-l',risk);setCol('rp-risk-l',riskC);
  setTxt('risk-l',risk);setCol('risk-l',riskC);
  const rb=document.getElementById('rp-risk-b');if(rb){rb.style.width=riskP+'%';rb.style.background=riskC;}
  const rds=document.querySelectorAll('#rdots .rd');
  const nd=wr>65?2:wr>50?3:5,rc=wr>65?'g':wr>50?'y':'r';
  rds.forEach((d,i)=>{d.className='rd'+(i<nd?' '+rc:'');});

  // Live price in signal tab
  setTxt('sig-pb',p>0?fmt(p):'—');
  const spc=document.getElementById('sig-pc');
  if(spc){spc.textContent=(up?'▲ +':'▼ ')+Math.abs(S.chg).toFixed(2)+' ('+(up?'+':'')+S.pct.toFixed(2)+'%)';spc.style.color=up?C_UP:C_DN;}
  setTxt('sig-bid',S.bid>0?fmt(S.bid):'—');setTxt('sig-ask',S.ask>0?fmt(S.ask):'—');
  setTxt('sig-dxy',S.dxy?S.dxy.toFixed(3):'—');
  const z=S.zones||{};
  setTxt('sig-sup',z.support&&z.support>0?fmt(z.support):'—');
  setTxt('sig-res',z.resistance&&z.resistance>0?fmt(z.resistance):'—');
  setTxt('sig-fb',(z.fvg_bullish||[]).length+' zones');
  setTxt('sig-fs',(z.fvg_bearish||[]).length+' zones');

  // Multi-TF
  ['H1','M15','M5'].forEach(tf=>{
    const k=tf.toLowerCase(),d=S.mtf[tf]||{};
    const v=d.signal||'—',cr2=typeof d.corr==='number'?d.corr.toFixed(4):'—',tr=d.trend||'—';
    const e1=document.getElementById('mtf-'+k);if(e1){e1.textContent=v;e1.className='ts '+(v==='BUY'?'buy':v==='SELL'?'sell':'wait');}
    const e2=document.getElementById('mtf-big-'+k);if(e2){e2.textContent=v;e2.className='sb-badge '+(v==='BUY'?'buy':v==='SELL'?'sell':'wait');}
    setTxt('mtf-cr-'+k,cr2);setTxt('mtf-tr-'+k,tr);
  });
  const sigs=['H1','M15','M5'].map(t=>(S.mtf[t]||{}).signal||'WAIT');
  const nb=sigs.filter(s=>s==='BUY').length,ns=sigs.filter(s=>s==='SELL').length;
  const consT=nb>=2?'🟢 CONSENSUS BUY':ns>=2?'🔴 CONSENSUS SELL':'⚪ PAS DE CONSENSUS';
  const consC=nb>=2?C_UP:ns>=2?C_DN:'var(--gold)';
  setTxt('cons-txt',consT);setCol('cons-txt',consC);
  setTxt('cons-sub','H1: '+sigs[0]+' · M15: '+sigs[1]+' · M5: '+sigs[2]);

  // Connexion
  const da=document.getElementById('dot-api');if(da)da.className='dot '+(S.apiOk?'g':'y');
  setTxt('lbl-api',S.apiOk?'API Live':'Simulation');setCol('lbl-api',S.apiOk?C_UP:'var(--gold)');
  const dm=document.getElementById('dot-mt5');if(dm)dm.className='dot '+(S.mt5Ok?'g':isMarketClosed()?'y':S.apiOk?'r':'y');
  const isWknd = isMarketClosed();
  let mt5Lbl, mt5Col;
  if (S.mt5Ok) {
    mt5Lbl = 'MT5 Connecté ✓'; mt5Col = C_UP;
  } else if (isWknd) {
    mt5Lbl = '💤 Veille Weekend'; mt5Col = 'var(--gold)';
  } else if (S.botStatus && ['sleeping','paused','idle'].includes(S.botStatus)) {
    mt5Lbl = '⏸ Bot en veille'; mt5Col = 'var(--gold)';
  } else if (S.apiOk) {
    mt5Lbl = '⚠ MT5 Hors ligne'; mt5Col = C_DN;
  } else {
    mt5Lbl = 'MT5 En attente...'; mt5Col = 'var(--muted)';
  }
  setTxt('lbl-mt5', mt5Lbl); setCol('lbl-mt5', mt5Col);

  // Historique
  setTxt('ht-tot',S.signals.length);setTxt('ht-wr',wr+'%');setTxt('ht-w',S.wins);setTxt('ht-l',S.losses);
  const hb=document.getElementById('ht-body');
  if(hb){
    if(!S.signals.length){hb.innerHTML='<tr><td colspan="9" style="color:var(--muted);text-align:center;padding:20px">Aucun signal</td></tr>';}
    else {
      hb.innerHTML=[...S.signals].reverse().slice(0,50).map(s=>{
        const rc=s.result==='WIN'?C_UP:s.result==='LOSS'?C_DN:s.result==='OPEN'?'var(--gold)':C_MU;
        const dc=s.direction==='BUY'?C_UP:s.direction==='SELL'?C_DN:C_MU;
        const rl=s.result==='WIN'?'✅ WIN':s.result==='LOSS'?'❌ LOSS':s.result==='OPEN'?'🔵 OPEN':s.result||'—';
        return `<tr><td style="color:var(--muted)">${(s.time||'').slice(-8)||'—'}</td>
          <td style="color:${dc};font-weight:700">${s.direction||'—'}</td>
          <td>${s.tf||'—'}</td>
          <td>${s.entry>0?fmt(s.entry):'—'}</td>
          <td style="color:var(--green)">${s.tp>0?fmt(s.tp):'—'}</td>
          <td style="color:var(--red)">${s.sl>0?fmt(s.sl):'—'}</td>
          <td>${s.rr?'1:'+s.rr:'—'}</td>
          <td>${s.lot||'—'}</td>
          <td style="color:${rc};font-weight:700">${rl}</td></tr>`;
      }).join('');
    }
  }

  // Logs
  renderLogs();

  // Ticker
  setTxt('tk-g',p>0?p.toFixed(2):'—');
  const tgc=document.getElementById('tk-gc');if(tgc){tgc.textContent=(up?'▲ +':'▼ ')+Math.abs(S.chg).toFixed(2);tgc.className='tc2 '+(up?'up':'dn');}
  setTxt('tk-d',S.dxy?S.dxy.toFixed(3):'—');
  const tdc=document.getElementById('tk-dc');if(tdc){tdc.textContent=(dup?'▲':'▼')+Math.abs(S.dxyChg).toFixed(4);tdc.className='tc2 '+(dup?'up':'dn');}
  setTxt('tk-cr',cr.toFixed(3));
  const tcl=document.getElementById('tk-crl');if(tcl){tcl.textContent=cr<-0.6?'✅ FORTE':cr<-0.4?'⚠️ MOD':'❌ FAIBLE';tcl.className='tc2 '+(cr<-0.5?'up':'dn');}
  setTxt('tk-sig',sig);setCol('tk-sig',sig==='BUY'?C_UP:sig==='SELL'?C_DN:C_MU);
  setTxt('tk-cf2',S.conf+'%');
  setTxt('tk-pp',S.pipe||'IDLE');
  setTxt('tk-api',S.apiOk?'LIVE':'SIM');setCol('tk-api',S.apiOk?C_UP:'var(--gold)');
  setTxt('tk-n',S.tick);setTxt('sb-tk',S.tick);

  const now=new Date().toLocaleTimeString('fr-FR');
  setTxt('clock',now);setTxt('sb-tm',now);
}

function renderLogs(){
  const lb=document.getElementById('logs-body');if(!lb)return;
  const logs=S.logs||[];
  if(!logs.length){lb.innerHTML='<div style="color:var(--muted);padding:20px">Aucun log</div>';return;}
  const filt=logs.filter(l=>S.logFilter==='ALL'||(l.level||'').toUpperCase()===S.logFilter).slice(-120).reverse();
  lb.innerHTML=filt.map(l=>{
    const lv=(l.level||'INFO').toUpperCase();
    const cl={INFO:'i',WARNING:'w',ERROR:'e',SIGNAL:'s'}[lv]||'i';
    return `<div class="ll ${cl}">${l.time||''} [${lv}] ${l.msg||''}</div>`;
  }).join('');
}

/* ══════════ ALERTS & TRADE RESULTS ══════════ */
let alertTimer = null;

function showAlert(msg) {
  const banner = document.getElementById('alert-banner');
  const msgEl  = document.getElementById('ab-msg');
  const timeEl = document.getElementById('ab-time');
  if (!banner || !msg) return;
  msgEl.textContent  = msg;
  timeEl.textContent = new Date().toLocaleTimeString('fr-FR');
  banner.style.display = 'flex';
  // Auto-dismiss après 30s
  clearTimeout(alertTimer);
  alertTimer = setTimeout(dismissAlert, 30000);
  // Notification son (bip discret)
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = 880;
    osc.type = 'sine';
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
    osc.start(); osc.stop(ctx.currentTime + 0.4);
  } catch(e){}
  // Faire clignoter le titre de la page
  let blink = 0;
  const origTitle = document.title;
  const blinkTimer = setInterval(() => {
    document.title = blink++ % 2 === 0 ? '🚨 ALERTE BOT — ' + origTitle : origTitle;
    if (blink > 10) { clearInterval(blinkTimer); document.title = origTitle; }
  }, 500);
}

function dismissAlert() {
  const banner = document.getElementById('alert-banner');
  if (banner) banner.style.display = 'none';
  clearTimeout(alertTimer);
}

function showTradeResult(result, profit) {
  const toast  = document.getElementById('trade-toast');
  const title  = document.getElementById('tt-title');
  const sub    = document.getElementById('tt-sub');
  if (!toast) return;
  if (result === 'WIN') {
    toast.className = 'win';
    title.textContent = '✅ TRADE GAGNANT';
    sub.textContent   = profit ? 'Profit: +' + (+profit).toFixed(2) + ' USD' : 'TP atteint';
  } else if (result === 'LOSS') {
    toast.className = 'loss';
    title.textContent = '❌ TRADE PERDANT';
    sub.textContent   = profit ? 'Perte: ' + (+profit).toFixed(2) + ' USD' : 'SL touché';
  }
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 8000);
}

/* Vérifier si TP/SL touché côté dashboard (si l'API ne le dit pas) */
function checkTPSL() {
  if (!S.entry || !S.tp || !S.sl || !S.price) return;
  if (S.tradeResult === 'WIN' || S.tradeResult === 'LOSS') return;
  if (S.sig !== 'BUY' && S.sig !== 'SELL') return;
  const isBuy = S.sig === 'BUY';
  let hit = null;
  if (isBuy) {
    if (S.price >= S.tp) hit = 'WIN';
    else if (S.price <= S.sl) hit = 'LOSS';
  } else {
    if (S.price <= S.tp) hit = 'WIN';
    else if (S.price >= S.sl) hit = 'LOSS';
  }
  if (hit) {
    S.tradeResult = hit;
    const profit = hit==='WIN' ? Math.abs(S.tp - S.entry) * (S.lot||0.1) * 100
                               : -Math.abs(S.entry - S.sl) * (S.lot||0.1) * 100;
    showTradeResult(hit, profit);
    // Alert aussi
    showAlert((hit==='WIN'?'✅ TP atteint':'🛑 SL touché') +
              ' — XAUUSD @ ' + S.price.toFixed(2));
    S.tp = 0; S.sl = 0; S.entry = 0;
  }
}

/* ══════════ MARKET HOURS ══════════ */
function isMarketClosed() {
  // Forex/Gold fermé : vendredi 22:00 UTC → dimanche 22:00 UTC
  const now = new Date();
  const day = now.getUTCDay();   // 0=dim, 1=lun, ..., 5=ven, 6=sam
  const hour = now.getUTCHours();
  if (day === 6) return true;                        // samedi entier
  if (day === 0 && hour < 22) return true;           // dimanche avant 22h UTC
  if (day === 5 && hour >= 22) return true;          // vendredi après 22h UTC
  return false;
}

function getMarketStatus() {
  if (isMarketClosed()) {
    const now = new Date();
    const day = now.getUTCDay();
    // Calcul réouverture : dimanche 22:00 UTC
    const reopen = new Date(now);
    const daysUntilSun = (7 - day) % 7 || 7;
    reopen.setUTCDate(now.getUTCDate() + (day===0 ? 0 : daysUntilSun));
    reopen.setUTCHours(22, 0, 0, 0);
    const diff = reopen - now;
    const hh = Math.floor(diff/3600000);
    const mm = Math.floor((diff%3600000)/60000);
    return { closed: true, label: '🔴 Marché FERMÉ', sub: `Réouverture dans ${hh}h${mm}m (dim. 22:00 UTC)` };
  }
  return { closed: false, label: '🟢 Marché OUVERT', sub: 'Gold · Forex' };
}

function updateMarketBanner() {
  const st = getMarketStatus();
  const banner = document.getElementById('market-banner');
  const bannerTxt = document.getElementById('market-banner-txt');
  const bannerSub = document.getElementById('market-banner-sub');
  if (!banner) return;
  if (st.closed) {
    banner.style.display = 'flex';
    if (bannerTxt) bannerTxt.textContent = st.label;
    if (bannerSub) bannerSub.textContent = st.sub;
  } else {
    banner.style.display = 'none';
  }
  // Ticker marché
  const tkMkt = document.getElementById('tk-mkt');
  if (tkMkt) { tkMkt.textContent = st.closed ? '⏸ FERMÉ' : '● OUVERT'; tkMkt.style.color = st.closed ? 'var(--red)' : 'var(--green)'; }
}


/* ══════════ MARKET CLOSED OVERLAY ══════════ */
function showMarketClosedOverlay(mkt) {
  let ov = document.getElementById('market-overlay');
  if (!ov) {
    ov = document.createElement('div');
    ov.id = 'market-overlay';
    ov.style.cssText = [
      'position:absolute','inset:0','z-index:50',
      'display:flex','flex-direction:column',
      'align-items:center','justify-content:center',
      'background:rgba(11,15,26,0.82)',
      'backdrop-filter:blur(4px)',
      'border-radius:9px','pointer-events:none'
    ].join(';');
    const cw = document.getElementById('cw');
    if (cw) { cw.style.position='relative'; cw.appendChild(ov); }
  }
  ov.innerHTML = `
    <div style="font-size:2rem;margin-bottom:8px">🔒</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:1rem;
      font-weight:700;color:#f5a623;margin-bottom:4px">MARCHÉ FERMÉ</div>
    <div style="font-size:.62rem;color:#4a5568;margin-bottom:6px">
      Weekend — Gold/Forex suspendu</div>
    <div style="font-size:.58rem;color:#00d4aa;font-weight:600">
      Réouverture dans ${mkt.reopenIn||'—'}</div>
    <div style="font-size:.5rem;color:#4a5568;margin-top:3px">${mkt.reopenTime||''}</div>
    <div style="font-size:.5rem;color:#2e3a4e;margin-top:8px">
      Données affichées : historique OHLCV</div>`;
  ov.style.display='flex';
}
function hideMarketClosedOverlay() {
  const ov = document.getElementById('market-overlay');
  if (ov) ov.style.display='none';
}

/* ══════════ MAIN LOOP ══════════ */
async function mainLoop() {
  S.tick++;

  // ── 1. Render API → signal, corrélation, MT5, OHLCV ──
  const snap = await fetchSnap();
  if (snap) {
    S.apiOk = true;
    const prevP = S.price;
    applySnap(snap);
    // Calibrer offset Binance↔MT5 à la 1ère réponse
    if (lastBinancePrice > 100 && S.price > 100 && priceOffset === 0) {
      priceOffset = +(S.price - lastBinancePrice).toFixed(2);
      console.log('[Cal] Offset Binance→MT5:', priceOffset);
    }
    // Ne pas écraser le prix si Binance WS actif (plus frais)
    if (!binanceOk) {
      S.prev = prevP || S.price;
      S.chg  = +(S.price - S.prev).toFixed(2);
      S.pct  = +(S.chg / (S.prev||S.price) * 100).toFixed(3);
    }
    if (!S.openPrice && S.price>0) S.openPrice = S.price;
  } else {
    S.apiOk = false;
    if (!binanceOk && !isMarketClosed()) {
      S.prev   = S.price || 4328.92;
      if (!S.price) S.price = 4328.92;
      S.price  = +(S.price + (Math.random()-0.48)*0.5).toFixed(2);
      S.dxy    = +(S.dxy   - (Math.random()-0.48)*0.01).toFixed(3);
      S.corr   = +Math.max(-1,Math.min(1,S.corr+(Math.random()-0.5)*0.005)).toFixed(4);
      S.chg    = +(S.price - S.prev).toFixed(2);
      S.pct    = +(S.chg / (S.prev||S.price) * 100).toFixed(3);
    } else if (isMarketClosed()) { S.chg=0; S.pct=0; }
    S.dxyChg = +(S.dxy-104.23).toFixed(4);
    S.bid = +(S.price-0.15).toFixed(2); S.ask = +(S.price+0.15).toFixed(2);
    if (!S.entry) S.entry = S.price;
  }

  // ── 2. Chart rebuild si TF changé ou 1er chargement ──
  if (!S.chartLoaded || S.chartTF !== S.tf) {
    // Essayer Binance REST pour l'historique réel
    const binD = await fetchBinanceHistory(S.tf);
    if (binD && binD.length > 10) {
      console.log('[Binance REST]', binD.length, 'bougies chargées');
      // Appliquer offset
      S.ohlcv[S.tf] = binD.map(d => ({
        time: d.time, open: d.open, high: d.high,
        low: d.low, close: d.close, volume: d.volume
      }));
      // Calibrer offset si API pas encore répondu
      if (S.price > 100 && priceOffset === 0) {
        const lc = binD[binD.length-1].close;
        if (Math.abs(S.price - lc) < 200) {
          priceOffset = +(S.price - lc).toFixed(2);
          // Re-appliquer offset sur les données
          S.ohlcv[S.tf] = S.ohlcv[S.tf].map(d => ({
            ...d,
            open:  +(d.open+priceOffset).toFixed(2),
            high:  +(d.high+priceOffset).toFixed(2),
            low:   +(d.low+priceOffset).toFixed(2),
            close: +(d.close+priceOffset).toFixed(2),
          }));
        }
      }
    }
    buildChart();
    // Lancer WS Binance après 1er chart
    if (!wsPrice || wsPrice.readyState > 1) startBinanceWS();
  } else {
    // Mise à jour live si pas de WS kline Binance
    if (!binanceOk || !wsKline || wsKline.readyState !== 1) {
      const now=Math.floor(Date.now()/1000), p=S.price, pv=S.prev||p;
      if (p>100) {
        try { CSER.update({time:now,open:+pv.toFixed(2),
          high:+Math.max(p,pv).toFixed(2),low:+Math.min(p,pv).toFixed(2),
          close:+p.toFixed(2)});
          if (S.hArr.length) {
            S.hArr[S.hArr.length-1]=Math.max(S.hArr[S.hArr.length-1],p);
            S.lArr[S.lArr.length-1]=Math.min(S.lArr[S.lArr.length-1],p);
          }
        } catch(e){}
        try { CRS.update({time:now, value:S.corr}); } catch(e){}
      }
    }
    computeATRLevels();
  }

  updateConnStatus(binanceOk);
  updateUI();
  setTimeout(mainLoop, S.apiOk?3000:2500);
}

/* ══════════ CONTROLS ══════════ */

// ── Navigation onglets ──
function goTab(tab, btn) {
  document.querySelectorAll('.tab-panel').forEach(e => e.classList.remove('active'));
  document.querySelectorAll('.nav-btn,.ib').forEach(e => e.classList.remove('active'));
  const p = document.getElementById('p-' + tab);
  if (p) p.classList.add('active');
  if (btn) btn.classList.add('active');
  // Forcer resize du chart si on revient sur l'onglet chart
  if (tab === 'chart') {
    setTimeout(() => {
      GC.resize(gcEl.offsetWidth, gcEl.offsetHeight);
      CC.resize(ccEl.offsetWidth, ccEl.offsetHeight);
    }, 60);
  }
}

// ── Sidebar TF (M5 / M15 / H1) ──
function setTF(tf, el) {
  if (S.tf === tf) return;  // Rien à faire si déjà ce TF
  S.tf          = tf;
  S.chartTF     = '';       // Forcer rebuild
  S.chartLoaded = false;
  document.querySelectorAll('.tf-tab').forEach(e => e.classList.remove('active'));
  el.classList.add('active');
  // Fermer le WS kline et le relancer sur le bon interval
  if (wsKline && wsKline.readyState <= 1) { wsKline.close(); wsKline = null; }
  buildChart();
}

// ── Pills TF du chart toolbar (1m, 5m, 15m, 1h…) ──
const PILL_TF_MAP = { '1m':'M5','5m':'M5','10m':'M5','15m':'M15','1h':'H1','5h':'H1','All':'H1' };
const PILL_MINS   = { '1m':1, '5m':5, '10m':10, '15m':15, '1h':60, '5h':300, 'All':240 };

function setPill(el, tf, mins) {
  document.querySelectorAll('.tf-pill').forEach(e => e.classList.remove('active'));
  el.classList.add('active');
  const label = el.textContent.trim();
  const newTF = tf || PILL_TF_MAP[label] || 'M15';
  // Synchroniser aussi les sidebar tabs
  document.querySelectorAll('.tf-tab').forEach(e => {
    e.classList.toggle('active', e.textContent.trim() === newTF);
  });
  if (S.tf !== newTF) {
    S.tf          = newTF;
    S.chartTF     = '';
    S.chartLoaded = false;
    if (wsKline && wsKline.readyState <= 1) { wsKline.close(); wsKline = null; }
    buildChart();
  }
}

// ── Mode Candle / Line ──
function setChartType(t) {
  if (chartMode === t) return;  // Déjà dans ce mode
  chartMode = t;
  document.getElementById('btn-c').classList.toggle('active', t === 'candle');
  document.getElementById('btn-l').classList.toggle('active', t === 'line');
  // Rebuild les séries (sans changer le TF)
  buildChart();
}

// ── Buy / Sell ──
function setSig(d) {
  S.sig = d;
  const b = document.getElementById('rp-buy');
  const s = document.getElementById('rp-sell');
  if (d === 'BUY') {
    if (b) { b.style.background='var(--green)'; b.style.color='#000'; b.style.border='none'; }
    if (s) s.classList.remove('on');
  } else {
    if (s) s.classList.add('on');
    if (b) { b.style.background='var(--bg3)'; b.style.color='var(--muted)'; b.style.border='1px solid var(--border)'; }
  }
  computeATRLevels();
  updateUI();
}

// ── ATR mode ──
function setATRMode(mode, el) {
  S.atrMode = mode;
  document.querySelectorAll('.atr-btn').forEach(e => e.classList.remove('active'));
  el.classList.add('active');
  const explain = document.getElementById('atr-explain');
  if (explain) explain.querySelector('b').textContent = ATR_MODES[mode].label;
  computeATRLevels();
}

// ── Log filter ──
function filterLog(f, el) {
  S.logFilter = f;
  document.querySelectorAll('.log-tb .ct-btn').forEach(e => e.classList.remove('active'));
  el.classList.add('active');
  renderLogs();
}

/* ══════════ DÉMARRAGE ══════════ */
(function init() {
  // Prix affiché immédiatement — données Python pré-générées
  S.price = 4328.92; S.bid = 4328.77; S.ask = 4329.07;
  S.openPrice = 4328.92; S.chg = 0; S.pct = 0;
  buildChart();   // Chart visible dès la 1ère frame
  updateUI();
})();

mainLoop();  // Lance API Render + Binance WebSocket

</script>
</body>
</html>
""".replace('APIURL_PLACEHOLDER', API_URL).replace('APIKEY_PLACEHOLDER', API_KEY).replace('"OHLCV_PLACEHOLDER"', INIT_OHLCV_JSON)

components.html(HTML, height=10000, scrolling=False)
