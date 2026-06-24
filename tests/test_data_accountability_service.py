from __future__ import annotations

from src.services.data_accountability_service import (
    NOT_ENOUGH_INFORMATION,
    build_free_agent_pool_audit,
    build_identity_coverage_audit,
    build_status_context,
    classify_status_warning,
    rostered_player_ids,
    sleeper_lookup,
)


def test_sleeper_free_agent_audit_matches_pdf_and_flags_rostered_conflict() -> None:
    pdf_rows = [
        {"player": "Tyreek Hill", "pos": "WR", "nfl_team": "MIA"},
        {"player": "Dallas Goedert", "pos": "TE", "nfl_team": "PHI"},
    ]
    sleeper_rows = [
        {
            "sleeper_player_id": "1",
            "full_name": "Tyreek Hill",
            "position": "WR",
            "team": "MIA",
            "status": "Active",
        },
        {
            "sleeper_player_id": "2",
            "full_name": "Dallas Goedert",
            "position": "TE",
            "team": "PHI",
            "status": "Active",
        },
    ]
    rows = build_free_agent_pool_audit(
        pdf_rows=pdf_rows,
        sleeper_rows=sleeper_rows,
        rostered_ids={"1"},
    )
    pdf_audits = [row for row in rows if row["audit_scope"] == "pdf_page3_free_agent"]

    assert pdf_audits[0]["audit_category"] == "PDF_MATCHED_BUT_ROSTERED_CONFLICT"
    assert pdf_audits[0]["sleeper_current_roster_state"] == "rostered_conflict"
    assert pdf_audits[1]["audit_category"] == "PDF_MATCHED_SLEEPER_FA"


def test_k_dst_are_retained_but_hidden_by_default() -> None:
    rows = build_free_agent_pool_audit(
        pdf_rows=[
            {"player": "Evan McPherson", "pos": "K", "nfl_team": "CIN"},
            {"player": "Jets", "pos": "DST", "nfl_team": "NYJ"},
        ],
        sleeper_rows=[
            {
                "sleeper_player_id": "10",
                "full_name": "Evan McPherson",
                "position": "K",
                "team": "CIN",
                "status": "Active",
            },
            {
                "sleeper_player_id": "11",
                "full_name": "Jets",
                "position": "DST",
                "team": "NYJ",
                "status": "Active",
            },
        ],
        rostered_ids=set(),
    )

    pdf_include_defaults = {
        row["include_default"]
        for row in rows
        if row["audit_scope"] == "pdf_page3_free_agent"
    }
    assert pdf_include_defaults == {"no"}
    assert all("K/DST hidden by default" in row["exclude_reason"] for row in rows)


def test_status_warning_classification_uses_flags_without_medical_inference() -> None:
    assert (
        classify_status_warning(
            player={"team": "MIA", "status": "Active", "injury_status": ""},
            expected_team="MIA",
        )
        == "clean"
    )
    assert (
        classify_status_warning(
            player={"team": "MIA", "status": "Injured Reserve", "injury_status": "IR"},
            expected_team="MIA",
        )
        == "injury/status review"
    )
    assert (
        classify_status_warning(
            player={"team": "BAL", "status": "Active", "injury_status": ""},
            expected_team="MIA",
        )
        == "team/status mismatch"
    )
    assert classify_status_warning(player=None) == "missing status metadata"


def test_status_context_missing_metadata_says_not_enough_information() -> None:
    rows = build_status_context(
        [{"player": "Unmatched Player", "pos": "WR", "nfl_team": "FA"}],
        sleeper_lookup([]),
    )

    assert rows[0]["status"] == NOT_ENOUGH_INFORMATION
    assert rows[0]["injury_status"] == NOT_ENOUGH_INFORMATION
    assert rows[0]["warning_classification"] == "missing status metadata"
    assert "do not infer clean health" in rows[0]["source_note"]


def test_identity_coverage_requires_high_confidence_for_no_manual_review() -> None:
    sleeper_rows = [
        {
            "sleeper_player_id": "9997",
            "full_name": "Zay Flowers",
            "position": "WR",
            "team": "BAL",
        }
    ]
    dp_rows = [
        {
            "player": "Zay Flowers",
            "pos": "WR",
            "sleeper_id": "9997",
            "fp_id": "23001",
        }
    ]
    rows = build_identity_coverage_audit(
        surfaces={
            "frozen_board": [
                {"player": "Zay Flowers", "position": "WR", "player_id": "9997"},
                {"player": "Mystery Player", "position": "RB"},
            ]
        },
        sleeper_rows=sleeper_rows,
        dynastyprocess_rows=dp_rows,
    )

    assert rows[0]["match_confidence"] == "HIGH"
    assert rows[0]["needs_manual_review"] == "no"
    assert rows[1]["match_method"] == "unresolved"
    assert rows[1]["needs_manual_review"] == "yes"


def test_rostered_player_ids_flattens_sleeper_rosters() -> None:
    assert rostered_player_ids([{"players": ["1", 2, None]}, {"players": []}]) == {
        "1",
        "2",
    }
