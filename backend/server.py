"""
FastAPI Server for OmniExtract — Universal Any Video Downloader
Supports downloading videos & audio from YouTube, TikTok, Facebook, Instagram,
Twitter/X, Reddit, Adult websites, Vimeo, and 1,000+ online video platforms.
Supports video resolutions: 1080p, 720p, 480p, 360p, 240p, 144p and MP3 audio up to 320 kbps.
"""

import os
import io
import re
import json
import zipfile
import shutil
import tempfile
import urllib.parse
import socket
from typing import Dict, Any, List, Optional
import requests
from fastapi import FastAPI, HTTPException, Query, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.fb_extractor import FacebookExtractor, HEADERS, extract_all_facebook_urls, normalize_fb_url, upgrade_to_full_resolution
from backend.video_extractor import UniversalVideoExtractor, format_duration, format_filesize, detect_platform

app = FastAPI(
    title="OmniExtract — Universal Any Video Downloader",
    description="Download videos in full quality (1080p to 144p) and audio (up to 320 kbps MP3) from YouTube, TikTok, Facebook, Instagram, Adult sites, and 1,000+ platforms.",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

video_extractor = UniversalVideoExtractor()
fb_extractor = FacebookExtractor()

class ExtractRequest(BaseModel):
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

def sanitize_for_json(obj: Any) -> Any:
    """Ensure all strings have no lone surrogates that break JSON UTF-8 encoding."""
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
    """Safely remove temporary directory and downloaded media."""
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass

@app.get("/api/network-info")
async def get_network_info():
    """Retrieve local LAN IP and active public tunnel URL."""
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
        "app": "OmniExtract Universal Video Downloader",
        "version": "2.0.0",
        "lan_ip": lan_ip,
        "port": 8000,
        "local_url": "http://localhost:8000",
        "lan_url": f"http://{lan_ip}:8000",
        "public_url": public_url,
        "is_public": public_url is not None
    }

@app.post("/api/extract")
async def extract_media(req: ExtractRequest):
    """
    Extract video & audio download options from any platform URL.
    Supports YouTube, TikTok, Facebook, Instagram, Twitter/X, Reddit,
    Adult platforms (Pornhub, XVideos, etc.), Vimeo, and 1,000+ sites.
    """
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="Video URL is required")

    url = req.url.strip()
    vid_err = None

    # 1. Primary Engine: Universal Video Extractor (yt-dlp + FFmpeg)
    try:
        vid_data = video_extractor.extract_info(url)
        if vid_data.get("success"):
            # Build unified schema for frontend
            vid_data["type"] = "video"
            vid_data["author"] = {
                "name": vid_data.get("uploader"),
                "url": vid_data.get("uploader_url")
            }

            # Thumbnail format for frontend gallery & preview
            if vid_data.get("thumbnail"):
                thumb_enc = urllib.parse.quote(vid_data["thumbnail"], safe="")
                vid_data["images"] = [{
                    "url": vid_data["thumbnail"],
                    "proxy_url": f"/api/proxy?url={thumb_enc}",
                    "type": "thumbnail",
                    "label": "High-Definition Video Poster"
                }]
            else:
                vid_data["images"] = []

            # Populate videos array with format downloads
            vid_data["videos"] = []
            for v in vid_data.get("video_downloads", []):
                vid_data["videos"].append({
                    "url": v["download_url"],
                    "quality": v["resolution"],
                    "height": v.get("height"),
                    "format": v["extension"],
                    "filesize": v.get("filesize", ""),
                    "badge": v.get("badge", ""),
                    "is_best": v.get("is_best", False)
                })

            # Format text description & metadata
            text_parts = [
                f"🎬 Title: {vid_data.get('title')}",
                f"🌐 Platform: {vid_data.get('platform', {}).get('name')}",
                f"👤 Uploader: {vid_data.get('uploader')}",
                f"⏱️ Duration: {vid_data.get('duration_string')}",
                f"🔗 URL: {url}"
            ]
            if vid_data.get("view_count"):
                text_parts.append(f"👁️ Views: {vid_data.get('view_count'):,}")
            if vid_data.get("like_count"):
                text_parts.append(f"👍 Likes: {vid_data.get('like_count'):,}")
            if vid_data.get("description"):
                text_parts.append(f"\n📝 Description:\n{vid_data.get('description')}")

            vid_data["text"] = "\n".join(text_parts)
            return sanitize_for_json(vid_data)
    except Exception as e:
        vid_err = str(e)

    # 2. Secondary Engine: Facebook Extractor fallback (for posts/albums without video)
    if "facebook.com" in url or "fb.watch" in url:
        clean_url = normalize_fb_url(url)
        try:
            data = fb_extractor.extract(clean_url, cookies=req.cookies)
            if data.get("success"):
                for idx, img in enumerate(data.get("images", [])):
                    img_url = img["url"] if isinstance(img, dict) else img
                    encoded_img = urllib.parse.quote(img_url, safe="")
                    if isinstance(img, dict):
                        img["proxy_url"] = f"/api/proxy?url={encoded_img}"
                        img["download_url"] = f"/api/download?url={encoded_img}&filename=image_{idx+1}.jpg"

                for idx, vid in enumerate(data.get("videos", [])):
                    vid_url = vid["url"] if isinstance(vid, dict) else vid
                    encoded_vid = urllib.parse.quote(vid_url, safe="")
                    if isinstance(vid, dict):
                        vid["download_url"] = f"/api/download?url={encoded_vid}&filename=video_{idx+1}.mp4"

                return sanitize_for_json(data)
        except Exception:
            pass

    return JSONResponse(status_code=400, content={
        "success": False,
        "error": f"Could not extract video from this link: {vid_err or 'Invalid or unsupported link'}"
    })

@app.post("/api/extract-batch")
async def extract_batch(req: BatchExtractRequest):
    """Batch extract multiple video links from text or URL list."""
    urls_to_process = []
    if req.urls:
        urls_to_process.extend(req.urls)
    if req.raw_text:
        # Extract URLs matching http/https
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
            item_data = video_extractor.extract_info(u)
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

@app.get("/api/download-video")
async def download_video_stream(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="Target video URL"),
    quality: str = Query("best", description="Resolution: 1080, 720, 480, 360, 240, 144, or best"),
    title: Optional[str] = Query("video", description="Video title")
):
    """
    Download and merge video + audio at selected resolution (1080p, 720p, 480p, etc.)
    Streams the finished MP4 file directly to the user's browser.
    """
    temp_dir = tempfile.mkdtemp(prefix="omniextract_vid_")
    safe_title = re.sub(r'[^\w\-\.]', '_', title or "video")[:60].strip('_') or "video"
    out_template = os.path.join(temp_dir, f"{safe_title}.%(ext)s")

    try:
        final_file = video_extractor.download_video_file(url, quality, out_template)
        if not os.path.exists(final_file):
            raise HTTPException(status_code=500, detail="Downloaded video file not found.")

        # Schedule automatic cleanup after streaming completes
        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        ext = os.path.splitext(final_file)[1] or ".mp4"
        suffix = f"_{quality}p" if quality != "best" else ""
        filename = f"{safe_title}{suffix}{ext}"

        return FileResponse(
            final_file,
            media_type="video/mp4",
            filename=filename,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")

@app.get("/api/download-audio")
async def download_audio_stream(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="Target video URL"),
    bitrate: str = Query("320", description="Audio bitrate: 320, 256, 192, 128"),
    title: Optional[str] = Query("audio", description="Audio title")
):
    """
    Extract and convert audio to high-quality MP3 (up to 320 kbps).
    Streams the finished MP3 file directly to the user's browser.
    """
    temp_dir = tempfile.mkdtemp(prefix="omniextract_aud_")
    safe_title = re.sub(r'[^\w\-\.]', '_', title or "audio")[:60].strip('_') or "audio"
    out_template = os.path.join(temp_dir, f"{safe_title}.%(ext)s")

    try:
        final_file = video_extractor.download_audio_file(url, bitrate, out_template)
        if not os.path.exists(final_file):
            raise HTTPException(status_code=500, detail="Extracted audio file not found.")

        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        filename = f"{safe_title}_{bitrate}kbps.mp3"

        return FileResponse(
            final_file,
            media_type="audio/mpeg",
            filename=filename,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to extract audio: {str(e)}")

@app.get("/api/proxy")
async def proxy_media(url: str = Query(...)):
    """Proxy image/video streams to bypass CDN cross-origin referrer blocks."""
    try:
        media_url = urllib.parse.unquote(url)
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
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

@app.get("/api/download")
async def download_direct(url: str = Query(...), filename: str = Query("media.bin")):
    """Force download any direct media URL as attachment."""
    try:
        media_url = urllib.parse.unquote(url)
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        resp = requests.get(media_url, headers=req_headers, stream=True, timeout=30)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch media from CDN")

        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)

        def iter_stream():
            for chunk in resp.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk

        return StreamingResponse(
            iter_stream(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download-zip")
async def download_all_zip(req: ZipDownloadRequest):
    """Package media info and files into a downloadable ZIP."""
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
        clean_title = re.sub(r'[^\w\-_\.]', '_', req.title or "video_bundle")[:40]
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

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
