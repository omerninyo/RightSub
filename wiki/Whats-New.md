# 🚀 What's New in RightSub — Product & Milestone Releases

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="WHATS_NEW.he.md"><b>עברית</b></a>
</p>

This document tracks **major milestone releases** and product capabilities in RightSub. Unlike dry git commit logs, these notes focus on practical user value, media server improvements, and workflow enhancements.

---

## 🌟 Version 1.1.0 — Home Media Automation & Full Windows Parity

> **Release Date:** September 2026  
> **Milestone Focus:** Hands-off home lab automation, zero-daemon architecture, and 100% feature equality across macOS and Windows.

### 🎯 Key Highlights
- **Home Media Integrations (Set-and-Forget):** Native, tested hooks for **qBittorrent**, **Sonarr**, **Radarr**, **Bazarr**, **Transmission**, and **Tautulli/Plex**.
- **Architectural Shift — Why No 24/7 Daemon:** Proved why event-driven completion hooks beat heavy background polling daemons: **0% idle CPU, 0 MB RAM**, and absolute elimination of race conditions on multi-gigabyte active torrent downloads.
- **Full Windows Feature Parity:** Added native `install.bat`, automatic PowerShell User PATH registration, CMD/PowerShell UTF-8 console wrappers (`chcp 65001`), and Winget FFmpeg guidance.
- **Clean-Slate / Bare System Support:** Guided setups for users starting without basic package managers (no Homebrew on macOS or no Winget on Windows).
- **Safe-Zone Social Preview & Hero Banner:** 1280x640 OpenGraph-compliant cards featuring authentic Hebrew and Arabic subtitles designed with 65% central safe margins.
- **Architectural Specifications:** Published comprehensive future roadmaps for the [Interactive CLI Wizard](FUTURE_INTERACTIVE_CLI.md) and the [Autonomous Setup & Health-Check Wizard](FUTURE_SETUP_WIZARD.md).

---

## 🌟 Version 1.0.0 — Core SubRefine & SubSwarm Multi-Agent Engine

> **Release Date:** September 2026  
> **Milestone Focus:** Ground-up algorithmic subtitle mastering, Plex BiDi repair, and context-aware AI translation.

### 🎯 Key Highlights
- **SubRefine Engine (Plex & Infuse BiDi Fix):** Idempotent Right-to-Left Mark (`\u200F` / RLM) injection solving inverted punctuation (`? ! .`) and dashes across Apple TV, Android TV, LG WebOS, Infuse, and VLC.
- **Mojibake & Legacy Charset Recovery:** Autonomous detection of CP1255 / Windows-1255 / ISO-8859-8 and lossless conversion to modern UTF-8.
- **SDH & Watermark Sanitizer:** Removal of auditory sound cues (`[DOOR CREAKS]`, `♪ Pop music ♪`) and release group promotional spam while strictly maintaining dialogue sync timestamps.
- **TMDb Deterministic Entity & Gender Resolution:** Direct API integration mapping cast and episodic guest stars to guaranteed grammatical gender (`את/היא` vs `אתה/הוא`), eliminating AI gender hallucinations in Semitic languages.
- **SubSwarm Multi-Agent Pipeline:** Splits full-length episodes into ~210 cue waves with context overlaps, character translation bibles, and guaranteed 1:1 line reconciliation.
- **On-Device Apple Silicon STT (`quicksubs`):** High-speed local audio transcription and audio-grounded retiming utilizing Apple's Neural Engine with zero cloud costs.
- **100% Test Coverage:** 69 automated unit tests verifying docs integrity, CLI parity, and live regression coverage against 101 full television episodes.
