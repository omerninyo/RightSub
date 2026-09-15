# The Ultimate Subtitle Translation & Synchronization Master Prompt
> **Version**: 2.0 (High-Speed Hybrid Pipeline with BiDi/RLM Protection)  
> **Designed for**: Antigravity, Gemini, Claude, GPT-4, and Autonomous Coding Agents.

---

## MISSION STATEMENT
Translate and synchronize subtitles from English (or any source language) to Hebrew (or target language) with:
1. **Millisecond-Perfect Synchronization**: 0 time drift, 0 dropped frames, exact 1:1 line matching.
2. **Superior Cinematic Translation**: Natural, idiom-aware, speaker-gender-accurate dialogue matching legal/medical/scientific context.
3. **Flawless Player Compatibility**: Built-in bidirectional (BiDi) Right-to-Left Mark (`\u200F`) injection ensuring punctuation never reverses on Plex, Infuse, VLC, or Kodi.
4. **Extreme Resource Efficiency & Dynamic Minimum Baseline**: High-throughput execution anchored to the **Gemini >= 3.5 Flash-Lite** baseline (`Model: "flash_lite"` with ~210-item chunks). Highly cost-effective ($0.15/M tokens), zero unnecessary thinking overhead. Upgradable to future lightweight releases (3.6+, 4.x) via A/B benchmarking. NEVER use deprecated 2.x/2.5 models or expensive heavyweight tiers for bulk batches.

---

## 5-PHASE EXECUTION WORKFLOW

### PHASE 1: Source Discovery & Extraction (Universal Media Ingestion)
1. **Media & Subtitle Discovery**: Inspect video container (`.mkv`, `.mp4`, `.m4v`, `.avi`, `.ts`, `.mov`).
2. **Priority Rule (Embedded-First)**: Embedded subtitle tracks inside the video container are the **Master Ground Truth** (PTS-synchronized to video frames, zero FPS drift, official studio script).
3. **Universal Extraction**: Run `toolkit.py extract <video_or_season_dir>`: Automatically extracts the matching language track, sanitizes technical font/styling tags (`<font...>`, `{\an8}`), and writes clean `<stem>.en.srt`.
4. **Fallback to External**: If no embedded tracks exist, automatically discover external subtitles (`.srt`, `.vtt`, `.ass`) and convert to standard SRT.

### PHASE 2: Translation Bible & Character Profiling
1. Run `03_generate_bible.py` on the season or movie to detect:
   - Lead and recurring character names.
   - Genders (male / female / non-binary) and addressing forms (`אתה` / `את`).
   - Professional titles and recurring institutional jargon (e.g. `Your Honor` -> `כבוד השופט/ת`, `Objection` -> `התנגדות`, `Sustained` -> `מתקבלת`).
2. Lock this Bible into `translation_bible.json` to prevent gender switching across episodes.

### PHASE 3: Route Decision (The 3 Routes)
- **Route A (Exact Web Match)**: If a verified Hebrew subtitle exists on OpenSubtitles/Wizdom/Torec with exact line count and <250ms delta -> Adopt, verify, inject RLM, done.
- **Route B (Web Subtitle with Offset/FPS Drift)**: If a Hebrew subtitle exists but has FPS difference (23.976 vs 25) or constant offset -> Run `06_adjust_fps_or_offset.py` to stretch/shift, match to English master timestamps, inject RLM.
- **Route C (Fresh Hybrid AI Translation - Gold Standard)**:
  - Run `04_split_batches.py` to divide English SRT into batches of ~210 items.
  - Translate each batch using the dynamic minimum baseline (**Gemini >= 3.5 Flash-Lite** via `Model: "flash_lite"`, or newer lightweight generations 3.6+/4.x post A/B benchmark) with the **Batch Translation Prompt** below. Avoid expensive thinking models or deprecated 2.x/2.5.
  - Run `05_merge_and_validate.py` to assemble the final `.he.srt` with automatic RLM injection and zero-discrepancy validation.

---

## THE BATCH TRANSLATION PROMPT (For AI / Subagent)

```markdown
You are a master cinematic translator translating English dialogue into Hebrew for television/cinema subtitles.

### STRICT OPERATIONAL RULES:
1. PRESERVE EXACT JSON STRUCTURE:
   Return ONLY a valid JSON array of objects:
   [
     {"index": 1, "hebrew": "תרגום שורה ראשונה"},
     {"index": 2, "hebrew": "תרגום שורה שנייה"}
   ]
2. 1-TO-1 INDEX INTEGRITY:
   Do NOT skip, merge, or delete any index. Exactly N input items must yield N output items.
3. GENDER & TERMINOLOGY CONSISTENCY:
   Adhere strictly to the Translation Bible. Pay attention to who is speaking and to whom.
4. PUNCTUATION & ACRONYMS:
   - For Hebrew acronyms with quotes (e.g., עו"ד, ארה"ב, ת"א), use the Hebrew gershayim character (״, Unicode U+05F4) or single quotes to prevent breaking JSON strings.
   - Do NOT manually flip question marks or exclamation marks; the pipeline handles BiDi formatting.
6. CLOSED CAPTIONS & SDH CONTEXTUAL INTELLIGENCE:
   - Speaker tags (e.g. [Denny], [Alan]) and stage/audio directions (e.g. [Whispering], [Laughs], [Sarcastic]) are provided for YOUR contextual analysis. Use them to identify who is speaking, their gender, their listener, and their emotional delivery.
   - In your Hebrew output ('hebrew' field), translate ONLY the spoken dialogue. NEVER output speaker names like [דני] or sound descriptions like [מחיאות כפיים].
   - If a cue contains purely ambient sound with zero spoken dialogue (e.g. '[Music Playing]'), return an empty string "" to keep the viewer screen clean while preserving index alignment.

5. CONCISENESS & NATURAL CADENCE:
   Subtitles must be concise, punchy, and natural to read at speed. Avoid overly literal word-for-word translation.
```

---

## RED TEAM CHECKLIST & CRITICAL DEFENSES

| Threat | Cause | Automated Defense |
|---|---|---|
| **Flipped Punctuation on Plex** | LTR engine default for SRT | Auto-inject `\u200F` (RLM) before end-of-line punctuation via `05_merge_and_validate.py`. |
| **JSON Parse Failures** | Hebrew acronym quotes (`עו"ד`) | Auto-sanitization with regex replacing `"` with `״` (`\u05F4`). |
| **Dropped / Skipped Lines** | LLM hallucinations / token limits | Max batch size capped at 210 items; validator rejects any missing index. |
| **Framerate Desync (23.976 <-> 25)** | Web subtitle from PAL source | `06_adjust_fps_or_offset.py --fps_from 25.0 --fps_to 23.976`. |
| **Commercial Break Drift** | TV rip vs Web-DL gaps | Split-point sync or pure Route C translation against Web-DL master. |
| **Gender Confusion** | English gender-neutral "you" | Translation Bible consultation before translating each scene. |
