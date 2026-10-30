"""
Automated unit tests for spreadProfit.

Verifies moving weighted average cost basis calculations, unit conversions,
atomic JSON database operations, cloud snapshot creation, and UI loading.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from typing import Any, Dict, List

import cloud_backup
from config import get_unit_factor, normalize_action, normalize_category, normalize_unit
from db_manager import calculate_portfolio, next_id


class TestPortfolioCalculations(unittest.TestCase):
    """Test suite for financial calculations and moving average cost basis."""

    def test_unit_conversion_factors(self) -> None:
        """Ensure standard precious metals units resolve to correct Troy Ounce factors."""
        self.assertAlmostEqual(get_unit_factor("tael"), 1.2057, places=4)
        self.assertAlmostEqual(get_unit_factor("lượng"), 1.2057, places=4)
        self.assertAlmostEqual(get_unit_factor("chi"), 0.12057, places=4)
        self.assertAlmostEqual(get_unit_factor("chỉ"), 0.12057, places=4)
        self.assertAlmostEqual(get_unit_factor("ounce"), 1.0, places=4)
        self.assertAlmostEqual(get_unit_factor("0.1 chi"), 0.012057, places=5)
        # Default fallback
        self.assertEqual(get_unit_factor("unknown_unit"), 1.0)

    def test_normalizers(self) -> None:
        """Verify category, action, and unit normalizers to standard English."""
        self.assertEqual(normalize_category("Vàng"), "Gold")
        self.assertEqual(normalize_category("gold"), "Gold")
        self.assertEqual(normalize_category("Bạc"), "Silver")
        self.assertEqual(normalize_category("silver"), "Silver")

        self.assertEqual(normalize_action("Mua"), "Buy")
        self.assertEqual(normalize_action("buy"), "Buy")
        self.assertEqual(normalize_action("Bán"), "Sell")
        self.assertEqual(normalize_action("sell"), "Sell")

        self.assertEqual(normalize_unit("lượng"), "Tael")
        self.assertEqual(normalize_unit("chỉ"), "Chi")
        self.assertEqual(normalize_unit("tael"), "Tael")

    def test_moving_average_cost_buy_only(self) -> None:
        """Verify weighted average cost basis on multiple buy transactions."""
        txs: List[Dict[str, Any]] = [
            {
                "id": 1,
                "date": "2026-01-01",
                "category": "Gold",
                "asset": "Gold Coin 1",
                "action": "Buy",
                "quantity": 2.0,
                "unit": "Chi",
                "unit_price": 10000000.0,
                "total": 20000000.0,
            },
            {
                "id": 2,
                "date": "2026-01-02",
                "category": "Gold",
                "asset": "Gold Coin 1",
                "action": "Buy",
                "quantity": 2.0,
                "unit": "Chi",
                "unit_price": 12000000.0,
                "total": 24000000.0,
            },
        ]
        prices = {"Gold": {"buy": 15000000.0, "sell": 15500000.0, "unit": "Chi"}}
        holdings, summary = calculate_portfolio(txs, prices)

        asset = holdings["Gold Coin 1"]
        self.assertEqual(asset["qty"], 4.0)
        self.assertEqual(asset["cost"], 44000000.0)
        self.assertEqual(asset["avg_price"], 11000000.0)
        self.assertEqual(asset["current_value"], 60000000.0)
        self.assertEqual(asset["pnl"], 16000000.0)
        self.assertAlmostEqual(asset["pnl_pct"], 36.36, delta=0.01)

    def test_moving_average_cost_with_sells(self) -> None:
        """Verify cost basis deduction after partial liquidation."""
        txs: List[Dict[str, Any]] = [
            {
                "id": 1,
                "date": "2026-01-01",
                "category": "Gold",
                "asset": "Gold Bar",
                "action": "Buy",
                "quantity": 4.0,
                "unit": "Tael",
                "unit_price": 80000000.0,
                "total": 320000000.0,
            },
            {
                "id": 2,
                "date": "2026-01-05",
                "category": "Gold",
                "asset": "Gold Bar",
                "action": "Sell",
                "quantity": 2.0,
                "unit": "Tael",
                "unit_price": 90000000.0,
                "total": 180000000.0,
            },
        ]
        prices = {"Gold": {"buy": 85000000.0, "sell": 86000000.0, "unit": "Tael"}}
        holdings, summary = calculate_portfolio(txs, prices)

        asset = holdings["Gold Bar"]
        self.assertEqual(asset["qty"], 2.0)
        self.assertEqual(asset["cost"], 160000000.0)
        self.assertEqual(asset["avg_price"], 80000000.0)
        self.assertEqual(asset["current_value"], 170000000.0)
        self.assertEqual(asset["pnl"], 10000000.0)

    def test_next_id_generation(self) -> None:
        """Check incremental ID generation."""
        self.assertEqual(next_id([]), 1)
        self.assertEqual(next_id([{"id": 5}, {"id": 12}, {"id": 3}]), 13)


class TestCloudAndLocalBackup(unittest.TestCase):
    """Test suite for local snapshot creation and data archiving."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_snapshot_and_archive(self) -> None:
        """Verify snapshot JSON and ZIP archive generation."""
        meta = cloud_backup.create_local_snapshot(target_dir=self.test_dir)
        self.assertEqual(meta["status"], "success")
        self.assertTrue(os.path.exists(meta["snapshot_path"]))
        self.assertTrue(os.path.exists(meta["archive_path"]))
        self.assertGreater(os.path.getsize(meta["snapshot_path"]), 0)
        self.assertGreater(os.path.getsize(meta["archive_path"]), 0)


class TestAppUIInitialization(unittest.TestCase):
    """Verify Tkinter application structure loads cleanly."""

    def test_app_startup_and_view_refresh(self) -> None:
        """Initialize SpreadProfitApp and ensure tabs refresh without exception."""
        from ui_main import SpreadProfitApp

        app = SpreadProfitApp()
        try:
            app.tab_transactions.refresh_table()
            app.tab_portfolio.refresh_view()
            app.tab_charts.draw_charts()
            self.assertIsNotNone(app.tab_portfolio)
            self.assertIsNotNone(app.tab_transactions)
            self.assertIsNotNone(app.tab_charts)
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
