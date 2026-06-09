from __future__ import annotations

import csv
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.services.model_v4_sprint14b_cut_keep_pressure_service import (
    DEFAULT_14B_OUTPUT_ROOT,
)
from src.services.model_v4_sprint14c_trade_review_service import (
    DEFAULT_OUTPUT_ROOT as TRADE_ROOT,
)
from src.services.model_v4_sprint14d_pick_trade_defer_service import (
    DEFAULT_14D_OUTPUT_ROOT,
)
from src.services.model_v4_sprint14e_rookie_draft_review_service import (
    DEFAULT_14E_OUTPUT_ROOT,
)

SPRINT_14F_VERSION = "model_v4_sprint_14f_june15_decision_board_review_0.1.0"
MANUAL_ONLY_NO_BASELINE = "manual_only_no_exact_model_baseline"
PRESSURE_ROWS = DEFAULT_14B_OUTPUT_ROOT / "cut_keep_pressure_review_rows.csv"
TRADE_AWAY_ROWS = TRADE_ROOT / "trade_away_candidate_review_rows.csv"
LEGACY_TRADE_AWAY_ROWS = (
    Path("local_exports/model_v4/trade_review/latest")
    / "trade_away_candidate_review_rows.csv"
)
PICK_INVENTORY_ROWS = DEFAULT_14D_OUTPUT_ROOT / "niners_pick_inventory_review_rows.csv"
PICK_DEFER_ROWS = DEFAULT_14D_OUTPUT_ROOT / "pick_defer_scenario_review_rows.csv"
ROOKIE_CANDIDATE_ROWS = DEFAULT_14E_OUTPUT_ROOT / "rookie_pick_candidate_review_rows.csv"
ROOKIE_BOARD_ROWS = DEFAULT_14E_OUTPUT_ROOT / "rookie_draft_board_review_rows.csv"
DEFAULT_14F_OUTPUT_ROOT = Path("local_exports/model_v4/june15_decision_board/latest")
DEFAULT_PACKET_ROOT = Path("local_exports/model_v4/audit_packets")
SPRINT14F_DOC = Path("docs/model_v4/SPRINT_14F_JUNE15_DECISION_BOARD.md")
SPRINT14F_AUDIT_PROMPT = Path("docs/model_v4/SPRINT_14F_EXTERNAL_AUDIT_PROMPT.md")

DECISION_BOARD_HEADER = (
    "decision_key",
    "decision_area",
    "entity_label",
    "related_pick_label",
    "position",
    "review_priority",
    "primary_review_band",
    "source_review_score",
    "secondary_review_score",
    "review_context",
    "next_review_step",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

COMPONENT_HEADER = (
    "decision_key",
    "entity_label",
    "component_layer",
    "component_name",
    "component_value",
    "source_status",
    "receipt_pointer",
    "formula_version",
)

RECEIPT_HEADER = (
    "decision_key",
    "entity_label",
    "receipt_layer",
    "receipt_pointer",
    "source_status",
    "formula_version",
)

WARNING_HEADER = (
    "decision_key",
    "entity_label",
    "decision_area",
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
class June15DecisionBoardResult:
    decision_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class June15DecisionBoardPaths:
    decision_rows: Path
    components: Path
    receipts: Path
    warnings: Path
    summary: Path
    doc: Path
    audit_prompt: Path
    audit_packet: Path


def build_june15_decision_board_outputs(
    *,
    pressure_rows_path: str | Path = PRESSURE_ROWS,
    trade_away_rows_path: str | Path = TRADE_AWAY_ROWS,
    pick_inventory_path: str | Path = PICK_INVENTORY_ROWS,
    pick_defer_path: str | Path = PICK_DEFER_ROWS,
    rookie_candidate_path: str | Path = ROOKIE_CANDIDATE_ROWS,
) -> June15DecisionBoardResult:
    pressure_rows = _read_rows(Path(pressure_rows_path))
    trade_rows = _read_rows(
        _first_existing_path(Path(trade_away_rows_path), LEGACY_TRADE_AWAY_ROWS)
    )
    pick_rows = _read_rows(Path(pick_inventory_path))
    defer_rows = _read_rows(Path(pick_defer_path))
    rookie_rows = _read_rows(Path(rookie_candidate_path))

    trade_by_player = {row["player_name"]: row for row in trade_rows}
    defer_by_pick = {row["current_pick_label"]: row for row in defer_rows}

    roster_decisions = tuple(
        _roster_decision_row(row, trade_by_player.get(row["player_name"], {}))
        for row in pressure_rows
    )
    pick_decisions = tuple(
        _pick_decision_row(row, defer_by_pick.get(row["pick_label"], {}))
        for row in pick_rows
    )
    rookie_decisions = tuple(_rookie_candidate_decision_row(row) for row in rookie_rows)
    decision_rows = (*roster_decisions, *pick_decisions, *rookie_decisions)
    component_rows = tuple(_component_rows(decision_rows))
    receipt_rows = tuple(_receipt_row(row) for row in decision_rows)
    warning_rows = (
        *_decision_warnings(decision_rows),
        _global_warning(),
    )
    summary_rows = _summary_rows(decision_rows)
    summary = {
        "review_status": "review_only",
        "decision_rows": len(decision_rows),
        "roster_decision_rows": len(roster_decisions),
        "pick_decision_rows": len(pick_decisions),
        "rookie_candidate_rows": len(rookie_decisions),
        "final_recommendations_created": False,
        "war_board_changed": False,
        "my_team_changed": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return June15DecisionBoardResult(
        decision_rows=decision_rows,
        component_rows=component_rows,
        receipt_rows=receipt_rows,
        warning_rows=warning_rows,
        summary_rows=summary_rows,
        summary=summary,
    )


def write_june15_decision_board_outputs(
    *,
    output_root: str | Path = DEFAULT_14F_OUTPUT_ROOT,
    packet_root: str | Path = DEFAULT_PACKET_ROOT,
    result: June15DecisionBoardResult | None = None,
) -> June15DecisionBoardPaths:
    result = result or build_june15_decision_board_outputs()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    packet_path = Path(packet_root) / "sprint14f_june15_decision_board_audit_packet_20260518.zip"
    paths = June15DecisionBoardPaths(
        decision_rows=output / "june15_decision_board_review_rows.csv",
        components=output / "june15_decision_board_component_rows.csv",
        receipts=output / "june15_decision_board_receipts.csv",
        warnings=output / "june15_decision_board_warnings.csv",
        summary=output / "june15_decision_board_summary.csv",
        doc=SPRINT14F_DOC,
        audit_prompt=SPRINT14F_AUDIT_PROMPT,
        audit_packet=packet_path,
    )
    _write_csv(paths.decision_rows, DECISION_BOARD_HEADER, result.decision_rows)
    _write_csv(paths.components, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    _write_text(paths.doc, _doc(result, paths))
    _write_text(paths.audit_prompt, _audit_prompt(paths))
    _write_packet(paths, packet_path)
    return paths


def _roster_decision_row(
    pressure: dict[str, str],
    trade: dict[str, str],
) -> dict[str, object]:
    band = _roster_band(pressure, trade)
    context = (
        f"pressure={pressure.get('pressure_band', '')}; "
        f"trade_away={trade.get('trade_away_review_band', 'missing_trade_context')}"
    )
    warnings = [
        "review_only_no_final_decision_recommendation",
        *(pressure.get("warning_flags", "").split("|") if pressure.get("warning_flags") else []),
        *(trade.get("warning_flags", "").split("|") if trade.get("warning_flags") else []),
    ]
    return {
        "decision_key": f"june15:roster:{pressure['pressure_key']}",
        "decision_area": "roster_pressure_trade_context",
        "entity_label": pressure["player_name"],
        "related_pick_label": "",
        "position": pressure["position"],
        "review_priority": _roster_priority(pressure, trade),
        "primary_review_band": band,
        "source_review_score": pressure["pressure_score"],
        "secondary_review_score": pressure["dynasty_asset_value_review_score"],
        "review_context": context,
        "next_review_step": _roster_next_step(band),
        "allowed_use": "review_only_june15_decision_context_not_final_action",
        "blocked_use": "do_not_use_as_final_cut_keep_trade_or_draft_recommendation",
        "warning_flags": "|".join(dict.fromkeys(flag for flag in warnings if flag)),
        "formula_version": SPRINT_14F_VERSION,
    }


def _pick_decision_row(
    pick: dict[str, str],
    defer: dict[str, str],
) -> dict[str, object]:
    band = _pick_band(pick, defer)
    warnings = [
        "review_only_no_final_decision_recommendation",
        *(pick.get("warning_flags", "").split("|") if pick.get("warning_flags") else []),
        *(defer.get("warning_flags", "").split("|") if defer.get("warning_flags") else []),
    ]
    if pick.get("baseline_match_status") == "missing_pick_value_baseline":
        warnings.append(MANUAL_ONLY_NO_BASELINE)
    return {
        "decision_key": f"june15:pick:{pick['pick_review_key']}",
        "decision_area": "pick_trade_defer_context",
        "entity_label": pick["pick_label"],
        "related_pick_label": pick["pick_label"],
        "position": "PICK",
        "review_priority": _pick_priority(pick, defer),
        "primary_review_band": band,
        "source_review_score": pick.get("pick_value_review_score", ""),
        "secondary_review_score": defer.get("value_delta_review", ""),
        "review_context": _pick_context(pick, defer),
        "next_review_step": _pick_next_step(band),
        "allowed_use": "review_only_june15_decision_context_not_final_action",
        "blocked_use": "do_not_use_as_final_cut_keep_trade_or_draft_recommendation",
        "warning_flags": "|".join(dict.fromkeys(flag for flag in warnings if flag)),
        "formula_version": SPRINT_14F_VERSION,
    }


def _rookie_candidate_decision_row(row: dict[str, str]) -> dict[str, object]:
    band = _rookie_band(row)
    warnings = [
        "review_only_no_final_decision_recommendation",
        *(row.get("warning_flags", "").split("|") if row.get("warning_flags") else []),
    ]
    return {
        "decision_key": f"june15:rookie:{row['pick_candidate_key']}",
        "decision_area": "rookie_pick_window_context",
        "entity_label": row["prospect_name"],
        "related_pick_label": row["pick_label"],
        "position": row["position"],
        "review_priority": _rookie_priority(row),
        "primary_review_band": band,
        "source_review_score": row["league_format_adjusted_score"],
        "secondary_review_score": row["pick_value_gap_review"],
        "review_context": (
            f"candidate_rank={row['candidate_board_rank']}; "
            f"window={row['candidate_window_band']}; fit={row['roster_fit_context']}"
        ),
        "next_review_step": _rookie_next_step(band),
        "allowed_use": "review_only_june15_decision_context_not_final_action",
        "blocked_use": "do_not_use_as_final_cut_keep_trade_or_draft_recommendation",
        "warning_flags": "|".join(dict.fromkeys(flag for flag in warnings if flag)),
        "formula_version": SPRINT_14F_VERSION,
    }


def _roster_band(pressure: dict[str, str], trade: dict[str, str]) -> str:
    if pressure.get("pressure_band") == "required_pressure_zone_review":
        return "roster_pressure_line_review"
    trade_band = trade.get("trade_away_review_band", "")
    if trade_band in {"pressure_shop_watch_review", "liquidity_check_context_review"}:
        return "trade_market_before_cut_context_review"
    if trade_band == "depth_liquidity_watch_review":
        return "depth_liquidity_context_review"
    if trade_band == "hold_core_unless_overpay_review":
        return "core_hold_context_review"
    return "roster_context_review"


def _pick_band(pick: dict[str, str], defer: dict[str, str]) -> str:
    if pick.get("baseline_match_status") == "missing_pick_value_baseline":
        return "pick_baseline_missing_review"
    if defer.get("defer_review_band") == "future_first_defer_premium_context_review":
        return "future_first_defer_premium_context_review"
    if defer.get("defer_review_band"):
        return "pick_defer_context_review"
    return "pick_inventory_context_review"


def _rookie_band(row: dict[str, str]) -> str:
    if row.get("candidate_window_band") == "pick_value_aligned_context_review":
        return "rookie_candidate_aligned_context_review"
    if row.get("candidate_window_band") == "tier_gap_context_review":
        return "rookie_candidate_tier_gap_context_review"
    if row.get("candidate_window_band") == "late_watchlist_no_pick_baseline_review":
        return "rookie_late_watchlist_context_review"
    return "rookie_candidate_gap_context_review"


def _roster_priority(pressure: dict[str, str], trade: dict[str, str]) -> float:
    priority = _float(pressure.get("pressure_score"), 0.0) or 0.0
    if pressure.get("pressure_band") == "required_pressure_zone_review":
        priority += 40.0
    if trade.get("trade_away_review_band") == "pressure_shop_watch_review":
        priority += 15.0
    return round(priority, 4)


def _pick_priority(pick: dict[str, str], defer: dict[str, str]) -> float:
    value = _float(pick.get("pick_value_review_score"), 0.0) or 0.0
    delta = _float(defer.get("value_delta_review"), 0.0) or 0.0
    if pick.get("baseline_match_status") == "missing_pick_value_baseline":
        return 20.0
    return round(value + delta, 4)


def _rookie_priority(row: dict[str, str]) -> float:
    score = _float(row.get("league_format_adjusted_score"), 0.0) or 0.0
    rank_penalty = (int(row.get("candidate_board_rank") or 0) - 1) * 0.1
    return round(score - rank_penalty, 4)


def _roster_next_step(band: str) -> str:
    if band == "roster_pressure_line_review":
        return "Compare trade-away and rookie replacement context before any human cut call."
    if band == "trade_market_before_cut_context_review":
        return "Inspect liquidity context before any human roster decision."
    if band == "depth_liquidity_context_review":
        return "Inspect as depth/liquidity context only."
    if band == "core_hold_context_review":
        return "Core roster context row; compare only if later audited context creates a question."
    return "Roster context row for human review."


def _pick_next_step(band: str) -> str:
    if band == "pick_baseline_missing_review":
        return (
            "Manual-only: no exact model baseline exists. Do not include in pick-defer, "
            "draft, trade, or cut-equivalence math."
        )
    if band == "future_first_defer_premium_context_review":
        return "Audit owner risk and premium before any defer discussion."
    if band == "pick_defer_context_review":
        return "Review defer context alongside rookie candidate board."
    return "Review pick inventory context only."


def _rookie_next_step(band: str) -> str:
    if band == "rookie_candidate_aligned_context_review":
        return "Review as candidate-window context before final draft-room decision."
    if band == "rookie_candidate_tier_gap_context_review":
        return "Review tier gap and source warnings before draft-room use."
    if band == "rookie_late_watchlist_context_review":
        return "Treat as late watchlist only until pick baseline is repaired."
    return "Review gap and warnings before any draft-room use."


def _pick_context(pick: dict[str, str], defer: dict[str, str]) -> str:
    if pick.get("baseline_match_status") == "missing_pick_value_baseline":
        return (
            f"pick={pick['pick_label']}; {MANUAL_ONLY_NO_BASELINE}; "
            "exact_model_equivalent=blocked"
        )
    if not defer:
        return f"pick={pick['pick_label']}; defer_context=missing_or_not_applicable"
    return (
        f"pick={pick['pick_label']}; future={defer.get('future_pick_label', '')}; "
        f"delta={defer.get('value_delta_review', '')}"
    )


def _component_rows(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        pointer = _pointer_for_area(str(row["decision_area"]))
        output.extend(
            [
                _component(
                    row["decision_key"],
                    row["entity_label"],
                    row["decision_area"],
                    "primary_review_band",
                    row["primary_review_band"],
                    pointer,
                ),
                _component(
                    row["decision_key"],
                    row["entity_label"],
                    row["decision_area"],
                    "source_review_score",
                    row["source_review_score"],
                    pointer,
                ),
                _component(
                    row["decision_key"],
                    row["entity_label"],
                    row["decision_area"],
                    "review_priority",
                    row["review_priority"],
                    pointer,
                ),
            ]
        )
    return tuple(output)


def _component(
    key: object,
    label: object,
    layer: object,
    name: str,
    value: object,
    pointer: Path,
) -> dict[str, object]:
    return {
        "decision_key": key,
        "entity_label": label,
        "component_layer": layer,
        "component_name": name,
        "component_value": value,
        "source_status": "review_only_june15_decision_context",
        "receipt_pointer": str(pointer),
        "formula_version": SPRINT_14F_VERSION,
    }


def _receipt_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "decision_key": row["decision_key"],
        "entity_label": row["entity_label"],
        "receipt_layer": "sprint_14f_june15_decision_board",
        "receipt_pointer": str(_pointer_for_area(str(row["decision_area"]))),
        "source_status": "review_only_not_final_decision_recommendation",
        "formula_version": SPRINT_14F_VERSION,
    }


def _decision_warnings(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    warnings: list[dict[str, object]] = []
    for row in rows:
        band = str(row["primary_review_band"])
        if band in {
            "roster_pressure_line_review",
            "pick_baseline_missing_review",
            "rookie_candidate_gap_context_review",
            "rookie_late_watchlist_context_review",
        }:
            warnings.append(
                _warning(
                    row["decision_key"],
                    row["entity_label"],
                    row["decision_area"],
                    "review",
                    band,
                    "Decision-board row requires review before any final action.",
                    "Use as input to audited final decision discussion only.",
                )
            )
    return tuple(warnings)


def _global_warning() -> dict[str, object]:
    return _warning(
        "sprint_14f",
        "June 15 decision board",
        "all",
        "review",
        "no_final_decisions_or_mutations_created",
        "Sprint 14F creates a review-only checkpoint board.",
        "Run audit before treating any row as final roster, trade, or draft advice.",
    )


def _warning(
    key: object,
    label: object,
    area: object,
    severity: str,
    code: str,
    detail: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "decision_key": key,
        "entity_label": label,
        "decision_area": area,
        "severity": severity,
        "warning_code": code,
        "warning_detail": detail,
        "next_action": next_action,
        "formula_version": SPRINT_14F_VERSION,
    }


def _summary_rows(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    output = [
        _summary("decision_rows", len(rows), str(DEFAULT_14F_OUTPUT_ROOT)),
        _summary("final_recommendations_created", False, "sprint_14f_guardrail"),
        _summary("war_board_changed", False, "sprint_14f_guardrail"),
        _summary("my_team_changed", False, "sprint_14f_guardrail"),
    ]
    output.extend(
        _summary(
            f"decision_area_count:{area}",
            sum(1 for row in rows if row["decision_area"] == area),
            str(DEFAULT_14F_OUTPUT_ROOT),
        )
        for area in sorted({str(row["decision_area"]) for row in rows})
    )
    output.extend(
        _summary(
            f"review_band_count:{band}",
            sum(1 for row in rows if row["primary_review_band"] == band),
            str(DEFAULT_14F_OUTPUT_ROOT),
        )
        for band in sorted({str(row["primary_review_band"]) for row in rows})
    )
    return tuple(output)


def _summary(key: str, value: object, source: str) -> dict[str, object]:
    return {
        "summary_key": key,
        "summary_value": value,
        "source": source,
        "allowed_use": "review_only_june15_decision_board_summary",
        "formula_version": SPRINT_14F_VERSION,
    }


def _doc(result: June15DecisionBoardResult, paths: June15DecisionBoardPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14F June 15 Decision Board",
            "",
            "Sprint 14F combines roster pressure, trade context, pick defer context, "
            "and rookie pick windows into one review-only checkpoint board. It does "
            "not create final cut, keep, trade, defer, or draft recommendations.",
            "",
            "## Outputs",
            "",
            f"- `{paths.decision_rows}`",
            f"- `{paths.components}`",
            f"- `{paths.receipts}`",
            f"- `{paths.warnings}`",
            f"- `{paths.summary}`",
            "",
            "## Summary",
            "",
            f"- Decision rows: {result.summary['decision_rows']}",
            f"- Roster rows: {result.summary['roster_decision_rows']}",
            f"- Pick rows: {result.summary['pick_decision_rows']}",
            f"- Rookie candidate rows: {result.summary['rookie_candidate_rows']}",
            "- Final recommendations created: False",
            "- My Team changed: False",
            "- War Board changed: False",
        ]
    ) + "\n"


def _audit_prompt(paths: June15DecisionBoardPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14F External Audit Prompt",
            "",
            "Audit Sprint 14F for Model v4. The packet is a review-only June 15 "
            "decision-board checkpoint.",
            "",
            "Verify:",
            "- roster pressure rows preserve 14B/14C context without final cut/sell calls",
            "- pick rows preserve 14D defer context without final trade/defer calls",
            "- rookie rows preserve 14E candidate windows without final draft calls",
            "- My Team, War Board, active rankings, readiness gates, and app promotion "
            "did not change",
            "- review priorities are explainable and do not override source warnings",
            "- missing pick baselines remain blocked from fake math",
            "- market/ADP/projection/ranking fields do not drive private football value",
            "- whether the board is ready for a human final-decision conversation",
            "",
            "Verdict options:",
            "- ready_for_human_final_decision_review",
            "- needs_roster_decision_board_repair",
            "- needs_pick_or_rookie_board_repair",
            "- needs_source_or_leakage_repair",
            "",
            "Primary files:",
            f"- `{paths.decision_rows}`",
            f"- `{paths.components}`",
            f"- `{paths.warnings}`",
        ]
    ) + "\n"


def _write_packet(paths: June15DecisionBoardPaths, packet_path: Path) -> None:
    files = (
        paths.decision_rows,
        paths.components,
        paths.receipts,
        paths.warnings,
        paths.summary,
        paths.doc,
        paths.audit_prompt,
        PRESSURE_ROWS,
        TRADE_AWAY_ROWS,
        PICK_INVENTORY_ROWS,
        PICK_DEFER_ROWS,
        ROOKIE_CANDIDATE_ROWS,
        ROOKIE_BOARD_ROWS,
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    if packet_path.exists():
        packet_path.unlink()
    manifest = packet_path.with_suffix(".manifest.json")
    manifest.write_text(
        "{\n"
        f'  "created_at_utc": "{datetime.now(UTC).isoformat()}",\n'
        '  "packet_type": "model_v4_sprint14f_june15_decision_board_audit",\n'
        '  "review_only": true\n'
        "}\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (*files, manifest):
            if path.exists():
                archive.write(path, path.as_posix())


def _pointer_for_area(area: str) -> Path:
    if area == "roster_pressure_trade_context":
        return PRESSURE_ROWS
    if area == "pick_trade_defer_context":
        return PICK_INVENTORY_ROWS
    if area == "rookie_pick_window_context":
        return ROOKIE_CANDIDATE_ROWS
    return DEFAULT_14F_OUTPUT_ROOT


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


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
    if header == DECISION_BOARD_HEADER:
        return tuple(
            sorted(
                rows,
                key=lambda row: _float(row.get("review_priority"), 0.0) or 0.0,
                reverse=True,
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
