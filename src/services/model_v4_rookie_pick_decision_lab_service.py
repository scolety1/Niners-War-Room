from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "rookie_pick_decision_lab/latest"
DOC_PATH = Path("docs/model_v4/ROOKIE_PICK_DECISION_LAB.md")
VERSION = "model_v4_rookie_pick_decision_lab_0.1.0"

NINERS_PICKS = ("2026 1.03", "2026 1.04", "2026 2.04", "2026 2.08", "2026 5.04")
REVIEW_ONLY_USE = "review_only_rookie_pick_decision_lab_not_final_selection"
BLOCKED_USE = "do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation"
MANUAL_ONLY_NO_BASELINE = "manual_only_no_exact_model_baseline"
TRADE_MARKET_GUARDRAIL = (
    "internal_model_neighbor_only_not_one_for_one_trade_equivalent"
)

PICK_CANDIDATES = MODEL_ROOT / "rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv"
PROSPECT_VALUE_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_review_rows.csv"
PROSPECT_COMPONENT_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_component_rows.csv"
STARTUP_SLOT_ROWS = MODEL_ROOT / "startup_slot_simulator/latest/startup_slot_review_rows.csv"
STARTUP_PICK_ZONE_ROWS = (
    MODEL_ROOT / "startup_slot_simulator/latest/startup_slot_pick_zone_rows.csv"
)
OUTCOME_BUCKET_ROWS = MODEL_ROOT / "startup_slot_simulator/latest/startup_slot_bucket_rows.csv"
PICK_INVENTORY_ROWS = MODEL_ROOT / "pick_trade_defer/latest/niners_pick_inventory_review_rows.csv"
PICK_DEFER_ROWS = MODEL_ROOT / "pick_trade_defer/latest/pick_defer_scenario_review_rows.csv"
ROSTER_PRESSURE_ROWS = MODEL_ROOT / "decision_pressure/latest/cut_keep_pressure_review_rows.csv"
OPPORTUNITY_COST_ROWS = (
    MODEL_ROOT / "roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv"
)

ROW_HEADER = (
    "pick_label",
    "pick_value_score",
    "source_path",
    "source_column",
    "lineage_class",
    "pick_tier",
    "top_rookie_candidates",
    "nearby_startup_slot_assets",
    "candidate_fit_context",
    "biggest_model_risk",
    "upside_context_candidate",
    "lower_variance_context_candidate",
    "defer_review_context",
    "confidence_status",
    "manual_questions",
    "manual_question_rookie_profile",
    "manual_question_roster_fit",
    "manual_question_pick_value",
    "manual_question_trade_defer",
    "manual_question_source_risk",
    "trade_market_reality_context",
    "equivalence_guardrail",
    "review_label",
    "warning_flags",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

COMPONENT_HEADER = (
    "component_key",
    "pick_label",
    "component_layer",
    "component_name",
    "component_value",
    "component_context",
    "allowed_input_file",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

COMPARE_HEADER = (
    "compare_key",
    "pick_label",
    "comparison_type",
    "comparison_mode",
    "comparator_key",
    "comparator_source_status",
    "asset_name",
    "position",
    "asset_score",
    "source_path",
    "source_column",
    "lineage_class",
    "asset_context",
    "score_gap_to_pick",
    "evidence_or_risk_note",
    "trade_market_reality_context",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

WARNING_HEADER = (
    "warning_key",
    "pick_label",
    "warning_layer",
    "warning_code",
    "warning_detail",
    "next_action",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class RookiePickDecisionLabResult:
    rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    compare_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_rookie_pick_decision_lab() -> RookiePickDecisionLabResult:
    pick_candidates = _read_rows(PICK_CANDIDATES)
    prospect_rows = _read_rows(PROSPECT_VALUE_ROWS)
    prospect_components = _read_rows(PROSPECT_COMPONENT_ROWS)
    startup_rows = _read_rows(STARTUP_SLOT_ROWS)
    startup_pick_zones = _read_rows(STARTUP_PICK_ZONE_ROWS)
    buckets = _read_rows(OUTCOME_BUCKET_ROWS)
    pick_inventory = _read_rows(PICK_INVENTORY_ROWS)
    defer_rows = _read_rows(PICK_DEFER_ROWS)
    pressure_rows = _read_rows(ROSTER_PRESSURE_ROWS)
    opportunity_rows = _read_rows(OPPORTUNITY_COST_ROWS)

    prospect_lookup = {_norm(row.get("prospect_name")): row for row in prospect_rows}
    bucket_lookup = {_norm(row.get("player_name")): row for row in buckets}
    pick_lookup = {row.get("pick_label"): row for row in pick_inventory}
    defer_lookup = {row.get("current_pick_label"): row for row in defer_rows}
    startup_pick_lookup = {row.get("pick_label"): row for row in startup_pick_zones}

    rows: list[dict[str, object]] = []
    compare_rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []
    candidate_names: set[str] = set()
    for pick in NINERS_PICKS:
        pick_row = pick_lookup.get(pick, {})
        pick_score = _float(pick_row.get("pick_value_review_score"))
        candidates = _pick_candidates(pick, pick_candidates, prospect_lookup, bucket_lookup)
        candidate_names.update(str(candidate["name"]) for candidate in candidates[:8])
        zone_row = startup_pick_lookup.get(pick, {})
        defer = defer_lookup.get(pick, {})
        nearby_assets = _nearby_assets_for_pick(pick_score, startup_rows)
        roster_pressure = _roster_pressure_context(pressure_rows, opportunity_rows)
        label = _review_label(pick_score, candidates, defer, zone_row)
        warnings = _join(
            pick_row.get("warning_flags", ""),
            zone_row.get("warning_flags", ""),
            defer.get("warning_flags", ""),
            "review_only_no_final_rookie_pick_recommendation",
            "manual_decision_required",
            zone_row.get("equivalence_guardrail", ""),
            MANUAL_ONLY_NO_BASELINE if pick_score is None else "",
            "pick_value_baseline_missing" if pick_score is None else "",
        )
        manual_only = pick_score is None
        manual_question_fields = _manual_question_fields(
            pick,
            label,
            roster_pressure,
            missing_baseline=manual_only,
        )
        manual_only_context = (
            f"{MANUAL_ONLY_NO_BASELINE}: inspect the full board manually; "
            "no exact candidate cluster or slot equivalence is admitted for this pick."
        )
        row = {
            "pick_label": pick,
            "pick_value_score": _blank(pick_score),
            "source_path": str(PICK_INVENTORY_ROWS),
            "source_column": "pick_value_review_score",
            "lineage_class": "review_v4_owned_pick",
            "pick_tier": (
                MANUAL_ONLY_NO_BASELINE
                if pick_score is None
                else pick_row.get("tier_label", "missing_pick_value_baseline")
            ),
            "top_rookie_candidates": manual_only_context
            if manual_only
            else _candidate_names(candidates[:6]),
            "nearby_startup_slot_assets": manual_only_context
            if manual_only
            else _asset_names(nearby_assets[:8]),
            "candidate_fit_context": _candidate_fit_context(candidates, manual_only=manual_only),
            "biggest_model_risk": _biggest_risk(candidates),
            "upside_context_candidate": _upside_context_candidate(
                candidates,
                manual_only=manual_only,
            ),
            "lower_variance_context_candidate": _lower_variance_context_candidate(
                candidates,
                manual_only=manual_only,
            ),
            "defer_review_context": _defer_context(
                defer,
                zone_row,
                missing_baseline=pick_score is None,
            ),
            "confidence_status": _confidence_status(candidates, pick_score),
            "manual_questions": _manual_questions(manual_question_fields),
            **manual_question_fields,
            "trade_market_reality_context": _market_reality_context(
                zone_row,
                nearby_assets,
                manual_only=manual_only,
            ),
            "equivalence_guardrail": _equivalence_guardrail(
                zone_row,
                nearby_assets,
                manual_only=manual_only,
            ),
            "review_label": label,
            "warning_flags": warnings,
            "allowed_use": REVIEW_ONLY_USE,
            "blocked_use": BLOCKED_USE,
            "formula_version": VERSION,
        }
        rows.append(row)
        component_rows.extend(_components_for_pick(row, defer, zone_row))
        compare_rows.extend(
            _compare_rows_for_pick(pick, pick_score, candidates, nearby_assets, defer)
        )
        warning_rows.extend(_warnings_for_pick(row))
    component_rows.extend(_prospect_component_receipts(prospect_components, candidate_names))
    return RookiePickDecisionLabResult(
        rows=tuple(rows),
        component_rows=tuple(component_rows),
        compare_rows=tuple(compare_rows),
        warning_rows=tuple(warning_rows),
        doc_text=_doc_text(rows),
    )


def write_rookie_pick_decision_lab_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: RookiePickDecisionLabResult | None = None,
) -> dict[str, Path]:
    result = result or build_rookie_pick_decision_lab()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "rows": output / "pick_decision_rows.csv",
        "component_rows": output / "pick_decision_component_rows.csv",
        "compare_rows": output / "pick_decision_compare_rows.csv",
        "warnings": output / "pick_decision_warnings.csv",
        "doc": Path(doc_path),
    }
    _write_csv(paths["rows"], ROW_HEADER, result.rows)
    _write_csv(paths["component_rows"], COMPONENT_HEADER, result.component_rows)
    _write_csv(paths["compare_rows"], COMPARE_HEADER, result.compare_rows)
    _write_csv(paths["warnings"], WARNING_HEADER, result.warning_rows)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _pick_candidates(
    pick: str,
    rows: list[dict[str, str]],
    prospect_lookup: dict[str, dict[str, str]],
    bucket_lookup: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        if row.get("pick_label") != pick:
            continue
        name = row.get("prospect_name", "")
        prospect = prospect_lookup.get(_norm(name), {})
        bucket = bucket_lookup.get(_norm(name), {})
        score = _float(row.get("league_format_adjusted_score"))
        pick_gap = _float(row.get("pick_value_gap_review"))
        output.append(
            {
                "name": name,
                "position": row.get("position", ""),
                "score": score,
                "rank": _int(row.get("candidate_board_rank")) or 999,
                "pick_gap": pick_gap,
                "window": row.get("candidate_window_band", ""),
                "rationale": row.get("review_rationale", ""),
                "warnings": _join(row.get("warning_flags", ""), prospect.get("warning_flags", "")),
                "confidence": prospect.get(
                    "confidence_status", row.get("candidate_window_band", "")
                ),
                "top20": bucket.get("top_20_bucket", ""),
                "starter": bucket.get("starter_bucket", ""),
                "sample": bucket.get("sample_size_status", ""),
                "production": _float(prospect.get("production_score")),
                "draft": _float(prospect.get("draft_capital_score")),
                "share": _float(prospect.get("market_share_score")),
            }
        )
    return sorted(output, key=lambda item: (int(item["rank"]), -(item["score"] or 0)))


def _nearby_assets_for_pick(
    pick_score: float | None,
    startup_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    if pick_score is None:
        return []
    assets: list[dict[str, object]] = []
    for row in startup_rows:
        if row.get("entity_type") == "owned_rookie_pick":
            continue
        score = _float(row.get("model_score"))
        if score is None:
            continue
        assets.append(
            {
                "name": row.get("player_or_asset", ""),
                "key": row.get("entity_key", ""),
                "position": row.get("position", ""),
                "score": score,
                "type": row.get("entity_type", ""),
                "context": row.get("pick_equivalent_context", ""),
                "warnings": row.get("warning_flags", ""),
                "trade_market_reality_context": row.get("trade_market_reality_context", ""),
                "equivalence_guardrail": row.get("equivalence_guardrail", ""),
            }
        )
    return sorted(assets, key=lambda item: abs(float(item["score"]) - pick_score))


def _review_label(
    pick_score: float | None,
    candidates: list[dict[str, object]],
    defer: dict[str, str],
    zone: dict[str, str],
) -> str:
    if pick_score is None:
        return "manual_decision_required"
    if defer.get("defer_review_band") or zone.get("review_label") == "review_rookie_vs_drop_player":
        return "hold_pick_value_context"
    if candidates:
        best_gap = max(float(candidate["score"] or 0) - pick_score for candidate in candidates)
        if best_gap < -12:
            return "hold_pick_value_context"
        return "use_pick_review"
    return "manual_decision_required"


def _candidate_fit_context(
    candidates: list[dict[str, object]],
    *,
    manual_only: bool = False,
) -> str:
    if manual_only:
        return "manual_only_no_exact_candidate_fit_context"
    if not candidates:
        return "no_candidate_cluster_loaded"
    best = min(candidates, key=lambda item: abs(float(item["pick_gap"] or 0)))
    return f"{best['name']} {best['position']} ({best['score']})"


def _biggest_risk(candidates: list[dict[str, object]]) -> str:
    if not candidates:
        return "manual_review_required"
    risky = max(
        candidates,
        key=lambda item: (
            "missing" in str(item["warnings"]),
            "source_limited" in str(item["warnings"]),
            abs(float(item["pick_gap"] or 0)),
        ),
    )
    return f"{risky['name']}: {_risk_note(risky)}"


def _upside_context_candidate(
    candidates: list[dict[str, object]],
    *,
    manual_only: bool = False,
) -> str:
    if manual_only:
        return "manual_only_no_exact_upside_context"
    if not candidates:
        return "manual_review_required"
    upside = max(
        candidates,
        key=lambda item: (
            _bucket_rank(str(item.get("top20", ""))),
            float(item.get("draft") or 0),
            float(item.get("production") or 0),
        ),
    )
    return f"{upside['name']} {upside['position']}: top20 {upside.get('top20') or 'unknown'}"


def _lower_variance_context_candidate(
    candidates: list[dict[str, object]],
    *,
    manual_only: bool = False,
) -> str:
    if manual_only:
        return "manual_only_no_exact_lower_variance_context"
    if not candidates:
        return "manual_review_required"
    safe = max(
        candidates,
        key=lambda item: (
            float(item.get("draft") or 0),
            _bucket_rank(str(item.get("starter", ""))),
            0 if "missing" in str(item.get("warnings", "")) else 1,
        ),
    )
    return f"{safe['name']} {safe['position']}: draft signal {safe.get('draft') or 'missing'}"


def _defer_context(
    defer: dict[str, str],
    zone: dict[str, str],
    *,
    missing_baseline: bool = False,
) -> str:
    if defer:
        return (f"{defer.get('defer_review_band', '')}: {defer.get('review_rationale', '')}").strip(
            ": "
        )
    if missing_baseline or (zone and zone.get("review_label") == MANUAL_ONLY_NO_BASELINE):
        return (
            f"{MANUAL_ONLY_NO_BASELINE}: no admitted exact pick baseline exists; "
            "do not use this pick for exact trade, draft, or cut equivalence."
        )
    if zone:
        return f"{zone.get('review_label', '')}: {zone.get('human_review_question', '')}"
    return "no_defer_context_loaded"


def _confidence_status(candidates: list[dict[str, object]], pick_score: float | None) -> str:
    if pick_score is None:
        return MANUAL_ONLY_NO_BASELINE
    if not candidates:
        return "candidate_cluster_missing"
    if any("missing" in str(candidate["warnings"]) for candidate in candidates[:3]):
        return "top_cluster_has_missing_evidence_review"
    return "candidate_cluster_loaded_review_only"


def _manual_question_fields(
    pick: str,
    label: str,
    roster_pressure: str,
    *,
    missing_baseline: bool = False,
) -> dict[str, str]:
    questions = {
        "manual_question_rookie_profile": (
            f"For {pick}, which rookie profiles are carried by production, draft signal, "
            "athletic profile, or team-share evidence?"
        ),
        "manual_question_roster_fit": (
            f"How does the {pick} candidate cluster compare with current roster pressure?"
        ),
        "manual_question_pick_value": (
            "Is the candidate cluster close enough to the owned pick value to deserve "
            "manual review?"
        ),
        "manual_question_trade_defer": (
            "Does defer or trade-down context need review before assuming pick use?"
        ),
        "manual_question_source_risk": (
            "Are the key risks source-driven, missing-data driven, or football-profile driven?"
        ),
    }
    if missing_baseline:
        questions["manual_question_pick_value"] = (
            "No admitted exact model baseline exists for this pick; use manual-only "
            "watchlist review."
        )
    if label == "hold_pick_value_context":
        questions["manual_question_trade_defer"] = (
            "Review defer or hold-value context manually before comparing this pick "
            "to alternatives."
        )
    if roster_pressure:
        questions["manual_question_roster_fit"] = (
            f"Roster pressure context to consider: {roster_pressure}."
        )
    return questions


def _manual_questions(fields: dict[str, str]) -> str:
    return " ".join(value for value in fields.values() if value)


def _market_reality_context(
    zone_row: dict[str, str],
    nearby_assets: list[dict[str, object]],
    *,
    manual_only: bool = False,
) -> str:
    if manual_only:
        return (
            "Manual-only pick baseline; no exact trade-market equivalence or package "
            "context is admitted."
        )
    zone_context = str(zone_row.get("trade_market_reality_context") or "")
    if zone_context:
        return zone_context
    if _has_elite_current_asset(nearby_assets[:8]) or any(
        str(asset.get("equivalence_guardrail")) for asset in nearby_assets[:8]
    ):
        return (
            "Nearby assets are internal model-value neighbors only; this is not a claim "
            "that one pick can buy those players or a one-for-one trade-market equivalent."
        )
    return "Verify actual trade market separately; this lab is internal model context."


def _equivalence_guardrail(
    zone_row: dict[str, str],
    nearby_assets: list[dict[str, object]],
    *,
    manual_only: bool = False,
) -> str:
    if manual_only:
        return "no_exact_equivalence_without_pick_baseline"
    if _has_elite_current_asset(nearby_assets[:8]):
        return TRADE_MARKET_GUARDRAIL
    return str(zone_row.get("equivalence_guardrail") or "nearby_model_value_not_trade_equivalence")


def _has_elite_current_asset(assets: list[dict[str, object]]) -> bool:
    for asset in assets:
        if asset.get("type") in {"current_rostered_player", "available_or_context_player"}:
            score = _float(asset.get("score"))
            if score is not None and score >= 78:
                return True
    return False


def _roster_pressure_context(
    pressure_rows: list[dict[str, str]],
    opportunity_rows: list[dict[str, str]],
) -> str:
    pressure_count = sum(
        1 for row in pressure_rows if row.get("pressure_band") == "required_pressure_zone_review"
    )
    expensive = [
        row.get("player_name", "")
        for row in opportunity_rows
        if row.get("opportunity_cost_label") == "expensive_to_cut"
    ]
    examples = ", ".join(expensive[:3])
    return f"{pressure_count} required pressure row(s); expensive-to-cut examples: {examples}"


def _components_for_pick(
    row: dict[str, object],
    defer: dict[str, str],
    zone: dict[str, str],
) -> list[dict[str, object]]:
    pick = str(row["pick_label"])
    components = []
    for name, value, context, source in (
        ("pick_value_score", row["pick_value_score"], "Owned pick baseline.", PICK_INVENTORY_ROWS),
        (
            "top_rookie_candidates",
            row["top_rookie_candidates"],
            "Candidate cluster from rookie pick windows.",
            PICK_CANDIDATES,
        ),
        (
                "nearby_startup_slot_assets",
                row["nearby_startup_slot_assets"],
                "Nearby assets by internal startup slot; not trade-market equivalents.",
                STARTUP_SLOT_ROWS,
            ),
        (
            "defer_review_context",
            row["defer_review_context"],
            "Defer/trade-down context if available.",
            PICK_DEFER_ROWS if defer else STARTUP_PICK_ZONE_ROWS,
        ),
        ("review_label", row["review_label"], "Review label, not recommendation.", PICK_CANDIDATES),
    ):
        components.append(
            {
                "component_key": f"{pick}:{name}",
                "pick_label": pick,
                "component_layer": "rookie_pick_decision_lab",
                "component_name": name,
                "component_value": value,
                "component_context": context,
                "allowed_input_file": str(source),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    if zone:
        components.append(
            {
                "component_key": f"{pick}:startup_pick_zone",
                "pick_label": pick,
                "component_layer": "startup_slot_context",
                "component_name": zone.get("review_label", ""),
                "component_value": zone.get("nearby_startup_assets", ""),
                "component_context": _join(
                    zone.get("human_review_question", ""),
                    zone.get("trade_market_reality_context", ""),
                ),
                "allowed_input_file": str(STARTUP_PICK_ZONE_ROWS),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return components


def _compare_rows_for_pick(
    pick: str,
    pick_score: float | None,
    candidates: list[dict[str, object]],
    assets: list[dict[str, object]],
    defer: dict[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if defer and defer.get("future_pick_label"):
        mode = _defer_comparison_mode(defer)
        rows.append(
            _compare_row(
                pick,
                "future_pick_defer_context",
                mode,
                defer.get("defer_scenario_key", ""),
                "concrete_comparator_loaded",
                defer.get("future_pick_label", ""),
                "PICK",
                defer.get("future_pick_value_review_score", ""),
                str(PICK_DEFER_ROWS),
                "future_pick_value_review_score",
                "review_v4_pick_defer_context",
                defer.get("future_tier_label", ""),
                pick_score,
                defer.get("warning_flags", ""),
            )
        )
    for candidate in candidates[:8]:
        rows.append(
            _compare_row(
                pick,
                "rookie_candidate",
                "rookie_candidate_comparison",
                f"{pick}:rookie:{_norm(candidate['name'])}",
                "concrete_comparator_loaded",
                candidate["name"],
                candidate["position"],
                candidate["score"],
                str(PICK_CANDIDATES),
                "league_format_adjusted_score",
                "review_v4_rookie_pick_candidate",
                str(candidate["window"]),
                pick_score,
                _risk_note(candidate),
            )
        )
    for asset in assets[:8]:
        rows.append(
            _compare_row(
                pick,
                "startup_slot_asset",
                _startup_asset_comparison_mode(asset),
                str(asset.get("key", "")) or f"startup:{_norm(asset['name'])}",
                "concrete_comparator_loaded",
                asset["name"],
                asset["position"],
                asset["score"],
                str(STARTUP_SLOT_ROWS),
                "model_score",
                "review_v4_startup_slot_context",
                asset["type"],
                pick_score,
                str(asset["warnings"]),
                _asset_trade_market_context(asset),
            )
        )
    return rows


def _defer_comparison_mode(defer: dict[str, str]) -> str:
    text = " ".join(
        (
            defer.get("defer_review_band", ""),
            defer.get("review_rationale", ""),
            defer.get("future_pick_label", ""),
        )
    ).lower()
    if "trade_down" in text or "trade-down" in text:
        return "trade_down_pick_comparison"
    return "future_pick_comparison"


def _startup_asset_comparison_mode(asset: dict[str, object]) -> str:
    if asset.get("type") in {"current_rostered_player", "available_or_context_player"}:
        return "current_player_comparison"
    return "startup_asset_comparison"


def _asset_trade_market_context(asset: dict[str, object]) -> str:
    context = str(asset.get("trade_market_reality_context") or "")
    if context:
        return context
    score = _float(asset.get("score"))
    if (
        asset.get("type") in {"current_rostered_player", "available_or_context_player"}
        and score is not None
        and score >= 78
    ):
        return (
            "Elite/current asset model neighbor only; not a one-for-one pick trade equivalent."
        )
    return ""


def _compare_row(
    pick: str,
    comparison_type: str,
    comparison_mode: str,
    comparator_key: str,
    comparator_source_status: str,
    name: object,
    position: object,
    score: object,
    source_path: str,
    source_column: str,
    lineage_class: str,
    context: object,
    pick_score: float | None,
    risk: str,
    market_reality_context: str = "",
) -> dict[str, object]:
    score_value = _float(score)
    gap = "" if pick_score is None or score_value is None else round(score_value - pick_score, 4)
    return {
        "compare_key": f"{pick}:{comparison_type}:{_norm(name)}",
        "pick_label": pick,
        "comparison_type": comparison_type,
        "comparison_mode": comparison_mode,
        "comparator_key": comparator_key,
        "comparator_source_status": comparator_source_status,
        "asset_name": name,
        "position": position,
        "asset_score": _blank(score_value),
        "source_path": source_path,
        "source_column": source_column,
        "lineage_class": lineage_class,
        "asset_context": context,
        "score_gap_to_pick": gap,
        "evidence_or_risk_note": risk,
        "trade_market_reality_context": market_reality_context,
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _prospect_component_receipts(
    prospect_components: list[dict[str, str]],
    candidate_names: set[str],
) -> list[dict[str, object]]:
    wanted_names = {_norm(name) for name in candidate_names}
    output: list[dict[str, object]] = []
    for component in prospect_components:
        name = component.get("entity_name", "")
        if _norm(name) not in wanted_names:
            continue
        output.append(
            {
                "component_key": f"prospect:{_norm(name)}:{component.get('component_name')}",
                "pick_label": "candidate_component_receipt",
                "component_layer": component.get("component_layer", ""),
                "component_name": component.get("component_name", ""),
                "component_value": component.get("component_value", ""),
                "component_context": component.get("component_warning", ""),
                "allowed_input_file": component.get("allowed_input_file", ""),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output[:300]


def _warnings_for_pick(row: dict[str, object]) -> list[dict[str, object]]:
    warnings = []
    seen: set[str] = set()
    for warning in str(row["warning_flags"]).split("|"):
        if not warning:
            continue
        if warning in seen:
            continue
        seen.add(warning)
        warnings.append(
            {
                "warning_key": f"{row['pick_label']}:{warning}",
                "pick_label": row["pick_label"],
                "warning_layer": "rookie_pick_decision_lab",
                "warning_code": warning,
                "warning_detail": warning.replace("_", " "),
                "next_action": "Use as review-only context; human decision required.",
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return warnings


def _candidate_names(candidates: list[dict[str, object]]) -> str:
    return " | ".join(
        f"{candidate['name']} {candidate['position']} ({candidate['score']})"
        for candidate in candidates
    )


def _asset_names(assets: list[dict[str, object]]) -> str:
    return " | ".join(f"{asset['name']} {asset['position']} ({asset['score']})" for asset in assets)


def _risk_note(candidate: dict[str, object]) -> str:
    notes = []
    warnings = str(candidate.get("warnings", ""))
    if "missing" in warnings:
        notes.append("missing evidence")
    if "source_limited" in warnings:
        notes.append("source-limited evidence")
    if candidate.get("sample") == "low_confidence_small_or_missing_sample":
        notes.append("thin historical bucket")
    if not notes:
        notes.append(str(candidate.get("rationale", "")) or "review candidate profile")
    return "; ".join(notes)


def _bucket_rank(value: str) -> int:
    return {"very_high": 5, "high": 4, "moderate": 3, "low": 2, "very_low": 1}.get(value, 0)


def _doc_text(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Rookie Pick Decision Lab",
        "",
        "## Scope",
        "",
        "This review-only lab summarizes candidate clusters, nearby startup-slot assets, "
        "defer context, and manual questions for each owned Niners rookie pick. It does "
        "not create final rookie draft recommendations.",
        "",
        "## Pick Rows",
        "",
        "| Pick | Label | Candidate Cluster | Nearby Assets |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['pick_label']} | {row['review_label']} | "
            f"{str(row['top_rookie_candidates']).replace(' | ', ', ')} | "
            f"{str(row['nearby_startup_slot_assets']).replace(' | ', ', ')} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Review labels are not recommendations.",
            "- Nearby model assets are internal value neighbors, not one-for-one "
            "trade-market equivalents.",
            "- ADP, market rankings, projections, mocks, big boards, and consensus are blocked.",
            "- Missing 5.04 or other baseline gaps stay quarantined.",
            "- No active rankings, My Team, War Board, readiness gates, or app promotion changed.",
        ]
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


def _norm(value: object) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def _join(*values: object) -> str:
    parts: list[str] = []
    for value in values:
        for part in str(value or "").split("|"):
            clean = part.strip()
            if clean and clean not in parts:
                parts.append(clean)
    return "|".join(parts)


def _float(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None


def _int(value: object) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _blank(value: float | None) -> str | float:
    return "" if value is None else round(value, 4)
