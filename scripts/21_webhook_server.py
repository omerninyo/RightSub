#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
21_webhook_server.py
---------------------
Native lightweight Webhook Daemon and automation listener for RightSub.
Seamlessly integrates Sonarr, Radarr, and Bazarr with zero external dependencies.

Features:
1. Lightweight Standard-Library HTTP Daemon:
   Runs via `http.server.ThreadingHTTPServer` consuming under 15 MB RAM idle.
2. Native *arr & Bazarr Parsers:
   - POST /webhook/sonarr: Handles Download, Upgrade, Rename events, companions, and Test pings.
   - POST /webhook/radarr: Handles Download, MovieFileImported events, and Test pings.
   - POST /webhook/bazarr: Handles subtitle Download events (Hebrew filtering) and Test pings.
   - POST /webhook/generic (or /process): Ad-hoc path processing.
   - GET /health (or /): Health checks, uptime, and processed metrics.
3. Cross-Container Volume Path Translation (PATH_MAP):
   Translates container mount disparities (e.g. `/data/media:/media`).
4. Seed-Safe Preservation & Media Server Acceleration:
   Enforces seed safety for active torrents while updating `os.utime()` for instant Plex/Infuse recognition.
"""

import os
import sys
import json
import time
import re
import argparse
from pathlib import Path
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import List, Tuple, Dict, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SERVER_VERSION = "1.4.0"
DEFAULT_PORT = 8775
DEFAULT_HOST = "0.0.0.0"

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".m4v", ".avi", ".ts", ".mov", ".webm"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".ssa", ".sub"}

# Dynamically import SubRefine engine from 07_fix_plex_punctuation.py
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import importlib
    m07 = importlib.import_module("07_fix_plex_punctuation")
    process_file = getattr(m07, "process_file", None)
    detect_hebrew = getattr(m07, "detect_hebrew", None)
except Exception as e:
    process_file = None
    detect_hebrew = None

# Global server metrics
START_TIME = time.time()
METRICS = {
    "events_count": 0,
    "processed_count": 0,
    "error_count": 0,
}


def parse_path_map(mapping_str: Optional[str]) -> List[Tuple[str, str]]:
    """
    Parses PATH_MAP environment variable or CLI argument.
    Format: FROM_PREFIX:TO_PREFIX[,FROM_2:TO_2]
    Example: '/data/media:/media,/downloads:/mnt/downloads'
    """
    if not mapping_str:
        return []
    
    pairs = []
    # Split by comma or semicolon
    raw_pairs = re.split(r'[,;]', mapping_str.strip())
    for item in raw_pairs:
        item = item.strip()
        if not item or ":" not in item:
            continue
        # Split on the first colon or handle Windows drive letters (e.g. C:\from:D:\to)
        # If drive letter is present on the right or left:
        parts = item.split(":")
        if len(parts) == 2:
            from_p, to_p = parts[0].strip(), parts[1].strip()
        elif len(parts) == 4 and len(parts[0]) == 1 and len(parts[2]) == 1:
            # e.g. C:\data:D:\media
            from_p = f"{parts[0]}:{parts[1]}".strip()
            to_p = f"{parts[2]}:{parts[3]}".strip()
        elif len(parts) == 3:
            # either left or right had a drive letter
            if len(parts[0]) == 1:
                from_p = f"{parts[0]}:{parts[1]}".strip()
                to_p = parts[2].strip()
            else:
                from_p = parts[0].strip()
                to_p = f"{parts[1]}:{parts[2]}".strip()
        else:
            from_p, to_p = parts[0].strip(), parts[-1].strip()
        
        # Normalize slashes for comparison
        from_norm = from_p.replace("\\", "/").rstrip("/")
        to_norm = to_p.replace("\\", "/").rstrip("/")
        if from_norm:
            pairs.append((from_norm, to_norm))
    return pairs


def translate_path(raw_path: str, path_map: List[Tuple[str, str]]) -> Path:
    """
    Translates an incoming file path from another container's perspective
    into the local file system path according to path_map.
    """
    if not raw_path:
        return Path("")
    
    clean_path = str(raw_path).replace("\\", "/")
    
    for from_p, to_p in path_map:
        if clean_path == from_p:
            clean_path = to_p
            break
        elif clean_path.startswith(from_p + "/"):
            suffix = clean_path[len(from_p):]
            clean_path = to_p + suffix
            break
    
    return Path(clean_path)


def is_hebrew_content_sample(file_path: Path) -> bool:
    """
    Quickly samples an SRT file to verify whether it contains Hebrew dialogue.
    """
    if not file_path.is_file():
        return False
    try:
        raw = file_path.read_bytes()[:65536]
        # Check UTF-8 / UTF-8-SIG
        try:
            text = raw.decode("utf-8-sig")
            he_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
            if he_chars >= 5:
                return True
        except UnicodeDecodeError:
            pass
        # Check Windows-1255 / CP1255
        cp1255_he_bytes = sum(1 for b in raw if 0xE0 <= b <= 0xFA)
        if cp1255_he_bytes >= 5:
            return True
        return False
    except Exception:
        return False


def discover_hebrew_subtitles_for_video(video_path: Path) -> List[Path]:
    """
    Discovers Hebrew subtitle files associated with a given video file.
    Checks:
    1. <stem>.he.srt, <stem>.heb.srt, <stem>.hebrew.srt
    2. <stem>.srt (if it contains Hebrew characters)
    3. Any .srt matching <stem> in parent dir or Subs/ subfolder that is Hebrew.
    """
    if not video_path.exists():
        return []
    
    parent_dir = video_path.parent
    stem = video_path.stem
    candidates: List[Path] = []
    
    # 1. Standard Plex naming
    for ext in [".he.srt", ".heb.srt", ".hebrew.srt"]:
        cand = parent_dir / f"{stem}{ext}"
        if cand.is_file() and cand not in candidates:
            candidates.append(cand)
    
    # 2. Base .srt match
    base_srt = parent_dir / f"{stem}.srt"
    if base_srt.is_file() and base_srt not in candidates:
        if is_hebrew_content_sample(base_srt):
            candidates.append(base_srt)
            
    # 3. Subs folder
    for sub_dir_name in ["Subs", "subs", "Subtitles", "subtitles"]:
        sub_dir = parent_dir / sub_dir_name
        if sub_dir.is_dir():
            for srt_file in sub_dir.glob("*.srt"):
                if srt_file.is_file() and not srt_file.name.endswith(".bak"):
                    if is_hebrew_content_sample(srt_file) and srt_file not in candidates:
                        candidates.append(srt_file)
                        
    return candidates


def master_subtitle_file(
    file_path: Path,
    in_place: bool = True,
    seed_safe: bool = False,
    clean_ads: bool = True,
    backup: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Applies SubRefine mastering (RLM, BiDi, CP1255 fix, ad cleaning) to a subtitle file.
    Returns status dictionary.
    """
    if not file_path.is_file():
        return {
            "file": str(file_path),
            "status": "not_found",
            "message": "File not found on disk"
        }
    
    if process_file is None:
        return {
            "file": str(file_path),
            "status": "error",
            "message": "SubRefine mastering engine (07_fix_plex_punctuation) not available"
        }
    
    # Seed-safe check: If seed_safe is enabled and the target is e.g. "movie.srt" (not ".he.srt")
    actual_in_place = in_place
    output_path = None
    name_lower = file_path.name.lower()
    
    if seed_safe and not (name_lower.endswith(".he.srt") or name_lower.endswith(".heb.srt")):
        # Generate companion .he.srt instead of overwriting torrent file
        stem = file_path.stem
        output_path = file_path.parent / f"{stem}.he.srt"
        actual_in_place = False
    
    try:
        subs, mods, ads, status = process_file(
            file_path,
            output_path=output_path,
            in_place=actual_in_place,
            dry_run=dry_run,
            backup=backup,
            clean_ads=clean_ads,
            force=False
        )
        
        # Accelerate media server detection via timestamp touch
        target_dest = file_path if actual_in_place else (output_path or file_path)
        if not dry_run and target_dest.exists():
            try:
                os.utime(target_dest, None)
            except Exception:
                pass
                
        if status in ("processed", "dry_run"):
            METRICS["processed_count"] += 1
            
        detailed_status = status
        if status == "processed":
            detailed_status = "already compliant" if mods == 0 and ads == 0 else "fixed"
            
        return {
            "file": str(target_dest),
            "status": detailed_status,
            "total_subtitles": subs,
            "lines_adjusted": mods,
            "ads_removed": ads
        }
    except Exception as exc:
        METRICS["error_count"] += 1
        return {
            "file": str(file_path),
            "status": "error",
            "message": str(exc)
        }


def process_target_path(
    target_path: Path,
    options: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Determines whether target_path is a subtitle, a video file, or a directory,
    and executes appropriate mastering.
    """
    results: List[Dict[str, Any]] = []
    
    if not target_path.exists():
        results.append({
            "target": str(target_path),
            "status": "not_found",
            "message": "Target path does not exist on disk (verify PATH_MAP or container volumes)"
        })
        return results
    
    # 1. Target is a single subtitle file
    if target_path.is_file() and target_path.suffix.lower() in SUBTITLE_EXTENSIONS:
        res = master_subtitle_file(
            target_path,
            in_place=options.get("in_place", True),
            seed_safe=options.get("seed_safe", False),
            clean_ads=options.get("clean_ads", True),
            backup=options.get("backup", False),
            dry_run=options.get("dry_run", False)
        )
        results.append(res)
        return results
    
    # 2. Target is a video file
    if target_path.is_file() and target_path.suffix.lower() in VIDEO_EXTENSIONS:
        companions = discover_hebrew_subtitles_for_video(target_path)
        if not companions:
            results.append({
                "target": str(target_path),
                "status": "no_subtitles_found",
                "message": f"No companion Hebrew subtitles found for video {target_path.name}"
            })
            return results
        
        for comp in companions:
            res = master_subtitle_file(
                comp,
                in_place=options.get("in_place", True),
                seed_safe=options.get("seed_safe", False),
                clean_ads=options.get("clean_ads", True),
                backup=options.get("backup", False),
                dry_run=options.get("dry_run", False)
            )
            results.append(res)
        return results
    
    # 3. Target is a directory
    if target_path.is_dir():
        for srt_path in target_path.rglob("*.srt"):
            if srt_path.is_file() and not srt_path.name.endswith(".bak"):
                if is_hebrew_content_sample(srt_path):
                    res = master_subtitle_file(
                        srt_path,
                        in_place=options.get("in_place", True),
                        seed_safe=options.get("seed_safe", False),
                        clean_ads=options.get("clean_ads", True),
                        backup=options.get("backup", False),
                        dry_run=options.get("dry_run", False)
                    )
                    results.append(res)
        if not results:
            results.append({
                "target": str(target_path),
                "status": "no_subtitles_found",
                "message": "No Hebrew subtitles found in directory"
            })
        return results
    
    results.append({
        "target": str(target_path),
        "status": "unsupported_type",
        "message": f"Unsupported target file format: {target_path.suffix}"
    })
    return results


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler for RightSub Webhook Daemon.
    Routes:
      GET  /health, GET /
      POST /webhook/sonarr
      POST /webhook/radarr
      POST /webhook/bazarr
      POST /webhook/generic, POST /process
    """
    
    # Config injected from server instance
    server_options: Dict[str, Any] = {}
    path_map: List[Tuple[str, str]] = []
    
    def log_message(self, format, *args):
        # Clean formatted logging with timestamp
        sys.stderr.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [Webhook] {format % args}\n")
    
    def _send_json(self, status_code: int, data: Dict[str, Any]):
        response_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("X-Powered-By", f"RightSub/{SERVER_VERSION}")
        self.end_headers()
        self.wfile.write(response_bytes)
        
    def _read_json_payload(self) -> Optional[Dict[str, Any]]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        try:
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)
        except Exception as e:
            self.log_message("Failed to parse JSON body: %s", str(e))
            return None

    def do_GET(self):
        url_path = self.path.split("?")[0].rstrip("/")
        if url_path in ("", "/health"):
            uptime = round(time.time() - START_TIME, 2)
            self._send_json(200, {
                "status": "healthy",
                "service": "RightSub Webhook Daemon",
                "version": SERVER_VERSION,
                "uptime_seconds": uptime,
                "metrics": METRICS,
                "endpoints": [
                    "/health",
                    "/webhook/sonarr",
                    "/webhook/radarr",
                    "/webhook/bazarr",
                    "/webhook/generic"
                ]
            })
        else:
            self._send_json(404, {
                "error": "Not Found",
                "path": self.path,
                "available_endpoints": ["/health", "/webhook/sonarr", "/webhook/radarr", "/webhook/bazarr", "/webhook/generic"]
            })

    def do_POST(self):
        url_path = self.path.split("?")[0].rstrip("/")
        METRICS["events_count"] += 1
        
        payload = self._read_json_payload()
        if payload is None:
            self._send_json(400, {"error": "Invalid or malformed JSON payload"})
            return
            
        if url_path == "/webhook/sonarr":
            self.handle_sonarr(payload)
        elif url_path == "/webhook/radarr":
            self.handle_radarr(payload)
        elif url_path == "/webhook/bazarr":
            self.handle_bazarr(payload)
        elif url_path in ("/webhook/generic", "/process"):
            self.handle_generic(payload)
        else:
            self._send_json(404, {
                "error": "Not Found",
                "path": self.path,
                "available_endpoints": ["/webhook/sonarr", "/webhook/radarr", "/webhook/bazarr", "/webhook/generic"]
            })

    def handle_sonarr(self, payload: Dict[str, Any]):
        """
        Handles Sonarr webhook events.
        Supported events: Test, Download, Upgrade, Rename.
        """
        event_type = payload.get("eventType") or payload.get("event") or ""
        
        # 1. Test ping
        if event_type.lower() == "test":
            self.log_message("Received Sonarr test ping.")
            self._send_json(200, {
                "status": "ok",
                "event": "Test",
                "message": "Sonarr Webhook test received successfully"
            })
            return
            
        # 2. Extract targets
        targets: List[str] = []
        ep_file = payload.get("episodeFile", {})
        if isinstance(ep_file, dict) and ep_file.get("path"):
            targets.append(ep_file["path"])
            
        ep_files = payload.get("episodeFiles", [])
        if isinstance(ep_files, list):
            for ef in ep_files:
                if isinstance(ef, dict) and ef.get("path"):
                    targets.append(ef["path"])
                    
        # Fallback to series path if no episode file path is specified
        if not targets and payload.get("series", {}).get("path"):
            targets.append(payload["series"]["path"])
            
        if not targets:
            self._send_json(200, {
                "status": "ignored",
                "event": event_type,
                "message": "No episodeFile.path or series.path found in payload"
            })
            return
            
        results = []
        for raw_target in targets:
            local_target = translate_path(raw_target, self.path_map)
            self.log_message("Sonarr [%s] Translated '%s' -> '%s'", event_type, raw_target, local_target)
            res = process_target_path(local_target, self.server_options)
            results.extend(res)
            
        self._send_json(200, {
            "status": "ok",
            "event": event_type,
            "processed_items": len(results),
            "results": results
        })

    def handle_radarr(self, payload: Dict[str, Any]):
        """
        Handles Radarr webhook events.
        Supported events: Test, Download, MovieFileImported, Upgrade, Rename.
        """
        event_type = payload.get("eventType") or payload.get("event") or ""
        
        # 1. Test ping
        if event_type.lower() == "test":
            self.log_message("Received Radarr test ping.")
            self._send_json(200, {
                "status": "ok",
                "event": "Test",
                "message": "Radarr Webhook test received successfully"
            })
            return
            
        # 2. Extract targets
        targets: List[str] = []
        movie_file = payload.get("movieFile", {})
        if isinstance(movie_file, dict) and movie_file.get("path"):
            targets.append(movie_file["path"])
            
        movie_files = payload.get("movieFiles", [])
        if isinstance(movie_files, list):
            for mf in movie_files:
                if isinstance(mf, dict) and mf.get("path"):
                    targets.append(mf["path"])
                    
        if not targets and payload.get("movie", {}).get("folderPath"):
            targets.append(payload["movie"]["folderPath"])
            
        if not targets:
            self._send_json(200, {
                "status": "ignored",
                "event": event_type,
                "message": "No movieFile.path or movie.folderPath found in payload"
            })
            return
            
        results = []
        for raw_target in targets:
            local_target = translate_path(raw_target, self.path_map)
            self.log_message("Radarr [%s] Translated '%s' -> '%s'", event_type, raw_target, local_target)
            res = process_target_path(local_target, self.server_options)
            results.extend(res)
            
        self._send_json(200, {
            "status": "ok",
            "event": event_type,
            "processed_items": len(results),
            "results": results
        })

    def handle_bazarr(self, payload: Dict[str, Any]):
        """
        Handles Bazarr webhook events.
        Supported events: Test, download / Subtitle Downloaded.
        """
        event_type = payload.get("event") or payload.get("eventType") or ""
        
        # 1. Test ping
        if str(event_type).lower() == "test":
            self.log_message("Received Bazarr test ping.")
            self._send_json(200, {
                "status": "ok",
                "event": "test",
                "message": "Bazarr Webhook test received successfully"
            })
            return
            
        # 2. Subtitle details
        subtitle_info = payload.get("subtitle", {})
        sub_path = subtitle_info.get("path") if isinstance(subtitle_info, dict) else None
        sub_lang = subtitle_info.get("language", "").lower() if isinstance(subtitle_info, dict) else ""
        
        # If no subtitle object, check top-level path or file
        if not sub_path:
            sub_path = payload.get("path") or payload.get("file")
            
        if not sub_path:
            self._send_json(200, {
                "status": "ignored",
                "event": event_type,
                "message": "No subtitle.path found in payload"
            })
            return
            
        # 3. Language filter: Ignore non-Hebrew downloads
        if sub_lang and sub_lang not in ("he", "heb", "hebrew", "iw"):
            self.log_message("Bazarr: Ignoring non-Hebrew subtitle download (lang=%s)", sub_lang)
            self._send_json(200, {
                "status": "skipped",
                "language": sub_lang,
                "message": f"Skipped non-Hebrew subtitle download ({sub_lang})"
            })
            return
            
        local_target = translate_path(sub_path, self.path_map)
        self.log_message("Bazarr [%s] Translated '%s' -> '%s'", event_type, sub_path, local_target)
        
        # For Bazarr, the file itself is the downloaded subtitle: master directly
        res = master_subtitle_file(
            local_target,
            in_place=self.server_options.get("in_place", True),
            seed_safe=self.server_options.get("seed_safe", False),
            clean_ads=self.server_options.get("clean_ads", True),
            backup=self.server_options.get("backup", False),
            dry_run=self.server_options.get("dry_run", False)
        )
        
        self._send_json(200, {
            "status": "ok",
            "event": event_type,
            "processed_items": 1,
            "result": res
        })

    def handle_generic(self, payload: Dict[str, Any]):
        """
        Handles generic / ad-hoc processing requests.
        Payload: {"path": "/path/to/media/or/subtitle.srt"}
        """
        raw_path = payload.get("path") or payload.get("target")
        if not raw_path:
            self._send_json(400, {
                "error": "Missing 'path' or 'target' field in JSON payload"
            })
            return
            
        local_target = translate_path(raw_path, self.path_map)
        self.log_message("Generic: Translated '%s' -> '%s'", raw_path, local_target)
        results = process_target_path(local_target, self.server_options)
        
        self._send_json(200, {
            "status": "ok",
            "processed_items": len(results),
            "results": results
        })


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    path_map_str: Optional[str] = None,
    in_place: bool = True,
    seed_safe: bool = False,
    clean_ads: bool = True,
    backup: bool = False,
    dry_run: bool = False
):
    """
    Initializes and starts the RightSub Webhook HTTP Server.
    """
    path_map = parse_path_map(path_map_str)
    
    server_options = {
        "in_place": in_place,
        "seed_safe": seed_safe,
        "clean_ads": clean_ads,
        "backup": backup,
        "dry_run": dry_run,
    }
    
    # Configure handler class
    WebhookRequestHandler.server_options = server_options
    WebhookRequestHandler.path_map = path_map
    
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, WebhookRequestHandler)
    
    print("==================================================================")
    print(f"  RightSub Webhook Daemon v{SERVER_VERSION}")
    print(f"  Listening on:   http://{host}:{port}")
    print(f"  Path Mappings:  {len(path_map)} active rules")
    for from_p, to_p in path_map:
        print(f"    • '{from_p}' -> '{to_p}'")
    print(f"  SubRefine Mode: {'In-Place' if in_place and not seed_safe else 'Seed-Safe (.he.srt sidecars)'}")
    print(f"  Ad Cleaner:     {'Active' if clean_ads else 'Disabled'}")
    print(f"  Backup (.bak):  {'Enabled' if backup else 'Disabled'}")
    print(f"  Dry-Run Mode:   {'YES (No modifications)' if dry_run else 'NO (Live modifications)'}")
    print("==================================================================")
    print("Endpoints ready for Sonarr, Radarr, and Bazarr webhooks.")
    print("Press Ctrl+C to terminate.")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down RightSub Webhook Daemon...")
    finally:
        httpd.server_close()
        print("Server gracefully stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="RightSub Webhook Daemon: native lightweight listener for Sonarr, Radarr, and Bazarr."
    )
    env_port = int(os.environ.get("RIGHTSUB_PORT", DEFAULT_PORT))
    env_host = os.environ.get("RIGHTSUB_HOST", DEFAULT_HOST)
    env_path_map = os.environ.get("PATH_MAP", "")
    
    parser.add_argument("--host", "-H", default=env_host, help=f"Host/IP to bind to (default: {env_host})")
    parser.add_argument("--port", "-p", type=int, default=env_port, help=f"Port to listen on (default: {env_port})")
    parser.add_argument("--path-map", default=env_path_map, help="Container volume prefix mappings (e.g. /data/media:/media)")
    parser.add_argument("--seed-safe", action="store_true", help="Never modify original torrent subtitle files; produce .he.srt sidecars")
    parser.add_argument("--no-clean-ads", action="store_true", help="Do not strip promo spam and credits")
    parser.add_argument("--backup", action="store_true", help="Create .bak backups before in-place modifications")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without modifying any files on disk")
    
    args = parser.parse_args()
    
    run_server(
        host=args.host,
        port=args.port,
        path_map_str=args.path_map,
        in_place=not args.seed_safe,
        seed_safe=args.seed_safe,
        clean_ads=not args.no_clean_ads,
        backup=args.backup,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
