#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
18_auto_pipeline.py
-------------------
Universal Autonomous Pipeline Runner for RightSub ("The Zero-Flag / Foolproof Runner").

Purpose:
Provides a single, intuitive entrypoint (./rightsub auto <path>) that automatically determines
what the target is (Hebrew SRT, English SRT, Video file, or entire Directory/Season) and executes
the optimal mastering, transcription, BiDi repair, and translation workflow with zero flag configuration.

Workflow Logic:
1. Target is a Hebrew subtitle (.he.srt or Hebrew text):
   -> Fixes Plex punctuation, BiDi RLM, converts charset, cleans ads and creates backup.
2. Target is an English subtitle (.en.srt):
   -> Generates Translation Bible (with TMDb enrichment if configured) and AI batch prompts.
   -> If --ollama is active, translates 100% locally and merges to .he.srt.
3. Target is a Video file (.mkv, .mp4, etc.):
   -> Checks if companion .he.srt exists. If so, fixes it.
   -> If no .he.srt exists, checks for .en.srt.
   -> If no .en.srt exists, extracts embedded English tracks via FFmpeg.
   -> If no embedded subtitles exist, automatically runs quicksubs on-device STT!
   -> Generates translation batches. If --ollama is active, translates and merges.
4. Target is a Directory:
   -> Discovers all subtitle and video files recursively.
   -> Automatically repairs all Hebrew subtitles in-place.
   -> Automatically prepares/extracts English source subtitles for all un-subtitled videos.
   -> If --ollama is active, completes translation for the entire directory!
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse

SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".m4v", ".avi", ".ts", ".mov", ".webm"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".ssa", ".sub"}

def run_cmd(cmd):
    """Runs a command and returns the returncode."""
    print(f"[*] Running: {' '.join(str(c) for c in cmd)}")
    res = subprocess.run(cmd)
    return res.returncode

def read_srt_sample_auto_encoding(srt_path, max_bytes=65536):
    """
    Reads raw bytes from srt_path and decodes text, detecting UTF-8, UTF-8-BOM,
    Windows-1255 / CP1255, ISO-8859-8, or UTF-16.
    """
    try:
        with open(srt_path, "rb") as f:
            raw = f.read(max_bytes)
        if not raw:
            return ""

        # 1. UTF-16 BOM
        if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
            try:
                return raw.decode('utf-16', errors='replace')
            except Exception:
                pass

        # 2. Check UTF-8 / UTF-8-SIG
        try:
            text = raw.decode('utf-8-sig')
            he_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
            cp1255_hebrew_bytes = sum(1 for b in raw if 0xE0 <= b <= 0xFA)
            # If valid UTF-8 has zero Hebrew, but contains extensive CP1255 Hebrew bytes
            if cp1255_hebrew_bytes > 15 and he_chars == 0:
                try:
                    return raw.decode('cp1255', errors='replace')
                except Exception:
                    pass
            return text
        except UnicodeDecodeError:
            pass

        # 3. Check CP1255 (Hebrew ANSI - bytes 0xE0..0xFA)
        cp1255_bytes = sum(1 for b in raw if 0xE0 <= b <= 0xFA)
        if cp1255_bytes >= 5:
            try:
                return raw.decode('cp1255', errors='replace')
            except Exception:
                pass

        # 4. Fallbacks
        for enc in ['cp1255', 'iso-8859-8', 'utf-8', 'latin1']:
            try:
                return raw.decode(enc, errors='replace')
            except Exception:
                continue

        return raw.decode('utf-8', errors='replace')
    except Exception:
        return ""

def is_hebrew_file(srt_path):
    """
    Quickly and reliably inspects if an SRT file is Hebrew.
    Supports legacy Windows-1255 (CP1255), ISO-8859-8, and UTF-8.
    """
    text = read_srt_sample_auto_encoding(srt_path)
    if not text:
        return False
    he_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
    en_chars = sum(1 for c in text if ('a' <= c <= 'z') or ('A' <= c <= 'Z'))
    total_alpha = he_chars + en_chars
    if total_alpha == 0:
        return False
    return (he_chars >= 3 and en_chars == 0) or (he_chars >= 5 and (he_chars / total_alpha >= 0.12))

def find_companion_hebrew_subtitle(video_path):
    """
    Finds existing Hebrew subtitle for video_path.
    Checks:
    1. Standard Plex naming: video_stem.he.srt, video_stem.heb.srt, video_stem.hebrew.srt
    2. Alternate naming: video_stem.srt (if content is detected as Hebrew)
    3. Single video directory fallback: if directory has only one video file,
       checks any .srt in the directory (excluding .bak, .en.srt, .eng.srt)
       or within Subs/Subtitles folders for Hebrew content.
    Returns Path to the Hebrew subtitle, or None.
    """
    video_path = Path(video_path).resolve()
    parent_dir = video_path.parent
    stem = video_path.stem

    # 1. Direct standard stem matches
    for ext in [".he.srt", ".heb.srt", ".hebrew.srt"]:
        cand = parent_dir / f"{stem}{ext}"
        if cand.is_file():
            return cand

    # 2. Direct stem.srt match (content check)
    alt_srt = parent_dir / f"{stem}.srt"
    if alt_srt.is_file() and is_hebrew_file(alt_srt):
        return alt_srt

    # 3. Directory fallback: if this is the only video in parent_dir
    try:
        videos_in_dir = [
            f for f in parent_dir.iterdir()
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
        ]
    except Exception:
        videos_in_dir = []

    if len(videos_in_dir) == 1:
        search_dirs = [parent_dir]
        for sub_name in ["Subs", "subs", "Subtitles", "subtitles"]:
            sub_dir = parent_dir / sub_name
            if sub_dir.is_dir():
                search_dirs.append(sub_dir)

        for s_dir in search_dirs:
            for srt in s_dir.glob("*.srt"):
                if not srt.is_file():
                    continue
                name_lower = srt.name.lower()
                if (
                    name_lower.endswith(".bak") or
                    name_lower.endswith(".en.srt") or
                    name_lower.endswith(".eng.srt") or
                    name_lower.endswith(".english.srt") or
                    "prompts_" in str(srt)
                ):
                    continue
                if (
                    name_lower.endswith(".he.srt") or
                    name_lower.endswith(".heb.srt") or
                    name_lower.endswith(".hebrew.srt") or
                    is_hebrew_file(srt)
                ):
                    return srt

    return None

def find_companion_english_subtitle(video_path):
    """
    Finds existing English / source subtitle for video_path.
    """
    video_path = Path(video_path).resolve()
    parent_dir = video_path.parent
    stem = video_path.stem

    for ext in [".en.srt", ".eng.srt", ".english.srt"]:
        cand = parent_dir / f"{stem}{ext}"
        if cand.is_file():
            return cand

    alt_srt = parent_dir / f"{stem}.srt"
    if alt_srt.is_file() and not is_hebrew_file(alt_srt):
        return alt_srt

    # Directory fallback if single video in parent
    try:
        videos_in_dir = [
            f for f in parent_dir.iterdir()
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
        ]
    except Exception:
        videos_in_dir = []

    if len(videos_in_dir) == 1:
        for srt in parent_dir.glob("*.srt"):
            if not srt.is_file():
                continue
            name_lower = srt.name.lower()
            if (
                name_lower.endswith(".bak") or
                name_lower.endswith(".he.srt") or
                name_lower.endswith(".heb.srt") or
                name_lower.endswith(".hebrew.srt") or
                "prompts_" in str(srt)
            ):
                continue
            if not is_hebrew_file(srt):
                return srt

    return None

def handle_single_srt(srt_file, args):
    """Processes a single subtitle file."""
    srt_path = Path(srt_file).resolve()
    print(f"\n[+] Processing Subtitle: {srt_path.name}")
    
    name_lower = srt_path.name.lower()
    is_he = (
        name_lower.endswith(".he.srt") or
        name_lower.endswith(".heb.srt") or
        name_lower.endswith(".hebrew.srt") or
        is_hebrew_file(srt_path)
    )

    if is_he:
        # Standardize naming to .he.srt for Plex & Infuse recognition
        target_name = srt_path.name
        if name_lower.endswith(".heb.srt"):
            target_name = srt_path.name[:-8] + ".he.srt"
        elif name_lower.endswith(".hebrew.srt"):
            target_name = srt_path.name[:-11] + ".he.srt"
        elif not name_lower.endswith(".he.srt"):
            target_name = f"{srt_path.stem}.he.srt"

        target_path = srt_path.with_name(target_name)
        replace_orig = getattr(args, "replace_original", False)
        fix_script = SCRIPT_DIR / "07_fix_plex_punctuation.py"

        if target_path == srt_path:
            print("[i] Detected Hebrew subtitle (.he.srt). Applying Plex BiDi & Punctuation mastering...")
            cmd = [sys.executable, str(fix_script), str(srt_path), "--in-place"]
            if not args.no_clean_ads:
                cmd.append("--clean-ads")
            if not args.no_backup:
                cmd.append("--backup")
            if args.dry_run:
                cmd.append("--dry-run")
            run_cmd(cmd)
            final_path = srt_path
        elif replace_orig:
            print(f"[i] Detected Hebrew subtitle. Applying Plex BiDi mastering and renaming (--replace-original)...")
            cmd = [sys.executable, str(fix_script), str(srt_path), "--in-place"]
            if not args.no_clean_ads:
                cmd.append("--clean-ads")
            if not args.no_backup:
                cmd.append("--backup")
            if args.dry_run:
                cmd.append("--dry-run")
            run_cmd(cmd)

            if not target_path.exists() and not args.dry_run:
                try:
                    srt_path.rename(target_path)
                    print(f"[i] Renamed original subtitle for Plex: {srt_path.name} -> {target_path.name}")
                    final_path = target_path
                except Exception as e:
                    print(f"[!] Note: Could not rename to {target_path.name}: {e}")
                    final_path = srt_path
            else:
                final_path = target_path
        else:
            print(f"[i] Detected Hebrew subtitle. Seed-Safe mode: duplicating to {target_name} (original file left untouched)...")
            if not args.dry_run:
                try:
                    shutil.copy2(srt_path, target_path)
                    print(f"[✓] Seed-Safe duplicate created: {target_path.name} (original {srt_path.name} left 100% untouched)")
                except Exception as e:
                    print(f"[-] Failed to copy to {target_path.name}: {e}")
                    return False

                cmd = [sys.executable, str(fix_script), str(target_path), "--in-place"]
                if not args.no_clean_ads:
                    cmd.append("--clean-ads")
                run_cmd(cmd)
            else:
                print(f"[i] [Dry-Run] Would copy {srt_path.name} -> {target_path.name} and apply Plex mastering.")
            final_path = target_path

        print(f"[✓] Hebrew subtitle {final_path.name} is now 100% Plex & Infuse compliant!\n")
        return True
    else:
        print("[i] Detected English/source subtitle. Generating Translation Bible & Batches...")
        parent_dir = srt_path.parent
        stem = srt_path.stem.replace(".en", "").replace(".eng", "")
        prompts_dir = parent_dir / f"prompts_{stem}"
        bible_path = parent_dir / "translation_bible.json"

        # 1. Bible generation
        bible_script = SCRIPT_DIR / "03_generate_bible.py"
        cmd_bible = [sys.executable, str(bible_script), str(srt_path), "-o", str(bible_path)]
        if os.environ.get("TMDB_API_KEY"):
            cmd_bible.append("--tmdb")
        run_cmd(cmd_bible)

        # 2. Prompt builder
        prompt_script = SCRIPT_DIR / "09_prompt_builder.py"
        cmd_prompt = [
            sys.executable, str(prompt_script), str(srt_path),
            "-t", stem,
            "-o", str(prompts_dir)
        ]
        if bible_path.exists():
            cmd_prompt.extend(["-b", str(bible_path)])
        run_cmd(cmd_prompt)

        # 3. Optional Ollama local translation
        if args.ollama:
            print("\n[!] ==============================================================")
            print("[!] WARNING: LOCAL LLM HEBREW TRANSLATION LIMITATION")
            print("[!] Local models (Llama 3 / Qwen) have very low Hebrew token accuracy.")
            print("[!] Grammatical gender, verb conjugations and slang will be degraded.")
            print("[!] Use local Ollama for offline fallback only. Use Gemini for quality.")
            print("[!] ==============================================================\n")
            print(f"[i] --ollama requested: Starting offline local translation...")
            ollama_script = SCRIPT_DIR / "17_translate_ollama.py"
            out_he = parent_dir / f"{stem}.he.srt"
            cmd_ollama = [
                sys.executable, str(ollama_script), str(prompts_dir),
                "--en-srt", str(srt_path),
                "-o", str(out_he)
            ]
            if args.model:
                cmd_ollama.extend(["-m", args.model])
            run_cmd(cmd_ollama)
            # Fix plex on the newly generated hebrew subtitle
            if out_he.exists():
                fix_script = SCRIPT_DIR / "07_fix_plex_punctuation.py"
                run_cmd([sys.executable, str(fix_script), str(out_he), "--in-place", "--clean-ads"])
                print(f"[✓] End-to-end local translation complete! Created: {out_he.name}")
        else:
            print(f"\n[✓] Translation batches ready in: {prompts_dir}/")
            print("[i] Next steps:")
            print(f"    • With an AI Agent (Antigravity/Claude Code): 'Translate batches in {prompts_dir.name} and merge to {stem}.he.srt'")
            print(f"    • With 100% Free Local LLM: './rightsub translate-ollama \"{prompts_dir}\" --en-srt \"{srt_path}\"'")
        return True

def handle_single_video(video_file, args):
    """Processes a single video file."""
    video_path = Path(video_file).resolve()
    print(f"\n[+] Processing Video: {video_path.name}")
    parent_dir = video_path.parent
    stem = video_path.stem

    # Check if Hebrew subtitle already exists
    companion_he = find_companion_hebrew_subtitle(video_path)
    if companion_he:
        print(f"[i] Found existing Hebrew subtitle: {companion_he.name}")
        target_he = parent_dir / f"{stem}.he.srt"
        replace_orig = getattr(args, "replace_original", False)

        if companion_he == target_he:
            return handle_single_srt(companion_he, args)

        if replace_orig:
            success = handle_single_srt(companion_he, args)
            if not target_he.exists() and not args.dry_run:
                current_he = companion_he if companion_he.exists() else (companion_he.with_name(f"{companion_he.stem}.he.srt"))
                if current_he.exists() and current_he != target_he:
                    try:
                        current_he.rename(target_he)
                        print(f"[i] Standardized Hebrew subtitle for video (--replace-original): {current_he.name} -> {target_he.name}")
                    except Exception as e:
                        pass
            return success
        else:
            # Seed-Safe mode: duplicate companion_he directly to target_he
            print(f"[i] Seed-Safe mode: copying {companion_he.name} -> {target_he.name} (original left untouched)")
            if not args.dry_run:
                try:
                    shutil.copy2(companion_he, target_he)
                except Exception as e:
                    print(f"[-] Failed to copy to {target_he.name}: {e}")
                    return False
                return handle_single_srt(target_he, args)
            else:
                print(f"[i] [Dry-Run] Would copy {companion_he.name} -> {target_he.name} and apply Plex mastering.")
                return True

    # Check if English subtitle already exists
    companion_en = find_companion_english_subtitle(video_path)

    # If no English subtitle exists on disk, attempt extraction or transcription
    if not companion_en or not companion_en.exists():
        target_en = parent_dir / f"{stem}.en.srt"
        print(f"[i] No external English subtitle found. Attempting extraction from {video_path.name}...")
        extract_script = SCRIPT_DIR / "01_extract_subtitles.py"
        res = subprocess.run([
            sys.executable, str(extract_script), str(video_path),
            "-o", str(target_en), "-l", "eng"
        ])
        
        if res.returncode == 0 and target_en.exists() and target_en.stat().st_size > 100:
            print(f"[✓] Extracted embedded English subtitles to: {target_en.name}")
            companion_en = target_en
        else:
            print("[!] No embedded subtitles found. Falling back to quicksubs on-device audio transcription...")
            transcribe_script = SCRIPT_DIR / "00_transcribe_audio.py"
            t_res = subprocess.run([
                sys.executable, str(transcribe_script), str(video_path),
                "-o", str(parent_dir),
                "-e", args.engine
            ])
            if target_en.exists():
                companion_en = target_en
            else:
                gen_srt = parent_dir / f"{stem}.srt"
                if gen_srt.exists():
                    gen_srt.rename(target_en)
                    companion_en = target_en

    if companion_en and companion_en.exists():
        return handle_single_srt(companion_en, args)
    else:
        print(f"[-] Could not extract or transcribe subtitles for {video_path.name}")
        return False

def handle_directory(dir_path, args):
    """Processes an entire directory (movies folder, TV season, or entire series)."""
    dir_path = Path(dir_path).resolve()
    print(f"\n==================================================================")
    print(f"=== RightSub Auto: Scanning Directory {dir_path.name} ===")
    print(f"==================================================================")

    replace_orig = getattr(args, "replace_original", False)
    fix_script = SCRIPT_DIR / "07_fix_plex_punctuation.py"

    # 1. Discover all Hebrew subtitles
    srts_to_master = []
    discovered_he_srts = []
    for srt in dir_path.rglob("*.srt"):
        if srt.name.endswith(".bak") or "prompts_" in str(srt):
            continue
        name_lower = srt.name.lower()
        if (
            name_lower.endswith(".he.srt") or
            name_lower.endswith(".heb.srt") or
            name_lower.endswith(".hebrew.srt") or
            is_hebrew_file(srt)
        ):
            discovered_he_srts.append(srt)

    if discovered_he_srts:
        if replace_orig:
            print(f"[+] Found {len(discovered_he_srts)} Hebrew subtitle(s). Running automated Plex BiDi mastering (--replace-original)...")
            cmd = [sys.executable, str(fix_script)] + [str(s) for s in discovered_he_srts] + ["--in-place"]
            if not args.no_clean_ads:
                cmd.append("--clean-ads")
            if not args.no_backup:
                cmd.append("--backup")
            if args.dry_run:
                cmd.append("--dry-run")
            run_cmd(cmd)

            # Standardize names
            for srt in discovered_he_srts:
                name_lower = srt.name.lower()
                if not name_lower.endswith(".he.srt"):
                    if name_lower.endswith(".heb.srt"):
                        target_name = srt.name[:-8] + ".he.srt"
                    elif name_lower.endswith(".hebrew.srt"):
                        target_name = srt.name[:-11] + ".he.srt"
                    else:
                        target_name = f"{srt.stem}.he.srt"
                    target_path = srt.with_name(target_name)
                    if not target_path.exists() and not args.dry_run and srt.exists():
                        try:
                            srt.rename(target_path)
                            print(f"[i] Renamed Hebrew subtitle for Plex: {srt.name} -> {target_path.name}")
                        except Exception:
                            pass
        else:
            print(f"[+] Found {len(discovered_he_srts)} Hebrew subtitle(s). Seed-Safe mode active (originals preserved)...")
            for srt in discovered_he_srts:
                name_lower = srt.name.lower()
                if name_lower.endswith(".he.srt"):
                    srts_to_master.append(srt)
                else:
                    if name_lower.endswith(".heb.srt"):
                        target_name = srt.name[:-8] + ".he.srt"
                    elif name_lower.endswith(".hebrew.srt"):
                        target_name = srt.name[:-11] + ".he.srt"
                    else:
                        target_name = f"{srt.stem}.he.srt"
                    target_path = srt.with_name(target_name)

                    if not target_path.exists():
                        if not args.dry_run:
                            try:
                                shutil.copy2(srt, target_path)
                                print(f"[i] Seed-Safe duplicate created: {srt.name} -> {target_path.name} (original left untouched)")
                            except Exception as e:
                                print(f"[!] Warning: Could not duplicate {srt.name}: {e}")
                                continue
                        else:
                            print(f"[i] [Dry-Run] Would duplicate {srt.name} -> {target_path.name}")
                    if target_path not in srts_to_master:
                        srts_to_master.append(target_path)

            if srts_to_master:
                cmd = [sys.executable, str(fix_script)] + [str(s) for s in srts_to_master] + ["--in-place"]
                if not args.no_clean_ads:
                    cmd.append("--clean-ads")
                if args.dry_run:
                    cmd.append("--dry-run")
                run_cmd(cmd)

        print(f"[✓] Successfully processed {len(discovered_he_srts)} Hebrew subtitle file(s)!")

    # 2. Discover video files
    video_files = [f for f in dir_path.rglob("*") if f.suffix.lower() in VIDEO_EXTENSIONS]
    print(f"[+] Found {len(video_files)} video file(s). Checking for missing Hebrew subtitles...")

    processed_vids = 0
    for vid in sorted(video_files):
        he_sub = find_companion_hebrew_subtitle(vid)
        if he_sub:
            # Video already has a Hebrew subtitle! Ensure Plex .he.srt standard naming
            target_he = vid.parent / f"{vid.stem}.he.srt"
            if he_sub != target_he:
                if replace_orig:
                    if not target_he.exists() and not args.dry_run:
                        try:
                            he_sub.rename(target_he)
                            print(f"[i] Standardized Hebrew subtitle for Plex (--replace-original): {he_sub.name} -> {target_he.name}")
                        except Exception:
                            pass
                else:
                    if not target_he.exists() and not args.dry_run:
                        try:
                            shutil.copy2(he_sub, target_he)
                            print(f"[i] Seed-Safe standardized Hebrew subtitle for Plex: {he_sub.name} -> {target_he.name} (original left untouched)")
                            cmd = [sys.executable, str(fix_script), str(target_he), "--in-place"]
                            if not args.no_clean_ads:
                                cmd.append("--clean-ads")
                            run_cmd(cmd)
                        except Exception:
                            pass
            continue  # Already has Hebrew subtitle

        print(f"\n---> Video missing Hebrew subtitles: {vid.name}")
        handle_single_video(vid, args)
        processed_vids += 1

    print("\n==================================================================")
    print(f"=== RightSub Auto Execution Summary ===")
    print(f"  • Hebrew subtitles mastered: {len(srts_to_master if not replace_orig else discovered_he_srts)}")
    print(f"  • Total video files scanned:  {len(video_files)}")
    print(f"  • New videos prepared:        {processed_vids}")
    print(f"==================================================================\n")
    return True

def main():
    parser = argparse.ArgumentParser(
        prog="rightsub auto",
        description="Universal Autonomous Pipeline Runner — Zero flags needed. Handles single files or full seasons."
    )
    parser.add_argument("target", help="Path to video file, subtitle file, or directory")
    parser.add_argument(
        "--replace-original",
        action="store_true",
        help="In-place rename mode: replace and rename original non-standard subtitle files instead of duplicating (breaks torrent seeding)"
    )
    parser.add_argument("--ollama", action="store_true", help="Perform 100% offline local translation using Ollama")
    parser.add_argument("--model", help="Ollama model name (default: llama3.2 / llama3:8b)")
    parser.add_argument("--engine", choices=["apple", "whisper", "parakeet"], default="apple", help="quicksubs speech engine")
    parser.add_argument("--no-clean-ads", action="store_true", help="Do not strip promo spam/credits")
    parser.add_argument("--no-backup", action="store_true", help="Do not create .srt.bak before in-place modifications")
    parser.add_argument("--dry-run", action="store_true", help="Preview mode without writing changes")

    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"[-] Target not found: {target_path}")
        sys.exit(1)

    if target_path.is_file():
        suffix = target_path.suffix.lower()
        if suffix in SUBTITLE_EXTENSIONS:
            success = handle_single_srt(target_path, args)
        elif suffix in VIDEO_EXTENSIONS:
            success = handle_single_video(target_path, args)
        else:
            print(f"[-] Unsupported file format: {target_path.name}")
            sys.exit(1)
    elif target_path.is_dir():
        success = handle_directory(target_path, args)
    else:
        print(f"[-] Invalid target: {target_path}")
        sys.exit(1)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
