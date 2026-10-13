"""
Unit tests for olga+ rebranding, QML structure, and licensing adjustments.
"""

import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestOlgaPlus(unittest.TestCase):
    def test_app_naming_and_config(self):
        import config
        from desktop import main as desktop_main

        self.assertIn("olga+", config.__doc__)
        self.assertIn("OlgaPlus", str(config.USER_CACHE_DIR))

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

    def test_storage_hierarchy_depth_3_enforced(self):
        import tempfile
        import shutil
        from desktop.backend.library import LibraryManager

        tmp_dir = Path(tempfile.mkdtemp(prefix="olga_test_lib_"))
        try:
            # Depth 2 item: Category / AssetName (MUST BE IGNORED)
            d2_dir = tmp_dir / "Category1" / "AssetDepth2"
            d2_dir.mkdir(parents=True)
            (d2_dir / "thumb.jpg").write_bytes(b"dummy_img")
            (d2_dir / "model").mkdir()
            (d2_dir / "model" / "asset.skp").write_bytes(b"dummy_skp")

            # Depth 3 item: Category / Subcategory / AssetName (MUST BE SCANNED)
            d3_dir = tmp_dir / "Category1" / "Subcategory1" / "AssetDepth3"
            d3_dir.mkdir(parents=True)
            (d3_dir / "thumb.jpg").write_bytes(b"dummy_img")
            (d3_dir / "model").mkdir()
            (d3_dir / "model" / "asset.skp").write_bytes(b"dummy_skp")

            mgr = LibraryManager(base_dir=tmp_dir)
            scan = mgr.scan_library()

            # Only depth 3 item should be returned
            titles = [it["title"] for it in scan["items"]]
            self.assertIn("AssetDepth3", titles)
            self.assertNotIn("AssetDepth2", titles)
            self.assertEqual(len(scan["items"]), 1)
            self.assertEqual(scan["items"][0]["category"], "Category1")
            self.assertEqual(scan["items"][0]["subcategory"], "Subcategory1")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_articles_without_model_are_hidden(self):
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
            self.assertNotIn("NoModel", titles)
            self.assertEqual(len(scan["items"]), 1)
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

            res = mgr.add_item(
                title="Nordic Armchair",
                image_paths=[str(src_img)],
                model_paths=[str(src_model)],
                category="Furniture",
                subcategory="Chairs",
            )

            expected_path = tmp_dir / "Furniture" / "Chairs" / "Nordic Armchair"
            self.assertTrue(expected_path.exists())
            self.assertTrue((expected_path / "image_1.jpg").exists())
            self.assertTrue((expected_path / "model" / "test_model.skp").exists())
            self.assertTrue((expected_path / "meta.json").exists())

            # Verify it is scanned
            scan = mgr.scan_library()
            self.assertEqual(len(scan["items"]), 1)
            self.assertEqual(scan["items"][0]["title"], "Nordic Armchair")
            self.assertEqual(scan["items"][0]["category"], "Furniture")
            self.assertEqual(scan["items"][0]["subcategory"], "Chairs")

            # Verify get_subcategories discovers 'Chairs'
            subcats = mgr.get_subcategories()
            self.assertIn("Chairs", subcats)
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


if __name__ == "__main__":
    unittest.main()

