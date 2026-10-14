import requests
from PIL import Image
import io
import re

from backend.fb_extractor import FacebookExtractor, clean_cdn_url, upgrade_to_full_resolution

ext = FacebookExtractor()
for test_url in ['https://www.facebook.com/profile.php?id=61591690491229', 'https://www.facebook.com/zuck']:
    res = ext.extract(test_url)
    print(f"\n==========================================")
    print(f"Results for: {test_url}")
    print(f"Name: {res.get('title')}")
    print(f"Total Images: {len(res.get('images', []))}")
    
    for idx, img in enumerate(res.get('images', [])):
        orig = img.get('url', '')
        upg = upgrade_to_full_resolution(orig)
        headers = {'User-Agent': 'Mozilla/5.0'}
        dim = "N/A"
        try:
            r = requests.get(upg, headers=headers, timeout=10)
            if r.status_code == 200:
                im = Image.open(io.BytesIO(r.content))
                dim = f"{im.size[0]}x{im.size[1]}"
            else:
                dim = f"HTTP {r.status_code}"
        except Exception as e:
            dim = f"Error: {e}"
        print(f"[{idx+1}] {dim:12s} | Type: {img.get('type', 'img'):15s} | URL: {upg[:70]}...")
