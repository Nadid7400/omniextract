"""
FastAPI Server for Facebook Anything Extractor
Provides single extraction, batch extraction, media proxy, direct downloader, and ZIP bundler.
"""

import os
import io
import re
import json
import zipfile
import urllib.parse
import socket
from typing import Dict, Any, List, Optional
import requests
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.fb_extractor import FacebookExtractor, HEADERS, extract_all_facebook_urls, normalize_fb_url, parse_fb_cookies

app = FastAPI(
    title="OmniExtract Facebook",
    description="Extract post texts, high-res images, and videos from public and locked Facebook links.",
    version="1.2.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = FacebookExtractor()

class CookieRequest(BaseModel):
    cookies: Optional[str] = ""
    c_user: Optional[str] = ""
    xs: Optional[str] = ""

class ExtractRequest(BaseModel):
    url: str
    cookies: Optional[str] = None

class BatchExtractRequest(BaseModel):
    raw_text: Optional[str] = ""
    urls: Optional[List[str]] = []
    cookies: Optional[str] = None

class ZipDownloadRequest(BaseModel):
    title: Optional[str] = "facebook_post"
    text: Optional[str] = ""
    author: Optional[str] = ""
    url: str
    images: List[str] = []
    videos: List[str] = []

class BatchDownloadTxtRequest(BaseModel):
    title: Optional[str] = "facebook_novel_collection"
    chapters: List[Dict[str, Any]] = []

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
        "lan_ip": lan_ip,
        "port": 8000,
        "local_url": "http://localhost:8000",
        "lan_url": f"http://{lan_ip}:8000",
        "public_url": public_url,
        "is_public": public_url is not None
    }

@app.get("/api/cookies")
async def get_cookie_status():
    """Check current status of authenticated session cookies."""
    return extractor.get_cookie_status()

@app.post("/api/cookies")
async def set_cookies(req: CookieRequest):
    """Set Facebook authentication cookies to extract locked/private posts."""
    cookie_payload = ""
    if req.c_user and req.xs:
        cookie_payload = f"c_user={req.c_user.strip()}; xs={req.xs.strip()}"
    elif req.cookies:
        cookie_payload = req.cookies.strip()
    
    if not cookie_payload:
        raise HTTPException(status_code=400, detail="No cookies provided")
    
    extractor.set_cookies(cookie_payload)
    status = extractor.get_cookie_status()
    return {
        "success": True,
        "message": "Cookies saved successfully" if status["has_cookies"] else "Could not parse cookies",
        "status": status
    }

@app.delete("/api/cookies")
async def clear_cookies():
    """Clear stored authentication cookies."""
    extractor.clear_cookies()
    return {"success": True, "message": "Cookies cleared successfully"}

@app.post("/api/extract")
async def extract_facebook(req: ExtractRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="Facebook URL is required")
    
    clean_url = normalize_fb_url(req.url.strip())
    try:
        data = extractor.extract(clean_url, cookies=req.cookies)
        if not data.get("success"):
            return JSONResponse(status_code=400, content=sanitize_for_json(data))
        
        # Inject proxy and download endpoints for frontend convenience
        for idx, img in enumerate(data.get("images", [])):
            img_url = img["url"] if isinstance(img, dict) else img
            encoded_img = urllib.parse.quote(img_url, safe="")
            if isinstance(img, dict):
                img["proxy_url"] = f"/api/proxy?url={encoded_img}"
                img["download_url"] = f"/api/download?url={encoded_img}&filename=fb_image_{idx+1}.jpg"

        for idx, vid in enumerate(data.get("videos", [])):
            vid_url = vid["url"] if isinstance(vid, dict) else vid
            encoded_vid = urllib.parse.quote(vid_url, safe="")
            if isinstance(vid, dict):
                vid["download_url"] = f"/api/download?url={encoded_vid}&filename=fb_video_{idx+1}.mp4"

        clean_data = sanitize_for_json(data)
        return clean_data
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "success": False,
            "error": f"Internal extraction error: {str(e)}"
        })

@app.post("/api/extract-batch")
async def extract_batch(req: BatchExtractRequest):
    """
    Extract multiple Facebook URLs in sequence.
    Can accept either a list of URLs or raw text with multiple URLs (e.g. numbered list).
    """
    urls_to_process = []
    if req.urls:
        urls_to_process.extend(req.urls)
    if req.raw_text:
        parsed = extract_all_facebook_urls(req.raw_text)
        for p in parsed:
            if p not in urls_to_process:
                urls_to_process.append(p)

    if not urls_to_process:
        raise HTTPException(status_code=400, detail="No valid Facebook URLs found in input.")

    results = []
    for idx, u in enumerate(urls_to_process, 1):
        try:
            item_data = extractor.extract(u, cookies=req.cookies)
            item_data["index"] = idx
            # Inject proxy and download URLs
            for i_idx, img in enumerate(item_data.get("images", [])):
                img_url = img["url"] if isinstance(img, dict) else img
                encoded_img = urllib.parse.quote(img_url, safe="")
                if isinstance(img, dict):
                    img["proxy_url"] = f"/api/proxy?url={encoded_img}"
                    img["download_url"] = f"/api/download?url={encoded_img}&filename=chapter_{idx:02d}_img_{i_idx+1}.jpg"
            for v_idx, vid in enumerate(item_data.get("videos", [])):
                vid_url = vid["url"] if isinstance(vid, dict) else vid
                encoded_vid = urllib.parse.quote(vid_url, safe="")
                if isinstance(vid, dict):
                    vid["download_url"] = f"/api/download?url={encoded_vid}&filename=chapter_{idx:02d}_vid_{v_idx+1}.mp4"
            results.append(item_data)
        except Exception as e:
            results.append({
                "index": idx,
                "url": u,
                "success": False,
                "error": str(e),
                "text": "",
                "images": [],
                "videos": []
            })

    # Compile combined text
    compiled_parts = []
    for r in results:
        if r.get("text"):
            header = f"\n{'='*50}\nPart {r.get('index', 1)}: {r.get('title') or r.get('url')}\n{'='*50}\n\n"
            compiled_parts.append(header + r.get("text") + "\n\n")

    return sanitize_for_json({
        "success": True,
        "total_requested": len(urls_to_process),
        "total_extracted": len(results),
        "results": results,
        "compiled_text": "".join(compiled_parts)
    })

@app.post("/api/download-compiled-txt")
async def download_compiled_txt(req: BatchDownloadTxtRequest):
    """Download all batch chapters merged as a single .txt document."""
    title = req.title or "Facebook_Compiled_Stories"
    output_lines = [f"COLLECTION: {title}\n{'='*60}\n\n"]
    for ch in req.chapters:
        idx = ch.get("index", "")
        ch_title = ch.get("title", f"Part {idx}")
        url = ch.get("url", "")
        text = ch.get("text", "")
        output_lines.append(f"--- [PART {idx}: {ch_title}] ---\nURL: {url}\n\n{text}\n\n{'*'*40}\n\n")
    
    full_content = "".join(output_lines)
    safe_filename = re.sub(r'[^\w\-_\.]', '_', title) + ".txt"
    return Response(
        content=full_content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.get("/api/proxy")
async def proxy_media(url: str = Query(...)):
    """Proxy image/media streams to bypass Facebook CDN cross-origin referrer restrictions."""
    try:
        media_url = urllib.parse.unquote(url)
        req_headers = dict(HEADERS)
        req_headers["Referer"] = "https://www.facebook.com/"
        
        resp = requests.get(media_url, headers=req_headers, stream=True, timeout=20)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Unable to retrieve media from CDN")
        
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
async def download_media(url: str = Query(...), filename: str = Query("media.bin")):
    """Force-download any remote Facebook media file as an attachment."""
    try:
        media_url = urllib.parse.unquote(url)
        req_headers = dict(HEADERS)
        req_headers["Referer"] = "https://www.facebook.com/"
        
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
    """Package extracted post text, metadata, and images into a downloadable zip file."""
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            text_content = f"Source URL: {req.url}\n"
            if req.author:
                text_content += f"Author: {req.author}\n"
            if req.title:
                text_content += f"Title: {req.title}\n"
            text_content += f"{'-'*40}\n\n"
            text_content += req.text or "[No post text found]"
            zip_file.writestr("post_content.txt", text_content.encode("utf-8"))

            meta_dict = {
                "url": req.url,
                "author": req.author,
                "title": req.title,
                "text": req.text,
                "total_images": len(req.images),
                "total_videos": len(req.videos),
                "image_urls": req.images,
                "video_urls": req.videos
            }
            zip_file.writestr("metadata.json", json.dumps(meta_dict, indent=2).encode("utf-8"))

            req_headers = dict(HEADERS)
            req_headers["Referer"] = "https://www.facebook.com/"
            
            for idx, img_url in enumerate(req.images[:20]):
                try:
                    img_resp = requests.get(img_url, headers=req_headers, timeout=10)
                    if img_resp.status_code == 200:
                        ext = ".jpg"
                        if "png" in img_resp.headers.get("Content-Type", ""):
                            ext = ".png"
                        elif "webp" in img_resp.headers.get("Content-Type", ""):
                            ext = ".webp"
                        zip_file.writestr(f"images/image_{idx+1:02d}{ext}", img_resp.content)
                except Exception:
                    continue

        zip_buffer.seek(0)
        clean_title = re.sub(r'[^\w\-_\.]', '_', req.title or "facebook_bundle")[:30]
        zip_filename = f"{clean_title}_extracted.zip"

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

# Mount static folder
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
