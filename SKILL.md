---
name: subtitle-translator
description: Production-grade subtitle extraction, translation, synchronization, and BiDi formatting (Plex/Infuse) for movies and TV series.
---

# Subtitle Translator Skill (RightSub)

## Overview
This skill equips Antigravity with a robust, modular framework for translating, synchronizing, and fixing subtitles for movies and TV series using **RightSub**.
Master repository: `/Volumes/Other/Antigravity/RightSub`

It features a unified CLI entrypoint (`rightsub` or `toolkit.py`) powered by two core engines:
- **SubRefine Engine**: Standalone Plex/Infuse Hebrew BiDi Fixer, idempotent RLM injection, language-verified legacy charset conversion (CP1255 -> UTF-8), formatting tags protection, and SDH/ad stripping.
- **SubSwarm Engine**: Quota-optimized translation pipeline generating Translation Bibles, splitting into ~210-line JSON chunks (saving 95% API quota with Gemini Flash-Lite), and merging with zero-discrepancy validation.

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
For exhaustive details on handling VFR framerate fluctuations, SDH hearing-impaired noise stripping vs context extraction, legacy Windows-1255 charsets, Smart TV quote flips, and contextual legal homographs, refer to:
👉 `EDGE_CASES_AND_RED_TEAM.md`

## Available Scripts (in `/Volumes/Other/Antigravity/RightSub/scripts/`)
- `01_extract_subtitles.py`: Universal discovery & FFmpeg extractor (MKV/MP4/M4V/AVI/etc.) with embedded-first priority, tag sanitization, and format conversion.
- `02_web_search_and_sync.py`: Timing delta & sync tester for external subtitles.
- `03_generate_bible.py`: Entity, gender, and honorific scanner.
- `04_split_batches.py`: Optimal chunker (~210 items) for LLMs.
- `05_merge_and_validate.py`: Zero-discrepancy merger with RLM injection and homoglyph normalization.
- `06_adjust_fps_or_offset.py`: Linear time shifter and FPS stretcher.
- `07_fix_plex_punctuation.py`: Standalone Plex punctuation fixer with encoding conversion & ad cleaner (SubRefine Core).
- `08_quality_assurance.py`: Comprehensive Red Team QA auditor for subtitle files and libraries.
- `09_prompt_builder.py`: Universal multi-agent wave prompt generator.
