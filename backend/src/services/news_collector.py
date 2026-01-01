"""
RSS News Collector - Collects FX-related news from multiple sources
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Set
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from src.config import settings

logger = logging.getLogger(__name__)


class RSSFeed:
    """Configuration for an RSS feed source"""

    def __init__(
        self,
        name: str,
        url: str,
        language: str = "en",
        topics: Optional[List[str]] = None,
    ):
        self.name = name
        self.url = url
        self.language = language
        self.topics = topics or []


class NewsArticle:
    """Represents a raw news article before AI analysis"""

    def __init__(
        self,
        news_id: str,
        source: str,
        title: str,
        url: str,
        published_at: datetime,
        collected_at: datetime,
        content_raw: Optional[str] = None,
        summary_raw: Optional[str] = None,
    ):
        self.news_id = news_id
        self.source = source
        self.title = title
        self.url = url
        self.published_at = published_at
        self.collected_at = collected_at
        self.content_raw = content_raw
        self.summary_raw = summary_raw

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "news_id": self.news_id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "collected_at": self.collected_at,
            "content_raw": self.content_raw,
            "summary_raw": self.summary_raw,
        }


class NewsCollector:
    """Collects news from multiple RSS feeds with deduplication"""

    # RSS Feed configurations
    RSS_FEEDS = [
        RSSFeed(
            name="Reuters Business",
            url="https://www.reuters.com/business/finance/rss",
            language="en",
            topics=["finance", "economics"],
        ),
        RSSFeed(
            name="Bloomberg Markets",
            url="https://www.bloomberg.com/feed/podcast/etf-report.xml",
            language="en",
            topics=["markets", "finance"],
        ),
        RSSFeed(
            name="Yahoo Finance",
            url="https://finance.yahoo.com/news/rssindex",
            language="en",
            topics=["finance", "markets"],
        ),
    ]

    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_ids: Set[str] = set()
        logger.info("NewsCollector initialized")

    def generate_news_id(self, url: str, published_at: datetime) -> str:
        """
        Generate a unique ID for a news article based on URL and publish time

        Args:
            url: Article URL
            published_at: Publication datetime

        Returns:
            Unique news ID
        """
        # Create a hash from URL and timestamp
        content = f"{url}_{published_at.isoformat()}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:12]

        # Format: news_YYYYMMDD_HASH
        date_str = published_at.strftime("%Y%m%d")
        return f"news_{date_str}_{hash_digest}"

    def is_duplicate(self, news_id: str, url: str) -> bool:
        """
        Check if an article is a duplicate

        Args:
            news_id: Generated news ID
            url: Article URL

        Returns:
            True if duplicate, False otherwise
        """
        if news_id in self.seen_ids or url in self.seen_urls:
            logger.debug(f"Duplicate detected: {url}")
            return True

        self.seen_ids.add(news_id)
        self.seen_urls.add(url)
        return False

    def parse_published_date(self, entry: feedparser.FeedParserDict) -> Optional[datetime]:
        """
        Parse publication date from RSS entry

        Args:
            entry: feedparser entry

        Returns:
            Parsed datetime or None if parsing fails
        """
        try:
            # Try published_parsed first
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            # Fallback to updated_parsed
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            # If no parsed date available, use current time
            logger.warning(f"No parsed date for entry: {entry.get('title', 'Unknown')}")
            return datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"Failed to parse date: {e}")
            return datetime.now(timezone.utc)

    def extract_content(self, entry: feedparser.FeedParserDict) -> tuple[Optional[str], Optional[str]]:
        """
        Extract content and summary from RSS entry

        Args:
            entry: feedparser entry

        Returns:
            Tuple of (content_raw, summary_raw)
        """
        content_raw = None
        summary_raw = None

        # Extract summary
        if hasattr(entry, "summary") and entry.summary:
            summary_raw = entry.summary

        # Extract full content if available
        if hasattr(entry, "content") and entry.content:
            content_raw = entry.content[0].value if isinstance(entry.content, list) else entry.content

        return content_raw, summary_raw

    def fetch_feed(self, feed: RSSFeed) -> List[NewsArticle]:
        """
        Fetch articles from a single RSS feed

        Args:
            feed: RSSFeed configuration

        Returns:
            List of NewsArticle objects
        """
        articles = []
        collected_at = datetime.now(timezone.utc)

        try:
            logger.info(f"Fetching feed: {feed.name} ({feed.url})")

            # Parse RSS feed
            parsed_feed = feedparser.parse(feed.url)

            if parsed_feed.bozo:
                logger.warning(f"Feed parsing warning for {feed.name}: {parsed_feed.bozo_exception}")

            # Process each entry
            for entry in parsed_feed.entries:
                try:
                    # Extract basic information
                    title = entry.get("title", "No title")
                    url = entry.get("link", "")

                    if not url:
                        logger.warning(f"Entry without URL: {title}")
                        continue

                    # Parse publication date
                    published_at = self.parse_published_date(entry)

                    # Generate unique ID
                    news_id = self.generate_news_id(url, published_at)

                    # Check for duplicates
                    if self.is_duplicate(news_id, url):
                        continue

                    # Extract content
                    content_raw, summary_raw = self.extract_content(entry)

                    # Create NewsArticle
                    article = NewsArticle(
                        news_id=news_id,
                        source=feed.name,
                        title=title,
                        url=url,
                        published_at=published_at,
                        collected_at=collected_at,
                        content_raw=content_raw,
                        summary_raw=summary_raw,
                    )

                    articles.append(article)
                    logger.debug(f"Collected: {title[:50]}...")

                except Exception as e:
                    logger.error(f"Error processing entry from {feed.name}: {e}")
                    continue

            logger.info(f"Collected {len(articles)} articles from {feed.name}")

        except Exception as e:
            logger.error(f"Failed to fetch feed {feed.name}: {e}")

        return articles

    def collect_all(self) -> List[NewsArticle]:
        """
        Collect articles from all configured RSS feeds

        Returns:
            List of all collected NewsArticle objects
        """
        all_articles = []

        logger.info(f"Starting collection from {len(self.RSS_FEEDS)} feeds")

        for feed in self.RSS_FEEDS:
            articles = self.fetch_feed(feed)
            all_articles.extend(articles)

        logger.info(f"Total collected: {len(all_articles)} unique articles")

        return all_articles

    def reset_seen(self):
        """Reset the deduplication tracking (useful for testing)"""
        self.seen_urls.clear()
        self.seen_ids.clear()
        logger.info("Deduplication tracking reset")


# Module-level convenience function
def collect_news() -> List[NewsArticle]:
    """
    Convenience function to collect news articles

    Returns:
        List of collected NewsArticle objects
    """
    collector = NewsCollector()
    return collector.collect_all()


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Test the collector
    articles = collect_news()

    print(f"\n{'='*60}")
    print(f"Collected {len(articles)} articles")
    print(f"{'='*60}\n")

    # Display first 5 articles
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. [{article.source}] {article.title}")
        print(f"   URL: {article.url}")
        print(f"   Published: {article.published_at}")
        print(f"   ID: {article.news_id}")
        print()
