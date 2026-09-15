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
- **Hebrew-Only Detection**: Automatically inspects character distribution in each `.srt` file. English subtitles (`.en.srt`), Spanish, French, etc. are identified and skipped entirely (`[SKIP] Not Hebrew`). The script never touches non-Hebrew files.
- **Subtitle-Only Filtering**: Completely ignores video containers (MKV, MP4, AVI), poster art, or metadata files (`.nfo`).
- **Strict Idempotency**: Running repeatedly on already-fixed subtitles does not duplicate RLM marks or corrupt dialogue text.
- **Safety Flags**: Full support for `--dry-run` (preview mode with zero disk writes) and `--backup` (creates `.srt.bak` before editing in-place).
