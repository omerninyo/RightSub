#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_gender_and_bible.py
-------------------------
Validates:
1. Prompt builder injection of Translation Bible characters and context overlap window.
2. QA engine detection of vocative gender mismatches in Hebrew dialogue.
"""

import os
import json
import tempfile
from importlib import import_module
import pytest

prompt_module = import_module("09_prompt_builder")
build_prompts = prompt_module.build_prompts
load_bible = prompt_module.load_bible

qa_module = import_module("08_quality_assurance")
check_gender_mismatches = qa_module.check_gender_mismatches
audit_pair = qa_module.audit_pair

SAMPLE_SRT = """1
00:00:01,000 --> 00:00:03,000
Alan, did you talk to Denny?

2
00:00:03,500 --> 00:00:05,000
Yes, Shirley. He is waiting in his office.

3
00:00:05,500 --> 00:00:08,000
[Tara] Did you file the brief with the court?

4
00:00:08,500 --> 00:00:11,000
Not yet, Tara. I will do it after lunch.

5
00:00:11,500 --> 00:00:14,000
Your Honor, the defense is ready.

6
00:00:14,500 --> 00:00:17,000
Proceed, Mr. Shore.
"""

SAMPLE_BIBLE = {
    "characters": [
        {"name": "Alan Shore", "hebrew_name": "אלן שור", "gender": "male", "pronouns": "אתה"},
        {"name": "Shirley Schmidt", "hebrew_name": "שירלי שמידט", "gender": "female", "pronouns": "את"},
        {"name": "Tara Wilson", "hebrew_name": "טרה וילסון", "gender": "female", "pronouns": "את"}
    ],
    "honorifics_and_terms": [
        {"term": "Your Honor", "hebrew_translation": "כבוד השופט/ת"},
        {"term": "Counselor", "hebrew_translation": "עורך הדין"}
    ]
}

class TestPromptBuilderWithBibleAndOverlap:
    def test_load_bible_formatting(self, tmp_path):
        bible_file = tmp_path / "bible.json"
        bible_file.write_text(json.dumps(SAMPLE_BIBLE, ensure_ascii=False), encoding="utf-8")

        formatted = load_bible(str(bible_file))
        assert "Alan Shore (אלן שור): Gender=male, Pronouns=אתה" in formatted
        assert "Shirley Schmidt (שירלי שמידט): Gender=female, Pronouns=את" in formatted
        assert "Your Honor -> כבוד השופט/ת" in formatted

    def test_prompt_generation_with_overlap_and_bible(self, tmp_path):
        srt_file = tmp_path / "test.en.srt"
        srt_file.write_text(SAMPLE_SRT, encoding="utf-8")

        bible_file = tmp_path / "translation_bible.json"
        bible_file.write_text(json.dumps(SAMPLE_BIBLE, ensure_ascii=False), encoding="utf-8")

        output_dir = tmp_path / "prompts"

        success = build_prompts(
            srt_path=str(srt_file),
            title="Test Show",
            bible_path=str(bible_file),
            overlap=2,
            chunk_size=3,
            output_dir=str(output_dir)
        )
        assert success is True

        # Check agent 1 (cues 1..3)
        agent1_path = output_dir / "agent_01.json"
        assert agent1_path.exists()
        agent1_data = json.loads(agent1_path.read_text(encoding="utf-8"))
        assert "Shirley Schmidt (שירלי שמידט)" in agent1_data["Prompt"]
        assert "GENDER ACCURACY & VOCATIVE (DIRECT ADDRESS) RULES" in agent1_data["Prompt"]
        # Chunk 1 has no previous overlap
        assert "PREVIOUS DIALOGUE CONTEXT" not in agent1_data["Prompt"]

        # Check agent 2 (cues 4..6)
        agent2_path = output_dir / "agent_02.json"
        assert agent2_path.exists()
        agent2_data = json.loads(agent2_path.read_text(encoding="utf-8"))
        assert "Shirley Schmidt (שירלי שמידט)" in agent2_data["Prompt"]
        assert "PREVIOUS DIALOGUE CONTEXT" in agent2_data["Prompt"]
        # Should contain cue 2 and cue 3 as context
        assert "[2]" in agent2_data["Prompt"]
        assert "[3]" in agent2_data["Prompt"]

        # Check manifest
        manifest_path = output_dir / "prompt_manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest_data["overlap_cues"] == 2
        assert manifest_data["bible_path"] == str(bible_file)

class TestQAGenderMismatchDetection:
    def test_female_mismatch_flagged(self):
        cues = [
            (1, "00:00:01,000 --> 00:00:03,000", "שירלי, אתה מוכן ללכת למשפט?"),
            (2, "00:00:04,000 --> 00:00:06,000", "גברתי השופטת, אתה צודק בהחלט."),
            (3, "00:00:07,000 --> 00:00:09,000", "טרה, תפסיק לצעוק עליי.")
        ]
        mismatches = check_gender_mismatches(cues)
        assert len(mismatches) == 3
        assert "female 'שירלי' with masculine 'אתה מוכן'" in mismatches[0]
        assert "female 'גברתי השופטת' with masculine 'אתה צודק'" in mismatches[1]
        assert "female 'טרה' with masculine 'תפסיק'" in mismatches[2]

    def test_male_mismatch_flagged(self):
        cues = [
            (1, "00:00:01,000 --> 00:00:03,000", "אדוני, את מוכנה להעיד?"),
            (2, "00:00:04,000 --> 00:00:06,000", "כבוד השופט, את צודקת."),
            (3, "00:00:07,000 --> 00:00:09,000", "אלן, תפסיקי לבכות.")
        ]
        mismatches = check_gender_mismatches(cues)
        assert len(mismatches) == 3
        assert "male 'אדוני' with feminine 'את מוכנה'" in mismatches[0]
        assert "male 'כבוד השופט' with feminine 'את צודקת'" in mismatches[1]
        assert "male 'אלן' with feminine 'תפסיקי'" in mismatches[2]

    def test_clean_gender_passes(self):
        cues = [
            (1, "00:00:01,000 --> 00:00:03,000", "שירלי, את מוכנה ללכת למשפט?\u200F"),
            (2, "00:00:04,000 --> 00:00:06,000", "כבוד השופטת, את צודקת בהחלט.\u200F"),
            (3, "00:00:07,000 --> 00:00:09,000", "טרה, תפסיקי לצעוק עליי.\u200F"),
            (4, "00:00:10,000 --> 00:00:12,000", "אלן, אתה מוכן לבוא איתי?\u200F"),
            (5, "00:00:13,000 --> 00:00:15,000", "אדוני, אתה יכול להמשיך.\u200F")
        ]
        mismatches = check_gender_mismatches(cues)
        assert len(mismatches) == 0

    def test_audit_pair_strict_gender(self, tmp_path):
        en_file = tmp_path / "test.en.srt"
        en_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nShirley, are you ready?\n", encoding="utf-8")

        he_mismatch = tmp_path / "test.he.srt"
        he_mismatch.write_text("1\n00:00:01,000 --> 00:00:03,000\nשירלי, אתה מוכן?\u200F\n", encoding="utf-8")

        # Non-strict mode: reports warning, passes
        passed_loose, report_loose = audit_pair(str(en_file), str(he_mismatch), strict_gender=False)
        assert passed_loose is True
        assert report_loose["gender_mismatches"] == 1
        assert len(report_loose["warnings"]) == 1

        # Strict mode: reports error, fails
        passed_strict, report_strict = audit_pair(str(en_file), str(he_mismatch), strict_gender=True)
        assert passed_strict is False
        assert report_strict["gender_mismatches"] == 1
        assert len(report_strict["errors"]) == 1
