from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "historical_similarity/latest"
DOC_PATH = Path("docs/model_v4/HISTORICAL_SIMILARITY_ENGINE.md")
VERSION = "model_v4_historical_similarity_engine_0.1.0"

PROSPECT_VALUE_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_review_rows.csv"
HISTORICAL_TUNING_ROWS = (
    MODEL_ROOT / "historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv"
)

REVIEW_ONLY_USE = "review_only_historical_similarity_not_formula_input"
BLOCKED_USE = "do_not_use_as_final_pick_trade_cut_keep_or_rank_recommendation"

SIMILARITY_DIMENSIONS = (
    (
        "production",
        "production_score",
        "Production Score",
        0.24,
        "college production evidence",
    ),
    (
        "college_team_share",
        "market_share_score",
        "College Team Share",
        0.18,
        "college team-share evidence",
    ),
    (
        "draft_capital",
        "draft_capital_score",
        "NFL Draft Pick Signal",
        0.28,
        "factual NFL draft pick evidence",
    ),
    ("athletic", "athletic_prior_score", "Athletic Score", 0.12, "workout profile evidence"),
    ("recruiting", "recruiting_prior_score", "Recruiting", 0.08, "recruiting prior evidence"),
    ("age", "age_lifecycle_score", "Age Score", 0.06, "age/lifecycle evidence"),
    (
        "evidence_available",
        "component_weight_available",
        "Evidence Available",
        0.04,
        "evidence coverage context",
    ),
)

ROW_HEADER = (
    "player_name",
    "position",
    "model_score",
    "similarity_profile_bucket",
    "top_5_similar_historical_players",
    "similarity_score",
    "shared_positive_signals",
    "shared_risk_signals",
    "historical_outcome_summary",
    "sample_size_status",
    "confidence_status",
    "warning_flags",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

COMPONENT_HEADER = (
    "component_key",
    "player_name",
    "position",
    "historical_player",
    "historical_draft_year",
    "similarity_rank",
    "similarity_profile_bucket",
    "component_name",
    "current_value",
    "historical_value",
    "absolute_delta",
    "component_weight",
    "component_similarity",
    "allowed_input_file",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

WARNING_HEADER = (
    "warning_key",
    "player_name",
    "position",
    "warning_layer",
    "warning_code",
    "warning_detail",
    "next_action",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class HistoricalSimilarityResult:
    rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_historical_similarity_engine() -> HistoricalSimilarityResult:
    prospects = _read_rows(PROSPECT_VALUE_ROWS)
    historical_rows = _read_rows(HISTORICAL_TUNING_ROWS)

    rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    historical_by_position = _historical_by_position(historical_rows)

    for prospect in prospects:
        name = str(prospect.get("prospect_name", "")).strip()
        position = str(prospect.get("position", "")).strip()
        if not name or not position:
            continue
        candidates = _similar_candidates(prospect, historical_by_position.get(position, []))
        top_five = candidates[:5]
        bucket = _profile_bucket(prospect)
        score = _average_similarity(top_five)
        outcome_summary = _outcome_summary(top_five)
        sample_status = _sample_size_status(top_five)
        confidence = _confidence_status(prospect, top_five)
        warnings = _warning_flags(prospect, top_five, sample_status)
        row = {
            "player_name": name,
            "position": position,
            "model_score": _blank(_float(prospect.get("prospect_private_value_review_score"))),
            "similarity_profile_bucket": bucket,
            "top_5_similar_historical_players": _top_players(top_five),
            "similarity_score": _blank(score),
            "shared_positive_signals": _positive_signals(prospect, top_five),
            "shared_risk_signals": _risk_signals(prospect, top_five),
            "historical_outcome_summary": outcome_summary,
            "sample_size_status": sample_status,
            "confidence_status": confidence,
            "warning_flags": warnings,
            "allowed_use": REVIEW_ONLY_USE,
            "blocked_use": BLOCKED_USE,
            "formula_version": VERSION,
        }
        rows.append(row)
        component_rows.extend(_component_rows(prospect, top_five, bucket))
        warning_rows.extend(_warnings_for_row(row))

    rows.sort(
        key=lambda row: (
            1 if _float(row["similarity_score"]) is None else 0,
            -(_float(row["model_score"]) or 0.0),
            -(_float(row["similarity_score"]) or 0.0),
            str(row["player_name"]),
        )
    )
    return HistoricalSimilarityResult(
        rows=tuple(rows),
        component_rows=tuple(component_rows),
        warning_rows=tuple(warning_rows),
        doc_text=_doc_text(rows),
    )


def write_historical_similarity_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
) -> dict[str, Path]:
    result = build_historical_similarity_engine()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)

    paths = {
        "rows": output / "prospect_similarity_rows.csv",
        "component_rows": output / "prospect_similarity_component_rows.csv",
        "warnings": output / "prospect_similarity_warnings.csv",
        "doc": doc,
    }
    _write_csv(paths["rows"], ROW_HEADER, result.rows)
    _write_csv(paths["component_rows"], COMPONENT_HEADER, result.component_rows)
    _write_csv(paths["warnings"], WARNING_HEADER, result.warning_rows)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _historical_by_position(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        position = str(row.get("Pos", "")).strip()
        if not position:
            continue
        output.setdefault(position, []).append(row)
    return output


def _similar_candidates(
    prospect: dict[str, str], historical_rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for historical in historical_rows:
        score, matched_dimensions = _similarity_score(prospect, historical)
        if score is None:
            continue
        candidates.append(
            {
                "row": historical,
                "score": score,
                "matched_dimensions": matched_dimensions,
            }
        )
    candidates.sort(key=lambda candidate: float(candidate["score"]), reverse=True)
    return candidates


def _similarity_score(
    prospect: dict[str, str], historical: dict[str, str]
) -> tuple[float | None, list[str]]:
    weighted_similarity = 0.0
    total_weight = 0.0
    matched_dimensions: list[str] = []
    for name, current_key, historical_key, weight, _purpose in SIMILARITY_DIMENSIONS:
        current_value = _float(prospect.get(current_key))
        historical_value = _float(historical.get(historical_key))
        if current_value is None or historical_value is None:
            continue
        component_similarity = max(0.0, 100.0 - abs(current_value - historical_value))
        weighted_similarity += component_similarity * weight
        total_weight += weight
        matched_dimensions.append(name)
    if total_weight <= 0 or len(matched_dimensions) < 3:
        return None, matched_dimensions
    return round(weighted_similarity / total_weight, 4), matched_dimensions


def _component_rows(
    prospect: dict[str, str],
    candidates: list[dict[str, object]],
    bucket: str,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    name = str(prospect.get("prospect_name", ""))
    position = str(prospect.get("position", ""))
    for rank, candidate in enumerate(candidates, start=1):
        historical = candidate["row"]
        assert isinstance(historical, dict)
        historical_name = str(historical.get("Player", ""))
        historical_year = str(historical.get("Draft Year", ""))
        for component_name, current_key, historical_key, weight, purpose in SIMILARITY_DIMENSIONS:
            current_value = _float(prospect.get(current_key))
            historical_value = _float(historical.get(historical_key))
            if current_value is None or historical_value is None:
                continue
            delta = abs(current_value - historical_value)
            output.append(
                {
                    "component_key": (
                        f"{_norm(name)}:{rank}:{_norm(historical_name)}:{component_name}"
                    ),
                    "player_name": name,
                    "position": position,
                    "historical_player": historical_name,
                    "historical_draft_year": historical_year,
                    "similarity_rank": rank,
                    "similarity_profile_bucket": bucket,
                    "component_name": component_name,
                    "current_value": round(current_value, 4),
                    "historical_value": round(historical_value, 4),
                    "absolute_delta": round(delta, 4),
                    "component_weight": weight,
                    "component_similarity": round(max(0.0, 100.0 - delta), 4),
                    "allowed_input_file": purpose,
                    "allowed_use": REVIEW_ONLY_USE,
                    "blocked_use": BLOCKED_USE,
                    "formula_version": VERSION,
                }
            )
    return output


def _profile_bucket(prospect: dict[str, str]) -> str:
    position = str(prospect.get("position", "prospect")).lower()
    draft_score = _float(prospect.get("draft_capital_score")) or 0.0
    production = _float(prospect.get("production_score")) or 0.0
    share = _float(prospect.get("market_share_score")) or 0.0
    athletic = _float(prospect.get("athletic_prior_score")) or 0.0

    if draft_score >= 80 and position == "rb" and production >= 70:
        return "round_1_rb_strong_production"
    if draft_score >= 80 and position == "wr" and share < 55:
        return "round_1_wr_low_team_share_high_capital"
    if draft_score >= 80 and position == "wr":
        return "round_1_wr_balanced_profile"
    if position == "wr" and draft_score < 45 and share >= 80:
        return "day_3_wr_elite_team_share"
    if position == "rb" and draft_score < 45 and production >= 75:
        return "day_3_rb_production_edge"
    if position == "te" and (draft_score >= 65 or athletic >= 75):
        return "elite_te_no_premium_context"
    if position == "qb":
        return "qb_1qb_discounted_context"
    if draft_score == 0:
        return "no_draft_capital_watchlist"
    return f"{position}_balanced_similarity_profile"


def _top_players(candidates: list[dict[str, object]]) -> str:
    parts: list[str] = []
    for candidate in candidates:
        row = candidate["row"]
        assert isinstance(row, dict)
        parts.append(
            f"{row.get('Draft Year')} {row.get('Player')} "
            f"({round(float(candidate['score']), 1)}, {row.get('Outcome Category') or 'unknown'})"
        )
    return " | ".join(parts)


def _outcome_summary(candidates: list[dict[str, object]]) -> str:
    counts = {
        "difference_maker": 0,
        "starter": 0,
        "usable": 0,
        "replacement_or_miss": 0,
        "unknown": 0,
        "immature_2025": 0,
    }
    for candidate in candidates:
        row = candidate["row"]
        assert isinstance(row, dict)
        category = str(row.get("Outcome Category", "") or "").strip()
        maturity = str(row.get("Outcome Maturity", "") or "").strip()
        loaded = _boolish(row.get("Outcome Loaded"))
        if str(row.get("Draft Year", "")) == "2025" or maturity == "rookie_year_only":
            counts["immature_2025"] += 1
        if not loaded:
            counts["unknown"] += 1
        elif "difference" in category:
            counts["difference_maker"] += 1
        elif "starter" in category:
            counts["starter"] += 1
        elif "usable" in category:
            counts["usable"] += 1
        else:
            counts["replacement_or_miss"] += 1
    return "; ".join(f"{key}={value}" for key, value in counts.items())


def _sample_size_status(candidates: list[dict[str, object]]) -> str:
    loaded_count = sum(
        1 for candidate in candidates if _boolish(candidate["row"].get("Outcome Loaded"))  # type: ignore[index]
    )
    has_immature = any(
        str(candidate["row"].get("Draft Year", "")) == "2025"  # type: ignore[index]
        or str(candidate["row"].get("Outcome Maturity", "")) == "rookie_year_only"  # type: ignore[index]
        for candidate in candidates
    )
    if loaded_count >= 5 and not has_immature:
        return "adequate_similarity_sample"
    if loaded_count >= 3:
        if has_immature:
            return "thin_similarity_sample_includes_immature_2025"
        return "thin_similarity_sample"
    return "low_confidence_similarity_sample"


def _confidence_status(prospect: dict[str, str], candidates: list[dict[str, object]]) -> str:
    warnings = str(prospect.get("warning_flags", ""))
    if not candidates:
        return "no_same_position_similarity_sample"
    if "missing" in warnings or "source_limited" in warnings:
        return "similarity_review_with_source_warnings"
    if _sample_size_status(candidates) != "adequate_similarity_sample":
        return "similarity_review_with_thin_sample"
    return "similarity_review_supported_sample"


def _warning_flags(
    prospect: dict[str, str],
    candidates: list[dict[str, object]],
    sample_status: str,
) -> str:
    warnings = _join(
        prospect.get("warning_flags", ""),
        "review_only_similarity_not_formula_input",
        "missing_outcome_unknown_not_miss",
    )
    if "low_confidence" in sample_status or len(candidates) < 3:
        warnings = _join(warnings, "low_similarity_sample")
    if any(
        str(candidate["row"].get("Draft Year", "")) == "2025"  # type: ignore[index]
        or str(candidate["row"].get("Outcome Maturity", "")) == "rookie_year_only"  # type: ignore[index]
        for candidate in candidates
    ):
        warnings = _join(warnings, "includes_2025_immature_outcome_context")
    return warnings


def _positive_signals(prospect: dict[str, str], candidates: list[dict[str, object]]) -> str:
    signals: list[str] = []
    if (_float(prospect.get("draft_capital_score")) or 0) >= 75:
        signals.append("strong NFL draft pick signal")
    if (_float(prospect.get("production_score")) or 0) >= 75:
        signals.append("strong college production")
    if (_float(prospect.get("market_share_score")) or 0) >= 75:
        signals.append("strong college team share")
    if (_float(prospect.get("athletic_prior_score")) or 0) >= 75:
        signals.append("strong workout profile")
    if candidates:
        signals.append("same-position historical profile match")
    return "; ".join(signals) or "no dominant positive signal"


def _risk_signals(prospect: dict[str, str], candidates: list[dict[str, object]]) -> str:
    signals: list[str] = []
    warnings = str(prospect.get("warning_flags", ""))
    position = str(prospect.get("position", ""))
    if (_float(prospect.get("draft_capital_score")) or 0) < 45:
        signals.append("weak NFL draft pick signal")
    if "missing" in warnings:
        signals.append("missing evidence warning")
    if "source_limited" in warnings:
        signals.append("source-limited evidence warning")
    if position == "TE":
        signals.append("no-premium TE caution")
    if position == "QB":
        signals.append("1QB format caution")
    if any(
        str(candidate["row"].get("Draft Year", "")) == "2025"  # type: ignore[index]
        for candidate in candidates
    ):
        signals.append("some comp outcomes are immature")
    return "; ".join(signals) or "standard review risk"


def _average_similarity(candidates: list[dict[str, object]]) -> float | None:
    if not candidates:
        return None
    return round(sum(float(candidate["score"]) for candidate in candidates) / len(candidates), 4)


def _warnings_for_row(row: dict[str, object]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    seen: set[str] = set()
    for warning in str(row.get("warning_flags", "")).split("|"):
        if not warning or warning in seen:
            continue
        seen.add(warning)
        output.append(
            {
                "warning_key": f"{_norm(row.get('player_name'))}:{warning}",
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "warning_layer": "historical_similarity",
                "warning_code": warning,
                "warning_detail": warning.replace("_", " "),
                "next_action": "Use as review-only context; scout the profile before acting.",
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _doc_text(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Historical Similarity Engine",
        "",
        "## Scope",
        "",
        "This review-only engine compares current rookie prospects to same-position "
        "historical rookie profiles from the local 2021-2025 replay surfaces. It uses "
        "admitted football evidence only. Outcome labels are display-only context and "
        "cannot feed back into private value.",
        "",
        "## Guardrails",
        "",
        "- Similarity rows are not final draft, trade, cut, or ranking recommendations.",
        "- Missing historical outcomes are labeled unknown, not misses.",
        "- 2025 outcome context is marked immature where it appears.",
        "- Market, rank, mock, big-board, and projection fields are blocked from value.",
        "",
        "## Top Similarity Rows",
        "",
        "| Player | Pos | Bucket | Similarity | Historical Pattern |",
        "|---|---|---|---:|---|",
    ]
    for row in rows[:25]:
        lines.append(
            f"| {row['player_name']} | {row['position']} | "
            f"{row['similarity_profile_bucket']} | {row['similarity_score']} | "
            f"{row['historical_outcome_summary']} |"
        )
    return "\n".join(lines) + "\n"


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _float(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None


def _blank(value: float | None) -> str | float:
    return "" if value is None else round(value, 4)


def _boolish(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _join(*values: object) -> str:
    parts: list[str] = []
    for value in values:
        for part in str(value or "").split("|"):
            clean = part.strip()
            if clean and clean not in parts:
                parts.append(clean)
    return "|".join(parts)


def _norm(value: object) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())
