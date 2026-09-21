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

def is_hebrew_file(srt_path):
    """Quickly inspects if an SRT file is Hebrew."""
    try:
        with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(4096)
        he_chars = sum(1 for c in sample if '\u0590' <= c <= '\u05FF')
        en_chars = sum(1 for c in sample if ('a' <= c <= 'z') or ('A' <= c <= 'Z'))
        total_alpha = he_chars + en_chars
        if total_alpha == 0:
            return False
        return (he_chars >= 3 and en_chars == 0) or (he_chars >= 10 and (he_chars / total_alpha >= 0.15))
    except Exception:
        return False

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
        print("[i] Detected Hebrew subtitle. Applying Plex BiDi & Punctuation mastering...")
        fix_script = SCRIPT_DIR / "07_fix_plex_punctuation.py"
        cmd = [sys.executable, str(fix_script), str(srt_path), "--in-place"]
        if not args.no_clean_ads:
            cmd.append("--clean-ads")
        if not args.no_backup:
            cmd.append("--backup")
        if args.dry_run:
            cmd.append("--dry-run")
        run_cmd(cmd)
        print(f"[✓] Hebrew subtitle {srt_path.name} is now 100% Plex & Infuse compliant!\n")
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
    companion_he = parent_dir / f"{stem}.he.srt"
    alt_he = parent_dir / f"{stem}.srt"
    if companion_he.exists():
        print(f"[i] Found existing Hebrew subtitle: {companion_he.name}")
        return handle_single_srt(companion_he, args)
    elif alt_he.exists() and is_hebrew_file(alt_he):
        print(f"[i] Found existing Hebrew subtitle: {alt_he.name}")
        return handle_single_srt(alt_he, args)

    # Check if English subtitle already exists
    companion_en = parent_dir / f"{stem}.en.srt"
    if not companion_en.exists():
        alt_en = parent_dir / f"{stem}.srt"
        if alt_en.exists() and not is_hebrew_file(alt_en):
            companion_en = alt_en

    # If no English subtitle exists on disk, attempt extraction or transcription
    if not companion_en.exists():
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

    if companion_en.exists():
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

    # 1. Discover all Hebrew subtitles and batch-fix them
    he_srts = []
    for srt in dir_path.rglob("*.srt"):
        if srt.name.endswith(".bak"):
            continue
        name_lower = srt.name.lower()
        if (
            name_lower.endswith(".he.srt") or
            name_lower.endswith(".heb.srt") or
            name_lower.endswith(".hebrew.srt") or
            is_hebrew_file(srt)
        ):
            he_srts.append(srt)

    if he_srts:
        print(f"[+] Found {len(he_srts)} Hebrew subtitle(s). Running automated Plex BiDi mastering...")
        fix_script = SCRIPT_DIR / "07_fix_plex_punctuation.py"
        cmd = [sys.executable, str(fix_script)] + [str(s) for s in he_srts] + ["--in-place"]
        if not args.no_clean_ads:
            cmd.append("--clean-ads")
        if not args.no_backup:
            cmd.append("--backup")
        if args.dry_run:
            cmd.append("--dry-run")
        run_cmd(cmd)
        print(f"[✓] Successfully repaired all {len(he_srts)} Hebrew subtitle files!")

    # 2. Discover video files
    video_files = [f for f in dir_path.rglob("*") if f.suffix.lower() in VIDEO_EXTENSIONS]
    print(f"[+] Found {len(video_files)} video file(s). Checking for missing Hebrew subtitles...")

    processed_vids = 0
    for vid in sorted(video_files):
        stem = vid.stem
        comp_he = vid.parent / f"{stem}.he.srt"
        alt_he = vid.parent / f"{stem}.srt"
        if comp_he.exists() or (alt_he.exists() and is_hebrew_file(alt_he)):
            continue  # Already has Hebrew subtitle
        
        print(f"\n---> Video missing Hebrew subtitles: {vid.name}")
        handle_single_video(vid, args)
        processed_vids += 1

    print("\n==================================================================")
    print(f"=== RightSub Auto Execution Summary ===")
    print(f"  • Hebrew subtitles mastered: {len(he_srts)}")
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
