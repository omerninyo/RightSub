#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_interactive_wizard.py
--------------------------
Unit and Red-Team tests for:
1. Interactive Terminal Mastering Wizard (`scripts/22_interactive_wizard.py`)
2. Drag & Drop path normalization across Finder, Windows Explorer, and PowerShell
3. Interactive Line-by-Line Polish Diff Reviewer (`scripts/19_polish_and_qc.py --interactive`)
4. Downloader Hooks & Background Service Generator (`scripts/20_config_and_doctor.py`)
"""

import sys
import json
import pytest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import importlib
wiz_mod = importlib.import_module("22_interactive_wizard")
polish_mod = importlib.import_module("19_polish_and_qc")
cfg_mod = importlib.import_module("20_config_and_doctor")


class TestDragAndDropNormalization:
    def test_finder_escaped_spaces_and_parens(self, tmp_path):
        movie = tmp_path / "Boston Legal (2004) S01E01.mkv"
        movie.touch()
        escaped = str(movie).replace(" ", r"\ ").replace("(", r"\(").replace(")", r"\)")
        normalized = wiz_mod.normalize_dragged_path(escaped)
        assert normalized == movie

    def test_windows_quotes_and_powershell_prefix(self, tmp_path):
        sub = tmp_path / "Movie Name.srt"
        sub.touch()
        ps_dragged = f"& '{sub}'"
        assert wiz_mod.normalize_dragged_path(ps_dragged) == sub

        win_quoted = f'"{sub}"'
        assert wiz_mod.normalize_dragged_path(win_quoted) == sub


class TestFileBrowserAndSummary:
    def test_inspect_target_summary_detects_seed_safe_candidates(self, tmp_path):
        vid = tmp_path / "Show.S01E01.mkv"
        vid.touch()
        plain_he = tmp_path / "Show.S01E01.srt"
        plain_he.write_text("1\n00:00:01,000 --> 00:00:02,000\nשלום עולם!\n", encoding="utf-8")
        en_srt = tmp_path / "Show.S01E01.en.srt"
        en_srt.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello world!\n", encoding="utf-8")

        summary = wiz_mod.inspect_target_summary(tmp_path)
        assert len(summary["videos"]) == 1
        assert len(summary["hebrew_srts"]) == 1
        assert len(summary["plain_hebrew_srts"]) == 1
        assert len(summary["english_srts"]) == 1

    def test_interactive_file_browser_selection(self, tmp_path):
        ep1 = tmp_path / "Episode1.mkv"
        ep1.touch()
        # Selecting '1' picks the first listed file; selecting '0' picks the whole folder
        picked_file = wiz_mod.interactive_file_browser(tmp_path, input_fn=lambda _: "1")
        assert picked_file == ep1

        picked_dir = wiz_mod.interactive_file_browser(tmp_path, input_fn=lambda _: "0")
        assert picked_dir == tmp_path.resolve()


class TestInteractivePolishReviewer:
    def test_approve_reject_edit_and_approve_all(self):
        mods = {
            10: {"index": 10, "original_he": "חרב לייזר", "polished_he": "חרב אור", "reason": "Canon"},
            20: {"index": 20, "original_he": "אתה מוכן, שירלי?", "polished_he": "את מוכנה, שירלי?", "reason": "Gender"},
            30: {"index": 30, "original_he": "יש 84 תיקים", "polished_he": "יש 48 תיקים", "reason": "Number"},
            40: {"index": 40, "original_he": "דეייט", "polished_he": "דייט", "reason": "Homoglyph"},
        }
        en_map = {10: "Lightsaber", 20: "Are you ready, Shirley?", 30: "48 cases", 40: "Date"}

        # Sequence of user inputs:
        # Cue #10 -> 'y' (approve)
        # Cue #20 -> 'n' (reject)
        # Cue #30 -> 'e' (edit manually) -> 'יש בדיוק 48 תיקים.'
        # Cue #40 -> 'a' (approve all remaining)
        answers = iter(["y", "n", "e", "יש בדיוק 48 תיקים.", "a"])
        approved = polish_mod.interactive_review_modifications(mods, en_map, input_fn=lambda _: next(answers))

        assert set(approved.keys()) == {10, 30, 40}
        assert 20 not in approved
        assert approved[30]["polished_he"] == "יש בדיוק 48 תיקים."
        assert "Manual User Edit" in approved[30]["reason"]

    def test_keyboard_interrupt_partial_save_recovery(self):
        """Red Team #8: Pressing Ctrl+C mid-review asks whether to keep edits approved so far."""
        mods = {
            1: {"index": 1, "original_he": "א", "polished_he": "ב", "reason": "Fix 1"},
            2: {"index": 2, "original_he": "ג", "polished_he": "ד", "reason": "Fix 2"},
        }

        calls = []
        def mock_input(_prompt):
            calls.append(_prompt)
            if len(calls) == 1:
                return "y"  # Approve cue #1
            if len(calls) == 2:
                raise KeyboardInterrupt()  # Hit Ctrl+C on cue #2
            return "y"  # Confirm saving partial approved edits

        approved = polish_mod.interactive_review_modifications(mods, {}, input_fn=mock_input)
        assert approved is not None
        assert list(approved.keys()) == [1]


class TestDownloaderHooksAndServiceGenerator:
    def test_install_downloader_hooks(self, tmp_path):
        res = cfg_mod.install_downloader_hooks(hooks_dir=tmp_path)
        assert (tmp_path / "qbittorrent_hook.sh").is_file()
        assert (tmp_path / "qbittorrent_hook.bat").is_file()
        assert (tmp_path / "transmission_hook.sh").is_file()
        assert "%F" in res["qbittorrent_command"]
        assert "http://localhost:8775/webhook/sonarr" in res["webhook_urls"]["sonarr"]

    def test_install_background_service_cross_platform(self, tmp_path, monkeypatch):
        for plat, expected_ext in [("darwin", ".plist"), ("linux", ".service"), ("win32", ".bat")]:
            monkeypatch.setattr(sys, "platform", plat)
            svc_dir = tmp_path / plat
            res = cfg_mod.install_background_service(service_dir=svc_dir, port=8775)
            assert res["platform"] == plat
            assert Path(res["service_file"]).is_file()
            assert res["service_file"].endswith(expected_ext)
