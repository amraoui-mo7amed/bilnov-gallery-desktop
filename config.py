"""
olga+ Configuration
"""

import os
import sys
from pathlib import Path
from decouple import config

if getattr(sys, "frozen", False):
    if sys.platform == "darwin":
        app_dir = Path(sys.executable).resolve().parent.parent.parent
        if (Path.cwd() / "storage").exists() or (Path.cwd() / "data").exists():
            BASE_DIR = Path.cwd()
        else:
            BASE_DIR = app_dir.parent
    else:
        if (Path.cwd() / "storage").exists() or (Path.cwd() / "data").exists():
            BASE_DIR = Path.cwd()
        else:
            BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

# The primary asset library folder the app reads (defaults to ./storage)
if (BASE_DIR / "storage").exists():
    DEFAULT_DATA_DIR = str(BASE_DIR / "storage")
elif (BASE_DIR / "data").exists():
    DEFAULT_DATA_DIR = str(BASE_DIR / "data")
else:
    DEFAULT_DATA_DIR = str(BASE_DIR / "storage")

DATA_DIR = Path(config("DATA_DIR", default=DEFAULT_DATA_DIR)).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Separate user cache directory outside ./data to protect data folder
if sys.platform == "darwin":
    USER_CACHE_DIR = Path.home() / "Library" / "Caches" / "OlgaPlus"
elif sys.platform == "win32":
    USER_CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "OlgaPlus" / "Cache"
else:
    USER_CACHE_DIR = Path.home() / ".cache" / "olga_plus"

IMAGE_CACHE_DIR = USER_CACHE_DIR / "images"
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Licensing API Configuration (from openapi.json)
# All license endpoints are public machine-to-machine APIs: no admin credentials required.
LICENSE_SERVER_URL = config("LICENSE_SERVER_URL", default="https://bilnov-gallery.bilnov.com").rstrip("/")
OFFLINE_GRACE_DAYS = 7
HEARTBEAT_INTERVAL_SECONDS = 4 * 3600  # 4 hours
LICENSE_FILE_PATH = Path.home() / ".zed_license.json"
