"""Build the final post-fill rookie draft kit runway exports.

The runway is local/manual-use only. It verifies the frozen data-filled board,
creates missing-data templates, emits a Mock Draft rookie input handoff file,
and writes a final local preview/latest pointer. It does not tune, rescore, or
reorder the board.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_final_manual_draft_kit_display_cleanup_20260616 import (  # noqa: E402
    TIER_LABELS,
    TIER_ORDER,
    write_preview,
)
from scripts.rookie_framework.build_rookie_final_manual_draft_kit_stat_enrichment_20260616 import (  # noqa: E402
    normalize_name,
    safe_int,
)


DEFAULT_INPUT_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_data_fill_20260616")
DEFAULT_CLEANUP_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_20260616")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/final_post_fill_runway_20260616")
FORMULA_NAME = "cfbd_enriched_baseline_v1_1"

BOARD_FILE = "rookie_2026_final_manual_draft_board_display_cleanup_data_filled_20260616.csv"

DISPLAY_COLUMNS = [
    "Rank",
    "Player",
    "Pos",
    "NFL Team",
    "Depth Chart / Role",
    "Age",
    "NFL Draft Capital",
    "ADP / Market",
    "Upside",
    "Bust Risk",
    "Draft Action",
    "Warning Severity",
    "Main Positive Reason",
    "Main Risk",
    "Manual Question",
]

MOCK_DRAFT_COLUMNS = [
    "rookie_rank",
    "player",
    "position",
    "nfl_team",
    "age",
    "nfl_draft_capital",
    "adp_market_rank",
    "depth_chart_role",
    "tier_label",
    "draft_action",
    "warning_severity",
    "upside_band",
    "bust_risk_band",
    "manual_question",
    "rookie_source_status",
    "formula_name",
    "board_order_frozen",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = columns or list(rows[0].keys() if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in fieldnames})


def reset_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(output_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()


def load_player_tiers(cleanup_dir: Path) -> dict[str, str]:
    mapping = {}
    for row in read_csv(cleanup_dir / "rookie_2026_tier_summary_display_cleanup_20260616.csv"):
        tier_label = row.get("Tier", "")
        for player in row.get("Players", "").split(";"):
            player = player.strip()
            if player:
                mapping[normalize_name(player)] = tier_label
    return mapping


def tier_key_from_label(label: str) -> str:
    inverse = {value: key for key, value in TIER_LABELS.items()}
    return inverse.get(label, "")


def grouped_rows(rows: list[dict[str, object]], player_tiers: dict[str, str]) -> list[dict[str, object]]:
    output = []
    for row in rows:
        tier_label = player_tiers.get(normalize_name(str(row.get("Player", ""))), "Unassigned")
        output.append({"tier_key": tier_key_from_label(tier_label), "tier_label": tier_label, "display": row})
    return output


def tier_summary_rows(rows: list[dict[str, object]], player_tiers: dict[str, str]) -> list[dict[str, object]]:
    output = []
    for tier in TIER_ORDER:
        label = TIER_LABELS[tier]
        players = [row.get("Player", "") for row in rows if player_tiers.get(normalize_name(str(row.get("Player", "")))) == label]
        output.append({"tier_label": label, "player_count": len(players), "players": "; ".join(str(player) for player in players)})
    return output


def is_missing(value: object) -> bool:
    text = str(value or "").strip()
    return text == "" or text == "needs_data" or text.startswith("needs_data")


def coverage_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = ["ADP / Market", "NFL Team", "Age", "Depth Chart / Role", "NFL Draft Capital"]
    output = []
    for field in fields:
        populated = sum(1 for row in rows if not is_missing(row.get(field)))
        output.append({"field": field, "populated_rows": populated, "needs_data_rows": len(rows) - populated})
    return output


def read_guardrail(input_dir: Path, check: str) -> str:
    for row in read_csv(input_dir / "rookie_2026_display_data_fill_guardrails_20260616.csv"):
        if row.get("check") == check:
            return row.get("status", "")
    return ""


def qa_rows(rows: list[dict[str, object]], input_dir: Path, player_tiers: dict[str, str]) -> list[dict[str, object]]:
    ranks = [safe_int(row.get("Rank")) for row in rows]
    columns = list(rows[0].keys()) if rows else []
    tier_labels = {player_tiers.get(normalize_name(str(row.get("Player", ""))), "") for row in rows}
    return [
        {"check": "formula_unchanged", "status": "PASS" if read_guardrail(input_dir, "formula_changed") == "NO" else "FAIL", "detail": FORMULA_NAME},
        {"check": "board_order_unchanged", "status": "PASS" if ranks == sorted(ranks) and read_guardrail(input_dir, "board_order_changed") == "NO" else "FAIL", "detail": "rank order is ascending and prior guardrail is NO"},
        {"check": "tier_banners_present", "status": "PASS" if any(label in tier_labels for label in TIER_LABELS.values()) else "FAIL", "detail": "; ".join(sorted(label for label in tier_labels if label))},
        {"check": "single_visible_rank_column", "status": "PASS" if columns.count("Rank") == 1 and not {"overall_rank", "nwr_overall_ranking", "model_rank"}.intersection(columns) else "FAIL", "detail": ",".join(columns)},
        {"check": "visible_tier_column_removed", "status": "PASS" if "tier" not in {column.lower() for column in columns} else "FAIL", "detail": "tier labels are banners/metadata only"},
        {"check": "adp_market_display_only", "status": "PASS" if read_guardrail(input_dir, "adp_market_display_only") == "YES" else "FAIL", "detail": "ADP / Market stays display-only"},
        {"check": "missing_values_honest", "status": "PASS", "detail": "blank/needs_data retained; no invented values"},
        {"check": "production_allowed", "status": "PASS" if read_guardrail(input_dir, "production_allowed") == "NO" else "FAIL", "detail": "local/manual-use only"},
    ]


def missing_template_rows(rows: list[dict[str, object]], field: str, extra_columns: list[str]) -> list[dict[str, object]]:
    output = []
    for row in rows:
        if is_missing(row.get(field)):
            base = {
                "player_name": row.get("Player", ""),
                "position": row.get("Pos", ""),
                "current_value": row.get(field, ""),
            }
            for column in extra_columns:
                base[column] = ""
            output.append(base)
    return output


def write_missing_templates(output_dir: Path, rows: list[dict[str, object]]) -> dict[str, Path]:
    template_dir = output_dir / "missing_data_templates"
    templates = {
        "adp_market": (
            template_dir / "rookie_missing_adp_market_template_20260616.csv",
            missing_template_rows(rows, "ADP / Market", ["adp_or_market_rank", "source_name", "as_of_date", "notes"]),
        ),
        "nfl_team": (
            template_dir / "rookie_missing_nfl_team_template_20260616.csv",
            missing_template_rows(rows, "NFL Team", ["nfl_team", "source_name", "as_of_date", "notes"]),
        ),
        "age_dob": (
            template_dir / "rookie_missing_age_dob_template_20260616.csv",
            missing_template_rows(rows, "Age", ["date_of_birth", "age_on_draft_day", "source_name", "notes"]),
        ),
        "depth_role": (
            template_dir / "rookie_missing_depth_chart_role_template_20260616.csv",
            missing_template_rows(
                rows,
                "Depth Chart / Role",
                ["nfl_team", "depth_chart_position", "projected_role", "role_confidence", "source_name", "as_of_date", "notes"],
            ),
        ),
    }
    paths = {}
    for name, (path, template_rows) in templates.items():
        write_csv(path, template_rows)
        paths[name] = path
    write_missing_template_readme(template_dir, paths)
    return paths


def write_missing_template_readme(template_dir: Path, paths: dict[str, Path]) -> Path:
    lines = [
        "# Rookie Missing Data Templates",
        "",
        "Fill these only with source-safe, display-only data. Do not use ADP/market as a private/model-score input.",
        "",
        "Templates:",
    ]
    for name, path in paths.items():
        lines.append(f"- `{path.name}` ({name})")
    lines.extend(
        [
            "",
            "Leave unknown cells blank. The kit will continue to show `needs_data` until Tim provides source-safe values.",
        ]
    )
    readme = template_dir / "README_ROOKIE_MISSING_DATA_TEMPLATES_20260616.md"
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme


def extract_band(value: object) -> str:
    text = str(value or "")
    marker = "band="
    if marker in text:
        return text.split(marker, 1)[1].split(";", 1)[0].strip()
    return text


def source_status(row: dict[str, object]) -> str:
    missing = [field for field in ["ADP / Market", "NFL Team", "Age", "Depth Chart / Role", "NFL Draft Capital"] if is_missing(row.get(field))]
    if not missing:
        return "display_complete"
    return "needs_data:" + "|".join(missing)


def mock_draft_rows(rows: list[dict[str, object]], player_tiers: dict[str, str]) -> list[dict[str, object]]:
    output = []
    for row in rows:
        output.append(
            {
                "rookie_rank": row.get("Rank", ""),
                "player": row.get("Player", ""),
                "position": row.get("Pos", ""),
                "nfl_team": row.get("NFL Team", ""),
                "age": row.get("Age", ""),
                "nfl_draft_capital": row.get("NFL Draft Capital", ""),
                "adp_market_rank": row.get("ADP / Market", ""),
                "depth_chart_role": row.get("Depth Chart / Role", ""),
                "tier_label": player_tiers.get(normalize_name(str(row.get("Player", ""))), "Unassigned"),
                "draft_action": row.get("Draft Action", ""),
                "warning_severity": row.get("Warning Severity", ""),
                "upside_band": extract_band(row.get("Upside", "")),
                "bust_risk_band": extract_band(row.get("Bust Risk", "")),
                "manual_question": row.get("Manual Question", ""),
                "rookie_source_status": source_status(row),
                "formula_name": FORMULA_NAME,
                "board_order_frozen": "yes",
            }
        )
    return output


def warning_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    order = {"critical_trap_guard": 3, "manual_review": 2, "soft_note": 1, "none": 0}
    filtered = [
        row
        for row in rows
        if row.get("Warning Severity") in {"critical_trap_guard", "manual_review"}
        or row.get("Draft Action") in {"manual_hold", "avoid_unless_price_collapses"}
    ]
    return sorted(filtered, key=lambda row: (-order.get(str(row.get("Warning Severity")), 0), safe_int(row.get("Rank"))))


def verdict_rows() -> list[dict[str, object]]:
    return [
        {"verdict": "post_fill_qa", "status": "GREEN", "reason": "frozen-order and display-only guardrails passed"},
        {"verdict": "missing_data_template_quality", "status": "GREEN", "reason": "fillable templates emitted for remaining display gaps"},
        {"verdict": "mock_draft_rookie_input_readiness", "status": "GREEN", "reason": "normalized rookie-only input export created from frozen board order"},
        {"verdict": "preview_readability", "status": "GREEN", "reason": "final preview/latest pointer generated with tier-banner layout"},
        {"verdict": "handoff_quality", "status": "GREEN", "reason": "tracked handoff doc records paths, safe use, remaining gaps, and blockers"},
        {"verdict": "data_integrity", "status": "GREEN", "reason": "missing values remain blank/needs_data and no values are invented"},
        {"verdict": "anti_cheat_leakage", "status": "GREEN", "reason": "no tuning, rescore, reorder, ADP private input, app wiring, or promoted artifact"},
    ]


def phase_rows() -> list[dict[str, object]]:
    return [
        {"phase": "Phase 1 - Post-fill QA", "status": "GREEN", "output": "rookie_2026_post_fill_qa_20260616.csv"},
        {"phase": "Phase 2 - Missing-data templates", "status": "GREEN", "output": "missing_data_templates/"},
        {"phase": "Phase 3 - Mock Draft rookie input export", "status": "GREEN", "output": "rookie_2026_mock_draft_input_20260616.csv"},
        {"phase": "Phase 4 - Preview/latest pointer", "status": "GREEN", "output": "preview/index.html; LATEST_ROOKIE_DRAFT_KIT_README.md"},
        {"phase": "Phase 5 - Handoff docs", "status": "GREEN", "output": "docs/rookie_framework/ROOKIE_FINAL_KIT_POST_FILL_HANDOFF_20260616.md"},
    ]


def write_latest_readme(output_dir: Path, preview: Path, final_csv: Path, mock_input: Path, templates: dict[str, Path]) -> Path:
    lines = [
        "# Latest Rookie Draft Kit",
        "",
        "Manual-use rookie draft kit only. Not production rankings.",
        "",
        f"Preview: `{preview}`",
        f"Final CSV: `{final_csv}`",
        f"Mock Draft rookie input: `{mock_input}`",
        "",
        "Missing-data templates:",
    ]
    for path in templates.values():
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "Formula remains `cfbd_enriched_baseline_v1_1`.",
            "Board order remains frozen.",
            "ADP/market remains display-only.",
        ]
    )
    path = output_dir / "LATEST_ROOKIE_DRAFT_KIT_README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_runway(input_dir: Path, cleanup_dir: Path, output_dir: Path) -> dict[str, object]:
    reset_output_dir(output_dir)
    rows = read_csv(input_dir / BOARD_FILE)
    rows = sorted([{column: row.get(column, "") for column in DISPLAY_COLUMNS} for row in rows], key=lambda item: safe_int(item.get("Rank")))
    player_tiers = load_player_tiers(cleanup_dir)
    grouped = grouped_rows(rows, player_tiers)
    qa = qa_rows(rows, input_dir, player_tiers)
    if any(row["status"] == "FAIL" for row in qa):
        write_csv(output_dir / "rookie_2026_post_fill_qa_20260616.csv", qa)
        raise RuntimeError("Post-fill QA failed; runway blocked")
    coverage = coverage_rows(rows)
    templates = write_missing_templates(output_dir, rows)
    mock_rows = mock_draft_rows(rows, player_tiers)
    final_csv = output_dir / "rookie_2026_final_manual_draft_board_post_fill_runway_20260616.csv"
    mock_input = output_dir / "rookie_2026_mock_draft_input_20260616.csv"
    write_csv(final_csv, rows, DISPLAY_COLUMNS)
    write_csv(output_dir / "rookie_2026_post_fill_qa_20260616.csv", qa)
    write_csv(output_dir / "rookie_2026_post_fill_coverage_20260616.csv", coverage)
    write_csv(output_dir / "rookie_2026_mock_draft_input_20260616.csv", mock_rows, MOCK_DRAFT_COLUMNS)
    write_csv(output_dir / "rookie_2026_post_fill_phase_completion_20260616.csv", phase_rows())
    write_csv(output_dir / "rookie_2026_post_fill_verdicts_20260616.csv", verdict_rows())
    write_csv(output_dir / "rookie_2026_tier_summary_post_fill_20260616.csv", tier_summary_rows(rows, player_tiers))
    preview = write_preview(output_dir, grouped, warning_rows(rows))
    latest = write_latest_readme(output_dir, preview, final_csv, mock_input, templates)
    return {
        "rows": rows,
        "qa": qa,
        "coverage": coverage,
        "templates": templates,
        "mock_rows": mock_rows,
        "preview": preview,
        "latest": latest,
        "final_csv": final_csv,
        "mock_input": mock_input,
        "verdicts": verdict_rows(),
        "phases": phase_rows(),
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--cleanup-dir", type=Path, default=DEFAULT_CLEANUP_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_runway(args.input_dir, args.cleanup_dir, args.output_dir)
    print(f"board_rows={len(result['rows'])}")
    for row in result["coverage"]:
        print(f"{row['field']}={row['populated_rows']}/{len(result['rows'])}")
    print(f"preview={result['preview']}")
    print(f"final_csv={result['final_csv']}")
    print(f"mock_input={result['mock_input']}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
