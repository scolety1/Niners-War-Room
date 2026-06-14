from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "build_rookie_analyzer_v03.py"
spec = importlib.util.spec_from_file_location("build_rookie_analyzer_v03", SCRIPT_PATH)
analyzer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(analyzer)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


REVIEW_FIELDS = [
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

SHADOW_FIELDS = [
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

CANDIDATE_FIELDS = [
    "candidate_rank",
    "player_id",
    "player_name",
    "position",
    "school",
    "pick_zone",
    "tag_summary",
    "production_ready_status",
    "promotion_blockers",
    "manual_warnings",
    "source_confidence",
    "evidence_basis_summary",
    "why_ranked_here",
    "why_not_higher",
    "why_not_lower",
    "production_candidate_only",
    "app_read_allowed",
    "probabilities_created",
    "source_safety_notes",
]


def make_fixture(root: Path) -> tuple[Path, Path, Path]:
    review_root = root / "local_exports" / "model_v4" / "rookie_framework_v02" / "review_board_v03"
    shadow_root = root / "local_exports" / "model_v4" / "rookie_framework_v02" / "shadow_ranking_v03"
    candidate_root = root / "local_exports" / "model_v4" / "rookie_framework_v02" / "production_candidate_v03"

    review_rows = [
        {
            "player_id": "p1",
            "player_name": "Alpha Back",
            "position": "RB",
            "school": "State",
            "current_pick_zone": "1.04",
            "v03_candidate_pick_zone": "1.04",
            "review_bucket": "premium_review",
            "position_group": "RB",
            "tag_summary": "RB_PREMIUM_THREE_DOWN",
            "hard_caps": "",
            "soft_flags": "RB_GOAL_LINE_SOFT_PROXY",
            "manual_review_flags": "pass_protection_grade_or_notes: manual_review_only",
            "urgent_manual_questions": "pass protection check",
            "source_confidence": "high",
            "best_source_safe_evidence_summary": "official final stats",
            "remaining_true_gaps": "routes_per_game|goal_line_touch_share",
            "prohibited_sources_detected": "none",
            "source_conflict_status": "none",
            "review_status": "review_needed",
            "notes": "fixture",
        },
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
            "manual_review_flags": "games_missed_if_available: premium_pick_injury_manual_review",
            "urgent_manual_questions": "injury check",
            "source_confidence": "medium",
            "best_source_safe_evidence_summary": "manual note",
            "remaining_true_gaps": "injury_history_score",
            "prohibited_sources_detected": "ranking",
            "source_conflict_status": "none",
            "review_status": "review_needed",
            "notes": "fixture",
        },
        {
            "player_id": "p3",
            "player_name": "Gamma Tight End",
            "position": "TE",
            "school": "Metro",
            "current_pick_zone": "5.04",
            "v03_candidate_pick_zone": "5.04",
            "review_bucket": "5_04_watchlist",
            "position_group": "TE",
            "tag_summary": "TE_REPLACEABLE",
            "hard_caps": "TE_REPLACEABLE",
            "soft_flags": "",
            "manual_review_flags": "",
            "urgent_manual_questions": "",
            "source_confidence": "low",
            "best_source_safe_evidence_summary": "unavailable",
            "remaining_true_gaps": "target_path",
            "prohibited_sources_detected": "none",
            "source_conflict_status": "none",
            "review_status": "capped_review",
            "notes": "fixture",
        },
    ]
    shadow_rows = []
    for index, row in enumerate(review_rows, start=1):
        shadow_rows.append(
            {
                "shadow_order": str(index),
                "player_id": row["player_id"],
                "player_name": row["player_name"],
                "position": row["position"],
                "school": row["school"],
                "current_pick_zone": row["current_pick_zone"],
                "v03_candidate_pick_zone": row["v03_candidate_pick_zone"],
                "review_bucket": row["review_bucket"],
                "shadow_review_group": "premium_shadow_review" if row["review_bucket"] == "premium_review" else "capped_shadow_review",
                "shadow_order_basis": "fixture; no market/rank/projection/private-score/probability/band inputs",
                "tag_summary": row["tag_summary"],
                "promotion_status": "shadow_only",
                "production_allowed": "no",
                "source_confidence": row["source_confidence"],
                "review_status": row["review_status"],
                "hard_caps": row["hard_caps"],
                "soft_flags": row["soft_flags"],
                "manual_review_flags": row["manual_review_flags"],
                "manual_flag_count": "1" if row["manual_review_flags"] else "0",
                "remaining_gap_count": "1",
                "prohibited_sources_detected": row["prohibited_sources_detected"],
                "source_conflict_status": row["source_conflict_status"],
                "best_source_safe_evidence_summary": row["best_source_safe_evidence_summary"],
                "remaining_true_gaps": row["remaining_true_gaps"],
                "notes": "fixture",
            }
        )
    candidate_rows = [
        {
            "candidate_rank": "1",
            "player_id": "p1",
            "player_name": "Alpha Back",
            "position": "RB",
            "school": "State",
            "pick_zone": "1.04",
            "tag_summary": "RB_PREMIUM_THREE_DOWN",
            "production_ready_status": "rankable_with_warning",
            "promotion_blockers": "none",
            "manual_warnings": "manual=pass_protection_grade_or_notes: manual_review_only|remaining_gaps=routes_per_game",
            "source_confidence": "high",
            "evidence_basis_summary": "official final stats",
            "why_ranked_here": "candidate fixture",
            "why_not_higher": "1.03 remains empty",
            "why_not_lower": "visible warnings",
            "production_candidate_only": "yes",
            "app_read_allowed": "no",
            "probabilities_created": "no",
            "source_safety_notes": "rankable only with visible warnings",
        },
        {
            "candidate_rank": "2",
            "player_id": "p2",
            "player_name": "Beta Wideout",
            "position": "WR",
            "school": "Tech",
            "pick_zone": "1.04",
            "tag_summary": "WR_ROUTE_EARNING",
            "production_ready_status": "manual_review_required",
            "promotion_blockers": "manual_review_required_before_ranking",
            "manual_warnings": "manual=games_missed_if_available: premium_pick_injury_manual_review",
            "source_confidence": "medium",
            "evidence_basis_summary": "manual note",
            "why_ranked_here": "candidate fixture",
            "why_not_higher": "injury review",
            "why_not_lower": "premium context",
            "production_candidate_only": "yes",
            "app_read_allowed": "no",
            "probabilities_created": "no",
            "source_safety_notes": "human review required before production ranking movement",
        },
        {
            "candidate_rank": "3",
            "player_id": "p3",
            "player_name": "Gamma Tight End",
            "position": "TE",
            "school": "Metro",
            "pick_zone": "5.04",
            "tag_summary": "TE_REPLACEABLE",
            "production_ready_status": "blocked",
            "promotion_blockers": "hard_caps=TE_REPLACEABLE",
            "manual_warnings": "low_source_confidence",
            "source_confidence": "low",
            "evidence_basis_summary": "unavailable",
            "why_ranked_here": "candidate fixture",
            "why_not_higher": "blocked",
            "why_not_lower": "capped",
            "production_candidate_only": "yes",
            "app_read_allowed": "no",
            "probabilities_created": "no",
            "source_safety_notes": "not eligible for promotion movement",
        },
    ]

    write_csv(review_root / "rookie_review_board_v03.csv", review_rows, REVIEW_FIELDS)
    write_csv(review_root / "rookie_review_board_manual_flags_v03.csv", [{"player_id": "p1"}, {"player_id": "p2"}], ["player_id"])
    write_csv(review_root / "rookie_review_board_remaining_gaps_v03.csv", [{"player_id": "p1"}, {"player_id": "p3"}], ["player_id"])
    (review_root / "README_ROOKIE_REVIEW_BOARD_V03.md").write_text("# fixture\n", encoding="utf-8")

    write_csv(shadow_root / "rookie_shadow_ranking_v03.csv", shadow_rows, SHADOW_FIELDS)
    write_csv(shadow_root / "rookie_shadow_ranking_premium_v03.csv", shadow_rows[:2], SHADOW_FIELDS)
    write_csv(shadow_root / "rookie_shadow_ranking_round2_v03.csv", [], SHADOW_FIELDS)
    write_csv(shadow_root / "rookie_shadow_ranking_5_04_watchlist_v03.csv", shadow_rows[2:], SHADOW_FIELDS)
    (shadow_root / "README_ROOKIE_SHADOW_RANKING_V03.md").write_text("# fixture\n", encoding="utf-8")

    write_csv(candidate_root / "rookie_production_candidate_v03.csv", candidate_rows, CANDIDATE_FIELDS)
    write_csv(candidate_root / "rookie_production_candidate_premium_v03.csv", candidate_rows[:2], CANDIDATE_FIELDS)
    write_csv(candidate_root / "rookie_production_candidate_round2_v03.csv", [], CANDIDATE_FIELDS)
    write_csv(candidate_root / "rookie_production_candidate_5_04_v03.csv", candidate_rows[2:], CANDIDATE_FIELDS)
    write_csv(candidate_root / "rookie_production_candidate_manual_warnings_v03.csv", candidate_rows, CANDIDATE_FIELDS)
    write_csv(candidate_root / "rookie_production_candidate_source_safety_audit_v03.csv", candidate_rows, CANDIDATE_FIELDS)
    (candidate_root / "README_ROOKIE_PRODUCTION_CANDIDATE_V03.md").write_text("# fixture\n", encoding="utf-8")

    return review_root, shadow_root, candidate_root


def test_analyzer_rows_are_not_app_ready_and_create_no_scores_or_probabilities(tmp_path: Path) -> None:
    review_root, shadow_root, candidate_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    analyzer.build_exports(review_root, shadow_root, candidate_root, out, strict=True)
    rows = read_csv(out / "rookie_analyzer_v03.csv")
    assert rows
    assert {row["app_ready"] for row in rows} == {"no"}
    assert {row["production_score_created"] for row in rows} == {"no"}
    assert {row["probabilities_created"] for row in rows} == {"no"}


def test_rankable_with_warning_rows_keep_visible_warning_context(tmp_path: Path) -> None:
    review_root, shadow_root, candidate_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    analyzer.build_exports(review_root, shadow_root, candidate_root, out, strict=True)
    rows = {row["player_id"]: row for row in read_csv(out / "rookie_analyzer_v03.csv")}
    assert rows["p1"]["production_ready_status"] == "rankable_with_warning"
    assert "pass_protection_grade_or_notes" in rows["p1"]["warnings"]
    assert rows["p1"]["best_pick_fit"] == "1.04_premium_warning_visible"


def test_manual_review_and_blocked_splits_are_written(tmp_path: Path) -> None:
    review_root, shadow_root, candidate_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    analyzer.build_exports(review_root, shadow_root, candidate_root, out, strict=True)
    manual = read_csv(out / "rookie_analyzer_manual_review_v03.csv")
    blocked = read_csv(out / "rookie_analyzer_blocked_v03.csv")
    assert [row["player_id"] for row in manual] == ["p2"]
    assert [row["player_id"] for row in blocked] == ["p3"]


def test_required_outputs_are_written(tmp_path: Path) -> None:
    review_root, shadow_root, candidate_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    analyzer.build_exports(review_root, shadow_root, candidate_root, out, strict=True)
    for name in [
        "rookie_analyzer_v03.csv",
        "rookie_analyzer_premium_v03.csv",
        "rookie_analyzer_round2_v03.csv",
        "rookie_analyzer_5_04_v03.csv",
        "rookie_analyzer_manual_review_v03.csv",
        "rookie_analyzer_blocked_v03.csv",
        "rookie_analyzer_readme.md",
    ]:
        assert (out / name).exists()


def test_strict_mode_rejects_prohibited_private_input_columns(tmp_path: Path) -> None:
    review_root, shadow_root, candidate_root = make_fixture(tmp_path)
    path = candidate_root / "rookie_production_candidate_v03.csv"
    rows = read_csv(path)
    for row in rows:
        row["private_score"] = "99"
    write_csv(path, rows, list(rows[0].keys()))
    try:
        analyzer.build_exports(review_root, shadow_root, candidate_root, tmp_path / "out", strict=True)
    except analyzer.RookieAnalyzerError as exc:
        assert "Prohibited private input columns" in str(exc)
    else:
        raise AssertionError("strict mode should reject private_score input")


def test_strict_mode_rejects_data_paths(tmp_path: Path) -> None:
    review_root, shadow_root, candidate_root = make_fixture(tmp_path)
    try:
        analyzer.build_exports(review_root, shadow_root, candidate_root, tmp_path / "data" / "out", strict=True)
    except analyzer.RookieAnalyzerError as exc:
        assert "data/" in str(exc)
    else:
        raise AssertionError("analyzer should reject data/ output paths")


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
        test_analyzer_rows_are_not_app_ready_and_create_no_scores_or_probabilities,
        test_rankable_with_warning_rows_keep_visible_warning_context,
        test_manual_review_and_blocked_splits_are_written,
        test_required_outputs_are_written,
        test_strict_mode_rejects_prohibited_private_input_columns,
        test_strict_mode_rejects_data_paths,
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for index, test in enumerate(tests):
            test(Path(tmp) / f"case_{index}")
    test_no_streamlit_outcome_or_veteran_imports_are_required()
