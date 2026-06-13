from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "build_rookie_shadow_ranking_v03.py"
spec = importlib.util.spec_from_file_location("build_rookie_shadow_ranking_v03", SCRIPT_PATH)
shadow = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(shadow)


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
    input_root = root / "local_exports" / "model_v4" / "rookie_framework_v02" / "review_board_v03"
    fields = [
        "player_id",
        "player_name",
        "position",
        "school",
        "current_pick_zone",
        "v03_candidate_pick_zone",
        "review_bucket",
        "position_group",
        "tag_summary",
        "hard_caps",
        "soft_flags",
        "manual_review_flags",
        "urgent_manual_questions",
        "source_confidence",
        "best_source_safe_evidence_summary",
        "remaining_true_gaps",
        "prohibited_sources_detected",
        "source_conflict_status",
        "review_status",
        "notes",
    ]
    rows = [
        {
            "player_id": "p2",
            "player_name": "Beta Wideout",
            "position": "WR",
            "school": "Tech",
            "current_pick_zone": "1.04",
            "v03_candidate_pick_zone": "1.04",
            "review_bucket": "premium_review",
            "position_group": "WR",
            "tag_summary": "WR_ROUTE_EARNING",
            "hard_caps": "",
            "soft_flags": "SOURCE_LIMITED",
            "manual_review_flags": "route_tree_grade_or_notes: manual_review_only",
            "urgent_manual_questions": "route_tree_grade_or_notes requires manual_review_only",
            "source_confidence": "medium",
            "best_source_safe_evidence_summary": "final_season_yprr: 2.1 (use_as_soft_flag)",
            "remaining_true_gaps": "",
            "prohibited_sources_detected": "ranking",
            "source_conflict_status": "none",
            "review_status": "review_needed",
            "notes": "manual review only",
        },
        {
            "player_id": "p1",
            "player_name": "Alpha Back",
            "position": "RB",
            "school": "State",
            "current_pick_zone": "2.08",
            "v03_candidate_pick_zone": "2.08",
            "review_bucket": "round2_review",
            "position_group": "RB",
            "tag_summary": "RB_CONTACT",
            "hard_caps": "",
            "soft_flags": "RB_RECEIVING_BACK",
            "manual_review_flags": "pass_protection_grade_or_notes: manual_review_only",
            "urgent_manual_questions": "pass_protection_grade_or_notes requires manual_review_only",
            "source_confidence": "high",
            "best_source_safe_evidence_summary": "fumbles_per_touch: use_now",
            "remaining_true_gaps": "routes_per_game|goal_line_touch_share",
            "prohibited_sources_detected": "none",
            "source_conflict_status": "none",
            "review_status": "needs_data",
            "notes": "review only",
        },
        {
            "player_id": "p3",
            "player_name": "Gamma Passer",
            "position": "QB",
            "school": "Metro",
            "current_pick_zone": "5.04",
            "v03_candidate_pick_zone": "5.04",
            "review_bucket": "5_04_watchlist",
            "position_group": "QB",
            "tag_summary": "QB_RUSHING_EDGE",
            "hard_caps": "QB_RUSHING_NO_JOB_SECURITY",
            "soft_flags": "",
            "manual_review_flags": "",
            "urgent_manual_questions": "",
            "source_confidence": "low",
            "best_source_safe_evidence_summary": "unavailable",
            "remaining_true_gaps": "designed_rush_share",
            "prohibited_sources_detected": "none",
            "source_conflict_status": "none",
            "review_status": "capped_review",
            "notes": "capped",
        },
    ]
    write_csv(input_root / "rookie_review_board_v03.csv", rows, fields)
    write_csv(input_root / "rookie_review_board_premium_review_v03.csv", [rows[0]], fields)
    write_csv(input_root / "rookie_review_board_round2_v03.csv", [rows[1]], fields)
    write_csv(input_root / "rookie_review_board_5_04_watchlist_v03.csv", [rows[2]], fields)
    write_csv(
        input_root / "rookie_review_board_manual_flags_v03.csv",
        [
            {"player_id": "p2", "framework_field": "route_tree_grade_or_notes"},
            {"player_id": "p1", "framework_field": "pass_protection_grade_or_notes"},
        ],
        ["player_id", "framework_field"],
    )
    write_csv(
        input_root / "rookie_review_board_remaining_gaps_v03.csv",
        [
            {"player_id": "p1", "missing_field": "routes_per_game"},
            {"player_id": "p3", "missing_field": "designed_rush_share"},
        ],
        ["player_id", "missing_field"],
    )
    (input_root / "README_ROOKIE_REVIEW_BOARD_V03.md").write_text("# fixture\n", encoding="utf-8")
    return input_root


def test_shadow_rows_are_marked_shadow_only_and_not_production(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    output_dir = tmp_path / "out"
    shadow.build_exports(input_root=input_root, output_dir=output_dir, strict=True)
    rows = read_csv(output_dir / "rookie_shadow_ranking_v03.csv")
    assert rows
    assert {row["promotion_status"] for row in rows} == {"shadow_only"}
    assert {row["production_allowed"] for row in rows} == {"no"}


def test_shadow_export_uses_review_metadata_not_private_inputs(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    output_dir = tmp_path / "out"
    shadow.build_exports(input_root=input_root, output_dir=output_dir, strict=True)
    rows = read_csv(output_dir / "rookie_shadow_ranking_v03.csv")
    assert all("no market/rank/projection/private-score/probability/band inputs" in row["shadow_order_basis"] for row in rows)
    assert rows[0]["review_bucket"] == "premium_review"


def test_strict_mode_rejects_prohibited_private_input_columns(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    path = input_root / "rookie_review_board_v03.csv"
    rows = read_csv(path)
    for row in rows:
        row["private_score"] = "99"
    write_csv(path, rows, list(rows[0].keys()))
    try:
        shadow.build_exports(input_root=input_root, output_dir=tmp_path / "out", strict=True)
    except shadow.ShadowExportError as exc:
        assert "Prohibited private input columns" in str(exc)
    else:
        raise AssertionError("strict mode should reject private_score input")


def test_warning_field_is_allowed_but_not_promoted(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    output_dir = tmp_path / "out"
    shadow.build_exports(input_root=input_root, output_dir=output_dir, strict=True)
    rows = {row["player_id"]: row for row in read_csv(output_dir / "rookie_shadow_ranking_v03.csv")}
    assert rows["p2"]["prohibited_sources_detected"] == "ranking"
    assert rows["p2"]["production_allowed"] == "no"


def test_capped_watchlist_rows_remain_capped(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    output_dir = tmp_path / "out"
    shadow.build_exports(input_root=input_root, output_dir=output_dir, strict=True)
    rows = {row["player_id"]: row for row in read_csv(output_dir / "rookie_shadow_ranking_v03.csv")}
    assert rows["p3"]["shadow_review_group"] == "capped_shadow_review"


def test_outputs_are_deterministic(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    shadow.build_exports(input_root=input_root, output_dir=out1, strict=True)
    shadow.build_exports(input_root=input_root, output_dir=out2, strict=True)
    assert (out1 / "rookie_shadow_ranking_v03.csv").read_text(encoding="utf-8") == (
        out2 / "rookie_shadow_ranking_v03.csv"
    ).read_text(encoding="utf-8")


def test_no_streamlit_or_outcome_imports_are_required() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8").lower()
    assert "import streamlit" not in source
    assert "from streamlit" not in source
    assert "import outcome" not in source
    assert "from outcome" not in source
    assert "import veteran" not in source
    assert "from veteran" not in source
