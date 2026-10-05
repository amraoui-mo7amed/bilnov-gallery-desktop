# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

ROOT_DIR = Path.cwd()

datas = [
    (str(ROOT_DIR / 'desktop' / 'qml'), 'desktop/qml'),
    (str(ROOT_DIR / 'desktop' / 'assets'), 'desktop/assets'),
]
if (ROOT_DIR / 'storage').exists():
    datas.append((str(ROOT_DIR / 'storage'), 'storage'))
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

icon_ico = str(ROOT_DIR / 'desktop' / 'assets' / 'icon.ico')
icon_icns = str(ROOT_DIR / 'desktop' / 'assets' / 'icon.icns')

if sys.platform == 'win32':
    # 1. Standalone Single-File Executable
    # Contains Python DLL, PySide6 DLLs, and QML data embedded directly inside BilnovGallery.exe
    exe_standalone = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='BilnovGallery',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_ico,
    )

    # 2. Portable Directory Distribution (All DLLs alongside BilnovGallery.exe)
    exe_dir = EXE(
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
        icon=icon_ico,
    )

    coll = COLLECT(
        exe_dir,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='BilnovGallery-Portable',
    )

elif sys.platform == 'darwin':
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
        icon=icon_icns,
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

    app = BUNDLE(
        coll,
        name='BilnovGallery.app',
        icon=icon_icns,
        bundle_identifier='com.bilnov.gallery',
        info_plist={
            'CFBundleShortVersionString': '1.2.1',
            'CFBundleVersion': '1.2.1',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '11.0',
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='BilnovGallery',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        icon=icon_ico,
    )
