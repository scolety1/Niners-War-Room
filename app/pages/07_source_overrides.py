from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.demo_source_labels import demo_source_label
from app.components.human_labels import human_label
from src.config.settings import get_settings
from src.services.data_pack_health_service import (
    build_data_pack_health_report,
    readiness_status_rows,
)
from src.services.lve_stats_first_apply_service import (
    DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT,
    STATS_FIRST_APPLY_CONFIRMATION,
    create_stats_first_applied_pack,
    stats_first_applied_pack_review_rows,
    stats_first_applied_pack_snapshot_rows,
)
from src.services.lve_stats_first_preview_service import (
    DEFAULT_STATS_FIRST_PREVIEW_ROOT,
    create_stats_first_model_preview,
    stats_first_preview_review_rows,
    stats_first_preview_review_summary_rows,
    stats_first_preview_snapshot_rows,
)
from src.services.nflverse_player_stats_import_service import (
    official_player_stats_source_rows,
)
from src.services.public_source_import_service import (
    DEFAULT_PUBLIC_SOURCE_MODEL_APPLIED_PACK_ROOT,
    DEFAULT_PUBLIC_SOURCE_MODEL_INPUT_ROOT,
    DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT,
    DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT,
    DEFAULT_PUBLIC_SOURCE_SNAPSHOT_ROOT,
    DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT,
    DEFAULT_PUBLIC_SOURCE_WORKLIST_ROOT,
    DEFAULT_VETERAN_FEATURE_REGISTRY_PATH,
    build_public_source_feature_readiness_rows,
    build_public_source_match_rows,
    build_public_source_player_match_rows,
    build_unscored_player_rows,
    create_public_source_model_applied_pack,
    create_public_source_model_input_candidate,
    create_public_source_model_preview,
    create_public_source_model_promotion_candidate,
    create_public_source_normalization_worklist,
    create_public_source_snapshot,
    public_source_backfill_acceptance_rows,
    public_source_backfill_acceptance_summary_rows,
    public_source_count_rows,
    public_source_domain_rows,
    public_source_feature_readiness_summary_rows,
    public_source_issue_rows,
    public_source_model_applied_pack_review_rows,
    public_source_model_applied_pack_review_summary_rows,
    public_source_model_applied_pack_snapshot_rows,
    public_source_model_input_candidate_coverage_rows,
    public_source_model_input_candidate_coverage_summary_rows,
    public_source_model_input_candidate_rows,
    public_source_model_input_candidate_snapshot_rows,
    public_source_model_input_candidate_validation_rows,
    public_source_model_input_candidate_validation_summary_rows,
    public_source_model_preview_comparison_rows,
    public_source_model_preview_comparison_summary_rows,
    public_source_model_preview_review_rows,
    public_source_model_preview_review_summary_rows,
    public_source_model_preview_snapshot_rows,
    public_source_model_promotion_candidate_review_rows,
    public_source_model_promotion_candidate_review_summary_rows,
    public_source_model_promotion_candidate_snapshot_rows,
    public_source_normalization_worklist_rows,
    public_source_normalization_worklist_snapshot_rows,
    public_source_player_match_summary_rows,
    public_source_policy_rows,
    public_source_readiness_rows,
    public_source_snapshot_rows,
    validate_public_source_inputs,
)
from src.services.source_governance_service import build_source_governance_board


@st.cache_data
def _load_board(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
):
    _ = data_pack_fingerprint
    return build_source_governance_board(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_public_source_report(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    source_root: str,
    source_fingerprint: tuple[str, int, int, int],
    backfill_path: str,
    backfill_fingerprint: tuple[str, int, int, int],
    registry_path: str,
    registry_fingerprint: tuple[str, int, int, int],
):
    _ = (
        data_pack_fingerprint,
        source_fingerprint,
        backfill_fingerprint,
        registry_fingerprint,
    )
    report = validate_public_source_inputs(source_root)
    matches = build_public_source_match_rows(active_data_pack, source_root)
    player_matches = build_public_source_player_match_rows(active_data_pack, source_root)
    feature_readiness = build_public_source_feature_readiness_rows(
        active_data_pack,
        source_root,
        registry_path,
    )
    unscored = build_unscored_player_rows(
        active_data_pack,
        backfill_path if backfill_path else None,
    )
    return report, matches, player_matches, feature_readiness, unscored


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
veteran_model_dir = settings.project_root / "sample_data" / "veteran_model_v1"
health = _load_health(active_data_pack, active_fingerprint)

st.title("Settings")
st.caption(
    "Start here when you need to know whether the app's data is usable. Import, "
    "backfill, preview, and source-builder controls are below in Advanced sections."
)

status_rows = readiness_status_rows(health)
model_mode = next(
    (
        str(row.get("status") or "")
        for row in status_rows
        if row.get("status_area") == "model_ready"
    ),
    "review_only",
)
decision_mode = next(
    (
        str(row.get("status") or "")
        for row in status_rows
        if row.get("status_area") == "decision_ready"
    ),
    "review_only",
)

if health.error_count:
    st.error(
        "Data health has blocking errors. Open Data Health Details before "
        "reviewing decisions."
    )
elif health.warning_count:
    st.warning("Data health has warnings. The app is usable, but inspect the warning details.")
else:
    st.success("Data health is ready. Review outputs remain human-review-only.")

health_cols = st.columns(5)
health_cols[0].metric("Active Data Pack", health.data_pack_name)
health_cols[1].metric("Data Health", health.readiness.upper())
health_cols[2].metric("Snapshot", health.snapshot_date or "Unknown")
health_cols[3].metric("Mode", human_label(decision_mode))
health_cols[4].metric("Warnings / Errors", f"{health.warning_count} / {health.error_count}")

model_cols = st.columns(4)
model_cols[0].metric("Model Status", human_label(model_mode))
model_cols[1].metric("Roster Rows", health.roster_count)
model_cols[2].metric("Future Picks", health.pick_count)
model_cols[3].metric("Placeholder Outputs", health.placeholder_model_output_count)

st.caption(
    "A data pack is the active snapshot of rosters, picks, rankings context, "
    "and model review outputs the app is reading. Switching packs changes what "
    "the app displays; opening Settings does not mutate data."
)

st.caption(
    "Opening Settings is read-only. Nothing imports, backfills, previews, or applies "
    "unless you open an Advanced section and click an explicit action."
)

if health.issues:
    st.warning("Major issues: " + "; ".join(str(issue) for issue in health.issues[:5]))
else:
    st.caption("Major warnings/errors: none reported by the active data pack health check.")

with st.expander("Data Health Details", expanded=False):
    health_rows = pd.DataFrame(readiness_status_rows(health))
    for column in ("status", "check", "level"):
        if column in health_rows:
            health_rows[column] = health_rows[column].map(human_label)
    st.dataframe(
        health_rows,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(demo_source_label(active_data_pack))

with st.expander("Advanced Settings", expanded=False):
    st.caption(
        "Local source roots and export paths. Change these only when you are "
        "rebuilding inputs or reviewing source imports."
    )
    left, right = st.columns(2)
    with left:
        public_source_root = st.text_input(
            "Public source root",
            value=str(DEFAULT_PUBLIC_SOURCE_TEMPLATE_ROOT),
        )
        feature_backfill_path = st.text_input(
            "Feature backfill file",
            value="local_exports/money_readiness/veteran_feature_scores_backfill_required.csv",
        )
        public_snapshot_root = st.text_input(
            "Public source snapshot root",
            value=str(DEFAULT_PUBLIC_SOURCE_SNAPSHOT_ROOT),
        )
        normalization_worklist_root = st.text_input(
            "Normalization worklist root",
            value=str(DEFAULT_PUBLIC_SOURCE_WORKLIST_ROOT),
        )
        model_input_candidate_root = st.text_input(
            "Model input candidate root",
            value=str(DEFAULT_PUBLIC_SOURCE_MODEL_INPUT_ROOT),
        )
        model_preview_root = st.text_input(
            "Model preview root",
            value=str(DEFAULT_PUBLIC_SOURCE_MODEL_PREVIEW_ROOT),
        )
    with right:
        model_promotion_root = st.text_input(
            "Model promotion candidate root",
            value=str(DEFAULT_PUBLIC_SOURCE_MODEL_PROMOTION_ROOT),
        )
        model_applied_pack_root = st.text_input(
            "Model applied pack root",
            value=str(DEFAULT_PUBLIC_SOURCE_MODEL_APPLIED_PACK_ROOT),
        )
        stats_first_normalized_feature_path = st.text_input(
            "NFLVerse normalized features",
            value="local_exports/nflverse/lve_normalized_veteran_features.csv",
        )
        stats_first_preview_root = st.text_input(
            "Stats-first preview root",
            value=str(DEFAULT_STATS_FIRST_PREVIEW_ROOT),
        )
        stats_first_applied_pack_root = st.text_input(
            "Stats-first applied pack root",
            value=str(DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT),
        )
        veteran_feature_registry_path = st.text_input(
            "Veteran feature registry",
            value=str(DEFAULT_VETERAN_FEATURE_REGISTRY_PATH),
        )

board = _load_board(
    active_data_pack,
    path_fingerprint(active_data_pack),
    str(veteran_model_dir),
)
(
    public_report,
    public_matches,
    public_player_matches,
    public_feature_readiness,
    unscored_players,
) = _load_public_source_report(
    active_data_pack,
    path_fingerprint(active_data_pack),
    public_source_root,
    path_fingerprint(public_source_root),
    feature_backfill_path,
    path_fingerprint(feature_backfill_path),
    veteran_feature_registry_path,
    path_fingerprint(veteran_feature_registry_path),
)

st.info(
    "Advanced controls are file-based and review-only by default. Direct final-score "
    "overrides are blocked by validation unless a future model phase explicitly "
    "approves them."
)

tabs = [
    st.expander(label, expanded=False)
    for label in (
        "Advanced: Data Pack Sources",
        "Advanced: Veteran Source Audit",
        "Advanced: Audit Notes",
        "Advanced: Source Overrides",
        "Advanced: Import, Refresh, And Backfills",
        "Advanced: Stats-First Preview Packs",
        "Advanced: Raw Data / Debug Validation",
    )
]

with tabs[0]:
    st.dataframe(
        pd.DataFrame(board.data_pack_sources),
        use_container_width=True,
        hide_index=True,
    )

with tabs[1]:
    st.dataframe(
        pd.DataFrame(board.veteran_sources),
        use_container_width=True,
        hide_index=True,
    )

with tabs[2]:
    st.dataframe(
        pd.DataFrame(board.audit_notes),
        use_container_width=True,
        hide_index=True,
    )

with tabs[3]:
    st.caption(
        "Edit `sample_data/veteran_model_v1/veteran_manual_overrides.csv` and add a "
        "matching `veteran_audit_notes.csv` row with `affects_score=true`. The app "
        "will not accept score changes without that audit trail."
    )
    overrides = pd.DataFrame(board.manual_overrides)
    if overrides.empty:
        st.dataframe(
            pd.DataFrame(board.override_template_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.data_editor(
            overrides,
            use_container_width=True,
            hide_index=True,
            disabled=True,
        )

with tabs[4]:
    st.info(
        "This tab is the waiting-room for real source data. It does not change "
        "keeper, drop, trade, or release scores. Raw source rows only become useful "
        "after they are normalized into veteran feature scores and the model is "
        "regenerated."
    )
    left, middle, right = st.columns(3)
    left.metric("Source Intake", public_report.status.upper())
    middle.metric("Source Issues", len(public_report.issues))
    right.metric("Unscored Players", len(unscored_players))

    st.subheader("Readiness Checklist")
    st.dataframe(
        pd.DataFrame(
            public_source_readiness_rows(
                public_report,
                public_matches,
                unscored_players,
                model_input_candidate_root,
                model_preview_root,
                model_promotion_root,
                model_applied_pack_root,
                data_pack_path=active_data_pack,
            )
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Snapshot Workflow")
    st.caption(
        "Create a dated local copy of the current public-source files before any "
        "normalization or scoring work. Snapshots are raw evidence backups only."
    )
    snapshot_id = st.text_input(
        "Snapshot id",
        value="",
        placeholder="Optional; blank creates a timestamped id",
    )
    if st.button("Create Public Source Snapshot"):
        result = create_public_source_snapshot(
            public_source_root,
            public_snapshot_root,
            snapshot_id=snapshot_id or None,
        )
        if result.created:
            st.success(f"{result.message} `{result.snapshot_path}`")
        else:
            st.error(f"{result.message} `{result.snapshot_path}`")
    st.dataframe(
        pd.DataFrame(public_source_snapshot_rows(public_snapshot_root)),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("V1 Source Policy Lock")
    st.caption(
        "Approved sources can enter the import lane. Rejected sources may be "
        "manual context only and cannot become required machine-ingested inputs."
    )
    st.dataframe(
        pd.DataFrame(public_source_policy_rows()),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Source Domain Coverage")
    st.dataframe(
        pd.DataFrame(public_source_domain_rows(public_matches)),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Player Match Review")
    st.caption(
        "Source rows must match a roster/player record by ID or an unambiguous "
        "normalized name before they are safe to normalize."
    )
    st.dataframe(
        pd.DataFrame(public_source_player_match_summary_rows(public_player_matches)),
        use_container_width=True,
        hide_index=True,
    )
    player_match_frame = pd.DataFrame(public_player_matches)
    if player_match_frame.empty:
        st.dataframe(player_match_frame, use_container_width=True, hide_index=True)
    else:
        st.dataframe(
            player_match_frame,
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Feature Normalization Readiness")
    st.caption(
        "This maps matched source evidence to active veteran features. "
        "It is a checklist for normalization work, not a scoring engine."
    )
    st.dataframe(
        pd.DataFrame(
            public_source_feature_readiness_summary_rows(public_feature_readiness)
        ),
        use_container_width=True,
        hide_index=True,
    )
    feature_readiness_frame = pd.DataFrame(public_feature_readiness)
    if feature_readiness_frame.empty:
        st.dataframe(
            feature_readiness_frame,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            feature_readiness_frame,
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Normalization Worklist")
    st.caption(
        "Generate a CSV checklist for feature-normalization work. This export "
        "does not write model inputs or update any score."
    )
    worklist_rows = public_source_normalization_worklist_rows(
        public_feature_readiness
    )
    if worklist_rows:
        st.dataframe(
            pd.DataFrame(worklist_rows)
            .groupby(["priority", "status"], as_index=False)
            .size()
            .rename(columns={"size": "rows"}),
            use_container_width=True,
            hide_index=True,
        )
    worklist_id = st.text_input(
        "Worklist id",
        value="",
        placeholder="Optional; blank creates a timestamped id",
    )
    if st.button("Create Normalization Worklist"):
        worklist_result = create_public_source_normalization_worklist(
            active_data_pack,
            public_source_root,
            veteran_feature_registry_path,
            normalization_worklist_root,
            worklist_id=worklist_id or None,
        )
        if worklist_result.created:
            st.success(f"{worklist_result.message} `{worklist_result.csv_path}`")
        else:
            st.error(f"{worklist_result.message} `{worklist_result.worklist_path}`")
    st.dataframe(
        pd.DataFrame(
            public_source_normalization_worklist_snapshot_rows(
                normalization_worklist_root
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(worklist_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Backfill Acceptance Gate")
    st.caption(
        "This checks whether normalized backfill rows are safe to carry into a "
        "later model-run input step. It does not run the model."
    )
    acceptance_rows = public_source_backfill_acceptance_rows(
        public_feature_readiness
    )
    if acceptance_rows:
        status_counts = {
            row["acceptance_status"]: sum(
                1
                for item in acceptance_rows
                if item.get("acceptance_status") == row["acceptance_status"]
            )
            for row in acceptance_rows
        }
        accepted_count = status_counts.get("accepted", 0)
        review_count = status_counts.get("review", 0)
        blocked_count = status_counts.get("blocked", 0)
        c1, c2, c3 = st.columns(3)
        c1.metric("Accepted", accepted_count)
        c2.metric("Review", review_count)
        c3.metric("Blocked", blocked_count)
    st.dataframe(
        pd.DataFrame(public_source_backfill_acceptance_summary_rows(acceptance_rows)),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(acceptance_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Model Input Candidate Export")
    st.caption(
        "Export accepted normalized backfill rows in veteran_feature_scores shape. "
        "This is still a candidate file; it does not overwrite live inputs or run scoring."
    )
    candidate_rows = public_source_model_input_candidate_rows(
        active_data_pack,
        acceptance_rows,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Candidate Rows", len(candidate_rows))
    c2.metric(
        "Candidate Players",
        len({str(row.get("player_id") or "") for row in candidate_rows}),
    )
    c3.metric(
        "Candidate Features",
        len({str(row.get("feature_name") or "") for row in candidate_rows}),
    )
    candidate_id = st.text_input(
        "Candidate id",
        value="",
        placeholder="Optional; blank creates a timestamped id",
    )
    if st.button("Create Model Input Candidate"):
        candidate_result = create_public_source_model_input_candidate(
            active_data_pack,
            public_source_root,
            veteran_feature_registry_path,
            model_input_candidate_root,
            candidate_id=candidate_id or None,
        )
        if candidate_result.created:
            st.success(f"{candidate_result.message} `{candidate_result.csv_path}`")
        else:
            st.error(
                f"{candidate_result.message} `{candidate_result.candidate_path}`"
            )
    st.dataframe(
        pd.DataFrame(
            public_source_model_input_candidate_snapshot_rows(
                model_input_candidate_root
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(candidate_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Model Input Candidate Validation")
    st.caption(
        "Validate candidate feature-score rows before any later isolated "
        "model-run preview consumes them."
    )
    candidate_validation_rows = public_source_model_input_candidate_validation_rows(
        active_data_pack,
        candidate_rows,
        veteran_feature_registry_path,
    )
    st.dataframe(
        pd.DataFrame(
            public_source_model_input_candidate_validation_summary_rows(
                candidate_validation_rows
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(candidate_validation_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Model Preview Coverage")
    st.caption(
        "Check whether each rostered player has accepted active feature rows "
        "before any later isolated model preview."
    )
    candidate_coverage_rows = public_source_model_input_candidate_coverage_rows(
        active_data_pack,
        candidate_rows,
        candidate_validation_rows,
        veteran_feature_registry_path,
    )
    st.dataframe(
        pd.DataFrame(
            public_source_model_input_candidate_coverage_summary_rows(
                candidate_coverage_rows
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(candidate_coverage_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Isolated Model Preview")
    st.caption(
        "Run the veteran model against complete accepted candidate rows in a "
        "separate preview folder. This does not overwrite live model outputs or "
        "change recommendations."
    )
    preview_id = st.text_input(
        "Preview id",
        value="",
        placeholder="Optional; blank creates a timestamped id",
    )
    if st.button("Create Isolated Model Preview"):
        preview_result = create_public_source_model_preview(
            active_data_pack,
            public_source_root,
            veteran_feature_registry_path,
            model_preview_root,
            preview_id=preview_id or None,
        )
        if preview_result.created:
            st.success(f"{preview_result.message} `{preview_result.output_path}`")
        else:
            st.error(f"{preview_result.message} `{preview_result.preview_path}`")
    st.dataframe(
        pd.DataFrame(public_source_model_preview_snapshot_rows(model_preview_root)),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Model Preview Review Gate")
    st.caption(
        "Review isolated preview outputs before any future promotion workflow. "
        "Ready here means safe to compare, not automatically safe to publish."
    )
    preview_review_rows = public_source_model_preview_review_rows(model_preview_root)
    st.dataframe(
        pd.DataFrame(
            public_source_model_preview_review_summary_rows(preview_review_rows)
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(preview_review_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Preview vs Live Comparison")
    st.caption(
        "Compare review-gated preview rows against the selected pack's current "
        "model outputs. This is still read-only and does not promote scores."
    )
    preview_comparison_rows = public_source_model_preview_comparison_rows(
        active_data_pack,
        model_preview_root,
    )
    st.dataframe(
        pd.DataFrame(
            public_source_model_preview_comparison_summary_rows(
                preview_comparison_rows
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(preview_comparison_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Promotion Candidate Export")
    st.caption(
        "Export only ready preview-vs-live rows into a candidate model_outputs "
        "CSV. This still does not overwrite the selected pack."
    )
    promotion_id = st.text_input(
        "Promotion candidate id",
        value="",
        placeholder="Optional; blank creates a timestamped id",
    )
    if st.button("Create Promotion Candidate"):
        promotion_result = create_public_source_model_promotion_candidate(
            active_data_pack,
            model_preview_root,
            model_promotion_root,
            promotion_id=promotion_id or None,
        )
        if promotion_result.created:
            st.success(f"{promotion_result.message} `{promotion_result.csv_path}`")
        else:
            st.error(
                f"{promotion_result.message} `{promotion_result.promotion_path}`"
            )
    st.dataframe(
        pd.DataFrame(
            public_source_model_promotion_candidate_snapshot_rows(
                model_promotion_root
            )
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Promotion Candidate Review Gate")
    st.caption(
        "Validate promotion candidates against the currently selected pack. "
        "This is still not an apply step."
    )
    promotion_review_rows = public_source_model_promotion_candidate_review_rows(
        active_data_pack,
        model_promotion_root,
    )
    st.dataframe(
        pd.DataFrame(
            public_source_model_promotion_candidate_review_summary_rows(
                promotion_review_rows
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(promotion_review_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Apply To New Data Pack")
    st.caption(
        "Apply ready promotion candidates into a new generated data-pack copy. "
        "The selected pack is never overwritten."
    )
    applied_pack_id = st.text_input(
        "Applied pack id",
        value="",
        placeholder="Optional; blank creates a timestamped id",
    )
    if st.button("Create Applied Data Pack Copy"):
        applied_result = create_public_source_model_applied_pack(
            active_data_pack,
            model_promotion_root,
            model_applied_pack_root,
            applied_pack_id=applied_pack_id or None,
        )
        if applied_result.created:
            st.success(f"{applied_result.message} `{applied_result.applied_pack_path}`")
        else:
            st.error(
                f"{applied_result.message} `{applied_result.applied_pack_path}`"
            )
    st.dataframe(
        pd.DataFrame(
            public_source_model_applied_pack_snapshot_rows(model_applied_pack_root)
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Applied Pack Admission Gate")
    st.caption(
        "Validate generated applied packs before selecting them elsewhere in "
        "the app."
    )
    applied_pack_review_rows = public_source_model_applied_pack_review_rows(
        model_applied_pack_root
    )
    st.dataframe(
        pd.DataFrame(
            public_source_model_applied_pack_review_summary_rows(
                applied_pack_review_rows
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(applied_pack_review_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Public Source File Coverage")
    st.dataframe(
        pd.DataFrame(public_source_count_rows(public_report)),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Player Match Coverage")
    match_frame = pd.DataFrame(public_matches)
    if match_frame.empty:
        st.dataframe(match_frame, use_container_width=True, hide_index=True)
    else:
        st.dataframe(
            match_frame[
                [
                    "player_name",
                    "position",
                    "team_name",
                    "matched_sources",
                    "missing_sources",
                    "projection_match",
                    "market_match",
                    "role_match",
                    "injury_match",
                    "bio_match",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    st.subheader("Unscored Player Report")
    st.caption(
        "A placeholder row means the player has roster/rank inventory, but not a "
        "real model recommendation yet."
    )
    st.dataframe(
        pd.DataFrame(unscored_players),
        use_container_width=True,
        hide_index=True,
    )
    issue_rows = public_source_issue_rows(public_report)
    if issue_rows:
        st.subheader("Public Source Issues")
        st.dataframe(pd.DataFrame(issue_rows), use_container_width=True, hide_index=True)

with tabs[5]:
    st.info(
        "This is the stats-first model lane. It can create previews and copied "
        "applied packs, but it never overwrites the selected pack. A copied pack "
        "still has to pass Import Review before it is decision-ready."
    )
    stat_cols = st.columns(3)
    stat_cols[0].metric(
        "Normalized File",
        "present" if Path(stats_first_normalized_feature_path).exists() else "missing",
    )
    stat_cols[1].metric(
        "Preview Root",
        "present" if Path(stats_first_preview_root).exists() else "empty",
    )
    stat_cols[2].metric(
        "Applied Root",
        "present" if Path(stats_first_applied_pack_root).exists() else "empty",
    )

    st.subheader("Verified nflverse Import Source")
    st.caption(
        "These are approved source contracts for local import. They do not score "
        "players until a transformed CSV is normalized, previewed, audited, and "
        "explicitly applied to a copied pack."
    )
    st.dataframe(
        pd.DataFrame(official_player_stats_source_rows()),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Create Stats-First Preview")
    st.caption(
        "Preview rows are scored from normalized football/stat features. Market "
        "does not enter private value. This writes isolated preview files only."
    )
    stats_preview_id = st.text_input(
        "Stats-first preview id",
        value="",
        placeholder="Optional; blank creates a timestamped id",
        key="stats_first_preview_id",
    )
    if st.button("Create Stats-First Preview", type="secondary"):
        preview_result = create_stats_first_model_preview(
            stats_first_normalized_feature_path,
            stats_first_preview_root,
            preview_id=stats_preview_id or None,
        )
        if preview_result.created:
            st.success(f"{preview_result.message} `{preview_result.output_path}`")
        else:
            st.error(f"{preview_result.message} `{preview_result.preview_path}`")

    st.subheader("Preview Review Gate")
    st.caption(
        "Ready means safe for the next comparison/apply review step. It does not "
        "mean the scores are live."
    )
    stats_preview_snapshots = stats_first_preview_snapshot_rows(stats_first_preview_root)
    st.dataframe(
        pd.DataFrame(stats_preview_snapshots),
        use_container_width=True,
        hide_index=True,
    )
    stats_preview_review_rows = stats_first_preview_review_rows(stats_first_preview_root)
    st.dataframe(
        pd.DataFrame(
            stats_first_preview_review_summary_rows(stats_preview_review_rows)
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(stats_preview_review_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Explicit Apply To Copied Pack")
    st.caption(
        "This creates a new data-pack copy and applies only preview rows marked "
        "`ready`. The active/source pack is not overwritten."
    )
    preview_options = [
        str(row.get("preview_id") or "")
        for row in stats_preview_snapshots
        if row.get("preview_id")
    ]
    selected_stats_preview = st.selectbox(
        "Preview to apply",
        preview_options or [""],
        key="stats_first_apply_preview_id",
    )
    stats_applied_pack_id = st.text_input(
        "Applied stats-first pack id",
        value="",
        placeholder="Optional; blank uses source pack + preview id",
        key="stats_first_applied_pack_id",
    )
    confirmation_text = st.text_input(
        "Confirmation phrase",
        value="",
        placeholder=STATS_FIRST_APPLY_CONFIRMATION,
        key="stats_first_apply_confirmation",
    )
    st.caption(f"Required phrase: `{STATS_FIRST_APPLY_CONFIRMATION}`")
    if st.button("Create Stats-First Applied Pack Copy", type="primary"):
        if not selected_stats_preview:
            st.warning("Create and select a stats-first preview first.")
        else:
            applied_result = create_stats_first_applied_pack(
                active_data_pack,
                stats_first_preview_root,
                stats_first_applied_pack_root,
                preview_id=selected_stats_preview,
                applied_pack_id=stats_applied_pack_id or None,
                confirmation_text=confirmation_text,
            )
            if applied_result.created:
                st.success(
                    f"{applied_result.message} `{applied_result.applied_pack_path}`"
                )
            else:
                st.error(
                    f"{applied_result.message} `{applied_result.applied_pack_path}`"
                )

    st.subheader("Applied Pack Review")
    st.caption(
        "After this, go to Import Review and select the copied pack. Only use it "
        "for decisions if admission says decision ready."
    )
    st.dataframe(
        pd.DataFrame(stats_first_applied_pack_snapshot_rows(stats_first_applied_pack_root)),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(stats_first_applied_pack_review_rows(stats_first_applied_pack_root)),
        use_container_width=True,
        hide_index=True,
    )

with tabs[6]:
    issue_frame = pd.DataFrame(board.issue_rows)
    if issue_frame.empty:
        st.success("No source, audit, or override validation issues.")
    else:
        st.dataframe(issue_frame, use_container_width=True, hide_index=True)
