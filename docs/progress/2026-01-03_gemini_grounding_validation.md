# Gemini Grounding機能 動作確認完了レポート

**日付**: 2026-01-03
**フェーズ**: Phase 2 - ニュース収集機能
**ステータス**: ✅ 完了

---

## 概要

Gemini Grounding with Google Search機能の動作確認を完了し、FX関連ニュースの収集が正常に機能することを確認しました。

---

## 実施内容

### 1. 環境構築

- **Python バージョン**: 3.10
- **必要パッケージ**: `google-genai`
- **GCP プロジェクト**: `fx-insight-bot-prod`
- **リージョン**: `asia-northeast1`
- **認証方法**: サービスアカウントキー

### 2. テストスクリプト作成

作成したファイル:
- [backend/examples/test_gemini_grounding.py](../../backend/examples/test_gemini_grounding.py)
- [backend/examples/test_rss_gemini_analysis.py](../../backend/examples/test_rss_gemini_analysis.py)
- [backend/examples/README.md](../../backend/examples/README.md)

### 3. テスト実行結果

#### TEST 1: 基本的なGrounding機能
- **ステータス**: ✅ 成功
- **レスポンス**: 最新のUSD/JPY関連ニュース3件を取得
- **Grounding Metadata**: 18個のソースから情報を収集
- **所要時間**: 約30-60秒

#### TEST 2: FXニュース収集（JSON形式）
- **ステータス**: ✅ 成功
- **取得件数**: 5件
- **出力形式**: JSON配列
- **データ構造**:
  ```json
  {
    "title": "ニュースタイトル",
    "summary": "要約",
    "sentiment": -2〜2の整数,
    "impact_score": 1〜10の整数,
    "time_horizon": "short-term/medium-term/long-term",
    "source_url": "ソースURL"
  }
  ```

#### 取得されたニュースの例

1. **FRBの金利決定** (影響度: 8/10)
   - センチメント: Neutral (0)
   - 時間軸: short-term

2. **日銀の利上げと円安** (影響度: 9/10)
   - センチメント: Positive (1)
   - 時間軸: short-term

3. **円のショートポジション** (影響度: 8/10)
   - センチメント: Negative (-1)
   - 時間軸: short-term

4. **日銀の追加利上げ延期** (影響度: 8/10)
   - センチメント: Positive (1)
   - 時間軸: medium-term

5. **円の戦略的リバウンド予測** (影響度: 9/10)
   - センチメント: Negative (-1)
   - 時間軸: medium-term

---

## 技術的な知見

### 使用したSDK

従来の `vertexai.preview.generative_models` ではなく、新しい `google.genai` SDKを使用:

```python
from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)

client = genai.Client(
    vertexai=True,
    project=project_id,
    location=location,
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=GenerateContentConfig(
        tools=[Tool(google_search=GoogleSearch())],
    ),
)
```

### JSON出力の注意点

- `response_mime_type="application/json"` と Grounding を同時に使うと問題が発生
- **解決策**: プロンプトでJSON形式を明示的に指示し、レスポンスからマークダウンコードブロック (```) を削除

### パフォーマンス

- **API応答時間**: 約30-60秒 (Google検索実行のため)
- **トークン数** (推定):
  - 入力: 約2,000トークン
  - 出力: 約1,000トークン

---

## コスト試算

### 月間想定コスト

**想定条件**:
- 実行頻度: 2回/日
- 月間実行回数: 60回
- 1回あたりトークン: 入力2,000 + 出力1,000

**コスト計算**:
```
Gemini 3 Flash料金:
- 入力: 60回 × 2,000トークン × $0.50/1M = $0.06
- 出力: 60回 × 1,000トークン × $3.00/1M = $0.18
小計: $0.24

Grounding料金 (2026年1月5日〜):
- 1,500検索/日まで無料
- 60回/月 → 無料枠内
小計: $0

合計: $0.24 ≈ 約36円/月 (1ドル=150円換算)
```

**年間コスト**: 約432円

---

## 評価

### ✅ メリット

1. **最新ニュースの取得**: リアルタイムでGoogle検索から最新情報を収集
2. **構造化データ**: JSON形式で一貫したデータ構造
3. **高品質な分析**: センチメント、影響度、時間軸を含む詳細な分析
4. **ソース付き**: すべてのニュースにソースURLが付与
5. **低コスト**: 月額約37円と非常に低コスト

### ⚠️ 注意点

1. **応答時間**: 30-60秒かかる (Google検索実行のため)
2. **JSON出力の安定性**: マークダウンコードブロック除去処理が必要
3. **レート制限**: 詳細は要確認 (無料枠: 1,500検索/日)

---

## 次のステップ

### Phase 2 本実装

1. **プロンプトテンプレート作成**
   - センチメント分析基準の明確化
   - 影響度評価ロジックの標準化

2. **エラーハンドリング**
   - JSON パースエラーへの対応
   - API タイムアウトへの対応
   - リトライロジックの実装

3. **Firestore統合**
   - 収集したニュースの保存
   - 重複チェック機能

4. **定期実行**
   - Cloud Scheduler + Cloud Functions による自動実行
   - 1日2回の定期実行設定

### 検討事項

- 検索クエリの最適化 (より関連性の高いニュースを取得)
- レート制限への対応方針
- モニタリング・アラート設定

---

## 結論

Gemini Grounding機能は、FXニュース収集に非常に有効であることが確認できました。

**採用決定**: ✅ Grounding方式を本実装に採用

**主な理由**:
1. 最新ニュースをリアルタイムで取得可能
2. 高品質な構造化データが得られる
3. コストが非常に低い (月額約37円)
4. 予算の4%程度で96%の余裕あり

---

**作成者**: Claude Code
**レビュー**: -
**承認**: -
