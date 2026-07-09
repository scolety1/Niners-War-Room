from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pandas as pd


OUT = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
CANONICAL_REPO = Path(r"C:\NWR\Niners-War-Room")
PRIOR_PACKET = Path(
    r"C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708"
    r"\docs\hq\model\production_rankings_backtest_v1_20260708"
)
V3_DIR = (
    REPO
    / "docs/hq/experiments/historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
)
V3_PARQUET = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
CURRENT_BOARD = (
    CANONICAL_REPO
    / "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
)


POSITIONS = ("QB", "RB", "WR", "TE")
PARTIAL_COMPONENTS_BY_POSITION = {
    "QB": {
        "vorp_anchor",
        "review_scoring_points",
        "passing_volume_security",
        "passing_production",
    },
    "RB": {
        "vorp_anchor",
        "review_scoring_points",
        "role_volume",
        "first_down_high_value",
        "receiving_utility",
    },
    "WR": {
        "vorp_anchor",
        "review_scoring_points",
        "target_route_role",
        "first_down_yardage",
        "air_yard_role",
    },
    "TE": {
        "vorp_anchor",
        "review_scoring_points",
        "route_target_role",
        "first_down_yardage",
    },
}
EXACT_COMPONENTS_BY_POSITION = {
    "QB": {
        "vorp_anchor",
        "rushing_separation",
        "passing_volume_security",
        "passing_production",
        "regression_context",
        "discipline_multiplier",
        "lifecycle_modifier_review",
        "confidence_cap",
        "checkpoint_review_score",
        "wr_qb_v2_candidate_adjustment",
        "old_pocket_qb_horizon_cap",
    },
    "RB": {
        "vorp_anchor",
        "role_volume",
        "first_down_high_value",
        "receiving_utility",
        "efficiency_context",
        "lifecycle_modifier_review",
        "confidence_cap",
        "checkpoint_review_score",
    },
    "WR": {
        "vorp_anchor",
        "target_route_role",
        "first_down_yardage",
        "air_yard_role",
        "efficiency_context",
        "lifecycle_modifier_review",
        "confidence_cap",
        "checkpoint_review_score",
        "wr_qb_v2_candidate_adjustment",
    },
    "TE": {
        "vorp_anchor",
        "route_target_role",
        "first_down_yardage",
        "yprr_target_efficiency",
        "red_zone_secondary",
        "discipline_multiplier",
        "lifecycle_modifier_review",
        "confidence_cap",
        "checkpoint_review_score",
    },
}


def main() -> int:
    substrate = pd.read_parquet(V3_PARQUET)
    board_rows = read_csv_rows(CURRENT_BOARD) if CURRENT_BOARD.exists() else []
    component_map = build_component_map(board_rows)
    availability = build_availability_matrix(substrate)
    panel = build_partial_panel(substrate)

    write_csv(OUT / "MODEL_V4_FORMULA_COMPONENT_SOURCE_MAP.csv", component_map)
    write_csv(OUT / "MODEL_V4_HISTORICAL_REPLAY_AVAILABILITY_MATRIX.csv", availability)
    write_csv(OUT / "MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv", panel)
    write_replay_contract()
    write_replay_blockers()
    write_source_trace(board_rows, substrate)
    write_report(component_map, availability, board_rows, substrate)
    return 0


def build_component_map(board_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    current_board_allowed = sorted({row.get("allowed_use", "") for row in board_rows})
    allowed_summary = "|".join(value for value in current_board_allowed if value) or "missing_board"
    board_caveat = (
        "Canonical current board artifact is stamped "
        f"{allowed_summary}; it is a displayed review/candidate surface, not an approved "
        "historical replay formula."
    )
    rows: list[dict[str, object]] = []

    def add(
        component_name: str,
        position_scope: str,
        component_layer: str,
        production_input: str,
        source: str,
        data_source: str,
        gate_status: str,
        historical_availability: str,
        earliest: str,
        decision_safe: str,
        leakage_risk: str,
        identity_risk: str,
        replay_status: str,
        drop_proxy_block: str,
        caveat: str,
    ) -> None:
        rows.append(
            {
                "component_name": component_name,
                "position_scope": position_scope,
                "component_layer": component_layer,
                "production_input": production_input,
                "current_source_file_function": source,
                "data_source": data_source,
                "admission_status": gate_status,
                "historical_availability": historical_availability,
                "earliest_season_available": earliest,
                "available_at_decision_date": decision_safe,
                "leakage_risk": leakage_risk,
                "identity_join_risk": identity_risk,
                "can_replay_historically": replay_capability(replay_status),
                "replay_status": replay_status,
                "drop_proxy_block": drop_proxy_block,
                "caveat": caveat,
            }
        )

    add(
        "full_dynasty_board_display",
        "ALL",
        "ui_surface",
        "No",
        "app/pages/20_final_board_v1.py; src/services/draft_day_app_v1_service.py::load_dynasty_rankings",
        "full_player_board_value_review_rows.csv",
        "displayed_current_artifact; review/candidate allowed_use",
        "current artifact only; no season-by-season board snapshots",
        "2026 current only",
        "No for historical replay",
        "high if replayed historically",
        "medium; current names/teams are current-context artifacts",
        "EXACT_REPLAY_BLOCKED",
        "Block historical use; use only for current source trace.",
        board_caveat,
    )
    add(
        "nwr_dynasty_score",
        "ALL",
        "displayed_score_surface",
        "Yes_current_displayed_score",
        "src/services/full_player_board_value_service.py::_assign_private_ranks; src/services/model_v4_wr_qb_v2_candidate_service.py::_candidate_rows",
        "current full board CSV; upstream checkpoint file named by rows is absent locally",
        "candidate_review_only_not_active_rankings in current artifact",
        "not available historically as exact score; current-only final score present",
        "2026 current only",
        "No for historical replay",
        "high without component receipts",
        "medium; final CSV has player keys but no historical point-in-time identity table",
        "EXACT_REPLAY_BLOCKED",
        "Do not replay score directly; rebuild only after component receipts exist.",
        "The UI sorts by this field, but the current artifact is a review-only candidate surface.",
    )
    add(
        "nwr_rank",
        "ALL",
        "rank_assignment",
        "Yes_current_displayed_sort",
        "src/services/full_player_board_value_service.py::_assign_private_ranks",
        "derived from nwr_dynasty_score sort",
        "derived display rank",
        "only derivable after exact score exists historically",
        "depends on score",
        "No until score replay is safe",
        "inherits score leakage risk",
        "inherits score identity risk",
        "EXACT_REPLAY_BLOCKED",
        "Block exact rank replay until exact score replay exists.",
        "Rank is a consequence of score, not an independent model input.",
    )

    add_current_value_components(add)
    add_candidate_overlay_components(add)
    add_excluded_signal_rows(add)
    return rows


def add_current_value_components(add) -> None:
    add(
        "checkpoint_review_score",
        "QB/RB/WR/TE",
        "current_value_checkpoint",
        "Yes_base_score_input",
        "src/services/model_v4_current_value_checkpoint_service.py::_checkpoint_row",
        "current_player_value_full_board_review_rows.csv plus component rows",
        "review_only current value checkpoint",
        "not present as historical season-by-season checkpoint rows",
        "current only",
        "No",
        "high if current checkpoint replayed backward",
        "medium",
        "EXACT_REPLAY_BLOCKED",
        "Block exact replay; can only preserve name/status.",
        "The current board points to this upstream source, but the source file is not present in this checkout.",
    )
    add(
        "position_specific_review_score",
        "QB/RB/WR/TE",
        "current_value_checkpoint",
        "Yes_base_component",
        "src/services/model_v4_current_value_checkpoint_service.py::_checkpoint_row",
        "rb_wr_current_value_rows.csv; qb_te_current_value_rows.csv",
        "review_only current value component output",
        "not present historically; partial factual overlap only",
        "current only",
        "No",
        "high without historical component rows",
        "medium",
        "EXACT_REPLAY_BLOCKED",
        "Proxy only from lagged factual V3 fields, never exact.",
        "This is the base score before lifecycle and confidence cap.",
    )
    add(
        "discipline_multiplier",
        "QB/TE",
        "current_value_position_guard",
        "Yes_base_component",
        "src/services/model_v4_qb_te_current_value_service.py::_discipline_multiplier",
        "position component rows",
        "review_only formula component",
        "not stored historically with current formula receipts",
        "current only",
        "No",
        "medium; depends on current component distribution",
        "medium",
        "EXACT_REPLAY_BLOCKED",
        "Block exact replay until QB/TE components exist by historical decision date.",
        "Requires exact QB/TE component scores and 1QB guard context.",
    )
    add(
        "lifecycle_modifier_review",
        "QB/RB/WR/TE",
        "lifecycle_archetype",
        "Yes_base_component",
        "src/services/model_v4_lifecycle_archetype_service.py::_player_row",
        "lifecycle_archetype_rows.csv; age/source sidecars; stats_first evidence",
        "review_only lifecycle component",
        "not available in V3; age/role shape not safely reconstructed for all historical rows",
        "current only",
        "No",
        "high if current age/role state used historically",
        "medium-high for age/name/current-team joins",
        "EXACT_REPLAY_BLOCKED",
        "Block exact replay; future lane needs historical age and role-shape receipts.",
        "Current role/age shape is one of the biggest replay blockers.",
    )
    add(
        "confidence_cap",
        "QB/RB/WR/TE",
        "confidence_missingness",
        "Yes_base_component",
        "src/services/model_v4_confidence_missingness_service.py::_player_row",
        "source_coverage_matrix.csv and component warning flags",
        "review_only confidence cap",
        "not available historically with current source-coverage receipts",
        "current only",
        "No",
        "medium-high; missingness can encode current source state",
        "medium",
        "EXACT_REPLAY_BLOCKED",
        "Block exact replay; future lane needs historical source coverage/warning matrix.",
        "Missingness/caveat logic is part of score and cannot be guessed.",
    )
    add_vorp_components(add)
    add_rb_wr_components(add)
    add_qb_te_components(add)


def add_vorp_components(add) -> None:
    base = "src/services/model_v4_replacement_vorp_core_service.py"
    for name, caveat in (
        ("review_scoring_points", "Can be partially proxied from V3 prior_nwr_points, but not exact current receipt."),
        ("positive_vorp_points", "Requires position replacement baselines and exact review scoring rows."),
        ("imported_rushing_first_downs", "V3 has lagged rushing first downs, not admitted matched current first-down view receipts by season."),
        ("imported_receiving_first_downs", "V3 has lagged receiving first downs, not admitted matched current first-down view receipts by season."),
        ("imported_first_down_points", "Can be partially computed from V3 rushing/receiving first downs, but exact current source status is absent."),
        ("return_scoring_points", "Return scoring evidence is not in V3 partial replay panel."),
    ):
        partial = name in {
            "review_scoring_points",
            "imported_rushing_first_downs",
            "imported_receiving_first_downs",
            "imported_first_down_points",
        }
        add(
            name,
            "QB/RB/WR/TE",
            "replacement_vorp_core",
            "Yes_base_component",
            f"{base}::_score_player/_component_rows",
            "NFL evidence matrix; admitted first-down views; admitted return view",
            "formula contract admits current matched views only",
            "partial V3 overlap" if partial else "not in V3 substrate",
            "2012 feature season for V3 overlap" if partial else "not established",
            "Yes for V3 lagged proxy only" if partial else "No",
            "low for V3 lagged proxy; high for direct current replay",
            "low for V3 GSIS rows; medium for current receipts",
            "PARTIAL_REPLAY_AVAILABLE" if partial else "EXACT_REPLAY_BLOCKED",
            "Use only as partial proxy source; exact receipt blocked.",
            caveat,
        )


def add_rb_wr_components(add) -> None:
    source = "src/services/model_v4_rb_wr_current_value_service.py"
    rb = {
        "vorp_anchor": "positive_vorp_points|review_scoring_points",
        "role_volume": "target_carry_volume|target_share_team_share|rushing_att|receiving_tar",
        "first_down_high_value": "imported_first_down_points|red_zone_involvement",
        "receiving_utility": "receiving_tar|routes_run_tprr|routes_run_yprr|receiving_yds",
        "efficiency_context": "yards_after_catch_contact|broken_tackle_context|explosive_play_profile",
    }
    wr = {
        "vorp_anchor": "positive_vorp_points|review_scoring_points",
        "target_route_role": "target_carry_volume|target_share_team_share|routes_run_tprr|routes_run_yprr|snap_count_off_2",
        "first_down_yardage": "imported_first_down_points|production_trend|receiving_yds_g",
        "air_yard_role": "air_yard_role|team_ay|air_yards_ay_depth_of_target_adot",
        "efficiency_context": "yards_after_catch_contact|drop_catchable_context",
    }
    for position, components in (("RB", rb), ("WR", wr)):
        for name, fields in components.items():
            partial = name in {
                "vorp_anchor",
                "role_volume",
                "first_down_high_value",
                "receiving_utility",
                "target_route_role",
                "first_down_yardage",
                "air_yard_role",
            }
            blocked_reason = (
                "exact stats_first/route/red-zone component receipts unavailable"
                if name != "vorp_anchor"
                else "exact VORP receipt unavailable"
            )
            add(
                name,
                position,
                "rb_wr_current_value",
                "Yes_base_component",
                f"{source}::{position.lower()}_components",
                fields,
                "review_only formula component; explicit field-path guarded",
                "partial V3 lagged factual overlap" if partial else "not in V3 substrate",
                "2012 feature season for overlap" if partial else "not established",
                "Yes for proxy overlap only" if partial else "No",
                "medium; route/current role metrics are leakage-prone without as-of receipts",
                "low for V3 GSIS rows; medium for current component rows",
                "PARTIAL_REPLAY_AVAILABLE" if partial else "EXACT_REPLAY_BLOCKED",
                f"Exact replay blocked: {blocked_reason}.",
                "V3 overlap preserves component name but not exact current normalized score/weight receipt.",
            )


def add_qb_te_components(add) -> None:
    source = "src/services/model_v4_qb_te_current_value_service.py"
    qb = {
        "vorp_anchor": "positive_vorp_points|review_scoring_points",
        "rushing_separation": "rushing_yds|rushing_td|rushing_first_downs",
        "passing_volume_security": "passing_attempts|passing_completions|passing_yards",
        "passing_production": "passing_td|passing_first_downs|interceptions",
        "regression_context": "stats_first_component_evidence",
    }
    te = {
        "vorp_anchor": "positive_vorp_points|review_scoring_points",
        "route_target_role": "route_data_route|route_data_targets|team_tar|routes_run_tprr",
        "first_down_yardage": "imported_first_down_points|receiving_yds",
        "yprr_target_efficiency": "routes_run_yprr|routes_run_tprr",
        "red_zone_secondary": "red_zone_targets_in20|red_zone_involvement",
    }
    for position, components in (("QB", qb), ("TE", te)):
        for name, fields in components.items():
            partial = name in {
                "vorp_anchor",
                "rushing_separation",
                "passing_volume_security",
                "passing_production",
                "route_target_role",
                "first_down_yardage",
            }
            add(
                name,
                position,
                "qb_te_current_value",
                "Yes_base_component",
                f"{source}::{position.lower()}_components",
                fields,
                "review_only formula component; explicit field-path guarded",
                "partial V3 lagged factual overlap" if partial else "not in V3 substrate",
                "2012 feature season for overlap" if partial else "not established",
                "Yes for proxy overlap only" if partial else "No",
                "medium-high for TE route/red-zone and QB regression context",
                "low for V3 GSIS rows; medium for current component rows",
                "PARTIAL_REPLAY_AVAILABLE" if partial else "EXACT_REPLAY_BLOCKED",
                "Exact normalized component replay blocked by missing current-named historical receipts.",
                "Partial overlap is not score-equivalent to Model v4.",
            )


def add_candidate_overlay_components(add) -> None:
    source = "src/services/model_v4_wr_qb_v2_candidate_service.py"
    for name, scope, caveat in (
        (
            "wr_qb_v2_candidate_adjustment",
            "WR/QB",
            "Current displayed board applies a WR/QB candidate overlay, but it is stamped not active rankings.",
        ),
        (
            "candidate_reason_codes",
            "WR/QB/RB/TE/K",
            "Reason-code audit field, not a standalone model input.",
        ),
        (
            "candidate_evidence_fields_used",
            "WR/QB/RB/TE/K",
            "Field-name audit context only; not numeric component receipts.",
        ),
        (
            "old_pocket_qb_horizon_cap",
            "QB",
            "Requires historical age, role_archetype, and current component receipts.",
        ),
    ):
        add(
            name,
            scope,
            "wr_qb_v2_candidate_overlay",
            "Yes_current_displayed_candidate_layer" if name != "candidate_reason_codes" else "No_diagnostic",
            f"{source}::_candidate_adjustment/_wr_adjustment/_qb_adjustment/_old_qb_horizon_overlay",
            "current board, current component rows, age sidecar, historical shadow metrics",
            "candidate_review_only_not_active_rankings",
            "not historically available with decision-date receipts",
            "current only",
            "No",
            "high if current candidate overlay used historically",
            "medium-high; depends on age/name/current role joins",
            "EXACT_REPLAY_BLOCKED",
            "Block exact replay until current candidate layer is either approved or explicitly excluded.",
            caveat,
        )


def add_excluded_signal_rows(add) -> None:
    excluded = [
        ("league_rank", "league roster/display context", "display-only; not formula"),
        ("market_rank", "market/ADP context", "display-only; blocked as private value input"),
        ("legacy_active_pack_score", "legacy active pack", "comparison-only; not primary score"),
        ("Outcome V2 probabilities", "Outcome V2 display artifacts", "display-only; not rankings/input"),
        ("current injury/depth/roster/status", "nflverse/rotowire/sleeper context", "current-only leakage unsafe historically"),
        ("NGS advanced metrics", "NGS display packet", "review-only display; not model input"),
        ("PFR advanced metrics", "advanced metrics bridge", "identity unsafe in current gate"),
        ("CFBD college metrics", "CFBD review artifacts", "review-only identity review required"),
    ]
    for name, source, caveat in excluded:
        add(
            name,
            "ALL",
            "excluded_signal",
            "No",
            "source gates and display packets",
            source,
            "blocked/display-only/review-only",
            "not eligible for exact replay",
            "varies",
            "No",
            "high unless separately as-of/source admitted",
            "varies",
            "EXCLUDED_FROM_REPLAY",
            "Exclude from production accuracy/replay substrate.",
            caveat,
        )


def build_availability_matrix(df: pd.DataFrame) -> list[dict[str, object]]:
    rows = []
    for (target_season, position), group in (
        df[df["position"].isin(POSITIONS)].groupby(["target_season", "position"], sort=True)
    ):
        position = str(position)
        total = int(len(group))
        label_count = int(group["next_position_finish"].notna().sum())
        identity_count = int(group["player_id_gsis"].astype(str).str.len().gt(0).sum())
        optional_null = int(group["optional_source_null_fenced"].fillna(False).astype(bool).sum())
        partial_components = PARTIAL_COMPONENTS_BY_POSITION[position]
        exact_components = EXACT_COMPONENTS_BY_POSITION[position]
        partial_coverage = len(partial_components) / len(exact_components)
        rows.append(
            {
                "target_season": int(target_season),
                "feature_season": int(target_season) - 1,
                "position": position,
                "exact_replay_rows_possible": 0,
                "partial_replay_rows_possible": total,
                "label_coverage": round(label_count / total, 4) if total else 0,
                "identity_coverage": round(identity_count / total, 4) if total else 0,
                "exact_input_coverage": 0.0,
                "partial_input_overlap_coverage": round(partial_coverage, 4),
                "exact_source_receipt_coverage": 0.0,
                "v3_review_source_coverage": 1.0,
                "decision_date_safe": "partial_v3_lagged_only",
                "valid_exact_replay_row_can_exist": "No",
                "valid_partial_replay_row_can_exist": "Yes",
                "missingness": f"optional_null_fenced_rows={optional_null}; exact_component_receipts_missing={total}",
                "main_blocker": main_blocker(position),
            }
        )
    return rows


def main_blocker(position: str) -> str:
    if position == "QB":
        return "missing current QB component receipts, age/role lifecycle receipts, and candidate old-pocket overlay history"
    if position == "RB":
        return "missing current RB component receipts for role/red-zone/efficiency plus lifecycle/confidence history"
    if position == "WR":
        return "missing current WR route/YPRR/air-yard/stats-first receipts plus candidate overlay history"
    if position == "TE":
        return "missing TE route/YPRR/red-zone receipts and TE discipline/lifecycle/confidence history"
    return "not modeled"


def build_partial_panel(df: pd.DataFrame) -> list[dict[str, object]]:
    keep_cols = [
        "substrate_row_id",
        "player_id_gsis",
        "feature_season",
        "target_season",
        "position",
        "feature_player_name",
        "target_player_name",
        "prior_nwr_points",
        "prior_games",
        "prior_nwr_ppg",
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
        "target_games",
        "next_nwr_points",
        "next_nwr_ppg",
        "next_position_finish",
        "startable_hit",
        "startable_bucket",
        "optional_source_null_fenced",
        "feature_asof_rule",
        "leakage_check_result",
        "asof_check_result",
    ]
    panel = df[df["position"].isin(POSITIONS)][keep_cols].copy()
    panel.insert(0, "review_only", True)
    panel.insert(1, "model_use_allowed", False)
    panel.insert(2, "training_allowed", False)
    panel.insert(3, "source_truth_allowed", False)
    panel.insert(4, "production_approved", False)
    panel["exact_model_v4_replay_status"] = "EXACT_REPLAY_BLOCKED"
    panel["partial_replay_status"] = "PARTIAL_V3_LAGGED_FACTUAL_OVERLAP_ONLY"
    panel["decision_date_rule"] = (
        "target_season_N uses completed feature_season_N_minus_1 only; no current/future fields"
    )
    panel["formula_component_names_preserved"] = (
        "vorp_anchor|review_scoring_points|imported_first_down_points|"
        "role_volume|target_route_role|first_down_yardage|passing_volume_security|"
        "route_target_role|lifecycle_modifier_review|confidence_cap|checkpoint_review_score"
    )
    panel["missing_component_receipt_flag"] = True
    panel["source_receipt_pointer"] = (
        "docs/hq/experiments/historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701/"
        "nwr_historical_tuning_feature_target_substrate_v3.parquet"
    )
    panel["caveat"] = (
        "Panel is review-only substrate overlap, not a score replay and not production accuracy."
    )
    return panel.fillna("").to_dict("records")


def write_replay_contract() -> None:
    (OUT / "MODEL_V4_REPLAY_CONTRACT.md").write_text(
        """# Model v4 Historical Replay Contract

## Status

`REVIEW_ONLY_CONTRACT_EXACT_REPLAY_BLOCKED_UNTIL_COMPONENT_RECEIPTS_EXIST`

## League Contract

- League: 10-team dynasty/keeper hybrid.
- Format: 1QB, non-PPR, first-down scoring.
- Starters: 1 QB, 2 RB, 3 WR, 1 TE, 2 FLEX, 1 K.
- FLEX eligibility: RB/WR/TE only.
- Kicker: de-emphasized and not meaningfully modeled by current Model v4 current-value chain.

## Decision Date

For target season `Y`, the replay decision date must be after the regular season `Y-1`
stats are complete and before target season `Y` current roster, injury, depth chart,
market, ADP, projection, or outcome information is used. The historical feature anchor
is therefore `feature_season = Y - 1`, and labels are `target_season = Y`.

## Valid Player Universe

Valid exact replay rows require all of the following:

- Position is QB/RB/WR/TE.
- Canonical identity is available at the historical decision date.
- Required Model v4 component inputs are present with source receipts.
- Required source receipts prove the evidence existed by the decision date.
- Target labels exist only as held-out evaluation labels, never as inputs.

The partial V3 panel is narrower: it only contains players with prior-season NFL
feature rows and next-season labels. It is not rookie-complete.

## Required Labels

- `next_nwr_points`
- `next_nwr_ppg`
- `next_position_finish`
- Position top-N labels: QB top 12, RB top 12/top 24, WR top 12/top 24/top 36, TE top 12.
- Startable label using NWR format cutoffs: QB10, RB30, WR40, TE12.

## Required Exact Inputs

Exact replay requires current Model v4 component names and receipts:

- Replacement/VORP: `review_scoring_points`, `positive_vorp_points`,
  `imported_first_down_points`, first-down source status, return scoring status.
- RB: `vorp_anchor`, `role_volume`, `first_down_high_value`,
  `receiving_utility`, `efficiency_context`.
- WR: `vorp_anchor`, `target_route_role`, `first_down_yardage`,
  `air_yard_role`, `efficiency_context`.
- QB: `vorp_anchor`, `rushing_separation`, `passing_volume_security`,
  `passing_production`, `regression_context`, discipline multiplier.
- TE: `vorp_anchor`, `route_target_role`, `first_down_yardage`,
  `yprr_target_efficiency`, `red_zone_secondary`, discipline multiplier.
- Checkpoint: `position_specific_review_score`, `lifecycle_modifier_review`,
  `confidence_cap`, `checkpoint_review_score`.
- Current displayed candidate layer, if it remains the board source:
  `wr_qb_v2_candidate_adjustment`, `candidate_reason_codes`,
  `old_pocket_qb_horizon_cap`, and their evidence receipts.

## Allowed Proxies

Allowed only for partial review lanes, never exact replay:

- V3 lagged factual fields such as prior NWR points, prior targets/carries,
  first downs, yards, passing stats, snap fields with null fences, and air-yard/YAC
  fields with null fences.
- Component names may be preserved as status columns, but proxy fields must not be
  relabeled as exact Model v4 component scores.

## Blocked Inputs

- Current ADP, market, projections, rankings, mock drafts, big boards, and consensus.
- Current roster/status/injury/depth-chart/schedule context.
- Target-season outcomes.
- Display-only Outcome V2 probabilities.
- NGS/PFR/CFBD/advanced metrics unless separately source-admitted and decision-date safe.
- Current-only age/role/lifecycle/confidence fields without historical receipts.

## Leakage Checks

- Every feature must have `feature_season = target_season - 1` or an earlier
  static-event timestamp.
- Every source must have an as-of receipt before the target-season decision anchor.
- Missing values must remain missing unless source semantics prove explicit zero.
- Identity joins must use approved IDs; name-only fallback is not allowed.

## Future Replay Metrics

The future replay lane should report MAE, RMSE, Spearman, Top-12/24/36 hit rates,
startable precision and recall, coverage by position and season, source/identity
coverage, baseline comparisons, and miss patterns by rookie/veteran, role change,
injury caveat, age band, and position.
""",
        encoding="utf-8",
    )


def write_replay_blockers() -> None:
    (OUT / "MODEL_V4_REPLAY_BLOCKERS.md").write_text(
        """# Model v4 Replay Blockers

## Verdict

`EXACT_MODEL_V4_REPLAY_BLOCKED`

## Ranked Blockers

1. The current board artifact is stamped `candidate_review_only_not_active_rankings`,
   so the displayed Full Dynasty board is not an approved production-accuracy target.
2. The canonical runtime folder contains the final board CSV but not the upstream
   current checkpoint/component receipt files required to replay `nwr_dynasty_score`.
3. Historical season-by-season Model v4 component rows do not exist for the current
   component names and source receipts.
4. Route/TPRR/YPRR/red-zone/stats-first component evidence is not historically
   available and admitted with decision-date receipts for all positions.
5. Lifecycle, role archetype, age, confidence cap, and warning flag layers are
   current-state dependent and are not historically reproducible from V3.
6. The WR/QB v2 candidate overlay depends on current component rows, current age
   sidecars, and historical shadow metrics; it is review-only and cannot be replayed
   as production.
7. Rookie/first-NFL-season players are structurally missing from the V3 prior-season
   veteran substrate.
8. Advanced metrics remain display-only, review-only, identity unsafe, or blocked
   under current gates and must not be used to fill formula gaps.

## Safe Partial Substrate

The generated partial panel preserves component names and uses only V3 lagged factual
overlap with source/governance caveats. It is not a score replay, not training data,
not source truth, and not production accuracy.
""",
        encoding="utf-8",
    )


def write_source_trace(board_rows: list[dict[str, str]], substrate: pd.DataFrame) -> None:
    traced_paths = [
        REPO / "app/pages/20_final_board_v1.py",
        REPO / "src/services/draft_day_app_v1_service.py",
        REPO / "src/services/full_player_board_value_service.py",
        REPO / "src/services/model_v4_wr_qb_v2_candidate_service.py",
        REPO / "src/services/model_v4_current_value_checkpoint_service.py",
        REPO / "src/services/model_v4_replacement_vorp_core_service.py",
        REPO / "src/services/model_v4_rb_wr_current_value_service.py",
        REPO / "src/services/model_v4_qb_te_current_value_service.py",
        REPO / "src/services/model_v4_lifecycle_archetype_service.py",
        REPO / "src/services/model_v4_confidence_missingness_service.py",
        REPO / "src/services/model_v4_formula_contract_service.py",
        REPO / "config/source_registry.csv",
        REPO / "config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json",
        V3_PARQUET,
        V3_DIR / "safe_feature_allowlist_v3.csv",
        V3_DIR / "historical_tuning_substrate_v3_summary.md",
        V3_DIR / "asof_and_leakage_guardrail_report_v3.md",
        V3_DIR / "identity_join_report_v3.csv",
        REPO / "docs/hq/experiments/historical_tuning_source_contract_v1_20260701/formula_tuning_not_ready_reason.md",
        REPO / "docs/hq/data_sources/sleeper_nflverse_usage_redzone_source_admission_v1_20260701/source_admission_summary.md",
        REPO / "docs/hq/data_sources/nflverse_lagged_usage_point_in_time_rules_v1_20260701/point_in_time_rules_summary.md",
        REPO / "docs/hq/data_sources/nflverse_point_in_time_snapshot_feasibility_v1_20260630/point_in_time_blocker_report.md",
        REPO / "docs/hq/data_sources/advanced_metrics_hardening_v2_backtest_20260707/ADVANCED_METRICS_V2_USE_GATE.md",
        REPO / "docs/hq/data_sources/advanced_metrics_hardening_v2_backtest_20260707/ADVANCED_METRICS_PFR_ESPN_BRIDGE_REVIEW.md",
        REPO / "docs/hq/data_sources/cfbd_review_artifacts_20260624/README.md",
        REPO / "docs/hq/outcomes/outcome_row_level_label_source_admission_v1_20260630/source_admission_summary.md",
        REPO / "docs/hq/outcomes/outcome_v2_horizon_20260630/08_OUTCOME_V2_CURRENT_FEATURE_SOURCE_APPROVAL_GATE.md",
        PRIOR_PACKET / "PRODUCTION_RANKINGS_BACKTEST_V1_REPORT.md",
        PRIOR_PACKET / "PRODUCTION_RANKINGS_BACKTEST_V1_SOURCE_TRACE.md",
        CURRENT_BOARD,
    ]
    lines = [
        "# Model v4 Replay Source Trace",
        "",
        "## Current Board Facts",
        "",
        f"- Current board path: `{CURRENT_BOARD}`",
        f"- Current board exists: `{CURRENT_BOARD.exists()}`",
        f"- Current board SHA-256: `{sha256(CURRENT_BOARD)}`",
        f"- Current board rows: `{len(board_rows)}`",
        f"- Current board allowed_use values: `{sorted({r.get('allowed_use', '') for r in board_rows})}`",
        f"- Current board candidate_mode values: `{sorted({r.get('candidate_mode', '') for r in board_rows})}`",
        f"- V3 substrate rows: `{len(substrate)}`",
        f"- V3 target seasons: `{int(substrate['target_season'].min())}-{int(substrate['target_season'].max())}`",
        "",
        "## Files",
        "",
        "| Path | Exists | SHA-256 | Role |",
        "| --- | --- | --- | --- |",
    ]
    for path in traced_paths:
        role = classify_role(path)
        lines.append(f"| {path} | {path.exists()} | {sha256(path)} | {role} |")
    (OUT / "MODEL_V4_REPLAY_SOURCE_TRACE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(
    component_map: list[dict[str, object]],
    availability: list[dict[str, object]],
    board_rows: list[dict[str, str]],
    substrate: pd.DataFrame,
) -> None:
    allowed = sorted({row.get("allowed_use", "") for row in board_rows})
    candidate_modes = sorted({row.get("candidate_mode", "") for row in board_rows})
    summary_rows = availability_summary_rows(availability)
    component_summary = component_map_summary(component_map)
    exact_ready = "No"
    partial_range = f"{int(substrate['target_season'].min())}-{int(substrate['target_season'].max())}"
    lines = [
        "# Historical Model v4 Replay Substrate V1 Report",
        "",
        "## Verdict",
        "",
        "`YELLOW_MODEL_V4_HISTORICAL_REPLAY_SUBSTRATE_PARTIAL_WITH_BLOCKERS`",
        "",
        "## Clear Answer",
        "",
        "Exact historical replay of the current production formula is not possible because the current displayed Full Dynasty board is a review-only WR/QB v2 candidate artifact, the upstream current checkpoint/component receipt files are absent locally, and no season-by-season historical Model v4 component receipt layer exists with decision-date source proofs.",
        "",
        "A partial replay substrate is possible for QB/RB/WR/TE target seasons "
        f"{partial_range} using V3 lagged factual overlap, but it is not an exact Model v4 score replay and cannot claim production accuracy.",
        "",
        "## Current Surface Facts",
        "",
        f"- Board rows inspected: `{len(board_rows)}`.",
        f"- Board allowed_use values: `{allowed}`.",
        f"- Board candidate_mode values: `{candidate_modes}`.",
        "- The displayed board sorts by `nwr_dynasty_score`, then `nwr_rank` is assigned from that score.",
        "- The current artifact points to `checkpoint_review_score` upstream, but the named upstream file is not present in the local canonical runtime folder.",
        "",
        "## Formula Component Map Summary",
        "",
        "| Component | Production Input? | Source | Gate Status | Historical Availability | Decision-Date Safe? | Replay Status | Caveat |",
        "| --------- | ----------------- | ------ | ----------- | ----------------------- | ------------------- | ------------- | ------ |",
    ]
    for row in component_summary:
        lines.append(
            "| {component_name} | {production_input} | {source} | {gate_status} | {historical} | {decision_safe} | {replay_status} | {caveat} |".format(
                component_name=row["component_name"],
                production_input=row["production_input"],
                source=row["source"],
                gate_status=row["gate_status"],
                historical=row["historical"],
                decision_safe=row["decision_safe"],
                replay_status=row["replay_status"],
                caveat=row["caveat"],
            )
        )
    lines.extend(
        [
            "",
            "## Historical Availability Summary",
            "",
            "| Season Range | Position | Replay Rows Possible | Label Coverage | Input Coverage | Identity Coverage | Main Blocker |",
            "| ------------ | -------- | -------------------: | -------------: | -------------: | ----------------: | ------------ |",
        ]
    )
    for row in summary_rows:
        lines.append(
            f"| {row['season_range']} | {row['position']} | {row['replay_rows_possible']} | "
            f"{row['label_coverage']} | {row['input_coverage']} | {row['identity_coverage']} | {row['main_blocker']} |"
        )
    lines.extend(
        [
            "",
            "## Replay Contract",
            "",
            "The next lane must run, if and only if exact component receipts are available, a target-season `Y` replay using only completed `Y-1` factual inputs and static events known before the `Y` decision anchor. The player universe is QB/RB/WR/TE with approved identity joins. Required labels are next-season NWR points, position finish, top-N hits, and startable labels under the 10-team 1QB non-PPR first-down league contract. Required inputs are the Model v4 component names and source receipts listed in `MODEL_V4_REPLAY_CONTRACT.md`.",
            "",
            "## Blocked / Excluded Signals",
            "",
            "- Display-only: market rank, league rank, DynastyProcess values/ECR, Outcome V2 probabilities, NGS display fields.",
            "- Review-only: V3 substrate, advanced-metrics shadow panels, CFBD review artifacts, current WR/QB v2 candidate overlay.",
            "- Blocked: ADP, projections, rankings, mocks, big boards, consensus, source row order, generic JSON slurping.",
            "- Not historically available: current component receipt rows, lifecycle/role archetype rows, confidence cap rows, route/YPRR/TPRR receipts.",
            "- Not decision-date safe: current roster/status/injury/depth/schedule context and current market context.",
            "- Identity unsafe: PFR advanced bridge and ESPN QBR under current advanced metrics gate; CFBD before identity review approval.",
            "",
            "## Biggest Replay Blockers",
            "",
            "1. Current board is review-only candidate, not a clean approved production formula target.",
            "2. Upstream current component/checkpoint receipt files are absent from the local canonical runtime folder.",
            "3. Historical Model v4 component receipts with current names do not exist.",
            "4. Route/YPRR/TPRR/red-zone/stats-first evidence is not historically admitted with as-of receipts.",
            "5. Lifecycle, age, role archetype, warning, and confidence layers are current-state dependent.",
            "6. Rookie and UDFA first-season rows are structurally outside the V3 prior-season veteran substrate.",
            "",
            "## Recommendation",
            "",
            "The next lane should be `Formula documentation/cleanup lane first`, followed by a bounded component-receipt backfill/source-admission lane. An actual Model v4 Historical Replay Benchmark should wait until the current board surface is clearly separated into approved production versus review-only candidate layers and historical component receipts exist.",
            "",
            "## Generated Artifacts",
            "",
            "- `MODEL_V4_FORMULA_COMPONENT_SOURCE_MAP.csv`",
            "- `MODEL_V4_HISTORICAL_REPLAY_AVAILABILITY_MATRIX.csv`",
            "- `MODEL_V4_REPLAY_CONTRACT.md`",
            "- `MODEL_V4_REPLAY_BLOCKERS.md`",
            "- `MODEL_V4_REPLAY_SOURCE_TRACE.md`",
            "- `MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`",
            "- `build_historical_model_v4_replay_substrate_v1.py`",
            "",
            "## Non-Goals Honored",
            "",
            "No formula weights were tuned, no rankings were changed, no source was promoted, no app behavior was changed, and no current/future-only fields were used as historical inputs.",
        ]
    )
    (OUT / "HISTORICAL_MODEL_V4_REPLAY_SUBSTRATE_V1_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def availability_summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    by_position: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_position.setdefault(str(row["position"]), []).append(row)
    for position in POSITIONS:
        group = by_position[position]
        season_range = f"{min(r['target_season'] for r in group)}-{max(r['target_season'] for r in group)}"
        partial_rows = sum(int(r["partial_replay_rows_possible"]) for r in group)
        exact_rows = sum(int(r["exact_replay_rows_possible"]) for r in group)
        label = sum(float(r["label_coverage"]) for r in group) / len(group)
        identity = sum(float(r["identity_coverage"]) for r in group) / len(group)
        partial_input = sum(float(r["partial_input_overlap_coverage"]) for r in group) / len(group)
        output.append(
            {
                "season_range": season_range,
                "position": position,
                "replay_rows_possible": f"{exact_rows} exact / {partial_rows} partial",
                "label_coverage": pct(label),
                "input_coverage": f"0.0% exact / {pct(partial_input)} partial",
                "identity_coverage": pct(identity),
                "main_blocker": main_blocker(position),
            }
        )
    return output


def component_map_summary(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    wanted = [
        "nwr_dynasty_score",
        "nwr_rank",
        "checkpoint_review_score",
        "position_specific_review_score",
        "positive_vorp_points",
        "review_scoring_points",
        "imported_first_down_points",
        "RB role_volume",
        "WR target_route_role",
        "QB passing_volume_security",
        "TE route_target_role",
        "lifecycle_modifier_review",
        "confidence_cap",
        "wr_qb_v2_candidate_adjustment",
        "old_pocket_qb_horizon_cap",
        "market_rank",
        "NGS advanced metrics",
        "PFR advanced metrics",
        "CFBD college metrics",
    ]
    output = []
    for wanted_name in wanted:
        if " " in wanted_name and wanted_name.split(" ", 1)[0] in POSITIONS:
            position, component = wanted_name.split(" ", 1)
            row = next(
                (
                    row
                    for row in rows
                    if row["component_name"] == component and row["position_scope"] == position
                ),
                None,
            )
            name = wanted_name
        else:
            row = next((row for row in rows if row["component_name"] == wanted_name), None)
            name = wanted_name
        if not row:
            continue
        output.append(
            {
                "component_name": name,
                "production_input": short(row["production_input"]),
                "source": short(row["data_source"]),
                "gate_status": short(row["admission_status"]),
                "historical": short(row["historical_availability"]),
                "decision_safe": short(row["available_at_decision_date"]),
                "replay_status": row["replay_status"],
                "caveat": short(row["caveat"], 96),
            }
        )
    return output


def classify_role(path: Path) -> str:
    text = str(path).lower()
    if "services" in text or "app/pages" in text or "app\\pages" in text:
        return "current board/formula code trace"
    if "source_registry" in text or "scoring_rules" in text:
        return "source/scoring contract"
    if "historical_tuning" in text or "production_rankings_backtest" in text:
        return "historical substrate or prior benchmark"
    if "data_sources" in text or "outcomes" in text:
        return "source gate or label gate"
    if "full_player_board" in text:
        return "current displayed board artifact"
    return "supporting evidence"


def replay_capability(replay_status: str) -> str:
    if "EXCLUDED" in replay_status or "BLOCKED" in replay_status:
        return "No"
    if "PARTIAL" in replay_status:
        return "Partial"
    return "No"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    header = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def short(value: object, max_len: int = 72) -> str:
    text = str(value).replace("|", " / ")
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
