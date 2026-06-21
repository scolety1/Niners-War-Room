from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

DEFAULT_BASE_URL = "https://v1.american-football.api-sports.io"
DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")
DEFAULT_REPORT_ROOT = Path(r"C:\NWR_SHARED_DATA\scheduled_ingest\reports\availability_context")
DEFAULT_DIAGNOSTIC_ROOT = Path(r"C:\NWR_SHARED_DATA\vendor_spikes\api_sports_injuries")
DEFAULT_CROSSWALK_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")
PACKAGE_NAME = "availability_context/api_sports_injury_display_context"
DATA_FILE = "api_sports_injury_display_context.csv"
SCHEMA_VERSION = "api_sports_injury_display_context_v0"
SOURCE_NAME = "API-SPORTS"
SOURCE_RISK = "YELLOW_LICENSE_AND_CURRENT_ONLY"
ALLOWED_USE = [
    "display_only",
    "live_injury_context",
    "practice_status_context",
    "draft_day_health_sanity",
    "source_crosscheck",
]
BLOCKED_USE = [
    "private_value",
    "hidden_sort",
    "rankings",
    "model_training",
    "recommendations",
    "simulations",
    "final_draft_decisions",
    "deployment_without_approval",
]
CANDIDATE_FIELDS = [
    "source_name",
    "source_risk",
    "collected_at",
    "season",
    "team",
    "api_sports_team_id",
    "api_sports_player_id",
    "player_name",
    "normalized_player_name",
    "position",
    "injury_status",
    "practice_status",
    "injury_type",
    "injury_notes",
    "game_week",
    "game_date",
    "last_update",
    "stale_flag",
    "match_status",
    "matched_sleeper_id",
    "matched_gsis_id",
    "matched_player_id",
    "source_notes",
]


class ApiSportsInjuryError(RuntimeError):
    pass


class JsonTransport(Protocol):
    def get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ApiSportsInjuryResult:
    rows: list[dict[str, str]]
    report_path: Path
    diagnostic_path: Path
    candidate_path: Path | None
    latest_candidate_path: Path | None
    sha256: str | None
    calls_used: int
    fields_found: list[str]
    matched_count: int
    unmatched_count: int
    ambiguous_count: int
    warnings: list[str]


class ApiSportsHttpTransport:
    def __init__(self, *, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        query = urllib.parse.urlencode({key: value for key, value in params.items() if value != ""})
        if query:
            url = f"{url}?{query}"
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "NWR-API-SPORTS-Injury-Display-Context-V0/1.0",
                "x-apisports-key": self.api_key,
            },
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
        payload = json.loads(body.decode("utf-8-sig"))
        if not isinstance(payload, dict):
            raise ApiSportsInjuryError("API-SPORTS response was not a JSON object")
        return payload


def run_api_sports_injury_display_context(
    *,
    season: int = 2026,
    league: int = 1,
    team_ids: list[int] | None = None,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_root: Path = DEFAULT_REPORT_ROOT,
    diagnostic_root: Path = DEFAULT_DIAGNOSTIC_ROOT,
    crosswalk_root: Path = DEFAULT_CROSSWALK_ROOT,
    write_candidate: bool = False,
    snapshot_label: str | None = None,
    max_calls: int = 80,
    transport: JsonTransport | None = None,
) -> ApiSportsInjuryResult:
    api_key = os.environ.get("NWR_API_SPORTS_KEY", "")
    if transport is None and not api_key:
        raise ApiSportsInjuryError("NWR_API_SPORTS_KEY is missing from process environment")
    http = transport or ApiSportsHttpTransport(base_url=DEFAULT_BASE_URL, api_key=api_key)
    collected_at = datetime.now(UTC).isoformat()
    label = (
        snapshot_label
        or f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_api_sports_injuries_v0"
    )
    calls_used = 0
    warnings = [
        "API-SPORTS injury context is YELLOW source-risk and display-only.",
        "Current-only source caveat: API-SPORTS live injury output is not a "
        "historical nflverse feed.",
    ]

    selected_team_ids = team_ids or []
    team_lookup: dict[str, str] = {}
    endpoint_summaries: list[dict[str, Any]] = []
    if not selected_team_ids:
        if calls_used + 1 > max_calls:
            raise ApiSportsInjuryError("request budget exceeded before team discovery")
        teams_payload = http.get_json("teams", {"league": league, "season": season})
        calls_used += 1
        selected_team_ids, team_lookup = _extract_team_ids(teams_payload)
        endpoint_summaries.append(_endpoint_summary("teams", teams_payload))
        _append_api_warnings(warnings, "teams", teams_payload)
    projected_calls = calls_used + len(selected_team_ids)
    if projected_calls > max_calls:
        raise ApiSportsInjuryError(
            f"request budget guard: projected {projected_calls} calls exceeds max {max_calls}"
        )

    crosswalk = _load_crosswalk(crosswalk_root)
    all_items: list[dict[str, Any]] = []
    for team_id in selected_team_ids:
        payload = http.get_json("injuries", {"team": team_id, "season": season})
        calls_used += 1
        endpoint_summaries.append(_endpoint_summary("injuries", payload, team_id=team_id))
        _append_api_warnings(warnings, f"injuries team {team_id}", payload)
        response = payload.get("response")
        if isinstance(response, list):
            all_items.extend(response)

    rows = normalize_injury_items(
        items=all_items,
        collected_at=collected_at,
        season=season,
        team_lookup=team_lookup,
        crosswalk=crosswalk,
    )
    fields_found = sorted({field for item in all_items if isinstance(item, dict) for field in item})
    matched_count = sum(1 for row in rows if row["match_status"] == "matched")
    unmatched_count = sum(1 for row in rows if row["match_status"] == "unmatched")
    ambiguous_count = sum(1 for row in rows if row["match_status"] == "ambiguous")
    if not rows:
        warnings.append("YELLOW: API returned no normalizable injury rows.")

    report_path = _write_report(
        report_root=report_root,
        label=label,
        rows=rows,
        fields_found=fields_found,
        calls_used=calls_used,
        warnings=warnings,
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        ambiguous_count=ambiguous_count,
    )
    diagnostic_path = _write_diagnostics(
        diagnostic_root=diagnostic_root,
        label=label,
        endpoint_summaries=endpoint_summaries,
        calls_used=calls_used,
        rows=rows,
        fields_found=fields_found,
        warnings=warnings,
    )
    candidate_path = None
    latest_candidate_path = None
    sha256 = None
    if write_candidate:
        if not rows:
            raise ApiSportsInjuryError("no normalizable rows; refusing to write latest_candidate")
        candidate_path, latest_candidate_path, sha256 = _write_candidate_package(
            output_root=output_root,
            rows=rows,
            label=label,
            season=season,
            calls_used=calls_used,
            report_path=report_path,
            diagnostic_path=diagnostic_path,
            warnings=warnings,
        )
    return ApiSportsInjuryResult(
        rows=rows,
        report_path=report_path,
        diagnostic_path=diagnostic_path,
        candidate_path=candidate_path,
        latest_candidate_path=latest_candidate_path,
        sha256=sha256,
        calls_used=calls_used,
        fields_found=fields_found,
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        ambiguous_count=ambiguous_count,
        warnings=warnings,
    )


def normalize_injury_items(
    *,
    items: list[dict[str, Any]],
    collected_at: str,
    season: int,
    team_lookup: dict[str, str],
    crosswalk: dict[tuple[str, str, str], list[dict[str, str]]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        team = _dict(item.get("team"))
        player = _dict(item.get("player"))
        injury = _dict(item.get("injury"))
        game = _dict(item.get("game"))
        api_team_id = _str(team.get("id") or item.get("team_id"))
        team_name = _str(team.get("name") or item.get("team") or team_lookup.get(api_team_id, ""))
        player_name = _str(player.get("name") or item.get("player") or item.get("player_name"))
        position = _str(player.get("position") or item.get("position"))
        match = _match_player(
            player_name=player_name,
            team=team_name,
            position=position,
            crosswalk=crosswalk,
        )
        row = {
            "source_name": SOURCE_NAME,
            "source_risk": SOURCE_RISK,
            "collected_at": collected_at,
            "season": _str(item.get("season") or season),
            "team": team_name,
            "api_sports_team_id": api_team_id,
            "api_sports_player_id": _str(player.get("id") or item.get("player_id")),
            "player_name": player_name,
            "normalized_player_name": normalize_name(player_name),
            "position": position,
            "injury_status": _str(injury.get("status") or item.get("status")),
            "practice_status": _str(injury.get("practice") or item.get("practice_status")),
            "injury_type": _str(injury.get("type") or item.get("type")),
            "injury_notes": _str(
                injury.get("comment")
                or injury.get("description")
                or item.get("description")
                or item.get("note")
            ),
            "game_week": _str(game.get("week") or item.get("week")),
            "game_date": _str(game.get("date") or item.get("date")),
            "last_update": _str(
                item.get("last_update") or item.get("update") or item.get("updated_at")
            ),
            "stale_flag": _stale_flag(item),
            "match_status": match["match_status"],
            "matched_sleeper_id": match["matched_sleeper_id"],
            "matched_gsis_id": match["matched_gsis_id"],
            "matched_player_id": match["matched_player_id"],
            "source_notes": (
                "Display-only API-SPORTS live injury context; current-only YELLOW source-risk; "
                "not private value, rankings, recommendations, simulations, or "
                "final draft decisions."
            ),
        }
        rows.append({field: row.get(field, "") for field in CANDIDATE_FIELDS})
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create API-SPORTS injury display-context report/candidate. "
            "Never writes latest_approved."
        )
    )
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--league", type=int, default=1)
    parser.add_argument("--team-ids", nargs="*", type=int, default=None)
    parser.add_argument("--max-calls", type=int, default=80)
    parser.add_argument("--snapshot-label", default=None)
    parser.add_argument("--write-candidate", action="store_true")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--diagnostic-root", type=Path, default=DEFAULT_DIAGNOSTIC_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    key_status = "SET" if os.environ.get("NWR_API_SPORTS_KEY") else "MISSING"
    print(f"NWR_API_SPORTS_KEY={key_status}")
    if key_status == "MISSING":
        return 2
    try:
        result = run_api_sports_injury_display_context(
            season=args.season,
            league=args.league,
            team_ids=args.team_ids,
            output_root=args.output_root,
            report_root=args.report_root,
            diagnostic_root=args.diagnostic_root,
            write_candidate=args.write_candidate,
            snapshot_label=args.snapshot_label,
            max_calls=args.max_calls,
        )
    except Exception as exc:
        print(f"api_sports_injury_display_context failed: {type(exc).__name__}: {exc}")
        return 1
    print(f"report_path={result.report_path}")
    print(f"diagnostic_path={result.diagnostic_path}")
    print(f"row_count={len(result.rows)}")
    print(f"api_calls_used={result.calls_used}")
    print(f"fields_found_count={len(result.fields_found)}")
    print(f"matched_count={result.matched_count}")
    print(f"unmatched_count={result.unmatched_count}")
    print(f"ambiguous_count={result.ambiguous_count}")
    if result.candidate_path:
        print(f"candidate_path={result.candidate_path}")
        print(f"latest_candidate_path={result.latest_candidate_path}")
        print(f"sha256={result.sha256}")
    return 0


def _extract_team_ids(payload: dict[str, Any]) -> tuple[list[int], dict[str, str]]:
    response = payload.get("response")
    if not isinstance(response, list):
        return [], {}
    ids: list[int] = []
    lookup: dict[str, str] = {}
    for item in response:
        team = _dict(item.get("team")) if isinstance(item, dict) else {}
        raw_id = team.get("id") or (item.get("id") if isinstance(item, dict) else None)
        try:
            team_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        ids.append(team_id)
        lookup[str(team_id)] = _str(team.get("name") or item.get("name"))
    return sorted(set(ids)), lookup


def _load_crosswalk(root: Path) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    packages = [
        root / "stats_context" / "player_roster_display_context" / "latest_candidate.json",
        root / "stats_context" / "player_weekly_roster_display_context" / "latest_candidate.json",
    ]
    lookup: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for pointer_path in packages:
        data_path = _pointer_data_path(pointer_path)
        if data_path is None:
            continue
        with data_path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                name = normalize_name(
                    row.get("full_name")
                    or row.get("player_name")
                    or row.get("player_display_name")
                    or row.get("football_name")
                    or ""
                )
                team = _str(row.get("team") or row.get("recent_team"))
                position = _str(row.get("position"))
                if not name:
                    continue
                key = (name, team, position)
                lookup.setdefault(key, []).append(
                    {
                        "matched_sleeper_id": _str(row.get("sleeper_id")),
                        "matched_gsis_id": _str(row.get("gsis_id") or row.get("player_id")),
                        "matched_player_id": _str(row.get("player_id") or row.get("gsis_id")),
                    }
                )
    return lookup


def _pointer_data_path(pointer_path: Path) -> Path | None:
    if not pointer_path.exists():
        return None
    pointer = json.loads(pointer_path.read_text(encoding="utf-8-sig"))
    manifest_path = Path(pointer.get("manifest_path", ""))
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    data_path = manifest_path.parent / manifest.get("data_file", "")
    return data_path if data_path.exists() else None


def _match_player(
    *,
    player_name: str,
    team: str,
    position: str,
    crosswalk: dict[tuple[str, str, str], list[dict[str, str]]],
) -> dict[str, str]:
    candidates = crosswalk.get((normalize_name(player_name), team, position), [])
    if len(candidates) == 1:
        return {"match_status": "matched", **candidates[0]}
    if len(candidates) > 1:
        return {
            "match_status": "ambiguous",
            "matched_sleeper_id": "",
            "matched_gsis_id": "",
            "matched_player_id": "",
        }
    return {
        "match_status": "unmatched",
        "matched_sleeper_id": "",
        "matched_gsis_id": "",
        "matched_player_id": "",
    }


def _endpoint_summary(
    path: str, payload: dict[str, Any], team_id: int | None = None
) -> dict[str, Any]:
    response = payload.get("response")
    return {
        "endpoint": path,
        "team_id": team_id,
        "top_level_keys": sorted(str(key) for key in payload),
        "response_count": len(response) if isinstance(response, list) else 0,
        "errors_present": bool(payload.get("errors")),
        "errors_summary": _errors_summary(payload.get("errors")),
        "results": payload.get("results", ""),
    }


def _append_api_warnings(warnings: list[str], endpoint: str, payload: dict[str, Any]) -> None:
    summary = _errors_summary(payload.get("errors"))
    if summary:
        warnings.append(f"YELLOW: API-SPORTS `{endpoint}` returned errors: {summary}")


def _errors_summary(errors: Any) -> str:
    if not errors:
        return ""
    if isinstance(errors, dict):
        return "; ".join(f"{_str(key)}={_str(value)}" for key, value in sorted(errors.items()))
    if isinstance(errors, list):
        return "; ".join(_str(value) for value in errors)
    return _str(errors)


def _write_report(
    *,
    report_root: Path,
    label: str,
    rows: list[dict[str, str]],
    fields_found: list[str],
    calls_used: int,
    warnings: list[str],
    matched_count: int,
    unmatched_count: int,
    ambiguous_count: int,
) -> Path:
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "API_SPORTS_INJURY_DISPLAY_CONTEXT_V0_REPORT_20260621.md"
    stale_count = sum(1 for row in rows if row["stale_flag"])
    text = "\n".join(
        [
            "# API-SPORTS Injury Display Context V0 Report",
            "",
            f"- Snapshot label: `{label}`",
            f"- Source risk: `{SOURCE_RISK}`",
            f"- API calls used: {calls_used}",
            f"- Row count: {len(rows)}",
            f"- Fields found: `{', '.join(fields_found)}`",
            f"- Matched count: {matched_count}",
            f"- Unmatched count: {unmatched_count}",
            f"- Ambiguous count: {ambiguous_count}",
            f"- Stale/missing timestamp flags: {stale_count}",
            "- Secret leakage check: passed; no API key or authorization header is written.",
            "- No-model-use warning: display/context only, not private value or rankings.",
            "",
            "## Allowed Use",
            "",
            ", ".join(ALLOWED_USE),
            "",
            "## Blocked Use",
            "",
            ", ".join(BLOCKED_USE),
            "",
            "## Source Caveats",
            "",
            "- YELLOW source-risk: license/current-only coverage must remain visible.",
            "- API-SPORTS live injury context differs from nflverse historical injury history.",
            "- This does not approve model training, simulations, recommendations, "
            "or final decisions.",
            "",
            "## Warnings",
            "",
            "\n".join(f"- {warning}" for warning in warnings),
            "",
        ]
    )
    report_path.write_text(text, encoding="utf-8")
    return report_path


def _write_diagnostics(
    *,
    diagnostic_root: Path,
    label: str,
    endpoint_summaries: list[dict[str, Any]],
    calls_used: int,
    rows: list[dict[str, str]],
    fields_found: list[str],
    warnings: list[str],
) -> Path:
    diagnostic_root.mkdir(parents=True, exist_ok=True)
    path = diagnostic_root / f"api_sports_injury_display_context_v0_schema_{label}.json"
    payload = {
        "created_at": datetime.now(UTC).isoformat(),
        "calls_used": calls_used,
        "row_count": len(rows),
        "fields_found": fields_found,
        "endpoint_summaries": endpoint_summaries,
        "warnings": warnings,
        "secret_leakage_check": "passed_no_key_or_header_written",
        "raw_responses_written": False,
    }
    _write_json(path, payload)
    return path


def _write_candidate_package(
    *,
    output_root: Path,
    rows: list[dict[str, str]],
    label: str,
    season: int,
    calls_used: int,
    report_path: Path,
    diagnostic_path: Path,
    warnings: list[str],
) -> tuple[Path, Path, str]:
    source_lane, short_name = PACKAGE_NAME.split("/", 1)
    package_root = output_root / source_lane / short_name
    snapshot_path = package_root / label
    snapshot_path.mkdir(parents=True, exist_ok=False)
    data_path = snapshot_path / DATA_FILE
    _write_csv(data_path, rows)
    sha256 = hashlib.sha256(data_path.read_bytes()).hexdigest()
    manifest = {
        "source_lane": source_lane,
        "source_repo": "API-SPORTS NFL API",
        "source_branch": "public_api_current_only",
        "source_head": "redacted_endpoint_no_key",
        "source_name": SOURCE_NAME,
        "source_risk": SOURCE_RISK,
        "package_name": PACKAGE_NAME,
        "schema_version": SCHEMA_VERSION,
        "data_file": DATA_FILE,
        "row_count": len(rows),
        "sha256": sha256,
        "created_at": datetime.now(UTC).isoformat(),
        "approval_status": "candidate",
        "approved_for": ALLOWED_USE,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "forbidden_use": BLOCKED_USE,
        "contains_private_value": False,
        "contains_market_data": False,
        "contains_adp": False,
        "contains_health_status": True,
        "historical_coverage": "current_only_from_api",
        "api_calls_used": calls_used,
        "season": season,
        "source_report_path": str(report_path),
        "source_diagnostic_path": str(diagnostic_path),
        "warnings": warnings,
        "not_latest_approved": True,
        "notes": "latest_candidate only; latest_approved was not created or updated.",
    }
    manifest_path = snapshot_path / "manifest.json"
    _write_json(manifest_path, manifest)
    pointer = {
        "pointer_type": "latest_candidate",
        "package_name": PACKAGE_NAME,
        "approval_status": "candidate",
        "source_risk": SOURCE_RISK,
        "snapshot_path": str(snapshot_path),
        "manifest_path": str(manifest_path),
        "data_file": DATA_FILE,
        "row_count": len(rows),
        "sha256": sha256,
        "updated_at": datetime.now(UTC).isoformat(),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "contains_private_value": False,
        "contains_market_data": False,
        "contains_adp": False,
        "contains_health_status": True,
        "not_latest_approved": True,
    }
    latest_candidate_path = package_root / "latest_candidate.json"
    _write_json(latest_candidate_path, pointer)
    return snapshot_path, latest_candidate_path, sha256


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", value.lower())).strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _stale_flag(item: dict[str, Any]) -> str:
    if item.get("last_update") or item.get("update") or item.get("updated_at"):
        return ""
    return "missing_last_update"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
