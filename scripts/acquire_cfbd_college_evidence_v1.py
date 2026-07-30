"""Acquire the smallest governed CFBD REST v2 college-evidence snapshot.

The caller must bridge the Windows user-level ``CFBD_BEARER_TOKEN`` into this
process. The token is read only from the process environment and is never
written to an artifact, URL, exception, or receipt.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services import cfbd_official_v2_adapter as cfbd  # noqa: E402
from src.services import new_evidence_foundation_service as foundation  # noqa: E402

DEFAULT_SNAPSHOT_ROOT = Path(r"C:\NWR_SHARED_DATA\source_snapshots")
DEFAULT_CATALOG = ROOT / "config" / "nwr_cfbd_college_evidence_snapshot_v1.json"
OPENAPI_PATH = "/api-docs.json"
TERMS_URL = "https://collegefootballdata.com/terms"
DRAFT_YEARS = tuple(range(2012, 2027))
COLLEGE_YEARS = tuple(range(2011, 2026))
DATA_REQUEST_COUNT = len(DRAFT_YEARS) + 3 * len(COLLEGE_YEARS)
TOTAL_AUTHENTICATED_REQUESTS = DATA_REQUEST_COUNT + 2
REQUIRED_PATHS = {
    "/draft/picks": "DraftPick",
    "/stats/player/season": "PlayerStat",
    "/player/usage": "PlayerUsage",
    "/ppa/players/season": "PlayerSeasonPredictedPointsAdded",
    "/info": "UserInfo",
    "/info/usage": "UserUsage",
}
TEMPORAL_RULES = {
    "draft_picks": (
        "NFL draft fact and collegeAthleteId are available only after the "
        "applicable selection; used for identity, never as pre-draft evidence"
    ),
    "player_season_stats": (
        "season aggregate is eligible only after the player's final game and "
        "only where college season <= NFL draft year - 1"
    ),
    "player_usage": (
        "season aggregate is eligible only after the player's final game and "
        "only where college season <= NFL draft year - 1"
    ),
    "player_ppa": (
        "season aggregate is eligible only after the player's final game and "
        "only where college season <= NFL draft year - 1"
    ),
}


class AcquisitionError(RuntimeError):
    """Fail-closed CFBD acquisition error."""


@dataclass(frozen=True)
class HttpResult:
    status: int
    url: str
    body: bytes
    headers: dict[str, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT_ROOT)
    parser.add_argument("--catalog-output", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--retrieval-label",
        help="Fixed YYYYMMDDTHHMMSSZ label; defaults to the UTC retrieval start.",
    )
    return parser.parse_args()


def _safe_headers(headers: Any) -> dict[str, str]:
    allowed = ("content-length", "content-type", "date", "etag", "last-modified")
    return {
        name: str(headers.get(name, ""))
        for name in allowed
        if str(headers.get(name, ""))
    }


def _get(url: str, *, authenticated: bool) -> HttpResult:
    headers = {
        "Accept": "application/json",
        "User-Agent": "NWR-CFBD-College-Evidence-Admission-V1",
    }
    if authenticated:
        headers["Authorization"] = f"Bearer {cfbd.token_from_environment()}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return HttpResult(
                status=int(response.status),
                url=str(response.url),
                body=body,
                headers=_safe_headers(response.headers),
            )
    except urllib.error.HTTPError as exc:
        raise AcquisitionError(
            f"official CFBD request failed with HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise AcquisitionError("official CFBD request failed") from exc


def _json(result: HttpResult) -> Any:
    if result.status != 200:
        raise AcquisitionError(f"unexpected HTTP status {result.status}")
    try:
        return json.loads(result.body)
    except json.JSONDecodeError as exc:
        raise AcquisitionError("official CFBD response is not valid JSON") from exc


def _validate_authority(openapi: dict[str, Any], terms_text: str) -> dict[str, Any]:
    info = openapi.get("info", {})
    servers = {str(item.get("url", "")).rstrip("/") for item in openapi.get("servers", [])}
    if info.get("title") != "College Football Data API":
        raise cfbd.CfbdSchemaDriftError("official API title drift")
    version = str(info.get("version", ""))
    if not re.fullmatch(r"5\.\d+\.\d+", version):
        raise cfbd.CfbdSchemaDriftError(f"unsupported official API version: {version}")
    if cfbd.CFBD_BASE_URL not in servers:
        raise cfbd.CfbdSchemaDriftError("official REST v2 server authority drift")
    schemas = openapi.get("components", {}).get("schemas", {})
    for path, schema_name in REQUIRED_PATHS.items():
        if "get" not in openapi.get("paths", {}).get(path, {}):
            raise cfbd.CfbdSchemaDriftError(f"required v2 endpoint missing: {path}")
        if schema_name not in schemas:
            raise cfbd.CfbdSchemaDriftError(f"required v2 schema missing: {schema_name}")
    # The current Nuxt page ships a client-rendered shell. Preserve its exact
    # bytes and require official page identity here; the substantive clauses
    # are recorded from the independent rendered-page review in the receipt.
    if (
        "<title>CollegeFootballData.com</title>" not in terms_text
        or "/_nuxt/" not in terms_text
        or len(terms_text) < 1000
    ):
        raise AcquisitionError("official terms page identity drift")
    return {
        "api_title": info["title"],
        "api_version": version,
        "openapi_version": str(openapi.get("openapi", "")),
        "server": cfbd.CFBD_BASE_URL,
        "terms_effective_date": "2025-07-01",
        "terms_text_review": "INDEPENDENT_RENDERED_OFFICIAL_PAGE_REVIEW_2026-07-30",
    }


def _required_fields(openapi: dict[str, Any], schema_name: str) -> set[str]:
    return set(
        openapi.get("components", {})
        .get("schemas", {})
        .get(schema_name, {})
        .get("required", [])
    )


def _validate_rows(rows: Any, *, required: set[str], label: str) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise cfbd.CfbdSchemaDriftError(f"{label} response is not an array")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise cfbd.CfbdSchemaDriftError(f"{label} row {index} is not an object")
        missing = sorted(required - set(row))
        if missing:
            raise cfbd.CfbdSchemaDriftError(
                f"{label} row {index} missing required fields: {missing}"
            )
    return rows


def _schema_fingerprint(rows: list[dict[str, Any]]) -> str:
    fields = sorted({key for row in rows for key in row})
    return foundation.sha256_bytes(
        json.dumps(fields, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


def _write_asset(
    *,
    pending: Path,
    relative_path: Path,
    result: HttpResult,
    endpoint: str,
    parameters: dict[str, Any],
    rows: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise AcquisitionError("unsafe snapshot relative path")
    output = pending / relative_path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result.body)
    return {
        "endpoint": endpoint,
        "parameters": parameters,
        "relative_path": relative_path.as_posix(),
        "source_url": cfbd.CFBD_BASE_URL + endpoint if endpoint.startswith("/") else endpoint,
        "http_status": result.status,
        "bytes": len(result.body),
        "sha256": foundation.sha256_bytes(result.body),
        "rows": len(rows) if rows is not None else 0,
        "schema_fingerprint": _schema_fingerprint(rows) if rows is not None else "",
        "response_headers": result.headers,
    }


def _redacted_info(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "tier_name": str(document.get("tierName", "")),
        "patron_level": int(document.get("patronLevel", 0)),
        "monthly_limit": int(document.get("monthlyLimit", 0)),
        "used_calls": int(document.get("usedCalls", 0)),
        "remaining_calls": int(document.get("remainingCalls", 0)),
        "reset_at": str(document.get("resetAt", "")),
        "shared_pool": bool(document.get("sharedPool", False)),
        "enabled_features": sorted(
            key for key, value in document.get("features", {}).items() if value
        ),
    }


def main() -> int:
    args = parse_args()
    token = cfbd.token_from_environment()
    retrieval = args.retrieval_label or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    retrieved_at = datetime.strptime(retrieval, "%Y%m%dT%H%M%SZ").replace(
        tzinfo=UTC
    ).isoformat().replace("+00:00", "Z")

    before = _redacted_info(_json(_get(cfbd.build_url("/info"), authenticated=True)))
    cfbd.validate_request_plan(
        planned_calls=TOTAL_AUTHENTICATED_REQUESTS,
        remaining_calls=before["remaining_calls"],
    )
    if before["monthly_limit"] <= 0:
        raise cfbd.CfbdRequestLimitError("CFBD monthly limit is unavailable")

    openapi_result = _get(cfbd.CFBD_BASE_URL + OPENAPI_PATH, authenticated=False)
    openapi = _json(openapi_result)
    terms_result = _get(TERMS_URL, authenticated=False)
    terms_text = terms_result.body.decode("utf-8", "replace")
    authority = _validate_authority(openapi, terms_text)

    snapshot_root = args.snapshot_root.resolve()
    provider_root = snapshot_root / "cfbd" / "rest_v2"
    provider_root.mkdir(parents=True, exist_ok=True)
    pending = provider_root / f".pending-{retrieval}"
    if pending.exists():
        raise AcquisitionError(f"pending snapshot already exists: {pending}")
    pending.mkdir()
    assets: list[dict[str, Any]] = []
    try:
        assets.append(
            _write_asset(
                pending=pending,
                relative_path=Path("authority/api-docs.json"),
                result=openapi_result,
                endpoint=OPENAPI_PATH,
                parameters={},
                rows=None,
            )
        )
        assets.append(
            _write_asset(
                pending=pending,
                relative_path=Path("authority/terms.html"),
                result=terms_result,
                endpoint=TERMS_URL,
                parameters={},
                rows=None,
            )
        )
        plans = (
            (
                "draft_picks",
                "/draft/picks",
                DRAFT_YEARS,
                "DraftPick",
                {},
            ),
            (
                "player_season_stats",
                "/stats/player/season",
                COLLEGE_YEARS,
                "PlayerStat",
                {},
            ),
            (
                "player_usage",
                "/player/usage",
                COLLEGE_YEARS,
                "PlayerUsage",
                {"excludeGarbageTime": "true"},
            ),
            (
                "player_ppa",
                "/ppa/players/season",
                COLLEGE_YEARS,
                "PlayerSeasonPredictedPointsAdded",
                {"excludeGarbageTime": "true"},
            ),
        )
        family_counts: dict[str, int] = {}
        for family, endpoint, years, schema_name, fixed in plans:
            required = _required_fields(openapi, schema_name)
            family_counts[family] = 0
            for year in years:
                params = {"year": year, **fixed}
                url = cfbd.build_url(endpoint, params)
                result = _get(url, authenticated=True)
                rows = _validate_rows(
                    _json(result),
                    required=required,
                    label=f"{family}/{year}",
                )
                family_counts[family] += len(rows)
                assets.append(
                    _write_asset(
                        pending=pending,
                        relative_path=Path("raw") / family / f"{year}.json",
                        result=result,
                        endpoint=endpoint,
                        parameters=params,
                        rows=rows,
                    )
                )
                print(f"{family} year={year} rows={len(rows)}")

        after = _redacted_info(_json(_get(cfbd.build_url("/info"), authenticated=True)))
        hashes = [asset["sha256"] for asset in assets]
        aggregate = foundation.sha256_bytes("".join(hashes).encode("ascii"))
        snapshot_id = f"{retrieval}-{aggregate[:12]}"
        final = provider_root / snapshot_id
        if final.exists():
            raise AcquisitionError(f"immutable snapshot already exists: {final}")
        manifest = {
            "schema_version": 1,
            "foundation_id": "NWR_NEW_EVIDENCE_FOUNDATION_V1",
            "admission_id": "NWR_CFBD_COLLEGE_EVIDENCE_ADMISSION_V1",
            "provider": "CollegeFootballData",
            "api_family": "official REST API v2",
            "snapshot_id": snapshot_id,
            "retrieved_at_utc": retrieved_at,
            "authority": authority,
            "terms_url": TERMS_URL,
            "terms_sha256": foundation.sha256_bytes(terms_result.body),
            "terms_review": (
                "PRIVATE_RESEARCH_USE_ACCEPTED_NO_RAW_REDISTRIBUTION_"
                "ATTRIBUTION_RECORDED"
            ),
            "credential_receipt": "OWNER_USER_LEVEL_TOKEN_BRIDGED_REDACTED",
            "request_plan": {
                "data_calls": DATA_REQUEST_COUNT,
                "quota_checks": 2,
                "authenticated_calls": TOTAL_AUTHENTICATED_REQUESTS,
                "lane_limit": cfbd.MAX_LANE_REQUESTS,
                "stop_rule": "STOP_BEFORE_80_PERCENT_OF_REMAINING_ALLOWANCE",
            },
            "usage_before": before,
            "usage_after": after,
            "families": {
                family: {
                    "endpoint": endpoint,
                    "years": list(years),
                    "rows": family_counts[family],
                    "schema": schema_name,
                    "temporal_availability_rule": TEMPORAL_RULES[family],
                    "admission_status": (
                        "ADMITTED_PRIMARY_SOURCE"
                        if family == "draft_picks"
                        else "ADMITTED_WITH_RETROSPECTIVE_REVISION_LIMIT"
                    ),
                }
                for family, endpoint, years, schema_name, _ in plans
            },
            "aggregate_sha256": aggregate,
            "immutable": True,
            "complete": True,
            "assets": assets,
        }
        manifest_text = (
            json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        foundation.require_no_secret(manifest_text, known_tokens=(token,))
        (pending / "COMPLETION_MANIFEST.json").write_text(
            manifest_text,
            encoding="utf-8",
            newline="\n",
        )
        (pending / "TERMS_AND_LICENSE_RECEIPT.json").write_text(
            json.dumps(
                {
                    "provider": "CollegeFootballData",
                    "owner": "Rad Sports Analytics LLC",
                    "terms_url": TERMS_URL,
                    "effective_date": "2025-07-01",
                    "raw_redistribution": "PROHIBITED_WITHOUT_EXPLICIT_PERMISSION",
                    "attribution": "STRONGLY_ENCOURAGED_AND_RECORDED",
                    "credential_handling": "PASS_NOT_STORED",
                    "tier_change": "NONE",
                    "purchase": "NONE",
                    "review_result": (
                        "ACCEPTED_FOR_PRIVATE_LOCAL_RESEARCH_AND_HASH_ONLY_RAW_RECEIPTS"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        pending.rename(final)
        for path in sorted(final.rglob("*")):
            if path.is_file():
                path.chmod(stat.S_IREAD)
        catalog = {
            "schema_version": 1,
            "foundation_id": "NWR_NEW_EVIDENCE_FOUNDATION_V1",
            "admission_id": "NWR_CFBD_COLLEGE_EVIDENCE_ADMISSION_V1",
            "snapshot_id": snapshot_id,
            "manifest_relative_path": (
                f"cfbd/rest_v2/{snapshot_id}/COMPLETION_MANIFEST.json"
            ),
            "aggregate_sha256": aggregate,
            "retrieved_at_utc": retrieved_at,
            "provider_calls": TOTAL_AUTHENTICATED_REQUESTS,
            "data_calls": DATA_REQUEST_COUNT,
            "raw_payloads_committed": False,
            "source_snapshot_root_contract": "SOURCE_SNAPSHOT_ROOT",
        }
        catalog_text = (
            json.dumps(catalog, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        foundation.require_no_secret(catalog_text, known_tokens=(token,))
        args.catalog_output.parent.mkdir(parents=True, exist_ok=True)
        args.catalog_output.write_text(catalog_text, encoding="utf-8", newline="\n")
        print(f"snapshot_id={snapshot_id}")
        print(f"aggregate_sha256={aggregate}")
        print(f"data_calls={DATA_REQUEST_COUNT}")
        print(f"authenticated_calls={TOTAL_AUTHENTICATED_REQUESTS}")
        print(f"catalog={args.catalog_output}")
        return 0
    except Exception:
        if pending.exists():
            shutil.rmtree(pending)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
