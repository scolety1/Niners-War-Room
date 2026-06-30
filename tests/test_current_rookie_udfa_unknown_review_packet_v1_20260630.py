from __future__ import annotations

import csv
import subprocess
from collections import Counter
from pathlib import Path

from scripts.build_current_rookie_udfa_unknown_review_packet_v1_20260630 import (
    DOC_ROOT,
    PACKET_COLUMNS,
    PREVIEW_COLUMNS,
    RECOMMENDATION_COLUMNS,
    VALID_DECISIONS,
)

ROOT = Path(__file__).resolve().parents[1]
NOT_ENOUGH = "Not enough information"


def test_evidence_packet_schema_counts_decisions_and_flags() -> None:
    rows = _rows("current_rookie_udfa_unknown_evidence_packet_v1.csv")
    decision_counts = _counts(rows, "recommended_human_decision")

    assert set(rows[0]) == set(PACKET_COLUMNS)
    assert len(rows) == 38
    assert decision_counts["CONFIRM_UDFA_REVIEW_ONLY"] == 28
    assert decision_counts["KEEP_UNKNOWN"] == 10
    assert set(decision_counts).issubset(VALID_DECISIONS)
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_packet_confirm_recommendations_have_strong_review_only_evidence() -> None:
    rows = _rows("current_rookie_udfa_unknown_evidence_packet_v1.csv")
    confirm_rows = [
        row
        for row in rows
        if row["recommended_human_decision"] == "CONFIRM_UDFA_REVIEW_ONLY"
    ]

    assert len(confirm_rows) == 28
    assert {row["evidence_strength"] for row in confirm_rows} == {
        "STRONG_REVIEW_ONLY"
    }
    assert {
        row["nflverse_draft_pick_search_result"] for row in confirm_rows
    } == {"not_found_in_complete_2025_2026_nflverse_draft_picks"}
    assert {
        row["CFBD_identity_status_if_available"] for row in confirm_rows
    } == {"GREEN_REVIEW_ONLY_IDENTITY_APPROVAL"}
    assert all("Absence" not in row["recommended_reason"] for row in confirm_rows)


def test_packet_unknown_rows_remain_not_enough_information() -> None:
    rows = _rows("current_rookie_udfa_unknown_evidence_packet_v1.csv")
    unknown_rows = [
        row for row in rows if row["recommended_human_decision"] == "KEEP_UNKNOWN"
    ]

    assert len(unknown_rows) == 10
    assert {row["evidence_strength"] for row in unknown_rows} == {
        "WEAK_REVIEW_ONLY"
    }
    assert {row["wrong_universe_risk"] for row in unknown_rows} == {"medium"}
    assert all(
        "Not enough information" in row["recommended_reason"]
        or "too thin" in row["recommended_reason"]
        for row in unknown_rows
    )


def test_recommendations_are_not_human_approved_or_model_training_allowed() -> None:
    rows = _rows("current_rookie_udfa_unknown_review_recommendations_v1.csv")
    decision_counts = _counts(rows, "recommended_human_decision")

    assert set(rows[0]) == set(RECOMMENDATION_COLUMNS)
    assert len(rows) == 38
    assert decision_counts["CONFIRM_UDFA_REVIEW_ONLY"] == 28
    assert decision_counts["KEEP_UNKNOWN"] == 10
    assert {row["approved_by_human"] for row in rows} == {"false"}
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_v5_preview_is_status_only_and_not_official_app_wiring() -> None:
    rows = _rows("rookie_display_artifact_v5_preview_coverage_matrix.csv")
    status_counts = _counts(rows, "preview_display_status_if_accepted")

    assert set(rows[0]) == set(PREVIEW_COLUMNS)
    assert len(rows) == 157
    assert status_counts["review_only_outcome_rates_available"] == 117
    assert status_counts["udfa_status_review_only_preview"] == 28
    assert status_counts[NOT_ENOUGH] == 10
    assert status_counts["wrong_universe_blocked"] == 2
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["display_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}


def test_v5_preview_does_not_create_fake_probabilities_or_round_eight() -> None:
    text = (
        DOC_ROOT / "rookie_display_artifact_v5_preview_coverage_matrix.csv"
    ).read_text(encoding="utf-8")

    assert "0%" not in text
    assert "round_8" not in text
    assert "probability" not in text.lower()


def test_human_summary_and_next_action_keep_gate_g_blocked() -> None:
    summary_text = (DOC_ROOT / "01_HUMAN_REVIEW_SUMMARY.md").read_text(
        encoding="utf-8"
    )
    decision_text = (DOC_ROOT / "02_NEXT_ACTION_DECISION.md").read_text(
        encoding="utf-8"
    )

    assert "CONFIRM_UDFA_REVIEW_ONLY: 28" in summary_text
    assert "KEEP_UNKNOWN: 10" in summary_text
    assert "Nothing was auto-applied" in decision_text
    assert "Gate G remains blocked" in decision_text
    assert "PARTIAL_REVIEW_PACKET_READY" in decision_text


def test_blocked_sources_not_used_in_packet_csv_outputs() -> None:
    output_text = "\n".join(path.read_text(encoding="utf-8") for path in DOC_ROOT.glob("*.csv"))

    for blocked in (
        "JackLich",
        "array-carpenter",
        "FootballDB",
        "ESPN",
        "DynastyProcess",
        "Gmail",
    ):
        assert blocked not in output_text


def test_shared_local_secret_raw_and_app_paths_are_not_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    normalized_status = status.replace("\\", "/")

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "C:\\NWR_LOCAL_SECRETS" not in tracked
    assert "local_exports" not in tracked
    assert "rookie_outcomes/display_artifact_v5/" not in tracked
    assert "app/" not in normalized_status
    assert "src/services/" not in normalized_status
    assert "docs/draft_day_exports/final_board_v1_20260622/" not in normalized_status


def _rows(file_name: str) -> list[dict[str, str]]:
    with (DOC_ROOT / file_name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _counts(rows: list[dict[str, str]], column: str) -> Counter[str]:
    return Counter(row[column] for row in rows)
