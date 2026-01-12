"""
Rule Engine Test Script

ルールエンジンのテストスクリプト
ニュース分析とテクニカル指標を統合してトレードシグナルを生成します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.rule_engine import RuleEngine


def test_single_signal():
    """TEST 1: 単一通貨ペアのシグナル生成"""
    print("\n" + "=" * 60)
    print("TEST 1: 単一通貨ペアのシグナル生成（USD/JPY）")
    print("=" * 60)

    try:
        engine = RuleEngine()

        # USD/JPYのシグナル生成
        signal = engine.generate_signal(
            symbol="USD_JPY", interval="1hour", days=7, lookback_hours=24
        )

        print(f"\n✅ シグナル生成成功")
        print(f"\n📊 基本情報:")
        print(f"  通貨ペア: {signal['symbol']}")
        print(f"  シグナル: {signal['signal'].upper()}")
        print(f"  信頼度: {signal['confidence']:.2%}")
        print(f"  タイムスタンプ: {signal['timestamp']}")

        print(f"\n📈 テクニカル分析:")
        tech = signal["technical"]
        print(f"  トレンド: {tech['trend'].upper()}")
        print(f"  モメンタム: {tech['momentum'].upper()}")
        print(f"  最新価格: {tech['latest_price']:.3f}")
        print(f"  MA20: {tech['ma']['ma20']:.3f}")
        print(f"  MA50: {tech['ma']['ma50']:.3f}")
        print(f"  RSI: {tech['rsi']['rsi']:.2f}")
        print(f"  MACD Histogram: {tech['macd']['macd_histogram']:.4f}")

        print(f"\n📰 ニュース分析:")
        news = signal["news_summary"]
        print(f"  ニュース数: {news['count']} 件")
        print(f"  平均センチメント: {news['avg_sentiment']:.2f}")
        print(f"  平均インパクト: {news['avg_impact']:.1f}/5")
        print(f"  強気ニュース: {news['bullish_count']} 件")
        print(f"  弱気ニュース: {news['bearish_count']} 件")
        print(f"  中立ニュース: {news['neutral_count']} 件")

        if news["signals"]:
            print(f"  シグナル分布:")
            for sig, count in news["signals"].items():
                print(f"    - {sig}: {count} 件")

        print(f"\n🎯 判定理由:")
        print(f"  {signal['reason']}")

        # シグナル推奨アクション
        print(f"\n💡 推奨アクション:")
        if signal["signal"] == "buy":
            if signal["confidence"] >= 0.7:
                print(f"  🟢 強い買いシグナル（信頼度: {signal['confidence']:.0%}）")
            else:
                print(f"  🟡 買いシグナル（信頼度: {signal['confidence']:.0%}）- 慎重に")
        elif signal["signal"] == "sell":
            if signal["confidence"] >= 0.7:
                print(f"  🔴 強い売りシグナル（信頼度: {signal['confidence']:.0%}）")
            else:
                print(f"  🟡 売りシグナル（信頼度: {signal['confidence']:.0%}）- 慎重に")
        else:
            print(f"  ⚪ 様子見（信頼度: {signal['confidence']:.0%}）")

        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_multiple_signals():
    """TEST 2: 複数通貨ペアのシグナル生成"""
    print("\n" + "=" * 60)
    print("TEST 2: 複数通貨ペアのシグナル生成")
    print("=" * 60)

    try:
        engine = RuleEngine()

        # 複数通貨ペアのシグナル生成
        symbols = ["USD_JPY", "EUR_JPY"]
        signals = engine.generate_multiple_signals(
            symbols=symbols, interval="1hour", lookback_hours=24
        )

        print(f"\n✅ 複数シグナル生成成功")

        for symbol, signal in signals.items():
            if "error" in signal:
                print(f"\n❌ {symbol}: {signal['error']}")
                continue

            print(f"\n📌 {symbol}")
            print(f"  シグナル: {signal['signal'].upper()}")
            print(f"  信頼度: {signal['confidence']:.0%}")
            print(f"  トレンド: {signal['technical']['trend'].upper()}")
            print(f"  モメンタム: {signal['technical']['momentum'].upper()}")
            print(f"  ニュース数: {signal['news_summary']['count']} 件")
            print(f"  平均センチメント: {signal['news_summary']['avg_sentiment']:.2f}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_signal_comparison():
    """TEST 3: シグナル比較（異なる条件）"""
    print("\n" + "=" * 60)
    print("TEST 3: シグナル比較（ニュース取得期間の違い）")
    print("=" * 60)

    try:
        engine = RuleEngine()

        # 24時間 vs 72時間のニュース取得期間
        lookback_periods = [24, 72]

        print(f"\n📊 USD/JPY - ニュース取得期間による違い:")

        for hours in lookback_periods:
            signal = engine.generate_signal(
                symbol="USD_JPY", interval="1hour", days=7, lookback_hours=hours
            )

            print(f"\n  ⏱️ {hours}時間:")
            print(f"    シグナル: {signal['signal'].upper()}")
            print(f"    信頼度: {signal['confidence']:.0%}")
            print(f"    ニュース数: {signal['news_summary']['count']} 件")
            print(f"    平均センチメント: {signal['news_summary']['avg_sentiment']:.2f}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_save_to_firestore():
    """TEST 4: Firestoreへの保存"""
    print("\n" + "=" * 60)
    print("TEST 4: Firestoreへのシグナル保存")
    print("=" * 60)

    try:
        engine = RuleEngine()

        # シグナル生成
        signal = engine.generate_signal(symbol="USD_JPY", interval="1hour", days=7)

        print(f"\n📊 生成されたシグナル:")
        print(f"  通貨ペア: {signal['symbol']}")
        print(f"  シグナル: {signal['signal'].upper()}")
        print(f"  信頼度: {signal['confidence']:.0%}")

        # Firestoreに保存
        doc_id = engine.save_signal_to_firestore(signal)

        print(f"\n✅ Firestoreに保存成功")
        print(f"  ドキュメントID: {doc_id}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メイン実行"""
    print("=" * 60)
    print("Rule Engine Test")
    print("=" * 60)
    print("\nルールエンジンのテストを実行します。")
    print("ニュース分析 + テクニカル指標 → トレードシグナル生成")
    print("\n" + "=" * 60)

    results = []

    # TEST 1: 単一シグナル
    results.append(("TEST 1: 単一シグナル", test_single_signal()))

    # TEST 2: 複数シグナル
    results.append(("TEST 2: 複数シグナル", test_multiple_signals()))

    # TEST 3: シグナル比較
    results.append(("TEST 3: シグナル比較", test_signal_comparison()))

    # TEST 4: Firestore保存
    results.append(("TEST 4: Firestore保存", test_save_to_firestore()))

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
