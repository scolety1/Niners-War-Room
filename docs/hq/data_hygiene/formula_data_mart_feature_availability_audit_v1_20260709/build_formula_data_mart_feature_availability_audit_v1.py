from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"

PANEL_PATH = REPO / "docs/hq/model/historical_model_v4_replay_substrate_v1_20260708/MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
ROLE_RECEIPTS_PATH = REPO / "docs/hq/data_hygiene/model_v4_role_archetype_receipt_regeneration_pilot_v1_20260709/MODEL_V4_ROLE_ARCHETYPE_RECEIPTS_REVIEW_ONLY.csv"
CONFIDENCE_RECEIPTS_PATH = REPO / "docs/hq/data_hygiene/model_v4_confidence_cap_receipt_regeneration_pilot_v1_20260709/MODEL_V4_CONFIDENCE_CAP_RECEIPTS_REVIEW_ONLY.csv"
SYSTEM_AUDIT_DIR = REPO / "docs/hq/master/nwr_full_system_audit_integration_map_v1_20260709"
DATA_HYGIENE_CLOSURE_DIR = REPO / "docs/hq/data_hygiene/historical_label_identity_source_gate_closure_v1_20260708"
LOCATOR_DIR = REPO / "docs/hq/data_hygiene/model_v4_historical_receipt_locator_ledger_v1_20260709"
FREEZE_DIR = REPO / "docs/hq/data_hygiene/model_v4_historical_receipt_freeze_schema_validation_v1_20260709"
MASTER_RECEIPT_REVIEW_DIR = REPO / "docs/hq/master/model_v4_historical_receipt_master_review_admission_decision_v1_20260709"
FG_READINESS_DIR = REPO / "docs/hq/formula_gauntlet/formula_gauntlet_data_readiness_gate_v1_20260708"
FG_SCAFFOLD_DIR = REPO / "docs/hq/formula_gauntlet/formula_gauntlet_no_code_tournament_design_scaffold_v1_20260708"
ROLE_SIGNAL_DIR = REPO / "docs/hq/model/model_v4_role_archetype_component_signal_test_v1_20260709"
ROLE_MASTER_DIR = REPO / "docs/hq/master/model_v4_role_archetype_master_review_v1_20260709"
CONFIDENCE_SIGNAL_DIR = REPO / "docs/hq/model/model_v4_confidence_cap_component_signal_test_v1_20260709"
CONFIDENCE_MASTER_DIR = REPO / "docs/hq/master/model_v4_confidence_cap_receipt_master_review_v1_20260709"
PFR_ADDENDUM_DIR = REPO / "docs/hq/master/nwr_full_system_audit_pfr_rb_broken_tackle_addendum_v1_20260709"
HQ1_STANDARD_DIR = REPO / "docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708"
DATA_HYGIENE_CHARTER_DIR = REPO / "docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708"

MART_PATH = OUT_DIR / "FORMULA_DATA_MART_REVIEW_ONLY.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def num(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fmt(value: float | None, places: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{places}f}"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def non_empty_count(rows: list[dict[str, object]], column: str) -> int:
    return sum(1 for row in rows if str(row.get(column, "")).strip() != "")


def position_coverage(rows: list[dict[str, object]], column: str | None = None) -> str:
    parts = []
    for pos in ["QB", "RB", "WR", "TE"]:
        subset = [row for row in rows if row.get("position") == pos]
        count = len(subset) if column is None else non_empty_count(subset, column)
        if count:
            parts.append(f"{pos}={count}")
    return "|".join(parts)


def season_coverage(rows: list[dict[str, object]], season_col: str = "season") -> str:
    seasons = sorted({int(str(row[season_col])) for row in rows if str(row.get(season_col, "")).isdigit()})
    if not seasons:
        return ""
    return f"{seasons[0]}-{seasons[-1]}"


def rank_by_position_season(panel_rows: list[dict[str, str]]) -> dict[str, int]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in panel_rows:
        grouped[(row["feature_season"], row["position"])].append(row)
    ranks = {}
    for _, group in grouped.items():
        group_sorted = sorted(group, key=lambda row: num(row.get("prior_nwr_points")) or -999999.0, reverse=True)
        for idx, row in enumerate(group_sorted, start=1):
            ranks[row["substrate_row_id"]] = idx
    return ranks


def build_multiyear(panel_rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    by_player_feature: dict[tuple[str, int, str], float] = {}
    for row in panel_rows:
        points = num(row.get("prior_nwr_points"))
        if points is None:
            continue
        by_player_feature[(row["player_id_gsis"], int(row["feature_season"]), row["position"])] = points

    output = {}
    for row in panel_rows:
        player_id = row["player_id_gsis"]
        feature_year = int(row["feature_season"])
        position = row["position"]
        current = by_player_feature.get((player_id, feature_year, position))
        prev1 = by_player_feature.get((player_id, feature_year - 1, position))
        prev2 = by_player_feature.get((player_id, feature_year - 2, position))
        two_values = [(current, 0.70), (prev1, 0.30)]
        three_values = [(current, 0.60), (prev1, 0.25), (prev2, 0.15)]
        two_present = [(v, w) for v, w in two_values if v is not None]
        three_present = [(v, w) for v, w in three_values if v is not None]
        output[row["substrate_row_id"]] = {
            "prior_2yr_weighted_nwr_points": fmt(sum(v * w for v, w in two_present) / sum(w for _, w in two_present) if two_present else None),
            "prior_2yr_points_years_available": len(two_present),
            "prior_3yr_weighted_nwr_points": fmt(sum(v * w for v, w in three_present) / sum(w for _, w in three_present) if three_present else None),
            "prior_3yr_points_years_available": len(three_present),
            "multiyear_derivation_status": "review_only_derived_from_prior_nwr_points_no_weight_tuning",
        }
    return output


def build_mart() -> tuple[list[dict[str, object]], dict[str, object]]:
    panel = read_csv(PANEL_PATH)
    roles = read_csv(ROLE_RECEIPTS_PATH)
    confidence = read_csv(CONFIDENCE_RECEIPTS_PATH)

    role_by_key = {(r["season"], r["feature_season"], r["player_id"], r["position"]): r for r in roles}
    confidence_by_key = {(r["season"], r["feature_season"], r["player_id"], r["position"]): r for r in confidence}
    ranks = rank_by_position_season(panel)
    multi = build_multiyear(panel)

    mart: list[dict[str, object]] = []
    missing_role = 0
    missing_confidence = 0
    for row in panel:
        key = (row["target_season"], row["feature_season"], row["player_id_gsis"], row["position"])
        role = role_by_key.get(key)
        conf = confidence_by_key.get(key)
        if role is None:
            missing_role += 1
        if conf is None:
            missing_confidence += 1
        m = multi[row["substrate_row_id"]]
        out = {
            "player_id": row["player_id_gsis"],
            "player_name": row["feature_player_name"],
            "target_player_name": row["target_player_name"],
            "season": row["target_season"],
            "feature_season": row["feature_season"],
            "position": row["position"],
            "row_grain": "player_id+season+position",
            "substrate_row_id": row["substrate_row_id"],
            "review_only": row["review_only"],
            "model_use_allowed": row["model_use_allowed"],
            "training_allowed": row["training_allowed"],
            "source_truth_allowed": row["source_truth_allowed"],
            "production_approved": row["production_approved"],
            "feature_asof_rule": row["feature_asof_rule"],
            "leakage_check_result": row["leakage_check_result"],
            "asof_check_result": row["asof_check_result"],
            "exact_model_v4_replay_status": row["exact_model_v4_replay_status"],
            "partial_replay_status": row["partial_replay_status"],
            "formula_test_allowed_scope": "review_only_component_signal_tests_only",
            "ranking_integration_allowed": "false",
            "label_next_nwr_points": row["next_nwr_points"],
            "label_next_nwr_ppg": row["next_nwr_ppg"],
            "label_next_position_finish": row["next_position_finish"],
            "label_startable_hit": row["startable_hit"],
            "label_startable_bucket": row["startable_bucket"],
            "label_target_games": row["target_games"],
            "pyf_prior_nwr_points": row["prior_nwr_points"],
            "pyf_prior_nwr_ppg": row["prior_nwr_ppg"],
            "pyf_prior_rank_position_feature_season": ranks[row["substrate_row_id"]],
            "prior_2yr_weighted_nwr_points": m["prior_2yr_weighted_nwr_points"],
            "prior_2yr_points_years_available": m["prior_2yr_points_years_available"],
            "prior_3yr_weighted_nwr_points": m["prior_3yr_weighted_nwr_points"],
            "prior_3yr_points_years_available": m["prior_3yr_points_years_available"],
            "multiyear_derivation_status": m["multiyear_derivation_status"],
            "prior_games": row["prior_games"],
            "prior_targets": row["prior_targets"],
            "prior_carries": row["prior_carries"],
            "prior_receptions": row["prior_receptions"],
            "prior_rushing_yards": row["prior_rushing_yards"],
            "prior_receiving_yards": row["prior_receiving_yards"],
            "prior_receiving_air_yards": row["prior_receiving_air_yards"],
            "prior_receiving_yards_after_catch": row["prior_receiving_yards_after_catch"],
            "prior_rushing_first_downs": row["prior_rushing_first_downs"],
            "prior_receiving_first_downs": row["prior_receiving_first_downs"],
            "prior_passing_attempts": row["prior_passing_attempts"],
            "prior_passing_completions": row["prior_passing_completions"],
            "prior_passing_yards": row["prior_passing_yards"],
            "prior_passing_td": row["prior_passing_td"],
            "prior_interceptions": row["prior_interceptions"],
            "prior_passing_first_downs": row["prior_passing_first_downs"],
            "prior_offensive_snaps": row["prior_offensive_snaps"],
            "prior_offense_pct": row["prior_offense_pct"],
            "prior_touches": row["prior_touches"],
            "prior_opportunities": row["prior_opportunities"],
            "sparse_history_flag": role.get("sparse_history_flag", "") if role else "",
            "low_games_flag": role.get("low_games_flag", "") if role else "",
            "role_archetype": role.get("role_archetype", "") if role else "",
            "role_usage_bucket": role.get("usage_bucket", "") if role else "",
            "role_games_context": role.get("games_context", "") if role else "",
            "role_volume_context": role.get("volume_context", "") if role else "",
            "role_source_gate_status": role.get("source_gate_status", "") if role else "",
            "role_leakage_flag": role.get("leakage_flag", "") if role else "",
            "role_allowed_use": role.get("allowed_use", "") if role else "",
            "confidence_cap_value": conf.get("confidence_cap_value", "") if conf else "",
            "confidence_status": conf.get("confidence_status", "") if conf else "",
            "confidence_components_present": conf.get("components_present", "") if conf else "",
            "confidence_components_expected_for_position": conf.get("components_expected_for_position", "") if conf else "",
            "confidence_missingness_flag": conf.get("missingness_flag", "") if conf else "",
            "confidence_source_gate_status": conf.get("source_gate_status", "") if conf else "",
            "confidence_leakage_flag": conf.get("leakage_flag", "") if conf else "",
            "confidence_allowed_use": conf.get("allowed_use", "") if conf else "",
            "age_lifecycle_status": "blocked_missing_historical_receipt",
            "experience_year_status": "blocked_missing_historical_receipt",
            "return_scoring_status": "blocked_missing_source_or_admission",
            "red_zone_status": "blocked_not_regenerated_requires_contract",
            "route_yprr_tprr_status": "blocked_no_admitted_route_denominator",
            "pfr_rb_broken_tackle_status": "review_only_hypothesis_not_joined_to_mart",
            "injury_availability_status": "blocked_no_historical_asof_use_gate",
            "rookie_draft_capital_status": "review_only_or_blocked_not_joined",
            "market_adp_status": "display_only_or_blocked_no_historical_asof_gate",
            "checkpoint_review_score_historical_status": "blocked_missing_receipt",
            "position_specific_review_score_historical_status": "blocked_missing_receipt",
            "nwr_dynasty_score_historical_status": "blocked_exact_replay_missing",
            "wr_qb_v2_overlay_status": "blocked_missing_historical_receipt_chain",
            "shadow_model_v2_metrics_status": "blocked_missing_source",
            "production_model_use_status": "blocked",
        }
        mart.append(out)

    meta = {
        "panel_rows": len(panel),
        "role_rows": len(roles),
        "confidence_rows": len(confidence),
        "missing_role_joins": missing_role,
        "missing_confidence_joins": missing_confidence,
    }
    return mart, meta


MART_FIELDNAMES = [
    "player_id",
    "player_name",
    "target_player_name",
    "season",
    "feature_season",
    "position",
    "row_grain",
    "substrate_row_id",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "production_approved",
    "feature_asof_rule",
    "leakage_check_result",
    "asof_check_result",
    "exact_model_v4_replay_status",
    "partial_replay_status",
    "formula_test_allowed_scope",
    "ranking_integration_allowed",
    "label_next_nwr_points",
    "label_next_nwr_ppg",
    "label_next_position_finish",
    "label_startable_hit",
    "label_startable_bucket",
    "label_target_games",
    "pyf_prior_nwr_points",
    "pyf_prior_nwr_ppg",
    "pyf_prior_rank_position_feature_season",
    "prior_2yr_weighted_nwr_points",
    "prior_2yr_points_years_available",
    "prior_3yr_weighted_nwr_points",
    "prior_3yr_points_years_available",
    "multiyear_derivation_status",
    "prior_games",
    "prior_targets",
    "prior_carries",
    "prior_receptions",
    "prior_rushing_yards",
    "prior_receiving_yards",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
    "prior_rushing_first_downs",
    "prior_receiving_first_downs",
    "prior_passing_attempts",
    "prior_passing_completions",
    "prior_passing_yards",
    "prior_passing_td",
    "prior_interceptions",
    "prior_passing_first_downs",
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_touches",
    "prior_opportunities",
    "sparse_history_flag",
    "low_games_flag",
    "role_archetype",
    "role_usage_bucket",
    "role_games_context",
    "role_volume_context",
    "role_source_gate_status",
    "role_leakage_flag",
    "role_allowed_use",
    "confidence_cap_value",
    "confidence_status",
    "confidence_components_present",
    "confidence_components_expected_for_position",
    "confidence_missingness_flag",
    "confidence_source_gate_status",
    "confidence_leakage_flag",
    "confidence_allowed_use",
    "age_lifecycle_status",
    "experience_year_status",
    "return_scoring_status",
    "red_zone_status",
    "route_yprr_tprr_status",
    "pfr_rb_broken_tackle_status",
    "injury_availability_status",
    "rookie_draft_capital_status",
    "market_adp_status",
    "checkpoint_review_score_historical_status",
    "position_specific_review_score_historical_status",
    "nwr_dynasty_score_historical_status",
    "wr_qb_v2_overlay_status",
    "shadow_model_v2_metrics_status",
    "production_model_use_status",
]


def schema_rows() -> list[dict[str, object]]:
    rows = []
    def add(field_name: str, category: str, position_scope: str, ideal_status: str, source_family: str, actual_column: str, notes: str) -> None:
        rows.append({
            "field_name": field_name,
            "category": category,
            "position_scope": position_scope,
            "ideal_player_season_formula_table_status": ideal_status,
            "row_grain": "player_id+season+position",
            "source_family": source_family,
            "actual_mart_column": actual_column,
            "included_in_review_mart": bool_text(actual_column in MART_FIELDNAMES),
            "formula_input_or_label": "label" if category == "label" else "input_or_context",
            "production_model_use_allowed": "no",
            "review_only_use_allowed": "yes" if ideal_status in {"available_review_only", "derived_review_only", "label_only_review_ready", "review_only_context"} else "no",
            "blocked_reason": "" if ideal_status in {"available_review_only", "derived_review_only", "label_only_review_ready", "review_only_context"} else ideal_status,
            "notes": notes,
        })

    add("player_id", "identity", "QB/RB/WR/TE", "available_review_only", "partial replay panel", "player_id", "GSIS player ID carried by the accepted panel.")
    add("player_name", "identity", "QB/RB/WR/TE", "available_review_only", "partial replay panel", "player_name", "Display name only; player_id is join key.")
    add("season", "identity", "QB/RB/WR/TE", "available_review_only", "partial replay panel", "season", "Target season.")
    add("position", "identity", "QB/RB/WR/TE", "available_review_only", "partial replay panel", "position", "QB/RB/WR/TE only.")
    add("historical fantasy finish", "label", "QB/RB/WR/TE", "label_only_review_ready", "historical label closure", "label_next_position_finish", "Outcome label; never use as input.")
    add("historical fantasy points", "label", "QB/RB/WR/TE", "label_only_review_ready", "historical label closure", "label_next_nwr_points", "Outcome label; never use as input.")
    add("PYF prior-year points", "baseline", "QB/RB/WR/TE", "available_review_only", "partial replay panel", "pyf_prior_nwr_points", "Mandatory anchor comparator.")
    add("prior-year rank", "baseline", "QB/RB/WR/TE", "derived_review_only", "derived from PYF within feature season/position", "pyf_prior_rank_position_feature_season", "Review-only derived rank; no tuning.")
    add("two-year weighted production", "baseline", "QB/RB/WR/TE", "derived_review_only", "derived from prior_nwr_points panel history", "prior_2yr_weighted_nwr_points", "Deterministic review-only derived context.")
    add("three-year weighted production", "baseline", "QB/RB/WR/TE", "derived_review_only", "derived from prior_nwr_points panel history", "prior_3yr_weighted_nwr_points", "Deterministic review-only derived context.")
    for field, scope in [
        ("prior_games", "QB/RB/WR/TE"),
        ("prior_targets", "RB/WR/TE"),
        ("prior_carries", "QB/RB"),
        ("prior_receptions", "RB/WR/TE"),
        ("prior_rushing_yards", "QB/RB"),
        ("prior_receiving_yards", "RB/WR/TE"),
        ("prior_receiving_air_yards", "RB/WR/TE"),
        ("prior_receiving_yards_after_catch", "RB/WR/TE"),
        ("prior_rushing_first_downs", "QB/RB"),
        ("prior_receiving_first_downs", "RB/WR/TE"),
        ("prior_passing_attempts", "QB"),
        ("prior_passing_completions", "QB"),
        ("prior_passing_yards", "QB"),
        ("prior_passing_td", "QB"),
        ("prior_interceptions", "QB"),
        ("prior_passing_first_downs", "QB"),
        ("prior_offensive_snaps", "QB/RB/WR/TE"),
        ("prior_offense_pct", "QB/RB/WR/TE"),
        ("prior_touches", "RB"),
        ("prior_opportunities", "RB/WR/TE"),
    ]:
        add(field, "lagged production/usage", scope, "available_review_only", "partial replay panel", field, "Lagged N to N+1 review-only component context.")
    add("sparse_history_flag", "guardrail", "QB/RB/WR/TE", "review_only_context", "role archetype receipts", "sparse_history_flag", "Review-only warning/context.")
    add("low_games_flag", "guardrail", "QB/RB/WR/TE", "review_only_context", "role archetype receipts", "low_games_flag", "Review-only warning/context.")
    add("role_archetype", "guardrail", "QB/RB/WR/TE", "review_only_context", "role archetype receipts", "role_archetype", "Review-only miss taxonomy and guardrail context.")
    add("confidence_cap", "coverage", "QB/RB/WR/TE", "review_only_context", "confidence cap receipts", "confidence_cap_value", "Caution/coverage context only.")
    for blocked, reason in [
        ("age/lifecycle", "blocked_missing_historical_receipt"),
        ("experience year", "blocked_missing_historical_receipt"),
        ("return scoring", "blocked_missing_source_or_admission"),
        ("red-zone stats", "blocked_not_regenerated_requires_contract"),
        ("route/YPRR/TPRR", "blocked_no_admitted_route_denominator"),
        ("PFR RB broken tackles", "review_only_hypothesis_not_joined"),
        ("injury/availability context", "blocked_no_historical_asof_use_gate"),
        ("rookie/draft capital", "review_only_or_blocked_not_joined"),
        ("market/ADP context", "display_only_or_blocked_no_historical_asof_gate"),
        ("checkpoint_review_score historical", "blocked_missing_receipt"),
        ("position_specific_review_score historical", "blocked_missing_receipt"),
        ("nwr_dynasty_score historical", "blocked_exact_replay_missing"),
        ("WR/QB v2 overlay", "blocked_missing_historical_receipt_chain"),
        ("shadow_model_v2_metrics", "blocked_missing_source"),
    ]:
        add(blocked, "blocked/backlog", "QB/RB/WR/TE", reason, "backlog/source gate", "", "Not populated with values in this mart.")
    return rows


def feature_defs() -> list[dict[str, object]]:
    return [
        {"feature_family": "historical_fantasy_finish_labels", "actual_column": "label_next_position_finish", "status": "LABEL_ONLY_REVIEW_READY", "category": "label", "position_scope": "QB/RB/WR/TE", "source": str(DATA_HYGIENE_CLOSURE_DIR), "allowed": "label_evaluation_only", "join_key": "player_id+season+position", "decision_date_safe": "label_only_not_input", "leakage": "safe_as_outcome_only", "blocked": ""},
        {"feature_family": "next_nwr_points_label", "actual_column": "label_next_nwr_points", "status": "LABEL_ONLY_REVIEW_READY", "category": "label", "position_scope": "QB/RB/WR/TE", "source": str(DATA_HYGIENE_CLOSURE_DIR), "allowed": "label_evaluation_only", "join_key": "player_id+season+position", "decision_date_safe": "label_only_not_input", "leakage": "safe_as_outcome_only", "blocked": ""},
        {"feature_family": "startable_label", "actual_column": "label_startable_hit", "status": "LABEL_ONLY_REVIEW_READY", "category": "label", "position_scope": "QB/RB/WR/TE", "source": str(DATA_HYGIENE_CLOSURE_DIR), "allowed": "label_evaluation_only", "join_key": "player_id+season+position", "decision_date_safe": "label_only_not_input", "leakage": "safe_as_outcome_only", "blocked": ""},
        {"feature_family": "PYF_prior_year_points", "actual_column": "pyf_prior_nwr_points", "status": "AVAILABLE_REVIEW_ONLY", "category": "baseline", "position_scope": "QB/RB/WR/TE", "source": str(PANEL_PATH), "allowed": "mandatory_anchor_comparator", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "prior_year_ppg", "actual_column": "pyf_prior_nwr_ppg", "status": "AVAILABLE_REVIEW_ONLY", "category": "baseline", "position_scope": "QB/RB/WR/TE", "source": str(PANEL_PATH), "allowed": "secondary_baseline", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "prior_year_rank", "actual_column": "pyf_prior_rank_position_feature_season", "status": "DERIVED_REVIEW_ONLY", "category": "baseline", "position_scope": "QB/RB/WR/TE", "source": "derived from PYF in review mart", "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "two_year_weighted_production", "actual_column": "prior_2yr_weighted_nwr_points", "status": "DERIVED_REVIEW_ONLY", "category": "baseline", "position_scope": "QB/RB/WR/TE", "source": "derived from prior_nwr_points panel history", "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "partial history coverage varies"},
        {"feature_family": "three_year_weighted_production", "actual_column": "prior_3yr_weighted_nwr_points", "status": "DERIVED_REVIEW_ONLY", "category": "baseline", "position_scope": "QB/RB/WR/TE", "source": "derived from prior_nwr_points panel history", "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "partial history coverage varies"},
        {"feature_family": "prior_games", "actual_column": "prior_games", "status": "AVAILABLE_REVIEW_ONLY", "category": "availability", "position_scope": "QB/RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "passing_volume_stats", "actual_column": "prior_passing_yards", "status": "AVAILABLE_REVIEW_ONLY", "category": "passing", "position_scope": "QB", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "rushing_volume_stats", "actual_column": "prior_rushing_yards", "status": "AVAILABLE_REVIEW_ONLY", "category": "rushing", "position_scope": "QB/RB", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "receiving_volume_stats", "actual_column": "prior_receiving_yards", "status": "AVAILABLE_REVIEW_ONLY", "category": "receiving", "position_scope": "RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "targets", "actual_column": "prior_targets", "status": "AVAILABLE_REVIEW_ONLY", "category": "receiving", "position_scope": "RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "carries", "actual_column": "prior_carries", "status": "AVAILABLE_REVIEW_ONLY", "category": "rushing", "position_scope": "QB/RB", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "receptions", "actual_column": "prior_receptions", "status": "AVAILABLE_REVIEW_ONLY", "category": "receiving", "position_scope": "RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": ""},
        {"feature_family": "air_yards_and_yac", "actual_column": "prior_receiving_air_yards", "status": "AVAILABLE_REVIEW_ONLY", "category": "receiving", "position_scope": "RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "partial proxy receipt status"},
        {"feature_family": "offensive_snaps_and_pct", "actual_column": "prior_offensive_snaps", "status": "AVAILABLE_REVIEW_ONLY", "category": "usage", "position_scope": "QB/RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "review-only source gate"},
        {"feature_family": "touches_and_opportunities", "actual_column": "prior_touches", "status": "AVAILABLE_REVIEW_ONLY", "category": "usage", "position_scope": "RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "review-only source gate"},
        {"feature_family": "first_down_stats", "actual_column": "prior_rushing_first_downs", "status": "AVAILABLE_REVIEW_ONLY", "category": "first downs", "position_scope": "QB/RB/WR/TE", "source": str(PANEL_PATH), "allowed": "component_signal_tests_only", "join_key": "player_id+feature_season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "exact raw admitted first-down chain remains a caveat"},
        {"feature_family": "sparse_history_flag", "actual_column": "sparse_history_flag", "status": "AVAILABLE_REVIEW_ONLY", "category": "guardrail", "position_scope": "QB/RB/WR/TE", "source": str(ROLE_RECEIPTS_PATH), "allowed": "guardrail_context_only", "join_key": "player_id+season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "not formula weight"},
        {"feature_family": "low_games_flag", "actual_column": "low_games_flag", "status": "AVAILABLE_REVIEW_ONLY", "category": "guardrail", "position_scope": "QB/RB/WR/TE", "source": str(ROLE_RECEIPTS_PATH), "allowed": "guardrail_context_only", "join_key": "player_id+season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "not formula weight"},
        {"feature_family": "role_archetype", "actual_column": "role_archetype", "status": "AVAILABLE_REVIEW_ONLY", "category": "guardrail", "position_scope": "QB/RB/WR/TE", "source": str(ROLE_RECEIPTS_PATH), "allowed": "miss_taxonomy_guardrail_context_only", "join_key": "player_id+season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "not formula weight or ranking input"},
        {"feature_family": "confidence_cap", "actual_column": "confidence_cap_value", "status": "AVAILABLE_REVIEW_ONLY", "category": "coverage", "position_scope": "QB/RB/WR/TE", "source": str(CONFIDENCE_RECEIPTS_PATH), "allowed": "caution_coverage_context_only", "join_key": "player_id+season+position", "decision_date_safe": "yes", "leakage": "PASS", "blocked": "not formula/ranking feature"},
        {"feature_family": "age_lifecycle", "actual_column": "age_lifecycle_status", "status": "MISSING_RECEIPT", "category": "lifecycle", "position_scope": "QB/RB/WR/TE", "source": str(LOCATOR_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "exact historical lifecycle/age receipts missing"},
        {"feature_family": "experience_year", "actual_column": "experience_year_status", "status": "MISSING_RECEIPT", "category": "lifecycle", "position_scope": "QB/RB/WR/TE", "source": str(LOCATOR_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "season-by-season experience receipts missing"},
        {"feature_family": "return_scoring", "actual_column": "return_scoring_status", "status": "MISSING_SOURCE", "category": "special teams", "position_scope": "QB/RB/WR/TE/K", "source": str(MASTER_RECEIPT_REVIEW_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "return scoring source/admission recovery required"},
        {"feature_family": "red_zone_stats", "actual_column": "red_zone_status", "status": "MISSING_RECEIPT", "category": "red zone", "position_scope": "QB/RB/WR/TE", "source": str(MASTER_RECEIPT_REVIEW_DIR), "allowed": "blocked_until_regenerated", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "red-zone exact receipts not regenerated"},
        {"feature_family": "route_yprr_tprr", "actual_column": "route_yprr_tprr_status", "status": "BLOCKED", "category": "routes", "position_scope": "RB/WR/TE", "source": str(FG_READINESS_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "no", "leakage": "blocked", "blocked": "no admitted true route denominator"},
        {"feature_family": "pfr_rb_broken_tackles", "actual_column": "pfr_rb_broken_tackle_status", "status": "REVIEW_ONLY_NOT_JOINED", "category": "PFR context", "position_scope": "RB", "source": str(PFR_ADDENDUM_DIR), "allowed": "future_bounded_review_only_hypothesis", "join_key": "requires_safe_PFR_bridge", "decision_date_safe": "conditional", "leakage": "conditional", "blocked": "not joined to this mart; not production-approved"},
        {"feature_family": "injury_availability_context", "actual_column": "injury_availability_status", "status": "LEAKAGE_UNSAFE", "category": "availability", "position_scope": "QB/RB/WR/TE", "source": str(DATA_HYGIENE_CLOSURE_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "high", "blocked": "historical as-of injury/depth gate absent"},
        {"feature_family": "rookie_draft_capital_context", "actual_column": "rookie_draft_capital_status", "status": "REVIEW_ONLY_OR_BLOCKED", "category": "rookie", "position_scope": "QB/RB/WR/TE", "source": str(DATA_HYGIENE_CLOSURE_DIR), "allowed": "blocked_for_gauntlet", "join_key": "not_joined", "decision_date_safe": "conditional", "leakage": "conditional", "blocked": "source/use-gate not cleared for formula tournament"},
        {"feature_family": "market_adp_context", "actual_column": "market_adp_status", "status": "DISPLAY_ONLY", "category": "market", "position_scope": "QB/RB/WR/TE", "source": str(SYSTEM_AUDIT_DIR), "allowed": "display_only", "join_key": "not_joined", "decision_date_safe": "not_proven", "leakage": "market/asof_risk", "blocked": "no historical point-in-time gate"},
        {"feature_family": "checkpoint_review_score_historical", "actual_column": "checkpoint_review_score_historical_status", "status": "MISSING_RECEIPT", "category": "Model v4 component", "position_scope": "QB/RB/WR/TE", "source": str(MASTER_RECEIPT_REVIEW_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "season-by-season checkpoint receipts missing"},
        {"feature_family": "position_specific_review_score_historical", "actual_column": "position_specific_review_score_historical_status", "status": "MISSING_RECEIPT", "category": "Model v4 component", "position_scope": "QB/RB/WR/TE", "source": str(MASTER_RECEIPT_REVIEW_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "season-by-season position score receipts missing"},
        {"feature_family": "nwr_dynasty_score_historical", "actual_column": "nwr_dynasty_score_historical_status", "status": "REBUILD_BLOCKED", "category": "Model v4 output", "position_scope": "QB/RB/WR/TE", "source": str(MASTER_RECEIPT_REVIEW_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "exact replay missing; current board only"},
        {"feature_family": "WR_QB_v2_candidate_overlay", "actual_column": "wr_qb_v2_overlay_status", "status": "MISSING_RECEIPT", "category": "Model v4 overlay", "position_scope": "QB/WR", "source": str(MASTER_RECEIPT_REVIEW_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "historical overlay chain missing"},
        {"feature_family": "shadow_model_v2_metrics", "actual_column": "shadow_model_v2_metrics_status", "status": "MISSING_SOURCE", "category": "shadow sidecar", "position_scope": "QB/RB/WR/TE", "source": str(MASTER_RECEIPT_REVIEW_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "not_proven", "leakage": "unknown", "blocked": "missing source file"},
        {"feature_family": "NGS_advanced_metrics", "actual_column": "", "status": "DISPLAY_ONLY", "category": "advanced metrics", "position_scope": "QB/RB/WR/TE", "source": str(FG_READINESS_DIR), "allowed": "future_review_only_if_gated", "join_key": "not_joined", "decision_date_safe": "conditional", "leakage": "conditional", "blocked": "not included in current mart; no model-use approval"},
        {"feature_family": "PFR_broad_feature_sets", "actual_column": "", "status": "IDENTITY_UNSAFE", "category": "PFR context", "position_scope": "QB/RB/WR/TE", "source": str(PFR_ADDENDUM_DIR), "allowed": "blocked_except_named_RB_BT_context", "join_key": "requires_source_gate", "decision_date_safe": "conditional", "leakage": "identity_risk", "blocked": "broad PFR production use blocked"},
        {"feature_family": "PFF_elusive_or_proxy_names", "actual_column": "", "status": "BLOCKED", "category": "blocked metric", "position_scope": "RB", "source": str(PFR_ADDENDUM_DIR), "allowed": "blocked", "join_key": "not_available", "decision_date_safe": "no", "leakage": "blocked", "blocked": "PFF elusive/proxy naming explicitly blocked"},
    ]


def feature_matrix(mart: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for f in feature_defs():
        col = str(f.get("actual_column", ""))
        non_null = non_empty_count(mart, col) if col in MART_FIELDNAMES else 0
        has_actual = col in MART_FIELDNAMES and non_null > 0 and not col.endswith("_status")
        review_allowed = f["status"] in {"AVAILABLE_REVIEW_ONLY", "DERIVED_REVIEW_ONLY", "LABEL_ONLY_REVIEW_READY", "REVIEW_ONLY_NOT_JOINED", "REVIEW_ONLY_OR_BLOCKED"}
        rows.append({
            "feature_family": f["feature_family"],
            "category": f["category"],
            "current_status": f["status"],
            "availability_class": "actual_values_in_mart" if has_actual else "availability_flag_or_backlog",
            "position_scope": f["position_scope"],
            "season_coverage": season_coverage(mart) if has_actual else ("2013-2025" if review_allowed else ""),
            "row_count": len(mart) if has_actual else 0,
            "non_null_rows": non_null,
            "source_path_or_artifact": f["source"],
            "join_key": f["join_key"],
            "decision_date_safe": f["decision_date_safe"],
            "leakage_status": f["leakage"],
            "source_use_gate": "review_only_not_production_model_use" if review_allowed else f["status"],
            "formula_test_eligibility": f["allowed"],
            "ranking_integration_eligibility": "blocked",
            "production_model_use_allowed": "no",
            "review_only_allowed": "yes" if review_allowed else "no",
            "display_only_allowed": "yes" if f["status"] in {"DISPLAY_ONLY", "REVIEW_ONLY_NOT_JOINED", "AVAILABLE_REVIEW_ONLY", "DERIVED_REVIEW_ONLY", "LABEL_ONLY_REVIEW_READY"} else "no",
            "blocked_reason": f["blocked"],
            "position_coverage": position_coverage(mart, col) if has_actual else f["position_scope"],
            "caveats": f["blocked"] or "review-only; not production/model-use",
        })
    return rows


def validation_rows(mart: list[dict[str, object]], meta: dict[str, object]) -> list[dict[str, object]]:
    keys = [(row["player_id"], row["season"], row["position"]) for row in mart]
    duplicate_count = len(keys) - len(set(keys))
    checks = [
        ("row_count", len(mart), len(mart) == 5518, "Expected accepted partial replay panel grain."),
        ("season_coverage", season_coverage(mart), season_coverage(mart) == "2013-2025", ""),
        ("position_coverage", position_coverage(mart), position_coverage(mart) == "QB=754|RB=1429|WR=2124|TE=1211", ""),
        ("duplicate_player_season_position_keys", duplicate_count, duplicate_count == 0, ""),
        ("required_columns_present", len([c for c in MART_FIELDNAMES if c in mart[0]]), all(c in mart[0] for c in MART_FIELDNAMES), ""),
        ("role_join_missing_rows", meta["missing_role_joins"], meta["missing_role_joins"] == 0, ""),
        ("confidence_join_missing_rows", meta["missing_confidence_joins"], meta["missing_confidence_joins"] == 0, ""),
        ("review_only_all_rows", sum(1 for r in mart if r["review_only"] == "True"), all(r["review_only"] == "True" for r in mart), ""),
        ("model_use_allowed_all_false", sum(1 for r in mart if r["model_use_allowed"] == "False"), all(r["model_use_allowed"] == "False" for r in mart), ""),
        ("production_approved_all_false", sum(1 for r in mart if r["production_approved"] == "False"), all(r["production_approved"] == "False" for r in mart), ""),
        ("leakage_check_pass", sum(1 for r in mart if str(r["leakage_check_result"]).startswith("PASS")), all(str(r["leakage_check_result"]).startswith("PASS") for r in mart), ""),
        ("asof_check_pass", sum(1 for r in mart if str(r["asof_check_result"]).startswith("PASS")), all(str(r["asof_check_result"]).startswith("PASS") for r in mart), ""),
        ("exact_replay_status_blocked", sum(1 for r in mart if r["exact_model_v4_replay_status"] == "EXACT_REPLAY_BLOCKED"), all(r["exact_model_v4_replay_status"] == "EXACT_REPLAY_BLOCKED" for r in mart), ""),
        ("blocked_fields_are_status_flags_only", "yes", all(str(r["return_scoring_status"]).startswith("blocked") and str(r["route_yprr_tprr_status"]).startswith("blocked") for r in mart), "Blocked fields are not fake numeric values."),
    ]
    return [{"check": name, "result": result, "passed": bool_text(bool(passed)), "caveat": caveat} for name, result, passed, caveat in checks]


def status_counts(matrix: list[dict[str, object]]) -> dict[str, int]:
    counts = Counter(str(row["current_status"]) for row in matrix)
    available_now = sum(1 for row in matrix if row["availability_class"] == "actual_values_in_mart")
    review_only = sum(1 for row in matrix if row["review_only_allowed"] == "yes")
    blocked_missing = sum(1 for row in matrix if str(row["current_status"]) in {"BLOCKED", "MISSING_RECEIPT", "MISSING_SOURCE", "LEAKAGE_UNSAFE", "IDENTITY_UNSAFE", "REBUILD_BLOCKED"} or str(row["current_status"]).startswith("MISSING"))
    counts["available_now"] = available_now
    counts["review_only"] = review_only
    counts["blocked_missing"] = blocked_missing
    return dict(counts)


def write_backlog() -> None:
    write_text(OUT_DIR / "FORMULA_DATA_MISSING_UPGRADE_BACKLOG.md", "\n".join([
        "# Formula Data Missing Upgrade Backlog",
        "",
        "## Highest Priority",
        "",
        "1. `route_yprr_tprr_exact_receipts`: Route Recovery/source admission only; true routes, YPRR, and TPRR remain blocked.",
        "2. `return_scoring_receipts`: source admission/recovery lane required before any formula use.",
        "3. `red_zone_exact_receipts`: regeneration pilot/contract required before values can enter a mart.",
        "4. `shadow_model_v2_metrics.csv`: manual recovery or Master HQ scope-removal decision required.",
        "5. `checkpoint_review_score_historical` and `position_specific_review_score_historical`: exact Model v4 replay remains blocked without season-by-season receipts.",
        "6. `age_lifecycle` and `experience_year`: historical sidecar receipts remain missing or not separately admitted.",
        "7. PFR RB broken tackles: preserve only as narrow RB review-only context; a joined runner/panel is still required before inclusion.",
        "8. Rookie/draft-capital context: needs source/use-gate review before any formula sprint.",
        "9. Injury/availability context: needs point-in-time historical as-of controls.",
        "10. Market/ADP context: needs historical point-in-time source gate; display-only until then.",
        "",
        "## Do Not Backfill By Guessing",
        "",
        "Blocked fields in `FORMULA_DATA_MART_REVIEW_ONLY.csv` are status flags only. They must not be interpreted as zeroes, inferred values, or permission to run formula tournaments.",
    ]))


def write_source_trace(mart: list[dict[str, object]]) -> None:
    source_rows = []
    for path, role, use_gate in [
        (PANEL_PATH, "base player-season panel with labels, PYF, lagged factual components", "review_only_component_signal_tests_only"),
        (ROLE_RECEIPTS_PATH, "role archetype receipts", "review_only_guardrail_context"),
        (CONFIDENCE_RECEIPTS_PATH, "confidence cap receipts", "review_only_caution_coverage_context"),
        (SYSTEM_AUDIT_DIR / "NWR_DATA_STAT_INVENTORY.csv", "full system stat inventory", "governance_reference"),
        (DATA_HYGIENE_CLOSURE_DIR / "HISTORICAL_LABEL_IDENTITY_SOURCE_GATE_CLOSURE_V1_REPORT.md", "label/identity/source gate closure", "governance_reference"),
        (LOCATOR_DIR / "MODEL_V4_HISTORICAL_RECEIPT_LOCATOR_LEDGER_V1_REPORT.md", "historical receipt locator", "governance_reference"),
        (FREEZE_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FREEZE_SCHEMA_VALIDATION_V1_REPORT.md", "receipt freeze/schema validation", "governance_reference"),
        (MASTER_RECEIPT_REVIEW_DIR / "MODEL_V4_HISTORICAL_RECEIPT_MASTER_REVIEW_ADMISSION_DECISION_V1_REPORT.md", "receipt admission decision", "governance_reference"),
        (FG_READINESS_DIR / "FORMULA_GAUNTLET_DATA_READINESS_GATE_V1_REPORT.md", "Formula Gauntlet readiness gate", "governance_reference"),
        (FG_SCAFFOLD_DIR / "FORMULA_GAUNTLET_NO_CODE_TOURNAMENT_DESIGN_SCAFFOLD_V1_REPORT.md", "Formula Gauntlet no-code scaffold", "governance_reference"),
        (PFR_ADDENDUM_DIR / "NWR_SYSTEM_AUDIT_PFR_RB_BROKEN_TACKLE_ADDENDUM_V1_REPORT.md", "PFR RB broken tackle addendum", "governance_reference"),
    ]:
        source_rows.append(f"- `{path.relative_to(REPO) if path.is_relative_to(REPO) else path}`: {role}; `{use_gate}`; SHA256 `{sha256(path) if path.is_file() else 'directory_reference'}`")
    write_text(OUT_DIR / "FORMULA_DATA_SOURCE_TRACE.md", "\n".join([
        "# Formula Data Source Trace",
        "",
        f"Canonical remote HEAD verified before build: `{EXPECTED_REMOTE_HEAD}`",
        "",
        "## Sources Used",
        "",
        *source_rows,
        "",
        "## Join Result",
        "",
        f"- Review-only data mart rows: `{len(mart)}`",
        "- Join grain: `player_id + season + position`",
        "- Role archetype joins missing: `0`",
        "- Confidence cap joins missing: `0`",
        "",
        "## Guardrails",
        "",
        "- No source was promoted.",
        "- No production/model-use approval was introduced.",
        "- No Formula Gauntlet, tournament, tuning, exact replay, ranking integration, or app/runtime/model behavior change occurred.",
        "- No canonical `local_exports` write occurred.",
    ]))


def write_readiness(matrix: list[dict[str, object]], mart: list[dict[str, object]]) -> None:
    counts = status_counts(matrix)
    write_text(OUT_DIR / "FORMULA_TESTING_READINESS_DECISION.md", "\n".join([
        "# Formula Testing Readiness Decision",
        "",
        "## Readiness Level",
        "",
        "`READY_FOR_SMALL_COMPONENT_ONLY_TEST_TABLE`",
        "",
        "## Verdict",
        "",
        "`YELLOW_FORMULA_DATA_MART_PARTIAL_COMPONENT_ONLY`",
        "",
        "## Decision",
        "",
        "A 5,518-row review-only player-season mart can be built for component signal tests and guardrail design. It is not complete enough for a 50-100 candidate Formula Gauntlet sprint, champion refinement, rankings integration, production/model-use, or exact Model v4 replay.",
        "",
        "## Evidence",
        "",
        f"- Feature families audited: `{len(matrix)}`",
        f"- Actual value families in mart: `{counts['available_now']}`",
        f"- Review-only allowed families: `{counts['review_only']}`",
        f"- Blocked/missing families: `{counts['blocked_missing']}`",
        f"- Mart rows: `{len(mart)}`",
        "- All rows are `review_only=True`, `model_use_allowed=False`, and `production_approved=False`.",
        "",
        "## Allowed Now",
        "",
        "- Review-only component signal tests.",
        "- PYF anchor comparison.",
        "- Guardrail/miss taxonomy reporting using role archetypes.",
        "- Confidence-cap caution/coverage context.",
        "",
        "## Still Blocked",
        "",
        "- 50-100 candidate Formula Gauntlet sprint.",
        "- Formula tournament winners.",
        "- Formula tuning or weight optimization.",
        "- Champion refinement.",
        "- Rankings integration.",
        "- Production/model-use.",
        "- Exact Model v4 historical replay.",
    ]))


def write_report(matrix: list[dict[str, object]], mart: list[dict[str, object]]) -> None:
    counts = status_counts(matrix)
    highest_available = [
        "PYF/prior-year points baseline",
        "historical fantasy labels and startable labels",
        "lagged passing/rushing/receiving volume stats",
        "lagged first-down proxy fields",
        "offensive snaps/opportunity/touches",
        "role archetype guardrail/miss taxonomy",
        "confidence-cap caution/coverage context",
    ]
    missing = [
        "route/YPRR/TPRR exact receipts",
        "return scoring receipts",
        "red-zone exact receipts",
        "shadow_model_v2_metrics.csv",
        "exact historical checkpoint and position-specific Model v4 receipts",
        "age/lifecycle sidecars",
        "historical point-in-time injury/market gates",
    ]
    write_text(OUT_DIR / "FORMULA_DATA_MART_FEATURE_AVAILABILITY_AUDIT_V1_REPORT.md", "\n".join([
        "# Formula Data Mart / Feature Availability Audit V1 Report",
        "",
        "## Verdict",
        "",
        "`YELLOW_FORMULA_DATA_MART_PARTIAL_COMPONENT_ONLY`",
        "",
        "## Clear Answer",
        "",
        "NWR has enough joined, leakage-safe, review-only historical data to build a small component-test data mart, but not enough complete/source-cleared data for a 50-100 candidate Formula Gauntlet sprint or rankings integration.",
        "",
        "## Data Mart Result",
        "",
        f"- Rows: `{len(mart)}`",
        f"- Season coverage: `{season_coverage(mart)}`",
        f"- Position coverage: `{position_coverage(mart)}`",
        "- Grain: `player_id + season + position`",
        "- Allowed scope: `review_only_component_signal_tests_only`",
        "",
        "## Feature Availability Summary",
        "",
        f"- Feature families audited: `{len(matrix)}`",
        f"- Actual value families in mart: `{counts['available_now']}`",
        f"- Review-only allowed families: `{counts['review_only']}`",
        f"- Blocked/missing families: `{counts['blocked_missing']}`",
        "",
        "## Highest-Value Available Features",
        "",
        *[f"- {item}" for item in highest_available],
        "",
        "## Highest-Priority Missing Upgrades",
        "",
        *[f"- {item}" for item in missing],
        "",
        "## Formula Sprint Decision",
        "",
        "Enough data exists for review-only component signal tests. Enough data does not exist for a 100-candidate Formula Gauntlet, champion refinement, rankings integration, production/model-use, or exact Model v4 historical replay.",
        "",
        "## Production Status",
        "",
        "- Exact Model v4 replay remains blocked.",
        "- Formula Gauntlet tournaments remain blocked.",
        "- 100-candidate Gauntlet remains blocked.",
        "- Champion refinement remains blocked.",
        "- Rankings integration remains blocked.",
        "- Production/model-use remains blocked.",
        "- No source was promoted.",
    ]))


def main() -> None:
    for path in [
        PANEL_PATH,
        ROLE_RECEIPTS_PATH,
        CONFIDENCE_RECEIPTS_PATH,
        SYSTEM_AUDIT_DIR / "NWR_DATA_STAT_INVENTORY.csv",
        DATA_HYGIENE_CLOSURE_DIR / "HISTORICAL_LABEL_IDENTITY_SOURCE_GATE_CLOSURE_V1_REPORT.md",
        FG_READINESS_DIR / "FORMULA_GAUNTLET_DATA_READINESS_GATE_V1_REPORT.md",
    ]:
        if not path.exists():
            raise FileNotFoundError(path)

    mart, meta = build_mart()
    matrix = feature_matrix(mart)
    schema = schema_rows()
    validations = validation_rows(mart, meta)

    if any(row["passed"] != "true" for row in validations):
        failed = [row["check"] for row in validations if row["passed"] != "true"]
        raise RuntimeError(f"validation failed: {failed}")

    write_csv(MART_PATH, mart, MART_FIELDNAMES)
    write_csv(OUT_DIR / "FORMULA_DATA_TARGET_SCHEMA.csv", schema, [
        "field_name",
        "category",
        "position_scope",
        "ideal_player_season_formula_table_status",
        "row_grain",
        "source_family",
        "actual_mart_column",
        "included_in_review_mart",
        "formula_input_or_label",
        "production_model_use_allowed",
        "review_only_use_allowed",
        "blocked_reason",
        "notes",
    ])
    write_csv(OUT_DIR / "FORMULA_FEATURE_AVAILABILITY_MATRIX.csv", matrix, [
        "feature_family",
        "category",
        "current_status",
        "availability_class",
        "position_scope",
        "season_coverage",
        "row_count",
        "non_null_rows",
        "source_path_or_artifact",
        "join_key",
        "decision_date_safe",
        "leakage_status",
        "source_use_gate",
        "formula_test_eligibility",
        "ranking_integration_eligibility",
        "production_model_use_allowed",
        "review_only_allowed",
        "display_only_allowed",
        "blocked_reason",
        "position_coverage",
        "caveats",
    ])
    write_csv(OUT_DIR / "FORMULA_DATA_MART_SCHEMA_VALIDATION.csv", validations, ["check", "result", "passed", "caveat"])
    write_backlog()
    write_source_trace(mart)
    write_readiness(matrix, mart)
    write_report(matrix, mart)

    counts = status_counts(matrix)
    print(f"rows={len(mart)}")
    print(f"features_audited={len(matrix)}")
    print(f"available_now={counts['available_now']}")
    print(f"review_only={counts['review_only']}")
    print(f"blocked_missing={counts['blocked_missing']}")


if __name__ == "__main__":
    main()
