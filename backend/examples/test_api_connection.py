"""
GMOコイン API接続テスト

実際のAPIキーを使用して接続を確認するスクリプト
"""

import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.gmo_client import GMOCoinClient

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_public_api():
    """公開APIテスト（認証不要）"""
    print("\n" + "=" * 60)
    print("TEST 1: 公開API - ローソク足取得")
    print("=" * 60)

    try:
        client = GMOCoinClient()

        # ローソク足データ取得（今日の1時間足）
        print("\n📊 USD/JPY ローソク足（1時間足・本日分）:")
        klines = client.get_klines("USD_JPY", interval="1hour")

        if klines:
            print(f"  取得件数: {len(klines)} 件")
            for i, k in enumerate(klines[-3:], 1):  # 直近3本を表示
                print(f"\n  [{i}] {k.get('openTime')}:")
                print(f"    Open: {k.get('open')}")
                print(f"    High: {k.get('high')}")
                print(f"    Low: {k.get('low')}")
                print(f"    Close: {k.get('close')}")

        print("\n✅ TEST 1 PASSED: 公開APIが正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_private_api():
    """プライベートAPIテスト（認証必要）"""
    print("\n" + "=" * 60)
    print("TEST 2: プライベートAPI - 口座情報取得")
    print("=" * 60)

    try:
        # 環境変数から自動的にAPIキーを読み込み
        client = GMOCoinClient()

        if not client._has_private_credentials():
            print("\n⚠️  APIキーが設定されていません")
            print("  .envファイルにGMO_API_KEY, GMO_API_SECRETを設定してください")
            return False

        print("\n🔑 認証情報:")
        print(f"  API Key: {client.api_key[:10]}...{client.api_key[-4:]}")
        print(f"  API Secret: {client.api_secret[:10]}...****")

        # 口座資産情報を取得
        print("\n📊 口座資産情報を取得中...")
        assets = client.get_account_assets()

        print("\n💰 口座資産:")
        print(f"  口座残高: {assets.get('balance', 'N/A')} 円")
        print(f"  取引余力: {assets.get('availableAmount', 'N/A')} 円")
        print(f"  必要証拠金: {assets.get('margin', 'N/A')} 円")
        print(f"  評価損益: {assets.get('profitLoss', 'N/A')} 円")
        print(f"  振替可能額: {assets.get('transferableAmount', 'N/A')} 円")

        print("\n✅ TEST 2 PASSED: プライベートAPI認証成功")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_positions():
    """ポジション取得テスト"""
    print("\n" + "=" * 60)
    print("TEST 3: プライベートAPI - ポジション取得")
    print("=" * 60)

    try:
        client = GMOCoinClient()

        if not client._has_private_credentials():
            print("\n⚠️  APIキーが設定されていません")
            return False

        print("\n📊 ポジション一覧を取得中...")
        positions = client.get_positions()

        if not positions:
            print("\n  ポジションはありません")
        else:
            print(f"\n  ポジション数: {len(positions)} 件")
            for i, pos in enumerate(positions, 1):
                print(f"\n  [{i}] {pos.get('symbol')}:")
                print(f"    サイド: {pos.get('side')}")
                print(f"    サイズ: {pos.get('size')}")
                print(f"    価格: {pos.get('price')}")
                print(f"    損益: {pos.get('lossGain')}")

        print("\n✅ TEST 3 PASSED: ポジション取得成功")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_active_orders():
    """有効注文取得テスト"""
    print("\n" + "=" * 60)
    print("TEST 4: プライベートAPI - 有効注文取得")
    print("=" * 60)

    try:
        client = GMOCoinClient()

        if not client._has_private_credentials():
            print("\n⚠️  APIキーが設定されていません")
            return False

        print("\n📊 有効注文一覧を取得中...")
        orders = client.get_orders()

        if not orders:
            print("\n  有効な注文はありません")
        else:
            print(f"\n  注文数: {len(orders)} 件")
            for i, order in enumerate(orders, 1):
                print(f"\n  [{i}] {order.get('symbol')}:")
                print(f"    注文ID: {order.get('orderId')}")
                print(f"    サイド: {order.get('side')}")
                print(f"    タイプ: {order.get('executionType')}")
                print(f"    サイズ: {order.get('size')}")
                print(f"    価格: {order.get('price')}")
                print(f"    ステータス: {order.get('status')}")

        print("\n✅ TEST 4 PASSED: 有効注文取得成功")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    print("=" * 60)
    print("GMOコイン API接続テスト")
    print("=" * 60)

    results = {
        "TEST 1: 公開API": test_public_api(),
        "TEST 2: 口座情報": test_private_api(),
        "TEST 3: ポジション": test_positions(),
        "TEST 4: 有効注文": test_active_orders(),
    }

    # 結果サマリー
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\n結果: {passed}/{total} テスト成功")

    if passed == total:
        print("\n🎉 All tests passed! API接続が正常に動作しています。")
    else:
        print("\n⚠️  一部のテストが失敗しました。ログを確認してください。")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
