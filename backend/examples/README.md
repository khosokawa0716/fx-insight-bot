# 動作確認用スクリプト

このディレクトリには、Gemini APIの動作確認用スクリプトが含まれています。

## 📋 スクリプト一覧

### 1. test_gemini_grounding.py

Gemini Grounding with Google Search機能のテストスクリプト

**目的:**
- Grounding機能が正常に動作するか確認
- 最新のFXニュースをリアルタイムで取得できるか検証
- JSON出力の精度を確認
- コスト試算

**テスト内容:**
1. 基本的なGrounding機能のテスト
2. FXニュース収集の実用ケーステスト
3. コスト試算

---

### 2. test_rss_gemini_analysis.py

RSS + Gemini 3 Flash分析機能のテストスクリプト

**目的:**
- 既存のRSS News Collectorとの連携確認
- Gemini 3 Flashによるニュース分析機能の検証
- JSON出力の安定性確認
- センチメント分析の精度評価

**テスト内容:**
1. RSSからニュース収集
2. Gemini 3 Flashで分析
3. 分析結果のサマリー表示
4. コスト試算

---

## 🚀 実行方法

### 事前準備

1. **GCPプロジェクトの設定**
   ```bash
   # GCPプロジェクトIDを設定
   export GCP_PROJECT_ID="your-project-id"
   ```

2. **サービスアカウントキーの取得**
   - GCP Console → IAM → サービスアカウント
   - サービスアカウントを作成（またはを使用）
   - 権限: Vertex AI User
   - JSONキーをダウンロード

3. **環境変数の設定**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

4. **必要なパッケージのインストール**
   ```bash
   cd backend
   source venv/bin/activate
   pip install google-genai google-cloud-aiplatform feedparser requests beautifulsoup4
   ```

5. **Vertex AI APIの有効化**
   - GCP Console → APIs & Services → Library
   - "Vertex AI API" を検索して有効化

---

### test_gemini_grounding.py の実行

```bash
cd backend
source venv/bin/activate

# 環境変数を設定
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# スクリプト実行
python examples/test_gemini_grounding.py
```

**実行例:**
```
============================================================
Gemini Grounding with Google Search - 動作確認
============================================================

✅ 環境変数チェック完了
   GCP_PROJECT_ID: fx-insight-bot-12345
   GOOGLE_APPLICATION_CREDENTIALS: /path/to/key.json

✅ Vertex AI initialized
   Project: fx-insight-bot-12345
   Location: asia-northeast1

============================================================
TEST 1: 基本的なGrounding機能
============================================================

📝 プロンプト: USD/JPYに影響する最新の経済ニュースを3件教えてください。

⏳ Gemini APIにリクエスト中...

✅ レスポンス受信成功

------------------------------------------------------------
AIの回答:
------------------------------------------------------------
[ニュース内容が表示されます]

...
```

---

### test_rss_gemini_analysis.py の実行

```bash
cd backend
source venv/bin/activate

# 環境変数を設定
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# スクリプト実行
python examples/test_rss_gemini_analysis.py
```

**実行例:**
```
============================================================
RSS + Gemini 3 Flash分析 - 動作確認
============================================================

✅ 環境変数チェック完了
   GCP_PROJECT_ID: fx-insight-bot-12345
   GOOGLE_APPLICATION_CREDENTIALS: /path/to/key.json

============================================================
STEP 1: RSSからニュース収集
============================================================

✅ 収集完了: 49件のニュース

取得したニュース（最初の3件）:

1. [Yahoo Finance] Investors should beware of AI's circular...
   URL: https://finance.yahoo.com/news/...
   公開日: 2025-12-30 18:31:52+00:00

...
```

---

## 📊 期待される結果

### test_gemini_grounding.py

**成功時:**
- ✅ TEST 1: 基本的なGrounding機能 - success
- ✅ TEST 2: FXニュース収集 - success
- ✅ TEST 3: コスト試算 - info

**確認ポイント:**
- Grounding機能で最新ニュースが取得できているか
- JSON形式で正しく出力されているか
- ソースURLが付与されているか
- センチメント分析・影響度評価が妥当か

---

### test_rss_gemini_analysis.py

**成功時:**
- ✅ RSS収集: 40-50件程度
- ✅ Gemini分析: 5/5件成功

**確認ポイント:**
- RSSから正常にニュースが取得できているか
- Gemini分析が正常に完了しているか
- JSON出力のパースエラー率が低いか（0件が理想）
- センチメント・影響度の評価が妥当か

---

## ⚠️ トラブルシューティング

### エラー: 認証エラー

```
google.auth.exceptions.DefaultCredentialsError
```

**解決方法:**
1. GOOGLE_APPLICATION_CREDENTIALS環境変数が正しく設定されているか確認
2. サービスアカウントキーのパスが正しいか確認
3. サービスアカウントに"Vertex AI User"権限があるか確認

---

### エラー: Vertex AI APIが有効でない

```
google.api_core.exceptions.PermissionDenied: 403 Vertex AI API has not been used
```

**解決方法:**
1. GCP Console → APIs & Services → Library
2. "Vertex AI API" を検索
3. "有効にする"をクリック

---

### エラー: JSON Parse Error

```
⚠️ JSON パース失敗: Expecting value: line 1 column 1 (char 0)
```

**原因:**
- Geminiのレスポンスが期待通りのJSON形式でない

**対策:**
1. `response_mime_type: "application/json"` が設定されているか確認
2. プロンプトを調整（より明確なJSON出力指示）
3. temperatureを低く設定（0.1-0.2）

---

### エラー: RSS取得失敗

```
✅ 収集完了: 0件のニュース
```

**原因:**
- RSSフィードのURLが無効
- ネットワークエラー

**対策:**
1. `backend/src/services/news_collector.py` のRSS URLを確認
2. インターネット接続を確認
3. 別のRSSフィードURLを試す

---

## 📈 次のステップ

### 短期（今すぐ）

1. ✅ **両方のスクリプトを実行**
   - Grounding機能の動作確認
   - RSS + Gemini分析の動作確認

2. ✅ **結果を評価**
   - JSON出力の安定性
   - 分析精度
   - コスト

3. ⏳ **最終方式を決定**
   - RSS + Gemini分析で開始（推奨）
   - またはGrounding方式を採用

### 中期（1-2週間後）

1. ⏳ **本実装開始**
   - Gemini分析機能の実装
   - Firestoreへの保存機能
   - エラーハンドリング強化

2. ⏳ **Grounding機能の検証**（選択した場合）
   - 精度比較
   - コスト測定

---

## 📚 関連ドキュメント

- [GEMINI_GROUNDING_EVALUATION.md](../../docs/design/GEMINI_GROUNDING_EVALUATION.md) - Grounding機能の評価結果
- [COST_ESTIMATE.md](../../docs/design/COST_ESTIMATE.md) - コスト試算
- [AI_COMPARISON.md](../../docs/design/AI_COMPARISON.md) - AI選定の経緯
- [requirements.md](../../docs/design/requirements.md) - 要件定義

---

**作成日**: 2026-01-03
**最終更新**: 2026-01-03
