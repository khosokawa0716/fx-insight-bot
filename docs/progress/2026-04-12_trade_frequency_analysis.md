# 2026-04-12 現状仕様整理・取引頻度の改善検討

## 背景

正常運用開始から約1ヶ月が経過。Cloud費用も300円/月と健全。
ただし取引実績が月1回程度と少なく、機会を増やしたい。

本ドキュメントでは現状の仕様を噛み砕いて整理し、なぜ取引が少ないのか、
どう改善できるかを検討する。

---

## 現在の仕組みを噛み砕いて説明

### 全体の流れ

```
平日 9:00 / 21:00 JST（1日2回）
     ↓
1. テクニカル指標を計算（過去7日分の1時間足）
     ↓
2. ニュース感情を取得（過去24時間、インパクト3以上）
     ↓
3. スコアで buy / sell / hold を判定
     ↓
4. buy or sell の場合: AIがロット数を決定（0 or 500 or 1000 or 1500通貨）
     ↓
5. ロット=0 なら見送り
     ↓
6. リスクチェック（月間損失・ポジション数・取引間隔）
     ↓
7. IFDOCO注文を発注（エントリー + 損切り40pips + 利確40pips）
```

### テクニカル指標とは

3つの指標を使っている。

| 指標 | 意味 | 使い方 |
|------|------|--------|
| **MA（移動平均）** | 過去20本・50本の終値の平均 | MA20 > MA50 なら「上昇トレンド」 |
| **RSI** | 14本分の上昇幅vs下落幅の比率（0〜100） | 30以下→売られすぎ、70以上→買われすぎ |
| **MACD** | 短期EMA（12本）− 長期EMA（26本） | ヒストグラムがマイナス→プラスに転換したら「ゴールデンクロス」 |

### トレンドとモメンタムの判定

ここが重要なポイント。

**トレンド（上か下か）**
```
MA20 > MA50 → "up"（上昇トレンド）
MA20 < MA50 → "down"（下降トレンド）
```

**モメンタム（勢いがあるか）**
```
MACDがゴールデンクロス（ヒストグラムがマイナス→プラス）
  → "bullish"（強気モメンタム）

MACDがデッドクロス（ヒストグラムがプラス→マイナス）
  → "bearish"（弱気モメンタム）

それ以外
  → "neutral"（中立）
```

**ポイント**: モメンタムが "bullish" になるのは「MACDが今ちょうどクロスした瞬間」だけ。
1時間足で数日に1回しか起きない比較的稀なイベント。

---

## スコアリングの詳細

### 買いスコア（buy_score）

| 条件 | 点数 |
|------|------|
| トレンド上昇 かつ モメンタム強気 | **+3点** |
| トレンド上昇 のみ（モメンタム中立） | **+1点** |
| RSI ≤ 30（売られすぎ） | **+2点** |
| ニュース感情 > 0.5 かつ インパクト ≥ 3 | **+3点** |
| ニュース感情 > 0（小幅ポジティブ） | **+1点** |

### 売りスコア（sell_score）

| 条件 | 点数 |
|------|------|
| トレンド下降 かつ モメンタム弱気 | **+3点** |
| トレンド下降 のみ（モメンタム中立） | **+1点** |
| RSI ≥ 70（買われすぎ） | **+2点** |
| ニュース感情 < -0.5 かつ インパクト ≥ 3 | **+3点** |
| ニュース感情 < 0（小幅ネガティブ） | **+1点** |

### 最終判定ルール

```
buy_score ≥ 4 かつ sell_score ≤ 1  →  BUY シグナル
sell_score ≥ 4 かつ buy_score ≤ 1  →  SELL シグナル
それ以外                             →  HOLD（様子見）
```

---

## なぜ取引が月1回程度しか起きないのか

### ボトルネックを整理すると…

取引が成立するには以下の複数の条件を**同時に**満たす必要がある。

#### ボトルネック① MACDクロスが実行タイミングと重なる確率が低い

BUYシグナルへの最短ルートは:
```
トレンド上昇(up) + モメンタム強気(bullish) = 3点
+ ニュース小幅ポジティブ = 1点
────────────────────────
合計 4点 → BUY シグナル 🎉
```

しかし「モメンタム強気」は **MACDがちょうどゴールデンクロスしたとき** だけ成立する。
1時間足だと数日に1回程度のイベントで、かつそれが **9:00か21:00に実行される瞬間** と重なる必要がある。

#### ボトルネック② モメンタムなしでは4点に届きにくい

モメンタムが "neutral"（ほとんどの時間帯はこれ）の場合:
```
トレンド上昇(up) のみ = 1点
RSI売られすぎ(≤30)   = 2点   ← RSIが30以下は滅多にない
ニュース小幅ポジティブ = 1点
────────────────────────
合計 4点 → BUY シグナル（RSI≤30 必須）
```

USD/JPYでRSIが30以下になるのも比較的稀なため、このルートも滅多に発動しない。

#### ボトルネック③ 相反するシグナルでHOLDになる

例えば「トレンド上昇＋RSI買われすぎ」の状態:
```
buy_score = 1（トレンド上昇のみ）
sell_score = 2（RSI買われすぎ）
→ どちらも閾値未達 → HOLD
```

上昇トレンド中でもRSIが高くなると売りシグナルも積まれるため、打ち消し合ってHOLDになる。

#### ボトルネック④ AIロット判定がさらに絞る

BUYシグナルが出ても、ニュース感情がマイナスだとAIがロット=0にして見送る。
（この設計はテクニカルとファンダメンタルズの一致を求めるもの）

#### ボトルネック⑤ 同時実行できるポジションは1つのみ

ポジションを持っている間は次の取引ができない。
SL/TP 40pips設定のため、ポジション保有期間が長くなることも。

### まとめ: HOLD率が高い構造的理由

| ボトルネック | 発生頻度の目安 |
|------------|-------------|
| MACDクロスが実行時刻に重なる | 月5〜10回程度（実行120回中） |
| かつニュース感情がプラス | さらに絞られる |
| かつ対向シグナル（RSI等）が弱い | さらに絞られる |
| **総合的に取引成立** | **月1〜3回程度** |

---

## 改善オプション（選択肢の整理）

### オプション A: BUYスコアの閾値を下げる（4点 → 3点）

**変更箇所**: [rule_engine.py:329](../../backend/src/services/rule_engine.py#L329)

```python
# 現在
if buy_score >= 4 and sell_score <= 1:

# 変更後
if buy_score >= 3 and sell_score <= 1:
```

**効果**: 「トレンド上昇(3点) のみ」でシグナルが出るようになる。
**懸念**: ニュースやMACDの裏付けなし で取引するケースが増える。ノイズが多くなる可能性。

---

### オプション B: トレンドのみの点数を上げる（1点 → 2点）

**変更箇所**: [rule_engine.py:281-282](../../backend/src/services/rule_engine.py#L281)

```python
# 現在: トレンド上昇のみで +1点
elif tech_trend == "up":
    buy_score += 1

# 変更後: トレンド上昇のみで +2点
elif tech_trend == "up":
    buy_score += 2
```

**効果**: 「トレンド上昇(2点) + ニュース小幅ポジティブ(1点) + 何か1点」で届くようになる。
モメンタムの瞬間的クロスに依存しなくなる。
**懸念**: 依然として閾値4点なら3点+何かが必要。でも現実的。

---

### オプション C: モメンタム判定を「クロス瞬間」だけでなく「MACD方向」も考慮する

**変更箇所**: [technical_analyzer.py:271-295](../../backend/src/services/technical_analyzer.py#L271)

```python
# 現在: クロスオーバーの瞬間だけ "bullish"
if macd_data["bullish_crossover"] or (...):
    return "bullish"

# 変更後: ヒストグラムがプラス圏で上昇中なら "bullish"
if macd_data["bullish_crossover"] or macd_data["macd_histogram"] > 0:
    return "bullish"
```

**効果**: クロス後もしばらく "bullish" が継続するようになる。
実行タイミングとクロスタイミングのずれ問題が解消される。
**懸念**: "bullish" の持続期間が長くなるため、+3点が取りやすくなりすぎる可能性。

---

### オプション D: 対向スコアの許容範囲を広げる（sell_score ≤ 1 → ≤ 2）

**変更箇所**: [rule_engine.py:329](../../backend/src/services/rule_engine.py#L329)

```python
# 現在: 売りシグナルが1点以下でないとBUYにならない
if buy_score >= 4 and sell_score <= 1:

# 変更後: 売りシグナルが2点以下まで許容
if buy_score >= 4 and sell_score <= 2:
```

**効果**: 「トレンド上昇中にRSIが買われすぎ気味」でも買いシグナルが出るようになる。
**懸念**: RSI高いのに買い注文という、やや逆張り的な状況を許容することになる。

---

### オプション E: ニュースなし時も最小ロットで取引する（現状維持）

現在、ニュースがない場合はセンチメント=0.0扱いで、
AIのロット判定では「ファンダ中立 → 500通貨」になる。
これは既に実装済み。

---

## 推奨する改善案

**段階的に試すとよさそうな組み合わせ**:

### Step 1: まず C（モメンタム判定の改善）を試す

現在の実装では「クロスの瞬間だけbullish」になっているが、
**クロス後もMACDヒストグラムがプラスの間は bullish を維持する**ほうが自然。
副作用が少なく、かつ最もボトルネックの根本原因に近い改善。

```python
# technical_analyzer.py _determine_momentum()
def _determine_momentum(self, rsi_data, macd_data):
    # 強気: クロスの瞬間 OR ヒストグラムがプラス（クロス後も継続）
    if macd_data["bullish_crossover"] or macd_data["macd_histogram"] > 0:
        return "bullish"
    if macd_data["bearish_crossover"] or macd_data["macd_histogram"] < 0:
        return "bearish"
    return "neutral"
```

> 注意: RSI条件（`rsi_oversold and macd_histogram > 0`）も既存でカバーされていたが、
> 単純に `macd_histogram > 0` にすることで条件がシンプルになる。

### Step 2: 効果を見ながら A（閾値 4→3）または B（トレンド点数 1→2）を検討

Step 1 だけで取引回数が月3〜5回程度に増えるかを観察。
まだ少ない場合は B（トレンドのみ2点）を追加する。
A（閾値下げ）はシグナル品質に最も影響するので最後の手段として。

---

## 現状パラメータ一覧（変更前の基準値）

| パラメータ | 現在値 | 場所 |
|-----------|--------|------|
| 実行スケジュール | 平日 9:00 / 21:00 JST | Cloud Scheduler |
| テクニカル時間足 | 1時間足 | rule_engine.py `interval="1hour"` |
| テクニカル取得日数 | 7日分 | rule_engine.py `days=7` |
| ニュース取得時間 | 過去24時間 | rule_engine.py `lookback_hours=24` |
| buy/sell スコア閾値 | **4点以上** | rule_engine.py L329 |
| 対向スコア上限 | **1点以下** | rule_engine.py L329 |
| トレンド+モメンタム点数 | **3点** | rule_engine.py L279 |
| トレンドのみ点数 | **1点** | rule_engine.py L282 |
| RSI異常値点数 | **2点** | rule_engine.py L286 |
| ニュース強気点数 | **3点** | rule_engine.py L293 |
| ニュース小幅点数 | **1点** | rule_engine.py L296 |
| ロット選択肢 | 0/500/1000/1500通貨 | trade_executor.py |
| SL/TP | 各40pips | risk_manager.py |
| 月間最大損失 | 5,000円 | risk_manager.py |
| 取引間隔（最小） | **6時間** | risk_manager.py |
| 1日最大取引数 | **2回** | risk_manager.py |
| 最大同時ポジション | **1つ** | trade_executor.py |

---

## 現在のデータフロー図（v2.0）

```
Cloud Scheduler（9:00/21:00 JST 平日）
  │
  ▼
POST /api/v1/trade/execute（Service B: exec専用）
  │
  ▼
TradeExecutor.execute_signal_for_symbol("USD_JPY")
  │
  ├─ RuleEngine.generate_signal()
  │    ├─ TechnicalAnalyzer.get_indicators()  ← GMO APIから1時間足取得
  │    │    ├─ MA20, MA50 → トレンド(up/down)
  │    │    ├─ RSI(14) → 売られすぎ/買われすぎ
  │    │    └─ MACD(12/26/9) → モメンタム(bullish/bearish/neutral)
  │    │
  │    ├─ _fetch_recent_news()  ← Firestoreからニュース取得
  │    │    └─ 過去24h・impact≥3・最新10件
  │    │
  │    └─ _integrate_signals()  ← スコアリング
  │         └─ buy/sell/hold + confidence
  │
  ├─ [hold → ログ保存して終了]
  │
  ├─ RuleEngine.determine_lot()  ← AIロット決定
  │    └─ sentiment×impact → 0/500/1000/1500通貨
  │
  ├─ [lot=0 → スキップログ保存して終了]
  │
  ├─ RiskManager.check_trade_allowed()
  │    ├─ 月間損失チェック（≥5,000円で停止）
  │    ├─ 日次取引回数チェック（≥2回で停止）
  │    ├─ 取引間隔チェック（前回から6時間未満で停止）
  │    └─ 証拠金率チェック（<100%で停止）
  │
  └─ GMOCoinClient.place_ifdoco_order()  ← 実際に発注
       └─ entry(LIMIT) + SL + TP を一括発注
```

---

---

## 実施した変更（2026-04-12）

### Step 1: モメンタム判定の改善

**変更ファイル**: [technical_analyzer.py:271](../../backend/src/services/technical_analyzer.py#L271)

| | 変更前 | 変更後 |
|---|---|---|
| bullish の条件 | MACDクロスの瞬間のみ | MACDヒストグラム > 0 の間ずっと |
| bearish の条件 | MACDクロスの瞬間のみ | MACDヒストグラム < 0 の間ずっと |
| neutral の条件 | 大半の時間（クロスでも極値でもない） | ヒストグラムがちょうど0のとき（ほぼなし） |

---

## デプロイ手順

今回の変更はバックエンド共通コードのため、Service A・B の**両方**をデプロイする。

```bash
export GCP_PROJECT_ID=fx-insight-bot-prod

# Service A（読み取り専用）
gcloud run deploy fx-insight-bot \
  --source backend/ \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --allow-unauthenticated \
  --set-secrets "GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --set-env-vars "ENVIRONMENT=production,FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_PROJECT_ID=fx-insight-bot-prod"

# Service B（取引実行専用）
gcloud run deploy fx-insight-bot-exec \
  --source backend/ \
  --region asia-northeast1 \
  --project fx-insight-bot-prod \
  --no-allow-unauthenticated \
  --set-secrets "GMO_API_KEY=gmo-api-key:latest,GMO_API_SECRET=gmo-api-secret:latest" \
  --set-env-vars "ENVIRONMENT=production,FIRESTORE_DATABASE_ID=fx-insight-bot-db,GCP_PROJECT_ID=fx-insight-bot-prod" \
  --memory 512Mi \
  --concurrency 1 \
  --max-instances 2 \
  --timeout 300
```

---

## 検証方法

### ① デプロイ直後の動作確認（dry-run）

デプロイ完了後、以下のコマンドで即時確認できる（実際の注文は出ない）。

```bash
curl -X POST "https://fx-insight-bot-exec-755346299346.asia-northeast1.run.app/api/v1/trade/execute" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
```

**確認ポイント**:

| 項目 | 変更前の典型例 | 変更後の期待値 |
|------|--------------|--------------|
| `action` | `"HOLD"` が大半 | `"BUY"` or `"SELL"` が増える |
| `reason` に含まれる文言 | `"上昇トレンド"` のみ | `"上昇トレンド + 強気モメンタム"` |
| `buy_score` / `sell_score` | 1〜2点が多い | 3〜4点になりやすい |

### ② 運用中の取引回数で確認（1〜2週間後）

Firestore の `trades` コレクションで以下を確認する。

| 確認項目 | 変更前 | 変更後の目安 |
|---------|--------|------------|
| HOLDログの `technical_score.buy_score` | 1〜2点が多い | 3点のケースが増える |
| 月間のBUY/SELL件数 | 月1回程度 | 月3〜5回程度を期待 |
| SKIPログの増加 | ― | 増えた場合はAIがロット=0と判定（想定内） |

> **注意**: SKIPが増えても問題ない。「テクニカルはBUYだがニュース感情がマイナス → lot=0」という
> AIの見送り判断が正しく機能していることを示す。取引回数だけでなく「どのステップで止まったか」も合わせて見ると良い。

### ③ 過剰取引になっていないかのチェック

月5回を大きく超えるようなら閾値が緩すぎる可能性がある。
その場合は **オプション D（対向スコア上限を1のまま維持）** の確認や、
必要に応じて閾値を `buy_score >= 4` のままにして様子を見る。

---

## 関連ファイル

- [rule_engine.py](../../backend/src/services/rule_engine.py) - スコアリング・ロット決定
- [technical_analyzer.py](../../backend/src/services/technical_analyzer.py) - テクニカル指標計算
- [risk_manager.py](../../backend/src/services/risk_manager.py) - リスクチェック
- [trade_executor.py](../../backend/src/services/trade_executor.py) - 取引実行フロー
- [RULE_ENGINE_LOGIC.md](../design/RULE_ENGINE_LOGIC.md) - 詳細仕様書（v2.0含む）
