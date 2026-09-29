#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_polish_and_qc.py
----------------------
Unit test suite for the Semantic AI Polish & Subtitle QC Engine (scripts/19_polish_and_qc.py).
Tests:
1. Cue parsing and bilingual alignment (exact index & timestamp proximity).
2. Franchise detection and canonical lore dictionary retrieval.
3. Deterministic offline canon pass (replacing 'חרב לייזר' with 'חרב אור' without LLM).
4. Constrained prompt construction and JSON schema contract.
5. Markdown diff report generation with correct statistics.
6. Full end-to-end subtitle polish with mock AI response and Seed-Safe backup.
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import importlib
polish_module = importlib.import_module("19_polish_and_qc")

SAMPLE_EN_SRT = """1
00:01:10,000 --> 00:01:14,200
Your father's lightsaber. This is the weapon of a Jedi Knight.

2
00:01:15,000 --> 00:01:18,500
Can you hear me, Princess?

3
00:01:20,000 --> 00:01:23,000
I have a bad feeling about this.

4
00:01:25,000 --> 00:01:28,000
May the Force be with you.
"""

SAMPLE_HE_SRT = """1
00:01:10,000 --> 00:01:14,200
חרב הלייזר של אביך. זה הנשק של אביר ג'דיי.

2
00:01:15,000 --> 00:01:18,500
אתה שומע אותי, נסיכה?

3
00:01:20,000 --> 00:01:23,000
אני יש לי הרגשה רעה לגבי זה.

4
00:01:25,000 --> 00:01:28,000
מי ייתן והכוח יהיה עמך.
"""

class TestPolishAndQC:

    def test_parse_srt(self, tmp_path):
        srt_file = tmp_path / "test.srt"
        srt_file.write_text(SAMPLE_EN_SRT, encoding="utf-8")
        cues = polish_module.parse_srt(srt_file)
        assert len(cues) == 4
        assert cues[0]["index"] == 1
        assert "lightsaber" in cues[0]["text"]

    def test_align_bilingual_cues_exact(self):
        en_cues = [
            {"index": 1, "timing": "00:00:10,000 --> 00:00:12,000", "text": "Hello"},
            {"index": 2, "timing": "00:00:15,000 --> 00:00:18,000", "text": "Goodbye"}
        ]
        he_cues = [
            {"index": 1, "timing": "00:00:10,000 --> 00:00:12,000", "text": "שלום"},
            {"index": 2, "timing": "00:00:15,000 --> 00:00:18,000", "text": "להתראות"}
        ]
        aligned = polish_module.align_bilingual_cues(en_cues, he_cues)
        assert len(aligned) == 2
        assert aligned[0]["en"] == "Hello"
        assert aligned[0]["he"] == "שלום"

    def test_align_bilingual_cues_proximity(self):
        en_cues = [
            {"index": 10, "timing": "00:00:10,000 --> 00:00:12,000", "text": "Hello"},
            {"index": 11, "timing": "00:00:15,000 --> 00:00:18,000", "text": "Goodbye"}
        ]
        # Hebrew cues with different indices but matching timestamps
        he_cues = [
            {"index": 1, "timing": "00:00:10,200 --> 00:00:12,200", "text": "שלום"},
            {"index": 2, "timing": "00:00:15,100 --> 00:00:18,100", "text": "להתראות"}
        ]
        aligned = polish_module.align_bilingual_cues(en_cues, he_cues)
        assert len(aligned) == 2
        assert aligned[0]["en"] == "Hello"
        assert aligned[0]["he"] == "שלום"

    def test_detect_franchise(self):
        name, data = polish_module.detect_franchise("Star Wars Episode IV A New Hope")
        assert name == "star wars"
        assert len(data["canon_terms"]) > 0

        name_lotr, _ = polish_module.detect_franchise("Lord of the Rings The Two Towers")
        assert name_lotr == "lord of the rings"

        name_none, _ = polish_module.detect_franchise("Random Indie Drama")
        assert name_none is None

    def test_deterministic_canon_pass(self):
        _, franchise_data = polish_module.detect_franchise("Star Wars")
        aligned = [
            {"index": 1, "timing": "...", "en": "Lightsaber", "he": "חרב הלייזר של אביך."},
            {"index": 2, "timing": "...", "en": "Hello", "he": "שלום לכולם."}
        ]
        mods = polish_module.run_deterministic_canon_pass(aligned, franchise_data)
        assert 1 in mods
        assert "חרב האור" in mods[1]["polished_he"]
        assert 2 not in mods  # Conservation rule: line 2 left untouched

    def test_build_polish_prompt(self):
        _, franchise_data = polish_module.detect_franchise("Star Wars")
        aligned = [
            {"index": 1, "timing": "...", "en": "Lightsaber", "he": "חרב הלייזר"}
        ]
        prompt = polish_module.build_polish_prompt(
            aligned,
            title="Star Wars (1977)",
            franchise_name="star wars",
            franchise_data=franchise_data,
            characters=[{"name": "Princess Leia", "gender": "Female", "pronouns": "את/היא"}]
        )
        assert "THE CONSERVATION RULE" in prompt
        assert "Lightsaber" in prompt
        assert "Princess Leia" in prompt
        assert "JSON SCHEMA" in prompt

    def test_generate_diff_report(self, tmp_path):
        report_file = tmp_path / "diff.md"
        mods = {
            1: {
                "index": 1,
                "original_he": "חרב הלייזר של אביך.",
                "polished_he": "חרב האור של אביך.",
                "reason": "מינוח קאנוני (חרב אור)"
            }
        }
        en_map = {1: "Your father's lightsaber."}
        content = polish_module.generate_diff_report("Star Wars", 10, mods, report_file, en_map)
        assert report_file.exists()
        assert "10" in content
        assert "9 (90.0%)" in content
        assert "1 (10.0%)" in content
        assert "חרב האור של אביך." in content

    def test_full_polish_dry_run_and_in_place_backup(self, tmp_path):
        he_file = tmp_path / "Star.Wars.he.srt"
        en_file = tmp_path / "Star.Wars.en.srt"
        he_file.write_text(SAMPLE_HE_SRT, encoding="utf-8")
        en_file.write_text(SAMPLE_EN_SRT, encoding="utf-8")

        # 1. Test Dry Run (--diff-only)
        args_dry = MagicMock()
        args_dry.offline_canon_only = True
        args_dry.diff_only = True
        args_dry.dry_run = True
        args_dry.in_place = False
        args_dry.output = None
        args_dry.diff_report = None
        args_dry.title = "Star Wars"

        res_dry = polish_module.polish_subtitle_file(he_file, en_file, args_dry)
        assert res_dry is True
        diff_report = tmp_path / "Star.Wars_polish_diff.md"
        assert diff_report.exists()
        # Subtitle file should NOT be created in diff-only
        assert not (tmp_path / "Star.Wars.he.polished.srt").exists()

        # 2. Test Execution with In-Place & Seed-Safe Backup
        args_inplace = MagicMock()
        args_inplace.offline_canon_only = True
        args_inplace.diff_only = False
        args_inplace.dry_run = False
        args_inplace.in_place = True
        args_inplace.output = None
        args_inplace.diff_report = None
        args_inplace.title = "Star Wars"

        res_inplace = polish_module.polish_subtitle_file(he_file, en_file, args_inplace)
        assert res_inplace is True
        
        # Verify Seed-Safe backup exists
        backup_file = tmp_path / "Star.Wars.he.original.srt"
        assert backup_file.exists()
        assert "חרב הלייזר" in backup_file.read_text(encoding="utf-8")

        # Verify target file was mastered and polished
        polished_content = he_file.read_text(encoding="utf-8")
        assert "חרב האור" in polished_content
        assert "\u200F" in polished_content  # RLM mark present

    def test_polish_loads_translation_bible(self, tmp_path):
        he_file = tmp_path / "Movie.he.srt"
        en_file = tmp_path / "Movie.en.srt"
        he_file.write_text(SAMPLE_HE_SRT, encoding="utf-8")
        en_file.write_text(SAMPLE_EN_SRT, encoding="utf-8")

        bible_data = {
            "metadata": {
                "title": "Star Wars",
                "overview": "A long time ago in a galaxy far, far away...",
                "genres": ["Action", "Sci-Fi"]
            },
            "characters": [
                {"name": "Luke Skywalker", "hebrew_name": "לוק סקייווקר", "gender": "male", "pronouns": "אתה/הוא"},
                {"name": "Leia Organa", "hebrew_name": "ליאה אורגנה", "gender": "female", "pronouns": "את/היא"}
            ]
        }
        bible_path = tmp_path / "translation_bible.json"
        bible_path.write_text(json.dumps(bible_data, ensure_ascii=False), encoding="utf-8")

        args = MagicMock()
        args.bible = str(bible_path)
        args.offline_canon_only = True
        args.diff_only = True
        args.dry_run = True
        args.in_place = False
        args.output = None
        args.diff_report = None
        args.title = "Star Wars"

        res = polish_module.polish_subtitle_file(he_file, en_file, args)
        assert res is True

    @patch("urllib.request.urlopen")
    def test_gemini_model_cascade_down_to_3_5_flash(self, mock_urlopen):
        import urllib.error
        polish_module._cached_gemini_models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
        polish_module._active_working_model = None

        call_count = 0
        def side_effect(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                err_body = json.dumps({"error": {"message": f"model unavailable, code {call_count}"}}).encode("utf-8")
                raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, MagicMock(read=lambda: err_body))
            # 4th call (gemini-3.5-flash) succeeds
            mock_resp = MagicMock()
            mock_resp.__enter__.return_value = mock_resp
            mock_resp.read.return_value = json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": '{"modifications": []}'
                        }]
                    }
                }]
            }).encode("utf-8")
            return mock_resp

        mock_urlopen.side_effect = side_effect
        result = polish_module.query_gemini_api("Test prompt", api_key="test-key")
        assert result == {"modifications": []}
        assert call_count == 4
        assert polish_module._active_working_model == "gemini-3.5-flash"


