"""
Unit tests for orga+ rebranding, QML structure, and licensing adjustments.
"""

import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestOrgaPlus(unittest.TestCase):
    def test_app_naming_and_config(self):
        import config
        from desktop import main as desktop_main

        self.assertIn("orga+", config.__doc__)
        self.assertIn("OrgaPlus", str(config.USER_CACHE_DIR))

    def test_qml_header_buttons_and_settings_removed(self):
        main_qml = (ROOT_DIR / "desktop" / "qml" / "main.qml").read_text(encoding="utf-8")
        header_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "HeaderBar.qml").read_text(encoding="utf-8")
        lib_qml = (ROOT_DIR / "desktop" / "qml" / "views" / "LibraryView.qml").read_text(encoding="utf-8")
        license_dialog_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "LicenseDialog.qml").read_text(encoding="utf-8")

        # SidebarNav and SettingsView must not be in main.qml
        self.assertNotIn("SidebarNav {", main_qml)
        self.assertNotIn("SettingsView {", main_qml)
        self.assertFalse((ROOT_DIR / "desktop" / "qml" / "views" / "SettingsView.qml").exists())

        # Title must be orga+ only
        self.assertIn('title: "orga+"', main_qml)

        # HeaderBar must have openLicense signal, license button, EN/FR language toggle,
        # filter button and add item button
        self.assertIn("signal openLicense()", header_qml)
        self.assertIn("signal addItemRequested()", header_qml)
        self.assertIn("signal filterChanged(", header_qml)
        self.assertIn("Icons.key", header_qml)
        self.assertIn("Icons.filter", header_qml)
        self.assertIn('I18n.currentLanguage === "fr" ? "EN" : "FR"', header_qml)
        self.assertIn("id: filterPopup", header_qml)

        # Settings cog icon and toggleSettings must be removed
        self.assertNotIn("Icons.cog", header_qml)
        self.assertNotIn("signal toggleSettings()", header_qml)

        # LibraryView control bar (search / reload / add / open folder) must be removed
        self.assertNotIn("id: libFilterInput", lib_qml)
        self.assertNotIn("id: reloadMouse", lib_qml)
        self.assertNotIn("id: addItemMouse", lib_qml)

        # Category filter dropdown must be removed from LibraryView
        self.assertNotIn("id: catMenu", lib_qml)

        # LicenseDialog must contain license key input, activation status, and contact phone numbers
        self.assertIn("id: keyInput", license_dialog_qml)
        self.assertIn("Bridge.activateLicense", license_dialog_qml)
        self.assertIn("+213775189229", license_dialog_qml)
        self.assertIn("+213673782115", license_dialog_qml)

    def test_i18n_strings(self):
        i18n_content = (ROOT_DIR / "desktop" / "qml" / "I18n.qml").read_text(encoding="utf-8")

        # Check English strings
        self.assertIn('"app_title": "orga+"', i18n_content)
        self.assertIn('"header_gallery_title": "Library"', i18n_content)
        self.assertIn('"nav_settings": "Settings"', i18n_content)
        self.assertIn('"back_to_library": "Back to Library"', i18n_content)

        # Check French strings
        self.assertIn('"header_gallery_title": "Bibliothèque"', i18n_content)
        self.assertIn('"nav_settings": "Paramètres"', i18n_content)
        self.assertIn('"back_to_library": "Retour à la bibliothèque"', i18n_content)

    def test_icon_assets_exist(self):
        assets = ROOT_DIR / "desktop" / "assets"
        self.assertTrue((assets / "icon.png").exists())
        self.assertTrue((assets / "icon.ico").exists())
        self.assertTrue((assets / "icon.icns").exists())
        self.assertTrue((ROOT_DIR / "icon.png").exists())
        self.assertTrue((ROOT_DIR / "icon.ico").exists())

    def test_dynamic_scanning_arbitrary_depths_and_multi_items(self):
        """Test that orga+ dynamically discovers assets across any folder depth (depth 2, 3, 5, 6)
        and supports multi-item subcategory folders."""
        import tempfile
        import shutil
        from desktop.backend.library import LibraryManager

        tmp_dir = Path(tempfile.mkdtemp(prefix="orga_test_lib_"))
        try:
            # 1. Depth 2 item: Category / AssetName
            d2_dir = tmp_dir / "Lighting" / "DeskLamp"
            d2_dir.mkdir(parents=True)
            (d2_dir / "thumb.jpg").write_bytes(b"dummy_img")
            (d2_dir / "model").mkdir()
            (d2_dir / "model" / "lamp.skp").write_bytes(b"dummy_skp")

            # 2. Depth 3 item: Category / Subcategory / AssetName
            d3_dir = tmp_dir / "Furniture" / "Chairs" / "OfficeChair"
            d3_dir.mkdir(parents=True)
            (d3_dir / "thumb.jpg").write_bytes(b"dummy_img")
            (d3_dir / "model").mkdir()
            (d3_dir / "model" / "chair.skp").write_bytes(b"dummy_skp")

            # 3. Depth 5 item: Architecture / Residential / Houses / Exteriors / Villa19492
            d5_dir = tmp_dir / "Architecture" / "Residential" / "Houses" / "Exteriors" / "Villa19492"
            d5_dir.mkdir(parents=True)
            (d5_dir / "render.jpg").write_bytes(b"dummy_img")
            (d5_dir / "model").mkdir()
            (d5_dir / "model" / "villa.skp").write_bytes(b"dummy_skp")

            # 4. Multi-item subcategory folder (no asset folder): Scenes / Commercial / Offices
            multi_dir = tmp_dir / "Scenes" / "Commercial" / "Offices"
            multi_dir.mkdir(parents=True)
            (multi_dir / "Executive_Suite.jpg").write_bytes(b"dummy_img")
            (multi_dir / "Boardroom_Modern.jpg").write_bytes(b"dummy_img")
            (multi_dir / "model").mkdir()
            (multi_dir / "model" / "Executive_Suite.rar").write_bytes(b"dummy_rar")
            (multi_dir / "model" / "Boardroom_Modern.skp").write_bytes(b"dummy_skp")

            mgr = LibraryManager(base_dir=tmp_dir)
            scan = mgr.scan_library()

            # All 5 items across all depths must be discovered
            self.assertEqual(len(scan["items"]), 5)
            titles = [it["title"] for it in scan["items"]]
            self.assertIn("DeskLamp", titles)
            self.assertIn("OfficeChair", titles)
            self.assertIn("Villa19492", titles)
            self.assertIn("Executive Suite", titles)
            self.assertIn("Boardroom Modern", titles)

            # Check category & subcategory resolutions
            by_title = {it["title"]: it for it in scan["items"]}
            self.assertEqual(by_title["DeskLamp"]["category"], "Lighting")
            self.assertEqual(by_title["OfficeChair"]["category"], "Furniture")
            self.assertEqual(by_title["OfficeChair"]["subcategory"], "Chairs")
            self.assertEqual(by_title["Villa19492"]["category"], "Architecture")
            self.assertEqual(by_title["Villa19492"]["subcategory"], "Residential / Houses / Exteriors")
            self.assertEqual(by_title["Executive Suite"]["category"], "Scenes")
            self.assertEqual(by_title["Executive Suite"]["subcategory"], "Commercial / Offices")
            self.assertEqual(by_title["Boardroom Modern"]["category"], "Scenes")
            self.assertEqual(by_title["Boardroom Modern"]["subcategory"], "Commercial / Offices")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_articles_without_model_are_shown(self):
        import tempfile
        import shutil
        from desktop.backend.library import LibraryManager

        tmp_dir = Path(tempfile.mkdtemp(prefix="olga_test_nomodel_"))
        try:
            with_model = tmp_dir / "Architect" / "Furniture" / "WithModel"
            with_model.mkdir(parents=True)
            (with_model / "image_1.jpg").write_bytes(b"img")
            (with_model / "model").mkdir()
            (with_model / "model" / "chair.skp").write_bytes(b"skp")

            no_model = tmp_dir / "Architect" / "Furniture" / "NoModel"
            no_model.mkdir(parents=True)
            (no_model / "image_1.jpg").write_bytes(b"img")

            mgr = LibraryManager(base_dir=tmp_dir)
            scan = mgr.scan_library()

            titles = [it["title"] for it in scan["items"]]
            self.assertIn("WithModel", titles)
            self.assertIn("NoModel", titles)
            self.assertEqual(len(scan["items"]), 2)

            by_title = {it["title"]: it for it in scan["items"]}
            self.assertTrue(by_title["WithModel"]["has_model"])
            self.assertFalse(by_title["NoModel"]["has_model"])
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_add_item_creates_depth_3(self):
        import tempfile
        import shutil
        from desktop.backend.library import LibraryManager

        tmp_dir = Path(tempfile.mkdtemp(prefix="olga_test_add_"))
        try:
            mgr = LibraryManager(base_dir=tmp_dir)

            src_img = tmp_dir / "test_thumb.jpg"
            src_img.write_bytes(b"dummy_jpeg_bytes")
            src_model = tmp_dir / "test_model.skp"
            src_model.write_bytes(b"dummy_model_bytes")

            # 1. Default: imports using absolute locations (no file copying)
            res = mgr.add_item(
                title="Nordic Armchair",
                image_paths=[str(src_img)],
                model_paths=[str(src_model)],
                category="Furniture",
                subcategory="Chairs",
                copy_files=False,
            )

            expected_path = tmp_dir / "Furniture" / "Chairs" / "Nordic Armchair"
            self.assertTrue(expected_path.exists())
            self.assertTrue((expected_path / "meta.json").exists())
            # Files are NOT copied to save disk space
            self.assertFalse((expected_path / "image_1.jpg").exists())
            self.assertFalse((expected_path / "model").exists())

            # Verify it is scanned
            scan = mgr.scan_library()
            self.assertEqual(len(scan["items"]), 1)
            self.assertEqual(scan["items"][0]["title"], "Nordic Armchair")
            self.assertEqual(scan["items"][0]["category"], "Furniture")
            self.assertEqual(scan["items"][0]["subcategory"], "Chairs")
            self.assertTrue(scan["items"][0]["has_model"])

            # Verify get_subcategories discovers 'Chairs'
            subcats = mgr.get_subcategories()
            self.assertIn("Chairs", subcats)

            # 2. Test with copy_files=True
            res_copied = mgr.add_item(
                title="Copied Chair",
                image_paths=[str(src_img)],
                model_paths=[str(src_model)],
                category="Furniture",
                subcategory="Chairs",
                copy_files=True,
            )
            copied_path = tmp_dir / "Furniture" / "Chairs" / "Copied Chair"
            self.assertTrue(copied_path.exists())
            self.assertTrue((copied_path / "image_1.jpg").exists())
            self.assertTrue((copied_path / "model" / "test_model.skp").exists())
            self.assertTrue((copied_path / "meta.json").exists())
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_add_item_dialog_job_dropdown_and_category(self):
        add_dialog_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "AddItemDialog.qml").read_text(encoding="utf-8")

        # Verify category field is replaced with job dropdown
        self.assertIn("selectedJob", add_dialog_qml)
        self.assertIn("jobOptions", add_dialog_qml)
        self.assertIn('"architect"', add_dialog_qml)
        self.assertIn('"graphiste"', add_dialog_qml)
        self.assertIn('"video maker"', add_dialog_qml)
        self.assertIn("jobMenu", add_dialog_qml)
        self.assertIn("jobSelectBox", add_dialog_qml)

        # Verify the category field is prefilled from the storage folder taxonomy
        # and that the user can still type a custom category.
        self.assertIn("Bridge.predefinedCategories", add_dialog_qml)
        self.assertIn("categoryOptions", add_dialog_qml)
        self.assertIn("categoryMenu", add_dialog_qml)
        self.assertIn("categoryInput", add_dialog_qml)
        self.assertIn("create_new_category", add_dialog_qml)
        self.assertNotIn("subcatMenu", add_dialog_qml)
        self.assertNotIn("Bridge.librarySubcategories", add_dialog_qml)

    def test_predefined_categories_from_storage(self):
        import json
        import tempfile
        from desktop.backend.library import LibraryManager

        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp) / "storage"
            storage.mkdir()
            (storage / "categories.json").write_text(
                json.dumps([
                    {"heading": {"name": "Furniture"}, "subcategories": []},
                    {"heading": {"name": "Kitchen"}, "subcategories": []},
                    {"heading": {"name": "Furniture"}, "subcategories": []},
                ]),
                encoding="utf-8",
            )
            mgr = LibraryManager(base_dir=storage)
            self.assertEqual(mgr.get_predefined_categories(), ["Furniture", "Kitchen"])

    def test_header_bar_import_folder_and_new_job_buttons(self):
        header_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "HeaderBar.qml").read_text(encoding="utf-8")

        # Must have importFolderRequested and createNewJobRequested signals
        self.assertIn("signal importFolderRequested()", header_qml)
        self.assertIn("signal createNewJobRequested()", header_qml)

        # Must have importFolderBtn (icon only) with Icons.folderOpen
        self.assertIn("id: importFolderBtn", header_qml)
        self.assertIn("Icons.folderOpen", header_qml)
        self.assertIn("root.importFolderRequested()", header_qml)

        # Must have dynamic job options and "+ New Job" in filterPopup
        self.assertIn("getFilterJobOptions()", header_qml)
        self.assertIn("newJobFilterBtn", header_qml)
        self.assertIn("newJobFilterMouse", header_qml)
        self.assertIn("root.createNewJobRequested()", header_qml)

    def test_new_job_dialog_structure(self):
        job_dialog_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "NewJobDialog.qml").read_text(encoding="utf-8")

        self.assertIn("parent: Overlay.overlay", job_dialog_qml)
        self.assertIn("signal jobCreated(", job_dialog_qml)
        self.assertIn("id: jobNameInput", job_dialog_qml)
        self.assertIn("Bridge.createJob(", job_dialog_qml)
        self.assertIn("openForTarget(", job_dialog_qml)

    def test_import_folder_dialog_structure(self):
        import_dialog_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "ImportFolderDialog.qml").read_text(encoding="utf-8")
        add_item_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "AddItemDialog.qml").read_text(encoding="utf-8")

        self.assertIn("signal createNewJobRequested()", import_dialog_qml)
        self.assertIn("browseFolder()", import_dialog_qml)
        self.assertIn("Bridge.pickFolder()", import_dialog_qml)
        self.assertIn("Bridge.importFolder(", import_dialog_qml)
        self.assertIn("categoryInput", import_dialog_qml)
        self.assertIn("jobSelectBox", import_dialog_qml)

        # Dropdowns must have z: 100005 to render above overlay dialogs (which have z ~99997)
        self.assertIn("id: jobMenu\n                        z: 100005", import_dialog_qml)
        self.assertIn("id: categoryMenu\n                        z: 100005", import_dialog_qml)
        self.assertIn("id: jobMenu\n                            z: 100005", add_item_qml)
        self.assertIn("id: categoryMenu\n                            z: 100005", add_item_qml)

        # Dropdowns must have scrollable overflow with capped height
        self.assertIn("implicitHeight: Math.min(220, contentHeight)", import_dialog_qml)
        self.assertIn("implicitHeight: Math.min(220, contentHeight)", add_item_qml)

    def test_library_manager_jobs_and_folder_import(self):
        import tempfile
        import shutil
        from desktop.backend.library import LibraryManager

        tmp_dir = Path(tempfile.mkdtemp(prefix="olga_test_jobs_import_"))
        try:
            mgr = LibraryManager(base_dir=tmp_dir)

            # 1. Test get_jobs returns default jobs
            jobs = mgr.get_jobs()
            job_names = [j["name"] for j in jobs]
            self.assertIn("Architect", job_names)
            self.assertIn("Graphiste", job_names)
            self.assertIn("Video Maker", job_names)

            # 2. Test create_job
            new_job = mgr.create_job("Interior Designer")
            self.assertEqual(new_job["name"], "Interior Designer")
            self.assertTrue((tmp_dir / "Interior Designer").exists())

            # Check that get_jobs now contains Interior Designer
            updated_jobs = mgr.get_jobs()
            updated_names = [j["name"] for j in updated_jobs]
            self.assertIn("Interior Designer", updated_names)

            # 3. Test import_folder with single asset folder
            src_asset_folder = tmp_dir / "my_source_asset"
            src_asset_folder.mkdir()
            (src_asset_folder / "preview.png").write_bytes(b"dummy_png")
            (src_asset_folder / "table.skp").write_bytes(b"dummy_skp")

            import_res = mgr.import_folder(
                src_asset_folder,
                job="Interior Designer",
                category="Tables",
            )
            self.assertEqual(import_res["count"], 1)
            self.assertEqual(import_res["job"], "Interior Designer")
            self.assertEqual(import_res["category"], "Tables")

            # Check files were placed in depth 3: storage / <Job> / <Category> / <Asset>
            imported_asset = tmp_dir / "Interior Designer" / "Tables" / "my_source_asset"
            self.assertTrue(imported_asset.exists())
            self.assertTrue((imported_asset / "meta.json").exists())
            # Default import does not copy files to prevent disk duplication
            self.assertFalse((imported_asset / "image_1.png").exists())
            self.assertFalse((imported_asset / "model").exists())

            # Scan library and verify it appears with correct job and category
            scan = mgr.scan_library(category_filter="Interior Designer", subcategory_filter="Tables")
            self.assertEqual(len(scan["items"]), 1)
            self.assertEqual(scan["items"][0]["category"], "Interior Designer")
            self.assertEqual(scan["items"][0]["subcategory"], "Tables")
            self.assertTrue(scan["items"][0]["has_model"])

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_app_bridge_job_and_folder_import(self):
        from desktop.backend.app_bridge import AppBridge

        bridge = AppBridge()
        # Verify jobOptions returns default jobs
        job_options = bridge.jobOptions
        self.assertGreaterEqual(len(job_options), 3)

        # Verify getJobFolder
        self.assertEqual(bridge.getJobFolder("architect"), "Architect")
        self.assertEqual(bridge.getJobFolder("graphiste"), "Graphiste")

    def test_inno_setup_script_shortcuts_and_tasks(self):
        """Verify that the Inno Setup script exists and configures desktop and taskbar shortcuts."""
        iss_path = ROOT_DIR / "installer" / "orga_plus.iss"
        self.assertTrue(iss_path.exists())
        content = iss_path.read_text(encoding="utf-8")

        # Must configure desktopicon and taskbaricon tasks
        self.assertIn('Name: "desktopicon"', content)
        self.assertIn('Name: "taskbaricon"', content)

        # Must have [Icons] section with conditional Tasks
        self.assertIn('Tasks: desktopicon', content)
        self.assertIn('Tasks: taskbaricon', content)

        # Output filename must be orga+_Setup
        self.assertIn('OutputBaseFilename=orga+_Setup', content)

    def test_app_bridge_create_shortcut_slot(self):
        """Verify that AppBridge exposes createShortcut slot for desktop/taskbar shortcuts."""
        from desktop.backend.app_bridge import AppBridge

        bridge = AppBridge()
        self.assertTrue(hasattr(bridge, "createShortcut"))

    def test_copy_tool_prioritizes_installer(self):
        """Verify that orga+ Copy Tool find_orga_app prioritizes the setup installer."""
        import tempfile
        import shutil
        from tools.orga_copy_tool import find_orga_app

        tmp_dist = Path(tempfile.mkdtemp(prefix="test_dist_"))
        try:
            installer = tmp_dist / "orga+_Setup.exe"
            installer.write_bytes(b"dummy_installer_exe")
            found = find_orga_app(str(installer))
            self.assertEqual(found, installer.resolve())
        finally:
            shutil.rmtree(tmp_dist, ignore_errors=True)

    def test_import_data_no_copy_and_external_location(self):
        """Verify that importing files/folders stores absolute locations in meta.json without copying files."""
        import tempfile
        import shutil
        import json
        from desktop.backend.app_bridge import AppBridge
        from config import DATA_DIR

        bridge = AppBridge()
        tmp_dir = Path(tempfile.mkdtemp(prefix="test_import_data_"))
        try:
            # Create external asset folder
            ext_asset = tmp_dir / "Sofa_Modern"
            ext_asset.mkdir()
            img_file = ext_asset / "sofa.png"
            img_file.write_bytes(b"dummy_png")
            model_file = ext_asset / "sofa.skp"
            model_file.write_bytes(b"dummy_skp")

            # Import folder via importData
            res = bridge.importData(str(ext_asset))
            self.assertTrue(res)

            # Check that imported entry exists in DATA_DIR / Imported
            imported_target = DATA_DIR / "Imported" / "Sofa_Modern"
            self.assertTrue(imported_target.exists())
            meta_path = imported_target / "meta.json"
            self.assertTrue(meta_path.exists())

            # Original files must NOT be copied into imported_target
            self.assertFalse((imported_target / "sofa.png").exists())
            self.assertFalse((imported_target / "sofa.skp").exists())

            # Metadata must contain absolute location of files
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertTrue(meta.get("is_external"))
            self.assertEqual(meta.get("source_dir"), str(ext_asset.resolve()))
            self.assertIn(str(img_file.resolve()), meta.get("images", []))
            self.assertIn(str(model_file.resolve()), meta.get("models", []))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            if (DATA_DIR / "Imported" / "Sofa_Modern").exists():
                shutil.rmtree(DATA_DIR / "Imported" / "Sofa_Modern", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()


