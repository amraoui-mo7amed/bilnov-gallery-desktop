#!/usr/bin/env python3
"""
orga+ Copy Tool
===============

High-speed standalone utility that copies 3D library items to USB / flash drives
with full automation:
  * Select multiple disks or folders as copy targets.
  * Filters and copies assets containing 3D models (or preview assets).
  * Automatically unzips model archives directly into `<Asset>/model/` and cleans .zip.
  * Automatically copies the `orga+` desktop application to the disk root.
  * Flexible copy mechanisms:
      - Storage Limit (GB or MB)
      - Exact Item Count
      - Select All in Chosen Categories
      - Round-Robin Balanced distribution across chosen categories / subcategories
      - Auto-Fit to target disk capacity
  * Hierarchical Category & Subcategory tree selection with real-time size & count indicators.
  * Prominent real-time display of Current Size of Selected Objects and disk space status.
  * Intelligent library scanning: supports root library directories, single Category folders
    (e.g. 'Scenes'), and arbitrary subcategory hierarchies.
  * Real-time progress bar with transfer rate (MB/s), ETA, and pause/resume/stop controls.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import zipfile
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# --------------------------------------------------------------------------
# Configuration & Formats
# --------------------------------------------------------------------------

MODEL_EXTS = {
    ".skp", ".obj", ".fbx", ".blend", ".zip", ".rar", ".7z",
    ".3ds", ".max", ".c4d", ".glb", ".gltf", ".stl", ".dae", ".dxf",
}

ARCHIVE_EXTS = {".zip", ".rar", ".7z", ".tar", ".gz"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

# 16 MiB chunks: maximizes sustained sequential write speed on USB flash drives
CHUNK_SIZE = 16 * 1024 * 1024
DEFAULT_WORKERS = 1


class CopyStopped(Exception):
    """Raised internally to unwind workers when the user hits Stop."""


# --------------------------------------------------------------------------
# Data Models
# --------------------------------------------------------------------------

@dataclass
class CopyItem:
    job: str               # Category (e.g. Scenes, Furniture)
    category: str          # Subcategory (e.g. Exteriors, Chairs)
    asset: Path            # Path to asset folder
    title: str             # Asset display title
    total_bytes: int = 0
    files_count: int = 0
    model_format: str = ""
    is_zip: bool = False
    model_path: Optional[Path] = None
    custom_files: Optional[List[Path]] = None
    item_id: Optional[str] = None

    @property
    def is_archive(self) -> bool:
        return self.is_zip or (self.model_path is not None and self.model_path.suffix.lower() in ARCHIVE_EXTS)

    @property
    def category_name(self) -> str:
        return self.job

    @property
    def subcategory_name(self) -> str:
        return self.category

    @property
    def rel_parts(self) -> Tuple[str, str, str]:
        suffix = self.title if self.custom_files else self.asset.name
        return (self.job, self.category, suffix)

    @property
    def unique_id(self) -> str:
        if self.item_id:
            return self.item_id
        suffix = self.title if self.custom_files else self.asset.name
        return f"{self.job}/{self.category}/{suffix}"


@dataclass
class VolumeInfo:
    label: str
    path: str
    free: int
    total: int
    is_removable: bool = False


# --------------------------------------------------------------------------
# Format Helpers
# --------------------------------------------------------------------------

def human_size(n: float) -> str:
    """Format bytes into human-readable string (e.g. 14.2 GB)."""
    if n <= 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def _visible(p: Path) -> bool:
    return not p.name.startswith(".")


# --------------------------------------------------------------------------
# Library Scanning & Model Detection
# --------------------------------------------------------------------------

def has_model(asset: Path) -> bool:
    """True when the asset folder contains a model or archive file (in model/ dir or asset root)."""
    model_dir = asset / "model"
    if model_dir.is_dir():
        for f in model_dir.iterdir():
            if f.is_file() and _visible(f):
                ext = f.suffix.lower()
                if ext in MODEL_EXTS or ext in ARCHIVE_EXTS:
                    return True
        return False

    for f in asset.iterdir():
        if f.is_file() and _visible(f):
            ext = f.suffix.lower()
            if ext in MODEL_EXTS or ext in ARCHIVE_EXTS:
                return True
    return False


def get_model_details(asset: Path) -> Tuple[str, bool, Optional[Path]]:
    """Return (model_format, is_zip, model_file_path) for an asset."""
    model_dir = asset / "model"
    candidates: List[Path] = []

    if model_dir.is_dir():
        for f in sorted(model_dir.iterdir()):
            if f.is_file() and _visible(f):
                ext = f.suffix.lower()
                if ext in MODEL_EXTS or ext in ARCHIVE_EXTS:
                    candidates.append(f)

    if not candidates:
        for f in sorted(asset.iterdir()):
            if f.is_file() and _visible(f):
                ext = f.suffix.lower()
                if ext in MODEL_EXTS or ext in ARCHIVE_EXTS:
                    candidates.append(f)

    if not candidates:
        return ("", False, None)

    # Prefer native 3D formats (.skp, .fbx, .obj, .blend, etc.) over archive formats (.zip, .rar), else first
    native_formats = {".skp", ".fbx", ".obj", ".blend", ".3ds", ".max", ".c4d", ".glb", ".gltf", ".stl", ".dae", ".dxf"}
    natives = [c for c in candidates if c.suffix.lower() in native_formats]
    primary = natives[0] if natives else candidates[0]

    fmt = primary.suffix.lower().lstrip(".").upper()
    is_zip = primary.suffix.lower() in ARCHIVE_EXTS
    return (fmt, is_zip, primary)


def _is_asset_directory(p: Path) -> bool:
    """True if directory p looks like an individual asset folder."""
    if not p.is_dir() or not _visible(p):
        return False
    if p.name.lower() in ("model", "images", "textures", "__macosx"):
        return False

    # 1. Has model/ subfolder
    if (p / "model").is_dir():
        return True

    # 2. Has meta.json
    if (p / "meta.json").exists():
        return True

    # 3. Inspect directory contents
    try:
        has_img = False
        has_model_file = False
        subdirs: List[Path] = []
        for child in p.iterdir():
            if not _visible(child):
                continue
            if child.is_file():
                ext = child.suffix.lower()
                if ext in MODEL_EXTS or ext in ARCHIVE_EXTS:
                    has_model_file = True
                elif ext in IMAGE_EXTS:
                    has_img = True
            elif child.is_dir() and child.name.lower() not in ("model", "images", "textures", "__macosx"):
                subdirs.append(child)

        if has_model_file:
            return True
        if has_img and not subdirs:
            return True
    except (PermissionError, OSError):
        pass

    return False


def match_model_for_image(img_path: Path, candidate_models: List[Path]) -> Optional[Path]:
    """Matches a preview image to its corresponding 3D model file by stem, prefix, or ID."""
    if not candidate_models:
        return None
    img_stem = img_path.stem.lower()
    for m in candidate_models:
        if m.stem.lower() == img_stem:
            return m
    for m in candidate_models:
        m_stem = m.stem.lower()
        if m_stem in img_stem or img_stem in m_stem:
            return m
    img_nums = re.findall(r"\d+", img_stem)
    if img_nums:
        for m in candidate_models:
            m_nums = re.findall(r"\d+", m.stem.lower())
            if any(num in m_nums for num in img_nums if len(num) >= 2):
                return m
    if len(candidate_models) == 1:
        return candidate_models[0]
    return None


def find_asset_directories(root: Path) -> List[Path]:
    """Find all asset directories under root, avoiding recursing inside asset directories."""
    root = Path(root).resolve()
    if not root.is_dir():
        return []

    if _is_asset_directory(root):
        return [root]

    assets: List[Path] = []

    def _walk(curr: Path, depth: int):
        if depth > 20:
            return
        subdirs: List[Path] = []
        try:
            for child in sorted(curr.iterdir()):
                if child.is_dir() and _visible(child) and child.name.lower() not in ("model", "images", "textures", "__macosx"):
                    subdirs.append(child)
        except (PermissionError, OSError):
            return

        for d in subdirs:
            if _is_asset_directory(d):
                assets.append(d)
            else:
                _walk(d, depth + 1)

    _walk(root, 0)
    return assets


def get_asset_hierarchy(root: Path, asset_dir: Path) -> Tuple[str, str, str]:
    """
    Given an asset directory and the library root, determine:
    (Category, Subcategory, AssetTitle/FolderName).
    Handles arbitrary nested hierarchies (depth 1, 2, 3, 4, 5, 6+).
    """
    root = Path(root).resolve()
    asset_dir = Path(asset_dir).resolve()
    try:
        rel = asset_dir.relative_to(root)
        parts = rel.parts
    except ValueError:
        parts = (asset_dir.name,)

    if len(parts) == 0:
        cat = root.name or "General"
        subcat = "General"
        asset_name = asset_dir.name
    elif len(parts) == 1:
        cat = root.parent.name if (root.parent and root.parent.name and root.parent != root) else root.name
        subcat = root.name
        asset_name = parts[0]
    elif len(parts) == 2:
        cat = root.name
        subcat = parts[0]
        asset_name = parts[1]
    else:
        cat = parts[0]
        subcat = " / ".join(p.strip() for p in parts[1:-1])
        asset_name = parts[-1]

    return cat, subcat, asset_name


def _iter_asset_files(asset: Path) -> List[Path]:
    """Iterate all non-hidden files inside an asset directory."""
    out: List[Path] = []
    for p in asset.rglob("*"):
        if not p.is_file():
            continue
        if any(part.startswith(".") for part in p.relative_to(asset).parts):
            continue
        out.append(p)
    return out


def scan_items(root: Path, models_only: bool = True) -> Tuple[List[CopyItem], int]:
    """
    Dynamically scan root for all 3D assets and preview images regardless of folder depth.
    Supports:
      - Deeply nested subfolders (depth 1, 2, 3, 4, 5, 6+ levels).
      - Dedicated single asset folders.
      - Multi-item subcategory folders with multiple preview images & models.
    """
    items: List[CopyItem] = []
    skipped = 0
    root = Path(root).resolve()
    if not root.is_dir():
        return items, skipped

    skip_dirs = {"model", "images", "textures", "__macosx", ".git", "venv", ".venv"}

    # Track folders we already handled to prevent duplicate child scans
    handled_dirs: Set[Path] = set()

    for root_str, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in skip_dirs]
        curr_dir = Path(root_str)
        if any(h in curr_dir.parents for h in handled_dirs):
            continue

        raw_imgs = [
            curr_dir / f for f in files
            if not f.startswith(".") and Path(f).suffix.lower() in IMAGE_EXTS
        ]
        imgs_sub = curr_dir / "images"
        if imgs_sub.is_dir():
            try:
                for f in imgs_sub.iterdir():
                    if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in IMAGE_EXTS:
                        raw_imgs.append(f)
            except (PermissionError, OSError):
                pass

        models: List[Path] = []
        model_sub = curr_dir / "model"
        if model_sub.is_dir():
            try:
                for f in model_sub.iterdir():
                    if f.is_file() and not f.name.startswith(".") and (f.suffix.lower() in MODEL_EXTS or f.suffix.lower() in ARCHIVE_EXTS):
                        models.append(f)
            except (PermissionError, OSError):
                pass
        for f in files:
            if not f.startswith("."):
                ext = Path(f).suffix.lower()
                if ext in MODEL_EXTS or ext in ARCHIVE_EXTS:
                    models.append(curr_dir / f)

        has_meta = (curr_dir / "meta.json").exists()
        if not raw_imgs and not models and not has_meta:
            continue

        try:
            rel_parts = curr_dir.relative_to(root).parts
        except ValueError:
            rel_parts = (curr_dir.name,)

        # Determine whether curr_dir is a multi-item folder
        is_multi = False
        if len(models) > 1 and len(raw_imgs) > 1 and not has_meta and not imgs_sub.is_dir():
            matched_count = sum(1 for img in raw_imgs if match_model_for_image(img, models) is not None)
            if matched_count >= 2:
                is_multi = True

        if is_multi:
            handled_dirs.add(curr_dir)
            if len(rel_parts) == 0:
                cat = root.name or "General"
                subcat = "General"
            elif len(rel_parts) == 1:
                cat = root.name
                subcat = rel_parts[0]
            else:
                cat = rel_parts[0]
                subcat = " / ".join(p.strip() for p in rel_parts[1:])

            for img in raw_imgs:
                matched_m = match_model_for_image(img, models)
                if models_only and not matched_m:
                    skipped += 1
                    continue

                item_title = img.stem.replace("_", " ").replace("-", " ").strip().title()
                custom_files = [img]
                if matched_m:
                    custom_files.append(matched_m)
                    fmt = matched_m.suffix.lower().lstrip(".").upper()
                    is_zip = matched_m.suffix.lower() in ARCHIVE_EXTS
                else:
                    fmt = ""
                    is_zip = False

                size = sum(f.stat().st_size for f in custom_files if f.exists())
                items.append(
                    CopyItem(
                        job=cat,
                        category=subcat,
                        asset=curr_dir,
                        title=item_title,
                        total_bytes=size,
                        files_count=len(custom_files),
                        model_format=fmt,
                        is_zip=is_zip,
                        model_path=matched_m,
                        custom_files=custom_files,
                        item_id=f"{cat}/{subcat}/{img.stem}",
                    )
                )
        elif _is_asset_directory(curr_dir):
            handled_dirs.add(curr_dir)
            if models_only and not models:
                skipped += 1
                continue

            cat, subcat, default_title = get_asset_hierarchy(root, curr_dir)
            fmt, is_zip, model_p = get_model_details(curr_dir)

            title = default_title
            meta_p = curr_dir / "meta.json"
            if meta_p.exists():
                try:
                    meta_data = json.loads(meta_p.read_text(encoding="utf-8"))
                    if meta_data.get("title"):
                        title = meta_data.get("title")
                except Exception:
                    pass

            files = _iter_asset_files(curr_dir)
            size = sum(f.stat().st_size for f in files)

            items.append(
                CopyItem(
                    job=cat,
                    category=subcat,
                    asset=curr_dir,
                    title=title,
                    total_bytes=size,
                    files_count=len(files),
                    model_format=fmt,
                    is_zip=is_zip,
                    model_path=model_p,
                )
            )

    return items, skipped


# --------------------------------------------------------------------------
# Selection & Limit Utilities
# --------------------------------------------------------------------------

def select_exact_count(items: List[CopyItem], count: int) -> Set[str]:
    """Return unique_ids for the first `count` items."""
    count = max(0, min(count, len(items)))
    return {it.unique_id for it in items[:count]}


def select_storage_limit(items: List[CopyItem], limit_bytes: int) -> Set[str]:
    """Return unique_ids for items totaling up to `limit_bytes`."""
    selected: Set[str] = set()
    current_bytes = 0
    for it in items:
        if current_bytes + it.total_bytes <= limit_bytes:
            selected.add(it.unique_id)
            current_bytes += it.total_bytes
    return selected


def select_fit_disk(
    items: List[CopyItem],
    disk_free_bytes: int,
    safety_margin_bytes: int = 500 * 1024 * 1024,
) -> Set[str]:
    """Return unique_ids for items that fit within disk free space minus margin."""
    usable = max(0, disk_free_bytes - safety_margin_bytes)
    return select_storage_limit(items, usable)


def select_balanced_mechanism(
    items: List[CopyItem],
    mode: str,  # "count", "size", or "storage"
    limit_value: float,
    strategy: str = "round_robin",
    included_categories: Optional[Set[str]] = None,
    included_subcategories: Optional[Set[Tuple[str, str]]] = None,
) -> Set[str]:
    """
    Select items balancing across chosen categories / subcategories (round-robin).
    Picks items round-robin from each category / subcategory until the target
    GB size or file count limit is reached.
    """
    available = list(items)
    if included_categories is not None:
        available = [it for it in available if it.job in included_categories]
    if included_subcategories is not None:
        available = [it for it in available if (it.job, it.category) in included_subcategories]

    groups: Dict[str, List[CopyItem]] = {}
    for it in available:
        groups.setdefault(it.job, []).append(it)

    selected_ids: Set[str] = set()
    normalized_mode = "storage" if mode in ("size", "storage") else "count"

    if normalized_mode == "count":
        target_count = max(0, int(limit_value))
        queues = {k: list(v) for k, v in groups.items()}
        active_keys = list(groups.keys())
        while active_keys and len(selected_ids) < target_count:
            for k in list(active_keys):
                if not queues[k]:
                    active_keys.remove(k)
                    continue
                item = queues[k].pop(0)
                selected_ids.add(item.unique_id)
                if len(selected_ids) >= target_count:
                    break
        return selected_ids

    else:  # size / storage
        target_bytes = max(0, int(limit_value))
        current_bytes = 0
        queues = {k: list(v) for k, v in groups.items()}
        active_keys = list(groups.keys())

        while active_keys:
            added_any = False
            for k in list(active_keys):
                if not queues[k]:
                    active_keys.remove(k)
                    continue
                item = queues[k][0]
                if current_bytes + item.total_bytes <= target_bytes:
                    queues[k].pop(0)
                    selected_ids.add(item.unique_id)
                    current_bytes += item.total_bytes
                    added_any = True
                else:
                    found_smaller = False
                    for idx, candidate in enumerate(queues[k]):
                        if current_bytes + candidate.total_bytes <= target_bytes:
                            queues[k].pop(idx)
                            selected_ids.add(candidate.unique_id)
                            current_bytes += candidate.total_bytes
                            added_any = True
                            found_smaller = True
                            break
                    if not found_smaller:
                        active_keys.remove(k)

            if not added_any:
                break
        return selected_ids


select_balanced_items = select_balanced_mechanism



# --------------------------------------------------------------------------
# App Discovery & Copying
# --------------------------------------------------------------------------

def find_orga_app(custom_path: Optional[str] = None) -> Optional[Path]:
    """Find the orga+ desktop app executable or .app bundle."""
    if custom_path:
        p = Path(custom_path).resolve()
        if p.exists():
            return p

    here = Path(__file__).resolve().parent.parent
    dist_dir = here / "dist"

    candidates = []
    if sys.platform == "darwin":
        candidates.extend([
            dist_dir / "orga+.app",
            dist_dir / "olga+.app",
            here / "orga+.app",
            here / "olga+.app",
            Path("/Applications/orga+.app"),
            Path("/Applications/olga+.app"),
            dist_dir / "orga+",
            dist_dir / "olga+",
        ])
    elif sys.platform == "win32":
        candidates.extend([
            dist_dir / "orga+.exe",
            dist_dir / "olga+.exe",
            dist_dir / "orga+ Copy Tool.exe",
            dist_dir / "orga+-Portable",
            dist_dir / "olga+-Portable",
            here / "orga+.exe",
            here / "olga+.exe",
        ])
    else:
        candidates.extend([
            dist_dir / "orga+",
            dist_dir / "olga+",
            here / "orga+",
            here / "olga+",
        ])

    for cand in candidates:
        if cand.exists():
            return cand
    return None


def get_app_size(app_path: Optional[Path]) -> int:
    """Calculate total size of the app."""
    if not app_path or not app_path.exists():
        return 0
    if app_path.is_file():
        return app_path.stat().st_size
    return sum(
        f.stat().st_size
        for f in app_path.rglob("*")
        if f.is_file() and not f.is_symlink()
    )


# --------------------------------------------------------------------------
# Pause / Stop Controller
# --------------------------------------------------------------------------

class CopyController:
    def __init__(self) -> None:
        self._paused = threading.Event()
        self._stop = threading.Event()

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def stop(self) -> None:
        self._stop.set()
        self._paused.clear()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def checkpoint(self) -> None:
        """Block while paused; raise CopyStopped when stopping."""
        if self._stop.is_set():
            raise CopyStopped()
        while self._paused.is_set():
            if self._stop.is_set():
                raise CopyStopped()
            time.sleep(0.05)


# --------------------------------------------------------------------------
# Fast Copy & Zip Extraction Engine
# --------------------------------------------------------------------------

def _fast_copy(
    src: Path,
    dst: Path,
    ctrl: CopyController,
    on_chunk: Callable[[int], None],
) -> str:
    """Copy one file with chunked streaming and graceful cleanup on stop."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        try:
            dst.unlink()
        except OSError:
            pass

    try:
        with open(src, "rb", buffering=0) as fsrc, open(dst, "wb", buffering=0) as fdst:
            while True:
                ctrl.checkpoint()
                buf = fsrc.read(CHUNK_SIZE)
                if not buf:
                    break
                fdst.write(buf)
                on_chunk(len(buf))

        try:
            shutil.copystat(src, dst)
        except OSError:
            pass

        if dst.stat().st_size != src.stat().st_size:
            raise IOError(f"size mismatch after copy: {src}")
    except BaseException:
        if dst.exists():
            try:
                dst.unlink()
            except OSError:
                pass
        raise
    return "buffered"


def normalize_model_directory(target_model_dir: Path, archive_name: str = "") -> None:
    """
    Normalizes the extracted model directory:
      1. Purges archive files (.zip, .rar, .7z, .tar, .gz) from model/ and parent asset dir.
      2. Removes metadata junk (__MACOSX, .DS_Store, Thumbs.db, desktop.ini).
      3. Peels back single-wrapper directories iteratively so model files sit directly in model/.
      4. If no .skp file is at the root of model/, locates any .skp file in subdirectories
         and promotes it directly to model/.
      5. Cleans up any remaining empty subdirectories.
    """
    target_model_dir = Path(target_model_dir).resolve()
    if not target_model_dir.is_dir():
        return

    # 1. Clean up archives from model/ and parent asset directory
    for d in (target_model_dir, target_model_dir.parent):
        if not d.is_dir():
            continue
        for ext in ("*.zip", "*.rar", "*.7z", "*.tar", "*.gz"):
            for arch in d.glob(ext):
                try:
                    arch.unlink()
                except OSError:
                    pass
        if archive_name:
            af = d / archive_name
            if af.exists():
                try:
                    af.unlink()
                except OSError:
                    pass

    # 2. Remove metadata junk
    for macosx in list(target_model_dir.rglob("__MACOSX")):
        if macosx.is_dir():
            shutil.rmtree(macosx, ignore_errors=True)
    for junk in list(target_model_dir.rglob(".DS_Store")) + list(target_model_dir.rglob("Thumbs.db")) + list(target_model_dir.rglob("desktop.ini")):
        try:
            junk.unlink()
        except OSError:
            pass

    # 3. Peel back single-wrapper directories iteratively
    while True:
        entries = [e for e in target_model_dir.iterdir() if not e.name.startswith(".")]
        if len(entries) == 1 and entries[0].is_dir():
            wrapper = entries[0]
            for child in list(wrapper.iterdir()):
                dest = target_model_dir / child.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest, ignore_errors=True)
                    else:
                        dest.unlink()
                shutil.move(str(child), str(dest))
            shutil.rmtree(str(wrapper), ignore_errors=True)
        else:
            break

    # 4. If no .skp file sits at root of model/, find any .skp in subdirectories and promote to root
    root_skp = [f for f in target_model_dir.iterdir() if f.is_file() and f.suffix.lower() == ".skp"]
    if not root_skp:
        sub_skps = [f for f in target_model_dir.rglob("*.skp") if f.is_file() and not f.name.startswith(".")]
        for s in sub_skps:
            dest_skp = target_model_dir / s.name
            if not dest_skp.exists():
                shutil.move(str(s), str(dest_skp))

    # 5. Clean up empty subdirectories
    for p in sorted(target_model_dir.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            try:
                p.rmdir()
            except OSError:
                pass


def safe_extract_archive(
    archive_path: Path,
    target_model_dir: Path,
    ctrl: CopyController,
    on_chunk: Callable[[int], None],
    log_cb: Optional[Callable[[str], None]] = None,
) -> int:
    """
    Extract archive (.zip, .rar, .7z) directly into target_model_dir.
    Promotes the model's .skp file directly to /model/, strips single wrapper directories,
    and guarantees no archive file is left in target_model_dir or asset root.
    """
    log = log_cb or (lambda m: None)
    archive_path = Path(archive_path).resolve()
    target_model_dir = Path(target_model_dir).resolve()
    target_model_dir.mkdir(parents=True, exist_ok=True)
    archive_size = archive_path.stat().st_size if archive_path.exists() else 0
    ext = archive_path.suffix.lower()

    extracted = False
    err_msgs: List[str] = []

    # 1. For .zip archives, try native zipfile first (fast, pure Python, streaming chunks)
    if ext == ".zip":
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                members = [
                    m for m in zf.infolist()
                    if not m.filename.startswith("__MACOSX/")
                    and not Path(m.filename).name.startswith(".")
                ]
                for member in members:
                    ctrl.checkpoint()
                    if member.is_dir():
                        continue

                    rel_name = member.filename
                    dest_file = (target_model_dir / rel_name).resolve()
                    # Security: prevent zip-slip
                    if not str(dest_file).startswith(str(target_model_dir)):
                        continue

                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member, "r") as src_stream, open(dest_file, "wb") as dst_stream:
                        while True:
                            ctrl.checkpoint()
                            buf = src_stream.read(CHUNK_SIZE)
                            if not buf:
                                break
                            dst_stream.write(buf)
            extracted = True
        except Exception as e:
            err_msgs.append(f"zipfile: {e}")

    # 2. Try py7zz (bundled universal 7zz binary: supports RAR1-5, 7Z, ZIP, TAR, GZ)
    if not extracted:
        try:
            import py7zz
            ctrl.checkpoint()
            py7zz.extract_archive(archive_path, output_dir=target_model_dir, overwrite=True)
            extracted = True
        except Exception as e:
            err_msgs.append(f"py7zz: {e}")

    # 3. Fallback: System 7z / 7zz / 7za CLI
    if not extracted:
        for cmd in ("7zz", "7z", "7za"):
            cmd_path = shutil.which(cmd)
            if cmd_path:
                try:
                    ctrl.checkpoint()
                    res = subprocess.run(
                        [cmd_path, "x", str(archive_path), f"-o{target_model_dir}", "-y"],
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    if res.returncode == 0:
                        extracted = True
                        break
                    else:
                        err_msgs.append(f"{cmd} (code {res.returncode}): {res.stderr.strip()[:80]}")
                except Exception as e:
                    err_msgs.append(f"{cmd}: {e}")

    # 4. Fallback: macOS / Linux bsdtar / tar
    if not extracted and sys.platform != "win32":
        bsdtar = shutil.which("bsdtar") or "/usr/bin/bsdtar"
        if os.path.exists(bsdtar):
            try:
                ctrl.checkpoint()
                res = subprocess.run(
                    [bsdtar, "-xf", str(archive_path), "-C", str(target_model_dir)],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                if res.returncode == 0:
                    extracted = True
                else:
                    err_msgs.append(f"bsdtar (code {res.returncode}): {res.stderr.strip()[:80]}")
            except Exception as e:
                err_msgs.append(f"bsdtar: {e}")

    # 5. Fallback: unrar command
    if not extracted:
        unrar = shutil.which("unrar")
        if unrar:
            try:
                ctrl.checkpoint()
                res = subprocess.run(
                    [unrar, "x", "-o+", str(archive_path), str(target_model_dir)],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                if res.returncode == 0:
                    extracted = True
                else:
                    err_msgs.append(f"unrar (code {res.returncode})")
            except Exception as e:
                err_msgs.append(f"unrar: {e}")

    if not extracted:
        raise RuntimeError(f"Extraction failed for {archive_path.name}: {'; '.join(err_msgs)}")

    # 6. Normalize model directory (promote .skp to model/ root, peel wrappers, clean archives)
    normalize_model_directory(target_model_dir, archive_name=archive_path.name)
    on_chunk(archive_size)
    return archive_size


def safe_extract_zip(
    zip_path: Path,
    target_model_dir: Path,
    ctrl: CopyController,
    on_chunk: Callable[[int], None],
    log_cb: Optional[Callable[[str], None]] = None,
) -> int:
    """Backwards-compatible extraction function."""
    return safe_extract_archive(
        zip_path,
        target_model_dir,
        ctrl,
        on_chunk=on_chunk,
        log_cb=log_cb,
    )


def copy_orga_app(
    app_path: Path,
    dest_root: Path,
    ctrl: CopyController,
    on_chunk: Callable[[int], None],
    log_cb: Callable[[str], None],
    skip_existing: bool = True,
) -> int:
    """Copy the orga+ app bundle or binary to destination disk root."""
    dest_app = dest_root / app_path.name
    total_copied = 0

    if app_path.is_file():
        if skip_existing and dest_app.exists() and dest_app.stat().st_size == app_path.stat().st_size:
            log_cb(f"App already up-to-date on {dest_root.name}: {app_path.name}")
            return 0
        log_cb(f"Copying app {app_path.name} -> {dest_root}")
        _fast_copy(app_path, dest_app, ctrl, on_chunk)
        return app_path.stat().st_size

    # Directory app (.app bundle or portable directory)
    log_cb(f"Copying app bundle {app_path.name} -> {dest_root}")
    for p in app_path.rglob("*"):
        ctrl.checkpoint()
        rel = p.relative_to(app_path)
        dst = dest_app / rel

        if p.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        elif p.is_symlink():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            try:
                os.symlink(os.readlink(p), dst)
            except OSError:
                pass
        elif p.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            size = p.stat().st_size
            if skip_existing and dst.exists() and dst.stat().st_size == size:
                on_chunk(size)
                continue
            _fast_copy(p, dst, ctrl, on_chunk)
            total_copied += size

    # On macOS, ensure execute permissions on Contents/MacOS/*
    if sys.platform == "darwin" and (dest_app / "Contents" / "MacOS").is_dir():
        for b in (dest_app / "Contents" / "MacOS").iterdir():
            if b.is_file():
                try:
                    b.chmod(b.stat().st_mode | 0o111)
                except OSError:
                    pass

    log_cb(f"App bundle {app_path.name} copied successfully.")
    return total_copied


# --------------------------------------------------------------------------
# Progress Tracker
# --------------------------------------------------------------------------

@dataclass
class Progress:
    total: int = 0
    copied: int = 0
    items_done: int = 0
    items_total: int = 0
    current_item: str = ""
    current_file: str = ""
    started: float = field(default_factory=time.monotonic)
    _samples: deque = field(default_factory=lambda: deque(maxlen=40))
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        now = time.monotonic()
        self._samples.append((now, self.copied))

    def add_bytes(self, n: int) -> None:
        with self._lock:
            self.copied += n
            now = time.monotonic()
            if not self._samples or (now - self._samples[-1][0]) >= 0.05:
                self._samples.append((now, self.copied))

    def snapshot(self) -> Tuple[int, int, float]:
        with self._lock:
            copied = self.copied
            samples = list(self._samples)

        now = time.monotonic()
        speed = 0.0
        if len(samples) >= 2:
            cutoff = now - 2.0
            idx = 0
            while idx < len(samples) - 1 and samples[idx][0] < cutoff:
                idx += 1
            dt = samples[-1][0] - samples[idx][0]
            db = samples[-1][1] - samples[idx][1]
            if dt >= 0.2 and db >= 0:
                speed = db / dt
            else:
                elapsed = max(now - self.started, 1e-6)
                speed = copied / elapsed
        else:
            elapsed = max(now - self.started, 1e-6)
            speed = copied / elapsed

        return copied, self.total, max(0.0, speed)


# --------------------------------------------------------------------------
# Multi-Disk Copy Runner
# --------------------------------------------------------------------------

def run_copy(
    items: List[CopyItem],
    dest_root: Path,
    ctrl: CopyController,
    *,
    workers: int = DEFAULT_WORKERS,
    skip_existing: bool = True,
    auto_copy_app: bool = True,
    app_path: Optional[Path] = None,
    unzip_models: bool = True,
    progress_cb: Optional[Callable[[Tuple[int, int, float], str, str], None]] = None,
    log_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    """Execute copying of selected items and optional app to a single destination root."""
    dest_root = Path(dest_root).resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    log = log_cb or (lambda m: None)

    # Calculate overall total payload size
    items_total_bytes = sum(it.total_bytes for it in items)
    app_bytes = get_app_size(app_path) if (auto_copy_app and app_path) else 0
    grand_total = items_total_bytes + app_bytes

    progress = Progress(total=grand_total, items_total=len(items))
    last_emit = [0.0]

    def emit(item_label: str, file_label: str, force: bool = False) -> None:
        if not progress_cb:
            return
        now = time.monotonic()
        if not force and (now - last_emit[0]) < 0.1:
            return
        last_emit[0] = now
        copied, tot, speed = progress.snapshot()
        progress_cb((copied, tot, speed), item_label, file_label)

    def on_chunk(n: int) -> None:
        progress.add_bytes(n)
        emit(progress.current_item, progress.current_file)

    free = shutil.disk_usage(dest_root).free
    if grand_total > free:
        raise IOError(
            f"Not enough space on {dest_root.name}: need {human_size(grand_total)}, "
            f"free {human_size(free)}"
        )

    log(f"Starting copy to {dest_root} ({human_size(grand_total)} across {len(items)} items)")

    # 1. Auto-copy orga+ app if requested
    if auto_copy_app and app_path and app_path.exists():
        ctrl.checkpoint()
        progress.current_item = "orga+ App"
        progress.current_file = app_path.name
        emit(progress.current_item, progress.current_file, force=True)
        try:
            copy_orga_app(
                app_path,
                dest_root,
                ctrl,
                on_chunk=on_chunk,
                log_cb=log,
                skip_existing=skip_existing,
            )
        except Exception as e:
            log(f"App copy warning: {e}")

    # 2. Copy Items (Assets)
    for it in items:
        ctrl.checkpoint()
        item_label = f"{it.job} / {it.category} / {it.title}"
        progress.current_item = item_label

        subcat_parts = [p.strip() for p in it.category.split("/") if p.strip()]
        dest_asset = dest_root / it.job
        for sp in subcat_parts:
            dest_asset = dest_asset / sp
        asset_folder_name = it.title if it.custom_files is not None else it.asset.name
        dest_asset = dest_asset / asset_folder_name
        dest_model_dir = dest_asset / "model"
        dest_asset.mkdir(parents=True, exist_ok=True)
        dest_model_dir.mkdir(parents=True, exist_ok=True)

        asset_files = it.custom_files if it.custom_files is not None else _iter_asset_files(it.asset)

        # Separate model files from preview images and metadata
        model_files = [f for f in asset_files if f.suffix.lower() in MODEL_EXTS or f.suffix.lower() in ARCHIVE_EXTS]
        other_files = [f for f in asset_files if f not in model_files]

        # Copy previews and metadata
        for f in other_files:
            ctrl.checkpoint()
            if it.custom_files is not None:
                dst_f = dest_asset / f.name
            else:
                rel = f.relative_to(it.asset)
                dst_f = dest_asset / rel
            size = f.stat().st_size
            progress.current_file = f.name

            if skip_existing and dst_f.exists() and dst_f.stat().st_size == size:
                on_chunk(size)
                continue

            emit(item_label, f.name, force=True)
            _fast_copy(f, dst_f, ctrl, on_chunk)

        # Handle model files
        for mf in model_files:
            ctrl.checkpoint()
            ext = mf.suffix.lower()
            is_archive = ext in ARCHIVE_EXTS
            progress.current_file = mf.name

            if is_archive and unzip_models:
                # Check if model has already been extracted on target disk
                has_extracted_model = any(
                    f.is_file() and (f.suffix.lower() == ".skp" or f.suffix.lower() in MODEL_EXTS)
                    for f in dest_model_dir.iterdir()
                ) if dest_model_dir.is_dir() else False

                if skip_existing and has_extracted_model:
                    on_chunk(mf.stat().st_size)
                    continue

                progress.current_file = f"Extracting {mf.name} -> /model/"
                emit(item_label, progress.current_file, force=True)
                log(f"Extracting model archive for {it.title} ({mf.name}) -> model/")
                try:
                    safe_extract_archive(
                        mf,
                        dest_model_dir,
                        ctrl,
                        on_chunk=on_chunk,
                        log_cb=log,
                    )
                except Exception as e:
                    log(f"Extraction failed for {mf.name} ({e}), falling back to direct copy")
                    dst_m = dest_model_dir / mf.name
                    size = mf.stat().st_size
                    if skip_existing and dst_m.exists() and dst_m.stat().st_size == size:
                        on_chunk(size)
                        continue
                    emit(item_label, mf.name, force=True)
                    _fast_copy(mf, dst_m, ctrl, on_chunk)
            else:
                dst_m = dest_model_dir / mf.name
                size = mf.stat().st_size
                if skip_existing and dst_m.exists() and dst_m.stat().st_size == size:
                    on_chunk(size)
                    continue

                emit(item_label, mf.name, force=True)
                _fast_copy(mf, dst_m, ctrl, on_chunk)

        progress.items_done += 1
        progress.current_file = "Done"
        emit(item_label, "Done", force=True)

    progress.current_file = "Complete"
    emit(progress.current_item, "Complete", force=True)
    log(f"Finished copying to {dest_root.name} successfully.")
    copied, tot, _ = progress.snapshot()
    return {
        "dest": str(dest_root),
        "items_done": progress.items_done,
        "copied_bytes": copied,
        "total_bytes": tot,
        "stopped": False,
    }


def run_copy_multi(
    items: List[CopyItem],
    dests: List[Path],
    ctrl: CopyController,
    *,
    workers: int = DEFAULT_WORKERS,
    skip_existing: bool = True,
    auto_copy_app: bool = True,
    app_path: Optional[Path] = None,
    unzip_models: bool = True,
    progress_cb: Optional[Callable[[Tuple[int, int, float], str, str], None]] = None,
    log_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    """Sequential fan-out to multiple drives to ensure maximum USB write bandwidth."""
    dests = [Path(d) for d in dests]
    log = log_cb or (lambda m: None)
    results: List[dict] = []
    n = len(dests)

    items_total_bytes = sum(it.total_bytes for it in items)
    app_bytes = get_app_size(app_path) if (auto_copy_app and app_path) else 0
    disk_payload = items_total_bytes + app_bytes
    overall_total = disk_payload * n

    for i, dest in enumerate(dests, 1):
        if ctrl.stopped:
            break
        log(f"=== [Disk {i}/{n}] Starting export to {dest} ===")

        base_offset = (i - 1) * disk_payload

        def pcb(snap, item, fname, disk_idx=i, offset=base_offset):
            if progress_cb:
                disk_copied, disk_tot, speed = snap
                curr_copied = offset + disk_copied
                progress_cb((curr_copied, overall_total, speed), f"[Disk {disk_idx}/{n}] {item}", fname)

        try:
            r = run_copy(
                items,
                dest,
                ctrl,
                workers=workers,
                skip_existing=skip_existing,
                auto_copy_app=auto_copy_app,
                app_path=app_path,
                unzip_models=unzip_models,
                progress_cb=pcb,
                log_cb=log,
            )
            results.append(r)
        except CopyStopped:
            log(f"[Disk {i}/{n}] Stopped by user.")
            results.append({"dest": str(dest), "stopped": True})
            break
        except Exception as e:
            log(f"[Disk {i}/{n}] FAILED: {e}")
            results.append({"dest": str(dest), "error": str(e), "stopped": False})

        if r.get("stopped"):
            break

    return {"destinations": results, "stopped": ctrl.stopped}


# --------------------------------------------------------------------------
# Destination & Volume Listing
# --------------------------------------------------------------------------

def list_volumes() -> List[VolumeInfo]:
    """Discover mounted removable volumes and disks across macOS, Windows, Linux."""
    out: List[VolumeInfo] = []
    seen_paths: Set[str] = set()

    if sys.platform == "darwin":
        vol_base = Path("/Volumes")
        if vol_base.is_dir():
            for vol in sorted(vol_base.iterdir()):
                try:
                    resolved = str(vol.resolve())
                    if resolved in seen_paths:
                        continue
                    seen_paths.add(resolved)
                    u = shutil.disk_usage(vol)
                    is_removable = not (vol.name in ("Macintosh HD", "Macintosh HD - Data"))
                    out.append(VolumeInfo(vol.name, str(vol), u.free, u.total, is_removable))
                except OSError:
                    continue

    elif sys.platform == "win32":
        import string
        for letter in string.ascii_uppercase:
            drive_str = f"{letter}:\\"
            if os.path.exists(drive_str):
                try:
                    u = shutil.disk_usage(drive_str)
                    label = f"Drive ({letter}:)"
                    out.append(VolumeInfo(label, drive_str, u.free, u.total, letter != "C"))
                except OSError:
                    continue

    else:
        for base_str in ("/media", "/mnt", "/run/media"):
            base = Path(base_str)
            if not base.is_dir():
                continue
            for vol in sorted(base.rglob("*")):
                if vol.is_dir() and vol.parent == base:
                    try:
                        resolved = str(vol.resolve())
                        if resolved in seen_paths:
                            continue
                        seen_paths.add(resolved)
                        u = shutil.disk_usage(vol)
                        out.append(VolumeInfo(vol.name, str(vol), u.free, u.total, True))
                    except OSError:
                        continue

    return out


def default_source() -> str:
    """Determine default library source folder."""
    try:
        import config  # type: ignore
        if hasattr(config, "DATA_DIR") and Path(config.DATA_DIR).is_dir():
            return str(config.DATA_DIR)
    except Exception:
        pass

    here = Path(__file__).resolve().parent.parent
    for name in ("storage", "data", "feeds"):
        p = here / name
        if p.is_dir():
            return str(p)
    return str(here / "storage")


# --------------------------------------------------------------------------
# Modern Dark UI Theme Stylesheet
# --------------------------------------------------------------------------

MODERN_DARK_QSS = """
QWidget {
    background-color: #0A0E1A;
    color: #F8FAFC;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}

QGroupBox {
    background-color: #111827;
    border: 1px solid #26334D;
    border-radius: 10px;
    margin-top: 18px;
    font-weight: 700;
    font-size: 13px;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 12px;
    background-color: #1E293B;
    border: 1px solid #26334D;
    border-radius: 6px;
    color: #818CF8;
}

QPushButton {
    background-color: #1E293B;
    border: 1px solid #26334D;
    border-radius: 8px;
    color: #F8FAFC;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2D3D58;
    border-color: #6366F1;
}

QPushButton:pressed {
    background-color: #1E293B;
}

QPushButton:disabled {
    background-color: #161F30;
    border-color: #1F2A3F;
    color: #64748B;
}

QPushButton#primaryBtn {
    background-color: #6366F1;
    border: 1px solid #4F46E5;
    color: #FFFFFF;
    font-weight: 700;
}

QPushButton#primaryBtn:hover {
    background-color: #4F46E5;
}

QPushButton#primaryBtn:disabled {
    background-color: #3730A3;
    color: #94A3B8;
}

QPushButton#accentBtn {
    background-color: #312E81;
    border: 1px solid #4338CA;
    color: #C7D2FE;
    font-weight: 600;
}

QPushButton#accentBtn:hover {
    background-color: #3730A3;
    border-color: #6366F1;
}

QPushButton#pauseBtn {
    background-color: #D97706;
    border: 1px solid #B45309;
    color: #FFFFFF;
}

QPushButton#pauseBtn:hover {
    background-color: #B45309;
}

QPushButton#stopBtn {
    background-color: #DC2626;
    border: 1px solid #B91C1C;
    color: #FFFFFF;
}

QPushButton#stopBtn:hover {
    background-color: #B91C1C;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #161F30;
    border: 1px solid #26334D;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F8FAFC;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #6366F1;
}

QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

QListWidget, QTableWidget, QTreeWidget {
    background-color: #111827;
    border: 1px solid #26334D;
    border-radius: 8px;
    gridline-color: #1E293B;
    outline: none;
}

QListWidget::item, QTableWidget::item, QTreeWidget::item {
    padding: 5px 8px;
    border-bottom: 1px solid #161F30;
}

QListWidget::item:hover, QTableWidget::item:hover, QTreeWidget::item:hover {
    background-color: #1E293B;
}

QListWidget::item:selected, QTableWidget::item:selected, QTreeWidget::item:selected {
    background-color: #26334D;
    color: #FFFFFF;
}

QListWidget#disksList {
    background-color: #0E1524;
    border: 1px solid #26334D;
    border-radius: 8px;
    padding: 6px;
}

QListWidget#disksList::item {
    padding: 10px 12px;
    border: 1px solid #1E293B;
    background-color: #141C2E;
    border-radius: 6px;
    margin-bottom: 6px;
    color: #F8FAFC;
}

QListWidget#disksList::item:hover {
    background-color: #1A243B;
    border-color: #38BDF8;
}

QListWidget#disksList::item:selected {
    background-color: #1E2B47;
    border: 1px solid #6366F1;
}

QTabWidget::pane {
    border: 1px solid #26334D;
    background-color: #0E1524;
    border-radius: 8px;
    top: -1px;
    padding: 12px;
}

QTabBar::tab {
    background-color: #161F30;
    color: #94A3B8;
    border: 1px solid #26334D;
    border-bottom: none;
    padding: 9px 18px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 700;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #0E1524;
    color: #F8FAFC;
    border-top: 2px solid #6366F1;
}

QTabBar::tab:hover:!selected {
    background-color: #1A2438;
    color: #E2E8F0;
}

QHeaderView::section {
    background-color: #161F30;
    color: #94A3B8;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #26334D;
    border-bottom: 1px solid #26334D;
    font-weight: 700;
}

QProgressBar {
    background-color: #161F30;
    border: 1px solid #26334D;
    border-radius: 8px;
    text-align: center;
    color: #F8FAFC;
    font-weight: 700;
    height: 24px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
    border-radius: 7px;
}

QCheckBox, QRadioButton {
    spacing: 8px;
    color: #F8FAFC;
    font-weight: 500;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3B4B6E;
    border-radius: 4px;
    background-color: #161F30;
}

QRadioButton::indicator {
    border-radius: 9px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

QPlainTextEdit {
    background-color: #070A12;
    border: 1px solid #26334D;
    border-radius: 8px;
    font-family: "JetBrains Mono", Menlo, Monaco, "Courier New", monospace;
    font-size: 12px;
    color: #94A3B8;
    padding: 8px;
}

QScrollBar:vertical {
    background: #0A0E1A;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #26334D;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #6366F1;
}
"""


# --------------------------------------------------------------------------
# GUI Implementation
# --------------------------------------------------------------------------

def run_gui(source: str, initial_dest: str = "", workers: int = DEFAULT_WORKERS) -> int:
    from PySide6.QtCore import QObject, Qt, QThread, Signal, QUrl
    from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon
    from PySide6.QtWidgets import (
        QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog,
        QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
        QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
        QProgressBar, QPushButton, QRadioButton, QSpinBox, QSplitter, QTableWidget,
        QTableWidgetItem, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    )

    class Signals(QObject):
        progress = Signal(object, object, float, str, str)
        log = Signal(str)
        finished = Signal(dict)
        error = Signal(str)

    class CopyWorker(QThread):
        def __init__(
            self,
            items: List[CopyItem],
            dests: List[Path],
            ctrl: CopyController,
            workers: int,
            skip_existing: bool,
            auto_copy_app: bool,
            app_path: Optional[Path],
            unzip_models: bool,
            signals: Signals,
        ) -> None:
            super().__init__()
            self.items = items
            self.dests = dests
            self.ctrl = ctrl
            self.workers = workers
            self.skip_existing = skip_existing
            self.auto_copy_app = auto_copy_app
            self.app_path = app_path
            self.unzip_models = unzip_models
            self.signals = signals

        def run(self) -> None:
            try:
                summary = run_copy_multi(
                    self.items,
                    self.dests,
                    self.ctrl,
                    workers=self.workers,
                    skip_existing=self.skip_existing,
                    auto_copy_app=self.auto_copy_app,
                    app_path=self.app_path,
                    unzip_models=self.unzip_models,
                    progress_cb=lambda snap, item, fname: self.signals.progress.emit(
                        snap[0], snap[1], snap[2], item, fname
                    ),
                    log_cb=lambda msg: self.signals.log.emit(msg),
                )
                self.signals.finished.emit(summary)
            except Exception as e:
                self.signals.error.emit(str(e))

    # Shared State
    ctrl = CopyController()
    signals = Signals()
    state: Dict[str, Any] = {
        "source": source,
        "items": [],
        "volumes": [],
        "app_path": find_orga_app(),
        "auto_copy_app": True,
        "unzip_models": True,
        "skip_existing": True,
        "models_only": True,
        "workers": workers,
        "safety_margin_mb": 500,
        "mechanism_mode": "storage",
        "limit_storage_val": 16.0,
        "limit_storage_unit": "GB",
        "limit_count_val": 50,
        "balanced": True,
        "worker": None,
        "updating_table": False,
        "updating_tree": False,
    }

    # ----------------------------------------------------------------------
    # Tabbed Settings Modal Dialog
    # ----------------------------------------------------------------------

    class SettingsDialog(QDialog):
        """Spacious modal dialog housing all copy mechanisms, target disks, and preferences."""

        def __init__(self, parent: QWidget) -> None:
            super().__init__(parent)
            self.setWindowTitle("⚙️ Preferences, Limits && Target Disks")
            self.resize(740, 580)
            self.setMinimumSize(660, 500)
            self.setStyleSheet(MODERN_DARK_QSS)

            dlg_layout = QVBoxLayout(self)
            dlg_layout.setContentsMargins(18, 18, 18, 18)
            dlg_layout.setSpacing(14)

            # Header Banner
            header_lbl = QLabel("⚙️ Preferences, Limits && Automation Settings")
            header_lbl.setStyleSheet("font-size: 17px; font-weight: 800; color: #F8FAFC;")
            subtitle_lbl = QLabel(
                "Configure selection limits, target destination disks, application bundling, and transfer performance."
            )
            subtitle_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
            dlg_layout.addWidget(header_lbl)
            dlg_layout.addWidget(subtitle_lbl)

            # Tab Widget
            self.tabs = QTabWidget()
            dlg_layout.addWidget(self.tabs, 1)

            # --- Tab 0: Copy Mechanism & Limits ---
            tab_limits = QWidget()
            tl_layout = QVBoxLayout(tab_limits)
            tl_layout.setContentsMargins(14, 16, 14, 14)
            tl_layout.setSpacing(14)

            lim_box = QGroupBox("Copy Mechanism && Selection Rules")
            lim_box_layout = QVBoxLayout(lim_box)
            lim_box_layout.setContentsMargins(14, 16, 14, 14)
            lim_box_layout.setSpacing(10)

            self.mode_group = QButtonGroup(self)
            self.rb_storage = QRadioButton("By Storage Limit (GB / MB)")
            self.rb_count = QRadioButton("By Number of Files / Items")
            self.rb_all = QRadioButton("Select All in Chosen Categories")
            self.rb_storage.setChecked(True)
            self.mode_group.addButton(self.rb_storage)
            self.mode_group.addButton(self.rb_count)
            self.mode_group.addButton(self.rb_all)

            lim_box_layout.addWidget(self.rb_storage)

            storage_row = QHBoxLayout()
            storage_row.setContentsMargins(24, 0, 0, 4)
            self.storage_spin = QDoubleSpinBox()
            self.storage_spin.setRange(0.1, 100000.0)
            self.storage_spin.setValue(state.get("limit_storage_val", 16.0))
            self.storage_spin.setDecimals(1)
            self.storage_spin.setMinimumWidth(100)
            self.unit_combo = QComboBox()
            self.unit_combo.addItems(["GB", "MB"])
            self.unit_combo.setCurrentText(state.get("limit_storage_unit", "GB"))
            storage_row.addWidget(QLabel("Limit:"))
            storage_row.addWidget(self.storage_spin)
            storage_row.addWidget(self.unit_combo)
            storage_row.addStretch(1)
            lim_box_layout.addLayout(storage_row)

            lim_box_layout.addWidget(self.rb_count)

            count_row = QHBoxLayout()
            count_row.setContentsMargins(24, 0, 0, 4)
            self.count_spin = QSpinBox()
            self.count_spin.setRange(1, 100000)
            self.count_spin.setValue(state.get("limit_count_val", 50))
            self.count_spin.setMinimumWidth(100)
            count_row.addWidget(QLabel("Items:"))
            count_row.addWidget(self.count_spin)
            count_row.addStretch(1)
            lim_box_layout.addLayout(count_row)

            lim_box_layout.addWidget(self.rb_all)

            self.balanced_cb = QCheckBox("Distribute evenly across chosen categories (Balanced round-robin)")
            self.balanced_cb.setChecked(state.get("balanced", True))
            self.balanced_cb.setStyleSheet("color: #818CF8; font-weight: 600; margin-top: 6px;")
            balanced_help = QLabel(
                "Fair-share distribution: cycles through selected categories and subcategories one item at a time until limit is reached."
            )
            balanced_help.setStyleSheet("font-size: 11px; color: #94A3B8; margin-left: 26px;")
            lim_box_layout.addWidget(self.balanced_cb)
            lim_box_layout.addWidget(balanced_help)

            tl_layout.addWidget(lim_box)

            # Limit Actions
            lim_act_row = QHBoxLayout()
            fit_disk_btn = QPushButton("💾 Auto-Fit to Selected Disk Free Space")
            fit_disk_btn.setObjectName("accentBtn")
            fit_disk_btn.clicked.connect(self._on_auto_fit)
            apply_now_btn = QPushButton("⚡ Apply Selection Limit Now")
            apply_now_btn.setObjectName("primaryBtn")
            apply_now_btn.clicked.connect(self._on_apply_limit)
            lim_act_row.addWidget(fit_disk_btn)
            lim_act_row.addStretch(1)
            lim_act_row.addWidget(apply_now_btn)
            tl_layout.addLayout(lim_act_row)

            tl_layout.addStretch(1)
            self.tabs.addTab(tab_limits, "⚡ Copy Mechanism && Limits")

            # --- Tab 1: Target Disks & Drives ---
            tab_disks = QWidget()
            td_layout = QVBoxLayout(tab_disks)
            td_layout.setContentsMargins(14, 16, 14, 14)
            td_layout.setSpacing(10)

            disk_header_lbl = QLabel("Select destination flash drives, memory cards, or local output directories:")
            disk_header_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
            td_layout.addWidget(disk_header_lbl)

            disk_tb = QHBoxLayout()
            rescan_disks_btn = QPushButton("🔄 Rescan Disks")
            rescan_disks_btn.clicked.connect(self.refresh_disks)
            add_disk_btn = QPushButton("➕ Add Folder / Disk…")
            add_disk_btn.clicked.connect(self._add_custom_disk)
            sel_all_disks_btn = QPushButton("Select All")
            sel_all_disks_btn.clicked.connect(lambda: self._set_all_disks(True))
            clear_disks_btn = QPushButton("Clear All")
            clear_disks_btn.clicked.connect(lambda: self._set_all_disks(False))
            disk_tb.addWidget(rescan_disks_btn)
            disk_tb.addWidget(add_disk_btn)
            disk_tb.addStretch(1)
            disk_tb.addWidget(sel_all_disks_btn)
            disk_tb.addWidget(clear_disks_btn)
            td_layout.addLayout(disk_tb)

            self.disks_list = QListWidget()
            self.disks_list.setObjectName("disksList")
            self.disks_list.setSelectionMode(QListWidget.NoSelection)
            self.disks_list.itemChanged.connect(lambda *_: self._on_disk_changed())
            td_layout.addWidget(self.disks_list, 1)

            self.disks_status_lbl = QLabel("No disk selected")
            self.disks_status_lbl.setStyleSheet("color: #10B981; font-weight: 700; font-size: 12px;")
            td_layout.addWidget(self.disks_status_lbl)

            self.tabs.addTab(tab_disks, "💾 Target Disks && Drives")

            # --- Tab 2: Application & Model Extraction ---
            tab_app = QWidget()
            ta_layout = QVBoxLayout(tab_app)
            ta_layout.setContentsMargins(14, 16, 14, 14)
            ta_layout.setSpacing(14)

            app_box = QGroupBox("orga+ Application Distribution")
            app_box_layout = QVBoxLayout(app_box)
            app_box_layout.setContentsMargins(12, 14, 12, 12)
            app_box_layout.setSpacing(8)

            self.auto_app_cb = QCheckBox("Auto-copy orga+ app bundle to destination disk root")
            self.auto_app_cb.setChecked(state.get("auto_copy_app", True))
            app_box_layout.addWidget(self.auto_app_cb)

            app_row = QHBoxLayout()
            app_path = state.get("app_path")
            self.app_info_lbl = QLabel(f"App: {app_path.name if app_path else 'Not detected'}")
            self.app_info_lbl.setStyleSheet("font-size: 11px; color: #38BDF8; font-weight: 600;")
            browse_app_btn = QPushButton("📁 Browse…")
            browse_app_btn.setMaximumWidth(90)
            browse_app_btn.clicked.connect(self._browse_app)
            app_row.addWidget(self.app_info_lbl, 1)
            app_row.addWidget(browse_app_btn)
            app_box_layout.addLayout(app_row)
            ta_layout.addWidget(app_box)

            extract_box = QGroupBox("Model Archive Extraction")
            extract_box_layout = QVBoxLayout(extract_box)
            extract_box_layout.setContentsMargins(12, 14, 12, 12)
            extract_box_layout.setSpacing(6)

            self.unzip_cb = QCheckBox("Extract 3D model archives (.zip, .rar, .7z) directly into /model/ directory")
            self.unzip_cb.setChecked(state.get("unzip_models", True))
            unzip_help = QLabel(
                "Extracts 3D model files (including .skp) cleanly into /model/, promotes nested files, and removes the original archive (.zip/.rar)."
            )
            unzip_help.setStyleSheet("font-size: 11px; color: #94A3B8; margin-left: 26px;")
            extract_box_layout.addWidget(self.unzip_cb)
            extract_box_layout.addWidget(unzip_help)
            ta_layout.addWidget(extract_box)

            ta_layout.addStretch(1)
            self.tabs.addTab(tab_app, "📦 App && Extraction")

            # --- Tab 3: Performance & Engine ---
            tab_perf = QWidget()
            tp_layout = QVBoxLayout(tab_perf)
            tp_layout.setContentsMargins(14, 16, 14, 14)
            tp_layout.setSpacing(14)

            perf_box = QGroupBox("Transfer Engine && Safety Buffer")
            perf_box_layout = QVBoxLayout(perf_box)
            perf_box_layout.setContentsMargins(12, 14, 12, 12)
            perf_box_layout.setSpacing(10)

            self.resume_cb = QCheckBox("Fast Resume (Skip files already present on target disks)")
            self.resume_cb.setChecked(state.get("skip_existing", True))
            perf_box_layout.addWidget(self.resume_cb)

            workers_row = QHBoxLayout()
            workers_lbl = QLabel("Parallel copy streams:")
            self.workers_spin = QSpinBox()
            self.workers_spin.setRange(1, 8)
            self.workers_spin.setValue(state.get("workers", workers))
            workers_help = QLabel("(1 worker recommended for USB flash drives; 2-4 for fast SSDs)")
            workers_help.setStyleSheet("font-size: 11px; color: #64748B;")
            workers_row.addWidget(workers_lbl)
            workers_row.addWidget(self.workers_spin)
            workers_row.addWidget(workers_help, 1)
            perf_box_layout.addLayout(workers_row)

            safety_row = QHBoxLayout()
            safety_lbl = QLabel("Auto-Fit disk safety buffer:")
            self.safety_spin = QSpinBox()
            self.safety_spin.setRange(50, 10000)
            self.safety_spin.setSingleStep(50)
            self.safety_spin.setValue(state.get("safety_margin_mb", 500))
            self.safety_spin.setSuffix(" MB")
            safety_help = QLabel("Reserved free buffer left untouched on target disk")
            safety_help.setStyleSheet("font-size: 11px; color: #64748B;")
            safety_row.addWidget(safety_lbl)
            safety_row.addWidget(self.safety_spin)
            safety_row.addWidget(safety_help, 1)
            perf_box_layout.addLayout(safety_row)

            tp_layout.addWidget(perf_box)
            tp_layout.addStretch(1)
            self.tabs.addTab(tab_perf, "🚀 Performance && Engine")

            # --- Tab 4: Scanning Rules ---
            tab_scan = QWidget()
            ts_layout = QVBoxLayout(tab_scan)
            ts_layout.setContentsMargins(14, 16, 14, 14)
            ts_layout.setSpacing(14)

            filter_box = QGroupBox("Library Scanning Rules")
            filter_box_layout = QVBoxLayout(filter_box)
            filter_box_layout.setContentsMargins(12, 14, 12, 12)
            filter_box_layout.setSpacing(6)

            self.models_only_cb = QCheckBox("Only display and export assets containing 3D models")
            self.models_only_cb.setChecked(state.get("models_only", True))
            models_help = QLabel("When unchecked, preview-only folders with images are also shown and exported.")
            models_help.setStyleSheet("font-size: 11px; color: #94A3B8; margin-left: 26px;")
            filter_box_layout.addWidget(self.models_only_cb)
            filter_box_layout.addWidget(models_help)
            ts_layout.addWidget(filter_box)

            ts_layout.addStretch(1)
            self.tabs.addTab(tab_scan, "🔍 Scanning Rules")

            # Bottom Action Buttons
            btn_box = QHBoxLayout()
            reset_btn = QPushButton("Reset to Defaults")
            reset_btn.clicked.connect(self._reset_defaults)
            done_btn = QPushButton("Save && Close")
            done_btn.setObjectName("primaryBtn")
            done_btn.clicked.connect(self.accept)
            btn_box.addWidget(reset_btn)
            btn_box.addStretch(1)
            btn_box.addWidget(done_btn)
            dlg_layout.addLayout(btn_box)

        def open_tab(self, index: int) -> None:
            self.tabs.setCurrentIndex(index)
            self.exec()

        def refresh_disks(self) -> None:
            self.disks_list.blockSignals(True)
            self.disks_list.clear()
            vols = list_volumes()
            state["volumes"] = vols

            for v in vols:
                drive_type = "Removable Disk" if v.is_removable else "Local / Fixed Drive"
                used_pct = ((v.total - v.free) / v.total * 100) if v.total > 0 else 0
                text = (
                    f"💾  {v.label}   [{drive_type}]\n"
                    f"    Path: {v.path}\n"
                    f"    Space: {human_size(v.free)} free  /  {human_size(v.total)} total  ({used_pct:.1f}% used)"
                )
                item = QListWidgetItem(text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setCheckState(Qt.Checked if v.is_removable else Qt.Unchecked)
                item.setData(Qt.UserRole, v)
                item.setToolTip(v.path)
                self.disks_list.addItem(item)

            if not vols:
                item = QListWidgetItem("⚠️ No removable drives detected. Click 'Add Folder / Disk…' to choose a destination.")
                item.setFlags(Qt.NoItemFlags)
                self.disks_list.addItem(item)

            self.disks_list.blockSignals(False)
            self.update_disks_status()

        def _add_custom_disk(self) -> None:
            d = QFileDialog.getExistingDirectory(self, "Choose Destination Disk or Folder")
            if d:
                p = str(Path(d).resolve())
                try:
                    u = shutil.disk_usage(p)
                    v = VolumeInfo(Path(p).name or p, p, u.free, u.total, True)
                    drive_type = "Custom Destination Folder"
                    used_pct = ((v.total - v.free) / v.total * 100) if v.total > 0 else 0
                    text = (
                        f"📁  {v.label}   [{drive_type}]\n"
                        f"    Path: {v.path}\n"
                        f"    Space: {human_size(v.free)} free  /  {human_size(v.total)} total  ({used_pct:.1f}% used)"
                    )
                    item = QListWidgetItem(text)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    item.setCheckState(Qt.Checked)
                    item.setData(Qt.UserRole, v)
                    item.setToolTip(v.path)
                    self.disks_list.addItem(item)
                    self.update_disks_status()
                    log_msg(f"Added custom destination: {p}")
                except OSError as e:
                    QMessageBox.warning(self, "Error", f"Could not access {p}: {e}")

        def _set_all_disks(self, checked: bool) -> None:
            self.disks_list.blockSignals(True)
            for i in range(self.disks_list.count()):
                it = self.disks_list.item(i)
                if it.flags() & Qt.ItemIsUserCheckable:
                    it.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.disks_list.blockSignals(False)
            self.update_disks_status()

        def _on_disk_changed(self) -> None:
            self.update_disks_status()

        def get_selected_disks(self) -> List[VolumeInfo]:
            chosen: List[VolumeInfo] = []
            for i in range(self.disks_list.count()):
                item = self.disks_list.item(i)
                if item.checkState() == Qt.Checked:
                    data = item.data(Qt.UserRole)
                    if data and isinstance(data, VolumeInfo):
                        chosen.append(data)
            return chosen

        def update_disks_status(self) -> None:
            chosen = self.get_selected_disks()
            if not chosen:
                self.disks_status_lbl.setText("⚠️ No target disk selected.")
                self.disks_status_lbl.setStyleSheet("color: #F59E0B; font-weight: 700; font-size: 12px;")
            else:
                free_caps = [f"{v.label}: {human_size(v.free)}" for v in chosen]
                self.disks_status_lbl.setText(f"✓ {len(chosen)} disk(s) selected: " + " | ".join(free_caps))
                self.disks_status_lbl.setStyleSheet("color: #10B981; font-weight: 700; font-size: 12px;")
            update_pills()
            update_selection_summary()

        def get_mechanism_mode(self) -> str:
            if self.rb_count.isChecked():
                return "count"
            elif self.rb_storage.isChecked():
                return "storage"
            return "all"

        def _on_auto_fit(self) -> None:
            apply_fit_disk()

        def _on_apply_limit(self) -> None:
            self._save_state()
            apply_selection_limit()

        def _browse_app(self) -> None:
            path, _ = QFileDialog.getOpenFileName(self, "Select orga+ Application", str(Path.cwd()))
            if not path:
                path = QFileDialog.getExistingDirectory(self, "Select orga+ .app Bundle")
            if path:
                state["app_path"] = Path(path).resolve()
                self.app_info_lbl.setText(f"App: {state['app_path'].name}")
                update_selection_summary()

        def _reset_defaults(self) -> None:
            self.rb_storage.setChecked(True)
            self.storage_spin.setValue(16.0)
            self.unit_combo.setCurrentText("GB")
            self.count_spin.setValue(50)
            self.balanced_cb.setChecked(True)
            self.auto_app_cb.setChecked(True)
            self.unzip_cb.setChecked(True)
            self.resume_cb.setChecked(True)
            self.workers_spin.setValue(1)
            self.safety_spin.setValue(500)
            self.models_only_cb.setChecked(True)

        def _save_state(self) -> None:
            state["mechanism_mode"] = self.get_mechanism_mode()
            state["limit_storage_val"] = self.storage_spin.value()
            state["limit_storage_unit"] = self.unit_combo.currentText()
            state["limit_count_val"] = self.count_spin.value()
            state["balanced"] = self.balanced_cb.isChecked()
            state["auto_copy_app"] = self.auto_app_cb.isChecked()
            state["unzip_models"] = self.unzip_cb.isChecked()
            state["skip_existing"] = self.resume_cb.isChecked()
            state["workers"] = self.workers_spin.value()
            state["safety_margin_mb"] = self.safety_spin.value()
            state["models_only"] = self.models_only_cb.isChecked()

        def accept(self) -> None:
            prev_models_only = state.get("models_only", True)
            self._save_state()
            super().accept()
            update_pills()
            update_selection_summary()
            if prev_models_only != state["models_only"]:
                load_library(state["source"])
            log_msg("Preferences and automation settings updated.")

    # ----------------------------------------------------------------------
    # Main Window Setup
    # ----------------------------------------------------------------------
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("orga+ Copy Tool")
    app.setStyleSheet(MODERN_DARK_QSS)

    win = QWidget()
    win.setWindowTitle("orga+ Copy Tool — High-Speed Multi-Disk Exporter")
    win.resize(1280, 880)
    win.setMinimumSize(1040, 720)

    icon_p = Path(__file__).resolve().parent.parent / "desktop" / "assets" / "icon.png"
    if icon_p.exists():
        win.setWindowIcon(QIcon(str(icon_p)))

    main_layout = QVBoxLayout(win)
    main_layout.setContentsMargins(14, 14, 14, 14)
    main_layout.setSpacing(10)

    # ----------------------------------------------------------------------
    # 1. Top Header Bar
    # ----------------------------------------------------------------------
    header_frame = QFrame()
    header_frame.setObjectName("headerFrame")
    header_frame.setStyleSheet("""
        QFrame#headerFrame {
            background-color: #111827;
            border: 1px solid #26334D;
            border-radius: 10px;
        }
    """)
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(14, 10, 14, 10)
    header_layout.setSpacing(12)

    title_box = QVBoxLayout()
    title_box.setSpacing(2)
    title_row = QHBoxLayout()
    title_row.setSpacing(8)
    title_lbl = QLabel("orga+ Copy Tool")
    title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
    badge_lbl = QLabel("v2.3.0")
    badge_lbl.setStyleSheet("background-color: #312E81; color: #818CF8; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 700;")
    title_row.addWidget(title_lbl)
    title_row.addWidget(badge_lbl)
    title_row.addStretch(1)

    subtitle_lbl = QLabel("High-Speed Library Exporter && Smart Drive Provisioner")
    subtitle_lbl.setStyleSheet("font-size: 11px; color: #818CF8; font-weight: 600;")
    title_box.addLayout(title_row)
    title_box.addWidget(subtitle_lbl)
    header_layout.addLayout(title_box)

    header_layout.addStretch(1)

    settings_btn = QPushButton("⚙️ Settings && Mechanisms…")
    settings_btn.setObjectName("accentBtn")
    settings_btn.setToolTip("Configure copy mechanism, target disks, app bundling, and transfer rules")
    settings_btn.clicked.connect(lambda: _open_settings(0))
    header_layout.addWidget(settings_btn)

    main_layout.addWidget(header_frame)

    # ----------------------------------------------------------------------
    # 2. Sleek Unified Location Bar
    # ----------------------------------------------------------------------
    loc_frame = QFrame()
    loc_frame.setObjectName("locationBar")
    loc_frame.setStyleSheet("""
        QFrame#locationBar {
            background-color: #0E1524;
            border: 1px solid #26334D;
            border-radius: 8px;
        }
    """)
    loc_layout = QHBoxLayout(loc_frame)
    loc_layout.setContentsMargins(12, 6, 8, 6)
    loc_layout.setSpacing(10)

    loc_icon_lbl = QLabel("📂 Source Library:")
    loc_icon_lbl.setStyleSheet("font-weight: 700; color: #94A3B8; font-size: 12px;")
    loc_layout.addWidget(loc_icon_lbl)

    src_display = QLabel(state["source"])
    src_display.setStyleSheet("font-weight: 600; color: #38BDF8; font-family: monospace; font-size: 12px;")
    src_display.setToolTip(state["source"])
    loc_layout.addWidget(src_display, 1)

    change_src_btn = QPushButton("📁 Change Folder…")
    change_src_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
    loc_layout.addWidget(change_src_btn)

    rescan_btn = QPushButton("🔄 Rescan")
    rescan_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
    loc_layout.addWidget(rescan_btn)

    main_layout.addWidget(loc_frame)

    # ----------------------------------------------------------------------
    # 3. Quick Status & Configuration Pill Bar
    # ----------------------------------------------------------------------
    pill_frame = QFrame()
    pill_frame.setObjectName("pillBar")
    pill_frame.setStyleSheet("""
        QFrame#pillBar {
            background-color: #111827;
            border: 1px solid #1E293B;
            border-radius: 8px;
        }
    """)
    pill_layout = QHBoxLayout(pill_frame)
    pill_layout.setContentsMargins(12, 6, 12, 6)
    pill_layout.setSpacing(12)

    disk_pill_lbl = QLabel("💾 Target: Loading…")
    disk_pill_lbl.setStyleSheet("color: #10B981; font-weight: 700; font-size: 12px;")
    manage_disks_btn = QPushButton("Manage Disks…")
    manage_disks_btn.setStyleSheet("padding: 3px 8px; font-size: 11px;")
    manage_disks_btn.clicked.connect(lambda: _open_settings(1))

    pill_layout.addWidget(disk_pill_lbl)
    pill_layout.addWidget(manage_disks_btn)

    pill_div1 = QFrame()
    pill_div1.setFrameShape(QFrame.VLine)
    pill_div1.setStyleSheet("color: #26334D;")
    pill_layout.addWidget(pill_div1)

    mode_pill_lbl = QLabel("⚡ Limit: 16.0 GB (Balanced)")
    mode_pill_lbl.setStyleSheet("color: #818CF8; font-weight: 700; font-size: 12px;")
    change_mode_btn = QPushButton("Change Limit…")
    change_mode_btn.setStyleSheet("padding: 3px 8px; font-size: 11px;")
    change_mode_btn.clicked.connect(lambda: _open_settings(0))

    quick_apply_btn = QPushButton("⚡ Apply Limit")
    quick_apply_btn.setObjectName("primaryBtn")
    quick_apply_btn.setStyleSheet("padding: 3px 10px; font-size: 11px; font-weight: 700;")
    quick_apply_btn.clicked.connect(lambda: apply_selection_limit())

    pill_layout.addWidget(mode_pill_lbl)
    pill_layout.addWidget(change_mode_btn)
    pill_layout.addWidget(quick_apply_btn)

    pill_layout.addStretch(1)

    main_layout.addWidget(pill_frame)

    # ----------------------------------------------------------------------
    # 4. Main Two-Column Workspace (Categories Tree | Items & Metrics)
    # ----------------------------------------------------------------------
    splitter = QSplitter(Qt.Horizontal)

    # ========================== LEFT PANEL (Tree) ========================
    left_panel = QWidget()
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(0, 0, 6, 0)
    left_layout.setSpacing(8)

    cat_group = QGroupBox("Categories && Subcategories to Include")
    cat_layout = QVBoxLayout(cat_group)
    cat_layout.setContentsMargins(10, 14, 10, 10)
    cat_layout.setSpacing(8)

    cat_toolbar = QHBoxLayout()
    sel_all_cats_btn = QPushButton("Select All")
    sel_none_cats_btn = QPushButton("Clear All")
    expand_cats_btn = QPushButton("Expand All")
    cat_toolbar.addWidget(sel_all_cats_btn)
    cat_toolbar.addWidget(sel_none_cats_btn)
    cat_toolbar.addWidget(expand_cats_btn)
    cat_layout.addLayout(cat_toolbar)

    category_tree = QTreeWidget()
    category_tree.setHeaderLabels(["Category / Subcategory", "Items && Size"])
    category_tree.setColumnCount(2)
    category_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
    category_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    cat_layout.addWidget(category_tree, 1)

    cat_hint_lbl = QLabel("Uncheck categories or subcategories to exclude them from the export.")
    cat_hint_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
    cat_layout.addWidget(cat_hint_lbl)

    left_layout.addWidget(cat_group, 1)
    splitter.addWidget(left_panel)

    # ========================== RIGHT PANEL (Table) ======================
    right_panel = QWidget()
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(6, 0, 0, 0)
    right_layout.setSpacing(8)

    # Prominent Metric Banner
    summary_frame = QFrame()
    summary_frame.setStyleSheet("""
        QFrame#summaryBanner {
            background-color: #111827;
            border: 1px solid #26334D;
            border-radius: 10px;
        }
    """)
    summary_frame.setObjectName("summaryBanner")
    summary_layout = QHBoxLayout(summary_frame)
    summary_layout.setContentsMargins(16, 10, 16, 10)
    summary_layout.setSpacing(20)

    # Metric 1: Selected Count
    count_block = QVBoxLayout()
    count_title = QLabel("SELECTED OBJECTS")
    count_title.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
    count_val_lbl = QLabel("0 items")
    count_val_lbl.setStyleSheet("color: #F8FAFC; font-size: 16px; font-weight: 800;")
    count_block.addWidget(count_title)
    count_block.addWidget(count_val_lbl)
    summary_layout.addLayout(count_block)

    div1 = QFrame()
    div1.setFrameShape(QFrame.VLine)
    div1.setStyleSheet("color: #26334D;")
    summary_layout.addWidget(div1)

    # Metric 2: Current Size
    size_block = QVBoxLayout()
    size_title = QLabel("CURRENT SIZE OF SELECTED OBJECTS")
    size_title.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
    size_val_lbl = QLabel("0 B")
    size_val_lbl.setStyleSheet("color: #818CF8; font-size: 16px; font-weight: 800;")
    size_block.addWidget(size_title)
    size_block.addWidget(size_val_lbl)
    summary_layout.addLayout(size_block)

    div2 = QFrame()
    div2.setFrameShape(QFrame.VLine)
    div2.setStyleSheet("color: #26334D;")
    summary_layout.addWidget(div2)

    # Metric 3: Target Disk Capacity Status
    disk_block = QVBoxLayout()
    disk_title = QLabel("TARGET DISK CAPACITY STATUS")
    disk_title.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;")
    disk_val_lbl = QLabel("Select a target disk in Settings")
    disk_val_lbl.setStyleSheet("color: #10B981; font-size: 14px; font-weight: 700;")
    disk_block.addWidget(disk_title)
    disk_block.addWidget(disk_val_lbl)
    summary_layout.addLayout(disk_block)

    summary_layout.addStretch(1)
    right_layout.addWidget(summary_frame)

    # Search & Filter Bar
    table_filter_row = QHBoxLayout()
    search_input = QLineEdit()
    search_input.setPlaceholderText("🔍 Search by title, subcategory, format…")
    format_combo = QComboBox()
    format_combo.addItem("All Formats")
    format_combo.addItems(["SKP", "RAR", "ZIP", "FBX", "OBJ", "BLEND"])

    sel_all_btn = QPushButton("Select All Filtered")
    sel_none_btn = QPushButton("Clear Filtered")
    invert_sel_btn = QPushButton("Invert")

    table_filter_row.addWidget(search_input, 1)
    table_filter_row.addWidget(format_combo)
    table_filter_row.addWidget(sel_all_btn)
    table_filter_row.addWidget(sel_none_btn)
    table_filter_row.addWidget(invert_sel_btn)
    right_layout.addLayout(table_filter_row)

    # Items Table
    items_table = QTableWidget()
    items_table.setColumnCount(7)
    items_table.setHorizontalHeaderLabels([
        "", "Category", "Subcategory", "Asset Title", "Format", "Files", "Size"
    ])
    items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
    items_table.setColumnWidth(0, 36)
    items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
    items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
    items_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
    items_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
    items_table.verticalHeader().setVisible(False)
    items_table.setSelectionBehavior(QTableWidget.SelectRows)
    right_layout.addWidget(items_table, 1)

    splitter.addWidget(right_panel)
    splitter.setSizes([380, 880])
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    main_layout.addWidget(splitter, 1)

    # ----------------------------------------------------------------------
    # 5. Bottom Progress & Controls Section
    # ----------------------------------------------------------------------
    bottom_group = QFrame()
    bottom_group.setStyleSheet("background-color: #111827; border: 1px solid #26334D; border-radius: 10px; padding: 8px;")
    bottom_layout = QVBoxLayout(bottom_group)
    bottom_layout.setContentsMargins(12, 8, 12, 8)
    bottom_layout.setSpacing(8)

    status_row = QHBoxLayout()
    status_lbl = QLabel("Ready.")
    status_lbl.setStyleSheet("font-weight: 600; color: #38BDF8;")
    speed_eta_lbl = QLabel("0.0 MB/s • ETA: --:--")
    speed_eta_lbl.setStyleSheet("color: #94A3B8; font-weight: 600;")
    status_row.addWidget(status_lbl, 1)
    status_row.addWidget(speed_eta_lbl)
    bottom_layout.addLayout(status_row)

    bar = QProgressBar()
    bar.setRange(0, 1000)
    bar.setValue(0)
    bar.setFormat("%p%")
    bottom_layout.addWidget(bar)

    btn_row = QHBoxLayout()
    start_btn = QPushButton("▶ Start Copy to Disks")
    start_btn.setObjectName("primaryBtn")
    start_btn.setMinimumHeight(38)
    start_btn.setMinimumWidth(180)

    pause_btn = QPushButton("⏸ Pause")
    pause_btn.setObjectName("pauseBtn")
    pause_btn.setMinimumHeight(38)
    pause_btn.setEnabled(False)

    stop_btn = QPushButton("⏹ Stop")
    stop_btn.setObjectName("stopBtn")
    stop_btn.setMinimumHeight(38)
    stop_btn.setEnabled(False)

    toggle_log_btn = QPushButton("📋 Activity Log")
    toggle_log_btn.setMinimumHeight(38)

    btn_row.addWidget(start_btn)
    btn_row.addWidget(pause_btn)
    btn_row.addWidget(stop_btn)
    btn_row.addStretch(1)
    btn_row.addWidget(toggle_log_btn)
    bottom_layout.addLayout(btn_row)

    log_view = QPlainTextEdit()
    log_view.setReadOnly(True)
    log_view.setMaximumBlockCount(3000)
    log_view.setFixedHeight(120)
    log_view.setVisible(False)
    bottom_layout.addWidget(log_view)

    main_layout.addWidget(bottom_group)

    # ----------------------------------------------------------------------
    # Helper Functions & UI Logic
    # ----------------------------------------------------------------------

    settings_dlg: Any = None

    def log_msg(msg: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        log_view.appendPlainText(f"[{ts}] {msg}")

    def update_pills() -> None:
        chosen = settings_dlg.get_selected_disks()
        if not chosen:
            disk_pill_lbl.setText("💾 Target: ⚠️ None Selected")
            disk_pill_lbl.setStyleSheet("color: #F59E0B; font-weight: 700; font-size: 12px;")
        elif len(chosen) == 1:
            d = chosen[0]
            disk_pill_lbl.setText(f"💾 Target: {d.label} ({human_size(d.free)} free)")
            disk_pill_lbl.setStyleSheet("color: #10B981; font-weight: 700; font-size: 12px;")
        else:
            disk_pill_lbl.setText(f"💾 Target: {len(chosen)} Disks Selected")
            disk_pill_lbl.setStyleSheet("color: #10B981; font-weight: 700; font-size: 12px;")

        mode = settings_dlg.get_mechanism_mode()
        if mode == "storage":
            val = settings_dlg.storage_spin.value()
            unit = settings_dlg.unit_combo.currentText()
            bal = " (Balanced)" if settings_dlg.balanced_cb.isChecked() else ""
            mode_pill_lbl.setText(f"⚡ Limit: {val:.1f} {unit}{bal}")
        elif mode == "count":
            cnt = settings_dlg.count_spin.value()
            bal = " (Balanced)" if settings_dlg.balanced_cb.isChecked() else ""
            mode_pill_lbl.setText(f"⚡ Limit: {cnt} Items{bal}")
        else:
            mode_pill_lbl.setText("⚡ Mode: All in Chosen Categories")

    def get_checked_subcategories() -> Set[Tuple[str, str]]:
        checked: Set[Tuple[str, str]] = set()
        for i in range(category_tree.topLevelItemCount()):
            parent = category_tree.topLevelItem(i)
            cat_name = parent.data(0, Qt.UserRole)[1]
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    sub_name = child.data(0, Qt.UserRole)[2]
                    checked.add((cat_name, sub_name))
        return checked

    def get_selected_items() -> List[CopyItem]:
        selected = []
        for r in range(items_table.rowCount()):
            cb_item = items_table.item(r, 0)
            if cb_item and cb_item.checkState() == Qt.Checked:
                it = cb_item.data(Qt.UserRole)
                if it:
                    selected.append(it)
        return selected

    def update_selection_summary() -> None:
        selected = get_selected_items()
        total_bytes = sum(it.total_bytes for it in selected)
        app_size = get_app_size(state["app_path"]) if (state.get("auto_copy_app", True) and state["app_path"]) else 0
        grand_total = total_bytes + app_size

        count_val_lbl.setText(f"{len(selected)} items  (of {len(state['items'])})")
        size_val_lbl.setText(
            f"{human_size(total_bytes)}" + (f" + {human_size(app_size)} App" if app_size else "")
        )

        chosen_disks = settings_dlg.get_selected_disks()
        if not chosen_disks:
            disk_val_lbl.setText("⚠️ Select target disk in Settings")
            disk_val_lbl.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: 700;")
            return

        min_free = min(d.free for d in chosen_disks)
        disk_label = chosen_disks[0].label if len(chosen_disks) == 1 else f"{len(chosen_disks)} disks"

        if grand_total > min_free:
            over = grand_total - min_free
            disk_val_lbl.setText(f"⚠️ Exceeds space by {human_size(over)}! (Free: {human_size(min_free)})")
            disk_val_lbl.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: 700;")
        else:
            remaining = min_free - grand_total
            disk_val_lbl.setText(f"✓ Fits comfortably ({human_size(remaining)} remaining on {disk_label})")
            disk_val_lbl.setStyleSheet("color: #10B981; font-size: 14px; font-weight: 700;")

    def populate_category_tree() -> None:
        state["updating_tree"] = True
        category_tree.clear()

        # Group items by Category -> Subcategory
        cat_map: Dict[str, Dict[str, List[CopyItem]]] = {}
        for it in state["items"]:
            cat_map.setdefault(it.job, {}).setdefault(it.category, []).append(it)

        for cat_name in sorted(cat_map.keys()):
            sub_map = cat_map[cat_name]
            cat_items = [it for subs in sub_map.values() for it in subs]
            cat_bytes = sum(it.total_bytes for it in cat_items)

            parent_item = QTreeWidgetItem(category_tree)
            parent_item.setText(0, f"📁 {cat_name}")
            parent_item.setText(1, f"{len(cat_items)} items • {human_size(cat_bytes)}")
            parent_item.setFlags(parent_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            parent_item.setCheckState(0, Qt.Checked)
            parent_item.setData(0, Qt.UserRole, ("category", cat_name))

            for sub_name in sorted(sub_map.keys()):
                subs_items = sub_map[sub_name]
                sub_bytes = sum(it.total_bytes for it in subs_items)
                child_item = QTreeWidgetItem(parent_item)
                child_item.setText(0, f"  📂 {sub_name}")
                child_item.setText(1, f"{len(subs_items)} items • {human_size(sub_bytes)}")
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                child_item.setCheckState(0, Qt.Checked)
                child_item.setData(0, Qt.UserRole, ("subcategory", cat_name, sub_name))

        category_tree.expandAll()
        state["updating_tree"] = False

    def on_tree_item_changed(item: QTreeWidgetItem, col: int) -> None:
        if col != 0 or state["updating_tree"]:
            return
        state["updating_tree"] = True
        data = item.data(0, Qt.UserRole)
        if not data:
            state["updating_tree"] = False
            return

        node_type = data[0]
        if node_type == "category":
            cs = item.checkState(0)
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, cs)
        elif node_type == "subcategory":
            parent = item.parent()
            if parent:
                checked_cnt = 0
                for i in range(parent.childCount()):
                    if parent.child(i).checkState(0) == Qt.Checked:
                        checked_cnt += 1
                if checked_cnt == parent.childCount():
                    parent.setCheckState(0, Qt.Checked)
                elif checked_cnt == 0:
                    parent.setCheckState(0, Qt.Unchecked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)

        state["updating_tree"] = False
        apply_category_filter_to_table()
        update_selection_summary()

    def populate_table() -> None:
        state["updating_table"] = True
        items_table.setRowCount(0)
        items_table.setRowCount(len(state["items"]))

        for r, it in enumerate(state["items"]):
            cb_item = QTableWidgetItem()
            cb_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            cb_item.setCheckState(Qt.Checked)
            cb_item.setData(Qt.UserRole, it)
            items_table.setItem(r, 0, cb_item)

            c_item = QTableWidgetItem(it.job)
            c_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 1, c_item)

            sub_item = QTableWidgetItem(it.category)
            sub_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 2, sub_item)

            t_item = QTableWidgetItem(it.title)
            t_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 3, t_item)

            fmt_lbl = f"{it.model_format}" + (" (unzip)" if it.is_zip else "")
            f_item = QTableWidgetItem(fmt_lbl)
            f_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 4, f_item)

            fc_item = QTableWidgetItem(str(it.files_count))
            fc_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            fc_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 5, fc_item)

            s_item = QTableWidgetItem(human_size(it.total_bytes))
            s_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            s_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 6, s_item)

        state["updating_table"] = False
        update_selection_summary()

    def apply_category_filter_to_table() -> None:
        checked_subcats = get_checked_subcategories()
        query = search_input.text().strip().lower()
        fmt_filter = format_combo.currentText().upper()

        state["updating_table"] = True
        for r in range(items_table.rowCount()):
            cb_item = items_table.item(r, 0)
            it: CopyItem = cb_item.data(Qt.UserRole)

            in_checked_subcats = (it.job, it.category) in checked_subcats
            matches_fmt = (fmt_filter == "ALL FORMATS") or (fmt_filter in it.model_format.upper())
            matches_query = (
                not query
                or (query in it.title.lower())
                or (query in it.category.lower())
                or (query in it.job.lower())
                or (query in it.model_format.lower())
            )

            is_visible = in_checked_subcats and matches_fmt and matches_query
            items_table.setRowHidden(r, not is_visible)
            if not in_checked_subcats:
                cb_item.setCheckState(Qt.Unchecked)

        state["updating_table"] = False
        update_selection_summary()

    def filter_table() -> None:
        apply_category_filter_to_table()

    def load_library(path_str: str) -> None:
        state["source"] = path_str
        src_display.setText(path_str)
        src_display.setToolTip(path_str)
        log_msg(f"Scanning library: {path_str}")

        models_only = state.get("models_only", True)
        items, skipped = scan_items(Path(path_str), models_only=models_only)

        if not items and models_only:
            all_items, _ = scan_items(Path(path_str), models_only=False)
            if all_items:
                log_msg(f"Notice: Found {len(all_items)} asset folders with preview images, but none containing 3D models.")
                items = all_items
                state["models_only"] = False
                settings_dlg.models_only_cb.setChecked(False)

        state["items"] = items
        populate_category_tree()
        populate_table()

        total_bytes = sum(it.total_bytes for it in items)
        log_msg(
            f"Scan complete: {len(items)} items ({human_size(total_bytes)}) discovered. "
            f"{skipped} non-model folders skipped."
        )

    # ----------------------------------------------------------------------
    # Selection Mode Actions
    # ----------------------------------------------------------------------

    def apply_selection_limit() -> None:
        checked_subcats = get_checked_subcategories()
        if not checked_subcats:
            QMessageBox.warning(win, "No Categories Selected", "Please select at least one category or subcategory from the tree.")
            return

        candidate_items = [it for it in state["items"] if (it.job, it.category) in checked_subcats]
        if not candidate_items:
            QMessageBox.warning(win, "No Items", "No items available in the selected categories.")
            return

        is_balanced = settings_dlg.balanced_cb.isChecked()
        mode = settings_dlg.get_mechanism_mode()

        if mode == "count":
            limit_cnt = settings_dlg.count_spin.value()
            if is_balanced:
                selected_ids = select_balanced_items(
                    candidate_items,
                    mode="count",
                    limit_value=limit_cnt,
                    selected_subcategories=checked_subcats,
                    group_by="category",
                )
            else:
                selected_ids = select_exact_count(candidate_items, limit_cnt)

            selected_bytes = sum(it.total_bytes for it in candidate_items if it.unique_id in selected_ids)
            log_msg(f"Applied item limit: selected {len(selected_ids)} items ({human_size(selected_bytes)}) {'(balanced round-robin)' if is_balanced else '(sequential)'}.")

        elif mode == "storage":
            unit = settings_dlg.unit_combo.currentText()
            mult = 1024 * 1024 * 1024 if unit == "GB" else 1024 * 1024
            val = settings_dlg.storage_spin.value()
            limit_bytes = int(val * mult)
            if is_balanced:
                selected_ids = select_balanced_items(
                    candidate_items,
                    mode="storage",
                    limit_value=limit_bytes,
                    selected_subcategories=checked_subcats,
                    group_by="category",
                )
            else:
                selected_ids = select_storage_limit(candidate_items, limit_bytes)

            selected_bytes = sum(it.total_bytes for it in candidate_items if it.unique_id in selected_ids)
            log_msg(f"Applied storage limit: selected {len(selected_ids)} items ({human_size(selected_bytes)}) within {val} {unit} {'(balanced round-robin)' if is_balanced else '(sequential)'}.")

        else:  # mode == "all"
            selected_ids = {it.unique_id for it in candidate_items}
            selected_bytes = sum(it.total_bytes for it in candidate_items)
            log_msg(f"Selected all {len(selected_ids)} items ({human_size(selected_bytes)}) across chosen categories.")

        state["updating_table"] = True
        for r in range(items_table.rowCount()):
            cb_item = items_table.item(r, 0)
            it: CopyItem = cb_item.data(Qt.UserRole)
            cb_item.setCheckState(Qt.Checked if it.unique_id in selected_ids else Qt.Unchecked)
        state["updating_table"] = False

        update_selection_summary()
        update_pills()

    def apply_fit_disk() -> None:
        chosen = settings_dlg.get_selected_disks()
        if not chosen:
            QMessageBox.warning(win, "No Target Disk", "Please select at least one target disk first in Settings -> Target Disks.")
            return

        min_free = min(d.free for d in chosen)
        app_size = get_app_size(state["app_path"]) if (state.get("auto_copy_app", True) and state["app_path"]) else 0
        safety_reserve = state.get("safety_margin_mb", 500) * 1024 * 1024 + app_size
        usable = max(0, min_free - safety_reserve)

        usable_gb = usable / (1024 * 1024 * 1024)
        settings_dlg.storage_spin.setValue(max(0.1, round(usable_gb, 1)))
        settings_dlg.unit_combo.setCurrentText("GB")
        settings_dlg.rb_storage.setChecked(True)
        settings_dlg._save_state()

        apply_selection_limit()
        disk_label = chosen[0].label if len(chosen) == 1 else f"{len(chosen)} disks"
        log_msg(f"Auto-fit to disk free space: set limit to {usable_gb:.1f} GB based on {disk_label} (reserving safety buffer).")

    # ----------------------------------------------------------------------
    # Copy Process Controls
    # ----------------------------------------------------------------------

    def set_running_state(running: bool) -> None:
        start_btn.setEnabled(not running)
        pause_btn.setEnabled(running)
        stop_btn.setEnabled(running)
        change_src_btn.setEnabled(not running)
        rescan_btn.setEnabled(not running)
        settings_btn.setEnabled(not running)
        manage_disks_btn.setEnabled(not running)
        change_mode_btn.setEnabled(not running)
        quick_apply_btn.setEnabled(not running)
        sel_all_cats_btn.setEnabled(not running)
        sel_none_cats_btn.setEnabled(not running)
        expand_cats_btn.setEnabled(not running)
        sel_all_btn.setEnabled(not running)
        sel_none_btn.setEnabled(not running)
        invert_sel_btn.setEnabled(not running)
        if not running:
            pause_btn.setText("⏸ Pause")
        else:
            bar.setValue(0)
            bar.setFormat("0.0%")
            status_lbl.setText("Starting export…")
            speed_eta_lbl.setText("0.0 B/s • ETA: calculating…")

    def format_eta(seconds: float) -> str:
        if seconds <= 0 or seconds > 86400 * 7:
            return "--:--"
        sec = int(round(seconds))
        hours = sec // 3600
        mins = (sec % 3600) // 60
        secs = sec % 60
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def on_progress(copied: int, total: int, speed: float, item_lbl: str, file_lbl: str) -> None:
        copied = int(copied) if copied else 0
        total = int(total) if total else 0
        speed = float(speed) if speed else 0.0

        pct_val = int(copied / total * 1000) if total > 0 else 0
        pct_val = max(0, min(1000, pct_val))
        bar.setValue(pct_val)

        pct_float = (copied / total * 100.0) if total > 0 else 0.0
        bar.setFormat(f"{pct_float:.1f}%  ({human_size(copied)} / {human_size(total)})")

        remaining = max(total - copied, 0)
        if speed >= 1024:
            eta_str = format_eta(remaining / speed)
            speed_str = f"{human_size(speed)}/s"
        elif copied >= total and total > 0:
            eta_str = "00:00"
            speed_str = "0.0 B/s"
        else:
            eta_str = "calculating…"
            speed_str = f"{human_size(speed)}/s" if speed > 0 else "0.0 B/s"

        if item_lbl or file_lbl:
            status_lbl.setText(f"{item_lbl}  [{file_lbl}]")
        speed_eta_lbl.setText(
            f"{human_size(copied)} / {human_size(total)} • {speed_str} • ETA {eta_str}"
        )

    def on_finished(summary: dict) -> None:
        set_running_state(False)
        bar.setValue(1000)
        bar.setFormat("100.0%  Complete")
        status_lbl.setText("Finished successfully.")
        speed_eta_lbl.setText("Complete")
        log_msg("Copy finished successfully to all selected disks!")
        QMessageBox.information(win, "Export Finished", "All files and models have been successfully exported.")

    def on_error(err_msg: str) -> None:
        set_running_state(False)
        status_lbl.setText(f"Error: {err_msg}")
        log_msg(f"ERROR: {err_msg}")
        QMessageBox.critical(win, "Export Error", err_msg)

    signals.progress.connect(on_progress)
    signals.log.connect(log_msg)
    signals.finished.connect(on_finished)
    signals.error.connect(on_error)

    def start_copy() -> None:
        chosen_disks = settings_dlg.get_selected_disks()
        if not chosen_disks:
            QMessageBox.warning(win, "No Disk Selected", "Please select at least one destination disk in Settings -> Target Disks.")
            settings_dlg.open_tab(1)
            return

        selected_items = get_selected_items()
        if not selected_items:
            QMessageBox.warning(win, "No Items Selected", "Please select at least one item to copy.")
            return

        total_needed = sum(it.total_bytes for it in selected_items)
        app_size = get_app_size(state["app_path"]) if (state.get("auto_copy_app", True) and state["app_path"]) else 0
        grand_total = total_needed + app_size

        for d in chosen_disks:
            if grand_total > d.free:
                res = QMessageBox.question(
                    win,
                    "Insufficient Space Warning",
                    f"Target disk '{d.label}' has only {human_size(d.free)} free, but {human_size(grand_total)} is required.\n\nProceed anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if res != QMessageBox.Yes:
                    return

        ctrl.resume()
        dest_paths = [Path(d.path) for d in chosen_disks]

        worker = CopyWorker(
            items=selected_items,
            dests=dest_paths,
            ctrl=ctrl,
            workers=state.get("workers", 1),
            skip_existing=state.get("skip_existing", True),
            auto_copy_app=state.get("auto_copy_app", True),
            app_path=state["app_path"] if state.get("auto_copy_app", True) else None,
            unzip_models=state.get("unzip_models", True),
            signals=signals,
        )
        state["worker"] = worker
        set_running_state(True)
        worker.start()
        log_msg(f"Started export of {len(selected_items)} items to {len(dest_paths)} disk(s).")

    def toggle_pause() -> None:
        if ctrl.paused:
            ctrl.resume()
            pause_btn.setText("⏸ Pause")
            status_lbl.setText("Transfer resumed.")
            log_msg("Transfer resumed.")
        else:
            ctrl.pause()
            pause_btn.setText("▶ Resume")
            status_lbl.setText("Transfer paused.")
            speed_eta_lbl.setText("Paused")
            log_msg("Transfer paused.")

    def stop_copy() -> None:
        ctrl.stop()
        log_msg("Stop requested. Unwinding and cleaning partial files…")

    # ----------------------------------------------------------------------
    # Event Connections
    # ----------------------------------------------------------------------
    change_src_btn.clicked.connect(lambda: _choose_src())
    rescan_btn.clicked.connect(lambda: load_library(state["source"]))

    category_tree.itemChanged.connect(on_tree_item_changed)
    sel_all_cats_btn.clicked.connect(lambda: _set_tree_checked(True))
    sel_none_cats_btn.clicked.connect(lambda: _set_tree_checked(False))
    expand_cats_btn.clicked.connect(lambda: category_tree.expandAll())

    search_input.textChanged.connect(filter_table)
    format_combo.currentIndexChanged.connect(filter_table)

    sel_all_btn.clicked.connect(lambda: _set_table_selection(True))
    sel_none_btn.clicked.connect(lambda: _set_table_selection(False))
    invert_sel_btn.clicked.connect(lambda: _invert_table_selection())

    items_table.itemChanged.connect(
        lambda item: update_selection_summary() if not state["updating_table"] and item.column() == 0 else None
    )
    items_table.cellDoubleClicked.connect(
        lambda r, c: _open_item_folder(r)
    )

    toggle_log_btn.clicked.connect(lambda: log_view.setVisible(not log_view.isVisible()))

    start_btn.clicked.connect(start_copy)
    pause_btn.clicked.connect(toggle_pause)
    stop_btn.clicked.connect(stop_copy)

    def _open_settings(tab_idx: int = 0):
        settings_dlg.open_tab(tab_idx)

    def _choose_src():
        d = QFileDialog.getExistingDirectory(win, "Choose Library or Category Root Directory", state["source"])
        if d:
            load_library(d)

    def _set_tree_checked(checked: bool):
        state["updating_tree"] = True
        for i in range(category_tree.topLevelItemCount()):
            parent = category_tree.topLevelItem(i)
            parent.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
            for j in range(parent.childCount()):
                parent.child(j).setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        state["updating_tree"] = False
        apply_category_filter_to_table()
        update_selection_summary()

    def _set_table_selection(checked: bool):
        state["updating_table"] = True
        for r in range(items_table.rowCount()):
            if not items_table.isRowHidden(r):
                items_table.item(r, 0).setCheckState(Qt.Checked if checked else Qt.Unchecked)
        state["updating_table"] = False
        update_selection_summary()

    def _invert_table_selection():
        state["updating_table"] = True
        for r in range(items_table.rowCount()):
            if not items_table.isRowHidden(r):
                cb = items_table.item(r, 0)
                cb.setCheckState(Qt.Unchecked if cb.checkState() == Qt.Checked else Qt.Checked)
        state["updating_table"] = False
        update_selection_summary()

    def _open_item_folder(row: int):
        cb_item = items_table.item(row, 0)
        if cb_item:
            it: CopyItem = cb_item.data(Qt.UserRole)
            if it and it.asset.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(it.asset.resolve())))

    # Initial load & dialog setup
    settings_dlg = SettingsDialog(win)
    settings_dlg.refresh_disks()

    if initial_dest:
        try:
            u = shutil.disk_usage(initial_dest)
            v = VolumeInfo(Path(initial_dest).name, initial_dest, u.free, u.total, True)
            used_pct = ((v.total - v.free) / v.total * 100) if v.total > 0 else 0
            text = (
                f"💾  {v.label}   [Initial Destination]\n"
                f"    Path: {v.path}\n"
                f"    Space: {human_size(v.free)} free  /  {human_size(v.total)} total  ({used_pct:.1f}% used)"
            )
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, v)
            settings_dlg.disks_list.addItem(item)
            settings_dlg.update_disks_status()
        except OSError:
            pass

    update_pills()
    load_library(source)
    win.show()
    return app.exec()


# --------------------------------------------------------------------------
# CLI Headless Entry Point
# --------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="orga+ Copy Tool — ultra-fast models-only exporter to flash drives"
    )
    parser.add_argument("--source", default=default_source(), help="source library or category folder")
    parser.add_argument(
        "--dest", action="append", default=[],
        help="destination drive or folder (repeat for multiple)",
    )
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="parallel copy streams")
    parser.add_argument("--limit-count", type=int, default=0, help="copy exact first N items")
    parser.add_argument("--limit-size-gb", type=float, default=0.0, help="storage limit in GB")
    parser.add_argument("--balanced", action="store_true", help="distribute limit evenly across categories")
    parser.add_argument("--categories", help="comma-separated category names to include")
    parser.add_argument("--subcategories", help="comma-separated subcategory names to include")
    parser.add_argument("--no-auto-app", action="store_true", help="do not auto-copy the orga+ app")
    parser.add_argument("--app-path", default=None, help="custom path to orga+ app")
    parser.add_argument("--no-unzip", action="store_true", help="do not unzip model archives")
    parser.add_argument("--no-skip-existing", action="store_true", help="re-copy files already present")
    parser.add_argument("--include-no-models", action="store_true", help="include assets without 3D models")
    parser.add_argument("--headless", action="store_true", help="run in terminal without GUI")
    args = parser.parse_args(argv)

    dests = [d.strip() for part in args.dest for d in part.split(",") if d.strip()]

    if not args.headless:
        try:
            return run_gui(args.source, dests[0] if dests else "", args.workers)
        except ImportError:
            print("PySide6 not available — falling back to terminal headless mode.", file=sys.stderr)

    if not dests:
        parser.error("--dest is required in headless mode.")

    models_only = not args.include_no_models
    items, skipped = scan_items(Path(args.source), models_only=models_only)
    print(f"Found {len(items)} items ({skipped} skipped without models).")
    if not items:
        return 0

    # Filter categories / subcategories if requested
    if args.categories:
        allowed_cats = {c.strip() for c in args.categories.split(",")}
        items = [it for it in items if it.job in allowed_cats]
    if args.subcategories:
        allowed_subs = {s.strip() for s in args.subcategories.split(",")}
        items = [it for it in items if it.category in allowed_subs]

    if args.limit_count > 0:
        if args.balanced:
            sel_ids = select_balanced_items(items, mode="count", limit_value=args.limit_count)
            items = [it for it in items if it.unique_id in sel_ids]
        else:
            items = items[:args.limit_count]
        print(f"Applying count limit: selected {len(items)} items.")
    elif args.limit_size_gb > 0:
        limit_bytes = int(args.limit_size_gb * 1024 * 1024 * 1024)
        if args.balanced:
            sel_ids = select_balanced_items(items, mode="storage", limit_value=limit_bytes)
            items = [it for it in items if it.unique_id in sel_ids]
        else:
            filtered = []
            tot = 0
            for it in items:
                if tot + it.total_bytes <= limit_bytes:
                    filtered.append(it)
                    tot += it.total_bytes
            items = filtered
        print(f"Applying storage limit: selected {len(items)} items ({human_size(sum(it.total_bytes for it in items))}).")

    app_path = find_orga_app(args.app_path)
    ctrl = CopyController()

    def on_progress(snap, item, fname):
        copied, total, speed = snap
        pct = (copied / total * 100) if total else 0
        print(
            f"\r{pct:6.1f}%  {copied/1e6:8.1f}/{total/1e6:.1f} MB  "
            f"{speed/1e6:6.1f} MB/s  {item} [{fname}]",
            end="",
            flush=True,
        )

    summary = run_copy_multi(
        items=items,
        dests=[Path(d) for d in dests],
        ctrl=ctrl,
        workers=args.workers,
        skip_existing=not args.no_skip_existing,
        auto_copy_app=not args.no_auto_app,
        app_path=app_path,
        unzip_models=not args.no_unzip,
        progress_cb=on_progress,
        log_cb=lambda m: print(f"\n{m}"),
    )
    print()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
