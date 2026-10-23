#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
22_interactive_wizard.py
------------------------
Interactive Terminal & Windows Command Prompt Mastering Wizard for RightSub (RFC 001).
Provides a zero-flag, linear bilingual menu experience when running `rightsub` with no arguments
or `rightsub wizard`.

Features:
1. Cross-Platform Drag & Drop Path Normalization (`normalize_dragged_path`):
   Handles macOS Finder backslash escapes (`\\ `, `\\(`, `\\)`), Windows Explorer double quotes,
   and PowerShell `& '...'` call prefixes.
2. Built-in Terminal File Explorer (`interactive_file_browser`):
   Allows navigating season folders and selecting a whole directory or a specific episode/subtitle.
3. Smart Target Inspection (`inspect_target_summary`):
   Detects video containers, Hebrew subtitles (including plain `.srt` files needing Seed-Safe
   `.he.srt` torrent protection), and English master `.en.srt` files.
4. Direct Integration with:
   - Autonomous Runner (`18_auto_pipeline.py`)
   - SubRefine 0-Token Plex Fixer (`07_fix_plex_punctuation.py`)
   - Interactive Line-by-Line Polish Reviewer (`19_polish_and_qc.py --interactive`)
   - Setup & Hooks Installer (`20_config_and_doctor.py setup`)
   - Multi-Agent MCP Installer (`23_mcp_server.py --install`)
"""

import os
import re
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, Callable

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from rightsub import __version__ as VERSION
except Exception:
    VERSION = "1.5.0"


def normalize_dragged_path(raw_input: str) -> Path:
    """
    Normalizes a file or directory path pasted or dragged from macOS Finder,
    Windows Explorer, or PowerShell into the terminal.
    """
    if not raw_input:
        return Path("")

    s = raw_input.strip()

    # 1. Strip PowerShell leading call operator: & 'C:\path\file.mkv' or & "C:\path\file.mkv"
    if s.startswith("& ") or s.startswith("&\t"):
        s = s[1:].strip()

    # 2. Strip matching outer single or double quotes
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        s = s[1:-1].strip()

    # 3. On POSIX (macOS / Linux), Finder escapes spaces and special chars with backslashes (\ , \(, \), \[, \], \', \&)
    if sys.platform != "win32" and "\\" in s:
        unescaped = re.sub(r'\\([ \(\)\[\]\{\}\'\"\&\!\$\#\,\;])', r'\1', s)
        cand = Path(unescaped).expanduser()
        if cand.exists() or not Path(s).expanduser().exists():
            s = unescaped

    return Path(s).expanduser()


def interactive_file_browser(start_dir: Path, input_fn: Callable[[str], str] = input) -> Optional[Path]:
    """
    Linear numbered terminal file browser for selecting a directory, video file, or subtitle file.
    Safe across macOS Terminal, iTerm2, SSH, and Windows CMD/PowerShell without curses breakage.
    """
    curr = start_dir.expanduser().resolve()
    if curr.is_file():
        return curr
    if not curr.is_dir():
        curr = Path.cwd()

    media_exts = {".mkv", ".mp4", ".m4v", ".avi", ".mov", ".srt"}

    while True:
        print("\n------------------------------------------------------------------")
        print(f" Current Folder / תיקייה נוכחית: {curr}")
        print("------------------------------------------------------------------")
        print("  [0] Process ENTIRE current folder / טפל בכל התיקייה הנוכחית")
        print("  [..] Go up to parent directory / עלה לתיקיית האב")

        entries = []
        try:
            for item in sorted(curr.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.name.startswith("."):
                    continue
                if item.is_dir() or item.suffix.lower() in media_exts:
                    entries.append(item)
        except Exception as e:
            print(f"  [!] Cannot list directory: {e}")
            return None

        shown_entries = entries[:40]
        for i, entry in enumerate(shown_entries, start=1):
            kind = "[DIR]" if entry.is_dir() else "[FILE]"
            print(f"  [{i}] {kind:<6} {entry.name}")

        if len(entries) > len(shown_entries):
            print(f"  ... ({len(entries) - len(shown_entries)} more items)")

        print("  [Q] Cancel / ביטול")
        try:
            choice = input_fn("\nSelect item number [0 / .. / 1..N / Q]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if not choice or choice == "0":
            return curr
        if choice.lower() == "q":
            return None
        if choice == "..":
            curr = curr.parent
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(shown_entries):
                picked = shown_entries[idx - 1]
                if picked.is_dir():
                    curr = picked
                    continue
                return picked
        print("  [!] Invalid selection. Try again.")


def inspect_target_summary(target: Path) -> Dict[str, Any]:
    """Inspects a target file or directory and returns a quick summary of media and subtitles."""
    import importlib
    m18 = importlib.import_module("18_auto_pipeline")

    vid_exts = {".mkv", ".mp4", ".m4v", ".avi", ".mov"}
    summary = {
        "exists": target.exists(),
        "is_dir": target.is_dir(),
        "videos": [],
        "hebrew_srts": [],
        "plain_hebrew_srts": [],
        "english_srts": [],
    }
    if not target.exists():
        return summary

    files = sorted(target.rglob("*")) if target.is_dir() else [target]
    for f in files:
        if not f.is_file() or f.name.startswith("."):
            continue
        low = f.name.lower()
        if ".bak" in low or ".original." in low:
            continue
        if f.suffix.lower() in vid_exts:
            summary["videos"].append(f)
        elif f.suffix.lower() == ".srt":
            if m18.is_hebrew_file(f):
                summary["hebrew_srts"].append(f)
                if not low.endswith(".he.srt"):
                    summary["plain_hebrew_srts"].append(f)
            else:
                summary["english_srts"].append(f)

    return summary


def prompt_target_path(input_fn: Callable[[str], str] = input) -> Optional[Path]:
    """Prompts the user to drag & drop a file/folder or open the terminal file browser."""
    print("\n[?] Drag & drop a video, subtitle (.srt), or folder here")
    print("    (or press [B] to browse folders, [Enter] for current directory, [Q] to cancel):")
    try:
        raw = input_fn("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None

    if raw.lower() == "q":
        return None
    if raw.lower() == "b":
        return interactive_file_browser(Path.cwd(), input_fn=input_fn)
    if not raw:
        return interactive_file_browser(Path.cwd(), input_fn=input_fn)

    target = normalize_dragged_path(raw)
    if not target.exists():
        print(f"[-] Path not found: {target}")
        return None
    return target


def run_interactive_hub(input_fn: Callable[[str], str] = input) -> int:
    """Main interactive loop when running `rightsub` with no arguments or `rightsub wizard`."""
    import importlib
    m18 = importlib.import_module("18_auto_pipeline")
    m19 = importlib.import_module("19_polish_and_qc")
    m20 = importlib.import_module("20_config_and_doctor")
    m23 = importlib.import_module("23_mcp_server")

    cfg = m20.load_config()
    ffmpeg_ok = shutil.which("ffmpeg") is not None

    while True:
        print("\n==================================================================")
        print(f"       RightSub v{VERSION} — Interactive Mastering Suite")
        print("==================================================================")
        if not cfg and not ffmpeg_ok:
            print(" [!] First-time environment notice: FFmpeg or config not yet initialized.")
            print("     Select [4] to run the guided Setup & Health Wizard.\n")

        print("  [1] Auto-Process File or Folder (Drag & Drop / Seed-Safe Mastering)")
        print("      טיפול אוטומטי מלא בקובץ או תיקייה (זיהוי .srt בעברית, הגנת טורנט ותיקון פלקס)")
        print("  [2] Fix Plex/Infuse Hebrew BiDi & Punctuation (0 AI Tokens)")
        print("      תיקון דטרמיניסטי לפלקס ואינפיוז (RLM, קידוד CP1255, ניקוי פרסומות)")
        print("  [3] Interactive Subtitle Polish & Line-by-Line Review (polish --interactive)")
        print("      ליטוש והגהה שורה-אחר-שורה (אישור / דחייה / עריכה ידנית)")
        print("  [4] Setup Wizard, System Health & Downloader Hooks (qBittorrent / Sonarr / Radarr)")
        print("      אשף התקנה, בדיקת מערכת וחיבור אוטומטי לתוכנות הורדה")
        print("  [5] Connect Local MCP Server to AI Agents (Antigravity, Claude, Cursor, Windsurf)")
        print("      חיבור שרת MCP מקומי לשליטה מלאה מכל סוכן AI")
        print("  [6] Configure API Keys & Run System Doctor (config / doctor)")
        print("      הגדרת מפתחות API (TMDb / Gemini) ובדיקת תקינות")
        print("  [0] Exit / יציאה")
        print("==================================================================")

        try:
            choice = input_fn("Select option / בחר אפשרות [1-6, 0]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if choice in ("0", "q", "exit", "quit"):
            return 0

        if choice == "1":
            target = prompt_target_path(input_fn=input_fn)
            if not target:
                continue
            info = inspect_target_summary(target)
            print("\n------------------------------------------------------------------")
            print(f" Target Summary: {target.name}")
            print(f"  - Video files:         {len(info['videos'])}")
            print(f"  - Hebrew subtitles:    {len(info['hebrew_srts'])} ({len(info['plain_hebrew_srts'])} plain .srt needing Seed-Safe .he.srt copy)")
            print(f"  - English subtitles:   {len(info['english_srts'])}")
            print("------------------------------------------------------------------")
            try:
                seed_ans = input_fn("Keep original torrent files untouched (Seed-Safe .he.srt)? [Y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            replace_orig = seed_ans in ("n", "no")
            auto_args = argparse.Namespace(
                target=str(target),
                replace_original=replace_orig,
                ollama=False,
                model=None,
                engine="apple" if sys.platform == "darwin" else "whisper",
                no_clean_ads=False,
                no_backup=False,
                dry_run=False
            )
            if target.is_file() and target.suffix.lower() == ".srt":
                m18.handle_single_srt(target, auto_args)
            elif target.is_file():
                m18.handle_single_video(target, auto_args)
            else:
                m18.handle_directory(target, auto_args)

        elif choice == "2":
            target = prompt_target_path(input_fn=input_fn)
            if not target:
                continue
            auto_args = argparse.Namespace(
                target=str(target),
                replace_original=False,
                ollama=False,
                model=None,
                engine="apple" if sys.platform == "darwin" else "whisper",
                no_clean_ads=False,
                no_backup=False,
                dry_run=False
            )
            if target.is_file() and target.suffix.lower() == ".srt":
                m18.handle_single_srt(target, auto_args)
            elif target.is_dir():
                for srt in sorted(target.rglob("*.srt")):
                    if ".bak" in srt.name.lower() or ".original." in srt.name.lower():
                        continue
                    if m18.is_hebrew_file(srt):
                        m18.handle_single_srt(srt, auto_args)
            else:
                m18.handle_single_video(target, auto_args)

        elif choice == "3":
            target = prompt_target_path(input_fn=input_fn)
            if not target:
                continue
            try:
                ai_ans = input_fn("Mode: [1] 0-Token Deterministic Canon & Number Pass (Recommended)  [2] Include Cloud/Local AI Polish [1/2]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            offline_only = (ai_ans != "2")
            p_args = argparse.Namespace(
                target=str(target),
                en_path=None,
                tmdb_id=None,
                title=None,
                bible=None,
                ollama=False,
                gemini=(ai_ans == "2"),
                model=None,
                api_key=None,
                batch_size=60,
                offline_canon_only=offline_only,
                diff_only=False,
                dry_run=False,
                in_place=True,
                interactive=True,
                output=None,
                diff_report=None
            )
            m19.polish_target(str(target), None, p_args)

        elif choice == "4":
            s_args = argparse.Namespace(
                non_interactive=False,
                install_hooks=True,
                install_service=False,
                install_mcp=True
            )
            m20.handle_setup(s_args, input_fn=input_fn)

        elif choice == "5":
            res = m23.install_mcp_for_agents(target_agent="all")
            print("\n------------------------------------------------------------------")
            for item in res.get("results", []):
                icon = "[✓]" if item["success"] else "[✗]"
                print(f" {icon} [{item['agent']}] {item['message']}")
            print("------------------------------------------------------------------")

        elif choice == "6":
            m20.handle_doctor(argparse.Namespace())
            try:
                cfg_ans = input_fn("Would you like to update API keys (TMDb / Gemini) now? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                continue
            if cfg_ans in ("y", "yes"):
                m20.handle_config(argparse.Namespace(
                    install_quicksubs=False,
                    install_hooks=False,
                    install_service=False,
                    show=False,
                    clear=False,
                    gemini=None,
                    tmdb=None
                ))
                cfg = m20.load_config()
        else:
            print(" [!] Unknown option. Please choose 1-6 or 0.")

    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="rightsub wizard",
        description="RightSub Interactive Mastering Wizard"
    )
    parser.parse_args()
    sys.exit(run_interactive_hub())


if __name__ == "__main__":
    main()
