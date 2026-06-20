import json
from pathlib import Path

import pytest

from scripts.trading_lab_lane_exchange_readiness_check import main as readiness_main
from src.trading_lab.trading_lab_lane_exchange import (
    LATEST_CANDIDATE,
    LaneExchangeError,
    file_sha256,
    load_registry,
    publish_trade_research_snapshot,
    trading_lab_role,
    validate_latest_approved_manifest,
)


def test_trading_lab_role_from_registry(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)

    role = trading_lab_role(load_registry(registry_path))

    assert role.lane_id == "trading_lab"
    assert role.owned_packages == ("trade_research_snapshot",)
    assert role.consumed_packages == ()
    assert role.requires_explicit_publish_approval is True


def test_latest_approved_manifest_validates_hash_rows_and_allowed_use(tmp_path: Path) -> None:
    hub_root = tmp_path / "hub"
    _write_approved_snapshot(hub_root)

    result = validate_latest_approved_manifest(
        hub_root=hub_root,
        source_lane="league_state",
        package_name="nwr_picks",
        allowed_use="trade_lab_research_review",
    )

    assert result.package_name == "league_state/nwr_picks"
    assert result.row_count == 2
    assert result.approval_status == "approved"
    assert result.sha256 == file_sha256(result.data_path)


def test_latest_candidate_is_refused_for_decisions(tmp_path: Path) -> None:
    hub_root = tmp_path / "hub"
    _write_approved_snapshot(hub_root)

    with pytest.raises(LaneExchangeError, match="latest_candidate"):
        validate_latest_approved_manifest(
            hub_root=hub_root,
            source_lane="league_state",
            package_name="nwr_picks",
            pointer_name=LATEST_CANDIDATE,
        )


def test_manifest_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    hub_root = tmp_path / "hub"
    _write_approved_snapshot(hub_root, sha256="not-the-real-hash")

    with pytest.raises(LaneExchangeError, match="sha256"):
        validate_latest_approved_manifest(
            hub_root=hub_root,
            source_lane="league_state",
            package_name="nwr_picks",
        )


def test_manifest_row_count_mismatch_fails_closed(tmp_path: Path) -> None:
    hub_root = tmp_path / "hub"
    _write_approved_snapshot(hub_root, row_count=99)

    with pytest.raises(LaneExchangeError, match="row count"):
        validate_latest_approved_manifest(
            hub_root=hub_root,
            source_lane="league_state",
            package_name="nwr_picks",
        )


def test_trading_lab_publish_requires_explicit_registry_approval(tmp_path: Path) -> None:
    registry = load_registry(_write_registry(tmp_path))

    with pytest.raises(LaneExchangeError, match="explicit approval"):
        publish_trade_research_snapshot(
            hub_root=tmp_path / "hub",
            registry=registry,
            rows=(_fake_research_row(),),
            source_repo=r"C:\NWR\Niners-War-Room-trading-lab",
            source_branch="work/trading-lab",
            source_head="fake-head",
        )


def test_trading_lab_publish_writes_only_temp_owned_research_snapshot(tmp_path: Path) -> None:
    registry = load_registry(_write_registry(tmp_path))

    manifest_path = publish_trade_research_snapshot(
        hub_root=tmp_path / "hub",
        registry=registry,
        rows=(_fake_research_row(),),
        source_repo=r"C:\NWR\Niners-War-Room-trading-lab",
        source_branch="work/trading-lab",
        source_head="fake-head",
        explicit_publish_approval=True,
        snapshot_label="temp_test_snapshot",
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["package_name"] == "trading_lab/trade_research_snapshot"
    assert manifest["approval_status"] == "candidate"
    assert manifest["contains_private_value"] is False
    assert (manifest_path.parent / "trade_research_snapshot.csv").exists()
    assert str(tmp_path) in str(manifest_path)


def test_readiness_script_reports_role_and_validates_fake_package(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    registry_path = _write_registry(tmp_path)
    hub_root = tmp_path / "hub"
    _write_approved_snapshot(hub_root)

    exit_code = readiness_main(
        [
            "--registry",
            str(registry_path),
            "--hub-root",
            str(hub_root),
            "--package",
            "league_state/nwr_picks",
            "--allowed-use",
            "trade_lab_research_review",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "GREEN" in output
    assert "trade_research_snapshot" in output


def test_exchange_helpers_do_not_expose_execution_or_provider_fetch_terms() -> None:
    source = Path("src/trading_lab/trading_lab_lane_exchange.py").read_text(
        encoding="utf-8"
    ).lower()

    for blocked in ("broker order", "real-money", "credential", "automated execution"):
        assert blocked not in source


def _write_registry(tmp_path: Path) -> Path:
    registry = {
        "contract_version": "lane_exchange_v0",
        "hub_root": str(tmp_path / "hub"),
        "git_commit_allowed": False,
        "lane_ownership": [
            {
                "source_lane": "trading_lab",
                "owns_packages": ["trade_research_snapshot"],
                "requires_explicit_approval_later": True,
                "notes": "May publish only with later explicit approval.",
            },
            {
                "source_lane": "league_state",
                "owns_packages": ["nwr_picks"],
                "notes": "Fake test owner.",
            },
        ],
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    return registry_path


def _write_approved_snapshot(
    hub_root: Path,
    *,
    sha256: str | None = None,
    row_count: int = 2,
) -> Path:
    snapshot_dir = hub_root / "league_state" / "nwr_picks" / "20260620_approved"
    snapshot_dir.mkdir(parents=True)
    csv_path = snapshot_dir / "nwr_picks.csv"
    csv_path.write_text(
        "pick_id,display_name,notes\n"
        "pick-1,2026 2nd,Fake pick context\n"
        "pick-2,2026 3rd,Fake pick context\n",
        encoding="utf-8",
    )
    manifest = {
        "source_lane": "League State",
        "source_repo": r"C:\NWR\Niners-War-Room",
        "source_branch": "main",
        "source_head": "fake-head",
        "package_name": "league_state/nwr_picks",
        "schema_version": "nwr_picks_v0",
        "data_file": csv_path.name,
        "row_count": row_count,
        "sha256": sha256 or file_sha256(csv_path),
        "created_at": "2026-06-20T00:00:00-06:00",
        "approval_status": "approved",
        "approved_for": ["trade_lab_research_review"],
        "allowed_use": ["trade_lab_research_review"],
        "forbidden_use": ["automatic_transaction"],
        "contains_private_value": False,
        "contains_market_data": False,
        "contains_adp": False,
        "notes": "Fake approved package for Trading Lab validation tests.",
    }
    manifest_path = snapshot_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    pointer_path = hub_root / "league_state" / "nwr_picks" / "latest_approved.json"
    pointer_path.write_text(json.dumps({"manifest_path": str(manifest_path)}), encoding="utf-8")
    return manifest_path


def _fake_research_row() -> dict[str, str]:
    return {
        "research_id": "fake-trade-review-1",
        "trade_question": "Should Team Alpha review Target Player for Player A?",
        "review_status": "manual_review",
        "notes": "Fake temp-only research row.",
    }
