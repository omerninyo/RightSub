# 🚀 What's New in RightSub — Product & Milestone Releases

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="WHATS_NEW.he.md"><b>עברית</b></a>
</p>

This document tracks **major milestone releases** and product capabilities in RightSub. Unlike dry git commit logs, these notes focus on practical user value, media server improvements, and workflow enhancements.

---

## 🌟 Version 1.5.0 — Native MCP Server (`rightsub mcp`), Multi-Agent Auto-Installer & Interactive Mastering Suite (`wizard` / `setup`)

> **Release Date:** October 2026  
> **Milestone Focus:** Delivering the complete `v1.4.0` and `v1.5.0` roadmap in a unified zero-dependency package: Native Model Context Protocol (`MCP`) Server over `stdio`, 1-command auto-registration across all major AI agents (`Antigravity`, `Claude Desktop`, `Cursor`, `Windsurf`, `Claude Code`), Interactive Terminal/CMD Mastering Wizard (`rightsub` / `rightsub wizard`), Line-by-Line Polish Diff Reviewer (`rightsub polish --interactive`), and Automated Downloader Hook & Service Generator (`rightsub setup` / `rightsub config --install-hooks`).

### 🎯 Key Highlights
- **Native Model Context Protocol Server (`rightsub mcp` — `scripts/23_mcp_server.py`):** Zero-dependency JSON-RPC 2.0 server over `stdio` supporting both standard MCP newline-delimited JSON and LSP-style `Content-Length` headers, with strict `stdout` capture isolation so tool logs never corrupt the wire stream. Exposes 8 tools (`inspect_media`, `fix_plex_subtitles`, `extract_subtitles`, `prepare_translation`, `merge_and_master`, `polish_subtitles`, `audit_subtitles_qa`, `transcribe_audio`).
- **1-Command Multi-Agent Auto-Installer (`rightsub mcp --install`):** Automatically detects and registers `rightsub` into **Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf**, and **Claude Code** with exact absolute paths (`sys.executable` + `rightsub.py`), full `PATH` environment injection for GUI apps, `.bak` backups, and preservation of all existing MCP servers.
- **Interactive Terminal & Windows CMD Mastering Wizard (`rightsub` / `rightsub wizard` — `scripts/22_interactive_wizard.py`):** Running `rightsub` with no arguments in an interactive terminal launches a bilingual menu with cross-platform Drag & Drop path normalization (macOS Finder backslash escapes, Windows Explorer quotes, PowerShell `& '...'`) and a built-in terminal file browser.
- **Interactive Line-by-Line Diff Reviewer (`rightsub polish --interactive` / `-i`):** Inspect proposed subtitle edits one-by-one (`[Y] Approve`, `[N] Reject`, `[E] Edit manually`, `[A] Approve All`, `[R] Reject Remaining`) with `Ctrl+C` partial-save recovery.
- **End-to-End Setup, Downloader Hooks & Background Service Wizard (`rightsub setup` / `rightsub config --install-hooks` / `--install-service`):** Generates ready-to-run `qBittorrent` (`.sh`/`.bat`) and `Transmission` hook scripts, optional live `Sonarr`/`Radarr` REST API webhook registration, and background service definitions (`launchd` on macOS, `systemd --user` on Linux, `schtasks` on Windows).
- **Bilingual Web App, Client-Side `.srt` Master & Built-in Local Web UI (`site/` & `rightsub serve`):** 100% client-side JavaScript port of the `SubRefine` engine (`site/subrefine.js`) with byte-level `CP1255` detection, 18-pattern `Subabi` un-flipping, bilingual `HE + EN` number cross-checking, UAX #9 Rule N1 `RLM` wrapping, Seed-Safe `.he.srt` naming, an interactive Plex / Apple TV screen simulator, and automatic serving on `http://localhost:8775/ui` via `rightsub serve`.

---

## 🌟 Version 1.3.3 — Deterministic vs. AI Decision Matrix, Seed-Safe Plain `.srt` Discovery & Bilingual Number Un-Flipping

> **Release Date:** October 2026  
> **Milestone Focus:** Clear architectural separation between 0-token deterministic subtitle mastering and rare-case AI semantic polishing, content-based Hebrew `.srt` discovery with Seed-Safe `.he.srt` torrent protection across `auto` and `polish`, deterministic bilingual number un-flipping (`84` $\rightarrow$ `48`), Georgian homoglyph repair (`דეייט` $\rightarrow$ `דייט`), and 100% cue-drift un-shifting across all 101 episodes of *Boston Legal*.

### 🎯 Key Highlights
- **Deterministic (0-Token) vs. AI-Assisted Decision Matrix:** Documented and enforced the strict boundary between technical subtitle mastering (**0 AI tokens** for 99% of existing human Hebrew subtitles via `fix-plex` and `auto`) and LLM-based semantic proofreading (`rightsub polish`, reserved only for rare edge cases such as legacy amateur drafts, OCR-corrupted releases, or unmarked cross-cue gender errors).
- **Content-Based Hebrew `.srt` Discovery & Seed-Safe Torrent Protection (`.srt` $\rightarrow$ `.he.srt`):** Both `rightsub auto` and `rightsub polish --in-place` detect any `.srt` file containing Hebrew text (`Movie.srt`, `Movie.heb.srt`, `Subs/*.srt`), preserve the original file 100% untouched on disk for torrent seeding (`qBittorrent` / `Transmission`), and output the mastered subtitle separately as `<stem>.he.srt` without polluting `Subs/` subdirectories.
- **Deterministic Bilingual Number Un-Flipping (`cross_check_bilingual_numbers`):** Automatically un-flips 2-digit numbers reversed by legacy `Subabi` visual-flipping scripts (`84` $\rightarrow$ `48`) at **0 token cost** whenever the un-flipped number is verified in the matching `.en.srt` cue (as digits `48` or English number words `forty-eight`).
- **Georgian Homoglyph Repair:** Added deterministic replacement for Georgian `ე` (`U+10D4`) inside Hebrew words (`דეייט` $\rightarrow$ `דייט`).
- **101-Episode *Boston Legal* Dataset Mastering & Un-Shifting:** Un-shifted localized 1-cue drift windows in `.bak.v25` for `S02E09`, `S03E12`, and `S04E05`, achieving `0` shifted windows and `0` vocative/morphological gender errors across all 101 episodes (`88,622` cues).

---

## 🌟 Version 1.3.2 — 3-Stage Canonical BiDi & Un-Flipping Engine, UAX #9 Rule N1 Wrapping & Cue Drift Guard

> **Release Date:** October 2026  
> **Milestone Focus:** Corpus-benchmarked (`20,299` `.srt` files / `15,630,175` Hebrew lines) 3-Stage Canonical BiDi & Un-Flipping Engine, UAX #9 Rule N1 trailing `RLM` placement, homoglyph-conditional final-letter safety, and 25-cue window `Cue Drift` detection.

### 🎯 Key Highlights
- **3-Stage Canonical BiDi & Un-Flipping Engine (`07_fix_plex_punctuation.py`):** Benchmarked across **20,299 subtitle files (`14,752` Hebrew files / `15,630,175` Hebrew lines)**. Combines file-level flip polarity detection (`detect_file_flip_polarity`), deterministic un-flipping of 18 legacy visual-flipping patterns (`canonicalize_visual_flipped_line`), and **UAX #9 Rule N1** wrapping (`\u200F + Logical Core + \u200F` with trailing `RLM` placed **after** trailing punctuation).
- **Homoglyph-Conditional Final-Letter Safety:** Runs `normalize_final_letters` strictly when a Cyrillic or Arabic homoglyph was actually replaced in the line, preventing corruption of Hebrew hesitation interjections (`אממ`, `הממ`, `מממ`) and loanwords (`טרמפ`, `ג'יפ`), while normalizing vocalized `אִמם` ("their mother") to `אימם`.
- **Cue Drift Anchor Validation (`validate_anchor_alignment`):** Detects silent `+1`/`-1` cue shifts caused by LLM line merges/splits using 25-cue sliding windows over question marks (`?`), musical notes (`♪`), and numbers.
- **Expanded Bidirectional Vocative & Morphological QA (`08_quality_assurance.py`):** Detects both leading vocatives (`"שירלי, אתה מוכן?"`) and trailing vocatives (`"תן לי לומר לך משהו, שירלי."`, `"אל תגידי לי להירגע, דני!"`), plus internal morphological contradictions (`"אתה ובעלך"`).

---

## 🌟 Version 1.3.0 — Semantic AI Proofreading, Homebrew Universal Tap & Interactive Onboarding

> **Release Date:** September 2026  
> **Milestone Focus:** Semantic AI subtitle QC (`polish`), official Homebrew tap distribution with instant universal bottles, 10-second credential onboarding (`config`), and proactive system diagnostics (`doctor`).

### 🎯 Key Highlights
- **Semantic AI Polish & Subtitle Quality Control (`rightsub polish`):** Autonomous proofreading engine for existing subtitles. Combines zero-token deterministic franchise canon rules with bilingual cue alignment, Markdown diff reporting, and seed-safe protection.
- **Hierarchical Domain Knowledge Engine & 3-Tier Classification:** Intelligent context detector operating across 3 tiers (Tier 1: TMDb genres & translation bibles; Tier 2: Franchise/title patterns; Tier 3: Offline lexical cue fingerprinting). Features genre packs (`SCI_FI`, `MILITARY`, `LEGAL`, `MEDICAL`, `FANTASY`, `UNIVERSAL_IDIOMS`) and **Bilingual Anchor Validation** to eliminate cross-genre false positives.
- **Split-Cue Partitioning & Forward Anticipation Drift Guard:** Advanced cue alignment with `split_part` markers and a real-time drift guard preventing the LLM from collapsing split cues or leaking future dialogue lines ahead of time, ensuring 100% dialogue synchronization.
- **Network Storage (SMB/NAS) Timestamp Synchronization:** Explicit filesystem metadata flushing (`os.utime`) on all mastered subtitles, diff audit reports, and backups, preventing macOS SMB clients from falling back to Apple's CoreFoundation epoch (`2001-01-01`).
- **Translation Bible & TMDb Plot Context Ingestion:** Integrates companion `translation_bible.json` (or via explicit `-b` / `--bible` flag) along with TMDb plot overview, genres, and full verified character cast rosters with grammatical gender tags before running the LLM pass.
- **Adaptive Model Cascade & Google API Hardening:** Multi-tier waterfall fallback (`gemini-3.8-flash` → `gemini-3.7-flash` → `gemini-3.6-flash` → `gemini-3.5-flash` → `gemini-3.5-flash-lite`) with dynamic model discovery, real-time Google API error body parsing, handling for 429 quota and 503 overload errors, and working model lock-in for subsequent batches.
- **Official Homebrew Tap & Universal Bottle (`omerninyo/tap`):** Global 1-second installation on macOS (both Apple Silicon and Intel) via pre-packaged `:all` bottles on GitHub Releases, bypassing Xcode compiler checks completely.
- **Interactive Credentials Onboarding (`rightsub config`):** 10-second setup wizard for Google Gemini & TMDb API keys with live ping authentication checks and automated storage in `~/.config/rightsub/config.json`.
- **System Health Diagnostics (`rightsub doctor`):** End-to-end environment inspector verifying Python 3.9+, FFmpeg suite, TMDb, Gemini, Ollama daemon, and Quicksubs STT.
- **On-Device STT Engine Clarification & OS Safety:** Apple SpeechAnalyzer integration for instant source audio transcription on Apple Silicon with macOS 26+ (Tahoe), with automated detection and clear guidance for Whisper (`whisper-cpp`) on older macOS versions and for Hebrew audio transcription.

---

## 🌟 Version 1.2.0 — Home Media Automation Stack & Clean-Slate Setup

> **Release Date:** September 2026 (Commit: `0acfb14`)  
> **Milestone Focus:** Hands-off home lab automation, zero-daemon architecture, and clean-slate onboarding without package managers.

### 🎯 Key Highlights
- **Home Media Integrations (Set-and-Forget):** Native, tested hooks for **qBittorrent**, **Sonarr**, **Radarr**, **Bazarr**, **Transmission**, and **Tautulli/Plex**.
- **Architectural Shift — Why No 24/7 Daemon:** Proved why event-driven completion hooks beat heavy background polling daemons: **0% idle CPU, 0 MB RAM**, and absolute elimination of race conditions on multi-gigabyte active torrent downloads.
- **Clean-Slate / Bare System Support:** Guided setups for users starting without basic package managers (no Homebrew on macOS or no Winget on Windows).
- **Safe-Zone Social Preview & Hero Banner:** 1280x640 OpenGraph-compliant cards featuring authentic Hebrew and Arabic subtitles designed with 65% central safe margins.
- **Architectural Specifications:** Published comprehensive future RFC specifications for the [Interactive CLI Wizard](proposals/RFC_001_INTERACTIVE_TUI.md) and the [Autonomous Setup & Health-Check Wizard](proposals/RFC_003_SYSTEM_INTEGRATION_WIZARD.md).

---

## 🌟 Version 1.1.0 — Windows Parity & Seed-Safe Architecture

> **Release Date:** September 2026 (Commit: `ec4ea70`)  
> **Milestone Focus:** 100% cross-platform equality for Windows users and torrent seeding protection.

### 🎯 Key Highlights
- **Seed-Safe Architecture by Default:** Non-destructive subtitle duplication into `Movie.he.srt` leaving original files 100% bit-for-bit intact so active torrent seeding is never broken.
- **Full Windows Feature Parity:** Native `install.bat`, automatic PowerShell User PATH registration, CMD/PowerShell UTF-8 console wrappers (`chcp 65001`), and Winget FFmpeg guidance.
- **Interactive Issue Forms:** Category-specific issue templates for SubRefine Core vs. SubSwarm Translation pipelines.
- **Automated Documentation Consistency:** Automated unit tests verifying cross-platform parity and valid doc link resolution across the repository.

---

## 🌟 Version 1.0.0 — The Autonomous Engine (`auto`, STT & TMDb)

> **Release Date:** September 2026 (Commit: `bf3ec19`)  
> **Milestone Focus:** All-in-one autonomous runner, on-device transcription, and live entity resolution.

### 🎯 Key Highlights
- **Autonomous Zero-Config Runner (`rightsub auto`):** Drop a file or folder and RightSub detects whether to extract, fix Plex BiDi, or prepare AI translation waves automatically.
- **On-Device Apple Silicon STT (`quicksubs`):** High-speed local audio transcription and audio-grounded retiming utilizing Apple's Neural Engine with zero cloud costs.
- **TMDb Deterministic Entity & Gender Resolution:** Direct API integration mapping cast and episodic guest stars to guaranteed grammatical gender (`את/היא` vs `אתה/הוא`), eliminating AI gender hallucinations.
- **Offline Local LLM Translation:** Integrated support for [Ollama](https://ollama.ai) (`llama3.2`, `qwen2.5:7b`) for 100% local, free translation.
- **Global Homebrew Distribution:** Official `Formula/rightsub.rb` and global `./install.sh`.

---

## 🌟 Version 0.9.0 — Core SubRefine & SubSwarm Multi-Agent Engine

> **Release Date:** September 2026 (Commit: `7f68354`)  
> **Milestone Focus:** Ground-up algorithmic subtitle mastering, Plex BiDi repair, and 101-episode television benchmark.

### 🎯 Key Highlights
- **SubRefine Engine (Plex & Infuse BiDi Fix):** Idempotent Right-to-Left Mark (`\u200F` / RLM) injection solving inverted punctuation (`? ! .`) and dashes across Apple TV, Android TV, LG WebOS, Infuse, and VLC.
- **Mojibake & Legacy Charset Recovery:** Autonomous detection of CP1255 / Windows-1255 / ISO-8859-8 and lossless conversion to modern UTF-8.
- **SDH & Watermark Sanitizer:** Removal of auditory sound cues (`[DOOR CREAKS]`, `♪ Pop music ♪`) and release group promotional spam while strictly maintaining dialogue sync timestamps.
- **SubSwarm Multi-Agent Pipeline:** Splits full-length episodes into ~210 cue waves with context overlaps, character translation bibles, and guaranteed 1:1 line reconciliation.
- **100% Verified Benchmark:** Processed and validated all 101 full episodes of Boston Legal (5 seasons) with 51 passing automated regression tests.
