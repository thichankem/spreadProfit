import sys
import traceback
from ui_main import GoldTrackerApp

app = None
try:
    app = GoldTrackerApp()
    app.tab_transactions.refresh_table()
    app.tab_portfolio.refresh_view()
    print("REFRESH_OK")
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
finally:
    if app:
        try:
            app.destroy()
        except Exception:
            pass
