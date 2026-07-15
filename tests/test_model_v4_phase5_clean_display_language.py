from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DRAFT_ROOM_PAGE = ROOT / "app/pages/06_draft_board.py"
LEGACY_DECISION_BOARD_PAGE = ROOT / "app/pages/08_june15_review.py"
CURRENT_RANKINGS_PAGE = ROOT / "app/pages/20_final_board_v1.py"
DECISION_TRUST_SERVICE = ROOT / "src/services/decision_trust_strip_service.py"


def test_phase5_display_label_mapping_is_present() -> None:
    draft_room = LEGACY_DRAFT_ROOM_PAGE.read_text(encoding="utf-8")
    june15 = LEGACY_DECISION_BOARD_PAGE.read_text(encoding="utf-8")
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
    decision_board = LEGACY_DECISION_BOARD_PAGE.read_text(encoding="utf-8")

    assert 'output["Warning Groups"]' in decision_board
    assert 'output["Warning Details"]' in decision_board
    assert 'frame.get("confidence_or_risk_warnings", "")' in decision_board
    assert 'frame.get("warning_flags", "")' in decision_board
    assert '"warning_flags"' in decision_board


def test_phase5_warning_groups_cover_required_plain_english_buckets() -> None:
    combined = (
        LEGACY_DRAFT_ROOM_PAGE.read_text(encoding="utf-8")
        + "\n"
        + LEGACY_DECISION_BOARD_PAGE.read_text(encoding="utf-8")
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
    rankings = CURRENT_RANKINGS_PAGE.read_text(encoding="utf-8")

    for label in (
        '"Dynasty Review"',
        '"Market Context"',
        '"Data Review"',
        '"Advanced filters"',
        '"Review needed"',
    ):
        assert label in rankings
    assert '"Risk Level"' not in rankings
    assert '"Weirdness Type"' not in rankings


def test_phase5_no_final_action_directive_language_added() -> None:
    combined = (
        LEGACY_DRAFT_ROOM_PAGE.read_text(encoding="utf-8")
        + "\n"
        + LEGACY_DECISION_BOARD_PAGE.read_text(encoding="utf-8")
    ).lower()

    directive_phrases = (
        "make this trade",
        "draft this player",
        "cut this player",
        "drop this player",
    )
    assert not any(phrase in combined for phrase in directive_phrases)


def test_main_score_tables_expose_score_disclosure_fields() -> None:
    rankings = CURRENT_RANKINGS_PAGE.read_text(encoding="utf-8")
    trust_service = DECISION_TRUST_SERVICE.read_text(encoding="utf-8")

    for required in (
        "build_rankings_dataset_trust_strip(",
        'heading="Visible board evidence trust"',
        "source_path, source_column",
        "model_version, score_type, score_as_of_date, confidence_cap",
    ):
        assert required in rankings

    for required in (
        '"evidence_source": "Evidence / source"',
        '"as_of_freshness": "As of / freshness"',
        '"identity_join": "Identity / join"',
        '"missingness_completeness": "Completeness"',
        '"material_caveats": "Material caveats"',
        '"receipt_details": "Receipts / details"',
    ):
        assert required in trust_service
