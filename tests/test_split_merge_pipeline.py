import pytest
import json
from pathlib import Path
from importlib import import_module

split_module = import_module("04_split_batches")
merge_module = import_module("05_merge_and_validate")

class TestSplitMergePipeline:
    def test_split_and_merge_exact_match(self, sample_english_srt, sample_hebrew_batches_dir, tmp_path):
        output_he_srt = tmp_path / "output.he.srt"
        
        success = merge_module.merge_and_validate(
            str(sample_english_srt),
            str(sample_hebrew_batches_dir),
            str(output_he_srt)
        )
        assert success is True
        assert output_he_srt.exists()
        
        content = output_he_srt.read_text(encoding="utf-8")
        assert "בפרקים הקודמים" in content
        assert "המשרד פושט רגל" in content
        assert "שלבים המוקדמים" in content

    def test_merge_fails_loudly_on_missing_index(self, sample_english_srt, tmp_path):
        bad_dir = tmp_path / "bad_translated"
        bad_dir.mkdir()
        incomplete_data = [
            {"index": 1, "hebrew": "שורה אחת"},
            {"index": 2, "hebrew": "שורה שתיים"},
        ]
        (bad_dir / "batch_01_he.json").write_text(json.dumps(incomplete_data), encoding="utf-8")
        
        output_he_srt = tmp_path / "output_fail.he.srt"
        success = merge_module.merge_and_validate(
            str(sample_english_srt),
            str(bad_dir),
            str(output_he_srt)
        )
        assert success is False

    def test_merge_clamps_overlapping_timestamps(self, tmp_path):
        en_srt = tmp_path / "overlapping.en.srt"
        en_srt.write_text(
            "1\n00:00:01,000 --> 00:00:04,500\nFirst line.\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\nSecond line.\n",
            encoding="utf-8"
        )
        batches_dir = tmp_path / "batches"
        batches_dir.mkdir()
        (batches_dir / "batch_01.json").write_text(
            json.dumps([
                {"index": 1, "hebrew": "שורה ראשונה."},
                {"index": 2, "hebrew": "שורה שנייה."}
            ], ensure_ascii=False),
            encoding="utf-8"
        )
        out_srt = tmp_path / "clamped.he.srt"
        assert merge_module.merge_and_validate(str(en_srt), str(batches_dir), str(out_srt)) is True
        merged_text = out_srt.read_text(encoding="utf-8")
        # Cue 1 end time (00:00:04,500) must be clamped to 20ms before Cue 2 start (00:00:03,980)
        assert "00:00:01,000 --> 00:00:03,980" in merged_text
        assert "00:00:04,000 --> 00:00:06,000" in merged_text

    def test_extract_filters_bitmap_subtitle_streams(self, tmp_path, monkeypatch):
        extract_mod = import_module("01_extract_subtitles")
        fake_video = tmp_path / "movie.mkv"
        fake_video.write_bytes(b"fake")

        # Stream 2 is PGS bitmap, Stream 3 is forced subrip, Stream 4 is full dialogue subrip
        fake_probe = {
            "streams": [
                {"index": 2, "codec_type": "subtitle", "codec_name": "hdmv_pgs_subtitle", "tags": {"language": "eng"}},
                {"index": 3, "codec_type": "subtitle", "codec_name": "subrip", "tags": {"language": "eng", "title": "Forced"}, "disposition": {"forced": 1}},
                {"index": 4, "codec_type": "subtitle", "codec_name": "subrip", "tags": {"language": "eng", "title": "Full"}, "disposition": {"forced": 0}},
            ]
        }
        monkeypatch.setattr(extract_mod, "inspect_video", lambda p: fake_probe)

        captured_cmd = []
        def fake_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            out_file = Path(cmd[-1])
            out_file.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello\n", encoding="utf-8")
            class DummyRes:
                returncode = 0
                stderr = ""
            return DummyRes()

        monkeypatch.setattr(extract_mod.subprocess, "run", fake_run)
        out_srt = tmp_path / "movie.en.srt"
        ok, reason = extract_mod.extract_from_video(fake_video, output_srt=out_srt)
        assert ok is True
        assert reason == "extracted"
        # Must select stream 0:4 (full subrip) and pass -nostdin
        assert "0:4" in captured_cmd
        assert "-nostdin" in captured_cmd

    def test_validate_anchor_alignment_detects_cue_drift(self):
        en_texts = {}
        he_synced = {}
        he_drifted = {}
        for i in range(1, 21):
            if i % 2 == 1:
                en_texts[i] = f"Did you see case {i * 10}?"
                he_synced[i] = f"האם ראית את תיק {i * 10}?"
            else:
                en_texts[i] = "♪ ♪"
                he_synced[i] = "♪ ♪"

        # Shift he_drifted by +1
        for i in range(1, 20):
            he_drifted[i] = he_synced[i + 1]
        he_drifted[20] = "שלום."

        ok_sync, rep_sync = merge_module.validate_anchor_alignment(en_texts, he_synced)
        assert ok_sync is True
        assert rep_sync["shifted_windows"] == 0

        ok_drift, rep_drift = merge_module.validate_anchor_alignment(en_texts, he_drifted)
        assert ok_drift is False
        assert rep_drift["shifted_windows"] >= 1


