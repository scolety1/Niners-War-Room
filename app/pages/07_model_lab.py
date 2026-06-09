from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.trust_status import render_page_trust_banner
from src.config.settings import get_settings
from src.services.data_pack_health_service import (
    build_data_pack_health_report,
    readiness_status_rows,
)
from src.services.final_calibration_gate_service import (
    build_final_calibration_gate,
    final_calibration_gate_rows,
    final_calibration_gate_summary_row,
)
from src.services.lifecycle_audit_service import build_lifecycle_audit
from src.services.lifecycle_receipt_drilldown_service import (
    build_lifecycle_receipt_drilldown,
)
from src.services.model_audit_worklist_service import build_model_audit_worklist
from src.services.model_outlier_service import build_model_outlier_report
from src.services.model_recalibration_service import model_recalibration_policy
from src.services.model_v4_app_review_service import (
    DEFAULT_MODEL_V4_NAMED_PATH,
    DEFAULT_MODEL_V4_PREVIEW_ROOT,
    DEFAULT_MODEL_V4_SANITY_PATH,
    build_model_v4_app_review,
)
from src.services.named_player_audit_service import build_named_player_audit
from src.services.player_comparison_service import (
    build_player_compare_options,
    compare_players,
)
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    build_player_feature_receipts,
)
from src.services.pre_decision_checklist_service import (
    build_pre_decision_checklist,
    pre_decision_checklist_rows,
    pre_decision_checklist_summary_row,
)
from src.services.ranking_audit_service import (
    build_ranking_audit,
    ranking_audit_summary_rows,
)
from src.services.ranking_readiness_service import ranking_readiness_from_calibration
from src.services.roster_decision_readiness_service import (
    build_roster_decision_readiness,
    roster_decision_gate_rows,
    roster_decision_summary_row,
)
from src.services.route_participation_gap_gate_service import (
    build_route_participation_gap_gate_report,
)
from src.services.source_coverage_audit_service import build_source_coverage_audit
from src.services.young_player_review_service import build_young_player_review

MODEL_V4_PREVIEW_REVIEW_ONLY_LABEL = "Review-only v4 preview. Not active rankings."
MODEL_V4_PREVIEW_RANKING_COLUMNS = (
    "overall_preview_rank",
    "position_preview_rank",
    "player",
    "position",
    "nfl_team",
    "lifecycle",
    "dynasty_asset_value",
    "confidence_label",
    "review_warnings",
    "unavailable_sections",
)
MODEL_V4_PREVIEW_RANKING_LABELS = {
    "overall_preview_rank": "Overall Preview Rank",
    "position_preview_rank": "Position Preview Rank",
    "player": "Player",
    "position": "Position",
    "nfl_team": "NFL Team",
    "lifecycle": "Lifecycle",
    "dynasty_asset_value": "Dynasty Asset Value",
    "confidence_label": "Confidence Label",
    "review_warnings": "Review Warnings",
    "unavailable_sections": "Unavailable Sections",
}
MODEL_V4_RECEIPT_SECTION_LABELS = {
    "production": "Production",
    "first_down_scoring_fit": "First-Down Scoring Fit",
    "usage_opportunity": "Usage / Opportunity",
    "snap_proxy_role": "Snap / Proxy Role",
    "projection": "Projection",
    "age_dropoff": "Age / Dropoff",
    "young_player_prior": "Young-Player Prior",
    "confidence": "Confidence",
}
MODEL_V4_RECEIPT_SECTION_ORDER = tuple(MODEL_V4_RECEIPT_SECTION_LABELS)
MODEL_V4_SOURCE_GAP_CATEGORY_LABELS = {
    "critical_missing_evidence": "Critical Missing Evidence",
    "proxy_only_evidence": "Proxy-Only Evidence",
    "projection_gap": "Projection Gap",
    "first_down_projection_gap": "First-Down Projection Gap",
    "route_data_unavailable": "Route Data Unavailable",
    "not_applicable": "Not Applicable",
    "covered_evidence": "Covered Evidence",
}
MODEL_V4_SOURCE_GAP_CATEGORY_ORDER = tuple(MODEL_V4_SOURCE_GAP_CATEGORY_LABELS)


def _model_v4_source_gap_rows(
    source_coverage_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in source_coverage_rows:
        categories = _model_v4_source_gap_categories(row)
        rows.append(
            {
                "player": row.get("player", ""),
                "position": row.get("position", ""),
                "component": row.get("section", ""),
                "coverage_status": row.get("coverage_status", ""),
                "source_status": row.get("source_status", ""),
                "warning": row.get("warning", ""),
                "unavailable_reason": row.get("unavailable_reason", ""),
                "gap_categories": "|".join(categories),
                "gap_labels": ", ".join(
                    MODEL_V4_SOURCE_GAP_CATEGORY_LABELS.get(category, category)
                    for category in categories
                ),
                "gap_explanation": _model_v4_source_gap_explanation(categories),
                "is_data_failure": any(
                    category
                    in {
                        "critical_missing_evidence",
                        "projection_gap",
                        "first_down_projection_gap",
                        "route_data_unavailable",
                    }
                    for category in categories
                ),
            }
        )
    return rows


def _model_v4_source_gap_summary_rows(
    source_gap_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    summary: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in source_gap_rows:
        categories = str(row.get("gap_categories") or "").split("|")
        for category in categories:
            if not category:
                continue
            key = (
                category,
                str(row.get("component") or ""),
                str(row.get("position") or ""),
            )
            output = summary.setdefault(
                key,
                {
                    "gap_category": category,
                    "gap_label": MODEL_V4_SOURCE_GAP_CATEGORY_LABELS.get(
                        category, category
                    ),
                    "component": row.get("component", ""),
                    "position": row.get("position", ""),
                    "row_count": 0,
                    "is_failure": category
                    in {
                        "critical_missing_evidence",
                        "projection_gap",
                        "first_down_projection_gap",
                        "route_data_unavailable",
                    },
                },
            )
            output["row_count"] = int(output["row_count"]) + 1
    return sorted(
        summary.values(),
        key=lambda row: (
            _model_v4_category_sort_order(str(row["gap_category"])),
            str(row["component"]),
            str(row["position"]),
        ),
    )


def _model_v4_source_gap_categories(row: dict[str, str]) -> tuple[str, ...]:
    text = "|".join(
        str(row.get(key) or "")
        for key in (
            "section",
            "source_status",
            "coverage_status",
            "warning",
            "unavailable_reason",
        )
    ).lower()
    source_status = str(row.get("source_status") or "").lower()
    coverage_status = str(row.get("coverage_status") or "").lower()
    section = str(row.get("section") or "").lower()
    if source_status == "not_applicable" or "not_applicable" in text:
        return ("not_applicable",)

    categories: list[str] = []
    if "snap_share_proxy_only_not_route_participation" in text or "proxy_only" in text:
        categories.extend(["proxy_only_evidence", "route_data_unavailable"])
    if "route_data_unavailable" in text or "route participation" in text:
        categories.append("route_data_unavailable")
    if "missing_first_down_projection" in text or "projection_first_downs_missing" in text:
        categories.append("first_down_projection_gap")
    if section == "projection" and (
        "missing_projection" in text
        or "local_baseline_projection" in text
        or coverage_status == "missing"
    ):
        categories.append("projection_gap")
    if (
        coverage_status == "missing"
        or source_status == "missing"
        or str(row.get("unavailable_reason") or "").strip()
    ) and not categories:
        categories.append("critical_missing_evidence")
    if not categories:
        categories.append("covered_evidence")
    return tuple(dict.fromkeys(categories))


def _model_v4_source_gap_explanation(categories: tuple[str, ...]) -> str:
    if categories == ("not_applicable",):
        return "This section does not apply to the player or lifecycle."
    if categories == ("covered_evidence",):
        return "This section has usable review-only evidence."
    explanations = {
        "critical_missing_evidence": "A required evidence section is missing.",
        "proxy_only_evidence": "The model has proxy evidence, not the preferred direct field.",
        "projection_gap": "Projection evidence is missing or only baseline/review quality.",
        "first_down_projection_gap": (
            "Projection rows do not include direct first-down projections."
        ),
        "route_data_unavailable": (
            "Route participation metrics are not available from safe free sources."
        ),
    }
    return " ".join(
        explanations[category]
        for category in categories
        if category in explanations
    )


def _model_v4_category_sort_order(category: str) -> int:
    try:
        return MODEL_V4_SOURCE_GAP_CATEGORY_ORDER.index(category)
    except ValueError:
        return len(MODEL_V4_SOURCE_GAP_CATEGORY_ORDER)


def _model_v4_audit_status_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = {"ready": 0, "review": 0, "blocked": 0}
    if frame.empty:
        return counts
    for status in frame["audit_status"].fillna("review").astype(str):
        counts[status if status in counts else "review"] += 1
    return counts


def _model_v4_fixture_audit_status(status: object) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"ready", "pass", "passed"}:
        return "ready"
    if normalized in {"blocked", "blocked_missing_input", "missing_input"}:
        return "blocked"
    return "review"


def _model_v4_named_audit_status(row: pd.Series) -> str:
    match_status = str(row.get("match_status") or "").strip().lower()
    confidence = str(row.get("confidence_label") or "").strip().lower()
    review_notes = str(row.get("review_notes") or "").lower()
    if match_status not in {"matched", "ready"}:
        return "blocked"
    if confidence in {"weak", "review", "blocked"} or "weak confidence" in review_notes:
        return "review"
    return "ready"


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


@st.cache_data
def _load_outliers(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_model_outlier_report(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_worklist(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_model_audit_worklist(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_receipts(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_player_feature_receipts(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_compare_options(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_player_compare_options(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_player_compare(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
    player_a: str,
    player_b: str,
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return compare_players(
        active_data_pack,
        player_a,
        player_b,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_source_coverage(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_source_coverage_audit(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_ranking_audit(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint
    return build_ranking_audit(active_data_pack)


@st.cache_data
def _load_lifecycle_audit(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_lifecycle_audit(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_young_player_review(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_young_player_review(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_roster_decision_readiness(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_roster_decision_readiness(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_named_player_audit(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_named_player_audit(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_pre_decision_checklist(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_pre_decision_checklist(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_route_participation_gap_gate(
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = veteran_model_fingerprint
    return build_route_participation_gap_gate_report(veteran_model_dir)


@st.cache_data
def _load_model_v4_app_review(
    preview_fingerprint: tuple[str, int, int, int],
    sanity_fingerprint: tuple[str, int, int, int],
    named_fingerprint: tuple[str, int, int, int],
):
    _ = preview_fingerprint, sanity_fingerprint, named_fingerprint
    return build_model_v4_app_review()


def _selected_dataframe_rows(event: object) -> list[int]:
    try:
        selection = getattr(event, "selection", None)
        if selection is not None:
            rows = getattr(selection, "rows", None)
            if rows is not None:
                return [int(row) for row in rows]
        if isinstance(event, dict):
            rows = event.get("selection", {}).get("rows", [])
            return [int(row) for row in rows]
    except (TypeError, ValueError):
        return []
    return []


def _format_metric(value: object) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value or "")


def _model_v4_receipt_drilldown_rows(
    selected_row: dict[str, object],
    receipt_rows: list[dict[str, str]],
) -> pd.DataFrame:
    player = str(selected_row.get("player") or "")
    expected_contributions = _json_dict(
        str(selected_row.get("component_contributions") or "{}")
    )
    rows: list[dict[str, object]] = []
    for row in receipt_rows:
        if str(row.get("player") or "") != player:
            continue
        component = str(row.get("component") or "")
        contribution = _to_float(row.get("contribution")) or 0.0
        expected = _to_float(expected_contributions.get(component))
        delta = 0.0 if expected is None else contribution - expected
        rows.append(
            {
                **row,
                "receipt_group": MODEL_V4_RECEIPT_SECTION_LABELS.get(
                    component,
                    component.replace("_", " ").title(),
                ),
                "audit_highlight": _model_v4_receipt_highlight(row),
                "expected_component_contribution": (
                    "" if expected is None else round(expected, 3)
                ),
                "contribution_delta": round(delta, 3),
                "reconciles_preview_contribution": abs(delta) <= 0.01,
                "receipt_sort_order": _model_v4_receipt_sort_order(component),
            }
        )
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    return frame.sort_values(["receipt_sort_order", "component"]).reset_index(drop=True)


def _json_dict(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _to_float(value: object) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _model_v4_receipt_highlight(row: dict[str, str]) -> str:
    text = "|".join(
        str(row.get(key) or "")
        for key in ("source_status", "warning", "unavailable_reason")
    ).lower()
    highlights: list[str] = []
    if "missing_first_down_projection" in text or "projection_first_downs_missing" in text:
        highlights.append("missing first-down projection")
    if "snap_share_proxy_only_not_route_participation" in text:
        highlights.append("proxy-only snap role")
    if "local_baseline_projection" in text:
        highlights.append("local baseline projection")
    if "young_player_prior_review_only" in text:
        highlights.append("young prior review-only")
    if "missing" in text or str(row.get("unavailable_reason") or "").strip():
        highlights.append("missing source section")
    return "; ".join(dict.fromkeys(highlights))


def _model_v4_receipt_sort_order(component: str) -> int:
    try:
        return MODEL_V4_RECEIPT_SECTION_ORDER.index(component)
    except ValueError:
        return len(MODEL_V4_RECEIPT_SECTION_ORDER)


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
veteran_model_dir = str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR)
veteran_model_fingerprint = path_fingerprint(DEFAULT_RECEIPT_VETERAN_MODEL_DIR)
model_v4_review = _load_model_v4_app_review(
    path_fingerprint(DEFAULT_MODEL_V4_PREVIEW_ROOT),
    path_fingerprint(DEFAULT_MODEL_V4_SANITY_PATH),
    path_fingerprint(DEFAULT_MODEL_V4_NAMED_PATH),
)
health = _load_health(active_data_pack, active_fingerprint)
policy = model_recalibration_policy()
calibration_report = build_final_calibration_gate(active_data_pack)
ranking_readiness = ranking_readiness_from_calibration(calibration_report)
outlier_report = _load_outliers(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
worklist_report = _load_worklist(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
receipt_report = _load_receipts(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
compare_options = _load_compare_options(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
coverage_report = _load_source_coverage(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
route_participation_gap = _load_route_participation_gap_gate(
    veteran_model_dir,
    veteran_model_fingerprint,
)
ranking_audit = _load_ranking_audit(active_data_pack, active_fingerprint)
lifecycle_audit = _load_lifecycle_audit(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
young_player_review = _load_young_player_review(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
roster_readiness = _load_roster_decision_readiness(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
named_player_audit = _load_named_player_audit(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)
pre_decision_checklist = _load_pre_decision_checklist(
    active_data_pack,
    active_fingerprint,
    veteran_model_dir,
    veteran_model_fingerprint,
)

st.title("Model Lab")
st.caption("Advanced model audit, source import, rookie sandbox, and historical replay tools.")
render_page_trust_banner(
    health,
    calibration_passed=calibration_report.passed,
    review_only_message=ranking_readiness.message if ranking_readiness.review_only else "",
    review_only_detail=(
        "Model Lab is an audit workbench. Use it to inspect blockers, source coverage, "
        "outliers, lifecycle handling, and calibration before trusting rankings."
    )
    if ranking_readiness.review_only
    else "",
)

readiness = {
    row["status_area"]: row["status"]
    for row in readiness_status_rows(
        health,
        calibration_passed=calibration_report.passed,
    )
}
left, middle, right = st.columns(3)
left.metric("Data", readiness["data_ready"])
middle.metric("Model", readiness["model_ready"])
right.metric("Decision", readiness["decision_ready"])

st.subheader("Decision Gate")
gate_overview_frame = pd.DataFrame(final_calibration_gate_rows(calibration_report))
blocking_gate_rows = gate_overview_frame[
    gate_overview_frame["status"].astype(str) != "ready"
]
if calibration_report.passed:
    st.success("Decision gates are clear.")
elif blocking_gate_rows.empty:
    st.warning("Decision gates need review.")
else:
    st.warning("Decision gates are blocking or need review.")
    st.dataframe(
        blocking_gate_rows.reindex(
            columns=[
                "requirement",
                "status",
                "blocker",
                "why_it_matters",
                "next_action",
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
with st.expander("Full checklist and gate summaries"):
    st.dataframe(
        pd.DataFrame([pre_decision_checklist_summary_row(pre_decision_checklist)]),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame([final_calibration_gate_summary_row(calibration_report)]),
        use_container_width=True,
        hide_index=True,
    )

(
    decision_gate_tab,
    player_audit_tab,
    source_coverage_tab,
    outliers_tab,
    lifecycle_workbench_tab,
    imports_sources_tab,
    model_v4_tab,
    calibration_tab,
) = st.tabs(
    [
        "Decision Gate",
        "Player Audit",
        "Source Coverage",
        "Outliers",
        "Lifecycle",
        "Imports/Sources",
        "Model v4 Preview",
        "Calibration",
    ]
)

checklist_tab = decision_gate_tab
worklist_tab = decision_gate_tab
gate_tab = decision_gate_tab
roster_tab = decision_gate_tab
lifecycle_tab = lifecycle_workbench_tab
young_player_tab = lifecycle_workbench_tab
named_audit_tab = player_audit_tab
receipt_tab = player_audit_tab
compare_tab = player_audit_tab
coverage_tab = source_coverage_tab
outlier_tab = outliers_tab
ranking_tab = player_audit_tab
tool_tab = imports_sources_tab

with checklist_tab:
    st.subheader("Final Pre-Decision Checklist")
    st.caption(
        "One screen for what remains before roster, draft, and final money decisions "
        "can be trusted. This does not change rankings or unlock decision-ready labels."
    )
    if pre_decision_checklist.final_money_ready:
        st.success("All final money-decision gates are clear.")
    elif pre_decision_checklist.roster_decisions_ready:
        st.warning(
            "Roster decisions are clear, but draft/final money decisions still have "
            "remaining gates."
        )
    elif pre_decision_checklist.status == "blocked":
        st.error("Roster decisions still have blocking checks.")
    else:
        st.warning("Roster decisions still need review.")

    status_cols = st.columns(3)
    status_cols[0].metric(
        "Roster Decision Status",
        pre_decision_checklist.roster_decision_badge,
    )
    status_cols[1].metric("Draft Status", pre_decision_checklist.draft_badge)
    status_cols[2].metric(
        "Final Money Status",
        pre_decision_checklist.final_money_badge,
    )
    checklist_frame = pd.DataFrame(
        pre_decision_checklist_rows(pre_decision_checklist)
    )
    with st.expander("Checklist rows"):
        summary_frame = pd.DataFrame([pre_decision_checklist_summary_row(pre_decision_checklist)])
        summary_frame = summary_frame.rename(
            columns={
                "Roster Decisions Ready": "Roster Decision Status",
                "Draft Ready": "Draft Status",
                "Final Money Decisions Ready": "Final Money Status",
            }
        )
        st.dataframe(
            summary_frame,
            use_container_width=True,
            hide_index=True,
        )
        st.dataframe(
            checklist_frame,
            use_container_width=True,
            hide_index=True,
        )

with worklist_tab:
    st.subheader("Model Trust Worklist")
    st.caption(
        "This is the shortest path to a trustworthy model: fix blockers first, then "
        "review suspicious rankings. It does not change any score."
    )
    if worklist_report.issues:
        for issue in worklist_report.issues:
            st.warning(issue)
    st.dataframe(
        pd.DataFrame(worklist_report.summary_rows),
        use_container_width=True,
        hide_index=True,
    )
    worklist_frame = pd.DataFrame(worklist_report.rows)
    if worklist_frame.empty:
        st.success("No trust worklist items remain.")
    else:
        priorities = sorted(worklist_frame["priority"].dropna().unique())
        areas = sorted(worklist_frame["area"].dropna().unique())
        filter_cols = st.columns(3)
        selected_priorities = filter_cols[0].multiselect(
            "Priority",
            priorities,
            default=priorities,
        )
        selected_areas = filter_cols[1].multiselect("Area", areas, default=areas)
        player_search = filter_cols[2].text_input("Search Worklist", "")
        filtered_worklist = worklist_frame[
            worklist_frame["priority"].isin(selected_priorities)
            & worklist_frame["area"].isin(selected_areas)
            & (
                worklist_frame["player"].str.contains(player_search, case=False, na=False)
                | worklist_frame["item"].str.contains(player_search, case=False, na=False)
                | worklist_frame["detail"].str.contains(player_search, case=False, na=False)
            )
        ]
        with st.expander("Worklist rows"):
            st.dataframe(filtered_worklist, use_container_width=True, hide_index=True)

with gate_tab:
    st.subheader("Final Calibration Gate")
    if calibration_report.passed:
        st.success(f"**{calibration_report.badge}.** Decision-ready status may be restored.")
    elif calibration_report.status == "review":
        st.warning(
            f"**{calibration_report.badge}.** Rankings remain review-only while the "
            "remaining warning gates are checked."
        )
    else:
        st.error(
            f"**{calibration_report.badge}.** Rankings remain review-only until these "
            "checks pass."
        )
    gate_frame = pd.DataFrame(final_calibration_gate_rows(calibration_report))
    gate_display_columns = [
        "requirement",
        "status",
        "severity",
        "blocker",
        "why_it_matters",
        "detail",
        "next_action",
    ]
    gate_blockers = gate_frame[gate_frame["status"].astype(str) != "ready"]
    if not gate_blockers.empty:
        st.dataframe(
            gate_blockers.reindex(columns=gate_display_columns),
            use_container_width=True,
            hide_index=True,
        )
    with st.expander("Full gate rows"):
        st.dataframe(
            pd.DataFrame([final_calibration_gate_summary_row(calibration_report)]),
            use_container_width=True,
            hide_index=True,
        )
        st.dataframe(
            gate_frame.reindex(columns=gate_display_columns),
            use_container_width=True,
            hide_index=True,
        )

with roster_tab:
    st.subheader("Roster Decisions Readiness")
    st.caption(
        "This is the pre-declaration gate for keep, shop, and forced-release review. "
        "It is intentionally separate from final draft-day readiness, so missing "
        "released veterans do not block roster decisions."
    )
    if roster_readiness.passed:
        st.success(
            "Roster-declaration decisions are ready for review. Final draft readiness "
            "still waits on draft-pool gates."
        )
    elif roster_readiness.status == "blocked":
        st.error("Roster-declaration decisions need data before they can be trusted.")
    else:
        st.warning("Roster-declaration decisions need review before they can be trusted.")
    with st.expander("Roster decision gate rows"):
        st.dataframe(
            pd.DataFrame([roster_decision_summary_row(roster_readiness)]),
            use_container_width=True,
            hide_index=True,
        )
        st.dataframe(
            pd.DataFrame(roster_decision_gate_rows(roster_readiness)),
            use_container_width=True,
            hide_index=True,
        )

with lifecycle_tab:
    st.subheader("Lifecycle Audit")
    st.caption(
        "This checks whether players are in the right scoring lane: incoming rookies "
        "on rookie inputs, young NFL players on bridge receipts, established veterans "
        "on stats-first receipts, and draftable players with explicit availability labels."
    )
    if lifecycle_audit.issues:
        for issue in lifecycle_audit.issues:
            st.warning(issue)
    if lifecycle_audit.has_blockers:
        st.error(
            "Lifecycle blockers are present. Rankings stay review-only until these "
            "players are separated and audited."
        )
    else:
        st.success("No lifecycle blockers are currently flagged.")
    st.dataframe(
        pd.DataFrame(lifecycle_audit.count_rows),
        use_container_width=True,
        hide_index=True,
    )

    suspicious_frame = pd.DataFrame(lifecycle_audit.suspicious_rows)
    if suspicious_frame.empty:
        st.info("No suspicious lifecycle assignments are currently flagged.")
    else:
        st.markdown("**Suspicious Lifecycle Assignments**")
        warning_types = sorted(suspicious_frame["warning_type"].dropna().unique())
        selected_warnings = st.multiselect(
            "Warning",
            warning_types,
            default=warning_types,
            key="lifecycle_warning_filter",
        )
        suspicious_filtered = suspicious_frame[
            suspicious_frame["warning_type"].isin(selected_warnings)
        ]
        st.dataframe(
            suspicious_filtered,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("**Focused Receipt Drilldown**")
    drilldown_players = []
    if not suspicious_frame.empty and "player" in suspicious_frame:
        drilldown_players.extend(
            str(player)
            for player in suspicious_frame["player"].dropna().unique()
            if str(player)
        )
    drilldown_players.extend(
        player for player in receipt_report.players if player not in drilldown_players
    )
    if not drilldown_players:
        st.info("No receipt players are available for lifecycle drilldown.")
    else:
        selected_receipt_player = st.selectbox(
            "Player Receipt",
            drilldown_players,
            key="lifecycle_receipt_drilldown_player",
        )
        drilldown = build_lifecycle_receipt_drilldown(
            receipt_report,
            selected_receipt_player,
        )
        if drilldown.issues:
            for issue in drilldown.issues:
                st.warning(issue)
        else:
            st.info(drilldown.lifecycle_explanation)
            st.dataframe(
                pd.DataFrame(drilldown.section_rows),
                use_container_width=True,
                hide_index=True,
            )
            if drilldown.bridge_rows:
                st.markdown("**Young-Player Bridge Prior**")
                st.dataframe(
                    pd.DataFrame(drilldown.bridge_rows),
                    use_container_width=True,
                    hide_index=True,
                )
            elif drilldown.lifecycle_label == "Established Veteran":
                st.caption("Draft capital not scored for established veterans.")
            st.markdown("**Component Reconciliation**")
            st.dataframe(
                pd.DataFrame(drilldown.component_reconciliation_rows),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Receipt Rows"):
                receipt_columns = [
                    "receipt_section_label",
                    "component",
                    "formula_feature_name",
                    "raw_feature_value",
                    "normalized_score",
                    "feature_weight",
                    "contribution",
                    "source_file",
                    "warning_reason",
                    "imputed_flag",
                ]
                st.dataframe(
                    pd.DataFrame(drilldown.receipt_rows).reindex(columns=receipt_columns),
                    use_container_width=True,
                    hide_index=True,
                )

    player_frame = pd.DataFrame(lifecycle_audit.player_rows)
    if player_frame.empty:
        st.info("No lifecycle player rows are available.")
    else:
        with st.expander("All lifecycle rows"):
            filter_cols = st.columns(4)
            lifecycles = sorted(player_frame["asset_lifecycle_label"].dropna().unique())
            positions = sorted(player_frame["position"].dropna().unique())
            teams = sorted(player_frame["team"].dropna().unique())
            source_areas = sorted(player_frame["source_area"].dropna().unique())
            selected_lifecycles = filter_cols[0].multiselect(
                "Lifecycle",
                lifecycles,
                default=lifecycles,
                key="lifecycle_filter",
            )
            selected_positions = filter_cols[1].multiselect(
                "Position",
                positions,
                default=positions,
                key="lifecycle_position_filter",
            )
            selected_teams = filter_cols[2].multiselect(
                "Team",
                teams,
                default=teams,
                key="lifecycle_team_filter",
            )
            selected_source_areas = filter_cols[3].multiselect(
                "Source Area",
                source_areas,
                default=source_areas,
                key="lifecycle_source_area_filter",
            )
            warning_only = st.checkbox("Warnings only", value=False)
            filtered_lifecycle = player_frame[
                player_frame["asset_lifecycle_label"].isin(selected_lifecycles)
                & player_frame["position"].isin(selected_positions)
                & player_frame["team"].isin(selected_teams)
                & player_frame["source_area"].isin(selected_source_areas)
            ]
            if warning_only:
                filtered_lifecycle = filtered_lifecycle[
                    filtered_lifecycle["warning"].astype(str) != ""
                ]
            display_columns = [
                "source_area",
                "player",
                "position",
                "team",
                "asset_type",
                "asset_lifecycle_label",
                "warning",
                "has_bridge_prior_receipts",
                "has_draft_capital_prior_scored",
                "receipt_hint",
            ]
            st.dataframe(
                filtered_lifecycle.reindex(columns=display_columns),
                use_container_width=True,
                hide_index=True,
            )

with young_player_tab:
    st.subheader("Young Player Review")
    st.caption(
        "Year-one, year-two, and year-three NFL players get extra review because "
        "draft/prospect prior can still matter, but it must be checked against real "
        "NFL evidence. This tab does not tune weights or change scores."
    )
    if young_player_review.issues:
        for issue in young_player_review.issues:
            st.warning(issue)
    st.dataframe(
        pd.DataFrame(young_player_review.summary_rows),
        use_container_width=True,
        hide_index=True,
    )
    young_frame = pd.DataFrame(young_player_review.rows)
    if young_frame.empty:
        st.info("No year-one, year-two, or year-three NFL players are available for review.")
    else:
        filter_cols = st.columns(4)
        positions = sorted(young_frame["position"].dropna().unique())
        buckets = sorted(young_frame["experience_bucket"].dropna().unique())
        teams = sorted(young_frame["nfl_team"].dropna().unique())
        flag_values = sorted(
            {
                flag
                for flags in young_frame["flags"].dropna()
                for flag in str(flags).split("|")
                if flag
            }
        )
        selected_positions = filter_cols[0].multiselect(
            "Position",
            positions,
            default=positions,
            key="young_review_position_filter",
        )
        selected_buckets = filter_cols[1].multiselect(
            "Experience",
            buckets,
            default=buckets,
            key="young_review_bucket_filter",
        )
        selected_teams = filter_cols[2].multiselect(
            "NFL Team",
            teams,
            default=teams,
            key="young_review_team_filter",
        )
        selected_flags = filter_cols[3].multiselect(
            "Flag",
            flag_values,
            default=flag_values,
            key="young_review_flag_filter",
        )
        flagged_only = st.checkbox(
            "Flagged only",
            value=True,
            key="young_review_flagged_only",
        )
        filtered_young = young_frame[
            young_frame["position"].isin(selected_positions)
            & young_frame["experience_bucket"].isin(selected_buckets)
            & young_frame["nfl_team"].isin(selected_teams)
        ]
        if selected_flags:
            filtered_young = filtered_young[
                filtered_young["flags"].apply(
                    lambda value: any(
                        flag in selected_flags
                        for flag in str(value or "").split("|")
                        if flag
                    )
                    or (not str(value or "") and not flagged_only)
                )
            ]
        if flagged_only:
            filtered_young = filtered_young[
                filtered_young["flags"].astype(str) != ""
            ]
        young_columns = [
            "player",
            "position",
            "nfl_team",
            "draft_year",
            "draft_round",
            "draft_pick",
            "rookie_prior_score",
            "bridge_weight",
            "nfl_evidence_weight",
            "private_stat_value",
            "confidence",
            "warning",
            "flags",
            "next_action",
        ]
        with st.expander("Young player rows", expanded=True):
            st.dataframe(
                filtered_young.reindex(columns=young_columns),
                use_container_width=True,
                hide_index=True,
            )

        flag_frame = pd.DataFrame(young_player_review.flag_rows)
        if not flag_frame.empty:
            with st.expander("Flag Details"):
                st.dataframe(
                    flag_frame,
                    use_container_width=True,
                    hide_index=True,
                )

with named_audit_tab:
    st.subheader("Named Player Audit")
    st.caption(
        "Fast sanity checks for the player comparisons that are easiest to mistrust. "
        "This is audit-only: it explains the current output and does not tune weights."
    )
    if named_player_audit.issues:
        for issue in named_player_audit.issues:
            st.warning(issue)

    pair_frame = pd.DataFrame(named_player_audit.pair_rows)
    if pair_frame.empty:
        st.info("No named audit pairs are available.")
    else:
        st.markdown("**Quick Compare Pairs**")
        status_values = sorted(pair_frame["status"].dropna().unique())
        selected_statuses = st.multiselect(
            "Pair Status",
            status_values,
            default=status_values,
            key="named_audit_pair_status",
        )
        filtered_pairs = pair_frame[pair_frame["status"].isin(selected_statuses)]
        pair_columns = [
            "pair",
            "status",
            "player_a",
            "player_b",
            "leader",
            "private_gap_a_minus_b",
            "market_edge_gap_a_minus_b",
            "confidence_min",
            "top_gap_driver",
            "next_action",
        ]
        st.dataframe(
            filtered_pairs.reindex(columns=pair_columns),
            use_container_width=True,
            hide_index=True,
        )

        selected_pair = st.selectbox(
            "Pair Detail",
            list(pair_frame["pair"]),
            key="named_audit_pair_detail",
        )
        detail_frame = pd.DataFrame(
            [
                row
                for row in named_player_audit.pair_detail_rows
                if row["pair"] == selected_pair
            ]
        )
        if detail_frame.empty:
            st.info("One or both players are missing from this pair.")
        else:
            detail_columns = [
                "side",
                "player",
                "lifecycle",
                "rank",
                "position_rank",
                "private_stat_value",
                "market_value",
                "market_edge",
                "confidence",
                "warning",
                "top_receipt_contributions",
            ]
            st.dataframe(
                detail_frame.reindex(columns=detail_columns),
                use_container_width=True,
                hide_index=True,
            )

            receipt_frame = pd.DataFrame(
                [
                    row
                    for row in named_player_audit.receipt_rows
                    if row["pair"] == selected_pair
                ]
            )
            with st.expander("Top Receipt Contributions"):
                receipt_columns = [
                    "side",
                    "player",
                    "component",
                    "receipt_section",
                    "feature",
                    "raw_value",
                    "normalized_score",
                    "weight",
                    "contribution",
                    "source",
                    "warning",
                    "imputed",
                ]
                st.dataframe(
                    receipt_frame.reindex(columns=receipt_columns),
                    use_container_width=True,
                    hide_index=True,
                )

    player_frame = pd.DataFrame(named_player_audit.player_rows)
    if not player_frame.empty:
        st.markdown("**Player Search**")
        search = st.text_input("Search Player", "", key="named_audit_player_search")
        filtered_players = player_frame[
            player_frame["player"].str.contains(search, case=False, na=False)
        ]
        player_columns = [
            "rank",
            "position_rank",
            "player",
            "position",
            "team",
            "lifecycle",
            "private_stat_value",
            "market_value",
            "market_edge",
            "confidence",
            "warning",
            "top_receipt_contributions",
        ]
        st.dataframe(
            filtered_players.reindex(columns=player_columns),
            use_container_width=True,
            hide_index=True,
        )

with outlier_tab:
    st.subheader("Ranking Outliers")
    st.caption(
        "This is where suspicious rankings are sorted into likely data/model bugs "
        "versus possible market edges. Rankings stay review-only while high-severity "
        "outliers remain."
    )
    if outlier_report.issues:
        for issue in outlier_report.issues:
            st.warning(issue)
    st.dataframe(
        pd.DataFrame(outlier_report.bucket_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.dataframe(
        pd.DataFrame(outlier_report.summary_rows),
        use_container_width=True,
        hide_index=True,
    )
    if outlier_report.acceptance_summary_rows:
        st.markdown("**Outlier Acceptance Workflow**")
        st.caption(
            "Accepted outliers are audit status only. They do not change scores; "
            "they only tell the final gate that a weird ranking has been reviewed "
            "and intentionally tolerated."
        )
        st.dataframe(
            pd.DataFrame(outlier_report.acceptance_summary_rows),
            use_container_width=True,
            hide_index=True,
        )
        if outlier_report.invalid_acceptance_rows:
            st.error(
                "Some outlier acceptance rows are invalid and will not unblock "
                "the final gate."
            )
            st.dataframe(
                pd.DataFrame(outlier_report.invalid_acceptance_rows),
                use_container_width=True,
                hide_index=True,
            )
        if outlier_report.acceptance_rows:
            with st.expander("Accepted Outlier Rows"):
                st.dataframe(
                    pd.DataFrame(outlier_report.acceptance_rows),
                    use_container_width=True,
                    hide_index=True,
                )
    outlier_frame = pd.DataFrame(outlier_report.rows)
    if outlier_frame.empty:
        st.success("No model outliers are currently flagged.")
    else:
        buckets = sorted(outlier_frame["bucket"].dropna().unique())
        severities = sorted(outlier_frame["severity"].dropna().unique())
        outlier_types = sorted(outlier_frame["outlier_type"].dropna().unique())
        review_statuses = sorted(outlier_frame["review_status"].dropna().unique())
        acceptance_statuses = sorted(outlier_frame["acceptance_status"].dropna().unique())
        filter_cols = st.columns(5)
        selected_buckets = filter_cols[0].multiselect("Bucket", buckets, default=buckets)
        selected_severities = filter_cols[1].multiselect(
            "Severity",
            severities,
            default=severities,
        )
        selected_types = filter_cols[2].multiselect(
            "Outlier Type",
            outlier_types,
            default=outlier_types,
        )
        selected_statuses = filter_cols[3].multiselect(
            "Review Status",
            review_statuses,
            default=review_statuses,
        )
        selected_acceptance_statuses = filter_cols[4].multiselect(
            "Acceptance",
            acceptance_statuses,
            default=acceptance_statuses,
        )
        search = st.text_input("Search Player", "")
        filtered = outlier_frame[
            outlier_frame["bucket"].isin(selected_buckets)
            & outlier_frame["severity"].isin(selected_severities)
            & outlier_frame["outlier_type"].isin(selected_types)
            & outlier_frame["review_status"].isin(selected_statuses)
            & outlier_frame["acceptance_status"].isin(selected_acceptance_statuses)
            & outlier_frame["player"].str.contains(search, case=False, na=False)
        ]
        display_columns = [
            "bucket",
            "acceptance_status",
            "review_status",
            "next_action",
            "outlier_type",
            "severity",
            "player",
            "position",
            "team",
            "model_rank",
            "position_rank",
            "private_score",
            "trade_liquidity",
            "confidence_score",
            "component",
            "source_feature",
            "reason",
            "accepted_reason",
            "reviewed_by",
            "reviewed_at",
        ]
        with st.expander("Outlier rows", expanded=True):
            st.dataframe(
                filtered.reindex(columns=display_columns),
                use_container_width=True,
                hide_index=True,
            )

with receipt_tab:
    st.subheader("Player Feature Receipts")
    st.caption(
        "Use this when a ranking feels insane. It shows raw/normalized feature values, "
        "weights, source files, imputation, and contribution math."
    )
    if receipt_report.issues:
        for issue in receipt_report.issues:
            st.warning(issue)
    if not receipt_report.rows:
        st.info("No feature receipts are available yet.")
    else:
        selected_player = st.selectbox("Player", receipt_report.players)
        components = receipt_report.components
        selected_components = st.multiselect(
            "Component",
            components,
            default=components,
        )
        summary_frame = pd.DataFrame(
            [
                row
                for row in receipt_report.component_summary_rows
                if row["player"] == selected_player
                and row["component"] in selected_components
            ]
        )
        st.dataframe(summary_frame, use_container_width=True, hide_index=True)
        receipt_frame = pd.DataFrame(
            [
                row
                for row in receipt_report.rows
                if row["player"] == selected_player
                and row["component"] in selected_components
            ]
        )
        display_columns = [
            "component",
            "formula_feature_name",
            "source_feature_name",
            "raw_feature_value",
            "normalized_score",
            "feature_weight",
            "contribution",
            "component_score",
            "source_name",
            "source_date",
            "imputed_flag",
            "warning_reason",
        ]
        with st.expander("Receipt rows", expanded=True):
            st.dataframe(
                receipt_frame.reindex(columns=display_columns),
                use_container_width=True,
                hide_index=True,
            )

with compare_tab:
    st.subheader("Player Compare")
    st.caption(
        "Compare two players by stats value, trade liquidity, feature contributions, "
        "warnings, and market edge."
    )
    if len(compare_options) < 2:
        st.info("At least two scored players are needed for comparison.")
    else:
        label_lookup = {str(row["label"]): str(row["player_id"]) for row in compare_options}
        labels = list(label_lookup)
        compare_cols = st.columns(2)
        player_a_label = compare_cols[0].selectbox("Player A", labels, index=0)
        player_b_label = compare_cols[1].selectbox(
            "Player B",
            labels,
            index=1 if len(labels) > 1 else 0,
        )
        report = _load_player_compare(
            active_data_pack,
            active_fingerprint,
            veteran_model_dir,
            veteran_model_fingerprint,
            label_lookup[player_a_label],
            label_lookup[player_b_label],
        )
        if report.issues:
            for issue in report.issues:
                st.warning(issue)
        st.dataframe(pd.DataFrame(report.score_rows), use_container_width=True, hide_index=True)
        st.dataframe(
            pd.DataFrame(report.gap_driver_rows),
            use_container_width=True,
            hide_index=True,
        )
        with st.expander("All Feature Gaps"):
            st.dataframe(
                pd.DataFrame(report.feature_rows),
                use_container_width=True,
                hide_index=True,
            )
        with st.expander("Warnings And Market Edge"):
            st.dataframe(
                pd.DataFrame(report.warning_rows),
                use_container_width=True,
                hide_index=True,
            )
            st.dataframe(
                pd.DataFrame(report.market_edge_rows),
                use_container_width=True,
                hide_index=True,
            )

with coverage_tab:
    st.subheader("Source Coverage")
    st.caption(
        "Coverage separates critical trust inputs from review-only gaps. Missing "
        "production, role/usage, age/bio, or identity can block decisions. Missing "
        "projection, injury, or market data lowers confidence until reviewed or accepted. "
        "Projection rows marked local baseline are local baseline, not forecast. "
        "Source gap summaries separate roster-critical blockers from draft/final blockers "
        "and paid/free source-upgrade candidates."
    )
    if coverage_report.issues:
        for issue in coverage_report.issues:
            st.warning(issue)
    st.dataframe(
        pd.DataFrame(coverage_report.summary_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("**Route/Participation Gap Gate**")
    st.caption(
        "Route participation is the biggest remaining role-data weakness. This gate "
        "separates imported real data, derived proxy, missing/proxy, and neutral "
        "default rows, then marks where paid/exported route data would materially "
        "improve confidence."
    )
    if route_participation_gap.issues:
        for issue in route_participation_gap.issues:
            st.warning(issue)
    else:
        st.dataframe(
            pd.DataFrame(route_participation_gap.area_rows),
            use_container_width=True,
            hide_index=True,
        )
        with st.expander("Route/Participation Player Details"):
            route_frame = pd.DataFrame(route_participation_gap.rows)
            if route_frame.empty:
                st.info("No route/participation rows are available.")
            else:
                route_statuses = sorted(
                    route_frame["route_participation_status"].dropna().unique()
                )
                materialities = sorted(
                    route_frame["paid_data_materiality"].dropna().unique()
                )
                route_cols = st.columns(3)
                selected_route_statuses = route_cols[0].multiselect(
                    "Route Status",
                    route_statuses,
                    default=route_statuses,
                )
                selected_materiality = route_cols[1].multiselect(
                    "Paid Data Materiality",
                    materialities,
                    default=materialities,
                )
                material_only = route_cols[2].checkbox("Material paid-data gaps only")
                route_filtered = route_frame[
                    route_frame["route_participation_status"].isin(selected_route_statuses)
                    & route_frame["paid_data_materiality"].isin(selected_materiality)
                ]
                if material_only:
                    route_filtered = route_filtered[
                        route_filtered["paid_data_materiality"].isin(["high", "medium"])
                    ]
                st.dataframe(
                    route_filtered,
                    use_container_width=True,
                    hide_index=True,
                )
        with st.expander("Route/Participation Summary"):
            st.dataframe(
                pd.DataFrame(route_participation_gap.summary_rows),
                use_container_width=True,
                hide_index=True,
            )
    if coverage_report.gap_acceptance_summary_rows:
        st.markdown("**Source Gap Acceptance Workflow**")
        st.caption(
            "Accepted optional source gaps stay visible and keep their confidence "
            "penalty. Acceptance never fabricates projection, injury, or market data."
        )
        st.dataframe(
            pd.DataFrame(coverage_report.gap_acceptance_summary_rows),
            use_container_width=True,
            hide_index=True,
        )
        if coverage_report.invalid_gap_acceptance_rows:
            st.error(
                "Some source gap acceptance rows are invalid and will not unblock "
                "the source coverage gate."
            )
            st.dataframe(
                pd.DataFrame(coverage_report.invalid_gap_acceptance_rows),
                use_container_width=True,
                hide_index=True,
            )
    player_coverage = pd.DataFrame(coverage_report.player_rows)
    if player_coverage.empty:
        st.info("No source coverage rows are available.")
    else:
        statuses = sorted(player_coverage["coverage_status"].dropna().unique())
        filter_cols = st.columns(3)
        selected_statuses = filter_cols[0].multiselect(
            "Coverage Status",
            statuses,
            default=statuses,
        )
        critical_only = filter_cols[1].checkbox("Critical gaps only", value=False)
        review_only = filter_cols[2].checkbox("Review gaps only", value=False)
        filtered_player_coverage = player_coverage[
            player_coverage["coverage_status"].isin(selected_statuses)
        ]
        if critical_only:
            filtered_player_coverage = filtered_player_coverage[
                filtered_player_coverage["missing_critical_count"].astype(float) > 0
            ]
        if review_only:
            filtered_player_coverage = filtered_player_coverage[
                filtered_player_coverage["review_gap_count"].astype(float) > 0
            ]
        display_columns = [
            "player",
            "position",
            "team",
            "coverage_status",
            "source_gap_summary",
            "source_gap_scopes",
            "coverage_pct",
            "coverage_adjusted_confidence",
            "missing_critical_inputs",
            "critical_review_inputs",
            "review_gap_inputs",
            "accepted_review_gap_inputs",
            "unaccepted_review_gap_inputs",
            "coverage_confidence_penalty",
        ]
        st.dataframe(
            filtered_player_coverage.reindex(columns=display_columns),
            use_container_width=True,
            hide_index=True,
        )
    with st.expander("Bucket And Feature Details"):
        bucket_frame = pd.DataFrame(coverage_report.bucket_rows)
        if not bucket_frame.empty:
            acceptance_statuses = sorted(
                bucket_frame["gap_acceptance_status"].dropna().unique()
            )
            selected_acceptance_statuses = st.multiselect(
                "Gap Acceptance Status",
                acceptance_statuses,
                default=acceptance_statuses,
            )
            bucket_display_columns = [
                "player",
                "position",
                "bucket",
                "coverage_class",
                "bucket_status",
                "coverage_pct",
                "decision_effect",
                "source_gap_scope",
                "source_gap_summary",
                "gap_acceptance_status",
                "next_action",
                "confidence_penalty",
                "missing_features",
                "imputed_features",
                "gap_acceptance_reason",
            ]
            st.dataframe(
                bucket_frame[
                    bucket_frame["gap_acceptance_status"].isin(
                        selected_acceptance_statuses
                    )
                ].reindex(columns=bucket_display_columns),
                use_container_width=True,
                hide_index=True,
            )
        st.dataframe(
            pd.DataFrame(coverage_report.feature_rows),
            use_container_width=True,
            hide_index=True,
        )

with ranking_tab:
    st.subheader("Ranking Audit")
    st.caption(
        "This shows which source table, rank column, sort direction, and model version "
        "drive each visible ranking. Use it when a table order feels random."
    )
    st.dataframe(
        pd.DataFrame(ranking_audit_summary_rows(ranking_audit)),
        use_container_width=True,
        hide_index=True,
    )
    audit_frame = pd.DataFrame(ranking_audit.rows)
    if audit_frame.empty:
        st.info("No ranking audit rows are available.")
    else:
        audit_cols = st.columns(3)
        selected_pages = audit_cols[0].multiselect(
            "Page",
            ranking_audit.pages,
            default=ranking_audit.pages,
        )
        selected_sources = audit_cols[1].multiselect(
            "Source",
            ranking_audit.sources,
            default=ranking_audit.sources,
        )
        search = audit_cols[2].text_input("Search", "")
        filtered_audit = audit_frame[
            audit_frame["page"].isin(selected_pages)
            & audit_frame["source"].isin(selected_sources)
            & audit_frame["player"].str.contains(search, case=False, na=False)
        ]
        with st.expander("Ranking audit rows", expanded=True):
            st.dataframe(filtered_audit, use_container_width=True, hide_index=True)

with model_v4_tab:
    st.subheader("Model v4 Preview")
    st.warning(
        "Review-only Model v4 preview. These rows are visible for audit only; active "
        "War Board, My Team, Rankings, Draft Board, League Targets, and readiness gates "
        "are unchanged."
    )
    if model_v4_review.issues:
        st.error("Some Model v4 review files are missing or unreadable.")
        st.dataframe(
            pd.DataFrame({"issue": model_v4_review.issues}),
            use_container_width=True,
            hide_index=True,
        )

    v4_summary_frame = pd.DataFrame(model_v4_review.summary_rows)
    if v4_summary_frame.empty:
        st.info("No Model v4 preview summary is available.")
    else:
        summary = v4_summary_frame.iloc[0]
        metric_cols = st.columns(4)
        metric_cols[0].metric("Preview Status", str(summary["preview_status"]))
        metric_cols[1].metric("Formula Version", str(summary["formula_version"]))
        metric_cols[2].metric("Preview Rows", int(summary["preview_rows"]))
        metric_cols[3].metric("Warning Rows", int(summary["warning_rows"]))
        with st.expander("Preview summary details"):
            st.dataframe(v4_summary_frame, use_container_width=True, hide_index=True)

    v4_gate_frame = pd.DataFrame(model_v4_review.gate_rows)
    if v4_gate_frame.empty:
        st.info("No Model v4 guard rows are available.")
    elif (v4_gate_frame["status"].astype(str) == "blocked").any():
        st.error("A Model v4 preview guard failed. Do not use these outputs.")
        st.dataframe(v4_gate_frame, use_container_width=True, hide_index=True)
    else:
        st.success("Model v4 preview is isolated. No readiness gates are unlocked.")
        with st.expander("Review-only guard rows"):
            st.dataframe(v4_gate_frame, use_container_width=True, hide_index=True)

    (
        v4_preview_rankings_tab,
        v4_component_receipts_tab,
        v4_source_coverage_tab,
        v4_warning_rows_tab,
        v4_sanity_fixtures_tab,
        v4_named_review_tab,
    ) = st.tabs(
        [
            "Preview Rankings",
            "Component Receipts",
            "Source Coverage",
            "Warning Rows",
            "Sanity Fixture Dry Run",
            "Named Player Review",
        ]
    )

    with v4_preview_rankings_tab:
        preview_frame = pd.DataFrame(model_v4_review.preview_rows)
        if preview_frame.empty:
            st.info("No Model v4 preview rankings are available.")
        else:
            st.caption(MODEL_V4_PREVIEW_REVIEW_ONLY_LABEL)
            st.caption(
                "Sorted by review-only Dynasty Asset Value descending, then player."
            )
            filter_cols = st.columns([1, 1, 1, 1, 1.2])
            positions = sorted(preview_frame["position"].dropna().astype(str).unique())
            lifecycles = sorted(preview_frame["lifecycle"].dropna().astype(str).unique())
            confidence_labels = sorted(
                preview_frame["confidence_label"].dropna().astype(str).unique()
            )
            selected_positions = filter_cols[0].multiselect(
                "Position",
                positions,
                default=positions,
                key="model_v4_preview_position_filter",
            )
            selected_lifecycles = filter_cols[1].multiselect(
                "Lifecycle",
                lifecycles,
                default=lifecycles,
                key="model_v4_preview_lifecycle_filter",
            )
            selected_confidence = filter_cols[2].multiselect(
                "Confidence Label",
                confidence_labels,
                default=confidence_labels,
                key="model_v4_preview_confidence_filter",
            )
            warning_contains = filter_cols[3].text_input(
                "Warning Contains",
                "",
                key="model_v4_preview_warning_filter",
            )
            search = filter_cols[4].text_input(
                "Search",
                "",
                key="model_v4_preview_search",
            )
            filtered_preview = preview_frame[
                preview_frame["position"].astype(str).isin(selected_positions)
                & preview_frame["lifecycle"].astype(str).isin(selected_lifecycles)
                & preview_frame["confidence_label"].astype(str).isin(selected_confidence)
            ].copy()
            if warning_contains:
                filtered_preview = filtered_preview[
                    filtered_preview["review_warnings"].astype(str).str.contains(
                        warning_contains,
                        case=False,
                        na=False,
                    )
                ]
            if search:
                filtered_preview = filtered_preview[
                    filtered_preview["player"].astype(str).str.contains(
                        search,
                        case=False,
                        na=False,
                    )
                    | filtered_preview["nfl_team"].astype(str).str.contains(
                        search,
                        case=False,
                        na=False,
                    )
                ]

            table_frame = filtered_preview.reindex(
                columns=list(MODEL_V4_PREVIEW_RANKING_COLUMNS)
            ).copy()
            table_event = st.dataframe(
                table_frame,
                column_config={
                    "overall_preview_rank": st.column_config.NumberColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["overall_preview_rank"],
                        pinned=True,
                    ),
                    "position_preview_rank": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["position_preview_rank"],
                        pinned=True,
                    ),
                    "player": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["player"],
                        pinned=True,
                    ),
                    "position": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["position"],
                    ),
                    "nfl_team": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["nfl_team"],
                    ),
                    "lifecycle": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["lifecycle"],
                    ),
                    "dynasty_asset_value": st.column_config.NumberColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["dynasty_asset_value"],
                        format="%.2f",
                    ),
                    "confidence_label": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["confidence_label"],
                    ),
                    "review_warnings": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["review_warnings"],
                    ),
                    "unavailable_sections": st.column_config.TextColumn(
                        MODEL_V4_PREVIEW_RANKING_LABELS["unavailable_sections"],
                    ),
                },
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="model_v4_preview_rankings_table",
            )
            with st.expander("Selected Player Receipt Preview", expanded=True):
                selected_indices = _selected_dataframe_rows(table_event)
                if not selected_indices:
                    st.info("Select one preview row above to inspect its v4 receipt.")
                else:
                    selected_player = str(
                        table_frame.iloc[selected_indices[0]].to_dict().get("player", "")
                    )
                    selected_matches = filtered_preview[
                        filtered_preview["player"].astype(str) == selected_player
                    ]
                    selected_row = (
                        selected_matches.iloc[0].to_dict()
                        if not selected_matches.empty
                        else table_frame.iloc[selected_indices[0]].to_dict()
                    )
                    selected_player = str(selected_row.get("player", ""))
                    receipt_drilldown = _model_v4_receipt_drilldown_rows(
                        selected_row,
                        model_v4_review.receipt_rows,
                    )
                    if receipt_drilldown.empty:
                        st.info("No receipt rows are available for the selected player.")
                    else:
                        receipt_cols = st.columns(5)
                        receipt_cols[0].metric(
                            "Rank",
                            str(selected_row.get("overall_preview_rank") or ""),
                        )
                        receipt_cols[1].metric(
                            "Position Rank",
                            str(selected_row.get("position_preview_rank") or ""),
                        )
                        receipt_cols[2].metric(
                            "Dynasty Asset Value",
                            _format_metric(selected_row.get("dynasty_asset_value")),
                        )
                        receipt_cols[3].metric(
                            "Confidence",
                            str(selected_row.get("confidence_label") or ""),
                        )
                        receipt_cols[4].metric(
                            "Lifecycle",
                            str(selected_row.get("lifecycle") or ""),
                        )
                        unavailable_sections = str(
                            selected_row.get("unavailable_sections") or ""
                        )
                        if unavailable_sections:
                            st.warning(
                                f"Unavailable sections: {unavailable_sections}"
                            )
                        highlighted_receipts = receipt_drilldown[
                            receipt_drilldown["audit_highlight"].astype(str) != ""
                        ]
                        if not highlighted_receipts.empty:
                            st.caption(
                                "Highlighted audit issues: missing source sections, "
                                "proxy-only snap role, missing first-down projections, "
                                "local baseline projections, and young-prior review flags."
                            )
                            st.dataframe(
                                highlighted_receipts.reindex(
                                    columns=[
                                        "component",
                                        "audit_highlight",
                                        "warning",
                                        "unavailable_reason",
                                        "source_status",
                                    ]
                                ),
                                use_container_width=True,
                                hide_index=True,
                            )
                        receipt_display_columns = [
                            "receipt_group",
                            "component",
                            "normalized_score",
                            "weight",
                            "contribution",
                            "expected_component_contribution",
                            "contribution_delta",
                            "reconciles_preview_contribution",
                            "source_status",
                            "raw_fields_used",
                            "warning",
                            "unavailable_reason",
                        ]
                        for component_id in MODEL_V4_RECEIPT_SECTION_ORDER:
                            group_label = MODEL_V4_RECEIPT_SECTION_LABELS[component_id]
                            group_frame = receipt_drilldown[
                                receipt_drilldown["component"].astype(str)
                                == component_id
                            ]
                            if group_frame.empty:
                                st.warning(f"{group_label}: missing source section.")
                                continue
                            st.caption(group_label)
                            st.dataframe(
                                group_frame.reindex(columns=receipt_display_columns),
                                use_container_width=True,
                                hide_index=True,
                            )
                        extra_components = receipt_drilldown[
                            ~receipt_drilldown["component"].astype(str).isin(
                                MODEL_V4_RECEIPT_SECTION_ORDER
                            )
                        ]
                        if not extra_components.empty:
                            st.caption("Other components")
                            st.dataframe(
                                extra_components.reindex(columns=receipt_display_columns),
                                use_container_width=True,
                                hide_index=True,
                            )
                        with st.expander("Advanced raw JSON and raw values"):
                            st.dataframe(
                                receipt_drilldown.reindex(
                                    columns=[
                                        "component",
                                        "raw_fields_used",
                                        "raw_values",
                                        "source_status",
                                        "review_only",
                                    ]
                                ),
                                use_container_width=True,
                                hide_index=True,
                            )

    with v4_component_receipts_tab:
        receipt_frame = pd.DataFrame(model_v4_review.receipt_rows)
        component_frame = pd.DataFrame(model_v4_review.component_rows)
        if receipt_frame.empty and component_frame.empty:
            st.info("No Model v4 receipt rows are available.")
        else:
            st.caption(
                "Component receipts show raw fields, source status, normalized scores, "
                "weights, and contributions for the review-only preview."
            )
            with st.expander("Receipt rows", expanded=True):
                st.dataframe(receipt_frame, use_container_width=True, hide_index=True)
            with st.expander("Normalized component rows"):
                st.dataframe(component_frame, use_container_width=True, hide_index=True)

    with v4_source_coverage_tab:
        source_coverage_rows = list(model_v4_review.source_coverage_rows)
        source_gap_detail_rows = list(
            getattr(model_v4_review, "source_gap_detail_rows", [])
        )
        if not source_gap_detail_rows and source_coverage_rows:
            source_gap_detail_rows = _model_v4_source_gap_rows(source_coverage_rows)
        source_gap_summary_rows = list(
            getattr(model_v4_review, "source_gap_summary_rows", [])
        )
        if not source_gap_summary_rows and source_gap_detail_rows:
            source_gap_summary_rows = _model_v4_source_gap_summary_rows(
                source_gap_detail_rows
            )
        gap_summary_frame = pd.DataFrame(source_gap_summary_rows)
        gap_detail_frame = pd.DataFrame(source_gap_detail_rows)
        if gap_detail_frame.empty:
            st.info("No Model v4 source coverage rows are available.")
        else:
            st.caption(
                "V4 source gaps are classified for review. Not applicable rows, such "
                "as young-player prior for established veterans, are not data failures."
            )
            category_counts = (
                gap_summary_frame.groupby("gap_label", dropna=False)["row_count"]
                .sum()
                .reset_index()
                .sort_values("row_count", ascending=False)
            )
            st.dataframe(category_counts, use_container_width=True, hide_index=True)
            st.caption("Counts by component and position")
            st.dataframe(
                gap_summary_frame.reindex(
                    columns=[
                        "gap_label",
                        "component",
                        "position",
                        "row_count",
                        "is_failure",
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Source gap detail rows"):
                st.dataframe(
                    gap_detail_frame.reindex(
                        columns=[
                            "player",
                            "position",
                            "component",
                            "gap_labels",
                            "coverage_status",
                            "source_status",
                            "warning",
                            "unavailable_reason",
                            "gap_explanation",
                            "is_data_failure",
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            with st.expander("Raw source coverage rows"):
                st.dataframe(
                    pd.DataFrame(source_coverage_rows),
                    use_container_width=True,
                    hide_index=True,
                )

    with v4_warning_rows_tab:
        warning_frame = pd.DataFrame(model_v4_review.warning_rows)
        if warning_frame.empty:
            st.success("No Model v4 warning rows are available.")
        else:
            st.dataframe(warning_frame, use_container_width=True, hide_index=True)

    with v4_sanity_fixtures_tab:
        fixture_frame = pd.DataFrame(model_v4_review.sanity_fixture_rows)
        if fixture_frame.empty:
            st.info("No Phase 3 sanity fixture dry-run rows are available.")
        else:
            if "audit_status" not in fixture_frame.columns:
                fixture_frame["audit_status"] = fixture_frame["status"].map(
                    _model_v4_fixture_audit_status
                )
            if "classification" not in fixture_frame.columns:
                fixture_frame["classification"] = fixture_frame.get(
                    "disagreement_classification",
                    "",
                )
            if "receipt_drilldown_hint" not in fixture_frame.columns:
                fixture_frame["receipt_drilldown_hint"] = (
                    "Use the Model v4 receipt drilldown for the listed player(s)."
                )
            if "decision_ready_unlocked" not in fixture_frame.columns:
                fixture_frame["decision_ready_unlocked"] = False
            fixture_counts = _model_v4_audit_status_counts(fixture_frame)
            fixture_cols = st.columns(4)
            fixture_cols[0].metric("Ready", fixture_counts["ready"])
            fixture_cols[1].metric("Review", fixture_counts["review"])
            fixture_cols[2].metric("Blocked", fixture_counts["blocked"])
            fixture_cols[3].metric("Decision-ready unlocked", "False")
            st.caption(
                "Review findings are sorted first. Fixture findings do not auto-change "
                "formulas or unlock readiness."
            )
            st.caption(
                "Review finding columns: expected behavior, actual behavior, "
                "classification, likely cause, next action, receipt drilldown hint."
            )
            fixture_review_frame = fixture_frame[
                fixture_frame["audit_status"].astype(str).isin(["blocked", "review"])
            ]
            if fixture_review_frame.empty:
                st.success("No sanity fixture review findings are currently open.")
            else:
                st.dataframe(
                    fixture_review_frame.reindex(
                        columns=[
                            "fixture_id",
                            "fixture_name",
                            "audit_status",
                            "review_severity",
                            "players",
                            "expected_behavior",
                            "actual_behavior",
                            "classification",
                            "likely_cause",
                            "next_action",
                            "receipt_drilldown_hint",
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            with st.expander("All sanity fixture rows"):
                st.dataframe(
                    fixture_frame.reindex(
                    columns=[
                        "fixture_id",
                        "fixture_name",
                        "fixture_type",
                        "status",
                        "audit_status",
                        "review_severity",
                        "players",
                        "expected_behavior",
                        "actual_behavior",
                        "classification",
                        "likely_cause",
                        "next_action",
                        "receipt_drilldown_hint",
                        "decision_ready_unlocked",
                    ]
                ),
                    use_container_width=True,
                    hide_index=True,
                )

    with v4_named_review_tab:
        named_frame = pd.DataFrame(model_v4_review.named_player_rows)
        if named_frame.empty:
            st.info("No Phase 3 named-player review rows are available.")
        else:
            if "audit_status" not in named_frame.columns:
                named_frame["audit_status"] = named_frame.apply(
                    _model_v4_named_audit_status,
                    axis=1,
                )
            if "expected_behavior" not in named_frame.columns:
                named_frame["expected_behavior"] = (
                    "Named player should map cleanly and have receipt-backed Model v4 "
                    "preview evidence."
                )
            if "actual_behavior" not in named_frame.columns:
                named_frame["actual_behavior"] = (
                    named_frame["matched_player"].fillna(named_frame["requested_player"])
                    + ": rank "
                    + named_frame["overall_rank"].astype(str)
                    + ", position rank "
                    + named_frame["position_rank"].astype(str)
                    + ", Dynasty Asset Value "
                    + named_frame["dynasty_asset_value"].astype(str)
                    + "."
                )
            if "classification" not in named_frame.columns:
                named_frame["classification"] = named_frame["audit_status"].map(
                    {
                        "blocked": "identity or missing-output issue",
                        "review": "confidence or source review",
                        "ready": "receipt-backed ready row",
                    }
                )
            if "likely_cause" not in named_frame.columns:
                named_frame["likely_cause"] = named_frame["review_notes"].fillna("")
            if "next_action" not in named_frame.columns:
                named_frame["next_action"] = (
                    "Open the v4 receipt drilldown; fill missing evidence or document "
                    "the review risk before formula tuning."
                )
            if "receipt_drilldown_hint" not in named_frame.columns:
                named_frame["receipt_drilldown_hint"] = (
                    "Use the Model v4 receipt drilldown for the matched player."
                )
            if "decision_ready_unlocked" not in named_frame.columns:
                named_frame["decision_ready_unlocked"] = False
            named_counts = _model_v4_audit_status_counts(named_frame)
            named_cols = st.columns(4)
            named_cols[0].metric("Ready", named_counts["ready"])
            named_cols[1].metric("Review", named_counts["review"])
            named_cols[2].metric("Blocked", named_counts["blocked"])
            named_cols[3].metric("Decision-ready unlocked", "False")
            st.caption(
                "Review findings are sorted first. Named-player audit rows point back "
                "to the v4 receipt drilldown for inspection."
            )
            st.caption(
                "Review finding columns: expected behavior, actual behavior, "
                "classification, likely cause, next action, receipt drilldown hint."
            )
            named_review_frame = named_frame[
                named_frame["audit_status"].astype(str).isin(["blocked", "review"])
            ]
            if named_review_frame.empty:
                st.success("No named-player review findings are currently open.")
            else:
                st.dataframe(
                    named_review_frame.reindex(
                        columns=[
                            "requested_player",
                            "matched_player",
                            "audit_status",
                            "position",
                            "nfl_team",
                            "lifecycle",
                            "expected_behavior",
                            "actual_behavior",
                            "classification",
                            "likely_cause",
                            "next_action",
                            "receipt_drilldown_hint",
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            with st.expander("All named-player review rows"):
                st.dataframe(
                    named_frame.reindex(
                    columns=[
                        "requested_player",
                        "matched_player",
                        "match_status",
                        "audit_status",
                        "position",
                        "nfl_team",
                        "lifecycle",
                        "overall_rank",
                        "position_rank",
                        "dynasty_asset_value",
                        "confidence_label",
                        "expected_behavior",
                        "actual_behavior",
                        "classification",
                        "likely_cause",
                        "next_action",
                        "receipt_drilldown_hint",
                        "top_positive_receipt_drivers",
                        "top_negative_receipt_drivers",
                        "warnings",
                        "review_notes",
                        "decision_ready_unlocked",
                    ]
                ),
                    use_container_width=True,
                    hide_index=True,
                )

with calibration_tab:
    st.subheader("Calibration")
    st.caption(
        "Calibration is where model readiness, historical replay, and final trust "
        "checks live. It is not a normal draft-pressure page."
    )
    calibration_cols = st.columns(3)
    calibration_cols[0].metric("Gate", calibration_report.badge)
    calibration_cols[1].metric("Roster", pre_decision_checklist.roster_decision_badge)
    calibration_cols[2].metric("Final", pre_decision_checklist.final_money_badge)
    if calibration_report.passed:
        st.success("Calibration gate passed.")
    else:
        st.warning("Calibration gate has blockers or review items.")
    with st.expander("Calibration gate rows", expanded=True):
        st.dataframe(
            gate_overview_frame.reindex(
                columns=[
                    "requirement",
                    "status",
                    "severity",
                    "blocker",
                    "why_it_matters",
                    "next_action",
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    st.caption("Historical replay and rookie calibration stay in debug tools.")
    calibration_link_cols = st.columns(2)
    calibration_link_cols[0].link_button(
        "Open Historical Replay Debug",
        "/historical-replay-debug",
    )
    calibration_link_cols[1].link_button(
        "Open Rookie Model Debug",
        "/rookie-model-debug",
    )

with tool_tab:
    st.subheader("What Belongs Here")
    st.write(
        "Model Lab is for checking the machinery behind the boards. It is intentionally "
        "off the draft-pressure path: use War Board, My Team, League Targets, Rankings, "
        "Draft Board, and Trade Lab for normal decisions."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "area": "Outliers",
                    "purpose": "Find rankings that are probably broken or potentially exploitable.",
                    "sidebar": "visible here",
                    "decision_use": "Audit suspicious rankings before trusting them.",
                    "path": "/model-lab",
                },
                {
                    "area": "Receipts",
                    "purpose": "Inspect feature weights, sources, imputation, and contributions.",
                    "sidebar": "visible here",
                    "decision_use": "Use before formula changes or player-specific trust calls.",
                    "path": "/model-lab",
                },
                {
                    "area": "Compare",
                    "purpose": "Compare two players side by side and explain the score gap.",
                    "sidebar": "visible here",
                    "decision_use": "Use for sanity checks like Kyren vs Bijan or JSN vs Tee.",
                    "path": "/model-lab",
                },
                {
                    "area": "Sources",
                    "purpose": (
                        "Import public/stat source files, inspect source coverage, "
                        "and build preview/apply packs."
                    ),
                    "sidebar": "hidden",
                    "decision_use": "Use before trusting new stats, not during a pick clock.",
                    "path": "/model-lab-sources",
                },
                {
                    "area": "Rookie Model Debug",
                    "purpose": (
                        "Run rookie intake, normalization, board generation, "
                        "and veteran benchmark checks."
                    ),
                    "sidebar": "hidden",
                    "decision_use": (
                        "Use when rebuilding rookie fixtures or checking formula receipts."
                    ),
                    "path": "/rookie-model-debug",
                },
                {
                    "area": "Historical Replay Debug",
                    "purpose": (
                        "Backtest pre-NFL rookie prospect ranks against later outcome labels."
                    ),
                    "sidebar": "hidden",
                    "decision_use": (
                        "Use for calibration and trust-building, never as a live "
                        "ranking input."
                    ),
                    "path": "/historical-replay-debug",
                },
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    source_col, rookie_col, replay_col = st.columns(3)
    source_col.link_button("Open Sources", "/model-lab-sources")
    rookie_col.link_button("Open Rookie Model Debug", "/rookie-model-debug")
    replay_col.link_button("Open Historical Replay Debug", "/historical-replay-debug")

    with st.expander("Why Some Tools Are Hidden From Sidebar"):
        st.write(
            "They are still available, but they are not first-click decision surfaces. "
            "The compressed sidebar keeps the app focused on import, roster decisions, "
            "targets, trades, draft choices, model audit, and freeze workflow."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "policy": "navigation_compression",
                        "status": "active",
                        "meaning": "Only decision-focused pages appear in the sidebar.",
                    },
                    {
                        "policy": "model_recalibration",
                        "status": "active" if policy.active else "inactive",
                        "meaning": "Rankings remain review-only while trust work continues.",
                    },
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
