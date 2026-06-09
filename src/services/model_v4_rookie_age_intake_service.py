from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

RAW_ROOKIE_AGE_SOURCE = Path(
    "local_exports/model_v4/raw_user_exports/rookie_manual/incoming/"
    "player_age_mike_clay_top240_20260522.txt"
)
DEFAULT_ROOKIE_AGE_OUTPUT = Path(
    "local_exports/model_v4/prospect_age/latest/player_age_2026.csv"
)
DEFAULT_ROOKIE_AGE_DOC = Path("docs/model_v4/ROOKIE_AGE_INTAKE_20260522.md")
ROOKIE_AGE_SOURCE_STATUS = "user_provided_age_source_formula_admitted_after_validation"

ROOKIE_AGE_HEADER = (
    "source_row",
    "player",
    "normalized_player_name",
    "nfl_team",
    "position",
    "position_rank_text",
    "age_years",
    "age_month_remainder",
    "age_total_months",
    "age_years_decimal",
    "source_status",
    "allowed_use",
    "warning_flags",
)

_LINE_RE = re.compile(
    r"^\s*(?P<source_row>\d+)\.\s+"
    r"(?P<player>.+?),\s+"
    r"(?P<nfl_team>[A-Z]{2,3}\*?)\s+--\s+"
    r"(?P<position>[A-Z]+)(?P<position_rank>\d+)\s+"
    r"\(Age:\s+(?P<age_years>\d+)-(?P<age_months>\d+)\)\s*$"
)


@dataclass(frozen=True)
class RookieAgeIntakeResult:
    rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]


def build_rookie_age_rows(
    *,
    raw_path: str | Path = RAW_ROOKIE_AGE_SOURCE,
) -> RookieAgeIntakeResult:
    rows: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    path = Path(raw_path)
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.lstrip("\ufeff")
        if not line.strip() or line.strip().lower() == "top 80 rookies":
            continue
        match = _LINE_RE.match(line)
        if not match:
            warnings.append(
                {
                    "line_number": line_number,
                    "warning_code": "rookie_age_line_parse_failed",
                    "warning_detail": line,
                }
            )
            continue
        data = match.groupdict()
        age_years = int(data["age_years"])
        age_months = int(data["age_months"])
        warning_flags: list[str] = []
        if age_months < 0 or age_months > 11:
            warning_flags.append("age_month_remainder_out_of_range")
        age_total_months = age_years * 12 + age_months
        rows.append(
            {
                "source_row": int(data["source_row"]),
                "player": data["player"],
                "normalized_player_name": _normalize_name(data["player"]),
                "nfl_team": data["nfl_team"].removesuffix("*"),
                "position": data["position"],
                "position_rank_text": f"{data['position']}{data['position_rank']}",
                "age_years": age_years,
                "age_month_remainder": age_months,
                "age_total_months": age_total_months,
                "age_years_decimal": round(age_total_months / 12, 3),
                "source_status": ROOKIE_AGE_SOURCE_STATUS,
                "allowed_use": "prospect_lifecycle_age_evidence_not_ranking_input",
                "warning_flags": "|".join(warning_flags),
            }
        )
    return RookieAgeIntakeResult(rows=tuple(rows), warning_rows=tuple(warnings))


def write_rookie_age_outputs(
    *,
    output_path: str | Path = DEFAULT_ROOKIE_AGE_OUTPUT,
    doc_path: str | Path = DEFAULT_ROOKIE_AGE_DOC,
    result: RookieAgeIntakeResult | None = None,
) -> tuple[Path, Path]:
    result = result or build_rookie_age_rows()
    output = Path(output_path)
    doc = Path(doc_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROOKIE_AGE_HEADER)
        writer.writeheader()
        writer.writerows(result.rows)
    doc.write_text(_doc(result, output), encoding="utf-8")
    return output, doc


def _normalize_name(value: str) -> str:
    lowered = value.lower().strip()
    for token in (" jr.", " sr.", " ii", " iii", " iv"):
        lowered = lowered.replace(token, "")
    return re.sub(r"[^a-z0-9]+", "", lowered)


def _doc(result: RookieAgeIntakeResult, output_path: Path) -> str:
    return (
        "# Rookie Age Intake - 2026-05-22\n\n"
        "This intake preserves the user-provided Mike Clay ranking/age list as a targeted "
        "age and market-context source. Age can support lifecycle logic after matching. "
        "The source ranking/order is retained only as `source_row` and must not drive "
        "private player value.\n\n"
        f"- Parsed rows: {len(result.rows)}\n"
        f"- Parse warnings: {len(result.warning_rows)}\n"
        f"- Output: `{output_path}`\n"
        f"- Source status: `{ROOKIE_AGE_SOURCE_STATUS}`\n\n"
        "Allowed use: age/lifecycle evidence for admitted player or prospect rows. "
        "Blocked use: source order, Mike Clay rank, positional rank text, or team labels "
        "as private football value or final recommendations.\n"
    )
