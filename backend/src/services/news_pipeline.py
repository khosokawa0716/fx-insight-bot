"""
News Pipeline Service

ニュース収集・分析・保存の一連のパイプライン処理
"""

import logging
from typing import Dict, List, Optional

from src.services.news_analyzer import NewsAnalyzer, NewsAnalysisResult
from src.services.news_storage import NewsStorage

logger = logging.getLogger(__name__)


class NewsPipeline:
    """ニュース処理パイプライン"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "asia-northeast1",
        model: str = "gemini-2.5-flash",
        database_id: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 120,
    ):
        """
        初期化

        Args:
            project_id: GCPプロジェクトID
            location: リージョン
            model: 使用するGeminiモデル
            database_id: FirestoreデータベースID
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
            timeout: APIタイムアウト（秒）
        """
        self.analyzer = NewsAnalyzer(
            project_id=project_id,
            location=location,
            model=model,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
        )

        self.storage = NewsStorage(
            project_id=project_id,
            database_id=database_id,
        )

        logger.info("NewsPipeline initialized")

    def run(
        self,
        query: str = "USD/JPY EUR/JPY 為替 最新ニュース",
        news_count: int = 5,
        skip_duplicate: bool = True,
    ) -> Dict:
        """
        パイプライン実行: 分析 → 保存

        Args:
            query: 検索クエリ
            news_count: 取得するニュース件数
            skip_duplicate: 重複時にスキップするか

        Returns:
            実行結果の統計情報
            {
                "analyzed": 分析件数,
                "saved": 保存件数,
                "skipped": スキップ件数,
                "failed": 失敗件数,
                "saved_ids": 保存されたニュースIDリスト
            }
        """
        logger.info(f"Starting news pipeline (query='{query}', count={news_count})")

        try:
            # Step 1: ニュース分析
            logger.info("Step 1: Analyzing news...")
            results = self.analyzer.analyze_news(query=query, news_count=news_count)
            logger.info(f"Analyzed {len(results)} news items")

            # Step 2: Firestore保存
            logger.info("Step 2: Saving to Firestore...")
            save_stats = self.storage.save_multiple_news(
                results, skip_duplicate=skip_duplicate
            )

            # 統計情報をマージ
            pipeline_stats = {
                "analyzed": len(results),
                **save_stats,
            }

            logger.info(
                f"Pipeline completed: {pipeline_stats['analyzed']} analyzed, "
                f"{pipeline_stats['saved']} saved, "
                f"{pipeline_stats['skipped']} skipped, "
                f"{pipeline_stats['failed']} failed"
            )

            return pipeline_stats

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


def run_news_collection(
    query: str = "USD/JPY EUR/JPY 為替 最新ニュース",
    news_count: int = 5,
    skip_duplicate: bool = True,
) -> Dict:
    """
    ニュース収集を実行する便利関数

    Args:
        query: 検索クエリ
        news_count: 取得するニュース件数
        skip_duplicate: 重複時にスキップするか

    Returns:
        実行結果の統計情報
    """
    pipeline = NewsPipeline()
    return pipeline.run(query=query, news_count=news_count, skip_duplicate=skip_duplicate)


if __name__ == "__main__":
    # スタンドアロン実行用
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("News Pipeline - Collect & Save FX News")
    print("=" * 60)

    try:
        stats = run_news_collection(news_count=3)

        print("\n" + "=" * 60)
        print("Pipeline Results")
        print("=" * 60)
        print(f"Analyzed: {stats['analyzed']} news items")
        print(f"Saved:    {stats['saved']} items")
        print(f"Skipped:  {stats['skipped']} items (duplicates)")
        print(f"Failed:   {stats['failed']} items")
        print(f"\nSaved IDs:")
        for news_id in stats["saved_ids"]:
            print(f"  - {news_id}")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
