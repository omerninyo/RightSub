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

## 2. Sonarr & Radarr (Connect Scripts)

Sonarr and Radarr allow custom scripts to execute immediately after an episode or movie has been imported and organized into your library (`On Download` and `On Upgrade`).

### What Happens Automatically:
RightSub inspects the newly imported media file:
1. Extracts embedded English or Hebrew subtitle streams from MKV/MP4 containers.
2. If an external Hebrew subtitle exists, masters it immediately for Plex (BiDi RLM injection, UTF-8 charset normalization, SDH and ad cleaning).
3. If no Hebrew subtitle exists, pre-splits the master English track into ~210 cue waves ready for AI translation.

### Step 1: Create the Hook Script

#### Windows: `C:\Scripts\rightsub_arr_hook.bat`
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

#### macOS / Linux: `/usr/local/bin/rightsub_arr_hook.sh`
```bash
#!/usr/bin/env bash
TARGET_PATH="${sonarr_episodefile_path:-$radarr_moviefile_path}"

if [ -n "$TARGET_PATH" ] && [ -f "$TARGET_PATH" ]; then
    /usr/local/bin/rightsub auto "$TARGET_PATH"
fi
```
*(Make sure to grant execution permissions: `chmod +x /usr/local/bin/rightsub_arr_hook.sh`)*

### Step 2: Configure in Sonarr / Radarr UI
1. Navigate to **Settings** -> **Connect**.
2. Click the **`+`** icon and select **Custom Script**.
3. Fill in the fields:
   - **Name**: `RightSub Auto-Master`
   - **Notification Triggers**: Check ☑ **On Download** and ☑ **On Upgrade**.
   - **Path**: Set to your script path (`C:\Scripts\rightsub_arr_hook.bat` or `/usr/local/bin/rightsub_arr_hook.sh`).
4. Click **Test** and then **Save**.

---

## 3. Bazarr (Post-Processing Hook)

Bazarr crawls 30+ internet providers to find community-uploaded subtitles. However, downloaded Hebrew subtitles routinely suffer from reversed punctuation (`? ! .`), legacy CP1255 encoding, and promo spam.

By attaching RightSub as a Post-Processing script, Bazarr handles the downloading while RightSub automatically masters every downloaded file.

### How to Configure:
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
