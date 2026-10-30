# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller packaging specification for spreadProfit.

Bundles Python bytecode, icons, and seed database files into a self-contained
single-file Windows executable (SpreadProfit.exe).
"""

datas = [
    ('app_icon.ico', '.'),
    ('app_icon.png', '.'),
    ('_seed/gold_transactions.json', '_seed'),
    ('_seed/market_prices.json', '_seed'),
    ('_seed/custom_assets.json', '_seed'),
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'openpyxl',
        'matplotlib.backends.backend_tkagg',
        'cloud_backup',
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
    icon='app_icon.ico',
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
