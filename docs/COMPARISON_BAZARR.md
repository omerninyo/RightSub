# ⚖️ RightSub vs. Bazarr — Technical & Code-Level Architectural Comparison

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="COMPARISON_BAZARR.he.md"><b>עברית</b></a>
</p>

---

## 📌 Executive Summary & Architectural Conclusions

A rigorous technical audit against Bazarr's official documentation ([Bazarr Subtitles Wiki](http://wiki.bazarr.media/Additional-Configuration/Settings/Subtitles/)) and its open-source GitHub repository ([`morpheus65535/bazarr`](https://github.com/morpheus65535/bazarr)) establishes an unambiguous distinction:

> **Core Architectural Conclusion**: **RightSub and Bazarr are not competitors; they operate at complementary stages of the modern media processing pipeline.**  
> - **Bazarr is a Subtitle Ingestion & Download Crawler (Web Crawler & Management UI):** It excels at monitoring TV series and movies via Sonarr/Radarr, crawling 30+ internet subtitle providers (OpenSubtitles, Subscene, etc.), and downloading existing community files.  
> - **RightSub is a Mastering, Semitic Linguistics, BiDi, and Multi-Agent AI Engine (Mastering & Intelligence Factory):** It solves the structural, typographical, and grammatical flaws inherent in community subtitles (reversed BiDi punctuation, legacy CP1255 mojibake, gender address blindness, and broken torrent seeding).

### 🔍 Key Findings from Bazarr's Source Code:
1. **Bazarr's Subtitle "Tools" Inherit Legacy Sub-Zero Code (`custom_libs/subzero/modification/mods/`):**
   - **`Reverse RTL` (`common.py`):** Performs a crude physical character swap (`\5\4\3\2`) assuming players lack Unicode BiDi support. On modern players (Plex, Apple TV, Infuse, Android TV, LG webOS), this physically corrupts rendering and completely ignores trailing question marks. RightSub injects invisible Unicode RLM (`\u200F`) marks according to Unicode UAX #9, preserving 100% logical text.
   - **`Remove HI Tags` (`hearing_impaired.py`):** The bracket removal regex is strictly confined to Latin characters (`[A-Za-zÀ-ž0-9...]`) and hardcoded to 19 English-only keywords (`LAUGH`, `MUSIC`, `DOOR`, etc.). **The code is 100% blind to Hebrew characters**, leaving tags like `[מוזיקה מתנגנת]` or `[דלת נטרקת]` untouched. RightSub features a dedicated bilingual SDH cleaner.
   - **`OCR Fixes` (`ocr_fixes.py` & `dictionaries/data.py`):** Bazarr's OCR dictionary only contains 16 Western/Slavic languages. **Hebrew (`heb`) is completely absent**. Clicking OCR Fixes on a Hebrew file logs an error and does nothing. RightSub normalizes homoglyphs across 7 scripts and executes semantic proofreading (`rightsub polish`).
   - **`Translate...` (`google_translator.py` & `gemini_translator.py`):** The Google engine scrapes line-by-line via ThreadPoolExecutor in complete isolation (zero context, zero gender). The Gemini engine sends flat 300-line batches with no context overlap, no TMDb cast gender resolution, and wraps lines in legacy Unicode 2.0 `\u202b...\u202c` (RLE/PDF) codes that cause rendering glitches with numbers. RightSub executes SubSwarm with context overlap, a locked Translation Bible, and TMDb cast gender mapping.
   - **Torrent Seeding Protection (Seed-Safe):** Bazarr modifies downloaded subtitle files in-place inside media folders, corrupting active torrent hashes in qBittorrent/Transmission. RightSub operates in Seed-Safe mode by default, cloning into `<stem>.he.srt` and leaving original files 100% bit-for-bit intact.

---

## 🏛️ Code-Level Head-to-Head Analysis

### 1. Punctuation & BiDi Directionality: `Reverse RTL` vs. `SubRefine`
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/common.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/common.py), lines 119–134):**
  ```python
  class ReverseRTL(SubtitleModification):
      identifier = "reverse_rtl"
      processors = [
          NReProcessor(re.compile(r"(?u)(^([\s.!?:,'-]*)(.+?)(\s*)(-?\s*)$)"), r"\5\4\3\2", name="CM_RTL_reverse")
      ]
  ```
  - **The Flaw:** Swaps characters physically from the beginning to the end of the line. On modern players with native Unicode BiDi rendering (Apple TV, Plex, Infuse, Android TV), this physical swap breaks dialogue dashes (`- שלום` becomes `שלום- `). Furthermore, the trailing group only matches `(-?\s*)$`, completely skipping trailing question marks (`?`) or periods (`.`).
- **In RightSub (`SubRefine`):**
  - Leaves the logical text completely unaltered.
  - Injects invisible Unicode Right-to-Left Marks (`\u200F` - RLM) adjacent to neutral punctuation and dialogue dashes according to **Unicode UAX #9**.
  - Result: 100% compliant rendering on Apple TV, Plex, Infuse, and Smart TVs without word distortion.

---

### 2. Auditory Noise Sanitization: `Remove HI Tags` vs. RightSub SDH Cleaner
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/hearing_impaired.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/hearing_impaired.py), lines 60–64):**
  ```python
  NReProcessor(re.compile(r'(?sux)-?%(t)s[\"\']*\[(?=[^\[\]]{3,})[A-Za-zÀ-ž0-9\s\'\".:-_&+]+[\)\]][\"\'*[\s:]*%(t)s' % {"t": TAG}), "", name="HI_brackets")
  ```
  - **The Flaw:** Character class `[A-Za-zÀ-ž0-9...]` strictly matches Latin characters. Hebrew Unicode codepoints (`\u0590-\u05FF`) are entirely excluded. A Hebrew cue like `[מוזיקה מתנגנת]` or `(חריקת בלמים)` is never matched and never removed.
- **In RightSub (`junk_and_sdh_cleaning.py`):**
  - Full native support for Hebrew and English auditory cues.
  - Guarded against stripping legitimate dialogue (`test_legitimate_dialogue_not_flagged_as_ad`).
  - Cleans musical notation (`♪`) and bracket noise while strictly preserving SRT cue intervals.

---

### 3. OCR and Typographical Repairs: `OCR Fixes` vs. RightSub Polish
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/ocr_fixes.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/ocr_fixes.py)):**
  ```python
  data_dict = OCR_fix_data.get(parent.language.alpha3t)
  if not data_dict:
      logger.debug("No SnR-data available for language %s", parent.language)
      return
  ```
  - **The Flaw:** Inspecting `dictionaries/data.py` reveals only 16 languages:  
    `['bos', 'dan', 'deu', 'eng', 'fin', 'fra', 'hrv', 'hun', 'nld', 'nob', 'nor', 'por', 'rus', 'spa', 'srp', 'swe']`.  
    **Hebrew (`heb`) is completely absent.** The tool logs a debug message and terminates without making any changes.
- **In RightSub (v1.3.0):**
  - **Universal Homoglyph Normalization:** Automatically fixes foreign scripts injected during bitmap OCR (e.g. Cyrillic `с` resembling Latin `c` or Hebrew characters).
  - **Semantic AI Polish (`rightsub polish`):** 3-tier domain knowledge classifier (`domain_knowledge.py`), franchise canon verification (Star Wars, Marvel, Boston Legal), and Minimal Edit Distance proofreading (85%–90% preservation target).

---

### 4. Translation Engines: `Translate...` vs. `SubSwarm`
- **In Bazarr Source Code ([`bazarr/subtitles/tools/translate/services/`](https://github.com/morpheus65535/bazarr/tree/master/bazarr/subtitles/tools/translate/services)):**
  - **Google Translator:** Scrapes Google Translate using `ThreadPoolExecutor(max_workers=10)` on isolated cues. Zero context, zero grammatical gender mapping.
  - **Gemini Translator (`gemini_translator.py`):** Sends flat 300-cue batches with a simplistic prompt. Wraps output lines in `\u202b...\u202c` (RLE/PDF) embedding marks that reverse numeric sequences and trigger rendering glitches in modern Plex players.
- **In RightSub:**
  - **Deterministic TMDb Cast Gender Mapping:** Resolves character names, genders, and plot summaries before translation begins.
  - **Context-Overlapped Wave Batches:** Passes surrounding context to prevent sentence fragmentation across cues.
  - **Translation Bible Locking:** Enforces canonical terminology and gender consistency across all season episodes.
  - **Strict Red Team QA:** Validates 1:1 index alignment, timing bounds, and grammatical gender accuracy.

---

### 5. Timing Synchronization: `Two-Point Fit...` vs. RightSub Sync Math
- **In Bazarr Source Code ([`custom_libs/subzero/modification/mods/two_point_fit.py`](https://github.com/morpheus65535/bazarr/blob/master/custom_libs/subzero/modification/mods/two_point_fit.py)):**
  ```python
  parent.f.shift(...)
  parent.f.transform_framerate(float(kwargs.get("from")), float(kwargs.get("to")))
  parent.f.shift(...)
  ```
  - **The Comparison:** The mathematical formula for linear scaling and shifting in Bazarr matches RightSub's `timing_and_sync.py`.
  - **Operational Distinction:** Bazarr requires manual GUI intervention to identify and enter sync timestamps into a modal. RightSub executes these transformations headlessly via CLI flags (`rightsub sync`) or via on-device Neural Engine STT alignment (`quicksubs`) at zero cloud cost.

---

### 6. Torrent Seeding Protection & System Footprint
- **Seed-Safe Architecture:**
  - **Bazarr:** Modifies files in-place inside download directories, breaking active torrent hashes in qBittorrent or Transmission.
  - **RightSub:** Strictly non-destructive. Clones and formats into `<stem>.he.srt` leaving the original torrent payload 100% bit-for-bit intact.
- **Resource Footprint:**
  - **Bazarr:** Continuous background daemon / Docker container running 24/7 on port 6767, consuming idle RAM and CPU cycles.
  - **RightSub:** **Zero-Daemon**. Executes purely on-demand or via completion hooks (0% idle CPU and 0 MB RAM overhead).

---

## 📊 Comprehensive Comparison Matrix (Version 1.3.0)

| Capability / Dimension | Bazarr | RightSub (v1.3.0) |
| :--- | :--- | :--- |
| **Primary Pipeline Role** | Automated web crawler & downloader for existing community subtitles (Ingest). | Mastering, Semitic linguistics, BiDi RLM, AI proofreading, and headless automation (Mastering). |
| **Plex & Infuse BiDi Handling** | ❌ Broken physical swap (`common.py`) or legacy RLE tags (`\u202b`). | ✔️ `SubRefine` engine injecting invisible Unicode RLM (`\u200F`) marks (UAX #9). |
| **Hearing Impaired / SDH Sanitization** | ❌ Latin characters only; blind to Hebrew auditory descriptions. | ✔️ Native bilingual SDH sanitizer with dialogue protection. |
| **OCR Character Repair** | ❌ Hebrew is completely missing from dictionary (`data.py`). | ✔️ Homoglyph normalization from 7 scripts + AI semantic polish. |
| **Machine Translation vs. Semantic AI** | ⚠️ Isolated cue scraping or flat Gemini batches with zero gender awareness. | ✔️ `SubSwarm` with TMDb cast resolution, context overlap, and Translation Bible. |
| **Subtitle Proofreading / Polish** | ❌ None. Cannot polish existing subtitles. | ✔️ `rightsub polish` with Minimal Edit Distance (85%–90% preservation). |
| **Torrent Seeding Protection (Seed-Safe)** | ❌ Modifies files in-place, corrupting torrent hashes. | ✔️ Non-destructive duplication to `<stem>.he.srt` (Bit-for-Bit intact). |
| **Legacy Mojibake Repair (CP1255)** | ⚠️ Passes through raw encoding from provider. | ✔️ Auto-Charset engine detecting Windows-1255 and converting to UTF-8. |
| **NAS / SMB Metadata Synchronization** | None (susceptible to macOS SMB 2001 epoch bug). | Explicit `os.utime()` metadata sync for immediate NAS indexing. |
| **Automated 24/7 Web Crawling** | ✔️ **Industry standard** (crawls 30+ providers linked to Sonarr/Radarr). | ❌ Does not crawl pirate sites; processes local files or generates subtitles via AI. |
| **System Resource Overhead** | 24/7 Docker container / background daemon (RAM/CPU). | Zero-daemon CLI running purely on event hooks (0% idle CPU, 0 MB RAM). |

---

## 🤝 The Recommended Synergy: Bazarr + RightSub

The most effective home media architecture pairs Bazarr for **ingestion** with RightSub for **mastering**:

In Bazarr (`Settings` -> `Subtitles` -> `Post-processing` -> `Custom Post-Processing`):
```bash
rightsub auto "{{subtitles_path}}"
```

### The End-to-End Workflow:
1. **Acquisition:** Bazarr monitors your media library and downloads raw community subtitles from web providers.
2. **Autonomous Mastering:** Upon download completion, RightSub wakes up for ~0.2s, injects invisible RLM marks for Plex, sanitizes SDH noise and ad spam, converts CP1255 to UTF-8, preserves torrent seeding, and flushes NAS timestamps.
3. **AI Fallback:** If Bazarr finds no subtitle on the web, RightSub can translate or polish the video stream directly using multi-agent AI at broadcast quality.
