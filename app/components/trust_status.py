from __future__ import annotations

import streamlit as st

from src.services.data_pack_health_service import DataPackHealthReport
from src.services.model_recalibration_service import model_recalibration_policy
from src.services.trust_status_service import trust_status_from_health

REVIEW_ONLY_SURFACE_BANNER = (
    "Review-only surface. This page does not make automatic trade, cut, keep, "
    "or draft recommendations."
)


def render_trust_status(
    health: DataPackHealthReport,
    *,
    calibration_passed: bool = False,
) -> None:
    trust = trust_status_from_health(health, calibration_passed=calibration_passed)
    text = f"**{trust.title}.** {trust.message} Next: {trust.next_action}"
    if trust.severity == "error":
        st.error(text)
    elif trust.severity == "warning":
        st.warning(text)
    elif trust.severity == "success":
        st.success(text)
    else:
        st.info(text)


def render_model_recalibration_banner(
    *,
    compact: bool = False,
    calibration_passed: bool = False,
) -> None:
    policy = model_recalibration_policy()
    if not policy.active or calibration_passed:
        return
    text = f"**{policy.title}.** {policy.message} Next: {policy.next_action}"
    if compact:
        st.warning(f"**{policy.title}.** Rankings are review-only.")
    else:
        st.warning(text)


def render_page_trust_banner(
    health: DataPackHealthReport,
    *,
    calibration_passed: bool = False,
    review_only_message: str = "",
    review_only_detail: str = "",
    details_label: str = "Why review-only?",
    compact: bool = False,
) -> None:
    trust = trust_status_from_health(health, calibration_passed=calibration_passed)
    if compact and not calibration_passed:
        text = f"**{trust.title}.** Rankings are review-only until calibration gates pass."
    else:
        text = f"**{trust.title}.** {trust.message}"
    if trust.severity == "error":
        st.error(text)
    elif trust.severity == "warning":
        st.warning(text)
    elif trust.severity == "success":
        st.success(text)
    else:
        st.info(text)

    if calibration_passed:
        return

    st.warning(REVIEW_ONLY_SURFACE_BANNER)
    with st.expander(details_label):
        st.write(f"Next: {trust.next_action}")
        if review_only_message:
            st.write(review_only_message)
        if review_only_detail:
            st.write(review_only_detail)
