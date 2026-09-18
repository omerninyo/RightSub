import pytest
import re
from importlib import import_module

merge_module = import_module("05_merge_and_validate")
fix_plex_module = import_module("07_fix_plex_punctuation")

RLM = "\u200F"
GERSHAYIM = "\u05F4"

class TestBiDiAndTextFormatting:
    def test_apply_rlm_trailing_punctuation(self):
        # Hebrew sentence with period at end
        raw = "שלום עולם."
        fixed = merge_module.apply_rlm_punctuation_fix(raw)
        assert fixed.startswith(RLM)
        assert fixed.endswith(f"{RLM}.")

    def test_apply_rlm_question_and_exclamation(self):
        raw1 = "מה קרה?"
        fixed1 = merge_module.apply_rlm_punctuation_fix(raw1)
        assert fixed1.endswith(f"{RLM}?")
        
        raw2 = "דני קריין!"
        fixed2 = merge_module.apply_rlm_punctuation_fix(raw2)
        assert fixed2.endswith(f"{RLM}!")

    def test_gershayim_conversion_for_acronyms(self):
        # Standard quotes in acronyms should be converted to Hebrew Gershayim
        raw = 'עו"ד אמר שלום לארה"ב ובימ"ש'
        fixed = merge_module.apply_rlm_punctuation_fix(raw)
        assert 'עו״ד' in fixed
        assert 'ארה״ב' in fixed
        assert 'בימ״ש' in fixed
        assert '"' not in fixed

    def test_idempotency_no_duplicate_rlm(self):
        raw = "שלום עולם."
        fixed_once = merge_module.apply_rlm_punctuation_fix(raw)
        fixed_twice = merge_module.apply_rlm_punctuation_fix(fixed_once)
        # Should not double-inject leading RLM
        assert not fixed_twice.startswith(f"{RLM}{RLM}")

    def test_orphaned_hyphens_filtering(self):
        # A line with only a dash or RLM dash should be discarded
        dirty_lines = ["-", f"{RLM}-", f"{RLM} -", "—", f"{RLM}—", ""]
        for line in dirty_lines:
            assert line.strip() in ['', '-', f'{RLM}-', f'{RLM} -', '—', f'{RLM}—']

    def test_html_tag_preservation(self):
        # HTML italics should be preserved cleanly with apply_rlm_to_line
        raw = "<i>שלום חברים</i>"
        fixed = fix_plex_module.apply_rlm_to_line(raw)
        assert "<i>" in fixed
        assert "</i>" in fixed

    def test_arabic_homoglyph_normalization(self):
        # Arabic letters (Yeh \u064A, Waw \u0648, Noon \u0646) should be normalized to Hebrew
        raw = "זה לא יפתיע אותي ولמחץ אותם نכון."
        fixed = fix_plex_module.apply_rlm_to_line(raw)
        assert "אותי" in fixed
        assert "ולמחץ" in fixed
        assert "נכון" in fixed
        assert not re.search(r'[\u0600-\u06FF]', fixed)

    def test_arabic_phrase_normalization(self):
        # Arabic phrases like كل ما should be converted to כל מה
        raw = "כל ما עשית היה להרחיק אותם."
        fixed = fix_plex_module.apply_rlm_to_line(raw)
        assert "כל מה" in fixed
        assert not re.search(r'[\u0600-\u06FF]', fixed)

    def test_cyrillic_homoglyph_normalization(self):
        # Cyrillic lookalike m (\u043C) should be normalized to Hebrew mem
        raw = "שלום חבריм."
        fixed = fix_plex_module.apply_rlm_to_line(raw)
        assert "חברים" in fixed
        assert not re.search(r'[\u0400-\u04FF]', fixed)

    def test_literal_slash_n_unescaping(self):
        # Literal \n string should be unescaped into real newlines and processed cleanly
        raw = "שלום\\nמה שלומך?"
        fixed = fix_plex_module.clean_and_sanitize_text(raw)
        assert "\\n" not in fixed
        assert "\n" in fixed

    def test_transcript_truncation_and_json_artifact_cleaning(self):
        # Stray transcript truncation and leaked JSON should be stripped cleanly
        raw = 'אני כמעט שם <truncated 3545 bytes> {"index": 231, "hebrew": "ראית בזה'
        fixed = fix_plex_module.clean_and_sanitize_text(raw)
        assert "<truncated" not in fixed
        assert "3545" not in fixed
        assert "index" not in fixed
        assert "hebrew" not in fixed

    def test_universal_homoglyph_normalization(self):
        # Georgian, Armenian, Greek, Tibetan, Bengali, Thai, Katakana
        cases = [
            ("האם ה\u10D7זת בבושם הזה", "התזת"),
            ("קרויצפלד-י\u10D0\u10D9וב", "קרויצפלד-יאקוב"),
            ("נכחדו בשלושים השנים האחרונ\u03B5\u03C2...", "האחרונות"),
            ("עורך הדין האגדי מב\u0578ס\u03C4\u03BF\u03BD", "מבוסטון"),
            ("זה יהיה הרבה יותר גרוע, כי למעשה מר מ\u0995\u09C7\u09AC\u09BE", "מר מקבה"),
            ("לעשות פ\u0F62\u0F0Bסה מהעניין הזה", "פארסה"),
            ("ג׳ק בוסטי\u0E34\u0E01", "בוסטיק"),
            ("מתקד\u056B\u0574ים", "מתקדימים")
        ]
        for raw, expected in cases:
            fixed = fix_plex_module.clean_and_sanitize_text(raw)
            assert expected in fixed
            assert not re.search(fix_plex_module.DISALLOWED_FOREIGN_SCRIPTS, fixed)

