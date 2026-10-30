"""
spreadProfit - Personal Precious Metals & Multi-Asset Portfolio Tracker.

Application entry point. Configures high-DPI awareness on Windows to prevent
display blurriness, initializes the primary application window, and starts
the Tkinter event loop.
"""

import ctypes
from ui_main import SpreadProfitApp


def main() -> None:
    """Initialize system DPI awareness and run the primary UI event loop."""
    # Enable per-monitor High-DPI scaling on Windows platforms
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    app = SpreadProfitApp()
    app.mainloop()


if __name__ == "__main__":
    main()
