"""Build Rookie Framework v0.3 draft-day simulation exports.

This is a local-only dry-run over the rookie analyzer output for Tim's known
picks. It does not model opponents, use ADP or market data, create
probabilities or bands, wire app output, change private scores, or use veteran
outcome heads.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


DEFAULT_ANALYZER_ROOT = Path("local_exports/model_v4/rookie_framework_v02/rookie_analyzer_v03")
DEFAULT_OUTPUT_DIR = Path("local_exports/model_v4/rookie_framework_v02/draft_day_simulation_v03")

ANALYZER_FULL = Path("rookie_analyzer_v03.csv")
ANALYZER_README = Path("rookie_analyzer_readme.md")
REQUIRED_INPUTS = [ANALYZER_FULL, ANALYZER_README]

PICKS = ["1.03", "1.04", "2.04", "2.08", "5.04"]

SIMULATION_COLUMNS = [
    "pick",
    "simulation_rank",
    "player_id",
    "player",
    "position",
    "school",
    "source_pick_zone",
    "production_ready_status",
    "analyzer_group",
    "fit_signal",
    "best_pick_fit",
    "trade_down_signal",
    "emergency_stop_signal",
    "warnings",
    "blockers",
    "draft_only_if",
    "do_not_draft_if",
    "simulation_action",
    "simulation_only",
    "app_ready",
    "production_score_created",
    "probabilities_created",
]

PICK_CARD_COLUMNS = [
    "pick",
    "default_action",
    "top_review_options",
    "manual_review_options",
    "emergency_stop_count",
    "trade_down_signal",
    "notes",
    "simulation_only",
    "app_ready",
    "production_score_created",
    "probabilities_created",
]

PROHIBITED_PRIVATE_INPUT_COLUMNS = {
    "adp",
    "rank",
    "ranking",
    "rankings",
    "projection",
    "projections",
    "consensus",
    "market",
    "trade_value",
    "draft_kit",
    "league_rank",
    "private_score",
    "fantasy_forecast",
    "fantasy_forecasts",
    "probability",
    "band",
}

ALLOWED_CONTEXT_COLUMNS = {"analyzer_rank", "trade_down_signal"}


class DraftDaySimulationError(RuntimeError):
    """Raised when draft-day simulation export validation fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise DraftDaySimulationError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def reject_data_path(path: Path) -> None:
    if any(part.lower() == "data" for part in path.parts):
        raise DraftDaySimulationError(f"Draft-day simulation must not read from or write to data/: {path}")


def require_inputs(analyzer_root: Path) -> None:
    reject_data_path(analyzer_root)
    missing = [str(analyzer_root / rel_path) for rel_path in REQUIRED_INPUTS if not (analyzer_root / rel_path).exists()]
    if missing:
        raise DraftDaySimulationError("Required analyzer inputs are missing:\n" + "\n".join(f"- {p}" for p in missing))


def normalized_field_tokens(field_name: str) -> set[str]:
    normalized = "".join(ch if ch.isalnum() else "_" for ch in field_name.lower())
    tokens = {token for token in normalized.split("_") if token}
    tokens.add(normalized)
    return tokens


def find_prohibited_private_input_columns(fieldnames: Iterable[str]) -> list[str]:
    bad = []
    for field in fieldnames:
        if field in ALLOWED_CONTEXT_COLUMNS:
            continue
        if normalized_field_tokens(field) & PROHIBITED_PRIVATE_INPUT_COLUMNS:
            bad.append(field)
    return sorted(set(bad))


def strict_validate_inputs(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise DraftDaySimulationError("Analyzer input has no rows.")
    bad = find_prohibited_private_input_columns(rows[0].keys())
    if bad:
        raise DraftDaySimulationError("Prohibited private input columns detected: " + ", ".join(bad))
    bad_app = [row.get("player_id", "") for row in rows if row.get("app_ready") != "no"]
    bad_score = [row.get("player_id", "") for row in rows if row.get("production_score_created") != "no"]
    bad_prob = [row.get("player_id", "") for row in rows if row.get("probabilities_created") != "no"]
    if bad_app:
        raise DraftDaySimulationError("Analyzer rows missing app_ready=no: " + ", ".join(bad_app[:10]))
    if bad_score:
        raise DraftDaySimulationError("Analyzer rows missing production_score_created=no: " + ", ".join(bad_score[:10]))
    if bad_prob:
        raise DraftDaySimulationError("Analyzer rows missing probabilities_created=no: " + ", ".join(bad_prob[:10]))


def fit_field_for_pick(pick: str) -> str:
    return "fit_" + pick.replace(".", "_")


def is_review_option(row: dict[str, str], pick: str) -> bool:
    if pick == "1.03":
        return False
    fit_value = row.get(fit_field_for_pick(pick), "")
    if fit_value.startswith("do_not_use") or fit_value.startswith("not_a_"):
        return False
    if fit_value in {"manual_review_only", "roster_declaration_hold"}:
        return False
    return bool(fit_value)


def simulation_action(row: dict[str, str], pick: str) -> str:
    fit_value = row.get(fit_field_for_pick(pick), "")
    if row.get("production_ready_status") == "manual_review_required" or fit_value == "manual_review_hold":
        return "manual_review_before_pick"
    if row.get("emergency_stop_signal", "").startswith("yes"):
        return "emergency_stop_review"
    if "visible_warnings" in fit_value:
        return "review_with_visible_warnings"
    if pick == "1.03":
        return "trade_down_or_manual_review"
    return "context_only"


def no_player_row(pick: str) -> dict[str, str]:
    return {
        "pick": pick,
        "simulation_rank": "1",
        "player_id": f"pick:{pick}:no_player_cleared",
        "player": "NO_PLAYER_CLEARED",
        "position": "",
        "school": "",
        "source_pick_zone": pick,
        "production_ready_status": "manual_review_required",
        "analyzer_group": "manual_review",
        "fit_signal": "trade_down_or_manual_review_only_no_player_cleared",
        "best_pick_fit": "trade_down_or_manual_review",
        "trade_down_signal": "yes_1_03_and_premium_bar_not_cleared",
        "emergency_stop_signal": "yes_no_clear_uncapped_player",
        "warnings": "1.03 remains unsupported by source-safe analyzer rows",
        "blockers": "no_player_cleared",
        "draft_only_if": "Tim manually clears a player from later approved source-safe evidence",
        "do_not_draft_if": "no clear uncapped player is available",
        "simulation_action": "trade_down_or_manual_review",
        "simulation_only": "yes",
        "app_ready": "no",
        "production_score_created": "no",
        "probabilities_created": "no",
    }


def pick_rows(rows: list[dict[str, str]], pick: str) -> list[dict[str, str]]:
    if pick == "1.03":
        return [no_player_row(pick)]
    candidates = [row for row in rows if is_review_option(row, pick)]
    output: list[dict[str, str]] = []
    for index, row in enumerate(candidates, start=1):
        output.append(
            {
                "pick": pick,
                "simulation_rank": str(index),
                "player_id": row.get("player_id", ""),
                "player": row.get("player", ""),
                "position": row.get("position", ""),
                "school": row.get("school", ""),
                "source_pick_zone": row.get("pick_zone", ""),
                "production_ready_status": row.get("production_ready_status", ""),
                "analyzer_group": row.get("analyzer_group", ""),
                "fit_signal": row.get(fit_field_for_pick(pick), ""),
                "best_pick_fit": row.get("best_pick_fit", ""),
                "trade_down_signal": row.get("trade_down_signal", ""),
                "emergency_stop_signal": row.get("emergency_stop_signal", ""),
                "warnings": row.get("warnings", ""),
                "blockers": row.get("blockers", ""),
                "draft_only_if": row.get("draft_only_if", ""),
                "do_not_draft_if": row.get("do_not_draft_if", ""),
                "simulation_action": simulation_action(row, pick),
                "simulation_only": "yes",
                "app_ready": "no",
                "production_score_created": "no",
                "probabilities_created": "no",
            }
        )
    return output


def pick_card(pick: str, rows: list[dict[str, str]]) -> dict[str, str]:
    names = [row["player"] for row in rows if row["player"] != "NO_PLAYER_CLEARED"]
    manual = [row["player"] for row in rows if row["simulation_action"] == "manual_review_before_pick"]
    emergency_count = sum(1 for row in rows if row.get("emergency_stop_signal", "").startswith("yes"))
    if pick == "1.03":
        default_action = "trade_down_or_manual_review"
        trade_signal = "yes"
        notes = "1.03 remains unsupported; no player is forced open."
    elif names:
        default_action = "review_top_options_with_visible_warnings"
        trade_signal = "yes" if any(row.get("trade_down_signal", "").startswith("yes") for row in rows[:3]) else "no"
        notes = "Dry-run pick card from analyzer output only."
    else:
        default_action = "pause_no_review_option"
        trade_signal = "yes"
        notes = "No analyzer row cleared for this pick context."
    return {
        "pick": pick,
        "default_action": default_action,
        "top_review_options": "|".join(names[:5]) if names else "none",
        "manual_review_options": "|".join(manual[:5]) if manual else "none",
        "emergency_stop_count": str(emergency_count),
        "trade_down_signal": trade_signal,
        "notes": notes,
        "simulation_only": "yes",
        "app_ready": "no",
        "production_score_created": "no",
        "probabilities_created": "no",
    }


def validate_simulation_rows(rows: list[dict[str, str]], cards: list[dict[str, str]]) -> None:
    if not rows:
        raise DraftDaySimulationError("No simulation rows were produced.")
    missing_picks = [pick for pick in PICKS if pick not in {row["pick"] for row in rows}]
    if missing_picks:
        raise DraftDaySimulationError("Missing simulation pick contexts: " + ", ".join(missing_picks))
    if any(row.get("app_ready") != "no" for row in rows + cards):
        raise DraftDaySimulationError("Simulation rows must keep app_ready=no.")
    if any(row.get("production_score_created") != "no" for row in rows + cards):
        raise DraftDaySimulationError("Simulation rows must keep production_score_created=no.")
    if any(row.get("probabilities_created") != "no" for row in rows + cards):
        raise DraftDaySimulationError("Simulation rows must keep probabilities_created=no.")
    one03 = [row for row in rows if row["pick"] == "1.03"]
    if len(one03) != 1 or one03[0]["player"] != "NO_PLAYER_CLEARED":
        raise DraftDaySimulationError("1.03 must remain no-player-cleared in the simulation.")


def write_readme(output_dir: Path, rows: list[dict[str, str]], cards: list[dict[str, str]]) -> None:
    pick_counts = Counter(row["pick"] for row in rows)
    text = f"""# Rookie Draft-Day Simulation v0.3

Status: local-only dry-run simulation.

This export does not model opponents, does not use ADP or market data, does not
create probabilities or bands, does not create app-ready output, does not change
private scores, and does not use veteran outcome heads.

## Outputs

- `rookie_draft_day_simulation_v03.csv`
- `rookie_draft_day_pick_cards_v03.csv`
- `README_ROOKIE_DRAFT_DAY_SIMULATION_V03.md`

## Pick Counts

"""
    for pick in PICKS:
        text += f"- {pick}: {pick_counts.get(pick, 0)} simulation rows\n"
    text += f"\nPick cards: {len(cards)}\n\nEvery row has `simulation_only=yes`, `app_ready=no`, `production_score_created=no`, and `probabilities_created=no`.\n"
    (output_dir / "README_ROOKIE_DRAFT_DAY_SIMULATION_V03.md").write_text(text, encoding="utf-8")


def build_exports(analyzer_root: Path, output_dir: Path, strict: bool = False) -> dict[str, int]:
    reject_data_path(output_dir)
    require_inputs(analyzer_root)
    analyzer_rows = read_csv(analyzer_root / ANALYZER_FULL)
    if strict:
        strict_validate_inputs(analyzer_rows)
    simulation_rows: list[dict[str, str]] = []
    for pick in PICKS:
        simulation_rows.extend(pick_rows(analyzer_rows, pick))
    cards = [pick_card(pick, [row for row in simulation_rows if row["pick"] == pick]) for pick in PICKS]
    validate_simulation_rows(simulation_rows, cards)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_draft_day_simulation_v03.csv", simulation_rows, SIMULATION_COLUMNS)
    write_csv(output_dir / "rookie_draft_day_pick_cards_v03.csv", cards, PICK_CARD_COLUMNS)
    write_readme(output_dir, simulation_rows, cards)

    counts = Counter(row["pick"] for row in simulation_rows)
    return {
        "simulation_rows": len(simulation_rows),
        "pick_cards": len(cards),
        "pick_1_03_rows": counts.get("1.03", 0),
        "pick_1_04_rows": counts.get("1.04", 0),
        "pick_2_04_rows": counts.get("2.04", 0),
        "pick_2_08_rows": counts.get("2.08", 0),
        "pick_5_04_rows": counts.get("5.04", 0),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Rookie Framework v0.3 draft-day simulation exports.")
    parser.add_argument("--analyzer-root", type=Path, default=DEFAULT_ANALYZER_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    try:
        counts = build_exports(args.analyzer_root, output_dir, strict=args.strict)
    except DraftDaySimulationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
