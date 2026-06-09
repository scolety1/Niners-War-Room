from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_current_value_export_service import (
    DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS,
)
from src.services.market_gap_service import build_market_gap_report
from src.services.model_v4_identity_join_gate_service import normalize_identity_name
from src.services.rotowire_local_team_status_service import (
    rotowire_team_status_lookup,
    select_rotowire_team_status_row,
)

FULL_PLAYER_BOARD_VERSION = "model_v4_full_player_board_value_0.1.0"
DEFAULT_CURRENT_VALUE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_FULL_PLAYER_BOARD_ROWS = DEFAULT_OUTPUT_ROOT / "full_player_board_value_review_rows.csv"
DEFAULT_ROOKIE_BOARD_ROWS = Path(
    "local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
)

SCORED_LINEAGE = "review_v4_current_player"
UNKNOWN_LINEAGE = "unknown"
FULL_BOARD_SCORE_COLUMN = "nwr_dynasty_score"
CURRENT_CHECKPOINT_SCORE_COLUMN = "checkpoint_review_score"

FULL_PLAYER_BOARD_HEADER = (
    "player_id",
    "canonical_player_key",
    "player_name",
    "normalized_player_name",
    "position",
    "age",
    "nfl_team",
    "nwr_rank",
    "nwr_dynasty_score",
    "score_status",
    "trust_status",
    "pool_status",
    "is_my_team",
    "is_available",
    "is_rookie",
    "roster_team_id",
    "roster_team_name",
    "roster_status",
    "league_rank",
    "league_rank_source",
    "market_rank",
    "market_rank_source",
    "legacy_active_pack_score",
    "legacy_active_pack_score_allowed_use",
    "risk_level",
    "risk_level_source",
    "source_path",
    "source_column",
    "upstream_source_path",
    "upstream_source_column",
    "model_version",
    "lineage_class",
    "score_type",
    "score_as_of_date",
    "confidence_cap",
    "confidence_status",
    "allowed_use",
    "blocked_use",
    "raw_model_warning_flags",
    "team_resolution_status",
    "canonical_team_source",
    "warning_flags",
    "data_needed",
    "raw_source_repair_notes",
    "full_board_version",
)

WARNING_TO_DATA_NEEDED = {
    "missing_model_v4_current_player_row": (
        "Need a current Model v4 private score row for this player."
    ),
    "unmatched_identity_join_key": "Need clean identity join key / canonical player mapping.",
    "duplicate_identity_join_key": "Need duplicate identity join repair.",
    "missing_score_disclosure_fields": (
        "Need source_path, source_column, model_version, lineage_class, and allowed/blocked "
        "use disclosure."
    ),
    "missing_or_review_route_target_snap_evidence": (
        "Need route/target/snap or role-usage evidence."
    ),
    "missing_lifecycle_or_role_shape_evidence": "Need lifecycle/role-shape evidence.",
    "missing_role_evidence_gate": "Need role/volume evidence before full trust.",
    "missing_role_evidence": "Need role/volume evidence before full trust.",
    "licensed_route_metrics_not_available": (
        "Licensed route metrics unavailable; use as source limitation, not a formula instruction."
    ),
    "partial_first_down_confidence_cap": (
        "Need stronger first-down evidence or accept confidence cap."
    ),
    "team_mismatch_or_missing_model_team": (
        "Need current team verification / team mapping repair."
    ),
    "stale_team_or_status_evidence": "Need current team/status refresh.",
    "partial_or_quarantined_join_evidence": (
        "Need identity/source join repair before full trust."
    ),
    "partial_or_quarantined_join_cap": "Need identity/source join repair before full trust.",
    "missing_vorp_anchor": "Need VORP anchor / replacement baseline evidence.",
    "missing_stats_first_component_evidence": "Need stats-first component evidence.",
    "missing_rotowire_player_stats": "Need player stats source coverage.",
    "missing_prospect_or_college_evidence": (
        "Need prospect/college evidence for rookie/prospect row."
    ),
    "pick_baseline_missing_review": "Need admitted pick baseline before scoring/comparison.",
    "blank_current_player_checkpoint_score": (
        "Need repaired current-player checkpoint score from admitted private inputs."
    ),
    "no_active_free_agent_source_loaded": (
        "Need available/free-agent source before this row can be marked available."
    ),
    "no_active_rookie_flag_source_loaded": (
        "Need rookie/prospect source match before this row can be marked rookie."
    ),
    "historical_team_context_warning": (
        "Historical source team differs from the verified current-team source."
    ),
    "rotowire_current_team_status_warning": (
        "Current team/status was repaired from local RotoWire source context."
    ),
    "rotowire_current_status_no_team": (
        "Local RotoWire source verifies no current NFL team; do not invent a team."
    ),
}


@dataclass(frozen=True)
class FullPlayerBoardValueResult:
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class FullPlayerBoardValuePaths:
    review_rows: Path


def build_full_player_board_value_rows(
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
    *,
    current_value_path: str | Path | None = None,
    rookie_board_path: str | Path = DEFAULT_ROOKIE_BOARD_ROWS,
    output_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
) -> FullPlayerBoardValueResult:
    pack = Path(data_pack_path)
    current_path = Path(current_value_path or _default_current_value_rows())
    output = Path(output_path)
    model_rows = _read_rows(pack / "model_outputs.csv")
    roster_by_player_id = _by_player_id(_read_rows(pack / "fact_rosters.csv"))
    official_by_player_id = _by_player_id(_read_rows(pack / "fact_official_rankings.csv"))
    dim_by_player_id = _by_player_id(_read_rows(pack / "dim_players.csv"))
    current_lookup = _current_lookup(_read_rows(current_path))
    rotowire_lookup = rotowire_team_status_lookup()
    rookie_lookup = _rookie_lookup(_read_rows(Path(rookie_board_path)))
    market_by_player_id = {
        str(row.get("player_id") or ""): row
        for row in build_market_gap_report(pack).rows
        if row.get("player_id")
    }

    rows = tuple(
        _full_board_row(
            output_path=output,
            active_row=row,
            roster_row=roster_by_player_id.get(str(row.get("player_id") or ""), {}),
            official_row=official_by_player_id.get(str(row.get("player_id") or ""), {}),
            dim_row=dim_by_player_id.get(str(row.get("player_id") or ""), {}),
            rotowire_row=select_rotowire_team_status_row(
                rotowire_lookup.get(
                    (
                        normalize_identity_name(row.get("player_name")),
                        str(row.get("position") or "").upper(),
                    ),
                    (),
                )
            ),
            current_lookup=current_lookup,
            rookie_lookup=rookie_lookup,
            market_row=market_by_player_id.get(str(row.get("player_id") or ""), {}),
            current_value_path=current_path,
        )
        for row in model_rows
    )
    ranked_rows = _assign_private_ranks(rows)
    summary = {
        "full_board_version": FULL_PLAYER_BOARD_VERSION,
        "active_board_rows": len(ranked_rows),
        "qb_rb_wr_te_rows": sum(row["position"] in {"QB", "RB", "WR", "TE"} for row in ranked_rows),
        "kicker_rows": sum(row["position"] == "K" for row in ranked_rows),
        "nwr_scored_rows": sum(_has_score(row.get("nwr_dynasty_score")) for row in ranked_rows),
        "no_private_score_rows": sum(
            row["trust_status"] in {"No Private Score", "Source Repair Needed"}
            for row in ranked_rows
        ),
        "source_repair_needed_rows": sum(
            row["trust_status"] == "Source Repair Needed" for row in ranked_rows
        ),
        "my_team_rows": sum(row["is_my_team"] == "1" for row in ranked_rows),
        "available_rows": sum(row["is_available"] == "1" for row in ranked_rows),
        "rookie_rows": sum(row["is_rookie"] == "1" for row in ranked_rows),
        "legacy_primary_scores_used": 0,
        "market_or_league_primary_scores_used": 0,
    }
    return FullPlayerBoardValueResult(rows=ranked_rows, summary=summary)


def write_full_player_board_value_rows(
    *,
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
    output_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    result: FullPlayerBoardValueResult | None = None,
) -> FullPlayerBoardValuePaths:
    output = Path(output_path)
    result = result or build_full_player_board_value_rows(
        data_pack_path,
        output_path=output,
    )
    _write_csv(output, FULL_PLAYER_BOARD_HEADER, result.rows)
    return FullPlayerBoardValuePaths(review_rows=output)


def _default_current_value_rows() -> Path:
    if DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.exists():
        return DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS
    return DEFAULT_CURRENT_VALUE_ROWS


def data_needed_messages(warning_flags: object) -> tuple[str, ...]:
    flags = _split_flags(warning_flags)
    messages = [
        WARNING_TO_DATA_NEEDED.get(flag, _humanize_warning(flag))
        for flag in flags
        if not flag.startswith("unmatched_identity_join_source:")
        and not flag.startswith("duplicate_identity_join_source:")
    ]
    return tuple(dict.fromkeys(message for message in messages if message))


def _full_board_row(
    *,
    output_path: Path,
    active_row: dict[str, str],
    roster_row: dict[str, str],
    official_row: dict[str, str],
    dim_row: dict[str, str],
    rotowire_row: dict[str, str],
    current_lookup: dict[tuple[str, str], list[dict[str, str]]],
    rookie_lookup: dict[tuple[str, str], dict[str, str]],
    market_row: dict[str, Any],
    current_value_path: Path,
) -> dict[str, object]:
    player = str(active_row.get("player_name") or "")
    position = str(active_row.get("position") or "").upper()
    normalized = normalize_identity_name(player)
    join_key = (normalized, position)
    current_matches = current_lookup.get(join_key, [])
    current = current_matches[0] if len(current_matches) == 1 else {}
    score = str(current.get(CURRENT_CHECKPOINT_SCORE_COLUMN) or "").strip()
    scored = _has_score(score)
    raw_warnings = _row_warnings(
        current=current,
        current_matches=current_matches,
        scored=scored,
        position=position,
    )
    team_resolution = _team_resolution(
        current=current,
        roster_row=roster_row,
        official_row=official_row,
        dim_row=dim_row,
        rotowire_row=rotowire_row,
    )
    warnings = _user_facing_warnings(
        raw_warnings,
        team_resolution["status"],
        team_resolution["source"],
    )
    confidence_cap = str(current.get("confidence_cap") or "").strip()
    pool_status, is_my_team, is_available = _pool_status(roster_row)
    rookie = _rookie_status(join_key, dim_row, rookie_lookup)
    trust_status = _trust_status(
        scored=scored,
        confidence_cap=confidence_cap,
        warnings=warnings,
    )
    return {
        "player_id": active_row.get("player_id", ""),
        "canonical_player_key": current.get("canonical_player_key")
        or f"nfl:{normalized}:{position}",
        "player_name": player,
        "normalized_player_name": normalized,
        "position": position,
        "age": "",
        "nfl_team": (
            rotowire_row.get("nfl_team")
            or current.get("nfl_team")
            or official_row.get("nfl_team")
            or dim_row.get("nfl_team")
            or roster_row.get("nfl_team")
            or active_row.get("nfl_team", "")
        ),
        "nwr_rank": "",
        "nwr_dynasty_score": score if scored else "",
        "score_status": "scored" if scored else "not_scored",
        "trust_status": trust_status,
        "pool_status": pool_status,
        "is_my_team": "1" if is_my_team else "0",
        "is_available": "1" if is_available else "0",
        "is_rookie": "1" if rookie else "0",
        "roster_team_id": roster_row.get("team_id", ""),
        "roster_team_name": roster_row.get("team_name", ""),
        "roster_status": roster_row.get("roster_status", ""),
        "league_rank": official_row.get("league_rank") or roster_row.get("league_rank", ""),
        "league_rank_source": official_row.get("rank_source_name", ""),
        "market_rank": market_row.get("dynasty_startup_adp", ""),
        "market_rank_source": "market_gap_report.dynasty_startup_adp",
        "legacy_active_pack_score": active_row.get("private_score", ""),
        "legacy_active_pack_score_allowed_use": "comparison_only_not_primary_value",
        "risk_level": active_row.get("risk_level", ""),
        "risk_level_source": (
            "legacy_active_pack_display_only" if active_row.get("risk_level") else ""
        ),
        "source_path": str(output_path),
        "source_column": FULL_BOARD_SCORE_COLUMN,
        "upstream_source_path": str(current_value_path) if scored else "",
        "upstream_source_column": CURRENT_CHECKPOINT_SCORE_COLUMN if scored else "",
        "model_version": current.get("checkpoint_version") or FULL_PLAYER_BOARD_VERSION,
        "lineage_class": SCORED_LINEAGE if scored else UNKNOWN_LINEAGE,
        "score_type": FULL_BOARD_SCORE_COLUMN,
        "score_as_of_date": active_row.get("snapshot_date", ""),
        "confidence_cap": confidence_cap,
        "confidence_status": current.get("confidence_status", ""),
        "allowed_use": "review_only_full_player_board_rankings",
        "blocked_use": (
            "do_not_use_as_final_trade_cut_keep_draft_buy_sell_defer_target_or_start_sit_"
            "recommendation"
        ),
        "raw_model_warning_flags": "|".join(raw_warnings),
        "team_resolution_status": team_resolution["status"],
        "canonical_team_source": team_resolution["source"],
        "warning_flags": "|".join(warnings),
        "data_needed": " | ".join(data_needed_messages("|".join(warnings))),
        "raw_source_repair_notes": _raw_source_repair_notes(warnings),
        "full_board_version": FULL_PLAYER_BOARD_VERSION,
    }


def _row_warnings(
    *,
    current: dict[str, str],
    current_matches: list[dict[str, str]],
    scored: bool,
    position: str,
) -> tuple[str, ...]:
    warnings = list(_split_flags(current.get("warning_flags")))
    if len(current_matches) > 1:
        warnings.extend(("duplicate_identity_join_key",))
    if not current_matches:
        warnings.extend(
            (
                "missing_model_v4_current_player_row",
                "unmatched_identity_join_key",
                "missing_rotowire_player_stats",
                "missing_stats_first_component_evidence",
                "missing_vorp_anchor",
                "missing_lifecycle_or_role_shape_evidence",
            )
        )
        if position in {"RB", "WR", "TE"}:
            warnings.append("missing_or_review_route_target_snap_evidence")
    elif not scored:
        warnings.append("blank_current_player_checkpoint_score")
    return tuple(dict.fromkeys(flag for flag in warnings if flag))


def _team_resolution(
    *,
    current: dict[str, str],
    roster_row: dict[str, str],
    official_row: dict[str, str],
    dim_row: dict[str, str],
    rotowire_row: dict[str, str],
) -> dict[str, str]:
    sources = {
        "rotowire_nfl_team_status.nfl_team": str(rotowire_row.get("nfl_team") or "").strip(),
        "fact_rosters.nfl_team": str(roster_row.get("nfl_team") or "").strip(),
        "fact_official_rankings.nfl_team": str(official_row.get("nfl_team") or "").strip(),
        "dim_players.nfl_team": str(dim_row.get("nfl_team") or "").strip(),
        "current_player_value_full_board.nfl_team": str(current.get("nfl_team") or "").strip(),
    }
    nonblank = {source: _team_alias(team) for source, team in sources.items() if team}
    unique_teams = set(nonblank.values())
    chosen_source, _chosen_team = _canonical_team_source(sources)
    if (
        not nonblank
        and rotowire_row.get("status") == "free_agent_or_no_team"
        and rotowire_row.get("source_file")
    ):
        return {
            "status": "current_status_verified_no_team",
            "source": "rotowire_nfl_team_status.status",
        }
    if not nonblank:
        return {
            "status": "unresolved_missing_current_team_source",
            "source": "",
        }
    if len(unique_teams) > 1:
        return {
            "status": "unresolved_current_source_conflict",
            "source": chosen_source,
        }
    return {
        "status": "resolved_current_team_verified",
        "source": chosen_source,
    }


def _canonical_team_source(sources: dict[str, str]) -> tuple[str, str]:
    for source in (
        "rotowire_nfl_team_status.nfl_team",
        "fact_rosters.nfl_team",
        "fact_official_rankings.nfl_team",
        "dim_players.nfl_team",
        "current_player_value_full_board.nfl_team",
    ):
        team = str(sources.get(source) or "").strip()
        if team:
            return source, _team_alias(team)
    return "", ""


def _user_facing_warnings(
    raw_warnings: tuple[str, ...],
    team_resolution_status: str,
    team_resolution_source: str = "",
) -> tuple[str, ...]:
    if team_resolution_status not in {
        "resolved_current_team_verified",
        "current_status_verified_no_team",
    }:
        return raw_warnings
    downgraded: list[str] = []
    suppressed = {
        "team_mismatch_or_missing_model_team",
        "team_mismatch_or_historical_team",
        "identity_review_cap",
        "partial_or_quarantined_join_cap",
    }
    saw_team_context = False
    for warning in raw_warnings:
        if warning in suppressed:
            saw_team_context = True
            continue
        downgraded.append(warning)
    if saw_team_context:
        if team_resolution_status == "current_status_verified_no_team":
            downgraded.append("rotowire_current_status_no_team")
        elif team_resolution_source.startswith("rotowire"):
            downgraded.append("rotowire_current_team_status_warning")
        else:
            downgraded.append("historical_team_context_warning")
    return tuple(dict.fromkeys(downgraded))


def _trust_status(
    *,
    scored: bool,
    confidence_cap: str,
    warnings: tuple[str, ...],
) -> str:
    severe = {
        "missing_model_v4_current_player_row",
        "unmatched_identity_join_key",
        "duplicate_identity_join_key",
        "missing_score_disclosure_fields",
        "blank_current_player_checkpoint_score",
    }
    if not scored and any(flag in severe for flag in warnings):
        return "Source Repair Needed"
    if not scored:
        return "No Private Score"
    cap = _float(confidence_cap)
    if cap is not None and cap < 1.0:
        return "Capped Score"
    if warnings:
        return "Scored + Warnings"
    return "Scored"


def _pool_status(roster_row: dict[str, str]) -> tuple[str, bool, bool]:
    team = str(roster_row.get("team_name") or "").strip()
    roster_status = str(roster_row.get("roster_status") or "").strip().lower()
    if team.lower() == "niners":
        return "MY TEAM", True, False
    if roster_status == "rostered" and team:
        return "OTHER TEAM", False, False
    if not team:
        return "UNKNOWN POOL", False, False
    return "AVAILABLE", False, True


def _rookie_status(
    join_key: tuple[str, str],
    dim_row: dict[str, str],
    rookie_lookup: dict[tuple[str, str], dict[str, str]],
) -> bool:
    if join_key in rookie_lookup:
        return True
    rookie_year = str(dim_row.get("rookie_year") or "").strip()
    return rookie_year in {"2025", "2026"}


def _assign_private_ranks(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    ranked = [dict(row) for row in rows]
    scored = sorted(
        (row for row in ranked if _has_score(row.get("nwr_dynasty_score"))),
        key=lambda row: (
            -(_float(row.get("nwr_dynasty_score")) or -1.0),
            str(row.get("player_name") or "").lower(),
        ),
    )
    for rank, row in enumerate(scored, start=1):
        row["nwr_rank"] = str(rank)
    rank_by_key = {row["canonical_player_key"]: row["nwr_rank"] for row in scored}
    for row in ranked:
        row["nwr_rank"] = rank_by_key.get(row["canonical_player_key"], "")
    return tuple(
        sorted(
            ranked,
            key=lambda row: (
                0 if _has_score(row.get("nwr_dynasty_score")) else 1,
                _rank_sort(row.get("nwr_rank")),
                _rank_sort(row.get("league_rank")),
                _rank_sort(row.get("market_rank")),
                str(row.get("player_name") or "").lower(),
            ),
        )
    )


def _raw_source_repair_notes(warnings: tuple[str, ...]) -> str:
    if "missing_model_v4_current_player_row" in warnings:
        return (
            "Player is present in active board but absent from the admitted NFL evidence "
            "matrix/current-value checkpoint source."
        )
    if "blank_current_player_checkpoint_score" in warnings:
        return "Current checkpoint row exists but blank score remains fail-closed."
    return ""


def _current_lookup(
    rows: tuple[dict[str, str], ...],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    lookup: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (
            normalize_identity_name(row.get("player_name") or row.get("normalized_player_name")),
            str(row.get("position") or "").upper(),
        )
        if key == ("", ""):
            continue
        lookup.setdefault(key, []).append(row)
    return lookup


def _rookie_lookup(rows: tuple[dict[str, str], ...]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (
            normalize_identity_name(row.get("prospect_name") or row.get("normalized_player_name")),
            str(row.get("position") or "").upper(),
        ): row
        for row in rows
        if row.get("prospect_name") or row.get("normalized_player_name")
    }


def _by_player_id(rows: tuple[dict[str, str], ...]) -> dict[str, dict[str, str]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _split_flags(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(flag.strip() for flag in str(value).split("|") if flag.strip())


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _has_score(value: object) -> bool:
    return _float(value) is not None


def _float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rank_sort(value: object) -> float:
    parsed = _float(value)
    return parsed if parsed is not None else 999999.0


def _team_alias(value: object) -> str:
    team = str(value or "").strip().upper()
    return {"LA": "LAR"}.get(team, team)


def _humanize_warning(flag: str) -> str:
    return flag.replace("_", " ").replace("/", " / ")
