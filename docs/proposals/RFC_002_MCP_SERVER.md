# 🔌 RFC 002: RightSub Native Model Context Protocol (MCP) Server

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="RFC_002_MCP_SERVER.he.md"><b>עברית</b></a>
</p>

This Request for Comments (RFC) specifies the architectural design, protocol interfaces, tool schemas, and integration strategy for turning **RightSub** into an official **Model Context Protocol (MCP) Server**.

The objective is to expose RightSub's core media discovery, FFmpeg stream extraction, SubRefine BiDi processing, and translation orchestrator natively to leading AI agents and desktop environments (e.g. **Claude Desktop**, **Antigravity**, **Cursor**, **Windsurf**, and **ChatGPT**).

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

## 3. Proposed MCP Toolset Schema

### Tool 1: `rightsub_inspect_media`
- **Description:** Probes a video file, subtitle file, or directory and returns structured media information.
- **Arguments:**
  - `path` (string, required): Absolute filesystem path to media container or subtitle.
- **Returns:**
  - Embedded subtitle tracks (languages, codecs, track indices).
  - External companion subtitle presence and encoding (UTF-8, CP1255).
  - BiDi RLM compliance status.

### Tool 2: `rightsub_extract_subtitles`
- **Description:** Extracts embedded subtitle stream to standalone `.srt` file.
- **Arguments:**
  - `video_path` (string, required): Path to video container.
  - `lang` (string, default: `"eng"`): Preferred language code.
  - `track_index` (integer, optional): Specific stream index.

### Tool 3: `rightsub_fix_plex_bidi`
- **Description:** Runs SubRefine engine to inject Plex/Infuse RLM marks, strip ads, and normalize character encodings.
- **Arguments:**
  - `subtitle_path` (string, required): Path to subtitle file.
  - `in_place` (boolean, default: `false`): Overwrite in-place with `.bak` safety.

### Tool 4: `rightsub_polish_cues`
- **Description:** Reviews and modernizes a batch of Hebrew cues against English master text using franchise domain rules.
- **Arguments:**
  - `english_cues` (array of objects, required): Master English dialogue cues.
  - `hebrew_cues` (array of objects, required): Hebrew translation cues.
  - `domain` (string, optional): Domain pack (`"sci_fi"`, `"legal"`, `"military"`, etc.).

---

## 4. Claude Desktop / Antigravity Configuration Example

Add to `claude_desktop_config.json` or Antigravity MCP settings:

```json
{
  "mcpServers": {
    "rightsub": {
      "command": "rightsub",
      "args": ["mcp"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

---

## 5. Target Release & Tracking

- **Target Release:** Version 1.5.0
- **Milestone:** `v1.5.0 — Agentic Subtitle Protocol & MCP Server`
