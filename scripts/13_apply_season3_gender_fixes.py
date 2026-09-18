#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
13_apply_season3_gender_fixes.py
---------------------------------
Applies surgical gender fixes, shift resynchronizations, full content restoration
from .bak.v25 for truncated episodes (S17-S20), translation of S03E10 cues 386-452,
and strict 1..N re-indexing with Plex/Infuse compliant RLM markers across all 24
episodes of Boston Legal Season 3.
"""

import os
import re
import sys

MEDIA_DIR = "/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p/Season 3"

# Import official apply_rlm_to_line from 07_fix_plex_punctuation.py
sys.path.insert(0, "/Volumes/Other/Antigravity/RightSub/scripts")
from importlib import import_module
fix_plex = import_module("07_fix_plex_punctuation")
apply_rlm_to_line = fix_plex.apply_rlm_to_line
clean_and_sanitize_text = fix_plex.clean_and_sanitize_text

def parse_srt_blocks(filepath):
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        content = f.read().strip()
    raw_blocks = re.split(r"\n\s*\n", content)
    blocks = []
    for b in raw_blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            try:
                timing = lines[1].strip()
                text_lines = lines[2:]
                blocks.append((timing, text_lines))
            except Exception:
                continue
    return blocks

def format_clean_hebrew(text_lines):
    cleaned = []
    for line in text_lines:
        c = clean_and_sanitize_text(line)
        if c:
            c = apply_rlm_to_line(c)
            cleaned.append(c)
    return cleaned

def clean_he(t):
    return re.sub(r"[\u200e\u200f]", "", t).strip()

def process_season3():
    print("Starting Boston Legal Season 3 Gender & Formatting Fixes...")

    for ep_num in range(1, 25):
        ep = f"S03E{ep_num:02d}"
        en_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.en.srt")
        he_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.he.srt")
        bak_v25_path = os.path.join(MEDIA_DIR, f"Boston Legal {ep}.he.srt.bak.v25")

        en_blocks = parse_srt_blocks(en_path)

        # 1. Source selection: Restore truncated episodes (17..20) from bak.v25
        if 17 <= ep_num <= 20 and os.path.exists(bak_v25_path):
            source_path = bak_v25_path
            print(f"[{ep}] Restoring complete translation from {os.path.basename(bak_v25_path)} (recovering from truncation)...")
        else:
            source_path = he_path

        he_blocks = parse_srt_blocks(source_path)

        if len(en_blocks) != len(he_blocks):
            print(f"[{ep}] ERROR: Block count mismatch! EN={len(en_blocks)}, HE={len(he_blocks)}")
            sys.exit(1)

        # Convert to mutable list of text line lists
        he_texts = [list(lines) for _, lines in he_blocks]

        # 2. Resynchronize merge shifts
        if ep == "S03E03":
            print("[S03E03] Applying merge shift resynchronization (cues 468-542)...")
            # Cue 468 (idx 467): Split into 468 and 469
            he_texts[467] = ["האם ראית מישהו מלבד סקוט ליטל"]
            he_texts.insert(468, ["מגיע לשם באותו לילה? לא."])
            # Delete redundant duplicate at 542 (now idx 542)
            del he_texts[542]

        elif ep == "S03E10":
            print("[S03E10] Correcting cues 386-452 (matching actual video audio & storylines)...")
            corrections_s03e10 = {
                386: ["לתבוע את הכנסייה? למה לא?"],
                387: ["מכת ברק היא כוח עליון."],
                388: ["הכנסייה מציגה את עצמה כנציגה של אלוהים."],
                389: ["בוא נתבע את האפיסקופלים. זה מגוחך."],
                390: ["יש לך רעיון טוב יותר? אתה זה שאמור להיות עם הרעיונות הטובים יותר,"],
                391: ["כי אמרת שנוכל לנצח בזה בפסק דין מקוצר. טוב, הנה רעיון."],
                392: ["למה שלא נגיד לשופט שיישק לנו בתחת?"],
                393: ["זה יכול לעבוד די יפה אם אומרים את זה בדיוק כמו שצריך."],
                394: ["תן לי להתאמן. שק לי בתחת."],
                395: ["מה אתה חושב?"],
                396: ["או... לא, לא!"],
                397: ["לא, לא, לא, לא, לא!"],
                398: ["אה-אה. זה מספיק."],
                399: [],
                400: ["אני לא משתמשת בסמים, ואני לא שותה."],
                401: ["אני לוקחת קורסים מתקדמים, ומקבלת רק מאיות."],
                402: ["ואת מסיימת את הלימודים מוקדם?"],
                403: ["בהצטיינות."],
                404: ["יש לך גם אתר אינטרנט, נכון?"],
                405: ["הוא נקרא ת'ינספייר."],
                406: ["זו קהילת תמיכה לנשים צעירות עם מטרות."],
                407: ["אנחנו מפרסמות מאמרים והצעות"],
                408: ["כיצד לחיות חיים מלאי השראה לרזון."],
                409: ["וכיצד את מתכננת"],
                410: ["לפרנס את עצמך כלכלית? אני מדגמנת."],
                411: ["ובכן, אני רק בתחילת הדרך, באמת."],
                412: ["עשיתי תצוגות אופנה לכמה חנויות כלבו מקומיות,"],
                413: ["אבל לאחרונה קיבלתי הרבה עבודות לקטלוגים."],
                414: ["זו עבודה די קבועה, ואני מרוויחה כ-125 דולר לשעה."],
                415: ["נשמע לי שאת מסתדרת"],
                416: ["די יפה בעצמך, גב' וילסון."],
                417: ["כן, בהחלט."],
                418: ["מה אכלת לארוחת בוקר הבוקר?"],
                419: ["שתיתי משקה דיאטטי"],
                420: ["וקרקר עם קצת תרסיס חמאה עליו."],
                421: ["וארוחת צהריים? לא אכלתי ארוחת צהריים."],
                422: ["אני לא מסוגלת לאכול כשאני בלחץ."],
                423: ["אז כמה קלוריות צרכת היום?"],
                424: ["16."],
                425: ["האם את מודעת לכך שהכמות היומית הנדרשת"],
                426: ["של קלוריות למישהי בגילך ובגובה שלך"],
                427: ["נעה בין 1,800 ל-2,400?"],
                428: ["והאם את מודעת לכך ששניים מתוך שלושה אמריקאים"],
                429: ["סובלים מעודף משקל?"],
                430: ["אף אחד לא קורא להם חולים. אני בריאה."],
                431: ["אני שומרת על מה שאני אוכלת, ואני מתעמלת."],
                432: ["את יכולה לשאול כל בחורה שמנה בבית הספר שלי"],
                433: ["אם היא הייתה רוצה להתחלף איתי. עכשיו אל תרדי על בחורות שמנות."],
                434: ["אני אוהב סקס עם שמנמנות, ואני בטוח שכבודו גם. מר קריין!"],
                435: ["גב' וילסון..."],
                436: ["האם את מודעת לכך"],
                437: ["שמדריך האבחון והסטטיסטיקה של הפרעות נפשיות"],
                438: ["מגדיר אנורקסיה נרבוזה"],
                439: ["כמחלת נפש?"],
                440: ["לפני 30 שנה אמרו את אותו הדבר על הומוסקסואליות."],
                441: ["בדיוק!"],
                442: ["אין לי שאלות נוספות."],
                443: [],
                444: ["אני לא מבין."],
                445: ["למה הוא צריך לשמוע טיעוני סיכום?"],
                446: ["זו החלטה פשוטה. מה לא בסדר עם השופט הזה?"],
                447: ["ובכן, אולי הוא פשוט בעל דעות קדומות נגד,"],
                448: ["אתם יודעים, גלוחי ראש."],
                449: ["אני נראה כמו גלוח ראש, מר שור?"],
                450: ["נאמר לי שהם יכולים להופיע במגוון צורות."],
                451: ["היי, אם אתה בעל דעות קדומות נגדנו--"],
                452: ["* קומו והאירו"],
            }
            for cue, lines in corrections_s03e10.items():
                he_texts[cue - 1] = lines

        elif ep == "S03E11":
            print("[S03E11] Applying merge shift resynchronization (cues 364-441)...")
            # Insert empty cue at 364 (idx 363)
            he_texts.insert(363, [])
            # Delete empty cue at 441 (now idx 441)
            del he_texts[441]

        elif ep == "S03E24":
            print("[S03E24] Applying merge shift resynchronization (cues 315-349)...")
            # Cue 315 (idx 314): Split into 315 and 316
            he_texts[314] = ["קשורה יותר לקבלת תשומת לב"]
            he_texts.insert(315, ["כדי להסיח את דעתי ממה שהפכתי להיות..."])
            # Delete redundant duplicate at 349 (now idx 349)
            del he_texts[349]

        # 3. Episode-specific surgical gender fixes
        def replace_in_cue(cue_num, old_sub, new_sub):
            idx = cue_num - 1
            if idx < len(he_texts):
                lines = he_texts[idx]
                updated = []
                for l in lines:
                    c = clean_he(l)
                    if old_sub in c:
                        c = c.replace(old_sub, new_sub)
                    updated.append(c)
                he_texts[idx] = updated

        if ep == "S03E14":
            # Judge Gloria Weldon (addressed as female judge)
            replace_in_cue(38, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(117, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(134, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(163, "כבוד השופט, האם אתה באמת רוצה", "כבוד השופטת, האם את באמת רוצה")
            replace_in_cue(169, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(181, "כבוד השופט", "כבוד השופטת")
            # Judge Weldon speaking in 1st-person feminine
            replace_in_cue(197, "אני שמח", "אני שמחה")
            replace_in_cue(587, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(755, "כבוד השופט", "כבוד השופטת")

        elif ep == "S03E18":
            # Addressing Shirley Schmidt
            replace_in_cue(177, "אתה, מי אתה?", "את, מי את?")

        elif ep == "S03E20":
            # Judge Gloria Weldon
            replace_in_cue(6, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(11, "כבוד השופט", "כבוד השופטת")

        elif ep == "S03E22":
            # Judge Folger (female judge)
            replace_in_cue(661, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(672, "כבוד השופט", "כבוד השופטת")
            replace_in_cue(763, "השופט פולגר", "השופטת פולג'ר")

        # 4. Strict 1..N re-indexing and dual RLM formatting
        output_blocks = []
        for i, ((timing, _), lines) in enumerate(zip(en_blocks, he_texts)):
            clean_lines = format_clean_hebrew(lines)
            output_blocks.append((i + 1, timing, clean_lines))

        # Write output file
        with open(he_path, "w", encoding="utf-8") as f:
            for cue_num, timing, lines in output_blocks:
                f.write(f"{cue_num}\n")
                f.write(f"{timing}\n")
                if lines:
                    f.write("\n".join(lines) + "\n")
                else:
                    f.write("\n")
                f.write("\n")

        print(f"[{ep}] Successfully written {len(output_blocks)} cues to {os.path.basename(he_path)}")

    print("\nSeason 3 processing completed successfully.")

if __name__ == "__main__":
    process_season3()
