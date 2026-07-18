from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.durable_refresh_receipt_panel import (
    render_durable_refresh_receipt_panel,
)
from app.components.ui_framework import page_header
from src.services.data_refresh_orchestrator_service import (
    CHECK_PROTECTED_ARTIFACTS,
    DEFAULT_STATUS_PATH,
    FULL_SAFE_REFRESH,
    MANUAL_SOURCES_CHECKLIST,
    QUICK_REFRESH,
    build_refresh_registry,
    export_results_csv,
    refresh_results_table,
    run_check_protected_artifacts,
    run_full_safe_refresh,
    run_manual_sources_checklist,
    run_quick_refresh,
    validate_refresh_result_schema,
)
from src.services.refresh_receipt_store_service import inspect_refresh_receipt

RESULT_COLUMNS = [
    "run_id",
    "run_timestamp",
    "start_time",
    "end_time",
    "loader_mode",
    "source_id",
    "source_name",
    "loader_category",
    "action_type",
    "refreshed",
    "configured",
    "runner_exists",
    "runner_path",
    "exit_code",
    "freshness",
    "source_family",
    "dataset_id",
    "dataset_default_mode",
    "headline_status",
    "execution_status",
    "dataset_health_status",
    "dataset_row_count",
    "dataset_column_count",
    "season_coverage",
    "key_column_coverage",
    "schema_fingerprint",
    "schema_status",
    "coverage_status",
    "row_count_status",
    "freshness_status",
    "missingness_status",
    "source_policy_status",
    "raw_cache_path",
    "tracked_summary_path",
    "training_allowed",
    "rank_logic_allowed",
    "last_attempt_at",
    "last_success_at",
    "full_safe_refresh_health",
    "expected_artifacts",
    "found_artifacts",
    "raw_cache_location",
    "tracked_artifacts_written",
    "user_explanation",
    "model_use_allowed",
    "model_use_warning",
]

NFLVERSE_COLUMNS = [
    "source_id",
    "dataset_id",
    "dataset_default_mode",
    "headline_status",
    "execution_status",
    "schema_status",
    "coverage_status",
    "row_count_status",
    "freshness_status",
    "missingness_status",
    "source_policy_status",
    "dataset_row_count",
    "season_coverage",
    "key_column_coverage",
    "schema_fingerprint",
    "raw_cache_path",
    "tracked_summary_path",
    "model_use_allowed",
    "training_allowed",
    "rank_logic_allowed",
    "user_explanation",
]

REGISTRY_COLUMNS = [
    "source_id",
    "source_name",
    "source_kind",
    "loader_category",
    "enabled_in_quick_refresh",
    "enabled_in_full_safe_refresh",
    "requires_api_key",
    "required_env_vars",
    "runner_exists",
    "configured",
    "safe_to_pull",
    "protected_artifact",
    "writes_raw_cache",
    "raw_cache_location",
    "writes_tracked_artifact",
    "freshness_policy",
    "expected_artifacts",
    "model_use_allowed",
    "model_use_warning",
    "default_action",
    "failure_mode",
    "user_explanation",
]


def _run_and_store(mode: str) -> None:
    runners = {
        QUICK_REFRESH: run_quick_refresh,
        FULL_SAFE_REFRESH: run_full_safe_refresh,
        CHECK_PROTECTED_ARTIFACTS: run_check_protected_artifacts,
        MANUAL_SOURCES_CHECKLIST: run_manual_sources_checklist,
    }
    with st.spinner(f"Running {mode.replace('_', ' ').title()}..."):
        run = runners[mode]()
    rows = refresh_results_table(run)
    validate_refresh_result_schema(rows)
    st.session_state["refresh_data_last_run"] = {
        "run": run,
        "rows": rows,
        "summary": _summary_rows(rows),
    }


def _summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    values = {
        "refreshed": sum(1 for row in rows if row.get("action_type") == "REFRESHED"),
        "checked only": sum(1 for row in rows if row.get("action_type") == "CHECK_ONLY"),
        "skipped by policy": sum(
            1 for row in rows if row.get("action_type") == "SKIPPED_BY_POLICY"
        ),
        "not configured": sum(1 for row in rows if row.get("action_type") == "NOT_CONFIGURED"),
        "manual blocked": sum(1 for row in rows if row.get("action_type") == "BLOCKED_MANUAL"),
        "failed": sum(1 for row in rows if row.get("action_type") == "FAILED"),
    }
    return [{"metric": key, "value": value} for key, value in values.items()]


def _display_results(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)
    return frame.loc[:, RESULT_COLUMNS]


def _display_nflverse_results(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=NFLVERSE_COLUMNS)
    nflverse = frame.loc[
        frame.get("source_family", pd.Series(dtype=str)).astype(str).eq("nflverse")
        | frame.get("source_id", pd.Series(dtype=str)).astype(str).str.startswith("nflverse_")
    ]
    if nflverse.empty:
        return pd.DataFrame(columns=NFLVERSE_COLUMNS)
    return nflverse.loc[:, NFLVERSE_COLUMNS]


def _display_registry() -> pd.DataFrame:
    rows = []
    for entry in build_refresh_registry():
        row = entry.__dict__.copy()
        row["required_env_vars"] = "; ".join(entry.required_env_vars)
        row["expected_artifacts"] = "; ".join(entry.expected_artifacts)
        rows.append(row)
    return pd.DataFrame(rows).loc[:, REGISTRY_COLUMNS]


page_header(
    "Refresh Data",
    eyebrow="Safe Data Loader V1",
    description=(
        "Pull every approved eligible current source; check protected/manual sources; "
        "do not mutate rankings/model/frozen/latest artifacts."
    ),
    status_items=(
        ("No model/rank changes", "safe"),
        ("Manual sources stay manual", "review"),
        ("Protected artifacts check-only", "safe"),
    ),
)

st.caption(
    "Refreshed data does not automatically update rankings, model outputs, candidate files, "
    "the frozen board, pinned snapshots, latest_candidate/latest_approved, or runtime draft state."
)

st.markdown("### Loader Modes")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("Quick Refresh", type="primary", use_container_width=True):
        _run_and_store(QUICK_REFRESH)
with col2:
    if st.button("Full Safe Refresh", use_container_width=True):
        _run_and_store(FULL_SAFE_REFRESH)
with col3:
    if st.button("Check Protected Artifacts", use_container_width=True):
        _run_and_store(CHECK_PROTECTED_ARTIFACTS)
with col4:
    if st.button("Manual Sources Checklist", use_container_width=True):
        _run_and_store(MANUAL_SOURCES_CHECKLIST)

st.info(
    "Quick Refresh pulls Sleeper league state and DynastyProcess market baseline. "
    "Full Safe Refresh also includes the nflverse runner plus dataset-level nflverse "
    "health rows, and CFBD only when CFBD_API_KEY is configured. Vendor, Gmail, "
    "frozen/latest/pinned, model, Outcome, PDF, ADP, and runtime sources are not pulled "
    "automatically. Missing nflverse data means Not enough information, not zero, false, "
    "healthy, clean, no-role, no-injury, or no-usage. Pulled data is review/status/cache "
    "material until a separate approved lane admits it."
)

with st.expander("Manual Sources Checklist", expanded=True):
    st.markdown(
        "\n".join(
            [
                "- Gmail league-history evidence: privacy-gated manual evidence intake; "
                "raw email bodies are not pulled.",
                "- RotoWire/vendor exports: manual/export-only and never scraped.",
                "- FantasyPros/vendor/projection exports: manual/keyed export only; no scraping.",
                "- PDFs/manual evidence files: user-provided and reviewed before use.",
            ]
        )
    )

with st.expander("Source Registry", expanded=False):
    st.dataframe(_display_registry(), use_container_width=True, hide_index=True)

last_run = st.session_state.get("refresh_data_last_run")
if last_run:
    run = last_run["run"]
    st.subheader("Run Summary")
    st.metric("Overall", run.overall_status)
    st.caption(f"{run.loader_mode} finished at {run.finished_at_utc}")
    st.dataframe(
        pd.DataFrame(last_run["summary"]),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Per-Source Results")
    st.dataframe(
        _display_results(list(last_run["rows"])),
        use_container_width=True,
        hide_index=True,
    )
    nflverse_results = _display_nflverse_results(list(last_run["rows"]))
    if not nflverse_results.empty:
        st.subheader("NFLVerse Dataset Health")
        st.dataframe(
            nflverse_results,
            use_container_width=True,
            hide_index=True,
        )
    st.download_button(
        "Export Results",
        data=export_results_csv(run),
        file_name=f"{run.run_id}_{run.loader_mode.lower()}_results.csv",
        mime="text/csv",
    )
else:
    st.info(
        "No safe loader run has been started in this session. The durable local receipt "
        "below remains available across supported reruns and reloads."
    )

render_durable_refresh_receipt_panel(
    inspect_refresh_receipt(status_path=DEFAULT_STATUS_PATH),
    title="Latest durable refresh receipt",
)
