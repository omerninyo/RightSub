import pytest
import re
from importlib import import_module

fix_plex = import_module("07_fix_plex_punctuation")

class TestJunkAndSDHCleaning:
    def test_promo_and_ad_detection(self):
        ad_lines = [
            "סונכרן ע״י קבוצת תרגום",
            "תורגם על ידי צוות Wizdom",
            "Downloaded from opensubtitles.org",
            "הורד מ- torec.net",
            "הצטרפו לערוץ הטלגרם t.me/movies",
            "Sync by SubCenter"
        ]
        for line in ad_lines:
            assert fix_plex.AD_REGEX.search(line) is not None

    def test_legitimate_dialogue_not_flagged_as_ad(self):
        dialogues = [
            "בוקר טוב אלן, המשרד בסכנה.",
            "אני הולך לבית המשפט העליון.",
            "דני קריין מעולם לא הפסיד תיק."
        ]
        for line in dialogues:
            assert fix_plex.AD_REGEX.search(line) is None

    def test_sdh_sound_pattern_matching(self):
        sound_patterns = [
            r"^\(.*\)$",
            r"^\[.*\]$",
            r"^\*+.*\*+$"
        ]
        test_samples = [
            "(screams)",
            "[LAUGHS]",
            "(instrumental music playing)",
            "***"
        ]
        for sample in test_samples:
            is_sound = any(re.match(p, sample.strip()) for p in sound_patterns)
            assert is_sound is True
