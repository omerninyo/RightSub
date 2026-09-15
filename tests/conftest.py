import sys
import os
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

@pytest.fixture
def sample_english_srt(tmp_path):
    content = """1
00:00:01,000 --> 00:00:03,500
PREVIOUSLY ON "BOSTON LEGAL"...

2
00:00:04,000 --> 00:00:06,800
(Alan) THE FIRM IS GOING BROKE?
DID I KNOW THIS AND FORGET?

3
00:00:07,000 --> 00:00:09,200
(dramatic music playing)

4
00:00:09,500 --> 00:00:12,000
YOU'RE IN THE EARLY STAGES OF ALZHEIMER'S.
"""
    file_path = tmp_path / "sample.en.srt"
    file_path.write_text(content, encoding="utf-8")
    return file_path

@pytest.fixture
def sample_hebrew_batches_dir(tmp_path):
    translated_dir = tmp_path / "translated"
    translated_dir.mkdir()
    batch_data = [
        {"index": 1, "hebrew": "בפרקים הקודמים ב״בוסטון ליגל״..."},
        {"index": 2, "hebrew": "המשרד פושט רגל?\nידעתי את זה ושכחתי?"},
        {"index": 3, "hebrew": ""},
        {"index": 4, "hebrew": "אתה בשלבים המוקדמים של אלצהיימר."},
    ]
    import json
    batch_file = translated_dir / "batch_01_he.json"
    batch_file.write_text(json.dumps(batch_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return translated_dir
