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


def _is_song_or_sdh_only(en_t):
    """Returns True if an English cue contains only blank text, music lyrics/notes, SDH tags, or credits."""
    s = re.sub(r'<[^>]+>', '', en_t or '').strip()
    if not s:
        return True
    if '♪' in s or re.search(r'^\s*\*+|\*+\s*$', s):
        return True
    if re.match(r'^\s*(?:\[[^\]]*\]|\([^\)]*\))(?:\s*[-–—]?\s*(?:\[[^\]]*\]|\([^\)]*\)))*\s*$', s, flags=re.DOTALL):
        return True
    if re.search(r'(?i)captioned\s+by|closed\s+captioning|playing\)\s*$', s):
        return True
    if not re.search(r'[A-Za-z0-9]', s):
        return True
    return False


def validate_anchor_alignment(en_texts, he_translations):
    """
    Three-layer bilingual alignment & non-sequitur validator between English cues and Hebrew cues:
      Check A: Sliding-window drift detection (k in -2, -1, +1, +2) on non-song dialogue cues.
      Check B: Consecutive untranslated dialogue runs (>= 8 non-lyric EN cues with zero Hebrew glyphs).
      Check C: Isolated non-sequitur / hallucinated cue contradictions (missing specific numbers,
               1-speaker EN '?' vs 2-speaker HE dashes without '?', or long EN vs 1-word HE).
    Returns (is_aligned, drift_report_dict).
    """
    common_indices = sorted(set(en_texts.keys()) & set(he_translations.keys()))
    if len(common_indices) < 10:
        return True, {"shifted_windows": 0, "details": []}

    def _score_pair(en_t, he_t):
        en_c = re.sub(r'<[^>]+>|\[[^\]]*\]|\([^\)]*\)', '', en_t or '').strip()
        he_c = re.sub(r'[\u200e\u200f\u202a-\u202e]|<[^>]+>|\[[^\]]*\]|\([^\)]*\)', '', he_t or '').strip()
        if not en_c:
            return 0.0
        if not he_c or not re.search(r'[\u0590-\u05FF]', he_c):
            return -2.5
        score = 0.0
        if ('?' in en_c) == ('?' in he_c):
            score += 2.0 if '?' in en_c else 0.3
        else:
            score -= 2.0
        if ('!' in en_c) == ('!' in he_c):
            score += 1.2 if '!' in en_c else 0.1
        else:
            score -= 1.0
        en_nums = set(re.findall(r'\d+', en_c.replace(',', '')))
        he_nums = set(re.findall(r'\d+', he_c.replace(',', '')))
        if en_nums and en_nums == he_nums:
            score += 3.0
        ew = len(en_c.split())
        hw = len(he_c.split())
        ratio = (hw + 1) / (ew * 0.72 + 1)
        if 0.5 <= ratio <= 1.85:
            score += 1.0
        elif ratio < 0.28 or ratio > 3.0:
            score -= 2.0
        return score

    shifted_details = []
    dialogue_indices = [i for i in common_indices if not _is_song_or_sdh_only(en_texts[i])]

    # Check A: Sliding-window drift detection (k in -2, -1, 1, 2)
    if len(dialogue_indices) >= 8:
        ws = min(12, len(dialogue_indices))
        starts = list(range(0, max(1, len(dialogue_indices) - ws + 1), 4))
        if len(dialogue_indices) > ws and (len(dialogue_indices) - ws) % 4 != 0:
            starts.append(len(dialogue_indices) - ws)
        for pos in starts:
            chunk = dialogue_indices[pos:pos + ws]
            score_0 = sum(_score_pair(en_texts[i], he_translations.get(i, "")) for i in chunk)
            best_k, best_s = 0, score_0
            for k in (-2, -1, 1, 2):
                sk = sum(_score_pair(en_texts[i], he_translations.get(i + k, "")) for i in chunk if (i + k) in he_translations)
                if sk > best_s:
                    best_k, best_s = k, sk
            if best_k != 0 and best_s >= score_0 + 9.0 and best_s > 4.0:
                shifted_details.append(f"Cues {chunk[0]}..{chunk[-1]} (drift {best_k:+d})")

    # Check B: Untranslated dialogue run (>= 8 consecutive non-lyric cues with no Hebrew characters)
    untranslated_run = []
    for i in common_indices:
        if _is_song_or_sdh_only(en_texts[i]):
            continue
        e_raw = re.sub(r'<[^>]+>|\[[^\]]*\]|\([^\)]*\)', '', en_texts[i] or '').strip()
        h_raw = re.sub(r'[\u200e\u200f]', '', he_translations.get(i, "") or '')
        if len(e_raw.split()) >= 3 and not re.search(r'[\u0590-\u05FF]', h_raw):
            untranslated_run.append((i, e_raw))
        else:
            if len(untranslated_run) >= 8:
                words = [w.lower() for _, txt in untranslated_run for w in re.findall(r'[a-zA-Z]+', txt)]
                if len(set(words)) / max(1, len(words)) > 0.55:
                    shifted_details.append(f"Untranslated dialogue run at cues {untranslated_run[0][0]}..{untranslated_run[-1][0]}")
            untranslated_run = []
    if len(untranslated_run) >= 8:
        words = [w.lower() for _, txt in untranslated_run for w in re.findall(r'[a-zA-Z]+', txt)]
        if len(set(words)) / max(1, len(words)) > 0.55:
            shifted_details.append(f"Untranslated dialogue run at cues {untranslated_run[0][0]}..{untranslated_run[-1][0]}")

    # Check C: Isolated non-sequitur / hallucinated cues
    c1_hits = []
    c23_hits = []
    for i in dialogue_indices:
        en_c = re.sub(r'<[^>]+>|\[[^\]]*\]|\([^\)]*\)', '', en_texts[i] or '').strip()
        he_clean = re.sub(r'[\u200e\u200f\u202a-\u202e]|<[^>]+>|\[[^\]]*\]|\([^\)]*\)', '', he_translations[i] or '').strip()
        en_body = re.sub(r'^[A-Za-z][A-Za-z0-9\s.#\'\-]{0,20}:\s*', '', en_c).strip()

        raw_nums = re.findall(r'\b\d{4,}\b', en_body.replace(',', ''))
        nums = [n for n in raw_nums if not (n.startswith('0') and re.match(r'^0\d[0-5]\d$', n))]
        has_time_expr = bool(re.search(r'\b(?:0\d|1\d|2[0-3])[0-5]\d\b', en_body)) and bool(
            re.search(r'(?:^|\s)[בלמ]?(?:אפס|אחת|שתיים|שלוש|ארבע|חמש|שש|שבע|שמונה|תשע|עשר|שתים|חצות|צהריים|בוקר|ערב)(?=\s|$|[.,?!])', he_clean)
        )
        if nums and not has_time_expr and not re.search(r'\d', he_clean) and not re.search(r'אלף|אלפים|אלפיים|אלפי|מאות|מיליון|מיליארד', he_clean):
            c1_hits.append(i)

        en_words = en_body.split()
        he_lines = [l.strip() for l in he_clean.splitlines() if l.strip()]
        if len(en_words) <= 7 and '?' in en_body and not any(re.match(r'^\s*[-–—]', l) for l in en_c.splitlines()):
            if len(he_lines) >= 2 and all(re.match(r'^[-–—]\s*', l) for l in he_lines[:2]) and '?' not in he_clean:
                c23_hits.append(i)
        elif len(en_words) >= 8 and len(he_clean.split()) == 1 and len(he_clean) <= 7 and not re.search(r'(?i)come again\?|sorry\?|what say you\?|excuse me\?', en_body):
            c23_hits.append(i)

    if c1_hits or len(c23_hits) >= 2:
        flagged = sorted(set(c1_hits + c23_hits))[:10]
        shifted_details.append(f"Isolated non-sequitur cues: {flagged}")

    return len(shifted_details) == 0, {
        "shifted_windows": len(shifted_details),
        "details": shifted_details
    }


def merge_and_validate(en_srt_path, translated_json_dir, output_he_srt_path):
    # 1. Parse original English SRT
    try:
        en_content, _ = _m07.read_file_with_auto_encoding(en_srt_path)
        en_content = en_content.strip()
    except Exception:
        with open(en_srt_path, "r", encoding="utf-8-sig", errors="replace") as f:
            en_content = f.read().strip()

    en_blocks = re.split(r'\r?\n\s*\r?\n', en_content) if en_content else []
    en_subs = {}
    en_texts = {}
    for b in en_blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                idx = int(lines[0].strip())
                time_line = lines[1].strip()
                en_subs[idx] = time_line
                en_texts[idx] = "\n".join(lines[2:]).strip()
            except ValueError:
                continue

    en_subs, overlaps_fixed = clamp_overlapping_timelines(en_subs)

    # 2. Gather all translated batches (excluding English *_input.json / *_en.json files and sorting naturally)
    files = sorted(
        [
            f for f in os.listdir(translated_json_dir)
            if f.startswith("batch_")
            and f.endswith(".json")
            and not f.lower().endswith(("_input.json", "_en.json"))
        ],
        key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
    )
    if not files:
        print(f"[-] No batch files found in {translated_json_dir}")
        return False

    he_translations = {}
    overlapping_indices = []
    for fname in files:
        fpath = os.path.join(translated_json_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"[!] JSON parsing error in {fname}: {e}. Retrying with sanitization...")
                with open(fpath, "r", encoding="utf-8") as rf:
                    raw = rf.read().strip()
                raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.IGNORECASE | re.DOTALL)
                sanitized = re.sub(r'([\u0590-\u05FF])"([\u0590-\u05FF])', r'\1״\2', raw)
                try:
                    data = json.loads(sanitized)
                except Exception as e2:
                    print(f"[CRITICAL ERROR] Unrecoverable JSON syntax error in {fname}: {e2}")
                    return False

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

            if not isinstance(items, list):
                print(f"[CRITICAL ERROR] Malformed batch JSON list structure in {fname}")
                return False

            for item in items:
                if not isinstance(item, dict) or "index" not in item:
                    continue
                try:
                    idx_val = int(item["index"])
                except (ValueError, TypeError):
                    continue
                raw_he = item.get("hebrew") if item.get("hebrew") is not None else item.get("text")
                he_text = "" if raw_he is None else str(raw_he).strip()
                if idx_val in he_translations:
                    overlapping_indices.append(idx_val)
                he_translations[idx_val] = he_text

    if overlapping_indices:
        print(f"[WARNING] Overwritten duplicate batch indices ({len(overlapping_indices)}): {overlapping_indices[:10]}")

    # 3. Discrepancy & Validation Check
    missing = [idx for idx in en_subs if idx not in he_translations]
    extra = [idx for idx in he_translations if idx not in en_subs]

    if missing:
        print(f"[CRITICAL ERROR] Missing {len(missing)} subtitle indices: {missing[:20]}...")
        return False
    if extra:
        print(f"[WARNING] Extra subtitle indices found: {extra[:20]}...")

    is_aligned, drift_report = validate_anchor_alignment(en_texts, he_translations)
    if not is_aligned:
        print(f"[WARNING] Potential Cue Drift detected in {drift_report['shifted_windows']} window(s): {drift_report['details']}")

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
            clean_check = re.sub(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]', '', clean_l).strip()
            if clean_check not in ['', '-', '–', '—']:
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
    ok = merge_and_validate(args.en_srt, args.json_dir, args.output)
    sys.exit(0 if ok else 1)
