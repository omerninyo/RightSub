#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_web_search_and_sync.py
-------------------------
Compares an existing Hebrew subtitle file (e.g. downloaded from OpenSubtitles/Wizdom/Torec)
against the target English master SRT file.
Calculates timestamp drift, detects FPS differences, and re-times the Hebrew subtitles
if the line-count or dialogue flow matches.
"""
import sys
import re
import datetime
import argparse

def parse_srt(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()
    
    blocks = re.split(r'\n\s*\n', content)
    subs = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 3:
            idx = lines[0].strip()
            time_line = lines[1].strip()
            text = "\n".join(lines[2:]).strip()
            m = re.match(r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})', time_line)
            if m:
                start_str, end_str = m.group(1), m.group(2)
                subs.append({"index": idx, "start": start_str, "end": end_str, "text": text})
    return subs

def time_to_ms(t_str):
    t_str = t_str.replace(",", ".")
    h, m, s = t_str.split(":")
    sec, ms = s.split(".")
    return (int(h)*3600 + int(m)*60 + int(sec))*1000 + int(ms)

def compare_subtitles(en_path, he_path, threshold_ms=1000):
    en_subs = parse_srt(en_path)
    he_subs = parse_srt(he_path)

    print(f"[i] English subs count: {len(en_subs)}")
    print(f"[i] Hebrew subs count:  {len(he_subs)}")

    diff_count = abs(len(en_subs) - len(he_subs))
    ratio = min(len(en_subs), len(he_subs)) / max(len(en_subs), len(he_subs)) if max(len(en_subs), len(he_subs)) > 0 else 0
    print(f"[i] Count match ratio: {ratio:.1%}")

    if len(en_subs) == len(he_subs):
        print("[+] Exact 1:1 count match! Checking timestamp deltas...")
        deltas = []
        for e, h in zip(en_subs, he_subs):
            e_start = time_to_ms(e["start"])
            h_start = time_to_ms(h["start"])
            deltas.append(h_start - e_start)
        
        avg_delta = sum(deltas) / len(deltas)
        max_delta = max(deltas)
        min_delta = min(deltas)
        drift = abs(deltas[-1] - deltas[0])
        print(f"    Avg Delta: {avg_delta:.1f}ms | Min: {min_delta}ms | Max: {max_delta}ms | Drift: {drift}ms")
        
        if drift < 250:
            print("[✓] Constant offset detected! Can be trivially fixed with shift.")
        elif drift > 2000:
            print("[!] Framerate difference detected (likely 23.976 vs 25.0 FPS) or TV ad commercial gap!")
    else:
        print("[-] Subtitle counts differ. May require fuzzy time-window alignment or partial segment borrowing.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare and sync external Hebrew SRT with English master SRT.")
    parser.add_argument("en_srt", help="Master English SRT")
    parser.add_argument("he_srt", help="External Hebrew SRT to compare")
    args = parser.parse_args()
    compare_subtitles(args.en_srt, args.he_srt)
