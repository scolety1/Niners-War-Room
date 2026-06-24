from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.draft_day_app_v1_service import (
    load_dynasty_rankings,
    load_expanded_draftable_player_pool,
    load_frozen_board,
)
from src.services.market_baseline_service import compute_market_sanity_flags

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "docs" / "hq" / "model" / "evaluation_v0"
SUMMARY_FILE = "NWR_MODEL_EVALUATION_SUMMARY_V0_20260623.csv"
BY_BUCKET_FILE = "NWR_MODEL_EVALUATION_BY_BUCKET_V0_20260623.csv"
WARNINGS_FILE = "NWR_MODEL_EVALUATION_WARNINGS_V0_20260623.csv"

HISTORICAL_DROP_RECONSTRUCTION_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "historical_drop_lists"
    / "NWR_HISTORICAL_DROP_LIST_RECONSTRUCTION_2010_2026.csv"
)
BACKTEST_ELIGIBILITY_RULES_PATH = (
    REPO_ROOT / "docs" / "hq" / "model" / "NWR_BACKTEST_ROW_ELIGIBILITY_RULES_20260623.csv"
)
OUTCOME_COVERAGE_MATCH_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "NWR_OUTCOME_COLUMNS_COVERAGE_MATCH_TABLE_20260622.csv"
)

NOT_ENOUGH_INFORMATION = "Not enough information"
SUMMARY_COLUMNS = (
    "evaluation_area",
    "metric",
    "value",
    "status",
    "notes",
)
BUCKET_COLUMNS = (
    "bucket",
    "source_class",
    "confidence",
    "row_count",
    "eligible_for_truth_backtest",
    "eligible_for_caution_backtest",
    "eligible_for_sensitivity",
    "eligible_for_training",
    "notes",
)
WARNING_COLUMNS = (
    "warning_id",
    "severity",
    "player",
    "area",
    "warning",
    "evidence",
    "recommended_action",
)

TRUTH_BACKTEST = "Truth backtest"
CAUTION_BACKTEST = "Caution backtest"
SENSITIVITY_TEST = "Sensitivity test"
MARKET_DIAGNOSTIC = "Market sanity diagnostics"
UNKNOWN_BUCKET = "Excluded / unknown"

ELIGIBILITY_COLUMNS = (
    "allowed_for_training",
    "allowed_for_truth_backtest",
    "allowed_for_caution_backtest",
    "allowed_for_sensitivity",
)


@dataclass(frozen=True)
class EvaluationHarnessResult:
    summary: pd.DataFrame
    by_bucket: pd.DataFrame
    warnings: pd.DataFrame


def run_model_evaluation_harness(
    *,
    output_root: Path = OUTPUT_ROOT,
) -> dict[str, Path]:
    result = build_model_evaluation_harness()
    return write_model_evaluation_outputs(result, output_root=output_root)


def build_model_evaluation_harness(
    *,
    dynasty_frame: pd.DataFrame | None = None,
    frozen_frame: pd.DataFrame | None = None,
    expanded_pool_frame: pd.DataFrame | None = None,
    historical_drop_frame: pd.DataFrame | None = None,
    eligibility_rules_frame: pd.DataFrame | None = None,
    outcome_coverage_frame: pd.DataFrame | None = None,
    market_enriched_frame: pd.DataFrame | None = None,
) -> EvaluationHarnessResult:
    loaded_frozen = frozen_frame if frozen_frame is not None else _load_frozen_frame()
    loaded_dynasty = dynasty_frame if dynasty_frame is not None else _load_dynasty_frame()
    loaded_expanded = (
        expanded_pool_frame
        if expanded_pool_frame is not None
        else _load_expanded_pool(loaded_frozen)
    )
    historical = (
        historical_drop_frame
        if historical_drop_frame is not None
        else _read_optional_csv(HISTORICAL_DROP_RECONSTRUCTION_PATH)
    )
    eligibility = (
        eligibility_rules_frame
        if eligibility_rules_frame is not None
        else _read_optional_csv(BACKTEST_ELIGIBILITY_RULES_PATH)
    )
    outcome = (
        outcome_coverage_frame
        if outcome_coverage_frame is not None
        else _read_optional_csv(OUTCOME_COVERAGE_MATCH_PATH)
    )
    market_frame = (
        market_enriched_frame
        if market_enriched_frame is not None
        else _market_enriched_or_empty(loaded_dynasty)
    )

    by_bucket = _bucket_rows(historical, eligibility)
    summary = _summary_rows(
        dynasty=loaded_dynasty,
        frozen=loaded_frozen,
        expanded=loaded_expanded,
        historical=historical,
        outcome=outcome,
        market_frame=market_frame,
        by_bucket=by_bucket,
    )
    warnings = _warning_rows(
        dynasty=loaded_dynasty,
        expanded=loaded_expanded,
        outcome=outcome,
        by_bucket=by_bucket,
    )
    return EvaluationHarnessResult(
        summary=_frame(summary, SUMMARY_COLUMNS),
        by_bucket=_frame(by_bucket, BUCKET_COLUMNS),
        warnings=_frame(warnings, WARNING_COLUMNS),
    )


def write_model_evaluation_outputs(
    result: EvaluationHarnessResult,
    *,
    output_root: Path = OUTPUT_ROOT,
) -> dict[str, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    paths = {
        "summary": output_root / SUMMARY_FILE,
        "by_bucket": output_root / BY_BUCKET_FILE,
        "warnings": output_root / WARNINGS_FILE,
    }
    result.summary.to_csv(paths["summary"], index=False)
    result.by_bucket.to_csv(paths["by_bucket"], index=False)
    result.warnings.to_csv(paths["warnings"], index=False)
    return paths


def validate_evaluation_outputs(output_root: Path = OUTPUT_ROOT) -> list[str]:
    issues: list[str] = []
    expected = {
        SUMMARY_FILE: SUMMARY_COLUMNS,
        BY_BUCKET_FILE: BUCKET_COLUMNS,
        WARNINGS_FILE: WARNING_COLUMNS,
    }
    for name, columns in expected.items():
        path = output_root / name
        if not path.exists():
            issues.append(f"Missing output: {path}")
            continue
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        if tuple(frame.columns) != columns:
            issues.append(f"{name} columns mismatch: {list(frame.columns)}")
        if name == BY_BUCKET_FILE:
            invalid = sorted(set(frame["bucket"]) - {
                TRUTH_BACKTEST,
                CAUTION_BACKTEST,
                SENSITIVITY_TEST,
                MARKET_DIAGNOSTIC,
                UNKNOWN_BUCKET,
            })
            if invalid:
                issues.append(f"{name} invalid bucket values: {invalid}")
            if frame.loc[
                frame["source_class"].isin({"PROXY_DROP", "PROXY_ONLY"})
                & frame["eligible_for_truth_backtest"].eq("yes")
            ].shape[0]:
                issues.append("Proxy rows cannot be truth-backtest eligible.")
            if frame.loc[
                frame["source_class"].isin({"PROXY_DROP", "PROXY_ONLY"})
                & frame["eligible_for_training"].eq("yes")
            ].shape[0]:
                issues.append("Proxy rows cannot be training eligible.")
    return issues


def _summary_rows(
    *,
    dynasty: pd.DataFrame,
    frozen: pd.DataFrame,
    expanded: pd.DataFrame,
    historical: pd.DataFrame,
    outcome: pd.DataFrame,
    market_frame: pd.DataFrame,
    by_bucket: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(_coverage_summary("full_dynasty_board", dynasty, rank_column="nwr_rank"))
    rows.extend(_coverage_summary("frozen_baseline_board", frozen, rank_column="final_board_rank"))
    rows.extend(
        _coverage_summary(
            "expanded_draftable_pool",
            expanded,
            rank_column="final_board_rank",
        )
    )
    rows.extend(_position_summary("full_dynasty_board", dynasty))
    rows.extend(_position_summary("frozen_baseline_board", frozen))
    rows.extend(_outcome_summary(outcome, expanded))
    rows.extend(_market_summary(market_frame))
    rows.extend(_bucket_summary(by_bucket))
    rows.append(
        _summary(
            "evidence_separation",
            "predictive_accuracy_claim",
            NOT_ENOUGH_INFORMATION,
            "GREEN",
            "Harness does not claim predictive accuracy without actual outcome labels.",
        )
    )
    rows.append(
        _summary(
            "guardrail",
            "market_as_model_truth",
            "no",
            "GREEN",
            "DynastyProcess/ADP/market context is diagnostics only.",
        )
    )
    rows.append(
        _summary(
            "guardrail",
            "proxy_as_training_truth",
            "no",
            "GREEN",
            "PROXY_DROP/PROXY_ONLY/LOW rows are sensitivity-only.",
        )
    )
    if historical.empty:
        rows.append(
            _summary(
                "historical_evidence",
                "historical_drop_rows_loaded",
                "0",
                "YELLOW",
                "Historical drop reconstruction file was unavailable.",
            )
        )
    return rows


def _coverage_summary(area: str, frame: pd.DataFrame, *, rank_column: str) -> list[dict[str, str]]:
    total = len(frame)
    return [
        _summary(area, "row_count", total, "GREEN" if total else "YELLOW", ""),
        _summary(
            area,
            "rank_coverage",
            _coverage(frame, rank_column),
            _coverage_status(frame, rank_column),
            rank_column,
        ),
        _summary(
            area,
            "player_id_coverage",
            _coverage(frame, "player_id"),
            _coverage_status(frame, "player_id"),
            "",
        ),
        _summary(
            area,
            "age_coverage",
            _coverage(frame, "age"),
            _coverage_status(frame, "age"),
            "",
        ),
        _summary(
            area,
            "missing_data_count",
            _missing_data_count(frame),
            "GREEN",
            "Counts blank/null/Not enough information cells.",
        ),
        _summary(
            area,
            "not_enough_information_players",
            _players_with_nei(frame),
            "GREEN",
            "Players with at least one Not enough information field.",
        ),
    ]


def _position_summary(area: str, frame: pd.DataFrame) -> list[dict[str, str]]:
    if frame.empty or "position" not in frame.columns:
        return [
            _summary(
                area,
                "coverage_by_position",
                NOT_ENOUGH_INFORMATION,
                "YELLOW",
                "position column missing.",
            )
        ]
    rows = []
    counts = frame["position"].astype(str).str.upper().replace("", "UNKNOWN").value_counts()
    for position, count in counts.sort_index().items():
        rows.append(_summary(area, f"position_count_{position}", int(count), "GREEN", ""))
    return rows


def _outcome_summary(outcome: pd.DataFrame, expanded: pd.DataFrame) -> list[dict[str, str]]:
    if outcome.empty:
        return [
            _summary(
                "outcome",
                "outcome_coverage",
                NOT_ENOUGH_INFORMATION,
                "YELLOW",
                "Outcome coverage artifact missing.",
            ),
            _summary(
                "outcome",
                "unsupported_count",
                NOT_ENOUGH_INFORMATION,
                "YELLOW",
                "Outcome coverage artifact missing.",
            ),
        ]
    status_col = "prop_match_status" if "prop_match_status" in outcome.columns else ""
    matched = int(_outcome_match_mask(outcome[status_col]).sum()) if status_col else 0
    unmatched = len(outcome) - matched
    rows = [
        _summary("outcome", "coverage_artifact_rows", len(outcome), "GREEN", ""),
        _summary("outcome", "matched_outcome_rows", matched, "GREEN" if matched else "YELLOW", ""),
        _summary(
            "outcome",
            "unsupported_or_missing_rows",
            unmatched,
            "YELLOW" if unmatched else "GREEN",
            "Must display as Not enough information, not zero.",
        ),
    ]
    if "outcome_applicable_summary" in expanded.columns:
        supported = expanded["outcome_applicable_summary"].map(_has_value).sum()
        rows.append(
            _summary(
                "outcome",
                "expanded_pool_outcome_summary_supported",
                int(supported),
                "GREEN" if supported else "YELLOW",
                "Display-only only.",
            )
        )
    return rows


def _outcome_match_mask(status: pd.Series) -> pd.Series:
    normalized = status.astype(str).str.strip().str.lower()
    return normalized.str.startswith("matched") | normalized.isin(
        {"match", "covered", "supported"}
    )


def _market_summary(frame: pd.DataFrame) -> list[dict[str, str]]:
    if frame.empty:
        return [
            _summary(
                "market_sanity",
                "market_match_coverage",
                NOT_ENOUGH_INFORMATION,
                "YELLOW",
                "Market context unavailable.",
            ),
            _summary(
                "market_sanity",
                "nwr_vs_market_gap_summary",
                NOT_ENOUGH_INFORMATION,
                "YELLOW",
                "Market context unavailable.",
            ),
        ]
    value_col = "dp_value_1qb" if "dp_value_1qb" in frame.columns else ""
    matched = int(frame[value_col].map(_has_value).sum()) if value_col else 0
    gap_values = pd.to_numeric(
        frame.get("market_gap", pd.Series(dtype=str)),
        errors="coerce",
    ).dropna()
    if gap_values.empty:
        gap_summary = NOT_ENOUGH_INFORMATION
    else:
        gap_summary = (
            f"count={len(gap_values)}; "
            f"mean={gap_values.mean():.1f}; "
            f"max_abs={gap_values.abs().max():.1f}"
        )
    return [
        _summary(
            "market_sanity",
            "market_match_count",
            matched,
            "GREEN" if matched else "YELLOW",
            "Display-only context only.",
        ),
        _summary(
            "market_sanity",
            "market_match_coverage",
            _ratio(matched, len(frame)),
            "GREEN" if matched else "YELLOW",
            "Display-only context only.",
        ),
        _summary(
            "market_sanity",
            "nwr_vs_market_gap_summary",
            gap_summary,
            "GREEN" if gap_summary != NOT_ENOUGH_INFORMATION else "YELLOW",
            "Diagnostics only; not model truth.",
        ),
    ]


def _bucket_rows(
    historical: pd.DataFrame,
    eligibility: pd.DataFrame,
) -> list[dict[str, str]]:
    if historical.empty:
        return [
            _bucket(
                UNKNOWN_BUCKET,
                "UNKNOWN",
                "UNKNOWN",
                0,
                "no",
                "no",
                "no",
                "no",
                "Historical drop reconstruction unavailable.",
            )
        ]
    merged = _with_eligibility(historical, eligibility)
    rows: list[dict[str, str]] = []
    group_columns = ["source_class", "confidence"]
    for (source_class, confidence), group in merged.groupby(group_columns, dropna=False):
        bucket = _evaluation_bucket(group.iloc[0].to_dict())
        rows.append(
            _bucket(
                bucket,
                _text(source_class) or "UNKNOWN",
                _text(confidence) or "UNKNOWN",
                len(group),
                _yes_no(group["allowed_for_truth_backtest"].eq("yes").any()),
                _yes_no(group["allowed_for_caution_backtest"].eq("yes").any()),
                _yes_no(group["allowed_for_sensitivity"].eq("yes").any()),
                _yes_no(group["allowed_for_training"].eq("yes").any()),
                _bucket_note(bucket),
            )
        )
    rows.append(
        _bucket(
            MARKET_DIAGNOSTIC,
            "DISPLAY_ONLY",
            "HIGH",
            0,
            "no",
            "no",
            "yes",
            "no",
            "Market/ADP/DynastyProcess context is diagnostics-only and never training truth.",
        )
    )
    return sorted(rows, key=lambda row: (row["bucket"], row["source_class"], row["confidence"]))


def _bucket_summary(bucket_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for bucket in (TRUTH_BACKTEST, CAUTION_BACKTEST, SENSITIVITY_TEST, MARKET_DIAGNOSTIC):
        count = sum(int(row["row_count"]) for row in bucket_rows if row["bucket"] == bucket)
        rows.append(
            _summary(
                "evidence_buckets",
                f"{bucket.lower().replace(' ', '_')}_row_count",
                count,
                "GREEN" if count else "YELLOW",
                "Rows are separated; no bucket is collapsed into truth.",
            )
        )
    return rows


def _warning_rows(
    *,
    dynasty: pd.DataFrame,
    expanded: pd.DataFrame,
    outcome: pd.DataFrame,
    by_bucket: list[dict[str, str]],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    high_rank = _top_ranked(
        expanded,
        ("dynasty_asset_rank", "cross_asset_candidate_rank", "final_board_rank"),
        30,
    )
    for row in high_rank.to_dict("records"):
        player = _player(row)
        missing = []
        for label, column in (("player_id", "player_id"), ("age", "age")):
            if not _has_value(row.get(column)):
                missing.append(label)
        outcome_value = row.get("outcome_applicable_summary")
        if not _has_value(outcome_value):
            missing.append("outcome")
        confidence = _text(row.get("confidence_band") or row.get("dynasty_asset_confidence"))
        if missing:
            warnings.append(
                _warning(
                    "P2",
                    player,
                    "potential_false_confidence",
                    f"High-rank player missing {', '.join(missing)}.",
                    f"confidence={confidence or NOT_ENOUGH_INFORMATION}",
                    "Keep confidence/caveat visible; do not treat missing data as clean.",
                )
            )
    proxy_truth = [
        row
        for row in by_bucket
        if row["source_class"] in {"PROXY_DROP", "PROXY_ONLY"}
        and row["eligible_for_truth_backtest"] == "yes"
    ]
    if proxy_truth:
        warnings.append(
            _warning(
                "P0",
                "",
                "bucket_guardrail",
                "Proxy rows were marked truth-backtest eligible.",
                str(proxy_truth),
                "Fix eligibility rules before using evaluation outputs.",
            )
        )
    if outcome.empty:
        warnings.append(
            _warning(
                "P2",
                "",
                "outcome_coverage",
                "Outcome coverage artifact unavailable.",
                str(OUTCOME_COVERAGE_MATCH_PATH),
                "Keep Outcome as Not enough information until approved artifact loads.",
            )
        )
    if dynasty.empty:
        warnings.append(
            _warning(
                "P1",
                "",
                "dynasty_source",
                "Full dynasty board could not be loaded.",
                "0 rows",
                "Restore approved 240-row source before relying on rankings audit.",
            )
        )
    return warnings


def _with_eligibility(historical: pd.DataFrame, eligibility: pd.DataFrame) -> pd.DataFrame:
    frame = historical.copy()
    for column in ("source_class", "confidence"):
        if column not in frame.columns:
            frame[column] = "UNKNOWN"
    if eligibility.empty:
        for column in ELIGIBILITY_COLUMNS:
            frame[column] = "no"
        return frame
    rules = eligibility.copy()
    for column in ("source_class", "confidence"):
        if column not in rules.columns:
            rules[column] = "UNKNOWN"
    merged = frame.merge(
        rules[["source_class", "confidence", *ELIGIBILITY_COLUMNS, "notes"]],
        on=["source_class", "confidence"],
        how="left",
        suffixes=("", "_eligibility"),
    )
    for column in ELIGIBILITY_COLUMNS:
        merged[column] = merged[column].fillna("no").astype(str).str.lower()
    return merged


def _evaluation_bucket(row: dict[str, Any]) -> str:
    source_class = _text(row.get("source_class")).upper()
    truth = _text(row.get("allowed_for_truth_backtest")).lower() == "yes"
    caution = _text(row.get("allowed_for_caution_backtest")).lower() == "yes"
    sensitivity = _text(row.get("allowed_for_sensitivity")).lower() == "yes"
    if truth and source_class == "ACTUAL_DROP":
        return TRUTH_BACKTEST
    if caution and source_class in {"ACTUAL_DROP", "INFERRED_DROP", "CURRENT_FA_SNAPSHOT"}:
        return CAUTION_BACKTEST
    if sensitivity:
        return SENSITIVITY_TEST
    return UNKNOWN_BUCKET


def _coverage(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return NOT_ENOUGH_INFORMATION
    covered = int(frame[column].map(_has_value).sum())
    return _ratio(covered, len(frame))


def _coverage_status(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        return "YELLOW"
    covered = int(frame[column].map(_has_value).sum())
    if covered == len(frame):
        return "GREEN"
    if covered:
        return "YELLOW"
    return "RED"


def _missing_data_count(frame: pd.DataFrame) -> int | str:
    if frame.empty:
        return 0
    return int(frame.map(lambda value: not _has_value(value)).sum().sum())


def _players_with_nei(frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    if "player" in frame.columns:
        player_col = "player"
    elif "player_name" in frame.columns:
        player_col = "player_name"
    else:
        return 0
    mask = frame.astype(str).apply(
        lambda row: row.str.contains(NOT_ENOUGH_INFORMATION, case=False, na=False).any(),
        axis=1,
    )
    return int(frame.loc[mask, player_col].nunique())


def _top_ranked(frame: pd.DataFrame, rank_columns: tuple[str, ...], limit: int) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    output = frame.copy()
    available = [column for column in rank_columns if column in output.columns]
    if not available:
        return pd.DataFrame()
    rank_values = []
    for _, row in output.iterrows():
        rank_values.append(_first_rank_value(row, available))
    output["_evaluation_rank"] = rank_values
    return (
        output.loc[output["_evaluation_rank"].notna()]
        .sort_values("_evaluation_rank")
        .head(limit)
    )


def _first_rank_value(row: pd.Series, columns: list[str]) -> float | None:
    for column in columns:
        value = _float(row.get(column))
        if value is not None:
            return value
    return None


def _load_frozen_frame() -> pd.DataFrame:
    bundle = load_frozen_board()
    return bundle.frame.copy()


def _load_dynasty_frame() -> pd.DataFrame:
    bundle = load_dynasty_rankings()
    return bundle.frame.copy()


def _load_expanded_pool(frozen_frame: pd.DataFrame) -> pd.DataFrame:
    return load_expanded_draftable_player_pool(frozen_frame).copy()


def _market_enriched_or_empty(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    try:
        return compute_market_sanity_flags(frame)
    except (FileNotFoundError, ValueError, KeyError):
        return pd.DataFrame()


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _summary(area: str, metric: str, value: Any, status: str, notes: str) -> dict[str, str]:
    return {
        "evaluation_area": area,
        "metric": metric,
        "value": _text(value),
        "status": status,
        "notes": notes,
    }


def _bucket(
    bucket: str,
    source_class: str,
    confidence: str,
    row_count: int,
    truth: str,
    caution: str,
    sensitivity: str,
    training: str,
    notes: str,
) -> dict[str, str]:
    return {
        "bucket": bucket,
        "source_class": source_class,
        "confidence": confidence,
        "row_count": str(row_count),
        "eligible_for_truth_backtest": truth,
        "eligible_for_caution_backtest": caution,
        "eligible_for_sensitivity": sensitivity,
        "eligible_for_training": training,
        "notes": notes,
    }


def _warning(
    severity: str,
    player: str,
    area: str,
    warning: str,
    evidence: str,
    recommended_action: str,
) -> dict[str, str]:
    return {
        "warning_id": "",
        "severity": severity,
        "player": player,
        "area": area,
        "warning": warning,
        "evidence": evidence,
        "recommended_action": recommended_action,
    }


def _frame(rows: list[dict[str, str]], columns: tuple[str, ...]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=columns).fillna("")
    if "warning_id" in frame.columns:
        frame["warning_id"] = [f"MEV0-W{i:03d}" for i in range(1, len(frame) + 1)]
    return frame


def _bucket_note(bucket: str) -> str:
    return {
        TRUTH_BACKTEST: "High-confidence actual evidence only; not training truth.",
        CAUTION_BACKTEST: "Actual plus medium/high inferred evidence; report separately.",
        SENSITIVITY_TEST: "Proxy/low-confidence rows; sensitivity only.",
        MARKET_DIAGNOSTIC: "Display-only market diagnostics only.",
        UNKNOWN_BUCKET: "Excluded until classified.",
    }.get(bucket, "")


def _ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return NOT_ENOUGH_INFORMATION
    return f"{numerator}/{denominator} ({(numerator / denominator) * 100:.1f}%)"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _has_value(value: Any) -> bool:
    text = _text(value).strip()
    return bool(text) and text.lower() not in {
        "nan",
        "none",
        "null",
        "n/a",
        "<na>",
        NOT_ENOUGH_INFORMATION.lower(),
    }


def _float(value: Any) -> float | None:
    text = _text(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _player(row: dict[str, Any]) -> str:
    return _text(row.get("player") or row.get("player_name")) or NOT_ENOUGH_INFORMATION
