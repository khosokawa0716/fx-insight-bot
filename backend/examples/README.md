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
   pip install google-genai
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

## 📊 期待される結果

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

## 📚 関連ドキュメント

- [2026-01-03_gemini_grounding_validation.md](../../docs/progress/2026-01-03_gemini_grounding_validation.md) - Grounding機能の検証結果
- [COST_ESTIMATE.md](../../docs/design/COST_ESTIMATE.md) - コスト試算
- [AI_COMPARISON.md](../../docs/design/AI_COMPARISON.md) - AI選定の経緯
- [requirements.md](../../docs/design/requirements.md) - 要件定義

---

**作成日**: 2026-01-03
**最終更新**: 2026-01-04
