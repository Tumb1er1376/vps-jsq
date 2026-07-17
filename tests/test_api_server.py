#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "api_server.py"
spec = importlib.util.spec_from_file_location("vps_jsq_api", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "exchange_rate": "6.780",
            "custom_exchange_rate": "6.780",
            "renew_money": "10",
            "currency_code": "USD",
            "expiry_date": "2027-07-18",
            "trade_date": "2026-07-18",
        }

    def calc(self, **changes):
        payload = self.base | changes
        with tempfile.TemporaryDirectory() as share_dir:
            with patch.object(api, "SHARE_DIR", share_dir):
                return api.calc(payload)["data"]

    def test_all_payment_cycle_labels(self):
        units = {
            "monthly": "月",
            "quarterly": "季",
            "semiannually": "半年",
            "annually": "年",
            "biennially": "两年",
            "triennially": "三年",
            "quinquennially": "五年",
        }
        for cycle, unit in units.items():
            with self.subTest(cycle=cycle):
                data = self.calc(cycle=cycle)
                self.assertEqual(data["renewal"], f"67.80 人民币/{unit}")

    def test_custom_rate_is_calculated_separately(self):
        data = self.calc(cycle="annually", custom_exchange_rate="7.000")
        self.assertEqual(data["exchange_rate"], "6.780")
        self.assertEqual(data["custom_exchange_rate"], "7.000")
        self.assertEqual(data["remain_value"], "67.800")
        self.assertEqual(data["custom_remain_value"], "70.000")

    def test_expired_item_has_zero_remaining_value(self):
        data = self.calc(
            cycle="annually",
            expiry_date="2026-07-17",
            trade_date="2026-07-18",
        )
        self.assertEqual(data["remain_days"], "0")
        self.assertEqual(data["remain_value"], "0.000")

    def test_rejects_invalid_numbers_and_cycles(self):
        cases = [
            ({"cycle": "annually", "renew_money": "-1"}, "续费金额"),
            ({"cycle": "annually", "exchange_rate": "NaN"}, "参考汇率"),
            ({"cycle": "annually", "custom_exchange_rate": "Infinity"}, "外币汇率"),
            ({"cycle": "unknown"}, "付款周期"),
            ({"cycle": "annually", "exchange_rate": "1000001"}, "参考汇率"),
            ({"cycle": "annually", "renew_money": "1000000001"}, "续费金额"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, message):
                    self.calc(**changes)

    def test_rejects_non_object_or_missing_fields(self):
        with self.assertRaisesRegex(ValueError, "JSON 对象"):
            api.calc([])
        with self.assertRaisesRegex(ValueError, "不能为空"):
            api.calc({})

    def test_share_directory_is_bounded(self):
        with tempfile.TemporaryDirectory() as share_dir:
            share_path = Path(share_dir)
            for index in range(4):
                (share_path / f"{index:020x}.svg").write_text("old")
            with patch.object(api, "SHARE_DIR", share_dir), patch.object(api, "MAX_SHARE_FILES", 3):
                api.calc(self.base | {"cycle": "annually"})
            self.assertLessEqual(len(list(share_path.glob("*.svg"))), 3)

    def test_share_card_uses_configured_public_host(self):
        with patch.object(api, "PUBLIC_BASE_URL", "https://vps.example.com/tools"):
            data = self.calc(cycle="annually")
            share_name = data["share_pic"].rsplit("/", 1)[-1]
            # self.calc uses a temporary directory, so verify the pure renderer too.
            svg = api.make_share_svg(data)
        self.assertIn("vps.example.com", svg)
        self.assertNotIn("tool.beaver1376.top", svg)
        self.assertTrue(share_name.endswith(".svg"))

    def test_multi_cycle_remaining_days_are_intentionally_not_capped(self):
        data = self.calc(
            cycle="monthly",
            expiry_date="2027-07-18",
            trade_date="2026-07-18",
        )
        self.assertEqual(data["remain_days"], "365")
        self.assertGreater(float(data["remain_value"]), float(data["total_value"]))


if __name__ == "__main__":
    unittest.main()
