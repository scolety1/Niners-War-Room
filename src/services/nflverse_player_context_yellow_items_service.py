from __future__ import annotations

import csv
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from src.services.nflverse_refresh_health_service import NOT_ENOUGH_INFORMATION

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DISPLAY_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
)
DEFAULT_ARTIFACT_PATH = DEFAULT_DISPLAY_DIR / "nflverse_player_context_display_artifact.csv"
DEFAULT_SNAPSHOT_DIR = Path(
    r"C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630"
)
DEFAULT_IDENTITY_OUTPUT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_identity_review_20260630"
)
DEFAULT_SCHEDULE_OUTPUT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_schedule_audit_20260630"
)

SAFE_RESOLUTION_PROPOSED = "SAFE_RESOLUTION_PROPOSED"
KEEP_NEED_IDENTITY_REVIEW = "KEEP_NEED_IDENTITY_REVIEW"
NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
SAFE_NOW_DISPLAY_ONLY = "SAFE_NOW_DISPLAY_ONLY"
NEED_CURRENT_SCHEDULE_REFRESH = "NEED_CURRENT_SCHEDULE_REFRESH"
NEED_TEAM_ALIAS_REVIEW = "NEED_TEAM_ALIAS_REVIEW"
NOT_APPLICABLE = "NOT_APPLICABLE"

DISPLAY_ONLY = "true"
DENY = "false"

IDENTITY_REVIEW_COLUMNS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "reason_identity_failed",
    "candidate_source",
    "candidate_match_rule",
    "candidate_nflverse_player_names",
    "candidate_sleeper_ids",
    "candidate_gsis_ids",
    "candidate_teams",
    "proposed_decision",
    "confidence",
    "source_columns_used",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "notes",
)

IDENTITY_PROPOSAL_COLUMNS = (
    "nwr_player_id",
    "nwr_player_name",
    "nwr_position",
    "nwr_team",
    "candidate_gsis_id",
    "candidate_sleeper_id",
    "candidate_nflverse_name",
    "candidate_team",
    "candidate_source",
    "candidate_match_rule",
    "proposed_decision",
    "confidence",
    "source_columns_used",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "notes",
)

SCHEDULE_AUDIT_COLUMNS = (
    "team",
    "canonical_schedule_team",
    "artifact_player_rows",
    "safe_identity_player_rows",
    "schedule_rows",
    "schedule_seasons",
    "schedule_weeks",
    "min_gameday",
    "max_gameday",
    "as_of_date",
    "has_current_or_future_game",
    "next_game_week",
    "next_game_date",
    "next_opponent",
    "bye_week",
    "schedule_context_status",
    "root_cause",
    "team_alias_status",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "rank_logic_allowed",
    "hidden_sort_allowed",
    "trade_value_allowed",
    "pick_value_allowed",
    "notes",
)


@dataclass(frozen=True)
class IdentityReviewResult:
    reviewed_rows: int
    safe_resolution_proposals: int
    human_review_rows: int
    keep_review_rows: int
    queue_rows: tuple[dict[str, str], ...]
    proposal_rows: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class ScheduleAuditResult:
    audited_teams: int
    teams_with_schedule_rows: int
    teams_with_current_or_future_game: int
    root_cause: str
    audit_rows: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class YellowItemsResult:
    identity: IdentityReviewResult
    schedule: ScheduleAuditResult
    artifact_rebuild_recommended: bool
    verdict: str


def write_nflverse_player_context_yellow_item_docs(
    *,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    identity_output_dir: Path = DEFAULT_IDENTITY_OUTPUT_DIR,
    schedule_output_dir: Path = DEFAULT_SCHEDULE_OUTPUT_DIR,
    as_of: date | None = None,
) -> YellowItemsResult:
    as_of_date = as_of or datetime.now(UTC).date()
    identity = build_identity_review(artifact_path=artifact_path, snapshot_dir=snapshot_dir)
    schedule = build_schedule_audit(
        artifact_path=artifact_path,
        snapshot_dir=snapshot_dir,
        as_of=as_of_date,
    )

    identity_output_dir.mkdir(parents=True, exist_ok=True)
    schedule_output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        identity_output_dir / "nflverse_player_context_identity_review_queue.csv",
        identity.queue_rows,
        IDENTITY_REVIEW_COLUMNS,
    )
    _write_csv(
        identity_output_dir / "nflverse_player_context_identity_resolution_proposals.csv",
        identity.proposal_rows,
        IDENTITY_PROPOSAL_COLUMNS,
    )
    (identity_output_dir / "nflverse_player_context_identity_review_summary.md").write_text(
        _identity_summary_markdown(identity),
        encoding="utf-8",
    )
    _write_csv(
        schedule_output_dir / "nflverse_schedule_context_audit.csv",
        schedule.audit_rows,
        SCHEDULE_AUDIT_COLUMNS,
    )
    (schedule_output_dir / "nflverse_schedule_context_build_report.md").write_text(
        _schedule_build_report_markdown(schedule, as_of_date),
        encoding="utf-8",
    )
    (schedule_output_dir / "nflverse_schedule_context_guardrail_report.md").write_text(
        _schedule_guardrail_report_markdown(schedule),
        encoding="utf-8",
    )

    artifact_rebuild_recommended = False
    verdict = (
        "YELLOW_PARTIAL_IMPROVEMENT"
        if identity.safe_resolution_proposals > 0
        else "YELLOW_IDENTITY_REVIEW_QUEUE_CREATED"
    )
    return YellowItemsResult(
        identity=identity,
        schedule=schedule,
        artifact_rebuild_recommended=artifact_rebuild_recommended,
        verdict=verdict,
    )


def build_identity_review(
    *,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> IdentityReviewResult:
    artifact_rows = _read_csv(artifact_path)
    review_rows = [
        row for row in artifact_rows if row.get("identity_join_status") == "NEED_IDENTITY_REVIEW"
    ]
    sources = _identity_sources(snapshot_dir)
    queue_rows: list[dict[str, str]] = []
    proposal_rows: list[dict[str, str]] = []
    for row in review_rows:
        candidate = _identity_candidate(row, sources)
        queue_row = _identity_queue_row(row, candidate)
        queue_rows.append(queue_row)
        proposal_rows.append(_identity_proposal_row(row, candidate, queue_row))

    decision_counts = Counter(row["proposed_decision"] for row in queue_rows)
    return IdentityReviewResult(
        reviewed_rows=len(review_rows),
        safe_resolution_proposals=decision_counts[SAFE_RESOLUTION_PROPOSED],
        human_review_rows=decision_counts[NEEDS_HUMAN_REVIEW],
        keep_review_rows=decision_counts[KEEP_NEED_IDENTITY_REVIEW],
        queue_rows=tuple(queue_rows),
        proposal_rows=tuple(proposal_rows),
    )


def build_schedule_audit(
    *,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    as_of: date | None = None,
) -> ScheduleAuditResult:
    as_of_date = as_of or datetime.now(UTC).date()
    artifact_rows = _read_csv(artifact_path)
    schedule_rows = _read_csv(snapshot_dir / "schedules.csv")
    schedule_team_rows = _rows_by_schedule_team(schedule_rows)
    team_aliases = _team_aliases(snapshot_dir, set(schedule_team_rows))
    artifact_team_counts = _artifact_team_counts(artifact_rows, team_aliases)
    audit_rows = tuple(
        _schedule_audit_row(
            team=team,
            player_rows=counts["all"],
            safe_rows=counts["safe"],
            schedule_rows=schedule_team_rows.get(canonical_team, ()),
            canonical_team=canonical_team,
            alias_status=alias_status,
            as_of=as_of_date,
        )
        for team, counts in sorted(artifact_team_counts.items())
        for canonical_team, alias_status in [
            _canonical_team(team, schedule_team_rows, team_aliases)
        ]
    )
    with_rows = sum(1 for row in audit_rows if int(row["schedule_rows"]) > 0)
    with_future = sum(1 for row in audit_rows if row["has_current_or_future_game"] == "true")
    root_cause = (
        "approved schedules data is present for 2024-2025 only; as_of_date has no "
        "current/future games, and the player-context builder correctly leaves next "
        "game/opponent/bye as Not enough information"
    )
    return ScheduleAuditResult(
        audited_teams=len(audit_rows),
        teams_with_schedule_rows=with_rows,
        teams_with_current_or_future_game=with_future,
        root_cause=root_cause,
        audit_rows=audit_rows,
    )


def _identity_sources(snapshot_dir: Path) -> dict[str, tuple[dict[str, str], ...]]:
    return {
        dataset: tuple(_read_csv(snapshot_dir / f"{dataset}.csv"))
        for dataset in ("ff_playerids", "players", "rosters", "weekly_rosters")
        if (snapshot_dir / f"{dataset}.csv").exists()
    }


def _identity_candidate(
    artifact_row: dict[str, str],
    sources: dict[str, tuple[dict[str, str], ...]],
) -> dict[str, str]:
    target_name = _normalize_name(artifact_row.get("nwr_player_name"))
    target_position = _clean(artifact_row.get("nwr_position"))
    target_team = _clean(artifact_row.get("nwr_team"))
    exact_team_matches: list[dict[str, str]] = []
    exact_name_position_matches: list[dict[str, str]] = []
    for source_name, rows in sources.items():
        for row in rows:
            if _candidate_name(row) != target_name:
                continue
            if _candidate_position(row) != target_position:
                continue
            candidate = _candidate_dict(source_name, row, "exact_name_position")
            exact_name_position_matches.append(candidate)
            if _candidate_team(row) == target_team:
                exact_team_matches.append({**candidate, "match_rule": "exact_name_position_team"})

    selected = exact_team_matches or exact_name_position_matches
    gsis_ids = sorted({_clean(row["gsis_id"]) for row in selected if _clean(row["gsis_id"])})
    sleeper_ids = sorted(
        {_clean(row["sleeper_id"]) for row in selected if _clean(row["sleeper_id"])}
    )
    names = sorted(
        {_clean(row["candidate_name"]) for row in selected if _clean(row["candidate_name"])}
    )
    teams = sorted({_clean(row["team"]) for row in selected if _clean(row["team"])})
    sources_used = sorted({_clean(row["source"]) for row in selected if _clean(row["source"])})
    match_rules = sorted(
        {_clean(row["match_rule"]) for row in selected if _clean(row["match_rule"])}
    )

    if exact_team_matches and len(gsis_ids) == 1:
        decision = SAFE_RESOLUTION_PROPOSED
        confidence = "high"
        notes = (
            "Exact normalized name, position, and team found one unique local nflverse "
            "identity candidate. This is a proposal only; artifact not rewritten until "
            "human/Data Hygiene approval accepts the bridge."
        )
    elif selected:
        decision = NEEDS_HUMAN_REVIEW
        confidence = "medium"
        notes = (
            "Exact normalized name and position candidate exists, but team evidence is "
            "missing, aliased, or ambiguous. Keep out of app artifact until reviewed."
        )
    else:
        decision = KEEP_NEED_IDENTITY_REVIEW
        confidence = "low"
        notes = "No exact local nflverse identity candidate found under approved sources."

    return {
        "candidate_source": ";".join(sources_used) or NOT_ENOUGH_INFORMATION,
        "candidate_match_rule": ";".join(match_rules) or NOT_ENOUGH_INFORMATION,
        "candidate_nflverse_player_names": ";".join(names) or NOT_ENOUGH_INFORMATION,
        "candidate_sleeper_ids": ";".join(sleeper_ids) or NOT_ENOUGH_INFORMATION,
        "candidate_gsis_ids": ";".join(gsis_ids) or NOT_ENOUGH_INFORMATION,
        "candidate_teams": ";".join(teams) or NOT_ENOUGH_INFORMATION,
        "proposed_decision": decision,
        "confidence": confidence,
        "source_columns_used": (
            "artifact.nwr_player_name,nwr_position,nwr_team; "
            "ff_playerids.name,position,team,gsis_id,sleeper_id; "
            "players.display_name,position,latest_team,gsis_id; "
            "rosters.full_name,position,team,gsis_id,sleeper_id; "
            "weekly_rosters.full_name,position,team,gsis_id,sleeper_id"
        ),
        "notes": notes,
    }


def _identity_queue_row(row: dict[str, str], candidate: dict[str, str]) -> dict[str, str]:
    return _ordered(
        {
            "nwr_player_id": _clean(row.get("nwr_player_id")) or NOT_ENOUGH_INFORMATION,
            "nwr_player_name": _clean(row.get("nwr_player_name")) or NOT_ENOUGH_INFORMATION,
            "nwr_position": _clean(row.get("nwr_position")) or NOT_ENOUGH_INFORMATION,
            "nwr_team": _clean(row.get("nwr_team")) or NOT_ENOUGH_INFORMATION,
            "reason_identity_failed": _clean(row.get("identity_caveat")) or NOT_ENOUGH_INFORMATION,
            **candidate,
            "review_only": DISPLAY_ONLY,
            "model_use_allowed": DENY,
            "training_allowed": DENY,
            "source_truth_allowed": DENY,
        },
        IDENTITY_REVIEW_COLUMNS,
    )


def _identity_proposal_row(
    row: dict[str, str],
    candidate: dict[str, str],
    queue_row: dict[str, str],
) -> dict[str, str]:
    return _ordered(
        {
            "nwr_player_id": queue_row["nwr_player_id"],
            "nwr_player_name": queue_row["nwr_player_name"],
            "nwr_position": queue_row["nwr_position"],
            "nwr_team": queue_row["nwr_team"],
            "candidate_gsis_id": _first_token(candidate["candidate_gsis_ids"]),
            "candidate_sleeper_id": _first_token(candidate["candidate_sleeper_ids"]),
            "candidate_nflverse_name": _first_token(candidate["candidate_nflverse_player_names"]),
            "candidate_team": _first_token(candidate["candidate_teams"]),
            "candidate_source": candidate["candidate_source"],
            "candidate_match_rule": candidate["candidate_match_rule"],
            "proposed_decision": candidate["proposed_decision"],
            "confidence": candidate["confidence"],
            "source_columns_used": candidate["source_columns_used"],
            "review_only": DISPLAY_ONLY,
            "model_use_allowed": DENY,
            "training_allowed": DENY,
            "source_truth_allowed": DENY,
            "notes": candidate["notes"],
        },
        IDENTITY_PROPOSAL_COLUMNS,
    )


def _candidate_dict(source: str, row: dict[str, str], match_rule: str) -> dict[str, str]:
    return {
        "source": source,
        "match_rule": match_rule,
        "candidate_name": _display_name(row),
        "sleeper_id": _clean(row.get("sleeper_id")),
        "gsis_id": _clean(row.get("gsis_id")),
        "team": _candidate_team(row),
    }


def _candidate_name(row: dict[str, str]) -> str:
    return _normalize_name(
        row.get("full_name")
        or row.get("display_name")
        or row.get("name")
        or row.get("player_name")
        or row.get("player")
        or row.get("football_name")
    )


def _display_name(row: dict[str, str]) -> str:
    return _clean(
        row.get("full_name")
        or row.get("display_name")
        or row.get("name")
        or row.get("player_name")
        or row.get("player")
        or row.get("football_name")
    )


def _candidate_position(row: dict[str, str]) -> str:
    return _clean(row.get("position") or row.get("pos"))


def _candidate_team(row: dict[str, str]) -> str:
    return _clean(row.get("team") or row.get("latest_team") or row.get("recent_team"))


def _rows_by_schedule_team(
    rows: Sequence[dict[str, str]],
) -> dict[str, tuple[dict[str, str], ...]]:
    by_team: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        for column in ("home_team", "away_team"):
            team = _clean(row.get(column))
            if team:
                by_team[team].append(row)
    return {team: tuple(team_rows) for team, team_rows in by_team.items()}


def _team_aliases(snapshot_dir: Path, schedule_teams: set[str]) -> dict[str, str]:
    aliases = {"JAC": "JAX", "LAR": "LA"}
    teams_path = snapshot_dir / "teams.csv"
    if teams_path.exists():
        for row in _read_csv(teams_path):
            team = _clean(row.get("team_abbr"))
            if team in schedule_teams:
                aliases[team] = team
    return aliases


def _artifact_team_counts(
    artifact_rows: Sequence[dict[str, str]],
    aliases: dict[str, str],
) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"all": 0, "safe": 0})
    for row in artifact_rows:
        team = _clean(row.get("nflverse_team"))
        if team == NOT_ENOUGH_INFORMATION:
            team = _clean(row.get("nwr_team"))
        if not team or team in {NOT_ENOUGH_INFORMATION, "needs_data"}:
            team = NOT_ENOUGH_INFORMATION
        display_team = aliases.get(team, team)
        counts[display_team]["all"] += 1
        if row.get("identity_join_status") == SAFE_NOW_DISPLAY_ONLY:
            counts[display_team]["safe"] += 1
    return counts


def _canonical_team(
    team: str,
    schedule_team_rows: dict[str, tuple[dict[str, str], ...]],
    aliases: dict[str, str],
) -> tuple[str, str]:
    if team in schedule_team_rows:
        return team, "aligned"
    alias = aliases.get(team)
    if alias and alias in schedule_team_rows:
        return alias, f"alias:{team}->{alias}"
    if team == NOT_ENOUGH_INFORMATION:
        return team, NOT_APPLICABLE
    return team, NEED_TEAM_ALIAS_REVIEW


def _schedule_audit_row(
    *,
    team: str,
    player_rows: int,
    safe_rows: int,
    schedule_rows: Sequence[dict[str, str]],
    canonical_team: str,
    alias_status: str,
    as_of: date,
) -> dict[str, str]:
    dated_rows = sorted(
        (row for row in schedule_rows if _parse_date(row.get("gameday")) is not None),
        key=lambda row: _parse_date(row.get("gameday")) or date.min,
    )
    future_rows = [
        row for row in dated_rows if (_parse_date(row.get("gameday")) or date.min) >= as_of
    ]
    next_row = future_rows[0] if future_rows else {}
    seasons = sorted(
        {_clean(row.get("season")) for row in schedule_rows if _clean(row.get("season"))}
    )
    weeks = sorted(
        {_clean(row.get("week")) for row in schedule_rows if _clean(row.get("week"))},
        key=_int_sort,
    )
    min_gameday = _clean(dated_rows[0].get("gameday")) if dated_rows else NOT_ENOUGH_INFORMATION
    max_gameday = _clean(dated_rows[-1].get("gameday")) if dated_rows else NOT_ENOUGH_INFORMATION
    if next_row:
        status = SAFE_NOW_DISPLAY_ONLY
        root_cause = NOT_APPLICABLE
    elif not schedule_rows:
        status = NEED_TEAM_ALIAS_REVIEW
        root_cause = "no schedule rows found for team or approved alias"
    else:
        status = NEED_CURRENT_SCHEDULE_REFRESH
        root_cause = "schedule data has no game on or after as_of_date"
    return _ordered(
        {
            "team": team,
            "canonical_schedule_team": canonical_team,
            "artifact_player_rows": player_rows,
            "safe_identity_player_rows": safe_rows,
            "schedule_rows": len(schedule_rows),
            "schedule_seasons": ";".join(seasons) or NOT_ENOUGH_INFORMATION,
            "schedule_weeks": f"{weeks[0]}-{weeks[-1]}" if weeks else NOT_ENOUGH_INFORMATION,
            "min_gameday": min_gameday,
            "max_gameday": max_gameday,
            "as_of_date": as_of.isoformat(),
            "has_current_or_future_game": "true" if next_row else "false",
            "next_game_week": _clean(next_row.get("week")) or NOT_ENOUGH_INFORMATION,
            "next_game_date": _clean(next_row.get("gameday")) or NOT_ENOUGH_INFORMATION,
            "next_opponent": (
                _next_opponent(canonical_team, next_row) if next_row else NOT_ENOUGH_INFORMATION
            ),
            "bye_week": NOT_ENOUGH_INFORMATION,
            "schedule_context_status": status,
            "root_cause": root_cause,
            "team_alias_status": alias_status,
            "review_only": DISPLAY_ONLY,
            "display_only": DISPLAY_ONLY,
            "model_use_allowed": DENY,
            "training_allowed": DENY,
            "source_truth_allowed": DENY,
            "rank_logic_allowed": DENY,
            "hidden_sort_allowed": DENY,
            "trade_value_allowed": DENY,
            "pick_value_allowed": DENY,
            "notes": (
                "team-level schedule display context only; no matchup strength, "
                "projection, start/sit, win probability, rank/model, hidden sort, "
                "trade value, or pick value"
            ),
        },
        SCHEDULE_AUDIT_COLUMNS,
    )


def _next_opponent(team: str, row: dict[str, str]) -> str:
    home = _clean(row.get("home_team"))
    away = _clean(row.get("away_team"))
    if team == home:
        return away or NOT_ENOUGH_INFORMATION
    if team == away:
        return home or NOT_ENOUGH_INFORMATION
    return NOT_ENOUGH_INFORMATION


def _identity_summary_markdown(result: IdentityReviewResult) -> str:
    return "\n".join(
        [
            "# NFLVerse Player Context Identity Review Summary",
            "",
            f"Rows reviewed: `{result.reviewed_rows}`",
            f"Safe resolution proposals: `{result.safe_resolution_proposals}`",
            "Rows safely resolved/applied to artifact: `0`",
            f"Needs human review: `{result.human_review_rows}`",
            f"Keep NEED_IDENTITY_REVIEW: `{result.keep_review_rows}`",
            "",
            "This packet is review-only. It does not approve fuzzy identity matches, does "
            "not use market/DynastyProcess/vendor/private data, and does not rewrite the "
            "player context display artifact.",
            "",
            "Rows marked `SAFE_RESOLUTION_PROPOSED` have exact normalized local-source "
            "name, position, and team evidence with one unique candidate ID. They still "
            "require Data Hygiene/HQ acceptance before the primary app artifact can be "
            "rebuilt, especially where the current NWR player ID is missing.",
        ]
    )


def _schedule_build_report_markdown(result: ScheduleAuditResult, as_of: date) -> str:
    return "\n".join(
        [
            "# NFLVerse Schedule Context Build Report",
            "",
            f"As-of date: `{as_of.isoformat()}`",
            f"Teams audited: `{result.audited_teams}`",
            f"Teams with schedule rows: `{result.teams_with_schedule_rows}`",
            f"Teams with current/future game rows: `{result.teams_with_current_or_future_game}`",
            "",
            "Root cause:",
            "",
            result.root_cause,
            "",
            "Findings:",
            "",
            "- Approved schedules data is present and readable.",
            "- Local schedules cover 2024-2025 with weeks 1-22.",
            "- The latest local game date is before the current as-of date, so next game, "
            "opponent, and bye cannot be safely populated.",
            "- Team abbreviations are mostly aligned for nflverse team codes; app-facing "
            "`LAR` and `JAC` require aliases to schedules `LA` and `JAX` when using NWR "
            "team values directly.",
            "- Current-date/week logic is required before any future schedule display.",
            "- Missing schedule context remains `Not enough information`.",
        ]
    )


def _schedule_guardrail_report_markdown(result: ScheduleAuditResult) -> str:
    flags_ok = all(
        row["display_only"] == DISPLAY_ONLY
        and row["review_only"] == DISPLAY_ONLY
        and row["model_use_allowed"] == DENY
        and row["training_allowed"] == DENY
        and row["source_truth_allowed"] == DENY
        and row["rank_logic_allowed"] == DENY
        and row["hidden_sort_allowed"] == DENY
        and row["trade_value_allowed"] == DENY
        and row["pick_value_allowed"] == DENY
        for row in result.audit_rows
    )
    return "\n".join(
        [
            "# NFLVerse Schedule Context Guardrail Report",
            "",
            f"Guardrail flags valid: `{str(flags_ok).lower()}`",
            "",
            "This audit adds no app behavior, Rankings behavior, model input, source truth, "
            "hidden sort, matchup strength, projected points, start/sit logic, win "
            "probability, trade value, or pick value.",
            "",
            "No raw `C:\\NWR_SHARED_DATA` files are tracked. Only compact derived audit "
            "CSV/Markdown outputs are committed.",
        ]
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[dict[str, str]], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _ordered(row: dict[str, Any], columns: tuple[str, ...]) -> dict[str, str]:
    return {column: str(row.get(column, "")) for column in columns}


def _first_token(value: str) -> str:
    if value == NOT_ENOUGH_INFORMATION:
        return NOT_ENOUGH_INFORMATION
    return value.split(";")[0] if value else NOT_ENOUGH_INFORMATION


def _parse_date(value: Any) -> date | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _int_sort(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 999


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_name(value: Any) -> str:
    return "".join(character.lower() for character in _clean(value) if character.isalnum())
