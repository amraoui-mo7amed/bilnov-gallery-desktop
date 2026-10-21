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

DEFAULT_JOBS = [
    {"id": "architect", "name": "Architect", "folder": "Architect"},
    {"id": "graphiste", "name": "Graphiste", "folder": "Graphiste"},
    {"id": "video maker", "name": "Video Maker", "folder": "Video Maker"},
]


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
        if not p.is_dir() or p.name.startswith(".") or p.name.lower() in ("model", "images"):
            return False
        # Check for model folder
        model_dir = p / "model"
        if model_dir.is_dir():
            return True
        # Check for images folder
        imgs_dir = p / "images"
        if imgs_dir.is_dir():
            return True
        # Check for meta.json
        if (p / "meta.json").exists():
            return True
        # Check for images or 3D model files
        try:
            for item in p.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    ext = item.suffix.lower()
                    if ext in SUPPORTED_IMAGE_EXTS or ext in SUPPORTED_MODEL_EXTS:
                        return True
        except (PermissionError, OSError):
            pass
        return False

    def scan_library(self, search: Optional[str] = None, category_filter: Optional[str] = None, subcategory_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Dynamically scans storage for all 3D models and preview images regardless of folder depth.
        Supports:
          - Deeply nested subfolders (depth 1, 2, 3, 4, 5, 6+ levels).
          - Dedicated asset folders (e.g. Category/Subcategory/.../AssetFolder/).
          - Multi-item subcategory folders (multiple images & models in the same directory).
        Dynamically derives Category, Subcategory, and Title, pairing preview images with their
        corresponding 3D model files.
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

        def _sort_key(p: Path):
            m = re.search(r"(\d+)", p.stem)
            return int(m.group(1)) if m else 9999

        def _match_model(img_path: Path, candidate_models: List[Path]) -> Optional[Path]:
            if not candidate_models:
                return None
            img_stem = img_path.stem.lower()
            # 1. Exact stem match
            for m in candidate_models:
                if m.stem.lower() == img_stem:
                    return m
            # 2. Substring / prefix match
            for m in candidate_models:
                m_stem = m.stem.lower()
                if m_stem in img_stem or img_stem in m_stem:
                    return m
            # 3. Numeric ID match (e.g. 19492)
            img_nums = re.findall(r"\d+", img_stem)
            if img_nums:
                for m in candidate_models:
                    m_nums = re.findall(r"\d+", m.stem.lower())
                    if any(num in m_nums for num in img_nums if len(num) >= 2):
                        return m
            # 4. If exactly one candidate in directory, pair with it
            if len(candidate_models) == 1:
                return candidate_models[0]
            return None

        # Recursively discover asset folders and multi-item directories
        discovered_candidates: List[Dict[str, Any]] = []
        skip_dirs = {"model", "images", "textures", "__macosx", ".git", "venv", ".venv"}

        for root_str, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in skip_dirs]
            curr_dir = Path(root_str)
            if curr_dir == self.base_dir:
                continue

            # Preview images directly in curr_dir
            raw_imgs = [
                curr_dir / f for f in files
                if not f.startswith(".") and Path(f).suffix.lower() in SUPPORTED_IMAGE_EXTS
            ]

            # Preview images in images/ subfolder
            imgs_subdir = curr_dir / "images"
            if imgs_subdir.is_dir():
                try:
                    for f in imgs_subdir.iterdir():
                        if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in SUPPORTED_IMAGE_EXTS:
                            raw_imgs.append(f)
                except (PermissionError, OSError):
                    pass

            raw_imgs.sort(key=_sort_key)

            # Models in model/ subfolder or directly in curr_dir
            models: List[Path] = []
            model_dir = curr_dir / "model"
            if model_dir.is_dir():
                try:
                    for f in model_dir.iterdir():
                        if f.is_file() and not f.name.startswith(".") and (f.suffix.lower() in SUPPORTED_MODEL_EXTS or f.suffix.lower() in {".zip", ".rar", ".7z", ".tar", ".gz"}):
                            models.append(f)
                except (PermissionError, OSError):
                    pass

            for f in files:
                if not f.startswith("."):
                    ext = Path(f).suffix.lower()
                    if ext in SUPPORTED_MODEL_EXTS or ext in {".zip", ".rar", ".7z", ".tar", ".gz"}:
                        models.append(curr_dir / f)

            has_meta = (curr_dir / "meta.json").exists()

            if not raw_imgs and not models and not has_meta:
                continue

            try:
                rel_parts = curr_dir.relative_to(self.base_dir).parts
            except ValueError:
                rel_parts = (curr_dir.name,)

            # Check if this folder contains multiple items or is a dedicated asset folder
            is_multi = False
            if len(models) > 1 and len(raw_imgs) > 1 and not has_meta and not imgs_subdir.is_dir():
                matched_count = sum(1 for img in raw_imgs if _match_model(img, models) is not None)
                if matched_count >= 2:
                    is_multi = True

            if is_multi:
                # Multi-item directory: curr_dir is the subcategory container
                if len(rel_parts) == 0:
                    cat_name = "General"
                    sub_name = "General"
                elif len(rel_parts) == 1:
                    cat_name = rel_parts[0]
                    sub_name = rel_parts[0]
                else:
                    cat_name = rel_parts[0]
                    sub_name = " / ".join(rel_parts[1:])

                for img in raw_imgs:
                    matched_m = _match_model(img, models)
                    m_size = matched_m.stat().st_size if matched_m and matched_m.exists() else 0
                    i_size = img.stat().st_size if img.exists() else 0
                    item_title = img.stem.replace("_", " ").replace("-", " ").strip()
                    rel_item_id = f"{'/'.join(rel_parts)}/{img.stem}"

                    discovered_candidates.append({
                        "id": rel_item_id,
                        "category": cat_name,
                        "subcategory": sub_name,
                        "title": item_title,
                        "folder_dir": curr_dir,
                        "images": [img],
                        "model_file": matched_m,
                        "model_size": m_size,
                        "total_size": i_size + m_size,
                        "article_url": "",
                        "modified_at": int(img.stat().st_mtime) if img.exists() else int(curr_dir.stat().st_mtime),
                    })
            else:
                # Dedicated single asset folder
                if len(rel_parts) == 0:
                    cat_name = "General"
                    sub_name = "General"
                    folder_title = curr_dir.name
                elif len(rel_parts) == 1:
                    cat_name = self.base_dir.name or "General"
                    sub_name = "General"
                    folder_title = rel_parts[0]
                elif len(rel_parts) == 2:
                    cat_name = rel_parts[0]
                    sub_name = "General"
                    folder_title = rel_parts[1]
                elif len(rel_parts) == 3:
                    cat_name = rel_parts[0]
                    sub_name = rel_parts[1]
                    folder_title = rel_parts[2]
                else:
                    cat_name = rel_parts[0]
                    sub_name = " / ".join(rel_parts[1:-1])
                    folder_title = rel_parts[-1]

                meta = self.get_meta(curr_dir)
                article_title = meta.get("title") or folder_title.replace("_", " ")
                main_model = models[0] if models else None
                m_size = main_model.stat().st_size if main_model and main_model.exists() else 0
                imgs_size = sum(img.stat().st_size for img in raw_imgs if img.exists())
                rel_article = str(curr_dir.relative_to(self.base_dir))

                discovered_candidates.append({
                    "id": rel_article,
                    "category": cat_name,
                    "subcategory": sub_name,
                    "title": article_title,
                    "folder_dir": curr_dir,
                    "images": raw_imgs,
                    "model_file": main_model,
                    "model_size": m_size,
                    "total_size": imgs_size + m_size,
                    "article_url": meta.get("article_url", ""),
                    "modified_at": int(curr_dir.stat().st_mtime),
                })

        for candidate in discovered_candidates:
            cat_name = candidate["category"]
            sub_name = candidate["subcategory"]
            article_title = candidate["title"]
            model_file = candidate["model_file"]
            raw_imgs = candidate["images"]
            model_size = candidate["model_size"]
            curr_dir = candidate["folder_dir"]

            if cat_name:
                categories_set.add(cat_name)
            if sub_name:
                subcategories_set.add(sub_name)

            if model_file:
                total_models += 1
                total_size_bytes += model_size

            # Filter by Category
            if category_filter and category_filter != "all" and cat_name.lower() != category_filter.lower():
                continue

            # Filter by Subcategory (supports full path e.g. "Commercial / Offices" or leaf "Offices")
            if subcategory_filter and subcategory_filter != "all":
                s_filter = subcategory_filter.strip().lower()
                sub_lower = sub_name.lower()
                leaf_sub = sub_lower.split(" / ")[-1].strip()
                if s_filter != sub_lower and s_filter != leaf_sub:
                    continue

            # Filter by Search Keyword
            if search:
                s_lower = search.lower()
                match_title = s_lower in article_title.lower()
                match_cat = s_lower in cat_name.lower() or (sub_name and s_lower in sub_name.lower())
                match_file = model_file and s_lower in model_file.name.lower()
                if not (match_title or match_cat or match_file):
                    continue

            images = []
            for img in raw_imgs:
                images.append(str(img.relative_to(self.base_dir)))
                total_images += 1
                total_size_bytes += img.stat().st_size

            rel_article = str(curr_dir.relative_to(self.base_dir))
            rel_model = str(model_file.relative_to(self.base_dir)) if model_file else None

            items.append({
                "id": candidate["id"],
                "category": cat_name,
                "subcategory": sub_name,
                "title": article_title,
                "folder_path": rel_article,
                "folder_full_path": str(curr_dir.resolve()),
                "has_model": model_file is not None,
                "model_filename": model_file.name if model_file else None,
                "model_path": rel_model,
                "model_file_full": str(model_file.resolve()) if model_file else "",
                "model_size": format_bytes(model_size),
                "model_size_bytes": model_size,
                "images": images,
                "images_count": len(images),
                "article_url": candidate["article_url"],
                "modified_at": candidate["modified_at"],
            })

        # Sort newest first
        items.sort(key=lambda x: x["modified_at"], reverse=True)

        # Categories are derived from all discovered articles (with or without a model)
        categories_list = sorted({it["category"] for it in items if it.get("category")})

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

    def get_subcategories(self, category: Optional[str] = None) -> List[str]:
        """Returns unique subcategory names found in storage, optionally filtered by category."""
        subcats: Set[str] = set()
        if not self.base_dir.exists():
            return []

        try:
            items = self.scan_library().get("items", [])
            target = category.strip().lower() if category and category.strip() else None
            for itm in items:
                c = (itm.get("category") or "").strip()
                s = (itm.get("subcategory") or "").strip()
                if s and s.lower() != "general":
                    if not target or c.lower() == target:
                        subcats.add(s)
        except Exception as e:
            logger.error("Error reading subcategories: %s", e)

        return sorted(list(subcats), key=lambda x: x.lower())

    def get_predefined_categories(self) -> List[str]:
        """Returns prefilled category names from the storage folder taxonomy file
        (categories.json), falling back to the sibling data folder when needed."""
        candidates = [
            self.base_dir / "categories.json",
            self.base_dir.parent / "data" / "categories.json",
            self.base_dir.parent / "storage" / "categories.json",
        ]
        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                with open(candidate, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning("Failed to read predefined categories from %s: %s", candidate, e)
                continue

            names: List[str] = []
            if isinstance(data, dict):
                data = data.get("categories", [])
            if isinstance(data, list):
                for entry in data:
                    if not isinstance(entry, dict):
                        continue
                    heading = entry.get("heading") or {}
                    name = heading.get("name") if isinstance(heading, dict) else None
                    if not name:
                        name = entry.get("name") or entry.get("title")
                    if name and name not in names:
                        names.append(str(name))
            if names:
                return names
        return []

    def get_subcategory_map(self) -> Dict[str, List[str]]:
        """Maps each storage category folder to its immediate subcategory folders,
        i.e. the live storage/<category>/<subcategory>/ hierarchy. Also covers
        user-created categories/subcategories since those are just folders."""
        result: Dict[str, List[str]] = {}
        if not self.base_dir.exists():
            return result
        try:
            for cat_dir in sorted(self.base_dir.iterdir()):
                if not cat_dir.is_dir() or cat_dir.name.startswith(".") or self.is_article_dir(cat_dir):
                    continue
                subs: List[str] = []
                for sub_dir in sorted(cat_dir.iterdir()):
                    if not sub_dir.is_dir() or sub_dir.name.startswith(".") or self.is_article_dir(sub_dir):
                        continue
                    if sub_dir.name not in subs:
                        subs.append(sub_dir.name)
                result[cat_dir.name] = subs
        except Exception as e:
            logger.error("Error reading subcategory map from disk: %s", e)
        return result

    def add_item(
        self,
        title: str,
        image_paths: List[str],
        model_paths: List[str],
        category: str = "",
        subcategory: str = "",
    ) -> Dict[str, Any]:
        """
        Creates a new article in the library:
          storage/<Category>/<Subcategory>/<Title>/image_1.ext (thumbnail), image_2.ext, ...
          storage/<Category>/<Subcategory>/<Title>/model/<sketchup files>
          storage/<Category>/<Subcategory>/<Title>/meta.json
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
            return s or "General"

        cat_name = _safe(category.strip()) if category and category.strip() else "General"
        sub_name = _safe(subcategory.strip()) if subcategory and subcategory.strip() else "General"
        parent = self.base_dir / cat_name / sub_name
        folder_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", clean_title).strip().strip(".") or "Untitled"
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
                "subcategory": sub_name,
                "thumbnail": f"image_1{imgs[0].suffix.lower()}",
                "created_at": datetime.now().isoformat(),
                "source": "user",
            })
        except Exception:
            shutil.rmtree(target, ignore_errors=True)
            raise

        return {"folder_path": str(target.relative_to(self.base_dir)), "title": clean_title}

    def get_jobs(self) -> List[Dict[str, Any]]:
        """Returns all available jobs: default jobs + discovered folders + user-created jobs."""
        jobs: List[Dict[str, Any]] = [dict(j) for j in DEFAULT_JOBS]
        seen_folders = {j["folder"].lower() for j in jobs}
        seen_ids = {j["id"].lower() for j in jobs}

        # 1. Check jobs.json if exists
        jobs_file = self.base_dir / "jobs.json"
        if jobs_file.exists():
            try:
                with open(jobs_file, "r", encoding="utf-8") as f:
                    saved_jobs = json.load(f)
                    if isinstance(saved_jobs, list):
                        for sj in saved_jobs:
                            if isinstance(sj, dict) and "name" in sj:
                                name = str(sj["name"]).strip()
                                folder = str(sj.get("folder", name)).strip()
                                jid = str(sj.get("id", name.lower())).strip()
                                if folder.lower() not in seen_folders:
                                    seen_folders.add(folder.lower())
                                    seen_ids.add(jid.lower())
                                    jobs.append({
                                        "id": jid,
                                        "name": name,
                                        "folder": folder,
                                        "is_custom": True,
                                    })
            except Exception as e:
                logger.warning("Failed to read jobs.json: %s", e)

        # 2. Check live folders in base_dir
        if self.base_dir.exists():
            try:
                for d in sorted(self.base_dir.iterdir()):
                    if not d.is_dir() or d.name.startswith(".") or self.is_article_dir(d):
                        continue
                    if d.name.lower() in ("imported", "categories", "__pycache__"):
                        continue
                    if d.name.lower() not in seen_folders:
                        seen_folders.add(d.name.lower())
                        jobs.append({
                            "id": d.name.lower(),
                            "name": d.name,
                            "folder": d.name,
                            "is_custom": True,
                        })
            except Exception as e:
                logger.warning("Failed to scan base_dir for jobs: %s", e)

        return jobs

    def create_job(self, name: str) -> Dict[str, Any]:
        """Creates a new job folder in the library and persists it in jobs.json."""
        clean_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", str(name or "")).strip().strip(".")
        if not clean_name:
            raise ValueError("Job name is required")

        # Check existing
        for j in self.get_jobs():
            if j["name"].lower() == clean_name.lower() or j["folder"].lower() == clean_name.lower():
                job_dir = self.base_dir / j["folder"]
                job_dir.mkdir(parents=True, exist_ok=True)
                return j

        job_dir = self.base_dir / clean_name
        job_dir.mkdir(parents=True, exist_ok=True)

        new_job = {
            "id": clean_name.lower(),
            "name": clean_name,
            "folder": clean_name,
            "is_custom": True,
        }

        jobs_file = self.base_dir / "jobs.json"
        saved_jobs: List[Dict[str, Any]] = []
        if jobs_file.exists():
            try:
                with open(jobs_file, "r", encoding="utf-8") as f:
                    saved_jobs = json.load(f)
                    if not isinstance(saved_jobs, list):
                        saved_jobs = []
            except Exception:
                saved_jobs = []

        if not any(sj.get("name", "").lower() == clean_name.lower() for sj in saved_jobs):
            saved_jobs.append(new_job)
            try:
                with open(jobs_file, "w", encoding="utf-8") as f:
                    json.dump(saved_jobs, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.warning("Failed to save jobs.json: %s", e)

        return new_job

    def import_folder(
        self,
        folder_path: Path,
        job: str = "Architect",
        category: str = "General",
    ) -> Dict[str, Any]:
        """
        Imports an entire directory of 3D assets or a single asset folder into the library:
        storage / <job> / <category> / <asset>
        Guarantees strict 3-level hierarchy so all items are discovered by scan_library().
        """
        import shutil
        from datetime import datetime

        src_path = Path(folder_path).resolve()
        if not src_path.exists() or not src_path.is_dir():
            raise ValueError(f"Selected folder does not exist or is not a directory: {folder_path}")

        def _safe(s: str) -> str:
            clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", str(s or "")).strip().strip(".")
            return clean or "General"

        cat_job = _safe(job) or "Architect"
        sub_cat = _safe(category) or "General"
        target_parent = self.base_dir / cat_job / sub_cat
        target_parent.mkdir(parents=True, exist_ok=True)

        def _copy_single_asset(asset_src: Path, asset_title: Optional[str] = None) -> bool:
            title = (asset_title or asset_src.name).replace("_", " ").replace("-", " ").strip()
            folder_clean_name = _safe(asset_src.name) or "Imported_Asset"
            dest = target_parent / folder_clean_name
            counter = 1
            while dest.exists():
                dest = target_parent / f"{folder_clean_name}_{counter}"
                counter += 1
            dest.mkdir(parents=True, exist_ok=True)

            try:
                # 1. Images
                raw_imgs = []
                for f in asset_src.iterdir():
                    if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in SUPPORTED_IMAGE_EXTS:
                        raw_imgs.append(f)
                imgs_subdir = asset_src / "images"
                if imgs_subdir.exists() and imgs_subdir.is_dir():
                    for f in imgs_subdir.iterdir():
                        if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in SUPPORTED_IMAGE_EXTS:
                            raw_imgs.append(f)

                def _sort_key(p: Path):
                    m = re.search(r"(\d+)", p.stem)
                    return int(m.group(1)) if m else 9999
                raw_imgs.sort(key=_sort_key)

                copied_images = []
                for idx, img in enumerate(raw_imgs, start=1):
                    dest_img = dest / f"image_{idx}{img.suffix.lower()}"
                    shutil.copy2(img, dest_img)
                    copied_images.append(dest_img.name)

                # 2. Models
                model_dir = dest / "model"
                model_dir.mkdir(parents=True, exist_ok=True)

                src_model_dir = asset_src / "model"
                raw_models = []
                if src_model_dir.exists() and src_model_dir.is_dir():
                    for f in src_model_dir.iterdir():
                        if f.is_file() and not f.name.startswith("."):
                            raw_models.append(f)

                for f in asset_src.iterdir():
                    if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in SUPPORTED_MODEL_EXTS:
                        raw_models.append(f)

                for m in raw_models:
                    dest_m = model_dir / m.name
                    counter_m = 1
                    while dest_m.exists():
                        dest_m = model_dir / f"{m.stem}_{counter_m}{m.suffix}"
                        counter_m += 1
                    shutil.copy2(m, dest_m)

                # 3. Meta
                existing_meta = self.get_meta(asset_src)
                meta_data = {
                    "title": existing_meta.get("title") or title,
                    "category": cat_job,
                    "subcategory": sub_cat,
                    "thumbnail": copied_images[0] if copied_images else "",
                    "created_at": datetime.now().isoformat(),
                    "source": "imported_folder",
                }
                self.save_meta(dest, meta_data)
                return True
            except Exception as e:
                logger.error("Failed to copy asset %s: %s", asset_src, e)
                shutil.rmtree(dest, ignore_errors=True)
                return False

        child_dirs = [d for d in src_path.iterdir() if d.is_dir() and not d.name.startswith(".") and d.name.lower() not in ("model", "images")]
        asset_dirs = [d for d in child_dirs if self.is_article_dir(d)]

        imported_count = 0
        if asset_dirs:
            for ad in asset_dirs:
                if _copy_single_asset(ad):
                    imported_count += 1
        elif self.is_article_dir(src_path):
            if _copy_single_asset(src_path):
                imported_count += 1
        elif child_dirs:
            for cd in child_dirs:
                if _copy_single_asset(cd):
                    imported_count += 1
            if imported_count == 0:
                if _copy_single_asset(src_path):
                    imported_count += 1
        else:
            if _copy_single_asset(src_path):
                imported_count += 1

        return {
            "count": imported_count,
            "job": cat_job,
            "category": sub_cat,
        }


library_manager = LibraryManager()

