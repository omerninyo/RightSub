# 🔌 RFC 002: RightSub Native Model Context Protocol (MCP) Server (`rightsub mcp`)

> **Status:** ✅ **Shipped in Production (`v1.5.0`)** — Implemented in [`scripts/23_mcp_server.py`](file:///Volumes/Other/Antigravity/RightSub/scripts/23_mcp_server.py) and [`rightsub.py`](file:///Volumes/Other/Antigravity/RightSub/rightsub.py). Verified by [`tests/test_mcp_server.py`](file:///Volumes/Other/Antigravity/RightSub/tests/test_mcp_server.py).

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="RFC_002_MCP_SERVER.he.md"><b>עברית</b></a>
</p>

This document specifies the architectural design, protocol interfaces, tool schemas, and multi-agent auto-installer for **RightSub's official Model Context Protocol (MCP) Server** (`v1.5.0`).

The MCP server exposes RightSub's core media discovery, FFmpeg stream extraction, SubRefine BiDi processing, semantic polish engine, and translation orchestrator natively to leading AI agents and desktop environments (**Google Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf**, and **Claude Code**).

---

## 1. Engineering Motivation & Objectives

1. **Natural Language as the Ultimate Media UI:**
   - Rather than forcing non-technical users to master CLI flags or building a cumbersome cross-platform GUI, users interact via conversational dialog: *"I downloaded a new film, inspect its subtitle tracks, fix reversed punctuation, and polish it against canon lore."*
2. **Local-First Media Processing (Zero Bandwidth Waste):**
   - Media containers are multi-gigabyte files (2 GB to 30 GB) that cannot and should not be uploaded over the network.
   - The MCP server runs locally over `stdio`, executing FFmpeg on local disks. Track extraction completes in ~0.2 seconds, and only tiny subtitle text payloads (~50 KB) are shared with the LLM.
3. **Transparent Credential Management:**
   - Users interacting through their favorite desktop AI client leverage the client's existing LLM subscription without needing separate API key management.
4. **Agentic Subtitle Quality Control:**
   - AI agents can invoke `inspect_media`, analyze cues, detect franchise lore anomalies, and review diffs autonomously.

---

## 2. Transport & Protocol Architecture

- **Protocol Standard:** Anthropic Model Context Protocol (MCP) Specification.
- **Transport Mechanism:** `stdio` (Standard Input / Standard Output) exchanging JSON-RPC 2.0 messages.
- **Security Boundaries:**
  - Sandboxed subprocess under the host AI application.
  - Strict filesystem scoping restricted to media directories.
  - Read-only protection on video containers (`.mkv`, `.mp4`).
- **Invocation Command:**
  ```bash
  rightsub mcp
  # or via python:
  python3 -m scripts.mcp_server
  ```

---

## 3. Shipped MCP Toolset Schema (8 Native Tools)

1. **`inspect_media(path)`**: Probes a video file, subtitle file, or directory and returns embedded tracks, companion `.srt` encodings, Hebrew ratios, BiDi compliance status, and recommended next steps.
2. **`fix_plex_subtitles(path, in_place=True, keep_sdh=False)`**: Runs the 0-token `SubRefine` engine (`Windows-1255` recovery, 18-pattern visual un-flipping, UAX #9 Rule N1 `RLM` wrapping, ad/SDH cleaning, and Seed-Safe `.srt` $\rightarrow$ `.he.srt` duplication).
3. **`extract_subtitles(video_path, lang="eng", output_path=None)`**: Extracts embedded text subtitle tracks from `.mkv`/`.mp4` containers via `ffmpeg`.
4. **`prepare_translation(srt_path, title="", is_tv=False, enrich_tmdb=True)`**: Generates `translation_bible.json` (with TMDb cast genders when `TMDB_API_KEY` is present) and splits the English `.srt` into ~210-cue JSON batches with sliding context overlap.
5. **`merge_and_master(en_srt_path, translated_batches_dir, output_path=None)`**: Validates 1:1 cue parity, checks for cue drift (`validate_anchor_alignment`), injects `RLM` marks, and writes the final `.he.srt`.
6. **`polish_subtitles(he_srt_path, en_srt_path="", diff_only=False, use_gemini=False)`**: Executes the 0-token deterministic franchise canon & bilingual 2-digit number un-flipping pass (`cross_check_bilingual_numbers`), plus optional Gemini AI proofreading.
7. **`audit_subtitles_qa(en_srt_path, he_srt_path, strict_gender=True)`**: Runs the Red Team QA suite (line count parity, timestamp drift, foreign homoglyphs, vocative & intra-line gender mismatches).
8. **`transcribe_audio(video_path, lang="en")`**: Invokes on-device Speech-to-Text (`quicksubs` — Apple SpeechAnalyzer on Apple Silicon or Whisper) when no embedded subtitle tracks exist.

---

## 4. Multi-Agent Auto-Installer & Protocol Hardening (`v1.5.0`)

Instead of editing JSON config files manually, run:
```bash
rightsub mcp --install      # Auto-registers in Antigravity, Claude Desktop, Cursor, Windsurf & Claude Code
rightsub mcp --status       # Displays registration status across all detected AI clients
rightsub mcp --print-config # Prints the exact JSON block with absolute Python & script paths
rightsub mcp --uninstall    # Cleanly removes RightSub from agent configs
```

### Red Team Safeguards Implemented in `scripts/23_mcp_server.py`:
- **Strict `stdout` Isolation (`_isolated_stdio`)**: Redirects Python `sys.stdout` to `sys.stderr` during tool execution so internal `print()` calls or `ffmpeg` output never corrupt the JSON-RPC 2.0 wire stream.
- **Dual-Mode Wire Framing**: Automatically detects and replies in either newline-delimited JSON (MCP stdio standard) or LSP-style `Content-Length` headers.
- **GUI Subprocess `PATH` Injection**: Injects `/opt/homebrew/bin`, `/usr/local/bin`, and `~/.local/bin` into the MCP `env` block so GUI clients (Claude Desktop, Cursor) always locate `ffmpeg` and `python3`.

---

## 5. Release Status

- **Status:** ✅ **Shipped in Version 1.5.0**
- **Milestone:** `v1.5.0 — Agentic Subtitle Protocol, Interactive TUI & Turnkey Setup`
