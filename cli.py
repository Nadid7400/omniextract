#!/usr/bin/env python3
"""
Command-Line Interface for Facebook Anything Extractor
Supports Single URL Extraction & Batch Extraction (e.g. Novels/Series with 90+ parts)

Usage:
    python cli.py <facebook_url>
    python cli.py <facebook_url> --download
    python cli.py --batch-file urls.txt --compile-txt complete_story.txt
    python cli.py --batch-text "1.https://... 2.https://..." --compile-txt story.txt
"""

import sys
import os
import argparse
import json
import re
import requests
from backend.fb_extractor import FacebookExtractor, HEADERS, extract_all_facebook_urls, normalize_fb_url

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\.]', '_', name)

def download_file(url: str, filepath: str):
    headers = dict(HEADERS)
    headers["Referer"] = "https://www.facebook.com/"
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=30)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception as e:
        print(f"  [!] Failed to download {url}: {e}")
    return False

def main():
    parser = argparse.ArgumentParser(
        description="Extract anything (post texts, images, videos, full series/novels) from public Facebook URLs without login."
    )
    parser.add_argument("url", nargs="?", default=None, help="Facebook link (post, reel, photo, video, share link)")
    parser.add_argument("--batch-file", "-bf", help="Path to text file containing multiple Facebook links")
    parser.add_argument("--batch-text", "-bt", help="Raw string/list containing multiple Facebook links")
    parser.add_argument("--cookies", help="Facebook session cookies (e.g. 'c_user=...; xs=...') to extract locked/private posts")
    parser.add_argument("--cookie-file", help="Path to Netscape cookies.txt or JSON file for authenticated extraction")
    parser.add_argument("--compile-txt", "-c", help="Filepath to compile all extracted chapters/text into a single .txt file")
    parser.add_argument("--json", action="store_true", help="Print raw extraction result as JSON")
    parser.add_argument("--download", "-d", action="store_true", help="Automatically download media to output folder")
    parser.add_argument("--output-dir", "-o", default="./extracted_fb_media", help="Output directory for downloaded media")

    args = parser.parse_args()
    extractor = FacebookExtractor()

    # Configure session cookies if provided
    if args.cookie_file and os.path.exists(args.cookie_file):
        with open(args.cookie_file, "r", encoding="utf-8") as cf:
            extractor.set_cookies(cf.read())
            print("[*] Loaded authenticated cookies from file.")
    elif args.cookies:
        extractor.set_cookies(args.cookies)
        print("[*] Loaded authenticated session cookies.")

    # BATCH EXTRACTION MODE
    raw_batch_content = ""
    if args.batch_file and os.path.exists(args.batch_file):
        with open(args.batch_file, "r", encoding="utf-8") as f:
            raw_batch_content = f.read()
    elif args.batch_text:
        raw_batch_content = args.batch_text
    elif args.url and len(extract_all_facebook_urls(args.url)) > 1:
        raw_batch_content = args.url

    if raw_batch_content:
        urls = extract_all_facebook_urls(raw_batch_content)
        print(f"[*] Batch Mode: Found {len(urls)} Facebook URLs to extract.")
        compiled_sections = []
        total_words = 0

        out_dir = os.path.abspath(args.output_dir)
        if args.download:
            os.makedirs(out_dir, exist_ok=True)

        for idx, u in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] Extracting: {u} ...", end=" ", flush=True)
            try:
                res = extractor.extract(u)
                text = res.get("text", "")
                title = res.get("title") or f"Part {idx}"
                words = len(text.split()) if text else 0
                total_words += words
                print(f"OK ({len(text)} chars, {words} words)")

                header = f"\n{'='*60}\nPart {idx}: {title}\nURL: {res.get('url')}\n{'='*60}\n\n"
                compiled_sections.append(header + (text or "[No text found]") + "\n\n")

                if args.download and text:
                    ch_file = os.path.join(out_dir, f"part_{idx:02d}.txt")
                    with open(ch_file, "w", encoding="utf-8") as cf:
                        cf.write(header + text)

            except Exception as e:
                print(f"FAILED: {e}")

        # Save compiled story
        compile_path = args.compile_txt or (os.path.join(out_dir, "Complete_Series.txt") if args.download else None)
        if compile_path:
            with open(compile_path, "w", encoding="utf-8") as cf:
                cf.write(f"FACEBOOK SERIES COMPILATION ({len(urls)} Parts, {total_words} Words)\n\n")
                cf.write("".join(compiled_sections))
            print(f"\n[OK] Compiled full story saved to: {compile_path}")

        print(f"\n[OK] Batch extraction complete: {len(urls)} parts processed, {total_words} total words.")
        return

    # SINGLE EXTRACTION MODE
    if not args.url:
        parser.print_help()
        sys.exit(1)

    clean_url = normalize_fb_url(args.url)
    print(f"[*] Extracting Facebook content from: {clean_url}")
    data = extractor.extract(clean_url)

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not data.get("success"):
        print(f"[x] Error: {data.get('error', 'Unknown extraction failure')}")
        sys.exit(1)

    print("\n" + "="*50)
    print(f"Type:       {data.get('type', 'post').upper()}")
    print(f"Author:     {data.get('author', {}).get('name') or 'Unknown'}")
    if data.get("uid") or (data.get("author") and data["author"].get("uid")):
        print(f"UID:        {data.get('uid') or data['author'].get('uid')}")
    print(f"Title:      {data.get('title') or 'N/A'}")
    print(f"Resolved:   {data.get('url')}")
    print("="*50)

    # Post Text
    post_text = data.get("text", "")
    if post_text:
        words = len(post_text.split())
        print(f"\n--- [POST TEXT ({len(post_text)} characters, {words} words)] ---")
        try:
            print(post_text[:1200] + ("\n... [truncated in terminal preview]" if len(post_text) > 1200 else ""))
        except UnicodeEncodeError:
            # Fallback for Windows CP1252 consoles
            print(post_text[:1200].encode('ascii', 'replace').decode('ascii'))
    else:
        print("\n[i] No standalone post text detected.")

    # Images
    images = data.get("images", [])
    print(f"\n--- [IMAGES FOUND: {len(images)}] ---")
    for idx, img in enumerate(images, 1):
        print(f" {idx}. {img.get('label', 'Image')}: {img.get('url')}")

    # Videos
    videos = data.get("videos", [])
    print(f"\n--- [VIDEOS FOUND: {len(videos)}] ---")
    for idx, vid in enumerate(videos, 1):
        quality = vid.get("quality", "Standard")
        fmt = vid.get("format", "mp4")
        print(f" {idx}. [{quality}] ({fmt}): {vid.get('url')}")

    # Download handling
    if args.download:
        out_dir = os.path.abspath(args.output_dir)
        os.makedirs(out_dir, exist_ok=True)
        print(f"\n[*] Downloading content to: {out_dir}")

        if post_text:
            text_file = os.path.join(out_dir, "post_text.txt")
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(f"URL: {data.get('url')}\n")
                f.write(f"Author: {data.get('author', {}).get('name')}\n")
                f.write(f"Title: {data.get('title')}\n\n")
                f.write(post_text)
            print("  [+] Saved post_text.txt")

        meta_file = os.path.join(out_dir, "metadata.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("  [+] Saved metadata.json")

        for idx, img in enumerate(images, 1):
            filename = f"image_{idx:02d}.jpg"
            filepath = os.path.join(out_dir, filename)
            if download_file(img["url"], filepath):
                print(f"  [+] Saved {filename}")

        if videos:
            top_video = videos[0]
            filename = "video.mp4"
            filepath = os.path.join(out_dir, filename)
            if download_file(top_video["url"], filepath):
                print(f"  [+] Saved {filename}")

        print(f"\n[OK] All assets saved to: {out_dir}")

if __name__ == "__main__":
    main()
