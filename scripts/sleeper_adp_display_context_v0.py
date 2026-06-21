from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")
DEFAULT_REPORT_ROOT = Path(r"C:\NWR_SHARED_DATA\scheduled_ingest\reports\market_behavior")
DEFAULT_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")
DEFAULT_SEASON_TYPE = "regular"
PACKAGE_NAME = "market_behavior/sleeper_adp_display_context"
DATA_FILE = "sleeper_adp_display_context.csv"
SOURCE_RISK = "YELLOW_UNDOCUMENTED_ENDPOINT"
SCHEMA_VERSION = "sleeper_adp_display_context_v0"
ALLOWED_USE = [
    "display_only",
    "market_awareness",
    "draft_timing_context",
    "mock_draft_display_overlay",
]
BLOCKED_USE = [
    "private_value",
    "hidden_sort",
    "rankings",
    "model_training",
    "recommendations",
    "final_draft_decisions",
    "decision_driving_simulations",
    "deployment_without_approval",
]
ADP_FIELDS = [
    "adp_std",
    "adp_half_ppr",
    "adp_ppr",
    "adp_2qb",
    "adp_dynasty",
    "adp_dynasty_std",
    "adp_dynasty_half_ppr",
    "adp_dynasty_ppr",
    "adp_dynasty_2qb",
    "adp_rookie",
]
CANDIDATE_FIELDS = [
    "source_name",
    "source_type",
    "source_risk",
    "season",
    "collected_at",
    "updated_at",
    "last_modified",
    "sleeper_player_id",
    "player_name",
    "normalized_player_name",
    "team",
    "position",
    *ADP_FIELDS,
    "preferred_adp_for_nwr",
    "preferred_adp_reason",
    "stale_flag",
    "source_notes",
]
FORBIDDEN_CANDIDATE_FIELD_PATTERNS = (
    "private",
    "hidden",
    "sort",
    "rank",
    "ranking",
    "recommendation",
    "projection",
    "pts_",
    "fantasy_points",
    "value",
    "score",
    "probability",
)


class SleeperAdpError(ValueError):
    pass


@dataclass(frozen=True)
class CandidateResult:
    rows: list[dict[str, str]]
    report_path: Path
    candidate_path: Path | None
    latest_candidate_path: Path | None
    sha256: str | None
    preferred_adp_coverage_count: int
    missing_adp_count: int
    warnings: list[str]


def run_sleeper_adp_display_context(
    *,
    season: int,
    positions: list[str],
    output_root: Path,
    report_root: Path,
    write_candidate: bool,
    snapshot_label: str | None = None,
    order_by: str | None = None,
    input_json: Path | None = None,
) -> CandidateResult:
    collected_at = datetime.now(UTC).isoformat()
    label = snapshot_label or _timestamp_label("sleeper_adp_display_context_v0")
    warnings = [
        "Sleeper projections endpoint is undocumented by official Sleeper API docs.",
        "Candidate is display-only market context and not private value.",
    ]
    endpoint_url = build_endpoint_url(
        season=season,
        positions=positions,
        season_type=DEFAULT_SEASON_TYPE,
        order_by=order_by,
    )
    if input_json is not None:
        payload = json.loads(input_json.read_text(encoding="utf-8"))
        warnings.append(f"Loaded payload from local test input: {input_json}")
    else:
        payload = fetch_json(endpoint_url)

    rows = normalize_payload(payload=payload, season=season, collected_at=collected_at)
    if not rows:
        raise SleeperAdpError("Sleeper ADP endpoint returned no normalizable rows")

    report_path = write_schema_report(
        report_root=report_root,
        label=label,
        rows=rows,
        payload=payload,
        endpoint_url=endpoint_url,
        positions=positions,
        season=season,
        collected_at=collected_at,
        warnings=warnings,
        write_candidate=write_candidate,
    )
    candidate_path = None
    latest_candidate_path = None
    sha256 = None
    if write_candidate:
        candidate_path, latest_candidate_path, sha256 = write_candidate_package(
            output_root=output_root,
            rows=rows,
            label=label,
            endpoint_url=endpoint_url,
            report_path=report_path,
            season=season,
            positions=positions,
            collected_at=collected_at,
            warnings=warnings,
        )

    preferred_coverage = sum(1 for row in rows if row["preferred_adp_for_nwr"])
    return CandidateResult(
        rows=rows,
        report_path=report_path,
        candidate_path=candidate_path,
        latest_candidate_path=latest_candidate_path,
        sha256=sha256,
        preferred_adp_coverage_count=preferred_coverage,
        missing_adp_count=len(rows) - preferred_coverage,
        warnings=warnings,
    )


def build_endpoint_url(
    *,
    season: int,
    positions: list[str],
    season_type: str,
    order_by: str | None = None,
) -> str:
    query: list[tuple[str, str]] = [("season_type", season_type)]
    query.extend(("position[]", position) for position in positions)
    if order_by:
        query.append(("order_by", order_by))
    encoded = urllib.parse.urlencode(query, doseq=True)
    return f"https://api.sleeper.com/projections/nfl/{season}?{encoded}"


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "NWR-Sleeper-ADP-Display-Context-V0/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
    except Exception as urllib_error:
        body = _fetch_json_with_curl(url, urllib_error)

    try:
        return json.loads(body.decode("utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SleeperAdpError(f"Sleeper endpoint did not return valid JSON: {exc}") from exc


def normalize_payload(
    *,
    payload: Any,
    season: int,
    collected_at: str,
) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        raise SleeperAdpError(f"Expected Sleeper projections list, got {type(payload).__name__}")

    rows: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
        player = item.get("player") if isinstance(item.get("player"), dict) else {}
        player_name = _player_name(item=item, player=player)
        player_id = _string(item.get("player_id") or player.get("player_id"))
        position = _position(item=item, player=player)
        team = _string(item.get("team") or player.get("team") or player.get("team_abbr"))
        preferred_value, preferred_reason = preferred_adp(stats)
        row = {
            "source_name": "Sleeper",
            "source_type": "adp",
            "source_risk": SOURCE_RISK,
            "season": _string(item.get("season") or season),
            "collected_at": collected_at,
            "updated_at": _string(item.get("updated_at")),
            "last_modified": _string(item.get("last_modified")),
            "sleeper_player_id": player_id,
            "player_name": player_name,
            "normalized_player_name": normalize_name(player_name),
            "team": team,
            "position": position,
            "preferred_adp_for_nwr": preferred_value,
            "preferred_adp_reason": preferred_reason,
            "stale_flag": _stale_flag(item),
            "source_notes": (
                "Undocumented Sleeper projections endpoint; YELLOW source-risk; "
                "display-only market timing context; not private value."
            ),
        }
        for field in ADP_FIELDS:
            row[field] = _number_string(stats.get(field))
        rows.append({field: row.get(field, "") for field in CANDIDATE_FIELDS})

    return rows


def preferred_adp(stats: dict[str, Any]) -> tuple[str, str]:
    ordered_choices = [
        ("adp_dynasty_std", "adp_dynasty_std_primary_dynasty_non_ppr"),
        ("adp_dynasty", "adp_dynasty_fallback"),
        ("adp_std", "adp_std_fallback_non_ppr"),
        ("adp_ppr", "adp_ppr_last_resort_display_only"),
    ]
    for field, reason in ordered_choices:
        value = _number_string(stats.get(field))
        if value:
            return value, reason
    return "", "missing_preferred_adp"


def write_schema_report(
    *,
    report_root: Path,
    label: str,
    rows: list[dict[str, str]],
    payload: Any,
    endpoint_url: str,
    positions: list[str],
    season: int,
    collected_at: str,
    warnings: list[str],
    write_candidate: bool,
) -> Path:
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / f"sleeper_adp_display_context_v0_report_{label}.md"
    top_level_keys = _top_level_keys(payload)
    stats_keys = _nested_keys(payload, "stats")
    player_keys = _nested_keys(payload, "player")
    preferred_coverage = sum(1 for row in rows if row["preferred_adp_for_nwr"])
    missing_coverage = len(rows) - preferred_coverage
    lines = [
        "# Sleeper ADP Display Context V0 Report",
        "",
        "## Scope",
        "",
        "Local-only schema/report output for an undocumented Sleeper projections "
        "endpoint. This report does not approve ADP for private value, rankings, "
        "hidden sort, model training, recommendations, simulations, final draft "
        "decisions, deployment, or latest_approved.",
        "",
        "## Endpoint",
        "",
        f"- URL: `{endpoint_url}`",
        "- Official docs status: not documented in Sleeper public API docs",
        f"- Source risk: `{SOURCE_RISK}`",
        f"- Season: `{season}`",
        f"- Positions: `{', '.join(positions)}`",
        f"- Collected at: `{collected_at}`",
        f"- Candidate written: `{write_candidate}`",
        "",
        "## Counts",
        "",
        f"- Normalized rows: {len(rows)}",
        f"- Preferred ADP coverage: {preferred_coverage}",
        f"- Missing preferred ADP: {missing_coverage}",
        "",
        "## Response Shape",
        "",
        f"- Top-level type: `{type(payload).__name__}`",
        f"- Top-level keys observed: `{', '.join(top_level_keys)}`",
        f"- `stats` keys observed: `{', '.join(stats_keys)}`",
        f"- `player` keys observed: `{', '.join(player_keys)}`",
        "",
        "## Candidate Fields",
        "",
        f"`{', '.join(CANDIDATE_FIELDS)}`",
        "",
        "## ADP Fields Kept",
        "",
        f"`{', '.join(ADP_FIELDS)}`",
        "",
        "## Fields Omitted From Candidate",
        "",
        "- `pts_std`, `pts_half_ppr`, `pts_ppr`, and projection/scoring fields are "
        "omitted from V0 candidate output.",
        "- Raw API payload is not written by this script.",
        "",
        "## Preferred ADP Rule",
        "",
        "1. `adp_dynasty_std`",
        "2. `adp_dynasty`",
        "3. `adp_std`",
        "4. `adp_ppr` only as a last-resort display-only fallback",
        "",
        "`adp_rookie` remains a separate rookie market-context field and does not "
        "replace the main preferred ADP field.",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in warnings)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def write_candidate_package(
    *,
    output_root: Path,
    rows: list[dict[str, str]],
    label: str,
    endpoint_url: str,
    report_path: Path,
    season: int,
    positions: list[str],
    collected_at: str,
    warnings: list[str],
) -> tuple[Path, Path, str]:
    _validate_candidate_fields()
    source_lane, short_name = PACKAGE_NAME.split("/", 1)
    package_root = output_root / source_lane / short_name
    snapshot_path = package_root / label
    snapshot_path.mkdir(parents=True, exist_ok=False)
    data_path = snapshot_path / DATA_FILE
    _write_csv(data_path, rows)
    sha256 = _file_sha256(data_path)
    manifest = _manifest(
        rows=rows,
        sha256=sha256,
        label=label,
        endpoint_url=endpoint_url,
        report_path=report_path,
        season=season,
        positions=positions,
        collected_at=collected_at,
        warnings=warnings,
    )
    manifest_path = snapshot_path / "manifest.json"
    _write_json(manifest_path, manifest)
    pointer = {
        "pointer_type": "latest_candidate",
        "package_name": PACKAGE_NAME,
        "approval_status": "candidate",
        "approval_scope": "display_only_market_context_review",
        "source_risk": SOURCE_RISK,
        "snapshot_path": str(snapshot_path),
        "manifest_path": str(manifest_path),
        "data_file": DATA_FILE,
        "row_count": len(rows),
        "sha256": sha256,
        "updated_at": datetime.now(UTC).isoformat(),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "forbidden_use": BLOCKED_USE,
        "contains_private_value": False,
        "contains_market_data": True,
        "contains_adp": True,
        "not_latest_approved": True,
        "notes": "latest_candidate only; latest_approved was not created or updated.",
    }
    latest_candidate_path = package_root / "latest_candidate.json"
    _write_json(latest_candidate_path, pointer)
    return snapshot_path, latest_candidate_path, sha256


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create display-only Sleeper ADP market-context reports or explicit "
            "Lane Exchange latest_candidate packages. Never writes latest_approved."
        )
    )
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--positions", nargs="+", default=list(DEFAULT_POSITIONS))
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--write-candidate", action="store_true")
    parser.add_argument("--snapshot-label", default=None)
    parser.add_argument("--order-by", default=None)
    parser.add_argument(
        "--input-json",
        type=Path,
        default=None,
        help="Local test input only; no raw API response is written by this script.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_sleeper_adp_display_context(
            season=args.season,
            positions=args.positions,
            output_root=args.output_root,
            report_root=args.report_root,
            write_candidate=args.write_candidate,
            snapshot_label=args.snapshot_label,
            order_by=args.order_by,
            input_json=args.input_json,
        )
    except Exception as exc:
        print(f"Sleeper ADP display context failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"report_path={result.report_path}")
    print(f"write_candidate={result.candidate_path is not None}")
    print(f"row_count={len(result.rows)}")
    print(f"preferred_adp_coverage_count={result.preferred_adp_coverage_count}")
    print(f"missing_adp_count={result.missing_adp_count}")
    if result.candidate_path:
        print(f"candidate_path={result.candidate_path}")
        print(f"latest_candidate_path={result.latest_candidate_path}")
        print(f"sha256={result.sha256}")
    return 0


def _manifest(
    *,
    rows: list[dict[str, str]],
    sha256: str,
    label: str,
    endpoint_url: str,
    report_path: Path,
    season: int,
    positions: list[str],
    collected_at: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "source_lane": "market_behavior",
        "source_repo": "Sleeper projections endpoint",
        "source_branch": "public_read_only_api",
        "source_head": endpoint_url,
        "package_name": PACKAGE_NAME,
        "schema_version": SCHEMA_VERSION,
        "data_file": DATA_FILE,
        "row_count": len(rows),
        "sha256": sha256,
        "created_at": datetime.now(UTC).isoformat(),
        "approval_status": "candidate",
        "approved_for": ["display_only_market_context_review"],
        "approval_scope": "display_only_market_context_review",
        "source_risk": SOURCE_RISK,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "forbidden_use": BLOCKED_USE,
        "contains_private_value": False,
        "contains_market_data": True,
        "contains_adp": True,
        "not_latest_approved": True,
        "not_private_value": True,
        "not_rankings": True,
        "not_hidden_sort": True,
        "not_model_training": True,
        "not_recommendations": True,
        "not_final_draft_decision": True,
        "not_decision_driving_simulation": True,
        "season": season,
        "positions": positions,
        "collected_at": collected_at,
        "source_report_path": str(report_path),
        "source_warnings": warnings,
        "notes": (
            "YELLOW source-risk because the Sleeper projections/ADP endpoint is "
            "publicly reachable but not documented in official Sleeper API docs. "
            "ADP is display-only market timing context and must not become NWR "
            "private value, ranking, hidden sort, simulation driver, or final "
            "draft decision input."
        ),
        "snapshot_label": label,
    }


def _player_name(*, item: dict[str, Any], player: dict[str, Any]) -> str:
    direct = item.get("player")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    for key in ("full_name", "search_full_name", "metadata_full_name"):
        value = _string(player.get(key))
        if value:
            return value
    first = _string(player.get("first_name"))
    last = _string(player.get("last_name"))
    name = f"{first} {last}".strip()
    return name or _string(item.get("player_id") or player.get("player_id"))


def _position(*, item: dict[str, Any], player: dict[str, Any]) -> str:
    value = _string(item.get("position") or player.get("position"))
    if value:
        return value
    positions = player.get("fantasy_positions")
    if isinstance(positions, list) and positions:
        return _string(positions[0])
    return ""


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", name.lower())).strip()


def _stale_flag(item: dict[str, Any]) -> str:
    if not item.get("updated_at") and not item.get("last_modified"):
        return "missing_source_timestamp"
    return ""


def _number_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() in {"none", "null", "nan"}:
            return ""
        try:
            return str(float(stripped)).rstrip("0").rstrip(".")
        except ValueError:
            return stripped
    if isinstance(value, int | float):
        return str(float(value)).rstrip("0").rstrip(".")
    return _string(value)


def _string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _top_level_keys(payload: Any) -> list[str]:
    keys: set[str] = set()
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                keys.update(str(key) for key in item)
    return sorted(keys)


def _nested_keys(payload: Any, nested_name: str) -> list[str]:
    keys: set[str] = set()
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and isinstance(item.get(nested_name), dict):
                keys.update(str(key) for key in item[nested_name])
    return sorted(keys)


def _validate_candidate_fields() -> None:
    for field in CANDIDATE_FIELDS:
        lowered = field.lower()
        if field.startswith("adp_") or field == "preferred_adp_for_nwr":
            continue
        if field in {"source_risk", "source_notes"}:
            continue
        if any(pattern in lowered for pattern in FORBIDDEN_CANDIDATE_FIELD_PATTERNS):
            raise SleeperAdpError(f"Forbidden field name in candidate schema: {field}")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fetch_json_with_curl(url: str, urllib_error: Exception) -> bytes:
    try:
        result = subprocess.run(
            ["curl.exe", "-L", "-sS", url],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except Exception as curl_error:
        raise SleeperAdpError(
            "Sleeper endpoint fetch failed with urllib and curl fallback; "
            f"urllib={urllib_error}; curl={curl_error}"
        ) from curl_error
    return result.stdout


def _timestamp_label(suffix: str) -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{suffix}"


if __name__ == "__main__":
    raise SystemExit(main())
