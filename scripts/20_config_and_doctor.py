#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
20_config_and_doctor.py
-----------------------
Provides lightweight, autonomous configuration and diagnostics for RightSub:
1. `rightsub config`: Interactive or flag-driven API key manager with live connectivity checks (TMDb, Gemini).
2. `rightsub doctor`: System health dashboard inspecting Python, FFmpeg, TMDb, Gemini, Ollama, and Quicksubs.
"""

import os
import sys
import json
import shutil
import platform
import subprocess
import urllib.request
import urllib.error
import argparse
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "rightsub"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load configuration from ~/.config/rightsub/config.json if it exists."""
    if CONFIG_FILE.is_file():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(cfg: dict) -> None:
    """Save configuration dictionary to ~/.config/rightsub/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def mask_key(key: str) -> str:
    """Mask sensitive API key for display."""
    if not key:
        return "<Not Set>"
    key = str(key).strip()
    if len(key) <= 8:
        return "********"
    return f"{key[:4]}...{key[-4:]}"


def verify_tmdb(key: str) -> tuple:
    """Verify TMDb API key or v4 Bearer Token with a live request."""
    if not key:
        return False, "Key is empty"
    key = key.strip()
    is_bearer = key.startswith("ey") and len(key) > 50

    url = "https://api.themoviedb.org/3/configuration"
    if not is_bearer:
        url += f"?api_key={key}"

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    if is_bearer:
        req.add_header("Authorization", f"Bearer {key}")

    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            if resp.status == 200:
                return True, "Authenticated (HTTP 200 OK)"
            return False, f"HTTP Status {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"Authentication failed (HTTP {e.code})"
    except Exception as e:
        return False, f"Network error: {str(e)}"


def verify_gemini(key: str) -> tuple:
    """Verify Google Gemini API key with a live metadata/models check."""
    if not key:
        return False, "Key is empty"
    key = key.strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                flash_found = any("gemini-2.5-flash" in m or "gemini-1.5-flash" in m for m in models)
                detail = "Authenticated (gemini-flash verified)" if flash_found else "Authenticated"
                return True, detail
            return False, f"HTTP Status {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"Authentication failed (HTTP {e.code})"
    except Exception as e:
        return False, f"Network error: {str(e)}"


def handle_config(args):
    """Handle `rightsub config` command."""
    cfg = load_config()

    if getattr(args, "install_quicksubs", False):
        is_silicon = sys.platform == "darwin" and platform.machine() == "arm64"
        if not is_silicon:
            print("[-] quicksubs Apple SpeechAnalyzer requires an Apple Silicon Mac.")
            return 1
        print("[*] Installing quicksubs via Homebrew...")
        res = subprocess.run(["brew", "install", "mattbirchler/tap/quicksubs"])
        if res.returncode == 0:
            print("[✓] Quicksubs installed successfully!")
            return 0
        else:
            print(f"[!] brew install exited with code {res.returncode}. Manual install: brew tap mattbirchler/tap && brew install quicksubs")
            return res.returncode

    if getattr(args, "show", False):
        print("\n========================================================")
        print("          RightSub Current API Configuration            ")
        print("========================================================")
        print(f" Config file: {CONFIG_FILE}")
        gemini_k = cfg.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        tmdb_k = cfg.get("tmdb_api_key") or os.environ.get("TMDB_API_KEY") or os.environ.get("TMDB_READ_TOKEN")
        print(f" Google Gemini API Key: {mask_key(gemini_k)}")
        print(f" TMDb API Key / Token:  {mask_key(tmdb_k)}")
        print("========================================================\n")
        return 0

    if getattr(args, "clear", False):
        if CONFIG_FILE.is_file():
            CONFIG_FILE.unlink()
            print(f"[✓] Configuration file deleted: {CONFIG_FILE}")
        else:
            print("[i] No configuration file found to clear.")
        return 0

    # Non-interactive updates via flags
    modified = False
    if args.gemini:
        ok, msg = verify_gemini(args.gemini)
        if ok:
            cfg["gemini_api_key"] = args.gemini.strip()
            modified = True
            print(f"[✓] Gemini API Key verified: {msg}")
        else:
            print(f"[✗] Gemini API Key verification failed: {msg}")
            return 1

    if args.tmdb:
        ok, msg = verify_tmdb(args.tmdb)
        if ok:
            cfg["tmdb_api_key"] = args.tmdb.strip()
            modified = True
            print(f"[✓] TMDb API Key verified: {msg}")
        else:
            print(f"[✗] TMDb API Key verification failed: {msg}")
            return 1

    if modified:
        save_config(cfg)
        print(f"[✓] Saved configuration to {CONFIG_FILE}")
        return 0

    # Interactive Wizard Mode
    print("\n========================================================")
    print("          RightSub API Key Onboarding Wizard            ")
    print("========================================================")
    print("Configure your credentials once (Set and Forget).\n")

    current_gemini = cfg.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
    current_tmdb = cfg.get("tmdb_api_key") or os.environ.get("TMDB_API_KEY") or os.environ.get("TMDB_READ_TOKEN", "")

    # 1. Gemini
    print("1. Google Gemini API (Required for AI subtitle translation):")
    print("   Get your free key here: https://aistudio.google.com/app/apikey")
    prompt_gemini = f"   Enter Gemini API Key [{mask_key(current_gemini)}]: "
    try:
        entered_gemini = input(prompt_gemini).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return 1

    if entered_gemini:
        print("   Verifying Gemini API key...", end=" ", flush=True)
        ok, msg = verify_gemini(entered_gemini)
        if ok:
            print(f"[✓] {msg}")
            cfg["gemini_api_key"] = entered_gemini
        else:
            print(f"[✗] {msg}")
            print("   Key was not saved due to verification failure.")
    elif current_gemini:
        print("   Keeping existing Gemini API key.")

    print()

    # 2. TMDb
    print("2. TMDb API (Recommended for character names, overview & gender):")
    print("   Get your key/token here: https://www.themoviedb.org/settings/api")
    prompt_tmdb = f"   Enter TMDb Key or Token [{mask_key(current_tmdb)}]: "
    try:
        entered_tmdb = input(prompt_tmdb).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return 1

    if entered_tmdb:
        print("   Verifying TMDb credentials...", end=" ", flush=True)
        ok, msg = verify_tmdb(entered_tmdb)
        if ok:
            print(f"[✓] {msg}")
            cfg["tmdb_api_key"] = entered_tmdb
        else:
            print(f"[✗] {msg}")
            print("   Key was not saved due to verification failure.")
    elif current_tmdb:
        print("   Keeping existing TMDb credentials.")

    print()

    # 3. Quicksubs On-Device Speech-to-Text (Apple Silicon only)
    is_apple_silicon = sys.platform == "darwin" and platform.machine() == "arm64"
    has_brew = shutil.which("brew") is not None
    quicksubs_path = shutil.which("quicksubs")
    if is_apple_silicon and not quicksubs_path and has_brew:
        print("3. Quicksubs On-Device Speech-to-Text (Apple Silicon detected):")
        print("   Enables 100% free, local audio transcription directly on Apple Neural Engine.")
        print("   Official tap: mattbirchler/tap/quicksubs")
        prompt_qs = "   Would you like to install quicksubs now via Homebrew? [y/N]: "
        try:
            entered_qs = input(prompt_qs).strip().lower()
            if entered_qs in ("y", "yes"):
                print("   Installing quicksubs via Homebrew...", flush=True)
                res = subprocess.run(["brew", "install", "mattbirchler/tap/quicksubs"])
                if res.returncode == 0:
                    print("   [✓] Quicksubs installed successfully!")
                else:
                    print(f"   [!] Note: brew install exited with code {res.returncode}. Manual install: brew tap mattbirchler/tap && brew install quicksubs")
            else:
                print("   Skipped. You can install anytime via: brew tap mattbirchler/tap && brew install quicksubs")
        except (EOFError, KeyboardInterrupt):
            print("\nSkipped.")
        print()

    save_config(cfg)
    print("\n========================================================")
    print(f"[✓] Setup complete! Configuration saved to: {CONFIG_FILE}")
    print("    You can now run: rightsub auto \"Movie.mkv\"")
    print("========================================================\n")
    return 0


def handle_doctor(args):
    """Handle `rightsub doctor` diagnostic command."""
    print("\n========================================================")
    print("             RightSub System Health Doctor              ")
    print("========================================================")

    overall_ok = True

    # 1. Python Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 9)
    if py_ok:
        print(f" [✓] Python Runtime:  v{py_ver} ({sys.executable})")
    else:
        print(f" [✗] Python Runtime:  v{py_ver} (Requires Python 3.9+)")
        overall_ok = False

    # 2. FFmpeg & FFprobe
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if ffmpeg_path and ffprobe_path:
        print(f" [✓] FFmpeg Suite:    Installed ({ffmpeg_path})")
    elif ffmpeg_path:
        print(f" [!] FFmpeg Suite:    ffmpeg found, but ffprobe is missing")
    else:
        print(" [✗] FFmpeg Suite:    Missing from PATH (Required for video container operations)")
        print("     Fix: brew install ffmpeg  (or winget install Gyan.FFmpeg)")
        overall_ok = False

    # 3. Google Gemini API
    cfg = load_config()
    gemini_key = cfg.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        ok, msg = verify_gemini(gemini_key)
        if ok:
            print(f" [✓] Gemini API:      Ready — {mask_key(gemini_key)} ({msg})")
        else:
            print(f" [✗] Gemini API:      Error — {msg}")
            overall_ok = False
    else:
        print(" [!] Gemini API:      Not configured (Optional, required for AI subtitle translation)")
        print("     Setup: Run 'rightsub config' to configure.")

    # 4. TMDb API
    tmdb_key = cfg.get("tmdb_api_key") or os.environ.get("TMDB_API_KEY") or os.environ.get("TMDB_READ_TOKEN")
    if tmdb_key:
        ok, msg = verify_tmdb(tmdb_key)
        if ok:
            print(f" [✓] TMDb API:        Ready — {mask_key(tmdb_key)} ({msg})")
        else:
            print(f" [✗] TMDb API:        Error — {msg}")
            overall_ok = False
    else:
        print(" [!] TMDb API:        Not configured (Optional, recommended for character gender checks)")
        print("     Setup: Run 'rightsub config' to configure.")

    # 5. Ollama Local Daemon
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                print(f" [✓] Ollama Local AI: Running (Detected {len(models)} models)")
            else:
                print(" [i] Ollama Local AI: Daemon responding with non-200")
    except Exception:
        print(" [i] Ollama Local AI: Offline (Not running, cloud Gemini fallback available)")

    # 6. Quicksubs / Apple Silicon Speech-to-Text
    quicksubs_path = shutil.which("quicksubs")
    is_apple_silicon = sys.platform == "darwin" and platform.machine() == "arm64"
    if quicksubs_path:
        print(f" [✓] Quicksubs STT:   Installed ({quicksubs_path}) — Apple Neural Engine ready")
    elif is_apple_silicon:
        print(" [i] Quicksubs STT:   Not installed (Recommended on Apple Silicon for 0-cost audio transcription)")
        print("     Installation:    brew tap mattbirchler/tap && brew install quicksubs")
    else:
        print(" [i] Quicksubs STT:   Not installed (Optional speech-to-text engine)")

    print("========================================================")
    if overall_ok:
        print(" [✓] RightSub is healthy and ready for media automation!")
    else:
        print(" [!] Some recommended components require attention.")
    print("========================================================\n")
    return 0 if overall_ok else 1


def main():
    parser = argparse.ArgumentParser(description="RightSub Configuration & System Diagnostics")
    subparsers = parser.add_subparsers(dest="command")

    # config sub-command
    config_parser = subparsers.add_parser("config", help="Interactive API key onboarding and credentials manager")
    config_parser.add_argument("--gemini", help="Directly set Google Gemini API Key")
    config_parser.add_argument("--tmdb", help="Directly set TMDb API Key or Bearer Token")
    config_parser.add_argument("--show", action="store_true", help="Display current configuration status")
    config_parser.add_argument("--clear", action="store_true", help="Delete configuration file")
    config_parser.add_argument("--install-quicksubs", action="store_true", help="Install quicksubs via Homebrew on Apple Silicon")

    # doctor sub-command
    doctor_parser = subparsers.add_parser("doctor", help="Run comprehensive health check on dependencies and services")

    args = parser.parse_args()
    if args.command == "doctor":
        sys.exit(handle_doctor(args))
    else:
        sys.exit(handle_config(args))


if __name__ == "__main__":
    main()
