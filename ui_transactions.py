# ui_transactions.py
"""
Tab nhập và quản lý lịch sử giao dịch mua/bán các loại tài sản.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from config import *
from db_manager import next_id, save_db

class TransactionsTab(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app
        
        self.var_date = tk.StringVar(value=datetime.date.today().isoformat())
        self.var_category = tk.StringVar(value=ASSET_CATEGORIES[0])
        self.var_asset_select = tk.StringVar()
        self.var_custom_name = tk.StringVar()
        self.var_custom_ticker = tk.StringVar()
        self.var_action = tk.StringVar(value="Mua")
        self.var_qty = tk.StringVar()
        self.var_unit = tk.StringVar()
        self.var_unit_price = tk.StringVar()
        self.var_note = tk.StringVar()
        self.var_search = tk.StringVar()
        self.var_filter_cat = tk.StringVar(value="Tất cả")
        self.var_total_preview = tk.StringVar(value="Tổng tiền tạm tính: —")

        self._build_ui()
        self._on_category_change()

        # Lắng nghe thay đổi của qty và price để cập nhật preview tổng tiền
        self.var_qty.trace_add("write", self._update_total_preview)
        self.var_unit_price.trace_add("write", self._update_total_preview)

    def _build_ui(self):
        # Thiết lập PanedWindow để chia khung nhập liệu và bảng lịch sử
        paned = tk.PanedWindow(self, orient="horizontal", bg=CLR_BG, sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        left_panel = tk.Frame(paned, bg=CLR_BG)
        right_panel = tk.Frame(paned, bg=CLR_BG)
        
        paned.add(left_panel, minsize=420)
        paned.add(right_panel, minsize=650)

        # ────────── PHẦN TRÁI: KHUNG NHẬP LIỆU GIAO DỊCH ──────────
        form_frame = tk.LabelFrame(left_panel, text=" 📝  NHẬP GIAO DỊCH MỚI ", font=FONT_BOLD,
                                    bg=CLR_PANEL, fg=CLR_GOLD, bd=1, relief="solid", padx=10, pady=8)
        form_frame.pack(fill="both", expand=True)

        # Grid form nhập
        def lbl(text, r, c, sticky="e"):
            tk.Label(form_frame, text=text, bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=r, column=c, sticky=sticky, padx=5, pady=4)

        # 1. Ngày giao dịch
        lbl("Ngày giao dịch:", 0, 0)
        ent_date = tk.Entry(form_frame, textvariable=self.var_date, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        ent_date.grid(row=0, column=1, sticky="ew", padx=5, pady=4)

        # 2. Nhóm tài sản
        lbl("Nhóm tài sản:", 1, 0)
        cb_cat = ttk.Combobox(form_frame, textvariable=self.var_category, values=ASSET_CATEGORIES, state="readonly", font=FONT_MAIN)
        cb_cat.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        cb_cat.bind("<<ComboboxSelected>>", self._on_category_change)

        # 3. Chọn tài sản
        lbl("Tài sản cụ thể:", 2, 0)
        self.cb_asset = ttk.Combobox(form_frame, textvariable=self.var_asset_select, state="readonly", font=FONT_MAIN)
        self.cb_asset.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
        self.cb_asset.bind("<<ComboboxSelected>>", self._on_asset_select_change)

        # 4. Khung nhập tài sản tùy chọn (chỉ hiển thị khi chọn Khác/Custom)
        self.custom_assets_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        self.custom_assets_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        tk.Label(self.custom_assets_frame, text="Tên tài sản mới:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=0, sticky="e", padx=5, pady=4)
        self.ent_cust_name = tk.Entry(self.custom_assets_frame, textvariable=self.var_custom_name, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        self.ent_cust_name.grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        
        tk.Label(self.custom_assets_frame, text="Mã Ticker (API):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=1, column=0, sticky="e", padx=5, pady=4)
        self.ent_cust_ticker = tk.Entry(self.custom_assets_frame, textvariable=self.var_custom_ticker, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        self.ent_cust_ticker.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        
        self.custom_assets_frame.columnconfigure(1, weight=1)

        # 5. Hành động (Mua / Bán)
        lbl("Hành động:", 4, 0)
        cb_act = ttk.Combobox(form_frame, textvariable=self.var_action, values=["Mua", "Bán"], state="readonly", font=FONT_MAIN)
        cb_act.grid(row=4, column=1, sticky="ew", padx=5, pady=4)
        cb_act.bind("<<ComboboxSelected>>", lambda _: self._update_price_from_api_if_available())

        # 6. Số lượng & Đơn vị
        lbl("Số lượng:", 5, 0)
        qty_unit_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        qty_unit_frame.grid(row=5, column=1, sticky="ew")
        qty_unit_frame.columnconfigure(0, weight=2)
        qty_unit_frame.columnconfigure(2, weight=1)

        ent_qty = tk.Entry(qty_unit_frame, textvariable=self.var_qty, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        ent_qty.grid(row=0, column=0, sticky="ew", padx=(0,5))
        
        tk.Label(qty_unit_frame, text="Đơn vị:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=1, sticky="e", padx=2)
        ent_unit = tk.Entry(qty_unit_frame, textvariable=self.var_unit, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, width=8, bd=3)
        ent_unit.grid(row=0, column=2, sticky="ew")

        # 7. Đơn giá
        lbl("Đơn giá (đ):", 6, 0)
        price_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        price_frame.grid(row=6, column=1, sticky="ew")
        price_frame.columnconfigure(0, weight=1)

        ent_price = tk.Entry(price_frame, textvariable=self.var_unit_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        ent_price.grid(row=0, column=0, sticky="ew", padx=(0,5))
        
        btn_get_price = tk.Button(price_frame, text="⚡ Lấy giá thị trường", command=self._update_price_from_api_if_available,
                                   bg="#3b82f6", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", padx=5, pady=2, cursor="hand2")
        btn_get_price.grid(row=0, column=1, sticky="e")

        # 8. Ghi chú
        lbl("Ghi chú:", 7, 0)
        ent_note = tk.Entry(form_frame, textvariable=self.var_note, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        ent_note.grid(row=7, column=1, sticky="ew", padx=5, pady=4)

        # 9. Preview tổng tiền
        lbl_preview = tk.Label(form_frame, textvariable=self.var_total_preview, bg=CLR_PANEL, fg=CLR_GOLD, font=FONT_BOLD, anchor="w")
        lbl_preview.grid(row=8, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        form_frame.columnconfigure(1, weight=1)

        # Nút thao tác
        btn_grid = tk.Frame(form_frame, bg=CLR_PANEL)
        btn_grid.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.btn_add = tk.Button(btn_grid, text="➕  Thêm giao dịch", command=self._add_transaction,
                                  bg=CLR_GREEN, fg="white", font=FONT_BOLD, relief="flat", padx=10, pady=6, cursor="hand2")
        self.btn_add.pack(side="left", padx=4)

        btn_load = tk.Button(btn_grid, text="✏️  Nạp vào Form", command=self._load_selected,
                              bg="#555588", fg="white", font=FONT_BOLD, relief="flat", padx=10, pady=6, cursor="hand2")
        btn_load.pack(side="left", padx=4)

        btn_del = tk.Button(btn_grid, text="🗑️  Xóa đã chọn", command=self._delete_selected,
                             bg=CLR_RED, fg="white", font=FONT_BOLD, relief="flat", padx=10, pady=6, cursor="hand2")
        btn_del.pack(side="left", padx=4)

        # ────────── PHẦN PHẢI: BẢNG LỊCH SỬ GIAO DỊCH ──────────
        hist_frame = tk.LabelFrame(right_panel, text=" 📋  LỊCH SỬ GIAO DỊCH MUA BÁN ", font=FONT_BOLD,
                                     bg=CLR_PANEL, fg=CLR_GOLD, bd=1, relief="solid", padx=10, pady=8)
        hist_frame.pack(fill="both", expand=True)

        # Dòng bộ lọc tìm kiếm
        filter_bar = tk.Frame(hist_frame, bg=CLR_PANEL)
        filter_bar.pack(fill="x", pady=(0, 10))

        tk.Label(filter_bar, text="Tìm kiếm:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).pack(side="left", padx=2)
        ent_search = tk.Entry(filter_bar, textvariable=self.var_search, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", width=15, bd=3)
        ent_search.pack(side="left", padx=5)
        self.var_search.trace_add("write", lambda *_: self.refresh_table())

        tk.Label(filter_bar, text="Nhóm:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).pack(side="left", padx=5)
        cb_fcat = ttk.Combobox(filter_bar, textvariable=self.var_filter_cat, values=["Tất cả"] + ASSET_CATEGORIES, state="readonly", font=FONT_MAIN, width=12)
        cb_fcat.pack(side="left", padx=5)
        cb_fcat.bind("<<ComboboxSelected>>", lambda _: self.refresh_table())

        # Bảng dữ liệu chính
        cols = ("ID", "Date", "Category", "Asset", "Ticker", "Action", "Qty", "Unit", "Price", "Total", "Note")
        self.tree = ttk.Treeview(hist_frame, columns=cols, show="headings", height=18, selectmode="browse")
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Date", text="Ngày")
        self.tree.heading("Category", text="Nhóm")
        self.tree.heading("Asset", text="Tên tài sản")
        self.tree.heading("Ticker", text="Ticker")
        self.tree.heading("Action", text="GD")
        self.tree.heading("Qty", text="SL")
        self.tree.heading("Unit", text="ĐV")
        self.tree.heading("Price", text="Đơn giá")
        self.tree.heading("Total", text="Tổng tiền")
        self.tree.heading("Note", text="Ghi chú")

        self.tree.column("ID", width=35, anchor="center")
        self.tree.column("Date", width=85, anchor="center")
        self.tree.column("Category", width=80, anchor="center")
        self.tree.column("Asset", width=160, anchor="w")
        self.tree.column("Ticker", width=70, anchor="center")
        self.tree.column("Action", width=50, anchor="center")
        self.tree.column("Qty", width=55, anchor="center")
        self.tree.column("Unit", width=45, anchor="center")
        self.tree.column("Price", width=100, anchor="e")
        self.tree.column("Total", width=110, anchor="e")
        self.tree.column("Note", width=140, anchor="w")

        vsb = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(hist_frame, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side="top", fill="both", expand=True)
        vsb.pack(side="right", fill="y", before=self.tree)
        hsb.pack(side="bottom", fill="x")

        # Cấu hình màu sắc nhãn dòng bảng lịch sử
        self.tree.tag_configure("buy", background="#132c20", foreground="#6ee7b7")  # Xanh tối
        self.tree.tag_configure("sell", background="#3b1919", foreground="#fca5a5") # Đỏ tối

    def _on_category_change(self, event=None):
        """Khi đổi nhóm tài sản ở Combobox chính."""
        cat = self.var_category.get()
        # Lọc danh sách tài sản mẫu tương ứng nhóm này
        assets = [a for a in DEFAULT_ASSETS if a["category"] == cat]
        vals = [a["name"] for a in assets] + ["Nhập thủ công... (Khác)"]
        self.cb_asset.configure(values=vals)
        
        # Mặc định chọn phần tử đầu tiên
        if vals:
            self.cb_asset.current(0)
            self._on_asset_select_change()

    def _on_asset_select_change(self, event=None):
        """Khi đổi lựa chọn tài sản mẫu."""
        val = self.var_asset_select.get()
        if val == "Nhập thủ công... (Khác)":
            self.custom_assets_frame.grid()
            self.var_custom_name.set("")
            self.var_custom_ticker.set("")
            self.var_unit.set("")
        else:
            self.custom_assets_frame.grid_remove()
            # Lấy thông tin tài sản mặc định tương ứng
            asset_info = next((a for a in DEFAULT_ASSETS if a["name"] == val), None)
            if asset_info:
                self.var_custom_name.set(asset_info["name"])
                self.var_custom_ticker.set(asset_info["ticker"])
                self.var_unit.set(asset_info["unit"])
                
        # Thử lấy giá trị trực tuyến điền sẵn
        self._update_price_from_api_if_available()

    def _update_total_preview(self, *_):
        """Cập nhật preview tổng tiền = số lượng * đơn giá."""
        try:
            qty = float(self.var_qty.get())
            price = float(self.var_unit_price.get().replace(",", ""))
            total = qty * price
            self.var_total_preview.set(f"Tổng tiền tạm tính: {total:,.0f} đ")
        except ValueError:
            self.var_total_preview.set("Tổng tiền tạm tính: —")

    def _update_price_from_api_if_available(self):
        """Tìm trong bảng giá thực tế và pre-fill giá giao dịch."""
        ticker = self.var_custom_ticker.get()
        if not ticker:
            # Nếu là nhập custom, xem ticker đang nhập
            ticker = self.var_custom_ticker.get()
            
        if ticker in self.main_app.current_prices:
            prices = self.main_app.current_prices[ticker]
            action = self.var_action.get()
            # Nếu mua, ta mua ở giá Bán ra của thị trường (sell)
            # Nếu bán, ta bán ở giá Mua vào của thị trường (buy)
            price = prices["sell"] if action == "Mua" else prices["buy"]
            if price > 0:
                self.var_unit_price.set(f"{price:,.0f}")
                self.main_app.var_status.set(f"⚡ Đã lấy giá thị trường cho {ticker} ({action}): {price:,.0f} đ")

    def refresh_table(self):
        """Lọc dữ liệu lịch sử và hiển thị ra bảng."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        search_kw = self.var_search.get().lower().strip()
        filter_cat = self.var_filter_cat.get()

        for r in sorted(self.main_app.db, key=lambda x: x.get("date", ""), reverse=True):
            # Lọc theo Nhóm
            cat = r.get("category", "Khác")
            if filter_cat != "Tất cả" and cat != filter_cat:
                continue

            # Lọc theo Từ khóa tìm kiếm
            asset_name = r.get("asset", "").lower()
            ticker = r.get("ticker", "").lower()
            note = r.get("note", "").lower()
            
            if search_kw:
                if (search_kw not in asset_name and 
                    search_kw not in ticker and 
                    search_kw not in note and 
                    search_kw not in r.get("date", "")):
                    continue

            tag = "buy" if r["action"] == "Mua" else "sell"
            self.tree.insert("", "end", tag=tag, values=(
                r["id"],
                r.get("date", ""),
                cat,
                r["asset"],
                r.get("ticker", ""),
                r["action"],
                f"{r['quantity']:g}",
                r["unit"],
                f"{r['unit_price']:,.0f}",
                f"{r['total']:,.0f}",
                r.get("note", "")
            ))

    def _add_transaction(self):
        """Thêm giao dịch mới."""
        try:
            qty = float(self.var_qty.get())
            price = float(self.var_unit_price.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("Lỗi", "Số lượng và đơn giá phải là số hợp lệ!")
            return

        # Lấy tên tài sản và mã ticker
        asset_select = self.var_asset_select.get()
        if asset_select == "Nhập thủ công... (Khác)":
            asset_name = self.var_custom_name.get().strip()
            ticker = self.var_custom_ticker.get().strip()
            if not asset_name or not ticker:
                messagebox.showerror("Lỗi", "Nhập thủ công yêu cầu đầy đủ Tên tài sản và Mã Ticker!")
                return
        else:
            asset_name = asset_select
            asset_info = next((a for a in DEFAULT_ASSETS if a["name"] == asset_select), None)
            ticker = asset_info["ticker"] if asset_info else ""

        if not self.var_date.get():
            messagebox.showerror("Lỗi", "Vui lòng nhập ngày giao dịch!")
            return

        record = {
            "id": next_id(self.main_app.db),
            "date": self.var_date.get(),
            "category": self.var_category.get(),
            "asset": asset_name,
            "ticker": ticker,
            "action": self.var_action.get(),
            "quantity": qty,
            "unit": self.var_unit.get().strip(),
            "unit_price": price,
            "total": qty * price,
            "note": self.var_note.get().strip()
        }

        self.main_app.db.append(record)
        save_db(self.main_app.db)
        
        # Reset form
        self.var_qty.set("")
        self.var_unit_price.set("")
        self.var_note.set("")
        self.var_total_preview.set("Tổng tiền tạm tính: —")

        # Cập nhật các bảng
        self.refresh_table()
        self.main_app.refresh_portfolio_view()
        
        self.main_app.var_status.set(f"✅ Đã thêm: {record['action']} {qty} {record['unit']} {record['asset']} thành công.")

    def _load_selected(self):
        """Nạp dữ liệu hàng đang chọn vào Form để sửa/nhập nhanh."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một dòng lịch sử để nạp dữ liệu!")
            return
        
        iid = int(self.tree.item(sel[0])["values"][0])
        rec = next((r for r in self.main_app.db if r["id"] == iid), None)
        if not rec:
            return

        self.var_date.set(rec.get("date", ""))
        self.var_category.set(rec.get("category", ASSET_CATEGORIES[0]))
        self._on_category_change()
        
        # Thử tìm xem tài sản này có trong mặc định không
        found_in_default = any(a["name"] == rec["asset"] for a in DEFAULT_ASSETS)
        if found_in_default:
            self.var_asset_select.set(rec["asset"])
            self.custom_assets_frame.grid_remove()
        else:
            self.var_asset_select.set("Nhập thủ công... (Khác)")
            self.custom_assets_frame.grid()
            self.var_custom_name.set(rec["asset"])
            self.var_custom_ticker.set(rec.get("ticker", ""))

        self.var_action.set(rec["action"])
        self.var_qty.set(f"{rec['quantity']:g}")
        self.var_unit.set(rec["unit"])
        self.var_unit_price.set(f"{rec['unit_price']:,.0f}")
        self.var_note.set(rec.get("note", ""))

    def _delete_selected(self):
        """Xóa giao dịch đang chọn."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Hãy chọn một dòng giao dịch để xóa!")
            return
        
        iid = int(self.tree.item(sel[0])["values"][0])
        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa giao dịch ID {iid}?"):
            return

        self.main_app.db = [r for r in self.main_app.db if r["id"] != iid]
        save_db(self.main_app.db)
        
        self.refresh_table()
        self.main_app.refresh_portfolio_view()
        self.main_app.var_status.set(f"🗑️ Đã xóa giao dịch ID {iid}.")
