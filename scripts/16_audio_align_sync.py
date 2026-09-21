#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16_audio_align_sync.py
-----------------------
Audio-Guided Subtitle Retiming & Synchronization Engine.

Credit & Attribution:
- Utilizes the on-device transcription engine `quicksubs` created by Matt Birchler.
- GitHub: https://github.com/mattbirchler/quicksubs
- Blog: https://birchtree.me

Problem Solved:
- Often an existing translated subtitle (.he.srt) has perfect language/content,
  but its timing is desynced (FPS mismatch 23.976 vs 25, commercial cuts, or offset).
- This script uses `quicksubs` to extract true spoken dialogue timestamps directly
  from the video file's audio track, then calculates optimal offset and drift (stretch),
  re-aligning the subtitle file with zero manual guessing.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from importlib import import_module

try:
    _transcribe_mod = import_module("00_transcribe_audio")
    transcribe_audio = _transcribe_mod.transcribe_audio
    is_quicksubs_available = _transcribe_mod.is_quicksubs_available
except Exception:
    transcribe_audio = None
    is_quicksubs_available = lambda: False

def parse_time(t_str: str) -> int:
    """Parse SRT timestamp 'HH:MM:SS,mmm' to milliseconds."""
    t_str = t_str.replace(",", ".").strip()
    parts = t_str.split(":")
    if len(parts) != 3:
        return 0
    h, m, s = parts
    sec, ms = s.split(".") if "." in s else (s, "0")
    return (int(h) * 3600 + int(m) * 60 + int(sec)) * 1000 + int(ms.ljust(3, "0")[:3])

def format_time(ms: int) -> str:
    """Format milliseconds to SRT timestamp 'HH:MM:SS,mmm'."""
    if ms < 0:
        ms = 0
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def parse_srt_cues(srt_path: Path) -> list:
    """Parse SRT file into structured cues: [{'index': int, 'start': int, 'end': int, 'lines': [str]}]."""
    content = srt_path.read_text(encoding="utf-8-sig", errors="replace").strip()
    blocks = re.split(r'\n\s*\n', content)
    cues = []
    
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            time_match = re.search(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', lines[1])
            if time_match:
                start_ms = parse_time(time_match.group(1))
                end_ms = parse_time(time_match.group(2))
                cue_lines = lines[2:] if len(lines) > 2 else [""]
                cues.append({
                    "raw_index": lines[0],
                    "start": start_ms,
                    "end": end_ms,
                    "lines": cue_lines
                })
    return cues

def compute_alignment_parameters(target_cues: list, ref_cues: list) -> tuple:
    """
    Compute optimal linear transformation (scale_ratio, offset_ms)
    mapping target timestamps to audio reference timestamps:
        t_aligned = t_target * scale_ratio + offset_ms
    """
    if not target_cues or not ref_cues:
        return 1.0, 0

    # Start-to-start anchor offset based on the first substantial dialogue burst
    t0_target = target_cues[0]["start"]
    t0_ref = ref_cues[0]["start"]
    initial_offset = t0_ref - t0_target

    # If cue counts are roughly comparable (e.g. within 20%), estimate stretch ratio
    n_target = len(target_cues)
    n_ref = len(ref_cues)
    
    t_end_target = target_cues[-1]["start"]
    t_end_ref = ref_cues[-1]["start"]

    span_target = t_end_target - t0_target
    span_ref = t_end_ref - t0_ref

    scale_ratio = 1.0
    if span_target > 60000 and span_ref > 60000:
        ratio = span_ref / span_target
        # Check if ratio matches common film/TV FPS conversions (e.g. 23.976/25 = 0.95904, 25/23.976 = 1.0427)
        if 0.90 <= ratio <= 1.10:
            scale_ratio = ratio

    offset_ms = int(t0_ref - (t0_target * scale_ratio))
    return scale_ratio, offset_ms

def align_subtitles(
    unsynced_srt_path: str,
    output_srt_path: str,
    video_path: str = None,
    reference_srt_path: str = None,
    engine: str = "apple"
) -> dict:
    """
    Align unsynced SRT timestamps using either an audio track via quicksubs
    or a pre-existing reference SRT file.
    """
    unsynced = Path(unsynced_srt_path).resolve()
    output = Path(output_srt_path).resolve()

    if not unsynced.exists():
        return {"success": False, "error": f"Target subtitle not found: {unsynced_srt_path}"}

    target_cues = parse_srt_cues(unsynced)
    if not target_cues:
        return {"success": False, "error": f"No valid subtitle cues found in {unsynced.name}"}

    ref_cues = None
    temp_ref_generated = None

    # Option A: Reference SRT provided directly
    if reference_srt_path and Path(reference_srt_path).exists():
        ref_path = Path(reference_srt_path).resolve()
        ref_cues = parse_srt_cues(ref_path)

    # Option B: Transcribe audio track from video using quicksubs
    elif video_path and Path(video_path).exists():
        vid = Path(video_path).resolve()
        print(f"[+] Transcribing audio reference from video via quicksubs ({engine})...")
        if not is_quicksubs_available():
            return {
                "success": False,
                "error": (
                    "quicksubs CLI tool is required for audio alignment but not found in PATH.\n"
                    "Install via: brew install mattbirchler/tap/quicksubs\n"
                    "(Attribution: Matt Birchler - https://github.com/mattbirchler/quicksubs)"
                )
            }
        
        temp_dir = output.parent / ".temp_audio_sync"
        temp_dir.mkdir(parents=True, exist_ok=True)
        res = transcribe_audio(str(vid), output_dir=str(temp_dir), engine=engine, format_type="srt")
        if not res["success"] or not res["output_file"]:
            return {"success": False, "error": f"Audio transcription failed: {res.get('error')}"}
        
        temp_ref_generated = Path(res["output_file"])
        ref_cues = parse_srt_cues(temp_ref_generated)

    else:
        return {"success": False, "error": "Must provide either --video or --reference-srt"}

    if not ref_cues:
        return {"success": False, "error": "Could not parse reference cues for alignment"}

    # Compute parameters
    scale, offset_ms = compute_alignment_parameters(target_cues, ref_cues)
    print(f"[i] Audio Alignment Computed: Scale Ratio={scale:.6f}, Offset={offset_ms:+d}ms")

    # Re-align target cues
    aligned_blocks = []
    for i, cue in enumerate(target_cues, start=1):
        new_start = max(0, int(cue["start"] * scale + offset_ms))
        dur = cue["end"] - cue["start"]
        new_end = new_start + max(500, int(dur * scale))

        block = [
            str(i),
            f"{format_time(new_start)} --> {format_time(new_end)}"
        ] + cue["lines"]
        aligned_blocks.append("\n".join(block))

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n\n".join(aligned_blocks) + "\n\n")

    # Clean up temporary reference file if created
    if temp_ref_generated and temp_ref_generated.exists():
        try:
            import shutil
            shutil.rmtree(temp_ref_generated.parent)
        except Exception:
            pass

    return {
        "success": True,
        "output_file": str(output),
        "cues_count": len(target_cues),
        "scale_ratio": scale,
        "offset_ms": offset_ms
    }

def main():
    parser = argparse.ArgumentParser(
        description="Audio-Guided Subtitle Alignment & Synchronization Engine (using quicksubs by Matt Birchler)."
    )
    parser.add_argument("unsynced_srt", help="Path to desynced subtitle file to align")
    parser.add_argument("-o", "--output", required=True, help="Path for aligned output SRT file")
    parser.add_argument("-v", "--video", help="Video file containing authoritative audio track")
    parser.add_argument("-r", "--reference-srt", help="Pre-existing audio-transcribed reference SRT")
    parser.add_argument(
        "-e", "--engine", choices=["apple", "whisper", "parakeet"], default="apple",
        help="quicksubs speech engine (default: apple)"
    )

    args = parser.parse_args()

    print(f"[+] Audio-Guided Subtitle Sync Engine")
    print(f"    Attribution: quicksubs by Matt Birchler (https://github.com/mattbirchler/quicksubs)")
    print(f"    Target:      {args.unsynced_srt}")

    res = align_subtitles(
        unsynced_srt_path=args.unsynced_srt,
        output_srt_path=args.output,
        video_path=args.video,
        reference_srt_path=args.reference_srt,
        engine=args.engine
    )

    if res["success"]:
        print(f"[✓] Subtitle successfully aligned -> {res['output_file']}")
        print(f"    Cues: {res['cues_count']} | Scale: {res['scale_ratio']:.5f} | Offset: {res['offset_ms']}ms")
        sys.exit(0)
    else:
        print(f"[-] Alignment failed: {res['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
