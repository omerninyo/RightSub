import pytest
import os
import glob
from pathlib import Path

BASE_REPO = Path("/Volumes/video/TV/TV Shows/Boston Legal Season 1 to 5 Mp4 x264 1080p")
SEASONS = ["Season 1", "Season 2", "Season 3", "Season 4", "Season 5"]

class TestBostonLegalFullDataset:
    @pytest.mark.parametrize("season", SEASONS)
    def test_all_episodes_have_subtitles(self, season):
        season_dir = BASE_REPO / season
        mp4_files = sorted(season_dir.glob("*.mp4"))
        assert len(mp4_files) > 0, f"No mp4 files found in {season}"
        
        for mp4 in mp4_files:
            he_srt = mp4.with_suffix(".he.srt")
            assert he_srt.exists(), f"Missing Hebrew subtitle: {he_srt.name}"
            assert he_srt.stat().st_size > 10000, f"Subtitle file too small: {he_srt.name} ({he_srt.stat().st_size} bytes)"

    @pytest.mark.parametrize("season", SEASONS)
    def test_subtitle_cue_parity_with_english(self, season):
        season_dir = BASE_REPO / season
        mp4_files = sorted(season_dir.glob("*.mp4"))
        
        for mp4 in mp4_files:
            en_srt = mp4.with_suffix(".en.srt")
            he_srt = mp4.with_suffix(".he.srt")
            
            if not en_srt.exists():
                continue
                
            en_content = en_srt.read_text(encoding="utf-8-sig", errors="ignore")
            he_content = he_srt.read_text(encoding="utf-8-sig", errors="ignore")
            
            en_cues = [c for c in en_content.strip().split("\n\n") if "-->" in c]
            he_cues = [c for c in he_content.strip().split("\n\n") if "-->" in c]
            
            assert len(en_cues) == len(he_cues), (
                f"Mismatch in {mp4.name}: English has {len(en_cues)} cues, Hebrew has {len(he_cues)} cues"
            )

    @pytest.mark.parametrize("season", SEASONS)
    def test_hebrew_subtitles_contain_rlm(self, season):
        season_dir = BASE_REPO / season
        mp4_files = sorted(season_dir.glob("*.mp4"))
        
        for mp4 in mp4_files:
            he_srt = mp4.with_suffix(".he.srt")
            assert he_srt.exists()
            content = he_srt.read_text(encoding="utf-8", errors="ignore")
            assert "\u200F" in content, f"File {he_srt.name} missing RLM marks"

    @pytest.mark.parametrize("season", SEASONS)
    def test_hebrew_subtitles_zero_anomalies(self, season):
        import re
        season_dir = BASE_REPO / season
        mp4_files = sorted(season_dir.glob("*.mp4"))
        
        for mp4 in mp4_files:
            he_srt = mp4.with_suffix(".he.srt")
            assert he_srt.exists()
            content = he_srt.read_text(encoding="utf-8", errors="ignore")
            
            # Assert zero Arabic or disallowed foreign script characters
            foreign_chars = re.findall(r'[\u0600-\u06FF\u0400-\u04FF\u0370-\u03FF\u0530-\u058F\u10A0-\u10FF\u0900-\u0DFF\u0E00-\u0E7F\u0F00-\u0FFF\u3040-\u30FF\u4E00-\u9FFF]', content)
            assert len(foreign_chars) == 0, f"Found {len(foreign_chars)} foreign script characters in {he_srt.name}: {set(foreign_chars)}"

            # Assert zero literal \n sequences
            assert r"\n" not in content, f"Found literal '\\n' string in {he_srt.name}"

            # Assert zero <truncated markers
            assert "<truncated" not in content, f"Found '<truncated' marker in {he_srt.name}"

            # Assert zero leaked JSON syntax artifacts
            json_artifacts = re.findall(r'["\']?hebrew["\']?\s*:\s*|["\']?index["\']?\s*:\s*\d+', content)
            assert len(json_artifacts) == 0, f"Found {len(json_artifacts)} JSON artifacts in {he_srt.name}"
