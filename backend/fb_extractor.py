"""
Facebook Anything Extractor Engine
Extracts post texts, high-res images, and video streams from public Facebook links without login.
Uses multi-strategy scraping: SSR Relay JSON parsing, OpenGraph metadata, and yt-dlp.
"""

import re
import json
import html
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import yt_dlp

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0"
}

def clean_cdn_url(url: str) -> str:
    """Clean and unescape Facebook CDN URLs."""
    if not url:
        return ""
    url = url.replace('\\/', '/')
    url = url.replace('&amp;', '&')
    url = url.replace('\\u0026', '&')
    url = url.strip('"\' ')
    return url

def clean_text_content(text: str) -> str:
    """
    Clean post text from JSON and HTML escapes without corrupting non-ASCII
    or creating lone UTF-8 surrogate code points that crash JSON serialization.
    """
    if not text:
        return ""
    
    # 1. Unescape standard HTML entities (&amp;, &lt;, etc.)
    text = html.unescape(text)

    # 2. Decode JSON-escaped unicode like \u09ae\u09c7 safely
    if '\\u' in text:
        def decode_unicode_escape(match):
            try:
                code_hex = match.group(1)
                return chr(int(code_hex, 16))
            except Exception:
                return match.group(0)
        text = re.sub(r'\\u([0-9a-fA-F]{4})', decode_unicode_escape, text)

    # 3. Re-pair UTF-16 surrogate pairs (e.g. emojis \ud83d\ude04 -> 😄)
    try:
        text = text.encode('utf-16', 'surrogatepass').decode('utf-16', 'replace')
    except Exception:
        pass

    # 4. Strip any lone surrogate characters to guarantee 100% valid UTF-8
    try:
        text = text.encode('utf-8', 'replace').decode('utf-8')
    except Exception:
        pass

    # 5. Clean common JSON escape characters
    text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\/', '/')
    return text.strip()

def normalize_fb_url(url: str) -> str:
    """
    Ensure standard Facebook URL format.
    Automatically extracts the clean URL even if the user pasted numbering like '1.',
    markdown brackets [url](url), or surrounding text.
    """
    url = url.strip()
    match = re.search(r'https?://(?:[a-zA-Z0-9_\-\.]+\.)?facebook\.com/[^\s\)\]"]+', url)
    if match:
        url = match.group(0)
    elif not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Remove trailing punctuation or closing brackets
    url = re.sub(r'[\)\]",\']+$', '', url)
    return url

def extract_all_facebook_urls(text: str) -> List[str]:
    """
    Extracts all Facebook URLs from any formatted text, numbered list, or markdown links.
    Handles concatenated URLs like '.../share/123/48.https://...' cleanly.
    """
    if not text:
        return []
    
    # Add spacing before embedded URLs
    spaced_text = re.sub(r'(\d+\.)?(https?://)', r' \2', text)
    matches = re.findall(r'https?://(?:[a-zA-Z0-9_\-\.]+\.)?facebook\.com/[^\s\)\]"]+', spaced_text)
    
    cleaned_urls = []
    seen = set()
    for u in matches:
        clean_u = re.sub(r'[\)\]",\']+$', '', u).strip()
        if clean_u and clean_u not in seen:
            seen.add(clean_u)
            cleaned_urls.append(clean_u)
    return cleaned_urls

def is_valid_fb_image(url: str) -> bool:
    """Filter out icons, emojis, tracking pixels, and blank assets."""
    u = url.lower()
    if 'rsrc.php' in u or 'emoji.php' in u or 'safe_image.php' in u:
        return False
    if any(k in u for k in ['/p50x50/', '/s50x50/', '/p60x60/', '/s60x60/', '16x16', '32x32', 'badge', 'icon']):
        return False
    return True

class FacebookExtractor:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def resolve_redirects(self, url: str) -> str:
        """Resolve shortened or share URLs like fb.watch or /share/r/"""
        try:
            resp = self.session.head(url, allow_redirects=True, timeout=self.timeout)
            return resp.url
        except Exception:
            return url

    def extract(self, raw_url: str) -> Dict[str, Any]:
        """Extract all texts, photos, and video assets from a public Facebook URL."""
        initial_url = normalize_fb_url(raw_url)
        resolved_url = self.resolve_redirects(initial_url)

        result: Dict[str, Any] = {
            "success": True,
            "url": resolved_url,
            "original_url": initial_url,
            "title": "",
            "text": "",
            "author": {
                "name": "",
                "url": "",
                "avatar": ""
            },
            "type": "post", # post, photo, video, reel, album
            "images": [],
            "videos": [],
            "metadata": {
                "publish_time": None,
                "likes": None,
                "comments": None,
                "shares": None
            },
            "raw_opengraph": {},
            "source": "facebook"
        }

        # Step 1: Fetch HTML and parse SSR data
        html_content = ""
        try:
            resp = self.session.get(resolved_url, headers=HEADERS, timeout=self.timeout, allow_redirects=True)
            if resp.status_code == 200:
                html_content = resp.text
                if resp.url != resolved_url:
                    result["url"] = resp.url
                self._parse_html_and_ssr(html_content, result)
        except Exception as e:
            result["fetch_warning"] = f"HTML fetch error: {str(e)}"

        # Step 2: yt-dlp extraction for video/reel only if it's actually a video link
        is_video_link = any(v in result["url"].lower() for v in ['reel', 'watch', 'video', 'fb.watch', '/share/r', '/share/v'])
        if is_video_link or bool(result["videos"]):
            self._parse_with_ytdlp(result["url"], result)

        # Step 3: Polish and deduplicate
        self._polish_results(result)

        if not result["text"] and not result["images"] and not result["videos"] and not result["title"]:
            result["success"] = False
            result["error"] = "Could not extract content from this Facebook link. Ensure the post/video is publicly visible."

        return result

    def _parse_html_and_ssr(self, html_text: str, result: Dict[str, Any]):
        soup = BeautifulSoup(html_text, 'html.parser')

        # 1. OpenGraph / Twitter Meta Tags
        og = {}
        for tag in soup.find_all('meta'):
            prop = tag.get('property', '') or tag.get('name', '')
            content = tag.get('content', '')
            if prop and content:
                og[prop] = content
        result["raw_opengraph"] = og

        # Title
        if "og:title" in og:
            result["title"] = clean_text_content(og["og:title"])
        elif soup.find('title'):
            result["title"] = clean_text_content(soup.find('title').text)

        # OpenGraph Description as initial text
        og_desc = og.get("og:description") or og.get("description") or og.get("twitter:description") or ""
        if og_desc:
            result["text"] = clean_text_content(og_desc)

        # Author info
        if "og:site_name" in og and og["og:site_name"] not in ["Facebook", "Meta"]:
            result["author"]["name"] = clean_text_content(og["og:site_name"])
        elif result["title"]:
            parts = re.split(r'\s+[|\-•]\s+', result["title"])
            if len(parts) > 1 and parts[0].strip():
                result["author"]["name"] = parts[0].strip()

        # Cover/Primary Image from OpenGraph
        if "og:image" in og:
            og_img = clean_cdn_url(og["og:image"])
            if is_valid_fb_image(og_img):
                result["images"].append({
                    "url": og_img,
                    "type": "cover",
                    "label": "Featured / Cover Image"
                })

        # Video from OpenGraph / Twitter
        og_video = og.get("og:video") or og.get("og:video:url") or og.get("og:video:secure_url") or og.get("twitter:player:stream")
        if og_video:
            clean_vid = clean_cdn_url(og_video)
            result["videos"].append({
                "url": clean_vid,
                "quality": "Standard",
                "format": "mp4",
                "source": "meta_tag"
            })

        # 2. SSR Relay JSON Search for full post text
        # Use regex pattern that supports escaped characters and quotes
        text_patterns = [
            r'"message":\{"text":"((?:[^"\\]|\\.)*)"\}',
            r'"story":\{.*?"message":\{"text":"((?:[^"\\]|\\.)*)"\}',
            r'"post_message":\{"text":"((?:[^"\\]|\\.)*)"\}',
            r'"creation_story":\{.*?"message":\{"text":"((?:[^"\\]|\\.)*)"\}',
            r'"comet_sections":\{.*?"message":\{"text":"((?:[^"\\]|\\.)*)"\}',
            r'"text":"([^"]{20,})","__typename":"TextWithEntities"'
        ]
        
        found_texts = []
        for pat in text_patterns:
            try:
                matches = re.findall(pat, html_text)
                for m in matches:
                    raw = m if isinstance(m, str) else m[0]
                    cleaned = clean_text_content(raw)
                    if cleaned and len(cleaned) > 5 and not cleaned.startswith('http'):
                        found_texts.append(cleaned)
            except Exception:
                continue

        if found_texts:
            # Pick the longest authentic message text
            longest = max(found_texts, key=len)
            if len(longest) >= len(result["text"]):
                result["text"] = longest

        # 3. High-res Photo Extraction from SSR Relay
        scontent_matches = re.findall(r'https://scontent[^\s"\'<>\\]+(?:\\/[^\s"\'<>\\]+)*', html_text)
        for match in scontent_matches:
            c_url = clean_cdn_url(match)
            if is_valid_fb_image(c_url):
                if not any(item['url'] == c_url for item in result["images"]):
                    result["images"].append({
                        "url": c_url,
                        "type": "photo",
                        "label": f"Image #{len(result['images']) + 1}"
                    })

        # Avatar extraction
        avatar_matches = re.findall(r'"profile_picture":\{"uri":"(https:[^"]+)"\}', html_text)
        if avatar_matches:
            result["author"]["avatar"] = clean_cdn_url(avatar_matches[0])
        elif not result["author"]["avatar"]:
            actor_matches = re.findall(r'"profile_photo":\{"url":"(https:[^"]+)"\}', html_text)
            if actor_matches:
                result["author"]["avatar"] = clean_cdn_url(actor_matches[0])

        # 4. Embedded Video Stream extraction from SSR
        video_stream_patterns = [
            (r'"playable_url_quality_hd":"(https:[^"]+)"', "HD (720p+)"),
            (r'"browser_native_hd_url":"(https:[^"]+)"', "HD"),
            (r'"playable_url":"(https:[^"]+)"', "SD"),
            (r'"browser_native_sd_url":"(https:[^"]+)"', "SD"),
            (r'"hd_src":"(https:[^"]+)"', "HD"),
            (r'"sd_src":"(https:[^"]+)"', "SD")
        ]
        for pattern, quality in video_stream_patterns:
            try:
                matches = re.findall(pattern, html_text)
                for m in matches:
                    v_url = clean_cdn_url(m)
                    if not any(v['url'] == v_url for v in result["videos"]):
                        result["videos"].append({
                            "url": v_url,
                            "quality": quality,
                            "format": "mp4",
                            "source": "ssr_payload"
                        })
            except Exception:
                continue

    def _parse_with_ytdlp(self, url: str, result: Dict[str, Any]):
        """Use yt-dlp to extract high-quality video formats, thumbnails, and metadata."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
            'socket_timeout': self.timeout,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return

                if not result["title"] and info.get("title"):
                    result["title"] = info.get("title")

                desc = info.get("description")
                if desc and len(desc.strip()) > len(result["text"]):
                    result["text"] = clean_text_content(desc)

                if not result["author"]["name"] and info.get("uploader"):
                    result["author"]["name"] = info.get("uploader")

                thumb = info.get("thumbnail")
                if thumb:
                    c_thumb = clean_cdn_url(thumb)
                    if is_valid_fb_image(c_thumb) and not any(img['url'] == c_thumb for img in result["images"]):
                        result["images"].insert(0, {
                            "url": c_thumb,
                            "type": "thumbnail",
                            "label": "Video Poster / Thumbnail"
                        })

                formats = info.get("formats", [])
                seen_urls = set(v["url"] for v in result["videos"])
                for f in formats:
                    v_url = f.get("url")
                    if not v_url or v_url in seen_urls:
                        continue
                    
                    vcodec = f.get("vcodec", "")
                    acodec = f.get("acodec", "")
                    is_video = vcodec != "none" or f.get("ext") == "mp4" or "video" in str(f.get("format_note", "")).lower()
                    
                    if is_video:
                        h = f.get("height")
                        res = f.get("resolution") or (f"{h}p" if h else f.get("format_id"))
                        quality = "HD" if (h and h >= 720) or "hd" in str(f.get("format_id", "")).lower() else "SD"
                        
                        result["videos"].append({
                            "url": v_url,
                            "quality": f"{quality} ({res})" if res else quality,
                            "format": f.get("ext", "mp4"),
                            "filesize": f.get("filesize") or f.get("filesize_approx"),
                            "source": "yt-dlp",
                            "duration": info.get("duration"),
                            "has_audio": acodec != "none"
                        })
                        seen_urls.add(v_url)

                if result["videos"]:
                    result["type"] = "video"
        except Exception:
            pass

    def _polish_results(self, result: Dict[str, Any]):
        """Deduplicate images, set clean labels, and determine overall content type."""
        seen_img_bases = set()
        unique_images = []
        for img in result["images"]:
            u = img["url"]
            base = u.split("?")[0] if "?" in u else u
            if base not in seen_img_bases:
                seen_img_bases.add(base)
                unique_images.append(img)
        result["images"] = unique_images

        seen_vid_bases = set()
        unique_videos = []
        for vid in result["videos"]:
            u = vid["url"]
            base = u.split("?")[0] if "?" in u else u
            if base not in seen_vid_bases:
                seen_vid_bases.add(base)
                unique_videos.append(vid)
        result["videos"] = unique_videos

        if "reel" in result["url"].lower():
            result["type"] = "reel"
        elif result["videos"]:
            result["type"] = "video"
        elif len(result["images"]) > 1:
            result["type"] = "album"
        elif len(result["images"]) == 1:
            result["type"] = "photo"
        else:
            result["type"] = "text_post"

        if result["text"]:
            result["text"] = result["text"].strip()
            result["text"] = re.sub(r'(\s*Log in or sign up to view.*|\s*See more of .* on Facebook)$', '', result["text"], flags=re.I).strip()
