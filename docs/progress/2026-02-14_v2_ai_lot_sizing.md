# v2.0 AIロット決定機能 実装計画

**作成日**: 2026-02-14
**目的**: AIファンダメンタルズ分析がロット調整に意味を持つかを検証するための改修
**仕様書**: [RULE_ENGINE_LOGIC.md](../design/RULE_ENGINE_LOGIC.md) v2.0 セクション

---

## タスク一覧

### Task 1: GMO API size単位の確認・修正

**対象ファイル**: `backend/src/services/gmo_client.py`

- [ ] GMO FX APIの `size` パラメータが `1 = 1通貨` であることを確認
- [ ] docstring の「1 = 1万通貨」を「1 = 1通貨」に修正
- [ ] `place_ifdoco_order()` の `first_size`, `second_size` の型を確認（`int` のまま可）
- [ ] DRY-RUNモードのシミュレーション出力も単位を合わせる

**見積もり**: 小（docstring修正 + 動作確認）

---

### Task 2: RiskConfig の改修

**対象ファイル**: `backend/src/services/risk_manager.py`

- [ ] `RiskConfig` のパラメータ変更:
  ```python
  stop_loss_pips: float = 40.0       # 50 → 40
  take_profit_pips: float = 40.0     # 100 → 40
  max_monthly_loss: float = 5000.0   # 新規
  max_loss_per_trade: float = 700.0  # 新規
  max_daily_trades: int = 2          # 10 → 2
  min_trade_interval_hours: int = 6  # 新規
  max_consecutive_losses: int = 7    # 3 → 7
  ```
- [ ] `max_daily_loss` を削除（月間上限に統合）
- [ ] `max_position_hours` を削除（IFDOCOに委ねる）
- [ ] 月間損失チェックメソッド追加: `check_monthly_loss()`
  - Firestoreから当月の決済済み取引を集計
  - 累計損失 >= 5,000円 なら取引拒否
- [ ] 取引間隔チェックメソッド追加: `check_trade_interval()`
  - 前回取引から6時間以上経過しているか確認
- [ ] `min_confidence` チェックを削除

**見積もり**: 中（30〜50行の追加・変更）

---

### Task 3: TradeConfig の改修

**対象ファイル**: `backend/src/services/trade_executor.py`

- [ ] `TradeConfig` の変更:
  ```python
  symbols: List[str]                         # → ["USD_JPY"] 固定
  lot_options: List[int] = [0, 500, 1000, 1500]  # 新規
  max_positions_per_symbol: int = 1          # 3 → 1
  max_total_positions: int = 1               # 5 → 1
  execution_type = "IFDOCO"                  # MARKET → IFDOCO
  entry_buffer_pips: float = 1.0             # 新規（+1pipバッファ）
  ```
- [ ] `default_size` を削除（AIが決定するため）
- [ ] `min_confidence` を削除（ロット=0に役割移管）

**見積もり**: 小

---

### Task 4: AIロット決定ロジックの実装

**対象ファイル**: `backend/src/services/rule_engine.py`（または新規メソッド追加）

- [ ] `determine_lot()` メソッドを追加:
  ```python
  def determine_lot(
      self,
      signal: str,          # "buy" / "sell" / "hold"
      news_summary: Dict,   # avg_sentiment, avg_impact, count
  ) -> int:               # 0 / 500 / 1000 / 1500
  ```
- [ ] ロットマッピングロジック実装（仕様書通り）
- [ ] AIの決定理由（lot_reason）を文字列で返す
- [ ] 日次AIロット決定をFirestoreに保存: `daily_ai_decisions` コレクション

**見積もり**: 中（20〜30行）

---

### Task 5: 取引実行フローの改修

**対象ファイル**: `backend/src/services/trade_executor.py`

- [ ] `execute_signal()` の改修:
  1. テクニカル → buy/sell/hold
  2. hold → 終了
  3. AIロット決定 → 0 なら終了（スキップログ記録）
  4. リスクチェック（月間損失、ポジション数、取引間隔、連続損失、証拠金率）
  5. IFDOCO注文の価格計算:
     - BUY: entry = current + 0.01, SL = entry - 0.40, TP = entry + 0.40
     - SELL: entry = current - 0.01, SL = entry + 0.40, TP = entry - 0.40
  6. `place_ifdoco_order()` で発注
  7. 結果を研究ログ付きでFirestoreに保存
- [ ] `place_order()` の呼び出しを `place_ifdoco_order()` に変更
- [ ] スキップログ記録（ロット=0の場合）

**見積もり**: 大（既存フローの大幅改修）

---

### Task 6: 研究ログ・Baseline記録の実装

**対象ファイル**: `backend/src/services/trade_executor.py` + Firestoreモデル

- [ ] トレード記録に v2.0 フィールドを追加:
  - `used_lot`, `actual_pnl`, `baseline_pnl`
  - `ai_decision` (sentiment, impact, news_count, lot_reason)
  - `technical_score` (buy_score, sell_score, confidence)
- [ ] baseline_pnl の計算ロジック:
  ```python
  baseline_pnl = (exit_price - entry_price) × 1000 × direction
  ```
- [ ] AI見送りログの記録（`skipped_` prefix付きドキュメント）
- [ ] Firestoreモデル（`backend/src/models/firestore.py`）にフィールド追加

**見積もり**: 中（20〜30行）

---

### Task 7: FastAPIエンドポイントの調整

**対象ファイル**: `backend/src/main.py`

- [ ] 取引実行エンドポイントのパラメータ変更（symbols → USD/JPYのみ）
- [ ] AI見送りを含む取引結果のレスポンス形式更新
- [ ] 月間損益サマリーエンドポイント追加（研究用）

**見積もり**: 小

---

### Task 8: DRY-RUNテスト

- [ ] 新パラメータでの DRY-RUN テスト
- [ ] AIロット決定のテスト（各sentiment/impact条件でのロット確認）
- [ ] IFDOCO注文の価格計算テスト（+1pipバッファ含む）
- [ ] 月間損失チェックのテスト
- [ ] 取引間隔チェックのテスト
- [ ] Baseline計算のテスト

**見積もり**: 中

---

### Task 9: 実API接続テスト

- [ ] GMO コイン実APIで size=500, 1000, 1500 の IFDOCO注文が通るか確認
- [ ] 注文 → 約定 → 決済の一連フローを確認
- [ ] 研究ログが正しくFirestoreに保存されるか確認

**見積もり**: 小（手動テスト）

---

## 実装順序

```
Task 1 (API単位確認)
  ↓
Task 2 (RiskConfig) + Task 3 (TradeConfig)  ← 並行可
  ↓
Task 4 (AIロット決定)
  ↓
Task 5 (取引フロー改修)
  ↓
Task 6 (研究ログ)
  ↓
Task 7 (エンドポイント)
  ↓
Task 8 (DRY-RUNテスト)
  ↓
Task 9 (実API テスト)
```

---

## 影響範囲まとめ

| ファイル | 変更内容 | 規模 |
|---------|---------|------|
| `gmo_client.py` | docstring修正、size単位確認 | 小 |
| `risk_manager.py` | パラメータ変更、月間損失チェック追加 | 中 |
| `trade_executor.py` | フロー改修、IFDOCO化、AIロット統合 | 大 |
| `rule_engine.py` | `determine_lot()` 追加 | 中 |
| `models/firestore.py` | 研究ログフィールド追加 | 小 |
| `main.py` | エンドポイント調整 | 小 |
