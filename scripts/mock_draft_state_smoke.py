from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.draft_state_service import (  # noqa: E402
    AvailablePlayer,
    assert_draft_state_valid,
    create_empty_draft_state,
    draft_pick_history,
    mark_player_drafted,
    validate_draft_state,
)


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append((name, passed, detail))

    pick_rows = [
        {
            "overall_pick": 1,
            "round": 1,
            "round_pick": 1,
            "pick_label": "1.01",
            "current_owner": "Opponent A",
            "original_owner": "Opponent A",
            "is_my_pick": False,
        },
        {
            "overall_pick": 2,
            "round": 1,
            "round_pick": 2,
            "pick_label": "1.02",
            "current_owner": "Niners",
            "original_owner": "Niners",
            "is_my_pick": True,
        },
        {
            "overall_pick": 3,
            "round": 1,
            "round_pick": 3,
            "pick_label": "1.03",
            "current_owner": "Opponent B",
            "original_owner": "Opponent B",
            "is_my_pick": False,
        },
    ]
    available_rows = [
        {
            "asset_id": "rookie:alpha_wr",
            "player": "Alpha WR",
            "position": "WR",
            "nfl_team": "Rookie Pool",
            "asset_type": "Rookie",
            "asset_lifecycle": "incoming_rookie",
            "stats_model_value": 91.0,
            "confidence": 88.0,
            "overall_rank": 1,
        },
        {
            "asset_id": "veteran:steady_rb",
            "player": "Steady RB",
            "position": "RB",
            "nfl_team": "FA",
            "asset_type": "Available Veteran",
            "asset_lifecycle": "available_veteran",
            "stats_model_value": 74.0,
            "confidence": 76.0,
            "overall_rank": 2,
        },
    ]

    state = create_empty_draft_state(pick_rows=pick_rows, available_rows=available_rows)
    state = mark_player_drafted(state, "rookie:alpha_wr", overall_pick=1)
    record("validate clean draft state", validate_draft_state(state) == ())

    try:
        assert_draft_state_valid(state)
    except ValueError as exc:
        record("assert clean draft state", False, str(exc))
    else:
        record("assert clean draft state", True)

    history = draft_pick_history(state)
    record(
        "deterministic draft pick history",
        [(row.overall_pick, row.asset_id) for row in history]
        == [(1, "rookie:alpha_wr")],
    )

    try:
        create_empty_draft_state(
            pick_rows=pick_rows,
            available_rows=[*available_rows, {**available_rows[0], "player": "Dupe"}],
        )
    except ValueError as exc:
        record(
            "duplicate available asset rejection",
            "Available player asset appears more than once" in str(exc),
            str(exc),
        )
    else:
        record("duplicate available asset rejection", False, "duplicate accepted")

    try:
        create_empty_draft_state(
            pick_rows=[*pick_rows, pick_rows[0]],
            available_rows=available_rows,
        )
    except ValueError as exc:
        record(
            "duplicate pick-number rejection",
            "Draft pick appears more than once" in str(exc),
            str(exc),
        )
    else:
        record("duplicate pick-number rejection", False, "duplicate accepted")

    drafted = state.drafted_players[0]
    overlap_player = AvailablePlayer(
        asset_id=drafted.asset_id,
        player=drafted.player,
        position=drafted.position,
        nfl_team=drafted.nfl_team,
        asset_type=drafted.asset_type,
        asset_lifecycle=drafted.asset_lifecycle,
        why_available=drafted.why_available,
        stats_model_value=drafted.stats_model_value,
        market_value=drafted.market_value,
        market_edge=drafted.market_edge,
        confidence=drafted.confidence,
        warning="",
        draft_rank=1,
        do_not_draft_before_pick=drafted.do_not_draft_before_pick,
        recommended_range=drafted.recommended_range,
    )
    overlap_state = replace(
        state,
        available_players=(*state.available_players, overlap_player),
    )
    record(
        "available/drafted overlap detection",
        any(
            "both available and drafted" in issue
            for issue in validate_draft_state(overlap_state)
        ),
    )

    stale_current_state = replace(state, current_pick=3)
    record(
        "stale current_pick detection",
        any(
            "Current pick is inconsistent" in issue
            for issue in validate_draft_state(stale_current_state)
        ),
    )

    stale_my_picks_state = replace(state, my_pick_numbers=(3,))
    record(
        "stale my_pick_numbers detection",
        any(
            "My pick numbers are inconsistent" in issue
            for issue in validate_draft_state(stale_my_picks_state)
        ),
    )

    try:
        mark_player_drafted(state, "veteran:steady_rb", overall_pick=99)
    except ValueError as exc:
        record(
            "invalid explicit pick-number rejection",
            "outside the draft board" in str(exc),
            str(exc),
        )
    else:
        record("invalid explicit pick-number rejection", False, "invalid pick accepted")

    failed = [(name, detail) for name, passed, detail in checks if not passed]
    for name, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        suffix = f" - {detail}" if detail else ""
        print(f"{status}: {name}{suffix}")

    print(f"SUMMARY: {len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
