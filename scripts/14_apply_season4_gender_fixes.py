#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
14_apply_season4_gender_fixes.py
---------------------------------
Applies surgical gender fixes, shift resynchronizations, full content restoration
from .bak.v25 for S04E06, accurate translation of S04E12 ending preview cues,
and strict 1..N re-indexing with Plex/Infuse compliant RLM markers across all 20
episodes of Boston Legal Season 4.
"""

import os
import re
import sys

MEDIA_DIR = "/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p/Season 4"

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

def process_season4():
    print("Starting Boston Legal Season 4 Gender & Formatting Fixes...")

    for ep_num in range(1, 21):
        ep = f"S04E{ep_num:02d}"
        en_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.en.srt")
        he_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.he.srt")
        bak_v25_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.he.srt.bak.v25")

        en_blocks = parse_srt_blocks(en_path)

        # 1. Source selection: Restore S04E06 from bak.v25
        if ep == "S04E06" and os.path.exists(bak_v25_path):
            source_path = bak_v25_path
            print(f"[{ep}] Restoring complete translation from {os.path.basename(bak_v25_path)} (recovering from desync)...")
        else:
            source_path = he_path

        he_blocks = parse_srt_blocks(source_path)

        if len(en_blocks) != len(he_blocks):
            print(f"[{ep}] ERROR: Block count mismatch! EN={len(en_blocks)}, HE={len(he_blocks)}")
            sys.exit(1)

        # Convert to mutable list of text line lists
        he_texts = [list(lines) for _, lines in he_blocks]

        # 2. Episode-specific surgical gender and dialogue fixes (indices are 1-based cue numbers)
        def replace_in_cue(cue_num, old_sub, new_sub):
            idx = cue_num - 1
            if idx < len(he_texts):
                lines = he_texts[idx]
                updated = []
                for l in lines:
                    c = clean_he(l)
                    if old_sub in c:
                        c = c.replace(old_sub, new_sub)
                    updated.append(c)
                he_texts[idx] = updated

        if ep == "S04E04":
            # Addressing Whitney Rome
            replace_in_cue(85, "אתה לא יכול", "את לא יכולה")

        elif ep == "S04E08":
            # Addressing Shirley Schmidt
            replace_in_cue(97, "תשמע, ברצינות, שירלי", "תשמעי, ברצינות, שירלי")
            # Addressing Judge Victoria Thomson
            replace_in_cue(697, "כבודו", "כבוד השופטת")
            replace_in_cue(703, "כבודו יכול", "כבוד השופטת יכולה")

        elif ep == "S04E12":
            # Carl speaking to Shirley Schmidt
            replace_in_cue(263, "אתה יודע מה? אני מופתע ממך, שירלי", "את יודעת מה? אני מופתע ממך, שירלי")
            # Translate ending preview cues (710-725) to match video audio
            preview_translations = {
                710: ["קריין: בפרק הבא של בוסטון ליגל."],
                711: ["ג'ק רוס. אל תדבר. זה יהרוס לי את זה."],
                712: ["- ג'ק? - את זוכרת. ואני חשבתי שזה היה רק פיזי."],
                713: ["עדיין מנסה להרשים אותי אחרי כל השנים האלה?"],
                714: ["כן. הצלחתי?"],
                715: ["מה הסיפור איתו?"],
                716: ["יצאנו יחד בבית הספר למשפטים."],
                717: ["אשתך יודעת שאתה יוצא איתי הערב?"],
                718: ["לפעמים אני מבוגר מדי וחכם מדי בשביל לומר את האמת."],
                719: ["אם תדברי עם ג'רי, עלולים להיות לי דחפים אלימים."],
                720: ["תתרחקי מהגבר שלי, קייטי."],
                721: ["- אלן, הרגע שכבתי עם זר. - מתי זה קרה?"],
                722: ["לפני עשר דקות, ממש כאן. סיימתי לפני תשע דקות. הייתי מדהימה."],
                723: [],
                724: ["- שער, שער, שער!"],
                725: ["איי."],
            }
            for cue, lines in preview_translations.items():
                he_texts[cue - 1] = lines

        elif ep == "S04E14":
            # Carl speaking to Shirley Schmidt
            replace_in_cue(185, "אתה ואני", "את ואני")

        elif ep == "S04E20":
            # Katie speaking to Alan
            replace_in_cue(237, "קייטי: איך אתה מעז להתערב?", "- איך אתה מעז להתערב?")

        # 3. Strict 1..N re-indexing and dual RLM formatting
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

    print("\nSeason 4 processing completed successfully.")

if __name__ == "__main__":
    process_season4()
