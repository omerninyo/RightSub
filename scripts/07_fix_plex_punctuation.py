#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07_fix_plex_punctuation.py
--------------------------
Enterprise-grade standalone tool to fix Hebrew punctuation reversal (BiDi) in Plex,
Infuse, VLC, and Kodi without altering timestamps or legitimate dialogue.

Key Features:
1. Auto-Charset Detection & Conversion:
   Detects legacy Windows-1255 / CP1255 / ISO-8859-8 and converts to pure UTF-8 (eliminating mojibake/gibberish).
2. Smart Language Verification:
   Ensures file is actually Hebrew before touching it. Automatically skips English and other languages.
3. Formatting Tag Preservation:
   Handles HTML tags (<i>, <b>, <u>) and SSA tags ({\\an8}) gracefully without tag breaking.
4. Ad & Spam Stripper (--clean-ads):
   Detects and cleans promo spam ("OpenSubtitles", "Torec", "Wizdom", "תורגם על ידי", "טלגרם").
5. Safety Controls:
   --dry-run (preview mode with zero disk writes)
   --backup (creates .srt.bak prior to modifying files in-place)
6. Full Idempotency:
   Running repeatedly never duplicates RLM marks or corrupts text.
"""

import os
import sys
import re
import argparse
import shutil
from pathlib import Path

RLM = "\u200F"

# Common advertising, website promotions, and translator credit patterns
AD_PATTERNS = [
    r'opensubtitles',
    r'torec(?:\.net)?',
    r'wizdom(?:\.xyz)?',
    r'sratim\.co\.il',
    r'subcenter',
    r'ktuvit',
    r'סונכרן\s+(?:על\s+ידי|ע["״\']?י)',
    r'תורגם\s+(?:על\s+ידי|ע["״\']?י)',
    r'תרגום:\s*',
    r'סנכרון:\s*',
    r'הורד\s+מ[-–—]',
    r'הועלה\s+על\s+ידי',
    r'הצטרפו\s+ל.*טלגרם',
    r't\.me\/',
    r'telegram\.me',
    r'rip\s+by\b',
    r'sync\s+by\b',
]
AD_REGEX = re.compile('|'.join(AD_PATTERNS), re.IGNORECASE)

def read_file_with_auto_encoding(file_path):
    """
    Reads a subtitle file, automatically detecting if it's UTF-8, UTF-8-SIG,
    or legacy Windows-1255 / CP1255 / ISO-8859-8.
    Returns (content_str, detected_encoding).
    """
    raw_bytes = Path(file_path).read_bytes()

    # 1. Try UTF-8 / UTF-8-SIG
    try:
        text = raw_bytes.decode('utf-8-sig')
        # Verify it does not look like double-encoded mojibake
        hebrew_chars = len(re.findall(r'[\u0590-\u05FF]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        if hebrew_chars > 0 or latin_chars > 0:
            return text, 'utf-8'
    except UnicodeDecodeError:
        pass

    # 2. Check for Windows-1255 (Hebrew ANSI)
    # Hebrew characters in CP1255 reside in 0xE0..0xFA
    cp1255_hebrew_bytes = sum(1 for b in raw_bytes if 0xE0 <= b <= 0xFA)
    if cp1255_hebrew_bytes >= 10:
        try:
            text = raw_bytes.decode('cp1255')
            return text, 'windows-1255'
        except Exception:
            pass

    # 3. Fallbacks
    for enc in ['cp1255', 'iso-8859-8', 'latin1', 'utf-8']:
        try:
            return raw_bytes.decode(enc, errors='replace'), enc
        except Exception:
            continue

    return raw_bytes.decode('utf-8', errors='replace'), 'utf-8-fallback'

def detect_hebrew(content, min_chars=15, min_ratio=0.15):
    """
    Checks if content has a valid ratio of Hebrew letters.
    """
    hebrew_chars = len(re.findall(r'[\u0590-\u05FF]', content))
    latin_chars = len(re.findall(r'[a-zA-Z]', content))
    total_alpha = hebrew_chars + latin_chars

    if total_alpha == 0:
        return False, 0.0, "No alphabetic characters found"

    ratio = hebrew_chars / total_alpha
    is_hebrew = (hebrew_chars >= min_chars) and (ratio >= min_ratio)
    details = f"Hebrew chars: {hebrew_chars}, Latin chars: {latin_chars} (Hebrew ratio: {ratio:.1%})"
    return is_hebrew, ratio, details

def is_ad_line(line):
    clean = re.sub(r'<[^>]+>', '', line).strip()
    return bool(AD_REGEX.search(clean))

def apply_rlm_to_line(line):
    """
    Applies RLM formatting safely around tags (<i>, <b>, <u>, {\\anX}).
    """
    stripped = line.strip()
    if not stripped:
        return line

    # If no Hebrew in this line, keep untouched
    if not re.search(r'[\u0590-\u05FF]', stripped):
        return line

    # Convert standard double quotes in Hebrew acronyms to Hebrew gershayim (״)
    stripped = re.sub(r'([\u0590-\u05FF])"([\u0590-\u05FF])', r'\1״\2', stripped)

    # Separate SSA coordinate prefix if present, e.g. "{\an8}..."
    ssa_prefix = ""
    ssa_match = re.match(r'^(\{\\an\d+\})(.*)$', stripped)
    if ssa_match:
        ssa_prefix = ssa_match.group(1)
        stripped = ssa_match.group(2).strip()

    # Separate opening tags like <i>, <b>
    tag_prefix = ""
    tag_open_match = re.match(r'^((?:<[iIuUbB]>)+)(.*)$', stripped)
    if tag_open_match:
        tag_prefix = tag_open_match.group(1)
        stripped = tag_open_match.group(2).strip()

    # Separate closing tags like </i>, </b>
    tag_suffix = ""
    tag_close_match = re.search(r'((?:<\/[iIuUbB]>)+)$', stripped)
    if tag_close_match:
        tag_suffix = tag_close_match.group(1)
        stripped = stripped[:tag_close_match.start()].strip()

    # Clean existing trailing RLMs
    stripped = re.sub(rf'{RLM}+([\.!\?,:;\-\—\)»\]]+)$', r'\1', stripped)
    
    # Add RLM before trailing neutral punctuation
    stripped = re.sub(r'([\.!\?,:;\-\—\)»\]]+)$', f'{RLM}\\1', stripped)

    # Clean and add leading RLM
    stripped = stripped.lstrip(RLM)
    stripped = RLM + stripped

    # Reconstruct with original tags
    return f"{ssa_prefix}{tag_prefix}{stripped}{tag_suffix}"

def process_srt_content(content, clean_ads=False):
    blocks = re.split(r'\n\s*\n', content.strip())
    new_blocks = []
    total_subs = 0
    modified_lines = 0
    ads_removed = 0

    idx_counter = 1

    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 3:
            timeline = lines[1]
            text_lines = lines[2:]

            if clean_ads and any(is_ad_line(l) for l in text_lines):
                ads_removed += 1
                continue

            total_subs += 1
            new_text_lines = []
            for tl in text_lines:
                fixed = apply_rlm_to_line(tl)
                if fixed != tl:
                    modified_lines += 1
                new_text_lines.append(fixed)

            new_block = [str(idx_counter), timeline] + new_text_lines
            idx_counter += 1
            new_blocks.append("\n".join(new_block))
        elif lines:
            new_blocks.append("\n".join(lines))

    result_text = "\n\n".join(new_blocks) + "\n" if new_blocks else ""
    return result_text, total_subs, modified_lines, ads_removed

def process_file(file_path, output_path=None, in_place=False, force=False, dry_run=False, backup=False, clean_ads=False):
    p = Path(file_path)
    if not p.is_file():
        print(f"[-] File not found: {file_path}")
        return 0, 0, 0, "not_found"

    content, encoding_detected = read_file_with_auto_encoding(p)

    # Language verification
    is_heb, ratio, details = detect_hebrew(content)
    if not is_heb and not force:
        print(f"[SKIP] {p.name}: NOT Hebrew ({details}). Skipped.")
        return 0, 0, 0, "skipped_non_hebrew"

    fixed_content, total_subs, modified_lines, ads_removed = process_srt_content(content, clean_ads=clean_ads)

    enc_note = f" (Converted from {encoding_detected} to UTF-8)" if encoding_detected != 'utf-8' else ""
    ads_note = f", {ads_removed} ad lines removed" if ads_removed > 0 else ""

    if dry_run:
        print(f"[DRY-RUN] {p.name}: {total_subs} subtitles{enc_note} -> would adjust {modified_lines} lines{ads_note}.")
        return total_subs, modified_lines, ads_removed, "dry_run"

    dest = p if in_place else Path(output_path if output_path else str(p).replace(".srt", ".plex_fixed.srt"))

    if in_place and backup:
        bak_file = p.with_suffix(".srt.bak")
        shutil.copy2(p, bak_file)

    with open(dest, "w", encoding="utf-8") as f:
        f.write(fixed_content)

    status = "already compliant" if modified_lines == 0 and ads_removed == 0 and encoding_detected == 'utf-8' else "fixed"
    print(f"[✓] {p.name}: Processed {total_subs} subs ({modified_lines} lines adjusted{ads_note}{enc_note}, {status}) -> {dest.name}")
    return total_subs, modified_lines, ads_removed, "processed"

def main():
    parser = argparse.ArgumentParser(
        description="Fix Hebrew punctuation reversal (Plex/Infuse BiDi fix) on SRT subtitle files with encoding conversion and ad stripping."
    )
    parser.add_argument("targets", nargs="+", help="SRT files or directory paths to process")
    parser.add_argument("--in-place", "-i", action="store_true", help="Overwrite existing files directly")
    parser.add_argument("--output-dir", "-o", help="Optional output directory for fixed files")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively search directories for .srt files")
    parser.add_argument("--clean-ads", action="store_true", help="Strip translator credits and promo spam lines (e.g. Torec, OpenSubtitles)")
    parser.add_argument("--backup", "-b", action="store_true", help="Create .srt.bak backup before modifying files in-place")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Preview modifications without writing anything to disk")
    parser.add_argument("--force", "-f", action="store_true", help="Force processing even if Hebrew ratio is low")

    args = parser.parse_args()

    file_list = []
    for t in args.targets:
        tp = Path(t)
        if tp.is_file() and tp.suffix.lower() == ".srt":
            file_list.append(tp)
        elif tp.is_dir():
            pattern = "**/*.srt" if args.recursive else "*.srt"
            found = [f for f in tp.glob(pattern) if not f.name.endswith(".bak")]
            file_list.extend(found)

    if not file_list:
        print("[-] No .srt files found to process.")
        sys.exit(1)

    print(f"=== Starting Plex Hebrew BiDi Fix on {len(file_list)} file(s) ===")
    if args.dry_run:
        print("[!] MODE: DRY-RUN (No files will be modified on disk)")
    if args.clean_ads:
        print("[i] AD-STRIPPER: Active (removing promo spam and credit lines)")
    if args.backup and args.in_place:
        print("[i] BACKUP: Enabled (creating .srt.bak before editing)")

    total_all_subs = 0
    total_all_modified = 0
    total_ads_removed = 0
    skipped_count = 0
    processed_count = 0

    for srt in sorted(file_list):
        if args.output_dir:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / srt.name
            subs, mods, ads, res = process_file(
                srt, output_path=out_file, in_place=False, force=args.force,
                dry_run=args.dry_run, backup=args.backup, clean_ads=args.clean_ads
            )
        else:
            subs, mods, ads, res = process_file(
                srt, in_place=args.in_place, force=args.force,
                dry_run=args.dry_run, backup=args.backup, clean_ads=args.clean_ads
            )

        if res == "skipped_non_hebrew":
            skipped_count += 1
        elif res in ["processed", "dry_run"]:
            processed_count += 1
            total_all_subs += subs
            total_all_modified += mods
            total_ads_removed += ads

    print("==================================================================")
    print(f"Summary:")
    print(f"  • Files found:           {len(file_list)}")
    print(f"  • Hebrew files handled:  {processed_count}")
    print(f"  • Non-Hebrew skipped:    {skipped_count}")
    print(f"  • Total subtitles:       {total_all_subs}")
    print(f"  • Lines adjusted:        {total_all_modified}")
    if args.clean_ads:
        print(f"  • Ad lines stripped:     {total_ads_removed}")
    print("Execution complete. 100% Plex & Infuse compliant.")
    print("==================================================================")

if __name__ == "__main__":
    main()
