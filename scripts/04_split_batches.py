#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_split_batches.py
-------------------
Splits an English master SRT file into optimal chunks of ~200-220 subtitles.
Features:
- SDH & Closed-Captions Context Intelligence: Extracts speaker tags and stage directions
  into a dedicated "context" field for the LLM to deduce gender, speaker identity, and tone.
- Dialogue Cleaning: Strips technical <font> tags and bracketed sound tags from the "text" field,
  presenting the LLM with clean dialogue to translate.
- 100% Index Preservation: Preserves sequential numbering for foolproof merging.
"""
import os
import re
import json
import argparse

def clean_dialogue_text(raw_text):
    # Remove HTML / font tags
    text = re.sub(r'</?font[^>]*>', '', raw_text, flags=re.IGNORECASE)
    
    # Extract bracketed context (e.g. [ Denny ], [ Whispering ])
    bracket_matches = re.findall(r'\[\s*([^\]]{1,30})\s*\]', text)
    context_list = []
    for bm in bracket_matches:
        b_clean = bm.strip()
        context_list.append(b_clean)

    # Clean bracketed tags from dialogue
    dialogue = re.sub(r'\[\s*[^\]]{1,30}\s*\]', '', text)
    # Clean leading whitespace and clean dash spaces
    cleaned_lines = []
    for l in dialogue.splitlines():
        l_str = l.strip()
        if l_str:
            cleaned_lines.append(l_str)
    
    final_dialogue = "\n".join(cleaned_lines).strip()
    context_str = ", ".join(context_list) if context_list else None
    return final_dialogue, context_str

def split_srt_to_batches(srt_path, output_dir, batch_size=210):
    os.makedirs(output_dir, exist_ok=True)
    with open(srt_path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()
    
    blocks = re.split(r'\n\s*\n', content)
    items = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 3:
            idx = int(lines[0].strip())
            raw_text = "\n".join(lines[2:]).strip()
            dialogue, context = clean_dialogue_text(raw_text)
            
            item = {"index": idx, "text": dialogue}
            if context:
                item["context"] = context
            items.append(item)

    total = len(items)
    batches = [items[i:i + batch_size] for i in range(0, total, batch_size)]
    print(f"[+] Total subtitles: {total} -> Splitting into {len(batches)} batch(es) of ~{batch_size}")

    manifest = []
    for i, batch in enumerate(batches, start=1):
        filename = f"batch_{i:02d}_en.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)
        manifest.append({
            "batch": i,
            "file": filename,
            "range": [batch[0]["index"], batch[-1]["index"]],
            "count": len(batch)
        })
        print(f"    Batch {i:02d}: #{batch[0]['index']} to #{batch[-1]['index']} ({len(batch)} items) -> {filename}")

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[✓] Manifest written to {manifest_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split English SRT into JSON batches for translation.")
    parser.add_argument("srt", help="Input English SRT file")
    parser.add_argument("-o", "--output_dir", required=True, help="Output directory for batches")
    parser.add_argument("-s", "--size", type=int, default=210, help="Batch size (default: 210)")
    args = parser.parse_args()
    split_srt_to_batches(args.srt, args.output_dir, args.size)
