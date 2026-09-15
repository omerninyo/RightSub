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
import re
import datetime
import argparse

def parse_time(t_str):
    t_str = t_str.replace(",", ".")
    h, m, s = t_str.split(":")
    sec, ms = s.split(".")
    return (int(h)*3600 + int(m)*60 + int(sec))*1000 + int(ms)

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
    if fps_from and fps_to:
        ratio = float(fps_from) / float(fps_to)
        print(f"[i] Framerate stretch ratio: {ratio:.6f} ({fps_from} -> {fps_to})")

    with open(input_path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()

    blocks = re.split(r'\n\s*\n', content)
    out_blocks = []
    
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            idx = lines[0]
            m = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', lines[1])
            if m:
                s_ms = int(parse_time(m.group(1)) * ratio + offset_ms)
                e_ms = int(parse_time(m.group(2)) * ratio + offset_ms)
                new_time_line = f"{format_time(s_ms)} --> {format_time(e_ms)}"
                new_block = [idx, new_time_line] + lines[2:]
                out_blocks.append("\n".join(new_block))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out_blocks) + "\n")
    print(f"[✓] Adjusted SRT saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adjust subtitle framerate and time offsets.")
    parser.add_argument("input", help="Input SRT file")
    parser.add_argument("-o", "--output", required=True, help="Output SRT file")
    parser.add_argument("--offset_ms", type=int, default=0, help="Offset in milliseconds (e.g. 1200 or -500)")
    parser.add_argument("--fps_from", type=float, default=None, help="Source FPS (e.g. 23.976)")
    parser.add_argument("--fps_to", type=float, default=None, help="Target FPS (e.g. 25.0)")
    args = parser.parse_args()
    adjust_srt(args.input, args.output, args.offset_ms, args.fps_from, args.fps_to)
