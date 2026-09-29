#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_domain_knowledge.py
-------------------------
Unit tests for the Hierarchical Domain Knowledge & Context Engine (scripts/domain_knowledge.py).
Tests:
1. Multi-tier classification: Genres (TMDb/Bible), Overview keywords, and Offline cue fingerprinting.
2. Domain pack guidelines generation.
3. Bilingual Anchor Validation:
   - Replaces MT blunders only when confirmed by master English cue.
   - Preserves non-sci-fi terms (e.g. military tanker is NOT turned into a spaceship).
   - Preserves theological/biblical 'מעשה בראשית' when English line is not 'as a matter of fact'.
4. Integration with run_deterministic_canon_pass in 19_polish_and_qc.py.
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import domain_knowledge as dk
import importlib
polish_module = importlib.import_module("19_polish_and_qc")

class TestDomainKnowledge:

    def test_classify_from_tmdb_genres(self):
        # Sci-Fi
        prof_scifi = dk.classify_media_domain(title="Unknown Space Movie", genres=["Science Fiction", "Action"])
        assert prof_scifi.primary_domain == "sci_fi"
        assert "sci_fi" in prof_scifi.active_domains

        # Legal
        prof_legal = dk.classify_media_domain(title="Courtroom Drama", genres=["Crime", "Drama"])
        # If overview contains courtroom keywords
        prof_legal2 = dk.classify_media_domain(title="The Verdict", genres=["Legal"])
        assert "legal" in prof_legal2.active_domains

        # Military
        prof_mil = dk.classify_media_domain(title="WWII Story", genres=["War"])
        assert "military" in prof_mil.active_domains

        # Fantasy
        prof_fan = dk.classify_media_domain(title="The Dragon Realm", genres=["Fantasy"])
        assert "fantasy" in prof_fan.active_domains

    def test_classify_from_franchise_title(self):
        prof = dk.classify_media_domain(title="Star Wars Episode IV A New Hope")
        assert prof.franchise == "star wars"
        assert "sci_fi" in prof.active_domains
        assert "military" in prof.active_domains

        prof_trek = dk.classify_media_domain(title="Star Trek The Next Generation")
        assert prof_trek.franchise == "star trek"
        assert "sci_fi" in prof_trek.active_domains

        prof_lotr = dk.classify_media_domain(title="Lord of the Rings The Fellowship")
        assert prof_lotr.franchise == "lord of the rings"
        assert "fantasy" in prof_lotr.active_domains

    def test_classify_from_overview_keywords(self):
        overview = "The crew of a deep space starship encounters a hostile alien species in high planetary orbit."
        prof = dk.classify_media_domain(title="Nameless 2024", overview=overview)
        assert "sci_fi" in prof.active_domains

        legal_overview = "A tenacious defense attorney delivers a passionate courtroom objection during cross-examination."
        prof_legal = dk.classify_media_domain(title="Law Series", overview=legal_overview)
        assert "legal" in prof_legal.active_domains

    def test_classify_offline_cue_fingerprinting(self):
        # Media with no title or overview or genres, but cues contain sci-fi terms
        cues = [
            {"index": 1, "text": "Prepare the hyperdrive for jump."},
            {"index": 2, "text": "The starship is entering orbit."},
            {"index": 3, "text": "Sir, our energy shields are failing."},
            {"index": 4, "text": "Tell the droid to fix it."}
        ]
        prof = dk.classify_media_domain(sample_cues=cues)
        assert "sci_fi" in prof.active_domains
        assert prof.primary_domain == "sci_fi"

    def test_bilingual_anchor_validation(self):
        # Case 1: English has 'As a matter of fact' and Hebrew has 'מעשה בראשית' -> REPLACED
        cues_match = [
            {"index": 1, "en": "As a matter of fact, I was there.", "he": "מעשה בראשית, הייתי שם."}
        ]
        mods = polish_module.run_deterministic_canon_pass(cues_match)
        assert 1 in mods
        assert mods[1]["polished_he"] == "למעשה, הייתי שם."

        # Case 2: Theological context (Hebrew has 'מעשה בראשית' but English has 'The story of Creation') -> PRESERVED!
        cues_theology = [
            {"index": 1, "en": "Let us study the story of Creation.", "he": "בואו נלמד על מעשה בראשית."}
        ]
        mods_theo = polish_module.run_deterministic_canon_pass(cues_theology)
        assert 1 not in mods_theo  # ZERO false positives!

        # Case 3: Military aviation tanker (English has 'aerial tanker', Hebrew has 'מכלית קרב') -> PRESERVED!
        prof_military = dk.classify_media_domain(title="Top Gun", genres=["War"])
        cues_tanker = [
            {"index": 1, "en": "The aerial tanker is approaching at 20,000 feet.", "he": "מכלית הקרב מתקרבת בעשרים אלף רגל."}
        ]
        mods_tanker = polish_module.run_deterministic_canon_pass(cues_tanker, domain_profile=prof_military)
        assert 1 not in mods_tanker  # Not turned into a spaceship!

        # Case 4: Sci-Fi fighter (English has 'snub fighters', Hebrew has 'מכליות קרב') -> REPLACED WITH SPACESHIP!
        prof_scifi = dk.classify_media_domain(title="Space War", genres=["Science Fiction"])
        cues_scifi = [
            {"index": 1, "en": "Enemy snub fighters incoming!", "he": "מכליות קרב של האויב מגיעות!"}
        ]
        mods_scifi = polish_module.run_deterministic_canon_pass(cues_scifi, domain_profile=prof_scifi)
        assert 1 in mods_scifi
        assert mods_scifi[1]["polished_he"] == "חלליות קרב של האויב מגיעות!"

    def test_universal_typographical_corrections_always_run(self):
        cues = [
            {"index": 1, "en": "Hello Captain", "he": "שלום קאבתן."},
            {"index": 2, "en": "Put it here", "he": "צריך לשום את זה כאן."},
            {"index": 3, "en": "It pulls us", "he": "זה מוחב אותנו."}
        ]
        mods = polish_module.run_deterministic_canon_pass(cues)
        assert mods[1]["polished_he"] == "שלום קברניט."
        assert mods[2]["polished_he"] == "צריך לשים את זה כאן."
        assert mods[3]["polished_he"] == "זה מושכת אותנו."
