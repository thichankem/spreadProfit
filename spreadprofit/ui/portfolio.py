"""
Portfolio dashboard view displaying holdings, performance metrics, and simulators.

Presents asset-level cost basis, real-time valuation, unrealized PnL, return on
investment (ROI), quick category benchmark price editing, and What-If scenario modeling.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict

from spreadprofit.config import (
    ASSET_CATEGORIES,
    CLR_BG,
    CLR_BORDER,
    CLR_ENTRY,
    CLR_GOLD,
    CLR_GREEN,
    CLR_HEAD,
    CLR_PANEL,
    CLR_RED,
    CLR_TEXT,
    CLR_TEXT_MUTED,
    FONT_BOLD,
    FONT_MAIN,
    normalize_category,
    normalize_unit,
)
from spreadprofit.db import calculate_portfolio, save_market_prices


class PortfolioTab(tk.Frame):
    """Portfolio overview tab with KPI cards, holding details, and what-if simulation."""

    def __init__(self, parent: tk.Widget, main_app: Any) -> None:
        super().__init__(parent, bg=CLR_BG)
        self.main_app = main_app

        # State variables for What-If simulator
        self.var_wi_asset = tk.StringVar()
        self.var_wi_target_price = tk.StringVar()
        self.var_wi_result = tk.StringVar(value="Enter a target sell price to forecast projected PnL.")

        # State variables for manual benchmark price updates
        self.var_buy_price = tk.StringVar()
        self.var_sell_price = tk.StringVar()

        # State variable for category filtering
        self.var_filter_cat = tk.StringVar(value="All")

        self.active_holdings: Dict[str, Dict[str, Any]] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the dashboard cards, holdings treeview, and simulation controls."""
        # Category Filter Bar
        filter_bar = tk.Frame(self, bg=CLR_BG)
        filter_bar.pack(fill="x", padx=15, pady=(12, 0))

        tk.Label(
            filter_bar,
            text="Filter by Category:",
            bg=CLR_BG,
            fg=CLR_TEXT,
            font=FONT_BOLD,
        ).pack(side="left", padx=5)

        cb_filter = ttk.Combobox(
            filter_bar,
            textvariable=self.var_filter_cat,
            values=["All"] + ASSET_CATEGORIES,
            state="readonly",
            font=FONT_MAIN,
            width=15,
        )
        cb_filter.pack(side="left", padx=5)
        cb_filter.bind("<<ComboboxSelected>>", lambda _: self.refresh_view())

        # Top Section: KPI Metric Cards
        cards_frame = tk.Frame(self, bg=CLR_BG)
        cards_frame.pack(fill="x", padx=10, pady=8)

        for col in range(4):
            cards_frame.columnconfigure(col, weight=1)

        def create_kpi_card(parent_frame: tk.Frame, title: str, column_idx: int) -> tk.Label:
            card = tk.Frame(
                parent_frame,
                bg=CLR_PANEL,
                bd=0,
                relief="solid",
                highlightbackground=CLR_BORDER,
                highlightthickness=1,
                padx=12,
                pady=10,
            )
            card.grid(row=0, column=column_idx, sticky="ew", padx=6)

            lbl_title = tk.Label(
                card,
                text=title,
                font=("Segoe UI", 9, "bold"),
                bg=CLR_PANEL,
                fg=CLR_TEXT_MUTED,
            )
            lbl_title.pack(anchor="w")

            lbl_val = tk.Label(
                card,
                text="-",
                font=("Segoe UI", 16, "bold"),
                bg=CLR_PANEL,
                fg=CLR_TEXT,
            )
            lbl_val.pack(anchor="w", pady=(3, 0))
            return lbl_val

        self.card_cost = create_kpi_card(cards_frame, "TOTAL INVESTED CAPITAL", 0)
        self.card_value = create_kpi_card(cards_frame, "CURRENT PORTFOLIO VALUE", 1)
        self.card_pnl = create_kpi_card(cards_frame, "UNREALIZED PnL", 2)
        self.card_pnl_pct = create_kpi_card(cards_frame, "RETURN ON INVESTMENT (ROI)", 3)

        # Middle Section: Holdings Detail Table
        table_label = tk.Label(
            self,
            text="PORTFOLIO HOLDINGS (Select a row to inspect or update benchmark prices)",
            font=FONT_BOLD,
            bg=CLR_BG,
            fg=CLR_HEAD,
            anchor="w",
        )
        table_label.pack(fill="x", padx=10, pady=(10, 5))

        table_frame = tk.Frame(
            self,
            bg=CLR_PANEL,
            bd=1,
            relief="flat",
            highlightbackground=CLR_BORDER,
            highlightthickness=1,
        )
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = (
            "Asset",
            "Category",
            "Qty",
            "Unit",
            "AvgCost",
            "MarketPrice",
            "TotalCost",
            "CurrentValue",
            "PnL",
            "PnLPct",
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10, selectmode="browse")

        self.tree.heading("Asset", text="Asset Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Qty", text="Quantity")
        self.tree.heading("Unit", text="Unit")
        self.tree.heading("AvgCost", text="Avg Cost Basis")
        self.tree.heading("MarketPrice", text="Market Benchmark")
        self.tree.heading("TotalCost", text="Total Invested")
        self.tree.heading("CurrentValue", text="Current Value")
        self.tree.heading("PnL", text="Unrealized PnL")
        self.tree.heading("PnLPct", text="ROI %")

        self.tree.column("Asset", width=180, anchor="w")
        self.tree.column("Category", width=80, anchor="center")
        self.tree.column("Qty", width=80, anchor="center")
        self.tree.column("Unit", width=55, anchor="center")
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

        self.tree.tag_configure("green", foreground="#34d399")
        self.tree.tag_configure("red", foreground="#f87171")
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Bottom Section: Benchmark Price Updater & What-If Simulator
        bottom_frame = tk.Frame(self, bg=CLR_BG)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        bottom_frame.columnconfigure(0, weight=1, uniform="bottom_panels")
        bottom_frame.columnconfigure(1, weight=1, uniform="bottom_panels")

        # Left Panel: Market Price Benchmark Updater
        price_frame = tk.LabelFrame(
            bottom_frame,
            text=" BENCHMARK MARKET PRICES ",
            font=FONT_BOLD,
            bg=CLR_PANEL,
            fg=CLR_GOLD,
            bd=1,
            relief="solid",
            padx=10,
            pady=8,
        )
        price_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        price_grid = tk.Frame(price_frame, bg=CLR_PANEL)
        price_grid.pack(fill="x")

        tk.Label(price_grid, text="Category:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(
            row=0, column=0, sticky="e", padx=5, pady=5
        )
        self.var_price_asset_sel = tk.StringVar(value=ASSET_CATEGORIES[0])
        self.cb_price_asset = ttk.Combobox(
            price_grid,
            textvariable=self.var_price_asset_sel,
            values=ASSET_CATEGORIES,
            state="readonly",
            font=FONT_MAIN,
            width=12,
        )
        self.cb_price_asset.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.cb_price_asset.bind("<<ComboboxSelected>>", self._on_price_asset_combobox_change)

        tk.Label(price_grid, text="Price Unit:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(
            row=0, column=2, sticky="e", padx=10, pady=5
        )
        self.var_price_unit = tk.StringVar(value="Ounce")
        self.cb_price_unit = ttk.Combobox(
            price_grid,
            textvariable=self.var_price_unit,
            values=["Ounce", "Gram", "Kilogram", "Tael", "Chi"],
            state="readonly",
            font=FONT_MAIN,
            width=10,
        )
        self.cb_price_unit.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        tk.Label(price_grid, text="Buy Price (VND):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )
        self.ent_buy = tk.Entry(
            price_grid,
            textvariable=self.var_buy_price,
            bg=CLR_ENTRY,
            fg=CLR_TEXT,
            font=FONT_MAIN,
            relief="flat",
            insertbackground=CLR_TEXT,
            width=15,
            bd=3,
        )
        self.ent_buy.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Label(price_grid, text="Sell Price (VND):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(
            row=1, column=2, sticky="e", padx=10, pady=5
        )
        self.ent_sell = tk.Entry(
            price_grid,
            textvariable=self.var_sell_price,
            bg=CLR_ENTRY,
            fg=CLR_TEXT,
            font=FONT_MAIN,
            relief="flat",
            insertbackground=CLR_TEXT,
            width=15,
            bd=3,
        )
        self.ent_sell.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        btn_save_price = tk.Button(
            price_grid,
            text="Save Prices",
            command=self._save_price,
            bg=CLR_GOLD,
            fg="white",
            font=FONT_BOLD,
            relief="flat",
            padx=15,
            pady=4,
            cursor="hand2",
        )
        btn_save_price.grid(row=2, column=0, columnspan=4, pady=(10, 0))

        # Right Panel: What-If Profit Simulation
        wi_frame = tk.LabelFrame(
            bottom_frame,
            text=" WHAT-IF PROFIT SIMULATOR ",
            font=FONT_BOLD,
            bg=CLR_PANEL,
            fg=CLR_GOLD,
            bd=1,
            relief="solid",
            padx=10,
            pady=8,
        )
        wi_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        wi_grid = tk.Frame(wi_frame, bg=CLR_PANEL)
        wi_grid.pack(fill="x")

        tk.Label(wi_grid, text="Target Asset:", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(
            row=0, column=0, sticky="e", padx=5, pady=5
        )
        self.cb_wi_asset = ttk.Combobox(
            wi_grid,
            textvariable=self.var_wi_asset,
            state="readonly",
            font=FONT_MAIN,
            width=22,
        )
        self.cb_wi_asset.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(wi_grid, text="If sold at (VND):", bg=CLR_PANEL, fg=CLR_TEXT, font=FONT_BOLD).grid(
            row=0, column=2, sticky="e", padx=10, pady=5
        )
        self.ent_target = tk.Entry(
            wi_grid,
            textvariable=self.var_wi_target_price,
            bg=CLR_ENTRY,
            fg=CLR_TEXT,
            font=FONT_MAIN,
            relief="flat",
            insertbackground=CLR_TEXT,
            width=15,
            bd=3,
        )
        self.ent_target.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        btn_calc = tk.Button(
            wi_grid,
            text="Calculate",
            command=self._calculate_whatif,
            bg=CLR_GREEN,
            fg="white",
            font=FONT_BOLD,
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_calc.grid(row=0, column=4, padx=10)

        self.lbl_result = tk.Label(
            wi_frame,
            textvariable=self.var_wi_result,
            font=FONT_BOLD,
            bg=CLR_PANEL,
            fg=CLR_TEXT,
            justify="left",
            anchor="w",
            wraplength=500,
        )
        self.lbl_result.pack(fill="x", padx=10, pady=(8, 4))

        # Thousands separator formatting on focus in/out
        for var, entry in (
            (self.var_buy_price, self.ent_buy),
            (self.var_sell_price, self.ent_sell),
            (self.var_wi_target_price, self.ent_target),
        ):
            entry.bind("<FocusOut>", lambda e, v=var: self._format_number_entry(v))
            entry.bind("<FocusIn>", lambda e, v=var, w=entry: self._strip_number_entry(v, w))
            entry.bind("<Return>", lambda e, v=var: self._format_number_entry(v))

    def refresh_view(self) -> None:
        """Recalculate portfolio metrics and render updated table rows and summary cards."""
        self.active_holdings, summary = calculate_portfolio(self.main_app.db, self.main_app.current_prices)

        filter_cat = self.var_filter_cat.get()
        filtered_cost = 0.0
        filtered_value = 0.0
        filtered_pnl = 0.0

        for row in self.tree.get_children():
            self.tree.delete(row)

        for asset, h in sorted(self.active_holdings.items(), key=lambda x: (x[1]["category"], x[0])):
            cat = normalize_category(h.get("category", "Gold"))
            if filter_cat != "All" and cat != filter_cat:
                continue

            filtered_cost += h["cost"]
            filtered_value += h["current_value"] if h["market_price"] > 0 else h["cost"]
            filtered_pnl += h["pnl"]

            tag = "green" if h["pnl"] >= 0 else "red"
            sign_prefix = "+" if h["pnl"] >= 0 else "-"
            pnl_str = f"{sign_prefix}{abs(h['pnl']):,.0f} VND" if h["market_price"] > 0 else "-"

            pct_sign = "+" if h["pnl_pct"] >= 0 else ""
            pnl_pct_str = f"{pct_sign}{h['pnl_pct']:.2f}%" if h["market_price"] > 0 else "-"
            market_price_str = f"{h['market_price']:,.0f}" if h["market_price"] > 0 else "-"
            current_value_str = f"{h['current_value']:,.0f}" if h["market_price"] > 0 else "-"

            self.tree.insert(
                "",
                "end",
                tags=(tag,),
                values=(
                    h["asset"],
                    cat,
                    f"{h['qty']:g}",
                    normalize_unit(h["unit"]),
                    f"{h['avg_price']:,.0f}",
                    market_price_str,
                    f"{h['cost']:,.0f}",
                    current_value_str,
                    pnl_str,
                    pnl_pct_str,
                ),
            )

        filtered_roi = (filtered_pnl / filtered_cost * 100) if filtered_cost > 0 else 0.0

        # Update KPI Cards
        self.card_cost.configure(text=f"{filtered_cost:,.0f} VND")
        self.card_value.configure(text=f"{filtered_value:,.0f} VND")

        sign = "+" if filtered_pnl >= 0 else ""
        self.card_pnl.configure(text=f"{sign}{filtered_pnl:,.0f} VND")
        self.card_pnl.configure(fg=CLR_GREEN if filtered_pnl >= 0 else CLR_RED)

        sign_pct = "+" if filtered_roi >= 0 else ""
        self.card_pnl_pct.configure(text=f"{sign_pct}{filtered_roi:.2f}%")
        self.card_pnl_pct.configure(fg=CLR_GREEN if filtered_roi >= 0 else CLR_RED)

        # Update What-If dropdown
        active_assets = [
            asset
            for asset, h in self.active_holdings.items()
            if (filter_cat == "All" or normalize_category(h.get("category", "Gold")) == filter_cat)
        ]
        self.cb_wi_asset.configure(values=active_assets)
        if active_assets:
            if self.var_wi_asset.get() not in active_assets:
                self.cb_wi_asset.current(0)
        else:
            self.var_wi_asset.set("")
            self.var_wi_result.set("No assets available in this category for simulation.")

        # Default price benchmark category
        if not self.var_price_asset_sel.get():
            self.cb_price_asset.current(0)
            self._on_price_asset_combobox_change()

    def _on_price_asset_combobox_change(self, event: Any = None) -> None:
        """Load benchmark price information for the selected category."""
        cat = normalize_category(self.var_price_asset_sel.get())
        if not cat:
            return

        price_info = self.main_app.current_prices.get(cat)
        if not price_info:
            legacy_key = "Vàng" if cat == "Gold" else "Bạc"
            price_info = self.main_app.current_prices.get(legacy_key, {"buy": 0.0, "sell": 0.0, "unit": "Tael"})

        buy_val = price_info.get("buy", 0.0)
        sell_val = price_info.get("sell", 0.0)
        unit = normalize_unit(price_info.get("unit", "Tael"))

        self.var_buy_price.set(f"{buy_val:,.0f}" if buy_val > 0 else "")
        self.var_sell_price.set(f"{sell_val:,.0f}" if sell_val > 0 else "")
        self.var_price_unit.set(unit)

    def _on_row_select(self, event: Any) -> None:
        """Synchronize selected row's asset category with the price editing panel."""
        selection = self.tree.selection()
        if not selection:
            return
        row_vals = self.tree.item(selection[0])["values"]
        category = normalize_category(row_vals[1])

        if category in ASSET_CATEGORIES:
            self.var_price_asset_sel.set(category)
            self._on_price_asset_combobox_change()

    def _save_price(self) -> None:
        """Persist updated benchmark market prices."""
        cat = normalize_category(self.var_price_asset_sel.get())
        if not cat:
            messagebox.showwarning("Notice", "Please select an asset category to edit.")
            return

        try:
            buy_val = float(self.var_buy_price.get().replace(",", "")) if self.var_buy_price.get() else 0.0
            sell_val = float(self.var_sell_price.get().replace(",", "")) if self.var_sell_price.get() else 0.0
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter valid numeric price values.")
            return

        self.main_app.current_prices[cat] = {
            "buy": buy_val,
            "sell": sell_val,
            "unit": normalize_unit(self.var_price_unit.get()),
        }

        save_market_prices(self.main_app.current_prices)
        self.main_app.var_status.set(
            f"Saved price for [{cat}]: {buy_val:,.0f} VND / {sell_val:,.0f} VND per {self.var_price_unit.get()}."
        )
        self.refresh_view()

    def _calculate_whatif(self) -> None:
        """Simulate asset liquidation proceeds and forecast projected return on investment."""
        asset = self.var_wi_asset.get()
        if not asset or asset not in self.active_holdings:
            messagebox.showwarning("Notice", "Please choose an asset from your active holdings.")
            return

        try:
            target_price = float(self.var_wi_target_price.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("Validation Error", "Please provide a valid simulation price.")
            return

        h = self.active_holdings[asset]
        qty = h["qty"]
        cost = h["cost"]
        unit = normalize_unit(h["unit"])

        total_proceeds = qty * target_price
        pnl = total_proceeds - cost
        roi = (pnl / cost * 100) if cost > 0 else 0.0

        sign = "+" if pnl >= 0 else ""
        sign_pct = "+" if roi >= 0 else ""
        color = CLR_GREEN if pnl >= 0 else CLR_RED
        status_label = "PROFIT" if pnl >= 0 else "LOSS"

        self.lbl_result.configure(fg=color)
        self.var_wi_result.set(
            f"Scenario Simulation for [{asset}]:\n"
            f"   Holding: {qty:g} {unit}  |  Avg Cost Basis: {h['avg_price']:,.0f} VND\n"
            f"   Hypothetical Exit Price: {target_price:,.0f} VND / {unit}\n"
            f"   Estimated Gross Proceeds: {total_proceeds:,.0f} VND\n"
            f"   Forecast Net PnL: {sign}{pnl:,.0f} VND ({status_label})  |  Projected ROI: {sign_pct}{roi:.2f}%"
        )

    def _format_number_entry(self, var: tk.StringVar) -> None:
        """Format raw numeric string with comma thousands separators."""
        try:
            val = var.get()
            clean = "".join([c for c in val.replace(",", "") if c.isdigit()])
            if clean:
                var.set(f"{int(clean):,}")
        except Exception:
            pass

    def _strip_number_entry(self, var: tk.StringVar, entry: tk.Entry) -> None:
        """Strip separators during active typing to avoid cursor jitter."""
        try:
            raw = var.get().replace(",", "")
            var.set(raw)
            entry.icursor(tk.END)
        except Exception:
            pass
