# 2026-02-23 プロジェクト統一 & Auth 除去

## 背景
- Firebase Hosting: `fx-insight-bot` (GCP: 737798608273)
- Cloud Run / Firestore / Scheduler: `fx-insight-bot-prod` (GCP: 755346299346)
- 2プロジェクトに分散していたことが判明 → 統一方針を決定

## 決定事項
1. **`fx-insight-bot-prod` に統一**（バックエンド側に Firebase Hosting を追加）
2. **Firebase Auth を除去**（読み取り専用ダッシュボードに認証不要）
3. **URL 変更を許容**（`fx-insight-bot-prod.web.app` になる）

## 完了タスク ✅

### Step 1: Firebase Hosting を `fx-insight-bot-prod` に追加【手動】✅
### Step 2: フロントエンドから Auth を削除【コード修正】✅
- `AuthContext.tsx` / `ProtectedRoute.tsx` / `LoginPage.tsx` / `firebase.ts` 削除
- `App.tsx` のルーティング簡素化
- `firebase` パッケージ削除（バンドル -105KB）
### Step 3: firebase.json を run リライトに変更【コード修正】✅
### Step 4: .firebaserc を `fx-insight-bot-prod` に変更してデプロイ【完了】✅
- 新URL: https://fx-insight-bot-prod.web.app
### Step 5: 旧プロジェクト削除【手動】✅
- `fx-insight-bot` を GCP コンソールからシャットダウン（30日後に完全削除）

## コミット
`7533811 refactor: プロジェクト統一とFirebase Auth除去`

---

## 次回対応予定：エンドポイント認証（必ずやる）

### 背景
Firebase Auth 除去後、`/api/v1/trade/execute` を含む全エンドポイントに認証がない。
GMOコインのシークレットキーは Secret Manager 内にあり外部露出はないが、
**エンドポイントURLを知っている人物が POST するだけで実際の取引が実行される**リスクがある。

### 対策方針：カスタムヘッダーによるシークレット検証

Cloud Scheduler のリクエストに `X-Internal-Token` を追加し、バックエンドで検証する。

```
Cloud Scheduler → X-Internal-Token: <secret> → Cloud Run（検証） → GMOコイン
```

**実装内容**:
1. Secret Manager に `INTERNAL_API_TOKEN` を追加
2. FastAPI に `X-Internal-Token` ヘッダー検証ミドルウェアを追加
   - 対象: POST エンドポイント（`/execute`, `/news/collect`）
   - GET エンドポイント（`/account`, `/positions`, `/news`, `/signals`）は除外でもよい
3. Cloud Scheduler のジョブに `--headers X-Internal-Token=<secret>` を追加

**優先度**: 監視機能実装の次
