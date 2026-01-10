"""
Firestore Save Functionality Test

NewsStorageサービスのローカルテストスクリプト
モックJSONデータを使用してFirestoreへの保存機能を検証します。
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.news_analyzer import NewsAnalysisResult
from src.services.news_storage import NewsStorage, DuplicateNewsError

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# モックデータ定義
# ============================================================

MOCK_NEWS_DATA = [
    {
        "title": "日銀が金利据え置き決定",
        "summary": "日銀が政策金利を据え置き。市場は予想通りと受け止め。",
        "sentiment": 0,
        "impact_usd_jpy": 4,
        "impact_eur_jpy": 2,
        "time_horizon": "short-term",
        "source_url": "https://example.com/news/123",
        "rationale": "金融政策の現状維持により市場への影響は限定的",
    },
    {
        "title": "米FOMC、利上げ継続を決定",
        "summary": "FRBが0.25%の利上げを実施。インフレ抑制姿勢を継続。",
        "sentiment": 2,
        "impact_usd_jpy": 5,
        "impact_eur_jpy": 3,
        "time_horizon": "medium-term",
        "source_url": "https://example.com/news/456",
        "rationale": "米金利上昇により円安ドル高が進行する可能性が高い",
    },
    {
        "title": "ECB、追加利下げを示唆",
        "summary": "ラガルド総裁が景気減速懸念から追加緩和の可能性に言及。",
        "sentiment": -1,
        "impact_usd_jpy": 2,
        "impact_eur_jpy": 4,
        "time_horizon": "short-term",
        "source_url": "https://example.com/news/789",
        "rationale": "ユーロ安進行によりEUR/JPYは下落圧力を受ける",
    },
]

# エッジケース: 範囲外の値
INVALID_SENTIMENT_DATA = {
    "title": "テストニュース: 無効なセンチメント",
    "summary": "センチメント値が範囲外（3）のテストケース",
    "sentiment": 3,  # 無効: -2〜2の範囲外
    "impact_usd_jpy": 3,
    "impact_eur_jpy": 3,
    "time_horizon": "short-term",
    "source_url": "https://example.com/test/invalid-sentiment",
    "rationale": "無効データテスト",
}

INVALID_IMPACT_DATA = {
    "title": "テストニュース: 無効なインパクト",
    "summary": "インパクト値が範囲外（6）のテストケース",
    "sentiment": 0,
    "impact_usd_jpy": 6,  # 無効: 1〜5の範囲外
    "impact_eur_jpy": 2,
    "time_horizon": "short-term",
    "source_url": "https://example.com/test/invalid-impact",
    "rationale": "無効データテスト",
}


# ============================================================
# テスト関数
# ============================================================


def create_analysis_result(data: dict) -> NewsAnalysisResult:
    """モックデータからNewsAnalysisResultを作成"""
    return NewsAnalysisResult(
        title=data["title"],
        summary=data["summary"],
        sentiment=data["sentiment"],
        impact_usd_jpy=data["impact_usd_jpy"],
        impact_eur_jpy=data["impact_eur_jpy"],
        time_horizon=data["time_horizon"],
        source_url=data["source_url"],
        rationale=data["rationale"],
        analyzed_at=datetime.now(timezone.utc),
    )


def test_1_normal_save():
    """TEST 1: 正常なデータ保存"""
    print("\n" + "=" * 60)
    print("TEST 1: 正常なデータ保存")
    print("=" * 60)

    try:
        storage = NewsStorage()
        results = [create_analysis_result(data) for data in MOCK_NEWS_DATA]

        print(f"\n📝 保存するニュース件数: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.title}")

        print("\n⏳ Firestoreに保存中...")
        stats = storage.save_multiple_news(results, skip_duplicate=True)

        print("\n✅ 保存完了")
        print(f"   Total:   {stats['total']} items")
        print(f"   Saved:   {stats['saved']} items")
        print(f"   Skipped: {stats['skipped']} items (duplicates)")
        print(f"   Failed:  {stats['failed']} items")

        if stats["saved_ids"]:
            print(f"\n💾 保存されたニュースID:")
            for news_id in stats["saved_ids"]:
                print(f"   - {news_id}")

        return stats["saved_ids"]

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return []


def test_2_duplicate_detection(saved_ids: list):
    """TEST 2: 重複検出"""
    print("\n" + "=" * 60)
    print("TEST 2: 重複検出テスト")
    print("=" * 60)

    if not saved_ids:
        print("\n⚠️ TEST 1で保存されたデータがないため、スキップします")
        return

    try:
        storage = NewsStorage()

        # 同じデータを再度保存（重複をスキップ）
        results = [create_analysis_result(data) for data in MOCK_NEWS_DATA]

        print(f"\n📝 同じニュースを再度保存（重複スキップモード）")
        print("\n⏳ Firestoreに保存中...")
        stats = storage.save_multiple_news(results, skip_duplicate=True)

        print("\n✅ 重複検出完了")
        print(f"   Total:   {stats['total']} items")
        print(f"   Saved:   {stats['saved']} items (新規)")
        print(f"   Skipped: {stats['skipped']} items (重複)")
        print(f"   Failed:  {stats['failed']} items")

        if stats["skipped"] == len(MOCK_NEWS_DATA):
            print("\n✅ 重複検出が正常に動作しています")
        else:
            print(
                f"\n⚠️ 警告: {stats['saved']} 件が新規として保存されました（重複検出が期待通り動作していない可能性）"
            )

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback

        traceback.print_exc()


def test_3_retrieve_news(saved_ids: list):
    """TEST 3: ニュース取得"""
    print("\n" + "=" * 60)
    print("TEST 3: ニュース取得テスト")
    print("=" * 60)

    if not saved_ids:
        print("\n⚠️ TEST 1で保存されたデータがないため、スキップします")
        return

    try:
        storage = NewsStorage()
        news_id = saved_ids[0]

        print(f"\n📝 ニュースIDで取得: {news_id}")
        print("\n⏳ Firestoreから取得中...")

        news = storage.get_news_by_id(news_id)

        if news:
            print("\n✅ 取得成功")
            print(f"   Title:        {news.title}")
            print(f"   Sentiment:    {news.sentiment}")
            print(f"   Impact USD/JPY: {news.impact_usdjpy}")
            print(f"   Impact EUR/JPY: {news.impact_eurjpy}")
            print(f"   Time Horizon: {news.time_horizon}")
        else:
            print(f"\n❌ 取得失敗: ニュースが見つかりません")

        # 最近のニュースを取得
        print(f"\n📝 最近のニュースを取得 (limit=5)")
        print("\n⏳ Firestoreから取得中...")

        recent_news = storage.get_recent_news(limit=5)

        print(f"\n✅ {len(recent_news)} 件取得")
        for i, news in enumerate(recent_news, 1):
            print(f"   {i}. {news.title} (collected: {news.collected_at})")

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback

        traceback.print_exc()


def test_4_invalid_data():
    """TEST 4: 無効なデータの処理"""
    print("\n" + "=" * 60)
    print("TEST 4: 無効なデータ処理テスト")
    print("=" * 60)

    storage = NewsStorage()

    # Test 4-1: 無効なセンチメント値
    print("\n📝 TEST 4-1: 無効なセンチメント値（3）")
    try:
        result = create_analysis_result(INVALID_SENTIMENT_DATA)
        news_id = storage.save_news(result)
        print(f"   ⚠️ 保存成功（バリデーションが機能していない可能性）: {news_id}")
    except Exception as e:
        print(f"   ✅ 期待通りエラー発生: {type(e).__name__}")

    # Test 4-2: 無効なインパクト値
    print("\n📝 TEST 4-2: 無効なインパクト値（6）")
    try:
        result = create_analysis_result(INVALID_IMPACT_DATA)
        news_id = storage.save_news(result)
        print(f"   ⚠️ 保存成功（バリデーションが機能していない可能性）: {news_id}")
    except Exception as e:
        print(f"   ✅ 期待通りエラー発生: {type(e).__name__}")


# ============================================================
# メイン実行
# ============================================================


def main():
    print("=" * 60)
    print("Firestore Save Functionality Test")
    print("=" * 60)
    print("\nこのテストは実際のFirestoreに接続します。")
    print("GCPプロジェクトとサービスアカウントの設定を確認してください。")
    print("\n" + "=" * 60)

    # TEST 1: 正常なデータ保存
    saved_ids = test_1_normal_save()

    # TEST 2: 重複検出
    test_2_duplicate_detection(saved_ids)

    # TEST 3: ニュース取得
    test_3_retrieve_news(saved_ids)

    # TEST 4: 無効なデータ処理
    test_4_invalid_data()

    print("\n" + "=" * 60)
    print("All Tests Completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
