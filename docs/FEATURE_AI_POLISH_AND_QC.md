# 💎 Architectural Specification: Semantic AI Polish & Subtitle QC Engine (`rightsub polish`)

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="FEATURE_AI_POLISH_AND_QC.he.md"><b>עברית</b></a>
</p>

This document specifies the architectural design, data contracts, CLI interface, and execution workflow for the future **Semantic AI Polish & Subtitle QC Engine** in RightSub: the `rightsub polish` (or `rightsub qc-ai`) command.

The goal of this engine is to proofread, polish, and modernize existing Hebrew subtitles (legacy releases, imperfect human translations, or raw machine drafts — such as community scans like *Star Wars 4K77*) **without re-translating the entire movie from scratch**, correcting canon drift, gender agreement errors, and literal idioms while strictly preserving quality human phrasing.

---

## 1. Problem Statement & Engineering Motivation

Tens of thousands of community-uploaded Hebrew subtitle files exist for classic films and series. In 85%–90% of cases, the dialogue timing is accurate and basic phrasing is serviceable, yet they suffer from three pervasive semantic defects:
1. **Franchise & Canon Terminology Drift:** Inconsistent or obsolete translations of lore terms (e.g. translating "Lightsaber" as "Laser Sword" / *"חרב לייזר"*, or omitting military ranks like "Grand Moff").
2. **Grammatical Gender Flipping:** Second-person English dialogue ("You") translated into masculine Hebrew verbs even when addressing female characters (e.g. Han or Luke addressing Princess Leia with masculine verbs).
3. **Anachronistic Registers & Literal Idiom Translation:** Idiomatic expressions translated word-for-word, resulting in unnatural dialogue (e.g. *"I have a bad feeling about this"* translated literally instead of natural Hebrew cinematic prose).

Re-translating the entire film with an LLM burns unnecessary tokens, risks hallucinating or discarding authentic human dialogue choices, and can introduce timing drift. **The Polish Engine operates on the principle of Minimal Edit Distance.**

---

## 2. RightSub Subtitle Operation Comparison

| Command | Primary Role | Modifies Text? | Uses AI? | Token Cost |
| :--- | :--- | :---: | :---: | :---: |
| `rightsub fix-plex` | Algorithmic BiDi (RLM), CP1255 recovery, and ad cleaning. | ❌ No | ❌ No | 0 |
| `rightsub qa` | Deterministic verification of line counts, timing, and homoglyphs. | ❌ Audit report only | ❌ No | 0 |
| `rightsub auto` | Autonomous runner (extracts, fixes Plex, or translates from scratch). | ✔️ Full (if translating) | ✔️ Yes (if needed) | 100% |
| **`rightsub polish`** | **Proofreading, semantic gender correction & canon harmonization.** | **✔️ Selective fixes only** | **✔️ Yes (QC Reviewer)** | **~15%–20%** |

---

## 3. CLI Command Interface

```bash
# Review and polish an existing Hebrew subtitle against master English:
rightsub polish "Star Wars (1977).he.srt" --en "Star Wars (1977).en.srt"

# Query TMDb by specific ID for cast rosters and franchise canon:
rightsub polish "Gladiator.he.srt" --en "Gladiator.en.srt" --tmdb-id 98

# Run locally and 100% offline via Ollama:
rightsub polish "Movie.he.srt" --en "Movie.en.srt" --ollama --model qwen2.5:7b

# Dry run / Audit mode: generate a change report without modifying the subtitle file:
rightsub polish "Movie.he.srt" --en "Movie.en.srt" --diff-only
```

---

## 4. Pipeline Architecture

```text
[Movie.en.srt] ──┐
                 ├──> [1. Bilingual Cue Alignment] ──> [2. TMDb Lore & Gender Ingestion]
[Movie.he.srt] ──┘                                                    │
                                                                      ▼
[Master: Movie.he.polished.srt] <── [4. RLM & BiDi Enforcement] <─── [3. Constrained AI Polish Prompt]
                 │
                 └──> [5. Markdown Diff Report: Movie_polish_diff.md]
```

### Stage 1: Bilingual Cue Alignment
Pairs each English cue with its corresponding Hebrew cue based on timestamp intervals and sequence indexes:
```json
{
  "index": 142,
  "timing": "00:18:22,100 --> 00:18:24,800",
  "en": "Your father's lightsaber. This is the weapon of a Jedi Knight.",
  "current_he": "חרב הלייזר של אביך. זה הנשק של אביר ג'דיי."
}
```

### Stage 2: TMDb Lore & Gender Ingestion
Extracts verified character genders from the TMDb API and injects domain-specific glossaries for recognized franchises (Star Wars, Lord of the Rings, Harry Potter, Marvel Cinematic Universe).

### Stage 3: Constrained Polish Prompt Contract
Instructs the LLM to act strictly as a professional subtitling editor:
1. **The Conservation Rule:** If the current Hebrew line is accurate, natural, and grammatically correct — **do not touch it**.
2. **Canon Correction:** Align character names and established franchise terms to accepted modern canon.
3. **Gender Agreement:** Align second- and third-person pronouns with the confirmed speaker and addressee.
4. **Flow & Syntax Modernization:** Untangle awkward literal translations into natural cinematic dialogue.
5. **Subtitle Constraints:** Strict limit of 38–40 characters per line, maximum 2 lines per block.

### Stage 4: Structured AI Response Schema
The LLM returns only the cues that required modification:
```json
{
  "cues": [
    {
      "index": 142,
      "original_he": "חרב הלייזר של אביך. זה הנשק של אביר ג'דיי.",
      "polished_he": "חרב האור של אביך. זהו נשקו של אביר ג'דיי.",
      "reason": "Canon terminology (Lightsaber = חרב אור) + improved syntax"
    }
  ]
}
```

### Stage 5: Markdown Diff Audit Report
Produces a readable Markdown change log alongside the mastered subtitle:
```markdown
# 📋 RightSub Polish Audit Report — Star Wars (1977)

- **Total Cues Audited:** 1,248
- **Preserved Intact:** 1,114 (89.3%)
- **Polished / Corrected:** 134 (10.7%)

### Line Modification Details:
| Cue | Original English | Previous Hebrew | Polished Hebrew | Reason |
| :---: | :--- | :--- | :--- | :--- |
| **#142** | "Your father's lightsaber." | "חרב הלייזר של אביך." | "חרב האור של אביך." | Canon terminology (Lightsaber) |
| **#315** | "Can you hear me, Princess?" | "אתה שומע אותי, נסיכה?" | "את שומעת אותי, נסיכה?" | Gender correction (Princess Leia is female) |
| **#520** | "I have a bad feeling about this." | "אני יש לי הרגשה רעה לגבי זה." | "יש לי תחושה רעה בקשר לזה." | Fixed literal clumsy machine syntax |
```

---

## 5. Non-Destructive Safety Guarantees

- Original subtitles (`Movie.he.srt`) are safely backed up to `Movie.he.original.srt` before any replacement occurs.
- Polished output files are passed through the SubRefine engine, guaranteeing UTF-8 encoding and idempotent RLM (`\u200F`) injection for Plex, Infuse, and Apple TV playback.
