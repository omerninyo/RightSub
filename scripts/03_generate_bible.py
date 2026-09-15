#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_generate_bible.py
--------------------
Scans English SRT files or show description to extract speaker tags (e.g. 'ALAN:', 'DENNY:'),
names, and recurring legal/technical terminology to initialize the Translation Bible.
"""
import re
import json
import argparse
from collections import Counter

def extract_entities(srt_paths):
    speaker_pattern = re.compile(r'^[A-Z][A-Z\s\.\-]{1,20}:')
    bracket_pattern = re.compile(r'\[\s*([A-Za-z][A-Za-z\s\.\-]{1,25})\s*\]')
    honorific_pattern = re.compile(r'\b(Judge|Your Honor|Counselor|Mr\.|Mrs\.|Ms\.|Dr\.|Detective|Officer)\s+([A-Z][a-z]+)', re.IGNORECASE)
    
    speakers = Counter()
    honorifics = Counter()

    for path in srt_paths:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                spk = speaker_pattern.match(line)
                if spk:
                    speakers[spk.group(0).rstrip(':').strip()] += 1
                for b in bracket_pattern.finditer(line):
                    val = b.group(1).strip()
                    if not any(noise in val.lower() for noise in ['applause', 'music', 'cheering', 'laughter', 'screaming', 'gasping', 'sighs', 'sighing', 'chuckles', 'mouthing']):
                        speakers[val] += 1
                for h in honorific_pattern.finditer(line):
                    honorifics[h.group(0)] += 1

    bible = {
        "metadata": {
            "title": "Translation Bible & Glossary",
            "source_files": srt_paths
        },
        "characters": [
            {"name": spk, "hebrew_name": "", "gender": "male/female", "pronouns": "אתה/את", "occurrences": count}
            for spk, count in speakers.most_common(50)
        ],
        "honorifics_and_terms": [
            {"term": term, "hebrew_translation": "", "occurrences": count}
            for term, count in honorifics.most_common(50)
        ]
    }
    return bible

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Translation Bible skeleton from English SRTs.")
    parser.add_argument("srts", nargs="+", help="English SRT files to analyze")
    parser.add_argument("-o", "--output", default="translation_bible.json", help="Output JSON path")
    args = parser.parse_args()
    
    data = extract_entities(args.srts)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[✓] Translation Bible generated: {args.output} ({len(data['characters'])} characters, {len(data['honorifics_and_terms'])} terms)")
