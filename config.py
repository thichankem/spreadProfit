"""
Configuration settings, theme styling, typography, and default asset models.

Centralizes theme color palettes, unit conversion metrics, and standard asset presets.
All UI components source typography and visual variables from this module.
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
ASSET_CATEGORIES: List[str] = ["Vàng", "Bạc"]

# 1 Troy Ounce = 31.1034768 grams.
# In Vietnam, 1 Luong (Cay) = 37.5 grams = 1.2057 Troy Ounces.
# Therefore: 1 Luong price = 1 Ounce price * 1.2057.
CONVERSION_OUNCE_TO_LUONG: float = 1.2057

# Base unit multiplier relative to 1 Troy Ounce
UNIT_FACTORS: Dict[str, float] = {
    "lượng": 1.2057,
    "luong": 1.2057,
    "cây": 1.2057,
    "cay": 1.2057,
    "chỉ": 0.12057,
    "chi": 0.12057,
    "0.1 chỉ": 0.012057,
    "0.1 chi": 0.012057,
    "0.2 chỉ": 0.024114,
    "0.2 chi": 0.024114,
    "0.3 chỉ": 0.036171,
    "0.3 chi": 0.036171,
    "0.5 chỉ": 0.060285,
    "0.5 chi": 0.060285,
    "2 chỉ": 0.24114,
    "2 chi": 0.24114,
    "3 chỉ": 0.36171,
    "3 chi": 0.36171,
    "5 chỉ": 0.60285,
    "5 chi": 0.60285,
    "ounce": 1.0,
    "oz": 1.0,
    "gram": 0.0321507,
    "g": 0.0321507,
}


def get_unit_factor(unit_name: str) -> float:
    """Return conversion factor relative to Troy Ounce for any recognized unit."""
    cleaned = str(unit_name).strip().lower()
    return UNIT_FACTORS.get(cleaned, 1.0)


# ---------------------------------------------------------------------------
# Default Built-in Seed Assets
# ---------------------------------------------------------------------------
DEFAULT_ASSETS: List[Dict[str, Any]] = [
    {
        "name": "Vàng miếng SJC",
        "category": "Vàng",
        "unit": "Lượng",
    },
    {
        "name": "Vàng nhẫn Doji",
        "category": "Vàng",
        "unit": "Chỉ",
    },
    {
        "name": "Bạc Thế Giới",
        "category": "Bạc",
        "unit": "Lượng",
    },
]
