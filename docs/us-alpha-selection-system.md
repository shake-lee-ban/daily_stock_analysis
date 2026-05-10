# 美股高報酬選股與交易決策系統

## 系統定位

不隨便推薦股票。所有標的都必須經過完整流程：

```
資訊閘門 → 市場判斷 → 板塊強度 → 策略分類 → SEC/稀釋排雷
→ 催化劑驗證 → 技術面 → 流動性 → 風險報酬比
→ 推薦/觀察/排除 → 復盤修正
```

## 模組總覽

| 模組 | 版本 | 用途 | 代碼位置 |
|------|------|------|----------|
| INFO_GATE | v1.0 | 資訊來源分級、防污染、查證 | `src/us_alpha/info_gate.py` |
| MARKET_GATE | v1.0 | 市場環境判斷 | `src/us_alpha/market_gate.py` |
| SECTOR_RANK | v1.0 | 板塊強度排行榜 | `src/us_alpha/sector_rank.py` |
| STRATEGY_ROUTER | v1.0 | 策略路由分配 | `src/us_alpha/strategy_router.py` |
| RISK_LOCK_ENGINE | v1.0 | SEC/流動性/過熱/稀釋/風險報酬比封鎖 | `src/us_alpha/risk_engine.py` |
| SCORE_ENGINE | v1.0 | 評分、分級與動作判定 | `src/us_alpha/score_engine.py` |
| REC_ENGINE | v1.0 | 正式推薦資格與輸出 | `src/us_alpha/rec_engine.py` |
| POSTMORTEM_ENGINE | v1.0 | 復盤與模型進化 | `src/us_alpha/postmortem.py` |
| Schemas | v1.0 | 全部資料模型定義 | `src/us_alpha/schemas.py` |

## 策略版本

| 策略 | 版本 | 適用場景 |
|------|------|----------|
| CORE_US | v2.0 | 主流強勢股：財報上修、主流題材、相對強勢、回踩續攻 |
| HIGH_ALPHA_LAUNCHPAD_US | v2.1 | 高報酬飆股掃描總控模型 |
| EXPLOSIVE_MOMENTUM_US | v2.1 | 爆發動能狀態機：S0/S1/S2/S3/S4 |
| US_Equity_Alpha_Selection | v3.0 | 大型優質股/主線輪動/市場環境選股（輔助） |
| SPEC_EVENT | v1.0 | 事件股、生技催化、財報前後特殊標的 |

## 系統流程

```
使用者輸入資訊/新聞/截圖/富途選股結果/持倉
        ↓
【INFO_INBOX】原始資訊收錄
        ↓
【INFO_GATE】來源分級 (A1/A2/B/C/R/UNKNOWN)、查證
        ↓
【MARKET_GATE】市場環境判斷 (SPY/QQQ/IWM/SMH/VIX/美債/美元/油價/Fed)
        ↓
【SECTOR_RANK】板塊強度排行 (6維度/100分)
        ↓
【STRATEGY_ROUTER】策略分配
        ↓
【候選股票池分層】核心/標準/事件/觀察/待查/排除
        ↓
【RISK_LOCK_ENGINE】SEC/稀釋/流動性/過熱/催化/RR排雷
        ↓
【SCORE_ENGINE】主分數、扣分、封鎖、等級、動作
        ↓
【REC_ENGINE】是否建立正式推薦
        ↓
【POSTMORTEM_ENGINE】7/30/90/180/365日復盤
```

## 資訊來源等級

| 等級 | 來源 | 可否進入正式評分 |
|------|------|------------------|
| A1 | SEC、公司公告、FDA/EMA、官方財報、Fed、官方數據 | 可以 |
| A2 | Reuters、Bloomberg、CNBC、WSJ、主流媒體 | 可以（需確認事實vs解讀） |
| B | 券商報告、行業報告、研報、專家訪談 | 可低權重使用 |
| C | X、Reddit、YouTube、社群貼文 | 不可直接進主分數 |
| R | 傳聞、無來源截圖、單一帳號爆料 | 只能放風險/情緒備忘錄 |
| UNKNOWN | 來源不明 | 隔離，不進模型 |

## 市場狀態

| 狀態 | 操作指引 |
|------|----------|
| 風險偏好強攻 (RISK_ON) | 可積極找 S1/S2，高分股可分批進 |
| 選擇性多頭 (SELECTIVE_BULL) | 只做主線板塊與強勢個股 |
| 中性震盪 (NEUTRAL_RANGE) | 降低倉位，等回踩與確認 |
| 風險退潮 (RISK_OFF) | 不追高，不做低流動性小票 |
| 事件限定 (EVENT_ONLY) | 只做有明確催化劑的標的，小倉 |

## 板塊評分（100分制）

| 維度 | 權重 |
|------|------|
| 資訊熱度 | 20 |
| 資金流/成交量 | 20 |
| 相對強度 | 20 |
| 催化劑密度 | 15 |
| 宏觀環境配合度 | 15 |
| 可持續性 | 10 |

等級：A (85+) / B (75-84) / C (60-74) / WEAK (<60)

## 動能狀態機 (EXPLOSIVE_MOMENTUM)

| 狀態 | 定義 | 動作 |
|------|------|------|
| S0-A | 乾淨潛伏/核心追蹤 | 高優先觀察 |
| S0-B | 普通潛伏 | 觀察 |
| S0-C | 噪音/資訊不足 | 排除或待查 |
| S1 | 起漲初期，剛確認 | 重點觀察，可等進場 |
| S2 | 續航強勢 | 可交易，但不可追太高 |
| S3 | 過熱 | **禁止追高** |
| S4 | 退潮或失效 | 移除/封鎖 |

## 富途四池優先級

| 優先級 | 條件 | 解讀 |
|--------|------|------|
| P1 | S1-B + S2 | 最值得優先研究 |
| P2 | S1-A + S2 | 強勢續航候選 |
| P3 | S1-A only | 強點火，需確認是否過熱 |
| P4 | S1-B only | 早期觀察 |
| P5 | S0 only | 潛伏觀察，不主推 |

## 評分等級

| 等級 | 動作 |
|------|------|
| A | 主推候選：標準倉/可分批 |
| B | 可推薦：半倉以下/必須等進場點 |
| C | 觀察：不進場 |
| D | 不推薦：不進場 |
| F | 禁止推薦：封鎖 |
| P | Pending 待查：不進場 |

## 風險封鎖條件

- SEC 未通過 → 不看技術，直接封鎖
- 催化劑不明 → 不主推
- RS < 70 → 不主推
- Spread > 2% → 不主推
- RR < 2.5:1 → 不主推
- S3 過熱 → 不追，等回踩
- S4 失效 → 移除或封鎖
- 無法設停損 → 不主推

## 核心紀律

1. 先判斷市場，再選股
2. 先做資訊分級，再做評分
3. 未確認消息不能直接加分
4. SEC 風險未通過，不看技術面
5. 沒有催化劑，不做主推
6. 沒有明確停損，不做主推
7. RR < 2.5:1，不做主推
8. S3 過熱不追
9. S4 失效移除
10. 寧可不推薦，也不硬推
11. 每筆推薦都要可復盤
12. 每次錯誤都要分類，但不能因單次錯誤亂改模型

## 使用方式

```python
from src.us_alpha.info_gate import process_info
from src.us_alpha.market_gate import build_market_gate_entry
from src.us_alpha.sector_rank import score_sector, rank_sectors
from src.us_alpha.strategy_router import CandidateStock, route_strategy
from src.us_alpha.risk_engine import run_full_risk_assessment
from src.us_alpha.score_engine import ScoreInput, score_candidate
from src.us_alpha.rec_engine import qualifies_for_rec, build_recommendation
from src.us_alpha.postmortem import create_postmortem, compute_summary
```

## 資料表

| 資料表 | Schema | 用途 |
|--------|--------|------|
| INFO_INBOX_LOG | `InfoInboxEntry` | 原始資訊輸入 |
| MARKET_GATE_LOG | `MarketGateEntry` | 市場環境判斷 |
| SECTOR_RANK_LOG | `SectorRankEntry` | 板塊強度排行 |
| CATALYST_CALENDAR | `CatalystEntry` | 催化劑行事曆 |
| SCORE_AUDIT_LOG | `ScoreAuditEntry` | 分數變動審計 |
| FORMAL_REC_DB | `FormalRecommendation` | 正式推薦資料庫 |
| WATCHLIST_SIGNAL_LOG | `WatchlistEntry` | 觀察名單 |
| EXCLUSION_LOG | `ExclusionEntry` | 排除紀錄 |
| HOLDING_MANAGEMENT_LOG | `HoldingEntry` | 持倉管理紀錄 |
| POSTMORTEM_LOG | `PostmortemEntry` | 復盤資料庫 |
| MODEL_CHANGE_LOG | `ModelChangeEntry` | 模型修正紀錄 |
