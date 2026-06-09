from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_player_board_value_service import (
    FULL_BOARD_SCORE_COLUMN,
    FullPlayerBoardValueResult,
    build_full_player_board_value_rows,
)

DEFAULT_REPAIR_QUEUE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/full_board_missing_score_repair_queue.csv"
)

REPAIR_QUEUE_HEADER = (
    "player",
    "position",
    "team",
    "age",
    "league_rank",
    "market_rank",
    "roster_status",
    "is_my_team",
    "is_available",
    "is_rookie",
    "legacy_active_pack_score",
    "missing_score_reason_bucket",
    "raw_warning_flags",
    "human_readable_data_needed",
    "repair_priority",
    "repair_action",
    "can_score_now_from_existing_private_sources",
    "blocked_reason_if_not",
    "candidate_source_files_needed",
    "identity_join_status",
    "source_disclosure_status",
)


@dataclass(frozen=True)
class MissingScoreRepairQueueResult:
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class MissingScoreRepairQueuePaths:
    rows: Path


def build_missing_score_repair_queue(
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
    *,
    full_board_result: FullPlayerBoardValueResult | None = None,
) -> MissingScoreRepairQueueResult:
    result = full_board_result or build_full_player_board_value_rows(data_pack_path)
    rows = tuple(
        sorted(
            (
                _repair_row(row)
                for row in result.rows
                if not str(row.get(FULL_BOARD_SCORE_COLUMN) or "").strip()
            ),
            key=lambda row: (
                _priority_sort(row["repair_priority"]),
                _rank_sort(row["league_rank"]),
                _rank_sort(row["market_rank"]),
                str(row["player"]).lower(),
            ),
        )
    )
    summary = {
        "repair_queue_rows": len(rows),
        "my_team_unscored_rows": sum(row["is_my_team"] == "1" for row in rows),
        "available_unscored_rows": sum(row["is_available"] == "1" for row in rows),
        "rookie_unscored_rows": sum(row["is_rookie"] == "1" for row in rows),
        "kicker_unscored_rows": sum(row["position"] == "K" for row in rows),
        "can_score_now_from_existing_private_sources": sum(
            row["can_score_now_from_existing_private_sources"] == "1" for row in rows
        ),
    }
    return MissingScoreRepairQueueResult(rows=rows, summary=summary)


def write_missing_score_repair_queue(
    *,
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
    output_path: str | Path = DEFAULT_REPAIR_QUEUE_ROWS,
    result: MissingScoreRepairQueueResult | None = None,
) -> MissingScoreRepairQueuePaths:
    result = result or build_missing_score_repair_queue(data_pack_path)
    output = Path(output_path)
    _write_csv(output, REPAIR_QUEUE_HEADER, result.rows)
    return MissingScoreRepairQueuePaths(rows=output)


def _repair_row(row: dict[str, object]) -> dict[str, object]:
    position = str(row.get("position") or "")
    warning_flags = str(row.get("warning_flags") or "")
    data_needed = str(row.get("data_needed") or "")
    return {
        "player": row.get("player_name", ""),
        "position": position,
        "team": row.get("nfl_team", ""),
        "age": row.get("age", ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "roster_status": row.get("pool_status") or row.get("roster_status", ""),
        "is_my_team": row.get("is_my_team", ""),
        "is_available": row.get("is_available", ""),
        "is_rookie": row.get("is_rookie", ""),
        "legacy_active_pack_score": row.get("legacy_active_pack_score", ""),
        "missing_score_reason_bucket": _reason_bucket(position, warning_flags),
        "raw_warning_flags": warning_flags,
        "human_readable_data_needed": data_needed,
        "repair_priority": _repair_priority(row),
        "repair_action": _repair_action(position, warning_flags),
        "can_score_now_from_existing_private_sources": "0",
        "blocked_reason_if_not": _blocked_reason(position, warning_flags),
        "candidate_source_files_needed": _candidate_sources(position, warning_flags),
        "identity_join_status": _identity_join_status(warning_flags),
        "source_disclosure_status": _source_disclosure_status(row),
    }


def _repair_priority(row: dict[str, object]) -> str:
    if str(row.get("position") or "") == "K":
        return "P5_kicker_low_priority"
    if row.get("is_my_team") == "1":
        return "P0_my_team"
    league_rank = _float(row.get("league_rank"))
    market_rank = _float(row.get("market_rank"))
    if league_rank is not None and league_rank <= 75:
        return "P1_high_league_rank"
    if market_rank is not None and market_rank <= 75:
        return "P2_high_market_rank"
    if row.get("is_rookie") == "1":
        return "P2_rookie_or_prospect"
    if row.get("is_available") == "1":
        return "P3_available_player"
    if str(row.get("position") or "") in {"RB", "WR", "TE"}:
        return "P3_flex_depth"
    return "P4_depth_or_low_context"


def _reason_bucket(position: str, warning_flags: str) -> str:
    if position == "K":
        return "kicker_excluded_from_default_private_rankings"
    if "missing_model_v4_current_player_row" in warning_flags:
        return "missing_model_v4_current_player_row"
    if "unmatched_identity_join_key" in warning_flags:
        return "identity_join_missing"
    if "missing_score_disclosure_fields" in warning_flags:
        return "missing_score_disclosure"
    return "private_score_missing"


def _repair_action(position: str, warning_flags: str) -> str:
    if position == "K":
        return "Keep hidden by default; add K-specific admitted scoring only if product needs it."
    if "unmatched_identity_join_key" in warning_flags:
        return "Repair deterministic identity mapping, then rerun full-board current-value export."
    if "missing_model_v4_current_player_row" in warning_flags:
        return "Add player to admitted private evidence matrix, then rerun current-value export."
    return "Inspect source disclosure and admitted private component coverage."


def _blocked_reason(position: str, warning_flags: str) -> str:
    if position == "K":
        return "Kickers are intentionally outside default QB/RB/WR/TE dynasty scoring."
    if "missing_model_v4_current_player_row" in warning_flags:
        return "No admitted current Model v4 private score row is available."
    return "Private score is missing or blocked by source disclosure."


def _candidate_sources(position: str, warning_flags: str) -> str:
    if position == "K":
        return "K-specific scoring contract and admitted kicker source files, if ever needed."
    sources = [
        "active_board_qb_rb_wr_te_truth_set.csv",
        "nfl_player_current_evidence_matrix.csv",
        "player_vorp_review_rows.csv",
        "current_player_value_full_board_review_rows.csv",
    ]
    if "missing_rotowire_player_stats" in warning_flags:
        sources.append("rotowire_player_stats_clean_rows.csv")
    if "missing_stats_first_component_evidence" in warning_flags:
        sources.append("stats_first_component_evidence_rows.csv")
    return " | ".join(dict.fromkeys(sources))


def _identity_join_status(warning_flags: str) -> str:
    if "duplicate_identity_join_key" in warning_flags:
        return "duplicate_identity_review"
    if "unmatched_identity_join_key" in warning_flags:
        return "missing_identity_join"
    return "joined_or_not_applicable"


def _source_disclosure_status(row: dict[str, object]) -> str:
    required = ("source_path", "source_column", "model_version", "lineage_class")
    missing = [field for field in required if not str(row.get(field) or "").strip()]
    return "complete" if not missing else f"missing:{'|'.join(missing)}"


def _priority_sort(value: object) -> int:
    text = str(value or "")
    if text.startswith("P0"):
        return 0
    if text.startswith("P1"):
        return 1
    if text.startswith("P2"):
        return 2
    if text.startswith("P3"):
        return 3
    if text.startswith("P4"):
        return 4
    return 5


def _rank_sort(value: object) -> float:
    parsed = _float(value)
    return parsed if parsed is not None else 999999.0


def _float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
