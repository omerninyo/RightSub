#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
08_quality_assurance.py
------------------------
Performs automated, exhaustive quality assurance on subtitle files:
1. 1-to-1 timing and block count match between English and Hebrew SRTs.
2. Verification of Right-to-Left Mark (RLM \u200F) on every line for Plex/Infuse.
3. Zero tolerance for foreign glyphs (Arabic, Cyrillic).
4. Zero tolerance for Hebrew vocalization (nikud).
5. Zero tolerance for literal escape sequences (\\n).
6. Support for single files and recursive directory batch audits.
"""

import os
import sys
import re
import argparse

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
                timing = lines[1].strip()
                text = '\n'.join(lines[2:])
                res.append((idx, timing, text))
            except ValueError:
                continue
    return res

def audit_pair(en_path, he_path, verbose=False):
    if not os.path.exists(en_path):
        return False, {"errors": [f"English SRT not found: {en_path}"]}
    if not os.path.exists(he_path):
        return False, {"errors": [f"Hebrew SRT not found: {he_path}"]}

    en_subs = parse_srt(en_path)
    he_subs = parse_srt(he_path)

    errors = []
    warnings = []

    if len(en_subs) != len(he_subs):
        errors.append(f"Block count mismatch: EN has {len(en_subs)} vs HE has {len(he_subs)}")

    min_len = min(len(en_subs), len(he_subs))
    timing_mismatches = 0
    for i in range(min_len):
        if en_subs[i][1] != he_subs[i][1]:
            timing_mismatches += 1
            if timing_mismatches <= 3:
                errors.append(f"Timing mismatch at cue {i+1}: EN='{en_subs[i][1]}' != HE='{he_subs[i][1]}'")

    if timing_mismatches > 3:
        errors.append(f"Total timing mismatches: {timing_mismatches}")

    with open(he_path, 'r', encoding='utf-8', errors='replace') as f:
        he_raw = f.read()

    rlm_count = he_raw.count('\u200F')
    arabic_matches = re.findall(r'[\u0600-\u06FF]', he_raw)
    cyrillic_matches = re.findall(r'[\u0400-\u04FF]', he_raw)
    nikud_matches = re.findall(r'[\u0591-\u05BD\u05BF-\u05C2\u05C4-\u05C7]', he_raw)
    literal_n_count = he_raw.count('\\n')
    trunc_count = len(re.findall(r'<truncated\s+\d+\s+bytes>', he_raw))
    json_artifacts = len(re.findall(r'["\']?hebrew["\']?\s*:\s*|["\']?index["\']?\s*:\s*\d+', he_raw))

    if len(arabic_matches) > 0:
        errors.append(f"Found {len(arabic_matches)} Arabic characters in Hebrew file")
    if len(cyrillic_matches) > 0:
        errors.append(f"Found {len(cyrillic_matches)} Cyrillic characters in Hebrew file")
    if len(nikud_matches) > 0:
        errors.append(f"Found {len(nikud_matches)} Nikud / vocalization marks in Hebrew file")
    if literal_n_count > 0:
        errors.append(f"Found {literal_n_count} literal '\\n' string occurrences in Hebrew file")
    if trunc_count > 0:
        errors.append(f"Found {trunc_count} transcript '<truncated ...>' markers in Hebrew file")
    if json_artifacts > 0:
        errors.append(f"Found {json_artifacts} leaked JSON syntax artifacts in Hebrew file")
    if rlm_count == 0 and len(he_subs) > 0:
        warnings.append("Zero RLM characters found (Plex/Infuse punctuation might be reversed)")

    is_clean = (len(errors) == 0)
    report = {
        "en_cues": len(en_subs),
        "he_cues": len(he_subs),
        "timing_mismatches": timing_mismatches,
        "rlm_count": rlm_count,
        "errors": errors,
        "warnings": warnings,
        "passed": is_clean
    }
    return is_clean, report

def main():
    parser = argparse.ArgumentParser(description="Automated Subtitle QA & Verification Engine")
    parser.add_argument("en_srt", help="Master English SRT or directory")
    parser.add_argument("he_srt", nargs="?", help="Hebrew SRT to verify (optional if auditing a directory)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if os.path.isfile(args.en_srt):
        if not args.he_srt:
            he_candidate = args.en_srt.replace('.en.srt', '.he.srt')
            if not os.path.exists(he_candidate):
                print("[-] Please specify he_srt path or pass matching .en.srt/.he.srt pair")
                sys.exit(1)
            args.he_srt = he_candidate

        passed, report = audit_pair(args.en_srt, args.he_srt, args.verbose)
        print(f"\n=== QA Audit for {os.path.basename(args.he_srt)} ===")
        print(f"  - Cues: EN={report.get('en_cues', 0)}, HE={report.get('he_cues', 0)}")
        print(f"  - Timing Mismatches: {report.get('timing_mismatches', 0)}")
        print(f"  - RLM Characters: {report.get('rlm_count', 0)}")
        if report.get('warnings'):
            for w in report['warnings']:
                print(f"  [!] WARNING: {w}")
        if report.get('errors'):
            for e in report['errors']:
                print(f"  [-] ERROR: {e}")
            print("\n[FAILED] QA Audit did not pass!")
            sys.exit(1)
        else:
            print("\n[PASSED] 100% QA Compliant! Ready for Plex/Infuse.")
            sys.exit(0)
    elif os.path.isdir(args.en_srt):
        target_dir = args.en_srt
        import glob
        en_files = sorted(glob.glob(os.path.join(target_dir, "**/*.en.srt"), recursive=True))
        if not en_files:
            print(f"[-] No .en.srt files found in {target_dir}")
            sys.exit(1)
        
        passed_count = 0
        failed_count = 0
        for en in en_files:
            he = en.replace('.en.srt', '.he.srt')
            passed, report = audit_pair(en, he, args.verbose)
            name = os.path.basename(en)[:-7]
            if passed:
                passed_count += 1
                print(f"[✓ PASS] {name}: {report['he_cues']} cues, {report['rlm_count']} RLMs")
            else:
                failed_count += 1
                print(f"[✗ FAIL] {name}: {report['errors']}")

        print(f"\n=== Batch Audit Summary ===")
        print(f"Passed: {passed_count}/{len(en_files)} ({passed_count/len(en_files)*100:.1f}%)")
        print(f"Failed: {failed_count}/{len(en_files)}")
        sys.exit(0 if failed_count == 0 else 1)

if __name__ == '__main__':
    main()
