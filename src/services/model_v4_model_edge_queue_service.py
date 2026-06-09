from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "model_edge_queue/latest"
DOC_PATH = Path("docs/model_v4/MODEL_EDGE_QUEUE.md")
VERSION = "model_v4_model_edge_queue_0.1.0"

ROOKIE_BOARD_ROWS = MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
PROSPECT_COMPONENT_ROWS = MODEL_ROOT / "prospect_value/latest/prospect_value_component_rows.csv"
CURRENT_VALUE_ROWS = MODEL_ROOT / "current_value/latest/current_player_value_review_rows.csv"
STARTUP_SLOT_ROWS = MODEL_ROOT / "startup_slot_simulator/latest/startup_slot_review_rows.csv"
SOURCE_RISK_ROWS = MODEL_ROOT / "source_risk_heatmap/latest/source_risk_player_rows.csv"
EXPLAINER_ROWS = MODEL_ROOT / "explainers/latest/player_rank_explainer_rows.csv"

REVIEW_ONLY_USE = "review_only_model_edge_queue_not_final_recommendation"
BLOCKED_USE = "do_not_use_as_final_pick_trade_cut_keep_or_rank_instruction"

ROW_HEADER = (
    "player_name",
    "position",
    "entity_type",
    "score",
    "model_rank",
    "weirdness_type",
    "edge_classification",
    "why_weird",
    "evidence_supporting_edge",
    "evidence_against_edge",
    "source_risk",
    "human_review_question",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

COMPONENT_HEADER = (
    "component_key",
    "player_name",
    "position",
    "entity_type",
    "weirdness_type",
    "component_name",
    "component_value",
    "normalized_score",
    "component_weight",
    "weighted_contribution",
    "component_interpretation",
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
    "weirdness_type",
    "edge_classification",
    "warning_code",
    "warning_detail",
    "next_action",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class ModelEdgeQueueResult:
    rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_model_edge_queue() -> ModelEdgeQueueResult:
    rookie_rows = _read_rows(ROOKIE_BOARD_ROWS)
    prospect_components = _components_by_name(_read_rows(PROSPECT_COMPONENT_ROWS), "entity_name")
    current_rows = _read_rows(CURRENT_VALUE_ROWS)
    startup_lookup = {
        _norm(row.get("player_or_asset")): row for row in _read_rows(STARTUP_SLOT_ROWS)
    }
    source_lookup = {
        (_norm(row.get("player_name")), row.get("entity_type", "")): row
        for row in _read_rows(SOURCE_RISK_ROWS)
    }
    explainer_lookup = {
        (_norm(row.get("player_name")), row.get("entity_type", "")): row
        for row in _read_rows(EXPLAINER_ROWS)
    }

    rows: list[dict[str, object]] = []
    component_rows: list[dict[str, object]] = []
    warning_rows: list[dict[str, object]] = []

    for row in rookie_rows:
        name = str(row.get("prospect_name", "")).strip()
        if not name:
            continue
        components = prospect_components.get(_norm(name), [])
        source = source_lookup.get((_norm(name), "rookie_prospect"), {})
        explainer = explainer_lookup.get((_norm(name), "rookie_prospect"), {})
        startup = startup_lookup.get(_norm(name), {})
        triggers = _rookie_triggers(row, components, source, startup)
        for trigger in triggers:
            built = _edge_row(
                name=name,
                position=str(row.get("position", "")),
                entity_type="rookie_prospect",
                score=_float(row.get("league_format_adjusted_score")),
                model_rank=row.get("board_rank", ""),
                weirdness_type=trigger,
                components=components,
                source=source,
                explainer=explainer,
                warning_flags=row.get("warning_flags", ""),
            )
            rows.append(built)
            component_rows.extend(_component_rows(built, components))
            warning_rows.extend(_warning_rows(built, row.get("warning_flags", "")))

    for row in current_rows:
        name = str(row.get("player_name", "")).strip()
        if not name:
            continue
        source = source_lookup.get((_norm(name), "current_player"), {})
        explainer = explainer_lookup.get((_norm(name), "current_player"), {})
        triggers = _current_triggers(row, source)
        for trigger in triggers:
            built = _edge_row(
                name=name,
                position=str(row.get("position", "")),
                entity_type="current_player",
                score=_float(row.get("checkpoint_review_score")),
                model_rank=explainer.get("rank", ""),
                weirdness_type=trigger,
                components=[],
                source=source,
                explainer=explainer,
                warning_flags=row.get("warning_flags", ""),
            )
            rows.append(built)
            warning_rows.extend(_warning_rows(built, row.get("warning_flags", "")))

    rows.sort(
        key=lambda row: (
            _classification_sort(str(row["edge_classification"])),
            -(_float(row["score"]) or 0.0),
            str(row["player_name"]),
        )
    )
    return ModelEdgeQueueResult(
        rows=tuple(rows),
        component_rows=tuple(component_rows),
        warning_rows=tuple(warning_rows),
        doc_text=_doc_text(rows),
    )


def write_model_edge_queue_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
) -> dict[str, Path]:
    result = build_model_edge_queue()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "rows": output / "model_edge_rows.csv",
        "component_rows": output / "model_edge_component_rows.csv",
        "warnings": output / "model_edge_warnings.csv",
        "doc": doc,
    }
    _write_csv(paths["rows"], ROW_HEADER, result.rows)
    _write_csv(paths["component_rows"], COMPONENT_HEADER, result.component_rows)
    _write_csv(paths["warnings"], WARNING_HEADER, result.warning_rows)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _rookie_triggers(
    row: dict[str, str],
    components: list[dict[str, str]],
    source: dict[str, str],
    startup: dict[str, str],
) -> list[str]:
    triggers: list[str] = []
    position = str(row.get("position", ""))
    rank = int(_float(row.get("board_rank")) or 9999)
    score = _float(row.get("league_format_adjusted_score")) or 0.0
    draft_score = _component_score(components, "draft_capital")
    production_score = _component_score(components, "production")
    share_score = _component_score(components, "market_share")
    risk = str(source.get("source_risk_level", ""))
    draft_context = str(startup.get("draft_capital_context", ""))
    if (
        draft_score is not None
        and draft_score < 50
        and ((production_score or 0) >= 75 or (share_score or 0) >= 75)
    ):
        triggers.append("huge_production_bad_draft_signal")
    elif rank <= 15 and draft_score is not None and draft_score < 50:
        triggers.append("day_three_or_low_capital_player_ranked_high")
    if rank >= 20 and draft_score is not None and draft_score >= 80:
        triggers.append("first_round_player_ranked_low")
    if position == "TE" and rank <= 35:
        triggers.append("te_ranked_high_no_premium")
    if position == "QB" and rank <= 35:
        triggers.append("qb_ranked_high_1qb")
    if (
        draft_score is not None
        and draft_score >= 75
        and ((production_score or 100) < 45 or (share_score or 100) < 45)
    ):
        triggers.append("high_draft_capital_weak_production_or_share")
    if "depth" in draft_context and score >= 55:
        triggers.append("depth_slot_with_strong_model_score")
    if (
        score >= 60
        and risk in {"red_manual_review", "orange_source_limited"}
        and not triggers
    ):
        triggers.append("strong_score_with_source_risk")
    return _dedupe(triggers)


def _current_triggers(row: dict[str, str], source: dict[str, str]) -> list[str]:
    triggers: list[str] = []
    position = str(row.get("position", ""))
    score = _float(row.get("checkpoint_review_score")) or 0.0
    risk = str(source.get("source_risk_level", ""))
    if position == "TE" and score >= 45:
        triggers.append("te_ranked_high_no_premium")
    if position == "QB" and score >= 45:
        triggers.append("qb_ranked_high_1qb")
    if score >= 60 and risk in {"red_manual_review", "orange_source_limited"}:
        triggers.append("strong_score_with_source_risk")
    if risk == "red_manual_review":
        triggers.append("major_source_warning")
    return _dedupe(triggers)


def _edge_row(
    *,
    name: str,
    position: str,
    entity_type: str,
    score: float | None,
    model_rank: object,
    weirdness_type: str,
    components: list[dict[str, str]],
    source: dict[str, str],
    explainer: dict[str, str],
    warning_flags: object,
) -> dict[str, object]:
    classification = _classification(weirdness_type, components, source, warning_flags, position)
    return {
        "player_name": name,
        "position": position,
        "entity_type": entity_type,
        "score": _blank(score),
        "model_rank": model_rank,
        "weirdness_type": weirdness_type,
        "edge_classification": classification,
        "why_weird": _why_weird(weirdness_type, position),
        "evidence_supporting_edge": _supporting_evidence(components, explainer),
        "evidence_against_edge": _evidence_against(components, source, position),
        "source_risk": _source_risk_text(source),
        "human_review_question": _human_question(weirdness_type, classification),
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _classification(
    weirdness_type: str,
    components: list[dict[str, str]],
    source: dict[str, str],
    warning_flags: object,
    position: str,
) -> str:
    risk = str(source.get("source_risk_level", ""))
    warnings = str(warning_flags)
    if risk == "red_manual_review":
        return "do_not_trust_without_review"
    if position in {"QB", "TE"}:
        return "format_discipline_case"
    draft_score = _component_score(components, "draft_capital") or 0.0
    production_score = _component_score(components, "production") or 0.0
    share_score = _component_score(components, "market_share") or 0.0
    if draft_score < 50 and max(production_score, share_score) >= 75:
        return "legitimate_model_edge"
    if risk == "orange_source_limited" or "missing" in warnings or "source_shape" in warnings:
        return "source_shape_warning"
    return "manual_scout_required"


def _component_rows(
    parent: dict[str, object],
    components: list[dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for component in components:
        component_name = str(component.get("component_name", ""))
        output.append(
            {
                "component_key": (
                    f"{_norm(parent['player_name'])}:{parent['weirdness_type']}:"
                    f"{component_name}"
                ),
                "player_name": parent["player_name"],
                "position": parent["position"],
                "entity_type": parent["entity_type"],
                "weirdness_type": parent["weirdness_type"],
                "component_name": component_name,
                "component_value": component.get("component_value", ""),
                "normalized_score": component.get("normalized_score", ""),
                "component_weight": component.get("component_weight", ""),
                "weighted_contribution": component.get("weighted_contribution", ""),
                "component_interpretation": _component_interpretation(component),
                "receipt_pointer": component.get("allowed_input_file", ""),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _warning_rows(parent: dict[str, object], warnings: object) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for warning in _dedupe(str(warnings).split("|")):
        if not warning:
            continue
        output.append(
            {
                "warning_key": (
                    f"{_norm(parent['player_name'])}:{parent['weirdness_type']}:{warning}"
                ),
                "player_name": parent["player_name"],
                "position": parent["position"],
                "entity_type": parent["entity_type"],
                "weirdness_type": parent["weirdness_type"],
                "edge_classification": parent["edge_classification"],
                "warning_code": warning,
                "warning_detail": warning.replace("_", " "),
                "next_action": "Use this as a review queue item; do not act automatically.",
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _why_weird(weirdness_type: str, position: str) -> str:
    mapping = {
        "day_three_or_low_capital_player_ranked_high": (
            "Low draft-pick signal player is high on the model board."
        ),
        "first_round_player_ranked_low": "Strong NFL draft signal player sits lower than expected.",
        "te_ranked_high_no_premium": f"{position} is high despite no premium scoring.",
        "qb_ranked_high_1qb": f"{position} is high despite shallow 1QB format.",
        "strong_score_with_source_risk": "Strong score is paired with source-risk warnings.",
        "high_draft_capital_weak_production_or_share": (
            "NFL investment is strong, but college production or team share is weak."
        ),
        "huge_production_bad_draft_signal": (
            "College production or team share is excellent, but draft-pick signal is weak."
        ),
        "depth_slot_with_strong_model_score": "Strong score appears in a depth-slot zone.",
        "major_source_warning": "Current-player score carries a major source-risk warning.",
    }
    return mapping.get(weirdness_type, weirdness_type.replace("_", " "))


def _supporting_evidence(
    components: list[dict[str, str]], explainer: dict[str, str]
) -> str:
    strong = str(explainer.get("strongest_signals", "")).strip()
    if strong:
        return strong
    top = sorted(
        components,
        key=lambda row: _float(row.get("weighted_contribution")) or 0.0,
        reverse=True,
    )[:3]
    if not top:
        return "No component support available beyond source-risk context."
    return "; ".join(
        f"{row.get('component_name')}={row.get('normalized_score')}" for row in top
    )


def _evidence_against(
    components: list[dict[str, str]], source: dict[str, str], position: str
) -> str:
    risks: list[str] = []
    low = [
        row
        for row in components
        if (_float(row.get("normalized_score")) is not None)
        and (_float(row.get("normalized_score")) or 0.0) < 45
    ]
    for row in low[:2]:
        risks.append(f"weak {row.get('component_name')} ({row.get('normalized_score')})")
    if source:
        risks.append(str(source.get("biggest_source_risk", "")))
    if position == "TE":
        risks.append("no-premium TE opportunity cost")
    if position == "QB":
        risks.append("1QB replacement discipline")
    return "; ".join(risk for risk in risks if risk) or "No obvious counter-signal."


def _source_risk_text(source: dict[str, str]) -> str:
    if not source:
        return "source_risk_not_loaded"
    return (
        f"{source.get('source_risk_level')}; "
        f"{source.get('biggest_source_risk')}; {source.get('warning_summary')}"
    )


def _human_question(weirdness_type: str, classification: str) -> str:
    if classification == "do_not_trust_without_review":
        return "Is the source issue resolved enough to trust this row at all?"
    if classification == "source_shape_warning":
        return "Is this ranking caused by a missing or source-limited evidence shape?"
    if classification == "legitimate_model_edge":
        return "Is the admitted evidence strong enough to accept the weird ranking?"
    if weirdness_type in {"te_ranked_high_no_premium", "qb_ranked_high_1qb"}:
        return "Does this player create enough format-specific edge to matter?"
    return "Should this be treated as edge, caution, or ignored?"


def _component_interpretation(component: dict[str, str]) -> str:
    name = str(component.get("component_name", ""))
    score = _float(component.get("normalized_score"))
    if score is None:
        return f"{name} is missing or context-only."
    if score >= 75:
        return f"{name} strongly supports the edge."
    if score < 45:
        return f"{name} argues against the edge."
    return f"{name} is neutral context."


def _component_score(components: list[dict[str, str]], component_name: str) -> float | None:
    for component in components:
        if component.get("component_name") == component_name:
            return _float(component.get("normalized_score"))
    return None


def _components_by_name(
    rows: list[dict[str, str]], name_key: str
) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        output.setdefault(_norm(row.get(name_key)), []).append(row)
    return output


def _doc_text(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Model Edge Queue",
        "",
        "## Scope",
        "",
        "This review-only queue surfaces unusual model rankings and separates likely "
        "model edge from source-shape risk and format discipline.",
        "",
        "| Player | Pos | Weirdness | Classification | Review Question |",
        "|---|---|---|---|---|",
    ]
    for row in rows[:40]:
        lines.append(
            f"| {row['player_name']} | {row['position']} | {row['weirdness_type']} | "
            f"{row['edge_classification']} | {row['human_review_question']} |"
        )
    return "\n".join(lines) + "\n"


def _classification_sort(value: str) -> int:
    return {
        "do_not_trust_without_review": 0,
        "source_shape_warning": 1,
        "manual_scout_required": 2,
        "legitimate_model_edge": 3,
        "format_discipline_case": 4,
    }.get(value, 9)


def _dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in output:
            output.append(clean)
    return output


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
