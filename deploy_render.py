#!/usr/bin/env python3
"""
Automated Deploy & Sync Tool for Omni Extractor on Render
Stages changes, commits, pushes to GitHub origin main, and triggers instant Render deployment via API.

Usage:
  python deploy_render.py
  python deploy_render.py "Your commit message"
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error

# User Render credentials & services
RENDER_SERVICES = [
    {
        "name": "omniextract",
        "service_id": "srv-db78orm7bikc739udr00",
        "api_key": os.getenv("RENDER_API_KEY_1", "rnd_8xuO0ddHTcRcHzAyLt0PPhSx43pD"),
        "url": "https://omniextract-9h5t.onrender.com"
    },
    {
        "name": "omniextract-fb",
        "service_id": "srv-db7kqrfavr4c738k82n0",
        "api_key": os.getenv("RENDER_API_KEY_2", "rnd_ZCNZVFSx75IYygJKDFFkUTFP3yrz"),
        "url": "https://omniextract-fb.onrender.com"
    }
]

def run_git_cmd(args):
    """Run a git command and return stdout string."""
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[!] Git error ({' '.join(args)}):", e.stderr.strip())
        return None

def trigger_render_deploy(svc):
    """Trigger deployment via Render API."""
    url = f"https://api.render.com/v1/services/{svc['service_id']}/deploys"
    headers = {
        "Authorization": f"Bearer {svc['api_key']}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"clearCache": "do_not_clear"}).encode()
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data.get("id"), data.get("status")
    except Exception as e:
        print(f"[!] Failed to trigger deploy for {svc['name']}: {e}")
        return None, None

def check_deploy_status(svc, deploy_id):
    """Check the status of a specific deployment."""
    url = f"https://api.render.com/v1/services/{svc['service_id']}/deploys/{deploy_id}"
    headers = {"Authorization": f"Bearer {svc['api_key']}"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data.get("status")
    except Exception:
        return "unknown"

def main():
    commit_msg = "update: sync latest code and fixes to Render"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        commit_msg = sys.argv[1].strip()

    print("=" * 64)
    print("   [+] Omni Extractor -- Render Auto-Sync & Deployment Engine")
    print("=" * 64)

    # 1. Check git status
    status = run_git_cmd(["status", "--porcelain"])
    if status:
        print("\n[*] Detected local modifications:")
        for line in status.splitlines()[:10]:
            print("   ", line)
        print("\n[*] Staging and committing changes...")
        run_git_cmd(["add", "-A"])
        run_git_cmd(["commit", "-m", commit_msg])
        print(f"[+] Committed: \"{commit_msg}\"")
    else:
        print("\n[*] Working tree is clean (no uncommitted changes).")

    # 2. Push to GitHub
    print("\n[*] Pushing commits to GitHub (origin/main)...")
    push_out = run_git_cmd(["push", "origin", "main"])
    if push_out is not None:
        print("[+] Pushed successfully to GitHub!")
    else:
        print("[!] Warning: Could not push to origin main (or already up to date).")

    # 3. Trigger Render API Deployments
    print("\n[*] Triggering Render Cloud Deployments via API...")
    active_deploys = []
    for svc in RENDER_SERVICES:
        dep_id, status = trigger_render_deploy(svc)
        if dep_id:
            print(f"   -> {svc['name']}: Deploy started! (ID: {dep_id}, Status: {status})")
            active_deploys.append((svc, dep_id))
        else:
            print(f"   -> {svc['name']}: Render auto-deploy will trigger via GitHub webhook.")

    # 4. Monitor deploys until live
    if active_deploys:
        print("\n[*] Waiting for Render deployment to complete...")
        for svc, dep_id in active_deploys:
            print(f"   Monitoring {svc['name']}...", end=" ", flush=True)
            for attempt in range(24): # Wait up to ~2 minutes
                time.sleep(5)
                st = check_deploy_status(svc, dep_id)
                if st == "live":
                    print(f"LIVE! (Status: {st})")
                    break
                elif st in ["build_failed", "canceled", "deactivated"]:
                    print(f"FAILED ({st})")
                    break
                else:
                    print(".", end="", flush=True)
            else:
                print(" In progress (Render is finishing build in background).")

    print("\n" + "=" * 64)
    print("   [+] Deployment Complete! Public Live URLs:")
    for svc in RENDER_SERVICES:
        print(f"   [Public URL] {svc['url']}")
    print("=" * 64)

if __name__ == "__main__":
    main()
