#!/usr/bin/env python3
"""
Launcher for Omni Extractor - Universal Video & Audio Downloader
Starts the FastAPI server and makes it accessible locally, over LAN, and globally via public tunnel.
"""

import os
import sys
import socket
import webbrowser
import threading
import time
import subprocess
import re
import requests
import uvicorn

def get_lan_ip():
    """Detect local network IP for cross-device access on Wi-Fi/LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def get_public_tunnel_url():
    """Check if an ngrok tunnel is currently running."""
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1.0)
        if resp.status_code == 200:
            data = resp.json()
            tunnels = data.get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    return t.get("public_url")
            if tunnels:
                return tunnels[0].get("public_url")
    except Exception:
        pass
    return None

def start_public_tunnel(port=8000, domain=None):
    """Start ngrok in background with optional permanent static domain."""
    existing_url = get_public_tunnel_url()
    if existing_url:
        return existing_url

    cmd = ["ngrok", "http", str(port)]
    target_domain = domain or os.getenv("NGROK_DOMAIN")
    if target_domain:
        cmd.extend(["--domain", target_domain])

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        for _ in range(12):
            time.sleep(0.5)
            url = get_public_tunnel_url()
            if url:
                return url
    except Exception as e:
        print(f"[!] Could not launch ngrok: {e}")
    return None

def start_cloudflared_tunnel(port=8000):
    """Start Cloudflare Quick Tunnel in background."""
    cloudflared_bin = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if not os.path.exists(cloudflared_bin):
        cloudflared_bin = "cloudflared"

    try:
        proc = subprocess.Popen(
            [cloudflared_bin, "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        for _ in range(25):
            line = proc.stdout.readline() if proc.stdout else ""
            if "trycloudflare.com" in line:
                m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if m:
                    return m.group(0)
            time.sleep(0.4)
    except Exception as e:
        print(f"[!] Could not launch cloudflared: {e}")
    return None

def open_browser(port=8000):
    """Open default web browser pointing to application."""
    time.sleep(1.2)
    url = f"http://localhost:{port}"
    print(f"\n[+] Opening Omni Extractor in your browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    for i, arg in enumerate(sys.argv):
        if arg in ("--port", "-p") and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass

    host = "0.0.0.0"
    lan_ip = get_lan_ip()

    enable_public = "--public" in sys.argv or "--share" in sys.argv or "--cloudflare" in sys.argv
    use_cf = "--cloudflare" in sys.argv or "--cloudflared" in sys.argv
    static_domain = None
    for i, arg in enumerate(sys.argv):
        if arg in ("--domain", "--static-domain") and i + 1 < len(sys.argv):
            static_domain = sys.argv[i + 1]
            enable_public = True

    public_url = None

    if enable_public:
        if use_cf:
            print("\n[*] Starting Cloudflare tunnel...")
            public_url = start_cloudflared_tunnel(port)
        else:
            print("\n[*] Starting public internet tunnel...")
            public_url = start_public_tunnel(port, domain=static_domain)
            if not public_url:
                print("[*] Falling back to Cloudflare tunnel...")
                public_url = start_cloudflared_tunnel(port)
    else:
        public_url = get_public_tunnel_url()

    print("=" * 68)
    print("   [+] Omni Extractor -- Universal Video & Audio Downloader")
    print("=" * 68)
    print(f"   [Local]   http://localhost:{port}")
    print(f"   [LAN]     http://{lan_ip}:{port}")
    if public_url:
        print(f"   [Public]  {public_url}")
    else:
        print(f"   [Public]  Run with '--public' or '--cloudflare' for global HTTPS URL")
    print("=" * 68)

    # Launch browser automatically if not in headless/CI
    if os.getenv("NO_BROWSER") != "1" and "--no-browser" not in sys.argv:
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start Uvicorn bound to 0.0.0.0 (with auto-reload for local changes)
    is_dev = os.getenv("ENV") != "production" and "--no-reload" not in sys.argv
    uvicorn.run("backend.server:app", host=host, port=port, reload=is_dev, log_level="info")

