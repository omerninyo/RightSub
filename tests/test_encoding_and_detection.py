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
