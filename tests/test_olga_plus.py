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

    def test_qml_sidebar_removed_and_settings_icon(self):
        main_qml = (ROOT_DIR / "desktop" / "qml" / "main.qml").read_text(encoding="utf-8")
        header_qml = (ROOT_DIR / "desktop" / "qml" / "components" / "HeaderBar.qml").read_text(encoding="utf-8")
        settings_qml = (ROOT_DIR / "desktop" / "qml" / "views" / "SettingsView.qml").read_text(encoding="utf-8")

        # SidebarNav must not be instantiated in main.qml
        self.assertNotIn("SidebarNav {", main_qml)

        # Title must be olga+
        self.assertIn('title: "olga+ • 3D Asset Platform"', main_qml)

        # HeaderBar must have toggleSettings signal and cog icon button
        self.assertIn("signal toggleSettings()", header_qml)
        self.assertIn("signal backToLibrary()", header_qml)
        self.assertIn("Icons.cog", header_qml)

        # SettingsView must NOT contain license details widget (licenseCol / device fingerprint)
        self.assertNotIn("id: licenseCol", settings_qml)
        self.assertNotIn("field_device_id", settings_qml)

        # SettingsView must NOT contain client phone or address inputs
        self.assertNotIn("id: phoneInput", settings_qml)
        self.assertNotIn("id: addrInput", settings_qml)

        # SettingsView must NOT contain developer contact numbers pane (appInfoCol)
        self.assertNotIn("id: appInfoCol", settings_qml)
        self.assertNotIn("+213775189229", settings_qml)
        self.assertNotIn("+213673782115", settings_qml)

    def test_i18n_strings(self):
        i18n_content = (ROOT_DIR / "desktop" / "qml" / "I18n.qml").read_text(encoding="utf-8")

        # Check English strings
        self.assertIn('"app_title": "olga+"', i18n_content)
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
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
