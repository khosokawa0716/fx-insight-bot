"""
Tests for News Collector Service
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import feedparser

from src.services.news_collector import (
    NewsCollector,
    NewsArticle,
    RSSFeed,
    collect_news,
)


class TestNewsArticle:
    """Test NewsArticle class"""

    def test_create_news_article(self):
        """Test creating a NewsArticle instance"""
        published_at = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        collected_at = datetime(2025, 1, 1, 10, 5, 0, tzinfo=timezone.utc)

        article = NewsArticle(
            news_id="news_20250101_abc123",
            source="Reuters",
            title="Test Article",
            url="https://example.com/article",
            published_at=published_at,
            collected_at=collected_at,
            content_raw="Full content here",
            summary_raw="Summary here",
        )

        assert article.news_id == "news_20250101_abc123"
        assert article.source == "Reuters"
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.published_at == published_at
        assert article.collected_at == collected_at
        assert article.content_raw == "Full content here"
        assert article.summary_raw == "Summary here"

    def test_to_dict(self):
        """Test converting NewsArticle to dictionary"""
        published_at = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        collected_at = datetime(2025, 1, 1, 10, 5, 0, tzinfo=timezone.utc)

        article = NewsArticle(
            news_id="news_20250101_abc123",
            source="Reuters",
            title="Test Article",
            url="https://example.com/article",
            published_at=published_at,
            collected_at=collected_at,
        )

        article_dict = article.to_dict()

        assert article_dict["news_id"] == "news_20250101_abc123"
        assert article_dict["source"] == "Reuters"
        assert article_dict["title"] == "Test Article"
        assert article_dict["url"] == "https://example.com/article"
        assert article_dict["published_at"] == published_at
        assert article_dict["collected_at"] == collected_at


class TestRSSFeed:
    """Test RSSFeed class"""

    def test_create_rss_feed(self):
        """Test creating an RSSFeed instance"""
        feed = RSSFeed(
            name="Test Feed",
            url="https://example.com/feed.xml",
            language="en",
            topics=["finance", "markets"],
        )

        assert feed.name == "Test Feed"
        assert feed.url == "https://example.com/feed.xml"
        assert feed.language == "en"
        assert feed.topics == ["finance", "markets"]

    def test_create_rss_feed_default_topics(self):
        """Test RSSFeed with default empty topics"""
        feed = RSSFeed(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )

        assert feed.topics == []
        assert feed.language == "en"


class TestNewsCollector:
    """Test NewsCollector class"""

    def test_init(self):
        """Test NewsCollector initialization"""
        collector = NewsCollector()

        assert len(collector.seen_urls) == 0
        assert len(collector.seen_ids) == 0

    def test_generate_news_id(self):
        """Test generating unique news IDs"""
        collector = NewsCollector()
        published_at = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        news_id_1 = collector.generate_news_id(
            "https://example.com/article1", published_at
        )
        news_id_2 = collector.generate_news_id(
            "https://example.com/article2", published_at
        )

        # IDs should be different for different URLs
        assert news_id_1 != news_id_2

        # IDs should start with news_YYYYMMDD_
        assert news_id_1.startswith("news_20250101_")
        assert news_id_2.startswith("news_20250101_")

        # Same URL and time should generate same ID
        news_id_3 = collector.generate_news_id(
            "https://example.com/article1", published_at
        )
        assert news_id_1 == news_id_3

    def test_is_duplicate(self):
        """Test duplicate detection"""
        collector = NewsCollector()

        # First article should not be duplicate
        is_dup_1 = collector.is_duplicate(
            "news_20250101_abc123", "https://example.com/article1"
        )
        assert is_dup_1 is False

        # Same ID should be duplicate
        is_dup_2 = collector.is_duplicate(
            "news_20250101_abc123", "https://example.com/article2"
        )
        assert is_dup_2 is True

        # Same URL should be duplicate
        is_dup_3 = collector.is_duplicate(
            "news_20250101_xyz789", "https://example.com/article1"
        )
        assert is_dup_3 is True

    def test_reset_seen(self):
        """Test resetting deduplication tracking"""
        collector = NewsCollector()

        collector.is_duplicate("news_20250101_abc123", "https://example.com/article1")
        assert len(collector.seen_ids) == 1
        assert len(collector.seen_urls) == 1

        collector.reset_seen()
        assert len(collector.seen_ids) == 0
        assert len(collector.seen_urls) == 0

    def test_parse_published_date_with_published_parsed(self):
        """Test parsing date from published_parsed"""
        collector = NewsCollector()

        # Mock feedparser entry
        entry = MagicMock()
        entry.published_parsed = (2025, 1, 1, 10, 30, 0, 0, 1, 0)

        result = collector.parse_published_date(entry)

        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_published_date_fallback_to_updated(self):
        """Test parsing date fallback to updated_parsed"""
        collector = NewsCollector()

        # Mock feedparser entry without published_parsed
        entry = MagicMock()
        entry.published_parsed = None
        entry.updated_parsed = (2025, 1, 1, 11, 0, 0, 0, 1, 0)

        result = collector.parse_published_date(entry)

        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 11

    def test_extract_content(self):
        """Test extracting content and summary from entry"""
        collector = NewsCollector()

        # Mock feedparser entry
        entry = MagicMock()
        entry.summary = "This is a summary"
        entry.content = [MagicMock(value="This is full content")]

        content_raw, summary_raw = collector.extract_content(entry)

        assert summary_raw == "This is a summary"
        assert content_raw == "This is full content"

    def test_extract_content_no_content(self):
        """Test extracting when no full content is available"""
        collector = NewsCollector()

        # Mock feedparser entry with only summary
        entry = MagicMock()
        entry.summary = "This is a summary"
        entry.content = None

        content_raw, summary_raw = collector.extract_content(entry)

        assert summary_raw == "This is a summary"
        assert content_raw is None

    @patch("src.services.news_collector.feedparser.parse")
    def test_fetch_feed_success(self, mock_parse):
        """Test successfully fetching a feed"""
        collector = NewsCollector()

        # Mock RSS feed response
        mock_entry = MagicMock()
        mock_entry.get = MagicMock(side_effect=lambda key, default=None: {
            "title": "Test Article",
            "link": "https://example.com/article1"
        }.get(key, default))
        mock_entry.published_parsed = (2025, 1, 1, 10, 0, 0, 0, 1, 0)
        mock_entry.summary = "Article summary"
        mock_entry.content = None

        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [mock_entry]

        mock_parse.return_value = mock_feed

        feed = RSSFeed(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )

        articles = collector.fetch_feed(feed)

        assert len(articles) == 1
        assert articles[0].source == "Test Feed"
        assert articles[0].title == "Test Article"
        assert articles[0].url == "https://example.com/article1"
        assert articles[0].summary_raw == "Article summary"

    @patch("src.services.news_collector.feedparser.parse")
    def test_fetch_feed_skip_no_url(self, mock_parse):
        """Test skipping entries without URL"""
        collector = NewsCollector()

        # Mock RSS feed response with entry without URL
        mock_entry = MagicMock()
        mock_entry.title = "Test Article"
        mock_entry.get.return_value = ""  # No URL

        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [mock_entry]

        mock_parse.return_value = mock_feed

        feed = RSSFeed(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )

        articles = collector.fetch_feed(feed)

        assert len(articles) == 0

    @patch("src.services.news_collector.feedparser.parse")
    def test_fetch_feed_deduplication(self, mock_parse):
        """Test deduplication within a feed"""
        collector = NewsCollector()

        # Mock RSS feed with duplicate entries
        mock_entry_1 = MagicMock()
        mock_entry_1.get = MagicMock(side_effect=lambda key, default=None: {
            "title": "Test Article",
            "link": "https://example.com/article1"
        }.get(key, default))
        mock_entry_1.published_parsed = (2025, 1, 1, 10, 0, 0, 0, 1, 0)
        mock_entry_1.summary = "Summary"
        mock_entry_1.content = None

        mock_entry_2 = MagicMock()
        mock_entry_2.get = MagicMock(side_effect=lambda key, default=None: {
            "title": "Test Article (duplicate)",
            "link": "https://example.com/article1"  # Same URL
        }.get(key, default))
        mock_entry_2.published_parsed = (2025, 1, 1, 10, 0, 0, 0, 1, 0)
        mock_entry_2.summary = "Summary"
        mock_entry_2.content = None

        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [mock_entry_1, mock_entry_2]

        mock_parse.return_value = mock_feed

        feed = RSSFeed(
            name="Test Feed",
            url="https://example.com/feed.xml",
        )

        articles = collector.fetch_feed(feed)

        # Only one article should be returned (duplicate filtered)
        assert len(articles) == 1

    @patch("src.services.news_collector.NewsCollector.fetch_feed")
    def test_collect_all(self, mock_fetch_feed):
        """Test collecting from all feeds"""
        # Mock fetch_feed to return test articles
        mock_article = NewsArticle(
            news_id="news_20250101_abc123",
            source="Test Feed",
            title="Test Article",
            url="https://example.com/article",
            published_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            collected_at=datetime(2025, 1, 1, 10, 5, 0, tzinfo=timezone.utc),
        )

        mock_fetch_feed.return_value = [mock_article]

        collector = NewsCollector()
        articles = collector.collect_all()

        # Should call fetch_feed for each configured feed
        assert mock_fetch_feed.call_count == len(NewsCollector.RSS_FEEDS)

        # Should return articles from all feeds
        assert len(articles) == len(NewsCollector.RSS_FEEDS)


class TestCollectNews:
    """Test module-level collect_news function"""

    @patch("src.services.news_collector.NewsCollector.collect_all")
    def test_collect_news(self, mock_collect_all):
        """Test collect_news convenience function"""
        mock_article = NewsArticle(
            news_id="news_20250101_abc123",
            source="Test Feed",
            title="Test Article",
            url="https://example.com/article",
            published_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            collected_at=datetime(2025, 1, 1, 10, 5, 0, tzinfo=timezone.utc),
        )

        mock_collect_all.return_value = [mock_article]

        articles = collect_news()

        assert len(articles) == 1
        assert articles[0].title == "Test Article"
        mock_collect_all.assert_called_once()
