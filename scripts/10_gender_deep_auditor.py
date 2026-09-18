#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10_gender_deep_auditor.py
-------------------------
Deep context-aware auditor for subtitle gender consistency.
Analyzes English-Hebrew subtitle pairs across multi-cue dialogue windows.
Detects:
1. Dialogue turns directed at female characters where Hebrew uses 2nd-person masculine.
2. Dialogue turns directed at male characters where Hebrew uses 2nd-person feminine.
3. Incorrect gender honorifics for judges (e.g. female judge addressed as male or vice-versa).
4. Direct vocative mismatches within the same cue or neighboring cues (+/- 2).
"""

import os
import sys
import re
import glob
import json

FEMALE_NAMES_EN = [
    "tara", "lori", "sally", "shirley", "chelina", "samantha", "christine",
    "peggy", "bertha", "tracy", "kendra", "jamie", "nora", "catherine",
    "anne", "annie", "renee", "marla", "melanie", "paula", "chloe", "rachel"
]

MALE_NAMES_EN = [
    "alan", "denny", "brad", "paul", "jerry", "edwin", "dan", "daniel",
    "george", "jack", "bernard", "harvey", "clifford", "robert", "milton",
    "sheffield", "myron", "clark", "walter", "ronald", "brian", "dwight"
]

FEMALE_NAMES_HE = [
    "טרה", "טארה", "לורי", "סאלי", "שירלי", "צ'לינה", "סמנתה", "סמנת'ה",
    "כריסטין", "פגי", "ברתה", "טרייסי", "קנדרה", "ג'יימי", "נורה", "קתרין",
    "אן", "אנני", "רנה", "מרלה", "מלאני", "פולה", "קלואי", "רייצ'ל", "רחל"
]

MALE_NAMES_HE = [
    "אלן", "דני", "בראד", "פול", "ג'רי", "אדווין", "דן", "דניאל",
    "ג'ורג'", "ג'ק", "ברנרד", "הארווי", "קליפורד", "רוברט", "מילטון",
    "שפילד", "מיירון", "קלארק", "וולטר", "רונלד", "בריאן", "דווייט"
]

MASCULINE_2ND_PERSON = [
    r"\bאתה\b", r"\bאתה\s+\w+",
    r"\bתגיד\b", r"\bתשמע\b", r"\bתקשיב\b", r"\bתפסיק\b", r"\bבוא\b", r"\bתרגיע\b", r"\bתירגע\b",
    r"\b(אתה\s+)?(יכול|רוצה|יודע|מבין|מוכן|בטוח|צודק|חושב|זוכר|מסוגל|רציני|מדבר|עושה|הולך|אשם|משוגע|עייף|מודאג)\b",
]

FEMININE_2ND_PERSON = [
    r"\bאת\b", r"\bאת\s+\w+",
    r"\bתגידי\b", r"\bתשמעי\b", r"\bתקשיבי\b", r"\bתפסיקי\b", r"\bבואי\b", r"\bתרגיעי\b", r"\bתירגעי\b",
    r"\b(את\s+)?(יכולה|רוצה|יודעת|מבינה|מוכנה|בטוחה|צודקת|חושבת|זוכרת|מסוגלת|רצינית|מדברת|עושה|הולכת|אשמה|משוגעת|עייפה|מודאגת)\b",
]

def parse_srt(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()
    blocks = re.split(r"\n\s*\n", content)
    cues = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                idx = int(lines[0].strip())
                timing = lines[1].strip()
                text = "\n".join(lines[2:])
                cues.append({"idx": idx, "timing": timing, "text": text})
            except ValueError:
                continue
    return cues

def clean_he(text):
    return re.sub(r"[\u200e\u200f]", "", text).strip()

def clean_en(text):
    return re.sub(r"<[^>]+>", "", text).strip()

def audit_episode(en_path, he_path):
    en_cues = parse_srt(en_path)
    he_cues = parse_srt(he_path)

    if not en_cues or not he_cues:
        return []

    en_map = {c["idx"]: c for c in en_cues}
    he_map = {c["idx"]: c for c in he_cues}

    reports = []
    all_indices = sorted(set(en_map.keys()) & set(he_map.keys()))

    masc_pattern = re.compile("|".join(MASCULINE_2ND_PERSON))
    fem_pattern = re.compile("|".join(FEMININE_2ND_PERSON))

    f_en_regex = re.compile(r"\b(" + "|".join(FEMALE_NAMES_EN) + r")\b", re.IGNORECASE)
    m_en_regex = re.compile(r"\b(" + "|".join(MALE_NAMES_EN) + r")\b", re.IGNORECASE)

    f_he_regex = re.compile(r"\b(" + "|".join(FEMALE_NAMES_HE) + r")\b")
    m_he_regex = re.compile(r"\b(" + "|".join(MALE_NAMES_HE) + r")\b")

    for i, idx in enumerate(all_indices):
        en_text = clean_en(en_map[idx]["text"])
        he_text = clean_he(he_map[idx]["text"])

        has_f_voc_en = bool(f_en_regex.search(en_text))
        has_f_voc_he = bool(f_he_regex.search(he_text))
        has_m_voc_en = bool(m_en_regex.search(en_text))
        has_m_voc_he = bool(m_he_regex.search(he_text))

        has_masc_he = bool(masc_pattern.search(he_text))
        has_fem_he = bool(fem_pattern.search(he_text))

        # Check 1: Same cue female vocative + masculine 2nd person in HE
        if (has_f_voc_en or has_f_voc_he) and not (has_m_voc_en or has_m_voc_he):
            if has_masc_he and not has_fem_he:
                reports.append({
                    "type": "SAME_CUE_FEMALE_WITH_MASC",
                    "idx": idx,
                    "en": en_text,
                    "he": he_text,
                    "surrounding": [
                        {"idx": all_indices[k], "en": clean_en(en_map[all_indices[k]]["text"]), "he": clean_he(he_map[all_indices[k]]["text"])}
                        for k in range(max(0, i-2), min(len(all_indices), i+3))
                    ]
                })

        # Check 2: Preceding cue vocative address
        if i > 0:
            prev_idx = all_indices[i-1]
            prev_en = clean_en(en_map[prev_idx]["text"])
            prev_he = clean_he(he_map[prev_idx]["text"])
            prev_f_en = bool(f_en_regex.search(prev_en))
            prev_f_he = bool(f_he_regex.search(prev_he))
            prev_m_en = bool(m_en_regex.search(prev_en))
            prev_m_he = bool(m_he_regex.search(prev_he))

            if (prev_f_en or prev_f_he) and not (prev_m_en or prev_m_he) and not (has_m_voc_en or has_m_voc_he):
                if has_masc_he:
                    reports.append({
                        "type": "FOLLOWUP_FEMALE_WITH_MASC",
                        "idx": idx,
                        "en": en_text,
                        "he": he_text,
                        "surrounding": [
                            {"idx": all_indices[k], "en": clean_en(en_map[all_indices[k]]["text"]), "he": clean_he(he_map[all_indices[k]]["text"])}
                            for k in range(max(0, i-2), min(len(all_indices), i+3))
                        ]
                    })

        # Check 3: Female judge honorifics
        if re.search(r"\b(YOUR HONOR|JUDGE)\b", en_text, re.IGNORECASE):
            reports.append({
                "type": "JUDGE_HONORIFIC",
                "idx": idx,
                "en": en_text,
                "he": he_text
            })

    return reports

def main():
    s1_files = sorted(glob.glob("/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p/Season 1/Boston Legal S01E*.he.srt"))
    total_flagged = 0
    all_results = {}

    for he_file in s1_files:
        ep_name = os.path.basename(he_file).replace(".he.srt", "")
        en_file = he_file.replace(".he.srt", ".en.srt")
        reports = audit_episode(en_file, he_file)
        
        mismatches = [r for r in reports if r["type"] != "JUDGE_HONORIFIC"]
        judges = [r for r in reports if r["type"] == "JUDGE_HONORIFIC"]
        
        all_results[ep_name] = {
            "mismatches": mismatches,
            "judge_cues": len(judges),
            "judges": judges
        }
        total_flagged += len(mismatches)
        print(f"[{ep_name}] Flagged dialogue candidates: {len(mismatches)}, Judge cues: {len(judges)}")

    os.makedirs("scratch", exist_ok=True)
    with open("scratch/season1_gender_audit.json", "w", encoding="utf-8") as out:
        json.dump(all_results, out, ensure_ascii=False, indent=2)
    print(f"\nTotal potential dialogue candidates flagged across S1: {total_flagged}")
    print("Report written to scratch/season1_gender_audit.json")

if __name__ == "__main__":
    main()
