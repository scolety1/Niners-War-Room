from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from src.services.nwr_outcome_internal_model_package_service import (
    PACKAGE_METADATA,
    _validate_metadata_contract,
    canonical_feature_vector,
    export_sprint_5t_internal_logistic_package,
    fit_regularized_logistic,
    forbidden_feature_scan,
    load_internal_dataset,
    validate_feature_contract,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    base = repo / "local_exports/outcome_probability/sprint_5n_broader_historical_rebuild"
    snapshots: list[dict[str, object]] = []
    labels: list[dict[str, object]] = []
    for season in (2023, 2024):
        for index in range(24):
            row_id = f"row-{season}-{index}"
            position = ("QB", "RB", "WR", "TE")[index % 4]
            feature_vector = {
                "age_at_snapshot": 24 + (index % 8),
                "position": position,
                "experience_at_snapshot": index % 6,
                "prior_nwr_ppg": 4.0 + index,
                "prior_nwr_finish_rank": 80 - index,
                "prior_games_played": 8 + (index % 9),
                "prior_rushing_first_downs": index % 5,
                "prior_receiving_first_downs": (index + 1) % 6,
                "prior_receptions": index * 2,
                "prior_rushing_yards": index * 11,
                "prior_receiving_yards": index * 13,
                "prior_passing_yards": index * 17,
            }
            snapshots.append(
                {
                    "row_id": row_id,
                    "player_id": f"player-{season}-{index}",
                    "row_type": "all_player_pre_week1",
                    "cutoff_id": f"PRE_WK1_{season}",
                    "input_snapshot_date": f"{season}-09-01",
                    "source_max_timestamp": f"{season}-09-01",
                    "feature_vector": json.dumps(feature_vector, sort_keys=True),
                    "missingness_mask": "{}",
                    "source_manifest": "fixture_manifest",
                    "snapshot_hash": f"hash-{season}-{index}",
                    "legality_status": "valid",
                    "manual_review_status": "not_required",
                }
            )
            event = index < 4
            labels.append(
                {
                    "row_id": row_id,
                    "player_id": f"player-{season}-{index}",
                    "player_name": f"Player {season} {index}",
                    "position": position,
                    "cohort": "fixture",
                    "row_type": "all_player_pre_week1",
                    "target_season": season,
                    "cutoff_id": f"PRE_WK1_{season}",
                    "trainability_status": "trainable_now",
                    "label_source": "fixture",
                    "same_year_difference_maker": str(event).lower(),
                    "same_year_starter": str(index < 8).lower(),
                    "same_year_useful": str(index < 12).lower(),
                    "same_year_replacement_or_bust": str(index >= 12).lower(),
                    "next_year_starter": "false",
                    "next_year_label_status": "fixture",
                    "position_rank": index + 1,
                    "available_outcomes": "|".join(
                        (
                            "same_year_difference_maker",
                            "same_year_starter",
                            "same_year_useful",
                            "same_year_replacement_or_bust",
                        )
                    ),
                    "missing_or_censored_outcomes": "",
                    "block_reason": "",
                }
            )
    _write_csv(base / "broader_historical_feature_snapshots.csv", snapshots)
    _write_csv(base / "broader_historical_label_linkage.csv", labels)
    return repo


def test_metadata_contract_and_output_blocks(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    output = tmp_path / "out"

    result = export_sprint_5t_internal_logistic_package(repo_root=repo, output_dir=output)

    metadata = result["metadata"]
    assert metadata["promotion_allowed"] is False
    assert metadata["player_output_block"] is True
    assert metadata["app_output_block"] is True
    assert metadata["calibration_allowed"] is False
    assert metadata["production_artifact"] is False
    assert metadata["random_seed"] == "not_used_deterministic_gradient_descent"
    assert metadata["package_created_at_utc"]
    assert metadata["code_version_git_commit"]
    assert "next_year_starter" not in metadata["outcomes"]


def test_metadata_contract_blocks_bad_governance_flags() -> None:
    valid_metadata = {
        **PACKAGE_METADATA,
        "feature_list": ["age_at_snapshot"],
        "forbidden_feature_scan_passed": True,
        "training_row_count": 1,
        "test_row_count": 1,
        "random_seed": "not_used_deterministic_gradient_descent",
        "package_created_at_utc": "2026-06-12T00:00:00Z",
        "code_version_git_commit": "abc123",
    }

    for field, bad_value in (
        ("promotion_allowed", True),
        ("player_output_block", False),
        ("app_output_block", False),
        ("calibration_allowed", True),
        ("production_artifact", True),
        ("feature_lineage_required", False),
        ("renamed_feature_schema_required", False),
        ("forbidden_feature_scan_passed", False),
    ):
        metadata = {**valid_metadata, field: bad_value}
        with pytest.raises(ValueError):
            _validate_metadata_contract(metadata)


def test_missing_metadata_blocks_package_contract() -> None:
    metadata = {
        **PACKAGE_METADATA,
        "feature_list": ["age_at_snapshot"],
        "forbidden_feature_scan_passed": True,
        "training_row_count": 1,
        "test_row_count": 1,
        "random_seed": "not_used_deterministic_gradient_descent",
        "package_created_at_utc": "2026-06-12T00:00:00Z",
    }

    with pytest.raises(ValueError, match="code_version_git_commit"):
        _validate_metadata_contract(metadata)


def test_old_ambiguous_feature_names_fail_contract() -> None:
    with pytest.raises(ValueError, match="forbidden or ambiguous"):
        validate_feature_contract(["prior_nwr_ppg", "age_at_snapshot"])


def test_canonical_feature_vector_renames_legacy_snapshot_fields() -> None:
    canonical = canonical_feature_vector(
        {
            "prior_nwr_ppg": 12.0,
            "prior_nwr_finish_rank": 20,
            "prior_games_played": 16,
            "prior_rushing_yards": 400,
        }
    )

    assert "prior_nwr_ppg" not in canonical
    assert "prior_nwr_finish_rank" not in canonical
    assert canonical["prior_season_nwr_ppg"] == 12.0
    assert canonical["prior_season_nwr_finish_rank"] == 20
    assert canonical["prior_completed_season_games_played"] == 16
    assert canonical["prior_completed_season_rushing_yards"] == 400


def test_forbidden_scan_catches_public_market_projection_fields() -> None:
    rows = forbidden_feature_scan(
        [
            "prior_completed_season_games_played",
            "adp",
            "market_rank",
            "rotowire_projection",
            "legacy_private_score",
        ]
    )

    blockers = {row["feature_name"] for row in rows if row["blocker"] == "yes"}
    assert blockers == {"adp", "market_rank", "rotowire_projection", "legacy_private_score"}


def test_next_year_starter_is_blocked(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    rows = load_internal_dataset(
        feature_snapshot_path=repo
        / "local_exports/outcome_probability/sprint_5n_broader_historical_rebuild"
        / "broader_historical_feature_snapshots.csv",
        label_linkage_path=repo
        / "local_exports/outcome_probability/sprint_5n_broader_historical_rebuild"
        / "broader_historical_label_linkage.csv",
    )

    with pytest.raises(ValueError, match="not allowed"):
        fit_regularized_logistic(
            rows=rows,
            outcome="next_year_starter",
            feature_list=["age_at_snapshot"],
            train_season=2023,
            test_season=2024,
        )


def test_exported_diagnostics_have_no_player_identifiers_or_probabilities(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    output = tmp_path / "out"

    export_sprint_5t_internal_logistic_package(repo_root=repo, output_dir=output)

    forbidden_headers = {"player_id", "player_name", "row_id", "predicted_probability"}
    for path in output.glob("*.csv"):
        header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
        assert not forbidden_headers.intersection(header), path.name
    assert not (output / "model.pkl").exists()
    assert not (output / "model.joblib").exists()
    assert not (output / "player_level_predictions.csv").exists()
    assert not (output / "app_probability_table.csv").exists()


def test_app_and_ranking_modules_do_not_import_internal_package_service() -> None:
    repo = Path(__file__).resolve().parents[1]
    searched_roots = [repo / "app", repo / "pages", repo / "streamlit_app.py"]
    forbidden_terms = (
        "nwr_outcome_internal_model_package_service",
        "sprint_5t_internal_logistic_package",
        "internal_logistic_package_metadata",
    )
    offenders: list[str] = []
    for root in searched_roots:
        if root.is_file():
            files = [root]
        elif root.is_dir():
            files = list(root.rglob("*.py"))
        else:
            files = []
        for path in files:
            text = path.read_text(encoding="utf-8")
            if any(term in text for term in forbidden_terms):
                offenders.append(str(path.relative_to(repo)))

    assert offenders == []
