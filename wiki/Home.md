# Welcome to the RightSub Wiki

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="Home-HE"><b>עברית</b></a>
</p>

**RightSub** is a production-grade, battle-tested Python framework and CLI designed to fix, translate, synchronize, and format subtitles for **ANY movie or television series**.

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
   - **Multi-Agent Translation Waves**: Distributed parallel translation via Google Gemini 3.5 Flash-Lite.
   - **Translation Bibles**: Pre-extracts character gender, honorifics, and terminology.
   - **1-to-1 Parity Guarantee**: Zero dropped cues, zero merged timestamps, zero hallucinations.

---

## 📚 Wiki Documentation Index

- **[🔰 Quickstart for Beginners](Quickstart-for-Beginners)**: Step-by-step beginner guide with zero technical jargon (Instant Plex repair & full translation).
- **[🤖 AI Integration & Coding Assistants](AI-Integration-Guide)**: Understand what needs AI vs. what runs 100% locally, plus guides for Antigravity, Claude Code, Gemini, and ChatGPT.
- **[BiDi & Plex Formatting Guide](BiDi-and-Plex-Guide)**: Deep dive into Unicode RLM (`\u200F`), BiDi rendering levels, and why Plex flips punctuation.
- **[End-to-End Pipeline Workflow](Pipeline-Workflow)**: Step-by-step workflow from raw video file to deployed subtitles.
- **[Boston Legal Benchmark Case Study (Theoretical)](Boston-Legal-Case-Study)**: Algorithmic validation benchmark across 101 episodes and 78,000+ dialogue cues (presented strictly as a theoretical study for stress-testing and timing research).

---

## 💻 CLI Commands Reference

| Command | Engine | Description |
| :--- | :---: | :--- |
| `fix-plex` | **SubRefine** | Fix BiDi, RLM, punctuation, CP1255 encoding & ads in-place |
| `adjust-fps` | **SubRefine** | Stretch framerate (25.0 <-> 23.976) or shift offsets |
| `extract` | **SubRefine** | Extract subtitle tracks from MKV/MP4 using FFmpeg |
| `sync` | **SubRefine** | Compare timing delta between English & Hebrew SRTs |
| `bible` | **SubSwarm** | Generate Character & Terminology Bible from SRTs |
| `split` | **SubSwarm** | Split master English SRT into ~210 cue JSON chunks |
| `prompt-gen` | **SubSwarm** | Generate AI translation prompt waves for any title |
| `merge` | **Both** | Assemble translated JSONs into Hebrew SRT with RLM |
| `qa` | **Both** | Zero-discrepancy 1:1 validation report |
