"""
Bilnov Gallery Desktop PySide6 QObject Bridge
Connecting Qt Quick (QML) to the local LibraryManager (reading ./data)
and the licensing lifecycle engine (implementing openapi.json).
All scraper mechanisms, write/copy functions, and settings have been completely removed.
"""

import datetime
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import (
    Property,
    QObject,
    QRunnable,
    QSettings,
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

logger = logging.getLogger("app_bridge")


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

    # Client Registration & Inquiry (openapi.json)
    clientProfileResult = Signal(bool, str)  # (success, message)
    clientStatusResult = Signal(bool, str, str, str)  # (success, status_code, message, license_key)

    languageChanged = Signal()

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

        # First-paint licensing state (trial by default) so the lock overlay
        # never flashes before the async verify_license() completes.
        self.lic.bootstrap_state()

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
    def deviceId(self) -> str:
        return self.lic.device_id

    @Property(int, notify=licenseChanged)
    def offlineDaysRemaining(self) -> int:
        return self.lic.current_state.offline_days_remaining

    @Property(bool, notify=licenseChanged)
    def isTrial(self) -> bool:
        return self.lic.current_state.status_code == "TRIAL"

    @Property(str, notify=licenseChanged)
    def expiresAt(self) -> str:
        return self.lic.current_state.expires_at or "Perpetual / Unset"

    @Property(str, notify=licenseChanged)
    def customerEmail(self) -> str:
        return self.lic.current_state.customer_email or ""

    @Property(str, notify=licenseChanged)
    def customerPhone(self) -> str:
        return self.lic.current_state.customer_phone or ""

    @Property(str, notify=licenseChanged)
    def licenseExpiresAt(self) -> str:
        return self.lic.current_state.expires_at or "Perpetual"

    @staticmethod
    def _parse_expiry(value: str):
        """Parses expires_at strings (ISO, 'YYYY-MM-DD HH:MM UTC', ...)."""
        if not value:
            return None
        raw = str(value).strip().replace("Z", "+00:00")
        for fmt in (None, "%Y-%m-%d %H:%M UTC", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.datetime.fromisoformat(raw) if fmt is None else datetime.datetime.strptime(raw, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                return dt
            except Exception:
                continue
        return None

    @Property(str, notify=licenseChanged)
    def licenseCountdownText(self) -> str:
        """Days/hours until the license expires, or 'Perpetual' when timeless."""
        expiry = self._parse_expiry(self.lic.current_state.expires_at)
        if expiry is None:
            return "Perpetual"
        remaining = max(0.0, (expiry - datetime.datetime.now(datetime.timezone.utc)).total_seconds())
        days = int(remaining // 86400)
        hours = int((remaining % 86400) // 3600)
        return f"{days}d {hours:02d}h"

    @Property(bool, notify=licenseChanged)
    def licenseIsPerpetual(self) -> bool:
        return self._parse_expiry(self.lic.current_state.expires_at) is None

    @Property(int, notify=licenseChanged)
    def trialDaysRemaining(self) -> int:
        details = getattr(self.lic, "trial_details", {})
        if not details:
            details = self.lic.evaluate_trial_detailed()
        return details.get("days_remaining", 0)

    @Property(int, notify=licenseChanged)
    def trialHoursRemaining(self) -> int:
        details = getattr(self.lic, "trial_details", {})
        if not details:
            details = self.lic.evaluate_trial_detailed()
        return details.get("hours_remaining", 0)

    @Property(str, notify=licenseChanged)
    def trialFormattedTime(self) -> str:
        details = getattr(self.lic, "trial_details", {})
        if not details:
            details = self.lic.evaluate_trial_detailed()
        days = details.get("days_remaining", 0)
        hours = details.get("hours_remaining", 0)
        return f"{days}d {hours}h"

    @Property(str, notify=licenseChanged)
    def trialExpiresAt(self) -> str:
        details = getattr(self.lic, "trial_details", {})
        if not details:
            details = self.lic.evaluate_trial_detailed()
        return details.get("expires_at", "N/A")

    @Property(bool, notify=licenseChanged)
    def isNetworkTimeSynced(self) -> bool:
        details = getattr(self.lic, "trial_details", {})
        if not details:
            details = self.lic.evaluate_trial_detailed()
        return details.get("is_net_synced", False)

    @Slot()
    def refreshTrialStatus(self):
        """Re-checks trial status against the network."""
        def _task():
            return self.lic.evaluate_trial_detailed()

        def _on_success(details):
            self.licenseChanged.emit()
            if details.get("is_net_synced"):
                self.toast.emit("success", f"Trial status verified from server ({details.get('days_remaining')}d {details.get('hours_remaining')}h remaining)")
            else:
                self.toast.emit("info", "Trial evaluated using local clock (server unreachable)")

        self.thread_pool.start(Worker(_task, on_success=_on_success))

    @Property(str, constant=True)
    def appVersion(self) -> str:
        return "v2.0.1"

    # =============================================================
    # Internationalization / Language Preference (en / fr only)
    # =============================================================

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        settings = QSettings("OlgaPlus", "olga+")
        val = settings.value("language", "")
        if not val:
            settings_old = QSettings("Bilnov", "BilnovGallery")
            val = settings_old.value("language", "en")
        return str(val or "en")

    @Slot(str)
    def saveLanguagePreference(self, lang: str):
        if lang in ["en", "fr"]:
            settings = QSettings("OlgaPlus", "olga+")
            current = str(settings.value("language", ""))
            if current != lang:
                settings.setValue("language", lang)
                self.languageChanged.emit()

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

    @Property("QVariant", notify=libraryItemsChanged)
    def librarySubcategories(self) -> List[str]:
        try:
            return self.lib.get_subcategories()
        except Exception:
            return []

    @Slot(str, result="QVariant")
    def getSubcategories(self, category: str = "") -> List[str]:
        try:
            return self.lib.get_subcategories(category)
        except Exception:
            return []

    @Property(str, constant=True)
    def dataDir(self) -> str:
        return str(DATA_DIR)

    # =============================================================
    # Licensing Slots
    # =============================================================

    @Slot(str)
    @Slot(str, str, str, str, str)
    def activateLicense(self, key: str, name: str = "", email: str = "", phone: str = "", address: str = ""):
        """Invokes initial activation endpoint POST /api/v1/license/activate."""
        def _task():
            res = self.lic.activate_license(key, name, email, phone, address, lang=self.language)
            # Refresh the cached trial countdown immediately so every QML
            # binding (trial + license) updates as soon as the key is entered,
            # instead of waiting for the deferred application restart.
            try:
                self.lic.evaluate_trial_detailed(use_network=False)
            except Exception:
                logger.exception("Immediate trial countdown refresh failed after activation")
            return res

        def _on_success(res):
            success, msg = res
            self.licenseChanged.emit()
            self.activationResult.emit(success, msg)
            if success:
                target_label = f"Welcome, {name}." if name else "Workstation activated."
                self.toast.emit("success", f"Activation successful! {target_label}")
                self.loadLibrary()
                self.loadCategories()
                QTimer.singleShot(1500, self._restart_application)
            else:
                self.toast.emit("error", f"Activation error: {msg}")

        def _on_error(exc):
            err_msg = str(exc)
            self.licenseChanged.emit()
            self.activationResult.emit(False, err_msg)
            self.toast.emit("error", f"Activation failed: {err_msg}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

    def _restart_application(self) -> None:
        """Restarts the application process (used after a successful activation)."""
        from PySide6.QtCore import QCoreApplication, QProcess

        if getattr(sys, "frozen", False):
            program = sys.executable
            arguments = sys.argv[1:]
            workdir = os.path.dirname(sys.executable) or os.getcwd()
        else:
            program = sys.executable
            main_script = str(Path(__file__).resolve().parents[2] / "main.py")
            arguments = [main_script] + sys.argv[1:]
            workdir = str(Path(main_script).parent)

        if QProcess.startDetached(program, arguments, workdir):
            QCoreApplication.quit()
        else:
            logger.error("Restart failed: could not start a new application process")

    @Slot()
    def verifyLicense(self):
        """Verifies license with handshake POST /api/v1/license/verify with offline grace check."""
        def _task():
            return self.lic.verify_license(lang=self.language)

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
            return self.lic.heartbeat(lang=self.language)

        def _on_success(res):
            success, msg = res
            self.licenseChanged.emit()
            if not success:
                self.toast.emit("error", f"License Alert: {msg}")

        self.thread_pool.start(Worker(_task, on_success=_on_success))

    @Slot(str, str, str, str)
    def registerClientProfile(self, name: str, email: str, phone: str, address: str = ""):
        """Client profile creation POST /api/v1/client/profile (waits for admin license key)."""
        def _task():
            return self.lic.register_client_profile(name, email, phone, address, lang=self.language)

        def _on_success(res):
            success, msg = res
            self.clientProfileResult.emit(success, msg)
            if success:
                self.toast.emit("success", msg)
            else:
                self.toast.emit("error", msg)

        def _on_error(exc):
            self.clientProfileResult.emit(False, str(exc))
            self.toast.emit("error", f"Registration failed: {exc}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

    @Slot(str)
    def checkClientStatus(self, query: str):
        """Client license/profile status lookup GET /api/v1/client/status?query=..."""
        def _task():
            return self.lic.query_client_status(query, lang=self.language)

        def _on_success(res):
            success, msg, data = res
            status_code = str(data.get("status_code") or ("OK" if success else "ERROR"))
            license_key = str(data.get("license_key") or "")
            self.clientStatusResult.emit(success, status_code, msg, license_key)
            if success:
                self.toast.emit("info", msg)
            else:
                self.toast.emit("error", msg)

        def _on_error(exc):
            self.clientStatusResult.emit(False, "ERROR", str(exc), "")
            self.toast.emit("error", f"Status check failed: {exc}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

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

    # =============================================================
    # Add Item to Library (images + article name + SketchUp files)
    # =============================================================

    itemAdded = Signal(bool, str)

    @Slot(result="QVariantList")
    def pickImages(self) -> list:
        """Opens a multi-select image picker. Returns absolute local paths (order preserved)."""
        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            None,
            "Select Images",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.gif)",
        )
        return [f for f in files if f]

    @Slot(result="QVariantList")
    def pickModelFiles(self) -> list:
        """Opens a multi-select picker with no file-type restriction on model uploads."""
        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            None,
            "Select Model Files",
            "",
            "All Files (*)",
        )
        return [f for f in files if f]

    @Slot(str, result=str)
    def toFileUrl(self, path: str) -> str:
        return QUrl.fromLocalFile(path).toString() if path else ""

    @Slot(str, "QVariantList", "QVariantList", str)
    @Slot(str, "QVariantList", "QVariantList", str, str)
    def addLibraryItem(self, title: str, images: list, models: list, category: str = "", subcategory: str = ""):
        """Copies images (first = thumbnail) and model files into a new article folder in storage."""
        img_list = [str(p) for p in (images or [])]
        model_list = [str(p) for p in (models or [])]

        def _task():
            return self.lib.add_item(title, img_list, model_list, category, subcategory)

        def _on_success(res):
            self.itemAdded.emit(True, res.get("folder_path", ""))
            self.toast.emit("success", f"\"{res.get('title', title)}\" added to your library")
            self.loadLibrary()
            self.loadCategories()

        def _on_error(exc):
            self.itemAdded.emit(False, str(exc))
            self.toast.emit("error", f"Could not add item: {exc}")

        self.thread_pool.start(Worker(_task, on_success=_on_success, on_error=_on_error))

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

    # =============================================================
    # Data Management (Export & Import)
    # =============================================================

    @Slot(str, result=bool)
    def exportData(self, target_path: str = "") -> bool:
        """
        Exports 3D models metadata, categories tree, user preferences,
        and licensing status to a portable JSON backup file.
        """
        import datetime
        import json
        from PySide6.QtWidgets import QFileDialog

        file_path = target_path.strip()
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Export Bilnov Gallery Data",
                "bilnov_gallery_backup.json",
                "JSON Files (*.json);;All Files (*.*)",
            )

        if not file_path:
            return False

        try:
            # 1. Collect library scan
            scan_res = self.lib.scan_library()
            items = scan_res.get("items", [])
            categories = self.lib.load_categories_tree()

            # 2. Collect preferences
            settings = QSettings("Bilnov", "BilnovGallery")
            lang = str(settings.value("language", "en"))

            # 3. Collect license state
            trial_data = self.lic.get_or_create_trial()

            backup_payload = {
                "schema_version": "1.1.0",
                "app": "olga+",
                "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "preferences": {
                    "language": lang,
                },
                "device_id": self.lic.device_id,
                "trial": trial_data,
                "license": {
                    "is_licensed": self.lic.current_state.is_valid,
                    "status_code": self.lic.current_state.status_code,
                    "customer_name": self.lic.current_state.customer_name,
                    "customer_email": self.lic.current_state.customer_email,
                    "customer_phone": self.lic.current_state.customer_phone,
                    "expires_at": self.lic.current_state.expires_at,
                },
                "total_models": len(items),
                "categories": categories,
                "models": items,
            }

            dest = Path(file_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(backup_payload, f, indent=2, ensure_ascii=False)

            self.toast.emit("success", f"Successfully exported {len(items)} models to {dest.name}")
            return True
        except Exception as e:
            self.toast.emit("error", f"Export failed: {str(e)}")
            return False

    @Slot(str, result=bool)
    def importData(self, source_path: str = "") -> bool:
        """
        Imports 3D model files (.skp, .obj, .fbx, .blend, .glb, .stl, etc.), archives (.zip),
        asset folders, or backup JSON files directly into the ./data library.
        """
        import json
        import shutil
        import zipfile
        from datetime import datetime
        from PySide6.QtWidgets import QFileDialog

        raw_path = source_path.strip() if source_path else ""
        selected_files = []

        if not raw_path:
            files, _ = QFileDialog.getOpenFileNames(
                None,
                "Import Assets or Backups into Bilnov Gallery",
                "",
                "All Files (*)",
            )
            selected_files = [Path(f) for f in files if f.strip()]
        else:
            p = Path(raw_path)
            if p.exists():
                selected_files = [p]

        if not selected_files:
            return False

        # If a single JSON backup file is selected
        if len(selected_files) == 1 and selected_files[0].is_file() and selected_files[0].suffix.lower() == ".json":
            try:
                with open(selected_files[0], "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and ("models" in data or "preferences" in data or "license" in data):
                    prefs = data.get("preferences", {})
                    if "language" in prefs and prefs["language"] in ["en", "fr"]:
                        self.saveLanguagePreference(prefs["language"])

                    models = data.get("models", [])
                    restored_count = 0
                    for item in models:
                        folder_rel = item.get("folder_path")
                        if folder_rel:
                            folder_abs = DATA_DIR / folder_rel
                            if folder_abs.exists() and folder_abs.is_dir():
                                meta_file = folder_abs / "metadata.json"
                                meta_content = {
                                    "title": item.get("title", folder_abs.name),
                                    "category": item.get("category", "Uncategorized"),
                                    "description": item.get("description", ""),
                                    "tags": item.get("tags", []),
                                    "author": item.get("author", "Bilnov"),
                                    "updated_at": item.get("updated_at", ""),
                                }
                                try:
                                    with open(meta_file, "w", encoding="utf-8") as mf:
                                        json.dump(meta_content, mf, indent=2, ensure_ascii=False)
                                    restored_count += 1
                                except Exception:
                                    pass
                    self.loadLibrary()
                    self.loadCategories()
                    self.toast.emit("success", f"Backup restored! {restored_count} item metadata records updated.")
                    return True
            except Exception:
                pass

        # Import 3D model files, archives, and directories into ./data/Imported/
        imported_dir = DATA_DIR / "Imported"
        imported_dir.mkdir(parents=True, exist_ok=True)

        imported_count = 0
        IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

        try:
            for item_path in selected_files:
                if not item_path.exists():
                    continue

                if item_path.is_dir():
                    # Direct folder import
                    target_folder_name = item_path.name
                    target_folder = imported_dir / target_folder_name
                    counter = 1
                    while target_folder.exists():
                        target_folder = imported_dir / f"{target_folder_name}_{counter}"
                        counter += 1
                    shutil.copytree(item_path, target_folder)
                    meta_path = target_folder / "meta.json"
                    if not meta_path.exists():
                        meta = {
                            "title": target_folder_name.replace("_", " ").replace("-", " ").title(),
                            "category": "Imported",
                            "imported_at": datetime.now().isoformat(),
                        }
                        with open(meta_path, "w", encoding="utf-8") as mf:
                            json.dump(meta, mf, indent=2, ensure_ascii=False)
                    imported_count += 1

                elif item_path.suffix.lower() == ".zip":
                    # Zip archive import: extract contents into article folder
                    item_stem = item_path.stem
                    target_folder = imported_dir / item_stem
                    counter = 1
                    while target_folder.exists():
                        target_folder = imported_dir / f"{item_stem}_{counter}"
                        counter += 1
                    target_folder.mkdir(parents=True, exist_ok=True)

                    with zipfile.ZipFile(item_path, "r") as zf:
                        zf.extractall(target_folder)

                    meta_path = target_folder / "meta.json"
                    if not meta_path.exists():
                        meta = {
                            "title": item_stem.replace("_", " ").replace("-", " ").title(),
                            "category": "Imported",
                            "source_archive": item_path.name,
                            "imported_at": datetime.now().isoformat(),
                        }
                        with open(meta_path, "w", encoding="utf-8") as mf:
                            json.dump(meta, mf, indent=2, ensure_ascii=False)
                    imported_count += 1

                elif item_path.suffix.lower() not in IMAGE_EXTS:
                    # Any other file type is imported as a model file (no file-type restriction)
                    item_stem = item_path.stem
                    clean_title = item_stem.replace("_", " ").replace("-", " ").title()
                    target_folder = imported_dir / item_stem
                    counter = 1
                    while target_folder.exists():
                        target_folder = imported_dir / f"{item_stem}_{counter}"
                        counter += 1
                    target_folder.mkdir(parents=True, exist_ok=True)

                    # Create model subdirectory and copy model
                    model_dir = target_folder / "model"
                    model_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item_path, model_dir / item_path.name)

                    # Look for companion materials (.mtl) or preview images (.png, .jpg) in the same directory
                    parent_dir = item_path.parent
                    for sibling in parent_dir.iterdir():
                        if sibling.is_file() and sibling.name != item_path.name:
                            sib_ext = sibling.suffix.lower()
                            if sibling.stem.startswith(item_stem):
                                if sib_ext in IMAGE_EXTS:
                                    shutil.copy2(sibling, target_folder / sibling.name)
                                elif sib_ext in {".mtl", ".bin"}:
                                    shutil.copy2(sibling, model_dir / sibling.name)

                    meta = {
                        "title": clean_title,
                        "category": "Imported",
                        "subcategory": "3D Models",
                        "model_file": item_path.name,
                        "imported_at": datetime.now().isoformat(),
                    }
                    with open(target_folder / "meta.json", "w", encoding="utf-8") as mf:
                        json.dump(meta, mf, indent=2, ensure_ascii=False)
                    imported_count += 1

                elif item_path.suffix.lower() in IMAGE_EXTS:
                    # Image file import
                    item_stem = item_path.stem
                    target_folder = imported_dir / item_stem
                    counter = 1
                    while target_folder.exists():
                        target_folder = imported_dir / f"{item_stem}_{counter}"
                        counter += 1
                    target_folder.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item_path, target_folder / item_path.name)
                    meta = {
                        "title": item_stem.replace("_", " ").replace("-", " ").title(),
                        "category": "Imported",
                        "imported_at": datetime.now().isoformat(),
                    }
                    with open(target_folder / "meta.json", "w", encoding="utf-8") as mf:
                        json.dump(meta, mf, indent=2, ensure_ascii=False)
                    imported_count += 1

            self.loadLibrary()
            self.loadCategories()

            if imported_count > 0:
                self.toast.emit("success", f"Successfully imported {imported_count} asset(s) into the library!")
                return True
            else:
                self.toast.emit("error", "No valid 3D assets or files found to import.")
                return False

        except Exception as e:
            logger.error("Import failed: %s", e)
            self.toast.emit("error", f"Import failed: {str(e)}")
            return False

    @Slot(result=bool)
    def importFolder(self) -> bool:
        """
        Opens a directory picker to import an entire folder of 3D assets into the library.
        """
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(
            None,
            "Select 3D Asset Folder to Import into Library",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if not dir_path:
            return False
        return self.importData(dir_path)

