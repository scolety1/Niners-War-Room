from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path
from urllib.request import urlopen

ACTIVE_PACK_MODEL_OUTPUTS = Path(
    "local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv"
)
OUTPUT = Path(
    "local_exports/model_v4/prospect_age/latest/sleeper_player_age_supplement_20260528.csv"
)
REFERENCE_DATE = date(2026, 9, 1)
SOURCE_STATUS = "sleeper_birth_date_age_derived_admitted_fact"

HEADER = (
    "source_row",
    "player",
    "normalized_player_name",
    "nfl_team",
    "position",
    "birth_date",
    "age_reference_date",
    "age_years",
    "age_month_remainder",
    "age_total_months",
    "age_years_decimal",
    "source_status",
    "allowed_use",
    "warning_flags",
)

ALIASES = {
    "hollywoodbrown": "marquisebrown",
}


def main() -> None:
    players = _sleeper_players()
    model_players = _model_players()
    rows = []
    for source_row, player in enumerate(model_players, start=1):
        key = _normalize(player["player_name"])
        sleeper = players.get(key) or players.get(ALIASES.get(key, ""))
        if not sleeper or not sleeper.get("birth_date"):
            continue
        birth = date.fromisoformat(str(sleeper["birth_date"]))
        months = _age_months(birth, REFERENCE_DATE)
        warning_flags = []
        if key in ALIASES:
            warning_flags.append(f"sleeper_alias_match_{ALIASES[key]}")
        rows.append(
            {
                "source_row": source_row,
                "player": player["player_name"],
                "normalized_player_name": key,
                "nfl_team": sleeper.get("team") or player.get("nfl_team", ""),
                "position": sleeper.get("position") or player.get("position", ""),
                "birth_date": birth.isoformat(),
                "age_reference_date": REFERENCE_DATE.isoformat(),
                "age_years": months // 12,
                "age_month_remainder": months % 12,
                "age_total_months": months,
                "age_years_decimal": round(months / 12, 3),
                "source_status": SOURCE_STATUS,
                "allowed_use": "display_and_current_lifecycle_age_evidence_not_ranking_input",
                "warning_flags": "|".join(warning_flags),
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)
    print(f"rows={len(rows)}")
    print(f"output={OUTPUT}")


def _sleeper_players() -> dict[str, dict[str, object]]:
    with urlopen("https://api.sleeper.app/v1/players/nfl", timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    players = {}
    for player in payload.values():
        if not isinstance(player, dict):
            continue
        for field in ("full_name", "search_full_name"):
            key = _normalize(player.get(field))
            if key:
                players.setdefault(key, player)
    return players


def _model_players() -> list[dict[str, str]]:
    with ACTIVE_PACK_MODEL_OUTPUTS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            {
                "player_name": str(row.get("player_name") or ""),
                "position": str(row.get("position") or ""),
                "nfl_team": str(row.get("nfl_team") or ""),
            }
            for row in reader
            if row.get("player_name")
        ]


def _age_months(birth: date, reference: date) -> int:
    months = (reference.year - birth.year) * 12 + reference.month - birth.month
    if reference.day < birth.day:
        months -= 1
    return max(0, months)


def _normalize(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


if __name__ == "__main__":
    main()
