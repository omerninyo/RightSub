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
import unicodedata
import argparse
import shutil
import threading
from collections import Counter
from pathlib import Path

RLM = "\u200F"

# Common advertising, website promotions, and translator credit patterns
AD_PATTERNS = [
    r'\bopensubtitles\b',
    r'\btorec(?:\.net)?\b',
    r'\bwizdom(?:\.xyz)?\b',
    r'\bsratim\.co\.il\b',
    r'\bsubcenter\b',
    r'\bktuvit\b',
    r'סונכרן\s+(?:על\s+ידי|ע["״\']?י)',
    r'תורגם\s+(?:על\s+ידי|ע["״\']?י)',
    r'^[‏\u200F\s\-–—]*(?:מלאכת\s+)?ה?תרגום\s*:\s*\S+',
    r'^[‏\u200F\s\-–—]*(?:מלאכת\s+)?ה?סנכרון\s*:\s*\S+',
    r'הורד\s+מ[-–—]\s*(?!\d)(?:אתר|[A-Za-z0-9\-]+\.[A-Za-z]{2,}|טורק|כתובית|סאבסנטר|וויזדום)',
    r'^[\u200e\u200f\s\-–—]*(?:הועלה|סונכרן\s+ו?הועלה)\s+על\s+ידי',
    r'הצטרפו\s+ל.*טלגרם',
    r't\.me\/',
    r'telegram\.me',
    r'rip\s+by\b',
    r'sync\s+by\b',
]
AD_REGEX = re.compile('|'.join(AD_PATTERNS), re.IGNORECASE)

def read_file_with_auto_encoding(file_path):
    """
    Reads a subtitle file, automatically detecting if it's UTF-16, UTF-8, UTF-8-SIG,
    or legacy Windows-1255 / CP1255 / ISO-8859-8 vs Western European Windows-1252.
    Returns (content_str, detected_encoding).
    """
    raw_bytes = Path(file_path).read_bytes()
    if not raw_bytes:
        return "", "utf-8"

    # 1. Check UTF-16 BOM (LE / BE)
    if raw_bytes.startswith(b'\xff\xfe') or raw_bytes.startswith(b'\xfe\xff'):
        try:
            return raw_bytes.decode('utf-16'), 'utf-16'
        except Exception:
            pass

    # 2. Try UTF-8 / UTF-8-SIG strictly
    try:
        text = raw_bytes.decode('utf-8-sig')
        return text, 'utf-8'
    except UnicodeDecodeError:
        pass

    # 3. Distinguish Windows-1255 (Hebrew ANSI) from Windows-1252 (Western European ANSI)
    # Hebrew characters in CP1255 reside in 0xE0..0xFA and form consecutive multi-byte words,
    # whereas French/Spanish/German accented letters in CP1252 are isolated inside ASCII words.
    cp1255_hebrew_bytes = sum(1 for b in raw_bytes if 0xE0 <= b <= 0xFA)
    consecutive_hebrew_words = len(re.findall(rb'[\xE0-\xFA]{2,}', raw_bytes))
    ascii_alpha_bytes = sum(1 for b in raw_bytes if (0x41 <= b <= 0x5A) or (0x61 <= b <= 0x7A))

    if cp1255_hebrew_bytes >= 4 and (
        consecutive_hebrew_words >= 2
        or (consecutive_hebrew_words >= 1 and cp1255_hebrew_bytes > ascii_alpha_bytes * 0.5)
    ):
        for heb_enc in ('cp1255', 'iso-8859-8'):
            try:
                text = raw_bytes.decode(heb_enc)
                return text, 'windows-1255' if heb_enc == 'cp1255' else heb_enc
            except Exception:
                continue

    # 4. Non-Hebrew legacy fallbacks (Windows-1252 / Latin-1 first so European files aren't mapped to Hebrew)
    for enc in ['cp1252', 'latin1', 'utf-8']:
        try:
            return raw_bytes.decode(enc, errors='replace'), enc
        except Exception:
            continue

    return raw_bytes.decode('utf-8', errors='replace'), 'utf-8-fallback'

# Comprehensive Arabic to Hebrew homoglyph & vocabulary conversion
ARABIC_TO_HEBREW = {
    '\u0645': 'מ',  # Meem
    '\u064A': 'י',  # Yeh
    '\u0648': 'ו',  # Waw
    '\u0647': 'ה',  # Heh
    '\u0646': 'נ',  # Noon
    '\u0631': 'ר',  # Reh
    '\u062F': 'ד',  # Dal
    '\u0633': 'ס',  # Seen
    '\u0643': 'כ',  # Kaf
    '\u0628': 'ב',  # Beh
    '\u062A': 'ת',  # Teh
    '\u0644': 'ל',  # Lam
    '\u0642': 'ק',  # Qaf
    '\u0635': 'צ',  # Sad
    '\u0637': 'ט',  # Tah
    '\u0639': 'ע',  # Ain
    '\u062D': 'ח',  # Hah
    '\u062E': 'ח',  # Khah
    '\u062C': 'ג',  # Jeem
    '\u0632': 'ז',  # Zain
    '\u0641': 'פ',  # Feh
    '\u0634': 'ש',  # Sheen
    '\u0627': 'א',  # Alef
    '\u0623': 'א',  # Alef with Hamza Above
    '\u0621': 'א',  # Hamza
    '\u0626': 'י',  # Yeh with Hamza
    '\u0624': 'ו',  # Waw with Hamza
    '\u0625': 'א',  # Alef with Hamza Below
    '\u0622': 'א',  # Alef with Madda
    '\u0629': 'ה',  # Teh Marbuta
    '\u0649': 'י',  # Alef Maksura
    '\u0630': 'ד',  # Thal
    '\u0636': 'צ',  # Dad
    '\u0638': 'ט',  # Zah
    '\u063A': 'ג',  # Ghain
    '\u064A': 'י',  # Standard Arabic Yaa
    '\u0648': 'ו',  # Standard Arabic Waw
}

ARABIC_PHRASES = [
    (r'(?<![א-ת\u0600-\u06FF])כל\s*ما(?![א-ת\u0600-\u06FF])', 'כל מה'),
    (r'(?<![א-ת\u0600-\u06FF])ما(?![א-ת\u0600-\u06FF])', 'מה'),
    (r'(?<![א-ת\u0600-\u06FF])كل\s+ما(?![א-ת\u0600-\u06FF])', 'כל מה'),
    (r'(?<![א-ת\u0600-\u06FF])تكون(?![א-ת\u0600-\u06FF])', 'תהיה'),
    (r'(?<![א-ת\u0600-\u06FF])يكون(?![א-ת\u0600-\u06FF])', 'יהיה'),
    (r'(?<![א-ת\u0600-\u06FF])اكون(?![א-ת\u0600-\u06FF])', 'אהיה'),
    (r'(?<![א-ת\u0600-\u06FF])أكون(?![א-ת\u0600-\u06FF])', 'אהיה'),
    (r'(?<![א-ת\u0600-\u06FF])بالכאד(?![א-ת\u0600-\u06FF])', 'בקושי'),
    (r'(?<![א-ת\u0600-\u06FF])بالكاد(?![א-ת\u0600-\u06FF])', 'בקושי'),
    (r'(?<![א-ת\u0600-\u06FF])هي(?![א-ת\u0600-\u06FF])', 'היא'),
    (r'(?<![א-ת\u0600-\u06FF])هو(?![א-ת\u0600-\u06FF])', 'הוא'),
]

CYRILLIC_TO_HEBREW = {
    'м': 'מ', 'М': 'מ', 'а': 'א', 'А': 'א',
    'р': 'ר', 'Р': 'ר', 'с': 'ס', 'С': 'ס',
    'т': 'ת', 'Т': 'ת', 'х': 'ח', 'Х': 'ח',
    'о': 'ס', 'О': 'ס', 'е': 'ה', 'Е': 'ה',
    'в': 'ב', 'В': 'ב', 'н': 'נ', 'Н': 'נ',
    'и': 'י', 'И': 'י', 'к': 'כ', 'К': 'כ',
    'у': 'ו', 'У': 'ו',
}

UNIVERSAL_HOMOGLYPH_MAP = {
    # Georgian to Hebrew
    '\u10D7': 'ת',  # თ -> ת (e.g. התזת)
    '\u10D0': 'א',  # ა -> א (e.g. קרויצפלד-יאקוב)
    '\u10D9': 'ק',  # კ -> ק
    '\u10D4': 'ה',  # ე -> ה
    '\u10DA': 'ל',  # ლ -> ל

    # Armenian to Hebrew
    '\u0578': 'ו',  # ո -> ו (e.g. מבוסטון)
    '\u056B': 'י',  # ի -> י (e.g. מתקדימים)
    '\u0574': 'מ',  # մ -> מ

    # Greek homoglyphs to Hebrew
    '\u03C2': 'ס',  # ς -> ס
    '\u03C4': 'ט',  # τ -> ט
    '\u03BF': 'ו',  # ο -> ו
    '\u03BD': 'ן',  # ν -> ן
    '\u03B5': 'ה',  # ε -> ה

    # Tibetan to Hebrew
    '\u0F62': 'ר',  # ར་ -> ר
    '\u0F0B': '',   # ་ -> removal

    # Thai to Hebrew
    '\u0E01': 'ק',  # ก -> ק
    '\u0E34': '',   # ิ -> removal

    # Katakana / Japanese to Hebrew
    '\u30E1': 'מ',  # メ -> מ
    '\u30EA': 'ר',  # リ -> ר
    '\u30AB': 'ק',  # カ -> ק
}

UNIVERSAL_PHRASES = [
    (r'השופט[ο\u03BF][ς\u03C2]', 'השופט'),
    (r'האחרו[נן\u03BD][ה\u03B5][ס\u03C2]', 'האחרונות'),
    (r'מב[ո\u0578]ס[τ\u03C4][ο\u03BF][ν\u03BD]', 'מבוסטון'),
    (r'בא[メ\u30E1][ר\u30EA][ק\u30AB]ה?', 'באמריקה'),
    (r'לא\s*מ[ե\u10D4][ל\u10DA]רוז', 'לא מלרוז'),
    (r'מר\s*מ[কেবাబ\u0995\u09C7\u09AC\u09BE\u0C2C\u0C3E]+', 'מר מקבה'),
    (r'פ[ר\u0F62\u0F0B]+סה', 'פארסה'),
    (r'ג([׳\'])ק\s*בוסט[יק\u0E01\u0E34]+', r'ג\1ק בוסטיק'),
    (r'מתקד[ימ\u056B\u0574]+ם', 'מתקדמים'),
    (r'קרויצפלד[- ]י[א\u10D0][ק\u10D9]וב', 'קרויצפלד-יאקוב'),
    (r'ה[ת\u10D7]זת', 'התזת'),
    (r'(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?ד[\u10D4]ייט(?![א-ת])', r'\g<1>דייט'),
    (r'[\u585A]', ''),
    (r'\\"', '"'),
    (r'(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?קאבתן(?![א-ת])', r'\g<1>קברניט'),
    (r'(?<![א-ת])לשום\s+את(?![א-ת])', 'לשים את'),
    (r'(?<![א-ת])מוחב\s+אותנו(?![א-ת])', 'מושכת אותנו'),
    (r'(?<![א-ת])(ו)?ירתי(?=\s+(?:בו|בה|בהם|בהן|לעבר|באוויר|כדור))', r'\g<1>יריתי'),
    (r'(?<![א-ת])(ש)?הודאת(?=\s+(?:תחת|בכך|בפני|כי|על))', r'\g<1>הודית'),
]

def cross_check_bilingual_numbers(he_text, en_text):
    """
    Deterministic 0-token bilingual number un-flipper:
    When a companion English cue is available, checks if any multi-digit number in `he_text`
    (e.g. '84' from a legacy Subabi visual reversal) is the exact digit-reversal of a number
    present in `en_text` ('48') while respecting occurrence multiplicities and skipping HTML tags/entities.
    """
    if not he_text or not en_text:
        return he_text
    en_counts = Counter(re.findall(r'\b\d{2,}\b', en_text))
    if not en_counts:
        return he_text

    he_visible = re.sub(r'<[^>]+>|&#\d+;|&[A-Za-z0-9#]+;', ' ', he_text)
    he_counts = Counter(re.findall(r'(?<!\d)\d{2,}(?!\d)', he_visible))

    def _replace_num(match):
        if match.group(1):
            return match.group(1)
        num_str = match.group(2)
        rev_str = num_str[::-1]
        if num_str == rev_str:
            return num_str
        if en_counts.get(rev_str, 0) > he_counts.get(rev_str, 0) and he_counts.get(num_str, 0) > en_counts.get(num_str, 0):
            he_counts[num_str] -= 1
            he_counts[rev_str] += 1
            return rev_str
        return num_str

    return re.sub(r'(<[^>]+>|&#\d+;)|(?<!\d)(\d{2,})(?!\d)', _replace_num, he_text)

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

def normalize_final_letters(text):
    # Punctuation or whitespace indicating end of word, excluding hyphen attached to numbers/words (prefixes like מ-100, כ-50)
    # and excluding quotes/gershayim inside acronyms or loanwords (e.g. בימ"ש, מנכ"ל, צ'יפס).
    # Require a preceding Hebrew letter (?<=[א-ת]) so single-letter labels (e.g. "סעיף כ.") are not altered,
    # exclude repeated hesitation letters (אממ, הממ, מממ, ממ, ננ), and exclude 'פ' -> 'ף' to preserve loanwords ending in /p/.
    punct = r'(?:[\u200F\s\.\?!,:;\–\—\)\]»…]|["\'״׳”’](?![א-ת])|$)'
    text = re.sub(r'(?<=[א-ת])(?<![כך])כ(?=' + punct + r')', 'ך', text)
    text = re.sub(r'(?<=[א-ת])(?<![מם])מ(?=' + punct + r')', 'ם', text)
    text = re.sub(r'(?<=[א-ת])(?<![נן])נ(?=' + punct + r')', 'ן', text)
    text = re.sub(r'(?<=[א-ת])(?<![צץ])צ(?=' + punct + r')', 'ץ', text)

    # Explicitly repair prefixes mistakenly normalized before hyphens (e.g. ם-100 -> מ-100, ך-50 -> כ-50)
    text = re.sub(r'(?<![א-תa-zA-Z0-9])ם-(?=\d|[א-תa-zA-Z])', 'מ-', text)
    text = re.sub(r'(?<![א-תa-zA-Z0-9])ך-(?=\d|[א-תa-zA-Z])', 'כ-', text)
    text = re.sub(r'(?<![א-תa-zA-Z0-9])ן-(?=\d|[א-תa-zA-Z])', 'נ-', text)
    text = re.sub(r'(?<![א-תa-zA-Z0-9])ף-(?=\d|[א-תa-zA-Z])', 'פ-', text)
    text = re.sub(r'(?<![א-תa-zA-Z0-9])ץ-(?=\d|[א-תa-zA-Z])', 'צ-', text)
    return text

CORRUPTED_FINAL_LETTER_REPAIRS = [
    (r'(?<![א-ת])אמם(?![א-ת])', 'אממ'),
    (r'(?<![א-ת])המם(?![א-ת])', 'הממ'),
    (r'(?<![א-ת])ממם(?![א-ת])', 'מממ'),
    (r'(?<![א-ת])(ו|ה|ב|ל|כ|מ|ש)?טרמף(?![א-ת])', r'\g<1>טרמפ'),
]

def clean_and_sanitize_text(text):
    """
    Cleans transcript truncation tags, stray JSON syntax, unescapes literal \\n,
    and normalizes foreign homoglyphs (Arabic, Cyrillic, Georgian, Armenian, Greek, Asian) into pure Hebrew
    while preserving valid leading SSA override tags such as {\\an8} and legitimate SDH brackets [...].
    """
    if not text:
        return ""

    # Preserve leading SSA tags (e.g. {\an8}, {\pos(x,y)}) before stripping stray JSON braces
    ssa_lead = ""
    ssa_match = re.match(r'^\s*((?:\{\\[^}]+\}\s*)+)(.*)$', text, flags=re.DOTALL)
    if ssa_match:
        ssa_lead = re.sub(r'\s+', '', ssa_match.group(1))
        text = ssa_match.group(2)

    # 1. Clean transcript truncation tags and leaked tool artifacts
    text = re.sub(r'<truncated\s+\d+\s+bytes>', '', text)

    # 2. Clean leaked JSON key/value syntax if dialogue got contaminated (avoid false matches like "[context: ...]")
    has_json_leak = bool(re.search(r'(?:["\'](?:hebrew|index|text)["\']|(?<![A-Za-z])(?:hebrew|index))\s*:', text))
    if has_json_leak:
        text = re.sub(r'(?:["\'](?:hebrew|text)["\']|(?<![A-Za-z])hebrew)\s*:\s*["\']?', '', text)
        text = re.sub(r'(?:["\']index["\']|(?<![A-Za-z])index)\s*:\s*\d+,?', '', text)
        text = re.sub(r'^\s*[\{\}\[\]]+\s*', '', text)
        text = re.sub(r'\s*[\{\}\[\]]+\s*$', '', text)
    else:
        text = re.sub(r'^\s*[\{\}]+\s*', '', text)
        text = re.sub(r'\s*[\{\}]+\s*$', '', text)

    # 3. Unescape literal backslash-n sequences unconditionally
    text = text.replace(r'\n', '\n')
    text = text.replace(r'\r', '')
    text = text.replace(r'\"', '"')

    # Decompose Hebrew and Arabic presentation forms into canonical letters before homoglyph/final-letter pass
    text = re.sub(r'[\uFB1D-\uFDFF\uFE70-\uFEFF]+', lambda m: unicodedata.normalize('NFKD', m.group(0)), text)

    # Preserve vocalized 'אִמם' ("their mother") and strip Hebrew Nikud + Arabic diacritics BEFORE homoglyph/final-letter passes
    text = re.sub(r'א\u05B4מ\u05B8?ם', 'אימם', text)
    text = re.sub(r'(?<=אביהם וגם )אמם(?![א-ת])', 'אימם', text)
    text = re.sub(r'[\u0591-\u05BD\u05BF-\u05C7]', '', text)

    # 4. Normalize multi-lingual phrases and Arabic idioms
    for pattern, repl in UNIVERSAL_PHRASES:
        text = re.sub(pattern, repl, text)

    for pattern, repl in ARABIC_PHRASES:
        text = re.sub(pattern, repl, text)

    # 5. Convert homoglyphs into pure Hebrew, tracking whether any foreign character was replaced
    had_homoglyph = False
    if re.search(r'[\u064B-\u065F\u0670]', text):
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        had_homoglyph = True

    for cyr, he in CYRILLIC_TO_HEBREW.items():
        if cyr in text:
            text = text.replace(cyr, he)
            had_homoglyph = True

    for ar, he in ARABIC_TO_HEBREW.items():
        if ar in text:
            text = text.replace(ar, he)
            had_homoglyph = True

    for fg, he in UNIVERSAL_HOMOGLYPH_MAP.items():
        if fg in text:
            text = text.replace(fg, he)
            had_homoglyph = True

    # 6. Only normalize final letters if a foreign homoglyph was actually replaced in this string
    if had_homoglyph:
        text = normalize_final_letters(text)

    # Repair known historical final-letter corruptions (אמם -> אממ, המם -> הממ, ממם -> מממ, טרמף -> טרמפ)
    for pattern, repl in CORRUPTED_FINAL_LETTER_REPAIRS:
        text = re.sub(pattern, repl, text)

    # 7. Strip any remaining disallowed foreign script characters & Nikud
    text = re.sub(DISALLOWED_FOREIGN_SCRIPTS, '', text)
    text = re.sub(r'[\u0591-\u05BD\u05BF-\u05C7]', '', text)

    # Clean double spaces or broken quotes
    text = re.sub(r'[ \t]+', ' ', text).strip()
    return f"{ssa_lead}{text}" if ssa_lead else text

# Alias for external script compatibility
normalize_homoglyphs = clean_and_sanitize_text

def detect_hebrew(content, min_chars=6, min_ratio=0.15):
    """
    Checks if content has a valid ratio of Hebrew letters.
    """
    hebrew_chars = len(re.findall(r'[\u0590-\u05FF]', content))
    latin_chars = len(re.findall(r'[a-zA-Z]', content))
    total_alpha = hebrew_chars + latin_chars

    if total_alpha == 0:
        return False, 0.0, "No alphabetic characters found"

    ratio = hebrew_chars / total_alpha
    is_hebrew = ((hebrew_chars >= min_chars) or (latin_chars == 0 and hebrew_chars >= 3)) and (ratio >= min_ratio)
    details = f"Hebrew chars: {hebrew_chars}, Latin chars: {latin_chars} (Hebrew ratio: {ratio:.1%})"
    return is_hebrew, ratio, details

DANGLING_CREDIT_REGEX = re.compile(
    r'(?:על\s+ידי|ע["״\']?י|(?:מלאכת\s+)?ה?(?:תרגום|סנכרון)\s*:|הועלה\s+על\s+ידי|synced\s+by|translated\s+by)\s*$',
    re.IGNORECASE
)

def _strip_tags_and_bidi(line):
    return BIDI_CONTROL_CHARS_REGEX.sub('', re.sub(r'<[^>]+>|\{\\[^}]+\}', '', line)).strip()

def is_ad_line(line):
    clean = _strip_tags_and_bidi(line)
    return bool(AD_REGEX.search(clean))

def _filter_ad_lines_from_block(lines):
    """
    Filters advertising/credit lines from a subtitle cue block, including orphan second lines
    of multi-line translator credits (e.g. '<i>הובא וסונכרן על ידי\\nאריאל אפרתי</i>').
    Returns (kept_lines, removed_count).
    """
    kept = []
    removed = 0
    skip_next = False
    for idx, l in enumerate(lines):
        if skip_next:
            removed += 1
            skip_next = False
            continue
        if is_ad_line(l):
            removed += 1
            clean_curr = _strip_tags_and_bidi(l)
            has_unclosed_italic = ('<i' in l.lower() and '</i>' not in l.lower())
            if idx + 1 < len(lines):
                next_l = lines[idx + 1]
                clean_next = _strip_tags_and_bidi(next_l)
                closes_italic = ('</i>' in next_l.lower() and '<i' not in next_l.lower())
                if DANGLING_CREDIT_REGEX.search(clean_curr) or (
                    has_unclosed_italic and closes_italic and len(clean_next) <= 35 and not re.search(r'[\.?!]', clean_next)
                ):
                    skip_next = True
        else:
            kept.append(l)
    return kept, removed

def clean_line(line, clean_ads=True):
    """Filters out advertising/credit lines within a multi-line cue text."""
    if not line:
        return ""
    raw_lines = line.splitlines()
    if not clean_ads:
        return "\n".join(raw_lines)
    kept, _ = _filter_ad_lines_from_block(raw_lines)
    return "\n".join(kept)

BIDI_CONTROL_CHARS_REGEX = re.compile(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069]')

def detect_file_flip_polarity(content):
    """
    Scans an SRT file's Hebrew lines to determine whether the file was pre-flipped by a
    legacy visual BiDi tool (e.g. Subabi / HebFix) or is in normal logical order.
    Returns True if pre-flipped, False if logical.
    """
    if not content:
        return False
    preflipped_votes = 0
    logical_votes = 0
    for raw_line in content.splitlines():
        s = BIDI_CONTROL_CHARS_REGEX.sub('', re.sub(r'<[^>]+>|\{\\[^}]+\}', '', raw_line)).strip()
        if not s or '-->' in s or s.isdigit():
            continue
        if not re.search(r'[\u0590-\u05FF]', s):
            continue
        # Unambiguous pre-flipped indicators
        if (
            re.match(r'^[\.,!:;]+\s*[\u0590-\u05FF]', s)
            or re.match(r'^\?+\s*[\u0590-\u05FF]', s)
            or re.match(r'^(?!\.{2,}|…)["\'״׳]?[\.?!,:;]+\s*.+(?<![-–—\s][והבלכמש])(?<![-–—])[-–—]$', s)
            or re.match(r'^[-–—]\s*[\.,?!:;]+', s)
            or re.match(r'^[\.,?!:;]+\s*[-–—]', s)
            or re.match(r'^[\"\'\״\׳][\.,?!:;]+[\u0590-\u05FF]', s)
        ):
            preflipped_votes += 1
        elif re.search(r'[\u0590-\u05FF][\"\'\״\׳\)\]]*[\.?!,:;]+$', s) and not re.match(r'^[\.?!,:;…]', s):
            logical_votes += 1

    return (
        (preflipped_votes >= 2 or (preflipped_votes == 1 and logical_votes == 0))
        and preflipped_votes >= logical_votes * 0.25
    )

def canonicalize_visual_flipped_line(core, is_preflipped_file=False):
    """
    Reverses all 18 legacy visual-flipping mutations discovered across the 15.6M-line corpus
    back into pure logical Hebrew order before BiDi wrapping.
    """
    if not core or not re.search(r'[\u0590-\u05FF]', core):
        return core

    s = BIDI_CONTROL_CHARS_REGEX.sub('', core).strip()
    if not s:
        return core

    # 1. P_DASH_THEN_PUNCT: '- ,חיי אינם ראויים' or '- :יועצים -' -> '- חיי אינם ראויים,' / '- יועצים:'
    m = re.match(r'^([-–—])\s*([\.?!,:;…]+)\s*(.+?)(?:\s*[-–—])?$', s)
    if m:
        dash, punct, body = m.group(1), m.group(2), m.group(3).strip()
        if not re.search(r'[\.?!,:;…]$', body):
            s = f"{dash} {body}{punct}"

    # 2. P_PUNCT_THEN_DASH: '.-או-טי 8. הרמה הגבוהה ביותר' -> '- או-טי 8. הרמה הגבוהה ביותר.'
    m = re.match(r'^([\.?!,:;…]+)\s*([-–—])\s*(.+)$', s)
    if m and not re.search(r'[-–—]$', s):
        punct, dash, body = m.group(1), m.group(2), m.group(3).strip()
        if not re.search(r'[\.?!,:;…]$', body):
            s = f"{dash} {body}{punct}"

    # 3. P_FULL_EDGE_SWAP: '.המתקפה האחרונה ברצף מתקפות-' or '".המתקפה-' or '...המתקפה-'
    m = re.match(r'^([\"\'\״\׳]?\s*(?:\.{2,3}|…|[\.?!,:;]+)\s*[\"\'\״\׳]?)\s*(.+?)\s*(?<![-–—])([-–—])$', s)
    if m:
        lead_punct, body, dash = m.group(1).strip(), m.group(2).strip(), m.group(3)
        is_ellipsis_only = bool(re.match(r'^[\"\'\״\׳\s]*(?:\.{2,3}|…)[\"\'\״\׳\s]*$', lead_punct))
        if is_preflipped_file or not is_ellipsis_only:
            # Normalize quote+punct at the end if quote was part of lead_punct
            m_qp_edge = re.match(r'^([\"\'\״\׳])(\.{2,3}|…|[\.?!,:;]+)$', lead_punct)
            if m_qp_edge:
                lead_punct = m_qp_edge.group(2) + m_qp_edge.group(1)
            s = f"{dash} {body}{lead_punct}"

    # 4. P_START_QUOTE_PUNCT: '".אהבה משחררת אותך' or '."אבל זה בטח לא ימצא חן בעיניכם"'
    m_qp1 = re.match(r'^([\"\'\״\׳])((?:\.{2,3}|…|[\.?!,:;]+))\s*([\u0590-\u05FF].*)$', s)
    if m_qp1 and (is_preflipped_file or not re.match(r'^(?:\.{2,3}|…)$', m_qp1.group(2))) and not re.search(r'[\.?!,:;…][\"\'\״\׳]?$', s):
        q, punct, body = m_qp1.group(1), m_qp1.group(2), m_qp1.group(3).strip()
        if body.endswith(('"', "'", '״', '׳')):
            s = f"{q}{body[:-1]}{punct}{body[-1]}"
        else:
            s = f"{body}{punct}{q}"
    else:
        m_qp2 = re.match(r'^((?:\.{2,3}|…|[\.?!,:;]+))([\"\'\״\׳])\s*([\u0590-\u05FF].*)$', s)
        if m_qp2 and (is_preflipped_file or not re.match(r'^(?:\.{2,3}|…)$', m_qp2.group(1))) and not re.search(r'[\.?!,:;…][\"\'\״\׳]?$', s):
            punct, q, body = m_qp2.group(1), m_qp2.group(2), m_qp2.group(3).strip()
            if body.endswith(('"', "'", '״', '׳')):
                s = f"{q}{body[:-1]}{punct}{body[-1]}"
            else:
                s = f"{body}{punct}{q}"

    # 5. P_START_PUNCT_NUMBER: ',19 יש לי קול. אני בת"' -> '"יש לי קול. אני בת 19,'
    m_num = re.match(r'^(?:([,!:;\?]+)|(\.(?!\.)))(\d+)\s+([\u0590-\u05FF].*?)(?:([\"\'\״\׳]))?$', s)
    if m_num and not re.search(r'[\.?!,:;…][\"\'\״\׳]?$', s):
        punct = m_num.group(1) or m_num.group(2)
        num = m_num.group(3)
        body = m_num.group(4).strip()
        trail_q = m_num.group(5) or ""
        s = f"{trail_q}{body} {num}{punct}"

    # 6. P_START_PUNCT_ATTACHED & P_START_PUNCT_SPACED (excluding '...' and '? ')
    # Matches single/compound punctuation (. , ! : ; ?!) attached to start, or (. , ! : ;) with spaces
    if not re.search(r'[\.?!,:;…][\"\'\״\׳\)\]]*$', s):
        # 6a. Attached punctuation (excluding 2+ dots '..' / '...' / '…')
        m_att = re.match(r'^(?!\.{2,}|…)([\.?!,:;]+)(?=[\u0590-\u05FF\(\)\[\]\"\'\״\׳<])(.*)$', s)
        if m_att:
            punct, body = m_att.group(1), m_att.group(2).strip()
            s = f"{body}{punct}"
        else:
            # 6b. Spaced punctuation (. , ! : ;) - never valid at start of Hebrew line even with spaces
            m_sp = re.match(r'^(?!\.{2,}|…)([,!:;]+|\.(?!\.))\s+([\u0590-\u05FF].*)$', s)
            if m_sp:
                punct, body = m_sp.group(1), m_sp.group(2).strip()
                s = f"{body}{punct}"
            elif is_preflipped_file:
                # 6c. Polarity-dependent: '? ' with space (WALL-E vs The Night Before musical note '?' artifact)
                m_qm = re.match(r'^(\?+)\s+([\u0590-\u05FF].*)$', s)
                if m_qm:
                    punct, body = m_qm.group(1), m_qm.group(2).strip()
                    s = f"{body}{punct}"
                else:
                    # 6d. Polarity-dependent: '...בכך שתגיד' (leading ellipsis only in preflipped files)
                    m_el = re.match(r'^(\.{2,3}|…)\s*([\u0590-\u05FF].*)$', s)
                    if m_el:
                        punct, body = m_el.group(1), m_el.group(2).strip()
                        s = f"{body}{punct}"

    # 7. P_END_DASH_ONLY: 'עובדות, שם: אלאניס נדין -' or 'הגנרל בקהיר-' -> '- עובדות...'
    # Gate strictly on pre-flipped files so logical interrupted lines ('אתה מבין ש-', 'וניפול עם נשק—') stay intact.
    if is_preflipped_file and not re.match(r'^[-–—]', s):
        m_ed = re.match(r'^(.+[\u0590-\u05FF][\.?!,:;\"\'\״\׳]*)\s*(?<![-–—])([-–—])$', s)
        if m_ed and not re.search(r'(?:^|\s)[והבלכמש]$', m_ed.group(1).strip()):
            s = f"{m_ed.group(2)} {m_ed.group(1).strip()}"

    # 8. Parentheses & Brackets Canonicalization
    # 8a. P_DOUBLE_OPEN_PAREN: '(לאודיטור (אדם שמקשיב.' -> 'לאודיטור (אדם שמקשיב).'
    if s.count('(') == 2 and s.count(')') == 0:
        m_dop = re.match(r'^\(\s*([^\(]+?\s*\([^\(]+?)([\.?!,:;…]*)$', s)
        if m_dop:
            s = f"{m_dop.group(1).strip()}){m_dop.group(2)}"
        else:
            s = re.sub(r'\(([\.?!,:;…]*)$', r')\1', s)
    # 8b. P_DOUBLE_CLOSE_PAREN: ')ראשית, הם הביאו את הדליקטסן )מעדנייה,' -> 'ראשית, הם הביאו את הדליקטסן (מעדנייה),'
    elif s.count(')') == 2 and s.count('(') == 0:
        m_dcp = re.match(r'^\)\s*([^\)]+?)\s*\)\s*([^\)]+?)([\.?!,:;…]*)$', s)
        if m_dcp:
            s = f"{m_dcp.group(1).strip()} ({m_dcp.group(2).strip()}){m_dcp.group(3)}"
        elif s.startswith(')'):
            s = '(' + s[1:]
    # 8c. P_INVERTED_PARENS: ')מדרגות לפני הבית(' -> '(מדרגות לפני הבית)'
    elif s.count('(') == 1 and s.count(')') == 1 and s.index(')') < s.index('('):
        s = re.sub(r'\)([^\(\)]+)\(', r'(\1)', s)

    # 8d. P_DOUBLE_BRACKETS: '[אתם מוקפים! [צרפתית' -> 'אתם מוקפים! [צרפתית]'
    if s.count('[') == 2 and s.count(']') == 0:
        m_dob = re.match(r'^\[\s*([^\[]+?\s*\[[^\[]+?)([\.?!,:;…]*)$', s)
        if m_dob:
            s = f"{m_dob.group(1).strip()}]{m_dob.group(2)}"
        else:
            s = re.sub(r'\[([\.?!,:;…]*)$', r']\1', s)
    elif s.count(']') == 2 and s.count('[') == 0:
        m_dcb = re.match(r'^\]\s*([^\]]+?)\s*\]\s*([^\]]+?)([\.?!,:;…]*)$', s)
        if m_dcb:
            s = f"{m_dcb.group(1).strip()} [{m_dcb.group(2).strip()}]{m_dcb.group(3)}"
        elif s.startswith(']'):
            s = '[' + s[1:]
    elif s.count('[') == 1 and s.count(']') == 1 and s.index(']') < s.index('['):
        s = re.sub(r'\]([^\[\]]+)\[', r'[\1]', s)

    return s

def apply_rlm_to_line(line, is_preflipped_file=False, clean_speakers=False):
    """
    Applies 3-stage BiDi canonicalization and RLM wrapping safely around tags
    (<i>, <b>, <u>, <font...>, {\\anX}) according to Unicode UAX #9:
      Stage 1: Strip existing BiDi controls & separate outer SSA/HTML tags.
      Stage 2: Canonicalize visually pre-flipped punctuation/brackets into logical order.
      Stage 3: Wrap inner logical core with leading RLM and trailing RLM (after trailing punctuation).
    """
    # Sanitize and normalize line first
    line = clean_and_sanitize_text(line)
    stripped = line.strip()
    if not stripped:
        return line

    # If no Hebrew in this line, keep untouched
    if not re.search(r'[\u0590-\u05FF]', stripped):
        return line

    # Strip any stray outer BiDi controls before extracting leading tags
    stripped = BIDI_CONTROL_CHARS_REGEX.sub('', stripped)

    # Separate SSA override prefix if present, e.g. "{\an8}..."
    ssa_prefix = ""
    ssa_match = re.match(r'^((?:\{\\[^}]+\})+)\s*(.*)$', stripped)
    if ssa_match:
        ssa_prefix = ssa_match.group(1)
        stripped = ssa_match.group(2).strip()

    # Separate opening HTML tags like <i>, <b>, <u>, <font color="...">
    tag_prefix = ""
    tag_open_match = re.match(r'^((?:<(?:[iIuUbB]|font\b[^>]*)>\s*)+)(.*)$', stripped, flags=re.IGNORECASE)
    if tag_open_match:
        tag_prefix = tag_open_match.group(1)
        stripped = tag_open_match.group(2).strip()

    # Separate closing HTML tags like </i>, </b>, </u>, </font>
    tag_suffix = ""
    tag_close_match = re.search(r'((?:\s*<\/(?:[iIuUbB]|font)>)+)$', stripped, flags=re.IGNORECASE)
    if tag_close_match:
        tag_suffix = tag_close_match.group(1)
        stripped = stripped[:tag_close_match.start()].strip()

    # Stage 2: Canonicalize pre-flipped visual order into logical order
    stripped = canonicalize_visual_flipped_line(stripped, is_preflipped_file=is_preflipped_file)

    # If leading punctuation preceded an opening HTML tag (e.g. '.<i>שלום</i>'), extract tag_prefix now
    if not tag_prefix:
        post_tag_open = re.match(r'^((?:<(?:[iIuUbB]|font\b[^>]*)>\s*)+)(.*)$', stripped, flags=re.IGNORECASE)
        if post_tag_open:
            tag_prefix = post_tag_open.group(1)
            stripped = post_tag_open.group(2).strip()

    if clean_speakers:
        stripped = SPEAKER_TAG_REGEX.sub(r'\1', stripped).strip()
        if not stripped:
            return ""
        if not re.search(r'[\u0590-\u05FF]', stripped):
            return f"{ssa_prefix}{tag_prefix}{stripped}{tag_suffix}"

    # Convert standard double quotes in genuine Hebrew acronyms to Hebrew gershayim (״),
    # strictly avoiding prefixed opening quotes of balanced "..." spans.
    stripped = re.sub(
        r'([\u0590-\u05FF]{2,})"([\u0590-\u05FF](?:ים|ות|ית)?)(?![\u0590-\u05FF"])(?=\s|$|[\.,?!:;…\)\]\-–—׳\'])',
        r'\1״\2',
        stripped
    )
    stripped = re.sub(
        r'(?<![\u0590-\u05FF"])([\u0590-\u05FF])"([\u0590-\u05FF](?:ים|ות)?)(?![\u0590-\u05FF"])(?=\s|$|[\.,?!:;…\)\]\-–—׳\'])',
        r'\1״\2',
        stripped
    )

    # Repair prefixed opening quotes previously converted to gershayim (e.g. ב״בוסטון ליגל" -> ב"בוסטון ליגל")
    # Runs regardless of even/odd quote counts while protecting genuine 2-letter acronyms before space.
    stripped = re.sub(
        r'(?<![א-ת])(?!(?:ב״ה|ב״ש|ד״ר|ה״י|ה״ש|כ״כ|כ״ע|כ״א|ל״ג|ל״ט|מ״פ|מ״מ|מ״ג|נ״ב|ס״מ|ק״מ|ש״ח|ש״ס|ש״י|ת״א|ז״ל)(?=\s|$|[\.,?!:;…\)\]\-–—]))((?:[והבלכמש]|ו?[בכלהמש]|מה|שה|כש|מש)־?)״([^\s"״][^"״\n]*?(?<=\S))"(?=\s|$|[\.,?!:;…\)\]\-–—])',
        r'\1"\2"',
        stripped
    )

    # Inject RLM after leading dialogue hyphen when followed by an English word so the hyphen stays on the right
    stripped = re.sub(r'^([-\–\—]\s+)(?=[A-Za-z])', rf'\1{RLM}', stripped)

    # If a Hebrew line ends with an English word or alphanumeric code (e.g. 'ב-FBI.' or 'ב-MI6.'),
    # place an RLM before the punctuation as well so the period does not attach to the LTR word's right edge
    stripped = re.sub(r'([A-Za-z][A-Za-z0-9\-]*\d|[A-Za-z])([\.!\?,:;…]+)$', rf'\1{RLM}\2', stripped)

    # Stage 3: Wrap logical core with leading RLM and trailing RLM (AFTER trailing punctuation)
    # Under UAX #9 Rule N1 (R + Neutral + R -> R), sandwiching trailing punctuation between the last
    # Hebrew letter (R) and a final RLM (R) locks all trailing punctuation to the visual left in Plex & Infuse.
    stripped = f"{RLM}{stripped}{RLM}"

    # Reconstruct with original tags
    return f"{ssa_prefix}{tag_prefix}{stripped}{tag_suffix}"

# Backward/cross-module alias
apply_bidi_and_punctuation = apply_rlm_to_line

SPEAKER_TAG_REGEX = re.compile(
    r'^((?:\{\\[^}]+\}\s*)*(?:<(?:[iIuUbB]|font\b[^>]*)>\s*)*)[\u200e\u200f\u202a-\u202e\u2066-\u2069\s]*(?:[-–—]\s*)?(?:'
    r'(?:אלן|דני|שירלי|פול|בראד|לורי|טרה|סאלי|דניס|קייטי|ג[\'\׳]רי|בברלי|אדווין|'
    r'אישה|גבר|דובר|דוברת|שופט|שופטת|השופט|השופטת|קול|קריין|קריינית|כולם|שוטר|שוטרת|ילד|ילדה|רופא|רופאה|אחות|עד(?!\s+\d+\s*:\s*\d)|עדה|סוכן|סוכנת)(?:\s+\d+)?:(?:\s+|$)'
    r'|\[\s*(?:לוחש|לוחשת|לוחשים|לוחש/ת)\s*\]\s+(?=[\u0590-\u05FFA-Za-z])'
    r')',
    re.IGNORECASE
)

def _parse_srt_start_ms(timeline):
    """Parses the start timestamp of an SRT timeline into milliseconds."""
    if not timeline:
        return None
    m = re.search(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->', timeline)
    if not m:
        return None
    return (
        int(m.group(1)) * 3600000
        + int(m.group(2)) * 60000
        + int(m.group(3)) * 1000
        + int(m.group(4))
    )


def _parse_en_cue_map(en_content):
    """Parses English SRT cues into exact-timeline lookup plus sorted timestamp entries."""
    by_time = {}
    entries = []
    if not en_content:
        return {"by_time": by_time, "entries": entries}
    normalized = en_content.replace("\r\n", "\n").replace("\r", "\n").strip()
    for eb in (re.split(r'\n\s*\n', normalized) if normalized else []):
        el = eb.strip().splitlines()
        if len(el) >= 2 and ('-->' in el[1] or '-->' in el[0]):
            has_idx = '-->' in el[1]
            t_str = (el[1] if has_idx else el[0]).strip()
            txt = "\n".join(el[2:] if has_idx else el[1:])
            by_time[t_str] = txt
            start_ms = _parse_srt_start_ms(t_str)
            if start_ms is not None:
                entries.append((start_ms, txt))
    entries.sort(key=lambda item: item[0])
    return {"by_time": by_time, "entries": entries}


def _find_companion_en_text(en_cue_map, timeline):
    """Finds companion English cue by exact timeline, falling back to nearest start within <= 2500ms."""
    t_key = timeline.strip()
    if t_key in en_cue_map["by_time"]:
        return en_cue_map["by_time"][t_key]
    entries = en_cue_map["entries"]
    if not entries:
        return ""
    he_start_ms = _parse_srt_start_ms(t_key)
    if he_start_ms is None:
        return ""
    best_text = ""
    best_diff = 2501
    for start_ms, txt in entries:
        diff = abs(start_ms - he_start_ms)
        if diff < best_diff:
            best_diff = diff
            best_text = txt
        elif start_ms > he_start_ms + 2501:
            break
    return best_text


def process_srt_content(content, clean_ads=False, clean_speakers=True, en_content=None):
    content = (content or "").replace("\r\n", "\n").replace("\r", "\n")
    is_preflipped_file = detect_file_flip_polarity(content)
    blocks = re.split(r'\n\s*\n', content.strip()) if content.strip() else []
    en_cue_map = _parse_en_cue_map(en_content) if en_content else {"by_time": {}, "entries": []}

    new_blocks = []
    total_subs = 0
    modified_lines = 0
    ads_removed = 0

    idx_counter = 1

    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2 and ('-->' in lines[1] or '-->' in lines[0]):
            if '-->' in lines[1]:
                timeline = lines[1]
                text_lines = lines[2:] if len(lines) >= 3 else []
            else:
                timeline = lines[0]
                text_lines = lines[1:]

            flat_text = "\n".join(text_lines).replace(r'\n', '\n')
            expanded_lines = [l for l in flat_text.splitlines() if l.strip()]
            was_initially_empty = (len(expanded_lines) == 0)

            if clean_ads and not was_initially_empty:
                expanded_lines, removed_in_block = _filter_ad_lines_from_block(expanded_lines)
                ads_removed += removed_in_block
                if not expanded_lines:
                    continue

            if was_initially_empty:
                total_subs += 1
                new_block = [str(idx_counter), timeline, ""]
                idx_counter += 1
                new_blocks.append("\n".join(new_block))
                continue

            companion_en = _find_companion_en_text(en_cue_map, timeline) if en_content else ""
            new_text_lines = []
            for tl in expanded_lines:
                orig_tl = tl
                if clean_speakers:
                    tl = SPEAKER_TAG_REGEX.sub(r'\1', tl)
                if companion_en:
                    tl = cross_check_bilingual_numbers(tl, companion_en)
                fixed = apply_rlm_to_line(tl, is_preflipped_file=is_preflipped_file, clean_speakers=clean_speakers)
                # Discard orphan dashes or empty lines
                clean_check = BIDI_CONTROL_CHARS_REGEX.sub('', fixed).strip()
                if clean_check not in ['', '-', '–', '—']:
                    new_text_lines.append(fixed)
                if fixed != orig_tl:
                    modified_lines += 1

            if not new_text_lines:
                continue

            total_subs += 1
            new_block = [str(idx_counter), timeline] + new_text_lines
            idx_counter += 1
            new_blocks.append("\n".join(new_block))
        elif lines:
            new_blocks.append("\n".join(lines))

    result_text = "\n\n".join(new_blocks) + "\n" if new_blocks else ""
    return result_text, total_subs, modified_lines, ads_removed

def _atomic_write_text(dest_path, content):
    """Writes text atomically via a temporary sibling file and touches mtime for Plex/Infuse."""
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest.with_name(f".{dest.name}.tmp.{os.getpid()}.{threading.get_ident()}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, dest)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
    try:
        os.utime(dest, None)
    except Exception:
        pass

def process_file(file_path, output_path=None, in_place=False, force=False, dry_run=False, backup=False, clean_ads=False, en_path=None):
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

    en_content = None
    if en_path:
        ep = Path(en_path)
        if ep.is_file():
            en_content, _ = read_file_with_auto_encoding(ep)

    fixed_content, total_subs, modified_lines, ads_removed = process_srt_content(
        content, clean_ads=clean_ads, en_content=en_content
    )

    enc_note = f" (Converted from {encoding_detected} to UTF-8)" if encoding_detected != 'utf-8' else ""
    ads_note = f", {ads_removed} ad lines removed" if ads_removed > 0 else ""

    if dry_run:
        print(f"[DRY-RUN] {p.name}: {total_subs} subtitles{enc_note} -> would adjust {modified_lines} lines{ads_note}.")
        return total_subs, modified_lines, ads_removed, "dry_run"

    dest = p if in_place else Path(output_path if output_path else str(p).replace(".srt", ".plex_fixed.srt"))

    if in_place and backup:
        bak_file = p.with_suffix(".srt.bak")
        shutil.copy2(p, bak_file)
        try:
            os.utime(bak_file, None)
        except Exception:
            pass

    _atomic_write_text(dest, fixed_content)

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
    parser.add_argument("--en", help="Optional companion English SRT file for bilingual number cross-checking")

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

    en_arg = None
    if args.en:
        ep = Path(args.en)
        if ep.is_file() and len(file_list) == 1:
            en_arg = str(ep)
        elif ep.is_file() and len(file_list) > 1:
            print("[!] Ignoring --en because multiple target SRTs matched; pass --en with a single SRT file.")
        elif not ep.exists():
            print(f"[!] Ignoring missing --en file: {args.en}")

    for srt in sorted(file_list):
        if args.output_dir:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / srt.name
            subs, mods, ads, res = process_file(
                srt, output_path=out_file, in_place=False, force=args.force,
                dry_run=args.dry_run, backup=args.backup, clean_ads=args.clean_ads,
                en_path=en_arg
            )
        else:
            subs, mods, ads, res = process_file(
                srt, in_place=args.in_place, force=args.force,
                dry_run=args.dry_run, backup=args.backup, clean_ads=args.clean_ads,
                en_path=en_arg
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
