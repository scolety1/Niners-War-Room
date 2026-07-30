"""Acquire immutable official nflverse release snapshots through nflreadpy 0.1.5.

Raw release bytes are written only to the governed external snapshot root. Git
receives a small snapshot-set receipt containing relative references, hashes,
schemas, and terms decisions. Existing admitted snapshots are never modified.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services import new_evidence_foundation_service as foundation  # noqa: E402

DEFAULT_SNAPSHOT_ROOT = Path(r"C:\NWR_SHARED_DATA\source_snapshots")
DEFAULT_CATALOG = ROOT / "config" / "nwr_new_evidence_snapshot_set_v1.json"
DEFAULT_SEASONS = tuple(range(2012, 2026))
PARTICIPATION_SEASONS = tuple(range(2016, 2026))
MAX_REQUESTS = 160

LICENSE_URL = "https://github.com/nflverse/nflverse-data/blob/master/LICENSE.md"
NFLREADPY_LICENSE_URL = "https://github.com/nflverse/nflreadpy/blob/v0.1.5/LICENSE"


@dataclass(frozen=True)
class DatasetSpec:
    dataset: str
    release: str
    path_template: str
    seasons: tuple[int, ...] | None
    license_spdx: str = "CC-BY-4.0"
    terms_note: str = "Credit nflverse; preserve source attribution."
    data_dictionary_url: str = ""
    temporal_rule: str = ""


DATASETS = (
    DatasetSpec(
        "players",
        "players",
        "players/players",
        None,
        data_dictionary_url="https://nflreadr.nflverse.com/articles/dictionary_players.html",
        temporal_rule=(
            "stable identity and historical draft facts only; mutable/current player fields "
            "are current-only"
        ),
    ),
    DatasetSpec(
        "draft_picks",
        "draft_picks",
        "draft_picks/draft_picks",
        None,
        data_dictionary_url=(
            "https://nflreadr.nflverse.com/articles/dictionary_draft_picks.html"
        ),
        temporal_rule="draft fact available only after the applicable NFL draft selection",
    ),
    DatasetSpec(
        "combine",
        "combine",
        "combine/combine",
        None,
        data_dictionary_url="https://nflreadr.nflverse.com/articles/dictionary_combine.html",
        temporal_rule="measurement available only after the applicable combine event",
    ),
    DatasetSpec(
        "seasonal_rosters",
        "rosters",
        "rosters/roster_{season}",
        DEFAULT_SEASONS,
        data_dictionary_url="https://nflreadr.nflverse.com/articles/dictionary_rosters.html",
        temporal_rule="season roster fact available after its recorded season snapshot",
    ),
    DatasetSpec(
        "weekly_rosters",
        "weekly_rosters",
        "weekly_rosters/roster_weekly_{season}",
        DEFAULT_SEASONS,
        data_dictionary_url=(
            "https://nflreadr.nflverse.com/articles/dictionary_roster_status.html"
        ),
        temporal_rule="week roster/status fact available after its recorded week",
    ),
    DatasetSpec(
        "player_stats_seasonal",
        "stats_player",
        "stats_player/stats_player_reg_{season}",
        DEFAULT_SEASONS,
        data_dictionary_url=(
            "https://nflreadr.nflverse.com/articles/dictionary_player_stats.html"
        ),
        temporal_rule="regular-season total available after the completed regular season",
    ),
    DatasetSpec(
        "player_stats_weekly",
        "stats_player",
        "stats_player/stats_player_week_{season}",
        DEFAULT_SEASONS,
        data_dictionary_url=(
            "https://nflreadr.nflverse.com/articles/dictionary_player_stats.html"
        ),
        temporal_rule="week statistic available only after the applicable game",
    ),
    DatasetSpec(
        "snap_counts",
        "snap_counts",
        "snap_counts/snap_counts_{season}",
        DEFAULT_SEASONS,
        data_dictionary_url=(
            "https://nflreadr.nflverse.com/articles/dictionary_snap_counts.html"
        ),
        temporal_rule="week snap count available only after the applicable game",
    ),
    DatasetSpec(
        "participation",
        "pbp_participation",
        "pbp_participation/pbp_participation_{season}",
        PARTICIPATION_SEASONS,
        license_spdx="CC-BY-SA-4.0",
        terms_note="Credit FTN Data via nflverse; share adaptations under CC-BY-SA-4.0.",
        data_dictionary_url=(
            "https://nflreadr.nflverse.com/articles/dictionary_participation.html"
        ),
        temporal_rule=(
            "historical participation release is available after season-end publication; "
            "not a same-week historical feature"
        ),
    ),
    DatasetSpec(
        "depth_charts",
        "depth_charts",
        "depth_charts/depth_charts_{season}",
        DEFAULT_SEASONS,
        data_dictionary_url=(
            "https://nflreadr.nflverse.com/articles/dictionary_depth_charts.html"
        ),
        temporal_rule="depth status available only after the source date/timestamp",
    ),
    DatasetSpec(
        "injuries",
        "injuries",
        "injuries/injuries_{season}",
        DEFAULT_SEASONS,
        data_dictionary_url="https://nflreadr.nflverse.com/articles/dictionary_injuries.html",
        temporal_rule="injury/practice status available only after the applicable report",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT_ROOT)
    parser.add_argument("--catalog-output", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--retrieval-label",
        help="Fixed YYYYMMDDTHHMMSSZ label. Defaults to the actual UTC retrieval start.",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=[spec.dataset for spec in DATASETS],
        default=[spec.dataset for spec in DATASETS],
    )
    parser.add_argument(
        "--skip-client-archive",
        action="store_true",
        help="Do not acquire the official nflreadpy v0.1.5 source tag archive.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    version = importlib.metadata.version("nflreadpy")
    if version != foundation.NFLREADPY_VERSION:
        raise foundation.SourceAdmissionError(
            f"nflreadpy version must be {foundation.NFLREADPY_VERSION}, got {version}"
        )

    retrieval = args.retrieval_label or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    retrieved_at = datetime.strptime(retrieval, "%Y%m%dT%H%M%SZ").replace(
        tzinfo=UTC
    ).isoformat().replace("+00:00", "Z")
    snapshot_root = args.snapshot_root.resolve()
    snapshot_root.mkdir(parents=True, exist_ok=True)

    selected = [spec for spec in DATASETS if spec.dataset in set(args.datasets)]
    request_count = sum(len(spec.seasons or (None,)) for spec in selected)
    request_count += 0 if args.skip_client_archive else 1
    foundation.enforce_request_limit(request_count, MAX_REQUESTS)

    from nflreadpy.config import DataFormat, update_config  # noqa: PLC0415
    from nflreadpy.downloader import get_downloader  # noqa: PLC0415

    update_config(cache_mode="off", verbose=False, timeout=120)
    downloader = get_downloader()
    downloader.session.headers.update(
        {
            "User-Agent": f"NWR-New-Evidence-Foundation-V1 nflreadpy/{version}",
            "Accept": "application/octet-stream",
        }
    )

    catalog_entries: list[dict[str, Any]] = []
    for spec in selected:
        entry = _acquire_dataset(
            spec=spec,
            snapshot_root=snapshot_root,
            retrieval=retrieval,
            retrieved_at=retrieved_at,
            downloader=downloader,
            data_format=DataFormat.PARQUET,
            package_version=version,
        )
        catalog_entries.append(entry)
        print(
            f"{spec.dataset}: {entry['admission_status']} "
            f"assets={entry['downloaded_assets']}/{entry['attempted_assets']}"
        )

    client_entry: dict[str, Any] | None = None
    if not args.skip_client_archive:
        client_entry = _acquire_client_archive(
            snapshot_root=snapshot_root,
            retrieval=retrieval,
            retrieved_at=retrieved_at,
            session=downloader.session,
            package_version=version,
        )
        print(
            "nflreadpy_client: "
            f"{client_entry['admission_status']} sha256={client_entry['aggregate_sha256']}"
        )

    catalog = {
        "schema_version": 1,
        "foundation_id": "NWR_NEW_EVIDENCE_FOUNDATION_V1",
        "retrieved_at_utc": retrieved_at,
        "snapshot_root_contract": "SOURCE_SNAPSHOT_ROOT",
        "package": {
            "name": "nflreadpy",
            "version": version,
            "official_release": (
                "https://github.com/nflverse/nflreadpy/releases/tag/v0.1.5"
            ),
            "source_archive_sha256": (
                client_entry["aggregate_sha256"] if client_entry else ""
            ),
        },
        "request_count": request_count,
        "datasets": sorted(catalog_entries, key=lambda row: row["dataset"]),
        "client_source": client_entry or {},
        "cfbd_live_requests": 0,
    }
    body = _json_bytes(catalog)
    foundation.require_no_secret(body.decode("utf-8"))
    args.catalog_output.parent.mkdir(parents=True, exist_ok=True)
    args.catalog_output.write_bytes(body)
    print(f"catalog={args.catalog_output}")
    print(f"requests={request_count}")
    return 0


def _acquire_dataset(
    *,
    spec: DatasetSpec,
    snapshot_root: Path,
    retrieval: str,
    retrieved_at: str,
    downloader: Any,
    data_format: Any,
    package_version: str,
) -> dict[str, Any]:
    dataset_root = snapshot_root / "nflverse" / spec.dataset
    dataset_root.mkdir(parents=True, exist_ok=True)
    pending = dataset_root / f".pending-{retrieval}"
    if pending.exists():
        raise foundation.SourceAdmissionError(f"pending snapshot already exists: {pending}")
    pending.mkdir()
    raw_root = pending / "raw"
    raw_root.mkdir()
    assets: list[dict[str, Any]] = []
    try:
        for season in spec.seasons or (None,):
            path = spec.path_template.format(season=season)
            url = downloader._build_url("nflverse-data", path, data_format)
            foundation.require_official_url(url)
            response = downloader.session.get(
                url,
                timeout=120,
                stream=False,
                allow_redirects=True,
            )
            status_code = int(response.status_code)
            if status_code == 404:
                assets.append(
                    {
                        "season": season if season is not None else "",
                        "status": "not_available",
                        "http_status": status_code,
                        "source_url": url,
                        "final_url": str(response.url),
                        "relative_path": "",
                        "bytes": 0,
                        "sha256": "",
                        "rows": 0,
                        "columns": 0,
                        "schema_fingerprint": "",
                        "schema": [],
                        "response_headers": _safe_headers(response.headers),
                    }
                )
                continue
            response.raise_for_status()
            foundation.require_official_url(str(response.url), final=True)
            body = response.content
            file_name = f"{spec.dataset}_{season}.parquet" if season else f"{spec.dataset}.parquet"
            relative = Path("raw") / file_name
            output = pending / relative
            output.write_bytes(body)
            frame = pl.read_parquet(body)
            schema = [
                {"name": name, "dtype": str(dtype)}
                for name, dtype in frame.schema.items()
            ]
            fingerprint = foundation.sha256_bytes(
                json.dumps(
                    schema,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            assets.append(
                {
                    "season": season if season is not None else "",
                    "status": "downloaded",
                    "http_status": status_code,
                    "source_url": url,
                    "final_url": str(response.url),
                    "relative_path": relative.as_posix(),
                    "bytes": len(body),
                    "sha256": foundation.sha256_bytes(body),
                    "rows": frame.height,
                    "columns": frame.width,
                    "schema_fingerprint": fingerprint,
                    "schema": schema,
                    "response_headers": _safe_headers(response.headers),
                }
            )
            print(
                f"  {spec.dataset} season={season or 'all'} rows={frame.height} "
                f"bytes={len(body)}"
            )

        downloaded = [asset for asset in assets if asset["status"] == "downloaded"]
        aggregate = foundation.sha256_bytes(
            "".join(asset["sha256"] for asset in downloaded).encode("ascii")
        )
        snapshot_id = f"{retrieval}-{aggregate[:12]}"
        final = dataset_root / snapshot_id
        if final.exists():
            raise foundation.SourceAdmissionError(
                f"immutable snapshot already exists: {final}"
            )
        admission_status = _admission_status(spec.dataset, assets)
        manifest = {
            "schema_version": 1,
            "provider": "nflverse",
            "dataset": spec.dataset,
            "snapshot_id": snapshot_id,
            "retrieved_at_utc": retrieved_at,
            "package_name": "nflreadpy",
            "package_version": package_version,
            "source_release": spec.release,
            "source_repository": "https://github.com/nflverse/nflverse-data",
            "data_dictionary_url": spec.data_dictionary_url,
            "license_spdx": spec.license_spdx,
            "license_url": LICENSE_URL,
            "license_terms_note": spec.terms_note,
            "temporal_availability_rule": spec.temporal_rule,
            "upstream_update_behavior": (
                "rolling GitHub release tag may update; this local snapshot is immutable"
            ),
            "request_parameters": {
                "seasons": list(spec.seasons or []),
                "format": "parquet",
            },
            "admission_status": admission_status,
            "aggregate_sha256": aggregate,
            "immutable": True,
            "complete": True,
            "assets": assets,
        }
        (pending / "LICENSE_TERMS_RECEIPT.json").write_bytes(
            _json_bytes(
                {
                    "license_spdx": spec.license_spdx,
                    "license_url": LICENSE_URL,
                    "terms_note": spec.terms_note,
                    "review_result": (
                        "TERMS_ACCEPTED_FOR_RESEARCH_WITH_ATTRIBUTION"
                    ),
                }
            )
        )
        (pending / "COMPLETION_MANIFEST.json").write_bytes(_json_bytes(manifest))
        pending.rename(final)
        _mark_read_only(final)
        return {
            "dataset": spec.dataset,
            "snapshot_id": snapshot_id,
            "manifest_relative_path": (
                f"nflverse/{spec.dataset}/{snapshot_id}/COMPLETION_MANIFEST.json"
            ),
            "aggregate_sha256": aggregate,
            "admission_status": admission_status,
            "attempted_assets": len(assets),
            "downloaded_assets": len(downloaded),
            "rows": sum(int(asset["rows"]) for asset in downloaded),
            "seasons_downloaded": [
                int(asset["season"])
                for asset in downloaded
                if str(asset["season"]).strip()
            ],
            "seasons_unavailable": [
                int(asset["season"])
                for asset in assets
                if asset["status"] != "downloaded" and str(asset["season"]).strip()
            ],
            "license_spdx": spec.license_spdx,
            "temporal_availability_rule": spec.temporal_rule,
        }
    except Exception:
        if pending.exists():
            shutil.rmtree(pending)
        raise


def _acquire_client_archive(
    *,
    snapshot_root: Path,
    retrieval: str,
    retrieved_at: str,
    session: Any,
    package_version: str,
) -> dict[str, Any]:
    dataset = "nflreadpy_client"
    url = "https://github.com/nflverse/nflreadpy/archive/refs/tags/v0.1.5.zip"
    foundation.require_official_url(url)
    response = session.get(url, timeout=120, allow_redirects=True)
    response.raise_for_status()
    foundation.require_official_url(str(response.url), final=True)
    body = response.content
    aggregate = foundation.sha256_bytes(body)
    snapshot_id = f"{retrieval}-{aggregate[:12]}"
    final = snapshot_root / "nflverse" / dataset / snapshot_id
    if final.exists():
        raise foundation.SourceAdmissionError(f"immutable snapshot already exists: {final}")
    final.mkdir(parents=True)
    (final / "raw").mkdir()
    (final / "raw" / "nflreadpy-v0.1.5.zip").write_bytes(body)
    manifest = {
        "schema_version": 1,
        "provider": "nflverse",
        "dataset": dataset,
        "snapshot_id": snapshot_id,
        "retrieved_at_utc": retrieved_at,
        "package_name": "nflreadpy",
        "package_version": package_version,
        "source_release": "v0.1.5",
        "source_repository": "https://github.com/nflverse/nflreadpy",
        "data_dictionary_url": "",
        "license_spdx": "MIT",
        "license_url": NFLREADPY_LICENSE_URL,
        "license_terms_note": "Official nflreadpy client source archive.",
        "temporal_availability_rule": "client build-time dependency",
        "upstream_update_behavior": "immutable Git tag archive",
        "request_parameters": {},
        "admission_status": "ADMITTED_PRIMARY_SOURCE",
        "aggregate_sha256": aggregate,
        "immutable": True,
        "complete": True,
        "assets": [
            {
                "season": "",
                "status": "downloaded",
                "http_status": int(response.status_code),
                "source_url": url,
                "final_url": str(response.url),
                "relative_path": "raw/nflreadpy-v0.1.5.zip",
                "bytes": len(body),
                "sha256": aggregate,
                "rows": 0,
                "columns": 0,
                "schema_fingerprint": "",
                "schema": [],
                "response_headers": _safe_headers(response.headers),
            }
        ],
    }
    (final / "LICENSE_TERMS_RECEIPT.json").write_bytes(
        _json_bytes(
            {
                "license_spdx": "MIT",
                "license_url": NFLREADPY_LICENSE_URL,
                "review_result": "TERMS_ACCEPTED_FOR_CLIENT_USE",
            }
        )
    )
    (final / "COMPLETION_MANIFEST.json").write_bytes(_json_bytes(manifest))
    _mark_read_only(final)
    return {
        "dataset": dataset,
        "snapshot_id": snapshot_id,
        "manifest_relative_path": (
            f"nflverse/{dataset}/{snapshot_id}/COMPLETION_MANIFEST.json"
        ),
        "aggregate_sha256": aggregate,
        "admission_status": "ADMITTED_PRIMARY_SOURCE",
        "attempted_assets": 1,
        "downloaded_assets": 1,
        "rows": 0,
        "seasons_downloaded": [],
        "seasons_unavailable": [],
        "license_spdx": "MIT",
        "temporal_availability_rule": "client build-time dependency",
    }


def _admission_status(dataset: str, assets: list[dict[str, Any]]) -> str:
    downloaded = [asset for asset in assets if asset["status"] == "downloaded"]
    if not downloaded:
        return "NOT_ENOUGH_INFORMATION"
    if len(downloaded) != len(assets):
        return "ADMITTED_WITH_COVERAGE_LIMIT"
    if dataset in {
        "seasonal_rosters",
        "weekly_rosters",
        "snap_counts",
        "participation",
        "depth_charts",
        "injuries",
    }:
        return "ADMITTED_WITH_COVERAGE_LIMIT"
    return "ADMITTED_PRIMARY_SOURCE"


def _safe_headers(headers: Any) -> dict[str, str]:
    allowed = (
        "content-length",
        "content-type",
        "etag",
        "last-modified",
        "x-github-request-id",
    )
    return {
        name: str(headers.get(name, ""))
        for name in allowed
        if str(headers.get(name, ""))
    }


def _json_bytes(document: Any) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _mark_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            os.chmod(path, 0o444)
    os.chmod(root, 0o555)


if __name__ == "__main__":
    raise SystemExit(main())
