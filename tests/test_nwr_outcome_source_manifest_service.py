from __future__ import annotations

import csv

import pytest

from src.services.nwr_outcome_source_manifest_service import (
    audit_source_records_for_leakage,
    build_data_readiness_report,
    build_row_family_source_manifest,
    calculate_source_max_timestamp,
    classify_source,
    default_cutoff_definitions,
    future_window_status,
    label_available_date,
    raw_stat_field_mapping_contract,
    scoring_component_names,
    validate_raw_stat_mapping,
    write_source_manifest_exports,
)


def _csv(path, header, rows=None):
    rows = rows or []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_missing_source_timestamp_blocks_production_row_emission(tmp_path) -> None:
    source = tmp_path / "nwr_historical_week_scores.csv"
    _csv(source, ["player_id", "player_name", "position", "week_score_total"])

    manifest = build_row_family_source_manifest(
        row_family="all_player_pre_week1",
        source_paths=[source],
        cutoff=default_cutoff_definitions()["all_player_pre_week1"],
        required_source_families=("nwr_historical_week_scores",),
    )

    entry = manifest.source_entries[0]
    assert entry.classification == "allowed"
    assert entry.missing_timestamp is True
    assert entry.readiness_status == "blocked"
    assert manifest.readiness_status == "blocked"


def test_unknown_source_is_manual_review_required_not_allowed(tmp_path) -> None:
    source = tmp_path / "mystery_source.csv"
    _csv(
        source,
        ["player_id", "player_name", "position", "source_max_timestamp"],
        [["p1", "A", "WR", "2025-09-01"]],
    )

    family, classification, manual_review, note = classify_source(
        source,
        ("player_id", "player_name", "position", "source_max_timestamp"),
    )

    assert family == "unknown"
    assert classification == "unknown"
    assert manual_review is True
    assert "manual review" in note.lower()


def test_forbidden_source_remains_blocked(tmp_path) -> None:
    source = tmp_path / "fantasypros_adp.csv"
    _csv(source, ["player_id", "player_name", "position", "adp", "source_max_timestamp"])

    manifest = build_row_family_source_manifest(
        row_family="rookie_post_draft",
        source_paths=[source],
        cutoff=default_cutoff_definitions()["rookie_post_draft"],
        required_source_families=(),
    )

    entry = manifest.source_entries[0]
    assert entry.classification == "blocked"
    assert entry.readiness_status == "blocked"
    assert "Forbidden" not in entry.notes
    assert "Blocked" in entry.notes


def test_row_family_source_manifests_are_deterministic(tmp_path) -> None:
    source = tmp_path / "nwr_historical_week_scores.csv"
    _csv(
        source,
        ["player_id", "player_name", "position", "source_max_timestamp"],
        [["p1", "A", "WR", "2025-09-01"]],
    )
    kwargs = {
        "row_family": "all_player_pre_week1",
        "source_paths": [source],
        "cutoff": default_cutoff_definitions()["all_player_pre_week1"],
        "required_source_families": ("nwr_historical_week_scores",),
    }

    first = build_row_family_source_manifest(**kwargs)
    second = build_row_family_source_manifest(**kwargs)

    assert first.manifest_id == second.manifest_id
    assert first.manifest_hash == second.manifest_hash


def test_source_max_timestamp_is_calculated_correctly() -> None:
    rows = [
        {"source_max_timestamp": "2025-08-01"},
        {"source_max_timestamp": "2025-08-15T12:00:00"},
        {"source_max_timestamp": "2025-07-31"},
    ]

    assert calculate_source_max_timestamp(rows) == "2025-08-15T12:00:00"


def test_label_available_date_for_supported_windows() -> None:
    assert label_available_date(target_season=2026, target_horizon="year_1") == "2027-01-15"
    assert label_available_date(target_season=2026, target_horizon="next_year") == "2028-01-15"
    assert label_available_date(target_season=2026, target_horizon="next_3y") == "2029-01-15"
    assert label_available_date(target_season=2026, target_horizon="next_5y") == "2031-01-15"
    assert (
        label_available_date(
            target_season=2026,
            target_horizon="year_1",
            outcome_window="postseason",
        )
        == "2027-02-15"
    )


def test_censored_future_windows_remain_unavailable() -> None:
    assert (
        future_window_status(
            target_season=2026,
            target_horizon="next_3y",
            as_of_date="2028-01-15",
        )
        == "needs_data"
    )
    assert (
        future_window_status(
            target_season=2026,
            target_horizon="next_3y",
            as_of_date="2029-01-15",
        )
        == "ready"
    )


def test_raw_stat_field_mapping_covers_sprint_1_scoring_components() -> None:
    mapping = raw_stat_field_mapping_contract()

    assert set(scoring_component_names()) == set(mapping)
    for component, aliases in mapping.items():
        assert component
        assert aliases


def test_missing_required_scoring_component_is_reported() -> None:
    issues = validate_raw_stat_mapping(["player_id", "pass_yds", "passing_tds"])
    by_component = {issue.scoring_component: issue for issue in issues}

    assert by_component["pass_yds"].readiness_status == "ready"
    assert by_component["pass_td"].readiness_status == "ready"
    assert by_component["rush_yds"].readiness_status == "needs_data"
    assert "Missing required raw stat field" in by_component["rush_yds"].notes


def test_row_level_leakage_audit_blocks_missing_and_post_cutoff_timestamps() -> None:
    audits = audit_source_records_for_leakage(
        row_family="all_player_pre_week1",
        source_path="nwr_historical_week_scores.csv",
        source_family="nwr_historical_week_scores",
        input_snapshot_date="2025-09-01",
        records=[
            {"player_id": "p1", "source_max_timestamp": "2025-08-30"},
            {"player_id": "p2"},
            {"player_id": "p3", "source_max_timestamp": "2025-09-02"},
        ],
    )

    by_id = {audit.row_identifier: audit for audit in audits}
    assert by_id["p1"].readiness_status == "ready"
    assert by_id["p2"].issue_type == "missing_source_timestamp"
    assert by_id["p3"].issue_type == "post_cutoff_source_timestamp"


def test_row_level_leakage_audit_blocks_forbidden_fields() -> None:
    audits = audit_source_records_for_leakage(
        row_family="rookie_post_draft",
        source_path="official_draft_capital.csv",
        source_family="official_draft_capital",
        input_snapshot_date="2026-05-01",
        records=[
            {
                "player_id": "p1",
                "source_max_timestamp": "2026-04-30",
                "market_rank": "12",
            }
        ],
    )

    assert audits[0].readiness_status == "blocked"
    assert audits[0].issue_type == "forbidden_source_or_field"


def test_readiness_report_blocks_before_base_rates_when_data_missing(tmp_path) -> None:
    source = tmp_path / "nwr_historical_week_scores.csv"
    _csv(source, ["player_id", "player_name", "position"], [["p1", "A", "WR"]])
    manifest = build_row_family_source_manifest(
        row_family="all_player_pre_week1",
        source_paths=[source],
        cutoff=default_cutoff_definitions()["all_player_pre_week1"],
        required_source_families=("nwr_historical_week_scores",),
    )
    mapping_issues = validate_raw_stat_mapping(["player_id", "pass_yds"])
    report = build_data_readiness_report(
        manifests=[manifest],
        leakage_audits=[],
        raw_stat_mapping_issues=mapping_issues,
    )

    assert report.readiness_status == "blocked"
    assert report.blocked_manifest_count == 1
    assert report.missing_mapping_count > 0


def test_write_source_manifest_exports_are_read_only_to_requested_folder(tmp_path) -> None:
    source = tmp_path / "nwr_historical_week_scores.csv"
    _csv(
        source,
        ["player_id", "player_name", "position", "source_max_timestamp"],
        [["p1", "A", "WR", "2025-08-30"]],
    )
    manifest = build_row_family_source_manifest(
        row_family="all_player_pre_week1",
        source_paths=[source],
        cutoff=default_cutoff_definitions()["all_player_pre_week1"],
        required_source_families=("nwr_historical_week_scores",),
    )
    audits = audit_source_records_for_leakage(
        row_family="all_player_pre_week1",
        source_path=source,
        source_family="nwr_historical_week_scores",
        input_snapshot_date="2025-09-01",
        records=[{"player_id": "p1", "source_max_timestamp": "2025-08-30"}],
    )
    mapping = validate_raw_stat_mapping(["pass_yds", "pass_td", "rush_yds"])
    report = build_data_readiness_report(
        manifests=[manifest],
        leakage_audits=audits,
        raw_stat_mapping_issues=mapping,
    )

    output = tmp_path / "exports"
    write_source_manifest_exports(
        output_dir=output,
        manifests=[manifest],
        leakage_audits=audits,
        raw_stat_mapping_issues=mapping,
        readiness_report=report,
    )

    assert (output / "row_family_source_manifests.csv").exists()
    assert (output / "source_manifest_entries.csv").exists()
    assert (output / "row_level_leakage_audit.csv").exists()
    assert (output / "raw_stat_mapping_readiness.csv").exists()
    assert (output / "data_readiness_report.csv").exists()


def test_unsupported_row_family_is_rejected(tmp_path) -> None:
    source = tmp_path / "nwr_historical_week_scores.csv"
    _csv(source, ["player_id", "source_max_timestamp"], [["p1", "2025-08-30"]])

    with pytest.raises(ValueError, match="Unsupported row_family"):
        build_row_family_source_manifest(
            row_family="in_season",
            source_paths=[source],
            cutoff=default_cutoff_definitions()["all_player_pre_week1"],
        )
