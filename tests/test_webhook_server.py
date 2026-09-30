#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_webhook_server.py
-----------------------
Unit and integration tests for RightSub Webhook Daemon (`scripts/21_webhook_server.py`).
Tests path translation, Sonarr/Radarr/Bazarr payload parsing, companion subtitle discovery,
and live HTTP daemon requests.
"""

import sys
import json
import time
import threading
import urllib.request
import urllib.error
import pytest
from pathlib import Path
from http.server import ThreadingHTTPServer

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import importlib
srv = importlib.import_module("21_webhook_server")


class TestPathMapping:
    def test_parse_path_map_empty(self):
        assert srv.parse_path_map("") == []
        assert srv.parse_path_map(None) == []

    def test_parse_path_map_single(self):
        result = srv.parse_path_map("/data/media:/media")
        assert result == [("/data/media", "/media")]

    def test_parse_path_map_multiple_and_trailing_slashes(self):
        raw = "/data/media/:/media/,/downloads/:/mnt/downloads/"
        result = srv.parse_path_map(raw)
        assert result == [
            ("/data/media", "/media"),
            ("/downloads", "/mnt/downloads")
        ]

    def test_parse_path_map_windows_paths(self):
        raw = r"C:\data\media:D:\media"
        result = srv.parse_path_map(raw)
        assert len(result) == 1
        assert result[0] == ("C:/data/media", "D:/media")

    def test_translate_path(self):
        pmap = [("/data/media", "/media"), ("/downloads", "/mnt/downloads")]
        
        # Exact prefix match
        res = srv.translate_path("/data/media/tv/Show/S01E01.mkv", pmap)
        assert str(res).replace("\\", "/") == "/media/tv/Show/S01E01.mkv"

        # Backslash handling in incoming payload
        res2 = srv.translate_path(r"/data/media\movies\Movie (2020)\movie.mkv", pmap)
        assert str(res2).replace("\\", "/") == "/media/movies/Movie (2020)/movie.mkv"

        # No match
        res3 = srv.translate_path("/var/log/syslog", pmap)
        assert str(res3).replace("\\", "/") == "/var/log/syslog"

        # Empty
        assert srv.translate_path("", pmap) == Path("")


class TestSubtitleDiscoveryAndMastering:
    def test_is_hebrew_content_sample(self, tmp_path):
        he_file = tmp_path / "test_he.srt"
        he_file.write_text("1\n00:00:01,000 --> 00:00:02,000\nשלום עולם!\n", encoding="utf-8")
        assert srv.is_hebrew_content_sample(he_file) is True

        en_file = tmp_path / "test_en.srt"
        en_file.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello World!\n", encoding="utf-8")
        assert srv.is_hebrew_content_sample(en_file) is False

        non_existent = tmp_path / "missing.srt"
        assert srv.is_hebrew_content_sample(non_existent) is False

    def test_discover_hebrew_subtitles_for_video(self, tmp_path):
        video = tmp_path / "Boston Legal - S01E01.mkv"
        video.touch()

        # Create companion files
        sub_he = tmp_path / "Boston Legal - S01E01.he.srt"
        sub_he.write_text("1\n00:00:01,000 --> 00:00:02,000\nשלום דני!\n", encoding="utf-8")

        sub_en = tmp_path / "Boston Legal - S01E01.en.srt"
        sub_en.write_text("1\n00:00:01,000 --> 00:00:02,000\nHello Denny!\n", encoding="utf-8")

        discovered = srv.discover_hebrew_subtitles_for_video(video)
        assert sub_he in discovered
        assert sub_en not in discovered

    def test_master_subtitle_file_in_place(self, tmp_path):
        sub = tmp_path / "test.he.srt"
        sub.write_text("1\n00:00:01,000 --> 00:00:02,000\nשלום חברים...\n", encoding="utf-8")

        res = srv.master_subtitle_file(sub, in_place=True, seed_safe=False, clean_ads=True)
        assert res["status"] in ("fixed", "already compliant")
        assert sub.exists()

    def test_master_subtitle_file_seed_safe(self, tmp_path):
        # When seed_safe=True and original file is test.srt, should create test.he.srt
        sub = tmp_path / "torrent_movie.srt"
        sub.write_text("1\n00:00:01,000 --> 00:00:02,000\nשלום עולם!\n", encoding="utf-8")

        res = srv.master_subtitle_file(sub, in_place=False, seed_safe=True)
        expected_output = tmp_path / "torrent_movie.he.srt"
        assert expected_output.exists()
        assert res["file"] == str(expected_output)


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """
    Spins up a real ThreadingHTTPServer on an ephemeral port for HTTP tests.
    """
    media_dir = tmp_path_factory.mktemp("media")
    virtual_prefix = "/remote/media"
    path_map = [(virtual_prefix, str(media_dir).replace("\\", "/"))]

    srv.WebhookRequestHandler.server_options = {
        "in_place": True,
        "seed_safe": False,
        "clean_ads": True,
        "backup": False,
        "dry_run": False
    }
    srv.WebhookRequestHandler.path_map = path_map

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.WebhookRequestHandler)
    port = httpd.server_address[1]
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    yield {
        "url": f"http://127.0.0.1:{port}",
        "media_dir": media_dir,
        "virtual_prefix": virtual_prefix
    }

    httpd.shutdown()
    httpd.server_close()


class TestLiveWebhookDaemon:
    def _send_post(self, url, payload):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_health_check(self, live_server):
        with urllib.request.urlopen(f"{live_server['url']}/health") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "healthy"
            assert data["version"] == "1.4.0"
            assert "uptime_seconds" in data
            assert "/webhook/sonarr" in data["endpoints"]

    def test_root_route_health(self, live_server):
        with urllib.request.urlopen(f"{live_server['url']}/") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "healthy"

    def test_404_not_found(self, live_server):
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"{live_server['url']}/unknown_route")
        assert exc_info.value.code == 404

    def test_sonarr_test_ping(self, live_server):
        status, data = self._send_post(
            f"{live_server['url']}/webhook/sonarr",
            {"eventType": "Test"}
        )
        assert status == 200
        assert data["status"] == "ok"
        assert data["event"] == "Test"

    def test_sonarr_download_event(self, live_server):
        # Create a mock video and companion Hebrew subtitle in mapped directory
        media_dir = live_server["media_dir"]
        vid = media_dir / "Boston.Legal.S01E01.mkv"
        vid.touch()
        sub = media_dir / "Boston.Legal.S01E01.he.srt"
        sub.write_text("1\n00:00:01,000 --> 00:00:02,000\nדני קריין: שלום לכולם!\n", encoding="utf-8")

        # Sonarr sends virtual path
        virtual_path = f"{live_server['virtual_prefix']}/Boston.Legal.S01E01.mkv"
        payload = {
            "eventType": "Download",
            "series": {"title": "Boston Legal"},
            "episodeFile": {"path": virtual_path}
        }

        status, data = self._send_post(f"{live_server['url']}/webhook/sonarr", payload)
        assert status == 200
        assert data["status"] == "ok"
        assert data["processed_items"] >= 1
        assert data["results"][0]["status"] in ("fixed", "already compliant")

    def test_radarr_test_ping(self, live_server):
        status, data = self._send_post(
            f"{live_server['url']}/webhook/radarr",
            {"eventType": "Test"}
        )
        assert status == 200
        assert data["status"] == "ok"

    def test_radarr_movie_imported(self, live_server):
        media_dir = live_server["media_dir"]
        mov = media_dir / "Gladiator (2000).mkv"
        mov.touch()
        sub = media_dir / "Gladiator (2000).he.srt"
        sub.write_text("1\n00:00:05,000 --> 00:00:07,000\nבכוח ובכבוד!\n", encoding="utf-8")

        virtual_path = f"{live_server['virtual_prefix']}/Gladiator (2000).mkv"
        payload = {
            "eventType": "MovieFileImported",
            "movie": {"title": "Gladiator"},
            "movieFile": {"path": virtual_path}
        }

        status, data = self._send_post(f"{live_server['url']}/webhook/radarr", payload)
        assert status == 200
        assert data["status"] == "ok"
        assert data["processed_items"] == 1

    def test_bazarr_test_ping(self, live_server):
        status, data = self._send_post(
            f"{live_server['url']}/webhook/bazarr",
            {"event": "test"}
        )
        assert status == 200
        assert data["status"] == "ok"

    def test_bazarr_hebrew_download(self, live_server):
        media_dir = live_server["media_dir"]
        sub = media_dir / "Show.S02E05.he.srt"
        sub.write_text("1\n00:00:01,000 --> 00:00:02,000\nתרגום: סאבסנטר\nשלום!\n", encoding="utf-8")

        virtual_path = f"{live_server['virtual_prefix']}/Show.S02E05.he.srt"
        payload = {
            "event": "download",
            "subtitle": {
                "path": virtual_path,
                "language": "he"
            }
        }

        status, data = self._send_post(f"{live_server['url']}/webhook/bazarr", payload)
        assert status == 200
        assert data["status"] == "ok"
        assert data["result"]["status"] in ("fixed", "already compliant")

    def test_bazarr_skips_non_hebrew(self, live_server):
        payload = {
            "event": "download",
            "subtitle": {
                "path": "/media/Show.S01E01.fr.srt",
                "language": "fr"
            }
        }
        status, data = self._send_post(f"{live_server['url']}/webhook/bazarr", payload)
        assert status == 200
        assert data["status"] == "skipped"
        assert "fr" in data["message"]

    def test_generic_webhook(self, live_server):
        media_dir = live_server["media_dir"]
        sub = media_dir / "generic_test.he.srt"
        sub.write_text("1\n00:00:01,000 --> 00:00:02,000\nבדיקה כללית.\n", encoding="utf-8")

        virtual_path = f"{live_server['virtual_prefix']}/generic_test.he.srt"
        status, data = self._send_post(
            f"{live_server['url']}/webhook/generic",
            {"path": virtual_path}
        )
        assert status == 200
        assert data["status"] == "ok"
        assert data["processed_items"] == 1

    def test_generic_missing_path(self, live_server):
        req = urllib.request.Request(
            f"{live_server['url']}/webhook/generic",
            data=json.dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)
        assert exc_info.value.code == 400
