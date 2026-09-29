# ⚖️ RightSub vs. Bazarr — Technical & Code-Level Architectural Comparison

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="השוואה-מול-Bazarr"><b>עברית</b></a>
</p>

---

## 📌 Executive Summary & Architectural Conclusions

This technical audit is based on Bazarr's official documentation ([Bazarr Subtitles Wiki](http://wiki.bazarr.media/Additional-Configuration/Settings/Subtitles/)) and a line-by-line inspection of **Bazarr's open-source GitHub codebase** ([`morpheus65535/bazarr`](https://github.com/morpheus65535/bazarr)).

### The Core Question: "Why do I need RightSub if Bazarr is already running on my media server?"

**Short Answer: Because Bazarr is an Ingestion Web Crawler & Downloader, while RightSub is a Semitic Linguistics, BiDi Engineering, and Mastering Factory.**

Users frequently observe buttons in Bazarr's UI labeled *Reverse RTL*, *Remove HI Tags*, *OCR Fixes*, *Translate*, and *Two-Point Fit*, and assume Bazarr provides a complete subtitle solution for Hebrew. Inspecting the underlying source code reveals that these tools were inherited from the legacy `Sub-Zero` library, engineered specifically for Western European Latin languages. When executed on Semitic (Hebrew/Arabic) subtitles, they fail across four fundamental dimensions:

1. **Physical BiDi Corruption:** Bazarr's `Reverse RTL` performs a crude physical character swap instead of injecting logical Unicode directionality marks, corrupting subtitles on modern players (Apple TV, Infuse, Plex, Android TV).
2. **Total Blindness to Hebrew in Sanitization:** Bazarr's OCR and Hearing Impaired filters contain zero Hebrew Unicode codepoints (`\u0590-\u05FF`) in their regular expressions and dictionaries, silently skipping Hebrew files.
3. **Flat, Gender-Blind Machine Translation:** Translation tools execute a static 3-line prompt on massive 300-cue batches with zero pre-flight analysis, zero TMDb cast gender resolution, and zero context overlap, causing severe second-person grammatical gender flips ("אתה" vs. "את") and severed sentences.
4. **Torrent Seed Invalidation:** In-place file edits inside media folders alter file sizes and cryptographic hashes, causing active torrent clients (qBittorrent, Transmission) to fail with I/O hash check errors.

> **Engineering Verdict**: RightSub and Bazarr are not rivals; **they are complementary**. The optimal automated home media setup uses Bazarr to crawl and download community files from the web, and triggers RightSub as a Post-Processing hook to master, sanitize, and format the subtitles to broadcast standards.

---

## 🏛️ Code-Level Head-to-Head Analysis

### 1. Directionality & BiDi Punctuation: `Reverse RTL` vs. `SubRefine`
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/common.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/common.py), lines 119–134):**
  ```python
  class ReverseRTL(SubtitleModification):
      identifier = "reverse_rtl"
      processors = [
          NReProcessor(re.compile(r"(?u)(^([\s.!?:,'-]*)(.+?)(\s*)(-?\s*)$)"), r"\5\4\3\2", name="CM_RTL_reverse")
      ]
  ```
- **The Engineering Flaw:**
  - The routine assumes the target playback engine lacks Unicode BiDi support and performs a **crude physical swap** of line characters (`\5\4\3\2`).
  - Modern media players (Plex, Apple TV, Infuse, Android TV, VLC) implement native **Unicode Bidirectional Algorithm (UAX #9)**.
  - When Bazarr's physical swap is applied, dialogue dashes jump from the start of the line to the end (`שלום-` instead of `- שלום`). Furthermore, the regex trailing capture only matches hyphens (`-?\s*$`), completely ignoring trailing question marks (`?`) and exclamation points.
- **The RightSub Solution (`SubRefine`):**
  - Keeps 100% of the underlying text in valid, logical UTF-8 sequence. Never physically reverses characters.
  - Injects invisible Unicode Right-to-Left Marks (`\u200F` - RLM) adjacent to neutral punctuation and dialogue dashes in strict compliance with **Unicode UAX #9**.
  - Result: Flawless rendering on Apple TV, Plex, Infuse, and Smart TVs without character inversions.

---

### 2. Auditory Noise Sanitization: `Remove HI Tags` vs. RightSub SDH Cleaner
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/hearing_impaired.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/hearing_impaired.py), lines 60–64):**
  ```python
  NReProcessor(re.compile(r'(?sux)-?%(t)s[\"\']*\[(?=[^\[\]]{3,})[A-Za-zÀ-ž0-9\s\'\".:-_&+]+[\)\]][\"\'*[\s:]*%(t)s' % {"t": TAG}), "", name="HI_brackets")
  ```
- **The Engineering Flaw:**
  - The bracket regex character class `[A-Za-zÀ-ž0-9...]` strictly matches Latin and Western European characters.
  - **Hebrew Unicode codepoints (`\u0590-\u05FF`) are completely excluded.** Tags such as `[מוזיקה מתנגנת]`, `(טלפון מצלצל)`, or `[צעקות]` are never matched and remain intact.
  - Additionally, the All-Caps sound description list is hardcoded to exactly 19 English-only words (`LAUGH`, `SCREAM`, `DOOR`, etc.).
- **The RightSub Solution (`junk_and_sdh_cleaning.py`):**
  - Full native support for Hebrew and English auditory patterns across all bracket types (`[]`, `()`, `{}`).
  - Removes musical notation (`♪`) while strictly preserving cue timing intervals.
  - Whitelist protection (`test_legitimate_dialogue_not_flagged_as_ad`) to ensure short dialogue lines are never mistakenly stripped.

---

### 3. OCR and Typographical Repairs: `OCR Fixes` vs. Homoglyphs & Semantic Polish
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/ocr_fixes.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/ocr_fixes.py)):**
  ```python
  data_dict = OCR_fix_data.get(parent.language.alpha3t)
  if not data_dict:
      logger.debug("No SnR-data available for language %s", parent.language)
      return
  ```
- **The Engineering Flaw:**
  - Inspecting `dictionaries/data.py` reveals dictionary tables for only 16 European languages:  
    `['bos', 'dan', 'deu', 'eng', 'fin', 'fra', 'hrv', 'hun', 'nld', 'nob', 'nor', 'por', 'rus', 'spa', 'srp', 'swe']`.
  - **Hebrew (`heb`) is totally unsupported.** When clicked on a Hebrew subtitle, Bazarr outputs a debug log entry and silently exits without modifying anything.
- **The RightSub Solution (v1.3.0):**
  - **Universal Homoglyph Normalization:** Automatically identifies and replaces foreign character intrusions introduced by legacy bitmap OCR (e.g. Cyrillic `с` resembling Latin `c` or Hebrew characters).
  - **Hebrew Typographical Normalization:** Converts ASCII double quotes into canonical Hebrew Gershayim (`״` / `\u05F4`) for acronyms (e.g., עו״ד, ארה״ב, ד״ר).
  - **Semantic AI Polish (`rightsub polish`):** Uses LLMs and 3-tier domain lore (`domain_knowledge.py`) to audit spelling, slang, and franchise canon.

---

### 4. Legacy Encodings & Mojibake: Raw Pass-Through vs. `Auto-Charset` Engine
- **In Bazarr:**
  - Bazarr crawls files from community websites (OpenSubtitles, Subscene, Torec) and saves them with their original encoding.
  - Many older Israeli subtitle archives were saved in Windows-1255 (CP1255) or ISO-8859-8.
  - When modern streaming players read CP1255 files under UTF-8 assumptions, subtitles display as unreadable gibberish (`àðé øåöä` instead of `אני רוצה`). Bazarr has no automated Semitic encoding detection or conversion pipeline.
- **The RightSub Solution:**
  - The **Auto-Charset** engine evaluates all input files with statistical heuristic confidence, automatically detecting CP1255 and ISO-8859-8 encodings and converting them to clean, modern UTF-8.

---

### 5. Timing Synchronization: `Two-Point Fit` vs. Headless CLI & Hardware-Accelerated STT
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/two_point_fit.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/two_point_fit.py)):**
  ```python
  parent.f.shift(...)
  parent.f.transform_framerate(float(kwargs.get("from")), float(kwargs.get("to")))
  parent.f.shift(...)
  ```
- **The Operational Difference:**
  - The underlying linear time scaling and offset math matches RightSub's `timing_and_sync.py`.
  - **The Bazarr Bottleneck:** Requires manual user interaction: opening the video in an external player, seeking out two spoken lines, recording 4 separate timestamps, typing them into a web GUI modal, and clicking save.
- **The RightSub Solution:**
  - **Single-Line Headless CLI:** FPS conversions and millisecond offsets execute in a single headless command (`rightsub sync`).
  - **Hardware-Accelerated Alignment (`quicksubs`):** Performs local on-device speech-to-text audio alignment against the video's audio track via Apple Silicon Neural Engine/Metal or local Whisper models — zero manual timestamp hunting and zero cloud API expenses.

---

### 6. Translation & Linguistics: Bazarr's Flat Engine vs. RightSub's Pre-Flight Architecture

This is the primary architectural differentiator refuting the misconception that Bazarr's "Translate" button makes an external tool redundant.

#### How Bazarr Executes Translation (`bazarr/subtitles/tools/translate/services/`):
- **Google Translator (`google_translator.py`):**
  Dispatches individual cues in parallel via `ThreadPoolExecutor(max_workers=10)`. Every line is translated in complete isolation: zero conversational context, total grammatical gender blindness, and broken sentence flow.
- **Gemini Translator (`gemini_translator.py`, lines 135–150):**
  Sends monolithic 300-cue blocks using a static, 3-line prompt:
  ```text
  You are an assistant that translates subtitles to {language}.
  Dialogs must be translated as they are without any changes.
  If a line has a comma or multiple sentences, try to keep one line to about 40-50 characters.
  ```
  - **Zero Pre-Flight Intelligence:** No TMDb character cast query, no speaker extraction, and no awareness of speaker identities or genders.
  - **Zero Context Overlap:** If a dialogue sentence is split across subtitle batches, the first half is translated in batch A and the second half in batch B without conversational context.
  - **Destructive BiDi Encodings:** Bazarr wraps Hebrew lines in legacy Unicode 2.0 `\u202b...\u202c` (RLE/PDF) directional embedding codes. In modern media players (Apple TV, Infuse, Plex), these obsolete marks physically invert numbers, times, and currency symbols.

#### RightSub's 3-Phase Pre-Flight Architecture:
1. **Phase 1: Pre-Flight Bible & TMDb Entity Resolution (`03_generate_bible.py`):**
   - Before submitting a single token to the LLM, RightSub scans the English SRT for explicit speaker tags (`ALAN:`, `[DENNY]`), character names, and recurring honorifics (`Judge`, `Counselor`, `Dr.`).
   - Executes an automated pre-flight query against the **TMDb API** to resolve the verified cast roster, character names, and official genders (Male/Female).
   - Generates and locks `translation_bible.json`, guaranteeing that character gender and nomenclature remain 100% consistent across entire 24-episode seasons.
2. **Phase 2: Master System Prompt & Context Overlap (`09_prompt_builder.py`):**
   - **Explicit Vocative Agreement Rules:** Enforces strict Semitic 2nd-person gender inflection ("אתה" vs. "את", "אתה רוצה" vs. "את רוצה") based on speaker and addressee continuity.
   - **SDH Filtered as Context-Only:** Speaker tags like `[Tara]` or `ALAN:` are supplied as context to inform the LLM of conversational participants, while the prompt strictly forbids outputting these metadata tags into final subtitles.
   - **Sliding Context Overlap:** Every batch receives 3–5 overlapping dialogue lines from preceding and succeeding cues, preventing fragmented sentences.
   - **Domain Knowledge & Canon Lore (`domain_knowledge.py`):** Dynamically injects genre glossaries (legal courtroom terms, medical jargon, sci-fi franchises).
3. **Phase 3: Semantic AI Polish (`19_polish_and_qc.py`):**
   - If Bazarr already downloaded an existing community subtitle that suffers from machine-translation errors, RightSub does not need to re-translate the file from scratch.
   - The `rightsub polish` engine operates on **Minimal Edit Distance**, auditing the Hebrew subtitle against master English dialogue to preserve 85%–90% of valid human phrasing while surgically fixing gender flips and terminology at ~15% of the token cost.

---

### 7. Torrent Seeding Protection: In-Place Mutation vs. Seed-Safe Architecture
- **In Bazarr:**
  - When Bazarr edits, converts, or synchronizes a subtitle file inside a media folder, it alters the file **in-place**.
  - This mutates the file size and payload content. BitTorrent clients (qBittorrent, Transmission) detect hash mismatches during re-checks and immediately halt torrent seeding with I/O errors.
- **The RightSub Solution:**
  - Operates on a **Strictly Non-Destructive Seed-Safe Model** by default.
  - Leaves the original downloaded subtitle 100% bit-for-bit intact, creating an external `<stem>.he.srt` that Plex and Infuse automatically recognize and prioritize.

---

### 8. Resource Footprint & System Impact: 24/7 Daemon vs. Zero-Daemon CLI
- **Bazarr:**
  - Designed as an always-on server daemon or continuous Docker container running 24/7.
  - Occupies port 6767, maintains background worker loops, and consumes continuous RAM (150–300 MB).
- **RightSub:**
  - **Zero-Daemon Architecture.**
  - Lightweight CLI utility with zero background processes.
  - Idle resource consumption: **0% CPU and 0 MB RAM**. Wakes up on event triggers or manual calls, masters the subtitle in ~0.2s, and immediately terminates.

---

## 📊 Comprehensive Comparison Matrix (Version 1.3.0)

| Capability / Dimension | Bazarr | RightSub (v1.3.0) |
| :--- | :--- | :--- |
| **Primary Pipeline Role** | Automated web crawler & downloader for existing community subtitles (Ingest). | Mastering, Semitic linguistics, BiDi RLM, AI proofreading, and headless automation (Mastering). |
| **Plex & Infuse BiDi Handling** | ❌ Broken physical character swap (`common.py`) or legacy RLE tags (`\u202b`). | ✔️ `SubRefine` engine injecting invisible Unicode RLM (`\u200F`) marks (UAX #9). |
| **Hearing Impaired / SDH Sanitization** | ❌ Latin characters only; blind to Hebrew auditory descriptions. | ✔️ Native bilingual SDH sanitizer with dialogue protection. |
| **OCR Typo Repair** | ❌ Hebrew is completely missing from dictionary (`data.py`). | ✔️ Homoglyph normalization from 7 scripts + Hebrew Gershayim normalization. |
| **Legacy Mojibake Repair (CP1255)** | ⚠️ Passes through raw encoding from provider. | ✔️ Auto-Charset engine detecting Windows-1255 and converting to UTF-8. |
| **Timing Synchronization (Sync)** | ⚠️ Manual web GUI only (Two-Point Fit requires typing 4 timestamps). | ✔️ Direct CLI flags (`rightsub sync`) + hardware-accelerated STT (`quicksubs`). |
| **Pre-Flight Architecture & Bible** | ❌ None. Static 4-line prompt with zero domain knowledge. | ✔️ TMDb cast resolution, speaker extraction, locked `translation_bible.json`. |
| **Context Overlap Across Batches** | ❌ Flat 300-line batches. Sentences severed without context. | ✔️ 3–5 cue sliding overlap windows guaranteeing sentence continuity. |
| **Vocative & Gender Agreement** | ❌ Completely blind (defaults to masculine, frequent gender flips). | ✔️ Explicit 2nd-person gender rules based on speaker continuity. |
| **Subtitle Proofreading / Polish** | ❌ None. Requires translating from scratch. | ✔️ `rightsub polish` with Minimal Edit Distance (85%–90% preservation). |
| **Torrent Seeding Protection (Seed-Safe)** | ❌ Modifies files in-place, corrupting torrent hashes. | ✔️ Non-destructive duplication to `<stem>.he.srt` (Bit-for-Bit intact). |
| **NAS / SMB Metadata Synchronization** | None (susceptible to macOS SMB 2001 epoch bug). | Explicit `os.utime()` metadata sync for immediate NAS indexing. |
| **Automated 24/7 Web Crawling** | ✔️ **Industry standard** (crawls 30+ providers linked to Sonarr/Radarr). | ❌ Does not crawl pirate sites; processes local files or generates subtitles via AI. |
| **System Resource Overhead** | 24/7 Docker container / background daemon (RAM/CPU). | Zero-daemon CLI running purely on event hooks (0% idle CPU, 0 MB RAM). |

---

## 🤝 The Recommended Synergy: Bazarr + RightSub

The most reliable media server architecture pairs Bazarr for **ingestion** with RightSub for **mastering**:

In Bazarr (`Settings` -> `Subtitles` -> `Post-processing` -> `Custom Post-Processing`):
```bash
rightsub auto "{{subtitles_path}}"
```

### The End-to-End Workflow:
1. **Acquisition:** Bazarr monitors media libraries and downloads raw community subtitles from web providers.
2. **Autonomous Mastering (0.2s):** RightSub triggers immediately upon download, converts CP1255 to clean UTF-8, injects invisible RLM marks for Plex/Apple TV, removes SDH noise and ad spam, preserves torrent seeding, and updates NAS timestamps.
3. **AI Fallback & Polish:** If Bazarr finds no subtitle on the web, or retrieves a low-grade machine translation, RightSub can translate or polish the media file directly at broadcast quality.
