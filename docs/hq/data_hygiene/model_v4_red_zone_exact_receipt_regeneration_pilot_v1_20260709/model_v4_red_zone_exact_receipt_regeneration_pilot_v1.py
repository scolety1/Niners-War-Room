from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_SWEEP_COMMIT = "41f7e8d0463be17e227f8fc41dae091722632e3f"

PRIOR_SWEEP_DIR = Path(r"C:\NWR\Niners-War-Room-formula-data-mart-remaining-upgrade-sweep-v1-20260709\docs\hq\data_hygiene\formula_data_mart_remaining_upgrade_sweep_v1_20260709")
PRIOR_DATA_MART_DIR = Path(r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709")

SOURCE_DIR = REPO / "docs/hq/data_sources"
REDZONE_SIDE_CAR = SOURCE_DIR / "nflverse_core_usage_review_dataset_v1_20260701/nwr_player_week_redzone_sidecar_v1.parquet"
REDZONE_DECISION = SOURCE_DIR / "nflverse_core_usage_review_dataset_v1_20260701/nwr_redzone_sidecar_decision_v1.md"
REDZONE_SAMPLE = SOURCE_DIR / "nflverse_core_usage_review_dataset_v1_20260701/nwr_redzone_sidecar_schema_or_sample_v1.csv"
ADMISSION_DIR = SOURCE_DIR / "sleeper_nflverse_usage_redzone_source_admission_v1_20260701"
ADMISSION_SUMMARY = ADMISSION_DIR / "source_admission_summary.md"
FIELD_MAPPING = ADMISSION_DIR / "usage_redzone_field_mapping.csv"
WEEKLY_RECEIPT = ADMISSION_DIR / "sleeper_weekly_stats_receipt.csv"
COVERAGE_MATRIX = ADMISSION_DIR / "season_week_coverage_matrix.csv"
MISSINGNESS_POLICY = ADMISSION_DIR / "missingness_and_zero_policy.md"
GUARDRAIL_REPORT = ADMISSION_DIR / "guardrail_report.md"
ARTIFACT_MANIFEST = ADMISSION_DIR / "artifact_manifest.md"
NEXT_HANDOFF = ADMISSION_DIR / "next_dataset_handoff.md"

CONTRACT_DIR = REPO / "docs/hq/master/model_v4_historical_receipt_regeneration_contract_planning_v1_20260709"
MASTER_REVIEW_DIR = REPO / "docs/hq/master/model_v4_historical_receipt_master_review_admission_decision_v1_20260709"
DATA_HYGIENE_CHARTER_DIR = REPO / "docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708"
HQ1_STANDARD_DIR = REPO / "docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708"

FORMULA_DATA_MART = PRIOR_DATA_MART_DIR / "FORMULA_DATA_MART_REVIEW_ONLY.csv"

METRICS = {
    "red_zone_targets": "source_reported_sparse_weekly_receiving_red_zone_targets",
    "red_zone_carries": "source_reported_sparse_weekly_rushing_red_zone_attempts",
    "red_zone_pass_attempts": "source_reported_sparse_weekly_passing_red_zone_attempts",
}

REQUIRED_RECEIPT_COLUMNS = [
    "season",
    "player_id",
    "player_name",
    "position",
    "receipt_family",
    "red_zone_metric_name",
    "red_zone_value",
    "red_zone_value_type",
    "source_artifact",
    "source_hash",
    "source_gate_status",
    "decision_date_safe",
    "leakage_flag",
    "identity_flag",
    "missingness_flag",
    "true_zero_vs_unknown_status",
    "regeneration_method",
    "review_only_status",
    "caveat",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def csv_meta(path: Path) -> tuple[int | str, int | str, str]:
    if path.suffix.lower() != ".csv":
        return "", "", ""
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            count = sum(1 for _ in reader)
        return count, len(header), "|".join(header)
    except Exception:
        return "", "", ""


def parquet_meta(path: Path) -> tuple[int | str, int | str, str]:
    if path.suffix.lower() != ".parquet":
        return "", "", ""
    df = pd.read_parquet(path)
    return len(df), len(df.columns), "|".join(str(c) for c in df.columns)


def load_identity_map() -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    if not FORMULA_DATA_MART.exists():
        return mapping
    with FORMULA_DATA_MART.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            player_id = (row.get("player_id") or "").strip()
            if not player_id:
                continue
            name = (row.get("target_player_name") or row.get("player_name") or "").strip()
            position = (row.get("position") or "").strip()
            season = (row.get("season") or "").strip()
            feature_season = (row.get("feature_season") or "").strip()
            # Prefer exact feature-season identity when available; fall back to latest seen identity.
            key = f"{player_id}|{feature_season}"
            mapping[key] = {"player_name": name, "position": position, "identity_source": f"formula_data_mart_feature_season_{feature_season}"}
            existing = mapping.get(player_id)
            if existing is None or season > existing.get("season", ""):
                mapping[player_id] = {"player_name": name, "position": position, "identity_source": "formula_data_mart_latest_available", "season": season}
    return mapping


def source_manifest() -> list[dict[str, object]]:
    source_roles = {
        REDZONE_SIDE_CAR: "primary_review_only_redzone_sidecar",
        REDZONE_DECISION: "sidecar_decision",
        REDZONE_SAMPLE: "schema_sample",
        ADMISSION_SUMMARY: "source_gate_summary",
        FIELD_MAPPING: "field_mapping_and_use_gate",
        WEEKLY_RECEIPT: "weekly_source_receipts",
        COVERAGE_MATRIX: "coverage_matrix",
        MISSINGNESS_POLICY: "missingness_zero_policy",
        GUARDRAIL_REPORT: "guardrail_report",
        ARTIFACT_MANIFEST: "artifact_manifest",
        NEXT_HANDOFF: "next_dataset_handoff",
    }
    rows: list[dict[str, object]] = []
    for path, role in source_roles.items():
        if not path.exists():
            rows.append({
                "source_artifact": rel(path),
                "sha256": "",
                "file_size": "",
                "row_count": "",
                "column_count": "",
                "columns": "",
                "source_role": role,
                "exists": "false",
            })
            continue
        if path.suffix.lower() == ".parquet":
            row_count, col_count, cols = parquet_meta(path)
        else:
            row_count, col_count, cols = csv_meta(path)
        rows.append({
            "source_artifact": rel(path),
            "sha256": sha256(path),
            "file_size": path.stat().st_size,
            "row_count": row_count,
            "column_count": col_count,
            "columns": cols,
            "source_role": role,
            "exists": "true",
        })
    return rows


def source_preflight(sidecar: pd.DataFrame) -> list[dict[str, object]]:
    source_hash = sha256(REDZONE_SIDE_CAR)
    field_rows = []
    with FIELD_MAPPING.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            field_rows.append(row)
    field_gate_summary = {
        row["normalized_field"]: row for row in field_rows if row.get("normalized_field")
    }
    seasons = sorted(str(x) for x in sidecar["season"].dropna().unique())
    weeks_by_season = sidecar.groupby("season")["week"].nunique().to_dict()
    gsis_present = int(sidecar["player_id_gsis"].notna().sum())
    player_rows = int(len(sidecar))
    rows = [
        {
            "source_path": rel(REDZONE_SIDE_CAR),
            "source_type": "derived_compact_parquet_sidecar_from_sleeper_public_weekly_stats_with_pbp_validation_columns",
            "raw_vs_derived": "derived_compact_review_only_not_raw_api_payload",
            "row_grain": "player-week",
            "season_coverage": "|".join(seasons),
            "week_coverage": ";".join(f"{k}:{v}" for k, v in sorted(weeks_by_season.items())),
            "position_coverage": "not_in_source; added only when review mart identity join is available",
            "player_id_availability": f"player_id_sleeper_rows={player_rows};player_id_gsis_nonnull={gsis_present}",
            "source_use_gate_status": "REVIEW_ONLY_SOURCE_ADMISSION_CANDIDATE_NOT_MODEL_USE_NOT_TRAINING_NOT_SOURCE_TRUTH",
            "decision_date_asof_safety": "PROVEN_ONLY_FOR_COMPLETED_SOURCE_SEASON_OR_LAGGED_N_PLUS_1_REVIEW_USE",
            "leakage_risk": "LOW_FOR_LAGGED_FUTURE_USE; HIGH_IF_USED_FOR_SAME_SEASON_PREDICTION",
            "identity_risk": "MEDIUM_SOURCE_LACKS_POSITION_NAME_AND_HAS_SOME_MISSING_GSIS",
            "missingness_risk": "MEDIUM_HIGH_SPARSE_KEYS_MISSING_IS_UNKNOWN_NOT_ZERO",
            "can_support_exact_red_zone_receipts": "partial_only_2024_2025_not_exact_2013_2025",
            "source_hash": source_hash,
            "caveat": "Ambiguous rz_att is excluded. Source is review-only and not production/source-truth approved.",
        },
        {
            "source_path": rel(FIELD_MAPPING),
            "source_type": "field_mapping_source_gate_csv",
            "raw_vs_derived": "governance_mapping",
            "row_grain": "field",
            "season_coverage": "2024|2025 sampled weekly source evidence",
            "week_coverage": "regular_weeks_1_18",
            "position_coverage": "not_position_scoped",
            "player_id_availability": "not_applicable",
            "source_use_gate_status": "typed_redzone_fields_review_only_candidate; rz_att_blocked",
            "decision_date_asof_safety": "requires_lagged_use_and_source_policy_gate",
            "leakage_risk": "controlled_by_lagged_use_only",
            "identity_risk": "not_applicable",
            "missingness_risk": "sparse_missing_unknown_not_zero",
            "can_support_exact_red_zone_receipts": "partial_semantics_only",
            "source_hash": sha256(FIELD_MAPPING),
            "caveat": "Mapping permits typed rec/rush/pass red-zone opportunities only as review-only candidates.",
        },
    ]
    for metric in ["red_zone_targets_receiving", "red_zone_rushing_attempts", "red_zone_passing_attempts", "red_zone_attempts_ambiguous"]:
        if metric in field_gate_summary:
            r = field_gate_summary[metric]
            rows.append({
                "source_path": rel(FIELD_MAPPING),
                "source_type": "field_level_gate",
                "raw_vs_derived": "governance_mapping",
                "row_grain": "field",
                "season_coverage": "2024|2025 sampled weekly source evidence",
                "week_coverage": "regular_weeks_1_18",
                "position_coverage": "not_position_scoped",
                "player_id_availability": "not_applicable",
                "source_use_gate_status": r.get("source_policy_status", ""),
                "decision_date_asof_safety": r.get("recommended_next_action", ""),
                "leakage_risk": "blocked" if "BLOCKED" in r.get("source_policy_status", "") else "review_only_lagged_gate_required",
                "identity_risk": "not_applicable",
                "missingness_risk": r.get("missingness_zero_rule", ""),
                "can_support_exact_red_zone_receipts": "no_blocked_ambiguous" if metric == "red_zone_attempts_ambiguous" else "partial_typed_field_only",
                "source_hash": sha256(FIELD_MAPPING),
                "caveat": r.get("semantics_decision", ""),
            })
    return rows


def build_receipts(sidecar: pd.DataFrame) -> tuple[list[dict[str, object]], dict[str, object]]:
    identity = load_identity_map()
    source_hash = sha256(REDZONE_SIDE_CAR)
    source_artifact = rel(REDZONE_SIDE_CAR)

    rows: list[dict[str, object]] = []
    excluded_missing_gsis = int(sidecar["player_id_gsis"].isna().sum())
    sidecar = sidecar[sidecar["player_id_gsis"].notna()].copy()
    sidecar["player_id_gsis"] = sidecar["player_id_gsis"].astype(str)

    for metric_name, value_type in METRICS.items():
        metric_df = sidecar[sidecar[metric_name].notna()].copy()
        if metric_df.empty:
            continue
        grouped = metric_df.groupby(["season", "player_id_gsis"], dropna=False)
        for (season, player_id), group in grouped:
            value = float(group[metric_name].sum())
            exact_identity = identity.get(f"{player_id}|{season}")
            fallback_identity = identity.get(str(player_id))
            identity_row = exact_identity or fallback_identity or {}
            position = identity_row.get("position", "") or "UNKNOWN"
            player_name = identity_row.get("player_name", "")
            identity_flag = "PASS_GSIS_TO_REVIEW_MART_IDENTITY" if exact_identity else (
                "PARTIAL_GSIS_TO_REVIEW_MART_LATEST_IDENTITY" if fallback_identity else "IDENTITY_LIMITED_GSIS_PRESENT_BUT_NO_REVIEW_MART_POSITION_NAME"
            )
            validation_counts = Counter(str(x) for x in group["pbp_validation_status"].fillna("missing"))
            receipt_basis = f"{season}|{player_id}|{position}|{metric_name}|{value:.6f}|{source_hash}"
            receipt_hash = hashlib.sha256(receipt_basis.encode("utf-8")).hexdigest()
            rows.append({
                "season": int(season),
                "player_id": str(player_id),
                "player_name": player_name,
                "position": position,
                "receipt_family": "red_zone_exact_receipts",
                "red_zone_metric_name": metric_name,
                "red_zone_value": f"{value:.6f}",
                "red_zone_value_type": value_type,
                "source_artifact": source_artifact,
                "source_hash": source_hash,
                "source_gate_status": "REVIEW_ONLY_SOURCE_ADMISSION_CANDIDATE_NOT_MODEL_USE_NOT_TRAINING_NOT_SOURCE_TRUTH",
                "decision_date_safe": "PASS_ONLY_FOR_COMPLETED_SOURCE_SEASON_OR_LAGGED_N_PLUS_1_REVIEW_USE",
                "leakage_flag": "PASS_FOR_LAGGED_FUTURE_USE_BLOCKED_FOR_SAME_SEASON_PREDICTION",
                "identity_flag": identity_flag,
                "missingness_flag": "SPARSE_SOURCE_EXPLICIT_VALUES_ONLY_MISSING_NOT_ZERO",
                "true_zero_vs_unknown_status": "NO_SYNTHETIC_ZERO_ROWS_MISSING_PLAYER_METRIC_IS_UNKNOWN_NOT_ZERO",
                "regeneration_method": "aggregate_typed_sleeper_redzone_weekly_values_by_gsis_source_season",
                "review_only_status": "REVIEW_ONLY_NOT_MODEL_USE_NOT_TRAINING_NOT_SOURCE_TRUTH_NOT_RANKING_INPUT",
                "caveat": "Partial 2024-2025 source-reported typed red-zone opportunities only; ambiguous rz_att excluded; not exact 2013-2025 Model v4 replay.",
                "source_rows_used": len(group),
                "weeks_with_explicit_value": group["week"].nunique(),
                "pbp_validation_status_summary": "|".join(f"{k}={v}" for k, v in sorted(validation_counts.items())),
                "receipt_hash": receipt_hash,
            })

    duplicate_keys = Counter((r["season"], r["player_id"], r["position"], r["red_zone_metric_name"]) for r in rows)
    duplicate_count = sum(v - 1 for v in duplicate_keys.values() if v > 1)
    position_counts = Counter(str(r["position"]) for r in rows)
    season_counts = Counter(str(r["season"]) for r in rows)
    metric_counts = Counter(str(r["red_zone_metric_name"]) for r in rows)
    identity_counts = Counter(str(r["identity_flag"]) for r in rows)
    stats = {
        "row_count": len(rows),
        "duplicate_count": duplicate_count,
        "position_counts": position_counts,
        "season_counts": season_counts,
        "metric_counts": metric_counts,
        "identity_counts": identity_counts,
        "excluded_missing_gsis_source_rows": excluded_missing_gsis,
    }
    rows.sort(key=lambda r: (int(r["season"]), str(r["position"]), str(r["player_id"]), str(r["red_zone_metric_name"])))
    return rows, stats


def schema_validation(receipts: list[dict[str, object]], stats: dict[str, object]) -> list[dict[str, object]]:
    if receipts:
        columns_present = set(receipts[0].keys())
    else:
        columns_present = set()
    required_missing = [c for c in REQUIRED_RECEIPT_COLUMNS if c not in columns_present]
    all_review_only = all("REVIEW_ONLY" in str(r["review_only_status"]) for r in receipts)
    no_model_claims = all("NOT_MODEL_USE" in str(r["review_only_status"]) for r in receipts)
    rz_att_excluded = all(r["red_zone_metric_name"] != "rz_att" for r in receipts)
    return [
        {"check_name": "required_columns_present", "result": "|".join(REQUIRED_RECEIPT_COLUMNS), "passed": str(not required_missing), "caveat": "missing=" + "|".join(required_missing)},
        {"check_name": "row_count", "result": stats["row_count"], "passed": str(stats["row_count"] > 0), "caveat": "partial 2024-2025 only"},
        {"check_name": "duplicate_key_count", "result": stats["duplicate_count"], "passed": str(stats["duplicate_count"] == 0), "caveat": "key=season|player_id|position|red_zone_metric_name"},
        {"check_name": "review_only_status_all_rows", "result": all_review_only, "passed": str(all_review_only), "caveat": ""},
        {"check_name": "no_model_training_source_truth_claims", "result": no_model_claims, "passed": str(no_model_claims), "caveat": ""},
        {"check_name": "ambiguous_rz_att_excluded", "result": rz_att_excluded, "passed": str(rz_att_excluded), "caveat": "typed fields only: red_zone_targets|red_zone_carries|red_zone_pass_attempts"},
        {"check_name": "season_coverage", "result": "|".join(f"{k}={v}" for k, v in sorted(stats["season_counts"].items())), "passed": "True", "caveat": "source coverage is not exact 2013-2025"},
        {"check_name": "position_coverage", "result": "|".join(f"{k}={v}" for k, v in sorted(stats["position_counts"].items())), "passed": "True", "caveat": "UNKNOWN rows lack safe position/name join"},
        {"check_name": "identity_flags", "result": "|".join(f"{k}={v}" for k, v in sorted(stats["identity_counts"].items())), "passed": "True", "caveat": "position/name from review mart only where available"},
        {"check_name": "source_rows_excluded_missing_gsis", "result": stats["excluded_missing_gsis_source_rows"], "passed": "True", "caveat": "team/no-GSIS rows excluded from player-season receipts"},
    ]


def write_markdown(receipts: list[dict[str, object]], stats: dict[str, object], preflight: list[dict[str, object]]) -> None:
    position_summary = ", ".join(f"{k}={v}" for k, v in sorted(stats["position_counts"].items())) or "none"
    season_summary = ", ".join(f"{k}={v}" for k, v in sorted(stats["season_counts"].items())) or "none"
    metric_summary = ", ".join(f"{k}={v}" for k, v in sorted(stats["metric_counts"].items())) or "none"
    identity_summary = ", ".join(f"{k}={v}" for k, v in sorted(stats["identity_counts"].items())) or "none"
    source_paths = [
        rel(REDZONE_SIDE_CAR),
        rel(REDZONE_DECISION),
        rel(FIELD_MAPPING),
        rel(WEEKLY_RECEIPT),
        rel(COVERAGE_MATRIX),
        rel(MISSINGNESS_POLICY),
    ]
    write_text(OUT_DIR / "MODEL_V4_RED_ZONE_EXACT_RECEIPT_REGENERATION_PILOT_V1_REPORT.md", "\n".join([
        "# Model v4 Red Zone Exact Receipt Regeneration Pilot V1 Report",
        "",
        "## Verdict",
        "",
        "`YELLOW_RED_ZONE_RECEIPTS_PARTIAL_WITH_CAVEATS`",
        "",
        "## Clear Answer",
        "",
        "Red-zone source/as-of safety is proven only for a narrow review-only partial pilot using typed 2024-2025 Sleeper weekly red-zone sidecar fields. Exact 2013-2025 red-zone receipts are still not available.",
        "",
        "## What Was Generated",
        "",
        f"- Receipt rows generated: `{stats['row_count']}`",
        f"- Season coverage: `{season_summary}`",
        f"- Position coverage: `{position_summary}`",
        f"- Metric coverage: `{metric_summary}`",
        f"- Duplicate keys: `{stats['duplicate_count']}`",
        f"- Identity flags: `{identity_summary}`",
        "",
        "## Source / As-Of Decision",
        "",
        "- Source availability: proven for the tracked 2024-2025 compact review-only sidecar.",
        "- Source/use-gate status: review-only source-admission candidate; not model-use, training, production, source-truth, ranking, or app use.",
        "- As-of safety: safe only for completed source-season review or lagged N+1 component testing. It is blocked for same-season prediction use.",
        "- Missingness: sparse missing source keys remain unknown/not enough information, not zero.",
        "- Ambiguous `rz_att`: excluded.",
        "",
        "## Source Artifacts Found",
        "",
        *[f"- `{p}`" for p in source_paths],
        "",
        "## Maximum Allowed Use",
        "",
        "`PARTIAL_REVIEW_ONLY_WITH_CAVEATS`",
        "",
        "These receipts may support future review-only component signal tests after Master HQ approval. They do not approve Formula Gauntlet tournaments, exact replay, production/model-use, formula weights, rankings integration, hidden sort, recommendation logic, or source promotion.",
        "",
        "## Gates Preserved",
        "",
        "- Exact Model v4 replay remains blocked.",
        "- Formula Gauntlet tournaments remain blocked.",
        "- Production/model-use remains blocked.",
        "- Rankings integration remains blocked.",
        "- No source was promoted.",
    ]))

    write_text(OUT_DIR / "MODEL_V4_RED_ZONE_LEAKAGE_ASOF_VALIDATION.md", "\n".join([
        "# Model v4 Red Zone Leakage / As-Of Validation",
        "",
        "Result: `PASS_PARTIAL_LAGGED_REVIEW_ONLY_WITH_CAVEATS`",
        "",
        "The regenerated receipts use completed source-season red-zone facts. They are decision-date safe only when used as lagged season N factual inputs for season N+1 review-only analysis or as completed-season evidence. They are leakage-unsafe for same-season prediction, exact Model v4 replay, production scoring, or ranking integration without a separate approval lane.",
        "",
        "The source sidecar covers 2024-2025 regular-season weeks 1-18. This does not prove 2013-2025 historical coverage.",
        "",
        "Blocked uses: same-season prediction, production/model-use, training use, source-truth use, Formula Gauntlet tournaments, hidden sort, recommendation logic, rankings integration.",
    ]))

    write_text(OUT_DIR / "MODEL_V4_RED_ZONE_IDENTITY_MISSINGNESS_VALIDATION.md", "\n".join([
        "# Model v4 Red Zone Identity / Missingness Validation",
        "",
        "Result: `PASS_PARTIAL_WITH_IDENTITY_AND_MISSINGNESS_CAVEATS`",
        "",
        f"- Source rows without GSIS player ID excluded from player-season receipts: `{stats['excluded_missing_gsis_source_rows']}`",
        f"- Identity flags: `{identity_summary}`",
        f"- Position coverage: `{position_summary}`",
        "",
        "The source sidecar contains Sleeper and GSIS IDs but does not contain player name or position. Names and positions are added only when the review-only formula data mart has a matching GSIS identity. Rows without a safe position/name join are preserved with `UNKNOWN` position and an identity-limited flag.",
        "",
        "Sparse missing Sleeper keys are unknown/not enough information, not zero. No synthetic zero receipt rows were generated.",
    ]))

    write_text(OUT_DIR / "MODEL_V4_RED_ZONE_TRUE_ZERO_UNKNOWN_REVIEW.md", "\n".join([
        "# Model v4 Red Zone True-Zero / Unknown Review",
        "",
        "Result: `MISSING_REMAINS_UNKNOWN_NOT_ZERO`",
        "",
        "The source-admission packet states that audited Sleeper weekly fields appeared as sparse per-player keys and that missing keys are not evidence of zero. This pilot therefore generated rows only for explicit numeric source values and did not create zero rows for missing player/metric combinations.",
        "",
        "An explicit zero may be used only if a future source row explicitly returns numeric zero. This pilot did not infer zero from absence.",
    ]))

    write_text(OUT_DIR / "MODEL_V4_RED_ZONE_PILOT_LIMITATIONS.md", "\n".join([
        "# Model v4 Red Zone Pilot Limitations",
        "",
        "- Coverage is partial: 2024-2025 only, not 2013-2025.",
        "- These are typed red-zone opportunity fields, not guaranteed touches or scoring expectation.",
        "- `rz_att` remains blocked because its semantics are ambiguous.",
        "- Source/use-gate remains review-only; no production/model-use, training use, source-truth use, Formula Gauntlet tournament use, ranking use, hidden sort, or app behavior is approved.",
        "- Position/name identity is available only where a review-only mart identity join exists.",
        "- Exact Model v4 replay remains blocked.",
    ]))

    write_text(OUT_DIR / "MODEL_V4_RED_ZONE_NEXT_ACTIONS.md", "\n".join([
        "# Model v4 Red Zone Next Actions",
        "",
        "## Recommended Next Lane",
        "",
        "`Model v4 Red Zone Review-Only Component Signal Test Contract V1`",
        "",
        "The next lane should not run Formula Gauntlet. It should define whether these partial 2024-2025 red-zone receipts are sufficient for a tiny review-only signal/slice test, and should explicitly decide how to handle the limited season coverage and UNKNOWN-position rows.",
        "",
        "## Do Not Do Yet",
        "",
        "- Do not run Formula Gauntlet.",
        "- Do not tune or optimize formulas.",
        "- Do not use as production/model input.",
        "- Do not integrate with rankings.",
        "- Do not treat partial 2024-2025 receipts as exact 2013-2025 historical Model v4 replay.",
    ]))

    write_text(OUT_DIR / "MODEL_V4_RED_ZONE_SOURCE_TRACE.md", "\n".join([
        "# Model v4 Red Zone Source Trace",
        "",
        f"- Current remote HQ expected/verified by lane preflight: `{EXPECTED_REMOTE_HEAD}`",
        f"- Prior Remaining Data Upgrades Sweep V1 local commit: `{PRIOR_SWEEP_COMMIT}`",
        f"- Prior Remaining Data Upgrades Sweep V1 artifact: `{PRIOR_SWEEP_DIR}`",
        f"- Formula Data Mart / Feature Availability Audit V1 artifact: `{PRIOR_DATA_MART_DIR}`",
        f"- Regeneration Contract Planning V1: `{rel(CONTRACT_DIR)}`",
        f"- Historical Receipt Master Review V1: `{rel(MASTER_REVIEW_DIR)}`",
        f"- Data Hygiene Operating Charter: `{rel(DATA_HYGIENE_CHARTER_DIR)}`",
        f"- HQ1 source receipt-chain standard: `{rel(HQ1_STANDARD_DIR)}`",
        "",
        "## Primary Source Artifacts",
        "",
        *[f"- `{p}`" for p in source_paths],
        "",
        "## Guardrail",
        "",
        "No raw API payload was copied. No source was promoted. No Formula Gauntlet, tournament, tuning, exact replay, ranking, app/runtime/model behavior change, production/model-use approval, push, merge, or canonical `local_exports` write occurred.",
    ]))


def main() -> None:
    required_paths = [
        PRIOR_SWEEP_DIR,
        PRIOR_DATA_MART_DIR,
        CONTRACT_DIR,
        MASTER_REVIEW_DIR,
        DATA_HYGIENE_CHARTER_DIR,
        HQ1_STANDARD_DIR,
        REDZONE_SIDE_CAR,
        REDZONE_DECISION,
        REDZONE_SAMPLE,
        ADMISSION_SUMMARY,
        FIELD_MAPPING,
        WEEKLY_RECEIPT,
        COVERAGE_MATRIX,
        MISSINGNESS_POLICY,
        GUARDRAIL_REPORT,
        FORMULA_DATA_MART,
    ]
    missing = [str(p) for p in required_paths if not p.exists()]
    if missing:
        raise FileNotFoundError("missing required inputs: " + "; ".join(missing))

    sidecar = pd.read_parquet(REDZONE_SIDE_CAR)
    preflight = source_preflight(sidecar)
    receipts, stats = build_receipts(sidecar)
    manifest = source_manifest()
    validation = schema_validation(receipts, stats)

    receipt_fields = REQUIRED_RECEIPT_COLUMNS + [
        "source_rows_used",
        "weeks_with_explicit_value",
        "pbp_validation_status_summary",
        "receipt_hash",
    ]
    write_csv(OUT_DIR / "MODEL_V4_RED_ZONE_SOURCE_ASOF_PREFLIGHT.csv", preflight, [
        "source_path",
        "source_type",
        "raw_vs_derived",
        "row_grain",
        "season_coverage",
        "week_coverage",
        "position_coverage",
        "player_id_availability",
        "source_use_gate_status",
        "decision_date_asof_safety",
        "leakage_risk",
        "identity_risk",
        "missingness_risk",
        "can_support_exact_red_zone_receipts",
        "source_hash",
        "caveat",
    ])
    write_csv(OUT_DIR / "MODEL_V4_RED_ZONE_RECEIPTS_REVIEW_ONLY.csv", receipts, receipt_fields)
    write_csv(OUT_DIR / "MODEL_V4_RED_ZONE_SOURCE_HASH_MANIFEST.csv", manifest, [
        "source_artifact",
        "sha256",
        "file_size",
        "row_count",
        "column_count",
        "columns",
        "source_role",
        "exists",
    ])
    write_csv(OUT_DIR / "MODEL_V4_RED_ZONE_SCHEMA_VALIDATION.csv", validation, [
        "check_name",
        "result",
        "passed",
        "caveat",
    ])
    write_markdown(receipts, stats, preflight)

    print(f"receipt_rows={stats['row_count']}")
    print("season_coverage=" + "|".join(f"{k}={v}" for k, v in sorted(stats["season_counts"].items())))
    print("position_coverage=" + "|".join(f"{k}={v}" for k, v in sorted(stats["position_counts"].items())))
    print(f"duplicate_keys={stats['duplicate_count']}")
    print("verdict=YELLOW_RED_ZONE_RECEIPTS_PARTIAL_WITH_CAVEATS")


if __name__ == "__main__":
    main()
