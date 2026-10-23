#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mcp_server.py
------------------
Unit and Red-Team integration tests for RightSub Native MCP Server & Multi-Agent Auto-Installer
(`scripts/23_mcp_server.py`).
"""

import io
import sys
import json
import pytest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import importlib
mcp_mod = importlib.import_module("23_mcp_server")


class TestMCPProtocolAndRedTeamIsolation:
    def test_initialize_and_notification_handling(self):
        # 1. Standard initialize request
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "antigravity-test", "version": "1.0"}
            }
        }
        resp = mcp_mod.handle_jsonrpc_message(init_req)
        assert resp is not None
        assert resp["id"] == 1
        assert resp["result"]["protocolVersion"] == "2024-11-05"
        assert resp["result"]["serverInfo"]["name"] == "rightsub"
        assert resp["result"]["serverInfo"]["version"] == "1.5.0"

        # 2. Red Team #2: Notification (no "id" field) MUST return None
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        assert mcp_mod.handle_jsonrpc_message(notif) is None

    def test_tools_list_exposes_all_core_tools(self):
        resp = mcp_mod.handle_jsonrpc_message({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })
        tools = resp["result"]["tools"]
        names = {t["name"] for t in tools}
        expected = {
            "inspect_media",
            "fix_plex_subtitles",
            "extract_subtitles",
            "prepare_translation",
            "merge_and_master",
            "polish_subtitles",
            "audit_subtitles_qa",
            "transcribe_audio",
        }
        assert expected.issubset(names)
        for t in tools:
            assert "inputSchema" in t
            assert t["inputSchema"]["type"] == "object"

    def test_newline_delimited_stdio_and_strict_stdout_isolation(self, tmp_path):
        """
        Red Team #1: Verify that calling `inspect_media`, `fix_plex_subtitles`, `polish_subtitles`,
        and `audit_subtitles_qa` over stdio NEVER leaks raw `print()` lines onto the wire stream,
        and preserves Seed-Safe torrent protection on plain `.srt` files.
        """
        plain_he = tmp_path / "Episode.S01E01.srt"
        original_content = "1\n00:00:01,000 --> 00:00:03,000\n.שלום עולם, היו 84 תיקים\n"
        plain_he.write_text(original_content, encoding="utf-8")

        en_srt = tmp_path / "Episode.S01E01.en.srt"
        en_srt.write_text("1\n00:00:01,000 --> 00:00:03,000\nHello world, there were 48 cases.\n", encoding="utf-8")

        requests = [
            {"jsonrpc": "2.0", "id": 10, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {"name": "inspect_media", "arguments": {"path": str(tmp_path)}}
            },
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {"name": "fix_plex_subtitles", "arguments": {"path": str(plain_he)}}
            },
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "polish_subtitles",
                    "arguments": {
                        "target_path": str(plain_he),
                        "en_path": str(en_srt),
                        "offline_canon_only": True,
                        "in_place": True
                    }
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {
                    "name": "audit_subtitles_qa",
                    "arguments": {
                        "en_srt_path": str(en_srt),
                        "he_srt_path": str(tmp_path / "Episode.S01E01.he.srt")
                    }
                }
            }
        ]

        in_bytes = "\n".join(json.dumps(r, ensure_ascii=False) for r in requests).encode("utf-8") + b"\n"
        in_stream = io.BytesIO(in_bytes)
        out_stream = io.BytesIO()

        rc = mcp_mod.serve_stdio(in_stream=in_stream, out_stream=out_stream)
        assert rc == 0

        out_lines = [line for line in out_stream.getvalue().decode("utf-8").splitlines() if line.strip()]
        # 5 requests had "id" (1 notification had no "id" and must NOT produce an output line)
        assert len(out_lines) == 5

        parsed_responses = [json.loads(line) for line in out_lines]
        assert [r["id"] for r in parsed_responses] == [10, 11, 12, 13, 14]

        # Verify Seed-Safe torrent protection: plain .srt untouched, .he.srt created and fixed
        assert plain_he.read_text(encoding="utf-8") == original_content
        he_master = tmp_path / "Episode.S01E01.he.srt"
        assert he_master.is_file()
        master_text = he_master.read_text(encoding="utf-8")
        assert "\u200f" in master_text
        assert "48" in master_text

    def test_content_length_lsp_framing_mode(self):
        """Red Team #2: Verify Content-Length header framing works identically to newline framing."""
        req = {"jsonrpc": "2.0", "id": 99, "method": "ping"}
        body = json.dumps(req).encode("utf-8")
        wire = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body

        in_stream = io.BytesIO(wire)
        out_stream = io.BytesIO()
        mcp_mod.serve_stdio(in_stream=in_stream, out_stream=out_stream)

        raw_reply = out_stream.getvalue()
        assert raw_reply.startswith(b"Content-Length:")
        _, json_part = raw_reply.split(b"\r\n\r\n", 1)
        parsed = json.loads(json_part.decode("utf-8"))
        assert parsed["id"] == 99
        assert parsed["result"] == {}


class TestMultiAgentMCPInstaller:
    def test_install_and_uninstall_preserves_existing_servers_and_creates_backup(self, tmp_path):
        """
        Red Team #4: Ensure installing `rightsub` into an agent config file preserves existing
        MCP servers, creates a `.bak` backup, and cleanly removes only `rightsub` on uninstall.
        """
        antigravity_dir = tmp_path / ".gemini" / "antigravity"
        antigravity_dir.mkdir(parents=True)
        cfg_file = antigravity_dir / "mcp_config.json"

        existing_config = {
            "mcpServers": {
                "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
            },
            "customSetting": True
        }
        cfg_file.write_text(json.dumps(existing_config, indent=2), encoding="utf-8")

        # 1. Install across detected agents in simulated home
        res = mcp_mod.install_mcp_for_agents(target_agent="all", home_dir=tmp_path)
        assert any(r["agent"] == "antigravity" and r["success"] for r in res["results"])

        # Verify .bak backup was created
        bak_file = cfg_file.with_suffix(".json.bak")
        assert bak_file.is_file()
        assert json.loads(bak_file.read_text(encoding="utf-8")) == existing_config

        # Verify merged config preserves 'github' and 'customSetting' and adds 'rightsub'
        merged = json.loads(cfg_file.read_text(encoding="utf-8"))
        assert merged["customSetting"] is True
        assert "github" in merged["mcpServers"]
        assert "rightsub" in merged["mcpServers"]
        assert merged["mcpServers"]["rightsub"]["args"][-1] == "mcp"
        assert "PATH" in merged["mcpServers"]["rightsub"]["env"]

        # Verify status check
        statuses = mcp_mod.get_mcp_registration_status(home_dir=tmp_path)
        ag_status = next(s for s in statuses if s["agent"] == "antigravity")
        assert ag_status["registered"] is True

        # 2. Uninstall removes 'rightsub' while keeping 'github'
        mcp_mod.install_mcp_for_agents(target_agent="antigravity", home_dir=tmp_path, remove=True)
        after_uninstall = json.loads(cfg_file.read_text(encoding="utf-8"))
        assert "rightsub" not in after_uninstall["mcpServers"]
        assert "github" in after_uninstall["mcpServers"]

    def test_refuses_to_overwrite_malformed_json(self, tmp_path):
        """Red Team #4: If the user's existing config file has broken JSON syntax, refuse to overwrite it."""
        broken_cfg = tmp_path / "broken_mcp.json"
        broken_text = "{ \"mcpServers\": { broken json "
        broken_cfg.write_text(broken_text, encoding="utf-8")

        ok, msg = mcp_mod.update_agent_config_file(broken_cfg)
        assert ok is False
        assert "malformed" in msg.lower()
        assert broken_cfg.read_text(encoding="utf-8") == broken_text
