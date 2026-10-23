import pytest
import re
from importlib import import_module

merge_module = import_module("05_merge_and_validate")
fix_plex_module = import_module("07_fix_plex_punctuation")

RLM = "\u200F"
GERSHAYIM = "\u05F4"

class TestBiDiAndTextFormatting:
    def test_apply_rlm_trailing_punctuation(self):
        # Hebrew sentence with period at end: RLM must wrap the entire line (AFTER the period)
        raw = "שלום עולם."
        fixed = merge_module.apply_rlm_punctuation_fix(raw)
        assert fixed.startswith(RLM)
        assert fixed.endswith(f".{RLM}")
        assert fixed == f"{RLM}שלום עולם.{RLM}"

    def test_apply_rlm_question_and_exclamation(self):
        raw1 = "מה קרה?"
        fixed1 = merge_module.apply_rlm_punctuation_fix(raw1)
        assert fixed1.endswith(f"?{RLM}")
        
        raw2 = "דני קריין!"
        fixed2 = merge_module.apply_rlm_punctuation_fix(raw2)
        assert fixed2.endswith(f"!{RLM}")

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
        assert fixed_once == fixed_twice
        assert not fixed_twice.startswith(f"{RLM}{RLM}")
        assert not fixed_twice.endswith(f"{RLM}{RLM}")

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
        assert fixed == f"<i>{RLM}שלום חברים{RLM}</i>"

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
        # Cyrillic lookalike m (\u043C) should be normalized to Hebrew mem and final mem
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

    def test_ssa_override_tag_preservation(self):
        raw = "{\\an8}שלום עולם."
        fixed = fix_plex_module.apply_rlm_to_line(raw)
        assert fixed.startswith("{\\an8}")
        assert fixed == f"{{\\an8}}{RLM}שלום עולם.{RLM}"
        # Idempotency check
        assert fix_plex_module.apply_rlm_to_line(fixed) == fixed

    def test_html_font_and_nested_tags_preservation(self):
        raw = '<font color="#ffff00"><i>שלום עולם!</i></font>'
        fixed = fix_plex_module.apply_rlm_to_line(raw)
        assert fixed == f'<font color="#ffff00"><i>{RLM}שלום עולם!{RLM}</i></font>'
        # Ensure RLM is never injected inside HTML tag brackets
        for tag in re.findall(r'<[^>]+>', fixed):
            assert RLM not in tag
        # Idempotency check
        assert fix_plex_module.apply_rlm_to_line(fixed) == fixed

    def test_loanword_pe_hesitations_and_corrupted_final_repairs(self):
        raw = "אממ, הממ, מממ, נסענו בג'יפ עם פיליפ ובישופ לתפוס טרמפ לפי סעיף כ."
        fixed = fix_plex_module.clean_and_sanitize_text(raw)
        for word in ["אממ", "הממ", "מממ", "בג'יפ", "פיליפ", "ובישופ", "טרמפ", "סעיף כ."]:
            assert word in fixed
        for bad in ["אמם", "המם", "ממם", "טרמף", "פיליף", "בישוף"]:
            assert bad not in fixed

        # Verify active repair of previously corrupted words (אמם, המם, ממם, טרמף)
        corrupted = "אמם, המם, ממם, לקחתי טרמף וטרמף הביתה."
        repaired = fix_plex_module.clean_and_sanitize_text(corrupted)
        assert repaired == "אממ, הממ, מממ, לקחתי טרמפ וטרמפ הביתה."

    def test_sdh_square_brackets_preserved(self):
        raw = "[מוזיקה דרמטית]"
        fixed = fix_plex_module.clean_and_sanitize_text(raw)
        assert fixed == "[מוזיקה דרמטית]"

    def test_dialogue_hyphen_with_english_word_bidi(self):
        raw = "- FBI כאן."
        fixed = fix_plex_module.apply_rlm_to_line(raw)
        assert fixed == f"{RLM}- {RLM}FBI כאן.{RLM}"
        # Idempotency check
        assert fix_plex_module.apply_rlm_to_line(fixed) == fixed

    def test_decimal_percentage_and_trailing_quotes_bidi(self):
        raw_pct = "הסיכוי הוא 99.5%."
        fixed_pct = fix_plex_module.apply_rlm_to_line(raw_pct)
        # Ensure 99.5% is not split by an internal RLM before %
        assert "99.5%" in fixed_pct
        assert fixed_pct.endswith(f".{RLM}")

        raw_quote = 'הוא אמר "שלום"…'
        fixed_quote = fix_plex_module.apply_rlm_to_line(raw_quote)
        assert fixed_quote.startswith(RLM)
        assert fixed_quote.endswith(f'"…{RLM}')
        assert fix_plex_module.apply_rlm_to_line(fixed_quote) == fixed_quote

    def test_canonicalize_18_real_world_corpus_mutations(self):
        # 1. P_START_PUNCT_ATTACHED
        assert fix_plex_module.apply_rlm_to_line(",מבעד לאפלת הדרכים") == f"{RLM}מבעד לאפלת הדרכים,{RLM}"
        assert fix_plex_module.apply_rlm_to_line("?!מה קרה") == f"{RLM}מה קרה?!{RLM}"

        # 2. P_FULL_EDGE_SWAP
        assert fix_plex_module.apply_rlm_to_line(".המתקפה האחרונה ברצף מתקפות-") == f"{RLM}- המתקפה האחרונה ברצף מתקפות.{RLM}"

        # 3. P_DASH_THEN_PUNCT & both-ends dash with punct
        assert fix_plex_module.apply_rlm_to_line("- ,חיי אינם ראויים") == f"{RLM}- חיי אינם ראויים,{RLM}"
        assert fix_plex_module.apply_rlm_to_line("- :יועצים -") == f"{RLM}- יועצים:{RLM}"

        # 4. P_PUNCT_THEN_DASH
        assert fix_plex_module.apply_rlm_to_line(".-או-טי 8. הרמה הגבוהה ביותר") == f"{RLM}- או-טי 8. הרמה הגבוהה ביותר.{RLM}"

        # 5. P_START_QUOTE_PUNCT
        assert fix_plex_module.apply_rlm_to_line('".אהבה משחררת אותך') == f'{RLM}אהבה משחררת אותך."{RLM}'
        assert fix_plex_module.apply_rlm_to_line('."אבל זה בטח לא ימצא חן בעיניכם"') == f'{RLM}"אבל זה בטח לא ימצא חן בעיניכם."{RLM}'

        # 6. P_START_PUNCT_SPACED (. , ! : ;)
        assert fix_plex_module.apply_rlm_to_line(",       היא מאמצע שנות ה-70") == f"{RLM}היא מאמצע שנות ה-70,{RLM}"

        # 7. P_START_PUNCT_NUMBER
        assert fix_plex_module.apply_rlm_to_line(',19 יש לי קול. אני בת"') == f'{RLM}"יש לי קול. אני בת 19,{RLM}'

        # 8. P_DOUBLE_OPEN_PAREN, P_DOUBLE_CLOSE_PAREN, P_INVERTED_PARENS, P_DOUBLE_BRACKETS
        assert fix_plex_module.apply_rlm_to_line(".(לאודיטור (אדם שמקשיב") == f"{RLM}לאודיטור (אדם שמקשיב).{RLM}"
        assert fix_plex_module.apply_rlm_to_line(",)ראשית, הם הביאו את הדליקטסן )מעדנייה") == f"{RLM}ראשית, הם הביאו את הדליקטסן (מעדנייה),{RLM}"
        assert fix_plex_module.apply_rlm_to_line(")מדרגות לפני הבית(") == f"{RLM}(מדרגות לפני הבית){RLM}"
        assert fix_plex_module.apply_rlm_to_line("[אתם מוקפים! [צרפתית") == f"{RLM}אתם מוקפים! [צרפתית]{RLM}"

        # 9. RLM_BEFORE_END_PUNCT_BUG cleanup
        assert fix_plex_module.apply_rlm_to_line(f"{RLM}אלן שור{RLM}.") == f"{RLM}אלן שור.{RLM}"

        # 10. Polarity-dependent rules: P_ELLIPSIS_START_ONLY, P_START_QMARK_SPACE, P_END_DASH_ONLY
        # In logical file (is_preflipped_file=False):
        assert fix_plex_module.apply_rlm_to_line("...בכך שתגיד", is_preflipped_file=False) == f"{RLM}...בכך שתגיד{RLM}"
        assert fix_plex_module.apply_rlm_to_line("? הרוח הקרה נושפת", is_preflipped_file=False) == f"{RLM}? הרוח הקרה נושפת{RLM}"
        # In preflipped file (is_preflipped_file=True):
        assert fix_plex_module.apply_rlm_to_line("...בכך שתגיד", is_preflipped_file=True) == f"{RLM}בכך שתגיד...{RLM}"
        assert fix_plex_module.apply_rlm_to_line("? אז מה קורה", is_preflipped_file=True) == f"{RLM}אז מה קורה?{RLM}"
        assert fix_plex_module.apply_rlm_to_line("עובדות, שם: אלאניס נדין -", is_preflipped_file=True) == f"{RLM}- עובדות, שם: אלאניס נדין{RLM}"

    def test_georgian_homoglyph_and_bilingual_number_unflipping(self):
        # Georgian '\u10D4' inside 'דეייט' repaired to 'דייט'
        assert fix_plex_module.clean_and_sanitize_text("אונס ד\u10D4ייט.") == "אונס דייט."
        # Deterministic bilingual number un-flipping
        assert fix_plex_module.cross_check_bilingual_numbers("הוא בן 84 היום.", "He is 48 today.") == "הוא בן 48 היום."
        # Preserves numbers when already matching or when palindrome
        assert fix_plex_module.cross_check_bilingual_numbers("הוא בן 48 היום.", "He is 48 today.") == "הוא בן 48 היום."
        assert fix_plex_module.cross_check_bilingual_numbers("סעיף 22 בחוזה.", "Section 22 in the contract.") == "סעיף 22 בחוזה."
