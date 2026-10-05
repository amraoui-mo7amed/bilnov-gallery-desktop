"""
Bilnov Gallery Configuration
"""

import os
import sys
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent

# The one and only data folder the app reads
DEFAULT_DATA_DIR = str(BASE_DIR / "data")
DATA_DIR = Path(config("DATA_DIR", default=DEFAULT_DATA_DIR)).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Separate user cache directory outside ./data to protect data folder
if sys.platform == "darwin":
    USER_CACHE_DIR = Path.home() / "Library" / "Caches" / "BilnovGallery"
elif sys.platform == "win32":
    USER_CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "BilnovGallery" / "Cache"
else:
    USER_CACHE_DIR = Path.home() / ".cache" / "bilnov_gallery"

IMAGE_CACHE_DIR = USER_CACHE_DIR / "images"
IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Licensing API Configuration (from openapi.json)
LICENSE_SERVER_URL = config("LICENSE_SERVER_URL", default="http://localhost:8000").rstrip("/")
ADMIN_KEY = config("ADMIN_KEY", default="")
OFFLINE_GRACE_DAYS = 7
HEARTBEAT_INTERVAL_SECONDS = 4 * 3600  # 4 hours
LICENSE_FILE_PATH = Path.home() / ".zed_license.json"
