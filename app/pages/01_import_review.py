from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import SESSION_KEY, render_data_pack_selector
from app.components.demo_source_labels import demo_source_label
from app.components.trust_status import render_trust_status
from src.config.settings import get_settings
from src.services.app_workflow_service import (
    build_app_workflow_report,
    workflow_summary_row,
)
from src.services.command_board_service import build_import_review_board
from src.services.data_pack_admission_service import (
    admission_reason_rows,
    admission_summary_row,
    build_data_pack_admission_report,
)
from src.services.data_pack_build_service import (
    DEFAULT_DATA_PACK_OUTPUT_ROOT,
    build_data_pack_from_refresh,
    data_pack_status_rows,
    find_latest_rank_merge_for_snapshot,
)
from src.services.data_pack_catalog_service import (
    DataPackCatalogEntry,
    discover_data_packs,
)
from src.services.data_pack_diff_service import (
    build_data_pack_diff_report,
    diff_detail_rows,
    diff_summary_rows,
)
from src.services.data_pack_health_service import (
    build_data_pack_health_report,
    coverage_report_rows,
    health_check_rows,
    health_issue_rows,
    health_summary_row,
    readiness_status_rows,
)
from src.services.final_calibration_gate_service import (
    build_final_calibration_gate,
    final_calibration_gate_rows,
    final_calibration_gate_summary_row,
)
from src.services.lve_refresh_service import (
    DEFAULT_MERGED_OUTPUT_ROOT,
    DEFAULT_RANK_TEXT_PATH,
    DEFAULT_SLEEPER_OUTPUT_ROOT,
    find_latest_sleeper_snapshot,
    refresh_status_rows,
    run_full_refresh,
    run_rank_merge_for_snapshot,
    run_sleeper_refresh,
)
from src.services.nflverse_player_stats_import_service import (
    official_player_stats_source_rows,
)
from src.services.nflverse_raw_import_service import (
    nflverse_raw_import_readiness_rows,
    nflverse_raw_import_summary_rows,
    validate_nflverse_raw_imports,
)
from src.services.ranking_readiness_service import ranking_readiness_from_calibration
from src.services.routine_refresh_service import (
    DEFAULT_ROUTINE_VETERAN_MODEL_INPUT_DIR,
    routine_refresh_status_rows,
    run_routine_refresh,
)
from src.services.sleeper_import_service import DEFAULT_LEAGUE_ID


@st.cache_data
def _load_board(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_import_review_board(active_data_pack)


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


@st.cache_data
def _load_diff(
    baseline_data_pack: str,
    candidate_data_pack: str,
    baseline_fingerprint: tuple[str, int, int, int],
    candidate_fingerprint: tuple[str, int, int, int],
):
    _ = baseline_fingerprint, candidate_fingerprint
    return build_data_pack_diff_report(
        baseline_data_pack=baseline_data_pack,
        candidate_data_pack=candidate_data_pack,
    )


@st.cache_data
def _load_admission(
    candidate_data_pack: str,
    baseline_data_pack: str | None,
    candidate_fingerprint: tuple[str, int, int, int],
    baseline_fingerprint: tuple[str, int, int, int] | None,
):
    _ = candidate_fingerprint, baseline_fingerprint
    return build_data_pack_admission_report(
        candidate_data_pack=candidate_data_pack,
        baseline_data_pack=baseline_data_pack,
    )


def _pack_option_label(entry: DataPackCatalogEntry) -> str:
    return (
        f"{entry.name} | {entry.source_group} | "
        f"{entry.snapshot_date or 'unknown'} | "
        f"{entry.error_count} errors/{entry.warning_count} warnings"
    )


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
default_nflverse_raw_import_root = Path("local_exports/nflverse/raw")
board = _load_board(active_data_pack, active_fingerprint)
health = _load_health(active_data_pack, active_fingerprint)
calibration = build_final_calibration_gate(active_data_pack)
ranking_readiness = ranking_readiness_from_calibration(calibration)

st.title("Import & Refresh")
st.caption(demo_source_label(active_data_pack))
admission_for_workflow = _load_admission(
    active_data_pack,
    None,
    active_fingerprint,
    None,
)
workflow = build_app_workflow_report(health, admission_for_workflow, calibration)

st.subheader("How To Use This App Right Now")
st.dataframe(
    pd.DataFrame([workflow_summary_row(workflow)]),
    use_container_width=True,
    hide_index=True,
)
if workflow.mode in {"Data Blocked", "Safe Inventory Mode"}:
    st.error(f"**{workflow.headline}** {workflow.explanation}")
elif workflow.mode == "Decision Mode":
    st.success(f"**{workflow.headline}** {workflow.explanation}")
else:
    st.warning(f"**{workflow.headline}** {workflow.explanation}")
st.info(f"Next: {workflow.primary_next_step}")

guide_tabs = st.tabs(["Safe Now", "Blocked", "Next Update", "Pages"])
with guide_tabs[0]:
    st.dataframe(pd.DataFrame(workflow.safe_rows), use_container_width=True, hide_index=True)
with guide_tabs[1]:
    if workflow.blocked_rows:
        st.dataframe(
            pd.DataFrame(workflow.blocked_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("Nothing is blocked by the current workflow mode.")
with guide_tabs[2]:
    st.dataframe(
        pd.DataFrame(workflow.next_update_rows),
        use_container_width=True,
        hide_index=True,
    )
with guide_tabs[3]:
    st.dataframe(pd.DataFrame(workflow.page_rows), use_container_width=True, hide_index=True)

left, middle, right, far_right = st.columns(4)
left.metric("Errors", board.issue_counts.get("error", 0))
middle.metric("Warnings", board.issue_counts.get("warning", 0))
right.metric("Snapshot", board.snapshot_date or "unknown")
far_right.metric("Pack Health", health.readiness.upper())

if board.has_errors:
    st.error("Data is blocked. Fix the listed import errors before using any board.")
else:
    st.success("Data files load. Review model and decision readiness below.")
render_trust_status(health, calibration_passed=ranking_readiness.calibration_passed)

with st.expander("Advanced: readiness and calibration gate"):
    st.subheader("Readiness")
    st.dataframe(
        pd.DataFrame(readiness_status_rows(health)),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Final Calibration Gate")
    st.dataframe(
        pd.DataFrame([final_calibration_gate_summary_row(calibration)]),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(final_calibration_gate_rows(calibration)),
        use_container_width=True,
        hide_index=True,
    )

(
    admission_tab,
    health_tab,
    coverage_tab,
    diff_tab,
    validation_tab,
    rows_tab,
    sources_tab,
) = st.tabs(
    [
        "Admission",
        "Pack Health",
        "Coverage",
        "Pack Diff",
        "Validation",
        "Loaded Rows",
        "Sources",
    ]
)

entries = discover_data_packs(
    project_root=settings.project_root,
    default_data_pack=settings.active_data_pack,
)
baseline_options = {
    _pack_option_label(entry): str(entry.path)
    for entry in entries
    if str(entry.path) != active_data_pack
}
selected_baseline = (
    st.session_state.get("admission_baseline_label")
    if st.session_state.get("admission_baseline_label") in baseline_options
    else None
)
baseline_path = baseline_options[selected_baseline] if selected_baseline else None

with admission_tab:
    if baseline_options:
        admission_options = ["No baseline"] + list(baseline_options)
        current_admission_label = (
            st.session_state.get("admission_baseline_label") or "No baseline"
        )
        admission_index = (
            admission_options.index(current_admission_label)
            if current_admission_label in admission_options
            else 0
        )
        selected_baseline = st.selectbox(
            "Admission baseline",
            admission_options,
            index=admission_index,
        )
        baseline_path = (
            baseline_options[selected_baseline]
            if selected_baseline != "No baseline"
            else None
        )
        st.session_state["admission_baseline_label"] = (
            selected_baseline if selected_baseline != "No baseline" else None
        )
    baseline_fingerprint = path_fingerprint(baseline_path) if baseline_path else None
    admission = _load_admission(
        active_data_pack,
        baseline_path,
        active_fingerprint,
        baseline_fingerprint,
    )
    st.dataframe(
        pd.DataFrame([admission_summary_row(admission)]),
        use_container_width=True,
        hide_index=True,
    )
    if admission.decision == "blocked":
        st.error("Decision blocked: fix the listed data issue first.")
    elif admission.decision == "review":
        st.warning("Review mode: tables can help, but recommendations are not final.")
    elif ranking_readiness.review_only:
        st.warning(
            "Data pack admitted for inspection, but rankings are review-only until "
            "the sanity/audit gates pass."
        )
    else:
        st.success("Decision ready: this pack can drive the local boards.")
    st.subheader("Reasons and Actions")
    st.dataframe(
        pd.DataFrame(admission_reason_rows(admission)),
        use_container_width=True,
        hide_index=True,
    )

with health_tab:
    summary_frame = pd.DataFrame([health_summary_row(health)])
    st.subheader("Pack Summary")
    st.dataframe(summary_frame, use_container_width=True, hide_index=True)
    st.subheader("Readiness Checks")
    st.dataframe(
        pd.DataFrame(health_check_rows(health)),
        use_container_width=True,
        hide_index=True,
    )

with coverage_tab:
    st.subheader("Coverage Report")
    st.caption(
        "Coverage shows whether the active pack has the rows needed for review, "
        "model scoring, and decision-ready boards. It does not change any score."
    )
    coverage_frame = pd.DataFrame(coverage_report_rows(health))
    st.dataframe(coverage_frame, use_container_width=True, hide_index=True)
    blocking_coverage = coverage_frame[coverage_frame["decision_blocking"].astype(bool)]
    review_coverage = coverage_frame[coverage_frame["status"] == "review"]
    if not blocking_coverage.empty:
        st.error("Coverage has blocking gaps. Fix those before money decisions.")
    elif not review_coverage.empty:
        st.warning("Coverage has review gaps. The pack can load, but verify these rows.")
    else:
        st.success("Coverage is complete for the current readiness contract.")

with diff_tab:
    if not baseline_options:
        st.info("No other data pack is available for comparison.")
    else:
        diff_options = list(baseline_options)
        selected_baseline = st.selectbox("Compare against", diff_options)
        selected_baseline_path = baseline_options[selected_baseline]
        diff_report = _load_diff(
            selected_baseline_path,
            active_data_pack,
            path_fingerprint(selected_baseline_path),
            active_fingerprint,
        )
        left_diff, right_diff = st.columns(2)
        left_diff.metric("Baseline", diff_report.baseline_snapshot or "unknown")
        right_diff.metric("Candidate", diff_report.candidate_snapshot or "unknown")
        st.subheader("Change Summary")
        st.dataframe(
            pd.DataFrame(diff_summary_rows(diff_report)),
            use_container_width=True,
            hide_index=True,
        )
        st.subheader("Change Details")
        detail_frame = pd.DataFrame(diff_detail_rows(diff_report))
        if detail_frame.empty:
            st.success("No roster, league-rank, or pick-owner changes found.")
            st.dataframe(
                pd.DataFrame(
                    columns=[
                        "change_type",
                        "player",
                        "pick",
                        "position",
                        "from_team",
                        "to_team",
                        "baseline_value",
                        "candidate_value",
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(detail_frame, use_container_width=True, hide_index=True)

with validation_tab:
    issue_frame = pd.DataFrame(health_issue_rows(health))
    if issue_frame.empty:
        st.dataframe(
            pd.DataFrame(columns=["severity", "file", "row", "entity", "issue", "fix"])
        )
    else:
        severity_filter = st.multiselect(
            "Severity",
            sorted(issue_frame["severity"].dropna().unique()),
            default=sorted(issue_frame["severity"].dropna().unique()),
        )
        filtered_issues = issue_frame[issue_frame["severity"].isin(severity_filter)]
        st.dataframe(filtered_issues, use_container_width=True, hide_index=True)

with rows_tab:
    st.dataframe(pd.DataFrame(board.row_counts), use_container_width=True, hide_index=True)

with sources_tab:
    source_frame = pd.DataFrame(board.source_rows)
    st.dataframe(source_frame, use_container_width=True, hide_index=True)

st.subheader("Routine Refresh")
st.caption(
    "One safe refresh path: Sleeper snapshot, league-rank merge, candidate data pack, "
    "validation, optional model scoring, and readiness review. Frozen/final folders are blocked."
)

refresh_league_id = st.text_input("Sleeper league ID", value=DEFAULT_LEAGUE_ID)
rank_text_path = st.text_input("League-rank text path", value=str(DEFAULT_RANK_TEXT_PATH))
routine_cols = st.columns(3)
with routine_cols[0]:
    refresh_sleeper_enabled = st.checkbox("Refresh Sleeper from API", value=True)
with routine_cols[1]:
    dry_run_enabled = st.checkbox("Dry run only", value=False)
with routine_cols[2]:
    make_candidate_active = st.checkbox("Select built candidate pack", value=True)

with st.expander("Routine Paths", expanded=False):
    sleeper_output_root = st.text_input(
        "Sleeper output root",
        value=str(DEFAULT_SLEEPER_OUTPUT_ROOT),
    )
    merged_output_root = st.text_input(
        "Merged output root",
        value=str(DEFAULT_MERGED_OUTPUT_ROOT),
    )
    data_pack_output_root = st.text_input(
        "Candidate data-pack output root",
        value=str(DEFAULT_DATA_PACK_OUTPUT_ROOT),
    )
    veteran_model_input_dir = st.text_input(
        "Veteran model input root",
        value=str(DEFAULT_ROUTINE_VETERAN_MODEL_INPUT_DIR),
    )

if st.button("Refresh Data", type="primary"):
    result = run_routine_refresh(
        league_id=refresh_league_id,
        rank_text_path=rank_text_path,
        sleeper_output_root=sleeper_output_root,
        merged_output_root=merged_output_root,
        data_pack_output_root=data_pack_output_root,
        veteran_model_input_dir=veteran_model_input_dir,
        refresh_sleeper=refresh_sleeper_enabled,
        dry_run=dry_run_enabled,
    )
    st.session_state["routine_refresh_rows"] = routine_refresh_status_rows(result)
    st.session_state["routine_refresh_warnings"] = list(result.warnings)
    st.session_state["routine_refresh_summary"] = {
        "run_id": result.run_id,
        "status": result.status,
        "readiness": result.readiness,
        "dry_run": result.dry_run,
        "candidate_pack": str(result.active_candidate_pack or ""),
    }
    if result.active_candidate_pack and not result.dry_run and make_candidate_active:
        st.session_state[SESSION_KEY] = str(result.active_candidate_pack)
    if result.status == "blocked":
        st.error("Refresh blocked. Review the step statuses below.")
    elif result.status == "planned":
        st.info("Dry run complete. No files were changed.")
    elif result.status == "ready":
        st.success("Refresh complete. Candidate pack is ready for review.")
    else:
        st.warning("Refresh complete with review items. Check readiness before using boards.")

if st.session_state.get("routine_refresh_summary"):
    st.subheader("Last Routine Refresh")
    st.dataframe(
        pd.DataFrame([st.session_state["routine_refresh_summary"]]),
        use_container_width=True,
        hide_index=True,
    )

if st.session_state.get("routine_refresh_warnings"):
    for warning in st.session_state["routine_refresh_warnings"]:
        st.warning(warning)

if st.session_state.get("routine_refresh_rows"):
    st.dataframe(
        pd.DataFrame(st.session_state["routine_refresh_rows"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "mutated": st.column_config.CheckboxColumn("Wrote Files"),
        },
    )

st.subheader("Stats Source Backbone")
st.caption(
    "Sleeper and league ranks tell the app who is in the league. The stats backbone "
    "is where nflverse football evidence enters later model previews. These rows are "
    "source readiness only; they do not change rankings until an explicit preview/apply."
)
raw_import_report = validate_nflverse_raw_imports(default_nflverse_raw_import_root)
raw_import_rows = nflverse_raw_import_readiness_rows(raw_import_report)
raw_summary_rows = nflverse_raw_import_summary_rows(raw_import_rows)
stat_cols = st.columns(3)
stat_cols[0].metric("Raw nflverse Root", raw_import_report.status.upper())
stat_cols[1].metric(
    "Ready Files",
    sum(1 for row in raw_import_rows if row["status"] == "ready"),
)
stat_cols[2].metric(
    "Blocked Files",
    sum(1 for row in raw_import_rows if row["status"] == "blocked"),
)
with st.expander("Stats Source Import Status", expanded=False):
    st.caption(
        f"Local raw folder: `{default_nflverse_raw_import_root}`. "
        "The player-stats helper can transform the official nflverse CSV into the "
        "local weekly-stats template."
    )
    st.code(
        "python scripts/import_nflverse_player_stats.py "
        "--download-to local_exports/nflverse/downloads/player_stats.csv "
        "--season 2025 "
        "--output local_exports/nflverse/raw/nflverse_player_stats_weekly.csv",
        language="powershell",
    )
    st.dataframe(
        pd.DataFrame(raw_summary_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(raw_import_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Verified Source Contracts")
    st.dataframe(
        pd.DataFrame(official_player_stats_source_rows()),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Advanced Manual Refresh Tools", expanded=False):
    st.caption(
        "These are the old step-by-step tools. Use them only for debugging a failed "
        "routine refresh."
    )
    latest_snapshot = find_latest_sleeper_snapshot(
        league_id=refresh_league_id,
        output_root=sleeper_output_root,
    )
    snapshot_dir = st.text_input(
        "Snapshot folder for rank merge",
        value=str(latest_snapshot or ""),
    )
    latest_rank_merge = (
        find_latest_rank_merge_for_snapshot(
            sleeper_output_dir=snapshot_dir,
            merged_output_root=merged_output_root,
        )
        if snapshot_dir
        else None
    )
    rank_merge_dir = st.text_input(
        "Merged rank folder for data pack",
        value=str(latest_rank_merge or ""),
    )

    refresh_cols = st.columns(4)
    with refresh_cols[0]:
        if st.button("Refresh Sleeper Snapshot", type="secondary"):
            try:
                sleeper_result = run_sleeper_refresh(
                    league_id=refresh_league_id,
                    output_root=sleeper_output_root,
                )
                st.session_state["refresh_status_rows"] = [
                    {
                        "step": f"sleeper_{name}",
                        "status": "ok",
                        "rows": sleeper_result.counts.get(name, 0),
                        "output_path": str(path),
                        "message": "Local Sleeper snapshot file refreshed.",
                    }
                    for name, path in sleeper_result.files.items()
                ]
                st.session_state["last_sleeper_snapshot_dir"] = str(
                    sleeper_result.output_dir
                )
                st.success(f"Refreshed Sleeper snapshot: {sleeper_result.output_dir}")
            except Exception as exc:
                st.error(f"Sleeper refresh failed: {exc}")

    with refresh_cols[1]:
        if st.button("Merge League Ranks", type="secondary"):
            if not snapshot_dir:
                st.warning("Choose or enter a Sleeper snapshot folder first.")
            else:
                try:
                    merge_result = run_rank_merge_for_snapshot(
                        sleeper_output_dir=snapshot_dir,
                        rank_text_path=rank_text_path,
                        output_root=merged_output_root,
                    )
                    st.session_state["refresh_status_rows"] = [
                        {
                            "step": f"league_rank_{name}",
                            "status": "ok",
                            "rows": merge_result.counts.get(name, 0),
                            "output_path": str(path),
                            "message": "League-rank merge output refreshed.",
                        }
                        for name, path in merge_result.files.items()
                    ]
                    st.session_state["last_rank_merge_dir"] = str(merge_result.output_dir)
                    st.success(f"Merged league ranks: {merge_result.output_dir}")
                except Exception as exc:
                    st.error(f"League-rank merge failed: {exc}")

    with refresh_cols[2]:
        if st.button("Run Full Refresh", type="secondary"):
            result = run_full_refresh(
                league_id=refresh_league_id,
                rank_text_path=rank_text_path,
                sleeper_output_root=sleeper_output_root,
                merged_output_root=merged_output_root,
            )
            st.session_state["refresh_status_rows"] = refresh_status_rows(result)
            st.session_state["refresh_warnings"] = list(result.warnings)
            if any(step.status == "error" for step in result.steps):
                st.error("Refresh completed with errors. Review the status rows below.")
            else:
                st.success("Full refresh completed.")
            if result.sleeper_result is not None:
                st.session_state["last_sleeper_snapshot_dir"] = str(
                    result.sleeper_result.output_dir
                )
            if result.rank_merge_result is not None:
                st.session_state["last_rank_merge_dir"] = str(
                    result.rank_merge_result.output_dir
                )

    with refresh_cols[3]:
        if st.button("Build Data Pack", type="secondary"):
            resolved_snapshot_dir = (
                st.session_state.get("last_sleeper_snapshot_dir") or snapshot_dir
            )
            resolved_rank_dir = st.session_state.get("last_rank_merge_dir") or rank_merge_dir
            if not resolved_snapshot_dir:
                st.warning("Refresh or select a Sleeper snapshot folder first.")
            else:
                try:
                    data_pack_result = build_data_pack_from_refresh(
                        sleeper_output_dir=resolved_snapshot_dir,
                        merged_rank_output_dir=resolved_rank_dir or None,
                        output_root=data_pack_output_root,
                    )
                    st.session_state["data_pack_status_rows"] = data_pack_status_rows(
                        data_pack_result
                    )
                    st.session_state["data_pack_warnings"] = list(
                        data_pack_result.warnings
                    )
                    st.success(f"Built data pack: {data_pack_result.output_dir}")
                except Exception as exc:
                    st.error(f"Data pack build failed: {exc}")

    if st.session_state.get("refresh_warnings"):
        for warning in st.session_state["refresh_warnings"]:
            st.warning(warning)

    if st.session_state.get("refresh_status_rows"):
        st.dataframe(
            pd.DataFrame(st.session_state["refresh_status_rows"]),
            use_container_width=True,
            hide_index=True,
        )

    if st.session_state.get("data_pack_warnings"):
        for warning in st.session_state["data_pack_warnings"]:
            st.warning(warning)

    if st.session_state.get("data_pack_status_rows"):
        st.dataframe(
            pd.DataFrame(st.session_state["data_pack_status_rows"]),
            use_container_width=True,
            hide_index=True,
        )
