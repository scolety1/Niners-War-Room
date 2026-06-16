from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_RUN_ROOT = Path("local_exports/mock_draft/mock_draft_run_20260616")
DEFAULT_DRAFT_ROOM_KIT_ROOT = Path("local_exports/mock_draft/draft_room_kit_20260616")

TIM_PICK_WINDOWS_COLUMNS = (
    "overall_pick",
    "round",
    "pick_label",
    "owning_team",
    "manager",
    "selection_mode",
    "manual_review_status",
    "shortlist_rows",
    "frozen_rookie_options",
    "value_neutral_options",
    "top_frozen_rookie_options",
    "value_neutral_names",
    "review_flags",
    "draft_room_notes",
    "score_policy",
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
    "draft_room_use",
)

OPPONENT_SUMMARY_COLUMNS = (
    "owning_team",
    "opponent_picks",
    "frozen_rookie_count",
    "declared_drop_count",
    "free_agent_count",
    "market_context_used_count",
    "selection_modes",
    "first_pick",
    "selected_players",
    "behavior_note",
)

REVIEW_FLAGS_COLUMNS = (
    "flag_type",
    "flag",
    "count",
    "example_players_or_picks",
    "review_note",
)


@dataclass(frozen=True)
class DraftRoomKit:
    review_only: bool
    tim_pick_windows: tuple[dict[str, object], ...]
    tim_shortlist_rows: tuple[dict[str, object], ...]
    opponent_summary_rows: tuple[dict[str, object], ...]
    review_flag_rows: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def build_draft_room_kit(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
) -> DraftRoomKit:
    root = Path(run_root)
    pick_rows = _read_csv(root / "mock_draft_pick_by_pick_review_rows.csv")
    shortlist_rows = _read_csv(root / "tim_pick_shortlist_review_rows.csv")
    notes_rows = _read_csv(root / "opponent_behavior_notes.csv")
    manifest = json.loads((root / "mock_draft_run_manifest.json").read_text(encoding="utf-8"))

    tim_windows = _tim_pick_windows(pick_rows, shortlist_rows)
    manual_shortlist = _manual_shortlist_rows(shortlist_rows)
    opponent_summary = _opponent_summary_rows(pick_rows, notes_rows)
    review_flags = _review_flag_rows(pick_rows, shortlist_rows, manifest)
    kit_manifest = _manifest(
        run_root=root,
        run_manifest=manifest,
        tim_windows=tim_windows,
        manual_shortlist=manual_shortlist,
        opponent_summary=opponent_summary,
        review_flags=review_flags,
    )
    return DraftRoomKit(
        review_only=True,
        tim_pick_windows=tuple(tim_windows),
        tim_shortlist_rows=tuple(manual_shortlist),
        opponent_summary_rows=tuple(opponent_summary),
        review_flag_rows=tuple(review_flags),
        manifest=kit_manifest,
        artifact_paths={},
    )


def write_draft_room_kit(
    kit: DraftRoomKit,
    *,
    output_root: str | Path = DEFAULT_DRAFT_ROOM_KIT_ROOT,
) -> DraftRoomKit:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    windows_path = root / "tim_pick_windows_quick_sheet.csv"
    shortlist_path = root / "tim_manual_pick_shortlist_by_pick.csv"
    opponent_path = root / "opponent_run_summary.csv"
    flags_path = root / "review_flags_to_resolve_before_draft.csv"
    manifest_path = root / "draft_room_kit_manifest.json"
    _write_csv(windows_path, TIM_PICK_WINDOWS_COLUMNS, kit.tim_pick_windows)
    _write_csv(shortlist_path, TIM_SHORTLIST_COLUMNS, kit.tim_shortlist_rows)
    _write_csv(opponent_path, OPPONENT_SUMMARY_COLUMNS, kit.opponent_summary_rows)
    _write_csv(flags_path, REVIEW_FLAGS_COLUMNS, kit.review_flag_rows)
    manifest = {
        **kit.manifest,
        "artifact_paths": {
            "tim_pick_windows": str(windows_path),
            "tim_manual_shortlist": str(shortlist_path),
            "opponent_run_summary": str(opponent_path),
            "review_flags": str(flags_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return DraftRoomKit(
        review_only=kit.review_only,
        tim_pick_windows=kit.tim_pick_windows,
        tim_shortlist_rows=kit.tim_shortlist_rows,
        opponent_summary_rows=kit.opponent_summary_rows,
        review_flag_rows=kit.review_flag_rows,
        manifest=manifest,
        artifact_paths={
            "tim_pick_windows": windows_path,
            "tim_manual_shortlist": shortlist_path,
            "opponent_run_summary": opponent_path,
            "review_flags": flags_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_draft_room_kit(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    output_root: str | Path = DEFAULT_DRAFT_ROOM_KIT_ROOT,
) -> DraftRoomKit:
    return write_draft_room_kit(
        build_draft_room_kit(run_root=run_root),
        output_root=output_root,
    )


def _tim_pick_windows(
    pick_rows: list[dict[str, str]],
    shortlist_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    shortlist_by_pick: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in shortlist_rows:
        shortlist_by_pick[str(row.get("overall_pick") or "")].append(row)
    windows: list[dict[str, object]] = []
    for pick in pick_rows:
        if str(pick.get("selection_mode") or "") != "Tim_review_pick":
            continue
        rows = sorted(
            shortlist_by_pick.get(str(pick.get("overall_pick") or ""), []),
            key=lambda row: _safe_int(row.get("shortlist_rank"), default=999),
        )
        frozen = [row for row in rows if row.get("player_source") == "frozen_rookie"]
        value_neutral = [row for row in rows if row.get("value_status") == "value_neutral"]
        flags = _flag_summary(rows)
        notes = [
            row.get("draft_room_note", "")
            for row in frozen[:3]
            if row.get("draft_room_note")
        ]
        windows.append(
            {
                "overall_pick": pick.get("overall_pick") or "",
                "round": pick.get("round") or "",
                "pick_label": pick.get("pick_label") or "",
                "owning_team": pick.get("owning_team") or "",
                "manager": pick.get("manager") or "",
                "selection_mode": pick.get("selection_mode") or "",
                "manual_review_status": "manual_review_only_no_auto_best_pick",
                "shortlist_rows": len(rows),
                "frozen_rookie_options": len(frozen),
                "value_neutral_options": len(value_neutral),
                "top_frozen_rookie_options": _join_names(frozen[:5]),
                "value_neutral_names": _join_names(value_neutral[:5]),
                "review_flags": "|".join(flags),
                "draft_room_notes": " || ".join(notes),
                "score_policy": (
                    "No numeric NWR score is invented; rookie guidance copied read-only; "
                    "ADP/market is not NWR value."
                ),
            }
        )
    return windows


def _manual_shortlist_rows(shortlist_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in shortlist_rows:
        rows.append(
            {
                **row,
                "draft_room_use": (
                    "manual_review_option; not an auto-final best pick; "
                    "value-neutral rows are clearly marked"
                ),
            }
        )
    return rows


def _opponent_summary_rows(
    pick_rows: list[dict[str, str]],
    notes_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    notes_by_pick = {row.get("overall_pick", ""): row for row in notes_rows}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pick_rows:
        if str(row.get("selection_mode") or "").startswith("opponent"):
            grouped[row.get("owning_team", "")].append(row)
    out: list[dict[str, object]] = []
    for team, rows in sorted(grouped.items()):
        source_counts = Counter(row.get("selected_player_source", "") for row in rows)
        mode_counts = Counter(row.get("selection_mode", "") for row in rows)
        market_used = sum(_truthy(row.get("market_context_used")) for row in rows)
        first_pick = min(_safe_int(row.get("overall_pick"), default=999) for row in rows)
        notes = [
            notes_by_pick.get(row.get("overall_pick", ""), {}).get("note", "")
            for row in rows[:2]
        ]
        out.append(
            {
                "owning_team": team,
                "opponent_picks": len(rows),
                "frozen_rookie_count": source_counts.get("frozen_rookie", 0),
                "declared_drop_count": source_counts.get("declared_drop", 0),
                "free_agent_count": source_counts.get("free_agent", 0),
                "market_context_used_count": market_used,
                "selection_modes": "|".join(
                    f"{mode}:{count}" for mode, count in sorted(mode_counts.items())
                ),
                "first_pick": first_pick,
                "selected_players": _join_selected_players(rows),
                "behavior_note": " || ".join(note for note in notes if note),
            }
        )
    return out


def _review_flag_rows(
    pick_rows: list[dict[str, str]],
    shortlist_rows: list[dict[str, str]],
    manifest: dict[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    grouped_examples: dict[str, list[str]] = defaultdict(list)
    grouped_counts: Counter[str] = Counter()
    for row in [*pick_rows, *shortlist_rows]:
        label = row.get("selected_player") or row.get("player") or row.get("pick_label") or ""
        for flag in str(row.get("review_flags") or "").split("|"):
            if flag:
                grouped_counts[flag] += 1
                if label and len(grouped_examples[flag]) < 8:
                    grouped_examples[flag].append(label)
    upstream_flags = manifest.get("upstream_review_flags", {})
    if isinstance(upstream_flags, dict):
        for flag, count in upstream_flags.items():
            grouped_counts.setdefault(flag, int(count))
    for flag, count in sorted(grouped_counts.items()):
        rows.append(
            {
                "flag_type": _flag_type(flag),
                "flag": flag,
                "count": count,
                "example_players_or_picks": " | ".join(grouped_examples.get(flag, [])),
                "review_note": _review_note(flag),
            }
        )
    return rows


def _manifest(
    *,
    run_root: Path,
    run_manifest: dict[str, object],
    tim_windows: list[dict[str, object]],
    manual_shortlist: list[dict[str, object]],
    opponent_summary: list[dict[str, object]],
    review_flags: list[dict[str, object]],
) -> dict[str, object]:
    value_neutral_rows = sum(
        1 for row in manual_shortlist if row.get("value_status") == "value_neutral"
    )
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "source_run_root": str(run_root),
        "source_run_manifest": str(run_root / "mock_draft_run_manifest.json"),
        "input_artifacts": {
            "pick_by_pick": str(run_root / "mock_draft_pick_by_pick_review_rows.csv"),
            "tim_shortlist": str(run_root / "tim_pick_shortlist_review_rows.csv"),
            "opponent_behavior_notes": str(run_root / "opponent_behavior_notes.csv"),
            "manifest": str(run_root / "mock_draft_run_manifest.json"),
        },
        "tim_pick_window_count": len(tim_windows),
        "tim_shortlist_row_count": len(manual_shortlist),
        "opponent_summary_row_count": len(opponent_summary),
        "review_flag_row_count": len(review_flags),
        "value_neutral_shortlist_rows": value_neutral_rows,
        "run_pick_by_pick_rows": run_manifest.get("pick_by_pick_rows"),
        "run_review_flag_count_semantics": run_manifest.get("review_flag_count_semantics"),
        "score_policy": (
            "No numeric NWR score is invented by the draft-room kit; source stats_model_value "
            "is copied only to preserve the review artifact and remains zero in current inputs."
        ),
        "market_policy": (
            "ADP/market context, if present in run artifacts, remains behavior-only and is "
            "not used as NWR value or rookie guidance."
        ),
        "tim_pick_policy": (
            "Tim/Niners windows are manual-review only; no auto-final best pick is created."
        ),
        "promotion_status": "local_draft_room_review_kit_only_not_app_wired_not_promoted",
    }


def _flag_summary(rows: list[dict[str, str]]) -> list[str]:
    flags: set[str] = set()
    for row in rows:
        for flag in str(row.get("review_flags") or "").split("|"):
            if flag:
                flags.add(flag)
    return sorted(flags)


def _join_names(rows: list[dict[str, str]]) -> str:
    return " | ".join(row.get("player", "") for row in rows if row.get("player"))


def _join_selected_players(rows: list[dict[str, str]]) -> str:
    return " | ".join(
        row.get("selected_player", "")
        for row in rows
        if row.get("selected_player")
    )


def _flag_type(flag: str) -> str:
    if flag == "duplicate_drop_review_required":
        return "Brock Purdy duplicate drop declaration"
    if flag == "future_placeholder_pick_review_required":
        return "future placeholder picks excluded from simulator"
    if flag in {"value_neutral", "declared_drop", "free_agent"}:
        return "value-neutral veterans/free agents"
    if flag == "frozen_rookie_guidance_read_only":
        return "frozen rookie guidance read-only"
    if flag == "identity_review_required":
        return "missing identity/data fields"
    if flag == "tim_manual_review_required":
        return "Tim manual pick review"
    return "other review flag"


def _review_note(flag: str) -> str:
    notes = {
        "duplicate_drop_review_required": (
            "Brock Purdy duplicate declaration is preserved; resolve before final use."
        ),
        "future_placeholder_pick_review_required": (
            "Future 1.00 placeholder picks are excluded from simulator-ready draft rows."
        ),
        "value_neutral": (
            "Snapshot-only veterans/free agents remain value-neutral; no NWR score was inferred."
        ),
        "declared_drop": "Declared drops are available-pool review rows, not model promotions.",
        "free_agent": "Free agents are snapshot review rows, not private-value rows.",
        "frozen_rookie_guidance_read_only": (
            "Frozen rookie rank/tier/action/note fields are copied read-only."
        ),
        "identity_review_required": "Missing identity/data fields require manual review.",
        "tim_manual_review_required": "Tim/Niners pick remains manual-review only.",
    }
    return notes.get(flag, "Review before draft-day use.")


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


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}
