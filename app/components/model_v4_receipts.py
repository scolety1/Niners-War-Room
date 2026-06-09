from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import streamlit as st

from src.services.model_v4_app_review_service import (
    MODEL_V4_RECEIPT_DRILLDOWN_COLUMNS,
    MODEL_V4_RECEIPT_DRILLDOWN_LABELS,
    MODEL_V4_RECEIPT_SECTION_LABELS,
    MODEL_V4_RECEIPT_SECTION_ORDER,
    build_model_v4_receipt_drilldown_rows,
    build_model_v4_receipt_reconciliation_row,
)


def render_model_v4_shadow_receipt_drilldown(
    selected_shadow_row: dict[str, object] | None,
    preview_rows: Iterable[dict[str, object]],
    receipt_rows: list[dict[str, str]],
    *,
    key_prefix: str,
) -> None:
    if selected_shadow_row is None:
        st.info("Select one V4 shadow row to inspect its receipt.")
        return

    preview_row = _find_preview_row(selected_shadow_row, preview_rows)
    if not preview_row:
        st.info("No V4 preview receipt can be matched for the selected shadow row.")
        return

    receipt_rows_for_player = build_model_v4_receipt_drilldown_rows(
        preview_row,
        receipt_rows,
    )
    if not receipt_rows_for_player:
        st.info("No V4 receipt rows are available for the selected player.")
        return

    receipt_frame = pd.DataFrame(receipt_rows_for_player)
    reconciliation = build_model_v4_receipt_reconciliation_row(
        preview_row,
        receipt_rows_for_player,
    )
    st.caption(
        "Audit-only receipt drilldown. These rows explain the V4 shadow value; "
        "they do not change active rankings or readiness gates."
    )
    metric_cols = st.columns(5)
    metric_cols[0].metric("Rank", str(preview_row.get("overall_preview_rank") or ""))
    metric_cols[1].metric(
        "Position Rank",
        str(preview_row.get("position_preview_rank") or ""),
    )
    metric_cols[2].metric(
        "Dynasty Asset Value",
        _format_metric(preview_row.get("dynasty_asset_value")),
    )
    metric_cols[3].metric(
        "Receipt Total",
        _format_metric(reconciliation.get("receipt_contribution_total")),
    )
    metric_cols[4].metric(
        "Confidence",
        str(preview_row.get("confidence_label") or ""),
    )
    if reconciliation["reconciles_preview_score"]:
        st.success(
            "Receipt contributions reconcile to the V4 preview Dynasty Asset Value."
        )
    else:
        st.warning(
            "Receipt contribution total does not reconcile to the V4 preview score. "
            "Treat this player as a receipt audit issue."
        )
        st.dataframe(
            pd.DataFrame([reconciliation]),
            use_container_width=True,
            hide_index=True,
        )

    unavailable_sections = str(preview_row.get("unavailable_sections") or "").strip()
    if unavailable_sections:
        st.warning(f"Unavailable sections: {unavailable_sections}")

    highlighted = receipt_frame[
        receipt_frame["audit_highlight"].astype(str).str.strip() != ""
    ]
    if not highlighted.empty:
        st.caption(
            "Highlighted audit issues include missing evidence, proxy-only evidence, "
            "unavailable route data, estimated first-down projections, and rookie "
            "review-policy warnings."
        )
        st.dataframe(
            highlighted.reindex(
                columns=[
                    "component",
                    "audit_highlight",
                    "source_status",
                    "warning",
                    "unavailable_reason",
                ]
            ),
            use_container_width=True,
            hide_index=True,
            key=f"{key_prefix}_highlighted_receipts",
        )

    for component in MODEL_V4_RECEIPT_SECTION_ORDER:
        section_label = MODEL_V4_RECEIPT_SECTION_LABELS[component]
        group_frame = receipt_frame[
            receipt_frame["component"].astype(str) == component
        ]
        if group_frame.empty:
            st.warning(f"{section_label}: no receipt rows available.")
            continue
        st.caption(section_label)
        st.dataframe(
            group_frame.reindex(columns=list(MODEL_V4_RECEIPT_DRILLDOWN_COLUMNS)),
            column_config=MODEL_V4_RECEIPT_DRILLDOWN_LABELS,
            use_container_width=True,
            hide_index=True,
            key=f"{key_prefix}_{component}_receipt_rows",
        )

    extra_components = receipt_frame[
        ~receipt_frame["component"].astype(str).isin(MODEL_V4_RECEIPT_SECTION_ORDER)
    ]
    if not extra_components.empty:
        st.caption("Other Components")
        st.dataframe(
            extra_components.reindex(columns=list(MODEL_V4_RECEIPT_DRILLDOWN_COLUMNS)),
            column_config=MODEL_V4_RECEIPT_DRILLDOWN_LABELS,
            use_container_width=True,
            hide_index=True,
            key=f"{key_prefix}_extra_receipt_rows",
        )

    with st.expander("Advanced: raw V4 receipt rows"):
        st.dataframe(
            receipt_frame.reindex(
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
            key=f"{key_prefix}_raw_receipt_rows",
        )


def _find_preview_row(
    selected_shadow_row: dict[str, object],
    preview_rows: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    target_names = [
        str(selected_shadow_row.get("matched_v4_player") or "").strip(),
        str(selected_shadow_row.get("player") or "").strip(),
    ]
    target_keys = {_normalized_player_key(name) for name in target_names if name}
    for row in preview_rows:
        row_name = str(row.get("player") or "")
        keys = {
            _normalized_player_key(row_name),
            _normalized_player_key(_remove_suffix(row_name)),
        }
        if target_keys & keys:
            return row
    return None


def _normalized_player_key(player: object) -> str:
    text = _remove_suffix(str(player or ""))
    return "".join(character.lower() for character in text if character.isalnum())


def _remove_suffix(player: str) -> str:
    parts = player.replace(".", "").split()
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    while parts and parts[-1].lower() in suffixes:
        parts.pop()
    return " ".join(parts)


def _format_metric(value: object) -> str:
    try:
        return f"{float(str(value)):.2f}"
    except (TypeError, ValueError):
        return str(value or "")
