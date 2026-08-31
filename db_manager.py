# db_manager.py
"""
Quản lý cơ sở dữ liệu giao dịch dưới dạng JSON và tính toán các chỉ số danh mục đầu tư.
"""

import json
import os
import shutil
import sys

APP_NAME = "spreadProfit"

# BASE_DIR   : thư mục chứa file exe (khi đã đóng gói) hoặc thư mục mã nguồn.
# BUNDLE_DIR : thư mục tạm _MEIPASS chứa dữ liệu mẫu được nhúng sẵn trong exe.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

DATA_FILE_NAMES = ("gold_transactions.json", "market_prices.json", "custom_assets.json")


def _is_writable(path):
    """Kiểm tra thư mục có ghi được không (ví dụ Program Files thì không)."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("")
        os.remove(probe)
        return True
    except Exception:
        return False


def _resolve_data_dir():
    """
    Chọn nơi lưu dữ liệu theo thứ tự ưu tiên:
      1. Thư mục 'data' nằm cạnh file exe  -> chạy kiểu portable, copy sang máy khác là xong.
      2. %APPDATA%/spreadProfit           -> dự phòng khi thư mục exe không ghi được.
    """
    portable = os.path.join(BASE_DIR, "data")
    if _is_writable(portable):
        return portable
    fallback = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME)
    os.makedirs(fallback, exist_ok=True)
    return fallback


DATA_DIR = _resolve_data_dir()


def _seed_data_files():
    """
    Lần chạy đầu tiên trên máy mới: khôi phục dữ liệu từ bản nhúng trong exe,
    hoặc từ file JSON cũ nằm cạnh exe/mã nguồn (tương thích ngược phiên bản trước).
    """
    for name in DATA_FILE_NAMES:
        target = os.path.join(DATA_DIR, name)
        if os.path.exists(target):
            continue
        for source in (os.path.join(BASE_DIR, name), os.path.join(BUNDLE_DIR, "_seed", name)):
            if os.path.abspath(source) == os.path.abspath(target):
                continue
            if os.path.exists(source):
                try:
                    shutil.copyfile(source, target)
                except Exception:
                    pass
                break


_seed_data_files()

DB_FILE = os.path.join(DATA_DIR, "gold_transactions.json")
PRICES_FILE = os.path.join(DATA_DIR, "market_prices.json")
CUSTOM_ASSETS_FILE = os.path.join(DATA_DIR, "custom_assets.json")


def load_db():
    """Tải dữ liệu từ file JSON. Nếu file chưa tồn tại, khởi tạo dữ liệu mẫu."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Nếu file lỗi, trả về list rỗng
            return []
    
    # Hóa đơn mẫu số 00271176 (Bảo Tín Mạnh Hải, 26/03/2026)
    seed = [
        {
            "id": 1,
            "date": "2026-03-26",
            "category": "Vàng",
            "asset": "Vàng nhẫn 24K Bảo Tín Mạnh Hải",
            "action": "Mua",
            "quantity": 2.0,
            "unit": "Chỉ",
            "unit_price": 18500000.0,
            "total": 37000000.0,
            "note": "HĐ 00271176 – 2 nhẫn Kim Gia Bảo (KGB1C10022001)",
        }
    ]
    save_db(seed)
    return seed


def save_db(data):
    """Ghi dữ liệu vào file JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_id(data):
    """Tìm ID tiếp theo cho bản ghi mới."""
    return max((r["id"] for r in data), default=0) + 1


def calculate_portfolio(transactions, current_prices):
    """
    Tính toán trạng thái danh mục đầu tư hiện tại từ các giao dịch.
    Áp dụng phương pháp giá vốn bình quân gia quyền di động.
    
    current_prices: dict chứa giá thị trường {category: {"buy": price, "sell": price}}
    Trả về:
        holdings: dict {asset_name -> dữ liệu tài sản}
        summary: dict chứa tổng số liệu (total_cost, total_value, total_pnl, pnl_pct)
    """
    holdings = {}
    
    # Sắp xếp giao dịch theo ngày tăng dần để tính toán chính xác giá vốn bình quân di động
    sorted_txs = sorted(transactions, key=lambda x: x.get("date", ""))
    
    for r in sorted_txs:
        asset = r["asset"]
        category = r.get("category", "Vàng")
        unit = r["unit"]
        
        if asset not in holdings:
            holdings[asset] = {
                "asset": asset,
                "category": category,
                "qty": 0.0,
                "cost": 0.0,
                "unit": unit
            }
            
        qty = r["quantity"]
        total = r["total"]
        
        if r["action"] == "Mua":
            holdings[asset]["qty"] += qty
            holdings[asset]["cost"] += total
        else:  # Bán
            if holdings[asset]["qty"] > 0:
                avg_cost = holdings[asset]["cost"] / holdings[asset]["qty"]
                holdings[asset]["qty"] -= qty
                holdings[asset]["cost"] -= qty * avg_cost
                
                if holdings[asset]["qty"] < 1e-9:
                    holdings[asset]["qty"] = 0.0
                    holdings[asset]["cost"] = 0.0

    # Định nghĩa các yếu tố quy đổi đơn vị
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

    # Tính toán giá trị hiện tại và lời lỗ theo giá của Nhóm tài sản
    total_cost = 0.0
    total_value = 0.0
    total_pnl = 0.0
    
    active_holdings = {}
    for asset, h in holdings.items():
        if h["qty"] <= 0:
            continue
            
        avg_price = h["cost"] / h["qty"]
        cat = h["category"]
        
        # Tìm giá mua vào trên thị trường của Nhóm tài sản này
        price_info = current_prices.get(cat, {"buy": 0.0, "sell": 0.0, "unit": "Lượng"})
        market_buy_price = price_info.get("buy", 0.0)
        price_unit = price_info.get("unit", "Lượng")
        
        # Quy đổi giá thị trường của nhóm sang đơn vị của tài sản
        if market_buy_price > 0:
            ratio = get_factor(price_unit) / get_factor(h["unit"])
            asset_market_price = market_buy_price / ratio
        else:
            asset_market_price = 0.0
            
        current_val = h["qty"] * asset_market_price
        pnl = current_val - h["cost"] if asset_market_price > 0 else 0.0
        pnl_pct = (pnl / h["cost"] * 100) if (h["cost"] > 0 and asset_market_price > 0) else 0.0
        
        h["avg_price"] = avg_price
        h["market_price"] = asset_market_price
        h["current_value"] = current_val
        h["pnl"] = pnl
        h["pnl_pct"] = pnl_pct
        
        total_cost += h["cost"]
        if asset_market_price > 0:
            total_value += current_val
            total_pnl += pnl
        else:
            total_value += h["cost"]
            
        active_holdings[asset] = h
        
    pnl_pct_total = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
    
    summary = {
        "total_cost": total_cost,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "pnl_pct": pnl_pct_total
    }
    
    return active_holdings, summary


def load_market_prices():
    """Tải giá thị trường thủ công theo Nhóm (Vàng/Bạc) từ file JSON."""
    if os.path.exists(PRICES_FILE):
        try:
            with open(PRICES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "Vàng" in data and "Bạc" in data:
                    return data
        except Exception:
            pass
            
    # Tạo giá trị mặc định cho Vàng và Bạc
    prices = {
        "Vàng": {"buy": 80000000.0, "sell": 81000000.0, "unit": "Lượng"},
        "Bạc": {"buy": 1000000.0, "sell": 1050000.0, "unit": "Lượng"}
    }
    save_market_prices(prices)
    return prices

def save_market_prices(prices):
    """Lưu giá thị trường vào file JSON."""
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)


def load_custom_assets():
    """Tải danh sách tài sản tùy chọn của người dùng."""
    if os.path.exists(CUSTOM_ASSETS_FILE):
        try:
            with open(CUSTOM_ASSETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_custom_assets(assets):
    """Lưu danh sách tài sản tùy chọn."""
    with open(CUSTOM_ASSETS_FILE, "w", encoding="utf-8") as f:
        json.dump(assets, f, ensure_ascii=False, indent=2)
