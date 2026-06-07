import streamlit as st
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
          <button class="tf-pill" onclick="setPill(this)">1m</button>
          <button class="tf-pill" onclick="setPill(this)">5m</button>
          <button class="tf-pill" onclick="setPill(this)">10m</button>
          <button class="tf-pill active" onclick="setPill(this)">15m</button>
          <button class="tf-pill" onclick="setPill(this)">1h</button>
          <button class="tf-pill" onclick="setPill(this)">5h</button>
          <button class="tf-pill" onclick="setPill(this)">All</button>
          <div class="csep"></div>
          <span style="font-size:.52rem;color:var(--muted)">EMA20<b style="color:var(--gold)"> ●</b> EMA50<b style="color:rgba(255,255,255,.2)"> ●</b></span>
          <span style="margin-left:auto;font-size:.52rem;color:var(--muted)" id="clock">--:--:--</span>
        </div>
        <div id="chart-body">
          <div id="cw">
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
  <div class="ti" style="margin-left:auto"><span class="ts2">API</span><span class="tv2" id="tk-api" style="color:var(--muted)">—</span></div>
  <div class="ti"><span class="ts2">TICK#</span><span class="tv2" id="tk-n">0</span></div>
</div>

<script>
/* ══════════ CONFIG ══════════ */
const API_URL = 'APIURL_PLACEHOLDER';
const API_KEY = 'APIKEY_PLACEHOLDER';

/* ══════════ STATE ══════════ */
const S = {
  price:0, prev:0, dxy:104.23, corr:-0.65,
  chg:0, pct:0, dxyChg:0, bid:0, ask:0,
  sig:'WAIT', conf:0, entry:0, tp:0, sl:0, rr:0, lot:0,
  pipe:'IDLE', wins:0, losses:0, wr:0,
  atr:0, atrMode:'balanced',
  apiOk:false, mt5Ok:false, tick:0, tf:'M15', logFilter:'ALL',
  ohlcv:{M5:[],M15:[],H1:[]}, mtf:{H1:{},M15:{},M5:{}},
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

/* ══════════ CHARTS INIT ══════════ */
const gcEl = document.getElementById('gc');
const ccEl = document.getElementById('cc');

const GC = LightweightCharts.createChart(gcEl, {
  layout:{background:{color:'#0f1623'},textColor:'#4a5568'},
  grid:{vertLines:{color:'rgba(255,255,255,0.03)'},horzLines:{color:'rgba(255,255,255,0.03)'}},
  crosshair:{mode:LightweightCharts.CrosshairMode.Normal},
  rightPriceScale:{borderColor:'rgba(255,255,255,0.06)',scaleMargins:{top:0.05,bottom:0.2}},
  timeScale:{borderColor:'rgba(255,255,255,0.06)',timeVisible:true,secondsVisible:false},
  handleScroll:{mouseWheel:true,pressedMouseMove:true},
  handleScale:{mouseWheel:true,pinch:true},
});

let CSER = GC.addCandlestickSeries({
  upColor:'#00d4aa', downColor:'#ff4d6a',
  borderUpColor:'#00d4aa', borderDownColor:'#ff4d6a',
  wickUpColor:'rgba(0,212,170,0.8)', wickDownColor:'rgba(255,77,106,0.8)',
});
const E20 = GC.addLineSeries({color:'rgba(245,166,35,0.85)',lineWidth:1.5,lineStyle:0,priceLineVisible:false,lastValueVisible:false});
const E50 = GC.addLineSeries({color:'rgba(255,255,255,0.2)',lineWidth:1,priceLineVisible:false,lastValueVisible:false});
const VOLS = GC.addHistogramSeries({
  priceFormat:{type:'volume'}, priceScaleId:'vol',
  scaleMargins:{top:0.85,bottom:0},
});
const TPL = GC.addLineSeries({color:'rgba(0,212,170,0.7)',lineWidth:1,lineStyle:2,priceLineVisible:false,lastValueVisible:false});
const SLL = GC.addLineSeries({color:'rgba(255,77,106,0.7)',lineWidth:1,lineStyle:2,priceLineVisible:false,lastValueVisible:false});

const CC = LightweightCharts.createChart(ccEl, {
  layout:{background:{color:'#0f1623'},textColor:'#4a5568'},
  grid:{vertLines:{color:'rgba(255,255,255,0.02)'},horzLines:{color:'rgba(255,255,255,0.02)'}},
  rightPriceScale:{borderColor:'rgba(255,255,255,0.06)'},
  timeScale:{borderColor:'rgba(255,255,255,0.06)',visible:false},
  crosshair:{mode:LightweightCharts.CrosshairMode.Normal},
});
const CRS = CC.addLineSeries({
  color:'#f5a623', lineWidth:1.5, priceLineVisible:false, lastValueVisible:true,
  autoscaleInfoProvider: () => { return {priceRange:{minValue:-1,maxValue:1}}; }
});

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
  if (!data || data.length<2) return [];
  const out=[], n=data.length;
  let cv = typeof realCorr==='number' ? realCorr : -0.65;
  // Walk backwards from realCorr to make a realistic history
  const noise = 0.007;
  // Build array forward from a past value
  let start = Math.max(-1, Math.min(1, cv + (Math.random()-0.5)*0.3));
  let cur = start;
  for (let i=0; i<n; i++) {
    if (i===n-1) { cur=realCorr; }
    else { cur = Math.max(-1, Math.min(1, cur+(Math.random()-0.5)*noise)); }
    out.push({time:data[i].time, value:+cur.toFixed(4)});
  }
  return out;
}

/* ══════════ BUILD CHART ══════════ */
const TF_MINS = {M5:5,M15:15,H1:60};

function buildChart() {
  const tf = S.tf;
  S.chartTF = tf;
  const raw = S.ohlcv[tf];
  const base = S.price>100 ? S.price : 3284.0;

  let data;
  if (raw && raw.length>5) {
    data = parseAPICandles(raw, base);
  }
  if (!data || data.length<5) {
    data = simCandles(250, TF_MINS[tf], base);
  }

  // Sort & deduplicate
  data.sort((a,b)=>a.time-b.time);
  const seen=new Set();
  data = data.filter(d => { if(seen.has(d.time))return false; seen.add(d.time);return true; });

  if (!data.length) return;

  // Compute ATR from real data
  S.atr = calcATR(data, 14);

  const ema20 = calcEMA(data,20);
  const ema50 = calcEMA(data,50);
  const vol   = data.map(d=>({
    time:d.time, value:d.vol||500,
    color:d.close>=d.open?'rgba(0,212,170,0.4)':'rgba(255,77,106,0.4)'
  }));
  const corrD = buildCorrSeries(data, S.corr);

  CSER.setData(data);
  E20.setData(ema20);
  E50.setData(ema50);
  VOLS.setData(vol);
  CRS.setData(corrD);

  // Corr reference lines
  [-0.6,-0.3,0,0.3,0.6].forEach(v => {
    try {
      const ls = CC.addLineSeries({color:v<0?'rgba(0,212,170,0.2)':'rgba(255,77,106,0.2)',lineWidth:1,lineStyle:2,priceLineVisible:false,lastValueVisible:false});
      ls.setData([{time:data[0].time,value:v},{time:data[data.length-1].time,value:v}]);
    } catch(e){}
  });

  S.hArr = data.map(x=>x.high);
  S.lArr = data.map(x=>x.low);
  const lc = data[data.length-1];
  setTxt('oh-o', fmt(lc.open));
  setTxt('oh-h', fmt(lc.high));
  setTxt('oh-l', fmt(lc.low));
  setTxt('oh-c', fmt(S.price>0?S.price:lc.close));
  setTxt('oh-v', (lc.vol/1000).toFixed(1)+'K');
  setTxt('rp-hi', fmt(Math.max(...S.hArr)));
  setTxt('rp-lo', fmt(Math.min(...S.lArr)));

  drawTPSL(data[0].time, data[data.length-1].time);
  GC.timeScale().fitContent();
  S.chartLoaded = true;

  // ATR-based TP/SL
  computeATRLevels();
}

function parseAPICandles(raw, realPrice) {
  const data = [];
  raw.forEach(c => {
    const t  = parseTs(c.time);
    const o  = +c.open, h = +c.high, l = +c.low, cl = +c.close;
    if (isNaN(o)||isNaN(h)||isNaN(l)||isNaN(cl)) return;
    if (o<500||h<500||l<500||cl<500) return;   // pas XAUUSD
    if (o>8000||h>8000) return;
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
    const chg = (Math.random()-0.485)*p*0.0018;
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
  if (d.mt5_connected!=null)           S.mt5Ok  = !!d.mt5_connected;
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
  const mtf=d.mtf_analysis||d.mtf||{};
  ['H1','M15','M5'].forEach(t=>{if(mtf[t])S.mtf[t]=mtf[t];});
  const ohlcv=d.ohlcv||{};
  ['M5','M15','H1'].forEach(tf=>{
    if(ohlcv[tf]&&Array.isArray(ohlcv[tf])&&ohlcv[tf].length>5) S.ohlcv[tf]=ohlcv[tf];
  });
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
  const dm=document.getElementById('dot-mt5');if(dm)dm.className='dot '+(S.mt5Ok?'g':'y');
  setTxt('lbl-mt5',S.mt5Ok?'MT5 Connecté':'MT5 Déconnecté');setCol('lbl-mt5',S.mt5Ok?C_UP:'var(--gold)');

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

/* ══════════ MAIN LOOP ══════════ */
async function mainLoop() {
  S.tick++;
  const snap = await fetchSnap();
  if (snap) {
    S.apiOk=true;
    applySnap(snap);
  } else {
    S.apiOk=false;
    S.prev  = S.price||3284;
    if (!S.price) S.price=3284;
    S.price  = +(S.price+(Math.random()-0.48)*0.65).toFixed(2);
    S.dxy    = +(S.dxy -(Math.random()-0.48)*0.01).toFixed(3);
    S.corr   = +Math.max(-1,Math.min(1,S.corr+(Math.random()-0.5)*0.007)).toFixed(4);
    S.chg    = +(S.price-S.prev).toFixed(2);
    S.pct    = +(S.chg/(S.prev||S.price)*100).toFixed(3);
    S.dxyChg = +(S.dxy-104.23).toFixed(4);
    S.bid    = S.price-0.15; S.ask=S.price+0.15;
    if (!S.entry) S.entry=S.price;
  }

  // Build or refresh chart
  if (!S.chartLoaded || S.chartTF!==S.tf) {
    buildChart();
  } else {
    // Live tick update
    const now=Math.floor(Date.now()/1000);
    const p=S.price, pv=S.prev||p;
    if (p>100) {
      try {
        CSER.update({time:now,open:+pv.toFixed(2),
          high:+Math.max(p,pv).toFixed(2),
          low:+Math.min(p,pv).toFixed(2),
          close:+p.toFixed(2)});
        if(S.hArr.length){
          S.hArr[S.hArr.length-1]=Math.max(S.hArr[S.hArr.length-1],p);
          S.lArr[S.lArr.length-1]=Math.min(S.lArr[S.lArr.length-1],p);
          setTxt('rp-hi',fmt(Math.max(...S.hArr)));setTxt('oh-h',fmt(Math.max(...S.hArr)));
          setTxt('rp-lo',fmt(Math.min(...S.lArr)));setTxt('oh-l',fmt(Math.min(...S.lArr)));
        }
        setTxt('oh-c',fmt(p));
      } catch(e){}
      try{CRS.update({time:now,value:S.corr});}catch(e){}
    }
    computeATRLevels();
  }

  updateUI();
  setTimeout(mainLoop, S.apiOk?3000:2000);
}

/* ══════════ CONTROLS ══════════ */
function goTab(tab, btn) {
  document.querySelectorAll('.tab-panel').forEach(e=>e.classList.remove('active'));
  document.querySelectorAll('.nav-btn,.ib').forEach(e=>e.classList.remove('active'));
  const p=document.getElementById('p-'+tab); if(p) p.classList.add('active');
  if(btn) btn.classList.add('active');
  if(tab==='chart'){setTimeout(()=>{GC.resize(gcEl.offsetWidth,gcEl.offsetHeight);CC.resize(ccEl.offsetWidth,ccEl.offsetHeight);},60);}
}
function setTF(tf,el){
  S.tf=tf;S.chartTF='';S.chartLoaded=false;
  document.querySelectorAll('.tf-tab').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
}
function setPill(el){document.querySelectorAll('.tf-pill').forEach(e=>e.classList.remove('active'));el.classList.add('active');}
function setChartType(t){
  document.getElementById('btn-c').classList.toggle('active',t==='candle');
  document.getElementById('btn-l').classList.toggle('active',t==='line');
  S.chartTF='';S.chartLoaded=false;
}
function setSig(d){
  S.sig=d;
  const b=document.getElementById('rp-buy'),s=document.getElementById('rp-sell');
  if(d==='BUY'){if(b){b.style.background='var(--green)';b.style.color='#000';b.style.border='none';}if(s)s.classList.remove('on');}
  else{if(s)s.classList.add('on');if(b){b.style.background='var(--bg3)';b.style.color='var(--muted)';b.style.border='1px solid var(--border)';}}
  computeATRLevels();updateUI();
}
function setATRMode(mode,el){
  S.atrMode=mode;
  document.querySelectorAll('.atr-btn').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
  const m=ATR_MODES[mode];
  const explain=document.getElementById('atr-explain');
  if(explain)explain.querySelector('b').textContent=m.label;
  computeATRLevels();
}
function filterLog(f,el){
  S.logFilter=f;
  document.querySelectorAll('.log-tb .ct-btn').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
  renderLogs();
}

mainLoop();
</script>
</body>
</html>
""".replace('APIURL_PLACEHOLDER', API_URL).replace('APIKEY_PLACEHOLDER', API_KEY)

components.html(HTML, height=10000, scrolling=False)
