# ⚡ OmniExtract — Facebook Content Extractor (No Login Required)

A powerful, privacy-first tool to extract **post texts**, **high-resolution images**, and **MP4 video streams** from public Facebook links with **zero login**, **zero cookies**, and **no credentials**.

Supports single posts as well as **Batch Extraction** for full story/novel series (e.g. 90+ chapter posts).

---

## ✨ Features

- 📝 **Full Post Text & Long Novels**: Extracts complete un-truncated post body text, statuses, descriptions, and hashtags across all languages (including Bengali, Arabic, Hindi, CJK, etc.).
- 📚 **Batch Series Extraction**: Paste an entire list of 90+ Facebook links or numbered chapters at once.
- 📖 **Compile Novel to .TXT**: One-click download of all extracted parts compiled into a single clean story file (`Compiled_Novel.txt`).
- 🖼️ **High-Definition Images**: Finds all `scontent` CDN photo URLs, multi-image albums, and cover photos.
- 🎬 **Video & Reel Streams**: Extracts playable MP4 streams (HD 1080p, 720p, SD 360p) with duration and format info.
- 📦 **One-Click .ZIP Bundle**: Packages post text (`.txt`), metadata (`metadata.json`), and all images packed neatly into a single ZIP file.
- 🛡️ **CDN Proxy & Referer Shield**: Direct in-browser viewing and downloading without Facebook's cross-origin 403 blocks.
- 💻 **Dual Interfaces**:
  - **Sleek Web App**: Dark-mode glassmorphism interface with Single & Batch mode tabs, zoom lightbox, and in-app video player.
  - **Terminal CLI**: Command-line tool for automated batch archiving and scripting.

---

## 🚀 Quick Start

### 1. Launch the Web Application

Simply run:
```powershell
python run.py
```
This automatically starts the local server at `http://127.0.0.1:8000` and opens the web application in your default browser.

- **Single Mode**: Paste any post, reel, or photo URL.
- **Batch Mode**: Paste multiple links, numbered lists (e.g. `1.https://... 2.https://...`), or multi-line URLs. Click **Extract All Links** and download the compiled novel with one click!

### 2. Run via Command Line (CLI)

#### Single Link:
```powershell
# Print extraction summary in terminal
python cli.py "https://www.facebook.com/share/p/1DyLPPg1BQ/"

# Download all assets to a folder
python cli.py "https://www.facebook.com/share/p/1DyLPPg1BQ/" --download --output-dir ./extracted_media
```

#### Batch Extraction (Full Novel / 90+ Chapters):
```powershell
# Extract a batch of links and compile into a single novel document
python cli.py --batch-text "1.https://... 2.https://..." --compile-txt my_novel.txt

# Or from a text file containing Facebook links:
python cli.py --batch-file my_links.txt --compile-txt full_series.txt --download
```

---

## 🛠️ API Endpoints

- **`POST /api/extract`**: Extract single URL (`{"url": "..."}`)
- **`POST /api/extract-batch`**: Batch extract multiple URLs (`{"raw_text": "...", "urls": [...]}`)
- **`POST /api/download-compiled-txt`**: Compiles chapters into a single `.txt` file.
- **`GET /api/proxy?url=<CDN_URL>`**: Streams media directly with anti-referer bypass.
- **`GET /api/download?url=<CDN_URL>&filename=photo.jpg`**: Triggers immediate browser file download.
- **`POST /api/download-zip`**: Assembles a zip archive with texts and images on the fly.
