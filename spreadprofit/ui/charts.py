"""
Visual analytics and charts module for spreadProfit.

Renders embedded Matplotlib charts within Tkinter:
1. Portfolio Asset Allocation (Donut Chart)
2. Invested Capital vs Current Valuation (Bar Chart)
3. Cumulative Purchase Capital by Date (Trend Line Chart)
4. Cost Basis vs Market Benchmark Price (Grouped Bar Chart)
5. Net Unrealized Profit & Loss by Asset (Horizontal Bar Chart)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from spreadprofit.config import (
    ASSET_CATEGORIES,
    CLR_BG,
    CLR_BORDER,
    CLR_GOLD,
    CLR_GREEN,
    CLR_HEAD,
    CLR_PANEL,
    CLR_RED,
    CLR_TEXT,
    CLR_TEXT_MUTED,
    FONT_BIG,
    FONT_BOLD,
    FONT_MAIN,
    normalize_action,
    normalize_category,
    normalize_unit,
)
from spreadprofit.db import calculate_portfolio


def truncate_label(name: str, max_length: int = 18) -> str:
    """Trim lengthy asset labels for chart readability."""
    return f"{name[:max_length - 3]}..." if len(name) > max_length else name


class ChartsTab(tk.Frame):
    """Analytics view embedding scrollable Matplotlib financial charts."""

    def __init__(self, parent: tk.Widget, main_app: Any) -> None:
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app

        self.canvas_widget: Optional[tk.Widget] = None
        self.current_figure: Optional[Figure] = None
        self.var_filter_cat = tk.StringVar(value="All")
        self.var_filter_asset = tk.StringVar(value="All")

        self._build_ui()

    def _build_ui(self) -> None:
        """Create navigation header, category filters, and chart container canvas."""
        header_frame = tk.Frame(self, bg=CLR_BG)
        header_frame.pack(fill="x", padx=10, pady=8)

        tk.Label(
            header_frame,
            text="PORTFOLIO ANALYTICS & VISUAL METRICS",
            font=FONT_BOLD,
            bg=CLR_BG,
            fg=CLR_HEAD,
        ).pack(side="left")

        # Category Filter
        tk.Label(header_frame, text="Category:", bg=CLR_BG, fg=CLR_TEXT, font=FONT_BOLD).pack(
            side="left", padx=(20, 5)
        )
        cb_cat = ttk.Combobox(
            header_frame,
            textvariable=self.var_filter_cat,
            values=["All"] + ASSET_CATEGORIES,
            state="readonly",
            font=FONT_MAIN,
            width=12,
        )
        cb_cat.pack(side="left", padx=5)
        cb_cat.bind("<<ComboboxSelected>>", self._on_category_changed)

        # Asset Filter
        tk.Label(header_frame, text="Asset:", bg=CLR_BG, fg=CLR_TEXT, font=FONT_BOLD).pack(
            side="left", padx=(15, 5)
        )
        self.cb_asset = ttk.Combobox(
            header_frame,
            textvariable=self.var_filter_asset,
            values=["All"],
            state="readonly",
            font=FONT_MAIN,
            width=24,
        )
        self.cb_asset.pack(side="left", padx=5)
        self.cb_asset.bind("<<ComboboxSelected>>", lambda _: self.draw_charts())

        # Reload Button
        tk.Button(
            header_frame,
            text="Refresh Charts",
            command=self.draw_charts,
            bg="#4f46e5",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        ).pack(side="right")

        self.chart_container = tk.Frame(self, bg=CLR_BG)
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=5)

    def _on_category_changed(self, event: Any = None) -> None:
        """Reset asset filter and refresh chart canvas when category selection changes."""
        self.var_filter_asset.set("All")
        self.draw_charts()

    def draw_charts(self) -> None:
        """Compute latest metrics and render 5 analytical subplots onto the scrollable canvas."""
        # Cleanup prior canvas widget
        if self.canvas_widget:
            self.canvas_widget.destroy()
            self.canvas_widget = None

        holdings, _ = calculate_portfolio(self.main_app.db, self.main_app.current_prices)

        # Update available asset filter values
        filter_cat = self.var_filter_cat.get()
        available_assets = sorted(
            list({
                name
                for name, h in holdings.items()
                if filter_cat == "All" or normalize_category(h.get("category", "Gold")) == filter_cat
            })
        )
        self.cb_asset["values"] = ["All"] + available_assets

        current_asset = self.var_filter_asset.get()
        if current_asset != "All" and current_asset not in available_assets:
            self.var_filter_asset.set("All")
            current_asset = "All"

        # Filter active holdings
        if filter_cat != "All":
            filtered_holdings = {
                k: v for k, v in holdings.items() if normalize_category(v.get("category", "Gold")) == filter_cat
            }
        else:
            filtered_holdings = dict(holdings)

        if current_asset != "All":
            filtered_holdings = {k: v for k, v in filtered_holdings.items() if k == current_asset}

        if not filtered_holdings:
            no_data = tk.Label(
                self.chart_container,
                text=f"No holdings found in category '{filter_cat}' to visualize.",
                font=FONT_BIG,
                bg=CLR_BG,
                fg=CLR_TEXT_MUTED,
            )
            no_data.pack(fill="both", expand=True)
            self.canvas_widget = no_data
            return

        # Build scrollable frame container
        wrapper = tk.Frame(self.chart_container, bg=CLR_BG)
        wrapper.pack(fill="both", expand=True)
        self.canvas_widget = wrapper

        scroll_canvas = tk.Canvas(wrapper, bg=CLR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=scroll_canvas.yview)
        scrollable_frame = tk.Frame(scroll_canvas, bg=CLR_BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")),
        )
        canvas_win = scroll_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scroll_canvas.bind(
            "<Configure>",
            lambda e: scroll_canvas.itemconfig(canvas_win, width=e.width),
        )
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scroll listeners
        def _on_wheel(e: Any) -> None:
            scroll_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        scroll_canvas.bind("<Enter>", lambda _: scroll_canvas.bind_all("<MouseWheel>", _on_wheel))
        scroll_canvas.bind("<Leave>", lambda _: scroll_canvas.unbind_all("<MouseWheel>"))

        # Create multi-panel Figure
        fig = Figure(figsize=(11, 11), dpi=95, facecolor=CLR_BG)
        self.current_figure = fig

        # -------------------------------------------------------------
        # 1. Donut Chart: Asset Value Allocation
        # -------------------------------------------------------------
        ax1 = fig.add_subplot(321)
        ax1.set_facecolor(CLR_BG)

        pie_data: Dict[str, float] = {}
        if filter_cat == "All":
            for h in filtered_holdings.values():
                cat = normalize_category(h["category"])
                pie_data[cat] = pie_data.get(cat, 0.0) + h["current_value"]
            title_pie = "Portfolio Allocation by Value"
        else:
            for asset_name, h in filtered_holdings.items():
                pie_data[asset_name] = pie_data.get(asset_name, 0.0) + h["current_value"]
            title_pie = f"{filter_cat} Allocation by Value"

        pie_data = {k: v for k, v in pie_data.items() if v > 0}
        if pie_data:
            labels = list(pie_data.keys())
            sizes = list(pie_data.values())
            palette = ["#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#6b7280"]
            _, _, autotexts = ax1.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                colors=palette[: len(labels)],
                textprops={"color": CLR_TEXT, "fontsize": 8},
                wedgeprops={"width": 0.4, "edgecolor": CLR_BG, "linewidth": 1.5},
            )
            for at in autotexts:
                at.set_fontsize(8)
                at.set_weight("bold")
                at.set_color("#ffffff")
            ax1.set_title(title_pie, color=CLR_HEAD, fontproperties={"weight": "bold", "size": 10})
        else:
            ax1.text(0.5, 0.5, "No valuation data available", color=CLR_TEXT_MUTED, ha="center", va="center")

        # -------------------------------------------------------------
        # 2. Bar Chart: Invested Capital vs Current Market Value
        # -------------------------------------------------------------
        ax2 = fig.add_subplot(322)
        ax2.set_facecolor(CLR_BG)

        cost_data: Dict[str, float] = {}
        val_data: Dict[str, float] = {}
        if filter_cat == "All":
            for h in filtered_holdings.values():
                cat = normalize_category(h["category"])
                cost_data[cat] = cost_data.get(cat, 0.0) + h["cost"]
                val_data[cat] = val_data.get(cat, 0.0) + h["current_value"]
            title_bar = "Cost vs Current Value (Million VND)"
        else:
            for asset_name, h in filtered_holdings.items():
                cost_data[asset_name] = cost_data.get(asset_name, 0.0) + h["cost"]
                val_data[asset_name] = val_data.get(asset_name, 0.0) + h["current_value"]
            title_bar = f"{filter_cat}: Cost vs Value (Million VND)"

        all_keys = sorted(list(set(cost_data.keys()) | set(val_data.keys())))
        if all_keys:
            costs_m = [cost_data.get(k, 0.0) / 1_000_000 for k in all_keys]
            vals_m = [val_data.get(k, 0.0) / 1_000_000 for k in all_keys]

            x_indices = np.arange(len(all_keys))
            w = 0.35
            ax2.bar(x_indices - w / 2, costs_m, w, label="Invested Capital", color="#64748b")
            ax2.bar(x_indices + w / 2, vals_m, w, label="Current Value", color=CLR_GOLD)

            ax2.set_title(title_bar, color=CLR_HEAD, fontproperties={"weight": "bold", "size": 10})
            ax2.set_xticks(x_indices)
            ax2.set_xticklabels(all_keys, color=CLR_TEXT, fontsize=8)
            ax2.tick_params(colors=CLR_TEXT_MUTED, labelsize=8)
            ax2.grid(True, linestyle=":", alpha=0.15, color="#94a3b8")
            ax2.legend(facecolor=CLR_PANEL, edgecolor=CLR_BORDER, labelcolor=CLR_TEXT, fontsize=8, framealpha=0.6)

            for spine in ("top", "right"):
                ax2.spines[spine].set_visible(False)
            ax2.spines["left"].set_color(CLR_BORDER)
            ax2.spines["bottom"].set_color(CLR_BORDER)
        else:
            ax2.text(0.5, 0.5, "No comparison data", color=CLR_TEXT_MUTED, ha="center", va="center")

        # -------------------------------------------------------------
        # 3. Line Chart: Cumulative Capital Outlay Over Time
        # -------------------------------------------------------------
        ax3 = fig.add_subplot(323)
        ax3.set_facecolor(CLR_BG)

        buy_txs = [r for r in self.main_app.db if normalize_action(r.get("action", "Buy")) == "Buy"]
        if filter_cat != "All":
            buy_txs = [r for r in buy_txs if normalize_category(r.get("category", "Gold")) == filter_cat]
        if current_asset != "All":
            buy_txs = [r for r in buy_txs if r.get("asset") == current_asset]

        buy_by_date: Dict[str, float] = {}
        for r in buy_txs:
            d_str = str(r.get("date", ""))
            if d_str:
                buy_by_date[d_str] = buy_by_date.get(d_str, 0.0) + float(r.get("total", 0.0))

        sorted_dates = sorted(buy_by_date.keys())
        if sorted_dates:
            outlays_m = [buy_by_date[d] / 1_000_000 for d in sorted_dates]
            short_labels: List[str] = []
            for d in sorted_dates:
                parts = d.split("-")
                short_labels.append(f"{parts[2]}/{parts[1]}" if len(parts) == 3 else d)

            ax3.plot(short_labels, outlays_m, marker="o", color="#10b981", linewidth=2, label="Purchased")
            ax3.set_title("Capital Inflow by Date (Million VND)", color=CLR_HEAD, fontproperties={"weight": "bold", "size": 10})
            ax3.tick_params(colors=CLR_TEXT, labelsize=8)
            ax3.grid(True, linestyle=":", alpha=0.15, color="#94a3b8")

            ax3.set_xticks(range(len(short_labels)))
            rot = 30 if len(short_labels) > 5 else 0
            ax3.set_xticklabels(short_labels, rotation=rot, ha="right" if rot else "center", color=CLR_TEXT, fontsize=7)

            for spine in ("top", "right"):
                ax3.spines[spine].set_visible(False)
            ax3.spines["left"].set_color(CLR_BORDER)
            ax3.spines["bottom"].set_color(CLR_BORDER)
        else:
            ax3.text(0.5, 0.5, "No buy transactions", color=CLR_TEXT_MUTED, ha="center", va="center")

        # -------------------------------------------------------------
        # 4. Grouped Bar: Average Cost Basis vs Benchmark Price
        # -------------------------------------------------------------
        ax4 = fig.add_subplot(324)
        ax4.set_facecolor(CLR_BG)

        price_comps = [
            {
                "asset": name,
                "unit": normalize_unit(h["unit"]),
                "avg_price": h["avg_price"],
                "market_price": h["market_price"],
            }
            for name, h in filtered_holdings.items()
            if h["market_price"] > 0
        ]
        price_comps.sort(key=lambda x: x["asset"])

        if price_comps:
            labels_p = [f"{truncate_label(item['asset'], 12)}\n({item['unit']})" for item in price_comps]
            avg_m = [item["avg_price"] / 1_000_000 for item in price_comps]
            mkt_m = [item["market_price"] / 1_000_000 for item in price_comps]

            x_idx = np.arange(len(price_comps))
            w = 0.35
            ax4.bar(x_idx - w / 2, avg_m, w, label="Avg Cost Basis", color="#64748b")
            ax4.bar(x_idx + w / 2, mkt_m, w, label="Market Benchmark", color=CLR_GOLD)

            ax4.set_title("Avg Cost Basis vs Market Price (Tr/Unit)", color=CLR_HEAD, fontproperties={"weight": "bold", "size": 10})
            ax4.set_xticks(x_idx)
            ax4.set_xticklabels(labels_p, color=CLR_TEXT, fontsize=8)
            ax4.tick_params(colors=CLR_TEXT_MUTED, labelsize=8)
            ax4.grid(True, linestyle=":", alpha=0.15, color="#94a3b8")
            ax4.legend(facecolor=CLR_PANEL, edgecolor=CLR_BORDER, labelcolor=CLR_TEXT, fontsize=8, framealpha=0.6)

            for spine in ("top", "right"):
                ax4.spines[spine].set_visible(False)
            ax4.spines["left"].set_color(CLR_BORDER)
            ax4.spines["bottom"].set_color(CLR_BORDER)
        else:
            ax4.text(0.5, 0.5, "No price comparison data", color=CLR_TEXT_MUTED, ha="center", va="center")

        # -------------------------------------------------------------
        # 5. Horizontal Bar: Net PnL by Individual Asset
        # -------------------------------------------------------------
        ax5 = fig.add_subplot(313)
        ax5.set_facecolor(CLR_BG)

        pnl_items = [
            (name, h["pnl"] / 1_000_000)
            for name, h in filtered_holdings.items()
            if h["market_price"] > 0
        ]
        pnl_items.sort(key=lambda x: x[1])

        if pnl_items:
            ax5.yaxis.set_visible(False)
            pnls = [item[1] for item in pnl_items]
            y_pos = np.arange(len(pnls))
            bar_colors = [CLR_GREEN if p >= 0 else CLR_RED for p in pnls]
            bars = ax5.barh(y_pos, pnls, color=bar_colors, edgecolor="none", height=0.4)
            ax5.axvline(0, color=CLR_TEXT_MUTED, linewidth=1, linestyle="-")

            title_pnl = "Net Unrealized PnL by Asset (Million VND)"
            if filter_cat != "All":
                title_pnl = f"{filter_cat}: Net Unrealized PnL (Million VND)"

            ax5.set_title(title_pnl, color=CLR_HEAD, fontproperties={"weight": "bold", "size": 10})
            ax5.tick_params(colors=CLR_TEXT, labelsize=8)
            ax5.grid(True, linestyle=":", alpha=0.15, color="#94a3b8")

            min_val, max_val = min(pnls), max(pnls)
            left_lim = min_val - abs(min_val) * 0.25 if min_val < 0 else -1.0
            right_lim = max_val + abs(max_val) * 0.25 if max_val > 0 else 1.0
            ax5.set_xlim(left_lim, right_lim)

            for spine in ("top", "right", "left"):
                ax5.spines[spine].set_visible(False)
            ax5.spines["bottom"].set_color(CLR_BORDER)

            for i, bar in enumerate(bars):
                val_width = bar.get_width()
                full_name = pnl_items[i][0]
                align = "left" if val_width >= 0 else "right"
                offset = (right_lim * 0.01) if val_width >= 0 else (left_lim * 0.01)

                ax5.text(
                    0 + offset,
                    bar.get_y() + bar.get_height() + 0.05,
                    full_name,
                    va="bottom",
                    ha=align,
                    color=CLR_TEXT,
                    fontsize=8,
                    fontweight="bold",
                )

                val_offset = (right_lim * 0.02) if val_width >= 0 else (left_lim * 0.02)
                formatted_num = f"{val_width:+.2f}M" if abs(val_width) < 1 else f"{val_width:+.1f}M"
                ax5.text(
                    val_width + val_offset,
                    bar.get_y() + bar.get_height() / 2,
                    formatted_num,
                    va="center",
                    ha=align,
                    color=CLR_TEXT,
                    fontsize=7.5,
                    fontweight="bold",
                )
        else:
            ax5.text(0.5, 0.5, "Requires benchmark prices to compute net PnL", color=CLR_TEXT_MUTED, ha="center", va="center")

        fig.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.06, hspace=0.45, wspace=0.22)

        canvas = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        scrollable_frame.update_idletasks()
