import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Insert scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from importlib import import_module
tmdb_mod = import_module("tmdb_client")
bible_mod = import_module("03_generate_bible")
prompt_mod = import_module("09_prompt_builder")

class TestTMDbIntegration:

    def test_parse_media_filename_tv(self):
        p1 = tmdb_mod.parse_media_filename("Boston.Legal.S01E05.1080p.mkv")
        assert p1["title"] == "Boston Legal"
        assert p1["season"] == 1
        assert p1["episode"] == 5
        assert p1["is_tv"] is True

        p2 = tmdb_mod.parse_media_filename("Peaky_Blinders_2x03.en.srt")
        assert p2["title"] == "Peaky Blinders"
        assert p2["season"] == 2
        assert p2["episode"] == 3
        assert p2["is_tv"] is True

    def test_parse_media_filename_movie(self):
        p = tmdb_mod.parse_media_filename("Inception.2010.BluRay.x264.mp4")
        assert p["title"] == "Inception"
        assert p["year"] == 2010
        assert p["is_tv"] is False

    def test_gender_mapping(self):
        assert tmdb_mod.map_gender(1) == ("female", "את/היא")
        assert tmdb_mod.map_gender(2) == ("male", "אתה/הוא")
        assert tmdb_mod.map_gender(0) == ("unknown", "אתה/את")

    def test_auth_detection(self):
        # Bearer v4 JWT token
        jwt = "ey" + "a" * 60
        token, is_bearer = tmdb_mod.get_tmdb_auth(jwt)
        assert is_bearer is True
        assert token == jwt

        # Standard v3 API Key
        v3_key = "abcdef1234567890abcdef1234567890"
        token, is_bearer = tmdb_mod.get_tmdb_auth(v3_key)
        assert is_bearer is False
        assert token == v3_key

    def test_missing_api_key_graceful_handling(self):
        with patch.dict(os.environ, {}, clear=True):
            res = tmdb_mod.fetch_show_or_movie_metadata(title="Boston Legal")
            assert res["success"] is False
            assert "API key not configured" in res["error"]

    @patch("tmdb_client.tmdb_get")
    def test_fetch_show_metadata_mocked(self, mock_get):
        def side_effect(endpoint, params=None, api_key=None):
            if endpoint == "/search/tv":
                return {
                    "results": [{
                        "id": 1739,
                        "name": "Boston Legal",
                        "overview": "Legal comedy-drama television series.",
                        "first_air_date": "2004-10-03",
                        "original_language": "en",
                        "origin_country": ["US"]
                    }]
                }
            elif endpoint == "/tv/1739":
                return {
                    "genres": [{"id": 35, "name": "Comedy"}, {"id": 18, "name": "Drama"}],
                    "origin_country": ["US"]
                }
            elif endpoint == "/tv/1739/season/1/episode/5":
                return {
                    "name": "An Eye for an Eye",
                    "overview": "Alan Shore takes on a new civil case.",
                    "guest_stars": [
                        {"name": "Leslie Jordan", "character": "Bernard Ferrion", "gender": 2},
                        {"name": "Betty White", "character": "Catherine Piper", "gender": 1}
                    ]
                }
            elif endpoint == "/tv/1739/credits":
                return {
                    "cast": [
                        {"name": "James Spader", "character": "Alan Shore", "gender": 2},
                        {"name": "Candice Bergen", "character": "Shirley Schmidt", "gender": 1}
                    ]
                }
            return {}

        mock_get.side_effect = side_effect

        meta = tmdb_mod.fetch_show_or_movie_metadata(
            title="Boston Legal",
            season=1,
            episode=5,
            api_key="mock_key"
        )

        assert meta["success"] is True
        assert meta["title"] == "Boston Legal"
        assert meta["genres"] == ["Comedy", "Drama"]
        assert "Alan Shore" in meta["overview"]
        
        # Verify characters and genders
        chars = {c["name"]: c for c in meta["characters"]}
        assert "Alan Shore" in chars
        assert chars["Alan Shore"]["gender"] == "male"
        assert chars["Alan Shore"]["pronouns"] == "אתה/הוא"

        assert "Shirley Schmidt" in chars
        assert chars["Shirley Schmidt"]["gender"] == "female"
        assert chars["Shirley Schmidt"]["pronouns"] == "את/היא"

        # Verify guest stars
        assert "Catherine Piper" in chars
        assert chars["Catherine Piper"]["gender"] == "female"
        assert chars["Catherine Piper"]["is_guest"] is True

    @patch("03_generate_bible.fetch_metadata")
    def test_extract_entities_merges_tmdb(self, mock_fetch, tmp_path):
        dummy_srt = tmp_path / "Boston.Legal.S01E05.en.srt"
        dummy_srt.write_text(
            "1\n00:00:01,000 --> 00:00:03,000\nALAN: Good morning, Shirley.\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\nSHIRLEY: Hello, Alan.\n\n",
            encoding="utf-8"
        )

        mock_fetch.return_value = {
            "success": True,
            "tmdb_id": 1739,
            "title": "Boston Legal",
            "overview": "Courtroom drama",
            "genres": ["Drama"],
            "origin_country": ["US"],
            "original_language": "en",
            "characters": [
                {"name": "Alan Shore", "gender": "male", "pronouns": "אתה/הוא", "is_guest": False},
                {"name": "Shirley Schmidt", "gender": "female", "pronouns": "את/היא", "is_guest": False}
            ]
        }

        bible = bible_mod.extract_entities(
            [str(dummy_srt)],
            use_tmdb=True,
            tmdb_key="mock_key"
        )

        assert bible["metadata"]["tmdb_id"] == 1739
        chars = {c["name"]: c for c in bible["characters"]}
        
        # ALAN should have matched Alan Shore and received verified male gender
        assert "ALAN" in chars
        assert chars["ALAN"]["gender"] == "male"
        assert chars["ALAN"]["pronouns"] == "אתה/הוא"
        assert chars["ALAN"]["verified_by_tmdb"] is True

    def test_prompt_builder_british_dialect_injection(self, tmp_path):
        dummy_bible = tmp_path / "translation_bible.json"
        dummy_bible.write_text(json.dumps({
            "metadata": {
                "title": "Peaky Blinders",
                "origin_country": ["GB"],
                "genres": ["Crime", "Drama"],
                "overview": "Tommy Shelby expands his empire."
            },
            "characters": [
                {"name": "Tommy Shelby", "gender": "male", "pronouns": "אתה/הוא"}
            ],
            "honorifics_and_terms": []
        }), encoding="utf-8")

        prompt_str, meta = prompt_mod.load_bible_data(str(dummy_bible))
        assert "British English (UK)" in prompt_str
        assert "pissed'=drunk" in prompt_str
        assert meta["overview"] == "Tommy Shelby expands his empire."
        assert meta["genres"] == ["Crime", "Drama"]
