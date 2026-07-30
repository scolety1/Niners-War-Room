from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import src.services.draft_day_app_v1_service as draft_day_service
from src.services.draft_day_trade_lab_service import (
    TradePlayerUniverseError,
    add_trade_item,
    build_trade_item_lookup,
    clear_trade_state,
    display_package_summary,
    display_trade_item_rows,
    empty_trade_state,
    package_summary_rows,
    parse_trade_asset_text,
    pick_context_options,
    player_key,
    player_options,
    remove_trade_item,
    review_trade_package,
    trade_item_rows,
    validate_trade_player_universe,
)


def _board() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Premium RB",
                "position": "RB",
                "nfl_team": "SF",
                "final_tier": "Tier 1",
                "position_rank": 1,
                "final_board_score_visible": "95.0",
                "risk_notes": "",
            },
            {
                "final_board_rank": 20,
                "player": "Depth WR",
                "position": "WR",
                "nfl_team": "DAL",
                "final_tier": "Tier 2",
                "position_rank": 9,
                "final_board_score_visible": "60.0",
                "risk_notes": "role check",
            },
        ]
    )


def _trade_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Premium RB",
                "position": "RB",
                "nfl_team": "SF",
                "visible_score_for_context": "95.0",
                "tier_movement_note": "premium tier",
                "position_scarcity_note": "scarce RB",
                "pick_window_note": "",
                "risk_manual_review_notes": "",
            },
            {
                "final_board_rank": 20,
                "player": "Depth WR",
                "position": "WR",
                "nfl_team": "DAL",
                "visible_score_for_context": "60.0",
                "tier_movement_note": "same tier",
                "position_scarcity_note": "",
                "pick_window_note": "late pick window",
                "risk_manual_review_notes": "role check",
            },
        ]
    )


def _dynasty_board(row_count: int = 2) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "player_id": str(9000 + index),
                "player_name": f"Current Player {index + 1}",
                "position": ("RB", "WR")[index % 2],
                "nfl_team": ("SF", "DAL")[index % 2],
                "nwr_rank": index + 1,
                "nwr_dynasty_score": 90 - index,
                "pool_status": "MY TEAM" if index == 0 else "OTHER TEAM",
                "roster_status": "rostered",
                "is_rookie": "1" if index == 45 else "0",
                "risk_level": "LOW",
            }
            for index in range(row_count)
        ]
    )
    if row_count > 100:
        frame.loc[45, "player_name"] = "Ashton Jeanty"
        frame.loc[100, "player_name"] = "Patrick Mahomes"
    return frame


def _write_dynasty_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    frame: pd.DataFrame,
    *,
    expected_hash: str | None = None,
) -> Path:
    root = tmp_path / "dynasty"
    root.mkdir()
    path = root / draft_day_service.DYNASTY_BOARD_FILE_NAME
    frame.to_csv(path, index=False)
    monkeypatch.setenv("NWR_DYNASTY_RANKINGS_ROOT", str(root))
    monkeypatch.setattr(
        draft_day_service,
        "EXPECTED_DYNASTY_RANKINGS_HASH",
        expected_hash or draft_day_service.file_sha256(path),
    )
    return path


def _pick_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Premium RB",
                "position": "RB",
                "nfl_team": "SF",
                "rookie_tier_display_only": "Tier 1",
                "pick_window_note": "round=1; pick=3",
                "caveat": "display-only pick context",
            }
        ]
    )


def test_trade_builder_add_remove_and_clear_state() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    players = player_options(lookup)
    premium = players["#1 - Premium RB (RB, SF)"]
    state = add_trade_item(empty_trade_state(), "give", premium)

    assert state["give"] == [premium]

    state = remove_trade_item(state, "give", premium)

    assert state == empty_trade_state()
    assert clear_trade_state() == empty_trade_state()


def test_dynasty_schema_exposes_complete_player_universe() -> None:
    lookup = build_trade_item_lookup(
        _dynasty_board(240),
        pd.DataFrame(),
        pd.DataFrame(),
        require_complete_player_universe=True,
    )
    players = player_options(lookup)

    assert len(players) == 240
    assert len(set(players.values())) == 240
    first_key = players["Dynasty #1 - Current Player 1 (RB, SF)"]
    first = lookup[first_key]
    assert first_key == "player:id:9000"
    assert first["nwr_player_id"] == "9000"
    assert first["player"] == "Current Player 1"
    assert first["rank_source"] == "Dynasty Rank"
    assert first["dynasty_rank"] == 1
    assert first["final_board_rank"] == ""
    assert first["roster_context"] == "MY TEAM"
    assert first["data_status"] == "Current production player universe"


@pytest.mark.parametrize(
    ("case", "mutate", "expected"),
    (
        (
            "frozen_or_truncated_66",
            lambda frame: frame.head(66),
            "requires exactly 240 current players",
        ),
        (
            "prohibited_368",
            lambda frame: pd.concat(
                [
                    frame,
                    frame.iloc[:128].assign(
                        player_id=lambda value: value["player_id"] + "-extra",
                        nwr_rank=lambda value: value["nwr_rank"] + 240,
                    ),
                ],
                ignore_index=True,
            ),
            "requires exactly 240 current players",
        ),
        (
            "duplicate_player_id",
            lambda frame: frame.assign(
                player_id=[
                    frame.iloc[0]["player_id"],
                    frame.iloc[0]["player_id"],
                    *frame.iloc[2:]["player_id"].tolist(),
                ]
            ),
            "duplicate player IDs",
        ),
        (
            "name_only_identity",
            lambda frame: frame.drop(columns=["player_id"]),
            "missing required fields: player_id",
        ),
        (
            "blank_player_id",
            lambda frame: frame.assign(
                player_id=["", *frame.iloc[1:]["player_id"].tolist()]
            ),
            "blank player IDs",
        ),
        (
            "established_veteran_removed",
            lambda frame: frame.iloc[1:].reset_index(drop=True),
            "requires exactly 240 current players",
        ),
        (
            "dynasty_rank_relabelled",
            lambda frame: frame.rename(columns={"nwr_rank": "final_board_rank"}),
            "missing required fields: nwr_rank",
        ),
        (
            "unknown_ownership_promoted_to_free_agent",
            lambda frame: frame.assign(
                pool_status=[
                    "FREE AGENT",
                    *frame.iloc[1:]["pool_status"].tolist(),
                ]
            ),
            "unapproved ownership states: FREE AGENT",
        ),
        (
            "opaque_trade_winner",
            lambda frame: frame.assign(opaque_trade_result="NWR gets"),
            "prohibited recommendation or hidden-sort fields: opaque_trade_result",
        ),
        (
            "outcome_v3_hidden_sort",
            lambda frame: frame.assign(
                outcome_v3_hidden_sort=list(range(240, 0, -1))
            ),
            "prohibited recommendation or hidden-sort fields: outcome_v3_hidden_sort",
        ),
    ),
)
def test_complete_player_universe_mutations_fail_closed(
    case: str,
    mutate,
    expected: str,
) -> None:
    del case
    mutated = mutate(_dynasty_board(240).copy())

    errors = validate_trade_player_universe(mutated)

    assert expected in " ".join(errors)
    with pytest.raises(TradePlayerUniverseError, match=expected):
        build_trade_item_lookup(
            mutated,
            pd.DataFrame(),
            _pick_context(),
            require_complete_player_universe=True,
        )


def test_complete_player_universe_uses_player_id_and_keeps_pick_identity_separate() -> None:
    frame = _dynasty_board(240)
    frame.loc[0, "player_name"] = "2026 1.01"
    picks = _pick_context().copy()
    picks.loc[0, "player"] = "2026 1.01"
    lookup = build_trade_item_lookup(
        frame,
        pd.DataFrame(),
        picks,
        require_complete_player_universe=True,
    )

    player_keys = set(player_options(lookup).values())
    pick_keys = set(pick_context_options(lookup).values())
    assert "player:id:9000" in player_keys
    assert player_keys.isdisjoint(pick_keys)
    assert all(key.startswith("player:id:") for key in player_keys)
    assert all(key.startswith("pick_context:") for key in pick_keys)


def test_dynasty_rank_controls_selector_order_and_labels_without_outcome_sorting() -> None:
    frame = _dynasty_board(240)
    frame["final_board_rank"] = list(range(240, 0, -1))
    frame["nwr_rank"] = frame["nwr_rank"].astype(object)
    frame.loc[239, "nwr_rank"] = ""
    lookup = build_trade_item_lookup(
        frame,
        pd.DataFrame(),
        pd.DataFrame(),
        require_complete_player_universe=True,
    )
    labels = list(player_options(lookup))

    assert labels[0].startswith("Dynasty #1 - Current Player 1")
    assert labels[-1].startswith("Dynasty rank unavailable - Current Player 240")
    assert not any("Final Board" in label or "Outcome" in label for label in labels)


def test_trading_lab_page_wires_selector_to_dynasty_bundle_without_frozen_fallback() -> None:
    page = (
        Path(__file__).resolve().parents[1] / "app" / "pages" / "23_trading_lab_v1.py"
    ).read_text(encoding="utf-8")

    assert "dynasty_bundle = load_dynasty_rankings()" in page
    assert "lookup = build_trade_item_lookup(" in page
    assert "    dynasty_bundle.frame," in page
    assert "source_context_counts(dynasty_bundle.frame" in page
    assert "require_complete_player_universe=True" in page
    assert "validate_trade_player_universe(dynasty_bundle.frame)" in page
    assert "build_trade_item_lookup(bundle.frame" not in page
    assert "The frozen draft-board checkpoint will not be substituted" in page
    assert "complete 240-player production universe" in page


def test_trading_lab_route_renders_complete_universe_rookie_veteran_and_picks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_dynasty_artifact(tmp_path, monkeypatch, _dynasty_board(240))
    before = tuple(sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")))

    at = AppTest.from_file("app/pages/23_trading_lab_v1.py").run(timeout=40)

    after = tuple(sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")))
    assert not at.exception
    assert not at.error
    assert after == before
    player_selectors = [item for item in at.selectbox if item.label == "Add player"]
    pick_selectors = [item for item in at.selectbox if item.label == "Add pick/context"]
    assert len(player_selectors) == 2
    assert all(len(item.options) == 240 for item in player_selectors)
    assert all(len(set(item.options)) == 240 for item in player_selectors)
    assert all(
        any("Ashton Jeanty" in option for option in item.options)
        for item in player_selectors
    )
    assert all(
        any("Patrick Mahomes" in option for option in item.options)
        for item in player_selectors
    )
    assert pick_selectors and all(item.options for item in pick_selectors)
    source_notices = [item.value for item in at.info if "Current player universe:" in item.value]
    assert len(source_notices) == 1
    assert "Full Dynasty Rankings | GREEN | 240 rows" in source_notices[0]
    assert any(
        "Frozen Final Draft Board V1 is draft/pick context only" in item.value
        for item in at.caption
    )
    assert not any(
        phrase in item.value.casefold()
        for item in (*at.success, *at.info, *at.warning, *at.error)
        for phrase in ("trade winner:", "recommended side:", "accept this trade")
    )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda frame: frame.head(66),
        lambda frame: pd.concat([frame, frame.iloc[:128]], ignore_index=True),
        lambda frame: frame.assign(
            player_id=[
                frame.iloc[0]["player_id"],
                frame.iloc[0]["player_id"],
                *frame.iloc[2:]["player_id"].tolist(),
            ]
        ),
        lambda frame: frame.drop(columns=["player_id"]),
        lambda frame: frame.assign(
            player_id=["", *frame.iloc[1:]["player_id"].tolist()]
        ),
        lambda frame: frame.iloc[1:].reset_index(drop=True),
        lambda frame: frame.rename(columns={"nwr_rank": "final_board_rank"}),
        lambda frame: frame.assign(
            pool_status=["FREE AGENT", *frame.iloc[1:]["pool_status"].tolist()]
        ),
        lambda frame: frame.assign(opaque_trade_result="NWR gets"),
        lambda frame: frame.assign(
            outcome_v3_hidden_sort=list(range(240, 0, -1))
        ),
    ),
)
def test_trading_lab_route_fails_closed_for_mutated_player_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate,
) -> None:
    mutated = mutate(_dynasty_board(240).copy())
    _write_dynasty_artifact(tmp_path, monkeypatch, mutated)

    at = AppTest.from_file("app/pages/23_trading_lab_v1.py").run(timeout=40)

    assert not at.exception
    assert any(
        "requires the approved hash-validated 240-player production universe"
        in item.value
        for item in at.error
    )
    assert not any(item.label == "Add player" for item in at.selectbox)


def test_trading_lab_route_does_not_silently_fallback_after_hash_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_dynasty_artifact(
        tmp_path,
        monkeypatch,
        _dynasty_board(240),
        expected_hash="0" * 64,
    )

    at = AppTest.from_file("app/pages/23_trading_lab_v1.py").run(timeout=40)

    assert not at.exception
    assert any("hash mismatch" in item.value.lower() for item in at.error)
    assert not any(item.label == "Add player" for item in at.selectbox)


def test_trade_summary_uses_visible_context_and_not_enough_information() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    players = player_options(lookup)
    state = add_trade_item(empty_trade_state(), "give", players["#20 - Depth WR (WR, DAL)"])
    state = add_trade_item(state, "get", players["#1 - Premium RB (RB, SF)"])

    summary = package_summary_rows(state, lookup)
    review = review_trade_package(state, lookup)

    assert set(summary["side"]) == {"NWR gives", "NWR gets"}
    assert review.status == "Context ready for manual review"
    assert review.missing_context_display == "Manual review required"
    assert review.rank_context == "Player-rank labels present"
    display = display_package_summary(summary)
    assert "Best Player Rank" in display.columns
    assert "Visible Score Sum" not in display.columns


def test_pick_context_can_be_added_but_does_not_create_numeric_pick_context() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    picks = pick_context_options(lookup)
    pick_key = next(iter(picks.values()))
    state = add_trade_item(empty_trade_state(), "give", pick_key)
    state = add_trade_item(
        state,
        "get",
        player_options(lookup)["#1 - Premium RB (RB, SF)"],
    )

    review = review_trade_package(state, lookup)
    rows = trade_item_rows(state, lookup)

    assert review.status == "Pick-only context present"
    assert "no numeric pick context is inferred" in review.explanation.lower()
    pick_rows = rows.loc[rows["asset_type"] == "Pick context"]
    assert set(pick_rows["data_status"]) == {
        "Display-only context; no standalone numeric pick context"
    }
    assert "visible_score_for_context" not in rows.columns


def test_display_items_hide_internal_keys() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    state = add_trade_item(
        empty_trade_state(),
        "give",
        player_options(lookup)["#1 - Premium RB (RB, SF)"],
    )

    display = display_trade_item_rows(trade_item_rows(state, lookup))

    assert "Asset" in display.columns
    assert "item_key" not in display.columns
    assert not any("hidden" in column.lower() for column in display.columns)


def test_player_key_is_visible_board_identity() -> None:
    row = _board().iloc[0]

    assert player_key(row) == "1|Premium RB|RB|SF"


def test_trade_asset_parser_keeps_pick_labels_without_pricing() -> None:
    rows = parse_trade_asset_text(
        "2026 1.04, 2026 2.03, 2028 1st, 2028 2nd, 2027 3rd, unknown text"
    )

    by_raw = {row["raw_text"]: row for row in rows}
    assert by_raw["2026 1.04"]["pick_label"] == "1.04"
    assert by_raw["2026 2.03"]["display_label"] == "2026 2.03"
    assert by_raw["2028 1st"]["asset_type"] == "future_pick"
    assert by_raw["2028 2nd"]["round"] == 2
    assert by_raw["2027 3rd"]["round"] == 3
    assert by_raw["unknown text"]["status"] == "REVIEW_NEEDED"


def test_trading_lab_service_has_no_market_or_pick_pricing_helpers() -> None:
    import src.services.draft_day_trade_lab_service as trade_lab_service

    blocked_helpers = [
        "lookup_pick_market_value",
        "lookup_player_market_value",
        "summarize_trade_package_market",
        "classify_market_trade_gap",
        "display_market_package_rows",
        "display_market_totals",
    ]
    for helper in blocked_helpers:
        assert not hasattr(trade_lab_service, helper)


def test_manual_review_language_is_not_automatic_recommendation() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    players = player_options(lookup)
    state = add_trade_item(empty_trade_state(), "give", players["#20 - Depth WR (WR, DAL)"])
    state = add_trade_item(state, "get", players["#1 - Premium RB (RB, SF)"])

    review = review_trade_package(state, lookup)
    text = " ".join((review.status, review.missing_context_display, review.explanation))

    assert "manual review" in text.lower()
    for forbidden in ("looks favorable", "risky", "fair", "winner", "score gap"):
        assert forbidden not in text.lower()
