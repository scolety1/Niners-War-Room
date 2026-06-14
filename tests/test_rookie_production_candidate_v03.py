from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "build_rookie_production_candidate_v03.py"
spec = importlib.util.spec_from_file_location("build_rookie_production_candidate_v03", SCRIPT_PATH)
candidate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate)


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
    input_root = root / "local_exports" / "model_v4" / "rookie_framework_v02" / "shadow_ranking_v03"
    fields = [
        "shadow_order",
        "player_id",
        "player_name",
        "position",
        "school",
        "current_pick_zone",
        "v03_candidate_pick_zone",
        "review_bucket",
        "shadow_review_group",
        "shadow_order_basis",
        "tag_summary",
        "promotion_status",
        "production_allowed",
        "source_confidence",
        "review_status",
        "hard_caps",
        "soft_flags",
        "manual_review_flags",
        "manual_flag_count",
        "remaining_gap_count",
        "prohibited_sources_detected",
        "source_conflict_status",
        "best_source_safe_evidence_summary",
        "remaining_true_gaps",
        "notes",
    ]
    rows = [
        {
            "shadow_order": "1",
            "player_id": "p1",
            "player_name": "Alpha Back",
            "position": "RB",
            "school": "State",
            "current_pick_zone": "1.04",
            "v03_candidate_pick_zone": "1.04",
            "review_bucket": "premium_review",
            "shadow_review_group": "premium_shadow_review",
            "shadow_order_basis": "fixture",
            "tag_summary": "RB_PREMIUM",
            "promotion_status": "shadow_only",
            "production_allowed": "no",
            "source_confidence": "high",
            "review_status": "review_needed",
            "hard_caps": "",
            "soft_flags": "",
            "manual_review_flags": "",
            "manual_flag_count": "0",
            "remaining_gap_count": "0",
            "prohibited_sources_detected": "none",
            "source_conflict_status": "none",
            "best_source_safe_evidence_summary": "official data",
            "remaining_true_gaps": "",
            "notes": "fixture",
        },
        {
            "shadow_order": "2",
            "player_id": "p2",
            "player_name": "Beta Wideout",
            "position": "WR",
            "school": "Tech",
            "current_pick_zone": "1.04",
            "v03_candidate_pick_zone": "1.04",
            "review_bucket": "premium_review",
            "shadow_review_group": "premium_shadow_review",
            "shadow_order_basis": "fixture",
            "tag_summary": "WR_ROUTE",
            "promotion_status": "shadow_only",
            "production_allowed": "no",
            "source_confidence": "medium",
            "review_status": "review_needed",
            "hard_caps": "",
            "soft_flags": "SOURCE_LIMITED",
            "manual_review_flags": "route_tree_grade_or_notes: manual_review_only",
            "manual_flag_count": "1",
            "remaining_gap_count": "1",
            "prohibited_sources_detected": "ranking",
            "source_conflict_status": "none",
            "best_source_safe_evidence_summary": "soft flag",
            "remaining_true_gaps": "targets_per_route_run",
            "notes": "fixture",
        },
        {
            "shadow_order": "3",
            "player_id": "p3",
            "player_name": "Gamma Receiver",
            "position": "WR",
            "school": "Metro",
            "current_pick_zone": "1.04",
            "v03_candidate_pick_zone": "1.04",
            "review_bucket": "premium_review",
            "shadow_review_group": "premium_shadow_review",
            "shadow_order_basis": "fixture",
            "tag_summary": "WR_ROUTE",
            "promotion_status": "shadow_only",
            "production_allowed": "no",
            "source_confidence": "medium",
            "review_status": "review_needed",
            "hard_caps": "",
            "soft_flags": "SOURCE_LIMITED",
            "manual_review_flags": "games_missed_if_available: premium_pick_injury_manual_review",
            "manual_flag_count": "1",
            "remaining_gap_count": "1",
            "prohibited_sources_detected": "none",
            "source_conflict_status": "none",
            "best_source_safe_evidence_summary": "injury note",
            "remaining_true_gaps": "return_status",
            "notes": "fixture",
        },
        {
            "shadow_order": "4",
            "player_id": "p4",
            "player_name": "Gamma Passer",
            "position": "QB",
            "school": "Metro",
            "current_pick_zone": "5.04",
            "v03_candidate_pick_zone": "5.04",
            "review_bucket": "5_04_watchlist",
            "shadow_review_group": "capped_shadow_review",
            "shadow_order_basis": "fixture",
            "tag_summary": "QB_EXCEPTION",
            "promotion_status": "shadow_only",
            "production_allowed": "no",
            "source_confidence": "low",
            "review_status": "capped_review",
            "hard_caps": "QB_RUSHING_NO_JOB_SECURITY",
            "soft_flags": "",
            "manual_review_flags": "",
            "manual_flag_count": "0",
            "remaining_gap_count": "1",
            "prohibited_sources_detected": "none",
            "source_conflict_status": "none",
            "best_source_safe_evidence_summary": "unavailable",
            "remaining_true_gaps": "designed_rush_share",
            "notes": "fixture",
        },
    ]
    write_csv(input_root / "rookie_shadow_ranking_v03.csv", rows, fields)
    write_csv(input_root / "rookie_shadow_ranking_premium_v03.csv", rows[:3], fields)
    write_csv(input_root / "rookie_shadow_ranking_round2_v03.csv", [], fields)
    write_csv(input_root / "rookie_shadow_ranking_5_04_watchlist_v03.csv", [rows[3]], fields)
    (input_root / "README_ROOKIE_SHADOW_RANKING_V03.md").write_text("# fixture\n", encoding="utf-8")
    return input_root


def test_candidate_rows_are_candidate_only_and_not_app_read(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    candidate.build_exports(input_root=input_root, output_dir=out, strict=True)
    rows = read_csv(out / "rookie_production_candidate_v03.csv")
    assert rows
    assert {row["production_candidate_only"] for row in rows} == {"yes"}
    assert {row["app_read_allowed"] for row in rows} == {"no"}
    assert {row["probabilities_created"] for row in rows} == {"no"}


def test_candidate_export_does_not_open_1_03(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    candidate.build_exports(input_root=input_root, output_dir=out, strict=True)
    rows = read_csv(out / "rookie_production_candidate_v03.csv")
    assert not any(row["pick_zone"] == "1.03" for row in rows)


def test_rankable_warning_manual_review_and_blocked_statuses_are_preserved(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    candidate.build_exports(input_root=input_root, output_dir=out, strict=True)
    rows = {row["player_id"]: row for row in read_csv(out / "rookie_production_candidate_v03.csv")}
    assert rows["p1"]["production_ready_status"] == "ready"
    assert rows["p2"]["production_ready_status"] == "rankable_with_warning"
    assert "quarantined_sources=ranking" in rows["p2"]["manual_warnings"]
    assert "remaining_gaps=targets_per_route_run" in rows["p2"]["manual_warnings"]
    assert rows["p3"]["production_ready_status"] == "manual_review_required"
    assert "manual_review_required_before_ranking" in rows["p3"]["promotion_blockers"]
    assert rows["p4"]["production_ready_status"] == "blocked"
    assert "hard_caps=QB_RUSHING_NO_JOB_SECURITY" in rows["p4"]["promotion_blockers"]


def test_required_split_outputs_are_written(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    candidate.build_exports(input_root=input_root, output_dir=out, strict=True)
    for name in [
        "rookie_production_candidate_v03.csv",
        "rookie_production_candidate_premium_v03.csv",
        "rookie_production_candidate_round2_v03.csv",
        "rookie_production_candidate_5_04_v03.csv",
        "rookie_production_candidate_manual_warnings_v03.csv",
        "rookie_production_candidate_source_safety_audit_v03.csv",
        "README_ROOKIE_PRODUCTION_CANDIDATE_V03.md",
    ]:
        assert (out / name).exists()


def test_strict_mode_rejects_prohibited_private_input_columns(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    path = input_root / "rookie_shadow_ranking_v03.csv"
    rows = read_csv(path)
    for row in rows:
        row["private_score"] = "99"
    write_csv(path, rows, list(rows[0].keys()))
    try:
        candidate.build_exports(input_root=input_root, output_dir=tmp_path / "out", strict=True)
    except candidate.ProductionCandidateError as exc:
        assert "Prohibited private input columns" in str(exc)
    else:
        raise AssertionError("strict mode should reject private_score input")


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
        test_candidate_rows_are_candidate_only_and_not_app_read,
        test_candidate_export_does_not_open_1_03,
        test_rankable_warning_manual_review_and_blocked_statuses_are_preserved,
        test_required_split_outputs_are_written,
        test_strict_mode_rejects_prohibited_private_input_columns,
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for index, test in enumerate(tests):
            test(Path(tmp) / f"case_{index}")
    test_no_streamlit_outcome_or_veteran_imports_are_required()
