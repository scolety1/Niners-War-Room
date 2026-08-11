from __future__ import annotations

from pathlib import Path

from src.services.future_tools_rd_service import (
    ALLOWED_DECISIONS,
    REFRESH_HEALTH_WAITING,
    SAFE_REFRESH_CONTEXT_READY,
    append_manual_csv_row,
    deadline_checklist,
    development_lab_readiness_rows,
    future_pick_ledger_from_runtime_state,
    future_tool_gate_badge_rows,
    future_tools_summary,
    group_future_tools,
    load_future_tools_status_matrix,
    nflverse_waiting_context_rows,
    parse_manual_future_pick_text,
    parse_manual_roster_text,
    parse_manual_table_text,
    roster_age_bucket_summary,
    roster_dynasty_rank_bucket_summary,
    roster_position_summary,
    safe_v0_tools,
    tool_refresh_waiting_rows,
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


def test_future_tools_gate_badges_keep_blocked_tools_inactive() -> None:
    rows = load_future_tools_status_matrix()
    badge_rows = future_tool_gate_badge_rows(rows)

    assert len(badge_rows) == len(rows)
    assert all(row["Active output"] == "no" for row in badge_rows)
    assert all(row["Model input"] == "no" for row in badge_rows)
    assert any(row["Gate badge"] == "Safe manual sibling exists" for row in badge_rows)
    assert any(row["Gate badge"] == "Needs dataset refresh" for row in badge_rows)
    assert any(
        row["Gate badge"] == "Dataset exists but not approved for model/rank logic"
        for row in badge_rows
    )
    assert any(row["Manual sibling route"] == "Inactive roadmap idea" for row in badge_rows)


def test_development_lab_readiness_marks_nflverse_context_display_ready() -> None:
    rows = load_future_tools_status_matrix()
    readiness = development_lab_readiness_rows(
        rows,
        local_state_by_tool={"future_pick_planning": "Saved locally"},
    )

    assert len(readiness) == 6
    assert {row["Readiness"] for row in readiness} == {"Manual only"}
    assert {row["nflverse context"] for row in readiness} == {
        SAFE_REFRESH_CONTEXT_READY
    }
    assert {row["Missing data display"] for row in readiness} == {
        "Not enough information"
    }
    assert any(row["Saved state"] == "Saved locally" for row in readiness)


def test_nflverse_context_status_keeps_schedule_and_identity_caveats() -> None:
    rows = nflverse_waiting_context_rows()
    roster_rows = tool_refresh_waiting_rows("roster_weakness_tracker")
    deadline_rows = tool_refresh_waiting_rows("trade_deadline_prep")

    assert len(rows) >= 6
    classifications = {row["Classification"] for row in rows}
    assert SAFE_REFRESH_CONTEXT_READY in classifications
    assert REFRESH_HEALTH_WAITING in classifications
    assert "Needs identity review" in classifications
    assert any(row["Current display"] == "Not enough information" for row in rows)
    assert roster_rows
    assert deadline_rows


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
    assert all("not active output" in row["guardrail"] for row in position_summary)


def test_guided_planning_rows_preserve_commas_in_notes() -> None:
    text = append_manual_csv_row(
        "",
        ("Player One", "WR", "23", "19", "Starter, but monitor role", "00-1"),
    )
    rows = parse_manual_roster_text(text)

    assert rows[0]["notes"] == "Starter, but monitor role"
    assert rows[0]["nwr_player_id"] == "00-1"


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
    assert manual[0]["guardrail"] == "Planning ledger only; no pick/trade math."
    joined = " ".join(str(row) for row in [*ledger, *manual]).lower()
    assert "valuation" not in joined
    assert "market_value" not in joined
    assert "dynastyprocess" not in joined


def test_deadline_prep_toolkit_is_manual_checklist_only() -> None:
    rows = deadline_checklist(
        "trade_deadline_prep",
        date_text="2026-10-31",
        notes="manual review",
    )

    assert rows
    assert rows[0]["status"] == "To do"
    assert rows[0]["manual_deadline"] == "2026-10-31"
    assert rows[-1]["status"] == SAFE_REFRESH_CONTEXT_READY
    assert all("model output" in row["guardrail"] for row in rows[:4])

    completed = deadline_checklist(
        "trade_deadline_prep",
        completed_tasks=("Confirm league trade deadline",),
    )
    assert completed[0]["status"] == "Done"
    assert completed[1]["status"] == "To do"


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
        guardrail="Planning notes only; no position target plan.",
    )

    assert len(setup) == 9
    assert len(questions) == 5
    assert len(readiness) == 10
    assert setup[0]["status"] == "Not Started"
    assert "not active output" in setup[0]["guardrail"]
    assert "not a target plan" in questions[0]["guardrail"]
    assert "not a refresh" in readiness[0]["guardrail"]
    assert readiness[-1]["status"] == SAFE_REFRESH_CONTEXT_READY
    assert roster_notes[0]["guardrail"] == (
        "Planning notes only; no position target plan."
    )
    joined = " ".join(str(row) for row in [*setup, *questions, *readiness, *roster_notes]).lower()
    assert "valuation" not in joined
    assert "model score" not in joined
