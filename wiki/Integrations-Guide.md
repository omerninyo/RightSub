# 🔄 RightSub Home Media & Download Integrations Guide

> **Overview**: Automate RightSub across your home lab and media server stack. Run subtitle mastering, BiDi correction, and translation in a 100% hands-off "Set-and-Forget" workflow.

This guide provides tested, copy-pasteable configurations for the most popular home media tools across **Windows** and **macOS/Linux**:
0. [The Recommended 2-Phase Strategy & Daemon Architecture](#0-the-recommended-2-phase-strategy--daemon-architecture)
1. [qBittorrent (Run on Completion & Seed-Safe)](#1-qbittorrent-torrent-completion-hook)
2. [Sonarr & Radarr (Webhook Integration or Post-Import Script)](#2-sonarr--radarr-webhook-integration-or-post-import-script)
3. [Bazarr (Webhook Daemon or Post-Processing Hook)](#3-bazarr-webhook-daemon-or-post-processing-hook)
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
   RightSub recursively scans the entire directory, converts legacy CP1255 / ISO-8859-8 charsets to clean UTF-8, injects RLM marks for flawless Plex BiDi punctuation, cleans ads and SDH hearing-impaired noise, and outputs standard `.he.srt` files without modifying original torrent downloads.
2. **Phase 2: Event-Driven Automation (Set-and-Forget)**  
   From this point on, **do not run** a heavy, polling background directory scanner. Instead, connect your downloaders (qBittorrent, Sonarr, Radarr, Bazarr) to trigger RightSub **the exact second a new file finishes downloading**.

### 🏛️ Why Event-Driven Hooks Beat a 24/7 Polling Daemon

Users often ask: *"Why doesn't RightSub run as a persistent background daemon that watches directories?"*

In home media environments, constant filesystem polling is an **architectural anti-pattern**:
1. **Race Conditions & Partial File Corruption**: When torrent clients download large 15GB files or extract multi-part archives, disk writes take minutes or hours. A naive watcher daemon detects file creation instantly and attempts to read or lock partial, incompletely written files — resulting in crashes and corrupt subtitle output.
2. **Zero Idle Resource Consumption**: Background daemons keep Python runtime active continuously (40–80 MB RAM) and wake CPU cores periodically. Event-driven hooks consume **0% CPU and 0 MB RAM when idle** — RightSub spawns for a fraction of a second, masters the subtitle, and exits cleanly.
3. **Atomic, Verified Execution**: Downloaders know with mathematical certainty when a file has passed hash verification, finished writing, and closed its file handles. Triggering at that moment guarantees zero errors.

---

## 1. qBittorrent (Torrent Completion Hook)

qBittorrent can invoke RightSub the exact millisecond a download finishes.

### Key Benefit: Seed-Safe Guarantee
Modifying an active torrent's subtitle file (changing its name to `Movie.he.srt` or editing punctuation directly) changes the file's hash and triggers qBittorrent I/O recheck errors.  
RightSub's **Seed-Safe** engine avoids this by **duplicating** the subtitle into a clean `.he.srt` file while leaving the original file **100% bit-for-bit intact**. Active torrent seeding is never interrupted.

### How to Configure:
1. Open qBittorrent.
2. Go to: **Tools** -> **Options** (or `Preferences` on macOS).
3. Select the **Downloads** tab in the sidebar.
4. Scroll to the bottom and check:  
   ☑ **"Run external program on torrent completion"**.
5. Enter the command for your operating system:

#### Windows (CMD / PowerShell):
```cmd
rightsub auto "%F"
```
*(If `rightsub` is not in your system PATH, use: `python "C:\path\to\RightSub\rightsub.py" auto "%F"`)*

#### macOS / Linux (Terminal):
```bash
/usr/local/bin/rightsub auto "%F"
```
*(Or `~/.local/bin/rightsub auto "%F"`)*

> **Note on `%F`**: qBittorrent replaces `%F` with the absolute path of the downloaded file or directory.

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
*(Grant execution permissions: `chmod +x /usr/local/bin/transmission_rightsub.sh`)*

### Step 2: Configure in Transmission `settings.json`:
```json
"script-torrent-done-enabled": true,
"script-torrent-done-filename": "/usr/local/bin/transmission_rightsub.sh"
```

---

## 5. Tautulli / Plex (Recently Added Hook)

For users running Tautulli to monitor Plex libraries and trigger instant subtitle checks whenever new items land:

1. Go to: **Settings** -> **Notification Agents**.
2. Click **Add a Notification Agent** -> **Script**.
3. Configuration:
   - **Script Folder**: Folder containing your script.
   - **Script File**: Script invoking `rightsub auto "{file}"`.
   - **Triggers**: Check ☑ **Recently Added**.
   - **Arguments** (under Recently Added): `"{file}"`

---

## 6. Standalone OS Folder Watchers (Non-Arr / Manual Setups)

If you do not use automated downloaders and prefer dropping video files into an intake folder manually:

### macOS / Linux (using `fswatch`):
```bash
fswatch -0 -e ".*" -i "\\.(mkv|mp4|srt)$" /path/to/incoming | while read -d "" event; do
    echo "[*] New file detected: $event"
    rightsub auto "$event"
done
```

### Windows (PowerShell FileSystemWatcher):
```powershell
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "C:\Media\Incoming"
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

Register-ObjectEvent $watcher "Created" -Action {
    $path = $Event.SourceEventArgs.FullPath
    if ($path -match '\.(mkv|mp4|srt)$') {
        Start-Sleep -Seconds 5 # Wait for write flush
        & rightsub auto "$path"
    }
}
```

---

## 7. Troubleshooting & Verifying Integrations

### How to Verify RightSub Triggered Successfully:
1. **Plex / Infuse Validation**:
   - Check Hebrew punctuation: question marks (`?`), exclamation points (`!`), and periods should sit at the correct natural Hebrew ends of lines.
2. **Log Verification**:
   - Webhook server prints structured timestamped logs:
     `[Webhook] Sonarr [Download] Translated '/data/media/tv/ep.mkv' -> '/media/tv/ep.mkv'`
     `[Webhook] Bazarr [download] Processed 1 subs (1 lines adjusted, fixed) -> Show.S01E01.he.srt`
3. **Backup Protection**:
   - When modifying in-place, pass `--backup` to preserve the original subtitle as `.srt.bak`.

---

<p align="center">
  <b>RightSub Automation Suite</b> • <i>Subtitles Done Right, 100% Hands-Free.</i>
</p>
