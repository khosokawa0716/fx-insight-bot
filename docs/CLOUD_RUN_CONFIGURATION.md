# Cloud Run サーバー設定ドキュメント

## 概要
FX Insight Bot のCloud Run サービス設定と最適化履歴を管理。

## 現在の設定 (2026-02-21更新)

### 基本情報
- **サービス名**: fx-insight-bot
- **リージョン**: asia-northeast1
- **URL**: https://fx-insight-bot-755346299346.asia-northeast1.run.app
- **最終更新**: 2026-02-21 21:30 JST

### スケーリング設定
```yaml
autoscaling:
  minInstances: 0          # コスト最適化のため0維持
  maxInstances: 2          # 2026-02-21: 5→2に削減
  concurrency: 1           # 2026-02-21: 80→1に変更
```

### リソース制限
```yaml
resources:
  cpu: 500m               # 2026-02-21: 1000m→500mに削減
  memory: 256Mi           # 2026-02-21: 512Mi→256Miに削減
```

### その他設定
```yaml
annotations:
  run.googleapis.com/startup-cpu-boost: true
  autoscaling.knative.dev/maxScale: '2'
```

## 設定変更履歴

### 2026-02-21: コスト最適化
**目的**: AUTOSCALING による料金増加懸念への対応

**変更内容**:
| 項目 | 変更前 | 変更後 | 削減率 |
|------|--------|--------|--------|
| 最大インスタンス数 | 5 | 2 | 60% |
| 同時実行数 | 80 | 1 | - |
| CPU | 1000m | 500m | 50% |
| メモリ | 512Mi | 256Mi | 50% |

**実行コマンド**:
```bash
# Step 1: スケーリング設定
gcloud run services update fx-insight-bot \
  --region=asia-northeast1 \
  --max-instances=2 \
  --concurrency=1

# Step 2: リソース削減
gcloud run services update fx-insight-bot \
  --region=asia-northeast1 \
  --cpu=500m \
  --memory=256Mi
```

**検証結果**: ✅ 正常動作確認済み

## 運用ガイドライン

### 料金最適化のベストプラクティス
1. **最小インスタンス数**: 0維持（コールドスタート許容）
2. **最大インスタンス数**: 必要最小限に制限
3. **リソース制限**: ワークロードに応じた適切な設定
4. **同時実行数**: シンプルな処理の場合は1に設定

### パフォーマンス監視
以下の指標を定期的に確認:
- **レスポンス時間**: 取引実行API応答速度
- **エラー率**: リソース不足によるエラー発生
- **コールドスタート時間**: インスタンス起動時間

### 設定変更の手順
1. **現在設定の確認**:
   ```bash
   gcloud run services describe fx-insight-bot --region=asia-northeast1
   ```

2. **設定変更**:
   ```bash
   gcloud run services update fx-insight-bot \
     --region=asia-northeast1 \
     [オプション]
   ```

3. **動作確認**:
   ```bash
   curl -X POST "https://fx-insight-bot-755346299346.asia-northeast1.run.app/health"
   ```

## トラブルシューティング

### よくある問題と解決方法

#### 1. CPU制限エラー
**エラー**: `cpu < 1 is not supported with concurrency > 1`
**解決**: 同時実行数を1に設定
```bash
gcloud run services update fx-insight-bot --region=asia-northeast1 --concurrency=1
```

#### 2. メモリ不足
**症状**: 502 Bad Gateway、アプリケーションクラッシュ
**解決**: メモリ制限を増加
```bash
gcloud run services update fx-insight-bot --region=asia-northeast1 --memory=512Mi
```

#### 3. レスポンス遅延
**症状**: タイムアウト、遅いレスポンス
**解決**: CPUを増加またはインスタンス数調整
```bash
gcloud run services update fx-insight-bot --region=asia-northeast1 --cpu=1000m
```

## 将来の最適化案

### トラフィック増加時の対応
```bash
# より多くのリクエストが予想される場合
gcloud run services update fx-insight-bot \
  --region=asia-northeast1 \
  --max-instances=5 \
  --concurrency=10 \
  --cpu=1000m \
  --memory=512Mi
```

### コールドスタート回避
```bash
# レスポンス時間を重視する場合
gcloud run services update fx-insight-bot \
  --region=asia-northeast1 \
  --min-instances=1
```

## 関連サービス設定

### fx-insight-bot-api
- **URL**: https://fx-insight-bot-api-755346299346.asia-northeast1.run.app
- **用途**: APIサーバー（別サービス）
- **設定**: 個別管理

### Cloud Scheduler連携
- **ジョブ名**: fx-trade-execute
- **スケジュール**: 0 9,21 * * 1-5 (Asia/Tokyo)
- **エンドポイント**: /api/v1/trade/execute

## 参考リンク
- [Cloud Run 料金](https://cloud.google.com/run/pricing)
- [Cloud Run CPU設定](https://cloud.google.com/run/docs/configuring/cpu)
- [Cloud Run スケーリング](https://cloud.google.com/run/docs/configuring/concurrency)