from __future__ import annotations

from pathlib import Path

PACKAGE = Path("docs/model_v4/MODEL_V4_REPAIR_EXTERNAL_AUDIT_PACKAGE_20260530.md")
PROMPT = Path("docs/model_v4/MODEL_V4_REPAIR_PRO_AGENT_PROMPT_20260530.md")
CHECKLIST = Path("docs/model_v4/MODEL_V4_REPAIR_ACCEPTANCE_CHECKLIST_20260530.md")


def test_repair_external_audit_package_files_exist_and_link_together() -> None:
    assert PACKAGE.exists()
    assert PROMPT.exists()
    assert CHECKLIST.exists()

    package = PACKAGE.read_text(encoding="utf-8")
    prompt = PROMPT.read_text(encoding="utf-8")

    assert str(PROMPT).replace("\\", "/") in package
    assert str(CHECKLIST).replace("\\", "/") in package
    assert str(PACKAGE).replace("\\", "/") in prompt
    assert str(CHECKLIST).replace("\\", "/") in prompt


def test_repair_external_audit_package_names_required_sentinels() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (PACKAGE, PROMPT, CHECKLIST)
    )

    for required in (
        "tests/test_model_v4_final_sentinel_gate.py",
        "Keenan Allen",
        "82.4",
        "Darius Slayton",
        "78.88",
        "checkpoint_review_score",
        "legacy_active_pack_score",
        "market_display_only",
        "source_path",
        "source_column",
        "lineage_class",
        "manual_decision_required",
        "Review-only surface",
        "repair_gate_passed_for_review_only_source_routing",
        "needs_repair_before_formula_tuning",
    ):
        assert required in combined


def test_repair_external_audit_prompt_preserves_no_tuning_guardrails() -> None:
    prompt = PROMPT.read_text(encoding="utf-8")

    for required in (
        "Do not tune formulas",
        "Do not add ADP",
        "Do not turn review labels into final",
        "Do not mutate active rankings",
        "Suggested Commands",
        "Return Format",
    ):
        assert required in prompt
