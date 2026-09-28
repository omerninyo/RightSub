# Welcome to the RightSub Wiki

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="Home-HE"><b>עברית</b></a>
</p>

**RightSub** is a production-grade, battle-tested Python framework and CLI designed to fix, translate, synchronize, and format subtitles for **ANY movie or television series** across **Windows** and **macOS**.

---

## ⚡ Quickstart in 30 Seconds

Got an out-of-sync subtitle, reversed punctuation, or an English video you want in Hebrew? Simply run one command:

### Windows (CMD / PowerShell):
```cmd
rightsub auto "C:\Movies\Inception.he.srt"
```

### macOS / Linux (Terminal):
```bash
rightsub auto ~/Movies/Inception.he.srt
```

*Or simply type `rightsub auto ` and drag & drop any file or folder from Explorer / Finder into the terminal.*

---

## 📚 Complete Wiki Documentation

- 🔰 **[Quickstart for Beginners](Quickstart-for-Beginners)**: Step-by-step guide with zero technical jargon (Instant Plex repair & full translation).
- 📦 **[Installation & Packaging Guide](Installation-Guide)**: Homebrew tap setup, Windows installer (`install.bat`), and PATH configuration.
- 🤖 **[AI Integration & Coding Assistants](AI-Integration-Guide)**: What needs AI vs. what runs 100% locally, plus setups for Antigravity, Claude Code, Gemini, and ChatGPT.
- 📐 **[BiDi & Plex Formatting Guide](BiDi-and-Plex-Guide)**: Deep dive into Unicode RLM (`\u200F`), BiDi rendering levels, and why Plex flips punctuation.
- 🎙️ **[On-Device STT & Audio Alignment](Quicksubs-Integration)**: Local speech-to-subtitle extraction via quicksubs.
- 🎬 **[TMDb Metadata & Gender Resolution](TMDb-Integration)**: Deterministic character gender mapping and context priming.
- 🔄 **[End-to-End Pipeline Workflow](Pipeline-Workflow)**: Step-by-step workflow from raw video file to deployed subtitles.
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

## 💻 CLI Commands Reference

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
