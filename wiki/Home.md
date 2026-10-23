# Welcome to the RightSub Wiki

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="Home-HE"><b>עברית</b></a>
</p>

**RightSub** is a production-grade, battle-tested Python framework and CLI designed to fix, translate, synchronize, and format subtitles for **ANY movie or television series** across **Windows** and **macOS**.

---

## ⚡ Quickstart in 30 Seconds

Got an out-of-sync subtitle, reversed punctuation, or an English video you want in Hebrew? You have three effortless options in **RightSub v1.5.0**:

1. **Interactive Mastering Wizard (Zero Flags):** Simply type `rightsub` with no arguments to open the guided interactive menu with Drag & Drop and a built-in file browser (`[B] Browse`).
2. **One-Command Autonomous Runner (`rightsub auto`):**
   - **Windows (CMD / PowerShell):** `rightsub auto "C:\Movies\Inception.srt"`
   - **macOS / Linux (Terminal):** `rightsub auto ~/Movies/Inception.srt`
3. **1-Click Native MCP Server for AI Agents:** Run `rightsub mcp --install` to connect **Google Antigravity**, **Claude Desktop**, **Cursor**, **Windsurf**, and **Claude Code**.

---

## 📚 Complete Wiki Documentation

- 🔰 **[Quickstart for Beginners](Quickstart-for-Beginners)**: Step-by-step guide with zero technical jargon (Interactive Wizard, instant Plex repair & full translation).
- 📦 **[Installation & Packaging Guide](Installation-Guide)**: Homebrew tap setup, Windows installer (`install.bat`), `rightsub setup`, and `rightsub mcp --install`.
- 🤖 **[AI Integration & Coding Assistants](AI-Integration-Guide)**: Native MCP Server (`rightsub mcp`), what needs AI (`0` tokens for 99% of repairs) vs. full translation.
- 📐 **[BiDi & Plex Formatting Guide](BiDi-and-Plex-Guide)**: Deep dive into Unicode RLM (`\u200F`), UAX #9 Rule N1, and un-flipping 18 legacy visual-flip patterns.
- 💎 **[Semantic AI Polish & QC Specification](Semantic-AI-Polish-and-QC)**: Proofreading, bilingual number un-flipping, and `--interactive` line-by-line diff review.
- 🔄 **[Home Media & Download Integrations](Integrations-Guide)**: Turnkey automation for qBittorrent, Sonarr, Radarr, Bazarr, Transmission, and Docker (`rightsub serve`).
- ⚖️ **[RightSub vs. Bazarr Comparison](Bazarr-Comparison)**: Code-level architectural comparison and recommended synergy.
- 🎙️ **[On-Device STT & Audio Alignment](Quicksubs-Integration)**: Local speech-to-subtitle extraction via quicksubs.
- 🎬 **[TMDb Metadata & Gender Resolution](TMDb-Integration)**: Deterministic character gender mapping and context priming.
- 🔄 **[End-to-End Pipeline Workflow](Pipeline-Workflow)**: Step-by-step workflow from raw video file to deployed subtitles.
- 🗺️ **[Product Roadmap](Roadmap)** & 🚀 **[What's New (`v1.5.0`)](Whats-New)**: Release history and milestone tracking.
- 🏆 **[Boston Legal Benchmark Case Study (Theoretical)](Boston-Legal-Case-Study)**: Algorithmic validation benchmark across 101 episodes and 78,000+ dialogue cues.

---

## 🏛️ Two Core Engines

RightSub separates user-facing CLI operations from its two underlying algorithmic engines:

1. **SubRefine Engine**:
   - **Plex & Infuse BiDi / RLM**: Fixes reversed punctuation and RTL dialogue dashes on Apple TV, Android TV, Infuse, and VLC.
   - **SDH Cleaner**: Strips auditory descriptors (`[DOOR CREAKS]`, `(LAUGHTER)`) while preserving dialogue cues.
   - **Charset Conversion**: Detects legacy Windows-1255 / CP1255 / ISO-8859-8 encodings and converts them into UTF-8.
   - **Homoglyph & Typography Repair**: Normalizes Cyrillic and Arabic lookalike glyphs and converts standard quotes in Hebrew acronyms to typographic gershayim (`עו״ד`, `ארה״ב`).
   - **Framerate & Sync**: Auto-stretches 25.0 FPS <-> 23.976 FPS and aligns timing.

2. **SubSwarm Engine**:
   - **Multi-Agent Translation Waves**: Distributed parallel translation via Google Gemini 3.5 Flash-Lite or local Ollama.
   - **Translation Bibles**: Pre-extracts character gender, honorifics, and terminology via TMDb.
   - **1-to-1 Parity Guarantee**: Zero dropped cues, zero merged timestamps, zero hallucinations.

---

## 💻 CLI Commands Reference (`v1.5.0`)

| Command | Engine | Description | Windows Example | macOS / Linux Example |
| :--- | :---: | :--- | :--- | :--- |
| `rightsub` *(no args)* / `wizard` | **TUI** | Interactive Mastering Wizard (Drag & Drop + File Browser) | `rightsub` | `rightsub` |
| `setup` | **Core** | First-Time Setup, Downloader Hooks & Background Service Wizard | `rightsub setup` | `rightsub setup` |
| `mcp` | **MCP** | Native JSON-RPC 2.0 MCP Server & Multi-Agent Auto-Installer | `rightsub mcp --install` | `rightsub mcp --install` |
| `auto` | **All** | Zero-flag autonomous runner for files, seasons, or directories | `rightsub auto "Movie.mkv"` | `rightsub auto "Movie.mkv"` |
| `polish` | **Both** | Semantic AI proofreading, canon/number fix & `--interactive` review | `rightsub polish "Movie.he.srt" -i` | `rightsub polish "Movie.he.srt" -i` |
| `serve` | **Daemon** | Container & Host Webhook Daemon for Sonarr, Radarr & Bazarr | `rightsub serve --port 8775` | `rightsub serve --port 8775` |
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
| `config` | **Core** | API key onboarding, downloader hooks (`--install-hooks`) & services | `rightsub config --install-hooks` | `rightsub config --install-hooks` |
| `doctor` | **Core** | System diagnostics & health check for dependencies & MCP agents | `rightsub doctor` | `rightsub doctor` |
| `merge` | **Both** | Assemble translated JSONs into Hebrew SRT with RLM | `rightsub merge ep.en.srt ./b/ -o ep.he.srt` | `rightsub merge ep.en.srt ./b/ -o ep.he.srt` |
| `qa` | **Both** | Zero-discrepancy 1:1 validation & gender mismatch audit | `rightsub qa ep.en.srt ep.he.srt` | `rightsub qa ep.en.srt ep.he.srt` |
