from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = Path(r"C:\NWR_SHARED_DATA\public_sources\cfbd")
DEFAULT_SECRET_PATH = Path(r"C:\NWR_LOCAL_SECRETS\cfbd_api_key.txt")
DEFAULT_ARTIFACT_DIR = REPO_ROOT / "docs" / "hq" / "data_sources" / "cfbd_review_artifacts_20260624"

SEASONS = (2024, 2025, 2026)
STAT_CATEGORIES = ("passing", "rushing", "receiving")
GUARDRAILS = {
    "model_use_allowed": "false",
    "training_allowed": "false",
    "identity_review_required": "true",
    "review_only": "true",
}

MANIFEST_COLUMNS = (
    "run_id",
    "run_timestamp",
    "dataset_name",
    "season",
    "endpoint_or_source",
    "action_type",
    "refreshed",
    "raw_cache_location",
    "tracked_artifact",
    "row_count",
    "freshness",
    "model_use_allowed",
    "training_allowed",
    "identity_review_required",
    "review_only",
    "notes",
)

IDENTITY_COLUMNS = (
    "run_id",
    "season",
    "cfbd_player_id",
    "player_name",
    "college_team",
    "position",
    "height",
    "weight",
    "hometown",
    "recruiting_year",
    "candidate_nwr_player_id",
    "candidate_sleeper_id",
    "match_confidence",
    "match_status",
    "review_note",
    "model_use_allowed",
    "training_allowed",
    "identity_review_required",
    "review_only",
)

PRODUCTION_COLUMNS = (
    "run_id",
    "season",
    "cfbd_player_id",
    "player_name",
    "college_team",
    "position",
    "stat_category",
    "games",
    "stat_1_name",
    "stat_1_value",
    "stat_2_name",
    "stat_2_value",
    "stat_3_name",
    "stat_3_value",
    "stat_4_name",
    "stat_4_value",
    "stat_5_name",
    "stat_5_value",
    "source_dataset",
    "identity_review_required",
    "model_use_allowed",
    "training_allowed",
    "review_only",
    "notes",
)

COVERAGE_COLUMNS = (
    "run_id",
    "dataset_name",
    "season",
    "row_count",
    "player_count",
    "team_count",
    "fields_present",
    "raw_cache_location",
    "tracked_artifact",
    "freshness",
    "gap_or_limitation",
    "notes",
    "model_use_allowed",
    "training_allowed",
    "identity_review_required",
    "review_only",
)

DICTIONARY_COLUMNS = (
    "dataset_name",
    "field_name",
    "field_type",
    "meaning",
    "model_use_status",
    "identity_review_required",
    "training_allowed",
    "review_only",
    "notes",
)


@dataclass(frozen=True)
class PullResult:
    dataset_name: str
    season: int
    endpoint_or_source: str
    raw_cache_location: Path
    rows: list[dict[str, Any]]
    refreshed: bool
    notes: str


class CfbdClient:
    def __init__(
        self,
        *,
        api_key: str,
        api_base: str,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def get_json(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        url = f"{self.api_base}{path}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "NinersWarRoom-CFBD-ReviewArtifacts/1.0",
            },
        )
        data: Any = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code != 429 or attempt >= self.max_retries:
                    raise
                time.sleep(_retry_after_seconds(exc, attempt))
        if not isinstance(data, list):
            raise ValueError(f"Expected list payload from {path}; got {type(data).__name__}.")
        return [row for row in data if isinstance(row, dict)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build review-only CFBD artifacts for NWR.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--secret-path", type=Path, default=DEFAULT_SECRET_PATH)
    parser.add_argument(
        "--api-base",
        default=os.environ.get("CFBD_API_BASE", "https://api.collegefootballdata.com"),
    )
    parser.add_argument("--delay-seconds", type=float, default=0.05)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    api_key = _read_cfbd_key(args.secret_path)
    client = CfbdClient(api_key=api_key, api_base=args.api_base, max_retries=args.max_retries)
    run_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = f"cfbd_review_artifacts_v1_20260624_{run_timestamp.replace(':', '').replace('-', '')}"
    raw_run_root = args.raw_root / run_id
    raw_run_root.mkdir(parents=True, exist_ok=True)
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    pulls: list[PullResult] = []
    teams_by_season: dict[int, list[dict[str, Any]]] = {}
    all_rosters: list[dict[str, Any]] = []
    all_stats: list[dict[str, Any]] = []
    optional_recruiting: list[dict[str, Any]] = []

    for season in SEASONS:
        teams = _pull_dataset(
            client,
            dataset_name="cfbd_teams_fbs",
            season=season,
            endpoint="/teams/fbs",
            params={"year": str(season)},
            raw_path=raw_run_root / "teams" / f"teams_fbs_{season}.json",
        )
        pulls.append(teams)
        teams_by_season[season] = teams.rows
        time.sleep(args.delay_seconds)

    for season in SEASONS:
        for category in STAT_CATEGORIES:
            result = _pull_dataset(
                client,
                dataset_name=f"cfbd_player_season_stats_{category}",
                season=season,
                endpoint="/stats/player/season",
                params={"year": str(season), "category": category},
                raw_path=raw_run_root / "player_stats" / str(season) / f"{category}.json",
            )
            pulls.append(result)
            all_stats.extend(result.rows)
            time.sleep(args.delay_seconds)

    for season in SEASONS:
        result = _pull_dataset(
            client,
            dataset_name="cfbd_recruiting_players_optional",
            season=season,
            endpoint="/recruiting/players",
            params={"year": str(season)},
            raw_path=raw_run_root / "recruiting" / f"recruiting_players_{season}.json",
        )
        pulls.append(result)
        optional_recruiting.extend(result.rows)
        time.sleep(args.delay_seconds)

    for season in SEASONS:
        season_rosters: list[dict[str, Any]] = []
        raw_dir = raw_run_root / "rosters" / str(season)
        for team in teams_by_season.get(season, []):
            school = str(team.get("school", "")).strip()
            if not school:
                continue
            try:
                rows = client.get_json("/roster", {"year": str(season), "team": school})
                _write_json(raw_dir / f"{_slug(school)}.json", rows)
                for row in rows:
                    row["_nwr_season"] = season
                season_rosters.extend(rows)
            except (OSError, urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
                _write_json(raw_dir / f"{_slug(school)}.error.json", _safe_error_metadata(exc))
            time.sleep(args.delay_seconds)
        all_rosters.extend(season_rosters)
        pulls.append(
            PullResult(
                dataset_name="cfbd_roster_player_identity",
                season=season,
                endpoint_or_source="/roster?year={season}&team={school}",
                raw_cache_location=raw_dir,
                rows=season_rosters,
                refreshed=True,
                notes="Team-scoped roster pull; all-roster query returned no rows in shape smoke.",
            )
        )

    identity_rows = build_identity_rows(run_id, all_rosters)
    production_rows = build_production_rows(run_id, all_stats)

    artifact_paths = {
        "manifest": args.artifact_dir / "cfbd_pull_manifest.csv",
        "identity": args.artifact_dir / "cfbd_player_identity_review_queue.csv",
        "production": args.artifact_dir / "cfbd_player_production_review.csv",
        "coverage": args.artifact_dir / "cfbd_coverage_report.csv",
        "dictionary": args.artifact_dir / "cfbd_data_dictionary.csv",
    }
    write_csv(artifact_paths["identity"], IDENTITY_COLUMNS, identity_rows)
    write_csv(artifact_paths["production"], PRODUCTION_COLUMNS, production_rows)
    coverage_rows = build_coverage_rows(
        run_id=run_id,
        pulls=pulls,
        artifact_dir=args.artifact_dir,
    )
    write_csv(artifact_paths["coverage"], COVERAGE_COLUMNS, coverage_rows)
    dictionary_rows = build_dictionary_rows()
    write_csv(artifact_paths["dictionary"], DICTIONARY_COLUMNS, dictionary_rows)
    manifest_rows = build_manifest_rows(
        run_id=run_id,
        run_timestamp=run_timestamp,
        pulls=pulls,
        artifact_dir=args.artifact_dir,
    )
    write_csv(artifact_paths["manifest"], MANIFEST_COLUMNS, manifest_rows)
    write_readme(
        artifact_dir=args.artifact_dir,
        run_id=run_id,
        run_timestamp=run_timestamp,
        pulls=pulls,
        identity_count=len(identity_rows),
        production_count=len(production_rows),
        recruiting_count=len(optional_recruiting),
        raw_run_root=raw_run_root,
    )

    print(
        json.dumps(
            {
                "run_id": run_id,
                "raw_cache_location": str(raw_run_root),
                "identity_rows": len(identity_rows),
                "production_rows": len(production_rows),
                "artifact_dir": str(args.artifact_dir),
            },
            sort_keys=True,
        )
    )
    return 0


def _read_cfbd_key(secret_path: Path) -> str:
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if key:
        return key
    file_key = secret_path.read_text(encoding="utf-8").strip() if secret_path.exists() else ""
    if not file_key:
        raise RuntimeError("CFBD API key is not configured.")
    return file_key


def _pull_dataset(
    client: CfbdClient,
    *,
    dataset_name: str,
    season: int,
    endpoint: str,
    params: dict[str, str],
    raw_path: Path,
) -> PullResult:
    try:
        rows = client.get_json(endpoint, params)
        _write_json(raw_path, rows)
        return PullResult(
            dataset_name=dataset_name,
            season=season,
            endpoint_or_source=f"{endpoint}?{urllib.parse.urlencode(params)}",
            raw_cache_location=raw_path,
            rows=rows,
            refreshed=True,
            notes="HTTP 200; raw payload cached outside git.",
        )
    except (OSError, urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
        _write_json(raw_path.with_suffix(".error.json"), _safe_error_metadata(exc))
        return PullResult(
            dataset_name=dataset_name,
            season=season,
            endpoint_or_source=f"{endpoint}?{urllib.parse.urlencode(params)}",
            raw_cache_location=raw_path.with_suffix(".error.json"),
            rows=[],
            refreshed=False,
            notes=f"Pull failed: {type(exc).__name__}.",
        )


def build_identity_rows(run_id: str, roster_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in roster_rows:
        season = _clean(row.get("_nwr_season"))
        player_id = _clean(row.get("id"))
        team = _clean(row.get("team"))
        key = (season, player_id, team)
        if key in seen:
            continue
        seen.add(key)
        first = _clean(row.get("firstName"))
        last = _clean(row.get("lastName"))
        player_name = " ".join(part for part in (first, last) if part).strip()
        output.append(
            {
                "run_id": run_id,
                "season": season,
                "cfbd_player_id": player_id,
                "player_name": player_name,
                "college_team": team,
                "position": _clean(row.get("position")),
                "height": _clean(row.get("height")),
                "weight": _clean(row.get("weight")),
                "hometown": _hometown(row),
                "recruiting_year": "",
                "candidate_nwr_player_id": "",
                "candidate_sleeper_id": "",
                "match_confidence": "",
                "match_status": "unmatched_review_required",
                "review_note": "Review-only CFBD roster identity; no automatic NWR/Sleeper match.",
                **GUARDRAILS,
            }
        )
    return output


def build_production_rows(run_id: str, stat_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in stat_rows:
        key = (
            _clean(row.get("season")),
            _clean(row.get("playerId")),
            _clean(row.get("player")),
            _clean(row.get("team")),
            _clean(row.get("position")),
            _clean(row.get("category")),
        )
        grouped[key].append(row)

    output: list[dict[str, str]] = []
    for (season, player_id, player, team, position, category), rows in sorted(grouped.items()):
        games = ""
        stats: list[tuple[str, str]] = []
        for row in sorted(rows, key=lambda item: _clean(item.get("statType"))):
            stat_name = _clean(row.get("statType"))
            stat_value = _clean(row.get("stat"))
            if stat_name.lower() in {"games", "g"}:
                games = stat_value
            elif stat_name:
                stats.append((stat_name, stat_value))
        record = {
            "run_id": run_id,
            "season": season,
            "cfbd_player_id": player_id,
            "player_name": player,
            "college_team": team,
            "position": position,
            "stat_category": category,
            "games": games,
        }
        for index in range(5):
            name, value = stats[index] if index < len(stats) else ("", "")
            slot = index + 1
            record[f"stat_{slot}_name"] = name
            record[f"stat_{slot}_value"] = value
        record.update(
            {
                "source_dataset": "cfbd_player_season_stats",
                "identity_review_required": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "review_only": "true",
                "notes": "Review-only college production; identity review required before any use.",
            }
        )
        output.append(record)
    return output


def build_manifest_rows(
    *,
    run_id: str,
    run_timestamp: str,
    pulls: list[PullResult],
    artifact_dir: Path,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pull in pulls:
        rows.append(
            {
                "run_id": run_id,
                "run_timestamp": run_timestamp,
                "dataset_name": pull.dataset_name,
                "season": str(pull.season),
                "endpoint_or_source": pull.endpoint_or_source,
                "action_type": "REFRESHED" if pull.refreshed else "FAILED",
                "refreshed": str(pull.refreshed).lower(),
                "raw_cache_location": str(pull.raw_cache_location),
                "tracked_artifact": _tracked_artifact_for_dataset(pull.dataset_name, artifact_dir),
                "row_count": str(len(pull.rows)),
                "freshness": f"refreshed {run_timestamp}" if pull.refreshed else "not refreshed",
                **GUARDRAILS,
                "notes": pull.notes,
            }
        )
    return rows


def build_coverage_rows(
    *,
    run_id: str,
    pulls: list[PullResult],
    artifact_dir: Path,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for pull in pulls:
        rows.append(
            {
                "run_id": run_id,
                "dataset_name": pull.dataset_name,
                "season": str(pull.season),
                "row_count": str(len(pull.rows)),
                "player_count": str(_distinct_count(pull.rows, ("id", "playerId", "athleteId"))),
                "team_count": str(_distinct_count(pull.rows, ("team", "school", "committedTo"))),
                "fields_present": ";".join(_fields_present(pull.rows)),
                "raw_cache_location": str(pull.raw_cache_location),
                "tracked_artifact": _tracked_artifact_for_dataset(pull.dataset_name, artifact_dir),
                "freshness": (
                    "current run cached outside git" if pull.refreshed else "not refreshed"
                ),
                "gap_or_limitation": _gap_for_pull(pull),
                "notes": pull.notes,
                **GUARDRAILS,
            }
        )
    return rows


def build_dictionary_rows() -> list[dict[str, str]]:
    meanings = {
        "run_id": "Unique CFBD review-artifact run identifier.",
        "run_timestamp": "UTC timestamp when the artifact run started.",
        "dataset_name": "Review dataset or raw endpoint grouping.",
        "season": "College football season for the row.",
        "endpoint_or_source": "CFBD endpoint path and query shape, without secrets.",
        "action_type": "Whether the dataset was refreshed or failed.",
        "refreshed": "Boolean refresh result for the dataset.",
        "raw_cache_location": (
            "Outside-git raw cache path under C:\\NWR_SHARED_DATA\\public_sources\\cfbd."
        ),
        "tracked_artifact": "Tracked review artifact derived from the raw payload.",
        "row_count": "Number of rows returned or produced.",
        "freshness": "Human-readable cache freshness for this run.",
        "model_use_allowed": "Always false; CFBD is not model input in this lane.",
        "training_allowed": "Always false; CFBD is not training input in this lane.",
        "identity_review_required": "Always true; player identities require manual review.",
        "review_only": "Always true; artifacts are for review and later matching only.",
        "notes": "Review notes and limitations.",
        "cfbd_player_id": "CFBD player or athlete identifier from the source payload.",
        "player_name": "Player name from CFBD roster or player stats.",
        "college_team": "College team reported by CFBD.",
        "position": "CFBD position value.",
        "height": "CFBD height value from roster where available.",
        "weight": "CFBD weight value from roster where available.",
        "hometown": "CFBD hometown fields combined for review.",
        "recruiting_year": "Reserved for reviewed recruiting linkage; blank in V1 roster rows.",
        "candidate_nwr_player_id": "Reserved manual candidate match to NWR identity.",
        "candidate_sleeper_id": "Reserved manual candidate match to Sleeper identity.",
        "match_confidence": "Reserved manual match confidence.",
        "match_status": "Identity review status for the row.",
        "review_note": "Identity review note.",
        "stat_category": "CFBD stat category such as passing, rushing, or receiving.",
        "games": "Games stat when present in CFBD statType values.",
        "source_dataset": "Source grouping used to derive the production review row.",
        "field_name": "Artifact field name.",
        "field_type": "Plain-text expected field type.",
        "meaning": "Field meaning for review users.",
        "model_use_status": "Review-only model-use status statement.",
    }
    datasets = {
        "cfbd_pull_manifest": MANIFEST_COLUMNS,
        "cfbd_player_identity_review_queue": IDENTITY_COLUMNS,
        "cfbd_player_production_review": PRODUCTION_COLUMNS,
        "cfbd_coverage_report": COVERAGE_COLUMNS,
        "cfbd_data_dictionary": DICTIONARY_COLUMNS,
    }
    rows: list[dict[str, str]] = []
    for dataset_name, columns in datasets.items():
        for field_name in columns:
            rows.append(
                {
                    "dataset_name": dataset_name,
                    "field_name": field_name,
                    "field_type": "string",
                    "meaning": meanings.get(field_name, "Review-only CFBD artifact field."),
                    "model_use_status": "model_use_allowed=false",
                    "identity_review_required": "true",
                    "training_allowed": "false",
                    "review_only": "true",
                    "notes": "Do not use for modeling, rankings, candidates, or training.",
                }
            )
    return rows


def write_readme(
    *,
    artifact_dir: Path,
    run_id: str,
    run_timestamp: str,
    pulls: list[PullResult],
    identity_count: int,
    production_count: int,
    recruiting_count: int,
    raw_run_root: Path,
) -> None:
    successful = [pull for pull in pulls if pull.refreshed]
    gaps = [pull for pull in pulls if "0 rows" in _gap_for_pull(pull) or not pull.refreshed]
    lines = [
        "# CFBD Review Artifacts V1 - 2026-06-24",
        "",
        f"Run ID: `{run_id}`",
        f"Run timestamp: `{run_timestamp}`",
        "",
        "These CFBD artifacts are review-only.",
        "",
        "- `model_use_allowed=false`",
        "- `training_allowed=false`",
        "- `identity_review_required=true`",
        "- `review_only=true`",
        "",
        "CFBD data is not model input yet. Player identity matching must be reviewed before use.",
        "Raw CFBD cache files are outside git under:",
        "",
        f"`{raw_run_root}`",
        "",
        "This lane is separate from nflverse and NFL data loader work. It does not promote CFBD",
        "data into rankings, candidates, source-truth files, model logic, or training inputs.",
        "",
        "## Artifacts",
        "",
        "- `cfbd_pull_manifest.csv`",
        "- `cfbd_player_identity_review_queue.csv`",
        "- `cfbd_player_production_review.csv`",
        "- `cfbd_coverage_report.csv`",
        "- `cfbd_data_dictionary.csv`",
        "",
        "## Coverage Summary",
        "",
        f"- Successful dataset-season pulls: {len(successful)} of {len(pulls)}",
        f"- Identity review rows: {identity_count}",
        f"- Production review rows: {production_count}",
        f"- Optional recruiting rows cached for coverage only: {recruiting_count}",
        "",
        "## Known Limitations",
        "",
        "- Roster identity is team-scoped because the all-roster query returned no rows in smoke.",
        "- 2026 roster and player-production availability depends on CFBD current-season coverage.",
        "- V1 does not automatically match CFBD players to NWR or Sleeper identities.",
        "- Optional recruiting data is cached and counted, but not promoted to a player-level",
        "  tracked recruiting artifact in V1.",
    ]
    if gaps:
        lines.extend(["", "## Missing Endpoints Or Seasons", ""])
        for pull in gaps:
            lines.append(f"- {pull.dataset_name} {pull.season}: {_gap_for_pull(pull)}")
    (artifact_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _retry_after_seconds(exc: urllib.error.HTTPError, attempt: int) -> float:
    header = exc.headers.get("Retry-After") if exc.headers else None
    if header:
        try:
            return min(float(header), 90.0)
        except ValueError:
            pass
    return min(10.0 * (attempt + 1), 60.0)


def _safe_error_metadata(exc: BaseException) -> dict[str, str]:
    metadata = {"error_class": type(exc).__name__}
    if isinstance(exc, urllib.error.HTTPError):
        metadata["http_status"] = str(exc.code)
        metadata["reason"] = _clean(exc.reason)
    return metadata


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _hometown(row: dict[str, Any]) -> str:
    parts = [
        _clean(row.get("homeCity")),
        _clean(row.get("homeState")),
        _clean(row.get("homeCountry")),
    ]
    return ", ".join(part for part in parts if part)


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return slug or "unknown"


def _fields_present(rows: list[dict[str, Any]]) -> list[str]:
    fields: set[str] = set()
    for row in rows:
        fields.update(key for key in row if not key.startswith("_nwr_"))
    return sorted(fields)


def _distinct_count(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> int:
    values: set[str] = set()
    for row in rows:
        for key in keys:
            value = _clean(row.get(key))
            if value:
                values.add(value)
                break
    return len(values)


def _tracked_artifact_for_dataset(dataset_name: str, artifact_dir: Path) -> str:
    if dataset_name == "cfbd_roster_player_identity":
        return str(artifact_dir / "cfbd_player_identity_review_queue.csv")
    if dataset_name.startswith("cfbd_player_season_stats"):
        return str(artifact_dir / "cfbd_player_production_review.csv")
    return str(artifact_dir / "cfbd_coverage_report.csv")


def _gap_for_pull(pull: PullResult) -> str:
    if not pull.refreshed:
        return "Dataset failed to refresh; see notes."
    if not pull.rows:
        return "0 rows returned by CFBD for this season/query."
    if pull.dataset_name == "cfbd_roster_player_identity":
        return "Roster rows require manual identity matching before any use."
    if pull.dataset_name.startswith("cfbd_player_season_stats"):
        return "Production rows are long-form source stats; identity review required."
    if pull.dataset_name == "cfbd_recruiting_players_optional":
        return "Optional V1 coverage only; no tracked recruiting detail artifact."
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
