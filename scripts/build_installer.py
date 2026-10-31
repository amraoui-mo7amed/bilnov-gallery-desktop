#!/usr/bin/env python3
"""
Build & Package orga+ Windows Installer
=======================================
Builds orga+ desktop application with PyInstaller and compiles the Inno Setup
installer (dist/orga+_Setup.exe), allowing users to install the application
and select Desktop shortcut, Taskbar shortcut, or both.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def find_iscc() -> Path | None:
    """Finds Inno Setup Compiler (iscc) on the system."""
    which_iscc = shutil.which("iscc") or shutil.which("ISCC")
    if which_iscc:
        return Path(which_iscc)

    candidate_locations = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 5\ISCC.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]
    for loc in candidate_locations:
        if loc.exists():
            return loc
    return None


def build_pyinstaller():
    """Runs PyInstaller using bilnov_gallery.spec."""
    spec_path = ROOT_DIR / "bilnov_gallery.spec"
    print(f"--> Building application with PyInstaller using {spec_path.name}...")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "-y", str(spec_path)]
    subprocess.check_call(cmd, cwd=str(ROOT_DIR))


def build_installer():
    """Compiles the Inno Setup script."""
    iscc = find_iscc()
    iss_file = ROOT_DIR / "installer" / "orga_plus.iss"

    if not iscc:
        print("\n[WARNING] Inno Setup Compiler (ISCC) was not found in PATH or standard directories.")
        print("To compile the installer on Windows, install Inno Setup 6:")
        print("  winget install JRSoftware.InnoSetup")
        print("  choco install innosetup")
        print(f"Then run:\n  ISCC {iss_file}")
        return False

    print(f"\n--> Compiling installer using {iscc}...")
    cmd = [str(iscc), str(iss_file)]
    subprocess.check_call(cmd, cwd=str(ROOT_DIR))

    out_file = ROOT_DIR / "dist" / "orga+_Setup.exe"
    if out_file.exists():
        print(f"\n[SUCCESS] Installer successfully built: {out_file}")
        print(f"File size: {out_file.stat().st_size / (1024 * 1024):.2f} MB")
        return True
    return False


def main():
    build_pyinstaller()
    if sys.platform == "win32":
        build_installer()
    else:
        print(f"\nNote: Inno Setup compilation is performed on Windows runners (or via Wine).")
        print(f"Inno Setup script is ready at: {ROOT_DIR / 'installer' / 'orga_plus.iss'}")


if __name__ == "__main__":
    main()
