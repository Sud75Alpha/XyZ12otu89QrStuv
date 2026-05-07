"""
GOLD/DXY Signal Bot v3.0
- Trade lock : 1 seul trade actif à la fois
- STILL BUY/SELL si signal identique pendant trade actif
- Filtre confidence >= 80%
- Toutes les sessions (24h/5j)
- Filtres news économiques
- Gestion capital dynamique
"""

import os, time, logging, requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_URL     = os.getenv("API_URL",  "https://en-ligne-5wi6.onrender.com")
API_KEY     = os.getenv("API_KEY",  "gold_dxy_secret_2024")
API_HEADERS = {"X-API-Key": API_KEY}

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "VOTRE_TOKEN_ICI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "VOTRE_CHAT_ID_ICI")

GOLD_SYMBOLS = ["XAUUSDm", "XAUUSD", "GOLD", "XAU/USD"]
DXY_SYMBOLS  = ["DXYm", "DXY", "USDX", "USDIndex", "DX-Y.NYB"]

# Corrélation
CORR_WINDOW         = 50
CORR_SIGNAL_THRESH  = -0.60   # H1
CORR_CONFIRM_THRESH = -0.50   # M15/M5

# Qualité signal — seuils par timeframe
MIN_CONFIDENCE_H1  = 60   # H1 : signal déclencheur
MIN_CONFIDENCE_M15 = 65   # M15 : confirmation
MIN_CONFIDENCE_M5  = 70   # M5  : entrée
MIN_CONFIDENCE     = 80   # seuil global pour STILL signal

# TP/SL
TP_ATR_MULT = 2.0
SL_ATR_MULT = 1.0
ATR_PERIOD  = 14

# Pipeline
H1_TO_M15_TIMEOUT_MIN = 45
M15_TO_M5_TIMEOUT_MIN = 30
SIGNAL_COOLDOWN_SEC   = 1800  # 30min entre trades

# Sessions : TOUTES (24h/5j)
SESSION_FILTER_ENABLED = False  # False = toutes les sessions

# News
NEWS_FILTER_ENABLED   = True
NEWS_BLOCK_MIN_BEFORE = 30
NEWS_BLOCK_MIN_AFTER  = 30
NEWS_CACHE_TTL        = 3600
NEWS_KEYWORDS = [
    "Non-Farm", "NFP", "CPI", "Fed", "FOMC", "Interest Rate",
    "GDP", "Unemployment", "Inflation", "PPI", "PCE",
    "Retail Sales", "ISM",
]

# Capital
RISK_PERCENT = 1.5
MIN_LOT      = 0.01
MAX_LOT      = 1.0

# Boucle
PRICE_REFRESH_SEC = 5
SIGNAL_SCAN_SEC   = 60
LOG_FILE          = "gold_dxy.log"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

try:
    from risk import compute_smart_sl_tp as _smart_sl_tp
    SMART_RISK = True
except ImportError:
    SMART_RISK = False

# ── LOGGING ───────────────────────────────────────────────────────────────────
def setup_logging():
    logger = logging.getLogger("GoldDXY")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    try:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass
    return logger

log = setup_logging()

# ── MODULE NEWS ────────────────────────────────────────────────────────────────
class NewsFilter:
    def __init__(self):
        self._events: List[Dict] = []
        self._last_fetch: float  = 0.0

    def _fetch(self):
        try:
            r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json", timeout=8)
            if r.status_code != 200:
                return
            events = []
            for ev in r.json():
                if ev.get("country","").upper() != "USD":
                    continue
                if ev.get("impact","").lower() not in ("high","3"):
                    continue
                title = ev.get("title","")
                if not any(kw.lower() in title.lower() for kw in NEWS_KEYWORDS):
                    continue
                try:
                    dt_str = ev.get("date","") + " " + ev.get("time","")
                    dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %I:%M%p")
                    dt = dt.replace(tzinfo=timezone.utc)
                    events.append({"title": title, "time": dt})
                except Exception:
                    pass
            self._events     = events
            self._last_fetch = time.time()
            log.info(f"Calendrier: {len(events)} news USD high-impact")
        except Exception as e:
            log.warning(f"Calendrier fetch: {e}")

    def is_blocked(self) -> Tuple[bool, str]:
        if not NEWS_FILTER_ENABLED:
            return False, ""
        if time.time() - self._last_fetch > NEWS_CACHE_TTL:
            self._fetch()
        now = datetime.now(timezone.utc)
        for ev in self._events:
            delta = (ev["time"] - now).total_seconds() / 60
            if -NEWS_BLOCK_MIN_AFTER <= delta <= NEWS_BLOCK_MIN_BEFORE:
                return True, f"News: {ev['title']} (dans {int(delta)}min)"
        return False, ""

news_filter = NewsFilter()

# ── CAPITAL ────────────────────────────────────────────────────────────────────
_account_balance = 10000.0

def get_balance() -> float:
    global _account_balance
    if MT5_AVAILABLE and mt5:
        try:
            info = mt5.account_info()
            if info:
                _account_balance = float(info.balance)
        except Exception:
            pass
    return _account_balance

def compute_lot(sl_dist: float) -> float:
    balance  = get_balance()
    risk_amt = balance * RISK_PERCENT / 100
    lot      = risk_amt / (sl_dist * 100.0) if sl_dist > 0 else MIN_LOT
    return round(max(MIN_LOT, min(MAX_LOT, round(lot / 0.01) * 0.01)), 2)

# ── HISTORIQUE ─────────────────────────────────────────────────────────────────
class SignalHistory:
    def __init__(self):
        self.signals: List[Dict] = []

    def add(self, d: str, corr: float, conf: int,
            entry: float, tp: float, sl: float, rr: float, lot: float):
        self.signals.append({
            "time": datetime.now().isoformat(), "direction": d,
            "corr": corr, "confidence": conf,
            "entry": entry, "tp": tp, "sl": sl, "rr": rr,
            "lot": lot, "result": "OPEN",
        })
        if len(self.signals) > 100:
            self.signals = self.signals[-100:]

    def get_winrate(self):
        closed = [s for s in self.signals if s["result"] in ("WIN","LOSS")]
        if len(closed) < 3: return 0.0
        return round(sum(1 for s in closed if s["result"]=="WIN") / len(closed) * 100, 1)

    def get_stats(self):
        closed = [s for s in self.signals if s["result"] in ("WIN","LOSS")]
        wins   = sum(1 for s in closed if s["result"]=="WIN")
        return {"winrate": self.get_winrate(), "wins": wins,
                "losses": len(closed)-wins, "total": len(self.signals)}

    def to_list(self): return self.signals.copy()

history = SignalHistory()

# ── MT5 ────────────────────────────────────────────────────────────────────────
gold_symbol:   Optional[str] = None
dxy_symbol:    Optional[str] = None
mt5_connected: bool          = False

def connect_mt5() -> bool:
    global gold_symbol, dxy_symbol, mt5_connected
    if not MT5_AVAILABLE:
        log.warning("MT5 non disponible — simulation")
        gold_symbol = "XAUUSD"; dxy_symbol = "DXY"; mt5_connected = False
        return False
    if not mt5.initialize():
        log.error(f"MT5 échoué: {mt5.last_error()}")
        mt5_connected = False; return False
    info = mt5.account_info()
    if info:
        log.info(f"MT5 | Compte: {info.login} | {info.company}")
    available = {s.name for s in mt5.symbols_get()}
    for s in GOLD_SYMBOLS:
        if s in available: gold_symbol = s; break
    if not gold_symbol:
        for s in available:
            if any(c.upper() in s.upper() for c in ["XAU","GOLD"]):
                gold_symbol = s; break
    for s in DXY_SYMBOLS:
        if s in available: dxy_symbol = s; break
    if not dxy_symbol:
        for s in available:
            if any(c.upper() in s.upper() for c in ["DXY","USDX"]):
                dxy_symbol = s; break
    if not gold_symbol or not dxy_symbol:
        log.error(f"Symboles introuvables: Gold={gold_symbol} DXY={dxy_symbol}")
        mt5_connected = False; return False
    mt5_connected = True
    log.info(f"Symboles: {gold_symbol} | {dxy_symbol}")
    return True

def get_ohlc(symbol: str, tf_mt5, n: int) -> Optional[pd.DataFrame]:
    if not MT5_AVAILABLE or not mt5_connected: return None
    try:
        rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, n)
        if rates is None or len(rates) == 0: return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df = df[["open","high","low","close","tick_volume"]].copy()
        if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
            if df["close"].iloc[-1] > 3000:
                for c in ["open","high","low","close"]:
                    df[c] = (df[c] / 2.0).round(2)
        return df
    except Exception as e:
        log.error(f"get_ohlc {symbol}: {e}"); return None

# ── SIMULATION ─────────────────────────────────────────────────────────────────
def _sim_corr(n: int, tf_min: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    now   = datetime.now()
    times = pd.date_range(end=now, periods=n, freq=f"{tf_min}min")
    rng   = np.random.default_rng(int(time.time()) // (tf_min * 30))
    common = np.cumsum(rng.normal(0, 1, n))
    gc = 2320.0 + (common * 1.2 + np.cumsum(rng.normal(0, 0.4, n))) * 0.8
    dc = 104.5  + (-common * 0.6 + np.cumsum(rng.normal(0, 0.4, n))) * 0.15
    gc -= gc[0] - 2320.0; dc -= dc[0] - 104.5
    def build(closes, vol):
        opens = np.roll(closes, 1); opens[0] = closes[0]
        spread = np.abs(rng.normal(0, vol, n)) * 0.5 + vol * 0.3
        return pd.DataFrame({
            "open": np.round(opens,4), "high": np.round(np.maximum(opens,closes)+spread,4),
            "low":  np.round(np.minimum(opens,closes)-spread,4),
            "close": np.round(closes,4), "tick_volume": rng.exponential(2000,n).astype(int),
        }, index=times)
    return build(gc, 0.5), build(dc, 0.02)

# ── TECHNIQUES ────────────────────────────────────────────────────────────────
def compute_atr(df: pd.DataFrame, p: int = ATR_PERIOD) -> float:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    tr = pd.concat([hl,hc,lc], axis=1).max(axis=1)
    v  = tr.rolling(p).mean().iloc[-1]
    return round(float(v), 4) if not np.isnan(v) else 10.0

def rolling_corr(s1: pd.Series, s2: pd.Series, w: int) -> pd.Series:
    a, b = s1.align(s2, join="inner")
    return a.rolling(w).corr(b)

def get_trend(df: pd.DataFrame, n: int = 5) -> Tuple[str, float, float]:
    if df is None or len(df) < n+1: return "→ Stable", 0.0, 0.0
    last  = float(df["close"].iloc[-1])
    first = float(df["close"].iloc[-n])
    pct   = ((last-first)/first)*100 if first else 0.0
    trend = "↑ Hausse" if pct > 0.03 else ("↓ Baisse" if pct < -0.03 else "→ Stable")
    return trend, round(pct,4), round(last,4)

def compute_confidence(corr: float, corr_prev: float, dxy_pct: float,
                       move: float, atr: float) -> int:
    c1 = min(40, int(abs(corr)*40)) if corr < 0 else 0
    c2 = max(0, int(30 - abs(corr-corr_prev)*60))
    c3 = min(30, int(abs(dxy_pct)*600))
    return min(100, c1+c2+c3)

def compute_tp_sl(direction: str, df: pd.DataFrame,
                  atr: Optional[float]=None) -> Tuple[float,float,float,float,float,float]:
    if atr is None: atr = compute_atr(df)
    entry   = round(float(df["close"].iloc[-1]), 2)
    tp_dist = round(atr * TP_ATR_MULT, 2)
    sl_dist = round(atr * SL_ATR_MULT, 2)
    tp = round(entry+tp_dist,2) if direction=="BUY" else round(entry-tp_dist,2)
    sl = round(entry-sl_dist,2) if direction=="BUY" else round(entry+sl_dist,2)
    rr  = round(tp_dist/sl_dist,2) if sl_dist > 0 else 0.0
    lot = compute_lot(sl_dist)
    return entry, tp, sl, atr, rr, lot

# ── ANALYSE TF ────────────────────────────────────────────────────────────────
def analyze_tf(tf_name: str, tf_mt5, n: int,
               gold_ext=None, dxy_ext=None) -> Optional[Dict]:
    gold_df = gold_ext if gold_ext is not None else get_ohlc(gold_symbol, tf_mt5, n)
    dxy_df  = dxy_ext  if dxy_ext  is not None else get_ohlc(dxy_symbol,  tf_mt5, n)
    if gold_df is None or dxy_df is None:
        log.warning(f"[{tf_name}] Données manquantes"); return None
    if len(gold_df) < CORR_WINDOW+10 or len(dxy_df) < CORR_WINDOW+10:
        log.warning(f"[{tf_name}] Pas assez de barres"); return None

    cs = rolling_corr(gold_df["close"], dxy_df["close"], CORR_WINDOW).dropna()
    if len(cs) < 5: return None

    corr_curr = float(cs.iloc[-1])
    corr_prev = float(cs.iloc[-min(6,len(cs))])
    gold_trend, gold_pct, gold_price = get_trend(gold_df, 5)
    dxy_trend,  dxy_pct,  dxy_price  = get_trend(dxy_df,  5)
    atr = compute_atr(gold_df)

    log.info(f"[{tf_name}] Corr={corr_curr:+.3f} | Gold={gold_trend} {gold_pct:+.3f}% | DXY={dxy_trend} {dxy_pct:+.4f}%")

    thresh = CORR_SIGNAL_THRESH if tf_name=="H1" else CORR_CONFIRM_THRESH
    if corr_curr >= thresh:
        log.info(f"[{tf_name}] Corr insuffisante ({corr_curr:+.3f} >= {thresh})")
        return None

    dxy_up = dxy_pct >  0.010
    dxy_dn = dxy_pct < -0.010
    if not dxy_up and not dxy_dn:
        log.info(f"[{tf_name}] DXY stable ({dxy_pct:+.4f}%)")
        return None

    direction = "SELL" if dxy_up else "BUY"

    # Cohérence Gold
    if direction == "BUY"  and gold_pct < -0.05: return None
    if direction == "SELL" and gold_pct >  0.05: return None

    # Mouvement minimum
    move = abs(float(gold_df["close"].iloc[-1]) - float(gold_df["close"].iloc[-6]))
    if move < atr * 0.2:
        log.info(f"[{tf_name}] Mouvement trop faible ({move:.2f} vs ATR×0.2={atr*0.2:.2f})")
        return None

    conf = compute_confidence(corr_curr, corr_prev, dxy_pct, move, atr)

    # FILTRE QUALITÉ par timeframe
    min_conf = MIN_CONFIDENCE_H1 if tf_name == "H1" else (
               MIN_CONFIDENCE_M15 if tf_name == "M15" else MIN_CONFIDENCE_M5)
    if conf < min_conf:
        log.info(f"[{tf_name}] Conf trop faible ({conf}% < {min_conf}%)")
        return None

    log.info(f"[{tf_name}] ✅ {direction} | Conf={conf}% | Corr={corr_curr:+.3f}")
    return {
        "tf": tf_name, "direction": direction,
        "corr_curr": round(corr_curr,4), "corr_prev": round(corr_prev,4),
        "gold_trend": gold_trend, "gold_pct": gold_pct, "gold_price": gold_price,
        "dxy_trend": dxy_trend,   "dxy_pct": dxy_pct,   "dxy_price": dxy_price,
        "atr": atr, "confidence": conf,
        "gold_df": gold_df, "dxy_df": dxy_df,
    }

# ── PUSH API ───────────────────────────────────────────────────────────────────
def _df_to_ohlcv(df: Optional[pd.DataFrame], limit: int=200) -> List[Dict]:
    if df is None or df.empty: return []
    out = []
    for idx, row in df.tail(limit).iterrows():
        out.append({"time": idx.isoformat() if hasattr(idx,"isoformat") else str(idx),
                    "open": round(float(row["open"]),5), "high": round(float(row["high"]),5),
                    "low":  round(float(row["low"]),5),  "close": round(float(row["close"]),5),
                    "volume": int(row.get("tick_volume",0))})
    return out

def push_snapshot(pipeline_state: str, gold_dfs: Dict, dxy_dfs: Dict,
                  current_signal=None, mtf_results=None) -> None:
    gm5 = gold_dfs.get("M5"); dm5 = dxy_dfs.get("M5")
    gold_price = round(float(gm5["close"].iloc[-1]),2) if gm5 is not None and not gm5.empty else 0.0
    dxy_price  = round(float(dm5["close"].iloc[-1]),3) if dm5 is not None and not dm5.empty else 0.0
    gold_prev  = float(gm5["close"].iloc[-2]) if gm5 is not None and len(gm5)>1 else gold_price
    dxy_prev   = float(dm5["close"].iloc[-2]) if dm5 is not None and len(dm5)>1 else dxy_price
    gold_change = round(gold_price-gold_prev,2)
    gold_pct    = round((gold_change/gold_prev)*100,3) if gold_prev else 0.0
    dxy_change  = round(dxy_price-dxy_prev,4)

    corr_curr = 0.0
    if gm5 is not None and dm5 is not None and len(gm5) >= CORR_WINDOW:
        s = rolling_corr(gm5["close"], dm5["close"], CORR_WINDOW).dropna()
        if not s.empty: corr_curr = round(float(s.iloc[-1]),4)

    sig: Dict = {
        "direction": "WAIT", "anticipation": None, "confidence": 0,
        "corr": corr_curr, "gold_price": gold_price, "dxy_price": dxy_price,
        "entry": 0.0, "tp": 0.0, "sl": 0.0, "rr": 0.0,
        "sl_source": "—", "pipeline_state": pipeline_state,
    }
    if current_signal:
        sig.update({
            "direction":  current_signal.get("direction","WAIT"),
            "confidence": current_signal.get("confidence",0),
            "corr":       current_signal.get("corr_curr",corr_curr),
            "entry":      current_signal.get("entry",0.0),
            "tp":         current_signal.get("tp",0.0),
            "sl":         current_signal.get("sl",0.0),
            "rr":         current_signal.get("rr",0.0),
            "sl_source":  current_signal.get("sl_source","ATR"),
            "anticipation": current_signal.get("anticipation"),
        })

    mtf: Dict = {}
    if mtf_results:
        for tf_n, res in mtf_results.items():
            mtf[tf_n] = {
                "signal": res.get("direction","WAIT") if res else "WAIT",
                "corr":   res.get("corr_curr",0.0)   if res else 0.0,
                "trend":  res.get("gold_trend","—")   if res else "—",
                "anticipation": None,
            }

    stats = history.get_stats()
    payload = {
        "gold_price": gold_price, "dxy_price": dxy_price,
        "gold_bid": round(gold_price-0.15,2), "gold_ask": round(gold_price+0.15,2),
        "gold_change": gold_change, "gold_pct": gold_pct,
        "dxy_change": dxy_change,   "correlation": corr_curr,
        "signal": sig, "mtf": mtf,
        "ohlcv": {tf_n: _df_to_ohlcv(gold_dfs.get(tf_n),200) for tf_n in ["M5","M15","H1"]},
        "signals": history.to_list(),
        "winrate": stats["winrate"], "wins": stats["wins"], "losses": stats["losses"],
        "bot_status": "running", "mt5_connected": mt5_connected,
        "gold_symbol": gold_symbol or "XAUUSD",
        "last_update": datetime.now().isoformat(),
    }
    try:
        r = requests.post(f"{API_URL}/api/snapshot/push",
                          json=payload, headers=API_HEADERS, timeout=4)
        if r.status_code == 200:
            log.info(f"Snapshot ✅ | Gold={gold_price} Corr={corr_curr:+.3f}")
        else:
            log.warning(f"Snapshot push {r.status_code}")
    except requests.exceptions.ConnectionError:
        log.debug("API non joignable")
    except Exception as e:
        log.warning(f"Snapshot erreur: {e}")

def push_signal_api(direction: str, tf: str, entry: float, tp: float,
                    sl: float, rr: float, lot: float, sl_source: str,
                    corr: float, confidence: int, status: str="OPEN") -> None:
    try:
        r = requests.post(f"{API_URL}/api/signal/push", headers=API_HEADERS, timeout=4,
                          json={"direction": direction, "tf": tf, "entry": entry,
                                "tp": tp, "sl": sl, "rr": rr, "lot": lot,
                                "sl_source": sl_source, "corr": corr,
                                "confidence": confidence, "result": status,
                                "time": datetime.now().isoformat()})
        if r.status_code == 200:
            log.info(f"Signal API ✅ {direction} @ {entry}")
        else:
            log.warning(f"Signal push {r.status_code}")
    except Exception as e:
        log.warning(f"Signal push erreur: {e}")

# ── TELEGRAM ───────────────────────────────────────────────────────────────────
def send_telegram(text: str) -> bool:
    token   = TELEGRAM_TOKEN
    chat_id = TELEGRAM_CHAT_ID

    # Affiche dans le terminal dans tous les cas
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    print("\n" + "═"*50)
    print(clean)
    print("═"*50 + "\n")

    # Envoie Telegram si token configuré
    if not token or token in ("VOTRE_TOKEN_ICI", ""):
        log.warning("⚠️  TELEGRAM_TOKEN non configuré — message affiché uniquement en terminal")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10)
        if r.status_code == 200:
            log.info("✅ Telegram envoyé")
            return True
        else:
            log.error(f"Telegram erreur {r.status_code}: {r.text[:120]}")
            return False
    except Exception as e:
        log.error(f"Telegram exception: {e}")
        return False

def _stars(c: int) -> str:
    return "⭐⭐⭐" if c >= 80 else ("⭐⭐" if c >= 60 else "⭐")

def msg_startup() -> str:
    return (
        f"🚀 <b>Gold/DXY Bot v3.0 — Démarré</b>\n"
        f"{'─'*30}\n"
        f"• Or  : <b>{gold_symbol}</b>\n"
        f"• DXY : <b>{dxy_symbol}</b>\n"
        f"• Sessions : <b>Toutes (24h/5j)</b>\n"
        f"• Conf min : <b>{MIN_CONFIDENCE}%</b>\n"
        f"• Risque   : <b>{RISK_PERCENT}%/trade</b>\n"
        f"• News     : {'✅ Filtre actif' if NEWS_FILTER_ENABLED else '❌ Désactivé'}\n"
        f"{'─'*30}\n"
        f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

def msg_h1(sig: Dict) -> str:
    d = sig["direction"]
    return (
        f"{'📈' if d=='BUY' else '📉'} <b>{'🟢 BUY' if d=='BUY' else '🔴 SELL'} GOLD</b> — Alerte H1\n"
        f"{'─'*28}\n"
        f"📊 Corr : <code>{sig['corr_prev']:+.3f} → {sig['corr_curr']:+.3f}</code>\n"
        f"📈 Gold : {sig['gold_trend']} ({sig['gold_pct']:+.2f}%) @ <b>{sig['gold_price']}</b>\n"
        f"💵 DXY  : {sig['dxy_trend']} ({sig['dxy_pct']:+.4f}%)\n"
        f"🔥 Conf : <b>{sig['confidence']}%</b> {_stars(sig['confidence'])}\n"
        f"⏳ <b>Attente M15...</b> | ⏰ {datetime.now().strftime('%H:%M')}"
    )

def msg_m15(sig: Dict) -> str:
    d = sig["direction"]
    return (
        f"✅ <b>M15 confirmé — {'🟢 BUY' if d=='BUY' else '🔴 SELL'}</b>\n"
        f"📊 Corr M15 : <code>{sig['corr_prev']:+.3f} → {sig['corr_curr']:+.3f}</code>\n"
        f"🔥 Conf : <b>{sig['confidence']}%</b>\n"
        f"⏳ <b>Attente M5...</b> | ⏰ {datetime.now().strftime('%H:%M')}"
    )

def msg_entry(sig: Dict, entry: float, tp: float, sl: float,
              rr: float, lot: float, sl_src: str, winrate: float) -> str:
    d = sig["direction"]
    return (
        f"{'📈' if d=='BUY' else '📉'} <b>ENTRÉE {'🟢 BUY' if d=='BUY' else '🔴 SELL'} GOLD</b>\n"
        f"{'═'*28}\n"
        f"🎯 <b>H1 + M15 + M5 alignés</b>\n\n"
        f"💰 Entrée : <b>{entry}</b>\n"
        f"   TP     : <b>{tp}</b> 🟢\n"
        f"   SL     : <b>{sl}</b> 🔴\n"
        f"   R/R    : <b>1:{rr}</b>\n"
        f"   Lot    : <b>{lot}</b>\n"
        f"   SL src : {sl_src}\n\n"
        f"📊 Corr : <code>{sig['corr_prev']:+.3f}→{sig['corr_curr']:+.3f}</code>\n"
        f"🔥 Conf : <b>{sig['confidence']}%</b> {_stars(sig['confidence'])}\n"
        f"📈 WR   : {winrate}%\n"
        f"⏰ {datetime.now().strftime('%H:%M')}\n"
        f"<i>⚡ Signal algo — pas un conseil financier</i>"
    )

def msg_still(direction: str, entry: float, tp: float, sl: float) -> str:
    return (
        f"🔄 <b>STILL {'🟢 BUY' if direction=='BUY' else '🔴 SELL'}</b>\n"
        f"Trade actif en cours — pas de nouveau signal\n"
        f"Entrée : {entry} | TP : {tp} | SL : {sl}\n"
        f"⏰ {datetime.now().strftime('%H:%M')}"
    )

# ── TRADE LOCK ─────────────────────────────────────────────────────────────────
class TradeLock:
    """
    Garantit 1 seul trade actif à la fois.
    Si même direction → STILL signal
    Si direction opposée → bloqué silencieusement
    """
    def __init__(self):
        self.active_direction: Optional[str]  = None
        self.active_entry:     float          = 0.0
        self.active_tp:        float          = 0.0
        self.active_sl:        float          = 0.0
        self.active_since:     Optional[datetime] = None
        self.locked:           bool           = False
        self._last_still:      Optional[datetime] = None
        self._cooldown_until:  Optional[datetime] = None

    def is_free(self) -> bool:
        return not self.locked

    def can_open(self, direction: str) -> Tuple[bool, str]:
        """
        Retourne (peut_ouvrir, raison).
        raison = "OK" | "STILL" | "BLOCKED" | "COOLDOWN"
        """
        now = datetime.now()
        # Cooldown post-trade
        if self._cooldown_until and now < self._cooldown_until:
            remaining = int((self._cooldown_until - now).total_seconds() / 60)
            return False, f"COOLDOWN ({remaining}min)"
        # Trade actif
        if self.locked:
            if direction == self.active_direction:
                # STILL signal — max 1 toutes les 15min
                if (self._last_still is None or
                        (now - self._last_still).total_seconds() > 900):
                    self._last_still = now
                    return False, "STILL"
                return False, "STILL_SKIP"
            else:
                return False, "BLOCKED"
        return True, "OK"

    def open(self, direction: str, entry: float, tp: float, sl: float) -> None:
        self.active_direction = direction
        self.active_entry     = entry
        self.active_tp        = tp
        self.active_sl        = sl
        self.active_since     = datetime.now()
        self.locked           = True
        log.info(f"🔒 TradeLock ouvert: {direction} @ {entry}")

    def close(self, result: str) -> None:
        log.info(f"🔓 TradeLock fermé: {self.active_direction} → {result}")
        self.active_direction = None
        self.active_entry     = 0.0
        self.active_tp        = 0.0
        self.active_sl        = 0.0
        self.active_since     = None
        self.locked           = False
        self._cooldown_until  = datetime.now() + timedelta(seconds=SIGNAL_COOLDOWN_SEC)

    def auto_check_result(self, gold_price: float) -> Optional[str]:
        """
        Vérifie si TP ou SL est touché par le prix courant.
        Retourne "WIN" | "LOSS" | None
        """
        if not self.locked or self.active_entry == 0:
            return None
        if self.active_direction == "BUY":
            if gold_price >= self.active_tp: return "WIN"
            if gold_price <= self.active_sl: return "LOSS"
        else:
            if gold_price <= self.active_tp: return "WIN"
            if gold_price >= self.active_sl: return "LOSS"
        return None

trade_lock = TradeLock()

# ── PIPELINE H1 → M15 → M5 ────────────────────────────────────────────────────
class SignalPipeline:
    def __init__(self):
        self.state           = "IDLE"
        self.direction: Optional[str]   = None
        self.h1_signal: Optional[Dict]  = None
        self.m15_signal: Optional[Dict] = None
        self.h1_at: Optional[datetime]  = None
        self.m15_at: Optional[datetime] = None
        self.cycle = 0
        self.current_entry_signal: Optional[Dict] = None

    def reset(self, reason: str="") -> None:
        if reason: log.info(f"Pipeline reset → IDLE ({reason})")
        self.state = "IDLE"; self.direction = None
        self.h1_signal = None; self.m15_signal = None
        self.h1_at = None; self.m15_at = None
        self.current_entry_signal = None

    def _timeout(self) -> bool:
        now = datetime.now()
        if self.state=="WAIT_M15" and self.h1_at:
            if (now-self.h1_at).total_seconds() > H1_TO_M15_TIMEOUT_MIN*60:
                self.reset(f"H1→M15 timeout"); return True
        if self.state=="WAIT_M5" and self.m15_at:
            if (now-self.m15_at).total_seconds() > M15_TO_M5_TIMEOUT_MIN*60:
                self.reset(f"M15→M5 timeout"); return True
        return False

    @staticmethod
    def _elapsed(since) -> int:
        return 0 if since is None else int((datetime.now()-since).total_seconds()/60)

    def get_dashboard_signal(self) -> Optional[Dict]:
        if self.state == "IDLE":
            return self.current_entry_signal
        if self.state == "WAIT_M15" and self.h1_signal:
            s = self.h1_signal
            return {"direction": s["direction"], "confidence": s["confidence"],
                    "corr_curr": s["corr_curr"], "entry": s["gold_price"],
                    "tp": 0.0, "sl": 0.0, "rr": 0.0, "sl_source": "—",
                    "anticipation": f"⏳ H1 OK — Attente M15 ({self._elapsed(self.h1_at)}min)",
                    "pipeline_state": "WAIT_M15"}
        if self.state == "WAIT_M5" and self.m15_signal:
            s = self.m15_signal
            return {"direction": s["direction"], "confidence": s["confidence"],
                    "corr_curr": s["corr_curr"], "entry": s["gold_price"],
                    "tp": 0.0, "sl": 0.0, "rr": 0.0, "sl_source": "—",
                    "anticipation": f"⏳ M15 OK — Attente M5 ({self._elapsed(self.m15_at)}min)",
                    "pipeline_state": "WAIT_M5"}
        return self.current_entry_signal

    def process(self, h1: Optional[Dict], m15: Optional[Dict],
                m5: Optional[Dict]) -> None:
        self.cycle += 1
        if self._timeout(): return
        winrate = history.get_winrate()

        if self.state == "IDLE":
            if h1 is None:
                log.info("Pas de signal H1"); return

            # ── FILTRE QUALITÉ H1 ────────────────────────────────────────────
            if h1["confidence"] < MIN_CONFIDENCE_H1:
                log.info(f"H1 conf trop faible ({h1['confidence']}% < {MIN_CONFIDENCE_H1}%)")
                return

            direction = h1["direction"]

            # ── TRADE LOCK CHECK ──────────────────────────────────────────────
            can_open, reason = trade_lock.can_open(direction)
            if not can_open:
                if reason == "STILL":
                    log.info(f"STILL {direction} — trade déjà actif")
                    send_telegram(msg_still(
                        direction,
                        trade_lock.active_entry,
                        trade_lock.active_tp,
                        trade_lock.active_sl))
                elif reason == "BLOCKED":
                    log.info(f"Signal {direction} bloqué — trade {trade_lock.active_direction} actif")
                elif reason.startswith("COOLDOWN"):
                    log.info(f"Signal bloqué — {reason}")
                return

            log.info(f"🔔 H1 {direction} | Conf={h1['confidence']}% | Corr={h1['corr_curr']:+.3f}")
            send_telegram(msg_h1(h1))
            self.state = "WAIT_M15"; self.direction = direction
            self.h1_signal = h1; self.h1_at = datetime.now()

        elif self.state == "WAIT_M15":
            if m15 is None:
                log.info(f"Attente M15 pour {self.direction}... ({self._elapsed(self.h1_at)}min)")
                return
            if m15["direction"] != self.direction:
                self.reset(f"M15 contradictoire"); return
            # FILTRE QUALITÉ M15
            if m15["confidence"] < MIN_CONFIDENCE_M15:
                log.info(f"M15 conf faible ({m15['confidence']}% < {MIN_CONFIDENCE_M15}%), attente...")
                return
            log.info(f"✅ M15 confirmé {self.direction} | Conf={m15['confidence']}%")
            send_telegram(msg_m15(m15))
            self.state = "WAIT_M5"; self.m15_signal = m15; self.m15_at = datetime.now()

        elif self.state == "WAIT_M5":
            if m5 is None:
                log.info(f"Attente M5 pour {self.direction}... ({self._elapsed(self.m15_at)}min)")
                return
            if m5["direction"] != self.direction:
                self.reset(f"M5 contradictoire"); return
            # FILTRE QUALITÉ M5
            if m5["confidence"] < MIN_CONFIDENCE_M5:
                log.info(f"M5 conf faible ({m5['confidence']}% < {MIN_CONFIDENCE_M5}%), attente...")
                return

            # Calcul TP/SL + lot
            gold_df = m5.get("gold_df")
            if SMART_RISK and gold_df is not None:
                try:
                    entry, tp, sl, atr, rr, sl_src = _smart_sl_tp(m5["direction"], gold_df)
                    lot = compute_lot(atr * SL_ATR_MULT)
                except Exception:
                    entry, tp, sl, atr, rr, lot = compute_tp_sl(m5["direction"], gold_df)
                    sl_src = "ATR"
            elif gold_df is not None:
                entry, tp, sl, atr, rr, lot = compute_tp_sl(m5["direction"], gold_df)
                sl_src = "ATR"
            else:
                self.reset("gold_df manquant"); return

            conf = m5.get("confidence", 0)
            log.info(f"✅ M5 {self.direction} | Entry={entry} TP={tp} SL={sl} R/R=1:{rr} Lot={lot}")

            # Ouvre le trade lock
            trade_lock.open(self.direction, entry, tp, sl)

            # Telegram
            send_telegram(msg_entry(m5, entry, tp, sl, rr, lot, sl_src, winrate))

            # Historique
            history.add(self.direction, m5["corr_curr"], conf, entry, tp, sl, rr, lot)

            # Push API
            push_signal_api(self.direction, "M5", entry, tp, sl, rr, lot,
                            sl_src, m5["corr_curr"], conf)

            self.current_entry_signal = {
                "direction": self.direction, "confidence": conf,
                "corr_curr": m5["corr_curr"], "entry": entry,
                "tp": tp, "sl": sl, "rr": rr, "sl_source": sl_src,
                "lot": lot,
            }
            self.reset("signal complet envoyé")

# ── BOUCLE PRINCIPALE ──────────────────────────────────────────────────────────
def main():
    log.info("="*60)
    log.info("  GOLD/DXY SIGNAL BOT v3.0")
    log.info(f"  Sessions   : Toutes (24h/5j)")
    log.info(f"  Conf min   : {MIN_CONFIDENCE}%")
    log.info(f"  Risque     : {RISK_PERCENT}% / trade")
    log.info(f"  News filtre: {'ON' if NEWS_FILTER_ENABLED else 'OFF'}")
    log.info(f"  API        : {API_URL}")
    log.info("="*60)

    mt5_ok = connect_mt5()
    if MT5_AVAILABLE and not mt5_ok:
        log.error("MT5 non connecté")
        return

    TF_MAP = {"H1": None, "M15": None, "M5": None}
    if MT5_AVAILABLE and mt5_ok:
        TF_MAP = {"H1": mt5.TIMEFRAME_H1,
                  "M15": mt5.TIMEFRAME_M15,
                  "M5":  mt5.TIMEFRAME_M5}

    balance = get_balance()
    log.info(f"Solde : {balance:,.0f}$")
    log.info("Chargement calendrier économique...")
    news_filter._fetch()
    log.info("Envoi Telegram démarrage...")
    send_telegram(msg_startup())

    pipeline = SignalPipeline()
    gold_dfs: Dict = {"M5": None, "M15": None, "H1": None}
    dxy_dfs:  Dict = {"M5": None, "M15": None, "H1": None}
    last_scan = 0.0

    log.info(f"Boucle : prix/{PRICE_REFRESH_SEC}s | signaux/{SIGNAL_SCAN_SEC}s\n")

    try:
        while True:
            t0 = time.time()
            try:
                # Prix M5
                if mt5_ok:
                    gold_dfs["M5"] = get_ohlc(gold_symbol, TF_MAP["M5"], 200)
                    dxy_dfs["M5"]  = get_ohlc(dxy_symbol,  TF_MAP["M5"], 200)
                else:
                    gold_dfs["M5"], dxy_dfs["M5"] = _sim_corr(200, 5)

                # Vérif auto TP/SL atteint
                if gold_dfs["M5"] is not None and not gold_dfs["M5"].empty:
                    gp = float(gold_dfs["M5"]["close"].iloc[-1])
                    result = trade_lock.auto_check_result(gp)
                    if result:
                        log.info(f"🎯 Trade {trade_lock.active_direction} → {result} @ {gp}")
                        send_telegram(
                            f"{'✅' if result=='WIN' else '❌'} <b>{result}</b> — "
                            f"{'🟢 BUY' if trade_lock.active_direction=='BUY' else '🔴 SELL'} clôturé\n"
                            f"Prix : <b>{gp}</b> | {'TP touché 🎯' if result=='WIN' else 'SL touché 🛑'}")
                        # Màj historique
                        for s in reversed(history.signals):
                            if s["result"] == "OPEN":
                                s["result"] = result; break
                        trade_lock.close(result)
                        pipeline.current_entry_signal = None

                do_scan = (time.time() - last_scan) >= SIGNAL_SCAN_SEC
                h1_sig = m15_sig = m5_sig = None

                if do_scan:
                    log.info(f"─── Scan #{pipeline.cycle+1} | {datetime.now().strftime('%H:%M:%S')} ───")

                    # Filtre news
                    blocked, reason = news_filter.is_blocked()
                    if blocked:
                        log.info(f"📰 {reason}")
                        if pipeline.state != "IDLE":
                            send_telegram(f"📰 <b>Signaux suspendus</b>\n{reason}")
                            pipeline.reset("News")
                    else:
                        if mt5_ok:
                            for tf_n, nb in [("H1",120),("M15",150)]:
                                gold_dfs[tf_n] = get_ohlc(gold_symbol, TF_MAP[tf_n], nb)
                                dxy_dfs[tf_n]  = get_ohlc(dxy_symbol,  TF_MAP[tf_n], nb)
                        else:
                            gold_dfs["H1"], dxy_dfs["H1"]  = _sim_corr(120, 60)
                            gold_dfs["M15"], dxy_dfs["M15"] = _sim_corr(150, 15)

                        h1_sig  = analyze_tf("H1",  TF_MAP["H1"],  120, gold_dfs["H1"],  dxy_dfs["H1"])
                        m15_sig = analyze_tf("M15", TF_MAP["M15"], 150, gold_dfs["M15"], dxy_dfs["M15"])
                        m5_sig  = analyze_tf("M5",  TF_MAP["M5"],  200, gold_dfs["M5"],  dxy_dfs["M5"])
                        pipeline.process(h1_sig, m15_sig, m5_sig)

                    last_scan = time.time()

                push_snapshot(
                    pipeline_state = pipeline.state,
                    gold_dfs       = gold_dfs,
                    dxy_dfs        = dxy_dfs,
                    current_signal = pipeline.get_dashboard_signal(),
                    mtf_results    = {"H1": h1_sig, "M15": m15_sig, "M5": m5_sig} if do_scan else None,
                )

            except Exception as e:
                log.error(f"Cycle erreur: {e}", exc_info=True)

            time.sleep(max(0, PRICE_REFRESH_SEC - (time.time()-t0)))

    except KeyboardInterrupt:
        log.info("\n⛔ Arrêt")
    finally:
        if MT5_AVAILABLE and mt5_ok:
            mt5.shutdown()
        log.info("Bot arrêté.")

if __name__ == "__main__":
    main()
