# Firestore データベース設計書

## 1. 設計方針

### 1.1 基本方針
- **非正規化設計**: 読み取り性能を優先し、データの重複を許容
- **シンプル構造**: サブコレクションは使用せず、フラットな構造
- **型安全性**: フィールドの型を明確に定義
- **コスト最適化**: データ保持期間を制限し、BigQueryにアーカイブ

### 1.2 データ保持期間
- **Firestore**: 最新3ヶ月分のみ保持
- **BigQuery**: 全データを永久保存(分析・バックテスト用)
- **削除方法**: Cloud Functionsで定期的に古いデータを削除

### 1.3 インデックス
- 初期段階ではカスタムインデックスは作成しない
- パフォーマンス問題が発生した場合に、実際のクエリパターンに基づいて追加

---

## 2. コレクション設計

### 2.1 `news_events` コレクション

ニュース記事とAI分析結果を保存

#### スキーマ定義

| フィールド名 | 型 | 必須 | 説明 | 例 |
|------------|-----|------|------|-----|
| `news_id` | string | ○ | ニュース一意ID (自動生成) | `news_20250113_001` |
| `source` | string | ○ | ニュースソース名 | `Reuters`, `Bloomberg` |
| `title` | string | ○ | ニュースタイトル | `日銀が金利据え置き決定` |
| `url` | string | ○ | 記事URL | `https://...` |
| `published_at` | timestamp | ○ | 記事公開日時 | `2025-01-13T10:00:00Z` |
| `collected_at` | timestamp | ○ | システム収集日時 | `2025-01-13T10:05:00Z` |
| `content_raw` | string | △ | 記事本文(取得できた場合) | `...` |
| `summary_raw` | string | △ | RSS概要文 | `...` |
| `topic` | string | ○ | トピック分類 | `金融政策`, `経済指標`, `地政学` |
| `sentiment` | number | ○ | センチメントスコア | `-2`, `-1`, `0`, `1`, `2` |
| `impact_usdjpy` | number | ○ | USD/JPYへの影響度(0-10) | `7` |
| `impact_eurusd` | number | ○ | EUR/USDへの影響度(0-10) | `3` |
| `time_horizon` | string | ○ | 影響の時間軸 | `immediate`, `short`, `mid`, `long` |
| `summary_ai` | string | ○ | AI要約文(3-4行) | `日銀が金利を据え置き...` |
| `signal` | string | ○ | 生成されたシグナル | `BUY_CANDIDATE`, `SELL_CANDIDATE`, `RISK_OFF`, `IGNORE` |
| `rule_version` | string | ○ | 適用されたルールバージョン | `v1.0`, `v1.1` |
| `tweet_text` | string | △ | X投稿用テキスト | `日銀が金利据え置き...` |
| `is_tweeted` | boolean | ○ | X投稿済みフラグ | `true`, `false` |
| `tweeted_at` | timestamp | △ | X投稿日時 | `2025-01-13T11:00:00Z` |

#### インデックス(将来追加予定)

必要に応じて以下を作成:

```javascript
// 日時降順で重要度フィルタ
{ published_at: 'DESC', impact_usdjpy: 'DESC' }

// シグナル別で日時降順
{ signal: 'ASC', published_at: 'DESC' }

// トピック・センチメント別で日時降順
{ topic: 'ASC', sentiment: 'ASC', published_at: 'DESC' }
```

#### セキュリティルール

```javascript
match /news_events/{newsId} {
  // 管理者のみ読み書き可能
  allow read, write: if request.auth != null && request.auth.token.admin == true;
}
```

---

### 2.2 `trades` コレクション

取引履歴を保存

#### スキーマ定義

| フィールド名 | 型 | 必須 | 説明 | 例 |
|------------|-----|------|------|-----|
| `trade_id` | string | ○ | 取引一意ID | `trade_20250113_001` |
| `news_id` | string | △ | 関連ニュースID(参照) | `news_20250113_001` |
| `pair` | string | ○ | 通貨ペア | `USD/JPY`, `EUR/USD` |
| `side` | string | ○ | 売買方向 | `buy`, `sell` |
| `opened_at` | timestamp | ○ | エントリー日時 | `2025-01-13T10:30:00Z` |
| `closed_at` | timestamp | △ | クローズ日時 | `2025-01-13T15:00:00Z` |
| `entry_price` | number | ○ | エントリー価格 | `148.50` |
| `exit_price` | number | △ | 決済価格 | `148.70` |
| `units` | number | ○ | 取引数量 | `1000` |
| `stop_loss` | number | △ | ストップロス価格 | `148.30` |
| `take_profit` | number | △ | テイクプロフィット価格 | `148.90` |
| `result_pips` | number | △ | 結果(pips) | `20.0` |
| `result_jpy` | number | △ | 結果(円換算) | `200` |
| `status` | string | ○ | 取引状態 | `open`, `closed`, `cancelled` |
| `rule_version` | string | ○ | 適用されたルールバージョン | `v1.0` |
| `memo` | string | △ | メモ | `ニュースに基づくエントリー` |
| `created_at` | timestamp | ○ | 作成日時 | `2025-01-13T10:30:00Z` |
| `updated_at` | timestamp | ○ | 更新日時 | `2025-01-13T15:00:00Z` |

#### セキュリティルール

```javascript
match /trades/{tradeId} {
  // 管理者のみ読み書き可能
  allow read, write: if request.auth != null && request.auth.token.admin == true;
}
```

---

### 2.3 `positions` コレクション

現在保有中のポジション情報(リアルタイム更新)

#### スキーマ定義

| フィールド名 | 型 | 必須 | 説明 | 例 |
|------------|-----|------|------|-----|
| `position_id` | string | ○ | ポジションID(GMOコイン APIから) | `pos_123456` |
| `trade_id` | string | ○ | 関連取引ID | `trade_20250113_001` |
| `pair` | string | ○ | 通貨ペア | `USD/JPY` |
| `side` | string | ○ | 売買方向 | `buy`, `sell` |
| `units` | number | ○ | 保有数量 | `1000` |
| `entry_price` | number | ○ | エントリー価格 | `148.50` |
| `current_price` | number | ○ | 現在価格 | `148.65` |
| `unrealized_pnl` | number | ○ | 含み損益(円) | `150` |
| `stop_loss` | number | △ | ストップロス価格 | `148.30` |
| `take_profit` | number | △ | テイクプロフィット価格 | `148.90` |
| `opened_at` | timestamp | ○ | オープン日時 | `2025-01-13T10:30:00Z` |
| `updated_at` | timestamp | ○ | 最終更新日時 | `2025-01-13T12:00:00Z` |

#### セキュリティルール

```javascript
match /positions/{positionId} {
  // 管理者のみ読み書き可能
  allow read, write: if request.auth != null && request.auth.token.admin == true;
}
```

---

### 2.4 `system_config` コレクション

システム設定を保存(ルールバージョン、閾値など)

#### スキーマ定義

| フィールド名 | 型 | 必須 | 説明 | 例 |
|------------|-----|------|------|-----|
| `config_id` | string | ○ | 設定ID | `signal_rules`, `risk_management` |
| `version` | string | ○ | バージョン | `v1.0`, `v1.1` |
| `active` | boolean | ○ | 有効フラグ | `true`, `false` |
| `config_data` | map | ○ | 設定内容(JSON) | `{ "threshold": 5, ... }` |
| `created_at` | timestamp | ○ | 作成日時 | `2025-01-13T10:00:00Z` |
| `updated_at` | timestamp | ○ | 更新日時 | `2025-01-13T10:00:00Z` |

#### ドキュメント例

```javascript
// signal_rules ドキュメント
{
  config_id: "signal_rules",
  version: "v1.0",
  active: true,
  config_data: {
    buy_conditions: {
      sentiment_min: 1,
      impact_usdjpy_min: 5,
      topics: ["金融政策", "経済指標"]
    },
    sell_conditions: {
      sentiment_max: -1,
      impact_usdjpy_min: 5
    },
    risk_off_conditions: {
      sentiment_max: -2,
      topics: ["地政学"]
    }
  },
  created_at: "2025-01-13T10:00:00Z",
  updated_at: "2025-01-13T10:00:00Z"
}
```

#### セキュリティルール

```javascript
match /system_config/{configId} {
  // 管理者のみ読み書き可能
  allow read, write: if request.auth != null && request.auth.token.admin == true;
}
```

---

## 3. データライフサイクル管理

### 3.1 自動削除の実装(Cloud Functions)

```python
from datetime import datetime, timedelta
from google.cloud import firestore

def delete_old_news_events(request):
    """3ヶ月以上前のニュースを削除"""
    db = firestore.Client()
    threshold_date = datetime.now() - timedelta(days=90)

    # 古いニュースを検索
    old_news = db.collection('news_events').where(
        'published_at', '<', threshold_date
    ).stream()

    # バッチ削除
    batch = db.batch()
    count = 0
    for doc in old_news:
        batch.delete(doc.reference)
        count += 1
        if count >= 500:  # Firestoreのバッチ制限
            batch.commit()
            batch = db.batch()
            count = 0

    if count > 0:
        batch.commit()

    return f"Deleted old news events"

# Cloud Schedulerで月1回実行
# cron: 0 3 1 * *  (毎月1日 午前3時)
```

### 3.2 BigQueryへのエクスポート

Firebaseコンソールから設定:
- **エクスポート先**: BigQuery データセット `fx_insight_archive`
- **頻度**: 1日1回(午前2時)
- **対象コレクション**: `news_events`, `trades`

---

## 4. セキュリティルール(firestore.rules)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // デフォルトで全て拒否
    match /{document=**} {
      allow read, write: if false;
    }

    // 管理者のみアクセス可能
    function isAdmin() {
      return request.auth != null && request.auth.token.admin == true;
    }

    // news_eventsコレクション
    match /news_events/{newsId} {
      allow read, write: if isAdmin();
    }

    // tradesコレクション
    match /trades/{tradeId} {
      allow read, write: if isAdmin();
    }

    // positionsコレクション
    match /positions/{positionId} {
      allow read, write: if isAdmin();
    }

    // system_configコレクション
    match /system_config/{configId} {
      allow read, write: if isAdmin();
    }
  }
}
```

---

## 5. 型定義(TypeScript/Python)

### 5.1 TypeScript型定義

```typescript
// src/types/firestore.ts

export type Sentiment = -2 | -1 | 0 | 1 | 2;
export type TimeHorizon = 'immediate' | 'short' | 'mid' | 'long';
export type Signal = 'BUY_CANDIDATE' | 'SELL_CANDIDATE' | 'RISK_OFF' | 'IGNORE';
export type TradeSide = 'buy' | 'sell';
export type TradeStatus = 'open' | 'closed' | 'cancelled';

export interface NewsEvent {
  news_id: string;
  source: string;
  title: string;
  url: string;
  published_at: Date;
  collected_at: Date;
  content_raw?: string;
  summary_raw?: string;
  topic: string;
  sentiment: Sentiment;
  impact_usdjpy: number;
  impact_eurusd: number;
  time_horizon: TimeHorizon;
  summary_ai: string;
  signal: Signal;
  rule_version: string;
  tweet_text?: string;
  is_tweeted: boolean;
  tweeted_at?: Date;
}

export interface Trade {
  trade_id: string;
  news_id?: string;
  pair: string;
  side: TradeSide;
  opened_at: Date;
  closed_at?: Date;
  entry_price: number;
  exit_price?: number;
  units: number;
  stop_loss?: number;
  take_profit?: number;
  result_pips?: number;
  result_jpy?: number;
  status: TradeStatus;
  rule_version: string;
  memo?: string;
  created_at: Date;
  updated_at: Date;
}

export interface Position {
  position_id: string;
  trade_id: string;
  pair: string;
  side: TradeSide;
  units: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  stop_loss?: number;
  take_profit?: number;
  opened_at: Date;
  updated_at: Date;
}

export interface SystemConfig {
  config_id: string;
  version: string;
  active: boolean;
  config_data: Record<string, any>;
  created_at: Date;
  updated_at: Date;
}
```

### 5.2 Python型定義(Pydantic)

```python
# src/models/firestore.py

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

Sentiment = Literal[-2, -1, 0, 1, 2]
TimeHorizon = Literal['immediate', 'short', 'mid', 'long']
Signal = Literal['BUY_CANDIDATE', 'SELL_CANDIDATE', 'RISK_OFF', 'IGNORE']
TradeSide = Literal['buy', 'sell']
TradeStatus = Literal['open', 'closed', 'cancelled']

class NewsEvent(BaseModel):
    news_id: str
    source: str
    title: str
    url: str
    published_at: datetime
    collected_at: datetime
    content_raw: Optional[str] = None
    summary_raw: Optional[str] = None
    topic: str
    sentiment: Sentiment
    impact_usdjpy: int = Field(ge=0, le=10)
    impact_eurusd: int = Field(ge=0, le=10)
    time_horizon: TimeHorizon
    summary_ai: str
    signal: Signal
    rule_version: str
    tweet_text: Optional[str] = None
    is_tweeted: bool = False
    tweeted_at: Optional[datetime] = None

class Trade(BaseModel):
    trade_id: str
    news_id: Optional[str] = None
    pair: str
    side: TradeSide
    opened_at: datetime
    closed_at: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    units: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    result_pips: Optional[float] = None
    result_jpy: Optional[float] = None
    status: TradeStatus
    rule_version: str
    memo: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class Position(BaseModel):
    position_id: str
    trade_id: str
    pair: str
    side: TradeSide
    units: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime
    updated_at: datetime

class SystemConfig(BaseModel):
    config_id: str
    version: str
    active: bool
    config_data: dict
    created_at: datetime
    updated_at: datetime
```

---

## 6. 初期セットアップ手順

### 6.1 Firestoreの有効化

```bash
# GCPプロジェクトでFirestoreを有効化
gcloud firestore databases create --region=asia-northeast1

# セキュリティルールをデプロイ
firebase deploy --only firestore:rules
```

### 6.2 初期データの投入

```python
# scripts/init_firestore.py

from google.cloud import firestore
from datetime import datetime

db = firestore.Client()

# 初期設定を作成
config_ref = db.collection('system_config').document('signal_rules')
config_ref.set({
    'config_id': 'signal_rules',
    'version': 'v1.0',
    'active': True,
    'config_data': {
        'buy_conditions': {
            'sentiment_min': 1,
            'impact_usdjpy_min': 5,
            'topics': ['金融政策', '経済指標']
        },
        'sell_conditions': {
            'sentiment_max': -1,
            'impact_usdjpy_min': 5
        },
        'risk_off_conditions': {
            'sentiment_max': -2,
            'topics': ['地政学']
        }
    },
    'created_at': datetime.now(),
    'updated_at': datetime.now()
})

print("Initial config created")
```

---

## 7. よくある質問(FAQ)

### Q1. インデックスはいつ作成すべきですか?
**A**: クエリ実行時にFirestoreがエラーを返し、インデックス作成のリンクが表示されます。そのリンクから作成するか、Firebase Consoleで手動作成してください。

### Q2. データ削除は本当に自動で行われますか?
**A**: はい。Cloud Functionsをデプロイし、Cloud Schedulerで月1回実行するように設定します(Phase 2で実装)。

### Q3. BigQueryへのエクスポートはいつ行われますか?
**A**: Firebase Extensionsの「Export Collections to BigQuery」を使用し、毎日自動的にエクスポートされます。

### Q4. セキュリティルールで管理者を設定する方法は?
**A**: Firebase Authenticationでユーザーを作成後、Custom Claimsで `admin: true` を設定します。

```javascript
// Admin SDKで設定
admin.auth().setCustomUserClaims(uid, { admin: true });
```

---

## 8. 次のステップ

- [ ] Firestore有効化
- [ ] セキュリティルールデプロイ
- [ ] 初期設定データ投入
- [ ] BigQueryエクスポート設定(Phase 2)
- [ ] データ削除Cloud Function作成(Phase 2)

---

**ドキュメントバージョン**: v1.0
**最終更新日**: 2025-01-13
**次回レビュー**: 実装開始時
