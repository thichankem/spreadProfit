# ui_portfolio.py
"""
Tab hiển thị Dashboard Danh mục đầu tư, Lời/Lỗ thực tế và Giả lập chốt lời (What-if).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from db_manager import calculate_portfolio

class PortfolioTab(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app
        
        self.var_wi_asset = tk.StringVar()
        self.var_wi_target_price = tk.StringVar()
        self.var_wi_result = tk.StringVar(value="Nhập giá giả lập chốt lời để tính lợi nhuận dự tính.")

        self._build_ui()

    def _build_ui(self):
        # ────────── PHẦN TRÊN: DASHBOARD CARD SỐ LIỆU TỔNG QUAN ──────────
        cards_frame = tk.Frame(self, bg=CLR_BG)
        cards_frame.pack(fill="x", padx=10, pady=10)
        
        for c in range(4):
            cards_frame.columnconfigure(c, weight=1)

        # Helper tạo Card
        def create_card(parent, title, bg_color, col):
            card = tk.Frame(parent, bg=CLR_PANEL, bd=0, relief="solid", highlightbackground=CLR_BORDER, highlightthickness=1, padx=12, pady=10)
            card.grid(row=0, column=col, sticky="ew", padx=6)
            
            lbl_title = tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), bg=CLR_PANEL, fg=CLR_TEXT_MUTED)
            lbl_title.pack(anchor="w")
            
            lbl_value = tk.Label(card, text="—", font=("Segoe UI", 16, "bold"), bg=CLR_PANEL, fg=CLR_TEXT)
            lbl_value.pack(anchor="w", pady=(3,0))
            return lbl_value

        self.card_cost = create_card(cards_frame, "TỔNG VỐN ĐÃ ĐẦU TƯ", CLR_PANEL, 0)
        self.card_value = create_card(cards_frame, "GIÁ TRỊ DANH MỤC HIỆN TẠI", CLR_PANEL, 1)
        self.card_pnl = create_card(cards_frame, "LỜI / LỖ TẠM TÍNH", CLR_PANEL, 2)
        self.card_pnl_pct = create_card(cards_frame, "TỶ SUẤT LỢI NHUẬN (ROI)", CLR_PANEL, 3)

        # ────────── PHẦN GIỮA: BẢNG CHI TIẾT TÀI SẢN NẮM GIỮ ──────────
        table_label = tk.Label(self, text="💼  DANH MỤC CHI TIẾT CÁC TÀI SẢN ĐANG NẮM GIỮ",
                               font=FONT_BOLD, bg=CLR_BG, fg=CLR_HEAD, anchor="w")
        table_label.pack(fill="x", padx=10, pady=(10, 5))

        table_frame = tk.Frame(self, bg=CLR_PANEL, bd=1, relief="flat", highlightbackground=CLR_BORDER, highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("Asset", "Category", "Qty", "Unit", "AvgCost", "MarketPrice", "TotalCost", "CurrentValue", "PnL", "PnLPct")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10, selectmode="browse")
        
        self.tree.heading("Asset", text="Tên tài sản")
        self.tree.heading("Category", text="Nhóm")
        self.tree.heading("Qty", text="SL Nắm giữ")
        self.tree.heading("Unit", text="ĐV")
        self.tree.heading("AvgCost", text="Giá vốn BQ")
        self.tree.heading("MarketPrice", text="Giá thị trường")
        self.tree.heading("TotalCost", text="Tổng vốn")
        self.tree.heading("CurrentValue", text="Giá trị bán ngay")
        self.tree.heading("PnL", text="Lời/Lỗ")
        self.tree.heading("PnLPct", text="% Lời/Lỗ")

        self.tree.column("Asset", width=180, anchor="w")
        self.tree.column("Category", width=80, anchor="center")
        self.tree.column("Qty", width=80, anchor="center")
        self.tree.column("Unit", width=50, anchor="center")
        self.tree.column("AvgCost", width=120, anchor="e")
        self.tree.column("MarketPrice", width=120, anchor="e")
        self.tree.column("TotalCost", width=120, anchor="e")
        self.tree.column("CurrentValue", width=120, anchor="e")
        self.tree.column("PnL", width=130, anchor="e")
        self.tree.column("PnLPct", width=95, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("green", foreground="#34d399")  # Xanh lá sáng
        self.tree.tag_configure("red", foreground="#f87171")    # Đỏ sáng

        # ────────── PHẦN DƯỚI: GIẢ LẬP CHỐT LỜI (WHAT-IF CALCULATOR) ──────────
        wi_frame = tk.LabelFrame(self, text=" 🔮  GIẢ LẬP CHỐT LỜI (WHAT-IF SIMULATOR) ", font=FONT_BOLD,
                                   bg=CLR_PANEL, fg=CLR_GOLD, bd=1, relief="solid", padx=10, pady=8)
        wi_frame.pack(fill="x", padx=10, pady=10)

        wi_grid = tk.Frame(wi_frame, bg=CLR_PANEL)
        wi_grid.pack(fill="x")

        tk.Label(wi_grid, text="Chọn tài sản đang có:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cb_wi_asset = ttk.Combobox(wi_grid, textvariable=self.var_wi_asset, state="readonly", font=FONT_MAIN, width=28)
        self.cb_wi_asset.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(wi_grid, text="Nếu giá BÁN RA lên đến (đ):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=2, sticky="e", padx=15, pady=5)
        self.ent_target = tk.Entry(wi_grid, textvariable=self.var_wi_target_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, width=18, bd=3)
        self.ent_target.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        btn_calc = tk.Button(wi_grid, text="▶ Tính toán ngay", command=self._calculate_whatif,
                             bg=CLR_GREEN, fg="white", font=FONT_BOLD, relief="flat", padx=12, pady=3, cursor="hand2")
        btn_calc.grid(row=0, column=4, padx=15)

        # Label kết quả giả lập
        self.lbl_result = tk.Label(wi_frame, textvariable=self.var_wi_result, font=FONT_BOLD, bg=CLR_PANEL, fg=CLR_TEXT, justify="left", anchor="w", wraplength=1000)
        self.lbl_result.pack(fill="x", padx=10, pady=(8, 4))

        # Lưu trữ giữ liệu danh mục để phục vụ What-If
        self.active_holdings = {}

    def refresh_view(self):
        """Tính toán lại danh mục đầu tư và hiển thị dữ liệu mới lên màn hình."""
        # 1. Thực hiện tính toán
        self.active_holdings, summary = calculate_portfolio(self.main_app.db, self.main_app.current_prices)

        # 2. Cập nhật thẻ Dashboard Số liệu lớn
        self.card_cost.configure(text=f"{summary['total_cost']:,.0f} đ")
        self.card_value.configure(text=f"{summary['total_value']:,.0f} đ")
        
        # Thẻ Lời lỗ ròng
        pnl = summary['total_pnl']
        sign = "+" if pnl >= 0 else ""
        self.card_pnl.configure(text=f"{sign}{pnl:,.0f} đ")
        self.card_pnl.configure(fg=CLR_GREEN if pnl >= 0 else CLR_RED)
        
        # Thẻ Tỷ lệ P&L
        pnl_pct = summary['pnl_pct']
        sign_pct = "+" if pnl_pct >= 0 else ""
        self.card_pnl_pct.configure(text=f"{sign_pct}{pnl_pct:,.2f}%")
        self.card_pnl_pct.configure(fg=CLR_GREEN if pnl_pct >= 0 else CLR_RED)

        # 3. Cập nhật bảng dữ liệu nắm giữ
        for row in self.tree.get_children():
            self.tree.delete(row)

        for asset, h in sorted(self.active_holdings.items(), key=lambda x: (x[1]["category"], x[0])):
            tag = "green" if h["pnl"] >= 0 else "red"
            sign_item = "+" if h["pnl"] >= 0 else ""
            sign_pct_item = "+" if h["pnl_pct"] >= 0 else ""
            
            pnl_str = f"{sign_item}{h['pnl']:,.0f}đ" if h["market_price"] > 0 else "—"
            pnl_pct_str = f"{sign_pct_item}{h['pnl_pct']:.2f}%" if h["market_price"] > 0 else "—"
            market_price_str = f"{h['market_price']:,.0f}" if h["market_price"] > 0 else "—"
            current_value_str = f"{h['current_value']:,.0f}" if h["market_price"] > 0 else "—"

            self.tree.insert("", "end", tag=tag, values=(
                h["asset"],
                h["category"],
                f"{h['qty']:g}",
                h["unit"],
                f"{h['avg_price']:,.0f}",
                market_price_str,
                f"{h['cost']:,.0f}",
                current_value_str,
                pnl_str,
                pnl_pct_str
            ))

        # 4. Cập nhật danh sách ComboBox What-If
        active_assets = list(self.active_holdings.keys())
        self.cb_wi_asset.configure(values=active_assets)
        if active_assets:
            if self.var_wi_asset.get() not in active_assets:
                self.cb_wi_asset.current(0)
        else:
            self.var_wi_asset.set("")
            self.var_wi_result.set("Không có tài sản nào trong danh mục để chạy giả lập.")

    def _calculate_whatif(self):
        """Giả lập bán tài sản chốt lời lỗ."""
        asset = self.var_wi_asset.get()
        if not asset or asset not in self.active_holdings:
            messagebox.showwarning("Chú ý", "Vui lòng chọn tài sản từ danh sách đang sở hữu!")
            return
            
        try:
            target_price = float(self.var_wi_target_price.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập giá giả lập hợp lệ!")
            return

        h = self.active_holdings[asset]
        qty = h["qty"]
        cost = h["cost"]
        unit = h["unit"]
        
        total_proceeds = qty * target_price
        pnl = total_proceeds - cost
        roi = (pnl / cost * 100) if cost > 0 else 0.0
        
        sign = "+" if pnl >= 0 else ""
        sign_pct = "+" if roi >= 0 else ""
        color = CLR_GREEN if pnl >= 0 else CLR_RED
        status = "LỜI 🎉" if pnl >= 0 else "LỖ ⚠️"

        self.lbl_result.configure(fg=color)
        self.var_wi_result.set(
            f"📌 Kết quả Giả lập cho [{asset}]:\n"
            f"   Số lượng nắm giữ: {qty:g} {unit}  |  Giá vốn bình quân: {h['avg_price']:,.0f} đ\n"
            f"   Nếu bán ở giá giả định: {target_price:,.0f} đ/{unit}\n"
            f"   Tổng tiền thu về: {total_proceeds:,.0f} đ\n"
            f"   Lợi nhuận ròng dự tính: {sign}{pnl:,.0f} đ ({status})  |  Tỷ suất sinh lời: {sign_pct}{roi:.2f}%"
        )
