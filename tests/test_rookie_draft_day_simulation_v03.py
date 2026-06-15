from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "rookie_framework"
    / "build_rookie_draft_day_simulation_v03.py"
)
spec = importlib.util.spec_from_file_location("build_rookie_draft_day_simulation_v03", SCRIPT_PATH)
simulation = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(simulation)


FIELDS = [
    "analyzer_rank",
    "analyzer_group",
    "player_id",
    "player",
    "position",
    "school",
    "pick_zone",
    "production_ready_status",
    "tag_summary",
    "source_confidence",
    "warnings",
    "blockers",
    "evidence_summary",
    "remaining_gaps",
    "fit_1_03",
    "fit_1_04",
    "fit_2_04",
    "fit_2_08",
    "fit_5_04",
    "best_pick_fit",
    "trade_down_signal",
    "emergency_stop_signal",
    "draft_only_if",
    "do_not_draft_if",
    "why_ranked_here",
    "why_not_higher",
    "why_not_lower",
    "app_ready",
    "production_score_created",
    "probabilities_created",
    "analyzer_notes",
]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def make_fixture(root: Path) -> Path:
    analyzer_root = root / "local_exports" / "model_v4" / "rookie_framework_v02" / "rookie_analyzer_v03"
    rows = [
        {
            "analyzer_rank": "1",
            "analyzer_group": "premium_review",
            "player_id": "p1",
            "player": "Alpha Back",
            "position": "RB",
            "school": "State",
            "pick_zone": "1.04",
            "production_ready_status": "rankable_with_warning",
            "tag_summary": "RB_PREMIUM_THREE_DOWN",
            "source_confidence": "high",
            "warnings": "pass protection warning",
            "blockers": "none",
            "evidence_summary": "official final stats",
            "remaining_gaps": "goal_line_touch_share",
            "fit_1_03": "trade_down_or_manual_review_only_no_player_cleared",
            "fit_1_04": "premium_fit_with_visible_warnings",
            "fit_2_04": "premium_slip_review_with_visible_warnings",
            "fit_2_08": "premium_slip_review_with_visible_warnings",
            "fit_5_04": "falling_player_manual_review",
            "best_pick_fit": "1.04_premium_warning_visible",
            "trade_down_signal": "yes_1_03_and_premium_bar_not_cleared",
            "emergency_stop_signal": "no",
            "draft_only_if": "warnings accepted",
            "do_not_draft_if": "warnings hidden",
            "why_ranked_here": "fixture",
            "why_not_higher": "1.03 remains empty",
            "why_not_lower": "warnings visible",
            "app_ready": "no",
            "production_score_created": "no",
            "probabilities_created": "no",
            "analyzer_notes": "fixture",
        },
        {
            "analyzer_rank": "2",
            "analyzer_group": "round2_review",
            "player_id": "p2",
            "player": "Beta Wideout",
            "position": "WR",
            "school": "Tech",
            "pick_zone": "2.08",
            "production_ready_status": "rankable_with_warning",
            "tag_summary": "WR_ROUTE",
            "source_confidence": "medium",
            "warnings": "route warning",
            "blockers": "none",
            "evidence_summary": "manual charting context",
            "remaining_gaps": "press_success",
            "fit_1_03": "trade_down_or_manual_review_only_no_player_cleared",
            "fit_1_04": "not_a_1_04_fit",
            "fit_2_04": "round2_wr_fit_with_visible_warnings",
            "fit_2_08": "round2_wr_fit_with_visible_warnings",
            "fit_5_04": "falling_player_manual_review",
            "best_pick_fit": "round2_wr_evidence_profile",
            "trade_down_signal": "no",
            "emergency_stop_signal": "no",
            "draft_only_if": "role clear",
            "do_not_draft_if": "role unclear",
            "why_ranked_here": "fixture",
            "why_not_higher": "warnings",
            "why_not_lower": "role",
            "app_ready": "no",
            "production_score_created": "no",
            "probabilities_created": "no",
            "analyzer_notes": "fixture",
        },
        {
            "analyzer_rank": "3",
            "analyzer_group": "blocked",
            "player_id": "p3",
            "player": "Gamma Tight End",
            "position": "TE",
            "school": "Metro",
            "pick_zone": "5.04",
            "production_ready_status": "blocked",
            "tag_summary": "TE_REPLACEABLE",
            "source_confidence": "low",
            "warnings": "low_source_confidence",
            "blockers": "hard cap",
            "evidence_summary": "unavailable",
            "remaining_gaps": "target_path",
            "fit_1_03": "trade_down_or_manual_review_only_no_player_cleared",
            "fit_1_04": "do_not_use_blocked",
            "fit_2_04": "do_not_use_blocked",
            "fit_2_08": "do_not_use_blocked",
            "fit_5_04": "do_not_use_blocked",
            "best_pick_fit": "5.04_not_actionable",
            "trade_down_signal": "yes_if_only_blocked_or_unavailable_options_remain",
            "emergency_stop_signal": "yes_blocked_or_unavailable",
            "draft_only_if": "blocker removed",
            "do_not_draft_if": "blocked",
            "why_ranked_here": "fixture",
            "why_not_higher": "blocked",
            "why_not_lower": "blocked",
            "app_ready": "no",
            "production_score_created": "no",
            "probabilities_created": "no",
            "analyzer_notes": "fixture",
        },
    ]
    write_csv(analyzer_root / "rookie_analyzer_v03.csv", rows, FIELDS)
    (analyzer_root / "rookie_analyzer_readme.md").write_text("# fixture\n", encoding="utf-8")
    return analyzer_root


def test_simulation_outputs_are_local_only_and_not_app_ready(tmp_path: Path) -> None:
    analyzer_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    simulation.build_exports(analyzer_root, out, strict=True)
    rows = read_csv(out / "rookie_draft_day_simulation_v03.csv")
    assert rows
    assert {row["simulation_only"] for row in rows} == {"yes"}
    assert {row["app_ready"] for row in rows} == {"no"}
    assert {row["production_score_created"] for row in rows} == {"no"}
    assert {row["probabilities_created"] for row in rows} == {"no"}


def test_1_03_remains_no_player_cleared(tmp_path: Path) -> None:
    analyzer_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    simulation.build_exports(analyzer_root, out, strict=True)
    rows = [row for row in read_csv(out / "rookie_draft_day_simulation_v03.csv") if row["pick"] == "1.03"]
    assert len(rows) == 1
    assert rows[0]["player"] == "NO_PLAYER_CLEARED"
    assert rows[0]["simulation_action"] == "trade_down_or_manual_review"


def test_all_known_pick_cards_are_written(tmp_path: Path) -> None:
    analyzer_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    simulation.build_exports(analyzer_root, out, strict=True)
    cards = read_csv(out / "rookie_draft_day_pick_cards_v03.csv")
    assert [row["pick"] for row in cards] == ["1.03", "1.04", "2.04", "2.08", "5.04"]


def test_strict_mode_rejects_prohibited_private_input_columns(tmp_path: Path) -> None:
    analyzer_root = make_fixture(tmp_path)
    path = analyzer_root / "rookie_analyzer_v03.csv"
    rows = read_csv(path)
    for row in rows:
        row["private_score"] = "99"
    write_csv(path, rows, list(rows[0].keys()))
    try:
        simulation.build_exports(analyzer_root, tmp_path / "out", strict=True)
    except simulation.DraftDaySimulationError as exc:
        assert "Prohibited private input columns" in str(exc)
    else:
        raise AssertionError("strict mode should reject private_score input")


def test_strict_mode_rejects_data_paths(tmp_path: Path) -> None:
    analyzer_root = make_fixture(tmp_path)
    try:
        simulation.build_exports(analyzer_root, tmp_path / "data" / "out", strict=True)
    except simulation.DraftDaySimulationError as exc:
        assert "data/" in str(exc)
    else:
        raise AssertionError("simulation should reject data/ output paths")


def test_no_streamlit_outcome_or_veteran_imports_are_required() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8").lower()
    assert "import streamlit" not in source
    assert "from streamlit" not in source
    assert "import outcome" not in source
    assert "from outcome" not in source
    assert "import veteran" not in source
    assert "from veteran" not in source


if __name__ == "__main__":
    tests = [
        test_simulation_outputs_are_local_only_and_not_app_ready,
        test_1_03_remains_no_player_cleared,
        test_all_known_pick_cards_are_written,
        test_strict_mode_rejects_prohibited_private_input_columns,
        test_strict_mode_rejects_data_paths,
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for index, test in enumerate(tests):
            test(Path(tmp) / f"case_{index}")
    test_no_streamlit_outcome_or_veteran_imports_are_required()
