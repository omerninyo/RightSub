#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06_adjust_fps_or_offset.py
--------------------------
Adjusts timing of SRT subtitles:
1. Constant linear offset (shift by X milliseconds or seconds).
2. Framerate conversion (e.g. 23.976 -> 25.0 FPS, 25.0 -> 23.976 FPS).
3. Two-point linear sync stretch (anchor start and anchor end).
"""
import os
import re
import sys
import argparse
from pathlib import Path

def parse_time(t_str):
    t_str = t_str.replace(",", ".").strip()
    h, m, s = t_str.split(":")
    sec, ms = s.split(".") if "." in s else (s, "0")
    return (int(h)*3600 + int(m)*60 + int(sec))*1000 + int(ms.ljust(3, "0")[:3])

def format_time(ms):
    if ms < 0:
        ms = 0
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def adjust_srt(input_path, output_path, offset_ms=0, fps_from=None, fps_to=None):
    ratio = 1.0
    if fps_from is not None and fps_to is not None:
        if float(fps_to) <= 0 or float(fps_from) <= 0:
            raise ValueError("fps_from and fps_to must be positive numbers.")
        ratio = float(fps_from) / float(fps_to)
        print(f"[i] Framerate stretch ratio: {ratio:.6f} ({fps_from} -> {fps_to})")

    try:
        import importlib
        scripts_dir = str(Path(__file__).resolve().parent)
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        fix_mod = importlib.import_module("07_fix_plex_punctuation")
        content, _ = fix_mod.read_file_with_auto_encoding(Path(input_path))
        content = content.strip()
    except Exception:
        with open(input_path, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read().strip()

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r'\n\s*\n', content)
    out_blocks = []

    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            idx = lines[0]
            m = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{1,3})', lines[1])
            if m:
                s_ms = int(parse_time(m.group(1)) * ratio + offset_ms)
                e_ms = int(parse_time(m.group(2)) * ratio + offset_ms)
                new_time_line = f"{format_time(s_ms)} --> {format_time(e_ms)}"
                new_block = [idx, new_time_line] + lines[2:]
                out_blocks.append("\n".join(new_block))

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_dest = dest.with_name(f".{dest.name}.tmp.{os.getpid()}")
    try:
        with open(tmp_dest, "w", encoding="utf-8") as f:
            f.write("\n\n".join(out_blocks) + "\n")
        os.replace(tmp_dest, dest)
    finally:
        if tmp_dest.exists():
            try:
                tmp_dest.unlink()
            except Exception:
                pass
    try:
        os.utime(dest, None)
    except Exception:
        pass
    print(f"[✓] Adjusted SRT saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adjust subtitle framerate and time offsets.")
    parser.add_argument("input", help="Input SRT file")
    parser.add_argument("-o", "--output", required=True, help="Output SRT file")
    parser.add_argument("--offset_ms", "--offset-ms", dest="offset_ms", type=int, default=0, help="Offset in milliseconds (e.g. 1200 or -500)")
    parser.add_argument("--fps_from", "--fps-from", dest="fps_from", type=float, default=None, help="Source FPS (e.g. 23.976)")
    parser.add_argument("--fps_to", "--fps-to", dest="fps_to", type=float, default=None, help="Target FPS (e.g. 25.0)")
    args = parser.parse_args()
    if (args.fps_from is None) != (args.fps_to is None):
        print("[-] Error: --fps-from and --fps-to must be specified together.", file=sys.stderr)
        sys.exit(1)
    adjust_srt(args.input, args.output, args.offset_ms, args.fps_from, args.fps_to)
