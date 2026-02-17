# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('templates', 'templates'),
    ('staticfiles', 'staticfiles'),
    ('locale', 'locale'),
    ('manager/templates', 'manager/templates'),
    ('version.py', '.'),
    ('core/updater.py', '.'),
    ('icon.ico', '.'),
    ('version.rc', '.'),
    ('db.sqlite3', '.'),
    ('media', 'media'),      # Added media folder
]

binaries = []
hiddenimports = [
    'waitress', 
    'whitenoise', 
    'whitenoise.middleware', 
    'django.core.management', 
    'django.db.backends.sqlite3'
]

# Collect all data and imports from our main apps and dependencies
for pkg in ['manager', 'core', 'infrastructure', 'unfold', 'whitenoise']:
    try:
        tmp_ret = collect_all(pkg)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except ImportError:
        pass

a = Analysis(
    ['run_cafe.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Internet2000_win10', # Changed name
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    version_info={
        "name": "Internet2000_win10",
        "version": (1, 0, 0, 3),
        "company_name": "Internet 2000 Team",
        "file_description": "Cafe Management System Server",
        "legal_copyright": "Copyright (C) 2026 Internet 2000 Team",
        "original_filename": "Internet2000_win10.exe",
        "product_name": "Internet 2000 Cafe Management System",
        "product_version": (1, 0, 0, 3),
    },
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Internet2000_win10', # Changed name
)
