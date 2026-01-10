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

### 2. test_firestore_save.py

Firestore保存機能のテストスクリプト（モックデータ使用）

**目的:**
- NewsStorageサービスの動作確認
- Firestoreへのデータ保存・取得機能の検証
- 重複検出機能の確認
- データバリデーションの確認

**テスト内容:**
1. 正常なデータの保存（3件のモックニュース）
2. 重複検出テスト（同じデータを再度保存）
3. ニュース取得テスト（IDによる取得、最近のニュース取得）
4. 無効なデータ処理テスト（範囲外の値）

**特徴:**
- Gemini APIを呼び出さないため、**APIコストが発生しない**
- モックJSONデータを使用した高速テスト
- 実際のFirestoreに接続して動作を確認

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

---

### test_firestore_save.py の実行

```bash
cd backend
source venv/bin/activate

# 環境変数を設定（.envファイルがある場合は不要）
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# スクリプト実行
python examples/test_firestore_save.py
```

**test_gemini_grounding.py 実行例:**
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

**test_firestore_save.py 実行例:**
```
============================================================
Firestore Save Functionality Test
============================================================

このテストは実際のFirestoreに接続します。
GCPプロジェクトとサービスアカウントの設定を確認してください。

============================================================

============================================================
TEST 1: 正常なデータ保存
============================================================

📝 保存するニュース件数: 3
   1. 日銀が金利据え置き決定
   2. 米FOMC、利上げ継続を決定
   3. ECB、追加利下げを示唆

⏳ Firestoreに保存中...

✅ 保存完了
   Total:   3 items
   Saved:   3 items
   Skipped: 0 items (duplicates)
   Failed:  0 items

💾 保存されたニュースID:
   - news_20260110_a1b2c3d4e5f6
   - news_20260110_f6e5d4c3b2a1
   - news_20260110_123456789abc

============================================================
TEST 2: 重複検出テスト
============================================================

📝 同じニュースを再度保存（重複スキップモード）

⏳ Firestoreに保存中...

✅ 重複検出完了
   Total:   3 items
   Saved:   0 items (新規)
   Skipped: 3 items (重複)
   Failed:  0 items

✅ 重複検出が正常に動作しています

============================================================
TEST 3: ニュース取得テスト
============================================================

📝 ニュースIDで取得: news_20260110_a1b2c3d4e5f6

⏳ Firestoreから取得中...

✅ 取得成功
   Title:        日銀が金利据え置き決定
   Sentiment:    0
   Impact USD/JPY: 4
   Impact EUR/JPY: 2
   Time Horizon: short-term

📝 最近のニュースを取得 (limit=5)

⏳ Firestoreから取得中...

✅ 5 件取得
   1. ECB、追加利下げを示唆 (collected: 2026-01-10 12:00:00+00:00)
   2. 米FOMC、利上げ継続を決定 (collected: 2026-01-10 12:00:00+00:00)
   3. 日銀が金利据え置き決定 (collected: 2026-01-10 12:00:00+00:00)
   ...

============================================================
TEST 4: 無効なデータ処理テスト
============================================================

📝 TEST 4-1: 無効なセンチメント値（3）
   ✅ 期待通りエラー発生: ValidationError

📝 TEST 4-2: 無効なインパクト値（6）
   ✅ 期待通りエラー発生: ValidationError

============================================================
All Tests Completed
============================================================
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

### test_firestore_save.py

**成功時:**
- ✅ TEST 1: 正常なデータ保存 - 3件すべて保存成功
- ✅ TEST 2: 重複検出テスト - 3件すべて重複として検出
- ✅ TEST 3: ニュース取得テスト - IDで取得成功、最近のニュース取得成功
- ✅ TEST 4: 無効なデータ処理テスト - ValidationErrorが発生

**確認ポイント:**
- Firestoreへの保存が正常に完了しているか
- 重複検出が正しく動作しているか（skipped=3）
- 保存したニュースがIDで取得できるか
- 無効なデータに対して適切にエラーが発生するか
- ニュースIDのフォーマットが正しいか（`news_YYYYMMDD_[hash]`）

**注意:**
- TEST 1実行後、Firestoreに3件のテストデータが保存されます
- TEST 2で重複が検出されるのは、TEST 1で保存したデータと同一だからです
- 同じ日に複数回実行すると、既存のテストデータがある場合、TEST 1でskippedが増える可能性があります

---

## ⚠️ トラブルシューティング

### 共通エラー

#### エラー: 認証エラー

```
google.auth.exceptions.DefaultCredentialsError
```

**解決方法:**
1. GOOGLE_APPLICATION_CREDENTIALS環境変数が正しく設定されているか確認
2. サービスアカウントキーのパスが正しいか確認
3. サービスアカウントに"Vertex AI User"権限があるか確認

---

### test_gemini_grounding.py 固有エラー

#### エラー: Vertex AI APIが有効でない

```
google.api_core.exceptions.PermissionDenied: 403 Vertex AI API has not been used
```

**解決方法:**
1. GCP Console → APIs & Services → Library
2. "Vertex AI API" を検索
3. "有効にする"をクリック

#### エラー: JSON Parse Error

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

### test_firestore_save.py 固有エラー

#### エラー: Firestoreへの接続失敗

```
google.cloud.exceptions.NotFound: 404 Database not found
```

**解決方法:**
1. Firestore Databaseが作成されているか確認
   - GCP Console → Firestore → データベースを作成
2. `database_id` が正しいか確認（src/config.py）
3. サービスアカウントに"Cloud Datastore User"権限があるか確認

#### エラー: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'src'
```

**解決方法:**
1. `backend`ディレクトリから実行しているか確認
2. 仮想環境が有効になっているか確認（`source venv/bin/activate`）
3. 必要なパッケージがインストールされているか確認

#### TEST 4でエラーが発生しない

```
⚠️ 保存成功（バリデーションが機能していない可能性）
```

**原因:**
- Pydanticのバリデーションが期待通り動作していない可能性

**確認ポイント:**
1. NewsEventモデルのField定義を確認（ge=1, le=5など）
2. Pydanticのバージョンを確認（v2系を推奨）

## 📚 関連ドキュメント

- [2026-01-03_gemini_grounding_validation.md](../../docs/progress/2026-01-03_gemini_grounding_validation.md) - Grounding機能の検証結果
- [COST_ESTIMATE.md](../../docs/design/COST_ESTIMATE.md) - コスト試算
- [AI_COMPARISON.md](../../docs/design/AI_COMPARISON.md) - AI選定の経緯
- [requirements.md](../../docs/design/requirements.md) - 要件定義

---

**作成日**: 2026-01-03
**最終更新**: 2026-01-04
