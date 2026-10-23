---
name: subtitle-translator
description: Production-grade subtitle extraction, translation, synchronization, and BiDi formatting (Plex/Infuse) for movies and TV series.
---

# Subtitle Translator Skill (RightSub)

## Overview
This skill equips Antigravity with a robust, modular framework for translating, synchronizing, and fixing subtitles for movies and TV series using **RightSub**.
Master repository: `/Volumes/Other/Antigravity/RightSub`

It features a unified CLI entrypoint (`rightsub` or `toolkit.py`) powered by two core engines:
- **SubRefine Engine (100% Deterministic, 0 AI Tokens)**: Standalone Plex/Infuse 3-Stage Canonical Hebrew BiDi & Un-Flipping Engine (reversing 18 legacy visual-flipping patterns benchmarked across 20,299 files / 15.6M lines and wrapping lines with leading and trailing `\u200F` after punctuation per UAX #9 Rule N1), content-based Hebrew `.srt` discovery with Seed-Safe `.he.srt` output (preserving plain `.srt` files untouched for torrent seeding), language-verified legacy charset conversion (CP1255 -> UTF-8), homoglyph-conditional final-letter normalization, Georgian/Cyrillic homoglyph repair (`דეייט` -> `דייט`), deterministic bilingual number un-flipping (`cross_check_bilingual_numbers`, fixing `Subabi` `84` -> `48`), formatting tags protection, and SDH/multi-line ad stripping.
- **SubSwarm Engine (AI-Assisted Translation & Rare-Case Semantic Polish)**: Quota-optimized translation pipeline generating Translation Bibles, splitting into ~210-line JSON chunks (saving 95% API quota with Gemini Flash-Lite), and merging with zero-discrepancy & 25-cue window `Cue Drift` anchor validation (`validate_anchor_alignment`). Also includes `rightsub polish` for rare edge cases where an existing subtitle is an old amateur draft or corrupted OCR/machine translation needing semantic gender or franchise canon fixes.

## Quick CLI Reference (`./rightsub`)
```bash
# 1. Standalone Plex Hebrew punctuation fix & SDH/ad cleaning:
./rightsub fix-plex <path_or_dir> --recursive --in-place --clean-ads --backup
# (Use --dry-run to preview changes safely)

# 2. Universal Discovery & Extraction (embedded-first priority across formats):
./rightsub extract <video_or_season_dir> [--lang eng] [--force]

# 3. Build Translation Bible across an entire season:
./rightsub bible Season1/*.en.srt -o translation_bible.json

# 4. Split English SRT into JSON translation batches:
./rightsub split "video.en.srt" -o "work/batches/"

# 5. Generate AI Translation Prompts for Subagents:
./rightsub prompt-gen "work/batches/" -b translation_bible.json -t "Show Name" -o "work/prompts/"

# 6. Merge translated JSON batches into final Hebrew SRT with RLM & QC:
./rightsub merge "video.en.srt" "work/translated/" -o "video.he.srt"

# 7. Comprehensive Quality Assurance Audit:
./rightsub qa "video.he.srt" -m "video.en.srt"

# 8. Adjust framerate or time offset:
./rightsub adjust-fps "sub.srt" -o "synced.srt" --fps_from 25.0 --fps_to 23.976
```

## Full Season Batching & Autonomous Wave Strategy (SubSwarm)
When translating an entire season (20+ episodes, ~20,000 subtitles):
1. **Batch Extract**: `./rightsub extract <season_dir>`
2. **Season Translation Bible**: `./rightsub bible <season_dir>/*.en.srt -o translation_bible.json` (maps all characters and locked glossary upfront).
3. **Pre-Split**: Split all episodes into ~210-cue batches (`./rightsub split`).
4. **Autonomous Waves & Dynamic Minimum Baseline Model Governance**:
   - Execute in waves of 2-3 episodes (8-14 concurrent subagents).
   - **MANDATORY MINIMUM BASELINE**: Subagents MUST be configured with **Gemini 3.5 Flash-Lite** (`Model: "flash_lite"`). This provides the optimal balance of ultra-low cost ($0.15/M input tokens), sub-second latency, high throughput, and zero unnecessary thinking overhead for structured subtitle translation.
   - **STRICT PROHIBITION OF LEGACY & EXPENSIVE TIERS**:
     - NEVER use or fall back to deprecated legacy models (Gemini 2.x/2.5).
     - NEVER default to expensive heavyweight thinking tiers for bulk batch translation.
   - **FORWARD COMPATIBILITY & A/B BENCHMARKING (3.6+, 4.x)**:
     Whenever Google introduces a newer lightweight generation (e.g. Gemini 3.6 Flash-Lite, Gemini 4.x), conduct an A/B benchmark on a sample episode comparing translation fidelity, turnaround time, and token cost against the existing baseline. If results prove superior or equal in quality at comparable efficiency, update the documentation and establish the newer generation as the new minimum baseline floor.
5. **Unattended Execution**: Use `/goal translate all episodes of season X` to run autonomous back-to-back waves until 100% verified.

## Edge Cases & Red Team Guide
For exhaustive details on handling VFR framerate fluctuations, SDH hearing-impaired noise stripping vs context extraction, legacy Windows-1255 charsets, Smart TV quote flips, 18 legacy visual-flipping patterns, `Cue Drift` anchor validation, and contextual legal homographs, refer to:
👉 `EDGE_CASES_AND_RED_TEAM.md`

## Available Scripts (in `/Volumes/Other/Antigravity/RightSub/scripts/`)
- `01_extract_subtitles.py`: Universal discovery & FFmpeg extractor (MKV/MP4/M4V/AVI/etc.) with embedded-first priority, tag sanitization, and format conversion.
- `02_web_search_and_sync.py`: Timing delta & sync tester for external subtitles.
- `03_generate_bible.py`: Entity, gender, and honorific scanner.
- `04_split_batches.py`: Optimal chunker (~210 items) for LLMs.
- `05_merge_and_validate.py`: Zero-discrepancy merger with UAX #9 RLM injection, homoglyph normalization, and `validate_anchor_alignment` (`Cue Drift` guard).
- `06_adjust_fps_or_offset.py`: Linear time shifter and FPS stretcher.
- `07_fix_plex_punctuation.py`: Standalone 3-Stage Canonical BiDi & Un-Flipping Engine with encoding conversion & multi-line ad cleaner (SubRefine Core).
- `08_quality_assurance.py`: Comprehensive Red Team QA auditor (leading/trailing vocative gender mismatches, morphological contradictions, BiDi, timing).
- `09_prompt_builder.py`: Universal multi-agent wave prompt generator.
- `18_auto_pipeline.py`: Zero-flag autonomous runner with content-based Hebrew `.srt` discovery and Seed-Safe `.he.srt` torrent protection.
- `19_polish_and_qc.py`: Deterministic canon & bilingual number un-flipper + optional semantic AI proofreader + interactive line-by-line diff reviewer (`--interactive`).
- `20_config_and_doctor.py`: Unified setup wizard (`setup`), API key onboarding (`config`), downloader hooks/service installer (`--install-hooks` / `--install-service`), and health check (`doctor`).
- `21_webhook_server.py`: Native lightweight HTTP Webhook daemon for Sonarr, Radarr, and Bazarr (`serve`).
- `22_interactive_wizard.py`: Interactive Terminal & Windows CMD Mastering Wizard (`wizard` or `rightsub` with no arguments).
- `23_mcp_server.py`: Native Model Context Protocol (`MCP`) server over `stdio` & 1-command multi-agent installer (`rightsub mcp --install`).
