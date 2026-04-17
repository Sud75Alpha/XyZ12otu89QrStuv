"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RISK.PY — SL/TP INTELLIGENT PAR ZONES                    ║
║            Remplace compute_tp_sl() du fichier principal                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Utilisation :
    from risk import compute_smart_sl_tp
    entry, tp, sl, atr, rr, sl_source = compute_smart_sl_tp("BUY", gold_df)
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging

from zones import detect_zones, MarketZones

log = logging.getLogger("GoldDXY")

# ─────────────────────────────────────────────────────────────────────────────
#  PARAMÈTRES
# ─────────────────────────────────────────────────────────────────────────────

SL_BUFFER_PIPS   = 5.0    # Buffer de sécurité en $ au-delà de la zone SL
MIN_SL_PIPS      = 50.0   # SL minimum en $ (sécurité anti-micro-SL)
MAX_SL_PIPS      = 300.0  # SL maximum en $ (évite les SL trop larges)
MIN_RR           = 2.0    # Risk/Reward minimum
ATR_PERIOD       = 14     # Période ATR
ATR_SL_FALLBACK  = 0.8    # Multiplicateur ATR si aucune zone trouvée

# ─────────────────────────────────────────────────────────────────────────────
#  ATR
# ─────────────────────────────────────────────────────────────────────────────

def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> float:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(float(atr), 2) if not np.isnan(atr) else 10.0


# ─────────────────────────────────────────────────────────────────────────────
#  SÉLECTION DU MEILLEUR SL
# ─────────────────────────────────────────────────────────────────────────────

def _select_sl_buy(zones: MarketZones, entry: float, atr: float) -> Tuple[float, str]:
    """
    Pour un BUY, le SL va EN DESSOUS du prix.
    On cherche la zone la plus proche et la plus logique sous le prix.

    Candidats (du plus proche au plus loin) :
      1. Swing Low le plus proche
      2. FVG bullish bas le plus proche
      3. Order Block Buy bas
      4. Support (S/R)
      5. Fallback ATR
    """
    candidates = {}

    # 1. Swing Low le plus proche sous l'entrée
    sl_swing = zones.nearest_swing_low()
    if sl_swing and sl_swing < entry:
        candidates["Swing Low"] = sl_swing

    # 2. FVG bullish bas (sous l'entrée)
    fvg_low = zones.nearest_fvg_low()
    if fvg_low and fvg_low < entry:
        candidates["FVG Bas"] = fvg_low

    # 3. Order Block Buy
    if zones.ob_buy and zones.ob_buy < entry:
        candidates["Order Block"] = zones.ob_buy

    # 4. Support
    if zones.support and zones.support < entry:
        candidates["Support"] = zones.support

    if candidates:
        # Choisir la zone la plus proche SOUS l'entrée
        best_label = max(candidates, key=lambda k: candidates[k])
        best_zone  = candidates[best_label]
        sl_raw     = best_zone - SL_BUFFER_PIPS
        log.info(f"SL BUY basé sur {best_label}: {best_zone} → SL: {sl_raw}")
    else:
        # Fallback ATR
        sl_raw    = entry - atr * ATR_SL_FALLBACK
        best_label = "ATR fallback"
        log.info(f"SL BUY fallback ATR: {sl_raw}")

    return round(sl_raw, 2), best_label


def _select_sl_sell(zones: MarketZones, entry: float, atr: float) -> Tuple[float, str]:
    """
    Pour un SELL, le SL va AU-DESSUS du prix.

    Candidats :
      1. Swing High le plus proche
      2. FVG bearish haut le plus proche
      3. Order Block Sell haut
      4. Résistance (S/R)
      5. Fallback ATR
    """
    candidates = {}

    # 1. Swing High le plus proche au-dessus
    sh_swing = zones.nearest_swing_high()
    if sh_swing and sh_swing > entry:
        candidates["Swing High"] = sh_swing

    # 2. FVG bearish haut (au-dessus de l'entrée)
    fvg_high = zones.nearest_fvg_high()
    if fvg_high and fvg_high > entry:
        candidates["FVG Haut"] = fvg_high

    # 3. Order Block Sell
    if zones.ob_sell and zones.ob_sell > entry:
        candidates["Order Block"] = zones.ob_sell

    # 4. Résistance
    if zones.resistance and zones.resistance > entry:
        candidates["Résistance"] = zones.resistance

    if candidates:
        # Choisir la zone la plus proche AU-DESSUS de l'entrée
        best_label = min(candidates, key=lambda k: candidates[k])
        best_zone  = candidates[best_label]
        sl_raw     = best_zone + SL_BUFFER_PIPS
        log.info(f"SL SELL basé sur {best_label}: {best_zone} → SL: {sl_raw}")
    else:
        # Fallback ATR
        sl_raw     = entry + atr * ATR_SL_FALLBACK
        best_label = "ATR fallback"
        log.info(f"SL SELL fallback ATR: {sl_raw}")

    return round(sl_raw, 2), best_label


# ─────────────────────────────────────────────────────────────────────────────
#  CALCUL DU TP
# ─────────────────────────────────────────────────────────────────────────────

def _compute_tp(direction: str, entry: float, sl: float,
                zones: MarketZones, min_rr: float = MIN_RR) -> Tuple[float, str]:
    """
    TP = max(R/R minimum, zone de liquidité la plus proche).

    Pour BUY  : TP au-dessus du prix → Swing High ou Résistance proche
    Pour SELL : TP en dessous du prix → Swing Low ou Support proche
    """
    sl_dist = abs(entry - sl)
    tp_min  = entry + sl_dist * min_rr if direction == "BUY" else entry - sl_dist * min_rr

    tp_zone  = None
    tp_label = f"R/R {min_rr}:1"

    if direction == "BUY":
        # Chercher une résistance ou swing high au-dessus
        sh = zones.nearest_swing_high()
        if sh and sh > tp_min:
            tp_zone  = sh
            tp_label = "Swing High"
        elif zones.resistance and zones.resistance > tp_min:
            tp_zone  = zones.resistance
            tp_label = "Résistance"

    else:  # SELL
        # Chercher un support ou swing low en dessous
        sl_zone = zones.nearest_swing_low()
        if sl_zone and sl_zone < tp_min:
            tp_zone  = sl_zone
            tp_label = "Swing Low"
        elif zones.support and zones.support < tp_min:
            tp_zone  = zones.support
            tp_label = "Support"

    # Si zone trouvée et meilleure que le minimum R/R → l'utiliser
    if tp_zone:
        tp = tp_zone
    else:
        tp = tp_min

    return round(tp, 2), tp_label


# ─────────────────────────────────────────────────────────────────────────────
#  FONCTION PRINCIPALE — REMPLACE compute_tp_sl()
# ─────────────────────────────────────────────────────────────────────────────

def compute_smart_sl_tp(
    direction : str,
    gold_df   : pd.DataFrame,
) -> Tuple[float, float, float, float, float, str]:
    """
    Calcule SL et TP intelligents basés sur les zones de marché.

    Args:
        direction : "BUY" ou "SELL"
        gold_df   : DataFrame OHLC Gold

    Returns:
        (entry, tp, sl, atr, rr, sl_source)
        - entry     : prix d'entrée (close actuel)
        - tp        : Take Profit
        - sl        : Stop Loss
        - atr       : ATR actuel
        - rr        : Risk/Reward ratio
        - sl_source : source du SL ("Swing Low", "Support", "ATR fallback", etc.)

    Compatible avec l'appel existant :
        entry, tp, sl, atr, rr = compute_tp_sl(direction, gold_df)
    Pour utiliser la nouvelle version :
        entry, tp, sl, atr, rr, sl_source = compute_smart_sl_tp(direction, gold_df)
    """
    entry = float(gold_df["close"].iloc[-1])
    atr   = _compute_atr(gold_df)

    # Détection des zones
    zones = detect_zones(gold_df)

    # ── Calcul SL ─────────────────────────────────────────────────────────────
    if direction == "BUY":
        sl, sl_source = _select_sl_buy(zones, entry, atr)
    else:
        sl, sl_source = _select_sl_sell(zones, entry, atr)

    # ── Clamp SL dans les limites raisonnables ────────────────────────────────
    sl_dist = abs(entry - sl)

    if sl_dist < MIN_SL_PIPS:
        log.info(f"SL trop proche ({sl_dist:.1f}$) → ajusté au minimum {MIN_SL_PIPS}$")
        sl_dist   = MIN_SL_PIPS
        sl        = round(entry - sl_dist, 2) if direction == "BUY" else round(entry + sl_dist, 2)
        sl_source += " (ajusté min)"

    if sl_dist > MAX_SL_PIPS:
        log.info(f"SL trop large ({sl_dist:.1f}$) → limité à {MAX_SL_PIPS}$")
        sl_dist   = MAX_SL_PIPS
        sl        = round(entry - sl_dist, 2) if direction == "BUY" else round(entry + sl_dist, 2)
        sl_source += " (limité max)"

    # ── Calcul TP ─────────────────────────────────────────────────────────────
    tp, tp_label = _compute_tp(direction, entry, sl, zones)

    # ── Calcul R/R final ──────────────────────────────────────────────────────
    tp_dist = abs(tp - entry)
    rr      = round(tp_dist / sl_dist, 2) if sl_dist > 0 else MIN_RR

    log.info(
        f"Risk | Dir: {direction} | Entry: {entry} | "
        f"SL: {sl} ({sl_source}) | TP: {tp} ({tp_label}) | R/R: {rr}"
    )

    return entry, tp, sl, round(atr, 2), rr, sl_source
