from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from src.services.rookie_intake_service import build_rookie_intake_report
from src.services.rookie_model_service import (
    generated_audit_rows,
    generated_model_output_rows,
    run_rookie_model_from_dir,
    write_generated_model_outputs,
)
from src.services.rookie_normalization_service import (
    load_normalization_rules,
    normalize_rookie_raw_metrics,
    write_normalized_rookie_inputs,
)
from src.services.veteran_benchmark_service import (
    ASSET_FILE,
    asset_rows,
    load_or_derive_veteran_benchmarks,
    load_veteran_assets,
)

DEFAULT_DATA_DIR = "sample_data/rookie_model_v1"
DEFAULT_OUTPUT_PATH = "local_exports/rookies/rookie_model_outputs.csv"
DEFAULT_RAW_METRICS = "sample_data/rookie_model_v1/rookie_raw_metrics.csv"
DEFAULT_NORMALIZATION_RULES = "sample_data/rookie_model_v1/rookie_normalization_rules.csv"
DEFAULT_NORMALIZED_OUTPUT = "local_exports/rookies/normalized_rookie_prospect_inputs.csv"


@st.cache_data
def _run_model(data_dir: str, data_dir_fingerprint: tuple[str, int, int, int]):
    _ = data_dir_fingerprint
    intake = build_rookie_intake_report(data_dir)
    run = run_rookie_model_from_dir(data_dir)
    board = pd.DataFrame(generated_model_output_rows(run.scores))
    audit = pd.DataFrame(generated_audit_rows(run))
    registry = pd.DataFrame([feature.__dict__ for feature in run.registry])
    intake_rows = pd.DataFrame([row.__dict__ for row in intake.rows])
    intake_issues = pd.DataFrame([issue.__dict__ for issue in intake.issues])
    return board, audit, registry, intake_rows, intake_issues


@st.cache_data
def _load_normalization(
    raw_metrics: str,
    rules_path: str,
    raw_metrics_fingerprint: tuple[str, int, int, int],
    rules_fingerprint: tuple[str, int, int, int],
):
    _ = raw_metrics_fingerprint, rules_fingerprint
    rules = load_normalization_rules(rules_path)
    result = normalize_rookie_raw_metrics(raw_metrics, rules_path)
    rule_frame = pd.DataFrame([rule.__dict__ for rule in rules])
    feature_frame = pd.DataFrame([feature.__dict__ for feature in result.features])
    return rule_frame, feature_frame, result.rows


@st.cache_data
def _load_veteran_overlay(data_dir: str, data_dir_fingerprint: tuple[str, int, int, int]):
    _ = data_dir_fingerprint
    asset_path = Path(data_dir) / ASSET_FILE
    if not asset_path.exists():
        return pd.DataFrame(), pd.DataFrame()
    assets = load_veteran_assets(asset_path)
    benchmarks = load_or_derive_veteran_benchmarks(data_dir)
    benchmark_frame = pd.DataFrame(
        [
            {
                "benchmark_id": benchmark.benchmark_id,
                "position": benchmark.position.value,
                "benchmark_type": benchmark.benchmark_type,
                "benchmark_score": benchmark.benchmark_score,
                "same_position_score": benchmark.same_position_score,
                "flex_pool_score": benchmark.flex_pool_score,
                "asset_count": benchmark.asset_count,
                "source_snapshot_id": benchmark.source_snapshot_id,
                "source_date": benchmark.source_date,
            }
            for benchmark in benchmarks or ()
        ]
    )
    return pd.DataFrame(asset_rows(assets)), benchmark_frame


st.title("Rookie Board")

with st.sidebar:
    data_dir = st.text_input("Rookie source", DEFAULT_DATA_DIR)
    output_path = st.text_input("Generated output", DEFAULT_OUTPUT_PATH)
    raw_metrics_path = st.text_input("Raw metrics", DEFAULT_RAW_METRICS)
    rules_path = st.text_input("Normalization rules", DEFAULT_NORMALIZATION_RULES)
    normalized_output_path = st.text_input("Normalized output", DEFAULT_NORMALIZED_OUTPUT)
    if st.button("Normalize raw metrics", use_container_width=True):
        _load_normalization.clear()
        result = normalize_rookie_raw_metrics(raw_metrics_path, rules_path)
        write_normalized_rookie_inputs(normalized_output_path, result.rows)
        st.success(f"Wrote {Path(normalized_output_path)}")
    if st.button("Run V1 model", use_container_width=True):
        _run_model.clear()
        run = run_rookie_model_from_dir(data_dir)
        write_generated_model_outputs(output_path, run.scores)
        st.success(f"Wrote {Path(output_path)}")

data_dir_fingerprint = path_fingerprint(data_dir)
board_frame, audit_frame, registry_frame, intake_frame, intake_issues = _run_model(
    data_dir,
    data_dir_fingerprint,
)
rule_frame, normalized_feature_frame, _normalized_rows = _load_normalization(
    raw_metrics_path,
    rules_path,
    path_fingerprint(raw_metrics_path),
    path_fingerprint(rules_path),
)
veteran_asset_frame, veteran_benchmark_frame = _load_veteran_overlay(
    data_dir,
    data_dir_fingerprint,
)

left, middle, right, fourth = st.columns(4)
left.metric("Rookies", len(board_frame))
middle.metric(
    "Top Score",
    f"{board_frame['final_decision_score'].max():.1f}" if not board_frame.empty else "0.0",
)
right.metric("Model", board_frame["model_version"].iloc[0] if not board_frame.empty else "none")
fourth.metric(
    "Ready",
    int((intake_frame["readiness"] == "ready").sum()) if not intake_frame.empty else 0,
)

if board_frame.empty:
    st.dataframe(board_frame, use_container_width=True, hide_index=True)
else:
    board_frame = board_frame.sort_values(
        ["final_decision_score", "confidence_score", "main_prospect_score", "player_id"],
        ascending=[False, False, False, True],
    )
    positions = sorted(board_frame["position"].unique())
    controls = st.columns(3)
    selected_positions = controls[0].multiselect("Position", positions, default=positions)
    min_confidence = controls[1].slider("Min confidence", 0, 100, 0)
    show_gated = controls[2].checkbox("Gates only")

    filtered = board_frame[
        board_frame["position"].isin(selected_positions)
        & (board_frame["confidence_score"] >= min_confidence)
    ]
    if show_gated:
        filtered = filtered[filtered["gate_applied"] != "none"]

    intake_tab, board_tab, audit_tab, registry_tab, normalization_tab, veteran_tab = st.tabs(
        ["Intake", "Board", "Audit", "Registry", "Normalization", "Veterans"]
    )

    with intake_tab:
        if not intake_issues.empty and (intake_issues["severity"] == "error").any():
            st.error("Rookie intake has blocking errors.")
        elif not intake_issues.empty:
            st.warning("Rookie intake has warnings that lower confidence or need review.")
        else:
            st.success("Rookie intake is ready.")

        st.subheader("Readiness")
        st.dataframe(
            intake_frame[
                [
                    "player_name",
                    "position",
                    "model_mode",
                    "readiness",
                    "model_output_allowed",
                    "missing_core_features",
                    "missing_feature_sources",
                    "invalid_feature_values",
                    "source_snapshot_id",
                    "source_name",
                    "source_date",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "model_output_allowed": st.column_config.CheckboxColumn("Scorable"),
                "missing_core_features": st.column_config.NumberColumn("Missing Core"),
                "missing_feature_sources": st.column_config.NumberColumn("No Source"),
                "invalid_feature_values": st.column_config.NumberColumn("Bad Values"),
            },
        )

        st.subheader("Issues")
        if intake_issues.empty:
            st.dataframe(
                pd.DataFrame(
                    columns=["severity", "player_name", "field_name", "issue", "suggested_fix"]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(
                intake_issues[
                    [
                        "severity",
                        "player_name",
                        "field_name",
                        "issue",
                        "suggested_fix",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    with board_tab:
        st.dataframe(
            filtered[
                [
                    "board_rank",
                    "player_name",
                    "position",
                    "final_decision_score",
                    "confidence_score",
                    "recommended_range_label",
                    "do_not_draft_before_pick",
                    "main_prospect_score",
                    "league_fit_score",
                    "rookie_opportunity_score",
                    "veteran_opportunity_adjustment",
                    "gate_applied",
                    "risk_flags",
                    "upside_flags",
                    "floor_flags",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "board_rank": st.column_config.NumberColumn("Rank", pinned=True),
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "final_decision_score": st.column_config.NumberColumn("Final", format="%.1f"),
                "confidence_score": st.column_config.NumberColumn("Conf", format="%.1f"),
                "recommended_range_label": st.column_config.TextColumn("Range"),
                "do_not_draft_before_pick": st.column_config.NumberColumn("Floor"),
                "main_prospect_score": st.column_config.NumberColumn("Prospect", format="%.1f"),
                "league_fit_score": st.column_config.NumberColumn("LVE Fit", format="%.1f"),
                "rookie_opportunity_score": st.column_config.NumberColumn("Year 1", format="%.1f"),
                "veteran_opportunity_adjustment": st.column_config.NumberColumn(
                    "Vet Adj",
                    format="%+.1f",
                ),
            },
        )

    with audit_tab:
        audit_positions = selected_positions
        visible_player_ids = set(filtered["player_id"])
        audit_filtered = audit_frame[
            audit_frame["position"].isin(audit_positions)
            & audit_frame["player_id"].isin(visible_player_ids)
        ].sort_values(
            ["player_name", "weighted_final_contribution"],
            ascending=[True, False],
        )
        st.dataframe(
            audit_filtered[
                [
                    "player_name",
                    "position",
                    "feature_name",
                    "normalized_score",
                    "feature_weight",
                    "component_contribution",
                    "weighted_final_contribution",
                    "is_missing",
                    "evidence_strength",
                    "source_key",
                    "source_snapshot_id",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "player_name": st.column_config.TextColumn("Player", pinned=True),
                "normalized_score": st.column_config.NumberColumn("Score", format="%.1f"),
                "feature_weight": st.column_config.NumberColumn("Weight", format="%.0f"),
                "component_contribution": st.column_config.NumberColumn(
                    "Main Pts",
                    format="%.2f",
                ),
                "weighted_final_contribution": st.column_config.NumberColumn(
                    "Final Pts",
                    format="%.2f",
                ),
            },
        )

    with registry_tab:
        st.dataframe(
            registry_frame[
                [
                    "feature_id",
                    "position",
                    "feature_name",
                    "parent_component",
                    "default_weight",
                    "evidence_strength",
                    "is_core",
                    "is_display_only",
                    "post_draft_only",
                    "requires_source_type",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with normalization_tab:
        st.subheader("Rules")
        st.dataframe(
            rule_frame[
                [
                    "rule_id",
                    "position",
                    "feature_name",
                    "raw_metric",
                    "transform_type",
                    "direction",
                    "min_raw",
                    "max_raw",
                    "source_snapshot_id",
                    "notes",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.subheader("Generated Feature Scores")
        st.dataframe(
            normalized_feature_frame[
                [
                    "player_id",
                    "position",
                    "feature_name",
                    "raw_metric",
                    "raw_value",
                    "normalized_score",
                    "rule_id",
                    "source_key",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "player_id": st.column_config.TextColumn("Player ID", pinned=True),
                "raw_value": st.column_config.NumberColumn("Raw", format="%.3f"),
                "normalized_score": st.column_config.NumberColumn("Score", format="%.1f"),
            },
        )

    with veteran_tab:
        st.subheader("Derived Benchmarks")
        if veteran_benchmark_frame.empty:
            st.info("No veteran asset table found; static benchmark bands are being used.")
        else:
            st.dataframe(
                veteran_benchmark_frame,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "position": st.column_config.TextColumn("Pos", pinned=True),
                    "benchmark_score": st.column_config.NumberColumn(
                        "Benchmark",
                        format="%.2f",
                    ),
                    "same_position_score": st.column_config.NumberColumn(
                        "Same Pos",
                        format="%.2f",
                    ),
                    "flex_pool_score": st.column_config.NumberColumn(
                        "Flex",
                        format="%.2f",
                    ),
                },
            )

        st.subheader("Available Veteran Pool")
        if veteran_asset_frame.empty:
            st.dataframe(veteran_asset_frame, use_container_width=True, hide_index=True)
        else:
            st.dataframe(
                veteran_asset_frame.sort_values(
                    ["is_active_benchmark", "position", "lve_veteran_score"],
                    ascending=[False, True, False],
                ),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "asset_name": st.column_config.TextColumn("Asset", pinned=True),
                    "lve_veteran_score": st.column_config.NumberColumn(
                        "LVE",
                        format="%.1f",
                    ),
                    "win_now_score": st.column_config.NumberColumn(
                        "Now",
                        format="%.1f",
                    ),
                    "hold_value_score": st.column_config.NumberColumn(
                        "Hold",
                        format="%.1f",
                    ),
                    "trade_liquidity_score": st.column_config.NumberColumn(
                        "Trade",
                        format="%.1f",
                    ),
                    "is_active_benchmark": st.column_config.CheckboxColumn("Active"),
                },
            )
