import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/VETERAN_AGE_WINDOW_AUDIT_20260605.md"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
ROSTER = ROOT / "docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md"


def _rows() -> list[dict[str, str]]:
    with CURRENT_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _current_roster_veterans() -> list[str]:
    subjects: list[str] = []
    for line in ROSTER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| A"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 6 or cells[2] != "current_player":
            continue
        category = cells[5]
        if any(
            token in category
            for token in ["aging", "elite_aging", "veteran", "legacy_leak_sentinel"]
        ):
            subjects.append(cells[1])
    return subjects


def test_veteran_age_window_report_discloses_source_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "review_v4_current_player" in text
    assert "NAMED_PLAYER_AUDIT_ROSTER_20260605.md" in text
    assert "review_only_current_value_checkpoint" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "does not\nchange veteran age curves" in text
    assert "Do not change veteran age curves" in text


def test_veteran_age_window_report_matches_roster_and_warning_counts():
    text = REPORT.read_text(encoding="utf-8")
    rows = _rows()
    roster_veterans = _current_roster_veterans()
    rb_age_rows = [row for row in rows if "rb_age_" in row["warning_flags"]]

    assert len(roster_veterans) == 15
    assert len(rb_age_rows) == 8
    assert "Named current-player veteran/aging rows from audit roster: 15." in text
    assert "Additional exported RB age-warning rows outside those roster categories: 3." in text
    assert "Total rows reviewed here: 18." in text
    assert "Exported RB age-warning rows reviewed here: 8." in text


def test_veteran_age_window_report_includes_key_review_rows():
    text = REPORT.read_text(encoding="utf-8")

    for player in [
        "Christian McCaffrey",
        "Jonathan Taylor",
        "Derrick Henry",
        "Saquon Barkley",
        "Josh Jacobs",
        "Mike Evans",
        "Cooper Kupp",
        "Tyreek Hill",
        "Keenan Allen",
        "Travis Kelce",
        "George Kittle",
        "Mark Andrews",
        "Darrell Henderson",
    ]:
        assert player in text

    assert "explicit_age_guardrail" in text
    assert "high_score_age_review" in text
    assert "low_score_veteran_review" in text


def test_veteran_age_window_report_does_not_use_legacy_or_market_values():
    text = REPORT.read_text(encoding="utf-8")

    assert "41.6097" in text
    assert "legacy active-pack value as primary value" in text
    assert "82.4" not in text
    assert "78.88" not in text
    assert "market, ADP, rankings, projections, consensus, startup" in text
