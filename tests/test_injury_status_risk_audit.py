import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/INJURY_STATUS_RISK_AUDIT_20260605.md"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)


def _rows() -> list[dict[str, str]]:
    with CURRENT_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_injury_status_report_discloses_source_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "review_v4_current_player" in text
    assert "NAMED_PLAYER_AUDIT_ROSTER_20260605.md" in text
    assert "review_only_current_value_checkpoint" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "does not change injury penalties" in text
    assert "Do not change injury/status penalties" in text


def test_injury_status_report_matches_exported_warning_counts():
    text = REPORT.read_text(encoding="utf-8")
    rows = _rows()
    team_identity_rows = [
        row
        for row in rows
        if any(
            token in row["warning_flags"]
            for token in ["team_mismatch", "historical_team", "identity_review"]
        )
    ]
    partial_join_rows = [
        row for row in rows if "partial_or_quarantined_join_cap" in row["warning_flags"]
    ]

    assert len(team_identity_rows) == 15
    assert len(partial_join_rows) == 15
    assert "Rows reviewed here: 30." in text
    assert "Rows with `capped_review_required`: 17." in text
    assert "Rows with team, historical-team, or identity-review warning text: 15." in text
    assert "Rows with `partial_or_quarantined_join_cap`: 15." in text


def test_injury_status_report_includes_key_risk_rows():
    text = REPORT.read_text(encoding="utf-8")

    for player in [
        "George Pickens",
        "Jaylen Waddle",
        "Kenneth Walker III",
        "Stefon Diggs",
        "Keenan Allen",
        "Tank Dell",
        "Hollywood Brown",
        "Cooper Kupp",
        "Amari Cooper",
        "Darrell Henderson",
        "Daniel Jones",
    ]:
        assert player in text

    assert "missing_or_mismatched_team" in text
    assert "historical_team_context" in text
    assert "identity_review_cap" in text
    assert "roster_category_status_prompt" in text


def test_injury_status_report_does_not_use_legacy_or_market_values():
    text = REPORT.read_text(encoding="utf-8")

    assert "41.6097" in text
    assert "legacy active-pack value as primary value" in text
    assert "82.4" not in text
    assert "78.88" not in text
    assert "market, ADP, rankings, projections, consensus, startup" in text
