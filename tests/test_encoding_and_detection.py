import pytest
from importlib import import_module
from pathlib import Path

fix_plex = import_module("07_fix_plex_punctuation")

class TestEncodingAndDetection:
    def test_utf8_detection(self, tmp_path):
        f = tmp_path / "utf8.srt"
        f.write_text("1\n00:00:01,000 --> 00:00:02,000\nשלום עולם\n", encoding="utf-8")
        text, enc = fix_plex.read_file_with_auto_encoding(f)
        assert enc == "utf-8"
        assert "שלום עולם" in text

    def test_windows_1255_conversion(self, tmp_path):
        # Windows-1255 encoded bytes for "שלום עולם"
        hebrew_text = "1\n00:00:01,000 --> 00:00:02,000\nשלום עולם\n"
        raw_bytes = hebrew_text.encode("cp1255")
        
        f = tmp_path / "cp1255.srt"
        f.write_bytes(raw_bytes)
        
        text, enc = fix_plex.read_file_with_auto_encoding(f)
        assert enc in ["windows-1255", "cp1255"]
        assert "שלום עולם" in text

    def test_language_verification_skips_english(self, tmp_path):
        eng_file = tmp_path / "test.en.srt"
        eng_file.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello world this is English\n", encoding="utf-8")
        is_hebrew, ratio, details = fix_plex.detect_hebrew(eng_file.read_text(encoding="utf-8"))
        assert is_hebrew is False

    def test_language_verification_accepts_hebrew(self, tmp_path):
        heb_file = tmp_path / "test.he.srt"
        heb_file.write_text("1\n00:00:01,000 --> 00:00:02,000\nשלום לכולם בבית המשפט השלום והצדק\n", encoding="utf-8")
        is_hebrew, ratio, details = fix_plex.detect_hebrew(heb_file.read_text(encoding="utf-8"))
        assert is_hebrew is True

    def test_utf16_bom_detection(self, tmp_path):
        utf16_file = tmp_path / "utf16.he.srt"
        hebrew_text = "1\n00:00:01,000 --> 00:00:02,000\nשלום עולם בבית המשפט\n"
        utf16_file.write_bytes(hebrew_text.encode("utf-16"))
        text, enc = fix_plex.read_file_with_auto_encoding(utf16_file)
        assert enc == "utf-16"
        assert "שלום עולם" in text

    def test_windows_1252_european_not_misidentified_as_hebrew(self, tmp_path):
        auto_mod = import_module("18_auto_pipeline")
        webhook_mod = import_module("21_webhook_server")
        # French subtitle with >12 accented bytes in 0xE0..0xFA (é, à, è, ç, ê, ù, ô)
        french_srt = (
            "1\n00:00:01,000 --> 00:00:03,000\n"
            "C'est déjà l'été à Paris, très bien parlé, garçon!\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\n"
            "Où est la fenêtre de l'école? Voilà la réponse!\n"
        )
        fr_file = tmp_path / "french.srt"
        fr_file.write_bytes(french_srt.encode("cp1252"))

        text, enc = fix_plex.read_file_with_auto_encoding(fr_file)
        assert enc in ("cp1252", "latin1")
        is_heb, _, _ = fix_plex.detect_hebrew(text)
        assert is_heb is False
        assert auto_mod.is_hebrew_file(fr_file) is False
        assert webhook_mod.is_hebrew_content_sample(fr_file) is False

    def test_utf8_english_with_3byte_punctuation_not_corrupted(self, tmp_path):
        auto_mod = import_module("18_auto_pipeline")
        # 20+ smart apostrophes (’ = \xe2\x80\x99) and em-dashes (— = \xe2\x80\x94) whose lead byte is 0xE2
        en_text = (
            "1\n00:00:01,000 --> 00:00:04,000\n"
            "♪ Don’t stop — won’t stop — it’s a wonderful day — isn’t it? ♪\n\n"
            "2\n00:00:05,000 --> 00:00:08,000\n"
            "We’re going to see what’s happening — they’re already there — let’s go…\n"
        )
        en_file = tmp_path / "english_utf8.srt"
        en_file.write_text(en_text, encoding="utf-8")

        sampled = auto_mod.read_srt_sample_auto_encoding(en_file)
        assert "Don’t stop" in sampled
        assert auto_mod.is_hebrew_file(en_file) is False

