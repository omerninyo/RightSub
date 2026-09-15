# 🎬 SubtitleToolkit - Universal Subtitle Translation, BiDi & Repair Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://python.org)
[![Plex & Infuse Ready](https://img.shields.io/badge/Plex%20%26%20Infuse-BiDi%20Verified-orange.svg)]()
[![Benchmark: 101/101 Episodes](https://img.shields.io/badge/Boston%20Legal-100%25%20Tested-purple.svg)]()

**SubtitleToolkit** is a production-grade, battle-tested Python framework and CLI designed to fix, translate, synchronize, and format subtitles for **ANY movie or television series**.

Originally engineered and perfected across all 5 seasons (101 episodes, 78,000+ dialogue cues) of the courtroom drama *Boston Legal*, SubtitleToolkit provides an end-to-end autonomous pipeline with zero-drop 1-to-1 timing synchronization, flawless Right-to-Left (BiDi) formatting for Plex and Infuse, and high-throughput LLM orchestration via Google Gemini 3.5 / 3.8.

---

## ✨ Key Features

- 🎯 **1-to-1 Timing & Zero Dropped Cues**: Guarantees exact millisecond alignment against source master subtitles. No merged cues, no skipped lines.
- 📺 **Plex & Infuse BiDi Engine**: Automated Right-to-Left Mark (`U+200F` / RLM) injection to eliminate punctuation jumping (`?`, `!`, `.`, `-`) across all media players (Plex, Infuse, VLC, Apple TV, Android TV).
- 🧠 **Algorithmic Memory & Auto-Sanitization**:
  - Automatically detects and replaces visually identical Cyrillic homoglyphs (`CYRILLIC_TO_HEBREW`).
  - Normalizes Arabic homoglyphs into Hebrew equivalents.
  - Enforces standard Hebrew gershayim (`״` / `\u05F4`) for acronyms (עו״ד, ארה״ב).
  - Eliminates vocalization (nikud) and strips auditory hearing-impaired (SDH) tags while preserving block index.
- ⚡ **High-Throughput AI Translation**: Native prompt generator for Google Gemini (Flash-Lite / Flash) supporting wave-based parallel concurrency.
- 🔍 **Automated QA & Verification Suite**: Comprehensive verification of block counts, timestamps, character sets, and formatting.
- 🛠️ **Full Media Swiss Army Knife**: Subtitle extraction from MKV/MP4 via FFmpeg, framerate stretching (23.976 <-> 25.0 FPS), delay adjustment, and translation bible extraction.

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/<your-username>/SubtitleToolkit.git
cd SubtitleToolkit
pip install -r requirements.txt
```

### 2. Fix Existing Hebrew Subtitles for Plex/Infuse
```bash
python3 toolkit.py fix-plex "MyMovie.he.srt" --in-place
```

### 3. Translate Any Movie or TV Episode
```bash
# 1. Generate translation prompts and wave files
python3 toolkit.py prompt-gen "MyMovie.en.srt" --title "My Movie" --genre "Sci-Fi Action"

# 2. Merge translated JSON batches into final Hebrew SRT
python3 toolkit.py merge "MyMovie.en.srt" "prompts_My Movie" -o "MyMovie.he.srt"

# 3. Verify quality with automated QA
python3 toolkit.py qa "MyMovie.en.srt" "MyMovie.he.srt"
```

---

## 📖 CLI Commands Reference

| Command | Description | Example |
| :--- | :--- | :--- |
| `split` | Split English SRT into JSON batches (~210 items) | `python3 toolkit.py split movie.en.srt -o ./batches` |
| `merge` | Assemble translated JSON batches into Hebrew SRT with RLM | `python3 toolkit.py merge movie.en.srt ./batches -o movie.he.srt` |
| `prompt-gen` | Generate prompts and wave configs for any movie/show | `python3 toolkit.py prompt-gen movie.en.srt -t "Inception"` |
| `qa` | Run comprehensive QA audit on SRT pair or directory | `python3 toolkit.py qa movie.en.srt movie.he.srt` |
| `fix-plex` | Repair punctuation and BiDi in-place for Plex/Infuse | `python3 toolkit.py fix-plex ./Season1/ --recursive -i` |
| `extract` | Extract subtitle tracks from MKV/MP4 via FFmpeg | `python3 toolkit.py extract video.mkv -o video.en.srt` |
| `sync` | Compare synchronization between English & Hebrew SRTs | `python3 toolkit.py sync master.en.srt external.he.srt` |
| `adjust-fps` | Stretch framerate or apply time offsets | `python3 toolkit.py adjust-fps input.srt -o output.srt --offset_ms 1500` |

---

## 🏆 Case Study: Boston Legal (100% Completed)
SubtitleToolkit was proven and validated across all **101 episodes** of *Boston Legal* (Seasons 1–5):
- **101 / 101 Episodes Translated & Deployed** (100% completion).
- **78,000+ Cues Synchronized** with 0 timing discrepancies.
- **100% Plex & Infuse BiDi Compatibility** with zero punctuation reversal.
- See the full [Boston Legal Case Study](docs/CASE_STUDY_BOSTON_LEGAL.md).

---

## 📄 License
Released under the [MIT License](LICENSE).
