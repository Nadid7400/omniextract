# ⚡ Omni Extractor — Universal Video & Audio Downloader

A high-performance universal media extraction engine powered by **FastAPI**, **yt-dlp**, and **FFmpeg** (with automatic `imageio-ffmpeg` fallback).

Extract high-resolution video streams (**4K, 1440p, 1080p, 720p, 480p, 360p**) and master studio audio (**up to 320 kbps CBR MP3, M4A, FLAC, WAV**) from **YouTube, Shorts, TikTok, Instagram Reels, Facebook, X (Twitter), Reddit, Vimeo, Dailymotion, Twitch**, and 1,500+ platforms.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Nadid7400/omniextract)

---

## ✨ Features

- 🎬 **Dynamic Video Resolutions**: Automatically parses all available video resolutions (4K / 2160p, 2K / 1440p, 1080p Full HD, 720p, 480p, 360p, 240p, 144p) with file size estimates and bitrates.
- 🎵 **Studio Audio Transcoding (Up to 320 kbps CBR)**:
  - **MP3**: 320 kbps (Master Studio Quality), 256 kbps (Hi-Fi), 192 kbps (CD Quality), 128 kbps (Compact).
  - **M4A / AAC**: Original source audio track.
  - **FLAC**: Lossless Hi-Res studio audio.
  - **WAV**: Uncompressed 16-bit PCM broadcast audio.
- 🚀 **Auto-Detecting FFmpeg Engine**: Automatically detects system FFmpeg or falls back directly to bundled `imageio-ffmpeg` binaries — zero manual path configuration required.
- 🌐 **1,500+ Platforms Supported**: YouTube, YouTube Shorts, TikTok (no watermark), Instagram Reels, Facebook Videos/Reels, X/Twitter, Reddit, Vimeo, and more.
- 🧹 **Automatic Temp Folder Cleanup**: Background task automatically cleans up temporary download directories after streaming finishes, ensuring zero disk leaks.
- 📱 **Interactive Liquid Glass UI**:
  - Live video/audio mode switcher.
  - Dynamically populated resolution dropdown.
  - Single-click clean download triggers with instant visual feedback.
  - In-browser HTML5 video preview player.
  - Local history storage and network share modal for LAN / mobile access.
- 📦 **Container & Cloud Ready**: Production-ready `Dockerfile` and `render.yaml` for 1-click deployments on Docker, Render, Heroku, or VPS.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python run.py
```
This automatically starts the server at `http://localhost:8000` and opens your default browser.

Optional flags:
```bash
# Specify custom port
python run.py --port 8080

# Share globally via public tunnel
python run.py --public
```

---

## 🛠️ API Reference

### 1. `GET /api/info` or `POST /api/info`
Fetch metadata and all available video resolutions and audio formats.
- **Query Params / JSON Body**:
  - `url`: Video URL (e.g. `https://www.youtube.com/watch?v=...`)
- **Returns**: Video title, uploader, thumbnail, duration, platform info, dynamic `video_downloads` list, and `audio_downloads` list.

### 2. `GET /api/download`
Download media file with automatic temporary cleanup upon stream completion.
- **Parameters**:
  - `url`: Target video URL
  - `type`: `video` or `audio` (default: `video`)
  - `quality`: `best`, `2160`, `1440`, `1080`, `720`, `480`, `360`, etc. (for video)
  - `format`: `mp4` (video) or `mp3`, `m4a`, `flac`, `wav` (audio)
  - `bitrate`: `320`, `256`, `192`, `128` (for audio)
  - `title`: Preferred file title

### 3. `POST /api/extract-batch`
Extract multiple links at once from text or URL list.

### 4. `GET /api/network-info`
Returns local LAN IP and public tunnel status for cross-device access.

---

## 🐳 Docker Deployment

Build and run with Docker:
```bash
docker build -t omniextract .
docker run -p 8000:8000 omniextract
```

---

## 🍪 YouTube Bot Verification, Cookies & Proxy Setup

Datacenter IP addresses (like cloud hosts on Render, AWS, GCP, etc.) are frequently challenged by YouTube with bot verification blocks:
`"Sign in to confirm you're not a bot"`.

Omni Extractor automatically retries requests using alternate player clients (`tv`, `web_safari`, `android`, `ios`). To ensure 100% reliable downloads on cloud servers or for age-restricted / private videos, configure YouTube cookies or an outbound proxy:

### 1. Exporting Cookies from Your Browser
1. Install a Netscape-format cookie exporter browser extension:
   - Chrome / Brave / Edge: **Get cookies.txt LOCALLY**
   - Firefox: **Cookie-Editor** (Export as Netscape format)
2. Go to [YouTube.com](https://www.youtube.com) and ensure you are logged in.
3. Open the extension and click **Export** (or copy all lines).
4. Save as `cookies.txt` (this file is already excluded in `.gitignore` to protect your privacy).

### 2. Configuring Environment Variables
Omni Extractor recognizes the following environment variables:

| Environment Variable | Description | Example |
| :--- | :--- | :--- |
| `COOKIES_FILE` (or `YTDL_COOKIES`) | Absolute or relative path to your Netscape `cookies.txt` file. | `/etc/secrets/cookies.txt` or `./cookies.txt` |
| `YT_COOKIES` | The entire raw text content of your `cookies.txt` file (ideal for Render environment variables). | `# Netscape HTTP Cookie File...` |
| `PROXY_URL` | Outbound proxy for all video extractions and downloads. Supports HTTP, HTTPS, and SOCKS5. | `http://user:pass@proxy.example.com:8080` |

> [!NOTE]
> Cookie files are copied to a secure, temporary location before reading. Cookie contents are **never** logged to server logs or client responses.

### 3. Quick UI Cookies Paste
You can also paste your Netscape cookies directly into the web app:
- Click the **🍪 Cookies** button in the top navigation bar.
- Paste your Netscape formatted cookie text and click **Save Cookies**.
- Cookies are safely kept in your browser's local storage and passed directly with extraction and download requests.

---

## 📄 License
MIT License.
