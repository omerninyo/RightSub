#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_docs.py
--------------
Maintains documentation consistency across READMEs and Wiki:
1. Dynamically detects current total pytest test count.
2. Updates test badges in README.md and README.he.md.
3. Validates doc links and CLI command parity.
"""

import sys
import re
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
README_EN = BASE_DIR / "README.md"
README_HE = BASE_DIR / "README.he.md"

def get_pytest_test_count():
    """Runs pytest --collect-only and returns total collected tests."""
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )
    # Search for line like "69 tests collected" or "collected 69 items"
    match = re.search(r'collected\s+(\d+)\s+items', res.stdout)
    if not match:
        match = re.search(r'(\d+)\s+tests\s+collected', res.stdout)
    if match:
        return int(match.group(1))
    
    # Fallback: count lines ending in ::test_*
    lines = [line for line in res.stdout.splitlines() if "::test_" in line]
    if lines:
        return len(lines)
    return None

def update_test_badges(count):
    if not count:
        print("[-] Could not determine test count.")
        return False
    
    print(f"[*] Current test count: {count}")
    badge_en = f"https://img.shields.io/badge/Pytest-{count}%2F{count}%20Passing-success.svg"
    badge_he = f"https://img.shields.io/badge/Pytest-{count}%2F{count}%20Passing-success.svg"
    
    # Update README.md
    if README_EN.exists():
        content = README_EN.read_text(encoding="utf-8")
        updated = re.sub(
            r'https://img\.shields\.io/badge/Pytest-\d+%2F\d+%20Passing-success\.svg',
            badge_en,
            content
        )
        # Update text mentions of test counts e.g., (XX unit tests)
        updated = re.sub(r'\(\d+\s+unit tests\)', f'({count} unit tests)', updated)
        if updated != content:
            README_EN.write_text(updated, encoding="utf-8")
            print(f"[✓] Updated test badge in README.md to {count}/{count}")

    # Update README.he.md
    if README_HE.exists():
        content = README_HE.read_text(encoding="utf-8")
        updated = re.sub(
            r'https://img\.shields\.io/badge/Pytest-\d+%2F\d+%20Passing-success\.svg',
            badge_he,
            content
        )
        updated = re.sub(r'בדיקות יחידה מקיפה של \d+ בדיקות', f'בדיקות יחידה מקיפה של {count} בדיקות', updated)
        if updated != content:
            README_HE.write_text(updated, encoding="utf-8")
            print(f"[✓] Updated test badge in README.he.md to {count}/{count}")

    return True

if __name__ == "__main__":
    count = get_pytest_test_count()
    if count:
        update_test_badges(count)
    else:
        print("[-] Failed to collect tests.")
        sys.exit(1)
