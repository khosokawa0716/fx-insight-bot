# Phase 2 進捗レポート - RSS News Collector実装

**日付**: 2026-01-01
**フェーズ**: Phase 2（ニュース収集機能）
**ステータス**: 🚧 進行中

---

## 📊 実施内容サマリー

### 完了した実装

#### 1. RSS取得機能 ✅ 完了
実装ファイル: `backend/src/services/news_collector.py`

**主要クラス**:
- `NewsArticle`: 生のニュース記事データモデル
- `RSSFeed`: RSSフィードソース設定
- `NewsCollector`: メインコレクタークラス

**実装機能**:
- [x] 複数ソースからのRSS取得（Bloomberg、Reuters、Yahoo!ファイナンス）
- [x] feedparserを使用した堅牢なRSSパース処理
- [x] 重複チェック機能（URL + ニュースIDの二重チェック）
- [x] SHA256ハッシュベースの一意なニュースID生成
  - フォーマット: `news_YYYYMMDD_<12桁hash>`
- [x] エラーハンドリングとログ出力
- [x] スタンドアロン実行機能

**技術的な特徴**:
```python
# ニュースID生成例
news_20260101_07cb384454ef

# 重複チェック
- seen_urls: Set[str]  # URLベースの重複チェック
- seen_ids: Set[str]   # IDベースの重複チェック
```

#### 2. テストコード作成 ✅ 完了
テストファイル: `backend/tests/test_news_collector.py`

**テストカバレッジ**:
- NewsArticleクラス: 2テスト
- RSSFeedクラス: 2テスト
- NewsCollectorクラス: 12テスト
- モジュールレベル関数: 1テスト
- **合計: 17テストケース、全てパス ✅**

**テスト内容**:
- [x] データモデルの作成とシリアライズ
- [x] ニュースID生成ロジック
- [x] 重複検出ロジック
- [x] 日付パース処理（published_parsed、updated_parsedフォールバック）
- [x] コンテンツ抽出処理
- [x] フィード取得処理（成功ケース）
- [x] エントリスキップ処理（URLなし）
- [x] フィード内重複排除
- [x] 全フィードからの収集

#### 3. 動作確認 ✅ 完了

**実行コマンド**:
```bash
cd backend
source venv/bin/activate
python -m src.services.news_collector
```

**結果**:
- Yahoo Finance: **49件取得成功** ✅
- Bloomberg: 0件（フィードURL要調整）
- Reuters: 0件（フィードURL要調整）

**取得例**:
```
1. [Yahoo Finance] Investors should beware of AI's circular financing trap
   URL: https://finance.yahoo.com/news/investors-should-beware-of-ais-...
   Published: 2025-12-30 18:31:52+00:00
   ID: news_20251230_07cb384454ef
```

---

## 🔧 技術的な詳細

### アーキテクチャ

```
NewsCollector
├── RSS_FEEDS: List[RSSFeed]
│   └── 各ソースの設定（URL、言語、トピック）
├── seen_urls: Set[str]
├── seen_ids: Set[str]
└── Methods
    ├── fetch_feed(feed) -> List[NewsArticle]
    ├── collect_all() -> List[NewsArticle]
    ├── generate_news_id(url, datetime) -> str
    ├── is_duplicate(news_id, url) -> bool
    ├── parse_published_date(entry) -> datetime
    └── extract_content(entry) -> (content, summary)
```

### データフロー

```
RSSフィード URL
    ↓
feedparser.parse()
    ↓
各エントリを処理
    ├── タイトル・URL抽出
    ├── 公開日時パース
    ├── ニュースID生成
    ├── 重複チェック
    └── コンテンツ抽出
    ↓
NewsArticle オブジェクト作成
    ↓
List[NewsArticle] 返却
```

### エラーハンドリング

- フィードパースエラー: ログ警告、処理継続
- エントリ処理エラー: ログエラー、該当エントリスキップ
- URL欠落: ログ警告、エントリスキップ
- 日付パース失敗: 現在時刻をフォールバック

---

## 📝 残タスク

### Phase 2 残り実装

#### 2. Firestoreへの保存機能（次のステップ）
- [ ] `news_events` コレクションへの保存ロジック
- [ ] NewsArticle → Firestoreドキュメント変換
- [ ] 重複チェック（Firestore側でも実施）
- [ ] エラーハンドリング
- [ ] バッチ保存処理（効率化）

#### 3. 定期実行スクリプト作成
- [ ] スタンドアロンスクリプトの作成
- [ ] 収集→Firestore保存の一連フロー
- [ ] 手動実行での動作確認
- [ ] Cloud Schedulerでの定期実行設定（後のフェーズ）

### RSS フィードURL調整

#### Bloomberg
現在のURL（要確認）:
```
https://www.bloomberg.com/feed/podcast/etf-report.xml
```

検討すべき代替URL:
- Bloomberg Markets RSS
- Bloomberg Japan RSS（日本語記事）

#### Reuters
現在のURL（要確認）:
```
https://www.reuters.com/business/finance/rss
```

検討すべき代替URL:
- Reuters Japan Business RSS
- Reuters Markets RSS

**アクションアイテム**:
- [ ] 各ニュースソースの有効なRSS URL確認
- [ ] 日本語記事が含まれるフィードの特定
- [ ] 利用規約・レート制限の確認

---

## 🎯 次のステップ

### 優先度1: Firestore保存機能
1. `NewsCollector`から取得した記事をFirestoreに保存
2. 既存の`NewsEvent`モデルとの整合性確認
3. AI分析前の「生データ」として保存（AI分析フィールドは後で追加）

### 優先度2: 統合テスト
1. RSS取得 → Firestore保存の一連フロー
2. 重複記事の適切な処理
3. エラーケースの処理

### 優先度3: RSSフィードURL最適化
1. Bloomberg、Reutersの有効なフィード確認
2. FX関連記事が多く含まれるフィードの選定

---

## 📚 学んだこと・メモ

### feedparserの使い方
- `published_parsed` と `updated_parsed` のフォールバック処理が重要
- `bozo` フラグでパース警告を検出
- エントリは辞書ライクなアクセスが可能

### テスト設計
- `MagicMock.get()` のモック設定には `side_effect` を使用
- feedparserの動作を正確に再現するためのモック工夫

### ハッシュベースID
- URL + 公開日時のハッシュで一意性を保証
- 日付プレフィックスで時系列ソートが容易

---

## 📦 成果物

### 新規作成ファイル
- `backend/src/services/news_collector.py` (370行)
- `backend/tests/test_news_collector.py` (380行)

### 更新ファイル
- `docs/progress/2025-12-31_phase0-1_completion.md`

### コミット
```
d3bd351 feat: RSS News Collector実装完了
```

---

## 🚀 実行方法

### テスト実行
```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_news_collector.py -v
```

### スタンドアロン実行
```bash
cd backend
source venv/bin/activate
python -m src.services.news_collector
```

### モジュールとしてインポート
```python
from src.services.news_collector import collect_news, NewsCollector

# シンプルな使い方
articles = collect_news()

# 詳細制御
collector = NewsCollector()
articles = collector.collect_all()
```

---

**次回セッション**: Firestore保存機能の実装
