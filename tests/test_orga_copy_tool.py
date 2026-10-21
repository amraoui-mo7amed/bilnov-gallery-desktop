"""
Unit tests for the upgraded orga+ Copy Tool.
Tests model filtering, disk selection, exact limits, zip extraction to /model/,
and auto-copying of the orga+ app.
"""

import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.orga_copy_tool import (
    CopyController,
    CopyItem,
    copy_orga_app,
    find_orga_app,
    has_model,
    human_size,
    list_volumes,
    run_copy,
    safe_extract_zip,
    scan_items,
    select_balanced_mechanism,
    select_exact_count,
    select_fit_disk,
    select_storage_limit,
)


class TestOrgaCopyTool(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="test_copy_tool_"))
        self.src_dir = self.tmp_dir / "library"
        self.src_dir.mkdir()

        # Item 1: Model (.skp) inside model/
        self.item1 = self.src_dir / "Furniture" / "Chairs" / "Office Chair"
        (self.item1 / "model").mkdir(parents=True)
        (self.item1 / "image_1.jpg").write_bytes(b"PREVIEW_1_DATA" * 50)
        (self.item1 / "meta.json").write_text('{"title": "Ergonomic Office Chair"}', encoding="utf-8")
        (self.item1 / "model" / "office_chair.skp").write_bytes(b"SKP_MODEL_BYTES" * 100)

        # Item 2: Zipped model (.zip) inside model/
        self.item2 = self.src_dir / "Architecture" / "Doors" / "Sliding Glass Door"
        (self.item2 / "model").mkdir(parents=True)
        (self.item2 / "preview.png").write_bytes(b"PNG_DATA" * 50)
        (self.item2 / "meta.json").write_text('{"title": "Sliding Glass Door"}', encoding="utf-8")
        zip_p2 = self.item2 / "model" / "door_archive.zip"
        with zipfile.ZipFile(zip_p2, "w") as zf:
            zf.writestr("sliding_door.skp", b"DOOR_SKP_CONTENT" * 100)
            zf.writestr("textures/glass.jpg", b"TEXTURE_DATA" * 50)

        # Item 3: Standalone model file (.fbx) at asset root (no model/ dir in source)
        self.item3 = self.src_dir / "Lighting" / "Lamps" / "Desk Lamp"
        self.item3.mkdir(parents=True)
        (self.item3 / "image_1.jpg").write_bytes(b"LAMP_PREVIEW" * 50)
        (self.item3 / "desk_lamp.fbx").write_bytes(b"FBX_LAMP_BYTES" * 100)

        # Item 4: Asset WITHOUT model (previews only -> MUST BE SKIPPED)
        self.item4 = self.src_dir / "Decor" / "Plants" / "Indoor Plant"
        self.item4.mkdir(parents=True)
        (self.item4 / "image_1.jpg").write_bytes(b"PLANT_PREVIEW" * 50)

        # Dummy app
        self.app_dir = self.tmp_dir / "orga+.app"
        self.app_dir.mkdir()
        (self.app_dir / "Contents").mkdir()
        (self.app_dir / "Contents" / "MacOS").mkdir()
        (self.app_dir / "Contents" / "MacOS" / "orga+").write_bytes(b"APP_EXEC")
        (self.app_dir / "Contents" / "Info.plist").write_text("<plist></plist>", encoding="utf-8")

        # Destination disk
        self.dest_disk = self.tmp_dir / "USB_DRIVE"
        self.dest_disk.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_has_model(self):
        self.assertTrue(has_model(self.item1))
        self.assertTrue(has_model(self.item2))
        self.assertTrue(has_model(self.item3))
        self.assertFalse(has_model(self.item4))

    def test_scan_items_filters_models_only(self):
        items, skipped = scan_items(self.src_dir)
        self.assertEqual(len(items), 3)
        self.assertEqual(skipped, 1)

        titles = [it.title for it in items]
        self.assertIn("Ergonomic Office Chair", titles)
        self.assertIn("Sliding Glass Door", titles)
        self.assertIn("Desk Lamp", titles)
        self.assertNotIn("Indoor Plant", titles)

        # Verify formats
        by_title = {it.title: it for it in items}
        self.assertEqual(by_title["Ergonomic Office Chair"].model_format, "SKP")
        self.assertFalse(by_title["Ergonomic Office Chair"].is_zip)

        self.assertEqual(by_title["Sliding Glass Door"].model_format, "ZIP")
        self.assertTrue(by_title["Sliding Glass Door"].is_zip)

        self.assertEqual(by_title["Desk Lamp"].model_format, "FBX")
        self.assertFalse(by_title["Desk Lamp"].is_zip)

    def test_safe_extract_zip(self):
        zip_p = self.tmp_dir / "test_bundle.zip"
        with zipfile.ZipFile(zip_p, "w") as zf:
            zf.writestr("bundle_root/table.skp", b"TABLE_SKP_DATA")
            zf.writestr("bundle_root/textures/wood.jpg", b"WOOD_DATA")

        target_model = self.tmp_dir / "output_asset" / "model"
        ctrl = CopyController()
        chunks = []
        safe_extract_zip(zip_p, target_model, ctrl, on_chunk=lambda n: chunks.append(n))

        # Check that single root folder was stripped and files sit in model/
        self.assertTrue((target_model / "table.skp").exists())
        self.assertEqual((target_model / "table.skp").read_bytes(), b"TABLE_SKP_DATA")
        self.assertTrue((target_model / "textures" / "wood.jpg").exists())

        # Check that no zip file remains in model/
        self.assertFalse((target_model / "test_bundle.zip").exists())
        self.assertGreater(sum(chunks), 0)

    def test_selection_limits(self):
        items, _ = scan_items(self.src_dir)
        self.assertEqual(len(items), 3)

        # Exact count
        sel_count_1 = select_exact_count(items, 1)
        self.assertEqual(len(sel_count_1), 1)

        sel_count_2 = select_exact_count(items, 2)
        self.assertEqual(len(sel_count_2), 2)

        # Storage limit
        tot = sum(it.total_bytes for it in items)
        sel_storage_all = select_storage_limit(items, tot + 1000)
        self.assertEqual(len(sel_storage_all), 3)

        first_size = items[0].total_bytes
        sel_storage_first = select_storage_limit(items, first_size + 10)
        self.assertEqual(len(sel_storage_first), 1)

        # Fit disk
        sel_fit = select_fit_disk(items, disk_free_bytes=tot + 600 * 1024 * 1024)
        self.assertEqual(len(sel_fit), 3)

    def test_copy_orga_app(self):
        ctrl = CopyController()
        chunks = []
        copied_bytes = copy_orga_app(
            self.app_dir,
            self.dest_disk,
            ctrl,
            on_chunk=lambda n: chunks.append(n),
            log_cb=lambda m: None,
        )

        dest_app = self.dest_disk / "orga+.app"
        self.assertTrue(dest_app.exists())
        self.assertTrue((dest_app / "Contents" / "MacOS" / "orga+").exists())
        self.assertTrue((dest_app / "Contents" / "Info.plist").exists())
        self.assertGreater(copied_bytes, 0)

    def test_run_copy_end_to_end(self):
        items, _ = scan_items(self.src_dir)
        ctrl = CopyController()
        progress_calls = []

        def on_prog(snap, item, fname):
            progress_calls.append((snap, item, fname))

        summary = run_copy(
            items=items,
            dest_root=self.dest_disk,
            ctrl=ctrl,
            auto_copy_app=True,
            app_path=self.app_dir,
            unzip_models=True,
            progress_cb=on_prog,
        )

        self.assertFalse(summary["stopped"])
        self.assertEqual(summary["items_done"], 3)

        # 1. Check orga+ app copied to root
        dest_app = self.dest_disk / "orga+.app"
        self.assertTrue(dest_app.exists())

        # 2. Check item 1 (Chair): previews at root, model in model/
        dst_chair = self.dest_disk / "Furniture" / "Chairs" / "Office Chair"
        self.assertTrue((dst_chair / "image_1.jpg").exists())
        self.assertTrue((dst_chair / "meta.json").exists())
        self.assertTrue((dst_chair / "model" / "office_chair.skp").exists())

        # 3. Check item 2 (Door with .zip): unzipped into model/, .zip removed
        dst_door = self.dest_disk / "Architecture" / "Doors" / "Sliding Glass Door"
        self.assertTrue((dst_door / "preview.png").exists())
        self.assertTrue((dst_door / "meta.json").exists())
        self.assertTrue((dst_door / "model" / "sliding_door.skp").exists())
        self.assertTrue((dst_door / "model" / "textures" / "glass.jpg").exists())
        self.assertFalse((dst_door / "model" / "door_archive.zip").exists())
        self.assertFalse((dst_door / "door_archive.zip").exists())

        # 4. Check item 3 (Desk Lamp with root .fbx): placed in model/
        dst_lamp = self.dest_disk / "Lighting" / "Lamps" / "Desk Lamp"
        self.assertTrue((dst_lamp / "image_1.jpg").exists())
        self.assertTrue((dst_lamp / "model" / "desk_lamp.fbx").exists())

        # 5. Check item 4 (Indoor Plant, no model): NOT copied
        dst_plant = self.dest_disk / "Decor" / "Plants" / "Indoor Plant"
        self.assertFalse(dst_plant.exists())

        self.assertGreater(len(progress_calls), 0)

    def test_scan_items_direct_category_folder(self):
        """Test selecting a category folder directly (e.g. Scenes/)."""
        scenes_dir = self.tmp_dir / "Scenes"
        ext_dir = scenes_dir / "Exteriors"
        house_asset = ext_dir / "19492_House_Exterior"
        (house_asset / "model").mkdir(parents=True)
        (house_asset / "model" / "house.skp").write_bytes(b"SKP_DATA" * 50)
        (house_asset / "image_1.jpg").write_bytes(b"IMAGE_DATA" * 20)

        items, skipped = scan_items(scenes_dir, models_only=True)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].job, "Scenes")
        self.assertEqual(items[0].category, "Exteriors")
        self.assertEqual(items[0].asset.name, "19492_House_Exterior")
        self.assertEqual(items[0].model_format, "SKP")

    def test_scan_items_include_previews(self):
        """Test scanning with models_only=False includes items without 3D models."""
        items_all, skipped = scan_items(self.src_dir, models_only=False)
        self.assertEqual(len(items_all), 4)
        self.assertEqual(skipped, 0)
        titles = [it.title for it in items_all]
        self.assertIn("Indoor Plant", titles)

    def test_select_balanced_mechanism_by_count(self):
        """Test round-robin balanced selection across categories by item count."""
        items = [
            CopyItem(job="Scenes", category="Exteriors", asset=Path("a1"), title="Scene 1", total_bytes=100),
            CopyItem(job="Scenes", category="Exteriors", asset=Path("a2"), title="Scene 2", total_bytes=100),
            CopyItem(job="Furniture", category="Chairs", asset=Path("b1"), title="Chair 1", total_bytes=100),
            CopyItem(job="Furniture", category="Chairs", asset=Path("b2"), title="Chair 2", total_bytes=100),
            CopyItem(job="Lighting", category="Lamps", asset=Path("c1"), title="Lamp 1", total_bytes=100),
        ]
        # Target 3 items across 3 categories: should pick exactly 1 from each
        selected = select_balanced_mechanism(items, mode="count", limit_value=3, strategy="round_robin")
        self.assertEqual(len(selected), 3)
        sel_jobs = {uid.split("/")[0] for uid in selected}
        self.assertEqual(sel_jobs, {"Scenes", "Furniture", "Lighting"})

    def test_select_balanced_mechanism_by_size(self):
        """Test round-robin balanced selection across categories up to target size."""
        items = [
            CopyItem(job="Scenes", category="Exteriors", asset=Path("a1"), title="Scene 1", total_bytes=1000),
            CopyItem(job="Scenes", category="Exteriors", asset=Path("a2"), title="Scene 2", total_bytes=1000),
            CopyItem(job="Furniture", category="Chairs", asset=Path("b1"), title="Chair 1", total_bytes=1000),
            CopyItem(job="Furniture", category="Chairs", asset=Path("b2"), title="Chair 2", total_bytes=1000),
        ]
        # Target 2500 bytes: picks 1 from Furniture (1000), 1 from Scenes (1000) = 2000 bytes. Next would exceed 2500.
        selected = select_balanced_mechanism(items, mode="size", limit_value=2500, strategy="round_robin")
        self.assertEqual(len(selected), 2)
        sel_jobs = {uid.split("/")[0] for uid in selected}
        self.assertEqual(sel_jobs, {"Scenes", "Furniture"})

    def test_select_balanced_mechanism_with_filtering(self):
        """Test balanced selection filtered to included categories."""
        items = [
            CopyItem(job="Scenes", category="Exteriors", asset=Path("a1"), title="Scene 1", total_bytes=100),
            CopyItem(job="Furniture", category="Chairs", asset=Path("b1"), title="Chair 1", total_bytes=100),
            CopyItem(job="Lighting", category="Lamps", asset=Path("c1"), title="Lamp 1", total_bytes=100),
        ]
        selected = select_balanced_mechanism(
            items,
            mode="count",
            limit_value=2,
            included_categories={"Scenes", "Lighting"},
            strategy="round_robin",
        )
        self.assertEqual(len(selected), 2)
        sel_jobs = {uid.split("/")[0] for uid in selected}
        self.assertEqual(sel_jobs, {"Scenes", "Lighting"})
        self.assertNotIn("Furniture", sel_jobs)

    def test_user_folder_structure_with_rar_and_subcategories(self):
        """
        Test the user's exact folder structure:
          Scenes/
            Exteriors/
              Villa_19492/
                image_1.jpg
                image_2.jpg
                model/
                  exterior_model.rar
            Interiors/
              LivingRoom_20114/
                preview.png
                model/
                  living_room.zip
        When root is selected as 'Scenes/', it must discover both subcategories
        and allow copying only selected subcategories.
        """
        scenes_root = self.tmp_dir / "Scenes"
        ext_asset = scenes_root / "Exteriors" / "Villa_19492"
        (ext_asset / "model").mkdir(parents=True)
        (ext_asset / "image_1.jpg").write_bytes(b"EXT_IMG_1" * 10)
        (ext_asset / "image_2.jpg").write_bytes(b"EXT_IMG_2" * 10)
        rar_p = ext_asset / "model" / "exterior_model.rar"
        with zipfile.ZipFile(rar_p, "w") as zf:
            zf.writestr("exterior_model.skp", b"EXTERIOR_SKP_DATA" * 50)

        int_asset = scenes_root / "Interiors" / "LivingRoom_20114"
        (int_asset / "model").mkdir(parents=True)
        (int_asset / "preview.png").write_bytes(b"INT_IMG" * 10)
        zip_p = int_asset / "model" / "living_room.zip"
        with zipfile.ZipFile(zip_p, "w") as zf:
            zf.writestr("room.skp", b"ROOM_SKP_CONTENT" * 50)

        # 1. Scan with root = Scenes/
        items, skipped = scan_items(scenes_root, models_only=True)
        self.assertEqual(len(items), 2)
        self.assertEqual(skipped, 0)

        by_subcat = {it.category: it for it in items}
        self.assertIn("Exteriors", by_subcat)
        self.assertIn("Interiors", by_subcat)

        ext_item = by_subcat["Exteriors"]
        self.assertEqual(ext_item.job, "Scenes")
        self.assertEqual(ext_item.category, "Exteriors")
        self.assertEqual(ext_item.model_format, "RAR")
        self.assertEqual(ext_item.asset.name, "Villa_19492")

        int_item = by_subcat["Interiors"]
        self.assertEqual(int_item.job, "Scenes")
        self.assertEqual(int_item.category, "Interiors")
        self.assertEqual(int_item.model_format, "ZIP")

        # 2. Select ONLY Exteriors subcategory
        selected_subcats = {("Scenes", "Exteriors")}
        selected_ids = select_balanced_mechanism(
            items,
            mode="count",
            limit_value=10,
            included_subcategories=selected_subcats,
        )
        self.assertEqual(len(selected_ids), 1)
        self.assertIn(ext_item.unique_id, selected_ids)
        self.assertNotIn(int_item.unique_id, selected_ids)

        # 3. Copy only selected subcategory items
        items_to_copy = [it for it in items if it.unique_id in selected_ids]
        ctrl = CopyController()
        summary = run_copy(
            items=items_to_copy,
            dest_root=self.dest_disk,
            ctrl=ctrl,
            auto_copy_app=False,
            unzip_models=True,
        )
        self.assertEqual(summary["items_done"], 1)

        # Verify destination structure: model extracted to .skp, archive cleaned up
        dest_ext = self.dest_disk / "Scenes" / "Exteriors" / "Villa_19492"
        self.assertTrue((dest_ext / "image_1.jpg").exists())
        self.assertTrue((dest_ext / "image_2.jpg").exists())
        self.assertTrue((dest_ext / "model" / "exterior_model.skp").exists())
        self.assertFalse((dest_ext / "model" / "exterior_model.rar").exists())

        # Verify unselected subcategory was not copied
        dest_int = self.dest_disk / "Scenes" / "Interiors" / "LivingRoom_20114"
        self.assertFalse(dest_int.exists())

    def test_safe_extract_archive_rar_with_wrapper(self):
        """Test safe_extract_archive extracts RAR archive and strips wrapper folder."""
        from tools.orga_copy_tool import safe_extract_archive, normalize_model_directory

        rar_p = self.tmp_dir / "villa_bundle.rar"
        with zipfile.ZipFile(rar_p, "w") as zf:
            zf.writestr("Villa_Folder/villa.skp", b"VILLA_SKP_DATA")
            zf.writestr("Villa_Folder/textures/stone.jpg", b"STONE_DATA")

        target_model = self.tmp_dir / "villa_output" / "model"
        ctrl = CopyController()
        chunks = []
        safe_extract_archive(rar_p, target_model, ctrl, on_chunk=lambda n: chunks.append(n))

        # Check that villa.skp sits directly in /model/ and wrapper was stripped
        self.assertTrue((target_model / "villa.skp").exists())
        self.assertEqual((target_model / "villa.skp").read_bytes(), b"VILLA_SKP_DATA")
        self.assertTrue((target_model / "textures" / "stone.jpg").exists())
        self.assertFalse((target_model / "villa_bundle.rar").exists())
        self.assertFalse((target_model.parent / "villa_bundle.rar").exists())
        self.assertFalse((target_model / "Villa_Folder").exists())

    def test_normalize_model_directory_deep_skp_promotion(self):
        """Test normalize_model_directory promotes any .skp file to model/ root."""
        from tools.orga_copy_tool import normalize_model_directory

        target_model = self.tmp_dir / "deep_asset" / "model"
        deep_dir = target_model / "assets" / "nested_geometry"
        deep_dir.mkdir(parents=True)
        (deep_dir / "complex_scene.skp").write_bytes(b"COMPLEX_SKP_DATA")
        (deep_dir / "textures").mkdir()
        (deep_dir / "textures" / "fabric.jpg").write_bytes(b"FABRIC_DATA")

        # Also leave a dummy .rar in model and asset dir
        (target_model / "scene.rar").write_bytes(b"RAR")
        (target_model.parent / "scene.rar").write_bytes(b"RAR")

        normalize_model_directory(target_model, "scene.rar")

        # The .skp must be promoted directly to target_model / complex_scene.skp
        self.assertTrue((target_model / "complex_scene.skp").exists())
        self.assertEqual((target_model / "complex_scene.skp").read_bytes(), b"COMPLEX_SKP_DATA")
        # Archives must be removed
        self.assertFalse((target_model / "scene.rar").exists())
        self.assertFalse((target_model.parent / "scene.rar").exists())

    def test_nested_subfolders_depth_6_discovery_and_copy(self):
        """Test scanning and copying an asset nested at depth 6:
        root / Architecture / Residential / Houses / Exteriors / Modern / Villa_19492"""
        deep_root = self.tmp_dir / "Deep_Library"
        villa_dir = deep_root / "Architecture" / "Residential" / "Houses" / "Exteriors" / "Modern" / "Villa_19492"
        villa_dir.mkdir(parents=True)
        (villa_dir / "render_1.jpg").write_bytes(b"RENDER_1" * 20)
        (villa_dir / "render_2.jpg").write_bytes(b"RENDER_2" * 20)
        (villa_dir / "model").mkdir()
        rar_p = villa_dir / "model" / "villa.rar"
        with zipfile.ZipFile(rar_p, "w") as zf:
            zf.writestr("villa.skp", b"VILLA_SKP_DATA" * 50)

        # 1. Scan deep root
        items, skipped = scan_items(deep_root, models_only=True)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.job, "Architecture")
        self.assertEqual(item.category, "Residential / Houses / Exteriors / Modern")
        self.assertEqual(item.title, "Villa_19492")
        self.assertEqual(item.model_format, "RAR")

        # 2. Copy item to destination disk
        ctrl = CopyController()
        summary = run_copy(
            items=items,
            dest_root=self.dest_disk,
            ctrl=ctrl,
            auto_copy_app=False,
            unzip_models=True,
        )
        self.assertEqual(summary["items_done"], 1)

        # 3. Verify destination hierarchy preserves all nested subfolders and unzips .skp
        dest_villa = self.dest_disk / "Architecture" / "Residential" / "Houses" / "Exteriors" / "Modern" / "Villa_19492"
        self.assertTrue((dest_villa / "render_1.jpg").exists())
        self.assertTrue((dest_villa / "render_2.jpg").exists())
        self.assertTrue((dest_villa / "model" / "villa.skp").exists())
        self.assertFalse((dest_villa / "model" / "villa.rar").exists())

    def test_multi_item_subcategory_folder_dynamic_images(self):
        """Test a subcategory folder with multiple images and models directly inside:
        Scenes / Commercial / Offices / Meeting_Rooms / [Boardroom.jpg, Suite.jpg, model/Boardroom.rar, model/Suite.skp]"""
        multi_root = self.tmp_dir / "Multi_Library"
        rooms_dir = multi_root / "Scenes" / "Commercial" / "Offices" / "Meeting_Rooms"
        rooms_dir.mkdir(parents=True)
        (rooms_dir / "Boardroom_Modern.jpg").write_bytes(b"BOARDROOM_IMG" * 15)
        (rooms_dir / "Executive_Suite.png").write_bytes(b"SUITE_IMG" * 15)
        (rooms_dir / "model").mkdir()

        rar_p = rooms_dir / "model" / "Boardroom_Modern.rar"
        with zipfile.ZipFile(rar_p, "w") as zf:
            zf.writestr("Boardroom_Modern.skp", b"BOARDROOM_SKP" * 40)
        (rooms_dir / "model" / "Executive_Suite.skp").write_bytes(b"SUITE_SKP" * 40)

        # 1. Scan multi root: must discover both items individually!
        items, skipped = scan_items(multi_root, models_only=True)
        self.assertEqual(len(items), 2)
        by_title = {it.title: it for it in items}
        self.assertIn("Boardroom Modern", by_title)
        self.assertIn("Executive Suite", by_title)

        b_item = by_title["Boardroom Modern"]
        self.assertEqual(b_item.job, "Scenes")
        self.assertEqual(b_item.category, "Commercial / Offices / Meeting_Rooms")
        self.assertEqual(b_item.model_format, "RAR")

        s_item = by_title["Executive Suite"]
        self.assertEqual(s_item.job, "Scenes")
        self.assertEqual(s_item.category, "Commercial / Offices / Meeting_Rooms")
        self.assertEqual(s_item.model_format, "SKP")

        # 2. Copy only "Boardroom Modern"
        ctrl = CopyController()
        summary = run_copy(
            items=[b_item],
            dest_root=self.dest_disk,
            ctrl=ctrl,
            auto_copy_app=False,
            unzip_models=True,
        )
        self.assertEqual(summary["items_done"], 1)

        # 3. Verify destination: only Boardroom Modern copied and unzipped
        dest_b = self.dest_disk / "Scenes" / "Commercial" / "Offices" / "Meeting_Rooms" / "Boardroom Modern"
        self.assertTrue((dest_b / "Boardroom_Modern.jpg").exists())
        self.assertTrue((dest_b / "model" / "Boardroom_Modern.skp").exists())
        self.assertFalse((dest_b / "model" / "Boardroom_Modern.rar").exists())

        # Executive Suite should NOT exist
        dest_s = self.dest_disk / "Scenes" / "Commercial" / "Offices" / "Meeting_Rooms" / "Executive Suite"
        self.assertFalse(dest_s.exists())


if __name__ == "__main__":
    unittest.main()
