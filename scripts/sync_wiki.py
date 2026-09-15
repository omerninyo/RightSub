#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_wiki.py
------------
Synchronizes the local bilingual wiki/ directory with the GitHub Wiki repository
(https://github.com/<owner>/<repo>.wiki.git).
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WIKI_DIR = BASE_DIR / "wiki"

def sync_wiki(repo_url=None):
    if not WIKI_DIR.exists():
        print(f"[-] Wiki source directory not found at: {WIKI_DIR}")
        return False

    if not repo_url:
        # Detect remote from git config
        res = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, cwd=BASE_DIR)
        origin_url = res.stdout.strip()
        if not origin_url:
            print("[-] Could not determine remote.origin.url")
            return False
        
        # Convert https://github.com/owner/repo.git to https://github.com/owner/repo.wiki.git
        if origin_url.endswith(".git"):
            repo_url = origin_url[:-4] + ".wiki.git"
        else:
            repo_url = origin_url + ".wiki.git"

    print(f"[*] Target GitHub Wiki repository: {repo_url}")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "wiki_clone"
        
        # 1. Try to clone existing wiki
        clone_res = subprocess.run(["git", "clone", repo_url, str(tmp_path)], capture_output=True, text=True)
        if clone_res.returncode != 0:
            print("[!] Note: Remote wiki clone returned non-zero (wiki may not be enabled yet on GitHub):")
            print(f"    {clone_res.stderr.strip()}")
            print("[*] Initializing fresh local wiki git repository...")
            tmp_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-b", "master"], cwd=tmp_path, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=tmp_path, check=True)
        
        # 2. Copy all files from wiki/
        for item in WIKI_DIR.iterdir():
            if item.name.startswith("."):
                continue
            dest = tmp_path / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)

        # 3. Add, commit, and push
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=tmp_path)
        if not status_res.stdout.strip():
            print("[✓] Wiki is already up to date with remote.")
            return True
        
        subprocess.run(["git", "commit", "-m", "docs: sync bilingual documentation from repository wiki/"], cwd=tmp_path, check=True)
        push_res = subprocess.run(["git", "push", "-u", "origin", "HEAD"], capture_output=True, text=True, cwd=tmp_path)
        if push_res.returncode == 0:
            print("[✓] SUCCESS: GitHub Wiki updated successfully!")
            return True
        else:
            print(f"[!] Push to GitHub Wiki failed (GitHub requires Wiki to be active/public on Free plans):")
            print(f"    {push_res.stderr.strip()}")
            return False

if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    success = sync_wiki(url_arg)
    sys.exit(0 if success else 1)
