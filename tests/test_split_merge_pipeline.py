import pytest
import json
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
