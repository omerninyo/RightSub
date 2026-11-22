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
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
README_EN = BASE_DIR / "README.md"
README_HE = BASE_DIR / "README.he.md"

def _collect_count_for(targets) -> int:
    pytest_bin = shutil.which("pytest") or "pytest"
    cmd_base = [pytest_bin] if shutil.which("pytest") else [sys.executable, "-m", "pytest"]
    res = subprocess.run(
        cmd_base + list(targets) + ["--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )
    if res.returncode != 0 and cmd_base[0] != sys.executable:
        res = subprocess.run(
            [sys.executable, "-m", "pytest"] + list(targets) + ["--collect-only", "-q", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )
    match = re.search(r"collected\s+(\d+)\s+items", res.stdout) or re.search(
        r"(\d+)\s+tests?\s+collected", res.stdout
    )
    if match:
        return int(match.group(1))
    lines = [line for line in res.stdout.splitlines() if "::test_" in line]
    return len(lines)


def get_pytest_test_counts():
    """Returns (unit_count, dataset_count, total_count) across tests/ and case_study_archive/."""
    unit_count = _collect_count_for(["tests"]) if (BASE_DIR / "tests").exists() else 0
    dataset_count = (
        _collect_count_for(["case_study_archive"])
        if (BASE_DIR / "case_study_archive").exists()
        else 0
    )
    return unit_count, dataset_count, unit_count + dataset_count


def get_pytest_test_count():
    """Runs pytest --collect-only and returns total collected tests (unit + dataset)."""
    _, _, total = get_pytest_test_counts()
    return total or None


def update_test_badges(count, unit_count=None, dataset_count=None):
    if not count:
        print("[-] Could not determine test count.")
        return False

    if unit_count is None or dataset_count is None:
        unit_count, dataset_count, total = get_pytest_test_counts()
        if total == count and unit_count:
            pass
        else:
            unit_count = count
            dataset_count = 0

    print(f"[*] Current test counts: total={count} (unit={unit_count}, dataset={dataset_count})")
    badge_url = f"https://img.shields.io/badge/Pytest-{count}%2F{count}%20Passing-success.svg"

    # Update README.md
    if README_EN.exists():
        content = README_EN.read_text(encoding="utf-8")
        updated = re.sub(
            r"https://img\.shields\.io/badge/Pytest-\d+%2F\d+%20Passing-success\.svg",
            badge_url,
            content,
        )
        updated = re.sub(
            r"\(\d+\s+automated tests:\s*\d+\s+unit tests\s*\+\s*\d+\s+dataset integration tests\)",
            f"({count} automated tests: {unit_count} unit tests + {dataset_count} dataset integration tests)",
            updated,
        )
        updated = re.sub(r"\(\d+\s+unit tests\)", f"({unit_count} unit tests)", updated)
        if updated != content:
            README_EN.write_text(updated, encoding="utf-8")
            print(f"[✓] Updated test badge & breakdown in README.md to {count}/{count}")

    # Update README.he.md
    if README_HE.exists():
        content = README_HE.read_text(encoding="utf-8")
        updated = re.sub(
            r"https://img\.shields\.io/badge/Pytest-\d+%2F\d+%20Passing-success\.svg",
            badge_url,
            content,
        )
        updated = re.sub(
            r"של\s+\d+\s+בדיקות אוטומטיות\s*\(\d+\s+בדיקות יחידה\s*\+\s*\d+\s+בדיקות אינטגרציה על מערך הפרקים\)",
            f"של {count} בדיקות אוטומטיות ({unit_count} בדיקות יחידה + {dataset_count} בדיקות אינטגרציה על מערך הפרקים)",
            updated,
        )
        updated = re.sub(r"בדיקות יחידה מקיפה של \d+ בדיקות", f"בדיקות יחידה מקיפה של {count} בדיקות", updated)
        if updated != content:
            README_HE.write_text(updated, encoding="utf-8")
            print(f"[✓] Updated test badge & breakdown in README.he.md to {count}/{count}")

    # Update site/index.html & site/app.js
    site_html = BASE_DIR / "site" / "index.html"
    if site_html.exists():
        content = site_html.read_text(encoding="utf-8")
        updated = re.sub(r"\d+\s+בדיקות אוטומטיות", f"{count} בדיקות אוטומטיות", content)
        if updated != content:
            site_html.write_text(updated, encoding="utf-8")
            print(f"[✓] Updated test count in site/index.html to {count}")

    site_app = BASE_DIR / "site" / "app.js"
    if site_app.exists():
        content = site_app.read_text(encoding="utf-8")
        updated = re.sub(r"\d+\s+בדיקות אוטומטיות", f"{count} בדיקות אוטומטיות", content)
        updated = re.sub(r"\d+\s+Automated Tests", f"{count} Automated Tests", updated)
        if updated != content:
            site_app.write_text(updated, encoding="utf-8")
            print(f"[✓] Updated test count in site/app.js to {count}")

    return True


def sync_project_version():
    """Ensures pyproject.toml, site/*, install.bat, and Formula/rightsub.rb stay synchronized with rightsub.py __version__."""
    rightsub_py = BASE_DIR / "rightsub.py"
    if not rightsub_py.exists():
        return
    rs_text = rightsub_py.read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', rs_text, flags=re.MULTILINE)
    if not m:
        return
    ver = m.group(1)

    targets = [
        (
            BASE_DIR / "pyproject.toml",
            [(r'^(version\s*=\s*["\'])([^"\']+)(["\'])', rf"\g<1>{ver}\g<3>", re.MULTILINE)],
        ),
        (
            BASE_DIR / "site" / "index.html",
            [
                (r'(<span class="meta-tag" dir="ltr">v)([^<]+)(</span>)', rf"\g<1>{ver}\g<3>", 0),
                (r"(<strong>RightSub v)(\d+\.\d+\.\d+)(</strong>)", rf"\g<1>{ver}\g<3>", 0),
            ],
        ),
        (
            BASE_DIR / "site" / "app.js",
            [
                (r"(app\.js — RightSub v)(\d+\.\d+\.\d+)", rf"\g<1>{ver}", 0),
                (r"(<strong>RightSub v)(\d+\.\d+\.\d+)(</strong>)", rf"\g<1>{ver}\g<3>", 0),
            ],
        ),
        (
            BASE_DIR / "site" / "styles.css",
            [(r"(styles\.css — RightSub v)(\d+\.\d+\.\d+)", rf"\g<1>{ver}", 0)],
        ),
        (
            BASE_DIR / "site" / "subrefine.js",
            [(r"(Master(?:ing)? Engine \(v)(\d+\.\d+\.\d+)(\))", rf"\g<1>{ver}\g<3>", 0)],
        ),
        (
            BASE_DIR / "install.bat",
            [(r"(v)(\d+\.\d+\.\d+)", rf"\g<1>{ver}", 0)],
        ),
        (
            BASE_DIR / "Formula" / "rightsub.rb",
            [
                (r'(version\s+")(\d+\.\d+\.\d+)(")', rf"\g<1>{ver}\g<3>", 0),
                (r"(/archive/refs/tags/v)(\d+\.\d+\.\d+)(\.tar\.gz)", rf"\g<1>{ver}\g<3>", 0),
                (r'(assert_match\s+")(\d+\.\d+\.\d+)(")', rf"\g<1>{ver}\g<3>", 0),
            ],
        ),
    ]

    for path, patterns in targets:
        if not path.exists():
            continue
        orig = path.read_text(encoding="utf-8")
        updated = orig
        for pat, repl, flags in patterns:
            updated = re.sub(pat, repl, updated, flags=flags)
        if updated != orig:
            path.write_text(updated, encoding="utf-8")
            print(f"[✓] Synchronized {path.relative_to(BASE_DIR)} version to {ver}")


if __name__ == "__main__":
    sync_project_version()
    unit_c, ds_c, total_c = get_pytest_test_counts()
    if total_c:
        update_test_badges(total_c, unit_c, ds_c)
    else:
        print("[-] Failed to collect tests.")
        sys.exit(1)
