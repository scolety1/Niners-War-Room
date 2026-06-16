from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_RUN_ROOT = Path("local_exports/mock_draft/mock_draft_run_20260616")
DEFAULT_COMBINED_ROOT = Path("local_exports/mock_draft/combined_simulator_state_20260616")
DEFAULT_KIT_ROOT = Path("local_exports/mock_draft/draft_room_kit_20260616")
DEFAULT_OVERLAY_ROOT = Path(
    "local_exports/mock_draft/full_pool_visibility_overlay_20260616"
)

OVERLAY_COLUMNS = (
    "overall_pick",
    "pick_label",
    "round",
    "owning_team",
    "manager",
    "section",
    "section_order",
    "asset_id",
    "player",
    "position",
    "player_source",
    "rank",
    "tier",
    "draft_action",
    "warning_severity",
    "draft_room_note",
    "source_overall_rank",
    "source_team",
    "source_manager",
    "nwr_score_status",
    "value_status",
    "stats_model_value",
    "review_flags",
    "visibility_note",
    "ranking_policy",
)

REVIEW_REQUIRED_COLUMNS = (
    "overall_pick",
    "pick_label",
    "review_type",
    "asset_id",
    "player",
    "player_source",
    "review_flags",
    "review_note",
)


@dataclass(frozen=True)
class FullPoolVisibilityOverlay:
    review_only: bool
    overlay_rows: tuple[dict[str, object], ...]
    rookie_rows: tuple[dict[str, object], ...]
    value_neutral_rows: tuple[dict[str, object], ...]
    review_required_rows: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def build_full_pool_visibility_overlay(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    combined_root: str | Path = DEFAULT_COMBINED_ROOT,
    kit_root: str | Path = DEFAULT_KIT_ROOT,
) -> FullPoolVisibilityOverlay:
    run = Path(run_root)
    combined = Path(combined_root)
    kit = Path(kit_root)
    pick_rows = _read_csv(run / "mock_draft_pick_by_pick_review_rows.csv")
    available_rows = _read_csv(combined / "combined_available_pool_review_rows.csv")
    tim_windows = _read_csv(kit / "tim_pick_windows_quick_sheet.csv")
    run_manifest = json.loads((run / "mock_draft_run_manifest.json").read_text(encoding="utf-8"))

    available_by_asset = {row.get("asset_id", ""): row for row in available_rows}
    selected_by_pick = _selected_assets_by_pick(pick_rows)
    overlay_rows: list[dict[str, object]] = []
    rookie_rows: list[dict[str, object]] = []
    value_neutral_rows: list[dict[str, object]] = []
    review_required_rows: list[dict[str, object]] = []

    for window in tim_windows:
        overall_pick = _safe_int(window.get("overall_pick"), default=999)
        selected_before = {
            asset_id
            for pick, asset_id in selected_by_pick
            if pick < overall_pick and asset_id
        }
        still_available = [
            row
            for row in available_rows
            if row.get("asset_id", "") not in selected_before
        ]
        groups = {
            "frozen_rookie_options": [
                row for row in still_available if row.get("source_label") == "frozen_rookie"
            ],
            "declared_drop_value_neutral": [
                row for row in still_available if row.get("source_label") == "declared_drop"
            ],
            "free_agent_value_neutral": [
                row for row in still_available if row.get("source_label") == "free_agent"
            ],
        }
        for section, rows in groups.items():
            section_rows = sorted(rows, key=_section_sort_key)
            for index, row in enumerate(section_rows, start=1):
                overlay = _overlay_row(window, row, section=section, section_order=index)
                overlay_rows.append(overlay)
                if section == "frozen_rookie_options":
                    rookie_rows.append(overlay)
                else:
                    value_neutral_rows.append(overlay)
        review_required_rows.extend(
            _review_required_rows(
                window=window,
                still_available=still_available,
                run_manifest=run_manifest,
                available_by_asset=available_by_asset,
            )
        )

    manifest = _manifest(
        run_root=run,
        combined_root=combined,
        kit_root=kit,
        tim_windows=tim_windows,
        overlay_rows=overlay_rows,
        rookie_rows=rookie_rows,
        value_neutral_rows=value_neutral_rows,
        review_required_rows=review_required_rows,
    )
    return FullPoolVisibilityOverlay(
        review_only=True,
        overlay_rows=tuple(overlay_rows),
        rookie_rows=tuple(rookie_rows),
        value_neutral_rows=tuple(value_neutral_rows),
        review_required_rows=tuple(review_required_rows),
        manifest=manifest,
        artifact_paths={},
    )


def write_full_pool_visibility_overlay(
    overlay: FullPoolVisibilityOverlay,
    *,
    output_root: str | Path = DEFAULT_OVERLAY_ROOT,
) -> FullPoolVisibilityOverlay:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    overlay_path = root / "tim_full_pool_overlay_by_pick.csv"
    value_path = root / "tim_value_neutral_veterans_by_pick.csv"
    rookie_path = root / "tim_frozen_rookie_options_by_pick.csv"
    review_path = root / "tim_review_required_items_by_pick.csv"
    manifest_path = root / "full_pool_visibility_overlay_manifest.json"
    _write_csv(overlay_path, OVERLAY_COLUMNS, overlay.overlay_rows)
    _write_csv(value_path, OVERLAY_COLUMNS, overlay.value_neutral_rows)
    _write_csv(rookie_path, OVERLAY_COLUMNS, overlay.rookie_rows)
    _write_csv(review_path, REVIEW_REQUIRED_COLUMNS, overlay.review_required_rows)
    manifest = {
        **overlay.manifest,
        "artifact_paths": {
            "full_pool_overlay": str(overlay_path),
            "value_neutral_veterans": str(value_path),
            "frozen_rookies": str(rookie_path),
            "review_required": str(review_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return FullPoolVisibilityOverlay(
        review_only=overlay.review_only,
        overlay_rows=overlay.overlay_rows,
        rookie_rows=overlay.rookie_rows,
        value_neutral_rows=overlay.value_neutral_rows,
        review_required_rows=overlay.review_required_rows,
        manifest=manifest,
        artifact_paths={
            "full_pool_overlay": overlay_path,
            "value_neutral_veterans": value_path,
            "frozen_rookies": rookie_path,
            "review_required": review_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_full_pool_visibility_overlay(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    combined_root: str | Path = DEFAULT_COMBINED_ROOT,
    kit_root: str | Path = DEFAULT_KIT_ROOT,
    output_root: str | Path = DEFAULT_OVERLAY_ROOT,
) -> FullPoolVisibilityOverlay:
    return write_full_pool_visibility_overlay(
        build_full_pool_visibility_overlay(
            run_root=run_root,
            combined_root=combined_root,
            kit_root=kit_root,
        ),
        output_root=output_root,
    )


def _selected_assets_by_pick(pick_rows: list[dict[str, str]]) -> list[tuple[int, str]]:
    selected: list[tuple[int, str]] = []
    for row in pick_rows:
        asset_id = row.get("selected_asset_id", "")
        if asset_id:
            selected.append((_safe_int(row.get("overall_pick"), default=999), asset_id))
    return selected


def _overlay_row(
    window: dict[str, str],
    row: dict[str, str],
    *,
    section: str,
    section_order: int,
) -> dict[str, object]:
    source = row.get("source_label", "")
    return {
        "overall_pick": window.get("overall_pick", ""),
        "pick_label": window.get("pick_label", ""),
        "round": window.get("round", ""),
        "owning_team": window.get("owning_team", ""),
        "manager": window.get("manager", ""),
        "section": section,
        "section_order": section_order,
        "asset_id": row.get("asset_id", ""),
        "player": row.get("player", ""),
        "position": row.get("position", ""),
        "player_source": source,
        "rank": row.get("rank", ""),
        "tier": row.get("tier", ""),
        "draft_action": row.get("draft_action", ""),
        "warning_severity": row.get("warning_severity", ""),
        "draft_room_note": row.get("draft_room_note", ""),
        "source_overall_rank": row.get("source_overall_rank", ""),
        "source_team": row.get("source_team", ""),
        "source_manager": row.get("source_manager", ""),
        "nwr_score_status": row.get("nwr_score_status", ""),
        "value_status": row.get("value_status", ""),
        "stats_model_value": row.get("stats_model_value", "0.0"),
        "review_flags": row.get("review_flags", ""),
        "visibility_note": _visibility_note(source),
        "ranking_policy": _ranking_policy(source),
    }


def _review_required_rows(
    *,
    window: dict[str, str],
    still_available: list[dict[str, str]],
    run_manifest: dict[str, object],
    available_by_asset: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in still_available:
        flags = set(flag for flag in row.get("review_flags", "").split("|") if flag)
        if "duplicate_drop_review_required" in flags or "identity_review_required" in flags:
            rows.append(
                {
                    "overall_pick": window.get("overall_pick", ""),
                    "pick_label": window.get("pick_label", ""),
                    "review_type": (
                        "duplicate_drop_review_required"
                        if "duplicate_drop_review_required" in flags
                        else "identity_review_required"
                    ),
                    "asset_id": row.get("asset_id", ""),
                    "player": row.get("player", ""),
                    "player_source": row.get("source_label", ""),
                    "review_flags": row.get("review_flags", ""),
                    "review_note": _review_note(row.get("review_flags", "")),
                }
            )
    upstream = run_manifest.get("upstream_review_flags", {})
    future_count = 0
    if isinstance(upstream, dict):
        future_count = int(upstream.get("future_placeholder_pick_review_required", 0) or 0)
    if future_count:
        rows.append(
            {
                "overall_pick": window.get("overall_pick", ""),
                "pick_label": window.get("pick_label", ""),
                "review_type": "future_placeholder_pick_review_required",
                "asset_id": "",
                "player": "",
                "player_source": "future_pick_placeholder",
                "review_flags": "future_placeholder_pick_review_required",
                "review_note": (
                    f"{future_count} future 1.00 placeholder pick rows remain excluded "
                    "from simulator-ready windows."
                ),
            }
        )
    _ = available_by_asset
    return rows


def _manifest(
    *,
    run_root: Path,
    combined_root: Path,
    kit_root: Path,
    tim_windows: list[dict[str, str]],
    overlay_rows: list[dict[str, object]],
    rookie_rows: list[dict[str, object]],
    value_neutral_rows: list[dict[str, object]],
    review_required_rows: list[dict[str, object]],
) -> dict[str, object]:
    by_pick = _counts_by_pick(overlay_rows)
    review_by_type = Counter(str(row["review_type"]) for row in review_required_rows)
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "source_run_root": str(run_root),
        "source_combined_state_root": str(combined_root),
        "source_draft_room_kit_root": str(kit_root),
        "tim_pick_window_count": len(tim_windows),
        "full_pool_overlay_rows": len(overlay_rows),
        "frozen_rookie_option_rows": len(rookie_rows),
        "declared_drop_rows": sum(
            1 for row in value_neutral_rows if row["player_source"] == "declared_drop"
        ),
        "free_agent_rows": sum(
            1 for row in value_neutral_rows if row["player_source"] == "free_agent"
        ),
        "value_neutral_rows": len(value_neutral_rows),
        "review_required_rows": len(review_required_rows),
        "review_required_rows_by_type": dict(sorted(review_by_type.items())),
        "rows_by_pick_and_section": by_pick,
        "count_semantics": (
            "Overlay row counts are window-level visibility rows across Tim/Niners "
            "pick windows, not unique-player counts."
        ),
        "score_policy": (
            "No numeric NWR score is invented by the overlay; stats_model_value remains "
            "the copied review artifact field and is not used for NWR ranking."
        ),
        "market_policy": (
            "ADP/market is not used by the overlay as NWR value or rookie guidance."
        ),
        "ranking_policy": (
            "Frozen rookies, declared drops, and free agents are displayed in separate "
            "sections; value-neutral veterans/free agents are not ranked against frozen "
            "rookies as NWR quality."
        ),
        "tim_pick_policy": "Tim/Niners picks remain manual-review only with no auto-final pick.",
        "promotion_status": "local_full_pool_visibility_overlay_only_not_app_wired_not_promoted",
    }


def _counts_by_pick(rows: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = {}
    for row in rows:
        pick = str(row["pick_label"])
        grouped.setdefault(pick, Counter())
        grouped[pick][str(row["section"])] += 1
    return {
        pick: dict(sorted(counts.items()))
        for pick, counts in sorted(grouped.items())
    }


def _section_sort_key(row: dict[str, str]) -> tuple[int, str, str]:
    return (
        _safe_int(row.get("draft_rank") or row.get("source_overall_rank"), default=999),
        row.get("player", ""),
        row.get("asset_id", ""),
    )


def _visibility_note(source: str) -> str:
    if source == "frozen_rookie":
        return "Frozen rookie guidance is copied read-only."
    if source == "declared_drop":
        return "Declared drop is visible as value-neutral review context."
    if source == "free_agent":
        return "Free agent is visible as value-neutral review context."
    return "Review-only visibility row."


def _ranking_policy(source: str) -> str:
    if source == "frozen_rookie":
        return "Ordered only within frozen rookie section by copied frozen board order."
    return (
        "Ordered only within value-neutral section by source review rank context; "
        "not ranked against rookies as NWR quality."
    )


def _review_note(flags: str) -> str:
    if "duplicate_drop_review_required" in flags:
        return "Duplicate declared drop remains unresolved; do not silently dedupe."
    if "identity_review_required" in flags:
        return "Missing identity/data fields require manual review."
    return "Review before draft-day use."


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
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
