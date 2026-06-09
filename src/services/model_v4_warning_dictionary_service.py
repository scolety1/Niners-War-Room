from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "warning_dictionary/latest"
DOC_PATH = Path("docs/model_v4/MODEL_V4_6_WARNING_CODE_DICTIONARY.md")
VERSION = "model_v4_6_warning_dictionary_0.1.0"

REVIEW_ONLY_USE = "review_only_warning_dictionary_not_final_recommendation"
BLOCKED_USE = "do_not_use_warning_text_as_final_pick_trade_cut_keep_instruction"

WARNING_SOURCE_FILES = (
    MODEL_ROOT / "source_risk_heatmap/latest/source_risk_player_rows.csv",
    MODEL_ROOT / "source_risk_heatmap/latest/source_risk_player_summary_rows.csv",
    MODEL_ROOT / "source_risk_heatmap/latest/source_risk_feature_rows.csv",
    MODEL_ROOT / "model_edge_queue/latest/model_edge_warnings.csv",
    MODEL_ROOT / "explainers/latest/player_rank_explainer_warnings.csv",
    MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_warnings.csv",
    MODEL_ROOT / "roster_opportunity_cost/latest/roster_opportunity_cost_warnings.csv",
    MODEL_ROOT / "roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv",
    MODEL_ROOT / "rookie_pick_decision_lab/latest/pick_decision_warnings.csv",
    MODEL_ROOT / "rookie_pick_decision_lab/latest/pick_decision_rows.csv",
)

WARNING_CODE_COLUMNS = (
    "warning_code",
    "warning_codes",
    "warning_flags",
    "warning_summary",
    "confidence_or_risk_warnings",
    "pick_equivalent_warning",
    "source_risk_level",
    "worst_source_risk_level",
    "production_status",
    "draft_capital_status",
    "team_share_status",
    "athletic_status",
    "recruiting_status",
    "age_status",
    "landing_context_status",
    "injury_status",
    "route_usage_status",
    "first_down_status",
    "risk_level",
)

DICTIONARY_HEADER = (
    "raw_warning_code",
    "warning_group",
    "plain_english_meaning",
    "why_it_matters",
    "human_review_action",
    "severity_hint",
    "primary_module",
    "primary_export",
    "receipt_or_drilldown_to_open",
    "example_review_question",
    "source_files",
    "occurrence_count",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

DISPLAY_MAP_HEADER = (
    "warning_group",
    "display_label",
    "group_description",
    "severity_hint",
    "raw_warning_codes",
    "allowed_use",
    "blocked_use",
    "formula_version",
)

GROUP_RULES: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    (
        "Data incomplete",
        (
            "missing",
            "gray_missing",
            "combine_absent",
            "workout_metric_missing",
            "partial",
        ),
        "Some evidence is missing, partial, or repaired.",
        "Review the missing inputs before trusting the score.",
    ),
    (
        "Low draft investment",
        (
            "day_three",
            "missing_draft_capital",
            "draft_capital_anchor",
            "low_draft",
        ),
        "NFL investment is weak, missing, or needs a draft-capital guardrail.",
        "Treat the player as a model-edge case until manual scouting agrees.",
    ),
    (
        "No-premium TE caution",
        ("no_premium_te", "te_cap", "replaceable_no_premium_te"),
        "The league has no TE premium, so TE value needs extra discipline.",
        "Compare the TE against RB/WR alternatives and replacement value.",
    ),
    (
        "1QB QB caution",
        ("one_qb", "1qb", "pocket_qb", "replaceable_1qb"),
        "The league is 1QB, so QB value requires a real edge over replacement.",
        "Do not overpay for a replaceable QB profile.",
    ),
    (
        "Source-limited role data",
        (
            "source_limited",
            "licensed_route",
            "route_target_snap",
            "route",
            "snap",
            "target",
            "orange_source_limited",
        ),
        "Role, route, snap, target, or source-limited data reduces trust.",
        "Check receipts and role context before acting.",
    ),
    (
        "Manual review required",
        (
            "manual",
            "identity_review",
            "quarantined",
            "red_manual_review",
            "manual_only_no_exact_model_baseline",
        ),
        "The row requires human review before it can inform a decision.",
        "Open receipts and do not treat the row as an instruction.",
    ),
    (
        "Review-only guardrail",
        (
            "review_only",
            "not_final",
            "no_final",
            "no_cut_keep",
            "no_trade",
            "no_pick",
        ),
        "The row is context-only and cannot be used as a final recommendation.",
        "Use it only to prepare a human decision.",
    ),
    (
        "Model edge",
        ("model_edge", "weirdness", "source_shape_warning", "format_discipline"),
        "The model is intentionally surfacing an unusual or format-sensitive row.",
        "Decide whether this is real edge or a source-shape problem.",
    ),
)

SEVERITY_BY_GROUP = {
    "Manual review required": "high",
    "Data incomplete": "medium",
    "Source-limited role data": "medium",
    "Low draft investment": "medium",
    "No-premium TE caution": "medium",
    "1QB QB caution": "medium",
    "Model edge": "review",
    "Review-only guardrail": "info",
    "General review": "review",
}


@dataclass(frozen=True)
class WarningDictionaryResult:
    dictionary_rows: tuple[dict[str, object], ...]
    display_map_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_warning_dictionary() -> WarningDictionaryResult:
    code_sources: dict[str, set[str]] = defaultdict(set)
    code_counts: Counter[str] = Counter()
    for path in WARNING_SOURCE_FILES:
        for row in _read_rows(path):
            for column in WARNING_CODE_COLUMNS:
                for code in _warning_tokens(row.get(column, "")):
                    code_sources[code].add(path.as_posix())
                    code_counts[code] += 1

    dictionary_rows = [
        _dictionary_row(code, code_sources[code], code_counts[code])
        for code in sorted(code_counts)
    ]
    display_map_rows = _display_map_rows(dictionary_rows)
    return WarningDictionaryResult(
        dictionary_rows=tuple(dictionary_rows),
        display_map_rows=tuple(display_map_rows),
        doc_text=_doc_text(dictionary_rows, display_map_rows),
    )


def write_warning_dictionary_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: WarningDictionaryResult | None = None,
) -> dict[str, Path]:
    result = result or build_warning_dictionary()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "dictionary": output / "warning_code_dictionary.csv",
        "display_map": output / "warning_group_display_map.csv",
        "doc": doc,
    }
    _write_csv(paths["dictionary"], DICTIONARY_HEADER, result.dictionary_rows)
    _write_csv(paths["display_map"], DISPLAY_MAP_HEADER, result.display_map_rows)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _dictionary_row(
    code: str,
    source_files: set[str],
    count: int,
) -> dict[str, object]:
    group = _warning_group(code)
    primary_module = _primary_module(source_files)
    primary_export = _primary_export(source_files, primary_module)
    return {
        "raw_warning_code": code,
        "warning_group": group,
        "plain_english_meaning": _plain_english_meaning(code, group),
        "why_it_matters": _why_it_matters(group),
        "human_review_action": _human_review_action(group),
        "severity_hint": SEVERITY_BY_GROUP.get(group, "review"),
        "primary_module": primary_module,
        "primary_export": primary_export,
        "receipt_or_drilldown_to_open": _receipt_or_drilldown(primary_module),
        "example_review_question": _example_review_question(group, primary_module),
        "source_files": "|".join(sorted(source_files)),
        "occurrence_count": count,
        "allowed_use": REVIEW_ONLY_USE,
        "blocked_use": BLOCKED_USE,
        "formula_version": VERSION,
    }


def _display_map_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped[str(row["warning_group"])].append(str(row["raw_warning_code"]))
    output = []
    for group in sorted(grouped, key=lambda value: (SEVERITY_BY_GROUP.get(value, ""), value)):
        output.append(
            {
                "warning_group": group,
                "display_label": group,
                "group_description": _why_it_matters(group),
                "severity_hint": SEVERITY_BY_GROUP.get(group, "review"),
                "raw_warning_codes": "|".join(sorted(grouped[group])),
                "allowed_use": REVIEW_ONLY_USE,
                "blocked_use": BLOCKED_USE,
                "formula_version": VERSION,
            }
        )
    return output


def _primary_module(source_files: set[str]) -> str:
    modules = sorted({_module_from_path(path) for path in source_files})
    if not modules:
        return "unknown"
    if len(modules) == 1:
        return modules[0]
    return "multiple_modules"


def _primary_export(source_files: set[str], primary_module: str) -> str:
    if primary_module == "multiple_modules":
        return "multiple_exports"
    for path in sorted(source_files):
        if _module_from_path(path) == primary_module:
            return path
    return sorted(source_files)[0] if source_files else ""


def _module_from_path(path: str) -> str:
    text = path.replace("\\", "/")
    module_map = {
        "source_risk_heatmap": "source_risk_heatmap",
        "model_edge_queue": "model_edge_queue",
        "explainers": "player_rank_explainer",
        "rookie_draft_review": "rookie_draft_review",
        "roster_opportunity_cost": "roster_opportunity_cost",
        "rookie_pick_decision_lab": "rookie_pick_decision_lab",
    }
    for marker, module in module_map.items():
        if marker in text:
            return module
    return "unknown"


def _receipt_or_drilldown(module: str) -> str:
    return {
        "source_risk_heatmap": "Draft Room -> Evidence & Risk -> Player Detail",
        "model_edge_queue": "Draft Room -> Evidence & Risk -> Model Edges",
        "player_rank_explainer": "Draft Room -> Why This Rank",
        "rookie_draft_review": "Draft Room -> Prospect Board",
        "roster_opportunity_cost": "June 15 Review -> Cut Cost",
        "rookie_pick_decision_lab": "Draft Room -> Pick Decision Lab",
        "multiple_modules": "Open the source_files exports listed on this row",
    }.get(module, "Open the source_files exports listed on this row")


def _example_review_question(group: str, module: str) -> str:
    if group == "Data incomplete":
        return "Which evidence module is missing, and does that change trust?"
    if group == "Low draft investment":
        return "Is the production edge strong enough to overcome weak NFL investment?"
    if group == "No-premium TE caution":
        return "Is this TE still worth considering without TE premium?"
    if group == "1QB QB caution":
        return "Does this QB create a real edge in a 10-team 1QB league?"
    if group == "Source-limited role data":
        return "Is the role signal backed by admitted evidence or only limited context?"
    if group == "Manual review required":
        return "What receipt or identity/source issue must be checked manually?"
    if group == "Review-only guardrail":
        return "What human decision does this row prepare without recommending?"
    if group == "Model edge":
        return "Is the weird ranking supported by evidence or caused by source shape?"
    if module == "roster_opportunity_cost":
        return "What opportunity cost would leave the roster if this player is dropped?"
    return "What should the human reviewer verify before relying on this row?"


def _warning_group(code: str) -> str:
    for group, patterns, _meaning, _action in GROUP_RULES:
        if any(pattern in code for pattern in patterns):
            return group
    return "General review"


def _plain_english_meaning(code: str, group: str) -> str:
    for rule_group, patterns, meaning, _action in GROUP_RULES:
        if rule_group == group and any(pattern in code for pattern in patterns):
            return meaning
    return code.replace("_", " ").capitalize()


def _why_it_matters(group: str) -> str:
    for rule_group, _patterns, meaning, _action in GROUP_RULES:
        if rule_group == group:
            return meaning
    return "This warning should be reviewed before relying on the row."


def _human_review_action(group: str) -> str:
    for rule_group, _patterns, _meaning, action in GROUP_RULES:
        if rule_group == group:
            return action
    return "Review the row and receipts before making any final decision."


def _doc_text(
    dictionary_rows: list[dict[str, object]],
    display_map_rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Model v4.6 Warning Code Dictionary",
        "",
        "## Scope",
        "",
        "This review-only dictionary maps raw warning codes into plain-English groups. "
        "It does not change formulas, scores, rankings, or decision outputs.",
        "",
        "## Outputs",
        "",
        "- `local_exports/model_v4/warning_dictionary/latest/warning_code_dictionary.csv`",
        "- `local_exports/model_v4/warning_dictionary/latest/warning_group_display_map.csv`",
        "",
        "## Warning Groups",
        "",
        "| Group | Severity | Raw Codes |",
        "|---|---|---:|",
    ]
    for row in display_map_rows:
        raw_codes = str(row["raw_warning_codes"]).split("|")
        lines.append(
            f"| {row['warning_group']} | {row['severity_hint']} | {len(raw_codes)} |"
        )
    lines.extend(
        [
            "",
            "## Highest Frequency Codes",
            "",
            "| Raw Code | Group | Count |",
            "|---|---|---:|",
        ]
    )
    for row in sorted(
        dictionary_rows,
        key=lambda value: -int(value["occurrence_count"]),
    )[:25]:
        lines.append(
            f"| {row['raw_warning_code']} | {row['warning_group']} | "
            f"{row['occurrence_count']} |"
        )
    lines.extend(
        [
            "",
            "## Drilldown Fields",
            "",
            "Each dictionary row includes `primary_module`, `primary_export`, "
            "`receipt_or_drilldown_to_open`, and `example_review_question` so a "
            "reviewer can move from a raw code to the right app surface or CSV.",
        ]
    )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Raw warning codes remain available in source exports and drilldowns.",
            "- Dictionary rows are review-only.",
            "- Warning text is not a final cut, keep, trade, defer, or draft instruction.",
        ]
    )
    return "\n".join(lines) + "\n"


def _warning_tokens(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none"}:
        return []
    tokens: list[str] = []
    for part in re.split(r"[|;,]+", text):
        code = _normalize_code(part)
        if not code or code in {"ready", "ok", "none", "no_warning"}:
            continue
        if _looks_like_sentence(code):
            continue
        if code not in tokens:
            tokens.append(code)
    return tokens


def _looks_like_sentence(code: str) -> bool:
    return len(code) > 80 or code.count("_") > 12


def _normalize_code(value: object) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("-", "_").replace(" ", "_")
    return re.sub(r"[^a-z0-9_]+", "", text)


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
