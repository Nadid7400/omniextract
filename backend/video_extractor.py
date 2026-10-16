"""
Omni Extractor — Universal Video & Audio Extraction Engine
Powered by yt-dlp and FFmpeg (with automatic imageio-ffmpeg fallback).

Supports YouTube, Shorts, TikTok, Instagram Reels, Facebook, X (Twitter),
Reddit, Vimeo, Dailymotion, Twitch, Pinterest, Adult platforms (18+),
and 1,500+ online video streaming services.
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

def detect_ffmpeg() -> Optional[str]:
    """
    Detect FFmpeg binary:
    1. Check system PATH via shutil.which
    2. Check imageio-ffmpeg python package
    3. Check common installation directories on Windows and Linux
    """
    # 1. System PATH
    sys_path = shutil.which("ffmpeg")
    if sys_path and os.path.exists(sys_path):
        return sys_path

    # 2. imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        img_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if img_exe and os.path.exists(img_exe):
            return img_exe
    except Exception:
        pass

    # 3. Known common locations
    known_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\cloudflared\ffmpeg.exe",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg"
    ]
    for p in known_paths:
        if os.path.exists(p):
            return p

    return None

FFMPEG_PATH = detect_ffmpeg()

def format_duration(seconds: Optional[float]) -> str:
    """Format duration in seconds into HH:MM:SS or MM:SS."""
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
        is_shorts = "/shorts/" in u
        return {
            "name": "YouTube Shorts" if is_shorts else "YouTube",
            "color": "#FF0000",
            "icon": "youtube",
            "badge": "YouTube Shorts" if is_shorts else "YouTube"
        }
    if "facebook.com" in u or "fb.watch" in u or "fb.com" in u or "facebook" in ext:
        is_reel = "/reel" in u or "/reels" in u
        return {
            "name": "Facebook Reels" if is_reel else "Facebook",
            "color": "#1877F2",
            "icon": "facebook",
            "badge": "Facebook Reel" if is_reel else "Facebook"
        }
    if "instagram.com" in u or "instagram" in ext:
        is_reel = "/reel" in u or "/reels" in u
        return {
            "name": "Instagram Reels" if is_reel else "Instagram",
            "color": "#E1306C",
            "icon": "instagram",
            "badge": "Instagram Reel" if is_reel else "Instagram"
        }
    if "tiktok.com" in u or "tiktok" in ext:
        return {
            "name": "TikTok",
            "color": "#00F2FE",
            "icon": "tiktok",
            "badge": "TikTok No Watermark"
        }
    if "twitter.com" in u or "x.com" in u or "twitter" in ext:
        return {
            "name": "X (Twitter)",
            "color": "#1DA1F2",
            "icon": "twitter",
            "badge": "X (Twitter)"
        }
    if "reddit.com" in u or "v.redd.it" in u or "reddit" in ext:
        return {
            "name": "Reddit",
            "color": "#FF4500",
            "icon": "reddit",
            "badge": "Reddit Video"
        }
    if any(adult in u or adult in ext for adult in ["pornhub", "xvideos", "spankbang", "xnxx", "redtube", "youporn", "eporner"]):
        return {
            "name": "Adult Platform (18+)",
            "color": "#FFA500",
            "icon": "adult",
            "badge": "18+ Adult Video"
        }
    if "vimeo.com" in u or "vimeo" in ext:
        return {
            "name": "Vimeo",
            "color": "#1AB7EA",
            "icon": "vimeo",
            "badge": "Vimeo"
        }
    if "dailymotion.com" in u or "dailymotion" in ext:
        return {
            "name": "Dailymotion",
            "color": "#0066DC",
            "icon": "dailymotion",
            "badge": "Dailymotion"
        }
    if "twitch.tv" in u or "twitch" in ext:
        return {
            "name": "Twitch",
            "color": "#9146FF",
            "icon": "twitch",
            "badge": "Twitch Clip"
        }
    if "pinterest.com" in u or "pin.it" in u or "pinterest" in ext:
        return {
            "name": "Pinterest",
            "color": "#E60023",
            "icon": "pinterest",
            "badge": "Pinterest Video"
        }

    clean_name = (extractor_key or "Web Video").replace("Extractor", "").strip()
    return {
        "name": clean_name or "Web Video",
        "color": "#8B5CF6",
        "icon": "video",
        "badge": "Universal Video"
    }

import logging

logger = logging.getLogger("omniextract.extractor")

def is_bot_or_sign_in_error(error_val: Any) -> bool:
    """Detect if an error is specifically a YouTube bot check or sign-in requirement."""
    err_str = str(error_val).lower()
    return any(k in err_str for k in [
        "sign in to confirm",
        "confirm you're not a bot",
        "confirm you’re not a bot",
        "not a bot",
        "use --cookies-from-browser",
        "use --cookies for the authentication",
        "use --cookies",
        "bot verification",
        "bot detection",
        "automated queries",
        "unusual traffic",
        "http error 429",
        "429: too many requests"
    ])

def classify_extraction_error(e: Exception) -> str:
    """
    Map raw yt-dlp errors to user-friendly messages without exposing raw tracebacks in UI.
    Full error details are logged server-side only.
    """
    err_str = str(e)
    err_lower = err_str.lower()

    if is_bot_or_sign_in_error(err_str):
        return (
            "YouTube has blocked this request from the server IP (bot verification required). "
            "To resolve this, please provide YouTube cookies (via the Cookies button or COOKIES_FILE/YT_COOKIES env var), "
            "configure a proxy via PROXY_URL, or run Omni Extractor locally."
        )

    if any(k in err_lower for k in ["private video", "this video is private", "login required", "requires a login"]):
        return "This video is private and cannot be accessed. Please verify permissions or check the link."

    if any(k in err_lower for k in ["age-restricted", "confirm your age", "content warning", "inappropriate for some users"]):
        return "This video is age-restricted and requires YouTube authentication cookies to view."

    if any(k in err_lower for k in ["unavailable", "not available", "does not exist", "removed by the user", "has been removed", "404"]):
        return "This video is unavailable or has been removed."

    if any(k in err_lower for k in ["geo-restricted", "country", "not available in your region", "geolocation"]):
        return "This video is not available in the server's geographic location."

    return "Could not extract media from this link. Please verify the URL and try again."

def resolve_and_copy_cookie_file(custom_cookies: Optional[str] = None) -> Optional[str]:
    """
    Resolve cookie file from COOKIES_FILE, YT_COOKIES env vars, or custom cookies string.
    Copies any cookie file to a safe writable temp location before use.
    Never logs cookie contents.
    """
    writable_dir = tempfile.gettempdir()

    # 1. Custom cookies passed directly via request/UI
    if custom_cookies and str(custom_cookies).strip():
        try:
            import hashlib
            c_hash = hashlib.md5(custom_cookies.encode("utf-8", "ignore")).hexdigest()[:12]
            target_path = os.path.join(writable_dir, f"omniextract_custom_cookie_{c_hash}.txt")
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(custom_cookies.strip())
            return target_path
        except Exception as e:
            logger.warning(f"Failed to write custom cookie file: {e}")

    # 2. YT_COOKIES (or YTDL_COOKIES_CONTENT) env var containing raw cookie text
    raw_cookies_env = os.getenv("YT_COOKIES") or os.getenv("YTDL_COOKIES_CONTENT")
    if raw_cookies_env and raw_cookies_env.strip():
        try:
            target_path = os.path.join(writable_dir, "omniextract_env_cookies.txt")
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(raw_cookies_env.strip())
            logger.info("Loaded YouTube cookies from YT_COOKIES environment variable.")
            return target_path
        except Exception as e:
            logger.warning(f"Failed to write YT_COOKIES to temp file: {e}")

    # 3. COOKIES_FILE (or YTDL_COOKIES) env var containing file path
    cookie_path_env = os.getenv("COOKIES_FILE") or os.getenv("YTDL_COOKIES")
    candidate_paths = [cookie_path_env, "/etc/secrets/cookies.txt", os.path.join(os.getcwd(), "cookies.txt")]

    for c_path in candidate_paths:
        if c_path and os.path.exists(c_path):
            try:
                target_path = os.path.join(writable_dir, "omniextract_active_cookies.txt")
                shutil.copyfile(c_path, target_path)
                logger.info(f"Loaded YouTube cookies from file: {c_path} (copied to writable path).")
                return target_path
            except Exception as e:
                logger.warning(f"Could not copy cookie file '{c_path}' to writable location: {e}")
                return c_path

    logger.warning("No YouTube cookies configured via COOKIES_FILE or YT_COOKIES. Cloud requests may encounter bot verification.")
    return None

class UniversalVideoExtractor:
    """Robust universal video & audio extraction engine powered by yt-dlp."""

    def __init__(self):
        self.ffmpeg_path = FFMPEG_PATH
        self.node_path = shutil.which("node")

    def build_shared_ydl_opts(
        self,
        extra_opts: Optional[Dict[str, Any]] = None,
        is_download: bool = False,
        player_clients: Optional[List[str]] = None,
        cookies: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified shared options builder for EVERY yt-dlp call across the project:
        - Analyze / Single link extraction
        - Batch extraction mode
        - Video downloads & audio downloads
        - Supports COOKIES_FILE, YT_COOKIES, PROXY_URL, player_client overrides.
        """
        opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": not is_download,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "noplaylist": True,
            "concurrent_fragment_downloads": 5,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Fetch-Mode": "navigate"
            }
        }

        # Player client customization (e.g. for bot check retry)
        if player_clients:
            opts["extractor_args"] = {"youtube": {"player_client": list(player_clients)}}

        # Node.js runtime for YouTube signature deciphering
        if self.node_path:
            opts["js_runtimes"] = {"node": {"path": self.node_path}}

        # FFmpeg binary
        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            opts["ffmpeg_location"] = self.ffmpeg_path

        # Requirement 2 & 7: Cookie support from COOKIES_FILE / YT_COOKIES (never logged)
        custom_cookies = (extra_opts or {}).pop("cookies", None) if extra_opts else None
        active_cookies = cookies or custom_cookies
        cookie_file = resolve_and_copy_cookie_file(custom_cookies=active_cookies)
        if cookie_file and os.path.exists(cookie_file):
            opts["cookiefile"] = cookie_file

        # Requirement 3: Optional PROXY_URL support for extraction and download
        proxy_url = os.getenv("PROXY_URL") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if proxy_url and proxy_url.strip():
            opts["proxy"] = proxy_url.strip()

        if extra_opts:
            if "extractor_args" in extra_opts and "extractor_args" in opts:
                merged_ea = dict(opts["extractor_args"])
                merged_ea.update(extra_opts["extractor_args"])
                opts.update(extra_opts)
                opts["extractor_args"] = merged_ea
            else:
                opts.update(extra_opts)

        return opts

    def get_ydl_options(self, extra_opts: Optional[Dict[str, Any]] = None, is_download: bool = False) -> Dict[str, Any]:
        """Backward-compatible alias pointing directly to the shared options builder."""
        return self.build_shared_ydl_opts(extra_opts=extra_opts, is_download=is_download)

    def extract_info(self, url: str, cookies: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract video metadata, dynamically determine all available video resolutions,
        and generate high-quality audio extraction profiles (up to 320 kbps MP3, M4A, FLAC, WAV).
        On bot/sign-in errors, automatically retries with ['tv', 'web_safari'], then ['android', 'ios'].
        """
        info = None
        last_error = None

        # 1. Primary attempt with standard shared options
        try:
            opts = self.build_shared_ydl_opts(extra_opts={"skip_download": True}, is_download=False, cookies=cookies)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as first_err:
            last_error = first_err
            # Requirement 4: On a bot/sign-in error ONLY, retry with player_client ["tv", "web_safari"], then ["android", "ios"]
            if not is_bot_or_sign_in_error(first_err):
                logger.error(f"[OmniExtract] Extraction failed (non-bot error): {first_err}", exc_info=True)
                raise first_err

            logger.warning(f"[OmniExtract] YouTube bot/sign-in error encountered for {url}. Retrying with player_client ['tv', 'web_safari']...")
            try:
                opts_retry1 = self.build_shared_ydl_opts(
                    extra_opts={"skip_download": True},
                    is_download=False,
                    player_clients=["tv", "web_safari"],
                    cookies=cookies
                )
                with yt_dlp.YoutubeDL(opts_retry1) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as retry1_err:
                last_error = retry1_err
                if not is_bot_or_sign_in_error(retry1_err):
                    logger.error(f"[OmniExtract] Retry 1 failed (non-bot error): {retry1_err}", exc_info=True)
                    raise retry1_err

                logger.warning(f"[OmniExtract] YouTube bot error persisted. Retrying with player_client ['android', 'ios']...")
                try:
                    opts_retry2 = self.build_shared_ydl_opts(
                        extra_opts={"skip_download": True},
                        is_download=False,
                        player_clients=["android", "ios"],
                        cookies=cookies
                    )
                    with yt_dlp.YoutubeDL(opts_retry2) as ydl:
                        info = ydl.extract_info(url, download=False)
                except Exception as retry2_err:
                    last_error = retry2_err
                    logger.error(f"[OmniExtract] All bot retries exhausted for {url}: {retry2_err}", exc_info=True)
                    raise retry2_err

        if not info:
            raise ValueError(f"Could not extract video from URL: {str(last_error or 'No media info returned')}")

        # In case of playlist or multi-entry, pick the first video
        if "entries" in info and info["entries"]:
            entries = list(info["entries"])
            if entries:
                info = entries[0]

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

        # -------------------------------------------------------------
        # Dynamic Video Resolutions Parsing
        # -------------------------------------------------------------
        # Gather all distinct valid heights where video codec is present
        detected_heights = set()
        height_to_format: Dict[int, Dict[str, Any]] = {}

        for f in formats:
            h = f.get("height")
            vcodec = f.get("vcodec")
            # Must have height >= 144 and not be audio-only
            if h and isinstance(h, int) and h >= 144 and vcodec != "none":
                detected_heights.add(h)
                # Keep the format with largest filesize or best bitrate for this height
                curr = height_to_format.get(h)
                f_size = f.get("filesize") or f.get("filesize_approx") or 0
                c_size = (curr.get("filesize") or curr.get("filesize_approx") or 0) if curr else 0
                if not curr or f_size > c_size:
                    height_to_format[h] = f

        # If no specific heights found in formats, fallback to top-level info height or standards
        if not detected_heights:
            top_h = info.get("height")
            if top_h and isinstance(top_h, int) and top_h >= 144:
                detected_heights.add(top_h)
            else:
                detected_heights = {1080, 720, 480, 360}

        sorted_heights = sorted(list(detected_heights), reverse=True)
        max_height = sorted_heights[0] if sorted_heights else 1080

        standard_labels = {
            4320: "4320p (8K Ultra HD)",
            2160: "2160p (4K Ultra HD)",
            1440: "1440p (2K Quad HD)",
            1080: "1080p (Full HD)",
            720: "720p (HD)",
            480: "480p (Standard)",
            360: "360p (Medium)",
            240: "240p (Low)",
            144: "144p (Compact)"
        }

        video_downloads: List[Dict[str, Any]] = []

        # 1. Best Quality option (Highest available resolution)
        best_size = info.get("filesize") or info.get("filesize_approx")
        if not best_size and max_height in height_to_format:
            best_size = height_to_format[max_height].get("filesize") or height_to_format[max_height].get("filesize_approx")

        best_badge = "4K ULTRA" if max_height >= 2160 else "2K QHD" if max_height >= 1440 else "1080p FHD" if max_height >= 1080 else f"{max_height}p BEST"
        video_downloads.append({
            "quality": "best",
            "resolution": f"Best Quality ({max_height}p)" if max_height else "Best Quality",
            "height": max_height,
            "format_id": "bestvideo+bestaudio/best",
            "extension": "mp4",
            "badge": best_badge,
            "filesize": format_filesize(best_size),
            "download_url": f"/api/download?url={url}&type=video&quality=best",
            "is_best": True
        })

        # 2. Add each dynamically detected resolution
        for h in sorted_heights:
            fmt = height_to_format.get(h)
            f_size = (fmt.get("filesize") or fmt.get("filesize_approx")) if fmt else None
            
            # Label & badge
            res_label = standard_labels.get(h, f"{h}p")
            badge = f"{h}p"
            if h >= 2160:
                badge = "4K"
            elif h >= 1440:
                badge = "2K"
            elif h >= 1080:
                badge = "1080p"
            elif h >= 720:
                badge = "720p"

            video_downloads.append({
                "quality": str(h),
                "resolution": res_label,
                "height": h,
                "format_id": f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best",
                "extension": "mp4",
                "badge": badge,
                "filesize": format_filesize(f_size),
                "download_url": f"/api/download?url={url}&type=video&quality={h}",
                "is_best": False
            })

        # -------------------------------------------------------------
        # Audio Profiles (MP3 up to 320 kbps CBR, M4A, FLAC, WAV)
        # -------------------------------------------------------------
        audio_downloads: List[Dict[str, Any]] = [
            {
                "codec": "mp3",
                "bitrate": "320",
                "label": "MP3 Studio (320 kbps CBR)",
                "badge": "320K MP3",
                "extension": "mp3",
                "download_url": f"/api/download?url={url}&type=audio&format=mp3&bitrate=320",
                "is_best": True,
                "desc": "Master Studio Quality — Highest MP3 Bitrate"
            },
            {
                "codec": "mp3",
                "bitrate": "256",
                "label": "MP3 High Fidelity (256 kbps)",
                "badge": "256K MP3",
                "extension": "mp3",
                "download_url": f"/api/download?url={url}&type=audio&format=mp3&bitrate=256",
                "is_best": False,
                "desc": "High Fidelity — Audiophile Balance"
            },
            {
                "codec": "mp3",
                "bitrate": "192",
                "label": "MP3 CD Quality (192 kbps)",
                "badge": "192K MP3",
                "extension": "mp3",
                "download_url": f"/api/download?url={url}&type=audio&format=mp3&bitrate=192",
                "is_best": False,
                "desc": "Standard CD Quality"
            },
            {
                "codec": "mp3",
                "bitrate": "128",
                "label": "MP3 Compact (128 kbps)",
                "badge": "128K MP3",
                "extension": "mp3",
                "download_url": f"/api/download?url={url}&type=audio&format=mp3&bitrate=128",
                "is_best": False,
                "desc": "Fast Download & Compact File Size"
            },
            {
                "codec": "m4a",
                "bitrate": "best",
                "label": "M4A / AAC (Source Quality)",
                "badge": "M4A",
                "extension": "m4a",
                "download_url": f"/api/download?url={url}&type=audio&format=m4a&bitrate=best",
                "is_best": False,
                "desc": "Original AAC / M4A Stream — Crystal Clear"
            },
            {
                "codec": "flac",
                "bitrate": "lossless",
                "label": "FLAC Lossless Studio Audio",
                "badge": "FLAC Lossless",
                "extension": "flac",
                "download_url": f"/api/download?url={url}&type=audio&format=flac&bitrate=lossless",
                "is_best": False,
                "desc": "Uncompressed Hi-Res Studio FLAC"
            },
            {
                "codec": "wav",
                "bitrate": "uncompressed",
                "label": "WAV Uncompressed (16-bit PCM)",
                "badge": "WAV PCM",
                "extension": "wav",
                "download_url": f"/api/download?url={url}&type=audio&format=wav&bitrate=uncompressed",
                "is_best": False,
                "desc": "Broadcast Standard Uncompressed Audio"
            }
        ]

        # In-browser preview URL (direct stream if available)
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
            "max_resolution": f"{max_height}p",
            "video_downloads": video_downloads,
            "audio_downloads": audio_downloads,
            "preview_url": preview_url,
            "total_formats": len(formats)
        }

    def download_video_file(self, url: str, quality: str, output_path: str, cookies: Optional[str] = None) -> str:
        """
        Download video at specified resolution (e.g. 2160, 1440, 1080, 720, 480, 360, best)
        and merge with best audio into MP4. Supports both separate video/audio streams and
        progressive single streams (Facebook, TikTok, Instagram, Twitter, YouTube).
        """
        if quality == "best":
            format_spec = "bestvideo*+bestaudio/best"
        else:
            try:
                h = int(quality)
                format_spec = f"bestvideo*[height<={h}]+bestaudio/best[height<={h}]/bestvideo*[height<={h}]/best"
            except Exception:
                format_spec = "bestvideo*+bestaudio/best"

        extra = {
            "skip_download": False,
            "format": format_spec,
            "outtmpl": output_path,
            "merge_output_format": "mp4",
        }

        def run_video_dl(player_clients=None):
            ydl_opts = self.build_shared_ydl_opts(
                extra_opts=extra,
                is_download=True,
                player_clients=player_clients,
                cookies=cookies
            )
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        try:
            run_video_dl(player_clients=None)
        except Exception as first_dl_err:
            if not is_bot_or_sign_in_error(first_dl_err):
                logger.error(f"[OmniExtract] Video download error: {first_dl_err}", exc_info=True)
                raise first_dl_err

            logger.warning(f"[OmniExtract] Bot error on video download for {url}. Retrying with ['tv', 'web_safari']...")
            try:
                run_video_dl(player_clients=["tv", "web_safari"])
            except Exception as retry1_err:
                if not is_bot_or_sign_in_error(retry1_err):
                    logger.error(f"[OmniExtract] Video download retry 1 error: {retry1_err}", exc_info=True)
                    raise retry1_err

                logger.warning(f"[OmniExtract] Bot error persisted on video download. Retrying with ['android', 'ios']...")
                try:
                    run_video_dl(player_clients=["android", "ios"])
                except Exception as retry2_err:
                    logger.error(f"[OmniExtract] All bot retries exhausted on video download: {retry2_err}", exc_info=True)
                    raise retry2_err

        # Find the actual downloaded file in the directory
        parent_dir = os.path.dirname(output_path)
        if os.path.exists(parent_dir):
            files = [f for f in os.listdir(parent_dir) if not f.endswith(".part") and not f.endswith(".ytdl")]
            if files:
                # Prefer .mp4 or the largest file
                mp4s = [f for f in files if f.endswith(".mp4")]
                if mp4s:
                    return os.path.join(parent_dir, mp4s[0])
                return os.path.join(parent_dir, files[0])

        if os.path.exists(output_path):
            return output_path
        return output_path

    def download_audio_file(self, url: str, audio_format: str = "mp3", bitrate: str = "320", output_path: str = "", cookies: Optional[str] = None) -> str:
        """
        Extract audio and convert to specified format (MP3 up to 320 kbps CBR, M4A, FLAC, WAV).
        """
        clean_format = audio_format.lower().strip()
        if clean_format not in ["mp3", "m4a", "flac", "wav"]:
            clean_format = "mp3"

        postprocessor: Dict[str, Any] = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": clean_format
        }

        if clean_format == "mp3":
            clean_bitrate = str(bitrate) if bitrate in ["320", "256", "192", "128"] else "320"
            postprocessor["preferredquality"] = clean_bitrate
        elif clean_format == "m4a":
            postprocessor["preferredquality"] = "0"

        extra = {
            "skip_download": False,
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [postprocessor]
        }

        def run_audio_dl(player_clients=None):
            ydl_opts = self.build_shared_ydl_opts(
                extra_opts=extra,
                is_download=True,
                player_clients=player_clients,
                cookies=cookies
            )
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        try:
            run_audio_dl(player_clients=None)
        except Exception as first_dl_err:
            if not is_bot_or_sign_in_error(first_dl_err):
                logger.error(f"[OmniExtract] Audio download error: {first_dl_err}", exc_info=True)
                raise first_dl_err

            logger.warning(f"[OmniExtract] Bot error on audio download for {url}. Retrying with ['tv', 'web_safari']...")
            try:
                run_audio_dl(player_clients=["tv", "web_safari"])
            except Exception as retry1_err:
                if not is_bot_or_sign_in_error(retry1_err):
                    logger.error(f"[OmniExtract] Audio download retry 1 error: {retry1_err}", exc_info=True)
                    raise retry1_err

                logger.warning(f"[OmniExtract] Bot error persisted on audio download. Retrying with ['android', 'ios']...")
                try:
                    run_audio_dl(player_clients=["android", "ios"])
                except Exception as retry2_err:
                    logger.error(f"[OmniExtract] All bot retries exhausted on audio download: {retry2_err}", exc_info=True)
                    raise retry2_err

        parent_dir = os.path.dirname(output_path)
        target_ext = f".{clean_format}"
        if os.path.exists(parent_dir):
            matched = [f for f in os.listdir(parent_dir) if f.endswith(target_ext)]
            if matched:
                return os.path.join(parent_dir, matched[0])
            all_non_parts = [f for f in os.listdir(parent_dir) if not f.endswith(".part") and not f.endswith(".ytdl")]
            if all_non_parts:
                return os.path.join(parent_dir, all_non_parts[0])

        return output_path

