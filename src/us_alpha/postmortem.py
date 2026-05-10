# -*- coding: utf-8 -*-
"""
POSTMORTEM_ENGINE: Post-trade review and model evolution module.

Review cycles:
- 7 days: Short-term news effectiveness
- 30 days: Swing direction accuracy
- 90 days: Catalyst / earnings logic validation
- 180 days: Medium-term strategy effectiveness
- 365 days: Long-term model performance

Model correction discipline:
- Single failure does NOT trigger model change
- Repeated same-type errors -> adjust weights / gates
- Error rate > 30% -> mandatory model review
- High MFE but missed -> review exit rules
- Excessive MAE -> review entry and stop loss
- Overheated stocks frequently failing -> tighten S3 rules
- Info contamination -> strengthen INFO_GATE
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from .schemas import (
    MarketState,
    ModelChangeEntry,
    PostmortemEntry,
    PostmortemErrorType,
)


REVIEW_PERIODS = ["7d", "30d", "90d", "180d", "365d"]

MODEL_CORRECTION_THRESHOLD = 0.30  # 30% error rate triggers review


@dataclass
class PostmortemSummary:
    """Aggregate postmortem statistics."""

    period: str
    total_reviews: int = 0
    success_count: int = 0
    fail_count: int = 0
    partial_count: int = 0
    avg_mfe: Optional[float] = None
    avg_mae: Optional[float] = None
    error_type_distribution: Dict[str, int] = field(default_factory=dict)
    needs_model_review: bool = False

    @property
    def success_rate(self) -> float:
        if self.total_reviews == 0:
            return 0.0
        return self.success_count / self.total_reviews

    @property
    def error_rate(self) -> float:
        if self.total_reviews == 0:
            return 0.0
        return self.fail_count / self.total_reviews


def create_postmortem(
    rec_id: str,
    ticker: str,
    review_date: date,
    review_period: str,
    actual_performance_pct: Optional[float] = None,
    mfe: Optional[float] = None,
    mae: Optional[float] = None,
    market_state: Optional[MarketState] = None,
    error_type: Optional[PostmortemErrorType] = None,
    success_reason: Optional[str] = None,
    failure_reason: Optional[str] = None,
) -> PostmortemEntry:
    """Create a postmortem review entry."""
    needs_change = False
    if error_type and actual_performance_pct is not None and actual_performance_pct < -15:
        needs_change = True

    conclusion = None
    if actual_performance_pct is not None:
        if actual_performance_pct >= 10:
            conclusion = "Success - target reached or exceeded"
        elif actual_performance_pct >= 0:
            conclusion = "Partial success - positive but below target"
        elif actual_performance_pct >= -5:
            conclusion = "Minor loss - within acceptable range"
        else:
            conclusion = "Failure - significant loss or thesis invalidated"

    return PostmortemEntry(
        rec_id=rec_id,
        ticker=ticker,
        review_date=review_date,
        review_period=review_period,
        market_state_at_review=market_state,
        actual_performance_pct=actual_performance_pct,
        mfe=mfe,
        mae=mae,
        error_type=error_type,
        success_reason=success_reason,
        failure_reason=failure_reason,
        needs_model_change=needs_change,
        conclusion=conclusion,
    )


def classify_error(
    actual_pct: Optional[float],
    mfe: Optional[float],
    mae: Optional[float],
    catalyst_hit: bool = True,
    market_turned: bool = False,
    was_overheated: bool = False,
    info_was_contaminated: bool = False,
    timing_was_off: bool = False,
    chased_high: bool = False,
) -> Optional[PostmortemErrorType]:
    """Classify the type of error for a failed trade."""
    if actual_pct is not None and actual_pct >= 0:
        return None

    if info_was_contaminated:
        return PostmortemErrorType.INFO_ERROR
    if timing_was_off:
        return PostmortemErrorType.TIMING_ERROR
    if chased_high:
        return PostmortemErrorType.CHASING_ERROR
    if market_turned:
        return PostmortemErrorType.MARKET_TURN
    if was_overheated:
        return PostmortemErrorType.RISK_UNDERESTIMATE
    if not catalyst_hit:
        return PostmortemErrorType.CATALYST_MISS

    if mae is not None and mae < -20:
        return PostmortemErrorType.TECHNICAL_FAIL

    return PostmortemErrorType.RISK_UNDERESTIMATE


def compute_summary(entries: List[PostmortemEntry], period: str) -> PostmortemSummary:
    """Compute aggregate statistics for a review period."""
    period_entries = [e for e in entries if e.review_period == period]
    summary = PostmortemSummary(period=period, total_reviews=len(period_entries))

    if not period_entries:
        return summary

    for entry in period_entries:
        if entry.actual_performance_pct is not None:
            if entry.actual_performance_pct >= 10:
                summary.success_count += 1
            elif entry.actual_performance_pct >= 0:
                summary.partial_count += 1
            else:
                summary.fail_count += 1

        if entry.error_type:
            key = entry.error_type.value
            summary.error_type_distribution[key] = summary.error_type_distribution.get(key, 0) + 1

    mfe_values = [e.mfe for e in period_entries if e.mfe is not None]
    mae_values = [e.mae for e in period_entries if e.mae is not None]

    if mfe_values:
        summary.avg_mfe = sum(mfe_values) / len(mfe_values)
    if mae_values:
        summary.avg_mae = sum(mae_values) / len(mae_values)

    if summary.error_rate > MODEL_CORRECTION_THRESHOLD:
        summary.needs_model_review = True

    return summary


def suggest_model_corrections(summary: PostmortemSummary) -> List[str]:
    """Suggest model corrections based on postmortem patterns."""
    suggestions = []

    if not summary.needs_model_review:
        return suggestions

    dist = summary.error_type_distribution

    if dist.get(PostmortemErrorType.CHASING_ERROR.value, 0) >= 3:
        suggestions.append("Tighten S3 overheat rules - frequent chasing failures")

    if dist.get(PostmortemErrorType.INFO_ERROR.value, 0) >= 2:
        suggestions.append("Strengthen INFO_GATE - info contamination detected")

    if dist.get(PostmortemErrorType.CATALYST_MISS.value, 0) >= 3:
        suggestions.append("Raise catalyst certainty threshold for recommendations")

    if dist.get(PostmortemErrorType.MARKET_TURN.value, 0) >= 3:
        suggestions.append("Increase MARKET_GATE sensitivity for regime detection")

    if summary.avg_mfe and summary.avg_mae:
        if summary.avg_mfe > 15 and summary.success_rate < 0.5:
            suggestions.append("Review exit rules - high MFE but low capture rate")
        if abs(summary.avg_mae) > 10:
            suggestions.append("Review entry timing and stop-loss placement - excessive MAE")

    if dist.get(PostmortemErrorType.LIQUIDITY_MISJUDGE.value, 0) >= 2:
        suggestions.append("Tighten liquidity requirements in RISK_LOCK_ENGINE")

    return suggestions


def build_model_change(
    module_changed: str,
    change_description: str,
    rationale: str,
    triggered_by: Optional[str] = None,
) -> ModelChangeEntry:
    """Create a model change log entry."""
    return ModelChangeEntry(
        change_date=date.today(),
        triggered_by=triggered_by,
        module_changed=module_changed,
        change_description=change_description,
        rationale=rationale,
    )
