# Bilnov Gallery Desktop Platform

A modern, high-performance native desktop application built with **PySide6 (Qt Quick / QML)** and Python for browsing, previewing, and managing 3D models and digital assets stored locally in `./data`.

---

## 🌟 Key Features

- **Exclusive `./data` Reading**:
  - The application reads strictly and exclusively from one directory: `./data`.
  - Automatically indexes categories, subcategories, 3D model archives (`.skp`, `.obj`, `.blend`, `.zip`), and image previews.
  - No scraper or external scraping configuration.

- **Data Folder Protection**:
  - Protected against write, delete, copy, or exfiltration operations.
  - Image cache stored safely in separate system user cache outside `./data`.
  - Zero network transmission of local assets.

- **Exact Article Location Button**:
  - Each asset card includes an **Open Location** button.
  - Opens the exact article folder directly in macOS Finder or system file manager.

- **Complete Licensing Lifecycle (`openapi.json`)**:
  - All license endpoints are public machine-to-machine APIs — **no admin session key required**.
  - 64-character deterministic hardware fingerprint (`device_id`).
  - Atomic local license storage in `~/.zed_license.json` with HMAC-SHA256 anti-tamper checksums.
  - Initial activation workflow (`POST /api/v1/license/activate`) with optional customer details (30-day activation duration).
  - Subsequent verification handshake (`POST /api/v1/license/verify`) with **7-Day Offline Grace Period**.
  - Background heartbeat check (`POST /api/v1/license/heartbeat`) every 4 hours.
  - Client registration & inquiry (`POST /api/v1/client/profile`, `GET /api/v1/client/status`) to request a license key and track `PENDING_LICENSE` / `ACTIVE` / `EXPIRED` status.

---

## 💻 Running the Application

### Prerequisites
- Python 3.10+
- PySide6

### Running
```bash
# Install dependencies
pip install -r requirements.txt

# Run desktop application
python main.py
# or
./desktop/run.sh
```

### Running Tests
```bash
python3 -m unittest tests/test_bilnov.py
```
