#!/usr/bin/env python3
"""
Launcher for OmniExtract Facebook
Starts the FastAPI server and makes it accessible locally, over LAN, and globally via public tunnel.
"""

import os
import sys
import socket
import webbrowser
import threading
import time
import subprocess
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

def start_public_tunnel(port=8000):
    """Start ngrok in background if requested and not already running."""
    existing_url = get_public_tunnel_url()
    if existing_url:
        return existing_url

    try:
        subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        # Give ngrok a moment to establish tunnel
        for _ in range(10):
            time.sleep(0.5)
            url = get_public_tunnel_url()
            if url:
                return url
    except Exception as e:
        print(f"[!] Could not automatically launch ngrok: {e}")
    return None

def open_browser(port=8000):
    time.sleep(1.2)
    url = f"http://localhost:{port}"
    print(f"\n[+] Opening OmniExtract in your browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    port = 8000
    host = "0.0.0.0"  # Allows access from any device on the network
    lan_ip = get_lan_ip()

    enable_public = "--public" in sys.argv or "--share" in sys.argv
    public_url = None

    if enable_public:
        print("\n[*] Starting public internet tunnel via ngrok...")
        public_url = start_public_tunnel(port)
    else:
        public_url = get_public_tunnel_url()

    print("=" * 64)
    print("   [+] OmniExtract -- Universal Facebook Extractor (Liquid Glass)")
    print("=" * 64)
    print(f"   [Local]   http://localhost:{port}")
    print(f"   [LAN]     http://{lan_ip}:{port}")
    if public_url:
        print(f"   [Public]  {public_url}")
    else:
        print(f"   [Public]  Run with --public or run 'ngrok http {port}'")
    print("=" * 64)

    # Launch browser automatically
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start Uvicorn bound to 0.0.0.0 for multi-device network reach
    uvicorn.run("backend.server:app", host=host, port=port, reload=False, log_level="info")
