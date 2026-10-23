# 💎 Architectural Specification: Semantic AI Polish & Subtitle QC Engine (`rightsub polish`)

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="FEATURE_AI_POLISH_AND_QC.he.md"><b>עברית</b></a>
</p>

This document specifies the architectural design, data contracts, CLI interface, and production implementation of the **Semantic AI Polish & Subtitle QC Engine** in RightSub (shipped in v1.3.0): the `rightsub polish` command.

The goal of this engine is to proofread, polish, and modernize existing Hebrew subtitles (legacy releases, imperfect human translations, or raw machine drafts — such as community scans like *Star Wars 4K77*) **without re-translating the entire movie from scratch**, correcting canon drift, gender agreement errors, and literal idioms while strictly preserving quality human phrasing (85%–90% preservation target).

---

## 1. Problem Statement & Engineering Motivation

Tens of thousands of community-uploaded Hebrew subtitle files exist for classic films and series. In 85%–90% of cases, the dialogue timing is accurate and basic phrasing is serviceable, yet they suffer from three pervasive semantic defects:
1. **Franchise & Canon Terminology Drift:** Inconsistent or obsolete translations of lore terms (e.g. translating "Lightsaber" as "Laser Sword" / *"חרב לייזר"*, or omitting military ranks like "Grand Moff").
2. **Grammatical Gender Flipping:** Second-person English dialogue ("You") translated into masculine Hebrew verbs even when addressing female characters (e.g. Han or Luke addressing Princess Leia with masculine verbs).
3. **Anachronistic Registers & Literal Idiom Translation:** Idiomatic expressions translated word-for-word, resulting in unnatural dialogue (e.g. *"I have a bad feeling about this"* translated literally instead of natural Hebrew cinematic prose).

Re-translating the entire film with an LLM burns unnecessary tokens, risks hallucinating or discarding authentic human dialogue choices, and can introduce timing drift. **The Polish Engine operates on the principle of Minimal Edit Distance.**

---

## 2. RightSub Subtitle Operation Comparison & AI Decision Matrix

| Command | Primary Role | Modifies Text? | Uses AI? | Token Cost |
| :--- | :--- | :---: | :---: | :---: |
| `rightsub fix-plex` | Algorithmic BiDi (RLM), 18-pattern un-flipping, CP1255 recovery, homoglyph & ad cleaning. | ❌ No (Formatting only) | ❌ No | **0** |
| `rightsub qa` | Deterministic verification of line counts, timing, `Cue Drift`, and vocative/morphological gender. | ❌ Audit report only | ❌ No | **0** |
| `rightsub auto` (No AI Key) | Extracts, detects any Hebrew `.srt` by content, repairs BiDi/encoding, and writes Seed-Safe `.he.srt`. | ❌ No (Formatting only) | ❌ No | **0** |
| `rightsub auto` (With AI Key) | Same as above for existing Hebrew `.srt` (0 tokens); invokes AI **only** when no Hebrew subtitle exists and full translation is needed. | ✔️ Full (only if translating) | ✔️ Only if translating | **0** (existing HE) / **100%** (new translation) |
| **`rightsub polish`** | **Proofreading, semantic gender correction & canon harmonization (plus 0-token deterministic pass).** | **✔️ Selective fixes only** | **✔️ Optional (`--gemini` / `--ollama`)** | **0** (deterministic pass) / **~15%–20%** (with AI) |

### 2.1 When Is AI Actually Needed for Existing Subtitles? (Rare Edge Cases Only)
A core architectural principle of RightSub is **strict separation between technical subtitle mastering (0 AI tokens) and semantic AI proofreading**:
- **99% of Existing Human Subtitles Need Zero AI (`0` Tokens):** Technical defects — inverted punctuation (`.שלום`), missing UAX #9 `RLM` wrappers, `Windows-1255` mojibake, Cyrillic/Georgian homoglyphs (`דეייט` $\rightarrow$ `דייט`), reversed 2-digit `Subabi` numbers (`84` $\rightarrow$ `48`), and translator credit banners — are **100% deterministic** and handled offline by `fix-plex` / `auto` without an API key.
- **When to Use `rightsub polish` with AI:** Invoking an LLM (`GEMINI_API_KEY` or `--ollama`) on an existing Hebrew subtitle is reserved for **rare edge cases** — such as very old amateur translations, unedited machine/OCR drafts, or specific franchise releases with severe terminology drift (e.g. translating *"Lightsaber"* as *"חרב לייזר"*) or pervasive unmarked speaker-to-addressee gender errors where no explicit vocative name appears in the cue.
- **0-Token Deterministic Pass Always Runs First:** Even inside `rightsub polish`, Stage 0 executes the **Deterministic Canon, Homoglyph & Bilingual Number Un-Flipping Pass** (`run_deterministic_canon_pass` + `cross_check_bilingual_numbers`) at **0 token cost** before any LLM is ever called.

---

## 3. CLI Command Interface

```bash
# Review and polish an existing Hebrew subtitle against master English:
rightsub polish "Star Wars (1977).he.srt" --en "Star Wars (1977).en.srt"

# Explicitly provide a Translation Bible (or auto-detected translation_bible.json):
rightsub polish "Star Wars (1977).he.srt" --bible translation_bible.json

# Query TMDb by specific ID for cast rosters and franchise canon:
rightsub polish "Gladiator.he.srt" --en "Gladiator.en.srt" --tmdb-id 98

# Cloud AI proofreading with automated Model Cascade (gemini-3.8-flash -> gemini-3.5-flash):
rightsub polish "Movie.he.srt" --gemini

# Run locally and 100% offline via Ollama:
rightsub polish "Movie.he.srt" --en "Movie.en.srt" --ollama --model qwen2.5:7b

# Dry run / Audit mode: generate a change report without modifying the subtitle file:
rightsub polish "Movie.he.srt" --en "Movie.en.srt" --diff-only

# Interactive Line-by-Line Diff Reviewer (New in v1.5.0: [Y/Enter] Approve, [N] Reject, [E] Edit, [A] Approve All, [R] Reject Remaining, [Q] Quit):
rightsub polish "Movie.he.srt" --en "Movie.en.srt" --interactive
```

### 3.1 Interactive Line-by-Line Diff Reviewer (`--interactive` / `-i`)
Shipped in `v1.5.0` ([`scripts/19_polish_and_qc.py`](file:///Volumes/Other/Antigravity/RightSub/scripts/19_polish_and_qc.py)), `rightsub polish --interactive` (or `-i`) presents every proposed canon, number, or AI modification in a linear terminal review loop before writing to disk:
- **`[Y / Enter]`**: Approve the proposed change for this cue.
- **`[N]`**: Reject the change and preserve the original Hebrew line.
- **`[E]`**: Type a custom manual Hebrew replacement for this cue.
- **`[A]`**: Approve all remaining proposed modifications immediately.
- **`[R]` / `[Q]`**: Reject all remaining modifications and save only the cues approved so far.
- **`Ctrl+C` Partial-Save Safety**: Pressing `Ctrl+C` during an interactive review never corrupts the file; it catches `KeyboardInterrupt` and offers to save the partial approvals reviewed up to that cue.

---

## 4. Pipeline Architecture

```text
[Movie.en.srt] ──┐
                 ├──> [1. Bilingual Cue Alignment] ──> [2. Translation Bible & TMDb Ingestion]
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

### Stage 2: Translation Bible, Plot Synopsis & TMDb Ingestion
Ingests companion `translation_bible.json` (or via `-b`/`--bible`) and queries TMDb API for the film's synopsis, genre categorization, and verified character roster with grammatical gender mapping (e.g., Luke Skywalker: male/אתה, Leia Organa: female/את). Also injects domain-specific glossaries for recognized franchises (Star Wars, Lord of the Rings, Harry Potter, Marvel Cinematic Universe).

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

### Stage 6: Hierarchical Domain Knowledge Engine
RightSub operates an offline and online 3-tier classifier (`domain_knowledge.py`):
1. **Tier 1 (TMDb / Bible)**: Verified genre lists and character cast sheets directly from TMDb or local bibles.
2. **Tier 2 (Franchise Patterns)**: Regex and title matches across major film franchises (*Star Wars*, *Marvel*, *Star Trek*, *Lord of the Rings*, *Harry Potter*).
3. **Tier 3 (Offline Fingerprinting)**: Lexical keyword scans detecting sci-fi, military, medical, or legal dialogue inside the subtitle itself when offline.

#### Bilingual Anchor Validation & Deterministic Number Un-Flipping (`cross_check_bilingual_numbers`):
To guarantee that cross-genre terms never corrupt unintended lines (e.g. translating "motor" as "motivator" outside of droid contexts), deterministic franchise rules require **bidirectional validation**:
- The Hebrew trigger must match the pattern.
- The master English cue must independently confirm the presence of the anchor phrase.
- **Deterministic Bilingual Number Un-Flipping (`0` Tokens):** Old visual-flipping tools (`Subabi`) often reversed 2-digit numbers inside Hebrew lines (`48` $\rightarrow$ `84`). When a companion `.en.srt` is available, `cross_check_bilingual_numbers` compares every 2-digit number in the Hebrew cue against the matching English cue: if the reversed number (`48`) appears in the English cue (either as digits `48` or English words `forty-eight`) and the current number (`84`) does not, it deterministically un-flips `84` $\rightarrow$ `48` with zero AI calls.

### Stage 7: Forward Anticipation Drift Guard & Split-Cue Partitioning
When dialogue spans multiple split cues (e.g. a sentence begun in cue #144 and finished in cue #145), standard LLMs often collapse the sentence into the first cue and translate upcoming dialogue lines into subsequent cues, causing a cascading off-by-one desynchronization.
- **Split-Cue Annotations**: Cues are annotated with `split_part` markers (`"1/2"`, `"2/2"`).
- **Drift Guard**: Polished outputs are checked in real-time. If an edit leaks or quotes words from upcoming English master cues, the edit is automatically rejected and the authentic human translation is preserved.

### Stage 8: Network Storage (SMB/NAS) Metadata Synchronization
When writing mastered subtitles or diff reports across SMB network mounts (e.g. Synology NAS, TrueNAS, QNAP), macOS SMB clients (`smbfs`) often fail to flush creation metadata, falling back to Apple's CoreFoundation epoch (`2001-01-01`).
RightSub explicitly calls `os.utime()` after all file write and backup operations, issuing an immediate kernel `SYS_utimes` call and SMB2 `SET_INFO` (`FileBasicInformation`) packet with the current system clock.

---

## 5. Non-Destructive & Seed-Safe Torrent Guarantees

- **Content-Based Hebrew `.srt` Discovery & Seed-Safe Output (`.srt` $\rightarrow$ `.he.srt`):** Both `rightsub auto` and `rightsub polish` inspect all `.srt` files by content/encoding (`UTF-8`, `UTF-16`, `Windows-1255`), not just files ending in `.he.srt`. When a plain Hebrew `.srt` (e.g. `Movie.srt`, `Movie.heb.srt`, or `Subs/Hebrew.srt`) is processed with `--in-place`, **the original `.srt` is left 100% untouched on disk** so active torrent seeding (`qBittorrent` / `Transmission`) never breaks, and the mastered output is saved separately as `Movie.he.srt`.
- When polishing an existing `.he.srt` file in-place, it is safely backed up to `Movie.he.original.srt` before replacement.
- Polished output files are passed through the SubRefine engine, guaranteeing UTF-8 encoding and idempotent UAX #9 Rule N1 RLM (`\u200F`) wrapping for Plex, Infuse, and Apple TV playback.
- Subtitle timecodes and cue indexes are strictly immutable.
