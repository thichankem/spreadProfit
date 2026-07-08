# ui_main.py
"""
Giao diện chính của ứng dụng Quản lý tài sản (GoldTrackerApp).
Chịu trách nhiệm khởi tạo các Tab, quản lý cơ sở dữ liệu chung và điều phối luồng cập nhật giá API.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from config import *
from db_manager import load_db, save_db, load_market_prices
from ui_portfolio import PortfolioTab
from ui_transactions import TransactionsTab
from ui_charts import ChartsTab

class GoldTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("💰 Quản lý Tài Sản Cá Nhân Local – Vàng/Bạc/Cổ Phiếu/Crypto")
        self.geometry("1240x800")
        self.configure(bg=CLR_BG)
        self.resizable(True, True)

        # Thiết lập icon ứng dụng (hỗ trợ Windows .ico và đa nền tảng .png)
        import os
        try:
            icon_ico = os.path.join(os.path.dirname(__file__), "app_icon.ico")
            icon_png = os.path.join(os.path.dirname(__file__), "app_icon.png")
            if os.path.exists(icon_ico):
                self.iconbitmap(icon_ico)
            elif os.path.exists(icon_png):
                img = tk.PhotoImage(file=icon_png)
                self.iconphoto(False, img)
        except Exception as e:
            print(f"Không thể tải icon: {e}")

        # 1. Tải cơ sở dữ liệu JSON
        self.db = load_db()

        # 2. Khởi tạo và tải giá thị trường từ file nội bộ (offline)
        self.current_prices = load_market_prices()

        # Biến trạng thái hiển thị thanh trạng thái
        self.var_status = tk.StringVar(value="Sẵn sàng (Ngoại tuyến).")

        # 3. Thiết kế giao diện chính
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        # ────────── THANH TIÊU ĐỀ TRÊN CÙNG (Sleek Dark Theme) ──────────
        top_bar = tk.Frame(self, bg=CLR_PANEL, pady=12, bd=0, highlightbackground=CLR_BORDER, highlightthickness=1)
        top_bar.pack(fill="x")
        
        title_lbl = tk.Label(top_bar, text="💰  QUẢN LÝ TÀI SẢN CÁ NHÂN",
                             font=("Segoe UI", 18, "bold"), bg=CLR_PANEL, fg=CLR_GOLD)
        title_lbl.pack()
        
        subtitle_lbl = tk.Label(top_bar, text="Hệ thống Quản lý Danh mục & Tính Lợi nhuận Offline Bảo mật",
                                font=("Segoe UI", 10, "italic"), bg=CLR_PANEL, fg=CLR_TEXT_MUTED)
        subtitle_lbl.pack(pady=(2, 0))

        # ────────── KHUNG CHỨA CÁC TAB CHÍNH ──────────
        # Sử dụng ttk.Notebook để tạo các tab tiện lợi
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Khởi tạo các Tab
        self.tab_portfolio = PortfolioTab(self.notebook, self)
        self.tab_transactions = TransactionsTab(self.notebook, self)
        self.tab_charts = ChartsTab(self.notebook, self)

        # Thêm các tab vào Notebook
        self.notebook.add(self.tab_portfolio, text=" 💼  Danh mục & Lời/Lỗ ")
        self.notebook.add(self.tab_transactions, text=" 📝  Lịch sử giao dịch ")
        self.notebook.add(self.tab_charts, text=" 📈  Biểu đồ phân tích ")

        # Lắng nghe sự kiện chuyển Tab để tự động vẽ lại biểu đồ hoặc refresh bảng
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ────────── THANH TRẠNG THÁI DƯỚI CÙNG ──────────
        status_bar = tk.Frame(self, bg=CLR_PANEL, bd=1, relief="flat", highlightbackground=CLR_BORDER, highlightthickness=1)
        status_bar.pack(fill="x", side="bottom")

        lbl_status = tk.Label(status_bar, textvariable=self.var_status, font=("Segoe UI", 9),
                              bg=CLR_PANEL, fg=CLR_TEXT_MUTED, anchor="w")
        lbl_status.pack(side="left", padx=10, pady=5, fill="x", expand=True)

    def _apply_styles(self):
        """Thiết lập Style của ttk widget để đồng bộ giao diện tối phẳng (Clam Theme)."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Cấu hình Treeview (Bảng biểu)
        style.configure("Treeview",
                        background=CLR_PANEL,
                        foreground=CLR_TEXT,
                        fieldbackground=CLR_PANEL,
                        rowheight=26,
                        font=("Segoe UI", 9.5),
                        bordercolor=CLR_BORDER,
                        borderwidth=1)
        
        style.configure("Treeview.Heading",
                        background=CLR_ENTRY,
                        foreground=CLR_HEAD,
                        font=FONT_BOLD,
                        borderwidth=1,
                        relief="flat")
                        
        style.map("Treeview", 
                  background=[("selected", "#4f46e5")], # Màu nền xanh Indigo sáng đẹp khi chọn dòng
                  foreground=[("selected", "white")])
                  
        style.map("Treeview.Heading",
                  background=[("active", "#475569")],
                  foreground=[("active", "white")])

        # Cấu hình Tab (Notebook)
        style.configure("TNotebook", background=CLR_BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=CLR_PANEL,
                        foreground=CLR_TEXT_MUTED,
                        font=FONT_BOLD,
                        padding=[16, 8],
                        borderwidth=0,
                        focuscolor="")
                        
        style.map("TNotebook.Tab",
                  background=[("selected", CLR_BG)],
                  foreground=[("selected", CLR_GOLD)])

        # Cấu hình Combobox phẳng
        style.configure("TCombobox",
                        fieldbackground=CLR_ENTRY,
                        background=CLR_ENTRY,
                        foreground=CLR_TEXT,
                        bordercolor=CLR_BORDER,
                        lightcolor=CLR_BORDER,
                        darkcolor=CLR_BORDER,
                        arrowcolor=CLR_TEXT)
        style.map("TCombobox", 
                  fieldbackground=[("readonly", CLR_ENTRY)],
                  foreground=[("readonly", CLR_TEXT)])

        # Cấu hình thanh cuộn Scrollbar tối tối giản
        style.configure("Vertical.TScrollbar",
                        gripcount=0,
                        background=CLR_ENTRY,
                        darkcolor=CLR_PANEL,
                        lightcolor=CLR_PANEL,
                        troughcolor=CLR_BG,
                        bordercolor=CLR_BORDER,
                        arrowcolor=CLR_TEXT_MUTED)
                        
        style.configure("Horizontal.TScrollbar",
                        gripcount=0,
                        background=CLR_ENTRY,
                        darkcolor=CLR_PANEL,
                        lightcolor=CLR_PANEL,
                        troughcolor=CLR_BG,
                        bordercolor=CLR_BORDER,
                        arrowcolor=CLR_TEXT_MUTED)

    def _on_tab_changed(self, event):
        """Tự động làm mới dữ liệu/biểu đồ khi người dùng nhấp chọn Tab."""
        tab_idx = self.notebook.index(self.notebook.select())
        
        if tab_idx == 0:  # Tab Danh mục
            self.tab_portfolio.refresh_view()
        elif tab_idx == 1:  # Tab Giao dịch
            self.tab_transactions.refresh_table()
        elif tab_idx == 2:  # Tab Biểu đồ
            self.tab_charts.draw_charts()

    def refresh_prices(self):
        """Tải lại giá từ file lưu trữ cục bộ."""
        self.var_status.set("⏳ Đang nạp giá từ bộ nhớ cục bộ...")
        from db_manager import load_market_prices
        self.current_prices = load_market_prices()
        self.var_status.set("✅ Đã nạp giá từ bộ nhớ cục bộ (Ngoại tuyến).")
        self._refresh_current_active_tab()

    def _refresh_current_active_tab(self):
        """Làm mới dữ liệu của tab đang hiển thị."""
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 0:
            self.tab_portfolio.refresh_view()
        elif tab_idx == 1:
            self.tab_transactions.refresh_table()
        elif tab_idx == 2:
            self.tab_charts.draw_charts()

    def refresh_portfolio_view(self):
        """Cập nhật nhanh hiển thị danh mục sau khi thêm/xóa giao dịch."""
        self.tab_portfolio.refresh_view()
        # Nếu đang ở tab biểu đồ thì vẽ lại biểu đồ luôn
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 2:
            self.tab_charts.draw_charts()
