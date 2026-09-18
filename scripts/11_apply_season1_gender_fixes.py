#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
11_apply_season1_gender_fixes.py
---------------------------------
Applies verified, surgical gender fixes across Season 1 subtitle files.
Preserves exact SRT block numbering, timing, and Plex/Infuse RLM formatting.
"""

import os
import sys
import re
from pathlib import Path

# Add scripts directory to path to import apply_rlm_to_line
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from importlib import import_module
    fix_module = import_module("07_fix_plex_punctuation")
    apply_rlm = fix_module.apply_rlm_to_line
except Exception as e:
    print(f"[-] Warning: Failed to import 07_fix_plex_punctuation: {e}")
    RLM = "\u200F"
    def apply_rlm(line):
        line = re.sub(r"[\u200e\u200f]", "", line).strip()
        if not line:
            return line
        return f"{RLM}{line}{RLM}"

def parse_srt(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()
    blocks = re.split(r"\n\s*\n", content)
    cues = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                idx = int(lines[0].strip())
                timing = lines[1].strip()
                text = "\n".join(lines[2:])
                cues.append({"idx": idx, "timing": timing, "text": text})
            except ValueError:
                continue
    return cues

def write_srt(cues, path):
    out_blocks = []
    for i, c in enumerate(cues, 1):
        # Format text lines with RLM
        raw_lines = c["text"].splitlines()
        formatted_lines = [apply_rlm(l) for l in raw_lines]
        block_text = "\n".join(formatted_lines)
        out_blocks.append(f"{i}\n{c['timing']}\n{block_text}")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(out_blocks) + "\n")

SEASON_1_DIR = Path("/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p/Season 1")

# Exact surgical replacement rules per episode and cue index
FIXES = {
    "Boston Legal S01E01.he.srt": {
        330: ("כבוד השופט, אתה רציני?", "כבוד השופטת, את רצינית?"),
        331: ("עורכת דין, אנחנו מדברים כאן על אימוץ.", "פרקליט, אנחנו מדברים כאן על אימוץ."),
        338: ("כבוד השופט, זה באמת הוגן כלפי הילדה השנייה?", "כבוד השופטת, זה באמת הוגן כלפי הילדה השנייה?"),
        339: ("עורכת דין, אם היא יכולה לשיר שמונה פעמים בשבוע", "פרקליט, אם היא יכולה לשיר שמונה פעמים בשבוע"),
        552: ("למפיקים במצבים האלה -- כבודו,", "למפיקים במצבים האלה -- כבוד השופטת,"),
        557: ("אפשר להשמיע אותי, כבודו?", "אוכל להישמע, כבוד השופטת?"),
        560: ("אני מצטער, כבוד הכומר, אבל אין לך מעמד משפטי כאן.", "אני מצטערת, כבוד הכומר, אבל אין לך מעמד משפטי כאן."),
        587: ("לא מחר, כבודו.", "לא מחר, כבוד השופטת."),
    },
    "Boston Legal S01E02.he.srt": {
        468: ("אתה יודע מה? אתה יודע מה יהיה כיף?", "את יודעת מה? את יודעת מה יהיה כיף?"),
    },
    "Boston Legal S01E03.he.srt": {
        715: ("כבוד השופט, הם אינם בסכנת הכחדה", "כבוד השופטת, הם אינם בסכנת הכחדה"),
        717: ("אני לא סופר את סלמון הבריכות,", "אני לא סופרת את סלמון הבריכות,"),
    },
    "Boston Legal S01E06.he.srt": {
        138: ("חשש להימלטות? כבוד השופט,", "חשש להימלטות? כבוד השופטת,"),
        141: ("קצת שיגדון, כבוד השופט.", "קצת שיגדון, כבוד השופטת."),
    },
    "Boston Legal S01E11.he.srt": {
        450: ("כבוד השופטת.", "כבוד השופט."),
        453: ("התנגדות, כבוד השופטת.", "התנגדות, כבוד השופט."),
        462: ("אני מוחה על הזחיחות הזו,\nכבוד השופטת.", "אני מוחה על הזחיחות הזו,\nכבוד השופט."),
        506: ("ברשותך, כבוד השופטת?", "ברשותך, כבוד השופט?"),
        547: ("אנחנו מרוצים מכך שהשופטת\nלקחה את העניין לעיון.", "אנחנו מרוצים מכך שהשופט\nלקח את העניין לעיון."),
    },
    "Boston Legal S01E14.he.srt": {
        124: ("טרה וילסון בשם ההגנה, כבוד השופט.", "טרה וילסון בשם ההגנה, כבוד השופטת."),
        129: ("כבוד השופט, הבחור פגע בכבוד שלי.", "כבוד השופטת, הבחור פגע בכבוד שלי."),
        135: ("ההצעה שלי י שנודה בעובדות מספיקות", "ההצעה שלי היא שנודה בעובדות מספיקות"),
        136: ("כדי שתדחה את התיק ללא הרשעה.", "כדי שתדחי את התיק ללא הרשעה."),
        141: ("אתה רוצה זיכוי, עו״ד, אתה צריך משפט.", "את רוצה זיכוי, פרקליטה, את צריכה משפט."),
        147: ("משפט ח״ים כמובן.", "משפט מושבעים כמובן."),
        149: ("אני נוסע לאספן ביום רביעי.", "אני נוסעת לאספן ביום רביעי."),
        156: ("אתה מתכוון שזה לא מצחיק?", "את מתכוונת שזה לא מצחיק?"),
        754: ("הגענו, כבוד השופט.", "הגענו, כבוד השופטת."),
        761: ("נערער, כבוד השופט.", "נערער, כבוד השופטת."),
        767: ("כן, כבוד השופט.", "כן, כבוד השופטת."),
    }
}

def clean_he(text):
    return re.sub(r"[\u200e\u200f]", "", text).strip()

def apply_fixes():
    total_modified = 0
    for filename, cue_fixes in FIXES.items():
        filepath = SEASON_1_DIR / filename
        if not filepath.exists():
            print(f"[-] Missing: {filepath}")
            continue
        
        cues = parse_srt(str(filepath))
        cue_map = {c["idx"]: c for c in cues}
        modified_in_ep = 0
        
        for idx, (old_val, new_val) in cue_fixes.items():
            if idx not in cue_map:
                print(f"[-] Cue {idx} not found in {filename}")
                continue
            
            c = cue_map[idx]
            current_clean = clean_he(c["text"])
            clean_target = clean_he(old_val)
            
            if clean_target in current_clean:
                # Replace target within clean text
                updated_clean = current_clean.replace(clean_target, new_val)
                # Re-apply RLM to each line
                updated_lines = [apply_rlm(l) for l in updated_clean.splitlines()]
                c["text"] = "\n".join(updated_lines)
                modified_in_ep += 1
                print(f"[{filename}] Fixed cue #{idx}:\n   OLD: {clean_target}\n   NEW: {new_val}")
            else:
                print(f"[!] Target text mismatch in {filename} cue #{idx}:\n   Expected: {clean_target}\n   Actual:   {current_clean}")
        
        if modified_in_ep > 0:
            write_srt(cues, str(filepath))
            print(f"[+] Saved {modified_in_ep} fixes to {filename}\n")
            total_modified += modified_in_ep
        else:
            print(f"[*] No changes needed for {filename}\n")
            
    print(f"[=== DONE ===] Total cues surgically corrected across Season 1: {total_modified}")

if __name__ == "__main__":
    apply_fixes()
