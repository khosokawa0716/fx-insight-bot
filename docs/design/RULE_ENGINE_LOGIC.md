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

## バージョン履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| v1.0 | 2026-01-12 | 初版リリース |

---

**関連ドキュメント**:
- [進捗レポート](../progress/2026-01-12_rule_engine_implementation.md)
- [テクニカル指標実装](../progress/2026-01-12_technical_indicators_implementation.md)
- [GMOコインクライアント実装](../progress/2026-01-12_gmo_client_implementation.md)
