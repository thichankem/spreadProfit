"""
Main window interface for the spreadProfit desktop application.

Coordinates top-level navigation, ttk Clam dark theme styling, cross-tab data
synchronization, high-DPI scaling, and cloud backup actions.
"""

from __future__ import annotations

import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

import cloud_backup
from config import (
    CLR_BG,
    CLR_BORDER,
    CLR_ENTRY,
    CLR_GOLD,
    CLR_HEAD,
    CLR_PANEL,
    CLR_TEXT,
    CLR_TEXT_MUTED,
    FONT_BOLD,
)
from db_manager import load_db, load_market_prices
from ui_charts import ChartsTab
from ui_portfolio import PortfolioTab
from ui_transactions import TransactionsTab


def resource_path(relative_path: str) -> str:
    """Resolve absolute path to an embedded resource (for PyInstaller and script runs)."""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class SpreadProfitApp(tk.Tk):
    """Primary application frame orchestrating tabs, styles, and data persistence."""

    def __init__(self) -> None:
        super().__init__()

        self.title("SpreadProfit — Precious Metals & Multi-Asset Portfolio Tracker")
        self.geometry("1280x820")
        self.minsize(1050, 700)
        self.configure(bg=CLR_BG)
        self.resizable(True, True)

        # Set multi-platform window icon
        self._set_app_icon()

        # Initialize local database and benchmark prices
        self.db = load_db()
        self.current_prices = load_market_prices()

        # Global status variable
        self.var_status = tk.StringVar(value="System ready (Offline-first mode).")

        # Configure global selection colors for text entries
        self.option_add("*Entry.selectBackground", "#4f46e5")
        self.option_add("*Entry.selectForeground", "white")

        # Build interface components
        self._build_ui()
        self._apply_styles()

        # Initial data refresh across active views
        try:
            self.tab_transactions.refresh_table()
            self.tab_portfolio.refresh_view()
        except Exception:
            pass

    def _set_app_icon(self) -> None:
        """Attempt to load Windows .ico or PNG fallback icon."""
        try:
            icon_ico = resource_path("app_icon.ico")
            icon_png = resource_path("app_icon.png")
            if os.path.exists(icon_ico):
                self.iconbitmap(icon_ico)
            elif os.path.exists(icon_png):
                img = tk.PhotoImage(file=icon_png)
                self.iconphoto(False, img)
        except Exception as err:
            print(f"Warning: Unable to load window icon: {err}")

    def _build_ui(self) -> None:
        """Construct the top header, tab notebook, and bottom status bar."""
        # Top banner with title and action buttons
        top_bar = tk.Frame(
            self,
            bg=CLR_PANEL,
            pady=10,
            padx=16,
            bd=0,
            highlightbackground=CLR_BORDER,
            highlightthickness=1,
        )
        top_bar.pack(fill="x")

        # Left title group
        title_box = tk.Frame(top_bar, bg=CLR_PANEL)
        title_box.pack(side="left")

        title_lbl = tk.Label(
            title_box,
            text="💰 SPREADPROFIT",
            font=("Segoe UI", 16, "bold"),
            bg=CLR_PANEL,
            fg=CLR_GOLD,
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            title_box,
            text="Precious Metals & Multi-Asset Portfolio Tracker • Moving Average Cost Basis",
            font=("Segoe UI", 9, "italic"),
            bg=CLR_PANEL,
            fg=CLR_TEXT_MUTED,
        )
        subtitle_lbl.pack(anchor="w")

        # Right quick action group
        actions_box = tk.Frame(top_bar, bg=CLR_PANEL)
        actions_box.pack(side="right")

        btn_backup = tk.Button(
            actions_box,
            text="☁️  Cloud Backup",
            command=self.trigger_cloud_backup,
            bg="#0284c7",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
        )
        btn_backup.pack(side="left", padx=4)

        btn_refresh = tk.Button(
            actions_box,
            text="🔄  Reload",
            command=self.refresh_prices,
            bg="#334155",
            fg=CLR_TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        )
        btn_refresh.pack(side="left", padx=4)

        # Tab Notebook container
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Instantiate modular views
        self.tab_portfolio = PortfolioTab(self.notebook, self)
        self.tab_transactions = TransactionsTab(self.notebook, self)
        self.tab_charts = ChartsTab(self.notebook, self)

        # Register tabs
        self.notebook.add(self.tab_portfolio, text=" 💼  Portfolio & PnL ")
        self.notebook.add(self.tab_transactions, text=" 📝  Transaction History ")
        self.notebook.add(self.tab_charts, text=" 📈  Visual Analytics ")

        # Event binding for tab switches
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Bottom status bar
        status_bar = tk.Frame(
            self,
            bg=CLR_PANEL,
            bd=1,
            relief="flat",
            highlightbackground=CLR_BORDER,
            highlightthickness=1,
        )
        status_bar.pack(fill="x", side="bottom")

        lbl_status = tk.Label(
            status_bar,
            textvariable=self.var_status,
            font=("Segoe UI", 9),
            bg=CLR_PANEL,
            fg=CLR_TEXT_MUTED,
            anchor="w",
        )
        lbl_status.pack(side="left", padx=12, pady=4, fill="x", expand=True)

    def _apply_styles(self) -> None:
        """Apply unified Dark Clam theme styling to standard ttk widgets."""
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview (tabular lists)
        style.configure(
            "Treeview",
            background=CLR_PANEL,
            foreground=CLR_TEXT,
            fieldbackground=CLR_PANEL,
            rowheight=30,
            font=("Segoe UI", 10),
            bordercolor=CLR_BORDER,
            borderwidth=1,
        )
        style.configure(
            "Treeview.Heading",
            background=CLR_ENTRY,
            foreground=CLR_HEAD,
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#4f46e5"), ("!selected", CLR_PANEL)],
            foreground=[("selected", "white")],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", "#475569")],
            foreground=[("active", "white")],
        )

        # Tab Notebook
        style.configure("TNotebook", background=CLR_BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=CLR_PANEL,
            foreground=CLR_TEXT_MUTED,
            font=FONT_BOLD,
            padding=[16, 8],
            borderwidth=0,
            focuscolor="",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", CLR_BG)],
            foreground=[("selected", CLR_GOLD)],
        )

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground=CLR_ENTRY,
            background=CLR_ENTRY,
            foreground=CLR_TEXT,
            bordercolor=CLR_BORDER,
            lightcolor=CLR_BORDER,
            darkcolor=CLR_BORDER,
            arrowcolor=CLR_TEXT,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", CLR_ENTRY)],
            foreground=[("readonly", CLR_TEXT)],
        )

        # Scrollbars
        for sb_style in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            style.configure(
                sb_style,
                gripcount=0,
                background=CLR_ENTRY,
                darkcolor=CLR_PANEL,
                lightcolor=CLR_PANEL,
                troughcolor=CLR_BG,
                bordercolor=CLR_BORDER,
                arrowcolor=CLR_TEXT_MUTED,
            )

    def _on_tab_changed(self, event: Any) -> None:
        """Automatically refresh view content when navigating between tabs."""
        current_idx = self.notebook.index(self.notebook.select())
        if current_idx == 0:
            self.tab_portfolio.refresh_view()
        elif current_idx == 1:
            self.tab_transactions.refresh_table()
        elif current_idx == 2:
            self.tab_charts.draw_charts()

    def refresh_prices(self) -> None:
        """Reload market benchmark prices from local JSON cache."""
        self.var_status.set("Reloading benchmark prices from storage...")
        self.current_prices = load_market_prices()
        self.var_status.set("Prices updated from local repository.")
        self._refresh_current_active_tab()

    def _refresh_current_active_tab(self) -> None:
        """Refresh only the currently visible tab."""
        current_idx = self.notebook.index(self.notebook.select())
        if current_idx == 0:
            self.tab_portfolio.refresh_view()
        elif current_idx == 1:
            self.tab_transactions.refresh_table()
        elif current_idx == 2:
            self.tab_charts.draw_charts()

    def refresh_portfolio_view(self) -> None:
        """Trigger an instant recalculation of portfolio metrics after transaction changes."""
        self.tab_portfolio.refresh_view()
        if self.notebook.index(self.notebook.select()) == 2:
            self.tab_charts.draw_charts()

    def trigger_cloud_backup(self) -> None:
        """Create a complete local snapshot and attempt Google Cloud Storage synchronization."""
        self.var_status.set("Creating local snapshot and syncing with Cloud...")
        meta = cloud_backup.create_local_snapshot()
        gcs_ok, gcs_msg = cloud_backup.upload_to_google_cloud()

        if gcs_ok:
            self.var_status.set("Backup uploaded to Google Cloud Storage successfully.")
            messagebox.showinfo(
                "Cloud Backup Complete",
                f"Snapshot created successfully:\n{meta['snapshot_path']}\n\n"
                f"Google Cloud Storage Status:\n{gcs_msg}",
            )
        else:
            self.var_status.set("Local snapshot created. Cloud sync pending configuration.")
            messagebox.showinfo(
                "Local Snapshot Created",
                f"Portfolio backed up locally:\n{meta['snapshot_path']}\n\n"
                f"Archive Package:\n{meta['archive_path']}\n\n"
                f"Google Cloud Storage Status:\n{gcs_msg}\n\n"
                "To enable automatic GCS upload, set the GCS_BACKUP_BUCKET environment "
                "variable or configure your bucket in cloud_config.json.",
            )


# Backward compatibility alias
GoldTrackerApp = SpreadProfitApp

if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    app = SpreadProfitApp()
    app.mainloop()
