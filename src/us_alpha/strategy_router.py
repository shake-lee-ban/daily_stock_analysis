# -*- coding: utf-8 -*-
"""
STRATEGY_ROUTER: Routes candidates to the appropriate strategy module.

Available strategies:
- CORE_US_v2.0: Mainstream strong stocks (earnings revision, leading themes, RS, pullback)
- HIGH_ALPHA_LAUNCHPAD_US_v2.1: High-return scanning master controller
- EXPLOSIVE_MOMENTUM_US_v2.1: Explosive momentum state machine (S0-S4)
- SPEC_EVENT_v1.0: Event-driven biotech, special catalysts
- US_Equity_Alpha_Selection_v3.0: Large-cap quality / rotation (auxiliary)
"""

from dataclasses import dataclass
from typing import List, Optional

from .schemas import (
    CandidateLayer,
    FutuPoolSource,
    FutuPriority,
    MarketState,
    MomentumState,
    SectorGrade,
    StrategyVersion,
)


@dataclass
class CandidateStock:
    """A stock candidate with routing metadata."""

    ticker: str
    company_name: Optional[str] = None
    futu_pools: Optional[List[FutuPoolSource]] = None
    futu_priority: Optional[FutuPriority] = None
    momentum_state: Optional[MomentumState] = None
    sector: Optional[str] = None
    sector_grade: Optional[SectorGrade] = None
    market_cap_b: Optional[float] = None  # billions USD
    avg_daily_volume_m: Optional[float] = None  # millions USD
    price: Optional[float] = None
    above_50dma: Optional[bool] = None
    above_200dma: Optional[bool] = None
    has_earnings_catalyst: bool = False
    has_event_catalyst: bool = False
    rs_rank: Optional[int] = None  # 0-100


# ─── Futu Four-Pool Cross-Reference ──────────────────────────────────────────


def compute_futu_priority(pools: List[FutuPoolSource]) -> Optional[FutuPriority]:
    """Determine priority from pool cross-appearance."""
    pool_set = set(pools)

    if FutuPoolSource.S1_B_WIDE in pool_set and FutuPoolSource.S2_CONTINUATION in pool_set:
        return FutuPriority.P1
    if FutuPoolSource.S1_A_STRICT in pool_set and FutuPoolSource.S2_CONTINUATION in pool_set:
        return FutuPriority.P2
    if FutuPoolSource.S1_A_STRICT in pool_set:
        return FutuPriority.P3
    if FutuPoolSource.S1_B_WIDE in pool_set:
        return FutuPriority.P4
    if FutuPoolSource.S0_STALK in pool_set:
        return FutuPriority.P5
    return None


# ─── CORE_US_v2.0 Eligibility ────────────────────────────────────────────────


def check_core_us_eligibility(stock: CandidateStock) -> tuple:
    """
    Check if stock qualifies for CORE_US_v2.0 strategy.

    Returns (eligible: bool, reasons: list of pass/fail strings).
    """
    reasons = []
    eligible = True

    if stock.price is not None and stock.price < 20:
        reasons.append("FAIL: Price < $20")
        eligible = False

    if stock.market_cap_b is not None and stock.market_cap_b < 5:
        reasons.append("FAIL: Market cap < $5B")
        eligible = False

    if stock.avg_daily_volume_m is not None and stock.avg_daily_volume_m < 100:
        reasons.append("FAIL: 20d avg turnover < $100M")
        eligible = False

    if stock.above_50dma is False:
        reasons.append("FAIL: Below 50DMA")
        eligible = False

    if stock.above_200dma is False:
        reasons.append("FAIL: Below 200DMA")
        eligible = False

    if not stock.has_earnings_catalyst:
        reasons.append("WARN: No earnings catalyst confirmed")

    if eligible:
        reasons.append("PASS: Meets CORE_US_v2.0 minimum criteria")

    return eligible, reasons


# ─── HIGH_ALPHA_LAUNCHPAD_US_v2.1 Checks ─────────────────────────────────────


def check_high_alpha_eligibility(stock: CandidateStock) -> tuple:
    """
    Check if stock qualifies for HIGH_ALPHA_LAUNCHPAD_US_v2.1.

    Hard rules:
    - SEC must pass (checked separately by risk_engine)
    - Catalyst must exist
    - RS >= 70
    - Spread <= 2% (checked by risk_engine)
    - RR >= 2.5:1 (checked by score_engine)
    - Not S3 overheated
    - Not S4 invalidated
    """
    reasons = []
    eligible = True

    if stock.momentum_state == MomentumState.S3:
        reasons.append("FAIL: S3 overheated - do not chase")
        eligible = False

    if stock.momentum_state == MomentumState.S4:
        reasons.append("FAIL: S4 invalidated - remove/block")
        eligible = False

    if stock.momentum_state == MomentumState.S0_C:
        reasons.append("FAIL: S0-C noise/insufficient info")
        eligible = False

    if stock.rs_rank is not None and stock.rs_rank < 70:
        reasons.append(f"FAIL: RS rank {stock.rs_rank} < 70")
        eligible = False

    if not (stock.has_earnings_catalyst or stock.has_event_catalyst):
        reasons.append("FAIL: No confirmed catalyst")
        eligible = False

    if eligible:
        reasons.append("PASS: Meets HIGH_ALPHA_v2.1 criteria")

    return eligible, reasons


# ─── Strategy Routing ─────────────────────────────────────────────────────────


def route_strategy(
    stock: CandidateStock,
    market_state: MarketState,
) -> tuple:
    """
    Route a stock to the best-fit strategy module.

    Returns (strategy_version, candidate_layer, routing_notes).
    """
    notes = []

    if market_state == MarketState.RISK_OFF:
        if not stock.has_event_catalyst:
            return StrategyVersion.CORE_US_V2, CandidateLayer.EXCLUDED, ["Market RISK_OFF, no catalyst"]

    if stock.has_event_catalyst and stock.sector and "biotech" in stock.sector.lower():
        notes.append("Biotech event candidate -> SPEC_EVENT_v1.0")
        return StrategyVersion.SPEC_EVENT_V1, CandidateLayer.EVENT, notes

    ha_eligible, ha_reasons = check_high_alpha_eligibility(stock)
    if ha_eligible:
        if stock.futu_priority and stock.futu_priority.value <= 2:
            notes.append(f"High-alpha eligible, Futu P{stock.futu_priority.value}")
            return StrategyVersion.HIGH_ALPHA_V2_1, CandidateLayer.CORE, notes
        notes.append("High-alpha eligible")
        return StrategyVersion.HIGH_ALPHA_V2_1, CandidateLayer.STANDARD, notes

    core_eligible, core_reasons = check_core_us_eligibility(stock)
    if core_eligible:
        notes.extend(core_reasons)
        return StrategyVersion.CORE_US_V2, CandidateLayer.STANDARD, notes

    if stock.momentum_state in (MomentumState.S0_A, MomentumState.S0_B):
        notes.append("Stalking phase, observation only")
        return StrategyVersion.HIGH_ALPHA_V2_1, CandidateLayer.WATCH, notes

    notes.append("Does not meet any strategy criteria")
    return StrategyVersion.CORE_US_V2, CandidateLayer.PENDING, notes
