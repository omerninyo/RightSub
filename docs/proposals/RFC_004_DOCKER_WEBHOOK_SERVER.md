# 🔮 Future Architectural Specification: Docker Webhook Daemon for Sonarr, Radarr, and Bazarr

<p align="left">
  <b>Language / שפה:</b>
  <b>English</b> |
  <a href="RFC_004_DOCKER_WEBHOOK_SERVER.he.md"><b>עברית</b></a>
</p>

This document formalizes the design principles, architecture, API contracts, and deployment model for **RightSub's native Webhook Server and official Docker container**.  
The objective is to enable turnkey, zero-kludge integration into home media environments (Unraid, TrueNAS SCALE, Synology DSM, Docker Compose) and downloader stacks (`*arr` and Bazarr) without requiring host-level Python installations or brittle custom scripts.

---

## 1. Problem Statement & Background

1. **Container Isolation on Homelab & NAS Hardware:**
   - Modern homelabs and NAS appliances run Sonarr, Radarr, and Bazarr in isolated Docker containers.
   - Operating systems like Unraid, TrueNAS SCALE, and Synology DSM discourage direct package/library installations onto the host OS.
2. **The Failure of In-Container Custom Scripts:**
   - Attempting to configure custom post-processing scripts inside Bazarr or Sonarr that call `rightsub auto` fails immediately with `command not found`, because RightSub is not installed inside the third-party container.
3. **Current Community Workarounds ("Kludgy Scripts"):**
   - Users currently build ad-hoc Flask servers or fragile cron jobs to intercept events and trigger custom subtitle commands.
4. **The Architectural Opportunity in Native `*arr` / Bazarr Webhooks:**
   - Sonarr, Radarr, and Bazarr feature robust built-in Webhook notification engines that emit structured HTTP POST JSON payloads the moment an episode or subtitle file lands on disk.

---

## 2. Core Goals & Design Tenets

1. **Zero Heavy Server Dependencies:**
   - The Webhook server is embedded directly into the RightSub codebase, invokable via `rightsub serve --port 8775`.
   - Built on lightweight Python standard libraries (`http.server` / `asyncio`) consuming under 15 MB RAM idle.
2. **Native Parsing for Sonarr, Radarr, and Bazarr Payloads:**
   - Automatic schema matching without complex user parameter tuning.
3. **Autonomous Container Path Mapping (`PATH_MAP`):**
   - Bridges path disparities when Sonarr sees `/data/media/tv` while RightSub mounts `/tv`.
4. **Seed-Safe Guarantee for Active Torrents:**
   - Never alters original torrent subtitle files in-place; always generates mastered sidecar files (`<stem>.he.srt`).
5. **Accelerated Metadata Sync for Plex & Infuse:**
   - Automatic `os.utime()` flushing ensuring instantaneous player index recognition.

---

## 3. API Contract & Endpoint Specifications

Default listening port: `8775` (configurable via `RIGHTSUB_PORT` or `--port` flag).

### A. `POST /webhook/sonarr` (Sonarr Events)
- **Supported Events:** `Download`, `Upgrade`, `Rename`.
- **Payload Schema:**
  ```json
  {
    "eventType": "Download",
    "series": {
      "title": "Boston Legal",
      "path": "/data/media/tv/Boston Legal"
    },
    "episodeFile": {
      "relativePath": "Season 01/Boston Legal - S01E01.mkv",
      "path": "/data/media/tv/Boston Legal/Season 01/Boston Legal - S01E01.mkv"
    }
  }
  ```
- **Processing Flow:**
  1. Translates path via `PATH_MAP`.
  2. Scans episode directory for existing companion `.srt` files or embedded subtitle streams.
  3. Executes `SubRefine` (BiDi RLM punctuation, SDH removal, CP1255 encoding repair).
  4. Returns `200 OK` with execution report.

### B. `POST /webhook/radarr` (Radarr Events)
- **Supported Events:** `Download`, `MovieFileImported`.
- **Payload Schema:**
  ```json
  {
    "eventType": "Download",
    "movie": {
      "title": "Gladiator",
      "folderPath": "/data/media/movies/Gladiator (2000)"
    },
    "movieFile": {
      "relativePath": "Gladiator (2000).mkv",
      "path": "/data/media/movies/Gladiator (2000)/Gladiator (2000).mkv"
    }
  }
  ```

### C. `POST /webhook/bazarr` (Bazarr Events)
- **Supported Events:** `Subtitle Downloaded`.
- **Payload Schema:**
  ```json
  {
    "event": "download",
    "subtitle": {
      "path": "/data/media/tv/Boston Legal/Season 01/Boston Legal - S01E01.he.srt",
      "language": "he"
    }
  }
  ```
- **Processing Flow:**
  - Verifies language is Hebrew (`he` / `heb`).
  - Executes instant mastering (RLM injection, CP1255 fix, SDH cleaning) in ~0.05s to 0.2s.

### D. `POST /webhook/generic` or `POST /process`
- Generic endpoint for ad-hoc external calls:
  ```json
  {
    "path": "/media/tv/show.srt",
    "action": "refine"
  }
  ```

### E. `GET /health`
- Health check and operational status:
  ```json
  {
    "status": "healthy",
    "version": "1.4.0",
    "uptime_seconds": 86400,
    "processed_count": 142
  }
  ```

---

## 4. Container Path Mapping (`PATH_MAP`)

Container volumes frequently expose different mount prefixes.  
RightSub supports flexible path translation via `PATH_MAP`:

**Syntax:** `MAPPING=FROM_PREFIX:TO_PREFIX[,FROM_2:TO_2]`  
**Example:**
```bash
PATH_MAP="/data/media:/media"
```
Translates incoming payload path:
`/data/media/tv/Boston Legal/S01E01.mkv`  
Into container path:
`/media/tv/Boston Legal/S01E01.mkv`

---

## 5. Deployment Configurations: Docker Compose & Unraid

### Reference `docker-compose.yml`:
```yaml
version: "3.8"

services:
  rightsub:
    image: ghcr.io/omerninyo/rightsub:latest
    container_name: rightsub
    restart: unless-stopped
    ports:
      - "8775:8775"
    environment:
      - RIGHTSUB_PORT=8775
      - PATH_MAP=/data/media:/media
      - PUID=1000
      - PGID=1000
      - TZ=Asia/Jerusalem
    volumes:
      - /mnt/storage/media:/media
      - /mnt/storage/appdata/rightsub:/config
```

### Sonarr / Radarr Configuration:
1. Navigate to: `Settings` -> `Connect` -> click `+` and choose `Webhook`.
2. **Name:** `RightSub BiDi Master`
3. **URL:** `http://rightsub:8775/webhook/sonarr` (or Docker host IP).
4. **Method:** `POST`
5. **Triggers:** Check `On Download` and `On Upgrade`.
6. Click **Test** and **Save**.

### Bazarr Configuration:
1. Navigate to: `Settings` -> `Notifications` -> select `Webhook`.
2. **URL:** `http://rightsub:8775/webhook/bazarr`
3. **Notification Types:** Check `On Subtitles Download`.

---

## 6. Implementation Phasing for Version 1.4.0

1. **Phase 1: Core Webhook Daemon:**
   - Implement `src/daemon/webhook_server.py` with zero heavy dependencies.
   - Built-in Sonarr, Radarr, and Bazarr parsers.
2. **Phase 2: Asynchronous Worker Queue & Path Mapping:**
   - Background thread-pool processing preventing HTTP timeouts on large batches.
   - Prefix translation logic.
3. **Phase 3: Docker Packaging & GHCR Pipeline:**
   - Streamlined `Dockerfile` (`python:3.11-slim`).
   - GitHub Actions workflow publishing multi-arch images (`amd64`, `arm64`) to `ghcr.io`.
   - Official Unraid Community Applications template XML.
