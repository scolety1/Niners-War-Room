from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from src.services.young_nfl_bridge_service import draft_capital_prior_score

TRUTH_SET_YOUNG_BRIDGE_PREVIEW_HEADER = (
    "truth_set_player_id",
    "player_name",
    "position",
    "nfl_team",
    "draft_year",
    "nfl_draft_round",
    "nfl_draft_pick",
    "asset_lifecycle",
    "draft_capital_prior_score",
    "draft_capital_source_status",
    "college_production_context",
    "athletic_testing_context",
    "rookie_year_context",
    "source_confidence",
    "source_name",
    "source_url",
    "source_date",
    "model_usage_status",
    "warning_flags",
)

TRUTH_SET_YOUNG_BRIDGE_RECEIPT_HEADER = (
    "truth_set_player_id",
    "player_name",
    "receipt_section",
    "raw_value",
    "derived_value",
    "source",
    "warning",
)

TRUTH_SET_YOUNG_BRIDGE_FLAG_HEADER = (
    "category",
    "player_name",
    "flag",
    "severity",
    "detail",
)

CURRENT_TRUTH_SET_SEASON = 2026

YOUNG_BRIDGE_EXPECTED_PLAYERS = (
    "Xavier Worthy",
    "Brian Thomas Jr.",
    "Ricky Pearsall",
    "Jalen Coker",
    "Luke McCaffrey",
    "Jayden Higgins",
    "Oronde Gadsden II",
    "Kaleb Johnson",
    "Luther Burden",
    "Jake Ferguson",
    "Romeo Doubs",
    "Wan'Dale Robinson",
    "Chase Brown",
    "De'Von Achane",
    "Brenton Strange",
    "Quentin Johnston",
    "Puka Nacua",
    "Malik Nabers",
    "Jaxon Smith-Njigba",
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "Ashton Jeanty",
    "Brock Bowers",
)

MISSING_EXPECTED_LIFECYCLE = {
    "Jahmyr Gibbs": "year_three_nfl_bridge",
    "Ashton Jeanty": "year_one_nfl_bridge",
    "Brock Bowers": "year_two_nfl_bridge",
}


@dataclass(frozen=True)
class TruthSetYoungBridgePriorResult:
    rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, str], ...]
    flags: tuple[dict[str, str], ...]
    summary: dict[str, object]


def build_truth_set_young_bridge_prior(
    source_path: str | Path,
    *,
    season: int = CURRENT_TRUTH_SET_SEASON,
) -> TruthSetYoungBridgePriorResult:
    source_rows = _read_rows(Path(source_path))
    rows = tuple(_preview_row(row, season=season) for row in source_rows)
    found = {str(row["player_name"]) for row in rows}
    missing_rows = tuple(
        _missing_row(player)
        for player in YOUNG_BRIDGE_EXPECTED_PLAYERS
        if player not in found
    )
    all_rows = rows + missing_rows
    flags = tuple(flag for row in all_rows for flag in _flags_for_row(row))
    receipt_rows = tuple(receipt for row in all_rows for receipt in _receipt_rows_for_row(row))
    summary = {
        "rows": len(all_rows),
        "source_rows": len(rows),
        "missing_young_bridge_rows": len(missing_rows),
        "scored_bridge_prior_rows": sum(
            bool(str(row["draft_capital_prior_score"])) for row in all_rows
        ),
        "established_not_scored_rows": sum(
            row["asset_lifecycle"] == "not_applicable_established_veteran"
            for row in all_rows
        ),
        "incoming_rookie_rows": sum(
            row["asset_lifecycle"] == "incoming_rookie" for row in all_rows
        ),
        "year_one_rows": sum(row["asset_lifecycle"] == "year_one_nfl_bridge" for row in all_rows),
        "year_two_rows": sum(row["asset_lifecycle"] == "year_two_nfl_bridge" for row in all_rows),
        "year_three_rows": sum(
            row["asset_lifecycle"] == "year_three_nfl_bridge" for row in all_rows
        ),
        "scoring_effect": "preview-only young bridge prior; no model mutation",
    }
    return TruthSetYoungBridgePriorResult(
        rows=all_rows,
        receipt_rows=receipt_rows,
        flags=flags,
        summary=summary,
    )


def write_truth_set_young_bridge_prior(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    _write_dicts(output_path, TRUTH_SET_YOUNG_BRIDGE_PREVIEW_HEADER, rows)


def write_truth_set_young_bridge_receipts(
    output_path: str | Path,
    rows: tuple[dict[str, str], ...],
) -> None:
    _write_dicts(output_path, TRUTH_SET_YOUNG_BRIDGE_RECEIPT_HEADER, rows)


def write_truth_set_young_bridge_flags(
    output_path: str | Path,
    flags: tuple[dict[str, str], ...],
) -> None:
    _write_dicts(output_path, TRUTH_SET_YOUNG_BRIDGE_FLAG_HEADER, flags)


def _preview_row(row: dict[str, str], *, season: int) -> dict[str, object]:
    player_name = _normalize_name(row.get("player_name", ""))
    position = str(row.get("position") or "")
    draft_year = _int(row.get("draft_year"))
    draft_round = _draft_round(row.get("nfl_draft_round"))
    draft_pick = _int(row.get("nfl_draft_pick"))
    lifecycle = _asset_lifecycle(draft_year, season=season)
    source_status = _draft_capital_source_status(
        raw_round=row.get("nfl_draft_round"),
        raw_pick=row.get("nfl_draft_pick"),
        lifecycle=lifecycle,
    )
    score = ""
    if lifecycle != "not_applicable_established_veteran":
        if draft_round == 0:
            score = 0.0
        elif draft_round is not None or draft_pick is not None:
            score = round(
                draft_capital_prior_score(
                    position=position,
                    draft_round=draft_round,
                    draft_overall=draft_pick,
                ),
                2,
            )
    warning_flags = _warning_flags(row, lifecycle, source_status)
    return {
        "truth_set_player_id": _truth_set_id(player_name),
        "player_name": player_name,
        "position": position,
        "nfl_team": _clean_text(row.get("nfl_team", "")),
        "draft_year": "" if draft_year is None else draft_year,
        "nfl_draft_round": _clean_text(row.get("nfl_draft_round", "")),
        "nfl_draft_pick": _clean_text(row.get("nfl_draft_pick", "")),
        "asset_lifecycle": lifecycle,
        "draft_capital_prior_score": score,
        "draft_capital_source_status": source_status,
        "college_production_context": _college_context(row),
        "athletic_testing_context": _clean_text(row.get("athletic_testing_if_available", "")),
        "rookie_year_context": _clean_text(row.get("rookie_year_nfl_production_summary", "")),
        "source_confidence": _clean_text(row.get("confidence_0_100", "")),
        "source_name": _clean_text(row.get("source_name", "")),
        "source_url": _clean_text(row.get("source_url", "")),
        "source_date": _clean_text(row.get("source_date", "")),
        "model_usage_status": "preview_only_not_scoring",
        "warning_flags": "|".join(warning_flags),
    }


def _missing_row(player_name: str) -> dict[str, object]:
    lifecycle = MISSING_EXPECTED_LIFECYCLE.get(player_name, "not_applicable_established_veteran")
    return {
        "truth_set_player_id": _truth_set_id(player_name),
        "player_name": player_name,
        "position": "",
        "nfl_team": "",
        "draft_year": "",
        "nfl_draft_round": "",
        "nfl_draft_pick": "",
        "asset_lifecycle": lifecycle,
        "draft_capital_prior_score": "",
        "draft_capital_source_status": "missing_source_row",
        "college_production_context": "",
        "athletic_testing_context": "",
        "rookie_year_context": "",
        "source_confidence": "",
        "source_name": "",
        "source_url": "",
        "source_date": "",
        "model_usage_status": "preview_only_not_scoring",
        "warning_flags": "missing_young_bridge_source_row",
    }


def _flags_for_row(row: dict[str, object]) -> tuple[dict[str, str], ...]:
    player = str(row["player_name"])
    flags: list[dict[str, str]] = []
    warning_flags = set(str(row.get("warning_flags") or "").split("|"))
    if "missing_young_bridge_source_row" in warning_flags:
        flags.append(
            _flag(
                player,
                "missing_young_bridge_source_row",
                "blocking_for_bridge_completeness",
                "Expected young bridge player is missing from the sixth report.",
            )
        )
    if "missing_draft_pick" in warning_flags:
        flags.append(
            _flag(
                player,
                "missing_draft_pick",
                "review",
                "Draft pick is missing or non-numeric; prior must handle this explicitly.",
            )
        )
    if "missing_college_production" in warning_flags:
        flags.append(
            _flag(
                player,
                "missing_college_production",
                "review",
                "College production context is blank or unavailable.",
            )
        )
    if "subjective_note_language" in warning_flags:
        flags.append(
            _flag(
                player,
                "subjective_note_language",
                "review",
                "Notes include scouting/descriptive language; keep notes display-only.",
            )
        )
    if "established_veteran_draft_capital_not_scored" in warning_flags:
        flags.append(
            _flag(
                player,
                "established_veteran_draft_capital_not_scored",
                "info",
                "Established veteran row is present but draft capital is not scored.",
            )
        )
    return tuple(flags)


def _receipt_rows_for_row(row: dict[str, object]) -> tuple[dict[str, str], ...]:
    player_id = str(row["truth_set_player_id"])
    player = str(row["player_name"])
    source = str(row.get("source_name") or row.get("source_url") or "young_player_prior")
    warnings = str(row.get("warning_flags") or "")
    return (
        _receipt(
            player_id,
            player,
            "draft_capital_prior",
            _draft_raw(row),
            str(row.get("draft_capital_prior_score", "")),
            source,
            warnings,
        ),
        _receipt(
            player_id,
            player,
            "college_production_context",
            str(row.get("college_production_context", "")),
            "",
            source,
            warnings,
        ),
        _receipt(
            player_id,
            player,
            "athletic_testing_context",
            str(row.get("athletic_testing_context", "")),
            "",
            source,
            warnings,
        ),
        _receipt(
            player_id,
            player,
            "rookie_year_context",
            str(row.get("rookie_year_context", "")),
            "",
            source,
            warnings,
        ),
        _receipt(
            player_id,
            player,
            "lifecycle",
            str(row.get("draft_year", "")),
            str(row.get("asset_lifecycle", "")),
            source,
            warnings,
        ),
    )


def _receipt(
    player_id: str,
    player: str,
    section: str,
    raw_value: str,
    derived_value: str,
    source: str,
    warning: str,
) -> dict[str, str]:
    return {
        "truth_set_player_id": player_id,
        "player_name": player,
        "receipt_section": section,
        "raw_value": raw_value,
        "derived_value": derived_value,
        "source": source,
        "warning": warning,
    }


def _flag(player: str, flag: str, severity: str, detail: str) -> dict[str, str]:
    return {
        "category": "young_bridge_prior_preview",
        "player_name": player,
        "flag": flag,
        "severity": severity,
        "detail": detail,
    }


def _asset_lifecycle(draft_year: int | None, *, season: int) -> str:
    if draft_year is None:
        return "source_gap"
    delta = season - draft_year
    if delta <= 0:
        return "incoming_rookie"
    if delta == 1:
        return "year_one_nfl_bridge"
    if delta == 2:
        return "year_two_nfl_bridge"
    if delta == 3:
        return "year_three_nfl_bridge"
    return "not_applicable_established_veteran"


def _draft_capital_source_status(
    *,
    raw_round: object,
    raw_pick: object,
    lifecycle: str,
) -> str:
    if lifecycle == "not_applicable_established_veteran":
        return "not_scored_established_veteran"
    if str(raw_round or "").strip().upper() == "UDFA":
        return "udfa_known"
    if _int(raw_pick) is None:
        return "missing_draft_pick"
    return "derived_from_round_pick"


def _warning_flags(
    row: dict[str, str],
    lifecycle: str,
    source_status: str,
) -> tuple[str, ...]:
    flags: list[str] = []
    if source_status == "missing_draft_pick":
        flags.append("missing_draft_pick")
    if source_status == "not_scored_established_veteran":
        flags.append("established_veteran_draft_capital_not_scored")
    if not _college_context(row).strip():
        flags.append("missing_college_production")
    if _has_subjective_language(row.get("notes", "")):
        flags.append("subjective_note_language")
    return tuple(flags)


def _college_context(row: dict[str, str]) -> str:
    parts = [
        row.get("college_dominator_or_share_if_available", ""),
        row.get("college_yards", ""),
        row.get("college_tds", ""),
        row.get("college_receptions_or_carries", ""),
    ]
    return " | ".join(
        _clean_text(part) for part in parts if part and not _is_blankish(part)
    )


def _draft_raw(row: dict[str, object]) -> str:
    return (
        f"year={row.get('draft_year', '')}; "
        f"round={row.get('nfl_draft_round', '')}; "
        f"pick={row.get('nfl_draft_pick', '')}"
    )


def _draft_round(value: object) -> int | None:
    text = _clean_token(value).upper()
    if text == "UDFA":
        return 0
    return _int(text)


def _int(value: object) -> int | None:
    text = _clean_token(value)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _truth_set_id(player_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", player_name.lower()).strip("_")


def _normalize_name(value: str) -> str:
    text = _clean_text(value)
    if text == "Luther Burden III":
        return "Luther Burden"
    return text


def _clean_text(value: object) -> str:
    text = str(value or "")
    replacements = {
        "\u00a0": " ",
        "\u2018": "'",
        "\u2019": "'",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "â€“": "-",
        "â€‘": "-",
        "â€™": "'",
    }
    replacements.update(
        {
            "\u2032": "'",
            "\u2033": '"',
            "\u2248": "approx",
            "\u202f": " ",
            "\u00e2\u20ac\u201c": "-",
            "\u00e2\u20ac\u201d": "-",
            "\u00e2\u20ac\u2018": "-",
            "\u00e2\u20ac\u2122": "'",
            "\u00e2\u20ac\u2032": "'",
            "\u00e2\u20ac\u2033": '"',
            "\u00e2\u2030\u02c6": "approx",
            "\u00e2\u20ac\u00af": " ",
        }
    )
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(text.strip().split())


def _clean_token(value: object) -> str:
    text = _clean_text(value)
    return "" if _is_blankish(text) else text


def _is_blankish(value: object) -> bool:
    return _clean_text(value) in {"", "-", "–", "—", "â€“"}


def _has_subjective_language(value: str) -> bool:
    return bool(
        re.search(
            r"\b(elite|explosive|star|reliable|workhorse|physical|dynamic|"
            r"record-breaking|top|strong|exceptional|limited|modest)\b",
            value,
            re.I,
        )
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dicts(
    output_path: str | Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | tuple[dict[str, str], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
