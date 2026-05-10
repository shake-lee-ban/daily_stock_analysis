# -*- coding: utf-8 -*-
"""
US Alpha Selection System - Excel Export.

Exports all database tables to a formatted Excel workbook on Desktop.
Each table becomes a separate sheet with:
- Column headers with filters
- Conditional formatting for grades
- Proper column widths
- Summary sheet with statistics

Output: ~/Desktop/us_alpha_db/US_Alpha_Records.xlsx
"""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .storage import AlphaDB


# ─── Style Constants ──────────────────────────────────────────────────────────

_HEADER_FONT = Font(name="Microsoft JhengHei", bold=True, size=11, color="FFFFFF")
_HEADER_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
_HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=True)

_DATA_FONT = Font(name="Microsoft JhengHei", size=10)
_DATA_ALIGNMENT = Alignment(vertical="center", wrap_text=False)

_GRADE_FILLS = {
    "A": PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"),
    "B": PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid"),
    "C": PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid"),
    "D": PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"),
    "F": PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid"),
    "P": PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid"),
}

_PASS_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
_WARN_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
_BLOCK_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

_THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


# ─── Sheet Definitions ────────────────────────────────────────────────────────

_SHEETS = {
    "推薦紀錄": {
        "table": "formal_rec",
        "columns": [
            ("rec_id", "推薦ID", 18),
            ("rec_date", "日期", 12),
            ("ticker", "股票", 8),
            ("company_name", "公司", 16),
            ("strategy_version", "策略版本", 20),
            ("momentum_state", "動能狀態", 10),
            ("rec_type", "推薦類型", 10),
            ("buy_price", "買入價", 10),
            ("stop_loss", "停損", 10),
            ("target_1", "目標1", 10),
            ("target_2", "目標2", 10),
            ("risk_reward_ratio", "RR比", 8),
            ("final_grade", "等級", 6),
            ("total_score", "總分", 6),
            ("market_state", "市場狀態", 14),
            ("position_risk", "倉位風險", 10),
            ("futu_priority", "富途優先", 10),
            ("mfe", "MFE%", 8),
            ("mae", "MAE%", 8),
            ("final_outcome", "最終結果", 12),
        ],
    },
    "評分審計": {
        "table": "score_audit",
        "columns": [
            ("score_id", "評分ID", 22),
            ("ticker", "股票", 8),
            ("timestamp", "時間", 18),
            ("strategy_version", "策略版本", 20),
            ("original_score", "原始分", 8),
            ("final_score", "最終分", 8),
            ("final_grade", "等級", 6),
            ("risk_lock", "風險封鎖", 10),
            ("enters_rec", "進入推薦", 10),
        ],
    },
    "觀察名單": {
        "table": "watchlist",
        "columns": [
            ("watch_id", "觀察ID", 18),
            ("date", "日期", 12),
            ("ticker", "股票", 8),
            ("layer", "分層", 10),
            ("watch_reason", "觀察原因", 30),
            ("fail_reason", "未通過原因", 30),
            ("trigger_condition", "觸發條件", 20),
            ("can_convert_to_rec", "可轉推薦", 10),
            ("next_check_date", "下次檢查", 12),
        ],
    },
    "市場環境": {
        "table": "market_gate",
        "columns": [
            ("date", "日期", 12),
            ("market_state", "市場狀態", 14),
            ("spy_trend", "SPY", 8),
            ("qqq_trend", "QQQ", 8),
            ("iwm_trend", "IWM", 8),
            ("smh_trend", "SMH", 8),
            ("vix_level", "VIX", 8),
            ("us10y_yield", "10Y殖利率", 10),
            ("notes", "備註", 30),
        ],
    },
    "板塊強度": {
        "table": "sector_rank",
        "columns": [
            ("date", "日期", 12),
            ("sector_name", "板塊", 28),
            ("total_score", "總分", 8),
            ("grade", "等級", 6),
            ("representative_tickers", "代表股", 20),
        ],
    },
    "催化劑": {
        "table": "catalyst_calendar",
        "columns": [
            ("catalyst_id", "催化劑ID", 22),
            ("ticker", "股票", 8),
            ("event_type", "事件類型", 12),
            ("expected_date", "預計日期", 12),
            ("certainty", "確定性", 8),
        ],
    },
    "資訊收錄": {
        "table": "info_inbox",
        "columns": [
            ("info_id", "資訊ID", 18),
            ("timestamp", "時間", 18),
            ("market", "市場", 6),
            ("tickers", "涉及股票", 14),
            ("source_grade", "來源等級", 10),
            ("initial_direction", "方向", 10),
            ("enters_scoring", "進入主分數", 10),
            ("enters_market_gate", "進入市場閘門", 12),
            ("enters_risk_lock", "進入風險封鎖", 12),
            ("enters_sector_rank", "進入板塊分數", 12),
            ("conclusion", "結論", 8),
            ("raw_content", "內容摘要", 50),
        ],
    },
    "排除名單": {
        "table": "exclusion",
        "columns": [
            ("ticker", "股票", 8),
            ("date", "日期", 12),
            ("reason", "排除原因", 40),
            ("category", "類別", 12),
            ("duration", "期限", 12),
        ],
    },
    "持倉管理": {
        "table": "holding",
        "columns": [
            ("ticker", "股票", 8),
            ("timestamp", "時間", 18),
            ("action", "動作", 10),
            ("shares", "股數", 8),
            ("avg_cost", "成本", 10),
            ("current_price", "現價", 10),
            ("position_value", "持倉金額", 12),
            ("pnl_pct", "盈虧%", 8),
            ("linked_rec_id", "推薦ID", 16),
            ("original_buy_reason", "買入理由", 20),
            ("alert_price", "警戒價", 8),
            ("invalidation_price", "失效價", 8),
            ("stop_loss", "停損價", 8),
            ("target_1", "T1", 8),
            ("target_2", "T2", 8),
            ("can_add", "可否加碼", 10),
            ("add_condition", "加碼條件", 16),
            ("holding_days", "持有天數", 10),
            ("original_thesis_valid", "邏輯有效", 10),
            ("next_action", "下一步", 12),
        ],
    },
    "復盤紀錄": {
        "table": "postmortem",
        "columns": [
            ("rec_id", "推薦ID", 16),
            ("score_id", "評分ID", 16),
            ("plan_id", "計畫ID", 16),
            ("ticker", "股票", 8),
            ("review_date", "復盤日期", 12),
            ("review_period", "週期", 8),
            ("entry_price", "進場價", 10),
            ("stop_loss", "停損", 10),
            ("target_1", "T1", 10),
            ("target_2", "T2", 10),
            ("highest_price", "最高價", 10),
            ("lowest_price", "最低價", 10),
            ("current_or_exit_price", "現價/出場價", 12),
            ("mfe", "MFE%", 8),
            ("mae", "MAE%", 8),
            ("actual_performance_pct", "實際報酬%", 10),
            ("hit_t1", "觸發T1", 8),
            ("hit_t2", "觸發T2", 8),
            ("hit_stop_loss", "觸發停損", 8),
            ("hit_time_stop", "觸發時間停損", 10),
            ("holding_days", "持有天數", 10),
            ("exit_trigger", "出場觸發", 14),
            ("error_type", "錯誤類型", 16),
            ("success_reason", "成功原因", 20),
            ("failure_reason", "失敗原因", 20),
            ("needs_model_change", "需改模型", 10),
            ("conclusion", "結論", 30),
        ],
    },
    "交易計畫": {
        "table": "trade_plan",
        "columns": [
            ("rec_id", "推薦ID", 16),
            ("ticker", "股票", 8),
            ("date", "日期", 12),
            ("strategy_version", "策略", 16),
            ("market_state", "市場", 12),
            ("sector_state", "板塊", 12),
            ("entry_trigger", "進場觸發", 20),
            ("entry_method", "進場方式", 12),
            ("entry_range", "進場區間", 12),
            ("no_chase_price", "禁追價", 8),
            ("stop_loss", "停損", 8),
            ("invalidation_condition", "失效條件", 20),
            ("time_stop_days", "時間停損天", 10),
            ("target_1", "T1", 8),
            ("t1_exit_pct", "T1比例", 8),
            ("target_2", "T2", 8),
            ("t2_exit_pct", "T2比例", 8),
            ("remainder_rule", "剩餘處理", 14),
            ("trailing_stop_rule", "移動停損", 18),
            ("position_size", "倉位", 10),
            ("max_risk_pct", "風險%", 8),
            ("per_share_risk", "每股風險", 10),
            ("risk_reward_ratio", "RR比", 8),
            ("catalyst", "催化劑", 18),
            ("catalyst_date", "催化日期", 12),
            ("days_to_catalyst", "距事件天", 10),
            ("timing_state", "時間狀態", 10),
            ("timing_passed", "Timing通過", 10),
            ("counter_thesis_1", "反方論述1", 24),
            ("counter_thesis_2", "反方論述2", 24),
            ("counter_thesis_3", "反方論述3", 24),
            ("fail_condition_1", "失效條件1", 24),
            ("fail_condition_2", "失效條件2", 24),
            ("fail_condition_3", "失效條件3", 24),
            ("v22_compliant", "v2.2合規", 8),
        ],
    },
    "當前持倉": {
        "table": "holding_current",
        "columns": [
            ("ticker", "股票", 8),
            ("status", "狀態", 8),
            ("shares", "股數", 8),
            ("avg_cost", "成本", 10),
            ("current_price", "現價", 10),
            ("position_value", "持倉金額", 12),
            ("pnl_pct", "盈虧%", 8),
            ("pnl_amount", "盈虧金額", 10),
            ("entry_date", "進場日", 12),
            ("holding_days", "持有天數", 10),
            ("stop_loss", "停損", 8),
            ("alert_price", "警戒價", 8),
            ("invalidation_price", "失效價", 8),
            ("target_1", "T1", 8),
            ("target_2", "T2", 8),
            ("can_add", "可加碼", 8),
            ("add_condition", "加碼條件", 16),
            ("trailing_stop", "移動停損", 14),
            ("original_thesis_valid", "邏輯有效", 10),
            ("next_action", "下一步", 12),
            ("sector", "板塊", 14),
            ("momentum_state", "動能狀態", 10),
            ("notes", "備註", 24),
        ],
    },
    "時間閘門": {
        "table": "timing_gate",
        "columns": [
            ("ticker", "股票", 8),
            ("date", "日期", 12),
            ("timing_state", "時間狀態", 12),
            ("earnings_date", "財報日期", 12),
            ("days_to_earnings", "距財報天數", 10),
            ("catalyst_date", "催化劑日期", 12),
            ("days_to_catalyst", "距事件天數", 10),
            ("is_fomc_week", "FOMC週", 8),
            ("is_opex_week", "OPEX週", 8),
            ("is_cpi_nfp_week", "CPI/NFP", 8),
            ("is_earnings_season", "財報季", 8),
            ("timing_passed", "通過", 6),
            ("timing_action", "動作", 14),
            ("notes", "備註", 30),
        ],
    },
    "出場計畫": {
        "table": "exit_plan",
        "columns": [
            ("ticker", "股票", 8),
            ("rec_id", "推薦ID", 16),
            ("date", "日期", 12),
            ("entry_price", "進場價", 10),
            ("stop_loss", "停損", 10),
            ("trailing_stop_rule", "移動停損規則", 20),
            ("target_1", "T1", 10),
            ("t1_exit_pct", "T1出場比", 10),
            ("target_2", "T2", 10),
            ("t2_exit_pct", "T2出場比", 10),
            ("remainder_rule", "剩餘部位", 16),
            ("time_stop_days", "時間停損天數", 12),
            ("catalyst_fail_rule", "利多出盡規則", 20),
            ("structure_break_rule", "結構失效規則", 20),
            ("profit_lock_rules", "獲利鎖定規則", 24),
            ("actual_exit_trigger", "實際出場觸發", 14),
            ("actual_exit_price", "實際出場價", 12),
            ("actual_exit_date", "實際出場日", 12),
        ],
    },
    "模型修正": {
        "table": "model_change",
        "columns": [
            ("change_date", "日期", 12),
            ("module_changed", "修改模組", 16),
            ("change_description", "修改內容", 40),
            ("rationale", "原因", 30),
            ("triggered_by", "觸發來源", 16),
        ],
    },
    "相關性檢查": {
        "table": "correlation_guard",
        "columns": [
            ("corr_id", "檢查ID", 16),
            ("date", "日期", 12),
            ("tickers_in_portfolio", "組合標的", 24),
            ("same_sector_count", "同板塊數", 10),
            ("max_correlation", "最高相關係數", 12),
            ("same_catalyst_exposure", "同催化劑暴露", 20),
            ("portfolio_beta", "組合Beta", 10),
            ("concentration_verdict", "集中度判定", 14),
            ("max_total_position", "最大總倉位", 12),
        ],
    },
    "倉位計算": {
        "table": "position_sizing",
        "columns": [
            ("sizing_id", "計算ID", 16),
            ("ticker", "股票", 8),
            ("date", "日期", 12),
            ("account_value", "帳戶總值", 12),
            ("risk_pct", "風險%", 8),
            ("entry_price", "進場價", 10),
            ("stop_loss", "停損", 10),
            ("per_share_risk", "每股風險", 10),
            ("calculated_shares", "計算股數", 10),
            ("position_value", "倉位金額", 12),
            ("account_pct", "佔帳戶%", 10),
            ("trade_type", "交易類型", 14),
            ("sizing_verdict", "倉位判定", 12),
        ],
    },
    "禁止交易區": {
        "table": "no_trade_zone",
        "columns": [
            ("ntz_id", "禁區ID", 16),
            ("date", "日期", 12),
            ("zone_type", "類型", 12),
            ("reason", "原因", 30),
            ("affected_tickers", "影響標的", 20),
            ("start_date", "開始日", 12),
            ("end_date", "結束日", 12),
            ("is_active", "活躍", 6),
        ],
    },
    "偏誤檢查": {
        "table": "bias_check",
        "columns": [
            ("bias_id", "檢查ID", 16),
            ("ticker", "股票", 8),
            ("date", "日期", 12),
            ("is_already_held", "已持倉", 8),
            ("held_position_bias_deduction", "持倉扣分", 10),
            ("all_info_bullish", "全部利多", 10),
            ("excessive_consensus_warning", "過度一致", 10),
            ("social_unanimity", "社群一致", 10),
            ("media_hype", "媒體炒作", 10),
            ("counter_thesis_provided", "有反方論述", 10),
            ("bias_verdict", "偏誤判定", 12),
        ],
    },
    "決策疲勞": {
        "table": "fatigue_guard",
        "columns": [
            ("fatigue_id", "疲勞ID", 16),
            ("date", "日期", 12),
            ("recs_today", "今日推薦數", 10),
            ("max_recs_allowed", "上限", 6),
            ("consecutive_losses", "連續虧損", 10),
            ("losses_today", "今日虧損數", 10),
            ("is_cooled_down", "冷卻中", 8),
            ("fatigue_verdict", "疲勞判定", 12),
            ("allowed_grade", "允許等級", 10),
        ],
    },
    "勝率儀表板": {
        "table": "win_rate_dashboard",
        "columns": [
            ("snapshot_date", "快照日期", 12),
            ("total_recs", "總推薦", 8),
            ("wins", "勝利", 8),
            ("partial", "部分", 8),
            ("losses", "虧損", 8),
            ("win_rate", "勝率%", 8),
            ("t1_hit_rate", "T1命中%", 10),
            ("t2_hit_rate", "T2命中%", 10),
            ("stop_loss_rate", "停損率%", 10),
            ("avg_return", "平均報酬%", 10),
            ("avg_mfe", "平均MFE%", 10),
            ("avg_mae", "平均MAE%", 10),
            ("profit_factor", "賺賠比", 8),
            ("best_strategy", "最佳策略", 16),
            ("best_sector", "最佳板塊", 16),
            ("sample_size_sufficient", "樣本充足", 10),
        ],
    },
    "觀察名單結果": {
        "table": "watchlist_outcome",
        "columns": [
            ("watch_id", "觀察ID", 16),
            ("ticker", "股票", 8),
            ("original_date", "原始日期", 12),
            ("outcome_date", "結果日期", 12),
            ("outcome", "結果", 12),
            ("converted_to_rec", "轉推薦", 8),
            ("rec_id", "推薦ID", 16),
            ("missed_opportunity", "錯過", 8),
            ("missed_gain_pct", "錯過漲幅%", 10),
            ("false_negative", "偽陰性", 8),
        ],
    },
    "環境記憶": {
        "table": "regime_memory",
        "columns": [
            ("regime_id", "環境ID", 18),
            ("market_state", "市場狀態", 14),
            ("start_date", "開始日期", 12),
            ("end_date", "結束日期", 12),
            ("trigger_reason", "觸發原因", 30),
            ("spy_state", "SPY", 8),
            ("qqq_state", "QQQ", 8),
            ("vix_change", "VIX變化", 10),
            ("lessons", "經驗教訓", 40),
        ],
    },
}


def _default_export_path() -> Path:
    env_path = os.environ.get("US_ALPHA_DB_PATH")
    if env_path:
        return Path(env_path).parent / "US_Alpha_Records.xlsx"
    return Path.home() / "Desktop" / "us_alpha_db" / "US_Alpha_Records.xlsx"


def _apply_header_style(ws, col_count: int):
    """Apply header formatting to first row."""
    for col in range(1, col_count + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = _HEADER_ALIGNMENT
        cell.border = _THIN_BORDER


def _apply_grade_formatting(ws, col_idx: int, max_row: int):
    """Apply conditional color to grade columns."""
    col_letter = get_column_letter(col_idx)
    for row in range(2, max_row + 1):
        cell = ws.cell(row=row, column=col_idx)
        val = str(cell.value or "").strip()
        if val in _GRADE_FILLS:
            cell.fill = _GRADE_FILLS[val]


def _apply_risk_formatting(ws, col_idx: int, max_row: int):
    """Apply conditional color to risk/lock columns."""
    col_letter = get_column_letter(col_idx)
    for row in range(2, max_row + 1):
        cell = ws.cell(row=row, column=col_idx)
        val = str(cell.value or "").lower().strip()
        if val == "pass":
            cell.fill = _PASS_FILL
        elif val == "warning":
            cell.fill = _WARN_FILL
        elif val == "blocked":
            cell.fill = _BLOCK_FILL


def _write_sheet(ws, rows: List[Dict], columns: list):
    """Write data rows to a worksheet with formatting."""
    for col_idx, (key, header, width) in enumerate(columns, 1):
        ws.cell(row=1, column=col_idx, value=header)
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    _apply_header_style(ws, len(columns))

    grade_cols = []
    risk_cols = []

    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, (key, header, width) in enumerate(columns, 1):
            value = row_data.get(key)
            if value is None:
                value = ""
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = _DATA_FONT
            cell.alignment = _DATA_ALIGNMENT
            cell.border = _THIN_BORDER

    max_row = len(rows) + 1

    for col_idx, (key, header, width) in enumerate(columns, 1):
        if "grade" in key or key == "grade":
            _apply_grade_formatting(ws, col_idx, max_row)
        elif "risk_lock" in key or "risk" in key.lower():
            _apply_risk_formatting(ws, col_idx, max_row)

    ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{max_row}"
    ws.freeze_panes = "A2"

    if max_row < 2:
        return

    # Enhanced conditional formatting for numeric columns
    for col_idx, (key, header, width) in enumerate(columns, 1):
        col_letter = get_column_letter(col_idx)
        cell_range = f"{col_letter}2:{col_letter}{max_row}"

        if "pnl" in key or "performance" in key:
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="greaterThan", formula=["10"], fill=PatternFill(start_color="006100", end_color="006100", fill_type="solid"), font=Font(color="FFFFFF")),
            )
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="lessThan", formula=["-5"], fill=PatternFill(start_color="9C0006", end_color="9C0006", fill_type="solid"), font=Font(color="FFFFFF")),
            )
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="lessThan", formula=["0"], fill=PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")),
            )

        if "days_to" in key or key == "holding_days":
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="lessThanOrEqual", formula=["3"], fill=PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")),
            )
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="between", formula=["4", "7"], fill=PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")),
            )

        if key == "timing_passed" or key == "v22_compliant":
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="equal", formula=["0"], fill=PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")),
            )
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="equal", formula=["1"], fill=PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")),
            )

        if key == "can_add":
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="equal", formula=['"no"'], fill=PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")),
            )


def _write_summary_sheet(ws, db: AlphaDB):
    """Write formula-driven summary/dashboard sheet."""
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 36
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 36

    title_font = Font(name="Microsoft JhengHei", bold=True, size=16)
    section_font = Font(name="Microsoft JhengHei", bold=True, size=12, color="2F5496")
    data_font = Font(name="Microsoft JhengHei", size=11)
    value_font = Font(name="Microsoft JhengHei", bold=True, size=11)
    note_font = Font(name="Microsoft JhengHei", size=9, italic=True, color="666666")

    row = 1
    ws.cell(row=row, column=1, value="美股高報酬交易決策系統 v2.5").font = title_font
    row += 1
    ws.cell(row=row, column=1, value=f"匯出時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}").font = note_font
    ws.cell(row=row, column=3, value="HIGH_ALPHA_LAUNCHPAD_US_v2.5 | TIMING + EXIT + CORRELATION + BIAS + WIN_RATE").font = note_font
    row += 2

    # Section 1: System Status
    ws.cell(row=row, column=1, value="系統狀態").font = section_font
    ws.cell(row=row, column=4, value="v2.2 合規檢查").font = section_font
    row += 1

    counts = db.get_table_counts()
    table_names_zh = {
        "info_inbox": "資訊收錄",
        "market_gate": "市場環境",
        "sector_rank": "板塊評分",
        "catalyst_calendar": "催化劑",
        "score_audit": "評分審計",
        "formal_rec": "正式推薦",
        "watchlist": "觀察名單",
        "exclusion": "排除/封鎖",
        "holding": "持倉歷史",
        "holding_current": "當前持倉",
        "postmortem": "復盤紀錄",
        "model_change": "模型修正",
        "trade_plan": "交易計畫",
        "timing_gate": "時間閘門",
        "exit_plan": "出場計畫",
        "correlation_guard": "相關性檢查",
        "position_sizing": "倉位計算",
        "no_trade_zone": "禁止交易區",
        "bias_check": "偏誤檢查",
        "fatigue_guard": "決策疲勞",
        "win_rate_dashboard": "勝率儀表板",
        "watchlist_outcome": "觀察結果追蹤",
        "regime_memory": "環境記憶",
    }

    start_row = row
    for table, count in counts.items():
        zh_name = table_names_zh.get(table, table)
        ws.cell(row=row, column=1, value=zh_name).font = data_font
        cell = ws.cell(row=row, column=2, value=count)
        cell.font = value_font
        if count == 0:
            cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        row += 1

    # v2.5 compliance checks on right side
    row = start_row
    v22_checks = [
        ("v2.1 INFO_GATE", counts.get("info_inbox", 0) > 0),
        ("v2.1 MARKET_GATE", counts.get("market_gate", 0) > 0),
        ("v2.1 SECTOR_RANK", counts.get("sector_rank", 0) > 0),
        ("v2.1 RISK_LOCK", counts.get("exclusion", 0) > 0),
        ("v2.2 TIMING_ENGINE", counts.get("timing_gate", 0) > 0),
        ("v2.2 EXIT_ENGINE", counts.get("exit_plan", 0) > 0),
        ("v2.2 TRADE_PLAN", counts.get("trade_plan", 0) > 0),
        ("v2.3 CORRELATION_GUARD", counts.get("correlation_guard", 0) > 0),
        ("v2.3 POSITION_SIZING", counts.get("position_sizing", 0) > 0),
        ("v2.4 BIAS_FILTER", counts.get("bias_check", 0) > 0),
        ("v2.4 FATIGUE_GUARD", counts.get("fatigue_guard", 0) > 0),
        ("v2.5 WIN_RATE_DASHBOARD", counts.get("win_rate_dashboard", 0) > 0),
        ("v2.5 WATCHLIST_OUTCOME", counts.get("watchlist_outcome", 0) > 0),
        ("v2.5 REGIME_MEMORY", counts.get("regime_memory", 0) > 0),
    ]
    for label, ok in v22_checks:
        ws.cell(row=row, column=4, value=label).font = data_font
        cell = ws.cell(row=row, column=5, value="✓ 已啟用" if ok else "✗ 未啟用")
        cell.font = value_font
        cell.fill = _PASS_FILL if ok else PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        row += 1

    row += 2

    # Section 2: Performance
    ws.cell(row=row, column=1, value="績效統計").font = section_font
    ws.cell(row=row, column=4, value="風險控制").font = section_font
    row += 1

    stats = db.get_win_rate()
    perf_data = [
        ("總推薦數", stats.get("total", 0), "正式REC數量"),
        ("勝利", stats.get("wins", 0), "報酬≥10%"),
        ("部分成功", stats.get("partial", 0), "報酬0-10%"),
        ("虧損", stats.get("losses", 0), "報酬<0%"),
        ("勝率", f"{stats.get('win_rate', 0)}%", "勝利/總數"),
        ("平均報酬", f"{stats.get('avg_return', 0)}%", "全部推薦平均"),
        ("平均MFE", f"{stats.get('avg_mfe', 0)}%", "最大有利波動平均"),
        ("平均MAE", f"{stats.get('avg_mae', 0)}%", "最大不利波動平均"),
    ]
    for label, value, note in perf_data:
        ws.cell(row=row, column=1, value=label).font = data_font
        ws.cell(row=row, column=2, value=value).font = value_font
        ws.cell(row=row, column=3, value=note).font = note_font
        row += 1

    # Risk control on right side (use sector data)
    risk_row = row - len(perf_data)
    a_sectors = db._conn.execute("SELECT COUNT(*) as c FROM sector_rank WHERE grade='A'").fetchone()["c"]
    b_sectors = db._conn.execute("SELECT COUNT(*) as c FROM sector_rank WHERE grade='B'").fetchone()["c"]
    blocked = counts.get("exclusion", 0)
    active_watch = db._conn.execute("SELECT COUNT(*) as c FROM watchlist WHERE can_convert_to_rec=1").fetchone()["c"]
    current_hold = counts.get("holding_current", 0)

    risk_data = [
        ("A級主線板塊", a_sectors, "可積極做多"),
        ("B級強勢板塊", b_sectors, "可選股"),
        ("風險封鎖數", blocked, "不可觸碰"),
        ("活躍觀察名單", active_watch, "可能轉推薦"),
        ("當前持倉數", current_hold, "活躍倉位"),
        ("連續虧損", 0, "≥2收緊/≥3暫停"),
    ]
    for label, value, note in risk_data:
        ws.cell(row=risk_row, column=4, value=label).font = data_font
        ws.cell(row=risk_row, column=5, value=value).font = value_font
        risk_row += 1

    row += 2

    # Section 3: System Rules
    ws.cell(row=row, column=1, value="v2.5 核心紀律").font = section_font
    row += 1
    rules = [
        "1. 沒有 TIMING_GATE 通過，不可建立 REC",
        "2. 沒有 EXIT_PLAN，不可建立 REC",
        "3. 沒有完整 TRADE_PLAN（含反方論述），不可建立 REC",
        "4. RR < 2.5:1 不主推",
        "5. SEC 未通過直接封鎖",
        "6. S3 過熱不追",
        "7. 每日最多 3 支主推（FATIGUE_GUARD）",
        "8. 同板塊不超過 2 支主推（CORRELATION_GUARD）",
        "9. 已持倉重新評分自動扣 5 分（BIAS_FILTER）",
        "10. 2 連虧只做 A 級；3 連虧暫停",
        "11. 寧可不推薦也不硬推",
        "12. 每筆推薦都要可復盤、可追蹤 ID 鏈",
    ]
    for rule in rules:
        ws.cell(row=row, column=1, value=rule).font = data_font
        row += 1


_VALIDATION_RULES = {
    "資訊收錄": {
        "source_grade": "A1,A2,B,C,R,UNKNOWN",
        "initial_direction": "bullish,bearish,neutral,uncertain",
        "conclusion": "adopt,observe,isolate,exclude",
    },
    "市場環境": {
        "market_state": "risk_on,selective_bull,neutral_range,risk_off,event_only",
    },
    "板塊強度": {
        "grade": "A,B,C,WEAK",
    },
    "推薦紀錄": {
        "final_grade": "A,B,C,D,F,P",
        "market_state": "risk_on,selective_bull,neutral_range,risk_off,event_only",
        "momentum_state": "S0-A,S0-B,S0-C,S1,S2,S3,S4",
        "rec_type": "primary,secondary,small_event,continuation",
        "position_risk": "standard,half,small,forbidden",
    },
    "評分審計": {
        "final_grade": "A,B,C,D,F,P",
        "risk_lock": "pass,warning,blocked",
    },
    "時間閘門": {
        "timing_state": "T0_clear,T1_caution,T2_restricted,T3_earnings_zone,T4_event_lockout,T5_post_event",
        "timing_action": "clear,reduce,delay,block",
    },
    "持倉管理": {
        "action": "hold,add,reduce,stop_loss,wait",
        "next_action": "hold,add,reduce,exit,watch",
        "can_add": "yes,no,conditional",
    },
    "當前持倉": {
        "status": "active,closed,stopped",
        "next_action": "hold,add,reduce,exit,watch",
        "can_add": "yes,no,conditional",
        "momentum_state": "S0-A,S0-B,S0-C,S1,S2,S3,S4",
    },
    "復盤紀錄": {
        "review_period": "7d,30d,90d,180d,365d",
        "exit_trigger": "stop_loss,time_stop,t1_hit,t2_hit,trailing_stop,catalyst_fail,structure_break,manual",
        "error_type": "info_error,timing_error,chasing_error,sector_misjudge,risk_underestimate,catalyst_miss,market_turn,technical_fail,liquidity_misjudge,sec_dilution",
    },
    "觀察名單": {
        "layer": "core,standard,event,watch,pending,excluded",
    },
}


def _add_data_validations(wb: Workbook):
    """Add dropdown data validations to relevant sheets."""
    for sheet_name, fields in _VALIDATION_RULES.items():
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]

        header_map = {}
        for col in range(1, ws.max_column + 1):
            val = ws.cell(row=1, column=col).value
            if val:
                header_map[val] = col

        for col_key, allowed in fields.items():
            col_header_map = {
                "source_grade": "來源等級",
                "initial_direction": "方向",
                "conclusion": "結論",
                "market_state": "市場狀態",
                "grade": "等級",
                "final_grade": "等級",
                "momentum_state": "動能狀態",
                "rec_type": "推薦類型",
                "position_risk": "倉位風險",
                "risk_lock": "風險封鎖",
                "timing_state": "時間狀態",
                "timing_action": "動作",
                "action": "動作",
                "next_action": "下一步",
                "can_add": "可加碼",
                "status": "狀態",
                "review_period": "週期",
                "exit_trigger": "出場觸發",
                "error_type": "錯誤類型",
                "layer": "分層",
            }
            header_zh = col_header_map.get(col_key, col_key)
            if header_zh not in header_map:
                continue

            col_idx = header_map[header_zh]
            col_letter = get_column_letter(col_idx)
            dv = DataValidation(type="list", formula1=f'"{allowed}"', allow_blank=True)
            dv.error = f"請選擇有效值：{allowed}"
            dv.errorTitle = "輸入錯誤"
            ws.add_data_validation(dv)
            dv.add(f"{col_letter}2:{col_letter}1000")


def _add_id_chain_sheet(wb: Workbook, db: AlphaDB):
    """Add ID chain completeness check sheet."""
    ws = wb.create_sheet(title="ID鏈檢查")
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 14
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 14
    ws.column_dimensions["H"].width = 14
    ws.column_dimensions["I"].width = 14
    ws.column_dimensions["J"].width = 20

    headers = ["股票", "INFO_ID", "SCORE_ID", "WATCH/REC_ID", "PLAN_ID",
               "EXIT_ID", "TIMING_ID", "POSITION", "REVIEW_ID", "缺口"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = _HEADER_ALIGNMENT

    tickers_sql = """
        SELECT DISTINCT ticker FROM (
            SELECT ticker FROM holding_current
            UNION SELECT ticker FROM watchlist
            UNION SELECT ticker FROM score_audit
        )
    """
    tickers = [r["ticker"] for r in db._conn.execute(tickers_sql).fetchall()]

    for row_idx, ticker in enumerate(tickers, 2):
        ws.cell(row=row_idx, column=1, value=ticker)

        info = db._conn.execute("SELECT info_id FROM info_inbox WHERE tickers LIKE ?", (f'%{ticker}%',)).fetchone()
        ws.cell(row=row_idx, column=2, value=info["info_id"] if info else "✗")

        score = db._conn.execute("SELECT score_id FROM score_audit WHERE ticker=?", (ticker,)).fetchone()
        ws.cell(row=row_idx, column=3, value=score["score_id"] if score else "✗")

        watch = db._conn.execute("SELECT watch_id FROM watchlist WHERE ticker=?", (ticker,)).fetchone()
        rec = db._conn.execute("SELECT rec_id FROM formal_rec WHERE ticker=?", (ticker,)).fetchone()
        ref = (rec["rec_id"] if rec else watch["watch_id"] if watch else "✗")
        ws.cell(row=row_idx, column=4, value=ref)

        plan = db._conn.execute("SELECT id FROM trade_plan WHERE ticker=?", (ticker,)).fetchone()
        ws.cell(row=row_idx, column=5, value=f"PLAN-{plan['id']}" if plan else "✗")

        exit_p = db._conn.execute("SELECT id FROM exit_plan WHERE ticker=?", (ticker,)).fetchone()
        ws.cell(row=row_idx, column=6, value=f"EXIT-{exit_p['id']}" if exit_p else "✗")

        timing = db._conn.execute("SELECT id FROM timing_gate WHERE ticker=?", (ticker,)).fetchone()
        ws.cell(row=row_idx, column=7, value=f"TIME-{timing['id']}" if timing else "✗")

        pos = db._conn.execute("SELECT status FROM holding_current WHERE ticker=?", (ticker,)).fetchone()
        ws.cell(row=row_idx, column=8, value=pos["status"] if pos else "✗")

        review = db._conn.execute("SELECT id FROM postmortem WHERE ticker=?", (ticker,)).fetchone()
        ws.cell(row=row_idx, column=9, value=f"REV-{review['id']}" if review else "✗(待)")

        gaps = []
        if not score:
            gaps.append("SCORE")
        if not rec and not watch:
            gaps.append("REC/WATCH")
        if not plan:
            gaps.append("PLAN")
        if not exit_p:
            gaps.append("EXIT")
        if not review:
            gaps.append("REVIEW")
        gap_str = ", ".join(gaps) if gaps else "✓ 完整"
        cell = ws.cell(row=row_idx, column=10, value=gap_str)
        if gaps:
            cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        else:
            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")

    ws.freeze_panes = "A2"


def _add_data_dictionary_sheet(wb: Workbook):
    """Add data dictionary sheet for allowed values."""
    ws = wb.create_sheet(title="資料字典")
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 40

    headers = ["欄位名稱", "允許值", "說明"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL

    dictionary = [
        ("source_grade", "A1, A2, B, C, R, UNKNOWN", "A1=官方公告 A2=主流媒體 B=研報 C=社群 R=傳聞"),
        ("market_state", "risk_on, selective_bull, neutral_range, risk_off, event_only", "市場環境判定"),
        ("momentum_state", "S0-A, S0-B, S0-C, S1, S2, S3, S4", "爆發動能狀態機"),
        ("timing_state", "T0_clear, T1_caution, T2_restricted, T3_earnings_zone, T4_event_lockout, T5_post_event", "時間閘門狀態"),
        ("final_grade", "A, B, C, D, F, P", "A=主推 B=可推 C=觀察 D=不推 F=禁止 P=待查"),
        ("risk_lock", "pass, warning, blocked", "風險封鎖狀態"),
        ("rec_type", "primary, secondary, small_event, continuation", "推薦類型"),
        ("position_risk", "standard, half, small, forbidden", "建議倉位水準"),
        ("holding_action", "hold, add, reduce, stop_loss, wait", "持倉動作"),
        ("next_action", "hold, add, reduce, exit, watch", "下一步建議"),
        ("can_add", "yes, no, conditional", "是否允許加碼"),
        ("exit_trigger", "stop_loss, time_stop, t1_hit, t2_hit, trailing_stop, catalyst_fail, structure_break, manual", "出場觸發類型"),
        ("error_type", "info_error, timing_error, chasing_error, sector_misjudge, risk_underestimate, catalyst_miss, market_turn, technical_fail, liquidity_misjudge, sec_dilution", "復盤錯誤分類"),
        ("review_period", "7d, 30d, 90d, 180d, 365d", "復盤週期"),
        ("sector_grade", "A, B, C, WEAK", "A=85+ B=75-84 C=60-74 WEAK=<60"),
        ("info_conclusion", "adopt, observe, isolate, exclude", "資訊處理結論"),
        ("info_direction", "bullish, bearish, neutral, uncertain", "初步方向判斷"),
        ("concentration_verdict", "pass, warning, blocked", "相關性集中度判定"),
        ("bias_verdict", "clean, mild_bias, significant_bias, blocked", "確認偏誤判定"),
        ("fatigue_verdict", "clear, caution, restricted, blocked", "決策疲勞判定"),
        ("sample_guard", "insufficient(<20), borderline(20-30), sufficient(30+)", "樣本量是否足夠做模型調整"),
    ]

    for row_idx, (field, values, desc) in enumerate(dictionary, 2):
        ws.cell(row=row_idx, column=1, value=field)
        ws.cell(row=row_idx, column=2, value=values)
        ws.cell(row=row_idx, column=3, value=desc)

    ws.freeze_panes = "A2"


def export_to_excel(db: Optional[AlphaDB] = None, output_path: Optional[str] = None) -> str:
    """
    Export all database tables to a formatted Excel workbook.

    Args:
        db: AlphaDB instance (creates one if not provided)
        output_path: Custom output path (defaults to ~/Desktop/us_alpha_db/)

    Returns:
        Path to the created Excel file.
    """
    close_db = False
    if db is None:
        db = AlphaDB()
        close_db = True

    path = Path(output_path) if output_path else _default_export_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()

    summary_ws = wb.active
    summary_ws.title = "總覽"
    _write_summary_sheet(summary_ws, db)

    for sheet_name, config in _SHEETS.items():
        table = config["table"]
        columns = config["columns"]

        rows = db._conn.execute(f"SELECT * FROM {table} ORDER BY id DESC").fetchall()
        rows_data = [dict(r) for r in rows]

        ws = wb.create_sheet(title=sheet_name)
        _write_sheet(ws, rows_data, columns)

    _add_data_validations(wb)
    _add_id_chain_sheet(wb, db)
    _add_data_dictionary_sheet(wb)

    wb.save(str(path))

    if close_db:
        db.close()

    return str(path)
