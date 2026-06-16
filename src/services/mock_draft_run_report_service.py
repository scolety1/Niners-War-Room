from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.services.mock_draft_combined_state_service import (
    CombinedSimulatorState,
    build_combined_simulator_state,
)
from src.services.mock_draft_simulator_service import (
    BLOCKED_MARKET_SCORE_FIELDS,
)

DEFAULT_MOCK_DRAFT_RUN_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/mock_draft_run_20260616"
)

PICK_BY_PICK_COLUMNS = (
    "overall_pick",
    "round",
    "round_pick",
    "pick_label",
    "owning_team",
    "manager",
    "is_tim_pick",
    "selected_asset_id",
    "selected_player",
    "selected_position",
    "selected_player_source",
    "selection_mode",
    "selection_reason",
    "selection_basis",
    "review_flags",
    "nwr_score_status",
    "value_status",
    "stats_model_value",
    "market_adp",
    "market_context_used",
)

TIM_SHORTLIST_COLUMNS = (
    "overall_pick",
    "pick_label",
    "owning_team",
    "manager",
    "shortlist_rank",
    "asset_id",
    "player",
    "position",
    "player_source",
    "rank",
    "tier",
    "draft_action",
    "warning_severity",
    "draft_room_note",
    "review_flags",
    "nwr_score_status",
    "value_status",
    "stats_model_value",
    "market_context_used",
    "shortlist_reason",
)

OPPONENT_NOTES_COLUMNS = (
    "overall_pick",
    "pick_label",
    "owning_team",
    "selected_player",
    "selected_player_source",
    "note_type",
    "note",
    "market_context_used",
    "ignored_market_score_fields",
)


@dataclass(frozen=True)
class MarketTimingContext:
    asset_id: str
    market_adp: float | None
    ignored_score_fields: tuple[str, ...]


@dataclass(frozen=True)
class MockDraftRunReport:
    review_only: bool
    pick_rows: tuple[dict[str, object], ...]
    tim_shortlist_rows: tuple[dict[str, object], ...]
    opponent_behavior_notes: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    review_flags: dict[str, int]
    artifact_paths: dict[str, Path]


def build_mock_draft_run_report(
    combined_state: CombinedSimulatorState | None = None,
    *,
    market_context_rows: Sequence[Mapping[str, object]] | None = None,
    shortlist_size: int = 8,
    opponent_lookahead: int = 10,
) -> MockDraftRunReport:
    state = combined_state or build_combined_simulator_state()
    market_context = _market_context_by_asset(market_context_rows or ())
    remaining = list(state.available_rows)
    pick_rows: list[dict[str, object]] = []
    shortlist_rows: list[dict[str, object]] = []
    notes: list[dict[str, object]] = []

    for pick in sorted(
        state.pick_rows,
        key=lambda row: (int(row["overall_pick"]), str(row["pick_label"])),
    ):
        if bool(pick.get("is_my_pick")):
            shortlist = _tim_shortlist(remaining, limit=shortlist_size)
            shortlist_rows.extend(
                _tim_shortlist_rows(pick=pick, shortlist=shortlist)
            )
            pick_rows.append(_tim_pick_row(pick, shortlist_count=len(shortlist)))
            continue

        selection = _select_opponent_player(
            remaining,
            overall_pick=int(pick["overall_pick"]),
            market_context=market_context,
            opponent_lookahead=opponent_lookahead,
        )
        if selection is None:
            pick_rows.append(_empty_opponent_pick_row(pick))
            continue
        player, context, mode, reason, basis = selection
        remaining = [
            row for row in remaining if row.get("asset_id") != player.get("asset_id")
        ]
        pick_rows.append(
            _selected_pick_row(
                pick=pick,
                player=player,
                context=context,
                mode=mode,
                reason=reason,
                basis=basis,
            )
        )
        notes.append(
            _opponent_note_row(
                pick=pick,
                player=player,
                context=context,
                mode=mode,
                reason=reason,
            )
        )

    review_flags = _review_flag_counts(pick_rows, shortlist_rows, notes, state.review_flags)
    manifest = _manifest(
        state=state,
        pick_rows=pick_rows,
        shortlist_rows=shortlist_rows,
        notes=notes,
        review_flags=review_flags,
        market_context=market_context,
    )
    return MockDraftRunReport(
        review_only=True,
        pick_rows=tuple(pick_rows),
        tim_shortlist_rows=tuple(shortlist_rows),
        opponent_behavior_notes=tuple(notes),
        manifest=manifest,
        review_flags=review_flags,
        artifact_paths={},
    )


def write_mock_draft_run_report_artifacts(
    report: MockDraftRunReport,
    *,
    output_root: str | Path = DEFAULT_MOCK_DRAFT_RUN_OUTPUT_ROOT,
) -> MockDraftRunReport:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    pick_path = root / "mock_draft_pick_by_pick_review_rows.csv"
    shortlist_path = root / "tim_pick_shortlist_review_rows.csv"
    notes_path = root / "opponent_behavior_notes.csv"
    manifest_path = root / "mock_draft_run_manifest.json"
    _write_csv(pick_path, PICK_BY_PICK_COLUMNS, report.pick_rows)
    _write_csv(shortlist_path, TIM_SHORTLIST_COLUMNS, report.tim_shortlist_rows)
    _write_csv(notes_path, OPPONENT_NOTES_COLUMNS, report.opponent_behavior_notes)
    manifest = {
        **report.manifest,
        "artifact_paths": {
            "pick_by_pick": str(pick_path),
            "tim_shortlist": str(shortlist_path),
            "opponent_behavior_notes": str(notes_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return MockDraftRunReport(
        review_only=report.review_only,
        pick_rows=report.pick_rows,
        tim_shortlist_rows=report.tim_shortlist_rows,
        opponent_behavior_notes=report.opponent_behavior_notes,
        manifest=manifest,
        review_flags=report.review_flags,
        artifact_paths={
            "pick_by_pick": pick_path,
            "tim_shortlist": shortlist_path,
            "opponent_behavior_notes": notes_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_mock_draft_run_report(
    *,
    output_root: str | Path = DEFAULT_MOCK_DRAFT_RUN_OUTPUT_ROOT,
    market_context_rows: Sequence[Mapping[str, object]] | None = None,
    shortlist_size: int = 8,
    opponent_lookahead: int = 10,
) -> MockDraftRunReport:
    return write_mock_draft_run_report_artifacts(
        build_mock_draft_run_report(
            market_context_rows=market_context_rows,
            shortlist_size=shortlist_size,
            opponent_lookahead=opponent_lookahead,
        ),
        output_root=output_root,
    )


def _select_opponent_player(
    remaining: list[dict[str, object]],
    *,
    overall_pick: int,
    market_context: dict[str, MarketTimingContext],
    opponent_lookahead: int,
) -> tuple[dict[str, object], MarketTimingContext | None, str, str, str] | None:
    if not remaining:
        return None
    market_candidates = [
        (row, market_context[str(row.get("asset_id") or "")])
        for row in remaining
        if str(row.get("asset_id") or "") in market_context
        and market_context[str(row.get("asset_id") or "")].market_adp is not None
    ]
    in_window = [
        (row, context)
        for row, context in market_candidates
        if float(context.market_adp or 999) <= overall_pick + opponent_lookahead
    ]
    if in_window:
        player, context = min(
            in_window,
            key=lambda item: (
                max(float(item[1].market_adp or 999) - overall_pick, 0.0),
                float(item[1].market_adp or 999),
                _source_priority(item[0]),
                int(item[0].get("draft_rank") or 999),
                str(item[0].get("player") or ""),
            ),
        )
        return (
            player,
            context,
            "opponent_behavior_market_timing",
            (
                "Market/ADP timing placed this player in the opponent pick window; "
                "market fields did not alter NWR guidance or value."
            ),
            "market_timing_behavior_only",
        )
    player = min(
        remaining,
        key=lambda row: (
            _source_priority(row),
            int(row.get("draft_rank") or 999),
            str(row.get("player") or ""),
            str(row.get("asset_id") or ""),
        ),
    )
    return (
        player,
        None,
        "opponent_behavior_placeholder",
        (
            "No usable ADP/market timing was supplied, so this is a deterministic "
            "behavior-only placeholder based on source class and copied review order."
        ),
        "placeholder_behavior_only_not_private_value",
    )


def _tim_shortlist(
    remaining: list[dict[str, object]],
    *,
    limit: int,
) -> list[dict[str, object]]:
    return sorted(
        remaining,
        key=lambda row: (
            0 if row.get("source_label") == "frozen_rookie" else 1,
            int(row.get("draft_rank") or 999),
            str(row.get("player") or ""),
            str(row.get("asset_id") or ""),
        ),
    )[:limit]


def _tim_shortlist_rows(
    *,
    pick: Mapping[str, object],
    shortlist: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "overall_pick": pick.get("overall_pick"),
            "pick_label": pick.get("pick_label"),
            "owning_team": pick.get("current_owner") or "",
            "manager": pick.get("manager") or "",
            "shortlist_rank": index,
            "asset_id": row.get("asset_id") or "",
            "player": row.get("player") or "",
            "position": row.get("position") or "",
            "player_source": row.get("source_label") or "",
            "rank": row.get("rank") or "",
            "tier": row.get("tier") or "",
            "draft_action": row.get("draft_action") or "",
            "warning_severity": row.get("warning_severity") or "",
            "draft_room_note": row.get("draft_room_note") or "",
            "review_flags": row.get("review_flags") or "",
            "nwr_score_status": row.get("nwr_score_status") or "",
            "value_status": row.get("value_status") or "",
            "stats_model_value": row.get("stats_model_value", 0.0),
            "market_context_used": False,
            "shortlist_reason": _shortlist_reason(row),
        }
        for index, row in enumerate(shortlist, start=1)
    ]


def _tim_pick_row(pick: Mapping[str, object], *, shortlist_count: int) -> dict[str, object]:
    return {
        "overall_pick": pick.get("overall_pick"),
        "round": pick.get("round"),
        "round_pick": pick.get("round_pick"),
        "pick_label": pick.get("pick_label"),
        "owning_team": pick.get("current_owner") or "",
        "manager": pick.get("manager") or "",
        "is_tim_pick": True,
        "selected_asset_id": "",
        "selected_player": "",
        "selected_position": "",
        "selected_player_source": "",
        "selection_mode": "Tim_review_pick",
        "selection_reason": (
            f"Manual review required. See {shortlist_count} shortlist rows; "
            "no automatic best pick selected."
        ),
        "selection_basis": "manual_shortlist_no_market_quality",
        "review_flags": "tim_manual_review_required",
        "nwr_score_status": "no_auto_selection",
        "value_status": "",
        "stats_model_value": "",
        "market_adp": "",
        "market_context_used": False,
    }


def _selected_pick_row(
    *,
    pick: Mapping[str, object],
    player: Mapping[str, object],
    context: MarketTimingContext | None,
    mode: str,
    reason: str,
    basis: str,
) -> dict[str, object]:
    return {
        "overall_pick": pick.get("overall_pick"),
        "round": pick.get("round"),
        "round_pick": pick.get("round_pick"),
        "pick_label": pick.get("pick_label"),
        "owning_team": pick.get("current_owner") or "",
        "manager": pick.get("manager") or "",
        "is_tim_pick": False,
        "selected_asset_id": player.get("asset_id") or "",
        "selected_player": player.get("player") or "",
        "selected_position": player.get("position") or "",
        "selected_player_source": player.get("source_label") or "",
        "selection_mode": mode,
        "selection_reason": reason,
        "selection_basis": basis,
        "review_flags": player.get("review_flags") or "",
        "nwr_score_status": player.get("nwr_score_status") or "",
        "value_status": player.get("value_status") or "",
        "stats_model_value": player.get("stats_model_value", 0.0),
        "market_adp": context.market_adp if context else "",
        "market_context_used": context is not None,
    }


def _empty_opponent_pick_row(pick: Mapping[str, object]) -> dict[str, object]:
    return {
        "overall_pick": pick.get("overall_pick"),
        "round": pick.get("round"),
        "round_pick": pick.get("round_pick"),
        "pick_label": pick.get("pick_label"),
        "owning_team": pick.get("current_owner") or "",
        "manager": pick.get("manager") or "",
        "is_tim_pick": False,
        "selected_asset_id": "",
        "selected_player": "",
        "selected_position": "",
        "selected_player_source": "",
        "selection_mode": "placeholder_review_required",
        "selection_reason": "No available player remained for this review run.",
        "selection_basis": "review_required",
        "review_flags": "placeholder_review_required",
        "nwr_score_status": "",
        "value_status": "",
        "stats_model_value": "",
        "market_adp": "",
        "market_context_used": False,
    }


def _opponent_note_row(
    *,
    pick: Mapping[str, object],
    player: Mapping[str, object],
    context: MarketTimingContext | None,
    mode: str,
    reason: str,
) -> dict[str, object]:
    return {
        "overall_pick": pick.get("overall_pick"),
        "pick_label": pick.get("pick_label"),
        "owning_team": pick.get("current_owner") or "",
        "selected_player": player.get("player") or "",
        "selected_player_source": player.get("source_label") or "",
        "note_type": mode,
        "note": reason,
        "market_context_used": context is not None,
        "ignored_market_score_fields": (
            "|".join(context.ignored_score_fields) if context else ""
        ),
    }


def _market_context_by_asset(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, MarketTimingContext]:
    contexts: dict[str, MarketTimingContext] = {}
    for row in rows:
        asset_id = str(row.get("asset_id") or "").strip()
        if not asset_id:
            continue
        ignored = tuple(
            sorted(
                key
                for key, value in row.items()
                if key in BLOCKED_MARKET_SCORE_FIELDS and value not in (None, "")
            )
        )
        contexts[asset_id] = MarketTimingContext(
            asset_id=asset_id,
            market_adp=_optional_float(
                row.get("market_adp"),
                row.get("adp"),
                row.get("overall_adp"),
                row.get("expected_pick"),
            ),
            ignored_score_fields=ignored,
        )
    return contexts


def _manifest(
    *,
    state: CombinedSimulatorState,
    pick_rows: list[dict[str, object]],
    shortlist_rows: list[dict[str, object]],
    notes: list[dict[str, object]],
    review_flags: dict[str, int],
    market_context: dict[str, MarketTimingContext],
) -> dict[str, object]:
    opponent_count = sum(
        1 for row in pick_rows if str(row.get("selection_mode") or "").startswith("opponent")
    )
    tim_pick_count = sum(1 for row in pick_rows if row.get("selection_mode") == "Tim_review_pick")
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "combined_available_rows": len(state.available_rows),
        "pick_by_pick_rows": len(pick_rows),
        "tim_pick_rows": tim_pick_count,
        "tim_shortlist_rows": len(shortlist_rows),
        "opponent_selection_rows": opponent_count,
        "opponent_behavior_note_rows": len(notes),
        "review_flags": review_flags,
        "review_flag_count_semantics": (
            "review_flags counts are output-row occurrences across pick rows, "
            "Tim shortlist rows, opponent behavior notes, plus upstream combined-state "
            "review flags; they are not unique-player counts"
        ),
        "market_context_rows": len(market_context),
        "market_context_with_ignored_score_fields": sum(
            1 for row in market_context.values() if row.ignored_score_fields
        ),
        "nwr_score_policy": (
            "No numeric NWR score is invented from rookie rank, tier, action, "
            "snapshot rank, ADP, or market data."
        ),
        "market_adp_policy": (
            "ADP/market is behavior-only for opponent timing and availability; "
            "Tim shortlists and NWR guidance do not use market as quality."
        ),
        "tim_pick_policy": (
            "Tim/Niners picks are manual review rows with shortlist context only; "
            "no automatic best pick is finalized."
        ),
        "source_counts": state.source_counts,
        "upstream_review_flags": state.review_flags,
        "promotion_status": "local_review_output_only_not_app_wired_not_promoted",
    }


def _review_flag_counts(
    pick_rows: list[dict[str, object]],
    shortlist_rows: list[dict[str, object]],
    notes: list[dict[str, object]],
    upstream_flags: Mapping[str, int],
) -> dict[str, int]:
    flags: Counter[str] = Counter(upstream_flags)
    for group in (pick_rows, shortlist_rows):
        for row in group:
            for flag in str(row.get("review_flags") or "").split("|"):
                if flag:
                    flags[flag] += 1
    for note in notes:
        if note.get("market_context_used"):
            flags["market_behavior_context_used"] += 1
        if note.get("ignored_market_score_fields"):
            flags["market_score_fields_ignored"] += 1
    return dict(flags)


def _shortlist_reason(row: Mapping[str, object]) -> str:
    if row.get("source_label") == "frozen_rookie":
        return "Frozen rookie guidance copied read-only; no numeric score invented."
    return "Value-neutral available player retained for manual review only."


def _source_priority(row: Mapping[str, object]) -> int:
    return {"frozen_rookie": 0, "declared_drop": 1, "free_agent": 2}.get(
        str(row.get("source_label") or ""),
        99,
    )


def _optional_float(*values: object) -> float | None:
    for value in values:
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
