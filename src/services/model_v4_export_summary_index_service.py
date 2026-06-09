from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

MODEL_ROOT = Path("local_exports/model_v4")
DEFAULT_OUTPUT_ROOT = MODEL_ROOT / "export_summary/latest"
DOC_PATH = Path("docs/model_v4/MODEL_V4_7_RAW_EXPORT_SUMMARY_INDEX.md")
VERSION = "model_v4_7_export_summary_index_0.1.0"

REVIEW_ONLY_STATUS = "review_only_export_index_not_recommendation"

INDEX_HEADER = (
    "export_name",
    "path",
    "row_count",
    "primary_use",
    "review_first_when",
    "key_columns",
    "review_only_status",
    "raw_or_summary",
    "formula_version",
)

EXPORTS = (
    {
        "export_name": "Evidence Risk Player Summary",
        "path": MODEL_ROOT / "source_risk_heatmap/latest/source_risk_player_summary_rows.csv",
        "primary_use": "One-row-per-player evidence risk review.",
        "review_first_when": "A player score looks fragile or source-dependent.",
        "key_columns": (
            "player_name|worst_source_risk_level|severity_label|"
            "human_review_priority|warning_summary"
        ),
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Evidence Risk Raw Player Rows",
        "path": MODEL_ROOT / "source_risk_heatmap/latest/source_risk_player_rows.csv",
        "primary_use": "Module/context-level source-risk audit rows.",
        "review_first_when": "The summary row needs raw evidence detail.",
        "key_columns": "player_name|source_risk_level|biggest_source_risk|warning_summary",
        "raw_or_summary": "raw",
    },
    {
        "export_name": "Model Edge Queue",
        "path": MODEL_ROOT / "model_edge_queue/latest/model_edge_rows.csv",
        "primary_use": "Unusual model rankings and edge-vs-source classification.",
        "review_first_when": "A player rank looks weird, high, low, or format-sensitive.",
        "key_columns": (
            "player_name|weirdness_type|edge_classification|why_weird|"
            "human_review_question"
        ),
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Warning Code Dictionary",
        "path": MODEL_ROOT / "warning_dictionary/latest/warning_code_dictionary.csv",
        "primary_use": "Plain-English warning code decoder with module links.",
        "review_first_when": "Raw warning strings need translation or traceability.",
        "key_columns": (
            "raw_warning_code|warning_group|primary_module|"
            "receipt_or_drilldown_to_open"
        ),
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Warning Group Display Map",
        "path": MODEL_ROOT / "warning_dictionary/latest/warning_group_display_map.csv",
        "primary_use": "High-level warning groups and raw-code membership.",
        "review_first_when": "You need the warning group taxonomy.",
        "key_columns": "warning_group|severity_hint|raw_warning_codes",
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Pick Decision Lab",
        "path": MODEL_ROOT / "rookie_pick_decision_lab/latest/pick_decision_rows.csv",
        "primary_use": "Owned-pick candidate clusters and manual review questions.",
        "review_first_when": "Reviewing 1.03, 1.04, 2.04, 2.08, or manual-only 5.04.",
        "key_columns": (
            "pick_label|top_rookie_candidates|review_label|"
            "manual_question_pick_value|warning_flags"
        ),
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Cut Cost",
        "path": MODEL_ROOT / "roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv",
        "primary_use": "Roster deadline opportunity-cost context.",
        "review_first_when": "Reviewing what model value leaves the roster if a player is dropped.",
        "key_columns": (
            "player_name|current_model_score|rookie_pick_equivalent|"
            "pick_baseline_status|opportunity_cost_label"
        ),
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Player Rank Explainer",
        "path": MODEL_ROOT / "explainers/latest/player_rank_explainer_rows.csv",
        "primary_use": "Plain-English explanation for player ranks.",
        "review_first_when": "A rank needs an understandable reason.",
        "key_columns": (
            "player_name|short_explanation|strongest_signals|"
            "weakest_signals|manual_review_note"
        ),
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Startup Slot Board",
        "path": MODEL_ROOT / "startup_slot_simulator/latest/startup_slot_review_rows.csv",
        "primary_use": "Internal cross-asset model slot board.",
        "review_first_when": "Comparing rookies, picks, current players, and drop candidates.",
        "key_columns": (
            "startup_slot_rank|entity_type|player_or_asset|model_score|"
            "nearby_assets_before|nearby_assets_after"
        ),
        "raw_or_summary": "summary",
    },
    {
        "export_name": "Rookie Draft Board",
        "path": MODEL_ROOT / "rookie_draft_review/latest/rookie_draft_board_review_rows.csv",
        "primary_use": "Rookie prospect board and component-level review columns.",
        "review_first_when": "Inspecting rookie ranks and profile components.",
        "key_columns": (
            "board_rank|prospect_name|position|league_format_adjusted_score|"
            "warning_flags"
        ),
        "raw_or_summary": "summary",
    },
)


@dataclass(frozen=True)
class ExportSummaryIndexResult:
    rows: tuple[dict[str, object], ...]
    doc_text: str


def build_export_summary_index() -> ExportSummaryIndexResult:
    rows = tuple(_index_row(export) for export in EXPORTS)
    return ExportSummaryIndexResult(rows=rows, doc_text=_doc_text(rows))


def write_export_summary_index_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: ExportSummaryIndexResult | None = None,
) -> dict[str, Path]:
    result = result or build_export_summary_index()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "index": output / "export_summary_index.csv",
        "doc": doc,
    }
    _write_csv(paths["index"], INDEX_HEADER, result.rows)
    paths["doc"].write_text(result.doc_text, encoding="utf-8")
    return paths


def _index_row(export: dict[str, object]) -> dict[str, object]:
    path = Path(export["path"])
    return {
        "export_name": export["export_name"],
        "path": path.as_posix(),
        "row_count": _row_count(path),
        "primary_use": export["primary_use"],
        "review_first_when": export["review_first_when"],
        "key_columns": export["key_columns"],
        "review_only_status": REVIEW_ONLY_STATUS,
        "raw_or_summary": export["raw_or_summary"],
        "formula_version": VERSION,
    }


def _row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _row in csv.DictReader(handle))


def _doc_text(rows: tuple[dict[str, object], ...]) -> str:
    lines = [
        "# Model v4.7 Raw Export Summary Index",
        "",
        "## Scope",
        "",
        "This review-only index points human reviewers to the right Model v4 exports. "
        "It does not replace raw files and does not change model values.",
        "",
        "## Exports",
        "",
        "| Export | Rows | Type | Review First When |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['export_name']} | {row['row_count']} | {row['raw_or_summary']} | "
            f"{row['review_first_when']} |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- Index rows are review-only.",
            "- Raw exports remain available.",
            "- No formulas, scores, rankings, or app state are changed.",
            "- The index does not create cut, keep, trade, defer, or draft recommendations.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
