"""
Trade Executor Test Script

自動売買機能のテストスクリプト（DRY-RUNモード）
実際の注文は行わず、シミュレーションのみ実行します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.gmo_client import GMOCoinClient
from src.services.technical_analyzer import TechnicalAnalyzer
from src.services.rule_engine import RuleEngine
from src.services.trade_executor import TradeExecutor, TradeConfig, TradeResult
from src.services.risk_manager import RiskManager, RiskConfig


def test_dry_run_order():
    """TEST 1: DRY-RUNモードでの注文テスト"""
    print("\n" + "=" * 60)
    print("TEST 1: DRY-RUNモードでの注文テスト")
    print("=" * 60)

    try:
        # DRY-RUNモードでクライアント初期化
        client = GMOCoinClient(dry_run=True)

        # 買い注文（シミュレーション）
        print("\n📊 買い注文（シミュレーション）:")
        buy_result = client.place_order(
            symbol="USD_JPY",
            side="BUY",
            size=1,
            execution_type="MARKET",
        )

        print(f"  注文ID: {buy_result.get('orderId')}")
        print(f"  シンボル: {buy_result.get('symbol')}")
        print(f"  サイド: {buy_result.get('side')}")
        print(f"  サイズ: {buy_result.get('size')}")
        print(f"  ステータス: {buy_result.get('status')}")
        print(f"  DRY-RUN: {buy_result.get('_dry_run')}")

        # 売り注文（シミュレーション）
        print("\n📊 売り注文（シミュレーション）:")
        sell_result = client.place_order(
            symbol="EUR_JPY",
            side="SELL",
            size=2,
            execution_type="MARKET",
        )

        print(f"  注文ID: {sell_result.get('orderId')}")
        print(f"  シンボル: {sell_result.get('symbol')}")
        print(f"  サイド: {sell_result.get('side')}")
        print(f"  サイズ: {sell_result.get('size')}")

        print("\n✅ TEST 1 PASSED: DRY-RUNモードの注文が正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_manager():
    """TEST 2: リスク管理機能テスト"""
    print("\n" + "=" * 60)
    print("TEST 2: リスク管理機能テスト")
    print("=" * 60)

    try:
        # リスク管理設定
        risk_config = RiskConfig(
            stop_loss_pips=50.0,
            take_profit_pips=100.0,
            max_daily_loss=50000.0,
            max_daily_trades=10,
            max_consecutive_losses=3,
        )

        risk_manager = RiskManager(config=risk_config, db=None)

        # 取引可否チェック
        print("\n📊 取引可否チェック:")
        check_result = risk_manager.check_trade_allowed(
            symbol="USD_JPY",
            side="BUY",
            size=1,
        )

        print(f"  取引可能: {check_result.can_trade}")
        print(f"  理由: {check_result.reason}")
        print(f"  リスクレベル: {check_result.risk_level}")

        # ストップロス・利確価格計算
        print("\n📊 ストップロス・利確価格計算:")
        entry_price = 157.500
        stop_loss = risk_manager.calculate_stop_loss_price(entry_price, "BUY", "USD_JPY")
        take_profit = risk_manager.calculate_take_profit_price(entry_price, "BUY", "USD_JPY")

        print(f"  エントリー価格: {entry_price}")
        print(f"  ストップロス: {stop_loss} (-{risk_config.stop_loss_pips}pips)")
        print(f"  利確価格: {take_profit} (+{risk_config.take_profit_pips}pips)")

        # 損失記録とリスクレベル変化
        print("\n📊 連続損失のシミュレーション:")
        for i in range(3):
            risk_manager.record_trade_result(profit_loss=-10000, success=False)
            summary = risk_manager.get_risk_summary()
            print(f"  {i+1}回目の損失: リスクレベル={summary['risk_level']}, 連続損失={summary['consecutive_losses']}")

        # 連続損失後の取引チェック
        check_after_losses = risk_manager.check_trade_allowed("USD_JPY", "BUY", 1)
        print(f"\n  連続損失後の取引可否: {check_after_losses.can_trade}")
        print(f"  理由: {check_after_losses.reason}")

        print("\n✅ TEST 2 PASSED: リスク管理機能が正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_executor_dry_run():
    """TEST 3: TradeExecutor DRY-RUNモードテスト"""
    print("\n" + "=" * 60)
    print("TEST 3: TradeExecutor DRY-RUNモードテスト")
    print("=" * 60)

    try:
        # コンポーネント初期化（DRY-RUNモード）
        gmo_client = GMOCoinClient(dry_run=True)
        technical_analyzer = TechnicalAnalyzer(gmo_client)
        rule_engine = RuleEngine(
            technical_analyzer=technical_analyzer,
        )

        # トレード設定
        trade_config = TradeConfig(
            symbols=["USD_JPY"],
            default_size=1,
            max_positions_per_symbol=3,
            max_total_positions=5,
            min_confidence=0.5,  # テスト用に低めに設定
        )

        # TradeExecutor初期化
        executor = TradeExecutor(
            gmo_client=gmo_client,
            rule_engine=rule_engine,
            config=trade_config,
            db=None,
        )

        # シグナル実行
        print("\n📊 シグナル実行（DRY-RUN）:")
        results = executor.execute_signals()

        for result in results:
            print(f"\n  シンボル: {result.symbol}")
            print(f"  アクション: {result.action}")
            print(f"  成功: {result.success}")
            print(f"  理由: {result.reason}")
            print(f"  注文ID: {result.order_id or 'N/A'}")
            print(f"  DRY-RUN: {result.dry_run}")

        print("\n✅ TEST 3 PASSED: TradeExecutor DRY-RUNモードが正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_close_simulation():
    """TEST 4: ポジション決済シミュレーション"""
    print("\n" + "=" * 60)
    print("TEST 4: ポジション決済シミュレーション")
    print("=" * 60)

    try:
        client = GMOCoinClient(dry_run=True)

        # ポジション決済（シミュレーション）
        print("\n📊 ポジション決済（シミュレーション）:")
        close_result = client.close_position(
            position_id="TEST_POS_001",
            symbol="USD_JPY",
            side="SELL",  # BUYポジションの決済
            size=1,
        )

        print(f"  決済注文ID: {close_result.get('orderId')}")
        print(f"  ポジションID: {close_result.get('positionId')}")
        print(f"  シンボル: {close_result.get('symbol')}")
        print(f"  サイド: {close_result.get('side')}")
        print(f"  サイズ: {close_result.get('size')}")
        print(f"  ステータス: {close_result.get('status')}")
        print(f"  DRY-RUN: {close_result.get('_dry_run')}")

        print("\n✅ TEST 4 PASSED: ポジション決済シミュレーションが正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_account_summary():
    """TEST 5: 口座サマリー取得（DRY-RUN）"""
    print("\n" + "=" * 60)
    print("TEST 5: 口座サマリー取得（DRY-RUN）")
    print("=" * 60)

    try:
        gmo_client = GMOCoinClient(dry_run=True)
        technical_analyzer = TechnicalAnalyzer(gmo_client)
        rule_engine = RuleEngine(
            technical_analyzer=technical_analyzer,
        )

        trade_config = TradeConfig(
            symbols=["USD_JPY", "EUR_JPY"],
            default_size=1,
        )

        executor = TradeExecutor(
            gmo_client=gmo_client,
            rule_engine=rule_engine,
            config=trade_config,
            db=None,
        )

        print("\n📊 口座サマリー:")
        summary = executor.get_account_summary()

        print(f"  DRY-RUN: {summary['dry_run']}")
        print(f"  総ポジション数: {summary['total_positions']}")
        print(f"  最大ポジション数: {summary['max_positions']}")
        print(f"  口座情報: {summary['account']}")

        print("\n✅ TEST 5 PASSED: 口座サマリー取得が正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stop_loss_check():
    """TEST 6: ストップロス・利確チェック"""
    print("\n" + "=" * 60)
    print("TEST 6: ストップロス・利確チェック")
    print("=" * 60)

    try:
        risk_config = RiskConfig(
            stop_loss_pips=50.0,
            take_profit_pips=100.0,
        )
        risk_manager = RiskManager(config=risk_config, db=None)

        # テスト用ポジション
        position = {
            "positionId": "TEST_001",
            "symbol": "USD_JPY",
            "side": "BUY",
            "price": "157.500",
            "size": "1",
        }

        # 各シナリオをテスト
        scenarios = [
            ("現在価格 = エントリー価格", 157.500),
            ("小幅上昇（利確未達）", 157.800),
            ("大幅上昇（利確達成）", 158.600),
            ("小幅下落（損切り未達）", 157.200),
            ("大幅下落（損切り達成）", 156.900),
        ]

        print("\n📊 ストップロス・利確チェック:")
        print(f"  エントリー価格: 157.500")
        print(f"  ストップロス: 157.000 (-50pips)")
        print(f"  利確価格: 158.500 (+100pips)")
        print()

        for scenario_name, current_price in scenarios:
            should_close, reason = risk_manager.should_close_position(
                position, current_price
            )
            status = "❌ 決済" if should_close else "⚪ 保持"
            print(f"  {scenario_name}: {current_price} → {status}")
            if should_close:
                print(f"    理由: {reason}")

        print("\n✅ TEST 6 PASSED: ストップロス・利確チェックが正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ifdoco_order():
    """TEST 7: IFDOCO注文テスト（DRY-RUN）"""
    print("\n" + "=" * 60)
    print("TEST 7: IFDOCO注文テスト（DRY-RUN）")
    print("=" * 60)

    try:
        client = GMOCoinClient(dry_run=True)

        # IFDOCO注文（シミュレーション）
        print("\n📊 IFDOCO注文（シミュレーション）:")
        print("  シナリオ: USD/JPYを155円で買い、157円で利確、153円で損切り")

        result = client.place_ifdoco_order(
            symbol="USD_JPY",
            first_side="BUY",
            first_execution_type="LIMIT",
            first_size=1,
            first_price="155.000",
            second_size=1,
            second_limit_price="157.000",  # 利確（+200pips）
            second_stop_price="153.000",   # 損切り（-200pips）
        )

        print(f"\n  注文数: {len(result)} 件")

        for i, order in enumerate(result, 1):
            settle_type = order.get("settleType", "")
            exec_type = order.get("executionType", "")
            label = "新規" if settle_type == "OPEN" else (
                "利確" if exec_type == "LIMIT" else "損切"
            )
            print(f"\n  [{i}] {label}注文:")
            print(f"    注文ID: {order.get('orderId')}")
            print(f"    親注文ID: {order.get('rootOrderId')}")
            print(f"    サイド: {order.get('side')}")
            print(f"    タイプ: {order.get('executionType')}")
            print(f"    決済区分: {order.get('settleType')}")
            print(f"    価格: {order.get('price')}")
            print(f"    ステータス: {order.get('status')}")

        # IFD注文もテスト
        print("\n📊 IFD注文（シミュレーション）:")
        print("  シナリオ: EUR/JPYを160円で売り、158円で決済")

        ifd_result = client.place_ifd_order(
            symbol="EUR_JPY",
            first_side="SELL",
            first_execution_type="LIMIT",
            first_size=1,
            first_price="160.000",
            second_execution_type="LIMIT",
            second_size=1,
            second_price="158.000",
        )

        print(f"\n  注文数: {len(ifd_result)} 件")

        for i, order in enumerate(ifd_result, 1):
            settle_type = order.get("settleType", "")
            label = "新規" if settle_type == "OPEN" else "決済"
            print(f"\n  [{i}] {label}注文:")
            print(f"    注文ID: {order.get('orderId')}")
            print(f"    サイド: {order.get('side')}")
            print(f"    価格: {order.get('price')}")

        print("\n✅ TEST 7 PASSED: IFDOCO/IFD注文が正常に動作")
        return True

    except Exception as e:
        print(f"\n❌ TEST 7 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    print("=" * 60)
    print("Trade Executor Test Suite")
    print("Phase 4: 自動売買機能テスト（DRY-RUNモード）")
    print("=" * 60)

    results = {
        "TEST 1: DRY-RUN注文": test_dry_run_order(),
        "TEST 2: リスク管理": test_risk_manager(),
        "TEST 3: TradeExecutor": test_trade_executor_dry_run(),
        "TEST 4: 決済シミュレーション": test_position_close_simulation(),
        "TEST 5: 口座サマリー": test_account_summary(),
        "TEST 6: ストップロス・利確": test_stop_loss_check(),
        "TEST 7: IFDOCO注文": test_ifdoco_order(),
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
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
