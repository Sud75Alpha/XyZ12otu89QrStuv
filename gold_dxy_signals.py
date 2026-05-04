"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              GOLD / DXY — SYSTÈME DE SIGNAUX PROGRESSIFS v3.0               ║
║         H1 (alerte) → M15 (confirmation) → M5 (entrée + TP/SL)             ║
║                                                                              ║
║  NOUVEAU v3.0 :                                                              ║
║  ✅ Filtre calendrier économique (NFP, CPI, Fed ±30min)                     ║
║  ✅ Gestion du capital (lot size dynamique, risque 1-2%)                    ║
║  ✅ Filtre sessions London + New York                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Tuple
import os

API_URL     = os.getenv("API_URL",  "https://en-ligne-5wi6.onrender.com")
API_KEY     = os.getenv("API_KEY",  "gold_dxy_secret_2024")
API_HEADERS = {"X-API-Key": API_KEY}

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

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "VOTRE_TOKEN_ICI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "VOTRE_CHAT_ID_ICI")

GOLD_SYMBOLS = ["XAUUSD", "GOLD", "XAUUSDm", "XAU/USD"]
DXY_SYMBOLS  = ["DXY", "USDX", "USDIndex", "DX-Y.NYB", "DXYF", "DXYm"]

# Corrélation
CORR_WINDOW         = 50
CORR_SIGNAL_THRESH  = -0.60
CORR_CONFIRM_THRESH = -0.50
CORR_BREAK_THRESH   = -0.20

# TP/SL ATR fallback
TP_ATR_MULT = 2.0
SL_ATR_MULT = 1.0
ATR_PERIOD  = 14

# Pipeline timeouts
H1_TO_M15_TIMEOUT_MIN = 45
M15_TO_M5_TIMEOUT_MIN = 30

# Anti-spam
SIGNAL_COOLDOWN_SEC = 3600

# Boucle
PRICE_REFRESH_SEC = 5
SIGNAL_SCAN_SEC   = 60
LOOP_INTERVAL_SEC = 5
LOG_FILE          = "gold_dxy.log"

# ── FILTRE SESSIONS ────────────────────────────────────────────────────────────
# Heures UTC
SESSION_LONDON_START = 8    # 08:00 UTC
SESSION_LONDON_END   = 12   # 12:00 UTC
SESSION_NY_START     = 13   # 13:00 UTC
SESSION_NY_END       = 17   # 17:00 UTC
SESSION_FILTER_ENABLED = True   # False = toutes les sessions autorisées

# ── GESTION DU CAPITAL ─────────────────────────────────────────────────────────
RISK_PERCENT       = 1.5    # % du capital risqué par trade (1-2% recommandé)
ACCOUNT_BALANCE    = 0.0    # mis à jour dynamiquement depuis MT5
GOLD_PIP_VALUE     = 1.0    # valeur d'1 pip en USD pour 0.01 lot (XAUUSDm)
MIN_LOT            = 0.01
MAX_LOT            = 1.0
LOT_STEP           = 0.01

# ── FILTRE CALENDRIER ÉCONOMIQUE ───────────────────────────────────────────────
NEWS_FILTER_ENABLED  = True
NEWS_BLOCK_MIN_BEFORE = 30   # bloquer N minutes AVANT la news
NEWS_BLOCK_MIN_AFTER  = 30   # bloquer N minutes APRÈS la news
NEWS_CACHE_TTL        = 3600 # rafraîchir le calendrier toutes les heures
# Événements à filtrer (high impact USD)
NEWS_KEYWORDS = [
    "Non-Farm", "NFP", "CPI", "Fed", "FOMC", "Interest Rate",
    "GDP", "Unemployment", "Inflation", "PPI", "PCE",
    "Retail Sales", "ISM", "PMI Manufacturing",
]

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging() -> logging.Logger:
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

# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 1 — FILTRE SESSIONS (London + New York)
# ─────────────────────────────────────────────────────────────────────────────

def is_trading_session() -> Tuple[bool, str]:
    """
    Vérifie si on est dans une session autorisée (London ou New York) en UTC.
    Retourne (autorisé, raison).
    """
    if not SESSION_FILTER_ENABLED:
        return True, "Filtre sessions désactivé"

    now_utc = datetime.now(timezone.utc)
    hour    = now_utc.hour
    weekday = now_utc.weekday()  # 0=Lundi, 6=Dimanche

    # Week-end : marché fermé
    if weekday >= 5:
        return False, f"Week-end ({['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][weekday]})"

    # London : 08h-12h UTC
    in_london = SESSION_LONDON_START <= hour < SESSION_LONDON_END
    # New York : 13h-17h UTC
    in_ny     = SESSION_NY_START <= hour < SESSION_NY_END

    if in_london:
        return True, f"Session London ({hour:02d}h UTC)"
    if in_ny:
        return True, f"Session New York ({hour:02d}h UTC)"

    return False, f"Hors session ({hour:02d}h UTC — London 08-12h, NY 13-17h)"


# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 2 — FILTRE CALENDRIER ÉCONOMIQUE
# ─────────────────────────────────────────────────────────────────────────────

class NewsFilter:
    """
    Récupère le calendrier économique depuis ForexFactory (API publique)
    et bloque les signaux ±30min autour des news USD high-impact.
    """
    def __init__(self):
        self._events: List[Dict] = []
        self._last_fetch: float  = 0.0

    def _fetch_events(self) -> None:
        """Récupère les events du jour depuis ForexFactory RSS."""
        try:
            now   = datetime.now(timezone.utc)
            url   = f"https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            r     = requests.get(url, timeout=8)
            if r.status_code != 200:
                log.warning(f"Calendrier éco: status {r.status_code}")
                return
            data = r.json()
            events = []
            for ev in data:
                # Filtre : USD, impact High
                if ev.get("country", "").upper() != "USD":
                    continue
                if ev.get("impact", "").lower() not in ("high", "3"):
                    continue
                title = ev.get("title", "")
                # Filtre par mot-clé
                if not any(kw.lower() in title.lower() for kw in NEWS_KEYWORDS):
                    continue
                # Parse date
                try:
                    dt_str = ev.get("date", "") + " " + ev.get("time", "")
                    dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %I:%M%p")
                    dt = dt.replace(tzinfo=timezone.utc)
                    events.append({"title": title, "time": dt})
                except Exception:
                    pass
            self._events     = events
            self._last_fetch = time.time()
            log.info(f"Calendrier éco: {len(events)} news USD high-impact chargées")
        except Exception as e:
            log.warning(f"Calendrier éco fetch erreur: {e}")

    def is_news_time(self) -> Tuple[bool, str]:
        """
        Retourne (bloqué, raison).
        Bloqué si une news high-impact est dans ±NEWS_BLOCK_MIN minutes.
        """
        if not NEWS_FILTER_ENABLED:
            return False, ""

        # Rafraîchit le cache si expiré
        if time.time() - self._last_fetch > NEWS_CACHE_TTL:
            self._fetch_events()

        now = datetime.now(timezone.utc)
        for ev in self._events:
            delta = (ev["time"] - now).total_seconds() / 60
            if -NEWS_BLOCK_MIN_AFTER <= delta <= NEWS_BLOCK_MIN_BEFORE:
                if delta >= 0:
                    return True, f"⏰ News dans {int(delta)}min : {ev['title']}"
                else:
                    return True, f"⏰ News il y a {int(-delta)}min : {ev['title']}"
        return False, ""


news_filter = NewsFilter()


# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 3 — GESTION DU CAPITAL
# ─────────────────────────────────────────────────────────────────────────────

def get_account_balance() -> float:
    """Récupère le solde du compte MT5."""
    global ACCOUNT_BALANCE
    if MT5_AVAILABLE and mt5_connected:
        try:
            info = mt5.account_info()
            if info:
                ACCOUNT_BALANCE = float(info.balance)
                return ACCOUNT_BALANCE
        except Exception:
            pass
    return ACCOUNT_BALANCE or 1000.0  # fallback démo


def compute_lot_size(sl_pips: float, balance: Optional[float] = None) -> float:
    """
    Calcule le lot size dynamique basé sur le % de risque.

    Formule :
        risk_amount = balance × RISK_PERCENT / 100
        lot_size    = risk_amount / (sl_pips × pip_value_per_lot)

    Pour XAUUSDm : 1 pip = $1 pour 0.01 lot → pip_value = $100/lot
    """
    if balance is None:
        balance = get_account_balance()

    if sl_pips <= 0:
        return MIN_LOT

    risk_amount      = balance * RISK_PERCENT / 100
    pip_value_per_lot = 100.0   # $100 par lot pour XAUUSD (1 pip = $10 pour 0.1 lot)
    raw_lot          = risk_amount / (sl_pips * pip_value_per_lot)

    # Arrondi au LOT_STEP
    lot = round(round(raw_lot / LOT_STEP) * LOT_STEP, 2)
    lot = max(MIN_LOT, min(MAX_LOT, lot))

    log.info(f"Capital: balance={balance:.0f}$ | risque={RISK_PERCENT}% "
             f"({risk_amount:.0f}$) | SL={sl_pips:.1f}pts | lot={lot}")
    return lot


def compute_tp_sl_with_lot(direction: str, gold_df: pd.DataFrame,
                            balance: Optional[float] = None,
                            atr: Optional[float] = None
                            ) -> Tuple[float, float, float, float, float, float]:
    """
    Calcule TP, SL, R/R ET lot size.
    Retourne (entry, tp, sl, atr, rr, lot_size)
    """
    if atr is None:
        atr = compute_atr(gold_df)
    entry   = round(float(gold_df["close"].iloc[-1]), 2)
    tp_dist = round(atr * TP_ATR_MULT, 2)
    sl_dist = round(atr * SL_ATR_MULT, 2)
    tp = round(entry + tp_dist, 2) if direction == "BUY" else round(entry - tp_dist, 2)
    sl = round(entry - sl_dist, 2) if direction == "BUY" else round(entry + sl_dist, 2)
    rr = round(tp_dist / sl_dist, 2) if sl_dist > 0 else 0.0

    # SL en pips (1 pip = 0.01 pour XAUUSD, mais Exness cote en points donc 1:1)
    sl_pips  = sl_dist   # pour XAUUSDm : 1 point = $1 par lot → sl_dist = nb points
    lot_size = compute_lot_size(sl_pips, balance)

    return entry, tp, sl, atr, rr, lot_size



class SignalHistory:
    def __init__(self, max_history: int = 50):
        self.signals: List[Dict] = []
        self.max_history = max_history

    def add(self, direction: str, corr: float, confidence: int,
            entry: float, tp: float, sl: float, rr: float) -> None:
        self.signals.append({
            "time": datetime.now().isoformat(), "direction": direction,
            "corr": corr, "confidence": confidence,
            "entry": entry, "tp": tp, "sl": sl, "rr": rr, "result": "OPEN",
        })
        if len(self.signals) > self.max_history:
            self.signals = self.signals[-self.max_history:]

    def get_winrate(self) -> float:
        closed = [s for s in self.signals if s["result"] in ("WIN", "LOSS")]
        if len(closed) < 3:
            return 0.0
        return round(sum(1 for s in closed if s["result"] == "WIN") / len(closed) * 100, 1)

    def get_stats(self) -> Dict:
        closed = [s for s in self.signals if s["result"] in ("WIN", "LOSS")]
        wins   = sum(1 for s in closed if s["result"] == "WIN")
        return {"winrate": self.get_winrate(), "wins": wins,
                "losses": len(closed) - wins, "total": len(self.signals)}

    def to_list(self) -> List[Dict]:
        return self.signals.copy()


history = SignalHistory()

# ─────────────────────────────────────────────────────────────────────────────
#  CONNEXION MT5
# ─────────────────────────────────────────────────────────────────────────────

gold_symbol:   Optional[str] = None
dxy_symbol:    Optional[str] = None
mt5_connected: bool          = False


def connect_mt5() -> bool:
    global gold_symbol, dxy_symbol, mt5_connected
    if not MT5_AVAILABLE:
        log.warning("MT5 non disponible — mode simulation")
        gold_symbol = "XAUUSD"; dxy_symbol = "DXY"; mt5_connected = False
        return False
    if not mt5.initialize():
        log.error(f"Connexion MT5 échouée: {mt5.last_error()}")
        mt5_connected = False; return False
    info = mt5.account_info()
    if info:
        log.info(f"MT5 connecté | Compte: {info.login} | Broker: {info.company}")
    available   = {s.name for s in mt5.symbols_get()}
    gold_symbol = _find_symbol(GOLD_SYMBOLS, available, "GOLD")
    dxy_symbol  = _find_symbol(DXY_SYMBOLS,  available, "DXY")
    if not gold_symbol:
        log.error("Symbole GOLD introuvable!"); mt5_connected = False; return False
    if not dxy_symbol:
        log.warning(f"DXY introuvable. Disponibles: {sorted(available)[:15]}")
        mt5_connected = False; return False
    mt5_connected = True
    log.info(f"Symboles: Gold={gold_symbol} | DXY={dxy_symbol}")
    return True


def _find_symbol(candidates: List[str], available: set, label: str) -> Optional[str]:
    for s in candidates:
        if s in available:
            log.info(f"Symbole {label}: {s}"); return s
    for s in available:
        for c in candidates:
            if c.upper() in s.upper():
                log.info(f"Symbole {label} (partiel): {s}"); return s
    return None

# ─────────────────────────────────────────────────────────────────────────────
#  SIMULATION CORRÉLÉE
# ─────────────────────────────────────────────────────────────────────────────

def _simulate_correlated(n: int, tf_minutes: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    now   = datetime.now()
    times = pd.date_range(end=now, periods=n, freq=f"{tf_minutes}min")
    rng   = np.random.default_rng(int(time.time()) // (tf_minutes * 30))
    common = np.cumsum(rng.normal(0, 1, n))
    gold_close = 2320.0 + (common * 1.2 + np.cumsum(rng.normal(0, 0.4, n))) * 0.8
    dxy_close  = 104.5  + (-common * 0.6 + np.cumsum(rng.normal(0, 0.4, n))) * 0.15
    gold_close -= gold_close[0] - 2320.0
    dxy_close  -= dxy_close[0]  - 104.5

    def _build(closes, vol):
        opens  = np.roll(closes, 1); opens[0] = closes[0]
        spread = np.abs(rng.normal(0, vol, n)) * 0.5 + vol * 0.3
        return pd.DataFrame({
            "open":  np.round(opens, 4),
            "high":  np.round(np.maximum(opens, closes) + spread, 4),
            "low":   np.round(np.minimum(opens, closes) - spread, 4),
            "close": np.round(closes, 4),
            "tick_volume": rng.exponential(2000, n).astype(int),
        }, index=times)

    return _build(gold_close, 0.5), _build(dxy_close, 0.02)

# ─────────────────────────────────────────────────────────────────────────────
#  DONNÉES MT5
# ─────────────────────────────────────────────────────────────────────────────

def get_ohlc(symbol: str, tf_mt5, n_bars: int) -> Optional[pd.DataFrame]:
    if not MT5_AVAILABLE or not mt5_connected:
        return None
    try:
        rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, n_bars)
        if rates is None or len(rates) == 0:
            log.warning(f"Pas de données MT5: {symbol}"); return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df = df[["open", "high", "low", "close", "tick_volume"]].copy()
        # Exness XAUUSDm : prix réel ~4613 (pas de normalisation nécessaire)
        return df
    except Exception as e:
        log.error(f"Erreur get_ohlc {symbol}: {e}"); return None

# ─────────────────────────────────────────────────────────────────────────────
#  CALCULS TECHNIQUES
# ─────────────────────────────────────────────────────────────────────────────

def compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> float:
    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift()).abs()
    lc  = (df["low"]  - df["close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(float(atr), 4) if not np.isnan(atr) else 10.0


def rolling_corr(s1: pd.Series, s2: pd.Series, w: int) -> pd.Series:
    s1a, s2a = s1.align(s2, join="inner")
    return s1a.rolling(w).corr(s2a)


def get_trend(df: pd.DataFrame, n: int = 5) -> Tuple[str, float, float]:
    if df is None or len(df) < n + 1:
        return "→ Stable", 0.0, 0.0
    last  = float(df["close"].iloc[-1])
    first = float(df["close"].iloc[-n])
    pct   = ((last - first) / first) * 100 if first != 0 else 0.0
    trend = "↑ Hausse" if pct > 0.03 else ("↓ Baisse" if pct < -0.03 else "→ Stable")
    return trend, round(pct, 4), round(last, 4)


def compute_confidence(corr_curr: float, corr_prev: float,
                       atr: float, move: float, dxy_pct: float) -> int:
    corr_score      = min(40, int(abs(corr_curr) * 40)) if corr_curr < 0 else 0
    stability_score = max(0, int(30 - abs(corr_curr - corr_prev) * 60))
    dxy_score       = min(30, int(abs(dxy_pct) * 600))
    return min(100, corr_score + stability_score + dxy_score)


def compute_tp_sl(direction: str, gold_df: pd.DataFrame,
                  atr: Optional[float] = None) -> Tuple[float, float, float, float, float]:
    if atr is None:
        atr = compute_atr(gold_df)
    entry   = round(float(gold_df["close"].iloc[-1]), 2)
    tp_dist = round(atr * TP_ATR_MULT, 2)
    sl_dist = round(atr * SL_ATR_MULT, 2)
    tp = round(entry + tp_dist, 2) if direction == "BUY" else round(entry - tp_dist, 2)
    sl = round(entry - sl_dist, 2) if direction == "BUY" else round(entry + sl_dist, 2)
    rr = round(tp_dist / sl_dist, 2) if sl_dist > 0 else 0.0
    return entry, tp, sl, atr, rr

# ─────────────────────────────────────────────────────────────────────────────
#  ANALYSE PAR TIMEFRAME
# ─────────────────────────────────────────────────────────────────────────────

def analyze_tf(tf_name: str, tf_mt5, n_bars: int,
               gold_df_ext: Optional[pd.DataFrame] = None,
               dxy_df_ext:  Optional[pd.DataFrame] = None) -> Optional[Dict]:

    gold_df = gold_df_ext if gold_df_ext is not None else get_ohlc(gold_symbol, tf_mt5, n_bars)
    dxy_df  = dxy_df_ext  if dxy_df_ext  is not None else get_ohlc(dxy_symbol,  tf_mt5, n_bars)

    if gold_df is None or dxy_df is None:
        log.warning(f"[{tf_name}] Données manquantes"); return None

    min_bars = CORR_WINDOW + 10
    if len(gold_df) < min_bars or len(dxy_df) < min_bars:
        log.warning(f"[{tf_name}] Pas assez de bougies: Gold={len(gold_df)} DXY={len(dxy_df)}")
        return None

    corr_series = rolling_corr(gold_df["close"], dxy_df["close"], CORR_WINDOW).dropna()
    if len(corr_series) < 5:
        log.warning(f"[{tf_name}] Corrélation incalculable"); return None

    corr_curr = float(corr_series.iloc[-1])
    corr_prev = float(corr_series.iloc[-min(6, len(corr_series))])

    gold_trend, gold_pct, gold_price = get_trend(gold_df, 5)
    dxy_trend,  dxy_pct,  dxy_price  = get_trend(dxy_df,  5)
    atr = compute_atr(gold_df)

    log.info(f"[{tf_name}] Corr={corr_curr:+.3f} | Gold={gold_trend} {gold_pct:+.3f}% | DXY={dxy_trend} {dxy_pct:+.4f}%")

    # Seuil corrélation
    thresh = CORR_SIGNAL_THRESH if tf_name == "H1" else CORR_CONFIRM_THRESH
    if corr_curr >= thresh:
        log.info(f"[{tf_name}] Corrélation insuffisante ({corr_curr:+.3f} >= {thresh})")
        return None

    # Mouvement DXY (seuil réduit pour DXYm)
    dxy_up = dxy_pct >  0.010
    dxy_dn = dxy_pct < -0.010
    if not dxy_up and not dxy_dn:
        log.info(f"[{tf_name}] DXY trop stable ({dxy_pct:+.4f}%) — pas de signal")
        return None

    direction = "SELL" if dxy_up else "BUY"

    # Cohérence Gold (tolérance élargie)
    gold_aligned = (
        (direction == "BUY"  and gold_pct > -0.05) or
        (direction == "SELL" and gold_pct <  0.05)
    )
    if not gold_aligned:
        log.info(f"[{tf_name}] Or incohérent ({direction}, gold_pct={gold_pct:+.3f}%)")
        return None

    # Mouvement minimum (réduit à 0.2×ATR)
    move = abs(float(gold_df["close"].iloc[-1]) - float(gold_df["close"].iloc[-6]))
    if move < atr * 0.2:
        log.info(f"[{tf_name}] Mouvement Or trop faible ({move:.2f} vs ATR×0.2={atr*0.2:.2f})")
        return None

    confidence = compute_confidence(corr_curr, corr_prev, atr, move, dxy_pct)
    min_conf   = 35 if tf_name == "H1" else 45
    if confidence < min_conf:
        log.info(f"[{tf_name}] Confidence trop faible ({confidence}% < {min_conf}%)")
        return None

    log.info(f"[{tf_name}] ✅ SIGNAL {direction} | Conf={confidence}% | Corr={corr_curr:+.3f}")
    return {
        "tf": tf_name, "direction": direction,
        "corr_curr": round(corr_curr, 4), "corr_prev": round(corr_prev, 4),
        "gold_trend": gold_trend, "gold_pct": gold_pct, "gold_price": gold_price,
        "dxy_trend":  dxy_trend,  "dxy_pct":  dxy_pct,  "dxy_price":  dxy_price,
        "atr": atr, "confidence": confidence,
        "gold_df": gold_df,  # local uniquement — jamais envoyé en JSON
        "dxy_df":  dxy_df,
    }

# ─────────────────────────────────────────────────────────────────────────────
#  PUSH API
# ─────────────────────────────────────────────────────────────────────────────

def _df_to_ohlcv(df: Optional[pd.DataFrame], limit: int = 200) -> List[Dict]:
    if df is None or df.empty:
        return []
    out = []
    for idx, row in df.tail(limit).iterrows():
        out.append({
            "time":   idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
            "open":   round(float(row["open"]),  5),
            "high":   round(float(row["high"]),  5),
            "low":    round(float(row["low"]),   5),
            "close":  round(float(row["close"]), 5),
            "volume": int(row.get("tick_volume", 0)),
        })
    return out


def push_snapshot(pipeline_state: str,
                  gold_dfs: Dict[str, Optional[pd.DataFrame]],
                  dxy_dfs:  Dict[str, Optional[pd.DataFrame]],
                  current_signal: Optional[Dict] = None,
                  mtf_results:    Optional[Dict]  = None) -> None:

    gm5 = gold_dfs.get("M5"); dm5 = dxy_dfs.get("M5")
    # Prix déjà normalisés par get_ohlc (÷2 si Exness cents) — pas de double correction
    gold_price = round(float(gm5["close"].iloc[-1]), 2) if gm5 is not None and not gm5.empty else 0.0
    gold_prev  = round(float(gm5["close"].iloc[-2]), 2) if gm5 is not None and len(gm5) > 1 else gold_price
    dxy_price  = round(float(dm5["close"].iloc[-1]), 3) if dm5 is not None and not dm5.empty else 0.0
    gold_change = round(gold_price - gold_prev, 2)
    gold_pct    = round((gold_change / gold_prev) * 100, 3) if gold_prev else 0.0
    dxy_prev    = float(dm5["close"].iloc[-2]) if dm5 is not None and len(dm5) > 1 else dxy_price
    dxy_change  = round(dxy_price - dxy_prev, 4)

    corr_curr = 0.0
    if gm5 is not None and dm5 is not None and len(gm5) >= CORR_WINDOW:
        s = rolling_corr(gm5["close"], dm5["close"], CORR_WINDOW).dropna()
        if not s.empty:
            corr_curr = round(float(s.iloc[-1]), 4)

    sig: Dict = {
        "direction": "WAIT", "anticipation": None, "confidence": 0,
        "corr": corr_curr, "gold_price": gold_price, "dxy_price": dxy_price,
        "entry": 0.0, "tp": 0.0, "sl": 0.0, "rr": 0.0,
        "sl_source": "—", "pipeline_state": pipeline_state,
    }
    if current_signal:
        sig.update({
            "direction":  current_signal.get("direction",  "WAIT"),
            "confidence": current_signal.get("confidence", 0),
            "corr":       current_signal.get("corr_curr",  corr_curr),
            "entry":      current_signal.get("entry",  0.0),
            "tp":         current_signal.get("tp",     0.0),
            "sl":         current_signal.get("sl",     0.0),
            "rr":         current_signal.get("rr",     0.0),
            "sl_source":  current_signal.get("sl_source", "ATR"),
        })

    mtf: Dict = {}
    if mtf_results:
        for tf_n, res in mtf_results.items():
            mtf[tf_n] = {
                "signal":       res.get("direction", "WAIT") if res else "WAIT",
                "corr":         res.get("corr_curr", 0.0)    if res else 0.0,
                "trend":        res.get("gold_trend", "—")   if res else "—",
                "anticipation": None,
            }

    stats = history.get_stats()
    payload = {
        "gold_price":    gold_price,
        "dxy_price":     dxy_price,
        "gold_bid":      round(gold_price - 0.15, 2),
        "gold_ask":      round(gold_price + 0.15, 2),
        "gold_change":   gold_change,
        "gold_pct":      gold_pct,
        "dxy_change":    dxy_change,
        "correlation":   corr_curr,
        "signal":        sig,
        "mtf":           mtf,
        "ohlcv":         {tf_n: _df_to_ohlcv(gold_dfs.get(tf_n), 200) for tf_n in ["M5","M15","H1"]},
        "signals":       history.to_list(),
        "winrate":       stats["winrate"],
        "wins":          stats["wins"],
        "losses":        stats["losses"],
        "bot_status":    "running",
        "mt5_connected": mt5_connected,
        "gold_symbol":   gold_symbol or "XAUUSD",
        "last_update":   datetime.now().isoformat(),
    }

    try:
        r = requests.post(f"{API_URL}/api/snapshot/push",
                          json=payload, headers=API_HEADERS, timeout=4)
        if r.status_code == 200:
            log.info(f"Snapshot pushé ✅ | Gold={payload['gold_price']} Corr={payload['correlation']:+.3f}")
        else:
            log.warning(f"Snapshot push status: {r.status_code} | {r.text[:100]}")
    except requests.exceptions.ConnectionError as e:
        log.warning(f"API non joignable: {API_URL} — {e}")
    except Exception as e:
        log.warning(f"Snapshot push erreur: {e}")


def push_signal_to_api(direction: str, tf: str, entry: float, tp: float,
                        sl: float, rr: float, sl_source: str,
                        corr: float, confidence: int) -> None:
    try:
        r = requests.post(f"{API_URL}/api/signal/push", headers=API_HEADERS, timeout=4,
                          json={"direction": direction, "tf": tf, "entry": entry,
                                "tp": tp, "sl": sl, "rr": rr, "sl_source": sl_source,
                                "corr": corr, "confidence": confidence,
                                "result": "OPEN", "time": datetime.now().isoformat()})
        if r.status_code == 200:
            log.info("Signal pushé à l'API ✅")
        else:
            log.warning(f"Signal push status: {r.status_code}")
    except Exception as e:
        log.warning(f"Signal push échoué: {e}")

# ─────────────────────────────────────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

def send_telegram(text: str) -> bool:
    if TELEGRAM_TOKEN == "VOTRE_TOKEN_ICI":
        import re
        print("\n" + "═"*55)
        print(re.sub(r"<[^>]+>", "", text))
        print("═"*55 + "\n")
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10)
        ok = resp.status_code == 200
        if ok:
            log.info("✅ Telegram envoyé")
        else:
            log.error(f"Telegram erreur {resp.status_code}: {resp.text[:100]}")
        return ok
    except Exception as e:
        log.error(f"Telegram exception: {e}"); return False


def _stars(c: int) -> str:
    return "⭐⭐⭐" if c >= 75 else ("⭐⭐" if c >= 55 else "⭐")


def msg_startup() -> str:
    now  = datetime.now().strftime("%d/%m/%Y à %H:%M")
    mode = "🧠 SL intelligent (risk.py)" if SMART_RISK else "📐 SL ATR basique"
    return (
        f"🚀 <b>Gold/DXY Signal Bot — Démarré</b>\n"
        f"{'─'*32}\n"
        f"📌 <b>Actifs :</b>\n"
        f"   • Or  : <b>{gold_symbol}</b>\n"
        f"   • DXY : <b>{dxy_symbol}</b>\n\n"
        f"📊 Stratégie : Corrélation négative persistante GOLD/DXY\n"
        f"🕐 Pipeline  : H1 → M15 → M5\n"
        f"🔄 Scan      : toutes les <b>{LOOP_INTERVAL_SEC}s</b>\n"
        f"⚙️ SL Mode   : {mode}\n\n"
        f"⚙️ <b>Seuils :</b>\n"
        f"   H1      : corr &lt; {CORR_SIGNAL_THRESH}\n"
        f"   M15/M5  : corr &lt; {CORR_CONFIRM_THRESH}\n"
        f"   Cooldown : {SIGNAL_COOLDOWN_SEC//60}min\n"
        f"{'─'*32}\n"
        f"⏰ {now} | MT5 : {'✅ Live' if mt5_connected else '🟡 Simulation'}\n"
        f"<i>En attente des signaux...</i>"
    )


def msg_h1_signal(sig: Dict, winrate: float) -> str:
    d      = sig["direction"]
    reason = "DXY↑ → Dollar fort → pression baissière or" if d == "SELL" else "DXY↓ → Dollar faible → or attractif"
    return (
        f"{'📉' if d=='SELL' else '📈'} <b>{'🔴 SELL' if d=='SELL' else '🟢 BUY'} GOLD</b> — Alerte H1\n"
        f"{'─'*30}\n"
        f"📊 Corr : <code>{sig['corr_prev']:+.3f} → {sig['corr_curr']:+.3f}</code>\n"
        f"📈 Gold : {sig['gold_trend']} ({sig['gold_pct']:+.2f}%) @ <b>{sig['gold_price']}</b>\n"
        f"💵 DXY  : {sig['dxy_trend']} ({sig['dxy_pct']:+.4f}%) @ {sig['dxy_price']}\n"
        f"🔥 Confiance : <b>{sig['confidence']}%</b> {_stars(sig['confidence'])}\n"
        f"💡 {reason}\n"
        f"{'─'*30}\n"
        f"⏳ <b>Attente confirmation M15...</b>\n"
        f"⏰ {datetime.now().strftime('%H:%M')} | H1"
    )


def msg_m15_confirmation(sig: Dict, winrate: float) -> str:
    d = sig["direction"]
    return (
        f"✅ <b>Confirmation M15 — {'🔴 SELL' if d=='SELL' else '🟢 BUY'} GOLD</b>\n"
        f"{'─'*30}\n"
        f"📊 Corr M15 : <code>{sig['corr_prev']:+.3f} → {sig['corr_curr']:+.3f}</code>\n"
        f"📈 Gold : {sig['gold_trend']} ({sig['gold_pct']:+.2f}%)\n"
        f"💵 DXY  : {sig['dxy_trend']} ({sig['dxy_pct']:+.4f}%)\n"
        f"🔥 Confiance : <b>{sig['confidence']}%</b>\n"
        f"{'─'*30}\n"
        f"⏳ <b>Attente confirmation M5 pour entrée...</b>\n"
        f"⏰ {datetime.now().strftime('%H:%M')} | M15"
    )


def msg_m5_entry(sig: Dict, entry: float, tp: float, sl: float,
                 rr: float, sl_source: str, winrate: float) -> str:
    d = sig["direction"]
    return (
        f"{'📉' if d=='SELL' else '📈'} <b>ENTRÉE {'🔴 SELL' if d=='SELL' else '🟢 BUY'} GOLD — M5 Confirmé</b>\n"
        f"{'═'*30}\n"
        f"🎯 <b>SETUP COMPLET H1 + M15 + M5</b>\n\n"
        f"💰 <b>Niveaux :</b>\n"
        f"   Entrée : <b>{entry}</b>\n"
        f"   TP     : <b>{tp}</b> 🟢\n"
        f"   SL     : <b>{sl}</b> 🔴\n"
        f"   R/R    : <b>1:{rr}</b>\n"
        f"   SL src : {sl_source}\n\n"
        f"📊 Corr M5 : <code>{sig['corr_prev']:+.3f} → {sig['corr_curr']:+.3f}</code>\n"
        f"📈 Gold : {sig['gold_trend']} | DXY : {sig['dxy_trend']}\n"
        f"🔥 Confiance : <b>{sig['confidence']}%</b> {_stars(sig['confidence'])}\n"
        f"📈 Winrate : {winrate}%\n"
        f"{'═'*30}\n"
        f"⏰ {datetime.now().strftime('%H:%M')}\n"
        f"<i>⚡ Signal algo — pas un conseil financier</i>"
    )

# ─────────────────────────────────────────────────────────────────────────────
#  PIPELINE H1 → M15 → M5
# ─────────────────────────────────────────────────────────────────────────────

class SignalPipeline:
    def __init__(self):
        self.state               = "IDLE"
        self.direction: Optional[str]   = None
        self.h1_signal: Optional[Dict]  = None
        self.m15_signal: Optional[Dict] = None
        self.h1_at: Optional[datetime]  = None
        self.m15_at: Optional[datetime] = None
        self.last_full_sig: Dict[str, datetime] = {}
        self.cycle = 0
        self.current_entry_signal: Optional[Dict] = None

    def reset(self, reason: str = "") -> None:
        if reason: log.info(f"Pipeline reset → IDLE ({reason})")
        self.state = "IDLE"; self.direction = None
        self.h1_signal = None; self.m15_signal = None
        self.h1_at = None; self.m15_at = None
        self.current_entry_signal = None

    def _timeout_check(self) -> bool:
        now = datetime.now()
        if self.state == "WAIT_M15" and self.h1_at:
            if (now - self.h1_at).total_seconds() > H1_TO_M15_TIMEOUT_MIN * 60:
                self.reset(f"H1→M15 timeout ({H1_TO_M15_TIMEOUT_MIN}min)"); return True
        if self.state == "WAIT_M5" and self.m15_at:
            if (now - self.m15_at).total_seconds() > M15_TO_M5_TIMEOUT_MIN * 60:
                self.reset(f"M15→M5 timeout ({M15_TO_M5_TIMEOUT_MIN}min)"); return True
        return False

    def _is_cooldown(self, direction: str) -> bool:
        if direction in self.last_full_sig:
            elapsed = (datetime.now() - self.last_full_sig[direction]).total_seconds()
            if elapsed < SIGNAL_COOLDOWN_SEC:
                log.info(f"Cooldown {direction}: {int((SIGNAL_COOLDOWN_SEC-elapsed)/60)}min restantes")
                return True
        return False

    @staticmethod
    def _elapsed(since: Optional[datetime]) -> int:
        return 0 if since is None else int((datetime.now() - since).total_seconds() / 60)

    def get_dashboard_signal(self) -> Optional[Dict]:
        """Signal intermédiaire pour le dashboard selon l'état du pipeline."""
        if self.state == "IDLE":
            return None
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
                m5: Optional[Dict]) -> Optional[Dict]:
        self.cycle += 1
        if self._timeout_check(): return None
        winrate = history.get_winrate()

        if self.state == "IDLE":
            if h1 is None: log.info("Pas de signal H1"); return None
            if self._is_cooldown(h1["direction"]): return None
            log.info(f"🔔 H1 {h1['direction']} | Conf={h1['confidence']}% | Corr={h1['corr_curr']:+.3f}")
            send_telegram(msg_h1_signal(h1, winrate))
            self.state = "WAIT_M15"; self.direction = h1["direction"]
            self.h1_signal = h1; self.h1_at = datetime.now()
            return None

        elif self.state == "WAIT_M15":
            if m15 is None:
                log.info(f"Attente M15 pour {self.direction}... ({self._elapsed(self.h1_at)}min)")
                return None
            if m15["direction"] != self.direction:
                self.reset(f"M15 contradictoire ({m15['direction']} vs {self.direction})"); return None
            log.info(f"✅ M15 confirmé {self.direction} | Conf={m15['confidence']}%")
            send_telegram(msg_m15_confirmation(m15, winrate))
            self.state = "WAIT_M5"; self.m15_signal = m15; self.m15_at = datetime.now()
            return None

        elif self.state == "WAIT_M5":
            if m5 is None:
                log.info(f"Attente M5 pour {self.direction}... ({self._elapsed(self.m15_at)}min)")
                return None
            if m5["direction"] != self.direction:
                self.reset(f"M5 contradictoire ({m5['direction']} vs {self.direction})"); return None

            gold_df = m5.get("gold_df")
            if SMART_RISK and gold_df is not None:
                try:
                    entry, tp, sl, atr, rr, sl_source = _smart_sl_tp(m5["direction"], gold_df)
                except Exception as e:
                    log.warning(f"smart_sl_tp échoué: {e} — fallback ATR")
                    entry, tp, sl, atr, rr = compute_tp_sl(m5["direction"], gold_df)
                    sl_source = "ATR"
            else:
                entry, tp, sl, atr, rr = compute_tp_sl(m5["direction"], gold_df) if gold_df is not None else (0,0,0,0,0)
                sl_source = "ATR"

            confidence = m5.get("confidence", 0)
            log.info(f"✅ M5 {self.direction} | Entry={entry} TP={tp} SL={sl} R/R=1:{rr}")
            send_telegram(msg_m5_entry(m5, entry, tp, sl, rr, sl_source, winrate))

            history.add(direction=self.direction, corr=m5["corr_curr"],
                        confidence=confidence, entry=entry, tp=tp, sl=sl, rr=rr)
            push_signal_to_api(direction=self.direction, tf="M5",
                               entry=entry, tp=tp, sl=sl, rr=rr,
                               sl_source=sl_source, corr=m5["corr_curr"],
                               confidence=confidence)

            entry_signal = {"direction": self.direction, "confidence": confidence,
                            "corr_curr": m5["corr_curr"], "entry": entry,
                            "tp": tp, "sl": sl, "rr": rr, "sl_source": sl_source}
            self.current_entry_signal = entry_signal
            self.last_full_sig[self.direction] = datetime.now()
            self.reset("signal complet envoyé")
            return entry_signal

        return None

# ─────────────────────────────────────────────────────────────────────────────
#  BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("  GOLD / DXY SIGNAL SYSTEM v2.1 — DÉMARRAGE")
    log.info(f"  SL Mode : {'INTELLIGENT (risk.py)' if SMART_RISK else 'ATR basique'}")
    log.info(f"  MT5     : {'disponible' if MT5_AVAILABLE else 'non disponible → simulation'}")
    log.info(f"  API     : {API_URL}")
    log.info("=" * 60)

    mt5_ok = connect_mt5()
    if MT5_AVAILABLE and not mt5_ok:
        log.error("Impossible de connecter MT5. Assurez-vous que MT5 est ouvert.")
        return

    TF_MAP = {"H1": None, "M15": None, "M5": None}
    if MT5_AVAILABLE and mt5_ok:
        TF_MAP = {"H1": mt5.TIMEFRAME_H1, "M15": mt5.TIMEFRAME_M15, "M5": mt5.TIMEFRAME_M5}

    # ── Message Telegram démarrage ────────────────────────────────────────────
    log.info("Envoi message Telegram de démarrage...")
    send_telegram(msg_startup())

    pipeline = SignalPipeline()
    gold_dfs: Dict[str, Optional[pd.DataFrame]] = {"M5": None, "M15": None, "H1": None}
    dxy_dfs:  Dict[str, Optional[pd.DataFrame]] = {"M5": None, "M15": None, "H1": None}

    log.info(f"Boucle démarrée — prix toutes les {PRICE_REFRESH_SEC}s | signaux toutes les {SIGNAL_SCAN_SEC}s | Ctrl+C pour arrêter\n")

    last_signal_scan = 0.0  # timestamp dernier scan signaux

    try:
        while True:
            t0  = time.time()
            now = t0

            try:
                # ── Récupération prix tick (toutes les 5s) ────────────────────
                if mt5_ok:
                    # Récupère seulement M5 pour le prix rapide
                    gold_dfs["M5"] = get_ohlc(gold_symbol, TF_MAP["M5"], 200)
                    dxy_dfs["M5"]  = get_ohlc(dxy_symbol,  TF_MAP["M5"], 200)
                else:
                    gold_dfs["M5"], dxy_dfs["M5"] = _simulate_correlated(200, 5)

                # ── Scan signaux (toutes les 60s) ─────────────────────────────
                do_scan = (now - last_signal_scan) >= SIGNAL_SCAN_SEC
                if do_scan:
                    log.info(f"─── Scan signaux #{pipeline.cycle + 1} | {datetime.now().strftime('%H:%M:%S')} ───")
                    if mt5_ok:
                        gold_dfs["H1"]  = get_ohlc(gold_symbol, TF_MAP["H1"],  120)
                        gold_dfs["M15"] = get_ohlc(gold_symbol, TF_MAP["M15"], 150)
                        dxy_dfs["H1"]   = get_ohlc(dxy_symbol,  TF_MAP["H1"],  120)
                        dxy_dfs["M15"]  = get_ohlc(dxy_symbol,  TF_MAP["M15"], 150)
                    else:
                        gold_dfs["H1"],  dxy_dfs["H1"]  = _simulate_correlated(120, 60)
                        gold_dfs["M15"], dxy_dfs["M15"] = _simulate_correlated(150, 15)

                    h1_sig  = analyze_tf("H1",  TF_MAP["H1"],  120, gold_dfs["H1"],  dxy_dfs["H1"])
                    m15_sig = analyze_tf("M15", TF_MAP["M15"], 150, gold_dfs["M15"], dxy_dfs["M15"])
                    m5_sig  = analyze_tf("M5",  TF_MAP["M5"],  200, gold_dfs["M5"],  dxy_dfs["M5"])
                    pipeline.process(h1_sig, m15_sig, m5_sig)
                    last_signal_scan = now
                else:
                    # Réutilise les derniers signaux connus
                    h1_sig = m15_sig = m5_sig = None

                # ── Push snapshot prix vers dashboard (toutes les 5s) ─────────
                push_snapshot(
                    pipeline_state = pipeline.state,
                    gold_dfs       = gold_dfs,
                    dxy_dfs        = dxy_dfs,
                    current_signal = pipeline.get_dashboard_signal(),
                    mtf_results    = {"H1": h1_sig, "M15": m15_sig, "M5": m5_sig} if do_scan else None,
                )

            except Exception as e:
                log.error(f"Erreur cycle: {e}", exc_info=True)

            elapsed = time.time() - t0
            sleep_t = max(0, PRICE_REFRESH_SEC - elapsed)
            time.sleep(sleep_t)

    except KeyboardInterrupt:
        log.info("\n⛔ Arrêt (Ctrl+C)")
    finally:
        if MT5_AVAILABLE and mt5_ok:
            mt5.shutdown()
            log.info("MT5 déconnecté.")
        log.info("Système arrêté.")


if __name__ == "__main__":
    main()
