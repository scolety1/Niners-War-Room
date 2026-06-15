from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "build_rookie_review_board_v03.py"
spec = importlib.util.spec_from_file_location("build_rookie_review_board_v03", SCRIPT_PATH)
rookie_review = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(rookie_review)


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
    input_root = root / "local_exports" / "model_v4" / "rookie_framework_v02"
    player_fields = [
        "player_id",
        "player_name",
        "position",
        "school",
        "current_pick_zone",
        "v03_candidate_pick_zone",
        "tag_summary",
        "hard_caps",
        "soft_flags",
        "urgent_manual_flags",
        "best_source_safe_evidence_summary",
        "remaining_true_gaps",
        "source_confidence",
        "v03_candidate_action",
        "notes",
    ]
    player_rows = [
        {
            "player_id": "p1",
            "player_name": "Alpha Back",
            "position": "RB",
            "school": "State",
            "current_pick_zone": "2.08",
            "v03_candidate_pick_zone": "2.08",
            "tag_summary": "RB_CONTACT",
            "hard_caps": "",
            "soft_flags": "RB_RECEIVING_BACK",
            "urgent_manual_flags": "pass_protection_grade_or_notes: manual_review_only",
            "best_source_safe_evidence_summary": "pass_protection_grade_or_notes: prose note (manual_review_only)",
            "remaining_true_gaps": "fumbles_per_touch",
            "source_confidence": "medium",
            "v03_candidate_action": "manual_review",
            "notes": "fixture",
        },
        {
            "player_id": "p2",
            "player_name": "Beta Wideout",
            "position": "WR",
            "school": "Tech",
            "current_pick_zone": "1.04",
            "v03_candidate_pick_zone": "1.04",
            "tag_summary": "WR_ROUTE_EARNING",
            "hard_caps": "",
            "soft_flags": "SOURCE_LIMITED",
            "urgent_manual_flags": "route_tree_grade_or_notes: manual_review_only",
            "best_source_safe_evidence_summary": "final_season_yprr: 2.1 (use_as_soft_flag)",
            "remaining_true_gaps": "",
            "source_confidence": "medium",
            "v03_candidate_action": "manual_review",
            "notes": "fixture",
        },
        {
            "player_id": "p3",
            "player_name": "Gamma Passer",
            "position": "QB",
            "school": "Metro",
            "current_pick_zone": "5.04",
            "v03_candidate_pick_zone": "5.04",
            "tag_summary": "QB_RUSHING_EDGE",
            "hard_caps": "QB_RUSHING_NO_JOB_SECURITY",
            "soft_flags": "",
            "urgent_manual_flags": "",
            "best_source_safe_evidence_summary": "Deep Research found unavailable fields.",
            "remaining_true_gaps": "designed_rush_share",
            "source_confidence": "low",
            "v03_candidate_action": "cap",
            "notes": "fixture",
        },
        {
            "player_id": "p4",
            "player_name": "Delta Dart",
            "position": "WR",
            "school": "Coastal",
            "current_pick_zone": "5.04",
            "v03_candidate_pick_zone": "5.04",
            "tag_summary": "WR_TRUE_ALPHA_TARGET_EARNER",
            "hard_caps": "",
            "soft_flags": "",
            "urgent_manual_flags": "",
            "best_source_safe_evidence_summary": "target evidence unavailable",
            "remaining_true_gaps": "targets_per_route_run",
            "source_confidence": "low",
            "v03_candidate_action": "manual_review",
            "notes": "fixture",
        },
    ]
    candidate_dir = input_root / "v03_candidate_01"
    write_csv(candidate_dir / "v03_candidate_player_review_board.csv", player_rows, player_fields)
    write_csv(candidate_dir / "v03_candidate_premium_pick_board.csv", [player_rows[1]], player_fields + ["premium_pick_reason"])
    write_csv(candidate_dir / "v03_candidate_round2_board.csv", [player_rows[0]], player_fields + ["round2_focus"])
    write_csv(candidate_dir / "v03_candidate_5_04_board.csv", [player_rows[2], player_rows[3]], player_fields + ["five04_case"])

    manual_fields = [
        "player_id",
        "player_name",
        "position",
        "school",
        "framework_field",
        "value_or_note",
        "source_name",
        "source_url",
        "date_accessed",
        "flag_type",
        "review_priority",
        "identity_match_status",
        "reason",
    ]
    write_csv(
        input_root / "deep_research_intake_pass_04" / "deep_research_manual_review_flags.csv",
        [
            {
                "player_id": "p2",
                "player_name": "Beta Wideout",
                "position": "WR",
                "school": "Tech",
                "framework_field": "final_season_yprr",
                "value_or_note": "2.1",
                "source_name": "Secondary",
                "source_url": "https://example.test/analysis-rankings",
                "date_accessed": "2026-06-12",
                "flag_type": "use_as_soft_flag",
                "review_priority": "medium",
                "identity_match_status": "exact",
                "reason": "secondary evidence preserved as soft flag",
            }
        ],
        manual_fields,
    )
    gap_fields = [
        "player_id",
        "player_name",
        "position",
        "school",
        "missing_field",
        "marked_value",
        "source_file",
        "reason_missing",
        "recommended_next_source",
        "severity",
    ]
    write_csv(
        input_root / "deep_research_intake_pass_04" / "deep_research_remaining_gaps_after_pass04.csv",
        [
            {
                "player_id": "p1",
                "player_name": "Alpha Back",
                "position": "RB",
                "school": "State",
                "missing_field": "fumbles_per_touch",
                "marked_value": "unavailable",
                "source_file": "fixture",
                "reason_missing": "not sourced",
                "recommended_next_source": "official_structured",
                "severity": "high",
            }
        ],
        gap_fields,
    )
    safety_fields = [
        "evidence_id",
        "player_id",
        "player_name",
        "framework_field",
        "source_name",
        "source_url",
        "reported_field_status",
        "allowed_status",
        "private_value_allowed",
        "audit_only_allowed",
        "display_only_allowed",
        "contamination_risk",
        "market_contamination_blocker",
        "detected_forbidden_context_terms",
        "reason",
    ]
    write_csv(
        input_root / "deep_research_intake_pass_04" / "deep_research_source_safety_audit.csv",
        [
            {
                "evidence_id": "e1",
                "player_id": "p2",
                "player_name": "Beta Wideout",
                "framework_field": "final_season_yprr",
                "source_name": "Secondary",
                "source_url": "https://example.test/analysis-rankings",
                "reported_field_status": "use_as_soft_flag",
                "allowed_status": "use_as_soft_flag",
                "private_value_allowed": "conditional",
                "audit_only_allowed": "yes",
                "display_only_allowed": "yes",
                "contamination_risk": "medium",
                "market_contamination_blocker": "no",
                "detected_forbidden_context_terms": "ranking;projection",
                "reason": "quarantined source context",
            }
        ],
        safety_fields,
    )
    (input_root / "deep_research_intake_pass_04" / "deep_research_conflict_review.csv").parent.mkdir(parents=True, exist_ok=True)
    (input_root / "deep_research_intake_pass_04" / "deep_research_conflict_review.csv").write_text("\n", encoding="utf-8")
    write_csv(input_root / "v03_adversarial_audit_01" / "v03_adversarial_findings.csv", [], ["audit_question", "status", "severity", "finding", "evidence", "recommended_action"])
    write_csv(input_root / "v03_adversarial_audit_01" / "v03_patch_queue.csv", [], ["patch_id", "priority", "patch_type", "target", "issue", "safe_patch_action", "implemented", "requires_model_logic_change", "notes"])
    (input_root / "OVERNIGHT_QUEUE_FINAL_SUMMARY_20260612.md").write_text("# fixture\n", encoding="utf-8")
    return input_root


def test_required_columns_and_statuses_are_produced(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    rookie_review.build_exports(input_root=input_root, output_dir=out, strict=True)
    rows = read_csv(out / "rookie_review_board_v03.csv")
    assert set(rookie_review.REVIEW_COLUMNS).issubset(rows[0].keys())
    assert {row["review_status"] for row in rows} <= rookie_review.REVIEW_STATUS_VALUES


def test_prohibited_output_column_names_are_not_produced(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    rookie_review.build_exports(input_root=input_root, output_dir=out, strict=True)
    columns = read_csv(out / "rookie_review_board_v03.csv")[0].keys()
    for column in columns:
        assert not (rookie_review.normalized_field_tokens(column) & rookie_review.PROHIBITED_OUTPUT_NAME_TOKENS)


def test_prohibited_source_context_is_flagged_not_promoted(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    rookie_review.build_exports(input_root=input_root, output_dir=out, strict=True)
    rows = {row["player_id"]: row for row in read_csv(out / "rookie_review_board_v03.csv")}
    assert rows["p2"]["prohibited_sources_detected"] == "projection|ranking"
    assert rows["p2"]["review_status"] == "review_needed"


def test_soft_and_manual_flags_remain_review_context(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    rookie_review.build_exports(input_root=input_root, output_dir=out, strict=True)
    manual_rows = read_csv(out / "rookie_review_board_manual_flags_v03.csv")
    assert any(row["flag_type"] == "use_as_soft_flag" for row in manual_rows)
    assert any(row["flag_type"] == "manual_review_only" for row in manual_rows)
    assert not any(row["flag_type"] == "use_now" for row in manual_rows)


def test_unavailable_gaps_remain_needs_data(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out = tmp_path / "out"
    rookie_review.build_exports(input_root=input_root, output_dir=out, strict=True)
    gaps = read_csv(out / "rookie_review_board_remaining_gaps_v03.csv")
    assert gaps[0]["marked_value"] == "unavailable"
    rows = {row["player_id"]: row for row in read_csv(out / "rookie_review_board_v03.csv")}
    assert rows["p4"]["review_status"] == "watchlist_review"


def test_reconciliation_repair_context_carries_source_safe_local_evidence() -> None:
    row = {
        "player_id": "prospect:2026:carnelltate:WR",
        "player_name": "Carnell Tate",
        "position": "WR",
        "school": "Ohio State",
        "tag_summary": "WR_SOURCE_LIMITED_REVIEW",
        "soft_flags": "SOURCE_LIMITED",
        "manual_review_flags": "",
        "source_confidence": "low",
        "best_source_safe_evidence_summary": "No Deep Research evidence matched.",
        "remaining_true_gaps": "",
        "notes": "fixture",
    }
    context = {
        "tag_row": {
            "tag_confidence": "low",
            "soft_flag_tags": "SOURCE_LIMITED",
            "manual_review_tags": "career_yprr_review|final_season_yprr_review",
            "missing_data_tags": "career_yprr|final_season_yprr",
            "evidence_summary": "target-command context from approved local normalization only",
        },
        "source_hit_summaries": [
            "target_command_context: use_as_soft_flag (reception_share=0.0096); not a projection/rank"
        ],
    }
    repaired = rookie_review.apply_repair_context(row, context)
    assert repaired["best_source_safe_evidence_summary"].startswith("reconciliation_repair_context:")
    assert "source_hit_context:" in repaired["best_source_safe_evidence_summary"]
    assert "career_yprr: repair_context_review_only" in repaired["manual_review_flags"]
    assert "target_command_context: use_as_soft_flag" in repaired["manual_review_flags"]
    assert "career_yprr|final_season_yprr" == repaired["remaining_true_gaps"]
    assert "SOURCE_SAFE_REPAIR_CONTEXT" in repaired["soft_flags"]


def test_output_sorting_is_deterministic(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    rookie_review.build_exports(input_root=input_root, output_dir=out1, strict=True)
    rookie_review.build_exports(input_root=input_root, output_dir=out2, strict=True)
    assert (out1 / "rookie_review_board_v03.csv").read_text(encoding="utf-8") == (
        out2 / "rookie_review_board_v03.csv"
    ).read_text(encoding="utf-8")


def test_strict_mode_rejects_prohibited_input_columns(tmp_path: Path) -> None:
    input_root = make_fixture(tmp_path)
    path = input_root / "v03_candidate_01" / "v03_candidate_player_review_board.csv"
    rows = read_csv(path)
    for row in rows:
        row["adp"] = "1"
    write_csv(path, rows, list(rows[0].keys()))
    try:
        rookie_review.build_exports(input_root=input_root, output_dir=tmp_path / "out", strict=True)
    except rookie_review.ReviewBoardError as exc:
        assert "Prohibited input columns" in str(exc)
    else:
        raise AssertionError("strict mode should reject prohibited input columns")


def test_no_streamlit_import_is_required() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8").lower()
    assert "import streamlit" not in source
    assert "from streamlit" not in source
