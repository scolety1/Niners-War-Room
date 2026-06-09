from __future__ import annotations

import csv
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.services.model_v4_sprint14_15_calibration_service import DEFAULT_OUTPUT_ROOT
from src.services.model_v4_sprint14d_pick_trade_defer_service import (
    DEFAULT_14D_OUTPUT_ROOT,
)

SPRINT_14E_VERSION = "model_v4_sprint_14e_rookie_draft_review_0.1.0"
PROSPECT_ROWS = Path("local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv")
PICK_INVENTORY_ROWS = DEFAULT_14D_OUTPUT_ROOT / "niners_pick_inventory_review_rows.csv"
PICK_DEFER_ROWS = DEFAULT_14D_OUTPUT_ROOT / "pick_defer_scenario_review_rows.csv"
DEADLINE_CONTRACT = DEFAULT_OUTPUT_ROOT / "niners_deadline_contract.csv"
ROSTER_STATE_ROWS = DEFAULT_OUTPUT_ROOT / "niners_roster_state_review.csv"
DEFAULT_14E_OUTPUT_ROOT = Path("local_exports/model_v4/rookie_draft_review/latest")
DEFAULT_PACKET_ROOT = Path("local_exports/model_v4/audit_packets")
SPRINT14E_DOC = Path("docs/model_v4/SPRINT_14E_ROOKIE_DRAFT_REVIEW.md")
SPRINT14E_AUDIT_PROMPT = Path("docs/model_v4/SPRINT_14E_EXTERNAL_AUDIT_PROMPT.md")

POSITION_FORMAT_FACTORS = {
    "RB": 1.0,
    "WR": 1.0,
    "TE": 0.82,
    "QB": 0.62,
}

DRAFTABLE_COMPONENT_WEIGHT_THRESHOLD = 0.75
LOW_EVIDENCE_COMPONENT_WEIGHT_THRESHOLD = 0.5
LOW_EVIDENCE_SCORE_CAP = 50.0
WATCHLIST_WARNING_FLAGS = {
    "missing_prospect_or_college_evidence",
    "missing_production_component",
    "missing_market_share_component",
    "missing_landing_context_review",
}

ROOKIE_BOARD_HEADER = (
    "rookie_board_key",
    "board_rank",
    "prospect_name",
    "normalized_player_name",
    "position",
    "college",
    "nfl_team",
    "draft_year",
    "prospect_private_value_review_score",
    "format_adjustment_factor",
    "league_format_adjusted_score",
    "confidence_cap",
    "component_weight_available",
    "evidence_status",
    "roster_fit_context",
    "draft_board_band",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

PICK_CANDIDATE_HEADER = (
    "pick_candidate_key",
    "pick_label",
    "pick_value_review_score",
    "pick_tier_label",
    "candidate_board_rank",
    "prospect_name",
    "position",
    "college",
    "nfl_team",
    "league_format_adjusted_score",
    "pick_value_gap_review",
    "candidate_window_band",
    "roster_fit_context",
    "review_rationale",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

COMPONENT_HEADER = (
    "draft_review_key",
    "entity_label",
    "component_layer",
    "component_name",
    "component_value",
    "source_status",
    "receipt_pointer",
    "formula_version",
)

RECEIPT_HEADER = (
    "draft_review_key",
    "entity_label",
    "receipt_layer",
    "receipt_pointer",
    "source_status",
    "formula_version",
)

WARNING_HEADER = (
    "draft_review_key",
    "entity_label",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "formula_version",
)

SUMMARY_HEADER = (
    "summary_key",
    "summary_value",
    "source",
    "allowed_use",
    "formula_version",
)


@dataclass(frozen=True)
class RookieDraftReviewResult:
    rookie_board_rows: tuple[dict[str, object], ...]
    pick_candidate_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class RookieDraftReviewPaths:
    rookie_board_rows: Path
    pick_candidate_rows: Path
    components: Path
    receipts: Path
    warnings: Path
    summary: Path
    doc: Path
    audit_prompt: Path
    audit_packet: Path


def build_rookie_draft_review_outputs(
    *,
    prospect_rows_path: str | Path = PROSPECT_ROWS,
    pick_inventory_path: str | Path = PICK_INVENTORY_ROWS,
    roster_state_path: str | Path = ROSTER_STATE_ROWS,
) -> RookieDraftReviewResult:
    prospect_rows = _read_rows(Path(prospect_rows_path))
    pick_rows = _read_rows(Path(pick_inventory_path))
    roster_rows = _read_rows(Path(roster_state_path))
    roster_counts = _position_counts(roster_rows)
    board_rows = _rookie_board_rows(prospect_rows, roster_counts)
    pick_candidate_rows = tuple(
        candidate
        for pick in pick_rows
        for candidate in _pick_candidate_rows(pick, board_rows)
    )
    component_rows = (
        *_rookie_board_components(board_rows),
        *_pick_candidate_components(pick_candidate_rows),
    )
    receipt_rows = (
        *_rookie_board_receipts(board_rows),
        *_pick_candidate_receipts(pick_candidate_rows),
    )
    warning_rows = (
        *_rookie_board_warnings(board_rows),
        *_pick_candidate_warnings(pick_candidate_rows),
        _global_warning(),
    )
    summary_rows = _summary_rows(board_rows, pick_candidate_rows)
    summary = {
        "review_status": "review_only",
        "rookie_board_rows": len(board_rows),
        "pick_candidate_rows": len(pick_candidate_rows),
        "final_rookie_pick_recommendations_created": False,
        "war_board_changed": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return RookieDraftReviewResult(
        rookie_board_rows=board_rows,
        pick_candidate_rows=pick_candidate_rows,
        component_rows=tuple(component_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        summary_rows=summary_rows,
        summary=summary,
    )


def write_rookie_draft_review_outputs(
    *,
    output_root: str | Path = DEFAULT_14E_OUTPUT_ROOT,
    packet_root: str | Path = DEFAULT_PACKET_ROOT,
    result: RookieDraftReviewResult | None = None,
) -> RookieDraftReviewPaths:
    result = result or build_rookie_draft_review_outputs()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    packet_path = Path(packet_root) / "sprint14e_rookie_draft_review_audit_packet_20260518.zip"
    paths = RookieDraftReviewPaths(
        rookie_board_rows=output / "rookie_draft_board_review_rows.csv",
        pick_candidate_rows=output / "rookie_pick_candidate_review_rows.csv",
        components=output / "rookie_draft_component_rows.csv",
        receipts=output / "rookie_draft_receipts.csv",
        warnings=output / "rookie_draft_warnings.csv",
        summary=output / "rookie_draft_summary.csv",
        doc=SPRINT14E_DOC,
        audit_prompt=SPRINT14E_AUDIT_PROMPT,
        audit_packet=packet_path,
    )
    _write_csv(paths.rookie_board_rows, ROOKIE_BOARD_HEADER, result.rookie_board_rows)
    _write_csv(paths.pick_candidate_rows, PICK_CANDIDATE_HEADER, result.pick_candidate_rows)
    _write_csv(paths.components, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    _write_text(paths.doc, _doc(result, paths))
    _write_text(paths.audit_prompt, _audit_prompt(paths))
    _write_packet(paths, packet_path)
    return paths


def _rookie_board_rows(
    rows: tuple[dict[str, str], ...],
    roster_counts: dict[str, int],
) -> tuple[dict[str, object], ...]:
    built: list[dict[str, object]] = []
    for row in rows:
        if row.get("draft_year") != "2026":
            continue
        position = row.get("position", "")
        if position not in POSITION_FORMAT_FACTORS:
            continue
        raw_score = _float(row.get("prospect_private_value_review_score"))
        if raw_score is None:
            continue
        factor = POSITION_FORMAT_FACTORS[position]
        component_weight = _float(row.get("component_weight_available"), 0.0) or 0.0
        warnings = [
            "review_only_no_final_rookie_pick_recommendation",
            "market_context_excluded_from_private_value",
        ]
        source_warnings = row.get("warning_flags", "")
        if source_warnings:
            warnings.extend(source_warnings.split("|"))
        evidence_status = _evidence_status(
            component_weight=component_weight,
            nfl_team=row.get("nfl_team", ""),
            warning_flags=warnings,
        )
        adjusted_score = round(
            _evidence_adjusted_score(
                raw_score=raw_score,
                position_factor=factor,
                component_weight=component_weight,
                evidence_status=evidence_status,
            ),
            4,
        )
        if evidence_status == "watchlist_data_incomplete":
            warnings.append("watchlist_or_data_incomplete_context_review")
        elif evidence_status == "manual_scout_source_review":
            warnings.append("manual_scout_source_review")
        built.append(
            {
                "rookie_board_key": row["canonical_prospect_key"],
                "board_rank": 0,
                "prospect_name": row["prospect_name"],
                "normalized_player_name": row["normalized_player_name"],
                "position": position,
                "college": row["college"],
                "nfl_team": row["nfl_team"],
                "draft_year": row["draft_year"],
                "prospect_private_value_review_score": raw_score,
                "format_adjustment_factor": factor,
                "league_format_adjusted_score": adjusted_score,
                "confidence_cap": row["confidence_cap"],
                "component_weight_available": row["component_weight_available"],
                "evidence_status": evidence_status,
                "roster_fit_context": _roster_fit_context(position, roster_counts),
                "draft_board_band": "",
                "allowed_use": "review_only_rookie_board_context_not_final_pick",
                "blocked_use": "do_not_use_as_final_rookie_draft_recommendation",
                "warning_flags": "|".join(dict.fromkeys(warnings)),
                "formula_version": SPRINT_14E_VERSION,
            }
        )
    ranked = sorted(
        built,
        key=lambda row: (
            _float(row["league_format_adjusted_score"], 0.0) or 0.0,
            str(row["prospect_name"]),
        ),
        reverse=True,
    )
    return tuple(
        {
            **row,
            "board_rank": index,
            "draft_board_band": _draft_board_band(index, str(row["evidence_status"])),
        }
        for index, row in enumerate(ranked, start=1)
    )


def _pick_candidate_rows(
    pick: dict[str, str],
    board_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    start, end, limit = _candidate_window(pick)
    candidates = [
        row
        for row in board_rows
        if start <= int(row["board_rank"]) <= end
        and row.get("evidence_status") != "watchlist_data_incomplete"
    ][:limit]
    return tuple(_pick_candidate_row(pick, row) for row in candidates)


def _pick_candidate_row(
    pick: dict[str, str],
    prospect: dict[str, object],
) -> dict[str, object]:
    pick_value = _float(pick.get("pick_value_review_score"))
    candidate_score = _float(prospect["league_format_adjusted_score"], 0.0) or 0.0
    gap = "" if pick_value is None else round(candidate_score - pick_value, 4)
    band = _candidate_window_band(pick, gap)
    warnings = [
        "review_only_no_final_rookie_pick_recommendation",
        "market_context_excluded_from_private_value",
    ]
    if pick.get("baseline_match_status") == "missing_pick_value_baseline":
        warnings.append("pick_value_baseline_missing")
    if prospect.get("warning_flags"):
        warnings.extend(str(prospect["warning_flags"]).split("|"))
    return {
        "pick_candidate_key": f"{pick['pick_review_key']}:{prospect['rookie_board_key']}",
        "pick_label": pick["pick_label"],
        "pick_value_review_score": pick.get("pick_value_review_score", ""),
        "pick_tier_label": pick.get("tier_label", ""),
        "candidate_board_rank": prospect["board_rank"],
        "prospect_name": prospect["prospect_name"],
        "position": prospect["position"],
        "college": prospect["college"],
        "nfl_team": prospect["nfl_team"],
        "league_format_adjusted_score": candidate_score,
        "pick_value_gap_review": gap,
        "candidate_window_band": band,
        "roster_fit_context": prospect["roster_fit_context"],
        "review_rationale": _candidate_rationale(band),
        "allowed_use": "review_only_rookie_pick_candidate_context_not_final_selection",
        "blocked_use": "do_not_use_as_final_rookie_draft_recommendation",
        "warning_flags": "|".join(dict.fromkeys(warnings)),
        "formula_version": SPRINT_14E_VERSION,
    }


def _candidate_window(pick: dict[str, str]) -> tuple[int, int, int]:
    round_number = pick.get("round")
    slot = int(pick.get("slot") or 0)
    if pick.get("baseline_match_status") == "missing_pick_value_baseline":
        return 50, 90, 12
    if round_number == "1":
        end = 8 if slot <= 3 else 10
        return 1, end, end
    if round_number == "2" and slot <= 4:
        return 8, 28, 21
    if round_number == "2":
        return 12, 36, 25
    return 35, 70, 16


def _candidate_window_band(pick: dict[str, str], gap: float | str) -> str:
    if pick.get("baseline_match_status") == "missing_pick_value_baseline":
        return "late_watchlist_no_pick_baseline_review"
    if isinstance(gap, str):
        return "missing_pick_gap_review"
    if gap >= -5.0:
        return "pick_value_aligned_context_review"
    if gap >= -20.0:
        return "tier_gap_context_review"
    return "significant_pick_value_gap_review"


def _candidate_rationale(band: str) -> str:
    if band == "pick_value_aligned_context_review":
        return "Candidate score is near pick baseline; still requires draft-room audit."
    if band == "tier_gap_context_review":
        return "Candidate fits the review window but trails pick baseline."
    if band == "late_watchlist_no_pick_baseline_review":
        return "Late-pick watchlist only because this pick lacks a value baseline."
    if band == "missing_pick_gap_review":
        return "Pick-value gap unavailable; keep review-only."
    return "Candidate is in the window but has a large review gap to pick baseline."


def _evidence_status(
    *,
    component_weight: float,
    nfl_team: str,
    warning_flags: list[str],
) -> str:
    flag_set = set(warning_flags)
    if component_weight < LOW_EVIDENCE_COMPONENT_WEIGHT_THRESHOLD:
        return "watchlist_data_incomplete"
    if component_weight < DRAFTABLE_COMPONENT_WEIGHT_THRESHOLD:
        return "manual_scout_source_review"
    if WATCHLIST_WARNING_FLAGS.intersection(flag_set):
        return "watchlist_data_incomplete"
    if not str(nfl_team or "").strip():
        return "watchlist_data_incomplete"
    if "identity_review_cap" in flag_set or "partial_or_quarantined_join_cap" in flag_set:
        return "manual_scout_source_review"
    return "draftable_review"


def _evidence_adjusted_score(
    *,
    raw_score: float,
    position_factor: float,
    component_weight: float,
    evidence_status: str,
) -> float:
    base_score = raw_score * position_factor * component_weight
    if evidence_status == "watchlist_data_incomplete":
        return min(base_score, LOW_EVIDENCE_SCORE_CAP)
    return base_score


def _roster_fit_context(position: str, roster_counts: dict[str, int]) -> str:
    count = roster_counts.get(position, 0)
    if position == "QB":
        return "one_qb_depth_crowded_context" if count >= 2 else "one_qb_depth_open_context"
    if position == "TE":
        return "no_premium_te_crowded_context" if count >= 3 else "te_depth_context"
    if position == "WR":
        return "wr_room_crowded_context" if count >= 9 else "wr_room_fit_context"
    if position == "RB":
        return "possible_rb_roster_fit_context" if count <= 6 else "rb_room_crowded_context"
    return "position_fit_context_unavailable"


def _draft_board_band(rank: int, evidence_status: str) -> str:
    if evidence_status == "watchlist_data_incomplete":
        return "watchlist_or_data_incomplete_context_review"
    if evidence_status == "manual_scout_source_review":
        return "manual_scout_context_review"
    if rank <= 10:
        return "first_round_board_context_review"
    if rank <= 30:
        return "second_round_board_context_review"
    if rank <= 60:
        return "depth_board_context_review"
    return "watchlist_context_review"


def _rookie_board_components(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        output.extend(
            [
                _component(
                    row["rookie_board_key"],
                    row["prospect_name"],
                    "rookie_board",
                    "prospect_private_value_review_score",
                    row["prospect_private_value_review_score"],
                    PROSPECT_ROWS,
                ),
                _component(
                    row["rookie_board_key"],
                    row["prospect_name"],
                    "rookie_board",
                    "format_adjustment_factor",
                    row["format_adjustment_factor"],
                    DEADLINE_CONTRACT,
                ),
                _component(
                    row["rookie_board_key"],
                    row["prospect_name"],
                    "rookie_board",
                    "evidence_status",
                    row["evidence_status"],
                    PROSPECT_ROWS,
                ),
                _component(
                    row["rookie_board_key"],
                    row["prospect_name"],
                    "rookie_board",
                    "component_weight_available",
                    row["component_weight_available"],
                    PROSPECT_ROWS,
                ),
                _component(
                    row["rookie_board_key"],
                    row["prospect_name"],
                    "rookie_board",
                    "roster_fit_context",
                    row["roster_fit_context"],
                    ROSTER_STATE_ROWS,
                ),
            ]
        )
    return tuple(output)


def _pick_candidate_components(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        output.extend(
            [
                _component(
                    row["pick_candidate_key"],
                    row["prospect_name"],
                    "pick_candidate",
                    "pick_value_review_score",
                    row["pick_value_review_score"],
                    PICK_INVENTORY_ROWS,
                ),
                _component(
                    row["pick_candidate_key"],
                    row["prospect_name"],
                    "pick_candidate",
                    "league_format_adjusted_score",
                    row["league_format_adjusted_score"],
                    PROSPECT_ROWS,
                ),
                _component(
                    row["pick_candidate_key"],
                    row["prospect_name"],
                    "pick_candidate",
                    "pick_value_gap_review",
                    row["pick_value_gap_review"],
                    PICK_INVENTORY_ROWS,
                ),
            ]
        )
    return tuple(output)


def _component(
    key: object,
    label: object,
    layer: str,
    name: str,
    value: object,
    pointer: Path,
) -> dict[str, object]:
    return {
        "draft_review_key": key,
        "entity_label": label,
        "component_layer": layer,
        "component_name": name,
        "component_value": value,
        "source_status": "review_only_rookie_draft_context",
        "receipt_pointer": str(pointer),
        "formula_version": SPRINT_14E_VERSION,
    }


def _rookie_board_receipts(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(row["rookie_board_key"], row["prospect_name"], PROSPECT_ROWS)
        for row in rows
    )


def _pick_candidate_receipts(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(row["pick_candidate_key"], row["prospect_name"], PICK_INVENTORY_ROWS)
        for row in rows
    )


def _receipt(key: object, label: object, pointer: Path) -> dict[str, object]:
    return {
        "draft_review_key": key,
        "entity_label": label,
        "receipt_layer": "sprint_14e_rookie_draft_review",
        "receipt_pointer": str(pointer),
        "source_status": "review_only_not_final_rookie_pick_recommendation",
        "formula_version": SPRINT_14E_VERSION,
    }


def _rookie_board_warnings(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _warning(
            row["rookie_board_key"],
            row["prospect_name"],
            "review",
            "rookie_board_context_not_final_ranking",
            "Rookie board row is league-format review context only.",
            "Audit before using in any final rookie draft decision board.",
        )
        for row in rows[:10]
    )


def _pick_candidate_warnings(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    warnings: list[dict[str, object]] = []
    for row in rows:
        if row["candidate_window_band"] in {
            "significant_pick_value_gap_review",
            "late_watchlist_no_pick_baseline_review",
        }:
            warnings.append(
                _warning(
                    row["pick_candidate_key"],
                    row["prospect_name"],
                    "review",
                    str(row["candidate_window_band"]),
                    "Candidate row needs review before any draft-room use.",
                    "Use Sprint 14F to combine draft, trade, and cut pressure context.",
                )
            )
    return tuple(warnings)


def _global_warning() -> dict[str, object]:
    return _warning(
        "sprint_14e",
        "Rookie draft review layer",
        "review",
        "no_final_rookie_draft_recommendations_created",
        "Sprint 14E creates review-only draft board and pick-candidate context.",
        "Run audit before Sprint 14F final June 15 decision board work.",
    )


def _warning(
    key: object,
    label: object,
    severity: str,
    code: str,
    detail: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "draft_review_key": key,
        "entity_label": label,
        "severity": severity,
        "warning_code": code,
        "warning_detail": detail,
        "next_action": next_action,
        "formula_version": SPRINT_14E_VERSION,
    }


def _summary_rows(
    board_rows: tuple[dict[str, object], ...],
    candidate_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows = [
        _summary("rookie_board_rows", len(board_rows), str(PROSPECT_ROWS)),
        _summary("pick_candidate_rows", len(candidate_rows), str(PICK_INVENTORY_ROWS)),
        _summary("final_rookie_pick_recommendations_created", False, "sprint_14e_guardrail"),
        _summary("war_board_changed", False, "sprint_14e_guardrail"),
    ]
    rows.extend(
        _summary(
            f"position_count:{position}",
            sum(1 for row in board_rows if row["position"] == position),
            str(PROSPECT_ROWS),
        )
        for position in sorted({str(row["position"]) for row in board_rows})
    )
    rows.extend(
        _summary(
            f"candidate_band_count:{band}",
            sum(1 for row in candidate_rows if row["candidate_window_band"] == band),
            str(DEFAULT_14E_OUTPUT_ROOT),
        )
        for band in sorted({str(row["candidate_window_band"]) for row in candidate_rows})
    )
    return tuple(rows)


def _summary(key: str, value: object, source: str) -> dict[str, object]:
    return {
        "summary_key": key,
        "summary_value": value,
        "source": source,
        "allowed_use": "review_only_rookie_draft_summary",
        "formula_version": SPRINT_14E_VERSION,
    }


def _doc(result: RookieDraftReviewResult, paths: RookieDraftReviewPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14E Rookie Draft Review",
            "",
            "Sprint 14E creates a review-only rookie draft board and pick-candidate "
            "windows for the Niners' current picks. It does not create final rookie "
            "pick recommendations, draft-room instructions, or War Board mutations.",
            "",
            "## Outputs",
            "",
            f"- `{paths.rookie_board_rows}`",
            f"- `{paths.pick_candidate_rows}`",
            f"- `{paths.components}`",
            f"- `{paths.receipts}`",
            f"- `{paths.warnings}`",
            f"- `{paths.summary}`",
            "",
            "## Summary",
            "",
            f"- Rookie board rows: {result.summary['rookie_board_rows']}",
            f"- Pick-candidate rows: {result.summary['pick_candidate_rows']}",
            "- Final rookie pick recommendations created: False",
            "- War Board changed: False",
        ]
    ) + "\n"


def _audit_prompt(paths: RookieDraftReviewPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14E External Audit Prompt",
            "",
            "Audit Sprint 14E for Model v4. The attached outputs are review-only.",
            "",
            "Verify:",
            "- rookie board rows use admitted prospect value, not market/ranking/projection inputs",
            "- 10-team 1QB and no-TE-premium adjustments are visible and reasonable",
            "- pick-candidate windows are context, not final draft recommendations",
            "- Niners owned-pick context comes from Sprint 14D",
            "- missing pick baselines remain warnings, not fake values",
            "- roster-fit context is descriptive and does not override evidence",
            "- no final rookie picks, War Board changes, readiness unlock, or app "
            "promotion occurred",
            "- whether Sprint 14F June 15 decision board can begin review-only",
            "",
            "Verdict options:",
            "- ready_for_sprint_14f_review_only_decision_board_work",
            "- needs_rookie_board_repair",
            "- needs_pick_candidate_window_repair",
            "- needs_source_or_leakage_repair",
            "",
            "Primary files:",
            f"- `{paths.rookie_board_rows}`",
            f"- `{paths.pick_candidate_rows}`",
            f"- `{paths.warnings}`",
        ]
    ) + "\n"


def _write_packet(paths: RookieDraftReviewPaths, packet_path: Path) -> None:
    files = (
        paths.rookie_board_rows,
        paths.pick_candidate_rows,
        paths.components,
        paths.receipts,
        paths.warnings,
        paths.summary,
        paths.doc,
        paths.audit_prompt,
        PROSPECT_ROWS,
        PICK_INVENTORY_ROWS,
        PICK_DEFER_ROWS,
        DEADLINE_CONTRACT,
        ROSTER_STATE_ROWS,
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    if packet_path.exists():
        packet_path.unlink()
    manifest = packet_path.with_suffix(".manifest.json")
    manifest.write_text(
        "{\n"
        f'  "created_at_utc": "{datetime.now(UTC).isoformat()}",\n'
        '  "packet_type": "model_v4_sprint14e_rookie_draft_review_audit",\n'
        '  "review_only": true\n'
        "}\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (*files, manifest):
            if path.exists():
                archive.write(path, path.as_posix())


def _position_counts(rows: tuple[dict[str, str], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        position = row.get("position", "")
        counts[position] = counts.get(position, 0) + 1
    return counts


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = _sort_rows(rows, header)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)


def _sort_rows(
    rows: tuple[dict[str, object], ...],
    header: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    if header == ROOKIE_BOARD_HEADER:
        return tuple(sorted(rows, key=lambda row: int(str(row["board_rank"]))))
    if header == PICK_CANDIDATE_HEADER:
        return tuple(
            sorted(
                rows,
                key=lambda row: (
                    str(row["pick_label"]),
                    int(str(row["candidate_board_rank"])),
                ),
            )
        )
    return rows


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
