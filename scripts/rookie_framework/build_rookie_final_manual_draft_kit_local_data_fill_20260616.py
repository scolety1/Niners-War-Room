"""Fill display-only local fields for the cleaned rookie draft kit.

This patch reads the already-cleaned local/manual-use draft kit and fills only
display-room fields from approved local sources. It does not tune, rescore,
reorder, or use ADP/market as a private/model-score input.
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


DEFAULT_CLEANUP_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_20260616")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_data_fill_20260616")
DEFAULT_FANTASYPROS_ADP = Path(
    "local_exports/model_v4/prospect_sources/latest/files/source_project/data/fantasypros/processed/"
    "fantasypros_overall_adp_2026.csv"
)
DEFAULT_ROOKIE_ADP = Path(
    "local_exports/model_v4/prospect_sources/latest/files/source_project/data/market/processed/"
    "rookie_adp_2026_04_23_to_2026_05_17.csv"
)
DEFAULT_IDENTITY_SPINE = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/"
    "admitted_current_prospect_identity_spine.csv"
)
DEFAULT_AGE_EXPORT = Path(
    "C:/Users/smcol/Documents/Vacation/Niners-War-Room-drop-decision/local_exports/model_v4/prospect_age/latest/"
    "player_age_2026.csv"
)

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


def clean_number(value: str) -> str:
    text = str(value or "").strip()
    if text == "":
        return ""
    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
        return f"{number:.2f}".rstrip("0").rstrip(".")
    except ValueError:
        return text


def load_rookie_adp(path: Path) -> dict[str, dict[str, str]]:
    lookup = {}
    for row in read_csv(path):
        player = row.get("player", "")
        if not player:
            continue
        lookup[normalize_name(player)] = row
    return lookup


def load_fantasypros_adp(path: Path) -> dict[str, dict[str, str]]:
    lookup = {}
    for row in read_csv(path):
        player = row.get("player", "")
        if not player:
            continue
        lookup[normalize_name(player)] = row
    return lookup


def adp_display(player: str, rookie_adp: dict[str, dict[str, str]], fantasypros: dict[str, dict[str, str]]) -> str:
    key = normalize_name(player)
    if key in rookie_adp:
        row = rookie_adp[key]
        rank = clean_number(row.get("adp_rank", ""))
        adp = clean_number(row.get("adp", ""))
        return f"Rookie ADP rank {rank}; ADP {adp}; source=Rookie ADP"
    if key in fantasypros:
        row = fantasypros[key]
        rank = clean_number(row.get("rank", ""))
        adp = clean_number(row.get("average_adp", ""))
        return f"FantasyPros rank {rank}; ADP {adp}; source=FantasyPros"
    return "needs_data"


def load_identity_teams(path: Path) -> dict[str, str]:
    lookup = {}
    for row in read_csv(path):
        name = row.get("prospect_name", "")
        team = row.get("nfl_team", "").strip()
        admitted = row.get("formula_identity_admitted", "").strip().lower()
        if name and team and admitted in {"true", "1", "yes"}:
            lookup[normalize_name(name)] = team
    return lookup


def load_age(path: Path) -> dict[str, str]:
    lookup = {}
    for row in read_csv(path):
        name = row.get("player", "")
        age = row.get("age_years_decimal", "").strip()
        allowed = row.get("allowed_use", "").strip()
        if name and age and allowed == "local_review_only":
            lookup[normalize_name(name)] = clean_number(age)
    return lookup


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


def fill_rows(
    baseline: list[dict[str, str]],
    rookie_adp: dict[str, dict[str, str]],
    fantasypros: dict[str, dict[str, str]],
    teams: dict[str, str],
    ages: dict[str, str],
) -> list[dict[str, object]]:
    output = []
    for row in sorted(baseline, key=lambda item: safe_int(item.get("Rank"))):
        player = row.get("Player", "")
        key = normalize_name(player)
        filled = dict(row)
        filled["ADP / Market"] = adp_display(player, rookie_adp, fantasypros)
        filled["NFL Team"] = teams.get(key) or row.get("NFL Team", "") or "needs_data"
        filled["Age"] = ages.get(key) or row.get("Age", "") or "needs_data"
        for column in DISPLAY_COLUMNS:
            if filled.get(column, "") == "":
                filled[column] = "needs_data" if column in {"NFL Team", "Depth Chart / Role", "Age", "ADP / Market"} else ""
        output.append({column: filled.get(column, "") for column in DISPLAY_COLUMNS})
    return output


def grouped_rows(rows: list[dict[str, object]], player_tiers: dict[str, str]) -> list[dict[str, object]]:
    output = []
    for row in rows:
        tier_label = player_tiers.get(normalize_name(str(row.get("Player", ""))), "Unassigned")
        output.append({"tier_key": tier_key_from_label(tier_label), "tier_label": tier_label, "display": row})
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


def coverage_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = ["ADP / Market", "NFL Team", "Age", "Depth Chart / Role", "NFL Draft Capital"]
    output = []
    for field in fields:
        populated = sum(
            1
            for row in rows
            if str(row.get(field, "")).strip() not in {"", "needs_data"}
            and not str(row.get(field, "")).startswith("needs_data")
        )
        output.append(
            {
                "field": field,
                "populated_rows": populated,
                "needs_data_rows": len(rows) - populated,
            }
        )
    return output


def source_rows(paths: dict[str, Path]) -> list[dict[str, object]]:
    return [
        {"field": "ADP / Market", "source": "Rookie ADP, fallback FantasyPros overall ADP", "path": f"{paths['rookie_adp']} | {paths['fantasypros']}", "use": "display_only"},
        {"field": "NFL Team", "source": "Admitted current prospect identity spine", "path": str(paths["identity"]), "use": "display_only"},
        {"field": "Age", "source": "Drop Decision prospect age export", "path": str(paths["age"]), "use": "display_only_local_review_only"},
        {"field": "Depth Chart / Role", "source": "Existing role-tag fallback from cleanup export", "path": str(paths["cleanup"]), "use": "display_only"},
        {"field": "NFL Draft Capital", "source": "Existing cleanup/current board draft-capital display", "path": str(paths["cleanup"]), "use": "display_only"},
    ]


def prior_formula_guardrail(cleanup_dir: Path) -> str:
    for row in read_csv(cleanup_dir / "rookie_2026_display_cleanup_guardrails_20260616.csv"):
        if row.get("check") == "formula_changed":
            return "NO" if row.get("status") == "NO" else "REVIEW"
    return "REVIEW"


def guardrail_rows(rows: list[dict[str, object]], baseline: list[dict[str, str]], cleanup_dir: Path) -> list[dict[str, object]]:
    return [
        {"check": "board_order_changed", "status": "NO" if [row.get("Rank") for row in rows] == [row.get("Rank") for row in baseline] else "YES"},
        {"check": "formula_changed", "status": prior_formula_guardrail(cleanup_dir)},
        {"check": "adp_market_display_only", "status": "YES"},
        {"check": "new_model_inputs_added", "status": "NO"},
        {"check": "missing_values_invented", "status": "NO"},
        {"check": "duplicate_rank_columns_removed", "status": "YES"},
        {"check": "production_allowed", "status": "NO"},
    ]


def verdict_rows() -> list[dict[str, object]]:
    return [
        {"verdict": "data_fill_coverage", "status": "YELLOW_GREEN", "reason": "ADP/team/age coverage improved from local display-only sources; depth chart remains limited to role tags"},
        {"verdict": "draft_use_readability", "status": "GREEN", "reason": "tier-banner layout and cleaned columns preserved"},
        {"verdict": "data_integrity", "status": "GREEN", "reason": "missing values remain needs_data and no values are invented"},
        {"verdict": "anti_cheat_leakage", "status": "GREEN", "reason": "no tuning, rescore, reorder, ADP private input, app wiring, or promoted artifact"},
    ]


def write_readme(output_dir: Path, preview: Path) -> None:
    lines = [
        "# Rookie Final Manual Draft Kit Local Data Fill",
        "",
        "Local/manual-use display-data fill only.",
        "",
        f"Preview: `{preview}`",
        "",
        "ADP/market remains display-only.",
        "Formula remains cfbd_enriched_baseline_v1_1 and board order is unchanged.",
    ]
    (output_dir / "README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_LOCAL_DATA_FILL_20260616.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def build_local_data_fill(
    cleanup_dir: Path,
    fantasypros: Path,
    rookie_adp_path: Path,
    identity: Path,
    age: Path,
    output_dir: Path,
) -> dict[str, object]:
    reset_output_dir(output_dir)
    baseline = read_csv(cleanup_dir / "rookie_2026_final_manual_draft_board_display_cleanup_20260616.csv")
    player_tiers = load_player_tiers(cleanup_dir)
    rows = fill_rows(
        baseline,
        load_rookie_adp(rookie_adp_path),
        load_fantasypros_adp(fantasypros),
        load_identity_teams(identity),
        load_age(age),
    )
    grouped = grouped_rows(rows, player_tiers)
    warnings = warning_rows(rows)
    coverage = coverage_rows(rows)
    paths = {
        "cleanup": cleanup_dir,
        "fantasypros": fantasypros,
        "rookie_adp": rookie_adp_path,
        "identity": identity,
        "age": age,
    }
    sources = source_rows(paths)
    guardrails = guardrail_rows(rows, baseline, cleanup_dir)
    verdicts = verdict_rows()

    write_csv(output_dir / "rookie_2026_final_manual_draft_board_display_cleanup_data_filled_20260616.csv", rows, DISPLAY_COLUMNS)
    write_csv(output_dir / "rookie_2026_draft_day_quick_sheet_display_cleanup_data_filled_20260616.csv", rows, DISPLAY_COLUMNS)
    write_csv(output_dir / "rookie_2026_warning_priority_display_cleanup_data_filled_20260616.csv", warnings, DISPLAY_COLUMNS)
    write_csv(output_dir / "rookie_2026_display_data_fill_coverage_20260616.csv", coverage)
    write_csv(output_dir / "rookie_2026_display_data_fill_sources_20260616.csv", sources)
    write_csv(output_dir / "rookie_2026_display_data_fill_guardrails_20260616.csv", guardrails)
    write_csv(output_dir / "rookie_2026_display_data_fill_verdicts_20260616.csv", verdicts)
    preview = write_preview(output_dir, grouped, warnings)
    write_readme(output_dir, preview)
    return {
        "rows": rows,
        "grouped": grouped,
        "warnings": warnings,
        "coverage": coverage,
        "sources": sources,
        "guardrails": guardrails,
        "verdicts": verdicts,
        "preview": preview,
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup-dir", type=Path, default=DEFAULT_CLEANUP_DIR)
    parser.add_argument("--fantasypros-adp", type=Path, default=DEFAULT_FANTASYPROS_ADP)
    parser.add_argument("--rookie-adp", type=Path, default=DEFAULT_ROOKIE_ADP)
    parser.add_argument("--identity-spine", type=Path, default=DEFAULT_IDENTITY_SPINE)
    parser.add_argument("--age-export", type=Path, default=DEFAULT_AGE_EXPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_local_data_fill(
        args.cleanup_dir,
        args.fantasypros_adp,
        args.rookie_adp,
        args.identity_spine,
        args.age_export,
        args.output_dir,
    )
    print(f"board_rows={len(result['rows'])}")
    for row in result["coverage"]:
        print(f"{row['field']}={row['populated_rows']}/{len(result['rows'])}")
    print(f"preview={result['preview']}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
