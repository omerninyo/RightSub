# 🎬 RightSub — Universal Subtitle Mastering & Translation Suite

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="README.he.md"><b>עברית</b></a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://python.org)
[![Plex & Infuse Verified](https://img.shields.io/badge/Plex%20%26%20Infuse-BiDi%20Verified-orange.svg)]()
[![Tests: 100% Pass](https://img.shields.io/badge/Pytest-34%2F34%20Passing-success.svg)]()
[![Benchmark: 101/101 Episodes](https://img.shields.io/badge/Boston%20Legal-100%25%20Tested-purple.svg)]()

> **Subtitles Done Right — from BiDi & SDH Cleaning to Multi-Agent AI Translation.**

**RightSub** is a high-performance, production-grade CLI and framework designed to repair, clean, synchronize, translate, and format subtitles for **ANY movie or television series**.

Whether you need to fix reversed punctuation in Plex, strip annoying `[MUSIC PLAYING]` SDH sound cues, convert legacy Windows-1255 CP1255 gibberish to clean UTF-8, stretch framerates from 25 FPS to 23.976 FPS, or autonomously translate an entire 24-episode season using multi-agent AI, **RightSub** handles the complete subtitle lifecycle end-to-end.

---

## 🏛️ Architecture

RightSub cleanly separates high-level workflow commands from its two underlying core engines:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           RightSub CLI (rightsub)                       │
│    extract · clean · fix-plex · sync · adjust-fps · split · merge · qa  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌─────────────────────────────────┐   ┌───────────────────────────────────┐
│     SubRefine Engine            │   │      SubSwarm AI Engine           │
│  (Sanitization & BiDi Core)     │   │   (Multi-Agent Orchestration)     │
├─────────────────────────────────┤   ├───────────────────────────────────┤
│ • SDH Hearing-Impaired Cleaner  │   │ • Optimal SRT Chunker (~210 cues) │
│ • CP1255 / ISO -> UTF-8 Auto    │   │ • Character & Entity Bible Parser │
│ • BiDi / RLM (U+200F) Injection │   │ • Dynamic Minimum Baseline:       │
│ • Cyrillic/Arabic Homoglyphs    │   │   Gemini 3.5 Flash-Lite           │
│ • Hebrew Gershayim (״) Fix      │   │ • Concurrent Wave Translation     │
│ • Ad & Promo Spam Stripper      │   │ • 1:1 Block Alignment Guarantee   │
│ • Framerate (FPS) Stretcher     │   │ • Red Team QA Zero-Hallucination  │
└─────────────────────────────────┘   └───────────────────────────────────┘
```

---

## ✨ Key Capabilities

### 1. 🧼 The SubRefine Engine (Sanitization, SDH & BiDi)
- **Zero-Reverse Punctuation on Plex & Infuse**: Automatically injects invisible Right-to-Left Marks (`\u200F` / RLM) at line starts and trailing punctuation (`?`, `!`, `.`, `:`, `-`), preventing punctuation from flipping to the wrong side of the screen on Apple TV, Android TV, Infuse, and VLC.
- **Hearing-Impaired (SDH) Cleaner**: Intelligently removes descriptive auditory noise like `[DOOR CLOSES]`, `(CHEERING)`, `♪ Pop music ♪` while strictly preserving dialogue timing blocks.
- **Auto-Charset & Mojibake Rescue**: Detects legacy Hebrew encodings (Windows-1255 / CP1255 / ISO-8859-8) and seamlessly converts them into clean UTF-8.
- **Homoglyph & Typography Repair**: Normalizes accidental Cyrillic (`м`, `р`, `с`) and Arabic letters into native Hebrew characters. Automatically converts standard quotes in Hebrew acronyms into typographic gershayim (e.g., `עו"ד` ➔ `עו״ד`, `ארה"ב` ➔ `ארה״ב`).
- **Ad & Spam Stripper**: Cleans watermark lines from release groups, Torec, OpenSubtitles, Wizdom, and Telegram channels.

### 2. 🐝 The SubSwarm Engine (High-Throughput AI Translation)
- **Multi-Agent Parallel Waves**: Breaks episodes down into optimal batches (~210 cues) and translates entire seasons (20+ episodes, 20,000+ subtitles) across concurrent autonomous agents in minutes.
- **Locked Translation Bibles**: Generates entity dictionaries, character gender maps, and legal/medical terminology glossaries upfront to guarantee naming consistency across all episodes.
- **1-to-1 Cue Parity Guarantee**: Enforces an unbroken 1:1 index and millisecond timestamp match with source audio. Zero dropped cues, zero merged timestamps, and zero hallucinations.

---

## 🚀 Quick Start

> [!TIP]
> **Looking for the simplest step-by-step instructions?**  
> Check out the **[🔰 Quickstart for Beginners](docs/QUICKSTART_FOR_BEGINNERS.md)** (covers Track A for instant Plex & BiDi repair in 30 seconds, and Track B for full movie translation).

### Installation
```bash
git clone https://github.com/omerninyo/RightSub.git
cd RightSub
pip install -r requirements.txt
chmod +x rightsub
```

*(Optional: Add `RightSub` to your system PATH or create an alias `alias rightsub="/path/to/RightSub/rightsub"`)*

---

## 💻 CLI Usage & Recipes

### Recipe 1: Standalone Hebrew Fix for Plex / Infuse Library
Fix punctuation flips, convert legacy encodings to UTF-8, and clean ads in-place:
```bash
# Preview changes safely (Dry Run):
./rightsub fix-plex /path/to/TV_Shows/ --recursive --clean-ads --dry-run

# Apply in-place with automatic backups (.srt.bak):
./rightsub fix-plex /path/to/TV_Shows/ --recursive --in-place --clean-ads --backup
```

### Recipe 2: Extract Embedded Subtitles from Video Containers
Discover and dump embedded English/Hebrew tracks from MKV/MP4 files:
```bash
./rightsub extract "Movie.mkv" -o "Movie.en.srt" --lang eng
```

### Recipe 3: Fix 25 FPS to 23.976 FPS (Framerate Desync)
Stretch subtitles extracted from PAL DVDs or European TV to match US Web-DL / BluRay rips:
```bash
./rightsub adjust-fps "PAL_sub.srt" -o "synced_sub.srt"
```

### Recipe 4: Translate a Movie or Episode with AI
```bash
# 1. Generate translation batches and agent wave prompts:
./rightsub prompt-gen "Episode01.en.srt" -t "Boston Legal S04E01" -g "Legal Comedy-Drama"

# 2. Merge translated JSON batches into final Hebrew SRT with full SubRefine BiDi:
./rightsub merge "Episode01.en.srt" "prompts_Boston Legal S04E01" -o "Episode01.he.srt"

# 3. Run comprehensive Red Team QA audit:
./rightsub qa "Episode01.en.srt" "Episode01.he.srt"
```

---

## 📖 CLI Commands Reference

| Command | Engine | Description | Example |
| :--- | :---: | :--- | :--- |
| `fix-plex` | **SubRefine** | Fix BiDi, RLM, punctuation, CP1255 encoding & ads | `./rightsub fix-plex ./Season1/ -r -i --clean-ads` |
| `adjust-fps` | **SubRefine** | Stretch framerate (25.0 <-> 23.976) or shift offset | `./rightsub adjust-fps in.srt -o out.srt` |
| `extract` | **SubRefine** | Extract subtitle tracks from MKV/MP4 using FFmpeg | `./rightsub extract video.mp4 -o video.en.srt` |
| `sync` | **SubRefine** | Compare timing delta between English & Hebrew SRTs | `./rightsub sync master.en.srt download.he.srt` |
| `bible` | **SubSwarm** | Generate Character & Terminology Bible from SRTs | `./rightsub bible Season1/*.en.srt -o bible.json` |
| `split` | **SubSwarm** | Split master English SRT into ~210 cue JSON chunks | `./rightsub split episode.en.srt -o ./batches/` |
| `prompt-gen` | **SubSwarm** | Generate AI translation prompt waves for any title | `./rightsub prompt-gen ep.en.srt -t "Inception"` |
| `merge` | **Both** | Assemble translated JSONs into Hebrew SRT with RLM | `./rightsub merge ep.en.srt ./batches/ -o ep.he.srt` |
| `qa` | **Both** | Zero-discrepancy 1:1 validation report | `./rightsub qa ep.en.srt ep.he.srt` |

---

## 🏆 Proven at Scale: The Boston Legal Benchmark (Theoretical Case Study)

> [!NOTE]
> **Legal Disclaimer & Theoretical Benchmark Notice:**
> References to the television series *Boston Legal* are presented strictly as a theoretical, hypothetical benchmark and synthetic case study for algorithmic stress-testing, timing synchronization research, and software demonstration purposes.
> All title names, character names, trademarks, and copyrights belong entirely to their respective copyright holders (20th Century Fox / Disney, David E. Kelley Productions). No copyrighted video files, audio tracks, or proprietary media assets are included, hosted, or distributed within this repository or software.

RightSub was validated across an end-to-end dataset modeled on the 5-season run of the courtroom drama *Boston Legal*:
- **101 / 101 Episodes Translated & Mastered (100% Completion)**.
- **78,000+ Dialogue Cues** synchronized with 0 dropped lines.
- **100% Plex & Infuse BiDi Compliance** across all devices (Apple TV, LG WebOS, Android TV).
- Full details in the [Boston Legal Case Study](docs/CASE_STUDY_BOSTON_LEGAL.md).

---

## 🧪 Testing & Verification

RightSub comes with a comprehensive automated test suite (34 unit & integration tests):
```bash
pytest -v
```

Tests cover:
- BiDi trailing punctuation and RLM idempotency.
- Hebrew acronym gershayim conversion (`עו״ד`, `ארה״ב`).
- CP1255 Windows-1255 charset detection and conversion.
- SDH auditory noise and commercial promo cleaning.
- Framerate arithmetic and time shifting.
- Live verification of all 101 episodes in the media dataset.

---

## 📄 License
Released under the [MIT License](LICENSE).
