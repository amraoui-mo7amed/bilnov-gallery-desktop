"""
Desktop Backend package for PySide6 application.
"""
from .library import LibraryManager, library_manager
from .licensing import LicenseManager, license_manager

try:
    from .app_bridge import AppBridge
    from .image_provider import BilnovImageProvider, image_provider_instance
except (ImportError, ModuleNotFoundError):
    AppBridge = None
    BilnovImageProvider = None
    image_provider_instance = None

__all__ = [
    "AppBridge",
    "LibraryManager",
    "library_manager",
    "LicenseManager",
    "license_manager",
    "BilnovImageProvider",
    "image_provider_instance",
]
