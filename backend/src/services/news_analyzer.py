"""
Gemini Grounding News Analyzer

Gemini Grounding with Google Searchを使用してFX関連ニュースを収集・分析するサービス
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)
from google.api_core import exceptions as google_exceptions

from src.config import settings

logger = logging.getLogger(__name__)


class NewsAnalyzerError(Exception):
    """NewsAnalyzer基底例外クラス"""

    pass


class APIError(NewsAnalyzerError):
    """Gemini API呼び出しエラー"""

    pass


class JSONParseError(NewsAnalyzerError):
    """JSON解析エラー"""

    pass


class ValidationError(NewsAnalyzerError):
    """データ検証エラー"""

    pass


class NewsAnalysisResult:
    """ニュース分析結果"""

    def __init__(
        self,
        title: str,
        summary: str,
        sentiment: int,
        impact_usd_jpy: int,
        impact_eur_jpy: int,
        time_horizon: str,
        source_url: str,
        rationale: str,
        analyzed_at: datetime,
    ):
        self.title = title
        self.summary = summary
        self.sentiment = sentiment
        self.impact_usd_jpy = impact_usd_jpy
        self.impact_eur_jpy = impact_eur_jpy
        self.time_horizon = time_horizon
        self.source_url = source_url
        self.rationale = rationale
        self.analyzed_at = analyzed_at

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "title": self.title,
            "summary": self.summary,
            "sentiment": self.sentiment,
            "impact_usd_jpy": self.impact_usd_jpy,
            "impact_eur_jpy": self.impact_eur_jpy,
            "time_horizon": self.time_horizon,
            "source_url": self.source_url,
            "rationale": self.rationale,
            "analyzed_at": self.analyzed_at,
        }


class NewsAnalyzer:
    """Gemini Groundingを使用したニュース分析サービス"""

    # センチメント分析基準
    SENTIMENT_GUIDELINES = """
センチメントスコア基準（-2〜2の5段階）:
- -2 (Very Negative): 大幅な円高要因（例: 日銀の大幅利上げ、米国景気後退懸念）
- -1 (Negative): 円高要因（例: 日銀のタカ派発言、米国株式市場の急落）
- 0 (Neutral): 影響が不明確、または相反する要因が混在
- +1 (Positive): 円安要因（例: 日米金利差拡大、米国経済指標好調）
- +2 (Very Positive): 大幅な円安要因（例: 日銀の大幅緩和、FRBの大幅利上げ）

注: 円安=プラス、円高=マイナスとして評価
"""

    # 影響度評価基準
    IMPACT_GUIDELINES = """
影響度スコア基準（1〜5の5段階、通貨ペア別に評価）:

USD/JPY への影響度:
- 5 (Very High): 米FOMC決定、米雇用統計、日銀金融政策決定会合
- 4 (High): 米CPI/PPI、米GDP、FRB議長発言、日銀総裁発言
- 3 (Medium): 米小売売上高、米ISM指数、日本GDP、日本インフレ率
- 2 (Low): 地区連銀総裁発言、日銀審議委員発言、その他経済指標
- 1 (Very Low): アナリストコメント、市場予測レポート

EUR/JPY への影響度:
- 5 (Very High): ECB政策決定、ユーロ圏GDP、ECB総裁発言、日銀金融政策決定会合
- 4 (High): ユーロ圏CPI、ドイツ経済指標、ECB理事発言、日銀総裁発言
- 3 (Medium): ユーロ圏PMI、フランス・イタリア経済指標、日本GDP
- 2 (Low): 個別国の政治動向、その他経済指標
- 1 (Very Low): アナリストコメント、市場予測レポート

注: ニュースが主にどの地域・通貨に関連するかを考慮して評価
"""

    # 時間軸の定義
    TIME_HORIZON_GUIDELINES = """
時間軸の判定基準:
- immediate: 数時間以内に影響（例: 重要経済指標の発表直後）
- short-term: 数日〜2週間程度の影響（例: 中央銀行の政策決定）
- medium-term: 2週間〜3ヶ月程度の影響（例: 金融政策の方向性変更）
- long-term: 3ヶ月以上の影響（例: 構造的な経済トレンド変化）
"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "asia-northeast1",
        model: str = "gemini-2.5-flash",
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 120,
    ):
        """
        初期化

        Args:
            project_id: GCPプロジェクトID（省略時は設定から取得）
            location: リージョン
            model: 使用するGeminiモデル
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
            timeout: APIタイムアウト（秒）
        """
        self.project_id = project_id or settings.gcp_project_id
        self.location = location
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # Gemini クライアント初期化
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location,
        )

        logger.info(
            f"NewsAnalyzer initialized (project={self.project_id}, "
            f"location={self.location}, model={self.model}, "
            f"max_retries={self.max_retries}, timeout={self.timeout}s)"
        )

    def _build_prompt(self, query: str, news_count: int = 5) -> str:
        """
        プロンプトを構築

        Args:
            query: 検索クエリ
            news_count: 取得するニュース件数

        Returns:
            構築されたプロンプト
        """
        return f"""
あなたはFX市場の専門アナリストです。以下のクエリに基づいて、最新のニュースを{news_count}件収集し、
USD/JPYとEUR/JPYの為替レートへの影響を分析してください。

【検索クエリ】
{query}

【分析基準】

{self.SENTIMENT_GUIDELINES}

{self.IMPACT_GUIDELINES}

{self.TIME_HORIZON_GUIDELINES}

【出力形式】
以下のJSON配列形式で出力してください。マークダウンのコードブロック(```)は使用せず、JSON配列のみを出力してください:

[
  {{
    "title": "ニュースタイトル",
    "summary": "50-100文字の日本語要約",
    "sentiment": -2から2の整数,
    "impact": {{
      "usd_jpy": 1から5の整数,
      "eur_jpy": 1から5の整数
    }},
    "time_horizon": "immediate" | "short-term" | "medium-term" | "long-term",
    "source_url": "ニュースソースのURL",
    "rationale": "判断理由（100文字程度）"
  }}
]

重要:
- 必ず{news_count}件のニュースを返してください
- すべてのフィールドは必須です
- JSON配列のみを出力し、他の説明文は含めないでください
- sentimentとimpactの値は必ず指定された範囲内にしてください
"""

    def _clean_json_response(self, response_text: str) -> str:
        """
        Geminiのレスポンスからマークダウンコードブロックを削除

        Args:
            response_text: Geminiのレスポンステキスト

        Returns:
            クリーニングされたJSONテキスト
        """
        # マークダウンのコードブロックを削除
        cleaned = re.sub(r"```json\s*", "", response_text)
        cleaned = re.sub(r"```\s*", "", cleaned)
        return cleaned.strip()

    def _call_gemini_api(self, prompt: str) -> str:
        """
        Gemini APIを呼び出し（リトライ付き）

        Args:
            prompt: プロンプト

        Returns:
            APIレスポンステキスト

        Raises:
            APIError: API呼び出しに失敗した場合
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling Gemini API (attempt {attempt + 1}/{self.max_retries})..."
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=GenerateContentConfig(
                        tools=[Tool(google_search=GoogleSearch())],
                        temperature=0.2,
                    ),
                )

                response_text = response.text
                logger.debug(f"Received response: {len(response_text)} characters")
                return response_text

            except google_exceptions.DeadlineExceeded as e:
                last_error = e
                logger.warning(
                    f"API timeout (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                raise APIError(f"API timeout after {self.max_retries} attempts") from e

            except google_exceptions.ResourceExhausted as e:
                last_error = e
                logger.warning(
                    f"Rate limit exceeded (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1) * 2)  # Longer backoff
                    continue
                raise APIError(
                    f"Rate limit exceeded after {self.max_retries} attempts"
                ) from e

            except google_exceptions.ServiceUnavailable as e:
                last_error = e
                logger.warning(
                    f"Service unavailable (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise APIError(
                    f"Service unavailable after {self.max_retries} attempts"
                ) from e

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected API error: {e}")
                raise APIError(f"API call failed: {e}") from e

        # Should not reach here
        raise APIError(f"API call failed after {self.max_retries} attempts") from last_error

    def _parse_json_response(self, response_text: str) -> List[Dict]:
        """
        JSONレスポンスを解析

        Args:
            response_text: Geminiのレスポンステキスト

        Returns:
            解析されたニュースリスト

        Raises:
            JSONParseError: JSON解析に失敗した場合
        """
        # JSONクリーニング
        cleaned_text = self._clean_json_response(response_text)

        try:
            news_list = json.loads(cleaned_text)

            # リストであることを確認
            if not isinstance(news_list, list):
                raise JSONParseError(
                    f"Expected JSON array, got {type(news_list).__name__}"
                )

            logger.debug(f"Successfully parsed {len(news_list)} news items from JSON")
            return news_list

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Cleaned response text (first 500 chars): {cleaned_text[:500]}")
            raise JSONParseError(f"Failed to parse JSON response: {e}") from e

    def _validate_and_convert_news_item(
        self, news_item: Dict, analyzed_at: datetime
    ) -> Optional[NewsAnalysisResult]:
        """
        ニュースアイテムを検証してNewsAnalysisResultに変換

        Args:
            news_item: ニュースアイテムの辞書
            analyzed_at: 分析日時

        Returns:
            NewsAnalysisResult またはNone（検証失敗時）
        """
        required_fields = [
            "title",
            "summary",
            "sentiment",
            "impact",
            "time_horizon",
            "source_url",
            "rationale",
        ]

        # 必須フィールドチェック
        missing_fields = [field for field in required_fields if field not in news_item]
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return None

        # impactの構造チェック
        if not isinstance(news_item["impact"], dict):
            logger.warning("'impact' field is not a dictionary")
            return None

        if "usd_jpy" not in news_item["impact"] or "eur_jpy" not in news_item["impact"]:
            logger.warning("Missing usd_jpy or eur_jpy in impact field")
            return None

        try:
            result = NewsAnalysisResult(
                title=news_item["title"],
                summary=news_item["summary"],
                sentiment=int(news_item["sentiment"]),
                impact_usd_jpy=int(news_item["impact"]["usd_jpy"]),
                impact_eur_jpy=int(news_item["impact"]["eur_jpy"]),
                time_horizon=news_item["time_horizon"],
                source_url=news_item["source_url"],
                rationale=news_item["rationale"],
                analyzed_at=analyzed_at,
            )

            # 値の範囲チェック
            if not (-2 <= result.sentiment <= 2):
                logger.warning(f"Sentiment out of range: {result.sentiment}")
                return None

            if not (1 <= result.impact_usd_jpy <= 5):
                logger.warning(f"USD/JPY impact out of range: {result.impact_usd_jpy}")
                return None

            if not (1 <= result.impact_eur_jpy <= 5):
                logger.warning(f"EUR/JPY impact out of range: {result.impact_eur_jpy}")
                return None

            return result

        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to convert news item: {e}")
            return None

    def analyze_news(
        self, query: str = "USD/JPY EUR/JPY 為替 最新ニュース", news_count: int = 5
    ) -> List[NewsAnalysisResult]:
        """
        ニュースを収集・分析（エラーハンドリング・リトライ付き）

        Args:
            query: 検索クエリ
            news_count: 取得するニュース件数

        Returns:
            分析結果のリスト

        Raises:
            APIError: API呼び出しに失敗した場合
            JSONParseError: JSON解析に失敗した場合
            ValidationError: データ検証に失敗した場合
        """
        logger.info(f"Starting news analysis (query='{query}', count={news_count})")

        try:
            # プロンプト構築
            prompt = self._build_prompt(query, news_count)

            # Gemini API呼び出し（リトライ付き）
            response_text = self._call_gemini_api(prompt)

            # JSON解析
            news_list = self._parse_json_response(response_text)

            # NewsAnalysisResultオブジェクトに変換
            results = []
            analyzed_at = datetime.now(timezone.utc)

            for i, news_item in enumerate(news_list, 1):
                result = self._validate_and_convert_news_item(news_item, analyzed_at)
                if result:
                    results.append(result)
                else:
                    logger.warning(f"Skipped news item {i} due to validation failure")

            if not results:
                raise ValidationError("No valid news items were extracted from response")

            logger.info(
                f"Successfully analyzed {len(results)}/{len(news_list)} news items"
            )
            return results

        except (APIError, JSONParseError, ValidationError):
            # すでにログ出力済みなので再スロー
            raise

        except Exception as e:
            logger.error(f"Unexpected error during news analysis: {e}")
            raise NewsAnalyzerError(f"News analysis failed: {e}") from e


def analyze_fx_news(news_count: int = 5) -> List[NewsAnalysisResult]:
    """
    FXニュースを分析する便利関数

    Args:
        news_count: 取得するニュース件数

    Returns:
        分析結果のリスト
    """
    analyzer = NewsAnalyzer()
    return analyzer.analyze_news(news_count=news_count)


if __name__ == "__main__":
    # スタンドアロン実行用
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("FX News Analyzer - Gemini Grounding")
    print("=" * 60)

    try:
        results = analyze_fx_news(news_count=3)

        print(f"\n取得したニュース: {len(results)}件\n")

        for i, result in enumerate(results, 1):
            print(f"【ニュース {i}】")
            print(f"タイトル: {result.title}")
            print(f"要約: {result.summary}")
            print(f"センチメント: {result.sentiment}")
            print(f"影響度 (USD/JPY): {result.impact_usd_jpy}/5")
            print(f"影響度 (EUR/JPY): {result.impact_eur_jpy}/5")
            print(f"時間軸: {result.time_horizon}")
            print(f"URL: {result.source_url}")
            print(f"理由: {result.rationale}")
            print()

    except Exception as e:
        print(f"エラー: {e}")
        import traceback

        traceback.print_exc()
