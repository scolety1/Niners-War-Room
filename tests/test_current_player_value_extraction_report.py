import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md"
ROSTER = ROOT / "docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)


def _current_roster_subjects() -> list[str]:
    subjects: list[str] = []
    for line in ROSTER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| A"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[2] == "current_player":
            subjects.append(cells[1])
    return subjects


def _current_value_rows() -> dict[str, dict[str, str]]:
    with CURRENT_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return {
            row["player_name"]: row
            for row in csv.DictReader(handle)
        }


def test_current_player_extraction_report_discloses_source_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert (
        "local_exports/model_v4/current_value/latest/"
        "current_player_value_review_rows.csv"
    ) in text
    assert "checkpoint_review_score" in text
    assert "review_only_current_value_checkpoint" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "does not tune formulas" in text
    assert "does not expose or use the legacy active-pack `private_score`" in text


def test_current_player_extraction_report_covers_all_current_roster_subjects():
    text = REPORT.read_text(encoding="utf-8")
    current_rows = _current_value_rows()
    subjects = _current_roster_subjects()

    assert len(subjects) == 68
    assert all(subject in current_rows for subject in subjects)
    assert all(f"| {subject} |" in text for subject in subjects)
    assert "Current-player roster subjects found in the checkpoint: 68." in text
    assert "Missing current-player roster subjects: none." in text


def test_current_player_extraction_report_matches_key_checkpoint_values():
    text = REPORT.read_text(encoding="utf-8")
    current_rows = _current_value_rows()

    for player in [
        "Puka Nacua",
        "Christian McCaffrey",
        "Keenan Allen",
        "Kaleb Johnson",
        "Trey McBride",
    ]:
        score = float(current_rows[player]["checkpoint_review_score"])
        assert f"| {player} |" in text
        assert f"{score:.4f}" in text

    assert "82.4" not in text
    assert "78.88" not in text


def test_current_player_extraction_report_keeps_non_current_subjects_out_of_table():
    text = REPORT.read_text(encoding="utf-8")

    assert "Non-current roster subjects intentionally excluded from this report: 12" in text
    assert "- A69 Jeremiyah Love" in text
    assert "- A76 2026 1.03" in text
    assert "- A80 2026 5.04" in text
