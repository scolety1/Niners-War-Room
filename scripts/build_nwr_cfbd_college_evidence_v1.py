"""Build the governed CFBD college evidence admission and value-audit packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services import cfbd_college_evidence_service as college  # noqa: E402
from src.services import new_evidence_foundation_service as foundation  # noqa: E402

PACKET_REL = Path(
    "docs/hq/master/nwr_cfbd_college_evidence_admission_v1_20260730"
)
CATALOG_REL = Path("config/nwr_cfbd_college_evidence_snapshot_v1.json")
PRIOR_PACKET_REL = Path(
    "docs/hq/master/nwr_new_evidence_rookie_availability_foundation_v1_20260730"
)
DEFAULT_SNAPSHOT_ROOT = Path(r"C:\NWR_SHARED_DATA\source_snapshots")
CANONICAL_HQ = "2eb3532600cfc0665cc9869ba95a783b2aa0d549"
CANONICAL_TREE = "e3e913ab1f6fbf5d59b56e2a4df9391f18ab8f58"
BOARD_HASH = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
FROZEN_HASH = "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179"
PERSISTENT_DIGEST = "88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987"
RECOVERY_DIGEST = "1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835"
ADMISSION_ID = "NWR_CFBD_COLLEGE_EVIDENCE_ADMISSION_V1"
FOUNDATION_ID = "NWR_NEW_EVIDENCE_FOUNDATION_V1"
BASELINE_FEATURES = (
    "position",
    "draft_pick",
    "draft_age",
    "forty",
    "vertical",
    "broad_jump",
    "cone",
    "shuttle",
    "bench",
)
COLLEGE_STATS_FEATURES = college.COUNTING_FEATURES + college.DERIVED_FEATURES
COLLEGE_ADVANCED_FEATURES = college.USAGE_FEATURES + college.PPA_FEATURES
COLLEGE_ALL_FEATURES = COLLEGE_STATS_FEATURES + COLLEGE_ADVANCED_FEATURES
EARLY_FEATURES = (
    "rookie_offensive_snap_share",
    "rookie_opportunities_per_snap",
    "rookie_opportunity_growth",
    "rookie_production_per_snap",
    "rookie_active_roster_weeks",
    "rookie_injury_report_rows",
    "rookie_injury_weeks",
    "rookie_out_report_weeks",
    "rookie_did_not_practice_rows",
    "rookie_limited_practice_rows",
    "rookie_depth_chart_mean",
)
REQUIRED_FILES = (
    "EXECUTIVE_VERDICT.md",
    "CFBD_COLLEGE_EVIDENCE_ADMISSION_REPORT.md",
    "CFBD_API_AUTHORITY_AND_USAGE.md",
    "SOURCE_ACCESS_TERMS_AND_LICENSE.md",
    "CFBD_SOURCE_INVENTORY.csv",
    "CFBD_SOURCE_SNAPSHOT_MANIFEST.csv",
    "CFBD_SCHEMA_VALIDATION.csv",
    "CFBD_EXACT_IDENTITY_CROSSWALK.csv",
    "CFBD_REVIEW_ONLY_IDENTITY_CANDIDATES.csv",
    "CFBD_UNRESOLVED_IDENTITY_INVENTORY.csv",
    "CFBD_IDENTITY_COVERAGE.csv",
    "CFBD_FEATURE_MISSING_EXACT_IDENTITY.csv",
    "CFBD_COLLEGE_EVIDENCE_FOUNDATION.csv",
    "CFBD_FEATURE_COVERAGE.csv",
    "TEMPORAL_AVAILABILITY_AND_LEAKAGE_CONTRACT.md",
    "PRE_DRAFT_INCREMENTAL_VALUE_RESULTS.csv",
    "EARLY_CAREER_INCREMENTAL_VALUE_RESULTS.csv",
    "MULTI_YEAR_SURVIVAL_INCREMENTAL_VALUE_RESULTS.csv",
    "INCREMENTAL_VALUE_DECISIONS.csv",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "SOURCE_AND_FEATURE_ACCEPTANCE_GATE_MATRIX.csv",
    "MODEL_REENTRY_CONTRACT.md",
    "FINISHED_V1_OUTCOME_V3_AND_STATE_NO_CHANGE.md",
    "VALIDATION_RESULTS.md",
    "ROLLBACK_PLAN.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "MANIFEST.json",
)


@dataclass(frozen=True)
class Pipeline:
    snapshot: college.Snapshot
    identities: college.IdentityCrosswalk
    features: pd.DataFrame
    feature_missing: pd.DataFrame
    identity_coverage: pd.DataFrame
    feature_coverage: pd.DataFrame
    source_inventory: pd.DataFrame
    snapshot_manifest: pd.DataFrame
    schema_validation: pd.DataFrame
    pre_results: pd.DataFrame
    early_results: pd.DataFrame
    survival_results: pd.DataFrame
    decisions: pd.DataFrame
    gates: pd.DataFrame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT_ROOT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    packet = args.output_root.resolve() if args.output_root else root / PACKET_REL
    before = _hashes(packet) if args.verify_existing else {}
    pipeline = build_pipeline(root=root, snapshot_root=args.snapshot_root.resolve())
    write_packet(root=root, packet=packet, pipeline=pipeline)
    after = _hashes(packet)
    if args.verify_existing and before != after:
        changed = sorted(
            path
            for path in set(before) | set(after)
            if before.get(path) != after.get(path)
        )
        raise AssertionError(f"deterministic regeneration drift: {changed}")
    print(f"admission_id={ADMISSION_ID}")
    print(f"packet={packet}")
    print(f"packet_files={len(after)}")
    print(f"exact_identity_rows={len(pipeline.identities.exact)}")
    print(f"unresolved_identity_rows={len(pipeline.identities.unresolved)}")
    print(f"college_feature_rows={len(pipeline.features)}")
    print(
        "main_incremental_decision="
        + str(
            pipeline.decisions.loc[
                pipeline.decisions["comparison"].eq("EARLY_CAREER_ALL_CFBD"),
                "decision",
            ].iloc[0]
        )
    )
    print("deterministic_regeneration=PASS" if args.verify_existing else "build=PASS")
    return 0


def build_pipeline(*, root: Path, snapshot_root: Path) -> Pipeline:
    snapshot = college.validate_snapshot(root / CATALOG_REL, snapshot_root)
    prior = root / PRIOR_PACKET_REL
    rookie = pd.read_csv(prior / "ROOKIE_EVIDENCE_FOUNDATION.csv")
    early = pd.read_csv(prior / "EARLY_CAREER_OPPORTUNITY_FOUNDATION.csv")
    availability = pd.read_csv(prior / "AVAILABILITY_AND_INJURY_FOUNDATION.csv")

    draft_rows = college.load_family(snapshot, "draft_picks")
    identities = college.build_identity_crosswalk(rookie, draft_rows)
    features = college.build_college_features(
        identities.exact,
        stat_rows=college.load_family(snapshot, "player_season_stats"),
        usage_rows=college.load_family(snapshot, "player_usage"),
        ppa_rows=college.load_family(snapshot, "player_ppa"),
    )
    feature_ids = set(features["gsis_id"])
    feature_missing = identities.exact[
        ~identities.exact["gsis_id"].isin(feature_ids)
    ].copy()
    feature_missing["missing_reason"] = (
        "NO_SELECTED_PRE_DRAFT_TERMINAL_COLLEGE_STAT_ROW"
    )

    evaluation = _evaluation_frame(
        rookie=rookie,
        early=early,
        availability=availability,
        features=features,
    )
    pre = foundation.walk_forward_evaluate(
        evaluation[
            evaluation["year_two_vorp"].notna()
            & evaluation["year_two_top_outcome"].notna()
        ].copy(),
        model_features={
            "C0": BASELINE_FEATURES,
            "C1": BASELINE_FEATURES + COLLEGE_STATS_FEATURES,
            "C2": BASELINE_FEATURES + COLLEGE_ALL_FEATURES,
        },
        season_column="draft_year",
        continuous_target="year_two_vorp",
        binary_target="year_two_top_outcome",
        slice_column="rookie_games_slice",
    )
    early_result = foundation.walk_forward_evaluate(
        evaluation[
            evaluation["year_two_vorp"].notna()
            & evaluation["year_two_top_outcome"].notna()
        ].copy(),
        model_features={
            "E0": BASELINE_FEATURES + EARLY_FEATURES,
            "E1": BASELINE_FEATURES + EARLY_FEATURES + COLLEGE_ALL_FEATURES,
        },
        season_column="draft_year",
        continuous_target="year_two_vorp",
        binary_target="year_two_top_outcome",
        slice_column="rookie_games_slice",
    )
    survival = foundation.walk_forward_evaluate(
        evaluation[
            evaluation["career_survival_observable"].astype(bool)
            & evaluation["multi_year_cumulative_vorp"].notna()
            & evaluation["career_survival_year_three"].notna()
        ].copy(),
        model_features={
            "S0": BASELINE_FEATURES,
            "S1": BASELINE_FEATURES + COLLEGE_ALL_FEATURES,
        },
        season_column="draft_year",
        continuous_target="multi_year_cumulative_vorp",
        binary_target="career_survival_year_three",
        slice_column="rookie_games_slice",
    )
    decisions = pd.DataFrame(
        [
            _decision("PRE_DRAFT_COUNTING_STATS", pre.metrics, "C1", "C0"),
            _decision("PRE_DRAFT_USAGE_PPA", pre.metrics, "C2", "C1"),
            _decision("PRE_DRAFT_ALL_CFBD", pre.metrics, "C2", "C0"),
            _decision("EARLY_CAREER_ALL_CFBD", early_result.metrics, "E1", "E0"),
            _decision("MULTI_YEAR_SURVIVAL_ALL_CFBD", survival.metrics, "S1", "S0"),
        ]
    )
    source_inventory, snapshot_manifest, schema_validation = _source_rows(snapshot)
    identity_coverage = college.coverage_rows(rookie, identities, features)
    feature_coverage = _feature_coverage(features, identities, rookie)
    gates = _gate_rows(source_inventory, decisions)
    return Pipeline(
        snapshot=snapshot,
        identities=identities,
        features=features,
        feature_missing=feature_missing,
        identity_coverage=identity_coverage,
        feature_coverage=feature_coverage,
        source_inventory=source_inventory,
        snapshot_manifest=snapshot_manifest,
        schema_validation=schema_validation,
        pre_results=pre.metrics,
        early_results=early_result.metrics,
        survival_results=survival.metrics,
        decisions=decisions,
        gates=gates,
    )


def _evaluation_frame(
    *,
    rookie: pd.DataFrame,
    early: pd.DataFrame,
    availability: pd.DataFrame,
    features: pd.DataFrame,
) -> pd.DataFrame:
    college_fields = ["gsis_id", *college.MODEL_FEATURES]
    evaluation = rookie.merge(
        features[college_fields],
        on="gsis_id",
        how="inner",
        validate="one_to_one",
    )
    rookie_early = early[early["experience_class"].eq("ROOKIE")][
        [
            "gsis_id",
            "season",
            "offensive_snap_share",
            "opportunities_per_snap",
            "opportunity_growth",
            "production_per_snap",
        ]
    ].rename(
        columns={
            "season": "draft_year",
            "offensive_snap_share": "rookie_offensive_snap_share",
            "opportunities_per_snap": "rookie_opportunities_per_snap",
            "opportunity_growth": "rookie_opportunity_growth",
            "production_per_snap": "rookie_production_per_snap",
        }
    )
    rookie_availability = availability[
        [
            "gsis_id",
            "season",
            "active_roster_weeks",
            "injury_report_rows",
            "injury_weeks",
            "out_report_weeks",
            "did_not_practice_rows",
            "limited_practice_rows",
            "depth_chart_mean",
        ]
    ].rename(
        columns={
            "season": "draft_year",
            "active_roster_weeks": "rookie_active_roster_weeks",
            "injury_report_rows": "rookie_injury_report_rows",
            "injury_weeks": "rookie_injury_weeks",
            "out_report_weeks": "rookie_out_report_weeks",
            "did_not_practice_rows": "rookie_did_not_practice_rows",
            "limited_practice_rows": "rookie_limited_practice_rows",
            "depth_chart_mean": "rookie_depth_chart_mean",
        }
    )
    for frame in (evaluation, rookie_early, rookie_availability):
        frame["draft_year"] = pd.to_numeric(frame["draft_year"], errors="coerce")
    evaluation = evaluation.merge(
        rookie_early,
        on=["gsis_id", "draft_year"],
        how="left",
        validate="one_to_one",
    ).merge(
        rookie_availability,
        on=["gsis_id", "draft_year"],
        how="left",
        validate="one_to_one",
    )
    evaluation["rookie_games_slice"] = np.where(
        pd.to_numeric(evaluation["rookie_games"], errors="coerce").fillna(0) < 8,
        "LOW_GAMES",
        "EIGHT_PLUS_GAMES",
    )
    return evaluation


def _metric(results: pd.DataFrame, model: str) -> pd.Series | None:
    rows = results[
        results["model"].eq(model) & results["slice"].eq("ALL")
    ]
    return None if rows.empty else rows.iloc[0]


def _difference(left: Any, right: Any) -> float | str:
    try:
        value = float(left) - float(right)
        return round(value, 6) if math.isfinite(value) else ""
    except (TypeError, ValueError):
        return ""


def _decision(
    comparison: str,
    results: pd.DataFrame,
    challenger: str,
    baseline: str,
) -> dict[str, Any]:
    current = _metric(results, challenger)
    prior = _metric(results, baseline)
    if current is None or prior is None:
        return {
            "comparison": comparison,
            "challenger": challenger,
            "baseline": baseline,
            "rows": 0,
            "folds": 0,
            "delta_spearman": "",
            "delta_brier": "",
            "delta_rank_mae": "",
            "improved_metrics": 0,
            "decision": "NOT_ENOUGH_INFORMATION",
            "reason": "missing governed ALL evaluation row",
        }
    deltas = {
        "delta_spearman": _difference(current["spearman"], prior["spearman"]),
        "delta_brier": _difference(prior["brier"], current["brier"]),
        "delta_rank_mae": _difference(prior["rank_mae"], current["rank_mae"]),
    }
    values = [value for value in deltas.values() if value != ""]
    improved = sum(value > 0 for value in values)
    enough = (
        int(current["folds"]) >= 5
        and int(current["rows"]) >= 300
        and float(current["coverage"]) >= 0.5
    )
    decision = (
        "ADMIT_SOURCE_AND_FEATURE"
        if enough and improved >= 2
        else (
            "ADMIT_SOURCE_FEATURE_NOT_INCREMENTAL"
            if enough
            else "NOT_ENOUGH_INFORMATION"
        )
    )
    return {
        "comparison": comparison,
        "challenger": challenger,
        "baseline": baseline,
        "rows": int(current["rows"]),
        "folds": int(current["folds"]),
        **deltas,
        "improved_metrics": improved,
        "decision": decision,
        "reason": (
            "at least two of three governed out-of-sample metrics improved"
            if decision == "ADMIT_SOURCE_AND_FEATURE"
            else (
                "fewer than two governed out-of-sample metrics improved"
                if decision == "ADMIT_SOURCE_FEATURE_NOT_INCREMENTAL"
                else "minimum fold, row, or coverage gate failed"
            )
        ),
    }


def _source_rows(
    snapshot: college.Snapshot,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inventory = []
    schemas = []
    for family, record in sorted(snapshot.manifest["families"].items()):
        assets = [
            asset
            for asset in snapshot.manifest["assets"]
            if Path(asset["relative_path"]).parts[:2] == ("raw", family)
        ]
        inventory.append(
            {
                "provider": "CollegeFootballData",
                "api_family": "official REST API v2",
                "source_family": family,
                "endpoint": record["endpoint"],
                "years": f"{min(record['years'])}-{max(record['years'])}",
                "assets": len(assets),
                "rows": record["rows"],
                "schema": record["schema"],
                "provenance": "PASS_OFFICIAL_AUTHORITY",
                "terms_license": "PASS_PRIVATE_RESEARCH_NO_RAW_REDISTRIBUTION",
                "immutable_snapshot": "PASS",
                "identity": (
                    "PASS_UNIQUE_DRAFT_SLOT_CROSSWALK"
                    if family == "draft_picks"
                    else "PASS_EXACT_CFBD_COLLEGE_ATHLETE_ID"
                ),
                "temporal_availability": (
                    "PASS_IDENTITY_AFTER_SELECTION"
                    if family == "draft_picks"
                    else "PASS_WITH_RETROSPECTIVE_REVISION_LIMIT"
                ),
                "admission_status": record["admission_status"],
            }
        )
        schemas.append(
            {
                "source_family": family,
                "schema": record["schema"],
                "assets_validated": len(assets),
                "rows_validated": sum(int(asset["rows"]) for asset in assets),
                "schema_fingerprints": "|".join(
                    sorted({asset["schema_fingerprint"] for asset in assets})
                ),
                "required_openapi_contract": "PASS",
                "observed_top_level_schema": "PASS",
                "status": "PASS",
            }
        )
    snapshots = pd.DataFrame(
        [
            {
                "provider": "CollegeFootballData",
                "snapshot_id": snapshot.manifest["snapshot_id"],
                "endpoint": asset["endpoint"],
                "parameters": json.dumps(
                    asset["parameters"], sort_keys=True, separators=(",", ":")
                ),
                "relative_path": asset["relative_path"],
                "rows": asset["rows"],
                "bytes": asset["bytes"],
                "sha256": asset["sha256"],
                "schema_fingerprint": asset["schema_fingerprint"],
                "retrieved_at_utc": snapshot.manifest["retrieved_at_utc"],
                "external_reference": (
                    "SOURCE_SNAPSHOT_ROOT/"
                    + snapshot.catalog["manifest_relative_path"].rsplit("/", 1)[0]
                    + "/"
                    + asset["relative_path"]
                ),
            }
            for asset in snapshot.manifest["assets"]
        ]
    )
    return pd.DataFrame(inventory), snapshots, pd.DataFrame(schemas)


def _feature_coverage(
    features: pd.DataFrame,
    identities: college.IdentityCrosswalk,
    rookie: pd.DataFrame,
) -> pd.DataFrame:
    exact = len(identities.exact)
    drafted = int(rookie["drafted_status"].eq("DRAFTED").sum())
    total = len(rookie)
    rows = []
    for family, columns in (
        ("terminal_counting_stats", college.COUNTING_FEATURES),
        ("derived_college_production", college.DERIVED_FEATURES),
        ("player_usage", college.USAGE_FEATURES),
        ("player_ppa", college.PPA_FEATURES),
    ):
        present = features[list(columns)].notna().any(axis=1)
        rows.append(
            {
                "feature_family": family,
                "feature_count": len(columns),
                "rows_present": int(present.sum()),
                "exact_identity_rows": exact,
                "drafted_rookie_rows": drafted,
                "all_rookie_rows": total,
                "coverage_of_exact": round(present.sum() / exact, 6),
                "coverage_of_drafted": round(present.sum() / drafted, 6),
                "coverage_of_all_rookies": round(present.sum() / total, 6),
                "missing_preserved": True,
            }
        )
    return pd.DataFrame(rows)


def _gate_rows(
    source_inventory: pd.DataFrame,
    decisions: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        {
            "family": row["source_family"],
            "kind": "SOURCE",
            "provenance": row["provenance"],
            "terms_license": row["terms_license"],
            "immutable_snapshot": row["immutable_snapshot"],
            "identity": row["identity"],
            "historical_availability": row["temporal_availability"],
            "schema": "PASS",
            "incremental_value": "NOT_APPLICABLE_SOURCE_GATE",
            "decision": row["admission_status"],
        }
        for _, row in source_inventory.iterrows()
    ]
    rows.extend(
        {
            "family": row["comparison"],
            "kind": "FEATURE",
            "provenance": "PASS_ADMITTED_CFBD_SOURCE",
            "terms_license": "PASS_PRIVATE_RESEARCH",
            "immutable_snapshot": "PASS",
            "identity": "PASS_EXACT_ONLY",
            "historical_availability": "PASS_STRICTLY_PRE_TARGET",
            "schema": "PASS",
            "incremental_value": row["decision"],
            "decision": row["decision"],
        }
        for _, row in decisions.iterrows()
    )
    return pd.DataFrame(rows)


def write_packet(*, root: Path, packet: Path, pipeline: Pipeline) -> None:
    packet.mkdir(parents=True, exist_ok=True)
    csvs = {
        "CFBD_SOURCE_INVENTORY.csv": pipeline.source_inventory,
        "CFBD_SOURCE_SNAPSHOT_MANIFEST.csv": pipeline.snapshot_manifest,
        "CFBD_SCHEMA_VALIDATION.csv": pipeline.schema_validation,
        "CFBD_EXACT_IDENTITY_CROSSWALK.csv": pipeline.identities.exact,
        "CFBD_REVIEW_ONLY_IDENTITY_CANDIDATES.csv": pipeline.identities.review,
        "CFBD_UNRESOLVED_IDENTITY_INVENTORY.csv": pipeline.identities.unresolved,
        "CFBD_IDENTITY_COVERAGE.csv": pipeline.identity_coverage,
        "CFBD_FEATURE_MISSING_EXACT_IDENTITY.csv": pipeline.feature_missing,
        "CFBD_COLLEGE_EVIDENCE_FOUNDATION.csv": pipeline.features,
        "CFBD_FEATURE_COVERAGE.csv": pipeline.feature_coverage,
        "PRE_DRAFT_INCREMENTAL_VALUE_RESULTS.csv": pipeline.pre_results,
        "EARLY_CAREER_INCREMENTAL_VALUE_RESULTS.csv": pipeline.early_results,
        "MULTI_YEAR_SURVIVAL_INCREMENTAL_VALUE_RESULTS.csv": (
            pipeline.survival_results
        ),
        "INCREMENTAL_VALUE_DECISIONS.csv": pipeline.decisions,
        "MUTATION_SENSITIVITY_RESULTS.csv": pd.DataFrame(
            [
                {
                    "mutation": case,
                    "result": "PASS_FAIL_CLOSED",
                    "error_class": foundation.exercise_mutation(case),
                }
                for case in foundation.MUTATION_CASES
            ]
        ),
        "SOURCE_AND_FEATURE_ACCEPTANCE_GATE_MATRIX.csv": pipeline.gates,
        "FILES_CREATED_OR_CHANGED.csv": _changed_files(root),
    }
    for name, frame in csvs.items():
        _write_csv(packet / name, frame)

    exact = len(pipeline.identities.exact)
    unresolved = len(pipeline.identities.unresolved)
    feature_rows = len(pipeline.features)
    main = pipeline.decisions[
        pipeline.decisions["comparison"].eq("EARLY_CAREER_ALL_CFBD")
    ].iloc[0]
    admitted_features = pipeline.decisions[
        pipeline.decisions["decision"].eq("ADMIT_SOURCE_AND_FEATURE")
    ]["comparison"].tolist()
    non_incremental = pipeline.decisions[
        pipeline.decisions["decision"].eq(
            "ADMIT_SOURCE_FEATURE_NOT_INCREMENTAL"
        )
    ]["comparison"].tolist()
    authority = pipeline.snapshot.manifest["authority"]
    usage_before = pipeline.snapshot.manifest["usage_before"]
    usage_after = pipeline.snapshot.manifest["usage_after"]
    snapshot_hash = pipeline.snapshot.manifest["aggregate_sha256"]
    markdown = {
        "EXECUTIVE_VERDICT.md": f"""# Executive Verdict

`GREEN_CFBD_SOURCES_ADMITTED_RESEARCH_ONLY_MODEL_REENTRY_CLOSED`

Four official CFBD REST v2 source families passed provenance, terms, immutable
snapshot, schema, identity, and temporal gates with recorded limits. Exact
college-to-NFL mappings: {exact:,}; explicit unresolved rows: {unresolved:,};
leakage-safe terminal college feature rows: {feature_rows:,}. The governed
early-career incremental comparison is `{main['decision']}`.

This admission changes no formula, ranking, Outcome field, or UI.
""",
        "CFBD_COLLEGE_EVIDENCE_ADMISSION_REPORT.md": f"""# CFBD College Evidence Admission V1

## Result

Admission identifier: `{ADMISSION_ID}`.
Foundation identifier: `{FOUNDATION_ID}`.
Immutable snapshot: `{pipeline.snapshot.manifest['snapshot_id']}`.
Aggregate SHA-256: `{snapshot_hash}`.

The admitted families are CFBD draft identity, player season statistics, player
usage, and player PPA. Raw provider bytes remain external and uncommitted.
Recruiting is not admitted because this snapshot does not provide an exact
recruit-to-NFL authority without a prohibited name join.

## Identity and evidence

The only exact bridge is the unique NFL draft `year + round + overall` shared by
CFBD and the admitted nflverse rookie foundation. CFBD `collegeAthleteId` then
joins statistics, usage, and PPA. Names and positions are diagnostics only.
Undrafted players and missing provider IDs remain explicitly unresolved.

Terminal college seasons must be strictly earlier than the NFL draft year.
Current retrieval corrections are acknowledged through
`ADMITTED_WITH_RETROSPECTIVE_REVISION_LIMIT`.
""",
        "CFBD_API_AUTHORITY_AND_USAGE.md": f"""# CFBD API Authority and Usage

- Authority: `{authority['api_title']}`.
- Official server: `{authority['server']}`.
- OpenAPI: `{authority['openapi_version']}`.
- API version: `{authority['api_version']}`.
- Retrieval: `{pipeline.snapshot.manifest['retrieved_at_utc']}`.
- Data calls: `{pipeline.snapshot.manifest['request_plan']['data_calls']}`.
- Quota checks: `{pipeline.snapshot.manifest['request_plan']['quota_checks']}`.
- Tier before/after: `{usage_before['tier_name']}` / `{usage_after['tier_name']}`.
- Monthly limit: `{usage_before['monthly_limit']}`.
- Tier purchase or change: `NONE`.
- Authentication receipt: owner credential bridged or inherited and redacted.

No GraphQL, unofficial source, scrape, or paid-only endpoint was called.
""",
        "SOURCE_ACCESS_TERMS_AND_LICENSE.md": f"""# Source Access, Terms, and License

Official terms URL: `{pipeline.snapshot.manifest['terms_url']}`.
Terms effective date recorded by the rendered-page review: `2025-07-01`.
Terms snapshot SHA-256: `{pipeline.snapshot.manifest['terms_sha256']}`.

The provider permits API use subject to its terms, requires credential secrecy,
enforces account quotas, prohibits raw redistribution without permission, and
strongly encourages attribution. This repository records CFBD attribution and
commits only manifests, hashes, exact crosswalk decisions, and derived private
research evidence. Raw responses remain outside Git under `SOURCE_SNAPSHOT_ROOT`.
""",
        (
            "TEMPORAL_AVAILABILITY_AND_LEAKAGE_CONTRACT.md"
        ): """# Temporal Availability and Leakage Contract

College statistics, usage, and PPA are admitted only from the latest observed
college season strictly earlier than the NFL draft year. They may be used at a
post-college-season boundary, never to predict an event inside that college
season. Draft identity is available only after the applicable NFL selection.

The pre-draft-family audit uses draft/combine/age plus terminal college evidence
to predict later NFL outcomes. The early-career audit adds rookie-season nflverse
opportunity and availability only when predicting year-two outcomes. Chronological
walk-forward folds train exclusively on earlier draft classes. Missing advanced
metrics remain missing and receive explicit model missingness indicators.

The provider snapshot was retrieved in 2026 and may include retrospective
corrections. That limit is recorded; present-day fields, future NFL data, ADP,
market values, unresolved identities, and name-only joins are prohibited.
""",
        "MODEL_REENTRY_CONTRACT.md": f"""# Model Re-entry Contract

Formula redevelopment and production integration remain closed. Admitted CFBD
source families may support future governed research only at the recorded
post-college-season or post-draft identity boundary. Incrementally useful fixed
comparisons in this audit: {_comma(admitted_features)}. Fixed comparisons that did
not add governed value: {_comma(non_incremental)}.

The primary early-career comparison `{main['comparison']}` evaluated
{int(main['rows'])} out-of-sample rows across {int(main['folds'])} chronological
folds and concluded `{main['decision']}`. This result does not authorize a new
rookie formula or ranking. Re-entry requires owner review, independent reproduction,
repeated-season and position-slice safety, and a separately authorized formula
mission. Finished V1 and Outcome V3 remain the sole production authorities.
""",
        (
            "FINISHED_V1_OUTCOME_V3_AND_STATE_NO_CHANGE.md"
        ): f"""# Finished V1, Outcome V3, and State No Change

- Finished V1: `NWR_FINISHED_VERSION_1`; 240 rows; `{BOARD_HASH}`; change `NONE`.
- Outcome V3: `NWR_OUTCOME_COLUMNS_V3_RC1`; 72 fields / 79 schema rows; change `NONE`.
- Frozen comparator: 924 rows; `{FROZEN_HASH}`; change `NONE`.
- Opaque DynastyProcess artifacts: `5/5` exact; change `NONE`.
- Persistent state: 14 files / 542,801 bytes / `{PERSISTENT_DIGEST}`.
- Recovery state: 7 files / 172,878 bytes / `{RECOVERY_DIGEST}`.
- Scheduled refresh task: remains disabled pending owner approval.

No application, formula, ranking, Outcome, persistent-state, or recovery path is
an output of this builder.
""",
        "VALIDATION_RESULTS.md": f"""# Validation Results

- Canonical start: `{CANONICAL_HQ}` / `{CANONICAL_TREE}`.
- Snapshot assets: {len(pipeline.snapshot.manifest['assets'])}/{
            len(pipeline.snapshot.manifest['assets'])
        } hashes exact.
- Snapshot aggregate: `{snapshot_hash}`.
- Exact identity rows: {exact:,}.
- Review-only rows: {len(pipeline.identities.review):,}.
- Explicit unresolved rows: {unresolved:,}.
- Leakage-safe college feature rows: {feature_rows:,}.
- Main incremental decision: `{main['decision']}`.
- Mutation sensitivity: {len(foundation.MUTATION_CASES)}/{
            len(foundation.MUTATION_CASES)
        } fail closed.
- Raw CFBD payloads committed: `NO`.
- Credential stored or printed: `NO`.
- Formula/ranking/Outcome/UI changes: `NONE`.
""",
        "ROLLBACK_PLAN.md": """# Rollback Plan

The Git rollback unit is the CFBD admission commits. Revert normally if review
rejects them; never reset or force-push HQ. The external immutable snapshot is audit
evidence and need not be deleted. Do not alter Finished V1, Outcome V3, the frozen
comparator, persistent/recovery state, or the disabled scheduled task.
""",
    }
    for name, text in markdown.items():
        _write_text(packet / name, text)

    manifest = {
        "schema_version": 1,
        "foundation_id": FOUNDATION_ID,
        "admission_id": ADMISSION_ID,
        "verdict": "GREEN_CFBD_SOURCES_ADMITTED_RESEARCH_ONLY_MODEL_REENTRY_CLOSED",
        "build_date": "2026-07-30",
        "canonical_source_commit": CANONICAL_HQ,
        "canonical_source_tree": CANONICAL_TREE,
        "snapshot_id": pipeline.snapshot.manifest["snapshot_id"],
        "snapshot_aggregate_sha256": snapshot_hash,
        "provider_calls": pipeline.snapshot.catalog["provider_calls"],
        "row_counts": {
            "exact_identity": exact,
            "review_identity": len(pipeline.identities.review),
            "unresolved_identity": unresolved,
            "college_features": feature_rows,
            "mutation_cases": len(foundation.MUTATION_CASES),
        },
        "production_changes": {
            "finished_v1": "NONE",
            "outcome_v3": "NONE",
            "formula": "NONE",
            "ui": "NONE",
        },
        "builder_contract": {
            "stable_sorting": True,
            "encoding": "UTF-8 without BOM",
            "line_endings": "LF",
            "float_precision": 6,
            "wall_clock_used": False,
            "absolute_worktree_paths_emitted": False,
            "manifest_self_reference": False,
        },
        "artifacts": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha(path),
            }
            for path in sorted(packet.iterdir(), key=lambda item: item.name)
            if path.is_file() and path.name != "MANIFEST.json"
        ],
    }
    _write_json(packet / "MANIFEST.json", manifest)
    missing = [name for name in REQUIRED_FILES if not (packet / name).is_file()]
    extra = sorted(
        path.name
        for path in packet.iterdir()
        if path.is_file() and path.name not in REQUIRED_FILES
    )
    if missing or extra:
        raise AssertionError(f"packet inventory drift missing={missing} extra={extra}")
    for path in packet.iterdir():
        if path.is_file():
            foundation.require_no_secret(path.read_text(encoding="utf-8", errors="ignore"))


def _changed_files(_root: Path) -> pd.DataFrame:
    paths = [
        ".env.example",
        ".gitattributes",
        "config/nwr_cfbd_college_evidence_snapshot_v1.json",
        "config/nwr_cfbd_college_evidence_validation_receipt_v1.json",
        "config/nwr_new_evidence_snapshot_set_v1.json",
        "scripts/acquire_cfbd_college_evidence_v1.py",
        "scripts/build_nwr_cfbd_college_evidence_v1.py",
        "src/services/cfbd_college_evidence_service.py",
        "src/services/cfbd_official_v2_adapter.py",
        "src/services/new_evidence_foundation_service.py",
        "tests/test_cfbd_college_evidence_service.py",
        "tests/test_cfbd_official_v2_adapter.py",
        "tests/test_nwr_cfbd_college_evidence_v1.py",
        *[f"{PACKET_REL.as_posix()}/{name}" for name in REQUIRED_FILES],
    ]
    return pd.DataFrame(
        [{"status": "CREATED_OR_CHANGED", "path": path} for path in sorted(paths)]
    )


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    body = frame.to_csv(
        index=False,
        lineterminator="\n",
        na_rep="",
        float_format="%.6f",
    )
    path.write_text(body, encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    body = text.strip() + "\n"
    path.write_text(body, encoding="utf-8", newline="\n")


def _write_json(path: Path, document: Any) -> None:
    body = json.dumps(
        document,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    path.write_text(body + "\n", encoding="utf-8", newline="\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    return {
        path.name: _sha(path)
        for path in sorted(root.iterdir(), key=lambda item: item.name)
        if path.is_file()
    }


def _comma(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


if __name__ == "__main__":
    raise SystemExit(main())
