# End-to-End Subtitle Translation & Repair Workflow

This document describes the universal, production-tested workflow for translating or repairing subtitles for **any movie or TV series**.

```mermaid
graph TD
    A["Raw Video File / External SRT"] --> B["toolkit.py extract / sync"]
    B --> C["toolkit.py prompt-gen"]
    C --> D["Parallel AI Translation (Gemini Flash/Flash-Lite)"]
    D --> E["toolkit.py merge (BiDi + RLM + 1-to-1 Timing)"]
    E --> F["toolkit.py qa (Automated Discrepancy & Verification Check)"]
    F --> G["Deployment to Media Server (Plex / Infuse)"]
```

## Step 1: Subtitle Extraction & Preparation
If embedded in a video:
```bash
python3 toolkit.py extract "Movie.mkv" -o "Movie.en.srt"
```

## Step 2: Prompt Generation
Generate wave files and prompts tailored to the movie/show:
```bash
python3 toolkit.py prompt-gen "Movie.en.srt" --title "Inception" --genre "Sci-Fi Thriller" --context "Dream architecture, heist, Cobb and Mal"
```

## Step 3: Parallel AI Translation
Invoke Gemini 3.5 Flash-Lite or Gemini 3.8 Flash agents concurrently (up to 4 agents per wave) using `wave_01.json`, `wave_02.json`.

## Step 4: Merging with RLM & Sanitization
```bash
python3 toolkit.py merge "Movie.en.srt" "translated_batches_dir" -o "Movie.he.srt"
```

## Step 5: Automated QA Audit
```bash
python3 toolkit.py qa "Movie.en.srt" "Movie.he.srt"
```
