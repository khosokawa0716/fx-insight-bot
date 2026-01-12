"""
GMO Coin Client Test Script

GMOコインクライアントの動作確認スクリプト
ローソク足取得機能をテストします。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.gmo_client import GMOCoinClient, parse_kline_to_ohlcv


def test_get_klines():
    """TEST 1: ローソク足取得（1日分）"""
    print("\n" + "=" * 60)
    print("TEST 1: ローソク足取得（1日分）")
    print("=" * 60)

    try:
        client = GMOCoinClient()

        # 1時間足を取得（今日）
        klines = client.get_klines(
            symbol="USD_JPY",
            interval="1hour",
            price_type="ASK",
        )

        print(f"\n✅ 取得成功: {len(klines)} 本のローソク足")

        if klines:
            # 最初の3本を表示
            print("\n📊 サンプルデータ（最初の3本）:")
            for i, kline in enumerate(klines[:3], 1):
                print(f"\n{i}.")
                print(f"  Time:  {kline['openTime']}")
                print(f"  Open:  {kline['open']}")
                print(f"  High:  {kline['high']}")
                print(f"  Low:   {kline['low']}")
                print(f"  Close: {kline['close']}")

            # OHLCV形式に変換
            ohlcv = parse_kline_to_ohlcv(klines)
            print(f"\n📈 OHLCV変換成功:")
            print(f"  データ数: {len(ohlcv['close'])} 本")
            print(f"  Close価格範囲: {min(ohlcv['close']):.3f} 〜 {max(ohlcv['close']):.3f}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_klines_range():
    """TEST 2: 複数日のローソク足取得"""
    print("\n" + "=" * 60)
    print("TEST 2: 複数日のローソク足取得（過去3日）")
    print("=" * 60)

    try:
        client = GMOCoinClient()

        # 過去3日分の1時間足を取得
        klines = client.get_klines_range(
            symbol="USD_JPY",
            interval="1hour",
            days=3,
            price_type="ASK",
        )

        print(f"\n✅ 取得成功: {len(klines)} 本のローソク足（3日分）")

        if klines:
            # 最新のデータを表示
            print("\n📊 最新データ:")
            latest = klines[-1]
            print(f"  Time:  {latest['openTime']}")
            print(f"  Close: {latest['close']}")

            # OHLCV形式に変換
            ohlcv = parse_kline_to_ohlcv(klines)
            print(f"\n📈 統計情報:")
            print(f"  データ数: {len(ohlcv['close'])} 本")
            print(f"  最高値: {max(ohlcv['high']):.3f}")
            print(f"  最安値: {min(ohlcv['low']):.3f}")
            print(f"  最新価格: {ohlcv['close'][-1]:.3f}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_symbols():
    """TEST 3: 複数通貨ペアの取得"""
    print("\n" + "=" * 60)
    print("TEST 3: 複数通貨ペアの取得")
    print("=" * 60)

    try:
        client = GMOCoinClient()

        symbols = ["USD_JPY", "EUR_JPY"]

        for symbol in symbols:
            print(f"\n📌 {symbol}")
            klines = client.get_klines(
                symbol=symbol,
                interval="1hour",
                price_type="ASK",
            )
            print(f"  ✅ {len(klines)} 本のローソク足取得")

            if klines:
                latest_close = float(klines[-1]["close"])
                print(f"  最新価格: {latest_close:.3f}")

        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_intervals():
    """TEST 4: 異なる時間足の取得"""
    print("\n" + "=" * 60)
    print("TEST 4: 異なる時間足の取得")
    print("=" * 60)

    try:
        client = GMOCoinClient()

        intervals = ["15min", "1hour", "4hour"]

        for interval in intervals:
            print(f"\n📌 {interval}")
            klines = client.get_klines(
                symbol="USD_JPY",
                interval=interval,
                price_type="ASK",
            )
            print(f"  ✅ {len(klines)} 本のローソク足取得")

        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン実行"""
    print("=" * 60)
    print("GMO Coin Client Test")
    print("=" * 60)
    print("\nGMOコインのローソク足APIをテストします。")
    print("認証不要（公開API）")
    print("\n" + "=" * 60)

    results = []

    # TEST 1: 基本的なローソク足取得
    results.append(("TEST 1: ローソク足取得", test_get_klines()))

    # TEST 2: 複数日取得
    results.append(("TEST 2: 複数日取得", test_get_klines_range()))

    # TEST 3: 複数通貨ペア
    results.append(("TEST 3: 複数通貨ペア", test_multiple_symbols()))

    # TEST 4: 異なる時間足
    results.append(("TEST 4: 異なる時間足", test_different_intervals()))

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
