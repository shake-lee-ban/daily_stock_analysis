# -*- coding: utf-8 -*-
"""
SCORE_ENGINE: Scoring, grading, and recommendation qualification engine.

Standard output per evaluation:
- Main score (raw condition score)
- Risk deduction
- Risk lock status (pass/warning/blocked)
- Final score = main - deductions
- Final grade (A/B/C/D/F/P)
- Final action (primary_rec / recommend / observe / exclude / pending)

Grade rules:
- A: Primary recommendation candidate (score >= 80, no block)
- B: Recommendable (score >= 65, no block)
- C: Observation only (score >= 50)
- D: Do not recommend (score >= 35)
- F: Forbidden (blocked or score < 35)
- P: Pending verification
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .risk_engine import RiskAssessment
from .schemas import (
    CandidateLayer,
    FutuPriority,
    MomentumState,
    RiskLockStatus,
    ScoreAuditEntry,
    ScoreGrade,
    SectorGrade,
    SourceGrade,
    StrategyVersion,
)


@dataclass
class ScoreInput:
    """Input parameters for scoring a candidate."""

    ticker: str
    strategy_version: StrategyVersion = StrategyVersion.HIGH_ALPHA_V2_1

    # Sector & market
    sector_grade: Optional[SectorGrade] = None
    in_leading_sector: bool = False

    # Momentum & technical
    momentum_state: Optional[MomentumState] = None
    rs_rank: Optional[int] = None  # 0-100
    above_50dma: bool = True
    above_200dma: bool = True
    near_support: bool = False
    volume_confirmation: bool = False

    # Catalyst
    has_catalyst: bool = False
    catalyst_certainty: Optional[str] = None  # high/medium/low

    # Futu pools
    futu_priority: Optional[FutuPriority] = None

    # Fundamentals
    earnings_beat: bool = False
    revenue_growing: bool = False
    guidance_raised: bool = False

    # Source quality
    source_grade: SourceGrade = SourceGrade.A2

    # Risk assessment result
    risk_assessment: Optional[RiskAssessment] = None


@dataclass
class ScoreResult:
    """Output of the scoring engine."""

    ticker: str
    main_score: int = 0
    risk_deduction: int = 0
    risk_lock: RiskLockStatus = RiskLockStatus.PASS
    final_score: int = 0
    grade: ScoreGrade = ScoreGrade.P
    action: str = "pending"
    additions: List[str] = field(default_factory=list)
    deductions: List[str] = field(default_factory=list)
    pending_reasons: List[str] = field(default_factory=list)


def compute_main_score(inp: ScoreInput) -> tuple:
    """
    Compute the raw main score from positive factors.

    Returns (score, list of addition reasons).
    """
    score = 0
    additions = []

    # Sector strength (max 20)
    if inp.sector_grade == SectorGrade.A:
        score += 20
        additions.append("+20 A-grade sector (主線)")
    elif inp.sector_grade == SectorGrade.B:
        score += 15
        additions.append("+15 B-grade sector (強勢)")
    elif inp.sector_grade == SectorGrade.C:
        score += 8
        additions.append("+8 C-grade sector (觀察)")

    # Momentum state (max 20)
    if inp.momentum_state == MomentumState.S1:
        score += 20
        additions.append("+20 S1 initial breakout")
    elif inp.momentum_state == MomentumState.S2:
        score += 18
        additions.append("+18 S2 continuation")
    elif inp.momentum_state == MomentumState.S0_A:
        score += 10
        additions.append("+10 S0-A core stalking")

    # Relative strength (max 15)
    if inp.rs_rank is not None:
        if inp.rs_rank >= 90:
            score += 15
            additions.append(f"+15 RS rank {inp.rs_rank} (top decile)")
        elif inp.rs_rank >= 80:
            score += 12
            additions.append(f"+12 RS rank {inp.rs_rank}")
        elif inp.rs_rank >= 70:
            score += 8
            additions.append(f"+8 RS rank {inp.rs_rank}")

    # Catalyst (max 15)
    if inp.has_catalyst:
        if inp.catalyst_certainty == "high":
            score += 15
            additions.append("+15 High-certainty catalyst")
        elif inp.catalyst_certainty == "medium":
            score += 10
            additions.append("+10 Medium-certainty catalyst")
        else:
            score += 7
            additions.append("+7 Low-certainty catalyst")

    # Futu priority (max 10)
    if inp.futu_priority:
        priority_scores = {
            FutuPriority.P1: 10,
            FutuPriority.P2: 8,
            FutuPriority.P3: 6,
            FutuPriority.P4: 4,
            FutuPriority.P5: 2,
        }
        p_score = priority_scores.get(inp.futu_priority, 0)
        if p_score > 0:
            score += p_score
            additions.append(f"+{p_score} Futu priority P{inp.futu_priority.value}")

    # Technical confirmation (max 10)
    tech_score = 0
    if inp.above_50dma and inp.above_200dma:
        tech_score += 4
    if inp.near_support:
        tech_score += 3
    if inp.volume_confirmation:
        tech_score += 3
    if tech_score > 0:
        score += tech_score
        additions.append(f"+{tech_score} Technical confirmation")

    # Fundamentals (max 10)
    fund_score = 0
    if inp.earnings_beat:
        fund_score += 4
    if inp.revenue_growing:
        fund_score += 3
    if inp.guidance_raised:
        fund_score += 3
    if fund_score > 0:
        score += fund_score
        additions.append(f"+{fund_score} Fundamental strength")

    return score, additions


def determine_grade(final_score: int, risk_lock: RiskLockStatus, has_pending: bool = False) -> tuple:
    """Determine grade and action from final score and risk status."""
    if has_pending:
        return ScoreGrade.P, "pending"

    if risk_lock == RiskLockStatus.BLOCKED:
        return ScoreGrade.F, "blocked"

    if final_score >= 80:
        return ScoreGrade.A, "primary_rec"
    if final_score >= 65:
        return ScoreGrade.B, "recommend"
    if final_score >= 50:
        return ScoreGrade.C, "observe"
    if final_score >= 35:
        return ScoreGrade.D, "exclude"
    return ScoreGrade.F, "blocked"


def score_candidate(inp: ScoreInput) -> ScoreResult:
    """
    Full scoring pipeline for a single candidate stock.

    Combines main score computation, risk deductions, and grading.
    """
    result = ScoreResult(ticker=inp.ticker)

    # Check for Pending conditions
    pending_reasons = []
    if inp.source_grade in (SourceGrade.C, SourceGrade.R, SourceGrade.UNKNOWN):
        pending_reasons.append(f"Source grade {inp.source_grade.value} insufficient")
    if not inp.has_catalyst and inp.momentum_state not in (MomentumState.S1, MomentumState.S2):
        pending_reasons.append("No catalyst and not in active momentum state")

    if pending_reasons:
        result.pending_reasons = pending_reasons
        result.grade = ScoreGrade.P
        result.action = "pending"
        return result

    # Compute main score
    main_score, additions = compute_main_score(inp)
    result.main_score = main_score
    result.additions = additions

    # Apply risk deductions
    risk_deduction = 0
    deductions = []
    risk_lock = RiskLockStatus.PASS

    if inp.risk_assessment:
        risk_deduction = inp.risk_assessment.total_deduction
        risk_lock = inp.risk_assessment.overall_status
        for check in inp.risk_assessment.checks:
            if check.deduction > 0:
                deductions.append(f"-{check.deduction} {check.reason}")

    result.risk_deduction = risk_deduction
    result.deductions = deductions
    result.risk_lock = risk_lock

    # Final score
    result.final_score = max(0, main_score - risk_deduction)

    # Grade and action
    result.grade, result.action = determine_grade(result.final_score, risk_lock)

    return result


def build_score_audit(
    result: ScoreResult,
    strategy_version: StrategyVersion,
    linked_info_id: Optional[str] = None,
    linked_rec_id: Optional[str] = None,
    linked_cat_id: Optional[str] = None,
) -> ScoreAuditEntry:
    """Create audit trail entry from score result."""
    now = datetime.now()
    score_id = f"SCORE-{now.strftime('%Y%m%d')}-{result.ticker}-001"

    return ScoreAuditEntry(
        score_id=score_id,
        ticker=result.ticker,
        timestamp=now,
        linked_info_id=linked_info_id,
        linked_rec_id=linked_rec_id,
        linked_cat_id=linked_cat_id,
        strategy_version=strategy_version,
        original_score=result.main_score,
        additions=result.additions,
        deductions=result.deductions,
        risk_lock=result.risk_lock,
        final_score=result.final_score,
        final_grade=result.grade,
        enters_rec=(result.grade in (ScoreGrade.A, ScoreGrade.B)),
        enters_postmortem=(result.grade in (ScoreGrade.A, ScoreGrade.B)),
    )
