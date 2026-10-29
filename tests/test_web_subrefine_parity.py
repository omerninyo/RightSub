#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_web_subrefine_parity.py
----------------------------
Verifies 100% algorithmic parity between the Python SubRefine engine (`07_fix_plex_punctuation.py`)
and the client-side browser JavaScript engine (`site/subrefine.js`), plus Web UI asset serving
on the RightSub Webhook Daemon (`21_webhook_server.py`).
"""

import json
import shutil
import subprocess
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import importlib
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SITE_DIR = REPO_ROOT / "site"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

fix_plex = importlib.import_module("07_fix_plex_punctuation")
webhook_srv = importlib.import_module("21_webhook_server")


def _run_js_eval(js_expr: str):
    """Executes an expression against site/subrefine.js in Node.js and returns parsed JSON."""
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js not installed")
    subrefine_path = (SITE_DIR / "subrefine.js").as_posix()
    script = f"""
    const sr = require({json.dumps(subrefine_path)});
    const out = ({js_expr});
    process.stdout.write(JSON.stringify(out));
    """
    proc = subprocess.run(
        [node_bin, "-e", script],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_site_files_exist_and_comply_with_a11y_and_bidi():
    """Verify all static web app files exist and enforce semantic landmarks, skip-link, and LTR code isolation."""
    index_html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    styles_css = (SITE_DIR / "styles.css").read_text(encoding="utf-8")
    subrefine_js = (SITE_DIR / "subrefine.js").read_text(encoding="utf-8")
    app_js = (SITE_DIR / "app.js").read_text(encoding="utf-8")

    assert '<a href="#content" class="skip-link"' in index_html
    assert '<main id="content" tabindex="-1">' in index_html
    assert 'aria-live="polite"' in index_html
    assert 'role="tablist"' in index_html
    assert 'role="tab"' in index_html
    assert 'role="tabpanel"' in index_html
    assert '<link rel="icon"' in index_html
    assert 'id="sb-render-before" class="sb-player-line" dir="rtl"' in index_html
    assert "unicode-bidi: isolate" in styles_css
    assert "prefers-reduced-motion: reduce" in styles_css
    assert "decodeSrtBuffer" in subrefine_js
    assert "DEMO_HE_SRT" in app_js


def test_js_vs_python_18_visual_flip_and_homoglyph_parity():
    """
    Guarantee 100% character-for-character parity between Python apply_rlm_to_line()
    and JavaScript applyRlmToLine() across Red Team test vectors.
    """
    vectors = [
        ("?אלן, אתה שומע אותי", True),
        (".המתקפה האחרונה ברצף מתקפות-", True),
        ("- ,חיי אינם ראויים", True),
        (".-או-טי 8. הרמה הגבוהה ביותר", True),
        ('".אהבה משחררת אותך', True),
        ('"...אהבה משחררת אותך', True),
        (',19 יש לי קול. אני בת"', True),
        ("(לאודיטור (אדם שמקשיב.", True),
        ("(לאודיטור (אדם שמקשיב...", True),
        (")מדרגות לפני הבית(", True),
        ("[אתם מוקפים! [צרפתית", True),
        (".<i>שלום עולם</i>", True),
        ("ראיתי את הסוכנים של ה-FBI.", False),
        ("יצאנו ל-ד\u10D4ייט מעולה אתמול!", False),
        ('אביהם וגם אִמם הגיעו עם עו"ד בכיר.', False),
        ("אמם... אני לא בטוח אם לקחת טרמף.", False),
        ("<i>שלום עולם!</i>", False),
        ("{\\an8}- שלום דני!", False),
        ("{\\an8}{\\fad(100,100)}- שלום דני!", False),
    ]

    for raw_line, is_preflipped in vectors:
        py_out = fix_plex.apply_rlm_to_line(raw_line, is_preflipped_file=is_preflipped)
        js_out = _run_js_eval(
            f"sr.applyRlmToLine({json.dumps(raw_line)}, {json.dumps(is_preflipped)})"
        )
        assert js_out == py_out, (
            f"JS/Python parity mismatch for {raw_line!r} (preflipped={is_preflipped}):\n"
            f"  PY: {py_out!r}\n  JS: {js_out!r}"
        )


def test_js_cp1255_byte_decoding_and_bilingual_number_unflipping():
    """Verify that subrefine.js decodes raw Windows-1255 bytes and un-flips reversed 2-digit numbers."""
    he_str = "1\n00:00:01,000 --> 00:00:03,000\n.חיכינו לך 84 שעות במשרד-\n"
    en_str = "1\n00:00:01,000 --> 00:00:03,000\n- We waited 48 hours for you at the office.\n"
    cp1255_bytes = list(he_str.encode("cp1255"))

    res = _run_js_eval(
        f"""(() => {{
            const dec = sr.decodeSrtBuffer(new Uint8Array({json.dumps(cp1255_bytes)}));
            const proc = sr.processSrtContent(dec.text, {{
                cleanAds: true,
                cleanSpeakers: false,
                enContent: {json.dumps(en_str)}
            }});
            return {{ encoding: dec.encoding, proc }};
        }})()"""
    )

    assert res["encoding"] == "windows-1255"
    assert res["proc"]["numbersUnflipped"] == 1
    assert "\u200F- חיכינו לך 48 שעות במשרד.\u200F" in res["proc"]["resultText"]


def test_single_line_preflipped_polarity_and_shifted_timestamp_bilingual_numbers():
    """
    Verify QA/QC fixes:
    1. Single-line Subabi inputs (`? ...`, `...`) trigger pre-flipped polarity in both Python & JS.
    2. Timestamp-based bilingual number matching un-flips numbers even when cue indices shift by +1.
    """
    single_subabi = "1\n00:00:01,000 --> 00:00:03,000\n?אלן, אתה שומע אותי\n"
    assert fix_plex.detect_file_flip_polarity(single_subabi) is True

    he_shifted = (
        "1\n00:00:05,000 --> 00:00:08,000\n"
        "?חיכינו לך 84 שעות במשרד\n"
    )
    en_shifted = (
        "1\n00:00:01,000 --> 00:00:03,000\n"
        "Previously on Boston Legal...\n\n"
        "2\n00:00:05,000 --> 00:00:08,000\n"
        "Did we wait 48 hours for you at the office?\n"
    )
    res = _run_js_eval(
        f"""sr.processSrtContent({json.dumps(he_shifted)}, {{
            cleanAds: true,
            cleanSpeakers: true,
            enContent: {json.dumps(en_shifted)}
        }})"""
    )
    assert res["isPreflippedFile"] is True
    assert res["numbersUnflipped"] == 1
    assert "\u200Fחיכינו לך 48 שעות במשרד?\u200F" in res["resultText"]


def test_webhook_server_serves_web_ui_and_preserves_json_health():
    """Verify 21_webhook_server.py serves HTML to browsers/UI routes and JSON health to API clients."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), webhook_srv.WebhookRequestHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"

    try:
        # 1. API client hitting GET / (no Accept: text/html) -> JSON health
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "healthy"

        # 2. Browser hitting GET / with Accept: text/html -> Web UI HTML
        req = urllib.request.Request(
            f"{base_url}/", headers={"Accept": "text/html,application/xhtml+xml"}
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")
            html_body = resp.read().decode("utf-8")
            assert "RightSubRefine" in html_body or "subrefine.js" in html_body

        # 3. Static JS & CSS routes
        for route in ("/ui", "/subrefine.js", "/styles.css", "/app.js"):
            with urllib.request.urlopen(f"{base_url}{route}") as resp:
                assert resp.status == 200
                assert len(resp.read()) > 100
    finally:
        httpd.shutdown()
        httpd.server_close()
