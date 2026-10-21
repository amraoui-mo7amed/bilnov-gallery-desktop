# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the standalone orga+ Copy Tool."""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None
ROOT_DIR = Path.cwd()

datas = []
binaries = []
icon_ico = str(ROOT_DIR / 'desktop' / 'assets' / 'icon.ico')
icon_icns = str(ROOT_DIR / 'desktop' / 'assets' / 'icon.icns')

hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]

try:
    py7zz_datas, py7zz_binaries, py7zz_hiddenimports = collect_all('py7zz')
    datas += py7zz_datas
    binaries += py7zz_binaries
    hiddenimports += py7zz_hiddenimports
except Exception as e:
    print(f"Warning: collect_all('py7zz') failed: {e}")

a = Analysis(
    [str(ROOT_DIR / 'tools' / 'orga_copy_tool.py')],
    pathex=[str(ROOT_DIR), str(ROOT_DIR / 'tools')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'win32':
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name='orga+ Copy Tool', debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, runtime_tmpdir=None, console=False,
        disable_windowed_traceback=False, argv_emulation=False,
        target_arch=None, codesign_identity=None, entitlements_file=None,
        icon=icon_ico,
    )
elif sys.platform == 'darwin':
    exe = EXE(
        pyz, a.scripts, [], exclude_binaries=True,
        name='orga+ Copy Tool', debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False,
        disable_windowed_traceback=False, argv_emulation=False,
        target_arch=None, codesign_identity=None, entitlements_file=None,
        icon=icon_icns,
    )
    coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False,
                   upx_exclude=[], name='orga+ Copy Tool')
    app = BUNDLE(
        coll, name='orga+ Copy Tool.app', icon=icon_icns,
        bundle_identifier='com.orgaplus.copytool',
        info_plist={
            'CFBundleName': 'orga+ Copy Tool',
            'CFBundleDisplayName': 'orga+ Copy Tool',
            'CFBundleShortVersionString': '2.3.0',
            'CFBundleVersion': '2.3.0',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '11.0',
        },
    )
else:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name='orga+ Copy Tool', debug=False, bootloader_ignore_signals=False,
        strip=False, upx=False, console=False,
        disable_windowed_traceback=False,
        icon=icon_ico,
    )
