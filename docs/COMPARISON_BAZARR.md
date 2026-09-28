# ⚖️ RightSub vs. Bazarr — Technical Architectural Comparison

> **Summary**: RightSub and Bazarr are not competitors. They operate at completely different stages of the media ingestion pipeline.
> **Bazarr** is a subtitle *downloader & crawler* (aggregating files from internet providers).  
> **RightSub** is a subtitle *mastering, sanitization, BiDi perfection, and multi-agent AI generation factory*.

---

## 🏛️ Architectural Comparison Matrix

| Capability / Dimension | Bazarr | RightSub |
| :--- | :--- | :--- |
| **Primary Core Role** | Scrapes and downloads existing community subtitles from 30+ internet providers (OpenSubtitles, Subscene, etc.). | Algorithmic mastering, BiDi & RLM injection, CP1255 repair, and multi-agent AI translation. |
| **Plex & Infuse BiDi Formatting** | ❌ **Unsupported**. Question marks, exclamation points, and dashes flip to the wrong side on Apple TV, Android TV, and LG WebOS. | ✔️ **SubRefine Engine**. Idempotent Right-to-Left Mark (`\u200F` / RLM) injection for 100% compliant playback across all clients. |
| **Hebrew & Arabic AI Translation** | ⚠️ **Rudimentary line-by-line machine translation** (Google Translate, DeepL, or raw Whisper) with zero episodic context. | ✔️ **SubSwarm Multi-Agent Orchestrator**. Splits episodes into ~210 cue waves with context overlap, character bibles, and 1:1 alignment guarantee. |
| **Gender-Accurate Hebrew Pronouns (`את` vs. `אתה`)** | ❌ **Blind to gender**. Generates frequent grammatical errors when translating second-person English dialogue ("You"). | ✔️ **Deterministic TMDb API Resolution**. Maps cast and episodic guest stars to guaranteed grammatical gender with zero hallucinations. |
| **Legacy Mojibake & Encoding Repair** | ⚠️ Passes through whatever encoding the provider returned (frequently unreadable CP1255 / ISO-8859-8). | ✔️ **Auto-Charset Engine**. Detects Windows-1255 / ISO-8859-8 and converts to clean UTF-8. Normalizes homoglyphs across 7 writing systems. |
| **SDH Auditory Noise & Promo Removal** | ⚠️ Basic regex replacements (often leaves broken brackets). | ✔️ **SDH & Promo Sanitizer**. Strips `[DOOR OPENS]`, `♪ Music ♪`, and release group watermark spam while preserving dialogue timing blocks. |
| **Speech-to-Text & Audio Retiming** | ⚠️ Heavy Docker Whisper process (resource intensive). | ✔️ **Native On-Device Engine (`quicksubs`)**. Leverages Apple Silicon Neural Engine or fast local Whisper with zero cloud cost. |
| **Torrent Seeding Protection (Seed-Safe)** | ❌ Modifies or replaces files directly in the media directory, risking broken torrent hash checks. | ✔️ **Seed-Safe by Default**. Duplicates non-standard files to `Movie.he.srt`, leaving original files 100% bit-for-bit intact. |
| **Automated 24/7 Web Crawling & Indexing** | ✔️ **Industry standard**. Integrates with Sonarr/Radarr and continuously crawls web providers. | ❌ Does not crawl public pirated subtitle repositories; processes local media or generates subtitles via AI. |
| **Deployment Model** | Docker container, Web GUI on port 6767, background daemon. | Native cross-platform CLI tool for **Windows** (CMD/PowerShell) and **macOS** (Terminal). |

---

## 🔍 The Core Misconception

When someone says *"Bazarr already has most of your features"*, they are confusing **Subtitle Acquisition** with **Subtitle Quality & BiDi Mastering**:

1. **Bazarr is an Ingest Tool**: If an existing Hebrew subtitle exists on OpenSubtitles or Subscene, Bazarr downloads it. However, 95% of community-uploaded Hebrew subtitles suffer from reversed punctuation on modern Smart TVs, ad spam, and legacy CP1255 character encoding. Bazarr does not fix these defects.
2. **Bazarr's "Translation" is Not Production Subtitling**: Translating movie dialogue into Semitic languages (Hebrew/Arabic) requires grammatical agreement (male/female second-person address). Machine translation without character and episodic context produces unwatchable subtitles. RightSub solves this through deterministic TMDb gender mapping and multi-agent wave chunking.

---

## 🤝 The Recommended Synergy: Bazarr + RightSub

The most effective workflow uses Bazarr for **ingest** and RightSub for **mastering**:

In Bazarr (`Settings` -> `Subtitles` -> `Post-processing` -> `Custom post-processing`):
```bash
rightsub auto "{{subtitles_path}}"
```

### Result:
1. Bazarr downloads the raw community subtitle when available.
2. RightSub immediately masters the file: injects invisible RLM for Plex, strips ads and hearing-impaired noise, converts CP1255 to UTF-8, and protects torrent seeding.
3. If Bazarr finds no subtitle, RightSub translates the video file autonomously using multi-agent AI.
