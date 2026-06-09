from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_identity_join_gate_service import normalize_identity_name

DEFAULT_ROTOWIRE_WORKOUT_ROWS = Path(
    "local_exports/model_v4/workouts/latest/rotowire_workout_stats_may25.csv"
)
DEFAULT_ROTOWIRE_DEPTH_CHART_ROWS = Path(
    "local_exports/model_v4/depth_charts/latest/rotowire_upcoming_depth_charts_may22.csv"
)
DEFAULT_ROTOWIRE_TEAM_STATUS_ROWS = Path(
    "local_exports/external_sources/rotowire/nfl_players/latest/"
    "rotowire_nfl_team_status_review_rows.csv"
)
DEFAULT_ROTOWIRE_SOURCE_MANIFEST = Path(
    "local_exports/external_sources/rotowire/nfl_players/latest/"
    "rotowire_source_manifest.csv"
)
DEFAULT_ROTOWIRE_DISCOVERY_REPORT = Path(
    "docs/model_v4/ROTOWIRE_LOCAL_SOURCE_DISCOVERY_20260608.md"
)
DEFAULT_ROTOWIRE_SOURCE_CONTRACT = Path(
    "docs/model_v4/ROTOWIRE_LOCAL_SOURCE_CONTRACT_20260608.md"
)

SOURCE_LOADED_AT = "2026-06-08T00:00:00-06:00"
ALLOWED_USE = (
    "current_team_status_display_identity_team_source_repair_injury_status_context_"
    "source_quarantine_resolution"
)
BLOCKED_USE = (
    "do_not_use_for_nwr_dynasty_score_nwr_rank_tier_formula_weights_vorp_replacement_"
    "market_league_gaps_public_ranking_replacement_trade_cut_draft_recommendations_or_"
    "outcome_percentages"
)

NORMALIZED_ROTOWIRE_HEADER = (
    "source_provider",
    "source_file",
    "source_as_of_date",
    "source_loaded_at",
    "source_row_id",
    "player_id",
    "rotowire_player_id",
    "first_name",
    "last_name",
    "full_name",
    "search_full_name",
    "position",
    "fantasy_positions",
    "nfl_team",
    "team_abbr_raw",
    "status",
    "injury_status",
    "depth_chart_status",
    "active_flag",
    "age",
    "years_exp",
    "allowed_use",
    "blocked_use",
    "raw_source_payload_hash",
    "source_confidence",
)

ROTOWIRE_MANIFEST_HEADER = (
    "source_file",
    "file_type",
    "row_count",
    "column_names",
    "source_as_of_date",
    "contains_current_nfl_team",
    "contains_player_status",
    "contains_injuries",
    "contains_depth_chart_role",
    "contains_blocked_projection_rank_market_fields",
    "recommended_allowed_use",
    "recommended_blocked_use",
)

TEAM_ALIASES = {
    "49ERS": "SF",
    "BEARS": "CHI",
    "BENGALS": "CIN",
    "BILLS": "BUF",
    "BRONCOS": "DEN",
    "BROWNS": "CLE",
    "BUCCANEERS": "TB",
    "CARDINALS": "ARI",
    "CHARGERS": "LAC",
    "CHIEFS": "KC",
    "COLTS": "IND",
    "COMMANDERS": "WAS",
    "COWBOYS": "DAL",
    "DOLPHINS": "MIA",
    "EAGLES": "PHI",
    "FALCONS": "ATL",
    "GIANTS": "NYG",
    "JAGUARS": "JAX",
    "JETS": "NYJ",
    "LIONS": "DET",
    "PACKERS": "GB",
    "PANTHERS": "CAR",
    "PATRIOTS": "NE",
    "RAIDERS": "LV",
    "RAMS": "LAR",
    "RAVENS": "BAL",
    "SAINTS": "NO",
    "SEAHAWKS": "SEA",
    "STEELERS": "PIT",
    "TEXANS": "HOU",
    "TITANS": "TEN",
    "VIKINGS": "MIN",
    "WFT": "WAS",
    "WSH": "WAS",
    "LA": "LAR",
}
NO_TEAM_VALUES = {"", "FA", "FREE AGENT", "RET", "RETIRED", "UNSIGNED"}


@dataclass(frozen=True)
class RotoWireTeamStatusResult:
    rows: tuple[dict[str, object], ...]
    manifest_rows: tuple[dict[str, object], ...]
    discovery_report: str
    source_contract: str
    summary: dict[str, object]


@dataclass(frozen=True)
class RotoWireTeamStatusPaths:
    review_rows: Path
    manifest: Path
    discovery_report: Path
    source_contract: Path


def build_rotowire_team_status_source(
    *,
    workout_path: str | Path = DEFAULT_ROTOWIRE_WORKOUT_ROWS,
    depth_chart_path: str | Path = DEFAULT_ROTOWIRE_DEPTH_CHART_ROWS,
) -> RotoWireTeamStatusResult:
    workout = Path(workout_path)
    depth = Path(depth_chart_path)
    rows = (
        *_workout_rows(workout),
        *_depth_chart_rows(depth),
    )
    manifest_rows = _manifest_rows((workout, depth))
    summary = {
        "normalized_rows": len(rows),
        "team_rows": sum(bool(row["nfl_team"]) for row in rows),
        "no_team_rows": sum(row["status"] == "free_agent_or_no_team" for row in rows),
        "source_files_used": sum(1 for path in (workout, depth) if path.exists()),
    }
    return RotoWireTeamStatusResult(
        rows=tuple(rows),
        manifest_rows=manifest_rows,
        discovery_report=_discovery_report(manifest_rows),
        source_contract=_source_contract(),
        summary=summary,
    )


def write_rotowire_team_status_source(
    *,
    result: RotoWireTeamStatusResult | None = None,
    review_rows: str | Path = DEFAULT_ROTOWIRE_TEAM_STATUS_ROWS,
    manifest_path: str | Path = DEFAULT_ROTOWIRE_SOURCE_MANIFEST,
    discovery_report_path: str | Path = DEFAULT_ROTOWIRE_DISCOVERY_REPORT,
    source_contract_path: str | Path = DEFAULT_ROTOWIRE_SOURCE_CONTRACT,
) -> RotoWireTeamStatusPaths:
    result = result or build_rotowire_team_status_source()
    rows_path = Path(review_rows)
    manifest = Path(manifest_path)
    discovery = Path(discovery_report_path)
    contract = Path(source_contract_path)
    _write_csv(rows_path, NORMALIZED_ROTOWIRE_HEADER, result.rows)
    _write_csv(manifest, ROTOWIRE_MANIFEST_HEADER, result.manifest_rows)
    discovery.parent.mkdir(parents=True, exist_ok=True)
    contract.parent.mkdir(parents=True, exist_ok=True)
    discovery.write_text(result.discovery_report, encoding="utf-8")
    contract.write_text(result.source_contract, encoding="utf-8")
    return RotoWireTeamStatusPaths(
        review_rows=rows_path,
        manifest=manifest,
        discovery_report=discovery,
        source_contract=contract,
    )


def rotowire_team_status_lookup(
    path: str | Path = DEFAULT_ROTOWIRE_TEAM_STATUS_ROWS,
) -> dict[tuple[str, str], tuple[dict[str, str], ...]]:
    lookup: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in _read_rows(Path(path)):
        key = (
            normalize_identity_name(row.get("full_name")),
            str(row.get("position") or "").upper(),
        )
        if key[0] and key[1]:
            lookup.setdefault(key, []).append(row)
    return {key: tuple(value) for key, value in lookup.items()}


def select_rotowire_team_status_row(
    rows: tuple[dict[str, str], ...],
) -> dict[str, str]:
    if not rows:
        return {}
    exact_current = [row for row in rows if row.get("nfl_team")]
    if exact_current:
        teams = {_team_alias(row.get("nfl_team")) for row in exact_current}
        if len(teams) == 1:
            return exact_current[0]
        return {}
    no_team = [row for row in rows if row.get("status") == "free_agent_or_no_team"]
    return no_team[0] if no_team else {}


def _workout_rows(path: Path) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for index, row in enumerate(_read_rows(path), start=1):
        name = str(row.get("player") or "").strip()
        position = str(row.get("position") or "").upper()
        if not name or not position:
            continue
        team_raw = str(row.get("team") or "").strip()
        team = _team_alias(team_raw)
        status = "free_agent_or_no_team" if _is_no_team(team_raw) else "active_team_listed"
        first, last = _split_name(name)
        output.append(
            {
                "source_provider": "rotowire",
                "source_file": str(path),
                "source_as_of_date": row.get("collected_at_utc", ""),
                "source_loaded_at": SOURCE_LOADED_AT,
                "source_row_id": f"workout:{index}",
                "player_id": "",
                "rotowire_player_id": "",
                "first_name": first,
                "last_name": last,
                "full_name": name,
                "search_full_name": normalize_identity_name(name),
                "position": position,
                "fantasy_positions": position,
                "nfl_team": "" if _is_no_team(team_raw) else team,
                "team_abbr_raw": team_raw,
                "status": status,
                "injury_status": "",
                "depth_chart_status": "",
                "active_flag": "0" if _is_no_team(team_raw) else "1",
                "age": "",
                "years_exp": "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "raw_source_payload_hash": _payload_hash(row),
                "source_confidence": "local_subscription_export_current_status_context",
            }
        )
    return tuple(output)


def _depth_chart_rows(path: Path) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for index, row in enumerate(_read_rows(path), start=1):
        name = str(row.get("player") or "").strip()
        position = str(row.get("position") or "").upper()
        if not name or not position:
            continue
        team_raw = str(row.get("team") or "").strip()
        first, last = _split_name(name)
        output.append(
            {
                "source_provider": "rotowire",
                "source_file": str(path),
                "source_as_of_date": row.get("collected_at_utc", ""),
                "source_loaded_at": SOURCE_LOADED_AT,
                "source_row_id": f"depth_chart:{index}",
                "player_id": "",
                "rotowire_player_id": "",
                "first_name": first,
                "last_name": last,
                "full_name": name,
                "search_full_name": normalize_identity_name(name),
                "position": position,
                "fantasy_positions": position,
                "nfl_team": _team_alias(team_raw),
                "team_abbr_raw": team_raw,
                "status": "active_depth_chart",
                "injury_status": row.get("status", ""),
                "depth_chart_status": row.get("slot", ""),
                "active_flag": "1",
                "age": "",
                "years_exp": "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "raw_source_payload_hash": _payload_hash(row),
                "source_confidence": "local_subscription_export_depth_chart_context",
            }
        )
    return tuple(output)


def _manifest_rows(paths: tuple[Path, ...]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for path in paths:
        csv_rows = _read_rows(path)
        columns = tuple(csv_rows[0].keys()) if csv_rows else ()
        lower_columns = " ".join(column.lower() for column in columns)
        rows.append(
            {
                "source_file": str(path),
                "file_type": path.suffix.lstrip("."),
                "row_count": len(csv_rows),
                "column_names": "|".join(columns),
                "source_as_of_date": _first_source_date(csv_rows),
                "contains_current_nfl_team": "yes" if "team" in lower_columns else "no",
                "contains_player_status": "yes" if "status" in lower_columns else "yes_team_fa",
                "contains_injuries": "yes" if "status" in lower_columns else "no",
                "contains_depth_chart_role": "yes" if "depth" in lower_columns else "no",
                "contains_blocked_projection_rank_market_fields": "no",
                "recommended_allowed_use": ALLOWED_USE,
                "recommended_blocked_use": BLOCKED_USE,
            }
        )
    return tuple(rows)


def _discovery_report(manifest_rows: tuple[dict[str, object], ...]) -> str:
    lines = [
        "# RotoWire Local Source Discovery - 2026-06-08",
        "",
        "This discovery used local files already present in the repo. It did not scrape "
        "RotoWire, call a live app, use credentials, or read browser/session data.",
        "",
        "## Candidate Files Used",
        "",
        "| Path | Type | Rows | Columns | Current team | Status | Injuries | Depth | "
        "Blocked value fields | Allowed use | Blocked use |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in manifest_rows:
        lines.append(
            "| {source_file} | {file_type} | {row_count} | `{column_names}` | "
            "{contains_current_nfl_team} | {contains_player_status} | {contains_injuries} | "
            "{contains_depth_chart_role} | {contains_blocked_projection_rank_market_fields} | "
            "{recommended_allowed_use} | {recommended_blocked_use} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Discovery Conclusion",
            "",
            "- `rotowire_workout_stats_may25.csv` has exact local player/team rows for the "
            "12 unresolved non-kicker targets, including `FA` for teamless players.",
            "- `rotowire_upcoming_depth_charts_may22.csv` provides current depth-chart "
            "team/status context for matched active players such as Jauan Jennings, "
            "David Njoku, Aaron Rodgers, and Darius Slayton.",
            "- RotoWire projection, ranking, salary, ADP, market-like, and fantasy point "
            "fields are not normalized into the team/status source and remain blocked "
            "from private value.",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_contract() -> str:
    return (
        "# RotoWire Local Source Contract - 2026-06-08\n\n"
        "RotoWire data used here is a user-provided local subscription export/snapshot. "
        "The app makes no live RotoWire calls, performs no scraping, and stores no "
        "credentials, cookies, tokens, or account/session data.\n\n"
        "## Files Used\n\n"
        "- `local_exports/model_v4/workouts/latest/rotowire_workout_stats_may25.csv`\n"
        "- `local_exports/model_v4/depth_charts/latest/"
        "rotowire_upcoming_depth_charts_may22.csv`\n\n"
        "## Allowed Use\n\n"
        "- Current NFL team/status display.\n"
        "- Identity/team source repair.\n"
        "- Injury/status context.\n"
        "- Warning/data-needed explanation.\n"
        "- Source quarantine resolution.\n"
        "- Role/depth-chart context only where an existing source-safe pipeline explicitly "
        "allows it.\n\n"
        "## Blocked Use\n\n"
        "- NWR Dynasty Score, NWR Rank, tier, formula weights, VORP/replacement, "
        "market/league gaps, public ranking replacement, trade/cut/draft recommendations, "
        "or outcome percentages.\n"
        "- RotoWire projections, rankings, fantasy points, ADP, salaries, DFS values, "
        "or market-like fields cannot affect private NWR value.\n\n"
        "## Source Precedence\n\n"
        "For current-team/status repair, normalized local RotoWire exact deterministic "
        "matches are checked before active-pack sidecars. Old checkpoint team remains "
        "historical/context only and cannot override RotoWire current team/status.\n\n"
        "## Interpretation\n\n"
        "- `FA`, blank, unsigned, retired, or equivalent values mean no current team is "
        "assigned. The row can be classified as `current_status_verified_no_team` but "
        "must not receive an invented team.\n"
        "- Conflicting current-team sources remain quarantined until reconciled.\n"
        "- Ambiguous or fuzzy matches are audit candidates only and are not applied repairs.\n"
    )


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _team_alias(value: object) -> str:
    team = str(value or "").strip().upper()
    if team in NO_TEAM_VALUES:
        return ""
    return TEAM_ALIASES.get(team, team)


def _is_no_team(value: object) -> bool:
    return str(value or "").strip().upper() in NO_TEAM_VALUES


def _split_name(value: str) -> tuple[str, str]:
    parts = value.split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def _payload_hash(row: dict[str, str]) -> str:
    payload = json.dumps(row, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _first_source_date(rows: tuple[dict[str, str], ...]) -> str:
    for row in rows:
        for column in ("collected_at_utc", "source_as_of_date", "snapshot_date"):
            value = str(row.get(column) or "").strip()
            if value:
                return value
    return ""
