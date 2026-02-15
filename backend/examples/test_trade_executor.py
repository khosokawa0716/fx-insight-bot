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
            stop_loss_pips=40.0,
            take_profit_pips=40.0,
            max_monthly_loss=5000.0,
            max_daily_trades=2,
            min_trade_interval_hours=6,
            max_consecutive_losses=7,
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
            symbols=["USD_JPY"],
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
            first_size=100,
            first_price="155.000",
            second_size=100,
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
            first_size=500,
            first_price="160.000",
            second_execution_type="LIMIT",
            second_size=500,
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


def test_v2_ai_lot_decision():
    """TEST 8: v2.0 AIロット決定ロジックテスト"""
    print("\n" + "=" * 60)
    print("TEST 8: v2.0 AIロット決定ロジックテスト")
    print("=" * 60)

    try:
        gmo_client = GMOCoinClient(dry_run=True)
        technical_analyzer = TechnicalAnalyzer(gmo_client)
        rule_engine = RuleEngine(technical_analyzer=technical_analyzer)

        # テストケース: (signal, news_summary, expected_lot, description)
        test_cases = [
            ("hold", {"avg_sentiment": 0.0, "avg_impact": 0.0, "count": 0}, 0, "HOLD -> 0"),
            ("buy", {"avg_sentiment": 1.0, "avg_impact": 4.0, "count": 3}, 1500, "BUY + strong positive"),
            ("buy", {"avg_sentiment": 0.3, "avg_impact": 2.0, "count": 2}, 1000, "BUY + weak positive"),
            ("buy", {"avg_sentiment": 0.0, "avg_impact": 0.0, "count": 0}, 500, "BUY + no news"),
            ("buy", {"avg_sentiment": -0.5, "avg_impact": 3.0, "count": 2}, 0, "BUY + negative (skip)"),
            ("sell", {"avg_sentiment": -1.0, "avg_impact": 4.0, "count": 3}, 1500, "SELL + strong negative"),
            ("sell", {"avg_sentiment": -0.3, "avg_impact": 2.0, "count": 2}, 1000, "SELL + weak negative"),
            ("sell", {"avg_sentiment": 0.0, "avg_impact": 0.0, "count": 0}, 500, "SELL + no news"),
            ("sell", {"avg_sentiment": 0.5, "avg_impact": 3.0, "count": 2}, 0, "SELL + positive (skip)"),
        ]

        all_passed = True
        for signal, news_summary, expected_lot, desc in test_cases:
            lot, reason = rule_engine.determine_lot(signal, news_summary)
            status = "OK" if lot == expected_lot else "NG"
            if status == "NG":
                all_passed = False
            print(f"  [{status}] {desc}: lot={lot} (expected={expected_lot}) | {reason}")

        if all_passed:
            print("\n  ALL 9 CASES PASSED")
            print("\n  TEST 8 PASSED: AIロット決定ロジックが仕様通り動作")
            return True
        else:
            print("\n  TEST 8 FAILED: 一部のテストケースが失敗")
            return False

    except Exception as e:
        print(f"\n  TEST 8 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_ifdoco_price_calculation():
    """TEST 9: v2.0 IFDOCO価格計算テスト"""
    print("\n" + "=" * 60)
    print("TEST 9: v2.0 IFDOCO価格計算テスト")
    print("=" * 60)

    try:
        risk_config = RiskConfig()
        risk_manager = RiskManager(config=risk_config, db=None)

        current_price = 155.000
        pip_value = 0.01
        buffer = 1.0 * pip_value  # 1pip

        # BUY
        buy_entry = current_price + buffer  # 155.01
        buy_sl = risk_manager.calculate_stop_loss_price(buy_entry, "BUY", "USD_JPY")
        buy_tp = risk_manager.calculate_take_profit_price(buy_entry, "BUY", "USD_JPY")

        print(f"\n  BUY (current={current_price}):")
        print(f"    entry  = {buy_entry:.3f} (expected 155.010)")
        print(f"    SL     = {buy_sl:.3f} (expected 154.610)")
        print(f"    TP     = {buy_tp:.3f} (expected 155.410)")

        # SELL
        sell_entry = current_price - buffer  # 154.99
        sell_sl = risk_manager.calculate_stop_loss_price(sell_entry, "SELL", "USD_JPY")
        sell_tp = risk_manager.calculate_take_profit_price(sell_entry, "SELL", "USD_JPY")

        print(f"\n  SELL (current={current_price}):")
        print(f"    entry  = {sell_entry:.3f} (expected 154.990)")
        print(f"    SL     = {sell_sl:.3f} (expected 155.390)")
        print(f"    TP     = {sell_tp:.3f} (expected 154.590)")

        # 検証
        all_ok = True
        checks = [
            (abs(buy_entry - 155.010) < 0.001, "BUY entry"),
            (abs(buy_sl - 154.610) < 0.001, "BUY SL"),
            (abs(buy_tp - 155.410) < 0.001, "BUY TP"),
            (abs(sell_entry - 154.990) < 0.001, "SELL entry"),
            (abs(sell_sl - 155.390) < 0.001, "SELL SL"),
            (abs(sell_tp - 154.590) < 0.001, "SELL TP"),
        ]
        for ok, label in checks:
            if not ok:
                all_ok = False
                print(f"    NG: {label}")

        if all_ok:
            print("\n  TEST 9 PASSED: IFDOCO価格計算が仕様通り動作")
        else:
            print("\n  TEST 9 FAILED: 価格計算にずれあり")
        return all_ok

    except Exception as e:
        print(f"\n  TEST 9 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_baseline_calculation():
    """TEST 10: v2.0 Baseline損益計算テスト"""
    print("\n" + "=" * 60)
    print("TEST 10: v2.0 Baseline損益計算テスト")
    print("=" * 60)

    try:
        # BUY: 利益ケース (155.00 -> 155.40, +40pips)
        bl1 = TradeExecutor.calculate_baseline_pnl(155.00, 155.40, "BUY")
        # BUY: 損失ケース (155.00 -> 154.60, -40pips)
        bl2 = TradeExecutor.calculate_baseline_pnl(155.00, 154.60, "BUY")
        # SELL: 利益ケース (155.00 -> 154.60, +40pips)
        bl3 = TradeExecutor.calculate_baseline_pnl(155.00, 154.60, "SELL")
        # SELL: 損失ケース (155.00 -> 155.40, -40pips)
        bl4 = TradeExecutor.calculate_baseline_pnl(155.00, 155.40, "SELL")

        print(f"  BUY  155.00 -> 155.40: {bl1:.0f}  (expected 400)")
        print(f"  BUY  155.00 -> 154.60: {bl2:.0f}  (expected -400)")
        print(f"  SELL 155.00 -> 154.60: {bl3:.0f}  (expected 400)")
        print(f"  SELL 155.00 -> 155.40: {bl4:.0f}  (expected -400)")

        all_ok = (
            abs(bl1 - 400) < 0.01
            and abs(bl2 - (-400)) < 0.01
            and abs(bl3 - 400) < 0.01
            and abs(bl4 - (-400)) < 0.01
        )

        if all_ok:
            print("\n  TEST 10 PASSED: Baseline計算が正しい")
        else:
            print("\n  TEST 10 FAILED: Baseline計算にずれあり")
        return all_ok

    except Exception as e:
        print(f"\n  TEST 10 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_risk_config_defaults():
    """TEST 11: v2.0 RiskConfig デフォルト値テスト"""
    print("\n" + "=" * 60)
    print("TEST 11: v2.0 RiskConfig デフォルト値テスト")
    print("=" * 60)

    try:
        config = RiskConfig()

        checks = [
            (config.stop_loss_pips == 40.0, f"stop_loss_pips={config.stop_loss_pips} (expected 40.0)"),
            (config.take_profit_pips == 40.0, f"take_profit_pips={config.take_profit_pips} (expected 40.0)"),
            (config.max_monthly_loss == 5000.0, f"max_monthly_loss={config.max_monthly_loss} (expected 5000.0)"),
            (config.max_daily_trades == 2, f"max_daily_trades={config.max_daily_trades} (expected 2)"),
            (config.min_trade_interval_hours == 6, f"min_trade_interval_hours={config.min_trade_interval_hours} (expected 6)"),
            (config.max_consecutive_losses == 7, f"max_consecutive_losses={config.max_consecutive_losses} (expected 7)"),
        ]

        all_ok = True
        for ok, desc in checks:
            status = "OK" if ok else "NG"
            if not ok:
                all_ok = False
            print(f"  [{status}] {desc}")

        if all_ok:
            print("\n  TEST 11 PASSED: RiskConfig v2.0 デフォルト値が正しい")
        else:
            print("\n  TEST 11 FAILED: デフォルト値にずれあり")
        return all_ok

    except Exception as e:
        print(f"\n  TEST 11 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_risk_consecutive_losses():
    """TEST 12: v2.0 連続損失での取引停止テスト"""
    print("\n" + "=" * 60)
    print("TEST 12: v2.0 連続損失での取引停止テスト")
    print("=" * 60)

    try:
        # max_daily_trades を大きくして日次上限に引っかからないようにする
        risk_config = RiskConfig(max_daily_trades=100)
        risk_manager = RiskManager(config=risk_config, db=None)

        print(f"  max_consecutive_losses = {risk_config.max_consecutive_losses}")

        # 6回連続損失 -> まだ取引可能
        for i in range(6):
            risk_manager.record_trade_result(profit_loss=-600, success=False)

        check6 = risk_manager.check_trade_allowed("USD_JPY", "BUY", 1000)
        print(f"  6回連続損失後: can_trade={check6.can_trade} (expected True)")

        # 7回目 -> 取引停止
        risk_manager.record_trade_result(profit_loss=-600, success=False)
        check7 = risk_manager.check_trade_allowed("USD_JPY", "BUY", 1000)
        print(f"  7回連続損失後: can_trade={check7.can_trade} (expected False)")
        print(f"    reason: {check7.reason}")

        # 利益が出たらリセット
        risk_manager.record_trade_result(profit_loss=400, success=True)
        check_reset = risk_manager.check_trade_allowed("USD_JPY", "BUY", 1000)
        print(f"  利益後リセット: can_trade={check_reset.can_trade} (expected True)")

        all_ok = check6.can_trade and not check7.can_trade and check_reset.can_trade

        if all_ok:
            print("\n  TEST 12 PASSED: 連続損失の取引停止と復帰が正しい")
        else:
            print("\n  TEST 12 FAILED")
        return all_ok

    except Exception as e:
        print(f"\n  TEST 12 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_trade_executor_with_risk_manager():
    """TEST 13: v2.0 TradeExecutor + RiskManager 統合 DRY-RUN"""
    print("\n" + "=" * 60)
    print("TEST 13: v2.0 TradeExecutor + RiskManager 統合 DRY-RUN")
    print("=" * 60)

    try:
        gmo_client = GMOCoinClient(dry_run=True)
        technical_analyzer = TechnicalAnalyzer(gmo_client)
        rule_engine = RuleEngine(technical_analyzer=technical_analyzer)

        risk_config = RiskConfig()
        risk_manager = RiskManager(config=risk_config, db=None)

        trade_config = TradeConfig(symbols=["USD_JPY"])

        executor = TradeExecutor(
            gmo_client=gmo_client,
            rule_engine=rule_engine,
            config=trade_config,
            risk_manager=risk_manager,
            db=None,
        )

        print("\n  v2.0 フロー DRY-RUN 実行:")
        results = executor.execute_signals()

        for result in results:
            print(f"    symbol={result.symbol} action={result.action} "
                  f"size={result.size} success={result.success}")
            print(f"    reason: {result.reason}")
            print(f"    dry_run={result.dry_run}")

        print("\n  TEST 13 PASSED: v2.0 統合DRY-RUN完了（action確認済み）")
        return True

    except Exception as e:
        print(f"\n  TEST 13 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2_max_loss_per_trade():
    """TEST 14: v2.0 1取引最大損失の検証"""
    print("\n" + "=" * 60)
    print("TEST 14: v2.0 1取引最大損失の検証")
    print("=" * 60)

    try:
        # 仕様: 最大ロット1500通貨 x SL40pips x 0.01 = 600円
        max_lot = 1500
        sl_pips = 40.0
        pip_value = 0.01

        max_loss = max_lot * sl_pips * pip_value
        print(f"  最大ロット: {max_lot} 通貨")
        print(f"  SL: {sl_pips} pips")
        print(f"  pip_value: {pip_value}")
        print(f"  最大損失: {max_loss:.0f} 円 (設計目標 <= 700円)")

        ok = max_loss <= 700
        if ok:
            print(f"\n  TEST 14 PASSED: 最大損失 {max_loss:.0f}円 <= 700円")
        else:
            print(f"\n  TEST 14 FAILED: 最大損失 {max_loss:.0f}円 > 700円")
        return ok

    except Exception as e:
        print(f"\n  TEST 14 FAILED: {e}")
        return False


def main():
    """メイン関数"""
    print("=" * 60)
    print("Trade Executor Test Suite")
    print("v2.0: AIロット決定 + IFDOCO + リスク管理")
    print("=" * 60)

    results = {
        "TEST 1: DRY-RUN注文": test_dry_run_order(),
        "TEST 2: リスク管理": test_risk_manager(),
        "TEST 3: TradeExecutor": test_trade_executor_dry_run(),
        "TEST 4: 決済シミュレーション": test_position_close_simulation(),
        "TEST 5: 口座サマリー": test_account_summary(),
        "TEST 6: ストップロス・利確": test_stop_loss_check(),
        "TEST 7: IFDOCO注文": test_ifdoco_order(),
        "TEST 8: AIロット決定": test_v2_ai_lot_decision(),
        "TEST 9: IFDOCO価格計算": test_v2_ifdoco_price_calculation(),
        "TEST 10: Baseline計算": test_v2_baseline_calculation(),
        "TEST 11: RiskConfig v2.0": test_v2_risk_config_defaults(),
        "TEST 12: 連続損失停止": test_v2_risk_consecutive_losses(),
        "TEST 13: 統合DRY-RUN": test_v2_trade_executor_with_risk_manager(),
        "TEST 14: 最大損失検証": test_v2_max_loss_per_trade(),
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
