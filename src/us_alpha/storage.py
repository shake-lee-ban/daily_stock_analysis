# -*- coding: utf-8 -*-
"""
US Alpha Selection System - SQLite Storage Layer.

Provides persistent storage for all system logs:
- INFO_INBOX_LOG
- MARKET_GATE_LOG
- SECTOR_RANK_LOG
- CATALYST_CALENDAR
- SCORE_AUDIT_LOG
- FORMAL_REC_DB
- WATCHLIST_SIGNAL_LOG
- EXCLUSION_LOG
- HOLDING_MANAGEMENT_LOG
- POSTMORTEM_LOG
- MODEL_CHANGE_LOG
- TRADE_PLAN_LOG (v2.2)
- REGIME_MEMORY_LOG (v2.5)

Default DB path: ~/Desktop/us_alpha_db/us_alpha.db
Configurable via environment variable US_ALPHA_DB_PATH.
"""

import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import (
    CatalystEntry,
    ExclusionEntry,
    FormalRecommendation,
    HoldingEntry,
    InfoInboxEntry,
    MarketGateEntry,
    ModelChangeEntry,
    PostmortemEntry,
    ScoreAuditEntry,
    SectorRankEntry,
    WatchlistEntry,
)


def _default_db_path() -> Path:
    """Return default database path: ~/Desktop/us_alpha_db/us_alpha.db"""
    env_path = os.environ.get("US_ALPHA_DB_PATH")
    if env_path:
        return Path(env_path)
    return Path.home() / "Desktop" / "us_alpha_db" / "us_alpha.db"


def _serialize(obj: Any) -> str:
    """Serialize a pydantic model or dict to JSON string."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump(mode="json")
    elif isinstance(obj, dict):
        data = obj
    else:
        data = str(obj)
    return json.dumps(data, ensure_ascii=False, default=str)


def _deserialize(json_str: str) -> Dict:
    """Deserialize a JSON string back to dict."""
    return json.loads(json_str)


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS info_inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    info_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    market TEXT DEFAULT 'us',
    tickers TEXT,
    source_grade TEXT,
    initial_direction TEXT,
    enters_scoring INTEGER,
    enters_market_gate INTEGER,
    enters_risk_lock INTEGER,
    enters_sector_rank INTEGER,
    conclusion TEXT,
    raw_content TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS market_gate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    market_state TEXT NOT NULL,
    spy_trend TEXT,
    qqq_trend TEXT,
    iwm_trend TEXT,
    smh_trend TEXT,
    vix_level REAL,
    us10y_yield REAL,
    notes TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS sector_rank (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    total_score INTEGER,
    grade TEXT,
    representative_tickers TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS catalyst_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalyst_id TEXT UNIQUE NOT NULL,
    ticker TEXT NOT NULL,
    event_type TEXT,
    expected_date TEXT,
    certainty TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS score_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    score_id TEXT UNIQUE NOT NULL,
    ticker TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    strategy_version TEXT,
    original_score INTEGER,
    final_score INTEGER,
    final_grade TEXT,
    risk_lock TEXT,
    enters_rec INTEGER DEFAULT 0,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS formal_rec (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id TEXT UNIQUE NOT NULL,
    rec_date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    company_name TEXT,
    strategy_version TEXT,
    momentum_state TEXT,
    rec_type TEXT,
    buy_price REAL,
    stop_loss REAL,
    target_1 REAL,
    target_2 REAL,
    risk_reward_ratio REAL,
    final_grade TEXT,
    total_score INTEGER,
    market_state TEXT,
    position_risk TEXT,
    futu_priority TEXT,
    mfe REAL,
    mae REAL,
    final_outcome TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id TEXT UNIQUE NOT NULL,
    date TEXT NOT NULL,
    ticker TEXT NOT NULL,
    layer TEXT,
    watch_reason TEXT,
    fail_reason TEXT,
    trigger_condition TEXT,
    can_convert_to_rec INTEGER DEFAULT 0,
    next_check_date TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS exclusion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    reason TEXT NOT NULL,
    category TEXT,
    duration TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS holding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    avg_cost REAL,
    current_price REAL,
    shares INTEGER,
    position_value REAL,
    pnl_pct REAL,
    linked_rec_id TEXT,
    original_buy_reason TEXT,
    alert_price REAL,
    invalidation_price REAL,
    stop_loss REAL,
    target_1 REAL,
    target_2 REAL,
    can_add TEXT,
    add_condition TEXT,
    holding_days INTEGER,
    original_thesis_valid INTEGER DEFAULT 1,
    next_action TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS timing_gate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    timing_state TEXT DEFAULT 'T0_clear',
    earnings_date TEXT,
    days_to_earnings INTEGER,
    catalyst_date TEXT,
    days_to_catalyst INTEGER,
    is_fomc_week INTEGER DEFAULT 0,
    is_opex_week INTEGER DEFAULT 0,
    is_cpi_nfp_week INTEGER DEFAULT 0,
    is_earnings_season INTEGER DEFAULT 0,
    timing_passed INTEGER DEFAULT 1,
    timing_action TEXT,
    notes TEXT,
    full_json TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS exit_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    rec_id TEXT,
    date TEXT NOT NULL,
    entry_price REAL,
    stop_loss REAL,
    trailing_stop_rule TEXT,
    target_1 REAL,
    t1_exit_pct TEXT DEFAULT '1/3',
    target_2 REAL,
    t2_exit_pct TEXT DEFAULT '1/3',
    remainder_rule TEXT,
    time_stop_days INTEGER DEFAULT 10,
    catalyst_fail_rule TEXT,
    structure_break_rule TEXT,
    profit_lock_rules TEXT,
    actual_exit_trigger TEXT,
    actual_exit_price REAL,
    actual_exit_date TEXT,
    notes TEXT,
    full_json TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS postmortem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    review_date TEXT NOT NULL,
    review_period TEXT NOT NULL,
    actual_performance_pct REAL,
    mfe REAL,
    mae REAL,
    error_type TEXT,
    needs_model_change INTEGER DEFAULT 0,
    conclusion TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS model_change (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_date TEXT NOT NULL,
    module_changed TEXT NOT NULL,
    change_description TEXT NOT NULL,
    rationale TEXT,
    triggered_by TEXT,
    full_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS trade_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id TEXT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    plan_text TEXT NOT NULL,
    strategy_version TEXT,
    market_state TEXT,
    entry_trigger TEXT,
    stop_loss REAL,
    target_1 REAL,
    target_2 REAL,
    position_size TEXT,
    timing_gate TEXT,
    exit_rules TEXT,
    counter_thesis TEXT,
    full_json TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS regime_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regime_id TEXT,
    market_state TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    trigger_reason TEXT,
    spy_state TEXT,
    qqq_state TEXT,
    vix_change TEXT,
    recommendations_during TEXT,
    outcomes TEXT,
    lessons TEXT,
    full_json TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_info_date ON info_inbox(timestamp);
CREATE INDEX IF NOT EXISTS idx_info_ticker ON info_inbox(tickers);
CREATE INDEX IF NOT EXISTS idx_market_date ON market_gate(date);
CREATE INDEX IF NOT EXISTS idx_sector_date ON sector_rank(date);
CREATE INDEX IF NOT EXISTS idx_catalyst_ticker ON catalyst_calendar(ticker);
CREATE INDEX IF NOT EXISTS idx_score_ticker ON score_audit(ticker);
CREATE INDEX IF NOT EXISTS idx_rec_ticker ON formal_rec(ticker);
CREATE INDEX IF NOT EXISTS idx_rec_date ON formal_rec(rec_date);
CREATE INDEX IF NOT EXISTS idx_watch_ticker ON watchlist(ticker);
CREATE INDEX IF NOT EXISTS idx_holding_ticker ON holding(ticker);
CREATE INDEX IF NOT EXISTS idx_postmortem_rec ON postmortem(rec_id);
CREATE INDEX IF NOT EXISTS idx_trade_plan_ticker ON trade_plan(ticker);
CREATE INDEX IF NOT EXISTS idx_timing_ticker ON timing_gate(ticker);
CREATE INDEX IF NOT EXISTS idx_timing_date ON timing_gate(date);
CREATE INDEX IF NOT EXISTS idx_exit_ticker ON exit_plan(ticker);
CREATE INDEX IF NOT EXISTS idx_exit_rec ON exit_plan(rec_id);
"""


class AlphaDB:
    """
    SQLite-based storage for the US Alpha Selection System.

    Usage:
        db = AlphaDB()  # auto-creates DB on Desktop
        db.save_info(info_entry)
        db.save_rec(rec_entry)
        results = db.query_recs(ticker="AVGO")
        db.close()
    """

    def __init__(self, db_path: Optional[str] = None):
        path = Path(db_path) if db_path else _default_db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    @property
    def db_path(self) -> str:
        return str(self._path)

    def close(self):
        if self._conn:
            self._conn.close()

    # ─── Save Methods ─────────────────────────────────────────────────────

    def save_info(self, entry: InfoInboxEntry) -> int:
        """Save an INFO_INBOX entry."""
        cur = self._conn.execute(
            """INSERT OR REPLACE INTO info_inbox
            (info_id, timestamp, market, tickers, source_grade, initial_direction,
             enters_scoring, conclusion, raw_content, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.info_id,
                entry.timestamp.isoformat(),
                entry.market,
                json.dumps(entry.tickers),
                entry.source_grade.value,
                entry.initial_direction.value,
                1 if entry.enters_scoring else 0,
                entry.conclusion.value,
                entry.raw_content[:500],
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_market_gate(self, entry: MarketGateEntry) -> int:
        """Save a MARKET_GATE entry."""
        cur = self._conn.execute(
            """INSERT INTO market_gate
            (date, market_state, spy_trend, qqq_trend, iwm_trend, smh_trend,
             vix_level, us10y_yield, notes, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(entry.date),
                entry.market_state.value,
                entry.spy_trend,
                entry.qqq_trend,
                entry.iwm_trend,
                entry.smh_trend,
                entry.vix_level,
                entry.us10y_yield,
                entry.notes,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_sector_rank(self, entry: SectorRankEntry) -> int:
        """Save a SECTOR_RANK entry."""
        cur = self._conn.execute(
            """INSERT INTO sector_rank
            (date, sector_name, total_score, grade, representative_tickers, full_json)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(entry.date),
                entry.sector_name,
                entry.total_score,
                entry.grade.value,
                json.dumps(entry.representative_tickers),
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_catalyst(self, entry: CatalystEntry) -> int:
        """Save a CATALYST_CALENDAR entry."""
        cur = self._conn.execute(
            """INSERT OR REPLACE INTO catalyst_calendar
            (catalyst_id, ticker, event_type, expected_date, certainty, full_json)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                entry.catalyst_id,
                entry.ticker,
                entry.event_type.value,
                entry.expected_date,
                entry.certainty.value,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_score_audit(self, entry: ScoreAuditEntry) -> int:
        """Save a SCORE_AUDIT entry."""
        cur = self._conn.execute(
            """INSERT OR REPLACE INTO score_audit
            (score_id, ticker, timestamp, strategy_version, original_score,
             final_score, final_grade, risk_lock, enters_rec, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.score_id,
                entry.ticker,
                entry.timestamp.isoformat(),
                entry.strategy_version.value,
                entry.original_score,
                entry.final_score,
                entry.final_grade.value,
                entry.risk_lock.value,
                1 if entry.enters_rec else 0,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_rec(self, entry: FormalRecommendation) -> int:
        """Save a FORMAL_REC entry."""
        cur = self._conn.execute(
            """INSERT OR REPLACE INTO formal_rec
            (rec_id, rec_date, ticker, company_name, strategy_version, momentum_state,
             rec_type, buy_price, stop_loss, target_1, target_2, risk_reward_ratio,
             final_grade, total_score, market_state, position_risk, futu_priority,
             mfe, mae, final_outcome, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.rec_id,
                str(entry.rec_date),
                entry.ticker,
                entry.company_name,
                entry.strategy_version.value,
                entry.momentum_state.value if entry.momentum_state else None,
                entry.rec_type.value,
                entry.buy_price,
                entry.stop_loss,
                entry.target_1,
                entry.target_2,
                entry.risk_reward_ratio,
                entry.final_grade.value,
                entry.total_score,
                entry.market_state.value,
                entry.position_risk,
                f"P{entry.futu_priority.value}" if entry.futu_priority else None,
                entry.mfe,
                entry.mae,
                entry.final_outcome,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_watchlist(self, entry: WatchlistEntry) -> int:
        """Save a WATCHLIST entry."""
        cur = self._conn.execute(
            """INSERT OR REPLACE INTO watchlist
            (watch_id, date, ticker, layer, watch_reason, fail_reason,
             trigger_condition, can_convert_to_rec, next_check_date, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.watch_id,
                str(entry.date),
                entry.ticker,
                entry.layer.value,
                entry.watch_reason,
                entry.fail_reason,
                entry.trigger_condition,
                1 if entry.can_convert_to_rec else 0,
                str(entry.next_check_date) if entry.next_check_date else None,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_exclusion(self, entry: ExclusionEntry) -> int:
        """Save an EXCLUSION entry."""
        cur = self._conn.execute(
            """INSERT INTO exclusion
            (ticker, date, reason, category, duration, full_json)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                entry.ticker,
                str(entry.date),
                entry.reason,
                entry.category,
                entry.duration,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_holding(self, entry: HoldingEntry) -> int:
        """Save a HOLDING entry."""
        cur = self._conn.execute(
            """INSERT INTO holding
            (ticker, timestamp, action, avg_cost, current_price, shares,
             position_value, pnl_pct, linked_rec_id, original_buy_reason,
             alert_price, invalidation_price, stop_loss, target_1, target_2,
             can_add, add_condition, holding_days, original_thesis_valid,
             next_action, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.ticker,
                entry.timestamp.isoformat(),
                entry.action.value,
                entry.avg_cost,
                entry.current_price,
                entry.shares,
                entry.position_value,
                entry.pnl_pct,
                entry.linked_rec_id,
                entry.original_buy_reason,
                entry.alert_price,
                entry.invalidation_price,
                entry.stop_loss,
                entry.target_1,
                entry.target_2,
                entry.can_add,
                entry.add_condition,
                entry.holding_days,
                1 if entry.original_thesis_valid else 0,
                entry.next_action,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_timing_gate(self, entry) -> int:
        """Save a TIMING_GATE entry (v2.2)."""
        cur = self._conn.execute(
            """INSERT INTO timing_gate
            (ticker, date, timing_state, earnings_date, days_to_earnings,
             catalyst_date, days_to_catalyst, is_fomc_week, is_opex_week,
             is_cpi_nfp_week, is_earnings_season, timing_passed, timing_action,
             notes, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.ticker,
                str(entry.date),
                entry.timing_state.value if hasattr(entry.timing_state, 'value') else entry.timing_state,
                entry.earnings_date,
                entry.days_to_earnings,
                entry.catalyst_date,
                entry.days_to_catalyst,
                1 if entry.is_fomc_week else 0,
                1 if entry.is_opex_week else 0,
                1 if entry.is_cpi_nfp_week else 0,
                1 if entry.is_earnings_season else 0,
                1 if entry.timing_passed else 0,
                entry.timing_action,
                entry.notes,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_exit_plan(self, entry) -> int:
        """Save an EXIT_PLAN entry (v2.2)."""
        cur = self._conn.execute(
            """INSERT INTO exit_plan
            (ticker, rec_id, date, entry_price, stop_loss, trailing_stop_rule,
             target_1, t1_exit_pct, target_2, t2_exit_pct, remainder_rule,
             time_stop_days, catalyst_fail_rule, structure_break_rule,
             profit_lock_rules, actual_exit_trigger, actual_exit_price,
             actual_exit_date, notes, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.ticker,
                entry.rec_id,
                str(entry.date),
                entry.entry_price,
                entry.stop_loss,
                entry.trailing_stop_rule,
                entry.target_1,
                entry.t1_exit_pct,
                entry.target_2,
                entry.t2_exit_pct,
                entry.remainder_rule,
                entry.time_stop_days,
                entry.catalyst_fail_rule,
                entry.structure_break_rule,
                entry.profit_lock_rules,
                entry.actual_exit_trigger.value if entry.actual_exit_trigger and hasattr(entry.actual_exit_trigger, 'value') else None,
                entry.actual_exit_price,
                str(entry.actual_exit_date) if entry.actual_exit_date else None,
                entry.notes,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_postmortem(self, entry: PostmortemEntry) -> int:
        """Save a POSTMORTEM entry."""
        cur = self._conn.execute(
            """INSERT INTO postmortem
            (rec_id, ticker, review_date, review_period, actual_performance_pct,
             mfe, mae, error_type, needs_model_change, conclusion, full_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.rec_id,
                entry.ticker,
                str(entry.review_date),
                entry.review_period,
                entry.actual_performance_pct,
                entry.mfe,
                entry.mae,
                entry.error_type.value if entry.error_type else None,
                1 if entry.needs_model_change else 0,
                entry.conclusion,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_model_change(self, entry: ModelChangeEntry) -> int:
        """Save a MODEL_CHANGE entry."""
        cur = self._conn.execute(
            """INSERT INTO model_change
            (change_date, module_changed, change_description, rationale, triggered_by, full_json)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(entry.change_date),
                entry.module_changed,
                entry.change_description,
                entry.rationale,
                entry.triggered_by,
                _serialize(entry),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_trade_plan(
        self,
        ticker: str,
        plan_text: str,
        rec_id: Optional[str] = None,
        strategy_version: Optional[str] = None,
        market_state: Optional[str] = None,
        entry_trigger: Optional[str] = None,
        stop_loss: Optional[float] = None,
        target_1: Optional[float] = None,
        target_2: Optional[float] = None,
        position_size: Optional[str] = None,
        timing_gate: Optional[str] = None,
        exit_rules: Optional[str] = None,
        counter_thesis: Optional[str] = None,
    ) -> int:
        """Save a TRADE_PLAN (v2.2)."""
        cur = self._conn.execute(
            """INSERT INTO trade_plan
            (rec_id, ticker, date, plan_text, strategy_version, market_state,
             entry_trigger, stop_loss, target_1, target_2, position_size,
             timing_gate, exit_rules, counter_thesis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rec_id,
                ticker,
                str(date.today()),
                plan_text,
                strategy_version,
                market_state,
                entry_trigger,
                stop_loss,
                target_1,
                target_2,
                position_size,
                timing_gate,
                exit_rules,
                counter_thesis,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_regime(
        self,
        market_state: str,
        trigger_reason: str,
        start_date: Optional[str] = None,
        spy_state: Optional[str] = None,
        qqq_state: Optional[str] = None,
        vix_change: Optional[str] = None,
        lessons: Optional[str] = None,
    ) -> int:
        """Save a REGIME_MEMORY entry (v2.5)."""
        regime_id = f"REGIME-{date.today().strftime('%Y%m%d')}-001"
        cur = self._conn.execute(
            """INSERT INTO regime_memory
            (regime_id, market_state, start_date, trigger_reason,
             spy_state, qqq_state, vix_change, lessons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                regime_id,
                market_state,
                start_date or str(date.today()),
                trigger_reason,
                spy_state,
                qqq_state,
                vix_change,
                lessons,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ─── Query Methods ────────────────────────────────────────────────────

    def query_recs(
        self,
        ticker: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        grade: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Query formal recommendations with optional filters."""
        sql = "SELECT * FROM formal_rec WHERE 1=1"
        params = []

        if ticker:
            sql += " AND ticker = ?"
            params.append(ticker)
        if start_date:
            sql += " AND rec_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND rec_date <= ?"
            params.append(end_date)
        if grade:
            sql += " AND final_grade = ?"
            params.append(grade)

        sql += " ORDER BY rec_date DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def query_scores(self, ticker: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Query score audit history."""
        sql = "SELECT * FROM score_audit WHERE 1=1"
        params = []
        if ticker:
            sql += " AND ticker = ?"
            params.append(ticker)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def query_watchlist(self, active_only: bool = True, limit: int = 50) -> List[Dict]:
        """Query watchlist entries."""
        sql = "SELECT * FROM watchlist"
        if active_only:
            sql += f" WHERE next_check_date >= '{date.today()}' OR next_check_date IS NULL"
        sql += f" ORDER BY date DESC LIMIT {limit}"
        rows = self._conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def query_postmortems(
        self,
        ticker: Optional[str] = None,
        period: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Query postmortem reviews."""
        sql = "SELECT * FROM postmortem WHERE 1=1"
        params = []
        if ticker:
            sql += " AND ticker = ?"
            params.append(ticker)
        if period:
            sql += " AND review_period = ?"
            params.append(period)
        sql += " ORDER BY review_date DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def query_market_history(self, days: int = 30) -> List[Dict]:
        """Query recent market gate history."""
        sql = f"SELECT * FROM market_gate ORDER BY date DESC LIMIT {days}"
        rows = self._conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def query_exclusions(self, ticker: Optional[str] = None) -> List[Dict]:
        """Query exclusion list."""
        sql = "SELECT * FROM exclusion"
        params = []
        if ticker:
            sql += " WHERE ticker = ?"
            params.append(ticker)
        sql += " ORDER BY date DESC"
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def query_holdings(self, ticker: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Query holding management history."""
        sql = "SELECT * FROM holding WHERE 1=1"
        params = []
        if ticker:
            sql += " AND ticker = ?"
            params.append(ticker)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def query_trade_plans(self, ticker: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Query trade plans."""
        sql = "SELECT * FROM trade_plan WHERE 1=1"
        params = []
        if ticker:
            sql += " AND ticker = ?"
            params.append(ticker)
        sql += " ORDER BY date DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def query_regime_history(self, limit: int = 20) -> List[Dict]:
        """Query regime memory."""
        sql = f"SELECT * FROM regime_memory ORDER BY start_date DESC LIMIT {limit}"
        rows = self._conn.execute(sql).fetchall()
        return [dict(r) for r in rows]

    # ─── Statistics ───────────────────────────────────────────────────────

    def get_win_rate(
        self,
        strategy_version: Optional[str] = None,
        sector: Optional[str] = None,
    ) -> Dict:
        """Compute win rate statistics from postmortem data."""
        sql = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN actual_performance_pct >= 10 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_performance_pct >= 0 AND actual_performance_pct < 10 THEN 1 ELSE 0 END) as partial,
                SUM(CASE WHEN actual_performance_pct < 0 THEN 1 ELSE 0 END) as losses,
                AVG(actual_performance_pct) as avg_return,
                AVG(mfe) as avg_mfe,
                AVG(mae) as avg_mae
            FROM postmortem
            WHERE actual_performance_pct IS NOT NULL
        """
        row = self._conn.execute(sql).fetchone()
        if not row or row["total"] == 0:
            return {"total": 0, "win_rate": 0, "avg_return": 0}

        return {
            "total": row["total"],
            "wins": row["wins"],
            "partial": row["partial"],
            "losses": row["losses"],
            "win_rate": round((row["wins"] or 0) / row["total"] * 100, 1),
            "avg_return": round(row["avg_return"] or 0, 2),
            "avg_mfe": round(row["avg_mfe"] or 0, 2),
            "avg_mae": round(row["avg_mae"] or 0, 2),
        }

    def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables."""
        tables = [
            "info_inbox", "market_gate", "sector_rank", "catalyst_calendar",
            "score_audit", "formal_rec", "watchlist", "exclusion",
            "holding", "postmortem", "model_change", "trade_plan",
            "timing_gate", "exit_plan", "regime_memory",
        ]
        counts = {}
        for table in tables:
            row = self._conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
            counts[table] = row["cnt"]
        return counts

    def export_all(self, output_dir: Optional[str] = None) -> str:
        """Export all tables to JSON files for backup/analysis."""
        out_path = Path(output_dir) if output_dir else self._path.parent / "exports"
        out_path.mkdir(parents=True, exist_ok=True)

        tables = [
            "info_inbox", "market_gate", "sector_rank", "catalyst_calendar",
            "score_audit", "formal_rec", "watchlist", "exclusion",
            "holding", "postmortem", "model_change", "trade_plan", "regime_memory",
        ]

        for table in tables:
            rows = self._conn.execute(f"SELECT * FROM {table}").fetchall()
            data = [dict(r) for r in rows]
            file_path = out_path / f"{table}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return str(out_path)
