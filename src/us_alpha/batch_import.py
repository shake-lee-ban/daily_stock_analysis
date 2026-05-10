# -*- coding: utf-8 -*-
"""
Batch import historical INFO records into the US Alpha database.

This script imports the full INFO_INBOX backlog as provided by the user,
covering 2026-05-07 through 2026-05-10 across macro, sector, individual
stock, options flow, and system update categories.
"""

from datetime import date, datetime

from .schemas import (
    CandidateLayer,
    CatalystCertainty,
    CatalystEntry,
    CatalystType,
    ExclusionEntry,
    FutuPoolSource,
    HoldingAction,
    HoldingEntry,
    InfoConclusion,
    InfoDirection,
    InfoInboxEntry,
    MarketGateEntry,
    MarketState,
    MomentumState,
    ModelChangeEntry,
    SectorGrade,
    SectorRankEntry,
    SourceGrade,
    WatchlistEntry,
)
from .storage import AlphaDB


def import_all_historical(db: AlphaDB):
    """Import all historical records from the 2026-05-07 to 2026-05-10 sessions."""
    _import_macro_info(db)
    _import_ai_semi_info(db)
    _import_software_info(db)
    _import_futu_scan_info(db)
    _import_individual_stock_info(db)
    _import_options_sentiment_info(db)
    _import_market_gate(db)
    _import_sector_ranks(db)
    _import_catalysts(db)
    _import_holdings(db)
    _import_watchlist(db)
    _import_exclusions(db)
    _import_model_changes(db)


def _import_macro_info(db: AlphaDB):
    """Category 1: Macro & Market Environment."""
    entries = [
        InfoInboxEntry(
            info_id="INFO-20260507-004",
            timestamp=datetime(2026, 5, 7, 9, 0),
            raw_content="ADP就業韌性仍在，Fed降息預期降溫，油價與美元影響風險偏好。支持選擇性多頭，不是全面風險強攻。",
            market="us",
            tickers=["SPY", "QQQ"],
            initial_direction=InfoDirection.NEUTRAL,
            needs_verification=False,
            enters_scoring=True,
            source_grade=SourceGrade.A2,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-005",
            timestamp=datetime(2026, 5, 7, 10, 0),
            raw_content="美國/伊朗談判不確定，中東局勢仍可能影響油價、航運、風險資產。屬地緣風險，不是直接買股理由。",
            market="us",
            tickers=[],
            initial_direction=InfoDirection.BEARISH,
            needs_verification=True,
            enters_scoring=False,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.OBSERVE,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-006",
            timestamp=datetime(2026, 5, 7, 10, 30),
            raw_content="霍爾木茲風險、油價、航運通道可能影響市場。對高beta、小型股、航空、消費風險偏負面。",
            market="us",
            tickers=[],
            initial_direction=InfoDirection.BEARISH,
            needs_verification=True,
            enters_scoring=False,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.OBSERVE,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-HORMUZ-002",
            timestamp=datetime(2026, 5, 7, 11, 0),
            raw_content="沙烏地/科威特恢復美軍基地與空域通行。可能提高美國對Hormuz航線護航或軍事行動能力。油價、黃金、風險資產短線波動升高。",
            market="us",
            tickers=[],
            initial_direction=InfoDirection.UNCERTAIN,
            needs_verification=True,
            enters_scoring=False,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.OBSERVE,
        ),
        InfoInboxEntry(
            info_id="BATCH-20260508-PRE-002",
            timestamp=datetime(2026, 5, 8, 8, 0),
            raw_content="NFP高波動事件框架：2026年NFP波動大，單月數據不穩定，公布前不宜重倉押方向。NFP前禁止強推高波動標的。",
            market="us",
            tickers=["SPY", "QQQ", "IWM"],
            initial_direction=InfoDirection.NEUTRAL,
            needs_verification=False,
            enters_scoring=True,
            source_grade=SourceGrade.A2,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260508-NFP-001",
            timestamp=datetime(2026, 5, 8, 9, 30),
            raw_content="4月非農就業資料：醫療、零售、休閒、運輸就業增加；製造、資訊、金融收縮。勞動市場韌性仍在，但不是明確降息利多。",
            market="us",
            tickers=["SPY"],
            initial_direction=InfoDirection.NEUTRAL,
            needs_verification=False,
            enters_scoring=True,
            source_grade=SourceGrade.A2,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260509-MKT-001",
            timestamp=datetime(2026, 5, 9, 9, 0),
            raw_content="美股創高、SOX狂熱、Fed風險。S&P/Nasdaq創新高，SOX大漲，MU/INTC/AMD/SNDK過熱；Roger Ferguson提到今年可能不排除升息。風險偏好強但半導體擁擠交易升高。",
            market="us",
            tickers=["SPY", "QQQ", "SMH", "MU", "INTC", "AMD"],
            initial_direction=InfoDirection.BULLISH,
            needs_verification=False,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
    ]
    for e in entries:
        db.save_info(e)


def _import_ai_semi_info(db: AlphaDB):
    """Category 2: AI / Semiconductor / Memory / Hardware."""
    entries = [
        InfoInboxEntry(
            info_id="INFO-20260507-002",
            timestamp=datetime(2026, 5, 7, 9, 30),
            raw_content="AI半導體輪動、NVDA-Corning、AMD等。AI半導體、光通訊、資料中心供應鏈持續強勢。支持AI infrastructure主線。",
            market="us",
            tickers=["NVDA", "AMD", "GLW", "AVGO"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-SEMI-OVERHEAT-001",
            timestamp=datetime(2026, 5, 7, 14, 0),
            raw_content="半導體狂熱接近2000泡沫警告。SOXL、AMD、記憶體、CPU、AI半導體全面擁擠；但AI需求仍是真實支撐。主線仍強但短線追高風險大。",
            market="us",
            tickers=["SMH", "AMD", "MU", "INTC"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-GPU-BUDGET-001",
            timestamp=datetime(2026, 5, 7, 15, 0),
            raw_content="BBAT 2026 GPU採購預算傳聞：ByteDance、Tencent、Alibaba、Baidu GPU預算估算。只能作AI capex方向觀察，不可直接加分。",
            market="us",
            tickers=["NVDA", "AMD"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=False,
            source_grade=SourceGrade.C,
            conclusion=InfoConclusion.ISOLATE,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-CPU-CLOUD-001",
            timestamp=datetime(2026, 5, 7, 15, 30),
            raw_content="Token demand inflation：CPU到雲服務。Agentic AI可能推升CPU、主機記憶體、DRAM、雲端伺服器需求。支持AMD/ARM/INTC/GOOGL/MSFT/AMZN的AI CPU子題材。",
            market="us",
            tickers=["AMD", "ARM", "INTC", "GOOGL", "MSFT", "AMZN"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260509-MU-001",
            timestamp=datetime(2026, 5, 9, 10, 0),
            raw_content="MU記憶體拋物線式上漲：單日+15%左右，週漲近38%，月漲近84%；DRAM/NAND/HBM供需緊張。記憶體主線確認，但MU進入S3過熱，不追高。",
            market="us",
            tickers=["MU"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260509-AIHARDWARE-001",
            timestamp=datetime(2026, 5, 9, 11, 0),
            raw_content="AI基礎建設從NVDA擴散到AMD/INTC/MU/GLW。AI inference、CPU、記憶體、光通訊受重估；BTIG警告SOX可能修正25-30%。主線確認但所有垂直急漲標的都要等回踩。",
            market="us",
            tickers=["NVDA", "AMD", "INTC", "MU", "GLW"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260509-POWER-001",
            timestamp=datetime(2026, 5, 9, 12, 0),
            raw_content="Goldman：AI資料中心電力需求可能兩年翻倍。美國資料中心電力需求可能從約31GW增至66GW；電網、變壓器、施工週期成瓶頸。AI power bottleneck升級為一線主題。觀察CEG/VST/NRG/ETN/PWR/GEV/VRT。",
            market="us",
            tickers=["CEG", "VST", "NRG", "ETN", "PWR", "GEV", "VRT"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260508-INTC-APPLE-001",
            timestamp=datetime(2026, 5, 8, 14, 0),
            raw_content="Apple/Intel代工合作傳聞式報導：媒體稱Apple與Intel初步代工合作，政府可能推動，INTC大漲。因非官方公告，只能列入INTC/TSM/AAPL供應鏈觀察，不可直接加分。",
            market="us",
            tickers=["INTC", "AAPL", "TSM"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=False,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.OBSERVE,
            affected_module="待查，需WSJ原文或公司確認",
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-067",
            timestamp=datetime(2026, 5, 7, 16, 0),
            raw_content="Intel類Cisco泡沫警告：INTC技術與估值延伸被比作dot-com泡沫風險。INTC不追高，半導體風險備忘。",
            market="us",
            tickers=["INTC"],
            initial_direction=InfoDirection.BEARISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
    ]
    for e in entries:
        db.save_info(e)


def _import_software_info(db: AlphaDB):
    """Category 3: AI Software / Cloud / Cybersecurity."""
    entries = [
        InfoInboxEntry(
            info_id="INFO-20260507-077",
            timestamp=datetime(2026, 5, 7, 13, 0),
            raw_content="AI生產力、Agentic AI、雲端/軟體牛市。AI推升生產力，agentic AI、雲端、軟體應用受益。支持AI software/cloud/cybersecurity輪動。",
            market="us",
            tickers=["DDOG", "FTNT", "ZS", "CRWD"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-078",
            timestamp=datetime(2026, 5, 7, 13, 30),
            raw_content="IBD盤中更新：軟體強，半導體分化，小型股弱。DDOG/FTNT/ZS強，ARM/SNDK弱，小型股IWM弱。軟體/網安升溫，但小型股不能激進。",
            market="us",
            tickers=["DDOG", "FTNT", "ZS", "ARM", "IWM"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-083",
            timestamp=datetime(2026, 5, 7, 14, 30),
            raw_content="Rapid7分析師與財報電話會議：RPD Q1略優但ARR近乎持平，FY2026營收預期下滑，多家券商降目標價。RPD從可交易候選降為C+/B-，只能hold-only/watch，不可加碼。",
            market="us",
            tickers=["RPD"],
            initial_direction=InfoDirection.BEARISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
    ]
    for e in entries:
        db.save_info(e)


def _import_futu_scan_info(db: AlphaDB):
    """Category 4: Futu Screener / Market Scan."""
    entries = [
        InfoInboxEntry(
            info_id="INFO-20260508-HEATMAP-001",
            timestamp=datetime(2026, 5, 8, 10, 0),
            raw_content="富途熱力圖與板塊榜單：半導體、電腦硬體、半導體設備、太陽能強；軟體、醫療、廣告偏弱。板塊主線偏硬體，但多數已過熱。",
            market="us",
            tickers=["SMH"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260508-SCAN-001",
            timestamp=datetime(2026, 5, 8, 10, 30),
            raw_content="富途區間漲幅/選股器結果：GRPN、SHMD、FNKO、MX、GCTS、TRAW、EVTV等進入S1/S2池。大多是高波動小票，只能逐檔排雷，不能直接推薦。",
            market="us",
            tickers=["GRPN", "SHMD", "FNKO", "MX", "GCTS", "TRAW", "EVTV"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=False,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.OBSERVE,
        ),
        InfoInboxEntry(
            info_id="INFO-20260508-SCAN-002",
            timestamp=datetime(2026, 5, 8, 11, 0),
            raw_content="S1-A嚴格點火：GCTS、TRAW短線爆發動能強。需要SEC/流動性/催化劑檢查，未通過前不主推。",
            market="us",
            tickers=["GCTS", "TRAW"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=False,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.OBSERVE,
        ),
    ]
    for e in entries:
        db.save_info(e)


def _import_individual_stock_info(db: AlphaDB):
    """Category 5: Individual stock & position info."""
    entries = [
        InfoInboxEntry(
            info_id="INFO-20260509-MIST-001",
            timestamp=datetime(2026, 5, 9, 14, 0),
            raw_content="MIST IQVIA TRx：1月682、2月2947、3月9713、4月15876；但Q1 revenue $29.8M與TRx×ASP不一致。數據重要但未驗證；收入口徑有疑點；2026-05-13前不加碼。",
            market="us",
            tickers=["MIST"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=False,
            source_grade=SourceGrade.C,
            conclusion=InfoConclusion.OBSERVE,
            affected_module="事件持有/待查",
        ),
        InfoInboxEntry(
            info_id="INFO-20260509-CRSR-001",
            timestamp=datetime(2026, 5, 9, 15, 0),
            raw_content="CRSR進入S1-B/S2池。持倉120股，成本7.73；晚盤/收盤附近技術跟進至7.88。持有；8.20 T1，8.80-9.00 T2；7.20減倉/停損，7.00硬失效。",
            market="us",
            tickers=["CRSR"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260508-MRVL-001",
            timestamp=datetime(2026, 5, 8, 13, 0),
            raw_content="MRVL持倉盤中管理：仍有效但未breakout confirmed；167.4上方才可加碼。守165/164/162.8。後續已獲利+51.64美元稅費前。交易已關閉。",
            market="us",
            tickers=["MRVL"],
            initial_direction=InfoDirection.BULLISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
        InfoInboxEntry(
            info_id="INFO-20260507-RPD-HOLD-001",
            timestamp=datetime(2026, 5, 7, 15, 0),
            raw_content="RPD先前持倉成本6.80、155股；後續因公司展望弱被降級。若仍持有需重新提供最新股數與成本；舊邏輯已削弱。",
            market="us",
            tickers=["RPD"],
            initial_direction=InfoDirection.BEARISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
    ]
    for e in entries:
        db.save_info(e)


def _import_options_sentiment_info(db: AlphaDB):
    """Category 6: Options flow / Sentiment."""
    entries = [
        InfoInboxEntry(
            info_id="INFO-20260508-OPT-001",
            timestamp=datetime(2026, 5, 8, 16, 0),
            raw_content="消費可選股異常選擇權：TSLA/NKE/RCL/FLUT等出現bearish/neutral put或call flow；TPR/SGI有偏多流。選擇權流向歧義大，只能作情緒輔助，不可單獨做買賣依據。",
            market="us",
            tickers=["TSLA", "NKE", "RCL", "FLUT", "TPR", "SGI"],
            initial_direction=InfoDirection.UNCERTAIN,
            enters_scoring=False,
            source_grade=SourceGrade.C,
            conclusion=InfoConclusion.OBSERVE,
        ),
        InfoInboxEntry(
            info_id="INFO-20260509-SENTIMENT-001",
            timestamp=datetime(2026, 5, 9, 16, 0),
            raw_content="市場極度追逐AI/半導體：MU/INTC/AMD/SOX過熱，散戶與媒體關注升高。啟動SENTIMENT_GAUGE雛形：過熱冷卻，不追高。",
            market="us",
            tickers=["MU", "INTC", "AMD", "SMH"],
            initial_direction=InfoDirection.BEARISH,
            enters_scoring=True,
            source_grade=SourceGrade.B,
            conclusion=InfoConclusion.ADOPT,
        ),
    ]
    for e in entries:
        db.save_info(e)


def _import_market_gate(db: AlphaDB):
    """Import market environment snapshots."""
    entries = [
        MarketGateEntry(
            date=date(2026, 5, 9),
            spy_trend="up",
            qqq_trend="up",
            iwm_trend="range",
            smh_trend="up",
            xlv_trend="range",
            xbi_trend="range",
            vix_level=13.5,
            market_state=MarketState.SELECTIVE_BULL,
            notes="S&P/Nasdaq創新高，SOX大漲，但IWM弱。選擇性多頭，不是全面風險強攻。半導體擁擠交易升高。",
        ),
    ]
    for e in entries:
        db.save_market_gate(e)


def _import_sector_ranks(db: AlphaDB):
    """Import sector strength rankings."""
    d = date(2026, 5, 9)
    entries = [
        SectorRankEntry(date=d, sector_name="AI Infrastructure", info_heat=19, fund_flow=18, relative_strength=19, catalyst_density=14, macro_alignment=14, sustainability=9, representative_tickers=["NVDA", "AVGO", "MRVL", "GLW"]),
        SectorRankEntry(date=d, sector_name="Semiconductor / AI ASIC / Networking / CPO", info_heat=18, fund_flow=19, relative_strength=19, catalyst_density=13, macro_alignment=13, sustainability=8, representative_tickers=["AVGO", "MRVL", "ANET", "COHR"]),
        SectorRankEntry(date=d, sector_name="Memory / HBM / NAND / SSD", info_heat=17, fund_flow=18, relative_strength=18, catalyst_density=12, macro_alignment=12, sustainability=6, representative_tickers=["MU", "WDC", "SNDK"], notes="主線確認但多數標的S3過熱"),
        SectorRankEntry(date=d, sector_name="AI Software / Cloud / Agentic AI", info_heat=15, fund_flow=14, relative_strength=16, catalyst_density=12, macro_alignment=13, sustainability=8, representative_tickers=["DDOG", "CRWD", "ZS", "FTNT"]),
        SectorRankEntry(date=d, sector_name="AI Data Center Power", info_heat=14, fund_flow=13, relative_strength=15, catalyst_density=11, macro_alignment=13, sustainability=8, representative_tickers=["CEG", "VST", "NRG", "ETN", "VRT"], notes="新升級主線，Goldman報告確認"),
        SectorRankEntry(date=d, sector_name="Biotech / Healthcare Events", info_heat=10, fund_flow=8, relative_strength=9, catalyst_density=10, macro_alignment=7, sustainability=5, representative_tickers=["MIST", "MRNA", "REGN"]),
        SectorRankEntry(date=d, sector_name="Consumer Electronics / PC / Gaming", info_heat=8, fund_flow=9, relative_strength=10, catalyst_density=7, macro_alignment=8, sustainability=5, representative_tickers=["CRSR", "LOGI"]),
        SectorRankEntry(date=d, sector_name="Cybersecurity", info_heat=13, fund_flow=12, relative_strength=14, catalyst_density=10, macro_alignment=12, sustainability=8, representative_tickers=["FTNT", "ZS", "CRWD", "PANW"]),
    ]
    for e in entries:
        db.save_sector_rank(e)


def _import_catalysts(db: AlphaDB):
    """Import catalyst calendar entries."""
    entries = [
        CatalystEntry(catalyst_id="CAT-20260509-MIST-001", ticker="MIST", event_type=CatalystType.EARNINGS, expected_date="2026-05-13", certainty=CatalystCertainty.HIGH, bull_scenario="TRx加速確認+收入超預期", bear_scenario="TRx與revenue口徑矛盾未解、指引弱", priced_in="partial", pre_event_strategy="持有不加碼，等事件後確認"),
        CatalystEntry(catalyst_id="CAT-20260509-MU-001", ticker="MU", event_type=CatalystType.EARNINGS, expected_date="2026-06-25", certainty=CatalystCertainty.MEDIUM, bull_scenario="HBM需求持續+DRAM ASP上修", bear_scenario="過熱估值修正", priced_in="partial", pre_event_strategy="S3過熱不追，等回踩"),
    ]
    for e in entries:
        db.save_catalyst(e)


def _import_holdings(db: AlphaDB):
    """Import current holding status."""
    entries = [
        HoldingEntry(
            ticker="CRSR",
            timestamp=datetime(2026, 5, 9, 16, 0),
            action=HoldingAction.HOLD,
            avg_cost=7.73,
            current_price=7.88,
            shares=120,
            pnl_pct=1.94,
            key_support=7.20,
            alert_price=7.50,
            invalidation_price=7.00,
            target_1=8.20,
            target_2=9.00,
            original_thesis_valid=True,
            notes="S1-B/S2確認中；不追高，守7.85-8.00",
        ),
        HoldingEntry(
            ticker="MIST",
            timestamp=datetime(2026, 5, 9, 16, 0),
            action=HoldingAction.HOLD,
            avg_cost=None,
            current_price=None,
            original_thesis_valid=True,
            notes="事件持倉；2026-05-13前不加碼；TRx數據正面但revenue口徑待驗證",
        ),
        HoldingEntry(
            ticker="MRVL",
            timestamp=datetime(2026, 5, 8, 16, 0),
            action=HoldingAction.REDUCE,
            avg_cost=165.50,
            shares=6,
            pnl_pct=None,
            notes="已獲利結案 +$51.64 稅費前。交易已關閉。",
            original_thesis_valid=True,
        ),
    ]
    for e in entries:
        db.save_holding(e)


def _import_watchlist(db: AlphaDB):
    """Import watchlist entries."""
    entries = [
        WatchlistEntry(watch_id="WATCH-20260509-001", date=date(2026, 5, 9), ticker="CEG", layer=CandidateLayer.WATCH, watch_reason="AI data center power主線，Goldman報告確認", fail_reason="需確認是否已大幅反映", trigger_condition="回踩20EMA支撐+放量", can_convert_to_rec=True, next_check_date=date(2026, 5, 12)),
        WatchlistEntry(watch_id="WATCH-20260509-002", date=date(2026, 5, 9), ticker="VST", layer=CandidateLayer.WATCH, watch_reason="AI power主線代表", fail_reason="位置可能偏高", trigger_condition="回踩確認", can_convert_to_rec=True, next_check_date=date(2026, 5, 12)),
        WatchlistEntry(watch_id="WATCH-20260509-003", date=date(2026, 5, 9), ticker="GCTS", layer=CandidateLayer.PENDING, watch_reason="S1-A嚴格點火池", fail_reason="SEC/流動性/催化劑未查", trigger_condition="通過排雷後再評估", can_convert_to_rec=False, next_check_date=date(2026, 5, 12)),
        WatchlistEntry(watch_id="WATCH-20260509-004", date=date(2026, 5, 9), ticker="TRAW", layer=CandidateLayer.PENDING, watch_reason="S1-A嚴格點火池", fail_reason="SEC/流動性/催化劑未查", trigger_condition="通過排雷後再評估", can_convert_to_rec=False, next_check_date=date(2026, 5, 12)),
    ]
    for e in entries:
        db.save_watchlist(e)


def _import_exclusions(db: AlphaDB):
    """Import exclusion list."""
    entries = [
        ExclusionEntry(ticker="MU", date=date(2026, 5, 9), reason="S3過熱：單日+15%，週+38%，月+84%", category="overheated", duration="until_pullback"),
        ExclusionEntry(ticker="INTC", date=date(2026, 5, 9), reason="類Cisco泡沫警告+Apple代工未確認+垂直噴出", category="overheated", duration="until_pullback"),
        ExclusionEntry(ticker="AMD", date=date(2026, 5, 9), reason="SOX整體過熱，AMD延伸過快", category="overheated", duration="until_pullback"),
    ]
    for e in entries:
        db.save_exclusion(e)


def _import_model_changes(db: AlphaDB):
    """Import system/model change records."""
    entries = [
        ModelChangeEntry(change_date=date(2026, 5, 8), triggered_by="SYS-20260508-001", module_changed="STRATEGY_ROUTER", change_description="建立富途四選股器：S0潛伏池/S1-A嚴格點火/S1-B寬版點火/S2續航池", rationale="系統化Futu掃描結果的分層與優先級"),
        ModelChangeEntry(change_date=date(2026, 5, 8), triggered_by="SYS-20260508-002", module_changed="HIGH_ALPHA_LAUNCHPAD", change_description="啟用v2.1：SEC排雷先行、催化不明不主推、RS<70不主推、spread>2%不主推、RR≥2.5:1", rationale="防止低品質推薦進入正式名單"),
        ModelChangeEntry(change_date=date(2026, 5, 10), triggered_by="SYS-20260510-001", module_changed="SYSTEM", change_description="v2.2升級路線圖批准：新增TIMING_ENGINE、EXIT_ENGINE、TRADE_PLAN_TEMPLATE", rationale="系統從選股器升級為交易決策系統"),
        ModelChangeEntry(change_date=date(2026, 5, 10), triggered_by="MODEL-CHANGE-20260510-v2.2-001", module_changed="REC_ENGINE", change_description="v2.2正式執行：沒有Timing/Exit/Trade Plan不可建立REC", rationale="確保每筆推薦都有完整進出場計畫"),
    ]
    for e in entries:
        db.save_model_change(e)
