#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_transcribe_audio.py
-----------------------
On-Device Audio/Video Speech-to-Subtitle Engine using `quicksubs`.

Credit & Attribution:
- Powered by `quicksubs` CLI created by Matt Birchler.
- GitHub: https://github.com/mattbirchler/quicksubs
- Blog & Project Site: https://birchtree.me / https://quickstuff.app

Features:
- Transcribes media on-device on macOS with zero cloud latency and zero bandwidth cost.
- Supported speech engines:
  * apple    : Apple SpeechAnalyzer (native on macOS, on-device, zero download).
  * whisper  : OpenAI Whisper (highest accuracy, local ~626MB model).
  * parakeet : NVIDIA Parakeet (fastest local model ~400MB).
- Produces clean .srt subtitles and returns structured execution metrics.
- Can be imported as a library or executed directly from the command line.
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from pathlib import Path

VALID_ENGINES = ("apple", "whisper", "parakeet")

def is_quicksubs_available() -> bool:
    """Check if quicksubs CLI binary is available on system PATH."""
    return shutil.which("quicksubs") is not None

def transcribe_audio(
    input_media_path: str,
    output_dir: str = None,
    engine: str = "apple",
    format_type: str = "srt",
    gemini_cleanup: bool = False,
    api_key: str = None,
    model: str = None,
    quiet: bool = False
) -> dict:
    """
    Transcribe audio or video into subtitles using quicksubs.

    Returns:
        dict: {
            "success": bool,
            "output_file": str or None,
            "engine": str,
            "metrics": dict or None,
            "error": str or None
        }
    """
    input_path = Path(input_media_path).resolve()
    if not input_path.exists():
        return {
            "success": False,
            "output_file": None,
            "engine": engine,
            "metrics": None,
            "error": f"Input file not found: {input_media_path}"
        }

    if not is_quicksubs_available():
        err_msg = (
            "'quicksubs' is not installed or not in PATH.\n"
            "Install it via Homebrew on macOS:\n"
            "  brew install mattbirchler/tap/quicksubs\n"
            "Official repository: https://github.com/mattbirchler/quicksubs"
        )
        return {
            "success": False,
            "output_file": None,
            "engine": engine,
            "metrics": None,
            "error": err_msg
        }

    if engine not in VALID_ENGINES:
        return {
            "success": False,
            "output_file": None,
            "engine": engine,
            "metrics": None,
            "error": f"Invalid engine '{engine}'. Choose from: {VALID_ENGINES}"
        }

    cmd = ["quicksubs", str(input_path), "-f", format_type, "--engine", engine, "--json"]
    if quiet:
        cmd.append("-q")

    if output_dir:
        out_dir_path = Path(output_dir).resolve()
        out_dir_path.mkdir(parents=True, exist_ok=True)
        cmd.extend(["-o", str(out_dir_path)])
    else:
        out_dir_path = input_path.parent

    if gemini_cleanup:
        cmd.append("--clean-up")
        if api_key:
            cmd.extend(["--api-key", api_key])
        if model:
            cmd.extend(["--model", model])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        metrics = None
        output_files = []

        # Parse JSON output from stdout if available
        for line in stdout.splitlines():
            line_s = line.strip()
            if line_s.startswith("{") and line_s.endswith("}"):
                try:
                    data = json.loads(line_s)
                    metrics = data
                    output_files = data.get("outputs", [])
                    break
                except Exception:
                    pass

        # Fallback detection of expected output file
        expected_output = out_dir_path / f"{input_path.stem}.{format_type}"
        resolved_output = None
        if output_files and os.path.exists(output_files[0]):
            resolved_output = output_files[0]
        elif expected_output.exists():
            resolved_output = str(expected_output)

        if proc.returncode != 0 and not resolved_output:
            return {
                "success": False,
                "output_file": None,
                "engine": engine,
                "metrics": metrics,
                "error": f"quicksubs exited with code {proc.returncode}. Stderr: {stderr}"
            }

        return {
            "success": True,
            "output_file": resolved_output,
            "engine": engine,
            "metrics": metrics,
            "error": None
        }

    except Exception as exc:
        return {
            "success": False,
            "output_file": None,
            "engine": engine,
            "metrics": None,
            "error": str(exc)
        }

def main():
    parser = argparse.ArgumentParser(
        description="On-Device Speech-to-Subtitle Engine using quicksubs (by Matt Birchler)."
    )
    parser.add_argument("input", help="Path to video or audio file")
    parser.add_argument("-o", "--output-dir", help="Output directory for subtitles")
    parser.add_argument(
        "-e", "--engine",
        choices=VALID_ENGINES,
        default="apple",
        help="Speech engine: apple (on-device Apple SpeechAnalyzer), whisper (OpenAI), or parakeet (NVIDIA)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["srt", "vtt", "txt"],
        default="srt",
        help="Target subtitle/transcript format (default: srt)"
    )
    parser.add_argument("--clean-up", action="store_true", help="Perform Gemini AI cleanup pass on transcript")
    parser.add_argument("--api-key", help="Google Gemini API key for --clean-up pass")
    parser.add_argument("--model", help="Gemini model for --clean-up (e.g. gemini-2.5-flash)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")

    args = parser.parse_args()

    print(f"[+] quicksubs Speech-to-Subtitle Engine")
    print(f"    Attribution: quicksubs by Matt Birchler (https://github.com/mattbirchler/quicksubs)")
    print(f"    Input:       {args.input}")
    print(f"    Engine:      {args.engine}")
    print(f"    Format:      {args.format}")

    result = transcribe_audio(
        input_media_path=args.input,
        output_dir=args.output_dir,
        engine=args.engine,
        format_type=args.format,
        gemini_cleanup=args.clean_up,
        api_key=args.api_key,
        model=args.model,
        quiet=args.quiet
    )

    if result["success"]:
        print(f"[✓] Successfully transcribed: {result['output_file']}")
        if result.get("metrics"):
            m = result["metrics"]
            duration = m.get("audioDurationSeconds", 0)
            words = m.get("wordCount", 0)
            print(f"    Duration: {duration:.1f}s | Words: {words}")
        sys.exit(0)
    else:
        print(f"[-] Transcription failed:\n{result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
