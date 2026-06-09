from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _report_text() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_data_source_gap_triage_report_has_required_sections() -> None:
    text = _report_text()

    required_sections = [
        "Triage Buckets",
        "Current-Player Gaps",
        "Identity / Team Mismatch Gaps",
        "Rookie Source Gaps",
        "Output / Disclosure Gaps",
        "Legacy / Stale Lane Watchlist",
        "Fix-Before-Tuning Order",
        "Non-Goals",
    ]

    for section in required_sections:
        assert section in text


def test_data_source_gap_triage_report_covers_core_gap_patterns() -> None:
    text = _report_text()

    required_patterns = [
        "missing_rotowire_player_stats",
        "missing_stats_first_component_evidence",
        "missing_vorp_anchor",
        "no_historical_evidence_for_component",
        "shifted_header_expected_player_header_inferred",
        "team_mismatch_or_missing_model_team",
        "team_mismatch_or_historical_team",
        "identity_review_cap",
        "partial_or_quarantined_join_cap",
        "watchlist_data_incomplete",
        "current_college_team_mismatch_quarantined",
        "missing_prospect_or_college_evidence",
        "market_context_excluded_from_private_value",
        "source_limited_evidence_cap",
    ]

    for pattern in required_patterns:
        assert pattern in text


def test_data_source_gap_triage_report_names_sentinel_rows_and_surfaces() -> None:
    text = _report_text()

    required_subjects = [
        "Jeremiyah Love",
        "Carnell Tate",
        "Jordyn Tyson",
        "Fernando Mendoza",
        "Kenyon Sadiq",
        "George Pickens",
        "Jaylen Waddle",
        "Kenneth Walker III",
        "Keenan Allen",
        "82.4",
        "Darius Slayton",
        "78.88",
        "Daniel Sobkowicz",
        "2026 5.04",
        "Pick Decision comparison export",
        "External Asset Reviews canonical CSVs",
        "Decision Board warnings",
    ]

    for subject in required_subjects:
        assert subject in text


def test_data_source_gap_triage_report_preserves_review_only_guardrails() -> None:
    text = _report_text()

    required_guardrails = [
        "does not import external data",
        "write generated model outputs",
        "Do not tune formulas from this report.",
        "Do not import external data or mutate generated outputs.",
        "manual-only",
        "Fail closed",
        "comparison-only",
        "display-only",
        "Do not add ADP",
        "Do not turn review labels into final trade",
    ]

    for guardrail in required_guardrails:
        assert guardrail in text


def test_refinement_queue_marks_r24_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r24_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R24 |")
    ]
    assert len(r24_lines) == 1
    r24 = r24_lines[0]

    assert "| Done |" in r24
    assert "DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md" in r24
    assert "missing primary scores, identity/team mismatches, rookie evidence gaps, source-disclosure gaps, and stale compatibility lanes" in r24
