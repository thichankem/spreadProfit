# ui_charts.py
"""
Tab hiển thị các biểu đồ trực quan phân tích tài sản bằng Matplotlib.
Nhúng trực tiếp biểu đồ vào giao diện Tkinter.
"""

import tkinter as tk
from tkinter import ttk
from config import *
from db_manager import calculate_portfolio

# Import Matplotlib để vẽ biểu đồ
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

def truncate_name(name, max_len=18):
    """Rút ngắn tên tài sản nếu quá dài để tránh vỡ giao diện biểu đồ."""
    return name[:max_len-3] + "..." if len(name) > max_len else name

class ChartsTab(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app
        
        self.canvas_widget = None
        # Biến trạng thái cho bộ lọc nhóm tài sản
        self.var_filter_cat = tk.StringVar(value="Tất cả")
        # Biến trạng thái cho bộ lọc tài sản cụ thể
        self.var_filter_asset = tk.StringVar(value="Tất cả")
        self._build_ui()

    def _build_ui(self):
        # Thanh tiêu đề và nút làm mới biểu đồ
        header_frame = tk.Frame(self, bg=CLR_BG)
        header_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(header_frame, text="📊  BIỂU ĐỒ PHÂN TÍCH TÀI SẢN & LỢI NHUẬN",
                 font=FONT_BOLD, bg=CLR_BG, fg=CLR_HEAD).pack(side="left")

        # Thêm Combobox lọc nhóm tài sản
        tk.Label(header_frame, text="Lọc theo Nhóm:", bg=CLR_BG, fg=CLR_TEXT, font=FONT_BOLD).pack(side="left", padx=(20, 5))
        cb_filter = ttk.Combobox(header_frame, textvariable=self.var_filter_cat, values=["Tất cả"] + ASSET_CATEGORIES, state="readonly", font=FONT_MAIN, width=15)
        cb_filter.pack(side="left", padx=5)
        cb_filter.bind("<<ComboboxSelected>>", self._on_category_changed)

        # Thêm Combobox lọc tài sản cụ thể
        tk.Label(header_frame, text="Tài sản:", bg=CLR_BG, fg=CLR_TEXT, font=FONT_BOLD).pack(side="left", padx=(15, 5))
        self.cb_asset_filter = ttk.Combobox(header_frame, textvariable=self.var_filter_asset, values=["Tất cả"], state="readonly", font=FONT_MAIN, width=25)
        self.cb_asset_filter.pack(side="left", padx=5)
        self.cb_asset_filter.bind("<<ComboboxSelected>>", lambda _: self.draw_charts())

        btn_draw = tk.Button(header_frame, text="🔄  Tải lại biểu đồ", command=self.draw_charts,
                             bg="#4f46e5", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=4, cursor="hand2")
        btn_draw.pack(side="right")

        # Khung chứa Canvas biểu đồ chính
        self.chart_container = tk.Frame(self, bg=CLR_BG)
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=5)

    def _on_category_changed(self, event=None):
        self.var_filter_asset.set("Tất cả")
        self.draw_charts()

    def draw_charts(self):
        """Vẽ lại các biểu đồ dựa trên dữ liệu mới nhất từ DB và giá hiện tại."""
        # Xóa biểu đồ cũ trên canvas nếu có
        if self.canvas_widget:
            self.canvas_widget.destroy()

        # Tính toán dữ liệu portfolio hiện tại
        holdings, summary = calculate_portfolio(self.main_app.db, self.main_app.current_prices)

        # Cập nhật danh sách tài sản khả dụng cho Combobox lọc tài sản
        filter_cat = self.var_filter_cat.get()
        available_assets = []
        for name, h in holdings.items():
            if filter_cat == "Tất cả" or h.get("category") == filter_cat:
                available_assets.append(name)
        available_assets = sorted(list(set(available_assets)))
        
        self.cb_asset_filter["values"] = ["Tất cả"] + available_assets
        
        # Nếu tài sản đang chọn không còn nằm trong danh sách khả dụng, reset về "Tất cả"
        current_sel_asset = self.var_filter_asset.get()
        if current_sel_asset != "Tất cả" and current_sel_asset not in available_assets:
            self.var_filter_asset.set("Tất cả")
            current_sel_asset = "Tất cả"

        # Lọc theo Nhóm tài sản được chọn
        if filter_cat != "Tất cả":
            filtered_holdings = {k: v for k, v in holdings.items() if v.get("category") == filter_cat}
        else:
            filtered_holdings = holdings

        # Lọc theo Tài sản cụ thể được chọn
        if current_sel_asset != "Tất cả":
            filtered_holdings = {k: v for k, v in filtered_holdings.items() if k == current_sel_asset}

        if not filtered_holdings:
            # Vẽ thông báo rỗng nếu không có dữ liệu tài sản
            no_data_lbl = tk.Label(self.chart_container, text=f"⚠️  Không có dữ liệu tài sản nhóm '{filter_cat}' để hiển thị biểu đồ.",
                                   font=FONT_BIG, bg=CLR_BG, fg=CLR_TEXT_MUTED)
            no_data_lbl.pack(fill="both", expand=True)
            self.canvas_widget = no_data_lbl
            return

        # Tạo wrapper frame mới chứa cả canvas cuộn và scrollbar
        self.canvas_widget = tk.Frame(self.chart_container, bg=CLR_BG)
        self.canvas_widget.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(self.canvas_widget, bg=CLR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.canvas_widget, orient="vertical", command=scroll_canvas.yview)
        scrollable_frame = tk.Frame(scroll_canvas, bg=CLR_BG)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(
                scrollregion=scroll_canvas.bbox("all")
            )
        )
        
        canvas_window = scroll_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def _configure_width(event):
            scroll_canvas.itemconfig(canvas_window, width=event.width)
            
        scroll_canvas.bind("<Configure>", _configure_width)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Thiết lập sự kiện cuộn chuột
        def _on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
        def _bind_wheel(event):
            scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_wheel(event):
            scroll_canvas.unbind_all("<MouseWheel>")
            
        scroll_canvas.bind("<Enter>", _bind_wheel)
        scroll_canvas.bind("<Leave>", _unbind_wheel)

        # Khởi tạo Figure chứa 5 biểu đồ trong khung cuộn
        fig = Figure(figsize=(11, 11), dpi=95, facecolor=CLR_BG)
        
        # 1. BIỂU ĐỒ VÒNG / DONUT CHART (PHÂN BỔ TÀI SẢN THEO GIÁ TRỊ)
        ax1 = fig.add_subplot(321)
        ax1.set_facecolor(CLR_BG)
        
        # Gom nhóm giá trị theo Category (nếu chọn Tất cả) hoặc theo Asset (nếu lọc Vàng/Bạc)
        pie_data = {}
        if filter_cat == "Tất cả":
            for h in filtered_holdings.values():
                cat = h["category"]
                pie_data[cat] = pie_data.get(cat, 0.0) + h["current_value"]
            title_pie = "Phân bổ Danh mục (Giá trị)"
        else:
            for asset, h in filtered_holdings.items():
                pie_data[asset] = pie_data.get(asset, 0.0) + h["current_value"]
            title_pie = f"Phân bổ {filter_cat} (Giá trị)"

        # Loại bỏ các nhóm có giá trị = 0
        pie_data = {k: v for k, v in pie_data.items() if v > 0}
        
        if pie_data:
            labels = list(pie_data.keys())
            sizes = list(pie_data.values())
            colors = ["#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#6b7280"]
            wedges, texts, autotexts = ax1.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors[:len(labels)], textprops={'color': CLR_TEXT, 'fontsize': 8},
                wedgeprops={'width': 0.4, 'edgecolor': CLR_BG, 'linewidth': 1.5}
            )
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
                autotext.set_color('#ffffff')
            ax1.set_title(title_pie, color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
        else:
            ax1.text(0.5, 0.5, "Không có dữ liệu giá trị", color=CLR_TEXT_MUTED, ha='center', va='center')

        # 2. BIỂU ĐỒ CỘT SO SÁNH VỐN VS GIÁ TRỊ THỰC TẾ
        ax2 = fig.add_subplot(322)
        ax2.set_facecolor(CLR_BG)
        
        cost_data = {}
        val_data = {}
        if filter_cat == "Tất cả":
            for h in filtered_holdings.values():
                cat = h["category"]
                cost_data[cat] = cost_data.get(cat, 0.0) + h["cost"]
                val_data[cat] = val_data.get(cat, 0.0) + h["current_value"]
            title_bar = "Vốn vs Giá trị nhóm (Triệu đ)"
        else:
            for asset, h in filtered_holdings.items():
                cost_data[asset] = cost_data.get(asset, 0.0) + h["cost"]
                val_data[asset] = val_data.get(asset, 0.0) + h["current_value"]
            title_bar = f"Vốn vs Giá trị {filter_cat} (Triệu đ)"

        all_keys = sorted(list(set(list(cost_data.keys()) + list(val_data.keys()))))
        if all_keys:
            costs_m = [cost_data.get(k, 0.0) / 1_000_000 for k in all_keys]
            vals_m = [val_data.get(k, 0.0) / 1_000_000 for k in all_keys]
            
            import numpy as np
            x = np.arange(len(all_keys))
            width = 0.35
            
            rects1 = ax2.bar(x - width/2, costs_m, width, label='Vốn đầu tư', color='#64748b')
            rects2 = ax2.bar(x + width/2, vals_m, width, label='Giá trị hiện tại', color=CLR_GOLD)
            
            ax2.set_title(title_bar, color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
            ax2.set_xticks(x)
            ax2.set_xticklabels(all_keys, color=CLR_TEXT, fontsize=8)
            ax2.tick_params(colors=CLR_TEXT_MUTED, labelsize=8)
            ax2.grid(True, linestyle=':', alpha=0.15, color='#94a3b8')
            ax2.legend(facecolor=CLR_PANEL, edgecolor=CLR_BORDER, labelcolor=CLR_TEXT, fontsize=8, framealpha=0.6)
            
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color(CLR_BORDER)
            ax2.spines['bottom'].set_color(CLR_BORDER)
        else:
            ax2.text(0.5, 0.5, "Không có dữ liệu", color=CLR_TEXT_MUTED, ha='center', va='center')

        # 3. BIỂU ĐỒ XU HƯỚNG MUA THEO NGÀY (LINE CHART)
        ax3 = fig.add_subplot(323)
        ax3.set_facecolor(CLR_BG)
        
        buy_txs = [r for r in self.main_app.db if r["action"] == "Mua"]
        if filter_cat != "Tất cả":
            buy_txs = [r for r in buy_txs if r.get("category", "Vàng") == filter_cat]
        if current_sel_asset != "Tất cả":
            buy_txs = [r for r in buy_txs if r["asset"] == current_sel_asset]
            
        buy_by_date = {}
        for r in buy_txs:
            d = r.get("date", "")
            if d:
                buy_by_date[d] = buy_by_date.get(d, 0.0) + r["total"]
                
        sorted_dates = sorted(buy_by_date.keys())
        if sorted_dates:
            vals_m = [buy_by_date[d] / 1_000_000 for d in sorted_dates]
            short_dates = []
            for d in sorted_dates:
                try:
                    parts = d.split("-")
                    short_dates.append(f"{parts[2]}/{parts[1]}")
                except Exception:
                    short_dates.append(d)
            
            ax3.plot(short_dates, vals_m, marker='o', color='#10b981', linewidth=2, label='Vốn mua')
            ax3.set_title("Lượng mua tích lũy theo Ngày (Triệu đ)", color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
            ax3.tick_params(colors=CLR_TEXT, labelsize=8)
            ax3.grid(True, linestyle=':', alpha=0.15, color='#94a3b8')
            if len(short_dates) > 5:
                ax3.set_xticks(range(len(short_dates)))
                ax3.set_xticklabels(short_dates, rotation=30, ha='right', color=CLR_TEXT, fontsize=7)
            else:
                ax3.set_xticks(range(len(short_dates)))
                ax3.set_xticklabels(short_dates, color=CLR_TEXT, fontsize=8)
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.spines['left'].set_color(CLR_BORDER)
            ax3.spines['bottom'].set_color(CLR_BORDER)
        else:
            ax3.text(0.5, 0.5, "Không có dữ liệu mua", color=CLR_TEXT_MUTED, ha='center', va='center')

        # 4. BIỂU ĐỒ SO SÁNH GIÁ VỐN VS GIÁ THỰC TẾ (GROUPED BAR CHART)
        ax4 = fig.add_subplot(324)
        ax4.set_facecolor(CLR_BG)
        
        compare_data = []
        for asset, h in filtered_holdings.items():
            if h["market_price"] > 0:
                compare_data.append({
                    "asset": asset,
                    "unit": h["unit"],
                    "avg_price": h["avg_price"],
                    "market_price": h["market_price"]
                })
        compare_data.sort(key=lambda x: x["asset"])
        
        if compare_data:
            assets_labels = [f"{truncate_name(item['asset'], 12)}\n({item['unit']})" for item in compare_data]
            avg_prices = [item["avg_price"] / 1_000_000 for item in compare_data]
            market_prices = [item["market_price"] / 1_000_000 for item in compare_data]
            
            import numpy as np
            x = np.arange(len(compare_data))
            width = 0.35
            
            rects1 = ax4.bar(x - width/2, avg_prices, width, label='Giá vốn BQ', color='#64748b')
            rects2 = ax4.bar(x + width/2, market_prices, width, label='Giá thị trường', color=CLR_GOLD)
            
            ax4.set_title("Giá vốn BQ vs Giá thị trường (Tr/Đơn vị)", color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
            ax4.set_xticks(x)
            ax4.set_xticklabels(assets_labels, color=CLR_TEXT, fontsize=8)
            ax4.tick_params(colors=CLR_TEXT_MUTED, labelsize=8)
            ax4.grid(True, linestyle=':', alpha=0.15, color='#94a3b8')
            ax4.legend(facecolor=CLR_PANEL, edgecolor=CLR_BORDER, labelcolor=CLR_TEXT, fontsize=8, framealpha=0.6)
            
            ax4.spines['top'].set_visible(False)
            ax4.spines['right'].set_visible(False)
            ax4.spines['left'].set_color(CLR_BORDER)
            ax4.spines['bottom'].set_color(CLR_BORDER)
        else:
            ax4.text(0.5, 0.5, "Không có dữ liệu so sánh giá", color=CLR_TEXT_MUTED, ha='center', va='center')

        # 5. BIỂU ĐỒ CỘT LỜI/LỖ RÒNG THEO TỪNG TÀI SẢN
        ax5 = fig.add_subplot(313)
        ax5.set_facecolor(CLR_BG)
        
        assets_pnl = []
        for asset, h in filtered_holdings.items():
            if h["market_price"] > 0:
                assets_pnl.append((asset, h["pnl"] / 1_000_000))

        assets_pnl.sort(key=lambda x: x[1])
        
        if assets_pnl:
            ax5.yaxis.set_visible(False)
            pnls = [item[1] for item in assets_pnl]
            import numpy as np
            y_pos = np.arange(len(pnls))
            bar_colors = [CLR_GREEN if p >= 0 else CLR_RED for p in pnls]
            bars = ax5.barh(y_pos, pnls, color=bar_colors, edgecolor='none', height=0.4)
            ax5.axvline(0, color=CLR_TEXT_MUTED, linewidth=1, linestyle='-')
            
            title_pnl = "Lời / Lỗ ròng theo từng Tài sản (Triệu đ)"
            if filter_cat != "Tất cả":
                title_pnl = f"Lời / Lỗ ròng theo Tài sản {filter_cat} (Triệu đ)"
                
            ax5.set_title(title_pnl, color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
            ax5.tick_params(colors=CLR_TEXT, labelsize=8)
            ax5.grid(True, linestyle=':', alpha=0.15, color='#94a3b8')
            
            min_p = min(pnls)
            max_p = max(pnls)
            p_left = min_p - abs(min_p) * 0.25 if min_p < 0 else -1.0
            p_right = max_p + abs(max_p) * 0.25 if max_p > 0 else 1.0
            ax5.set_xlim(p_left, p_right)

            ax5.spines['top'].set_visible(False)
            ax5.spines['right'].set_visible(False)
            ax5.spines['left'].set_visible(False)
            ax5.spines['bottom'].set_color(CLR_BORDER)
            
            for i, bar in enumerate(bars):
                width = bar.get_width()
                asset_full_name = assets_pnl[i][0]
                align_name = 'left' if width >= 0 else 'right'
                offset_name = (p_right * 0.01) if width >= 0 else (p_left * 0.01)
                ax5.text(
                    0 + offset_name, bar.get_y() + bar.get_height() + 0.05,
                    asset_full_name,
                    va='bottom', ha=align_name, color=CLR_TEXT, fontsize=8, fontweight='bold'
                )
                
                align_val = 'left' if width >= 0 else 'right'
                offset_val = (p_right * 0.02) if width >= 0 else (p_left * 0.02)
                ax5.text(
                    width + offset_val, bar.get_y() + bar.get_height()/2,
                    f"{width:+.2f}M" if abs(width) < 1 else f"{width:+.1f}M",
                    va='center', ha=align_val, color=CLR_TEXT, fontsize=7.5, fontweight='bold'
                )
        else:
            ax5.text(0.5, 0.5, "Chưa có giá thị trường của các tài sản để tính Lời/Lỗ ròng", color=CLR_TEXT_MUTED, ha='center', va='center')

        fig.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.06, hspace=0.45, wspace=0.22)

        # Nhúng canvas vào khung cuộn Tkinter
        canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas.draw()
        
        tk_widget = canvas.get_tk_widget()
        tk_widget.pack(fill="both", expand=True)
        
        # Bắt buộc cập nhật kích thước khung cuộn để tránh lỗi cuộn không đúng kích cỡ thực
        scrollable_frame.update_idletasks()
