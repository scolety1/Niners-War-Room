from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MODEL_V4_PREVIEW_ROOT = Path("local_exports/model_v4/review_only_latest")
DEFAULT_MODEL_V4_SANITY_PATH = Path(
    "docs/model_v4/PHASE_7C_SANITY_FIXTURE_RESULTS.csv"
)
DEFAULT_MODEL_V4_NAMED_PATH = Path("docs/model_v4/PHASE_7C_NAMED_PLAYER_REVIEW.csv")
DEFAULT_MODEL_V4_MOVEMENT_PATH = Path("docs/model_v4/PHASE_7C_MOVEMENT_AUDIT.csv")
MODEL_V4_PREVIEW_REVIEW_ONLY_LABEL = "Review-only v4 preview. Not active rankings."
MODEL_V4_SHADOW_WAR_BOARD_BANNER = (
    "V4 shadow board. Review-only. Active rankings are unchanged."
)
MODEL_V4_OLD_VS_V4_BANNER = (
    "Old vs V4 comparison. Review-only. Active rankings are unchanged."
)
MODEL_V4_PROMOTION_BLOCKERS_BANNER = (
    "V4 promotion blockers. Review-only. No readiness gates are unlocked."
)
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
MODEL_V4_SHADOW_WAR_BOARD_COLUMNS = MODEL_V4_PREVIEW_RANKING_COLUMNS
MODEL_V4_SHADOW_WAR_BOARD_LABELS = {
    **MODEL_V4_PREVIEW_RANKING_LABELS,
    "overall_preview_rank": "V4 Overall Rank",
    "position_preview_rank": "V4 Position Rank",
}
MODEL_V4_OLD_VS_V4_COLUMNS = (
    "player",
    "position",
    "fantasy_team",
    "active_overall_rank",
    "v4_shadow_rank",
    "active_value",
    "v4_dynasty_asset_value",
    "active_confidence",
    "v4_confidence",
    "active_warning",
    "v4_warning",
    "movement_direction",
    "movement_size",
    "movement_reason",
    "large_unexplained_movement",
)
MODEL_V4_OLD_VS_V4_LABELS = {
    "player": "Player",
    "position": "Position",
    "fantasy_team": "Fantasy Team",
    "active_overall_rank": "Active Overall Rank",
    "v4_shadow_rank": "V4 Shadow Rank",
    "active_value": "Active Value",
    "v4_dynasty_asset_value": "V4 Dynasty Asset Value",
    "active_confidence": "Active Confidence",
    "v4_confidence": "V4 Confidence",
    "active_warning": "Active Warning",
    "v4_warning": "V4 Warning",
    "movement_direction": "Movement Direction",
    "movement_size": "Movement Size",
    "movement_reason": "Movement Reason",
    "large_unexplained_movement": "Large Unexplained Movement",
}
MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS = {
    "data_blocker": "Data Blocker",
    "formula_blocker": "Formula Blocker",
    "confidence_blocker": "Confidence Blocker",
    "source_limitation": "Source Limitation",
    "ui_blocker": "UI Blocker",
    "accepted_limitation": "Accepted Limitation",
}
MODEL_V4_PROMOTION_BLOCKER_GROUP_ORDER = tuple(
    MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS
)
MODEL_V4_PROMOTION_BLOCKER_COLUMNS = (
    "blocker_group_label",
    "blocker",
    "why_it_matters",
    "affected_players_surfaces",
    "next_action",
    "promotion_blocking_scope",
    "blocks_app_promotion",
    "blocks_final_decision_ready",
    "evidence_status",
)
MODEL_V4_PROMOTION_BLOCKER_LABELS = {
    "blocker_group_label": "Blocker Group",
    "blocker": "Blocker",
    "why_it_matters": "Why It Matters",
    "affected_players_surfaces": "Affected Players / Surfaces",
    "next_action": "Next Action",
    "promotion_blocking_scope": "Blocking Scope",
    "blocks_app_promotion": "Blocks App Promotion",
    "blocks_final_decision_ready": "Blocks Final Decision Ready",
    "evidence_status": "Evidence Status",
}
MODEL_V4_SHADOW_MY_TEAM_BANNER = (
    "V4 shadow My Team. Review-only. Active My Team is unchanged."
)
MODEL_V4_SHADOW_MY_TEAM_COLUMNS = (
    "player",
    "position",
    "nfl_team",
    "roster_rank",
    "league_rank",
    "top_five_rule_status",
    "v4_dynasty_asset_value",
    "v4_roster_decision_value",
    "confidence_label",
    "warnings",
    "unavailable_sections",
)
MODEL_V4_SHADOW_MY_TEAM_LABELS = {
    "player": "Player",
    "position": "Position",
    "nfl_team": "NFL Team",
    "roster_rank": "Roster Rank",
    "league_rank": "League Rank",
    "top_five_rule_status": "Roster's League-Rank Top Five Status",
    "v4_dynasty_asset_value": "V4 Dynasty Asset Value",
    "v4_roster_decision_value": "V4 Roster Decision Value",
    "confidence_label": "Confidence Label",
    "warnings": "Warnings",
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
    "market_context": "Market Context",
    "league_rank_rule_context": "League-Rank Rule Context",
}
MODEL_V4_RECEIPT_SECTION_ORDER = tuple(MODEL_V4_RECEIPT_SECTION_LABELS)
MODEL_V4_RECEIPT_DRILLDOWN_COLUMNS = (
    "receipt_group",
    "component",
    "raw_fields_used",
    "normalized_score",
    "weight",
    "contribution",
    "expected_component_contribution",
    "contribution_delta",
    "reconciles_preview_contribution",
    "source_status",
    "warning",
    "unavailable_reason",
    "audit_highlight",
)
MODEL_V4_RECEIPT_DRILLDOWN_LABELS = {
    "receipt_group": "Receipt Section",
    "component": "Component",
    "raw_fields_used": "Raw Fields Used",
    "normalized_score": "Normalized Score",
    "weight": "Weight",
    "contribution": "Contribution",
    "expected_component_contribution": "Expected Contribution",
    "contribution_delta": "Contribution Delta",
    "reconciles_preview_contribution": "Reconciles",
    "source_status": "Source Status",
    "warning": "Warning",
    "unavailable_reason": "Unavailable Reason",
    "audit_highlight": "Audit Highlight",
}
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


@dataclass(frozen=True)
class ModelV4AppReviewReport:
    summary_rows: list[dict[str, object]]
    gate_rows: list[dict[str, object]]
    preview_rows: list[dict[str, object]]
    component_rows: list[dict[str, str]]
    receipt_rows: list[dict[str, str]]
    source_coverage_rows: list[dict[str, str]]
    source_gap_detail_rows: list[dict[str, object]]
    source_gap_summary_rows: list[dict[str, object]]
    warning_rows: list[dict[str, str]]
    movement_rows: list[dict[str, str]]
    sanity_fixture_rows: list[dict[str, object]]
    named_player_rows: list[dict[str, object]]
    sanity_fixture_summary_rows: list[dict[str, object]]
    named_player_summary_rows: list[dict[str, object]]
    issues: list[str]


def build_model_v4_app_review(
    preview_root: str | Path = DEFAULT_MODEL_V4_PREVIEW_ROOT,
    sanity_fixture_path: str | Path = DEFAULT_MODEL_V4_SANITY_PATH,
    named_player_path: str | Path = DEFAULT_MODEL_V4_NAMED_PATH,
) -> ModelV4AppReviewReport:
    root = Path(preview_root)
    issues: list[str] = []
    summary = _read_summary(root, issues)
    preview_rows = _rank_preview_rows(
        _read_optional_csv(root / "v4_preview_outputs.csv", issues)
    )
    component_rows = _read_optional_csv(
        root / "v4_normalized_component_rows.csv", issues
    )
    receipt_rows = _read_optional_csv(root / "v4_receipt_rows.csv", issues)
    source_coverage_rows = _read_optional_csv(
        root / "v4_source_coverage_rows.csv", issues
    )
    source_gap_detail_rows = build_model_v4_source_gap_rows(source_coverage_rows)
    source_gap_summary_rows = build_model_v4_source_gap_summary_rows(
        source_gap_detail_rows
    )
    warning_rows = _read_optional_csv(root / "v4_warning_rows.csv", issues)
    movement_rows = _read_existing_csv(DEFAULT_MODEL_V4_MOVEMENT_PATH)
    sanity_rows = _read_optional_csv(Path(sanity_fixture_path), issues)
    named_rows = _read_optional_csv(Path(named_player_path), issues)
    sanity_audit_rows = build_model_v4_sanity_fixture_audit_rows(sanity_rows)
    named_audit_rows = build_model_v4_named_player_audit_rows(named_rows)

    return ModelV4AppReviewReport(
        summary_rows=_summary_rows(summary, root),
        gate_rows=_gate_rows(summary),
        preview_rows=preview_rows,
        component_rows=component_rows,
        receipt_rows=receipt_rows,
        source_coverage_rows=source_coverage_rows,
        source_gap_detail_rows=source_gap_detail_rows,
        source_gap_summary_rows=source_gap_summary_rows,
        warning_rows=warning_rows,
        movement_rows=movement_rows,
        sanity_fixture_rows=sanity_audit_rows,
        named_player_rows=named_audit_rows,
        sanity_fixture_summary_rows=build_model_v4_audit_summary_rows(
            "Sanity Fixture Dry Run",
            sanity_audit_rows,
        ),
        named_player_summary_rows=build_model_v4_audit_summary_rows(
            "Named Player Review",
            named_audit_rows,
        ),
        issues=issues,
    )


def build_model_v4_old_vs_v4_comparison_rows(
    active_rows: list[dict[str, object]],
    preview_rows: list[dict[str, object]],
    movement_rows: list[dict[str, str]] | None = None,
) -> list[dict[str, object]]:
    active_by_key = _row_lookup(active_rows, "player")
    preview_by_key = _preview_lookup(preview_rows)
    movement_by_key = _row_lookup(movement_rows or [], "player")
    rows: list[dict[str, object]] = []
    for key in sorted(
        set(active_by_key) | set(preview_by_key),
        key=lambda item: _comparison_sort_key(
            active_by_key.get(item),
            preview_by_key.get(item),
        ),
    ):
        active = active_by_key.get(key, {})
        preview = preview_by_key.get(key, {})
        movement = movement_by_key.get(key, {})
        active_rank = _int_or_none(active.get("overall_rank"))
        v4_rank = _int_or_none(preview.get("overall_preview_rank"))
        rank_delta = (
            active_rank - v4_rank
            if active_rank is not None and v4_rank is not None
            else None
        )
        movement_size = _comparison_movement_size(rank_delta)
        movement_reason = _comparison_movement_reason(movement, active, preview)
        player = (
            preview.get("player")
            or active.get("player")
            or movement.get("player")
            or ""
        )
        rows.append(
            {
                "player": player,
                "matched_active_player": _blank_if_missing(active.get("player")),
                "matched_v4_player": _blank_if_missing(preview.get("player")),
                "position": (
                    preview.get("position")
                    or active.get("pos")
                    or active.get("position")
                    or movement.get("position")
                    or ""
                ),
                "nfl_team": (
                    preview.get("nfl_team")
                    or active.get("nfl_team")
                    or movement.get("nfl_team")
                    or ""
                ),
                "fantasy_team": _blank_if_missing(active.get("team")),
                "active_overall_rank": active_rank or "",
                "v4_shadow_rank": v4_rank or "",
                "active_value": _number_or_blank(
                    active.get("stats_value")
                    or active.get("private_score")
                    or active.get("war_score")
                ),
                "v4_dynasty_asset_value": _number_or_blank(
                    preview.get("dynasty_asset_value")
                ),
                "active_confidence": _blank_if_missing(
                    active.get("confidence_label")
                    or active.get("confidence_bucket")
                    or active.get("confidence")
                ),
                "v4_confidence": _blank_if_missing(preview.get("confidence_label")),
                "active_warning": _blank_if_missing(
                    active.get("warning_reason") or active.get("warning_reasons")
                ),
                "v4_warning": _blank_if_missing(preview.get("review_warnings")),
                "movement_rank_delta": rank_delta if rank_delta is not None else "",
                "movement_direction": _comparison_movement_direction(
                    active_rank,
                    v4_rank,
                    rank_delta,
                ),
                "movement_size": movement_size,
                "movement_reason": movement_reason,
                "large_unexplained_movement": (
                    movement_size == "large" and movement_reason == "unknown"
                ),
                "movement_review_note": _comparison_review_note(
                    movement_size,
                    movement_reason,
                ),
                "movement_source": (
                    "phase_7c_movement_audit" if movement else "active_vs_v4_join"
                ),
                "in_niners_roster": (
                    str(active.get("team") or "").lower() == "niners"
                    or str(preview.get("truth_set_group") or "") == "niners_roster"
                ),
                "in_top_50": _rank_is_top_50(active_rank) or _rank_is_top_50(v4_rank),
                "warning_search_text": " | ".join(
                    str(value)
                    for value in (
                        active.get("warning_reason") or active.get("warning_reasons") or "",
                        preview.get("review_warnings") or "",
                        preview.get("unavailable_sections") or "",
                    )
                    if str(value).strip()
                ),
            }
        )
    return rows


def build_model_v4_promotion_blocker_rows(
    preview_rows: list[dict[str, object]],
    source_gap_rows: list[dict[str, object]],
    sanity_fixture_rows: list[dict[str, object]],
    named_player_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    preview_by_key = _preview_lookup(preview_rows)

    if "calebwilliams" not in preview_by_key:
        rows.append(
            _promotion_blocker_row(
                blocker_id="caleb_williams_missing_qb_control",
                blocker_group="data_blocker",
                blocker="Caleb Williams missing from current v4 QB-control preview",
                why_it_matters=(
                    "QB suppression cannot be fully validated while a named QB "
                    "control is absent from the v4 preview."
                ),
                affected_players_surfaces=(
                    "Caleb Williams; V4 Shadow War Board; QB controls; sanity fixtures"
                ),
                next_action=(
                    "Add or document the Caleb Williams v4 preview input, then rerun "
                    "QB-control fixtures."
                ),
                promotion_blocking_scope="Blocks app promotion",
                blocks_app_promotion=True,
                blocks_final_decision_ready=True,
                evidence_status="confirmed from current preview row absence",
            )
        )

    young_limited = _affected_preview_players(
        preview_rows,
        lambda row: _is_young_or_incoming(row)
        and _row_text(row).lower().find("missing") >= 0,
    )
    if young_limited:
        rows.append(
            _promotion_blocker_row(
                blocker_id="source_limited_incoming_young_players",
                blocker_group="confidence_blocker",
                blocker="Source-limited incoming/young players",
                why_it_matters=(
                    "Young players can be driven by projection or prior context before "
                    "NFL evidence is complete, so confidence must stay review/blocked."
                ),
                affected_players_surfaces=young_limited,
                next_action=(
                    "Keep young-player warnings visible; add sourced prospect/NFL "
                    "evidence where available before trusting roster decisions."
                ),
                promotion_blocking_scope="Blocks app promotion",
                blocks_app_promotion=True,
                blocks_final_decision_ready=True,
                evidence_status="derived from v4 preview warnings and unavailable sections",
            )
        )

    if _has_route_unavailable_evidence(preview_rows, source_gap_rows):
        rows.append(
            _promotion_blocker_row(
                blocker_id="unavailable_route_metrics",
                blocker_group="source_limitation",
                blocker="Unavailable route metrics",
                why_it_matters=(
                    "Routes run, route participation, TPRR, and YPRR are not safe "
                    "free/public structured inputs, so v4 must not treat them as real "
                    "evidence."
                ),
                affected_players_surfaces=(
                    "WR/TE review rows; V4 Shadow War Board; v4 receipts; source coverage"
                ),
                next_action=(
                    "Keep route data quarantined and visible. Use licensed structured "
                    "route data later if you choose to upgrade this source."
                ),
                promotion_blocking_scope="Final decision-ready only",
                blocks_app_promotion=False,
                blocks_final_decision_ready=True,
                evidence_status="confirmed source limitation",
            )
        )

    formula_issue_count = _review_issue_count(
        sanity_fixture_rows,
        named_player_rows,
        "formula",
    )
    if formula_issue_count:
        rows.append(
            _promotion_blocker_row(
                blocker_id="open_formula_review_findings",
                blocker_group="formula_blocker",
                blocker="Open formula review findings",
                why_it_matters=(
                    "Formula-classified review findings need a receipt-backed decision "
                    "before v4 can become the live model."
                ),
                affected_players_surfaces=(
                    f"{formula_issue_count} sanity/named-player audit rows; Model Lab; "
                    "V4 Shadow War Board"
                ),
                next_action=(
                    "Review the formula-classified audit rows and either patch with "
                    "fixtures or document as acceptable model disagreement."
                ),
                promotion_blocking_scope="Blocks app promotion",
                blocks_app_promotion=True,
                blocks_final_decision_ready=True,
                evidence_status="derived from sanity/named-player audit classifications",
            )
        )

    if _has_estimated_first_down_projection(preview_rows, source_gap_rows):
        rows.append(
            _promotion_blocker_row(
                blocker_id="estimated_first_down_projection_limitation",
                blocker_group="accepted_limitation",
                blocker="Estimated first-down projections",
                why_it_matters=(
                    "Projected rushing/receiving first downs are estimated from history, "
                    "not direct projection inputs."
                ),
                affected_players_surfaces=(
                    "Projection component; V4 receipts; source coverage; shadow rankings"
                ),
                next_action=(
                    "Keep the estimated label and confidence impact visible; replace "
                    "with direct sourced first-down projections only if available."
                ),
                promotion_blocking_scope="Accepted limitation; keep visible",
                blocks_app_promotion=False,
                blocks_final_decision_ready=False,
                evidence_status="confirmed accepted limitation",
            )
        )

    rows.extend(
        [
            _promotion_blocker_row(
                blocker_id="shadow_app_review_not_accepted",
                blocker_group="ui_blocker",
                blocker="Shadow app review not accepted yet",
                why_it_matters=(
                    "V4 is visible only as a shadow surface. It has not been reviewed "
                    "and accepted as the active app model."
                ),
                affected_players_surfaces=(
                    "V4 Shadow War Board; V4 Shadow My Team; Old vs V4 Comparison; "
                    "v4 receipts"
                ),
                next_action=(
                    "Review the shadow board, receipts, movement rows, and blockers, "
                    "then run the promotion decision gate."
                ),
                promotion_blocking_scope="Blocks app promotion",
                blocks_app_promotion=True,
                blocks_final_decision_ready=True,
                evidence_status="process blocker",
            ),
            _promotion_blocker_row(
                blocker_id="roster_decision_gate_not_unlocked",
                blocker_group="ui_blocker",
                blocker="No roster-decision gate unlock yet",
                why_it_matters=(
                    "Roster decisions cannot be labeled trusted until the formal "
                    "roster-decision gate passes on the promoted model."
                ),
                affected_players_surfaces=(
                    "My Team; War Board; Roster Decisions Ready; decision checklist"
                ),
                next_action=(
                    "After shadow review is accepted, run the v4 roster-decision gate "
                    "and unlock only roster readiness if it truly passes."
                ),
                promotion_blocking_scope="Blocks app promotion",
                blocks_app_promotion=True,
                blocks_final_decision_ready=True,
                evidence_status="gate remains locked",
            ),
        ]
    )

    return sorted(
        rows,
        key=lambda row: (
            _promotion_group_sort_order(str(row["blocker_group"])),
            str(row["blocker"]),
        ),
    )


def build_model_v4_promotion_blocker_summary_rows(
    blocker_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group in MODEL_V4_PROMOTION_BLOCKER_GROUP_ORDER:
        group_rows = [
            row for row in blocker_rows if str(row.get("blocker_group")) == group
        ]
        rows.append(
            {
                "blocker_group": group,
                "blocker_group_label": MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS[group],
                "blocker_count": len(group_rows),
                "app_promotion_blockers": sum(
                    1 for row in group_rows if bool(row.get("blocks_app_promotion"))
                ),
                "final_decision_ready_blockers": sum(
                    1
                    for row in group_rows
                    if bool(row.get("blocks_final_decision_ready"))
                ),
            }
        )
    return rows


def build_model_v4_shadow_war_board_rows(
    preview_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in preview_rows:
        rows.append(
            {
                column: row.get(column, "")
                for column in MODEL_V4_SHADOW_WAR_BOARD_COLUMNS
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            _intish(row.get("overall_preview_rank")) or 9999,
            str(row.get("player") or ""),
        ),
    )


def build_model_v4_shadow_my_team_rows(
    roster_rows: list[object] | tuple[object, ...],
    preview_rows: list[dict[str, object]],
    *,
    top_five_names: tuple[str, ...],
) -> list[dict[str, object]]:
    preview_by_key = _preview_lookup(preview_rows)
    top_five_keys = {_normalized_player_key(player) for player in top_five_names}
    output: list[dict[str, object]] = []
    for roster_row in roster_rows:
        player = _row_value(roster_row, "player_name", "player")
        key = _normalized_player_key(player)
        preview = preview_by_key.get(key) or {}
        match_status = "matched_v4_preview" if preview else "missing_v4_preview"
        top_five_status = (
            "Roster's League-Rank Top Five"
            if key in top_five_keys
            else "Not in Roster's League-Rank Top Five"
        )
        output.append(
            {
                "player": player,
                "position": _row_value(roster_row, "position"),
                "nfl_team": _row_value(roster_row, "nfl_team"),
                "roster_rank": _intish(_row_value(roster_row, "roster_rank")),
                "league_rank": _intish(_row_value(roster_row, "league_rank")),
                "top_five_rule_status": top_five_status,
                "v4_dynasty_asset_value": _blank_if_missing(
                    preview.get("dynasty_asset_value")
                ),
                "v4_roster_decision_value": _blank_if_missing(
                    preview.get("roster_decision_value")
                ),
                "confidence_label": _blank_if_missing(
                    preview.get("confidence_label")
                ),
                "warnings": _blank_if_missing(preview.get("review_warnings")),
                "unavailable_sections": _blank_if_missing(
                    preview.get("unavailable_sections")
                ),
                "v4_match_status": match_status,
                "matched_v4_player": _blank_if_missing(preview.get("player")),
                "rule_context": (
                    "League rank is rule context only; it does not change V4 Dynasty "
                    "Asset Value."
                ),
                "football_value_context": (
                    "V4 Dynasty Asset Value is review-only football value from the "
                    "v4 preview."
                ),
                "warning_context": _shadow_warning_context(preview, match_status),
            }
        )
    return sorted(
        output,
        key=lambda row: (
            _intish(row.get("roster_rank")) or 9999,
            str(row.get("player") or ""),
        ),
    )


def build_model_v4_source_gap_rows(
    source_coverage_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in source_coverage_rows:
        categories = _source_gap_categories(row)
        labels = [
            MODEL_V4_SOURCE_GAP_CATEGORY_LABELS[category]
            for category in categories
        ]
        next_row: dict[str, object] = dict(row)
        next_row["component"] = row.get("section", "")
        next_row["gap_categories"] = "|".join(categories)
        next_row["gap_labels"] = "|".join(labels)
        next_row["gap_count"] = len(
            [
                category
                for category in categories
                if category not in {"covered_evidence", "not_applicable"}
            ]
        )
        next_row["is_data_failure"] = any(
            category == "critical_missing_evidence" for category in categories
        )
        next_row["gap_explanation"] = _source_gap_explanation(categories)
        output.append(next_row)
    return output


def build_model_v4_source_gap_summary_rows(
    source_gap_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], int] = {}
    for row in source_gap_rows:
        component = str(row.get("component") or "")
        position = str(row.get("position") or "")
        for category in str(row.get("gap_categories") or "").split("|"):
            if not category:
                continue
            key = (category, component, position)
            grouped[key] = grouped.get(key, 0) + 1
    rows = [
        {
            "gap_category": category,
            "gap_label": MODEL_V4_SOURCE_GAP_CATEGORY_LABELS.get(category, category),
            "component": component,
            "position": position,
            "row_count": count,
            "is_failure": category == "critical_missing_evidence",
        }
        for (category, component, position), count in grouped.items()
    ]
    return sorted(
        rows,
        key=lambda row: (
            _category_sort_order(str(row["gap_category"])),
            str(row["component"]),
            str(row["position"]),
        ),
    )


def build_model_v4_sanity_fixture_audit_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        audit_status = _fixture_audit_status(row.get("status", ""))
        next_row: dict[str, object] = dict(row)
        next_row["audit_type"] = "Sanity Fixture Dry Run"
        next_row["audit_status"] = audit_status
        next_row["classification"] = row.get("disagreement_classification", "")
        next_row["receipt_drilldown_hint"] = _receipt_drilldown_hint(
            row.get("players", "")
        )
        next_row["decision_ready_unlocked"] = False
        output.append(next_row)
    return _audit_review_first(output)


def build_model_v4_named_player_audit_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        audit_status = _named_player_audit_status(row)
        next_row: dict[str, object] = dict(row)
        next_row["audit_type"] = "Named Player Review"
        next_row["audit_status"] = audit_status
        next_row["expected_behavior"] = (
            "Named player should map cleanly and have receipt-backed Model v4 "
            "preview evidence."
        )
        next_row["actual_behavior"] = _named_player_actual_behavior(row)
        next_row["classification"] = _named_player_classification(row, audit_status)
        next_row["likely_cause"] = _named_player_likely_cause(row, audit_status)
        next_row["next_action"] = _named_player_next_action(row, audit_status)
        next_row["receipt_drilldown_hint"] = _receipt_drilldown_hint(
            row.get("matched_player") or row.get("requested_player") or ""
        )
        next_row["decision_ready_unlocked"] = False
        output.append(next_row)
    return _audit_review_first(output)


def build_model_v4_audit_summary_rows(
    audit_name: str,
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    counts = {"ready": 0, "review": 0, "blocked": 0}
    for row in rows:
        status = str(row.get("audit_status") or "review")
        counts[status if status in counts else "review"] += 1
    return [
        {
            "audit_section": audit_name,
            "ready_count": counts["ready"],
            "review_count": counts["review"],
            "blocked_count": counts["blocked"],
            "decision_ready_unlocked": False,
        }
    ]


def build_model_v4_receipt_drilldown_rows(
    preview_row: dict[str, object],
    receipt_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    player = str(preview_row.get("player") or "")
    expected_contributions = _parse_json_dict(
        str(preview_row.get("component_contributions") or "{}")
    )
    output: list[dict[str, object]] = []
    for row in receipt_rows:
        if str(row.get("player") or "") != player:
            continue
        component = str(row.get("component") or "")
        contribution = _floatish(row.get("contribution"))
        expected = _floatish(expected_contributions.get(component))
        delta = contribution - expected
        if expected == float("-inf"):
            delta = 0.0
        next_row: dict[str, object] = dict(row)
        next_row["receipt_group"] = MODEL_V4_RECEIPT_SECTION_LABELS.get(
            component,
            component.replace("_", " ").title(),
        )
        next_row["audit_highlight"] = _receipt_highlight(row)
        next_row["expected_component_contribution"] = (
            "" if expected == float("-inf") else round(expected, 3)
        )
        next_row["contribution_delta"] = round(delta, 3)
        next_row["reconciles_preview_contribution"] = abs(delta) <= 0.01
        next_row["receipt_sort_order"] = _receipt_sort_order(component)
        next_row["is_placeholder_section"] = False
        output.append(next_row)
    existing_components = {str(row.get("component") or "") for row in output}
    for component in MODEL_V4_RECEIPT_SECTION_ORDER:
        if component in existing_components:
            continue
        output.append(
            _placeholder_receipt_section_row(
                player=player,
                position=str(preview_row.get("position") or ""),
                component=component,
            )
        )
    return sorted(
        output,
        key=lambda row: (
            int(row["receipt_sort_order"]),
            str(row.get("component") or ""),
        ),
    )


def build_model_v4_receipt_reconciliation_row(
    preview_row: dict[str, object],
    receipt_drilldown_rows: list[dict[str, object]],
) -> dict[str, object]:
    preview_score = _floatish(preview_row.get("dynasty_asset_value"))
    receipt_total = 0.0
    for row in receipt_drilldown_rows:
        if row.get("is_placeholder_section"):
            continue
        contribution = _floatish(row.get("contribution"))
        if contribution != float("-inf"):
            receipt_total += contribution
    delta = 0.0 if preview_score == float("-inf") else receipt_total - preview_score
    return {
        "player": preview_row.get("player", ""),
        "dynasty_asset_value": ""
        if preview_score == float("-inf")
        else round(preview_score, 3),
        "receipt_contribution_total": round(receipt_total, 3),
        "score_delta": round(delta, 3),
        "reconciles_preview_score": abs(delta) <= 0.01,
    }


def _preview_lookup(
    preview_rows: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for row in preview_rows:
        player = str(row.get("player") or "")
        key = _normalized_player_key(player)
        if key:
            lookup[key] = row
        base_key = _normalized_player_key(_remove_suffix(player))
        if base_key and base_key not in lookup:
            lookup[base_key] = row
    return lookup


def _row_lookup(
    rows: list[dict[str, object]] | list[dict[str, str]],
    player_key: str,
) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for row in rows:
        player = row.get(player_key, "")
        key = _normalized_player_key(player)
        if key and key not in lookup:
            lookup[key] = dict(row)
        base_key = _normalized_player_key(_remove_suffix(str(player or "")))
        if base_key and base_key not in lookup:
            lookup[base_key] = dict(row)
    return lookup


def _normalized_player_key(player: object) -> str:
    text = _remove_suffix(str(player or ""))
    return "".join(character.lower() for character in text if character.isalnum())


def _remove_suffix(player: str) -> str:
    parts = player.replace(".", "").split()
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    while parts and parts[-1].lower() in suffixes:
        parts.pop()
    return " ".join(parts)


def _row_value(row: object, *keys: str) -> object:
    for key in keys:
        if isinstance(row, dict):
            value = row.get(key)
        else:
            value = getattr(row, key, None)
        if value not in (None, ""):
            return value
    return ""


def _blank_if_missing(value: object) -> object:
    if value in (None, float("-inf")):
        return ""
    return value


def _shadow_warning_context(
    preview: dict[str, object],
    match_status: str,
) -> str:
    if match_status != "matched_v4_preview":
        return "No V4 preview row matched this roster player."
    warnings = str(preview.get("review_warnings") or "").strip()
    unavailable = str(preview.get("unavailable_sections") or "").strip()
    if warnings or unavailable:
        return "Review warnings or unavailable sections must be inspected before trust."
    return "No active V4 warning is shown for this shadow row."


def _promotion_blocker_row(
    *,
    blocker_id: str,
    blocker_group: str,
    blocker: str,
    why_it_matters: str,
    affected_players_surfaces: str,
    next_action: str,
    promotion_blocking_scope: str,
    blocks_app_promotion: bool,
    blocks_final_decision_ready: bool,
    evidence_status: str,
) -> dict[str, object]:
    return {
        "blocker_id": blocker_id,
        "blocker_group": blocker_group,
        "blocker_group_label": MODEL_V4_PROMOTION_BLOCKER_GROUP_LABELS[
            blocker_group
        ],
        "blocker": blocker,
        "why_it_matters": why_it_matters,
        "affected_players_surfaces": affected_players_surfaces,
        "next_action": next_action,
        "promotion_blocking_scope": promotion_blocking_scope,
        "blocks_app_promotion": blocks_app_promotion,
        "blocks_final_decision_ready": blocks_final_decision_ready,
        "evidence_status": evidence_status,
    }


def _promotion_group_sort_order(group: str) -> int:
    try:
        return MODEL_V4_PROMOTION_BLOCKER_GROUP_ORDER.index(group)
    except ValueError:
        return len(MODEL_V4_PROMOTION_BLOCKER_GROUP_ORDER)


def _affected_preview_players(
    preview_rows: list[dict[str, object]],
    predicate: object,
    *,
    limit: int = 8,
) -> str:
    if not callable(predicate):
        return ""
    players = sorted(
        {
            _preview_player_label(row)
            for row in preview_rows
            if predicate(row) and _preview_player_label(row)
        }
    )
    if not players:
        return ""
    suffix = f" (+{len(players) - limit} more)" if len(players) > limit else ""
    return ", ".join(players[:limit]) + suffix


def _preview_player_label(row: dict[str, object]) -> str:
    player = str(row.get("player") or "").strip()
    position = str(row.get("position") or "").strip()
    team = str(row.get("nfl_team") or "").strip()
    context = "/".join(value for value in (position, team) if value)
    return f"{player} ({context})" if player and context else player


def _is_young_or_incoming(row: dict[str, object]) -> bool:
    lifecycle = str(row.get("lifecycle") or "").lower()
    warnings = _row_text(row).lower()
    return any(
        token in lifecycle or token in warnings
        for token in (
            "incoming_rookie",
            "year_one",
            "year_two",
            "year_three",
            "young",
            "rookie",
        )
    )


def _row_text(row: dict[str, object]) -> str:
    return " | ".join(str(value) for value in row.values() if value not in (None, ""))


def _has_route_unavailable_evidence(
    preview_rows: list[dict[str, object]],
    source_gap_rows: list[dict[str, object]],
) -> bool:
    return any(_contains_route_unavailable(_row_text(row)) for row in preview_rows) or any(
        _contains_route_unavailable(_row_text(row)) for row in source_gap_rows
    )


def _contains_route_unavailable(text: str) -> bool:
    normalized = text.lower()
    return any(
        token in normalized
        for token in (
            "route_data_unavailable",
            "route_participation_unavailable",
            "routes_run_unavailable",
            "tprr_unavailable",
            "yprr_unavailable",
            "missing_paid_or_charted_data",
        )
    )


def _review_issue_count(
    sanity_fixture_rows: list[dict[str, object]],
    named_player_rows: list[dict[str, object]],
    token: str,
) -> int:
    normalized = token.lower()
    count = 0
    for row in [*sanity_fixture_rows, *named_player_rows]:
        status = str(row.get("audit_status") or "").lower()
        if status == "ready":
            continue
        classification_text = " | ".join(
            str(row.get(key) or "")
            for key in (
                "classification",
                "disagreement_classification",
                "likely_cause",
                "review_status",
            )
        ).lower()
        if normalized in classification_text:
            count += 1
    return count


def _has_estimated_first_down_projection(
    preview_rows: list[dict[str, object]],
    source_gap_rows: list[dict[str, object]],
) -> bool:
    return any(_contains_estimated_first_down(_row_text(row)) for row in preview_rows) or any(
        _contains_estimated_first_down(_row_text(row)) for row in source_gap_rows
    )


def _contains_estimated_first_down(text: str) -> bool:
    normalized = text.lower()
    return any(
        token in normalized
        for token in (
            "estimated_from_history",
            "projection_first_downs_estimated",
            "first_down_projection_preview_only",
        )
    )


def _read_summary(root: Path, issues: list[str]) -> dict[str, Any]:
    path = root / "v4_preview_summary.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            issues.append(f"{path} did not contain a JSON object.")
        except json.JSONDecodeError as exc:
            issues.append(f"{path} is not valid JSON: {exc}")

    csv_path = root / "v4_preview_summary.csv"
    rows = _read_optional_csv(csv_path, issues)
    summary: dict[str, Any] = {}
    for row in rows:
        metric = row.get("metric", "")
        if metric:
            summary[metric] = row.get("value", "")
    return summary


def _read_optional_csv(path: Path, issues: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        issues.append(f"Missing Model v4 review file: {path}")
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_existing_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _summary_rows(summary: dict[str, Any], root: Path) -> list[dict[str, object]]:
    return [
        {
            "preview_status": summary.get("review_status", "review_only"),
            "formula_version": summary.get("formula_version", ""),
            "preview_engine": summary.get("preview_engine_version", ""),
            "computed_at": summary.get("computed_at", ""),
            "preview_rows": _intish(summary.get("preview_output_rows")),
            "component_rows": _intish(summary.get("component_rows")),
            "receipt_rows": _intish(summary.get("receipt_rows")),
            "source_coverage_rows": _intish(summary.get("source_coverage_rows")),
            "warning_rows": _intish(summary.get("warning_rows")),
            "source_folder": str(root),
        }
    ]


def _gate_rows(summary: dict[str, Any]) -> list[dict[str, object]]:
    checks = (
        (
            "Active rankings unchanged",
            "active_rankings_overwritten",
            "V4 preview must not replace active War Board or My Team rows.",
        ),
        (
            "No app promotion",
            "app_promotion",
            "The app can inspect V4, but normal decision pages must stay on the active model.",
        ),
        (
            "No decision gate unlock",
            "decision_ready_unlocked",
            "Preview visibility cannot make model decisions trusted.",
        ),
        (
            "No draft readiness unlock",
            "draft_ready_unlocked",
            "Draft readiness still needs draft-pool and release-list gates.",
        ),
        (
            "No final money unlock",
            "final_money_ready_unlocked",
            "Final money decisions require every formal gate to pass.",
        ),
    )
    rows: list[dict[str, object]] = []
    for check, key, why in checks:
        unsafe = _boolish(summary.get(key))
        rows.append(
            {
                "check": check,
                "status": "blocked" if unsafe else "ready",
                "review_only_guard": not unsafe,
                "why_it_matters": why,
                "summary_field": key,
                "summary_value": summary.get(key, False),
            }
        )
    return rows


def _rank_preview_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -_floatish(row.get("dynasty_asset_value")),
            row.get("player", ""),
        ),
    )
    position_counts: dict[str, int] = {}
    output: list[dict[str, object]] = []
    for overall_rank, row in enumerate(ranked, start=1):
        position = row.get("position", "")
        position_counts[position] = position_counts.get(position, 0) + 1
        next_row: dict[str, object] = dict(row)
        next_row["overall_preview_rank"] = overall_rank
        next_row["position_preview_rank"] = (
            f"{position}{position_counts[position]}" if position else ""
        )
        output.append(next_row)
    return output


def _review_first(
    rows: list[dict[str, str]],
    status_key: str,
) -> list[dict[str, str]]:
    def sort_key(row: dict[str, str]) -> tuple[int, str]:
        status = row.get(status_key, "")
        priority = 0 if status in {"review", "unmatched", "blocked_missing_input"} else 1
        label = row.get("fixture_id") or row.get("requested_player") or row.get("player") or ""
        return priority, label

    return sorted(rows, key=sort_key)


def _audit_review_first(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    def sort_key(row: dict[str, object]) -> tuple[int, str]:
        status = str(row.get("audit_status") or "review")
        priority = {"blocked": 0, "review": 1, "ready": 2}.get(status, 1)
        severity = {"high": 0, "medium": 1, "low": 2}.get(
            str(row.get("review_severity") or "").lower(),
            3,
        )
        label = str(
            row.get("fixture_id")
            or row.get("requested_player")
            or row.get("matched_player")
            or row.get("player")
            or "",
        )
        return priority, severity, label

    return sorted(rows, key=sort_key)


def _fixture_audit_status(status: str) -> str:
    normalized = status.strip().lower()
    if normalized in {"ready", "pass", "passed"}:
        return "ready"
    if normalized in {"blocked", "blocked_missing_input", "missing_input"}:
        return "blocked"
    return "review"


def _named_player_audit_status(row: dict[str, str]) -> str:
    match_status = str(row.get("match_status") or "").strip().lower()
    confidence = str(row.get("confidence_label") or "").strip().lower()
    review_notes = str(row.get("review_notes") or "").lower()
    if match_status not in {"matched", "ready"}:
        return "blocked"
    if confidence in {"weak", "review", "blocked"} or "weak confidence" in review_notes:
        return "review"
    return "ready"


def _named_player_actual_behavior(row: dict[str, str]) -> str:
    matched = row.get("matched_player") or row.get("requested_player") or "Unknown"
    rank = row.get("overall_rank") or "unranked"
    position_rank = row.get("position_rank") or "unranked"
    value = row.get("dynasty_asset_value") or "missing"
    confidence = row.get("confidence_label") or row.get("confidence") or "missing"
    return (
        f"{matched}: overall rank {rank}, position rank {position_rank}, "
        f"Dynasty Asset Value {value}, confidence {confidence}."
    )


def _named_player_classification(row: dict[str, str], audit_status: str) -> str:
    if audit_status == "blocked":
        return "identity or missing-output issue"
    if audit_status == "review":
        return "confidence or source review"
    if row.get("warnings") or row.get("unavailable_sections"):
        return "receipt-backed with review warnings"
    return "receipt-backed ready row"


def _named_player_likely_cause(row: dict[str, str], audit_status: str) -> str:
    if audit_status == "blocked":
        return row.get("match_status") or "Player did not map to preview output."
    if audit_status == "review":
        return (
            row.get("review_notes")
            or row.get("unavailable_sections")
            or row.get("warnings")
            or "Confidence label requires review."
        )
    return row.get("review_notes") or "No blocking finding in named-player audit."


def _named_player_next_action(row: dict[str, str], audit_status: str) -> str:
    if audit_status == "blocked":
        return "Fix identity/source mapping before trusting this player row."
    player = row.get("matched_player") or row.get("requested_player") or "this player"
    if audit_status == "review":
        return (
            f"Open the v4 receipt drilldown for {player}; fill missing evidence or "
            "document the review risk before formula tuning."
        )
    return f"Use the v4 receipt drilldown for {player} if the ranking feels surprising."


def _receipt_drilldown_hint(players: str) -> str:
    player_list = [player.strip() for player in players.split("|") if player.strip()]
    if not player_list:
        return "Use the Model v4 receipt drilldown for the relevant player."
    if len(player_list) == 1:
        return f"Use the Model v4 receipt drilldown for {player_list[0]}."
    preview = ", ".join(player_list[:3])
    suffix = "..." if len(player_list) > 3 else ""
    return f"Use the Model v4 receipt drilldown for: {preview}{suffix}"


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _comparison_sort_key(
    active: dict[str, object] | None,
    preview: dict[str, object] | None,
) -> tuple[int, int, str]:
    active_rank = _int_or_none((active or {}).get("overall_rank"))
    v4_rank = _int_or_none((preview or {}).get("overall_preview_rank"))
    best_rank = min(
        [rank for rank in (active_rank, v4_rank) if rank is not None] or [9999]
    )
    missing_priority = 0 if active and preview else 1
    player = str((preview or {}).get("player") or (active or {}).get("player") or "")
    return best_rank, missing_priority, player


def _comparison_movement_direction(
    active_rank: int | None,
    v4_rank: int | None,
    rank_delta: int | None,
) -> str:
    if active_rank is None:
        return "missing from active"
    if v4_rank is None:
        return "missing from v4"
    if rank_delta is None or rank_delta == 0:
        return "unchanged"
    if rank_delta > 0:
        return "up in v4"
    return "down in v4"


def _comparison_movement_size(rank_delta: int | None) -> str:
    if rank_delta is None:
        return "unmatched"
    absolute_delta = abs(rank_delta)
    if absolute_delta == 0:
        return "none"
    if absolute_delta <= 5:
        return "small"
    if absolute_delta <= 25:
        return "medium"
    return "large"


def _comparison_movement_reason(
    movement: dict[str, object],
    active: dict[str, object],
    preview: dict[str, object],
) -> str:
    cause = str(
        movement.get("movement_cause")
        or movement.get("movement_reason")
        or ""
    ).lower()
    if "qb suppression" in cause:
        return "QB suppression"
    if "production import" in cause or "native production" in cause:
        return "production repair"
    if "first-down import" in cause or "first down import" in cause:
        return "first-down repair"
    if "usage" in cause or "snap" in cause:
        return "usage/snap repair"
    if "young" in cause and "confidence" in cause:
        return "young-player confidence repair"
    if "young" in cause or "te suppression" in cause or "rb workload" in cause:
        return "formula patch"
    if "formula" in cause or "balance" in cause or "weighting" in cause:
        return "formula patch"
    if "source" in cause or "missing-data" in cause or "confidence" in cause:
        return "source limitation"
    text = "|".join(
        str(value or "").lower()
        for value in (
            preview.get("review_warnings"),
            preview.get("unavailable_sections"),
            active.get("warning_reason"),
            active.get("warning_reasons"),
        )
    )
    if "qb" in str(preview.get("position") or active.get("pos") or "").lower() and (
        "one_qb_suppression" in text or "rushing_qb_exception" in text
    ):
        return "QB suppression"
    if "incoming_rookie" in text and "confidence" in text:
        return "young-player confidence repair"
    if "route_participation_unavailable" in text or "missing" in text:
        return "source limitation"
    return "unknown"


def _comparison_review_note(movement_size: str, movement_reason: str) -> str:
    if movement_size == "large" and movement_reason == "unknown":
        return "Large active-vs-v4 movement has no available explanation; review receipts."
    if movement_size == "unmatched":
        return "Player is missing from one side of the comparison."
    return "Review-only comparison; no active rank replacement."


def _rank_is_top_50(rank: int | None) -> bool:
    return rank is not None and rank <= 50


def _number_or_blank(value: object) -> object:
    try:
        return round(float(str(value)), 3)
    except (TypeError, ValueError):
        return ""


def _int_or_none(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _floatish(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return float("-inf")


def _intish(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _source_gap_categories(row: dict[str, str]) -> tuple[str, ...]:
    text = "|".join(
        str(row.get(key) or "")
        for key in ("section", "source_status", "coverage_status", "warning", "unavailable_reason")
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
    if (
        section == "projection"
        and (
            "missing_projection" in text
            or "local_baseline_projection" in text
            or coverage_status == "missing"
        )
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


def _source_gap_explanation(categories: tuple[str, ...]) -> str:
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


def _category_sort_order(category: str) -> int:
    try:
        return MODEL_V4_SOURCE_GAP_CATEGORY_ORDER.index(category)
    except ValueError:
        return len(MODEL_V4_SOURCE_GAP_CATEGORY_ORDER)


def _parse_json_dict(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _receipt_highlight(row: dict[str, str]) -> str:
    text = "|".join(
        str(row.get(key) or "")
        for key in ("source_status", "warning", "unavailable_reason")
    ).lower()
    highlights: list[str] = []
    if "missing_first_down_projection" in text or "projection_first_downs_missing" in text:
        highlights.append("missing first-down projection")
    if "estimated_from_history" in text or "first_down_projection_preview_only" in text:
        highlights.append("estimated first-down projection")
    if "snap_share_proxy_only_not_route_participation" in text:
        highlights.append("proxy-only snap role")
    if "proxy_only" in text:
        highlights.append("proxy-only evidence")
    if "route_participation_unavailable" in text or "route_data_unavailable" in text:
        highlights.append("unavailable route data")
    if "local_baseline_projection" in text:
        highlights.append("local baseline projection")
    if "young_player_prior_review_only" in text:
        highlights.append("young prior review-only")
    if "incoming_rookie" in text or "incoming-rookie" in text:
        highlights.append("incoming-rookie review-only policy")
    if "missing" in text or str(row.get("unavailable_reason") or "").strip():
        highlights.append("missing source section")
    return "; ".join(dict.fromkeys(highlights))


def _receipt_sort_order(component: str) -> int:
    try:
        return MODEL_V4_RECEIPT_SECTION_ORDER.index(component)
    except ValueError:
        return len(MODEL_V4_RECEIPT_SECTION_ORDER)


def _placeholder_receipt_section_row(
    *,
    player: str,
    position: str,
    component: str,
) -> dict[str, object]:
    label = MODEL_V4_RECEIPT_SECTION_LABELS[component]
    if component == "market_context":
        source_status = "context_only"
        unavailable_reason = "Market context is isolated from V4 private football value."
        warning = "market_not_scored_in_dynasty_asset_value"
    elif component == "league_rank_rule_context":
        source_status = "rule_context_only"
        unavailable_reason = (
            "League rank is a roster-rule signal only and is not scored in V4 "
            "Dynasty Asset Value."
        )
        warning = "league_rank_not_scored_in_dynasty_asset_value"
    else:
        source_status = "missing"
        unavailable_reason = f"{label} receipt section is unavailable for this player."
        warning = "missing_evidence"
    return {
        "player": player,
        "position": position,
        "component": component,
        "raw_fields_used": "",
        "raw_values": "{}",
        "normalized_score": "",
        "source_status": source_status,
        "contribution": 0.0,
        "weight": 0.0,
        "warning": warning,
        "unavailable_reason": unavailable_reason,
        "review_only": True,
        "receipt_group": label,
        "audit_highlight": _receipt_highlight(
            {
                "source_status": source_status,
                "warning": warning,
                "unavailable_reason": unavailable_reason,
            }
        ),
        "expected_component_contribution": "",
        "contribution_delta": 0.0,
        "reconciles_preview_contribution": True,
        "receipt_sort_order": _receipt_sort_order(component),
        "is_placeholder_section": True,
    }
