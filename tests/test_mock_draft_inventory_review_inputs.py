from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.mock_draft_inventory_review_inputs import (
    build_and_write_review_input_inventory,
    build_review_input_inventory,
)


def test_inventory_scans_only_approved_directories_and_reports_missing_inputs(tmp_path) -> None:
    root = tmp_path / "repo"
    approved = root / "local_exports" / "mock_draft" / "review_inputs"
    approved.mkdir(parents=True)
    (approved / "sample.csv").write_text("player,position\nAlpha,WR\n", encoding="utf-8")

    inventory = build_review_input_inventory(
        repo_root=root,
        approved_dirs=[Path("local_exports/mock_draft/review_inputs")],
        output_path=Path("local_exports/mock_draft/input_inventory_20260617/manifest.json"),
    )

    assert inventory.review_only is True
    assert len(inventory.file_rows) == 1
    assert inventory.file_rows[0]["row_count"] == 1
    assert inventory.missing_required_inputs == (
        "post_drop_rosters",
        "post_drop_draft_order",
        "team_managers",
    )
    assert inventory.manifest["simulation_run"] is False
    assert inventory.manifest["real_market_data_imported"] is False


def test_inventory_rejects_paths_outside_worktree(tmp_path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    with pytest.raises(ValueError, match="escapes mock-draft worktree"):
        build_review_input_inventory(repo_root=root, approved_dirs=[tmp_path.parent])


def test_inventory_writes_local_only_artifact(tmp_path) -> None:
    root = tmp_path / "repo"
    approved = root / "local_exports" / "mock_draft" / "review_inputs"
    approved.mkdir(parents=True)
    (approved / "sample.csv").write_text("player,position\nAlpha,WR\n", encoding="utf-8")
    output = Path("local_exports/mock_draft/input_inventory_20260617/manifest.json")

    inventory = build_and_write_review_input_inventory(repo_root=root, output_path=output)

    artifact = root / output
    assert artifact.exists()
    manifest = json.loads(artifact.read_text(encoding="utf-8"))
    assert manifest["promotion_status"] == "local_inventory_only_not_app_wired_not_promoted"
    assert manifest["full_simulation_blocked"] is True
    assert "No NWR score is invented" in manifest["nwr_score_policy"]
    assert inventory.artifact_path == output
