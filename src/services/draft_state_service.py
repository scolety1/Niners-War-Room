from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from src.services.draft_ux_service import DRAFT_TEAMS, DRAFT_TOTAL_PICKS


@dataclass(frozen=True)
class DraftPick:
    overall_pick: int
    round: int
    round_pick: int
    pick_label: str
    current_owner: str
    original_owner: str
    is_my_pick: bool


@dataclass(frozen=True)
class AvailablePlayer:
    asset_id: str
    player: str
    position: str
    nfl_team: str
    asset_type: str
    asset_lifecycle: str
    why_available: str
    stats_model_value: float
    market_value: float
    market_edge: float
    confidence: float
    warning: str
    draft_rank: int
    do_not_draft_before_pick: int | None
    recommended_range: str


@dataclass(frozen=True)
class DraftedPlayer:
    pick: DraftPick
    asset_id: str
    player: str
    position: str
    nfl_team: str
    asset_type: str
    asset_lifecycle: str
    why_available: str
    stats_model_value: float
    market_value: float
    market_edge: float
    confidence: float
    do_not_draft_before_pick: int | None
    recommended_range: str


@dataclass(frozen=True)
class DraftBoardState:
    picks: tuple[DraftPick, ...]
    drafted_players: tuple[DraftedPlayer, ...]
    available_players: tuple[AvailablePlayer, ...]
    current_pick: int | None
    my_pick_numbers: tuple[int, ...]


@dataclass(frozen=True)
class DraftPickGridCell:
    overall_pick: int
    round: int
    round_pick: int
    pick_label: str
    owner: str
    is_my_pick: bool
    is_current_pick: bool
    is_selected_pick: bool
    drafted_player: str
    drafted_position: str
    button_label: str
    status_label: str


@dataclass(frozen=True)
class DraftOptionRow:
    asset_id: str
    player: str
    position: str
    asset_type: str
    asset_lifecycle: str
    stats_model_value: float
    market_value: float
    market_edge: float
    confidence: float
    warning: str
    reach_value_label: str


@dataclass(frozen=True)
class BestRemainingPositionRow:
    position: str
    asset_id: str
    player: str
    asset_type: str
    asset_lifecycle: str
    stats_model_value: float
    confidence: float


@dataclass(frozen=True)
class RecentDraftPickRow:
    pick_label: str
    owner: str
    player: str
    position: str
    asset_type: str
    asset_lifecycle: str


@dataclass(frozen=True)
class PickGuardrailStatus:
    selected_pick: int | None
    current_pick: int | None
    selected_pick_label: str
    current_pick_label: str
    is_current_pick: bool
    is_prior_pick: bool
    is_future_pick: bool
    is_filled_pick: bool
    edit_mode: bool
    warning: str


@dataclass(frozen=True)
class DraftProgressSummary:
    current_pick_label: str
    current_owner: str
    next_my_pick_label: str
    picks_until_my_pick: int | None
    drafted_count: int
    available_count: int
    total_picks: int


def create_empty_draft_state(
    *,
    pick_rows: Sequence[Mapping[str, object]] | None = None,
    available_rows: Sequence[Mapping[str, object]] | None = None,
) -> DraftBoardState:
    picks = _draft_picks_from_rows(pick_rows or [])
    available_players = _available_players_from_rows(available_rows or [])
    return _with_recomputed_current_pick(
        DraftBoardState(
            picks=picks,
            drafted_players=(),
            available_players=available_players,
            current_pick=1 if picks else None,
            my_pick_numbers=tuple(pick.overall_pick for pick in picks if pick.is_my_pick),
        )
    )


def mark_player_drafted(
    state: DraftBoardState,
    asset_id: str,
    *,
    overall_pick: int | None = None,
) -> DraftBoardState:
    pick_number = overall_pick or state.current_pick
    if pick_number is None:
        raise ValueError("Cannot draft a player because the draft has no current pick.")
    pick = _find_pick(state, pick_number)
    if _drafted_at_pick(state, pick_number) is not None:
        raise ValueError(f"Pick {pick_number} already has a drafted player.")
    if _drafted_asset(state, asset_id) is not None:
        raise ValueError(f"Player asset {asset_id} is already drafted.")
    player = _find_available_player(state, asset_id)
    drafted = DraftedPlayer(
        pick=pick,
        asset_id=player.asset_id,
        player=player.player,
        position=player.position,
        nfl_team=player.nfl_team,
        asset_type=player.asset_type,
        asset_lifecycle=player.asset_lifecycle,
        why_available=player.why_available,
        stats_model_value=player.stats_model_value,
        market_value=player.market_value,
        market_edge=player.market_edge,
        confidence=player.confidence,
        do_not_draft_before_pick=player.do_not_draft_before_pick,
        recommended_range=player.recommended_range,
    )
    next_state = replace(
        state,
        drafted_players=_sorted_drafted((*state.drafted_players, drafted)),
        available_players=tuple(
            row for row in state.available_players if row.asset_id != asset_id
        ),
    )
    return _with_recomputed_current_pick(next_state)


def replace_drafted_player_at_pick(
    state: DraftBoardState,
    asset_id: str,
    *,
    overall_pick: int,
) -> DraftBoardState:
    pick = _find_pick(state, overall_pick)
    existing = _drafted_at_pick(state, overall_pick)
    if existing is None:
        return mark_player_drafted(state, asset_id, overall_pick=overall_pick)
    already_drafted = _drafted_asset(state, asset_id)
    if already_drafted is not None and already_drafted.pick.overall_pick != overall_pick:
        raise ValueError(f"Player asset {asset_id} is already drafted.")
    if already_drafted is not None and already_drafted.pick.overall_pick == overall_pick:
        return state
    replacement = _find_available_player(state, asset_id)
    restored = _available_player_from_drafted(existing, state=state)
    drafted = DraftedPlayer(
        pick=pick,
        asset_id=replacement.asset_id,
        player=replacement.player,
        position=replacement.position,
        nfl_team=replacement.nfl_team,
        asset_type=replacement.asset_type,
        asset_lifecycle=replacement.asset_lifecycle,
        why_available=replacement.why_available,
        stats_model_value=replacement.stats_model_value,
        market_value=replacement.market_value,
        market_edge=replacement.market_edge,
        confidence=replacement.confidence,
        do_not_draft_before_pick=replacement.do_not_draft_before_pick,
        recommended_range=replacement.recommended_range,
    )
    next_state = replace(
        state,
        drafted_players=_sorted_drafted(
            (
                *(
                    row
                    for row in state.drafted_players
                    if row.pick.overall_pick != overall_pick
                ),
                drafted,
            )
        ),
        available_players=_sorted_available(
            (
                *(
                    row
                    for row in state.available_players
                    if row.asset_id != replacement.asset_id
                ),
                restored,
            )
        ),
    )
    return _with_recomputed_current_pick(next_state)


def undo_pick(
    state: DraftBoardState,
    *,
    overall_pick: int | None = None,
) -> DraftBoardState:
    if not state.drafted_players:
        return state
    pick_number = overall_pick or max(
        drafted.pick.overall_pick for drafted in state.drafted_players
    )
    drafted = _drafted_at_pick(state, pick_number)
    if drafted is None:
        return state
    restored = _available_player_from_drafted(drafted, state=state)
    next_state = replace(
        state,
        drafted_players=tuple(
            row for row in state.drafted_players if row.pick.overall_pick != pick_number
        ),
        available_players=_sorted_available((*state.available_players, restored)),
    )
    return _with_recomputed_current_pick(next_state)


def reset_mock(state: DraftBoardState) -> DraftBoardState:
    restored = [
        AvailablePlayer(
            **_available_player_payload_from_drafted(row, state=state)
        )
        for row in state.drafted_players
    ]
    return _with_recomputed_current_pick(
        replace(
            state,
            drafted_players=(),
            available_players=_sorted_available((*state.available_players, *restored)),
        )
    )


def available_players_after_picks(state: DraftBoardState) -> tuple[AvailablePlayer, ...]:
    drafted_ids = {row.asset_id for row in state.drafted_players}
    return tuple(row for row in state.available_players if row.asset_id not in drafted_ids)


def apply_draft_status_to_rankings(
    rows: Sequence[Mapping[str, object]],
    state: DraftBoardState,
) -> list[dict[str, object]]:
    drafted_by_asset = {row.asset_id: row for row in state.drafted_players}
    annotated_rows: list[dict[str, object]] = []
    for row in rows:
        annotated = dict(row)
        asset_id = str(row.get("asset_id") or "")
        drafted = drafted_by_asset.get(asset_id)
        if drafted is not None:
            annotated["draft_status"] = "drafted"
            annotated["drafted_pick"] = drafted.pick.pick_label
            annotated["drafted_owner"] = drafted.pick.current_owner
        else:
            annotated["draft_status"] = "available"
            annotated["drafted_pick"] = ""
            annotated["drafted_owner"] = ""
        annotated_rows.append(annotated)
    return annotated_rows


def search_available_players(
    state: DraftBoardState,
    query: str,
    *,
    limit: int = 25,
) -> tuple[AvailablePlayer, ...]:
    clean_query = query.strip().lower()
    players = available_players_after_picks(state)
    if not clean_query:
        return players[:limit]
    terms = [term for term in clean_query.split() if term]
    filtered = [
        row
        for row in players
        if all(
            term in _search_blob(row)
            for term in terms
        )
    ]
    return tuple(filtered[:limit])


def best_options_at_pick(
    state: DraftBoardState,
    *,
    overall_pick: int | None = None,
    limit: int = 10,
) -> tuple[AvailablePlayer, ...]:
    _ = overall_pick or state.current_pick
    return available_players_after_picks(state)[:limit]


def current_draft_pick(state: DraftBoardState) -> DraftPick | None:
    return next(
        (pick for pick in state.picks if pick.overall_pick == state.current_pick),
        None,
    )


def next_my_pick(state: DraftBoardState) -> DraftPick | None:
    if state.current_pick is None:
        return None
    return next(
        (
            pick
            for pick in state.picks
            if pick.is_my_pick and pick.overall_pick >= state.current_pick
        ),
        None,
    )


def draft_progress_summary(state: DraftBoardState) -> DraftProgressSummary:
    current = current_draft_pick(state)
    next_mine = next_my_pick(state)
    picks_until = None
    if current is not None and next_mine is not None:
        picks_until = max(0, next_mine.overall_pick - current.overall_pick)
    return DraftProgressSummary(
        current_pick_label=current.pick_label if current else "Done",
        current_owner=current.current_owner if current else "",
        next_my_pick_label=next_mine.pick_label if next_mine else "None",
        picks_until_my_pick=picks_until,
        drafted_count=len(state.drafted_players),
        available_count=len(available_players_after_picks(state)),
        total_picks=len(state.picks),
    )


def is_my_turn(state: DraftBoardState) -> bool:
    pick = current_draft_pick(state)
    return bool(pick and pick.is_my_pick)


def best_option_rows_at_pick(
    state: DraftBoardState,
    *,
    overall_pick: int | None = None,
    limit: int = 8,
    review_only: bool = False,
) -> tuple[DraftOptionRow, ...]:
    pick_number = overall_pick or state.current_pick
    options = best_options_at_pick(state, overall_pick=pick_number, limit=limit)
    return tuple(
        DraftOptionRow(
            asset_id=row.asset_id,
            player=row.player,
            position=row.position,
            asset_type=row.asset_type,
            asset_lifecycle=row.asset_lifecycle,
            stats_model_value=row.stats_model_value,
            market_value=row.market_value,
            market_edge=row.market_edge,
            confidence=row.confidence,
            warning=_option_warning(row.warning, review_only=review_only),
            reach_value_label=_reach_value_label(row, pick_number),
        )
        for row in options
    )


def best_remaining_by_position(
    state: DraftBoardState,
    *,
    positions: Sequence[str] = ("QB", "RB", "WR", "TE"),
    limit_per_position: int = 3,
) -> tuple[BestRemainingPositionRow, ...]:
    remaining = available_players_after_picks(state)
    rows: list[BestRemainingPositionRow] = []
    for position in positions:
        position_rows = [
            row for row in remaining if row.position.upper() == position.upper()
        ][:limit_per_position]
        rows.extend(
            BestRemainingPositionRow(
                position=row.position,
                asset_id=row.asset_id,
                player=row.player,
                asset_type=row.asset_type,
                asset_lifecycle=row.asset_lifecycle,
                stats_model_value=row.stats_model_value,
                confidence=row.confidence,
            )
            for row in position_rows
        )
    return tuple(rows)


def recent_drafted_players(
    state: DraftBoardState,
    *,
    limit: int = 6,
) -> tuple[RecentDraftPickRow, ...]:
    return tuple(
        RecentDraftPickRow(
            pick_label=row.pick.pick_label,
            owner=row.pick.current_owner,
            player=row.player,
            position=row.position,
            asset_type=row.asset_type,
            asset_lifecycle=row.asset_lifecycle,
        )
        for row in state.drafted_players[-limit:]
    )


def drafted_player_at_pick(
    state: DraftBoardState,
    overall_pick: int | None,
) -> DraftedPlayer | None:
    if overall_pick is None:
        return None
    return _drafted_at_pick(state, overall_pick)


def pick_guardrail_status(
    state: DraftBoardState,
    selected_pick: int | None,
) -> PickGuardrailStatus:
    current_pick_number = state.current_pick
    selected = _find_pick(state, selected_pick) if selected_pick is not None else None
    current = _find_pick(state, current_pick_number) if current_pick_number is not None else None
    selected_label = selected.pick_label if selected else ""
    current_label = current.pick_label if current else "Done"
    is_current = selected_pick is not None and selected_pick == current_pick_number
    is_prior = (
        selected_pick is not None
        and current_pick_number is not None
        and selected_pick < current_pick_number
    )
    is_future = (
        selected_pick is not None
        and current_pick_number is not None
        and selected_pick > current_pick_number
    )
    is_filled = drafted_player_at_pick(state, selected_pick) is not None
    edit_mode = is_filled
    warning = ""
    if edit_mode:
        warning = f"Edit mode: pick {selected_label} already has a player."
    elif is_prior:
        warning = (
            f"Selected pick {selected_label} is behind the current pick {current_label}. "
            "Assigning here is a correction."
        )
    elif is_future:
        warning = (
            f"Selected pick {selected_label} is ahead of the current pick {current_label}. "
            "Make sure you are not entering the wrong pick."
        )
    return PickGuardrailStatus(
        selected_pick=selected_pick,
        current_pick=current_pick_number,
        selected_pick_label=selected_label,
        current_pick_label=current_label,
        is_current_pick=is_current,
        is_prior_pick=is_prior,
        is_future_pick=is_future,
        is_filled_pick=is_filled,
        edit_mode=edit_mode,
        warning=warning,
    )


def draft_pick_grid_cells(
    state: DraftBoardState,
    *,
    selected_pick: int | None = None,
) -> tuple[DraftPickGridCell, ...]:
    drafted_by_pick = {row.pick.overall_pick: row for row in state.drafted_players}
    cells: list[DraftPickGridCell] = []
    for pick in state.picks:
        drafted = drafted_by_pick.get(pick.overall_pick)
        status_label = _pick_status_label(
            pick=pick,
            drafted=bool(drafted),
            current_pick=state.current_pick,
            selected_pick=selected_pick,
        )
        drafted_player = drafted.player if drafted else ""
        drafted_position = drafted.position if drafted else ""
        cells.append(
            DraftPickGridCell(
                overall_pick=pick.overall_pick,
                round=pick.round,
                round_pick=pick.round_pick,
                pick_label=pick.pick_label,
                owner=pick.current_owner,
                is_my_pick=pick.is_my_pick,
                is_current_pick=pick.overall_pick == state.current_pick,
                is_selected_pick=pick.overall_pick == selected_pick,
                drafted_player=drafted_player,
                drafted_position=drafted_position,
                button_label=_pick_button_label(
                    pick=pick,
                    drafted_player=drafted_player,
                    drafted_position=drafted_position,
                    status_label=status_label,
                ),
                status_label=status_label,
            )
        )
    return tuple(cells)


def draft_pick_grid_rows(
    state: DraftBoardState,
    *,
    selected_pick: int | None = None,
) -> list[dict[str, object]]:
    return [
        {
            "round": cell.round,
            "round_pick": cell.round_pick,
            "overall_pick": cell.overall_pick,
            "pick": cell.pick_label,
            "owner": cell.owner,
            "my_pick": cell.is_my_pick,
            "current": cell.is_current_pick,
            "selected": cell.is_selected_pick,
            "player": cell.drafted_player,
            "pos": cell.drafted_position,
            "status": cell.status_label,
        }
        for cell in draft_pick_grid_cells(state, selected_pick=selected_pick)
    ]


def draft_board_export_rows(state: DraftBoardState) -> list[dict[str, object]]:
    drafted_by_pick = {row.pick.overall_pick: row for row in state.drafted_players}
    rows: list[dict[str, object]] = []
    for pick in state.picks:
        drafted = drafted_by_pick.get(pick.overall_pick)
        rows.append(
            {
                "overall_pick": pick.overall_pick,
                "pick": pick.pick_label,
                "round": pick.round,
                "round_pick": pick.round_pick,
                "current_owner": pick.current_owner,
                "original_owner": pick.original_owner,
                "is_my_pick": pick.is_my_pick,
                "status": "drafted" if drafted else "open",
                "player": drafted.player if drafted else "",
                "position": drafted.position if drafted else "",
                "asset_type": drafted.asset_type if drafted else "",
                "asset_lifecycle": drafted.asset_lifecycle if drafted else "",
                "stats_model_value": drafted.stats_model_value if drafted else "",
                "market_value": drafted.market_value if drafted else "",
                "confidence": drafted.confidence if drafted else "",
            }
        )
    return rows


def remaining_pool_export_rows(state: DraftBoardState) -> list[dict[str, object]]:
    return [
        {
            "asset_id": row.asset_id,
            "player": row.player,
            "position": row.position,
            "nfl_team": row.nfl_team,
            "asset_type": row.asset_type,
            "asset_lifecycle": row.asset_lifecycle,
            "why_available": row.why_available,
            "stats_model_value": row.stats_model_value,
            "market_value": row.market_value,
            "market_edge": row.market_edge,
            "confidence": row.confidence,
            "warning": row.warning,
            "recommended_range": row.recommended_range,
            "do_not_draft_before_pick": row.do_not_draft_before_pick or "",
        }
        for row in available_players_after_picks(state)
    ]


def _draft_picks_from_rows(rows: Sequence[Mapping[str, object]]) -> tuple[DraftPick, ...]:
    if not rows:
        rows = [
            {
                "overall_pick": overall_pick,
                "round": ((overall_pick - 1) // DRAFT_TEAMS) + 1,
                "round_pick": ((overall_pick - 1) % DRAFT_TEAMS) + 1,
                "pick_label": (
                    f"{((overall_pick - 1) // DRAFT_TEAMS) + 1}."
                    f"{(((overall_pick - 1) % DRAFT_TEAMS) + 1):02d}"
                ),
                "current_owner": "",
                "original_owner": "",
                "is_my_pick": False,
            }
            for overall_pick in range(1, DRAFT_TOTAL_PICKS + 1)
        ]
    picks = [
        DraftPick(
            overall_pick=int(row["overall_pick"]),
            round=int(row["round"]),
            round_pick=int(row["round_pick"]),
            pick_label=str(row["pick_label"]),
            current_owner=str(row.get("current_owner") or ""),
            original_owner=str(row.get("original_owner") or ""),
            is_my_pick=bool(row.get("is_my_pick")),
        )
        for row in rows
    ]
    return tuple(sorted(picks, key=lambda row: row.overall_pick))


def _available_players_from_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[AvailablePlayer, ...]:
    players = [
        AvailablePlayer(
            asset_id=str(row.get("asset_id") or ""),
            player=str(row.get("player") or ""),
            position=str(row.get("position") or ""),
            nfl_team=str(row.get("nfl_team") or row.get("team") or ""),
            asset_type=str(row.get("asset_type_label") or row.get("asset_type") or ""),
            asset_lifecycle=str(
                row.get("asset_lifecycle_label") or row.get("asset_lifecycle") or ""
            ),
            why_available=str(row.get("why_available") or ""),
            stats_model_value=float(
                row.get("stats_model_value") or row.get("model_value") or 0
            ),
            market_value=float(row.get("market_value") or 0),
            market_edge=float(row.get("market_edge") or 0),
            confidence=float(row.get("confidence") or 0),
            warning=str(row.get("warning") or ""),
            draft_rank=int(row.get("overall_rank") or row.get("draft_rank") or 999),
            do_not_draft_before_pick=_optional_int(row.get("do_not_draft_before_pick")),
            recommended_range=str(row.get("recommended_range") or ""),
        )
        for row in rows
        if row.get("asset_id")
    ]
    return _sorted_available(tuple(players))


def _sorted_available(players: tuple[AvailablePlayer, ...]) -> tuple[AvailablePlayer, ...]:
    return tuple(
        sorted(
            players,
            key=lambda row: (
                -row.stats_model_value,
                -row.confidence,
                row.draft_rank,
                row.player,
            ),
        )
    )


def _sorted_drafted(players: tuple[DraftedPlayer, ...]) -> tuple[DraftedPlayer, ...]:
    return tuple(sorted(players, key=lambda row: row.pick.overall_pick))


def _with_recomputed_current_pick(state: DraftBoardState) -> DraftBoardState:
    drafted_picks = {row.pick.overall_pick for row in state.drafted_players}
    current_pick = next(
        (pick.overall_pick for pick in state.picks if pick.overall_pick not in drafted_picks),
        None,
    )
    return replace(state, current_pick=current_pick)


def _find_pick(state: DraftBoardState, overall_pick: int) -> DraftPick:
    for pick in state.picks:
        if pick.overall_pick == overall_pick:
            return pick
    raise ValueError(f"Pick {overall_pick} is outside the draft board.")


def _find_available_player(state: DraftBoardState, asset_id: str) -> AvailablePlayer:
    for player in state.available_players:
        if player.asset_id == asset_id:
            return player
    raise ValueError(f"Player asset {asset_id} is not available.")


def _drafted_at_pick(
    state: DraftBoardState,
    overall_pick: int,
) -> DraftedPlayer | None:
    return next(
        (row for row in state.drafted_players if row.pick.overall_pick == overall_pick),
        None,
    )


def _drafted_asset(state: DraftBoardState, asset_id: str) -> DraftedPlayer | None:
    return next((row for row in state.drafted_players if row.asset_id == asset_id), None)


def _restore_draft_rank(state: DraftBoardState, stats_model_value: float) -> int:
    better_players = [
        row for row in state.available_players if row.stats_model_value > stats_model_value
    ]
    return len(better_players) + 1


def _available_player_from_drafted(
    drafted: DraftedPlayer,
    *,
    state: DraftBoardState,
) -> AvailablePlayer:
    return AvailablePlayer(**_available_player_payload_from_drafted(drafted, state=state))


def _available_player_payload_from_drafted(
    drafted: DraftedPlayer,
    *,
    state: DraftBoardState,
) -> dict[str, object]:
    return {
        "asset_id": drafted.asset_id,
        "player": drafted.player,
        "position": drafted.position,
        "nfl_team": drafted.nfl_team,
        "asset_type": drafted.asset_type,
        "asset_lifecycle": drafted.asset_lifecycle,
        "why_available": drafted.why_available,
        "stats_model_value": drafted.stats_model_value,
        "market_value": drafted.market_value,
        "market_edge": drafted.market_edge,
        "confidence": drafted.confidence,
        "warning": "",
        "draft_rank": _restore_draft_rank(state, drafted.stats_model_value),
        "do_not_draft_before_pick": drafted.do_not_draft_before_pick,
        "recommended_range": drafted.recommended_range,
    }


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _option_warning(base_warning: str, *, review_only: bool) -> str:
    if review_only:
        return "Review-only: calibration blocked"
    return base_warning


def _reach_value_label(player: AvailablePlayer, overall_pick: int | None) -> str:
    if overall_pick is None:
        return "Draft complete"
    if player.do_not_draft_before_pick is not None:
        earliest = player.do_not_draft_before_pick
        if overall_pick < earliest:
            return "Reach"
        if overall_pick == earliest:
            return "Fair"
        if overall_pick <= earliest + 10:
            return "Value"
        return "Strong value"
    if player.draft_rank <= max(1, overall_pick - 4):
        return "Value"
    if player.draft_rank <= overall_pick + 3:
        return "Fair"
    return "Reach"


def _search_blob(row: AvailablePlayer) -> str:
    return " ".join(
        [
            row.player,
            row.position,
            row.nfl_team,
            row.asset_type,
            row.asset_lifecycle,
            row.why_available,
        ]
    ).lower()


def _pick_status_label(
    *,
    pick: DraftPick,
    drafted: bool,
    current_pick: int | None,
    selected_pick: int | None,
) -> str:
    if drafted:
        return "Drafted"
    if pick.overall_pick == selected_pick:
        return "Selected"
    if pick.overall_pick == current_pick:
        return "On clock"
    if pick.is_my_pick:
        return "My pick"
    return "Open"


def _pick_button_label(
    *,
    pick: DraftPick,
    drafted_player: str,
    drafted_position: str,
    status_label: str,
) -> str:
    owner = pick.current_owner or "TBD"
    if drafted_player:
        player_line = f"{drafted_player} ({drafted_position})"
    else:
        player_line = status_label
    my_suffix = " [MY]" if pick.is_my_pick else ""
    return f"{pick.pick_label}{my_suffix}\n{owner}\n{player_line}"
