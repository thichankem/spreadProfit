# api_service.py
"""
Dịch vụ lấy giá thực tế từ SJC, Doji (Web Scraping) và Yahoo Finance API.
Hỗ trợ chuyển đổi tiền tệ USD -> VND và Ounce -> Lượng/Chỉ.
"""

import re
import datetime
import threading
from bs4 import BeautifulSoup
import requests
from config import CONVERSION_OUNCE_TO_LUONG

# Cache tỷ giá USD/VND dự phòng
USDVND_CACHE = 25400.0

def get_usdvnd_rate():
    """Lấy tỷ giá USD/VND hiện tại từ Yahoo Finance. Nếu lỗi, trả về giá trị cache."""
    global USDVND_CACHE
    url = "https://query1.finance.yahoo.com/v8/finance/chart/USDVND=X"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            rate = data['chart']['result'][0]['meta']['regularMarketPrice']
            if rate > 10000:
                USDVND_CACHE = float(rate)
    except Exception:
        pass
    return USDVND_CACHE


def fetch_yahoo_price(ticker):
    """
    Lấy giá từ Yahoo Finance cho cổ phiếu, crypto, bạc thế giới.
    Trả về giá gốc (thường bằng USD hoặc VND tùy mã).
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            meta = data['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice')
            currency = meta.get('currency', 'USD')
            return float(price), currency
    except Exception:
        pass
    return None, None


def fetch_vietnam_gold_prices():
    """
    Cào giá vàng SJC và Doji trực tiếp từ các trang chủ tại Việt Nam.
    Trả về dict: {ticker: {"buy": int, "sell": int}}
    """
    prices = {}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124 Safari/537.36"
        )
    }

    # 1. Cào giá Vàng SJC
    try:
        r = requests.get("https://sjc.com.vn/giavang/textContent.php", headers=headers, timeout=6)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                name = cells[0].get_text(strip=True)
                buy_txt  = cells[1].get_text(strip=True).replace(",", "").replace(".", "")
                sell_txt = cells[2].get_text(strip=True).replace(",", "").replace(".", "")
                buy_nums  = re.findall(r"\d{6,}", buy_txt)
                sell_nums = re.findall(r"\d{6,}", sell_txt)
                if buy_nums and sell_nums and "Miếng" in name:
                    prices["SJC"] = {
                        "buy":  int(buy_nums[0]) * 1000,
                        "sell": int(sell_nums[0]) * 1000,
                    }
                    break
    except Exception:
        pass

    # 2. Cào giá Vàng Doji
    try:
        r = requests.get("https://www.doji.vn/bang-gia-vang/", headers=headers, timeout=6)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                name = cells[0].get_text(strip=True)
                buy_txt  = cells[1].get_text(strip=True)
                sell_txt = cells[2].get_text(strip=True)
                buy_nums  = re.findall(r"\d{5,}", buy_txt.replace(",", "").replace(".", ""))
                sell_nums = re.findall(r"\d{5,}", sell_txt.replace(",", "").replace(".", ""))
                if buy_nums and sell_nums and "Nhẫn" in name:
                    prices["Doji"] = {
                        "buy":  int(buy_nums[0]) * 1000,
                        "sell": int(sell_nums[0]) * 1000,
                    }
                    break
    except Exception:
        pass

    return prices


def get_realtime_price(ticker, category, unit=""):
    """
    Hàm tổng hợp để lấy giá trị quy đổi sang VND của bất kỳ mã tài sản nào.
    Trả về dict: {"buy": price_vnd, "sell": price_vnd} hoặc None nếu lỗi.
    """
    # Nếu là vàng Việt Nam
    if ticker in ["SJC", "Doji"]:
        gold_prices = fetch_vietnam_gold_prices()
        if ticker in gold_prices:
            return gold_prices[ticker]
        return None

    # Lấy tỷ giá USD/VND hiện tại
    usdvnd = get_usdvnd_rate()

    # Lấy giá từ Yahoo Finance
    price, currency = fetch_yahoo_price(ticker)
    if price is None:
        return None

    # Quy đổi tiền tệ: Nếu giá trả về bằng USD, nhân với tỷ giá USD/VND
    price_vnd = price
    if currency == "USD" or ticker.endswith("-USD") or ticker in ["SI=F", "GC=F"]:
        price_vnd = price * usdvnd

    # Quy đổi đơn vị kim loại quý thế giới sang đơn vị Việt Nam
    if category == "Bạc" and ticker == "SI=F":
        # SI=F là bạc thế giới tính theo USD / Ounce troy
        # Quy đổi sang Lượng (cây) nếu đơn vị yêu cầu
        if unit == "Lượng" or unit == "Cây":
            price_vnd = price_vnd * CONVERSION_OUNCE_TO_LUONG
        elif unit == "Chỉ":
            price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 10.0
        elif unit == "Gram":
            price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 37.5

    elif category == "Vàng" and ticker == "GC=F":
        # Vàng thế giới quy đổi tương tự
        if unit == "Lượng" or unit == "Cây":
            price_vnd = price_vnd * CONVERSION_OUNCE_TO_LUONG
        elif unit == "Chỉ":
            price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 10.0
        elif unit == "Gram":
            price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 37.5

    # Cho các loại cổ phiếu, crypto, ngoại tệ... giá mua/bán thị trường tạm tính bằng nhau
    return {"buy": price_vnd, "sell": price_vnd}


def fetch_all_prices_threaded(tickers_info, callback):
    """
    Chạy luồng phụ tải giá của danh sách các mã tài sản.
    tickers_info: list các dict {"ticker": str, "category": str, "unit": str}
    callback: hàm callback nhận kết quả dict {ticker -> {"buy", "sell"}} sau khi tải xong.
    """
    def worker():
        results = {}
        # Ưu tiên lấy giá vàng Việt Nam gộp trước để tối ưu số lượt gọi mạng
        gold_prices = fetch_vietnam_gold_prices()
        results.update(gold_prices)
        
        # Lấy tỷ giá USD/VND một lần duy nhất
        usdvnd = get_usdvnd_rate()
        
        for item in tickers_info:
            ticker = item["ticker"]
            category = item["category"]
            unit = item.get("unit", "")
            
            if ticker in results:
                continue
                
            price, currency = fetch_yahoo_price(ticker)
            if price is not None:
                price_vnd = price
                if currency == "USD" or ticker.endswith("-USD") or ticker in ["SI=F", "GC=F"]:
                    price_vnd = price * usdvnd
                    
                # Quy đổi đơn vị kim loại quý
                if category == "Bạc" and ticker == "SI=F":
                    if unit in ["Lượng", "Cây"]:
                        price_vnd = price_vnd * CONVERSION_OUNCE_TO_LUONG
                    elif unit == "Chỉ":
                        price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 10.0
                    elif unit == "Gram":
                        price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 37.5
                elif category == "Vàng" and ticker == "GC=F":
                    if unit in ["Lượng", "Cây"]:
                        price_vnd = price_vnd * CONVERSION_OUNCE_TO_LUONG
                    elif unit == "Chỉ":
                        price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 10.0
                    elif unit == "Gram":
                        price_vnd = (price_vnd * CONVERSION_OUNCE_TO_LUONG) / 37.5
                        
                results[ticker] = {"buy": price_vnd, "sell": price_vnd}
        
        # Trả kết quả về luồng chính thông qua callback
        callback(results)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
