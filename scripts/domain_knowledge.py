#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
domain_knowledge.py
-------------------
Hierarchical Domain Knowledge & Genre Resolution Engine for RightSub.

Architecture:
1. Multi-Tiered Context Ingestion:
   - Tier 1: Ground-truth TMDb metadata & Translation Bible (genres, overview, characters, tone).
   - Tier 2: AI preliminary context analysis.
   - Tier 3: Zero-External Offline Fallback (lexical cue vocabulary fingerprinting + title pattern matching).
2. Modular Domain Packs:
   - SCI_FI: Spaceflight, energy shields, robotics, futuristic weaponry, warp/hyperspace.
   - MILITARY: Tactical comms, chain of command, aviation, rank structure, recon.
   - LEGAL: Courtroom procedures, objections, counsel, motions, verdicts.
   - MEDICAL: Triage, resuscitation, surgical procedures, clinical terms.
   - FANTASY: Medieval lore, magic, mythical races, archaic/ceremonial address.
   - GENERAL_IDIOMS: Common literal machine-translation blunders across all film genres.
3. Bilingual Anchor Validation (Cross-Lingual Guard):
   - Deterministic replacements only trigger when BOTH the English master cue contains the
     source trigger AND the Hebrew cue contains the mistranslation (zero false-positive risk).
"""

import re
from typing import List, Dict, Optional, Tuple, Set

# ==============================================================================
# 1. FRANCHISE LORE & CANON PACKS
# ==============================================================================

FRANCHISE_PACKS = {
    "star wars": {
        "title_patterns": [r"\bstar\s*wars\b", r"\b4k77\b", r"\b4k80\b", r"\b4k83\b", r"\bskywalker\b", r"\bmandalorian\b", r"\bahsoka\b", r"\bandor\b"],
        "domains": ["sci_fi", "military"],
        "canon_terms": [
            (r"(?<![א-ת])חרב\s*[-–—]?\s*הלייזר(?![א-ת])", "חרב האור", "מינוח קאנוני (Lightsaber = חרב אור)"),
            (r"(?<![א-ת])חרב\s*[-–—]?\s*לייזר(?![א-ת])", "חרב אור", "מינוח קאנוני (Lightsaber = חרב אור)"),
            (r"(?<![א-ת])חרבות\s*[-–—]?\s*הלייזר(?![א-ת])", "חרבות האור", "מינוח קאנוני (Lightsabers = חרבות אור)"),
            (r"(?<![א-ת])חרבות\s*[-–—]?\s*לייזר(?![א-ת])", "חרבות אור", "מינוח קאנוני (Lightsabers = חרבות אור)"),
            (r"(?<![א-ת])בז\s*אלף\s*השנים(?![א-ת])", "המילניום פלקון", "מינוח קאנוני (Millennium Falcon)"),
            (r"דארת\s*,\s*ויידא?ר", "דארת' ויידר", "תיקון איות ופסיק (דארת' ויידר)"),
            (r"דארת\.,", "דארת',", "תיקון פיסוק"),
            (r"(?<![א-ת])ויידאר(?![א-ת])", "ויידר", "תיקון איות ארכאי (ויידר)"),
            (r"(?<![א-ת])(ה)?גרנד\s*מוף(?![א-ת])", r"\g<1>גראנד מופ", "מינוח קאנוני (Grand Moff)"),
            (r"(?<![א-ת])כוכב\s*מוות(?![א-ת])", "כוכב המוות", "מינוח קאנוני (Death Star)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?חייל\s*סער(?![א-ת])", r"\g<1>לוחם סער", "מינוח קאנוני (Stormtrooper)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?חיילי\s*סער(?![א-ת])", r"\g<1>לוחמי סער", "מינוח קאנוני (Stormtroopers)"),
            (r"(?<![א-ת])הצד\s*החשוך(?![א-ת])", "הצד האפל", "מינוח קאנוני (Dark Side)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?מעשה\s*בראשית(?![א-ת])", r"\g<1>למעשה", "תיקון ביטוי שגוי (As a matter of fact = למעשה ולא מעשה בראשית)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?קאבתן(?![א-ת])", r"\g<1>קברניט", "תיקון תעתיק פונטי שגוי (Captain = קברניט/קפטן ולא קאבתן)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?מכלית\s*קרב(?![א-ת])", r"\g<1>חללית קרב", "מינוח מדויק (snub fighter = חללית קרב)"),
            (r"(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?קרן\s*משיכה(?![א-ת])", r"\g<1>קרן גרירה", "מינוח קאנוני (Tractor Beam = קרן גרירה ולא קרן משיכה)"),
            (r"(?<![א-ת])לשום\s+את(?![א-ת])", "לשים את", "תיקון שגיאת כתיב (לשים ולא לשום)"),
            (r"(?<![א-ת])מוחב\s+אותנו(?![א-ת])", "מושכת אותנו", "תיקון שגיאת כתיב (מושכת ולא מוחב)"),
            (r"(?<![א-ת])אובי\s*[-–—]?\s*וואן\s+קאנובי(?![א-ת])", "אובי-וואן קנובי", "תיקון איות קאנוני (קנובי)"),
            (r"(?<![א-ת])סי\s*[-–—]?\s*ת'?ריפיאו(?![א-ת])", "סי-ת'ריפיו", "תיקון איות קאנוני (C-3PO)"),
            (r"(?<![א-ת])ארטו\s*[-–—]?\s*דיטו(?![א-ת])", "ארטו-דיטו", "תיקון איות קאנוני (R2-D2)"),
        ],
        "characters": [
            {"name": "Princess Leia", "he_name": "הנסיכה ליאה", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Luke Skywalker", "he_name": "לוק סקייווקר", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Han Solo", "he_name": "האן סולו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Darth Vader", "he_name": "דארת' ויידר", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Obi-Wan Kenobi", "he_name": "אובי-וואן קנובי", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Grand Moff Tarkin", "he_name": "גראנד מופ טארקין", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "C-3PO", "he_name": "סי-ת'ריפיו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "R2-D2", "he_name": "ארטו-דיטו", "gender": "Male", "pronouns": "אתה/הוא"},
        ]
    },
    "star trek": {
        "title_patterns": [r"\bstar\s*trek\b", r"\benterprise\b", r"\bvoyager\b", r"\bdeep\s*space\s*nine\b", r"\bpicard\b"],
        "domains": ["sci_fi", "military"],
        "canon_terms": [
            (r"(?<![א-ת])קרן\s*השתגרות(?![א-ת])", "טרנספורטר", "מינוח קאנוני (Transporter)"),
            (r"(?<![א-ת])ווארפ\s*דרייב(?![א-ת])", "הנעת ווארפ", "מינוח קאנוני (Warp Drive)"),
            (r"(?<![א-ת])פייזרס(?![א-ת])", "פייזרים", "מינוח קאנוני (Phasers)"),
        ],
        "characters": [
            {"name": "Spock", "he_name": "ספוק", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Captain Kirk", "he_name": "קפטן קירק", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Jean-Luc Picard", "he_name": "ז'אן-לוק פיקארד", "gender": "Male", "pronouns": "אתה/הוא"},
        ]
    },
    "lord of the rings": {
        "title_patterns": [r"\blord\s*of\s*the\s*rings\b", r"\brings\s*of\s*power\b", r"\bthe\s*hobbit\b", r"\btolkien\b"],
        "domains": ["fantasy"],
        "canon_terms": [
            (r"(?<![א-ת])טבעת\s*אחת(?![א-ת])", "הטבעת האחת", "מינוח קאנוני (The One Ring)"),
            (r"(?<![א-ת])ארץ\s*תיכונה(?![א-ת])", "הארץ התיכונה", "מינוח קאנוני (Middle-earth)"),
            (r"(?<![א-ת])בני\s*לילית(?![א-ת])", "עלפים", "מינוח קאנוני מודרני (Elves)"),
        ],
        "characters": [
            {"name": "Frodo", "he_name": "פרודו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Gandalf", "he_name": "גנדלף", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Galadriel", "he_name": "גלדריאל", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Arwen", "he_name": "ארוון", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Eowyn", "he_name": "איאווין", "gender": "Female", "pronouns": "את/היא"},
        ]
    },
    "marvel": {
        "title_patterns": [r"\bmarvel\b", r"\bavengers\b", r"\biron\s*man\b", r"\bcaptain\s*america\b", r"\bthor\b", r"\bguardians\s*of\s*the\s*galaxy\b"],
        "domains": ["sci_fi", "action"],
        "canon_terms": [
            (r"(?<![א-ת])אבני\s*אינסוף(?![א-ת])", "אבני האינסוף", "מינוח קאנוני (Infinity Stones)"),
            (r"(?<![א-ת])סוכני\s*שילד(?![א-ת])", "סוכני ש.י.ל.ד.", "מינוח קאנוני (S.H.I.E.L.D.)"),
        ],
        "characters": [
            {"name": "Natasha Romanoff", "he_name": "נטשה רומנוף", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Wanda Maximoff", "he_name": "וונדה מקסימוף", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Carol Danvers", "he_name": "קרול דנברס", "gender": "Female", "pronouns": "את/היא"},
        ]
    },
    "boston legal": {
        "title_patterns": [r"\bboston\s*legal\b", r"\bcrane\s*poole\b"],
        "domains": ["legal"],
        "canon_terms": [
            (r"(?<![א-ת])מהשור\s+הזה(?![א-ת])", "מהבחור הזה שור", "תיקון תרגום מילולי שגוי של שם המשפחה Shore ('מהבחור הזה שור')"),
            (r"(?<![א-ת])השור\s+הזה,\s+סאלי", "הבחור הזה שור, סאלי", "תיקון תרגום מילולי שגוי של שם המשפחה Shore"),
            (r"(?<![א-ת])קלוד\s+דבראו(?![א-ת])", "קלוד דברו", "אחידות תעתיק צרפתי (Devereaux = דברו)"),
            (r"(?<![א-ת])ראלף\s+דבראו(?![א-ת])", "ראלף דברו", "אחידות תעתיק צרפתי (Devereaux = דברו)"),
        ],
        "characters": [
            {"name": "Alan Shore", "he_name": "אלן שור", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Denny Crane", "he_name": "דני קריין", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Shirley Schmidt", "he_name": "שירלי שמידט", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Lori Colson", "he_name": "לורי קולסון", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Sally Heep", "he_name": "סאלי היפ", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Tara Wilson", "he_name": "טארה וילסון", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Brad Chase", "he_name": "בראד צ'ייס", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Paul Lewiston", "he_name": "פול לויסטון", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Edwin Poole", "he_name": "אדווין פול", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Denise Bauer", "he_name": "דניס באוור", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Jerry Espenson", "he_name": "ג'רי אספנסון", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Jeffrey Coho", "he_name": "ג'פרי קוהו", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Claire Simms", "he_name": "קלייר סימס", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Katie Lloyd", "he_name": "קייטי לויד", "gender": "Female", "pronouns": "את/היא"},
            {"name": "Carl Sack", "he_name": "קארל סאק", "gender": "Male", "pronouns": "אתה/הוא"},
            {"name": "Whitney Rome", "he_name": "וויטני רום", "gender": "Female", "pronouns": "את/היא"},
        ]
    }
}

# ==============================================================================
# 2. MODULAR DOMAIN DEFINITIONS
# ==============================================================================

DOMAIN_PACKS = {
    "sci_fi": {
        "genre_names": ["science fiction", "sci-fi"],
        "keywords": [
            "spaceship", "starship", "lightsaber", "hyperdrive", "warp", "droid",
            "galaxy", "orbit", "mothership", "cloaking", "phaser", "blaster",
            "hyperspace", "tractor beam", "force field", "alien", "cyborg"
        ],
        "prompt_guidelines": (
            "SCIENCE FICTION TERMINOLOGY:\n"
            "- 'snub fighter' / 'starfighter' -> 'חללית קרב' או 'קרבית' (NEVER 'מכלית קרב').\n"
            "- 'tractor beam' -> 'קרן גרירה' (NEVER 'קרן משיכה').\n"
            "- 'motivator' -> 'יחידת מניע' / 'מניע' (NEVER 'מנוע').\n"
            "- 'shields down / failed' -> 'המגנים קרסו' / 'המגנים אינם פועלים'.\n"
            "- 'droid' / 'android' -> 'דרואיד' / 'אנדרואיד' (רובוט מתקדם)."
        ),
        "bilingual_rules": [
            (r"\b(?:snub\s*)?fighters?\b", r"\b(ו|ה|ב|ל|כ|מ|ש)?מכלית\s*קרב\b", r"\g<1>חללית קרב", "מינוח מד״ב (snub fighter = חללית קרב)"),
            (r"\b(?:snub\s*)?fighters?\b", r"\b(ו|ה|ב|ל|כ|מ|ש)?מכליות\s*קרב\b", r"\g<1>חלליות קרב", "מינוח מד״ב (snub fighters = חלליות קרב)"),
            (r"\btractor\s*beams?\b", r"\b(ו|ה|ב|ל|כ|מ|ש)?קרן\s*משיכה\b", r"\g<1>קרן גרירה", "מינוח מד״ב קאנוני (tractor beam = קרן גרירה)"),
            (r"\btractor\s*beams?\b", r"\b(ו|ה|ב|ל|כ|מ|ש)?קרני\s*משיכה\b", r"\g<1>קרני גרירה", "מינוח מד״ב קאנוני (tractor beams = קרני גרירה)"),
            (r"\bbad\s*motivator\b", r"\b(מנוע\s*הרוס|מניע\s*הרוס)\b", "מניע תקול", "מינוח מד״ב (bad motivator = מניע תקול)"),
        ]
    },
    "military": {
        "genre_names": ["war", "military"],
        "keywords": [
            "battalion", "platoon", "squadron", "airstrike", "recon", "artillery",
            "commanding officer", "lieutenant", "sergeant", "colonel", "admiral",
            "tanker", "convoy", "checkpoint", "sniper", "ambush", "firefight"
        ],
        "prompt_guidelines": (
            "MILITARY & AVIATION CONVENTIONS:\n"
            "- 'captain' -> 'קפטן', 'קברניט' (בחייל הים/אוויר) או 'סרן' (ביבשה). NEVER Arabic-influenced transliterations like 'קאבתן'.\n"
            "- 'tanker' -> 'מטוס תדלוק' / 'מכלית דלק' (NEVER 'חללית').\n"
            "- 'copy that' / 'roger' -> 'רות' / 'הבנתי' / 'קיבלתי'.\n"
            "- 'recon' -> 'סיור' / 'מודיעין'."
        ),
        "bilingual_rules": [
            (r"\bcaptains?\b", r"\b(ו|ה|ב|ל|כ|מ|ש)?קאבתן\b", r"\g<1>קברניט", "תיקון תעתיק פונטי שגוי (Captain = קברניט/קפטן ולא קאבתן)"),
        ]
    },
    "legal": {
        "genre_names": ["crime", "legal", "courtroom"],
        "keywords": [
            "objection", "your honor", "sustained", "overruled", "plaintiff", "defendant",
            "courtroom", "bailiff", "cross-examination", "prosecution", "testimony",
            "perjury", "subpoena", "affidavit", "verdict", "hung jury", "probation"
        ],
        "prompt_guidelines": (
            "LEGAL & COURTROOM CONVENTIONS:\n"
            "- 'objection' -> 'התנגדות'.\n"
            "- 'sustained' -> 'מתקבלת'.\n"
            "- 'overruled' -> 'נדחית'.\n"
            "- 'counsel' -> 'פרקליט' / 'אדוני הפרקליט' / 'בא-כוח' / 'עו״ד'.\n"
            "- 'second chair' -> 'פרקליט משנה' / 'פרקליטת משנה' (NEVER literal 'כיסא שני').\n"
            "- 'open minds (in that jury box)' -> 'אנשים עם ראש פתוח' (NEVER literal 'מוחות פתוחים').\n"
            "- 'Thank you, Officer' -> 'תודה לך, אדוני השוטר' (NEVER bare 'תודה לך, השוטר').\n"
            "- 'elicit derogatory, inculpatory information (from a witness on cross-examination)' -> 'להוציא מידע מביך שיערער את אמינותו'.\n"
            "- 'motion' -> 'בקשה' (למשל 'motion to dismiss' -> 'בקשה למחיקת התביעה').\n"
            "- 'Your Honor' -> 'כבוד השופט' / 'כבוד השופטת' / 'כבודו'."
        ),
        "bilingual_rules": [
            (r"\bobjection\b", r"\b(ו|ה|ב|ל|כ|מ|ש)?מחאה\b", r"\g<1>התנגדות", "מינוח משפטי (Objection = התנגדות)"),
            (r"\bsustained\b", r"\bנתמך\b", "מתקבלת", "מינוח משפטי (Sustained = מתקבלת)"),
            (r"\boverruled\b", r"\bבוטל\b", "נדחית", "מינוח משפטי (Overruled = נדחית)"),
            (r"\bsecond\s+chair\b", r"אם את צריכה כיסא שני", "אם את צריכה פרקליטת משנה", "מינוח משפטי (Second Chair = פרקליטת משנה)"),
            (r"\bsecond\s+chair\b", r"כיסא שני", "פרקליט משנה", "מינוח משפטי (Second Chair = פרקליט משנה ולא כיסא שני)"),
            (r"\b12\s+open\s+minds\b", r"12\s+מוחות\s+פתוחים", "12 אנשים עם ראש פתוח", "ניסוח עברי טבעי (open minds = אנשים עם ראש פתוח)"),
            (r"\bthank\s+you,\s+officer\b", r"תודה לך,\s+השוטר", "תודה לך, אדוני השוטר", "פנייה תקנית בעברית (Thank you, Officer = תודה לך, אדוני השוטר)"),
            (r"\btwo\s+questions\.\s*that\s+was\s+your\s+summation\b", r"זה היה הסיכום שלך", "זו הייתה החקירה הנגדית שלך", "דיוק הקשר משפטי (שתי שאלות לעד = חקירה נגדית)"),
        ]
    },
    "medical": {
        "genre_names": ["medical", "hospital"],
        "keywords": [
            "defibrillator", "scalpel", "intubate", "patient", "cardiac", "diagnosis",
            "resuscitate", "trauma", "operating room", "triage", "biopsy", "crash cart",
            "code blue", "stethoscope", "symptoms", "aneurysm", "icu"
        ],
        "prompt_guidelines": (
            "MEDICAL & HOSPITAL CONVENTIONS:\n"
            "- 'scrubs' -> 'מדי חדר ניתוח' / 'מדים'.\n"
            "- 'code blue' -> 'החייאה' / 'קוד כחול'.\n"
            "- 'triage' -> 'מיון נפגעים' / 'טריאז''.\n"
            "- 'intubate' -> 'לבצע אינטובציה' / 'להחדיר צינור'."
        ),
        "bilingual_rules": [
            (r"\bcode\s*blue\b", r"\bקוד\s*כחול\b", "החייאה", "מינוח רפואי (Code Blue = החייאה)"),
        ]
    },
    "fantasy": {
        "genre_names": ["fantasy"],
        "keywords": [
            "wizard", "elf", "elves", "dwarf", "dwarves", "sorcerer", "spell",
            "dragon", "kingdom", "realm", "orc", "magic", "sword", "enchantment"
        ],
        "prompt_guidelines": (
            "FANTASY & MYTHOLOGY CONVENTIONS:\n"
            "- 'elves' -> 'עלפים' (בתרגום מודרני) או 'בני לילית'.\n"
            "- Maintain elevated, ceremonial, or archaic register where appropriate for nobles and sorcerers."
        ),
        "bilingual_rules": []
    }
}

# ==============================================================================
# 3. UNIVERSAL MACHINE-TRANSLATION IDIOM RULES (CROSS-GENRE)
# ==============================================================================

UNIVERSAL_IDIOM_GUIDELINES = (
    "COMMON MACHINE-TRANSLATION BLUNDERS & NATURAL IDIOMS:\n"
    "- 'As a matter of fact' -> 'למעשה' / 'למען האמת' (NEVER 'מעשה בראשית' or 'כעניין של עובדה').\n"
    "- 'Make yourself at home' -> 'תרגיש בבית' (NEVER 'עשה את עצמך בבית').\n"
    "- 'For what it's worth' -> 'אם זה משנה משהו' / 'אם זה שווה משהו' (NEVER 'בשביל מה שזה שווה').\n"
    "- 'Take your time' -> 'קח את הזמן' / 'בלי לחץ' (NEVER 'קח את זמנך').\n"
    "- 'Out of the blue' -> 'משום מקום' / 'פתאום' (NEVER 'מחוץ לכחול').\n"
    "- 'Give me a break' -> 'נו באמת' / 'עזוב אותי' (NEVER 'תן לי הפסקה').\n"
    "- 'Cut some slack' -> 'תוותר לו' / 'תקל עליו' (NEVER 'חתוך רפוי').\n"
    "- 'By all means' -> 'בהחלט' / 'בוודאי' (NEVER 'בכל האמצעים').\n"
    "- 'Sleep on it' -> 'לחשוב על זה הלילה' / 'לישון על זה' (NEVER 'לישון עליו').\n"
    "- 'Rule of thumb' -> 'כלל אצבע'.\n"
    "- Common verbs: use proper Hebrew verb forms e.g. 'לשים' (never 'לשום'), 'מושכת' (never 'מוחב')."
)

# Cross-lingual anchor rules: Checked ONLY when English master is available!
# If English master contains en_pattern AND Hebrew cue contains he_pattern, replacement is 100% safe.
UNIVERSAL_BILINGUAL_RULES: List[Tuple[str, str, str, str]] = [
    (
        r"\bas a matter of fact\b",
        r"\b(ו|ה|ב|ל|כ|מ|ש)?מעשה\s*בראשית\b",
        r"\g<1>למעשה",
        "תיקון תרגום מכונה מילולי של As a matter of fact"
    ),
    (
        r"\bmake (?:your|one)selves? at home\b",
        r"\bעשה (?:את )?עצמך בבית\b",
        "תרגיש בבית",
        "תיקון תרגום מכונה מילולי של Make yourself at home"
    ),
    (
        r"\bfor what it'?s worth\b",
        r"\bבשביל מה שזה שווה\b",
        "אם זה משנה משהו",
        "תיקון תרגום מכונה מילולי של For what it's worth"
    ),
    (
        r"\bout of the blue\b",
        r"\bמחוץ לכחול\b",
        "משום מקום",
        "תיקון תרגום מכונה מילולי של Out of the blue"
    ),
    (
        r"\bgive me a break\b",
        r"\bתן לי הפסקה\b",
        "נו באמת",
        "תיקון תרגום מכונה מילולי של Give me a break"
    ),
    (
        r"\bcaptain\b",
        r"\b(ו|ה|ב|ל|כ|מ|ש)?קאבתן\b",
        r"\g<1>קברניט",
        "תיקון תעתיק פונטי שגוי (Captain = קברניט/קפטן ולא קאבתן)"
    ),
    (
        r"\bthat\s+shore\s+guy\b",
        r"(?<![א-ת])מהשור\s+הזה(?![א-ת])",
        "מהבחור הזה שור",
        "תיקון תרגום מילולי שגוי של שם המשפחה Shore ('מהבחור הזה שור')"
    ),
]

# ==============================================================================
# 4. DOMAIN PROFILE & CONTEXT RESOLVER
# ==============================================================================

class DomainProfile:
    """Encapsulates resolved domains, franchise lore, and targeted correction rules."""
    def __init__(self, primary_domain: str, active_domains: Set[str], franchise: Optional[str] = None):
        self.primary_domain = primary_domain
        self.active_domains = set(active_domains)
        self.franchise = franchise

    def get_prompt_guidelines(self) -> str:
        """Returns consolidated markdown guidelines for LLM prompts."""
        sections = []
        # 1. Franchise Guidelines
        if self.franchise and self.franchise in FRANCHISE_PACKS:
            f_data = FRANCHISE_PACKS[self.franchise]
            canon_lines = []
            for pat, rep, reas in f_data.get("canon_terms", []):
                clean_term = pat.replace(r"\b", "").replace(r"\s*", " ").replace(r"(?<![א-ת])", "").replace(r"(?![א-ת])", "")
                clean_term = re.sub(r'[\(\)\?\\|]+', '', clean_term).strip()
                canon_lines.append(f"- '{clean_term}' MUST BE TRANSLATED AS '{rep}' ({reas})")
            if canon_lines:
                sections.append(f"FRANCHISE CANON GUIDELINES ({self.franchise.upper()}):\n" + "\n".join(canon_lines))

        # 2. Domain Pack Guidelines
        for dom in sorted(self.active_domains):
            if dom in DOMAIN_PACKS and DOMAIN_PACKS[dom].get("prompt_guidelines"):
                sections.append(DOMAIN_PACKS[dom]["prompt_guidelines"])

        # 3. Universal Idioms Guidelines
        sections.append(UNIVERSAL_IDIOM_GUIDELINES)
        return "\n\n".join(sections)

    def get_bilingual_rules(self) -> List[Tuple[str, str, str, str]]:
        """Returns all deterministic bilingual rules matching active domains and universal rules."""
        rules = list(UNIVERSAL_BILINGUAL_RULES)
        for dom in self.active_domains:
            if dom in DOMAIN_PACKS:
                rules.extend(DOMAIN_PACKS[dom].get("bilingual_rules", []))
        return rules

    def get_canon_terms(self) -> List[Tuple[str, str, str]]:
        """Returns franchise canon terms for deterministic offline regex pass."""
        if self.franchise and self.franchise in FRANCHISE_PACKS:
            return FRANCHISE_PACKS[self.franchise].get("canon_terms", [])
        return []

    def get_characters(self) -> List[Dict]:
        """Returns franchise characters if available."""
        if self.franchise and self.franchise in FRANCHISE_PACKS:
            return FRANCHISE_PACKS[self.franchise].get("characters", [])
        return []

def classify_media_domain(
    title: Optional[str] = None,
    overview: Optional[str] = None,
    genres: Optional[List[str]] = None,
    sample_cues: Optional[List[Dict]] = None
) -> DomainProfile:
    """
    Classifies media into domain profile using multi-tier hierarchy:
    Tier 1: Explicit TMDb/Bible genres and overview.
    Tier 2: Title & franchise pattern matching.
    Tier 3: Offline lexical vocabulary scanning across subtitle cues.
    """
    clean_title = (title or "").lower().strip()
    clean_overview = (overview or "").lower().strip()
    norm_genres = [g.lower().strip() for g in (genres or []) if isinstance(g, str)]

    detected_franchise = None
    active_domains: Set[str] = set()

    # 1. Franchise Identification
    combined_search_text = f"{clean_title} {clean_overview}"
    for f_name, f_data in FRANCHISE_PACKS.items():
        matched = False
        for pat in f_data.get("title_patterns", []):
            if re.search(pat, combined_search_text, flags=re.IGNORECASE):
                matched = True
                break
        if matched:
            detected_franchise = f_name
            active_domains.update(f_data.get("domains", []))
            break

    # 2. Genre Mapping (from TMDb or Translation Bible)
    for dom_key, dom_data in DOMAIN_PACKS.items():
        target_genres = dom_data.get("genre_names", [])
        for g in norm_genres:
            if any(tg in g for tg in target_genres):
                active_domains.add(dom_key)

    # 3. Overview Keyword Scan
    if clean_overview:
        for dom_key, dom_data in DOMAIN_PACKS.items():
            kw_hits = sum(1 for kw in dom_data.get("keywords", []) if kw in clean_overview)
            if kw_hits >= 2:
                active_domains.add(dom_key)

    # 4. Offline Fallback: Lexical Cue Vocabulary Fingerprinting
    # Runs when no genres or franchise were resolved from external metadata
    if not active_domains and sample_cues:
        domain_cue_scores = {k: 0 for k in DOMAIN_PACKS.keys()}
        # Sample first 60 cues
        for c in sample_cues[:60]:
            text = (c.get("text") or c.get("en") or "").lower()
            if not text:
                continue
            for dom_key, dom_data in DOMAIN_PACKS.items():
                for kw in dom_data.get("keywords", []):
                    if re.search(rf"\b{re.escape(kw)}\b", text):
                        domain_cue_scores[dom_key] += 1

        for dom_key, score in domain_cue_scores.items():
            if score >= 3:
                active_domains.add(dom_key)

    primary_domain = "general"
    if "sci_fi" in active_domains:
        primary_domain = "sci_fi"
    elif "military" in active_domains:
        primary_domain = "military"
    elif "legal" in active_domains:
        primary_domain = "legal"
    elif "medical" in active_domains:
        primary_domain = "medical"
    elif "fantasy" in active_domains:
        primary_domain = "fantasy"
    elif active_domains:
        primary_domain = list(active_domains)[0]

    return DomainProfile(
        primary_domain=primary_domain,
        active_domains=active_domains,
        franchise=detected_franchise
    )
