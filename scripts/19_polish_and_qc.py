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
        ],
        "characters": [
            {"name": "Princess Leia", "he_name": "הנסיכה ליאה", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Luke Skywalker", "he_name": "לוק סקייווקר", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Han Solo", "he_name": "האן סולו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Darth Vader", "he_name": "דארת' ויידר", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Obi-Wan Kenobi", "he_name": "אובי-וואן קנובי", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Grand Moff Tarkin", "he_name": "גראנד מופ טארקין", "gender": "Male", "pronouns": "אתה/הוא"},
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

def align_bilingual_cues(en_cues, he_cues):
    """
    Pairs English master cues with Hebrew existing cues.
    Strategy:
    1. Try exact 1:1 index match if indices and timings are reasonably aligned.
    2. Fallback to nearest timestamp overlap within 2500ms window.
    """
    he_by_idx = {c["index"]: c for c in he_cues}
    en_by_idx = {c["index"]: c for c in en_cues}

    aligned = []
    
    # Check if exact index match holds (common case)
    if len(en_cues) == len(he_cues) and all(c["index"] in he_by_idx for c in en_cues):
        for en in en_cues:
            he = he_by_idx[en["index"]]
            aligned.append({
                "index": en["index"],
                "timing": he["timing"],
                "en": en["text"],
                "he": he["text"]
            })
        return aligned

    # Fallback to proximity alignment
    he_times = [(time_to_ms(c["timing"]), c) for c in he_cues]
    used_he_indices = set()

    for en in en_cues:
        en_ms = time_to_ms(en["timing"])
        best_he = None
        best_diff = float("inf")

        for h_ms, he in he_times:
            if he["index"] in used_he_indices:
                continue
            diff = abs(h_ms - en_ms)
            if diff < best_diff and diff <= 2500:
                best_diff = diff
                best_he = he

        if best_he:
            used_he_indices.add(best_he["index"])
            aligned.append({
                "index": best_he["index"],
                "timing": best_he["timing"],
                "en": en["text"],
                "he": best_he["text"]
            })
        else:
            # Unpaired English cue - skip or ignore
            pass

    # Add any remaining Hebrew cues that had no English pair (keep intact)
    for h_ms, he in he_times:
        if he["index"] not in used_he_indices:
            aligned.append({
                "index": he["index"],
                "timing": he["timing"],
                "en": "",
                "he": he["text"]
            })

    aligned.sort(key=lambda x: x["index"])
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

def build_polish_prompt(aligned_batch, title, franchise_name=None, franchise_data=None, characters=None):
    """Builds a constrained, high-efficiency Polish prompt."""
    glossary_lines = []
    if franchise_data:
        glossary_lines.append(f"FRANCHISE CANON GUIDELINES ({franchise_name.upper()}):")
        for pat, rep, reas in franchise_data.get("canon_terms", []):
            clean_term = pat.replace(r"\b", "").replace(r"\s*", " ")
            glossary_lines.append(f"- '{clean_term}' MUST BE TRANSLATED AS '{rep}' ({reas})")
    
    char_lines = []
    if characters:
        char_lines.append("CONFIRMED CHARACTERS & GENDERS:")
        for c in characters[:12]:
            c_name = c.get("name", "")
            c_he = c.get("he_name") or c_name
            c_gen = c.get("gender", "Unknown")
            c_pro = c.get("pronouns", "")
            char_lines.append(f"- {c_name} ({c_he}): Gender = {c_gen} (Hebrew 2nd/3rd person: {c_pro})")

    batch_input = [
        {"index": c["index"], "en": c["en"], "current_he": c["he"]}
        for c in aligned_batch
    ]

    prompt = f"""You are a professional Hebrew subtitling proofreader and quality-assurance editor.
Title: {title}

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

def query_gemini_api(prompt, api_key=None, model="gemini-2.0-flash"):
    """Calls Google Gemini API via standard library urllib with model fallback and descriptive errors."""
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

    models_to_try = [model]
    for fallback in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }
    raw_data = json.dumps(payload).encode("utf-8")

    last_error = None
    for m in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        req = urllib.request.Request(
            url,
            data=raw_data,
            headers={"Content-Type": "application/json", "User-Agent": "RightSub/1.3"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
            text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except urllib.error.HTTPError as e:
            err_msg = ""
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", err_body)
            except Exception:
                err_msg = str(e)

            if e.code == 404:
                last_error = f"Model '{m}' not found: {err_msg}"
                continue
            elif e.code in (400, 401, 403):
                raise RuntimeError(f"Authentication/Permission error (HTTP {e.code}): {err_msg}")
            else:
                raise RuntimeError(f"Google API HTTP {e.code}: {err_msg}")
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
    return json.loads(response_str)

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
    """Writes cues to SRT file with Plex/Infuse RLM and UTF-8 encoding."""
    out_blocks = []
    for c in cues:
        idx = c["index"]
        timing = c["timing"]
        raw_text = c["text"]
        
        # Apply Plex/Infuse BiDi RLM mastering to each line
        lines = [apply_bidi_and_punctuation(l) for l in raw_text.splitlines()]
        clean_text = "\n".join(lines)
        out_blocks.append(f"{idx}\n{timing}\n{clean_text}")

    content = "\n\n".join(out_blocks) + "\n"
    Path(output_path).write_text(content, encoding="utf-8")

def polish_subtitle_file(he_path, en_path=None, args=None):
    """Main execution function for polishing a subtitle file."""
    he_path = Path(he_path).resolve()
    if not he_path.is_file():
        print(f"[-] Target Hebrew subtitle not found: {he_path}")
        return False

    print(f"\n=======================================================")
    print(f"  💎 RightSub Semantic AI Polish & QC Engine")
    print(f"=======================================================")
    print(f"[*] Hebrew Target: {he_path.name}")

    # 1. Discover English counterpart if not provided
    if not en_path:
        for ext in [".en.srt", ".eng.srt", ".english.srt"]:
            cand = he_path.parent / f"{he_path.stem.replace('.he', '')}{ext}"
            if cand.is_file():
                en_path = cand
                break
        if not en_path:
            alt_cand = he_path.with_suffix(".en.srt")
            if alt_cand.is_file():
                en_path = alt_cand

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
    if not title:
        if parse_media_filename:
            parsed = parse_media_filename(he_path.name)
            title = parsed.get("title") or he_path.stem.replace(".he", "").replace(".polished", "")
        else:
            title = he_path.stem.replace(".he", "").replace(".polished", "")

    franchise_name, franchise_data = detect_franchise(title)
    if franchise_name:
        print(f"[+] Franchise Lore Detected: {franchise_name.upper()} (Enforcing canonical terms)")

    # 5. Fetch TMDb Characters (if available)
    characters = []
    tmdb_id = getattr(args, "tmdb_id", None)
    if fetch_media_metadata and is_tmdb_available(getattr(args, "api_key", None)):
        try:
            tmdb_meta = fetch_media_metadata(filepath=he_path, title=title, api_key=getattr(args, "api_key", None))
            if tmdb_meta and tmdb_meta.get("success"):
                characters = tmdb_meta.get("characters", [])
                print(f"[+] TMDb Metadata Loaded: {len(characters)} character gender assignments.")
        except Exception as e:
            print(f"[!] TMDb query notice: {e}")

    # Inject franchise characters if missing from TMDb
    if franchise_data and "characters" in franchise_data:
        existing_names = {c["name"].lower() for c in characters}
        for fc in franchise_data["characters"]:
            if fc["name"].lower() not in existing_names:
                characters.append(fc)

    # 6. Deterministic Heuristic Canon Pass (Offline baseline, 0 tokens)
    modifications = run_deterministic_canon_pass(aligned, franchise_data)
    if modifications:
        print(f"[✓] Offline Canon Pass identified {len(modifications)} terminology corrections.")

    # 7. AI Polish Pass (if backend requested / available)
    use_ollama = getattr(args, "ollama", False)
    use_gemini = getattr(args, "gemini", False) or bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    offline_only = getattr(args, "offline_canon_only", False)

    if not offline_only and (use_ollama or use_gemini):
        backend_name = f"Ollama ({getattr(args, 'model', None) or 'default'})" if use_ollama else f"Gemini ({getattr(args, 'model', None) or 'gemini-2.0-flash'})"
        print(f"[*] Running Semantic AI Proofreader via {backend_name}...")

        batch_size = getattr(args, "batch_size", 60) or 60
        total_batches = (len(aligned) + batch_size - 1) // batch_size
        consecutive_errors = 0

        for b_idx in range(0, len(aligned), batch_size):
            batch = aligned[b_idx:b_idx + batch_size]
            b_num = (b_idx // batch_size) + 1
            print(f"    -> Processing batch {b_num}/{total_batches} (cues {batch[0]['index']}..{batch[-1]['index']})...", end="", flush=True)

            prompt = build_polish_prompt(batch, title, franchise_name, franchise_data, characters)

            try:
                if use_ollama:
                    model = getattr(args, "model", None) or "qwen2.5:7b"
                    res = query_ollama_api(prompt, model=model)
                else:
                    model = getattr(args, "model", None) or "gemini-2.0-flash"
                    res = query_gemini_api(prompt, api_key=getattr(args, "api_key", None), model=model)

                batch_cues = res.get("cues", []) if isinstance(res, dict) else []
                for mod in batch_cues:
                    idx = mod.get("index")
                    if idx in en_map:
                        modifications[idx] = mod

                consecutive_errors = 0
                print(f" [✓ {len(batch_cues)} edits]")
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

    diff_path = getattr(args, "diff_report", None) or (he_path.parent / f"{base_stem}_polish_diff.md")
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

def main():
    parser = argparse.ArgumentParser(
        prog="rightsub polish",
        description="Semantic AI Polish & Subtitle QC Engine for RightSub"
    )
    parser.add_argument("target", help="Path to Hebrew subtitle (.he.srt) to polish")
    parser.add_argument("--en", dest="en_path", help="Path to companion master English subtitle (.en.srt)")
    parser.add_argument("--tmdb-id", type=int, help="TMDb Movie/TV ID for ground-truth entity resolution")
    parser.add_argument("--title", help="Explicit title for metadata/canon resolution")
    parser.add_argument("--ollama", action="store_true", help="Use local Ollama engine")
    parser.add_argument("--gemini", action="store_true", help="Force Google Gemini engine")
    parser.add_argument("--model", help="LLM model name (default: qwen2.5:7b for Ollama, gemini-2.0-flash for Gemini)")
    parser.add_argument("--api-key", help="TMDb or Gemini API key")
    parser.add_argument("--batch-size", type=int, default=60, help="Number of cues per prompt batch (default: 60)")
    parser.add_argument("--offline-canon-only", action="store_true", help="Run only offline deterministic canon pass (0 tokens)")
    parser.add_argument("--diff-only", "--dry-run", dest="diff_only", action="store_true", help="Generate audit report only without saving subtitle file")
    parser.add_argument("--in-place", action="store_true", help="Backup and update original file instead of creating .he.polished.srt")
    parser.add_argument("-o", "--output", help="Custom output path for polished subtitle file")
    parser.add_argument("--diff-report", help="Custom output path for markdown diff report")

    args = parser.parse_args()
    success = polish_subtitle_file(args.target, args.en_path, args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
