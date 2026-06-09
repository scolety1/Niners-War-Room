from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/FINAL_OVERNIGHT_READINESS_RERUN_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _report_text() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_final_overnight_readiness_rerun_records_blocked_pytest_and_ruff() -> None:
    text = _report_text()

    required_phrases = [
        "No module named pytest",
        "No module named ruff",
        "Full repository pytest command attempted",
        "Full repository lint command attempted",
        "runtime does not currently expose those modules",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_final_overnight_readiness_rerun_records_fallback_success() -> None:
    text = _report_text()

    required_phrases = [
        "DIRECT_READBACK_PASSED=121",
        "DIRECT_READBACK_FAILED=0",
        "py_compile passed for all 27 refinement readback test files",
        "tests/test_user_judgment_worksheet.py",
        "tests/test_model_refinement_external_audit_package.py",
        "tests/test_non_formula_sanity_fixtures.py",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_final_overnight_readiness_rerun_preserves_guardrails() -> None:
    text = _report_text()

    required_guardrails = [
        "No formula tuning.",
        "No model weights",
        "No ADP",
        "No active rankings",
        "No review labels were turned into final recommendations.",
        "does not prove football accuracy",
        "does not authorize money decisions",
    ]

    for guardrail in required_guardrails:
        assert guardrail in text


def test_refinement_queue_marks_r28_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r28_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R28 |")
    ]
    assert len(r28_lines) == 1
    r28 = r28_lines[0]

    assert "| Done |" in r28
    assert "FINAL_OVERNIGHT_READINESS_RERUN_20260605.md" in r28
    assert "direct readback runner passed 121 assertions" in r28
    assert "pytest/ruff unavailable" in r28
