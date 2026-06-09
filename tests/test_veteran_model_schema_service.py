from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.veteran_model_schema_service import (
    VETERAN_OPTIONAL_SOURCE_TABLES,
    VETERAN_SOURCE_TABLES,
    build_veteran_schema_report,
)
from src.services.veteran_model_service import run_veteran_model_from_dir

SAMPLE_DIR = Path("sample_data/veteran_model_v1")


def test_veteran_source_tables_exist_and_outputs_are_not_committed() -> None:
    for filename in VETERAN_SOURCE_TABLES:
        assert (SAMPLE_DIR / filename).exists()
    for filename in VETERAN_OPTIONAL_SOURCE_TABLES:
        assert (SAMPLE_DIR / filename).exists()
    assert not (SAMPLE_DIR / "veteran_model_outputs.csv").exists()


def test_sample_veteran_schema_fixture_validates_cleanly() -> None:
    report = build_veteran_schema_report(SAMPLE_DIR)

    assert not report.has_errors
    assert report.warning_count == 0
    assert len(report.players) == 12
    assert len(report.registry) == 66
    assert sum(1 for row in report.registry if row.scoring_status == "active_v1") == 20
    assert len(report.feature_scores) == 158
    assert {player.position for player in report.players} == {"QB", "RB", "WR", "TE"}


def test_veteran_registry_tracks_future_policy_without_affecting_v1_scores() -> None:
    report = build_veteran_schema_report(SAMPLE_DIR)
    future_features = {
        (row.position, row.feature_name)
        for row in report.registry
        if row.scoring_status == "future_candidate"
    }
    rejected_features = {
        (row.position, row.feature_name)
        for row in report.registry
        if row.scoring_status == "rejected"
    }

    assert ("WR", "route_participation") in future_features
    assert ("RB", "touch_share") in future_features
    assert ("TE", "target_earning") in future_features
    assert ("QB", "rushing_value") in future_features
    assert ("QB", "league_rank_as_talent") in rejected_features
    assert ("TE", "generic_te_scarcity") in rejected_features


def test_source_catalog_tracks_phase_9_authority_and_context_policy() -> None:
    report = build_veteran_schema_report(SAMPLE_DIR)
    sources = {source.source_key: source for source in report.sources}

    assert sources["sleeper_roster_2026"].source_domain == "league_state"
    assert sources["sleeper_roster_2026"].authority_tier == "tier_a_local_canonical"
    assert sources["league_rank_pdf_2026"].source_domain == "league_rank"
    assert sources["market_rank_fixture_2026"].scoring_context == "generic_dynasty"
    assert sources["projection_fixture_2026"].scoring_context == "custom_lve"
    assert sources["manual_fixture_2026"].is_active is True


def test_source_catalog_requires_scoring_context_for_market_and_projection_sources(
    tmp_path: Path,
) -> None:
    pack = _copy_sample(tmp_path)
    source_path = pack / "veteran_source_catalog.csv"
    rows = _read_csv(source_path)
    rows[2]["scoring_context"] = ""
    _write_csv(source_path, rows)

    report = build_veteran_schema_report(pack)

    assert (
        "error",
        "Market/projection source is missing scoring context.",
    ) in _issue_pairs(report)


def test_source_catalog_rejects_duplicate_active_domain_priority(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    source_path = pack / "veteran_source_catalog.csv"
    rows = _read_csv(source_path)
    rows[1]["source_domain"] = rows[0]["source_domain"]
    rows[1]["priority_rank"] = rows[0]["priority_rank"]
    _write_csv(source_path, rows)

    report = build_veteran_schema_report(pack)

    assert (
        "error",
        "Active source priority is duplicated within a source domain.",
    ) in _issue_pairs(report)


def test_future_candidate_core_features_do_not_create_missing_core_warnings() -> None:
    report = build_veteran_schema_report(SAMPLE_DIR)

    assert not any(
        issue.issue == "Missing core veteran feature."
        and issue.field_name in {"route_participation", "touch_share", "target_earning"}
        for issue in report.issues
    )


def test_validation_rejects_duplicate_veteran_player_ids(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    player_path = pack / "veteran_player_inputs.csv"
    rows = _read_csv(player_path)
    rows.append(dict(rows[0]))
    _write_csv(player_path, rows)

    report = build_veteran_schema_report(pack)

    assert ("error", "Duplicate player_id.") in _issue_pairs(report)


def test_validation_rejects_invalid_normalized_feature_score(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    score_path = pack / "veteran_feature_scores.csv"
    rows = _read_csv(score_path)
    rows[0]["normalized_score"] = "101"
    _write_csv(score_path, rows)

    report = build_veteran_schema_report(pack)

    assert ("error", "normalized_score must be numeric in range 0-100.") in _issue_pairs(report)


def test_validation_warns_for_missing_core_veteran_feature(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    score_path = pack / "veteran_feature_scores.csv"
    rows = [
        row
        for row in _read_csv(score_path)
        if not (
            row["player_id"] == "lamar_jackson"
            and row["feature_name"] == "lve_projection_value"
        )
    ]
    _write_csv(score_path, rows)

    report = build_veteran_schema_report(pack)

    assert not report.has_errors
    assert ("warning", "Missing core veteran feature.") in _issue_pairs(report)


def test_validation_rejects_missing_source_provenance(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    score_path = pack / "veteran_feature_scores.csv"
    rows = _read_csv(score_path)
    rows[0]["source_key"] = ""
    _write_csv(score_path, rows)

    report = build_veteran_schema_report(pack)

    assert ("error", "Missing required value.") in _issue_pairs(report)
    assert ("error", "Feature score is missing source provenance.") in _issue_pairs(report)


def test_validation_rejects_user_override_without_reason(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    score_path = pack / "veteran_feature_scores.csv"
    rows = _read_csv(score_path)
    rows[0]["is_user_override"] = "true"
    rows[0]["override_reason"] = ""
    _write_csv(score_path, rows)

    report = build_veteran_schema_report(pack)

    assert (
        "error",
        "User override does not include an override reason.",
    ) in _issue_pairs(report)


def test_manual_override_applies_only_with_matching_audit_note(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    _write_csv(
        pack / "veteran_manual_overrides.csv",
        [
            _override_row(
                override_id="override_lamar_start_security",
                player_id="lamar_jackson",
                position="QB",
                feature_name="start_security",
                override_value="55",
            )
        ],
    )
    audit_rows = _read_csv(pack / "veteran_audit_notes.csv")
    audit_rows.append(
        {
            "note_id": "note_lamar_role_override",
            "season": "2026",
            "player_id": "lamar_jackson",
            "feature_name": "start_security",
            "note_scope": "override",
            "note_text": "Manual role-security haircut for deterministic override test.",
            "source_key": "manual_fixture_2026",
            "affects_score": "true",
            "created_at": "2026-05-05T09:00:00-06:00",
        }
    )
    _write_csv(pack / "veteran_audit_notes.csv", audit_rows)

    report = build_veteran_schema_report(pack)
    score = next(
        row
        for row in report.feature_scores
        if row.player_id == "lamar_jackson" and row.feature_name == "start_security"
    )
    run = run_veteran_model_from_dir(pack)
    lamar = next(score for score in run.scores if score.player_id == "lamar_jackson")

    assert not report.has_errors
    assert score.normalized_score == 55.0
    assert score.is_user_override is True
    assert "role_fragility" in lamar.risk_flags
    assert "review_needed_manual_override" in lamar.warning_reasons


def test_manual_override_requires_old_value_and_explicit_self_approval(
    tmp_path: Path,
) -> None:
    pack = _copy_sample(tmp_path)
    row = _override_row(
        override_id="override_lamar_missing_guardrail",
        player_id="lamar_jackson",
        position="QB",
        feature_name="start_security",
        override_value="55",
    )
    row["old_value"] = ""
    row["self_approved"] = "false"
    _write_csv(pack / "veteran_manual_overrides.csv", [row])

    report = build_veteran_schema_report(pack)

    assert (
        "error",
        "Manual override is missing required audit provenance.",
    ) in _issue_pairs(report)
    assert (
        "error",
        "Self-approved override is not explicitly marked.",
    ) in _issue_pairs(report)


def test_manual_override_requires_approval_before_active(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    row = _override_row(
        override_id="override_lamar_pending",
        player_id="lamar_jackson",
        position="QB",
        feature_name="start_security",
        override_value="55",
    )
    row["review_status"] = "pending"
    _write_csv(pack / "veteran_manual_overrides.csv", [row])

    report = build_veteran_schema_report(pack)

    assert ("error", "Active override is not approved.") in _issue_pairs(report)


def test_inactive_override_may_share_a_superseded_target(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    active = _override_row(
        override_id="override_lamar_active_target",
        player_id="lamar_jackson",
        position="QB",
        feature_name="start_security",
        override_value="55",
    )
    inactive = {
        **_override_row(
            override_id="override_lamar_inactive_target",
            player_id="lamar_jackson",
            position="QB",
            feature_name="start_security",
            override_value="60",
        ),
        "status": "inactive",
        "review_status": "expired",
    }
    _write_csv(pack / "veteran_manual_overrides.csv", [active, inactive])
    audit_rows = _read_csv(pack / "veteran_audit_notes.csv")
    audit_rows.append(
        {
            "note_id": "note_lamar_superseded_override",
            "season": "2026",
            "player_id": "lamar_jackson",
            "feature_name": "start_security",
            "note_scope": "override",
            "note_text": "Active override plus expired historical row for same feature.",
            "source_key": "manual_fixture_2026",
            "affects_score": "true",
            "created_at": "2026-05-05T09:00:00-06:00",
        }
    )
    _write_csv(pack / "veteran_audit_notes.csv", audit_rows)

    report = build_veteran_schema_report(pack)

    assert not report.has_errors


def test_manual_override_requires_matching_score_affecting_audit_note(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    _write_csv(
        pack / "veteran_manual_overrides.csv",
        [
            _override_row(
                override_id="override_lamar_no_note",
                player_id="lamar_jackson",
                position="QB",
                feature_name="role_security",
                override_value="55",
            )
        ],
    )

    report = build_veteran_schema_report(pack)

    assert (
        "error",
        "Active override has no matching score-affecting audit note.",
    ) in _issue_pairs(report)


def test_manual_override_blocks_direct_final_score_override(tmp_path: Path) -> None:
    pack = _copy_sample(tmp_path)
    _write_csv(
        pack / "veteran_manual_overrides.csv",
        [
            {
                **_override_row(
                    override_id="override_lamar_final_score",
                    player_id="lamar_jackson",
                    position="QB",
                    feature_name="role_security",
                    override_value="99",
                ),
                "target_field": "keeper_score",
            }
        ],
    )

    report = build_veteran_schema_report(pack)

    assert ("error", "Unsupported target_field.") in _issue_pairs(report)


def _copy_sample(tmp_path: Path) -> Path:
    target = tmp_path / "veteran_model_v1"
    shutil.copytree(SAMPLE_DIR, target)
    return target


def _override_row(
    *,
    override_id: str,
    player_id: str,
    position: str,
    feature_name: str,
    override_value: str,
) -> dict[str, str]:
    return {
        "override_id": override_id,
        "season": "2026",
        "player_id": player_id,
        "position": position,
        "feature_name": feature_name,
        "target_field": "normalized_score",
        "old_value": "90.0",
        "override_value": override_value,
        "override_type": "data_correction",
        "reason_code": "other",
        "source_key": "manual_fixture_2026",
        "override_reason": "Deterministic test override with documented rationale.",
        "provenance": "test_fixture",
        "requested_by": "codex_test",
        "approved_by": "codex_test",
        "self_approved": "true",
        "review_status": "approved",
        "status": "active",
        "created_at": "2026-05-05T09:00:00-06:00",
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _issue_pairs(report) -> set[tuple[str, str]]:
    return {(issue.severity, issue.issue) for issue in report.issues}
