#!/usr/bin/env python3
"""
orga+ Copy Tool
===============

Standalone utility that copies library items to a USB / flash drive at the
fastest practical speed.

Rules
-----
* Only items that actually contain a model file are copied. Items without a
  model are skipped and never written to the destination.
* The full item folder is copied (previews + ``model/`` + ``meta.json``) so the
  copy stays a valid 3-level asset: ``<Job>/<Category>/<Asset>``.
* Files already present on the destination with the same size are skipped, so a
  re-run resumes instead of re-copying everything.

Controls
--------
* Start / Pause / Resume / Stop (Stop removes the partial file being written).

The same engine powers both the GUI and ``--headless`` mode.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Tuple

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

MODEL_EXTS = {
    ".skp", ".obj", ".fbx", ".blend", ".zip", ".rar", ".7z",
    ".3ds", ".max", ".c4d", ".glb", ".gltf", ".stl", ".dae", ".dxf",
}

# 16 MiB chunks: fewer syscalls than the 64 KiB default -> higher sustained
# throughput on USB flash drives, while still allowing pause/stop mid-file.
CHUNK_SIZE = 16 * 1024 * 1024

# One sequential write stream is usually the fastest (and safest) way to fill a
# flash drive. Bump --workers only when copying many small files.
DEFAULT_WORKERS = 1


class CopyStopped(Exception):
    """Raised internally to unwind workers when the user hits Stop."""


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class CopyItem:
    job: str
    category: str
    asset: Path
    title: str
    total_bytes: int = 0

    @property
    def rel_parts(self) -> Tuple[str, str, str]:
        return (self.job, self.category, self.asset.name)


# --------------------------------------------------------------------------
# Library scanning (self-contained; no dependency on the desktop app)
# --------------------------------------------------------------------------

def _visible(p: Path) -> bool:
    return not p.name.startswith(".")


def has_model(asset: Path) -> bool:
    """True when the asset folder contains a model file (model/ dir or root)."""
    model_dir = asset / "model"
    if model_dir.is_dir():
        for f in model_dir.iterdir():
            if f.is_file() and _visible(f):
                return True
        return False
    for f in asset.iterdir():
        if f.is_file() and _visible(f) and f.suffix.lower() in MODEL_EXTS:
            return True
    return False


def _looks_like_asset(p: Path) -> bool:
    """A folder that is itself an asset is not a Job/Category container."""
    if (p / "model").is_dir():
        return True
    if (p / "images").is_dir():
        return True
    if (p / "meta.json").exists():
        return True
    return False


def scan_items(root: Path) -> Tuple[List[CopyItem], int]:
    """Walk ``root/<Job>/<Category>/<Asset>`` and return (items_with_model, skipped)."""
    items: List[CopyItem] = []
    skipped = 0
    root = Path(root)
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
                title = asset.name
                meta = asset / "meta.json"
                if meta.exists():
                    try:
                        title = json.loads(meta.read_text(encoding="utf-8")).get("title") or title
                    except Exception:
                        pass
                items.append(CopyItem(job.name, category.name, asset, title))
    return items, skipped


def _iter_asset_files(asset: Path) -> List[Path]:
    out: List[Path] = []
    for p in asset.rglob("*"):
        if not p.is_file():
            continue
        if any(part.startswith(".") for part in p.relative_to(asset).parts):
            continue
        out.append(p)
    return out


def build_jobs(items: List[CopyItem]) -> List[Tuple[Path, Path, int, CopyItem]]:
    """Expand items into (src, dst, size, item) jobs, largest files first."""
    jobs: List[Tuple[Path, Path, int, CopyItem]] = []
    for it in items:
        files = _iter_asset_files(it.asset)
        it.total_bytes = sum(f.stat().st_size for f in files)
        for src in files:
            rel = src.relative_to(it.asset)
            jobs.append((src, None, src.stat().st_size, it))  # dst filled by caller
    # Largest first => extends the sequential stream with the biggest payloads.
    jobs.sort(key=lambda j: j[2], reverse=True)
    return jobs


# --------------------------------------------------------------------------
# Pause / Stop controller
# --------------------------------------------------------------------------

class CopyController:
    def __init__(self) -> None:
        self._paused = threading.Event()
        self._stop = threading.Event()
        self._lock = threading.Lock()

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
# Fast copy engine
# --------------------------------------------------------------------------

def _fast_copy(src: Path, dst: Path, ctrl: CopyController, on_chunk: Callable[[int], None]) -> str:
    """Copy one file with a chunked loop so pause/stop work mid-file.

    Returns a human label describing the method used.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    method = "buffered"

    # Remove a stale partial file so a stopped run leaves nothing behind.
    if dst.exists():
        dst.unlink()

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
        # Never leave a half-written file behind (Stop or any I/O failure).
        try:
            dst.unlink()
        except OSError:
            pass
        raise
    return method


@dataclass
class Progress:
    copied: int = 0
    total: int = 0
    files_done: int = 0
    files_total: int = 0
    skipped_files: int = 0
    skipped_bytes: int = 0
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


def run_copy(
    items: List[CopyItem],
    dest_root: Path,
    ctrl: CopyController,
    *,
    workers: int = DEFAULT_WORKERS,
    skip_existing: bool = True,
    progress_cb: Optional[Callable[[Tuple[int, int, float], str, str], None]] = None,
    log_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    """Copy every file of ``items`` under ``dest_root/<Job>/<Category>/<Asset>``."""
    dest_root = Path(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    log = log_cb or (lambda m: None)

    # Build concrete (src, dst, size, item) jobs.
    jobs: List[Tuple[Path, Path, int, CopyItem]] = []
    for src, _dst, size, it in build_jobs(items):
        dst = dest_root / it.job / it.category / it.asset.name / src.relative_to(it.asset)
        jobs.append((src, dst, size, it))

    total = sum(j[2] for j in jobs)
    progress = Progress(total=total, files_total=len(jobs))

    # Throttled progress emission (~10 Hz) so the GUI stays light.
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
    if total > free:
        raise IOError(
            f"Not enough space on destination: need {total/1e9:.2f} GB, "
            f"free {free/1e9:.2f} GB"
        )

    log(f"Copying {len(jobs)} files ({total/1e6:.1f} MB) -> {dest_root}")

    def handle(src: Path, dst: Path, size: int, it: CopyItem) -> None:
        label = f"{it.job}/{it.category}/{it.title}"
        progress.current_item = label
        progress.current_file = src.name
        if skip_existing and dst.exists() and dst.stat().st_size == size:
            progress.skipped_files += 1
            progress.skipped_bytes += size
            progress.add_bytes(size)  # count as done for progress/ETA
            progress.files_done += 1
            return
        emit(label, src.name)
        _fast_copy(src, dst, ctrl, progress.add_bytes)
        progress.files_done += 1
        emit(label, src.name)

    try:
        if workers <= 1:
            for src, dst, size, it in jobs:
                ctrl.checkpoint()
                handle(src, dst, size, it)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(handle, *j) for j in jobs]
                for fut in futures:
                    ctrl.checkpoint()
                    fut.result()
    except CopyStopped:
        log("Stopped by user.")
        return _summary(progress, stopped=True)

    emit("", "", force=True)
    log("Done.")
    return _summary(progress, stopped=False)


def run_copy_multi(
    items: List[CopyItem],
    dests: List[Path],
    ctrl: CopyController,
    *,
    workers: int = DEFAULT_WORKERS,
    skip_existing: bool = True,
    progress_cb: Optional[Callable[[Tuple[int, int, float], str, str], None]] = None,
    log_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    """Copy the same items to several destinations, one destination at a time.

    Sequential fan-out: each drive gets the full set before moving to the next,
    so drives never share USB bandwidth.
    """
    dests = [Path(d) for d in dests]
    log = log_cb or (lambda m: None)
    results: List[dict] = []
    n = len(dests)

    for i, dest in enumerate(dests, 1):
        if ctrl.stopped:
            break
        log(f"[Drive {i}/{n}] -> {dest}")

        def pcb(snap, item, fname, i=i):
            if progress_cb:
                progress_cb(snap, f"[{i}/{n}] {item}", fname)

        try:
            r = run_copy(
                items, dest, ctrl, workers=workers, skip_existing=skip_existing,
                progress_cb=pcb, log_cb=log_cb,
            )
        except Exception as e:  # noqa: BLE001
            log(f"[Drive {i}/{n}] FAILED: {e}")
            r = {"error": str(e), "stopped": False}

        results.append({"dest": str(dest), **r})
        if r.get("stopped"):
            break

    return {"destinations": results, "stopped": ctrl.stopped}


def _summary(progress: Progress, stopped: bool) -> dict:
    copied, total, _ = progress.snapshot()
    return {
        "stopped": stopped,
        "copied_bytes": copied,
        "total_bytes": total,
        "files_done": progress.files_done,
        "files_total": progress.files_total,
        "files_skipped": progress.skipped_files,
    }


# --------------------------------------------------------------------------
# Destination helpers
# --------------------------------------------------------------------------

def list_volumes() -> List[Tuple[str, str, int, int]]:
    """Return (label, path, free, total) for mounted volumes (macOS + Linux)."""
    out: List[Tuple[str, str, int, int]] = []
    candidates = []
    if sys.platform == "darwin":
        candidates = [Path("/Volumes")]
    elif sys.platform.startswith("linux"):
        candidates = [Path("/media"), Path("/mnt"), Path("/run/media")]
    for base in candidates:
        if not base.is_dir():
            continue
        for vol in sorted(base.iterdir()):
            try:
                if not vol.is_dir() or vol.is_symlink():
                    continue
                u = shutil.disk_usage(vol)
                out.append((vol.name, str(vol), u.free, u.total))
            except OSError:
                continue
    return out


def default_source() -> str:
    try:
        import config  # type: ignore
        return str(config.DATA_DIR)
    except Exception:
        pass
    here = Path(__file__).resolve().parent.parent
    for name in ("storage", "data"):
        if (here / name).is_dir():
            return str(here / name)
    return str(here / "storage")


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

def run_gui(source: str, dest: str, workers: int) -> int:
    from PySide6.QtCore import QObject, Qt, QThread, Signal
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
        QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
        QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget,
    )

    class Signals(QObject):
        progress = Signal(int, int, float, str, str)
        log = Signal(str)
        finished = Signal(dict)
        error = Signal(str)

    class Worker(QThread):
        def __init__(self, items, dests, ctrl, workers, signals):
            super().__init__()
            self.items, self.dests, self.ctrl = items, dests, ctrl
            self.workers, self.signals = workers, signals

        def run(self):
            try:
                summary = run_copy_multi(
                    self.items, self.dests, self.ctrl, workers=self.workers,
                    progress_cb=lambda snap, it, f: self.signals.progress.emit(
                        snap[0], snap[1], snap[2], it, f),
                    log_cb=lambda m: self.signals.log.emit(m),
                )
                self.signals.finished.emit(summary)
            except Exception as e:  # noqa: BLE001
                self.signals.error.emit(str(e))

    app = QApplication(sys.argv)
    app.setApplicationName("orga+ Copy Tool")

    win = QWidget()
    win.setWindowTitle("orga+ Copy Tool — copy items with models to a flash drive")
    win.resize(820, 620)
    root = QVBoxLayout(win)

    # Source
    src_row = QHBoxLayout()
    src_row.addWidget(QLabel("Library:"))
    src_label = QLabel(source)
    src_label.setStyleSheet("font-weight:600")
    src_row.addWidget(src_label, 1)
    rescan_btn = QPushButton("Rescan")
    src_row.addWidget(rescan_btn)
    root.addLayout(src_row)

    # Destinations (one or more drives, copied sequentially)
    root.addWidget(QLabel("Destinations — copied one after another:"))
    dest_list = QListWidget()
    dest_list.setMaximumHeight(96)
    root.addWidget(dest_list)
    dst_row = QHBoxLayout()
    vol_combo = QComboBox()
    vol_combo.setMinimumWidth(240)
    dst_row.addWidget(vol_combo)
    add_vol_btn = QPushButton("Add drive")
    dst_row.addWidget(add_vol_btn)
    browse_btn = QPushButton("Add folder…")
    dst_row.addWidget(browse_btn)
    remove_btn = QPushButton("Remove")
    dst_row.addWidget(remove_btn)
    free_label = QLabel("")
    dst_row.addWidget(free_label, 1)
    root.addLayout(dst_row)

    # Item list
    list_label = QLabel("")
    root.addWidget(list_label)
    item_list = QListWidget()
    root.addWidget(item_list, 1)

    sel_row = QHBoxLayout()
    all_btn = QPushButton("Select all")
    none_btn = QPushButton("Select none")
    sel_row.addWidget(all_btn)
    sel_row.addWidget(none_btn)
    sel_row.addStretch(1)
    sel_row.addWidget(QLabel("Parallel streams:"))
    workers_spin = QSpinBox()
    workers_spin.setRange(1, 8)
    workers_spin.setValue(workers)
    sel_row.addWidget(workers_spin)
    root.addLayout(sel_row)

    # Progress
    bar = QProgressBar()
    bar.setRange(0, 1000)
    root.addWidget(bar)
    info = QLabel("Idle")
    root.addWidget(info)

    # Controls
    ctrl_row = QHBoxLayout()
    start_btn = QPushButton("Start")
    pause_btn = QPushButton("Pause")
    stop_btn = QPushButton("Stop")
    pause_btn.setEnabled(False)
    stop_btn.setEnabled(False)
    ctrl_row.addWidget(start_btn)
    ctrl_row.addWidget(pause_btn)
    ctrl_row.addWidget(stop_btn)
    ctrl_row.addStretch(1)
    root.addLayout(ctrl_row)

    log_view = QPlainTextEdit()
    log_view.setReadOnly(True)
    log_view.setMaximumBlockCount(2000)
    root.addWidget(log_view, 1)

    signals = Signals()
    ctrl = CopyController()
    state = {"worker": None, "items": [], "selected_src": source}

    def human(n: float) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    def refresh_volumes():
        vol_combo.clear()
        vols = list_volumes()
        for label, path, free, total in vols:
            vol_combo.addItem(f"{label}  ({human(free)} free)", path)
        if not vols:
            vol_combo.addItem("No removable volume detected — use Add folder…", "")
        update_free()

    def destinations() -> List[str]:
        return [dest_list.item(i).data(Qt.UserRole) for i in range(dest_list.count())]

    def add_destination(path: str):
        if not path:
            return
        if path in destinations():
            on_log(f"Already added: {path}")
            return
        try:
            free = shutil.disk_usage(path).free
            label = f"{path}   ({human(free)} free)"
        except OSError:
            label = path
        li = QListWidgetItem(label)
        li.setData(Qt.UserRole, path)
        dest_list.addItem(li)
        on_log(f"Added destination: {path}")

    def highlighted_dest() -> str:
        it = dest_list.currentItem()
        return it.data(Qt.UserRole) if it else ""

    def update_free():
        d = highlighted_dest()
        if d:
            try:
                free_label.setText(f"{human(shutil.disk_usage(d).free)} free")
                return
            except OSError:
                pass
        free_label.setText("")

    def load_items():
        item_list.clear()
        items, skipped = scan_items(Path(state["selected_src"]))
        state["items"] = items
        for it in items:
            files = _iter_asset_files(it.asset)
            size = sum(f.stat().st_size for f in files)
            it.total_bytes = size
            li = QListWidgetItem(
                f"{it.job} / {it.category} / {it.title}   —   {human(size)}  ({len(files)} files)")
            li.setFlags(li.flags() | Qt.ItemIsUserCheckable)
            li.setCheckState(Qt.Checked)
            li.setData(Qt.UserRole, it)
            item_list.addItem(li)
        total = sum(it.total_bytes for it in items)
        list_label.setText(
            f"{len(items)} items with a model ({human(total)}) • "
            f"{skipped} items skipped (no model)")
        log_view.appendPlainText(
            f"Scanned {state['selected_src']}: {len(items)} items with model, {skipped} skipped.")

    def selected_items() -> List[CopyItem]:
        out = []
        for i in range(item_list.count()):
            li = item_list.item(i)
            if li.checkState() == Qt.Checked:
                out.append(li.data(Qt.UserRole))
        return out

    # Signals -> GUI
    def on_progress(copied, total, speed, item, fname):
        pct = int(copied / total * 1000) if total else 0
        bar.setValue(pct)
        remaining = max(total - copied, 0)
        eta = remaining / speed if speed > 0 else 0
        info.setText(
            f"{human(copied)} / {human(total)}  •  {human(speed)}/s  •  "
            f"ETA {int(eta//60):02d}:{int(eta%60):02d}  •  {item}  [{fname}]")

    def on_log(msg):
        log_view.appendPlainText(msg)

    def on_finished(_):
        _set_running(False)
        bar.setValue(1000)
        info.setText("Finished.")
        on_log("Copy finished successfully.")

    def on_error(msg):
        _set_running(False)
        QMessageBox.critical(win, "Copy error", msg)
        on_log(f"ERROR: {msg}")

    signals.progress.connect(on_progress)
    signals.log.connect(on_log)
    signals.finished.connect(on_finished)
    signals.error.connect(on_error)

    def _set_running(run: bool):
        start_btn.setEnabled(not run)
        pause_btn.setEnabled(run)
        stop_btn.setEnabled(run)
        rescan_btn.setEnabled(not run)
        browse_btn.setEnabled(not run)
        add_vol_btn.setEnabled(not run)
        remove_btn.setEnabled(not run)
        vol_combo.setEnabled(not run)
        dest_list.setEnabled(not run)
        workers_spin.setEnabled(not run)
        if not run:
            pause_btn.setText("Pause")

    def start():
        dests = destinations()
        if not dests:
            QMessageBox.warning(win, "No destination", "Add at least one flash drive or folder.")
            return
        items = selected_items()
        if not items:
            QMessageBox.warning(win, "No items", "Select at least one item to copy.")
            return
        ctrl.resume()
        state["worker"] = Worker(items, dests, ctrl, workers_spin.value(), signals)
        state["worker"].start()
        _set_running(True)
        log_view.appendPlainText(
            f"Started copying {len(items)} items to {len(dests)} destination(s)")

    def toggle_pause():
        if ctrl.paused:
            ctrl.resume()
            pause_btn.setText("Pause")
            on_log("Resumed.")
        else:
            ctrl.pause()
            pause_btn.setText("Resume")
            on_log("Paused.")

    def stop():
        ctrl.stop()
        on_log("Stop requested …")

    start_btn.clicked.connect(start)
    pause_btn.clicked.connect(toggle_pause)
    stop_btn.clicked.connect(stop)
    all_btn.clicked.connect(lambda: [item_list.item(i).setCheckState(Qt.Checked) for i in range(item_list.count())])
    none_btn.clicked.connect(lambda: [item_list.item(i).setCheckState(Qt.Unchecked) for i in range(item_list.count())])
    rescan_btn.clicked.connect(load_items)
    vol_combo.currentIndexChanged.connect(update_free)
    dest_list.currentItemChanged.connect(lambda *_: update_free())
    browse_btn.clicked.connect(lambda: _browse())
    add_vol_btn.clicked.connect(lambda: add_destination(vol_combo.currentData() or ""))
    remove_btn.clicked.connect(lambda: dest_list.takeItem(dest_list.currentRow()) if dest_list.currentRow() >= 0 else None)

    def _browse():
        d = QFileDialog.getExistingDirectory(win, "Choose destination folder", highlighted_dest() or "/")
        if d:
            add_destination(d)

    refresh_volumes()
    if dest:
        add_destination(dest)
    load_items()
    win.show()
    return app.exec()


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="orga+ copy tool — models-only copy to flash drive")
    parser.add_argument("--source", default=default_source(), help="source library folder")
    parser.add_argument(
        "--dest", action="append", default=[],
        help="destination folder / flash drive (repeat, or comma-separate, for multiple)",
    )
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="parallel copy streams")
    parser.add_argument("--headless", action="store_true", help="copy without GUI (no pause/stop)")
    parser.add_argument("--no-skip-existing", action="store_true", help="re-copy files already present")
    args = parser.parse_args(argv)

    dests = [d.strip() for part in args.dest for d in part.split(",") if d.strip()]

    if not args.headless:
        try:
            return run_gui(args.source, dests[0] if dests else "", args.workers)
        except ImportError:
            print("PySide6 not available — falling back to --headless", file=sys.stderr)

    if not dests:
        parser.error("--dest is required in headless mode")

    items, skipped = scan_items(Path(args.source))
    print(f"Found {len(items)} items with a model ({skipped} skipped, no model).")
    if not items:
        return 0

    ctrl = CopyController()

    def on_progress(snap, item, fname):
        copied, total, speed = snap
        pct = (copied / total * 100) if total else 0
        print(f"\r{pct:6.1f}%  {copied/1e6:8.1f}/{total/1e6:.1f} MB  "
              f"{speed/1e6:6.1f} MB/s  {item} [{fname}]", end="", flush=True)

    summary = run_copy_multi(
        items, dests, ctrl, workers=args.workers,
        skip_existing=not args.no_skip_existing,
        progress_cb=on_progress, log_cb=lambda m: print(f"\n{m}"),
    )
    print()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
