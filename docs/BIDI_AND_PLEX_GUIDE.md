# Hebrew Subtitle BiDi & Plex/Infuse Formatting Guide (RightSub)

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="BIDI_AND_PLEX_GUIDE.he.md"><b>עברית</b></a>
</p>

## The Core Problem: Punctuation Reversal in Modern Media Players
Modern media players (Plex, Infuse, VLC, Apple TV, Android TV, Smart TVs) use modern subtitle rendering engines (libass, ExoPlayer, AVPlayer) that default to **Left-to-Right (LTR)** embedding levels when rendering plaintext subtitles.

When a line containing Right-to-Left (RTL) text (such as Hebrew) ends with a neutral character (period, question mark, exclamation mark, hyphen, closing bracket, ellipses), the rendering engine treats the neutral punctuation as trailing LTR text, causing it to jump to the **far right** (the visual beginning of the line).

### Example of the Reversal:
- **Intended:** `?מה שלומך`
- **Rendered incorrectly:** `מה שלומך?` (with question mark on the right)
- **Dialogue with hyphens:** `- כן, אני מבין.` rendered as `כן, אני מבין. -`

## The Solution: The 3-Stage Canonical BiDi & Un-Flipping Engine (SubRefine)
Unicode character `U+200F` (RIGHT-TO-LEFT MARK - RLM) is a non-printable, zero-width formatting character with strong RTL directionality (`bc=R`).

### Stage 1: File-Level Flip Polarity Detection (`detect_file_flip_polarity`)
Many Hebrew subtitles downloaded from the web were previously altered by naive 1990s/2000s "Visual Punctuation Flipper" scripts (such as `Subabi` or `SubsCenter`), which physically moved periods and question marks to the logical start of the string (`.שלום` instead of `שלום.`) to trick old LTR-only DVD players.
- Before modifying any line, RightSub scans the file's punctuation polarity across all cues.
- If a file was pre-flipped (or contains unambiguous inverted lines), RightSub classifies the polarity so it never "double-flips" or locks broken punctuation in place with RLM.

### Stage 2: Line-Level Canonical Un-Flipping (`canonicalize_visual_flipped_line`)
RightSub strips all existing directional control characters (`RLM`, `LRM`, `LRE`, `RLE`, `PDF`, `LRI`, `RLI`, `FSI`, `PDI`), peels outer HTML/ASS tags (`{\an8}`, `<i>`, `<font>`), and reverses **18 distinct visual-flipping mutation patterns** validated across a **20,299-file (`15,630,175`-line)** real-world subtitle corpus:
- Leading punctuation attached or spaced (`.שלום` $\rightarrow$ `שלום.`, `?...מה` $\rightarrow$ `מה...?`)
- Full edge swaps (`.מה שלומך-` $\rightarrow$ `- מה שלומך.`)
- Leading dash + punctuation (`-.שלום` or `.-שלום` $\rightarrow$ `- שלום.`)
- Leading punctuation before numbers (`.1999 בשנת` $\rightarrow$ `בשנת 1999.`)
- Inverted or doubled parentheses/brackets (`(שלום(` / `)שלום)` / `)שלום(` $\rightarrow$ `(שלום)`)

### Stage 3: UAX #9 Rule N1 Wrapping (`\u200F + Logical Core + \u200F`)
Under **Unicode Standard Annex #9 (UAX #9, Rule N1)**, neutral characters (`?`, `!`, `.`, `,`, `:`, `;`, `…`, `-`, `)`, `]`, `"`) only resolve to `R` (Right-to-Left) when flanked on **both** sides by strong `R` characters (`R + N + R` $\rightarrow$ `R`) or when sitting between a strong `R` and a trailing `R` at the end of the line:
1. **Leading RLM (`\u200F` at index 0)**: Forces the subtitle renderer (`libass`, `ExoPlayer`, `AVPlayer`, `CoreText`) to establish an RTL start boundary, keeping leading dialogue hyphens (`-`), ellipses (`...`), and quotes on the **far right**.
2. **Trailing RLM (`\u200F` AFTER trailing punctuation)**: Placed at the **very end of the logical core** (`\u200Fמה שלומך?\u200F`), sandwiching any trailing punctuation (`?`, `!`, `.`, `...`, `)`) between the preceding Hebrew word (`R`) and the closing `RLM` (`R`). Placing `RLM` *before* trailing punctuation (`מה שלומך\u200F?`) leaves the punctuation exposed to the LTR paragraph boundary (`eos = L`), which still causes reversal in strict UAX #9 engines!
3. **Bilingual Boundary Guards**: When a Hebrew line ends with an English/Latin token followed by punctuation (`ראיתי את ה-FBI.`), an internal `RLM` is also injected before the trailing punctuation (`ראיתי את ה-FBI\u200F.\u200F`) so the Latin letters (`L`) cannot pull the period across the line. Similarly, a leading dialogue hyphen before an English word receives an internal `RLM` (`\u200F- \u200FFBI כאן.\u200F`).

## Automatic Rule Enforcement in RightSub
`./rightsub merge` and `./rightsub fix-plex` automatically apply this 3-stage engine along with homoglyph-conditional final-letter normalization, CP1255 encoding conversion, and SDH/multi-line credit stripping via the **SubRefine Engine**.

### 3 Execution Modes for `fix-plex`:

#### 1. Single File
```bash
./rightsub fix-plex "Movie.he.srt" --in-place
```

#### 2. Multiple Specific Files
Pass multiple paths sequentially:
```bash
./rightsub fix-plex "S01E01.he.srt" "S01E02.he.srt" "S01E03.he.srt" --in-place
```

#### 3. Whole Directory or Media Library (Recursive)
Recursively scan an entire season or library folder, cleaning ads and creating backups:
```bash
./rightsub fix-plex "/path/to/TV_Shows/" --recursive --in-place --clean-ads --backup
```

---

## Smart Safety & Filtering Architecture
The tool is engineered for worry-free batch operations on large, heterogeneous media libraries:
- **Hebrew-Only & Multi-Charset Detection (`UTF-8`, `UTF-16`, `Windows-1255` vs `Windows-1252`)**: Automatically inspects byte and character distributions in each `.srt` file, distinguishing Hebrew `CP1255` multi-byte words from Western European `CP1252` accented text (French, Spanish, German) and 3-byte UTF-8 punctuation (`0xE2`). Non-Hebrew subtitles are skipped entirely (`[SKIP] Not Hebrew`).
- **Content-Based Hebrew `.srt` Discovery & Seed-Safe Torrent Protection (`.srt` $\rightarrow$ `.he.srt`)**: `rightsub auto` and `rightsub polish` detect any `.srt` containing Hebrew text (e.g. `Movie.srt`, `Movie.heb.srt`, or `Subs/*.srt`), keep the original `.srt` 100% untouched on disk for torrent seeding (`qBittorrent` / `Transmission`), and write the mastered output separately as `<stem>.he.srt`.
- **Georgian/Cyrillic Homoglyph Repair & Bilingual Number Un-Flipping (`0` Tokens)**: Repairs cross-script OCR/keyboard typos such as Georgian `ე` (`U+10D4`) in `דეייט` $\rightarrow$ `דייט`, and deterministically un-flips 2-digit numbers reversed by legacy `Subabi` tools (`84` $\rightarrow$ `48`) when `48` is confirmed in the companion `.en.srt` cue (`cross_check_bilingual_numbers`).
- **Tag-Safe BiDi & Loanword Preservation (`{\an8}`, `<i>`, `<font>`)**: RLM marks are injected strictly around inner dialogue text (`{\an8}<font color="#ffff00"><i>\u200Fטקסט\u200F!</i></font>`), never inside tag brackets. Handles dialogue hyphens before English words (`\u200F- \u200FFBI כאן\u200F.`) and preserves Hebrew loanwords ending in `/p/` (`ג'יפ`, `קטשופ`, `טלסקופ`).
- **Subtitle-Only Filtering & Atomic Writes**: Completely ignores video containers (MKV, MP4, AVI), poster art, or metadata files (`.nfo`), and writes files atomically via temporary sibling replacement.
- **Strict Idempotency**: Running repeatedly on already-fixed subtitles does not duplicate RLM marks or corrupt dialogue text.
- **Safety Flags**: Full support for `--dry-run` (preview mode with zero disk writes) and `--backup` (creates `.srt.bak` before editing in-place).

