#!/bin/bash
set -e

export GCP_REGION="asia-northeast1"

echo "=== Backend Deploy ==="

# main に切り替えて最新を取得
git checkout main
git pull origin main

# デプロイ対象コミットを表示して確認
echo ""
echo "デプロイされるコミット:"
git log --oneline -5
echo ""
read -p "このコミットをデプロイしますか？ (y/N): " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "デプロイを中止しました。マージを確認してから再実行してください。"
  exit 1
fi

cd backend

# Service A: 読み取り専用API（ダッシュボード向け / 公開）
echo "--- Deploying Service A: fx-insight-bot ---"
gcloud run deploy fx-insight-bot \
  --source=. \
  --region=${GCP_REGION}

# Service B: 取引実行専用API（Cloud Scheduler向け / 非公開）
echo "--- Deploying Service B: fx-insight-bot-exec ---"
gcloud run deploy fx-insight-bot-exec \
  --source=. \
  --region=${GCP_REGION}

echo "=== Backend Deploy Complete ==="
