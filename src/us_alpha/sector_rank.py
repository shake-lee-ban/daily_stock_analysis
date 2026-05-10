# -*- coding: utf-8 -*-
"""
SECTOR_RANK: Sector strength ranking module.

Scores sectors across 6 dimensions (total 100):
- Info Heat (20)
- Fund Flow / Volume (20)
- Relative Strength (20)
- Catalyst Density (15)
- Macro Alignment (15)
- Sustainability (10)

Grades: A (85+), B (75-84), C (60-74), WEAK (<60)
"""

from datetime import date
from typing import Dict, List, Optional

from .schemas import SectorGrade, SectorRankEntry


KNOWN_SECTORS = [
    "AI Infrastructure",
    "Semiconductor / AI ASIC / Networking / CPO",
    "Memory / HBM / NAND / SSD",
    "AI Software / Cloud / Agentic AI",
    "Biotech / Healthcare Events",
    "Energy / Oil / Shipping / Insurance",
    "Consumer Electronics / PC / Gaming",
    "Financials",
    "Cybersecurity",
    "Quantum Computing",
    "Robotics / Automation",
    "Defense / Aerospace",
]


def score_sector(
    sector_name: str,
    info_heat: int = 0,
    fund_flow: int = 0,
    relative_strength: int = 0,
    catalyst_density: int = 0,
    macro_alignment: int = 0,
    sustainability: int = 0,
    representative_tickers: Optional[List[str]] = None,
    assessment_date: Optional[date] = None,
    notes: Optional[str] = None,
) -> SectorRankEntry:
    """Create a scored sector entry with proper bounds."""
    return SectorRankEntry(
        date=assessment_date or date.today(),
        sector_name=sector_name,
        info_heat=max(0, min(20, info_heat)),
        fund_flow=max(0, min(20, fund_flow)),
        relative_strength=max(0, min(20, relative_strength)),
        catalyst_density=max(0, min(15, catalyst_density)),
        macro_alignment=max(0, min(15, macro_alignment)),
        sustainability=max(0, min(10, sustainability)),
        representative_tickers=representative_tickers or [],
        notes=notes,
    )


def rank_sectors(entries: List[SectorRankEntry]) -> List[SectorRankEntry]:
    """Sort sectors by total score descending."""
    return sorted(entries, key=lambda e: e.total_score, reverse=True)


def get_top_sectors(entries: List[SectorRankEntry], min_grade: SectorGrade = SectorGrade.B) -> List[SectorRankEntry]:
    """Filter sectors meeting minimum grade threshold."""
    grade_order = {SectorGrade.A: 4, SectorGrade.B: 3, SectorGrade.C: 2, SectorGrade.WEAK: 1}
    min_value = grade_order.get(min_grade, 2)
    ranked = rank_sectors(entries)
    return [e for e in ranked if grade_order.get(e.grade, 0) >= min_value]


def format_sector_report(entries: List[SectorRankEntry]) -> str:
    """Format sector ranking into readable report."""
    ranked = rank_sectors(entries)
    lines = ["=" * 50, "SECTOR STRENGTH RANKING", "=" * 50]

    for i, entry in enumerate(ranked, 1):
        tickers_str = ", ".join(entry.representative_tickers[:5]) if entry.representative_tickers else "N/A"
        lines.append(
            f"{i}. [{entry.grade.value}] {entry.sector_name} "
            f"(Score: {entry.total_score}/100) | Reps: {tickers_str}"
        )

    lines.append("=" * 50)
    a_sectors = [e for e in ranked if e.grade == SectorGrade.A]
    b_sectors = [e for e in ranked if e.grade == SectorGrade.B]
    lines.append(f"A-grade (主線): {len(a_sectors)} sectors")
    lines.append(f"B-grade (強勢): {len(b_sectors)} sectors")
    return "\n".join(lines)
