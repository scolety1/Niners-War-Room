import json
from pathlib import Path

import pytest

from src.services.rookie_lane_exchange import (
    ManifestValidationError,
    PackageOwnershipError,
    compute_row_count,
    compute_sha256,
    publish_rookie_exchange_snapshot,
    read_exchange_pointer,
    validate_manifest,
)


def _fake_rookie_csv(path: Path) -> Path:
    path.write_text(
        "player,team,position\n"
        "Fake Rookie A,SF,RB\n"
        "Fake Rookie B,SF,WR\n",
        encoding="utf-8",
    )
    return path


def test_candidate_publish_writes_owned_snapshot_without_approval_pointer(tmp_path: Path) -> None:
    data_file = _fake_rookie_csv(tmp_path / "fake_rookie_mock_input.csv")

    result = publish_rookie_exchange_snapshot(
        data_file=data_file,
        exchange_root=tmp_path / "lane_exchange",
        snapshot_label="fake_candidate_20260620",
        source_branch="work/rookie-framework-path",
        source_head="7884d67",
        notes="Fake temp test data only.",
    )

    assert result.snapshot_dir.is_dir()
    assert result.data_path.read_text(encoding="utf-8") == data_file.read_text(encoding="utf-8")
    assert result.pointer_path.name == "latest_candidate.json"
    assert result.pointer_path.is_file()
    assert result.approved_pointer_path is None
    assert not (result.pointer_path.parent / "latest_approved.json").exists()
    assert result.manifest["package_name"] == "rookie_hq/frozen_rookie_mock_input"
    assert result.manifest["approval_status"] == "candidate"
    assert result.manifest["row_count"] == 2
    assert result.manifest["sha256"] == compute_sha256(result.data_path)


def test_approved_publish_requires_explicit_approve_flag(tmp_path: Path) -> None:
    data_file = _fake_rookie_csv(tmp_path / "fake_rookie_mock_input.csv")

    result = publish_rookie_exchange_snapshot(
        data_file=data_file,
        exchange_root=tmp_path / "lane_exchange",
        snapshot_label="fake_approved_20260620",
        approve=True,
        source_branch="work/rookie-framework-path",
        source_head="7884d67",
        notes="Fake approved test data only.",
    )

    assert result.approved_pointer_path is not None
    assert result.approved_pointer_path.name == "latest_approved.json"
    pointer_manifest = read_exchange_pointer(
        exchange_root=tmp_path / "lane_exchange",
        source_lane="rookie_hq",
        package_slug="frozen_rookie_mock_input",
        pointer_name="latest_approved.json",
        require_approved=True,
    )
    assert pointer_manifest["approval_status"] == "approved"
    assert pointer_manifest["row_count"] == 2


def test_publish_refuses_non_rookie_or_unowned_packages(tmp_path: Path) -> None:
    data_file = _fake_rookie_csv(tmp_path / "fake_rookie_mock_input.csv")

    with pytest.raises(PackageOwnershipError):
        publish_rookie_exchange_snapshot(
            data_file=data_file,
            package_name="mock_draft/live_board_state",
            exchange_root=tmp_path / "lane_exchange",
            snapshot_label="bad_lane",
            source_branch="work/rookie-framework-path",
            source_head="7884d67",
        )

    with pytest.raises(PackageOwnershipError):
        publish_rookie_exchange_snapshot(
            data_file=data_file,
            package_name="rookie_hq/not_rookie_owned",
            exchange_root=tmp_path / "lane_exchange",
            snapshot_label="bad_package",
            source_branch="work/rookie-framework-path",
            source_head="7884d67",
        )


def test_validate_manifest_detects_payload_tampering(tmp_path: Path) -> None:
    data_file = _fake_rookie_csv(tmp_path / "fake_rookie_mock_input.csv")
    result = publish_rookie_exchange_snapshot(
        data_file=data_file,
        exchange_root=tmp_path / "lane_exchange",
        snapshot_label="tamper_test",
        source_branch="work/rookie-framework-path",
        source_head="7884d67",
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    result.data_path.write_text("player,team,position\nChanged,SF,RB\n", encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="sha256"):
        validate_manifest(manifest, snapshot_dir=result.snapshot_dir, enforce_rookie_owned=True)


def test_csv_row_count_excludes_header(tmp_path: Path) -> None:
    data_file = _fake_rookie_csv(tmp_path / "fake_rookie_mock_input.csv")

    assert compute_row_count(data_file) == 2
