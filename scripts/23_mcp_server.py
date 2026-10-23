#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
23_mcp_server.py
-----------------
RightSub Native Model Context Protocol (MCP) Server & Multi-Agent Auto-Installer.
Implements RFC 002 with zero external third-party protocol dependencies (100% Python stdlib).

Key Capabilities & Red-Team Safeguards:
1. Strict stdout Isolation:
   All internal RightSub tool invocations run inside an isolated stdout/stderr capture context
   so `print()` statements from underlying scripts never corrupt the JSON-RPC 2.0 stdio wire stream.
2. Dual-Mode JSON-RPC Framing:
   Supports both standard MCP newline-delimited JSON (`\n`, protocolVersion 2024-11-05 / 2025-03-26)
   and LSP-style `Content-Length: N\r\n\r\n` framing. Strictly ignores response generation for
   JSON-RPC notifications (messages without `"id"`, e.g. `notifications/initialized`).
3. GUI Host PATH Augmentation:
   Automatically augments `os.environ["PATH"]` with `/opt/homebrew/bin`, `/usr/local/bin`,
   `~/.local/bin`, and Windows WinGet paths so GUI apps (Claude Desktop, Antigravity, Cursor,
   Windsurf) always locate `ffmpeg`, `ffprobe`, and `quicksubs`.
4. Multi-Agent Auto-Installer (`rightsub mcp --install`):
   Detects and safely registers `rightsub` in Antigravity, Claude Desktop, Cursor, Windsurf,
   and Claude Code CLI (creating `.bak` backups and preserving all existing MCP servers).
"""

import os
import io
import re
import sys
import json
import shutil
import argparse
import contextlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
for _p in (str(SCRIPT_DIR), str(REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from rightsub import __version__ as SERVER_VERSION
except Exception:
    SERVER_VERSION = "1.5.0"

# Augment PATH for GUI MCP hosts (Claude Desktop, Cursor, Antigravity, Windsurf)
def _augment_environment_path() -> str:
    current_path = os.environ.get("PATH", "")
    path_parts = [p for p in current_path.split(os.pathsep) if p]
    extra_dirs = []
    if sys.platform == "win32":
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            extra_dirs.append(str(Path(local_app) / "Microsoft" / "WinGet" / "Links"))
        extra_dirs.append(str(REPO_ROOT))
    else:
        extra_dirs.extend([
            "/opt/homebrew/bin",
            "/opt/homebrew/sbin",
            "/usr/local/bin",
            str(Path.home() / ".local" / "bin"),
            str(REPO_ROOT),
        ])
    for d in extra_dirs:
        if d and d not in path_parts and Path(d).is_dir():
            path_parts.insert(0, d)
    new_path = os.pathsep.join(path_parts)
    os.environ["PATH"] = new_path
    return new_path

_augment_environment_path()


# ==============================================================================
# MCP Tool Definitions (JSON Schema)
# ==============================================================================

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "inspect_media",
        "description": (
            "Inspect a video file (.mkv/.mp4), subtitle file (.srt), or media directory. "
            "Reports existing external Hebrew/English subtitles, character encoding (UTF-8 vs Windows-1255), "
            "BiDi visual-flip polarity, embedded subtitle streams via ffprobe, and recommended action."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to a video file, subtitle file, or directory."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "fix_plex_subtitles",
        "description": (
            "Run RightSub's 0-token deterministic 3-Stage Canonical BiDi & Un-Flipping Engine (SubRefine) "
            "on a Hebrew subtitle file or directory. Fixes 18 legacy visual-flipping patterns, wraps lines "
            "with UAX #9 Rule N1 RLM (\\u200F), converts Windows-1255 to UTF-8, repairs homoglyphs, and strips ads. "
            "By default uses Seed-Safe torrent protection (writes <stem>.he.srt and leaves plain .srt untouched)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to a subtitle file (.srt) or directory."
                },
                "replace_original": {
                    "type": "boolean",
                    "description": "If true, modifies plain .srt in-place instead of creating a Seed-Safe .he.srt copy.",
                    "default": False
                },
                "clean_ads": {
                    "type": "boolean",
                    "description": "Strip translator credits and promotional banners.",
                    "default": True
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "extract_subtitles",
        "description": "Discover and extract embedded subtitle streams from a video file (.mkv/.mp4/.m4v/.avi) via FFmpeg.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Absolute path to the video file or directory."
                },
                "lang": {
                    "type": "string",
                    "description": "Preferred ISO 639-2 language code to extract (e.g. 'eng', 'heb').",
                    "default": "eng"
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional explicit output .srt path."
                }
            },
            "required": ["video_path"]
        }
    },
    {
        "name": "prepare_translation",
        "description": (
            "Prepare an English master subtitle (.en.srt) for AI translation: builds a Translation Bible "
            "(character roster, grammatical genders, locked glossary, optional TMDb enrichment) and splits "
            "the subtitle into ~210-cue JSON batches."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "srt_path": {
                    "type": "string",
                    "description": "Absolute path to the source English .srt file."
                },
                "title": {
                    "type": "string",
                    "description": "Optional movie or TV show title for TMDb lookup."
                },
                "enrich_tmdb": {
                    "type": "boolean",
                    "description": "Query TMDb for verified character genders and plot overview if TMDB_API_KEY is configured.",
                    "default": True
                },
                "batch_size": {
                    "type": "integer",
                    "description": "Number of subtitle cues per JSON batch (default: 210).",
                    "default": 210
                }
            },
            "required": ["srt_path"]
        }
    },
    {
        "name": "merge_and_master",
        "description": (
            "Merge translated Hebrew JSON batches back against the master English .srt, enforcing 1:1 cue index "
            "parity, 25-cue window Cue Drift anchor validation, homoglyph normalization, and UAX #9 Rule N1 RLM wrapping."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "en_srt_path": {
                    "type": "string",
                    "description": "Absolute path to the master English .srt file."
                },
                "translated_batches_dir": {
                    "type": "string",
                    "description": "Directory containing translated batch JSON files."
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for the mastered .he.srt file."
                }
            },
            "required": ["en_srt_path", "translated_batches_dir", "output_path"]
        }
    },
    {
        "name": "polish_subtitles",
        "description": (
            "Run RightSub's Polish & QC Engine on an existing Hebrew subtitle. By default runs the 0-token "
            "deterministic canon, Georgian/Cyrillic homoglyph repair, and bilingual number un-flipping pass "
            "(fixing reversed 2-digit Subabi numbers like 84 -> 48 against the companion .en.srt) with Seed-Safe "
            ".he.srt output."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_path": {
                    "type": "string",
                    "description": "Path to the Hebrew subtitle (.srt / .he.srt) or video file."
                },
                "en_path": {
                    "type": "string",
                    "description": "Optional path to companion English master subtitle (.en.srt)."
                },
                "offline_canon_only": {
                    "type": "boolean",
                    "description": "Run only the 0-token deterministic pass without external LLM calls.",
                    "default": True
                },
                "in_place": {
                    "type": "boolean",
                    "description": "Save mastered file as <stem>.he.srt (preserving plain .srt untouched for torrent seeding).",
                    "default": True
                }
            },
            "required": ["target_path"]
        }
    },
    {
        "name": "audit_subtitles_qa",
        "description": (
            "Run RightSub's comprehensive Red Team Quality Assurance auditor comparing Hebrew and English SRTs "
            "(line count parity, timestamp drift, 25-cue window Cue Drift, RLM balance, homoglyphs, and "
            "bidirectional leading/trailing vocative & morphological gender mismatches)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "en_srt_path": {
                    "type": "string",
                    "description": "Path to master English .srt (or directory to audit)."
                },
                "he_srt_path": {
                    "type": "string",
                    "description": "Optional path to Hebrew .he.srt file."
                },
                "strict_gender": {
                    "type": "boolean",
                    "description": "Flag vocative and morphological gender mismatches.",
                    "default": True
                }
            },
            "required": ["en_srt_path"]
        }
    },
    {
        "name": "transcribe_audio",
        "description": "Run on-device speech-to-subtitle transcription on a media file via quicksubs (Apple SpeechAnalyzer / Whisper).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to video or audio file."
                },
                "engine": {
                    "type": "string",
                    "description": "Transcription engine ('apple', 'whisper', or 'parakeet').",
                    "default": "apple" if sys.platform == "darwin" else "whisper"
                }
            },
            "required": ["video_path"]
        }
    }
]


# ==============================================================================
# Tool Execution Engine (with Strict stdout Red-Team Isolation)
# ==============================================================================

@contextlib.contextmanager
def _isolated_stdio():
    """
    Captures all Python stdout and stderr writes into a StringIO buffer so that
    underlying RightSub functions cannot leak raw print() output onto the MCP
    stdio JSON-RPC wire channel.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        yield buf


def _exec_inspect_media(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m07 = importlib.import_module("07_fix_plex_punctuation")
    m01 = importlib.import_module("01_extract_subtitles")

    target = Path(arguments["path"]).expanduser().resolve()
    if not target.exists():
        return {"error": f"Path does not exist: {target}"}

    report: Dict[str, Any] = {
        "path": str(target),
        "type": "directory" if target.is_dir() else "file",
        "hebrew_subtitles": [],
        "english_subtitles": [],
        "videos": [],
        "recommended_action": ""
    }

    with _isolated_stdio() as log_buf:
        srt_files = sorted(target.rglob("*.srt")) if target.is_dir() else ([target] if target.suffix.lower() == ".srt" else sorted(target.parent.glob(f"{target.stem}*.srt")))
        vid_exts = {".mkv", ".mp4", ".m4v", ".avi", ".mov"}
        videos = sorted([p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in vid_exts]) if target.is_dir() else ([target] if target.suffix.lower() in vid_exts else [])

        for srt in srt_files:
            if ".bak" in srt.name.lower() or ".original." in srt.name.lower():
                continue
            try:
                content, enc = m07.read_file_with_encoding(srt)
                is_he = m07.detect_hebrew(content)
                if is_he:
                    polarity = m07.detect_file_flip_polarity(content)
                    has_rlm = "\u200f" in content
                    is_seed_safe_named = srt.name.lower().endswith(".he.srt")
                    report["hebrew_subtitles"].append({
                        "file": str(srt),
                        "encoding": enc,
                        "flip_polarity": polarity,
                        "has_rlm": has_rlm,
                        "is_he_srt_named": is_seed_safe_named,
                        "needs_fix_plex": (not has_rlm) or (enc.lower() != "utf-8") or (polarity == "VISUAL_FLIPPED") or (not is_seed_safe_named)
                    })
                else:
                    report["english_subtitles"].append({
                        "file": str(srt),
                        "encoding": enc
                    })
            except Exception as e:
                report["hebrew_subtitles"].append({"file": str(srt), "error": str(e)})

        for vid in videos[:20]:
            tracks = []
            try:
                if hasattr(m01, "probe_subtitle_streams"):
                    tracks = m01.probe_subtitle_streams(str(vid))
            except Exception:
                tracks = []
            report["videos"].append({
                "file": str(vid),
                "embedded_subtitle_streams": tracks
            })

    if report["hebrew_subtitles"]:
        needs_fix = [h for h in report["hebrew_subtitles"] if h.get("needs_fix_plex")]
        if needs_fix:
            report["recommended_action"] = "Run `fix_plex_subtitles` (0 AI tokens) to apply 3-Stage Canonical BiDi/RLM, UTF-8 conversion, and Seed-Safe .he.srt naming."
        else:
            report["recommended_action"] = "Hebrew subtitles are already UTF-8 and UAX #9 RLM compliant. Optionally run `audit_subtitles_qa`."
    elif report["english_subtitles"]:
        report["recommended_action"] = "No Hebrew subtitle found, but English .srt exists. Run `prepare_translation` to split into batches and translate."
    elif report["videos"]:
        report["recommended_action"] = "No external subtitles found. Run `extract_subtitles` to extract embedded tracks, or `transcribe_audio` if none exist."
    else:
        report["recommended_action"] = "No media or subtitle files detected at the given path."

    logs = log_buf.getvalue().strip()
    if logs:
        report["logs"] = logs
    return report


def _exec_fix_plex_subtitles(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m07 = importlib.import_module("07_fix_plex_punctuation")
    m18 = importlib.import_module("18_auto_pipeline")

    target = Path(arguments["path"]).expanduser().resolve()
    replace_original = bool(arguments.get("replace_original", False))
    clean_ads = bool(arguments.get("clean_ads", True))

    if not target.exists():
        return {"error": f"Path does not exist: {target}"}

    processed_files = []
    with _isolated_stdio() as log_buf:
        if target.is_file() and target.suffix.lower() == ".srt":
            args = argparse.Namespace(
                replace_original=replace_original,
                no_clean_ads=not clean_ads,
                no_backup=False,
                dry_run=False
            )
            ok = m18.handle_single_srt(target, args)
            processed_files.append({"file": str(target), "success": bool(ok)})
        elif target.is_dir():
            for srt in sorted(target.rglob("*.srt")):
                if ".bak" in srt.name.lower() or ".original." in srt.name.lower():
                    continue
                if m18.is_hebrew_file(srt):
                    args = argparse.Namespace(
                        replace_original=replace_original,
                        no_clean_ads=not clean_ads,
                        no_backup=False,
                        dry_run=False
                    )
                    ok = m18.handle_single_srt(srt, args)
                    processed_files.append({"file": str(srt), "success": bool(ok)})
        else:
            return {"error": f"Unsupported target for fix_plex_subtitles: {target}"}

    return {
        "status": "ok",
        "processed_count": len(processed_files),
        "processed_files": processed_files,
        "seed_safe_mode": not replace_original,
        "logs": log_buf.getvalue().strip()
    }


def _exec_extract_subtitles(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m01 = importlib.import_module("01_extract_subtitles")

    video_path = Path(arguments["video_path"]).expanduser().resolve()
    lang = arguments.get("lang", "eng")
    output_path = arguments.get("output_path")

    if not video_path.exists():
        return {"error": f"Video path does not exist: {video_path}"}

    with _isolated_stdio() as log_buf:
        out_srt = m01.extract_subtitle(
            str(video_path),
            output_srt=str(Path(output_path).expanduser().resolve()) if output_path else None,
            preferred_lang=lang
        )

    return {
        "status": "ok" if out_srt else "not_found",
        "extracted_srt": str(out_srt) if out_srt else None,
        "logs": log_buf.getvalue().strip()
    }


def _exec_prepare_translation(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m03 = importlib.import_module("03_generate_bible")
    m04 = importlib.import_module("04_split_batches")

    srt_path = Path(arguments["srt_path"]).expanduser().resolve()
    if not srt_path.is_file():
        return {"error": f"English SRT file not found: {srt_path}"}

    title = arguments.get("title") or srt_path.stem.replace(".en", "")
    enrich_tmdb = bool(arguments.get("enrich_tmdb", True))
    batch_size = int(arguments.get("batch_size", 210))

    work_dir = srt_path.parent / f"{srt_path.stem.replace('.en', '')}_rightsub_work"
    batches_dir = work_dir / "batches"
    bible_path = work_dir / "translation_bible.json"
    work_dir.mkdir(parents=True, exist_ok=True)

    with _isolated_stdio() as log_buf:
        bible_data = m03.generate_bible_skeleton([str(srt_path)], title=title, use_tmdb=enrich_tmdb)
        bible_path.write_text(json.dumps(bible_data, indent=2, ensure_ascii=False), encoding="utf-8")
        m04.split_srt_to_batches(str(srt_path), str(batches_dir), batch_size=batch_size)

    batch_files = sorted(str(p) for p in batches_dir.glob("batch_*_input.json"))
    return {
        "status": "ok",
        "work_dir": str(work_dir),
        "bible_path": str(bible_path),
        "batches_dir": str(batches_dir),
        "batch_files": batch_files,
        "batch_count": len(batch_files),
        "logs": log_buf.getvalue().strip()
    }


def _exec_merge_and_master(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m05 = importlib.import_module("05_merge_and_validate")

    en_srt_path = Path(arguments["en_srt_path"]).expanduser().resolve()
    batches_dir = Path(arguments["translated_batches_dir"]).expanduser().resolve()
    output_path = Path(arguments["output_path"]).expanduser().resolve()

    if not en_srt_path.is_file():
        return {"error": f"Master English SRT not found: {en_srt_path}"}
    if not batches_dir.is_dir():
        return {"error": f"Translated batches directory not found: {batches_dir}"}

    with _isolated_stdio() as log_buf:
        ok = m05.merge_batches_to_srt(str(en_srt_path), str(batches_dir), str(output_path))

    return {
        "status": "ok" if ok else "failed",
        "output_path": str(output_path),
        "exists": output_path.is_file(),
        "logs": log_buf.getvalue().strip()
    }


def _exec_polish_subtitles(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m19 = importlib.import_module("19_polish_and_qc")

    target_path = Path(arguments["target_path"]).expanduser().resolve()
    en_path = arguments.get("en_path")
    offline_canon_only = bool(arguments.get("offline_canon_only", True))
    in_place = bool(arguments.get("in_place", True))

    if not target_path.exists():
        return {"error": f"Target path not found: {target_path}"}

    args = argparse.Namespace(
        target=str(target_path),
        en_path=str(Path(en_path).expanduser().resolve()) if en_path else None,
        tmdb_id=None,
        title=None,
        bible=None,
        ollama=False,
        gemini=not offline_canon_only,
        model=None,
        api_key=None,
        batch_size=60,
        offline_canon_only=offline_canon_only,
        diff_only=False,
        dry_run=False,
        in_place=in_place,
        interactive=False,
        output=None,
        diff_report=None
    )

    with _isolated_stdio() as log_buf:
        ok = m19.polish_target(str(target_path), args.en_path, args)

    return {
        "status": "ok" if ok else "failed",
        "target_path": str(target_path),
        "offline_canon_only": offline_canon_only,
        "logs": log_buf.getvalue().strip()
    }


def _exec_audit_subtitles_qa(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m08 = importlib.import_module("08_quality_assurance")

    en_srt_path = Path(arguments["en_srt_path"]).expanduser().resolve()
    he_srt_path = arguments.get("he_srt_path")
    strict_gender = bool(arguments.get("strict_gender", True))

    if not en_srt_path.exists():
        return {"error": f"Path not found: {en_srt_path}"}

    with _isolated_stdio() as log_buf:
        if en_srt_path.is_dir():
            passed = m08.audit_directory(str(en_srt_path), strict_gender=strict_gender)
        else:
            if not he_srt_path:
                stem = en_srt_path.stem
                base = stem[:-3] if stem.lower().endswith(".en") else stem
                cand = en_srt_path.parent / f"{base}.he.srt"
                he_srt_path = str(cand)
            passed = m08.run_qa_audit(str(en_srt_path), str(Path(he_srt_path).expanduser().resolve()), strict_gender=strict_gender)

    return {
        "status": "passed" if passed else "issues_found",
        "passed": bool(passed),
        "logs": log_buf.getvalue().strip()
    }


def _exec_transcribe_audio(arguments: Dict[str, Any]) -> Dict[str, Any]:
    import importlib
    m00 = importlib.import_module("00_transcribe_audio")

    video_path = Path(arguments["video_path"]).expanduser().resolve()
    engine = arguments.get("engine") or ("apple" if sys.platform == "darwin" else "whisper")
    if not video_path.exists():
        return {"error": f"Media file not found: {video_path}"}

    with _isolated_stdio() as log_buf:
        ok = m00.transcribe_media(str(video_path), engine=engine)

    return {
        "status": "ok" if ok else "failed",
        "video_path": str(video_path),
        "engine": engine,
        "logs": log_buf.getvalue().strip()
    }


TOOL_HANDLERS = {
    "inspect_media": _exec_inspect_media,
    "fix_plex_subtitles": _exec_fix_plex_subtitles,
    "extract_subtitles": _exec_extract_subtitles,
    "prepare_translation": _exec_prepare_translation,
    "merge_and_master": _exec_merge_and_master,
    "polish_subtitles": _exec_polish_subtitles,
    "audit_subtitles_qa": _exec_audit_subtitles_qa,
    "transcribe_audio": _exec_transcribe_audio,
}


# ==============================================================================
# JSON-RPC 2.0 Request Dispatcher & Dual-Mode Framing Loop
# ==============================================================================

def handle_jsonrpc_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Processes a single JSON-RPC 2.0 message dictionary.
    Returns a response dict for Requests (`"id" in msg`), or `None` for Notifications.
    """
    if not isinstance(msg, dict):
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request"}
        }

    method = msg.get("method", "")
    has_id = "id" in msg
    req_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications (no "id" field) MUST NOT receive a response frame
    if not has_id:
        return None

    if method == "initialize":
        client_proto = params.get("protocolVersion", "2024-11-05")
        supported_proto = client_proto if client_proto in ("2024-11-05", "2025-03-26") else "2024-11-05"
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": supported_proto,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"listChanged": False},
                    "prompts": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "rightsub",
                    "version": SERVER_VERSION
                }
            }
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": MCP_TOOLS}
        }

    if method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"resources": []}
        }

    if method == "prompts/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"prompts": []}
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            }
        try:
            res_data = handler(arguments)
            is_error = "error" in res_data and len(res_data) == 1
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res_data, indent=2, ensure_ascii=False)
                        }
                    ],
                    "isError": bool(is_error)
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"error": str(e)}, ensure_ascii=False)
                        }
                    ],
                    "isError": True
                }
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    }


def serve_stdio(in_stream=None, out_stream=None) -> int:
    """
    Runs the MCP JSON-RPC 2.0 loop over binary/text stdio streams.
    Supports both newline-delimited JSON and Content-Length headers.
    """
    raw_in = in_stream if in_stream is not None else sys.stdin.buffer
    raw_out = out_stream if out_stream is not None else sys.stdout.buffer

    while True:
        line = raw_in.readline()
        if not line:
            break

        stripped = line.strip()
        if not stripped:
            continue

        # Mode A: LSP-style Content-Length framing
        if stripped.lower().startswith(b"content-length:"):
            try:
                length = int(stripped.split(b":", 1)[1].strip())
            except ValueError:
                continue
            # Consume remaining headers until blank line
            while True:
                hdr = raw_in.readline()
                if not hdr or hdr in (b"\r\n", b"\n"):
                    break
            body = raw_in.read(length)
            if not body:
                break
            try:
                msg = json.loads(body.decode("utf-8"))
            except Exception:
                resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
                payload = json.dumps(resp, ensure_ascii=False).encode("utf-8")
                raw_out.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
                raw_out.flush()
                continue

            resp = handle_jsonrpc_message(msg)
            if resp is not None:
                payload = json.dumps(resp, ensure_ascii=False).encode("utf-8")
                raw_out.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
                raw_out.flush()
        else:
            # Mode B: Standard MCP Newline-Delimited JSON
            try:
                msg = json.loads(stripped.decode("utf-8"))
            except Exception:
                resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
                raw_out.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                raw_out.flush()
                continue

            resp = handle_jsonrpc_message(msg)
            if resp is not None:
                raw_out.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                raw_out.flush()

    return 0


# ==============================================================================
# Multi-Agent Auto-Installer (`rightsub mcp --install` / `--uninstall` / `--status`)
# ==============================================================================

def get_known_agent_config_paths(home_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Returns canonical MCP configuration file paths for major AI agents across macOS, Windows, and Linux."""
    home = home_dir or Path.home()
    paths: Dict[str, Path] = {
        "antigravity": home / ".gemini" / "antigravity" / "mcp_config.json",
        "cursor": home / ".cursor" / "mcp.json",
        "windsurf": home / ".codeium" / "windsurf" / "mcp_config.json",
        "claude-code": home / ".claude.json",
    }
    if sys.platform == "darwin":
        paths["claude"] = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else (home / "AppData" / "Roaming")
        paths["claude"] = base / "Claude" / "claude_desktop_config.json"
    else:
        paths["claude"] = home / ".config" / "Claude" / "claude_desktop_config.json"

    return paths


def build_mcp_server_entry() -> Dict[str, Any]:
    """
    Constructs a self-contained MCP server definition using exact absolute paths
    for the Python interpreter and `rightsub.py`, plus full PATH and optional API keys.
    """
    rightsub_py = str((REPO_ROOT / "rightsub.py").resolve())
    python_exe = str(Path(sys.executable).resolve())
    env_dict: Dict[str, str] = {
        "PATH": _augment_environment_path(),
        "PYTHONIOENCODING": "utf-8",
    }

    # Include saved TMDb key if present in ~/.config/rightsub/config.json
    cfg_file = Path.home() / ".config" / "rightsub" / "config.json"
    if cfg_file.is_file():
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
            if cfg.get("tmdb_api_key"):
                env_dict["TMDB_API_KEY"] = cfg["tmdb_api_key"]
            if cfg.get("gemini_api_key"):
                env_dict["GEMINI_API_KEY"] = cfg["gemini_api_key"]
        except Exception:
            pass

    return {
        "command": python_exe,
        "args": [rightsub_py, "mcp"],
        "env": env_dict
    }


def update_agent_config_file(config_path: Path, remove: bool = False) -> Tuple[bool, str]:
    """
    Atomically installs or removes the `rightsub` MCP server entry in `config_path`.
    Creates a `.bak` backup before modifying existing files and refuses to overwrite corrupt JSON.
    """
    config_path = Path(config_path)
    data: Dict[str, Any] = {}

    if config_path.is_file():
        raw_text = config_path.read_text(encoding="utf-8").strip()
        if raw_text:
            try:
                loaded = json.loads(raw_text)
                if not isinstance(loaded, dict):
                    return False, f"Skipped {config_path}: Root JSON element is not an object."
                data = loaded
            except Exception as e:
                return False, f"Refused to modify {config_path}: Existing JSON is malformed ({e})."
        # Create backup before modifying
        bak_path = config_path.with_suffix(config_path.suffix + ".bak")
        shutil.copy2(config_path, bak_path)
    else:
        if remove:
            return True, f"Not present in {config_path} (file does not exist)."
        config_path.parent.mkdir(parents=True, exist_ok=True)

    mcp_servers = data.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        mcp_servers = {}
        data["mcpServers"] = mcp_servers

    if remove:
        if "rightsub" in mcp_servers:
            del mcp_servers["rightsub"]
            config_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return True, f"Removed 'rightsub' from {config_path}"
        return True, f"'rightsub' was not registered in {config_path}"

    mcp_servers["rightsub"] = build_mcp_server_entry()
    tmp_path = config_path.with_suffix(config_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_path.replace(config_path)
    return True, f"Installed 'rightsub' MCP server in {config_path}"


def install_mcp_for_agents(
    target_agent: str = "all",
    custom_config_path: Optional[str] = None,
    home_dir: Optional[Path] = None,
    remove: bool = False
) -> Dict[str, Any]:
    """
    Installs (or uninstalls) RightSub MCP server across detected or specified AI agents.
    """
    results = []
    if custom_config_path:
        ok, msg = update_agent_config_file(Path(custom_config_path).expanduser().resolve(), remove=remove)
        results.append({"agent": "custom", "path": custom_config_path, "success": ok, "message": msg})
        return {"results": results, "entry": build_mcp_server_entry()}

    known = get_known_agent_config_paths(home_dir=home_dir)
    if target_agent and target_agent != "all":
        if target_agent not in known:
            return {"error": f"Unknown agent '{target_agent}'. Choose from: {', '.join(known.keys())} or 'all'."}
        agents_to_process = {target_agent: known[target_agent]}
    else:
        # For 'all', install into agents whose parent directory or config file exists,
        # and always include Antigravity and Claude/Cursor if their base config folder exists.
        agents_to_process = {}
        for name, cfg_path in known.items():
            if cfg_path.exists() or cfg_path.parent.exists():
                agents_to_process[name] = cfg_path
        # If no agent folders exist yet on a fresh machine, default to Antigravity + Cursor
        if not agents_to_process and not remove:
            agents_to_process["antigravity"] = known["antigravity"]

    for name, cfg_path in agents_to_process.items():
        ok, msg = update_agent_config_file(cfg_path, remove=remove)
        results.append({
            "agent": name,
            "path": str(cfg_path),
            "success": ok,
            "message": msg
        })

    return {"results": results, "entry": build_mcp_server_entry()}


def get_mcp_registration_status(home_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Checks which AI agents currently have `rightsub` registered in their `mcpServers` block."""
    known = get_known_agent_config_paths(home_dir=home_dir)
    statuses = []
    for name, cfg_path in known.items():
        registered = False
        exists = cfg_path.is_file()
        if exists:
            try:
                data = json.loads(cfg_path.read_text(encoding="utf-8"))
                registered = isinstance(data.get("mcpServers"), dict) and ("rightsub" in data["mcpServers"])
            except Exception:
                registered = False
        statuses.append({
            "agent": name,
            "path": str(cfg_path),
            "config_exists": exists,
            "registered": registered
        })
    return statuses


def main():
    parser = argparse.ArgumentParser(
        prog="rightsub mcp",
        description="RightSub Native Model Context Protocol (MCP) Server & Multi-Agent Installer"
    )
    parser.add_argument("--install", action="store_true", help="Auto-register RightSub MCP server in AI agents (Antigravity, Claude Desktop, Cursor, Windsurf, Claude Code)")
    parser.add_argument("--uninstall", action="store_true", help="Remove RightSub MCP server from AI agent configurations")
    parser.add_argument("--agent", default="all", help="Target agent for --install/--uninstall: all, antigravity, claude, cursor, windsurf, claude-code (default: all)")
    parser.add_argument("--config-path", help="Custom path to an agent's MCP JSON configuration file")
    parser.add_argument("--status", action="store_true", help="Show MCP registration status across all known AI agents")
    parser.add_argument("--print-config", action="store_true", help="Print the ready-to-paste mcpServers JSON snippet for any custom agent")

    args = parser.parse_args()

    if args.print_config:
        snippet = {"mcpServers": {"rightsub": build_mcp_server_entry()}}
        print(json.dumps(snippet, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.status:
        print("\n========================================================")
        print("          RightSub MCP Agent Registration Status        ")
        print("========================================================")
        for st in get_mcp_registration_status():
            mark = "[✓] Registered" if st["registered"] else ("[i] Not registered" if st["config_exists"] else "[ ] Agent not installed")
            print(f" {st['agent']:<14} : {mark} ({st['path']})")
        print("========================================================\n")
        sys.exit(0)

    if args.install or args.uninstall:
        res = install_mcp_for_agents(
            target_agent=args.agent,
            custom_config_path=args.config_path,
            remove=args.uninstall
        )
        if "error" in res:
            print(f"[-] {res['error']}")
            sys.exit(1)

        action_title = "Uninstallation" if args.uninstall else "Installation"
        print(f"\n========================================================")
        print(f"          RightSub MCP Server {action_title}             ")
        print(f"========================================================")
        for item in res.get("results", []):
            icon = "[✓]" if item["success"] else "[✗]"
            print(f" {icon} [{item['agent']}] {item['message']}")
        if not args.uninstall:
            print("\n [i] Universal JSON snippet for any other MCP client:")
            snippet = {"mcpServers": {"rightsub": res["entry"]}}
            print(json.dumps(snippet, indent=2, ensure_ascii=False))
        print("========================================================\n")
        sys.exit(0)

    # Default mode: start JSON-RPC 2.0 MCP server over stdio
    sys.exit(serve_stdio())


if __name__ == "__main__":
    main()
