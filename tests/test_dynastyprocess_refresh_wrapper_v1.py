from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import scripts.build_dynastyprocess_market_baseline_v1 as builder
import scripts.refresh_dynastyprocess_market_baseline_v1 as refresh
from scripts.build_dynastyprocess_market_baseline_v1 import (
    parse_args as parse_build_args,
)
from scripts.refresh_dynastyprocess_market_baseline_v1 import (
    parse_args as parse_refresh_args,
)
from src.connectors.dynastyprocess_connector import (
    DynastyProcessFetchError,
    FreshnessMetadata,
)
from src.services.dynastyprocess_generation_service import (
    OUTPUT_FILE_NAMES,
    expected_safe_root,
    resolve_current_generation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _freshness(root: Path) -> FreshnessMetadata:
    return FreshnessMetadata(
        nwr_fetch_timestamp="2026-07-29T00:00:00+00:00",
        upstream_scrape_date="2026-07-25",
        upstream_latest_commit_sha="synthetic",
        upstream_latest_commit_timestamp="2026-07-25T00:00:00+00:00",
        upstream_workflow_name="synthetic",
        upstream_expected_cron="synthetic",
        local_cache_path="synthetic-cache",
        derived_artifact_path=str(root),
        freshness_status="GREEN_CURRENT",
        freshness_age_days=4,
        previous_scrape_date="2026-07-18",
        previous_values_sha256="before",
        current_values_sha256="after",
        freshness_warning="",
    )


def _patch_synthetic_frames(monkeypatch: pytest.MonkeyPatch) -> None:
    joined = pd.DataFrame(
        [
            {
                "nwr_name": "Synthetic Player",
                "player": "Synthetic Player",
            }
        ]
    )
    monkeypatch.setattr(builder, "load_nwr_universe", lambda: (pd.DataFrame(), {}))
    monkeypatch.setattr(builder, "load_dp_players", lambda _path: pd.DataFrame())
    monkeypatch.setattr(builder, "join_dp_to_nwr", lambda *_args: joined)
    monkeypatch.setattr(
        builder,
        "build_pick_context",
        lambda _path: pd.DataFrame([{"pick_label": "2026 1.01"}]),
    )
    monkeypatch.setattr(
        builder,
        "build_crosswalk_audit",
        lambda _frame: pd.DataFrame([{"player": "Synthetic Player"}]),
    )
    monkeypatch.setattr(
        builder,
        "build_coverage",
        lambda *_args: pd.DataFrame([{"source_name": "synthetic"}]),
    )


def test_writer_publishes_all_five_only_inside_one_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    root = expected_safe_root(repo)
    _patch_synthetic_frames(monkeypatch)

    paths = builder.write_outputs(
        snapshot_dir=tmp_path / "snapshot",
        safe_root=root,
        freshness=_freshness(root),
        run_id="writer-test",
        generation_id="writer-test-generation",
        repo_root=repo,
    )
    snapshot = resolve_current_generation(root, repo_root=repo)

    assert len(paths) == 5
    assert {path.name for path in paths.values()} == set(OUTPUT_FILE_NAMES)
    assert {path.parent for path in paths.values()} == {
        root / "generations" / snapshot.generation_id
    }
    assert set(snapshot.payloads) == set(OUTPUT_FILE_NAMES)


def test_refresh_without_valid_cache_does_not_publish_partial_freshness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    root = expected_safe_root(repo)

    class FailingConnector:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def fetch_snapshot(self, **_kwargs: object):
            raise DynastyProcessFetchError("synthetic fetch failure")

    monkeypatch.setattr(refresh, "DynastyProcessConnector", FailingConnector)
    monkeypatch.setattr(refresh, "latest_cached_snapshot", lambda *_args, **_kwargs: None)

    exit_code = refresh.main(["--safe-root", str(root)])

    assert exit_code == 2
    assert not root.exists()


@pytest.mark.parametrize("parser", (parse_build_args, parse_refresh_args))
def test_cli_requires_explicit_safe_root_and_rejects_legacy_output_arg(parser) -> None:
    with pytest.raises(SystemExit):
        parser([])
    with pytest.raises(SystemExit):
        parser(["--output-dir", r"C:\unsafe"])


def test_scheduled_wrapper_uses_explicit_transactional_safe_root() -> None:
    wrapper = (REPO_ROOT / "scripts" / "run_dynastyprocess_refresh_task.ps1").read_text(
        encoding="utf-8"
    )
    normalized = wrapper.replace("/", "\\")

    assert "--safe-root $SafeRoot" in wrapper
    assert (
        "local_exports\\refresh_data\\dynastyprocess_market_baseline"
        in normalized
    )
    assert "current_generation.json" in wrapper
    assert "Import-Csv" not in wrapper
    assert "docs\\hq\\parallel_lanes\\dynastyprocess_market_baseline_20260622" not in normalized
