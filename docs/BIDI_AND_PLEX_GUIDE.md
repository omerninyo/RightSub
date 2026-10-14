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

## The Solution: The SubRefine Invisible RLM Engine
Unicode character `U+200F` (RIGHT-TO-LEFT MARK - RLM) is a non-printable, zero-width formatting character with strong RTL directionality.

### 1. Leading RLM
Injecting `\u200F` as the very first character of every line forces the text shaper to start with an RTL base level, ensuring dialogue dashes (`-`) stay on the right.

### 2. Trailing RLM
Injecting `\u200F` immediately before trailing punctuation (`?`, `!`, `.`, `...`, `)`) binds the punctuation strongly to the preceding Hebrew text, preventing it from flipping across the screen.

## Automatic Rule Enforcement in RightSub
`./rightsub merge` and `./rightsub fix-plex` automatically apply these rules along with homoglyph normalization, CP1255 encoding conversion, and SDH noise stripping via the **SubRefine Engine**.

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
- **Tag-Safe BiDi & Loanword Preservation (`{\an8}`, `<i>`, `<font>`)**: RLM marks are injected strictly around inner dialogue text (`{\an8}<font color="#ffff00"><i>\u200Fטקסט\u200F!</i></font>`), never inside tag brackets. Handles dialogue hyphens before English words (`\u200F- \u200FFBI כאן\u200F.`) and preserves Hebrew loanwords ending in `/p/` (`ג'יפ`, `קטשופ`, `טלסקופ`).
- **Subtitle-Only Filtering & Atomic Writes**: Completely ignores video containers (MKV, MP4, AVI), poster art, or metadata files (`.nfo`), and writes files atomically via temporary sibling replacement.
- **Strict Idempotency**: Running repeatedly on already-fixed subtitles does not duplicate RLM marks or corrupt dialogue text.
- **Safety Flags**: Full support for `--dry-run` (preview mode with zero disk writes) and `--backup` (creates `.srt.bak` before editing in-place).

