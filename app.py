# app.py
"""
Điểm khởi chạy chính của ứng dụng Quản lý tài sản cá nhân local.
Thiết kế theo chuẩn sạch (Clean Code), tách biệt giao diện và logic tính toán.
"""

from ui_main import GoldTrackerApp

if __name__ == "__main__":
    app = GoldTrackerApp()
    app.mainloop()