from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/ORDERED_SANITY_FIXTURE_SPEC_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def test_ordered_sanity_fixture_spec_covers_required_fixture_families() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "Current-player elite tier",
        "RB/WR balance",
        "Replacement/depth tier",
        "QB format caps",
        "TE no-premium caps",
        "Veteran age windows",
        "Rookie top cluster",
        "Rookie watchlist",
        "Pick ladder",
        "Pick-vs-player neighborhoods",
        "External assets",
        "Decision Board",
    ]

    for term in required_terms:
        assert term in text


def test_ordered_sanity_fixture_spec_names_core_fixture_subjects() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "Christian McCaffrey",
        "Bijan Robinson",
        "Josh Allen",
        "Trey McBride",
        "Daniel Sobkowicz",
        "2026 1.03",
        "2026 5.04",
        "Keenan Allen",
        "Darius Slayton",
        "Kaleb Johnson",
        "Luke McCaffrey",
        "Jeremiyah Love",
        "Makai Lemon",
        "Ja'Kobi Lane",
    ]

    for term in required_terms:
        assert term in text


def test_ordered_sanity_fixture_spec_stays_non_formula_and_non_numeric_targeted() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "intentionally avoids exact numeric score targets" in text
    assert "Do not tune formulas from this spec." in text
    assert "R22 should not add tests that:" in text
    assert "require exact score values" in text
    assert "force a cross-position formula opinion" in text
    assert "Do not use this spec as proof the model is ready for money decisions." in text
    assert not re.search(r"(score|value|rank)\s*(>=|<=|==|>|<)\s*\d", text, re.IGNORECASE)


def test_ordered_sanity_fixture_spec_uses_existing_fixture_contract_types() -> None:
    text = REPORT.read_text(encoding="utf-8")

    for fixture_type in [
        "expected_ordering",
        "expected_tier",
        "expected_review_if_disagrees",
        "expected_receipt_explanation",
        "expected_lifecycle",
        "expected_suppression",
        "expected_market_separation",
    ]:
        assert fixture_type in text


def test_refinement_queue_marks_r21_done_with_audit_note() -> None:
    queue = QUEUE.read_text(encoding="utf-8")

    assert "| R21 | Build ordered sanity fixture spec |" in queue
    r21_line = next(line for line in queue.splitlines() if line.startswith("| R21 |"))
    assert "| Done |" in r21_line
    assert "ORDERED_SANITY_FIXTURE_SPEC_20260605.md" in r21_line
    assert "elite tiers, replacement/depth tiers, pick ladders, format caps" in r21_line
