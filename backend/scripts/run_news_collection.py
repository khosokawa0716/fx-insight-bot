#!/usr/bin/env python3
"""
Scheduled News Collection Script

Cloud Schedulerや手動実行から呼び出されるニュース収集スクリプト
1日1回の定期実行を想定しています。
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 環境変数を読み込む
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from src.services.news_pipeline import run_news_collection

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """
    ニュース収集のメイン処理

    環境変数で設定可能なパラメータ:
    - NEWS_COUNT: 取得するニュース件数 (デフォルト: 5)
    - SKIP_DUPLICATE: 重複をスキップするか (デフォルト: True)
    """
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("Starting scheduled news collection")
    logger.info(f"Start time: {start_time.isoformat()}")
    logger.info("=" * 60)

    try:
        # ニュース収集実行
        stats = run_news_collection(
            query="USD/JPY EUR/JPY 為替 最新ニュース",
            news_count=5,  # 1日1回なので5件取得
            skip_duplicate=True,
        )

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # 結果サマリー
        logger.info("=" * 60)
        logger.info("News collection completed successfully")
        logger.info(f"End time: {end_time.isoformat()}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("=" * 60)
        logger.info(f"Analyzed: {stats['analyzed']} news items")
        logger.info(f"Saved:    {stats['saved']} items")
        logger.info(f"Skipped:  {stats['skipped']} items (duplicates)")
        logger.info(f"Failed:   {stats['failed']} items")

        if stats["saved_ids"]:
            logger.info(f"Saved news IDs: {', '.join(stats['saved_ids'])}")

        # 成功終了
        sys.exit(0)

    except Exception as e:
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        logger.error("=" * 60)
        logger.error("News collection FAILED")
        logger.error(f"End time: {end_time.isoformat()}")
        logger.error(f"Duration: {duration:.2f} seconds")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)

        import traceback

        traceback.print_exc()

        # 異常終了
        sys.exit(1)


if __name__ == "__main__":
    main()
