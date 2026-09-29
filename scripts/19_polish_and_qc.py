#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
19_polish_and_qc.py
--------------------
Semantic AI Polish & Subtitle QC Engine for RightSub.

Purpose:
Proofread, modernize, and quality-audit existing Hebrew subtitles against master English
dialogue without re-translating from scratch. Operates on the principle of Minimal Edit
Distance (preserving 85%-90% of intact human dialogue while correcting canon drift,
gender agreement errors, and literal machine idioms).

Key Features:
1. Bilingual Cue Alignment: Pairs English cues with Hebrew cues by sequence or timestamp overlap.
2. Franchise Lore & Canon Glossaries: Pre-loaded glossaries (Star Wars, LOTR, Marvel, etc.)
   plus dynamic TMDb entity and character gender ingestion.
3. Constrained Polish Prompt Contract: Instructs the LLM to return ONLY modified cues in JSON,
   saving 80%-85% token costs compared to full re-translation.
4. Deterministic Offline Heuristic Pass: Standalone or pre-pass canon corrections (0 AI tokens).
5. Multi-Backend Support: Local Ollama (Qwen/Llama) and Google Gemini API (gemini-2.5-flash).
6. Seed-Safe by Default: Creates `<stem>.he.polished.srt` (or backs up original before --in-place).
7. Diff Audit Report: Generates `<stem>_polish_diff.md` summarizing all edits with reasons.
"""

import os
import sys
import re
import json
import argparse
import shutil
import urllib.request
import urllib.parse
import urllib.error
import socket
from pathlib import Path

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from tmdb_client import parse_media_filename, fetch_media_metadata, is_tmdb_available
except (ImportError, ModuleNotFoundError):
    try:
        from scripts.tmdb_client import parse_media_filename, fetch_media_metadata, is_tmdb_available
    except Exception:
        parse_media_filename = None
        fetch_media_metadata = None
        is_tmdb_available = lambda *args, **kwargs: False

try:
    import importlib
    m18 = importlib.import_module("18_auto_pipeline")
    find_companion_hebrew_subtitle = m18.find_companion_hebrew_subtitle
    find_companion_english_subtitle = m18.find_companion_english_subtitle
    is_hebrew_file = m18.is_hebrew_file
    VIDEO_EXTENSIONS = m18.VIDEO_EXTENSIONS
except Exception:
    find_companion_hebrew_subtitle = lambda p: None
    find_companion_english_subtitle = lambda p: None
    is_hebrew_file = lambda p: False
    VIDEO_EXTENSIONS = {".mp4", ".mkv", ".m4v", ".avi", ".ts", ".mov", ".webm"}

try:
    import importlib
    m01 = importlib.import_module("01_extract_subtitles")
    extract_from_video = m01.extract_from_video
    discover_external_subtitles = m01.discover_external_subtitles
    clean_srt_tags = m01.clean_srt_tags
except Exception:
    extract_from_video = None
    discover_external_subtitles = None
    clean_srt_tags = None

try:
    import importlib
    m07 = importlib.import_module("07_fix_plex_punctuation")
    normalize_homoglyphs = getattr(m07, "normalize_homoglyphs", getattr(m07, "clean_and_sanitize_text", lambda t: t))
    clean_subtitles = getattr(m07, "clean_subtitles", lambda c, **kw: c)
    clean_line = getattr(m07, "clean_line", lambda l, **kw: l)
except Exception:
    normalize_homoglyphs = lambda t: t
    clean_subtitles = lambda c, **kw: c
    clean_line = lambda l, **kw: l

try:
    import importlib
    m00 = importlib.import_module("00_transcribe_audio")
    transcribe_audio = m00.transcribe_audio
    is_quicksubs_available = m00.is_quicksubs_available
except Exception:
    transcribe_audio = None
    is_quicksubs_available = lambda: False

try:
    import importlib
    m5 = importlib.import_module("05_merge_and_validate")
    apply_bidi_and_punctuation = m5.apply_bidi_and_punctuation
    RLM = m5.RLM
except Exception:
    RLM = "\u200F"
    def apply_bidi_and_punctuation(line):
        if not line:
            return line
        line = re.sub(r'([\u0590-\u05FF])"([\u0590-\u05FF])', r'\1״\2', line)
        if re.search(r'[\u0590-\u05FF]', line):
            line = re.sub(r'([\.!\?,:;\-\—\)»\]]+)$', f'{RLM}\\1', line)
            if not line.startswith(RLM):
                line = RLM + line
        return line

# Built-in franchise canonical glossaries & character gender hints
FRANCHISE_GLOSSARIES = {
    "star wars": {
        "canon_terms": [
            (r"(?<![א-ת])חרב\s*[-–—]?\s*הלייזר(?![א-ת])", "חרב האור", "מינוח קאנוני (Lightsaber = חרב אור ולא חרב לייזר)"),
            (r"(?<![א-ת])חרב\s*[-–—]?\s*לייזר(?![א-ת])", "חרב אור", "מינוח קאנוני (Lightsaber = חרב אור ולא חרב לייזר)"),
            (r"(?<![א-ת])חרבות\s*[-–—]?\s*הלייזר(?![א-ת])", "חרבות האור", "מינוח קאנוני (Lightsabers = חרבות אור)"),
            (r"(?<![א-ת])חרבות\s*[-–—]?\s*לייזר(?![א-ת])", "חרבות אור", "מינוח קאנוני (Lightsabers = חרבות אור)"),
            (r"(?<![א-ת])בז\s*אלף\s*השנים(?![א-ת])", "המילניום פלקון", "מינוח קאנוני (Millennium Falcon = המילניום פלקון ולא בז אלף השנים)"),
            (r"דארת\s*,\s*ויידא?ר", "דארת' ויידר", "תיקון איות ופסיק מיותר (דארת' ויידר)"),
            (r"דארת\.,", "דארת',", "תיקון שגיאת פיסוק (דארת',)"),
            (r"(?<![א-ת])ויידאר(?![א-ת])", "ויידר", "תיקון איות ארכאי (ויידר ולא ויידאר)"),
            (r"(?<![א-ת])הגרנד\s*מוף(?![א-ת])", "הגראנד מופ", "מינוח קאנוני (Grand Moff)"),
            (r"(?<![א-ת])גרנד\s*מוף(?![א-ת])", "גראנד מופ", "מינוח קאנוני (Grand Moff)"),
            (r"(?<![א-ת])כוכב\s*מוות(?![א-ת])", "כוכב המוות", "מינוח קאנוני (Death Star)"),
            (r"(?<![א-ת])חייל\s*סער(?![א-ת])", "לוחם סער", "מינוח קאנוני (Stormtrooper)"),
            (r"(?<![א-ת])חיילי\s*סער(?![א-ת])", "לוחמי סער", "מינוח קאנוני (Stormtroopers)"),
            (r"(?<![א-ת])הצד\s*החשוך(?![א-ת])", "הצד האפל", "מינוח קאנוני (Dark Side)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?מעשה\s*בראשית(?![א-ת])", r"\g<1>למעשה", "תיקון ביטוי שגוי (As a matter of fact = למעשה ולא מעשה בראשית)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?קאבתן(?![א-ת])", r"\g<1>קברניט", "תיקון תעתיק פונטי שגוי (Captain = קברניט/קפטן ולא קאבתן)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?מכלית\s*קרב(?![א-ת])", r"\g<1>חללית קרב", "מינוח מדויק (snub fighter = חללית קרב)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?קרן\s*משיכה(?![א-ת])", r"\g<1>קרן גרירה", "מינוח קאנוני (Tractor Beam = קרן גרירה ולא קרן משיכה)"),
            (r"(?<![א-ת])לשום\s+את(?![א-ת])", "לשים את", "תיקון שגיאת כתיב (לשים ולא לשום)"),
            (r"(?<![א-ת])מוחב\s+אותנו(?![א-ת])", "מושכת אותנו", "תיקון שגיאת כתיב (מושכת ולא מוחב)"),
            (r"(?<![א-ת])אובי\s*[-–—]?\s*וואן\s+קאנובי(?![א-ת])", "אובי-וואן קנובי", "תיקון איות קאנוני (קנובי ולא קאנובי)"),
            (r"(?<![א-ת])סי\s*[-–—]?\s*ת'?ריפיאו(?![א-ת])", "סי-ת'ריפיו", "תיקון איות קאנוני (C-3PO)"),
            (r"(?<![א-ת])ארטו\s*[-–—]?\s*דיטו(?![א-ת])", "ארטו-דיטו", "תיקון איות קאנוני (R2-D2)"),
        ],
        "characters": [
            {"name": "Princess Leia", "he_name": "הנסיכה ליאה", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Luke Skywalker", "he_name": "לוק סקייווקר", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Han Solo", "he_name": "האן סולו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Darth Vader", "he_name": "דארת' ויידר", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Obi-Wan Kenobi", "he_name": "אובי-וואן קנובי", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Grand Moff Tarkin", "he_name": "גראנד מופ טארקין", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "C-3PO", "he_name": "סי-ת'ריפיו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "R2-D2", "he_name": "ארטו-דיטו", "gender": "Male", "pronouns": "אתה/הוא"},
        ]
    },
    "lord of the rings": {
        "canon_terms": [
            (r"(?<![א-ת])טבעת\s*אחת(?![א-ת])", "הטבעת האחת", "מינוח קאנוני (The One Ring)"),
            (r"(?<![א-ת])ארץ\s*תיכונה(?![א-ת])", "הארץ התיכונה", "מינוח קאנוני (Middle-earth)"),
            (r"(?<![א-ת])בני\s*לילית(?![א-ת])", "עלפים", "מינוח קאנוני/תרגום מודרני (Elves)"),
        ],
        "characters": [
            {"name": "Frodo", "he_name": "פרודו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Gandalf", "he_name": "גנדלף", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Galadriel", "he_name": "גלדריאל", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Arwen", "he_name": "ארוון", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Eowyn", "he_name": "איאווין", "gender": "Female", "pronouns": "את/היא"},
        ]
    },
    "marvel": {
        "canon_terms": [
            (r"(?<![א-ת])אבני\s*אינסוף(?![א-ת])", "אבני האינסוף", "מינוח קאנוני (Infinity Stones)"),
        ],
        "characters": [
            {"name": "Natasha Romanoff", "he_name": "נטשה רומנוף", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Wanda Maximoff", "he_name": "וונדה מקסימוף", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Carol Danvers", "he_name": "קרול דנברס", "gender": "Female", "pronouns": "את/היא"},
        ]
    }
}

def parse_srt(path):
    """Parses an SRT file and returns list of (index, timing, text)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()
    blocks = re.split(r'\n\s*\n', content)
    cues = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                idx = int(lines[0].strip())
                timing = lines[1].strip()
                text = '\n'.join(lines[2:])
                cues.append({
                    "index": idx,
                    "timing": timing,
                    "text": text
                })
            except ValueError:
                continue
    return cues

def time_to_ms(time_str):
    """Converts 00:00:00,000 to milliseconds."""
    try:
        parts = time_str.split('-->')
        start = parts[0].strip()
        h, m, s_ms = start.split(':')
        s, ms = s_ms.replace('.', ',').split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    except Exception:
        return 0

def parse_timing_ms(time_str):
    """Converts '00:00:00,000 --> 00:00:00,000' to (start_ms, end_ms)."""
    try:
        parts = time_str.split('-->')
        start = parts[0].strip()
        h, m, s_ms = start.split(':')
        s, ms = s_ms.replace('.', ',').split(',')
        start_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
        end = parts[1].strip()
        h, m, s_ms = end.split(':')
        s, ms = s_ms.replace('.', ',').split(',')
        end_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
        return start_ms, end_ms
    except Exception:
        return 0, 0

def align_bilingual_cues(en_cues, he_cues):
    """
    Pairs English master cues with Hebrew target cues anchored strictly on Hebrew timings.
    Ensures zero cue starvation and zero off-by-one drift even when segmentation differs.
    """
    he_by_idx = {c["index"]: c for c in he_cues}
    en_by_idx = {c["index"]: c for c in en_cues}

    aligned = []
    
    # 1. Exact 1:1 match if counts match and timestamps align within 2.5s
    if len(en_cues) == len(he_cues) and all(c["index"] in he_by_idx for c in en_cues):
        all_aligned = True
        for en in en_cues:
            he = he_by_idx[en["index"]]
            if abs(time_to_ms(en["timing"]) - time_to_ms(he["timing"])) > 2500:
                all_aligned = False
                break
        if all_aligned:
            for en in en_cues:
                he = he_by_idx[en["index"]]
                aligned.append({
                    "index": en["index"],
                    "timing": he["timing"],
                    "en": en["text"],
                    "he": he["text"],
                    "en_index": en["index"]
                })
            return aligned

    # 2. Resilient Anchor Matching (Hebrew-Centric Timestamp Overlap & Proximity)
    en_times = []
    for en in en_cues:
        s, e = parse_timing_ms(en["timing"])
        en_times.append((s, e, en))

    for he in he_cues:
        hs, he_end = parse_timing_ms(he["timing"])
        best_en = None
        best_overlap = 0
        best_dist = float("inf")

        for es, ee, en in en_times:
            # Calculate timestamp overlap in ms
            overlap = max(0, min(he_end, ee) - max(hs, es))
            dist = abs(hs - es)
            if overlap > best_overlap:
                best_overlap = overlap
                best_en = en
            elif best_overlap == 0 and dist < best_dist and dist <= 3000:
                best_dist = dist
                best_en = en

        en_text = best_en["text"] if best_en else ""
        aligned.append({
            "index": he["index"],
            "timing": he["timing"],
            "en": en_text,
            "he": he["text"],
            "en_index": best_en["index"] if best_en else None
        })

    # 3. Annotate split cues: detect consecutive Hebrew cues sharing the same English master cue
    i = 0
    while i < len(aligned):
        curr_en_idx = aligned[i].get("en_index")
        curr_en_text = (aligned[i].get("en") or "").strip()
        if curr_en_text and (curr_en_idx is not None or curr_en_text):
            j = i
            while j < len(aligned) and (
                (curr_en_idx is not None and aligned[j].get("en_index") == curr_en_idx) or
                (curr_en_idx is None and (aligned[j].get("en") or "").strip() == curr_en_text)
            ):
                j += 1
            total_parts = j - i
            if total_parts > 1:
                for part_idx, k in enumerate(range(i, j), start=1):
                    aligned[k]["split_part"] = f"{part_idx}/{total_parts}"
            i = j
        else:
            i += 1

    return aligned

def detect_franchise(title, overview=""):
    """Detects if title belongs to a supported franchise with canonical glossary."""
    combo = re.sub(r'[\._\-+]+', ' ', f"{title} {overview}".lower())
    for key, data in FRANCHISE_GLOSSARIES.items():
        if key in combo:
            return key, data
    if "star wars" in combo or "4k77" in combo or "4k80" in combo or "4k83" in combo or "skywalker" in combo:
        return "star wars", FRANCHISE_GLOSSARIES["star wars"]
    return None, None

def run_deterministic_canon_pass(aligned_cues, franchise_data):
    """
    Executes a deterministic, offline regex pass to fix established canon terms
    even without an LLM backend (0 tokens).
    """
    if not franchise_data:
        return {}

    modifications = {}
    canon_terms = franchise_data.get("canon_terms", [])
    
    for item in aligned_cues:
        idx = item["index"]
        current_he = item["he"]
        modified = current_he
        reasons = []

        for pattern, replacement, reason in canon_terms:
            if re.search(pattern, modified):
                modified = re.sub(pattern, replacement, modified)
                reasons.append(reason)

        if modified != current_he:
            modifications[idx] = {
                "index": idx,
                "original_he": current_he,
                "polished_he": modified,
                "reason": " + ".join(reasons)
            }

    return modifications

def build_polish_prompt(aligned_batch, title, franchise_name=None, franchise_data=None, characters=None, overview="", genres=None):
    """Builds a constrained, high-efficiency Polish prompt with rich context & characters."""
    glossary_lines = []
    if franchise_data:
        glossary_lines.append(f"FRANCHISE CANON GUIDELINES ({franchise_name.upper()}):")
        for pat, rep, reas in franchise_data.get("canon_terms", []):
            clean_term = pat.replace(r"\b", "").replace(r"\s*", " ")
            glossary_lines.append(f"- '{clean_term}' MUST BE TRANSLATED AS '{rep}' ({reas})")

    context_lines = []
    if genres:
        context_lines.append(f"Genre: {', '.join(genres) if isinstance(genres, list) else genres}")
    if overview:
        context_lines.append(f"Context & Plot Synopsis: {overview}")

    char_lines = []
    if characters:
        char_lines.append("CONFIRMED CHARACTERS & GENDERS (Ground-Truth Context):")
        for c in characters[:18]:
            c_name = c.get("name", "")
            c_he = c.get("he_name") or c.get("hebrew_name") or c_name
            c_gen = c.get("gender", "Unknown")
            c_pro = c.get("pronouns", "")
            char_lines.append(f"- {c_name} ({c_he}): Gender = {c_gen} (Hebrew 2nd/3rd person: {c_pro})")

    batch_input = [
        {
            **({"index": c["index"], "en": c["en"], "current_he": c["he"]}),
            **({"split_part": c["split_part"]} if c.get("split_part") else {})
        }
        for c in aligned_batch
    ]

    context_block = "\n".join(context_lines)
    prompt = f"""You are a professional Hebrew subtitling proofreader and quality-assurance editor.
Title: {title}
{context_block}

TASK:
Review the following existing Hebrew subtitles against the master English dialogue.
Your objective is to fix semantic errors, canon inconsistencies, and gender mismatches.

CRITICAL INSTRUCTIONS:
1. THE CONSERVATION RULE (CRITICAL):
   - If the current Hebrew line is accurate, natural, and grammatically correct — DO NOT CHANGE IT.
   - Retain 85% to 90% of intact lines. Do NOT rewrite for cosmetic preference.
2. CANON & LORE TERMS:
   - Correct outdated, clumsy, or wrong franchise terms (e.g. 'חרב לייזר' -> 'חרב אור').
3. GENDER AGREEMENT & DIRECT ADDRESS:
   - Ensure 2nd-person pronouns and verbs ('את' vs 'אתה') match the confirmed gender of the addressee.
   - When Han or Luke speaks to Princess Leia, use feminine verbs ('שמעת', 'ראית', 'את').
4. FLOW & IDIOM MODERNIZATION:
   - Fix clumsy literal machine translations into natural, idiomatic Hebrew dialogue.
5. SUBTITLE CONSTRAINTS:
   - Maximum 38-40 characters per line, maximum 2 lines per cue block.
6. STRICT TIMELINE INTEGRITY & SPLIT CUES (ZERO FORWARD DRIFT):
   - Never merge dialogue across multiple cues, and never shift lines from one cue to another.
   - Each cue must contain ONLY the dialogue spoken during that specific cue.
   - SPLIT CUES ('split_part'): When consecutive cues share an English reference (indicated by 'split_part': '1/2', '2/2'):
     * Part 1/2 must contain ONLY the first segment of the dialogue.
     * Part 2/2 must contain ONLY the continuation/concluding segment of the dialogue.
     * STRICTLY FORBIDDEN: Translating the complete sentence into Part 1/2 and then anticipating/guessing upcoming film dialogue for Part 2/2!
     * NEVER pull dialogue from subsequent scenes or upcoming cues into a split cue.
     * If the existing Hebrew cues already naturally divide the dialogue, PRESERVE THEM (The Conservation Rule).
7. NEVER DELETE CUES (NO EMPTY CUES):
   - 'polished_he' must NEVER be empty or whitespace.
   - You are strictly forbidden from returning empty cues ("").
   - If a cue requires no changes, leave it out of the 'cues' array completely.
8. HEBREW CHARACTERS ONLY:
   - Output must contain only valid Hebrew characters, numbers, and standard punctuation. Never output Arabic or foreign characters.
9. NATURAL IDIOMS & PROPER HEBREW VOCABULARY:
   - Translate English idioms by their true Hebrew meaning, not literal words. E.g. 'As a matter of fact' -> 'למעשה' or 'למען האמת' (NEVER 'מעשה בראשית').
   - Sci-Fi & Military: 'snub fighter' -> 'חללית קרב זעירה' or 'קרבית' (NEVER 'מכלית קרב'), 'tractor beam' -> 'קרן גרירה' (NEVER 'קרן משיכה').
   - Rank & Titles: 'captain' -> 'קברניט' or 'קפטן' (NEVER Arabic-influenced transliterations like 'קאבתן').
   - Common verbs: use proper Hebrew verb forms e.g. 'לשים' (never 'לשום'), 'מושכת' (never 'מוחב').

{chr(10).join(glossary_lines)}
{chr(10).join(char_lines)}

INPUT BATCH:
{json.dumps(batch_input, ensure_ascii=False, indent=2)}

OUTPUT FORMAT:
Return ONLY a valid JSON object containing an array of cues that were ACTUALLY MODIFIED.
If no cues in this batch need changes, return {{"cues": []}}.
Do NOT include cues that were left unchanged!

JSON SCHEMA:
```json
{{
  "cues": [
    {{
      "index": 142,
      "original_he": "חרב הלייזר של אביך. זה הנשק של אביר ג'דיי.",
      "polished_he": "חרב האור של אביך. זהו נשקו של אביר ג'דיי.",
      "reason": "מינוח קאנוני (חרב אור) ותחביר משופר"
    }}
  ]
}}
```"""
    return prompt

def extract_json_payload(raw_text):
    """Extracts and parses JSON object from LLM response text, safely stripping markdown fences or wrapping."""
    if isinstance(raw_text, dict):
        return raw_text
    if not isinstance(raw_text, str):
        return {}

    text = raw_text.strip()

    # Direct parse attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # Extract outermost { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Strip markdown code fences (```json ... ```)
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return json.loads(text)

_cached_gemini_models = None
_active_working_model = None

def get_available_gemini_models(api_key):
    """Discovers active models for this API key via Google Generative Language API, prioritizing Flash models."""
    global _cached_gemini_models
    if _cached_gemini_models is not None:
        return _cached_gemini_models

    discovered = []
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "x-goog-api-key": api_key, "User-Agent": "RightSub/1.3"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models", []):
                name = m.get("name", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    clean = name.replace("models/", "")
                    discovered.append(clean)
    except Exception:
        pass

    def model_priority(m_name):
        m_lower = m_name.lower()
        if "gemini-3.5-flash" in m_lower and "lite" not in m_lower:
            return 100
        if "gemini-3.5-flash-lite" in m_lower:
            return 95
        if "gemini-flash-latest" in m_lower:
            return 90
        if "gemini-3.6-flash" in m_lower:
            return 85
        if "gemini-3.7-flash" in m_lower:
            return 80
        if "gemini-3.8-flash" in m_lower:
            return 75
        if "gemini-3.1-flash-lite" in m_lower:
            return 70
        if "gemini-flash-lite-latest" in m_lower:
            return 65
        if "flash" in m_lower:
            return 50
        return 10

    if discovered:
        discovered.sort(key=model_priority, reverse=True)
        _cached_gemini_models = discovered
        return _cached_gemini_models

    # Lightweight, high-throughput waterfall cascade hierarchy starting with 3.5-flash
    _cached_gemini_models = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash",
        "gemini-3.1-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    return _cached_gemini_models

def query_gemini_api(prompt, api_key=None, model=None):
    """Calls Google Gemini API via standard library urllib with dynamic model discovery and cascade fallback."""
    global _active_working_model

    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        config_path = Path.home() / ".config" / "rightsub" / "config.json"
        if config_path.is_file():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                key = data.get("gemini_api_key") or data.get("GEMINI_API_KEY")
            except Exception:
                pass
    if not key:
        raise ValueError("Gemini API key not found. Run 'rightsub config' or pass --api-key.")

    available_models = get_available_gemini_models(key)

    # If user did not force a specific model, prefer the model that already succeeded previously
    if model:
        preferred_model = model
    elif _active_working_model and _active_working_model in available_models:
        preferred_model = _active_working_model
    else:
        preferred_model = available_models[0] if available_models else "gemini-3.5-flash"

    models_to_try = [preferred_model]
    for fallback in available_models:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    # Standard clean payload without restrictive responseMimeType to prevent HTTP 400 on models without native json mode flag
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2
        }
    }
    raw_data = json.dumps(payload).encode("utf-8")

    last_error = None
    for m in models_to_try:
        model_path = m if m.startswith("models/") else f"models/{m}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={key}"
        req = urllib.request.Request(
            url,
            data=raw_data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": key,
                "User-Agent": "RightSub/1.3"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))

            candidates = res_json.get("candidates", [])
            if not candidates:
                last_error = f"Model '{m}' returned no candidates"
                continue

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            # Filter out thinking/reasoning parts and extract text safely
            text_parts = []
            for p in parts:
                if isinstance(p, dict):
                    if p.get("thought") is True:
                        continue
                    if "text" in p and p["text"]:
                        text_parts.append(p["text"])

            if not text_parts:
                for p in parts:
                    if isinstance(p, dict) and "text" in p and p["text"]:
                        text_parts.append(p["text"])

            text = "\n".join(text_parts).strip()
            if not text:
                last_error = f"Model '{m}' returned empty text output"
                continue

            parsed = extract_json_payload(text)
            # Lock onto the successful model for subsequent batches
            _active_working_model = m
            return parsed
        except urllib.error.HTTPError as e:
            err_msg = ""
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                err_msg = str(e)

            # Retryable cascade conditions: 404 (not found/deprecated), 429 (quota), 500/502/503/504 (overloaded/server),
            # or 400 model feature limitation (e.g. JSON mode not enabled)
            is_cascadeable = (e.code in (400, 404, 429, 500, 502, 503, 504)) or any(
                term in err_msg.lower() for term in (
                    "quota", "overloaded", "not found", "no longer available",
                    "resource_exhausted", "not enabled for this model", "not supported"
                )
            )

            if is_cascadeable and e.code not in (401, 403) and "api_key_invalid" not in err_msg.lower():
                last_error = f"Model '{m}' unavailable (HTTP {e.code}): {err_msg}"
                continue
            elif e.code in (401, 403) or "api_key_invalid" in err_msg.lower():
                raise RuntimeError(f"Authentication/Permission error (HTTP {e.code}): {err_msg}")
            else:
                last_error = f"Google API HTTP {e.code} on '{m}': {err_msg}"
                continue
        except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
            err_msg = str(e)
            last_error = f"Model '{m}' timed out or connection failed: {err_msg}"
            continue
        except Exception as e:
            last_error = str(e)
            raise e

    raise RuntimeError(f"Gemini API request failed across models ({', '.join(models_to_try)}): {last_error}")



def query_ollama_api(prompt, model="qwen2.5:7b", url="http://localhost:11434"):
    """Calls Ollama generate API with format='json'."""
    gen_url = f"{url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2}
    }
    raw_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        gen_url,
        data=raw_data,
        headers={"Content-Type": "application/json", "User-Agent": "RightSub/1.2"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
    
    response_str = res_json.get("response", "")
    return extract_json_payload(response_str)

def generate_diff_report(title, total_cues, modifications, output_report_path, en_map=None):
    """Generates a clean, comprehensive Markdown Diff Audit Report."""
    en_map = en_map or {}
    modified_count = len(modifications)
    preserved_count = total_cues - modified_count
    preserved_pct = (preserved_count / total_cues * 100) if total_cues > 0 else 100.0
    modified_pct = (modified_count / total_cues * 100) if total_cues > 0 else 0.0

    lines = [
        f"# 📋 RightSub Polish & QC Audit Report — {title}",
        "",
        f"- **סך כל הכתוביות שנבדקו:** {total_cues:,}",
        f"- **כתוביות מקור שנשמרו ללא שינוי (Conservation):** {preserved_count:,} ({preserved_pct:.1f}%)",
        f"- **כתוביות שלוטשו ותוקנו:** {modified_count:,} ({modified_pct:.1f}%)",
        "",
        "### פירוט השינויים שבוצעו:",
        "| בלוק (#) | אנגלית מקורית | תרגום קודם | תרגום משופר ומלוטש | סיבת התיקון |",
        "| :---: | :--- | :--- | :--- | :--- |"
    ]

    for idx in sorted(modifications.keys()):
        m = modifications[idx]
        orig_en = en_map.get(idx, "").replace("\n", " ").replace("|", "\\|")
        old_he = m["original_he"].replace("\n", " ").replace("|", "\\|")
        new_he = m["polished_he"].replace("\n", " ").replace("|", "\\|")
        reason = m.get("reason", "הגהה וליטוש").replace("|", "\\|")
        lines.append(f"| **#{idx}** | {orig_en} | {old_he} | {new_he} | {reason} |")

    lines.append("")
    lines.append("---")
    lines.append("*Report automatically generated by RightSub Semantic AI Polish Engine (`rightsub polish`).*")
    lines.append("")

    report_content = "\n".join(lines)
    Path(output_report_path).write_text(report_content, encoding="utf-8")
    return report_content

def write_mastered_srt(cues, output_path):
    """Writes cues to SRT file with Plex/Infuse RLM, ad cleaning, and UTF-8 encoding."""
    out_blocks = []
    for c in cues:
        idx = c["index"]
        timing = c["timing"]
        raw_text = c["text"]
        
        # Clean ads/promotions if any
        if clean_line:
            raw_text = clean_line(raw_text, clean_ads=True)
            
        # Homoglyph normalization
        raw_text = normalize_homoglyphs(raw_text)
        
        # Apply Plex/Infuse BiDi RLM mastering to each line
        lines = [apply_bidi_and_punctuation(l) for l in raw_text.splitlines() if l.strip()]
        clean_text = "\n".join(lines)
        if clean_text:
            out_blocks.append(f"{idx}\n{timing}\n{clean_text}")

    content = "\n\n".join(out_blocks) + "\n"
    Path(output_path).write_text(content, encoding="utf-8")

def polish_target(target, en_path=None, args=None):
    """
    Main execution function for polishing a subtitle file or video container.
    Supports:
    1. Video files (.mkv, .mp4, .avi, etc.): Automatically extracts or finds companion
       Hebrew & English subtitles, fetches TMDb context, and polishes seamlessly.
    2. Subtitle files (.he.srt, .srt): Polishes Hebrew subtitle with automatic companion
       English discovery (from disk or from adjacent video containers).
    """
    target_path = Path(target).resolve()
    if not target_path.exists():
        print(f"[-] Target path not found: {target_path}")
        return False

    is_video = target_path.suffix.lower() in VIDEO_EXTENSIONS
    video_path = target_path if is_video else None
    he_path = None
    
    if is_video:
        print(f"\n=======================================================")
        print(f"  💎 RightSub Semantic AI Polish & QC Engine")
        print(f"=======================================================")
        print(f"[*] Video Media Target: {target_path.name}")
        
        # 1. Find companion Hebrew subtitle
        he_cand = find_companion_hebrew_subtitle(target_path)
        if he_cand and he_cand.is_file():
            he_path = he_cand
            print(f"[+] Found external Hebrew subtitle: {he_path.name}")
        else:
            # Try extracting embedded Hebrew subtitle from video
            extracted_he = target_path.parent / f"{target_path.stem}.he.srt"
            if extract_from_video:
                print(f"[*] Searching for embedded Hebrew subtitle track in {target_path.name}...")
                ok, status = extract_from_video(target_path, output_srt=extracted_he, lang="heb")
                if ok and extracted_he.is_file() and extracted_he.stat().st_size > 0:
                    he_path = extracted_he
                    print(f"[✓] Extracted embedded Hebrew subtitle: {he_path.name}")
                    
        if not he_path or not he_path.is_file():
            print(f"[-] No companion or embedded Hebrew subtitle found for '{target_path.name}'.")
            print(f"    To translate from scratch, use: rightsub auto \"{target_path}\"")
            return False
            
        # 2. Find or extract companion English subtitle
        if not en_path:
            en_cand = find_companion_english_subtitle(target_path)
            if en_cand and en_cand.is_file():
                en_path = en_cand
                print(f"[+] Found external English master: {en_path.name}")
            elif extract_from_video:
                extracted_en = target_path.parent / f"{target_path.stem}.en.srt"
                print(f"[*] Searching for embedded English master track in {target_path.name}...")
                ok, status = extract_from_video(target_path, output_srt=extracted_en, lang="eng", fallback_transcribe=True)
                if ok and extracted_en.is_file() and extracted_en.stat().st_size > 0:
                    en_path = extracted_en
                    print(f"[✓] Extracted embedded English master: {en_path.name}")
    else:
        he_path = target_path
        print(f"\n=======================================================")
        print(f"  💎 RightSub Semantic AI Polish & QC Engine")
        print(f"=======================================================")
        print(f"[*] Hebrew Target: {he_path.name}")
        
        # Check if companion video exists in same directory
        for ext in VIDEO_EXTENSIONS:
            cand_video = he_path.parent / f"{he_path.stem.replace('.he', '').replace('.polished', '')}{ext}"
            if cand_video.is_file():
                video_path = cand_video
                break
                
        # Discover English counterpart
        if not en_path:
            for ext in [".en.srt", ".eng.srt", ".english.srt"]:
                cand = he_path.parent / f"{he_path.stem.replace('.he', '').replace('.polished', '')}{ext}"
                if cand.is_file():
                    en_path = cand
                    break
            if not en_path:
                alt_cand = he_path.with_suffix(".en.srt")
                if alt_cand.is_file():
                    en_path = alt_cand
            # If still no English subtitle, but we found a companion video, extract from video!
            if not en_path and video_path and extract_from_video:
                extracted_en = he_path.parent / f"{video_path.stem}.en.srt"
                print(f"[*] Extracting embedded English master from companion video {video_path.name}...")
                ok, status = extract_from_video(video_path, output_srt=extracted_en, lang="eng")
                if ok and extracted_en.is_file():
                    en_path = extracted_en

    if en_path:
        en_path = Path(en_path).resolve()
        print(f"[*] English Master: {en_path.name}")
    else:
        print(f"[!] Warning: No companion English subtitle found. Polish will run on Hebrew standalone rules.")

    # 2. Parse Cues
    he_cues = parse_srt(he_path)
    en_cues = parse_srt(en_path) if en_path else []
    print(f"[+] Loaded {len(he_cues)} Hebrew cues ({len(en_cues)} English cues)")

    if not he_cues:
        print("[-] Hebrew subtitle contains 0 cues. Aborting.")
        return False

    # 3. Bilingual Alignment
    aligned = align_bilingual_cues(en_cues, he_cues) if en_cues else [
        {"index": c["index"], "timing": c["timing"], "en": "", "he": c["text"]}
        for c in he_cues
    ]
    en_map = {item["index"]: item["en"] for item in aligned}

    # 4. Detect Media Metadata & Franchise Lore
    title = getattr(args, "title", None)
    sample_name = video_path.name if video_path else he_path.name
    if not title:
        if parse_media_filename:
            parsed = parse_media_filename(sample_name)
            title = parsed.get("title") or sample_name.replace(".he", "").replace(".polished", "")
        else:
            title = sample_name.replace(".he", "").replace(".polished", "")

    franchise_name, franchise_data = detect_franchise(title)
    if franchise_name:
        print(f"[+] Franchise Lore Detected: {franchise_name.upper()} (Enforcing canonical terms)")

    # 5. Ingest Translation Bible & TMDb Context
    characters = []
    overview = ""
    genres = []

    # Check for Translation Bible (explicit argument or companion translation_bible.json)
    bible_arg = getattr(args, "bible", None)
    bible_file = None
    if bible_arg:
        bp = Path(bible_arg).resolve()
        if bp.is_file():
            bible_file = bp
        elif bp.is_dir() and (bp / "translation_bible.json").is_file():
            bible_file = bp / "translation_bible.json"
    else:
        local_cand = he_path.parent / "translation_bible.json"
        if local_cand.is_file():
            bible_file = local_cand

    if bible_file:
        try:
            b_data = json.loads(bible_file.read_text(encoding="utf-8"))
            b_meta = b_data.get("metadata", {})
            overview = b_meta.get("overview") or overview
            genres = b_meta.get("genres") or genres
            for c in b_data.get("characters", []):
                characters.append({
                    "name": c.get("name", ""),
                    "he_name": c.get("hebrew_name") or c.get("he_name", ""),
                    "gender": c.get("gender", "unknown"),
                    "pronouns": c.get("pronouns", "")
                })
            print(f"[✓] Translation Bible Loaded: {bible_file.name} ({len(characters)} characters with confirmed context)")
        except Exception as e:
            print(f"[!] Bible loading notice: {e}")

    # Query TMDb for ground truth metadata & cast if not already populated or if TMDb available
    if fetch_media_metadata and is_tmdb_available(getattr(args, "api_key", None)):
        try:
            print(f"[*] Querying TMDb for '{title}' ground-truth metadata & cast...")
            tmdb_meta = fetch_media_metadata(filepath=he_path, title=title, api_key=getattr(args, "api_key", None))
            if tmdb_meta and tmdb_meta.get("success"):
                tmdb_chars = tmdb_meta.get("characters", [])
                overview = tmdb_meta.get("overview") or overview
                genres = tmdb_meta.get("genres") or genres
                # Merge TMDb characters
                existing_names = {c["name"].lower() for c in characters if c.get("name")}
                added = 0
                for tc in tmdb_chars:
                    if tc["name"].lower() not in existing_names:
                        characters.append(tc)
                        existing_names.add(tc["name"].lower())
                        added += 1
                print(f"[✓] TMDb Matched: '{tmdb_meta.get('title')}' (Resolved {len(tmdb_chars)} cast members, overview & genres)")
        except Exception as e:
            print(f"[!] TMDb query notice: {e}")

    # Inject franchise characters if missing from TMDb/Bible
    if franchise_data and "characters" in franchise_data:
        existing_names = {c["name"].lower() for c in characters if c.get("name")}
        for fc in franchise_data["characters"]:
            if fc["name"].lower() not in existing_names:
                characters.append(fc)
                existing_names.add(fc["name"].lower())

    if characters:
        print(f"[+] Active Character Bible: {len(characters)} confirmed character roles.")

    # 6. Deterministic Heuristic Canon Pass (Offline baseline, 0 tokens)
    modifications = run_deterministic_canon_pass(aligned, franchise_data)
    if modifications:
        print(f"[✓] Offline Canon Pass identified {len(modifications)} terminology corrections.")

    # 7. AI Polish Pass (if backend requested / available)
    use_ollama = getattr(args, "ollama", False)
    use_gemini = getattr(args, "gemini", False) or bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    offline_only = getattr(args, "offline_canon_only", False)

    if not offline_only and (use_ollama or use_gemini):
        raw_bs = getattr(args, "batch_size", 60)
        batch_size = raw_bs if (isinstance(raw_bs, int) and not isinstance(raw_bs, bool) and raw_bs > 0) else 60
        raw_model = getattr(args, "model", None)
        model = raw_model if (isinstance(raw_model, str) and raw_model.strip()) else None

        backend_model = model or ("qwen2.5:7b" if use_ollama else "gemini-3.5-flash")
        backend_name = f"Ollama ({backend_model})" if use_ollama else f"Gemini ({backend_model})"
        print(f"[*] Running Semantic AI Proofreader via {backend_name}...")

        total_batches = (len(aligned) + batch_size - 1) // batch_size
        consecutive_errors = 0

        # Build forward dialogue lookup to detect and reject anticipation drift
        next_en_map = {}
        for i in range(len(aligned) - 1):
            curr_item = aligned[i]
            curr_en = (curr_item.get("en") or "").strip()
            candidates = []
            for j in range(i + 1, min(i + 5, len(aligned))):
                cand_en = (aligned[j].get("en") or "").strip()
                if cand_en and cand_en.lower() != curr_en.lower() and cand_en not in candidates:
                    candidates.append(cand_en)
            if candidates:
                next_en_map[curr_item["index"]] = candidates

        for b_idx in range(0, len(aligned), batch_size):
            batch = aligned[b_idx:b_idx + batch_size]
            if not batch:
                continue
            b_num = (b_idx // batch_size) + 1
            print(f"    -> Processing batch {b_num}/{total_batches} (cues {batch[0]['index']}..{batch[-1]['index']})...", end="", flush=True)

            prompt = build_polish_prompt(batch, title, franchise_name, franchise_data, characters, overview=overview, genres=genres)

            try:
                if use_ollama:
                    ollama_model = model or "qwen2.5:7b"
                    res = query_ollama_api(prompt, model=ollama_model)
                else:
                    gemini_model = model or "gemini-3.5-flash"
                    raw_api_key = getattr(args, "api_key", None)
                    api_key = raw_api_key if isinstance(raw_api_key, str) else None
                    res = query_gemini_api(prompt, api_key=api_key, model=gemini_model)

                batch_cues = res.get("cues", []) if isinstance(res, dict) else []
                valid_count = 0
                for mod in batch_cues:
                    idx = mod.get("index")
                    if idx not in en_map:
                        continue
                    polished_text = (mod.get("polished_he") or "").strip()
                    if not polished_text:
                        continue

                    # Anticipation Drift Guard:
                    # Reject edit if the LLM's reason indicates it anticipated upcoming dialogue instead of the current cue
                    reason = (mod.get("reason") or "").strip().lower()
                    upcoming_en_lines = next_en_map.get(idx, [])
                    is_anticipation_drift = False

                    for up_en in upcoming_en_lines:
                        clean_up = re.sub(r'[^\w\s]', '', up_en).lower()
                        up_words = clean_up.split()
                        if len(up_words) >= 3:
                            for w_i in range(len(up_words) - 2):
                                trigram = " ".join(up_words[w_i:w_i + 3])
                                if trigram in reason:
                                    is_anticipation_drift = True
                                    break
                        elif clean_up and clean_up in reason:
                            is_anticipation_drift = True

                        if is_anticipation_drift:
                            break

                    if is_anticipation_drift:
                        print(f"\n    [!] Warning: Rejected anticipation drift for cue #{idx} (detected forward line match in reason: '{mod.get('reason')}')")
                        continue

                    cleaned = normalize_homoglyphs(polished_text)
                    if re.search(r'[\u0600-\u06FF]', cleaned):
                        for pat, repl in [
                            (r'\bبالכאד\b', 'בקושי'),
                            (r'\bبالكاد\b', 'בקושי'),
                            (r'\bما\b', 'מה'),
                        ]:
                            cleaned = re.sub(pat, repl, cleaned)
                        if re.search(r'[\u0600-\u06FF]', cleaned):
                            print(f"\n    [!] Warning: Rejected edit for cue #{idx} due to foreign/Arabic characters: {cleaned}")
                            continue
                    mod["polished_he"] = cleaned
                    modifications[idx] = mod
                    valid_count += 1

                consecutive_errors = 0
                print(f" [✓ {valid_count} edits]")
            except Exception as e:
                consecutive_errors += 1
                print(f" [!] Error in batch {b_num}: {e}")
                if consecutive_errors >= 2 and any(term in str(e) for term in ("API key", "Authentication", "failed across models", "HTTP 4")):
                    print(f"\n[!] Aborting remaining AI batches due to persistent API error: {e}")
                    print("    Proceeding with offline canon corrections.")
                    break
    else:
        if offline_only:
            print("[i] Running in --offline-canon-only mode (skipping LLM calls).")
        else:
            print("[i] No active LLM backend detected (set GEMINI_API_KEY or pass --ollama). Using deterministic canon pass.")

    # 8. Produce Final Mastered Cues
    final_cues = []
    for c in he_cues:
        idx = c["index"]
        if idx in modifications:
            new_text = modifications[idx]["polished_he"]
        else:
            new_text = c["text"]
        final_cues.append({
            "index": idx,
            "timing": c["timing"],
            "text": new_text
        })

    # 9. Output Paths & Seed-Safe Handling
    stem = he_path.stem
    if stem.endswith(".he"):
        base_stem = stem[:-3]
    else:
        base_stem = stem

    raw_diff = getattr(args, "diff_report", None)
    diff_path = Path(raw_diff).resolve() if raw_diff else (he_path.parent / f"{base_stem}_polish_diff.md")
    generate_diff_report(title, len(he_cues), modifications, diff_path, en_map)
    print(f"\n[✓] Polish Audit Report saved to: {diff_path.name}")

    if getattr(args, "diff_only", False) or getattr(args, "dry_run", False):
        print(f"[i] Dry-run active (--diff-only): Subtitle files left unmodified.")
        return True

    # Subtitle Output File
    output_path = getattr(args, "output", None)
    if not output_path:
        if getattr(args, "in_place", False):
            # Seed-safe backup before in-place modification
            backup_path = he_path.parent / f"{base_stem}.he.original.srt"
            if not backup_path.exists():
                shutil.copy2(he_path, backup_path)
                print(f"[i] Seed-Safe Backup created: {backup_path.name}")
            output_path = he_path
        else:
            output_path = he_path.parent / f"{base_stem}.he.polished.srt"
    else:
        output_path = Path(output_path).resolve()

    write_mastered_srt(final_cues, output_path)
    print(f"[✓] Polished Subtitle saved: {output_path.name}")
    print(f"[✓] Preserved intact: {len(he_cues) - len(modifications)} / {len(he_cues)} ({(len(he_cues) - len(modifications))/len(he_cues)*100:.1f}%)")
    print(f"[✓] Polished & Mastered: {len(modifications)} cues.")
    return True

# Backward-compatibility alias
polish_subtitle_file = polish_target

def main():
    parser = argparse.ArgumentParser(
        prog="rightsub polish",
        description="Semantic AI Polish & Subtitle QC Engine for RightSub"
    )
    parser.add_argument("target", help="Path to Hebrew subtitle (.he.srt) or video file (.mkv/.mp4) to polish")
    parser.add_argument("--en", dest="en_path", help="Path to companion master English subtitle (.en.srt)")
    parser.add_argument("--tmdb-id", type=int, help="TMDb Movie/TV ID for ground-truth entity resolution")
    parser.add_argument("--title", help="Explicit title for metadata/canon resolution")
    parser.add_argument("-b", "--bible", help="Path to Translation Bible (translation_bible.json) or directory")
    parser.add_argument("--ollama", action="store_true", help="Use local Ollama engine")
    parser.add_argument("--gemini", action="store_true", help="Force Google Gemini engine")
    parser.add_argument("--model", help="LLM model name (default: qwen2.5:7b for Ollama, gemini-3.5-flash for Gemini)")
    parser.add_argument("--api-key", help="TMDb or Gemini API key")
    parser.add_argument("--batch-size", type=int, default=60, help="Number of cues per prompt batch (default: 60)")
    parser.add_argument("--offline-canon-only", action="store_true", help="Run only offline deterministic canon pass (0 tokens)")
    parser.add_argument("--diff-only", "--dry-run", dest="diff_only", action="store_true", help="Generate audit report only without saving subtitle file")
    parser.add_argument("--in-place", action="store_true", help="Backup and update original file instead of creating .he.polished.srt")
    parser.add_argument("-o", "--output", help="Custom output path for polished subtitle file")
    parser.add_argument("--diff-report", help="Custom output path for markdown diff report")

    args = parser.parse_args()
    success = polish_target(args.target, args.en_path, args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
