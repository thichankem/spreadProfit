"""
spreadProfit - Physical Precious Metals & Multi-Asset Portfolio Tracker.

Offline-first personal bullion tracker with moving weighted average cost (MAC)
basis calculations, multi-unit conversions, and cloud backup integration.
"""

from spreadprofit.cloud import create_local_snapshot, sync_portfolio_to_cloud
from spreadprofit.config import (
    ASSET_CATEGORIES,
    DEFAULT_ASSETS,
    DEFAULT_UNIT,
    STANDARD_UNITS,
    UNIT_FACTORS,
    get_unit_factor,
    normalize_action,
    normalize_category,
    normalize_unit,
)
from spreadprofit.db import (
    calculate_portfolio,
    load_custom_assets,
    load_db,
    load_market_prices,
    next_id,
    save_custom_assets,
    save_db,
    save_market_prices,
)
from spreadprofit.ui.main import SpreadProfitApp, main

__version__ = "1.0.0"

__all__ = [
    "SpreadProfitApp",
    "main",
    "ASSET_CATEGORIES",
    "DEFAULT_ASSETS",
    "DEFAULT_UNIT",
    "STANDARD_UNITS",
    "UNIT_FACTORS",
    "get_unit_factor",
    "normalize_action",
    "normalize_category",
    "normalize_unit",
    "calculate_portfolio",
    "load_db",
    "save_db",
    "load_custom_assets",
    "save_custom_assets",
    "load_market_prices",
    "save_market_prices",
    "next_id",
    "create_local_snapshot",
    "sync_portfolio_to_cloud",
]
