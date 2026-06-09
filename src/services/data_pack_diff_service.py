from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack


@dataclass(frozen=True)
class DataPackDiffReport:
    baseline_path: Path
    candidate_path: Path
    baseline_snapshot: str | None
    candidate_snapshot: str | None
    roster_added: tuple[dict[str, object], ...]
    roster_removed: tuple[dict[str, object], ...]
    roster_moved: tuple[dict[str, object], ...]
    league_rank_changed: tuple[dict[str, object], ...]
    pick_owner_changed: tuple[dict[str, object], ...]


def build_data_pack_diff_report(
    *,
    baseline_data_pack: str | Path,
    candidate_data_pack: str | Path,
) -> DataPackDiffReport:
    baseline = validate_data_pack(baseline_data_pack)
    candidate = validate_data_pack(candidate_data_pack)
    baseline_rosters = _rosters_by_player(baseline.rows_by_table.get("rosters", []))
    candidate_rosters = _rosters_by_player(candidate.rows_by_table.get("rosters", []))
    baseline_rankings = _rankings_by_player(baseline.rows_by_table.get("official_rankings", []))
    candidate_rankings = _rankings_by_player(candidate.rows_by_table.get("official_rankings", []))
    baseline_picks = _picks_by_key(baseline.rows_by_table.get("future_picks", []))
    candidate_picks = _picks_by_key(candidate.rows_by_table.get("future_picks", []))

    return DataPackDiffReport(
        baseline_path=Path(baseline_data_pack).resolve(),
        candidate_path=Path(candidate_data_pack).resolve(),
        baseline_snapshot=baseline.snapshot_date,
        candidate_snapshot=candidate.snapshot_date,
        roster_added=tuple(_roster_added(baseline_rosters, candidate_rosters)),
        roster_removed=tuple(_roster_removed(baseline_rosters, candidate_rosters)),
        roster_moved=tuple(_roster_moved(baseline_rosters, candidate_rosters)),
        league_rank_changed=tuple(
            _rank_changed(
                baseline_rosters,
                candidate_rosters,
                baseline_rankings,
                candidate_rankings,
            )
        ),
        pick_owner_changed=tuple(_pick_owner_changed(baseline_picks, candidate_picks)),
    )


def diff_summary_rows(report: DataPackDiffReport) -> list[dict[str, object]]:
    return [
        {"change_type": "roster_added", "count": len(report.roster_added)},
        {"change_type": "roster_removed", "count": len(report.roster_removed)},
        {"change_type": "roster_moved", "count": len(report.roster_moved)},
        {"change_type": "league_rank_changed", "count": len(report.league_rank_changed)},
        {"change_type": "pick_owner_changed", "count": len(report.pick_owner_changed)},
    ]


def diff_detail_rows(report: DataPackDiffReport) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(report.roster_added)
    rows.extend(report.roster_removed)
    rows.extend(report.roster_moved)
    rows.extend(report.league_rank_changed)
    rows.extend(report.pick_owner_changed)
    return sorted(
        rows,
        key=lambda row: (str(row["change_type"]), str(row.get("player") or row.get("pick"))),
    )


def _rosters_by_player(
    rows: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _rankings_by_player(
    rows: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _picks_by_key(
    rows: list[dict[str, object]],
) -> dict[tuple[str, str, str], dict[str, object]]:
    return {
        (
            str(row.get("pick_year") or ""),
            str(row.get("round") or ""),
            str(row.get("slot") or row.get("pick_label") or ""),
        ): row
        for row in rows
        if row.get("pick_year") and row.get("round")
    }


def _roster_added(
    baseline: dict[str, dict[str, object]],
    candidate: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "change_type": "roster_added",
            "player": row.get("player_name"),
            "position": row.get("position"),
            "from_team": "",
            "to_team": row.get("team_name"),
            "baseline_value": "",
            "candidate_value": _league_rank(row),
        }
        for player_id, row in candidate.items()
        if player_id not in baseline
    ]


def _roster_removed(
    baseline: dict[str, dict[str, object]],
    candidate: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "change_type": "roster_removed",
            "player": row.get("player_name"),
            "position": row.get("position"),
            "from_team": row.get("team_name"),
            "to_team": "",
            "baseline_value": _league_rank(row),
            "candidate_value": "",
        }
        for player_id, row in baseline.items()
        if player_id not in candidate
    ]


def _roster_moved(
    baseline: dict[str, dict[str, object]],
    candidate: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    rows = []
    for player_id, baseline_row in baseline.items():
        candidate_row = candidate.get(player_id)
        if candidate_row is None:
            continue
        if baseline_row.get("team_id") == candidate_row.get("team_id"):
            continue
        rows.append(
            {
                "change_type": "roster_moved",
                "player": candidate_row.get("player_name") or baseline_row.get("player_name"),
                "position": candidate_row.get("position") or baseline_row.get("position"),
                "from_team": baseline_row.get("team_name"),
                "to_team": candidate_row.get("team_name"),
                "baseline_value": _league_rank(baseline_row),
                "candidate_value": _league_rank(candidate_row),
            }
        )
    return rows


def _rank_changed(
    baseline_rosters: dict[str, dict[str, object]],
    candidate_rosters: dict[str, dict[str, object]],
    baseline_rankings: dict[str, dict[str, object]],
    candidate_rankings: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    rows = []
    for player_id, candidate_row in candidate_rosters.items():
        baseline_row = baseline_rosters.get(player_id)
        if baseline_row is None:
            continue
        baseline_rank = _league_rank(baseline_row, baseline_rankings.get(player_id))
        candidate_rank = _league_rank(candidate_row, candidate_rankings.get(player_id))
        if baseline_rank == candidate_rank:
            continue
        rows.append(
            {
                "change_type": "league_rank_changed",
                "player": candidate_row.get("player_name") or baseline_row.get("player_name"),
                "position": candidate_row.get("position") or baseline_row.get("position"),
                "from_team": baseline_row.get("team_name"),
                "to_team": candidate_row.get("team_name"),
                "baseline_value": baseline_rank,
                "candidate_value": candidate_rank,
            }
        )
    return rows


def _pick_owner_changed(
    baseline: dict[tuple[str, str, str], dict[str, object]],
    candidate: dict[tuple[str, str, str], dict[str, object]],
) -> list[dict[str, object]]:
    rows = []
    for key, candidate_row in candidate.items():
        baseline_row = baseline.get(key)
        if baseline_row is None:
            continue
        if baseline_row.get("current_team_id") == candidate_row.get("current_team_id"):
            continue
        rows.append(
            {
                "change_type": "pick_owner_changed",
                "pick": candidate_row.get("pick_label") or baseline_row.get("pick_label"),
                "position": "",
                "from_team": baseline_row.get("current_team_name"),
                "to_team": candidate_row.get("current_team_name"),
                "baseline_value": baseline_row.get("current_team_id"),
                "candidate_value": candidate_row.get("current_team_id"),
            }
        )
    return rows


def _league_rank(
    primary_row: dict[str, object],
    fallback_row: dict[str, object] | None = None,
) -> object:
    fallback = fallback_row or {}
    for row in (primary_row, fallback):
        for key in ("league_rank", "official_rank"):
            value = row.get(key)
            if value is not None and value != "":
                return value
    return ""
