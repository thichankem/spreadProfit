# ui_charts.py
"""
Tab hiển thị các biểu đồ trực quan phân tích tài sản bằng Matplotlib.
Nhúng trực tiếp biểu đồ vào giao diện Tkinter.
"""

import tkinter as tk
from config import *
from db_manager import calculate_portfolio

# Import Matplotlib để vẽ biểu đồ
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class ChartsTab(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app
        
        self.canvas_widget = None
        self._build_ui()

    def _build_ui(self):
        # Thanh tiêu đề và nút làm mới biểu đồ
        header_frame = tk.Frame(self, bg=CLR_BG)
        header_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(header_frame, text="📊  BIỂU ĐỒ PHÂN TÍCH TÀI SẢN & LỢI NHUẬN",
                 font=FONT_BOLD, bg=CLR_BG, fg=CLR_HEAD).pack(side="left")

        btn_draw = tk.Button(header_frame, text="🔄  Tải lại biểu đồ", command=self.draw_charts,
                             bg="#4f46e5", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=4, cursor="hand2")
        btn_draw.pack(side="right")

        # Khung chứa Canvas biểu đồ chính
        self.chart_container = tk.Frame(self, bg=CLR_BG)
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=5)

    def draw_charts(self):
        """Vẽ lại các biểu đồ dựa trên dữ liệu mới nhất từ DB và giá hiện tại."""
        # Xóa biểu đồ cũ trên canvas nếu có
        if self.canvas_widget:
            self.canvas_widget.destroy()

        # Tính toán dữ liệu portfolio hiện tại
        holdings, summary = calculate_portfolio(self.main_app.db, self.main_app.current_prices)

        if not holdings:
            # Vẽ thông báo rỗng nếu không có dữ liệu tài sản
            no_data_lbl = tk.Label(self.chart_container, text="⚠️  Chưa có dữ liệu tài sản để hiển thị biểu đồ phân tích.\nVui lòng thêm giao dịch mua bán để xem phân bổ.",
                                   font=FONT_BIG, bg=CLR_BG, fg=CLR_TEXT_MUTED)
            no_data_lbl.pack(fill="both", expand=True)
            self.canvas_widget = no_data_lbl
            return

        # Khởi tạo Figure chứa 3 biểu đồ
        # Bố cục: 2 dòng. Dòng 1 gồm 2 cột (Pie chart + Grouped Bar chart). Dòng 2 chứa Bar chart Lời lỗ theo tài sản.
        fig = Figure(figsize=(11, 7), dpi=95, facecolor=CLR_BG)
        
        # 1. BIỂU ĐỒ TRÒN (PHÂN BỔ TÀI SẢN THEO GIÁ TRỊ)
        ax1 = fig.add_subplot(221)
        ax1.set_facecolor(CLR_PANEL)
        
        # Gom nhóm giá trị theo Category
        cat_values = {}
        for h in holdings.values():
            cat = h["category"]
            cat_values[cat] = cat_values.get(cat, 0.0) + h["current_value"]

        # Loại bỏ các nhóm có giá trị = 0
        cat_values = {k: v for k, v in cat_values.items() if v > 0}
        
        if cat_values:
            labels = list(cat_values.keys())
            sizes = list(cat_values.values())
            
            # Cấu hình màu sắc đồng bộ cho biểu đồ tròn
            colors = ["#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#6b7280"]
            
            wedges, texts, autotexts = ax1.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors[:len(labels)], textprops={'color': CLR_TEXT, 'fontsize': 8},
                wedgeprops={'edgecolor': CLR_BG, 'linewidth': 1.5}
            )
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
            ax1.set_title("Phân bổ Danh mục (Giá trị)", color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
        else:
            ax1.text(0.5, 0.5, "Không có dữ liệu giá trị", color=CLR_TEXT_MUTED, ha='center', va='center')

        # 2. BIỂU ĐỒ CỘT SO SÁNH VỐN VS GIÁ TRỊ THỰC TẾ
        ax2 = fig.add_subplot(222)
        ax2.set_facecolor(CLR_PANEL)
        
        # Gom nhóm vốn (cost) và giá trị hiện tại (value) theo Category
        cat_cost = {}
        cat_val = {}
        for h in holdings.values():
            cat = h["category"]
            cat_cost[cat] = cat_cost.get(cat, 0.0) + h["cost"]
            cat_val[cat] = cat_val.get(cat, 0.0) + h["current_value"]

        all_cats = sorted(list(set(list(cat_cost.keys()) + list(cat_val.keys()))))
        if all_cats:
            costs_m = [cat_cost.get(c, 0.0) / 1_000_000 for c in all_cats]  # Quy đổi sang Triệu đồng
            vals_m = [cat_val.get(c, 0.0) / 1_000_000 for c in all_cats]
            
            import numpy as np
            x = np.arange(len(all_cats))
            width = 0.35
            
            rects1 = ax2.bar(x - width/2, costs_m, width, label='Vốn đầu tư', color='#64748b') # Xám xanh
            rects2 = ax2.bar(x + width/2, vals_m, width, label='Giá trị hiện tại', color=CLR_GOLD) # Vàng
            
            ax2.set_title("Vốn vs Giá trị (Triệu đ)", color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
            ax2.set_xticks(x)
            ax2.set_xticklabels(all_cats, color=CLR_TEXT, fontsize=8)
            ax2.tick_params(colors=CLR_TEXT_MUTED, labelsize=8)
            ax2.grid(True, linestyle='--', alpha=0.1, color='#fff')
            ax2.legend(facecolor=CLR_PANEL, edgecolor=CLR_BORDER, labelcolor=CLR_TEXT, fontsize=7)
        else:
            ax2.text(0.5, 0.5, "Không có dữ liệu", color=CLR_TEXT_MUTED, ha='center', va='center')

        # 3. BIỂU ĐỒ CỘT LỜI/LỖ RÒNG THEO TỪNG TÀI SẢN
        ax3 = fig.add_subplot(212)
        ax3.set_facecolor(CLR_PANEL)
        
        # Thu thập PnL từng tài sản
        assets_pnl = []
        for asset, h in holdings.items():
            if h["market_price"] > 0:  # Chỉ vẽ nếu có giá thị trường để tính lời lỗ
                assets_pnl.append((asset, h["pnl"] / 1_000_000))  # Quy đổi sang triệu đồng

        # Sắp xếp theo lời lỗ từ cao xuống thấp
        assets_pnl.sort(key=lambda x: x[1])
        
        if assets_pnl:
            names = [item[0] for item in assets_pnl]
            pnls = [item[1] for item in assets_pnl]
            
            # Đổi màu sắc: Lời màu xanh, Lỗ màu đỏ
            bar_colors = [CLR_GREEN if p >= 0 else CLR_RED for p in pnls]
            
            # Vẽ biểu đồ cột ngang (Horizontal Bar)
            bars = ax3.barh(names, pnls, color=bar_colors, edgecolor='none', height=0.6)
            
            ax3.axvline(0, color=CLR_TEXT_MUTED, linewidth=1, linestyle='-')
            ax3.set_title("Lời / Lỗ ròng theo từng Tài sản (Triệu đ)", color=CLR_HEAD, fontproperties={'weight': 'bold', 'size': 10})
            ax3.tick_params(colors=CLR_TEXT, labelsize=8)
            ax3.grid(True, linestyle='--', alpha=0.1, color='#fff')
            
            # Hiển thị số liệu trực tiếp trên đầu cột
            for bar in bars:
                width = bar.get_width()
                # Định vị chữ bên phải cột nếu dương, bên trái cột nếu âm
                align = 'left' if width >= 0 else 'right'
                offset = 0.05 if width >= 0 else -0.05
                ax3.text(
                    width + offset, bar.get_y() + bar.get_height()/2,
                    f"{width:+.1f}M",
                    va='center', ha=align, color=CLR_TEXT, fontsize=7, fontweight='bold'
                )
        else:
            ax3.text(0.5, 0.5, "Chưa có giá thị trường của các tài sản để tính Lời/Lỗ ròng", color=CLR_TEXT_MUTED, ha='center', va='center')

        # Tối ưu hóa khoảng cách giữa các biểu đồ
        fig.tight_layout()

        # Nhúng canvas vào giao diện Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)
