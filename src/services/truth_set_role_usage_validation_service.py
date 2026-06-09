from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

TRUTH_SET_ROLE_USAGE_STRICT_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "season",
    "snap_share",
    "route_participation",
    "routes_run",
    "target_share",
    "targets_per_route_run",
    "yards_per_route_run",
    "rb_carry_share",
    "rb_target_share",
    "weighted_opportunities",
    "red_zone_touches",
    "goal_line_touches",
    "source_name",
    "source_url",
    "source_date",
    "confidence_0_100",
    "notes",
)

ROLE_USAGE_NUMERIC_COLUMNS = (
    "season",
    "snap_share",
    "route_participation",
    "routes_run",
    "target_share",
    "targets_per_route_run",
    "yards_per_route_run",
    "rb_carry_share",
    "rb_target_share",
    "weighted_opportunities",
    "red_zone_touches",
    "goal_line_touches",
    "confidence_0_100",
)

ROLE_USAGE_FLAG_HEADER = (
    "source_file",
    "row_number",
    "player_name",
    "flag",
    "severity",
    "column",
    "value",
    "detail",
)

ROLE_USAGE_SUMMARY_HEADER = (
    "source_file",
    "status",
    "header_status",
    "rows",
    "expected_players",
    "unique_players",
    "missing_players",
    "duplicate_players",
    "malformed_width_rows",
    "numeric_error_rows",
    "uncertain_marker_rows",
    "prose_numeric_rows",
    "embedded_url_rows",
    "source_separation_rows",
    "blocking_flags",
    "review_flags",
)


@dataclass(frozen=True)
class RoleUsageValidationResult:
    source_file: str
    status: str
    summary: dict[str, object]
    flags: tuple[dict[str, object], ...]


def validate_truth_set_role_usage_export(
    source_path: str | Path,
    *,
    expected_players: tuple[str, ...] = (),
) -> RoleUsageValidationResult:
    path = Path(source_path)
    source_file = str(path)
    with path.open(newline="", encoding="utf-8") as handle:
        parsed_rows = list(csv.reader(handle))
    leading_blank_flags: list[dict[str, object]] = []
    while parsed_rows and all(not str(cell).strip() for cell in parsed_rows[0]):
        leading_blank_flags.append(
            _flag(
                source_file,
                1,
                "",
                "leading_blank_row",
                "blocking",
                "",
                "",
                "Strict role/usage exports must not contain blank rows before the header.",
            )
        )
        parsed_rows = parsed_rows[1:]
    if not parsed_rows:
        flags = (
            _flag(
                source_file,
                0,
                "",
                "empty_file",
                "blocking",
                "",
                "",
                "Role/usage export is empty.",
            ),
        )
        return _result(source_file, [], [], expected_players, flags)

    header = tuple(parsed_rows[0])
    data_rows = parsed_rows[1:]
    flags: list[dict[str, object]] = list(leading_blank_flags)
    if header != TRUTH_SET_ROLE_USAGE_STRICT_HEADER:
        flags.append(
            _flag(
                source_file,
                1,
                "",
                "header_mismatch",
                "blocking",
                "header",
                "|".join(header),
                "Header must exactly match the strict role/usage schema.",
            )
        )

    for row_number, raw_row in enumerate(data_rows, start=2):
        player_name = raw_row[0] if raw_row else ""
        if len(raw_row) != len(TRUTH_SET_ROLE_USAGE_STRICT_HEADER):
            flags.append(
                _flag(
                    source_file,
                    row_number,
                    player_name,
                    "malformed_row_width",
                    "blocking",
                    "",
                    str(len(raw_row)),
                    (
                        f"Row has {len(raw_row)} columns; expected "
                        f"{len(TRUTH_SET_ROLE_USAGE_STRICT_HEADER)}."
                    ),
                )
            )
        row = _row_dict(raw_row)
        _extend_numeric_flags(source_file, row_number, player_name, row, flags)
        _extend_source_separation_flags(source_file, row_number, player_name, row, flags)

    _extend_player_coverage_flags(source_file, data_rows, expected_players, flags)
    return _result(source_file, header, data_rows, expected_players, tuple(flags))


def write_role_usage_validation_flags(
    output_path: str | Path,
    flags: tuple[dict[str, object], ...],
) -> None:
    _write_dicts(output_path, ROLE_USAGE_FLAG_HEADER, flags)


def write_role_usage_validation_summary(
    output_path: str | Path,
    summaries: tuple[dict[str, object], ...],
) -> None:
    _write_dicts(output_path, ROLE_USAGE_SUMMARY_HEADER, summaries)


def write_role_usage_validation_summary_json(
    output_path: str | Path,
    summaries: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(summaries), indent=2) + "\n", encoding="utf-8")


def _result(
    source_file: str,
    header: tuple[str, ...] | list[str],
    data_rows: list[list[str]],
    expected_players: tuple[str, ...],
    flags: tuple[dict[str, object], ...],
) -> RoleUsageValidationResult:
    blocking_flags = sum(flag["severity"] == "blocking" for flag in flags)
    review_flags = sum(flag["severity"] == "review" for flag in flags)
    player_keys = [_player_key(row[0]) for row in data_rows if row]
    expected_by_key = {_player_key(player): _normalize_name(player) for player in expected_players}
    missing_players = sorted(
        name for key, name in expected_by_key.items() if key not in set(player_keys)
    )
    duplicate_players = sorted(
        key for key in set(player_keys) if player_keys.count(key) > 1
    )
    summary = {
        "source_file": source_file,
        "status": "rejected" if blocking_flags else "valid_preview_ready",
        "header_status": (
            "exact" if tuple(header) == TRUTH_SET_ROLE_USAGE_STRICT_HEADER else "mismatch"
        ),
        "rows": len(data_rows),
        "expected_players": len(expected_players),
        "unique_players": len(set(player_keys)),
        "missing_players": "|".join(missing_players),
        "duplicate_players": "|".join(duplicate_players),
        "malformed_width_rows": _row_count_for_flags(flags, "malformed_row_width"),
        "numeric_error_rows": _row_count_for_flags(flags, "non_numeric_value"),
        "uncertain_marker_rows": _row_count_for_flags(flags, "uncertain_numeric_marker"),
        "prose_numeric_rows": _row_count_for_flags(flags, "prose_in_numeric_field"),
        "embedded_url_rows": _row_count_for_flags(flags, "embedded_url_in_numeric_field"),
        "source_separation_rows": _row_count_for_flags(flags, "source_field_not_separated"),
        "blocking_flags": blocking_flags,
        "review_flags": review_flags,
    }
    return RoleUsageValidationResult(
        source_file=source_file,
        status=str(summary["status"]),
        summary=summary,
        flags=flags,
    )


def _extend_numeric_flags(
    source_file: str,
    row_number: int,
    player_name: str,
    row: dict[str, str],
    flags: list[dict[str, object]],
) -> None:
    for column in ROLE_USAGE_NUMERIC_COLUMNS:
        value = str(row.get(column) or "").strip()
        if not value:
            continue
        if "?" in value:
            flags.append(
                _flag(
                    source_file,
                    row_number,
                    player_name,
                    "uncertain_numeric_marker",
                    "blocking",
                    column,
                    value,
                    "Numeric fields must be numeric or blank; use notes for uncertainty.",
                )
            )
            continue
        if _contains_url(value):
            flags.append(
                _flag(
                    source_file,
                    row_number,
                    player_name,
                    "embedded_url_in_numeric_field",
                    "blocking",
                    column,
                    value,
                    "Numeric/stat fields cannot contain source URLs or snippets.",
                )
            )
            continue
        if _looks_like_prose(value):
            flags.append(
                _flag(
                    source_file,
                    row_number,
                    player_name,
                    "prose_in_numeric_field",
                    "blocking",
                    column,
                    value,
                    "Role/workload numeric fields cannot contain prose.",
                )
            )
            continue
        if _to_float(_strip_percent(value)) is None:
            flags.append(
                _flag(
                    source_file,
                    row_number,
                    player_name,
                    "non_numeric_value",
                    "blocking",
                    column,
                    value,
                    "Numeric fields must be numeric, percent-formatted, or blank.",
                )
            )


def _extend_source_separation_flags(
    source_file: str,
    row_number: int,
    player_name: str,
    row: dict[str, str],
    flags: list[dict[str, object]],
) -> None:
    source_name = str(row.get("source_name") or "")
    source_url = str(row.get("source_url") or "")
    if _contains_url(source_name):
        flags.append(
            _flag(
                source_file,
                row_number,
                player_name,
                "source_field_not_separated",
                "blocking",
                "source_name",
                source_name,
                "source_name must not contain URLs; put URLs in source_url only.",
            )
        )
    if source_url and not _contains_url(source_url):
        flags.append(
            _flag(
                source_file,
                row_number,
                player_name,
                "source_field_not_separated",
                "blocking",
                "source_url",
                source_url,
                "source_url must contain the URL when a source URL is provided.",
            )
        )


def _extend_player_coverage_flags(
    source_file: str,
    data_rows: list[list[str]],
    expected_players: tuple[str, ...],
    flags: list[dict[str, object]],
) -> None:
    if not expected_players:
        return
    player_keys = [_player_key(row[0]) for row in data_rows if row]
    expected_by_key = {_player_key(player): _normalize_name(player) for player in expected_players}
    for key, player in sorted(expected_by_key.items(), key=lambda item: item[1]):
        if key in set(player_keys):
            continue
        flags.append(
            _flag(
                source_file,
                0,
                player,
                "missing_expected_player",
                "blocking",
                "player_name",
                "",
                "Strict role/usage export must include one row per truth-set player.",
            )
        )
    for player in sorted(set(player_keys)):
        if player_keys.count(player) > 1:
            flags.append(
                _flag(
                    source_file,
                    0,
                    player,
                    "duplicate_player_row",
                    "blocking",
                    "player_name",
                    player,
                    "Strict role/usage export must have one row per player.",
                )
            )


def _row_dict(raw_row: list[str]) -> dict[str, str]:
    return {
        column: raw_row[index] if index < len(raw_row) else ""
        for index, column in enumerate(TRUTH_SET_ROLE_USAGE_STRICT_HEADER)
    }


def _flag(
    source_file: str,
    row_number: int,
    player_name: str,
    flag: str,
    severity: str,
    column: str,
    value: str,
    detail: str,
) -> dict[str, object]:
    return {
        "source_file": source_file,
        "row_number": row_number,
        "player_name": _normalize_name(player_name),
        "flag": flag,
        "severity": severity,
        "column": column,
        "value": value,
        "detail": detail,
    }


def _row_count_for_flags(flags: tuple[dict[str, object], ...], flag_name: str) -> int:
    return len({flag["row_number"] for flag in flags if flag["flag"] == flag_name})


def _contains_url(value: str) -> bool:
    text = value.lower()
    return "http://" in text or "https://" in text or "www." in text


def _looks_like_prose(value: str) -> bool:
    return any(char.isalpha() for char in value.replace("e", "").replace("E", ""))


def _strip_percent(value: str) -> str:
    return value[:-1] if value.endswith("%") else value


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _normalize_name(value: object) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").strip().split())


def _player_key(value: object) -> str:
    normalized = _normalize_name(value)
    for suffix in (" III", " II", " IV", " Jr.", " Jr"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
    return "".join(char.lower() for char in normalized if char.isalnum())


def _write_dicts(
    output_path: str | Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
