#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_traffic_analytics.py
-------------------------
Fetches traffic statistics (views, clones, referrers) from the GitHub API,
merges them cumulatively into a persistent JSON database, and generates
an updated TRAFFIC_REPORT.md summary.

Solves GitHub's 14-day data retention limit by archiving history permanently.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ANALYTICS_DIR = BASE_DIR / "docs" / "analytics"
HISTORY_FILE = ANALYTICS_DIR / "traffic_history.json"
REPORT_FILE = ANALYTICS_DIR / "TRAFFIC_REPORT.md"

DEFAULT_REPO = "omerninyo/RightSub"


def get_auth_token():
    token = os.environ.get("TRAFFIC_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        # Fallback to local gh auth token if running locally
        try:
            import subprocess
            res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                token = res.stdout.strip()
        except Exception:
            pass
    return token


def fetch_api(endpoint, token, repo=DEFAULT_REPO):
    url = f"https://api.github.com/repos/{repo}/traffic/{endpoint}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RightSub-Traffic-Archiver",
        "Authorization": f"Bearer {token}"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[-] HTTP Error {e.code} for endpoint '{endpoint}': {e.reason}", file=sys.stderr)
    except Exception as e:
        print(f"[-] Error fetching endpoint '{endpoint}': {e}", file=sys.stderr)
    return None


def load_history():
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Warning reading existing history: {e}, starting fresh.")
    return {
        "views": {},
        "clones": {},
        "referrers": {},
        "last_updated": None
    }


def merge_traffic_data(history, views_data, clones_data, referrers_data):
    # 1. Merge views (timestamp format: 2026-09-20T00:00:00Z -> 2026-09-20)
    if views_data and "views" in views_data:
        for entry in views_data["views"]:
            day = entry["timestamp"][:10]
            count = entry.get("count", 0)
            uniques = entry.get("uniques", 0)
            # Take max if day already partially tracked, or overwrite with official day count
            if day not in history["views"]:
                history["views"][day] = {"count": count, "uniques": uniques}
            else:
                history["views"][day]["count"] = max(history["views"][day]["count"], count)
                history["views"][day]["uniques"] = max(history["views"][day]["uniques"], uniques)

    # 2. Merge clones
    if clones_data and "clones" in clones_data:
        for entry in clones_data["clones"]:
            day = entry["timestamp"][:10]
            count = entry.get("count", 0)
            uniques = entry.get("uniques", 0)
            if day not in history["clones"]:
                history["clones"][day] = {"count": count, "uniques": uniques}
            else:
                history["clones"][day]["count"] = max(history["clones"][day]["count"], count)
                history["clones"][day]["uniques"] = max(history["clones"][day]["uniques"], uniques)

    # 3. Merge referrers
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    if referrers_data and isinstance(referrers_data, list):
        for ref in referrers_data:
            name = ref.get("referrer", "Unknown")
            count = ref.get("count", 0)
            uniques = ref.get("uniques", 0)
            if name not in history["referrers"]:
                history["referrers"][name] = {
                    "count": count,
                    "uniques": uniques,
                    "last_seen": today_str
                }
            else:
                history["referrers"][name]["count"] = max(history["referrers"][name]["count"], count)
                history["referrers"][name]["uniques"] = max(history["referrers"][name]["uniques"], uniques)
                history["referrers"][name]["last_seen"] = today_str

    history["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return history


def generate_report(history):
    views_dict = history.get("views", {})
    clones_dict = history.get("clones", {})
    referrers_dict = history.get("referrers", {})

    total_views = sum(item["count"] for item in views_dict.values())
    total_unique_views = sum(item["uniques"] for item in views_dict.values())
    total_clones = sum(item["count"] for item in clones_dict.values())
    total_unique_cloners = sum(item["uniques"] for item in clones_dict.values())

    all_days = sorted(set(list(views_dict.keys()) + list(clones_dict.keys())), reverse=True)

    report_lines = [
        "# 📊 RightSub — Historical Traffic & Analytics Report",
        "",
        f"> **Last Updated**: `{history.get('last_updated', 'N/A')}`  ",
        "> *This report archives continuous visitor and clone statistics, overcoming GitHub's standard 14-day limit.*",
        "",
        "## 📈 Lifetime Cumulative Totals",
        "",
        "| Metric | Total Count | Total Uniques |",
        "| :--- | :---: | :---: |",
        f"| **Page Views** | **{total_views:,}** | **{total_unique_views:,}** |",
        f"| **Git Clones** | **{total_clones:,}** | **{total_unique_cloners:,}** |",
        "",
        "## 🌐 Top Referring Sites & Networks",
        "",
        "| Referring Source | Total Views | Unique Visitors | Last Active |",
        "| :--- | :---: | :---: | :---: |",
    ]

    if referrers_dict:
        sorted_refs = sorted(referrers_dict.items(), key=lambda x: x[1]["count"], reverse=True)
        for name, data in sorted_refs:
            report_lines.append(f"| `{name}` | {data['count']:,} | {data['uniques']:,} | {data.get('last_seen', 'N/A')} |")
    else:
        report_lines.append("| *None recorded yet* | - | - | - |")

    report_lines.extend([
        "",
        "## 📅 Daily Activity Breakdown",
        "",
        "| Date | Page Views | Unique Visitors | Git Clones | Unique Cloners |",
        "| :---: | :---: | :---: | :---: | :---: |"
    ])

    for day in all_days:
        v = views_dict.get(day, {"count": 0, "uniques": 0})
        c = clones_dict.get(day, {"count": 0, "uniques": 0})
        report_lines.append(f"| {day} | {v['count']} | {v['uniques']} | {c['count']} | {c['uniques']} |")

    report_lines.append("")
    return "\n".join(report_lines)


def main():
    repo = os.environ.get("GITHUB_REPOSITORY") or DEFAULT_REPO
    token = get_auth_token()
    if not token:
        print("[-] Error: No GitHub authentication token found (set TRAFFIC_TOKEN or GITHUB_TOKEN).", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Archiving traffic statistics for: {repo}")
    views_data = fetch_api("views", token, repo)
    clones_data = fetch_api("clones", token, repo)
    referrers_data = fetch_api("popular/referrers", token, repo)

    history = load_history()
    updated_history = merge_traffic_data(history, views_data, clones_data, referrers_data)

    # Save JSON database
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_history, f, indent=2, ensure_ascii=False)
    print(f"[✓] Saved cumulative history: {HISTORY_FILE}")

    # Save Markdown report
    report_content = generate_report(updated_history)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"[✓] Generated traffic report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
