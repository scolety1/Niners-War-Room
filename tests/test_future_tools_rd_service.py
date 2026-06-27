from __future__ import annotations

from pathlib import Path

from src.services.future_tools_rd_service import (
    ALLOWED_DECISIONS,
    deadline_checklist,
    future_pick_ledger_from_runtime_state,
    future_tools_summary,
    group_future_tools,
    load_future_tools_status_matrix,
    parse_manual_future_pick_text,
    parse_manual_roster_text,
    parse_manual_table_text,
    roster_age_bucket_summary,
    roster_dynasty_rank_bucket_summary,
    roster_position_summary,
    safe_v0_tools,
    upcoming_draft_data_readiness_checklist,
    upcoming_draft_questions_checklist,
    upcoming_draft_setup_checklist,
)

EXPECTED_TOOLS = {
    "Who Should I Start?",
    "Waiver Wire Rankings",
    "In-Season Rankings",
    "Trade Targets",
    "Roster Weakness Tracker",
    "Upcoming Rookie Class Preview",
    "Draft Class Strength",
    "Position Strength by Class",
    "Future Pick Planning",
    "Upcoming Draft Prep",
    "Position Target Plan",
    "Keeper Deadline Prep",
    "Drop Deadline Prep",
    "Trade Deadline Prep",
    "Playoff Push Planner",
}


def test_future_tools_matrix_loads_all_expected_tools() -> None:
    rows = load_future_tools_status_matrix()

    assert len(rows) == 15
    assert {row.tool_name for row in rows} == EXPECTED_TOOLS
    assert set(group_future_tools(rows)) == {
        "In-Season Tools",
        "Future Draft Prep",
        "League Calendar Tools",
    }


def test_future_tools_matrix_keeps_all_active_outputs_blocked() -> None:
    rows = load_future_tools_status_matrix()
    summary = future_tools_summary(rows)

    assert summary["active_outputs"] == 0
    assert summary["model_inputs"] == 0
    assert summary["safe_v0_candidates"] == 6
    assert summary["blocked"] >= 8
    assert summary["framework_only"] >= 4
    assert all(row.decision in ALLOWED_DECISIONS for row in rows)
    assert all(row.active_output_allowed == "no" for row in rows)
    assert all(row.model_input_allowed == "no" for row in rows)


def test_future_tools_specs_exist_for_every_matrix_row() -> None:
    rows = load_future_tools_status_matrix()

    for row in rows:
        path = Path(row.docs_spec)
        assert path.exists(), f"missing spec for {row.tool_name}: {path}"


def test_future_tools_blocked_items_do_not_claim_safe_output() -> None:
    rows = load_future_tools_status_matrix()

    blocked = [row for row in rows if row.is_blocked]
    assert blocked
    for row in blocked:
        assert row.scaffold_status == "Roadmap card only"
        assert row.active_output_allowed == "no"
        assert row.model_input_allowed == "no"
        assert row.output_type != "Framework only"


def test_safe_v0_tool_set_is_limited_to_framework_only_candidates() -> None:
    rows = load_future_tools_status_matrix()
    safe = safe_v0_tools(rows)

    assert {row.tool_id for row in safe} == {
        "roster_weakness_tracker",
        "future_pick_planning",
        "upcoming_draft_prep",
        "keeper_deadline_prep",
        "drop_deadline_prep",
        "trade_deadline_prep",
    }
    assert all(row.active_output_allowed == "no" for row in safe)
    assert all(row.model_input_allowed == "no" for row in safe)


def test_roster_weakness_tracker_is_descriptive_only() -> None:
    rows = parse_manual_roster_text(
        "Player One,QB,24,12\nPlayer Two,RB,30,80\nPlayer Three,WR,,"
    )

    position_summary = roster_position_summary(rows)
    age_summary = roster_age_bucket_summary(rows)
    rank_summary = roster_dynasty_rank_bucket_summary(rows)

    assert rows[2]["age"] == "Not enough information"
    assert any(row["position"] == "QB" and row["player_count"] == "1" for row in position_summary)
    assert any(row["age_bucket"] == "Not enough information" for row in age_summary)
    assert any(row["dynasty_rank_bucket"] == "73+" for row in rank_summary)
    assert all("recommendation" in row["guardrail"] for row in position_summary)


def test_future_pick_planning_does_not_value_picks() -> None:
    state = {
        "trade_events": [
            {
                "team_a": "NWR",
                "team_b": "WhoDat",
                "team_a_assets": [],
                "team_b_assets": [
                    {
                        "asset_type": "future_pick",
                        "pick_year": "2028",
                        "pick_label": "2028 1st",
                        "display_label": "2028 1st",
                    }
                ],
                "notes": "manual trade note",
            }
        ]
    }

    ledger = future_pick_ledger_from_runtime_state(state)
    manual = parse_manual_future_pick_text("2029,2nd,acquired,Team X,manual note")

    assert ledger[0]["pick_year"] == "2028"
    assert ledger[0]["direction"] == "Received by Team A"
    assert manual[0]["guardrail"] == "Planning ledger only; no pick valuation."
    joined = " ".join(str(row) for row in [*ledger, *manual]).lower()
    assert "valuation" in joined
    assert "market_value" not in joined
    assert "dynastyprocess" not in joined


def test_deadline_prep_toolkit_is_manual_checklist_only() -> None:
    rows = deadline_checklist(
        "trade_deadline_prep",
        date_text="2026-10-31",
        notes="manual review",
    )

    assert rows
    assert rows[0]["status"] == "Not Started"
    assert rows[0]["manual_deadline"] == "2026-10-31"
    assert all("not a recommendation or model output" in row["guardrail"] for row in rows)


def test_upcoming_draft_prep_is_manual_only() -> None:
    setup = upcoming_draft_setup_checklist(notes="manual note")
    questions = upcoming_draft_questions_checklist(notes="manual question note")
    readiness = upcoming_draft_data_readiness_checklist(notes="manual readiness note")
    roster_notes = parse_manual_table_text(
        "WR,short,long,depth,watch",
        (
            "position",
            "short_term_need",
            "long_term_need",
            "depth_concern_notes",
            "watch_notes",
        ),
        source="Manual input / display-only",
        guardrail="Planning notes only; no position target recommendation.",
    )

    assert len(setup) == 9
    assert len(questions) == 5
    assert len(readiness) == 7
    assert setup[0]["status"] == "Not Started"
    assert "not a recommendation" in setup[0]["guardrail"]
    assert "not a target plan" in questions[0]["guardrail"]
    assert "not a refresh" in readiness[0]["guardrail"]
    assert roster_notes[0]["guardrail"] == (
        "Planning notes only; no position target recommendation."
    )
    joined = " ".join(str(row) for row in [*setup, *questions, *readiness, *roster_notes]).lower()
    assert "valuation" not in joined
    assert "model score" not in joined
