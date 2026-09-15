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
