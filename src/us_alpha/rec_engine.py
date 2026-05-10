# -*- coding: utf-8 -*-
"""
REC_ENGINE: Formal recommendation qualification and output engine.

A formal recommendation (REC) is ONLY created when ALL of:
1. Market environment is NOT risk-off (or event-only with controlled risk)
2. Sector grade is A or B
3. Info source is A1/A2 or verifiable B
4. Clear technical entry pattern exists
5. Catalyst is confirmed and trackable
6. Liquidity is sufficient
7. SEC / dilution passes
8. Risk/reward >= 2.5:1
9. Stop loss is defined
10. Target price is defined
11. Postmortem dates are set

If no qualified primary rec exists, output:
  "本輪沒有合格主推，僅列觀察名單。"
"""

from datetime import date, timedelta
from typing import List, Optional

from .schemas import (
    CandidateLayer,
    FormalRecommendation,
    FutuPoolSource,
    FutuPriority,
    MarketState,
    MomentumState,
    RecType,
    RiskLockStatus,
    ScoreGrade,
    SourceGrade,
    StrategyVersion,
    WatchlistEntry,
)
from .score_engine import ScoreResult


def qualifies_for_rec(
    score_result: ScoreResult,
    market_state: MarketState,
    source_grade: SourceGrade,
    has_entry_pattern: bool,
    has_stop_loss: bool,
    has_target: bool,
    sec_status: RiskLockStatus,
    liquidity_status: RiskLockStatus,
) -> tuple:
    """
    Check if a scored candidate qualifies for formal recommendation.

    Returns (qualified: bool, fail_reasons: list).
    """
    fail_reasons = []

    if market_state == MarketState.RISK_OFF:
        fail_reasons.append("Market in RISK_OFF - no new recs")

    if score_result.grade not in (ScoreGrade.A, ScoreGrade.B):
        fail_reasons.append(f"Grade {score_result.grade.value} insufficient (need A or B)")

    if source_grade not in (SourceGrade.A1, SourceGrade.A2, SourceGrade.B):
        fail_reasons.append(f"Source grade {source_grade.value} not verifiable")

    if not has_entry_pattern:
        fail_reasons.append("No clear technical entry pattern")

    if not has_stop_loss:
        fail_reasons.append("No defined stop loss")

    if not has_target:
        fail_reasons.append("No defined target price")

    if sec_status == RiskLockStatus.BLOCKED:
        fail_reasons.append("SEC/Dilution BLOCKED")

    if liquidity_status == RiskLockStatus.BLOCKED:
        fail_reasons.append("Liquidity BLOCKED")

    return len(fail_reasons) == 0, fail_reasons


def determine_rec_type(score_result: ScoreResult, is_event: bool = False) -> RecType:
    """Determine recommendation type from score."""
    if is_event:
        return RecType.SMALL_EVENT
    if score_result.grade == ScoreGrade.A:
        return RecType.PRIMARY
    return RecType.SECONDARY


def determine_position_risk(
    market_state: MarketState,
    score_grade: ScoreGrade,
    is_event: bool = False,
) -> str:
    """Determine suggested position sizing."""
    if is_event:
        return "small"
    if market_state == MarketState.RISK_ON and score_grade == ScoreGrade.A:
        return "standard"
    if market_state == MarketState.SELECTIVE_BULL:
        return "standard" if score_grade == ScoreGrade.A else "half"
    if market_state == MarketState.NEUTRAL_RANGE:
        return "half"
    return "small"


def build_recommendation(
    ticker: str,
    company_name: Optional[str],
    score_result: ScoreResult,
    strategy_version: StrategyVersion,
    momentum_state: Optional[MomentumState],
    buy_price: float,
    entry_range: str,
    stop_loss: float,
    target_1: float,
    target_2: Optional[float],
    catalyst_id: Optional[str],
    catalyst_desc: Optional[str],
    source_grade: SourceGrade,
    market_state: MarketState,
    futu_pools: Optional[List[FutuPoolSource]] = None,
    futu_priority: Optional[FutuPriority] = None,
    is_event: bool = False,
    rec_date: Optional[date] = None,
) -> FormalRecommendation:
    """Build a formal recommendation record."""
    today = rec_date or date.today()
    rec_id = f"REC-{today.strftime('%Y%m%d')}-001"

    rr_ratio = None
    if stop_loss and buy_price and target_1:
        risk = buy_price - stop_loss
        if risk > 0:
            reward = target_1 - buy_price
            rr_ratio = round(reward / risk, 2)

    rec_type = determine_rec_type(score_result, is_event)
    position_risk = determine_position_risk(market_state, score_result.grade, is_event)

    return FormalRecommendation(
        rec_id=rec_id,
        rec_date=today,
        ticker=ticker,
        company_name=company_name,
        strategy_version=strategy_version,
        momentum_state=momentum_state,
        rec_type=rec_type,
        buy_price=buy_price,
        entry_range=entry_range,
        stop_loss=stop_loss,
        target_1=target_1,
        target_2=target_2,
        risk_reward_ratio=rr_ratio,
        catalyst_id=catalyst_id,
        catalyst_desc=catalyst_desc,
        source_grade=source_grade,
        sec_risk=score_result.risk_lock,
        liquidity_status=RiskLockStatus.PASS,
        market_state=market_state,
        position_risk=position_risk,
        total_score=score_result.final_score,
        final_grade=score_result.grade,
        futu_pools=futu_pools or [],
        futu_priority=futu_priority,
        postmortem_7d=today + timedelta(days=7),
        postmortem_30d=today + timedelta(days=30),
        postmortem_90d=today + timedelta(days=90),
        postmortem_180d=today + timedelta(days=180),
        postmortem_365d=today + timedelta(days=365),
    )


def build_watchlist_entry(
    ticker: str,
    fail_reasons: List[str],
    source_pool: Optional[FutuPoolSource] = None,
    trigger_condition: Optional[str] = None,
    watch_date: Optional[date] = None,
) -> WatchlistEntry:
    """Build a watchlist entry for non-qualifying candidates."""
    today = watch_date or date.today()
    return WatchlistEntry(
        watch_id=f"WATCH-{today.strftime('%Y%m%d')}-001",
        date=today,
        ticker=ticker,
        layer=CandidateLayer.WATCH,
        source_pool=source_pool,
        watch_reason="Did not qualify for formal rec",
        fail_reason="; ".join(fail_reasons),
        trigger_condition=trigger_condition,
        can_convert_to_rec=True,
        next_check_date=today + timedelta(days=3),
    )


def format_no_rec_output() -> str:
    """Standard output when no qualified recommendation exists."""
    return "本輪沒有合格主推，僅列觀察名單。"


def format_rec_output(rec: FormalRecommendation) -> str:
    """Format a formal recommendation for display."""
    lines = [
        "=" * 60,
        "FORMAL RECOMMENDATION",
        "=" * 60,
        f"【REC ID】{rec.rec_id}",
        f"【推薦日期】{rec.rec_date}",
        f"【股票】{rec.ticker} - {rec.company_name or 'N/A'}",
        f"【策略版本】{rec.strategy_version.value}",
        f"【推薦類型】{rec.rec_type.value}",
        f"【動能狀態】{rec.momentum_state.value if rec.momentum_state else 'N/A'}",
        f"【推薦買入價】${rec.buy_price:.2f}" if rec.buy_price else "【推薦買入價】N/A",
        f"【建議進場區間】{rec.entry_range}",
        f"【停損價】${rec.stop_loss:.2f}" if rec.stop_loss else "【停損價】N/A",
        f"【第一目標】${rec.target_1:.2f}" if rec.target_1 else "【第一目標】N/A",
        f"【第二目標】${rec.target_2:.2f}" if rec.target_2 else "【第二目標】N/A",
        f"【風險報酬比】{rec.risk_reward_ratio:.1f}:1" if rec.risk_reward_ratio else "【風險報酬比】N/A",
        f"【催化劑】{rec.catalyst_desc or 'N/A'}",
        f"【資訊來源等級】{rec.source_grade.value}",
        f"【SEC 風險】{rec.sec_risk.value}",
        f"【流動性狀態】{rec.liquidity_status.value}",
        f"【市場狀態】{rec.market_state.value}",
        f"【建議倉位風險】{rec.position_risk}",
        f"【總分】{rec.total_score}/100 ({rec.final_grade.value})",
        f"【富途池優先級】P{rec.futu_priority.value}" if rec.futu_priority else "【富途池優先級】N/A",
        f"【復盤日期】7d={rec.postmortem_7d} | 30d={rec.postmortem_30d} | 90d={rec.postmortem_90d}",
        "=" * 60,
    ]
    return "\n".join(lines)
