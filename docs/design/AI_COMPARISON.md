# AI選定: Vertex AI vs OpenAI API

## 選定結果

**採用**: Vertex AI (Gemini 1.5 Flash)

## 比較表

| 項目 | OpenAI API (GPT-4o-mini) | Vertex AI (Gemini 1.5 Flash) |
|------|--------------------------|------------------------------|
| **コスト** | 入力: $0.15/1M<br>出力: $0.60/1M | 入力: $0.0375/1M<br>出力: $0.15/1M<br>**約1/4のコスト** |
| **認証** | API Key方式 | GCP IAM統合 |
| **エコシステム** | 外部サービス | GCP内で完結 |
| **課金管理** | 別途契約 | GCPで一元管理 |
| **リージョン** | 固定 | asia-northeast1選択可 |
| **セットアップ** | 簡単(API Key取得のみ) | GCP設定必要 |
| **モデル品質** | 高品質、実績豊富 | 高品質、日本語対応良好 |
| **コミュニティ** | 豊富 | 成長中 |
| **切り替え容易性** | - | **後からOpenAI APIに変更可能** |

---

## Vertex AI 採用のメリット

### 1. コスト削減(最重要)
```
月間想定処理:
- ニュース記事: 60件/月 (2回/日 × 30日)
- 1記事あたりトークン: 入力1,500 + 出力500

OpenAI API (GPT-4o-mini):
- 入力: 90,000トークン × $0.15/1M = $0.0135
- 出力: 30,000トークン × $0.60/1M = $0.018
- 月額: 約$0.03 (約4円)

Vertex AI (Gemini 1.5 Flash):
- 入力: 90,000トークン × $0.0375/1M = $0.0034
- 出力: 30,000トークン × $0.15/1M = $0.0045
- 月額: 約$0.008 (約1円)

→ 約75%のコスト削減
```

### 2. GCPエコシステム統合
- Firestoreと同じIAM認証
- Cloud Loggingで統一ログ管理
- Cloud Monitoringで一元監視
- サービスアカウントで権限管理

### 3. 運用の簡素化
- API Key管理不要(IAM認証)
- 課金が1つのGCPアカウントに集約
- リージョン選択でレイテンシ最適化

### 4. 日本語対応
- Gemini 1.5は日本語ニュース分析に強い
- 金融用語の理解度が高い

---

## Vertex AI 採用のデメリット

### ❌ 1. 初期セットアップの複雑さ

**OpenAI API**: API Key取得だけで即利用可能
```python
import openai
openai.api_key = "sk-..."
response = openai.ChatCompletion.create(...)
```

**Vertex AI**: GCP設定が必要
```python
# 1. Vertex AI API有効化
# 2. サービスアカウント作成
# 3. 権限設定
# 4. 認証情報設定
from google.cloud import aiplatform
aiplatform.init(project="your-project", location="asia-northeast1")
```

**対策**: Phase 0で設定手順を明確化

---

### ❌ 2. ドキュメント・コミュニティの少なさ

| 項目 | OpenAI API | Vertex AI |
|------|-----------|-----------|
| Stack Overflow質問数 | 多数 | 少ない |
| ブログ記事 | 豊富 | 限定的 |
| サンプルコード | 多数 | 増加中 |
| 日本語情報 | 多い | 少ない |

**影響**:
- トラブルシューティングに時間がかかる可能性
- プロンプト設計のベストプラクティスが少ない

**対策**:
- 公式ドキュメント中心に実装
- 初期段階で動作検証を徹底

---

### ❌ 3. モデル切り替えの手間

OpenAI APIは複数モデルへの切り替えが容易:
```python
# GPT-4o-mini
response = openai.ChatCompletion.create(model="gpt-4o-mini", ...)

# GPT-4に変更(コード変更不要)
response = openai.ChatCompletion.create(model="gpt-4", ...)
```

Vertex AIは別モデルへの切り替えに修正が必要:
```python
# Gemini 1.5 Flash
from vertexai.preview.generative_models import GenerativeModel
model = GenerativeModel("gemini-1.5-flash")

# Claude 3.5に変更する場合
from anthropic import AnthropicVertex
client = AnthropicVertex(region="asia-northeast1", project_id="...")
# ↑ コード修正が必要
```

**影響**: モデル変更時のコード修正が発生

**対策**:
- AIクライアントを抽象化してインターフェース統一
- 後からOpenAI APIに戻すことも可能

---

### ❌ 4. レート制限の違い

| 項目 | OpenAI API | Vertex AI |
|------|-----------|-----------|
| リクエスト/分 | 500 (Tier 1) | プロジェクト依存 |
| トークン/分 | 200,000 (Tier 1) | プロジェクト依存 |
| 引き上げ方法 | 使用量に応じて自動 | サポートリクエスト |

**影響**:
- 大量処理時に制限に引っかかる可能性
- 制限引き上げにサポート対応が必要

**対策**:
- 本システムは1日2回のバッチ処理のみなので影響小

---

### ❌ 5. JSON出力の安定性

**OpenAI API**: Function Calling機能で構造化出力が安定
```python
response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[...],
    functions=[{
        "name": "analyze_news",
        "parameters": {
            "type": "object",
            "properties": {
                "sentiment": {"type": "number"},
                "topic": {"type": "string"}
            }
        }
    }]
)
# → 確実にJSON形式で返却
```

**Vertex AI (Gemini)**: プロンプトで指示する方式
```python
model = GenerativeModel("gemini-1.5-flash")
response = model.generate_content(
    "以下のニュースを分析して、JSON形式で出力してください...",
    generation_config={"response_mime_type": "application/json"}
)
# → パース失敗のリスクあり
```

**影響**: JSON出力の検証・リトライ処理が必要

**対策**:
- Pydanticでバリデーション強化
- パース失敗時のリトライロジック実装

---

### ❌ 6. プロンプトの移植性

OpenAI APIで動作確認したプロンプトは、Vertex AIで再調整が必要になる可能性があります。

**例**:
```python
# OpenAI APIで最適化されたプロンプト
prompt = "Analyze the following news and return sentiment score from -2 to 2..."

# Geminiでは異なる結果になる可能性
# → プロンプトの再調整が必要
```

**影響**: 初期段階でのプロンプトチューニング工数

**対策**: MVP段階で十分なテストを実施

---

## 総合評価

### メリット合計: ⭐⭐⭐⭐☆ (4/5)
- コスト削減: 75%削減
- GCP統合: 運用が簡素化
- 切り替え可能: 後からOpenAI APIに変更可能

### デメリット合計: ⭐⭐☆☆☆ (2/5)
- セットアップ複雑
- ドキュメント少ない
- JSON出力の安定性に懸念

---

## 推奨実装方針

### 1. AIクライアントを抽象化

```python
# src/ai/base_client.py
from abc import ABC, abstractmethod

class AIClient(ABC):
    @abstractmethod
    def analyze_news(self, text: str) -> NewsAnalysis:
        pass

# src/ai/vertex_client.py
class VertexAIClient(AIClient):
    def analyze_news(self, text: str) -> NewsAnalysis:
        # Vertex AI実装
        pass

# src/ai/openai_client.py
class OpenAIClient(AIClient):
    def analyze_news(self, text: str) -> NewsAnalysis:
        # OpenAI実装
        pass

# 設定で切り替え可能
ai_client = VertexAIClient() if USE_VERTEX_AI else OpenAIClient()
```

### 2. 段階的な移行計画

| フェーズ | AI | 目的 |
|---------|-----|------|
| Phase 1 (MVP) | Vertex AI | 初期構築・コスト検証 |
| Phase 2 (検証) | Vertex AI | プロンプトチューニング |
| Phase 3 (判断) | 評価結果次第 | 必要に応じてOpenAI APIに切り替え |

### 3. 切り替え判断基準

以下の場合はOpenAI APIへの切り替えを検討:

- ❌ JSON出力の精度が80%を下回る
- ❌ センチメント分析の精度が不十分
- ❌ レート制限に頻繁に引っかかる
- ❌ GCPの月額コストが1,000円を超える

---

## 結論

**Vertex AIを採用する理由**:
1. ✅ コスト削減効果が大きい(75%削減)
2. ✅ GCP統合による運用簡素化
3. ✅ 後からOpenAI APIに変更可能
4. ✅ 立ち上げ時の簡素化を重視

**デメリットへの対策**:
- 抽象化レイヤーで切り替え可能に設計
- MVP段階で十分な検証を実施
- プロンプトとバリデーションを強化

---

**最終決定**: Vertex AI (Gemini 3 Flash) を採用

**次のアクション**:
- ✅ ドキュメント更新完了（2026-01-03）
- ✅ コスト試算の再計算完了（Gemini 3 Flash料金反映）
- ✅ Grounding機能評価完了
- ⏳ 実装時の設定手順を明確化
- ⏳ 動作確認用コードの作成

---

**更新情報 (2026-01-03)**:

### Gemini 3 Flash料金改定の影響

Gemini 1.5 Flash → Gemini 3 Flashへの移行により料金が大幅に改定されました:

- 入力トークン: $0.0375/1M → $0.50/1M（約13倍）
- 出力トークン: $0.15/1M → $3.00/1M（約20倍）

**新コスト試算**:
- Grounding使用: 約37円/月（旧: 約1.2円/月）

**評価**: 料金は大幅に上昇したが、予算1,000円/月の2-4%程度であり許容範囲内。
Grounding機能による最新ニュース取得という独自の価値があるため、採用を継続。

詳細は [GEMINI_GROUNDING_EVALUATION.md](GEMINI_GROUNDING_EVALUATION.md) を参照。

---

**ドキュメントバージョン**: v2.0
**作成日**: 2025-12-28
**最終更新**: 2026-01-03 (Gemini 3 Flash料金改定対応)
**次回レビュー**: Phase 2.1 完了時
