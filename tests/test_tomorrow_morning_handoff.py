from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs/model_v4/TOMORROW_MORNING_HANDOFF_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _handoff_text() -> str:
    return HANDOFF.read_text(encoding="utf-8")


def test_tomorrow_morning_handoff_summarizes_state_and_results() -> None:
    text = _handoff_text()

    required_phrases = [
        "Refinement tasks R01-R28 are complete.",
        "Direct stdlib refinement readback runner passed `121` assertions",
        "`py_compile` passed for all 27 refinement readback test files",
        "`No module named pytest`",
        "`No module named ruff`",
        "`1214 passed`",
        "`All checks passed!`",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_tomorrow_morning_handoff_points_to_key_artifacts() -> None:
    text = _handoff_text()

    required_files = [
        "USER_JUDGMENT_WORKSHEET_20260605.csv",
        "FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md",
        "SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md",
        "DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md",
        "MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md",
        "MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md",
    ]

    for file_name in required_files:
        assert file_name in text


def test_tomorrow_morning_handoff_names_required_judgment_rows() -> None:
    text = _handoff_text()

    required_rows = [
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
        "Josh Allen",
        "Patrick Mahomes",
        "Joe Burrow",
        "Jayden Daniels",
        "Trey McBride",
        "CeeDee Lamb",
        "Justin Jefferson",
        "Malik Nabers",
        "Daniel Sobkowicz",
    ]

    for row in required_rows:
        assert row in text


def test_tomorrow_morning_handoff_keeps_formula_work_blocked() -> None:
    text = _handoff_text()

    required_guardrails = [
        "Formula work remains blocked",
        "Do not tune formulas from this handoff.",
        "Do not change model weights",
        "Do not add ADP",
        "Do not mutate active rankings",
        "Do not turn review labels into final recommendations.",
        "not a final ranking",
    ]

    for guardrail in required_guardrails:
        assert guardrail in text


def test_refinement_queue_marks_r29_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r29_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R29 |")
    ]
    assert len(r29_lines) == 1
    r29 = r29_lines[0]

    assert "| Done |" in r29
    assert "TOMORROW_MORNING_HANDOFF_20260605.md" in r29
    assert "what changed, what passed" in r29
    assert "which rows require human judgment" in r29
