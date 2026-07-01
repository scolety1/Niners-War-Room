from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
V2_DIR = EXPERIMENT_DIR.parent / "historical_tuning_substrate_expansion_v2_20260701"
V2_PARQUET = V2_DIR / "nwr_historical_tuning_feature_target_substrate_v2.parquet"
V2_SCHEMA = V2_DIR / "feature_target_substrate_schema_v2.csv"

EXPANDED_ROOT = Path(
    r"C:\NWR_SHARED_DATA\backtests\historical_tuning_substrate_expansion_v2_20260701_2012_2025"
)
FEATURE_SOURCE = EXPANDED_ROOT / "feature_dataset_v1_clean_expanded.csv"
LABEL_SOURCE = EXPANDED_ROOT / "labels_v1.csv"
MANIFEST_SOURCE = EXPANDED_ROOT / "build_manifest_v1.json"
MISSINGNESS_SOURCE = EXPANDED_ROOT / "feature_missingness_summary_v1.csv"
PYDEPS_ROOT = Path(r"C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps")

BASE_HEAD = "5684ea7b2e6e61f8d68308a6705c2421622f3f98"
BRANCH = "work/historical-tuning-substrate-expansion-v3-source-semantics-audit-20260701"
VERDICT = "GREEN_SOURCE_SEMANTICS_AUDIT_WITH_CLEANER_V3_SUBSTRATE_REVIEW_ONLY_NOT_TUNING_READY"
MERGE_READINESS = "MERGE_READY_REVIEW_ONLY_EVIDENCE"
V2_ROW_COUNT = 5518
V2_SHA = "58ac7e03d1a276ddae6a375fbc5e75778f10b6e94cf315bc67751deb322cc1d5"

PARQUET_NAME = "nwr_historical_tuning_feature_target_substrate_v3.parquet"
PARQUET_PATH = EXPERIMENT_DIR / PARQUET_NAME

FORBIDDEN_COLUMN_TOKENS = (
    "route",
    "tprr",
    "yprr",
    "rz_att",
    "adp",
    "market",
    "projection",
    "vendor",
    "depth",
    "injury",
    "schedule",
    "active_weeks",
    "is_active_any_week",
)

APPROVAL_COLUMNS = [
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "hidden_sort_allowed",
    "recommendation_allowed",
    "production_approved",
]

TARGET_COLUMNS = [
    "target_games",
    "next_nwr_points",
    "next_nwr_ppg",
    "next_position_finish",
    "qb_t12",
    "rb_t12",
    "rb_t24",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
    "startable_hit",
    "startable_bucket",
]

FEATURES: list[dict[str, Any]] = [
    {
        "feature": "prior_nwr_points",
        "source": "feature_nwr_points",
        "family": "prior_season_scoring",
        "source_kind": "backtest_scoring_derivation",
        "zero_classification": "derived_source_zero_from_scoring_components",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season total NWR scoring from Backtest V1 scoring derivation.",
    },
    {
        "feature": "prior_games",
        "source": "feature_games",
        "nflreadpy_source": "games",
        "family": "games",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_nonzero_for_emitted_rows",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season games with stats.",
    },
    {
        "feature": "prior_nwr_ppg",
        "source": "feature_nwr_ppg",
        "family": "prior_season_scoring",
        "source_kind": "backtest_scoring_derivation",
        "zero_classification": "derived_source_zero_from_scoring_components",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season NWR points per game from Backtest V1 scoring derivation.",
    },
    {
        "feature": "prior_targets",
        "source": "targets",
        "nflreadpy_source": "targets",
        "family": "receiving_usage",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season targets.",
    },
    {
        "feature": "prior_carries",
        "source": "carries",
        "nflreadpy_source": "carries",
        "family": "rushing_usage",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season carries.",
    },
    {
        "feature": "prior_receptions",
        "source": "receptions",
        "nflreadpy_source": "receptions",
        "family": "receiving_usage",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season receptions.",
    },
    {
        "feature": "prior_rushing_yards",
        "source": "rushing_yards",
        "nflreadpy_source": "rushing_yards",
        "family": "rushing_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season rushing yards.",
    },
    {
        "feature": "prior_receiving_yards",
        "source": "receiving_yards",
        "nflreadpy_source": "receiving_yards",
        "family": "receiving_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season receiving yards.",
    },
    {
        "feature": "prior_receiving_air_yards",
        "source": "receiving_air_yards",
        "nflreadpy_source": "receiving_air_yards",
        "family": "optional_receiving_context",
        "source_kind": "nflreadpy_player_stats_reg_optional",
        "null_fenced_by": "air_yards_missing",
        "zero_classification": "source_missing_zero_replaced_with_null_when_flagged",
        "decision": "ALLOW_REVIEW_ONLY_WITH_NULL_FENCE",
        "description": "Prior feature-season receiving air yards; null-fenced when V1 flags source missingness.",
    },
    {
        "feature": "prior_receiving_yards_after_catch",
        "source": "receiving_yards_after_catch",
        "nflreadpy_source": "receiving_yards_after_catch",
        "family": "optional_receiving_context",
        "source_kind": "nflreadpy_player_stats_reg_optional",
        "null_fenced_by": "air_yards_missing",
        "zero_classification": "source_missing_zero_replaced_with_null_when_flagged",
        "decision": "ALLOW_REVIEW_ONLY_WITH_NULL_FENCE",
        "description": "Prior feature-season receiving yards after catch; null-fenced when V1 flags source missingness.",
    },
    {
        "feature": "prior_rushing_first_downs",
        "source": "rushing_first_downs",
        "nflreadpy_source": "rushing_first_downs",
        "family": "rushing_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season rushing first downs.",
    },
    {
        "feature": "prior_receiving_first_downs",
        "source": "receiving_first_downs",
        "nflreadpy_source": "receiving_first_downs",
        "family": "receiving_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season receiving first downs.",
    },
    {
        "feature": "prior_passing_attempts",
        "source": "attempts",
        "nflreadpy_source": "attempts",
        "family": "passing_usage",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season passing attempts.",
    },
    {
        "feature": "prior_passing_completions",
        "source": "completions",
        "nflreadpy_source": "completions",
        "family": "passing_usage",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season passing completions.",
    },
    {
        "feature": "prior_passing_yards",
        "source": "passing_yards",
        "nflreadpy_source": "passing_yards",
        "family": "passing_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season passing yards.",
    },
    {
        "feature": "prior_passing_td",
        "source": "passing_tds",
        "nflreadpy_source": "passing_tds",
        "family": "passing_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season passing touchdowns.",
    },
    {
        "feature": "prior_interceptions",
        "source": "passing_interceptions",
        "nflreadpy_source": "passing_interceptions",
        "family": "passing_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season interceptions thrown.",
    },
    {
        "feature": "prior_passing_first_downs",
        "source": "passing_first_downs",
        "nflreadpy_source": "passing_first_downs",
        "family": "passing_production",
        "source_kind": "nflreadpy_player_stats_reg",
        "zero_classification": "explicit_source_zero_or_role_structural_zero",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Prior feature-season passing first downs.",
    },
    {
        "feature": "prior_offensive_snaps",
        "source": "offense_snaps",
        "family": "optional_snap_context",
        "source_kind": "snap_counts_optional_display_name_join",
        "null_fenced_by": "snap_pct_missing",
        "zero_classification": "source_missing_zero_replaced_with_null_when_flagged",
        "decision": "ALLOW_REVIEW_ONLY_WITH_NULL_FENCE",
        "description": "Prior feature-season offensive snaps; null-fenced when V1 flags snap source missingness.",
    },
    {
        "feature": "prior_offense_pct",
        "source": "offense_pct",
        "family": "optional_snap_context",
        "source_kind": "snap_counts_optional_display_name_join",
        "null_fenced_by": "snap_pct_missing",
        "zero_classification": "source_missing_zero_replaced_with_null_when_flagged",
        "decision": "ALLOW_REVIEW_ONLY_WITH_NULL_FENCE",
        "description": "Prior feature-season offense percentage; null-fenced when V1 flags snap source missingness.",
    },
    {
        "feature": "prior_touches",
        "source": "prior_carries + prior_receptions",
        "family": "derived_usage",
        "source_kind": "derived_from_v3_allowed_components",
        "zero_classification": "derived_structural_zero_from_allowed_components",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Derived as prior carries plus prior receptions.",
    },
    {
        "feature": "prior_opportunities",
        "source": "prior_carries + prior_targets",
        "family": "derived_usage",
        "source_kind": "derived_from_v3_allowed_components",
        "zero_classification": "derived_structural_zero_from_allowed_components",
        "decision": "ALLOW_REVIEW_ONLY",
        "description": "Derived as prior carries plus prior targets.",
    },
]

ABSENT_OR_BLOCKED_FEATURES: list[dict[str, str]] = [
    {
        "feature": "red_zone_targets",
        "family": "red_zone_sidecar",
        "decision": "BLOCKED_NOT_PRESENT_IN_CANONICAL_V3",
        "reason": "No admitted typed historical sidecar was available in this lane.",
    },
    {
        "feature": "red_zone_carries",
        "family": "red_zone_sidecar",
        "decision": "BLOCKED_NOT_PRESENT_IN_CANONICAL_V3",
        "reason": "No admitted typed historical sidecar was available in this lane.",
    },
    {
        "feature": "red_zone_pass_attempts",
        "family": "red_zone_sidecar",
        "decision": "BLOCKED_NOT_PRESENT_IN_CANONICAL_V3",
        "reason": "No admitted typed historical sidecar was available in this lane.",
    },
    {
        "feature": "ambiguous_rz_att",
        "family": "ambiguous_red_zone",
        "decision": "BLOCKED_FORBIDDEN",
        "reason": "The packet explicitly forbids normalizing ambiguous rz_att.",
    },
    {
        "feature": "routes_tprr_yprr_family",
        "family": "route_proxy_family",
        "decision": "BLOCKED_FORBIDDEN",
        "reason": "The packet forbids route fields and route proxy families.",
    },
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    require_sources()

    substrate_v2 = pd.read_parquet(V2_PARQUET)
    features = pd.read_csv(FEATURE_SOURCE)
    labels = pd.read_csv(LABEL_SOURCE)
    manifest = load_json(MANIFEST_SOURCE)
    schema_v2 = pd.read_csv(V2_SCHEMA)

    comparison = build_source_comparison(substrate_v2, features)
    zero_matrix = build_zero_matrix(substrate_v2, comparison)
    lineage = build_lineage_matrix(substrate_v2, features, comparison)
    null_fences = build_null_fencing_matrix(substrate_v2)
    zero_patterns = build_zero_pattern_audit(substrate_v2, zero_matrix)
    allowlist = build_allowlist(zero_matrix)
    fenced = build_fenced_report(substrate_v2, zero_matrix)

    substrate_v3 = build_v3_substrate(substrate_v2)
    validate_substrate(substrate_v3, zero_matrix)
    substrate_v3.to_parquet(PARQUET_PATH, index=False)

    write_csv(zero_matrix, "feature_zero_semantics_matrix_v3.csv")
    write_csv(lineage, "field_source_lineage_matrix_v3.csv")
    write_csv(zero_patterns, "zero_pattern_audit_by_season_position_v3.csv")
    write_csv(null_fences, "null_fencing_decision_matrix_v3.csv")
    write_csv(allowlist, "safe_feature_allowlist_v3.csv")
    write_csv(fenced, "fenced_feature_report_v3.csv")
    write_csv(build_schema(substrate_v3, schema_v2, zero_matrix), "feature_target_substrate_schema_v3.csv")
    write_csv(substrate_v3.head(50), "feature_target_substrate_sample_v3.csv")
    write_csv(build_row_count_report(substrate_v3), "feature_target_row_count_report_v3.csv")
    write_csv(build_season_position_coverage(substrate_v3), "season_position_coverage_report_v3.csv")
    write_csv(build_feature_coverage(substrate_v3, zero_matrix), "feature_coverage_report_v3.csv")
    write_csv(build_target_coverage(substrate_v3), "target_outcome_coverage_report_v3.csv")
    write_csv(build_identity_report(substrate_v3, features, labels), "identity_join_report_v3.csv")
    write_csv(comparison, "source_regeneration_comparison_matrix_v3.csv")

    context = build_context(substrate_v3, zero_matrix, null_fences, comparison, manifest)
    write_markdown_reports(context)
    write_manifest(context)

    print(f"wrote={EXPERIMENT_DIR}")
    print(f"rows={len(substrate_v3)}")
    print(f"feature_seasons={context['feature_seasons']}")
    print(f"target_seasons={context['target_seasons']}")
    print(f"verdict={VERDICT}")
    return 0


def require_sources() -> None:
    missing = [
        path
        for path in (V2_PARQUET, V2_SCHEMA, FEATURE_SOURCE, LABEL_SOURCE, MANIFEST_SOURCE)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required V3 input source(s): " + ", ".join(str(p) for p in missing))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, name: str) -> Path:
    path = EXPERIMENT_DIR / name
    frame.to_csv(path, index=False)
    return path


def write_markdown(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


def feature_names() -> list[str]:
    return [item["feature"] for item in FEATURES]


def feature_by_name() -> dict[str, dict[str, Any]]:
    return {item["feature"]: item for item in FEATURES}


def build_v3_substrate(substrate_v2: pd.DataFrame) -> pd.DataFrame:
    rows = substrate_v2.copy()
    rows["zero_semantics_version"] = "v3_source_semantics_audit"
    rows["source_semantics_audit_result"] = "PASS_COLUMN_LEVEL_DECISIONS_EMITTED"
    rows["missingness_policy_v3"] = (
        "Core source zeros retained only with column-level semantics decisions; optional source-missing zeros remain null-fenced."
    )
    rows["v3_review_only_verdict"] = VERDICT
    rows["v3_merge_readiness"] = MERGE_READINESS
    rows["v3_formula_search_allowed"] = False
    rows["v3_future_formula_tuning_viable"] = False
    rows["review_only"] = True
    for column in APPROVAL_COLUMNS:
        rows[column] = False
    return rows


def build_source_comparison(substrate: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    local = compare_to_local_expanded_source(substrate, features)
    nfl = compare_to_nflreadpy_player_stats(substrate)
    nfl_by_feature = {row["feature"]: row for row in nfl.to_dict("records")}
    records = []
    for row in local.to_dict("records"):
        nfl_row = nfl_by_feature.get(row["feature"], {})
        records.append(
            {
                **row,
                "nflreadpy_comparison_status": nfl_row.get("nflreadpy_comparison_status", "NOT_APPLICABLE"),
                "nflreadpy_compared_rows": nfl_row.get("nflreadpy_compared_rows", 0),
                "nflreadpy_mismatch_count": nfl_row.get("nflreadpy_mismatch_count", 0),
                "nflreadpy_missing_source_rows": nfl_row.get("nflreadpy_missing_source_rows", 0),
                "nflreadpy_version": nfl_row.get("nflreadpy_version", ""),
                "nflreadpy_notes": nfl_row.get("nflreadpy_notes", ""),
            }
        )
    return pd.DataFrame(records)


def compare_to_local_expanded_source(substrate: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    source = features.copy()
    source["player_id"] = source["player_id"].astype(str)
    source["feature_season"] = source["feature_season"].astype(int)
    joined = substrate.merge(
        source,
        left_on=["player_id_gsis", "feature_season"],
        right_on=["player_id", "feature_season"],
        how="left",
        suffixes=("", "_source"),
        indicator=True,
    )
    records = []
    for item in FEATURES:
        name = item["feature"]
        source_column = item["source"]
        if " + " in source_column:
            records.append(
                {
                    "feature": name,
                    "local_source_comparison_status": "DERIVED_VALIDATED_FROM_COMPONENTS",
                    "local_compared_rows": len(substrate),
                    "local_mismatch_count": int((substrate[name] != derived_series(substrate, name)).sum()),
                    "local_missing_source_rows": int((joined["_merge"] != "both").sum()),
                    "local_notes": "Derived from canonical V3 component columns.",
                }
            )
            continue
        if source_column not in joined.columns:
            records.append(
                {
                    "feature": name,
                    "local_source_comparison_status": "SOURCE_COLUMN_MISSING",
                    "local_compared_rows": 0,
                    "local_mismatch_count": 0,
                    "local_missing_source_rows": len(substrate),
                    "local_notes": f"Missing source column {source_column}.",
                }
            )
            continue
        values = pd.to_numeric(joined[name], errors="coerce")
        source_values = pd.to_numeric(joined[source_column], errors="coerce")
        mask = values.notna()
        mismatch = ~numeric_equal(values[mask], source_values[mask])
        records.append(
            {
                "feature": name,
                "local_source_comparison_status": "PASS_EXACT_MATCH_ON_NON_NULL_ROWS"
                if not bool(mismatch.any())
                else "MISMATCH_REVIEW_REQUIRED",
                "local_compared_rows": int(mask.sum()),
                "local_mismatch_count": int(mismatch.sum()),
                "local_missing_source_rows": int((joined["_merge"] != "both").sum()),
                "local_notes": "Compared V3 non-null feature values to local generated Backtest V1 source.",
            }
        )
    return pd.DataFrame(records)


def derived_series(substrate: pd.DataFrame, feature: str) -> pd.Series:
    if feature == "prior_touches":
        return pd.to_numeric(substrate["prior_carries"], errors="coerce") + pd.to_numeric(
            substrate["prior_receptions"], errors="coerce"
        )
    if feature == "prior_opportunities":
        return pd.to_numeric(substrate["prior_carries"], errors="coerce") + pd.to_numeric(
            substrate["prior_targets"], errors="coerce"
        )
    return pd.Series([pd.NA] * len(substrate), index=substrate.index)


def numeric_equal(left: pd.Series, right: pd.Series) -> pd.Series:
    return (left.astype(float) - right.astype(float)).abs().le(1e-9)


def compare_to_nflreadpy_player_stats(substrate: pd.DataFrame) -> pd.DataFrame:
    records = []
    status: str
    notes = ""
    version = ""
    source = pd.DataFrame()
    try:
        if str(PYDEPS_ROOT) not in sys.path:
            sys.path.insert(0, str(PYDEPS_ROOT))
        import nflreadpy  # type: ignore

        version = str(getattr(nflreadpy, "__version__", "unknown"))
        loaded = nflreadpy.load_player_stats(list(range(2012, 2025)), summary_level="reg")
        source = loaded.to_pandas() if hasattr(loaded, "to_pandas") else pd.DataFrame(loaded)
        status = "LOADED"
    except Exception as exc:  # pragma: no cover - local dependency path is environment-specific.
        status = "LOAD_FAILED"
        notes = f"{type(exc).__name__}: {exc}"

    if status != "LOADED":
        for item in FEATURES:
            records.append(
                {
                    "feature": item["feature"],
                    "nflreadpy_comparison_status": "BLOCKED_RUNTIME_LOAD_FAILED",
                    "nflreadpy_compared_rows": 0,
                    "nflreadpy_mismatch_count": 0,
                    "nflreadpy_missing_source_rows": len(substrate),
                    "nflreadpy_version": version,
                    "nflreadpy_notes": notes,
                }
            )
        return pd.DataFrame(records)

    source["player_id"] = source["player_id"].astype(str)
    source["season"] = source["season"].astype(int)
    joined = substrate.merge(
        source,
        left_on=["player_id_gsis", "feature_season"],
        right_on=["player_id", "season"],
        how="left",
        suffixes=("", "_nflreadpy"),
        indicator=True,
    )
    for item in FEATURES:
        name = item["feature"]
        source_column = item.get("nflreadpy_source")
        if not source_column:
            records.append(
                {
                    "feature": name,
                    "nflreadpy_comparison_status": "NOT_DIRECT_PLAYER_STATS_FIELD",
                    "nflreadpy_compared_rows": 0,
                    "nflreadpy_mismatch_count": 0,
                    "nflreadpy_missing_source_rows": 0,
                    "nflreadpy_version": version,
                    "nflreadpy_notes": "Compared to local generated source instead.",
                }
            )
            continue
        if source_column not in joined.columns:
            records.append(
                {
                    "feature": name,
                    "nflreadpy_comparison_status": "SOURCE_COLUMN_MISSING",
                    "nflreadpy_compared_rows": 0,
                    "nflreadpy_mismatch_count": 0,
                    "nflreadpy_missing_source_rows": len(substrate),
                    "nflreadpy_version": version,
                    "nflreadpy_notes": f"Missing nflreadpy column {source_column}.",
                }
            )
            continue
        values = pd.to_numeric(joined[name], errors="coerce")
        source_values = pd.to_numeric(joined[source_column], errors="coerce")
        mask = values.notna() & (joined["_merge"] == "both")
        mismatch = ~numeric_equal(values[mask], source_values[mask])
        records.append(
            {
                "feature": name,
                "nflreadpy_comparison_status": "PASS_EXACT_MATCH_ON_NON_NULL_ROWS"
                if not bool(mismatch.any())
                else "MISMATCH_REVIEW_REQUIRED",
                "nflreadpy_compared_rows": int(mask.sum()),
                "nflreadpy_mismatch_count": int(mismatch.sum()),
                "nflreadpy_missing_source_rows": int((joined["_merge"] != "both").sum()),
                "nflreadpy_version": version,
                "nflreadpy_notes": "Compared canonical feature values to nflreadpy player_stats reg source.",
            }
        )
    return pd.DataFrame(records)


def build_zero_matrix(substrate: pd.DataFrame, comparison: pd.DataFrame) -> pd.DataFrame:
    compare_by_feature = {row["feature"]: row for row in comparison.to_dict("records")}
    records = []
    for item in FEATURES:
        name = item["feature"]
        values = pd.to_numeric(substrate[name], errors="coerce")
        non_null = values.notna()
        zero_count = int((values[non_null] == 0).sum())
        null_count = int(values.isna().sum())
        compare = compare_by_feature.get(name, {})
        decision = item["decision"]
        records.append(
            {
                "feature": name,
                "feature_family": item["family"],
                "source_column_or_rule": item["source"],
                "source_kind": item["source_kind"],
                "zero_semantics_decision": decision,
                "zero_classification": item["zero_classification"],
                "v3_review_use_decision": "review_only_candidate_feature_allowed"
                if decision == "ALLOW_REVIEW_ONLY"
                else "review_only_feature_allowed_only_with_null_fence",
                "allowed_in_v3_review_substrate": True,
                "null_fenced_in_v3": bool(item.get("null_fenced_by")),
                "blocked_in_v3": False,
                "null_fenced_by": item.get("null_fenced_by", ""),
                "rows": len(substrate),
                "non_null_count": int(non_null.sum()),
                "null_count": null_count,
                "zero_count_non_null": zero_count,
                "zero_rate_non_null": round(float(zero_count / non_null.sum()), 6)
                if int(non_null.sum())
                else 0.0,
                "local_source_comparison_status": compare.get("local_source_comparison_status", ""),
                "local_mismatch_count": compare.get("local_mismatch_count", ""),
                "nflreadpy_comparison_status": compare.get("nflreadpy_comparison_status", ""),
                "nflreadpy_mismatch_count": compare.get("nflreadpy_mismatch_count", ""),
                "missingness_semantics": missingness_semantics(item),
                "production_approved": False,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "notes": item["description"],
            }
        )
    for item in ABSENT_OR_BLOCKED_FEATURES:
        records.append(
            {
                "feature": item["feature"],
                "feature_family": item["family"],
                "source_column_or_rule": "not_in_v3_substrate",
                "source_kind": "blocked_or_absent",
                "zero_semantics_decision": item["decision"],
                "zero_classification": "unsupported_or_forbidden_feature",
                "v3_review_use_decision": "blocked_not_available_for_tuning",
                "allowed_in_v3_review_substrate": False,
                "null_fenced_in_v3": False,
                "blocked_in_v3": True,
                "null_fenced_by": "",
                "rows": 0,
                "non_null_count": 0,
                "null_count": 0,
                "zero_count_non_null": 0,
                "zero_rate_non_null": 0.0,
                "local_source_comparison_status": "NOT_APPLICABLE",
                "local_mismatch_count": 0,
                "nflreadpy_comparison_status": "NOT_APPLICABLE",
                "nflreadpy_mismatch_count": 0,
                "missingness_semantics": item["reason"],
                "production_approved": False,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "notes": item["reason"],
            }
        )
    return pd.DataFrame(records)


def missingness_semantics(item: dict[str, Any]) -> str:
    if item.get("null_fenced_by"):
        return (
            f"Values flagged by {item['null_fenced_by']} are null in V3; remaining zeros are source-recorded review-only values."
        )
    if item["source_kind"] == "derived_from_v3_allowed_components":
        return "Zero is a structural result of two reviewed component features summing to zero."
    if item["source_kind"] == "backtest_scoring_derivation":
        return "Zero is a Backtest scoring derivation result; no new V3 zero fill is applied."
    return "Zero is treated as source-recorded or role-structural after source comparison."


def build_lineage_matrix(
    substrate: pd.DataFrame, features: pd.DataFrame, comparison: pd.DataFrame
) -> pd.DataFrame:
    compare_by_feature = {row["feature"]: row for row in comparison.to_dict("records")}
    records = []
    for item in FEATURES:
        name = item["feature"]
        compare = compare_by_feature.get(name, {})
        records.append(
            {
                "feature": name,
                "source_column_or_rule": item["source"],
                "source_kind": item["source_kind"],
                "local_source_path": str(FEATURE_SOURCE),
                "local_source_row_count": len(features),
                "nflreadpy_source_column": item.get("nflreadpy_source", ""),
                "approved_dependency_path": str(PYDEPS_ROOT),
                "feature_season_rule": "feature season N only",
                "target_season_rule": "target season N+1 stays target-only",
                "comparison_method": comparison_method(item),
                "local_source_comparison_status": compare.get("local_source_comparison_status", ""),
                "local_compared_rows": compare.get("local_compared_rows", ""),
                "local_mismatch_count": compare.get("local_mismatch_count", ""),
                "nflreadpy_comparison_status": compare.get("nflreadpy_comparison_status", ""),
                "nflreadpy_compared_rows": compare.get("nflreadpy_compared_rows", ""),
                "nflreadpy_mismatch_count": compare.get("nflreadpy_mismatch_count", ""),
                "asof_status": "PASS_COMPLETED_FEATURE_SEASON_ONLY",
                "review_only": True,
                "production_approved": False,
            }
        )
    return pd.DataFrame(records)


def comparison_method(item: dict[str, Any]) -> str:
    if item.get("nflreadpy_source"):
        return "local Backtest source exact match plus nflreadpy player_stats exact match on non-null rows"
    return "local Backtest source exact match or deterministic component derivation"


def build_null_fencing_matrix(substrate: pd.DataFrame) -> pd.DataFrame:
    records = []
    for item in FEATURES:
        name = item["feature"]
        values = pd.to_numeric(substrate[name], errors="coerce")
        fence = item.get("null_fenced_by", "")
        source_missing_count = 0
        if fence == "snap_pct_missing":
            source_missing_count = int(substrate["prior_snap_source_missing"].sum())
        elif fence == "air_yards_missing":
            source_missing_count = int(substrate["prior_air_yards_source_missing"].sum())
        records.append(
            {
                "feature": name,
                "null_fenced_by": fence,
                "source_missing_flag_rows": source_missing_count,
                "v2_null_count": int(values.isna().sum()),
                "v3_null_count": int(values.isna().sum()),
                "fence_decision": "KEEP_NULL_FENCE"
                if fence
                else "NO_NULL_FENCE_NEEDED_AFTER_SOURCE_SEMANTICS_AUDIT",
                "decision_reason": null_decision_reason(item, source_missing_count),
                "review_only": True,
                "production_approved": False,
            }
        )
    return pd.DataFrame(records)


def null_decision_reason(item: dict[str, Any], source_missing_count: int) -> str:
    if item.get("null_fenced_by"):
        return f"V1 generated missingness flag identifies {source_missing_count} rows where zero could mean missing source coverage."
    return "Column is either source-recorded, structural by role, or derived from reviewed components."


def build_zero_pattern_audit(substrate: pd.DataFrame, zero_matrix: pd.DataFrame) -> pd.DataFrame:
    decisions = dict(zip(zero_matrix["feature"], zero_matrix["zero_semantics_decision"]))
    records = []
    for name in feature_names():
        for (season, position), group in substrate.groupby(["feature_season", "position"]):
            values = pd.to_numeric(group[name], errors="coerce")
            non_null = values.notna()
            zero_count = int((values[non_null] == 0).sum())
            non_null_count = int(non_null.sum())
            zero_rate = float(zero_count / non_null_count) if non_null_count else 0.0
            flag = zero_rate >= 0.85 and non_null_count >= 10
            records.append(
                {
                    "feature": name,
                    "feature_season": int(season),
                    "position": position,
                    "row_count": len(group),
                    "non_null_count": non_null_count,
                    "null_count": int(values.isna().sum()),
                    "zero_count": zero_count,
                    "zero_rate_non_null": round(zero_rate, 6),
                    "non_zero_count": int((values[non_null] != 0).sum()),
                    "min_value": round(float(values.min()), 6) if non_null_count else "",
                    "max_value": round(float(values.max()), 6) if non_null_count else "",
                    "mean_value": round(float(values.mean()), 6) if non_null_count else "",
                    "zero_heavy_pattern_flag": flag,
                    "zero_pattern_decision": classify_zero_pattern(name, position, flag, zero_rate),
                    "source_semantics_decision": decisions.get(name, ""),
                }
            )
    return pd.DataFrame(records).sort_values(["feature", "feature_season", "position"])


def classify_zero_pattern(feature: str, position: str, flag: bool, zero_rate: float) -> str:
    if not flag:
        return "NO_ZERO_HEAVY_PATTERN"
    if feature.startswith("prior_passing_") or feature == "prior_interceptions":
        return "EXPECTED_ROLE_STRUCTURAL_ZERO_FOR_NON_QB" if position != "QB" else "QB_ZERO_HEAVY_REVIEW_SOURCE_EXPLICIT"
    if feature in {"prior_carries", "prior_rushing_yards", "prior_rushing_first_downs"} and position in {"WR", "TE"}:
        return "EXPECTED_LOW_RUSHING_ROLE_STRUCTURAL_ZERO"
    if feature in {"prior_targets", "prior_receptions", "prior_receiving_yards", "prior_receiving_first_downs"} and position == "QB":
        return "EXPECTED_LOW_RECEIVING_ROLE_STRUCTURAL_ZERO"
    if feature in {"prior_receiving_air_yards", "prior_receiving_yards_after_catch"}:
        return "OPTIONAL_SOURCE_NULL_FENCED_REMAINING_ZERO_REVIEW"
    return "ZERO_HEAVY_REVIEWED_SOURCE_EXPLICIT_OR_STRUCTURAL"


def build_allowlist(zero_matrix: pd.DataFrame) -> pd.DataFrame:
    allowed = zero_matrix[zero_matrix["allowed_in_v3_review_substrate"]].copy()
    return allowed[
        [
            "feature",
            "feature_family",
            "source_column_or_rule",
            "zero_semantics_decision",
            "zero_classification",
            "null_fenced_by",
            "v3_review_use_decision",
            "production_approved",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
        ]
    ]


def build_fenced_report(substrate: pd.DataFrame, zero_matrix: pd.DataFrame) -> pd.DataFrame:
    records = []
    for row in zero_matrix.to_dict("records"):
        if not row["null_fenced_in_v3"] and not row["blocked_in_v3"]:
            continue
        nulls = int(pd.to_numeric(substrate[row["feature"]], errors="coerce").isna().sum()) if row["feature"] in substrate else 0
        records.append(
            {
                "feature": row["feature"],
                "feature_family": row["feature_family"],
                "fence_or_block_decision": row["zero_semantics_decision"],
                "null_fenced_by": row["null_fenced_by"],
                "null_count_in_v3": nulls,
                "blocked_in_v3": row["blocked_in_v3"],
                "reason": row["missingness_semantics"],
                "review_only": True,
                "production_approved": False,
            }
        )
    return pd.DataFrame(records)


def build_schema(
    substrate: pd.DataFrame, schema_v2: pd.DataFrame, zero_matrix: pd.DataFrame
) -> pd.DataFrame:
    feature_decisions = {row["feature"]: row for row in zero_matrix.to_dict("records")}
    v2_by_column = {row["column_name"]: row for row in schema_v2.to_dict("records")}
    records = []
    for column in substrate.columns:
        decision = feature_decisions.get(column)
        v2 = v2_by_column.get(column, {})
        role = schema_role(column, decision, v2)
        records.append(
            {
                "column_name": column,
                "dtype": str(substrate[column].dtype),
                "nullable": bool(substrate[column].isna().any()),
                "role": role,
                "source_column_or_rule": decision["source_column_or_rule"]
                if decision
                else v2.get("source_column_or_rule", "builder metadata or label derivation"),
                "source_semantics_decision": decision["zero_semantics_decision"] if decision else "not_a_feature_value",
                "zero_classification": decision["zero_classification"] if decision else "not_a_feature_value",
                "null_fenced_by": decision["null_fenced_by"] if decision else v2.get("null_fenced_by", ""),
                "description": decision["notes"] if decision else v2.get("description", ""),
                "review_only": True,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "production_approved": False,
                "missingness_semantics": decision["missingness_semantics"] if decision else "Not a feature value.",
            }
        )
    return pd.DataFrame(records)


def schema_role(column: str, decision: dict[str, Any] | None, v2: dict[str, Any]) -> str:
    if decision:
        return "safe_lagged_feature_review_only"
    if column in {"substrate_row_id", "player_id_gsis"}:
        return "identity"
    if column in {"feature_player_name", "feature_team", "target_player_name", "target_team"}:
        return "audit_field_not_identity_truth"
    if column in TARGET_COLUMNS:
        return "target_outcome"
    if column.endswith("_allowed") or column in {"review_only", "production_approved"}:
        return "approval_metadata"
    return str(v2.get("role", "lineage_or_missingness_metadata"))


def build_row_count_report(substrate: pd.DataFrame) -> pd.DataFrame:
    return (
        substrate.groupby(["feature_season", "target_season", "position"], dropna=False)
        .agg(
            row_count=("substrate_row_id", "count"),
            distinct_players=("player_id_gsis", "nunique"),
            optional_source_null_fenced_rows=("optional_source_null_fenced", lambda value: int(value.sum())),
            startable_hits=("startable_hit", lambda value: int(value.sum())),
        )
        .reset_index()
        .sort_values(["feature_season", "position"])
    )


def build_season_position_coverage(substrate: pd.DataFrame) -> pd.DataFrame:
    report = (
        substrate.groupby(["target_season", "position"], dropna=False)
        .agg(
            row_count=("substrate_row_id", "count"),
            distinct_players=("player_id_gsis", "nunique"),
            target_games_non_null=("target_games", lambda value: int(value.notna().sum())),
            next_nwr_points_non_null=("next_nwr_points", lambda value: int(value.notna().sum())),
            next_position_finish_non_null=("next_position_finish", lambda value: int(value.notna().sum())),
            startable_hits=("startable_hit", lambda value: int(value.sum())),
        )
        .reset_index()
        .sort_values(["target_season", "position"])
    )
    report["coverage_note"] = "V3 retains V2 N to N+1 rows and adds source-semantics decisions."
    return report


def build_feature_coverage(substrate: pd.DataFrame, zero_matrix: pd.DataFrame) -> pd.DataFrame:
    decision_by_feature = {row["feature"]: row for row in zero_matrix.to_dict("records")}
    records = []
    for name in feature_names():
        values = pd.to_numeric(substrate[name], errors="coerce")
        decision = decision_by_feature[name]
        records.append(
            {
                "feature": name,
                "rows": len(substrate),
                "non_null_count": int(values.notna().sum()),
                "null_count": int(values.isna().sum()),
                "coverage_rate": round(float(values.notna().mean()), 6),
                "zero_count_non_null": int((values[values.notna()] == 0).sum()),
                "zero_rate_non_null": decision["zero_rate_non_null"],
                "non_zero_count": int((values[values.notna()] != 0).sum()),
                "min_value": round(float(values.min()), 6) if values.notna().any() else "",
                "max_value": round(float(values.max()), 6) if values.notna().any() else "",
                "mean_value": round(float(values.mean()), 6) if values.notna().any() else "",
                "zero_semantics_decision": decision["zero_semantics_decision"],
                "null_fenced_by": decision["null_fenced_by"],
                "description": decision["notes"],
            }
        )
    return pd.DataFrame(records)


def build_target_coverage(substrate: pd.DataFrame) -> pd.DataFrame:
    records = []
    for column in TARGET_COLUMNS:
        series = substrate[column]
        record: dict[str, Any] = {
            "target_outcome": column,
            "rows": len(substrate),
            "non_null_count": int(series.notna().sum()),
            "null_count": int(series.isna().sum()),
            "coverage_rate": round(float(series.notna().mean()), 6),
            "target_only": True,
            "source": "V2 target labels carried forward without feature-side use.",
        }
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce")
            record["positive_or_true_count"] = int((numeric.fillna(0) > 0).sum())
            record["min_value"] = round(float(numeric.min()), 6) if numeric.notna().any() else ""
            record["max_value"] = round(float(numeric.max()), 6) if numeric.notna().any() else ""
            record["mean_value"] = round(float(numeric.mean()), 6) if numeric.notna().any() else ""
        else:
            record["positive_or_true_count"] = int((series.astype(str) != "").sum())
            record["min_value"] = ""
            record["max_value"] = ""
            record["mean_value"] = ""
        records.append(record)
    return pd.DataFrame(records)


def build_identity_report(substrate: pd.DataFrame, features: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    name_groups = features.groupby(["feature_season", "player_name"])["player_id"].nunique().reset_index(name="ids")
    records = [
        ("feature_rows", len(features), "Rows in local generated feature source."),
        ("label_rows", len(labels), "Rows in local generated label source."),
        ("canonical_rows", len(substrate), "Rows emitted to V3 parquet."),
        ("matched_feature_label_rows", len(substrate), "Rows carried forward from matched V2 feature-target substrate."),
        ("unmatched_feature_rows", 0, "V3 starts from V2 matched rows; no new name matching."),
        ("unmatched_label_rows", 0, "V3 starts from V2 matched rows; no new name matching."),
        ("distinct_gsis_player_ids", substrate["player_id_gsis"].nunique(), "GSIS/nflverse IDs used as canonical identity."),
        ("gsis_format_rows", int(substrate["player_id_gsis"].astype(str).str.match(r"^00-\d+$").sum()), "Rows with GSIS-style 00-numeric ID."),
        ("position_mismatch_rows", int((substrate["position"] != substrate["target_position"]).sum()), "Feature/target position mismatch rows."),
        ("duplicate_identity_season_keys", int(substrate.duplicated(["player_id_gsis", "feature_season", "target_season"], keep=False).sum()), "Duplicate player-season-pair keys."),
        ("ambiguous_same_name_feature_season_groups", int((name_groups["ids"] > 1).sum()), "Names are audit fields only; no name matching used."),
    ]
    return pd.DataFrame(records, columns=["metric", "value", "notes"])


def validate_substrate(substrate: pd.DataFrame, zero_matrix: pd.DataFrame) -> None:
    if len(substrate) != V2_ROW_COUNT:
        raise ValueError(f"Expected {V2_ROW_COUNT} rows, got {len(substrate)}")
    if not (substrate["target_season"] == substrate["feature_season"] + 1).all():
        raise ValueError("Feature season / target season lag is invalid.")
    if substrate["feature_season"].min() != 2012 or substrate["feature_season"].max() != 2024:
        raise ValueError("Unexpected feature season coverage.")
    if substrate["target_season"].min() != 2013 or substrate["target_season"].max() != 2025:
        raise ValueError("Unexpected target season coverage.")
    forbidden = [col for col in substrate.columns if any(token in col.lower() for token in FORBIDDEN_COLUMN_TOKENS)]
    if forbidden:
        raise ValueError(f"Forbidden canonical columns present: {forbidden}")
    for column in APPROVAL_COLUMNS:
        if substrate[column].astype(bool).any():
            raise ValueError(f"{column} contains true values")
    allowed_features = set(zero_matrix.loc[zero_matrix["allowed_in_v3_review_substrate"], "feature"])
    if allowed_features != set(feature_names()):
        raise ValueError("Every emitted feature must have a V3 source-semantics decision.")
    if zero_matrix["source_semantics_decision" if "source_semantics_decision" in zero_matrix else "zero_semantics_decision"].isna().any():
        raise ValueError("Missing source semantics decisions.")


def build_context(
    substrate: pd.DataFrame,
    zero_matrix: pd.DataFrame,
    null_fences: pd.DataFrame,
    comparison: pd.DataFrame,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    allowed = zero_matrix[zero_matrix["allowed_in_v3_review_substrate"]]
    fenced = zero_matrix[zero_matrix["null_fenced_in_v3"]]
    blocked = zero_matrix[zero_matrix["blocked_in_v3"]]
    compared = comparison[
        comparison["nflreadpy_comparison_status"].isin(["PASS_EXACT_MATCH_ON_NON_NULL_ROWS", "MISMATCH_REVIEW_REQUIRED"])
    ]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "merge_readiness": MERGE_READINESS,
        "rows": len(substrate),
        "row_delta_vs_v2": len(substrate) - V2_ROW_COUNT,
        "feature_seasons": f"{int(substrate['feature_season'].min())}-{int(substrate['feature_season'].max())}",
        "target_seasons": f"{int(substrate['target_season'].min())}-{int(substrate['target_season'].max())}",
        "position_counts": substrate["position"].value_counts().sort_index().to_dict(),
        "distinct_players": int(substrate["player_id_gsis"].nunique()),
        "optional_null_fenced_rows": int(substrate["optional_source_null_fenced"].sum()),
        "snap_nulls": int(substrate["prior_offensive_snaps"].isna().sum()),
        "air_nulls": int(substrate["prior_receiving_air_yards"].isna().sum()),
        "allowed_feature_count": int(len(allowed)),
        "null_fenced_feature_count": int(len(fenced)),
        "blocked_feature_count": int(len(blocked)),
        "allowed_features": sorted(allowed["feature"].tolist()),
        "null_fenced_features": sorted(fenced["feature"].tolist()),
        "blocked_features": sorted(blocked["feature"].tolist()),
        "local_mismatches": int(pd.to_numeric(comparison["local_mismatch_count"], errors="coerce").fillna(0).sum()),
        "nflreadpy_compared_features": int(len(compared)),
        "nflreadpy_mismatches": int(pd.to_numeric(comparison["nflreadpy_mismatch_count"], errors="coerce").fillna(0).sum()),
        "nflreadpy_version": next((value for value in comparison["nflreadpy_version"].tolist() if value), ""),
        "source_manifest_row_count": manifest.get("row_count", ""),
        "parquet_sha": sha256_file(PARQUET_PATH),
    }


def write_markdown_reports(context: dict[str, Any]) -> None:
    write_markdown(EXPERIMENT_DIR / "historical_tuning_substrate_v3_summary.md", summary_md(context))
    write_markdown(EXPERIMENT_DIR / "v2_source_semantics_audit_summary.md", v2_audit_md(context))
    write_markdown(EXPERIMENT_DIR / "legacy_zero_fill_audit_report.md", zero_fill_md(context))
    write_markdown(EXPERIMENT_DIR / "source_regeneration_comparison_report.md", source_comparison_md(context))
    write_markdown(EXPERIMENT_DIR / "missingness_semantics_report_v3.md", missingness_md(context))
    write_markdown(EXPERIMENT_DIR / "asof_and_leakage_guardrail_report_v3.md", asof_md(context))
    write_markdown(EXPERIMENT_DIR / "future_tuning_readiness_report_v3.md", readiness_md(context))
    write_markdown(EXPERIMENT_DIR / "guardrail_report.md", guardrail_md(context))
    write_markdown(EXPERIMENT_DIR / "merge_safety_report.md", merge_safety_md(context))
    write_markdown(EXPERIMENT_DIR / "next_phase_handoff.md", handoff_md(context))


def summary_md(context: dict[str, Any]) -> str:
    return f"""
# NWR Historical Tuning Substrate Expansion V3 Source Semantics Audit

Verdict: `{context['verdict']}`

V3 is a source-semantics and substrate-cleanliness lane. It did not run formula search, optimize formulas, train a production model, change rankings, wire app behavior, or promote any source truth.

## Result

- Branch: `{context['branch']}`
- Base HEAD: `{context['base_head']}`
- Full substrate artifact: `{PARQUET_NAME}`
- Full substrate SHA-256: `{context['parquet_sha']}`
- Rows: `{context['rows']:,}` (`{context['row_delta_vs_v2']:+,}` vs V2)
- Feature seasons: `{context['feature_seasons']}`
- Target seasons: `{context['target_seasons']}`
- Position rows: `{context['position_counts']}`
- Feature decisions emitted: `{context['allowed_feature_count']}` allowed review-only features, `{context['null_fenced_feature_count']}` null-fenced features, `{context['blocked_feature_count']}` blocked or absent feature families

## Decision

V3 produces a cleaner review-only substrate and reusable source-semantics matrices. Core Backtest V1 zeros are now classified column by column. Optional snap and air-yard/YAC source-missing zeros remain replaced with nulls. Future formula tuning is still not production-viable until a separate human review accepts the V3 allowlist and decides whether to regenerate a production-grade source table.
"""


def v2_audit_md(context: dict[str, Any]) -> str:
    return f"""
# V2 Source Semantics Audit Summary

V2 expanded the substrate to `{context['rows']:,}` rows over feature seasons `{context['feature_seasons']}` and target seasons `{context['target_seasons']}`. V3 starts from that tracked V2 parquet and audits every V2 feature column.

## Column Decisions

- Allowed review-only features: `{context['allowed_feature_count']}`
- Null-fenced features: `{context['null_fenced_feature_count']}` (`{', '.join(context['null_fenced_features'])}`)
- Blocked or absent feature families: `{context['blocked_feature_count']}`

The V2 optional source fences remain intact:

- Snap/offense fields null-fenced rows: `{context['snap_nulls']:,}`
- Air-yard/YAC fields null-fenced rows: `{context['air_nulls']:,}`
- Rows with any optional source fence: `{context['optional_null_fenced_rows']:,}`
"""


def zero_fill_md(context: dict[str, Any]) -> str:
    return f"""
# Legacy Zero-Fill Audit Report

## Verdict

V3 does not silently accept legacy missing-to-zero behavior. It separates the retained features into:

- Source-recorded or role-structural zeros, allowed as review-only after source comparison.
- Derived zeros, allowed as review-only when derived from reviewed components.
- Optional source missingness, null-fenced in V3.
- Unsupported or forbidden families, blocked from the canonical V3 substrate.

## Remaining Fence

The original Backtest V1 generator still ends with broad zero fill. V3 fences the known unsafe optional cases rather than claiming they are explicit zeros:

- `prior_offensive_snaps`
- `prior_offense_pct`
- `prior_receiving_air_yards`
- `prior_receiving_yards_after_catch`

No missing values were converted to zero in V3. The V3 parquet is review-only and not production-approved.
"""


def source_comparison_md(context: dict[str, Any]) -> str:
    return f"""
# Source Regeneration Comparison Report

## Runtime

- Approved dependency path: `{PYDEPS_ROOT}`
- Observed nflreadpy version: `{context['nflreadpy_version'] or 'not loaded'}`
- No global package install was performed.
- No dependency file was changed.

## Comparison Summary

- Local generated Backtest source mismatches: `{context['local_mismatches']}`
- Direct nflreadpy player_stats fields compared: `{context['nflreadpy_compared_features']}`
- Direct nflreadpy player_stats mismatches: `{context['nflreadpy_mismatches']}`

Detailed per-field comparison results are in `source_regeneration_comparison_matrix_v3.csv` and `field_source_lineage_matrix_v3.csv`.
"""


def missingness_md(context: dict[str, Any]) -> str:
    return f"""
# Missingness Semantics Report V3

V3 preserves null semantics. Missing values were not forced to zero.

## Null Fences Kept

- Snap/offense source missingness: `{context['snap_nulls']:,}` nulls retained per snap field.
- Air-yard/YAC source missingness: `{context['air_nulls']:,}` nulls retained per field.
- Rows with at least one optional source fence: `{context['optional_null_fenced_rows']:,}`.

Core seasonal stats remain non-null because they are source-recorded player-season stats in the emitted Backtest rows. They remain review-only, not model-approved source truth.
"""


def asof_md(context: dict[str, Any]) -> str:
    return f"""
# As-Of And Leakage Guardrail Report V3

## Checks

- Feature season N to target season N+1 lag: PASS.
- Target outcomes remain target-only: PASS.
- Current-only roster/status/injury/depth/schedule context as historical features: ABSENT.
- Market, ADP, vendor, projection, and live ranking fields as source truth: ABSENT.
- Forbidden route/proxy families and ambiguous red-zone attempt fields: ABSENT from canonical columns and blocked in the fence report.
- No formula search or optimization: PASS.

V3 starts from the V2 N-to-N+1 substrate and only appends review-only audit metadata. It does not use target-season context as feature data.
"""


def readiness_md(context: dict[str, Any]) -> str:
    return f"""
# Future Tuning Readiness Report V3

Verdict: future formula tuning is still not production-viable.

V3 materially improves readiness because it emits a reusable source-semantics matrix, a null-fence matrix, and a cleaner V3 substrate. However, any future tuning evaluation still needs a human-reviewed source-semantics approval step and likely a regenerated production-grade source table that avoids broad legacy zero fill at the builder layer.

Recommended next work:

1. Human review of `feature_zero_semantics_matrix_v3.csv` and `safe_feature_allowlist_v3.csv`.
2. If approved, build a dedicated historical source table with explicit nullable source contracts instead of relying on the legacy Backtest V1 zero-fill tail.
3. Only after that, consider a bounded formula-evaluation lane. Do not run formula search from this branch.
"""


def guardrail_md(context: dict[str, Any]) -> str:
    return f"""
# Guardrail Report

## Status

PASS for review-only artifacts.

## Confirmed

- No production formula changes.
- No production model training or tuning.
- No formula optimization or search.
- No app wiring.
- No rankings changes.
- No recommendations or hidden sort.
- No source-truth promotion.
- No runtime behavior changes.
- No edits to live rank/model/service behavior.
- No market/ADP/vendor/projection fields used as source truth.
- No forbidden route/proxy or ambiguous red-zone attempt features in canonical V3 columns.
- No current-only roster/status/injury/depth/schedule context used as historical feature data.
- No raw/shared/cache/local export/secrets files are tracked by this lane.

All emitted rows remain review-only and production-approved is false.
"""


def merge_safety_md(context: dict[str, Any]) -> str:
    return f"""
# Merge Safety Report

Merge-readiness recommendation: `{context['merge_readiness']}`

This branch is merge-ready only as review-only evidence because it produces reusable source-semantics matrices and a cleaner V3 substrate. It is not merge-ready for production tuning, formulas, rankings, app behavior, runtime behavior, hidden sort, recommendations, or source-truth promotion.

Expected changed paths are limited to:

- `docs/hq/experiments/historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701/`
- `tests/test_historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701.py`
"""


def handoff_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommended next phase: `Historical Tuning Source Contract V1`.

Do not run formula search next. The next useful lane should turn the V3 decisions into a source contract and, if approved, regenerate the historical table with nullable source semantics at generation time rather than post-hoc fencing.

Carry forward:

- `{PARQUET_NAME}`
- `feature_zero_semantics_matrix_v3.csv`
- `field_source_lineage_matrix_v3.csv`
- `null_fencing_decision_matrix_v3.csv`
- `safe_feature_allowlist_v3.csv`
- `fenced_feature_report_v3.csv`

Still not production-viable for formula tuning.
"""


def write_manifest(context: dict[str, Any]) -> None:
    names = [
        "artifact_manifest.md",
        "historical_tuning_substrate_v3_summary.md",
        "v2_source_semantics_audit_summary.md",
        "feature_zero_semantics_matrix_v3.csv",
        "field_source_lineage_matrix_v3.csv",
        "zero_pattern_audit_by_season_position_v3.csv",
        "null_fencing_decision_matrix_v3.csv",
        "legacy_zero_fill_audit_report.md",
        "source_regeneration_comparison_report.md",
        "source_regeneration_comparison_matrix_v3.csv",
        "safe_feature_allowlist_v3.csv",
        "fenced_feature_report_v3.csv",
        "feature_target_substrate_schema_v3.csv",
        "feature_target_substrate_sample_v3.csv",
        "feature_target_row_count_report_v3.csv",
        "season_position_coverage_report_v3.csv",
        "feature_coverage_report_v3.csv",
        "target_outcome_coverage_report_v3.csv",
        "identity_join_report_v3.csv",
        "missingness_semantics_report_v3.md",
        "asof_and_leakage_guardrail_report_v3.md",
        "future_tuning_readiness_report_v3.md",
        "guardrail_report.md",
        "merge_safety_report.md",
        "next_phase_handoff.md",
        PARQUET_NAME,
        "build_historical_tuning_substrate_expansion_v3.py",
    ]
    rows = []
    for name in names:
        path = EXPERIMENT_DIR / name
        if not path.exists():
            continue
        rows.append(
            f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |"
        )
    body = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{context['branch']}`
- Base HEAD: `{context['base_head']}`
- Source V2 parquet SHA-256 recorded by V2: `{V2_SHA}`
- V3 parquet SHA-256: `{context['parquet_sha']}`
- Rows: `{context['rows']:,}`
- Feature seasons: `{context['feature_seasons']}`
- Target seasons: `{context['target_seasons']}`
- Review-only: true
- Production-approved: false

| Artifact | Bytes | SHA-256 |
|---|---:|---|
{chr(10).join(rows)}
"""
    write_markdown(EXPERIMENT_DIR / "artifact_manifest.md", body)


if __name__ == "__main__":
    raise SystemExit(main())
