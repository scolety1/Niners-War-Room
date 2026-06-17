from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.mock_draft_regenerate_review_only_artifacts import run_regeneration_smoke


def test_regeneration_runner_writes_only_under_supplied_local_output(tmp_path) -> None:
    output_root = tmp_path / "local_exports" / "mock_draft" / "regeneration_smoke"

    result = run_regeneration_smoke(output_root=output_root)

    assert result.review_only is True
    assert result.artifact_paths["counts"].exists()
    assert result.artifact_paths["contamination_check"].exists()
    assert result.artifact_paths["manifest"].exists()
    assert all(str(path).startswith(str(output_root)) for path in result.artifact_paths.values())
    manifest = json.loads(result.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["real_market_data_imported"] is False
    assert manifest["promotion_status"] == "local_review_output_only_not_app_wired_not_promoted"
    assert Path(manifest["artifact_paths"]["scenario_variants"]).is_dir()
    assert Path(manifest["artifact_paths"]["manual_review_packet"]).is_dir()


def test_regeneration_runner_fails_closed_when_required_inputs_missing(tmp_path) -> None:
    missing = tmp_path / "missing_rookie_board.csv"

    with pytest.raises(FileNotFoundError, match="Missing required local review inputs"):
        run_regeneration_smoke(
            output_root=tmp_path / "local_exports" / "mock_draft" / "regen",
            required_inputs=[missing],
        )


def test_regeneration_runner_confirms_contamination_guardrails(tmp_path) -> None:
    output_root = tmp_path / "local_exports" / "mock_draft" / "regeneration_smoke"

    result = run_regeneration_smoke(output_root=output_root)

    checks = {row["check_name"]: row for row in result.contamination_rows}
    assert checks["local_only_output_root"]["passed"] is True
    assert checks["no_app_or_production_paths_written"]["passed"] is True
    assert checks["fake_market_fixture_only"]["passed"] is True
    assert checks["no_numeric_nwr_score_invented"]["passed"] is True
    assert result.manifest["fake_market_fixture"] == (
        "tests\\fixtures\\mock_draft\\fake_market_timing_rows.csv"
    )
    assert result.manifest["market_policy"] == "Fake market timing remains behavior-only."
