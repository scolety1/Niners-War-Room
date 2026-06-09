from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "startup_slot_simulator/latest"
DOC_PATH = Path("docs/model_v4/STARTUP_SLOT_SIMULATOR_REVIEW.md")
VERSION = "model_v4_startup_slot_simulator_0.1.0"

DYNASTY_ASSET_ROWS = MODEL_ROOT / "dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv"
ROOKIE_BOARD_ROWS = MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
ROOKIE_PICK_CANDIDATES = (
    MODEL_ROOT / "rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv"
)
PROSPECT_VALUE_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_review_rows.csv"
PROSPECT_COMPONENT_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_component_rows.csv"
PROSPECT_RECEIPTS = MODEL_ROOT / "prospect_value/latest/prospect_value_receipts.csv"
ROSTER_STATE_ROWS = MODEL_ROOT / "decision_calibration/latest/niners_roster_state_review.csv"
CUT_KEEP_ROWS = MODEL_ROOT / "decision_pressure/latest/cut_keep_pressure_review_rows.csv"
TRADE_AWAY_ROWS = MODEL_ROOT / "trade_review/latest/trade_away_candidate_review_rows.csv"
PICK_INVENTORY_ROWS = MODEL_ROOT / "pick_trade_defer/latest/niners_pick_inventory_review_rows.csv"
HISTORICAL_TUNING_ROWS = (
    MODEL_ROOT / "historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv"
)

NINERS_PICKS = ("2026 1.03", "2026 1.04", "2026 2.04", "2026 2.08", "2026 5.04")
REVIEW_ONLY_USE = "review_only_startup_slot_context_not_final_recommendation"
BLOCKED_USE = "do_not_use_as_adp_final_pick_cut_keep_trade_or_roster_recommendation"
MANUAL_ONLY_NO_BASELINE = "manual_only_no_exact_model_baseline"
ELITE_CURRENT_ASSET_SCORE = 78.0
TRADE_MARKET_GUARDRAIL = (
    "internal_model_neighbor_only_not_one_for_one_trade_equivalent"
)

REVIEW_HEADER = (
    "startup_slot_rank",
    "entity_key",
    "entity_type",
    "player_or_asset",
    "position",
    "team_or_college",
    "model_score",
    "source_path",
    "source_column",
    "lineage_class",
    "league_format_score",
    "confidence_cap",
    "trust_status",
    "slot_band",
    "nearby_assets_before",
    "nearby_assets_after",
    "pick_equivalent_context",
    "roster_pressure_context",
    "draft_capital_context",
    "evidence_status",
    "outcome_bucket_context",
    "why_this_slot",
    "trade_market_reality_context",
    "equivalence_guardrail",
    "warning_flags",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

COMPONENT_HEADER = (
    "component_key",
    "entity_key",
    "entity_type",
    "player_or_asset",
    "component_layer",
    "component_name",
    "component_value",
    "component_context",
    "allowed_input_file",
    "source_status",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

PICK_ZONE_HEADER = (
    "pick_label",
    "pick_value_review_score",
    "source_path",
    "source_column",
    "lineage_class",
    "pick_zone_band",
    "best_rookie_candidates",
    "nearby_startup_assets",
    "assets_above_pick",
    "assets_below_pick",
    "trade_market_reality_context",
    "equivalence_guardrail",
    "review_label",
    "human_review_question",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

BUCKET_HEADER = (
    "entity_key",
    "player_name",
    "position",
    "draft_year",
    "model_profile_bucket",
    "similar_historical_profile_count",
    "top_5_bucket",
    "top_10_bucket",
    "top_20_bucket",
    "top_30_bucket",
    "starter_bucket",
    "miss_bucket",
    "sample_size_status",
    "confidence_status",
    "main_positive_signals",
    "main_risk_signals",
    "warning_flags",
    "allowed_use",
    "blocked_use",
)

RECEIPT_HEADER = (
    "receipt_key",
    "entity_key",
    "player_or_asset",
    "receipt_layer",
    "receipt_pointer",
    "source_status",
    "allowed_input_file",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

WARNING_HEADER = (
    "warning_key",
    "entity_key",
    "player_or_asset",
    "warning_layer",
    "warning_code",
    "warning_detail",
    "next_action",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class StartupSlotSimulatorResult:
    review_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    pick_zone_rows: tuple[dict[str, object], ...]
    bucket_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_startup_slot_simulator() -> StartupSlotSimulatorResult:
    dynasty_rows = _read_rows(DYNASTY_ASSET_ROWS)
    rookie_rows = _read_rows(ROOKIE_BOARD_ROWS)
    prospect_rows = _read_rows(PROSPECT_VALUE_ROWS)
    component_source_rows = _read_rows(PROSPECT_COMPONENT_ROWS)
    receipt_source_rows = _read_rows(PROSPECT_RECEIPTS)
    roster_rows = _read_rows(ROSTER_STATE_ROWS)
    cut_rows = _read_rows(CUT_KEEP_ROWS)
    trade_rows = _read_rows(TRADE_AWAY_ROWS)
    pick_rows = _read_rows(PICK_INVENTORY_ROWS)
    pick_candidate_rows = _read_rows(ROOKIE_PICK_CANDIDATES)
    historical_rows = _read_rows(HISTORICAL_TUNING_ROWS)

    roster_context = _roster_context(roster_rows, cut_rows, trade_rows)
    prospect_lookup = {_normalize(row.get("prospect_name")): row for row in prospect_rows}
    entities = _current_player_entities(dynasty_rows, roster_context)
    entities.extend(_rookie_entities(rookie_rows, prospect_lookup))
    entities.extend(_pick_entities(pick_rows))

    review_rows = _ranked_review_rows(entities)
    bucket_lookup, bucket_rows = _bucket_rows(rookie_rows, prospect_lookup, historical_rows)
    review_rows = _attach_bucket_context(review_rows, bucket_lookup)
    pick_zone_rows = _pick_zone_rows(pick_rows, pick_candidate_rows, review_rows)
    component_rows = _component_rows(review_rows, component_source_rows, pick_zone_rows)
    receipt_rows = _receipt_rows(review_rows, receipt_source_rows)
    warning_rows = _warning_rows(review_rows, bucket_rows, pick_zone_rows)
    doc_text = _doc_text(review_rows, pick_zone_rows, bucket_rows)

    return StartupSlotSimulatorResult(
        review_rows=tuple(review_rows),
        component_rows=tuple(component_rows),
        pick_zone_rows=tuple(pick_zone_rows),
        bucket_rows=tuple(bucket_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        doc_text=doc_text,
    )


def write_startup_slot_simulator_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: StartupSlotSimulatorResult | None = None,
) -> dict[str, Path]:
    result = result or build_startup_slot_simulator()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "review_rows": output / "startup_slot_review_rows.csv",
        "component_rows": output / "startup_slot_component_rows.csv",
        "pick_zone_rows": output / "startup_slot_pick_zone_rows.csv",
        "bucket_rows": output / "startup_slot_bucket_rows.csv",
        "receipts": output / "startup_slot_receipts.csv",
        "warnings": output / "startup_slot_warnings.csv",
        "doc": Path(doc_path),
    }
    _write_csv(paths["review_rows"], REVIEW_HEADER, result.review_rows)
    _write_csv(paths["component_rows"], COMPONENT_HEADER, result.component_rows)
    _write_csv(paths["pick_zone_rows"], PICK_ZONE_HEADER, result.pick_zone_rows)
    _write_csv(paths["bucket_rows"], BUCKET_HEADER, result.bucket_rows)
    _write_csv(paths["receipts"], RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths["warnings"], WARNING_HEADER, result.warning_rows)
    paths["doc"].parent.mkdir(parents=True, exist_ok=True)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _current_player_entities(
    dynasty_rows: list[dict[str, str]],
    roster_context: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    entities: list[dict[str, object]] = []
    for row in dynasty_rows:
        if row.get("asset_type") != "current_player":
            continue
        name = row.get("asset_name", "")
        key = row.get("asset_key") or f"current:{_normalize(name)}:{row.get('position', '')}"
        context = roster_context.get(_normalize(name), {})
        if context:
            entity_type = (
                "potential_drop_player"
                if context.get("pressure_band")
                in {"required_pressure_zone_review", "protectable_depth_review"}
                else "current_rostered_player"
            )
        else:
            entity_type = "available_or_context_player"
        score = _float(row.get("dynasty_asset_value_review_score"))
        entities.append(
            {
                "entity_key": key,
                "entity_type": entity_type,
                "player_or_asset": name,
                "position": row.get("position", ""),
                "team_or_college": row.get("team_or_college", ""),
                "model_score": score,
                "league_format_score": score,
                "confidence_cap": row.get("confidence_cap", ""),
                "trust_status": row.get("value_source_layer", "current_player_model_value"),
                "roster_pressure_context": _join_present(
                    context.get("pressure_band", ""),
                    context.get("trade_away_review_band", ""),
                ),
                "draft_capital_context": "",
                "evidence_status": row.get("value_source_layer", ""),
                "warning_flags": _join_present(
                    row.get("warning_flags", ""), context.get("warning_flags", "")
                ),
                "source_file": str(DYNASTY_ASSET_ROWS),
                "score_field": "dynasty_asset_value_review_score",
                "lineage_class": "review_v4_dynasty_asset",
            }
        )
    return entities


def _rookie_entities(
    rookie_rows: list[dict[str, str]],
    prospect_lookup: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    entities: list[dict[str, object]] = []
    for row in rookie_rows:
        if row.get("evidence_status") not in {"draftable_review", "manual_scout_source_review"}:
            continue
        name = row.get("prospect_name", "")
        prospect = prospect_lookup.get(_normalize(name), {})
        draft_context = _draft_context(prospect)
        score = _float(row.get("league_format_adjusted_score"))
        entities.append(
            {
                "entity_key": row.get("rookie_board_key", f"prospect:2026:{_normalize(name)}"),
                "entity_type": "rookie_prospect",
                "player_or_asset": name,
                "position": row.get("position", ""),
                "team_or_college": _join_present(
                    row.get("nfl_team", ""), row.get("college", ""), sep=" / "
                ),
                "model_score": score,
                "league_format_score": score,
                "confidence_cap": row.get("confidence_cap", ""),
                "trust_status": row.get("evidence_status", ""),
                "roster_pressure_context": row.get("roster_fit_context", ""),
                "draft_capital_context": draft_context,
                "evidence_status": row.get("evidence_status", ""),
                "warning_flags": _join_present(
                    row.get("warning_flags", ""),
                    _position_warning(row.get("position", "")),
                ),
                "source_file": str(ROOKIE_BOARD_ROWS),
                "score_field": "league_format_adjusted_score",
                "lineage_class": "review_v4_rookie_board",
            }
        )
    return entities


def _pick_entities(pick_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    entities: list[dict[str, object]] = []
    for row in pick_rows:
        pick_label = row.get("pick_label", "")
        if pick_label not in NINERS_PICKS:
            continue
        score = _float(row.get("pick_value_review_score"))
        entities.append(
            {
                "entity_key": row.get("pick_review_key", f"pick:{pick_label}"),
                "entity_type": "owned_rookie_pick",
                "player_or_asset": pick_label,
                "position": "PICK",
                "team_or_college": "Niners",
                "model_score": score,
                "league_format_score": score,
                "confidence_cap": "",
                "trust_status": row.get("baseline_match_status", ""),
                "roster_pressure_context": row.get("roster_pressure_context", ""),
                "draft_capital_context": row.get("tier_label", ""),
                "evidence_status": row.get("baseline_match_status", ""),
                "warning_flags": row.get("warning_flags", ""),
                "source_file": str(PICK_INVENTORY_ROWS),
                "score_field": "pick_value_review_score",
                "lineage_class": "review_v4_owned_pick",
            }
        )
    return entities


def _ranked_review_rows(entities: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked = sorted(
        [entity for entity in entities if entity.get("model_score") is not None],
        key=lambda row: (-float(row["model_score"]), str(row["player_or_asset"]).lower()),
    )
    rows: list[dict[str, object]] = []
    for index, entity in enumerate(ranked, start=1):
        before = ranked[index - 2]["player_or_asset"] if index > 1 else ""
        after = ranked[index]["player_or_asset"] if index < len(ranked) else ""
        score = float(entity["model_score"])
        pick_equivalent_context = _pick_equivalent(score, entity)
        warning_flags = _join_present(
            entity["warning_flags"],
            _trade_market_warning(entity, score),
            "review_only_no_final_recommendation",
        )
        rows.append(
            {
                "startup_slot_rank": index,
                "entity_key": entity["entity_key"],
                "entity_type": entity["entity_type"],
                "player_or_asset": entity["player_or_asset"],
                "position": entity["position"],
                "team_or_college": entity["team_or_college"],
                "model_score": round(score, 4),
                "source_path": entity["source_file"],
                "source_column": entity["score_field"],
                "lineage_class": entity["lineage_class"],
                "league_format_score": round(float(entity["league_format_score"]), 4),
                "confidence_cap": entity["confidence_cap"],
                "trust_status": entity["trust_status"],
                "slot_band": _slot_band(index, score),
                "nearby_assets_before": before,
                "nearby_assets_after": after,
                "pick_equivalent_context": pick_equivalent_context,
                "roster_pressure_context": entity["roster_pressure_context"],
                "draft_capital_context": entity["draft_capital_context"],
                "evidence_status": entity["evidence_status"],
                "outcome_bucket_context": "",
                "why_this_slot": _why_slot(entity, before, after),
                "trade_market_reality_context": _entity_trade_market_context(entity, score),
                "equivalence_guardrail": _entity_equivalence_guardrail(entity, score),
                "warning_flags": warning_flags,
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return rows


def _bucket_rows(
    rookie_rows: list[dict[str, str]],
    prospect_lookup: dict[str, dict[str, str]],
    historical_rows: list[dict[str, str]],
) -> tuple[dict[str, str], list[dict[str, object]]]:
    profiles = [_historical_profile(row) for row in historical_rows if _historical_usable(row)]
    profile_counts: dict[str, list[dict[str, str]]] = {}
    for row, profile in profiles:
        profile_counts.setdefault(profile, []).append(row)
    lookup: dict[str, str] = {}
    rows: list[dict[str, object]] = []
    for row in rookie_rows:
        if row.get("evidence_status") not in {"draftable_review", "manual_scout_source_review"}:
            continue
        name = row.get("prospect_name", "")
        prospect = prospect_lookup.get(_normalize(name), {})
        profile = _current_profile(row, prospect)
        similar = profile_counts.get(profile, [])
        rates = _bucket_rates(similar)
        sample_status = _sample_status(len(similar))
        warnings = [row.get("warning_flags", "")]
        if len(similar) < 8:
            warnings.append("missing_or_small_outcome_history_low_confidence")
        if row.get("draft_year") == "2025":
            warnings.append("rookie_year_only_outcome_immature")
        if row.get("position") == "TE":
            warnings.append("no_premium_te_bucket_caution")
        if row.get("position") == "QB":
            warnings.append("one_qb_qb_bucket_caution")
        bucket = {
            "entity_key": row.get("rookie_board_key", ""),
            "player_name": name,
            "position": row.get("position", ""),
            "draft_year": row.get("draft_year", ""),
            "model_profile_bucket": profile,
            "similar_historical_profile_count": len(similar),
            "top_5_bucket": rates["top_5"],
            "top_10_bucket": rates["top_10"],
            "top_20_bucket": rates["top_20"],
            "top_30_bucket": rates["top_30"],
            "starter_bucket": rates["starter"],
            "miss_bucket": rates["miss"],
            "sample_size_status": sample_status,
            "confidence_status": row.get("evidence_status", ""),
            "main_positive_signals": _positive_signals(row, prospect),
            "main_risk_signals": _risk_signals(row, prospect),
            "warning_flags": _join_present(*warnings),
            "allowed_use": "review_only_outcome_bucket_context_not_formula_input",
            "blocked_use": "do_not_feed_bucket_back_into_rankings_or_final_recommendations",
        }
        lookup[bucket["entity_key"]] = (
            f"{profile}: top20 {bucket['top_20_bucket']}, starter {bucket['starter_bucket']}"
        )
        rows.append(bucket)
    return lookup, rows


def _attach_bucket_context(
    review_rows: list[dict[str, object]],
    bucket_lookup: dict[str, str],
) -> list[dict[str, object]]:
    for row in review_rows:
        context = bucket_lookup.get(str(row["entity_key"]), "")
        if context:
            row["outcome_bucket_context"] = context
        for hidden in ("_source_file", "_score_field"):
            row.pop(hidden, None)
    return review_rows


def _pick_zone_rows(
    pick_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    review_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    pick_lookup = {row.get("pick_label"): row for row in pick_rows}
    rows: list[dict[str, object]] = []
    for pick in NINERS_PICKS:
        pick_row = pick_lookup.get(pick, {})
        pick_score = _float(pick_row.get("pick_value_review_score"))
        candidates = [row for row in candidate_rows if row.get("pick_label") == pick][:6]
        nearby = _near_score_assets(review_rows, pick_score, limit=8)
        if pick_score is None:
            above: list[str] = []
            below: list[str] = []
        else:
            above = [
                str(row["player_or_asset"])
                for row in review_rows
                if _float(row.get("model_score")) is not None
                and float(row["model_score"]) >= float(pick_score) + 5
            ][:5]
            below = [
                str(row["player_or_asset"])
                for row in review_rows
                if _float(row.get("model_score")) is not None
                and float(row["model_score"]) <= float(pick_score) - 5
            ][:5]
        label = _pick_zone_label(pick_score, candidates, nearby)
        market_reality = _trade_market_reality_context(pick, pick_score, nearby)
        equivalence_guardrail = _equivalence_guardrail(pick_score, nearby)
        rows.append(
            {
                "pick_label": pick,
                "pick_value_review_score": "" if pick_score is None else round(pick_score, 4),
                "source_path": str(PICK_INVENTORY_ROWS),
                "source_column": "pick_value_review_score",
                "lineage_class": "review_v4_owned_pick",
                "pick_zone_band": (
                    MANUAL_ONLY_NO_BASELINE
                    if pick_score is None
                    else pick_row.get("tier_label", "missing_pick_value_baseline")
                ),
                "best_rookie_candidates": _candidate_names(candidates),
                "nearby_startup_assets": " | ".join(nearby),
                "assets_above_pick": " | ".join(above),
                "assets_below_pick": " | ".join(below),
                "trade_market_reality_context": market_reality,
                "equivalence_guardrail": equivalence_guardrail,
                "review_label": label,
                "human_review_question": _pick_question(pick, label),
                "allowed_use": "review_only_pick_zone_context_not_final_selection",
                "blocked_use": BLOCKED_USE,
                "warning_flags": _join_present(
                    pick_row.get("warning_flags", ""),
                    MANUAL_ONLY_NO_BASELINE if pick_score is None else "",
                    "pick_value_baseline_missing" if pick_score is None else "",
                    TRADE_MARKET_GUARDRAIL if pick_score is not None else "",
                    "elite_current_asset_requires_package_premium_review"
                    if _has_elite_current_asset(nearby)
                    else "",
                    "manual_decision_required",
                ),
                "formula_version": VERSION,
            }
        )
    return rows


def _component_rows(
    review_rows: list[dict[str, object]],
    source_components: list[dict[str, str]],
    pick_zone_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    source_lookup: dict[str, list[dict[str, str]]] = {}
    for row in source_components:
        source_lookup.setdefault(row.get("entity_key", ""), []).append(row)
    rows: list[dict[str, object]] = []
    for row in review_rows:
        key = str(row["entity_key"])
        rows.append(
            _component_row(row, "startup_slot", "unified_model_score", row["model_score"], "")
        )
        for source in source_lookup.get(key, [])[:8]:
            rows.append(
                {
                    "component_key": f"{key}:{source.get('component_name')}",
                    "entity_key": key,
                    "entity_type": row["entity_type"],
                    "player_or_asset": row["player_or_asset"],
                    "component_layer": source.get("component_layer", ""),
                    "component_name": source.get("component_name", ""),
                    "component_value": source.get("component_value", ""),
                    "component_context": source.get("component_warning", ""),
                    "allowed_input_file": source.get("allowed_input_file", ""),
                    "source_status": source.get("source_status", ""),
                    "allowed_use": REVIEW_ONLY_USE,
                    "blocked_use": BLOCKED_USE,
                    "formula_version": VERSION,
                }
            )
    for row in pick_zone_rows:
        key = f"pick_zone:{row['pick_label']}"
        rows.append(
            {
                "component_key": key,
                "entity_key": key,
                "entity_type": "pick_zone",
                "player_or_asset": row["pick_label"],
                "component_layer": "pick_zone_context",
                "component_name": row["review_label"],
                "component_value": row["pick_value_review_score"],
                "component_context": row["human_review_question"],
                "allowed_input_file": str(ROOKIE_PICK_CANDIDATES),
                "source_status": "review_only_pick_zone_context",
                "allowed_use": "review_only_pick_zone_context_not_final_selection",
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return rows


def _component_row(
    row: dict[str, object],
    layer: str,
    name: str,
    value: object,
    context: str,
) -> dict[str, object]:
    return {
        "component_key": f"{row['entity_key']}:{name}",
        "entity_key": row["entity_key"],
        "entity_type": row["entity_type"],
        "player_or_asset": row["player_or_asset"],
        "component_layer": layer,
        "component_name": name,
        "component_value": value,
        "component_context": context,
        "allowed_input_file": "existing_review_only_model_output",
        "source_status": "review_only_existing_model_score",
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _receipt_rows(
    review_rows: list[dict[str, object]],
    source_receipts: list[dict[str, str]],
) -> list[dict[str, object]]:
    source_lookup: dict[str, list[dict[str, str]]] = {}
    for row in source_receipts:
        source_lookup.setdefault(row.get("entity_key", ""), []).append(row)
    rows: list[dict[str, object]] = []
    for row in review_rows:
        key = str(row["entity_key"])
        rows.append(
            {
                "receipt_key": f"{key}:startup_slot_score_source",
                "entity_key": key,
                "player_or_asset": row["player_or_asset"],
                "receipt_layer": "startup_slot_score_source",
                "receipt_pointer": "review-only model output already generated before simulator",
                "source_status": "review_only_derived_from_existing_model_output",
                "allowed_input_file": "dynasty_asset/prospect/pick review outputs",
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
        for receipt in source_lookup.get(key, [])[:5]:
            rows.append(
                {
                    "receipt_key": f"{key}:{receipt.get('feature_group')}",
                    "entity_key": key,
                    "player_or_asset": row["player_or_asset"],
                    "receipt_layer": receipt.get("receipt_layer", ""),
                    "receipt_pointer": receipt.get("receipt_pointer", ""),
                    "source_status": receipt.get("source_status", ""),
                    "allowed_input_file": receipt.get("allowed_input_file", ""),
                    "allowed_use": REVIEW_ONLY_USE,
                    "blocked_use": BLOCKED_USE,
                    "formula_version": VERSION,
                }
            )
    return rows


def _warning_rows(
    review_rows: list[dict[str, object]],
    bucket_rows: list[dict[str, object]],
    pick_zone_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in review_rows:
        for warning in str(row.get("warning_flags", "")).split("|"):
            if not warning:
                continue
            rows.append(
                _warning(row["entity_key"], row["player_or_asset"], "startup_slot", warning)
            )
        if row.get("position") == "TE":
            rows.append(
                _warning(
                    row["entity_key"], row["player_or_asset"], "format", "no_premium_te_caution"
                )
            )
        if row.get("position") == "QB":
            rows.append(
                _warning(row["entity_key"], row["player_or_asset"], "format", "one_qb_qb_caution")
            )
    for row in bucket_rows:
        if "low_confidence" in str(row.get("sample_size_status", "")):
            rows.append(
                _warning(
                    row["entity_key"],
                    row["player_name"],
                    "outcome_bucket",
                    "missing_outcome_history_low_confidence",
                )
            )
    for row in pick_zone_rows:
        rows.append(
            _warning(
                f"pick_zone:{row['pick_label']}",
                row["pick_label"],
                "pick_zone",
                row["review_label"],
            )
        )
    return rows


def _warning(entity_key: object, name: object, layer: str, code: str) -> dict[str, object]:
    return {
        "warning_key": f"{entity_key}:{layer}:{code}",
        "entity_key": entity_key,
        "player_or_asset": name,
        "warning_layer": layer,
        "warning_code": code,
        "warning_detail": code.replace("_", " "),
        "next_action": "Use as review context only; human decision required.",
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _roster_context(
    roster_rows: list[dict[str, str]],
    cut_rows: list[dict[str, str]],
    trade_rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    context: dict[str, dict[str, str]] = {}
    for row in roster_rows:
        context[_normalize(row.get("player_name"))] = {
            "pressure_band": "rostered_review",
            "warning_flags": row.get("warning_flags", ""),
        }
    for row in cut_rows:
        context.setdefault(_normalize(row.get("player_name")), {}).update(
            {
                "pressure_band": row.get("pressure_band", ""),
                "warning_flags": row.get("warning_flags", ""),
            }
        )
    for row in trade_rows:
        context.setdefault(_normalize(row.get("player_name")), {}).update(
            {"trade_away_review_band": row.get("trade_away_review_band", "")}
        )
    return context


def _historical_usable(row: dict[str, str]) -> bool:
    return (
        row.get("Outcome Loaded") == "True"
        and row.get("Outcome Category") != ""
        and row.get("Draft Year") in {"2021", "2022", "2023", "2024"}
    )


def _historical_profile(row: dict[str, str]) -> tuple[dict[str, str], str]:
    return row, _profile_bucket(
        row.get("Pos", ""),
        _int(row.get("Draft Round")),
        _int(row.get("Overall Pick")),
        _float(row.get("Production Score")),
        _float(row.get("College Team Share")),
        _float(row.get("NFL Draft Pick Signal")),
    )


def _current_profile(row: dict[str, str], prospect: dict[str, str]) -> str:
    return _profile_bucket(
        row.get("position", ""),
        _draft_round_from_context(prospect),
        _draft_pick_from_context(prospect),
        _float(prospect.get("production_score")),
        _float(prospect.get("market_share_score")),
        _float(prospect.get("draft_capital_score")),
    )


def _profile_bucket(
    position: str,
    round_value: int | None,
    overall_pick: int | None,
    production: float | None,
    share: float | None,
    draft_score: float | None,
) -> str:
    position = position or "UNK"
    round_value = round_value or 99
    if not draft_score and round_value >= 90:
        return "no_draft_capital_watchlist"
    if position == "QB":
        return "qb_1qb_discounted"
    if position == "TE":
        return "elite_te_no_premium" if round_value <= 2 else "te_no_premium_depth"
    strong_production = (production or 0) >= 75 or (share or 0) >= 75
    low_share = share is not None and share < 45
    if round_value == 1 and position == "RB":
        return "round_1_rb_strong_production" if strong_production else "round_1_rb_capital_profile"
    if round_value == 1 and position == "WR":
        return (
            "round_1_wr_low_team_share_high_capital" if low_share else "round_1_wr_strong_profile"
        )
    if round_value == 2 and position == "RB":
        return "round_2_rb_receiving_role"
    if round_value >= 4 and position == "WR" and strong_production:
        return "day_3_wr_elite_team_share"
    if round_value >= 4 and position == "RB" and strong_production:
        return "day_3_rb_production_outlier"
    if round_value <= 3:
        return f"day_2_{position.lower()}_profile"
    return f"late_round_{position.lower()}_watchlist"


def _bucket_rates(rows: list[dict[str, str]]) -> dict[str, str]:
    if not rows:
        return {
            "top_5": "low_confidence",
            "top_10": "low_confidence",
            "top_20": "low_confidence",
            "top_30": "low_confidence",
            "starter": "low_confidence",
            "miss": "low_confidence",
        }
    diff = sum(1 for row in rows if row.get("Difference Maker?") == "True")
    strict = sum(1 for row in rows if row.get("Strict Starter Hit?") == "True")
    broad = sum(1 for row in rows if row.get("Broad Outcome Hit?") == "True")
    misses = sum(1 for row in rows if row.get("Outcome Category") in {"miss", "replacement"})
    count = len(rows)
    return {
        "top_5": _rate_label(diff / count * 0.35),
        "top_10": _rate_label(diff / count * 0.65),
        "top_20": _rate_label(diff / count),
        "top_30": _rate_label(max(diff, strict) / count),
        "starter": _rate_label(max(strict, broad) / count),
        "miss": _rate_label(misses / count),
    }


def _rate_label(value: float) -> str:
    if value >= 0.6:
        return "very_high"
    if value >= 0.4:
        return "high"
    if value >= 0.2:
        return "moderate"
    if value > 0:
        return "low"
    return "very_low"


def _sample_status(count: int) -> str:
    if count >= 20:
        return "adequate_historical_sample"
    if count >= 8:
        return "thin_historical_sample"
    return "low_confidence_small_or_missing_sample"


def _positive_signals(row: dict[str, str], prospect: dict[str, str]) -> str:
    signals: list[str] = []
    if (_float(prospect.get("draft_capital_score")) or 0) >= 75:
        signals.append("strong NFL draft pick signal")
    if (_float(prospect.get("production_score")) or 0) >= 75:
        signals.append("strong college production")
    if (_float(prospect.get("market_share_score")) or 0) >= 75:
        signals.append("strong college team share")
    if (_float(prospect.get("athletic_prior_score")) or 0) >= 75:
        signals.append("strong athletic prior")
    return "; ".join(signals) or f"model score {row.get('league_format_adjusted_score', '')}"


def _risk_signals(row: dict[str, str], prospect: dict[str, str]) -> str:
    risks: list[str] = []
    draft_round = _draft_round_from_context(prospect)
    if draft_round and draft_round >= 4:
        risks.append("day-three draft capital skepticism")
    if row.get("position") == "TE":
        risks.append("no-premium TE replaceability")
    if row.get("position") == "QB":
        risks.append("10-team 1QB replaceability")
    warnings = str(row.get("warning_flags", ""))
    if "missing" in warnings:
        risks.append("missing evidence warning")
    return "; ".join(risks) or "no major profile risk surfaced"


def _pick_zone_label(
    pick_score: float | None,
    candidates: list[dict[str, str]],
    nearby: list[str],
) -> str:
    if pick_score is None:
        return MANUAL_ONLY_NO_BASELINE
    candidate_scores = [_float(row.get("league_format_adjusted_score")) for row in candidates]
    candidate_scores = [score for score in candidate_scores if score is not None]
    if not candidate_scores:
        return "manual_decision_required"
    best_gap = max(candidate_scores) - pick_score
    if best_gap < -12:
        return "review_trade_down_or_defer"
    if abs(best_gap) <= 6 or nearby:
        return "review_rookie_vs_drop_player"
    if best_gap < -6:
        return "review_pick_value_gap"
    return "review_no_clear_edge"


def _pick_question(pick: str, label: str) -> str:
    if label == MANUAL_ONLY_NO_BASELINE:
        return (
            f"For {pick}, no admitted exact model baseline exists. Treat this as manual-only "
            "watchlist context, not a trade, draft, or cut equivalence."
        )
    if label == "review_trade_down_or_defer":
        return f"For {pick}, compare rookie use against trade-down/defer context before acting."
    if label == "review_rookie_vs_drop_player":
        return (
            f"For {pick}, inspect rookies and nearby current/drop players "
            "in the same model slot band."
        )
    if label == "review_pick_value_gap":
        return f"For {pick}, decide whether the rookie gap to pick baseline is acceptable."
    return f"For {pick}, human review required; no automatic recommendation."


def _near_score_assets(
    rows: list[dict[str, object]],
    score: float | None,
    *,
    limit: int,
) -> list[str]:
    if score is None:
        return []
    nearby = sorted(
        rows,
        key=lambda row: (
            abs(float(row.get("model_score", 0)) - score),
            int(row["startup_slot_rank"]),
        ),
    )
    return [
        f"{row['player_or_asset']} ({row['model_score']})"
        for row in nearby
        if row.get("entity_type") != "owned_rookie_pick"
    ][:limit]


def _candidate_names(rows: list[dict[str, str]]) -> str:
    return " | ".join(
        f"{row.get('prospect_name')} ({row.get('league_format_adjusted_score')})" for row in rows
    )


def _slot_band(rank: int, score: float) -> str:
    if rank <= 10 or score >= 80:
        return "elite_internal_startup_slot"
    if rank <= 30 or score >= 65:
        return "early_core_asset_slot"
    if rank <= 60 or score >= 50:
        return "middle_roster_asset_slot"
    if rank <= 100 or score >= 35:
        return "depth_or_rookie_pick_zone"
    return "watchlist_or_replacement_slot"


def _pick_equivalent(score: float, entity: dict[str, object] | None = None) -> str:
    prefix = ""
    if entity and _is_elite_current_asset(entity, score):
        prefix = "internal_value_zone_only_not_trade_market_equivalent: "
    if score >= 88:
        return prefix + "around_2026_1.03_1.04_review_zone"
    if score >= 68:
        return prefix + "around_2026_2.04_review_zone"
    if score >= 55:
        return prefix + "around_2026_2.08_review_zone"
    if score >= 20:
        return prefix + "around_2026_5.04_or_depth_review_zone"
    return prefix + "below_owned_pick_baseline_review_zone"


def _trade_market_warning(entity: dict[str, object], score: float) -> str:
    if _is_elite_current_asset(entity, score):
        return "elite_current_asset_not_single_pick_trade_equivalent"
    if entity.get("entity_type") == "owned_rookie_pick" and score >= 88:
        return "pick_baseline_not_elite_player_trade_offer"
    return ""


def _entity_trade_market_context(entity: dict[str, object], score: float) -> str:
    if _is_elite_current_asset(entity, score):
        return (
            "Elite/current asset shown by internal model value only; do not treat the "
            "pick-equivalent label as a one-pick trade market price."
        )
    if entity.get("entity_type") == "owned_rookie_pick":
        return (
            "Pick baseline is internal opportunity-cost context; it is not a claim that "
            "one pick buys nearby elite/current players."
        )
    return "Internal model context only; verify trade market separately."


def _entity_equivalence_guardrail(entity: dict[str, object], score: float) -> str:
    if _is_elite_current_asset(entity, score):
        return "elite_current_asset_not_single_pick_trade_equivalent"
    if entity.get("entity_type") == "owned_rookie_pick":
        return "pick_baseline_not_elite_player_trade_offer"
    return "nearby_model_value_not_trade_equivalence"


def _is_elite_current_asset(entity: dict[str, object], score: float) -> bool:
    return (
        entity.get("entity_type") in {"current_rostered_player", "available_or_context_player"}
        and entity.get("position") in {"RB", "WR", "TE", "QB"}
        and score >= ELITE_CURRENT_ASSET_SCORE
    )


def _has_elite_current_asset(nearby: list[str]) -> bool:
    return any(_asset_score_from_label(asset) >= ELITE_CURRENT_ASSET_SCORE for asset in nearby)


def _asset_score_from_label(asset_label: str) -> float:
    match = re.search(r"\(([-+]?\d+(?:\.\d+)?)\)\s*$", asset_label)
    if not match:
        return 0.0
    return float(match.group(1))


def _trade_market_reality_context(
    pick: str,
    pick_score: float | None,
    nearby: list[str],
) -> str:
    if pick_score is None:
        return (
            "Manual-only pick baseline; no trade-market equivalence or package context is admitted."
        )
    if _has_elite_current_asset(nearby):
        return (
            f"{pick} is shown near elite/current assets by internal model score only. "
            "This is opportunity-cost context, not a claim that one pick can buy those players."
        )
    return (
        "Nearby assets are internal value neighbors only; verify actual trade market separately."
    )


def _equivalence_guardrail(pick_score: float | None, nearby: list[str]) -> str:
    if pick_score is None:
        return "no_exact_equivalence_without_pick_baseline"
    if _has_elite_current_asset(nearby):
        return TRADE_MARKET_GUARDRAIL
    return "nearby_model_value_not_trade_equivalence"


def _why_slot(entity: dict[str, object], before: object, after: object) -> str:
    name = entity["player_or_asset"]
    position = entity["position"]
    entity_type = entity["entity_type"]
    score = entity["model_score"]
    if entity_type == "rookie_prospect":
        return (
            f"{name} slots here from rookie model score {score}; compare to {before or 'top'} "
            f"above and {after or 'bottom'} below before any human pick decision."
        )
    if entity_type == "owned_rookie_pick":
        return (
            f"{name} is an owned pick baseline, used only as internal opportunity-cost "
            "context; it is not a one-pick trade price for nearby players."
        )
    return f"{name} ({position}) slots here from current dynasty asset value {score}."


def _draft_context(prospect: dict[str, str]) -> str:
    draft_score = prospect.get("draft_capital_score", "")
    if not draft_score:
        return "missing_draft_capital_context"
    return f"NFL Draft Pick Signal {draft_score}"


def _draft_round_from_context(prospect: dict[str, str]) -> int | None:
    score = _float(prospect.get("draft_capital_score"))
    if score is None:
        return None
    if score >= 78:
        return 1
    if score >= 55:
        return 2
    if score >= 38:
        return 3
    if score >= 25:
        return 4
    if score >= 10:
        return 5
    return 7


def _draft_pick_from_context(prospect: dict[str, str]) -> int | None:
    score = _float(prospect.get("draft_capital_score"))
    if score is None:
        return None
    return max(1, min(257, int(round((100 - score) / 100 * 257))))


def _position_warning(position: str) -> str:
    if position == "TE":
        return "no_premium_te_caution"
    if position == "QB":
        return "one_qb_qb_caution"
    return ""


def _doc_text(
    review_rows: list[dict[str, object]],
    pick_zone_rows: list[dict[str, object]],
    bucket_rows: list[dict[str, object]],
) -> str:
    top_rows = review_rows[:12]
    low_confidence_buckets = [
        row
        for row in bucket_rows
        if row["sample_size_status"] == "low_confidence_small_or_missing_sample"
    ]
    lines = [
        "# Startup Slot Simulator Review",
        "",
        "## Scope",
        "",
        "This review-only simulator combines existing Model v4 player, prospect, "
        "and pick values into an internal startup-style slot board. It is not ADP, "
        "not a market mock, and not a final recommendation layer.",
        "",
        "## Outputs",
        "",
        "- `startup_slot_review_rows.csv`",
        "- `startup_slot_component_rows.csv`",
        "- `startup_slot_pick_zone_rows.csv`",
        "- `startup_slot_bucket_rows.csv`",
        "- `startup_slot_receipts.csv`",
        "- `startup_slot_warnings.csv`",
        "",
        "## Top Internal Slots",
        "",
        "| Slot | Asset | Type | Score | Nearby After |",
        "|---:|---|---|---:|---|",
    ]
    for row in top_rows:
        lines.append(
            f"| {row['startup_slot_rank']} | {row['player_or_asset']} | {row['entity_type']} | "
            f"{row['model_score']} | {row['nearby_assets_after']} |"
        )
    lines.extend(
        [
            "",
            "## Pick Zones",
            "",
            "| Pick | Baseline | Review Label | Nearby Model Neighbors | Trade Reality |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in pick_zone_rows:
        nearby_assets = str(row["nearby_startup_assets"]).replace(" | ", ", ")
        lines.append(
            f"| {row['pick_label']} | {row['pick_value_review_score']} | "
            f"{row['review_label']} | {nearby_assets} | "
            f"{row['trade_market_reality_context']} |"
        )
    lines.extend(
        [
            "",
            "## Outcome Bucket Guardrails",
            "",
            "Low-confidence or missing historical profile buckets: "
            f"`{len(low_confidence_buckets)}`.",
            "",
            "- Outcome buckets are display-only calibration context.",
            "- Missing historical outcomes are unknown, not misses.",
            "- Buckets do not feed back into rankings.",
            "- Nearby model neighbors are not one-for-one trade-market equivalents.",
            "- 2025 outcomes remain immature and are not treated as complete career outcomes.",
            "- Market, ADP, projection, ranking, mock, and big-board inputs remain "
            "blocked from private value.",
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


def _normalize(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", text)
    return re.sub(r"[^a-z0-9]", "", text)


def _join_present(*values: object, sep: str = "|") -> str:
    parts: list[str] = []
    for value in values:
        for part in str(value or "").split("|"):
            clean = part.strip()
            if clean and clean not in parts:
                parts.append(clean)
    return sep.join(parts)


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
