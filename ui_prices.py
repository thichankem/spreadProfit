# ui_prices.py
"""
Tab hiển thị Bảng giá thị trường, cho phép cập nhật trực tuyến hoặc nhập tay ghi đè giá.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from config import *

class PricesTab(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app
        self._build_ui()

    def _build_ui(self):
        # Thiết kế nhãn tiêu đề của tab
        title_lbl = tk.Label(self, text="📊  BẢNG GIÁ THỊ TRƯỜNG & TỶ GIÁ QUY ĐỔI (đ / Đơn vị)",
                             font=FONT_BOLD, bg=CLR_BG, fg=CLR_HEAD, anchor="w")
        title_lbl.pack(fill="x", padx=10, pady=10)

        # Khung chứa bảng giá
        table_frame = tk.Frame(self, bg=CLR_PANEL, bd=1, relief="flat", highlightbackground=CLR_BORDER, highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("Asset", "Ticker", "Category", "Buy", "Sell", "Unit")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15, selectmode="browse")
        
        self.tree.heading("Asset", text="Tên tài sản")
        self.tree.heading("Ticker", text="Mã Ticker")
        self.tree.heading("Category", text="Nhóm tài sản")
        self.tree.heading("Buy", text="Giá MUA VÀO (bạn bán)")
        self.tree.heading("Sell", text="Giá BÁN RA (bạn mua)")
        self.tree.heading("Unit", text="Đơn vị")

        self.tree.column("Asset", width=220, anchor="w")
        self.tree.column("Ticker", width=110, anchor="center")
        self.tree.column("Category", width=120, anchor="center")
        self.tree.column("Buy", width=160, anchor="e")
        self.tree.column("Sell", width=160, anchor="e")
        self.tree.column("Unit", width=90, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Khung chỉnh sửa thủ công giá
        edit_frame = tk.LabelFrame(self, text=" ✏️  ĐIỀU CHỈNH GIÁ THỦ CÔNG ", font=FONT_BOLD,
                                    bg=CLR_PANEL, fg=CLR_GOLD, bd=1, relief="solid", padx=10, pady=8)
        edit_frame.pack(fill="x", padx=10, pady=10)

        # Grid trong khung chỉnh sửa
        tk.Label(edit_frame, text="Tài sản chọn:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.lbl_selected_asset = tk.Label(edit_frame, text="Chưa chọn tài sản", bg=CLR_PANEL, fg=CLR_TEXT_MUTED, font=FONT_MAIN, anchor="w")
        self.lbl_selected_asset.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        tk.Label(edit_frame, text="Giá mua vào (đ):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.var_buy_price = tk.StringVar()
        self.ent_buy = tk.Entry(edit_frame, textvariable=self.var_buy_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, width=18, bd=3)
        self.ent_buy.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Label(edit_frame, text="Giá bán ra (đ):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.var_sell_price = tk.StringVar()
        self.ent_sell = tk.Entry(edit_frame, textvariable=self.var_sell_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, width=18, bd=3)
        self.ent_sell.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Nút hành động
        btn_row = tk.Frame(edit_frame, bg=CLR_PANEL)
        btn_row.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        btn_save = tk.Button(btn_row, text="💾  Ghi đè giá", command=self._override_price,
                              bg=CLR_GOLD, fg="white", font=FONT_BOLD, relief="flat", padx=15, pady=5, cursor="hand2")
        btn_save.pack(side="left", padx=5)

        btn_refresh = tk.Button(btn_row, text="🔄  Cập nhật trực tuyến", command=self.main_app.refresh_prices,
                                 bg=CLR_HEAD, fg="white", font=FONT_BOLD, relief="flat", padx=15, pady=5, cursor="hand2")
        btn_refresh.pack(side="left", padx=5)

        self.selected_ticker = None

    def refresh_table(self):
        """Đọc từ main_app.current_prices và nạp dữ liệu lên bảng."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Thu thập các mã ticker độc nhất từ db hiện có và default assets
        all_assets_info = {}
        
        # Nạp từ default assets
        for item in DEFAULT_ASSETS:
            all_assets_info[item["ticker"]] = {
                "name": item["name"],
                "category": item["category"],
                "ticker": item["ticker"],
                "unit": item["unit"]
            }

        # Nạp bổ sung từ db thực tế (nếu có tài sản mới tự thêm)
        for r in self.main_app.db:
            ticker = r.get("ticker", "")
            if ticker and ticker not in all_assets_info:
                all_assets_info[ticker] = {
                    "name": r["asset"],
                    "category": r.get("category", "Khác"),
                    "ticker": ticker,
                    "unit": r["unit"]
                }

        # Sắp xếp hiển thị theo Category rồi đến tên tài sản
        sorted_assets = sorted(all_assets_info.values(), key=lambda x: (x["category"], x["name"]))

        for a in sorted_assets:
            ticker = a["ticker"]
            price_info = self.main_app.current_prices.get(ticker, {"buy": 0.0, "sell": 0.0})
            buy_price = price_info.get("buy", 0.0)
            sell_price = price_info.get("sell", 0.0)

            buy_str = f"{buy_price:,.0f}" if buy_price > 0 else "—"
            sell_str = f"{sell_price:,.0f}" if sell_price > 0 else "—"

            self.tree.insert("", "end", values=(
                a["name"],
                ticker,
                a["category"],
                buy_str,
                sell_str,
                a["unit"]
            ))

    def _on_row_select(self, event):
        """Khi người dùng chọn một dòng trên bảng giá."""
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])["values"]
        name, ticker, category, buy_str, sell_str, unit = vals
        
        self.selected_ticker = ticker
        self.lbl_selected_asset.configure(text=f"{name} ({ticker})")
        
        # Điền giá cũ vào ô nhập liệu
        buy_val = buy_str.replace(",", "")
        sell_val = sell_str.replace(",", "")
        self.var_buy_price.set(buy_val if buy_val != "—" else "")
        self.var_sell_price.set(sell_val if sell_val != "—" else "")

    def _override_price(self):
        """Ghi đè giá mua/bán thị trường thủ công."""
        if not self.selected_ticker:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một dòng tài sản từ bảng để chỉnh sửa!")
            return
        
        try:
            buy_val = float(self.var_buy_price.get().replace(",", "")) if self.var_buy_price.get() else 0.0
            sell_val = float(self.var_sell_price.get().replace(",", "")) if self.var_sell_price.get() else 0.0
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập giá trị số hợp lệ!")
            return

        self.main_app.current_prices[self.selected_ticker] = {
            "buy": buy_val,
            "sell": sell_val
        }

        # Lưu log trạng thái
        self.main_app.var_status.set(f"✍️ Đã ghi đè thủ công giá cho mã {self.selected_ticker}: {buy_val:,.0f}đ / {sell_val:,.0f}đ")
        
        # Reload hiển thị bảng giá và cập nhật portfolio
        self.refresh_table()
        self.main_app.refresh_portfolio_view()
