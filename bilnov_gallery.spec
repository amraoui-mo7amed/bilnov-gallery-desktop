# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

ROOT_DIR = Path.cwd()

datas = [
    (str(ROOT_DIR / 'desktop' / 'qml'), 'desktop/qml'),
    (str(ROOT_DIR / 'desktop' / 'assets'), 'desktop/assets'),
]
if (ROOT_DIR / 'data').exists():
    datas.append((str(ROOT_DIR / 'data'), 'data'))

hiddenimports = [
    'PySide6.QtQuick',
    'PySide6.QtQml',
    'PySide6.QtQuickControls2',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtCore',
    'requests',
    'decouple',
    'desktop.backend.app_bridge',
    'desktop.backend.image_provider',
    'desktop.backend.library',
    'desktop.backend.licensing',
    'config',
]

a = Analysis(
    ['desktop/main.py'],
    pathex=[str(ROOT_DIR), str(ROOT_DIR / 'desktop')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas', 'playwright', 'cloudscraper', 'bs4'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BilnovGallery',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='BilnovGallery',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='BilnovGallery.app',
        icon=None,
        bundle_identifier='com.bilnov.gallery',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '11.0',
        },
    )
