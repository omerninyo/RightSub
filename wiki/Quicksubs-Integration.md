# On-Device Transcription & Audio Alignment (`quicksubs` Integration)

RightSub integrates with **`quicksubs`**, a high-performance on-device transcription CLI tool developed by **Matt Birchler**.

- **Author**: Matt Birchler
- **GitHub Repository**: [mattbirchler/quicksubs](https://github.com/mattbirchler/quicksubs)
- **Author's Site**: [Birchtree](https://birchtree.me)
- **Mac App Companion**: [Quick Subtitles](https://quickstuff.app)

---

## Overview

RightSub provides native on-device speech-to-subtitle and audio-guided retiming powered by `quicksubs`:

1. **Ingestion Fallback (Use Case 1)**: Transcribes raw video files into `.srt` subtitles when no embedded or external subtitles exist.
2. **Audio-Guided Alignment (Use Case 2)**: Re-synchronizes drifted or misaligned subtitles by extracting ground-truth speech timestamps directly from the audio track.

---

## Installation

```bash
brew install mattbirchler/tap/quicksubs
```

---

## Supported Speech Engines

| Engine | Flag | Model Size | Description |
| :--- | :--- | :--- | :--- |
| **Apple SpeechAnalyzer** | `--engine apple` | 0 MB (Built-in) | On-device Apple Silicon Neural Engine execution. Default. |
| **OpenAI Whisper** | `--engine whisper` | ~626 MB | Highest transcription accuracy for challenging audio. |
| **NVIDIA Parakeet** | `--engine parakeet` | ~400 MB | Fast, lightweight local neural model. |

---

## Commands & Usage

### 1. Direct Transcription
```bash
python3 scripts/00_transcribe_audio.py "/path/to/video.mp4" -e apple
```

### 2. Extraction with Automatic Fallback
```bash
python3 scripts/01_extract_subtitles.py "/path/to/videos" --transcribe --engine apple
```

### 3. Audio-Guided Synchronization
```bash
python3 scripts/16_audio_align_sync.py "unsynced.he.srt" -o "aligned.he.srt" -v "video.mp4"
```

---

## Future Roadmap

- **Zero-Bandwidth Cloud Optimization**: Local STT, sending only lightweight text cues to Gemini.
- **Media Server Folder Actions**: macOS LaunchAgent for automated drop-folder captioning.
- **Local Podcast Workflows**: Direct transcription of audio memos and lectures.
- **Apple Silicon Profiling**: Benchmarking local models via `quicksubs bench`.
