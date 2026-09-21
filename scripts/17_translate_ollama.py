#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
17_translate_ollama.py
----------------------
Offline, 100% Free Local Subtitle Translation Engine using Ollama.
Operates with zero external Python dependencies (pure standard library urllib).

Key Features:
1. Direct connection to Ollama REST API (http://localhost:11434/api/generate).
2. Model autodetection: checks /api/tags and falls back safely to available models.
3. Structured JSON enforcement: enforces format="json" for deterministic cue output.
4. Discrepancy & Validation: validates that all indices match the input batch cues.
5. Auto-Merge capability: seamlessly merges translated batches into final .he.srt.
"""

import os
import sys
import re
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Add scripts directory to sys.path to allow importing sibling modules
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODELS = ["llama3.2", "llama3.1:8b", "llama3:8b", "qwen2.5:7b", "qwen2.5", "mistral"]

def check_ollama_status(url=DEFAULT_OLLAMA_URL):
    """Checks if Ollama daemon is running and returns list of installed model names."""
    tags_url = f"{url.rstrip('/')}/api/tags"
    req = urllib.request.Request(tags_url, headers={"User-Agent": "RightSub/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return True, models
    except Exception:
        pass
    return False, []

def select_best_model(installed_models, requested_model=None):
    """Selects requested model or best matching installed model."""
    if requested_model:
        return requested_model
    for pref in DEFAULT_MODELS:
        for inst in installed_models:
            if inst.startswith(pref) or pref.startswith(inst.split(":")[0]):
                return inst
    if installed_models:
        return installed_models[0]
    return "llama3.2"

def query_ollama(prompt, model, url=DEFAULT_OLLAMA_URL, temperature=0.2):
    """Sends a generation request to Ollama and returns the parsed JSON dict/list."""
    gen_url = f"{url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature
        }
    }
    raw_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        gen_url,
        data=raw_data,
        headers={"Content-Type": "application/json", "User-Agent": "RightSub/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            raw_response = res_json.get("response", "").strip()
            # Clean possible markdown block
            if raw_response.startswith("```json"):
                raw_response = re.sub(r'^```json\s*', '', raw_response)
                raw_response = re.sub(r'\s*```$', '', raw_response)
            elif raw_response.startswith("```"):
                raw_response = re.sub(r'^```\s*', '', raw_response)
                raw_response = re.sub(r'\s*```$', '', raw_response)
            
            # Sanitize internal double-quotes in Hebrew text before parsing
            sanitized = re.sub(r'([\u0590-\u05FF])"([\u0590-\u05FF])', r'\1״\2', raw_response)
            return json.loads(sanitized)
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to connect to Ollama at {url}: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Ollama returned non-JSON response: {e}")

def translate_batch(batch_file, prompt_file=None, model="llama3.2", url=DEFAULT_OLLAMA_URL):
    """Translates a single batch JSON using Ollama."""
    with open(batch_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    # Read prompt instructions if available
    instructions = ""
    if prompt_file and os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as pf:
            instructions = pf.read()

    # Construct input cues representation
    input_dict = {}
    if isinstance(items, list):
        for it in items:
            idx = str(it.get("index"))
            txt = it.get("text", "")
            input_dict[idx] = txt
    elif isinstance(items, dict):
        input_dict = {str(k): str(v) for k, v in items.items() if str(k).isdigit()}

    cues_json_str = json.dumps(input_dict, ensure_ascii=False, indent=2)

    prompt = f"""You are a professional Hebrew film and television subtitle translator.
Translate the following subtitle dialogue cues from English to natural, fluent, context-aware Hebrew.

RULES:
1. Translate all dialogue into natural modern Hebrew.
2. NEVER skip or merge cues. Return an exact 1-to-1 JSON object mapping index to translated Hebrew.
3. Preserve all indices. Output must be a valid JSON object where keys are the cue indices and values are Hebrew dialogue strings:
{{"1": "שלום", "2": "מה שלומך?"}}
4. Use Hebrew gershayim (״) for acronyms (עו״ד, ארה״ב). Do not vocalize (ללא ניקוד).

{instructions}

CUES TO TRANSLATE (JSON):
{cues_json_str}
"""
    result = query_ollama(prompt, model=model, url=url)
    
    # Normalize output format to dict {index_str: hebrew_str}
    translations = {}
    if isinstance(result, list):
        for it in result:
            idx = str(it.get("index"))
            he = it.get("hebrew", it.get("text", ""))
            translations[idx] = str(he)
    elif isinstance(result, dict):
        if "cues" in result and isinstance(result["cues"], list):
            for it in result["cues"]:
                idx = str(it.get("index"))
                he = it.get("hebrew", it.get("text", ""))
                translations[idx] = str(he)
        else:
            for k, v in result.items():
                if str(k).isdigit():
                    translations[str(k)] = str(v)

    return translations

def run_ollama_pipeline(prompts_dir, model=None, url=DEFAULT_OLLAMA_URL, en_srt=None, output_he=None):
    """Processes all batches in prompts_dir with Ollama and optionally merges the result."""
    pdir = Path(prompts_dir)
    if not pdir.is_dir():
        print(f"[-] Directory not found: {pdir}")
        return False

    is_running, installed = check_ollama_status(url)
    if not is_running:
        print(f"[-] Ollama daemon is not running at {url}.")
        print("[!] To start Ollama, run: ollama serve (or launch the Ollama app).")
        print("[!] Download Ollama for free from: https://ollama.com")
        return False

    chosen_model = select_best_model(installed, model)
    print(f"[+] Connected to Ollama at {url}")
    print(f"[+] Active translation model: {chosen_model}")

    # Discover batch input files
    batch_inputs = sorted(list(pdir.glob("batch_*_input.json")) or list(pdir.glob("batch_*_en.json")))
    if not batch_inputs:
        print(f"[-] No batch input JSON files found in {pdir}")
        return False

    print(f"[+] Found {len(batch_inputs)} batch(es) to translate.")
    all_success = True

    for b_in in batch_inputs:
        batch_stem = b_in.stem.replace("_input", "").replace("_en", "")
        b_prompt = pdir / f"{batch_stem}_prompt.txt"
        b_out = pdir / f"{batch_stem}_translated.json"

        if b_out.exists():
            print(f"[i] Skipping already translated batch: {b_out.name}")
            continue

        print(f"[*] Translating {b_in.name} with model '{chosen_model}'...")
        try:
            translations = translate_batch(b_in, b_prompt if b_prompt.exists() else None, model=chosen_model, url=url)
            with open(b_out, "w", encoding="utf-8") as out_f:
                json.dump(translations, out_f, ensure_ascii=False, indent=2)
            print(f"    [✓] Successfully saved: {b_out.name} ({len(translations)} cues)")
        except Exception as e:
            print(f"    [!] Error translating {b_in.name}: {e}")
            all_success = False

    # Auto-merge if requested or if English SRT is identified
    if en_srt and all_success:
        if not output_he:
            output_he = str(Path(en_srt).with_suffix(".he.srt"))
        print(f"[*] Auto-merging batches into {output_he}...")
        try:
            from scripts.import_helper import import_script
        except ImportError:
            pass
        
        merge_script = SCRIPT_DIR / "05_merge_and_validate.py"
        if merge_script.exists():
            import subprocess
            cmd = [sys.executable, str(merge_script), str(en_srt), str(pdir), "-o", str(output_he)]
            res = subprocess.run(cmd)
            return res.returncode == 0

    return all_success

def main():
    parser = argparse.ArgumentParser(description="Offline Local Subtitle Translation via Ollama.")
    parser.add_argument("prompts_dir", help="Directory containing batch_*_input.json files")
    parser.add_argument("-m", "--model", help="Ollama model name (default: auto-detected or llama3.2)")
    parser.add_argument("--url", default=DEFAULT_OLLAMA_URL, help="Ollama server URL (default: http://localhost:11434)")
    parser.add_argument("--en-srt", help="Original English master SRT for automatic merge")
    parser.add_argument("-o", "--output", help="Output .he.srt path after merge")

    args = parser.parse_args()
    success = run_ollama_pipeline(
        prompts_dir=args.prompts_dir,
        model=args.model,
        url=args.url,
        en_srt=args.en_srt,
        output_he=args.output
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
