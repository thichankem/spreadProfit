"""
Automated PyInstaller build script for spreadProfit.

Compiles the standalone Windows executable and produces a portable distribution zip:
    dist/SpreadProfit.exe             -> Self-contained single-file binary with embedded seed data
    dist/SpreadProfit_portable/       -> Portable directory bundle (exe + data folder + quickstart guide)
    dist/SpreadProfit_portable.zip    -> Compressed distribution archive for distribution

Usage:
    python build_exe.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(ROOT_DIR, "_seed")
DATA_DIR = os.path.join(ROOT_DIR, "data")
DIST_DIR = os.path.join(ROOT_DIR, "dist")
PORTABLE_DIR = os.path.join(DIST_DIR, "SpreadProfit_portable")
EXE_NAME = "SpreadProfit.exe"
TRACKED_FILES = ("gold_transactions.json", "market_prices.json", "custom_assets.json")

PORTABLE_INSTRUCTIONS = """SpreadProfit - Portable Distribution Quickstart
===================================================

1. Extract or copy this entire folder to any Windows machine (USB flash drive, OneDrive, etc.).
2. Double-click SpreadProfit.exe to run. No Python installation or runtime setup is required.

YOUR DATA & PRIVACY
-------------------
- All transactions, custom assets, and benchmark market quotes are stored in the local 'data/' folder
  adjacent to the executable.
- To backup your portfolio, copy the 'data/' folder or use the in-app 'Cloud Backup' button.
- If launched in a restricted directory without write access (e.g., C:/Program Files), SpreadProfit
  automatically falls back to storing data safely in: %APPDATA%/spreadProfit

NOTES
-----
- First launch may take 5-10 seconds to extract bundled resources into memory. Subsequent runs are instant.
- Windows SmartScreen may show an 'Unknown Publisher' prompt because the binary is unsigned.
  Click 'More info' -> 'Run anyway'.
"""


def collect_seed_data() -> None:
    """Consolidate current database files to embed inside the standalone binary."""
    os.makedirs(SEED_DIR, exist_ok=True)
    for fname in TRACKED_FILES:
        source_candidates = (
            os.path.join(DATA_DIR, fname),
            os.path.join(ROOT_DIR, fname),
        )
        for src in source_candidates:
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(SEED_DIR, fname))
                print(f"  + Embedding seed file: {os.path.relpath(src, ROOT_DIR)}")
                break
        else:
            with open(os.path.join(SEED_DIR, fname), "w", encoding="utf-8") as f:
                f.write("[]" if fname == "gold_transactions.json" else "{}")
            print(f"  + Initializing empty seed file: {fname}")


def run_pyinstaller() -> None:
    """Invoke PyInstaller build with clean caches."""
    print("\n[2/4] Invoking PyInstaller build process...")
    subprocess.check_call(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "app.spec"],
        cwd=ROOT_DIR,
    )


def assemble_portable_bundle() -> None:
    """Assemble portable directory bundle containing executable and data folder."""
    print("\n[3/4] Assembling portable distribution bundle...")
    exe_path = os.path.join(DIST_DIR, EXE_NAME)
    if not os.path.exists(exe_path):
        raise SystemExit(f"Build failed: {exe_path} not found.")

    if os.path.isdir(PORTABLE_DIR):
        shutil.rmtree(PORTABLE_DIR)
    os.makedirs(os.path.join(PORTABLE_DIR, "data"), exist_ok=True)

    shutil.copyfile(exe_path, os.path.join(PORTABLE_DIR, EXE_NAME))
    for fname in TRACKED_FILES:
        src = os.path.join(SEED_DIR, fname)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(PORTABLE_DIR, "data", fname))

    with open(os.path.join(PORTABLE_DIR, "QUICKSTART.txt"), "w", encoding="utf-8") as f:
        f.write(PORTABLE_INSTRUCTIONS)


def compress_distribution_zip() -> str:
    """Compress the portable directory into a distributable zip archive."""
    print("\n[4/4] Compressing portable distribution archive...")
    zip_path = PORTABLE_DIR + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(PORTABLE_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                zf.write(full_path, os.path.relpath(full_path, DIST_DIR))
    return zip_path


def main() -> None:
    print("=== spreadProfit Standalone Distribution Builder ===")
    print("[1/4] Gathering seed database files...")
    collect_seed_data()
    run_pyinstaller()
    assemble_portable_bundle()
    zip_path = compress_distribution_zip()

    exe_file = os.path.join(PORTABLE_DIR, EXE_NAME)
    size_mb = os.path.getsize(exe_file) / (1024 * 1024)
    print("\n=== BUILD COMPLETE ===")
    print(f"  Binary      : {exe_file} ({size_mb:.1f} MB)")
    print(f"  Portable Dir: {PORTABLE_DIR}")
    print(f"  Zip Archive : {zip_path}")


if __name__ == "__main__":
    main()
