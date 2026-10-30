"""
Configuration settings, theme styling, typography, and default asset models.

Centralizes theme color palettes, unit conversion metrics, standard asset presets,
and normalization helpers for categories, actions, and bullion units.
"""

from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Typography & Font Definitions
# ---------------------------------------------------------------------------
FONT_MAIN: Tuple[str, int] = ("Segoe UI", 10)
FONT_BOLD: Tuple[str, int, str] = ("Segoe UI", 10, "bold")
FONT_BIG: Tuple[str, int, str] = ("Segoe UI", 20, "bold")
FONT_HUGE: Tuple[str, int, str] = ("Segoe UI", 28, "bold")

# ---------------------------------------------------------------------------
# Sleek Dark Palette (Tailwind Slate / Emerald / Amber inspired)
# ---------------------------------------------------------------------------
CLR_BG: str = "#0f172a"          # Deep background (Slate 900)
CLR_PANEL: str = "#1e293b"       # Card / Panel background (Slate 800)
CLR_ENTRY: str = "#334155"       # Input field background (Slate 700)
CLR_TEXT: str = "#f8fafc"        # Primary white text (Slate 50)
CLR_TEXT_MUTED: str = "#94a3b8"  # Secondary subdued text (Slate 400)
CLR_BORDER: str = "#475569"      # Surface outline (Slate 600)

CLR_GREEN: str = "#10b981"       # Profit / Bullish green (Emerald 500)
CLR_RED: str = "#ef4444"         # Loss / Bearish red (Red 500)
CLR_GOLD: str = "#f59e0b"        # Precious metals accent (Amber 500)
CLR_HEAD: str = "#818cf8"        # Section heading accent (Indigo 400)

# ---------------------------------------------------------------------------
# Asset Categories & Conversion Metrics
# ---------------------------------------------------------------------------
ASSET_CATEGORIES: List[str] = ["Gold", "Silver"]

# Standard Precious Metals Conversion Metric:
# 1 Troy Ounce = 31.1034768 grams.
# In Vietnam, 1 Tael (Luong / Cay) = 37.5 grams = 1.2057 Troy Ounces.
# 1 Tael = 10 Chi (Maces). Therefore 1 Chi = 0.12057 Troy Ounces.
CONVERSION_OUNCE_TO_TAEL: float = 1.2057
CONVERSION_OUNCE_TO_LUONG: float = CONVERSION_OUNCE_TO_TAEL  # Backward-compatibility alias

# Base unit multiplier relative to 1 Troy Ounce
UNIT_FACTORS: Dict[str, float] = {
    # Tael / Luong / Cay
    "tael": 1.2057,
    "taels": 1.2057,
    "lượng": 1.2057,
    "luong": 1.2057,
    "cây": 1.2057,
    "cay": 1.2057,
    # Chi / Mace
    "chi": 0.12057,
    "chỉ": 0.12057,
    "mace": 0.12057,
    "0.1 chi": 0.012057,
    "0.1 chỉ": 0.012057,
    "0.2 chi": 0.024114,
    "0.2 chỉ": 0.024114,
    "0.3 chi": 0.036171,
    "0.3 chỉ": 0.036171,
    "0.5 chi": 0.060285,
    "0.5 chỉ": 0.060285,
    "1 chi": 0.12057,
    "1 chỉ": 0.12057,
    "2 chi": 0.24114,
    "2 chỉ": 0.24114,
    "3 chi": 0.36171,
    "3 chỉ": 0.36171,
    "5 chi": 0.60285,
    "5 chỉ": 0.60285,
    # Troy Ounce
    "ounce": 1.0,
    "ounces": 1.0,
    "oz": 1.0,
    "troy ounce": 1.0,
    # Gram & Kilogram
    "gram": 0.0321507,
    "grams": 0.0321507,
    "g": 0.0321507,
    "kg": 32.1507,
}


def get_unit_factor(unit_name: str) -> float:
    """Return conversion factor relative to Troy Ounce for any recognized unit."""
    cleaned = str(unit_name).strip().lower()
    return UNIT_FACTORS.get(cleaned, 1.0)


def normalize_category(category_name: str) -> str:
    """Normalize asset category to standard English title ('Gold' or 'Silver')."""
    cleaned = str(category_name).strip().lower()
    if cleaned in ("vàng", "vang", "gold"):
        return "Gold"
    if cleaned in ("bạc", "bac", "silver"):
        return "Silver"
    return category_name.strip().title() if category_name else "Gold"


def normalize_action(action_name: str) -> str:
    """Normalize transaction action to standard English ('Buy' or 'Sell')."""
    cleaned = str(action_name).strip().lower()
    if cleaned in ("mua", "buy"):
        return "Buy"
    if cleaned in ("bán", "ban", "sell"):
        return "Sell"
    return action_name.strip().title() if action_name else "Buy"


def normalize_unit(unit_name: str) -> str:
    """Normalize unit string to clean English representation."""
    cleaned = str(unit_name).strip().lower()
    mapping = {
        "lượng": "Tael",
        "luong": "Tael",
        "cây": "Tael",
        "cay": "Tael",
        "tael": "Tael",
        "chỉ": "Chi",
        "chi": "Chi",
        "mace": "Chi",
        "0.1 chỉ": "0.1 Chi",
        "0.1 chi": "0.1 Chi",
        "0.2 chỉ": "0.2 Chi",
        "0.2 chi": "0.2 Chi",
        "0.3 chỉ": "0.3 Chi",
        "0.3 chi": "0.3 Chi",
        "0.5 chỉ": "0.5 Chi",
        "0.5 chi": "0.5 Chi",
        "1 chỉ": "1 Chi",
        "1 chi": "1 Chi",
        "2 chỉ": "2 Chi",
        "2 chi": "2 Chi",
        "3 chỉ": "3 Chi",
        "3 chi": "3 Chi",
        "5 chỉ": "5 Chi",
        "5 chi": "5 Chi",
        "ounce": "Ounce",
        "oz": "Ounce",
        "gram": "Gram",
        "g": "Gram",
    }
    return mapping.get(cleaned, unit_name.strip())


# ---------------------------------------------------------------------------
# Default Built-in Seed Assets (100% English)
# ---------------------------------------------------------------------------
DEFAULT_ASSETS: List[Dict[str, Any]] = [
    {
        "name": "SJC Gold Bar 9999",
        "category": "Gold",
        "unit": "Tael",
    },
    {
        "name": "Doji Round Gold Ring",
        "category": "Gold",
        "unit": "Chi",
    },
    {
        "name": "Global Spot Silver",
        "category": "Silver",
        "unit": "Tael",
    },
]
