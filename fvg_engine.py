"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              FVG ENGINE — Fair Value Gap Haute Qualité                      ║
║              XAUUSD / Intégrable dans bot MT5 ou dashboard                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Critères de qualité appliqués :
  1. Taille entre 0.6×ATR et 1.2×ATR (ni trop petit, ni trop large)
  2. Impulsion forte : la bougie centrale doit faire > 1.5×ATR de corps
  3. Non mitigé : le prix ne doit pas avoir retouché le gap après sa création
  4. Sens du marché : FVG bullish uniquement en tendance haussière (et vice versa)
  5. Bonus si proche d'un Order Block (confluence)

Usage :
    from fvg_engine import detect_quality_fvg, draw_fvg_on_figure
    fvgs = detect_quality_fvg(df)
    fig  = draw_fvg_on_figure(fig, fvgs)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional
import plotly.graph_objects as go


# ─────────────────────────────────────────────────────────────────────────────
#  PARAMÈTRES
# ─────────────────────────────────────────────────────────────────────────────

ATR_PERIOD        = 14
FVG_MIN_RATIO     = 0.6    # taille minimum = 0.6 × ATR
FVG_MAX_RATIO     = 1.2    # taille maximum = 1.2 × ATR
IMPULSE_MIN_RATIO = 1.5    # corps bougie centrale > 1.5 × ATR
MITIGATION_BUFFER = 0.0    # 0 = le prix doit toucher le gap pour le mitiger
OB_PROXIMITY_PCT  = 0.002  # FVG considéré "proche OB" si dans 0.2% du prix
TREND_EMA_PERIOD  = 50     # EMA pour définir la tendance


# ─────────────────────────────────────────────────────────────────────────────
#  DATACLASS RÉSULTAT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FVG:
    """Un Fair Value Gap qualifié."""
    direction:  str          # "bullish" ou "bearish"
    low:        float        # borne basse du gap
    high:       float        # borne haute du gap
    mid:        float        # milieu du gap (niveau clé)
    size:       float        # taille absolue en $
    size_ratio: float        # taille / ATR
    impulse:    float        # force de la bougie centrale (corps / ATR)
    bar_index:  int          # index de la bougie i (celle qui crée le gap)
    time:       object       # timestamp
    mitigated:  bool = False # déjà retouché par le prix
    near_ob:    bool = False # confluence avec un Order Block
    score:      float = 0.0  # score de qualité 0-100


# ─────────────────────────────────────────────────────────────────────────────
#  ATR
# ─────────────────────────────────────────────────────────────────────────────

def _compute_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """ATR classique (Wilder)."""
    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift(1)).abs()
    lc  = (df["low"]  - df["close"].shift(1)).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr


# ─────────────────────────────────────────────────────────────────────────────
#  TENDANCE
# ─────────────────────────────────────────────────────────────────────────────

def _get_trend(df: pd.DataFrame, period: int = TREND_EMA_PERIOD) -> pd.Series:
    """
    Tendance par EMA :
    +1 = prix au-dessus de l'EMA → haussier
    -1 = prix en-dessous        → baissier
    """
    ema   = df["close"].ewm(span=period, adjust=False).mean()
    trend = np.where(df["close"] > ema, 1, -1)
    return pd.Series(trend, index=df.index)


# ─────────────────────────────────────────────────────────────────────────────
#  DÉTECTION ORDER BLOCKS (simplifié pour confluence)
# ─────────────────────────────────────────────────────────────────────────────

def _detect_ob_levels(df: pd.DataFrame, atr: pd.Series,
                       lookback: int = 20) -> List[float]:
    """
    Retourne la liste des niveaux OB (haut ou bas de la bougie OB).
    Un OB = bougie de sens inverse avant une impulsion forte.
    """
    levels = []
    closes = df["close"].values
    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values
    n      = len(df)

    for i in range(1, min(n - 1, lookback)):
        move = abs(closes[i+1] - closes[i])
        atr_i = float(atr.iloc[i]) if not np.isnan(atr.iloc[i]) else 1.0

        # OB Bullish : bougie baissière avant hausse
        if opens[i] > closes[i] and closes[i+1] > opens[i+1] and move > atr_i * 0.8:
            levels.append(round(float(lows[i]),  2))
            levels.append(round(float(highs[i]), 2))

        # OB Bearish : bougie haussière avant baisse
        if closes[i] > opens[i] and closes[i+1] < opens[i+1] and move > atr_i * 0.8:
            levels.append(round(float(lows[i]),  2))
            levels.append(round(float(highs[i]), 2))

    return levels


# ─────────────────────────────────────────────────────────────────────────────
#  DÉTECTION FVG HAUTE QUALITÉ
# ─────────────────────────────────────────────────────────────────────────────

def detect_quality_fvg(
    df: pd.DataFrame,
    use_trend_filter:  bool  = True,
    use_ob_confluence: bool  = True,
    atr_min_ratio:     float = FVG_MIN_RATIO,
    atr_max_ratio:     float = FVG_MAX_RATIO,
    impulse_min_ratio: float = IMPULSE_MIN_RATIO,
    max_fvg:           int   = 5,
) -> List[FVG]:
    """
    Détecte les FVG de haute qualité sur un DataFrame OHLC.

    Args:
        df               : DataFrame avec colonnes open, high, low, close (index datetime)
        use_trend_filter : Ne garder que les FVG dans le sens de la tendance EMA50
        use_ob_confluence: Marquer les FVG proches d'un Order Block
        atr_min_ratio    : Taille minimum du FVG en multiple d'ATR (défaut 0.6)
        atr_max_ratio    : Taille maximum (défaut 1.2)
        impulse_min_ratio: Force minimum de la bougie centrale (défaut 1.5×ATR)
        max_fvg          : Nombre maximum de FVG à retourner (les meilleurs)

    Returns:
        Liste de FVG triée par score décroissant
    """
    if df is None or len(df) < ATR_PERIOD + 5:
        return []

    df   = df.copy().reset_index(drop=True)
    atr  = _compute_atr(df)
    n    = len(df)
    results: List[FVG] = []

    # Tendance et niveaux OB
    trend  = _get_trend(df) if use_trend_filter else pd.Series([0]*n)
    ob_lvl = _detect_ob_levels(df, atr) if use_ob_confluence else []

    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    opens  = df["open"].values

    for i in range(2, n - 1):

        atr_i = float(atr.iloc[i])
        if np.isnan(atr_i) or atr_i < 1e-6:
            continue

        # ── Bougie centrale (i-1) = la bougie qui crée l'impulsion ───────────
        body_i   = abs(closes[i-1] - opens[i-1])
        impulse  = body_i / atr_i

        # Filtrer les impulsions trop faibles
        if impulse < impulse_min_ratio:
            continue

        # ── Calcul du gap ─────────────────────────────────────────────────────

        # FVG Bullish : gap entre high[i-2] et low[i]
        gap_bull = lows[i] - highs[i-2]
        # FVG Bearish : gap entre low[i-2] et high[i]
        gap_bear = lows[i-2] - highs[i]

        for direction, gap_size, fvg_low, fvg_high in [
            ("bullish", gap_bull, float(highs[i-2]), float(lows[i])),
            ("bearish", gap_bear, float(highs[i]),   float(lows[i-2])),
        ]:
            if gap_size <= 0:
                continue

            size_ratio = gap_size / atr_i

            # ── FILTRE 1 : Taille entre 0.6×ATR et 1.2×ATR ──────────────────
            if not (atr_min_ratio <= size_ratio <= atr_max_ratio):
                continue

            # ── FILTRE 2 : Tendance ───────────────────────────────────────────
            if use_trend_filter:
                trend_i = int(trend.iloc[i])
                if direction == "bullish" and trend_i != 1:
                    continue
                if direction == "bearish" and trend_i != -1:
                    continue

            # ── FILTRE 3 : Mitigation (prix a-t-il retouché le gap ?) ─────────
            mitigated = False
            for j in range(i + 1, n):
                if direction == "bullish":
                    # Mitigation si le prix descend dans le gap
                    if lows[j] <= fvg_high + MITIGATION_BUFFER:
                        mitigated = True
                        break
                else:
                    # Mitigation si le prix monte dans le gap
                    if highs[j] >= fvg_low - MITIGATION_BUFFER:
                        mitigated = True
                        break

            # Ne garder que les FVG non mitigés
            if mitigated:
                continue

            # ── FILTRE 4 : Confluence Order Block ────────────────────────────
            near_ob = False
            if use_ob_confluence and ob_lvl:
                mid = (fvg_low + fvg_high) / 2
                for lvl in ob_lvl:
                    if abs(lvl - mid) / mid < OB_PROXIMITY_PCT:
                        near_ob = True
                        break

            # ── SCORE DE QUALITÉ ──────────────────────────────────────────────
            # Composantes :
            #   • Ratio de taille (idéal = 0.9×ATR)          → 0-40 pts
            #   • Force d'impulsion                            → 0-30 pts
            #   • Confluence OB                                → +20 pts
            #   • Position dans le range taille               → 0-10 pts

            # Meilleur score si taille proche de 0.9×ATR
            size_score   = max(0, 40 - abs(size_ratio - 0.9) * 40)
            impulse_score = min(30, (impulse - impulse_min_ratio) * 10)
            ob_score      = 20 if near_ob else 0
            range_score   = 10 if atr_min_ratio + 0.1 <= size_ratio <= atr_max_ratio - 0.1 else 0

            score = size_score + impulse_score + ob_score + range_score

            fvg = FVG(
                direction  = direction,
                low        = round(fvg_low,  2),
                high       = round(fvg_high, 2),
                mid        = round((fvg_low + fvg_high) / 2, 2),
                size       = round(gap_size, 3),
                size_ratio = round(size_ratio, 3),
                impulse    = round(impulse, 2),
                bar_index  = i,
                time       = df["time"].iloc[i] if "time" in df.columns else i,
                mitigated  = False,
                near_ob    = near_ob,
                score      = round(score, 1),
            )
            results.append(fvg)

    # Trier par score décroissant et limiter
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:max_fvg]


# ─────────────────────────────────────────────────────────────────────────────
#  AFFICHAGE SUR FIGURE PLOTLY
# ─────────────────────────────────────────────────────────────────────────────

def draw_fvg_on_figure(
    fig:     go.Figure,
    fvgs:    List[FVG],
    row:     int   = 1,
    col:     int   = 1,
    opacity: float = 0.15,
) -> go.Figure:
    """
    Dessine les FVG qualifiés sur une figure Plotly existante.
    Les FVG avec confluence OB ont une bordure plus épaisse.
    """
    for fvg in fvgs:
        if fvg.direction == "bullish":
            fill  = f"rgba(0,212,170,{opacity})"
            border= f"rgba(0,212,170,{opacity*3})"
        else:
            fill  = f"rgba(255,77,106,{opacity})"
            border= f"rgba(255,77,106,{opacity*3})"

        border_width = 1.5 if fvg.near_ob else 0.8

        # Zone FVG
        fig.add_hrect(
            y0=fvg.low, y1=fvg.high,
            row=row, col=col,
            fillcolor=fill,
            line=dict(color=border, width=border_width),
        )

        # Ligne du milieu (niveau clé)
        fig.add_hline(
            y=fvg.mid,
            row=row, col=col,
            line=dict(
                color=border.replace(f"{opacity*3}", "0.6"),
                width=0.6,
                dash="dot",
            ),
            opacity=0.5,
        )

    return fig


# ─────────────────────────────────────────────────────────────────────────────
#  CONVERSION POUR API SERVER
# ─────────────────────────────────────────────────────────────────────────────

def fvg_to_dict(fvg: FVG) -> dict:
    """Convertit un FVG en dict JSON-sérialisable pour l'API."""
    return {
        "direction":  fvg.direction,
        "low":        fvg.low,
        "high":       fvg.high,
        "mid":        fvg.mid,
        "size":       fvg.size,
        "size_ratio": fvg.size_ratio,
        "impulse":    fvg.impulse,
        "score":      fvg.score,
        "near_ob":    fvg.near_ob,
        "mitigated":  fvg.mitigated,
        "time":       str(fvg.time),
    }


def fvgs_to_dict_list(fvgs: List[FVG]) -> dict:
    """
    Retourne le format attendu par zones dans api_server.py :
    {"fvg_bullish": [...], "fvg_bearish": [...]}
    """
    return {
        "fvg_bullish": [fvg_to_dict(f) for f in fvgs if f.direction == "bullish"],
        "fvg_bearish": [fvg_to_dict(f) for f in fvgs if f.direction == "bearish"],
    }


# ─────────────────────────────────────────────────────────────────────────────
#  INTÉGRATION API SERVER — remplace compute_zones()
# ─────────────────────────────────────────────────────────────────────────────

def compute_zones_with_quality_fvg(candles: list) -> dict:
    """
    Remplace compute_zones() dans api_server.py.
    Appelle : from fvg_engine import compute_zones_with_quality_fvg
    Utilise : z = compute_zones_with_quality_fvg(STATE.ohlcv["M5"])
    """
    if not candles or len(candles) < 20:
        return {}

    df     = pd.DataFrame(candles)
    df["time"] = pd.to_datetime(df["time"])
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    opens  = df["open"].values
    n      = len(df)

    # ATR
    tr  = [max(highs[i]-lows[i],
               abs(highs[i]-closes[i-1]) if i>0 else 0,
               abs(lows[i] -closes[i-1]) if i>0 else 0) for i in range(n)]
    atr = float(np.mean(tr[-14:])) if n >= 14 else float(np.mean(tr))

    # Support / Résistance
    recent     = df.tail(30)
    support    = round(float(recent["low"].min()),  2)
    resistance = round(float(recent["high"].max()), 2)

    # Swings
    sw_lows, sw_highs, lb = [], [], 3
    for i in range(lb, n-lb):
        if all(lows[i]  < lows[i-j]  for j in range(1,lb+1)) and all(lows[i]  < lows[i+j]  for j in range(1,lb+1)): sw_lows.append(round(float(lows[i]),2))
        if all(highs[i] > highs[i-j] for j in range(1,lb+1)) and all(highs[i] > highs[i+j] for j in range(1,lb+1)): sw_highs.append(round(float(highs[i]),2))

    # FVG HAUTE QUALITÉ
    fvgs     = detect_quality_fvg(df, use_trend_filter=True, use_ob_confluence=True, max_fvg=5)
    fvg_dict = fvgs_to_dict_list(fvgs)

    # Order Blocks
    ob_buy = ob_sell = None
    for i in range(1, min(n-1, 25)):
        move = abs(closes[i+1]-closes[i])
        if opens[i]>closes[i] and closes[i+1]>opens[i+1] and move>atr*0.5: ob_buy  = round(float(lows[i]),  2)
        if closes[i]>opens[i] and closes[i+1]<opens[i+1] and move>atr*0.5: ob_sell = round(float(highs[i]), 2)

    return {
        "support":      support,
        "resistance":   resistance,
        "swing_lows":   sw_lows[-5:],
        "swing_highs":  sw_highs[-5:],
        "fvg_bullish":  fvg_dict["fvg_bullish"],
        "fvg_bearish":  fvg_dict["fvg_bearish"],
        "ob_buy":       ob_buy,
        "ob_sell":      ob_sell,
        "atr":          round(atr, 3),
        "fvg_filter":   round(atr * FVG_MIN_RATIO, 3),
        "fvg_count":    len(fvgs),
        "fvg_scores":   [f.score for f in fvgs],
    }


# ─────────────────────────────────────────────────────────────────────────────
#  TEST RAPIDE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import numpy as np
    from datetime import datetime, timedelta

    # Générer des données simulées
    np.random.seed(42)
    n = 200
    now = datetime.now()
    closes = [2300.0]
    for _ in range(n-1):
        closes.append(closes[-1] * (1 + np.random.normal(0, 0.0008)))

    rows = []
    for i in range(n):
        t = now - timedelta(minutes=5*(n-1-i))
        o = closes[i-1] if i>0 else closes[i]; c = closes[i]
        r = abs(c-o)*(1+abs(np.random.normal(0,.5)))
        rows.append({"time":t,"open":round(o,2),"high":round(max(o,c)+r*.4,2),
                      "low":round(min(o,c)-r*.4,2),"close":round(c,2),"volume":1000})

    df = pd.DataFrame(rows)
    fvgs = detect_quality_fvg(df, max_fvg=10)

    print(f"\n{'='*55}")
    print(f"  FVG Haute Qualité détectés : {len(fvgs)}")
    print(f"{'='*55}")
    for i, f in enumerate(fvgs, 1):
        ob = "⭐ OB" if f.near_ob else ""
        print(f"  {i}. {f.direction.upper():8} | {f.low:.2f}–{f.high:.2f}"
              f" | size={f.size_ratio:.2f}×ATR"
              f" | impulse={f.impulse:.1f}×"
              f" | score={f.score:.0f}/100 {ob}")
    print()
