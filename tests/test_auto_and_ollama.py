#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_auto_and_ollama.py
-----------------------
Unit tests for the autonomous zero-flag runner (18_auto_pipeline.py)
and offline local translation via Ollama (17_translate_ollama.py).
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import modules under test
import importlib
auto_mod = importlib.import_module("18_auto_pipeline")
ollama_mod = importlib.import_module("17_translate_ollama")

class TestOllamaIntegration:
    def test_select_best_model_fallback(self):
        installed = ["qwen2.5:7b", "mistral:latest"]
        chosen = ollama_mod.select_best_model(installed)
        assert chosen == "qwen2.5:7b"

        # Explicit request
        assert ollama_mod.select_best_model(installed, "custom_model") == "custom_model"

        # Empty installed
        assert ollama_mod.select_best_model([]) == "llama3.2"

    @patch("urllib.request.urlopen")
    def test_check_ollama_status_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "models": [{"name": "llama3.2:latest"}, {"name": "qwen2.5:7b"}]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        is_running, models = ollama_mod.check_ollama_status()
        assert is_running is True
        assert "llama3.2:latest" in models
        assert "qwen2.5:7b" in models

    @patch("urllib.request.urlopen")
    def test_check_ollama_status_offline(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")
        is_running, models = ollama_mod.check_ollama_status()
        assert is_running is False
        assert models == []

    @patch("urllib.request.urlopen")
    def test_translate_batch_mocked(self, mock_urlopen, tmp_path):
        batch_file = tmp_path / "batch_01_input.json"
        batch_file.write_text(json.dumps([
            {"index": 1, "text": "Good morning."},
            {"index": 2, "text": "Are you ready?"}
        ]), encoding="utf-8")

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "response": json.dumps({
                "1": "בוקר טוב.",
                "2": "האם אתה מוכן?"
            })
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        translations = ollama_mod.translate_batch(batch_file, model="llama3.2")
        assert translations["1"] == "בוקר טוב."
        assert translations["2"] == "האם אתה מוכן?"

class TestAutoPipeline:
    def test_is_hebrew_file_detection(self, tmp_path):
        he_file = tmp_path / "sample_he.srt"
        he_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nשלום לכולם, מה שלומכם?\n", encoding="utf-8")
        assert auto_mod.is_hebrew_file(he_file) is True

        en_file = tmp_path / "sample_en.srt"
        en_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nHello everyone, how are you today?\n", encoding="utf-8")
        assert auto_mod.is_hebrew_file(en_file) is False

    def test_handle_single_srt_hebrew_fixes_plex(self, tmp_path):
        he_file = tmp_path / "movie.he.srt"
        he_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nשלום עולם!\n", encoding="utf-8")

        args = MagicMock()
        args.no_clean_ads = False
        args.no_backup = False
        args.dry_run = False

        success = auto_mod.handle_single_srt(he_file, args)
        assert success is True
        
        # Verify RLM was injected into the Hebrew subtitle
        content = he_file.read_text(encoding="utf-8")
        assert "\u200F" in content

    def test_handle_single_srt_english_prepares_batches(self, tmp_path):
        en_file = tmp_path / "show.en.srt"
        en_file.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\nHello Alan, how is the case going?\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\nVery well, Shirley.\n",
            encoding="utf-8"
        )

        args = MagicMock()
        args.ollama = False
        args.no_clean_ads = False
        args.no_backup = False
        args.dry_run = False

        success = auto_mod.handle_single_srt(en_file, args)
        assert success is True

        # Check prompt batch directory created
        prompts_dir = tmp_path / "prompts_show"
        assert prompts_dir.is_dir()
        batch_files = list(prompts_dir.glob("batch_*_input.json"))
        assert len(batch_files) >= 1

    def test_handle_directory_batch_fixes_hebrew(self, tmp_path):
        season_dir = tmp_path / "Season 01"
        season_dir.mkdir()

        ep1 = season_dir / "S01E01.he.srt"
        ep1.write_text("1\n00:00:01,000 --> 00:00:03,000\nהאם אתה בטוח?\n", encoding="utf-8")

        ep2 = season_dir / "S01E02.he.srt"
        ep2.write_text("1\n00:00:01,000 --> 00:00:03,000\nזהו פרק שני!\n", encoding="utf-8")

        args = MagicMock()
        args.no_clean_ads = False
        args.no_backup = False
        args.dry_run = False
        args.ollama = False

        success = auto_mod.handle_directory(season_dir, args)
        assert success is True

        assert "\u200F" in ep1.read_text(encoding="utf-8")
        assert "\u200F" in ep2.read_text(encoding="utf-8")
