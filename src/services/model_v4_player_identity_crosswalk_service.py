from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SOURCE_ROOT = Path("local_exports/model_v4/prospect_sources/latest/files")
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/player_identity/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_10E_PLAYER_IDENTITY_CROSSWALK.md")

SUPPORTED_POSITIONS = {"QB", "RB", "WR", "TE"}
UNKNOWN_POSITION = "UNK"

EXPLICIT_NAME_ALIASES = {
    "kcconcepcion": "kevinconcepcion",
    "nicksingleton": "nicholassingleton",
}

POSITION_ALIASES = {
    "QB": "QB",
    "QUARTERBACK": "QB",
    "RB": "RB",
    "RUNNINGBACK": "RB",
    "RUNNING BACK": "RB",
    "WR": "WR",
    "WIDERECEIVER": "WR",
    "WIDE RECEIVER": "WR",
    "TE": "TE",
    "TIGHTEND": "TE",
    "TIGHT END": "TE",
}

IDENTITY_CROSSWALK_HEADER = (
    "canonical_player_key",
    "canonical_player_name",
    "normalized_player_name",
    "source_specific_names",
    "alias_names",
    "primary_position",
    "positions",
    "nfl_teams",
    "colleges",
    "draft_years",
    "player_urls",
    "sleeper_ids",
    "gsis_ids",
    "nfl_ids",
    "cfbd_player_ids",
    "rotowire_player_ids",
    "espn_ids",
    "nfl_person_ids",
    "source_groups",
    "source_files",
    "source_count",
    "join_status",
    "warning_flags",
)

IDENTITY_REPORT_HEADER = IDENTITY_CROSSWALK_HEADER + ("report_reason",)
IDENTITY_SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class SourceIdentityRecord:
    source_group: str
    source_name: str
    source_path: str
    source_player_name: str
    position: str = ""
    team: str = ""
    college: str = ""
    draft_year: str = ""
    player_url: str = ""
    sleeper_id: str = ""
    gsis_id: str = ""
    nfl_id: str = ""
    cfbd_player_id: str = ""
    rotowire_player_id: str = ""
    espn_id: str = ""
    nfl_person_id: str = ""
    source_specific_id: str = ""

    @property
    def normalized_name(self) -> str:
        return normalize_identity_name(self.source_player_name)


@dataclass(frozen=True)
class PlayerIdentityCrosswalkResult:
    crosswalk_rows: tuple[dict[str, object], ...]
    unresolved_rows: tuple[dict[str, object], ...]
    ambiguous_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_player_identity_crosswalk(
    *,
    source_root: str | Path = DEFAULT_SOURCE_ROOT,
    records: tuple[SourceIdentityRecord, ...] | None = None,
) -> PlayerIdentityCrosswalkResult:
    source_records = (
        records if records is not None else collect_source_identity_records(source_root)
    )
    source_records = tuple(record for record in source_records if record.normalized_name)
    grouped_records = _group_records(source_records)
    duplicate_name_keys = _duplicate_name_keys(grouped_records)

    crosswalk_rows = tuple(
        _build_crosswalk_row(key, rows, duplicate_name_keys)
        for key, rows in sorted(grouped_records.items())
    )
    unresolved_rows = tuple(
        {**row, "report_reason": _report_reason(row)}
        for row in crosswalk_rows
        if row["join_status"] == "unresolved"
    )
    ambiguous_rows = tuple(
        {**row, "report_reason": _report_reason(row)}
        for row in crosswalk_rows
        if row["join_status"] == "ambiguous"
    )
    return PlayerIdentityCrosswalkResult(
        crosswalk_rows=crosswalk_rows,
        unresolved_rows=unresolved_rows,
        ambiguous_rows=ambiguous_rows,
        summary=_summary(source_records, crosswalk_rows, unresolved_rows, ambiguous_rows),
    )


def collect_source_identity_records(
    source_root: str | Path = DEFAULT_SOURCE_ROOT,
) -> tuple[SourceIdentityRecord, ...]:
    root = Path(source_root)
    data_root = root / "source_project" / "data"
    kaggle_root = root / "kaggle_nfl_draft" / "extracted"
    records: list[SourceIdentityRecord] = []

    records.extend(_cfbd_records(data_root / "college_football_data" / "processed"))
    records.extend(_rotowire_records(data_root / "rotowire" / "processed"))
    records.extend(_fantasypros_records(data_root / "fantasypros" / "processed"))
    records.extend(_market_records(data_root / "market" / "processed"))
    records.extend(_kaggle_records(kaggle_root))
    records.extend(_third_party_records(data_root / "third_party" / "nfl_draft_data" / "processed"))

    deduped: dict[tuple[object, ...], SourceIdentityRecord] = {}
    for record in records:
        if not record.source_player_name.strip():
            continue
        key = (
            record.source_group,
            record.source_path,
            record.source_player_name,
            record.position,
            record.team,
            record.college,
            record.draft_year,
            record.player_url,
            record.sleeper_id,
            record.gsis_id,
            record.nfl_id,
            record.cfbd_player_id,
            record.rotowire_player_id,
            record.espn_id,
            record.nfl_person_id,
        )
        deduped[key] = record
    return tuple(deduped.values())


def write_player_identity_crosswalk_outputs(
    output_root: str | Path,
    result: PlayerIdentityCrosswalkResult,
    *,
    doc_path: str | Path = DEFAULT_DOC_PATH,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "crosswalk": root / "canonical_player_identity_crosswalk.csv",
        "unresolved": root / "unresolved_identity_report.csv",
        "ambiguous": root / "ambiguous_identity_report.csv",
        "summary_csv": root / "player_identity_crosswalk_summary.csv",
        "summary_json": root / "player_identity_crosswalk_summary.json",
        "doc": Path(doc_path),
    }
    _write_csv(paths["crosswalk"], IDENTITY_CROSSWALK_HEADER, result.crosswalk_rows)
    _write_csv(paths["unresolved"], IDENTITY_REPORT_HEADER, result.unresolved_rows)
    _write_csv(paths["ambiguous"], IDENTITY_REPORT_HEADER, result.ambiguous_rows)
    _write_csv(
        paths["summary_csv"],
        IDENTITY_SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    paths["summary_json"].write_text(
        json.dumps(result.summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _write_phase_doc(paths["doc"], result, paths)
    return paths


def normalize_identity_name(value: object) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("&", " and ")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", text, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "", text).lower()
    return EXPLICIT_NAME_ALIASES.get(normalized, normalized)


def normalize_raw_name_without_alias(value: object) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("&", " and ")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"[^a-zA-Z0-9]+", "", text).lower()


def _cfbd_records(processed_root: Path) -> list[SourceIdentityRecord]:
    records: list[SourceIdentityRecord] = []
    for filename in (
        "college_player_seasons_wide.csv",
        "college_market_share.csv",
        "college_player_category_summary.csv",
    ):
        path = processed_root / filename
        for row in _read_rows_if_exists(path):
            records.append(
                SourceIdentityRecord(
                    source_group="cfbd",
                    source_name=filename,
                    source_path=_path_text(path),
                    source_player_name=_clean(row.get("player")),
                    college=_clean(row.get("team") or row.get("final_team")),
                    cfbd_player_id=_clean(row.get("player_id")),
                )
            )

    for row in _read_rows_if_exists(processed_root / "roster.csv"):
        records.append(
            SourceIdentityRecord(
                source_group="cfbd",
                source_name="roster.csv",
                source_path=_path_text(processed_root / "roster.csv"),
                source_player_name=_clean(f"{row.get('firstName', '')} {row.get('lastName', '')}"),
                position=_position(row.get("position")),
                college=_clean(row.get("team")),
                cfbd_player_id=_clean(row.get("id")),
            )
        )

    for row in _read_rows_if_exists(processed_root / "recruiting_players.csv"):
        records.append(
            SourceIdentityRecord(
                source_group="cfbd",
                source_name="recruiting_players.csv",
                source_path=_path_text(processed_root / "recruiting_players.csv"),
                source_player_name=_clean(row.get("name")),
                position=_position(row.get("position")),
                college=_clean(row.get("committedTo") or row.get("school")),
                cfbd_player_id=_clean(row.get("athleteId")),
                source_specific_id=_clean(row.get("id")),
            )
        )

    for row in _read_rows_if_exists(processed_root / "draft_picks.csv"):
        records.append(
            SourceIdentityRecord(
                source_group="cfbd",
                source_name="draft_picks.csv",
                source_path=_path_text(processed_root / "draft_picks.csv"),
                source_player_name=_clean(row.get("name")),
                position=_position(row.get("position")),
                team=_clean(row.get("nflTeam")),
                college=_clean(row.get("collegeTeam")),
                draft_year=_clean(row.get("year")),
                cfbd_player_id=_clean(row.get("collegeAthleteId")),
                espn_id=_clean(row.get("nflAthleteId")),
            )
        )
    return records


def _rotowire_records(processed_root: Path) -> list[SourceIdentityRecord]:
    records: list[SourceIdentityRecord] = []
    source_specs = (
        (
            "rotowire_cfb_stats_all.csv",
            "player",
            "position",
            "",
            "team",
            "",
            "player_id",
        ),
        (
            "rotowire_cfb_targets_all.csv",
            "player",
            "position",
            "",
            "team",
            "",
            "",
        ),
        (
            "rotowire_workout_stats.csv",
            "player",
            "position",
            "team",
            "",
            "draft_year",
            "",
        ),
        (
            "rotowire_upcoming_depth_charts.csv",
            "player",
            "position",
            "team",
            "",
            "",
            "",
        ),
        (
            "rotowire_rookie_rankings_2026.csv",
            "player",
            "position",
            "nfl_team",
            "",
            "",
            "",
        ),
        (
            "rotowire_cfb_injury_report_2026.csv",
            "player",
            "position",
            "",
            "team",
            "",
            "",
        ),
        (
            "rotowire_nfl_injury_report.csv",
            "player",
            "position",
            "team",
            "",
            "",
            "",
        ),
    )
    for filename, name_col, pos_col, team_col, college_col, draft_col, id_col in source_specs:
        path = processed_root / filename
        for row in _read_rows_if_exists(path):
            records.append(
                SourceIdentityRecord(
                    source_group="rotowire",
                    source_name=filename,
                    source_path=_path_text(path),
                    source_player_name=_clean(row.get(name_col)),
                    position=_position(row.get(pos_col)),
                    team=_clean(row.get(team_col)),
                    college=_clean(row.get(college_col)),
                    draft_year=_clean(row.get(draft_col)),
                    rotowire_player_id=_clean(row.get(id_col)),
                )
            )
    return records


def _fantasypros_records(processed_root: Path) -> list[SourceIdentityRecord]:
    path = processed_root / "fantasypros_overall_adp_2026.csv"
    return [
        SourceIdentityRecord(
            source_group="fantasypros",
            source_name="fantasypros_overall_adp_2026.csv",
            source_path=_path_text(path),
            source_player_name=_clean(row.get("player")),
            position=_position(row.get("position")),
            team=_clean(row.get("team")),
            draft_year=_clean(row.get("season")),
        )
        for row in _read_rows_if_exists(path)
    ]


def _market_records(processed_root: Path) -> list[SourceIdentityRecord]:
    path = processed_root / "rookie_adp_2026_04_23_to_2026_05_17.csv"
    return [
        SourceIdentityRecord(
            source_group="market",
            source_name="rookie_adp_2026_04_23_to_2026_05_17.csv",
            source_path=_path_text(path),
            source_player_name=_clean(row.get("player")),
            position=_position(row.get("position")),
            draft_year=_clean(row.get("draft_year")),
            sleeper_id=_clean(row.get("sleeper_id")),
        )
        for row in _read_rows_if_exists(path)
    ]


def _kaggle_records(extracted_root: Path) -> list[SourceIdentityRecord]:
    records: list[SourceIdentityRecord] = []
    for filename in (
        "consensus_big_board_latest_2026.csv",
        "consensus_big_board.csv",
        "big_board_picks.csv",
        "first_round_picks.csv",
        "team_picks.csv",
        "draft_results.csv",
    ):
        path = extracted_root / filename
        for row in _read_rows_if_exists(path):
            records.append(
                SourceIdentityRecord(
                    source_group="kaggle_nfl_draft",
                    source_name=filename,
                    source_path=_path_text(path),
                    source_player_name=_clean(row.get("player_name")),
                    position=_position(row.get("position")),
                    team=_clean(row.get("team")),
                    college=_clean(row.get("college")),
                    draft_year=_clean(row.get("draft_year")),
                    player_url=_clean(row.get("player_url")),
                )
            )

    path = extracted_root / "players_nflverse.csv"
    for row in _read_rows_if_exists(path):
        records.append(
            SourceIdentityRecord(
                source_group="nflverse",
                source_name="players_nflverse.csv",
                source_path=_path_text(path),
                source_player_name=_clean(row.get("display_name")),
                position=_position(row.get("position")),
                team=_clean(row.get("latest_team")),
                college=_clean(row.get("college_name")),
                draft_year=_clean(row.get("draft_year") or row.get("rookie_season")),
                gsis_id=_clean(row.get("gsis_id")),
                nfl_id=_clean(row.get("nfl_id")),
                source_specific_id=_clean(row.get("pfr_id") or row.get("pff_id")),
            )
        )
    return records


def _third_party_records(processed_root: Path) -> list[SourceIdentityRecord]:
    records: list[SourceIdentityRecord] = []
    for filename in (
        "combine_skill_positions_all.csv",
        "combine_pro_day.csv",
        "combine_official.csv",
    ):
        path = processed_root / filename
        for row in _read_rows_if_exists(path):
            records.append(
                SourceIdentityRecord(
                    source_group="third_party_combine",
                    source_name=filename,
                    source_path=_path_text(path),
                    source_player_name=_clean(row.get("player")),
                    position=_position(row.get("position")),
                    college=_clean(row.get("college")),
                    draft_year=_clean(row.get("year")),
                    espn_id=_clean(row.get("espn_athlete_id")),
                    nfl_person_id=_clean(row.get("nfl_person_id")),
                )
            )
    return records


def _group_records(
    records: tuple[SourceIdentityRecord, ...],
) -> dict[tuple[str, str], tuple[SourceIdentityRecord, ...]]:
    by_name: dict[str, list[SourceIdentityRecord]] = defaultdict(list)
    for record in records:
        by_name[record.normalized_name].append(record)

    groups: dict[tuple[str, str], list[SourceIdentityRecord]] = defaultdict(list)
    for normalized_name, rows in by_name.items():
        known_positions = sorted({row.position for row in rows if row.position})
        for row in rows:
            position = row.position
            if not position:
                position = known_positions[0] if len(known_positions) == 1 else UNKNOWN_POSITION
            groups[(normalized_name, position)].append(row)
    return {key: tuple(value) for key, value in groups.items()}


def _duplicate_name_keys(
    grouped_records: dict[tuple[str, str], tuple[SourceIdentityRecord, ...]],
) -> set[tuple[str, str]]:
    name_counts: Counter[str] = Counter(name for name, _position_key in grouped_records)
    return {key for key in grouped_records if name_counts[key[0]] > 1}


def _build_crosswalk_row(
    key: tuple[str, str],
    records: tuple[SourceIdentityRecord, ...],
    duplicate_name_keys: set[tuple[str, str]],
) -> dict[str, object]:
    normalized_name, position_key = key
    names = _unique_sorted(record.source_player_name for record in records)
    raw_normalized_names = _unique_sorted(
        normalize_raw_name_without_alias(record.source_player_name) for record in records
    )
    positions = _unique_sorted(record.position for record in records if record.position)
    nfl_teams = _unique_sorted(record.team for record in records if record.team)
    colleges = _unique_sorted(record.college for record in records if record.college)
    draft_years = _unique_sorted(record.draft_year for record in records if record.draft_year)
    player_urls = _unique_sorted(record.player_url for record in records if record.player_url)
    sleeper_ids = _unique_sorted(record.sleeper_id for record in records if record.sleeper_id)
    gsis_ids = _unique_sorted(record.gsis_id for record in records if record.gsis_id)
    nfl_ids = _unique_sorted(record.nfl_id for record in records if record.nfl_id)
    cfbd_ids = _unique_sorted(record.cfbd_player_id for record in records if record.cfbd_player_id)
    rotowire_ids = _unique_sorted(
        record.rotowire_player_id for record in records if record.rotowire_player_id
    )
    espn_ids = _unique_sorted(record.espn_id for record in records if record.espn_id)
    nfl_person_ids = _unique_sorted(
        record.nfl_person_id for record in records if record.nfl_person_id
    )
    source_groups = _unique_sorted(record.source_group for record in records)
    source_files = _unique_sorted(record.source_path for record in records)

    warning_flags = _warning_flags(
        key=key,
        raw_normalized_names=raw_normalized_names,
        positions=positions,
        nfl_teams=nfl_teams,
        colleges=colleges,
        player_urls=player_urls,
        sleeper_ids=sleeper_ids,
        gsis_ids=gsis_ids,
        nfl_ids=nfl_ids,
        cfbd_ids=cfbd_ids,
        rotowire_ids=rotowire_ids,
        espn_ids=espn_ids,
        nfl_person_ids=nfl_person_ids,
        duplicate_name_keys=duplicate_name_keys,
    )
    join_status = _join_status(warning_flags)
    primary_position = (
        positions[0]
        if len(positions) == 1
        else ("" if not positions else position_key)
    )
    return {
        "canonical_player_key": f"name:{normalized_name}:{position_key}",
        "canonical_player_name": _canonical_name(names),
        "normalized_player_name": normalized_name,
        "source_specific_names": "|".join(names),
        "alias_names": "|".join(raw_normalized_names),
        "primary_position": primary_position,
        "positions": "|".join(positions),
        "nfl_teams": "|".join(nfl_teams),
        "colleges": "|".join(colleges),
        "draft_years": "|".join(draft_years),
        "player_urls": "|".join(player_urls),
        "sleeper_ids": "|".join(sleeper_ids),
        "gsis_ids": "|".join(gsis_ids),
        "nfl_ids": "|".join(nfl_ids),
        "cfbd_player_ids": "|".join(cfbd_ids),
        "rotowire_player_ids": "|".join(rotowire_ids),
        "espn_ids": "|".join(espn_ids),
        "nfl_person_ids": "|".join(nfl_person_ids),
        "source_groups": "|".join(source_groups),
        "source_files": "|".join(source_files),
        "source_count": len(records),
        "join_status": join_status,
        "warning_flags": "|".join(warning_flags),
    }


def _warning_flags(
    *,
    key: tuple[str, str],
    raw_normalized_names: tuple[str, ...],
    positions: tuple[str, ...],
    nfl_teams: tuple[str, ...],
    colleges: tuple[str, ...],
    player_urls: tuple[str, ...],
    sleeper_ids: tuple[str, ...],
    gsis_ids: tuple[str, ...],
    nfl_ids: tuple[str, ...],
    cfbd_ids: tuple[str, ...],
    rotowire_ids: tuple[str, ...],
    espn_ids: tuple[str, ...],
    nfl_person_ids: tuple[str, ...],
    duplicate_name_keys: set[tuple[str, str]],
) -> tuple[str, ...]:
    flags: list[str] = []
    stable_id_sets = (
        sleeper_ids,
        gsis_ids,
        nfl_ids,
        cfbd_ids,
        rotowire_ids,
        espn_ids,
        nfl_person_ids,
        player_urls,
    )
    if not any(stable_id_sets):
        flags.append("missing_all_stable_ids")
    if not positions:
        flags.append("missing_position")
    if key in duplicate_name_keys:
        flags.append("duplicate_normalized_name")
    if len(positions) > 1:
        flags.append("conflicting_positions")
    if len(nfl_teams) > 1:
        flags.append("conflicting_nfl_teams_or_team_history")
    if len(colleges) > 1:
        flags.append("conflicting_colleges_or_transfer_history")
    if len(raw_normalized_names) > 1:
        flags.append("explicit_alias_applied")
    for label, values in (
        ("multiple_sleeper_ids", sleeper_ids),
        ("multiple_gsis_ids", gsis_ids),
        ("multiple_nfl_ids", nfl_ids),
        ("multiple_cfbd_player_ids", cfbd_ids),
        ("multiple_rotowire_player_ids", rotowire_ids),
        ("multiple_espn_ids", espn_ids),
        ("multiple_nfl_person_ids", nfl_person_ids),
        ("multiple_player_urls", player_urls),
    ):
        if len(values) > 1:
            flags.append(label)
    return tuple(sorted(set(flags)))


def _join_status(warning_flags: tuple[str, ...]) -> str:
    ambiguous_flags = {
        "duplicate_normalized_name",
        "conflicting_positions",
        "multiple_sleeper_ids",
        "multiple_gsis_ids",
        "multiple_nfl_ids",
        "multiple_cfbd_player_ids",
        "multiple_rotowire_player_ids",
    }
    if any(flag in ambiguous_flags for flag in warning_flags):
        return "ambiguous"
    if "missing_all_stable_ids" in warning_flags or "missing_position" in warning_flags:
        return "unresolved"
    if warning_flags:
        return "review"
    return "ready"


def _report_reason(row: dict[str, object]) -> str:
    warning_flags = str(row.get("warning_flags") or "")
    return warning_flags or str(row.get("join_status") or "")


def _summary(
    records: tuple[SourceIdentityRecord, ...],
    crosswalk_rows: tuple[dict[str, object], ...],
    unresolved_rows: tuple[dict[str, object], ...],
    ambiguous_rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    status_counts: Counter[str] = Counter(str(row["join_status"]) for row in crosswalk_rows)
    source_counts: Counter[str] = Counter(record.source_group for record in records)
    warning_counts: Counter[str] = Counter()
    for row in crosswalk_rows:
        for flag in str(row.get("warning_flags") or "").split("|"):
            if flag:
                warning_counts[flag] += 1
    return {
        "status": "ready_for_review",
        "review_status": "review_only",
        "source_records": len(records),
        "canonical_rows": len(crosswalk_rows),
        "unresolved_rows": len(unresolved_rows),
        "ambiguous_rows": len(ambiguous_rows),
        "join_status_counts": json.dumps(dict(sorted(status_counts.items())), sort_keys=True),
        "source_group_counts": json.dumps(dict(sorted(source_counts.items())), sort_keys=True),
        "warning_counts": json.dumps(dict(sorted(warning_counts.items())), sort_keys=True),
        "fuzzy_joining_used": False,
        "formula_scores_changed": False,
        "active_rankings_changed": False,
        "readiness_gates_unlocked": False,
    }


def _write_phase_doc(
    doc_path: Path,
    result: PlayerIdentityCrosswalkResult,
    paths: dict[str, Path],
) -> None:
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 10E Player Identity Crosswalk",
        "",
        "## Summary",
        "",
        "Phase 10E builds a review-only identity crosswalk from exact normalized names, "
        "explicit aliases, source IDs, team/college context, draft year, and player URLs "
        "where available. It does not score players and does not promote any app rankings.",
        "",
        "## Outputs",
        "",
        f"- Crosswalk: `{paths['crosswalk']}`",
        f"- Unresolved report: `{paths['unresolved']}`",
        f"- Ambiguous report: `{paths['ambiguous']}`",
        f"- Summary JSON: `{paths['summary_json']}`",
        "",
        "## Counts",
        "",
        f"- Source records: {result.summary['source_records']}",
        f"- Canonical rows: {result.summary['canonical_rows']}",
        f"- Unresolved rows: {result.summary['unresolved_rows']}",
        f"- Ambiguous rows: {result.summary['ambiguous_rows']}",
        "",
        "## Guardrails",
        "",
        "- No fuzzy joins were used.",
        "- Suffixes Jr., Sr., II, III, and IV are stripped for normalized matching while "
        "source names are preserved.",
        "- `KC Concepcion` to `Kevin Concepcion` is the only explicit alias currently applied.",
        "- Duplicate normalized names, conflicting positions, conflicting team/college "
        "histories, and multiple IDs are flagged for review.",
        "- Missing IDs remain visible in the unresolved report instead of being silently accepted.",
        "",
    ]
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def _canonical_name(names: tuple[str, ...]) -> str:
    if not names:
        return ""
    counts = Counter(names)
    return sorted(names, key=lambda name: (counts[name], len(name), name))[-1]


def _position(value: object) -> str:
    raw = _clean(value)
    if not raw:
        return ""
    compact = re.sub(r"[^A-Za-z]+", "", raw).upper()
    return POSITION_ALIASES.get(raw.upper(), POSITION_ALIASES.get(compact, raw.upper()))


def _clean(value: object) -> str:
    return str(value or "").strip()


def _path_text(path: Path) -> str:
    return str(path).replace("\\", "/")


def _unique_sorted(values: object) -> tuple[str, ...]:
    return tuple(sorted({str(value).strip() for value in values if str(value).strip()}))


def _read_rows_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
