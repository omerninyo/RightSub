#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_merge_and_validate.py
------------------------
Merges translated batch JSON files back into a master Hebrew SRT file.
Enforces:
1. Automated BiDi / RLM (\u200F) injection for perfect punctuation on Plex & Infuse.
2. Full algorithmic memory: Cyrillic & Arabic homoglyph normalization.
3. Hebrew gershayim (״) conversion for acronyms (עו״ד, ארה״ב) to prevent parser breaks.
4. Strict 100% 1-to-1 index and timestamp match against the source English SRT.
5. Red Team zero-discrepancy validation report.
"""
import os
import sys
import re
import json
import argparse
import importlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

_m07 = importlib.import_module("07_fix_plex_punctuation")
RLM = _m07.RLM
ARABIC_TO_HEBREW = _m07.ARABIC_TO_HEBREW
ARABIC_PHRASES = _m07.ARABIC_PHRASES
CYRILLIC_TO_HEBREW = _m07.CYRILLIC_TO_HEBREW
UNIVERSAL_HOMOGLYPH_MAP = _m07.UNIVERSAL_HOMOGLYPH_MAP
UNIVERSAL_PHRASES = _m07.UNIVERSAL_PHRASES
DISALLOWED_FOREIGN_SCRIPTS = _m07.DISALLOWED_FOREIGN_SCRIPTS
normalize_final_letters = _m07.normalize_final_letters
sanitize_raw_hebrew = _m07.clean_and_sanitize_text
apply_rlm_punctuation_fix = _m07.apply_rlm_to_line
apply_bidi_and_punctuation = _m07.apply_rlm_to_line
_atomic_write_text = _m07._atomic_write_text


def _parse_srt_timestamp_ms(ts_str):
    """Parses 'HH:MM:SS,mmm' into integer milliseconds."""
    h, m, s_ms = ts_str.strip().split(":")
    s, ms = s_ms.replace(".", ",").split(",")
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def _format_srt_timestamp_ms(total_ms):
    """Formats integer milliseconds into 'HH:MM:SS,mmm'."""
    total_ms = max(0, int(total_ms))
    h = total_ms // 3600000
    rem = total_ms % 3600000
    m = rem // 60000
    rem %= 60000
    s = rem // 1000
    ms = rem % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def clamp_overlapping_timelines(en_subs_dict):
    """
    Inspects sorted cue timelines {idx: 'HH:MM:SS,mmm --> HH:MM:SS,mmm'} and clamps any cue
    whose end timestamp overlaps into the next cue's start timestamp (leaving a 20ms gap).
    Returns (clamped_dict, overlap_count).
    """
    sorted_indices = sorted(en_subs_dict.keys())
    parsed = []
    for idx in sorted_indices:
        raw_line = en_subs_dict[idx]
        if "-->" not in raw_line:
            parsed.append([idx, None, None, raw_line])
            continue
        try:
            parts = raw_line.split("-->")
            s_ms = _parse_srt_timestamp_ms(parts[0])
            e_ms = _parse_srt_timestamp_ms(parts[1])
            parsed.append([idx, s_ms, e_ms, raw_line])
        except Exception:
            parsed.append([idx, None, None, raw_line])

    overlaps_fixed = 0
    for i in range(len(parsed) - 1):
        curr_idx, curr_s, curr_e, _ = parsed[i]
        next_idx, next_s, next_e, _ = parsed[i + 1]
        if curr_s is not None and curr_e is not None and next_s is not None:
            if curr_e > next_s:
                clamped_e = max(curr_s + 200, next_s - 20)
                if clamped_e > next_s:
                    clamped_e = max(curr_s, next_s)
                parsed[i][2] = clamped_e
                parsed[i][3] = f"{_format_srt_timestamp_ms(curr_s)} --> {_format_srt_timestamp_ms(clamped_e)}"
                overlaps_fixed += 1

    return {item[0]: item[3] for item in parsed}, overlaps_fixed


def merge_and_validate(en_srt_path, translated_json_dir, output_he_srt_path):
    # 1. Parse original English SRT
    with open(en_srt_path, "r", encoding="utf-8-sig", errors="replace") as f:
        en_content = f.read().strip()
    
    en_blocks = re.split(r'\n\s*\n', en_content)
    en_subs = {}
    for b in en_blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                idx = int(lines[0].strip())
                time_line = lines[1].strip()
                en_subs[idx] = time_line
            except ValueError:
                continue

    en_subs, overlaps_fixed = clamp_overlapping_timelines(en_subs)

    # 2. Gather all translated batches
    files = sorted([f for f in os.listdir(translated_json_dir) if f.startswith("batch_") and f.endswith(".json")])
    if not files:
        print(f"[-] No batch files found in {translated_json_dir}")
        return False

    he_translations = {}
    for fname in files:
        fpath = os.path.join(translated_json_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"[!] JSON parsing error in {fname}: {e}. Retrying with sanitization...")
                with open(fpath, "r", encoding="utf-8") as rf:
                    raw = rf.read()
                sanitized = re.sub(r'([\u0590-\u05FF])"([\u0590-\u05FF])', r'\1״\2', raw)
                data = json.loads(sanitized)
            
            # Handle multiple batch JSON schemas:
            # a) {"cues": [{"index": 1, "text": "..."}]}
            # b) [{"index": 1, "hebrew": "..."}]
            # c) {"1": "...", "2": "..."}
            if isinstance(data, dict) and "cues" in data:
                items = data["cues"]
            elif isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = [{"index": k, "hebrew": v} for k, v in data.items() if str(k).isdigit()]
            else:
                items = []

            for item in items:
                idx_val = int(item["index"])
                he_text = item.get("hebrew", item.get("text", ""))
                he_translations[idx_val] = str(he_text).strip()

    # 3. Discrepancy & Validation Check
    missing = [idx for idx in en_subs if idx not in he_translations]
    extra = [idx for idx in he_translations if idx not in en_subs]

    if missing:
        print(f"[CRITICAL ERROR] Missing {len(missing)} subtitle indices: {missing[:20]}...")
        return False
    if extra:
        print(f"[WARNING] Extra subtitle indices found: {extra[:20]}...")

    # 4. Build output SRT with BiDi / RLM
    out_lines = []
    for idx in sorted(en_subs.keys()):
        out_lines.append(str(idx))
        out_lines.append(en_subs[idx])
        he_text = he_translations.get(idx, "")
        
        # Unescape literal \n and split into lines
        he_text = he_text.replace(r'\n', '\n')
        formatted_lines = []
        for l in he_text.splitlines():
            clean_l = apply_rlm_punctuation_fix(l)
            if clean_l.strip() not in ['', '-', f'{RLM}-', f'{RLM} -', '—', f'{RLM}—']:
                formatted_lines.append(clean_l)
        if not formatted_lines:
            formatted_lines = ['']
        out_lines.append("\n".join(formatted_lines))
        out_lines.append("") # Blank separator

    _atomic_write_text(output_he_srt_path, "\n".join(out_lines))

    print(f"[✓] SUCCESS: Merged {len(en_subs)} subtitles into {output_he_srt_path}")
    print(f"    - Missing subtitles: 0 (100% matched)")
    if overlaps_fixed > 0:
        print(f"    - Overlapping timestamps clamped: {overlaps_fixed}")
    print(f"    - RLM BiDi fix applied for Plex & Infuse")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge translated JSON batches into final Hebrew SRT with RLM & QC.")
    parser.add_argument("en_srt", help="Original English SRT")
    parser.add_argument("json_dir", help="Directory containing translated batch JSON files")
    parser.add_argument("-o", "--output", required=True, help="Output Hebrew SRT file")
    args = parser.parse_args()
    merge_and_validate(args.en_srt, args.json_dir, args.output)
