# 🔰 Quickstart for Beginners — RightSub (The Zero-Jargon Guide)

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="QUICKSTART_FOR_BEGINNERS.he.md"><b>עברית</b></a>
</p>

Welcome to **RightSub**!  
If you are unfamiliar with command-line tools, do not know what CLI "flags" are, or simply want perfect Plex subtitles with zero hassle — **this guide was written specifically for you.**

---

## 🚀 Two Zero-Jargon Ways to Use RightSub

Forget about remembering complex flags or chained commands. In **RightSub v1.5.0**, you have two effortless ways to do everything:

### Option A (Zero Flags): Launch the Interactive Mastering Wizard (`rightsub`)
Simply type `rightsub` with no arguments in your Terminal (macOS/Linux) or Command Prompt / PowerShell (Windows) and press **Enter**:
```bash
rightsub
```
An interactive menu opens automatically:
1. Choose your action (`1. Full Autonomous Ingest`, `2. Fix Subtitles for Plex`, `3. Polish & Proofread`, `4. AI Translation`, `7. First-Time Setup`, `8. Connect AI Agents via MCP`).
2. **Drag & drop** any file or folder into the window — or type **`B`** to use the built-in interactive file browser!

### Option B: One Single Command (`rightsub auto`)
Run a single smart command directly on any file or folder:
```bash
rightsub auto "Drag and drop your file or directory here"
```

#### 💡 How to run it using Drag & Drop:
1. Open your Terminal or Windows Command Prompt.
2. Type: `rightsub auto ` *(make sure to include a space after auto)*.
3. Open **Finder** (macOS) or **File Explorer** (Windows), click and drag your movie file, subtitle file, or entire TV season folder — **and drop it right onto the Terminal window**.
4. Press **Enter**.

---

## 🧭 What RightSub Does Automatically Based on What You Dragged

```mermaid
graph TD
    Start["Dragged an item into rightsub / rightsub auto"] --> Check{"What did you drop?"}
    
    Check -- "Hebrew subtitle file (.he.srt or plain .srt in any encoding)" --> Action1["Plex BiDi & RLM Punctuation Fix<br/>+ Auto CP1255 to UTF-8 conversion<br/>+ Seed-Safe .he.srt output (leaves torrent .srt untouched)<br/>+ Ad & credit spam stripping + .bak backup"]
    
    Check -- "Video file (MKV / MP4)" --> VideoCheck{"Does a Hebrew subtitle exist?"}
    VideoCheck -- "Hebrew subtitle exists (any name/encoding)" --> Action1
    VideoCheck -- "No Hebrew subtitle" --> Action2["Extracts English subtitles from video<br/>(If missing: transcribes audio on-device!)<br/>+ Prepares translation batches & Bible"]
    
    Check -- "Entire Directory (Season / Library)" --> Action3["Deep Directory Scan:<br/>1. Detects all Hebrew .srt files by content & masters to .he.srt<br/>2. Prepares English subtitles & batches for untranslated titles"]
```

---

## ⚡ 3 Common Everyday Scenarios

### 1. Fix Hebrew Subtitles for Plex / Infuse / Apple TV (0 AI Tokens Required)
- **The Issue**: Question marks (`?`), periods, or dashes jump to the wrong end of lines, characters are mojibake gibberish (`Windows-1255`), the file lacks the `.he` suffix (`Movie.srt`) so Plex shows `"Unknown"`, or lines are cluttered with website ads.
- **The Solution**:
  ```bash
  rightsub auto "Movie.srt"   # or "Movie.he.srt"
  ```
  *RightSub detects Hebrew by content in any encoding, converts to clean UTF-8, fixes BiDi with RLM, strips ads, and saves a Seed-Safe `Movie.he.srt` copy (leaving the original `Movie.srt` 100% untouched so torrent seeding never breaks).*

### 2. Fix an Entire TV Season or Complete Library
- **The Issue**: You have a folder with 24 episodes or dozens of movies and want them all mastered at once.
- **The Solution**:
  ```bash
  ./rightsub auto "/path/to/TV_Season_or_Movie_Folder/"
  ```
  *The system scans all subdirectories, automatically detects Hebrew files to repair them, and safely ignores English subtitles so they are never corrupted.*

### 3. Translate a Movie from English to Hebrew
- **The Issue**: You downloaded a media file with English subtitles and want a high-grade Hebrew translation.
- **The Solution**:
  ```bash
  ./rightsub auto "Movie.mkv"
  ```
  *The system extracts the English stream, pulls plot & character genders from TMDb, and prepares translation batches.*

---

## 🎙️ What If the Video Has No Subtitles at All? (Automatic Speech-to-Text!)

Unlike traditional subtitle tools that fail when subtitles are missing, RightSub has built-in on-device Speech-to-Text powered by **quicksubs** (Apple SpeechAnalyzer and Whisper):
- If you run `./rightsub auto "Movie.mkv"` on a video with no subtitles, RightSub **will not crash or stop!**
- It automatically invokes the on-device transcription engine, processes the audio stream, and produces a complete, perfectly timed English master subtitle.

---

## 🦙 Offline Local Translation via Ollama (Emergency Fallback / Experimental)

> [!WARNING]
> **Critical Hebrew Quality Limitation:**  
> Small open-weight models (Llama 3.2, Qwen, Mistral 7B/8B) suffer from **severe degradation when translating into Hebrew**:
> 1. **Gender & Grammar Collapse**: Frequent confusion between masculine ("אתה") and feminine ("את") address, corrupted verb conjugations, and wrong plurals.
> 2. **Byte-Level Tokenization**: Hebrew characters are fragmented into raw UTF-8 bytes, leading to slow inference and context degradation.
> 3. **Unnatural / Literal Phrasing**: Slang and cultural idioms are translated literally, resulting in awkward dialogue.
> 
> **Recommendation:** Local Ollama translation is intended **strictly as an offline fallback or experimental feature**. For broadcast-quality subtitles, you must use high-parameter cloud models (**Gemini Flash / Pro**, **Claude 3.5**, or **GPT-4o**).

### Running in emergency/offline mode (in 2 steps):
1. Install Ollama from [ollama.com](https://ollama.com) (or via Homebrew: `brew install ollama`).
2. Download a model (one time only):
   ```bash
   ollama pull llama3.2
   ```

### Running local offline translation:
```bash
./rightsub auto "Movie.mkv" --ollama
```

---

## 🤖 Want Your AI Agent to Do Everything for You? (Native MCP Server)

If you work with AI agents such as **Google Antigravity**, **Claude Desktop**, **Claude Code**, **Cursor**, or **Windsurf**, you can connect RightSub directly to your agent in **one single command**:

```bash
rightsub mcp --install
```

This automatically registers RightSub's **Native MCP Server** (`8` local subtitle & media tools) inside your AI client. From that moment on, you don't even have to touch the terminal yourself — simply tell your AI assistant in plain language:

> *"Please use RightSub to inspect, fix, and translate the subtitles in my directory [path], ensure 100% Plex compliance, and report back when finished."*

For complete MCP tool schemas, ready-to-copy prompt templates, and system prompt configurations, see the [AI Integration Guide](AI_INTEGRATION_GUIDE.md).

---

## 🛡️ Built-in Safety & Protection
1. **Foreign Language Protection**: RightSub checks the Hebrew character ratio in every file. English subtitles are never touched or modified.
2. **Seed-Safe Torrent Protection**: Plain `.srt` files (`Movie.srt`) are duplicated into `Movie.he.srt`, leaving the original downloaded file 100% bit-for-bit intact for active torrent seeding.
3. **Idempotency**: Running repeatedly on the same file never duplicates RLM marks or degrades formatting.
4. **Automatic Backups**: Creates a `.srt.bak` file before making in-place changes to any `.he.srt` file.
