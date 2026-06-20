from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_SHARED_ROOT = Path(r"C:\NWR_SHARED_DATA")
DEFAULT_REPORT_ROOT = DEFAULT_SHARED_ROOT / "scheduled_ingest" / "reports" / "operator_status"
MOCK_DRAFT_REQUIRED_PACKAGES = (
    "rookie_hq/frozen_rookie_mock_input",
    "drop_decision/dropped_veterans",
    "drop_decision/unavailable_players",
    "league_state/pick_order",
    "league_state/nwr_picks",
    "model_value/veteran_private_values",
)
STATS_CONTEXT_PACKAGES = (
    "stats_context/player_weekly_stats_display_context",
    "stats_context/player_season_stats_display_context",
    "stats_context/player_usage_context",
    "stats_context/player_stats_crosscheck_report",
)
BLOCKED_SYSTEMS = (
    "QA/Data Hygiene HOLD",
    "final draft-day approval",
    "simulations/recommendations",
    "hosted deployment",
)


@dataclass(frozen=True)
class PointerStatus:
    package_name: str
    pointer_type: str
    pointer_path: Path
    manifest_path: Path | None
    data_file: str
    row_count: int | None
    sha256: str
    approval_status: str
    approved_for: list[str]
    allowed_use: list[str]
    forbidden_use: list[str]
    updated_at: str
    created_at: str
    notes: str
    exists: bool
    warning: str = ""


@dataclass(frozen=True)
class OperatorStatus:
    shared_root: Path
    lane_exchange_root: Path
    registry_path: Path
    latest_sleeper_snapshot: Path | None
    latest_sleeper_report: Path | None
    latest_nflverse_snapshot: Path | None
    latest_nflverse_report: Path | None
    latest_candidates: dict[str, PointerStatus]
    latest_approved: dict[str, PointerStatus]
    warnings: list[str]
    blockers: list[str]
    report_path: Path | None = None


def collect_status(shared_root: Path = DEFAULT_SHARED_ROOT) -> OperatorStatus:
    lane_exchange_root = shared_root / "lane_exchange"
    registry_path = shared_root / "lane_exchange_registry" / "lane_exchange_v0_registry.json"
    sleeper_root = shared_root / "scheduled_ingest" / "sleeper"
    nflverse_root = shared_root / "scheduled_ingest" / "nflverse"
    live_test_root = shared_root / "live_test_reports"
    warnings: list[str] = []

    _warn_missing(warnings, "Lane Exchange root", lane_exchange_root)
    _warn_missing(warnings, "Lane Exchange registry", registry_path)
    _warn_missing(warnings, "Sleeper ingest root", sleeper_root)
    _warn_missing(warnings, "nflverse ingest root", nflverse_root)
    _warn_missing(warnings, "live-test reports root", live_test_root)

    latest_sleeper_snapshot = _latest_snapshot_dir(sleeper_root)
    latest_nflverse_snapshot = _latest_snapshot_dir(nflverse_root)
    latest_sleeper_report = _latest_report(
        latest_sleeper_snapshot,
        ("sleeper_normalizer_v0_report.md", "sleeper_pull_report.md"),
    )
    latest_nflverse_report = _latest_report(
        latest_nflverse_snapshot,
        ("nflverse_normalizer_v0_report.md", "nflverse_pull_report.md"),
    )

    latest_candidates = _collect_pointers(lane_exchange_root, "latest_candidate.json")
    latest_approved = _collect_pointers(lane_exchange_root, "latest_approved.json")
    _package_warnings(warnings, latest_candidates, latest_approved)
    blockers = list(BLOCKED_SYSTEMS)
    return OperatorStatus(
        shared_root=shared_root,
        lane_exchange_root=lane_exchange_root,
        registry_path=registry_path,
        latest_sleeper_snapshot=latest_sleeper_snapshot,
        latest_sleeper_report=latest_sleeper_report,
        latest_nflverse_snapshot=latest_nflverse_snapshot,
        latest_nflverse_report=latest_nflverse_report,
        latest_candidates=latest_candidates,
        latest_approved=latest_approved,
        warnings=warnings,
        blockers=blockers,
    )


def write_report(status: OperatorStatus, report_root: Path = DEFAULT_REPORT_ROOT) -> Path:
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / f"NWR_OPERATOR_STATUS_V0_{_timestamp()}.md"
    report_path.write_text(_markdown_report(status), encoding="utf-8")
    return report_path


def concise_summary(status: OperatorStatus) -> str:
    candidate_count = len(status.latest_candidates)
    approved_count = len(status.latest_approved)
    warnings = len(status.warnings)
    lines = [
        "NWR Operator Status V0",
        f"Sleeper snapshot: {_path_or_missing(status.latest_sleeper_snapshot)}",
        f"nflverse snapshot: {_path_or_missing(status.latest_nflverse_snapshot)}",
        f"latest_candidate packages: {candidate_count}",
        f"latest_approved packages: {approved_count}",
        f"warnings: {warnings}",
        f"next safe action: {_next_safe_action(status)}",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only NWR local automation and Lane Exchange status report. "
            "Does not create packages, approvals, simulations, deployments, or tasks."
        )
    )
    parser.add_argument("--shared-root", type=Path, default=DEFAULT_SHARED_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--write-report", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        status = collect_status(args.shared_root)
        report_path = write_report(status, args.report_root) if args.write_report else None
    except Exception as exc:
        print(f"NWR operator status failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(concise_summary(status))
    if report_path:
        print(f"report_path={report_path}")
    return 0


def _collect_pointers(lane_exchange_root: Path, pointer_name: str) -> dict[str, PointerStatus]:
    pointers: dict[str, PointerStatus] = {}
    if not lane_exchange_root.exists():
        return pointers
    for path in sorted(lane_exchange_root.glob(f"*/*/{pointer_name}")):
        package_name = "/".join(path.parts[-3:-1])
        pointers[package_name] = _read_pointer(package_name, path, pointer_name)
    return pointers


def _read_pointer(package_name: str, path: Path, pointer_name: str) -> PointerStatus:
    try:
        pointer = _read_json(path)
        manifest_path = _manifest_path(pointer)
        manifest = _read_json(manifest_path) if manifest_path and manifest_path.exists() else {}
        warning = "" if manifest else "manifest missing or unreadable"
        return PointerStatus(
            package_name=str(pointer.get("package_name") or package_name),
            pointer_type=pointer_name.removesuffix(".json"),
            pointer_path=path,
            manifest_path=manifest_path,
            data_file=str(pointer.get("data_file") or manifest.get("data_file") or ""),
            row_count=_int_or_none(pointer.get("row_count") or manifest.get("row_count")),
            sha256=str(pointer.get("sha256") or manifest.get("sha256") or ""),
            approval_status=str(
                pointer.get("approval_status") or manifest.get("approval_status") or ""
            ),
            approved_for=_as_str_list(manifest.get("approved_for")),
            allowed_use=_as_str_list(pointer.get("allowed_use") or manifest.get("allowed_use")),
            forbidden_use=_as_str_list(
                pointer.get("forbidden_use") or manifest.get("forbidden_use")
            ),
            updated_at=str(pointer.get("updated_at") or ""),
            created_at=str(manifest.get("created_at") or ""),
            notes=str(pointer.get("notes") or manifest.get("notes") or ""),
            exists=True,
            warning=warning,
        )
    except (OSError, json.JSONDecodeError) as exc:
        return PointerStatus(
            package_name=package_name,
            pointer_type=pointer_name.removesuffix(".json"),
            pointer_path=path,
            manifest_path=None,
            data_file="",
            row_count=None,
            sha256="",
            approval_status="",
            approved_for=[],
            allowed_use=[],
            forbidden_use=[],
            updated_at="",
            created_at="",
            notes="",
            exists=True,
            warning=f"{type(exc).__name__}: {exc}",
        )


def _manifest_path(pointer: dict[str, Any]) -> Path | None:
    raw = pointer.get("manifest_path")
    return Path(str(raw)) if raw else None


def _latest_snapshot_dir(root: Path) -> Path | None:
    if not root.exists():
        return None
    dirs = [path for path in root.iterdir() if path.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda path: (path.stat().st_mtime, path.name))


def _latest_report(snapshot_dir: Path | None, names: tuple[str, ...]) -> Path | None:
    if snapshot_dir is None:
        return None
    candidates = [snapshot_dir / name for name in names if (snapshot_dir / name).exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def _package_warnings(
    warnings: list[str],
    candidates: dict[str, PointerStatus],
    approved: dict[str, PointerStatus],
) -> None:
    for package in MOCK_DRAFT_REQUIRED_PACKAGES:
        if package not in approved:
            warnings.append(f"Mock Draft required package missing latest_approved: {package}")
    for package in STATS_CONTEXT_PACKAGES:
        if package not in candidates:
            warnings.append(f"stats_context package missing latest_candidate: {package}")
    for package, candidate in sorted(candidates.items()):
        approval = approved.get(package)
        if approval is None:
            continue
        if _stamp(candidate) > _stamp(approval):
            warnings.append(f"latest_candidate newer than latest_approved: {package}")
    for package, approval in sorted(approved.items()):
        text = " ".join([*approval.approved_for, *approval.allowed_use, approval.notes]).lower()
        if "first" in text and "live-test" in text:
            warnings.append(f"approval limited to first local live-test validation: {package}")


def _markdown_report(status: OperatorStatus) -> str:
    lines = [
        "# NWR Operator Status V0",
        "",
        f"Created at: `{datetime.now(UTC).isoformat()}`",
        "",
        "## Scope",
        "",
        "Read-only operator status. This report does not create Lane Exchange packages, "
        "update candidates or approvals, run simulations, deploy, create scheduled tasks, "
        "or touch lane worktrees.",
        "",
        "## Raw Snapshots",
        "",
        f"- Latest Sleeper snapshot: `{_path_or_missing(status.latest_sleeper_snapshot)}`",
        f"- Latest Sleeper report: `{_path_or_missing(status.latest_sleeper_report)}`",
        f"- Latest nflverse snapshot: `{_path_or_missing(status.latest_nflverse_snapshot)}`",
        f"- Latest nflverse report: `{_path_or_missing(status.latest_nflverse_report)}`",
        "",
        "## latest_candidate Summary",
        "",
        *_pointer_table(status.latest_candidates),
        "",
        "## latest_approved Summary",
        "",
        *_pointer_table(status.latest_approved),
        "",
        "## Required Mock Draft Packages",
        "",
        *_package_presence_table(MOCK_DRAFT_REQUIRED_PACKAGES, status.latest_approved),
        "",
        "## stats_context Candidates",
        "",
        *_package_presence_table(STATS_CONTEXT_PACKAGES, status.latest_candidates),
        "",
        "## Warnings And Gates",
        "",
    ]
    if status.warnings:
        lines.extend(f"- {warning}" for warning in status.warnings)
    else:
        lines.append("- none")
    lines.extend(["", "## Blocked Systems", ""])
    lines.extend(f"- {blocker}" for blocker in status.blockers)
    lines.extend(
        [
            "",
            "## Next Safe Action",
            "",
            _next_safe_action(status),
            "",
        ]
    )
    return "\n".join(lines)


def _pointer_table(pointers: dict[str, PointerStatus]) -> list[str]:
    lines = [
        "| Package | Status | Rows | Pointer | Manifest | Notes |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    if not pointers:
        lines.append("| none | missing |  |  |  |  |")
        return lines
    for package, pointer in sorted(pointers.items()):
        lines.append(
            f"| `{package}` | `{pointer.approval_status}` | "
            f"{pointer.row_count if pointer.row_count is not None else ''} | "
            f"`{pointer.pointer_path}` | `{_path_or_missing(pointer.manifest_path)}` | "
            f"{pointer.warning or pointer.notes[:80]} |"
        )
    return lines


def _package_presence_table(
    packages: tuple[str, ...], pointers: dict[str, PointerStatus]
) -> list[str]:
    lines = ["| Package | Present | Rows | Status |", "| --- | --- | ---: | --- |"]
    for package in packages:
        pointer = pointers.get(package)
        lines.append(
            f"| `{package}` | {pointer is not None} | "
            f"{pointer.row_count if pointer and pointer.row_count is not None else ''} | "
            f"`{pointer.approval_status if pointer else 'missing'}` |"
        )
    return lines


def _next_safe_action(status: OperatorStatus) -> str:
    if status.warnings:
        return "Review warnings, then decide whether to audit or promote candidates manually."
    return "Run read-only audits or request explicit Tim/Master approval before any promotion."


def _warn_missing(warnings: list[str], label: str, path: Path) -> None:
    if not path.exists():
        warnings.append(f"{label} missing: {path}")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else {}


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _stamp(pointer: PointerStatus) -> str:
    return pointer.updated_at or pointer.created_at


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _path_or_missing(path: Path | None) -> str:
    return str(path) if path else "missing"


if __name__ == "__main__":
    raise SystemExit(main())
