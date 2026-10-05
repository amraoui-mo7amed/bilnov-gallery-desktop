"""
Bilnov Gallery Desktop PySide6 QObject Bridge
Connecting Qt Quick (QML) to the local LibraryManager (reading ./data)
and the licensing lifecycle engine (implementing openapi.json).
All scraper mechanisms, write/copy functions, and settings have been completely removed.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import (
    Property,
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices, QGuiApplication

from config import DATA_DIR, HEARTBEAT_INTERVAL_SECONDS
from .library import library_manager
from .licensing import license_manager


class Worker(QRunnable):
    """Generic worker for running long-running operations in background threads."""

    def __init__(
        self,
        fn: Callable,
        *args,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.on_success = on_success
        self.on_error = on_error

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            if self.on_success:
                self.on_success(result)
        except Exception as exc:
            if self.on_error:
                self.on_error(exc)


class AppBridge(QObject):
    # Reactive state change signals
    licenseChanged = Signal()
    activationResult = Signal(bool, str)

    libraryItemsChanged = Signal()
    libraryLoadingChanged = Signal()
    libraryTotalChanged = Signal()

    categoriesChanged = Signal()
    categoriesLoadingChanged = Signal()

    # User notification signals
    toast = Signal(str, str)  # (type: 'info'|'success'|'warning'|'error', message)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.lib = library_manager
        self.lic = license_manager

        # Library state
        self._library_items: List[Dict[str, Any]] = []
        self._library_loading = False
        self._library_total = 0

        self._categories: List[Dict[str, Any]] = []
        self._categories_loading = False

        # Heartbeat timer (fires every 4 hours as specified in openapi.json)
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.setInterval(HEARTBEAT_INTERVAL_SECONDS * 1000)
        self.heartbeat_timer.timeout.connect(self.checkHeartbeat)
        self.heartbeat_timer.start()

    # =============================================================
    # Licensing Properties (openapi.json)
    # =============================================================

    @Property(bool, notify=licenseChanged)
    def isLicensed(self) -> bool:
        return self.lic.current_state.is_valid

    @Property(str, notify=licenseChanged)
    def licenseStatusCode(self) -> str:
        return self.lic.current_state.status_code

    @Property(str, notify=licenseChanged)
    def licenseMessage(self) -> str:
        return self.lic.current_state.message

    @Property(str, notify=licenseChanged)
    def licenseKey(self) -> str:
        return self.lic.current_state.license_key

    @Property(str, notify=licenseChanged)
    def customerName(self) -> str:
        return self.lic.current_state.customer_name

    @Property(str, notify=licenseChanged)
    def expiresAt(self) -> str:
        return self.lic.current_state.expires_at or "Perpetual / Unset"

    @Property(str, notify=licenseChanged)
    def deviceId(self) -> str:
        return self.lic.device_id

    @Property(int, notify=licenseChanged)
    def offlineDaysRemaining(self) -> int:
        return self.lic.current_state.offline_days_remaining

    # =============================================================
    # Library Properties (Reading exclusively ./data)
    # =============================================================

    @Property("QVariant", notify=libraryItemsChanged)
    def libraryItems(self) -> List[Dict[str, Any]]:
        return self._library_items

    @Property(bool, notify=libraryLoadingChanged)
    def libraryLoading(self) -> bool:
        return self._library_loading

    @Property(int, notify=libraryTotalChanged)
    def libraryTotal(self) -> int:
        return self._library_total

    @Property("QVariant", notify=categoriesChanged)
    def categories(self) -> List[Dict[str, Any]]:
        return self._categories

    @Property(bool, notify=categoriesLoadingChanged)
    def categoriesLoading(self) -> bool:
        return self._categories_loading

    @Property(str, constant=True)
    def dataDir(self) -> str:
        return str(DATA_DIR)

    # =============================================================
    # Licensing Slots
    # =============================================================

    @Slot(str, str, str, str, str)
    def activateLicense(self, key: str, name: str, email: str, phone: str, address: str = ""):
        """Invokes initial activation endpoint POST /api/v1/license/activate."""
        def _task():
            return self.lic.activate_license(key, name, email, phone, address)

        def _on_success(res):
            success, msg = res
            self.licenseChanged.emit()
            self.activationResult.emit(success, msg)
            if success:
                self.toast.emit("success", f"Activation successful! Welcome, {name}.")
                self.loadLibrary()
                self.loadCategories()
            else:
                self.toast.emit("error", f"Activation error: {msg}")

        def _on_error(exc):
            err_msg = str(exc)
            self.licenseChanged.emit()
            self.activationResult.emit(False, err_msg)
            self.toast.emit("error", f"Activation failed: {err_msg}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

    @Slot()
    def verifyLicense(self):
        """Verifies license with handshake POST /api/v1/license/verify with offline grace check."""
        def _task():
            return self.lic.verify_license()

        def _on_success(res):
            success, msg = res
            self.licenseChanged.emit()
            if success:
                if self.lic.current_state.status_code == "ACTIVE_OFFLINE":
                    self.toast.emit("warning", f"Offline mode active ({self.lic.current_state.offline_days_remaining} days left)")
            else:
                if self.lic.current_state.status_code != "NEEDS_ACTIVATION":
                    self.toast.emit("error", msg)

        def _on_error(exc):
            logger.error("Verification worker error: %s", exc)
            self.licenseChanged.emit()

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

    @Slot()
    def checkHeartbeat(self):
        """Background heartbeat query POST /api/v1/license/heartbeat."""
        def _task():
            return self.lic.heartbeat()

        def _on_success(res):
            success, msg = res
            self.licenseChanged.emit()
            if not success:
                self.toast.emit("error", f"License Alert: {msg}")

        self.thread_pool.start(Worker(_task, on_success=_on_success))

    # =============================================================
    # Library Slots (Reading ./data)
    # =============================================================

    @Slot(str, str)
    def loadLibrary(self, search: str = "", category: str = "all"):
        """Scans ./data for 3D model articles."""
        self._library_loading = True
        self.libraryLoadingChanged.emit()

        def _task():
            cat_filter = category if (category and category != "all") else None
            return self.lib.scan_library(search=search or None, category_filter=cat_filter)

        def _on_success(res):
            items = res.get("items", [])
            for item in items:
                # Convert local image paths to file:// QUrl strings
                raw_imgs = item.get("images", [])
                imgs_file_urls = []
                for rel_img in raw_imgs:
                    p = (DATA_DIR / rel_img).resolve()
                    if p.exists():
                        imgs_file_urls.append(QUrl.fromLocalFile(str(p)).toString())

                item["images_full"] = imgs_file_urls
                item["first_image"] = imgs_file_urls[0] if imgs_file_urls else ""
                item["folder_full_path"] = str((DATA_DIR / item["folder_path"]).resolve())

                if item.get("model_path"):
                    item["model_file_full"] = str((DATA_DIR / item["model_path"]).resolve())
                else:
                    item["model_file_full"] = ""

            self._library_items = items
            self._library_total = res.get("stats", {}).get("total_models", len(items))
            self._library_loading = False
            self.libraryItemsChanged.emit()
            self.libraryTotalChanged.emit()
            self.libraryLoadingChanged.emit()

        def _on_error(exc):
            self._library_loading = False
            self.libraryLoadingChanged.emit()
            self.toast.emit("error", f"Library load failed: {str(exc)}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

    @Slot()
    def loadCategories(self):
        """Loads categories discovered from ./data."""
        self._categories_loading = True
        self.categoriesLoadingChanged.emit()

        def _task():
            return self.lib.load_categories_tree()

        def _on_success(cats):
            self._categories = cats
            self._categories_loading = False
            self.categoriesChanged.emit()
            self.categoriesLoadingChanged.emit()

        def _on_error(exc):
            self._categories_loading = False
            self.categoriesLoadingChanged.emit()
            self.toast.emit("error", f"Categories load failed: {str(exc)}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

    # =============================================================
    # Exact Article Location Slot (Task 6)
    # =============================================================

    @Slot(str)
    def openArticleLocation(self, folder_path: str):
        """
        Opens the exact article folder inside ./data in macOS Finder or system file manager.
        """
        if not folder_path:
            target = DATA_DIR.resolve()
        else:
            target = (DATA_DIR / folder_path).resolve()

        # Security check: verify path is strictly within DATA_DIR
        try:
            target.relative_to(DATA_DIR.resolve())
        except ValueError:
            self.toast.emit("error", "Access denied: Path is outside ./data")
            return

        if not target.exists():
            self.toast.emit("warning", f"Folder does not exist: {folder_path}")
            return

        if sys.platform == "darwin":
            subprocess.run(["open", str(target)], check=False)
        elif sys.platform == "win32":
            os.startfile(str(target))
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    @Slot(str)
    def openFolder(self, folder_path: str):
        """Alias for openArticleLocation."""
        self.openArticleLocation(folder_path)

    @Slot(str)
    def copyToClipboard(self, text: str):
        """Copies text to system clipboard."""
        clean_text = str(text or "").strip()
        if not clean_text:
            return
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(clean_text)
            self.toast.emit("success", "Copied to clipboard!")

    @Slot(str)
    def deleteLibraryModel(self, folder_path: str):
        """Deletes model folder from local ./data library."""
        def _task():
            return self.lib.delete_item(folder_path)

        def _on_success(ok):
            if ok:
                self.toast.emit("success", "Model folder deleted from disk")
                self.loadLibrary()
                self.loadCategories()
            else:
                self.toast.emit("error", "Could not delete folder")

        def _on_error(exc):
            self.toast.emit("error", f"Delete error: {str(exc)}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))
