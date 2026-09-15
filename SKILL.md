---
name: subtitle-translator
description: Production-grade subtitle extraction, translation, synchronization, and BiDi formatting (Plex/Infuse) for movies and TV series.
---

# Subtitle Translator Skill

## Overview
This skill equips Antigravity with a robust, modular framework for translating, synchronizing, and fixing subtitles for movies and TV series.
Master repository: `/Volumes/Other/Antigravity/SubtitleToolkit`

It features a unified CLI entrypoint (`toolkit.py`) and dedicated scripts covering:
- **Standalone Plex/Infuse Hebrew BiDi Fixer**: Idempotent, language-verified, legacy charset conversion (CP1255 -> UTF-8), formatting tags protection, and ad stripping.
- **Quota-Optimized Translation Pipeline**: Generates Translation Bibles, splits into ~210-line JSON chunks (saving 95% API quota with Flash-Lite), and merges with zero-discrepancy validation.
- **Timing & Framerate Sync**: Auto-stretches 23.976 <-> 25.0 FPS and aligns web downloads to master video audio.
- **Automated QA & Prompt Generation**: Built-in 1-to-1 cue verification, BiDi audit, homoglyph cleaning, and multi-agent wave prompt generation.

## Quick CLI Reference (`toolkit.py`)
```bash
# 1. Standalone Plex Hebrew punctuation fix on existing files / libraries:
python3 toolkit.py fix-plex <path_or_dir> --recursive --in-place --clean-ads --backup
# (Use --dry-run to preview changes safely)

# 2. Universal Discovery & Extraction (embedded-first priority across formats):
python3 toolkit.py extract <video_or_season_dir> [--lang eng] [--force]

# 3. Build Translation Bible across an entire season:
python3 toolkit.py bible Season1/*.en.srt -o translation_bible.json

# 4. Split English SRT into JSON translation batches:
python3 toolkit.py split "video.en.srt" -o "work/batches/"

# 5. Generate AI Translation Prompts for Subagents:
python3 toolkit.py prompt-gen "work/batches/" -b translation_bible.json -t "Show Name" -o "work/prompts/"

# 6. Merge translated JSON batches into final Hebrew SRT with RLM & QC:
python3 toolkit.py merge "video.en.srt" "work/translated/" -o "video.he.srt"

# 7. Comprehensive Quality Assurance Audit:
python3 toolkit.py qa "video.he.srt" -m "video.en.srt"

# 8. Adjust framerate or time offset:
python3 toolkit.py adjust-fps "sub.srt" -o "synced.srt" --fps_from 25.0 --fps_to 23.976
```

## Full Season Batching & Autonomous Wave Strategy
When translating an entire season (20+ episodes, ~20,000 subtitles):
1. **Batch Extract**: `python3 toolkit.py extract <season_dir>`
2. **Season Translation Bible**: `python3 toolkit.py bible <season_dir>/*.en.srt -o translation_bible.json` (maps all characters and locked glossary upfront).
3. **Pre-Split**: Split all episodes into ~210-cue batches (`toolkit.py split`).
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

## Available Scripts (in `/Volumes/Other/Antigravity/SubtitleToolkit/scripts/`)
- `01_extract_subtitles.py`: Universal discovery & FFmpeg extractor (MKV/MP4/M4V/AVI/etc.) with embedded-first priority, tag sanitization, and format conversion.
- `02_web_search_and_sync.py`: Timing delta & sync tester for external subtitles.
- `03_generate_bible.py`: Entity, gender, and honorific scanner.
- `04_split_batches.py`: Optimal chunker (~210 items) for LLMs.
- `05_merge_and_validate.py`: Zero-discrepancy merger with RLM injection and homoglyph normalization.
- `06_adjust_fps_or_offset.py`: Linear time shifter and FPS stretcher.
- `07_fix_plex_punctuation.py`: Standalone Plex punctuation fixer with encoding conversion & ad cleaner.
- `08_quality_assurance.py`: Comprehensive Red Team QA auditor for subtitle files and libraries.
- `09_prompt_builder.py`: Universal multi-agent wave prompt generator.
