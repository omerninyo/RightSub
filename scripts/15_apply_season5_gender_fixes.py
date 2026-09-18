#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15_apply_season5_gender_fixes.py
---------------------------------
Applies strict 1..N re-indexing, text sanitation, and Plex/Infuse compliant
dual RLM markers across all 13 episodes of Boston Legal Season 5.
"""

import os
import re
import sys

MEDIA_DIR = "/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p/Season 5"

# Import official apply_rlm_to_line from 07_fix_plex_punctuation.py
sys.path.insert(0, "/Volumes/Other/Antigravity/RightSub/scripts")
from importlib import import_module
fix_plex = import_module("07_fix_plex_punctuation")
apply_rlm_to_line = fix_plex.apply_rlm_to_line
clean_and_sanitize_text = fix_plex.clean_and_sanitize_text

def parse_srt_blocks(filepath):
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()
    raw_blocks = re.split(r"\n\s*\n", content)
    blocks = []
    for b in raw_blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                timing = lines[1].strip()
                text_lines = lines[2:]
                blocks.append((timing, text_lines))
            except Exception:
                continue
    return blocks

def format_clean_hebrew(text_lines):
    cleaned = []
    for line in text_lines:
        c = clean_and_sanitize_text(line)
        if c:
            c = apply_rlm_to_line(c)
            cleaned.append(c)
    return cleaned

def clean_he(t):
    return re.sub(r"[\u200e\u200f]", "", t).strip()

def process_season5():
    print("Starting Boston Legal Season 5 Formatting & Verification...")

    for ep_num in range(1, 14):
        ep = f"S05E{ep_num:02d}"
        en_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.en.srt")
        he_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.he.srt")

        en_blocks = parse_srt_blocks(en_path)
        he_blocks = parse_srt_blocks(he_path)

        if len(en_blocks) != len(he_blocks):
            print(f"[{ep}] ERROR: Block count mismatch! EN={len(en_blocks)}, HE={len(he_blocks)}")
            sys.exit(1)

        he_texts = [list(lines) for _, lines in he_blocks]

        # Strict 1..N re-indexing and dual RLM formatting
        output_blocks = []
        for i, ((timing, _), lines) in enumerate(zip(en_blocks, he_texts)):
            clean_lines = format_clean_hebrew(lines)
            output_blocks.append((i + 1, timing, clean_lines))

        # Write output file
        with open(he_path, "w", encoding="utf-8") as f:
            for cue_num, timing, lines in output_blocks:
                f.write(f"{cue_num}\n")
                f.write(f"{timing}\n")
                if lines:
                    f.write("\n".join(lines) + "\n")
                else:
                    f.write("\n")
                f.write("\n")

        print(f"[{ep}] Successfully written {len(output_blocks)} cues to {os.path.basename(he_path)}")

    print("\nSeason 5 processing completed successfully.")

if __name__ == "__main__":
    process_season5()
