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
HOOKS_DIR = CONFIG_DIR / "hooks"
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def install_downloader_hooks(
    hooks_dir: Path = None,
    sonarr_url: str = None,
    sonarr_key: str = None,
    radarr_url: str = None,
    radarr_key: str = None
) -> dict:
    """
    Generates ready-to-run downloader completion hook scripts (qBittorrent, Transmission)
    in ~/.config/rightsub/hooks/ using exact absolute paths to Python and rightsub.py,
    and optionally registers the RightSub Webhook with local Sonarr/Radarr APIs.
    """
    target_dir = Path(hooks_dir) if hooks_dir else HOOKS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    python_exe = str(Path(sys.executable).resolve())
    rightsub_py = str((REPO_ROOT / "rightsub.py").resolve())

    # 1. qBittorrent POSIX script
    qbit_sh = target_dir / "qbittorrent_hook.sh"
    qbit_sh_content = (
        "#!/usr/bin/env bash\n"
        "# RightSub qBittorrent Completion Hook (Seed-Safe)\n"
        "# Usage in qBittorrent -> Options -> Downloads -> Run external program on torrent completion:\n"
        f"#   \"{qbit_sh}\" \"%F\"\n"
        "TARGET_PATH=\"$1\"\n"
        "if [ -z \"$TARGET_PATH\" ]; then exit 0; fi\n"
        f"\"{python_exe}\" \"{rightsub_py}\" auto \"$TARGET_PATH\"\n"
    )
    qbit_sh.write_text(qbit_sh_content, encoding="utf-8")
    try:
        qbit_sh.chmod(0o755)
    except Exception:
        pass

    # 2. qBittorrent Windows batch script
    qbit_bat = target_dir / "qbittorrent_hook.bat"
    qbit_bat_content = (
        "@echo off\r\n"
        ":: RightSub qBittorrent Completion Hook (Windows Seed-Safe)\r\n"
        ":: Usage in qBittorrent: \"" + str(qbit_bat) + "\" \"%F\"\r\n"
        "chcp 65001 >nul 2>&1\r\n"
        "if \"%~1\"==\"\" exit /b 0\r\n"
        f"\"{python_exe}\" \"{rightsub_py}\" auto \"%~1\"\r\n"
    )
    qbit_bat.write_text(qbit_bat_content, encoding="utf-8")

    # 3. Transmission completion script
    trans_sh = target_dir / "transmission_hook.sh"
    trans_sh_content = (
        "#!/usr/bin/env bash\n"
        "# RightSub Transmission Completion Hook (Seed-Safe)\n"
        "TARGET_PATH=\"${TR_TORRENT_DIR}/${TR_TORRENT_NAME}\"\n"
        "if [ -z \"$TR_TORRENT_NAME\" ]; then exit 0; fi\n"
        f"\"{python_exe}\" \"{rightsub_py}\" auto \"$TARGET_PATH\"\n"
    )
    trans_sh.write_text(trans_sh_content, encoding="utf-8")
    try:
        trans_sh.chmod(0o755)
    except Exception:
        pass

    api_registrations = []
    for svc_name, base_url, api_key, endpoint in [
        ("Sonarr", sonarr_url, sonarr_key, "http://localhost:8775/webhook/sonarr"),
        ("Radarr", radarr_url, radarr_key, "http://localhost:8775/webhook/radarr"),
    ]:
        if base_url and api_key:
            try:
                notif_url = f"{base_url.rstrip('/')}/api/v3/notification"
                payload = {
                    "name": "RightSub Seed-Safe Subtitle Mastering",
                    "implementation": "Webhook",
                    "configContract": "WebhookSettings",
                    "onDownload": True,
                    "onUpgrade": True,
                    "onRename": True,
                    "fields": [
                        {"name": "url", "value": endpoint},
                        {"name": "method", "value": 1}
                    ],
                    "tags": []
                }
                req = urllib.request.Request(
                    notif_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "X-Api-Key": api_key.strip()},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=7) as resp:
                    api_registrations.append({"service": svc_name, "success": resp.status in (200, 201)})
            except Exception as e:
                api_registrations.append({"service": svc_name, "success": False, "error": str(e)})

    qbit_cmd = f'"{qbit_bat}" "%F"' if sys.platform == "win32" else f'"{qbit_sh}" "%F"'
    return {
        "hooks_dir": str(target_dir),
        "qbittorrent_script": str(qbit_bat if sys.platform == "win32" else qbit_sh),
        "qbittorrent_command": qbit_cmd,
        "transmission_script": str(trans_sh),
        "webhook_urls": {
            "sonarr": "http://localhost:8775/webhook/sonarr",
            "radarr": "http://localhost:8775/webhook/radarr",
            "bazarr": "http://localhost:8775/webhook/bazarr",
        },
        "api_registrations": api_registrations
    }


def install_background_service(service_dir: Path = None, port: int = 8775) -> dict:
    """
    Generates a user-level background service definition (macOS launchd plist,
    Linux systemd --user unit, or Windows startup batch + schtasks command)
    to run `rightsub serve --seed-safe` automatically.
    """
    python_exe = str(Path(sys.executable).resolve())
    rightsub_py = str((REPO_ROOT / "rightsub.py").resolve())

    if sys.platform == "darwin":
        target_dir = Path(service_dir) if service_dir else (Path.home() / "Library" / "LaunchAgents")
        target_dir.mkdir(parents=True, exist_ok=True)
        plist_path = target_dir / "com.rightsub.webhook.plist"
        log_path = CONFIG_DIR / "webhook.log"
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rightsub.webhook</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{rightsub_py}</string>
        <string>serve</string>
        <string>--port</string>
        <string>{port}</string>
        <string>--seed-safe</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
</dict>
</plist>
"""
        plist_path.write_text(plist_content, encoding="utf-8")
        return {
            "platform": "darwin",
            "service_file": str(plist_path),
            "activate_cmd": f"launchctl load -w \"{plist_path}\""
        }
    elif sys.platform == "win32":
        target_dir = Path(service_dir) if service_dir else HOOKS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        bat_path = target_dir / "start_webhook_daemon.bat"
        bat_content = (
            "@echo off\r\n"
            f"\"{python_exe}\" \"{rightsub_py}\" serve --port {port} --seed-safe\r\n"
        )
        bat_path.write_text(bat_content, encoding="utf-8")
        return {
            "platform": "win32",
            "service_file": str(bat_path),
            "activate_cmd": f'schtasks /Create /SC ONLOGON /TN "RightSubWebhook" /TR "\\"{bat_path}\\"" /F'
        }
    else:
        target_dir = Path(service_dir) if service_dir else (Path.home() / ".config" / "systemd" / "user")
        target_dir.mkdir(parents=True, exist_ok=True)
        unit_path = target_dir / "rightsub-webhook.service"
        unit_content = f"""[Unit]
Description=RightSub Native Webhook Daemon (Sonarr/Radarr/Bazarr)
After=network.target

[Service]
Type=simple
ExecStart="{python_exe}" "{rightsub_py}" serve --port {port} --seed-safe
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""
        unit_path.write_text(unit_content, encoding="utf-8")
        return {
            "platform": "linux",
            "service_file": str(unit_path),
            "activate_cmd": "systemctl --user daemon-reload && systemctl --user enable --now rightsub-webhook.service"
        }


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
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "x-goog-api-key": key, "User-Agent": "RightSub/1.3"}
    )
    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                flash_found = any("flash" in m.lower() for m in models)
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

    if getattr(args, "install_hooks", False) is True:
        res = install_downloader_hooks()
        print("\n========================================================")
        print("       RightSub Downloader Hooks & Webhooks Ready       ")
        print("========================================================")
        print(f" [✓] Hook scripts generated in: {res['hooks_dir']}")
        print(f" [✓] qBittorrent completion command (Copy & Paste):")
        print(f"     {res['qbittorrent_command']}")
        print(f" [✓] Transmission completion script:")
        print(f"     {res['transmission_script']}")
        print("\n [i] Native Webhook Endpoints (when running `rightsub serve`):")
        print(f"     Sonarr : {res['webhook_urls']['sonarr']}")
        print(f"     Radarr : {res['webhook_urls']['radarr']}")
        print(f"     Bazarr : {res['webhook_urls']['bazarr']}")
        print("========================================================\n")
        if getattr(args, "install_service", False) is not True:
            return 0

    if getattr(args, "install_service", False) is True:
        svc = install_background_service()
        print("\n========================================================")
        print("       RightSub Background Webhook Service Generated    ")
        print("========================================================")
        print(f" [✓] Service file created: {svc['service_file']}")
        print(f" [i] To activate automatic startup in background, run:")
        print(f"     {svc['activate_cmd']}")
        print("========================================================\n")
        return 0

    if getattr(args, "install_quicksubs", False) is True:
        is_silicon = sys.platform == "darwin" and platform.machine() == "arm64"
        if not is_silicon:
            print("[-] quicksubs Apple SpeechAnalyzer requires an Apple Silicon Mac.")
            return 1
        macos_major = 0
        if sys.platform == "darwin":
            try:
                macos_major = int(platform.mac_ver()[0].split(".")[0])
            except Exception:
                pass
        if macos_major < 26:
            print(f"[-] quicksubs requires macOS 26+ Tahoe (Detected macOS {platform.mac_ver()[0]}).")
            print("    For local GPU-accelerated STT on this system, install whisper-cpp:")
            print("    brew install whisper-cpp")
            return 1
        print("[*] Trusting tap and installing quicksubs via Homebrew...")
        subprocess.run(["brew", "trust", "mattbirchler/tap"], check=False)
        res = subprocess.run(["brew", "install", "mattbirchler/tap/quicksubs"])
        if res.returncode == 0:
            print("[✓] Quicksubs installed successfully!")
            return 0
        else:
            print(f"[!] brew install exited with code {res.returncode}. Manual install: brew trust mattbirchler/tap && brew install mattbirchler/tap/quicksubs")
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

    # 3. Quicksubs On-Device Speech-to-Text (Apple Silicon on macOS 26+ only)
    is_apple_silicon = sys.platform == "darwin" and platform.machine() == "arm64"
    macos_major = 0
    if sys.platform == "darwin":
        try:
            macos_major = int(platform.mac_ver()[0].split(".")[0])
        except Exception:
            pass

    has_brew = shutil.which("brew") is not None
    quicksubs_path = shutil.which("quicksubs")
    if is_apple_silicon and not quicksubs_path and has_brew and macos_major >= 26:
        print("3. Quicksubs On-Device Speech-to-Text (Apple Silicon on macOS 26+ detected):")
        print("   Enables 100% free, local source audio transcription (English/Western) via Neural Engine.")
        print("   Note: Apple engine does not support Hebrew audio; use for English source or audio-sync.")
        print("   Official tap: mattbirchler/tap/quicksubs")
        prompt_qs = "   Would you like to trust and install quicksubs now via Homebrew? [y/N]: "
        try:
            entered_qs = input(prompt_qs).strip().lower()
            if entered_qs in ("y", "yes"):
                print("   Trusting and installing quicksubs via Homebrew...", flush=True)
                subprocess.run(["brew", "trust", "mattbirchler/tap"], check=False)
                res = subprocess.run(["brew", "install", "mattbirchler/tap/quicksubs"])
                if res.returncode == 0:
                    print("   [✓] Quicksubs installed successfully!")
                else:
                    print(f"   [!] Note: brew install exited with code {res.returncode}.")
            else:
                print("   Skipped.")
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
    macos_major = 0
    if sys.platform == "darwin":
        try:
            macos_major = int(platform.mac_ver()[0].split(".")[0])
        except Exception:
            pass

    if quicksubs_path:
        print(f" [✓] Quicksubs STT:   Installed ({quicksubs_path}) — Apple Neural Engine ready")
        print("     Scope:           Source audio (English/Western). Hebrew audio STT not supported by Apple.")
    elif is_apple_silicon and macos_major >= 26:
        print(" [i] Quicksubs STT:   Not installed (Recommended on Apple Silicon for 0-cost source audio STT)")
        print("     Installation:    brew trust mattbirchler/tap && brew install mattbirchler/tap/quicksubs")
        print("     Scope:           Source audio only (English, etc.). Hebrew audio STT requires whisper-cpp.")
    elif is_apple_silicon and macos_major < 26:
        print(" [i] Quicksubs STT:   Requires macOS 26+ Tahoe (For local STT on this OS: brew install whisper-cpp)")
    else:
        print(" [i] Quicksubs STT:   Not installed (Optional speech-to-text engine)")

    # 7. MCP Agent Integrations
    try:
        import importlib
        m23 = importlib.import_module("23_mcp_server")
        statuses = m23.get_mcp_registration_status()
        reg_agents = [s["agent"] for s in statuses if s["registered"]]
        if reg_agents:
            print(f" [✓] MCP AI Agents:   Registered in {', '.join(reg_agents)}")
        else:
            print(" [i] MCP AI Agents:   Not registered yet (Run 'rightsub mcp --install' to connect AI agents)")
    except Exception:
        pass

    print("========================================================")
    if overall_ok:
        print(" [✓] RightSub is healthy and ready for media automation!")
    else:
        print(" [!] Some recommended components require attention.")
    print("========================================================\n")
    return 0 if overall_ok else 1


def handle_setup(args, input_fn=input):
    """
    Unified End-to-End Setup & Integration Wizard (`rightsub setup`).
    Walks the user through:
    1. Environment & Dependency Diagnostics (`doctor`)
    2. Downloader Hooks & Background Service generation (`--install-hooks` / `--install-service`)
    3. Local MCP Server registration across AI Agents (`rightsub mcp --install`)
    4. Optional API Key configuration (`TMDb` / `Gemini`)
    """
    print("\n==================================================================")
    print("       RightSub — Environment Setup & Integration Wizard          ")
    print("==================================================================")

    # Step 1: Doctor check
    handle_doctor(args)

    # Step 2: Downloader Hooks
    hooks_res = install_downloader_hooks()
    print(f" [✓] Downloader Hooks created in: {hooks_res['hooks_dir']}")
    print(f"     qBittorrent Command: {hooks_res['qbittorrent_command']}")

    # Step 3: Background Service
    svc_res = install_background_service()
    print(f" [✓] Background Webhook Service file ready: {svc_res['service_file']}")

    # Step 4: MCP Auto-Registration across AI Agents
    try:
        import importlib
        m23 = importlib.import_module("23_mcp_server")
        mcp_res = m23.install_mcp_for_agents(target_agent="all")
        for item in mcp_res.get("results", []):
            icon = "[✓]" if item["success"] else "[i]"
            print(f" {icon} MCP Agent [{item['agent']}]: {item['message']}")
    except Exception as e:
        print(f" [!] MCP registration note: {e}")

    if not getattr(args, "non_interactive", False) and sys.stdin.isatty():
        try:
            ans = input_fn("\n [?] Would you like to configure optional API keys (TMDb / Gemini) now? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            ans = "n"
        if ans in ("y", "yes"):
            handle_config(argparse.Namespace(
                install_quicksubs=False,
                install_hooks=False,
                install_service=False,
                show=False,
                clear=False,
                gemini=None,
                tmdb=None
            ))

    print("\n==================================================================")
    print(" [✓] RightSub Setup Wizard Complete!")
    print("     - Run `rightsub` (no arguments) for the Interactive Wizard")
    print("     - Run `rightsub auto \"Movie.mkv\"` for instant processing")
    print("     - Your AI agents can now control RightSub via MCP!")
    print("==================================================================\n")
    return 0


def main():
    parser = argparse.ArgumentParser(description="RightSub Configuration, Setup & System Diagnostics")
    subparsers = parser.add_subparsers(dest="command")

    # config sub-command
    config_parser = subparsers.add_parser("config", help="Interactive API key onboarding, hooks & service manager")
    config_parser.add_argument("--gemini", help="Directly set Google Gemini API Key")
    config_parser.add_argument("--tmdb", help="Directly set TMDb API Key or Bearer Token")
    config_parser.add_argument("--show", action="store_true", help="Display current configuration status")
    config_parser.add_argument("--clear", action="store_true", help="Delete configuration file")
    config_parser.add_argument("--install-quicksubs", action="store_true", help="Install quicksubs via Homebrew on Apple Silicon")
    config_parser.add_argument("--install-hooks", action="store_true", help="Generate qBittorrent/Transmission completion hooks and Sonarr/Radarr webhook endpoints")
    config_parser.add_argument("--install-service", action="store_true", help="Generate launchd/systemd/Windows startup service for RightSub Webhook daemon")

    # doctor sub-command
    doctor_parser = subparsers.add_parser("doctor", help="Run comprehensive health check on dependencies and services")

    # setup sub-command
    setup_parser = subparsers.add_parser("setup", help="Run end-to-end Setup, Hooks & MCP Integration Wizard")
    setup_parser.add_argument("--non-interactive", action="store_true", help="Run setup without interactive prompts")

    args = parser.parse_args()
    if args.command == "doctor":
        sys.exit(handle_doctor(args))
    elif args.command == "setup":
        sys.exit(handle_setup(args))
    else:
        sys.exit(handle_config(args))


if __name__ == "__main__":
    main()
