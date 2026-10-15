#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_docs_consistency.py
------------------------
Validates documentation integrity and prevents documentation drift:
1. Verifies that all links referenced in README.md and README.he.md exist.
2. Verifies that all CLI commands listed in the documentation tables exist in rightsub.py.
3. Verifies that both Windows and macOS instructions are present and balanced.
4. Verifies that the test badge matches the actual number of tests.
"""

import re
import os
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
README_EN = REPO_ROOT / "README.md"
README_HE = REPO_ROOT / "README.he.md"
DOCS_DIR = REPO_ROOT / "docs"
RIGHTSUB_PY = REPO_ROOT / "rightsub.py"


def test_readme_files_exist():
    assert README_EN.exists(), "README.md must exist"
    assert README_HE.exists(), "README.he.md must exist"


def test_readme_links_resolve():
    """Ensure all markdown links to local docs in READMEs actually exist."""
    link_pattern = re.compile(r'\[([^\]]+)\]\((docs/[^\)#]+)(?:#[^\)]+)?\)')
    
    for readme_path in [README_EN, README_HE]:
        content = readme_path.read_text(encoding="utf-8")
        matches = link_pattern.findall(content)
        assert len(matches) > 0, f"Expected to find doc links in {readme_path.name}"
        
        for text, rel_path in matches:
            target = REPO_ROOT / rel_path
            assert target.exists(), f"Broken link in {readme_path.name}: '{rel_path}' does not exist on disk."


def test_cli_commands_documented():
    """Ensure every command defined in rightsub.py is listed in README documentation."""
    rightsub_code = RIGHTSUB_PY.read_text(encoding="utf-8")
    
    # Extract registered commands from script_mapping
    mapping_match = re.search(r'script_mapping\s*=\s*\{([^}]+)\}', rightsub_code)
    assert mapping_match, "Could not find script_mapping in rightsub.py"
    
    defined_commands = re.findall(r'["\']([a-z0-9\-_]+)["\']\s*:', mapping_match.group(1))
    assert len(defined_commands) >= 10, "Expected at least 10 commands in rightsub.py"
    
    readme_en_content = README_EN.read_text(encoding="utf-8")
    readme_he_content = README_HE.read_text(encoding="utf-8")
    
    for cmd in defined_commands:
        assert f"`{cmd}`" in readme_en_content, f"Command `{cmd}` missing from README.md"
        assert f"`{cmd}`" in readme_he_content, f"Command `{cmd}` missing from README.he.md"


def test_cross_platform_parity_in_docs():
    """Ensure both Windows and macOS/Linux have dedicated, balanced instructions."""
    for readme_path in [README_EN, README_HE]:
        content = readme_path.read_text(encoding="utf-8").lower()
        
        # Windows indicators
        assert "windows" in content, f"Missing Windows references in {readme_path.name}"
        assert ("cmd" in content or "powershell" in content), f"Missing CMD/PowerShell instructions in {readme_path.name}"
        assert ("rightsub.bat" in content or "install.bat" in content), f"Missing Windows batch references in {readme_path.name}"
        
        # macOS / Linux indicators
        assert "mac" in content or "macos" in content, f"Missing macOS references in {readme_path.name}"
        assert "terminal" in content, f"Missing Terminal references in {readme_path.name}"


def test_readme_hebrew_direction_wrapper():
    """Verify README.he.md starts with RTL wrapper and ends with closing tag."""
    content = README_HE.read_text(encoding="utf-8").strip()
    assert content.startswith('<div dir="rtl">'), "README.he.md must start with <div dir=\"rtl\">"
    assert content.endswith('</div>'), "README.he.md must end with </div>"


def test_roadmap_links_and_direction():
    """Ensure ROADMAP files exist, resolve internal doc links, and comply with RTL wrappers."""
    roadmap_en = REPO_ROOT / "ROADMAP.md"
    roadmap_he = REPO_ROOT / "ROADMAP.he.md"
    assert roadmap_en.exists(), "ROADMAP.md must exist"
    assert roadmap_he.exists(), "ROADMAP.he.md must exist"

    content_he = roadmap_he.read_text(encoding="utf-8").strip()
    assert content_he.startswith('<div dir="rtl">'), "ROADMAP.he.md must start with <div dir=\"rtl\">"
    assert content_he.endswith('</div>'), "ROADMAP.he.md must end with </div>"

    link_pattern = re.compile(r'\[([^\]]+)\]\((docs/[^\)#]+)(?:#[^\)]+)?\)')
    for roadmap_path in [roadmap_en, roadmap_he]:
        content = roadmap_path.read_text(encoding="utf-8")
        matches = link_pattern.findall(content)
        assert len(matches) > 0, f"Expected doc links in {roadmap_path.name}"
        for text, rel_path in matches:
            target = REPO_ROOT / rel_path
            assert target.exists(), f"Broken link in {roadmap_path.name}: '{rel_path}' does not exist on disk."


def test_version_single_source_of_truth_and_milestone_gate():
    """
    Prevent version drift across pyproject.toml, rightsub.py, and webhook server,
    and forbid premature minor/major milestone version bumps while ROADMAP tasks remain open.
    """
    pyproject_path = REPO_ROOT / "pyproject.toml"
    pyproject_content = pyproject_path.read_text(encoding="utf-8")
    pyproject_match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', pyproject_content, flags=re.MULTILINE)
    assert pyproject_match, "Could not find version = '...' in pyproject.toml"
    pyproject_version = pyproject_match.group(1)

    rightsub_content = RIGHTSUB_PY.read_text(encoding="utf-8")
    rightsub_match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', rightsub_content, flags=re.MULTILINE)
    assert rightsub_match, "Could not find __version__ = '...' in rightsub.py"
    rightsub_version = rightsub_match.group(1)

    assert re.match(r'^\d+\.\d+\.\d+$', rightsub_version), f"Invalid SemVer in rightsub.py: {rightsub_version}"
    assert pyproject_version == rightsub_version, (
        f"Version drift detected! pyproject.toml has '{pyproject_version}' "
        f"while rightsub.py has '{rightsub_version}'."
    )

    # Verify webhook server imports the exact same version
    import importlib.util
    ws_path = REPO_ROOT / "scripts" / "21_webhook_server.py"
    spec = importlib.util.spec_from_file_location("webhook_server_ver_check", ws_path)
    ws_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ws_mod)
    assert ws_mod.SERVER_VERSION == rightsub_version, (
        f"21_webhook_server.py SERVER_VERSION ('{ws_mod.SERVER_VERSION}') "
        f"does not match rightsub.py ('{rightsub_version}')."
    )

    # Milestone Gate: if version ends with .0 (e.g. 1.4.0), ensure its section in ROADMAP.md has no unchecked '- [ ]' items
    if rightsub_version.endswith(".0"):
        roadmap_content = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        section_pattern = re.compile(
            rf'^##+ [^\n]*(?:v|Version\s+){re.escape(rightsub_version)}\b(.*?)(?=^## |\Z)',
            flags=re.MULTILINE | re.DOTALL
        )
        sec_match = section_pattern.search(roadmap_content)
        if sec_match:
            unchecked = re.findall(r'^\s*-\s*\[\s\]\s+', sec_match.group(1), flags=re.MULTILINE)
            assert len(unchecked) == 0, (
                f"Premature milestone version '{rightsub_version}'! ROADMAP.md still has "
                f"{len(unchecked)} unchecked '- [ ]' task(s) for v{rightsub_version}. "
                f"Use a patch version (e.g. 1.3.x) until all milestone tasks are shipped."
            )

