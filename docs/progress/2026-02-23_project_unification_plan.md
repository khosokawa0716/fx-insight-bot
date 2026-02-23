# 2026-02-23 プロジェクト統一 & Auth 除去 計画

## 背景
- Firebase Hosting: `fx-insight-bot` (GCP: 737798608273)
- Cloud Run / Firestore / Scheduler: `fx-insight-bot-prod` (GCP: 755346299346)
- 2プロジェクトに分散していたことが判明 → 統一方針を決定

## 決定事項
1. **`fx-insight-bot-prod` に統一**（バックエンド側に Firebase Hosting を追加）
2. **Firebase Auth を除去**（読み取り専用ダッシュボードに認証不要）
3. **URL 変更を許容**（`fx-insight-bot-prod.web.app` になる）

## タスク

### Step 1: Firebase Hosting を `fx-insight-bot-prod` に追加【手動】
- Firebase コンソール → プロジェクトを追加 → 既存の GCP プロジェクト → `fx-insight-bot-prod` を選択

### Step 2: フロントエンドから Auth を削除【コード修正】
- `AuthContext.tsx` 削除
- `ProtectedRoute.tsx` 削除
- `LoginPage.tsx` 削除
- `App.tsx` のルーティング簡素化
- `firebase/auth` パッケージ削除
- `firebase.ts` を Hosting 用設定のみに整理

### Step 3: firebase.json を run リライトに変更【コード修正】
```json
{
  "source": "/api/**",
  "run": { "serviceId": "fx-insight-bot", "region": "asia-northeast1" }
}
```
- `.env.production` の `VITE_API_BASE_URL` も不要になる

### Step 4: .firebaserc を更新してデプロイ【コード修正 + デプロイ】
- `fx-insight-bot-prod` に変更してビルド & デプロイ

### Step 5: 旧プロジェクト削除【手動】
- `fx-insight-bot` プロジェクトを GCP コンソールから削除

## 再開時の注意
- Step 1 はブラウザ手動作業が必要（完了してからコード修正に入る）
- Cloud Run サービス名は `fx-insight-bot`（`firebase.json` の serviceId に使う）
