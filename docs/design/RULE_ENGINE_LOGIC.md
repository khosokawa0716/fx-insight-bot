# ルールエンジン判定ロジック仕様

**バージョン**: v1.0
**最終更新**: 2026-01-12
**実装ファイル**: [backend/src/services/rule_engine.py](../../backend/src/services/rule_engine.py)

---

## 概要

ルールエンジンは、ニュース分析結果とテクニカル指標を統合してトレードシグナル（buy/sell/hold）を生成します。スコアリングシステムにより、複数の要因を総合的に判断し、信頼度付きのシグナルを出力します。

---

## トレードシグナル生成フロー

### 1. データ取得

#### 1.1 テクニカル指標取得

**関数**: `TechnicalAnalyzer.get_indicators()`

```python
technical = self.technical_analyzer.get_indicators(
    symbol="USD_JPY",    # 通貨ペア
    interval="1hour",    # 時間足
    days=7               # 取得日数
)
```

**取得データ**:
```python
{
    "symbol": "USD_JPY",
    "trend": "up",           # トレンド: "up" or "down"
    "momentum": "neutral",   # モメンタム: "bullish" or "bearish" or "neutral"
    "latest_price": 157.922,
    "ma": {
        "ma20": 157.959,
        "ma50": 157.459,
        "ma20_above_ma50": True
    },
    "rsi": {
        "rsi": 50.86,
        "overbought": False,  # RSI ≥ 70
        "oversold": False     # RSI ≤ 30
    },
    "macd": {
        "macd": 0.1205,
        "macd_signal": 0.1764,
        "macd_histogram": -0.0472,
        "bullish_crossover": False,
        "bearish_crossover": False
    }
}
```

#### 1.2 ニュース分析取得

**関数**: `RuleEngine._fetch_recent_news()`

```python
news_list = self._fetch_recent_news(
    symbol="USD_JPY",
    lookback_hours=24    # 過去24時間
)
```

**Firestoreクエリ条件**:
- `collected_at >= (現在時刻 - lookback_hours)`
- `impact_usdjpy >= 3` (インパクト3以上)
- 最新10件まで
- 降順ソート

**取得データ**: `List[NewsEvent]`

#### 1.3 ニュースサマリー作成

**関数**: `RuleEngine._summarize_news()`

```python
news_summary = self._summarize_news(news_list, symbol)
```

**サマリー内容**:
```python
{
    "count": 5,                    # ニュース件数
    "avg_sentiment": 0.4,          # 平均センチメント (-2 〜 +2)
    "avg_impact": 3.8,             # 平均インパクト (1-5)
    "bullish_count": 3,            # 強気ニュース数 (sentiment > 0)
    "bearish_count": 1,            # 弱気ニュース数 (sentiment < 0)
    "neutral_count": 1,            # 中立ニュース数 (sentiment == 0)
    "signals": {                   # シグナル分布
        "BUY_CANDIDATE": 2,
        "SELL_CANDIDATE": 1,
        "IGNORE": 2
    }
}
```

---

## 統合判定ロジック

**関数**: `RuleEngine._integrate_signals()`

### スコアリングシステム

#### 買いスコア（buy_score）

| 条件 | スコア | 理由 |
|------|--------|------|
| テクニカル: `trend == "up"` AND `momentum == "bullish"` | +3pt | 上昇トレンド + 強気モメンタム |
| テクニカル: `trend == "up"` のみ | +1pt | 上昇トレンド |
| RSI: `rsi_oversold == True` (RSI ≤ 30) | +2pt | RSI売られすぎ（買いチャンス） |
| ニュース: `sentiment > 0.5` AND `impact >= 3` | +3pt | 強気センチメント + 高インパクト |
| ニュース: `sentiment > 0` | +1pt | 小幅ポジティブ |

**最大スコア**: 8点（テクニカル4点 + ニュース4点）

#### 売りスコア（sell_score）

| 条件 | スコア | 理由 |
|------|--------|------|
| テクニカル: `trend == "down"` AND `momentum == "bearish"` | +3pt | 下降トレンド + 弱気モメンタム |
| テクニカル: `trend == "down"` のみ | +1pt | 下降トレンド |
| RSI: `rsi_overbought == True` (RSI ≥ 70) | +2pt | RSI買われすぎ（売りチャンス） |
| ニュース: `sentiment < -0.5` AND `impact >= 3` | +3pt | 弱気センチメント + 高インパクト |
| ニュース: `sentiment < 0` | +1pt | 小幅ネガティブ |

**最大スコア**: 8点（テクニカル4点 + ニュース4点）

---

## 最終判定ルール

### シグナル判定

```python
# 買いシグナル
if buy_score >= 4 and sell_score <= 1:
    signal = "buy"
    confidence = min(0.3 + (buy_score * 0.15), 1.0)

# 売りシグナル
elif sell_score >= 4 and buy_score <= 1:
    signal = "sell"
    confidence = min(0.3 + (sell_score * 0.15), 1.0)

# 様子見（中立）
else:
    signal = "hold"
    confidence = 0.5
```

### 信頼度計算

**買い/売りシグナルの場合**:
```
confidence = 0.3 + (score × 0.15)
最大値: 1.0
```

**計算例**:
| スコア | 信頼度 | パーセント |
|--------|--------|-----------|
| 4点 | 0.3 + (4 × 0.15) = 0.90 | 90% |
| 5点 | 0.3 + (5 × 0.15) = 1.05 → 1.0 | 100% |
| 6点 | 0.3 + (6 × 0.15) = 1.20 → 1.0 | 100% |

**様子見の場合**:
```
confidence = 0.5 (固定)
```

---

## シグナル判定例

### 例1: 強い買いシグナル

**テクニカル指標**:
- trend: "up"
- momentum: "bullish"
- rsi: 35 (oversold: False)

**ニュース分析**:
- avg_sentiment: 0.8
- avg_impact: 4.5
- count: 5

**スコアリング**:
- テクニカル: 上昇トレンド + 強気モメンタム → +3pt
- ニュース: 強気センチメント (0.8 > 0.5) + 高インパクト (4.5 >= 3) → +3pt
- **buy_score = 6点**
- **sell_score = 0点**

**判定**:
- signal: "buy"
- confidence: 0.3 + (6 × 0.15) = 1.20 → **1.0 (100%)**
- reason: "テクニカル: 上昇トレンド + 強気モメンタム | ニュース強気 (sentiment: 0.8, impact: 4.5)"

### 例2: 様子見

**テクニカル指標**:
- trend: "up"
- momentum: "neutral"
- rsi: 50.86

**ニュース分析**:
- count: 0 (ニュースなし)

**スコアリング**:
- テクニカル: 上昇トレンドのみ → +1pt
- **buy_score = 1点**
- **sell_score = 0点**

**判定**:
- signal: "hold"
- confidence: **0.5 (50%)**
- reason: "買い要因 (1pt) vs 売り要因 (0pt) - 判断保留 | テクニカル: 上昇トレンド"

### 例3: 売りシグナル（RSI買われすぎ）

**テクニカル指標**:
- trend: "up"
- momentum: "neutral"
- rsi: 83.24 (overbought: True)

**ニュース分析**:
- avg_sentiment: 0.2
- avg_impact: 3.5
- count: 3

**スコアリング**:
- テクニカル: 上昇トレンドのみ → +1pt (buy_score)
- RSI: 買われすぎ → +2pt (sell_score)
- ニュース: 小幅ポジティブ (0.2 > 0) → +1pt (buy_score)
- **buy_score = 2点**
- **sell_score = 2点**

**判定**:
- signal: "hold"
- confidence: **0.5 (50%)**
- reason: "買い要因 (2pt) vs 売り要因 (2pt) - 判断保留 | テクニカル: 上昇トレンド | RSI買われすぎ (83.2)"

---

## 出力データ構造

**関数**: `RuleEngine.generate_signal()`

**戻り値**:
```python
{
    "symbol": "USD_JPY",
    "signal": "buy",                 # "buy" or "sell" or "hold"
    "confidence": 0.75,              # 0.0-1.0
    "timestamp": datetime(2026, 1, 12, 10, 50, 30),
    "technical": {                   # テクニカル指標（詳細）
        "trend": "up",
        "momentum": "bullish",
        "latest_price": 157.922,
        "ma": {...},
        "rsi": {...},
        "macd": {...}
    },
    "news_summary": {                # ニュースサマリー
        "count": 5,
        "avg_sentiment": 0.6,
        "avg_impact": 4.2,
        "bullish_count": 3,
        "bearish_count": 1,
        "neutral_count": 1,
        "signals": {...}
    },
    "reason": "テクニカル: 上昇トレンド + 強気モメンタム | ニュース強気 (sentiment: 0.6, impact: 4.2)",
    "rule_version": "v1.0"
}
```

---

## Firestore保存

**関数**: `RuleEngine.save_signal_to_firestore()`

### コレクション

**名前**: `signals`

### ドキュメントID形式

```
{timestamp}_{symbol}
例: 20260112_105030_USD_JPY
```

### ドキュメント構造

上記の出力データ構造と同じ（timestampはFirestore Timestamp型に自動変換）

---

## 実装関数一覧

### RuleEngine クラス

| 関数名 | 説明 | 戻り値 |
|--------|------|--------|
| `generate_signal(symbol, interval, days, lookback_hours)` | 単一通貨ペアのシグナル生成 | Dict |
| `generate_multiple_signals(symbols, interval, lookback_hours)` | 複数通貨ペアのシグナル生成 | Dict[str, Dict] |
| `save_signal_to_firestore(signal)` | シグナルをFirestoreに保存 | str (doc_id) |
| `_fetch_recent_news(symbol, lookback_hours)` | Firestoreからニュース取得 | List[NewsEvent] |
| `_summarize_news(news_list, symbol)` | ニュースサマリー作成 | Dict |
| `_integrate_signals(technical, news_summary, symbol)` | 統合判定ロジック | tuple[signal, confidence, reason] |
| `_convert_to_native_types(data)` | numpy型をPython native型に変換 | Any |

---

## パラメータ調整ガイド

### スコアリングの重み調整

現在の設定:
```python
# テクニカル最大4点
trend + momentum: 3点
trend のみ: 1点
RSI 異常値: 2点

# ニュース最大4点
強気/弱気 + 高インパクト: 3点
小幅ポジティブ/ネガティブ: 1点
```

**調整例**:
- テクニカル重視 → テクニカルの配点を増やす
- ニュース重視 → ニュースの配点を増やす

### 信頼度計算の調整

現在の設定:
```python
confidence = 0.3 + (score × 0.15)
```

**調整例**:
- より慎重に → ベース値を下げる（0.3 → 0.2）
- より積極的に → 係数を上げる（0.15 → 0.20）

### シグナル閾値の調整

現在の設定:
```python
buy_score >= 4 and sell_score <= 1  # 買い
sell_score >= 4 and buy_score <= 1  # 売り
```

**調整例**:
- より厳格に → 閾値を上げる（4 → 5）
- より緩く → 閾値を下げる（4 → 3）

---

## 注意事項

### Firestore複合インデックス

ニュース取得クエリには複合インデックスが必要です:

**必要なインデックス**:
1. `news` コレクション
   - `collected_at` (Ascending)
   - `impact_usdjpy` (Ascending)

2. `news` コレクション
   - `collected_at` (Ascending)
   - `impact_eurjpy` (Ascending)

**作成方法**:
1. GCP Firestore コンソールにアクセス
2. インデックスタブを開く
3. 複合インデックスを作成

現在の実装では、インデックスがない場合は空リスト（ニュースなし）として処理されます。

### numpy型の変換

テクニカル指標の計算結果（pandas）はnumpy型です。Firestoreに保存する前に、`_convert_to_native_types()`で自動的にPython native型に変換されます:

- `numpy.bool_` → `bool`
- `numpy.integer` → `int`
- `numpy.floating` → `float`

---

## v2.0 仕様（2026-02-14 決定）

### 目的

**AIファンダメンタルズ分析がロット調整に意味を持つかを検証する。**

- テクニカル判断・注文条件は固定し、AIはロットのみを決める
- 1ヶ月の実運用で方向性を評価する

### アーキテクチャ変更

```
【v1.0（旧）】
  ニュース分析 + テクニカル → 統合スコア → buy/sell/hold + confidence → 固定ロットで注文

【v2.0（新）】
  テクニカル → buy/sell/hold（方向決定、固定ロジック）
  AI（ニュース分析）→ ロット決定（0/500/1000/1500通貨）
  テクニカル方向 + AIロット → IFDOCO注文
```

---

### 取引パラメータ

| パラメータ | 値 | 備考 |
|-----------|------|------|
| 通貨ペア | USD/JPY のみ | |
| 口座資金 | 100,000円 | |
| SL | 40 pips（固定） | |
| TP | 40 pips（固定） | |
| 注文方式 | IFDOCO のみ | エントリー + SL + TP 一括発注 |
| 1次注文タイプ | LIMIT（指値） | 現在価格 +1pip バッファで即約定を狙う |
| 同一通貨ペア最大ポジション | 1 | |
| 全体最大ポジション | 1 | USD/JPYのみのため |
| テクニカル判定頻度 | 1日最大2回 | 間隔6時間以上 |
| AI分析頻度 | 1日1回 | ニュース収集と同時 |
| 評価期間 | 1ヶ月 | |

### SL/TP計算ロジック

```
pip_value（USD/JPY）= 0.01
entry_buffer = 1pip = 0.01

BUY:
  entry_price = current_price + 0.01（+1pip バッファ）
  SL = entry_price - (40 × 0.01) = entry_price - 0.40
  TP = entry_price + (40 × 0.01) = entry_price + 0.40

SELL:
  entry_price = current_price - 0.01（-1pip バッファ）
  SL = entry_price + (40 × 0.01) = entry_price + 0.40
  TP = entry_price - (40 × 0.01) = entry_price - 0.40
```

---

### AIロット決定ロジック

AIは**ファンダメンタルズ（ニュース分析結果）とテクニカル方向の一致度**でロットを決定する。

#### ロットマッピング

**テクニカル = BUY の場合:**

| ニュース条件 | ロット | 理由 |
|-------------|--------|------|
| sentiment > 0.5 AND impact >= 3 | 1500 | ファンダが買いを強く支持 |
| sentiment > 0 | 1000 | ファンダがやや買い支持 |
| sentiment == 0 or ニュースなし (count=0) | 500 | ファンダ中立、最小ロット |
| sentiment < 0 | 0 | ファンダが買いに反対 → 見送り |

**テクニカル = SELL の場合:**

| ニュース条件 | ロット | 理由 |
|-------------|--------|------|
| sentiment < -0.5 AND impact >= 3 | 1500 | ファンダが売りを強く支持 |
| sentiment < 0 | 1000 | ファンダがやや売り支持 |
| sentiment == 0 or ニュースなし (count=0) | 500 | ファンダ中立、最小ロット |
| sentiment > 0 | 0 | ファンダが売りに反対 → 見送り |

**テクニカル = HOLD の場合:**

ロット = 0（取引しない）

#### 入力データ

既存の `RuleEngine._summarize_news()` の出力をそのまま使用:

- `avg_sentiment`: -2 〜 +2
- `avg_impact`: 1 〜 5
- `count`: ニュース件数

#### GMOコイン注文単位

- GMOコイン FX APIの `size` パラメータ: **1 = 1通貨**
- 最小注文単位: 100通貨
- 選択可能ロット: 0 / 500 / 1000 / 1500（通貨）

---

### リスク管理パラメータ

| パラメータ | v2.0 値 | v1.0 値（旧） | 変更内容 |
|-----------|---------|-------------|---------|
| stop_loss_pips | 40.0 | 50.0 | 変更 |
| take_profit_pips | 40.0 | 100.0 | 変更 |
| max_monthly_loss | 5,000円 | なし | **新規** |
| max_loss_per_trade | 700円（設計目標） | なし | **新規** |
| max_daily_trades | 2 | 10 | 変更 |
| min_trade_interval_hours | 6 | なし | **新規** |
| max_positions_per_symbol | 1 | 3 | 変更 |
| max_total_positions | 1 | 5 | 変更 |
| max_consecutive_losses | 7 | 3 | 変更（想定連敗に合わせる） |
| min_margin_ratio | 100% | 100% | 変更なし |
| max_daily_loss | 削除 | 50,000円 | 月間上限に統合 |
| max_position_hours | 削除 | 24 | IFDOCO で SL/TP に委ねる |

#### 損失計算の検証

```
最大ロット 1500通貨 × SL 40pips × pip_value 0.01円
= 1500 × 0.40 = 600円 ≤ 700円（設計目標内）
```

#### 月間最大損失ガード

```
月初からの累計損失 >= 5,000円 → 新規取引を停止
算出方法: Firestore trades コレクションから当月の決済済み取引を集計
```

---

### 信頼度（confidence）の扱い

| 項目 | v2.0 | v1.0（旧） |
|------|------|-----------|
| 算出 | 維持（変更なし） | `0.3 + (score × 0.15)` |
| min_confidence フィルタ | **削除** | 0.7（機能していなかった） |
| 用途 | ログ・分析用のみ | 取引フィルタ |

**理由**: ロット=0 が「取引しない」の役割を担うため、confidence によるフィルタは不要。
ただし confidence はログに残し、後から「テクニカルスコアとAIロットの相関」を分析可能にする。

---

### 取引実行フロー（v2.0）

```
1. ニュース分析（1日1回）
   → avg_sentiment, avg_impact を算出
   → Firestore に保存（daily_ai_decision として）

2. テクニカル判定（1日最大2回、間隔6時間以上）
   → RuleEngine.generate_signal() → buy/sell/hold + confidence

3. hold の場合 → 終了

4. buy/sell の場合:
   a. AIロット決定
      → sentiment + impact + テクニカル方向 → 0/500/1000/1500
   b. ロット = 0 の場合 → 終了（ログに「AI見送り」として記録）

5. リスクチェック（RiskManager）
   - 月間損失上限チェック（5,000円）
   - ポジション上限チェック（1ポジション）
   - 連続損失チェック（7回）
   - 証拠金率チェック（100%）
   - 前回取引から6時間以上経過しているか

6. IFDOCO注文発注（GMOCoinClient.place_ifdoco_order()）
   - entry: 現在価格 ±1pip（LIMIT）
   - SL: entry ±40pips
   - TP: entry ±40pips

7. 結果をFirestoreに保存（研究ログ含む）
```

---

### Baseline比較仕様

実運用は AIロットのみで行い、比較用に仮想baselineをログ上で算出する。

| 項目 | AI運用（実取引） | Baseline（仮想） |
|------|----------------|-----------------|
| ロット | AI決定（0/500/1000/1500） | 1000通貨固定 |
| 方向 | テクニカル（共通） | テクニカル（共通） |
| SL/TP | 40/40 pips（共通） | 40/40 pips（共通） |
| 実取引 | あり | **なし（ログのみ）** |

**算出方法**:
```
baseline_pnl = (exit_price - entry_price) × 1000 × direction
  direction: BUY = +1, SELL = -1
```

**注意**: AI ロット=0 で見送った場合でも、テクニカルが buy/sell を出していれば
baseline_pnl は算出する（「AIが見送った取引がどうなったか」を記録するため）。

---

### 研究ログ仕様

各トレード（決済時）に以下を保存する:

```python
{
    # 既存フィールド
    "trade_id": str,
    "symbol": "USD_JPY",
    "side": "BUY" | "SELL",
    "entry_price": float,          # 約定価格
    "exit_price": float,           # 決済価格
    "status": "WIN" | "LOSS",
    "timestamp": datetime,

    # v2.0 追加フィールド
    "used_lot": int,               # 0/500/1000/1500
    "actual_pnl": float,           # 実損益（円）
    "baseline_pnl": float,         # 1000通貨換算の仮想損益（円）
    "ai_decision": {
        "avg_sentiment": float,    # AIが参照したsentiment
        "avg_impact": float,       # AIが参照したimpact
        "news_count": int,         # ニュース件数
        "lot_reason": str,         # ロット決定理由
    },
    "technical_score": {
        "buy_score": int,
        "sell_score": int,
        "confidence": float,       # ログ用に保持
    },
}
```

#### AI見送りログ（ロット=0の場合）

テクニカルが buy/sell を出したがAIがロット=0とした場合も記録する:

```python
{
    "trade_id": str,               # "skipped_" prefix
    "symbol": "USD_JPY",
    "side": "BUY" | "SELL",
    "used_lot": 0,
    "skip_reason": "AI_FUNDAMENTAL_OPPOSE",
    "ai_decision": {...},
    "technical_score": {...},
    "baseline_pnl": None,          # 決済されるまで不明、後から埋める
}
```

---

### 1ヶ月後の判断指標

| 指標 | 算出方法 | 判断基準 |
|------|---------|---------|
| 口座損益 | 月末残高 - 100,000円 | プラスなら継続検討 |
| 最大ドローダウン | 期間中の口座最大下落幅 | 5,000円以内なら許容 |
| AI運用 vs Baseline | Σ actual_pnl vs Σ baseline_pnl | AI > Baseline ならAIに価値あり |
| ロット別勝率 | 各ロット（500/1000/1500）ごとの勝率 | ロットが大きいほど勝率が高ければAIが有効 |
| AI見送り精度 | lot=0 で見送った取引のbaseline結果 | 見送り取引がLOSSならAIが正しい |

---

### 損失シミュレーション（v2.0）

```
【1取引の最大損失】
最大ロット 1500通貨 × 40pips × 0.01 = 600円

【1日の最大損失】
2取引 × 600円 = 1,200円

【想定連敗7回の損失（最大ロット固定の最悪ケース）】
7 × 600円 = 4,200円（月間上限5,000円以内）

【月間上限到達パターン】
5,000円 ÷ 600円 ≒ 8.3回 → 9回目の損切りで月間取引停止
```

---

## 残存する懸念点

> v2.0 仕様で対処済み / 未対処の分類

### 対処済み

| 懸念 | v2.0 での対処 |
|------|-------------|
| ポジションサイズ過大 | AIロット最大1500通貨に制限 |
| 1取引最大損失の未チェック | 最大600円（設計上保証） |
| 同時ポジション過多 | 1ポジション制約 |
| min_confidence の無意味なフィルタ | 廃止、ロット=0に役割移管 |
| システム障害時のSL/TP未執行 | IFDOCO注文で証券会社側が管理 |

### 未対処（許容 or 将来対応）

| 懸念 | 状態 | 備考 |
|------|------|------|
| スプレッドコスト | 許容 | 1日最大2取引 × 1500通貨 × 0.5銭 ≒ 1.5円/日。月45円程度で無視可能 |
| 週末ギャップ | 許容 | IFDOCO のSLが効くが、ギャップでSL超過の可能性は残る。ロットが小さいため影響限定的 |
| 1時間足のみの分析 | 将来 | 初回1ヶ月は現行のまま。結果を見て改善 |
| ニュース精度・遅延 | 検証対象 | AIロットの効果を測ること自体が目的 |
| バックテスト未実施 | 許容 | 実運用を小ロットで検証する方針 |

---

## バージョン履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| v1.0 | 2026-01-12 | 初版リリース |
| v2.0 | 2026-02-14 | AIロット決定・IFDOCO・研究ログ仕様を追加。リスク管理を全面改訂 |

---

**関連ドキュメント**:
- [要件定義書](requirements.md)
- [Firestore設計書](FIRESTORE_DESIGN.md)
- [進捗レポート](../progress/2026-01-12_rule_engine_implementation.md)
- [テクニカル指標実装](../progress/2026-01-12_technical_indicators_implementation.md)
- [GMOコインクライアント実装](../progress/2026-01-12_gmo_client_implementation.md)
