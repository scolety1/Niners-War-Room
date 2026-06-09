import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
ROSTER = ROOT / "docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md"


def _rows() -> list[dict[str, str]]:
    with CURRENT_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _score(row: dict[str, str]) -> float | None:
    value = row.get("checkpoint_review_score") or ""
    return float(value) if value else None


def _young_roster_subjects() -> list[str]:
    subjects: list[str] = []
    tokens = [
        "young",
        "elite_young",
        "rookie_current_bridge",
        "low_evidence",
        "emerging",
        "volatile",
        "roster_relevance",
        "suspicious_ranking",
    ]
    for line in ROSTER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| A"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 6 and cells[2] == "current_player":
            if any(token in cells[5] for token in tokens):
                subjects.append(cells[1])
    return subjects


def test_young_player_evidence_report_discloses_source_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "review_v4_current_player" in text
    assert "NAMED_PLAYER_AUDIT_ROSTER_20260605.md" in text
    assert "review_only_current_value_checkpoint" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "does not change young-player priors" in text
    assert "Do not change young-player priors" in text


def test_young_player_evidence_report_matches_scope_counts():
    text = REPORT.read_text(encoding="utf-8")
    rows = _rows()
    by_name = {row["player_name"]: row for row in rows}
    young_subjects = _young_roster_subjects()
    low_evidence_names = {
        row["player_name"]
        for row in rows
        if any(
            token in row["warning_flags"]
            for token in [
                "no_historical",
                "missing_stats_first",
                "shifted_header",
                "missing_vorp_anchor",
            ]
        )
    }
    selected = set(young_subjects) | low_evidence_names

    assert len(young_subjects) == 27
    assert len(selected) == 35
    assert sum((_score(by_name[name]) or -1) >= 50 for name in selected) == 9
    assert sum(by_name[name]["confidence_status"] == "capped_review_required" for name in selected) == 13
    assert sum(_score(by_name[name]) is None for name in selected) == 5
    assert "Named current-player young/volatile/low-evidence rows from audit roster: 27." in text
    assert "Additional exported low-evidence rows outside those roster categories: 8." in text
    assert "Total rows reviewed here: 35." in text
    assert "Rows with score at least 50: 9." in text
    assert "Rows with blank primary score: 5." in text


def test_young_player_evidence_report_includes_key_review_rows():
    text = REPORT.read_text(encoding="utf-8")

    for player in [
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "Bijan Robinson",
        "Jahmyr Gibbs",
        "Breece Hall",
        "Ashton Jeanty",
        "Luther Burden",
        "Kaleb Johnson",
        "Jeremiyah Love",
        "Carnell Tate",
        "Jordyn Tyson",
        "Fernando Mendoza",
        "Kenyon Sadiq",
    ]:
        assert player in text

    assert "high_score_young_review" in text
    assert "limited_history_or_stats_first_gap" in text
    assert "missing_primary_score_manual_review" in text
    assert "bottom_score_low_evidence_review" in text


def test_young_player_evidence_report_excludes_legacy_and_market_values():
    text = REPORT.read_text(encoding="utf-8")

    assert "legacy_active_pack" not in text
    assert "private_score" not in text
    assert "82.4" not in text
    assert "78.88" not in text
    assert "market, ADP, rankings, projections, consensus, startup" in text
