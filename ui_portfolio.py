# ui_portfolio.py
"""
Tab hiển thị Dashboard Danh mục đầu tư, Lời/Lỗ thực tế và Giả lập chốt lời (What-if).
Tích hợp trực tiếp bảng cập nhật giá thị trường nhanh theo nhóm tài sản (Vàng/Bạc).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from db_manager import calculate_portfolio, save_market_prices

class PortfolioTab(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app
        
        # Biến trạng thái cho What-If
        self.var_wi_asset = tk.StringVar()
        self.var_wi_target_price = tk.StringVar()
        self.var_wi_result = tk.StringVar(value="Nhập giá giả lập chốt lời để tính lợi nhuận dự tính.")

        # Biến trạng thái cho Cập nhật giá thủ công
        self.var_buy_price = tk.StringVar()
        self.var_sell_price = tk.StringVar()

        # Biến trạng thái cho bộ lọc nhóm tài sản
        self.var_filter_cat = tk.StringVar(value="Tất cả")

        self._build_ui()

    def _build_ui(self):
        # ────────── THANH BỘ LỌC DANH MỤC TÀI SẢN ──────────
        filter_bar = tk.Frame(self, bg=CLR_BG)
        filter_bar.pack(fill="x", padx=15, pady=(12, 0))
        
        tk.Label(filter_bar, text="🔍 Lọc theo Nhóm tài sản:", bg=CLR_BG, fg=CLR_TEXT, font=FONT_BOLD).pack(side="left", padx=5)
        cb_filter = ttk.Combobox(filter_bar, textvariable=self.var_filter_cat, values=["Tất cả"] + ASSET_CATEGORIES, state="readonly", font=FONT_MAIN, width=15)
        cb_filter.pack(side="left", padx=5)
        cb_filter.bind("<<ComboboxSelected>>", lambda _: self.refresh_view())

        # ────────── PHẦN TRÊN: DASHBOARD CARD SỐ LIỆU TỔNG QUAN ──────────
        cards_frame = tk.Frame(self, bg=CLR_BG)
        cards_frame.pack(fill="x", padx=10, pady=8)
        
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
        table_label = tk.Label(self, text="💼  DANH MỤC CHI TIẾT CÁC TÀI SẢN ĐANG NẮM GIỮ (Chọn 1 dòng để sửa nhanh giá nhóm ở dưới)",
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
        self.tree.heading("MarketPrice", text="Giá thị trường quy đổi")
        self.tree.heading("TotalCost", text="Tổng vốn")
        self.tree.heading("CurrentValue", text="Giá trị hiện tại")
        self.tree.heading("PnL", text="Lời/Lỗ")
        self.tree.heading("PnLPct", text="% Lời/Lỗ")

        self.tree.column("Asset", width=180, anchor="w")
        self.tree.column("Category", width=80, anchor="center")
        self.tree.column("Qty", width=80, anchor="center")
        self.tree.column("Unit", width=50, anchor="center")
        self.tree.column("AvgCost", width=120, anchor="e")
        self.tree.column("MarketPrice", width=130, anchor="e")
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

        # Lắng nghe sự kiện chọn dòng trên bảng danh mục để sửa giá nhanh
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # ────────── PHẦN DƯỚI: KHUNG ĐIỀU KHIỂN CHI TIẾT (CHỈNH GIÁ & GIẢ LẬP) ──────────
        bottom_frame = tk.Frame(self, bg=CLR_BG)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        bottom_frame.columnconfigure(0, weight=1, uniform="bottom_panels")
        bottom_frame.columnconfigure(1, weight=1, uniform="bottom_panels")

        # --- PANEL TRÁI: CẬP NHẬT GIÁ THỊ TRƯỜNG THEO NHÓM ---
        price_frame = tk.LabelFrame(bottom_frame, text=" ✏️  CẬP NHẬT GIÁ THỊ TRƯỜNG THEO NHÓM ", font=FONT_BOLD,
                                     bg=CLR_PANEL, fg=CLR_GOLD, bd=1, relief="solid", padx=10, pady=8)
        price_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        price_grid = tk.Frame(price_frame, bg=CLR_PANEL)
        price_grid.pack(fill="x")

        tk.Label(price_grid, text="Nhóm tài sản:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.var_price_asset_sel = tk.StringVar()
        self.cb_price_asset = ttk.Combobox(price_grid, textvariable=self.var_price_asset_sel, values=["Vàng", "Bạc"], state="readonly", font=FONT_MAIN, width=12)
        self.cb_price_asset.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.cb_price_asset.bind("<<ComboboxSelected>>", self._on_price_asset_combobox_change)

        tk.Label(price_grid, text="Đơn vị giá:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=2, sticky="e", padx=10, pady=5)
        self.var_price_unit = tk.StringVar(value="Lượng")
        self.cb_price_unit = ttk.Combobox(price_grid, textvariable=self.var_price_unit, values=["Lượng", "Cây", "Chỉ", "Ounce"], state="readonly", font=FONT_MAIN, width=10)
        self.cb_price_unit.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        tk.Label(price_grid, text="Giá mua vào (đ):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.ent_buy = tk.Entry(price_grid, textvariable=self.var_buy_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, width=15, bd=3)
        self.ent_buy.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Label(price_grid, text="Giá bán ra (đ):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=1, column=2, sticky="e", padx=10, pady=5)
        self.ent_sell = tk.Entry(price_grid, textvariable=self.var_sell_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, width=15, bd=3)
        self.ent_sell.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        btn_save_price = tk.Button(price_grid, text="💾  Cập nhật giá", command=self._save_price,
                                   bg=CLR_GOLD, fg="white", font=FONT_BOLD, relief="flat", padx=15, pady=4, cursor="hand2")
        btn_save_price.grid(row=2, column=0, columnspan=4, pady=(10, 0))

        # --- PANEL PHẢI: GIẢ LẬP CHỐT LỜI ---
        wi_frame = tk.LabelFrame(bottom_frame, text=" 🔮  GIẢ LẬP CHỐT LỜI (WHAT-IF SIMULATOR) ", font=FONT_BOLD,
                                   bg=CLR_PANEL, fg=CLR_GOLD, bd=1, relief="solid", padx=10, pady=8)
        wi_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        wi_grid = tk.Frame(wi_frame, bg=CLR_PANEL)
        wi_grid.pack(fill="x")

        tk.Label(wi_grid, text="Tài sản:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cb_wi_asset = ttk.Combobox(wi_grid, textvariable=self.var_wi_asset, state="readonly", font=FONT_MAIN, width=22)
        self.cb_wi_asset.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(wi_grid, text="Nếu bán ở giá (đ):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=2, sticky="e", padx=10, pady=5)
        self.ent_target = tk.Entry(wi_grid, textvariable=self.var_wi_target_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, width=15, bd=3)
        self.ent_target.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        btn_calc = tk.Button(wi_grid, text="▶  Tính", command=self._calculate_whatif,
                             bg=CLR_GREEN, fg="white", font=FONT_BOLD, relief="flat", padx=12, pady=4, cursor="hand2")
        btn_calc.grid(row=0, column=4, padx=10)

        # Label kết quả giả lập
        self.lbl_result = tk.Label(wi_frame, textvariable=self.var_wi_result, font=FONT_BOLD, bg=CLR_PANEL, fg=CLR_TEXT, justify="left", anchor="w", wraplength=500)
        self.lbl_result.pack(fill="x", padx=10, pady=(8, 4))

        # Lưu trữ dữ liệu danh mục để phục vụ What-If
        self.active_holdings = {}

    def refresh_view(self):
        """Tính toán lại danh mục đầu tư và hiển thị dữ liệu mới lên màn hình."""
        # 1. Thực hiện tính toán danh mục gốc
        self.active_holdings, summary = calculate_portfolio(self.main_app.db, self.main_app.current_prices)

        # 2. Áp dụng bộ lọc nhóm tài sản
        filter_cat = self.var_filter_cat.get()
        
        filtered_cost = 0.0
        filtered_value = 0.0
        filtered_pnl = 0.0

        # 3. Cập nhật bảng dữ liệu nắm giữ & cộng dồn số liệu đã lọc
        for row in self.tree.get_children():
            self.tree.delete(row)

        for asset, h in sorted(self.active_holdings.items(), key=lambda x: (x[1]["category"], x[0])):
            cat = h.get("category", "Vàng")
            if filter_cat != "Tất cả" and cat != filter_cat:
                continue

            filtered_cost += h["cost"]
            filtered_value += h["current_value"] if h["market_price"] > 0 else h["cost"]
            filtered_pnl += h["pnl"]

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

        # 4. Tính toán ROI đã lọc
        filtered_roi = (filtered_pnl / filtered_cost * 100) if filtered_cost > 0 else 0.0

        # 5. Cập nhật thẻ Dashboard Số liệu lớn đã lọc
        self.card_cost.configure(text=f"{filtered_cost:,.0f} đ")
        self.card_value.configure(text=f"{filtered_value:,.0f} đ")
        
        # Thẻ Lời lỗ ròng
        sign = "+" if filtered_pnl >= 0 else ""
        self.card_pnl.configure(text=f"{sign}{filtered_pnl:,.0f} đ")
        self.card_pnl.configure(fg=CLR_GREEN if filtered_pnl >= 0 else CLR_RED)
        
        # Thẻ Tỷ lệ P&L
        sign_pct = "+" if filtered_roi >= 0 else ""
        self.card_pnl_pct.configure(text=f"{sign_pct}{filtered_roi:.2f}%")
        self.card_pnl_pct.configure(fg=CLR_GREEN if filtered_roi >= 0 else CLR_RED)

        # 6. Cập nhật danh sách ComboBox What-If (chỉ chứa các tài sản hiển thị sau lọc)
        active_assets = [asset for asset, h in self.active_holdings.items() if (filter_cat == "Tất cả" or h.get("category", "Vàng") == filter_cat)]
        self.cb_wi_asset.configure(values=active_assets)
        if active_assets:
            if self.var_wi_asset.get() not in active_assets:
                self.cb_wi_asset.current(0)
        else:
            self.var_wi_asset.set("")
            self.var_wi_result.set("Không có tài sản nào trong nhóm để chạy giả lập.")

        # 7. Mặc định chọn nhóm Vàng nếu chưa chọn trong bộ chỉnh giá
        if not self.var_price_asset_sel.get():
            self.cb_price_asset.current(0)
            self._on_price_asset_combobox_change()

    def _on_price_asset_combobox_change(self, event=None):
        """Khi người dùng chọn nhóm tài sản để sửa giá."""
        cat = self.var_price_asset_sel.get()
        if not cat:
            return
            
        price_info = self.main_app.current_prices.get(cat, {"buy": 0.0, "sell": 0.0, "unit": "Lượng"})
        buy_price = price_info.get("buy", 0.0)
        sell_price = price_info.get("sell", 0.0)
        unit = price_info.get("unit", "Lượng")
        
        self.var_buy_price.set(f"{buy_price:,.0f}" if buy_price > 0 else "")
        self.var_sell_price.set(f"{sell_price:,.0f}" if sell_price > 0 else "")
        self.var_price_unit.set(unit)

    def _on_row_select(self, event):
        """Khi chọn dòng trên bảng, đồng bộ sang nhóm Vàng/Bạc sửa giá thị trường."""
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])["values"]
        category = vals[1]  # "Vàng" hoặc "Bạc"
        
        if category in ["Vàng", "Bạc"]:
            self.var_price_asset_sel.set(category)
            self._on_price_asset_combobox_change()

    def _save_price(self):
        """Lưu lại giá thị trường theo nhóm tài sản."""
        cat = self.var_price_asset_sel.get()
        if not cat:
            messagebox.showwarning("Chú ý", "Vui lòng chọn nhóm tài sản cần chỉnh sửa!")
            return
            
        try:
            buy_val = float(self.var_buy_price.get().replace(",", "")) if self.var_buy_price.get() else 0.0
            sell_val = float(self.var_sell_price.get().replace(",", "")) if self.var_sell_price.get() else 0.0
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập giá trị số hợp lệ!")
            return

        self.main_app.current_prices[cat] = {
            "buy": buy_val,
            "sell": sell_val,
            "unit": self.var_price_unit.get()
        }

        save_market_prices(self.main_app.current_prices)
        self.main_app.var_status.set(f"✍️ Đã lưu giá mới cho nhóm [{cat}]: {buy_val:,.0f}đ / {sell_val:,.0f}đ mỗi {self.var_price_unit.get()}")
        self.refresh_view()

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
            f"   Số lượng: {qty:g} {unit}  |  Giá vốn BQ: {h['avg_price']:,.0f} đ\n"
            f"   Nếu bán ở giá giả định: {target_price:,.0f} đ/{unit}\n"
            f"   Tổng tiền thu về: {total_proceeds:,.0f} đ\n"
            f"   Lợi nhuận ròng dự tính: {sign}{pnl:,.0f} đ ({status})  |  Tỷ suất: {sign_pct}{roi:.2f}%"
        )
