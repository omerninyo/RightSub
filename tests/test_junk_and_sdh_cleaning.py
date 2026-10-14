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

    def test_mid_sentence_colon_not_flagged_as_ad(self):
        legitimate_with_colons = [
            "יש לי בעיה בבקשת תרגום: המילה הזו לא ברורה.",
            "בזמן סנכרון: השעון קפץ קדימה.",
            "הוא ביקש תרגום: עברית לאנגלית."
        ]
        for line in legitimate_with_colons:
            assert fix_plex.is_ad_line(line) is False

        credit_headers = [
            "תרגום: סאבסנטר",
            "סנכרון: צוות כתובית",
            "- מלאכת התרגום: יוסי"
        ]
        for line in credit_headers:
            assert fix_plex.is_ad_line(line) is True

    def test_partial_cue_ad_stripping_preserves_dialogue(self):
        srt_content = (
            "1\n"
            "00:00:01,000 --> 00:00:03,000\n"
            "תרגום: סאבסנטר\n"
            "שלום לכולם!\n\n"
            "2\n"
            "00:00:04,000 --> 00:00:06,000\n"
            "סונכרן על ידי צוות טורק\n"
        )
        result_text, total_subs, modified_lines, ads_removed = fix_plex.process_srt_content(srt_content, clean_ads=True)
        assert ads_removed == 2
        assert total_subs == 1
        assert "סאבסנטר" not in result_text
        assert "שלום לכולם" in result_text

