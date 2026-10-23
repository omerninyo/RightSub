# Boston Legal (Seasons 1–5) - Complete Hebrew Subtitles Master Walkthrough (Theoretical Case Study)

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="CASE_STUDY_BOSTON_LEGAL.he.md"><b>עברית</b></a>
</p>

> [!NOTE]
> **Legal Disclaimer & Theoretical Benchmark Notice:**
> The following documentation details a hypothetical, theoretical case study and synthetic benchmark used exclusively for algorithmic stress-testing, timing synchronization research, and software demonstration purposes.
> All title names, character names, trademarks, and copyrights belong entirely to their respective copyright holders (20th Century Fox / Disney, David E. Kelley Productions). No copyrighted video files, audio tracks, or proprietary media assets are included, hosted, or distributed within this repository or software.

All **101 episodes** across all **5 seasons** of the critically acclaimed legal comedy-drama **"Boston Legal"** were modeled, synchronized, BiDi-formatted (with RLM injection for Plex & Infuse), quality-assured, and verified.

---

## 📊 Complete Series Summary Statistics

| Season | Total Episodes | Completed Episodes | Completion % | Original Backup (`.bak.v25`) | 1:1 Timing Sync | Plex / Infuse BiDi (RLM) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Season 1** | 17 | 17 | **100.0%** | 17 / 17 Verified | 100% Matched | Applied |
| **Season 2** | 27 | 27 | **100.0%** | 27 / 27 Verified | 100% Matched | Applied |
| **Season 3** | 24 | 24 | **100.0%** | 24 / 24 Verified | 100% Matched | Applied |
| **Season 4** | 20 | 20 | **100.0%** | 20 / 20 Verified | 100% Matched | Applied |
| **Season 5** | 13 | 13 | **100.0%** | 13 / 13 Verified | 100% Matched | Applied |
| **TOTAL** | **101** | **101** | **100.0%** | **101 / 101 Backed Up** | **100% (0 Mismatches)** | **100% Compliant** |

---

## 🎬 Season 4 Final Episodes Detail

Season 4 represents the emotional and ideological peak of the series, culminating in Denny and Alan's monumental courtroom clash and friendship reconciliation:

| Episode | Title | Cues | Waves / Agents | Model | Backup File | Final Output | Status |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| **S04E18** | Indecent Proposals | 769 | 2 waves (8 agents) | Gemini 3.5 Flash-Lite | `Season 4/Boston Legal S04E18.he.srt.bak.v25` | `Season 4/Boston Legal S04E18.he.srt` | **100% Deployed** |
| **S04E19** | The Gods Must Be Crazy | 706 | 2 waves (8 agents) | Gemini 3.5 Flash-Lite | `Season 4/Boston Legal S04E19.he.srt.bak.v25` | `Season 4/Boston Legal S04E19.he.srt` | **100% Deployed** |
| **S04E20** | Patriot Acts (Season Finale) | 695 | 2 waves (8 agents) | Gemini 3.5 Flash-Lite | `Season 4/Boston Legal S04E20.he.srt.bak.v25` | `Season 4/Boston Legal S04E20.he.srt` | **100% Deployed** |

---

## 🛠️ Architecture, Engineering & Tooling Documentation

### 1. RightSub Architecture (SubRefine & SubSwarm)
- **`split`**: Decomposes long English SRT files into chunked JSON batches (approx. 210 cues each) mapped through a `manifest.json`.
- **`merge`**: Assembles translated Hebrew batches back into standard `.srt` format, strictly maintaining original timestamps and block IDs.
- **BiDi Engine**: Automatically injects invisible Right-to-Left Marks (`\u200F` / RLM) at the start of every text line, ensuring proper punctuation and numeral display in Plex, Infuse, VLC, and Apple TV.

### 2. High-Throughput Autonomous AI Agent Architecture
- **Model Engine**: **Gemini 3.5 Flash-Lite** (`Model: "flash_lite"`).
- **Orchestration**: Concurrent waves of 4 autonomous subagents per wave, completing 700–900 cues in under 2 minutes per episode.
- **Context Injection**: Each agent receives rich episode context, character backgrounds (Denny Crane, Alan Shore, Shirley Schmidt, Jerry Espenson, Carl Sack), legal lexicon, and strict character constraints.

### 3. Algorithmic Memory, Anchor-Verified Reconciliation & 3-Stage Canonical BiDi
- **3-Stage Canonical BiDi & Un-Flipping Engine (`07_fix_plex_punctuation.py`)**: Wraps every line's logical core with leading `\u200F` and trailing `\u200F` **after** trailing punctuation (`\u200Fטקסט!\u200F`) in compliance with Unicode UAX #9 Rule N1, and reverses 18 legacy visual-flipping patterns benchmarked across 20,299 subtitle files (`15,630,175` Hebrew lines).
- **Homoglyph-Conditional Final-Letter Normalization**: Converts visually identical Cyrillic and Arabic homoglyphs to Hebrew and only runs final-letter (`מ` $\rightarrow$ `ם`, `פ` $\rightarrow$ `ף`) normalization when a foreign homoglyph was actually replaced, protecting hesitation tokens (`אממ`, `הממ`, `מממ`), loanwords (`טרמפ`, `ג'יפ`), and vocalized `אִמם` ($\rightarrow$ `אימם`).
- **Anchor-Verified Best-of-Both Reconciliation (`validate_anchor_alignment`)**: Reconciles high-tier `.bak.v25` translations with surgical female-judge and vocative gender fixes across all 101 episodes, eliminating all 13 `Cue Drift` windows (`0` shifted windows across all 101 episodes) and repairing 185 corrupted final-letter tokens.
- **Typography & SDH Stripping**: Enforces Hebrew gershayim (`״` / `\u05F4`) for acronyms (`עו״ד`, `ארה״ב`, `FDA`), strips hearing-impaired noise descriptors while preserving legitimate bracketed dialogue, and removes multi-line promotional credits while strictly preserving 1:1 timing block index alignment.

### 4. Safety & Verification (Definition of Done)
1. **Safety First**: Before overwriting any `.he.srt`, the original file is preserved under `.he.srt.bak.v25`.
2. **1-to-1 Timing & Zero Cue Drift Verification**: Automated QA checks verify that every cue index, timing range, and 25-cue anchor window (`?`, `♪`, numerals) matches the English master file (`assert len(en) == len(he)` and `0` shifted drift windows).
3. **Zero Gender & Morphological Mismatches**: Verified across all 101 episodes via `08_quality_assurance.py` (leading and trailing vocatives, female judges, and internal morphological consistency).
4. **Master Skill Reference**: Full operational standards and instructions are codified in `SKILL.md` (and the `subtitle-translator` AI skill).

