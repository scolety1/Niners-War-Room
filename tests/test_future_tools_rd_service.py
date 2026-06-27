from __future__ import annotations

from pathlib import Path

from src.services.future_tools_rd_service import (
    ALLOWED_DECISIONS,
    future_tools_summary,
    group_future_tools,
    load_future_tools_status_matrix,
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
    "Position Target Plan",
    "Keeper Deadline Prep",
    "Drop Deadline Prep",
    "Trade Deadline Prep",
    "Playoff Push Planner",
}


def test_future_tools_matrix_loads_all_expected_tools() -> None:
    rows = load_future_tools_status_matrix()

    assert len(rows) == 14
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
