#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_wiki.py
------------
Synchronizes the local bilingual wiki/ directory with the GitHub Wiki repository
(https://github.com/<owner>/<repo>.wiki.git).
"""

import os
import re
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WIKI_DIR = BASE_DIR / "wiki"
REPO_BLOB_BASE = "https://github.com/omerninyo/RightSub/blob/main"

# Canonical 1-to-1 mapping between repository Markdown sources and GitHub Wiki page slugs
DOCS_TO_WIKI_MAP = {
    "ROADMAP.md": "Roadmap",
    "ROADMAP.he.md": "מפת-דרכים",
    "docs/WHATS_NEW.md": "Whats-New",
    "docs/WHATS_NEW.he.md": "מה-חדש",
    "docs/QUICKSTART_FOR_BEGINNERS.md": "Quickstart-for-Beginners",
    "docs/QUICKSTART_FOR_BEGINNERS.he.md": "מדריך-פשוט-למתחילים",
    "docs/INSTALLATION_GUIDE.md": "Installation-Guide",
    "docs/INSTALLATION_GUIDE.he.md": "מדריך-התקנה-והפצה",
    "docs/INTEGRATIONS_GUIDE.md": "Integrations-Guide",
    "docs/INTEGRATIONS_GUIDE.he.md": "מדריך-אינטגרציות-ואוטומציה",
    "docs/AI_INTEGRATION_GUIDE.md": "AI-Integration-Guide",
    "docs/AI_INTEGRATION_GUIDE.he.md": "מדריך-חיבור-לכלי-בינה-מלאכותית",
    "docs/COMPARISON_BAZARR.md": "Bazarr-Comparison",
    "docs/COMPARISON_BAZARR.he.md": "השוואה-מול-Bazarr",
    "docs/FEATURE_AI_POLISH_AND_QC.md": "Semantic-AI-Polish-and-QC",
    "docs/FEATURE_AI_POLISH_AND_QC.he.md": "מפרט-מנוע-ליטוש-סמנטי-ובקרת-איכות",
    "docs/BIDI_AND_PLEX_GUIDE.md": "BiDi-and-Plex-Guide",
    "docs/BIDI_AND_PLEX_GUIDE.he.md": "מדריך-BiDi-ופלקס",
    "docs/CASE_STUDY_BOSTON_LEGAL.md": "Boston-Legal-Case-Study",
    "docs/CASE_STUDY_BOSTON_LEGAL.he.md": "מקרה-בוחן-בוסטון-ליגל",
    "docs/PIPELINE_WORKFLOW.md": "Pipeline-Workflow",
    "docs/PIPELINE_WORKFLOW.he.md": "תהליך-עבודה",
    "docs/QUICKSUBS_INTEGRATION.md": "Quicksubs-Integration",
    "docs/QUICKSUBS_INTEGRATION.he.md": "תמלול-וסנכרון-מקומי-quicksubs",
    "docs/TMDB_INTEGRATION.md": "TMDb-Integration",
    "docs/TMDB_INTEGRATION.he.md": "אינטגרציית-TMDb",
    "docs/proposals/RFC_001_INTERACTIVE_TUI.md": "Interactive-CLI-Specification",
    "docs/proposals/RFC_001_INTERACTIVE_TUI.he.md": "מפרט-אשף-פקודה-אינטראקטיבי",
    "docs/proposals/RFC_002_MCP_SERVER.md": "MCP-Server-Specification",
    "docs/proposals/RFC_002_MCP_SERVER.he.md": "מפרט-שרת-MCP",
    "docs/proposals/RFC_003_SYSTEM_INTEGRATION_WIZARD.md": "Setup-Wizard-Specification",
    "docs/proposals/RFC_003_SYSTEM_INTEGRATION_WIZARD.he.md": "מפרט-אשף-התקנה-ואבחון",
    "docs/proposals/RFC_004_DOCKER_WEBHOOK_SERVER.md": "Docker-Webhook-Server-Specification",
    "docs/proposals/RFC_004_DOCKER_WEBHOOK_SERVER.he.md": "מפרט-שרת-Webhook-וקונטיינר-Docker",
}

_BASENAME_TO_SLUG = {Path(k).name: v for k, v in DOCS_TO_WIKI_MAP.items()}


def _resolve_wiki_target(src_path: Path, raw_target: str) -> str:
    """Converts a relative docs/repo target into a GitHub Wiki slug or GitHub blob URL."""
    if raw_target.startswith(("http://", "https://", "mailto:", "#")):
        return raw_target
    if "#" in raw_target:
        path_part, anchor = raw_target.split("#", 1)
        anchor = f"#{anchor}"
    else:
        path_part, anchor = raw_target, ""

    if not path_part:
        return raw_target

    # Already an extensionless Wiki slug
    if "/" not in path_part and not path_part.endswith(".md") and path_part in DOCS_TO_WIKI_MAP.values():
        return raw_target

    # Try resolving relative to source doc directory, or from repo root
    candidates = [
        (src_path.parent / path_part).resolve(),
        (BASE_DIR / path_part).resolve(),
    ]
    for cand in candidates:
        try:
            rel_posix = cand.relative_to(BASE_DIR.resolve()).as_posix()
        except ValueError:
            continue
        if rel_posix in DOCS_TO_WIKI_MAP:
            return f"{DOCS_TO_WIKI_MAP[rel_posix]}{anchor}"
        if cand.exists():
            return f"{REPO_BLOB_BASE}/{rel_posix}{anchor}"

    base_name = Path(path_part).name
    if base_name in _BASENAME_TO_SLUG:
        return f"{_BASENAME_TO_SLUG[base_name]}{anchor}"

    return raw_target


def render_doc_for_wiki(src_path: Path, raw_text: str) -> str:
    """Transforms repository doc HTML switchers and relative links into clean GitHub Wiki slugs."""
    text = re.sub(
        r'href=(["\'])([^"\']+)\1',
        lambda m: f'href={m.group(1)}{_resolve_wiki_target(src_path, m.group(2))}{m.group(1)}',
        raw_text,
    )
    text = re.sub(
        r'(\[[^\]]+\]\()([^)\s]+)(\))',
        lambda m: f'{m.group(1)}{_resolve_wiki_target(src_path, m.group(2))}{m.group(3)}',
        text,
    )
    return text


def sync_docs_to_wiki() -> int:
    """Regenerates local wiki/*.md mirrors from docs/, docs/proposals/, and ROADMAP*.md."""
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    updated = 0
    for src_rel, wiki_slug in DOCS_TO_WIKI_MAP.items():
        src_path = BASE_DIR / src_rel
        if not src_path.is_file():
            continue
        rendered = render_doc_for_wiki(src_path, src_path.read_text(encoding="utf-8"))
        dest_path = WIKI_DIR / f"{wiki_slug}.md"
        if not dest_path.exists() or dest_path.read_text(encoding="utf-8") != rendered:
            dest_path.write_text(rendered, encoding="utf-8")
            updated += 1
    print(f"[✓] Local docs -> wiki sync complete ({updated} files updated, {len(DOCS_TO_WIKI_MAP)} mapped pages).")
    return updated


def sync_wiki(repo_url=None, local_only=False):
    sync_docs_to_wiki()
    if local_only:
        return True
    if not WIKI_DIR.exists():
        print(f"[-] Wiki source directory not found at: {WIKI_DIR}")
        return False

    if not repo_url:
        # Detect remote from git config
        res = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, cwd=BASE_DIR)
        origin_url = res.stdout.strip()
        if not origin_url:
            print("[-] Could not determine remote.origin.url")
            return False
        
        # Convert https://github.com/owner/repo.git to https://github.com/owner/repo.wiki.git
        if origin_url.endswith(".git"):
            repo_url = origin_url[:-4] + ".wiki.git"
        else:
            repo_url = origin_url + ".wiki.git"

    print(f"[*] Target GitHub Wiki repository: {repo_url}")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "wiki_clone"
        
        # 1. Try to clone existing wiki
        clone_res = subprocess.run(["git", "clone", repo_url, str(tmp_path)], capture_output=True, text=True)
        if clone_res.returncode != 0:
            print("[!] Note: Remote wiki clone returned non-zero (wiki may not be enabled yet on GitHub):")
            print(f"    {clone_res.stderr.strip()}")
            print("[*] Initializing fresh local wiki git repository...")
            tmp_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "-b", "master"], cwd=tmp_path, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=tmp_path, check=True)
        
        # 2. Copy all files from wiki/
        for item in WIKI_DIR.iterdir():
            if item.name.startswith("."):
                continue
            dest = tmp_path / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)

        # 3. Add, commit, and push
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=tmp_path)
        if not status_res.stdout.strip():
            print("[✓] Wiki is already up to date with remote.")
            return True
        
        subprocess.run(["git", "commit", "-m", "docs: sync bilingual documentation from repository wiki/"], cwd=tmp_path, check=True)
        push_res = subprocess.run(["git", "push", "-u", "origin", "HEAD"], capture_output=True, text=True, cwd=tmp_path)
        if push_res.returncode == 0:
            print("[✓] SUCCESS: GitHub Wiki updated successfully!")
            return True
        else:
            print(f"[!] Push to GitHub Wiki failed (GitHub requires Wiki to be active/public on Free plans):")
            print(f"    {push_res.stderr.strip()}")
            return False

if __name__ == "__main__":
    if "--local" in sys.argv:
        sync_docs_to_wiki()
        sys.exit(0)
    url_arg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    success = sync_wiki(url_arg)
    sys.exit(0 if success else 1)
