from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONTRACT_PATH = Path(
    r"C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_LANE_EXCHANGE_V0_CONTRACT.md"
)
DEFAULT_REGISTRY_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json"
)
DEFAULT_HUB_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def status_rank(status: str) -> int:
    return {"GREEN": 0, "SKIPPED": 0, "YELLOW": 1, "RED": 2}.get(status, 1)


def overall_verdict(results: list[CheckResult]) -> str:
    worst = max((status_rank(result.status) for result in results), default=0)
    if worst >= 2:
        return "RED"
    if worst == 1:
        return "YELLOW"
    return "GREEN"


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def has_git_ancestor(path: Path) -> bool:
    current = path.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return True
    return False


def load_registry(path: Path) -> tuple[dict[str, object] | None, str]:
    if not path.exists():
        return None, f"registry missing: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except json.JSONDecodeError as exc:
        return None, f"registry JSON invalid: {exc}"


def check_contract(contract_path: Path, expected_hub: Path, expected_registry: Path) -> CheckResult:
    if not contract_path.exists():
        return CheckResult("contract", "YELLOW", f"missing contract: {contract_path}")

    text = contract_path.read_text(encoding="utf-8", errors="ignore")
    missing: list[str] = []
    for needle in (
        str(expected_hub),
        str(expected_registry),
        "local-only",
        "must not be committed",
        "No lane may scrape another lane's local repo",
    ):
        if needle not in text:
            missing.append(needle)

    if missing:
        return CheckResult("contract", "YELLOW", f"contract missing expected language: {missing}")
    return CheckResult("contract", "GREEN", f"contract readable: {contract_path}")


def check_registry(
    registry_path: Path,
    expected_hub: Path,
) -> tuple[CheckResult, dict[str, object]]:
    registry, error = load_registry(registry_path)
    if registry is None:
        return CheckResult("registry", "YELLOW", error), {}

    problems: list[str] = []
    if registry.get("contract_version") != "lane_exchange_v0":
        problems.append("contract_version is not lane_exchange_v0")
    if registry.get("local_only") is not True:
        problems.append("local_only is not true")
    if registry.get("git_commit_allowed") is not False:
        problems.append("git_commit_allowed is not false")
    if str(registry.get("hub_root", "")).rstrip("\\/") != str(expected_hub).rstrip("\\/"):
        problems.append("hub_root does not match expected local exchange hub")

    rules = registry.get("rules", {})
    do_not_commit = rules.get("do_not_commit", []) if isinstance(rules, dict) else []
    if "exchange_snapshots" not in do_not_commit:
        problems.append("registry do_not_commit does not include exchange_snapshots")

    if problems:
        return CheckResult("registry", "RED", "; ".join(problems)), registry
    return CheckResult("registry", "GREEN", f"registry readable: {registry_path}"), registry


def check_hub_boundary(repo: Path, hub_root: Path) -> CheckResult:
    if not hub_root.exists():
        return CheckResult("hub_boundary", "YELLOW", f"exchange hub missing: {hub_root}")
    if not hub_root.is_dir():
        return CheckResult("hub_boundary", "RED", f"exchange hub is not a directory: {hub_root}")
    if is_relative_to(hub_root, repo):
        return CheckResult("hub_boundary", "RED", "exchange hub is inside Deployment V2 repo")
    if has_git_ancestor(hub_root):
        return CheckResult("hub_boundary", "RED", "exchange hub is inside a Git worktree")
    return CheckResult(
        "hub_boundary",
        "GREEN",
        f"exchange hub is local-only outside Git: {hub_root}",
    )


def check_packaging_boundary(
    repo: Path,
    hub_root: Path,
    registry: dict[str, object],
) -> CheckResult:
    if not registry:
        return CheckResult(
            "packaging_boundary",
            "YELLOW",
            "registry unavailable; cannot confirm do-not-commit exchange rules",
        )
    rules = registry.get("rules", {})
    do_not_commit = rules.get("do_not_commit", []) if isinstance(rules, dict) else []
    required = {"data", "local_exports", "generated_artifacts", "archives", "exchange_snapshots"}
    missing = sorted(required - set(do_not_commit))
    if missing:
        return CheckResult("packaging_boundary", "RED", f"missing do_not_commit entries: {missing}")
    if is_relative_to(hub_root, repo):
        return CheckResult("packaging_boundary", "RED", "exchange hub could be packaged from repo")
    return CheckResult(
        "packaging_boundary",
        "GREEN",
        "exchange snapshots remain outside repo and are marked do-not-commit",
    )


def build_results(
    repo: Path,
    contract_path: Path,
    registry_path: Path,
    hub_root: Path,
) -> list[CheckResult]:
    contract = check_contract(contract_path, hub_root, registry_path)
    registry_check, registry = check_registry(registry_path, hub_root)
    return [
        contract,
        registry_check,
        check_hub_boundary(repo, hub_root),
        check_packaging_boundary(repo, hub_root, registry),
    ]


def result_to_dict(results: list[CheckResult]) -> dict[str, object]:
    return {
        "verdict": overall_verdict(results),
        "checks": [
            {"name": result.name, "status": result.status, "detail": result.detail}
            for result in results
        ],
    }


def print_text(results: list[CheckResult]) -> None:
    print(f"Deployment V2 lane exchange readiness verdict: {overall_verdict(results)}")
    for result in results:
        print(f"- {result.name}: {result.status} - {result.detail}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Deployment V2 local-only Lane Exchange awareness."
    )
    parser.add_argument("--repo", default=".", help="Deployment V2 repository root.")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH), help="Contract path.")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH), help="Registry path.")
    parser.add_argument(
        "--hub",
        default=str(DEFAULT_HUB_ROOT),
        help="Local-only exchange hub path.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results = build_results(
        repo=Path(args.repo),
        contract_path=Path(args.contract),
        registry_path=Path(args.registry),
        hub_root=Path(args.hub),
    )
    if args.json:
        print(json.dumps(result_to_dict(results), indent=2, sort_keys=True))
    else:
        print_text(results)
    verdict = overall_verdict(results)
    if verdict == "GREEN":
        return 0
    if verdict == "YELLOW":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
