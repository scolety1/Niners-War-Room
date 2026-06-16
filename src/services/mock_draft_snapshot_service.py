from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LVE_ROSTERS_061326_SNAPSHOT = Path(
    "local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326"
)


@dataclass(frozen=True)
class MockDraftInputSnapshot:
    snapshot_root: Path
    manifest: dict[str, object]
    roster_rows: tuple[dict[str, str], ...]
    pick_rows: tuple[dict[str, str], ...]
    free_agent_rows: tuple[dict[str, str], ...]
    declared_drop_rows: tuple[dict[str, str], ...]
    review_warnings: tuple[str, ...]

    @property
    def duplicate_declared_drop_counts(self) -> dict[str, int]:
        return {
            player: count
            for player, count in Counter(
                row.get("normalized_player_key", "") for row in self.declared_drop_rows
            ).items()
            if player and count > 1
        }


def load_mock_draft_input_snapshot(
    snapshot_root: str | Path = DEFAULT_LVE_ROSTERS_061326_SNAPSHOT,
) -> MockDraftInputSnapshot:
    root = Path(snapshot_root)
    manifest = json.loads((root / "extraction_manifest.json").read_text(encoding="utf-8"))
    roster_rows = tuple(_read_csv(root / "roster_rows_normalized_review.csv"))
    pick_rows = tuple(_read_csv(root / "draft_pick_rows_normalized_review.csv"))
    free_agent_rows = tuple(_read_csv(root / "free_agent_rows_normalized_review.csv"))
    declared_drop_rows = tuple(_read_csv(root / "declared_top_five_drops_20260616.csv"))
    warnings = _snapshot_warnings(
        manifest=manifest,
        roster_rows=roster_rows,
        pick_rows=pick_rows,
        free_agent_rows=free_agent_rows,
        declared_drop_rows=declared_drop_rows,
    )
    return MockDraftInputSnapshot(
        snapshot_root=root,
        manifest=manifest,
        roster_rows=roster_rows,
        pick_rows=pick_rows,
        free_agent_rows=free_agent_rows,
        declared_drop_rows=declared_drop_rows,
        review_warnings=tuple(warnings),
    )


def simulator_pick_rows_from_snapshot(
    snapshot: MockDraftInputSnapshot,
    *,
    season: str = "2026",
    teams: int = 10,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in snapshot.pick_rows:
        if str(raw.get("season") or "") != season:
            continue
        parsed = _parse_pick_label(raw.get("pick_label", ""), teams=teams)
        if parsed is None:
            continue
        round_number, round_pick, overall_pick = parsed
        rows.append(
            {
                "overall_pick": overall_pick,
                "round": round_number,
                "round_pick": round_pick,
                "pick_label": str(raw.get("pick_label") or ""),
                "current_owner": str(raw.get("current_owner") or ""),
                "manager": str(raw.get("manager") or ""),
                "original_owner": str(raw.get("original_owner") or ""),
                "is_my_pick": _truthy(raw.get("is_niners_pick")),
                "source_status": raw.get("input_status") or "",
                "source_season": season,
            }
        )
    return sorted(
        rows,
        key=lambda row: (int(row["overall_pick"]), str(row["current_owner"])),
    )


def review_available_player_rows_from_snapshot(
    snapshot: MockDraftInputSnapshot,
    *,
    include_declared_drops: bool = True,
    include_free_agents: bool = True,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if include_declared_drops:
        rows.extend(_declared_drop_available_rows(snapshot.declared_drop_rows))
    if include_free_agents:
        rows.extend(_free_agent_available_rows(snapshot.free_agent_rows))
    return sorted(
        rows,
        key=lambda row: (
            int(row["draft_rank"]),
            str(row["asset_type"]),
            str(row["player"]),
            str(row["asset_id"]),
        ),
    )


def snapshot_audit_summary(snapshot: MockDraftInputSnapshot) -> dict[str, object]:
    simulator_picks = simulator_pick_rows_from_snapshot(snapshot)
    available_rows = review_available_player_rows_from_snapshot(snapshot)
    niners_picks = [row["pick_label"] for row in simulator_picks if row["is_my_pick"]]
    future_placeholder_count = sum(
        1
        for row in snapshot.pick_rows
        if str(row.get("season") or "") != "2026"
        and str(row.get("pick_label") or "").endswith(".00")
    )
    return {
        "review_only": bool(snapshot.manifest.get("review_only")),
        "roster_rows": len(snapshot.roster_rows),
        "draft_pick_rows": len(snapshot.pick_rows),
        "free_agent_rows": len(snapshot.free_agent_rows),
        "declared_drop_rows": len(snapshot.declared_drop_rows),
        "declared_drop_unique_players": len(
            {row.get("normalized_player_key", "") for row in snapshot.declared_drop_rows}
        ),
        "duplicate_declared_drops": snapshot.duplicate_declared_drop_counts,
        "simulator_ready_2026_picks": len(simulator_picks),
        "simulator_ready_available_rows": len(available_rows),
        "niners_2026_pick_labels": niners_picks,
        "future_placeholder_pick_rows": future_placeholder_count,
        "review_warning_count": len(snapshot.review_warnings),
        "nwr_quality_value_policy": (
            "snapshot PDF ranks are preserved as review rank context only; "
            "stats_model_value is not populated from PDF rank"
        ),
    }


def _declared_drop_available_rows(rows: tuple[dict[str, str], ...]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        player = str(row.get("player_name") or "").strip()
        sequence = _safe_int(row.get("declared_drop_sequence"), default=len(out) + 1)
        duplicate_instance = _safe_int(row.get("duplicate_instance"), default=1)
        normalized = row.get("normalized_player_key") or _normalize_player_key(player)
        out.append(
            _available_row(
                asset_id=(
                    f"declared_drop:{normalized}:seq{sequence}:instance{duplicate_instance}"
                ),
                player=player,
                position=row.get("matched_position") or "",
                nfl_team=row.get("matched_nfl_team") or "",
                asset_type="Declared Drop",
                asset_lifecycle="declared_top_five_drop",
                why_available=(
                    "Manual top-five declared drop from roster snapshot; "
                    "duplicate declarations are preserved for review."
                ),
                source_overall_rank=row.get("matched_overall_rank") or "",
                draft_rank=_safe_int(row.get("matched_overall_rank"), default=999),
                warning=_declared_drop_warning(row),
                source_status=row.get("input_status") or "",
                source_team=row.get("matched_roster_team") or "",
                source_manager=row.get("matched_roster_manager") or "",
            )
        )
    return out


def _free_agent_available_rows(rows: tuple[dict[str, str], ...]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        player = str(row.get("player_name") or "").strip()
        normalized = _normalize_player_key(player)
        out.append(
            _available_row(
                asset_id=f"free_agent:{normalized}:row{index}",
                player=player,
                position=row.get("position") or "",
                nfl_team=row.get("nfl_team") or "",
                asset_type="Free Agent",
                asset_lifecycle="free_agent_snapshot",
                why_available="Free-agent row extracted from the roster PDF snapshot.",
                source_overall_rank=row.get("overall_rank") or "",
                draft_rank=_safe_int(row.get("overall_rank"), default=999),
                warning="Review-only PDF extraction; verify before draft-day use.",
                source_status=row.get("input_status") or "",
                source_team="",
                source_manager="",
            )
        )
    return out


def _available_row(
    *,
    asset_id: str,
    player: str,
    position: str,
    nfl_team: str,
    asset_type: str,
    asset_lifecycle: str,
    why_available: str,
    source_overall_rank: str,
    draft_rank: int,
    warning: str,
    source_status: str,
    source_team: str,
    source_manager: str,
) -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "player": player,
        "position": position,
        "nfl_team": nfl_team,
        "asset_type": asset_type,
        "asset_lifecycle": asset_lifecycle,
        "why_available": why_available,
        "stats_model_value": 0.0,
        "market_value": 0.0,
        "market_edge": 0.0,
        "confidence": 25.0,
        "warning": warning,
        "draft_rank": draft_rank,
        "source_overall_rank": source_overall_rank,
        "source_team": source_team,
        "source_manager": source_manager,
        "source_status": source_status,
        "nwr_score_status": "not_populated_from_snapshot_rank",
        "allowed_use": "mock_draft_review_availability_only",
        "blocked_use": "nwr_private_quality_value_or_production_rankings",
    }


def _snapshot_warnings(
    *,
    manifest: dict[str, object],
    roster_rows: tuple[dict[str, str], ...],
    pick_rows: tuple[dict[str, str], ...],
    free_agent_rows: tuple[dict[str, str], ...],
    declared_drop_rows: tuple[dict[str, str], ...],
) -> list[str]:
    warnings: list[str] = []
    if manifest.get("review_only") is not True:
        warnings.append("Snapshot manifest is not marked review_only=true.")
    expected_counts = {
        "roster_rows": len(roster_rows),
        "draft_pick_rows": len(pick_rows),
        "free_agent_rows": len(free_agent_rows),
        "declared_drop_rows": len(declared_drop_rows),
    }
    for key, actual in expected_counts.items():
        if _safe_int(manifest.get(key), default=actual) != actual:
            warnings.append(f"Manifest count mismatch for {key}.")
    duplicate_counts = Counter(
        row.get("normalized_player_key", "") for row in declared_drop_rows
    )
    for player_key, count in sorted(duplicate_counts.items()):
        if player_key and count > 1:
            warnings.append(
                f"Duplicate declared drop preserved for review: {player_key} x{count}."
            )
    future_placeholders = [
        row
        for row in pick_rows
        if str(row.get("season") or "") != "2026"
        and str(row.get("pick_label") or "").endswith(".00")
    ]
    if future_placeholders:
        warnings.append(
            f"{len(future_placeholders)} future placeholder pick rows require review."
        )
    declared_without_match = [
        row for row in declared_drop_rows if not str(row.get("matched_roster_team") or "")
    ]
    if declared_without_match:
        warnings.append(
            f"{len(declared_without_match)} declared drops did not match roster rows."
        )
    return warnings


def _declared_drop_warning(row: dict[str, str]) -> str:
    duplicate_count = _safe_int(row.get("duplicate_declared_count"), default=1)
    if duplicate_count > 1:
        return "Duplicate declared drop input preserved; Tim must resolve before final use."
    return "Manual declared drop; review-only until final declaration confirmation."


def _parse_pick_label(value: str, *, teams: int) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(\d+)\.(\d+)", str(value or "").strip())
    if not match:
        return None
    round_number = int(match.group(1))
    round_pick = int(match.group(2))
    if round_pick <= 0:
        return None
    return round_number, round_pick, ((round_number - 1) * teams) + round_pick


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def _safe_int(value: object, *, default: int) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _normalize_player_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
