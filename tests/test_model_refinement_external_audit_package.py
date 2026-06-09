from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/model_v4/MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md"
PROMPT = ROOT / "docs/model_v4/MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _package_text() -> str:
    return PACKAGE.read_text(encoding="utf-8")


def _prompt_text() -> str:
    return PROMPT.read_text(encoding="utf-8")


def test_external_audit_package_lists_required_context_and_reports() -> None:
    text = _package_text()

    required_files = [
        "POST_AUDIT_READINESS_HANDOFF_20260531.md",
        "POST_AUDIT_CLEANUP_QUEUE_20260531.md",
        "MODEL_REFINEMENT_QUEUE_20260605.md",
        "MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md",
        "REFINEMENT_EVIDENCE_MAP_20260605.md",
        "CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md",
        "SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md",
        "DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md",
        "FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md",
        "PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md",
        "DRAFT_ROOM_UX_SMOKE_CHECKLIST_20260605.md",
        "EXTERNAL_ASSET_DECISION_BOARD_UX_SMOKE_CHECKLIST_20260605.md",
    ]

    for file_name in required_files:
        assert file_name in text


def test_external_audit_package_preserves_sentinels_and_candidate_areas() -> None:
    text = _package_text()

    required_items = [
        "Keenan Allen",
        "82.4",
        "Darius Slayton",
        "78.88",
        "Jeremiyah Love",
        "Carnell Tate",
        "Jordyn Tyson",
        "Fernando Mendoza",
        "Kenyon Sadiq",
        "2026 5.04",
        "FC01: No-premium TE ceiling clarity",
        "FC02: 1QB spread and cap clarity",
        "FC03: RB/WR cross-position balance",
        "FC04: Veteran age/status confidence shape",
        "FC05: Young-player evidence sensitivity",
        "FC06: Rookie source-limited prior handling",
        "FC07: Pick-neighborhood explanation and comparison shape",
    ]

    for item in required_items:
        assert item in text


def test_external_audit_package_has_verdict_options_and_guardrails() -> None:
    text = _package_text()

    required_phrases = [
        "refinement_packet_ready_for_human_review_only",
        "needs_repair_before_human_review",
        "needs_source_cleanup_before_formula_tuning",
        "formula_tuning_not_ready",
        "does not prove football accuracy",
        "does not authorize money decisions",
        "does not tune formulas",
        "display-only",
        "proposal-only",
        "Do not tune these during the audit.",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_external_audit_prompt_is_copy_ready_and_review_only() -> None:
    text = _prompt_text()

    required_phrases = [
        "Copy this prompt",
        "External audit only. Review-only refinement prep.",
        "Do not tune formulas.",
        "Do not change model weights",
        "Do not add ADP",
        "Do not turn review labels into final",
        "Do not mutate active rankings",
        "Return exactly one top-level verdict",
        "formula work should remain blocked",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_refinement_queue_marks_r26_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r26_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R26 |")
    ]
    assert len(r26_lines) == 1
    r26 = r26_lines[0]

    assert "| Done |" in r26
    assert "MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md" in r26
    assert "MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md" in r26
    assert "ChatGPT Pro" in r26
