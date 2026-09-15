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

### 2. Trailing RLM
Injecting `\u200F` immediately before trailing punctuation (`?`, `!`, `.`, `...`, `)`) binds the punctuation strongly to the preceding Hebrew text, preventing it from flipping across the screen.

## Automatic Rule Enforcement in RightSub
`./rightsub merge` and `./rightsub fix-plex` automatically apply these rules along with homoglyph normalization, CP1255 encoding conversion, and SDH noise stripping via the **SubRefine Engine**.
