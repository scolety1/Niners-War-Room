"""Fetch and validate DynastyProcess public data snapshots.

DynastyProcess is a GPL-3.0 public market data source. This connector caches
raw upstream files outside the repo by default and exposes only validated
snapshot metadata to downstream transforms.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

RAW_BASE_URL = "https://raw.githubusercontent.com/dynastyprocess/data"
GITHUB_COMMIT_API_URL = "https://api.github.com/repos/dynastyprocess/data/commits"
DEFAULT_BRANCH = "master"
DEFAULT_CACHE_ROOT = Path(r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess")
UPSTREAM_WORKFLOW_NAME = "weekly-playervalues"
UPSTREAM_EXPECTED_CRON = "23 2 * * 5"
UPSTREAM_EXPECTED_UTC = "Friday 02:23 UTC"
NWR_RECOMMENDED_PULL = "Friday 06:00 America/Denver"
NWR_BACKUP_RETRY = "Saturday morning America/Denver"
DEFAULT_FILE_NAMES = (
    "values.csv",
    "values-players.csv",
    "values-picks.csv",
    "db_playerids.csv",
    "db_fpecr_latest.csv",
)

REQUIRED_SCHEMAS: dict[str, frozenset[str]] = {
    "values.csv": frozenset(
        {
            "player",
            "pos",
            "team",
            "age",
            "draft_year",
            "ecr_1qb",
            "ecr_pos",
            "value_1qb",
            "scrape_date",
            "fp_id",
        }
    ),
    "values-players.csv": frozenset(
        {
            "player",
            "pos",
            "team",
            "age",
            "draft_year",
            "ecr_1qb",
            "ecr_pos",
            "value_1qb",
            "scrape_date",
            "fp_id",
        }
    ),
    "values-picks.csv": frozenset(
        {
            "player",
            "pos",
            "ecr_1qb",
            "ecr_2qb",
            "scrape_date",
            "pick",
        }
    ),
    "db_playerids.csv": frozenset(
        {
            "fantasypros_id",
            "sleeper_id",
            "gsis_id",
            "name",
            "position",
            "team",
            "birthdate",
            "age",
            "draft_year",
        }
    ),
    "db_fpecr_latest.csv": frozenset(
        {
            "fp_page",
            "page_type",
            "ecr_type",
            "player",
            "id",
            "pos",
            "team",
            "ecr",
            "scrape_date",
        }
    ),
}


class DynastyProcessSchemaError(RuntimeError):
    """Raised when an upstream DynastyProcess file changes schema."""


class DynastyProcessFetchError(RuntimeError):
    """Raised when an upstream DynastyProcess file cannot be fetched."""


@dataclass(frozen=True)
class HttpResponse:
    """Small response object used by the connector and tests."""

    body: bytes
    etag: str | None = None


class HttpClient(Protocol):
    """Minimal fetch interface for urllib and test doubles."""

    def fetch(self, url: str) -> HttpResponse:
        """Fetch a URL and return bytes plus optional cache metadata."""


class UrlLibHttpClient:
    """urllib-backed HTTP client with an explicit user agent."""

    def fetch(self, url: str) -> HttpResponse:
        request = Request(
            url,
            headers={"User-Agent": "NinersWarRoom-DynastyProcessConnector/1.0"},
        )
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310
                return HttpResponse(
                    body=response.read(),
                    etag=response.headers.get("ETag"),
                )
        except URLError as exc:
            raise DynastyProcessFetchError(f"Unable to fetch {url}: {exc}") from exc


@dataclass(frozen=True)
class FetchedFile:
    """Metadata for one cached upstream file."""

    file_name: str
    source_url: str
    cache_path: str
    fetched_at_utc: str
    sha256: str
    byte_count: int
    row_count: int
    scrape_date: str | None
    etag: str | None
    upstream_commit_sha: str | None
    upstream_commit_date: str | None


@dataclass(frozen=True)
class SnapshotResult:
    """Metadata for a complete DynastyProcess cache snapshot."""

    snapshot_dir: str
    metadata_path: str
    branch: str
    fetched_at_utc: str
    files: tuple[FetchedFile, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FreshnessMetadata:
    """Review metadata that prevents stale market context from looking current."""

    nwr_fetch_timestamp: str
    upstream_scrape_date: str
    upstream_latest_commit_sha: str
    upstream_latest_commit_timestamp: str
    upstream_workflow_name: str
    upstream_expected_cron: str
    local_cache_path: str
    derived_artifact_path: str
    freshness_status: str
    freshness_age_days: int | str
    previous_scrape_date: str
    previous_values_sha256: str
    current_values_sha256: str
    freshness_warning: str


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_raw_url(file_name: str, branch: str = DEFAULT_BRANCH) -> str:
    """Build a DynastyProcess raw GitHub URL for an explicit file name."""

    if not file_name or Path(file_name).name != file_name or "/" in file_name:
        raise ValueError(f"Unsafe DynastyProcess file name: {file_name!r}")
    return f"{RAW_BASE_URL}/{branch}/files/{file_name}"


def parse_upstream_cron_metadata() -> dict[str, str]:
    """Return the fixed upstream schedule metadata used by NWR refresh policy."""

    return {
        "upstream_workflow_name": UPSTREAM_WORKFLOW_NAME,
        "upstream_expected_cron": UPSTREAM_EXPECTED_CRON,
        "upstream_expected_utc": UPSTREAM_EXPECTED_UTC,
        "nwr_recommended_pull": NWR_RECOMMENDED_PULL,
        "nwr_backup_retry": NWR_BACKUP_RETRY,
    }


def validate_schema(headers: Iterable[str], file_name: str) -> None:
    """Validate the columns required for a supported upstream file."""

    required = REQUIRED_SCHEMAS.get(file_name)
    if required is None:
        raise ValueError(f"No DynastyProcess schema registered for {file_name!r}")
    present = {header.strip() for header in headers}
    missing = sorted(required - present)
    if missing:
        raise DynastyProcessSchemaError(
            f"DynastyProcess schema changed for {file_name}: missing {missing}"
        )


def _csv_metadata(body: bytes, file_name: str) -> tuple[int, str | None]:
    text = body.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise DynastyProcessSchemaError(f"{file_name} is not a CSV with headers")
    validate_schema(reader.fieldnames, file_name)
    row_count = 0
    scrape_dates: set[str] = set()
    for row in reader:
        row_count += 1
        scrape_date = (row.get("scrape_date") or "").strip()
        if scrape_date:
            scrape_dates.add(scrape_date)
    if len(scrape_dates) == 1:
        return row_count, next(iter(scrape_dates))
    if len(scrape_dates) > 1:
        return row_count, ";".join(sorted(scrape_dates))
    return row_count, None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def _file_metadata(snapshot: SnapshotResult, file_name: str) -> FetchedFile | None:
    for file_metadata in snapshot.files:
        if file_metadata.file_name == file_name:
            return file_metadata
    return None


def evaluate_freshness(
    snapshot: SnapshotResult | None,
    *,
    now_utc: datetime | None = None,
    previous_snapshot: SnapshotResult | None = None,
    fetch_failed: bool = False,
    derived_artifact_path: Path | str = "",
) -> FreshnessMetadata:
    """Evaluate NWR freshness status for a cached DynastyProcess snapshot."""

    if snapshot is None:
        return FreshnessMetadata(
            nwr_fetch_timestamp=_utc_now_iso(),
            upstream_scrape_date="",
            upstream_latest_commit_sha="",
            upstream_latest_commit_timestamp="",
            upstream_workflow_name=UPSTREAM_WORKFLOW_NAME,
            upstream_expected_cron=UPSTREAM_EXPECTED_CRON,
            local_cache_path="",
            derived_artifact_path=str(derived_artifact_path),
            freshness_status="RED_NO_VALID_CACHE",
            freshness_age_days="",
            previous_scrape_date="",
            previous_values_sha256="",
            current_values_sha256="",
            freshness_warning="Market baseline unavailable: no valid DynastyProcess cache.",
        )

    values_file = _file_metadata(snapshot, "values.csv") or _file_metadata(
        snapshot, "values-players.csv"
    )
    previous_values_file = (
        _file_metadata(previous_snapshot, "values.csv")
        if previous_snapshot is not None
        else None
    )
    now = now_utc or datetime.now(UTC)
    scrape_date = values_file.scrape_date if values_file else None
    scrape_datetime = _parse_date(scrape_date)
    age_days: int | str = ""
    if scrape_datetime is not None:
        age_days = (now.date() - scrape_datetime.date()).days

    previous_scrape_date = previous_values_file.scrape_date if previous_values_file else ""
    previous_sha = previous_values_file.sha256 if previous_values_file else ""
    current_sha = values_file.sha256 if values_file else ""
    commit_timestamp = values_file.upstream_commit_date if values_file else ""
    commit_datetime = _parse_date(commit_timestamp)
    commit_age_days: int | None = None
    if commit_datetime is not None:
        commit_age_days = (now.date() - commit_datetime.date()).days

    warning = ""
    if fetch_failed:
        status = "YELLOW_FETCH_FAILED_USING_LAST_CACHE"
        warning = "Market baseline stale risk: upstream fetch failed, using last local cache."
    elif isinstance(age_days, int) and age_days > 14:
        status = "RED_STALE"
        warning = "Market baseline stale: DynastyProcess scrape_date is older than 14 days."
    elif isinstance(age_days, int) and age_days > 8:
        status = "YELLOW_STALE"
        warning = "Market baseline stale: DynastyProcess scrape_date is older than 8 days."
    elif commit_age_days is not None and commit_age_days > 8:
        status = "YELLOW_STALE"
        warning = "Market baseline stale: upstream commit is older than expected weekly window."
    elif (
        scrape_date
        and previous_scrape_date
        and scrape_date == previous_scrape_date
        and current_sha
        and previous_sha
        and current_sha == previous_sha
    ):
        status = "GREEN_SAME_WEEK_NO_CHANGE"
    else:
        status = "GREEN_CURRENT"

    if status.startswith(("YELLOW", "RED")) and not warning:
        warning = "Market baseline stale: review freshness report before use."

    return FreshnessMetadata(
        nwr_fetch_timestamp=snapshot.fetched_at_utc,
        upstream_scrape_date=scrape_date or "",
        upstream_latest_commit_sha=values_file.upstream_commit_sha if values_file else "",
        upstream_latest_commit_timestamp=commit_timestamp or "",
        upstream_workflow_name=UPSTREAM_WORKFLOW_NAME,
        upstream_expected_cron=UPSTREAM_EXPECTED_CRON,
        local_cache_path=snapshot.snapshot_dir,
        derived_artifact_path=str(derived_artifact_path),
        freshness_status=status,
        freshness_age_days=age_days,
        previous_scrape_date=previous_scrape_date or "",
        previous_values_sha256=previous_sha,
        current_values_sha256=current_sha,
        freshness_warning=warning,
    )


class DynastyProcessConnector:
    """Fetch DynastyProcess files into an ignored local snapshot cache."""

    def __init__(
        self,
        cache_root: Path | str = DEFAULT_CACHE_ROOT,
        branch: str = DEFAULT_BRANCH,
        client: HttpClient | None = None,
    ) -> None:
        self.cache_root = Path(cache_root)
        self.branch = branch
        self.client = client or UrlLibHttpClient()

    def fetch_snapshot(
        self,
        file_names: Iterable[str] = DEFAULT_FILE_NAMES,
        snapshot_label: str | None = None,
    ) -> SnapshotResult:
        """Fetch explicit files and write snapshot metadata."""

        fetched_at = _utc_now_iso()
        label = snapshot_label or datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        snapshot_dir = self.cache_root / label
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        warnings: list[str] = []
        commit_sha, commit_date = self._fetch_commit_metadata(warnings)
        fetched_files: list[FetchedFile] = []
        for file_name in file_names:
            fetched_files.append(
                self._fetch_one(
                    file_name=file_name,
                    snapshot_dir=snapshot_dir,
                    fetched_at=fetched_at,
                    upstream_commit_sha=commit_sha,
                    upstream_commit_date=commit_date,
                )
            )

        metadata_path = snapshot_dir / "snapshot_metadata.json"
        result = SnapshotResult(
            snapshot_dir=str(snapshot_dir),
            metadata_path=str(metadata_path),
            branch=self.branch,
            fetched_at_utc=fetched_at,
            files=tuple(fetched_files),
            warnings=tuple(warnings),
        )
        metadata_path.write_text(
            json.dumps(asdict(result), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return result

    def _fetch_one(
        self,
        file_name: str,
        snapshot_dir: Path,
        fetched_at: str,
        upstream_commit_sha: str | None,
        upstream_commit_date: str | None,
    ) -> FetchedFile:
        source_url = build_raw_url(file_name, self.branch)
        response = self.client.fetch(source_url)
        row_count, scrape_date = _csv_metadata(response.body, file_name)
        digest = hashlib.sha256(response.body).hexdigest()
        cache_path = snapshot_dir / file_name
        cache_path.write_bytes(response.body)
        return FetchedFile(
            file_name=file_name,
            source_url=source_url,
            cache_path=str(cache_path),
            fetched_at_utc=fetched_at,
            sha256=digest,
            byte_count=len(response.body),
            row_count=row_count,
            scrape_date=scrape_date,
            etag=response.etag,
            upstream_commit_sha=upstream_commit_sha,
            upstream_commit_date=upstream_commit_date,
        )

    def _fetch_commit_metadata(
        self, warnings: list[str]
    ) -> tuple[str | None, str | None]:
        url = f"{GITHUB_COMMIT_API_URL}/{self.branch}"
        try:
            response = self.client.fetch(url)
            payload = json.loads(response.body.decode("utf-8"))
        except (DynastyProcessFetchError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            warnings.append(f"YELLOW: unable to record upstream commit metadata: {exc}")
            return None, None

        commit_sha = payload.get("sha")
        commit_date = (
            payload.get("commit", {})
            .get("committer", {})
            .get("date")
        )
        return commit_sha, commit_date


def read_snapshot_metadata(metadata_path: Path | str) -> SnapshotResult:
    """Load snapshot metadata written by DynastyProcessConnector."""

    payload = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    files = tuple(FetchedFile(**file_payload) for file_payload in payload["files"])
    return SnapshotResult(
        snapshot_dir=payload["snapshot_dir"],
        metadata_path=payload["metadata_path"],
        branch=payload["branch"],
        fetched_at_utc=payload["fetched_at_utc"],
        files=files,
        warnings=tuple(payload.get("warnings", ())),
    )


def iter_cached_snapshots(
    cache_root: Path | str = DEFAULT_CACHE_ROOT,
) -> tuple[SnapshotResult, ...]:
    """Load valid cached DynastyProcess snapshots, newest first."""

    root = Path(cache_root)
    if not root.exists():
        return ()
    snapshots: list[SnapshotResult] = []
    for metadata_path in root.glob("*/snapshot_metadata.json"):
        try:
            snapshots.append(read_snapshot_metadata(metadata_path))
        except (KeyError, TypeError, json.JSONDecodeError, OSError):
            continue
    return tuple(
        sorted(
            snapshots,
            key=lambda snapshot: snapshot.fetched_at_utc,
            reverse=True,
        )
    )


def latest_cached_snapshot(
    cache_root: Path | str = DEFAULT_CACHE_ROOT,
    *,
    exclude_snapshot_dir: Path | str | None = None,
) -> SnapshotResult | None:
    """Return the newest usable local cache metadata, optionally excluding one path."""

    excluded = str(Path(exclude_snapshot_dir)) if exclude_snapshot_dir is not None else None
    for snapshot in iter_cached_snapshots(cache_root):
        if excluded is None or str(Path(snapshot.snapshot_dir)) != excluded:
            return snapshot
    return None
