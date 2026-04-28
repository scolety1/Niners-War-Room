from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack


@dataclass(frozen=True)
class DraftRoomBoard:
    snapshot_date: str | None
    pick_rows: list[dict[str, object]]
    team_rows: list[dict[str, object]]
    teams: list[str]
    certainties: list[str]


def build_draft_room(data_pack_path: str | Path) -> DraftRoomBoard:
    validated = validate_data_pack(data_pack_path)
    pick_values = _pick_values_by_key(validated.rows_by_table.get("pick_values", []))
    pick_rows = sorted(
        [
            _draft_pick_row(row, pick_values)
            for row in validated.rows_by_table.get("future_picks", [])
        ],
        key=lambda row: (
            str(row["current_team"]),
            int(row["pick_year"]),
            int(row["overall_pick"] or 999),
        ),
    )
    return DraftRoomBoard(
        snapshot_date=validated.snapshot_date,
        pick_rows=pick_rows,
        team_rows=_team_rows(pick_rows),
        teams=sorted({str(row["current_team"]) for row in pick_rows if row["current_team"]}),
        certainties=sorted({str(row["certainty"]) for row in pick_rows if row["certainty"]}),
    )


def _pick_values_by_key(
    rows: list[dict[str, object]],
) -> dict[tuple[int, str], dict[str, object]]:
    return {
        (int(row["pick_year"]), str(row["pick_label"])): row
        for row in rows
        if row.get("pick_year") is not None and row.get("pick_label")
    }


def _draft_pick_row(
    row: dict[str, object],
    pick_values: dict[tuple[int, str], dict[str, object]],
) -> dict[str, object]:
    pick_year = int(row["pick_year"])
    pick_label = str(row["pick_label"])
    value_row = pick_values.get((pick_year, pick_label), {})
    final_value = _optional_float(value_row.get("final_pick_value"))
    base_value = _optional_float(value_row.get("base_value_1000"))
    return {
        "pick": pick_label,
        "current_team": row.get("current_team_name") or row.get("current_team_id"),
        "original_team": row.get("original_team_name") or row.get("original_team_id"),
        "pick_year": pick_year,
        "round": row.get("round"),
        "overall_pick": row.get("overall_pick") or value_row.get("overall_pick"),
        "certainty": row.get("certainty") or "unknown",
        "base_value": base_value,
        "snapshot_value": final_value,
        "future_discount": _optional_float(value_row.get("future_discount")),
        "certainty_factor": _optional_float(value_row.get("certainty_adjustment")),
        "bucket": value_row.get("bucket"),
    }


def _team_rows(pick_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows_by_team: dict[str, list[dict[str, object]]] = {}
    for row in pick_rows:
        rows_by_team.setdefault(str(row["current_team"]), []).append(row)

    team_rows: list[dict[str, object]] = []
    for team, rows in rows_by_team.items():
        valued_rows = [row for row in rows if row["snapshot_value"] is not None]
        team_rows.append(
            {
                "team": team,
                "picks": len(rows),
                "snapshot_value": round(
                    sum(float(row["snapshot_value"]) for row in valued_rows),
                    1,
                ),
                "highest_pick": _highest_pick_label(rows),
            }
        )
    return sorted(
        team_rows,
        key=lambda row: (-float(row["snapshot_value"]), str(row["team"])),
    )


def _highest_pick_label(rows: list[dict[str, object]]) -> str | None:
    ordered = sorted(rows, key=lambda row: int(row["overall_pick"] or 999))
    if not ordered:
        return None
    return str(ordered[0]["pick"])


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
