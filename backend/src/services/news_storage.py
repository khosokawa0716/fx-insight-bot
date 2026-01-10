"""
News Storage Service

NewsAnalysisResultをFirestoreに保存し、重複チェックを行うサービス
"""

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Set

from google.cloud import firestore

from src.config import settings, get_credentials_path
from src.models.firestore import NewsEvent
from src.services.news_analyzer import NewsAnalysisResult

# 日本時間タイムゾーン（JST = UTC+9）
JST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)


class NewsStorageError(Exception):
    """News Storage基底例外クラス"""

    pass


class DuplicateNewsError(NewsStorageError):
    """重複ニュースエラー"""

    pass


class NewsStorage:
    """ニュース保存サービス"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        database_id: Optional[str] = None,
    ):
        """
        初期化

        Args:
            project_id: GCPプロジェクトID（省略時は設定から取得）
            database_id: FirestoreデータベースID（省略時は設定から取得）
        """
        self.project_id = project_id or settings.gcp_project_id
        self.database_id = database_id or settings.firestore_database_id

        # Firestoreクライアント初期化
        credentials_path = get_credentials_path()
        self.db = firestore.Client(
            project=self.project_id,
            database=self.database_id,
        )

        logger.info(
            f"NewsStorage initialized (project={self.project_id}, "
            f"database={self.database_id})"
        )

    def _generate_news_id(self, title: str, source_url: str, analyzed_at: datetime) -> str:
        """
        ニュースIDを生成

        Args:
            title: ニュースタイトル
            source_url: ソースURL
            analyzed_at: 分析日時（未使用、後方互換性のため保持）

        Returns:
            一意なニュースID
        """
        # タイトル + URLでハッシュ生成
        # 同じニュースが複数回収集されても、日付をまたいでも同じIDを生成する
        content = f"{title}_{source_url}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]

        # フォーマット: news_[16-char-hash]
        return f"news_{hash_digest}"

    def _check_duplicate(self, news_id: str) -> bool:
        """
        重複チェック

        Args:
            news_id: ニュースID

        Returns:
            True: 重複, False: 新規
        """
        doc_ref = self.db.collection("news_events").document(news_id)
        doc = doc_ref.get()

        if doc.exists:
            logger.debug(f"Duplicate news found: {news_id}")
            return True

        return False

    def _convert_to_news_event(
        self, result: NewsAnalysisResult, news_id: str, signal: str = "IGNORE"
    ) -> NewsEvent:
        """
        NewsAnalysisResultをNewsEventに変換

        Args:
            result: 分析結果
            news_id: ニュースID
            signal: シグナル（デフォルト: IGNORE）

        Returns:
            NewsEventオブジェクト
        """
        # published_atは不明なので、analyzed_atを日本時間に変換して使用
        # 実際のニュースソースから取得できる場合は、そちらを優先すべき
        published_at = result.analyzed_at.astimezone(JST)
        collected_at = result.analyzed_at.astimezone(JST)

        return NewsEvent(
            news_id=news_id,
            source="Gemini Grounding",
            title=result.title,
            url=result.source_url,
            published_at=published_at,
            collected_at=collected_at,
            content_raw=None,
            summary_raw=None,
            topic=None,  # 今後、トピック分類を追加する場合
            sentiment=result.sentiment,
            impact_usdjpy=result.impact_usd_jpy,
            impact_eurjpy=result.impact_eur_jpy,
            time_horizon=result.time_horizon,
            summary_ai=result.summary,
            rationale=result.rationale,
            signal=signal,
            rule_version="v1.0",
            tweet_text=None,
            is_tweeted=False,
            tweeted_at=None,
        )

    def save_news(
        self, result: NewsAnalysisResult, skip_duplicate: bool = True
    ) -> Optional[str]:
        """
        単一のニュースを保存

        Args:
            result: 分析結果
            skip_duplicate: 重複時にスキップするか

        Returns:
            保存されたニュースID（重複スキップ時はNone）

        Raises:
            DuplicateNewsError: 重複ニュースの場合（skip_duplicate=Falseの時）
            NewsStorageError: 保存に失敗した場合
        """
        try:
            # ニュースID生成
            news_id = self._generate_news_id(
                result.title, result.source_url, result.analyzed_at
            )

            # 重複チェック
            if self._check_duplicate(news_id):
                if skip_duplicate:
                    logger.info(f"Skipped duplicate news: {news_id}")
                    return None
                else:
                    raise DuplicateNewsError(f"News already exists: {news_id}")

            # NewsEventに変換
            news_event = self._convert_to_news_event(result, news_id)

            # Firestoreに保存
            doc_ref = self.db.collection("news_events").document(news_id)
            doc_ref.set(news_event.model_dump(mode="json"))

            logger.info(f"Saved news: {news_id}")
            return news_id

        except DuplicateNewsError:
            raise

        except Exception as e:
            logger.error(f"Failed to save news: {e}")
            raise NewsStorageError(f"Failed to save news: {e}") from e

    def save_multiple_news(
        self, results: List[NewsAnalysisResult], skip_duplicate: bool = True
    ) -> dict:
        """
        複数のニュースを一括保存

        Args:
            results: 分析結果のリスト
            skip_duplicate: 重複時にスキップするか

        Returns:
            保存結果の統計情報
            {
                "total": 処理件数,
                "saved": 保存件数,
                "skipped": スキップ件数,
                "failed": 失敗件数,
                "saved_ids": 保存されたニュースIDリスト
            }
        """
        stats = {
            "total": len(results),
            "saved": 0,
            "skipped": 0,
            "failed": 0,
            "saved_ids": [],
        }

        logger.info(f"Starting batch save: {len(results)} news items")

        for i, result in enumerate(results, 1):
            try:
                news_id = self.save_news(result, skip_duplicate=skip_duplicate)

                if news_id:
                    stats["saved"] += 1
                    stats["saved_ids"].append(news_id)
                else:
                    stats["skipped"] += 1

            except Exception as e:
                logger.error(f"Failed to save news item {i}: {e}")
                stats["failed"] += 1
                continue

        logger.info(
            f"Batch save completed: {stats['saved']} saved, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        return stats

    def get_news_by_id(self, news_id: str) -> Optional[NewsEvent]:
        """
        ニュースIDでニュースを取得

        Args:
            news_id: ニュースID

        Returns:
            NewsEventオブジェクト（存在しない場合はNone）
        """
        try:
            doc_ref = self.db.collection("news_events").document(news_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.debug(f"News not found: {news_id}")
                return None

            return NewsEvent(**doc.to_dict())

        except Exception as e:
            logger.error(f"Failed to get news: {e}")
            raise NewsStorageError(f"Failed to get news: {e}") from e

    def get_recent_news(self, limit: int = 10) -> List[NewsEvent]:
        """
        最近のニュースを取得

        Args:
            limit: 取得件数

        Returns:
            NewsEventのリスト
        """
        try:
            docs = (
                self.db.collection("news_events")
                .order_by("collected_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )

            news_list = []
            for doc in docs:
                try:
                    news_list.append(NewsEvent(**doc.to_dict()))
                except Exception as e:
                    logger.warning(f"Failed to parse news document {doc.id}: {e}")
                    continue

            logger.info(f"Retrieved {len(news_list)} recent news items")
            return news_list

        except Exception as e:
            logger.error(f"Failed to get recent news: {e}")
            raise NewsStorageError(f"Failed to get recent news: {e}") from e


def save_analysis_results(
    results: List[NewsAnalysisResult], skip_duplicate: bool = True
) -> dict:
    """
    分析結果を保存する便利関数

    Args:
        results: 分析結果のリスト
        skip_duplicate: 重複時にスキップするか

    Returns:
        保存結果の統計情報
    """
    storage = NewsStorage()
    return storage.save_multiple_news(results, skip_duplicate=skip_duplicate)


if __name__ == "__main__":
    # スタンドアロン実行用
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("News Storage Service - Test")
    print("=" * 60)

    # テスト用のNewsAnalysisResultを作成
    test_result = NewsAnalysisResult(
        title="テストニュース: 日銀が金利据え置き",
        summary="日銀が政策金利を据え置き。市場は予想通りと受け止め。",
        sentiment=0,
        impact_usd_jpy=4,
        impact_eur_jpy=2,
        time_horizon="short-term",
        source_url="https://example.com/test-news",
        rationale="金融政策の現状維持により市場への影響は限定的",
        analyzed_at=datetime.now(timezone.utc),
    )

    try:
        storage = NewsStorage()

        # 保存テスト
        print("\n保存テスト...")
        news_id = storage.save_news(test_result)
        print(f"✅ 保存成功: {news_id}")

        # 取得テスト
        print(f"\n取得テスト (ID: {news_id})...")
        news = storage.get_news_by_id(news_id)
        if news:
            print(f"✅ 取得成功: {news.title}")
        else:
            print("❌ 取得失敗")

        # 重複チェックテスト
        print("\n重複チェックテスト...")
        news_id_2 = storage.save_news(test_result, skip_duplicate=True)
        if news_id_2 is None:
            print("✅ 重複検出成功")
        else:
            print("❌ 重複検出失敗")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
