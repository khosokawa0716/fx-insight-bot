"""
Cloud Functions Entry Point for News Collection

Cloud Schedulerから呼び出されるCloud Functions
"""

import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
root_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(root_dir))

from src.services.news_pipeline import run_news_collection

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def collect_fx_news(request):
    """
    Cloud Functions HTTPエントリポイント

    Args:
        request: Flask Request object
            {
                "query": str (optional),
                "news_count": int (optional),
                "skip_duplicate": bool (optional)
            }

    Returns:
        JSON response with status and statistics
    """
    logger.info("Cloud Function triggered")

    try:
        # リクエストパラメータ取得
        request_json = request.get_json(silent=True)
        query = request_json.get("query", "USD/JPY EUR/JPY 為替 最新ニュース") if request_json else "USD/JPY EUR/JPY 為替 最新ニュース"
        news_count = request_json.get("news_count", 5) if request_json else 5
        skip_duplicate = request_json.get("skip_duplicate", True) if request_json else True

        logger.info(f"Parameters: query={query}, news_count={news_count}, skip_duplicate={skip_duplicate}")

        # ニュース収集実行
        stats = run_news_collection(
            query=query,
            news_count=news_count,
            skip_duplicate=skip_duplicate,
        )

        logger.info(f"Collection completed: {stats}")

        return {
            "status": "success",
            "message": "News collection completed",
            "stats": stats,
        }, 200

    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }, 500
