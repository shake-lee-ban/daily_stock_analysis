#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Stock Pullback Confirmation Screener
========================================
Screens AI Power / Grid / Semiconductor Equipment US stocks
for pullback confirmation (回踩确认) patterns.

Criteria (mirrors src/stock_analyzer.py StockTrendAnalyzer logic):
- Trend: bullish (MA5 >= MA10 >= MA20 preferred)
- Bias: price near MA5/MA10 support (bias_ma5 between -5% and +3%)
- Volume: shrinking or normal (not heavy selling)
- Support: price near or above MA5/MA10
- MACD: not death cross
- Composite score >= 40

Usage:
    python3 scripts/us_pullback_screener.py
"""

import sys
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    print("请先安装 yfinance: pip install yfinance")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


class TrendStatus(Enum):
    STRONG_BULL = "强势多头"
    BULL = "多头排列"
    WEAK_BULL = "弱势多头"
    CONSOLIDATION = "盘整"
    WEAK_BEAR = "弱势空头"
    BEAR = "空头排列"
    STRONG_BEAR = "强势空头"

class VolumeStatus(Enum):
    HEAVY_VOLUME_UP = "放量上涨"
    HEAVY_VOLUME_DOWN = "放量下跌"
    SHRINK_VOLUME_UP = "缩量上涨"
    SHRINK_VOLUME_DOWN = "缩量回调"
    NORMAL = "量能正常"

class BuySignal(Enum):
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    WAIT = "观望"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"

class MACDStatus(Enum):
    GOLDEN_CROSS_ZERO = "零轴上金叉"
    GOLDEN_CROSS = "金叉"
    BULLISH = "多头"
    CROSSING_UP = "上穿零轴"
    CROSSING_DOWN = "下穿零轴"
    BEARISH = "空头"
    DEATH_CROSS = "死叉"

class RSIStatus(Enum):
    OVERBOUGHT = "超买"
    STRONG_BUY = "强势买入"
    NEUTRAL = "中性"
    WEAK = "弱势"
    OVERSOLD = "超卖"


@dataclass
class AnalysisResult:
    code: str
    name: str = ""
    current_price: float = 0.0
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    bias_ma5: float = 0.0
    bias_ma10: float = 0.0
    bias_ma20: float = 0.0
    trend_status: TrendStatus = TrendStatus.CONSOLIDATION
    trend_strength: float = 0.0
    volume_status: VolumeStatus = VolumeStatus.NORMAL
    volume_ratio_5d: float = 0.0
    support_ma5: bool = False
    support_ma10: bool = False
    macd_dif: float = 0.0
    macd_dea: float = 0.0
    macd_bar: float = 0.0
    macd_status: MACDStatus = MACDStatus.BULLISH
    rsi_14: float = 50.0
    rsi_status: RSIStatus = RSIStatus.NEUTRAL
    buy_signal: BuySignal = BuySignal.WAIT
    signal_score: int = 0
    signal_reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    pct_change_5d: float = 0.0
    pct_from_high_20d: float = 0.0


VOLUME_SHRINK = 0.7
VOLUME_HEAVY = 1.5
MA_SUPPORT_TOL = 0.02
BIAS_THRESHOLD = 5.0


def compute_analysis(df: pd.DataFrame, code: str, name: str = "") -> Optional[AnalysisResult]:
    if df is None or df.empty or len(df) < 25:
        return None

    df = df.sort_values('date').reset_index(drop=True).copy()
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean() if len(df) >= 60 else df['close'].rolling(20).mean()

    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['dif'] = ema12 - ema26
    df['dea'] = df['dif'].ewm(span=9, adjust=False).mean()
    df['macd_bar'] = 2 * (df['dif'] - df['dea'])

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df['rsi14'] = 100 - (100 / (1 + rs))

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest

    r = AnalysisResult(code=code, name=name)
    r.current_price = float(latest['close'])
    r.ma5 = float(latest['ma5'])
    r.ma10 = float(latest['ma10'])
    r.ma20 = float(latest['ma20'])
    r.ma60 = float(latest['ma60']) if not pd.isna(latest['ma60']) else r.ma20

    if r.ma5 > 0:
        r.bias_ma5 = (r.current_price - r.ma5) / r.ma5 * 100
    if r.ma10 > 0:
        r.bias_ma10 = (r.current_price - r.ma10) / r.ma10 * 100
    if r.ma20 > 0:
        r.bias_ma20 = (r.current_price - r.ma20) / r.ma20 * 100

    if r.ma5 > r.ma10 > r.ma20:
        spread = (r.ma5 - r.ma20) / r.ma20 * 100
        if spread > 5:
            r.trend_status = TrendStatus.STRONG_BULL
            r.trend_strength = min(100, 70 + spread)
        else:
            r.trend_status = TrendStatus.BULL
            r.trend_strength = 60
    elif r.ma5 > r.ma10:
        r.trend_status = TrendStatus.WEAK_BULL
        r.trend_strength = 40
    elif r.ma5 < r.ma10 < r.ma20:
        spread = (r.ma20 - r.ma5) / r.ma20 * 100
        if spread > 5:
            r.trend_status = TrendStatus.STRONG_BEAR
            r.trend_strength = 10
        else:
            r.trend_status = TrendStatus.BEAR
            r.trend_strength = 20
    elif r.ma5 < r.ma10:
        r.trend_status = TrendStatus.WEAK_BEAR
        r.trend_strength = 30
    else:
        r.trend_status = TrendStatus.CONSOLIDATION
        r.trend_strength = 50

    vol_5d = df['volume'].tail(5).mean()
    vol_today = float(latest['volume'])
    if vol_5d > 0:
        r.volume_ratio_5d = vol_today / vol_5d
    else:
        r.volume_ratio_5d = 1.0

    price_chg = (r.current_price - float(prev['close'])) / float(prev['close']) if float(prev['close']) > 0 else 0
    if r.volume_ratio_5d < VOLUME_SHRINK:
        r.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN if price_chg < 0 else VolumeStatus.SHRINK_VOLUME_UP
    elif r.volume_ratio_5d > VOLUME_HEAVY:
        r.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN if price_chg < -0.01 else VolumeStatus.HEAVY_VOLUME_UP
    else:
        r.volume_status = VolumeStatus.NORMAL

    if r.ma5 > 0 and abs(r.current_price - r.ma5) / r.ma5 <= MA_SUPPORT_TOL and r.current_price >= r.ma5 * 0.98:
        r.support_ma5 = True
    if r.ma10 > 0 and abs(r.current_price - r.ma10) / r.ma10 <= MA_SUPPORT_TOL and r.current_price >= r.ma10 * 0.98:
        r.support_ma10 = True

    r.macd_dif = float(latest['dif'])
    r.macd_dea = float(latest['dea'])
    r.macd_bar = float(latest['macd_bar'])
    prev_dif = float(prev['dif']) if not pd.isna(prev['dif']) else 0
    prev_dea = float(prev['dea']) if not pd.isna(prev['dea']) else 0

    if prev_dif <= prev_dea and r.macd_dif > r.macd_dea:
        r.macd_status = MACDStatus.GOLDEN_CROSS_ZERO if r.macd_dif > 0 else MACDStatus.GOLDEN_CROSS
    elif prev_dif >= prev_dea and r.macd_dif < r.macd_dea:
        r.macd_status = MACDStatus.DEATH_CROSS
    elif r.macd_dif > r.macd_dea > 0:
        r.macd_status = MACDStatus.BULLISH
    elif r.macd_dif < r.macd_dea < 0:
        r.macd_status = MACDStatus.BEARISH
    elif prev_dif < 0 and r.macd_dif >= 0:
        r.macd_status = MACDStatus.CROSSING_UP
    elif prev_dif > 0 and r.macd_dif <= 0:
        r.macd_status = MACDStatus.CROSSING_DOWN
    else:
        r.macd_status = MACDStatus.BULLISH if r.macd_dif > r.macd_dea else MACDStatus.BEARISH

    rsi_val = float(latest['rsi14']) if not pd.isna(latest['rsi14']) else 50
    r.rsi_14 = rsi_val
    if rsi_val > 70:
        r.rsi_status = RSIStatus.OVERBOUGHT
    elif rsi_val > 50:
        r.rsi_status = RSIStatus.STRONG_BUY
    elif rsi_val > 40:
        r.rsi_status = RSIStatus.NEUTRAL
    elif rsi_val > 30:
        r.rsi_status = RSIStatus.WEAK
    else:
        r.rsi_status = RSIStatus.OVERSOLD

    if len(df) >= 6:
        r.pct_change_5d = (r.current_price / float(df.iloc[-6]['close']) - 1) * 100
    high_20d = df['high'].tail(20).max()
    if high_20d > 0:
        r.pct_from_high_20d = (r.current_price / high_20d - 1) * 100

    _score(r)
    return r


def _score(r: AnalysisResult):
    score = 0
    reasons = []
    risks = []

    trend_scores = {
        TrendStatus.STRONG_BULL: 30, TrendStatus.BULL: 26, TrendStatus.WEAK_BULL: 18,
        TrendStatus.CONSOLIDATION: 12, TrendStatus.WEAK_BEAR: 8, TrendStatus.BEAR: 4, TrendStatus.STRONG_BEAR: 0,
    }
    score += trend_scores.get(r.trend_status, 12)
    if r.trend_status in (TrendStatus.STRONG_BULL, TrendStatus.BULL):
        reasons.append(f"✅ {r.trend_status.value}")
    elif r.trend_status in (TrendStatus.BEAR, TrendStatus.STRONG_BEAR):
        risks.append(f"⚠️ {r.trend_status.value}")

    bias = r.bias_ma5
    if bias < 0:
        if bias > -3:
            score += 20
            reasons.append(f"✅ 回踩MA5({bias:+.1f}%)")
        elif bias > -5:
            score += 16
            reasons.append(f"✅ 回踩MA5({bias:+.1f}%)")
        else:
            score += 8
            risks.append(f"⚠️ 乖离大({bias:+.1f}%)")
    elif bias < 2:
        score += 18
        reasons.append(f"✅ 贴近MA5({bias:+.1f}%)")
    elif bias < BIAS_THRESHOLD:
        score += 14
    else:
        score += 4
        risks.append(f"❌ 乖离率过高({bias:+.1f}%)")

    vol_scores = {
        VolumeStatus.SHRINK_VOLUME_DOWN: 15, VolumeStatus.HEAVY_VOLUME_UP: 12,
        VolumeStatus.NORMAL: 10, VolumeStatus.SHRINK_VOLUME_UP: 6, VolumeStatus.HEAVY_VOLUME_DOWN: 0,
    }
    score += vol_scores.get(r.volume_status, 8)
    if r.volume_status == VolumeStatus.SHRINK_VOLUME_DOWN:
        reasons.append("✅ 缩量回调")
    elif r.volume_status == VolumeStatus.HEAVY_VOLUME_DOWN:
        risks.append("⚠️ 放量下跌")

    if r.support_ma5:
        score += 5
        reasons.append("✅ MA5支撑")
    if r.support_ma10:
        score += 5
        reasons.append("✅ MA10支撑")

    macd_scores = {
        MACDStatus.GOLDEN_CROSS_ZERO: 15, MACDStatus.GOLDEN_CROSS: 12, MACDStatus.CROSSING_UP: 10,
        MACDStatus.BULLISH: 8, MACDStatus.BEARISH: 2, MACDStatus.CROSSING_DOWN: 0, MACDStatus.DEATH_CROSS: 0,
    }
    score += macd_scores.get(r.macd_status, 5)
    if r.macd_status in (MACDStatus.GOLDEN_CROSS_ZERO, MACDStatus.GOLDEN_CROSS):
        reasons.append(f"✅ {r.macd_status.value}")
    elif r.macd_status == MACDStatus.DEATH_CROSS:
        risks.append("⚠️ MACD死叉")

    rsi_scores = {
        RSIStatus.OVERSOLD: 10, RSIStatus.STRONG_BUY: 8,
        RSIStatus.NEUTRAL: 5, RSIStatus.WEAK: 3, RSIStatus.OVERBOUGHT: 0,
    }
    score += rsi_scores.get(r.rsi_status, 5)

    r.signal_score = score
    r.signal_reasons = reasons
    r.risk_factors = risks

    if score >= 75 and r.trend_status in (TrendStatus.STRONG_BULL, TrendStatus.BULL):
        r.buy_signal = BuySignal.STRONG_BUY
    elif score >= 60 and r.trend_status in (TrendStatus.STRONG_BULL, TrendStatus.BULL, TrendStatus.WEAK_BULL):
        r.buy_signal = BuySignal.BUY
    elif score >= 45:
        r.buy_signal = BuySignal.HOLD
    elif score >= 30:
        r.buy_signal = BuySignal.WAIT
    elif r.trend_status in (TrendStatus.BEAR, TrendStatus.STRONG_BEAR):
        r.buy_signal = BuySignal.STRONG_SELL
    else:
        r.buy_signal = BuySignal.SELL


# ──────────────────────────────────────────────
# Target universe
# ──────────────────────────────────────────────
SECTOR_STOCKS: Dict[str, List[Tuple[str, str]]] = {
    "AI 电力 / 数据中心电力": [
        ("VRT", "Vertiv (数据中心电力/散热)"),
        ("ETN", "Eaton Corp (电力管理)"),
        ("GEV", "GE Vernova (发电/电网)"),
        ("CEG", "Constellation Energy (核电)"),
        ("VST", "Vistra Energy (电力)"),
        ("TLN", "Talen Energy (核电)"),
        ("NRG", "NRG Energy (电力)"),
        ("OKLO", "Oklo (小型核电)"),
        ("SMR", "NuScale Power (SMR)"),
        ("CCJ", "Cameco (铀矿)"),
        ("BE", "Bloom Energy (燃料电池)"),
        ("FLNC", "Fluence Energy (储能)"),
    ],
    "电网基础设施": [
        ("PWR", "Quanta Services (电网建设)"),
        ("EME", "EMCOR Group (电气工程)"),
        ("MTZ", "MasTec (基建/电网)"),
        ("HUBB", "Hubbell (电气产品)"),
        ("NVT", "nVent Electric (电气连接)"),
        ("POWL", "Powell Industries (配电设备)"),
        ("AYI", "Acuity Brands (电力照明)"),
        ("GE", "GE Aerospace (工业电力)"),
    ],
    "半导体设备": [
        ("ASML", "ASML (光刻机龙头)"),
        ("AMAT", "Applied Materials (薄膜/刻蚀)"),
        ("LRCX", "Lam Research (刻蚀设备)"),
        ("KLAC", "KLA Corp (检测设备)"),
        ("TER", "Teradyne (测试设备)"),
        ("ENTG", "Entegris (材料/过滤)"),
        ("ONTO", "Onto Innovation (检测)"),
        ("ACLS", "Axcelis Technologies (离子注入)"),
        ("FORM", "FormFactor (探针卡)"),
        ("COHU", "Cohu (测试分选)"),
        ("UCTT", "Ultra Clean (零部件)"),
        ("KLIC", "Kulicke & Soffa (封装设备)"),
        ("MKSI", "MKS Instruments (仪器)"),
        ("AMKR", "Amkor Technology (封测)"),
    ],
}


def fetch_stock_data(ticker: str, days: int = 150) -> Optional[pd.DataFrame]:
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        stock = yf.Ticker(ticker)
        df = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        if df is None or df.empty:
            return None
        df = df.reset_index()
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        if 'close' not in df.columns or len(df) < 30:
            return None
        return df
    except Exception as e:
        logger.debug(f"  {ticker} fetch error: {e}")
        return None


def is_pullback_candidate(r: AnalysisResult) -> Tuple[bool, str]:
    reasons = []
    disq = []

    if r.trend_status in (TrendStatus.STRONG_BULL, TrendStatus.BULL):
        reasons.append(f"趋势: {r.trend_status.value}")
    elif r.trend_status == TrendStatus.WEAK_BULL:
        reasons.append(f"趋势: {r.trend_status.value}")
    elif r.trend_status == TrendStatus.CONSOLIDATION:
        if r.bias_ma20 > 0:
            reasons.append("盘整偏多")
        else:
            disq.append(f"趋势不佳: {r.trend_status.value}")
    else:
        disq.append(f"趋势不佳: {r.trend_status.value}")

    bias = r.bias_ma5
    if -5 <= bias <= 3:
        reasons.append(f"回踩MA5({bias:+.1f}%)")
    elif bias > 3:
        disq.append(f"乖离率偏高({bias:+.1f}%)")
    else:
        disq.append(f"跌幅过大({bias:+.1f}%)")

    if r.support_ma5 or r.support_ma10:
        sups = []
        if r.support_ma5:
            sups.append("MA5")
        if r.support_ma10:
            sups.append("MA10")
        reasons.append(f"获{'/'.join(sups)}支撑")

    if r.volume_status == VolumeStatus.SHRINK_VOLUME_DOWN:
        reasons.append("缩量回调 ✓")
    elif r.volume_status == VolumeStatus.HEAVY_VOLUME_DOWN:
        disq.append("放量下跌")

    if r.macd_status == MACDStatus.DEATH_CROSS:
        disq.append("MACD死叉")

    if r.signal_score < 40:
        disq.append(f"评分过低({r.signal_score})")

    if disq:
        return False, "; ".join(disq)
    return True, "; ".join(reasons)


def main():
    print("🔍 开始筛选美股 AI 电力 / 电网 / 半导体设备 — 回踩确认股...\n")
    all_candidates: Dict[str, List] = {}

    for sector, stocks in SECTOR_STOCKS.items():
        logger.info(f"\n📂 扫描板块: {sector} ({len(stocks)} 只)")
        candidates = []
        for ticker, name in stocks:
            df = fetch_stock_data(ticker)
            if df is None:
                logger.info(f"  ⏭  {ticker:6s} {name} — 数据不足")
                continue
            r = compute_analysis(df, ticker, name)
            if r is None:
                logger.info(f"  ⏭  {ticker:6s} {name} — 分析失败")
                continue
            ok, reason = is_pullback_candidate(r)
            if ok:
                candidates.append((ticker, name, r, reason))
                logger.info(f"  ✅ {ticker:6s} {name} — 评分{r.signal_score} | {r.buy_signal.value} | {reason}")
            else:
                logger.info(f"  ❌ {ticker:6s} {name} — {reason}")
        all_candidates[sector] = candidates

    print_report(all_candidates)


def print_report(all_candidates: Dict[str, list]):
    print("\n")
    print("=" * 100)
    print("  美股回踩确认筛选报告 — AI 电力 / 电网 / 半导体设备")
    print(f"  筛选时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 100)

    total = 0
    all_cands = []
    for sector, cands in all_candidates.items():
        print(f"\n{'─' * 100}")
        print(f"  📁 {sector}  ({len(cands)} 只符合)")
        print(f"{'─' * 100}")
        if not cands:
            print("     （无符合条件标的）")
            continue
        cands.sort(key=lambda x: x[2].signal_score, reverse=True)
        print(f"  {'代码':<8s} {'名称':<36s} {'评分':>4s}  {'信号':<10s} {'趋势':<10s} {'MA5乖离':>8s}  {'RSI':>5s}  {'量能':<10s} {'20日高点':>8s}")
        print(f"  {'─'*8} {'─'*36} {'─'*4}  {'─'*10} {'─'*10} {'─'*8}  {'─'*5}  {'─'*10} {'─'*8}")
        for ticker, name, r, reason in cands:
            print(
                f"  {ticker:<8s} {name:<36s} "
                f"{r.signal_score:4d}  "
                f"{r.buy_signal.value:<10s} "
                f"{r.trend_status.value:<10s} "
                f"{r.bias_ma5:>+7.1f}%  "
                f"{r.rsi_14:5.1f}  "
                f"{r.volume_status.value:<10s} "
                f"{r.pct_from_high_20d:>+7.1f}%"
            )
        total += len(cands)
        all_cands.extend(cands)
        print()
        for ticker, name, r, reason in cands:
            print(f"  📌 {ticker} ${r.current_price:.2f} — {reason}")
            if r.signal_reasons:
                print(f"     买入理由: {' | '.join(r.signal_reasons)}")
            if r.risk_factors:
                print(f"     风险提示: {' | '.join(r.risk_factors)}")

    print(f"\n{'=' * 100}")
    print(f"  共筛选出 {total} 只回踩确认候选股")
    print(f"{'=' * 100}")

    if total > 0:
        all_cands.sort(key=lambda x: x[2].signal_score, reverse=True)
        print("\n  🏆 综合排名 TOP (按评分):")
        print(f"  {'排名':>4s}  {'代码':<8s} {'名称':<36s} {'评分':>4s}  {'信号':<10s} {'价格':>8s}  {'MA5乖离':>8s}")
        print(f"  {'─'*4}  {'─'*8} {'─'*36} {'─'*4}  {'─'*10} {'─'*8}  {'─'*8}")
        for i, (ticker, name, r, _) in enumerate(all_cands[:15], 1):
            print(
                f"  {i:4d}  {ticker:<8s} {name:<36s} "
                f"{r.signal_score:4d}  "
                f"{r.buy_signal.value:<10s} "
                f"${r.current_price:>7.2f}  "
                f"{r.bias_ma5:>+7.1f}%"
            )

        tickers = [c[0] for c in all_cands]
        print(f"\n  ⚠️  以上仅为技术面筛选结果，不构成投资建议。")
        print(f"     建议结合基本面、新闻、资金流向进一步验证。")
        print(f"     可用本系统深度分析：python main.py --stocks {','.join(tickers[:10])}")
    print()


if __name__ == "__main__":
    main()
