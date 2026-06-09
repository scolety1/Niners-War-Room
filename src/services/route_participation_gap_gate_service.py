from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.services.player_feature_receipts_service import DEFAULT_RECEIPT_VETERAN_MODEL_DIR

NORMALIZED_FEATURE_FILE = "stats_first_normalized_features.csv"
MODEL_OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"
PLAYER_INPUT_FILE = "veteran_player_inputs.csv"
IDENTITY_BRIDGE_FILE = "sleeper_nflverse_identity_bridge.csv"

ROUTE_PARTICIPATION_GAP_ROW_HEADER = (
    "player_id",
    "player_name",
    "position",
    "nfl_team",
    "fantasy_team",
    "overall_rank",
    "position_rank_label",
    "route_participation_status",
    "route_source_status",
    "route_role",
    "target_earning_stability",
    "role_security",
    "workload_earning",
    "confidence",
    "warnings",
    "paid_data_materiality",
    "paid_data_fields",
    "next_action",
)

ROUTE_PARTICIPATION_AREA_ROW_HEADER = (
    "area",
    "status",
    "player_count",
    "gap_count",
    "neutral_default_count",
    "missing_proxy_count",
    "derived_proxy_count",
    "imported_real_data_count",
    "paid_data_material_count",
    "priority_players",
    "next_action",
)

ROUTE_PARTICIPATION_SUMMARY_ROW_HEADER = (
    "summary_type",
    "position",
    "route_participation_status",
    "rows",
    "paid_data_material_count",
)

ROUTE_STATUS_UNAVAILABLE = "unavailable_free_public"
ROUTE_STATUS_PROXY = "proxy_only_snap_target"
ROUTE_STATUS_MISSING_PAID = "missing_paid_or_charted_data"
_GAP_STATUSES = {
    ROUTE_STATUS_UNAVAILABLE,
    ROUTE_STATUS_PROXY,
    ROUTE_STATUS_MISSING_PAID,
}
_MISSING_MARKERS = {"missing_participation_proxy", "missing_snap_counts"}
_NEUTRAL_MARKERS = {"missing_role_usage_features"}
_PAID_FIELDS = (
    "routes_run",
    "route_share",
    "targets_per_route_run",
    "yards_per_route_run",
    "pass_route_participation",
    "rb_route_share",
)


@dataclass(frozen=True)
class RouteParticipationGapGateReport:
    rows: tuple[dict[str, object], ...]
    area_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    issues: tuple[str, ...]


def build_route_participation_gap_gate_report(
    model_dir: str | Path = DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    *,
    my_team_name: str = "Niners",
) -> RouteParticipationGapGateReport:
    root = Path(model_dir)
    normalized_path = root / NORMALIZED_FEATURE_FILE
    output_path = root / MODEL_OUTPUT_FILE
    if not normalized_path.exists():
        return RouteParticipationGapGateReport((), (), (), (f"Missing {normalized_path}",))
    if not output_path.exists():
        return RouteParticipationGapGateReport((), (), (), (f"Missing {output_path}",))

    normalized_by_id = {row.get("player_id", ""): row for row in _read_csv(normalized_path)}
    roster_by_gsis = _roster_by_gsis(root)
    output_rows = _read_csv(output_path)
    rows = tuple(
        _gap_row(
            output_row,
            normalized_by_id.get(output_row.get("player_id", ""), {}),
            roster_by_gsis,
        )
        for output_row in output_rows
        if output_row.get("player_id") in normalized_by_id
    )
    return RouteParticipationGapGateReport(
        rows=rows,
        area_rows=tuple(_area_rows(rows, my_team_name=my_team_name)),
        summary_rows=tuple(_summary_rows(rows)),
        issues=(),
    )


def write_route_participation_gap_gate_report(
    output_dir: str | Path,
    report: RouteParticipationGapGateReport,
) -> dict[str, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "players": root / "route_participation_gap_players.csv",
        "areas": root / "route_participation_gap_areas.csv",
        "summary": root / "route_participation_gap_summary.csv",
    }
    _write_csv(paths["players"], ROUTE_PARTICIPATION_GAP_ROW_HEADER, report.rows)
    _write_csv(paths["areas"], ROUTE_PARTICIPATION_AREA_ROW_HEADER, report.area_rows)
    _write_csv(paths["summary"], ROUTE_PARTICIPATION_SUMMARY_ROW_HEADER, report.summary_rows)
    return paths


def _gap_row(
    output_row: dict[str, str],
    normalized_row: dict[str, str],
    roster_by_gsis: dict[str, dict[str, str]],
) -> dict[str, object]:
    player_id = output_row.get("player_id", "")
    position = output_row.get("position", normalized_row.get("position", ""))
    warnings = str(
        normalized_row.get("warnings")
        or output_row.get("warning_reasons")
        or ""
    )
    status = _route_participation_status(position, normalized_row, warnings)
    materiality = _paid_data_materiality(output_row, normalized_row, status)
    roster_row = roster_by_gsis.get(player_id, {})
    return {
        "player_id": player_id,
        "player_name": output_row.get("player_name") or normalized_row.get("player_name", ""),
        "position": position,
        "nfl_team": output_row.get("team") or normalized_row.get("team", ""),
        "fantasy_team": roster_row.get("team_name", ""),
        "overall_rank": _int(output_row.get("overall_rank")),
        "position_rank_label": output_row.get("position_rank_label", ""),
        "route_participation_status": status,
        "route_source_status": status,
        "route_role": _float_text(normalized_row.get("route_role")),
        "target_earning_stability": _float_text(normalized_row.get("target_earning_stability")),
        "role_security": _float_text(normalized_row.get("role_security")),
        "workload_earning": _float_text(normalized_row.get("workload_earning")),
        "confidence": _float_text(
            output_row.get("confidence_score") or normalized_row.get("confidence")
        ),
        "warnings": warnings,
        "paid_data_materiality": materiality,
        "paid_data_fields": "|".join(_PAID_FIELDS) if materiality in {"high", "medium"} else "",
        "next_action": _next_action(status, materiality),
    }


def _route_participation_status(
    position: str,
    row: dict[str, str],
    warnings: str,
) -> str:
    warning_set = _warning_set(warnings)
    route_role = _float(row.get("route_role"), 50.0)
    target_earning = _float(row.get("target_earning_stability"), 50.0)
    role_security = _float(row.get("role_security"), 50.0)
    if warning_set & _NEUTRAL_MARKERS:
        return ROUTE_STATUS_MISSING_PAID
    if warning_set & _MISSING_MARKERS:
        if position in {"WR", "TE"} and (route_role == 50.0 or target_earning == 50.0):
            return ROUTE_STATUS_UNAVAILABLE
        if route_role == 50.0 and role_security == 50.0:
            return ROUTE_STATUS_MISSING_PAID
        return ROUTE_STATUS_PROXY
    if position in {"WR", "TE"} and route_role == 50.0 and target_earning == 50.0:
        return ROUTE_STATUS_UNAVAILABLE
    if position in {"WR", "TE"}:
        return ROUTE_STATUS_PROXY
    return ROUTE_STATUS_PROXY


def _paid_data_materiality(
    output_row: dict[str, str],
    normalized_row: dict[str, str],
    status: str,
) -> str:
    if status not in _GAP_STATUSES:
        return "none"
    position = output_row.get("position", normalized_row.get("position", ""))
    overall_rank = _int(output_row.get("overall_rank"))
    if position in {"WR", "TE"} and overall_rank <= 100:
        return "high"
    if position == "RB" and _rb_receiving_role(normalized_row):
        return "medium"
    if overall_rank <= 50:
        return "medium"
    return "low"


def _next_action(status: str, materiality: str) -> str:
    if status == ROUTE_STATUS_PROXY and materiality == "none":
        return "Snap/target proxy only; do not treat as true routes run."
    if materiality == "high":
        return (
            "High-value pass catcher: paid/exported route participation would "
            "materially improve confidence."
        )
    if materiality == "medium":
        return (
            "Review before acting; route/participation or RB receiving-role data "
            "could change confidence."
        )
    return "Keep visible as a source weakness; do not treat route evidence as fully confirmed."


def _area_rows(
    rows: tuple[dict[str, object], ...],
    *,
    my_team_name: str,
) -> list[dict[str, object]]:
    sorted_rows = sorted(rows, key=lambda row: _int(row.get("overall_rank")) or 9999)
    my_team = my_team_name.lower()
    area_definitions = {
        "Niners roster": [
            row
            for row in sorted_rows
            if str(row.get("fantasy_team", "")).lower() == my_team
        ],
        "Top 50 overall": [row for row in sorted_rows if 0 < _int(row.get("overall_rank")) <= 50],
        "WR/TE top 30": [
            row
            for row in sorted_rows
            if row.get("position") in {"WR", "TE"} and _position_rank_number(row) <= 30
        ],
        "RB receiving-role players": [
            row for row in sorted_rows if row.get("position") == "RB" and _row_receiving_role(row)
        ],
    }
    return [_area_row(area, area_rows) for area, area_rows in area_definitions.items()]


def _area_row(area: str, rows: list[dict[str, object]]) -> dict[str, object]:
    counts = Counter(str(row.get("route_participation_status", "")) for row in rows)
    gap_rows = [row for row in rows if row.get("route_participation_status") in _GAP_STATUSES]
    paid_rows = [
        row for row in rows if row.get("paid_data_materiality") in {"high", "medium"}
    ]
    return {
        "area": area,
        "status": "review" if gap_rows else "ready",
        "player_count": len(rows),
        "gap_count": len(gap_rows),
        "neutral_default_count": counts[ROUTE_STATUS_MISSING_PAID],
        "missing_proxy_count": counts[ROUTE_STATUS_UNAVAILABLE],
        "derived_proxy_count": counts[ROUTE_STATUS_PROXY],
        "imported_real_data_count": 0,
        "paid_data_material_count": len(paid_rows),
        "priority_players": "; ".join(str(row.get("player_name", "")) for row in paid_rows[:12]),
        "next_action": (
            "Trial paid/exported route participation for priority players."
            if paid_rows
            else "No material route/participation paid-data gap in this slice."
        ),
    }


def _summary_rows(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    counts: Counter[tuple[str, str]] = Counter()
    paid_counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        key = (str(row.get("position", "")), str(row.get("route_participation_status", "")))
        counts[key] += 1
        if row.get("paid_data_materiality") in {"high", "medium"}:
            paid_counts[key] += 1
    output = [
        {
            "summary_type": "position_status",
            "position": position,
            "route_participation_status": status,
            "rows": count,
            "paid_data_material_count": paid_counts[(position, status)],
        }
        for (position, status), count in sorted(counts.items())
    ]
    total_counts: Counter[str] = Counter(
        str(row.get("route_participation_status", "")) for row in rows
    )
    total_paid_counts: Counter[str] = Counter(
        str(row.get("route_participation_status", ""))
        for row in rows
        if row.get("paid_data_materiality") in {"high", "medium"}
    )
    output.extend(
        {
            "summary_type": "overall_status",
            "position": "ALL",
            "route_participation_status": status,
            "rows": count,
            "paid_data_material_count": total_paid_counts[status],
        }
        for status, count in sorted(total_counts.items())
    )
    return output


def _roster_by_gsis(root: Path) -> dict[str, dict[str, str]]:
    players = _read_csv(root / PLAYER_INPUT_FILE)
    bridge_by_sleeper = {
        row.get("sleeper_id", ""): row
        for row in _read_csv(root / IDENTITY_BRIDGE_FILE)
    }
    output: dict[str, dict[str, str]] = {}
    for player in players:
        sleeper_id = player.get("player_id", "")
        bridge = bridge_by_sleeper.get(sleeper_id, {})
        gsis_id = bridge.get("matched_gsis_id") or bridge.get("bridge_gsis_id") or ""
        if gsis_id:
            output[gsis_id] = player
    return output


def _rb_receiving_role(row: dict[str, str]) -> bool:
    return _float(row.get("target_earning_stability"), 0.0) >= 35.0


def _row_receiving_role(row: dict[str, object]) -> bool:
    return _float(row.get("target_earning_stability"), 0.0) >= 35.0


def _position_rank_number(row: dict[str, object]) -> int:
    label = str(row.get("position_rank_label", ""))
    digits = "".join(character for character in label if character.isdigit())
    return _int(digits) or 9999


def _warning_set(value: object) -> set[str]:
    return {part.strip() for part in str(value or "").split("|") if part.strip()}


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _float_text(value: object) -> object:
    text = str(value or "")
    if text == "":
        return ""
    try:
        return round(float(text), 2)
    except ValueError:
        return text


def _int(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0
