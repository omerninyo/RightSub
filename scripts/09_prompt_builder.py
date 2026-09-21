#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09_prompt_builder.py
--------------------
Generates high-precision, context-aware LLM translation prompts for ANY movie or TV show.
Features:
1. Automatically splits SRT into optimal agent chunks (default ~85-90 cues).
2. Generates Wave 1, Wave 2 JSON definitions ready for subagent invocation.
3. Injects context, characters, genre, and strict formatting rules.
"""

import os
import sys
import os
import sys
import re
import json
import argparse

PROMPT_TEMPLATE = """Translate the following subtitle cues from English to Hebrew for '{title}'.
Model Policy: Gemini 3.5 Flash-Lite / Gemini 3.8 Flash (fast, direct translation).

CRITICAL RULES:
1. Translate all cues into natural, fluent, context-aware Hebrew matching character voice, genre, and dialogue tone.
2. 1-to-1 matching: NEVER merge or drop cues. Exactly {count} items from index {start} to {end}. Every single index MUST be present!
3. Context & Background:
- Title: {title}
{genre_line}
{context_block}
{bible_block}
4. GENDER ACCURACY & VOCATIVE (DIRECT ADDRESS) RULES:
- Hebrew grammar strictly distinguishes 2nd person gender ("אתה" vs "את") and verb conjugations ("אתה רוצה" vs "את רוצה").
- Direct Address (Vocative): When dialogue addresses a female character by name or title (e.g. 'Shirley, you...', 'Tara, did you...', 'Judge (female), you...'), conjugate all verbs, pronouns, and adjectives in the feminine ("שירלי, את...", "טרה, ראית...", "כבוד השופטת, את...").
- Speaker & Listener Continuity: Use dialogue context to track who is in the room. When speaking to a woman, address her as female.
- SDH & Speaker Tags: Tags like [Tara], [Alan], or 'DENNY:' are context indicators for YOU. Use them to know who speaks and to whom, but STRIP them completely from the final Hebrew text (translate dialogue only).
5. If a cue is purely SDH or sound effects (e.g. ♪♪♪, [Music], (sighs), (sobs), [crying], [screaming], [gunshot], [buzzer blares], ***), return an empty string "" for hebrew, but KEEP ITS EXACT INDEX. Remove inline audio descriptions from dialogue.
6. Use Hebrew gershayim (״ \\u05F4) or single quotes for acronyms (e.g. עו״ד, ארה״ב, ד״ר, FBI, CIA, DNA). NEVER use standard double quotes inside Hebrew strings.
7. DO NOT VOCALIZE (ללא ניקוד): Write standard modern Hebrew spelling.
8. Return ONLY a valid JSON array in a single ```json ``` block:
```json
[
  {{"index": {start}, "hebrew": "..."}},
  ...
]
```
Do NOT call any tools. Do NOT run commands. Return the JSON directly.

{overlap_block}
INPUT CUES TO TRANSLATE:
{cues_json}"""

def load_bible_data(bible_path):
    """Loads character, glossary, and TMDb production metadata from a Translation Bible JSON."""
    if not bible_path or not os.path.exists(bible_path):
        return "", {}
    try:
        with open(bible_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        meta = data.get("metadata", {})
        lines = ["- Character Roster & Gender Mapping (Mandatory Consistency):"]
        characters = data.get("characters", [])
        for ch in characters[:40]:
            name = ch.get("name", "")
            he_name = ch.get("hebrew_name", "")
            gender = ch.get("gender", "unknown")
            pronouns = ch.get("pronouns", "")
            guest = " [Guest]" if ch.get("is_guest") else ""
            display_he = f" ({he_name})" if he_name else ""
            lines.append(f"  * {name}{display_he}{guest}: Gender={gender}, Pronouns={pronouns}")
        
        terms = data.get("honorifics_and_terms", [])
        if terms:
            lines.append("- Recurring Terms & Honorifics:")
            for t in terms[:25]:
                term = t.get("term", "")
                trans = t.get("hebrew_translation", "")
                if trans:
                    lines.append(f"  * {term} -> {trans}")
                else:
                    lines.append(f"  * {term}")
        
        # Add dialect notes if detected
        origin_country = meta.get("origin_country", [])
        if any(c in ["GB", "UK"] for c in origin_country):
            lines.append("- Source Dialect: British English (UK). Note British idioms, regional slang (e.g. 'pissed'=drunk, 'mate', 'cheers'=thanks, 'rubbish', 'chap'), and British cultural references.")
        
        return "\n".join(lines), meta
    except Exception as e:
        print(f"[!] Warning: Could not parse bible {bible_path}: {e}")
        return "", {}

def load_bible(bible_path):
    """Backward compatible wrapper returning only formatted string."""
    text, _ = load_bible_data(bible_path)
    return text

def parse_srt(path):
    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
        content = f.read().strip()
    blocks = re.split(r'\n\s*\n', content)
    res = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                idx = int(lines[0].strip())
                text = '\n'.join(lines[2:])
                res.append({"index": idx, "text": text})
            except ValueError:
                continue
    return res

def build_prompts(srt_path, title="", context="", genre="", bible_path="", overlap=5, chunk_size=88, output_dir=None, model="flash_lite"):
    cues = parse_srt(srt_path)
    total_cues = len(cues)
    if total_cues == 0:
        print(f"[-] No cues found in {srt_path}")
        return False

    if not title:
        title = os.path.splitext(os.path.basename(srt_path))[0]

    # Look for default bible in same directory or parent if not explicitly supplied
    if not bible_path:
        candidates = [
            os.path.join(os.path.dirname(srt_path), "translation_bible.json"),
            os.path.join(os.path.dirname(srt_path), "..", "translation_bible.json"),
            os.path.join(os.getcwd(), "translation_bible.json")
        ]
        for cand in candidates:
            if os.path.exists(cand):
                bible_path = cand
                break

    bible_block, bible_meta = load_bible_data(bible_path)

    if not genre and bible_meta.get("genres"):
        genre = ", ".join(bible_meta["genres"])
    if not context and bible_meta.get("overview"):
        context = bible_meta["overview"]

    if not output_dir:
        output_dir = os.path.join(os.path.dirname(srt_path), f"prompts_{title}")
    os.makedirs(output_dir, exist_ok=True)

    # Calculate splits
    num_chunks = (total_cues + chunk_size - 1) // chunk_size
    agents = []
    
    genre_line = f"- Genre / Tone: {genre}" if genre else ""
    context_block = f"- Extra Context & Plot:\n{context}" if context else ""

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_cues)
        chunk_cues = cues[start_idx:end_idx]
        start_num = chunk_cues[0]["index"]
        end_num = chunk_cues[-1]["index"]
        count = len(chunk_cues)

        # Build context overlap window from previous chunk
        overlap_block = ""
        if i > 0 and overlap > 0:
            overlap_start = max(0, start_idx - overlap)
            prev_cues = cues[overlap_start:start_idx]
            if prev_cues:
                overlap_lines = [f"[{c['index']}] {c['text']}" for c in prev_cues]
                overlap_block = (
                    "PREVIOUS DIALOGUE CONTEXT (Reference only to track speakers/gender - do NOT re-translate or include in JSON):\n"
                    + "\n".join(overlap_lines)
                    + "\n--- END PREVIOUS CONTEXT ---\n"
                )

        cues_json = json.dumps(chunk_cues, ensure_ascii=False, indent=1)
        prompt_text = PROMPT_TEMPLATE.format(
            title=title,
            count=count,
            start=start_num,
            end=end_num,
            genre_line=genre_line,
            context_block=context_block,
            bible_block=bible_block,
            overlap_block=overlap_block,
            cues_json=cues_json
        )

        agent_obj = {
            "TypeName": "self",
            "Role": f"Translator {title} Part {i+1:02d}",
            "Prompt": prompt_text,
            "Model": model,
            "Workspace": "inherit"
        }
        agents.append(agent_obj)

        with open(os.path.join(output_dir, f"agent_{i+1:02d}.json"), 'w', encoding='utf-8') as f:
            json.dump(agent_obj, f, ensure_ascii=False, indent=2)

    # Split into waves of 4 agents
    waves = []
    for w in range(0, len(agents), 4):
        wave_num = (w // 4) + 1
        wave_agents = agents[w:w+4]
        wave_file = os.path.join(output_dir, f"wave_{wave_num:02d}.json")
        with open(wave_file, 'w', encoding='utf-8') as f:
            json.dump(wave_agents, f, ensure_ascii=False, indent=2)
        waves.append(wave_file)

    manifest = {
        "title": title,
        "total_cues": total_cues,
        "chunk_size": chunk_size,
        "overlap_cues": overlap,
        "bible_path": bible_path if bible_block else None,
        "total_agents": len(agents),
        "total_waves": len(waves),
        "model": model,
        "waves": waves
    }
    with open(os.path.join(output_dir, "prompt_manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[✓] Successfully generated prompts for '{title}':")
    print(f"    - Total Cues: {total_cues}")
    print(f"    - Overlap: {overlap} cues per boundary")
    if bible_block:
        print(f"    - Bible Roster Injected: {bible_path}")
    print(f"    - Total Agents: {len(agents)} (in {len(waves)} waves of up to 4)")
    print(f"    - Output Directory: {output_dir}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Universal Prompt Generator for Subtitle Translation")
    parser.add_argument("srt", help="Path to English SRT file")
    parser.add_argument("--title", "-t", default="", help="Title of movie or series episode")
    parser.add_argument("--context", "-c", default="", help="Plot description, character names and notes")
    parser.add_argument("--genre", "-g", default="", help="Genre / dialogue tone (e.g. Legal comedy, Sci-Fi)")
    parser.add_argument("--bible", "-b", default="", help="Path to translation_bible.json")
    parser.add_argument("--overlap", type=int, default=5, help="Number of previous cues to inject as context (default: 5)")
    parser.add_argument("--chunk-size", "-s", type=int, default=88, help="Cues per agent (default: 88)")
    parser.add_argument("--output-dir", "-o", default="", help="Output directory for prompt JSON files")
    parser.add_argument("--model", "-m", default="flash_lite", help="Model tier (default: flash_lite)")
    args = parser.parse_args()

    build_prompts(
        srt_path=args.srt,
        title=args.title,
        context=args.context,
        genre=args.genre,
        bible_path=args.bible,
        overlap=args.overlap,
        chunk_size=args.chunk_size,
        output_dir=args.output_dir,
        model=args.model
    )

if __name__ == '__main__':
    main()

