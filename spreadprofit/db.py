"""
Database management, atomic I/O, and moving average cost basis calculations.

Handles persistent JSON storage for transactions, custom assets, and benchmark market quotes.
Provides robust Weighted Average Cost (MAC) basis calculations for physical bullion holdings.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from spreadprofit.config import (
    get_unit_factor,
    normalize_action,
    normalize_category,
    normalize_unit,
)

APP_NAME = "spreadProfit"
DATA_FILE_NAMES = ("gold_transactions.json", "market_prices.json", "custom_assets.json")

# Resolve base execution directory (supports standalone frozen exe and standard package runs)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    _pkg_dir = os.path.dirname(os.path.abspath(__file__))
    _parent = os.path.dirname(_pkg_dir)
    if os.path.exists(os.path.join(_parent, "data")):
        BASE_DIR = _parent
    elif os.path.exists(os.path.join(_pkg_dir, "data")):
        BASE_DIR = _pkg_dir
    else:
        BASE_DIR = _parent
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
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as f:
            tmp_file = f.name
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        shutil.move(tmp_file, file_path)
    except Exception:
        if tmp_file and os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass
        raise


def _seed_file_if_missing(file_path: str, seed_name: str, fallback_data: Any) -> None:
    """Seed data file from bundled resources or fallback defaults if not yet present."""
    if os.path.exists(file_path):
        return

    # Check for seed file in frozen bundle or local _seed directory
    bundled_seed_candidates = (
        os.path.join(BUNDLE_DIR, "_seed", seed_name),
        os.path.join(BUNDLE_DIR, "data", seed_name),
        os.path.join(BUNDLE_DIR, seed_name),
    )
    for candidate in bundled_seed_candidates:
        if os.path.exists(candidate):
            try:
                shutil.copyfile(candidate, file_path)
                return
            except Exception:
                pass

    # Fallback to in-memory defaults
    _atomic_write_json(file_path, fallback_data)


DB_FILE = os.path.join(DATA_DIR, "gold_transactions.json")
PRICES_FILE = os.path.join(DATA_DIR, "market_prices.json")
CUSTOM_ASSETS_FILE = os.path.join(DATA_DIR, "custom_assets.json")

# Ensure files exist with clean initial structures
_seed_file_if_missing(DB_FILE, "gold_transactions.json", [])
_seed_file_if_missing(
    PRICES_FILE,
    "market_prices.json",
    {
        "Gold": {"buy": 2750.0, "sell": 2775.0, "unit": "Ounce"},
        "Silver": {"buy": 33.5, "sell": 34.5, "unit": "Ounce"},
    },
)
_seed_file_if_missing(CUSTOM_ASSETS_FILE, "custom_assets.json", [])


def load_db() -> List[Dict[str, Any]]:
    """Load transaction records from persistent storage, applying English normalization."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            # Normalize schema to standard English
            for item in data:
                item["category"] = normalize_category(item.get("category", "Gold"))
                item["action"] = normalize_action(item.get("action", "Buy"))
                item["unit"] = normalize_unit(item.get("unit", "Ounce"))
            return data
    except Exception:
        return []


def save_db(data: List[Dict[str, Any]]) -> None:
    """Save transaction ledger atomically."""
    _atomic_write_json(DB_FILE, data)


def load_custom_assets() -> List[Dict[str, Any]]:
    """Load user-defined custom asset presets."""
    if not os.path.exists(CUSTOM_ASSETS_FILE):
        return []
    try:
        with open(CUSTOM_ASSETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    item["category"] = normalize_category(item.get("category", "Gold"))
                    item["unit"] = normalize_unit(item.get("unit", "Ounce"))
                return data
            return []
    except Exception:
        return []


def save_custom_assets(data: List[Dict[str, Any]]) -> None:
    """Persist user-defined asset presets atomically."""
    _atomic_write_json(CUSTOM_ASSETS_FILE, data)


def next_id(db: List[Dict[str, Any]]) -> int:
    """Generate sequential primary key for a new transaction entry."""
    if not db:
        return 1
    return max(item.get("id", 0) for item in db) + 1


def calculate_portfolio(
    transactions: List[Dict[str, Any]],
    current_prices: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, float]]:
    """
    Calculate portfolio holdings, weighted cost basis, and unrealized returns.

    Uses chronological Moving Weighted Average Cost (MAC) to accurately account
    for staggered acquisitions and partial divestments.

    Returns:
        Tuple of (active_holdings_dict, portfolio_summary_dict)
    """
    holdings: Dict[str, Dict[str, Any]] = {}

    # Sort transactions chronologically to enforce accurate moving cost basis
    sorted_txs = sorted(
        transactions,
        key=lambda x: (str(x.get("date", "")), int(x.get("id", 0))),
    )

    for tx in sorted_txs:
        asset = tx["asset"].strip()
        cat = normalize_category(tx.get("category", "Gold"))
        action = normalize_action(tx.get("action", "Buy"))
        qty = float(tx.get("quantity", 0.0))
        unit = normalize_unit(tx.get("unit", "Ounce"))
        total = float(tx.get("total", 0.0))

        if asset not in holdings:
            holdings[asset] = {
                "asset": asset,
                "category": cat,
                "qty": 0.0,
                "cost": 0.0,
                "unit": unit,
            }

        h = holdings[asset]

        # Convert quantity if recorded under alternate unit for same asset
        if h["unit"] != unit:
            conv_ratio = get_unit_factor(unit) / get_unit_factor(h["unit"])
            qty = qty * conv_ratio

        if action == "Buy":
            h["qty"] += qty
            h["cost"] += total
        elif action == "Sell":
            if h["qty"] > 0:
                avg_cost_before_sell = h["cost"] / h["qty"]
                h["qty"] -= qty
                if h["qty"] <= 1e-9:
                    h["qty"] = 0.0
                    h["cost"] = 0.0
                else:
                    h["cost"] = h["qty"] * avg_cost_before_sell
            else:
                h["qty"] -= qty

    total_cost = 0.0
    total_value = 0.0
    total_pnl = 0.0
    active_holdings: Dict[str, Dict[str, Any]] = {}

    for asset, h in holdings.items():
        if h["qty"] <= 0:
            continue

        avg_price = h["cost"] / h["qty"] if h["qty"] > 0 else 0.0
        cat = h["category"]

        # Resolve benchmark price supporting both English and legacy aliases
        price_info = current_prices.get(cat)
        if not price_info:
            if cat == "Gold":
                price_info = current_prices.get("Vàng")
            elif cat == "Silver":
                price_info = current_prices.get("Bạc")
        if not price_info:
            price_info = {"buy": 0.0, "sell": 0.0, "unit": "Ounce"}

        market_buy_price = float(price_info.get("buy", 0.0))
        price_unit = normalize_unit(price_info.get("unit", "Ounce"))

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
    """Load benchmark market prices from JSON storage with English normalization."""
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    normalized: Dict[str, Dict[str, Any]] = {}
                    # Migrate legacy keys if present
                    if "Gold" in data:
                        normalized["Gold"] = data["Gold"]
                    elif "Vàng" in data:
                        normalized["Gold"] = data["Vàng"]

                    if "Silver" in data:
                        normalized["Silver"] = data["Silver"]
                    elif "Bạc" in data:
                        normalized["Silver"] = data["Bạc"]

                    if "Gold" in normalized and "Silver" in normalized:
                        for cat_key in ("Gold", "Silver"):
                            normalized[cat_key]["unit"] = normalize_unit(
                                normalized[cat_key].get("unit", "Ounce")
                            )
                        return normalized
        except Exception:
            pass

    default_prices = {
        "Gold": {"buy": 2750.0, "sell": 2775.0, "unit": "Ounce"},
        "Silver": {"buy": 33.5, "sell": 34.5, "unit": "Ounce"},
    }
    save_market_prices(default_prices)
    return default_prices


def save_market_prices(prices: Dict[str, Dict[str, Any]]) -> None:
    """Save benchmark market quotes atomically."""
    _atomic_write_json(PRICES_FILE, prices)
