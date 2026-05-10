# -*- coding: utf-8 -*-
"""
MARKET_GATE: Market environment assessment module.

Determines overall market regime before any stock selection:
- Risk-On (aggressive)
- Selective Bull (selective strength)
- Neutral Range (reduce exposure)
- Risk-Off (no chasing, no low-liquidity small caps)
- Event-Only (only catalyst-driven, small size)

Key indicators: SPY, QQQ, IWM, SMH, XLV, XBI, VIX, USD, 10Y yield, Oil, Fed
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .schemas import MarketGateEntry, MarketState


@dataclass
class IndexSignal:
    """Directional signal for a single index/indicator."""

    symbol: str
    trend: str  # "up" / "down" / "range"
    vs_50dma: Optional[str] = None  # "above" / "below" / "at"
    vs_200dma: Optional[str] = None
    momentum: Optional[str] = None  # "strong" / "weak" / "diverging"


REQUIRED_INDICES = ["SPY", "QQQ", "IWM", "SMH", "XLV", "XBI"]

VIX_THRESHOLDS = {
    "low": 15.0,
    "elevated": 20.0,
    "high": 25.0,
    "extreme": 30.0,
}


def classify_vix(vix: float) -> str:
    """Classify VIX level into regime label."""
    if vix < VIX_THRESHOLDS["low"]:
        return "complacent"
    if vix < VIX_THRESHOLDS["elevated"]:
        return "normal"
    if vix < VIX_THRESHOLDS["high"]:
        return "elevated"
    if vix < VIX_THRESHOLDS["extreme"]:
        return "high"
    return "extreme"


def determine_market_state(
    spy_trend: str,
    qqq_trend: str,
    iwm_trend: str,
    smh_trend: str,
    vix_level: Optional[float] = None,
    us10y_trend: Optional[str] = None,
    fed_signal: Optional[str] = None,
) -> MarketState:
    """
    Determine overall market state from key indicators.

    Returns the appropriate MarketState enum value.
    """
    up_count = sum(1 for t in [spy_trend, qqq_trend, iwm_trend, smh_trend] if t == "up")
    down_count = sum(1 for t in [spy_trend, qqq_trend, iwm_trend, smh_trend] if t == "down")

    vix_regime = classify_vix(vix_level) if vix_level else "normal"

    if vix_regime in ("high", "extreme"):
        return MarketState.RISK_OFF

    if up_count >= 3 and vix_regime in ("complacent", "normal"):
        if iwm_trend == "up":
            return MarketState.RISK_ON
        return MarketState.SELECTIVE_BULL

    if down_count >= 3:
        return MarketState.RISK_OFF

    if up_count == 2 and down_count <= 1:
        return MarketState.SELECTIVE_BULL

    return MarketState.NEUTRAL_RANGE


def build_market_gate_entry(
    assessment_date: date,
    spy_trend: str = "range",
    qqq_trend: str = "range",
    iwm_trend: str = "range",
    smh_trend: str = "range",
    xlv_trend: str = "range",
    xbi_trend: str = "range",
    vix_level: Optional[float] = None,
    usd_index: Optional[float] = None,
    us10y_yield: Optional[float] = None,
    oil_price: Optional[float] = None,
    fed_signal: Optional[str] = None,
    notes: Optional[str] = None,
) -> MarketGateEntry:
    """Build a complete MarketGateEntry with state classification."""
    state = determine_market_state(
        spy_trend=spy_trend,
        qqq_trend=qqq_trend,
        iwm_trend=iwm_trend,
        smh_trend=smh_trend,
        vix_level=vix_level,
        fed_signal=fed_signal,
    )

    return MarketGateEntry(
        date=assessment_date,
        spy_trend=spy_trend,
        qqq_trend=qqq_trend,
        iwm_trend=iwm_trend,
        smh_trend=smh_trend,
        xlv_trend=xlv_trend,
        xbi_trend=xbi_trend,
        vix_level=vix_level,
        usd_index=usd_index,
        us10y_yield=us10y_yield,
        oil_price=oil_price,
        fed_signal=fed_signal,
        market_state=state,
        notes=notes,
    )


def get_position_guidance(state: MarketState) -> dict:
    """Return position sizing and strategy guidance based on market state."""
    guidance = {
        MarketState.RISK_ON: {
            "max_position": "standard",
            "strategy": "Aggressive S1/S2 entries, full-size positions allowed",
            "avoid": "Nothing specific - broad participation expected",
        },
        MarketState.SELECTIVE_BULL: {
            "max_position": "standard",
            "strategy": "Only leading sectors and relative strength names",
            "avoid": "Lagging sectors, low-RS names",
        },
        MarketState.NEUTRAL_RANGE: {
            "max_position": "half",
            "strategy": "Reduce exposure, wait for pullbacks and confirmations",
            "avoid": "Chasing breakouts, adding to losers",
        },
        MarketState.RISK_OFF: {
            "max_position": "small_or_none",
            "strategy": "No chasing, no low-liquidity small caps",
            "avoid": "All aggressive entries, speculative names",
        },
        MarketState.EVENT_ONLY: {
            "max_position": "small",
            "strategy": "Only clear catalyst-driven setups, small size",
            "avoid": "Non-catalyzed positions",
        },
    }
    return guidance.get(state, guidance[MarketState.NEUTRAL_RANGE])
