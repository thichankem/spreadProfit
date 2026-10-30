"""
Database management and portfolio financial calculation engine for spreadProfit.

Handles persistent storage in JSON format, directory resolution for portable/installed
modes, seed restoration, atomic file writes, and moving weighted average cost (MAC)
PnL analytics.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from config import get_unit_factor

APP_NAME = "spreadProfit"
DATA_FILE_NAMES = ("gold_transactions.json", "market_prices.json", "custom_assets.json")

# Resolve base execution and bundle directories
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR


def _is_writable(path: str) -> bool:
    """Verify write permissions for a target directory."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return True
    except Exception:
        return False


def _resolve_data_dir() -> str:
    """
    Determine the primary data directory based on execution context:
    1. Portable mode: 'data' folder alongside executable or root script.
    2. Fallback mode: %APPDATA%/spreadProfit when the parent directory is read-only.
    """
    portable = os.path.join(BASE_DIR, "data")
    if _is_writable(portable):
        return portable
    fallback = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME)
    os.makedirs(fallback, exist_ok=True)
    return fallback


DATA_DIR = _resolve_data_dir()


def _atomic_write_json(file_path: str, data: Any) -> None:
    """Atomically write JSON data using a temporary swap file to prevent corruption."""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    dir_name = os.path.dirname(os.path.abspath(file_path))
    temp_file = tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8")
    try:
        with temp_file as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(temp_file.name, file_path)
    except Exception:
        if os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
            except Exception:
                pass
        raise


def _seed_data_files() -> None:
    """Restore seed data files from bundled resources or root on fresh launch."""
    for name in DATA_FILE_NAMES:
        target = os.path.join(DATA_DIR, name)
        if os.path.exists(target):
            continue
        candidate_sources = (
            os.path.join(BASE_DIR, name),
            os.path.join(BUNDLE_DIR, "_seed", name),
            os.path.join(BASE_DIR, "_seed", name),
        )
        for source in candidate_sources:
            if os.path.exists(source) and os.path.abspath(source) != os.path.abspath(target):
                try:
                    shutil.copyfile(source, target)
                    break
                except Exception:
                    pass


# Ensure seed files are populated if missing
_seed_data_files()

DB_FILE = os.path.join(DATA_DIR, "gold_transactions.json")
PRICES_FILE = os.path.join(DATA_DIR, "market_prices.json")
CUSTOM_ASSETS_FILE = os.path.join(DATA_DIR, "custom_assets.json")


def load_db() -> List[Dict[str, Any]]:
    """Load transaction records from JSON storage, initializing sample record if missing."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []

    initial_seed = [
        {
            "id": 1,
            "date": "2026-03-26",
            "category": "Vàng",
            "asset": "Vàng nhẫn 24K Bảo Tín Mạnh Hải",
            "action": "Mua",
            "quantity": 2.0,
            "unit": "Chỉ",
            "unit_price": 18500000.0,
            "total": 37000000.0,
            "note": "HĐ 00271176 – 2 nhẫn Kim Gia Bảo",
        }
    ]
    save_db(initial_seed)
    return initial_seed


def save_db(data: List[Dict[str, Any]]) -> None:
    """Save transaction records atomically to JSON storage."""
    _atomic_write_json(DB_FILE, data)


def next_id(data: List[Dict[str, Any]]) -> int:
    """Generate the next incremental integer identifier for a record."""
    return max((int(r.get("id", 0)) for r in data), default=0) + 1


def calculate_portfolio(
    transactions: List[Dict[str, Any]],
    current_prices: Dict[str, Any],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, float]]:
    """
    Compute real-time portfolio holdings, average cost, market value, and PnL.

    Applies the moving weighted average cost (MAC) accounting method to accurately
    compute cost basis across chronological buy and sell events.

    Args:
        transactions: List of transaction dictionaries.
        current_prices: Dict mapping category -> {'buy': float, 'sell': float, 'unit': str}.

    Returns:
        Tuple of:
          - active_holdings: Dict[asset_name, asset_metrics_dict]
          - summary: Dict containing total_cost, total_value, total_pnl, and pnl_pct.
    """
    holdings: Dict[str, Dict[str, Any]] = {}

    # Sort chronologically to preserve moving average accuracy
    sorted_txs = sorted(transactions, key=lambda x: str(x.get("date", "")))

    for r in sorted_txs:
        asset = r.get("asset", "").strip()
        if not asset:
            continue
        category = r.get("category", "Vàng")
        unit = r.get("unit", "Lượng")
        action = r.get("action", "Mua")
        qty = float(r.get("quantity", 0.0))
        total = float(r.get("total", 0.0))

        if asset not in holdings:
            holdings[asset] = {
                "asset": asset,
                "category": category,
                "qty": 0.0,
                "cost": 0.0,
                "unit": unit,
            }

        if action == "Mua":
            holdings[asset]["qty"] += qty
            holdings[asset]["cost"] += total
        else:  # Sell
            current_qty = holdings[asset]["qty"]
            if current_qty > 0:
                avg_unit_cost = holdings[asset]["cost"] / current_qty
                holdings[asset]["qty"] -= qty
                holdings[asset]["cost"] -= qty * avg_unit_cost

                # Mitigate floating point rounding artifacts near zero
                if holdings[asset]["qty"] < 1e-9:
                    holdings[asset]["qty"] = 0.0
                    holdings[asset]["cost"] = 0.0

    total_cost = 0.0
    total_value = 0.0
    total_pnl = 0.0
    active_holdings: Dict[str, Dict[str, Any]] = {}

    for asset, h in holdings.items():
        if h["qty"] <= 0:
            continue

        avg_price = h["cost"] / h["qty"] if h["qty"] > 0 else 0.0
        cat = h["category"]
        price_info = current_prices.get(cat, {"buy": 0.0, "sell": 0.0, "unit": "Lượng"})
        market_buy_price = float(price_info.get("buy", 0.0))
        price_unit = price_info.get("unit", "Lượng")

        # Convert category benchmark price to asset unit
        if market_buy_price > 0:
            ratio = get_unit_factor(price_unit) / get_unit_factor(h["unit"])
            asset_market_price = market_buy_price / ratio if ratio > 0 else market_buy_price
        else:
            asset_market_price = 0.0

        current_val = h["qty"] * asset_market_price
        pnl = current_val - h["cost"] if asset_market_price > 0 else 0.0
        pnl_pct = (pnl / h["cost"] * 100) if (h["cost"] > 0 and asset_market_price > 0) else 0.0

        h["avg_price"] = avg_price
        h["market_price"] = asset_market_price
        h["current_value"] = current_val
        h["pnl"] = pnl
        h["pnl_pct"] = pnl_pct

        total_cost += h["cost"]
        if asset_market_price > 0:
            total_value += current_val
            total_pnl += pnl
        else:
            total_value += h["cost"]

        active_holdings[asset] = h

    overall_roi = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
    summary = {
        "total_cost": total_cost,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "pnl_pct": overall_roi,
    }

    return active_holdings, summary


def load_market_prices() -> Dict[str, Dict[str, Any]]:
    """Load benchmark market prices from JSON storage."""
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "Vàng" in data and "Bạc" in data:
                    return data
        except Exception:
            pass

    default_prices = {
        "Vàng": {"buy": 80000000.0, "sell": 81000000.0, "unit": "Lượng"},
        "Bạc": {"buy": 1000000.0, "sell": 1050000.0, "unit": "Lượng"},
    }
    save_market_prices(default_prices)
    return default_prices


def save_market_prices(prices: Dict[str, Any]) -> None:
    """Save benchmark market prices atomically to JSON storage."""
    _atomic_write_json(PRICES_FILE, prices)


def load_custom_assets() -> List[Dict[str, Any]]:
    """Load user-defined custom asset configurations."""
    if os.path.exists(CUSTOM_ASSETS_FILE):
        try:
            with open(CUSTOM_ASSETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            return []
    return []


def save_custom_assets(assets: List[Dict[str, Any]]) -> None:
    """Save user-defined custom asset configurations atomically to JSON storage."""
    _atomic_write_json(CUSTOM_ASSETS_FILE, assets)
