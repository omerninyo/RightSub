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
4. If a cue is purely SDH or sound effects (e.g. ♪♪♪, [Music], (sighs), (sobs), [crying], [screaming], [gunshot], [buzzer blares], ***), return an empty string "" for hebrew, but KEEP ITS EXACT INDEX. Remove inline audio descriptions from dialogue.
5. Use Hebrew gershayim (״ \\u05F4) or single quotes for acronyms (e.g. עו״ד, ארה״ב, ד״ר, FBI, CIA, DNA). NEVER use standard double quotes inside Hebrew strings.
6. DO NOT VOCALIZE (ללא ניקוד): Write standard modern Hebrew spelling.
7. Return ONLY a valid JSON array in a single ```json ``` block:
```json
[
  {{"index": {start}, "hebrew": "..."}},
  ...
]
```
Do NOT call any tools. Do NOT run commands. Return the JSON directly.

INPUT CUES TO TRANSLATE:
{cues_json}"""

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

def build_prompts(srt_path, title, context="", genre="", chunk_size=88, output_dir=None, model="flash_lite"):
    cues = parse_srt(srt_path)
    total_cues = len(cues)
    if total_cues == 0:
        print(f"[-] No cues found in {srt_path}")
        return False

    if not title:
        title = os.path.splitext(os.path.basename(srt_path))[0]

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

        cues_json = json.dumps(chunk_cues, ensure_ascii=False, indent=1)
        prompt_text = PROMPT_TEMPLATE.format(
            title=title,
            count=count,
            start=start_num,
            end=end_num,
            genre_line=genre_line,
            context_block=context_block,
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
        "total_agents": len(agents),
        "total_waves": len(waves),
        "model": model,
        "waves": waves
    }
    with open(os.path.join(output_dir, "prompt_manifest.json"), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[✓] Successfully generated prompts for '{title}':")
    print(f"    - Total Cues: {total_cues}")
    print(f"    - Total Agents: {len(agents)} (in {len(waves)} waves of up to 4)")
    print(f"    - Output Directory: {output_dir}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Universal Prompt Generator for Subtitle Translation")
    parser.add_argument("srt", help="Path to English SRT file")
    parser.add_argument("--title", "-t", default="", help="Title of movie or series episode")
    parser.add_argument("--context", "-c", default="", help="Plot description, character names and notes")
    parser.add_argument("--genre", "-g", default="", help="Genre / dialogue tone (e.g. Legal comedy, Sci-Fi)")
    parser.add_argument("--chunk-size", "-s", type=int, default=88, help="Cues per agent (default: 88)")
    parser.add_argument("--output-dir", "-o", default="", help="Output directory for prompt JSON files")
    parser.add_argument("--model", "-m", default="flash_lite", help="Model tier (default: flash_lite)")
    args = parser.parse_args()

    build_prompts(
        srt_path=args.srt,
        title=args.title,
        context=args.context,
        genre=args.genre,
        chunk_size=args.chunk_size,
        output_dir=args.output_dir,
        model=args.model
    )

if __name__ == '__main__':
    main()
