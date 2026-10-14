# Hebrew Subtitle BiDi & Plex/Infuse Formatting Guide

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="מדריך-BiDi-ופלקס"><b>עברית</b></a>
</p>

## The Core Problem: Punctuation Reversal in Modern Media Players
Modern media players (Plex, Infuse, VLC, Apple TV, Android TV, Smart TVs) use modern subtitle rendering engines (libass, ExoPlayer, AVPlayer) that default to **Left-to-Right (LTR)** embedding levels when rendering plaintext subtitles.

When a line containing Right-to-Left (RTL) text (such as Hebrew) ends with a neutral character (period, question mark, exclamation mark, hyphen, closing bracket, ellipses), the rendering engine treats the neutral punctuation as trailing LTR text, causing it to jump to the **far right** (the visual beginning of the line).

### Example of the Reversal:
- **Intended:** `?מה שלומך`
- **Rendered incorrectly:** `מה שלומך?` (with question mark on the right)
- **Dialogue with hyphens:** `- כן, אני מבין.` rendered as `כן, אני מבין. -`

## The Solution: The SubRefine Invisible RLM Engine
Unicode character `U+200F` (RIGHT-TO-LEFT MARK - RLM) is a non-printable, zero-width formatting character with strong RTL directionality.

### 1. Leading RLM
Injecting `\u200F` as the very first character of every line forces the text shaper to start with an RTL base level, ensuring dialogue dashes (`-`) stay on the right.

### 2. Trailing RLM & Dialogue Hyphen Protection
Injecting `\u200F` immediately before trailing punctuation (`?`, `!`, `.`, `...`, `…`, `)`, `"`, `'`, `״`, `׳`) binds the punctuation strongly to the preceding Hebrew text, preventing it from flipping across the screen. Additionally, dialogue hyphens followed by English words (`- FBI כאן.`) receive an extra `\u200F` after the hyphen space (`\u200F- \u200FFBI כאן\u200F.`) so the hyphen is never pulled to the left side of the English token.

### 3. HTML & ASS Tag Preservation
SubRefine strips existing RLM marks and re-applies them strictly **inside** HTML formatting wrappers (`<i>...</i>`, `<b>...</b>`, `<font color="#ffff00">...</font>`) while preserving leading ASS/SSA positioning tags (`{\an8}`, `{\pos(x,y)}`). `\u200F` is never injected inside `<...>` or `{...}` syntax.

### 4. Loanword-Safe Final Letter Normalization
Final Hebrew letters (`ך`, `ם`, `ן`, `ץ`) are normalized only at true Hebrew word boundaries (`(?<=[א-ת])`), preserving acronyms with mid-word quotes (`בימ"ש`, `צה"ל`) and loanwords ending in `/p/` (`ג'יפ`, `קטשופ`, `טלסקופ`, `סטארטאפ`).

## Automatic Rule Enforcement in RightSub
`./rightsub merge` and `./rightsub fix-plex` automatically apply these rules along with homoglyph normalization, CP1255/UTF-16 encoding conversion, and SDH noise stripping via the **SubRefine Engine**.

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
- **Hebrew-Only Detection & Encoding Heuristics**: Automatically inspects byte and character distributions in each `.srt` file (supporting UTF-8, UTF-16 LE/BE BOM, Windows-1255, and ISO-8859-8). English subtitles (`.en.srt`) and Western European Windows-1252 subtitles (French, Spanish, German) are distinguished via contiguous Hebrew word-pair heuristics and skipped entirely (`[SKIP] Not Hebrew`).
- **Line-Granular Ad Cleaning**: Promotional credit lines (`תרגום:`, `סנכרון:`) are removed at the individual line level without deleting legitimate dialogue sharing the same subtitle cue.
- **Crash-Safe Atomic Writes**: All file updates write to a temporary sibling file and execute an atomic `os.replace()` + `os.utime()` timestamp touch, ensuring zero partial files and instant Plex/Infuse index refresh.
- **Subtitle-Only Filtering**: Completely ignores video containers (MKV, MP4, AVI), poster art, or metadata files (`.nfo`).
- **Strict Idempotency**: Running repeatedly on already-fixed subtitles does not duplicate RLM marks or corrupt dialogue text.
- **Safety Flags**: Full support for `--dry-run` (preview mode with zero disk writes) and `--backup` (creates `.srt.bak` before editing in-place).
