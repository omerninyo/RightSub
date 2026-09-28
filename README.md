<p align="center">
  <img src="docs/assets/banner.png" alt="RightSub — Universal Subtitle Mastering & Translation Suite" width="100%" />
</p>

# 🎬 RightSub — Universal Subtitle Mastering & Translation Suite

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="README.he.md"><b>עברית</b></a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://python.org)
[![Platform: Windows & macOS](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-blue.svg)]()
[![Plex & Infuse Verified](https://img.shields.io/badge/Plex%20%26%20Infuse-BiDi%20Verified-orange.svg)]()
[![Tests: 100% Pass](https://img.shields.io/badge/Pytest-69%2F69%20Passing-success.svg)]()
[![Benchmark: 101/101 Episodes](https://img.shields.io/badge/Boston%20Legal-100%25%20Tested-purple.svg)]()

> **Subtitles Done Right — from 1-Click Plex & BiDi Repair to Autonomous Multi-Agent AI Translation.**

**RightSub** is a high-performance CLI suite and Python framework designed to repair, clean, synchronize, translate, and format subtitles for **ANY movie or television series** across **Windows** and **macOS**.

Whether you want to fix reversed question marks in Plex on your Apple TV, convert unreadable Windows-1255 CP1255 Hebrew gibberish to clean UTF-8, strip annoying `[MUSIC PLAYING]` noise cues, fix framerate sync drifts, or translate an entire TV season using AI agents, RightSub gives you a dead-simple, reliable workflow.

---

## ⚡ Quickstart in 30 Seconds

Got a video or subtitle file that needs fixing or translation? **You only need one command.**

Type `rightsub auto ` and simply **drag & drop** the file or folder into your terminal:

### Windows (Command Prompt / PowerShell):
```cmd
rightsub auto "C:\Movies\Inception.he.srt"
:: Or for an entire TV season:
rightsub auto "C:\TV Shows\Breaking Bad Season 1"
```

### macOS / Linux (Terminal):
```bash
rightsub auto ~/Movies/Inception.he.srt
# Or for an entire TV season:
rightsub auto ~/Movies/Breaking_Bad_S01/
```

### What happens automatically?
- **Hebrew Subtitle (`.srt`)**: RightSub instantly fixes reversed punctuation (`? ! .`), converts legacy encodings to UTF-8, strips ads, and masters the file for Plex & Infuse. 
- **Video File (`.mkv` / `.mp4`)**: RightSub extracts embedded subtitles, transcribes audio if needed, and builds AI-ready translation waves.
- **Torrents & Seeding Protected (Seed-Safe)**: When encountering non-standard subtitles (e.g. `Movie.srt`), RightSub creates a clean `Movie.he.srt` copy while leaving the original file 100% bit-for-bit intact so active torrent seeding is never broken.
- **Home Media Automation (Set-and-Forget)**: Plug RightSub into **qBittorrent**, **Sonarr**, **Radarr**, **Bazarr**, or **Transmission** to run seamlessly in the background without needing a heavy 24/7 daemon. See [Home Media Integrations Guide](docs/INTEGRATIONS_GUIDE.md).

---

## 🎯 Choose Your Track

RightSub is organized into two distinct paths:

### Track 1: Fix Existing Subtitles (100% Offline & Free)
*No AI required. No API keys. Zero cloud bandwidth.*

- **Plex & Infuse BiDi Fix**: Injects invisible Right-to-Left Marks (`\u200F` / RLM) so punctuation and dashes never flip to the wrong side on Apple TV, Android TV, LG WebOS, Infuse, and VLC.
- **Encoding Rescue**: Automatically detects CP1255 / Windows-1255 / ISO-8859-8 and converts to modern UTF-8.
- **SDH Cleaner**: Strips hearing-impaired noise descriptors (`[CHEERING]`, `♪ Pop music ♪`) while strictly preserving dialogue timing.
- **Ad & Watermark Stripper**: Removes release group spam, site URLs, and promotional lines.

```bash
# Windows:
rightsub fix-plex "C:\Movies\Season 01" --recursive --clean-ads

# macOS / Linux:
rightsub fix-plex ~/Movies/Season_01 --recursive --clean-ads
```

---

### Track 2: Translate English Media to Hebrew with AI
*Translate entire movies or 24-episode seasons with full character context and zero hallucinations.*

RightSub structures the translation process so you can use **any AI model or assistant you already have**:

1. **Prepare Batches & Context**:
   ```bash
   rightsub auto "Movie.mkv"
   ```
   RightSub splits dialogue into optimal ~210-cue batches, resolves character genders via TMDb (e.g. `את/היא` vs `אתה/הוא`), and produces ready-to-use prompts.

2. **Translate with Your AI Assistant**:
   - **Coding AI Agents**: Antigravity, Claude Code, Cursor, Codex — paste the generated wave prompts.
   - **Free Local LLM (100% Offline)**: Run with [Ollama](https://ollama.ai) using:
     ```bash
     rightsub auto "Movie.mkv" --ollama
     ```

3. **Auto-Merge & Validate**:
   RightSub automatically merges translated JSON batches back into a pristine `.he.srt` file, enforces 1:1 line matching, and applies full BiDi formatting.

---

## 🔄 Home Media Automation & Integrations (Set-and-Forget)

> **Key Integrations & Keywords**: `qBittorrent` • `Sonarr` • `Radarr` • `Bazarr` • `Transmission` • `Tautulli/Plex` • `Background Watchers & Daemons` • `Seed-Safe`

RightSub is engineered to integrate natively into automated home media and seedbox stacks in a 100% hands-off workflow.

### The Recommended 2-Phase Strategy
1. **Retroactive Batch Fix (Run Once)**: Clean and master your entire existing media library:
   ```bash
   # Windows:
   rightsub auto "C:\Media\TV Shows"

   # macOS / Linux:
   rightsub auto /Volumes/Media/TV_Shows
   ```
2. **Ongoing Event-Driven Ingress (Set-and-Forget)**: Attach RightSub to your downloaders or `*arr` managers to process new media the millisecond it finishes downloading.

### Why Event-Driven Hooks Beat a 24/7 Background Daemon
Unlike heavy background daemons that poll filesystems 24/7 and risk corrupting multi-gigabyte files while they are still being written, RightSub's **Event-Driven Hook Architecture** operates with:
- 🛡️ **Zero Race Conditions**: Executes only on completed, hash-verified files.
- ⚡ **Zero Idle Overhead**: 0% CPU and 0 MB RAM when idle.
- 🔒 **Seed-Safe by Default**: Duplicates into `.he.srt`, leaving original downloaded torrent files 100% bit-for-bit intact so active seeding never breaks.

👉 **Read the full [Home Media & Download Integrations Guide](docs/INTEGRATIONS_GUIDE.md)** for copy-pasteable configurations for qBittorrent, Sonarr, Radarr, Bazarr, Transmission, and native OS Folder Watchers.

---

## 📦 Installation & Setup

RightSub offers equal, first-class support for both **Windows** and **macOS/Linux**:

### Windows (CMD / PowerShell)
1. **Clone or Download** the repository:
   ```cmd
   git clone https://github.com/omerninyo/RightSub.git
   cd RightSub
   ```
2. **Run the Windows Installer**:
   Double-click `install.bat` (or execute it in CMD):
   ```cmd
   install.bat
   ```
   *The installer verifies Python 3, installs dependencies from `requirements.txt`, and prepares global wrappers.*
3. **Run from anywhere**:
   Use `rightsub.bat` or `python rightsub.py`:
   ```cmd
   rightsub auto "Movie.mkv"
   ```

### macOS / Linux (Terminal)
Choose any of the following 3 options:

- **Option A: Fast Local Install (Recommended)**:
  ```bash
  git clone https://github.com/omerninyo/RightSub.git
  cd RightSub
  ./install.sh
  ```
  *Symlinks `rightsub` globally to `~/.local/bin/rightsub`.*

- **Option B: One-Liner Remote Install**:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/omerninyo/RightSub/main/install.sh | bash
  ```

- **Option C: Official Homebrew Tap**:
  ```bash
  brew install omerninyo/tap/rightsub
  ```

---

## 💻 Everyday CLI Recipes

### Recipe 0: Autonomous One-Command Runner (Zero Flags / Zero Hassle)
```bash
# Auto-repair Hebrew subtitle (BiDi RLM, ad stripping, automatic backup):
rightsub auto "Movie.he.srt"

# Auto-process video file (extract/transcribe subtitles and build batches):
rightsub auto "Movie.mkv"

# 100% offline, free local translation using Ollama (Llama 3, Qwen):
rightsub auto "Movie.mkv" --ollama

# Auto-scan and process entire TV season or complete media library:
rightsub auto "/path/to/Season 01/"
```

### Recipe 1: Standalone Hebrew Fix for Plex / Infuse Library
```bash
# Option A: Fix a single file in-place:
rightsub fix-plex "Movie.he.srt" --in-place

# Option B: Fix multiple specific files:
rightsub fix-plex "Ep01.he.srt" "Ep02.he.srt" "Ep03.he.srt" --in-place

# Option C: Preview changes safely on a whole folder (Dry Run):
rightsub fix-plex /path/to/TV_Shows/ --recursive --clean-ads --dry-run

# Option D: Apply in-place recursively with automatic backups (.srt.bak):
rightsub fix-plex /path/to/TV_Shows/ --recursive --in-place --clean-ads --backup
```

### Recipe 2: Extract Embedded Subtitles from Video Containers
```bash
rightsub extract "Movie.mkv" -o "Movie.en.srt" --lang eng
```

### Recipe 3: Fix 25 FPS to 23.976 FPS (Framerate Desync)
Stretch subtitles extracted from PAL DVDs or European TV to match US Web-DL / BluRay rips:
```bash
rightsub adjust-fps "PAL_sub.srt" -o "synced_sub.srt"
```

### Recipe 4: Translate a Movie or Episode with AI
```bash
# 1. Generate translation batches and agent wave prompts:
rightsub prompt-gen "Episode01.en.srt" -t "Inception" -g "Sci-Fi Action"

# 2. Merge translated JSON batches into final Hebrew SRT with full SubRefine BiDi:
rightsub merge "Episode01.en.srt" "prompts_Inception" -o "Episode01.he.srt"

# 3. Run comprehensive Red Team QA audit:
rightsub qa "Episode01.en.srt" "Episode01.he.srt"
```

---

## 🏛️ Advanced Architecture & Core Engines

For developers and power users, RightSub cleanly separates high-level workflow commands from its two underlying core algorithmic engines:

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

### 1. 🧼 The SubRefine Engine (Sanitization, SDH & BiDi)
- **Zero-Reverse Punctuation on Plex & Infuse**: Automatically injects invisible Right-to-Left Marks (`\u200F` / RLM) at line starts and trailing punctuation (`?`, `!`, `.`, `:`, `-`), preventing punctuation from flipping to the wrong side of the screen on Apple TV, Android TV, Infuse, and VLC.
- **Hearing-Impaired (SDH) Cleaner**: Intelligently removes descriptive auditory noise like `[DOOR CLOSES]`, `(CHEERING)`, `♪ Pop music ♪` while strictly preserving dialogue timing blocks.
- **Auto-Charset & Mojibake Rescue**: Detects legacy Hebrew encodings (Windows-1255 / CP1255 / ISO-8859-8) and seamlessly converts them into clean UTF-8.
- **Homoglyph & Typography Repair**: Normalizes accidental Cyrillic (`м`, `р`, `с`) and Arabic letters into native Hebrew characters. Automatically converts standard quotes in Hebrew acronyms into typographic gershayim (e.g., `עו"ד` ➔ `עו״ד`, `ארה"ב` ➔ `ארה״ב`).
- **Ad & Spam Stripper**: Cleans watermark lines from release groups, Torec, OpenSubtitles, Wizdom, and Telegram channels.

### 2. 🐝 The SubSwarm Engine (High-Throughput AI Translation)
- **Concurrent Agent Waves**: Splits subtitles into optimal batches (~210 cues per batch) to translate entire seasons (20+ episodes, 20,000+ lines) in minutes.
- **Pre-Locked Translation Bible**: Pre-extracts character names, legal/technical terms, and gender assignments to eliminate intra-season inconsistencies.
- **1:1 Alignment Guarantee**: Every index and timing range matches the audio and English master file. Zero dropped cues, zero hallucinations.

### 3. 🎙️ On-Device Speech & Audio Alignment (`quicksubs` Integration)
- **Zero-Cloud STT Ingestion**: Powered by **[quicksubs](https://github.com/mattbirchler/quicksubs)** (by Matt Birchler). Transcribes raw media on-device using Apple SpeechAnalyzer (Apple Silicon Neural Engine), OpenAI Whisper, or NVIDIA Parakeet with zero bandwidth and zero API costs.
- **Audio-Guided Retiming**: Extracts authoritative dialogue speech timestamps directly from the video file's audio track to re-align drifted, cut, or framerate-mismatched subtitles automatically.

### 4. 🎬 Ground-Truth Entity & Gender Resolution (`TMDb` Integration)
- **Deterministic Gender Mapping**: Automatically resolves character genders and episodic guest stars via **[The Movie Database (TMDb)](https://www.themoviedb.org)** API, guaranteeing 100% accurate second-person Hebrew pronouns (`את/היא` vs `אתה/הוא`) with zero hallucinations.
- **Narrative Context & Dialect Priming**: Injects episodic plot synopses, genre terms, and regional dialect guidance (e.g. British English idioms) directly into the translation prompts.

---

## 📖 CLI Commands Reference

| Command | Engine | Description | Windows Example | macOS / Linux Example |
| :--- | :---: | :--- | :--- | :--- |
| `auto` | **All** | Zero-flag autonomous runner for files, seasons, or directories | `rightsub auto "Movie.mkv"` | `rightsub auto "Movie.mkv"` |
| `translate-ollama` | **SubSwarm** | 100% offline local subtitle translation via Ollama | `rightsub translate-ollama prompts` | `rightsub translate-ollama prompts` |
| `fix-plex` | **SubRefine** | Fix BiDi, RLM, punctuation, CP1255 encoding & ads | `rightsub fix-plex ./Season1/ -r -i` | `rightsub fix-plex ./Season1/ -r -i` |
| `adjust-fps` | **SubRefine** | Stretch framerate (25.0 <-> 23.976) or shift offset | `rightsub adjust-fps in.srt -o out.srt` | `rightsub adjust-fps in.srt -o out.srt` |
| `extract` | **SubRefine** | Extract subtitle tracks from MKV/MP4 using FFmpeg | `rightsub extract video.mp4 -o out.srt` | `rightsub extract video.mp4 -o out.srt` |
| `transcribe` | **quicksubs** | On-device Speech-to-Subtitle transcription (Apple / Whisper) | `rightsub transcribe video.mp4` | `rightsub transcribe video.mp4` |
| `audio-sync` | **quicksubs** | Subtitle retiming guided by authoritative audio | `rightsub audio-sync bad.srt -v vid.mp4 -o ok.srt` | `rightsub audio-sync bad.srt -v vid.mp4 -o ok.srt` |
| `sync` | **SubRefine** | Compare timing delta between English & Hebrew SRTs | `rightsub sync master.en.srt dl.he.srt` | `rightsub sync master.en.srt dl.he.srt` |
| `bible` | **SubSwarm** | Generate Character & Terminology Bible from SRTs & TMDb | `rightsub bible Season1/*.srt -o b.json --tmdb` | `rightsub bible Season1/*.srt -o b.json --tmdb` |
| `split` | **SubSwarm** | Split master English SRT into ~210 cue JSON chunks | `rightsub split ep.en.srt -o ./batches/` | `rightsub split ep.en.srt -o ./batches/` |
| `prompt-gen` | **SubSwarm** | Generate AI translation prompt waves with Bible & Context | `rightsub prompt-gen ep.en.srt -t "Title"` | `rightsub prompt-gen ep.en.srt -t "Title"` |
| `merge` | **Both** | Assemble translated JSONs into Hebrew SRT with RLM | `rightsub merge ep.en.srt ./b/ -o ep.he.srt` | `rightsub merge ep.en.srt ./b/ -o ep.he.srt` |
| `qa` | **Both** | Zero-discrepancy 1:1 validation & gender mismatch audit | `rightsub qa ep.en.srt ep.he.srt` | `rightsub qa ep.en.srt ep.he.srt` |

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
- **Universal Multi-Lingual Homoglyph Sanitization**: Automatic neutralization and conversion of 7 foreign writing systems (Georgian, Armenian, Greek, Tibetan, Bengali, Thai, Katakana) into pure Hebrew.
- Full details in the [Boston Legal Case Study](docs/CASE_STUDY_BOSTON_LEGAL.md).

---

## 🧪 Testing & Verification

RightSub comes with a comprehensive automated test suite (69 unit tests):
```bash
pytest -v
```

Tests cover:
- BiDi trailing punctuation and RLM idempotency.
- Hebrew acronym gershayim conversion (`עו״ד`, `ארה״ב`).
- Multi-lingual homoglyph normalization (Georgian, Armenian, Greek, Arabic, Cyrillic, Asian).
- Translation Bible prompt injection & context overlap continuity.
- Direct-address vocative gender mismatch detection.
- CP1255 Windows-1255 charset detection and conversion.
- SDH auditory noise and commercial promo cleaning.
- Framerate arithmetic and time shifting.
- On-device STT CLI wrappers, fallback handlers, and audio-guided retiming algorithms.
- TMDb API metadata resolution, smart media filename parsing, and deterministic gender mapping.
- Documentation consistency, cross-platform parity, and valid link resolution.
- Live verification of all 101 episodes in the media dataset.

---

## 📚 Documentation & Guides
- 🔰 **[Quickstart for Beginners (Step-by-Step)](docs/QUICKSTART_FOR_BEGINNERS.md)** — Instant 30-second fix with zero jargon.
- 📦 **[Global Installation & Packaging Guide](docs/INSTALLATION_GUIDE.md)** — Setting up Homebrew tap, Windows installer, and PATH configuration.
- 🎙️ **[On-Device STT & Audio Alignment (`quicksubs`)](docs/QUICKSUBS_INTEGRATION.md)** — Speech-to-subtitle extraction and audio-grounded alignment.
- 🎬 **[TMDb Metadata & Entity Resolution](docs/TMDB_INTEGRATION.md)** — Deterministic gender mapping, episodic guest stars, and dialect priming.
- 🤖 **[AI Integration & Coding Assistants Guide](docs/AI_INTEGRATION_GUIDE.md)** — What needs AI vs. what runs locally, plus Antigravity, Claude Code, Gemini, and ChatGPT setups.
- 📐 **[Hebrew BiDi & Plex/Infuse Guide](docs/BIDI_AND_PLEX_GUIDE.md)** — Deep dive into invisible RLM marks and punctuation reversal.
- 🔄 **[End-to-End Pipeline Workflow](docs/PIPELINE_WORKFLOW.md)** — Step-by-step from raw video to deployed subtitles.
- ⚖️ **[RightSub vs. Bazarr Technical Comparison](docs/COMPARISON_BAZARR.md)** — Architectural breakdown, differences, and integration guide.
- 🔄 **[Home Media & Download Integrations (qBittorrent, Sonarr, Radarr, Bazarr, Daemons)](docs/INTEGRATIONS_GUIDE.md)** — Automated hands-off pipeline setups, why event hooks beat background daemons, and folder watcher scripts.
- 🔮 **[Future Interactive CLI Specification](docs/FUTURE_INTERACTIVE_CLI.md)** — Interactive CLI wizard specification and design.
- 🔮 **[Future Setup & Health-Check Wizard Specification](docs/FUTURE_SETUP_WIZARD.md)** — Autonomous clean-slate onboarding and system doctor specification.
- 🌐 **[Future MCP Server Specification](docs/FUTURE_MCP_SERVER.he.md)** — RightSub Model Context Protocol (MCP) server architecture.
- 🚀 **[What's New & Release Notes](docs/WHATS_NEW.md)** — Curated product milestone announcements and feature highlights.
- 📖 **[Official GitHub Wiki](https://github.com/omerninyo/RightSub/wiki)** — Complete bilingual online documentation.

---

## 🤝 Acknowledgements & Credits
- **[quicksubs](https://github.com/mattbirchler/quicksubs)** by **[Matt Birchler](https://birchtree.me)** — High-performance on-device macOS speech-to-text CLI engine powering local transcription and audio-guided subtitle retiming.
- **[Quick Subtitles](https://quickstuff.app)** — The companion Mac application for desktop subtitle and transcript workflows.
- **[The Movie Database (TMDb)](https://www.themoviedb.org)** — Community-built movie and TV database providing the rich metadata, cast, episodic guest star, and gender APIs (*This product uses the TMDb API but is not endorsed or certified by TMDb*).

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
