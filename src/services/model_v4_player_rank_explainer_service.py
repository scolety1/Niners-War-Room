from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "explainers/latest"
DOC_PATH = Path("docs/model_v4/PLAYER_RANK_EXPLAINER.md")
VERSION = "model_v4_player_rank_explainer_0.1.0"

ROOKIE_BOARD_ROWS = MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
PROSPECT_COMPONENT_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_component_rows.csv"
CURRENT_VALUE_ROWS = MODEL_ROOT / "current_value/latest/current_player_value_review_rows.csv"
CURRENT_COMPONENT_ROWS = MODEL_ROOT / "current_value/latest/current_player_value_component_rows.csv"
DYNASTY_ASSET_ROWS = MODEL_ROOT / "dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv"
STARTUP_SLOT_ROWS = MODEL_ROOT / "startup_slot_simulator/latest/startup_slot_review_rows.csv"

REVIEW_ONLY_USE = "review_only_rank_explainer_not_final_recommendation"
BLOCKED_USE = "do_not_use_as_final_pick_trade_cut_keep_or_rank_instruction"

ROW_HEADER = (
    "player_name",
    "position",
    "entity_type",
    "score",
    "rank",
    "short_explanation",
    "strongest_signals",
    "weakest_signals",
    "why_above_nearby_players",
    "why_below_nearby_players",
    "trust_status",
    "manual_review_note",
    "warning_summary_plain_english",
    "edge_or_source_label",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

COMPONENT_HEADER = (
    "component_key",
    "player_name",
    "position",
    "entity_type",
    "component_name",
    "normalized_score",
    "component_weight",
    "weighted_contribution",
    "signal_direction",
    "plain_english_signal",
    "receipt_pointer",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

WARNING_HEADER = (
    "warning_key",
    "player_name",
    "position",
    "entity_type",
    "warning_code",
    "warning_plain_english",
    "next_action",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class PlayerRankExplainerResult:
    rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_player_rank_explainer() -> PlayerRankExplainerResult:
    rookie_rows = _read_rows(ROOKIE_BOARD_ROWS)
    prospect_components = _read_rows(PROSPECT_COMPONENT_ROWS)
    current_rows = _read_rows(CURRENT_VALUE_ROWS)
    current_components = _read_rows(CURRENT_COMPONENT_ROWS)
    dynasty_rows = _read_rows(DYNASTY_ASSET_ROWS)
    startup_rows = _read_rows(STARTUP_SLOT_ROWS)

    prospect_component_lookup = _components_by_name(prospect_components, "entity_name")
    current_component_lookup = _components_by_name(current_components, "player_name")
    startup_lookup = {_norm(row.get("player_or_asset")): row for row in startup_rows}

    rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []

    sorted_rookies = sorted(
        rookie_rows,
        key=lambda row: _float(row.get("board_rank")) or 9999.0,
    )
    rookie_names = {_norm(row.get("prospect_name")) for row in sorted_rookies}
    for index, row in enumerate(sorted_rookies):
        components = prospect_component_lookup.get(_norm(row.get("prospect_name")), [])
        previous_row = sorted_rookies[index - 1] if index > 0 else None
        next_row = sorted_rookies[index + 1] if index + 1 < len(sorted_rookies) else None
        built = _rookie_explainer_row(row, components, previous_row, next_row, startup_lookup)
        rows.append(built)
        component_rows.extend(_component_receipts(built, components, "rookie_prospect"))
        warning_rows.extend(_warning_rows(built))

    current_asset_ranks = _current_asset_ranks(dynasty_rows)
    sorted_current = sorted(
        current_rows,
        key=lambda row: current_asset_ranks.get(_norm(row.get("player_name")), 9999),
    )
    for index, row in enumerate(sorted_current):
        components = current_component_lookup.get(_norm(row.get("player_name")), [])
        previous_row = sorted_current[index - 1] if index > 0 else None
        next_row = sorted_current[index + 1] if index + 1 < len(sorted_current) else None
        built = _current_explainer_row(
            row,
            components,
            previous_row,
            next_row,
            current_asset_ranks,
        )
        if _norm(row.get("player_name")) in rookie_names:
            component_rows.append(_alternate_context_receipt(built, "current_player"))
            component_rows.extend(
                _component_receipts(
                    built,
                    components,
                    "alternate_context_current_player",
                )
            )
            warning_rows.extend(_alternate_context_warning_rows(built, "current_player"))
            continue
        rows.append(built)
        component_rows.extend(_component_receipts(built, components, "current_player"))
        warning_rows.extend(_warning_rows(built))

    return PlayerRankExplainerResult(
        rows=tuple(rows),
        component_rows=tuple(component_rows),
        warning_rows=tuple(warning_rows),
        doc_text=_doc_text(rows),
    )


def write_player_rank_explainer_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
) -> dict[str, Path]:
    result = build_player_rank_explainer()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "rows": output / "player_rank_explainer_rows.csv",
        "component_rows": output / "player_rank_explainer_component_rows.csv",
        "warnings": output / "player_rank_explainer_warnings.csv",
        "doc": doc,
    }
    _write_csv(paths["rows"], ROW_HEADER, result.rows)
    _write_csv(paths["component_rows"], COMPONENT_HEADER, result.component_rows)
    _write_csv(paths["warnings"], WARNING_HEADER, result.warning_rows)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _rookie_explainer_row(
    row: dict[str, str],
    components: list[dict[str, str]],
    previous_row: dict[str, str] | None,
    next_row: dict[str, str] | None,
    startup_lookup: dict[str, dict[str, str]],
) -> dict[str, object]:
    name = str(row.get("prospect_name", "")).strip()
    position = str(row.get("position", "")).strip()
    score = _float(row.get("league_format_adjusted_score"))
    warnings = str(row.get("warning_flags", ""))
    edge_label = _edge_or_source_label(
        position,
        warnings,
        components,
        row.get("draft_board_band", ""),
    )
    strong = _strongest_signals(components, position, warnings)
    weak = _weakest_signals(components, position, warnings)
    startup = startup_lookup.get(_norm(name), {})
    slot_context = str(startup.get("pick_equivalent_context", "") or "").strip()
    explanation = _short_explanation(
        name=name,
        position=position,
        entity_type="rookie_prospect",
        strong=strong,
        weak=weak,
        edge_label=edge_label,
        slot_context=slot_context,
    )
    return {
        "player_name": name,
        "position": position,
        "entity_type": "rookie_prospect",
        "score": _blank(score),
        "rank": row.get("board_rank", ""),
        "short_explanation": explanation,
        "strongest_signals": "; ".join(strong),
        "weakest_signals": "; ".join(weak),
        "why_above_nearby_players": _nearby_reason(name, previous_row, above=True),
        "why_below_nearby_players": _nearby_reason(name, next_row, above=False),
        "trust_status": row.get("evidence_status", ""),
        "manual_review_note": _manual_review_note(position, warnings, edge_label),
        "warning_summary_plain_english": _plain_warnings(warnings),
        "edge_or_source_label": edge_label,
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _current_explainer_row(
    row: dict[str, str],
    components: list[dict[str, str]],
    previous_row: dict[str, str] | None,
    next_row: dict[str, str] | None,
    ranks: dict[str, int],
) -> dict[str, object]:
    name = str(row.get("player_name", "")).strip()
    position = str(row.get("position", "")).strip()
    warnings = str(row.get("warning_flags", ""))
    edge_label = _edge_or_source_label(position, warnings, components, "")
    strong = _strongest_signals(components, position, warnings)
    weak = _weakest_signals(components, position, warnings)
    return {
        "player_name": name,
        "position": position,
        "entity_type": "current_player",
        "score": _blank(_float(row.get("checkpoint_review_score"))),
        "rank": ranks.get(_norm(name), ""),
        "short_explanation": _short_explanation(
            name=name,
            position=position,
            entity_type="current_player",
            strong=strong,
            weak=weak,
            edge_label=edge_label,
            slot_context="",
        ),
        "strongest_signals": "; ".join(strong),
        "weakest_signals": "; ".join(weak),
        "why_above_nearby_players": _current_nearby_reason(name, previous_row, above=True),
        "why_below_nearby_players": _current_nearby_reason(name, next_row, above=False),
        "trust_status": row.get("confidence_status", ""),
        "manual_review_note": _manual_review_note(position, warnings, edge_label),
        "warning_summary_plain_english": _plain_warnings(warnings),
        "edge_or_source_label": edge_label,
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _component_receipts(
    parent_row: dict[str, object],
    components: list[dict[str, str]],
    entity_type: str,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for component in components:
        name = str(parent_row["player_name"])
        component_name = str(component.get("component_name", ""))
        normalized_score = _float(component.get("normalized_score"))
        weighted = _float(component.get("weighted_contribution"))
        output.append(
            {
                "component_key": f"{entity_type}:{_norm(name)}:{component_name}",
                "player_name": name,
                "position": parent_row.get("position", ""),
                "entity_type": entity_type,
                "component_name": component_name,
                "normalized_score": _blank(normalized_score),
                "component_weight": component.get("component_weight", ""),
                "weighted_contribution": _blank(weighted),
                "signal_direction": _signal_direction(normalized_score, weighted),
                "plain_english_signal": _component_plain_english(
                    component_name,
                    normalized_score,
                    entity_type,
                    str(parent_row.get("position", "")),
                ),
                "receipt_pointer": _receipt_pointer(component),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _alternate_context_receipt(
    parent_row: dict[str, object],
    alternate_entity_type: str,
) -> dict[str, object]:
    name = str(parent_row["player_name"])
    return {
        "component_key": f"alternate_context:{_norm(name)}:{alternate_entity_type}",
        "player_name": name,
        "position": parent_row.get("position", ""),
        "entity_type": "alternate_context",
        "component_name": f"{alternate_entity_type}_context_preserved",
        "normalized_score": parent_row.get("score", ""),
        "component_weight": "context_only",
        "weighted_contribution": "",
        "signal_direction": "context_only",
        "plain_english_signal": (
            "Alternate current-player context was preserved in receipts while the "
            "default table shows one primary player row."
        ),
        "receipt_pointer": "current_value_context_collapsed_from_default_view",
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _warning_rows(parent_row: dict[str, object]) -> list[dict[str, object]]:
    warnings = str(parent_row.get("warning_summary_plain_english", ""))
    raw_codes = str(parent_row.get("warning_summary_plain_english", "")).split("; ")
    output: list[dict[str, object]] = []
    if not warnings:
        return output
    for index, text in enumerate(raw_codes, start=1):
        if not text:
            continue
        output.append(
            {
                "warning_key": f"{_norm(parent_row.get('player_name'))}:{index}",
                "player_name": parent_row.get("player_name", ""),
                "position": parent_row.get("position", ""),
                "entity_type": parent_row.get("entity_type", ""),
                "warning_code": _norm(text) or "review_warning",
                "warning_plain_english": text,
                "next_action": "Use this as a human review note, not an automatic action.",
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _alternate_context_warning_rows(
    parent_row: dict[str, object],
    alternate_entity_type: str,
) -> list[dict[str, object]]:
    warnings = str(parent_row.get("warning_summary_plain_english", ""))
    raw_codes = warnings.split("; ")
    output: list[dict[str, object]] = []
    if not warnings:
        return output
    for index, text in enumerate(raw_codes, start=1):
        if not text:
            continue
        output.append(
            {
                "warning_key": (
                    f"alternate_context:{_norm(parent_row.get('player_name'))}:"
                    f"{alternate_entity_type}:{index}"
                ),
                "player_name": parent_row.get("player_name", ""),
                "position": parent_row.get("position", ""),
                "entity_type": "alternate_context",
                "warning_code": f"{alternate_entity_type}_{_norm(text) or 'review_warning'}",
                "warning_plain_english": (
                    "Alternate current-player context: "
                    f"{text}"
                ),
                "next_action": (
                    "Use this preserved context as a drilldown note; the default "
                    "explainer table keeps one primary player row."
                ),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _strongest_signals(
    components: list[dict[str, str]], position: str, warnings: str
) -> list[str]:
    ranked = sorted(
        components,
        key=lambda row: _float(row.get("weighted_contribution")) or 0.0,
        reverse=True,
    )
    signals = [
        _component_plain_english(
            str(component.get("component_name", "")),
            _float(component.get("normalized_score")),
            "player",
            position,
        )
        for component in ranked[:3]
    ]
    if position == "QB" and "one_qb" in warnings:
        signals.append("1QB format keeps quarterback value disciplined.")
    return [signal for signal in signals if signal][:3] or ["No single signal dominates."]


def _weakest_signals(components: list[dict[str, str]], position: str, warnings: str) -> list[str]:
    weak: list[str] = []
    low_components = sorted(
        (
            component
            for component in components
            if (_float(component.get("normalized_score")) or 100.0) < 45.0
        ),
        key=lambda row: _float(row.get("normalized_score")) or 0.0,
    )
    for component in low_components[:2]:
        weak.append(
            _component_plain_english(
                str(component.get("component_name", "")),
                _float(component.get("normalized_score")),
                "player",
                position,
            )
        )
    if "missing" in warnings:
        weak.append("Source coverage is incomplete, so confidence should stay capped.")
    if "source_limited" in warnings:
        weak.append("Some evidence is source-limited and needs manual review.")
    if position == "TE":
        weak.append("No-premium format caps tight end upside.")
    if position == "QB":
        weak.append("1QB format caps quarterback value unless the edge is massive.")
    return weak[:3] or ["No major weak signal beyond normal review risk."]


def _short_explanation(
    *,
    name: str,
    position: str,
    entity_type: str,
    strong: list[str],
    weak: list[str],
    edge_label: str,
    slot_context: str,
) -> str:
    prefix = f"{name} is ranked here because {_sentence_fragment(strong[0])}"
    if edge_label == "legitimate_model_edge":
        prefix += " This is a model-edge row supported by admitted evidence."
    elif edge_label == "source_warning":
        prefix += " The ranking may be fragile because source coverage is incomplete."
    elif edge_label == "format_discipline_case":
        prefix += f" The {position} value is being disciplined for this league format."
    else:
        prefix += " The profile is mostly explained by normal component balance."
    if weak:
        prefix += f" Main caution: {_sentence_fragment(weak[0])}"
    if entity_type == "rookie_prospect" and slot_context:
        prefix += f" Internal slot context: {slot_context}."
    return prefix


def _sentence_fragment(value: str) -> str:
    text = value.strip()
    if not text:
        return text
    if text.startswith(("NFL", "1QB", "VORP")):
        return text
    return text[0].lower() + text[1:]


def _edge_or_source_label(
    position: str,
    warnings: str,
    components: list[dict[str, str]],
    board_band: str,
) -> str:
    normalized_scores = {
        str(component.get("component_name", "")): _float(component.get("normalized_score"))
        for component in components
    }
    draft_score = normalized_scores.get("draft_capital")
    production_score = normalized_scores.get("production")
    share_score = normalized_scores.get("market_share")
    if (
        draft_score is not None
        and draft_score < 45
        and ((production_score or 0) >= 75 or (share_score or 0) >= 75)
    ):
        return "legitimate_model_edge"
    if "source_shape_warning" in warnings or "missing" in warnings:
        return "source_warning"
    if position in {"QB", "TE"}:
        return "format_discipline_case"
    if "second_round" in board_band and "round_1" not in board_band:
        return "normal_component_balance"
    return "normal_component_balance"


def _manual_review_note(position: str, warnings: str, edge_label: str) -> str:
    if edge_label == "legitimate_model_edge":
        return "Review whether the unusual ranking is a real football edge or a sample-size trap."
    if edge_label == "source_warning":
        return "Verify the missing or source-limited evidence before trusting the score."
    if position == "TE":
        return "Check whether the player is truly worth no-premium tight end opportunity cost."
    if position == "QB":
        return "Check whether the quarterback can create a real 1QB format edge."
    if "review_only" in warnings:
        return "Human review required before any roster or draft action."
    return "Use as review context only."


def _plain_warnings(warnings: str) -> str:
    mapping = {
        "review_only_no_final_rookie_pick_recommendation": "Review-only: not a final rookie pick.",
        "market_context_excluded_from_private_value": "Non-scoring context is excluded from value.",
        "missing_prospect_or_college_evidence": "Prospect or college evidence is incomplete.",
        "missing_market_share_component": "College team-share component is missing.",
        "missing_athletic_prior_component": "Athletic prior is missing.",
        "third_party_combine_source_limited": "Workout evidence is source-limited.",
        "source_limited_evidence_cap": "Source-limited evidence caps trust.",
        "model_edge_weirdness": "Model edge: unusual ranking supported by admitted evidence.",
        "source_shape_warning": "Source warning: unusual ranking may be caused by missing data.",
        "no_premium_te_cap_warning": "No-premium TE format caps upside.",
        "one_qb_qb_scarcity_cap": "1QB format caps quarterback value.",
        "licensed_route_metrics_not_available": "Advanced route metrics are unavailable.",
        "missing_or_review_route_target_snap_evidence": (
            "Route, target, or snap evidence is partial."
        ),
        "missing_lifecycle_or_role_shape_evidence": (
            "Lifecycle or role-shape evidence is incomplete."
        ),
        "not_used_in_stats_first_value": "This context did not drive private value.",
    }
    output: list[str] = []
    for warning in warnings.split("|"):
        if not warning:
            continue
        output.append(mapping.get(warning, warning.replace("_", " ").capitalize() + "."))
    return "; ".join(output)


def _component_plain_english(
    component_name: str,
    normalized_score: float | None,
    entity_type: str,
    position: str,
) -> str:
    score_text = "" if normalized_score is None else f" ({round(normalized_score, 1)})"
    if component_name == "draft_capital":
        if normalized_score is not None and normalized_score < 45:
            return f"NFL draft pick signal is weak{score_text}."
        return f"High draft capital protects the floor{score_text}."
    if component_name == "production":
        if normalized_score is not None and normalized_score < 45:
            return f"College production is a weak part of the profile{score_text}."
        return f"College production is carrying part of the score{score_text}."
    if component_name == "market_share":
        if normalized_score is not None and normalized_score < 45:
            return f"College team share is weak or incomplete{score_text}."
        return f"College team share is a major signal{score_text}."
    if component_name == "athletic_prior":
        if normalized_score is not None and normalized_score < 45:
            return f"Workout profile is weak or incomplete{score_text}."
        return f"Workout profile supports the ranking{score_text}."
    if component_name == "age_lifecycle":
        return f"Age and lifecycle context support the ranking{score_text}."
    if component_name == "confidence_cap":
        return f"Confidence cap limits how much to trust the score{score_text}."
    if component_name == "lifecycle_modifier":
        return f"Lifecycle context adjusts the value window{score_text}."
    if component_name == "position_discipline":
        if position == "QB":
            return f"1QB format discipline limits quarterback value{score_text}."
        if position == "TE":
            return f"No-premium format discipline limits tight end value{score_text}."
        return f"Position format discipline adjusts the value{score_text}."
    if component_name == "vorp_anchor":
        return f"VORP over replacement anchors the current-player value{score_text}."
    if component_name == "role_volume":
        return f"Role and volume support the current-player value{score_text}."
    if component_name == "efficiency_context":
        return f"Efficiency is treated as context, not the whole case{score_text}."
    if position == "TE":
        readable = component_name.replace("_", " ").title()
        return f"{readable} is capped by no-premium TE format{score_text}."
    if position == "QB":
        readable = component_name.replace("_", " ").title()
        return f"{readable} is capped by 1QB format{score_text}."
    return f"{_readable_component_name(component_name)} contributes to the score{score_text}."


def _readable_component_name(component_name: str) -> str:
    mapping = {
        "confidence_cap": "Confidence cap",
        "available_component_weight": "Evidence availability",
        "lifecycle_modifier": "Lifecycle modifier",
        "position_discipline": "Position discipline",
    }
    return mapping.get(component_name, component_name.replace("_", " ").title())


def _nearby_reason(
    name: str,
    nearby_row: dict[str, str] | None,
    *,
    above: bool,
) -> str:
    if nearby_row is None:
        return "No nearby rookie row on this side of the board."
    nearby_name = nearby_row.get("prospect_name", "")
    nearby_score = nearby_row.get("league_format_adjusted_score", "")
    direction = "above" if above else "below"
    return (
        f"{name} is {direction} {nearby_name} by the review score gap and component balance "
        f"around {nearby_score}."
    )


def _current_nearby_reason(
    name: str,
    nearby_row: dict[str, str] | None,
    *,
    above: bool,
) -> str:
    if nearby_row is None:
        return "No nearby current-player row on this side of the board."
    nearby_name = nearby_row.get("player_name", "")
    nearby_score = nearby_row.get("checkpoint_review_score", "")
    direction = "above" if above else "below"
    return f"{name} is {direction} {nearby_name} by current value score around {nearby_score}."


def _signal_direction(normalized_score: float | None, weighted: float | None) -> str:
    if normalized_score is None:
        return "missing_or_context"
    if normalized_score >= 70 or (weighted or 0) >= 10:
        return "positive"
    if normalized_score < 45:
        return "risk"
    return "neutral"


def _receipt_pointer(component: dict[str, str]) -> str:
    return (
        component.get("allowed_input_file")
        or component.get("source_file")
        or component.get("allowed_lane")
        or "component_row"
    )


def _current_asset_ranks(rows: list[dict[str, str]]) -> dict[str, int]:
    current_rows = [row for row in rows if row.get("asset_type") == "current_player"]
    current_rows.sort(
        key=lambda row: _float(row.get("dynasty_asset_value_review_score")) or 0.0,
        reverse=True,
    )
    return {_norm(row.get("asset_name")): index for index, row in enumerate(current_rows, start=1)}


def _components_by_name(
    rows: list[dict[str, str]], name_key: str
) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        output.setdefault(_norm(row.get(name_key)), []).append(row)
    return output


def _doc_text(rows: list[dict[str, object]]) -> str:
    rookie_rows = [row for row in rows if row.get("entity_type") == "rookie_prospect"][:25]
    lines = [
        "# Player Rank Explainer",
        "",
        "## Scope",
        "",
        "This review-only layer converts model components and warnings into plain-English "
        "rank explanations. It does not create final draft, trade, cut, or ranking actions.",
        "",
        "## Top Rookie Explanations",
        "",
        "| Rank | Player | Pos | Explanation |",
        "|---:|---|---|---|",
    ]
    for row in rookie_rows:
        lines.append(
            f"| {row['rank']} | {row['player_name']} | {row['position']} | "
            f"{row['short_explanation']} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Explanations trace to component rows or warning rows.",
            "- Non-scoring context cannot drive private value.",
            "- Every row remains review-only.",
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


def _float(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None


def _blank(value: float | None) -> str | float:
    return "" if value is None else round(value, 4)


def _norm(value: object) -> str:
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())
