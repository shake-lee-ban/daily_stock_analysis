# -*- coding: utf-8 -*-
"""
Data models for the US Alpha Selection System.

Covers all log tables:
- INFO_INBOX_LOG
- INFO_GATE_LOG
- MARKET_GATE_LOG
- SECTOR_RANK_LOG
- CATALYST_CALENDAR
- SCORE_AUDIT_LOG
- DAILY_RECOMMENDATION_DB
- FORMAL_REC_DB
- WATCHLIST_SIGNAL_LOG
- EXCLUSION_LOG
- HOLDING_MANAGEMENT_LOG
- POSTMORTEM_LOG
- MODEL_CHANGE_LOG
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────


class SourceGrade(str, Enum):
    """Information source grade."""

    A1 = "A1"  # SEC, FDA, official filings, Fed, official data
    A2 = "A2"  # Reuters, Bloomberg, CNBC, WSJ, mainstream media
    B = "B"  # Broker reports, industry reports, expert interviews
    C = "C"  # X, Reddit, YouTube, social posts
    R = "R"  # Rumors, unverified screenshots, single account leaks
    UNKNOWN = "UNKNOWN"


class InfoDirection(str, Enum):
    """Initial directional assessment of info."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


class InfoConclusion(str, Enum):
    """Processing conclusion for info."""

    ADOPT = "adopt"
    OBSERVE = "observe"
    ISOLATE = "isolate"
    EXCLUDE = "exclude"


class MarketState(str, Enum):
    """Overall market regime."""

    RISK_ON = "risk_on"  # 風險偏好強攻
    SELECTIVE_BULL = "selective_bull"  # 選擇性多頭
    NEUTRAL_RANGE = "neutral_range"  # 中性震盪
    RISK_OFF = "risk_off"  # 風險退潮
    EVENT_ONLY = "event_only"  # 事件限定


class SectorGrade(str, Enum):
    """Sector strength grade."""

    A = "A"  # 85-100, 主線
    B = "B"  # 75-84, 強勢
    C = "C"  # 60-74, 觀察
    WEAK = "WEAK"  # <60, 弱勢


class MomentumState(str, Enum):
    """Explosive momentum state machine states."""

    S0_A = "S0-A"  # Clean stalking / core track
    S0_B = "S0-B"  # Normal stalking
    S0_C = "S0-C"  # Noise / insufficient info
    S1 = "S1"  # Initial breakout confirmed
    S2 = "S2"  # Continuation strong
    S3 = "S3"  # Overheated
    S4 = "S4"  # Fading / invalidated


class CandidateLayer(str, Enum):
    """Stock candidate tier."""

    CORE = "core"  # 核心候選
    STANDARD = "standard"  # 標準候選
    EVENT = "event"  # 事件候選
    WATCH = "watch"  # 觀察名單
    PENDING = "pending"  # 待查名單
    EXCLUDED = "excluded"  # 排除名單


class ScoreGrade(str, Enum):
    """Final score grade."""

    A = "A"  # 主推候選
    B = "B"  # 可推薦
    C = "C"  # 觀察
    D = "D"  # 不推薦
    F = "F"  # 禁止推薦
    P = "P"  # Pending 待查


class RiskLockStatus(str, Enum):
    """Risk lock status."""

    PASS = "pass"
    WARNING = "warning"
    BLOCKED = "blocked"


class RecType(str, Enum):
    """Recommendation type."""

    PRIMARY = "primary"  # 主推
    SECONDARY = "secondary"  # 備選
    SMALL_EVENT = "small_event"  # 小倉事件
    CONTINUATION = "continuation"  # 續航


class StrategyVersion(str, Enum):
    """Strategy module version."""

    CORE_US_V2 = "CORE_US_v2.0"
    HIGH_ALPHA_V2_1 = "HIGH_ALPHA_LAUNCHPAD_US_v2.1"
    EXPLOSIVE_MOMENTUM_V2_1 = "EXPLOSIVE_MOMENTUM_US_v2.1"
    US_EQUITY_ALPHA_V3 = "US_Equity_Alpha_Selection_v3.0"
    SPEC_EVENT_V1 = "SPEC_EVENT_v1.0"


class CatalystType(str, Enum):
    """Catalyst event type."""

    EARNINGS = "earnings"
    FDA = "fda"
    CONTRACT = "contract"
    PRODUCT = "product"
    MA = "m_and_a"
    ANALYST_DAY = "analyst_day"
    GUIDANCE_RAISE = "guidance_raise"
    BUYBACK = "buyback"
    OTHER = "other"


class CatalystCertainty(str, Enum):
    """Certainty of catalyst."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HoldingAction(str, Enum):
    """Holding management action."""

    HOLD = "hold"
    REDUCE = "reduce"
    STOP_LOSS = "stop_loss"
    ADD = "add"
    WAIT = "wait"


class PostmortemErrorType(str, Enum):
    """Error type classification for postmortem."""

    INFO_ERROR = "info_error"  # 資訊錯誤
    TIMING_ERROR = "timing_error"  # 時間錯誤
    CHASING_ERROR = "chasing_error"  # 追高錯誤
    SECTOR_MISJUDGE = "sector_misjudge"  # 板塊錯判
    RISK_UNDERESTIMATE = "risk_underestimate"  # 風險低估
    CATALYST_MISS = "catalyst_miss"  # 催化劑落空
    MARKET_TURN = "market_turn"  # 大盤環境變差
    TECHNICAL_FAIL = "technical_fail"  # 技術面失效
    LIQUIDITY_MISJUDGE = "liquidity_misjudge"  # 流動性誤判
    SEC_DILUTION = "sec_dilution"  # SEC / 稀釋風險低估


class FutuPoolSource(str, Enum):
    """Futu screener pool source."""

    S0_STALK = "S0_stalk"  # 飆股1 / S0 潛伏池
    S1_B_WIDE = "S1-B_wide"  # 飆股4 / S1-B 寬版點火池
    S1_A_STRICT = "S1-A_strict"  # 飆股2 / S1-A 嚴格點火池
    S2_CONTINUATION = "S2_continuation"  # 飆股3 / S2 續航池


class FutuPriority(int, Enum):
    """Futu cross-pool priority level (1=highest)."""

    P1 = 1  # S1-B + S2
    P2 = 2  # S1-A + S2
    P3 = 3  # S1-A only
    P4 = 4  # S1-B only
    P5 = 5  # S0 only


# ─── Data Models ──────────────────────────────────────────────────────────────


class TimingState(str, Enum):
    """Timing gate state (v2.2)."""

    T0_CLEAR = "T0_clear"  # No event conflict, fully clear
    T1_CAUTION = "T1_caution"  # FOMC/OPEX week, reduce beta
    T2_RESTRICTED = "T2_restricted"  # CPI/NFP imminent, no new high-vol
    T3_EARNINGS_ZONE = "T3_earnings_zone"  # Within 3 days of earnings
    T4_EVENT_LOCKOUT = "T4_event_lockout"  # 0-2 days to catalyst
    T5_POST_EVENT = "T5_post_event"  # Event just occurred, judge reaction


class ExitTrigger(str, Enum):
    """Exit trigger type (v2.2)."""

    STOP_LOSS = "stop_loss"
    TIME_STOP = "time_stop"
    T1_HIT = "t1_hit"
    T2_HIT = "t2_hit"
    TRAILING_STOP = "trailing_stop"
    CATALYST_FAIL = "catalyst_fail"  # 利多出盡
    STRUCTURE_BREAK = "structure_break"  # 跌破20EMA+量增
    VWAP_BREAK = "vwap_break"
    MANUAL = "manual"


class InfoInboxEntry(BaseModel):
    """INFO_INBOX_LOG: Raw information input."""

    info_id: str = Field(..., description="INFO-YYYYMMDD-NNN")
    timestamp: datetime
    raw_content: str
    market: str = Field(default="us", description="us/hk/cn/crypto/macro")
    tickers: List[str] = Field(default_factory=list)
    initial_direction: InfoDirection = InfoDirection.UNCERTAIN
    impact_timeframe: Optional[str] = None  # 1d/1w/1m/1q
    needs_verification: bool = True
    enters_scoring: Optional[bool] = None
    enters_market_gate: Optional[bool] = None
    enters_risk_lock: Optional[bool] = None
    enters_sector_rank: Optional[bool] = None
    source_grade: SourceGrade = SourceGrade.UNKNOWN
    affected_module: Optional[str] = None
    conclusion: InfoConclusion = InfoConclusion.OBSERVE


class MarketGateEntry(BaseModel):
    """MARKET_GATE_LOG: Market environment snapshot."""

    date: date
    spy_trend: Optional[str] = None
    qqq_trend: Optional[str] = None
    iwm_trend: Optional[str] = None
    smh_trend: Optional[str] = None
    xlv_trend: Optional[str] = None
    xbi_trend: Optional[str] = None
    vix_level: Optional[float] = None
    usd_index: Optional[float] = None
    us10y_yield: Optional[float] = None
    oil_price: Optional[float] = None
    fed_signal: Optional[str] = None
    market_state: MarketState = MarketState.NEUTRAL_RANGE
    notes: Optional[str] = None


class SectorRankEntry(BaseModel):
    """SECTOR_RANK_LOG: Single sector rating."""

    date: date
    sector_name: str
    info_heat: int = Field(default=0, ge=0, le=20)
    fund_flow: int = Field(default=0, ge=0, le=20)
    relative_strength: int = Field(default=0, ge=0, le=20)
    catalyst_density: int = Field(default=0, ge=0, le=15)
    macro_alignment: int = Field(default=0, ge=0, le=15)
    sustainability: int = Field(default=0, ge=0, le=10)
    representative_tickers: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    @property
    def total_score(self) -> int:
        return (
            self.info_heat
            + self.fund_flow
            + self.relative_strength
            + self.catalyst_density
            + self.macro_alignment
            + self.sustainability
        )

    @property
    def grade(self) -> SectorGrade:
        s = self.total_score
        if s >= 85:
            return SectorGrade.A
        if s >= 75:
            return SectorGrade.B
        if s >= 60:
            return SectorGrade.C
        return SectorGrade.WEAK


class CatalystEntry(BaseModel):
    """CATALYST_CALENDAR: Catalyst event record."""

    catalyst_id: str = Field(..., description="CAT-YYYYMMDD-TICKER-NNN")
    ticker: str
    event_type: CatalystType
    expected_date: Optional[str] = None
    certainty: CatalystCertainty = CatalystCertainty.MEDIUM
    bull_scenario: Optional[str] = None
    bear_scenario: Optional[str] = None
    priced_in: Optional[str] = None  # yes/partial/no
    pre_event_strategy: Optional[str] = None
    postmortem_dates: List[str] = Field(default_factory=list)


class ScoreAuditEntry(BaseModel):
    """SCORE_AUDIT_LOG: Score change audit trail."""

    score_id: str = Field(..., description="SCORE-YYYYMMDD-TICKER-NNN")
    ticker: str
    timestamp: datetime
    linked_info_id: Optional[str] = None
    linked_rec_id: Optional[str] = None
    linked_cat_id: Optional[str] = None
    strategy_version: StrategyVersion = StrategyVersion.HIGH_ALPHA_V2_1
    original_score: Optional[int] = None
    additions: List[str] = Field(default_factory=list)
    deductions: List[str] = Field(default_factory=list)
    risk_lock: RiskLockStatus = RiskLockStatus.PASS
    final_score: Optional[int] = None
    final_grade: ScoreGrade = ScoreGrade.P
    enters_rec: bool = False
    enters_postmortem: bool = False
    outcome: Optional[str] = None  # pending/success/fail/partial


class FormalRecommendation(BaseModel):
    """FORMAL_REC_DB: Formal recommendation record."""

    rec_id: str = Field(..., description="REC-YYYYMMDD-NNN")
    rec_date: date
    ticker: str
    company_name: Optional[str] = None
    strategy_version: StrategyVersion = StrategyVersion.HIGH_ALPHA_V2_1
    momentum_state: Optional[MomentumState] = None
    rec_type: RecType = RecType.PRIMARY
    buy_price: Optional[float] = None
    entry_range: Optional[str] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    catalyst_id: Optional[str] = None
    catalyst_desc: Optional[str] = None
    source_grade: SourceGrade = SourceGrade.A2
    sec_risk: RiskLockStatus = RiskLockStatus.PASS
    liquidity_status: RiskLockStatus = RiskLockStatus.PASS
    market_state: MarketState = MarketState.SELECTIVE_BULL
    position_risk: Optional[str] = None  # standard/half/small/forbidden
    total_score: Optional[int] = None
    final_grade: ScoreGrade = ScoreGrade.A
    futu_pools: List[FutuPoolSource] = Field(default_factory=list)
    futu_priority: Optional[FutuPriority] = None
    postmortem_7d: Optional[date] = None
    postmortem_30d: Optional[date] = None
    postmortem_90d: Optional[date] = None
    postmortem_180d: Optional[date] = None
    postmortem_365d: Optional[date] = None
    mfe: Optional[float] = None  # Maximum Favorable Excursion
    mae: Optional[float] = None  # Maximum Adverse Excursion
    final_outcome: Optional[str] = None
    model_correction: Optional[str] = None


class WatchlistEntry(BaseModel):
    """WATCHLIST_SIGNAL_LOG: Watch list entry."""

    watch_id: str = Field(..., description="WATCH-YYYYMMDD-NNN")
    date: date
    ticker: str
    layer: CandidateLayer = CandidateLayer.WATCH
    source_pool: Optional[FutuPoolSource] = None
    watch_reason: Optional[str] = None
    fail_reason: Optional[str] = None
    info_needed: Optional[str] = None
    trigger_condition: Optional[str] = None
    invalidation_condition: Optional[str] = None
    can_convert_to_rec: bool = False
    next_check_date: Optional[date] = None


class ExclusionEntry(BaseModel):
    """EXCLUSION_LOG: Exclusion record."""

    ticker: str
    date: date
    reason: str
    category: Optional[str] = None  # sec/dilution/liquidity/overheated/etc
    duration: Optional[str] = None  # permanent/30d/until_catalyst/etc
    notes: Optional[str] = None


class HoldingEntry(BaseModel):
    """HOLDING_MANAGEMENT_LOG: Position management."""

    ticker: str
    timestamp: datetime
    action: HoldingAction
    avg_cost: Optional[float] = None
    current_price: Optional[float] = None
    shares: Optional[int] = None
    position_value: Optional[float] = None
    pnl_pct: Optional[float] = None
    pnl_amount: Optional[float] = None
    linked_rec_id: Optional[str] = None
    linked_score_id: Optional[str] = None
    original_buy_reason: Optional[str] = None
    key_support: Optional[float] = None
    alert_price: Optional[float] = None
    invalidation_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    can_add: Optional[str] = None  # yes/no/conditional
    add_condition: Optional[str] = None
    holding_days: Optional[int] = None
    market_impact: Optional[str] = None
    sector_impact: Optional[str] = None
    original_thesis_valid: bool = True
    next_action: Optional[str] = None  # hold/reduce/exit/add/watch
    notes: Optional[str] = None


class TimingGateEntry(BaseModel):
    """TIMING_GATE_LOG: Time dimension check (v2.2)."""

    ticker: str
    date: date
    timing_state: TimingState = TimingState.T0_CLEAR
    earnings_date: Optional[str] = None
    days_to_earnings: Optional[int] = None
    catalyst_date: Optional[str] = None
    days_to_catalyst: Optional[int] = None
    is_fomc_week: bool = False
    is_opex_week: bool = False
    is_cpi_nfp_week: bool = False
    is_earnings_season: bool = False
    timing_passed: bool = True
    timing_action: Optional[str] = None  # clear/reduce/delay/block
    notes: Optional[str] = None


class ExitPlanEntry(BaseModel):
    """EXIT_PLAN_LOG: Exit strategy record (v2.2)."""

    ticker: str
    rec_id: Optional[str] = None
    date: date
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    trailing_stop_rule: Optional[str] = None
    target_1: Optional[float] = None
    t1_exit_pct: str = "1/3"
    target_2: Optional[float] = None
    t2_exit_pct: str = "1/3"
    remainder_rule: Optional[str] = None  # e.g. "track 20EMA"
    time_stop_days: int = 10
    catalyst_fail_rule: Optional[str] = None
    structure_break_rule: Optional[str] = None
    profit_lock_rules: Optional[str] = None  # +5%->保本, +10%->+3%, etc
    actual_exit_trigger: Optional[ExitTrigger] = None
    actual_exit_price: Optional[float] = None
    actual_exit_date: Optional[date] = None
    notes: Optional[str] = None


class PostmortemEntry(BaseModel):
    """POSTMORTEM_LOG: Post-trade review."""

    rec_id: str
    ticker: str
    review_date: date
    review_period: str  # 7d/30d/90d/180d/365d
    market_state_at_review: Optional[MarketState] = None
    actual_performance_pct: Optional[float] = None
    mfe: Optional[float] = None
    mae: Optional[float] = None
    error_type: Optional[PostmortemErrorType] = None
    success_reason: Optional[str] = None
    failure_reason: Optional[str] = None
    needs_model_change: bool = False
    affected_module: Optional[str] = None
    conclusion: Optional[str] = None


class ModelChangeEntry(BaseModel):
    """MODEL_CHANGE_LOG: Model evolution record."""

    change_date: date
    triggered_by: Optional[str] = None  # postmortem ID or pattern
    module_changed: str
    change_description: str
    rationale: str
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    revert_plan: Optional[str] = None
