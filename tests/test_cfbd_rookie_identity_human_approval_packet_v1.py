import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "model_upgrade"
    / "cfbd_rookie_identity_human_approval_packet_20260630"
)
CANDIDATE_CSV = PACKET_DIR / "candidate_identity_review_v1.csv"
BLOCKED_CSV = PACKET_DIR / "blocked_needs_more_info_v1.csv"
TEMPLATE_CSV = PACKET_DIR / "approval_template_v1.csv"

ALLOWED_DECISIONS = {
    "APPROVE_REVIEW_ONLY",
    "KEEP_BLOCKED",
    "NEEDS_MORE_INFO",
    "REJECT_WRONG_PLAYER",
}

REQUIRED_CANDIDATE_COLUMNS = [
    "approval_packet_id",
    "source_row_family",
    "player_name",
    "position",
    "school_or_team",
    "draft_class_year_if_known",
    "candidate_cfbd_identifier",
    "candidate_cfbd_name",
    "candidate_cfbd_position",
    "candidate_cfbd_team",
    "cfbd_years",
    "matched_nwr_identifier",
    "matched_sleeper_identifier",
    "nfl_team_if_available",
    "evidence_fields_available",
    "match_status",
    "match_confidence",
    "ambiguity_type",
    "ambiguity_reason",
    "recommended_review_decision",
    "approved_by_human",
    "model_use_allowed",
    "training_allowed",
    "review_only",
    "explanation",
    "source_citation_notes",
    "human_decision",
    "human_reviewer",
    "human_review_date",
    "human_notes",
]

ALLOWED_CHANGED_PREFIXES = (
    "docs/hq/model_upgrade/cfbd_rookie_identity_human_approval_packet_20260630/",
    "tests/test_cfbd_rookie_identity_human_approval_packet_v1.py",
)

PROTECTED_PATH_FRAGMENTS = (
    "final_board_rank",
    "FINAL_DRAFT_BOARD",
    "latest_candidate",
    "latest_approved",
    "draft_runtime",
    "draft_day_runtime",
    "live_draft",
    "mock_draft",
    "app/pages",
    "src/",
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_packet_files_exist() -> None:
    expected = {
        "README.md",
        "candidate_identity_review_v1.csv",
        "blocked_needs_more_info_v1.csv",
        "approval_template_v1.csv",
        "SOURCE_POLICY_NOTES.md",
        "REVIEWER_INSTRUCTIONS.md",
        "GUARDRAIL_PROOF.md",
    }
    assert expected <= {path.name for path in PACKET_DIR.iterdir()}


def test_candidate_required_columns_and_decisions() -> None:
    with CANDIDATE_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == REQUIRED_CANDIDATE_COLUMNS
        rows = list(reader)

    assert len(rows) == 213
    assert {row["recommended_review_decision"] for row in rows} <= ALLOWED_DECISIONS
    assert {row["recommended_review_decision"] for row in rows} == ALLOWED_DECISIONS


def test_all_csv_outputs_are_review_only_with_closed_model_flags() -> None:
    for path in (CANDIDATE_CSV, BLOCKED_CSV, TEMPLATE_CSV):
        for row in _rows(path):
            assert row["approved_by_human"] == "false"
            assert row["model_use_allowed"] == "false"
            assert row["training_allowed"] == "false"
            assert row["review_only"] == "true"


def test_blocked_rows_are_not_approve_review_only() -> None:
    rows = _rows(BLOCKED_CSV)
    assert rows
    for row in rows:
        assert row["recommended_review_decision"] in {
            "KEEP_BLOCKED",
            "NEEDS_MORE_INFO",
            "REJECT_WRONG_PLAYER",
        }


def test_approval_template_keeps_human_fields_blank_and_decisions_restricted() -> None:
    for row in _rows(TEMPLATE_CSV):
        assert row["recommended_review_decision"] in ALLOWED_DECISIONS
        assert row["allowed_human_decisions"] == (
            "APPROVE_REVIEW_ONLY|KEEP_BLOCKED|NEEDS_MORE_INFO|REJECT_WRONG_PLAYER"
        )
        assert row["human_decision"] == ""
        assert row["human_reviewer"] == ""
        assert row["human_review_date"] == ""


def test_no_protected_paths_are_changed_in_worktree() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        path = line[3:].replace("\\", "/")
        assert path.startswith(ALLOWED_CHANGED_PREFIXES)
        assert not any(fragment in path for fragment in PROTECTED_PATH_FRAGMENTS)


def test_docs_state_no_cfbd_model_or_training_promotion() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in PACKET_DIR.glob("*.md"))
    assert "CFBD is not model input" in text
    assert "CFBD is not training truth" in text
    assert "No rookie probabilities were created" in text
    assert "No player values were created" in text


def test_no_nan_placeholder_leaks() -> None:
    for path in (CANDIDATE_CSV, BLOCKED_CSV, TEMPLATE_CSV):
        text = path.read_text(encoding="utf-8").lower()
        assert ",nan," not in text
        assert "\nnan," not in text
        assert ",nan\n" not in text
