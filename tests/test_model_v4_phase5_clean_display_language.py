from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROOM_PAGE = ROOT / "app/pages/06_draft_board.py"
JUNE15_PAGE = ROOT / "app/pages/08_june15_review.py"


def test_phase5_display_label_mapping_is_present() -> None:
    draft_room = DRAFT_ROOM_PAGE.read_text(encoding="utf-8")
    june15 = JUNE15_PAGE.read_text(encoding="utf-8")
    combined = draft_room + "\n" + june15

    expected_labels = {
        '"allowed_use": "Use"',
        '"blocked_use": "Blocked"',
        '"confidence_cap": "Trust Cap"',
        '"market_share_score": "College Team Share"',
        '"draft_capital_score": "NFL Draft Pick Signal"',
        '"source_risk_level": "Evidence Risk"',
        '"model_edge_weirdness": "Model Separation"',
        '"source_shape_warning": "Data Shape Warning"',
        '"format_discipline_case": "Format Discipline"',
    }
    for label in expected_labels:
        assert label in combined


def test_phase5_default_tables_use_warning_groups_and_preserve_raw_drilldowns() -> None:
    draft_room = DRAFT_ROOM_PAGE.read_text(encoding="utf-8")
    june15 = JUNE15_PAGE.read_text(encoding="utf-8")

    assert 'output["Warning Groups"]' in draft_room
    assert 'output["Warning Details"]' in draft_room
    assert 'output["Warning Groups"]' in june15
    assert 'output["Warning Details"]' in june15
    assert 'st.tabs(["Receipts", "Components", "Warnings"])' in draft_room
    assert '"warning_flags"' in draft_room
    assert '"warning_flags"' in june15


def test_phase5_warning_groups_cover_required_plain_english_buckets() -> None:
    combined = (
        DRAFT_ROOM_PAGE.read_text(encoding="utf-8")
        + "\n"
        + JUNE15_PAGE.read_text(encoding="utf-8")
    )

    for label in (
        "Data incomplete",
        "Low draft investment",
        "No-premium TE caution",
        "1QB QB caution",
        "Source-limited role data",
        "Manual review required",
    ):
        assert label in combined


def test_phase5_filter_controls_use_clean_language() -> None:
    draft_room = DRAFT_ROOM_PAGE.read_text(encoding="utf-8")

    assert '"Evidence Risk"' in draft_room
    assert '"Separation Type"' in draft_room
    assert '"Why It Is Unusual"' in draft_room
    assert '"Raw Feature Rows"' in draft_room
    assert '"Risk Level"' not in draft_room
    assert '"Weirdness Type"' not in draft_room


def test_phase5_no_final_action_directive_language_added() -> None:
    combined = (
        DRAFT_ROOM_PAGE.read_text(encoding="utf-8")
        + "\n"
        + JUNE15_PAGE.read_text(encoding="utf-8")
    ).lower()

    directive_phrases = (
        "make this trade",
        "draft this player",
        "cut this player",
        "drop this player",
    )
    assert not any(phrase in combined for phrase in directive_phrases)


def test_main_score_tables_expose_score_disclosure_fields() -> None:
    rankings = (ROOT / "app/pages/05_rankings.py").read_text(encoding="utf-8")
    draft_room = DRAFT_ROOM_PAGE.read_text(encoding="utf-8")

    for required in (
        '"source_path": "Score Source File"',
        '"source_column": "Score Column"',
        '"score_type": "Score Type"',
        '"model_version": "Model Version"',
        '"lineage_class": "Score Lineage"',
        '"confidence_cap": "Trust Cap"',
    ):
        assert required in rankings

    for required in (
        'output["Score Source File"] = frame.get("source_path", "")',
        'output["Score Column"] = frame.get("source_column", "")',
        'output["Score Lineage"] = frame.get("lineage_class", "")',
        'output["Formula Version"] = frame.get("formula_version", "")',
        'output["Trust Cap"] = frame.get("confidence_cap", "")',
        "<strong>Score source:</strong>",
    ):
        assert required in draft_room
