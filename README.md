# WhatsApp Sticker Hub 🚀

An automated pipeline to download, segment, clean, resize, and verify custom stickers for WhatsApp. This hub allows you to take raw images or sticker sheets (grids), remove their backgrounds using AI or computer vision, process them to prevent transparency leaks, and output them in the exact format required by WhatsApp (512x512 transparent WebP).

---

## 📋 Features

- **Pinterest Downloader (`download_pinterest.py`)**: Resolves Pinterest short-links, parses the HTML for high-resolution images (`/originals/` where possible), and downloads them to the raw inputs folder.
- **AI Background Remover (`sticker_generator.py`)**: Uses the `rembg` AI model (U2NET) and Pillow to automatically cut out backgrounds for individual subject images.
- **Grid Segmentation & Processing (`process_grid.py`)**: 
  - Splits sticker sheets/grids into individual characters using OpenCV contour detection.
  - Automatically merges nested/overlapping contours (e.g. detached hats, accessories, or limbs).
  - Uses localized flood-filling to separate backgrounds from character outlines.
  - **Leakage Prevention**: Seals outlines and simulates borders near the bottom of characters to prevent transparency from leaking into the bodies of hand-drawn/open-contoured characters.
  - Packs and resizes elements into WhatsApp-compliant 512x512 transparent canvases with configurable margins.
- **Transparency Leak Finder (`find_leaks.py`)**: Scans final stickers and computes the ratio of white opaque pixels to non-transparent pixels, warning you of any potential background fill leaks.

---

## 🛠️ Installation

Ensure you have Python 3.8+ installed. Install the dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Dependencies
- `rembg` & `onnxruntime`: For AI-based background removal.
- `opencv-python`: For image processing, grid splitting, and contour manipulation.
- `pillow` (PIL): For canvas creation, padding, and WebP format encoding.
- `requests`: For downloading resources from Pinterest.

---

## 📂 Project Structure

```
whatsapp-sticker-hub/
│
├── pinterest_raw/             # Downloaded raw images / sticker sheets (created automatically)
├── whatsapp_stickers_ready/   # Final processed, 512x512 WebP stickers (created automatically)
│
├── download_pinterest.py      # Script to download pin images
├── sticker_generator.py       # AI-based background removal for single subject images
├── process_grid.py            # CV-based grid/sheet segmenter with contour leakage prevention
├── find_leaks.py              # Validation script to detect transparency leakages
└── requirements.txt           # Python packages required for the project
```

---

## 🚀 Usage Guide

The pipeline follows a download-process-validate workflow:

### 1. Download Raw Images
Configure the URL variable in `download_pinterest.py` and run:
```bash
python download_pinterest.py
```
This saves the high-resolution source image into the `pinterest_raw/` folder.

### 2. Process the Images

You can process raw images using two different methods depending on the source material:

#### Method A: For Individual Images (AI Cutout)
If your raw files are separate images of single subjects, run the AI background remover:
```bash
python sticker_generator.py
```
This uses deep learning to isolate the subject and saves the processed sticker into `whatsapp_stickers_ready/`.

#### Method B: For Sticker Sheets / Grids (CV-based Grid Splitter)
If your raw file is a sheet/grid containing multiple characters/stickers on a white background, run:
```bash
python process_grid.py
```
This script will:
1. Read each grid sheet.
2. Segment the individual characters automatically.
3. Apply outline protection & corner-based flood filling to keep the body opaque and background transparent.
4. Scale, pad, and save each extracted sticker into `whatsapp_stickers_ready/` as `{sheet_name}_sticker_{num}.webp`.

### 3. Verify Sticker Quality
To ensure there are no outline "leaks" (where the background extraction accidentally entered the body of a character, leaving it transparent), run:
```bash
python find_leaks.py
```
This checks the ratio of opaque pixels and warns you with `>>> LEAK DETECTED` if a sticker has too much transparency inside its bounding box.

---

## 📐 WhatsApp Sticker Specifications Met

All stickers exported to the `whatsapp_stickers_ready/` folder automatically comply with WhatsApp's exact technical requirements:
- **Format**: WebP (`.webp`)
- **Dimensions**: Exactly `512 x 512` pixels
- **Transparency**: Fully supported transparent background
- **Margins**: Features a `15px` margin (padding) surrounding the character bounds to ensure it renders correctly without getting cropped by the chat window.
