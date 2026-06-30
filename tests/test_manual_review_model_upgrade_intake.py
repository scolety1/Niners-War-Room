import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE_DIR = ROOT / "docs" / "hq" / "model_upgrade" / "manual_review_intake_20260630"
ISSUE_MATRIX = INTAKE_DIR / "manual_review_issue_matrix.csv"
SOURCE_GATE_MATRIX = INTAKE_DIR / "source_gate_needed_matrix.csv"

REQUIRED_ISSUE_COLUMNS = [
    "manual_review_id",
    "source_file",
    "source_section",
    "observation",
    "affected_page_or_system",
    "affected_player",
    "affected_player_id_if_known",
    "primary_type",
    "recommended_action",
    "why_it_matters",
    "safe_now",
    "blocked_reason",
    "data_needed",
    "source_gate_needed",
    "identity_gate_needed",
    "model_gate_needed",
    "rank_change_allowed",
    "display_only_allowed",
    "model_use_allowed",
    "training_allowed",
    "human_approval_required",
    "priority",
    "notes",
]

FORBIDDEN_SOURCE_FRAGMENTS = [
    "nwr_shared_data",
    "nwr_local_secrets",
    "local_exports",
    "raw_cache",
    "api_key",
    "secret",
    "gmail",
]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_paths() -> list[Path]:
    return sorted(INTAKE_DIR.glob("*.csv"))


def test_issue_matrix_required_columns_exist() -> None:
    with ISSUE_MATRIX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == REQUIRED_ISSUE_COLUMNS


def test_issue_matrix_has_review_items() -> None:
    rows = _rows(ISSUE_MATRIX)
    assert len(rows) >= 30
    assert {row["priority"] for row in rows} >= {"P0", "P1"}


def test_model_rank_flags_default_false() -> None:
    for row in _rows(ISSUE_MATRIX):
        assert row["rank_change_allowed"] == "false"
        assert row["model_use_allowed"] == "false"
        assert row["training_allowed"] == "false"


def test_blocked_items_cannot_have_model_use_allowed() -> None:
    for path in _csv_paths():
        for row in _rows(path):
            if row.get("recommended_action") == "BLOCKED_DO_NOT_USE" or row.get("blocked_item"):
                assert row.get("model_use_allowed") == "false"
                assert row.get("training_allowed") == "false"


def test_display_only_items_do_not_imply_model_input() -> None:
    for path in _csv_paths():
        for row in _rows(path):
            if row.get("display_only_allowed") == "true":
                assert row.get("model_use_allowed", "false") == "false"
                assert row.get("training_allowed", "false") == "false"
                assert row.get("rank_change_allowed", "false") == "false"


def test_source_gate_needed_rows_require_gate_field() -> None:
    for row in _rows(ISSUE_MATRIX):
        if row["recommended_action"] == "SOURCE_GATE_NEEDED":
            assert row["source_gate_needed"] == "true"
            assert row["data_needed"].strip()

    for row in _rows(SOURCE_GATE_MATRIX):
        assert row["gate_field"].strip()
        assert row["data_needed"].strip()
        assert row["model_use_allowed"] == "false"
        assert row["training_allowed"] == "false"


def test_no_forbidden_raw_or_secret_paths_are_tracked_sources() -> None:
    for artifact in INTAKE_DIR.rglob("*"):
        relative_path = artifact.relative_to(ROOT).as_posix().lower()
        assert not any(fragment in relative_path for fragment in FORBIDDEN_SOURCE_FRAGMENTS)

    for path in _csv_paths():
        for row in _rows(path):
            source = row.get("source_file", "").lower()
            assert source
            assert not source.startswith(("c:", "/", "\\"))
            assert not any(fragment in source for fragment in FORBIDDEN_SOURCE_FRAGMENTS)
