#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_config_and_doctor.py
-------------------------
Unit tests for `scripts/20_config_and_doctor.py` and CLI commands `config` and `doctor`.
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import importlib
config_module = importlib.import_module("20_config_and_doctor")


class TestConfigAndDoctor:
    def test_mask_key(self):
        assert config_module.mask_key("") == "<Not Set>"
        assert config_module.mask_key(None) == "<Not Set>"
        assert config_module.mask_key("short") == "********"
        assert config_module.mask_key("AIzaSy1234567890abcdef") == "AIza...cdef"

    def test_load_and_save_config(self, tmp_path, monkeypatch):
        test_file = tmp_path / "config.json"
        monkeypatch.setattr(config_module, "CONFIG_FILE", test_file)
        monkeypatch.setattr(config_module, "CONFIG_DIR", tmp_path)

        assert config_module.load_config() == {}

        sample = {"gemini_api_key": "test_gemini", "tmdb_api_key": "test_tmdb"}
        config_module.save_config(sample)

        loaded = config_module.load_config()
        assert loaded == sample

    def test_verify_tmdb_mocked(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            ok, msg = config_module.verify_tmdb("fake_key_123")
            assert ok is True
            assert "Authenticated" in msg

    def test_verify_gemini_mocked(self):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = json.dumps({
                "models": [{"name": "models/gemini-2.5-flash"}]
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            ok, msg = config_module.verify_gemini("fake_gemini_key")
            assert ok is True
            assert "gemini-flash verified" in msg

    def test_handle_config_show(self, tmp_path, monkeypatch, capsys):
        test_file = tmp_path / "config.json"
        test_file.write_text(json.dumps({"gemini_api_key": "AIzaSyTest123456789"}), encoding="utf-8")
        monkeypatch.setattr(config_module, "CONFIG_FILE", test_file)

        args = MagicMock()
        args.install_quicksubs = False
        args.show = True
        args.clear = False
        args.gemini = None
        args.tmdb = None

        res = config_module.handle_config(args)
        assert res == 0
        captured = capsys.readouterr().out
        assert "AIza...6789" in captured

    def test_handle_config_clear(self, tmp_path, monkeypatch):
        test_file = tmp_path / "config.json"
        test_file.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(config_module, "CONFIG_FILE", test_file)

        args = MagicMock()
        args.install_quicksubs = False
        args.show = False
        args.clear = True
        args.gemini = None
        args.tmdb = None

        res = config_module.handle_config(args)
        assert res == 0
        assert not test_file.exists()

    def test_doctor_smoke_test(self, capsys):
        args = MagicMock()
        # Even if APIs are not configured, doctor should print clean dashboard and return 0 or 1
        res = config_module.handle_doctor(args)
        captured = capsys.readouterr().out
        assert "RightSub System Health Doctor" in captured
        assert "Python Runtime" in captured
        assert "FFmpeg Suite" in captured

    def test_handle_config_install_quicksubs_non_mac(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "platform", "linux")
        args = MagicMock()
        args.install_quicksubs = True
        res = config_module.handle_config(args)
        assert res == 1
        assert "requires an Apple Silicon Mac" in capsys.readouterr().out
