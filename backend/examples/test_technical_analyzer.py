"""
Technical Analyzer Test Script

テクニカル指標計算機能のテストスクリプト
MA、RSI、MACDの計算を確認します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.technical_analyzer import TechnicalAnalyzer


def test_single_indicator():
    """TEST 1: 単一通貨ペアのテクニカル指標"""
    print("\n" + "=" * 60)
    print("TEST 1: 単一通貨ペアのテクニカル指標（USD/JPY）")
    print("=" * 60)

    try:
        analyzer = TechnicalAnalyzer()

        # USD/JPYのテクニカル指標を取得
        indicators = analyzer.get_indicators(
            symbol="USD_JPY", interval="1hour", days=7
        )

        print(f"\n✅ テクニカル指標計算成功")
        print(f"\n📊 基本情報:")
        print(f"  通貨ペア: {indicators['symbol']}")
        print(f"  時間足: {indicators['interval']}")
        print(f"  データ数: {indicators['data_count']} 本")
        print(f"  最新価格: {indicators['latest_price']:.3f}")

        print(f"\n📈 移動平均（MA）:")
        print(f"  MA20: {indicators['ma']['ma20']:.3f}")
        print(f"  MA50: {indicators['ma']['ma50']:.3f}")
        print(f"  MA20 > MA50: {indicators['ma']['ma20_above_ma50']}")

        print(f"\n📉 RSI:")
        print(f"  RSI(14): {indicators['rsi']['rsi']:.2f}")
        print(f"  買われすぎ (≥70): {indicators['rsi']['overbought']}")
        print(f"  売られすぎ (≤30): {indicators['rsi']['oversold']}")

        print(f"\n🔄 MACD:")
        print(f"  MACD: {indicators['macd']['macd']:.4f}")
        print(f"  Signal: {indicators['macd']['macd_signal']:.4f}")
        print(f"  Histogram: {indicators['macd']['macd_histogram']:.4f}")
        print(f"  強気クロスオーバー: {indicators['macd']['bullish_crossover']}")
        print(f"  弱気クロスオーバー: {indicators['macd']['bearish_crossover']}")

        print(f"\n🎯 判定:")
        print(f"  トレンド: {indicators['trend'].upper()}")
        print(f"  モメンタム: {indicators['momentum'].upper()}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_multiple_indicators():
    """TEST 2: 複数通貨ペアのテクニカル指標"""
    print("\n" + "=" * 60)
    print("TEST 2: 複数通貨ペアのテクニカル指標")
    print("=" * 60)

    try:
        analyzer = TechnicalAnalyzer()

        # 複数通貨ペアを取得
        symbols = ["USD_JPY", "EUR_JPY"]
        indicators_dict = analyzer.get_multiple_indicators(symbols, interval="1hour", days=7)

        print(f"\n✅ 複数通貨ペア取得成功")

        for symbol, indicators in indicators_dict.items():
            if "error" in indicators:
                print(f"\n❌ {symbol}: {indicators['error']}")
                continue

            print(f"\n📌 {symbol}")
            print(f"  最新価格: {indicators['latest_price']:.3f}")
            print(f"  トレンド: {indicators['trend'].upper()}")
            print(f"  モメンタム: {indicators['momentum'].upper()}")
            print(f"  RSI: {indicators['rsi']['rsi']:.2f}")
            print(f"  MA20 > MA50: {indicators['ma']['ma20_above_ma50']}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_signal_interpretation():
    """TEST 3: シグナル解釈"""
    print("\n" + "=" * 60)
    print("TEST 3: シグナル解釈（トレード推奨）")
    print("=" * 60)

    try:
        analyzer = TechnicalAnalyzer()

        # テクニカル指標取得
        indicators = analyzer.get_indicators("USD_JPY", interval="1hour", days=7)

        print(f"\n📊 {indicators['symbol']} - テクニカル分析結果")
        print(f"  最新価格: {indicators['latest_price']:.3f}")

        # シグナル解釈
        print(f"\n🎯 シグナル解釈:")

        # トレンド
        if indicators["trend"] == "up":
            print(f"  ✅ 上昇トレンド（MA20 > MA50）")
        else:
            print(f"  ⚠️ 下降トレンド（MA20 < MA50）")

        # RSI
        rsi = indicators["rsi"]["rsi"]
        if indicators["rsi"]["overbought"]:
            print(f"  ⚠️ RSI 買われすぎ ({rsi:.2f} ≥ 70) - 売りシグナル")
        elif indicators["rsi"]["oversold"]:
            print(f"  ✅ RSI 売られすぎ ({rsi:.2f} ≤ 30) - 買いシグナル")
        else:
            print(f"  ➖ RSI 中立 ({rsi:.2f})")

        # MACD
        if indicators["macd"]["bullish_crossover"]:
            print(f"  ✅ MACD 強気クロスオーバー - 買いシグナル")
        elif indicators["macd"]["bearish_crossover"]:
            print(f"  ⚠️ MACD 弱気クロスオーバー - 売りシグナル")
        else:
            macd_hist = indicators["macd"]["macd_histogram"]
            if macd_hist > 0:
                print(f"  ✅ MACD ヒストグラム > 0 ({macd_hist:.4f}) - 上昇継続")
            else:
                print(f"  ⚠️ MACD ヒストグラム < 0 ({macd_hist:.4f}) - 下降継続")

        # 総合判定
        print(f"\n💡 総合判定:")
        print(f"  トレンド: {indicators['trend'].upper()}")
        print(f"  モメンタム: {indicators['momentum'].upper()}")

        if indicators["trend"] == "up" and indicators["momentum"] == "bullish":
            print(f"  🟢 推奨: 買い（強気）")
        elif indicators["trend"] == "down" and indicators["momentum"] == "bearish":
            print(f"  🔴 推奨: 売り（弱気）")
        else:
            print(f"  🟡 推奨: 様子見（中立）")

        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メイン実行"""
    print("=" * 60)
    print("Technical Analyzer Test")
    print("=" * 60)
    print("\nテクニカル指標（MA, RSI, MACD）の計算をテストします。")
    print("GMOコインAPIから実際のデータを取得します。")
    print("\n" + "=" * 60)

    results = []

    # TEST 1: 単一通貨ペア
    results.append(("TEST 1: 単一通貨ペア", test_single_indicator()))

    # TEST 2: 複数通貨ペア
    results.append(("TEST 2: 複数通貨ペア", test_multiple_indicators()))

    # TEST 3: シグナル解釈
    results.append(("TEST 3: シグナル解釈", test_signal_interpretation()))

    # 結果サマリー
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n結果: {passed}/{total} テスト成功")
    print("=" * 60)


if __name__ == "__main__":
    main()
