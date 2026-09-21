#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
01_extract_subtitles.py
-----------------------
Universal Subtitle Discovery & Extraction Engine.

Features:
- Detects external subtitles (.srt, .vtt, .ass, .sub) alongside video files.
- Converts foreign subtitle formats (.vtt, .ass) to standard .srt automatically.
- Scans video containers (MKV, MP4, M4V, AVI, TS, MOV, WebM) for embedded subtitle streams.
- Extracts the desired language track (default: English) using FFmpeg.
- Sanitizes extracted subtitles: strips technical <font>, <c>, and {\...} ASS tags.
- Supports both single file and recursive/flat directory batch processing.
"""

import os
import sys
import re
import json
import subprocess
import argparse
from pathlib import Path
from importlib import import_module

# Optional quicksubs integration (Matt Birchler: https://github.com/mattbirchler/quicksubs)
try:
    _transcribe_mod = import_module("00_transcribe_audio")
    transcribe_audio = _transcribe_mod.transcribe_audio
    is_quicksubs_available = _transcribe_mod.is_quicksubs_available
except Exception:
    transcribe_audio = None
    is_quicksubs_available = lambda: False

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".m4v", ".avi", ".ts", ".mov", ".webm"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".ssa", ".sub"}

def inspect_video(file_path):
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return None
    try:
        return json.loads(res.stdout)
    except Exception:
        return None

def clean_srt_tags(srt_path):
    """Clean technical HTML font tags and ASS styling overrides from extracted SRT."""
    if not os.path.exists(srt_path):
        return
    try:
        with open(srt_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        # Remove <font ...> and </font>
        text = re.sub(r'</?font[^>]*>', '', text, flags=re.IGNORECASE)
        # Remove <c ...> and </c>
        text = re.sub(r'</?c[^>]*>', '', text, flags=re.IGNORECASE)
        # Remove ASS position/style tags e.g. {\an8}, {\pos(x,y)}, {\b1}
        text = re.sub(r'\{[^\}]+\}', '', text)
        # Normalize redundant empty lines (keep standard SRT 2 newlines between cues)
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(text.strip() + "\n\n")
    except Exception as e:
        print(f"    [!] Warning: Failed to sanitize tags in {srt_path}: {e}")

def convert_to_srt(source_sub_path, target_srt_path):
    """Convert .vtt, .ass, etc. to standard .srt via FFmpeg."""
    cmd = ["ffmpeg", "-y", "-i", str(source_sub_path), str(target_srt_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(target_srt_path):
        clean_srt_tags(target_srt_path)
        return True
    return False

def discover_external_subtitles(video_path, lang="eng"):
    """Check if external subtitles already exist for this video."""
    parent = video_path.parent
    stem = video_path.stem

    direct_candidates = [
        parent / f"{stem}.{lang}.srt",
        parent / f"{stem}.en.srt",
        parent / f"{stem}.srt",
        parent / f"{stem}.{lang}.vtt",
        parent / f"{stem}.en.vtt",
        parent / f"{stem}.vtt",
        parent / f"{stem}.ass",
    ]

    for cand in direct_candidates:
        if cand.exists() and cand.stat().st_size > 0:
            return cand
    return None

def extract_from_video(video_path, output_srt=None, track_index=None, lang="eng", force=False, fallback_transcribe=False, engine="apple"):
    """Extract embedded subtitle track from a video container or fallback to quicksubs STT."""
    video_path = Path(video_path)
    if not output_srt:
        output_srt = video_path.parent / f"{video_path.stem}.en.srt"
    else:
        output_srt = Path(output_srt)

    # 1. If output already exists and not forcing, keep it
    if output_srt.exists() and output_srt.stat().st_size > 0 and not force:
        print(f"    [=] Target SRT already exists: {output_srt.name} (skipping extraction)")
        return True, "exists"

    # 2. Check for other external subtitle files to convert if needed
    external_sub = discover_external_subtitles(video_path, lang=lang)
    if external_sub and external_sub != output_srt:
        if external_sub.suffix.lower() == ".srt":
            print(f"    [+] Found existing external SRT: {external_sub.name}")
            if external_sub != output_srt:
                import shutil
                shutil.copy2(external_sub, output_srt)
            clean_srt_tags(output_srt)
            return True, "external_found"
        else:
            print(f"    [+] Converting external {external_sub.suffix} to SRT: {external_sub.name} -> {output_srt.name}")
            if convert_to_srt(external_sub, output_srt):
                return True, "external_converted"

    # 3. Inspect video file for embedded subtitle tracks
    info = inspect_video(video_path)
    if not info:
        print(f"    [-] Could not inspect video: {video_path.name}")
        return False, "probe_failed"

    sub_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "subtitle"]
    if not sub_streams:
        print(f"    [-] No embedded subtitle streams found in {video_path.name}")
        if fallback_transcribe:
            return _attempt_quicksubs_transcription(video_path, output_srt, engine)
        return False, "no_streams"

    selected_index = None
    if track_index is not None:
        if 0 <= track_index < len(sub_streams):
            selected_index = sub_streams[track_index]["index"]
    else:
        lang_prefixes = ["eng", "en"] if lang in ["eng", "en"] else [lang.lower()]
        for s in sub_streams:
            stream_lang = s.get("tags", {}).get("language", "").lower()
            if any(stream_lang.startswith(prefix) for prefix in lang_prefixes):
                selected_index = s["index"]
                break
        if selected_index is None and len(sub_streams) > 0:
            selected_index = sub_streams[0]["index"]

    if selected_index is None:
        print(f"    [-] No matching subtitle stream for language '{lang}' in {video_path.name}")
        if fallback_transcribe:
            return _attempt_quicksubs_transcription(video_path, output_srt, engine)
        return False, "track_not_found"

    output_srt.parent.mkdir(parents=True, exist_ok=True)
    extract_cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-map", f"0:{selected_index}",
        str(output_srt)
    ]
    res = subprocess.run(extract_cmd, capture_output=True, text=True)
    if res.returncode == 0 and output_srt.exists() and output_srt.stat().st_size > 0:
        clean_srt_tags(output_srt)
        print(f"    [✓] Extracted & sanitized stream #{selected_index} -> {output_srt.name}")
        return True, "extracted"
    else:
        print(f"    [-] FFmpeg extraction failed for {video_path.name}: {res.stderr.strip()[:100]}")
        if fallback_transcribe:
            return _attempt_quicksubs_transcription(video_path, output_srt, engine)
        return False, "ffmpeg_failed"

def _attempt_quicksubs_transcription(video_path, output_srt, engine):
    """Fallback handler using quicksubs CLI on-device transcription."""
    if is_quicksubs_available() and transcribe_audio:
        print(f"    [+] Falling back to On-Device STT (quicksubs, engine: {engine})...")
        res = transcribe_audio(
            input_media_path=str(video_path),
            output_dir=str(output_srt.parent),
            engine=engine,
            format_type="srt"
        )
        if res.get("success") and res.get("output_file"):
            out_f = Path(res["output_file"])
            if out_f.resolve() != output_srt.resolve():
                import shutil
                shutil.move(str(out_f), str(output_srt))
            clean_srt_tags(output_srt)
            print(f"    [✓] Generated SRT from audio via quicksubs -> {output_srt.name}")
            return True, "transcribed"
        else:
            print(f"    [-] quicksubs transcription failed: {res.get('error')}")
            return False, "transcription_failed"
    else:
        print("    [!] quicksubs CLI not available. To enable On-Device STT fallback:")
        print("        brew install mattbirchler/tap/quicksubs")
        print("        (Attribution: Matt Birchler - https://github.com/mattbirchler/quicksubs)")
        return False, "quicksubs_unavailable"

def process_target(target_path, output=None, track_index=None, lang="eng", force=False, recursive=False, fallback_transcribe=False, engine="apple"):
    target = Path(target_path)
    if not target.exists():
        print(f"[-] Target does not exist: {target_path}")
        sys.exit(1)

    if target.is_file():
        ok, reason = extract_from_video(
            target,
            output_srt=output,
            track_index=track_index,
            lang=lang,
            force=force,
            fallback_transcribe=fallback_transcribe,
            engine=engine
        )
        sys.exit(0 if ok else 1)

    elif target.is_dir():
        print(f"[+] Scanning directory for video files: {target}")
        pattern = "**/*" if recursive else "*"
        video_files = [f for f in target.glob(pattern) if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
        video_files.sort()

        if not video_files:
            print(f"[-] No video files found in {target}")
            sys.exit(0)

        print(f"[+] Found {len(video_files)} video file(s). Starting Discovery & Extraction...")
        stats = {"extracted": 0, "exists": 0, "external_found": 0, "external_converted": 0, "transcribed": 0, "failed": 0}

        for i, vid in enumerate(video_files, start=1):
            print(f"[{i}/{len(video_files)}] Processing {vid.name}...")
            ok, reason = extract_from_video(
                vid,
                track_index=track_index,
                lang=lang,
                force=force,
                fallback_transcribe=fallback_transcribe,
                engine=engine
            )
            if ok:
                stats[reason] = stats.get(reason, 0) + 1
            else:
                stats["failed"] += 1

        print("\n" + "=" * 60)
        print(f"Summary for {target.name}:")
        print(f"  Total Videos:       {len(video_files)}")
        print(f"  Newly Extracted:    {stats.get('extracted', 0)}")
        print(f"  Already Existed:    {stats.get('exists', 0)}")
        print(f"  External Converted: {stats.get('external_converted', 0)}")
        print(f"  Transcribed (STT):  {stats.get('transcribed', 0)}")
        print(f"  Failed / No Subs:   {stats.get('failed', 0)}")
        print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Universal Subtitle Discovery & Extraction Engine (FFmpeg + quicksubs On-Device STT)."
    )
    parser.add_argument("target", help="Video file or directory containing video files")
    parser.add_argument("-o", "--output", help="Output .srt path (only for single file mode)")
    parser.add_argument("-t", "--track", type=int, default=None, help="Subtitle track index (0-based)")
    parser.add_argument("-l", "--lang", default="eng", help="Desired subtitle language code (default: eng)")
    parser.add_argument("-f", "--force", action="store_true", help="Force re-extraction even if target SRT exists")
    parser.add_argument("-r", "--recursive", action="store_true", help="Scan subdirectories recursively")
    parser.add_argument(
        "--transcribe", action="store_true",
        help="Fallback to quicksubs On-Device STT if no subtitles are found (Matt Birchler: github.com/mattbirchler/quicksubs)"
    )
    parser.add_argument(
        "-e", "--engine", choices=["apple", "whisper", "parakeet"], default="apple",
        help="Speech engine for quicksubs transcription (default: apple)"
    )
    args = parser.parse_args()

    process_target(
        args.target,
        output=args.output,
        track_index=args.track,
        lang=args.lang,
        force=args.force,
        recursive=args.recursive,
        fallback_transcribe=args.transcribe,
        engine=args.engine
    )
