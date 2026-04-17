"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ZONES.PY — DÉTECTION DES ZONES DE MARCHÉ                 ║
║        Support/Résistance | Swing | Fair Value Gap | Order Block            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Utilisation :
    from zones import detect_zones
    z = detect_zones(gold_df, direction="BUY")
    print(z)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List
import logging

log = logging.getLogger("GoldDXY")

# ─────────────────────────────────────────────────────────────────────────────
#  PARAMÈTRES
# ─────────────────────────────────────────────────────────────────────────────

SR_WINDOW      = 30    # Fenêtre support/résistance (bougies)
SWING_LOOKBACK = 3     # Nb bougies de chaque côté pour valider un swing
FVG_MIN_GAP    = 0.10  # Gap minimum en $ pour qu'un FVG soit valide
OB_LOOKBACK    = 20    # Fenêtre pour chercher les Order Blocks

# ─────────────────────────────────────────────────────────────────────────────
#  DATACLASS RÉSULTAT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MarketZones:
    """Toutes les zones détectées sur un DataFrame."""

    # Support / Résistance
    support    : Optional[float] = None
    resistance : Optional[float] = None

    # Swing points (liste des N derniers)
    swing_lows  : List[float] = field(default_factory=list)
    swing_highs : List[float] = field(default_factory=list)

    # Fair Value Gap (prix + label)
    fvg_bullish : List[dict] = field(default_factory=list)   # [{"low": x, "high": y, "mid": z}]
    fvg_bearish : List[dict] = field(default_factory=list)

    # Order Blocks simplifiés
    ob_buy  : Optional[float] = None   # bas du dernier OB haussier
    ob_sell : Optional[float] = None   # haut du dernier OB baissier

    # Prix courant (référence)
    current_price : float = 0.0

    def nearest_swing_low(self) -> Optional[float]:
        """Retourne le swing low le plus proche (en dessous du prix)."""
        candidates = [s for s in self.swing_lows if s < self.current_price]
        return max(candidates) if candidates else None

    def nearest_swing_high(self) -> Optional[float]:
        """Retourne le swing high le plus proche (au-dessus du prix)."""
        candidates = [s for s in self.swing_highs if s > self.current_price]
        return min(candidates) if candidates else None

    def nearest_fvg_low(self) -> Optional[float]:
        """FVG bullish le plus proche sous le prix (bas du gap)."""
        candidates = [f["low"] for f in self.fvg_bullish if f["low"] < self.current_price]
        return max(candidates) if candidates else None

    def nearest_fvg_high(self) -> Optional[float]:
        """FVG bearish le plus proche au-dessus du prix (haut du gap)."""
        candidates = [f["high"] for f in self.fvg_bearish if f["high"] > self.current_price]
        return min(candidates) if candidates else None


# ─────────────────────────────────────────────────────────────────────────────
#  CALCUL SUPPORT / RÉSISTANCE
# ─────────────────────────────────────────────────────────────────────────────

def calc_support_resistance(df: pd.DataFrame, window: int = SR_WINDOW) -> tuple:
    """
    Méthode simple et fiable :
    - support    = min(low) sur les N dernières bougies
    - résistance = max(high) sur les N dernières bougies
    """
    recent = df.tail(window)
    support    = float(recent["low"].min())
    resistance = float(recent["high"].max())
    return round(support, 2), round(resistance, 2)


# ─────────────────────────────────────────────────────────────────────────────
#  SWING HIGH / SWING LOW
# ─────────────────────────────────────────────────────────────────────────────

def calc_swings(df: pd.DataFrame, lookback: int = SWING_LOOKBACK) -> tuple:
    """
    Swing High = bougie dont le high est le plus élevé de ses [lookback] voisins de chaque côté.
    Swing Low  = bougie dont le low est le plus bas de ses [lookback] voisins de chaque côté.

    Retourne : (liste swing_lows, liste swing_highs) — les N derniers trouvés
    """
    highs = df["high"].values
    lows  = df["low"].values
    n     = len(df)

    swing_highs = []
    swing_lows  = []

    for i in range(lookback, n - lookback):
        # Swing High
        is_swing_high = all(highs[i] > highs[i - j] for j in range(1, lookback + 1)) and \
                        all(highs[i] > highs[i + j] for j in range(1, lookback + 1))
        if is_swing_high:
            swing_highs.append(round(float(highs[i]), 2))

        # Swing Low
        is_swing_low = all(lows[i] < lows[i - j] for j in range(1, lookback + 1)) and \
                       all(lows[i] < lows[i + j] for j in range(1, lookback + 1))
        if is_swing_low:
            swing_lows.append(round(float(lows[i]), 2))

    # Garder seulement les 5 derniers pour éviter le bruit
    return swing_lows[-5:], swing_highs[-5:]


# ─────────────────────────────────────────────────────────────────────────────
#  FAIR VALUE GAP (FVG)
# ─────────────────────────────────────────────────────────────────────────────

def calc_fvg(df: pd.DataFrame, min_gap: float = FVG_MIN_GAP) -> tuple:
    """
    FVG Bullish  : low[i] > high[i-2]  → zone de gap haussier
    FVG Bearish  : high[i] < low[i-2]  → zone de gap baissier

    Retourne : (liste fvg_bullish, liste fvg_bearish)
    Chaque FVG = {"low": x, "high": y, "mid": z, "index": i}
    """
    fvg_bullish = []
    fvg_bearish = []

    highs = df["high"].values
    lows  = df["low"].values
    n     = len(df)

    for i in range(2, n):
        # FVG Bullish : gap entre high[i-2] et low[i]
        gap_bull = lows[i] - highs[i - 2]
        if gap_bull > min_gap:
            fvg_bullish.append({
                "low"  : round(float(highs[i - 2]), 2),
                "high" : round(float(lows[i]),      2),
                "mid"  : round(float((highs[i - 2] + lows[i]) / 2), 2),
                "index": i,
            })

        # FVG Bearish : gap entre low[i-2] et high[i]
        gap_bear = lows[i - 2] - highs[i]
        if gap_bear > min_gap:
            fvg_bearish.append({
                "low"  : round(float(highs[i]),      2),
                "high" : round(float(lows[i - 2]),   2),
                "mid"  : round(float((highs[i] + lows[i - 2]) / 2), 2),
                "index": i,
            })

    # Garder les 3 derniers FVG de chaque type
    return fvg_bullish[-3:], fvg_bearish[-3:]


# ─────────────────────────────────────────────────────────────────────────────
#  ORDER BLOCK (version simplifiée)
# ─────────────────────────────────────────────────────────────────────────────

def calc_order_blocks(df: pd.DataFrame, lookback: int = OB_LOOKBACK) -> tuple:
    """
    Order Block simplifié :
    - BUY OB  = dernière bougie BAISSIÈRE (close < open) avant une impulsion HAUSSIÈRE
    - SELL OB = dernière bougie HAUSSIÈRE (close > open) avant une impulsion BAISSIÈRE

    Impulsion = mouvement > 0.5 × ATR

    Retourne : (ob_buy_low, ob_sell_high)
    - ob_buy_low   = bas de la dernière bougie baissière avant impulsion haussière
    - ob_sell_high = haut de la dernière bougie haussière avant impulsion baissière
    """
    closes = df["close"].values
    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values
    n      = len(df)

    # ATR simplifié pour filtrer les impulsions
    tr_values = [abs(highs[i] - lows[i]) for i in range(n)]
    atr_simple = np.mean(tr_values[-20:]) if n >= 20 else np.mean(tr_values)

    ob_buy_low   = None
    ob_sell_high = None

    recent = df.tail(lookback)
    rc = recent["close"].values
    ro = recent["open"].values
    rh = recent["high"].values
    rl = recent["low"].values
    rn = len(recent)

    for i in range(1, rn - 1):
        move_next = abs(rc[i + 1] - rc[i])

        # BUY OB : bougie baissière suivie d'une bougie haussière forte
        if ro[i] > rc[i]:   # bougie baissière
            if rc[i + 1] > ro[i + 1] and move_next > atr_simple * 0.5:
                ob_buy_low = round(float(rl[i]), 2)

        # SELL OB : bougie haussière suivie d'une bougie baissière forte
        if rc[i] > ro[i]:   # bougie haussière
            if rc[i + 1] < ro[i + 1] and move_next > atr_simple * 0.5:
                ob_sell_high = round(float(rh[i]), 2)

    return ob_buy_low, ob_sell_high


# ─────────────────────────────────────────────────────────────────────────────
#  FONCTION PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def detect_zones(df: pd.DataFrame) -> MarketZones:
    """
    Calcule toutes les zones de marché sur un DataFrame OHLC.

    Args:
        df : DataFrame avec colonnes open, high, low, close

    Returns:
        MarketZones avec toutes les zones détectées
    """
    if df is None or len(df) < SR_WINDOW + 10:
        log.warning("zones.detect_zones: données insuffisantes")
        return MarketZones()

    current_price = float(df["close"].iloc[-1])

    # ── Calcul des zones ──────────────────────────────────────────────────────
    support, resistance         = calc_support_resistance(df)
    swing_lows, swing_highs     = calc_swings(df)
    fvg_bullish, fvg_bearish    = calc_fvg(df)
    ob_buy_low, ob_sell_high    = calc_order_blocks(df)

    zones = MarketZones(
        support       = support,
        resistance    = resistance,
        swing_lows    = swing_lows,
        swing_highs   = swing_highs,
        fvg_bullish   = fvg_bullish,
        fvg_bearish   = fvg_bearish,
        ob_buy        = ob_buy_low,
        ob_sell       = ob_sell_high,
        current_price = current_price,
    )

    log.info(
        f"Zones | Support: {support} | Résistance: {resistance} | "
        f"Swings: {len(swing_lows)}L {len(swing_highs)}H | "
        f"FVG: {len(fvg_bullish)}↑ {len(fvg_bearish)}↓ | "
        f"OB Buy: {ob_buy_low} | OB Sell: {ob_sell_high}"
    )

    return zones
