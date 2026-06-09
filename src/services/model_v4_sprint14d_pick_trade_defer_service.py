from __future__ import annotations

import csv
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.model_v4_sprint14_15_calibration_service import DEFAULT_OUTPUT_ROOT
from src.services.model_v4_sprint14c_trade_review_service import DEFAULT_OUTPUT_ROOT as TRADE_ROOT

SPRINT_14D_VERSION = "model_v4_sprint_14d_pick_trade_defer_review_0.1.0"
DATA_PACK_ROOT = Path(DEFAULT_DATA_PACK)
FUTURE_PICKS = DATA_PACK_ROOT / "fact_future_picks.csv"
DEADLINE_CONTRACT = DEFAULT_OUTPUT_ROOT / "niners_deadline_contract.csv"
PICK_BASELINES = Path("local_exports/model_v4/pick_values/latest/pick_value_baselines_review.csv")
TRADE_AWAY_ROWS = TRADE_ROOT / "trade_away_candidate_review_rows.csv"
TRADE_FOR_ROWS = TRADE_ROOT / "trade_for_candidate_review_rows.csv"
DEFAULT_14D_OUTPUT_ROOT = Path("local_exports/model_v4/pick_trade_defer/latest")
DEFAULT_PACKET_ROOT = Path("local_exports/model_v4/audit_packets")
SPRINT14D_DOC = Path("docs/model_v4/SPRINT_14D_PICK_TRADE_DEFER_REVIEW.md")
SPRINT14D_AUDIT_PROMPT = Path("docs/model_v4/SPRINT_14D_EXTERNAL_AUDIT_PROMPT.md")
MANUAL_ONLY_NO_BASELINE = "manual_only_no_exact_model_baseline"

PICK_INVENTORY_HEADER = (
    "pick_review_key",
    "pick_label",
    "pick_year",
    "round",
    "slot",
    "overall_pick",
    "original_team_name",
    "current_team_name",
    "current_owner_name",
    "pick_value_review_score",
    "tier_label",
    "baseline_match_status",
    "roster_pressure_context",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

DEFER_SCENARIO_HEADER = (
    "defer_scenario_key",
    "current_pick_label",
    "current_pick_value_review_score",
    "future_pick_label",
    "future_pick_value_review_score",
    "value_delta_review",
    "current_tier_label",
    "future_tier_label",
    "defer_review_band",
    "review_rationale",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

FUTURE_PICK_CONTEXT_HEADER = (
    "future_pick_context_key",
    "future_pick_label",
    "season",
    "round",
    "slot",
    "pick_value_review_score",
    "tier_label",
    "future_pick_context_band",
    "review_rationale",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

COMPONENT_HEADER = (
    "pick_review_key",
    "entity_label",
    "component_layer",
    "component_name",
    "component_value",
    "source_status",
    "receipt_pointer",
    "formula_version",
)

RECEIPT_HEADER = (
    "pick_review_key",
    "entity_label",
    "receipt_layer",
    "receipt_pointer",
    "source_status",
    "formula_version",
)

WARNING_HEADER = (
    "pick_review_key",
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
class PickTradeDeferResult:
    pick_inventory_rows: tuple[dict[str, object], ...]
    defer_scenario_rows: tuple[dict[str, object], ...]
    future_pick_context_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class PickTradeDeferPaths:
    pick_inventory_rows: Path
    defer_scenario_rows: Path
    future_pick_context_rows: Path
    components: Path
    receipts: Path
    warnings: Path
    summary: Path
    doc: Path
    audit_prompt: Path
    audit_packet: Path


def build_pick_trade_defer_outputs(
    *,
    future_picks_path: str | Path = FUTURE_PICKS,
    pick_baselines_path: str | Path = PICK_BASELINES,
    contract_path: str | Path = DEADLINE_CONTRACT,
) -> PickTradeDeferResult:
    future_picks = _read_rows(Path(future_picks_path))
    baselines = _read_rows(Path(pick_baselines_path))
    contract_rows = _read_rows(Path(contract_path))
    baseline_by_label = {row["pick_label"]: row for row in baselines}
    current_pick_count = _contract_value(contract_rows, "current_rookie_pick_count", "unknown")
    pressure_count = _contract_value(contract_rows, "minimum_roster_pressure_count", "unknown")
    roster_pressure_context = (
        f"{current_pick_count} current rookie picks vs {pressure_count} minimum roster "
        "pressure slot"
    )

    niners_picks = tuple(
        row
        for row in future_picks
        if row.get("current_team_name") == "Niners" and row.get("pick_year") == "2026"
    )
    pick_inventory_rows = tuple(
        _pick_inventory_row(row, baseline_by_label, roster_pressure_context)
        for row in niners_picks
    )
    defer_scenario_rows = tuple(
        scenario
        for row in pick_inventory_rows
        if (scenario := _defer_scenario_row(row, baseline_by_label)) is not None
    )
    future_pick_context_rows = tuple(
        _future_pick_context_row(row)
        for row in baselines
        if row.get("season") == "2027" and row.get("round") in {"1", "2"}
    )
    component_rows = (
        *_pick_inventory_components(pick_inventory_rows),
        *_defer_scenario_components(defer_scenario_rows),
        *_future_pick_context_components(future_pick_context_rows),
    )
    receipt_rows = (
        *_pick_inventory_receipts(pick_inventory_rows),
        *_defer_scenario_receipts(defer_scenario_rows),
        *_future_pick_context_receipts(future_pick_context_rows),
    )
    warning_rows = (
        *_pick_inventory_warnings(pick_inventory_rows),
        *_defer_scenario_warnings(defer_scenario_rows),
        _global_warning(),
    )
    summary_rows = _summary_rows(
        pick_inventory_rows,
        defer_scenario_rows,
        future_pick_context_rows,
    )
    summary = {
        "review_status": "review_only",
        "niners_pick_rows": len(pick_inventory_rows),
        "defer_scenario_rows": len(defer_scenario_rows),
        "future_pick_context_rows": len(future_pick_context_rows),
        "pick_trade_recommendations_created": False,
        "trade_packages_created": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return PickTradeDeferResult(
        pick_inventory_rows=pick_inventory_rows,
        defer_scenario_rows=defer_scenario_rows,
        future_pick_context_rows=future_pick_context_rows,
        component_rows=tuple(component_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        summary_rows=summary_rows,
        summary=summary,
    )


def write_pick_trade_defer_outputs(
    *,
    output_root: str | Path = DEFAULT_14D_OUTPUT_ROOT,
    packet_root: str | Path = DEFAULT_PACKET_ROOT,
    result: PickTradeDeferResult | None = None,
) -> PickTradeDeferPaths:
    result = result or build_pick_trade_defer_outputs()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    packet_path = Path(packet_root) / "sprint14d_pick_trade_defer_audit_packet_20260518.zip"
    paths = PickTradeDeferPaths(
        pick_inventory_rows=output / "niners_pick_inventory_review_rows.csv",
        defer_scenario_rows=output / "pick_defer_scenario_review_rows.csv",
        future_pick_context_rows=output / "future_pick_context_review_rows.csv",
        components=output / "pick_trade_defer_component_rows.csv",
        receipts=output / "pick_trade_defer_receipts.csv",
        warnings=output / "pick_trade_defer_warnings.csv",
        summary=output / "pick_trade_defer_summary.csv",
        doc=SPRINT14D_DOC,
        audit_prompt=SPRINT14D_AUDIT_PROMPT,
        audit_packet=packet_path,
    )
    _write_csv(paths.pick_inventory_rows, PICK_INVENTORY_HEADER, result.pick_inventory_rows)
    _write_csv(paths.defer_scenario_rows, DEFER_SCENARIO_HEADER, result.defer_scenario_rows)
    _write_csv(
        paths.future_pick_context_rows,
        FUTURE_PICK_CONTEXT_HEADER,
        result.future_pick_context_rows,
    )
    _write_csv(paths.components, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    _write_text(paths.doc, _doc(result, paths))
    _write_text(paths.audit_prompt, _audit_prompt(paths))
    _write_packet(paths, packet_path)
    return paths


def _pick_inventory_row(
    row: dict[str, str],
    baseline_by_label: dict[str, dict[str, str]],
    roster_pressure_context: str,
) -> dict[str, object]:
    baseline = baseline_by_label.get(row["pick_label"], {})
    match_status = "matched_pick_value_baseline" if baseline else "missing_pick_value_baseline"
    warnings = ["review_only_no_pick_trade_recommendation"]
    if not baseline:
        warnings.append("pick_value_baseline_missing")
        warnings.append(MANUAL_ONLY_NO_BASELINE)
    return {
        "pick_review_key": f"niners_pick:{row['pick_label'].replace(' ', ':')}",
        "pick_label": row["pick_label"],
        "pick_year": row["pick_year"],
        "round": row["round"],
        "slot": row["slot"],
        "overall_pick": row["overall_pick"],
        "original_team_name": row["original_team_name"],
        "current_team_name": row["current_team_name"],
        "current_owner_name": row["current_owner_name"],
        "pick_value_review_score": baseline.get("pick_value_review_score", ""),
        "tier_label": baseline.get("tier_label", MANUAL_ONLY_NO_BASELINE),
        "baseline_match_status": match_status,
        "roster_pressure_context": roster_pressure_context,
        "allowed_use": "review_only_pick_inventory_not_trade_recommendation",
        "blocked_use": "do_not_use_as_pick_trade_recommendation_or_offer",
        "warning_flags": "|".join(warnings),
        "formula_version": SPRINT_14D_VERSION,
    }


def _defer_scenario_row(
    current_pick: dict[str, object],
    baseline_by_label: dict[str, dict[str, str]],
) -> dict[str, object] | None:
    if current_pick["baseline_match_status"] != "matched_pick_value_baseline":
        return None
    current_label = str(current_pick["pick_label"])
    future_label = current_label.replace("2026", "2027", 1)
    future = baseline_by_label.get(future_label)
    if not future:
        return None
    current_value = _float(current_pick.get("pick_value_review_score"), 0.0) or 0.0
    future_value = _float(future.get("pick_value_review_score"), 0.0) or 0.0
    delta = round(future_value - current_value, 3)
    band = _defer_band(current_pick, delta)
    warnings = [
        "review_only_no_pick_trade_recommendation",
        "heuristic_pick_curve_requires_audit",
    ]
    if delta > 0:
        warnings.append("future_pick_baseline_higher_than_current_same_slot")
    return {
        "defer_scenario_key": f"defer:{current_label.replace(' ', ':')}:to:{future_label}",
        "current_pick_label": current_label,
        "current_pick_value_review_score": current_value,
        "future_pick_label": future_label,
        "future_pick_value_review_score": future_value,
        "value_delta_review": delta,
        "current_tier_label": current_pick["tier_label"],
        "future_tier_label": future["tier_label"],
        "defer_review_band": band,
        "review_rationale": _defer_rationale(band),
        "allowed_use": "review_only_pick_defer_context_not_recommendation",
        "blocked_use": "do_not_use_as_pick_trade_recommendation_or_offer",
        "warning_flags": "|".join(warnings),
        "formula_version": SPRINT_14D_VERSION,
    }


def _future_pick_context_row(row: dict[str, str]) -> dict[str, object]:
    value = _float(row.get("pick_value_review_score"), 0.0) or 0.0
    band = _future_pick_context_band(row, value)
    return {
        "future_pick_context_key": f"future_context:{row['pick_label'].replace(' ', ':')}",
        "future_pick_label": row["pick_label"],
        "season": row["season"],
        "round": row["round"],
        "slot": row["pick_slot"],
        "pick_value_review_score": value,
        "tier_label": row["tier_label"],
        "future_pick_context_band": band,
        "review_rationale": _future_pick_context_rationale(band),
        "allowed_use": "review_only_future_pick_context_not_trade_target_recommendation",
        "blocked_use": "do_not_use_as_pick_trade_recommendation_or_offer",
        "warning_flags": (
            "review_only_no_pick_trade_recommendation|heuristic_pick_curve_requires_audit"
        ),
        "formula_version": SPRINT_14D_VERSION,
    }


def _defer_band(current_pick: dict[str, object], delta: float) -> str:
    round_number = str(current_pick["round"])
    if round_number == "1" and delta >= 5.0:
        return "future_first_defer_premium_context_review"
    if delta > 0.0:
        return "future_pick_defer_context_review"
    if delta == 0.0:
        return "same_slot_neutral_context_review"
    return "current_pick_stability_context_review"


def _defer_rationale(band: str) -> str:
    if band == "future_first_defer_premium_context_review":
        return "Future same-slot first has higher review baseline; audit premium and owner risk."
    if band == "future_pick_defer_context_review":
        return "Future same-slot pick has positive review delta; not an accept instruction."
    if band == "same_slot_neutral_context_review":
        return "Same-slot baseline is neutral; roster timeline and owner risk still matter."
    return "Current pick baseline is stronger or safer in this scenario."


def _future_pick_context_band(row: dict[str, str], value: float) -> str:
    if row.get("round") == "1" and value >= 95.0:
        return "premium_future_first_context_review"
    if row.get("round") == "1":
        return "future_first_context_review"
    if value >= 75.0:
        return "strong_future_second_context_review"
    return "future_second_context_review"


def _future_pick_context_rationale(band: str) -> str:
    if band == "premium_future_first_context_review":
        return "High future first baseline; review owner risk before any package logic."
    if band == "future_first_context_review":
        return "Future first baseline context only; not a trade target recommendation."
    if band == "strong_future_second_context_review":
        return "Future second has meaningful baseline context; audit liquidity separately."
    return "Depth future pick context only."


def _pick_inventory_components(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        output.extend(
            [
                _component(
                    row["pick_review_key"],
                    row["pick_label"],
                    "pick_inventory",
                    "pick_value_review_score",
                    row["pick_value_review_score"],
                    PICK_BASELINES,
                ),
                _component(
                    row["pick_review_key"],
                    row["pick_label"],
                    "pick_inventory",
                    "baseline_match_status",
                    row["baseline_match_status"],
                    PICK_BASELINES,
                ),
                _component(
                    row["pick_review_key"],
                    row["pick_label"],
                    "pick_inventory",
                    "roster_pressure_context",
                    row["roster_pressure_context"],
                    DEADLINE_CONTRACT,
                ),
            ]
        )
    return tuple(output)


def _defer_scenario_components(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        output.extend(
            [
                _component(
                    row["defer_scenario_key"],
                    row["current_pick_label"],
                    "pick_defer",
                    "current_pick_value_review_score",
                    row["current_pick_value_review_score"],
                    PICK_BASELINES,
                ),
                _component(
                    row["defer_scenario_key"],
                    row["future_pick_label"],
                    "pick_defer",
                    "future_pick_value_review_score",
                    row["future_pick_value_review_score"],
                    PICK_BASELINES,
                ),
                _component(
                    row["defer_scenario_key"],
                    row["future_pick_label"],
                    "pick_defer",
                    "value_delta_review",
                    row["value_delta_review"],
                    PICK_BASELINES,
                ),
            ]
        )
    return tuple(output)


def _future_pick_context_components(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _component(
            row["future_pick_context_key"],
            row["future_pick_label"],
            "future_pick_context",
            "pick_value_review_score",
            row["pick_value_review_score"],
            PICK_BASELINES,
        )
        for row in rows
    )


def _component(
    key: object,
    label: object,
    layer: str,
    name: str,
    value: object,
    pointer: Path,
) -> dict[str, object]:
    return {
        "pick_review_key": key,
        "entity_label": label,
        "component_layer": layer,
        "component_name": name,
        "component_value": value,
        "source_status": "review_only_pick_trade_defer_context",
        "receipt_pointer": str(pointer),
        "formula_version": SPRINT_14D_VERSION,
    }


def _pick_inventory_receipts(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(row["pick_review_key"], row["pick_label"], FUTURE_PICKS)
        for row in rows
    )


def _defer_scenario_receipts(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(row["defer_scenario_key"], row["current_pick_label"], PICK_BASELINES)
        for row in rows
    )


def _future_pick_context_receipts(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(row["future_pick_context_key"], row["future_pick_label"], PICK_BASELINES)
        for row in rows
    )


def _receipt(key: object, label: object, pointer: Path) -> dict[str, object]:
    return {
        "pick_review_key": key,
        "entity_label": label,
        "receipt_layer": "sprint_14d_pick_trade_defer",
        "receipt_pointer": str(pointer),
        "source_status": "review_only_not_pick_trade_recommendation",
        "formula_version": SPRINT_14D_VERSION,
    }


def _pick_inventory_warnings(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    warnings = [
        _warning(
            row["pick_review_key"],
            row["pick_label"],
            "review",
            "pick_value_baseline_missing",
            "Owned pick has no Sprint 12/13 pick baseline row.",
            "Keep this pick out of defer math until a baseline exists.",
        )
        for row in rows
        if row["baseline_match_status"] == "missing_pick_value_baseline"
    ]
    return tuple(warnings)


def _defer_scenario_warnings(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _warning(
            row["defer_scenario_key"],
            row["current_pick_label"],
            "review",
            "pick_defer_context_not_trade_recommendation",
            "Scenario compares same-slot pick baselines only.",
            "Audit owner risk, liquidity, packages, and rookie board before any action.",
        )
        for row in rows
    )


def _global_warning() -> dict[str, object]:
    return _warning(
        "sprint_14d",
        "Pick trade/defer layer",
        "review",
        "no_pick_trade_recommendations_or_packages_created",
        "Sprint 14D creates pick and defer context surfaces only.",
        "Run audit before Sprint 14E/F decision recommendation work.",
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
        "pick_review_key": key,
        "entity_label": label,
        "severity": severity,
        "warning_code": code,
        "warning_detail": detail,
        "next_action": next_action,
        "formula_version": SPRINT_14D_VERSION,
    }


def _summary_rows(
    inventory_rows: tuple[dict[str, object], ...],
    scenario_rows: tuple[dict[str, object], ...],
    future_context_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows = [
        _summary("niners_pick_rows", len(inventory_rows), str(FUTURE_PICKS)),
        _summary("defer_scenario_rows", len(scenario_rows), str(PICK_BASELINES)),
        _summary("future_pick_context_rows", len(future_context_rows), str(PICK_BASELINES)),
        _summary("pick_trade_recommendations_created", False, "sprint_14d_guardrail"),
        _summary("trade_packages_created", False, "sprint_14d_guardrail"),
    ]
    rows.extend(
        _summary(
            f"defer_band_count:{band}",
            sum(1 for row in scenario_rows if row["defer_review_band"] == band),
            str(DEFAULT_14D_OUTPUT_ROOT),
        )
        for band in sorted({str(row["defer_review_band"]) for row in scenario_rows})
    )
    return tuple(rows)


def _summary(key: str, value: object, source: str) -> dict[str, object]:
    return {
        "summary_key": key,
        "summary_value": value,
        "source": source,
        "allowed_use": "review_only_pick_trade_defer_summary",
        "formula_version": SPRINT_14D_VERSION,
    }


def _doc(result: PickTradeDeferResult, paths: PickTradeDeferPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14D Pick Trade And Defer Review",
            "",
            "Sprint 14D creates review-only pick inventory, future-pick context, and "
            "same-slot defer scenario surfaces. It does not create pick-trade "
            "recommendations, accepted deals, rejected deals, or trade packages.",
            "",
            "## Outputs",
            "",
            f"- `{paths.pick_inventory_rows}`",
            f"- `{paths.defer_scenario_rows}`",
            f"- `{paths.future_pick_context_rows}`",
            f"- `{paths.components}`",
            f"- `{paths.receipts}`",
            f"- `{paths.warnings}`",
            f"- `{paths.summary}`",
            "",
            "## Summary",
            "",
            f"- Niners pick rows: {result.summary['niners_pick_rows']}",
            f"- Defer scenario rows: {result.summary['defer_scenario_rows']}",
            f"- Future pick context rows: {result.summary['future_pick_context_rows']}",
            "- Pick trade recommendations created: False",
            "- Trade packages created: False",
        ]
    ) + "\n"


def _audit_prompt(paths: PickTradeDeferPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14D External Audit Prompt",
            "",
            "Audit Sprint 14D for Model v4. The attached outputs are review-only.",
            "",
            "Verify:",
            "- Niners pick inventory matches the source future-picks file",
            "- missing pick baselines are flagged and excluded from defer math",
            "- same-slot defer scenarios are context only, not trade recommendations",
            "- future pick context rows do not become target recommendations",
            "- no trade packages, accept/reject calls, or final decision advice was created",
            "- pick baselines remain review-only heuristic outputs requiring audit",
            "- roster-pressure context is visible but not overused",
            "- no market/ADP/projection/ranking leakage drives private football value",
            "- no active rankings, My Team, War Board, readiness gates, or app promotion changed",
            "- whether Sprint 14E rookie draft recommendations can begin review-only",
            "",
            "Verdict options:",
            "- ready_for_sprint_14e_review_only_rookie_draft_work",
            "- needs_pick_baseline_repair",
            "- needs_defer_context_repair",
            "- needs_source_or_contract_repair",
            "",
            "Primary files:",
            f"- `{paths.pick_inventory_rows}`",
            f"- `{paths.defer_scenario_rows}`",
            f"- `{paths.future_pick_context_rows}`",
            f"- `{paths.warnings}`",
        ]
    ) + "\n"


def _write_packet(paths: PickTradeDeferPaths, packet_path: Path) -> None:
    files = (
        paths.pick_inventory_rows,
        paths.defer_scenario_rows,
        paths.future_pick_context_rows,
        paths.components,
        paths.receipts,
        paths.warnings,
        paths.summary,
        paths.doc,
        paths.audit_prompt,
        FUTURE_PICKS,
        PICK_BASELINES,
        DEADLINE_CONTRACT,
        TRADE_AWAY_ROWS,
        TRADE_FOR_ROWS,
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    if packet_path.exists():
        packet_path.unlink()
    manifest = packet_path.with_suffix(".manifest.json")
    manifest.write_text(
        "{\n"
        f'  "created_at_utc": "{datetime.now(UTC).isoformat()}",\n'
        '  "packet_type": "model_v4_sprint14d_pick_trade_defer_audit",\n'
        '  "review_only": true\n'
        "}\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (*files, manifest):
            if path.exists():
                archive.write(path, path.as_posix())


def _contract_value(rows: tuple[dict[str, str], ...], key: str, default: str) -> str:
    for row in rows:
        if row.get("contract_key") == key:
            return row.get("contract_value") or default
    return default


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
    if header == PICK_INVENTORY_HEADER:
        return tuple(
            sorted(
                rows,
                key=lambda row: (
                    int(str(row.get("pick_year") or 0)),
                    int(str(row.get("round") or 0)),
                    int(str(row.get("slot") or 0)),
                ),
            )
        )
    if header == DEFER_SCENARIO_HEADER:
        return tuple(
            sorted(
                rows,
                key=lambda row: _float(row.get("current_pick_value_review_score"), 0.0)
                or 0.0,
                reverse=True,
            )
        )
    if header == FUTURE_PICK_CONTEXT_HEADER:
        return tuple(
            sorted(
                rows,
                key=lambda row: (
                    int(str(row.get("round") or 0)),
                    int(str(row.get("slot") or 0)),
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
