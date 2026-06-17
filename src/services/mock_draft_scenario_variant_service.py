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
from src.services.mock_draft_market_timing_adapter_service import (
    DEFAULT_FAKE_MARKET_TIMING_FIXTURE,
    behavior_only_market_context_rows,
    read_fake_market_timing_rows,
)

DEFAULT_SCENARIO_VARIANT_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/scenario_variants_20260617"
)

SCENARIO_NAMES = (
    "baseline_placeholder_behavior",
    "rookie_front_run_behavior",
    "veteran_visibility_behavior",
    "fake_market_timing_behavior",
)

PICK_COLUMNS = (
    "scenario_name",
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
    "review_flags",
    "nwr_score_status",
    "value_status",
    "stats_model_value",
    "market_context_used",
)

TIM_AVAILABILITY_COLUMNS = (
    "scenario_name",
    "overall_pick",
    "pick_label",
    "availability_rank",
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
    "availability_label",
)

BEHAVIOR_NOTE_COLUMNS = (
    "scenario_name",
    "overall_pick",
    "pick_label",
    "note_type",
    "note",
    "market_context_used",
)


@dataclass(frozen=True)
class ScenarioVariantOutputs:
    review_only: bool
    pick_rows: tuple[dict[str, object], ...]
    tim_availability_rows: tuple[dict[str, object], ...]
    behavior_notes: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def build_scenario_variant_outputs(
    combined_state: CombinedSimulatorState | None = None,
    *,
    fake_market_rows: Sequence[Mapping[str, object]] | None = None,
    tim_availability_limit: int = 8,
    opponent_lookahead: int = 10,
) -> ScenarioVariantOutputs:
    state = combined_state or build_combined_simulator_state()
    if fake_market_rows is None:
        fake_market_rows = read_fake_market_timing_rows(DEFAULT_FAKE_MARKET_TIMING_FIXTURE)
    fake_market_context = {
        str(row.get("asset_id") or ""): row
        for row in behavior_only_market_context_rows(fake_market_rows)
    }
    pick_rows: list[dict[str, object]] = []
    availability_rows: list[dict[str, object]] = []
    notes: list[dict[str, object]] = []

    for scenario_name in SCENARIO_NAMES:
        remaining = list(state.available_rows)
        for pick in sorted(
            state.pick_rows,
            key=lambda row: (int(row["overall_pick"]), str(row["pick_label"])),
        ):
            if bool(pick.get("is_my_pick")):
                window_rows = _tim_window_rows(
                    scenario_name=scenario_name,
                    pick=pick,
                    remaining=remaining,
                    limit=tim_availability_limit,
                )
                availability_rows.extend(window_rows)
                pick_rows.append(
                    _tim_pick_row(
                        scenario_name=scenario_name,
                        pick=pick,
                        shortlist_count=len(window_rows),
                    )
                )
                notes.append(
                    {
                        "scenario_name": scenario_name,
                        "overall_pick": pick.get("overall_pick"),
                        "pick_label": pick.get("pick_label"),
                        "note_type": "tim_manual_review_window",
                        "note": (
                            "Tim/Niners pick remains manual-review only; no best pick "
                            "is finalized by scenario behavior."
                        ),
                        "market_context_used": False,
                    }
                )
                continue

            selection, used_market = _select_opponent_player(
                scenario_name=scenario_name,
                remaining=remaining,
                overall_pick=int(pick["overall_pick"]),
                fake_market_context=fake_market_context,
                opponent_lookahead=opponent_lookahead,
            )
            if selection is None:
                pick_rows.append(_empty_opponent_row(scenario_name=scenario_name, pick=pick))
                continue
            remaining = [
                row
                for row in remaining
                if row.get("asset_id") != selection.get("asset_id")
            ]
            pick_rows.append(
                _selected_pick_row(
                    scenario_name=scenario_name,
                    pick=pick,
                    player=selection,
                    market_context_used=used_market,
                )
            )
            notes.append(
                _behavior_note_row(
                    scenario_name=scenario_name,
                    pick=pick,
                    player=selection,
                    market_context_used=used_market,
                )
            )

    review_flags = _review_flag_counts(pick_rows, availability_rows)
    manifest = _manifest(
        state=state,
        pick_rows=pick_rows,
        availability_rows=availability_rows,
        notes=notes,
        review_flags=review_flags,
        fake_market_context=fake_market_context,
    )
    return ScenarioVariantOutputs(
        review_only=True,
        pick_rows=tuple(pick_rows),
        tim_availability_rows=tuple(availability_rows),
        behavior_notes=tuple(notes),
        manifest=manifest,
        artifact_paths={},
    )


def write_scenario_variant_artifacts(
    outputs: ScenarioVariantOutputs,
    *,
    output_root: str | Path = DEFAULT_SCENARIO_VARIANT_OUTPUT_ROOT,
) -> ScenarioVariantOutputs:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    pick_path = root / "scenario_variant_pick_by_pick_review_rows.csv"
    availability_path = root / "tim_scenario_availability_rows.csv"
    notes_path = root / "scenario_variant_behavior_notes.csv"
    manifest_path = root / "scenario_variant_manifest.json"
    _write_csv(pick_path, PICK_COLUMNS, outputs.pick_rows)
    _write_csv(availability_path, TIM_AVAILABILITY_COLUMNS, outputs.tim_availability_rows)
    _write_csv(notes_path, BEHAVIOR_NOTE_COLUMNS, outputs.behavior_notes)
    manifest = {
        **outputs.manifest,
        "artifact_paths": {
            "pick_by_pick": str(pick_path),
            "tim_availability": str(availability_path),
            "behavior_notes": str(notes_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return ScenarioVariantOutputs(
        review_only=outputs.review_only,
        pick_rows=outputs.pick_rows,
        tim_availability_rows=outputs.tim_availability_rows,
        behavior_notes=outputs.behavior_notes,
        manifest=manifest,
        artifact_paths={
            "pick_by_pick": pick_path,
            "tim_availability": availability_path,
            "behavior_notes": notes_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_scenario_variant_artifacts(
    *,
    output_root: str | Path = DEFAULT_SCENARIO_VARIANT_OUTPUT_ROOT,
    fake_market_rows: Sequence[Mapping[str, object]] | None = None,
) -> ScenarioVariantOutputs:
    return write_scenario_variant_artifacts(
        build_scenario_variant_outputs(fake_market_rows=fake_market_rows),
        output_root=output_root,
    )


def _select_opponent_player(
    *,
    scenario_name: str,
    remaining: list[dict[str, object]],
    overall_pick: int,
    fake_market_context: Mapping[str, Mapping[str, object]],
    opponent_lookahead: int,
) -> tuple[dict[str, object] | None, bool]:
    if not remaining:
        return None, False
    if scenario_name == "fake_market_timing_behavior":
        timed = _fake_market_timed_rows(remaining, fake_market_context)
        in_window = [
            (row, market_adp)
            for row, market_adp in timed
            if float(market_adp or 999) <= overall_pick + opponent_lookahead
        ]
        if in_window:
            return min(
                in_window,
                key=lambda item: (
                    max(float(item[1] or 999) - overall_pick, 0.0),
                    float(item[1] or 999),
                    _scenario_sort_key("baseline_placeholder_behavior", item[0]),
                ),
            )[0], True
    return min(remaining, key=lambda row: _scenario_sort_key(scenario_name, row)), False


def _fake_market_timed_rows(
    remaining: list[dict[str, object]],
    fake_market_context: Mapping[str, Mapping[str, object]],
) -> list[tuple[dict[str, object], float | None]]:
    timed: list[tuple[dict[str, object], float | None]] = []
    for row in remaining:
        asset_id = str(row.get("asset_id") or "")
        if asset_id not in fake_market_context:
            continue
        market_adp = _optional_float(fake_market_context[asset_id].get("market_adp"))
        if market_adp is not None:
            timed.append((row, market_adp))
    return timed


def _scenario_sort_key(scenario_name: str, row: Mapping[str, object]) -> tuple[object, ...]:
    source = str(row.get("source_label") or "")
    draft_rank = int(row.get("draft_rank") or 999)
    player = str(row.get("player") or "")
    asset_id = str(row.get("asset_id") or "")
    if scenario_name == "veteran_visibility_behavior":
        priority = {"declared_drop": 0, "free_agent": 1, "frozen_rookie": 2}.get(source, 99)
    else:
        priority = {"frozen_rookie": 0, "declared_drop": 1, "free_agent": 2}.get(source, 99)
    if scenario_name == "rookie_front_run_behavior" and source == "frozen_rookie":
        priority = -1
    return (priority, draft_rank, player, asset_id)


def _tim_window_rows(
    *,
    scenario_name: str,
    pick: Mapping[str, object],
    remaining: list[dict[str, object]],
    limit: int,
) -> list[dict[str, object]]:
    ordered = sorted(remaining, key=lambda row: _scenario_sort_key(scenario_name, row))
    rows: list[dict[str, object]] = []
    for index, row in enumerate(ordered[:limit], start=1):
        rows.append(
            {
                "scenario_name": scenario_name,
                "overall_pick": pick.get("overall_pick"),
                "pick_label": pick.get("pick_label"),
                "availability_rank": index,
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
                "availability_label": _availability_label(row),
            }
        )
    return rows


def _tim_pick_row(
    *,
    scenario_name: str,
    pick: Mapping[str, object],
    shortlist_count: int,
) -> dict[str, object]:
    return {
        "scenario_name": scenario_name,
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
            f"Manual review only with {shortlist_count} visible availability rows."
        ),
        "review_flags": "tim_manual_review_required",
        "nwr_score_status": "no_auto_selection",
        "value_status": "",
        "stats_model_value": "",
        "market_context_used": False,
    }


def _selected_pick_row(
    *,
    scenario_name: str,
    pick: Mapping[str, object],
    player: Mapping[str, object],
    market_context_used: bool,
) -> dict[str, object]:
    return {
        "scenario_name": scenario_name,
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
        "selection_mode": (
            "opponent_behavior_fake_market_timing"
            if market_context_used
            else f"opponent_behavior_{scenario_name}"
        ),
        "selection_reason": _selection_reason(scenario_name, market_context_used),
        "review_flags": player.get("review_flags") or "",
        "nwr_score_status": player.get("nwr_score_status") or "",
        "value_status": player.get("value_status") or "",
        "stats_model_value": player.get("stats_model_value", 0.0),
        "market_context_used": market_context_used,
    }


def _empty_opponent_row(
    *,
    scenario_name: str,
    pick: Mapping[str, object],
) -> dict[str, object]:
    return {
        "scenario_name": scenario_name,
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
        "selection_reason": "No available player remained in this review-only scenario.",
        "review_flags": "placeholder_review_required",
        "nwr_score_status": "",
        "value_status": "",
        "stats_model_value": "",
        "market_context_used": False,
    }


def _behavior_note_row(
    *,
    scenario_name: str,
    pick: Mapping[str, object],
    player: Mapping[str, object],
    market_context_used: bool,
) -> dict[str, object]:
    return {
        "scenario_name": scenario_name,
        "overall_pick": pick.get("overall_pick"),
        "pick_label": pick.get("pick_label"),
        "note_type": "opponent_behavior",
        "note": (
            f"Opponent selected {player.get('player')} by behavior-only scenario "
            "rules; NWR guidance/value fields were copied unchanged."
        ),
        "market_context_used": market_context_used,
    }


def _selection_reason(scenario_name: str, market_context_used: bool) -> str:
    if market_context_used:
        return (
            "Fake fixture timing changed opponent behavior only; it did not alter "
            "NWR value or rookie guidance."
        )
    if scenario_name == "veteran_visibility_behavior":
        return "Deterministic veteran-visibility behavior only; not NWR quality."
    if scenario_name == "rookie_front_run_behavior":
        return "Deterministic rookie front-run behavior only; not NWR quality."
    return "Deterministic placeholder behavior only; not NWR quality."


def _availability_label(row: Mapping[str, object]) -> str:
    if row.get("source_label") == "frozen_rookie":
        return "frozen_rookie_guidance_read_only"
    return "value_neutral_visibility_only"


def _review_flag_counts(
    pick_rows: Sequence[Mapping[str, object]],
    availability_rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    flags: Counter[str] = Counter()
    for row_group in (pick_rows, availability_rows):
        for row in row_group:
            for flag in str(row.get("review_flags") or "").split("|"):
                if flag:
                    flags[flag] += 1
    return dict(sorted(flags.items()))


def _manifest(
    *,
    state: CombinedSimulatorState,
    pick_rows: list[dict[str, object]],
    availability_rows: list[dict[str, object]],
    notes: list[dict[str, object]],
    review_flags: dict[str, int],
    fake_market_context: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "scenario_names": list(SCENARIO_NAMES),
        "scenario_count": len(SCENARIO_NAMES),
        "available_pool_rows": len(state.available_rows),
        "pick_rows": len(pick_rows),
        "tim_availability_rows": len(availability_rows),
        "behavior_note_rows": len(notes),
        "tim_pick_rows": sum(
            1 for row in pick_rows if row.get("selection_mode") == "Tim_review_pick"
        ),
        "opponent_pick_rows": sum(
            1
            for row in pick_rows
            if str(row.get("selection_mode") or "").startswith("opponent_behavior")
        ),
        "fake_market_context_rows": len(fake_market_context),
        "market_context_used_rows": sum(
            1 for row in pick_rows if row.get("market_context_used")
        ),
        "review_flags": review_flags,
        "nwr_score_policy": (
            "Scenario variants do not invent numeric NWR scores from rank, tier, "
            "action, snapshot rank, ADP, market data, or fake timing rows."
        ),
        "market_policy": (
            "Fake market timing may affect opponent behavior, likely pick timing, "
            "availability, and behavior notes only."
        ),
        "tim_pick_policy": (
            "Tim/Niners picks remain manual-review only; no automatic best pick is "
            "finalized."
        ),
        "value_neutral_policy": (
            "Declared drops and free agents remain value-neutral visibility rows and "
            "are not ranked against rookies as NWR quality."
        ),
        "promotion_status": "local_review_output_only_not_app_wired_not_promoted",
    }


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: Sequence[Mapping[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
