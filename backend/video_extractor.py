"""
Universal Video & Audio Extractor Engine powered by yt-dlp and FFmpeg.
Supports YouTube, Facebook, TikTok, Instagram, Twitter/X, Reddit, Vimeo,
Adult websites (Pornhub, XVideos, SpankBang, etc.), and 1,000+ online video platforms.
"""

import os
import re
import sys
import json
import time
import shutil
import tempfile
from typing import Dict, Any, List, Optional
import yt_dlp

# Detect FFmpeg executable
FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    # Check system PATH
    shutil_path = shutil.which("ffmpeg")
    if shutil_path:
        FFMPEG_PATH = shutil_path
    elif os.path.exists(r"C:\Program Files (x86)\cloudflared\ffmpeg.exe"):
        FFMPEG_PATH = r"C:\Program Files (x86)\cloudflared\ffmpeg.exe"

def format_duration(seconds: Optional[float]) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "N/A"
    try:
        s = int(seconds)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:d}:{s:02d}"
    except Exception:
        return str(seconds)

def format_filesize(bytes_val: Optional[int]) -> str:
    """Format bytes into readable MB or GB."""
    if not bytes_val or bytes_val <= 0:
        return ""
    try:
        mb = bytes_val / (1024 * 1024)
        if mb >= 1000:
            return f"{mb / 1024:.2f} GB"
        return f"{mb:.1f} MB"
    except Exception:
        return ""

def detect_platform(url: str, extractor_key: Optional[str] = None) -> Dict[str, str]:
    """Detect platform name, badge color, and icon type from URL and yt-dlp extractor."""
    u = url.lower()
    ext = (extractor_key or "").lower()

    if "youtube" in u or "youtu.be" in u or "youtube" in ext:
        return {"name": "YouTube", "color": "#FF0000", "icon": "youtube"}
    if "facebook.com" in u or "fb.watch" in u or "facebook" in ext:
        return {"name": "Facebook", "color": "#1877F2", "icon": "facebook"}
    if "instagram.com" in u or "instagram" in ext:
        return {"name": "Instagram", "color": "#E4405F", "icon": "instagram"}
    if "tiktok.com" in u or "tiktok" in ext:
        return {"name": "TikTok", "color": "#00F2FE", "icon": "tiktok"}
    if "twitter.com" in u or "x.com" in u or "twitter" in ext:
        return {"name": "X / Twitter", "color": "#1DA1F2", "icon": "twitter"}
    if "reddit.com" in u or "v.redd.it" in u or "reddit" in ext:
        return {"name": "Reddit", "color": "#FF4500", "icon": "reddit"}
    if any(adult in u or adult in ext for adult in ["pornhub", "xvideos", "spankbang", "xnxx", "redtube", "youporn", "eporner"]):
        return {"name": "Adult Platform (18+)", "color": "#FFA500", "icon": "adult"}
    if "vimeo.com" in u or "vimeo" in ext:
        return {"name": "Vimeo", "color": "#1AB7EA", "icon": "vimeo"}
    if "dailymotion.com" in u or "dailymotion" in ext:
        return {"name": "Dailymotion", "color": "#0066DC", "icon": "dailymotion"}
    
    return {"name": extractor_key or "Web Video", "color": "#E11D48", "icon": "video"}

class UniversalVideoExtractor:
    """Universal Video & Audio Downloader Engine."""

    def __init__(self):
        self.ffmpeg_path = FFMPEG_PATH

    def get_ydl_options(self, extra_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Base yt-dlp configuration with anti-blocking headers, android client, and ffmpeg."""
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "headers": {
                "Accept-Language": "en-US,en;q=0.9",
            }
        }
        node_bin = shutil.which("node")
        if node_bin:
            opts["js_runtimes"] = {"node": {"path": node_bin}}

        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            opts["ffmpeg_location"] = self.ffmpeg_path

        if extra_opts:
            opts.update(extra_opts)
        return opts

    def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract video metadata and categorize download formats (1080p, 720p, 480p, 360p, 240p, 144p & MP3s)."""
        opts = self.get_ydl_options({"skip_download": True})
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                # Retry with relaxed options if needed
                raise ValueError(f"Could not extract video from URL: {str(e)}")

        if not info:
            raise ValueError("No video information returned for this link.")

        # In case of playlist, pick the first video or summary
        if "entries" in info and info["entries"]:
            info = list(info["entries"])[0]

        title = info.get("title") or "video_download"
        duration = info.get("duration")
        uploader = info.get("uploader") or info.get("channel") or info.get("creator") or "Unknown Creator"
        uploader_url = info.get("uploader_url") or info.get("channel_url")
        thumbnail = info.get("thumbnail")
        view_count = info.get("view_count")
        like_count = info.get("like_count")
        description = info.get("description") or ""
        platform = detect_platform(url, info.get("extractor_key"))

        formats = info.get("formats", [])

        # Categorize video formats by target resolutions: 1080, 720, 480, 360, 240, 144
        target_resolutions = [1080, 720, 480, 360, 240, 144]
        res_labels = {
            1080: "1080p (Full HD)",
            720: "720p (HD)",
            480: "480p (Standard)",
            360: "360p (Medium)",
            240: "240p (Low)",
            144: "144p (Compact)"
        }

        # Find best available formats
        video_downloads = []
        seen_res = set()

        # Check maximum height available
        max_height = 0
        for f in formats:
            h = f.get("height") or 0
            if h > max_height:
                max_height = h

        # 1. Best Quality Option
        video_downloads.append({
            "quality": "best",
            "resolution": f"Best Quality ({max_height}p)" if max_height else "Best Quality",
            "height": max_height or 1080,
            "format_id": "bestvideo+bestaudio/best",
            "extension": "mp4",
            "badge": "ULTRA HD" if max_height >= 1080 else "BEST",
            "filesize": format_filesize(info.get("filesize") or info.get("filesize_approx")),
            "download_url": f"/api/download-video?url={url}&quality=best",
            "is_best": True
        })

        # 2. Add each target resolution: 1080p, 720p, 480p, 360p, 240p, 144p
        for res in target_resolutions:

            # Look for format close to this resolution
            matching_format = None
            for f in formats:
                h = f.get("height") or 0
                if h == res:
                    matching_format = f
                    break

            size_str = ""
            if matching_format:
                size_str = format_filesize(matching_format.get("filesize") or matching_format.get("filesize_approx"))

            video_downloads.append({
                "quality": str(res),
                "resolution": res_labels.get(res, f"{res}p"),
                "height": res,
                "format_id": f"bestvideo[height<={res}]+bestaudio/best[height<={res}]/best",
                "extension": "mp4",
                "badge": f"{res}p",
                "filesize": size_str,
                "download_url": f"/api/download-video?url={url}&quality={res}",
                "is_best": False
            })

        # 3. Audio Formats (up to 320 kbps as requested)
        audio_downloads = [
            {
                "bitrate": "320",
                "label": "320 kbps MP3 (Master Studio Quality)",
                "badge": "320K",
                "extension": "mp3",
                "download_url": f"/api/download-audio?url={url}&bitrate=320",
                "is_best": True
            },
            {
                "bitrate": "256",
                "label": "256 kbps MP3 (High Fidelity)",
                "badge": "256K",
                "extension": "mp3",
                "download_url": f"/api/download-audio?url={url}&bitrate=256",
                "is_best": False
            },
            {
                "bitrate": "192",
                "label": "192 kbps MP3 (Standard CD Quality)",
                "badge": "192K",
                "extension": "mp3",
                "download_url": f"/api/download-audio?url={url}&bitrate=192",
                "is_best": False
            },
            {
                "bitrate": "128",
                "label": "128 kbps MP3 (Compact & Fast)",
                "badge": "128K",
                "extension": "mp3",
                "download_url": f"/api/download-audio?url={url}&bitrate=128",
                "is_best": False
            }
        ]

        # In-browser preview URL (direct stream if available or proxy)
        preview_url = None
        for f in formats:
            if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("ext") == "mp4":
                preview_url = f.get("url")
                break
        if not preview_url and formats:
            for f in formats:
                if f.get("url") and "googlevideo" not in f.get("url", ""):
                    preview_url = f.get("url")
                    break

        return {
            "success": True,
            "url": url,
            "title": title,
            "description": description[:4000],
            "uploader": uploader,
            "uploader_url": uploader_url,
            "duration": duration,
            "duration_string": format_duration(duration),
            "view_count": view_count,
            "like_count": like_count,
            "thumbnail": thumbnail,
            "platform": platform,
            "max_resolution": f"{max_height}p" if max_height else "1080p",
            "video_downloads": video_downloads,
            "audio_downloads": audio_downloads,
            "preview_url": preview_url,
            "total_formats": len(formats)
        }

    def download_video_file(self, url: str, quality: str, output_path: str) -> str:
        """Download video at specified resolution (e.g. 1080, 720, 480, 360, 240, 144, best) and merge to MP4."""
        if quality == "best":
            format_spec = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        else:
            try:
                h = int(quality)
                format_spec = f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
            except Exception:
                format_spec = "bestvideo+bestaudio/best"

        ydl_opts = self.get_ydl_options({
            "skip_download": False,
            "format": format_spec,
            "outtmpl": output_path,
            "merge_output_format": "mp4",
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the actual downloaded file in directory
        parent_dir = os.path.dirname(output_path)
        if os.path.exists(parent_dir):
            files = [f for f in os.listdir(parent_dir) if not f.endswith(".part") and not f.endswith(".ytdl")]
            if files:
                # Prefer .mp4 or largest file
                mp4s = [f for f in files if f.endswith(".mp4")]
                if mp4s:
                    return os.path.join(parent_dir, mp4s[0])
                return os.path.join(parent_dir, files[0])

        if os.path.exists(output_path):
            return output_path
        return output_path

    def download_audio_file(self, url: str, bitrate: str, output_path: str) -> str:
        """Extract audio and convert to MP3 at specified bitrate (up to 320 kbps)."""
        clean_bitrate = str(bitrate) if bitrate in ["320", "256", "192", "128"] else "320"
        
        ydl_opts = self.get_ydl_options({
            "skip_download": False,
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": clean_bitrate,
            }]
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find generated .mp3 file
        parent_dir = os.path.dirname(output_path)
        if os.path.exists(parent_dir):
            mp3_files = [f for f in os.listdir(parent_dir) if f.endswith(".mp3")]
            if mp3_files:
                return os.path.join(parent_dir, mp3_files[0])
            all_files = [f for f in os.listdir(parent_dir) if not f.endswith(".part")]
            if all_files:
                return os.path.join(parent_dir, all_files[0])

        return output_path
