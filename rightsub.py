#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rightsub.py
-----------
RightSub — Universal Subtitle Mastering & Translation Suite for Movies & TV Series.
Powered by the SubRefine Algorithmic Engine & SubSwarm Multi-Agent Orchestrator.

Commands:
  auto          Zero-flag autonomous runner: processes single file, season, or directory.
  translate-ollama 100% offline, free local subtitle translation using Ollama (LLaMA 3, Qwen).
  split         Split master English SRT into JSON batches (~210 items) for translation.
  merge         Merge translated JSON batches into master Hebrew SRT with automated RLM & QC.
  prompt-gen    Generate wave-based AI translation prompts (Gemini Flash/Flash-Lite) for any title.
  qa            Run comprehensive QA audit comparing EN and HE SRTs (or whole directory).
  fix-plex      Batch fix Hebrew punctuation & BiDi for Plex/Infuse (standalone SRT repair).
  extract       Extract embedded subtitles from video files via FFmpeg.
  sync          Compare & test synchronization of external Hebrew subtitles against master English.
  bible         Generate character & terminology Translation Bible from English subtitles.
  adjust-fps    Shift timestamps or stretch framerate (e.g. 25.0 -> 23.976 FPS).
  transcribe    On-Device Speech-to-Subtitle transcription via quicksubs.
  audio-sync    Audio-guided subtitle synchronization & retiming via quicksubs.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"

def run_script(script_name, args):
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"[-] Script not found: {script_path}")
        sys.exit(1)
    
    cmd = [sys.executable, str(script_path)] + args
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

def main():
    parser = argparse.ArgumentParser(
        prog="rightsub",
        description="RightSub — Universal Subtitle Mastering & Translation Suite (Powered by SubRefine Engine & SubSwarm)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: split
    p_split = subparsers.add_parser("split", help="Split SRT into JSON batches for translation")
    p_split.add_argument("srt", help="Master English SRT")
    p_split.add_argument("-o", "--output_dir", required=True, help="Batch output directory")
    p_split.add_argument("-s", "--size", type=int, default=210, help="Batch size (default: 210)")

    # Command: merge
    p_merge = subparsers.add_parser("merge", help="Merge translated JSON batches into final Hebrew SRT with RLM & QC")
    p_merge.add_argument("en_srt", help="Original master English SRT")
    p_merge.add_argument("json_dir", help="Directory of translated batch JSONs")
    p_merge.add_argument("-o", "--output", required=True, help="Output Hebrew SRT file")

    # Command: prompt-gen
    p_prompt = subparsers.add_parser("prompt-gen", help="Generate AI translation prompts and wave files for any title")
    p_prompt.add_argument("srt", help="Path to English SRT")
    p_prompt.add_argument("-t", "--title", default="", help="Title of movie or series episode")
    p_prompt.add_argument("-c", "--context", default="", help="Plot description, character names and notes")
    p_prompt.add_argument("-g", "--genre", default="", help="Genre or tone (e.g. Drama, Comedy, Sci-Fi)")
    p_prompt.add_argument("-b", "--bible", default="", help="Path to translation_bible.json")
    p_prompt.add_argument("--overlap", type=int, default=5, help="Context overlap cues from previous batch (default: 5)")
    p_prompt.add_argument("-s", "--chunk-size", type=int, default=88, help="Cues per agent (default: 88)")
    p_prompt.add_argument("-m", "--model", default="flash_lite", help="Model tier (default: flash_lite)")
    p_prompt.add_argument("-o", "--output-dir", default="", help="Output directory")

    # Command: qa
    p_qa = subparsers.add_parser("qa", help="Run comprehensive QA audit on subtitle files or directory")
    p_qa.add_argument("en_srt", help="Master English SRT or directory path")
    p_qa.add_argument("he_srt", nargs="?", help="Hebrew SRT file (optional if auditing a folder)")
    p_qa.add_argument("-b", "--bible", default="", help="Path to translation_bible.json for character gender checks")
    p_qa.add_argument("--strict-gender", action="store_true", help="Fail QA audit if gender mismatches are found")
    p_qa.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # Command: fix-plex
    p_fix = subparsers.add_parser("fix-plex", help="Fix Hebrew punctuation & BiDi for Plex/Infuse (standalone)")
    p_fix.add_argument("targets", nargs="+", help="SRT files or directory paths")
    p_fix.add_argument("--in-place", "-i", action="store_true", help="Overwrite files directly")
    p_fix.add_argument("--output-dir", "-o", help="Output directory")
    p_fix.add_argument("--recursive", "-r", action="store_true", help="Search directories recursively")
    p_fix.add_argument("--clean-ads", action="store_true", help="Strip promo spam & translation credit lines")
    p_fix.add_argument("--backup", "-b", action="store_true", help="Create .bak before in-place modifications")

    # Command: extract
    p_ext = subparsers.add_parser("extract", help="Discover & extract subtitles from video files via FFmpeg")
    p_ext.add_argument("target", help="Path to video file or directory")
    p_ext.add_argument("-o", "--output", help="Output .srt path")
    p_ext.add_argument("-l", "--lang", default="eng", help="Subtitle language code (default: eng)")

    # Command: sync
    p_sync = subparsers.add_parser("sync", help="Compare external Hebrew SRT against English master")
    p_sync.add_argument("en_srt", help="Master English SRT")
    p_sync.add_argument("he_srt", help="External Hebrew SRT to compare")

    # Command: bible
    p_bible = subparsers.add_parser("bible", help="Generate Translation Bible skeleton from English SRTs & TMDb")
    p_bible.add_argument("srts", nargs="+", help="English SRT files to analyze")
    p_bible.add_argument("-o", "--output", default="translation_bible.json", help="Output JSON path")
    p_bible.add_argument("-t", "--title", help="Movie or TV show title")
    p_bible.add_argument("-s", "--season", type=int, help="Season number")
    p_bible.add_argument("-e", "--episode", type=int, help="Episode number")
    p_bible.add_argument("--tmdb", action="store_true", help="Enrich Bible with TMDb characters, genders, and plot")
    p_bible.add_argument("--tmdb-key", help="TMDb API Key / Read Access Token")

    # Command: adjust-fps
    p_fps = subparsers.add_parser("adjust-fps", help="Stretch framerate or shift time offsets")
    p_fps.add_argument("input", help="Input SRT file")
    p_fps.add_argument("-o", "--output", required=True, help="Output SRT file")

    # Command: transcribe (quicksubs)
    p_trans = subparsers.add_parser("transcribe", help="On-Device Speech-to-Subtitle transcription via quicksubs")
    p_trans.add_argument("input", help="Media video/audio file")
    p_trans.add_argument("-o", "--output-dir", help="Output directory")
    p_trans.add_argument("-e", "--engine", choices=["apple", "whisper", "parakeet"], default="apple", help="Speech engine")

    # Command: audio-sync (quicksubs)
    p_async = subparsers.add_parser("audio-sync", help="Audio-guided subtitle synchronization & retiming via quicksubs")
    p_async.add_argument("unsynced_srt", help="Desynced subtitle file")
    p_async.add_argument("-o", "--output", required=True, help="Aligned output SRT file")
    p_async.add_argument("-v", "--video", help="Video file containing authoritative audio")
    p_async.add_argument("-r", "--reference-srt", help="Reference SRT file")
    p_async.add_argument("-e", "--engine", choices=["apple", "whisper", "parakeet"], default="apple", help="Speech engine")

    # Command: auto (Zero-flag autonomous runner)
    p_auto = subparsers.add_parser("auto", help="Zero-flag autonomous subtitle mastering & translation pipeline")
    p_auto.add_argument("target", help="Path to video file, subtitle file, or directory")
    p_auto.add_argument("--ollama", action="store_true", help="Perform 100%% offline local translation using Ollama")
    p_auto.add_argument("--model", help="Ollama model name (default: llama3.2 / llama3:8b)")
    p_auto.add_argument("--engine", choices=["apple", "whisper", "parakeet"], default="apple", help="quicksubs speech engine")
    p_auto.add_argument("--no-clean-ads", action="store_true", help="Do not strip promo spam/credits")
    p_auto.add_argument("--no-backup", action="store_true", help="Do not create .srt.bak before in-place modifications")
    p_auto.add_argument("--dry-run", action="store_true", help="Preview mode without writing changes")

    # Command: translate-ollama (Offline local translation)
    p_ollama = subparsers.add_parser("translate-ollama", help="Offline local subtitle translation using Ollama")
    p_ollama.add_argument("prompts_dir", help="Directory containing batch_*_input.json files")
    p_ollama.add_argument("-m", "--model", help="Ollama model name (default: llama3.2 / llama3:8b)")
    p_ollama.add_argument("--url", default="http://localhost:11434", help="Ollama server URL")
    p_ollama.add_argument("--en-srt", help="Original English master SRT for automatic merge")
    p_ollama.add_argument("-o", "--output", help="Output .he.srt path after merge")

    args, unknown = parser.parse_known_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    script_mapping = {
        "auto": "18_auto_pipeline.py",
        "translate-ollama": "17_translate_ollama.py",
        "split": "04_split_batches.py",
        "merge": "05_merge_and_validate.py",
        "prompt-gen": "09_prompt_builder.py",
        "qa": "08_quality_assurance.py",
        "fix-plex": "07_fix_plex_punctuation.py",
        "extract": "01_extract_subtitles.py",
        "sync": "02_web_search_and_sync.py",
        "bible": "03_generate_bible.py",
        "adjust-fps": "06_adjust_fps_or_offset.py",
        "transcribe": "00_transcribe_audio.py",
        "audio-sync": "16_audio_align_sync.py"
    }

    script_name = script_mapping[args.command]
    raw_args = sys.argv[2:]
    run_script(script_name, raw_args)

if __name__ == "__main__":
    main()
