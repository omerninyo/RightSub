# 🤖 AI Integration Guide — RightSub

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="AI_INTEGRATION_GUIDE.he.md"><b>עברית</b></a>
</p>

Welcome to the **RightSub** AI Integration Guide for modern autonomous coding assistants and LLMs (**Google Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, **Gemini CLI**, **ChatGPT**, and **Ollama**).

This guide provides:
1. **Copy-Paste Prompt Templates** to give directly to your AI agent.
2. **System Prompt Instructions** to embed in `.cursorrules`, `.claude.md`, or agent system prompts.
3. **100% Free Offline Local Translation** instructions with Ollama.

---

## 📋 Copy-Paste Prompt Templates for AI Agents

Simply copy the relevant prompt and send it to your AI agent (Antigravity, Claude Code, Cursor, ChatGPT):

### Template 1: Plex Hebrew BiDi & Ad Repair
> *"Please use the RightSub CLI to scan and fix all Hebrew subtitle files in [path to folder]. Ensure full Plex/Infuse BiDi compliance, strip advertisement/promo spam, and preserve safe .bak backups."*

### Template 2: Full End-to-End Translation
> *"Please use RightSub to process the video file [path to video]. If English subtitles are missing, extract or transcribe them using quicksubs. Generate translation batches, translate into natural Hebrew preserving character gender and tone, and merge into [Title].he.srt."*

### Template 3: 100% Offline Local Pipeline (Ollama)
> *"Please execute the autonomous RightSub pipeline using a local model: `./rightsub auto "[path to media]" --ollama`. Track the output and report back when the Hebrew subtitle is generated."*

### Template 4: Quality Assurance & Sync Audit
> *"Please run a QA audit comparing [Movie.en.srt] and [Movie.he.srt] using `./rightsub qa`. Verify that there are zero missing cues or timing misalignments."*

---

## 🛠️ System Prompt Instructions for AI Agents (.cursorrules / .claude.md)

Embed the following block into your project rules or agent instructions so your assistant knows how to invoke RightSub natively:

```markdown
# RightSub CLI Agent Instructions

You have access to the `RightSub` CLI tool in this workspace (`./rightsub`).
RightSub is an enterprise-grade subtitle translation, mastering, and BiDi engine for Plex/Infuse.

Key CLI Commands to execute tasks on behalf of the user:
1. Autonomous runner (Recommended for all single files or folders):
   `./rightsub auto "<path_to_video_or_srt_or_dir>"`
   Options:
   - `--ollama`: Perform 100% offline local translation using local Ollama instance.
   - `--dry-run`: Preview without writing changes.

2. Hebrew Plex & BiDi Repair:
   `./rightsub fix-plex "<path>" --in-place --clean-ads --backup`
   Recursively:
   `./rightsub fix-plex "<directory>" --recursive --in-place --clean-ads --backup`

3. Translation Batches & Bible Generation:
   `./rightsub bible "<file.en.srt>" -o "translation_bible.json" --tmdb`
   `./rightsub prompt-gen "<file.en.srt>" -t "<Title>" -b "translation_bible.json" -o "prompts_<Title>"`

4. Merge Translated Batches into Hebrew SRT:
   `./rightsub merge "<file.en.srt>" "prompts_<Title>" -o "<Title>.he.srt"`

5. Quality Assurance (QA):
   `./rightsub qa "<file.en.srt>" "<Title>.he.srt"`

6. Speech-to-Text Transcription (when video lacks subtitles):
   `./rightsub transcribe "<video_path>" -o "<output_dir>"`

Rules:
- Always use `./rightsub auto` when the user requests a simple or hands-off operation.
- Always preserve cue numbers and timestamps when translating subtitle batches.
- When generating Hebrew dialogue, ensure proper BiDi formatting and use Hebrew gershayim (״) for acronyms.
```

---

## 🛑 What Requires AI vs. What Is 100% Local? (The AI Key Decision Matrix)

**99% of subtitle fixing operations in RightSub do NOT use AI at all.** RightSub strictly separates deterministic technical mastering from AI-assisted workflows based on the task and whether the user configured an AI API key:

| Operation | CLI Command | Without AI Key (Default) | With AI Key (`GEMINI_API_KEY` / `--ollama`) |
| :--- | :--- | :---: | :---: |
| **Content-Based Hebrew `.srt` Discovery & Seed-Safe `.he.srt` Creation** | `./rightsub auto` | ✅ **100% Deterministic (0 AI)** — detects Hebrew inside any `.srt`, preserves original `.srt` for torrent seeding, writes `.he.srt` | Same (0 AI for existing Hebrew subtitles) |
| **3-Stage Plex BiDi, UAX #9 Rule N1 & Legacy `Subabi` Un-Flipping** | `./rightsub fix-plex` / `auto` | ✅ **100% Deterministic (0 AI)** | Same (never uses AI) |
| **Encoding Rescue (`CP1255` $\rightarrow$ `UTF-8`) & Homoglyph Repair** | `./rightsub fix-plex` / `auto` | ✅ **100% Deterministic (0 AI)** | Same (never uses AI) |
| **Bilingual Number Un-Flipping (`84` $\rightarrow$ `48` vs `.en.srt`) & Cue Drift Check** | `./rightsub merge` / `polish` | ✅ **100% Deterministic (0 AI)** | Same (runs before any LLM step) |
| **Subtitle Extraction (`FFmpeg`) & Local STT (`quicksubs`)** | `./rightsub extract` / `transcribe` | ✅ **100% Local (0 LLM tokens)** | Same |
| **Framerate (`adjust-fps`), Audio Sync (`audio-sync`) & QA (`qa`)** | `./rightsub qa` | ✅ **100% Deterministic (0 AI)** | Same |
| **Polishing Existing Subtitles (Rare Edge Cases Only)** | `./rightsub polish` | ✅ **Offline Deterministic Canon & Number Pass (0 AI)** | 🧠 **Semantic AI Proofreader** *(Strictly for rare cases: very old, OCR-corrupted, or low-quality machine translations)* |
| **Translating English Media to Hebrew from Scratch** | `./rightsub prompt-gen` / `auto` | Generates prompt batches for your chat agent | 🧠 **Full AI Translation (`EN` $\rightarrow$ `HE`)** |

> [!IMPORTANT]
> **When Do You Actually Need an AI Key for Existing Subtitles?**
> - **Standard Human Subtitles (99% of cases):** Never. Running `rightsub auto` or `rightsub fix-plex` fixes all BiDi, punctuation, encoding, and `Subabi` reversal issues deterministically with **0 tokens** while keeping the original torrent `.srt` untouched.
> - **Rare Legacy / Low-Quality Subtitles (~1% of cases):** Only when an existing subtitle is an old, raw machine translation or a corrupted OCR scan (`PGS`/`VobSub`) suffering from cross-line gender errors or broken syntax should you run `rightsub polish` with an AI key.

---

## 🦙 Local Translation with Ollama (Offline Fallback / Experimental)

> [!WARNING]
> **Technical Analysis: Why Local Open-Weight Models (7B/8B) Fall Short in Hebrew:**
> 
> While RightSub includes local Ollama integration, open-weight consumer models have fundamental architectural bottlenecks with Hebrew:
> 1. **Byte-Fallback Fragmentation**: The tokenizers of Llama 3, Mistral, and similar models lack Hebrew vocabulary representation. Hebrew characters are split into raw UTF-8 bytes (2–3 tokens per character), destroying syntax tracking and slowing generation.
> 2. **Negligible Training Corpus (<0.1%)**: The models lack grasp over Hebrew idioms, slang, and subtitle register, resulting in wooden, literal machine translations.
> 3. **Gender Agreement Collapse**: Hebrew morphology strictly differentiates between masculine ("אתה") and feminine ("את") address across verbs, adjectives, and pronouns. 8B models consistently mix up genders in fast dialogue.
> 
> **Bottom Line:** Local models are suitable only as a fully offline emergency fallback. For broadcast-quality subtitles, **multilingual cloud models (Gemini Flash / Pro, Claude 3.5 Sonnet, GPT-4o) are strictly recommended**.

### Running Local Translation (Offline Fallback):
1. Ensure Ollama is running (`ollama serve`).
2. Run translation on a prepared prompts folder:
   ```bash
   ./rightsub translate-ollama "prompts_Movie" --en-srt "Movie.en.srt" -o "Movie.he.srt"
   ```

---

## 🛠️ Step-by-Step Instructions for AI Assistants & 1-Command MCP Setup

### 0. Native MCP Server Auto-Registration (`rightsub mcp --install` — Recommended)
Instead of copying prompt files manually, connect RightSub's native **Model Context Protocol (MCP)** server directly to all your AI agents (**Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf**, and **Claude Code**) with a single command:
```bash
# Auto-detect and register RightSub in all installed AI agents:
rightsub mcp --install

# Or register in a specific agent:
rightsub mcp --install --agent claude
rightsub mcp --install --agent cursor

# Check registration status across all agents:
rightsub mcp --status
```
Once registered, your AI assistant natively receives 8 tools (`inspect_media`, `fix_plex_subtitles`, `extract_subtitles`, `prepare_translation`, `merge_and_master`, `polish_subtitles`, `audit_subtitles_qa`, `transcribe_audio`) and can inspect, fix, or translate any media folder directly from chat.

### 1. Google Antigravity (Default Multi-Agent Orchestrator)
Simply request:
> *"Run `./rightsub auto` on my video file, prepare translation batches, spawn subagents in parallel to translate them, and merge into the final subtitle."*

### 2. Claude Code CLI (Anthropic)
Inside your terminal running `claude`:
> *"Read `prompts_Movie/batch_01_prompt.txt` and translate `batch_01_input.json` into `batch_01_translated.json` maintaining exact JSON structure."*

### 3. Cursor & Windsurf
Open the project in Cursor, open Composer (`Cmd+I`):
> *"Read the batch files in `prompts_Movie`, translate each into `batch_XX_translated.json`, and run `./rightsub merge` when complete."*

---

## 🎯 The Golden Rule of Merging

Regardless of which AI model translates the text, **the final merge is always performed locally with 100% mathematical precision:**

```bash
./rightsub merge "Movie.en.srt" "prompts_Movie" -o "Movie.he.srt"
./rightsub qa "Movie.en.srt" "Movie.he.srt"
```
