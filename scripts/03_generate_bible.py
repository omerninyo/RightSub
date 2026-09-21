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
from pathlib import Path
from importlib import import_module

try:
    tmdb_mod = import_module("tmdb_client")
    fetch_metadata = tmdb_mod.fetch_show_or_movie_metadata
    is_tmdb_available = tmdb_mod.is_tmdb_available
except Exception:
    fetch_metadata = None
    is_tmdb_available = lambda key=None: False

def extract_entities(srt_paths, title=None, season=None, episode=None, use_tmdb=False, tmdb_key=None):
    speaker_pattern = re.compile(r'^[A-Z][A-Z\s\.\-]{1,20}:')
    bracket_pattern = re.compile(r'\[\s*([A-Za-z][A-Za-z\s\.\-]{1,25})\s*\]')
    honorific_pattern = re.compile(r'\b(Judge|Your Honor|Counselor|Mr\.|Mrs\.|Ms\.|Dr\.|Detective|Officer)\s+([A-Z][a-z]+)', re.IGNORECASE)
    
    speakers = Counter()
    honorifics = Counter()

    for path in srt_paths:
        if not Path(path).exists():
            continue
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

    # Base Bible skeleton
    bible = {
        "metadata": {
            "title": title or (Path(srt_paths[0]).stem if srt_paths else "Translation Bible & Glossary"),
            "source_files": [str(p) for p in srt_paths]
        },
        "characters": [
            {"name": spk, "hebrew_name": "", "gender": "unknown", "pronouns": "אתה/את", "occurrences": count}
            for spk, count in speakers.most_common(50)
        ],
        "honorifics_and_terms": [
            {"term": term, "hebrew_translation": "", "occurrences": count}
            for term, count in honorifics.most_common(50)
        ]
    }

    # Optional TMDb Enrichment
    if use_tmdb and fetch_metadata and (is_tmdb_available(tmdb_key) or tmdb_key):
        first_srt = srt_paths[0] if srt_paths else None
        print(f"[+] Querying TMDb for metadata & character gender resolution...")
        meta = fetch_metadata(
            title=title,
            filepath=first_srt,
            season=season,
            episode=episode,
            api_key=tmdb_key
        )

        if meta.get("success"):
            print(f"[✓] TMDb Match: '{meta['title']}' (ID: {meta['tmdb_id']})")
            if meta.get("episode"):
                print(f"    Episode: S{meta['season']:02d}E{meta['episode']:02d} - {meta.get('episode_name')}")
            print(f"    Resolved {len(meta.get('characters', []))} characters with verified gender.")

            # Store rich production metadata
            bible["metadata"].update({
                "tmdb_id": meta["tmdb_id"],
                "resolved_title": meta["title"],
                "overview": meta.get("overview", ""),
                "genres": meta.get("genres", []),
                "origin_country": meta.get("origin_country", []),
                "original_language": meta.get("original_language", "en"),
                "episode_name": meta.get("episode_name")
            })

            # Merge / Reconcile characters
            tmdb_chars = meta.get("characters", [])
            merged_characters = []
            seen_names = set()

            # 1. Update existing local speakers with TMDb ground truth
            for ch in bible["characters"]:
                local_name = ch["name"].strip()
                matched_tmdb = None

                for tc in tmdb_chars:
                    t_name = tc["name"].lower()
                    l_name = local_name.lower()
                    # Check exact match, first name match or substring match
                    t_parts = t_name.split()
                    l_parts = l_name.split()
                    if l_name == t_name or (l_parts and l_parts[0] in t_parts) or (l_parts and l_parts[-1] in t_parts):
                        matched_tmdb = tc
                        break

                if matched_tmdb:
                    ch["gender"] = matched_tmdb["gender"]
                    ch["pronouns"] = matched_tmdb["pronouns"]
                    ch["actor"] = matched_tmdb.get("actor", "")
                    ch["is_guest"] = matched_tmdb.get("is_guest", False)
                    ch["verified_by_tmdb"] = True
                    seen_names.add(matched_tmdb["name"].lower())
                merged_characters.append(ch)

            # 2. Add remaining TMDb cast members (especially episodic guest stars)
            for tc in tmdb_chars:
                if tc["name"].lower() not in seen_names:
                    merged_characters.append({
                        "name": tc["name"],
                        "actor": tc.get("actor", ""),
                        "hebrew_name": "",
                        "gender": tc["gender"],
                        "pronouns": tc["pronouns"],
                        "occurrences": 0,
                        "is_guest": tc.get("is_guest", False),
                        "verified_by_tmdb": True
                    })
                    seen_names.add(tc["name"].lower())

            bible["characters"] = merged_characters
        else:
            print(f"[-] TMDb Resolution Notice: {meta.get('error')}")

    return bible

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Translation Bible skeleton from English SRTs & TMDb.")
    parser.add_argument("srts", nargs="+", help="English SRT files to analyze")
    parser.add_argument("-o", "--output", default="translation_bible.json", help="Output JSON path")
    parser.add_argument("-t", "--title", help="Movie or TV show title")
    parser.add_argument("-s", "--season", type=int, help="Season number")
    parser.add_argument("-e", "--episode", type=int, help="Episode number")
    parser.add_argument("--tmdb", action="store_true", help="Enrich Bible with TMDb characters, genders, and plot")
    parser.add_argument("--tmdb-key", help="TMDb API Key / Read Access Token")
    args = parser.parse_args()
    
    # Auto-enable TMDb if TMDB_API_KEY environment variable is set
    should_use_tmdb = args.tmdb or (is_tmdb_available(args.tmdb_key))

    data = extract_entities(
        args.srts,
        title=args.title,
        season=args.season,
        episode=args.episode,
        use_tmdb=should_use_tmdb,
        tmdb_key=args.tmdb_key
    )
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[✓] Translation Bible generated: {args.output} ({len(data['characters'])} characters, {len(data['honorifics_and_terms'])} terms)")
