from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SLEEPER_API_BASE = "https://api.sleeper.app/v1"
DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\scheduled_ingest\sleeper")
DEFAULT_LEAGUE_ID = "1344772855908290560"
DEFAULT_DRAFT_ID = "1353280212753723392"
DEFAULT_SEASON = "2026"
DEFAULT_LEAGUE_NAME = "Las Vegas Enginerds"
USER_AGENT = "NWR-Sleeper-Scheduled-Puller-V0"


@dataclass(frozen=True)
class EndpointSpec:
    name: str
    path: str
    required: bool = True


@dataclass(frozen=True)
class EndpointResult:
    name: str
    path: str
    file_name: str
    status: str
    row_count: int
    byte_count: int
    sha256: str
    warning: str = ""
    error: str = ""


@dataclass(frozen=True)
class SleeperPullResult:
    snapshot_dir: Path
    report_path: Path
    metadata_path: Path
    endpoint_results: list[EndpointResult]
    warnings: list[str]


class SleeperClient:
    def __init__(self, api_base: str = SLEEPER_API_BASE, timeout: int = 30) -> None:
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def get_json(self, path: str) -> Any:
        url = f"{self.api_base}/{path.lstrip('/')}"
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=self.timeout) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)


def build_endpoint_specs(
    *,
    league_id: str,
    draft_id: str,
    transaction_rounds: list[int],
) -> list[EndpointSpec]:
    specs = [
        EndpointSpec("league", f"league/{league_id}"),
        EndpointSpec("users", f"league/{league_id}/users"),
        EndpointSpec("rosters", f"league/{league_id}/rosters"),
        EndpointSpec("drafts", f"league/{league_id}/drafts"),
        EndpointSpec("traded_picks", f"league/{league_id}/traded_picks"),
        EndpointSpec("draft_details", f"draft/{draft_id}"),
        EndpointSpec("draft_picks", f"draft/{draft_id}/picks"),
    ]
    specs.extend(
        EndpointSpec(
            f"transactions_round_{round_number}",
            f"league/{league_id}/transactions/{round_number}",
            required=False,
        )
        for round_number in transaction_rounds
    )
    return specs


def run_sleeper_pull(
    *,
    league_id: str,
    draft_id: str,
    season: str,
    league_name: str,
    output_root: Path,
    transaction_rounds: list[int] | None = None,
    snapshot_label: str | None = None,
    client: SleeperClient | None = None,
) -> SleeperPullResult:
    http = client or SleeperClient()
    rounds = transaction_rounds or []
    snapshot = snapshot_label or datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    snapshot_dir = output_root / snapshot
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    results: list[EndpointResult] = []
    warnings: list[str] = []
    specs = build_endpoint_specs(
        league_id=league_id,
        draft_id=draft_id,
        transaction_rounds=rounds,
    )

    for spec in specs:
        file_name = f"{spec.name}.json"
        output_path = snapshot_dir / file_name
        try:
            payload = http.get_json(spec.path)
            body = _json_bytes(payload)
            output_path.write_bytes(body)
            results.append(
                EndpointResult(
                    name=spec.name,
                    path=spec.path,
                    file_name=file_name,
                    status="ok",
                    row_count=_row_count(payload),
                    byte_count=len(body),
                    sha256=_sha256(body),
                    warning=_payload_warning(spec.name, payload),
                )
            )
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            error = f"{type(exc).__name__}: {exc}"
            status = "error" if spec.required else "warning"
            warning = "" if spec.required else "Optional endpoint failed."
            output_path.write_text("", encoding="utf-8")
            results.append(
                EndpointResult(
                    name=spec.name,
                    path=spec.path,
                    file_name=file_name,
                    status=status,
                    row_count=0,
                    byte_count=0,
                    sha256=_sha256(b""),
                    warning=warning,
                    error=error,
                )
            )
            warnings.append(f"{spec.name}: {error}")

    if not rounds:
        warnings.append(
            "transactions skipped; pass --transaction-rounds to fetch specific Sleeper "
            "transaction rounds safely."
        )

    metadata_path = snapshot_dir / "snapshot_metadata.json"
    report_path = snapshot_dir / "sleeper_pull_report.md"
    metadata = _metadata_payload(
        league_id=league_id,
        draft_id=draft_id,
        season=season,
        league_name=league_name,
        snapshot_label=snapshot,
        endpoint_results=results,
        warnings=warnings,
    )
    metadata_path.write_bytes(_json_bytes(metadata))
    report_path.write_text(_markdown_report(metadata, results), encoding="utf-8")
    return SleeperPullResult(
        snapshot_dir=snapshot_dir,
        report_path=report_path,
        metadata_path=metadata_path,
        endpoint_results=results,
        warnings=warnings,
    )


def parse_transaction_rounds(value: str) -> list[int]:
    if not value.strip():
        return []
    rounds: list[int] = []
    for part in value.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        round_number = int(stripped)
        if round_number < 1:
            raise ValueError("transaction rounds must be positive integers")
        rounds.append(round_number)
    return rounds


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a local-only raw Sleeper API snapshot and redacted report. "
            "Does not create Lane Exchange packages or approvals."
        )
    )
    parser.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--draft-id", default=DEFAULT_DRAFT_ID)
    parser.add_argument("--season", default=DEFAULT_SEASON)
    parser.add_argument("--league-name", default=DEFAULT_LEAGUE_NAME)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--transaction-rounds",
        default="",
        help="Comma-separated Sleeper transaction rounds to fetch, e.g. 1,2,3.",
    )
    parser.add_argument("--snapshot-label", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        transaction_rounds = parse_transaction_rounds(args.transaction_rounds)
        result = run_sleeper_pull(
            league_id=args.league_id,
            draft_id=args.draft_id,
            season=args.season,
            league_name=args.league_name,
            output_root=args.output_root,
            transaction_rounds=transaction_rounds,
            snapshot_label=args.snapshot_label,
        )
    except Exception as exc:
        print(f"Sleeper scheduled pull failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"snapshot_dir={result.snapshot_dir}")
    print(f"report_path={result.report_path}")
    for endpoint in result.endpoint_results:
        print(
            f"{endpoint.name}: {endpoint.status} rows={endpoint.row_count} "
            f"sha256={endpoint.sha256}"
        )
    return 0


def _metadata_payload(
    *,
    league_id: str,
    draft_id: str,
    season: str,
    league_name: str,
    snapshot_label: str,
    endpoint_results: list[EndpointResult],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "source": "Sleeper public read-only API",
        "puller": "sleeper_scheduled_pull_v0",
        "created_at": datetime.now(UTC).isoformat(),
        "snapshot_label": snapshot_label,
        "league_id": league_id,
        "draft_id": draft_id,
        "season": season,
        "league_name": league_name,
        "approval_status": "raw_snapshot_only_not_approved",
        "creates_lane_exchange_packages": False,
        "updates_latest_candidate": False,
        "updates_latest_approved": False,
        "allowed_use": [
            "local_raw_snapshot",
            "source_audit",
            "future_candidate_normalizer_input_after_review",
        ],
        "forbidden_use": [
            "latest_approved",
            "pinned_live_snapshot",
            "final_draft_day_decision",
            "simulation",
            "recommendation",
            "private_value",
            "hidden_sort",
            "production_deployment",
        ],
        "warnings": warnings,
        "endpoints": [
            {
                "name": result.name,
                "path": result.path,
                "file_name": result.file_name,
                "status": result.status,
                "row_count": result.row_count,
                "byte_count": result.byte_count,
                "sha256": result.sha256,
                "warning": result.warning,
                "error": result.error,
            }
            for result in endpoint_results
        ],
    }


def _markdown_report(metadata: dict[str, Any], results: list[EndpointResult]) -> str:
    lines = [
        "# Sleeper Scheduled Pull V0 Raw Snapshot Report",
        "",
        "## Scope",
        "",
        "Local-only raw Sleeper API snapshot. This report does not approve data for "
        "Lane Exchange, Mock Draft, final draft-day use, simulations, recommendations, "
        "deployment, private value, or production use.",
        "",
        "## Snapshot",
        "",
        f"- Created at: `{metadata['created_at']}`",
        f"- League: `{metadata['league_name']}`",
        f"- Season: `{metadata['season']}`",
        f"- League ID: `{metadata['league_id']}`",
        f"- Draft ID: `{metadata['draft_id']}`",
        f"- Snapshot label: `{metadata['snapshot_label']}`",
        "",
        "## Endpoint Status",
        "",
        "| Endpoint | Status | Rows | Bytes | SHA256 | Warning |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for result in results:
        warning = result.warning or result.error
        lines.append(
            f"| `{result.name}` | `{result.status}` | {result.row_count} | "
            f"{result.byte_count} | `{result.sha256}` | {warning} |"
        )
    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )
    warnings = metadata.get("warnings") or []
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Raw API responses stay local-only outside Git.",
            "- No Lane Exchange packages were created.",
            "- `latest_candidate` was not updated.",
            "- `latest_approved` was not updated.",
            "- No simulation, recommendation, deployment, or private value path is approved.",
        ]
    )
    return "\n".join(lines) + "\n"


def _payload_warning(name: str, payload: Any) -> str:
    if name == "draft_picks" and isinstance(payload, list) and not payload:
        return "Draft picks endpoint returned zero rows; this is expected for pre-draft leagues."
    if name == "traded_picks" and isinstance(payload, list) and not payload:
        return "No traded picks returned."
    return ""


def _row_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return len(payload)
    if payload is None:
        return 0
    return 1


def _json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
