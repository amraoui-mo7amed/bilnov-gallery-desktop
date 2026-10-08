# `olga+` Storage File Structure Documentation

This document describes the storage hierarchy and folder structure used by the **`olga+`** desktop application to discover, index, preview, and export 3D assets.

---

## 1. Storage Hierarchy Overview

The storage system strictly enforces a **3-level directory hierarchy**:

```
storage/
 └── <Category>/
      └── <Subcategory>/
           └── <Asset Name>/
                ├── <Preview Images>
                ├── model/
                │    └── <3D Model / Archive Files>
                └── meta.json (optional)
```

> [!IMPORTANT]
> **Depth 3 Strict Enforcement**: The scanner strictly expects assets at **depth 3** (`<Category>/<Subcategory>/<Asset Name>`).  
> Any legacy folder at **depth 2** (`<Category>/<Asset Name>`) is **ignored** and will not be indexed into the library.

---

## 2. Directory Level Details

| Level | Path Segment | Description | Example |
|---|---|---|---|
| **Root** | `storage/` or `data/` | Configured via `DATA_DIR` in `config.py` (defaults to `./storage`, fallback to `./data`). | `storage/` |
| **Level 1** | `<Category>` | Top-level domain/department grouping. | `Furniture`, `Lighting`, `Vehicles`, `Architecture` |
| **Level 2** | `<Subcategory>` | Specific typology or classification grouping under the category. | `Chairs`, `Sofas`, `Tables`, `Ceiling Lamps`, `Cars` |
| **Level 3** | `<Asset Name>` | Individual asset directory containing its preview images, models, and metadata. | `Nordic Minimalist Armchair`, `Barcelona Leather Daybed` |

---

## 3. Asset Interior Contents (Inside `<Asset Name>/`)

Each individual asset directory at Level 3 contains:

### A. Preview Images (`<images>`)
- **Location**: Directly inside `<Asset Name>/` OR inside `<Asset Name>/images/`.
- **Supported Formats**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`.
- **Thumbnail**: The first image alphabetically (e.g. `image_1.jpg` or `01_preview.png`) is automatically chosen as the library thumbnail card cover, unless custom defined in `meta.json`.

### B. 3D Model & Archive Files (`model/<archive file>`)
- **Location**: Inside the subfolder `<Asset Name>/model/`.
- **Supported Formats**:
  - **Native 3D Files**: `.skp` (SketchUp), `.fbx`, `.obj`, `.blend`, `.3ds`, `.max`, `.dae`, `.c4d`, `.dxf`, `.stl`.
  - **Archive Bundles**: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`.
- **Behavior**: The application displays the model file count, detects native SketchUp/archive formats, and offers one-click extraction/bundle export.

### C. Metadata (`meta.json` — Optional)
- **Location**: Directly inside `<Asset Name>/meta.json`.
- **Contents**: Stores metadata properties, e.g.:
```json
{
  "title": "Nordic Minimalist Armchair",
  "category": "Furniture",
  "subcategory": "Chairs",
  "thumbnail": "image_1.jpg",
  "created_at": "2026-10-08T17:00:00",
  "source": "user"
}
```

---

## 4. Concrete Example

Here is a full practical directory tree demonstrating valid assets across multiple categories and subcategories:

```
storage/
├── Architecture/
│   ├── Doors & Windows/
│   │   └── Modern Pivot Glass Door/
│   │       ├── image_1.jpg
│   │       ├── image_2.png
│   │       ├── model/
│   │       │   └── pivot_door_v2.skp
│   │       └── meta.json
│   └── Stairs/
│       └── Cantilever Floating Wood Stair/
│           ├── image_1.webp
│           └── model/
│               └── floating_stairs_bundle.zip
│
├── Furniture/
│   ├── Chairs/
│   │   ├── Eames Lounge & Ottoman/
│   │   │   ├── image_1.jpg
│   │   │   ├── image_2.jpg
│   │   │   ├── image_3.jpg
│   │   │   ├── model/
│   │   │   │   └── eames_lounge_chair.skp
│   │   │   └── meta.json
│   │   └── Nordic Minimalist Armchair/
│   │       ├── image_1.jpg
│   │       └── model/
│   │           └── nordic_armchair.skp
│   └── Sofas/
│       └── Velvet Modular Sectional/
│           ├── preview_main.png
│           ├── preview_side.png
│           └── model/
│               └── modular_sofa_collection.zip
│
└── Lighting/
    ├── Ceiling Lamps/
    │   └── Brass Halo Chandelier/
    │       ├── thumb.jpg
    │       └── model/
    │           └── halo_chandelier.skp
    └── Floor Lamps/
        └── Minimalist Arc Floor Lamp/
            ├── render_01.jpg
            └── model/
                └── arc_lamp.fbx
```

---

## 5. Scanner Rules & Distinction

| Rule | Valid (Indexed) | Invalid (Ignored) |
|---|---|---|
| **Level Depth** | `storage/Furniture/Chairs/Nordic Armchair` (Depth 3) | `storage/Furniture/Nordic Armchair` (Depth 2 — **Ignored**) |
| **Model Location** | `<Asset Name>/model/chair.skp` or `<Asset Name>/model/chair.zip` | Directly in root or category folder |
| **Reserved Names** | Folders named `model` or `images` are subcomponents, never assets. | Treated as asset candidates |
| **Hidden Items** | Any folder/file starting with `.` (e.g. `.git`, `.DS_Store`) is automatically excluded. | — |

---

## 6. Implementation Reference

- **Backend Scanner**: [`desktop/backend/library.py`](file:///Users/amraouimohamed/bilnov-gallery/desktop/backend/library.py)
  - `LibraryManager.scan_library()` walks `<category>/<subcategory>/<asset_name>`.
  - `LibraryManager.is_article_dir()` inspects assets for preview images and `model/` directory contents.
  - `LibraryManager.add_item()` writes newly created assets strictly at `<category>/<subcategory>/<asset_name>`.
- **UI & Bridge**:
  - [`desktop/backend/app_bridge.py`](file:///Users/amraouimohamed/bilnov-gallery/desktop/backend/app_bridge.py) (`addLibraryItem()`)
  - [`desktop/qml/components/AddItemDialog.qml`](file:///Users/amraouimohamed/bilnov-gallery/desktop/qml/components/AddItemDialog.qml) (provides Category & Subcategory inputs)
