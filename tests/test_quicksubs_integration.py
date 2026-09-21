import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Insert scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from importlib import import_module
transcribe_mod = import_module("00_transcribe_audio")
extract_mod = import_module("01_extract_subtitles")
align_mod = import_module("16_audio_align_sync")

class TestQuicksubsIntegration:

    def test_quicksubs_availability_helper(self):
        with patch("shutil.which", return_value="/usr/local/bin/quicksubs"):
            assert transcribe_mod.is_quicksubs_available() is True
        
        with patch("shutil.which", return_value=None):
            assert transcribe_mod.is_quicksubs_available() is False

    def test_transcribe_audio_missing_binary_graceful_error(self, tmp_path):
        dummy_media = tmp_path / "test.mp4"
        dummy_media.write_text("fake video content")

        with patch("shutil.which", return_value=None):
            res = transcribe_mod.transcribe_audio(str(dummy_media))
            assert res["success"] is False
            assert "quicksubs' is not installed" in res["error"]
            assert "brew install mattbirchler/tap/quicksubs" in res["error"]

    def test_transcribe_audio_invalid_engine(self, tmp_path):
        dummy_media = tmp_path / "test.mp4"
        dummy_media.write_text("fake video content")

        with patch("shutil.which", return_value="/usr/local/bin/quicksubs"):
            res = transcribe_mod.transcribe_audio(str(dummy_media), engine="invalid_engine")
            assert res["success"] is False
            assert "Invalid engine" in res["error"]

    @patch("subprocess.run")
    def test_transcribe_audio_cmd_construction(self, mock_run, tmp_path):
        dummy_media = tmp_path / "test.mp4"
        dummy_media.write_text("fake video content")
        expected_srt = tmp_path / "test.srt"
        expected_srt.write_text("1\n00:00:01,000 --> 00:00:03,000\nHello\n\n")

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"audioDurationSeconds": 10.5, "wordCount": 15, "outputs": ["' + str(expected_srt) + '"]}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        with patch("shutil.which", return_value="/usr/local/bin/quicksubs"):
            res = transcribe_mod.transcribe_audio(str(dummy_media), engine="whisper", format_type="srt", quiet=True)
            assert res["success"] is True
            assert res["engine"] == "whisper"
            assert res["output_file"] == str(expected_srt)
            
            # Verify command arguments passed
            cmd_called = mock_run.call_args[0][0]
            assert cmd_called[0] == "quicksubs"
            assert str(dummy_media) in cmd_called
            assert "--engine" in cmd_called
            assert "whisper" in cmd_called
            assert "-q" in cmd_called

    def test_audio_alignment_time_math(self):
        assert align_mod.parse_time("00:01:30,500") == 90500
        assert align_mod.format_time(90500) == "00:01:30,500"
        assert align_mod.format_time(0) == "00:00:00,000"

    def test_audio_alignment_offset_and_scale(self):
        # Target cues: starting at 1000ms, ending at 70000ms
        target_cues = [
            {"start": 1000, "end": 4000, "lines": ["Line 1"]},
            {"start": 70000, "end": 74000, "lines": ["Line 2"]}
        ]
        # Reference cues shifted by +2000ms offset (start 3000ms, end 72000ms)
        ref_cues = [
            {"start": 3000, "end": 6000, "lines": ["Spoken line 1"]},
            {"start": 72000, "end": 76000, "lines": ["Spoken line 2"]}
        ]

        scale, offset = align_mod.compute_alignment_parameters(target_cues, ref_cues)
        assert abs(scale - 1.0) < 0.001
        assert offset == 2000

    def test_align_subtitles_end_to_end_with_reference(self, tmp_path):
        target_srt = tmp_path / "target.he.srt"
        target_srt.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\n‏שלום עולם\n\n"
            "2\n00:01:10,000 --> 00:01:13,000\n‏להתראות\n\n",
            encoding="utf-8"
        )

        ref_srt = tmp_path / "ref_audio.srt"
        ref_srt.write_text(
            "1\n00:00:03,000 --> 00:00:05,000\nHello world\n\n"
            "2\n00:01:12,000 --> 00:01:15,000\nGoodbye\n\n",
            encoding="utf-8"
        )

        out_srt = tmp_path / "aligned.he.srt"
        res = align_mod.align_subtitles(
            unsynced_srt_path=str(target_srt),
            output_srt_path=str(out_srt),
            reference_srt_path=str(ref_srt)
        )

        assert res["success"] is True
        assert out_srt.exists()

        content = out_srt.read_text(encoding="utf-8")
        assert "‏שלום עולם" in content
        assert "00:00:03,000 --> 00:00:05,000" in content
        assert "00:01:12,000 --> 00:01:15,000" in content
