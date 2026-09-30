# 🔄 RightSub Home Media & Download Integrations Guide

> **Overview**: Automate RightSub across your home lab and media server stack. Run subtitle mastering, BiDi correction, and translation in a 100% hands-off "Set-and-Forget" workflow.

This guide provides tested, copy-pasteable configurations for the most popular home media tools across **Windows** and **macOS/Linux**:
0. [The Recommended 2-Phase Strategy & Daemon Architecture](#0-the-recommended-2-phase-strategy--daemon-architecture)
1. [qBittorrent (Run on Completion & Seed-Safe)](#1-qbittorrent-torrent-completion-hook)
2. [Sonarr & Radarr (Custom Connect Scripts)](#2-sonarr--radarr-connect-scripts)
3. [Bazarr (Custom Post-Processing Hook)](#3-bazarr-post-processing-hook)
4. [Transmission (Torrent Completion Script)](#4-transmission-completion-script)
5. [Tautulli / Plex (Recently Added Webhook)](#5-tautulli--plex-recently-added-hook)
6. [Standalone OS Folder Watchers (Non-Arr / Manual Setups)](#6-standalone-os-folder-watchers-non-arr--manual-setups)
7. [Troubleshooting & Verifying Integrations](#7-troubleshooting--verifying-integrations)

---

## 0. The Recommended 2-Phase Strategy & Daemon Architecture

Before configuring individual hooks, understand RightSub's architectural philosophy:

### ⚙️ The 2-Phase Setup
1. **Phase 1: One-Off Retroactive Library Fix**  
   Run RightSub once across your existing media library to normalize legacy files:
   ```bash
   # Windows:
   rightsub auto "C:\Media\TV Shows"

   # macOS / Linux:
   rightsub auto /Volumes/Media/TV_Shows
   ```
   RightSub recursively scans all subdirectories, converts CP1255/Windows-1255 to UTF-8, injects BiDi RLM marks for Plex, sanitizes ads/SDH, and creates `.he.srt` files without modifying original torrent downloads.
2. **Phase 2: Ongoing Hands-Off Ingress (Event-Driven Hooks)**  
   From this point forward, you do **not** need a heavy background scanner. You configure your download clients (qBittorrent, Sonarr, Radarr, Bazarr) to invoke RightSub **only when new media finishes downloading**.

### 🏛️ Why Event-Driven Hooks Beat a 24/7 Background Daemon

Users often ask: *"Why doesn't RightSub run as a continuous background daemon/service that polls folders?"*

In home media pipelines, a continuous folder watcher daemon is an **architectural anti-pattern**:
1. **Race Conditions on Active Writes**: When a torrent client downloads a 15GB video file or unpacks a release, the file is being written continuously for minutes or hours. A folder watcher daemon triggers immediately upon file creation and attempts to read or lock an incomplete, partially-written file—causing crashes or corrupt outputs.
2. **Zero Idle Resource Consumption**: A background daemon keeps a Python runtime loaded in RAM 24/7 (~40–80 MB) and continually wakes CPU cores for filesystem polling. Event-driven hooks consume **0% CPU and 0 MB RAM**—RightSub is spawned only when an item finishes, does its work, and immediately terminates.
3. **Atomic Execution**: Download managers know with 100% cryptographic certainty when a file is fully downloaded, verified against its torrent hash, and closed. Invoking RightSub at that exact instant guarantees complete safety.

---

## 1. qBittorrent (Torrent Completion Hook)

qBittorrent can automatically trigger RightSub the exact millisecond a download finishes.

### The Seed-Safe Advantage
Normally, modifying a downloaded subtitle (e.g., renaming `Movie.srt` to `Movie.he.srt` or editing the text) alters the file hash and breaks active torrent seeding with an `I/O Error` or hash mismatch.  
RightSub's default **Seed-Safe architecture** avoids this completely: it duplicates non-standard subtitles into `Movie.he.srt` and masters the copy for Plex/Infuse, leaving the downloaded source file **100% bit-for-bit intact**. Active seeding continues uninterrupted.

### How to Configure:
1. Open qBittorrent.
2. Go to **Tools** -> **Options** (or `Preferences` on macOS).
3. Select **Downloads** in the sidebar.
4. Scroll to the bottom and check:  
   ☑ **"Run external program on torrent completion"**.
5. Paste the appropriate command:

#### Windows (Command Prompt / PowerShell):
```cmd
rightsub auto "%F"
```
*(If `rightsub` is not in your global PATH, specify the full path: `python "C:\path\to\RightSub\rightsub.py" auto "%F"`)*

#### macOS / Linux (Terminal):
```bash
/usr/local/bin/rightsub auto "%F"
```
*(Or `~/.local/bin/rightsub auto "%F"`)*

> **Note on `%F`**: qBittorrent automatically replaces `%F` with the absolute path to the downloaded file or root folder.

---

## 2. Sonarr & Radarr (Webhook Integration or Post-Import Script)

Sonarr and Radarr allow external automation to execute immediately after an episode or movie has been imported and organized into your library (`On Download`, `On Upgrade`, and `On Movie Imported`).

RightSub supports two integration methods:
- **Method A (Recommended for Docker, Unraid, TrueNAS, Synology)**: Native Webhook Server with zero host script or Python dependencies.
- **Method B (For Bare-Metal Systems)**: Custom Script invocation.

---

### Method A (Recommended): Container Webhook Server (`rightsub serve`)

When Sonarr and Radarr run inside isolated Docker containers, invoking host scripts is impossible. RightSub's built-in Webhook daemon provides native, seamless HTTP event handling:

#### Step 1: Start the RightSub Webhook Server
```bash
# Direct CLI run or container launch:
rightsub serve --port 8775 --path-map "/data/media:/media"

# Or deploy via docker-compose.yml:
docker compose up -d
```
*(For path mapping details across volumes, see [Cross-Container Path Translation (PATH_MAP)](#-cross-container-path-translation-path_map))*

#### Step 2: Configure in Sonarr / Radarr UI
1. Open the **Sonarr** or **Radarr** Web UI.
2. Navigate to: **Settings** -> **Connect**.
3. Click the **`+`** icon and select **Webhook**.
4. Fill in the parameters:
   - **Name**: `RightSub Subtitle Master`
   - **Notification Triggers**: Check ☑ **On Download**, ☑ **On Upgrade**, and in Radarr also ☑ **On Movie Imported**.
   - **URL**:
     - Within same Docker bridge network: `http://rightsub:8775/webhook/sonarr` (or `/webhook/radarr`).
     - Across network / host IP: `http://SERVER-IP:8775/webhook/sonarr`.
   - **Method**: `POST`
5. Click **Test** — RightSub will respond with `200 OK` and log the test ping.
6. Click **Save**.

---

### Method B: Custom Script (For Bare-Metal Installations)

For users running Sonarr/Radarr directly on the host operating system:

#### Step 1: Create the Hook Script

##### Windows: `C:\Scripts\rightsub_arr_hook.bat`
```cmd
@echo off
setlocal

:: Sonarr passes sonarr_episodefile_path; Radarr passes radarr_moviefile_path
set "TARGET_PATH="
if defined sonarr_episodefile_path set "TARGET_PATH=%sonarr_episodefile_path%"
if defined radarr_moviefile_path set "TARGET_PATH=%radarr_moviefile_path%"

if defined TARGET_PATH (
    rightsub auto "%TARGET_PATH%"
)
```

##### macOS / Linux: `/usr/local/bin/rightsub_arr_hook.sh`
```bash
#!/usr/bin/env bash
TARGET_PATH="${sonarr_episodefile_path:-$radarr_moviefile_path}"

if [ -n "$TARGET_PATH" ] && [ -f "$TARGET_PATH" ]; then
    /usr/local/bin/rightsub auto "$TARGET_PATH"
fi
```
*(Make sure to grant execution permissions: `chmod +x /usr/local/bin/rightsub_arr_hook.sh`)*

#### Step 2: Configure in Sonarr / Radarr UI
1. Navigate to **Settings** -> **Connect**.
2. Click the **`+`** icon and select **Custom Script**.
3. Fill in the fields:
   - **Name**: `RightSub Auto-Master`
   - **Notification Triggers**: Check ☑ **On Download** and ☑ **On Upgrade**.
   - **Path**: Set to your script path (`C:\Scripts\rightsub_arr_hook.bat` or `/usr/local/bin/rightsub_arr_hook.sh`).
4. Click **Test** and then **Save**.

---

## 3. Bazarr (Webhook Daemon or Post-Processing Hook)

Bazarr crawls 30+ internet subtitle providers. However, community-uploaded Hebrew subtitles routinely suffer from serious flaws:
- ❌ Reversed punctuation (`?`, `!`, `...`, hyphens) in Plex, Apple TV, and Infuse.
- ❌ Legacy Windows-1255 / ISO-8859-8 charsets rendering as unreadable gibberish / mojibake.
- ❌ Annoying promotional ads and translation credit lines ("סונכרן ע\"י Torec", "SubCenter", Telegram links).

RightSub completely eliminates these anomalies the exact moment Bazarr saves the subtitle file to disk:
- **Method A (Recommended): Direct Webhook from Bazarr to RightSub Server** (Turnkey for Docker & NAS).
- **Method B: Custom Post-Processing** (For bare-metal non-containerized setups).

---

### Method A (Recommended): Native Bazarr Webhook Connection

This is the cleanest, fastest, and most robust approach. It requires **zero custom scripts** inside your Bazarr container:

#### Step 1: Ensure RightSub Webhook Server is Running
```bash
# Run server on port 8775:
rightsub serve --port 8775 --path-map "/data/media:/media"
```

#### Step 2: Configure in Bazarr Web UI
1. Open your Bazarr Web UI (`http://localhost:6767` or your NAS IP).
2. Navigate to: **Settings** -> **Notifications**.
3. Click the **`+`** button (Add Notification) and select **Webhook**.
4. Configure the settings:
   - **Name**: `RightSub BiDi & Hebrew Master`
   - **URL**:
     - Inside Docker network: `http://rightsub:8775/webhook/bazarr`
     - Or using server IP: `http://192.168.1.X:8775/webhook/bazarr`
   - **HTTP Method**: `POST`
   - **Notification Types**:
     - Check **ONLY**: ☑ **On Subtitles Download** (or `On subtitles download`).
5. Click **Test**:
   - RightSub logs: `[Webhook] Received Bazarr test ping.` and responds with `200 OK`.
6. Click **Save**.

#### What Happens Under the Hood Whenever Bazarr Downloads a Subtitle?
1. Bazarr issues a `POST /webhook/bazarr` event containing the subtitle path and language code (`language: "he"`).
2. RightSub Webhook Daemon:
   - **Language Verification**: Confirms language is Hebrew (`he`/`heb`); silently ignores non-Hebrew downloads (English, French, etc.) with 0 overhead.
   - **Path Translation**: Translates paths according to `PATH_MAP` if volume mounts differ between containers.
   - **SubRefine Engine Execution**:
     - Injects invisible Unicode RLM marks for flawless BiDi punctuation in Plex & Infuse.
     - Auto-converts legacy Windows-1255/CP1255 encoding to clean UTF-8.
     - Strips translator spam, promotional ads, and SDH noise tags.
   - **Metadata Touch**: Flushes file timestamps via `os.utime()` so Plex and Infuse detect modifications instantly.
3. The entire mastering cycle completes in **under 0.1 seconds**!

---

### Method B: Custom Post-Processing (For Bare-Metal Setups)

For users running Bazarr directly on the host machine without Docker:

1. Open the Bazarr Web UI (`http://localhost:6767`).
2. Go to **Settings** -> **Subtitles** -> **Post-processing**.
3. Under **Custom Post-Processing**:
   - Check ☑ **Enable custom post-processing**.
   - In **Command**, enter:

#### Windows:
```cmd
rightsub auto "{{subtitles_path}}"
```

#### macOS / Linux:
```bash
rightsub auto "{{subtitles_path}}"
```
4. Click **Save** in the upper left corner.

---

### 🌐 Cross-Container Path Translation (PATH_MAP)

In Docker environments (Docker Compose, Unraid, TrueNAS SCALE, Synology DSM), `*arr` containers and Bazarr often mount media shares under different directory prefixes than RightSub.
For example:
- Bazarr perceives subtitles at: `/data/media/tv/show.he.srt`
- RightSub mounts the media volume at: `/media/tv/show.he.srt`

Specify `PATH_MAP` when launching RightSub:
```bash
# Syntax: FROM_PREFIX:TO_PREFIX
rightsub serve --path-map "/data/media:/media"

# Or in docker-compose.yml:
environment:
  - PATH_MAP=/data/media:/media
```
RightSub automatically rewrites path prefixes for every incoming Sonarr, Radarr, and Bazarr webhook event.

---

## 4. Transmission (Completion Script)

For users running Transmission daemon or client on macOS/Linux/NAS:

### Step 1: Create Script `/usr/local/bin/transmission_rightsub.sh`
```bash
#!/usr/bin/env bash
# Transmission passes $TR_TORRENT_DIR and $TR_TORRENT_NAME
TARGET_DIR="${TR_TORRENT_DIR}/${TR_TORRENT_NAME}"

if [ -e "$TARGET_DIR" ]; then
    /usr/local/bin/rightsub auto "$TARGET_DIR"
fi
```
*(Run `chmod +x /usr/local/bin/transmission_rightsub.sh`)*

### Step 2: Enable in Transmission `settings.json`:
```json
"script-torrent-done-enabled": true,
"script-torrent-done-filename": "/usr/local/bin/transmission_rightsub.sh"
```

---

## 5. Tautulli / Plex (Recently Added Hook)

For users running Tautulli alongside Plex Media Server who want automated subtitle verification the moment new media enters their library:

### How to Configure:
1. In Tautulli, navigate to **Settings** -> **Notification Agents**.
2. Click **Add a Notification Agent** -> **Script**.
3. Set **Script Folder** to your scripts directory.
4. Set **Script File** to `rightsub_arr_hook.bat` (Windows) or `rightsub_arr_hook.sh` (macOS/Linux).
5. In the **Triggers** tab, check ☑ **Recently Added**.
6. In the **Arguments** tab, under **Recently Added**, pass:
   ```text
   <file>
   ```
7. Save the agent. RightSub will verify and master the subtitle before anyone sits down to stream.

---

## 6. Standalone OS Folder Watchers (Non-Arr / Manual Setups)

If you do **not** use automated download managers (such as qBittorrent, Sonarr, or Radarr) and instead manually copy or drop files into a folder, you can configure a native OS-level watcher with **write-settle protection**:

### macOS: Folder Action with Write-Settle Loop
Create an Automator Folder Action on your target folder (e.g. `~/Downloads` or `/Volumes/Media/Incoming`) with a **Run Shell Script** action:

```bash
#!/usr/bin/env bash
for f in "$@"; do
    # Only process video and subtitle files
    case "$f" in
        *.mkv|*.mp4|*.avi|*.srt) ;;
        *) continue ;;
    esac

    # Ensure file is completely written and unlocked before processing
    PREV_SIZE=-1
    while true; do
        CURR_SIZE=$(stat -f%z "$f" 2>/dev/null || echo 0)
        if [ "$CURR_SIZE" -eq "$PREV_SIZE" ] && [ "$CURR_SIZE" -gt 0 ]; then
            break
        fi
        PREV_SIZE="$CURR_SIZE"
        sleep 2
    done

    /usr/local/bin/rightsub auto "$f"
done
```

### Windows: PowerShell Folder Watcher (`rightsub_watcher.ps1`)
Save this script and launch it at startup (or via Windows Task Scheduler):

```powershell
param (
    [string]$WatchFolder = "C:\Users\$env:USERNAME\Downloads"
)

Write-Host "[*] RightSub Folder Watcher active on: $WatchFolder"
$watcher = New-Object System.IO.FileSystemWatcher $WatchFolder, "*.*" -Property @{
    IncludeSubdirectories = $false
    NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite
}

Register-ObjectEvent $watcher "Created" -Action {
    $path = $Event.SourceEventArgs.FullPath
    $ext = [System.IO.Path]::GetExtension($path).ToLower()
    if ($ext -notin @(".mkv", ".mp4", ".avi", ".srt")) { return }

    # Wait until file handle is unlocked (copy/download complete)
    while ($true) {
        try {
            $stream = [System.IO.File]::Open($path, 'Open', 'Read', 'None')
            $stream.Close()
            break
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    Write-Host "[+] Processing completed file: $path"
    rightsub auto "$path"
}

# Keep script running
while ($true) { Start-Sleep -Seconds 60 }
```

---

## 7. 💡 Troubleshooting & Verifying Integrations

To test that your automated pipeline is executing correctly:
1. Run a manual dry run on a sample file:
   ```bash
   rightsub auto "/path/to/Sample.mkv" --dry-run
   ```
2. Inspect the historical report at `docs/analytics/TRAFFIC_REPORT.md` to observe automated hits and processing records.
