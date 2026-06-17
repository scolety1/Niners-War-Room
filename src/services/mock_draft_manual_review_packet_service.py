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

DEFAULT_MANUAL_REVIEW_PACKET_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/manual_review_packet_20260617"
)

MANUAL_PICK_COLUMNS = (
    "pick_label",
    "overall_pick",
    "owning_team",
    "manager",
    "option_rank",
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
    "value_status",
    "nwr_score_status",
    "stats_model_value",
    "manual_decision",
    "manual_notes",
    "resolved_by",
    "resolution_status",
)
BROCK_DUPLICATE_COLUMNS = (
    "asset_id",
    "player",
    "position",
    "source_label",
    "review_flags",
    "value_status",
    "resolution_status",
    "manual_decision",
    "manual_notes",
    "resolved_by",
)
PLACEHOLDER_COLUMNS = (
    "placeholder_index",
    "review_flag",
    "simulator_ready",
    "resolution_status",
    "manual_decision",
    "manual_notes",
    "resolved_by",
)
VALUE_NEUTRAL_COLUMNS = (
    "asset_id",
    "player",
    "position",
    "source_label",
    "review_flags",
    "value_status",
    "visibility_only_note",
    "manual_decision",
    "manual_notes",
    "resolved_by",
    "resolution_status",
)
CHECKLIST_COLUMNS = (
    "check_id",
    "status",
    "item",
    "detail",
    "required_before_draft",
    "resolution_status",
    "manual_notes",
)


@dataclass(frozen=True)
class ManualReviewPacket:
    review_only: bool
    manual_pick_rows: tuple[dict[str, object], ...]
    brock_duplicate_rows: tuple[dict[str, object], ...]
    placeholder_pick_rows: tuple[dict[str, object], ...]
    value_neutral_rows: tuple[dict[str, object], ...]
    blocker_checklist_rows: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def build_manual_review_packet(
    combined_state: CombinedSimulatorState | None = None,
    *,
    options_per_pick: int = 8,
) -> ManualReviewPacket:
    state = combined_state or build_combined_simulator_state()
    tim_picks = [row for row in state.pick_rows if bool(row.get("is_my_pick"))]
    manual_pick_rows = _manual_pick_rows(
        tim_picks=tim_picks,
        available_rows=state.available_rows,
        options_per_pick=options_per_pick,
    )
    brock_rows = _brock_duplicate_rows(state.available_rows)
    placeholder_rows = _placeholder_pick_rows(state.review_flags)
    value_neutral_rows = _value_neutral_rows(state.available_rows)
    checklist_rows = _blocker_checklist_rows(
        brock_rows=brock_rows,
        placeholder_rows=placeholder_rows,
        value_neutral_rows=value_neutral_rows,
    )
    manifest = _manifest(
        manual_pick_rows=manual_pick_rows,
        brock_rows=brock_rows,
        placeholder_rows=placeholder_rows,
        value_neutral_rows=value_neutral_rows,
        checklist_rows=checklist_rows,
    )
    return ManualReviewPacket(
        review_only=True,
        manual_pick_rows=tuple(manual_pick_rows),
        brock_duplicate_rows=tuple(brock_rows),
        placeholder_pick_rows=tuple(placeholder_rows),
        value_neutral_rows=tuple(value_neutral_rows),
        blocker_checklist_rows=tuple(checklist_rows),
        manifest=manifest,
        artifact_paths={},
    )


def write_manual_review_packet_artifacts(
    packet: ManualReviewPacket,
    *,
    output_root: str | Path = DEFAULT_MANUAL_REVIEW_PACKET_OUTPUT_ROOT,
) -> ManualReviewPacket:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    manual_path = root / "manual_pick_decision_packet.csv"
    brock_path = root / "brock_purdy_duplicate_review.csv"
    placeholder_path = root / "future_placeholder_pick_review.csv"
    value_neutral_path = root / "value_neutral_player_review_inventory.csv"
    checklist_path = root / "pre_draft_blocker_checklist.csv"
    manifest_path = root / "manual_review_packet_manifest.json"
    _write_csv(manual_path, MANUAL_PICK_COLUMNS, packet.manual_pick_rows)
    _write_csv(brock_path, BROCK_DUPLICATE_COLUMNS, packet.brock_duplicate_rows)
    _write_csv(placeholder_path, PLACEHOLDER_COLUMNS, packet.placeholder_pick_rows)
    _write_csv(value_neutral_path, VALUE_NEUTRAL_COLUMNS, packet.value_neutral_rows)
    _write_csv(checklist_path, CHECKLIST_COLUMNS, packet.blocker_checklist_rows)
    manifest = {
        **packet.manifest,
        "artifact_paths": {
            "manual_pick_decision_packet": str(manual_path),
            "brock_purdy_duplicate_review": str(brock_path),
            "future_placeholder_pick_review": str(placeholder_path),
            "value_neutral_inventory": str(value_neutral_path),
            "pre_draft_blocker_checklist": str(checklist_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return ManualReviewPacket(
        review_only=packet.review_only,
        manual_pick_rows=packet.manual_pick_rows,
        brock_duplicate_rows=packet.brock_duplicate_rows,
        placeholder_pick_rows=packet.placeholder_pick_rows,
        value_neutral_rows=packet.value_neutral_rows,
        blocker_checklist_rows=packet.blocker_checklist_rows,
        manifest=manifest,
        artifact_paths={
            "manual_pick_decision_packet": manual_path,
            "brock_purdy_duplicate_review": brock_path,
            "future_placeholder_pick_review": placeholder_path,
            "value_neutral_inventory": value_neutral_path,
            "pre_draft_blocker_checklist": checklist_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_manual_review_packet(
    *,
    output_root: str | Path = DEFAULT_MANUAL_REVIEW_PACKET_OUTPUT_ROOT,
) -> ManualReviewPacket:
    return write_manual_review_packet_artifacts(
        build_manual_review_packet(),
        output_root=output_root,
    )


def _manual_pick_rows(
    *,
    tim_picks: Sequence[Mapping[str, object]],
    available_rows: Sequence[Mapping[str, object]],
    options_per_pick: int,
) -> list[dict[str, object]]:
    ordered_options = sorted(available_rows, key=_manual_option_sort_key)[:options_per_pick]
    rows: list[dict[str, object]] = []
    for pick in tim_picks:
        for index, option in enumerate(ordered_options, start=1):
            rows.append(
                {
                    "pick_label": pick.get("pick_label") or "",
                    "overall_pick": pick.get("overall_pick") or "",
                    "owning_team": pick.get("current_owner") or "",
                    "manager": pick.get("manager") or "",
                    "option_rank": index,
                    "asset_id": option.get("asset_id") or "",
                    "player": option.get("player") or "",
                    "position": option.get("position") or "",
                    "player_source": option.get("source_label") or "",
                    "rank": option.get("rank") or "",
                    "tier": option.get("tier") or "",
                    "draft_action": option.get("draft_action") or "",
                    "warning_severity": option.get("warning_severity") or "",
                    "draft_room_note": option.get("draft_room_note") or "",
                    "review_flags": option.get("review_flags") or "",
                    "value_status": option.get("value_status") or "",
                    "nwr_score_status": option.get("nwr_score_status") or "",
                    "stats_model_value": option.get("stats_model_value", 0.0),
                    "manual_decision": "",
                    "manual_notes": "",
                    "resolved_by": "",
                    "resolution_status": "manual_review_pending",
                }
            )
    return rows


def _brock_duplicate_rows(
    available_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in available_rows:
        if "duplicate_drop_review_required" not in str(row.get("review_flags") or ""):
            continue
        if str(row.get("player") or "").lower().replace(" ", "") != "brockpurdy":
            continue
        rows.append(
            {
                "asset_id": row.get("asset_id") or "",
                "player": row.get("player") or "",
                "position": row.get("position") or "",
                "source_label": row.get("source_label") or "",
                "review_flags": row.get("review_flags") or "",
                "value_status": row.get("value_status") or "",
                "resolution_status": "unresolved_review_required",
                "manual_decision": "",
                "manual_notes": "",
                "resolved_by": "",
            }
        )
    return rows


def _placeholder_pick_rows(review_flags: Mapping[str, int]) -> list[dict[str, object]]:
    count = int(review_flags.get("future_placeholder_pick_review_required", 0))
    return [
        {
            "placeholder_index": index,
            "review_flag": "future_placeholder_pick_review_required",
            "simulator_ready": False,
            "resolution_status": "excluded_review_required",
            "manual_decision": "",
            "manual_notes": "",
            "resolved_by": "",
        }
        for index in range(1, count + 1)
    ]


def _value_neutral_rows(
    available_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in available_rows:
        if row.get("value_status") != "value_neutral":
            continue
        rows.append(
            {
                "asset_id": row.get("asset_id") or "",
                "player": row.get("player") or "",
                "position": row.get("position") or "",
                "source_label": row.get("source_label") or "",
                "review_flags": row.get("review_flags") or "",
                "value_status": row.get("value_status") or "",
                "visibility_only_note": (
                    "Value-neutral manual review only; not ranked against rookies as "
                    "NWR quality."
                ),
                "manual_decision": "",
                "manual_notes": "",
                "resolved_by": "",
                "resolution_status": "manual_review_pending",
            }
        )
    return rows


def _blocker_checklist_rows(
    *,
    brock_rows: Sequence[Mapping[str, object]],
    placeholder_rows: Sequence[Mapping[str, object]],
    value_neutral_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "check_id": "review_only_layers_committed",
            "status": "GREEN",
            "item": "Review-only mock draft layers",
            "detail": "Committed services remain outside app and production outputs.",
            "required_before_draft": False,
            "resolution_status": "accepted",
            "manual_notes": "",
        },
        {
            "check_id": "brock_purdy_duplicate",
            "status": "YELLOW" if brock_rows else "GREEN",
            "item": "Brock Purdy duplicate drop declaration",
            "detail": f"{len(brock_rows)} duplicate rows preserved for manual review.",
            "required_before_draft": True,
            "resolution_status": "manual_review_pending" if brock_rows else "accepted",
            "manual_notes": "",
        },
        {
            "check_id": "future_placeholder_picks",
            "status": "YELLOW" if placeholder_rows else "GREEN",
            "item": "Future 1.00 placeholder picks",
            "detail": (
                f"{len(placeholder_rows)} placeholders remain excluded from simulation."
            ),
            "required_before_draft": False,
            "resolution_status": "manual_review_pending" if placeholder_rows else "accepted",
            "manual_notes": "",
        },
        {
            "check_id": "value_neutral_inventory",
            "status": "YELLOW" if value_neutral_rows else "GREEN",
            "item": "Snapshot-only veterans/free agents",
            "detail": f"{len(value_neutral_rows)} rows remain value-neutral visibility only.",
            "required_before_draft": False,
            "resolution_status": "manual_review_pending",
            "manual_notes": "",
        },
        {
            "check_id": "market_firewall",
            "status": "GREEN",
            "item": "ADP/market firewall",
            "detail": "No ADP/market field becomes NWR quality or rookie guidance.",
            "required_before_draft": True,
            "resolution_status": "accepted",
            "manual_notes": "",
        },
    ]


def _manual_option_sort_key(row: Mapping[str, object]) -> tuple[object, ...]:
    source = str(row.get("source_label") or "")
    priority = {"frozen_rookie": 0, "declared_drop": 1, "free_agent": 2}.get(source, 99)
    return (
        priority,
        int(row.get("draft_rank") or 999),
        str(row.get("player") or ""),
        str(row.get("asset_id") or ""),
    )


def _manifest(
    *,
    manual_pick_rows: Sequence[Mapping[str, object]],
    brock_rows: Sequence[Mapping[str, object]],
    placeholder_rows: Sequence[Mapping[str, object]],
    value_neutral_rows: Sequence[Mapping[str, object]],
    checklist_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    flags: Counter[str] = Counter()
    for row in value_neutral_rows:
        for flag in str(row.get("review_flags") or "").split("|"):
            if flag:
                flags[flag] += 1
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "manual_pick_rows": len(manual_pick_rows),
        "brock_purdy_duplicate_rows": len(brock_rows),
        "future_placeholder_pick_rows": len(placeholder_rows),
        "value_neutral_inventory_rows": len(value_neutral_rows),
        "pre_draft_blocker_rows": len(checklist_rows),
        "review_flags": dict(sorted(flags.items())),
        "manual_field_policy": (
            "manual_decision, manual_notes, resolved_by, and resolution_status are "
            "blank/manual-only review fields and do not feed NWR value."
        ),
        "rookie_guidance_policy": "Frozen rookie guidance remains read-only.",
        "value_neutral_policy": (
            "Value-neutral veterans/free agents remain visible but are not ranked "
            "against rookies as NWR quality."
        ),
        "market_policy": "ADP/market fields do not become NWR quality.",
        "nwr_score_policy": "No numeric NWR score is invented.",
        "promotion_status": "local_review_output_only_not_app_wired_not_promoted",
    }


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: Sequence[Mapping[str, object]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
