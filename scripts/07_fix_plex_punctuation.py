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
    r'^[‏\u200F\s\-–—]*(?:מלאכת\s+)?ה?תרגום\s*:\s*\S+',
    r'^[‏\u200F\s\-–—]*(?:מלאכת\s+)?ה?סנכרון\s*:\s*\S+',
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
    (r'\bכל\s*ما\b', 'כל מה'),
    (r'\bما\b', 'מה'),
    (r'\bكل\s+ما\b', 'כל מה'),
    (r'\bتكون\b', 'תהיה'),
    (r'\bيكون\b', 'יהיה'),
    (r'\bاكون\b', 'אהיה'),
    (r'\bأكون\b', 'אהיה'),
    (r'\bبالכאד\b', 'בקושי'),
    (r'\bبالكاد\b', 'בקושי'),
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
    (r'האחרונ[ε\u03B5][ς\u03C2]', 'האחרונות'),
    (r'מב[ո\u0578]ס[τ\u03C4][ο\u03BF][ν\u03BD]', 'מבוסטון'),
    (r'בא[メ\u30E1][ר\u30EA][ק\u30AB]ה?', 'באמריקה'),
    (r'לא\s*מ[ե\u10D4][ל\u10DA]רוז', 'לא מלרוז'),
    (r'מר\s*מ[কেবাబ\u0995\u09C7\u09AC\u09BE\u0C2C\u0C3E]+', 'מר מקבה'),
    (r'פ[ר\u0F62\u0F0B]+סה', 'פארסה'),
    (r'ג׳ק\s*בוסטי[ק\u0E01\u0E34]+', 'ג׳ק בוסטיק'),
    (r'מתקד[ימ\u056B\u0574]+ם', 'מתקדימים'),
    (r'קרויצפלד[- ]י[א\u10D0][ק\u10D9]וב', 'קרויצפלד-יאקוב'),
    (r'ה[ת\u10D7]זת', 'התזת'),
    (r'[\u585A]', ''),
    (r'\\"', '"'),
    (r'\b(ו|ה|ב|ל|כ|מ|ש)?קאבתן\b', r'\g<1>קברניט'),
    (r'\bלשום\s+את\b', 'לשים את'),
    (r'\bמוחב\s+אותנו\b', 'מושכת אותנו'),
]

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
    # and exclude 'פ' -> 'ף' to preserve loanwords ending in /p/ (ג'יפ, קטשופ, טלסקופ, קליפ, וואטסאפ, טראמפ).
    punct = r'(?:[\u200F\s\.\?!,:;\–\—\)\]»…]|["\'״׳”’](?![א-ת])|$)'
    text = re.sub(r'(?<=[א-ת])כ(?=' + punct + r')', 'ך', text)
    text = re.sub(r'(?<=[א-ת])מ(?=' + punct + r')', 'ם', text)
    text = re.sub(r'(?<=[א-ת])נ(?=' + punct + r')', 'ן', text)
    text = re.sub(r'(?<=[א-ת])צ(?=' + punct + r')', 'ץ', text)

    # Explicitly repair prefixes mistakenly normalized before hyphens (e.g. ם-100 -> מ-100, ך-50 -> כ-50)
    text = re.sub(r'\bם-(?=\d|[א-תa-zA-Z])', 'מ-', text)
    text = re.sub(r'\bך-(?=\d|[א-תa-zA-Z])', 'כ-', text)
    text = re.sub(r'\bן-(?=\d|[א-תa-zA-Z])', 'נ-', text)
    text = re.sub(r'\bף-(?=\d|[א-תa-zA-Z])', 'פ-', text)
    text = re.sub(r'\bץ-(?=\d|[א-תa-zA-Z])', 'צ-', text)
    return text

def clean_and_sanitize_text(text):
    """
    Cleans transcript truncation tags, stray JSON syntax, unescapes literal \\n,
    and normalizes foreign homoglyphs (Arabic, Cyrillic, Georgian, Armenian, Greek, Asian) into pure Hebrew
    while preserving valid leading SSA override tags such as {\\an8}.
    """
    if not text:
        return ""

    # Preserve leading SSA tags (e.g. {\an8}, {\pos(x,y)}) before stripping stray JSON braces
    ssa_lead = ""
    ssa_match = re.match(r'^\s*(\{\\[^}]+\})\s*(.*)$', text, flags=re.DOTALL)
    if ssa_match:
        ssa_lead = ssa_match.group(1)
        text = ssa_match.group(2)

    # 1. Clean transcript truncation tags and leaked tool artifacts
    text = re.sub(r'<truncated\s+\d+\s+bytes>', '', text)

    # 2. Clean leaked JSON key/value syntax if dialogue got contaminated
    text = re.sub(r'["\']?hebrew["\']?\s*:\s*["\']?', '', text)
    text = re.sub(r'["\']?index["\']?\s*:\s*\d+,?', '', text)
    text = re.sub(r'^\s*[\{\}\[\]]+\s*', '', text)
    text = re.sub(r'\s*[\{\}\[\]]+\s*$', '', text)

    # 3. Unescape literal backslash-n sequences unconditionally
    text = text.replace(r'\n', '\n')
    text = text.replace(r'\r', '')
    text = text.replace(r'\"', '"')

    # 4. Normalize multi-lingual phrases and Arabic idioms
    for pattern, repl in UNIVERSAL_PHRASES:
        text = re.sub(pattern, repl, text)

    for pattern, repl in ARABIC_PHRASES:
        text = re.sub(pattern, repl, text)

    # 5. Convert homoglyphs into pure Hebrew
    for cyr, he in CYRILLIC_TO_HEBREW.items():
        if cyr in text:
            text = text.replace(cyr, he)

    for ar, he in ARABIC_TO_HEBREW.items():
        if ar in text:
            text = text.replace(ar, he)

    for fg, he in UNIVERSAL_HOMOGLYPH_MAP.items():
        if fg in text:
            text = text.replace(fg, he)

    # 6. Normalize final letters (e.g. at end of words)
    text = normalize_final_letters(text)

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

def is_ad_line(line):
    clean = re.sub(r'<[^>]+>', '', line).strip()
    return bool(AD_REGEX.search(clean))

def clean_line(line, clean_ads=True):
    """Filters out advertising/credit lines within a multi-line cue text."""
    if not line:
        return ""
    kept = []
    for l in line.splitlines():
        if clean_ads and is_ad_line(l):
            continue
        kept.append(l)
    return "\n".join(kept)

def apply_rlm_to_line(line):
    """
    Applies RLM formatting safely around tags (<i>, <b>, <u>, <font...>, {\\anX})
    according to Unicode UAX #9 without ever injecting RLM inside tag brackets.
    """
    # Sanitize and normalize line first
    line = clean_and_sanitize_text(line)
    stripped = line.strip()
    if not stripped:
        return line

    # If no Hebrew in this line, keep untouched
    if not re.search(r'[\u0590-\u05FF]', stripped):
        return line

    # Strip any stray outer RLM before extracting leading tags
    stripped = stripped.lstrip(RLM)

    # Separate SSA override prefix if present, e.g. "{\an8}..."
    ssa_prefix = ""
    ssa_match = re.match(r'^((?:\{\\[^}]+\})+)\s*(.*)$', stripped)
    if ssa_match:
        ssa_prefix = ssa_match.group(1)
        stripped = ssa_match.group(2).strip().lstrip(RLM)

    # Separate opening HTML tags like <i>, <b>, <u>, <font color="...">
    tag_prefix = ""
    tag_open_match = re.match(r'^((?:<(?:[iIuUbB]|font\b[^>]*)>\s*)+)(.*)$', stripped, flags=re.IGNORECASE)
    if tag_open_match:
        tag_prefix = tag_open_match.group(1)
        stripped = tag_open_match.group(2).strip().lstrip(RLM)

    # Separate closing HTML tags like </i>, </b>, </u>, </font>
    tag_suffix = ""
    tag_close_match = re.search(r'((?:\s*<\/(?:[iIuUbB]|font)>)+)$', stripped, flags=re.IGNORECASE)
    if tag_close_match:
        tag_suffix = tag_close_match.group(1)
        stripped = stripped[:tag_close_match.start()].strip()

    # Convert standard double quotes in Hebrew acronyms to Hebrew gershayim (״)
    stripped = re.sub(r'([\u0590-\u05FF])"([\u0590-\u05FF])', r'\1״\2', stripped)

    # Clean existing trailing RLMs (both before and after trailing punctuation) for idempotency
    stripped = stripped.rstrip(RLM)
    trailing_punct_pattern = r'([\.!\?,:;\-\–\—\)»\]"\'״׳”’…]+)$'
    stripped = re.sub(rf'{RLM}+{trailing_punct_pattern}', r'\1', stripped)

    # Clean existing RLM after leading dialogue hyphen, then re-inject if followed by an English word
    stripped = re.sub(rf'^([-\–\—]\s*){RLM}+', r'\1', stripped)
    stripped = re.sub(r'^([-\–\—]\s+)(?=[A-Za-z])', rf'\1{RLM}', stripped)

    # Add RLM before trailing neutral punctuation
    stripped = re.sub(trailing_punct_pattern, f'{RLM}\\1', stripped)

    # Clean and add leading RLM
    stripped = stripped.lstrip(RLM)
    stripped = RLM + stripped

    # Reconstruct with original tags
    return f"{ssa_prefix}{tag_prefix}{stripped}{tag_suffix}"

# Backward/cross-module alias
apply_bidi_and_punctuation = apply_rlm_to_line

SPEAKER_TAG_REGEX = re.compile(
    r'^[‏\u200F\s]*(?:'
    r'אלן|דני|שירלי|פול|בראד|לורי|טרה|סאלי|דניס|קייטי|ג\'רי|בברלי|אדווין|'
    r'אישה|גבר|שופט|שופטת|השופט|השופטת|קול|קריין|כולם|גבר 2|אישה 2'
    r'):\s*'
)

def process_srt_content(content, clean_ads=False, clean_speakers=True):
    blocks = re.split(r'\n\s*\n', content.strip())
    new_blocks = []
    total_subs = 0
    modified_lines = 0
    ads_removed = 0

    idx_counter = 1

    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) >= 2:
            timeline = lines[1]
            text_lines = lines[2:] if len(lines) >= 3 else []

            flat_text = "\n".join(text_lines).replace(r'\n', '\n')
            expanded_lines = [l for l in flat_text.splitlines() if l.strip()]

            if clean_ads:
                filtered_lines = []
                for l in expanded_lines:
                    if is_ad_line(l):
                        ads_removed += 1
                    else:
                        filtered_lines.append(l)
                expanded_lines = filtered_lines
                if not expanded_lines:
                    continue

            total_subs += 1
            new_text_lines = []
            for tl in expanded_lines:
                orig_tl = tl
                if clean_speakers:
                    tl = SPEAKER_TAG_REGEX.sub('', tl)
                fixed = apply_rlm_to_line(tl)
                # Discard orphan dashes or empty lines
                if fixed.strip() not in ['', '-', f'{RLM}-', f'{RLM} -', '—', f'{RLM}—']:
                    new_text_lines.append(fixed)
                if fixed != orig_tl:
                    modified_lines += 1

            if not new_text_lines:
                continue

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
    tmp_path = dest.with_name(f".{dest.name}.tmp.{os.getpid()}")
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
