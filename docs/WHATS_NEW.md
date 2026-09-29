# 🚀 What's New in RightSub — Product & Milestone Releases

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="WHATS_NEW.he.md"><b>עברית</b></a>
</p>

This document tracks **major milestone releases** and product capabilities in RightSub. Unlike dry git commit logs, these notes focus on practical user value, media server improvements, and workflow enhancements.

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
