"""
Gemini Grounding with Google Search 動作確認スクリプト

このスクリプトは、Gemini APIのGrounding機能をテストし、
FX関連の最新ニュースを取得・分析できることを確認します。

実行前の準備:
1. GCPプロジェクトでVertex AI APIを有効化
2. サービスアカウントキーを取得し、GOOGLE_APPLICATION_CREDENTIALS環境変数に設定
3. 必要なパッケージをインストール: pip install google-genai

実行方法:
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
    export GCP_PROJECT_ID="your-project-id"
    python examples/test_gemini_grounding.py
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    HttpOptions,
    Tool,
)


class GeminiGroundingTester:
    """Gemini Grounding機能のテスター"""

    def __init__(self, project_id: str, location: str = "asia-northeast1"):
        """
        初期化

        Args:
            project_id: GCPプロジェクトID
            location: リージョン（デフォルト: asia-northeast1）
        """
        self.project_id = project_id
        self.location = location

        # Genai クライアント初期化
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
        )

        print(f"✅ Gemini Client initialized")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")

    def test_grounding_basic(self) -> Dict:
        """
        基本的なGrounding機能のテスト

        Returns:
            テスト結果の辞書
        """
        print("\n" + "=" * 60)
        print("TEST 1: 基本的なGrounding機能")
        print("=" * 60)

        try:
            # プロンプト
            prompt = """
            USD/JPYに影響する最新の経済ニュースを3件教えてください。
            各ニュースについて、以下の情報を含めてください:
            1. ニュースのタイトル
            2. 要約
            3. USD/JPYへの影響度（1-10のスコア）
            """

            print(f"\n📝 プロンプト: {prompt.strip()}")
            print("\n⏳ Gemini APIにリクエスト中...")

            # API呼び出し (Grounding機能を使用)
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=GenerateContentConfig(
                    tools=[Tool(google_search=GoogleSearch())],
                ),
            )

            print("\n✅ レスポンス受信成功")
            print("\n" + "-" * 60)
            print("AIの回答:")
            print("-" * 60)
            print(response.text)

            # Grounding Metadataの確認
            has_grounding = False
            if response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                    has_grounding = True
                    print("\n" + "-" * 60)
                    print("Grounding Metadata:")
                    print("-" * 60)
                    metadata = candidate.grounding_metadata

                    # 検索クエリ
                    if hasattr(metadata, "search_entry_point") and metadata.search_entry_point:
                        print(f"検索クエリ: {metadata.search_entry_point}")

                    # Web検索結果
                    if hasattr(metadata, "grounding_chunks") and metadata.grounding_chunks:
                        print(f"\n取得したソース数: {len(metadata.grounding_chunks)}")
                        for i, chunk in enumerate(metadata.grounding_chunks[:5], 1):
                            if hasattr(chunk, "web") and chunk.web:
                                print(f"  {i}. {chunk.web.uri}")
                                print(f"     タイトル: {chunk.web.title}")

            return {
                "status": "success",
                "response_text": response.text,
                "has_grounding": has_grounding,
            }

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            return {"status": "error", "error": str(e)}

    def test_fx_news_collection(self) -> Dict:
        """
        FXニュース収集のテスト（実用的なケース）

        Returns:
            テスト結果の辞書
        """
        print("\n" + "=" * 60)
        print("TEST 2: FXニュース収集（実用ケース）")
        print("=" * 60)

        try:
            # FX関連の検索クエリ（複数の観点）
            queries = [
                "USD/JPY latest news today",
                "Federal Reserve interest rate decision latest",
                "Japan economy FX market impact today",
            ]

            print(f"\n📝 検索クエリ:")
            for i, q in enumerate(queries, 1):
                print(f"   {i}. {q}")

            # プロンプト
            prompt = f"""
            以下の観点で、FX市場（特にUSD/JPY）に影響する最新ニュースを収集・分析してください:

            検索観点:
            {chr(10).join(f'- {q}' for q in queries)}

            各ニュースについて、以下の形式でJSON配列として出力してください:

            [
              {{
                "title": "ニュースのタイトル",
                "summary": "100文字程度の要約",
                "sentiment": -2から2の整数（Very Negative: -2, Negative: -1, Neutral: 0, Positive: 1, Very Positive: 2）,
                "impact_score": 1から10の整数（USD/JPYへの影響度）,
                "time_horizon": "immediate/short-term/medium-term/long-term",
                "source_url": "ソースURL"
              }}
            ]

            必ずJSON配列形式で出力してください。他のテキストは含めないでください。
            """

            print("\n⏳ Gemini APIにリクエスト中...")

            # API呼び出し (Grounding機能を使用)
            # 注: response_mime_typeとGroundingを同時に使うと問題が起きるため、
            #     プロンプトでJSON出力を指示する方式を採用
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=GenerateContentConfig(
                        tools=[Tool(google_search=GoogleSearch())],
                        temperature=0.2,
                    ),
                )
            except Exception as api_error:
                print(f"\n❌ API呼び出しエラー: {api_error}")
                print(f"エラータイプ: {type(api_error)}")
                import traceback
                traceback.print_exc()
                raise

            print("\n✅ レスポンス受信成功")
            print("\n" + "-" * 60)
            print("AIの回答 (JSON):")
            print("-" * 60)

            # レスポンスの内容を確認
            response_text = response.text if response.text else ""

            # candidatesから直接取得を試みる
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text = part.text

            # マークダウンのコードブロックを削除
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # ```json を削除
            elif response_text.startswith('```'):
                response_text = response_text[3:]  # ``` を削除
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # 末尾の ``` を削除
            response_text = response_text.strip()

            print(response_text)

            # JSONパース試行
            try:
                news_list = json.loads(response_text)
                print(f"\n✅ JSON パース成功: {len(news_list)}件のニュース")

                # 各ニュースを表示
                for i, news in enumerate(news_list, 1):
                    print(f"\n--- ニュース {i} ---")
                    print(f"タイトル: {news.get('title', 'N/A')}")
                    print(f"要約: {news.get('summary', 'N/A')}")
                    print(f"センチメント: {news.get('sentiment', 'N/A')}")
                    print(f"影響度: {news.get('impact_score', 'N/A')}/10")
                    print(f"時間軸: {news.get('time_horizon', 'N/A')}")
                    print(f"ソース: {news.get('source_url', 'N/A')}")

                return {
                    "status": "success",
                    "news_count": len(news_list),
                    "news_list": news_list,
                }

            except json.JSONDecodeError as e:
                print(f"\n⚠️ JSON パース失敗: {e}")
                print("生のレスポンステキストを確認してください")
                return {
                    "status": "partial_success",
                    "response_text": response.text,
                    "parse_error": str(e),
                }

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            return {"status": "error", "error": str(e)}

    def test_cost_estimation(self) -> Dict:
        """
        コスト試算のテスト

        Returns:
            コスト情報の辞書
        """
        print("\n" + "=" * 60)
        print("TEST 3: コスト試算")
        print("=" * 60)

        print("""
        Gemini 3 Flash料金:
        - 入力: $0.50 / 1M tokens
        - 出力: $3.00 / 1M tokens

        Grounding料金 (2026年1月5日〜):
        - 1,500検索/日まで無料
        - 以降: $35 / 1,000検索

        想定: 1日2回、各回3件のニュース検索

        月間コスト試算:
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        1. Gemini API利用料
           入力: 60回 × 2,000トークン × $0.50/1M = $0.06
           出力: 60回 × 1,000トークン × $3.00/1M = $0.18
           小計: $0.24 (約36円)

        2. Grounding料金
           60回/月 × 3検索 = 180検索/月
           → 1,500検索/日無料枠内 → $0

        合計: 約36円/月
        ━━━━━━━━━━━━━━━━━━━━━━━━━

        ※ 実際のトークン数はプロンプトとレスポンスの長さによって変動します
        """)

        return {
            "status": "info",
            "estimated_monthly_cost_usd": 0.24,
            "estimated_monthly_cost_jpy": 36,
        }


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("Gemini Grounding with Google Search - 動作確認")
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

    # テスター初期化
    tester = GeminiGroundingTester(project_id=project_id)

    # テスト実行
    results = []

    # TEST 1: 基本的なGrounding機能
    result1 = tester.test_grounding_basic()
    results.append(("基本的なGrounding機能", result1))

    # TEST 2: FXニュース収集
    result2 = tester.test_fx_news_collection()
    results.append(("FXニュース収集", result2))

    # TEST 3: コスト試算
    result3 = tester.test_cost_estimation()
    results.append(("コスト試算", result3))

    # サマリー表示
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    for test_name, result in results:
        status = result.get("status", "unknown")
        icon = "✅" if status == "success" else "⚠️" if status == "partial_success" else "❌"
        print(f"{icon} {test_name}: {status}")

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

    print("""
次のステップ:
1. テスト結果を確認し、Grounding機能の精度を評価
2. JSON出力の安定性を確認
3. 実際のコストを測定
4. RSS方式との比較検討

詳細は docs/design/GEMINI_GROUNDING_EVALUATION.md を参照してください。
    """)


if __name__ == "__main__":
    main()
