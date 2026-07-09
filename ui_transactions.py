# ui_transactions.py
"""
Tab nhập và quản lý lịch sử giao dịch mua/bán các loại tài sản.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import calendar
from config import *
from db_manager import next_id, save_db, load_custom_assets, save_custom_assets

class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, current_date_str, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Chọn Ngày")
        
        # Thiết lập kích thước lịch lớn hơn để không bị che khuất
        w = 440
        h = 485
        
        self.configure(bg=CLR_PANEL)
        
        # Đặt transient và grab_set để bắt buộc người dùng thao tác xong mới quay lại cửa sổ chính
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # Định nghĩa font chữ lớn hơn cho lịch
        FONT_CAL_TITLE = ("Segoe UI", 13, "bold")
        FONT_CAL_HEADER = ("Segoe UI", 11, "bold")
        FONT_CAL_DAY = ("Segoe UI", 11, "bold")
        
        # Center dialog relative to parent
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - w) // 2
        y = parent_y + (parent_h - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Parse current date
        try:
            self.current_date = datetime.date.fromisoformat(current_date_str)
        except Exception:
            self.current_date = datetime.date.today()

        self.year = self.current_date.year
        self.month = self.current_date.month

        # Month and Year selection headers
        header_frame = tk.Frame(self, bg=CLR_PANEL, pady=12)
        header_frame.pack(fill="x")

        btn_prev = tk.Button(header_frame, text="◀", command=self.prev_month, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_CAL_HEADER, relief="flat", padx=10, pady=4, cursor="hand2")
        btn_prev.pack(side="left", padx=15)

        self.lbl_month_year = tk.Label(header_frame, text="", bg=CLR_PANEL, fg=CLR_GOLD, font=FONT_CAL_TITLE)
        self.lbl_month_year.pack(side="left", expand=True, fill="x")

        btn_next = tk.Button(header_frame, text="▶", command=self.next_month, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_CAL_HEADER, relief="flat", padx=10, pady=4, cursor="hand2")
        btn_next.pack(side="right", padx=15)

        # Weekdays header
        week_frame = tk.Frame(self, bg=CLR_PANEL)
        week_frame.pack(fill="x", padx=15)
        days = ["Th 2", "Th 3", "Th 4", "Th 5", "Th 6", "Th 7", "CN"]
        for i, d in enumerate(days):
            lbl = tk.Label(week_frame, text=d, bg=CLR_PANEL, fg=CLR_TEXT_MUTED, font=FONT_CAL_HEADER, width=4)
            lbl.grid(row=0, column=i, padx=3, pady=4)

        # Days grid
        self.days_frame = tk.Frame(self, bg=CLR_PANEL)
        self.days_frame.pack(fill="both", expand=True, padx=15, pady=8)
        
        # Thiết lập cột của grid giãn đều
        for i in range(7):
            self.days_frame.columnconfigure(i, weight=1)
            
        self.draw_calendar()

    def draw_calendar(self):
        # Clear old widgets
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        FONT_CAL_TITLE = ("Segoe UI", 13, "bold")
        FONT_CAL_DAY = ("Segoe UI", 11, "bold")

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(self.year, self.month)
        self.lbl_month_year.config(text=f"Tháng {self.month} / {self.year}")

        for r_idx, week in enumerate(month_days):
            for c_idx, day in enumerate(week):
                if day == 0:
                    lbl = tk.Label(self.days_frame, text="", bg=CLR_PANEL, width=4, height=1)
                    lbl.grid(row=r_idx, column=c_idx, padx=3, pady=4)
                else:
                    is_today = (self.year == datetime.date.today().year and 
                                self.month == datetime.date.today().month and 
                                day == datetime.date.today().day)
                    
                    is_selected = (self.year == self.current_date.year and 
                                   self.month == self.current_date.month and 
                                   day == self.current_date.day)

                    bg_color = CLR_ENTRY
                    fg_color = CLR_TEXT
                    if is_selected:
                        bg_color = CLR_GOLD
                        fg_color = CLR_BG
                    elif is_today:
                        bg_color = CLR_HEAD
                        fg_color = "white"

                    btn = tk.Button(self.days_frame, text=str(day), bg=bg_color, fg=fg_color,
                                    font=FONT_CAL_DAY, relief="flat", width=4, height=1, cursor="hand2",
                                    command=lambda d=day: self.select_day(d))
                    btn.grid(row=r_idx, column=c_idx, padx=3, pady=4)

    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.draw_calendar()

    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.draw_calendar()

    def select_day(self, day):
        selected_date = datetime.date(self.year, self.month, day)
        self.callback(selected_date.isoformat())
        self.destroy()

class TransactionsTab(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app
        
        today = datetime.date.today()
        self.var_day = tk.StringVar(value=f"{today.day:02d}")
        self.var_month = tk.StringVar(value=f"{today.month:02d}")
        self.var_year = tk.StringVar(value=str(today.year))
        self.var_category = tk.StringVar(value=ASSET_CATEGORIES[0])
        self.var_asset_select = tk.StringVar()
        self.var_custom_name = tk.StringVar()
        self.var_action = tk.StringVar(value="Mua")
        self.var_qty = tk.StringVar()
        self.var_unit = tk.StringVar()
        self.var_unit_price = tk.StringVar()
        self.var_note = tk.StringVar()
        self.var_search = tk.StringVar()
        self.var_filter_cat = tk.StringVar(value="Tất cả")
        self.var_total_preview = tk.StringVar(value="Tổng tiền tạm tính: —")
        self.editing_id = None

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
        date_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        date_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        
        # 3 Entries: Day, Month, Year
        self.ent_day = tk.Entry(date_frame, textvariable=self.var_day, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3, width=4, justify="center")
        self.ent_day.pack(side="left")
        
        lbl_slash1 = tk.Label(date_frame, text="/", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD)
        lbl_slash1.pack(side="left", padx=2)
        
        self.ent_month = tk.Entry(date_frame, textvariable=self.var_month, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3, width=4, justify="center")
        self.ent_month.pack(side="left")
        
        lbl_slash2 = tk.Label(date_frame, text="/", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD)
        lbl_slash2.pack(side="left", padx=2)
        
        self.ent_year = tk.Entry(date_frame, textvariable=self.var_year, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3, width=6, justify="center")
        self.ent_year.pack(side="left")
        
        btn_cal = tk.Button(date_frame, text="📅", command=self._show_calendar,
                            bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", padx=6, pady=2, cursor="hand2")
        btn_cal.pack(side="left", padx=(10, 0))

        # Ràng buộc phím chuyển ô tự động cho Ngày / Tháng / Năm
        self.ent_day.bind("<Key>", self._on_day_key)
        self.ent_month.bind("<Key>", self._on_month_key)
        self.ent_month.bind("<BackSpace>", self._on_month_backspace)
        self.ent_year.bind("<BackSpace>", self._on_year_backspace)

        # 2. Nhóm tài sản
        lbl("Nhóm tài sản:", 1, 0)
        cb_cat = ttk.Combobox(form_frame, textvariable=self.var_category, values=ASSET_CATEGORIES, state="readonly", font=FONT_MAIN)
        cb_cat.grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        cb_cat.bind("<<ComboboxSelected>>", self._on_category_change)

        # 3. Chọn tài sản
        lbl("Tài sản cụ thể:", 2, 0)
        asset_select_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        asset_select_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=4)
        asset_select_frame.columnconfigure(0, weight=1)

        self.cb_asset = ttk.Combobox(asset_select_frame, textvariable=self.var_asset_select, state="readonly", font=FONT_MAIN)
        self.cb_asset.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.cb_asset.bind("<<ComboboxSelected>>", self._on_asset_select_change)

        self.btn_edit_asset = tk.Button(asset_select_frame, text="✏️", command=self._edit_custom_asset,
                                         bg=CLR_ENTRY, fg=CLR_TEXT, font=("Segoe UI", 9), relief="flat", padx=4, cursor="hand2")
        self.btn_edit_asset.grid(row=0, column=1, sticky="e", padx=2)

        self.btn_del_asset = tk.Button(asset_select_frame, text="🗑️", command=self._delete_custom_asset,
                                        bg=CLR_ENTRY, fg=CLR_RED, font=("Segoe UI", 9), relief="flat", padx=4, cursor="hand2")
        self.btn_del_asset.grid(row=0, column=2, sticky="e", padx=2)
        
        self.btn_edit_asset.configure(state="disabled")
        self.btn_del_asset.configure(state="disabled")

        # 4. Khung nhập tài sản tùy chọn (chỉ hiển thị khi chọn Khác/Custom)
        self.custom_assets_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        self.custom_assets_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        tk.Label(self.custom_assets_frame, text="Tên tài sản mới:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=0, sticky="e", padx=5, pady=4)
        
        cust_name_frame = tk.Frame(self.custom_assets_frame, bg=CLR_PANEL)
        cust_name_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=4)
        cust_name_frame.columnconfigure(0, weight=1)
        
        self.ent_cust_name = tk.Entry(cust_name_frame, textvariable=self.var_custom_name, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        self.ent_cust_name.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.btn_save_new_asset = tk.Button(cust_name_frame, text="💾 Lưu", command=self._save_new_custom_asset,
                                            bg="#4f46e5", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=8, cursor="hand2")
        self.btn_save_new_asset.grid(row=0, column=1, sticky="e")
        
        self.custom_assets_frame.columnconfigure(1, weight=1)

        # 5. Hành động (Mua / Bán)
        lbl("Hành động:", 4, 0)
        cb_act = ttk.Combobox(form_frame, textvariable=self.var_action, values=["Mua", "Bán"], state="readonly", font=FONT_MAIN)
        cb_act.grid(row=4, column=1, sticky="ew", padx=5, pady=4)
        cb_act.bind("<<ComboboxSelected>>", lambda _: self._update_price_from_market())

        # 6. Số lượng & Đơn vị
        lbl("Số lượng:", 5, 0)
        qty_unit_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        qty_unit_frame.grid(row=5, column=1, sticky="ew")
        qty_unit_frame.columnconfigure(0, weight=2)
        qty_unit_frame.columnconfigure(2, weight=1)

        ent_qty = tk.Entry(qty_unit_frame, textvariable=self.var_qty, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        ent_qty.grid(row=0, column=0, sticky="ew", padx=(0,5))
        
        tk.Label(qty_unit_frame, text="Đơn vị:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(row=0, column=1, sticky="e", padx=2)
        self.cb_unit = ttk.Combobox(qty_unit_frame, textvariable=self.var_unit, values=["Lượng", "Cây", "Chỉ", "0.1 Chỉ", "0.2 Chỉ", "0.3 Chỉ", "0.5 Chỉ", "2 Chỉ", "3 Chỉ", "5 Chỉ", "Ounce", "Gram", "USD"], font=FONT_MAIN, width=8)
        self.cb_unit.grid(row=0, column=2, sticky="ew")
        self.cb_unit.bind("<<ComboboxSelected>>", self._on_unit_selected)

        # 7. Đơn giá
        lbl("Đơn giá (đ):", 6, 0)
        price_frame = tk.Frame(form_frame, bg=CLR_PANEL)
        price_frame.grid(row=6, column=1, sticky="ew")
        price_frame.columnconfigure(0, weight=1)

        self.ent_price = tk.Entry(price_frame, textvariable=self.var_unit_price, bg=CLR_ENTRY, fg=CLR_TEXT, font=FONT_MAIN, relief="flat", insertbackground=CLR_TEXT, bd=3)
        self.ent_price.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.ent_price.bind("<FocusOut>", self._format_price_on_focus_out)
        self.ent_price.bind("<FocusIn>", self._strip_price_on_focus_in)
        self.ent_price.bind("<Return>", self._format_price_on_focus_out)
        
        btn_get_price = tk.Button(price_frame, text="⚡ Lấy giá thị trường", command=self._update_price_from_market,
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

        self.btn_cancel = tk.Button(btn_grid, text="❌  Hủy", command=self._cancel_edit,
                                     bg="#64748b", fg="white", font=FONT_BOLD, relief="flat", padx=10, pady=6, cursor="hand2")
        # Không pack ban đầu

        self.btn_load = tk.Button(btn_grid, text="✏️  Nạp vào Form", command=self._load_selected,
                              bg="#555588", fg="white", font=FONT_BOLD, relief="flat", padx=10, pady=6, cursor="hand2")
        self.btn_load.pack(side="left", padx=4)

        self.btn_del = tk.Button(btn_grid, text="🗑️  Xóa đã chọn", command=self._delete_selected,
                             bg=CLR_RED, fg="white", font=FONT_BOLD, relief="flat", padx=10, pady=6, cursor="hand2")
        self.btn_del.pack(side="left", padx=4)

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

        # Nút xuất nhập dữ liệu ở bên phải thanh bộ lọc
        btn_export = tk.Button(filter_bar, text="📤 Xuất dữ liệu", command=self._export_data,
                               bg=CLR_BORDER, fg="white", font=("Segoe UI", 8, "bold"),
                               relief="flat", padx=10, pady=3, cursor="hand2")
        btn_export.pack(side="right", padx=4)

        btn_import = tk.Button(filter_bar, text="📥 Nhập dữ liệu", command=self._import_data,
                               bg="#4f46e5", fg="white", font=("Segoe UI", 8, "bold"),
                               relief="flat", padx=10, pady=3, cursor="hand2")
        btn_import.pack(side="right", padx=4)

        # Bảng dữ liệu chính
        cols = ("ID", "Date", "Category", "Asset", "Action", "Qty", "Unit", "Price", "Total", "Note")
        self.tree = ttk.Treeview(hist_frame, columns=cols, show="headings", height=18, selectmode="browse")
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Date", text="Ngày")
        self.tree.heading("Category", text="Nhóm")
        self.tree.heading("Asset", text="Tên tài sản")
        self.tree.heading("Action", text="GD")
        self.tree.heading("Qty", text="SL")
        self.tree.heading("Unit", text="ĐV")
        self.tree.heading("Price", text="Đơn giá")
        self.tree.heading("Total", text="Tổng tiền")
        self.tree.heading("Note", text="Ghi chú")

        self.tree.column("ID", width=35, anchor="center")
        self.tree.column("Date", width=85, anchor="center")
        self.tree.column("Category", width=80, anchor="center")
        self.tree.column("Asset", width=200, anchor="w")
        self.tree.column("Action", width=50, anchor="center")
        self.tree.column("Qty", width=55, anchor="center")
        self.tree.column("Unit", width=45, anchor="center")
        self.tree.column("Price", width=105, anchor="e")
        self.tree.column("Total", width=115, anchor="e")
        self.tree.column("Note", width=160, anchor="w")

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
        
        # Thêm tài sản tùy chỉnh đã lưu
        custom_assets = load_custom_assets()
        assets += [a for a in custom_assets if a["category"] == cat]
        
        vals = [a["name"] for a in assets] + ["Nhập thủ công... (Khác)"]
        self.cb_asset.configure(values=vals)
        
        # Mặc định chọn phần tử đầu tiên
        if vals:
            self.cb_asset.current(0)
            self._on_asset_select_change()

    def _on_asset_select_change(self, event=None):
        """Khi đổi lựa chọn tài sản mẫu."""
        val = self.var_asset_select.get()
        
        # Kiểm tra xem tài sản hiện tại có phải là tùy chỉnh của người dùng không
        custom_assets = load_custom_assets()
        is_custom = any(a["name"] == val for a in custom_assets)
        
        if is_custom:
            self.btn_edit_asset.configure(state="normal")
            self.btn_del_asset.configure(state="normal")
        else:
            self.btn_edit_asset.configure(state="disabled")
            self.btn_del_asset.configure(state="disabled")

        if val == "Nhập thủ công... (Khác)":
            self.custom_assets_frame.grid()
            self.var_custom_name.set("")
            self.var_unit.set("")
        else:
            self.custom_assets_frame.grid_remove()
            # Lấy thông tin từ mặc định hoặc tùy chỉnh
            asset_info = next((a for a in DEFAULT_ASSETS if a["name"] == val), None)
            if not asset_info:
                asset_info = next((a for a in custom_assets if a["name"] == val), None)
                
            if asset_info:
                self.var_custom_name.set(asset_info["name"])
                self.var_unit.set(asset_info["unit"])
                
        # Đồng bộ đơn vị cơ sở
        self.last_unit = self.var_unit.get()
        
        # Thử lấy giá thị trường điền sẵn
        self._update_price_from_market()

    def _on_unit_selected(self, event=None):
        """Tự động quy đổi số lượng và đơn giá khi đổi đơn vị vàng (Lượng, Cây, Chỉ, Ounce)."""
        new_unit = self.var_unit.get().strip()
        old_unit = getattr(self, "last_unit", "")
        
        # Cập nhật cho lần kế tiếp
        self.last_unit = new_unit
        
        if not old_unit or old_unit == new_unit:
            return
            
        # Bản đồ quy đổi sang Ounce làm đơn vị trung gian
        factors = {
            "lượng": 1.2057,
            "cây": 1.2057,
            "cay": 1.2057,
            "luong": 1.2057,
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
            "oz": 1.0
        }
        
        old_key = old_unit.lower()
        new_key = new_unit.lower()
        
        if old_key in factors and new_key in factors:
            try:
                # Đọc số lượng và đơn giá hiện tại
                qty_val = float(self.var_qty.get())
                price_val = float(self.var_unit_price.get().replace(",", ""))
                
                # Tính tỷ lệ quy đổi
                ratio = factors[old_key] / factors[new_key]
                new_qty = qty_val * ratio
                new_price = price_val / ratio
                
                # Cập nhật giao diện
                self.var_qty.set(f"{new_qty:g}")
                self.var_unit_price.set(f"{new_price:,.0f}")
                self.main_app.var_status.set(f"🔄 Đã tự động quy đổi: {qty_val:g} {old_unit} ➔ {new_qty:g} {new_unit}")
            except ValueError:
                pass

    def _update_total_preview(self, *_):
        """Cập nhật preview tổng tiền = số lượng * đơn giá."""
        try:
            qty = float(self.var_qty.get())
            price = float(self.var_unit_price.get().replace(",", ""))
            total = qty * price
            self.var_total_preview.set(f"Tổng tiền tạm tính: {total:,.0f} đ")
        except ValueError:
            self.var_total_preview.set("Tổng tiền tạm tính: —")

    def get_date(self):
        """Trả về ngày dưới dạng YYYY-MM-DD từ 3 ô nhập."""
        try:
            d_str = self.var_day.get().strip()
            m_str = self.var_month.get().strip()
            y_str = self.var_year.get().strip()
            
            if not d_str or not m_str or not y_str:
                return ""
                
            d = int(d_str)
            m = int(m_str)
            y = int(y_str)
            
            # Kiểm tra ngày tháng năm hợp lệ
            datetime.date(y, m, d)
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            return ""

    def set_date(self, date_str):
        """Đặt giá trị cho 3 ô nhập ngày, tháng, năm từ chuỗi YYYY-MM-DD."""
        try:
            date_obj = datetime.date.fromisoformat(date_str)
            self.var_day.set(f"{date_obj.day:02d}")
            self.var_month.set(f"{date_obj.month:02d}")
            self.var_year.set(str(date_obj.year))
        except Exception:
            pass

    def _format_price_on_focus_out(self, event=None):
        """Định dạng đơn giá có dấu phân cách hàng nghìn khi rời khỏi ô hoặc nhấn Enter."""
        try:
            val = self.var_unit_price.get()
            clean_val = "".join([c for c in val.replace(",", "") if c.isdigit()])
            if clean_val:
                self.var_unit_price.set(f"{int(clean_val):,}")
        except Exception:
            pass

    def _strip_price_on_focus_in(self, event=None):
        """Xóa dấu phẩy phân cách khi bắt đầu gõ để tránh lỗi nhảy con trỏ chuột."""
        try:
            val = self.var_unit_price.get()
            clean_val = val.replace(",", "")
            self.var_unit_price.set(clean_val)
            # Chuyển con trỏ xuống cuối, không bôi đen
            self.ent_price.icursor(tk.END)
        except Exception:
            pass

    def _show_calendar(self):
        """Hiển thị cửa sổ chọn ngày trực quan."""
        CalendarDialog(self, self.get_date(), self.set_date)

    def _update_price_from_market(self):
        """Tìm trong bảng giá thực tế và pre-fill giá giao dịch theo Nhóm tài sản (Vàng/Bạc) và tự động quy đổi đơn vị."""
        cat = self.var_category.get()
        if cat in self.main_app.current_prices:
            prices = self.main_app.current_prices[cat]
            action = self.var_action.get()
            price = prices["sell"] if action == "Mua" else prices["buy"]
            price_unit = prices.get("unit", "Lượng")
            form_unit = self.var_unit.get().strip()
            
            def get_factor(u_str):
                u = str(u_str).strip().lower()
                factors = {
                    "lượng": 1.2057,
                    "cây": 1.2057,
                    "cay": 1.2057,
                    "luong": 1.2057,
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
                    "oz": 1.0
                }
                return factors.get(u, 1.0)
                
            if price > 0:
                ratio = get_factor(price_unit) / get_factor(form_unit)
                converted_price = price / ratio
                self.var_unit_price.set(f"{converted_price:,.0f}")
                self.main_app.var_status.set(f"⚡ Đã tự động điền giá hiện tại cho {cat} ({action}): {converted_price:,.0f} đ/{form_unit}")

    def refresh_table(self):
        """Lọc dữ liệu lịch sử và hiển thị ra bảng."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        search_kw = self.var_search.get().lower().strip()
        filter_cat = self.var_filter_cat.get()

        for r in sorted(self.main_app.db, key=lambda x: x.get("date", ""), reverse=True):
            # Lọc theo Nhóm
            cat = r.get("category", "Vàng")
            if filter_cat != "Tất cả" and cat != filter_cat:
                continue

            # Lọc theo Từ khóa tìm kiếm
            asset_name = r.get("asset", "").lower()
            note = r.get("note", "").lower()
            
            if search_kw:
                if (search_kw not in asset_name and 
                    search_kw not in note and 
                    search_kw not in r.get("date", "")):
                    continue

            tag = "buy" if r["action"] == "Mua" else "sell"
            action_str = "🟢 Mua" if r["action"] == "Mua" else "🔴 Bán"
            self.tree.insert("", "end", tags=(tag,), values=(
                r["id"],
                r.get("date", ""),
                cat,
                r["asset"],
                action_str,
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

        # Lấy tên tài sản
        asset_select = self.var_asset_select.get()
        if asset_select == "Nhập thủ công... (Khác)":
            asset_name = self.var_custom_name.get().strip()
            if not asset_name:
                messagebox.showerror("Lỗi", "Nhập thủ công yêu cầu đầy đủ Tên tài sản!")
                return
                
            # Lưu tài sản tự định nghĩa nếu chưa tồn tại
            custom_assets = load_custom_assets()
            if not any(a["name"].lower() == asset_name.lower() for a in DEFAULT_ASSETS) and \
               not any(a["name"].lower() == asset_name.lower() for a in custom_assets):
                new_asset = {
                    "name": asset_name,
                    "category": self.var_category.get(),
                    "unit": self.var_unit.get().strip()
                }
                custom_assets.append(new_asset)
                save_custom_assets(custom_assets)
        else:
            asset_name = asset_select

        tx_date = self.get_date()
        if not tx_date:
            messagebox.showerror("Lỗi", "Vui lòng nhập ngày giao dịch hợp lệ (Ngày/Tháng/Năm)!")
            return

        if self.editing_id is not None:
            # Chế độ Chỉnh sửa
            record = next((r for r in self.main_app.db if r["id"] == self.editing_id), None)
            if not record:
                messagebox.showerror("Lỗi", "Không tìm thấy giao dịch để cập nhật!")
                self._cancel_edit()
                return
            
            record["date"] = tx_date
            record["category"] = self.var_category.get()
            record["asset"] = asset_name
            record["action"] = self.var_action.get()
            record["quantity"] = qty
            record["unit"] = self.var_unit.get().strip()
            record["unit_price"] = price
            record["total"] = qty * price
            record["note"] = self.var_note.get().strip()
            
            save_db(self.main_app.db)
            
            # Reset trạng thái edit
            self.editing_id = None
            self.btn_add.configure(text="➕  Thêm giao dịch", bg=CLR_GREEN)
            self.btn_cancel.pack_forget()
            msg = f"✅ Đã cập nhật giao dịch ID {record['id']} thành công."
        else:
            # Chế độ Thêm mới
            record = {
                "id": next_id(self.main_app.db),
                "date": tx_date,
                "category": self.var_category.get(),
                "asset": asset_name,
                "action": self.var_action.get(),
                "quantity": qty,
                "unit": self.var_unit.get().strip(),
                "unit_price": price,
                "total": qty * price,
                "note": self.var_note.get().strip()
            }
            self.main_app.db.append(record)
            save_db(self.main_app.db)
            msg = f"✅ Đã thêm: {record['action']} {qty} {record['unit']} {record['asset']} thành công."
        
        # Reset form
        self.var_qty.set("")
        self.var_unit_price.set("")
        self.var_note.set("")
        self.var_total_preview.set("Tổng tiền tạm tính: —")

        # Cập nhật các bảng
        self._on_category_change()
        self.refresh_table()
        self.main_app.refresh_portfolio_view()
        
        self.main_app.var_status.set(msg)

    def _cancel_edit(self):
        """Hủy bỏ chế độ chỉnh sửa giao dịch, quay lại thêm mới."""
        self.editing_id = None
        self.btn_add.configure(text="➕  Thêm giao dịch", bg=CLR_GREEN)
        self.btn_cancel.pack_forget()
        
        # Reset form
        self.var_qty.set("")
        self.var_unit_price.set("")
        self.var_note.set("")
        self.var_total_preview.set("Tổng tiền tạm tính: —")

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

        self.editing_id = iid
        self.btn_add.configure(text="💾  Lưu thay đổi", bg=CLR_GOLD)
        
        # Hiển thị nút Hủy bằng cách repack lại theo thứ tự
        self.btn_add.pack_forget()
        self.btn_cancel.pack_forget()
        self.btn_load.pack_forget()
        self.btn_del.pack_forget()
        
        self.btn_add.pack(side="left", padx=4)
        self.btn_cancel.pack(side="left", padx=4)
        self.btn_load.pack(side="left", padx=4)
        self.btn_del.pack(side="left", padx=4)

        self.set_date(rec.get("date", ""))
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

        self.var_action.set(rec["action"])
        self.var_qty.set(f"{rec['quantity']:g}")
        self.var_unit.set(rec["unit"])
        self.var_unit_price.set(f"{rec['unit_price']:,.0f}")
        self.last_unit = rec["unit"]
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

    def _edit_custom_asset(self):
        """Chỉnh sửa tên tài sản tùy chọn."""
        val = self.var_asset_select.get()
        custom_assets = load_custom_assets()
        asset_info = next((a for a in custom_assets if a["name"] == val), None)
        if not asset_info:
            return
            
        from tkinter import simpledialog
        new_name = simpledialog.askstring("Chỉnh sửa tài sản", f"Nhập tên mới cho tài sản '{val}':", initialvalue=val)
        if not new_name:
            return
            
        new_name = new_name.strip()
        if not new_name:
            return
            
        if any(a["name"].lower() == new_name.lower() for a in DEFAULT_ASSETS) or \
           any(a["name"].lower() == new_name.lower() and a["name"] != val for a in custom_assets):
            messagebox.showerror("Lỗi", "Tên tài sản này đã tồn tại!")
            return
            
        # Cập nhật tên trong custom_assets
        for a in custom_assets:
            if a["name"] == val:
                a["name"] = new_name
                
        # Cập nhật tên trong các giao dịch cũ để tránh mất liên kết
        for tx in self.main_app.db:
            if tx.get("asset") == val:
                tx["asset"] = new_name
                
        save_custom_assets(custom_assets)
        save_db(self.main_app.db)
        
        # Làm mới và chọn tên mới
        self._on_category_change()
        self.var_asset_select.set(new_name)
        self._on_asset_select_change()
        self.refresh_table()
        
        self.main_app.var_status.set(f"✏️ Đã đổi tên tài sản từ '{val}' thành '{new_name}'.")

    def _delete_custom_asset(self):
        """Xóa tài sản tùy chọn khỏi bộ nhớ."""
        val = self.var_asset_select.get()
        custom_assets = load_custom_assets()
        asset_info = next((a for a in custom_assets if a["name"] == val), None)
        if not asset_info:
            return
            
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa tài sản tùy chọn '{val}' khỏi danh sách lưu trữ?"):
            custom_assets = [a for a in custom_assets if a["name"] != val]
            save_custom_assets(custom_assets)
            
            # Làm mới danh sách
            self._on_category_change()
            self.main_app.var_status.set(f"🗑️ Đã xóa tài sản tùy chọn '{val}'.")

    def _save_new_custom_asset(self):
        """Lưu tài sản tự định nghĩa mới từ ô nhập thủ công."""
        asset_name = self.var_custom_name.get().strip()
        if not asset_name:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên tài sản mới!")
            return
            
        custom_assets = load_custom_assets()
        # Kiểm tra trùng lặp
        if any(a["name"].lower() == asset_name.lower() for a in DEFAULT_ASSETS) or \
           any(a["name"].lower() == asset_name.lower() for a in custom_assets):
            messagebox.showerror("Lỗi", "Tên tài sản này đã tồn tại trong danh mục!")
            return
            
        # Lưu vào custom_assets.json
        new_asset = {
            "name": asset_name,
            "category": self.var_category.get(),
            "unit": self.var_unit.get().strip() or "Lượng"
        }
        custom_assets.append(new_asset)
        save_custom_assets(custom_assets)
        
        # Làm mới Combobox và chọn tài sản mới lưu này
        self._on_category_change()
        self.var_asset_select.set(asset_name)
        self._on_asset_select_change()
        
        self.main_app.var_status.set(f"💾 Đã lưu và kích hoạt tài sản tùy chọn mới: '{asset_name}'.")

    def _on_day_key(self, event):
        """Khi gõ phím ở ô Ngày, tự chuyển sang ô Tháng nếu đủ 2 kí tự hoặc gõ dấu phân cách."""
        char = event.char
        if char in ("/", ".", " ", "-"):
            self.ent_month.focus_set()
            self.ent_month.selection_range(0, tk.END)
            return "break"
        self.after(10, self._check_day_jump)

    def _check_day_jump(self):
        val = "".join([c for c in self.var_day.get() if c.isdigit()])
        if len(val) >= 2:
            self.ent_month.focus_set()
            self.ent_month.selection_range(0, tk.END)

    def _on_month_key(self, event):
        """Khi gõ phím ở ô Tháng, tự chuyển sang ô Năm nếu đủ 2 kí tự hoặc gõ dấu phân cách."""
        char = event.char
        if char in ("/", ".", " ", "-"):
            self.ent_year.focus_set()
            self.ent_year.selection_range(0, tk.END)
            return "break"
        self.after(10, self._check_month_jump)

    def _check_month_jump(self):
        val = "".join([c for c in self.var_month.get() if c.isdigit()])
        if len(val) >= 2:
            self.ent_year.focus_set()
            self.ent_year.selection_range(0, tk.END)

    def _on_month_backspace(self, event):
        """Khi xóa phím Backspace ở ô Tháng trống, tự quay về ô Ngày và xóa luôn kí tự cuối của ô Ngày."""
        if not self.var_month.get():
            self.ent_day.focus_set()
            val = self.var_day.get()
            if val:
                self.var_day.set(val[:-1])
            self.ent_day.icursor(tk.END)
            return "break"

    def _on_year_backspace(self, event):
        """Khi xóa phím Backspace ở ô Năm trống, tự quay về ô Tháng và xóa luôn kí tự cuối của ô Tháng."""
        if not self.var_year.get():
            self.ent_month.focus_set()
            val = self.var_month.get()
            if val:
                self.var_month.set(val[:-1])
            self.ent_month.icursor(tk.END)
            return "break"

    def _export_data(self):
        from tkinter import filedialog
        import csv
        import json
        import os
        import datetime
        
        if not self.main_app.db:
            messagebox.showwarning("Chú ý", "Không có dữ liệu giao dịch để xuất!")
            return
            
        # Tự động tạo thư mục exports riêng biệt
        project_root = os.path.dirname(os.path.abspath(__file__))
        exports_dir = os.path.join(project_root, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        
        default_name = f"giao_dich_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = filedialog.asksaveasfilename(
            title="Chọn nơi lưu file xuất dữ liệu",
            initialdir=exports_dir,
            initialfile=default_name,
            defaultextension=".xlsx",
            filetypes=[
                ("Excel Files", "*.xlsx"),
                ("CSV Files", "*.csv"),
                ("JSON Files", "*.json")
            ]
        )
        if not filepath:
            return
            
        try:
            if filepath.endswith(".json"):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self.main_app.db, f, ensure_ascii=False, indent=2)
            elif filepath.endswith(".csv"):
                with open(filepath, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    # Tiêu đề cột tiếng Việt để người dùng dễ đọc và sửa bằng Excel
                    writer.writerow(["ID", "Ngày", "Nhóm", "Tên tài sản", "Hành động", "Số lượng", "Đơn vị", "Đơn giá", "Tổng tiền", "Ghi chú"])
                    for r in self.main_app.db:
                        writer.writerow([
                            r["id"],
                            r.get("date", ""),
                            r.get("category", ""),
                            r["asset"],
                            r["action"],
                            r["quantity"],
                            r["unit"],
                            r["unit_price"],
                            r["total"],
                            r.get("note", "")
                        ])
            elif filepath.endswith(".xlsx"):
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Giao Dịch"
                
                # Ghi dòng tiêu đề
                headers = ["ID", "Ngày", "Nhóm", "Tên tài sản", "Hành động", "Số lượng", "Đơn vị", "Đơn giá", "Tổng tiền", "Ghi chú"]
                ws.append(headers)
                
                # Ghi dữ liệu giao dịch
                for r in self.main_app.db:
                    ws.append([
                        r["id"],
                        r.get("date", ""),
                        r.get("category", ""),
                        r["asset"],
                        r["action"],
                        r["quantity"],
                        r["unit"],
                        r["unit_price"],
                        r["total"],
                        r.get("note", "")
                    ])
                wb.save(filepath)
                
            messagebox.showinfo("Thành công", f"Đã xuất dữ liệu thành công ra file:\n{filepath}")
            self.main_app.var_status.set(f"📤 Đã xuất dữ liệu thành công ra file.")
        except Exception as e:
            messagebox.showerror("Lỗi xuất file", f"Đã xảy ra lỗi khi ghi file: {e}")

    def _import_data(self):
        from tkinter import filedialog
        import csv
        import json
        import datetime
        import os
        
        # Mở mặc định tại thư mục exports
        project_root = os.path.dirname(os.path.abspath(__file__))
        exports_dir = os.path.join(project_root, "exports")
        
        filepath = filedialog.askopenfilename(
            title="Chọn file dữ liệu để nhập",
            initialdir=exports_dir,
            filetypes=[
                ("All Supported Files", "*.json;*.csv;*.xlsx;*.xls"),
                ("Excel Files", "*.xlsx;*.xls"),
                ("CSV Files", "*.csv"),
                ("JSON Files", "*.json")
            ]
        )
        if not filepath:
            return
            
        try:
            imported_data = []
            if filepath.endswith(".json"):
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError("Dữ liệu JSON phải là một danh sách các giao dịch.")
                    # Validate basic fields
                    for item in data:
                        if not all(k in item for k in ["date", "asset", "action", "quantity", "unit", "unit_price"]):
                            raise ValueError("Một số bản ghi thiếu trường bắt buộc (date, asset, action, quantity, unit, unit_price).")
                        imported_data.append({
                            "date": str(item["date"]),
                            "category": str(item.get("category", "Vàng")),
                            "asset": str(item["asset"]),
                            "action": str(item["action"]),
                            "quantity": float(item["quantity"]),
                            "unit": str(item["unit"]),
                            "unit_price": float(item["unit_price"]),
                            "total": float(item.get("total", float(item["quantity"]) * float(item["unit_price"]))),
                            "note": str(item.get("note", ""))
                        })
            elif filepath.endswith(".csv"):
                with open(filepath, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    if not header:
                        raise ValueError("File CSV trống.")
                    
                    # Chuẩn hóa header về chữ thường không dấu để dễ so sánh
                    header_norm = [h.strip().lower() for h in header]
                    
                    # Hàm tìm index cột dựa vào tên cột tiếng Anh hoặc tiếng Việt
                    def find_col(aliases):
                        for alias in aliases:
                            if alias in header_norm:
                                return header_norm.index(alias)
                        return -1
                        
                    idx_date = find_col(["date", "ngày", "ngay"])
                    idx_cat = find_col(["category", "nhóm", "nhom", "nhóm tài sản", "nhom tai san"])
                    idx_asset = find_col(["asset", "tên tài sản", "ten tai san", "tên", "ten"])
                    idx_action = find_col(["action", "hành động", "hanh dong", "gd"])
                    idx_qty = find_col(["quantity", "số lượng", "so luong", "sl"])
                    idx_unit = find_col(["unit", "đơn vị", "don vi", "đv"])
                    idx_price = find_col(["unitprice", "unit_price", "đơn giá", "don gia", "giá", "gia"])
                    idx_total = find_col(["total", "tổng tiền", "tong tien", "tổng", "tong"])
                    idx_note = find_col(["note", "ghi chú", "ghi chu"])
                    
                    # Kiểm tra các cột bắt buộc
                    required_cols = [
                        (idx_date, "Ngày (Date)"),
                        (idx_asset, "Tên tài sản (Asset)"),
                        (idx_action, "Hành động (Action)"),
                        (idx_qty, "Số lượng (Quantity)"),
                        (idx_unit, "Đơn vị (Unit)"),
                        (idx_price, "Đơn giá (UnitPrice)")
                    ]
                    for idx, col_name in required_cols:
                        if idx == -1:
                            raise ValueError(f"Không tìm thấy cột bắt buộc: {col_name} trong file CSV.")
                            
                    for row in reader:
                        if not row or len(row) < max(idx_date, idx_asset, idx_action, idx_qty, idx_unit, idx_price) + 1:
                            continue
                        
                        qty = float(row[idx_qty].replace(",", "").strip())
                        price = float(row[idx_price].replace(",", "").strip())
                        total = float(row[idx_total].replace(",", "").strip()) if (idx_total != -1 and row[idx_total].strip()) else qty * price
                        
                        imported_data.append({
                            "date": row[idx_date].strip(),
                            "category": row[idx_cat].strip() if idx_cat != -1 else "Vàng",
                            "asset": row[idx_asset].strip(),
                            "action": row[idx_action].strip(),
                            "quantity": qty,
                            "unit": row[idx_unit].strip(),
                            "unit_price": price,
                            "total": total,
                            "note": row[idx_note].strip() if idx_note != -1 else ""
                        })
            elif filepath.endswith((".xlsx", ".xls")):
                import openpyxl
                wb = openpyxl.load_workbook(filepath, data_only=True)
                ws = wb.active
                
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    raise ValueError("File Excel trống.")
                    
                header = rows[0]
                if not header:
                    raise ValueError("Không tìm thấy dòng tiêu đề trong file Excel.")
                    
                header_norm = [str(h).strip().lower() if h is not None else "" for h in header]
                
                def find_col(aliases):
                    for alias in aliases:
                        if alias in header_norm:
                            return header_norm.index(alias)
                    return -1
                    
                idx_date = find_col(["date", "ngày", "ngay"])
                idx_cat = find_col(["category", "nhóm", "nhom", "nhóm tài sản", "nhom tai san"])
                idx_asset = find_col(["asset", "tên tài sản", "ten tai san", "tên", "ten"])
                idx_action = find_col(["action", "hành động", "hanh dong", "gd"])
                idx_qty = find_col(["quantity", "số lượng", "so luong", "sl"])
                idx_unit = find_col(["unit", "đơn vị", "don vi", "đv"])
                idx_price = find_col(["unitprice", "unit_price", "đơn giá", "don gia", "giá", "gia"])
                idx_total = find_col(["total", "tổng tiền", "tong tien", "tổng", "tong"])
                idx_note = find_col(["note", "ghi chú", "ghi chu"])
                
                required_cols = [
                    (idx_date, "Ngày (Date)"),
                    (idx_asset, "Tên tài sản (Asset)"),
                    (idx_action, "Hành động (Action)"),
                    (idx_qty, "Số lượng (Quantity)"),
                    (idx_unit, "Đơn vị (Unit)"),
                    (idx_price, "Đơn giá (UnitPrice)")
                ]
                for idx, col_name in required_cols:
                    if idx == -1:
                        raise ValueError(f"Không tìm thấy cột bắt buộc: {col_name} trong file Excel.")
                        
                for row in rows[1:]:
                    if not row or all(v is None for v in row):
                        continue
                    if len(row) < max(idx_date, idx_asset, idx_action, idx_qty, idx_unit, idx_price) + 1:
                        continue
                        
                    def clean_str(val):
                        return str(val).strip() if val is not None else ""
                        
                    def clean_float(val):
                        if val is None:
                            return 0.0
                        if isinstance(val, (int, float)):
                            return float(val)
                        try:
                            return float(str(val).replace(",", "").strip())
                        except ValueError:
                            return 0.0

                    qty = clean_float(row[idx_qty])
                    price = clean_float(row[idx_price])
                    total = clean_float(row[idx_total]) if (idx_total != -1 and row[idx_total] is not None) else qty * price
                    
                    date_val = row[idx_date]
                    if isinstance(date_val, datetime.date) or isinstance(date_val, datetime.datetime):
                        date_str = date_val.strftime("%Y-%m-%d")
                    else:
                        date_str = clean_str(date_val)
                        
                    imported_data.append({
                        "date": date_str,
                        "category": clean_str(row[idx_cat]) if idx_cat != -1 else "Vàng",
                        "asset": clean_str(row[idx_asset]),
                        "action": clean_str(row[idx_action]),
                        "quantity": qty,
                        "unit": clean_str(row[idx_unit]),
                        "unit_price": price,
                        "total": total,
                        "note": clean_str(row[idx_note]) if idx_note != -1 else ""
                    })
                        
            if not imported_data:
                messagebox.showwarning("Chú ý", "Không tìm thấy dữ liệu hợp lệ để nhập.")
                return
                
            # Hỏi người dùng muốn Gộp hay Ghi đè
            choice = messagebox.askyesnocancel(
                "Nhập dữ liệu",
                f"Tìm thấy {len(imported_data)} giao dịch.\n\n"
                "- Chọn 'Yes' để Gộp (Merge) vào dữ liệu hiện có.\n"
                "- Chọn 'No' để Ghi đè (Replace) hoàn toàn dữ liệu cũ.\n"
                "- Chọn 'Cancel' để Hủy thao tác nhập.",
                default=messagebox.YES
            )
            
            if choice is None: # Cancel
                return
                
            if choice: # Yes = Gộp
                for item in imported_data:
                    item["id"] = next_id(self.main_app.db)
                    self.main_app.db.append(item)
                action_text = "Gộp"
            else: # No = Ghi đè
                for idx, item in enumerate(imported_data):
                    item["id"] = idx + 1
                self.main_app.db = imported_data
                action_text = "Ghi đè"
                
            save_db(self.main_app.db)
            
            self.refresh_table()
            self.main_app.refresh_portfolio_view()
            messagebox.showinfo("Thành công", f"Đã {action_text} thành công {len(imported_data)} giao dịch.")
            self.main_app.var_status.set(f"✅ Đã nhập thành công {len(imported_data)} giao dịch từ file.")
            
        except Exception as e:
            messagebox.showerror("Lỗi nhập file", f"Đã xảy ra lỗi khi đọc file: {e}")
