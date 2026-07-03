# db_manager.py
"""
Quản lý cơ sở dữ liệu giao dịch dưới dạng JSON và tính toán các chỉ số danh mục đầu tư.
"""

import json
import os

DB_FILE = "gold_transactions.json"

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
            "ticker": "Doji",  # Gắn tạm vào Doji để lấy giá tự động
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
    
    current_prices: dict chứa giá thị trường {ticker: {"buy": price, "sell": price}}
    Trả về:
        holdings: dict {asset_name -> dữ liệu tài sản}
        summary: dict chứa tổng số liệu (total_cost, total_value, total_pnl, pnl_pct)
    """
    holdings = {}
    
    # Sắp xếp giao dịch theo ngày tăng dần để tính toán chính xác giá vốn bình quân di động
    sorted_txs = sorted(transactions, key=lambda x: x.get("date", ""))
    
    for r in sorted_txs:
        asset = r["asset"]
        category = r.get("category", "Khác")
        ticker = r.get("ticker", "")
        unit = r["unit"]
        
        if asset not in holdings:
            holdings[asset] = {
                "asset": asset,
                "category": category,
                "ticker": ticker,
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
                # Giảm số lượng nắm giữ
                holdings[asset]["qty"] -= qty
                # Giảm giá trị vốn tương ứng với số lượng bán theo giá vốn bình quân
                holdings[asset]["cost"] -= qty * avg_cost
                
                # Tránh lỗi sai số dấu phẩy động làm qty < 0 rất nhỏ
                if holdings[asset]["qty"] < 1e-9:
                    holdings[asset]["qty"] = 0.0
                    holdings[asset]["cost"] = 0.0

    # Tính toán giá trị hiện tại và lời lỗ
    total_cost = 0.0
    total_value = 0.0
    total_pnl = 0.0
    
    active_holdings = {}
    for asset, h in holdings.items():
        # Chỉ hiển thị tài sản còn số lượng nắm giữ > 0
        if h["qty"] <= 0:
            continue
            
        avg_price = h["cost"] / h["qty"]
        ticker = h["ticker"]
        
        # Lấy giá mua vào trên thị trường (bạn bán ra) để tính giá trị danh mục
        market_price = 0.0
        if ticker in current_prices:
            market_price = current_prices[ticker].get("buy", 0.0)
            
        current_val = h["qty"] * market_price
        pnl = current_val - h["cost"] if market_price > 0 else 0.0
        pnl_pct = (pnl / h["cost"] * 100) if (h["cost"] > 0 and market_price > 0) else 0.0
        
        h["avg_price"] = avg_price
        h["market_price"] = market_price
        h["current_value"] = current_val
        h["pnl"] = pnl
        h["pnl_pct"] = pnl_pct
        
        total_cost += h["cost"]
        if market_price > 0:
            total_value += current_val
            total_pnl += pnl
        else:
            # Nếu không có giá thị trường, xem như giá trị hiện tại = giá vốn (không lãi lỗ tạm tính)
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
