# -*- coding: utf-8 -*-
"""
INFO_GATE: Information source grading and verification module.

Core rules:
- Unconfirmed info CANNOT directly change a stock's main score.
- Social/rumor sources can only enter observation/pending/sentiment risk memo.
- Same news across multiple platforms does NOT get scored multiple times.
"""

from datetime import datetime
from typing import List, Optional

from .schemas import (
    InfoConclusion,
    InfoDirection,
    InfoInboxEntry,
    SourceGrade,
)


_SOURCE_KEYWORDS = {
    SourceGrade.A1: [
        "sec.gov", "fda.gov", "sec filing", "8-k", "10-q", "10-k",
        "s-1", "press release", "official", "federal reserve",
        "bls.gov", "bea.gov", "earnings release",
    ],
    SourceGrade.A2: [
        "reuters", "bloomberg", "cnbc", "wsj", "wall street journal",
        "financial times", "barron", "marketwatch",
    ],
    SourceGrade.B: [
        "analyst", "research note", "broker", "upgrade", "downgrade",
        "price target", "initiate coverage", "industry report",
    ],
    SourceGrade.C: [
        "reddit", "twitter", "x.com", "youtube", "stocktwits",
        "discord", "telegram", "weibo",
    ],
    SourceGrade.R: [
        "rumor", "unconfirmed", "source says", "heard that",
        "leak", "insider tip",
    ],
}


def classify_source(raw_content: str, explicit_grade: Optional[SourceGrade] = None) -> SourceGrade:
    """Classify the information source grade based on content keywords."""
    if explicit_grade is not None:
        return explicit_grade

    content_lower = raw_content.lower()

    for grade in [SourceGrade.A1, SourceGrade.A2, SourceGrade.B, SourceGrade.C, SourceGrade.R]:
        for kw in _SOURCE_KEYWORDS[grade]:
            if kw in content_lower:
                return grade

    return SourceGrade.UNKNOWN


def can_enter_scoring(grade: SourceGrade) -> bool:
    """Determine if this source grade can enter the formal scoring pipeline."""
    return grade in (SourceGrade.A1, SourceGrade.A2, SourceGrade.B)


def assess_direction(raw_content: str) -> InfoDirection:
    """Heuristic directional assessment from content."""
    content_lower = raw_content.lower()

    bull_signals = [
        "beat", "exceeded", "raised guidance", "upgrade", "strong demand",
        "fda approval", "contract win", "buyback", "record revenue",
        "above consensus", "upside surprise",
    ]
    bear_signals = [
        "miss", "below", "cut guidance", "downgrade", "weak demand",
        "fda rejection", "sec investigation", "dilution", "shelf offering",
        "atm", "below consensus", "warning",
    ]

    bull_count = sum(1 for s in bull_signals if s in content_lower)
    bear_count = sum(1 for s in bear_signals if s in content_lower)

    if bull_count > bear_count and bull_count >= 2:
        return InfoDirection.BULLISH
    if bear_count > bull_count and bear_count >= 2:
        return InfoDirection.BEARISH
    if bull_count == bear_count and bull_count > 0:
        return InfoDirection.NEUTRAL
    return InfoDirection.UNCERTAIN


def process_info(
    raw_content: str,
    tickers: Optional[List[str]] = None,
    market: str = "us",
    explicit_grade: Optional[SourceGrade] = None,
    info_id: Optional[str] = None,
) -> InfoInboxEntry:
    """
    Process raw information through the INFO_GATE.

    Returns a structured InfoInboxEntry with source grading and disposition.
    """
    now = datetime.now()

    if info_id is None:
        info_id = f"INFO-{now.strftime('%Y%m%d')}-001"

    grade = classify_source(raw_content, explicit_grade)
    direction = assess_direction(raw_content)
    enters = can_enter_scoring(grade)

    if grade in (SourceGrade.C, SourceGrade.R, SourceGrade.UNKNOWN):
        conclusion = InfoConclusion.ISOLATE if grade == SourceGrade.R else InfoConclusion.OBSERVE
    else:
        conclusion = InfoConclusion.ADOPT

    return InfoInboxEntry(
        info_id=info_id,
        timestamp=now,
        raw_content=raw_content,
        market=market,
        tickers=tickers or [],
        initial_direction=direction,
        needs_verification=(grade not in (SourceGrade.A1,)),
        enters_scoring=enters,
        source_grade=grade,
        conclusion=conclusion,
    )


def check_duplicate(existing_entries: List[InfoInboxEntry], new_entry: InfoInboxEntry) -> bool:
    """
    Check if the same news is already recorded (anti-duplication).
    Same ticker + same direction + same day = potential duplicate.
    """
    for entry in existing_entries:
        if (
            entry.timestamp.date() == new_entry.timestamp.date()
            and set(entry.tickers) & set(new_entry.tickers)
            and entry.initial_direction == new_entry.initial_direction
        ):
            return True
    return False
