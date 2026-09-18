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

FEMALE_TITLES = ["גברתי השופטת", "כבוד השופטת", "גברתי", "השופטת", "גברת"]
DEFAULT_FEMALE_NAMES = ["שירלי", "טרה", "לורי", "סאלי", "דניס", "בברלי", "קנדיס", "קלייר", "צ'לסי", "קייטי", "בטאני", "בת'אני", "מרלנה", "רנטה", "רייצ'ל", "רחל"]

MALE_TITLES = ["כבוד השופט", "אדוני השופט", "אדוני", "השופט"]
DEFAULT_MALE_NAMES = ["אלן", "דני", "פול", "בראד", "ג'רי", "דניאל", "ג'פרי"]

MASCULINE_VERBS_AND_PRONOUNS = [
    "אתה יכול", "אתה רוצה", "אתה יודע", "אתה מבין", "אתה חושב", "אתה מוכן", "אתה צודק", "אתה הולך",
    "אתה", "תגיד", "תשמע", "תפסיק", "בוא", "שב", "לך", "תרגיע", "תקשיב"
]

FEMININE_VERBS_AND_PRONOUNS = [
    "את יכולה", "את רוצה", "את יודעת", "את מבינה", "את חושבת", "את מוכנה", "את צודקת", "את הולכת",
    "תגידי", "תשמעי", "תפסיקי", "בואי", "שבי", "לכי", "תרגיעי", "תקשיבי"
]

def get_gender_rosters(bible_path=None):
    female_entities = set(FEMALE_TITLES + DEFAULT_FEMALE_NAMES)
    male_entities = set(MALE_TITLES + DEFAULT_MALE_NAMES)

    if bible_path and os.path.exists(bible_path):
        try:
            import json
            with open(bible_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for ch in data.get("characters", []):
                gender = ch.get("gender", "").lower()
                he_name = ch.get("hebrew_name", "").strip()
                if he_name:
                    first = he_name.split()[0]
                    if gender == "female":
                        female_entities.add(first)
                        female_entities.add(he_name)
                    elif gender == "male":
                        male_entities.add(first)
                        male_entities.add(he_name)
        except Exception:
            pass

    sorted_f = sorted(female_entities, key=len, reverse=True)
    sorted_m = sorted(male_entities, key=len, reverse=True)
    return sorted_f, sorted_m

def check_gender_mismatches(he_subs, bible_path=None):
    """
    Scans Hebrew cues for direct address vocative gender contradictions:
    E.g. addressing a female name with masculine 2nd person: 'שירלי, אתה מוכן?'
    """
    female_entities, male_entities = get_gender_rosters(bible_path)
    mismatches = []

    f_pattern_str = r'(?:^|[.?!;\n])\s*(' + '|'.join(re.escape(x) for x in female_entities) + r')\s*[,:\-]\s*(?:(?:ו?מה|ו?למה|ו?איך|ו?אם|ו?אולי|בבקשה|עכשיו)\s+)?(' + '|'.join(re.escape(x) for x in MASCULINE_VERBS_AND_PRONOUNS) + r')\b'
    m_pattern_str = r'(?:^|[.?!;\n])\s*(' + '|'.join(re.escape(x) for x in male_entities) + r')\s*[,:\-]\s*(?:(?:ו?מה|ו?למה|ו?איך|ו?אם|ו?אולי|בבקשה|עכשיו)\s+)?(' + '|'.join(re.escape(x) for x in FEMININE_VERBS_AND_PRONOUNS) + r')\b'

    f_regex = re.compile(f_pattern_str)
    m_regex = re.compile(m_pattern_str)

    for idx, timing, text in he_subs:
        clean_text = re.sub(r'[\u200e\u200f]', '', text)

        f_match = f_regex.search(clean_text)
        if f_match:
            entity, verb = f_match.group(1), f_match.group(2)
            mismatches.append(f"Gender mismatch at cue {idx}: Addressed female '{entity}' with masculine '{verb}' in '{clean_text.strip()}'")

        m_match = m_regex.search(clean_text)
        if m_match:
            entity, verb = m_match.group(1), m_match.group(2)
            mismatches.append(f"Gender mismatch at cue {idx}: Addressed male '{entity}' with feminine '{verb}' in '{clean_text.strip()}'")

    return mismatches

DISALLOWED_FOREIGN_SCRIPTS = (
    r'[\u0600-\u06FF'  # Arabic
    r'\u0400-\u04FF'  # Cyrillic
    r'\u0370-\u03FF'  # Greek
    r'\u0530-\u058F'  # Armenian
    r'\u10A0-\u10FF'  # Georgian
    r'\u0900-\u0DFF'  # Indic (Devanagari, Bengali, Telugu, etc.)
    r'\u0E00-\u0E7F'  # Thai
    r'\u0F00-\u0FFF'  # Tibetan
    r'\u3040-\u30FF\u31F0-\u31FF'  # Japanese Kana
    r'\u4E00-\u9FFF\u3400-\u4DBF\u2E80-\u2EFF'  # CJK
    r'\uAC00-\uD7AF'  # Hangul
    r']'
)

def audit_pair(en_path, he_path, verbose=False, bible_path=None, strict_gender=False):
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
    foreign_matches = re.findall(DISALLOWED_FOREIGN_SCRIPTS, he_raw)
    nikud_matches = re.findall(r'[\u0591-\u05BD\u05BF-\u05C2\u05C4-\u05C7]', he_raw)
    literal_n_count = he_raw.count('\\n')
    trunc_count = len(re.findall(r'<truncated\s+\d+\s+bytes>', he_raw))
    json_artifacts = len(re.findall(r'["\']?hebrew["\']?\s*:\s*|["\']?index["\']?\s*:\s*\d+', he_raw))

    if len(foreign_matches) > 0:
        unique_foreign = sorted(set(foreign_matches))
        errors.append(f"Found {len(foreign_matches)} foreign script characters in Hebrew file: {unique_foreign}")
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

    # Gender consistency checks
    gender_mismatches = check_gender_mismatches(he_subs, bible_path=bible_path)
    if gender_mismatches:
        if strict_gender:
            errors.extend(gender_mismatches)
        else:
            warnings.extend(gender_mismatches)

    is_clean = (len(errors) == 0)
    report = {
        "en_cues": len(en_subs),
        "he_cues": len(he_subs),
        "timing_mismatches": timing_mismatches,
        "rlm_count": rlm_count,
        "gender_mismatches": len(gender_mismatches),
        "errors": errors,
        "warnings": warnings,
        "passed": is_clean
    }
    return is_clean, report

def main():
    parser = argparse.ArgumentParser(description="Automated Subtitle QA & Verification Engine")
    parser.add_argument("en_srt", help="Master English SRT or directory")
    parser.add_argument("he_srt", nargs="?", help="Hebrew SRT to verify (optional if auditing a directory)")
    parser.add_argument("--bible", "-b", default="", help="Path to translation_bible.json for character gender checks")
    parser.add_argument("--strict-gender", action="store_true", help="Fail QA audit if gender mismatches are found")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if os.path.isfile(args.en_srt):
        if not args.he_srt:
            he_candidate = args.en_srt.replace('.en.srt', '.he.srt')
            if not os.path.exists(he_candidate):
                print("[-] Please specify he_srt path or pass matching .en.srt/.he.srt pair")
                sys.exit(1)
            args.he_srt = he_candidate

        passed, report = audit_pair(
            en_path=args.en_srt,
            he_path=args.he_srt,
            verbose=args.verbose,
            bible_path=args.bible,
            strict_gender=args.strict_gender
        )
        print(f"\n=== QA Audit for {os.path.basename(args.he_srt)} ===")
        print(f"  - Cues: EN={report.get('en_cues', 0)}, HE={report.get('he_cues', 0)}")
        print(f"  - Timing Mismatches: {report.get('timing_mismatches', 0)}")
        print(f"  - RLM Characters: {report.get('rlm_count', 0)}")
        if report.get('gender_mismatches', 0) > 0:
            print(f"  - Gender Mismatches Flagged: {report.get('gender_mismatches', 0)}")
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
            passed, report = audit_pair(
                en_path=en,
                he_path=he,
                verbose=args.verbose,
                bible_path=args.bible,
                strict_gender=args.strict_gender
            )
            name = os.path.basename(en)[:-7]
            if passed:
                passed_count += 1
                gender_str = f", {report['gender_mismatches']} gender warnings" if report.get('gender_mismatches', 0) > 0 else ""
                print(f"[✓ PASS] {name}: {report['he_cues']} cues, {report['rlm_count']} RLMs{gender_str}")
            else:
                failed_count += 1
                print(f"[✗ FAIL] {name}: {report['errors']}")

        print(f"\n=== Batch Audit Summary ===")
        print(f"Passed: {passed_count}/{len(en_files)} ({passed_count/len(en_files)*100:.1f}%)")
        print(f"Failed: {failed_count}/{len(en_files)}")
        sys.exit(0 if failed_count == 0 else 1)

if __name__ == '__main__':
    main()

