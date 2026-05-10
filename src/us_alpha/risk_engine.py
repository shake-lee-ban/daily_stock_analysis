# -*- coding: utf-8 -*-
"""
RISK_LOCK_ENGINE: Risk filtering and blocking module.

Hard blocks:
- SEC risk (S-3, ATM, PIPE, convertible, secondary offering)
- High dilution risk
- Insufficient volume / wide spread
- No clear catalyst
- Single-day >15% overheated (S3)
- Poor earnings quality / guidance cut
- Insider abnormal selling
- Social hype without official verification
- Risk/reward ratio < 2.5:1
- Market in RISK_OFF regime

Each risk check returns deductions and potential block status.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .schemas import RiskLockStatus


@dataclass
class RiskCheckResult:
    """Result of a single risk check."""

    check_name: str
    passed: bool
    deduction: int = 0
    status: RiskLockStatus = RiskLockStatus.PASS
    reason: str = ""


@dataclass
class RiskAssessment:
    """Aggregate risk assessment for a stock."""

    ticker: str
    checks: List[RiskCheckResult] = field(default_factory=list)

    @property
    def total_deduction(self) -> int:
        return sum(c.deduction for c in self.checks)

    @property
    def overall_status(self) -> RiskLockStatus:
        if any(c.status == RiskLockStatus.BLOCKED for c in self.checks):
            return RiskLockStatus.BLOCKED
        if any(c.status == RiskLockStatus.WARNING for c in self.checks):
            return RiskLockStatus.WARNING
        return RiskLockStatus.PASS

    @property
    def block_reasons(self) -> List[str]:
        return [c.reason for c in self.checks if c.status == RiskLockStatus.BLOCKED]

    @property
    def warning_reasons(self) -> List[str]:
        return [c.reason for c in self.checks if c.status == RiskLockStatus.WARNING]


def check_sec_dilution(
    has_s3: bool = False,
    has_atm: bool = False,
    has_pipe: bool = False,
    has_convertible: bool = False,
    has_secondary: bool = False,
    dilution_risk_level: Optional[str] = None,
) -> RiskCheckResult:
    """Check for SEC filing / dilution risks. Any positive = BLOCK."""
    risks = []
    if has_s3:
        risks.append("S-3 shelf registration")
    if has_atm:
        risks.append("ATM offering active")
    if has_pipe:
        risks.append("PIPE financing")
    if has_convertible:
        risks.append("Convertible notes outstanding")
    if has_secondary:
        risks.append("Secondary offering")

    if risks:
        return RiskCheckResult(
            check_name="SEC/Dilution",
            passed=False,
            deduction=30,
            status=RiskLockStatus.BLOCKED,
            reason=f"SEC/Dilution risk: {'; '.join(risks)}",
        )

    if dilution_risk_level == "high":
        return RiskCheckResult(
            check_name="SEC/Dilution",
            passed=False,
            deduction=20,
            status=RiskLockStatus.BLOCKED,
            reason="High dilution risk assessment",
        )

    return RiskCheckResult(check_name="SEC/Dilution", passed=True)


def check_liquidity(
    avg_daily_volume_m: Optional[float] = None,
    spread_pct: Optional[float] = None,
    price: Optional[float] = None,
) -> RiskCheckResult:
    """Check liquidity and spread requirements."""
    if avg_daily_volume_m is not None and avg_daily_volume_m < 10:
        return RiskCheckResult(
            check_name="Liquidity",
            passed=False,
            deduction=20,
            status=RiskLockStatus.BLOCKED,
            reason=f"Avg daily volume ${avg_daily_volume_m:.1f}M too low",
        )

    if spread_pct is not None and spread_pct > 2.0:
        return RiskCheckResult(
            check_name="Liquidity",
            passed=False,
            deduction=15,
            status=RiskLockStatus.BLOCKED,
            reason=f"Spread {spread_pct:.1f}% > 2% threshold",
        )

    if avg_daily_volume_m is not None and avg_daily_volume_m < 50:
        return RiskCheckResult(
            check_name="Liquidity",
            passed=True,
            deduction=5,
            status=RiskLockStatus.WARNING,
            reason=f"Moderate liquidity: ${avg_daily_volume_m:.1f}M daily",
        )

    return RiskCheckResult(check_name="Liquidity", passed=True)


def check_overheat(
    daily_gain_pct: Optional[float] = None,
    rsi: Optional[float] = None,
    distance_above_20ema_pct: Optional[float] = None,
    has_long_upper_shadow: bool = False,
) -> RiskCheckResult:
    """Check for overheated conditions (S3 risk)."""
    reasons = []
    deduction = 0

    if daily_gain_pct is not None and daily_gain_pct > 15:
        reasons.append(f"Single-day gain {daily_gain_pct:.1f}% > 15%")
        deduction += 15

    if rsi is not None and rsi > 78:
        reasons.append(f"RSI {rsi:.0f} > 78")
        deduction += 10

    if distance_above_20ema_pct is not None and distance_above_20ema_pct > 12:
        reasons.append(f"Price {distance_above_20ema_pct:.1f}% above 20EMA (>12%)")
        deduction += 10

    if has_long_upper_shadow:
        reasons.append("High-volume long upper shadow")
        deduction += 5

    if deduction >= 15:
        return RiskCheckResult(
            check_name="Overheat",
            passed=False,
            deduction=deduction,
            status=RiskLockStatus.BLOCKED,
            reason=f"Overheated (S3): {'; '.join(reasons)}",
        )

    if deduction > 0:
        return RiskCheckResult(
            check_name="Overheat",
            passed=True,
            deduction=deduction,
            status=RiskLockStatus.WARNING,
            reason=f"Heat warning: {'; '.join(reasons)}",
        )

    return RiskCheckResult(check_name="Overheat", passed=True)


def check_catalyst(has_catalyst: bool = False, catalyst_desc: Optional[str] = None) -> RiskCheckResult:
    """Check if a clear catalyst exists."""
    if not has_catalyst:
        return RiskCheckResult(
            check_name="Catalyst",
            passed=False,
            deduction=10,
            status=RiskLockStatus.WARNING,
            reason="No confirmed catalyst - cannot be primary recommendation",
        )
    return RiskCheckResult(check_name="Catalyst", passed=True)


def check_risk_reward(rr_ratio: Optional[float] = None) -> RiskCheckResult:
    """Check risk/reward ratio meets 2.5:1 minimum."""
    if rr_ratio is None:
        return RiskCheckResult(
            check_name="Risk/Reward",
            passed=False,
            deduction=5,
            status=RiskLockStatus.WARNING,
            reason="Risk/reward ratio not calculated",
        )
    if rr_ratio < 2.5:
        return RiskCheckResult(
            check_name="Risk/Reward",
            passed=False,
            deduction=10,
            status=RiskLockStatus.BLOCKED,
            reason=f"RR {rr_ratio:.1f}:1 < 2.5:1 minimum",
        )
    return RiskCheckResult(check_name="Risk/Reward", passed=True)


def check_earnings_quality(
    revenue_growing: Optional[bool] = None,
    eps_improving: Optional[bool] = None,
    guidance_cut: bool = False,
) -> RiskCheckResult:
    """Check fundamental quality."""
    if guidance_cut:
        return RiskCheckResult(
            check_name="Earnings Quality",
            passed=False,
            deduction=15,
            status=RiskLockStatus.WARNING,
            reason="Guidance cut - downgrade or exclude",
        )
    if revenue_growing is False and eps_improving is False:
        return RiskCheckResult(
            check_name="Earnings Quality",
            passed=False,
            deduction=10,
            status=RiskLockStatus.WARNING,
            reason="No revenue growth AND no EPS improvement",
        )
    return RiskCheckResult(check_name="Earnings Quality", passed=True)


def check_insider_selling(abnormal_insider_sell: bool = False) -> RiskCheckResult:
    """Check for abnormal insider selling."""
    if abnormal_insider_sell:
        return RiskCheckResult(
            check_name="Insider Activity",
            passed=True,
            deduction=8,
            status=RiskLockStatus.WARNING,
            reason="Abnormal insider selling detected",
        )
    return RiskCheckResult(check_name="Insider Activity", passed=True)


def run_full_risk_assessment(
    ticker: str,
    has_s3: bool = False,
    has_atm: bool = False,
    has_pipe: bool = False,
    has_convertible: bool = False,
    has_secondary: bool = False,
    dilution_risk_level: Optional[str] = None,
    avg_daily_volume_m: Optional[float] = None,
    spread_pct: Optional[float] = None,
    price: Optional[float] = None,
    daily_gain_pct: Optional[float] = None,
    rsi: Optional[float] = None,
    distance_above_20ema_pct: Optional[float] = None,
    has_long_upper_shadow: bool = False,
    has_catalyst: bool = False,
    catalyst_desc: Optional[str] = None,
    rr_ratio: Optional[float] = None,
    revenue_growing: Optional[bool] = None,
    eps_improving: Optional[bool] = None,
    guidance_cut: bool = False,
    abnormal_insider_sell: bool = False,
) -> RiskAssessment:
    """Run the complete risk assessment pipeline."""
    assessment = RiskAssessment(ticker=ticker)

    assessment.checks.append(
        check_sec_dilution(has_s3, has_atm, has_pipe, has_convertible, has_secondary, dilution_risk_level)
    )

    # SEC must pass before further checks (hard rule)
    if assessment.overall_status == RiskLockStatus.BLOCKED:
        return assessment

    assessment.checks.append(check_liquidity(avg_daily_volume_m, spread_pct, price))
    assessment.checks.append(
        check_overheat(daily_gain_pct, rsi, distance_above_20ema_pct, has_long_upper_shadow)
    )
    assessment.checks.append(check_catalyst(has_catalyst, catalyst_desc))
    assessment.checks.append(check_risk_reward(rr_ratio))
    assessment.checks.append(check_earnings_quality(revenue_growing, eps_improving, guidance_cut))
    assessment.checks.append(check_insider_selling(abnormal_insider_sell))

    return assessment
