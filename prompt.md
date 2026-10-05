# Bilnov Gallery — App Icon & Logo Generation Prompts

This document provides production-ready, detailed prompts designed specifically for **Google Gemini (Imagen 3)** (as well as Midjourney v6 and FLUX) to generate a square logo and macOS/Windows desktop application icon for **Bilnov Gallery**, featuring a clean, stylized **"B"** monogram symbol.

---

## 🎨 Brand Identity & Visual Concept

- **Application Name**: Bilnov Gallery
- **Core Symbol**: Stylized, minimalist 3D letter **"B"** monogram
- **Product Type**: 3D Asset Management & Architectural Model Gallery Workstation
- **Aesthetic**: Premium dark-mode tech, Apple macOS squircle design language, precision 3D geometric volumetric art, glassmorphic refraction, subtle ambient glow.
- **Color Palette**:
  - **Deep Slate / Navy Background**: `#0A0E1A`, `#0F172A`
  - **Electric Indigo & Violet**: `#6366F1`, `#818CF8`, `#4F46E5`
  - **Cyber Cyan & Sky Blue**: `#38BDF8`, `#0284C7`
  - **Specular Luster**: Crisp white reflections with subtle emerald security reflections (`#10B981`)

---

## ✨ Google Gemini (Imagen 3) Prompts (Featuring the "B" Symbol)

*Copy and paste any of these directly into Google Gemini:*

### 🏆 Gemini Master Prompt: Modern Isometric 3D "B" Monogram (Recommended)

```text
Create a high-resolution, square 1:1 desktop application icon for "Bilnov Gallery", an advanced 3D model and architectural asset platform.

The focal centerpiece is a bold, modern, stylized 3D capital letter "B" symbol, sculpted as an isometric architectural geometric object. The letter "B" is crafted from semi-translucent frosted sapphire glass and dark brushed titanium with precision beveled edges. The two chambers of the "B" feature subtle, glowing neon cyan and electric indigo wireframe lattice lines illuminating from within.

The entire "B" emblem is centered and floats cleanly inside an Apple macOS-style rounded squircle container with a soft ambient drop shadow. The background is a deep obsidian navy gradient (#0A0E1A to #1E293B) with a subtle radial vignette.

Style: Clean 3D volumetric render, Octane Render aesthetics, Apple Human Interface Guidelines, minimalist, perfectly balanced composition, raytraced glass reflections, high contrast, studio softbox lighting.

Important: The symbol must clearly and simply form the letter "B". Do not include any other words, slogans, or small text.
```

---

### 🔷 Gemini Concept 2: The Continuous Geometric Ribbon "B"

```text
A sleek, modern square app icon featuring a stylized letter "B" monogram for a digital 3D design workstation.

The letter "B" is formed by a single continuous 3D ribbon with smooth curved folds and sharp beveled facets, rendered in dark gunmetal alloy and glowing electric indigo (#6366F1) on the inner surfaces. The emblem is floating diagonally in isometric perspective in the center of a dark matte slate squircle tile.

Visual details: Minimalist luxury tech branding, glossy specular highlights along the outer curves, subtle cyan rim light (#38BDF8), realistic ambient occlusion shadow beneath the "B", clean vector-like clarity translated into 3D realism.

Only the single letter "B" symbol, no other letters, no full words, no typography.
```

---

### 🏛️ Gemini Concept 3: The Architectural Blueprint "B" (Clean & Minimalist)

```text
A premium square desktop application icon for "Bilnov Gallery", representing 3D architectural models and furniture assets.

A minimalist, architectural 3D capital letter "B" composed of two interlocking glass and aluminum modules. The front faces are made of ultra-clear polished crystal revealing delicate cyan CAD blueprint gridlines inside, while the outer shell is anodized matte midnight-blue metal. Set against a clean, deep navy rounded square canvas with soft studio lighting.

Aesthetic: Apple macOS Big Sur / Sonoma icon style, high-end industrial design, clean geometric symmetry, razor-sharp edges, pristine raytraced reflections.

No extra text, no branding words, only the clean "B" symbol.
```

---

## 🚀 Alternative Midjourney / FLUX Prompt (With CLI Parameters)

```text
A premium macOS app icon for "Bilnov Gallery". Centered minimalist 3D stylized capital letter "B" monogram symbol floating inside a dark rounded squircle tile. The "B" is sculpted from semi-transparent frosted sapphire glass with precision-machined titanium bevels and glowing indigo (#6366F1) and cyan (#38BDF8) wireframe edges inside. Soft volumetric blue-violet glow against deep obsidian navy background (#0A0E1A to #1E293B). Apple Big Sur icon aesthetic, ultra-clean geometry, raytraced caustics, cinematic studio lighting, minimalist, 8k resolution, centered composition, square 1:1 aspect ratio --ar 1:1 --v 6.1 --style raw --q 2 --no extra words, watermark, slogan
```

---

## 📐 Technical Specifications & Asset Export Guidelines

When exporting the final generated image into desktop application assets:

| Platform | Format | Recommended Dimensions | Destination in Codebase |
| :--- | :--- | :--- | :--- |
| **macOS** | `.icns` | 1024×1024 (down to 16×16) | `desktop/assets/icon.icns` |
| **Windows** | `.ico` | 256×256 (down to 16×16) | `desktop/assets/icon.ico` |
| **Linux / Web** | `.png` | 512×512, 256×256, 128×128 | `desktop/assets/icon.png` |

### Conversion Commands (macOS CLI)

Once you pick your favorite 1024×1024 PNG image from Gemini (e.g., save it as `icon_1024.png` in the project root):

```bash
# 1. Create temporary iconset folder
mkdir BilnovGallery.iconset

# 2. Generate all required resolutions
sips -z 16 16     icon_1024.png --out BilnovGallery.iconset/icon_16x16.png
sips -z 32 32     icon_1024.png --out BilnovGallery.iconset/icon_16x16@2x.png
sips -z 32 32     icon_1024.png --out BilnovGallery.iconset/icon_32x32.png
sips -z 64 64     icon_1024.png --out BilnovGallery.iconset/icon_32x32@2x.png
sips -z 128 128   icon_1024.png --out BilnovGallery.iconset/icon_128x128.png
sips -z 256 256   icon_1024.png --out BilnovGallery.iconset/icon_128x128@2x.png
sips -z 256 256   icon_1024.png --out BilnovGallery.iconset/icon_256x256.png
sips -z 512 512   icon_1024.png --out BilnovGallery.iconset/icon_256x256@2x.png
sips -z 512 512   icon_1024.png --out BilnovGallery.iconset/icon_512x512.png
sips -z 1024 1024 icon_1024.png --out BilnovGallery.iconset/icon_512x512@2x.png

# 3. Compile into native macOS .icns file
iconutil -c icns BilnovGallery.iconset -o desktop/assets/icon.icns
rm -rf BilnovGallery.iconset
```
