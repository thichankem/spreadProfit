import traceback
import sys
from db_manager import load_db, load_market_prices, load_custom_assets

print('Testing basic data loading...')
try:
    db = load_db()
    prices = load_market_prices()
    custom_assets = load_custom_assets()
    print('db records:', len(db))
    print('market prices loaded:', list(prices.keys()))
    print('custom assets loaded:', len(custom_assets))
except Exception:
    traceback.print_exc()
    sys.exit(1)

print('Testing UI initialization...')
from ui_main import GoldTrackerApp

app = None
try:
    app = GoldTrackerApp()
    app.tab_transactions.refresh_table()
    app.tab_portfolio.refresh_view()
    app.tab_charts.draw_charts()
    print('UI refresh OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)
finally:
    if app:
        try:
            app.destroy()
        except Exception:
            pass

print('All tests passed.')
