# 🔄 RightSub Home Media & Download Integrations Guide

> **Overview**: Automate RightSub across your home lab and media server stack. Run subtitle mastering, BiDi correction, and translation in a 100% hands-off "Set-and-Forget" workflow.

This guide provides tested, copy-pasteable configurations for the most popular home media tools across **Windows** and **macOS/Linux**:
1. [qBittorrent (Run on Completion & Seed-Safe)](#1-qbittorrent-torrent-completion-hook)
2. [Sonarr & Radarr (Custom Connect Scripts)](#2-sonarr--radarr-connect-scripts)
3. [Bazarr (Custom Post-Processing Hook)](#3-bazarr-post-processing-hook)
4. [Transmission (Torrent Completion Script)](#4-transmission-completion-script)
5. [Tautulli / Plex (Recently Added Webhook)](#5-tautulli--plex-recently-added-hook)

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

## 💡 Troubleshooting & Verifying Integrations

To test that your automated pipeline is executing correctly:
1. Run a manual dry run on a sample file:
   ```bash
   rightsub auto "/path/to/Sample.mkv" --dry-run
   ```
2. Inspect the historical report at `docs/analytics/TRAFFIC_REPORT.md` to observe automated hits and processing records.
