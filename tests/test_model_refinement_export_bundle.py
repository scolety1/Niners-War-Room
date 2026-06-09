import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/model_v4/MODEL_REFINEMENT_EXPORT_BUNDLE_MANIFEST_20260605.md"
ZIP_PATH = ROOT / "docs/model_v4/MODEL_REFINEMENT_EXPORT_BUNDLE_20260605.zip"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _manifest_text() -> str:
    return MANIFEST.read_text(encoding="utf-8")


def _zip_names() -> set[str]:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        return {Path(name).name for name in archive.namelist()}


def test_export_bundle_manifest_lists_required_artifacts() -> None:
    text = _manifest_text()

    required_artifacts = [
        "MODEL_REFINEMENT_EXPORT_BUNDLE_20260605.zip",
        "POST_AUDIT_READINESS_HANDOFF_20260531.md",
        "MODEL_REFINEMENT_QUEUE_20260605.md",
        "TOMORROW_MORNING_HANDOFF_20260605.md",
        "FINAL_OVERNIGHT_READINESS_RERUN_20260605.md",
        "MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md",
        "MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md",
        "USER_JUDGMENT_WORKSHEET_20260605.csv",
        "FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md",
        "DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md",
        "SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md",
    ]

    for artifact in required_artifacts:
        assert artifact in text


def test_export_bundle_manifest_preserves_guardrails_and_exclusions() -> None:
    text = _manifest_text()

    required_phrases = [
        "not a formula tuning packet",
        "not a generated model output refresh",
        "not a recommendation artifact",
        "Source code implementation files.",
        "Active data packs.",
        "Generated model output CSVs outside the human worksheet.",
        "Git staging or commits.",
        "Do not tune formulas from this bundle.",
        "Do not mutate active rankings",
        "Do not turn review labels into final recommendations.",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_export_bundle_zip_contains_required_files() -> None:
    assert ZIP_PATH.exists()
    names = _zip_names()

    required_names = [
        "MODEL_REFINEMENT_EXPORT_BUNDLE_MANIFEST_20260605.md",
        "POST_AUDIT_READINESS_HANDOFF_20260531.md",
        "POST_AUDIT_CLEANUP_QUEUE_20260531.md",
        "MODEL_REFINEMENT_QUEUE_20260605.md",
        "TOMORROW_MORNING_HANDOFF_20260605.md",
        "FINAL_OVERNIGHT_READINESS_RERUN_20260605.md",
        "MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md",
        "MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md",
        "USER_JUDGMENT_WORKSHEET_20260605.md",
        "USER_JUDGMENT_WORKSHEET_20260605.csv",
        "FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md",
        "DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md",
        "SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md",
        "test_model_refinement_export_bundle.py",
    ]

    for name in required_names:
        assert name in names


def test_export_bundle_zip_excludes_source_code_and_generated_outputs() -> None:
    names = _zip_names()

    assert not any(name.endswith(".py") and name.startswith("player_board") for name in names)
    assert "current_player_value_review_rows.csv" not in names
    assert "dynasty_asset_value_review_rows.csv" not in names
    assert "pick_decision_rows.csv" not in names


def test_refinement_queue_marks_r30_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r30_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R30 |")
    ]
    assert len(r30_lines) == 1
    r30 = r30_lines[0]

    assert "| Done |" in r30
    assert "MODEL_REFINEMENT_EXPORT_BUNDLE_20260605.zip" in r30
    assert "MODEL_REFINEMENT_EXPORT_BUNDLE_MANIFEST_20260605.md" in r30
    assert "no source code staging or commits" in r30
