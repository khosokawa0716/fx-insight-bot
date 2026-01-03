"""
RSS + Gemini分析 動作確認スクリプト

このスクリプトは、既存のRSS News Collectorで取得したニュースを
Gemini 3 Flashで分析する機能をテストします。

実行前の準備:
1. GCPプロジェクトでVertex AI APIを有効化
2. サービスアカウントキーを取得し、GOOGLE_APPLICATION_CREDENTIALS環境変数に設定
3. 必要なパッケージをインストール:
   pip install google-cloud-aiplatform feedparser requests beautifulsoup4

実行方法:
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
    export GCP_PROJECT_ID="your-project-id"
    python examples/test_rss_gemini_analysis.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import vertexai
from vertexai.generative_models import GenerativeModel

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.news_collector import NewsArticle, NewsCollector


class GeminiNewsAnalyzer:
    """Gemini 3 Flashを使ったニュース分析"""

    def __init__(self, project_id: str, location: str = "asia-northeast1"):
        """
        初期化

        Args:
            project_id: GCPプロジェクトID
            location: リージョン（デフォルト: asia-northeast1）
        """
        self.project_id = project_id
        self.location = location

        # Vertex AI初期化
        vertexai.init(project=project_id, location=location)

        # モデル初期化
        self.model = GenerativeModel("gemini-3-flash")

        print(f"✅ Gemini News Analyzer initialized")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")
        print(f"   Model: gemini-3-flash")

    def analyze_news(self, article: NewsArticle) -> Dict:
        """
        単一のニュース記事を分析

        Args:
            article: 分析対象のニュース記事

        Returns:
            分析結果の辞書
        """
        # プロンプト作成
        prompt = f"""
        以下のニュース記事を分析し、FX市場（特にUSD/JPYとEUR/USD）への影響を評価してください。

        【ニュース情報】
        タイトル: {article.title}
        ソース: {article.source}
        公開日: {article.published_at}
        URL: {article.url}

        要約: {article.summary_raw or "（要約なし）"}

        【分析タスク】
        1. センチメント分析: このニュースの市場心理への影響を評価
        2. 影響度評価: USD/JPYとEUR/USDへの影響の強さを評価
        3. 時間軸判定: 影響が現れる時間軸を判定
        4. 要約: 50-100文字で要約

        【出力形式】
        以下のJSON形式で出力してください。他のテキストは含めないでください:

        {{
          "sentiment": -2から2の整数（Very Negative: -2, Negative: -1, Neutral: 0, Positive: 1, Very Positive: 2）,
          "impact_usd_jpy": 1から10の整数,
          "impact_eur_usd": 1から10の整数,
          "time_horizon": "immediate" | "short-term" | "medium-term" | "long-term",
          "summary_ja": "日本語の要約（50-100文字）",
          "rationale": "判断理由（100文字程度）"
        }}
        """

        try:
            # API呼び出し
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                },
            )

            # JSONパース
            analysis = json.loads(response.text)

            return {
                "status": "success",
                "news_id": article.news_id,
                "title": article.title,
                "analysis": analysis,
            }

        except json.JSONDecodeError as e:
            return {
                "status": "parse_error",
                "news_id": article.news_id,
                "title": article.title,
                "error": str(e),
                "raw_response": response.text,
            }

        except Exception as e:
            return {
                "status": "error",
                "news_id": article.news_id,
                "title": article.title,
                "error": str(e),
            }

    def analyze_multiple_news(self, articles: List[NewsArticle], max_count: int = 5) -> List[Dict]:
        """
        複数のニュース記事を分析

        Args:
            articles: 分析対象のニュース記事リスト
            max_count: 分析する最大件数

        Returns:
            分析結果のリスト
        """
        results = []

        for i, article in enumerate(articles[:max_count], 1):
            print(f"\n{'='*60}")
            print(f"ニュース {i}/{min(len(articles), max_count)} を分析中")
            print(f"{'='*60}")
            print(f"タイトル: {article.title}")
            print(f"ソース: {article.source}")
            print(f"URL: {article.url}")

            result = self.analyze_news(article)
            results.append(result)

            if result["status"] == "success":
                print(f"\n✅ 分析成功")
                analysis = result["analysis"]
                print(f"   センチメント: {analysis.get('sentiment', 'N/A')}")
                print(f"   USD/JPY影響度: {analysis.get('impact_usd_jpy', 'N/A')}/10")
                print(f"   EUR/USD影響度: {analysis.get('impact_eur_usd', 'N/A')}/10")
                print(f"   時間軸: {analysis.get('time_horizon', 'N/A')}")
                print(f"   要約: {analysis.get('summary_ja', 'N/A')}")
            else:
                print(f"\n❌ 分析失敗: {result.get('error', 'Unknown error')}")

        return results


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("RSS + Gemini 3 Flash分析 - 動作確認")
    print("=" * 60)

    # 環境変数チェック
    project_id = os.getenv("GCP_PROJECT_ID")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not project_id:
        print("❌ エラー: GCP_PROJECT_ID環境変数が設定されていません")
        print("\n設定方法:")
        print('  export GCP_PROJECT_ID="your-project-id"')
        return

    if not credentials_path:
        print("❌ エラー: GOOGLE_APPLICATION_CREDENTIALS環境変数が設定されていません")
        print("\n設定方法:")
        print('  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"')
        return

    print(f"\n✅ 環境変数チェック完了")
    print(f"   GCP_PROJECT_ID: {project_id}")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")

    # Step 1: RSSニュース収集
    print("\n" + "=" * 60)
    print("STEP 1: RSSからニュース収集")
    print("=" * 60)

    collector = NewsCollector()
    articles = collector.collect_all()

    print(f"\n✅ 収集完了: {len(articles)}件のニュース")

    if len(articles) == 0:
        print("\n⚠️ ニュースが取得できませんでした")
        print("RSSフィードのURLを確認してください")
        return

    # 最初の3件を表示
    print(f"\n取得したニュース（最初の3件）:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n{i}. [{article.source}] {article.title}")
        print(f"   URL: {article.url}")
        print(f"   公開日: {article.published_at}")

    # Step 2: Gemini分析
    print("\n" + "=" * 60)
    print("STEP 2: Gemini 3 Flashで分析")
    print("=" * 60)

    analyzer = GeminiNewsAnalyzer(project_id=project_id)

    # 最大5件を分析
    max_analysis_count = min(5, len(articles))
    print(f"\n{max_analysis_count}件のニュースを分析します...")

    results = analyzer.analyze_multiple_news(articles, max_count=max_analysis_count)

    # Step 3: 結果サマリー
    print("\n" + "=" * 60)
    print("STEP 3: 分析結果サマリー")
    print("=" * 60)

    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    parse_error_count = sum(1 for r in results if r["status"] == "parse_error")

    print(f"\n分析件数: {len(results)}件")
    print(f"  ✅ 成功: {success_count}件")
    print(f"  ⚠️ パースエラー: {parse_error_count}件")
    print(f"  ❌ その他エラー: {error_count}件")

    # 成功した分析結果を詳細表示
    if success_count > 0:
        print("\n" + "-" * 60)
        print("分析結果詳細:")
        print("-" * 60)

        for i, result in enumerate([r for r in results if r["status"] == "success"], 1):
            analysis = result["analysis"]
            print(f"\n【ニュース {i}】")
            print(f"タイトル: {result['title']}")
            print(f"  センチメント: {analysis.get('sentiment', 'N/A')}")
            print(f"  USD/JPY影響: {analysis.get('impact_usd_jpy', 'N/A')}/10")
            print(f"  EUR/USD影響: {analysis.get('impact_eur_usd', 'N/A')}/10")
            print(f"  時間軸: {analysis.get('time_horizon', 'N/A')}")
            print(f"  要約: {analysis.get('summary_ja', 'N/A')}")
            print(f"  理由: {analysis.get('rationale', 'N/A')}")

    # コスト試算
    print("\n" + "=" * 60)
    print("コスト試算")
    print("=" * 60)

    avg_input_tokens = 1500  # 想定
    avg_output_tokens = 500  # 想定

    print(f"""
    Gemini 3 Flash料金:
    - 入力: $0.50 / 1M tokens
    - 出力: $3.00 / 1M tokens

    今回の分析:
    - 分析件数: {len(results)}件
    - 想定入力トークン: {avg_input_tokens * len(results):,} tokens
    - 想定出力トークン: {avg_output_tokens * len(results):,} tokens

    想定コスト:
    - 入力: ${(avg_input_tokens * len(results)) / 1_000_000 * 0.50:.4f}
    - 出力: ${(avg_output_tokens * len(results)) / 1_000_000 * 3.00:.4f}
    - 合計: ${((avg_input_tokens * len(results)) / 1_000_000 * 0.50 + (avg_output_tokens * len(results)) / 1_000_000 * 3.00):.4f}
    - 合計(円): 約{((avg_input_tokens * len(results)) / 1_000_000 * 0.50 + (avg_output_tokens * len(results)) / 1_000_000 * 3.00) * 150:.2f}円

    月間想定（60記事/月）:
    - 月額コスト: 約{((avg_input_tokens * 60) / 1_000_000 * 0.50 + (avg_output_tokens * 60) / 1_000_000 * 3.00) * 150:.2f}円
    """)

    # 次のステップ
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

    print(f"""
テスト結果:
  ✅ RSS収集: {len(articles)}件
  ✅ Gemini分析: {success_count}/{len(results)}件成功

次のステップ:
1. JSON出力の安定性を確認（パースエラー率: {parse_error_count}/{len(results)}）
2. センチメント分析の精度を評価
3. プロンプトのチューニング
4. Firestoreへの保存機能実装

詳細は docs/design/GEMINI_GROUNDING_EVALUATION.md を参照してください。
    """)


if __name__ == "__main__":
    main()
