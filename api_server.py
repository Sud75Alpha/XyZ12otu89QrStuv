"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              API SERVER — GOLD/DXY BOT ↔ DASHBOARD BRIDGE                  ║
║   FastAPI · tourne sur ton PC local · envoie les données au dashboard       ║
║                                                                              ║
║   Lancement : python api_server.py                                           ║
║   Écoute sur : http://0.0.0.0:8000                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import logging
import threading
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import deque

# ── FastAPI ───────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# ── MT5 ──────────────────────────────────────────────────────────────────────
MT5_AVAILABLE = False
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────

API_HOST        = "0.0.0.0"
API_PORT        = int(os.getenv("API_PORT", 8000))
API_KEY         = os.getenv("API_KEY", "X9vT$7qLm2#A8pZ_goldDXY_2026")   # Changer en prod

GOLD_SYMBOLS    = ["XAUUSD", "GOLD", "XAUUSDm", "XAU/USD"]
DXY_SYMBOLS     = ["DXY", "USDX", "USDIndex", "DX-Y.NYB", "DXYF"]
CORR_WINDOW     = 50
MAX_LOG_ENTRIES = 200
MAX_SIGNALS     = 100
DATA_REFRESH_S  = 1   # Fréquence actualisation données MT5 en arrière-plan

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("APIServer")

# ─────────────────────────────────────────────────────────────────────────────
#  STATE GLOBAL — partagé entre le bot et le dashboard
# ─────────────────────────────────────────────────────────────────────────────

class GlobalState:
    """Thread-safe store pour toutes les données du bot."""

    def __init__(self):
        self._lock = threading.RLock()

        # Prix live (mis à jour par le thread MT5)
        self.gold_price: float = 0.0
        self.dxy_price:  float = 0.0
        self.gold_bid:   float = 0.0
        self.gold_ask:   float = 0.0
        self.gold_prev:  float = 0.0
        self.dxy_prev:   float = 0.0

        # Corrélation
        self.correlation: float = -0.75
        self.corr_history: List[Dict] = []   # [{time, corr}]

        # Signal courant
        self.current_signal: Dict = {
            "direction": "WAIT",
            "anticipation": None,
            "confidence": 0,
            "corr": -0.75,
            "gold_price": 0.0,
            "dxy_price": 0.0,
            "entry": 0.0,
            "tp": 0.0,
            "sl": 0.0,
            "rr": 0.0,
            "sl_source": "—",
            "pipeline_state": "IDLE",
            "time": datetime.now().isoformat(),
        }

        # Historique signaux (persisté)
        self.signals: List[Dict] = []
        self._load_signals_file()

        # Logs du bot
        self.bot_logs: deque = deque(maxlen=MAX_LOG_ENTRIES)
        self.bot_logs.append(self._log_entry("INFO", "API Server démarré"))

        # OHLCV caches (timeframe → list of candles)
        self.ohlcv: Dict[str, List[Dict]] = {
            "M5": [], "M15": [], "H1": []
        }

        # Multi-timeframe analysis
        self.mtf_analysis: Dict = {
            "H1":  {"signal": "WAIT", "corr": 0.0, "trend": "—"},
            "M15": {"signal": "WAIT", "corr": 0.0, "trend": "—"},
            "M5":  {"signal": "WAIT", "corr": 0.0, "trend": "—"},
        }

        # Perf
        self.winrate:   float = 0.0
        self.wins:      int   = 0
        self.losses:    int   = 0
        self.bot_status: str  = "starting"
        self.mt5_connected: bool = False
        self.gold_symbol: Optional[str] = None
        self.dxy_symbol:  Optional[str] = None
        self.last_update: str = datetime.now().isoformat()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log_entry(self, level: str, msg: str) -> Dict:
        return {"time": datetime.now().strftime("%H:%M:%S"), "level": level, "msg": msg}

    def add_log(self, level: str, msg: str):
        with self._lock:
            self.bot_logs.append(self._log_entry(level, msg))

    def set_signal(self, data: Dict):
        with self._lock:
            self.current_signal = {**self.current_signal, **data,
                                   "time": datetime.now().isoformat()}

    def add_signal_to_history(self, signal: Dict):
        with self._lock:
            signal["id"] = int(time.time() * 1000)
            self.signals.append(signal)
            if len(self.signals) > MAX_SIGNALS:
                self.signals = self.signals[-MAX_SIGNALS:]
            self._save_signals_file()
            self._update_winrate()

    def _update_winrate(self):
        closed = [s for s in self.signals if s.get("result") in ("WIN", "LOSS")]
        if closed:
            self.wins    = sum(1 for s in closed if s["result"] == "WIN")
            self.losses  = sum(1 for s in closed if s["result"] == "LOSS")
            self.winrate = round(self.wins / len(closed) * 100, 1)

    def _load_signals_file(self):
        try:
            if os.path.exists("signals.json"):
                with open("signals.json") as f:
                    self.signals = json.load(f)
                self._update_winrate()
        except Exception:
            self.signals = []

    def _save_signals_file(self):
        try:
            with open("signals.json", "w") as f:
                json.dump(self.signals, f, indent=2, default=str)
        except Exception as e:
            log.warning(f"Save signals error: {e}")

    def snapshot(self) -> Dict:
        """Snapshot complet thread-safe pour l'API."""
        with self._lock:
            return {
                "gold_price":    self.gold_price,
                "dxy_price":     self.dxy_price,
                "gold_bid":      self.gold_bid,
                "gold_ask":      self.gold_ask,
                "gold_change":   round(self.gold_price - self.gold_prev, 2) if self.gold_prev else 0.0,
                "gold_pct":      round((self.gold_price - self.gold_prev) / self.gold_prev * 100, 3) if self.gold_prev else 0.0,
                "dxy_change":    round(self.dxy_price - self.dxy_prev, 4) if self.dxy_prev else 0.0,
                "dxy_pct":       round((self.dxy_price - self.dxy_prev) / self.dxy_prev * 100, 3) if self.dxy_prev else 0.0,
                "correlation":   self.correlation,
                "corr_history":  self.corr_history[-100:],
                "signal":        self.current_signal,
                "signals":       self.signals[-50:],
                "bot_logs":      list(self.bot_logs)[-50:],
                "mtf_analysis":  self.mtf_analysis,
                "winrate":       self.winrate,
                "wins":          self.wins,
                "losses":        self.losses,
                "bot_status":    self.bot_status,
                "mt5_connected": self.mt5_connected,
                "gold_symbol":   self.gold_symbol,
                "dxy_symbol":    self.dxy_symbol,
                "last_update":   self.last_update,
                "server_time":   datetime.now().isoformat(),
            }


STATE = GlobalState()

# ─────────────────────────────────────────────────────────────────────────────
#  MT5 DATA THREAD — actualise les prix en arrière-plan
# ─────────────────────────────────────────────────────────────────────────────

def _find_symbol(candidates, available):
    for s in candidates:
        if s in available:
            return s
    for s in available:
        for c in candidates:
            if c.upper() in s.upper():
                return s
    return None


def _simulate_tick(symbol: str, base_price: float, volatility: float) -> float:
    """Tick simulé si MT5 non disponible."""
    return round(base_price * (1 + np.random.normal(0, volatility)), 5)


def _get_ohlcv_mt5(symbol: str, tf, n: int) -> List[Dict]:
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, n)
    if rates is None or len(rates) == 0:
        return []
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    result = []
    for _, row in df.iterrows():
        result.append({
            "time":   row["time"].isoformat(),
            "open":   round(float(row["open"]),   5),
            "high":   round(float(row["high"]),   5),
            "low":    round(float(row["low"]),    5),
            "close":  round(float(row["close"]),  5),
            "volume": int(row.get("tick_volume", row.get("real_volume", 0))),
        })
    return result


def _simulate_ohlcv(symbol: str, n: int, interval_min: int) -> List[Dict]:
    """OHLCV simulé réaliste."""
    np.random.seed(hash(symbol) % 9999)
    base = 2320.0 if "XAU" in symbol.upper() else 104.5
    vol  = 0.0008 if "XAU" in symbol.upper() else 0.0004
    now  = datetime.now()
    delta = timedelta(minutes=interval_min)
    closes = [base]
    for _ in range(n - 1):
        closes.append(closes[-1] * (1 + np.random.normal(0, vol)))

    # Live jitter sur la dernière bougie
    seed = int(time.time() * 3) % 10000
    np.random.seed(seed)
    closes[-1] *= (1 + np.random.normal(0, vol * 0.3))

    result = []
    for i in range(n):
        t = now - delta * (n - 1 - i)
        o = closes[i - 1] if i > 0 else closes[i]
        c = closes[i]
        rng = abs(c - o) * (1 + abs(np.random.normal(0, 0.5)))
        h = max(o, c) + rng * abs(np.random.normal(0.2, 0.3))
        l = min(o, c) - rng * abs(np.random.normal(0.2, 0.3))
        result.append({
            "time":   t.isoformat(),
            "open":   round(o, 5),
            "high":   round(h, 5),
            "low":    round(max(l, 0.1), 5),
            "close":  round(c, 5),
            "volume": int(np.random.exponential(2000)),
        })
    return result


def _compute_rolling_corr(gold_closes: List[float], dxy_closes: List[float],
                           window: int = CORR_WINDOW) -> float:
    n = min(len(gold_closes), len(dxy_closes), window)
    if n < 5:
        return -0.75
    g = np.array(gold_closes[-n:])
    d = np.array(dxy_closes[-n:])
    if np.std(g) == 0 or np.std(d) == 0:
        return 0.0
    return float(np.corrcoef(g, d)[0, 1])


def _compute_signal(gold_closes: List[float], dxy_closes: List[float],
                    corr: float) -> Dict:
    """Logique de signal + anticipation."""
    if len(gold_closes) < 3 or len(dxy_closes) < 3:
        return {"direction": "WAIT", "anticipation": None, "confidence": 0}

    gold_up  = gold_closes[-1] > gold_closes[-2]
    dxy_down = dxy_closes[-1]  < dxy_closes[-2]
    dxy_up   = dxy_closes[-1]  > dxy_closes[-2]

    direction    = "WAIT"
    anticipation = None
    confidence   = 0

    # Signal confirmé
    if corr < -0.60:
        if gold_up and dxy_down:
            direction  = "BUY"
            confidence = min(100, int(abs(corr) * 100))
        elif not gold_up and dxy_up:
            direction  = "SELL"
            confidence = min(100, int(abs(corr) * 100))

    # Mode anticipation (DXY seul)
    dxy_move = abs(dxy_closes[-1] - dxy_closes[-3]) / (abs(dxy_closes[-3]) + 1e-9)
    if direction == "WAIT" and dxy_move > 0.0002:
        if dxy_down:
            anticipation = "ANTICIPATION BUY GOLD"
        elif dxy_up:
            anticipation = "ANTICIPATION SELL GOLD"

    return {
        "direction":    direction,
        "anticipation": anticipation,
        "confidence":   confidence,
    }


def _get_trend_label(closes: List[float], n: int = 5) -> str:
    if len(closes) < n + 1:
        return "→ Stable"
    pct = (closes[-1] - closes[-n]) / (closes[-n] + 1e-9) * 100
    if pct > 0.05:  return "↑ Hausse"
    if pct < -0.05: return "↓ Baisse"
    return "→ Stable"


def mt5_data_thread():
    """Thread principal : actualise toutes les données à DATA_REFRESH_S secondes."""
    global STATE

    # ── Connexion MT5 ──────────────────────────────────────────────────────────
    if MT5_AVAILABLE:
        ok = mt5.initialize()
        if ok:
            available   = {s.name for s in mt5.symbols_get()}
            gold_sym    = _find_symbol(GOLD_SYMBOLS, available)
            dxy_sym     = _find_symbol(DXY_SYMBOLS, available)
            STATE.gold_symbol    = gold_sym
            STATE.dxy_symbol     = dxy_sym
            STATE.mt5_connected  = True
            STATE.bot_status     = "running"
            STATE.add_log("INFO", f"MT5 connecté | Gold: {gold_sym} | DXY: {dxy_sym}")
            log.info(f"MT5 OK | Gold: {gold_sym} | DXY: {dxy_sym}")
        else:
            STATE.mt5_connected = False
            STATE.bot_status    = "simulation"
            STATE.add_log("WARNING", "MT5 introuvable — mode simulation")
            log.warning("MT5 non connecté — simulation")
    else:
        STATE.bot_status    = "simulation"
        STATE.mt5_connected = False
        STATE.add_log("WARNING", "MetaTrader5 non installé — simulation complète")

    # Bases simulation
    sim_gold = 2320.0
    sim_dxy  = 104.5

    TF_MAP = {"M5": 5, "M15": 15, "H1": 60}
    MT5_TF = {}
    if MT5_AVAILABLE and STATE.mt5_connected:
        MT5_TF = {
            "M5":  mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1":  mt5.TIMEFRAME_H1,
        }

    ohlcv_refresh_counter = 0

    while True:
        try:
            ts = datetime.now()

            # ── Ticks live ────────────────────────────────────────────────────
            if MT5_AVAILABLE and STATE.mt5_connected and STATE.gold_symbol:
                tick_gold = mt5.symbol_info_tick(STATE.gold_symbol)
                tick_dxy  = mt5.symbol_info_tick(STATE.dxy_symbol) if STATE.dxy_symbol else None

                gold_price = float(tick_gold.bid) if tick_gold else sim_gold
                dxy_price  = float(tick_dxy.bid)  if tick_dxy  else sim_dxy
                gold_bid   = float(tick_gold.bid) if tick_gold else gold_price
                gold_ask   = float(tick_gold.ask) if tick_gold else gold_price + 0.3
            else:
                # Simulation réaliste
                sim_gold += np.random.normal(0, 0.05)
                sim_dxy  += np.random.normal(0, 0.003)
                gold_price = round(sim_gold, 2)
                dxy_price  = round(sim_dxy, 3)
                gold_bid   = gold_price
                gold_ask   = gold_price + 0.25

            with STATE._lock:
                STATE.gold_prev  = STATE.gold_price or gold_price
                STATE.dxy_prev   = STATE.dxy_price  or dxy_price
                STATE.gold_price = gold_price
                STATE.dxy_price  = dxy_price
                STATE.gold_bid   = gold_bid
                STATE.gold_ask   = gold_ask
                STATE.last_update = ts.isoformat()

            # ── OHLCV (moins fréquent — toutes les 5s) ────────────────────────
            ohlcv_refresh_counter += 1
            if ohlcv_refresh_counter >= 5:
                ohlcv_refresh_counter = 0
                for tf_name, tf_min in TF_MAP.items():
                    n_bars = 200 if tf_name == "M5" else (150 if tf_name == "M15" else 100)
                    if MT5_AVAILABLE and STATE.mt5_connected and STATE.gold_symbol:
                        candles = _get_ohlcv_mt5(STATE.gold_symbol, MT5_TF[tf_name], n_bars)
                        if not candles:
                            candles = _simulate_ohlcv("XAUUSD", n_bars, tf_min)
                    else:
                        candles = _simulate_ohlcv("XAUUSD", n_bars, tf_min)

                    with STATE._lock:
                        STATE.ohlcv[tf_name] = candles

                    # ── Analyse corrélation par TF ────────────────────────────
                    if MT5_AVAILABLE and STATE.mt5_connected and STATE.dxy_symbol:
                        dxy_candles = _get_ohlcv_mt5(STATE.dxy_symbol, MT5_TF[tf_name], n_bars)
                    else:
                        dxy_candles = _simulate_ohlcv("DXY", n_bars, tf_min)

                    if candles and dxy_candles:
                        g_closes = [c["close"] for c in candles]
                        d_closes = [c["close"] for c in dxy_candles]
                        tf_corr  = _compute_rolling_corr(g_closes, d_closes)
                        tf_sig   = _compute_signal(g_closes, d_closes, tf_corr)
                        with STATE._lock:
                            STATE.mtf_analysis[tf_name] = {
                                "signal": tf_sig["direction"],
                                "corr":   round(tf_corr, 4),
                                "trend":  _get_trend_label(g_closes),
                                "anticipation": tf_sig.get("anticipation"),
                            }

            # ── Corrélation globale (M5) ──────────────────────────────────────
            with STATE._lock:
                gold_c = [c["close"] for c in STATE.ohlcv.get("M5", [])]
                dxy_c  = _simulate_ohlcv("DXY", 100, 5)
                dxy_c  = [c["close"] for c in dxy_c]

            if gold_c and dxy_c:
                corr = _compute_rolling_corr(gold_c, dxy_c)
                sig  = _compute_signal(gold_c, dxy_c, corr)

                # Corr history (1 point par seconde)
                with STATE._lock:
                    STATE.correlation = corr
                    STATE.corr_history.append({
                        "time": ts.isoformat(),
                        "corr": round(corr, 4),
                    })
                    if len(STATE.corr_history) > 500:
                        STATE.corr_history = STATE.corr_history[-500:]

                    STATE.current_signal.update({
                        "direction":    sig["direction"],
                        "anticipation": sig.get("anticipation"),
                        "confidence":   sig["confidence"],
                        "corr":         round(corr, 4),
                        "gold_price":   round(gold_price, 2),
                        "dxy_price":    round(dxy_price, 3),
                        "time":         ts.isoformat(),
                    })

            time.sleep(DATA_REFRESH_S)

        except Exception as e:
            log.error(f"Data thread error: {e}", exc_info=True)
            STATE.add_log("ERROR", str(e))
            time.sleep(2)


# ─────────────────────────────────────────────────────────────────────────────
#  FASTAPI APP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Gold/DXY Bot API",
    description="Bridge entre le bot MT5 local et le dashboard hébergé",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restreindre en prod à l'URL du dashboard
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth middleware léger ──────────────────────────────────────────────────────
def _check_key(request: Request):
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service":  "Gold/DXY Bot API",
        "version":  "2.0",
        "status":   STATE.bot_status,
        "mt5":      STATE.mt5_connected,
        "uptime":   datetime.now().isoformat(),
    }


@app.get("/health")
def health():
    """Endpoint de santé pour Render/Railway."""
    return {"status": "ok", "mt5": STATE.mt5_connected, "time": datetime.now().isoformat()}


@app.get("/api/snapshot")
def get_snapshot(request: Request):
    """Snapshot complet — appelé par le dashboard toutes les secondes."""
    _check_key(request)
    return JSONResponse(STATE.snapshot())


@app.get("/api/prices")
def get_prices(request: Request):
    """Prix live seulement (léger, pour affichage temps réel)."""
    _check_key(request)
    with STATE._lock:
        return {
            "gold": STATE.gold_price,
            "dxy":  STATE.dxy_price,
            "gold_bid": STATE.gold_bid,
            "gold_ask": STATE.gold_ask,
            "gold_change": round(STATE.gold_price - STATE.gold_prev, 2),
            "dxy_change":  round(STATE.dxy_price  - STATE.dxy_prev,  4),
            "time": STATE.last_update,
        }


@app.get("/api/ohlcv/{timeframe}")
def get_ohlcv(timeframe: str, request: Request):
    """Données OHLCV par timeframe pour les graphiques."""
    _check_key(request)
    tf = timeframe.upper()
    if tf not in ("M5", "M15", "H1"):
        raise HTTPException(400, f"Timeframe invalide: {tf}")
    with STATE._lock:
        return {"timeframe": tf, "candles": STATE.ohlcv.get(tf, [])}


@app.get("/api/signal")
def get_signal(request: Request):
    """Signal courant + anticipation."""
    _check_key(request)
    with STATE._lock:
        return STATE.current_signal


@app.get("/api/signals/history")
def get_signals_history(request: Request, limit: int = 50):
    """Historique des signaux."""
    _check_key(request)
    with STATE._lock:
        return {"signals": STATE.signals[-limit:], "total": len(STATE.signals)}


@app.get("/api/correlation")
def get_correlation(request: Request):
    """Corrélation + historique rolling."""
    _check_key(request)
    with STATE._lock:
        return {
            "current": STATE.correlation,
            "history": STATE.corr_history[-200:],
        }


@app.get("/api/mtf")
def get_mtf(request: Request):
    """Analyse multi-timeframe."""
    _check_key(request)
    with STATE._lock:
        return STATE.mtf_analysis


@app.get("/api/logs")
def get_logs(request: Request, limit: int = 100):
    """Logs du bot."""
    _check_key(request)
    with STATE._lock:
        return {"logs": list(STATE.bot_logs)[-limit:]}


@app.get("/api/stats")
def get_stats(request: Request):
    """Statistiques de performance."""
    _check_key(request)
    with STATE._lock:
        return {
            "winrate": STATE.winrate,
            "wins":    STATE.wins,
            "losses":  STATE.losses,
            "total":   len(STATE.signals),
            "status":  STATE.bot_status,
            "mt5":     STATE.mt5_connected,
        }


# ── Endpoints PUSH — le bot envoie ses données ────────────────────────────────

class SignalPayload(BaseModel):
    direction:    str
    tf:           str
    entry:        float
    tp:           float
    sl:           float
    rr:           float
    sl_source:    str = "ATR"
    corr:         float = 0.0
    confidence:   int = 0
    anticipation: Optional[str] = None
    pipeline_state: str = "IDLE"
    result:       str = "OPEN"


@app.post("/api/signal/push")
def push_signal(payload: SignalPayload, request: Request):
    """Le bot pousse un nouveau signal."""
    _check_key(request)
    data = payload.dict()
    data["time"] = datetime.now().isoformat()
    STATE.set_signal(data)
    if payload.direction in ("BUY", "SELL"):
        STATE.add_signal_to_history(data)
    STATE.add_log("SIGNAL", f"{payload.direction} {payload.tf} @ {payload.entry} | TP:{payload.tp} SL:{payload.sl}")
    return {"status": "ok", "signal": data}


class LogPayload(BaseModel):
    level: str = "INFO"
    msg:   str


@app.post("/api/log/push")
def push_log(payload: LogPayload, request: Request):
    """Le bot pousse un log."""
    _check_key(request)
    STATE.add_log(payload.level, payload.msg)
    return {"status": "ok"}


class PricePayload(BaseModel):
    gold: float
    dxy:  float
    gold_bid: Optional[float] = None
    gold_ask: Optional[float] = None


@app.post("/api/prices/push")
def push_prices(payload: PricePayload, request: Request):
    """Le bot peut pousser des prix manuellement."""
    _check_key(request)
    with STATE._lock:
        STATE.gold_prev  = STATE.gold_price or payload.gold
        STATE.dxy_prev   = STATE.dxy_price  or payload.dxy
        STATE.gold_price = payload.gold
        STATE.dxy_price  = payload.dxy
        if payload.gold_bid: STATE.gold_bid = payload.gold_bid
        if payload.gold_ask: STATE.gold_ask = payload.gold_ask
        STATE.last_update = datetime.now().isoformat()
    return {"status": "ok"}


class ResultPayload(BaseModel):
    signal_id: int
    result:    str   # "WIN" ou "LOSS"


@app.post("/api/signal/result")
def update_result(payload: ResultPayload, request: Request):
    """Mise à jour du résultat d'un signal."""
    _check_key(request)
    with STATE._lock:
        for sig in STATE.signals:
            if sig.get("id") == payload.signal_id:
                sig["result"] = payload.result
                break
        STATE._update_winrate()
        STATE._save_signals_file()
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
#  DÉMARRAGE
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    """Lance le thread de données MT5 au démarrage."""
    t = threading.Thread(target=mt5_data_thread, daemon=True)
    t.start()
    log.info(f"API Server démarré sur http://{API_HOST}:{API_PORT}")
    log.info(f"API Key: {API_KEY}")
    log.info(f"Mode: {'MT5 Live' if MT5_AVAILABLE else 'Simulation'}")


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info",
    )
