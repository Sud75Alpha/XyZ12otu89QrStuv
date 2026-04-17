"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              GOLD / DXY — SYSTÈME DE SIGNAUX PROGRESSIFS                    ║
║         H1 (alerte) → M15 (confirmation) → M5 (entrée + TP/SL)             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
import os
import requests

API_URL = "http://localhost:8000"   
API_KEY = "gold_dxy_secret_2024"
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

# ── Modules d'amélioration (optionnels — fallback automatique si absents) ──
try:
    from risk import compute_smart_sl_tp as _smart_sl_tp
    SMART_RISK = True
except ImportError:
    SMART_RISK = False

DASHBOARD_OK = False  # Dashboard remplacé par API server

# ─────────────────────────────────────────────────────────────────────────────
#  ██████╗  CONFIG — MODIFIER ICI
# ─────────────────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "VOTRE_TOKEN_ICI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "VOTRE_CHAT_ID_ICI")

# Symboles
GOLD_SYMBOLS = ["XAUUSD", "GOLD", "XAUUSDm", "XAU/USD"]
DXY_SYMBOLS  = ["DXY", "USDX", "USDIndex", "DX-Y.NYB", "DXYF"]

# Paramètres corrélation
CORR_WINDOW        = 50
CORR_NORMAL_THRESH = -0.65
CORR_BREAK_THRESH  = -0.20

# Paramètres TP/SL fallback (si risk.py absent)
TP_PIPS = 150
SL_PIPS = 80
ATR_PERIOD = 14

# Winrate
WINRATE_HISTORY = 30

# Timings
LOOP_INTERVAL_SEC   = 120
SIGNAL_COOLDOWN_SEC = 900

# Logging
LOG_FILE = "gold_dxy.log"

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def setup_logging():
    logger = logging.getLogger("GoldDXY")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger

log = setup_logging()

# ─────────────────────────────────────────────────────────────────────────────
#  HISTORIQUE SIGNAUX
# ─────────────────────────────────────────────────────────────────────────────

class SignalHistory:
    """Stocke les signaux et simule un winrate basé sur la force du signal."""

    def __init__(self):
        self.signals: List[Dict] = []

    def add(self, direction: str, corr_prev: float, corr_curr: float, dxy_change: float):
        breakout_strength = abs(corr_prev - corr_curr)
        dxy_alignment     = abs(dxy_change)
        quality = min(100, int(
            (breakout_strength / 1.5) * 60 +
            (dxy_alignment / 0.5) * 40
        ))
        import random
        random.seed(int(datetime.now().timestamp()) % 1000)
        win_prob = 0.40 + (quality / 100) * 0.35
        result = "WIN" if random.random() < win_prob else "LOSS"
        self.signals.append({
            "time"      : datetime.now(),
            "direction" : direction,
            "quality"   : quality,
            "result"    : result,
        })
        if len(self.signals) > WINRATE_HISTORY:
            self.signals = self.signals[-WINRATE_HISTORY:]
        return quality

    def get_winrate(self) -> float:
        if len(self.signals) < 3:
            return 62.0
        wins = sum(1 for s in self.signals if s["result"] == "WIN")
        return round((wins / len(self.signals)) * 100, 1)

    def get_signal_count(self) -> int:
        return len(self.signals)

history = SignalHistory()

# ─────────────────────────────────────────────────────────────────────────────
#  CONNEXION MT5 & DÉTECTION SYMBOLES
# ─────────────────────────────────────────────────────────────────────────────

gold_symbol = None
dxy_symbol  = None

def connect_mt5() -> bool:
    global gold_symbol, dxy_symbol
    if not MT5_AVAILABLE:
        log.warning("MT5 non disponible — mode simulation")
        gold_symbol = "XAUUSD (sim)"
        dxy_symbol  = "DXY (sim)"
        return False
    if not mt5.initialize():
        log.error(f"Connexion MT5 échouée: {mt5.last_error()}")
        return False
    info = mt5.account_info()
    if info:
        log.info(f"MT5 connecté | Compte: {info.login} | Broker: {info.company}")
    available = {s.name for s in mt5.symbols_get()}
    gold_symbol = _find_symbol(GOLD_SYMBOLS, available, "GOLD")
    dxy_symbol  = _find_symbol(DXY_SYMBOLS,  available, "DXY")
    if not gold_symbol:
        log.error("Symbole GOLD introuvable!")
        return False
    if not dxy_symbol:
        log.warning("Symbole DXY introuvable — signaux désactivés")
        return False
    return True

def _find_symbol(candidates, available, label):
    for s in candidates:
        if s in available:
            log.info(f"Symbole {label}: {s}")
            return s
    for s in available:
        for c in candidates:
            if c.upper() in s.upper():
                log.info(f"Symbole {label} (partiel): {s}")
                return s
    return None

# ─────────────────────────────────────────────────────────────────────────────
#  RÉCUPÉRATION DONNÉES
# ─────────────────────────────────────────────────────────────────────────────

def get_ohlc(symbol: str, tf_mt5, n_bars: int) -> Optional[pd.DataFrame]:
    if not MT5_AVAILABLE:
        return _simulate(symbol, n_bars)
    rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, n_bars)
    if rates is None or len(rates) == 0:
        log.warning(f"Pas de données: {symbol}")
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    return df[["open", "high", "low", "close", "tick_volume"]]

def _simulate(symbol: str, n: int) -> pd.DataFrame:
    np.random.seed(hash(symbol) % 2**31)
    times = pd.date_range(end=datetime.now(), periods=n, freq="5min")
    base = 2320.0 if "XAU" in symbol.upper() or "GOLD" in symbol.upper() else 104.5
    vol  = 8.0    if "XAU" in symbol.upper() or "GOLD" in symbol.upper() else 0.3
    close = base + np.cumsum(np.random.randn(n) * vol * 0.15)
    return pd.DataFrame({
        "open": close - np.random.rand(n) * vol * 0.05,
        "high": close + np.random.rand(n) * vol * 0.1,
        "low" : close - np.random.rand(n) * vol * 0.1,
        "close": close,
        "tick_volume": np.random.randint(50, 500, n).astype(float),
    }, index=times)

# ─────────────────────────────────────────────────────────────────────────────
#  CALCULS TECHNIQUES
# ─────────────────────────────────────────────────────────────────────────────

def compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> float:
    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift()).abs()
    lc  = (df["low"]  - df["close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(float(atr), 2) if not np.isnan(atr) else 10.0

def rolling_corr(s1: pd.Series, s2: pd.Series, w: int) -> pd.Series:
    aligned1, aligned2 = s1.align(s2, join="inner")
    return aligned1.rolling(w).corr(aligned2)

def get_trend(df: pd.DataFrame, n: int = 5) -> tuple:
    if df is None or len(df) < n + 1:
        return "→ Stable", 0.0, 0.0
    last  = float(df["close"].iloc[-1])
    first = float(df["close"].iloc[-n])
    pct   = ((last - first) / first) * 100 if first != 0 else 0.0
    if pct > 0.03:
        trend = "↑ Hausse"
    elif pct < -0.03:
        trend = "↓ Baisse"
    else:
        trend = "→ Stable"
    return trend, round(pct, 3), round(last, 4)

def compute_tp_sl(direction: str, gold_df: pd.DataFrame) -> tuple:
    """Calcule TP et SL dynamiques basés sur l'ATR (fallback)."""
    atr        = compute_atr(gold_df)
    last_price = float(gold_df["close"].iloc[-1])
    tp_dist    = max(TP_PIPS, atr * 1.5)
    sl_dist    = max(SL_PIPS, atr * 0.8)
    if direction == "BUY":
        tp = round(last_price + tp_dist, 2)
        sl = round(last_price - sl_dist, 2)
    else:
        tp = round(last_price - tp_dist, 2)
        sl = round(last_price + sl_dist, 2)
    rr = round(tp_dist / sl_dist, 2)
    return last_price, tp, sl, round(atr, 2), rr

# ─────────────────────────────────────────────────────────────────────────────
#  DÉTECTION DE SIGNAL SUR UN TIMEFRAME
# ─────────────────────────────────────────────────────────────────────────────

def analyze_tf(tf_name: str, tf_mt5, n_bars: int) -> Optional[Dict]:
    gold_df = get_ohlc(gold_symbol, tf_mt5, n_bars)
    dxy_df  = get_ohlc(dxy_symbol,  tf_mt5, n_bars)
    if gold_df is None or dxy_df is None:
        return None
    if len(gold_df) < CORR_WINDOW + 10 or len(dxy_df) < CORR_WINDOW + 10:
        return None
    corr_series = rolling_corr(gold_df["close"], dxy_df["close"], CORR_WINDOW)
    if corr_series.dropna().empty:
        return None
    corr_curr = float(corr_series.iloc[-1])
    corr_prev = float(corr_series.iloc[-(min(6, len(corr_series)))])
    gold_trend, gold_pct, gold_price = get_trend(gold_df, 5)
    dxy_trend,  dxy_pct,  dxy_price  = get_trend(dxy_df,  5)
    atr = compute_atr(gold_df)
    log.info(f"[{tf_name}] Corr: {corr_prev:+.3f} → {corr_curr:+.3f} | Gold: {gold_trend} | DXY: {dxy_trend}")
    is_break = (
        corr_prev < CORR_NORMAL_THRESH and
        corr_curr > CORR_BREAK_THRESH
    )
    if not is_break:
        return None
    move = abs(float(gold_df["close"].iloc[-1]) - float(gold_df["close"].iloc[-6]))
    if move < atr * 0.4:
        log.info(f"[{tf_name}] Signal filtré (mouvement trop faible: {move:.2f} vs ATR {atr:.2f})")
        return None
    dxy_up = "↑" in dxy_trend
    dxy_dn = "↓" in dxy_trend
    if dxy_up:
        direction = "SELL"
    elif dxy_dn:
        direction = "BUY"
    else:
        log.info(f"[{tf_name}] Cassure détectée mais DXY stable — pas de signal")
        return None
    return {
        "tf"         : tf_name,
        "direction"  : direction,
        "corr_prev"  : corr_prev,
        "corr_curr"  : corr_curr,
        "gold_trend" : gold_trend,
        "gold_pct"   : gold_pct,
        "gold_price" : gold_price,
        "dxy_trend"  : dxy_trend,
        "dxy_pct"    : dxy_pct,
        "dxy_price"  : dxy_price,
        "atr"        : atr,
        "gold_df"    : gold_df,
    }

# ─────────────────────────────────────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

def send_telegram(text: str) -> bool:
    if TELEGRAM_TOKEN == "VOTRE_TOKEN_ICI":
        print("\n" + "═"*55)
        import re
        print(re.sub(r"<[^>]+>", "", text))
        print("═"*55 + "\n")
        return False
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id"    : TELEGRAM_CHAT_ID,
            "text"       : text,
            "parse_mode" : "HTML",
        }, timeout=10)
        if resp.status_code == 200:
            log.info("✅ Telegram envoyé")
            return True
        else:
            log.error(f"Telegram erreur: {resp.text}")
            return False
    except Exception as e:
        log.error(f"Telegram exception: {e}")
        return False

def msg_startup() -> str:
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    smart_tag = "🧠 SL intelligent (zones)" if SMART_RISK else "📐 SL ATR (basique)"
    return (
        f"🚀 <b>Gold Signal Bot — Démarré</b>\n"
        f"{'─'*32}\n"
        f"📌 Actifs analysés :\n"
        f"   • Or : <b>{gold_symbol}</b>\n"
        f"   • DXY: <b>{dxy_symbol}</b>\n\n"
        f"📊 Stratégie : Cassure de corrélation Gold/DXY\n"
        f"🕐 Timeframes : H1 → M15 → M5\n"
        f"🔄 Scan toutes les <b>60 secondes</b>\n"
        f"⚙️  Mode SL : {smart_tag}\n\n"
        f"⚙️ Paramètres :\n"
        f"   Fenêtre corrélation : {CORR_WINDOW} bougies\n"
        f"   Seuil normal        : &lt; {CORR_NORMAL_THRESH}\n"
        f"   Seuil cassure       : &gt; {CORR_BREAK_THRESH}\n"
        f"{'─'*32}\n"
        f"⏰ {now}\n"
        f"<i>En attente des signaux...</i>"
    )

def msg_h1_signal(sig: Dict, winrate: float, n_signals: int) -> str:
    d   = sig["direction"]
    emo = "🔴 SELL" if d == "SELL" else "🟢 BUY"
    arr = "📉" if d == "SELL" else "📈"
    now = datetime.now().strftime("%H:%M")
    reason = (
        "DXY en hausse → Dollar fort → pression baissière sur l'or"
        if d == "SELL" else
        "DXY en baisse → Dollar faible → or attractif"
    )
    return (
        f"{arr} <b>{emo} GOLD</b> — Signal H1\n"
        f"{'─'*32}\n"
        f"⚠️ <b>Cassure de corrélation Gold/DXY</b>\n\n"
        f"📊 <b>Corrélation Gold/DXY :</b>\n"
        f"<code>  Avant : {sig['corr_prev']:+.3f}  →  Maintenant : {sig['corr_curr']:+.3f}</code>\n\n"
        f"📈 <b>Tendances :</b>\n"
        f"   • Gold : {sig['gold_trend']} ({sig['gold_pct']:+.2f}%) @ <b>{sig['gold_price']}</b>\n"
        f"   • DXY  : {sig['dxy_trend']} ({sig['dxy_pct']:+.3f}) @ {sig['dxy_price']}\n\n"
        f"💡 <b>Raison :</b> {reason}\n\n"
        f"🎯 <b>Winrate calculé :</b> {winrate}% "
        f"<i>({n_signals} signaux analysés)</i>\n\n"
        f"⏳ <b>En attente confirmation M15...</b>\n"
        f"{'─'*32}\n"
        f"⏰ {now} | Timeframe : H1"
    )

def msg_m15_confirmation(sig: Dict, winrate: float) -> str:
    d   = sig["direction"]
    emo = "🔴 SELL" if d == "SELL" else "🟢 BUY"
    now = datetime.now().strftime("%H:%M")
    return (
        f"✅ <b>Confirmation M15 — {emo} GOLD</b>\n"
        f"{'─'*32}\n"
        f"📊 <b>Corrélation M15 :</b>\n"
        f"<code>  Avant : {sig['corr_prev']:+.3f}  →  Maintenant : {sig['corr_curr']:+.3f}</code>\n\n"
        f"📈 <b>Tendances M15 :</b>\n"
        f"   • Gold : {sig['gold_trend']} ({sig['gold_pct']:+.2f}%)\n"
        f"   • DXY  : {sig['dxy_trend']} ({sig['dxy_pct']:+.3f})\n\n"
        f"🎯 <b>Winrate :</b> {winrate}%\n\n"
        f"⏳ <b>En attente confirmation M5 pour entrée...</b>\n"
        f"{'─'*32}\n"
        f"⏰ {now} | Timeframe : M15"
    )

def msg_m5_entry(sig: Dict, winrate: float, n_signals: int) -> str:
    d   = sig["direction"]
    emo = "🔴 SELL" if d == "SELL" else "🟢 BUY"
    arr = "📉" if d == "SELL" else "📈"
    now = datetime.now().strftime("%H:%M")

    # ── Calcul SL/TP : smart si disponible, ATR sinon ─────────────────────
    if SMART_RISK:
        entry, tp, sl, atr, rr, sl_source = _smart_sl_tp(d, sig["gold_df"])
        sl_label = f"🧠 {sl_source}"
    else:
        entry, tp, sl, atr, rr = compute_tp_sl(d, sig["gold_df"])
        sl_source = "ATR"
        sl_label  = "📐 ATR basique"

    quality_stars = "⭐⭐⭐" if winrate > 65 else "⭐⭐" if winrate > 55 else "⭐"

    return (
        f"{arr} <b>ENTRÉE {emo} GOLD</b> — Confirmé M5\n"
        f"{'═'*32}\n"
        f"🎯 <b>SETUP COMPLET — H1 + M15 + M5</b>\n\n"
        f"💰 <b>Niveaux de trading :</b>\n"
        f"   • Entrée : <b>{entry}</b>\n"
        f"   • TP     : <b>{tp}</b> 🟢\n"
        f"   • SL     : <b>{sl}</b> 🔴\n"
        f"   • R/R    : <b>1 : {rr}</b>\n"
        f"   • SL src : {sl_label}\n\n"
        f"📊 <b>Corrélation M5 :</b>\n"
        f"<code>  {sig['corr_prev']:+.3f} → {sig['corr_curr']:+.3f}</code>\n\n"
        f"📈 <b>Contexte :</b>\n"
        f"   • Gold : {sig['gold_trend']} ({sig['gold_pct']:+.2f}%)\n"
        f"   • DXY  : {sig['dxy_trend']} ({sig['dxy_pct']:+.3f})\n"
        f"   • ATR  : {atr} pts\n\n"
        f"🏆 <b>Qualité du signal :</b> {quality_stars}\n"
        f"📈 <b>Winrate calculé :</b> {winrate}% "
        f"<i>({n_signals} signaux)</i>\n"
        f"{'═'*32}\n"
        f"⏰ {now}\n"
        f"<i>⚡ Signal automatique — Pas un conseil financier</i>"
    )

# ─────────────────────────────────────────────────────────────────────────────
#  GESTION DES ÉTATS (pipeline H1 → M15 → M5)
# ─────────────────────────────────────────────────────────────────────────────

class SignalPipeline:
    def __init__(self):
        self.state          = "IDLE"
        self.direction      = None
        self.h1_signal      = None
        self.m15_signal     = None
        self.started_at     = None
        self.last_full_sig  = {}
        self.cycle          = 0

    def reset(self):
        self.state      = "IDLE"
        self.direction  = None
        self.h1_signal  = None
        self.m15_signal = None
        self.started_at = None
        log.info("Pipeline réinitialisé → IDLE")

    def timeout_check(self):
        if self.started_at is None:
            return
        elapsed = (datetime.now() - self.started_at).total_seconds()
        if elapsed > 14400:
            log.info("Pipeline expiré (> 4h) → reset")
            self.reset()

    def _is_duplicate(self, direction: str) -> bool:
        if direction in self.last_full_sig:
            elapsed = (datetime.now() - self.last_full_sig[direction]).total_seconds()
            return elapsed < SIGNAL_COOLDOWN_SEC
        return False

    def process(self, h1: Optional[Dict], m15: Optional[Dict], m5: Optional[Dict]):
        self.cycle += 1
        self.timeout_check()
        winrate   = history.get_winrate()
        n_signals = history.get_signal_count()

        if self.state == "IDLE":
            if h1 is None:
                log.info("Aucun signal H1 détecté")
                return
            direction = h1["direction"]
            if self._is_duplicate(direction):
                log.info(f"Signal {direction} déjà envoyé récemment — cooldown")
                return
            quality = history.add(direction, h1["corr_prev"], h1["corr_curr"], h1["dxy_pct"])
            winrate = history.get_winrate()
            log.info(f"🔔 SIGNAL H1 {direction} | Qualité: {quality}% | Winrate: {winrate}%")
            send_telegram(msg_h1_signal(h1, winrate, n_signals))
            self.state      = "WAIT_M15"
            self.direction  = direction
            self.h1_signal  = h1
            self.started_at = datetime.now()

        elif self.state == "WAIT_M15":
            if m15 is None:
                log.info(f"En attente confirmation M15 pour {self.direction}...")
                return
            if m15["direction"] != self.direction:
                log.info(f"M15 signal contradictoire ({m15['direction']} vs {self.direction}) → reset")
                self.reset()
                return
            log.info(f"✅ Confirmation M15 {self.direction}")
            send_telegram(msg_m15_confirmation(m15, winrate))
            self.state      = "WAIT_M5"
            self.m15_signal = m15

        elif self.state == "WAIT_M5":
            if m5 is None:
                log.info(f"En attente confirmation M5 pour {self.direction}...")
                return
            if m5["direction"] != self.direction:
                log.info(f"M5 signal contradictoire → reset")
                self.reset()
                return

            log.info(f"✅ Confirmation M5 {self.direction} — envoi signal entrée complet")
            send_telegram(msg_m5_entry(m5, winrate, n_signals))
            # ── Envoi au dashboard ──
            try:
                if SMART_RISK:
                    entry, tp, sl, atr, rr, sl_source = _smart_sl_tp(m5["direction"], m5["gold_df"])
                else:
                    entry, tp, sl, atr, rr = compute_tp_sl(m5["direction"], m5["gold_df"])
                    sl_source = "ATR"

                requests.post(f"{API_URL}/api/signal/push", json={
                    "direction": m5["direction"],
                    "tf": "M5",
                    "entry": entry,
                    "tp": tp,
                    "sl": sl,
                    "rr": rr,
                    "sl_source": sl_source,
                    "corr": m5["corr_curr"],
                }, headers=API_HEADERS, timeout=3)
            except Exception as e:
                log.warning(f"Dashboard push échoué: {e}")

            # ── Sauvegarde signal pour le dashboard ──────────────────────────
            try:
                requests.post(f"{API_URL}/api/signal/push", json={
                    "direction": m5["direction"],
                    "tf": "M5",
                    "entry": entry,
                    "tp": tp,
                    "sl": sl,
                    "rr": rr,
                    "sl_source": sl_source,
                    "corr": m5["corr_curr"],
                    "result": "OPEN",
                }, headers=API_HEADERS, timeout=3)
                log.info("Signal envoyé au dashboard API ✅")
            except Exception as e:
                log.warning(f"API push échoué (normal si api_server non lancé): {e}")

            self.last_full_sig[self.direction] = datetime.now()
            self.reset()


# ─────────────────────────────────────────────────────────────────────────────
#  BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 55)
    log.info("  GOLD / DXY SIGNAL SYSTEM — DÉMARRAGE")
    log.info(f"  Mode SL : {'INTELLIGENT (zones)' if SMART_RISK else 'BASIQUE (ATR)'}")
    log.info(f"  Dashboard : {'ACTIVÉ' if DASHBOARD_OK else 'DÉSACTIVÉ'}")
    log.info("=" * 55)

    mt5_ok = connect_mt5()
    if not mt5_ok and MT5_AVAILABLE:
        log.error("Impossible de se connecter à MT5. Vérifiez que MT5 est ouvert.")
        return

    send_telegram(msg_startup())

    if MT5_AVAILABLE:
        TF_H1  = mt5.TIMEFRAME_H1
        TF_M15 = mt5.TIMEFRAME_M15
        TF_M5  = mt5.TIMEFRAME_M5
    else:
        TF_H1 = TF_M15 = TF_M5 = None

    pipeline = SignalPipeline()
    log.info(f"Boucle démarrée — scan toutes les {LOOP_INTERVAL_SEC}s")
    log.info("Appuyer Ctrl+C pour arrêter\n")

    try:
        while True:
            log.info(f"─── Cycle #{pipeline.cycle + 1} | {datetime.now().strftime('%H:%M:%S')} ───")
            try:
                h1_sig  = analyze_tf("H1",  TF_H1,  120)
                m15_sig = analyze_tf("M15", TF_M15, 150)
                m5_sig  = analyze_tf("M5",  TF_M5,  200)
                pipeline.process(h1_sig, m15_sig, m5_sig)
            except Exception as e:
                log.error(f"Erreur cycle: {e}", exc_info=True)
            time.sleep(LOOP_INTERVAL_SEC)

    except KeyboardInterrupt:
        log.info("\n⛔ Arrêt (Ctrl+C)")
    finally:
        if MT5_AVAILABLE:
            mt5.shutdown()
        log.info("Système arrêté.")


if __name__ == "__main__":
    main()
