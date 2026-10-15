"""
FastAPI Server for Omni Extractor — Universal Video & Audio Downloader
Endpoints:
  - /api/info: Fetch rich video metadata & dynamic resolutions
  - /api/download: Stream downloaded video (MP4) or audio (MP3 up to 320k, M4A, FLAC, WAV) with automatic temp cleanup
  - /api/extract-batch: Batch extraction for multiple video links
  - /api/network-info: Local LAN & public tunnel status
  - /api/proxy: CDN stream proxy for thumbnails and previews
  - /api/download-zip: Package media & metadata into ZIP archive
"""

import os
import io
import re
import json
import time
import asyncio
import zipfile
import shutil
import tempfile
import urllib.parse
import socket
from typing import Dict, Any, List, Optional
import requests
from fastapi import FastAPI, HTTPException, Query, Response, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.video_extractor import UniversalVideoExtractor, detect_platform, format_duration, format_filesize

# Optional fallback for non-video Facebook posts/albums
try:
    from backend.fb_extractor import FacebookExtractor, normalize_fb_url
    fb_extractor = FacebookExtractor()
except Exception:
    fb_extractor = None

app = FastAPI(
    title="Omni Extractor — Universal Video & Audio Downloader",
    description="Download videos in full quality (4K, 1080p, 720p, etc.) and studio audio (up to 320 kbps MP3, M4A, FLAC, WAV) from YouTube, TikTok, Facebook, Instagram, X/Twitter, and 1,500+ sites.",
    version="2.1.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

video_extractor = UniversalVideoExtractor()

class InfoRequest(BaseModel):
    url: str
    cookies: Optional[str] = None

class BatchExtractRequest(BaseModel):
    raw_text: Optional[str] = ""
    urls: Optional[List[str]] = []
    cookies: Optional[str] = None

class ZipDownloadRequest(BaseModel):
    title: Optional[str] = "video_download"
    text: Optional[str] = ""
    author: Optional[str] = ""
    url: str
    images: List[str] = []
    videos: List[str] = []

def clean_ascii_filename(name: Optional[str], fallback: str = "media") -> str:
    """Ensure filename only contains safe ASCII characters to prevent header and filesystem crashes."""
    if not name:
        return fallback
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)
    clean = re.sub(r'_+', '_', clean).strip(' ._')
    return clean[:60] or fallback

def sanitize_for_json(obj: Any) -> Any:
    """Ensure all strings have no lone surrogates that break JSON UTF-8 serialization."""
    if isinstance(obj, str):
        try:
            return obj.encode('utf-16', 'surrogatepass').decode('utf-16', 'replace').encode('utf-8', 'replace').decode('utf-8')
        except Exception:
            return obj
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(elem) for elem in obj]
    return obj

def cleanup_temp_dir(path: str):
    """Safely and thoroughly remove temporary directory after response finishes streaming."""
    try:
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

def sweep_old_temp_dirs():
    """Clean up any abandoned omniextract temp folders older than 1 hour."""
    try:
        tmp_base = tempfile.gettempdir()
        now = time.time()
        for name in os.listdir(tmp_base):
            if name.startswith("omniextract_"):
                folder = os.path.join(tmp_base, name)
                if os.path.isdir(folder):
                    try:
                        mtime = os.path.getmtime(folder)
                        if now - mtime > 3600:
                            shutil.rmtree(folder, ignore_errors=True)
                    except Exception:
                        pass
    except Exception:
        pass

# Run startup sweep
sweep_old_temp_dirs()

@app.get("/api/network-info")
async def get_network_info():
    """Retrieve local LAN IP, port, and any active public tunnel URL."""
    lan_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            lan_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass

    public_url = None
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=0.8)
        if resp.status_code == 200:
            data = resp.json()
            tunnels = data.get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    public_url = t.get("public_url")
                    break
            if not public_url and tunnels:
                public_url = tunnels[0].get("public_url")
    except Exception:
        pass

    return {
        "status": "online",
        "app": "Omni Extractor Universal Downloader",
        "version": "2.1.1",
        "ffmpeg": video_extractor.ffmpeg_path is not None,
        "lan_ip": lan_ip,
        "port": 8000,
        "local_url": "http://localhost:8000",
        "lan_url": f"http://{lan_ip}:8000",
        "public_url": public_url,
        "is_public": public_url is not None
    }

async def process_video_info(url: str, cookies: Optional[str] = None) -> Dict[str, Any]:
    """Helper to extract video information in worker thread and assemble full metadata."""
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="Target video URL is required")

    url = url.strip()
    vid_err = None

    # 1. Primary Engine: UniversalVideoExtractor (non-blocking thread)
    try:
        data = await asyncio.to_thread(video_extractor.extract_info, url)
        if data.get("success"):
            data["type"] = "video"
            data["author"] = {
                "name": data.get("uploader"),
                "url": data.get("uploader_url")
            }

            # Thumbnail proxy for CDN protection bypass
            if data.get("thumbnail"):
                thumb_enc = urllib.parse.quote(data["thumbnail"], safe="")
                data["images"] = [{
                    "url": data["thumbnail"],
                    "proxy_url": f"/api/proxy?url={thumb_enc}",
                    "type": "thumbnail",
                    "label": "HD Poster / Thumbnail"
                }]
            else:
                data["images"] = []

            # Structure videos list for frontend compatibility
            data["videos"] = []
            for v in data.get("video_downloads", []):
                data["videos"].append({
                    "url": v["download_url"],
                    "quality": v["resolution"],
                    "height": v.get("height"),
                    "format": v.get("extension", "mp4"),
                    "filesize": v.get("filesize", ""),
                    "badge": v.get("badge", ""),
                    "is_best": v.get("is_best", False)
                })

            # Formatted readable summary text
            text_parts = [
                f"🎬 Title: {data.get('title')}",
                f"🌐 Platform: {data.get('platform', {}).get('name')}",
                f"👤 Creator / Uploader: {data.get('uploader')}",
                f"⏱️ Duration: {data.get('duration_string')}",
                f"🔗 Link: {url}"
            ]
            if data.get("view_count"):
                text_parts.append(f"👁️ Views: {data.get('view_count'):,}")
            if data.get("like_count"):
                text_parts.append(f"👍 Likes: {data.get('like_count'):,}")
            if data.get("description"):
                text_parts.append(f"\n📝 Description:\n{data.get('description')}")

            data["text"] = "\n".join(text_parts)
            return sanitize_for_json(data)
    except Exception as e:
        vid_err = str(e)

    # 2. Secondary Engine: Facebook Extractor fallback (for photos / albums / posts)
    if fb_extractor and ("facebook.com" in url or "fb.watch" in url):
        clean_url = normalize_fb_url(url)
        try:
            data = await asyncio.to_thread(fb_extractor.extract, clean_url, cookies)
            if data.get("success"):
                for idx, img in enumerate(data.get("images", [])):
                    img_url = img["url"] if isinstance(img, dict) else img
                    encoded_img = urllib.parse.quote(img_url, safe="")
                    if isinstance(img, dict):
                        img["proxy_url"] = f"/api/proxy?url={encoded_img}"
                        img["download_url"] = f"/api/download?direct_url={encoded_img}&filename=image_{idx+1}.jpg"

                for idx, vid in enumerate(data.get("videos", [])):
                    vid_url = vid["url"] if isinstance(vid, dict) else vid
                    encoded_vid = urllib.parse.quote(vid_url, safe="")
                    if isinstance(vid, dict):
                        vid["download_url"] = f"/api/download?direct_url={encoded_vid}&filename=video_{idx+1}.mp4"

                return sanitize_for_json(data)
        except Exception:
            pass

    raise HTTPException(
        status_code=400,
        detail=f"Could not extract video from this link: {vid_err or 'Invalid or unsupported link'}"
    )

@app.get("/api/info")
async def get_info(url: str = Query(..., description="Target video URL")):
    """Fetch video metadata and available video & audio formats via GET."""
    return await process_video_info(url)

@app.post("/api/info")
async def post_info(req: InfoRequest):
    """Fetch video metadata and available video & audio formats via POST."""
    return await process_video_info(req.url, cookies=req.cookies)

# Backward-compatible alias for /api/extract
@app.post("/api/extract")
async def extract_media_legacy(req: InfoRequest):
    """Legacy alias pointing to /api/info."""
    return await process_video_info(req.url, cookies=req.cookies)

@app.get("/api/download")
async def download_media(
    background_tasks: BackgroundTasks,
    url: Optional[str] = Query(None, description="Video URL to download and convert"),
    type: str = Query("video", description="Download type: 'video' or 'audio'"),
    quality: str = Query("best", description="Video quality: 'best', '2160', '1440', '1080', '720', '480', '360', etc."),
    format: Optional[str] = Query(None, description="Audio or video format: mp4, mp3, m4a, flac, wav"),
    bitrate: str = Query("320", description="Audio bitrate: 320, 256, 192, 128"),
    title: Optional[str] = Query("download", description="Preferred output filename"),
    direct_url: Optional[str] = Query(None, description="Direct URL to stream as file download"),
    filename: Optional[str] = Query(None, description="Direct URL target filename")
):
    """
    Download video or audio file with automatic temporary directory cleanup.
    Supports MP4 video (up to 4K / 1080p) and audio (up to 320 kbps MP3, M4A, FLAC, WAV).
    """
    # 1. Direct CDN / static stream proxy download
    if direct_url:
        try:
            target_url = urllib.parse.unquote(direct_url)
            req_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            }
            resp = requests.get(target_url, headers=req_headers, stream=True, timeout=30)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch media from CDN")

            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            out_name = clean_ascii_filename(filename or "media.bin", fallback="media.bin")

            def stream_chunks():
                for chunk in resp.iter_content(chunk_size=16384):
                    if chunk:
                        yield chunk

            return StreamingResponse(
                stream_chunks(),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{out_name}"',
                    "Access-Control-Allow-Origin": "*"
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if not url:
        raise HTTPException(status_code=400, detail="Missing required 'url' parameter for media download.")

    # 2. Dynamic conversion & download with yt-dlp + FFmpeg
    temp_dir = tempfile.mkdtemp(prefix="omniextract_dl_")
    safe_disk_name = clean_ascii_filename(title or "media", fallback="media")
    out_template = os.path.join(temp_dir, f"{safe_disk_name}.%(ext)s")

    try:
        is_audio = type.lower() == "audio" or (format and format.lower() in ["mp3", "m4a", "flac", "wav"])

        if is_audio:
            chosen_format = (format or "mp3").lower().strip()
            if chosen_format not in ["mp3", "m4a", "flac", "wav"]:
                chosen_format = "mp3"

            final_file = await asyncio.to_thread(
                video_extractor.download_audio_file,
                url,
                chosen_format,
                bitrate,
                out_template
            )

            if not os.path.exists(final_file):
                raise HTTPException(status_code=500, detail="Audio conversion produced no output file.")

            mime_types = {
                "mp3": "audio/mpeg",
                "m4a": "audio/mp4",
                "flac": "audio/flac",
                "wav": "audio/wav"
            }
            media_type = mime_types.get(chosen_format, "audio/mpeg")
            suffix = f"_{bitrate}kbps" if chosen_format == "mp3" else ""
            out_filename = f"{safe_disk_name}{suffix}.{chosen_format}"

        else:
            final_file = await asyncio.to_thread(
                video_extractor.download_video_file,
                url,
                quality,
                out_template
            )

            if not os.path.exists(final_file):
                raise HTTPException(status_code=500, detail="Video download produced no output file.")

            ext = os.path.splitext(final_file)[1].lstrip('.') or "mp4"
            media_type = "video/mp4" if ext == "mp4" else f"video/{ext}"
            res_tag = f"_{quality}p" if quality not in ["best", ""] else ""
            out_filename = f"{safe_disk_name}{res_tag}.{ext}"

        # Register background task to clean up temporary directory after streaming is done
        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        # FileResponse with clean ASCII out_filename sets the Content-Disposition RFC 5987 header safely
        return FileResponse(
            path=final_file,
            media_type=media_type,
            filename=out_filename
        )

    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

# Backward-compatible download aliases
@app.get("/api/download-video")
async def download_video_alias(
    background_tasks: BackgroundTasks,
    url: str = Query(...),
    quality: str = Query("best"),
    title: Optional[str] = Query("video")
):
    """Legacy alias for /api/download?type=video."""
    return await download_media(
        background_tasks=background_tasks,
        url=url,
        type="video",
        quality=quality,
        title=title
    )

@app.get("/api/download-audio")
async def download_audio_alias(
    background_tasks: BackgroundTasks,
    url: str = Query(...),
    bitrate: str = Query("320"),
    title: Optional[str] = Query("audio")
):
    """Legacy alias for /api/download?type=audio&format=mp3."""
    return await download_media(
        background_tasks=background_tasks,
        url=url,
        type="audio",
        format="mp3",
        bitrate=bitrate,
        title=title
    )

@app.post("/api/extract-batch")
async def extract_batch(req: BatchExtractRequest):
    """Batch extract multiple video links from raw text or URL list."""
    urls_to_process = []
    if req.urls:
        urls_to_process.extend(req.urls)
    if req.raw_text:
        found_urls = re.findall(r'https?://[^\s<>"\'\)]+', req.raw_text)
        for u in found_urls:
            u_clean = u.rstrip(".,;:)")
            if u_clean not in urls_to_process:
                urls_to_process.append(u_clean)

    if not urls_to_process:
        raise HTTPException(status_code=400, detail="No valid URLs found in input.")

    results = []
    for idx, u in enumerate(urls_to_process, 1):
        try:
            item_data = await asyncio.to_thread(video_extractor.extract_info, u)
            item_data["index"] = idx
            results.append(item_data)
        except Exception as e:
            results.append({
                "index": idx,
                "url": u,
                "success": False,
                "error": str(e),
                "title": f"Video #{idx}",
                "video_downloads": [],
                "audio_downloads": []
            })

    return sanitize_for_json({
        "success": True,
        "total_requested": len(urls_to_process),
        "total_extracted": len(results),
        "results": results
    })

@app.get("/api/proxy")
async def proxy_media(url: str = Query(...)):
    """Proxy image/video streams to bypass CDN cross-origin referrer blocks."""
    try:
        media_url = urllib.parse.unquote(url)
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        resp = requests.get(media_url, headers=req_headers, stream=True, timeout=20)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Unable to retrieve media stream")

        content_type = resp.headers.get("Content-Type", "image/jpeg")

        def iter_stream():
            for chunk in resp.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk

        return StreamingResponse(
            iter_stream(),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download-zip")
async def download_all_zip(req: ZipDownloadRequest):
    """Package media info and metadata into a downloadable ZIP."""
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            info_dict = {
                "title": req.title,
                "url": req.url,
                "author": req.author,
                "description": req.text,
                "images": req.images,
                "videos": req.videos
            }
            zip_file.writestr("video_info.json", json.dumps(info_dict, indent=2).encode("utf-8"))
            if req.text:
                zip_file.writestr("description.txt", req.text.encode("utf-8"))

        zip_buffer.seek(0)
        clean_title = clean_ascii_filename(req.title or "video_bundle", fallback="video_bundle")
        zip_filename = f"{clean_title}_package.zip"

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"',
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate zip: {str(e)}")

# Mount static frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
