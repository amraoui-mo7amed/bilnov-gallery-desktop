"""
Bilnov Gallery Library Manager
Reads from local asset library: ./storage (or ./data)
Guarantees asset storage is strictly protected against write, delete, copy, and sending operations.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from config import DATA_DIR

logger = logging.getLogger("library")

SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
SUPPORTED_MODEL_EXTS = {".skp", ".obj", ".fbx", ".blend", ".zip", ".rar", ".7z", ".3ds", ".max", ".c4d", ".glb", ".gltf", ".stl"}


def format_bytes(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.1f} {units[i]}"


class LibraryManager:
    """
    Manages scanning and indexing of 3D models and assets within ./data.
    Strictly read-only: no write, delete, copy, or export operations are permitted on ./data.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir or DATA_DIR).resolve()
        # Ensure directory exists without modifying existing files
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_meta(self, article_dir: Path) -> Dict[str, Any]:
        """Reads meta.json if present in the article folder."""
        meta_file = article_dir / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_meta(self, article_dir: Path, data: Dict[str, Any]):
        """Saves meta.json in the article folder."""
        meta_file = article_dir / "meta.json"
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning("Failed to save meta: %s", e)

    def delete_item(self, rel_folder_path: str) -> bool:
        """Deletes an article folder within ./data."""
        import shutil
        target = (self.base_dir / rel_folder_path).resolve()
        if not str(target).startswith(str(self.base_dir)):
            return False
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
            return True
        return False

    def create_bundle_zip(self, rel_folder_path: str) -> Optional[Path]:
        """Packages an article directory into a zip archive."""
        import zipfile
        import tempfile
        target = (self.base_dir / rel_folder_path).resolve()
        if not str(target).startswith(str(self.base_dir)) or not target.exists():
            return None
        temp_dir = Path(tempfile.gettempdir()) / "bilnov_exports"
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_path = temp_dir / f"{target.name}_bundle.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in sorted(target.rglob("*")):
                if item.is_file() and not item.name.startswith("."):
                    zf.write(item, arcname=str(item.relative_to(target)))
        return zip_path

    def is_article_dir(self, p: Path) -> bool:
        """Determines if a directory contains model assets or preview images."""
        if not p.is_dir() or p.name.startswith("."):
            return False
        # Check for model folder
        model_dir = p / "model"
        if model_dir.is_dir():
            return True
        # Check for images or 3D model files
        try:
            for item in p.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    if ext in SUPPORTED_IMAGE_EXTS or ext in SUPPORTED_MODEL_EXTS:
                        return True
        except (PermissionError, OSError):
            pass
        return False

    def scan_library(self, search: Optional[str] = None, category_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Scans ./data for all articles, categories, and 3D models.
        Supports depth 1, 2, or 3 hierarchy (e.g., data/Cat/Sub/Article, data/Cat/Article, data/Article).
        """
        items: List[Dict[str, Any]] = []
        total_models = 0
        total_images = 0
        total_size_bytes = 0
        categories_set: Set[str] = set()
        subcategories_set: Set[str] = set()

        if not self.base_dir.exists():
            return {
                "items": [],
                "stats": {
                    "total_models": 0,
                    "total_images": 0,
                    "total_size": "0 B",
                    "total_size_bytes": 0,
                    "categories_count": 0,
                    "subcategories_count": 0,
                },
                "categories": [],
            }

        # Discover article directories inside ./data
        visited_dirs: Set[Path] = set()
        article_candidates: List[Path] = []

        try:
            for root, dirs, files in os.walk(self.base_dir):
                root_path = Path(root)
                # Ignore hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                if root_path == self.base_dir:
                    continue

                if self.is_article_dir(root_path):
                    article_candidates.append(root_path)
                    visited_dirs.add(root_path)
                    # Don't descend into subfolders of an article dir (e.g. model/ or images/)
                    dirs.clear()
        except Exception as e:
            logger.error("Error walking data directory: %s", e)

        for article_dir in sorted(article_candidates):
            try:
                rel_parts = article_dir.relative_to(self.base_dir).parts
            except ValueError:
                continue

            article_title = article_dir.name
            meta = self.get_meta(article_dir)

            # Derive category and subcategory from path or metadata
            if len(rel_parts) >= 3:
                cat_name = rel_parts[0]
                sub_name = rel_parts[1]
            elif len(rel_parts) == 2:
                cat_name = rel_parts[0]
                sub_name = meta.get("subcategory", "")
            else:
                cat_name = meta.get("category", "General")
                sub_name = meta.get("subcategory", "")

            if cat_name:
                categories_set.add(cat_name)
            if sub_name:
                subcategories_set.add(sub_name)

            # Check model file inside article_dir / "model" or directly in article_dir
            model_file: Optional[Path] = None
            model_size = 0

            model_dir = article_dir / "model"
            if model_dir.exists() and model_dir.is_dir():
                model_files = [f for f in model_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
                if model_files:
                    model_file = model_files[0]
                    model_size = model_file.stat().st_size

            if not model_file:
                # Look for standalone 3D model files directly in article dir
                direct_models = [
                    f for f in article_dir.iterdir()
                    if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in SUPPORTED_MODEL_EXTS
                ]
                if direct_models:
                    model_file = direct_models[0]
                    model_size = model_file.stat().st_size

            if model_file:
                total_models += 1
                total_size_bytes += model_size

            # Discover image previews
            raw_imgs: List[Path] = []
            for img in article_dir.iterdir():
                if img.is_file() and not img.name.startswith(".") and img.suffix.lower() in SUPPORTED_IMAGE_EXTS:
                    raw_imgs.append(img)

            # Also check article_dir / "images" subfolder if present
            imgs_subdir = article_dir / "images"
            if imgs_subdir.exists() and imgs_subdir.is_dir():
                for img in imgs_subdir.iterdir():
                    if img.is_file() and not img.name.startswith(".") and img.suffix.lower() in SUPPORTED_IMAGE_EXTS:
                        raw_imgs.append(img)

            # Sort images naturally (image_1, image_2, image_10)
            def _sort_key(p: Path):
                m = re.search(r"(\d+)", p.stem)
                return int(m.group(1)) if m else 9999

            raw_imgs.sort(key=_sort_key)
            images = []
            for img in raw_imgs:
                images.append(str(img.relative_to(self.base_dir)))
                total_images += 1
                total_size_bytes += img.stat().st_size

            # Filter by Category
            if category_filter and category_filter != "all" and cat_name != category_filter:
                continue

            # Filter by Search Keyword
            if search:
                s_lower = search.lower()
                match_title = s_lower in article_title.lower()
                match_cat = s_lower in cat_name.lower() or (sub_name and s_lower in sub_name.lower())
                match_file = model_file and s_lower in model_file.name.lower()
                if not (match_title or match_cat or match_file):
                    continue

            rel_article = str(article_dir.relative_to(self.base_dir))
            rel_model = str(model_file.relative_to(self.base_dir)) if model_file else None

            # Format human title
            clean_title = meta.get("title") or article_title.replace("_", " ")

            items.append({
                "id": rel_article,
                "category": cat_name,
                "subcategory": sub_name,
                "title": clean_title,
                "folder_path": rel_article,
                "folder_full_path": str(article_dir.resolve()),
                "has_model": model_file is not None,
                "model_filename": model_file.name if model_file else None,
                "model_path": rel_model,
                "model_file_full": str(model_file.resolve()) if model_file else "",
                "model_size": format_bytes(model_size),
                "model_size_bytes": model_size,
                "images": images,
                "images_count": len(images),
                "article_url": meta.get("article_url", ""),
                "modified_at": int(article_dir.stat().st_mtime),
            })

        # Sort newest first
        items.sort(key=lambda x: x["modified_at"], reverse=True)

        # Categories are derived strictly from the real content of the storage folder
        categories_list = sorted(list(categories_set))

        return {
            "items": items,
            "stats": {
                "total_models": total_models,
                "total_images": total_images,
                "total_size": format_bytes(total_size_bytes),
                "total_size_bytes": total_size_bytes,
                "categories_count": len(categories_list),
                "subcategories_count": len(subcategories_set),
            },
            "categories": categories_list,
        }

    def load_categories_tree(self) -> List[Dict[str, Any]]:
        """Builds the categories hierarchy strictly from the items actually present in storage."""
        lib_data = self.scan_library()
        cat_map: Dict[str, Set[str]] = {}
        cat_counts: Dict[str, int] = {}
        for itm in lib_data["items"]:
            c = itm.get("category") or "General"
            s = itm.get("subcategory") or ""
            cat_map.setdefault(c, set())
            cat_counts[c] = cat_counts.get(c, 0) + 1
            if s:
                cat_map[c].add(s)

        tree = []
        for cat_name, subs in sorted(cat_map.items()):
            tree.append({
                "name": cat_name,
                "title": cat_name,
                "count": cat_counts.get(cat_name, 0),
                "subcategories": [{"name": sub, "title": sub} for sub in sorted(subs)],
            })
        return tree

    def add_item(
        self,
        title: str,
        image_paths: List[str],
        model_paths: List[str],
        category: str = "",
    ) -> Dict[str, Any]:
        """
        Creates a new article in the library:
          storage/<Category>/<Title>/image_1.ext (thumbnail), image_2.ext, ...
          storage/<Category>/<Title>/model/<sketchup files>
          storage/<Category>/<Title>/meta.json
        The first image provided is always used as the thumbnail.
        """
        import shutil
        from datetime import datetime

        clean_title = (title or "").strip()
        if not clean_title:
            raise ValueError("Article name is required")

        imgs = [Path(p) for p in image_paths if p and Path(p).is_file()]
        models = [Path(p) for p in model_paths if p and Path(p).is_file()]
        imgs = [p for p in imgs if p.suffix.lower() in SUPPORTED_IMAGE_EXTS]
        if not imgs:
            raise ValueError("At least one image is required")
        if not models:
            raise ValueError("At least one model file is required")

        def _safe(name: str) -> str:
            s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip().strip(".")
            return s or "Untitled"

        cat_name = _safe(category.strip()) if category and category.strip() else "My Models"
        parent = self.base_dir / cat_name
        folder_name = _safe(clean_title)
        target = parent / folder_name
        counter = 1
        while target.exists():
            target = parent / f"{folder_name}_{counter}"
            counter += 1
        target.mkdir(parents=True, exist_ok=False)

        try:
            # Images: numbered so the first one sorts first and becomes the thumbnail
            for idx, img in enumerate(imgs, start=1):
                shutil.copy2(img, target / f"image_{idx}{img.suffix.lower()}")

            model_dir = target / "model"
            model_dir.mkdir(exist_ok=True)
            for m in models:
                dest = model_dir / m.name
                n = 1
                while dest.exists():
                    dest = model_dir / f"{m.stem}_{n}{m.suffix}"
                    n += 1
                shutil.copy2(m, dest)

            self.save_meta(target, {
                "title": clean_title,
                "category": cat_name,
                "thumbnail": f"image_1{imgs[0].suffix.lower()}",
                "created_at": datetime.now().isoformat(),
                "source": "user",
            })
        except Exception:
            shutil.rmtree(target, ignore_errors=True)
            raise

        return {"folder_path": str(target.relative_to(self.base_dir)), "title": clean_title}


library_manager = LibraryManager()
