from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.demo_source_labels import demo_source_label
from app.components.trust_status import render_trust_status
from src.config.settings import get_settings
from src.services.data_pack_admission_service import (
    admission_reason_rows,
    admission_summary_row,
    build_data_pack_admission_report,
)
from src.services.data_pack_health_service import (
    build_data_pack_health_report,
    readiness_status_rows,
)
from src.services.draft_freeze_service import DEFAULT_FREEZE_ROOT, freeze_draft_pack
from src.services.final_qa_safety_gate_service import (
    build_final_qa_safety_gate_audit,
    safety_gate_audit_rows,
    safety_gate_audit_summary_row,
)
from src.services.lve_stats_first_apply_service import DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT
from src.services.lve_stats_first_preview_service import DEFAULT_STATS_FIRST_PREVIEW_ROOT
from src.services.trust_status_service import trust_status_from_health


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


@st.cache_data
def _load_admission(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint
    return build_data_pack_admission_report(candidate_data_pack=active_data_pack)


settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
health = _load_health(active_data_pack, active_fingerprint)
admission = _load_admission(active_data_pack, active_fingerprint)

st.title("Freeze")
st.caption(demo_source_label(active_data_pack))
st.info(
    "Freeze creates local backup copies and CSV board exports. It does not refresh "
    "Sleeper, rebuild the pack, or mutate the selected data pack."
)

st.subheader("Create Freeze")
freeze_id = st.text_input("Freeze ID", value="")
output_root = st.text_input("Freeze output root", value=str(DEFAULT_FREEZE_ROOT))
stats_first_preview_root = st.text_input(
    "Stats-first preview root",
    value=str(DEFAULT_STATS_FIRST_PREVIEW_ROOT),
)
stats_first_applied_pack_root = st.text_input(
    "Stats-first applied pack root",
    value=str(DEFAULT_STATS_FIRST_APPLIED_PACK_ROOT),
)

st.subheader("Final QA Safety Gate")
safety_report = build_final_qa_safety_gate_audit(
    active_data_pack,
    stats_first_preview_root=stats_first_preview_root,
    stats_first_applied_pack_root=stats_first_applied_pack_root,
    draft_freeze_root=output_root,
)
render_trust_status(health, calibration_passed=safety_report.calibration_passed)
if safety_report.calibration_passed:
    st.success(f"**{safety_report.calibration_badge}.** Final calibration gate is clear.")
elif safety_report.status == "blocked":
    st.error(
        "**Final QA Blocked.** Rankings remain review-only because one or more "
        "freeze/safety gates are blocked. Calibration status: "
        f"{safety_report.calibration_badge}."
    )
else:
    st.warning(
        f"**{safety_report.calibration_badge}.** Rankings remain review-only while "
        "the remaining calibration warnings are checked."
    )
st.dataframe(
    pd.DataFrame([safety_gate_audit_summary_row(safety_report)]),
    use_container_width=True,
    hide_index=True,
)
st.dataframe(
    pd.DataFrame(safety_gate_audit_rows(safety_report)),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Final Decision-Readiness Checklist")
checklist_frame = pd.DataFrame(
    readiness_status_rows(
        health,
        calibration_passed=safety_report.calibration_passed,
    )
)
st.dataframe(checklist_frame, use_container_width=True, hide_index=True)
st.subheader("Admission Gate")
st.dataframe(
    pd.DataFrame([admission_summary_row(admission)]),
    use_container_width=True,
    hide_index=True,
)
st.dataframe(
    pd.DataFrame(admission_reason_rows(admission)),
    use_container_width=True,
    hide_index=True,
)

left, middle, right = st.columns(3)
left.metric("Data", checklist_frame.loc[0, "status"])
middle.metric("Model", checklist_frame.loc[1, "status"])
right.metric("Admission", admission.decision)

confirm = st.checkbox("I understand this is a local draft-day freeze, not a refresh.")
trust = trust_status_from_health(
    health,
    calibration_passed=safety_report.calibration_passed,
)
final_ready = (
    trust.status == "decision_ready"
    and admission.decision == "ready"
    and safety_report.calibration_passed
)
not_ready_override = False
if not final_ready:
    st.warning(
        "The active pack is not fully decision-ready under the admission gate. "
        "You can still freeze it as a review snapshot, but it should not be treated "
        "as the draft-day board."
    )
    not_ready_override = st.checkbox(
        "Freeze anyway as a review snapshot, not a final decision board."
    )

can_freeze = confirm and (final_ready or not_ready_override)
if st.button("Freeze Active Pack", type="primary", disabled=not can_freeze):
    try:
        result = freeze_draft_pack(
            active_data_pack,
            output_root=output_root,
            freeze_id=freeze_id or None,
            allow_review_snapshot=not_ready_override and not final_ready,
            stats_first_preview_root=stats_first_preview_root,
            stats_first_applied_pack_root=stats_first_applied_pack_root,
        )
        st.success(f"Frozen: {result.freeze_dir}")
        st.session_state["last_freeze_result"] = {
            "freeze_id": result.freeze_id,
            "freeze_dir": str(result.freeze_dir),
            "metadata_path": str(result.metadata_path),
            "checklist_path": str(result.checklist_path),
            "summary_path": str(result.summary_path),
            "exports": {key: str(path) for key, path in result.export_files.items()},
        }
    except FileExistsError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Freeze failed: {exc}")

if st.session_state.get("last_freeze_result"):
    st.subheader("Last Freeze")
    result = st.session_state["last_freeze_result"]
    st.dataframe(
        pd.DataFrame(
            [
                {"item": "freeze_id", "path": result["freeze_id"]},
                {"item": "freeze_dir", "path": result["freeze_dir"]},
                {"item": "draft_day_readme", "path": result["summary_path"]},
                {"item": "metadata", "path": result["metadata_path"]},
                {"item": "checklist", "path": result["checklist_path"]},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    with st.expander("Exported Board Files"):
        st.dataframe(
            pd.DataFrame(
                [
                    {"board": board_name, "path": path}
                    for board_name, path in result["exports"].items()
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
