import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/DECISION_BOARD_COHERENCE_AUDIT_20260605.md"
BOARD_ROOT = ROOT / "local_exports/model_v4/june15_decision_board/latest"
BOARD_ROWS = BOARD_ROOT / "june15_decision_board_review_rows.csv"
RECEIPTS = BOARD_ROOT / "june15_decision_board_receipts.csv"
COMPONENTS = BOARD_ROOT / "june15_decision_board_component_rows.csv"
WARNINGS = BOARD_ROOT / "june15_decision_board_warnings.csv"
SUMMARY = BOARD_ROOT / "june15_decision_board_summary.csv"
PICK_INVENTORY = (
    ROOT / "local_exports/model_v4/pick_trade_defer/latest/"
    "niners_pick_inventory_review_rows.csv"
)
PRESSURE_ROWS = (
    ROOT / "local_exports/model_v4/decision_pressure/latest/"
    "cut_keep_pressure_review_rows.csv"
)
ROOKIE_CANDIDATES = (
    ROOT / "local_exports/model_v4/rookie_draft_review/latest/"
    "rookie_pick_candidate_review_rows.csv"
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def test_decision_board_report_discloses_sources_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "june15_decision_board_review_rows.csv" in text
    assert "june15_decision_board_receipts.csv" in text
    assert "june15_decision_board_component_rows.csv" in text
    assert "june15_decision_board_warnings.csv" in text
    assert "niners_pick_inventory_review_rows.csv" in text
    assert "cut_keep_pressure_review_rows.csv" in text
    assert "rookie_pick_candidate_review_rows.csv" in text
    assert "Do not mutate Decision Board outputs" in text


def test_decision_board_report_matches_board_counts_and_blocked_use():
    text = REPORT.read_text(encoding="utf-8")
    board_rows = _rows(BOARD_ROWS)
    receipts = _rows(RECEIPTS)
    components = _rows(COMPONENTS)
    warnings = _rows(WARNINGS)
    summary = {row["summary_key"]: row["summary_value"] for row in _rows(SUMMARY)}
    area_counts = Counter(row["decision_area"] for row in board_rows)

    assert len(board_rows) == 105
    assert len(receipts) == 105
    assert len(components) == 315
    assert len(warnings) == 54
    assert area_counts["rookie_pick_window_context"] == 76
    assert area_counts["roster_pressure_trade_context"] == 24
    assert area_counts["pick_trade_defer_context"] == 5
    assert {row["allowed_use"] for row in board_rows} == {
        "review_only_june15_decision_context_not_final_action"
    }
    assert {row["blocked_use"] for row in board_rows} == {
        "do_not_use_as_final_cut_keep_trade_or_draft_recommendation"
    }
    assert summary["final_recommendations_created"] == "False"
    assert summary["war_board_changed"] == "False"
    assert summary["my_team_changed"] == "False"
    assert "Decision rows: 105." in text
    assert "`rookie_pick_window_context`: 76." in text


def test_decision_board_report_matches_receipt_and_component_shape():
    board_rows = _rows(BOARD_ROWS)
    receipts = _by_key(_rows(RECEIPTS), "decision_key")
    components_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _rows(COMPONENTS):
        components_by_key[row["decision_key"]].append(row)

    assert set(receipts) == {row["decision_key"] for row in board_rows}
    for row in board_rows:
        component_names = {
            component["component_name"]
            for component in components_by_key[row["decision_key"]]
        }
        assert component_names == {
            "primary_review_band",
            "source_review_score",
            "review_priority",
        }


def test_decision_board_report_traces_sample_rows_to_sources():
    board = _by_key(_rows(BOARD_ROWS), "decision_key")
    picks = _by_key(_rows(PICK_INVENTORY), "pick_label")
    pressure = _by_key(_rows(PRESSURE_ROWS), "player_name")
    rookie_candidates = {
        (row["pick_label"], row["prospect_name"]): row for row in _rows(ROOKIE_CANDIDATES)
    }

    pick_103 = board["june15:pick:niners_pick:2026:1.03"]
    pick_504 = board["june15:pick:niners_pick:2026:5.04"]
    kaleb = board["june15:roster:niners:kalebjohnson:RB"]
    luke = board["june15:roster:niners:lukemccaffrey:WR"]
    love = board[
        "june15:rookie:niners_pick:2026:1.03:prospect:2026:jeremiyahlove:RB"
    ]
    makai = board[
        "june15:rookie:niners_pick:2026:1.03:prospect:2026:makailemon:WR"
    ]
    lane = board[
        "june15:rookie:niners_pick:2026:2.08:prospect:2026:jakobilane:WR"
    ]

    assert pick_103["source_review_score"] == picks["2026 1.03"][
        "pick_value_review_score"
    ]
    assert pick_504["source_review_score"] == picks["2026 5.04"][
        "pick_value_review_score"
    ]
    assert pick_504["primary_review_band"] == "pick_baseline_missing_review"
    assert kaleb["source_review_score"] == pressure["Kaleb Johnson"]["pressure_score"]
    assert luke["source_review_score"] == pressure["Luke McCaffrey"]["pressure_score"]
    assert love["source_review_score"] == rookie_candidates[
        ("2026 1.03", "Jeremiyah Love")
    ]["league_format_adjusted_score"]
    assert makai["source_review_score"] == rookie_candidates[
        ("2026 1.03", "Makai Lemon")
    ]["league_format_adjusted_score"]
    assert lane["source_review_score"] == rookie_candidates[
        ("2026 2.08", "Ja'Kobi Lane")
    ]["league_format_adjusted_score"]


def test_decision_board_report_records_sample_rows_and_warning_status():
    text = REPORT.read_text(encoding="utf-8")
    warnings_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _rows(WARNINGS):
        warnings_by_key[row["decision_key"]].append(row)

    assert "Kaleb Johnson" in text
    assert "Luke McCaffrey" in text
    assert "Jeremiyah Love" in text
    assert "Makai Lemon" in text
    assert "Ja'Kobi Lane" in text
    assert "2026 5.04" in text
    assert warnings_by_key["june15:pick:niners_pick:2026:5.04"][0][
        "warning_code"
    ] == "pick_baseline_missing_review"
    assert warnings_by_key["june15:roster:niners:kalebjohnson:RB"][0][
        "warning_code"
    ] == "roster_pressure_line_review"
    assert "Warning rows are not one-for-one with board rows." in text
