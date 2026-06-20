from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "validate_lane_exchange_local_only.py"
)
SPEC = importlib.util.spec_from_file_location("validate_lane_exchange_local_only", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
exchange_guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = exchange_guard
SPEC.loader.exec_module(exchange_guard)


def _write_contract(path: Path, hub: Path, registry: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "# NWR Lane Exchange V0 Contract\n\n"
            f"{hub}\n\n"
            f"{registry}\n\n"
            "This root is local-only and must not be committed.\n"
            "No lane may scrape another lane's local repo.\n"
        ),
        encoding="utf-8",
    )


def _write_registry(path: Path, hub: Path, *, git_commit_allowed: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "contract_version": "lane_exchange_v0",
                "hub_root": str(hub),
                "local_only": True,
                "git_commit_allowed": git_commit_allowed,
                "rules": {
                    "do_not_commit": [
                        "data",
                        "local_exports",
                        "generated_artifacts",
                        "archives",
                        "exchange_snapshots",
                    ]
                },
            }
        ),
        encoding="utf-8",
    )


def _fixture_paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repo = tmp_path / "repo"
    hub = tmp_path / "shared" / "lane_exchange"
    registry = tmp_path / "shared" / "registry" / "lane_exchange_v0_registry.json"
    contract = tmp_path / "master" / "NWR_LANE_EXCHANGE_V0_CONTRACT.md"
    repo.mkdir()
    hub.mkdir(parents=True)
    return repo, hub, registry, contract


def test_lane_exchange_readiness_is_green_for_local_only_fixture(tmp_path: Path) -> None:
    repo, hub, registry, contract = _fixture_paths(tmp_path)
    _write_contract(contract, hub, registry)
    _write_registry(registry, hub)

    results = exchange_guard.build_results(repo, contract, registry, hub)

    assert exchange_guard.overall_verdict(results) == "GREEN"
    assert {result.name: result.status for result in results} == {
        "contract": "GREEN",
        "registry": "GREEN",
        "hub_boundary": "GREEN",
        "packaging_boundary": "GREEN",
    }


def test_lane_exchange_hub_inside_repo_is_red(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    hub = repo / "lane_exchange"
    registry = tmp_path / "registry" / "lane_exchange_v0_registry.json"
    contract = tmp_path / "NWR_LANE_EXCHANGE_V0_CONTRACT.md"
    hub.mkdir(parents=True)
    _write_contract(contract, hub, registry)
    _write_registry(registry, hub)

    results = exchange_guard.build_results(repo, contract, registry, hub)

    assert exchange_guard.overall_verdict(results) == "RED"
    assert {result.name: result.status for result in results}["hub_boundary"] == "RED"
    assert {result.name: result.status for result in results}["packaging_boundary"] == "RED"


def test_lane_exchange_hub_inside_git_worktree_is_red(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git_root = tmp_path / "git_root"
    hub = git_root / "shared" / "lane_exchange"
    registry = tmp_path / "registry" / "lane_exchange_v0_registry.json"
    contract = tmp_path / "NWR_LANE_EXCHANGE_V0_CONTRACT.md"
    (git_root / ".git").mkdir(parents=True)
    hub.mkdir(parents=True)
    _write_contract(contract, hub, registry)
    _write_registry(registry, hub)

    results = exchange_guard.build_results(repo, contract, registry, hub)

    assert exchange_guard.overall_verdict(results) == "RED"
    assert {result.name: result.status for result in results}["hub_boundary"] == "RED"


def test_lane_exchange_registry_allowing_git_commit_is_red(tmp_path: Path) -> None:
    repo, hub, registry, contract = _fixture_paths(tmp_path)
    _write_contract(contract, hub, registry)
    _write_registry(registry, hub, git_commit_allowed=True)

    results = exchange_guard.build_results(repo, contract, registry, hub)

    assert exchange_guard.overall_verdict(results) == "RED"
    assert {result.name: result.status for result in results}["registry"] == "RED"


def test_lane_exchange_missing_contract_or_registry_is_yellow(tmp_path: Path) -> None:
    repo, hub, registry, contract = _fixture_paths(tmp_path)

    results = exchange_guard.build_results(repo, contract, registry, hub)

    assert exchange_guard.overall_verdict(results) == "YELLOW"
    assert {result.name: result.status for result in results}["contract"] == "YELLOW"
    assert {result.name: result.status for result in results}["registry"] == "YELLOW"


def test_lane_exchange_json_report_shape(tmp_path: Path) -> None:
    repo, hub, registry, contract = _fixture_paths(tmp_path)
    _write_contract(contract, hub, registry)
    _write_registry(registry, hub)

    report = exchange_guard.result_to_dict(
        exchange_guard.build_results(repo, contract, registry, hub)
    )

    assert report["verdict"] == "GREEN"
    assert [check["name"] for check in report["checks"]] == [
        "contract",
        "registry",
        "hub_boundary",
        "packaging_boundary",
    ]
