#!/usr/bin/env python3
"""
orga+ Copy Tool
===============

High-speed standalone utility that copies 3D library items to USB / flash drives
with full automation:
  * Select multiple disks or folders as copy targets.
  * Filters and copies ONLY assets that contain 3D models.
  * Unzips model archives directly into `<Asset>/model/` and removes the .zip file.
  * Automatically copies the `orga+` desktop application to the disk root.
  * Flexible selection modes: Manual selection, Exact item count, Storage limit (GB/MB),
    or Auto-fit to target disk capacity.
  * Real-time progress bar with transfer rate (MB/s), ETA, and pause/resume/stop controls.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

# --------------------------------------------------------------------------
# Configuration & Formats
# --------------------------------------------------------------------------

MODEL_EXTS = {
    ".skp", ".obj", ".fbx", ".blend", ".zip", ".rar", ".7z",
    ".3ds", ".max", ".c4d", ".glb", ".gltf", ".stl", ".dae", ".dxf",
}

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
    job: str
    category: str
    asset: Path
    title: str
    total_bytes: int = 0
    files_count: int = 0
    model_format: str = ""
    is_zip: bool = False
    model_path: Optional[Path] = None

    @property
    def rel_parts(self) -> Tuple[str, str, str]:
        return (self.job, self.category, self.asset.name)

    @property
    def unique_id(self) -> str:
        return f"{self.job}/{self.category}/{self.asset.name}"


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
    """True when the asset folder contains a model file (in model/ dir or asset root)."""
    model_dir = asset / "model"
    if model_dir.is_dir():
        for f in model_dir.iterdir():
            if f.is_file() and _visible(f) and f.suffix.lower() in MODEL_EXTS:
                return True
            if f.is_file() and _visible(f) and f.suffix.lower() == ".zip":
                return True
        return False

    for f in asset.iterdir():
        if f.is_file() and _visible(f) and f.suffix.lower() in MODEL_EXTS:
            return True
    return False


def get_model_details(asset: Path) -> Tuple[str, bool, Optional[Path]]:
    """Return (model_format, is_zip, model_file_path) for an asset."""
    model_dir = asset / "model"
    candidates: List[Path] = []

    if model_dir.is_dir():
        for f in sorted(model_dir.iterdir()):
            if f.is_file() and _visible(f) and f.suffix.lower() in MODEL_EXTS:
                candidates.append(f)

    if not candidates:
        for f in sorted(asset.iterdir()):
            if f.is_file() and _visible(f) and f.suffix.lower() in MODEL_EXTS:
                candidates.append(f)

    if not candidates:
        return ("", False, None)

    # Prefer non-zip model if both exist, else first
    non_zips = [c for c in candidates if c.suffix.lower() != ".zip"]
    primary = non_zips[0] if non_zips else candidates[0]

    fmt = primary.suffix.lower().lstrip(".").upper()
    is_zip = primary.suffix.lower() == ".zip"
    return (fmt, is_zip, primary)


def _looks_like_asset(p: Path) -> bool:
    """A folder that is itself an asset is not a Job/Category container."""
    if (p / "model").is_dir():
        return True
    if (p / "images").is_dir():
        return True
    if (p / "meta.json").exists():
        return True
    return False


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


def scan_items(root: Path) -> Tuple[List[CopyItem], int]:
    """
    Walk ``root/<Job>/<Category>/<Asset>`` (strictly depth 3 hierarchy)
    and return (items_with_model, skipped_count).
    Only items with models are returned.
    """
    items: List[CopyItem] = []
    skipped = 0
    root = Path(root).resolve()
    if not root.is_dir():
        return items, skipped

    for job in sorted(root.iterdir()):
        if not job.is_dir() or not _visible(job) or _looks_like_asset(job):
            continue
        for category in sorted(job.iterdir()):
            if not category.is_dir() or not _visible(category) or _looks_like_asset(category):
                continue
            for asset in sorted(category.iterdir()):
                if not asset.is_dir() or not _visible(asset):
                    continue
                if not has_model(asset):
                    skipped += 1
                    continue

                fmt, is_zip, model_p = get_model_details(asset)
                title = asset.name
                meta_p = asset / "meta.json"
                if meta_p.exists():
                    try:
                        meta_data = json.loads(meta_p.read_text(encoding="utf-8"))
                        if meta_data.get("title"):
                            title = meta_data.get("title")
                    except Exception:
                        pass

                files = _iter_asset_files(asset)
                size = sum(f.stat().st_size for f in files)

                items.append(
                    CopyItem(
                        job=job.name,
                        category=category.name,
                        asset=asset,
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


def get_app_size(app_path: Path) -> int:
    """Calculate total size of the app."""
    if not app_path.exists():
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


def safe_extract_zip(
    zip_path: Path,
    target_model_dir: Path,
    ctrl: CopyController,
    on_chunk: Callable[[int], None],
    log_cb: Optional[Callable[[str], None]] = None,
) -> int:
    """
    Extract zip archive contents directly into target_model_dir.
    Strips single root folder prefix if present so models sit cleanly in model/.
    Guarantees no .zip file is left in target_model_dir.
    """
    log = log_cb or (lambda m: None)
    target_model_dir.mkdir(parents=True, exist_ok=True)
    extracted_bytes = 0

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = [
                m for m in zf.infolist()
                if not m.filename.startswith("__MACOSX/")
                and not Path(m.filename).name.startswith(".")
            ]
            non_dirs = [m for m in members if not m.is_dir()]
            common_prefix = ""
            if non_dirs:
                first_parts = Path(non_dirs[0].filename).parts
                if len(first_parts) > 1:
                    candidate = first_parts[0] + "/"
                    if all(m.filename.startswith(candidate) for m in non_dirs):
                        common_prefix = candidate

            for member in members:
                ctrl.checkpoint()
                if member.is_dir():
                    continue

                rel_name = member.filename
                if common_prefix and rel_name.startswith(common_prefix):
                    rel_name = rel_name[len(common_prefix):]
                if not rel_name:
                    continue

                dest_file = (target_model_dir / rel_name).resolve()
                # Security: prevent zip-slip
                if not str(dest_file).startswith(str(target_model_dir.resolve())):
                    continue

                dest_file.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member, "r") as src_stream, open(dest_file, "wb") as dst_stream:
                    while True:
                        ctrl.checkpoint()
                        buf = src_stream.read(CHUNK_SIZE)
                        if not buf:
                            break
                        dst_stream.write(buf)
                        extracted_bytes += len(buf)
                        on_chunk(len(buf))
    except Exception as e:
        log(f"Warning: Extraction failed for {zip_path.name}: {e}")
        raise

    # Remove any stale zip files from destination model dir and asset dir
    for stale_dir in (target_model_dir, target_model_dir.parent):
        stale_file = stale_dir / zip_path.name
        if stale_file.exists():
            try:
                stale_file.unlink()
            except OSError:
                pass

    return extracted_bytes


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
    copied: int = 0
    total: int = 0
    items_done: int = 0
    items_total: int = 0
    current_item: str = ""
    current_file: str = ""
    started: float = field(default_factory=time.monotonic)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add_bytes(self, n: int) -> None:
        with self._lock:
            self.copied += n

    def snapshot(self) -> Tuple[int, int, float]:
        with self._lock:
            copied = self.copied
        elapsed = max(time.monotonic() - self.started, 1e-6)
        return copied, self.total, copied / elapsed


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
        emit("orga+ App", app_path.name)
        try:
            copy_orga_app(
                app_path,
                dest_root,
                ctrl,
                on_chunk=progress.add_bytes,
                log_cb=log,
                skip_existing=skip_existing,
            )
        except Exception as e:
            log(f"App copy warning: {e}")

    # 2. Copy Items (Assets with models)
    for it in items:
        ctrl.checkpoint()
        item_label = f"{it.job} / {it.category} / {it.title}"
        progress.current_item = item_label

        dest_asset = dest_root / it.job / it.category / it.asset.name
        dest_model_dir = dest_asset / "model"
        dest_asset.mkdir(parents=True, exist_ok=True)
        dest_model_dir.mkdir(parents=True, exist_ok=True)

        asset_files = _iter_asset_files(it.asset)

        # Separate model files from preview images and metadata
        model_files = [f for f in asset_files if f.suffix.lower() in MODEL_EXTS]
        other_files = [f for f in asset_files if f not in model_files]

        # Copy previews and metadata
        for f in other_files:
            ctrl.checkpoint()
            rel = f.relative_to(it.asset)
            dst_f = dest_asset / rel
            size = f.stat().st_size

            if skip_existing and dst_f.exists() and dst_f.stat().st_size == size:
                progress.add_bytes(size)
                continue

            emit(item_label, f.name)
            _fast_copy(f, dst_f, ctrl, progress.add_bytes)

        # Handle model files
        for mf in model_files:
            ctrl.checkpoint()
            is_zip_file = mf.suffix.lower() == ".zip"

            if is_zip_file and unzip_models:
                emit(item_label, f"Unzipping {mf.name} -> /model/")
                log(f"Unzipping model archive for {it.title} -> model/")
                safe_extract_zip(
                    mf,
                    dest_model_dir,
                    ctrl,
                    on_chunk=progress.add_bytes,
                    log_cb=log,
                )
            else:
                # Non-zip model: save into /model/ dir as requested
                dst_m = dest_model_dir / mf.name
                size = mf.stat().st_size
                if skip_existing and dst_m.exists() and dst_m.stat().st_size == size:
                    progress.add_bytes(size)
                    continue

                emit(item_label, mf.name)
                _fast_copy(mf, dst_m, ctrl, progress.add_bytes)

        progress.items_done += 1
        emit(item_label, "Done")

    emit("", "", force=True)
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

    for i, dest in enumerate(dests, 1):
        if ctrl.stopped:
            break
        log(f"=== [Disk {i}/{n}] Starting export to {dest} ===")

        def pcb(snap, item, fname, i=i):
            if progress_cb:
                progress_cb(snap, f"[Disk {i}/{n}] {item}", fname)

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
        # macOS: Volumes under /Volumes
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
        # Windows: Drive letters A-Z
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
        # Linux: /media, /mnt, /run/media
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
    for name in ("storage", "data"):
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
    font-weight: 600;
    font-size: 13px;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
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
}

QPushButton#primaryBtn:hover {
    background-color: #4F46E5;
}

QPushButton#primaryBtn:disabled {
    background-color: #3730A3;
    color: #94A3B8;
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

QListWidget, QTableWidget {
    background-color: #111827;
    border: 1px solid #26334D;
    border-radius: 8px;
    gridline-color: #1E293B;
    outline: none;
}

QListWidget::item, QTableWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid #161F30;
}

QListWidget::item:hover, QTableWidget::item:hover {
    background-color: #1E293B;
}

QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #26334D;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #161F30;
    color: #94A3B8;
    padding: 6px;
    border: none;
    border-right: 1px solid #26334D;
    border-bottom: 1px solid #26334D;
    font-weight: 600;
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

QCheckBox {
    spacing: 8px;
    color: #F8FAFC;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3B4B6E;
    border-radius: 4px;
    background-color: #161F30;
}

QCheckBox::indicator:checked {
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
    from PySide6.QtCore import QObject, Qt, QThread, Signal
    from PySide6.QtGui import QColor, QFont, QIcon
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
        QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
        QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
        QProgressBar, QPushButton, QSpinBox, QSplitter, QTableWidget,
        QTableWidgetItem, QVBoxLayout, QWidget,
    )

    class Signals(QObject):
        progress = Signal(int, int, float, str, str)
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
                    skip_existing=True,
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

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("orga+ Copy Tool")
    app.setStyleSheet(MODERN_DARK_QSS)

    win = QWidget()
    win.setWindowTitle("orga+ Copy Tool — High-Speed Multi-Disk Exporter")
    win.resize(1180, 840)
    win.setMinimumSize(950, 700)

    # Set icon if available
    icon_p = Path(__file__).resolve().parent.parent / "desktop" / "assets" / "icon.png"
    if icon_p.exists():
        win.setWindowIcon(QIcon(str(icon_p)))

    main_layout = QVBoxLayout(win)
    main_layout.setContentsMargins(14, 14, 14, 14)
    main_layout.setSpacing(12)

    # State
    ctrl = CopyController()
    signals = Signals()
    state: Dict[str, Any] = {
        "source": source,
        "items": [],
        "volumes": [],
        "app_path": find_orga_app(),
        "worker": None,
        "updating_table": False,
    }

    # ----------------------------------------------------------------------
    # Header Bar
    # ----------------------------------------------------------------------
    header_frame = QFrame()
    header_frame.setStyleSheet("background-color: #111827; border-radius: 10px; border: 1px solid #26334D; padding: 6px;")
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(12, 6, 12, 6)

    title_box = QVBoxLayout()
    title_lbl = QLabel("orga+ Copy Tool")
    title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
    subtitle_lbl = QLabel("Fast Multi-Disk Library Exporter • Models Only")
    subtitle_lbl.setStyleSheet("font-size: 11px; color: #818CF8; font-weight: 600;")
    title_box.addWidget(title_lbl)
    title_box.addWidget(subtitle_lbl)
    header_layout.addLayout(title_box)

    header_layout.addStretch(1)

    lib_lbl = QLabel("Library:")
    lib_lbl.setStyleSheet("color: #94A3B8; font-weight: 600;")
    header_layout.addWidget(lib_lbl)

    src_display = QLabel(state["source"])
    src_display.setStyleSheet("font-weight: 600; color: #38BDF8; background-color: #161F30; padding: 4px 10px; border-radius: 6px;")
    header_layout.addWidget(src_display)

    change_src_btn = QPushButton("Change…")
    header_layout.addWidget(change_src_btn)

    rescan_btn = QPushButton("🔄 Rescan")
    header_layout.addWidget(rescan_btn)

    main_layout.addWidget(header_frame)

    # ----------------------------------------------------------------------
    # Splitter: Left Sidebar (Disks, Limits, Options) | Right (Items Table)
    # ----------------------------------------------------------------------
    splitter = QSplitter(Qt.Horizontal)

    # LEFT PANEL
    left_panel = QWidget()
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(0, 0, 6, 0)
    left_layout.setSpacing(10)

    # 1. Disks Card
    disks_group = QGroupBox("1. Choose Target Disks")
    disks_layout = QVBoxLayout(disks_group)
    disks_layout.setContentsMargins(10, 14, 10, 10)

    disks_ctrl_row = QHBoxLayout()
    refresh_disks_btn = QPushButton("🔄 Refresh")
    add_disk_btn = QPushButton("➕ Add Folder/Disk…")
    select_all_disks_btn = QPushButton("All")
    disks_ctrl_row.addWidget(refresh_disks_btn)
    disks_ctrl_row.addWidget(add_disk_btn)
    disks_ctrl_row.addWidget(select_all_disks_btn)
    disks_layout.addLayout(disks_ctrl_row)

    disks_list = QListWidget()
    disks_list.setMaximumHeight(140)
    disks_layout.addWidget(disks_list)

    disks_status_lbl = QLabel("No disk selected")
    disks_status_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
    disks_layout.addWidget(disks_status_lbl)

    left_layout.addWidget(disks_group)

    # 2. Selection & Limits Card
    limits_group = QGroupBox("2. Selection Modes & Limits")
    limits_layout = QVBoxLayout(limits_group)
    limits_layout.setContentsMargins(10, 14, 10, 10)
    limits_layout.setSpacing(8)

    # Exact count mode
    count_row = QHBoxLayout()
    count_spin = QSpinBox()
    count_spin.setRange(1, 100000)
    count_spin.setValue(50)
    count_btn = QPushButton("Select Exact Count")
    count_row.addWidget(QLabel("Count:"))
    count_row.addWidget(count_spin, 1)
    count_row.addWidget(count_btn)
    limits_layout.addLayout(count_row)

    # Storage limit mode
    storage_row = QHBoxLayout()
    storage_spin = QDoubleSpinBox()
    storage_spin.setRange(0.1, 100000.0)
    storage_spin.setValue(16.0)
    storage_spin.setDecimals(1)
    unit_combo = QComboBox()
    unit_combo.addItems(["GB", "MB"])
    storage_btn = QPushButton("Select Storage Limit")
    storage_row.addWidget(QLabel("Limit:"))
    storage_row.addWidget(storage_spin, 1)
    storage_row.addWidget(unit_combo)
    storage_row.addWidget(storage_btn)
    limits_layout.addLayout(storage_row)

    # Fit disk button
    fit_disk_btn = QPushButton("⚡ Auto-Fit to Smallest Selected Disk")
    fit_disk_btn.setStyleSheet("background-color: #312E81; color: #C7D2FE; border-color: #4338CA;")
    limits_layout.addWidget(fit_disk_btn)

    left_layout.addWidget(limits_group)

    # 3. Options & Automation Card
    options_group = QGroupBox("3. Automation & Settings")
    options_layout = QVBoxLayout(options_group)
    options_layout.setContentsMargins(10, 14, 10, 10)
    options_layout.setSpacing(6)

    # Auto copy app
    auto_app_cb = QCheckBox("Auto-copy orga+ app to disk root")
    auto_app_cb.setChecked(True)
    options_layout.addWidget(auto_app_cb)

    app_info_row = QHBoxLayout()
    app_info_lbl = QLabel(
        f"App: {state['app_path'].name if state['app_path'] else 'Not detected'}"
    )
    app_info_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
    change_app_btn = QPushButton("Browse…")
    change_app_btn.setMaximumWidth(75)
    app_info_row.addWidget(app_info_lbl, 1)
    app_info_row.addWidget(change_app_btn)
    options_layout.addLayout(app_info_row)

    # Unzip model archives
    unzip_cb = QCheckBox("Unzip model into /model/ dir (remove .zip)")
    unzip_cb.setChecked(True)
    options_layout.addWidget(unzip_cb)

    # Resume support
    resume_cb = QCheckBox("Skip identical files (Fast Resume)")
    resume_cb.setChecked(True)
    options_layout.addWidget(resume_cb)

    # Streams
    stream_row = QHBoxLayout()
    stream_row.addWidget(QLabel("Parallel copy streams:"))
    workers_spin = QSpinBox()
    workers_spin.setRange(1, 8)
    workers_spin.setValue(workers)
    stream_row.addWidget(workers_spin)
    stream_row.addStretch(1)
    options_layout.addLayout(stream_row)

    left_layout.addWidget(options_group)
    left_layout.addStretch(1)
    splitter.addWidget(left_panel)

    # RIGHT PANEL (Items Table & Selection Controls)
    right_panel = QWidget()
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(6, 0, 0, 0)
    right_layout.setSpacing(8)

    # Filter / Search bar
    filter_row = QHBoxLayout()
    search_input = QLineEdit()
    search_input.setPlaceholderText("🔍 Search by title, subcategory, format…")
    category_combo = QComboBox()
    category_combo.addItem("All Categories")
    filter_row.addWidget(search_input, 1)
    filter_row.addWidget(category_combo)

    sel_all_btn = QPushButton("Select All")
    sel_none_btn = QPushButton("Select None")
    invert_sel_btn = QPushButton("Invert")
    filter_row.addWidget(sel_all_btn)
    filter_row.addWidget(sel_none_btn)
    filter_row.addWidget(invert_sel_btn)
    right_layout.addLayout(filter_row)

    # Summary pill
    summary_frame = QFrame()
    summary_frame.setStyleSheet("background-color: #161F30; border-radius: 8px; border: 1px solid #26334D; padding: 4px;")
    summary_layout = QHBoxLayout(summary_frame)
    summary_layout.setContentsMargins(12, 4, 12, 4)

    selection_status_lbl = QLabel("Selected: 0 items (0 B)")
    selection_status_lbl.setStyleSheet("font-weight: 700; color: #F8FAFC;")
    capacity_pill_lbl = QLabel("✓ Storage Status OK")
    capacity_pill_lbl.setStyleSheet("color: #10B981; font-weight: 600;")
    summary_layout.addWidget(selection_status_lbl)
    summary_layout.addStretch(1)
    summary_layout.addWidget(capacity_pill_lbl)
    right_layout.addWidget(summary_frame)

    # Items table
    items_table = QTableWidget()
    items_table.setColumnCount(6)
    items_table.setHorizontalHeaderLabels(["", "Category", "Subcategory", "Asset Title", "Format", "Size"])
    items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
    items_table.setColumnWidth(0, 36)
    items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
    items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
    items_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
    items_table.verticalHeader().setVisible(False)
    items_table.setSelectionBehavior(QTableWidget.SelectRows)
    right_layout.addWidget(items_table, 1)

    splitter.addWidget(right_panel)
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    main_layout.addWidget(splitter, 1)

    # ----------------------------------------------------------------------
    # Bottom Progress & Controls Section
    # ----------------------------------------------------------------------
    bottom_group = QFrame()
    bottom_group.setStyleSheet("background-color: #111827; border: 1px solid #26334D; border-radius: 10px; padding: 10px;")
    bottom_layout = QVBoxLayout(bottom_group)
    bottom_layout.setContentsMargins(12, 10, 12, 10)
    bottom_layout.setSpacing(8)

    # Status & Speed row
    status_row = QHBoxLayout()
    status_lbl = QLabel("Ready.")
    status_lbl.setStyleSheet("font-weight: 600; color: #38BDF8;")
    speed_eta_lbl = QLabel("0.0 MB/s • ETA: --:--")
    speed_eta_lbl.setStyleSheet("color: #94A3B8; font-weight: 600;")
    status_row.addWidget(status_lbl, 1)
    status_row.addWidget(speed_eta_lbl)
    bottom_layout.addLayout(status_row)

    # Progress bar
    bar = QProgressBar()
    bar.setRange(0, 1000)
    bar.setValue(0)
    bar.setFormat("%p%")
    bottom_layout.addWidget(bar)

    # Control buttons row
    btn_row = QHBoxLayout()
    start_btn = QPushButton("▶ Start Copy to Disks")
    start_btn.setObjectName("primaryBtn")
    start_btn.setMinimumHeight(38)
    start_btn.setMinimumWidth(160)

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

    # Collapsible log view
    log_view = QPlainTextEdit()
    log_view.setReadOnly(True)
    log_view.setMaximumBlockCount(3000)
    log_view.setFixedHeight(130)
    log_view.setVisible(False)
    bottom_layout.addWidget(log_view)

    main_layout.addWidget(bottom_group)

    # ----------------------------------------------------------------------
    # Helper Functions & UI Logic
    # ----------------------------------------------------------------------

    def log_msg(msg: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        log_view.appendPlainText(f"[{ts}] {msg}")

    def get_selected_disks() -> List[VolumeInfo]:
        chosen: List[VolumeInfo] = []
        for i in range(disks_list.count()):
            item = disks_list.item(i)
            if item.checkState() == Qt.Checked:
                chosen.append(item.data(Qt.UserRole))
        return chosen

    def refresh_disks() -> None:
        disks_list.clear()
        vols = list_volumes()
        state["volumes"] = vols

        for v in vols:
            item = QListWidgetItem(f"💾 {v.label}  ({v.path})  —  {human_size(v.free)} free / {human_size(v.total)}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if v.is_removable else Qt.Unchecked)
            item.setData(Qt.UserRole, v)
            disks_list.addItem(item)

        if not vols:
            item = QListWidgetItem("No removable volumes detected. Click 'Add Folder/Disk…'")
            item.setFlags(Qt.NoItemFlags)
            disks_list.addItem(item)

        update_disks_status()

    def update_disks_status() -> None:
        chosen = get_selected_disks()
        if not chosen:
            disks_status_lbl.setText("⚠️ No target disk selected.")
            disks_status_lbl.setStyleSheet("color: #F59E0B; font-weight: 600;")
        else:
            free_caps = [f"{v.label}: {human_size(v.free)}" for v in chosen]
            disks_status_lbl.setText(f"{len(chosen)} disk(s) selected: " + " | ".join(free_caps))
            disks_status_lbl.setStyleSheet("color: #10B981; font-weight: 600;")
        update_selection_summary()

    def get_selected_items() -> List[CopyItem]:
        selected = []
        for r in range(items_table.rowCount()):
            cb_item = items_table.item(r, 0)
            if cb_item and cb_item.checkState() == Qt.Checked:
                item_data = cb_item.data(Qt.UserRole)
                if item_data:
                    selected.append(item_data)
        return selected

    def update_selection_summary() -> None:
        selected = get_selected_items()
        total_bytes = sum(it.total_bytes for it in selected)
        app_size = get_app_size(state["app_path"]) if (auto_app_cb.isChecked() and state["app_path"]) else 0
        grand_total = total_bytes + app_size

        selection_status_lbl.setText(
            f"Selected: {len(selected)} / {len(state['items'])} items "
            f"({human_size(total_bytes)}" + (f" + {human_size(app_size)} app" if app_size else "") + ")"
        )

        chosen_disks = get_selected_disks()
        if not chosen_disks:
            capacity_pill_lbl.setText("Select target disk")
            capacity_pill_lbl.setStyleSheet("color: #F59E0B; font-weight: 600;")
            return

        min_free = min(d.free for d in chosen_disks)
        if grand_total > min_free:
            over = grand_total - min_free
            capacity_pill_lbl.setText(f"⚠️ Exceeds space by {human_size(over)}!")
            capacity_pill_lbl.setStyleSheet("color: #EF4444; font-weight: 700;")
        else:
            remaining = min_free - grand_total
            capacity_pill_lbl.setText(f"✓ Fits comfortably ({human_size(remaining)} remaining)")
            capacity_pill_lbl.setStyleSheet("color: #10B981; font-weight: 600;")

    def populate_table() -> None:
        state["updating_table"] = True
        items_table.setRowCount(0)
        category_combo.blockSignals(True)
        category_combo.clear()
        category_combo.addItem("All Categories")

        categories = sorted({it.job for it in state["items"]})
        for c in categories:
            category_combo.addItem(c)
        category_combo.blockSignals(False)

        items_table.setRowCount(len(state["items"]))
        for r, it in enumerate(state["items"]):
            # Checkbox col
            cb_item = QTableWidgetItem()
            cb_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            cb_item.setCheckState(Qt.Checked)
            cb_item.setData(Qt.UserRole, it)
            items_table.setItem(r, 0, cb_item)

            # Category
            c_item = QTableWidgetItem(it.job)
            c_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 1, c_item)

            # Subcategory
            sub_item = QTableWidgetItem(it.category)
            sub_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 2, sub_item)

            # Title
            t_item = QTableWidgetItem(it.title)
            t_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 3, t_item)

            # Format
            fmt_lbl = f"{it.model_format}" + (" (unzip)" if it.is_zip else "")
            f_item = QTableWidgetItem(fmt_lbl)
            f_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 4, f_item)

            # Size
            s_item = QTableWidgetItem(human_size(it.total_bytes))
            s_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            s_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items_table.setItem(r, 5, s_item)

        state["updating_table"] = False
        update_selection_summary()

    def filter_table() -> None:
        query = search_input.text().strip().lower()
        cat_filter = category_combo.currentText()

        for r in range(items_table.rowCount()):
            it = items_table.item(r, 0).data(Qt.UserRole)
            matches_cat = (cat_filter == "All Categories") or (it.job == cat_filter)
            matches_query = (
                not query
                or (query in it.title.lower())
                or (query in it.category.lower())
                or (query in it.job.lower())
                or (query in it.model_format.lower())
            )
            items_table.setRowHidden(r, not (matches_cat and matches_query))

    def load_library(path_str: str) -> None:
        state["source"] = path_str
        src_display.setText(path_str)
        log_msg(f"Scanning library: {path_str}")

        items, skipped = scan_items(Path(path_str))
        state["items"] = items
        populate_table()

        total_bytes = sum(it.total_bytes for it in items)
        log_msg(
            f"Scan complete: {len(items)} items with 3D models ({human_size(total_bytes)}). "
            f"{skipped} items skipped (no model)."
        )

    # ----------------------------------------------------------------------
    # Selection Mode Actions
    # ----------------------------------------------------------------------

    def apply_exact_count() -> None:
        count = count_spin.value()
        state["updating_table"] = True
        matched = 0
        for r in range(items_table.rowCount()):
            if not items_table.isRowHidden(r):
                cb_item = items_table.item(r, 0)
                if matched < count:
                    cb_item.setCheckState(Qt.Checked)
                    matched += 1
                else:
                    cb_item.setCheckState(Qt.Unchecked)
        state["updating_table"] = False
        update_selection_summary()
        log_msg(f"Applied exact count: selected {matched} items.")

    def apply_storage_limit() -> None:
        unit_mult = 1024 * 1024 * 1024 if unit_combo.currentText() == "GB" else 1024 * 1024
        limit_bytes = int(storage_spin.value() * unit_mult)

        state["updating_table"] = True
        accum = 0
        selected_count = 0
        for r in range(items_table.rowCount()):
            cb_item = items_table.item(r, 0)
            if items_table.isRowHidden(r):
                cb_item.setCheckState(Qt.Unchecked)
                continue
            it = cb_item.data(Qt.UserRole)
            if accum + it.total_bytes <= limit_bytes:
                cb_item.setCheckState(Qt.Checked)
                accum += it.total_bytes
                selected_count += 1
            else:
                cb_item.setCheckState(Qt.Unchecked)

        state["updating_table"] = False
        update_selection_summary()
        log_msg(f"Applied storage limit: selected {selected_count} items ({human_size(accum)}) within {storage_spin.value()} {unit_combo.currentText()}.")

    def apply_fit_disk() -> None:
        chosen = get_selected_disks()
        if not chosen:
            QMessageBox.warning(win, "No Target Disk", "Select at least one target disk first.")
            return

        min_free = min(d.free for d in chosen)
        app_size = get_app_size(state["app_path"]) if (auto_app_cb.isChecked() and state["app_path"]) else 0
        safety_reserve = 500 * 1024 * 1024 + app_size
        usable = max(0, min_free - safety_reserve)

        state["updating_table"] = True
        accum = 0
        selected_count = 0
        for r in range(items_table.rowCount()):
            cb_item = items_table.item(r, 0)
            if items_table.isRowHidden(r):
                cb_item.setCheckState(Qt.Unchecked)
                continue
            it = cb_item.data(Qt.UserRole)
            if accum + it.total_bytes <= usable:
                cb_item.setCheckState(Qt.Checked)
                accum += it.total_bytes
                selected_count += 1
            else:
                cb_item.setCheckState(Qt.Unchecked)

        state["updating_table"] = False
        update_selection_summary()
        log_msg(f"Auto-fit to disk free space: selected {selected_count} items ({human_size(accum)}), leaving safety margin on all selected disks.")

    # ----------------------------------------------------------------------
    # Copy Process Controls
    # ----------------------------------------------------------------------

    def set_running_state(running: bool) -> None:
        start_btn.setEnabled(not running)
        pause_btn.setEnabled(running)
        stop_btn.setEnabled(running)
        change_src_btn.setEnabled(not running)
        rescan_btn.setEnabled(not running)
        refresh_disks_btn.setEnabled(not running)
        add_disk_btn.setEnabled(not running)
        count_btn.setEnabled(not running)
        storage_btn.setEnabled(not running)
        fit_disk_btn.setEnabled(not running)
        sel_all_btn.setEnabled(not running)
        sel_none_btn.setEnabled(not running)
        invert_sel_btn.setEnabled(not running)
        if not running:
            pause_btn.setText("⏸ Pause")

    def on_progress(copied: int, total: int, speed: float, item_lbl: str, file_lbl: str) -> None:
        pct = int(copied / total * 1000) if total else 0
        bar.setValue(pct)
        remaining = max(total - copied, 0)
        eta = remaining / speed if speed > 0 else 0
        status_lbl.setText(f"{item_lbl}  [{file_lbl}]")
        speed_eta_lbl.setText(
            f"{human_size(copied)} / {human_size(total)} • {human_size(speed)}/s • ETA {int(eta//60):02d}:{int(eta%60):02d}"
        )

    def on_finished(summary: dict) -> None:
        set_running_state(False)
        bar.setValue(1000)
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
        chosen_disks = get_selected_disks()
        if not chosen_disks:
            QMessageBox.warning(win, "No Disk Selected", "Please select at least one destination disk or folder.")
            return

        selected_items = get_selected_items()
        if not selected_items:
            QMessageBox.warning(win, "No Items Selected", "Please select at least one item with a model to copy.")
            return

        # Check space
        total_needed = sum(it.total_bytes for it in selected_items)
        app_size = get_app_size(state["app_path"]) if (auto_app_cb.isChecked() and state["app_path"]) else 0
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
            workers=workers_spin.value(),
            auto_copy_app=auto_app_cb.isChecked(),
            app_path=state["app_path"] if auto_app_cb.isChecked() else None,
            unzip_models=unzip_cb.isChecked(),
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
            log_msg("Transfer resumed.")
        else:
            ctrl.pause()
            pause_btn.setText("▶ Resume")
            log_msg("Transfer paused.")

    def stop_copy() -> None:
        ctrl.stop()
        log_msg("Stop requested. Unwinding and cleaning partial files…")

    # ----------------------------------------------------------------------
    # Event Connections
    # ----------------------------------------------------------------------
    change_src_btn.clicked.connect(lambda: _choose_src())
    rescan_btn.clicked.connect(lambda: load_library(state["source"]))
    refresh_disks_btn.clicked.connect(refresh_disks)
    add_disk_btn.clicked.connect(lambda: _add_custom_disk())
    select_all_disks_btn.clicked.connect(lambda: _toggle_all_disks())
    disks_list.itemChanged.connect(lambda *_: update_disks_status())

    count_btn.clicked.connect(apply_exact_count)
    storage_btn.clicked.connect(apply_storage_limit)
    fit_disk_btn.clicked.connect(apply_fit_disk)

    search_input.textChanged.connect(filter_table)
    category_combo.currentIndexChanged.connect(filter_table)

    sel_all_btn.clicked.connect(lambda: _set_table_selection(True))
    sel_none_btn.clicked.connect(lambda: _set_table_selection(False))
    invert_sel_btn.clicked.connect(lambda: _invert_table_selection())

    items_table.itemChanged.connect(lambda item: update_selection_summary() if not state["updating_table"] and item.column() == 0 else None)

    change_app_btn.clicked.connect(lambda: _choose_app())
    auto_app_cb.toggled.connect(lambda *_: update_selection_summary())

    toggle_log_btn.clicked.connect(lambda: log_view.setVisible(not log_view.isVisible()))

    start_btn.clicked.connect(start_copy)
    pause_btn.clicked.connect(toggle_pause)
    stop_btn.clicked.connect(stop_copy)

    def _choose_src():
        d = QFileDialog.getExistingDirectory(win, "Choose Library Root Directory", state["source"])
        if d:
            load_library(d)

    def _add_custom_disk():
        d = QFileDialog.getExistingDirectory(win, "Choose Destination Disk or Folder")
        if d:
            p = str(Path(d).resolve())
            try:
                u = shutil.disk_usage(p)
                v = VolumeInfo(Path(p).name or p, p, u.free, u.total, True)
                item = QListWidgetItem(f"📁 {v.label}  ({v.path})  —  {human_size(v.free)} free / {human_size(v.total)}")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, v)
                disks_list.addItem(item)
                update_disks_status()
                log_msg(f"Added custom destination: {p}")
            except OSError as e:
                QMessageBox.warning(win, "Error", f"Could not access {p}: {e}")

    def _toggle_all_disks():
        for i in range(disks_list.count()):
            it = disks_list.item(i)
            it.setCheckState(Qt.Checked)
        update_disks_status()

    def _choose_app():
        path, _ = QFileDialog.getOpenFileName(win, "Select orga+ Application", str(Path.cwd()))
        if not path:
            path = QFileDialog.getExistingDirectory(win, "Select orga+ .app Bundle")
        if path:
            state["app_path"] = Path(path).resolve()
            app_info_lbl.setText(f"App: {state['app_path'].name}")
            log_msg(f"Selected custom app: {state['app_path']}")
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

    # Initial load
    refresh_disks()
    if initial_dest:
        try:
            u = shutil.disk_usage(initial_dest)
            v = VolumeInfo(Path(initial_dest).name, initial_dest, u.free, u.total, True)
            item = QListWidgetItem(f"💾 {v.label}  ({v.path})  —  {human_size(v.free)} free / {human_size(v.total)}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, v)
            disks_list.addItem(item)
            update_disks_status()
        except OSError:
            pass

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
    parser.add_argument("--source", default=default_source(), help="source library folder")
    parser.add_argument(
        "--dest", action="append", default=[],
        help="destination drive or folder (repeat for multiple)",
    )
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="parallel copy streams")
    parser.add_argument("--limit-count", type=int, default=0, help="copy exact first N items")
    parser.add_argument("--limit-size-gb", type=float, default=0.0, help="storage limit in GB")
    parser.add_argument("--no-auto-app", action="store_true", help="do not auto-copy the orga+ app")
    parser.add_argument("--app-path", default=None, help="custom path to orga+ app")
    parser.add_argument("--no-unzip", action="store_true", help="do not unzip model archives")
    parser.add_argument("--no-skip-existing", action="store_true", help="re-copy files already present")
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

    items, skipped = scan_items(Path(args.source))
    print(f"Found {len(items)} items with 3D models ({skipped} items without models skipped).")
    if not items:
        return 0

    if args.limit_count > 0:
        items = items[:args.limit_count]
        print(f"Applying count limit: selected {len(items)} items.")
    elif args.limit_size_gb > 0:
        limit_bytes = int(args.limit_size_gb * 1024 * 1024 * 1024)
        filtered = []
        tot = 0
        for it in items:
            if tot + it.total_bytes <= limit_bytes:
                filtered.append(it)
                tot += it.total_bytes
        items = filtered
        print(f"Applying storage limit: selected {len(items)} items ({human_size(tot)}).")

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
