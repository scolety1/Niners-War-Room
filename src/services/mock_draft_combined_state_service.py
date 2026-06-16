from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.services.draft_state_service import DraftBoardState, create_empty_draft_state
from src.services.mock_draft_snapshot_service import (
    DEFAULT_LVE_ROSTERS_061326_SNAPSHOT,
    MockDraftInputSnapshot,
    load_mock_draft_input_snapshot,
    review_available_player_rows_from_snapshot,
    simulator_pick_rows_from_snapshot,
    snapshot_audit_summary,
)

DEFAULT_ROOKIE_KIT_ROOT = Path(
    "local_exports/mock_draft/review_inputs/rookie_final_manual_kit_20260615"
)
DEFAULT_COMBINED_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/combined_simulator_state_20260616"
)
ROOKIE_BOARD_FILE = "rookie_2026_final_manual_draft_board_frozen_20260615.csv"
ROOKIE_QUICK_SHEET_FILE = "rookie_2026_draft_day_quick_sheet_20260615.csv"

FROZEN_ROOKIE_GUIDANCE_FIELDS = (
    "rank",
    "tier",
    "draft_action",
    "warning_severity",
    "trap_caution_warning",
    "main_positive_reason",
    "main_risk_manual_question",
    "draft_room_note",
    "model_formula_version",
    "main_ranking_formula_changed",
    "board_order_changed",
    "production_allowed",
    "promotion_status",
)

AVAILABLE_POOL_COLUMNS = (
    "asset_id",
    "player",
    "position",
    "nfl_team",
    "source_label",
    "asset_type",
    "asset_lifecycle",
    "draft_rank",
    "stats_model_value",
    "nwr_numeric_value_available",
    "nwr_guidance_available",
    "nwr_score_status",
    "value_status",
    "review_flags",
    "warning",
    "rank",
    "tier",
    "draft_action",
    "warning_severity",
    "trap_caution_warning",
    "main_positive_reason",
    "main_risk_manual_question",
    "draft_room_note",
    "model_formula_version",
    "main_ranking_formula_changed",
    "board_order_changed",
    "production_allowed",
    "promotion_status",
    "source_overall_rank",
    "source_team",
    "source_manager",
    "allowed_use",
    "blocked_use",
)

PICK_COLUMNS = (
    "overall_pick",
    "round",
    "round_pick",
    "pick_label",
    "current_owner",
    "original_owner",
    "is_my_pick",
    "source_status",
    "source_season",
)


@dataclass(frozen=True)
class FrozenRookieKit:
    root: Path
    board_rows: tuple[dict[str, str], ...]
    quick_sheet_rows: tuple[dict[str, str], ...]
    review_warnings: tuple[str, ...]


@dataclass(frozen=True)
class CombinedSimulatorState:
    review_only: bool
    available_rows: tuple[dict[str, object], ...]
    pick_rows: tuple[dict[str, object], ...]
    draft_state: DraftBoardState
    manifest: dict[str, object]
    review_flags: dict[str, int]
    source_counts: dict[str, int]
    artifact_paths: dict[str, Path]


def load_frozen_rookie_kit(
    rookie_kit_root: str | Path = DEFAULT_ROOKIE_KIT_ROOT,
) -> FrozenRookieKit:
    root = Path(rookie_kit_root)
    board_path = root / ROOKIE_BOARD_FILE
    quick_sheet_path = root / ROOKIE_QUICK_SHEET_FILE
    warnings: list[str] = []
    if not board_path.exists():
        raise FileNotFoundError(f"Missing frozen rookie board: {board_path}")
    if not quick_sheet_path.exists():
        raise FileNotFoundError(f"Missing frozen rookie quick sheet: {quick_sheet_path}")
    board_rows = tuple(_read_csv(board_path))
    quick_sheet_rows = tuple(_read_csv(quick_sheet_path))
    if len(board_rows) != len(quick_sheet_rows):
        warnings.append("Frozen rookie board and quick sheet row counts differ.")
    board_players = [_player_key(row.get("player", "")) for row in board_rows]
    quick_players = [_player_key(row.get("player", "")) for row in quick_sheet_rows]
    if board_players != quick_players:
        warnings.append("Frozen rookie quick sheet order differs from board order.")
    return FrozenRookieKit(
        root=root,
        board_rows=board_rows,
        quick_sheet_rows=quick_sheet_rows,
        review_warnings=tuple(warnings),
    )


def build_combined_simulator_state(
    *,
    rookie_kit_root: str | Path = DEFAULT_ROOKIE_KIT_ROOT,
    snapshot_root: str | Path = DEFAULT_LVE_ROSTERS_061326_SNAPSHOT,
) -> CombinedSimulatorState:
    rookie_kit = load_frozen_rookie_kit(rookie_kit_root)
    snapshot = load_mock_draft_input_snapshot(snapshot_root)
    pick_rows = tuple(simulator_pick_rows_from_snapshot(snapshot))
    available_rows = tuple(
        [
            *_frozen_rookie_available_rows(rookie_kit),
            *_snapshot_available_rows(snapshot),
        ]
    )
    draft_state = create_empty_draft_state(
        pick_rows=pick_rows,
        available_rows=available_rows,
    )
    review_flags = _review_flag_counts(available_rows, snapshot)
    source_counts = Counter(str(row["source_label"]) for row in available_rows)
    manifest = _combined_manifest(
        rookie_kit=rookie_kit,
        snapshot=snapshot,
        available_rows=available_rows,
        pick_rows=pick_rows,
        review_flags=dict(review_flags),
        source_counts=dict(source_counts),
    )
    return CombinedSimulatorState(
        review_only=True,
        available_rows=available_rows,
        pick_rows=pick_rows,
        draft_state=draft_state,
        manifest=manifest,
        review_flags=dict(review_flags),
        source_counts=dict(source_counts),
        artifact_paths={},
    )


def write_combined_simulator_state_artifacts(
    state: CombinedSimulatorState,
    *,
    output_root: str | Path = DEFAULT_COMBINED_OUTPUT_ROOT,
) -> CombinedSimulatorState:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    available_path = root / "combined_available_pool_review_rows.csv"
    picks_path = root / "simulator_ready_2026_pick_rows.csv"
    flags_path = root / "review_flag_summary.csv"
    manifest_path = root / "combined_simulator_state_manifest.json"
    _write_csv(available_path, AVAILABLE_POOL_COLUMNS, state.available_rows)
    _write_csv(picks_path, PICK_COLUMNS, state.pick_rows)
    _write_csv(
        flags_path,
        ("review_flag", "count"),
        [
            {"review_flag": flag, "count": count}
            for flag, count in sorted(state.review_flags.items())
        ],
    )
    manifest = {
        **state.manifest,
        "artifact_paths": {
            "available_pool": str(available_path),
            "pick_rows": str(picks_path),
            "review_flags": str(flags_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return CombinedSimulatorState(
        review_only=state.review_only,
        available_rows=state.available_rows,
        pick_rows=state.pick_rows,
        draft_state=state.draft_state,
        manifest=manifest,
        review_flags=state.review_flags,
        source_counts=state.source_counts,
        artifact_paths={
            "available_pool": available_path,
            "pick_rows": picks_path,
            "review_flags": flags_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_combined_simulator_state(
    *,
    rookie_kit_root: str | Path = DEFAULT_ROOKIE_KIT_ROOT,
    snapshot_root: str | Path = DEFAULT_LVE_ROSTERS_061326_SNAPSHOT,
    output_root: str | Path = DEFAULT_COMBINED_OUTPUT_ROOT,
) -> CombinedSimulatorState:
    return write_combined_simulator_state_artifacts(
        build_combined_simulator_state(
            rookie_kit_root=rookie_kit_root,
            snapshot_root=snapshot_root,
        ),
        output_root=output_root,
    )


def _frozen_rookie_available_rows(rookie_kit: FrozenRookieKit) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in rookie_kit.board_rows:
        rank = _safe_int(row.get("rank"), default=len(rows) + 1)
        player = str(row.get("player") or "").strip()
        review_flags = ["frozen_rookie_guidance_read_only"]
        if not player or not str(row.get("position") or "").strip():
            review_flags.append("identity_review_required")
        rows.append(
            {
                "asset_id": f"frozen_rookie:{_player_key(player)}:rank{rank}",
                "player": player,
                "position": row.get("position") or "",
                "nfl_team": "",
                "source_label": "frozen_rookie",
                "asset_type": "Frozen Rookie",
                "asset_lifecycle": "incoming_rookie_frozen_manual_kit",
                "draft_rank": rank,
                "stats_model_value": 0.0,
                "market_value": 0.0,
                "market_edge": 0.0,
                "confidence": 75.0,
                "nwr_numeric_value_available": False,
                "nwr_guidance_available": True,
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
                "review_flags": "|".join(review_flags),
                "warning": row.get("warning_severity") or "",
                "rank": row.get("rank") or "",
                "tier": row.get("tier") or "",
                "draft_action": row.get("draft_action") or "",
                "warning_severity": row.get("warning_severity") or "",
                "trap_caution_warning": row.get("trap_caution_warning") or "",
                "main_positive_reason": row.get("main_positive_reason") or "",
                "main_risk_manual_question": row.get("main_risk_manual_question") or "",
                "draft_room_note": row.get("draft_room_note") or "",
                "model_formula_version": row.get("model_formula_version") or "",
                "main_ranking_formula_changed": row.get("main_ranking_formula_changed") or "",
                "board_order_changed": row.get("board_order_changed") or "",
                "production_allowed": row.get("production_allowed") or "",
                "promotion_status": row.get("promotion_status") or "",
                "source_overall_rank": "",
                "source_team": "",
                "source_manager": "",
                "allowed_use": "mock_draft_review_frozen_rookie_guidance_only",
                "blocked_use": "numeric_nwr_score_inference_or_rookie_board_mutation",
            }
        )
    return rows


def _snapshot_available_rows(snapshot: MockDraftInputSnapshot) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in review_available_player_rows_from_snapshot(snapshot):
        source_label = (
            "declared_drop" if str(row.get("asset_id") or "").startswith("declared_drop:")
            else "free_agent"
        )
        review_flags = ["value_neutral"]
        if source_label == "declared_drop":
            review_flags.append("declared_drop")
            if "Duplicate declared drop" in str(row.get("warning") or ""):
                review_flags.append("duplicate_drop_review_required")
        else:
            review_flags.append("free_agent")
        if not str(row.get("player") or "").strip() or not str(row.get("position") or "").strip():
            review_flags.append("identity_review_required")
        rows.append(
            {
                **_blank_rookie_guidance_fields(),
                **row,
                "source_label": source_label,
                "nwr_numeric_value_available": False,
                "nwr_guidance_available": False,
                "value_status": "value_neutral",
                "review_flags": "|".join(review_flags),
                "allowed_use": "mock_draft_review_availability_only",
                "blocked_use": "nwr_private_quality_value_or_production_rankings",
            }
        )
    return rows


def _combined_manifest(
    *,
    rookie_kit: FrozenRookieKit,
    snapshot: MockDraftInputSnapshot,
    available_rows: tuple[dict[str, object], ...],
    pick_rows: tuple[dict[str, object], ...],
    review_flags: dict[str, int],
    source_counts: dict[str, int],
) -> dict[str, object]:
    nwr_numeric_count = sum(
        1 for row in available_rows if bool(row.get("nwr_numeric_value_available"))
    )
    value_neutral_count = sum(
        1 for row in available_rows if row.get("value_status") == "value_neutral"
    )
    guidance_count = sum(
        1 for row in available_rows if bool(row.get("nwr_guidance_available"))
    )
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "rookie_kit_root": str(rookie_kit.root),
        "snapshot_root": str(snapshot.snapshot_root),
        "rookie_board_file": ROOKIE_BOARD_FILE,
        "rookie_quick_sheet_file": ROOKIE_QUICK_SHEET_FILE,
        "available_rows": len(available_rows),
        "pick_rows": len(pick_rows),
        "source_counts": source_counts,
        "frozen_rookie_rows": source_counts.get("frozen_rookie", 0),
        "declared_drop_rows": source_counts.get("declared_drop", 0),
        "free_agent_rows": source_counts.get("free_agent", 0),
        "nwr_numeric_private_value_rows": nwr_numeric_count,
        "frozen_rookie_guidance_rows": guidance_count,
        "value_neutral_rows": value_neutral_count,
        "review_flags": review_flags,
        "snapshot_audit_summary": snapshot_audit_summary(snapshot),
        "rookie_review_warnings": list(rookie_kit.review_warnings),
        "snapshot_review_warnings": list(snapshot.review_warnings),
        "nwr_score_policy": (
            "No numeric NWR score is invented from rookie rank, tier, action, "
            "snapshot rank, ADP, or market data."
        ),
        "market_adp_policy": (
            "ADP/market may be used only for opponent behavior, availability, "
            "and likely pick timing; it is not part of this combined NWR guidance state."
        ),
        "promotion_status": "local_review_input_only_not_promoted",
    }


def _review_flag_counts(
    rows: tuple[dict[str, object], ...],
    snapshot: MockDraftInputSnapshot,
) -> dict[str, int]:
    flags: Counter[str] = Counter()
    for row in rows:
        for flag in str(row.get("review_flags") or "").split("|"):
            if flag:
                flags[flag] += 1
    future_placeholder_count = int(snapshot_audit_summary(snapshot)["future_placeholder_pick_rows"])
    if future_placeholder_count:
        flags["future_placeholder_pick_review_required"] = future_placeholder_count
    return dict(flags)


def _blank_rookie_guidance_fields() -> dict[str, str]:
    return {field: "" for field in FROZEN_ROOKIE_GUIDANCE_FIELDS}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _safe_int(value: object, *, default: int) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _player_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower()) or "unknown"
