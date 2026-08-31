# build_exe.py
"""
Đóng gói ứng dụng thành 1 file exe duy nhất kèm dữ liệu hiện tại.

Cách dùng:
    python build_exe.py

Kết quả:
    dist/QuanLyTaiSan.exe                  -> file exe chạy độc lập (đã nhúng sẵn dữ liệu)
    dist/QuanLyTaiSan_portable/            -> bộ portable: exe + thư mục data + hướng dẫn
    dist/QuanLyTaiSan_portable.zip         -> bản nén để chép sang máy Windows khác
"""

import os
import shutil
import subprocess
import sys
import zipfile

# Đảm bảo in được tiếng Việt trên Command Prompt
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(ROOT, "_seed")
DATA_DIR = os.path.join(ROOT, "data")
DIST_DIR = os.path.join(ROOT, "dist")
PORTABLE_DIR = os.path.join(DIST_DIR, "QuanLyTaiSan_portable")
EXE_NAME = "QuanLyTaiSan.exe"
DATA_FILES = ("gold_transactions.json", "market_prices.json", "custom_assets.json")

HUONG_DAN = """HƯỚNG DẪN SỬ DỤNG - Quản lý Tài Sản Cá Nhân
================================================

1. Chép nguyên thư mục này sang máy Windows khác (USB, OneDrive, Zalo...).
2. Nhấn đúp vào file QuanLyTaiSan.exe là chạy được ngay, không cần cài Python
   hay bất cứ phần mềm nào khác.

DỮ LIỆU CỦA BẠN
---------------
- Toàn bộ giao dịch, giá thị trường và danh mục tài sản được lưu trong thư mục "data"
  nằm cạnh file exe. Muốn sao lưu thì chỉ cần copy thư mục "data" này.
- Nếu chỉ chép mỗi file QuanLyTaiSan.exe (không chép thư mục data), ứng dụng vẫn chạy
  và tự khôi phục dữ liệu đã được nhúng sẵn bên trong exe tại thời điểm đóng gói.
- Muốn chuyển dữ liệu MỚI NHẤT sang máy khác thì phải chép cả thư mục "data".
- Nếu đặt exe vào nơi không có quyền ghi (ví dụ C:/Program Files), dữ liệu sẽ tự
  chuyển sang lưu tại: %APPDATA%/spreadProfit

LƯU Ý
-----
- Lần chạy đầu tiên có thể mất 5-15 giây để giải nén, các lần sau nhanh hơn.
- Windows SmartScreen có thể cảnh báo "Unknown publisher" vì file chưa mua chữ ký số:
  bấm "More info" -> "Run anyway".
- Một số phần mềm diệt virus có thể cảnh báo nhầm với file exe đóng gói bằng PyInstaller.
"""


def collect_seed():
    """Gom dữ liệu đang dùng làm bản nhúng trong exe."""
    os.makedirs(SEED_DIR, exist_ok=True)
    for name in DATA_FILES:
        for source in (os.path.join(DATA_DIR, name), os.path.join(ROOT, name)):
            if os.path.exists(source):
                shutil.copyfile(source, os.path.join(SEED_DIR, name))
                print(f"  + nhúng dữ liệu: {os.path.relpath(source, ROOT)}")
                break
        else:
            # Không có dữ liệu thì tạo file rỗng để PyInstaller không báo thiếu
            with open(os.path.join(SEED_DIR, name), "w", encoding="utf-8") as f:
                f.write("[]" if name == "gold_transactions.json" else "{}")
            print(f"  + nhúng dữ liệu rỗng: {name}")


def run_pyinstaller():
    print("\n[2/4] Chạy PyInstaller (có thể mất vài phút)...")
    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "app.spec"],
        cwd=ROOT,
    )


def make_portable():
    print("\n[3/4] Tạo bộ portable...")
    exe_path = os.path.join(DIST_DIR, EXE_NAME)
    if not os.path.exists(exe_path):
        raise SystemExit(f"Không tìm thấy {exe_path}")

    if os.path.isdir(PORTABLE_DIR):
        shutil.rmtree(PORTABLE_DIR)
    os.makedirs(os.path.join(PORTABLE_DIR, "data"), exist_ok=True)

    shutil.copyfile(exe_path, os.path.join(PORTABLE_DIR, EXE_NAME))
    for name in DATA_FILES:
        shutil.copyfile(os.path.join(SEED_DIR, name), os.path.join(PORTABLE_DIR, "data", name))
    with open(os.path.join(PORTABLE_DIR, "HUONG_DAN.txt"), "w", encoding="utf-8") as f:
        f.write(HUONG_DAN)


def make_zip():
    print("\n[4/4] Nén thành file zip...")
    zip_path = PORTABLE_DIR + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder, _, files in os.walk(PORTABLE_DIR):
            for name in files:
                full = os.path.join(folder, name)
                zf.write(full, os.path.relpath(full, DIST_DIR))
    return zip_path


if __name__ == "__main__":
    print("[1/4] Gom dữ liệu hiện tại...")
    collect_seed()
    run_pyinstaller()
    make_portable()
    zip_path = make_zip()

    size_mb = os.path.getsize(os.path.join(PORTABLE_DIR, EXE_NAME)) / 1024 / 1024
    print("\n=== XONG ===")
    print(f"  exe      : {os.path.join(DIST_DIR, EXE_NAME)}  ({size_mb:.1f} MB)")
    print(f"  portable : {PORTABLE_DIR}")
    print(f"  zip      : {zip_path}")
