"""
Facebook Anything Extractor Engine — Enhanced Edition
Extracts post texts, high-res images, and video streams from ANY Facebook link,
including locked/private/restricted posts through multi-strategy bypass:

Strategies:
  1. Standard desktop HTML + SSR Relay JSON parsing
  2. Mobile User-Agent fallback (m.facebook.com)
  3. mbasic.facebook.com text-only scraping (no JS required)
  4. Facebook oEmbed API (public embed metadata)
  5. Google Cache / Wayback Machine archive lookups
  6. Authenticated cookie-based session (for truly private content)
"""

import re
import json
import html
import urllib.parse
import time
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import yt_dlp

HEADERS_DESKTOP = {
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

# Keep backward-compatible alias
HEADERS = HEADERS_DESKTOP

HEADERS_MOBILE = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
}

HEADERS_MBASIC = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
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

    # 2. Decode JSON-escaped unicode like \\u09ae\\u09c7 safely
    if '\\u' in text:
        def decode_unicode_escape(match):
            try:
                code_hex = match.group(1)
                return chr(int(code_hex, 16))
            except Exception:
                return match.group(0)
        text = re.sub(r'\\u([0-9a-fA-F]{4})', decode_unicode_escape, text)

    # 3. Re-pair UTF-16 surrogate pairs (e.g. emojis \\ud83d\\ude04 -> 😄)
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
    url = re.sub(r'[\)\]"\',\']+$', '', url)
    return url


def extract_all_facebook_urls(text: str) -> List[str]:
    """
    Extracts all Facebook URLs from any formatted text, numbered list, or markdown links.
    Handles concatenated URLs like '.../share/123/48.https://...' cleanly.
    """
    if not text:
        return []
    
    # Add spacing before embedded URLs
    spaced_text = re.sub(r'(\d+\.)(https?://)', r' \2', text)
    matches = re.findall(r'https?://(?:[a-zA-Z0-9_\-\.]+\.)?facebook\.com/[^\s\)\]"]+', spaced_text)
    
    cleaned_urls = []
    seen = set()
    for u in matches:
        clean_u = re.sub(r'[\)\]"\',\']+$', '', u).strip()
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


def _convert_to_mbasic_url(url: str) -> str:
    """Convert any Facebook URL to its mbasic.facebook.com equivalent."""
    return re.sub(
        r'https?://(www\.|m\.|web\.)?facebook\.com',
        'https://mbasic.facebook.com',
        url
    )


def _convert_to_mobile_url(url: str) -> str:
    """Convert any Facebook URL to its m.facebook.com equivalent."""
    return re.sub(
        r'https?://(www\.|mbasic\.|web\.)?facebook\.com',
        'https://m.facebook.com',
        url
    )


def _extract_post_id(url: str) -> Optional[str]:
    """Extract numeric Facebook post/story ID from a URL."""
    patterns = [
        r'/posts/(\d+)',
        r'/permalink/(\d+)',
        r'story_fbid=(\d+)',
        r'/photos/[^/]+/(\d+)',
        r'/photo/\?fbid=(\d+)',
        r'fbid=(\d+)',
        r'/videos/(\d+)',
        r'/reel/(\d+)',
        r'/share/p/([a-zA-Z0-9]+)',
        r'/share/r/([a-zA-Z0-9]+)',
        r'/share/v/([a-zA-Z0-9]+)',
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def parse_fb_cookies(raw: Any) -> Dict[str, str]:
    """
    Parse cookies from multiple formats:
    - Dict: {"c_user": "...", "xs": "..."}
    - Header string: "c_user=1000...; xs=...; datr=..."
    - JSON string or list of cookie dicts
    - Netscape cookies.txt format
    """
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {str(k).strip(): str(v).strip() for k, v in raw.items() if str(k).strip()}
    
    cookie_dict = {}
    if isinstance(raw, str):
        raw_str = raw.strip()
        if (raw_str.startswith("{") and raw_str.endswith("}")) or (raw_str.startswith("[") and raw_str.endswith("]")):
            try:
                parsed = json.loads(raw_str)
                if isinstance(parsed, dict):
                    return {str(k).strip(): str(v).strip() for k, v in parsed.items() if str(k).strip()}
                elif isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict) and "name" in item and "value" in item:
                            cookie_dict[str(item["name"]).strip()] = str(item["value"]).strip()
                    if cookie_dict:
                        return cookie_dict
            except Exception:
                pass
        
        lines = raw_str.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 7:
                    cookie_dict[parts[5].strip()] = parts[6].strip()
            else:
                for chunk in line.split(";"):
                    chunk = chunk.strip()
                    if "=" in chunk:
                        name, _, value = chunk.partition("=")
                        name = name.strip()
                        value = value.strip()
                        if name and not name.startswith("#"):
                            cookie_dict[name] = value
    return cookie_dict


class FacebookExtractor:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS_DESKTOP)
        # Cookie store for authenticated sessions (user-provided cookies)
        self._auth_cookies: Dict[str, str] = {}
        # Track which strategies succeeded
        self._strategies_used: List[str] = []

    def set_cookies(self, cookies: Any):
        """Set Facebook authentication cookies for private/locked content extraction."""
        self._auth_cookies = parse_fb_cookies(cookies)

    def clear_cookies(self):
        """Remove all stored authentication cookies."""
        self._auth_cookies = {}

    def has_cookies(self) -> bool:
        """Check if authentication cookies are configured."""
        return bool(self._auth_cookies)

    def get_cookie_status(self) -> Dict[str, Any]:
        """Return status information about stored authentication cookies."""
        c_user = self._auth_cookies.get("c_user", "")
        has_xs = bool(self._auth_cookies.get("xs"))
        return {
            "has_cookies": bool(self._auth_cookies),
            "user_id": c_user if c_user else None,
            "has_xs": has_xs,
            "count": len(self._auth_cookies)
        }

    def resolve_redirects(self, url: str) -> str:
        """Resolve shortened or share URLs like fb.watch or /share/r/"""
        try:
            resp = self.session.head(url, allow_redirects=True, timeout=self.timeout)
            return resp.url
        except Exception:
            return url

    def extract(self, raw_url: str, cookies: Optional[Any] = None) -> Dict[str, Any]:
        """Extract all texts, photos, and video assets from a Facebook URL.
        
        Uses a cascading multi-strategy approach:
        1. Standard desktop scrape
        2. Mobile scrape fallback
        3. mbasic.facebook.com text extraction
        4. oEmbed API metadata
        5. Google Cache / Wayback Machine
        6. Cookie-authenticated session (if cookies are provided or stored)
        """
        # If per-request cookies were provided, temporarily apply them
        original_cookies = dict(self._auth_cookies)
        if cookies:
            req_cookies = parse_fb_cookies(cookies)
            if req_cookies:
                self._auth_cookies = req_cookies

        initial_url = normalize_fb_url(raw_url)
        resolved_url = self.resolve_redirects(initial_url)
        self._strategies_used = []

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
            "source": "facebook",
            "extraction_strategies": [],
            "is_locked": False,
            "lock_bypass_used": None
        }

        # === STRATEGY 1: Standard Desktop HTML + SSR ===
        html_content = ""
        is_login_walled = False
        try:
            resp = self.session.get(resolved_url, headers=HEADERS_DESKTOP, timeout=self.timeout, allow_redirects=True)
            if resp.status_code == 200:
                html_content = resp.text
                if resp.url != resolved_url:
                    result["url"] = resp.url
                
                is_login_walled = self._detect_login_wall(html_content)
                
                if not is_login_walled:
                    self._parse_html_and_ssr(html_content, result)
                    if result["text"] or result["images"] or result["videos"]:
                        self._strategies_used.append("desktop_ssr")
        except Exception as e:
            result["fetch_warning"] = f"HTML fetch error: {str(e)}"

        # === STRATEGY 2: Mobile User-Agent Fallback ===
        if not result["text"] and not result["images"]:
            try:
                mobile_url = _convert_to_mobile_url(resolved_url)
                resp = self.session.get(mobile_url, headers=HEADERS_MOBILE, timeout=self.timeout, allow_redirects=True)
                if resp.status_code == 200:
                    mobile_html = resp.text
                    if not self._detect_login_wall(mobile_html):
                        self._parse_html_and_ssr(mobile_html, result)
                        if result["text"] or result["images"]:
                            self._strategies_used.append("mobile_fallback")
                            result["lock_bypass_used"] = "mobile_ua"
            except Exception:
                pass

        # === STRATEGY 3: mbasic.facebook.com (Pure HTML, No JS) ===
        if not result["text"]:
            try:
                mbasic_data = self._scrape_mbasic(resolved_url)
                if mbasic_data.get("text") and len(mbasic_data["text"]) > len(result["text"]):
                    result["text"] = mbasic_data["text"]
                    self._strategies_used.append("mbasic_scrape")
                    result["lock_bypass_used"] = "mbasic"
                if mbasic_data.get("author_name") and not result["author"]["name"]:
                    result["author"]["name"] = mbasic_data["author_name"]
                if mbasic_data.get("images"):
                    for img_url in mbasic_data["images"]:
                        if is_valid_fb_image(img_url) and not any(i["url"] == img_url for i in result["images"]):
                            result["images"].append({
                                "url": img_url,
                                "type": "photo",
                                "label": f"Image #{len(result['images']) + 1} (mbasic)"
                            })
            except Exception:
                pass

        # === STRATEGY 4: Facebook oEmbed API ===
        if not result["text"] and not result["title"]:
            try:
                oembed_data = self._fetch_oembed(resolved_url)
                if oembed_data:
                    if oembed_data.get("title") and not result["title"]:
                        result["title"] = clean_text_content(oembed_data["title"])
                    if oembed_data.get("author_name") and not result["author"]["name"]:
                        result["author"]["name"] = oembed_data["author_name"]
                    if oembed_data.get("author_url") and not result["author"]["url"]:
                        result["author"]["url"] = oembed_data["author_url"]
                    if oembed_data.get("html"):
                        # Extract embedded content text from the oEmbed HTML
                        embed_soup = BeautifulSoup(oembed_data["html"], "html.parser")
                        embed_text = embed_soup.get_text(separator="\n", strip=True)
                        if embed_text and len(embed_text) > len(result["text"]):
                            result["text"] = clean_text_content(embed_text)
                    self._strategies_used.append("oembed_api")
            except Exception:
                pass

        # === STRATEGY 5: Google Cache + Wayback Machine ===
        if not result["text"] and not result["images"]:
            try:
                archive_data = self._fetch_from_archives(resolved_url)
                if archive_data:
                    if archive_data.get("text") and len(archive_data["text"]) > len(result["text"]):
                        result["text"] = archive_data["text"]
                    if archive_data.get("images"):
                        for img_url in archive_data["images"]:
                            if is_valid_fb_image(img_url) and not any(i["url"] == img_url for i in result["images"]):
                                result["images"].append({
                                    "url": img_url,
                                    "type": "photo",
                                    "label": f"Image #{len(result['images']) + 1} (archive)"
                                })
                    if archive_data.get("title") and not result["title"]:
                        result["title"] = archive_data["title"]
                    self._strategies_used.append("web_archive")
                    result["lock_bypass_used"] = "archive_cache"
            except Exception:
                pass

        # === STRATEGY 6: Cookie-Authenticated Session ===
        if self._auth_cookies and (not result["text"] and not result["images"] and not result["videos"]):
            try:
                auth_data = self._extract_with_cookies(resolved_url)
                if auth_data:
                    if auth_data.get("text") and len(auth_data["text"]) > len(result["text"]):
                        result["text"] = auth_data["text"]
                    if auth_data.get("images"):
                        for img in auth_data["images"]:
                            if not any(i["url"] == img["url"] for i in result["images"]):
                                result["images"].append(img)
                    if auth_data.get("videos"):
                        for vid in auth_data["videos"]:
                            if not any(v["url"] == vid["url"] for v in result["videos"]):
                                result["videos"].append(vid)
                    if auth_data.get("author_name") and not result["author"]["name"]:
                        result["author"]["name"] = auth_data["author_name"]
                    self._strategies_used.append("cookie_auth")
                    result["lock_bypass_used"] = "authenticated_session"
            except Exception:
                pass

        # Step 2: yt-dlp extraction for video/reel only if it's actually a video link
        is_video_link = any(v in result["url"].lower() for v in ['reel', 'watch', 'video', 'fb.watch', '/share/r', '/share/v'])
        if is_video_link or bool(result["videos"]):
            self._parse_with_ytdlp(result["url"], result)

        # Step 3: Polish and deduplicate
        self._polish_results(result)

        # Record strategies
        result["extraction_strategies"] = self._strategies_used
        result["is_locked"] = is_login_walled

        if not result["text"] and not result["images"] and not result["videos"] and not result["title"]:
            result["success"] = False
            if is_login_walled and not self._auth_cookies:
                result["error"] = (
                    "This post appears to be locked or restricted behind a login wall. "
                    "All bypass strategies were attempted. You can try: "
                    "(1) Provide your Facebook cookies for authenticated extraction, or "
                    "(2) Check if the post is truly public."
                )
            else:
                result["error"] = "Could not extract content from this Facebook link. Ensure the post/video is publicly visible."

        return result

    def _detect_login_wall(self, html_text: str) -> bool:
        """Detect if Facebook is serving a login/signup wall instead of content."""
        login_indicators = [
            'id="login_form"',
            'id="loginform"',
            '"login_form"',
            "Log in or sign up to view",
            "You must log in to continue",
            "Create new account",
            'name="login"',
            'id="mobile_login_bar"',
            "content_not_available",
            "This content isn't available",
            "This page isn't available",
        ]
        html_lower = html_text.lower()
        return any(indicator.lower() in html_lower for indicator in login_indicators)

    def _scrape_mbasic(self, url: str) -> Dict[str, Any]:
        """
        Scrape mbasic.facebook.com — the ultra-lightweight, no-JavaScript Facebook
        that often renders post content even when the main site blocks it.
        """
        mbasic_url = _convert_to_mbasic_url(url)
        result = {"text": "", "author_name": "", "images": []}

        try:
            resp = self.session.get(mbasic_url, headers=HEADERS_MBASIC, timeout=self.timeout, allow_redirects=True)
            if resp.status_code != 200:
                return result

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Check for login wall on mbasic
            if self._detect_login_wall(resp.text):
                return result

            # Extract post text from mbasic structure
            # mbasic wraps post content in specific divs
            post_divs = soup.find_all('div', {'data-ft': True})
            texts = []
            for div in post_divs:
                # Get paragraphs within post body
                paragraphs = div.find_all('p')
                for p in paragraphs:
                    t = p.get_text(strip=True)
                    if t and len(t) > 3:
                        texts.append(t)

            # Fallback: look for the main story body
            if not texts:
                story_div = soup.find('div', class_=re.compile(r'(story_body|_5rgt|_2phc|bi|bj|bl)'))
                if story_div:
                    t = story_div.get_text(separator='\n', strip=True)
                    if t:
                        texts.append(t)

            # Another fallback: main article or content area
            if not texts:
                for sel in ['article', '[role="article"]', '#m_story_permalink_view']:
                    container = soup.select_one(sel)
                    if container:
                        t = container.get_text(separator='\n', strip=True)
                        if t and len(t) > 20:
                            texts.append(t)
                            break

            if texts:
                combined = '\n'.join(texts)
                # Clean up common mbasic noise
                combined = re.sub(r'(Log In|Sign Up|Forgot password\?|Create new account).*$', '', combined, flags=re.I | re.S)
                combined = re.sub(r'\n{3,}', '\n\n', combined).strip()
                result["text"] = clean_text_content(combined)

            # Author name
            author_el = soup.find('strong') or soup.find('h3')
            if author_el:
                a_tag = author_el.find('a')
                if a_tag:
                    result["author_name"] = a_tag.get_text(strip=True)
                else:
                    result["author_name"] = author_el.get_text(strip=True)

            # Images from mbasic (lower res but still content)
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if 'scontent' in src and is_valid_fb_image(src):
                    clean_src = clean_cdn_url(src)
                    result["images"].append(clean_src)

        except Exception:
            pass

        return result

    def _fetch_oembed(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata via Facebook's oEmbed API endpoint.
        This can return author info and embedded HTML for some posts.
        """
        oembed_url = f"https://www.facebook.com/plugins/post/oembed.json/?url={urllib.parse.quote(url, safe='')}"
        try:
            resp = self.session.get(oembed_url, headers=HEADERS_DESKTOP, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

        # Try the video oembed endpoint too
        oembed_video_url = f"https://www.facebook.com/plugins/video/oembed.json/?url={urllib.parse.quote(url, safe='')}"
        try:
            resp = self.session.get(oembed_video_url, headers=HEADERS_DESKTOP, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

        return None

    def _fetch_from_archives(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to retrieve cached/archived version of the Facebook page from:
        1. Google Cache (webcache.googleusercontent.com)
        2. Wayback Machine (web.archive.org)
        """
        result = {"text": "", "images": [], "title": ""}

        # Try Google Cache
        try:
            google_cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{urllib.parse.quote(url, safe='')}"
            resp = self.session.get(google_cache_url, headers=HEADERS_DESKTOP, timeout=self.timeout)
            if resp.status_code == 200 and 'facebook.com' in resp.text.lower():
                self._parse_html_and_ssr(resp.text, {"text": "", "images": [], "title": "", "author": {"name": "", "url": "", "avatar": ""}, "videos": [], "raw_opengraph": {}})
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Extract text from Google's cached version
                og_desc = ""
                for tag in soup.find_all('meta'):
                    prop = tag.get('property', '') or tag.get('name', '')
                    if prop in ('og:description', 'description'):
                        og_desc = tag.get('content', '')
                        break
                if og_desc:
                    result["text"] = clean_text_content(og_desc)
                    return result
        except Exception:
            pass

        # Try Wayback Machine
        try:
            wb_api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url, safe='')}"
            resp = self.session.get(wb_api_url, timeout=8)
            if resp.status_code == 200:
                wb_data = resp.json()
                snapshots = wb_data.get("archived_snapshots", {})
                closest = snapshots.get("closest", {})
                if closest.get("available") and closest.get("url"):
                    archive_url = closest["url"]
                    archive_resp = self.session.get(archive_url, headers=HEADERS_DESKTOP, timeout=self.timeout)
                    if archive_resp.status_code == 200:
                        archive_html = archive_resp.text
                        # Parse the archived version
                        temp_result = {
                            "text": "", "images": [], "title": "",
                            "author": {"name": "", "url": "", "avatar": ""},
                            "videos": [], "raw_opengraph": {}
                        }
                        self._parse_html_and_ssr(archive_html, temp_result)
                        if temp_result.get("text"):
                            result["text"] = temp_result["text"]
                        if temp_result.get("title"):
                            result["title"] = temp_result["title"]
                        # Collect scontent images from archived version
                        scontent_matches = re.findall(r'https://scontent[^\s"\'<>\\]+', archive_html)
                        for match in scontent_matches:
                            c_url = clean_cdn_url(match)
                            if is_valid_fb_image(c_url):
                                result["images"].append(c_url)
                        if result["text"] or result["images"]:
                            return result
        except Exception:
            pass

        return None if not result["text"] and not result["images"] else result

    def _extract_with_cookies(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Use user-provided Facebook cookies to access private/locked content
        as an authenticated session.
        """
        if not self._auth_cookies:
            return None

        result = {"text": "", "images": [], "videos": [], "author_name": ""}

        try:
            # Build a session with the user's cookies
            auth_session = requests.Session()
            auth_session.headers.update(HEADERS_DESKTOP)
            for name, value in self._auth_cookies.items():
                auth_session.cookies.set(name, value, domain='.facebook.com')

            resp = auth_session.get(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code == 200:
                html_content = resp.text
                if not self._detect_login_wall(html_content):
                    temp_result = {
                        "text": "", "images": [], "title": "",
                        "author": {"name": "", "url": "", "avatar": ""},
                        "videos": [], "raw_opengraph": {}
                    }
                    self._parse_html_and_ssr(html_content, temp_result)
                    result["text"] = temp_result.get("text", "")
                    result["author_name"] = temp_result.get("author", {}).get("name", "")
                    for img in temp_result.get("images", []):
                        result["images"].append(img)
                    for vid in temp_result.get("videos", []):
                        result["videos"].append(vid)

            # If desktop was login-walled or empty, try mbasic with authenticated session
            if not result["text"] and not result["images"]:
                mbasic_url = _convert_to_mbasic_url(url)
                mresp = auth_session.get(mbasic_url, headers=HEADERS_MBASIC, timeout=self.timeout, allow_redirects=True)
                if mresp.status_code == 200 and not self._detect_login_wall(mresp.text):
                    soup = BeautifulSoup(mresp.text, 'html.parser')
                    post_divs = soup.find_all('div', {'data-ft': True})
                    texts = []
                    for div in post_divs:
                        paragraphs = div.find_all('p')
                        for p in paragraphs:
                            t = p.get_text(strip=True)
                            if t and len(t) > 3:
                                texts.append(t)
                    if not texts:
                        story_div = soup.find('div', class_=re.compile(r'(story_body|_5rgt|_2phc|bi|bj|bl)'))
                        if story_div:
                            t = story_div.get_text(separator='\n', strip=True)
                            if t:
                                texts.append(t)
                    if not texts:
                        for sel in ['article', '[role="article"]', '#m_story_permalink_view']:
                            container = soup.select_one(sel)
                            if container:
                                t = container.get_text(separator='\n', strip=True)
                                if t and len(t) > 10:
                                    texts.append(t)
                                    break
                    if texts:
                        combined = '\n'.join(texts)
                        combined = re.sub(r'(Log In|Sign Up|Forgot password\?|Create new account).*$', '', combined, flags=re.I | re.S)
                        result["text"] = clean_text_content(combined)

                    author_el = soup.find('strong') or soup.find('h3')
                    if author_el and not result["author_name"]:
                        a_tag = author_el.find('a')
                        result["author_name"] = a_tag.get_text(strip=True) if a_tag else author_el.get_text(strip=True)

                    for img in soup.find_all('img'):
                        src = img.get('src', '')
                        if src and 'scontent' in src and is_valid_fb_image(src):
                            clean_src = clean_cdn_url(src)
                            result["images"].append({
                                "url": clean_src,
                                "type": "photo",
                                "label": f"Image #{len(result['images']) + 1} (Auth)"
                            })

            auth_session.close()
            return result if (result["text"] or result["images"] or result["videos"]) else None

        except Exception:
            return None

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

        # If we have cookies, pass them to yt-dlp via cookiefile and http_headers
        cookie_file_path = None
        if self._auth_cookies:
            import tempfile
            try:
                cookie_lines = ["# Netscape HTTP Cookie File", "# Generated by OmniExtract", ""]
                for k, v in self._auth_cookies.items():
                    cookie_lines.append(f".facebook.com\tTRUE\t/\tTRUE\t2147483647\t{k}\t{v}")
                tf = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', prefix='fb_cookies_', delete=False)
                tf.write('\n'.join(cookie_lines))
                tf.close()
                cookie_file_path = tf.name
                ydl_opts['cookiefile'] = cookie_file_path
            except Exception:
                pass
            cookie_header = '; '.join(f'{k}={v}' for k, v in self._auth_cookies.items())
            ydl_opts['http_headers'] = {'Cookie': cookie_header}

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
                    if "yt-dlp" not in self._strategies_used:
                        self._strategies_used.append("yt-dlp")
        except Exception:
            pass
        finally:
            if cookie_file_path and os.path.exists(cookie_file_path):
                try:
                    os.remove(cookie_file_path)
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
