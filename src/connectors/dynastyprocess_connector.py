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


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_raw_url(file_name: str, branch: str = DEFAULT_BRANCH) -> str:
    """Build a DynastyProcess raw GitHub URL for an explicit file name."""

    if not file_name or Path(file_name).name != file_name or "/" in file_name:
        raise ValueError(f"Unsafe DynastyProcess file name: {file_name!r}")
    return f"{RAW_BASE_URL}/{branch}/files/{file_name}"


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
