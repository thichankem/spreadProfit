# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller packaging specification for spreadProfit.

Bundles Python bytecode, icons, and seed database files into a self-contained
single-file Windows executable (SpreadProfit.exe).
"""

import os

ROOT_DIR = os.path.abspath(SPECPATH)
if os.path.basename(ROOT_DIR) == "scripts":
    ROOT_DIR = os.path.dirname(ROOT_DIR)

datas = [
    (os.path.join(ROOT_DIR, 'assets', 'app_icon.ico'), 'assets'),
    (os.path.join(ROOT_DIR, 'assets', 'app_icon.png'), 'assets'),
    (os.path.join(ROOT_DIR, '_seed', 'gold_transactions.json'), '_seed'),
    (os.path.join(ROOT_DIR, '_seed', 'market_prices.json'), '_seed'),
    (os.path.join(ROOT_DIR, '_seed', 'custom_assets.json'), '_seed'),
]

icon_path = os.path.join(ROOT_DIR, 'assets', 'app_icon.ico')

a = Analysis(
    [os.path.join(ROOT_DIR, 'app.py')],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'openpyxl',
        'matplotlib.backends.backend_tkagg',
        'spreadprofit',
        'spreadprofit.config',
        'spreadprofit.db',
        'spreadprofit.cloud',
        'spreadprofit.ui',
        'spreadprofit.ui.main',
        'spreadprofit.ui.portfolio',
        'spreadprofit.ui.transactions',
        'spreadprofit.ui.charts',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        'IPython', 'jupyter', 'notebook', 'nbconvert', 'nbformat',
        'scipy', 'pandas', 'sympy', 'pytest', 'sphinx',
        'tornado', 'zmq', 'test', 'setuptools',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SpreadProfit',
    icon=icon_path,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
