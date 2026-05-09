#!/bin/bash
set -e

echo "=== Frontend Deploy ==="

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

# ビルド & Firebase Hosting へデプロイ
cd frontend
npm run build
firebase deploy --only hosting

echo "=== Frontend Deploy Complete ==="
