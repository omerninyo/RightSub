# 🔮 Architectural Specification: Interactive CLI Wizard

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="RFC_001_INTERACTIVE_TUI.he.md"><b>עברית</b></a>
</p>

This document details the architectural design principles, workflow, and system requirements for a future **Interactive CLI Wizard (TUI / Terminal Dialog)** for **RightSub**. The goal of the wizard is to empower end users to execute the full suite of RightSub mastering and translation capabilities without memorizing commands, arguments, or CLI flags.

---

## 1. Project Objectives

1. **Zero Flag Memorization:** Running `./rightsub` with no arguments automatically launches an interactive step-by-step interview with simple prompts, arrow keys, or number choices.
2. **Native Drag & Drop Support:** Prompts accept direct drag-and-drop of video files, subtitle files, or folders directly from file managers (macOS Finder, Windows File Explorer).
3. **Seed-Safe by Default:** Torrent seeding integrity is protected by default, offering non-destructive duplication into `.he.srt` without modifying original files.
4. **Zero Mandatory Dependencies:** Built on Python standard libraries (`sys`, `os`, `pathlib`, `shlex`, `getpass`), guaranteeing immediate execution without complex GUI or heavy curses requirements.

---

## 2. Platform Awareness & Operating System Constraints

The wizard detects the operating system at runtime via `platform.system()` and adapts features and input sanitization accordingly:

| Component / Capability | macOS | Windows | Linux / NAS |
| :--- | :--- | :--- | :--- |
| **Speech-to-Text Engine** | `Apple SpeechAnalyzer` (via `quicksubs -e apple`), utilizing Apple Silicon Neural Engine. | `Whisper` engine (or informational message if Whisper binary is missing). | `Whisper` engine (or manual reference). |
| **Path Drag & Drop** | Finder adds escape slashes to spaces (`\ `) or quotes. Normalized via `shlex` and `os.path.expanduser`. | Paths copied with backslashes (`\`) or surrounding double quotes. Normalized via `pathlib.Path`. | Standard POSIX path resolution. |
| **Terminal Charset** | UTF-8 by default. | Enforces UTF-8 active code page (`chcp 65001`) to prevent mojibake in Hebrew terminal prompts. | UTF-8 by default. |

---

## 3. Terminal BiDi & Layout Architecture

One of the common failure modes of Hebrew terminal interfaces is broken ASCII box boundaries due to mismatched Unicode double-width characters across terminal emulators (macOS Terminal.app vs. iTerm2 vs. Windows Terminal).

**RightSub Wizard Principles:**
1. **Linear Line-by-Line Dialog (Linear Wizard):**
   - Clean vertical text prompts instead of rigid multi-column ASCII tables and window splits.
   - Continuous scroll stream compatible with 100% of terminal environments, including SSH and tmux sessions.
2. **Clean Bilingual Mixed Labels:**
   - Technical actions and keys displayed in crisp English or clear bilingual terminology to prevent flipped punctuation and brackets in terminal streams.

---

## 4. Secure Key & Configuration Management

The wizard does not require re-entering API credentials on each run, nor does it require manual file editing:

1. **Local Configuration File:**
   - Stored at: `~/.config/rightsub/config.json`.
   - Secured with restrictive file permissions: `chmod 600` (readable and writable only by the active user).
2. **Precedence Hierarchy:**
   - Terminal Environment Variable (`export TMDB_API_KEY="..."`) -> Local config file -> Keyless offline fallback.
3. **Masked Input & Live Ping Verification:**
   - When entering API keys, input is masked via `getpass` to prevent exposure in shell histories.
   - Upon entry, the wizard fires a live ping to the upstream API (TMDb / Gemini) to verify validity before persisting.
4. **Offline-First Functionality:**
   - All core operations (Plex BiDi repair, RLM injection, CP1255 recovery, SDH/ad sanitization, local STT) operate completely keyless.

---

## 5. Interactive Flow Diagram

```text
==================================================================
           RightSub — Interactive Mastering Wizard
==================================================================

[?] What would you like to do today?
  > 1. Full Autonomous Ingest (Zero-Config Auto)
    2. Fix Subtitles for Plex (BiDi, RLM, CP1255 & Ad Sanitizing)
    3. AI Subtitle Translation
    4. Extract Embedded Subtitles from Video (FFmpeg)
    5. On-Device Speech-to-Text Transcription
    6. Configuration & API Keys (TMDb / AI Keys)
    7. Exit

[?] Drag & drop a video file, subtitle, or folder here and press Enter:
  > /Volumes/Media/Gladiator (2000)/Gladiator.mkv

[?] Video file detected without an external Hebrew subtitle.
    How would you like to proceed?
  > [1] Extract embedded English subtitle and prepare translation (Recommended)
    [2] Transcribe audio track locally using AI Speech-to-Text
    [3] Cancel

[?] Preserve active torrent seeding (Seed-Safe)?
  > [Y] Yes, duplicate into clean .he.srt and keep source intact (Recommended)
    [N] No, replace and rename source file in place
```

---

## 6. Implementation Libraries

1. **Standard Library Mode (Zero External Dependencies):**
   - Built exclusively with `sys`, `os`, `pathlib`, `shlex`, `getpass`.
   - Guaranteed out-of-the-box availability without `pip install` overhead.
2. **Enhanced Terminal Experience (Optional):**
   - Graceful elevation to `questionary` or `InquirerPy` if installed in the environment for arrow-key navigation and interactive checkboxes.
