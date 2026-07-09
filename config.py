# config.py
"""
Cấu hình giao diện, màu sắc và thiết lập loại tài sản mặc định cho ứng dụng.
"""

# Giao diện và Font chữ
FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_BIG  = ("Segoe UI", 20, "bold")
FONT_HUGE = ("Segoe UI", 28, "bold")

# Hệ thống màu sắc Dark Mode cao cấp
CLR_BG        = "#0f172a"  # Nền tối sâu (Slate 900)
CLR_PANEL     = "#1e293b"  # Nền panel (Slate 800)
CLR_ENTRY     = "#334155"  # Nền ô nhập liệu (Slate 700)
CLR_TEXT      = "#f8fafc"  # Chữ trắng sáng (Slate 50)
CLR_TEXT_MUTED = "#94a3b8" # Chữ mờ (Slate 400)
CLR_BORDER    = "#475569"  # Màu viền (Slate 600)

CLR_GREEN     = "#10b981"  # Xanh ngọc bích phát tài (Emerald 500)
CLR_RED       = "#ef4444"  # Đỏ san hô giảm lỗ (Red 500)
CLR_GOLD      = "#f59e0b"  # Vàng kim loại quý (Amber 500)
CLR_HEAD      = "#818cf8"  # Tím nhạt cho tiêu đề (Indigo 400)

# Danh mục nhóm tài sản
ASSET_CATEGORIES = ["Vàng", "Bạc"]

# Tỷ giá chuyển đổi
# 1 Ounce vàng/bạc troy = 31.1034768 grams.
# Ở Việt Nam, 1 Lượng (cây) = 37.5 grams = 1.2057 Ounce troy.
# Do đó, giá 1 lượng = giá 1 ounce * 1.2057.
CONVERSION_OUNCE_TO_LUONG = 1.2057

# Tài sản mặc định cấu hình sẵn trong hệ thống
DEFAULT_ASSETS = [
    {
        "name": "Vàng miếng SJC",
        "category": "Vàng",
        "unit": "Lượng"
    },
    {
        "name": "Vàng nhẫn Doji",
        "category": "Vàng",
        "unit": "Chỉ"
    },
    {
        "name": "Bạc Thế Giới",
        "category": "Bạc",
        "unit": "Lượng"
    }
]
