from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_sprint14f_june15_decision_board_service import (
    DEFAULT_14F_OUTPUT_ROOT,
)

DECISION_BOARD_VALIDATION_VERSION = (
    "model_v4_decision_board_validation_checkpoint_0.1.0"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/decision_board_validation/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/SPRINT_1_DECISION_BOARD_VALIDATION.md")

SUMMARY_HEADER = (
    "summary_key",
    "summary_value",
    "source",
    "status",
    "formula_version",
)

AREA_HEADER = (
    "decision_area",
    "row_count",
    "highest_priority_entity",
    "highest_priority",
    "review_band_counts",
    "status",
    "formula_version",
)

FOCUS_HEADER = (
    "focus_key",
    "decision_area",
    "entity_label",
    "related_pick_label",
    "position",
    "review_priority",
    "primary_review_band",
    "source_review_score",
    "secondary_review_score",
    "focus_reason",
    "morning_review_instruction",
    "receipt_pointer",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

WARNING_HEADER = (
    "warning_key",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "formula_version",
)


@dataclass(frozen=True)
class DecisionBoardValidationResult:
    summary_rows: tuple[dict[str, object], ...]
    area_rows: tuple[dict[str, object], ...]
    focus_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class DecisionBoardValidationPaths:
    summary: Path
    area_rows: Path
    focus_rows: Path
    warnings: Path
    doc: Path


def build_decision_board_validation(
    *,
    board_root: str | Path = DEFAULT_14F_OUTPUT_ROOT,
) -> DecisionBoardValidationResult:
    root = Path(board_root)
    decision_rows = _read_rows(root / "june15_decision_board_review_rows.csv")
    component_rows = _read_rows(root / "june15_decision_board_component_rows.csv")
    receipt_rows = _read_rows(root / "june15_decision_board_receipts.csv")
    warning_rows_source = _read_rows(root / "june15_decision_board_warnings.csv")

    decision_keys = {row["decision_key"] for row in decision_rows}
    receipt_keys = {row["decision_key"] for row in receipt_rows}
    component_keys = {row["decision_key"] for row in component_rows}
    allowed_safe = sum(
        row["allowed_use"] == "review_only_june15_decision_context_not_final_action"
        for row in decision_rows
    )
    blocked_safe = sum(
        row["blocked_use"]
        == "do_not_use_as_final_cut_keep_trade_or_draft_recommendation"
        for row in decision_rows
    )
    recommendations_created = any(
        _contains_final_action_language(row) for row in decision_rows
    )
    receipt_coverage = len(decision_keys & receipt_keys)
    component_coverage = len(decision_keys & component_keys)
    area_rows = _area_rows(decision_rows)
    focus_rows = _focus_rows(decision_rows, receipt_rows)
    warning_rows = _validation_warnings(
        decision_rows=decision_rows,
        receipt_coverage=receipt_coverage,
        component_coverage=component_coverage,
        allowed_safe=allowed_safe,
        blocked_safe=blocked_safe,
        recommendations_created=recommendations_created,
        source_warning_rows=warning_rows_source,
    )

    blocker_count = sum(row["severity"] == "blocker" for row in warning_rows)
    verdict = (
        "sprint_1_complete_ready_for_morning_human_review"
        if blocker_count == 0
        else "needs_repair_before_human_decision_review"
    )
    summary = {
        "decision_rows": len(decision_rows),
        "roster_rows": sum(
            row["decision_area"] == "roster_pressure_trade_context"
            for row in decision_rows
        ),
        "pick_rows": sum(
            row["decision_area"] == "pick_trade_defer_context"
            for row in decision_rows
        ),
        "rookie_candidate_rows": sum(
            row["decision_area"] == "rookie_pick_window_context"
            for row in decision_rows
        ),
        "receipt_coverage_rows": receipt_coverage,
        "component_coverage_rows": component_coverage,
        "safe_allowed_use_rows": allowed_safe,
        "safe_blocked_use_rows": blocked_safe,
        "focus_rows": len(focus_rows),
        "blocker_warnings": blocker_count,
        "final_recommendations_created": recommendations_created,
        "verdict": verdict,
    }
    summary_rows = tuple(
        {
            "summary_key": key,
            "summary_value": value,
            "source": str(root),
            "status": "review_only_validation_checkpoint",
            "formula_version": DECISION_BOARD_VALIDATION_VERSION,
        }
        for key, value in summary.items()
    )
    return DecisionBoardValidationResult(
        summary_rows=summary_rows,
        area_rows=area_rows,
        focus_rows=focus_rows,
        warning_rows=warning_rows,
        summary=summary,
    )


def write_decision_board_validation(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    board_root: str | Path = DEFAULT_14F_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: DecisionBoardValidationResult | None = None,
) -> DecisionBoardValidationPaths:
    result = result or build_decision_board_validation(board_root=board_root)
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    paths = DecisionBoardValidationPaths(
        summary=output / "decision_board_validation_summary.csv",
        area_rows=output / "decision_board_validation_area_rows.csv",
        focus_rows=output / "decision_board_validation_focus_rows.csv",
        warnings=output / "decision_board_validation_warnings.csv",
        doc=Path(doc_path),
    )
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    _write_csv(paths.area_rows, AREA_HEADER, result.area_rows)
    _write_csv(paths.focus_rows, FOCUS_HEADER, result.focus_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_text(paths.doc, _doc(result, paths))
    return paths


def _area_rows(decision_rows: list[dict[str, str]]) -> tuple[dict[str, object], ...]:
    areas = sorted({row["decision_area"] for row in decision_rows})
    rows: list[dict[str, object]] = []
    for area in areas:
        area_decisions = [row for row in decision_rows if row["decision_area"] == area]
        highest = max(area_decisions, key=_priority)
        band_counts: dict[str, int] = {}
        for row in area_decisions:
            band_counts[row["primary_review_band"]] = (
                band_counts.get(row["primary_review_band"], 0) + 1
            )
        rows.append(
            {
                "decision_area": area,
                "row_count": len(area_decisions),
                "highest_priority_entity": highest["entity_label"],
                "highest_priority": highest["review_priority"],
                "review_band_counts": "|".join(
                    f"{band}:{count}" for band, count in sorted(band_counts.items())
                ),
                "status": "review_only_area_validated",
                "formula_version": DECISION_BOARD_VALIDATION_VERSION,
            }
        )
    return tuple(rows)


def _focus_rows(
    decision_rows: list[dict[str, str]],
    receipt_rows: list[dict[str, str]],
) -> tuple[dict[str, object], ...]:
    receipt_by_key = {row["decision_key"]: row["receipt_pointer"] for row in receipt_rows}
    focus: list[dict[str, object]] = []
    for row in decision_rows:
        reason = _focus_reason(row)
        if not reason:
            continue
        focus.append(
            {
                "focus_key": f"sprint1:{row['decision_key']}",
                "decision_area": row["decision_area"],
                "entity_label": row["entity_label"],
                "related_pick_label": row["related_pick_label"],
                "position": row["position"],
                "review_priority": row["review_priority"],
                "primary_review_band": row["primary_review_band"],
                "source_review_score": row["source_review_score"],
                "secondary_review_score": row["secondary_review_score"],
                "focus_reason": reason,
                "morning_review_instruction": _morning_instruction(row),
                "receipt_pointer": receipt_by_key.get(row["decision_key"], ""),
                "allowed_use": row["allowed_use"],
                "blocked_use": row["blocked_use"],
                "formula_version": DECISION_BOARD_VALIDATION_VERSION,
            }
        )
    return tuple(sorted(focus, key=lambda row: float(row["review_priority"]), reverse=True))


def _focus_reason(row: dict[str, str]) -> str:
    band = row["primary_review_band"]
    if row["decision_area"] == "pick_trade_defer_context":
        return "owned_pick_or_defer_context_needs_human_strategy_review"
    if band in {
        "roster_pressure_line_review",
        "trade_market_before_cut_context_review",
    }:
        return "roster_pressure_or_trade_market_review_priority"
    if band in {
        "rookie_candidate_tier_gap_context_review",
        "rookie_candidate_gap_context_review",
        "rookie_late_watchlist_context_review",
    }:
        return "rookie_candidate_requires_pick_tier_review"
    return ""


def _morning_instruction(row: dict[str, str]) -> str:
    if row["decision_area"] == "roster_pressure_trade_context":
        return "Review roster fit, cut pressure, and trade-market path before any action."
    if row["decision_area"] == "pick_trade_defer_context":
        return "Review keep/use/defer/trade-down paths against roster needs and market offers."
    return "Review prospect profile, identity/source warnings, and pick cost before draft action."


def _validation_warnings(
    *,
    decision_rows: list[dict[str, str]],
    receipt_coverage: int,
    component_coverage: int,
    allowed_safe: int,
    blocked_safe: int,
    recommendations_created: bool,
    source_warning_rows: list[dict[str, str]],
) -> tuple[dict[str, object], ...]:
    warning_rows: list[dict[str, object]] = []
    expected = len(decision_rows)
    checks = (
        (
            "receipt_coverage_missing",
            receipt_coverage == expected,
            f"{receipt_coverage}/{expected} decision rows have receipts.",
        ),
        (
            "component_coverage_missing",
            component_coverage == expected,
            f"{component_coverage}/{expected} decision rows have component coverage.",
        ),
        (
            "unsafe_allowed_use_detected",
            allowed_safe == expected,
            f"{allowed_safe}/{expected} rows retain review-only allowed_use.",
        ),
        (
            "unsafe_blocked_use_detected",
            blocked_safe == expected,
            f"{blocked_safe}/{expected} rows block final recommendations.",
        ),
        (
            "final_action_language_detected",
            not recommendations_created,
            "Decision rows do not create final action recommendations.",
        ),
    )
    for code, passed, detail in checks:
        warning_rows.append(
            {
                "warning_key": f"sprint1:validation:{code}",
                "severity": "pass" if passed else "blocker",
                "warning_code": code,
                "warning_detail": detail,
                "next_action": "No action." if passed else "Repair before human decision use.",
                "formula_version": DECISION_BOARD_VALIDATION_VERSION,
            }
        )
    for row in source_warning_rows:
        warning_rows.append(
            {
                "warning_key": f"sprint1:source:{row['warning_code']}:{row['entity_label']}",
                "severity": row["severity"],
                "warning_code": row["warning_code"],
                "warning_detail": row["warning_detail"],
                "next_action": row["next_action"],
                "formula_version": DECISION_BOARD_VALIDATION_VERSION,
            }
        )
    return tuple(warning_rows)


def _contains_final_action_language(row: dict[str, str]) -> bool:
    final_words = (" cut ", " drop ", " draft ", " trade for ", " trade away ", " start ")
    haystack = f" {row['primary_review_band']} {row['next_review_step']} ".lower()
    return any(word in haystack for word in final_words) and "review" not in haystack


def _priority(row: dict[str, str]) -> float:
    try:
        return float(row["review_priority"])
    except ValueError:
        return 0.0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _doc(
    result: DecisionBoardValidationResult,
    paths: DecisionBoardValidationPaths,
) -> str:
    intro = (
        "This checkpoint validates the audited Sprint 14F June 15 decision board "
        "as a human-review surface. It does not create final cut, keep, trade, "
        "pick-defer, or rookie draft recommendations."
    )
    return f"""# Sprint 1 Decision Board Validation

{intro}

## Verdict

`{result.summary["verdict"]}`

## Summary

- Decision rows: {result.summary["decision_rows"]}
- Roster rows: {result.summary["roster_rows"]}
- Pick rows: {result.summary["pick_rows"]}
- Rookie candidate rows: {result.summary["rookie_candidate_rows"]}
- Focus rows for morning review: {result.summary["focus_rows"]}
- Blocker warnings: {result.summary["blocker_warnings"]}
- Final recommendations created: {result.summary["final_recommendations_created"]}

## Outputs

- `{paths.summary}`
- `{paths.area_rows}`
- `{paths.focus_rows}`
- `{paths.warnings}`

## Morning Review Order

1. Review owned pick and defer context first.
2. Review roster pressure and trade-market rows second.
3. Review rookie candidate windows by pick tier third.
4. Keep every row review-only until the final human decision pass.
"""
