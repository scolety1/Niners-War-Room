from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _report_text() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_suspicious_ranking_triage_report_has_required_buckets() -> None:
    text = _report_text()

    required_buckets = [
        "Likely Data Issue / Source-Missing",
        "Source-Disclosure / Output Gap",
        "Formula Candidate / Football-Quality Candidate",
        "UI / Explanation Risk",
        "Human-Review-Only",
        "Tomorrow Review Order",
        "Non-Goals",
    ]

    for bucket in required_buckets:
        assert bucket in text


def test_suspicious_ranking_triage_report_cites_prior_reports() -> None:
    text = _report_text()

    required_sources = [
        "TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md",
        "RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md",
        "QB_1QB_DISCIPLINE_REPORT_20260605.md",
        "TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md",
        "VETERAN_AGE_WINDOW_AUDIT_20260605.md",
        "YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md",
        "INJURY_STATUS_RISK_AUDIT_20260605.md",
        "ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md",
        "ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md",
        "PICK_VALUE_LADDER_AUDIT_20260605.md",
        "PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md",
        "EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md",
        "DECISION_BOARD_COHERENCE_AUDIT_20260605.md",
        "NON_FORMULA_SANITY_FIXTURE_TEST_NOTES_20260605.md",
    ]

    for source in required_sources:
        assert source in text


def test_suspicious_ranking_triage_report_preserves_sentinels_and_review_subjects() -> None:
    text = _report_text()

    required_subjects = [
        "Trey McBride",
        "Josh Allen",
        "Jalen Hurts",
        "Patrick Mahomes",
        "Joe Burrow",
        "Jayden Daniels",
        "Keenan Allen",
        "82.4",
        "Darius Slayton",
        "78.88",
        "Daniel Sobkowicz",
        "2026 5.04",
        "Kaleb Johnson",
        "Luke McCaffrey",
        "Jeremiyah Love",
        "Carnell Tate",
        "Jordyn Tyson",
        "Fernando Mendoza",
        "Kenyon Sadiq",
        "CeeDee Lamb",
        "Justin Jefferson",
        "Garrett Wilson",
        "Malik Nabers",
        "Brian Thomas Jr.",
        "Marvin Harrison Jr.",
    ]

    for subject in required_subjects:
        assert subject in text


def test_suspicious_ranking_triage_report_keeps_formula_candidates_proposal_only() -> None:
    text = _report_text()

    required_guardrails = [
        "does not tune formulas",
        "proposal-only",
        "Do not patch formulas from this report.",
        "not a final recommendation",
        "does not mutate generated model outputs",
        "display-only",
        "manual-only",
        "fail closed",
        "blocked-use",
        "no final recommendations",
        "Do not tune formulas from this report.",
    ]

    for guardrail in required_guardrails:
        assert guardrail in text


def test_refinement_queue_marks_r23_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r23_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R23 |")
    ]
    assert len(r23_lines) == 1
    r23 = r23_lines[0]

    assert "| Done |" in r23
    assert "SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md" in r23
    assert "likely data, source-missing, formula-candidate, UI/explanation, and human-review-only buckets" in r23
