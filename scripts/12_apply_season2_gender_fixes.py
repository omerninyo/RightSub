#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12_apply_season2_gender_fixes.py
---------------------------------
Applies surgical gender fixes, shift resynchronizations, full content restoration
from .bak.v25 for truncated episodes (S13-S20), and strict 1..N re-indexing with
Plex/Infuse compliant RLM markers across all 27 episodes of Boston Legal Season 2.
"""

import os
import re
import sys

MEDIA_DIR = "/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p/Season 2"

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

def process_season2():
    print("Starting Boston Legal Season 2 Gender & Formatting Fixes...")

    for ep_num in range(1, 28):
        ep = f"S02E{ep_num:02d}"
        en_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.en.srt")
        he_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.he.srt")
        bak_v25_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.he.srt.bak.v25")

        en_blocks = parse_srt_blocks(en_path)

        # 1. Source selection: Restore truncated episodes (13..20) from bak.v25
        if 13 <= ep_num <= 20 and os.path.exists(bak_v25_path):
            source_path = bak_v25_path
            print(f"[{ep}] Restoring complete translation from {os.path.basename(bak_v25_path)} (recovering from truncation)...")
        else:
            source_path = he_path

        he_blocks = parse_srt_blocks(source_path)

        if len(en_blocks) != len(he_blocks):
            print(f"[{ep}] ERROR: Block count mismatch! EN={len(en_blocks)}, HE={len(he_blocks)}")
            sys.exit(1)

        # Convert to mutable list of text line lists
        he_texts = [list(lines) for _, lines in he_blocks]

        # 2. Resynchronize merge shifts
        if ep == "S02E24":
            print("[S02E24] Applying merge shift resynchronization (cues 474-558)...")
            # Cue 474 (idx 473): Split into 474 and 475
            he_texts[473] = ["האם איש מקצוע רפואי אי פעם קישר את הסוכרת שלך,"]
            he_texts.insert(474, ["במיוחד, לעוגות החטיף של 'ליל ג'ימיז'?"])
            # Remove the empty/redundant placeholder at 558
            del he_texts[558]

        elif ep == "S02E25":
            print("[S02E25] Applying merge shift resynchronization (cues 198-220)...")
            # Cue 198 (idx 197): Split into 198 and 199
            he_texts[197] = ["כן. אז, דוקטור, כחוות דעתך המקצועית"]
            he_texts.insert(198, ["כרופא,"])
            # Delete redundant duplicate at 220
            del he_texts[220]

        # 3. Episode-specific surgical gender fixes (indices are 1-based cue numbers)
        def replace_in_cue(cue_num, old_sub, new_sub):
            idx = cue_num - 1
            if idx < len(he_texts):
                lines = he_texts[idx]
                joined = "\n".join(lines)
                clean_joined = clean_he(joined)
                if old_sub in clean_joined:
                    updated = clean_joined.replace(old_sub, new_sub)
                    he_texts[idx] = updated.splitlines()
                    print(f"[{ep}] Cue {cue_num} fixed: '{old_sub}' -> '{new_sub}'")
                else:
                    print(f"[{ep}] Cue {cue_num} WARNING: '{old_sub}' not found in: '{clean_joined}'")

        if ep == "S02E02":
            # Denise Bauer speaking
            replace_in_cue(142, "אני צריך תזכיר", "אני צריכה תזכיר")

        elif ep == "S02E08":
            # Paul to Shirley Schmidt
            replace_in_cue(113, "אתה הוא זה שתחקור אותה, שירלי.", "את זו שתחקרי אותה, שירלי.")

        elif ep == "S02E11":
            # Judge Rose Olsheim (Female)
            replace_in_cue(309, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(864, "כבוד השופט", "כבוד השופטת")

        elif ep == "S02E12":
            # Judge Peggy Zeder (Female)
            replace_in_cue(259, "כבוד היושב ראש", "כבוד השופטת")
            replace_in_cue(260, "השופט לא מחבב אותה", "השופטת לא מחבבת אותה")
            replace_in_cue(282, "כבוד היושב ראש", "כבוד השופטת")
            replace_in_cue(394, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(398, "תודה לך, כבוד השופט,", "תודה לך, כבוד השופטת,")
            replace_in_cue(641, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(643, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(644, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(654, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(714, "סליחה, כבוד השופט.", "סליחה, כבוד השופטת.")

        elif ep == "S02E13":
            # Judge Nora Lang (Female)
            replace_in_cue(660, "גברת אב-המושבעים", "גברתי יושבת ראש חבר המושבעים")
            replace_in_cue(661, "הגענו, כבוד השופט.", "הגענו, כבוד השופטת.")
            replace_in_cue(668, "כבוד השופט,", "כבוד השופטת,")

        elif ep == "S02E18":
            # Judge Diane Avent (Female)
            replace_in_cue(45, "כבוד השופט,", "כבוד השופטת,")
            replace_in_cue(48, "כבוד השופט...", "כבוד השופטת...")
            replace_in_cue(51, "ספור עד עשר, השופט.", "ספרי עד עשר, כבוד השופטת.")
            replace_in_cue(60, "כבוד השופט.", "כבוד השופטת.")
            replace_in_cue(528, "כבוד השופט,", "כבוד השופטת,")
            replace_in_cue(535, "כבוד השופט,", "כבוד השופטת,")
            replace_in_cue(777, "כבוד השופט.", "כבוד השופטת.")
            replace_in_cue(794, "כבוד השופט.", "כבוד השופטת.")
            replace_in_cue(806, "כבוד השופט,", "כבוד השופטת,")

        elif ep == "S02E20":
            # Judge Isabel Hernandez & Judge Leslie Bishop
            replace_in_cue(651, "השופט פסק.", "השופטת פסקה.")

        elif ep == "S02E21":
            # Judge Jamie Atkinson (Female) in Polygamy case
            replace_in_cue(430, "כבוד השופט.", "כבוד השופטת.")
            replace_in_cue(626, "כבוד השופט.", "כבוד השופטת.")

        elif ep == "S02E24":
            # Address to Shirley Schmidt
            replace_in_cue(499, "מה המילה? אתה, אה...", "מה המילה? את, אה...")

        elif ep == "S02E25":
            # Judge Kimberly Ohlund (Female)
            replace_in_cue(384, "שופט אמפתי", "שופטת אמפתית")
            replace_in_cue(451, "אין נוספות, כבוד השופט.", "אין נוספות, כבוד השופטת.")
            replace_in_cue(763, "כבוד היושב ראש.", "כבוד השופטת.")

        # 4. Write back clean, sequential 1..N SRT with RLM
        out_blocks = []
        for idx in range(len(en_blocks)):
            timing = en_blocks[idx][0]
            raw_lines = he_texts[idx]
            cleaned_lines = format_clean_hebrew(raw_lines)
            
            cue_num = idx + 1
            block_str = f"{cue_num}\n{timing}"
            if cleaned_lines:
                block_str += "\n" + "\n".join(cleaned_lines)
            out_blocks.append(block_str)

        final_content = "\n\n".join(out_blocks) + "\n"

        with open(he_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        print(f"[{ep}] Successfully written {len(out_blocks)} blocks to {os.path.basename(he_path)}")

    print("\nAll Season 2 episodes processed and saved successfully.")

if __name__ == "__main__":
    process_season2()
