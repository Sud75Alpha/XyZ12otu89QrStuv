import streamlit as st
import streamlit.components.v1 as components
import requests, json
from datetime import datetime

st.set_page_config(
    page_title="GOLD/DXY PRO v15",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
.main .block-container{padding:0!important;max-width:100%!important;margin:0!important;}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stHeader"]{display:none!important;}
body{overflow:hidden!important;}
iframe{border:none!important;display:block!important;}
</style>
""", unsafe_allow_html=True)

API_URL = "https://en-ligne-5wi6.onrender.com"
API_KEY = "gold_dxy_secret_2024"

# Fetch snapshot server-side for initial data
def get_snapshot():
    try:
        r = requests.get(f"{API_URL}/api/snapshot", headers={"X-API-Key": API_KEY}, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

snap = get_snapshot()
snap_json = json.dumps(snap)

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#0b0f1a;--bg2:#111827;--bg3:#141c2e;
  --card:#0f1623;--border:rgba(255,255,255,0.07);
  --gold:#f5a623;--green:#00d4aa;--red:#ff4d6a;--blue:#4da6ff;
  --text:#e2e8f0;--muted:#4a5568;
}
html,body{width:100%;height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:'Space Grotesk',sans-serif;}
/* ── TOPBAR ── */
#topbar{
  height:52px;background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;padding:0 14px;gap:12px;flex-shrink:0;
}
.logo{font-weight:700;font-size:.95rem;color:var(--gold);white-space:nowrap;}
.logo span{font-size:.52rem;color:var(--muted);margin-left:4px;font-weight:400;}
.nav{display:flex;gap:2px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:3px;}
.nav-btn{padding:4px 11px;border-radius:6px;font-size:.62rem;font-weight:600;color:var(--muted);cursor:pointer;transition:all .15s;border:none;background:transparent;}
.nav-btn.active{background:rgba(245,166,35,.15);color:var(--gold);}
.nav-btn:hover:not(.active){color:var(--text);}
.tp-price-wrap{margin-left:auto;display:flex;align-items:center;gap:10px;}
.tp-price{font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;color:var(--gold);line-height:1;}
.tp-chg{font-size:.56rem;margin-top:1px;}
.badge{display:inline-flex;align-items:center;padding:3px 9px;border-radius:6px;font-size:.6rem;font-weight:700;letter-spacing:.04em;}
.badge.buy{background:rgba(0,212,170,.12);border:1px solid rgba(0,212,170,.3);color:var(--green);}
.badge.sell{background:rgba(255,77,106,.12);border:1px solid rgba(255,77,106,.3);color:var(--red);}
.badge.wait{background:rgba(100,116,139,.1);border:1px solid rgba(100,116,139,.2);color:var(--muted);}
.acct{display:flex;align-items:center;gap:7px;padding:4px 10px;background:var(--card);border:1px solid var(--border);border-radius:8px;}
.acct .b1{font-family:'JetBrains Mono',monospace;font-size:.68rem;font-weight:600;}
.acct .b2{font-size:.48rem;color:var(--muted);}
.avatar{width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#ff9f43);display:flex;align-items:center;justify-content:center;font-size:.52rem;font-weight:700;color:#000;}
/* ── LAYOUT ── */
#layout{display:flex;height:calc(100vh - 52px - 28px);overflow:hidden;}
/* ── ICON SIDEBAR ── */
#icon-sb{width:60px;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;align-items:center;padding:10px 0;gap:3px;}
.i-btn{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--muted);transition:all .15s;border:none;background:transparent;position:relative;}
.i-btn:hover{background:rgba(255,255,255,.05);color:var(--text);}
.i-btn.active{background:rgba(245,166,35,.12);color:var(--gold);}
.i-btn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.15}}
.dot-live{width:5px;height:5px;background:var(--green);border-radius:50%;position:absolute;top:5px;right:5px;box-shadow:0 0 5px var(--green);animation:pulse 1.6s infinite;}
/* ── INFO SIDEBAR ── */
#info-sb{width:250px;background:var(--bg2);border-right:1px solid var(--border);overflow-y:auto;display:flex;flex-direction:column;}
#info-sb::-webkit-scrollbar{width:2px;}
#info-sb::-webkit-scrollbar-thumb{background:var(--border);}
.sb-sec{padding:10px 11px 0;}
.lbl{font-size:.46rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:5px;}
.tf-tabs{display:flex;gap:2px;background:var(--bg3);border:1px solid var(--border);border-radius:7px;padding:3px;}
.tf-tab{flex:1;text-align:center;padding:3px 0;border-radius:5px;font-size:.6rem;font-weight:600;color:var(--muted);cursor:pointer;border:none;background:transparent;transition:all .15s;}
.tf-tab.active{background:rgba(245,166,35,.2);color:var(--gold);}
.card{background:var(--card);border:1px solid var(--border);border-radius:9px;padding:9px 11px;margin:6px 0;}
.card.gold-border{border-color:rgba(245,166,35,.2);}
.card.green-border{border-color:rgba(0,212,170,.15);}
.big-val{font-family:'JetBrains Mono',monospace;font-size:1.4rem;font-weight:700;color:var(--gold);line-height:1.1;margin:2px 0;}
.big-val.blue{color:var(--blue);}
.chg{font-size:.58rem;font-weight:600;}
.chg.up{color:var(--green);}
.chg.dn{color:var(--red);}
.ba{font-size:.5rem;color:var(--muted);margin-top:3px;}
.ba b{color:#9ca3af;}
.corr-bar-wrap{height:4px;border-radius:2px;background:#1e2d42;margin:5px 0 3px;overflow:hidden;}
.corr-bar-fill{height:100%;border-radius:2px;transition:width .5s,background .5s;}
.sig-badge{display:inline-flex;padding:3px 10px;border-radius:6px;font-size:.64rem;font-weight:700;letter-spacing:.04em;margin-bottom:6px;}
.sig-badge.buy{background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:var(--green);}
.sig-badge.sell{background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:var(--red);}
.sig-badge.wait{background:rgba(100,116,139,.1);border:1px solid rgba(100,116,139,.25);color:var(--muted);}
.row{display:flex;justify-content:space-between;align-items:center;font-size:.57rem;line-height:1.9;}
.row .k{color:var(--muted);}
.row .v{font-weight:600;font-family:'JetBrains Mono',monospace;}
.sep{border:none;border-top:1px solid var(--border);margin:7px 11px;}
.mtf-row{display:flex;gap:4px;margin-bottom:5px;}
.mtf-cell{flex:1;background:var(--card);border:1px solid var(--border);border-radius:7px;padding:6px;text-align:center;}
.mtf-cell .tf-lbl{font-size:.48rem;font-weight:700;color:var(--muted);margin-bottom:3px;}
.mtf-cell .tf-sig{font-size:.58rem;font-weight:700;}
.tf-sig.buy{color:var(--green);}
.tf-sig.sell{color:var(--red);}
.tf-sig.wait{color:var(--muted);}
.stat-row{display:flex;gap:4px;margin-bottom:5px;}
.stat-box{flex:1;background:var(--card);border:1px solid var(--border);border-radius:7px;padding:6px 8px;}
.stat-box .sk{font-size:.46rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px;}
.stat-box .sv{font-size:.82rem;font-weight:700;font-family:'JetBrains Mono',monospace;}
.conn-row{display:flex;align-items:center;gap:5px;font-size:.55rem;margin-bottom:4px;}
.dot{width:5px;height:5px;border-radius:50%;flex-shrink:0;}
.dot.g{background:var(--green);box-shadow:0 0 4px var(--green);}
.dot.y{background:var(--gold);}
/* ── CHART ZONE ── */
#chart-zone{flex:1;display:flex;flex-direction:column;overflow:hidden;}
#chart-toolbar{height:40px;background:var(--bg2);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 12px;gap:10px;flex-shrink:0;}
.ct-btn{padding:3px 8px;border-radius:5px;font-size:.6rem;font-weight:600;color:var(--muted);cursor:pointer;border:1px solid transparent;background:transparent;transition:all .15s;}
.ct-btn.active{background:rgba(0,212,170,.12);border-color:rgba(0,212,170,.3);color:var(--green);}
.ct-sep{width:1px;height:15px;background:var(--border);}
.tf-pill{padding:3px 7px;border-radius:5px;font-size:.58rem;font-weight:600;color:var(--muted);cursor:pointer;border:none;background:transparent;transition:all .15s;}
.tf-pill.active{background:rgba(0,212,170,.12);color:var(--green);}
.tf-pill:hover:not(.active){color:var(--text);}
.sym-lbl{font-weight:700;font-size:.75rem;}
.dot-g2{width:6px;height:6px;background:var(--green);border-radius:50%;display:inline-block;margin-right:4px;box-shadow:0 0 5px var(--green);animation:pulse 1.6s infinite;vertical-align:middle;}
#chart-body{flex:1;display:flex;overflow:hidden;}
#chart-wrap{flex:1;display:flex;flex-direction:column;padding:7px 7px 0;gap:5px;overflow:hidden;}
#gold-chart{flex:1;border-radius:9px;overflow:hidden;border:1px solid var(--border);min-height:0;}
#corr-chart{height:90px;flex-shrink:0;border-radius:9px;overflow:hidden;border:1px solid var(--border);}
/* ── RIGHT PANEL ── */
#right-panel{width:280px;border-left:1px solid var(--border);background:var(--bg2);overflow-y:auto;display:flex;flex-direction:column;}
#right-panel::-webkit-scrollbar{width:2px;}
#right-panel::-webkit-scrollbar-thumb{background:var(--border);}
.rp-sec{padding:11px 12px;}
.order-btns{display:flex;gap:5px;margin-bottom:9px;}
.o-btn{flex:1;padding:8px;border-radius:7px;font-size:.7rem;font-weight:700;cursor:pointer;border:none;letter-spacing:.04em;font-family:'Space Grotesk',sans-serif;transition:all .15s;}
.o-btn.buy{background:var(--green);color:#000;}
.o-btn.buy:hover{background:#00bfa0;}
.o-btn.sell{background:var(--bg3);border:1px solid var(--border);color:var(--muted);}
.o-btn.sell.on{background:var(--red);color:#fff;border-color:var(--red);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px;}
.mini-card{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:7px 9px;}
.mini-card.tp{border-color:rgba(0,212,170,.2);}
.mini-card.sl{border-color:rgba(255,77,106,.2);}
.mini-card.en{border-color:rgba(77,166,255,.2);}
.mini-card .mk{font-size:.46rem;color:var(--muted);font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:2px;}
.mini-card .mv{font-family:'JetBrains Mono',monospace;font-size:.8rem;font-weight:700;}
.mini-card .ms{font-size:.48rem;color:var(--muted);margin-top:2px;}
.rbar-wrap{margin-bottom:8px;}
.rbar-row{display:flex;justify-content:space-between;font-size:.55rem;margin-bottom:3px;}
.rbar{height:4px;border-radius:2px;background:#1e2d42;overflow:hidden;}
.rbar-fill{height:100%;border-radius:2px;transition:width .5s;}
.wr-bar{height:4px;border-radius:2px;background:#1e2d42;overflow:hidden;margin:4px 0 2px;}
.wr-fill{height:100%;border-radius:2px;background:var(--green);}
.risk-dots{display:flex;gap:3px;margin:4px 0 3px;}
.rdot{flex:1;height:4px;border-radius:2px;background:#1e2d42;}
.rdot.g{background:var(--green);}
.rdot.y{background:var(--gold);}
.rdot.r{background:var(--red);}
/* ── TABS CONTENT ── */
.tab-content{display:none;}
.tab-content.active{display:flex;flex:1;overflow:hidden;}
/* ── TICKER ── */
#ticker{height:28px;border-top:1px solid var(--border);background:var(--bg2);display:flex;align-items:center;padding:0 12px;gap:16px;overflow:hidden;flex-shrink:0;}
.ti{display:flex;gap:6px;align-items:center;white-space:nowrap;}
.ts{font-size:.5rem;font-weight:700;color:var(--muted);}
.tv{font-family:'JetBrains Mono',monospace;font-size:.56rem;font-weight:600;}
.tc{font-size:.5rem;}
.tc.up{color:var(--green);}
.tc.dn{color:var(--red);}
/* LOGS */
#logs-wrap{flex:1;overflow-y:auto;padding:10px;font-family:'JetBrains Mono',monospace;font-size:.6rem;line-height:1.9;background:var(--bg);}
#logs-wrap::-webkit-scrollbar{width:3px;}
#logs-wrap::-webkit-scrollbar-thumb{background:var(--border);}
.log-line{padding:1px 0;border-bottom:1px solid rgba(255,255,255,.02);}
.log-info{color:var(--muted);}
.log-signal{color:var(--green);}
.log-warning{color:var(--gold);}
.log-error{color:var(--red);}
/* HISTORIQUE */
#hist-wrap{flex:1;overflow-y:auto;padding:10px;background:var(--bg);}
.hist-table{width:100%;border-collapse:collapse;font-size:.58rem;}
.hist-table th{padding:6px 8px;text-align:left;color:var(--muted);font-size:.48rem;letter-spacing:.08em;text-transform:uppercase;border-bottom:1px solid var(--border);}
.hist-table td{padding:5px 8px;border-bottom:1px solid rgba(255,255,255,.03);font-family:'JetBrains Mono',monospace;}
.hist-table tr:hover td{background:rgba(255,255,255,.02);}
/* MULTI-TF tab */
#multitf-wrap{flex:1;padding:14px;background:var(--bg);display:flex;flex-direction:column;gap:10px;overflow-y:auto;}
.mtf-big{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;flex:1;}
.mtf-big .tf-name{font-size:1rem;font-weight:700;color:var(--text);margin-bottom:6px;}
</style>
</head>
<body>

<!-- TOPBAR -->
<div id="topbar">
  <div class="logo">⚡ GOLD/DXY PRO<span>v15</span></div>
  <div class="nav">
    <button class="nav-btn active" onclick="switchTab('chart',this)">Chart</button>
    <button class="nav-btn" onclick="switchTab('signal',this)">Signal</button>
    <button class="nav-btn" onclick="switchTab('multitf',this)">Multi-TF</button>
    <button class="nav-btn" onclick="switchTab('logs',this)">Logs</button>
    <button class="nav-btn" onclick="switchTab('historique',this)">Historique</button>
  </div>
  <div class="tp-price-wrap">
    <div>
      <div class="tp-price" id="tp-price">—</div>
      <div class="tp-chg" id="tp-chg">—</div>
    </div>
    <div style="width:1px;height:24px;background:var(--border);"></div>
    <div class="badge wait" id="tp-badge">WAIT</div>
    <div style="font-size:.54rem;color:var(--muted);">Conf <b id="tp-conf" style="color:var(--text);">0%</b></div>
    <div class="acct">
      <div><div class="b1">XAUUSDm</div><div class="b2" id="acct-status">Connexion...</div></div>
      <div class="avatar">GP</div>
    </div>
  </div>
</div>

<!-- MAIN LAYOUT -->
<div id="layout">

  <!-- ICON SIDEBAR -->
  <div id="icon-sb">
    <button class="i-btn active" onclick="switchTab('chart',null)">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      <div class="dot-live"></div>
    </button>
    <button class="i-btn" onclick="switchTab('signal',null)"><svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></button>
    <button class="i-btn" onclick="switchTab('historique',null)"><svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><polyline points="18 9 12 15 9 12 3 18"/></svg></button>
    <button class="i-btn" onclick="switchTab('multitf',null)"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg></button>
    <button class="i-btn" onclick="switchTab('logs',null)"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></button>
  </div>

  <!-- INFO SIDEBAR (toujours visible) -->
  <div id="info-sb">
    <div class="sb-sec">
      <div class="lbl">Timeframe</div>
      <div class="tf-tabs">
        <button class="tf-tab" onclick="setTF('M5',this)">M5</button>
        <button class="tf-tab active" onclick="setTF('M15',this)">M15</button>
        <button class="tf-tab" onclick="setTF('H1',this)">H1</button>
      </div>
    </div>
    <div class="sb-sec">
      <div class="card gold-border">
        <div class="lbl">XAUUSD — OR</div>
        <div class="big-val" id="sb-gold">—</div>
        <div class="chg" id="sb-gold-chg">—</div>
        <div class="ba">BID <b id="sb-bid">—</b> | ASK <b id="sb-ask">—</b></div>
      </div>
      <div class="card">
        <div class="lbl">DXY</div>
        <div class="big-val blue" id="sb-dxy">—</div>
        <div class="chg" id="sb-dxy-chg">—</div>
      </div>
    </div>
    <div class="sep"></div>
    <div class="sb-sec">
      <div class="lbl">Corrélation Gold/DXY</div>
      <div class="card">
        <div style="font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:700;" id="sb-corr">—</div>
        <div class="corr-bar-wrap"><div class="corr-bar-fill" id="sb-corr-bar" style="width:0%"></div></div>
        <div style="font-size:.52rem;font-weight:600;" id="sb-corr-txt">En attente...</div>
      </div>
    </div>
    <div class="sb-sec">
      <div class="lbl">Signal Actif</div>
      <div class="card gold-border">
        <span class="sig-badge wait" id="sb-sig-badge">WAIT</span>
        <div class="row"><span class="k">Confiance</span><span class="v" id="sb-conf">—</span></div>
        <div class="row"><span class="k">Corrélation</span><span class="v" id="sb-corr2">—</span></div>
        <div class="row"><span class="k">Entrée</span><span class="v" id="sb-entry" style="color:var(--gold)">—</span></div>
        <div class="row"><span class="k">TP</span><span class="v" id="sb-tp" style="color:var(--green)">—</span></div>
        <div class="row"><span class="k">SL</span><span class="v" id="sb-sl" style="color:var(--red)">—</span></div>
        <div class="row"><span class="k">R/R</span><span class="v" id="sb-rr">—</span></div>
        <div class="row"><span class="k">Lot</span><span class="v" id="sb-lot">—</span></div>
        <div class="row"><span class="k">Pipeline</span><span class="v" id="sb-pipe" style="color:var(--gold)">IDLE</span></div>
      </div>
    </div>
    <div class="sep"></div>
    <div class="sb-sec">
      <div class="lbl">Multi-TF</div>
      <div class="mtf-row">
        <div class="mtf-cell"><div class="tf-lbl">H1</div><div class="tf-sig wait" id="mtf-h1">—</div></div>
        <div class="mtf-cell"><div class="tf-lbl">M15</div><div class="tf-sig wait" id="mtf-m15">—</div></div>
        <div class="mtf-cell"><div class="tf-lbl">M5</div><div class="tf-sig wait" id="mtf-m5">—</div></div>
      </div>
    </div>
    <div class="sep"></div>
    <div class="sb-sec">
      <div class="lbl">Connexion</div>
      <div class="conn-row"><div class="dot y" id="dot-api"></div><span id="lbl-api" style="color:var(--gold)">Connexion...</span></div>
      <div class="conn-row"><div class="dot y" id="dot-mt5"></div><span id="lbl-mt5" style="color:var(--gold)">MT5...</span></div>
    </div>
    <div class="sb-sec" style="padding-bottom:12px;">
      <div class="lbl">Statistiques</div>
      <div class="stat-row">
        <div class="stat-box"><div class="sk">Winrate</div><div class="sv" id="sb-wr" style="color:var(--green)">—</div></div>
        <div class="stat-box"><div class="sk">W / L</div><div class="sv" id="sb-wl">—</div></div>
      </div>
      <div style="font-size:.44rem;color:#1e2d42;text-align:center;margin-top:6px;line-height:2;">
        Tick #<span id="sb-tick">0</span> · <span id="sb-time">--:--:--</span>
      </div>
    </div>
  </div>

  <!-- TAB: CHART -->
  <div id="tab-chart" class="tab-content active">
    <div id="chart-zone">
      <div id="chart-toolbar">
        <span class="sym-lbl"><span class="dot-g2"></span>XAUUSD · XAUUSDm</span>
        <div class="ct-sep"></div>
        <button class="ct-btn active" id="btn-candle" onclick="setChartType('candle')">Candle</button>
        <button class="ct-btn" id="btn-line" onclick="setChartType('line')">Line</button>
        <div class="ct-sep"></div>
        <button class="tf-pill" onclick="setPill(this)">1m</button>
        <button class="tf-pill" onclick="setPill(this)">5m</button>
        <button class="tf-pill" onclick="setPill(this)">10m</button>
        <button class="tf-pill active" onclick="setPill(this)">15m</button>
        <button class="tf-pill" onclick="setPill(this)">1h</button>
        <button class="tf-pill" onclick="setPill(this)">5h</button>
        <button class="tf-pill" onclick="setPill(this)">All</button>
        <div class="ct-sep"></div>
        <span style="font-size:.54rem;color:var(--muted);">EMA20 <b style="color:var(--gold)">●</b> EMA50 <b style="color:rgba(255,255,255,.2)">●</b> RSI</span>
        <span style="margin-left:auto;font-size:.54rem;color:var(--muted)" id="clock">--:--:--</span>
      </div>
      <div id="chart-body">
        <div id="chart-wrap">
          <div id="gold-chart"></div>
          <div id="corr-chart"></div>
        </div>
        <!-- RIGHT PANEL -->
        <div id="right-panel">
          <div class="rp-sec">
            <div class="lbl">Ordre</div>
            <div class="order-btns">
              <button class="o-btn buy" id="rp-buy" onclick="setSig('BUY')">Buy</button>
              <button class="o-btn sell" id="rp-sell" onclick="setSig('SELL')">Sell</button>
            </div>
            <div class="grid2">
              <div class="mini-card tp"><div class="mk">Take Profit</div><div class="mv" id="rp-tp" style="color:var(--green)">—</div><div class="ms" id="rp-tp-pts">—</div></div>
              <div class="mini-card sl"><div class="mk">Stop Loss</div><div class="mv" id="rp-sl" style="color:var(--red)">—</div><div class="ms" id="rp-sl-pts">—</div></div>
              <div class="mini-card en"><div class="mk">Entrée</div><div class="mv" id="rp-entry" style="color:var(--blue)">—</div></div>
              <div class="mini-card"><div class="mk">Lot / R:R</div><div class="mv" id="rp-rr" style="color:var(--text)">—</div></div>
            </div>
            <div class="rbar-wrap">
              <div class="rbar-row"><span style="color:var(--muted)">Risk Exposure</span><span id="rp-risk-lbl" style="color:var(--gold);font-weight:600">—</span></div>
              <div class="rbar"><div class="rbar-fill" id="rp-risk-bar" style="width:0%;background:var(--gold)"></div></div>
            </div>
          </div>
          <div class="sep" style="margin:0"></div>
          <div class="rp-sec">
            <div class="lbl">Performance</div>
            <div class="grid2">
              <div class="mini-card"><div class="mk">Winrate</div><div class="mv" id="rp-wr" style="color:var(--green)">—</div><div class="wr-bar"><div class="wr-fill" id="rp-wr-bar" style="width:0%"></div></div></div>
              <div class="mini-card"><div class="mk">Trades</div><div class="mv" id="rp-trades">—</div><div style="font-size:.48rem;color:var(--muted);margin-top:2px" id="rp-wl">—</div></div>
              <div class="mini-card"><div class="mk">Day High</div><div class="mv" id="rp-high" style="color:var(--green)">—</div></div>
              <div class="mini-card"><div class="mk">Day Low</div><div class="mv" id="rp-low" style="color:var(--red)">—</div></div>
            </div>
            <div class="mini-card" style="margin-bottom:6px">
              <div class="mk">Risk Level</div>
              <div class="risk-dots" id="risk-dots">
                <div class="rdot"></div><div class="rdot"></div><div class="rdot"></div><div class="rdot"></div><div class="rdot"></div>
              </div>
              <div style="font-size:.5rem;font-weight:600" id="risk-lbl">—</div>
            </div>
            <div class="mini-card">
              <div class="lbl" style="margin-bottom:5px">OHLCV</div>
              <div class="row"><span class="k">Open</span><span class="v" id="ohlc-o">—</span></div>
              <div class="row"><span class="k">High</span><span class="v" id="ohlc-h" style="color:var(--green)">—</span></div>
              <div class="row"><span class="k">Low</span><span class="v" id="ohlc-l" style="color:var(--red)">—</span></div>
              <div class="row"><span class="k">Close</span><span class="v" id="ohlc-c" style="color:var(--gold)">—</span></div>
              <div class="row"><span class="k">Volume</span><span class="v" id="ohlc-v" style="color:var(--blue)">—</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB: SIGNAL -->
  <div id="tab-signal" class="tab-content" style="flex-direction:column;padding:14px;background:var(--bg);overflow-y:auto;gap:10px;">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
      <div class="card gold-border">
        <div class="lbl" style="margin-bottom:8px">Signal Principal</div>
        <span class="sig-badge wait" id="sig-badge2">WAIT</span>
        <div class="row" style="margin-top:4px"><span class="k">Confiance</span><span class="v" id="sig-conf2">—</span></div>
        <div class="row"><span class="k">Corrélation</span><span class="v" id="sig-corr2">—</span></div>
        <div class="row"><span class="k">Pipeline</span><span class="v" id="sig-pipe2" style="color:var(--gold)">IDLE</span></div>
      </div>
      <div class="card">
        <div class="lbl" style="margin-bottom:8px">Niveaux</div>
        <div class="row"><span class="k">Entrée</span><span class="v" id="sig-entry2" style="color:var(--gold)">—</span></div>
        <div class="row"><span class="k">Take Profit</span><span class="v" id="sig-tp2" style="color:var(--green)">—</span></div>
        <div class="row"><span class="k">Stop Loss</span><span class="v" id="sig-sl2" style="color:var(--red)">—</span></div>
        <div class="row"><span class="k">R/R</span><span class="v" id="sig-rr2">—</span></div>
        <div class="row"><span class="k">Lot</span><span class="v" id="sig-lot2">—</span></div>
      </div>
      <div class="card">
        <div class="lbl" style="margin-bottom:8px">Corrélation</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:1.4rem;font-weight:700;margin-bottom:6px" id="sig-corr-big">—</div>
        <div class="corr-bar-wrap"><div class="corr-bar-fill" id="sig-corr-bar2" style="width:0%"></div></div>
        <div style="font-size:.55rem;font-weight:600;margin-top:3px" id="sig-corr-txt2">—</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;flex:1">
      <div class="card" style="height:fit-content">
        <div class="lbl" style="margin-bottom:8px">Support / Résistance</div>
        <div class="row"><span class="k">Support</span><span class="v" id="sig-sup" style="color:var(--green)">—</span></div>
        <div class="row"><span class="k">Résistance</span><span class="v" id="sig-res" style="color:var(--red)">—</span></div>
        <div class="row"><span class="k">ATR</span><span class="v" id="sig-atr" style="color:var(--gold)">—</span></div>
        <div class="row"><span class="k">FVG Bull</span><span class="v" id="sig-fvg-b" style="color:var(--green)">—</span></div>
        <div class="row"><span class="k">FVG Bear</span><span class="v" id="sig-fvg-s" style="color:var(--red)">—</span></div>
      </div>
      <div class="card">
        <div class="lbl" style="margin-bottom:8px">Prix Live</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;color:var(--gold)" id="sig-price-big">—</div>
        <div style="font-size:.6rem;margin-top:4px" id="sig-price-chg">—</div>
        <div style="margin-top:10px" class="row"><span class="k">BID</span><span class="v" id="sig-bid">—</span></div>
        <div class="row"><span class="k">ASK</span><span class="v" id="sig-ask">—</span></div>
        <div class="row"><span class="k">DXY</span><span class="v" id="sig-dxy" style="color:var(--blue)">—</span></div>
      </div>
    </div>
  </div>

  <!-- TAB: MULTI-TF -->
  <div id="tab-multitf" class="tab-content" style="flex-direction:column;padding:14px;background:var(--bg);overflow-y:auto;gap:10px;">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
      <div class="card" id="mtf-card-h1">
        <div style="font-size:1.1rem;font-weight:700;color:var(--text);margin-bottom:8px">H1</div>
        <span class="sig-badge wait" id="mtf-big-h1">WAIT</span>
        <div class="row" style="margin-top:6px"><span class="k">Corrélation</span><span class="v" id="mtf-corr-h1">—</span></div>
        <div class="row"><span class="k">Tendance</span><span class="v" id="mtf-trend-h1">—</span></div>
      </div>
      <div class="card" id="mtf-card-m15">
        <div style="font-size:1.1rem;font-weight:700;color:var(--text);margin-bottom:8px">M15</div>
        <span class="sig-badge wait" id="mtf-big-m15">WAIT</span>
        <div class="row" style="margin-top:6px"><span class="k">Corrélation</span><span class="v" id="mtf-corr-m15">—</span></div>
        <div class="row"><span class="k">Tendance</span><span class="v" id="mtf-trend-m15">—</span></div>
      </div>
      <div class="card" id="mtf-card-m5">
        <div style="font-size:1.1rem;font-weight:700;color:var(--text);margin-bottom:8px">M5</div>
        <span class="sig-badge wait" id="mtf-big-m5">WAIT</span>
        <div class="row" style="margin-top:6px"><span class="k">Corrélation</span><span class="v" id="mtf-corr-m5">—</span></div>
        <div class="row"><span class="k">Tendance</span><span class="v" id="mtf-trend-m5">—</span></div>
      </div>
    </div>
    <div class="card">
      <div class="lbl" style="margin-bottom:8px">Consensus</div>
      <div id="consensus-txt" style="font-size:.8rem;font-weight:700;text-align:center;padding:10px;">—</div>
      <div id="consensus-sub" style="font-size:.58rem;color:var(--muted);text-align:center">H1: — · M15: — · M5: —</div>
    </div>
  </div>

  <!-- TAB: LOGS -->
  <div id="tab-logs" class="tab-content" style="flex-direction:column;background:var(--bg);">
    <div style="padding:8px 10px;border-bottom:1px solid var(--border);display:flex;gap:6px;background:var(--bg2);flex-shrink:0">
      <button class="ct-btn active" onclick="filterLogs('ALL',this)">ALL</button>
      <button class="ct-btn" onclick="filterLogs('SIGNAL',this)">SIGNAL</button>
      <button class="ct-btn" onclick="filterLogs('WARNING',this)">WARNING</button>
      <button class="ct-btn" onclick="filterLogs('ERROR',this)">ERROR</button>
    </div>
    <div id="logs-wrap"><div style="color:var(--muted);padding:20px">Chargement logs...</div></div>
  </div>

  <!-- TAB: HISTORIQUE -->
  <div id="tab-historique" class="tab-content" style="flex-direction:column;background:var(--bg);">
    <div style="padding:8px 10px;border-bottom:1px solid var(--border);background:var(--bg2);display:flex;gap:12px;align-items:center;flex-shrink:0">
      <div class="row" style="gap:20px">
        <span class="ts">Total: <b id="hist-total" style="color:var(--text)">—</b></span>
        <span class="ts">Winrate: <b id="hist-wr" style="color:var(--green)">—</b></span>
        <span class="ts">Wins: <b id="hist-w" style="color:var(--green)">—</b></span>
        <span class="ts">Losses: <b id="hist-l" style="color:var(--red)">—</b></span>
      </div>
    </div>
    <div id="hist-wrap">
      <table class="hist-table">
        <thead><tr>
          <th>Heure</th><th>Direction</th><th>TF</th><th>Entrée</th><th>TP</th><th>SL</th><th>R/R</th><th>Lot</th><th>Résultat</th>
        </tr></thead>
        <tbody id="hist-body"><tr><td colspan="9" style="color:var(--muted);text-align:center;padding:20px">Aucun signal enregistré</td></tr></tbody>
      </table>
    </div>
  </div>

</div>

<!-- TICKER -->
<div id="ticker">
  <div class="ti"><span class="ts">XAUUSD</span><span class="tv" id="tick-gold">—</span><span class="tc up" id="tick-gold-chg">—</span></div>
  <div class="ti"><span class="ts">DXY</span><span class="tv" id="tick-dxy">—</span><span class="tc" id="tick-dxy-chg">—</span></div>
  <div class="ti"><span class="ts">CORR</span><span class="tv" id="tick-corr">—</span><span class="tc" id="tick-corr-lbl">—</span></div>
  <div class="ti"><span class="ts">SIGNAL</span><span class="tv" id="tick-sig" style="color:var(--muted)">—</span><span class="tc" id="tick-conf-t">—</span></div>
  <div class="ti"><span class="ts">PIPELINE</span><span class="tv" id="tick-pipe" style="color:var(--gold)">IDLE</span></div>
  <div class="ti" style="margin-left:auto"><span class="ts">API</span><span class="tv" id="tick-api" style="color:var(--muted)">—</span></div>
  <div class="ti"><span class="ts">TICK#</span><span class="tv" id="tick-n">0</span></div>
</div>

<script>
/* ══════════════════════════════════════════
   CONFIG & STATE
══════════════════════════════════════════ */
const API_URL = '__API_URL__';
const API_KEY = '__API_KEY__';
const INIT_SNAP = __SNAP_JSON__;

const S = {
  price:0, prevPrice:0, dxy:104.23, corr:-0.65,
  goldChg:0, goldPct:0, dxyChg:0,
  bid:0, ask:0,
  signal:'WAIT', conf:0, tp:0, sl:0, entry:0, lot:0, rr:0,
  pipe:'IDLE', wins:0, losses:0, winrate:0,
  apiOk:false, mt5Ok:false, tick:0,
  tf:'M15', logFilter:'ALL',
  ohlcv:{M5:[],M15:[],H1:[]},
  mtf:{H1:{},M15:{},M5:{}},
  zones:{}, logs:[], signals:[],
  highArr:[], lowArr:[],
  chartLoaded:false, currentChartTF:'',
};

/* ══════════════════════════════════════════
   CHARTS INIT
══════════════════════════════════════════ */
const goldEl = document.getElementById('gold-chart');
const corrEl = document.getElementById('corr-chart');

const GC = LightweightCharts.createChart(goldEl, {
  layout:{background:{color:'#0f1623'},textColor:'#4a5568'},
  grid:{vertLines:{color:'rgba(255,255,255,0.03)'},horzLines:{color:'rgba(255,255,255,0.03)'}},
  crosshair:{mode:LightweightCharts.CrosshairMode.Normal},
  rightPriceScale:{borderColor:'rgba(255,255,255,0.06)'},
  timeScale:{borderColor:'rgba(255,255,255,0.06)',timeVisible:true,secondsVisible:false},
  handleScroll:{mouseWheel:true,pressedMouseMove:true},
  handleScale:{mouseWheel:true,pinch:true},
});

let CS = GC.addCandlestickSeries({
  upColor:'#00d4aa',downColor:'#ff4d6a',
  borderUpColor:'#00d4aa',borderDownColor:'#ff4d6a',
  wickUpColor:'#00d4aa',wickDownColor:'#ff4d6a',
});
const E20 = GC.addLineSeries({color:'#f5a623',lineWidth:1.5,lineStyle:1,priceLineVisible:false,title:'EMA20'});
const E50 = GC.addLineSeries({color:'rgba(255,255,255,0.18)',lineWidth:1,priceLineVisible:false,title:'EMA50'});
const VOL = GC.addHistogramSeries({
  color:'rgba(0,212,170,0.3)',priceFormat:{type:'volume'},
  priceScaleId:'vol',scaleMargins:{top:0.82,bottom:0}
});
const TPL = GC.addLineSeries({color:'rgba(0,212,170,0.6)',lineWidth:1,lineStyle:2,priceLineVisible:false});
const SLL = GC.addLineSeries({color:'rgba(255,77,106,0.6)',lineWidth:1,lineStyle:2,priceLineVisible:false});

const CC = LightweightCharts.createChart(corrEl, {
  layout:{background:{color:'#0f1623'},textColor:'#4a5568'},
  grid:{vertLines:{color:'rgba(255,255,255,0.02)'},horzLines:{color:'rgba(255,255,255,0.02)'}},
  rightPriceScale:{borderColor:'rgba(255,255,255,0.06)'},
  timeScale:{borderColor:'rgba(255,255,255,0.06)',visible:false},
  crosshair:{mode:LightweightCharts.CrosshairMode.Normal},
});
const CORRS = CC.addLineSeries({
  color:'#f5a623',lineWidth:1.5,priceLineVisible:false,
  autoscaleInfoProvider:() => {return {priceRange:{minValue:-1,maxValue:1}};}
});

// Responsive resize
const ro = new ResizeObserver(() => {
  GC.resize(goldEl.offsetWidth, goldEl.offsetHeight);
  CC.resize(corrEl.offsetWidth, corrEl.offsetHeight);
});
ro.observe(goldEl); ro.observe(corrEl);

/* ══════════════════════════════════════════
   CHART TYPE SWITCH
══════════════════════════════════════════ */
let lineCS = null;
function setChartType(type) {
  document.getElementById('btn-candle').classList.toggle('active', type==='candle');
  document.getElementById('btn-line').classList.toggle('active', type==='line');
  // Rebuild chart with same data in new type
  S.currentChartTF = '';
  buildChart();
}

/* ══════════════════════════════════════════
   BUILD CHART FROM OHLCV
══════════════════════════════════════════ */
const tfMins = {M5:5,M15:15,H1:60};

function buildChart() {
  const tf = S.tf;
  const candles = S.ohlcv[tf];
  const base = S.price > 100 ? S.price : 3284;

  if (candles && candles.length > 10) {
    loadRealCandles(candles, tf);
  } else {
    loadSimCandles(200, tfMins[tf], base);
  }
  S.currentChartTF = tf;
  buildCorrChart(200, tfMins[tf]);
  updateTPSLLines();
}

function loadRealCandles(candles, tf) {
  const data=[],em20=[],em50=[],vol=[];
  let e20 = +candles[0].close, e50 = +candles[0].close;
  candles.forEach((c,i) => {
    const t = Math.floor(new Date(c.time).getTime()/1000) || +c.time;
    const o=+c.open, h=+c.high, l=+c.low, cl=+c.close;
    data.push({time:t,open:o,high:h,low:l,close:cl});
    e20 = e20*19/20 + cl/20;
    e50 = e50*49/50 + cl/50;
    if(i>=20) em20.push({time:t,value:+e20.toFixed(2)});
    if(i>=50) em50.push({time:t,value:+e50.toFixed(2)});
    vol.push({time:t,value:+(c.volume||c.tick_volume||500),
      color:cl>=o?'rgba(0,212,170,0.35)':'rgba(255,77,106,0.35)'});
  });
  setChartData(data, em20, em50, vol);
}

function loadSimCandles(n, mins, base) {
  const data=[],em20=[],em50=[],vol=[];
  let p=base, e20=base, e50=base;
  const now = Math.floor(Date.now()/1000);
  for(let i=0;i<n;i++) {
    const t = now - (n-1-i)*mins*60;
    const chg = (Math.random()-0.48)*base*0.0022;
    const o=p, cl=p+chg;
    const h=Math.max(o,cl)+(Math.random()*base*0.0007);
    const l=Math.min(o,cl)-(Math.random()*base*0.0007);
    data.push({time:t,open:+o.toFixed(2),high:+h.toFixed(2),low:+Math.max(l,0.01).toFixed(2),close:+cl.toFixed(2)});
    e20=e20*19/20+cl/20; e50=e50*49/50+cl/50;
    if(i>=20) em20.push({time:t,value:+e20.toFixed(2)});
    if(i>=50) em50.push({time:t,value:+e50.toFixed(2)});
    vol.push({time:t,value:Math.floor(Math.random()*10000+500),
      color:cl>=o?'rgba(0,212,170,0.35)':'rgba(255,77,106,0.35)'});
    p=cl;
  }
  // Anchor last close to real price
  if(S.price>100) {
    const off = S.price - data[data.length-1].close;
    data.forEach(d=>{d.open+=off;d.high+=off;d.low+=off;d.close+=off;});
    em20.forEach(d=>d.value+=off); em50.forEach(d=>d.value+=off);
  }
  setChartData(data, em20, em50, vol);
}

function setChartData(data, em20, em50, vol) {
  CS.setData(data); E20.setData(em20); E50.setData(em50); VOL.setData(vol);
  S.highArr = data.map(x=>x.high);
  S.lowArr  = data.map(x=>x.low);
  const lc = data[data.length-1];
  setText('ohlc-o', fmt(lc.open));
  setText('ohlc-h', fmt(lc.high));
  setText('ohlc-l', fmt(lc.low));
  setText('ohlc-c', fmt(lc.close));
  setText('rp-high', fmt(Math.max(...S.highArr)));
  setText('rp-low',  fmt(Math.min(...S.lowArr)));
}

function buildCorrChart(n, mins) {
  const corrD = []; const now = Math.floor(Date.now()/1000);
  let cv = S.corr || -0.65;
  for(let i=20;i<n;i++) {
    cv = Math.max(-1, Math.min(0, cv+(Math.random()-0.5)*0.01));
    corrD.push({time:now-(n-1-i)*mins*60, value:+cv.toFixed(4)});
  }
  // Add real-time corr at end
  corrD.push({time:now, value:S.corr});
  CORRS.setData(corrD);
}

function updateTPSLLines() {
  const now = Math.floor(Date.now()/1000);
  const t0  = now - 200*tfMins[S.tf]*60;
  if(S.tp>0) TPL.setData([{time:t0,value:S.tp},{time:now,value:S.tp}]);
  if(S.sl>0) SLL.setData([{time:t0,value:S.sl},{time:now,value:S.sl}]);
}

/* ══════════════════════════════════════════
   API FETCH
══════════════════════════════════════════ */
async function fetchSnap() {
  try {
    const r = await fetch(API_URL+'/api/snapshot', {
      headers:{'X-API-Key':API_KEY},
      signal:AbortSignal.timeout(6000)
    });
    if(!r.ok) return null;
    return await r.json();
  } catch(e) { return null; }
}

function applySnap(d) {
  if(!d || typeof d !== 'object') return;
  S.prevPrice = S.price || d.gold_price || 3284;
  if(d.gold_price  && +d.gold_price>100)  S.price   = +d.gold_price;
  if(d.dxy_price   && +d.dxy_price>0)     S.dxy     = +d.dxy_price;
  if(typeof d.correlation==='number')      S.corr    = +d.correlation;
  if(d.gold_bid    && +d.gold_bid>0)       S.bid     = +d.gold_bid;   else S.bid = S.price-0.15;
  if(d.gold_ask    && +d.gold_ask>0)       S.ask     = +d.gold_ask;   else S.ask = S.price+0.15;
  if(typeof d.gold_change==='number')      S.goldChg = +d.gold_change; else S.goldChg = S.price-S.prevPrice;
  if(typeof d.gold_pct==='number')         S.goldPct = +d.gold_pct;   else S.goldPct = (S.goldChg/(S.prevPrice||S.price))*100;
  if(typeof d.dxy_change==='number')       S.dxyChg  = +d.dxy_change;
  if(typeof d.winrate==='number')          S.winrate = +d.winrate;
  if(typeof d.wins==='number')             S.wins    = +d.wins;
  if(typeof d.losses==='number')           S.losses  = +d.losses;
  if(d.mt5_connected!=null)                S.mt5Ok   = !!d.mt5_connected;
  if(d.last_update)                        S.lastUpdate = d.last_update;
  if(Array.isArray(d.bot_logs))            S.logs    = d.bot_logs;
  if(Array.isArray(d.signals))             S.signals = d.signals;
  if(d.zones && typeof d.zones==='object') S.zones   = d.zones;

  const sig = d.signal || {};
  if(sig.direction)  S.signal = sig.direction;
  if(sig.confidence) S.conf   = +sig.confidence;
  if(sig.entry && +sig.entry>0) S.entry = +sig.entry;
  if(sig.tp    && +sig.tp>0)    S.tp    = +sig.tp;
  if(sig.sl    && +sig.sl>0)    S.sl    = +sig.sl;
  if(sig.rr)    S.rr   = +sig.rr;
  if(sig.lot)   S.lot  = +sig.lot;
  if(sig.pipeline_state) S.pipe = sig.pipeline_state;
  if(sig.gold_price && +sig.gold_price>100 && !S.price) S.price = +sig.gold_price;

  const mtf = d.mtf_analysis || d.mtf || {};
  if(mtf.H1)  S.mtf.H1  = mtf.H1;
  if(mtf.M15) S.mtf.M15 = mtf.M15;
  if(mtf.M5)  S.mtf.M5  = mtf.M5;

  const ohlcv = d.ohlcv || {};
  ['M5','M15','H1'].forEach(tf => {
    if(ohlcv[tf] && ohlcv[tf].length > 5) S.ohlcv[tf] = ohlcv[tf];
  });
}

// Apply initial server-side snapshot
if(INIT_SNAP && typeof INIT_SNAP === 'object') {
  applySnap(INIT_SNAP);
  S.apiOk = Object.keys(INIT_SNAP).length > 0;
}

/* ══════════════════════════════════════════
   UI UPDATE
══════════════════════════════════════════ */
function fmt(v) { return (+v).toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function setText(id,v) { const el=document.getElementById(id); if(el) el.textContent=v; }
function setColor(id,c) { const el=document.getElementById(id); if(el) el.style.color=c; }

function updateUI() {
  const p=S.price, chg=S.goldChg||0, pct=S.goldPct||0;
  const up=chg>=0, sig=S.signal||'WAIT';
  const upColor='var(--green)', dnColor='var(--red)';

  // Topbar
  setText('tp-price', p>0?fmt(p):'—');
  const tpChgEl = document.getElementById('tp-chg');
  if(tpChgEl) { tpChgEl.textContent=(up?'▲ +':'▼ ')+Math.abs(chg).toFixed(2)+' ('+(up?'+':'')+pct.toFixed(2)+'%)'; tpChgEl.style.color=up?upColor:dnColor; }
  setText('tp-conf', S.conf+'%');
  const tb=document.getElementById('tp-badge');
  if(tb){tb.textContent='● '+sig; tb.className='badge '+(sig==='BUY'?'buy':sig==='SELL'?'sell':'wait');}
  setText('acct-status', S.apiOk?'Live':'Simulation');

  // Sidebar Gold
  setText('sb-gold', p>0?fmt(p):'—');
  const sgc=document.getElementById('sb-gold-chg');
  if(sgc){sgc.textContent=(up?'▲ +':'▼ ')+Math.abs(chg).toFixed(2)+' ('+(up?'+':'')+pct.toFixed(2)+'%)'; sgc.className='chg '+(up?'up':'dn');}
  setText('sb-bid', S.bid>0?fmt(S.bid):'—');
  setText('sb-ask', S.ask>0?fmt(S.ask):'—');

  // DXY
  setText('sb-dxy', S.dxy?S.dxy.toFixed(3):'—');
  const dc=S.dxyChg||0, dup=dc>=0;
  const dxEl=document.getElementById('sb-dxy-chg');
  if(dxEl){dxEl.textContent=(dup?'▲ +':'▼ ')+Math.abs(dc).toFixed(4); dxEl.className='chg '+(dup?'up':'dn');}

  // Correlation
  const corr=S.corr||0;
  const cc=corr<-0.6?'var(--green)':corr<-0.4?'var(--gold)':'var(--red)';
  const ctxt=corr<-0.6?'✅ Forte — signal possible':corr<-0.4?'⚠️ Modérée — attendre':'❌ Faible — éviter';
  ['sb-corr','sb-corr2','sig-corr2','sig-corr-big'].forEach(id=>{
    setText(id, corr.toFixed(4)); setColor(id, cc);
  });
  ['sb-corr-bar','sig-corr-bar2'].forEach(id=>{
    const el=document.getElementById(id);
    if(el){el.style.width=(Math.abs(corr)*100)+'%';el.style.background=cc;}
  });
  ['sb-corr-txt','sig-corr-txt2'].forEach(id=>{
    setText(id,ctxt); setColor(id,cc);
  });

  // Signal badge everywhere
  ['sb-sig-badge','sig-badge2'].forEach(id=>{
    const el=document.getElementById(id);
    if(el){el.textContent=sig; el.className='sig-badge '+(sig==='BUY'?'buy':sig==='SELL'?'sell':'wait');}
  });
  const rrStr=S.tp>0&&S.sl>0&&S.entry>0?'1:'+((S.tp-S.entry)/(S.entry-S.sl)).toFixed(2):'—';
  ['sb-conf','sig-conf2'].forEach(id=>setText(id,S.conf+'%'));
  ['sb-entry','sig-entry2'].forEach(id=>setText(id,S.entry>0?fmt(S.entry):'—'));
  ['sb-tp','sig-tp2'].forEach(id=>setText(id,S.tp>0?fmt(S.tp):'—'));
  ['sb-sl','sig-sl2'].forEach(id=>setText(id,S.sl>0?fmt(S.sl):'—'));
  ['sb-rr','sig-rr2'].forEach(id=>setText(id,rrStr));
  ['sb-lot','sig-lot2'].forEach(id=>setText(id,S.lot>0?S.lot.toFixed(2):'—'));
  ['sb-pipe','sig-pipe2','tick-pipe'].forEach(id=>setText(id,S.pipe||'IDLE'));

  // Right panel
  setText('rp-tp',    S.tp>0?fmt(S.tp):'—');
  setText('rp-sl',    S.sl>0?fmt(S.sl):'—');
  setText('rp-entry', S.entry>0?fmt(S.entry):'—');
  setText('rp-rr',    S.lot>0?(S.lot.toFixed(2)+' · '+rrStr):'—');
  setText('rp-tp-pts', S.tp>0&&S.entry>0?'+'+(S.tp-S.entry).toFixed(2)+' pts':'—');
  setText('rp-sl-pts', S.sl>0&&S.entry>0?'-'+(S.entry-S.sl).toFixed(2)+' pts':'—');

  // Perf
  const wr=S.wins+S.losses>0?Math.round(S.wins/(S.wins+S.losses)*100):(S.winrate||0);
  ['sb-wr','rp-wr','hist-wr'].forEach(id=>{setText(id,wr+'%');});
  ['sb-wl'].forEach(id=>setText(id,S.wins+'/'+S.losses));
  setText('rp-trades', S.wins+S.losses);
  setText('rp-wl', S.wins+'W · '+S.losses+'L');
  const wrBar=document.getElementById('rp-wr-bar'); if(wrBar) wrBar.style.width=wr+'%';

  const risk=wr>65?'Low':wr>50?'Moderate':'High';
  const riskPct=wr>65?25:wr>50?50:80;
  const riskColor=wr>65?'var(--green)':wr>50?'var(--gold)':'var(--red)';
  setText('rp-risk-lbl',risk); setText('risk-lbl',risk); setColor('risk-lbl',riskColor);
  const rb=document.getElementById('rp-risk-bar');
  if(rb){rb.style.width=riskPct+'%';rb.style.background=riskColor;}
  const rdots=document.querySelectorAll('#risk-dots .rdot');
  const nd=wr>65?2:wr>50?3:5, rc=wr>65?'g':wr>50?'y':'r';
  rdots.forEach((d,i)=>{d.className='rdot'+(i<nd?' '+rc:'');});

  // OHLCV close live
  setText('ohlc-c', p>0?fmt(p):'—');

  // Connexion
  const da=document.getElementById('dot-api'); if(da) da.className='dot '+(S.apiOk?'g':'y');
  setText('lbl-api', S.apiOk?'API Live':'Simulation');
  setColor('lbl-api', S.apiOk?'var(--green)':'var(--gold)');
  const dm=document.getElementById('dot-mt5'); if(dm) dm.className='dot '+(S.mt5Ok?'g':'y');
  setText('lbl-mt5', S.mt5Ok?'MT5 Connecté':'MT5 Déconnecté');
  setColor('lbl-mt5', S.mt5Ok?'var(--green)':'var(--gold)');

  // Multi-TF
  ['H1','M15','M5'].forEach(tf => {
    const key=tf.toLowerCase().replace('1','1').replace('5','5');
    const d=S.mtf[tf]||{};
    const v=d.signal||'—';
    const cr=typeof d.corr==='number'?d.corr.toFixed(4):'—';
    const tr=d.trend||'—';
    // sidebar
    const el=document.getElementById('mtf-'+key); if(el){el.textContent=v;el.className='tf-sig '+(v==='BUY'?'buy':v==='SELL'?'sell':'wait');}
    // tab
    const bigEl=document.getElementById('mtf-big-'+key); if(bigEl){bigEl.textContent=v;bigEl.className='sig-badge '+(v==='BUY'?'buy':v==='SELL'?'sell':'wait');}
    setText('mtf-corr-'+key, cr);
    setText('mtf-trend-'+key, tr);
  });
  // consensus
  const sigs=['H1','M15','M5'].map(t=>(S.mtf[t]||{}).signal||'WAIT');
  const buys=sigs.filter(s=>s==='BUY').length, sells=sigs.filter(s=>s==='SELL').length;
  const cons=buys>=2?'🟢 CONSENSUS BUY':sells>=2?'🔴 CONSENSUS SELL':'⚪ PAS DE CONSENSUS';
  const consColor=buys>=2?'var(--green)':sells>=2?'var(--red)':'var(--gold)';
  setText('consensus-txt',cons); setColor('consensus-txt',consColor);
  setText('consensus-sub','H1: '+sigs[0]+' · M15: '+sigs[1]+' · M5: '+sigs[2]);

  // Signal tab
  setText('sig-price-big', p>0?fmt(p):'—');
  const spc=document.getElementById('sig-price-chg');
  if(spc){spc.textContent=(up?'▲ +':'▼ ')+Math.abs(chg).toFixed(2)+' ('+(up?'+':'')+pct.toFixed(2)+'%)'; spc.style.color=up?upColor:dnColor;}
  setText('sig-bid', S.bid>0?fmt(S.bid):'—');
  setText('sig-ask', S.ask>0?fmt(S.ask):'—');
  setText('sig-dxy', S.dxy?S.dxy.toFixed(3):'—');
  const z=S.zones||{};
  setText('sig-sup', z.support&&z.support>0?fmt(z.support):'—');
  setText('sig-res', z.resistance&&z.resistance>0?fmt(z.resistance):'—');
  setText('sig-atr', z.atr?z.atr.toFixed(3):'—');
  setText('sig-fvg-b', (z.fvg_bullish||[]).length+' zones');
  setText('sig-fvg-s', (z.fvg_bearish||[]).length+' zones');

  // Ticker
  setText('tick-gold', p>0?p.toFixed(2):'—');
  const tgc=document.getElementById('tick-gold-chg');
  if(tgc){tgc.textContent=(up?'▲ +':'▼ ')+Math.abs(chg).toFixed(2);tgc.className='tc '+(up?'up':'dn');}
  setText('tick-dxy', S.dxy?S.dxy.toFixed(3):'—');
  const tdc=document.getElementById('tick-dxy-chg');
  if(tdc){tdc.textContent=(dup?'▲':'▼')+Math.abs(S.dxyChg||0).toFixed(4);tdc.className='tc '+(dup?'up':'dn');}
  setText('tick-corr', corr.toFixed(3));
  const tcl=document.getElementById('tick-corr-lbl');
  if(tcl){tcl.textContent=corr<-0.6?'✅ FORTE':corr<-0.4?'⚠️ MOD':'❌ FAIBLE'; tcl.className='tc '+(corr<-0.5?'up':'dn');}
  setText('tick-sig', sig); setColor('tick-sig', sig==='BUY'?'var(--green)':sig==='SELL'?'var(--red)':'var(--muted)');
  setText('tick-conf-t', S.conf+'%');
  setText('tick-api', S.apiOk?'LIVE':'SIM'); setColor('tick-api', S.apiOk?'var(--green)':'var(--gold)');
  setText('tick-n', S.tick);
  setText('sb-tick', S.tick);

  // Logs
  renderLogs();

  // Historique
  renderHist();

  const now=new Date().toLocaleTimeString('fr-FR');
  setText('clock',now); setText('sb-time',now);
}

function renderLogs() {
  const wrap=document.getElementById('logs-wrap'); if(!wrap)return;
  const logs=S.logs||[];
  if(!logs.length){wrap.innerHTML='<div style="color:var(--muted);padding:20px">Aucun log disponible</div>';return;}
  const filtered=logs.filter(l=>S.logFilter==='ALL'||l.level===S.logFilter).slice(-100).reverse();
  wrap.innerHTML=filtered.map(l=>{
    const lvl=(l.level||'INFO').toUpperCase();
    const cls={INFO:'log-info',WARNING:'log-warning',ERROR:'log-error',SIGNAL:'log-signal'}[lvl]||'log-info';
    return `<div class="log-line ${cls}">${l.time||''} [${lvl}] ${l.msg||''}</div>`;
  }).join('');
}

function renderHist() {
  const sigs=S.signals||[];
  setText('hist-total',sigs.length);
  const wr=S.wins+S.losses>0?Math.round(S.wins/(S.wins+S.losses)*100):(S.winrate||0);
  setText('hist-wr',wr+'%'); setText('hist-w',S.wins); setText('hist-l',S.losses);
  const tbody=document.getElementById('hist-body'); if(!tbody)return;
  if(!sigs.length){tbody.innerHTML='<tr><td colspan="9" style="color:var(--muted);text-align:center;padding:20px">Aucun signal enregistré</td></tr>';return;}
  tbody.innerHTML=[...sigs].reverse().slice(0,50).map(s=>{
    const res=s.result||'';
    const rc=res==='WIN'?'var(--green)':res==='LOSS'?'var(--red)':res==='OPEN'?'var(--gold)':'var(--muted)';
    const dc=s.direction==='BUY'?'var(--green)':s.direction==='SELL'?'var(--red)':'var(--muted)';
    const resLbl=res==='WIN'?'✅ WIN':res==='LOSS'?'❌ LOSS':res==='OPEN'?'🔵 OPEN':res||'—';
    return `<tr>
      <td style="color:var(--muted)">${(s.time||'').slice(-8)||'—'}</td>
      <td style="color:${dc};font-weight:700">${s.direction||'—'}</td>
      <td>${s.tf||'—'}</td>
      <td>${s.entry>0?fmt(s.entry):'—'}</td>
      <td style="color:var(--green)">${s.tp>0?fmt(s.tp):'—'}</td>
      <td style="color:var(--red)">${s.sl>0?fmt(s.sl):'—'}</td>
      <td>${s.rr?'1:'+s.rr:'—'}</td>
      <td>${s.lot||'—'}</td>
      <td style="color:${rc};font-weight:700">${resLbl}</td>
    </tr>`;
  }).join('');
}

/* ══════════════════════════════════════════
   MAIN LOOP
══════════════════════════════════════════ */
async function mainLoop() {
  S.tick++;
  const snap = await fetchSnap();
  if(snap) {
    S.apiOk=true; applySnap(snap);
  } else {
    S.apiOk=false;
    // Simulation fallback
    S.prevPrice = S.price || 3284;
    if(!S.price) S.price=3284;
    S.price = +(S.price+(Math.random()-0.48)*0.7).toFixed(2);
    S.dxy   = +(S.dxy-(Math.random()-0.48)*0.011).toFixed(3);
    S.corr  = +Math.max(-1,Math.min(0,S.corr+(Math.random()-0.5)*0.007)).toFixed(4);
    S.goldChg = S.price-S.prevPrice;
    S.goldPct = +(S.goldChg/S.prevPrice*100).toFixed(3);
    S.bid=S.price-0.15; S.ask=S.price+0.15;
    S.dxyChg=+(S.dxy-104.23).toFixed(4);
  }

  // Build chart once per TF or on first load
  if(!S.chartLoaded || S.currentChartTF !== S.tf) {
    buildChart();
    S.chartLoaded=true;
  } else {
    // Live update last candle
    const now=Math.floor(Date.now()/1000);
    try {
      CS.update({time:now, open:S.prevPrice||S.price, high:Math.max(S.price,S.prevPrice||S.price), low:Math.min(S.price,S.prevPrice||S.price), close:S.price});
      if(S.highArr.length){
        S.highArr[S.highArr.length-1]=Math.max(S.highArr[S.highArr.length-1],S.price);
        S.lowArr[S.lowArr.length-1]=Math.min(S.lowArr[S.lowArr.length-1],S.price);
        setText('rp-high',fmt(Math.max(...S.highArr)));
        setText('rp-low',fmt(Math.min(...S.lowArr)));
        setText('ohlc-h',fmt(Math.max(...S.highArr)));
        setText('ohlc-l',fmt(Math.min(...S.lowArr)));
      }
    } catch(e){}
    // Live corr
    try { CORRS.update({time:now, value:S.corr}); } catch(e){}
    // TP/SL lines
    updateTPSLLines();
  }

  updateUI();
  setTimeout(mainLoop, S.apiOk?3000:2000);
}

/* ══════════════════════════════════════════
   CONTROLS
══════════════════════════════════════════ */
function switchTab(tab, navEl) {
  document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('.i-btn').forEach(el=>el.classList.remove('active'));
  const tc=document.getElementById('tab-'+tab); if(tc) tc.classList.add('active');
  if(navEl) navEl.classList.add('active');
  // Trigger resize for charts when chart tab reactivated
  if(tab==='chart') { setTimeout(()=>{GC.resize(goldEl.offsetWidth,goldEl.offsetHeight); CC.resize(corrEl.offsetWidth,corrEl.offsetHeight);},50); }
}

function setTF(tf, el) {
  S.tf=tf; S.currentChartTF='';
  document.querySelectorAll('.tf-tab').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
}

function setPill(el) {
  document.querySelectorAll('.tf-pill').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
}

function setSig(dir) {
  S.signal=dir;
  const b=document.getElementById('rp-buy'), s=document.getElementById('rp-sell');
  if(dir==='BUY'){
    if(b){b.style.background='var(--green)';b.style.color='#000';b.style.border='none';}
    if(s){s.classList.remove('on');}
  } else {
    if(s) s.classList.add('on');
    if(b){b.style.background='var(--bg3)';b.style.color='var(--muted)';b.style.border='1px solid var(--border)';}
  }
  updateUI();
}

function filterLogs(f, el) {
  S.logFilter=f;
  document.querySelectorAll('#tab-logs .ct-btn').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
  renderLogs();
}

// Start
mainLoop();
</script>
</body>
</html>
""".replace('__API_URL__', API_URL).replace('__API_KEY__', API_KEY).replace('__SNAP_JSON__', snap_json)

# Hauteur = 100vh dans iframe, on utilise la hauteur max
components.html(HTML, height=980, scrolling=False)
