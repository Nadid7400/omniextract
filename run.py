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
        # Give ngrok a moment to establish tunnel
        for _ in range(12):
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
    port = int(os.getenv("PORT", 8000))
    for i, arg in enumerate(sys.argv):
        if arg in ("--port", "-p") and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass

    host = "0.0.0.0"  # Allows access from any device on the network
    lan_ip = get_lan_ip()

    enable_public = "--public" in sys.argv or "--share" in sys.argv
    static_domain = None
    for i, arg in enumerate(sys.argv):
        if arg in ("--domain", "--static-domain") and i + 1 < len(sys.argv):
            static_domain = sys.argv[i + 1]
            enable_public = True

    public_url = None

    if enable_public:
        print("\n[*] Starting public internet tunnel...")
        public_url = start_public_tunnel(port, domain=static_domain)
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
        print(f"   [Public]  Run with '--public' or '--domain <your-domain>' for global URL")
    print("=" * 64)

    # Launch browser automatically
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Start Uvicorn bound to 0.0.0.0 for multi-device network reach
    uvicorn.run("backend.server:app", host=host, port=port, reload=False, log_level="info")
