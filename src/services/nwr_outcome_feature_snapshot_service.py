from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.services.nwr_outcome_training_row_service import (
    FeatureLegalityAudit,
    FeatureLegalityIssue,
    FeatureSnapshot,
    PredictionSnapshot,
    SourceAllowlistRule,
    generate_row_id,
    missingness_mask,
    snapshot_hash,
    validate_feature_legality,
)

SUPPORTED_FEATURE_SNAPSHOT_ROW_TYPES = (
    "all_player_pre_week1",
    "offseason_carryover",
    "rookie_post_draft",
)

CUTOFF_TEMPLATES = {
    "all_player_pre_week1": "{season}-09-01",
    "offseason_carryover": "{season}-02-15",
    "rookie_post_draft": "{season}-05-01",
}

FORBIDDEN_SOURCE_FAMILIES = (
    "player_stats_rare_components",
    "play_by_play_rare_components",
    "historical_rookie_outcomes",
    "prior_league_draft_history",
    "rotowire_projections",
    "rotowire_rankings",
    "rotowire_outlooks",
    "rotowire_values",
    "market_rank",
    "league_rank",
    "prior_fantasy_draft_history",
    "legacy_private_score",
)

ALLOWED_SOURCE_FAMILIES = (
    "stable_identity_metadata",
    "truth_set_scoring_season",
    "truth_set_scoring_week",
    "usage_season",
    "usage_week",
    "snap_share_season",
    "snap_share_week",
    "official_draft_capital",
)

SOURCE_FAMILY_ROW_TYPES = {
    "stable_identity_metadata": SUPPORTED_FEATURE_SNAPSHOT_ROW_TYPES,
    "truth_set_scoring_season": ("all_player_pre_week1", "offseason_carryover"),
    "truth_set_scoring_week": ("all_player_pre_week1", "offseason_carryover"),
    "usage_season": ("all_player_pre_week1", "offseason_carryover"),
    "usage_week": ("all_player_pre_week1", "offseason_carryover"),
    "snap_share_season": ("all_player_pre_week1", "offseason_carryover"),
    "snap_share_week": ("all_player_pre_week1", "offseason_carryover"),
    "official_draft_capital": ("rookie_post_draft",),
}

FEATURE_RENAME_MAP = {
    "prior_nwr_ppg": "prior_season_nwr_ppg",
    "prior_nwr_finish_rank": "prior_season_nwr_finish_rank",
    "prior_games": "prior_completed_season_games",
    "prior_games_played": "prior_completed_season_games_played",
    "prior_games_active": "prior_completed_season_games_active",
    "prior_rushing_first_downs": "prior_completed_season_rushing_first_downs",
    "prior_receiving_first_downs": "prior_completed_season_receiving_first_downs",
    "prior_receptions": "prior_completed_season_receptions",
    "prior_rushing_yards": "prior_completed_season_rushing_yards",
    "prior_receiving_yards": "prior_completed_season_receiving_yards",
    "prior_passing_yards": "prior_completed_season_passing_yards",
}

PRIOR_COMPLETED_SEASON_POLICY_ID = "completed_prior_season_stats_available_feb15_v1"
STABLE_IDENTITY_POLICY_ID = "stable_identity_metadata_manifest_v1"


@dataclass(frozen=True)
class FeatureSnapshotCandidate:
    row_id: str
    player_id: str
    player_name: str
    position: str
    row_type: str
    cutoff_id: str
    input_snapshot_date: str
    source_max_timestamp: str
    feature_vector: dict[str, Any]
    missingness_mask: dict[str, bool]
    feature_lineage: dict[str, dict[str, str]]
    source_manifest: str
    snapshot_hash: str
    legality_status: str
    manual_review_status: str
    legality_issues: tuple[FeatureLegalityIssue, ...] = ()


@dataclass(frozen=True)
class SnapshotBuildResult:
    row_family: str
    attempted_rows: int
    emitted_rows: int
    blocked_rows: int
    readiness_status: str
    notes: str
    candidates: tuple[FeatureSnapshotCandidate, ...]
    legality_audits: tuple[dict[str, str], ...]


def cutoff_date(row_type: str, season: int) -> str:
    _require_supported_row_type(row_type)
    return CUTOFF_TEMPLATES[row_type].format(season=season)


def canonical_feature_name(feature_name: str) -> str:
    return FEATURE_RENAME_MAP.get(feature_name, feature_name)


def narrow_feature_source_allowlist() -> dict[str, SourceAllowlistRule]:
    rules: dict[str, SourceAllowlistRule] = {
        source: SourceAllowlistRule(
            source_family=source,
            allowed_for_features=True,
            blocked_fields=(),
            notes="Allowed only for Sprint 5E narrow feature snapshots when cutoff checks pass.",
        )
        for source in ALLOWED_SOURCE_FAMILIES
    }
    for source in FORBIDDEN_SOURCE_FAMILIES:
        rules[source] = SourceAllowlistRule(
            source_family=source,
            allowed_for_features=False,
            notes="Blocked from prediction-time feature snapshots.",
        )
    return rules


def build_feature_snapshot_candidate(
    *,
    player_id: str,
    player_name: str,
    position: str,
    row_type: str,
    target_season: int,
    target_horizon: str,
    features: Sequence[FeatureSnapshot],
    source_manifest: str,
    manual_review_status: str = "not_required",
    parser_version: str = "nwr_outcome_feature_snapshot_v1",
    input_snapshot_date: str | None = None,
    cutoff_id: str | None = None,
) -> FeatureSnapshotCandidate:
    _require_supported_row_type(row_type)
    input_snapshot_date = input_snapshot_date or cutoff_date(row_type, target_season)
    canonical_features = _canonicalize_features(features)
    prediction_snapshot = PredictionSnapshot(
        cutoff_id=cutoff_id or f"{row_type}_{target_season}",
        row_type=row_type,
        prediction_date=input_snapshot_date,
        input_snapshot_date=input_snapshot_date,
        label_available_date=f"{target_season + 1}-01-15",
        target_season=target_season,
        target_horizon=target_horizon,
        parser_version=parser_version,
        source_manifest=source_manifest,
    )
    feature_vector = {feature.feature_name: feature.value for feature in canonical_features}
    feature_lineage = feature_lineage_metadata(
        canonical_features,
        target_season=target_season,
        prediction_cutoff=input_snapshot_date,
        source_manifest=source_manifest,
    )
    issues = list(
        validate_snapshot_feature_legality(
            row_type=row_type,
            features=canonical_features,
            input_snapshot_date=input_snapshot_date,
            label_available_date=prediction_snapshot.label_available_date,
        ).issues
    )
    row_id = generate_row_id(
        row_type=row_type,
        player_id=player_id,
        position=position,
        cutoff_id=prediction_snapshot.cutoff_id,
        input_snapshot_date=input_snapshot_date,
        target_season=target_season,
        target_horizon=target_horizon,
    )
    source_max_timestamp = _source_max_timestamp(canonical_features, input_snapshot_date)
    payload = {
        "row_id": row_id,
        "player_id": player_id,
        "player_name": player_name,
        "position": position.upper(),
        "row_type": row_type,
        "cutoff_id": prediction_snapshot.cutoff_id,
        "input_snapshot_date": input_snapshot_date,
        "source_max_timestamp": source_max_timestamp,
        "feature_vector": feature_vector,
        "missingness_mask": missingness_mask(feature_vector),
        "feature_lineage": feature_lineage,
        "source_manifest": source_manifest,
        "manual_review_status": manual_review_status,
    }
    return FeatureSnapshotCandidate(
        row_id=row_id,
        player_id=player_id,
        player_name=player_name,
        position=position.upper(),
        row_type=row_type,
        cutoff_id=prediction_snapshot.cutoff_id,
        input_snapshot_date=input_snapshot_date,
        source_max_timestamp=source_max_timestamp,
        feature_vector=feature_vector,
        missingness_mask=missingness_mask(feature_vector),
        feature_lineage=feature_lineage,
        source_manifest=source_manifest,
        snapshot_hash=snapshot_hash(payload),
        legality_status="valid" if not issues else "blocked",
        manual_review_status=manual_review_status,
        legality_issues=tuple(issues),
    )


def feature_lineage_metadata(
    features: Sequence[FeatureSnapshot],
    *,
    target_season: int,
    prediction_cutoff: str,
    source_manifest: str,
) -> dict[str, dict[str, str]]:
    return {
        feature.feature_name: _feature_lineage_metadata(
            feature,
            target_season=target_season,
            prediction_cutoff=prediction_cutoff,
            source_manifest=source_manifest,
        )
        for feature in features
    }


def _canonicalize_features(features: Sequence[FeatureSnapshot]) -> tuple[FeatureSnapshot, ...]:
    canonical: list[FeatureSnapshot] = []
    for feature in features:
        canonical_name = canonical_feature_name(feature.feature_name)
        if canonical_name == feature.feature_name:
            canonical.append(feature)
        else:
            canonical.append(replace(feature, feature_name=canonical_name))
    return tuple(canonical)


def _feature_lineage_metadata(
    feature: FeatureSnapshot,
    *,
    target_season: int,
    prediction_cutoff: str,
    source_manifest: str,
) -> dict[str, str]:
    source_season = _lineage_value(feature.lineage, "source_season")
    if not source_season and _is_prior_completed_season_feature(feature):
        source_season = str(target_season - 1)
    if not source_season:
        source_season = "not_season_bound"

    derived_availability = _lineage_value(feature.lineage, "derived_availability_date")
    if not derived_availability and _is_prior_completed_season_feature(feature):
        derived_availability = _prior_completed_season_availability_date(target_season)
    if not derived_availability:
        derived_availability = feature.source_available_at or prediction_cutoff

    source_policy_id = _lineage_value(feature.lineage, "source_policy_id")
    if not source_policy_id and _is_prior_completed_season_feature(feature):
        source_policy_id = PRIOR_COMPLETED_SEASON_POLICY_ID
    if not source_policy_id and feature.source_family == "stable_identity_metadata":
        source_policy_id = STABLE_IDENTITY_POLICY_ID
    if not source_policy_id:
        source_policy_id = source_manifest

    strictly_before = _source_season_before_target(source_season, target_season)
    availability_ok = _timestamp_on_or_before(derived_availability, prediction_cutoff)
    blocked_supplement = feature.source_family in FORBIDDEN_SOURCE_FAMILIES
    same_season = source_season == str(target_season)
    legality_status = "allowed_prior_completed_season_fact"
    if blocked_supplement:
        legality_status = "blocked_for_modeling"
    elif same_season:
        legality_status = "blocked_same_season_leakage"
    elif not availability_ok:
        legality_status = "manual_review_required"

    return {
        "source_season": source_season,
        "target_season": str(target_season),
        "derived_availability_date": derived_availability,
        "prediction_cutoff": prediction_cutoff,
        "feature_family": _feature_family(feature),
        "legality_status": legality_status,
        "source_manifest_id_or_policy_id": source_policy_id,
        "source_season_strictly_before_target": strictly_before,
        "derived_availability_before_cutoff": "yes" if availability_ok else "no",
        "target_window_overlap": "no" if not same_season else "yes",
        "same_season_final_stat_leakage": "yes" if same_season else "no",
        "label_supplement_source_as_feature": "yes" if blocked_supplement else "no",
        "notes": _lineage_notes(feature),
    }


def _is_prior_completed_season_feature(feature: FeatureSnapshot) -> bool:
    return (
        feature.feature_name.startswith("prior_completed_season_")
        or feature.feature_name.startswith("prior_season_nwr_")
    )


def _feature_family(feature: FeatureSnapshot) -> str:
    if feature.feature_name.startswith("prior_season_nwr_"):
        return "prior_nwr_scoring"
    if feature.feature_name.startswith("prior_completed_season_"):
        return "prior_completed_season_stat"
    if feature.source_family == "stable_identity_metadata":
        return "stable_identity_metadata"
    if feature.source_family == "official_draft_capital":
        return "factual_draft_capital"
    return feature.source_family


def _lineage_notes(feature: FeatureSnapshot) -> str:
    if feature.feature_name.startswith("prior_season_nwr_"):
        return (
            "Completed prior-season NWR scoring feature; not same-season target "
            "label and not an imported public fantasy total."
        )
    if feature.feature_name.startswith("prior_completed_season_"):
        return "Completed prior-season factual production feature."
    if feature.source_family == "stable_identity_metadata":
        return "Stable identity metadata; not a scoring label."
    if feature.source_family in FORBIDDEN_SOURCE_FAMILIES:
        return "Blocked source family for prediction-time features."
    return "Feature lineage metadata carried through snapshot contract."


def _lineage_value(lineage: Sequence[str], key: str) -> str:
    prefix = f"{key}="
    for item in lineage:
        if item.startswith(prefix):
            return item.removeprefix(prefix)
    return ""


def _source_season_before_target(source_season: str, target_season: int) -> str:
    if source_season == "not_season_bound":
        return "not_applicable"
    try:
        return "yes" if int(source_season) < target_season else "no"
    except ValueError:
        return "unknown"


def _timestamp_on_or_before(timestamp: str, cutoff: str) -> bool:
    if not timestamp:
        return False
    return timestamp <= cutoff


def _prior_completed_season_availability_date(target_season: int) -> str:
    return f"{target_season}-02-15"


def validate_snapshot_feature_legality(
    *,
    row_type: str,
    features: Sequence[FeatureSnapshot],
    input_snapshot_date: str,
    label_available_date: str,
) -> FeatureLegalityAudit:
    issues: list[FeatureLegalityIssue] = []
    for feature in features:
        if feature.source_family not in SOURCE_FAMILY_ROW_TYPES:
            issues.append(
                _issue(
                    feature.feature_name,
                    "unknown_or_manual_review_source",
                    "Source family is not registered for Sprint 5E features: "
                    f"{feature.source_family}",
                )
            )
        elif row_type not in SOURCE_FAMILY_ROW_TYPES[feature.source_family]:
            issues.append(
                _issue(
                    feature.feature_name,
                    "source_not_allowed_for_row_family",
                    f"{feature.source_family} is not allowed for {row_type}.",
                )
            )
        if feature.source_family in FORBIDDEN_SOURCE_FAMILIES:
            issues.append(
                _issue(
                    feature.feature_name,
                    "supplement_or_blocked_source_as_feature",
                    f"{feature.source_family} cannot be used as a prediction feature.",
                )
            )
        normalized_name = _normalize_token(feature.feature_name + " " + feature.source_field)
        if "player_id" in normalized_name or "player_name" in normalized_name:
            issues.append(
                _issue(
                    feature.feature_name,
                    "identity_feature_blocked",
                    "player_id and player_name are identity fields, not model features.",
                )
            )
        if "same_season_final" in normalized_name or "same_season_target" in normalized_name:
            issues.append(
                _issue(
                    feature.feature_name,
                    "same_season_feature_blocked",
                    "Same-season final or target-window data cannot be a preseason feature.",
                )
            )
    base_audit = validate_feature_legality(
        list(features),
        input_snapshot_date=input_snapshot_date,
        label_available_date=label_available_date,
        source_allowlist=narrow_feature_source_allowlist(),
    )
    return FeatureLegalityAudit(
        valid=not issues and base_audit.valid,
        issues=tuple([*issues, *base_audit.issues]),
    )


def export_sprint_5e_packet(
    *,
    repo_root: str | Path,
    output_dir: str | Path,
    target_season: int = 2026,
) -> tuple[SnapshotBuildResult, ...]:
    repo = Path(repo_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    player_season = _read_csv(
        repo / "local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv"
    )
    identity_rows = _read_csv(
        repo
        / "local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads"
        / "dynastyprocess_db_playerids.csv"
    )
    identity_by_gsis = {
        str(row.get("gsis_id", "")): row for row in identity_rows if str(row.get("gsis_id", ""))
    }
    latest_by_player = _latest_completed_season_by_player(
        player_season,
        max_season=target_season - 2,
    )
    all_player_result = _build_all_player_pre_week1(
        latest_by_player=latest_by_player,
        identity_by_gsis=identity_by_gsis,
        target_season=target_season,
    )
    offseason_result = SnapshotBuildResult(
        row_family="offseason_carryover",
        attempted_rows=len(latest_by_player),
        emitted_rows=0,
        blocked_rows=len(latest_by_player),
        readiness_status="blocked_by_source_timestamps",
        notes=(
            "truth-set source_date is 2026-05-15, after the 2026-02-15 "
            "offseason cutoff; no snapshots emitted."
        ),
        candidates=(),
        legality_audits=(),
    )
    rookie_result = SnapshotBuildResult(
        row_family="rookie_post_draft",
        attempted_rows=0,
        emitted_rows=0,
        blocked_rows=0,
        readiness_status="readiness_report_only",
        notes=(
            "2026 draft capital manifest was collected after the YYYY-05-01 cutoff; "
            "defer production-like rookie snapshots until cutoff policy is approved."
        ),
        candidates=(),
        legality_audits=(),
    )
    results = (all_player_result, offseason_result, rookie_result)
    _write_exports(output, results)
    return results


def export_sprint_5h_packet(
    *,
    repo_root: str | Path,
    output_dir: str | Path,
    target_season: int = 2026,
    rookie_manifest_cutoff: str = "2026-05-25T23:45:00+00:00",
    cutoff_policy_id: str = "rookie_post_draft_manifest_approved_v1",
) -> tuple[SnapshotBuildResult, ...]:
    repo = Path(repo_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    player_season = _read_csv(
        repo / "local_exports/truth_set_lab/v3/reports/truth_set_v3_production_player_season.csv"
    )
    identity_rows = _read_csv(
        repo
        / "local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads"
        / "dynastyprocess_db_playerids.csv"
    )
    draft_rows = _read_csv(
        repo / "local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv"
    )
    identity_by_gsis = {
        str(row.get("gsis_id", "")): row for row in identity_rows if str(row.get("gsis_id", ""))
    }
    identity_by_name = {
        _normalize_token(str(row.get("merge_name") or row.get("name") or "")): row
        for row in identity_rows
        if row.get("merge_name") or row.get("name")
    }
    latest_by_player = _latest_completed_season_by_player(
        player_season,
        max_season=target_season - 2,
    )
    all_player_result = _build_all_player_pre_week1(
        latest_by_player=latest_by_player,
        identity_by_gsis=identity_by_gsis,
        target_season=target_season,
    )
    rookie_result = _build_rookie_post_draft(
        draft_rows=draft_rows,
        identity_by_name=identity_by_name,
        target_season=target_season,
        rookie_manifest_cutoff=rookie_manifest_cutoff,
        cutoff_policy_id=cutoff_policy_id,
    )
    offseason_result = SnapshotBuildResult(
        row_family="offseason_carryover",
        attempted_rows=len(latest_by_player),
        emitted_rows=0,
        blocked_rows=len(latest_by_player),
        readiness_status="blocked_by_source_after_cutoff",
        notes=(
            "Offseason carryover remains blocked until an on-or-before YYYY-02-15 "
            "source snapshot or availability manifest exists."
        ),
        candidates=(),
        legality_audits=(),
    )
    results = (all_player_result, rookie_result, offseason_result)
    _write_sprint_5h_exports(
        output=output,
        results=results,
        rookie_manifest_cutoff=rookie_manifest_cutoff,
        cutoff_policy_id=cutoff_policy_id,
        draft_rows=draft_rows,
    )
    return results


def _build_all_player_pre_week1(
    *,
    latest_by_player: Mapping[str, Mapping[str, str]],
    identity_by_gsis: Mapping[str, Mapping[str, str]],
    target_season: int,
) -> SnapshotBuildResult:
    candidates: list[FeatureSnapshotCandidate] = []
    audits: list[dict[str, str]] = []
    for player_id, season_row in latest_by_player.items():
        identity = identity_by_gsis.get(player_id, {})
        features = _all_player_features(season_row, identity, target_season=target_season)
        candidate = build_feature_snapshot_candidate(
            player_id=player_id,
            player_name=season_row.get("matched_player_name")
            or season_row.get("truth_set_player_name")
            or identity.get("name", ""),
            position=season_row.get("position", ""),
            row_type="all_player_pre_week1",
            target_season=target_season,
            target_horizon="same_year",
            features=features,
            source_manifest="sprint_5d_timestamp_registration",
        )
        candidates.append(candidate)
        audits.extend(_audit_rows(candidate))
    emitted = sum(1 for candidate in candidates if candidate.legality_status == "valid")
    return SnapshotBuildResult(
        row_family="all_player_pre_week1",
        attempted_rows=len(candidates),
        emitted_rows=emitted,
        blocked_rows=len(candidates) - emitted,
        readiness_status="snapshots_built" if emitted else "blocked",
        notes=(
            "Built only from stable identity metadata plus completed prior-season "
            "truth-set scoring fields."
        ),
        candidates=tuple(
            candidate for candidate in candidates if candidate.legality_status == "valid"
        ),
        legality_audits=tuple(audits),
    )


def _all_player_features(
    season_row: Mapping[str, str],
    identity: Mapping[str, str],
    *,
    target_season: int,
) -> tuple[FeatureSnapshot, ...]:
    input_snapshot_date = cutoff_date("all_player_pre_week1", target_season)
    identity_timestamp = input_snapshot_date
    scoring_timestamp = _prior_completed_season_availability_date(target_season)
    prior_source_season = str(season_row.get("season") or target_season - 1)
    birthdate = str(identity.get("birthdate") or "")
    draft_year = _optional_int(identity.get("draft_year"))
    features = [
        FeatureSnapshot(
            feature_name="age_at_snapshot",
            value=_age_on(birthdate, input_snapshot_date),
            source_family="stable_identity_metadata",
            source_field="birthdate",
            source_available_at=identity_timestamp,
            source_max_timestamp=identity_timestamp,
            lineage=(
                "dynastyprocess_db_playerids.csv",
                f"target_season={target_season}",
                f"source_policy_id={STABLE_IDENTITY_POLICY_ID}",
            ),
        ),
        FeatureSnapshot(
            feature_name="experience_at_snapshot",
            value=(target_season - draft_year) if draft_year is not None else None,
            source_family="stable_identity_metadata",
            source_field="draft_year",
            source_available_at=identity_timestamp,
            source_max_timestamp=identity_timestamp,
            lineage=(
                "dynastyprocess_db_playerids.csv",
                f"target_season={target_season}",
                f"source_policy_id={STABLE_IDENTITY_POLICY_ID}",
            ),
        ),
    ]
    for feature_name, source_field in (
        ("prior_completed_season_games_played", "games"),
        ("prior_completed_season_rushing_first_downs", "rushing_first_downs"),
        ("prior_completed_season_receiving_first_downs", "receiving_first_downs"),
        ("prior_completed_season_receptions", "receptions"),
        ("prior_completed_season_rushing_yards", "rushing_yards"),
        ("prior_completed_season_receiving_yards", "receiving_yards"),
        ("prior_completed_season_passing_yards", "passing_yards"),
    ):
        features.append(
            FeatureSnapshot(
                feature_name=feature_name,
                value=_optional_float(season_row.get(source_field)),
                source_family="truth_set_scoring_season",
                source_field=source_field,
                source_available_at=scoring_timestamp,
                source_max_timestamp=scoring_timestamp,
                lineage=(
                    "truth_set_v3_production_player_season.csv",
                    f"source_season={prior_source_season}",
                    f"target_season={target_season}",
                    f"derived_availability_date={scoring_timestamp}",
                    f"source_policy_id={PRIOR_COMPLETED_SEASON_POLICY_ID}",
                ),
            )
        )
    return tuple(features)


def _build_rookie_post_draft(
    *,
    draft_rows: Sequence[Mapping[str, str]],
    identity_by_name: Mapping[str, Mapping[str, str]],
    target_season: int,
    rookie_manifest_cutoff: str,
    cutoff_policy_id: str,
) -> SnapshotBuildResult:
    candidates: list[FeatureSnapshotCandidate] = []
    audits: list[dict[str, str]] = []
    for row in draft_rows:
        player_name = str(row.get("player") or "")
        normalized_name = str(row.get("normalized_player_name") or _normalize_token(player_name))
        identity = identity_by_name.get(_normalize_token(player_name), {})
        identity_player_id = str(identity.get("gsis_id") or "").strip()
        player_id = identity_player_id or f"rookie:{target_season}:{normalized_name}"
        position = str(identity.get("position") or "UNK")
        features = _rookie_post_draft_features(
            draft_row=row,
            identity=identity,
            rookie_manifest_cutoff=rookie_manifest_cutoff,
        )
        candidate = build_feature_snapshot_candidate(
            player_id=player_id,
            player_name=player_name,
            position=position,
            row_type="rookie_post_draft",
            target_season=target_season,
            target_horizon="year_1",
            features=features,
            source_manifest=cutoff_policy_id,
            input_snapshot_date=rookie_manifest_cutoff,
            cutoff_id=f"rookie_post_draft_{target_season}_{cutoff_policy_id}",
        )
        candidates.append(candidate)
        audits.extend(_audit_rows(candidate))
    emitted = sum(1 for candidate in candidates if candidate.legality_status == "valid")
    return SnapshotBuildResult(
        row_family="rookie_post_draft",
        attempted_rows=len(candidates),
        emitted_rows=emitted,
        blocked_rows=len(candidates) - emitted,
        readiness_status="snapshots_built" if emitted else "blocked",
        notes=(
            "Built only from approved factual draft manifest fields plus stable "
            "identity metadata where available."
        ),
        candidates=tuple(
            candidate for candidate in candidates if candidate.legality_status == "valid"
        ),
        legality_audits=tuple(audits),
    )


def _rookie_post_draft_features(
    *,
    draft_row: Mapping[str, str],
    identity: Mapping[str, str],
    rookie_manifest_cutoff: str,
) -> tuple[FeatureSnapshot, ...]:
    birthdate = str(identity.get("birthdate") or "")
    draft_year = _optional_int(draft_row.get("draft_year"))
    features = [
        FeatureSnapshot(
            feature_name="age_at_snapshot",
            value=_age_on(birthdate, rookie_manifest_cutoff[:10]) if birthdate else None,
            source_family="stable_identity_metadata",
            source_field="birthdate",
            source_available_at=rookie_manifest_cutoff,
            source_max_timestamp=rookie_manifest_cutoff,
            lineage=("dynastyprocess_db_playerids.csv",),
        ),
        FeatureSnapshot(
            feature_name="draft_year",
            value=draft_year,
            source_family="official_draft_capital",
            source_field="draft_year",
            source_available_at=str(draft_row.get("collected_at_utc") or ""),
            source_max_timestamp=str(draft_row.get("collected_at_utc") or ""),
            lineage=("rookie_draft_capital_2026.csv",),
        ),
        FeatureSnapshot(
            feature_name="draft_round",
            value=_optional_int(draft_row.get("round")),
            source_family="official_draft_capital",
            source_field="round",
            source_available_at=str(draft_row.get("collected_at_utc") or ""),
            source_max_timestamp=str(draft_row.get("collected_at_utc") or ""),
            lineage=("rookie_draft_capital_2026.csv",),
        ),
        FeatureSnapshot(
            feature_name="draft_pick",
            value=_optional_int(draft_row.get("overall_pick")),
            source_family="official_draft_capital",
            source_field="overall_pick",
            source_available_at=str(draft_row.get("collected_at_utc") or ""),
            source_max_timestamp=str(draft_row.get("collected_at_utc") or ""),
            lineage=("rookie_draft_capital_2026.csv",),
        ),
        FeatureSnapshot(
            feature_name="draft_day",
            value=_optional_int(draft_row.get("draft_day")),
            source_family="official_draft_capital",
            source_field="draft_day",
            source_available_at=str(draft_row.get("collected_at_utc") or ""),
            source_max_timestamp=str(draft_row.get("collected_at_utc") or ""),
            lineage=("rookie_draft_capital_2026.csv",),
        ),
    ]
    return tuple(features)


def _latest_completed_season_by_player(
    rows: Sequence[Mapping[str, str]], *, max_season: int
) -> dict[str, Mapping[str, str]]:
    best: dict[str, Mapping[str, str]] = {}
    best_season: dict[str, int] = defaultdict(int)
    for row in rows:
        player_id = str(row.get("player_id") or "")
        season = _optional_int(row.get("season"))
        if not player_id or season is None or season > max_season:
            continue
        if season >= best_season[player_id]:
            best[player_id] = row
            best_season[player_id] = season
    return best


def _write_exports(output: Path, results: Sequence[SnapshotBuildResult]) -> None:
    candidates = [candidate for result in results for candidate in result.candidates]
    _write_csv(
        output / "feature_snapshot_manifest.csv",
        [
            {
                "row_family": result.row_family,
                "attempted_rows": result.attempted_rows,
                "emitted_rows": result.emitted_rows,
                "blocked_rows": result.blocked_rows,
                "readiness_status": result.readiness_status,
                "notes": result.notes,
            }
            for result in results
        ],
        (
            "row_family",
            "attempted_rows",
            "emitted_rows",
            "blocked_rows",
            "readiness_status",
            "notes",
        ),
    )
    _write_csv(
        output / "candidate_prediction_snapshots.csv",
        [
            {
                "row_type": result.row_family,
                "cutoff_id": f"{result.row_family}_2026",
                "input_snapshot_date": cutoff_date(result.row_family, 2026),
                "target_season": 2026,
                "emitted_rows": result.emitted_rows,
                "readiness_status": result.readiness_status,
            }
            for result in results
        ],
        (
            "row_type",
            "cutoff_id",
            "input_snapshot_date",
            "target_season",
            "emitted_rows",
            "readiness_status",
        ),
    )
    _write_csv(
        output / "candidate_feature_snapshots.csv",
        [
            {
                **_candidate_flattened(candidate),
                "feature_vector": json.dumps(candidate.feature_vector, sort_keys=True),
                "missingness_mask": json.dumps(candidate.missingness_mask, sort_keys=True),
                "feature_lineage": json.dumps(candidate.feature_lineage, sort_keys=True),
            }
            for candidate in candidates
        ],
        (
            "row_id",
            "player_id",
            "row_type",
            "cutoff_id",
            "input_snapshot_date",
            "source_max_timestamp",
            "feature_vector",
            "missingness_mask",
            "feature_lineage",
            "source_manifest",
            "snapshot_hash",
            "legality_status",
            "manual_review_status",
        ),
    )
    missing_counts: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        for feature_name, missing in candidate.missingness_mask.items():
            if missing:
                missing_counts[feature_name] += 1
    _write_csv(
        output / "feature_missingness_report.csv",
        [
            {
                "feature_name": feature_name,
                "missing_count": count,
                "total_emitted_rows": len(candidates),
                "coverage_count": len(candidates) - count,
            }
            for feature_name, count in sorted(missing_counts.items())
        ],
        ("feature_name", "missing_count", "total_emitted_rows", "coverage_count"),
    )
    _write_csv(
        output / "feature_legality_audit.csv",
        [row for result in results for row in result.legality_audits],
        (
            "row_id",
            "player_id",
            "row_type",
            "legality_status",
            "issue_type",
            "feature_name",
            "message",
        ),
    )
    _write_csv(
        output / "row_family_snapshot_readiness.csv",
        [
            {
                "row_family": result.row_family,
                "attempted_rows": result.attempted_rows,
                "emitted_rows": result.emitted_rows,
                "blocked_rows": result.blocked_rows,
                "readiness_status": result.readiness_status,
                "notes": result.notes,
            }
            for result in results
        ],
        (
            "row_family",
            "attempted_rows",
            "emitted_rows",
            "blocked_rows",
            "readiness_status",
            "notes",
        ),
    )
    readme = [
        "# Sprint 5E Narrow Feature Snapshots",
        "",
        "Verdict: `FEATURE_SNAPSHOTS_BUILT_PARTIAL`",
        "",
        (
            "This packet contains local-only, internal feature snapshot candidates. "
            "It does not contain probabilities, rankings, calibrated model outputs, "
            "or app fields."
        ),
        "",
        "## Row Families",
    ]
    for result in results:
        readme.append(
            f"- `{result.row_family}`: {result.emitted_rows}/{result.attempted_rows} "
            f"emitted - {result.notes}"
        )
    readme += [
        "",
        "## Sources Used",
        "",
        "- `dynastyprocess_db_playerids.csv` for stable identity/DOB metadata.",
        (
            "- `truth_set_v3_production_player_season.csv` for completed "
            "prior-season scoring/first-down fields."
        ),
        "",
        "## Sources Excluded",
        "",
        (
            "- Raw snap counts, RotoWire injury/status, historical rookie replay "
            "context, player_stats label supplements, play-by-play label supplements, "
            "prior league draft history, projections/rankings/ADP/market sources."
        ),
    ]
    (output / "README_SPRINT_5E.md").write_text("\n".join(readme) + "\n", encoding="utf-8")


def _write_sprint_5h_exports(
    *,
    output: Path,
    results: Sequence[SnapshotBuildResult],
    rookie_manifest_cutoff: str,
    cutoff_policy_id: str,
    draft_rows: Sequence[Mapping[str, str]],
) -> None:
    candidates = [candidate for result in results for candidate in result.candidates]
    _write_csv(
        output / "cutoff_policy_registry_applied.csv",
        [
            {
                "row_family": "all_player_pre_week1",
                "cutoff_policy_id": "fixed_pre_week1_v1",
                "cutoff_date": "YYYY-09-01",
                "status": "eligible_now",
                "notes": "Narrow prior-season source set remains legal.",
            },
            {
                "row_family": "offseason_carryover",
                "cutoff_policy_id": "fixed_offseason_carryover_v1",
                "cutoff_date": "YYYY-02-15",
                "status": "blocked",
                "notes": "Requires earlier source snapshot or source availability manifest.",
            },
            {
                "row_family": "rookie_post_draft",
                "cutoff_policy_id": cutoff_policy_id,
                "cutoff_date": rookie_manifest_cutoff,
                "status": "eligible_now",
                "notes": "Approved for factual draft manifest fields only.",
            },
        ],
        ("row_family", "cutoff_policy_id", "cutoff_date", "status", "notes"),
    )
    _write_csv(
        output / "candidate_prediction_snapshots.csv",
        [
            {
                "row_type": result.row_family,
                "cutoff_id": _cutoff_id_for_result(result, cutoff_policy_id),
                "input_snapshot_date": _snapshot_date_for_result(
                    result,
                    rookie_manifest_cutoff,
                ),
                "target_season": 2026,
                "emitted_rows": result.emitted_rows,
                "readiness_status": result.readiness_status,
            }
            for result in results
        ],
        (
            "row_type",
            "cutoff_id",
            "input_snapshot_date",
            "target_season",
            "emitted_rows",
            "readiness_status",
        ),
    )
    _write_csv(
        output / "candidate_feature_snapshots.csv",
        [
            {
                **_candidate_flattened(candidate),
                "feature_vector": json.dumps(candidate.feature_vector, sort_keys=True),
                "missingness_mask": json.dumps(candidate.missingness_mask, sort_keys=True),
                "feature_lineage": json.dumps(candidate.feature_lineage, sort_keys=True),
            }
            for candidate in candidates
        ],
        (
            "row_id",
            "player_id",
            "row_type",
            "cutoff_id",
            "input_snapshot_date",
            "source_max_timestamp",
            "feature_vector",
            "missingness_mask",
            "feature_lineage",
            "source_manifest",
            "snapshot_hash",
            "legality_status",
            "manual_review_status",
        ),
    )
    _write_csv(
        output / "row_family_snapshot_readiness.csv",
        [
            {
                "row_family": result.row_family,
                "attempted_rows": result.attempted_rows,
                "emitted_rows": result.emitted_rows,
                "blocked_rows": result.blocked_rows,
                "readiness_status": result.readiness_status,
                "notes": result.notes,
            }
            for result in results
        ],
        (
            "row_family",
            "attempted_rows",
            "emitted_rows",
            "blocked_rows",
            "readiness_status",
            "notes",
        ),
    )
    manifest_rows = [
        {
            "manifest_source": row.get("source", ""),
            "source_file": row.get("source_file", ""),
            "collected_at_utc": row.get("collected_at_utc", ""),
            "draft_year": row.get("draft_year", ""),
            "rows_in_manifest": len(draft_rows),
            "source_status": row.get("source_status", ""),
            "allowed_use": row.get("allowed_use", ""),
            "cutoff_policy_id": cutoff_policy_id,
            "approved_cutoff": rookie_manifest_cutoff,
            "forbidden_field_count": _forbidden_draft_field_count(row),
            "status": "pass" if row.get("collected_at_utc") == rookie_manifest_cutoff else "review",
        }
        for row in draft_rows[:1]
    ]
    _write_csv(
        output / "rookie_post_draft_manifest_audit.csv",
        manifest_rows,
        (
            "manifest_source",
            "source_file",
            "collected_at_utc",
            "draft_year",
            "rows_in_manifest",
            "source_status",
            "allowed_use",
            "cutoff_policy_id",
            "approved_cutoff",
            "forbidden_field_count",
            "status",
        ),
    )
    _write_csv(
        output / "offseason_carryover_blocker_report.csv",
        [
            {
                "row_family": "offseason_carryover",
                "status": "blocked_by_source_after_cutoff",
                "cutoff": "YYYY-02-15",
                "required_repair": "earlier source snapshot or source availability manifest",
                "notes": (
                    "Cutoff policy should not move later without changing business meaning."
                ),
            }
        ],
        ("row_family", "status", "cutoff", "required_repair", "notes"),
    )
    _write_csv(
        output / "feature_legality_audit.csv",
        [row for result in results for row in result.legality_audits],
        (
            "row_id",
            "player_id",
            "row_type",
            "legality_status",
            "issue_type",
            "feature_name",
            "message",
        ),
    )
    missing_counts: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        for feature_name, missing in candidate.missingness_mask.items():
            if missing:
                missing_counts[feature_name] += 1
    _write_csv(
        output / "feature_missingness_report.csv",
        [
            {
                "feature_name": feature_name,
                "missing_count": count,
                "total_emitted_rows": len(candidates),
                "coverage_count": len(candidates) - count,
            }
            for feature_name, count in sorted(missing_counts.items())
        ],
        ("feature_name", "missing_count", "total_emitted_rows", "coverage_count"),
    )
    readme = [
        "# Sprint 5H Cutoff-Approved Snapshot Rebuild",
        "",
        "Verdict: `SNAPSHOTS_REBUILT_NARROW_PLUS_ROOKIES`",
        "",
        "The packet is local/internal only. It contains feature snapshots, not "
        "probabilities, rankings, calibrated models, or app fields.",
        "",
        "## Row Families",
    ]
    for result in results:
        readme.append(
            f"- `{result.row_family}`: {result.emitted_rows}/{result.attempted_rows} "
            f"emitted - {result.notes}"
        )
    readme += [
        "",
        "## Rookie Policy",
        "",
        f"- Cutoff policy ID: `{cutoff_policy_id}`",
        f"- Approved cutoff: `{rookie_manifest_cutoff}`",
        "- Draft features are factual manifest fields only.",
        "- Market/rank/projection/ADP/trade/RotoWire outlook fields remain blocked.",
    ]
    (output / "README_SPRINT_5H.md").write_text("\n".join(readme) + "\n", encoding="utf-8")


def _cutoff_id_for_result(result: SnapshotBuildResult, cutoff_policy_id: str) -> str:
    if result.row_family == "rookie_post_draft":
        return f"rookie_post_draft_2026_{cutoff_policy_id}"
    return f"{result.row_family}_2026"


def _snapshot_date_for_result(
    result: SnapshotBuildResult,
    rookie_manifest_cutoff: str,
) -> str:
    if result.row_family == "rookie_post_draft":
        return rookie_manifest_cutoff
    return cutoff_date(result.row_family, 2026)


def _forbidden_draft_field_count(row: Mapping[str, str]) -> int:
    forbidden = (
        "adp",
        "rank",
        "projection",
        "market",
        "trade",
        "consensus",
        "outlook",
        "camp",
    )
    return sum(1 for key in row if any(fragment in key.lower() for fragment in forbidden))


def _candidate_flattened(candidate: FeatureSnapshotCandidate) -> dict[str, Any]:
    payload = asdict(candidate)
    payload.pop("feature_vector")
    payload.pop("missingness_mask")
    payload.pop("feature_lineage")
    payload.pop("legality_issues")
    return payload


def _audit_rows(candidate: FeatureSnapshotCandidate) -> tuple[dict[str, str], ...]:
    if not candidate.legality_issues:
        return (
            {
                "row_id": candidate.row_id,
                "player_id": candidate.player_id,
                "row_type": candidate.row_type,
                "legality_status": candidate.legality_status,
                "issue_type": "none",
                "feature_name": "",
                "message": "Snapshot passed Sprint 5E legality checks.",
            },
        )
    return tuple(
        {
            "row_id": candidate.row_id,
            "player_id": candidate.player_id,
            "row_type": candidate.row_type,
            "legality_status": candidate.legality_status,
            "issue_type": issue.issue_type,
            "feature_name": issue.feature_name,
            "message": issue.message,
        }
        for issue in candidate.legality_issues
    )


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], headers: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _source_max_timestamp(features: Sequence[FeatureSnapshot], fallback: str) -> str:
    stamps = [feature.source_max_timestamp for feature in features if feature.source_max_timestamp]
    return max(stamps) if stamps else fallback


def _age_on(birthdate: str, snapshot_date: str) -> float | None:
    if not birthdate or birthdate.strip().lower() in {"na", "n/a", "none", "nan"}:
        return None
    try:
        born = datetime.fromisoformat(birthdate).date()
        snap = datetime.fromisoformat(snapshot_date).date()
    except ValueError:
        return None
    age = snap.year - born.year - ((snap.month, snap.day) < (born.month, born.day))
    return round(age + ((snap - date(snap.year, born.month, born.day)).days % 365) / 365.0, 2)


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value)))
    except ValueError:
        return None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value))
    except ValueError:
        return None


def _normalize_token(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(value).lower())


def _issue(feature_name: str, issue_type: str, message: str) -> FeatureLegalityIssue:
    return FeatureLegalityIssue(
        feature_name=feature_name,
        issue_type=issue_type,
        severity="error",
        message=message,
    )


def _require_supported_row_type(row_type: str) -> None:
    if row_type not in SUPPORTED_FEATURE_SNAPSHOT_ROW_TYPES:
        raise ValueError(
            f"Unsupported row_type {row_type!r}; supported types are "
            + ", ".join(SUPPORTED_FEATURE_SNAPSHOT_ROW_TYPES)
        )
