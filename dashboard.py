import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="GOLD/DXY PRO v14",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cache sidebar collapse + remove padding
st.markdown("""
<style>
[data-testid="stSidebar"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}
.main .block-container{padding:0!important;max-width:100%!important;}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
iframe{border:none!important;display:block!important;}
</style>
""", unsafe_allow_html=True)

API_URL = "https://en-ligne-5wi6.onrender.com"
API_KEY = "gold_dxy_secret_2024"

HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GOLD/DXY PRO v14</title>
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#0b0f1a;--bg2:#111827;--bg3:#141c2e;
  --card:#0f1623;--card2:#141e30;--border:rgba(255,255,255,0.07);
  --gold:#f5a623;--green:#00d4aa;--red:#ff4d6a;
  --blue:#4da6ff;--text:#e2e8f0;--muted:#4a5568;
  --sidebar-w:68px;--topbar-h:54px;
}}
body{{background:var(--bg);color:var(--text);font-family:'Space Grotesk',sans-serif;overflow:hidden;height:100vh;display:flex;flex-direction:column;}}
.topbar{{height:var(--topbar-h);background:var(--bg2);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 14px;gap:12px;flex-shrink:0;}}
.topbar-logo{{font-weight:700;font-size:.95rem;color:var(--gold);letter-spacing:.02em;white-space:nowrap;}}
.topbar-logo span{{font-size:.52rem;color:var(--muted);font-weight:400;margin-left:4px;}}
.topbar-nav{{display:flex;gap:2px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:3px;}}
.topbar-nav a{{padding:4px 10px;border-radius:6px;font-size:.6rem;font-weight:600;color:var(--muted);text-decoration:none;cursor:pointer;transition:all .15s;}}
.topbar-nav a.active{{background:rgba(245,166,35,.15);color:var(--gold);}}
.topbar-right{{display:flex;align-items:center;gap:10px;margin-left:auto;}}
.topbar-price .big{{font-family:'JetBrains Mono',monospace;font-size:1.25rem;font-weight:700;color:var(--gold);line-height:1;}}
.topbar-price .small{{font-size:.54rem;margin-top:1px;}}
.topbar-badge{{display:inline-flex;align-items:center;gap:3px;border-radius:6px;padding:3px 9px;font-size:.58rem;font-weight:700;letter-spacing:.05em;}}
.topbar-badge.buy{{background:rgba(0,212,170,.12);border:1px solid rgba(0,212,170,.3);color:var(--green);}}
.topbar-badge.sell{{background:rgba(255,77,106,.12);border:1px solid rgba(255,77,106,.3);color:var(--red);}}
.topbar-badge.wait{{background:rgba(100,116,139,.1);border:1px solid rgba(100,116,139,.2);color:var(--muted);}}
.topbar-account{{display:flex;align-items:center;gap:7px;padding:4px 10px;background:var(--card2);border:1px solid var(--border);border-radius:8px;}}
.topbar-account .bal{{font-family:'JetBrains Mono',monospace;font-size:.68rem;font-weight:600;}}
.topbar-account .sub{{font-size:.48rem;color:var(--muted);}}
.avatar{{width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#ff9f43);display:flex;align-items:center;justify-content:center;font-size:.52rem;font-weight:700;color:#000;}}
.main-layout{{display:flex;flex:1;overflow:hidden;}}
.icon-sidebar{{width:var(--sidebar-w);background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;align-items:center;padding:10px 0;gap:4px;flex-shrink:0;}}
.icon-btn{{width:38px;height:38px;border-radius:9px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:var(--muted);transition:all .15s;position:relative;}}
.icon-btn:hover{{background:rgba(255,255,255,.05);color:var(--text);}}
.icon-btn.active{{background:rgba(245,166,35,.12);color:var(--gold);}}
.icon-btn svg{{width:17px;height:17px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}}
.icon-sidebar-spacer{{flex:1;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}
.dot-live{{width:5px;height:5px;background:var(--green);border-radius:50%;position:absolute;top:6px;right:6px;box-shadow:0 0 5px var(--green);animation:blink 1.6s infinite;}}
.info-sidebar{{width:255px;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow-y:auto;flex-shrink:0;}}
.info-sidebar::-webkit-scrollbar{{width:2px;}}
.info-sidebar::-webkit-scrollbar-thumb{{background:var(--border);}}
.sb-section{{padding:11px 12px 0;}}
.sb-label{{font-size:.46rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:6px;}}
.tf-tabs{{display:flex;gap:3px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:3px;}}
.tf-tab{{flex:1;text-align:center;padding:3px 0;border-radius:6px;font-size:.58rem;font-weight:600;color:var(--muted);cursor:pointer;transition:all .15s;}}
.tf-tab.active{{background:rgba(245,166,35,.18);color:var(--gold);}}
.price-card{{background:var(--card);border:1px solid rgba(245,166,35,.18);border-radius:10px;padding:9px 11px;margin:7px 0;}}
.price-card .sym{{font-size:.46rem;font-weight:700;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;}}
.price-card .val{{font-family:'JetBrains Mono',monospace;font-size:1.4rem;font-weight:700;color:var(--gold);line-height:1.1;margin:2px 0;}}
.price-card .chg{{font-size:.56rem;font-weight:600;}}
.price-card .chg.up{{color:var(--green);}}
.price-card .chg.dn{{color:var(--red);}}
.price-card .ba{{font-size:.5rem;color:#2e3a4e;margin-top:3px;}}
.price-card .ba b{{color:#9ca3af;}}
.dxy-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:9px 11px;margin-bottom:7px;}}
.dxy-card .val{{font-family:'JetBrains Mono',monospace;font-size:1.15rem;font-weight:700;color:var(--blue);}}
.corr-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:9px 11px;margin-bottom:7px;}}
.corr-val{{font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:700;}}
.corr-bar{{height:4px;border-radius:2px;background:#1e2d42;margin:5px 0 3px;overflow:hidden;}}
.corr-fill{{height:100%;border-radius:2px;transition:width .5s,background .5s;}}
.corr-status{{font-size:.52rem;font-weight:600;}}
.signal-card{{background:var(--card);border:1px solid rgba(245,166,35,.2);border-radius:10px;padding:9px 11px;margin-bottom:7px;}}
.sig-badge{{display:inline-flex;align-items:center;padding:3px 10px;border-radius:6px;font-size:.62rem;font-weight:700;letter-spacing:.04em;margin-bottom:6px;}}
.sig-badge.buy{{background:rgba(0,212,170,.15);border:1px solid rgba(0,212,170,.4);color:var(--green);}}
.sig-badge.sell{{background:rgba(255,77,106,.15);border:1px solid rgba(255,77,106,.4);color:var(--red);}}
.sig-badge.wait{{background:rgba(100,116,139,.1);border:1px solid rgba(100,116,139,.25);color:var(--muted);}}
.sig-row{{display:flex;justify-content:space-between;font-size:.56rem;line-height:1.9;}}
.sig-row .lk{{color:var(--muted);}}
.sig-row .lv{{font-weight:600;font-family:'JetBrains Mono',monospace;}}
.sep{{border:none;border-top:1px solid var(--border);margin:7px 12px;}}
.mtf-row{{display:flex;gap:4px;margin-bottom:6px;}}
.mtf-cell{{flex:1;background:var(--card);border:1px solid var(--border);border-radius:7px;padding:6px;text-align:center;}}
.mtf-cell .tf{{font-size:.48rem;font-weight:700;color:var(--muted);margin-bottom:3px;}}
.mtf-cell .sig{{font-size:.56rem;font-weight:700;}}
.mtf-cell .sig.buy{{color:var(--green);}}
.mtf-cell .sig.sell{{color:var(--red);}}
.mtf-cell .sig.wait{{color:var(--muted);}}
.stats-row{{display:flex;gap:4px;margin-bottom:6px;}}
.stat-mini{{flex:1;background:var(--card);border:1px solid var(--border);border-radius:7px;padding:6px 8px;}}
.stat-mini .sk{{font-size:.46rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px;}}
.stat-mini .sv{{font-size:.8rem;font-weight:700;font-family:'JetBrains Mono',monospace;}}
.conn-row{{display:flex;align-items:center;gap:5px;font-size:.54rem;margin-bottom:4px;}}
.dot-g{{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 5px var(--green);flex-shrink:0;}}
.dot-y{{width:5px;height:5px;border-radius:50%;background:var(--gold);flex-shrink:0;}}
.chart-area{{flex:1;display:flex;flex-direction:column;overflow:hidden;background:var(--bg);}}
.chart-topbar{{height:40px;background:var(--bg2);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 12px;gap:10px;flex-shrink:0;}}
.chart-type-btn{{padding:3px 8px;border-radius:5px;font-size:.58rem;font-weight:600;color:var(--muted);cursor:pointer;border:1px solid transparent;transition:all .15s;}}
.chart-type-btn.active{{background:rgba(0,212,170,.12);border-color:rgba(0,212,170,.3);color:var(--green);}}
.chart-sep{{width:1px;height:15px;background:var(--border);}}
.tf-pill{{padding:3px 7px;border-radius:5px;font-size:.56rem;font-weight:600;color:var(--muted);cursor:pointer;transition:all .15s;}}
.tf-pill.active{{background:rgba(0,212,170,.12);color:var(--green);}}
.tf-pill:hover:not(.active){{color:var(--text);}}
.chart-sym{{font-weight:700;font-size:.74rem;}}
.dot-g2{{width:6px;height:6px;background:var(--green);border-radius:50%;display:inline-block;margin-right:4px;box-shadow:0 0 5px var(--green);animation:blink 1.6s infinite;vertical-align:middle;}}
.chart-body{{flex:1;display:flex;overflow:hidden;}}
.main-chart-wrap{{flex:1;display:flex;flex-direction:column;overflow:hidden;padding:7px 7px 0;gap:5px;}}
#chart-gold{{flex:1;border-radius:9px;overflow:hidden;border:1px solid var(--border);background:var(--card);min-height:0;}}
#chart-corr{{height:95px;border-radius:9px;overflow:hidden;border:1px solid var(--border);background:var(--card);flex-shrink:0;}}
.right-panel{{width:285px;border-left:1px solid var(--border);display:flex;flex-direction:column;background:var(--bg2);overflow-y:auto;flex-shrink:0;}}
.right-panel::-webkit-scrollbar{{width:2px;}}
.right-panel::-webkit-scrollbar-thumb{{background:var(--border);}}
.rp-section{{padding:11px 12px;}}
.rp-label{{font-size:.46rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:6px;}}
.order-btns{{display:flex;gap:5px;margin-bottom:9px;}}
.order-btn{{flex:1;padding:8px;border-radius:7px;font-size:.68rem;font-weight:700;text-align:center;cursor:pointer;border:none;letter-spacing:.04em;transition:all .15s;font-family:'Space Grotesk',sans-serif;}}
.btn-buy{{background:var(--green);color:#000;}}
.btn-buy:hover{{background:#00bfa0;}}
.btn-sell{{background:var(--bg3);border:1px solid var(--border);color:var(--muted);}}
.btn-sell.active-sell{{background:var(--red);color:#fff;border-color:var(--red);}}
.tp-sl-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px;}}
.tpsl-card{{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:7px 9px;}}
.tpsl-card.tp{{border-color:rgba(0,212,170,.2);}}
.tpsl-card.sl{{border-color:rgba(255,77,106,.2);}}
.tpsl-card.en{{border-color:rgba(77,166,255,.2);}}
.tpsl-card .lbl{{font-size:.46rem;color:var(--muted);font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:2px;}}
.tpsl-card .val{{font-family:'JetBrains Mono',monospace;font-size:.78rem;font-weight:700;}}
.tpsl-card .sub{{font-size:.48rem;color:var(--muted);margin-top:2px;}}
.rr-wrap{{margin-bottom:8px;}}
.rr-label-row{{display:flex;justify-content:space-between;font-size:.54rem;margin-bottom:3px;}}
.rr-bar{{height:4px;border-radius:2px;background:#1e2d42;overflow:hidden;}}
.rr-fill{{height:100%;border-radius:2px;transition:width .5s;}}
.perf-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:7px;}}
.perf-card{{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:7px 9px;}}
.perf-card .lbl{{font-size:.46rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px;}}
.perf-card .val{{font-family:'JetBrains Mono',monospace;font-size:.88rem;font-weight:700;}}
.wr-bar{{height:4px;border-radius:2px;background:#1e2d42;overflow:hidden;margin:4px 0 2px;}}
.wr-fill{{height:100%;border-radius:2px;background:var(--green);}}
.risk-row-card{{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:7px 9px;margin-bottom:5px;}}
.risk-dots{{display:flex;gap:3px;margin:4px 0 3px;}}
.risk-dot{{flex:1;height:4px;border-radius:2px;background:#1e2d42;}}
.risk-dot.g{{background:var(--green);}}
.risk-dot.y{{background:var(--gold);}}
.ohlcv-card{{background:var(--card);border:1px solid var(--border);border-radius:7px;padding:7px 9px;}}
.api-status{{font-size:.46rem;padding:3px 8px;border-radius:5px;font-weight:700;margin-bottom:5px;display:inline-block;}}
.api-status.live{{background:rgba(0,212,170,.12);border:1px solid rgba(0,212,170,.3);color:var(--green);}}
.api-status.sim{{background:rgba(247,181,41,.1);border:1px solid rgba(247,181,41,.2);color:var(--gold);}}
.bottom-ticker{{height:28px;border-top:1px solid var(--border);background:var(--bg2);display:flex;align-items:center;padding:0 12px;gap:16px;flex-shrink:0;overflow:hidden;}}
.ti{{display:flex;gap:6px;align-items:center;white-space:nowrap;}}
.ti .ts{{font-size:.5rem;font-weight:700;color:var(--muted);}}
.ti .tv{{font-family:'JetBrains Mono',monospace;font-size:.56rem;font-weight:600;}}
.ti .tc{{font-size:.5rem;}}
.ti .tc.up{{color:var(--green);}}
.ti .tc.dn{{color:var(--red);}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-logo">⚡ GOLD/DXY PRO<span>v14</span></div>
  <div class="topbar-nav">
    <a class="active">Chart</a>
    <a>Signal</a>
    <a>Multi-TF</a>
    <a>Logs</a>
    <a>Historique</a>
  </div>
  <div class="topbar-right">
    <div class="topbar-price">
      <div class="big" id="tp-price">3 284.50</div>
      <div class="small" id="tp-chg" style="color:var(--green);">▲ +12.30 (+0.38%)</div>
    </div>
    <div style="width:1px;height:24px;background:var(--border);"></div>
    <div class="topbar-badge buy" id="tp-badge">● BUY</div>
    <div style="font-size:.54rem;color:var(--muted);">Conf <b style="color:var(--text);" id="tp-conf">72%</b></div>
    <div class="topbar-account">
      <div>
        <div class="bal">XAUUSDm · Exness</div>
        <div class="sub" id="conn-status">Connexion...</div>
      </div>
      <div class="avatar">GP</div>
    </div>
  </div>
</div>

<div class="main-layout">
  <div class="icon-sidebar">
    <div class="icon-btn active">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      <div class="dot-live"></div>
    </div>
    <div class="icon-btn"><svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
    <div class="icon-btn"><svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><polyline points="18 9 12 15 9 12 3 18"/></svg></div>
    <div class="icon-btn"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg></div>
    <div class="icon-btn"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></div>
    <div class="icon-sidebar-spacer"></div>
    <div class="icon-btn"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></div>
  </div>

  <div class="info-sidebar">
    <div class="sb-section">
      <div class="sb-label">Timeframe</div>
      <div class="tf-tabs">
        <div class="tf-tab" onclick="setTF('M5',this)">M5</div>
        <div class="tf-tab active" onclick="setTF('M15',this)">M15</div>
        <div class="tf-tab" onclick="setTF('H1',this)">H1</div>
      </div>
    </div>
    <div class="sb-section">
      <div class="price-card">
        <div class="sym">XAUUSD — OR</div>
        <div class="val" id="sb-gold">—</div>
        <div class="chg up" id="sb-gold-chg">—</div>
        <div class="ba">BID <b id="sb-bid">—</b> &nbsp;|&nbsp; ASK <b id="sb-ask">—</b></div>
      </div>
      <div class="dxy-card">
        <div class="sb-label" style="margin-bottom:4px;">DXY — Dollar Index</div>
        <div class="val" id="sb-dxy">—</div>
        <div style="font-size:.54rem;font-weight:600;margin-top:2px;" id="sb-dxy-chg">—</div>
      </div>
    </div>
    <hr class="sep">
    <div class="sb-section">
      <div class="sb-label">Corrélation Gold/DXY</div>
      <div class="corr-card">
        <div class="corr-val" id="sb-corr" style="color:var(--muted);">—</div>
        <div class="corr-bar"><div class="corr-fill" id="sb-corr-bar" style="width:0%;background:var(--green);"></div></div>
        <div class="corr-status" id="sb-corr-txt" style="color:var(--muted);">En attente...</div>
      </div>
    </div>
    <div class="sb-section">
      <div class="sb-label">Signal Actif</div>
      <div class="signal-card">
        <div><span class="sig-badge wait" id="sb-sig-badge">WAIT</span></div>
        <div class="sig-row"><span class="lk">Confiance</span><span class="lv" id="sb-conf" style="color:var(--text);">—</span></div>
        <div class="sig-row"><span class="lk">Corrélation</span><span class="lv" id="sb-corr2" style="color:var(--text);">—</span></div>
        <div class="sig-row"><span class="lk">Entrée</span><span class="lv" id="sb-entry" style="color:var(--gold);">—</span></div>
        <div class="sig-row"><span class="lk">TP</span><span class="lv" id="sb-tp" style="color:var(--green);">—</span></div>
        <div class="sig-row"><span class="lk">SL</span><span class="lv" id="sb-sl" style="color:var(--red);">—</span></div>
        <div class="sig-row"><span class="lk">R/R</span><span class="lv" id="sb-rr" style="color:var(--text);">—</span></div>
        <div class="sig-row"><span class="lk">Lot</span><span class="lv" id="sb-lot" style="color:var(--text);">—</span></div>
        <div class="sig-row"><span class="lk">Pipeline</span><span class="lv" id="sb-pipe" style="color:var(--gold);">IDLE</span></div>
      </div>
    </div>
    <hr class="sep">
    <div class="sb-section">
      <div class="sb-label">Multi-Timeframe</div>
      <div class="mtf-row">
        <div class="mtf-cell"><div class="tf">H1</div><div class="sig wait" id="mtf-h1">—</div></div>
        <div class="mtf-cell"><div class="tf">M15</div><div class="sig wait" id="mtf-m15">—</div></div>
        <div class="mtf-cell"><div class="tf">M5</div><div class="sig wait" id="mtf-m5">—</div></div>
      </div>
    </div>
    <hr class="sep">
    <div class="sb-section">
      <div class="sb-label">Connexion</div>
      <div class="conn-row"><div id="dot-api" class="dot-y"></div><span id="lbl-api" style="color:var(--gold);">Connexion API...</span></div>
      <div class="conn-row"><div id="dot-mt5" class="dot-y"></div><span id="lbl-mt5" style="color:var(--gold);">MT5 En attente</span></div>
    </div>
    <div class="sb-section" style="padding-bottom:12px;">
      <div class="sb-label">Stats</div>
      <div class="stats-row">
        <div class="stat-mini"><div class="sk">Winrate</div><div class="sv" style="color:var(--green);" id="sb-wr">—</div></div>
        <div class="stat-mini"><div class="sk">W / L</div><div class="sv" id="sb-wl">—</div></div>
      </div>
      <div style="font-size:.46rem;color:#1e2d42;text-align:center;margin-top:5px;line-height:2;">
        Tick #<span id="sb-tick">0</span> · <span id="sb-time">--:--:--</span>
      </div>
    </div>
  </div>

  <div class="chart-area">
    <div class="chart-topbar">
      <span class="chart-sym"><span class="dot-g2"></span>XAUUSD · XAUUSDm</span>
      <div class="chart-sep"></div>
      <div class="chart-type-btn active">Candle</div>
      <div class="chart-type-btn">Line</div>
      <div class="chart-sep"></div>
      <div class="tf-pill" onclick="setPill(this)">1m</div>
      <div class="tf-pill" onclick="setPill(this)">5m</div>
      <div class="tf-pill" onclick="setPill(this)">10m</div>
      <div class="tf-pill active" onclick="setPill(this)">15m</div>
      <div class="tf-pill" onclick="setPill(this)">1h</div>
      <div class="tf-pill" onclick="setPill(this)">5h</div>
      <div class="tf-pill" onclick="setPill(this)">All</div>
      <div class="chart-sep"></div>
      <span style="font-size:.54rem;color:var(--muted);">EMA20 <b style="color:var(--gold);">●</b>&nbsp; EMA50 <b style="color:rgba(255,255,255,.2);">●</b></span>
      <div style="margin-left:auto;font-size:.54rem;color:var(--muted);" id="clock">--:--:--</div>
    </div>
    <div class="chart-body">
      <div class="main-chart-wrap">
        <div id="chart-gold"></div>
        <div id="chart-corr"></div>
      </div>
      <div class="right-panel">
        <div class="rp-section">
          <div class="rp-label">Ordre</div>
          <div class="order-btns">
            <button class="order-btn btn-buy" id="rp-buy-btn" onclick="setSig('BUY')">Buy</button>
            <button class="order-btn btn-sell" id="rp-sell-btn" onclick="setSig('SELL')">Sell</button>
          </div>
          <div class="tp-sl-grid">
            <div class="tpsl-card tp"><div class="lbl">Take Profit</div><div class="val" id="rp-tp" style="color:var(--green);">—</div><div class="sub" id="rp-tp-pts">—</div></div>
            <div class="tpsl-card sl"><div class="lbl">Stop Loss</div><div class="val" id="rp-sl" style="color:var(--red);">—</div><div class="sub" id="rp-sl-pts">—</div></div>
            <div class="tpsl-card en"><div class="lbl">Entrée</div><div class="val" id="rp-entry" style="color:var(--blue);">—</div></div>
            <div class="tpsl-card"><div class="lbl">Lot / R:R</div><div class="val" style="color:var(--text);" id="rp-rr">—</div></div>
          </div>
          <div class="rr-wrap">
            <div class="rr-label-row"><span style="color:var(--muted);">Risk Exposure</span><span style="color:var(--gold);font-weight:600;" id="rp-risk-lbl">—</span></div>
            <div class="rr-bar"><div class="rr-fill" id="rp-risk-bar" style="width:0%;background:var(--gold);"></div></div>
          </div>
        </div>
        <hr class="sep" style="margin:0;">
        <div class="rp-section">
          <div class="rp-label">Performance</div>
          <div class="perf-grid">
            <div class="perf-card"><div class="lbl">Winrate</div><div class="val" style="color:var(--green);" id="rp-wr">—</div><div class="wr-bar"><div class="wr-fill" id="rp-wr-bar" style="width:0%;"></div></div></div>
            <div class="perf-card"><div class="lbl">Trades</div><div class="val" id="rp-trades">—</div><div style="font-size:.48rem;color:var(--muted);margin-top:2px;" id="rp-wl">—</div></div>
            <div class="perf-card"><div class="lbl">Day High</div><div class="val" style="color:var(--green);" id="rp-high">—</div></div>
            <div class="perf-card"><div class="lbl">Day Low</div><div class="val" style="color:var(--red);" id="rp-low">—</div></div>
          </div>
          <div class="risk-row-card">
            <div class="lbl">Risk Level</div>
            <div class="risk-dots" id="risk-dots">
              <div class="risk-dot"></div><div class="risk-dot"></div><div class="risk-dot"></div><div class="risk-dot"></div><div class="risk-dot"></div>
            </div>
            <div style="font-size:.5rem;color:var(--gold);font-weight:600;" id="risk-lbl">—</div>
          </div>
          <div class="ohlcv-card">
            <div class="rp-label" style="margin-bottom:4px;">OHLCV</div>
            <div class="sig-row"><span class="lk">Open</span><span class="lv" id="ohlc-o" style="color:var(--text);">—</span></div>
            <div class="sig-row"><span class="lk">High</span><span class="lv" id="ohlc-h" style="color:var(--green);">—</span></div>
            <div class="sig-row"><span class="lk">Low</span><span class="lv" id="ohlc-l" style="color:var(--red);">—</span></div>
            <div class="sig-row"><span class="lk">Close</span><span class="lv" id="ohlc-c" style="color:var(--gold);">—</span></div>
            <div class="sig-row"><span class="lk">Volume</span><span class="lv" id="ohlc-v" style="color:var(--blue);">—</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="bottom-ticker">
  <div class="ti"><span class="ts">XAUUSD</span><span class="tv" id="tick-gold">—</span><span class="tc up" id="tick-gold-chg">—</span></div>
  <div class="ti"><span class="ts">DXY</span><span class="tv" id="tick-dxy">—</span><span class="tc dn" id="tick-dxy-chg">—</span></div>
  <div class="ti"><span class="ts">CORR</span><span class="tv" id="tick-corr">—</span><span class="tc" id="tick-corr-lbl">—</span></div>
  <div class="ti"><span class="ts">SIGNAL</span><span class="tv" id="tick-sig" style="color:var(--muted);">—</span><span class="tc up" id="tick-conf">—</span></div>
  <div class="ti"><span class="ts">PIPELINE</span><span class="tv" id="tick-pipe" style="color:var(--gold);">IDLE</span></div>
  <div class="ti" style="margin-left:auto;"><span class="ts">API</span><span class="tv" id="tick-api" style="color:var(--muted);">—</span></div>
  <div class="ti"><span class="ts">TICK #</span><span class="tv" id="tick-n">0</span></div>
</div>

<script>
const API_URL = '{API_URL}';
const API_KEY = '{API_KEY}';

const S = {{
  price:3284.50, prevPrice:3284.50, dxy:104.23, corr:-0.68,
  signal:'WAIT', conf:0, tp:0, sl:0, entry:0, lot:0,
  wins:0, losses:0, winrate:0, tick:0, tf:'M15',
  apiOk:false, mt5Ok:false,
  ohlcv:{{M5:[],M15:[],H1:[]}},
  highArr:[], lowArr:[],
  initDone:false
}};

const tfMins={{M5:5,M15:15,H1:60}};

/* ── CHARTS ── */
const goldEl=document.getElementById('chart-gold');
const corrEl=document.getElementById('chart-corr');
const GC=LightweightCharts.createChart(goldEl,{{layout:{{background:{{color:'#0f1623'}},textColor:'#4a5568'}},grid:{{vertLines:{{color:'rgba(255,255,255,0.03)'}},horzLines:{{color:'rgba(255,255,255,0.03)'}}}},crosshair:{{mode:LightweightCharts.CrosshairMode.Normal}},rightPriceScale:{{borderColor:'rgba(255,255,255,0.06)'}},timeScale:{{borderColor:'rgba(255,255,255,0.06)',timeVisible:true,secondsVisible:false}}}});
const CS=GC.addCandlestickSeries({{upColor:'#00d4aa',downColor:'#ff4d6a',borderUpColor:'#00d4aa',borderDownColor:'#ff4d6a',wickUpColor:'#00d4aa',wickDownColor:'#ff4d6a'}});
const E20=GC.addLineSeries({{color:'#f5a623',lineWidth:1.5,lineStyle:1,priceLineVisible:false,title:'EMA20'}});
const E50=GC.addLineSeries({{color:'rgba(255,255,255,0.18)',lineWidth:1,priceLineVisible:false,title:'EMA50'}});
const VOL=GC.addHistogramSeries({{color:'rgba(0,212,170,0.3)',priceFormat:{{type:'volume'}},priceScaleId:'vol',scaleMargins:{{top:0.82,bottom:0}}}});
const TPL=GC.addLineSeries({{color:'rgba(0,212,170,0.55)',lineWidth:1,lineStyle:2,priceLineVisible:false}});
const SLL=GC.addLineSeries({{color:'rgba(255,77,106,0.55)',lineWidth:1,lineStyle:2,priceLineVisible:false}});
const CC=LightweightCharts.createChart(corrEl,{{layout:{{background:{{color:'#0f1623'}},textColor:'#4a5568'}},grid:{{vertLines:{{color:'rgba(255,255,255,0.02)'}},horzLines:{{color:'rgba(255,255,255,0.02)'}}}},rightPriceScale:{{borderColor:'rgba(255,255,255,0.06)'}},timeScale:{{borderColor:'rgba(255,255,255,0.06)',visible:false}},crosshair:{{mode:LightweightCharts.CrosshairMode.Normal}}}});
const CORRS=CC.addLineSeries({{color:'#f5a623',lineWidth:1.5,priceLineVisible:false,autoscaleInfoProvider:()=>{{return {{priceRange:{{minValue:-1,maxValue:1}}}}}}}});

const ro=new ResizeObserver(()=>{{GC.resize(goldEl.offsetWidth,goldEl.offsetHeight);CC.resize(corrEl.offsetWidth,corrEl.offsetHeight);}});
ro.observe(goldEl); ro.observe(corrEl);

/* ── HELPERS ── */
function fmt(v){{return (+v).toLocaleString('fr-FR',{{minimumFractionDigits:2,maximumFractionDigits:2}});}}

function buildChartFromOHLCV(candles, tf){{
  if(!candles||candles.length<2)return false;
  const data=[],em20=[],em50=[],vol=[],corrD=[];
  let e20=candles[0].close, e50=candles[0].close;
  candles.forEach((c,i)=>{{
    const t=Math.floor(new Date(c.time).getTime()/1000)||c.time;
    data.push({{time:t,open:+c.open,high:+c.high,low:+c.low,close:+c.close}});
    e20=e20*(19/20)+(+c.close)*(1/20);
    e50=e50*(49/50)+(+c.close)*(1/50);
    if(i>=20)em20.push({{time:t,value:+e20.toFixed(2)}});
    if(i>=50)em50.push({{time:t,value:+e50.toFixed(2)}});
    vol.push({{time:t,value:+(c.volume||c.tick_volume||1000),color:+c.close>=+c.open?'rgba(0,212,170,0.35)':'rgba(255,77,106,0.35)'}});
  }});
  CS.setData(data); E20.setData(em20); E50.setData(em50); VOL.setData(vol);
  S.highArr=data.map(x=>x.high); S.lowArr=data.map(x=>x.low);
  document.getElementById('rp-high').textContent=fmt(Math.max(...S.highArr));
  document.getElementById('rp-low').textContent=fmt(Math.min(...S.lowArr));
  if(data.length>0){{
    const lc=data[data.length-1];
    document.getElementById('ohlc-o').textContent=fmt(lc.open);
    document.getElementById('ohlc-h').textContent=fmt(lc.high);
    document.getElementById('ohlc-l').textContent=fmt(lc.low);
    document.getElementById('ohlc-c').textContent=fmt(lc.close);
    document.getElementById('ohlc-v').textContent=(+(vol[vol.length-1]?.value||0)/1000).toFixed(1)+'K';
  }}
  updateTPSLLines(data);
  return true;
}}

function buildSimOHLCV(n,mins,base){{
  const data=[],em20=[],em50=[],vol=[];
  let p=base,e20=base,e50=base;
  const now=Math.floor(Date.now()/1000);
  for(let i=0;i<n;i++){{
    const t=now-(n-1-i)*mins*60;
    const chg=(Math.random()-0.48)*base*0.0022;
    const o=p,c=p+chg;
    const h=Math.max(o,c)+(Math.random()*base*0.0007);
    const l=Math.min(o,c)-(Math.random()*base*0.0007);
    data.push({{time:t,open:+o.toFixed(2),high:+h.toFixed(2),low:+Math.max(l,0.01).toFixed(2),close:+c.toFixed(2)}});
    e20=e20*(19/20)+c*(1/20); e50=e50*(49/50)+c*(1/50);
    if(i>=20)em20.push({{time:t,value:+e20.toFixed(2)}});
    if(i>=50)em50.push({{time:t,value:+e50.toFixed(2)}});
    vol.push({{time:t,value:Math.floor(Math.random()*12000+1000),color:c>=o?'rgba(0,212,170,0.35)':'rgba(255,77,106,0.35)'}});
    p=c;
  }}
  data[data.length-1].close=base;
  CS.setData(data); E20.setData(em20); E50.setData(em50); VOL.setData(vol);
  S.highArr=data.map(x=>x.high); S.lowArr=data.map(x=>x.low);
  document.getElementById('rp-high').textContent=fmt(Math.max(...S.highArr));
  document.getElementById('rp-low').textContent=fmt(Math.min(...S.lowArr));
  updateTPSLLines(data);
}}

function updateTPSLLines(data){{
  if(!data||data.length<2)return;
  const t0=data[0].time, t1=data[data.length-1].time;
  if(S.tp>0)TPL.setData([{{time:t0,value:S.tp}},{{time:t1,value:S.tp}}]);
  if(S.sl>0)SLL.setData([{{time:t0,value:S.sl}},{{time:t1,value:S.sl}}]);
}}

function buildCorrData(n,mins){{
  const corrD=[]; const now=Math.floor(Date.now()/1000);
  let cv=S.corr||(-0.6-Math.random()*0.3);
  for(let i=20;i<n;i++){{
    cv=Math.max(-1,Math.min(0,cv+(Math.random()-0.5)*0.01));
    corrD.push({{time:now-(n-1-i)*mins*60,value:+cv.toFixed(4)}});
  }}
  CORRS.setData(corrD);
}}

/* ── API FETCH ── */
async function fetchAPI(){{
  try{{
    const r=await fetch(API_URL+'/api/snapshot',{{headers:{{'X-API-Key':API_KEY}},signal:AbortSignal.timeout(5000)}});
    if(!r.ok)return null;
    return await r.json();
  }}catch(e){{return null;}}
}}

function applySnap(d){{
  if(!d||typeof d!=='object')return;
  if(d.gold_price&&+d.gold_price>100){{S.prevPrice=S.price; S.price=+d.gold_price;}}
  if(d.dxy_price&&+d.dxy_price>0)S.dxy=+d.dxy_price;
  if(typeof d.correlation==='number')S.corr=+d.correlation;
  if(d.gold_bid&&+d.gold_bid>0)S.bid=+d.gold_bid; else S.bid=S.price-0.15;
  if(d.gold_ask&&+d.gold_ask>0)S.ask=+d.gold_ask; else S.ask=S.price+0.15;
  if(d.gold_change)S.goldChg=+d.gold_change; else S.goldChg=S.price-S.prevPrice;
  if(d.gold_pct)S.goldPct=+d.gold_pct; else S.goldPct=(S.goldChg/S.price*100);
  if(d.dxy_change)S.dxyChg=+d.dxy_change; else S.dxyChg=0;
  if(d.winrate)S.winrate=+d.winrate;
  if(d.wins)S.wins=+d.wins;
  if(d.losses)S.losses=+d.losses;
  if(d.mt5_connected!=null)S.mt5Ok=!!d.mt5_connected;
  if(d.bot_status)S.botStatus=d.bot_status;
  if(d.last_update)S.lastUpdate=d.last_update;

  const sig=d.signal||{{}};
  if(sig.direction)S.signal=sig.direction;
  if(sig.confidence)S.conf=+sig.confidence;
  if(sig.entry&&+sig.entry>0)S.entry=+sig.entry;
  if(sig.tp&&+sig.tp>0)S.tp=+sig.tp;
  if(sig.sl&&+sig.sl>0)S.sl=+sig.sl;
  if(sig.rr)S.rr=+sig.rr;
  if(sig.lot)S.lot=+sig.lot;
  if(sig.pipeline_state)S.pipe=sig.pipeline_state;
  if(sig.gold_price&&+sig.gold_price>100&&S.price<100)S.price=+sig.gold_price;

  const mtf=d.mtf_analysis||d.mtf||{{}};
  S.mtf={{H1:mtf.H1||{{}},M15:mtf.M15||{{}},M5:mtf.M5||({{))}};

  const ohlcv=d.ohlcv||{{}};
  Object.keys(ohlcv).forEach(tf=>{{
    if(ohlcv[tf]&&ohlcv[tf].length>5)S.ohlcv[tf]=ohlcv[tf];
  }});
}}

/* ── UI UPDATE ── */
function updateUI(){{
  const p=S.price, chg=S.goldChg||0, pct=S.goldPct||0;
  const up=chg>=0;
  const sig=S.signal||'WAIT';

  document.getElementById('tp-price').textContent=fmt(p);
  document.getElementById('tp-chg').textContent=(up?'▲ +':'▼ ')+Math.abs(chg).toFixed(2)+' ('+(up?'+':'')+pct.toFixed(2)+'%)';
  document.getElementById('tp-chg').style.color=up?'var(--green)':'var(--red)';
  document.getElementById('tp-conf').textContent=(S.conf||0)+'%';
  const tb=document.getElementById('tp-badge');
  tb.textContent='● '+sig; tb.className='topbar-badge '+(sig==='BUY'?'buy':sig==='SELL'?'sell':'wait');

  document.getElementById('sb-gold').textContent=fmt(p);
  const gc=document.getElementById('sb-gold-chg');
  gc.textContent=(up?'▲ +':'▼ ')+Math.abs(chg).toFixed(2)+' ('+(up?'+':'')+pct.toFixed(2)+'%)';
  gc.className='chg '+(up?'up':'dn');
  document.getElementById('sb-bid').textContent=fmt(S.bid||p-0.15);
  document.getElementById('sb-ask').textContent=fmt(S.ask||p+0.15);

  const dxy=S.dxy||0, dc=S.dxyChg||0, dup=dc>=0;
  document.getElementById('sb-dxy').textContent=dxy.toFixed(3);
  const dchgEl=document.getElementById('sb-dxy-chg');
  dchgEl.textContent=(dup?'▲ +':'▼ ')+Math.abs(dc).toFixed(4);
  dchgEl.style.color=dup?'var(--green)':'var(--red)';

  const corr=S.corr||0;
  const cc=corr<-0.6?'var(--green)':corr<-0.4?'var(--gold)':'var(--red)';
  document.getElementById('sb-corr').textContent=corr.toFixed(4);
  document.getElementById('sb-corr').style.color=cc;
  document.getElementById('sb-corr-bar').style.width=(Math.abs(corr)*100)+'%';
  document.getElementById('sb-corr-bar').style.background=cc;
  document.getElementById('sb-corr-txt').textContent=corr<-0.6?'✅ Forte — signal possible':corr<-0.4?'⚠️ Modérée — attendre':'❌ Faible — éviter';
  document.getElementById('sb-corr-txt').style.color=cc;
  document.getElementById('sb-corr2').textContent=corr.toFixed(4);

  const sb=document.getElementById('sb-sig-badge');
  sb.textContent=sig; sb.className='sig-badge '+(sig==='BUY'?'buy':sig==='SELL'?'sell':'wait');
  document.getElementById('sb-conf').textContent=(S.conf||0)+'%';
  document.getElementById('sb-entry').textContent=S.entry>0?fmt(S.entry):'—';
  document.getElementById('sb-tp').textContent=S.tp>0?fmt(S.tp):'—';
  document.getElementById('sb-sl').textContent=S.sl>0?fmt(S.sl):'—';
  const rr=S.tp>0&&S.sl>0&&S.entry>0?((S.tp-S.entry)/(S.entry-S.sl)).toFixed(2):null;
  document.getElementById('sb-rr').textContent=rr?'1:'+rr:'—';
  document.getElementById('sb-lot').textContent=S.lot>0?S.lot.toFixed(2):'—';
  document.getElementById('sb-pipe').textContent=S.pipe||'IDLE';

  const rp_tp=document.getElementById('rp-tp');
  rp_tp.textContent=S.tp>0?fmt(S.tp):'—';
  document.getElementById('rp-sl').textContent=S.sl>0?fmt(S.sl):'—';
  document.getElementById('rp-entry').textContent=S.entry>0?fmt(S.entry):'—';
  document.getElementById('rp-tp-pts').textContent=S.tp>0&&S.entry>0?'+'+(S.tp-S.entry).toFixed(2)+' pts':'—';
  document.getElementById('rp-sl-pts').textContent=S.sl>0&&S.entry>0?'-'+(S.entry-S.sl).toFixed(2)+' pts':'—';
  document.getElementById('rp-rr').textContent=S.lot>0?(S.lot.toFixed(2)+' · 1:'+(rr||'—')):'—';

  const wr=S.wins+S.losses>0?Math.round(S.wins/(S.wins+S.losses)*100):S.winrate||0;
  document.getElementById('sb-wr').textContent=wr+'%';
  document.getElementById('sb-wl').textContent=S.wins+'/'+S.losses;
  document.getElementById('rp-wr').textContent=wr+'%';
  document.getElementById('rp-wr-bar').style.width=wr+'%';
  document.getElementById('rp-trades').textContent=S.wins+S.losses;
  document.getElementById('rp-wl').textContent=S.wins+'W · '+S.losses+'L';

  const risk=wr>65?'Low':wr>50?'Moderate':'High';
  const riskPct=wr>65?30:wr>50?55:80;
  document.getElementById('rp-risk-lbl').textContent=risk;
  document.getElementById('rp-risk-bar').style.width=riskPct+'%';
  document.getElementById('rp-risk-bar').style.background=wr>65?'var(--green)':wr>50?'var(--gold)':'var(--red)';
  document.getElementById('risk-lbl').textContent=risk;
  const dots=document.querySelectorAll('#risk-dots .risk-dot');
  const nDots=wr>65?2:wr>50?3:5;
  const cls=wr>65?'g':wr>50?'y':'r';
  dots.forEach((d,i)=>{{d.className='risk-dot'+(i<nDots?' '+cls:'');}});

  const mtfTFs=['H1','M15','M5'];
  mtfTFs.forEach(tf=>{{
    const el=document.getElementById('mtf-'+tf.toLowerCase());
    const v=(S.mtf&&S.mtf[tf]&&S.mtf[tf].signal)||'—';
    el.textContent=v; el.className='sig '+(v==='BUY'?'buy':v==='SELL'?'sell':'wait');
  }});

  const apiOk=S.apiOk, mt5Ok=S.mt5Ok;
  const dotApi=document.getElementById('dot-api');
  dotApi.className=apiOk?'dot-g':'dot-y';
  document.getElementById('lbl-api').textContent=apiOk?'API Live':'Simulation';
  document.getElementById('lbl-api').style.color=apiOk?'var(--green)':'var(--gold)';
  const dotMt5=document.getElementById('dot-mt5');
  dotMt5.className=mt5Ok?'dot-g':'dot-y';
  document.getElementById('lbl-mt5').textContent=mt5Ok?'MT5 Connecté':'MT5 Déconnecté';
  document.getElementById('lbl-mt5').style.color=mt5Ok?'var(--green)':'var(--gold)';
  document.getElementById('conn-status').textContent=apiOk?'Live':'Simulation';

  document.getElementById('tick-gold').textContent=p.toFixed(2);
  document.getElementById('tick-gold-chg').textContent=(up?'▲ +':'▼ ')+Math.abs(chg).toFixed(2);
  document.getElementById('tick-gold-chg').className='tc '+(up?'up':'dn');
  document.getElementById('tick-dxy').textContent=dxy.toFixed(3);
  document.getElementById('tick-dxy-chg').textContent=(dup?'▲ +':'▼ ')+Math.abs(dc).toFixed(4);
  document.getElementById('tick-dxy-chg').className='tc '+(dup?'up':'dn');
  document.getElementById('tick-corr').textContent=corr.toFixed(3);
  document.getElementById('tick-corr-lbl').textContent=corr<-0.6?'✅ FORTE':corr<-0.4?'⚠️ MOD':'❌ FAIBLE';
  document.getElementById('tick-corr-lbl').className='tc '+(corr<-0.5?'up':'dn');
  document.getElementById('tick-sig').textContent=sig;
  document.getElementById('tick-sig').style.color=sig==='BUY'?'var(--green)':sig==='SELL'?'var(--red)':'var(--muted)';
  document.getElementById('tick-conf').textContent=(S.conf||0)+'%';
  document.getElementById('tick-pipe').textContent=S.pipe||'IDLE';
  document.getElementById('tick-api').textContent=apiOk?'LIVE':'SIM';
  document.getElementById('tick-api').style.color=apiOk?'var(--green)':'var(--gold)';
  document.getElementById('tick-n').textContent=S.tick;
  document.getElementById('sb-tick').textContent=S.tick;

  const now=new Date().toLocaleTimeString('fr-FR');
  document.getElementById('clock').textContent=now;
  document.getElementById('sb-time').textContent=now;
}}

/* ── MAIN LOOP ── */
let lastChartTF='';
async function mainLoop(){{
  S.tick++;
  const snap=await fetchAPI();
  if(snap){{
    S.apiOk=true;
    applySnap(snap);
  }} else {{
    S.apiOk=false;
    S.prevPrice=S.price;
    S.price=+(S.price+(Math.random()-0.48)*0.6).toFixed(2);
    S.dxy=+(S.dxy-(Math.random()-0.48)*0.01).toFixed(3);
    S.corr=+Math.max(-1,Math.min(0,S.corr+(Math.random()-0.5)*0.007)).toFixed(4);
    S.goldChg=S.price-S.prevPrice;
    S.goldPct=+(S.goldChg/S.prevPrice*100).toFixed(2);
  }}

  // Update chart if tf changed or first load
  const curTF=S.tf||'M15';
  if(curTF!==lastChartTF||!S.initDone){{
    const candles=S.ohlcv[curTF];
    if(candles&&candles.length>10){{
      buildChartFromOHLCV(candles,curTF);
    }} else {{
      buildSimOHLCV(200,tfMins[curTF],S.price);
    }}
    buildCorrData(200,tfMins[curTF]);
    lastChartTF=curTF;
    S.initDone=true;
  }} else {{
    // Live update last candle
    const lastCandle={{time:Math.floor(Date.now()/1000),open:S.prevPrice,high:Math.max(S.price,S.prevPrice),low:Math.min(S.price,S.prevPrice),close:S.price}};
    try{{CS.update(lastCandle);}}catch(e){{}}
    if(S.highArr.length>0){{
      S.highArr[S.highArr.length-1]=Math.max(S.highArr[S.highArr.length-1],S.price);
      S.lowArr[S.lowArr.length-1]=Math.min(S.lowArr[S.lowArr.length-1],S.price);
      document.getElementById('rp-high').textContent=fmt(Math.max(...S.highArr));
      document.getElementById('rp-low').textContent=fmt(Math.min(...S.lowArr));
      document.getElementById('ohlc-h').textContent=fmt(Math.max(...S.highArr));
      document.getElementById('ohlc-l').textContent=fmt(Math.min(...S.lowArr));
    }}
    document.getElementById('ohlc-c').textContent=fmt(S.price);
    if(S.tp>0&&S.sl>0){{
      const allData=[];
      try{{
        const t0=Math.floor(Date.now()/1000)-200*tfMins[curTF]*60;
        TPL.setData([{{time:t0,value:S.tp}},{{time:Math.floor(Date.now()/1000),value:S.tp}}]);
        SLL.setData([{{time:t0,value:S.sl}},{{time:Math.floor(Date.now()/1000),value:S.sl}}]);
      }}catch(e){{}}
    }}
  }}

  updateUI();
  setTimeout(mainLoop, S.apiOk?3000:2000);
}}

/* ── CONTROLS ── */
function setTF(tf,el){{
  S.tf=tf; lastChartTF='';
  document.querySelectorAll('.tf-tab').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
}}
function setPill(el){{
  document.querySelectorAll('.tf-pill').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
}}
function setSig(dir){{
  S.signal=dir;
  const buyBtn=document.getElementById('rp-buy-btn');
  const sellBtn=document.getElementById('rp-sell-btn');
  if(dir==='BUY'){{
    buyBtn.style.background='var(--green)'; buyBtn.style.color='#000'; buyBtn.style.border='none';
    sellBtn.className='order-btn btn-sell';
  }} else {{
    sellBtn.className='order-btn btn-sell active-sell';
    buyBtn.style.background='var(--bg3)'; buyBtn.style.color='var(--muted)'; buyBtn.style.border='1px solid var(--border)';
  }}
  updateUI();
}}

mainLoop();
</script>
</body>
</html>"""

components.html(HTML, height=920, scrolling=False)
