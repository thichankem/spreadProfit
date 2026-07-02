# ui_main.py
"""
Giao diện chính của ứng dụng Quản lý tài sản (GoldTrackerApp).
Chịu trách nhiệm khởi tạo các Tab, quản lý cơ sở dữ liệu chung và điều phối luồng cập nhật giá API.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from config import *
from db_manager import load_db, save_db
from api_service import fetch_all_prices_threaded, get_usdvnd_rate
from ui_portfolio import PortfolioTab
from ui_transactions import TransactionsTab
from ui_prices import PricesTab
from ui_charts import ChartsTab

class GoldTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("💰 Quản lý Tài Sản Cá Nhân Local – Vàng/Bạc/Cổ Phiếu/Crypto")
        self.geometry("1240x800")
        self.configure(bg=CLR_BG)
        self.resizable(True, True)

        # 1. Tải cơ sở dữ liệu JSON
        self.db = load_db()

        # 2. Khởi tạo biến trạng thái giá thị trường
        # Cấu trúc: {ticker: {"buy": float, "sell": float}}
        self.current_prices = {}
        
        # Điền sẵn giá trị ban đầu bằng 0 cho các default assets
        for item in DEFAULT_ASSETS:
            self.current_prices[item["ticker"]] = {"buy": 0.0, "sell": 0.0}

        # Biến trạng thái hiển thị thanh trạng thái
        self.var_status = tk.StringVar(value="Sẵn sàng.")

        # 3. Thiết kế giao diện chính
        self._build_ui()
        self._apply_styles()

        # 4. Kích hoạt lấy giá trực tuyến ngay khi mở ứng dụng (chạy ngầm)
        self.refresh_prices()

    def _build_ui(self):
        # ────────── THANH TIÊU ĐỀ TRÊN CÙNG ──────────
        top_bar = tk.Frame(self, bg=CLR_GOLD, pady=8)
        top_bar.pack(fill="x")
        
        title_lbl = tk.Label(top_bar, text="💰  QUẢN LÝ TÀI SẢN CÁ NHÂN LOCAL",
                             font=("Segoe UI", 15, "bold"), bg=CLR_GOLD, fg="white")
        title_lbl.pack()
        
        subtitle_lbl = tk.Label(top_bar, text="Tính Lời/Lỗ Thực Tế Theo Spread & Cập Nhật Giá Tự Động Qua API",
                                font=("Segoe UI", 10, "italic"), bg=CLR_GOLD, fg="#fff8dc")
        subtitle_lbl.pack()

        # ────────── KHUNG CHỨA CÁC TAB CHÍNH ──────────
        # Sử dụng ttk.Notebook để tạo các tab tiện lợi
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Khởi tạo các Tab
        self.tab_portfolio = PortfolioTab(self.notebook, self)
        self.tab_transactions = TransactionsTab(self.notebook, self)
        self.tab_prices = PricesTab(self.notebook, self)
        self.tab_charts = ChartsTab(self.notebook, self)

        # Thêm các tab vào Notebook
        self.notebook.add(self.tab_portfolio, text=" 💼  Danh mục & Lời/Lỗ ")
        self.notebook.add(self.tab_transactions, text=" 📝  Lịch sử giao dịch ")
        self.notebook.add(self.tab_prices, text=" 📊  Bảng giá thị trường ")
        self.notebook.add(self.tab_charts, text=" 📈  Biểu đồ phân tích ")

        # Lắng nghe sự kiện chuyển Tab để tự động vẽ lại biểu đồ hoặc refresh bảng
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ────────── THANH TRẠNG THÁI DƯỚI CÙNG ──────────
        status_bar = tk.Frame(self, bg=CLR_PANEL, bd=1, relief="flat", highlightbackground=CLR_BORDER, highlightthickness=1)
        status_bar.pack(fill="x", side="bottom")

        lbl_status = tk.Label(status_bar, textvariable=self.var_status, font=("Segoe UI", 9),
                              bg=CLR_PANEL, fg=CLR_TEXT_MUTED, anchor="w")
        lbl_status.pack(side="left", padx=10, pady=5, fill="x", expand=True)

        self.btn_refresh_global = tk.Button(status_bar, text="🔄 Cập nhật giá", command=self.refresh_prices,
                                            bg="#4f46e5", fg="white", font=("Segoe UI", 8, "bold"),
                                            relief="flat", padx=10, pady=3, cursor="hand2")
        self.btn_refresh_global.pack(side="right", padx=10, pady=3)

    def _apply_styles(self):
        """Thiết lập Style của ttk widget để đồng bộ giao diện tối (Dark Theme)."""
        style = ttk.Style()
        style.theme_use("default")
        
        # Cấu hình Treeview (Bảng biểu)
        style.configure("Treeview",
                        background=CLR_PANEL,
                        foreground=CLR_TEXT,
                        fieldbackground=CLR_PANEL,
                        rowheight=24,
                        font=("Consolas", 9.5))
        style.configure("Treeview.Heading",
                        background=CLR_ENTRY,
                        foreground=CLR_HEAD,
                        font=FONT_BOLD,
                        borderwidth=1)
        style.map("Treeview", background=[("selected", "#334155")]) # Màu xám xanh khi chọn dòng

        # Cấu hình Tab (Notebook)
        style.configure("TNotebook", background=CLR_BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=CLR_PANEL,
                        foreground=CLR_TEXT_MUTED,
                        font=FONT_BOLD,
                        padding=[12, 6],
                        borderwidth=1,
                        relief="flat")
        style.map("TNotebook.Tab",
                  background=[("selected", CLR_BG)],
                  foreground=[("selected", CLR_GOLD)])

        # Cấu hình Combobox
        style.configure("TCombobox",
                        fieldbackground=CLR_ENTRY,
                        background=CLR_ENTRY,
                        foreground=CLR_TEXT,
                        selectbackground=CLR_ENTRY)

    def _on_tab_changed(self, event):
        """Tự động làm mới dữ liệu/biểu đồ khi người dùng nhấp chọn Tab."""
        tab_idx = self.notebook.index(self.notebook.select())
        
        if tab_idx == 0:  # Tab Danh mục
            self.tab_portfolio.refresh_view()
        elif tab_idx == 1:  # Tab Giao dịch
            self.tab_transactions.refresh_table()
        elif tab_idx == 2:  # Tab Bảng giá
            self.tab_prices.refresh_table()
        elif tab_idx == 3:  # Tab Biểu đồ
            self.tab_charts.draw_charts()

    def refresh_prices(self):
        """Khởi chạy luồng chạy ngầm để lấy giá tài sản thực tế từ Internet."""
        self.var_status.set("⏳ Đang tải giá trực tuyến mới nhất qua API...")
        self.btn_refresh_global.configure(state="disabled", bg="#6b7280")

        # Thu thập các ticker cần lấy giá: default + các ticker người dùng tự thêm trong DB
        tickers_to_fetch = []
        seen_tickers = set()

        # Thêm từ default
        for item in DEFAULT_ASSETS:
            if item["ticker"] not in seen_tickers:
                tickers_to_fetch.append({
                    "ticker": item["ticker"],
                    "category": item["category"],
                    "unit": item["unit"]
                })
                seen_tickers.add(item["ticker"])

        # Thêm từ DB thực tế
        for r in self.db:
            ticker = r.get("ticker", "")
            if ticker and ticker not in seen_tickers:
                tickers_to_fetch.append({
                    "ticker": ticker,
                    "category": r.get("category", "Khác"),
                    "unit": r["unit"]
                })
                seen_tickers.add(ticker)

        # Chạy Threading ngầm lấy giá tránh làm đơ giao diện chính
        fetch_all_prices_threaded(tickers_to_fetch, self._on_prices_fetched)

    def _on_prices_fetched(self, results):
        """Hàm callback chạy trên luồng chính khi tải giá hoàn tất."""
        # Cập nhật kết quả vào từ điển giá hiện tại của ứng dụng
        self.current_prices.update(results)
        
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.var_status.set(f"✅ Đã cập nhật giá trực tuyến lúc {now}.")
        
        # Bật lại nút Cập nhật
        self.btn_refresh_global.configure(state="normal", bg="#4f46e5")

        # Refresh lại màn hình tab hiện tại đang mở
        self._refresh_current_active_tab()

    def _refresh_current_active_tab(self):
        """Làm mới dữ liệu của tab đang hiển thị."""
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 0:
            self.tab_portfolio.refresh_view()
        elif tab_idx == 1:
            self.tab_transactions.refresh_table()
        elif tab_idx == 2:
            self.tab_prices.refresh_table()
        elif tab_idx == 3:
            self.tab_charts.draw_charts()

    def refresh_portfolio_view(self):
        """Cập nhật nhanh hiển thị danh mục sau khi thêm/xóa giao dịch."""
        self.tab_portfolio.refresh_view()
        # Nếu đang ở tab biểu đồ thì vẽ lại biểu đồ luôn
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 3:
            self.tab_charts.draw_charts()
