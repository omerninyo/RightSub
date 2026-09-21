# On-Device Transcription & Audio Alignment (`quicksubs` Integration)

RightSub integrates with **`quicksubs`**, a high-performance on-device transcription CLI tool developed by **Matt Birchler**.

- **Author**: Matt Birchler
- **GitHub Repository**: [mattbirchler/quicksubs](https://github.com/mattbirchler/quicksubs)
- **Author's Site**: [Birchtree](https://birchtree.me)
- **Mac App Companion**: [Quick Subtitles](https://quickstuff.app)

---

## Overview

RightSub is designed for high-fidelity subtitle translation, Hebrew bidirectional formatting (RLM for Plex/Infuse), and contextual gender QA. By integrating with `quicksubs`, RightSub gains **native on-device speech-to-subtitle capabilities**:

1. **Ingestion Fallback (Use Case 1)**: Transcribes raw audio/video files into clean `.srt` subtitles when no embedded or external subtitles exist.
2. **Audio-Guided Alignment (Use Case 2)**: Re-synchronizes drifted or misaligned subtitles by extracting ground-truth speech timestamps directly from the video's audio track.

---

## Installation

`quicksubs` is distributed via Homebrew for macOS:

```bash
brew install mattbirchler/tap/quicksubs
```

*Note: RightSub treats `quicksubs` as an optional enhancement. If not installed, all other extraction, translation, and BiDi formatting operations remain 100% functional.*

---

## Supported Speech Engines

`quicksubs` provides three local engines:

| Engine | Flag | Model Size | Description |
| :--- | :--- | :--- | :--- |
| **Apple SpeechAnalyzer** | `--engine apple` | 0 MB (Built-in) | On-device Apple Silicon Neural Engine execution. Default. |
| **OpenAI Whisper** | `--engine whisper` | ~626 MB | Highest transcription accuracy for challenging audio. |
| **NVIDIA Parakeet** | `--engine parakeet` | ~400 MB | Fast, lightweight local neural model. |

---

## Implemented Use Cases

### 1. On-Device Speech-to-Subtitle Ingestion
When a video file has no embedded subtitle streams and no external subtitle files exist on disk:

#### Option A: Dedicated Transcription Tool
```bash
python3 scripts/00_transcribe_audio.py "/path/to/episode.mp4" -e apple
```
Generates `/path/to/episode.srt` on-device with zero network traffic.

#### Option B: Automated Fallback in Subtitle Discovery
```bash
python3 scripts/01_extract_subtitles.py "/path/to/season_folder" --transcribe --engine apple
```
If embedded or external subtitles are missing, `01_extract_subtitles.py` automatically invokes `quicksubs`, creating `.en.srt` ready for the RightSub translation pipeline.

---

### 2. Audio-Guided Subtitle Retiming & Synchronization
When you have an existing translation (e.g. Hebrew `.he.srt`), but its timing is desynced due to framerate mismatches (23.976 vs 25 FPS), commercial cuts, or intro shifts:

```bash
python3 scripts/16_audio_align_sync.py \
  "path/to/unsynced.he.srt" \
  -o "path/to/aligned.he.srt" \
  -v "path/to/video.mp4" \
  -e apple
```

**How it works**:
1. `quicksubs` transcribes the video's audio track into a temporary reference timeline.
2. `16_audio_align_sync.py` calculates the optimal scale ratio (stretching/compression) and linear offset between dialogue cues.
3. The subtitle timestamps are shifted and aligned while preserving 100% of the translated Hebrew text and formatting.

---

## Future Roadmap (Planned Enhancements)

The following concepts are planned for future releases:

### 3. Zero-Bandwidth Cloud Optimization
Transcribe entire multi-gigabyte video libraries locally on Apple Silicon. Only send the resulting lightweight text cues (tens of kilobytes) to cloud LLMs (such as Google Gemini), eliminating 99% of cloud multimodal bandwidth and token costs.

### 4. macOS Folder Actions & Media Server Daemon
A macOS LaunchAgent or Folder Action that monitors Plex/Infuse media drop folders:
- Automatically detects newly added video files lacking subtitles.
- Transcribes with `quicksubs`.
- Runs RightSub RLM punctuation and BiDi processing in the background.

### 5. Local Podcast & Voice Memo Workflow
A dedicated pipeline for transcribing recorded audio memos, lectures, and Israeli podcasts locally to formatted `.srt` and `.txt`.

### 6. Apple Silicon Hardware Benchmarking
Integration of `quicksubs bench` to measure and compare Neural Engine vs GPU inference performance across M-series hardware setups before running bulk batch jobs.
