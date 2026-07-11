# app.py
"""
Điểm khởi chạy chính của ứng dụng Quản lý tài sản cá nhân local.
Thiết kế theo chuẩn sạch (Clean Code), tách biệt giao diện và logic tính toán.
"""

import ctypes
from ui_main import GoldTrackerApp

if __name__ == "__main__":
    # Tự động kích hoạt DPI Awareness trên Windows để sửa lỗi giao diện bị mờ (High DPI scaling)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware() # Fallback cho phiên bản Windows cũ hơn
        except Exception:
            pass

    app = GoldTrackerApp()
    app.mainloop()