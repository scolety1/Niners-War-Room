from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_score_movement_audit_service import (
    DEFAULT_MOVEMENT_AUDIT_ROWS,
)
from src.services.full_player_board_value_service import (
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
    FULL_BOARD_SCORE_COLUMN,
)
from src.services.model_v4_identity_join_gate_service import normalize_identity_name

DEFAULT_SOURCE_QUARANTINE_CSV = Path(
    "local_exports/model_v4/current_value/latest/full_board_source_quarantine_audit.csv"
)
DEFAULT_SOURCE_QUARANTINE_DOC = Path(
    "docs/model_v4/FULL_BOARD_SOURCE_QUARANTINE_AUDIT_20260608.md"
)
DEFAULT_QB_SANITY_DOC = Path(
    "docs/model_v4/FULL_BOARD_QB_1QB_SANITY_AUDIT_20260608.md"
)
DEFAULT_TE_SANITY_DOC = Path(
    "docs/model_v4/FULL_BOARD_TE_NO_PREMIUM_SANITY_AUDIT_20260608.md"
)
DEFAULT_SANITY_ISSUE_QUEUE = Path(
    "local_exports/model_v4/current_value/latest/full_board_rankings_sanity_issue_queue.csv"
)

SOURCE_WARNING_TOKENS = (
    "team_mismatch",
    "identity_review",
    "partial_or_quarantined",
    "stale_team",
    "stale_status",
    "missing_score_disclosure",
    "unmatched_identity",
    "duplicate_identity",
)
QB_ANCHORS = (
    "Josh Allen",
    "Drake Maye",
    "Trevor Lawrence",
    "Matthew Stafford",
    "Patrick Mahomes",
    "Jalen Hurts",
    "Lamar Jackson",
    "Brock Purdy",
    "Joe Burrow",
    "Jayden Daniels",
    "Kyler Murray",
    "Daniel Jones",
)
TE_ANCHORS = (
    "Trey McBride",
    "Brock Bowers",
    "Travis Kelce",
    "Kyle Pitts",
    "Sam LaPorta",
    "Mark Andrews",
    "T.J. Hockenson",
    "Jake Ferguson",
    "Brenton Strange",
)
SENTINELS = ("Keenan Allen", "Darius Slayton")

SOURCE_QUARANTINE_HEADER = (
    "player",
    "position",
    "active_board_team",
    "model_v4_team",
    "old_team_if_applicable",
    "current_export_team",
    "age",
    "nwr_rank",
    "nwr_dynasty_score",
    "league_rank",
    "market_rank",
    "trust_status",
    "warning_flags",
    "raw_identity_key_fields",
    "source_path",
    "source_column",
    "lineage_class",
    "quarantine_recommendation",
    "should_rank_normally",
    "human_readable_data_needed",
)

ISSUE_QUEUE_HEADER = (
    "issue_id",
    "player",
    "position",
    "age",
    "team",
    "nwr_rank",
    "nwr_score",
    "league_rank",
    "market_rank",
    "roster_status",
    "trust_status",
    "warning_count",
    "warning_summary",
    "issue_bucket",
    "severity",
    "why_flagged",
    "likely_cause",
    "recommended_next_action",
    "formula_candidate_allowed_later",
    "source_repair_required_first",
    "human_review_question",
)


@dataclass(frozen=True)
class RankingsSanityGateResult:
    source_quarantine_rows: tuple[dict[str, object], ...]
    issue_rows: tuple[dict[str, object], ...]
    source_doc: str
    qb_doc: str
    te_doc: str
    summary: dict[str, object]


@dataclass(frozen=True)
class RankingsSanityGatePaths:
    source_quarantine_csv: Path
    source_quarantine_doc: Path
    qb_sanity_doc: Path
    te_sanity_doc: Path
    issue_queue_csv: Path


def build_rankings_sanity_gate(
    *,
    full_board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    movement_path: str | Path = DEFAULT_MOVEMENT_AUDIT_ROWS,
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
) -> RankingsSanityGateResult:
    full_rows = _read_rows(Path(full_board_path))
    movement_rows = _read_rows(Path(movement_path))
    active_rows = _read_rows(Path(data_pack_path) / "model_outputs.csv")
    active_team_by_id = _active_team_by_id(Path(data_pack_path), active_rows)
    movement_by_key = _movement_lookup(movement_rows)

    source_rows = tuple(
        _source_quarantine_row(
            row=row,
            movement=movement_by_key.get(_join_key(row), {}),
            active_team=active_team_by_id.get(str(row.get("player_id") or ""), ""),
        )
        for row in full_rows
        if _source_quarantine_required(row)
    )
    issue_rows = _issue_queue_rows(full_rows, movement_by_key, source_rows)
    source_doc = _source_quarantine_doc(source_rows)
    qb_doc = _qb_sanity_doc(full_rows, movement_by_key)
    te_doc = _te_sanity_doc(full_rows, movement_by_key)
    summary = _summary(full_rows, source_rows, issue_rows)
    return RankingsSanityGateResult(
        source_quarantine_rows=source_rows,
        issue_rows=issue_rows,
        source_doc=source_doc,
        qb_doc=qb_doc,
        te_doc=te_doc,
        summary=summary,
    )


def write_rankings_sanity_gate(
    *,
    result: RankingsSanityGateResult | None = None,
    source_quarantine_csv: str | Path = DEFAULT_SOURCE_QUARANTINE_CSV,
    source_quarantine_doc: str | Path = DEFAULT_SOURCE_QUARANTINE_DOC,
    qb_sanity_doc: str | Path = DEFAULT_QB_SANITY_DOC,
    te_sanity_doc: str | Path = DEFAULT_TE_SANITY_DOC,
    issue_queue_csv: str | Path = DEFAULT_SANITY_ISSUE_QUEUE,
) -> RankingsSanityGatePaths:
    result = result or build_rankings_sanity_gate()
    source_csv = Path(source_quarantine_csv)
    source_doc = Path(source_quarantine_doc)
    qb_doc = Path(qb_sanity_doc)
    te_doc = Path(te_sanity_doc)
    issue_csv = Path(issue_queue_csv)
    _write_csv(source_csv, SOURCE_QUARANTINE_HEADER, result.source_quarantine_rows)
    _write_text(source_doc, result.source_doc)
    _write_text(qb_doc, result.qb_doc)
    _write_text(te_doc, result.te_doc)
    _write_csv(issue_csv, ISSUE_QUEUE_HEADER, result.issue_rows)
    return RankingsSanityGatePaths(
        source_quarantine_csv=source_csv,
        source_quarantine_doc=source_doc,
        qb_sanity_doc=qb_doc,
        te_sanity_doc=te_doc,
        issue_queue_csv=issue_csv,
    )


def _source_quarantine_row(
    *,
    row: dict[str, str],
    movement: dict[str, str],
    active_team: str,
) -> dict[str, object]:
    flags = _split_flags(row.get("warning_flags"))
    return {
        "player": movement.get("player") or row.get("player_name", ""),
        "position": row.get("position", ""),
        "active_board_team": active_team,
        "model_v4_team": row.get("nfl_team", ""),
        "old_team_if_applicable": movement.get("team_old", ""),
        "current_export_team": row.get("nfl_team", ""),
        "age": row.get("age", ""),
        "nwr_rank": row.get("nwr_rank", ""),
        "nwr_dynasty_score": row.get(FULL_BOARD_SCORE_COLUMN, ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "warning_flags": row.get("warning_flags", ""),
        "raw_identity_key_fields": _identity_fields(row),
        "source_path": row.get("upstream_source_path") or row.get("source_path", ""),
        "source_column": row.get("upstream_source_column") or row.get("source_column", ""),
        "lineage_class": row.get("lineage_class", ""),
        "quarantine_recommendation": _quarantine_recommendation(flags),
        "should_rank_normally": "no_source_quarantine_visible",
        "human_readable_data_needed": _data_needed(row, flags),
    }


def _issue_queue_rows(
    full_rows: tuple[dict[str, str], ...],
    movement_by_key: dict[tuple[str, str], dict[str, str]],
    source_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    issues: dict[tuple[str, str, str], dict[str, object]] = {}
    scored = _scored_non_k(full_rows)
    for row in scored[:50]:
        _maybe_add_issue(issues, row, movement_by_key, "top_50_scan")
    for row in list(reversed(scored[-50:])):
        _maybe_add_issue(issues, row, movement_by_key, "bottom_50_scan")
    for row in scored:
        key = _join_key(row)
        if _source_quarantine_required(row):
            _add_issue(
                issues,
                row,
                movement_by_key,
                "identity_team_mismatch",
                "high",
                "Identity/team/source quarantine warning is present.",
                "source mapping or identity join issue",
                "verify team/source mapping",
                formula_later=False,
                source_first=True,
            )
        if row.get("is_my_team") == "1":
            _maybe_add_issue(issues, row, movement_by_key, "my_team_scan")
        if _is_qb_sanity_issue(row, movement_by_key.get(key, {})):
            _add_issue(
                issues,
                row,
                movement_by_key,
                "qb_1qb_format_sanity",
                _qb_issue_severity(row, movement_by_key.get(key, {})),
                "QB placement needs 1QB format review.",
                "1QB compression, cap behavior, or universe-expansion artifact",
                "compare 1QB cap behavior",
                formula_later=True,
                source_first=_has_identity_source_flag(row),
            )
        if _is_te_sanity_issue(row, movement_by_key.get(key, {})):
            _add_issue(
                issues,
                row,
                movement_by_key,
                "te_no_premium_format_sanity",
                _te_issue_severity(row, movement_by_key.get(key, {})),
                "TE placement needs no-premium format review.",
                "no-premium TE discipline or elite exception behavior",
                "compare no-premium TE behavior",
                formula_later=True,
                source_first=_has_identity_source_flag(row),
            )
        if _is_high_league_low_nwr(row):
            _add_issue(
                issues,
                row,
                movement_by_key,
                "elite_player_too_low",
                "high",
                "League rank is strong but NWR rank is low.",
                "format compression, source issue, or formula candidate",
                "add to human review worksheet",
                formula_later=True,
                source_first=_has_identity_source_flag(row),
            )
        if _is_high_nwr_low_market_or_league(row):
            _add_issue(
                issues,
                row,
                movement_by_key,
                "market_league_disagreement",
                "medium",
                "NWR rank is much stronger than league or market rank.",
                "expected model edge or formula candidate",
                "inspect component breakdown",
                formula_later=True,
                source_first=_has_identity_source_flag(row),
            )
        if _many_warnings_high_score(row):
            _add_issue(
                issues,
                row,
                movement_by_key,
                "source_disclosure_gap",
                "medium",
                "High score has many warning flags.",
                "source coverage limitation",
                "add to human review worksheet",
                formula_later=False,
                source_first=True,
            )
    return tuple(
        dict(row, issue_id=f"FSQ-{index:03d}")
        for index, row in enumerate(
            sorted(
                issues.values(),
                key=lambda item: (
                    _severity_sort(item.get("severity")),
                    _rank_sort(item.get("nwr_rank")),
                    str(item.get("player") or ""),
                ),
            ),
            start=1,
        )
    )


def _maybe_add_issue(
    issues: dict[tuple[str, str, str], dict[str, object]],
    row: dict[str, str],
    movement_by_key: dict[tuple[str, str], dict[str, str]],
    scan: str,
) -> None:
    rank = _int(row.get("nwr_rank"))
    score = _float(row.get(FULL_BOARD_SCORE_COLUMN))
    warning_count = len(_split_flags(row.get("warning_flags")))
    if scan == "top_50_scan" and warning_count >= 6:
        _add_issue(
            issues,
            row,
            movement_by_key,
            "source_disclosure_gap",
            "medium",
            "Top-50 row carries many warning flags.",
            "source coverage limitation",
            "add to human review worksheet",
            formula_later=False,
            source_first=True,
        )
    if scan == "bottom_50_scan" and (_int(row.get("league_rank")) or 9999) <= 80:
        _add_issue(
            issues,
            row,
            movement_by_key,
            "elite_player_too_low",
            "high",
            "Bottom-50 NWR row has strong league rank.",
            "format compression, source issue, or universe-expansion artifact",
            "add to human review worksheet",
            formula_later=True,
            source_first=_has_identity_source_flag(row),
        )
    if scan == "my_team_scan" and (rank or 9999) >= 100:
        _add_issue(
            issues,
            row,
            movement_by_key,
            "human_review_only",
            "medium",
            "My Team player lands outside the top 100 NWR ranks.",
            "roster-specific review context",
            "add to human review worksheet",
            formula_later=False,
            source_first=_has_identity_source_flag(row),
        )
    if scan == "top_50_scan" and score is not None and _veteran_age_signal(row):
        _add_issue(
            issues,
            row,
            movement_by_key,
            "veteran_age_confidence",
            "medium",
            "Older veteran appears high in the full-board rankings.",
            "veteran age/status confidence review",
            "inspect component breakdown",
            formula_later=True,
            source_first=_has_identity_source_flag(row),
        )


def _add_issue(
    issues: dict[tuple[str, str, str], dict[str, object]],
    row: dict[str, str],
    movement_by_key: dict[tuple[str, str], dict[str, str]],
    issue_bucket: str,
    severity: str,
    why_flagged: str,
    likely_cause: str,
    next_action: str,
    *,
    formula_later: bool,
    source_first: bool,
) -> None:
    key = (_join_key(row)[0], _join_key(row)[1], issue_bucket)
    movement = movement_by_key.get(_join_key(row), {})
    issues[key] = {
        "issue_id": "",
        "player": movement.get("player") or row.get("player_name", ""),
        "position": row.get("position", ""),
        "age": row.get("age", ""),
        "team": row.get("nfl_team", ""),
        "nwr_rank": row.get("nwr_rank", ""),
        "nwr_score": row.get(FULL_BOARD_SCORE_COLUMN, ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "roster_status": row.get("pool_status", ""),
        "trust_status": row.get("trust_status", ""),
        "warning_count": len(_split_flags(row.get("warning_flags"))),
        "warning_summary": _warning_summary(row),
        "issue_bucket": issue_bucket,
        "severity": _max_severity(severity, movement.get("audit_severity", "")),
        "why_flagged": why_flagged,
        "likely_cause": likely_cause,
        "recommended_next_action": next_action,
        "formula_candidate_allowed_later": "yes" if formula_later else "no",
        "source_repair_required_first": "yes" if source_first else "no",
        "human_review_question": _human_review_question(row, issue_bucket),
    }


def _source_quarantine_doc(rows: tuple[dict[str, object], ...]) -> str:
    lines = [
        "# Full Board Source Quarantine Audit - 2026-06-08",
        "",
        "This report classifies source and identity risk only. It does not tune formulas, "
        "replace scores, or make roster decisions.",
        "",
        f"Quarantined rows: {len(rows)}",
        "",
        "| Player | Pos | Active Team | Model Team | Old Team | Rank | Score | Trust | "
        "Recommendation |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {player} | {pos} | {active} | {model} | {old} | {rank} | "
            "{score} | {trust} | {rec} |".format(
                player=row["player"],
                pos=row["position"],
                active=row["active_board_team"],
                model=row["model_v4_team"],
                old=row["old_team_if_applicable"],
                rank=row["nwr_rank"],
                score=row["nwr_dynasty_score"],
                trust=row["trust_status"],
                rec=row["quarantine_recommendation"],
            )
        )
    return "\n".join(lines) + "\n"


def _qb_sanity_doc(
    full_rows: tuple[dict[str, str], ...],
    movement_by_key: dict[tuple[str, str], dict[str, str]],
) -> str:
    qb_rows = [row for row in _scored_non_k(full_rows) if row.get("position") == "QB"]
    lines = [
        "# Full Board QB 1QB Sanity Audit - 2026-06-08",
        "",
        "League format: 10-team, 1QB, no superflex, no PPR, first-down scoring, "
        "deep benches. This is an audit only.",
        "",
        "| Player | Team | Rank | Score | League | Market | Trust | Old Score | "
        "Delta | Bucket | Question |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |",
    ]
    for row in qb_rows:
        movement = movement_by_key.get(_join_key(row), {})
        if _is_qb_sanity_issue(row, movement) or row.get("player_name") in QB_ANCHORS:
            lines.append(_qb_doc_row(row, movement))
    return "\n".join(lines) + "\n"


def _te_sanity_doc(
    full_rows: tuple[dict[str, str], ...],
    movement_by_key: dict[tuple[str, str], dict[str, str]],
) -> str:
    te_rows = [row for row in _scored_non_k(full_rows) if row.get("position") == "TE"]
    lines = [
        "# Full Board TE No-Premium Sanity Audit - 2026-06-08",
        "",
        "League format: no TE premium, 1 TE lineup, deep dynasty benches. This is an "
        "audit only.",
        "",
        "| Player | Team | Rank | Score | League | Market | Trust | Old Score | "
        "Delta | Bucket | Question |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |",
    ]
    for row in te_rows:
        movement = movement_by_key.get(_join_key(row), {})
        if _is_te_sanity_issue(row, movement) or row.get("player_name") in TE_ANCHORS:
            lines.append(_te_doc_row(row, movement))
    return "\n".join(lines) + "\n"


def _qb_doc_row(row: dict[str, str], movement: dict[str, str]) -> str:
    return (
        "| {player} | {team} | {rank} | {score} | {league} | {market} | "
        "{trust} | {old} | {delta} | {bucket} | {question} |"
    ).format(
        player=row.get("player_name", ""),
        team=row.get("nfl_team", ""),
        rank=row.get("nwr_rank", ""),
        score=row.get(FULL_BOARD_SCORE_COLUMN, ""),
        league=row.get("league_rank", ""),
        market=row.get("market_rank", ""),
        trust=row.get("trust_status", ""),
        old=movement.get("old_score", ""),
        delta=movement.get("score_delta", ""),
        bucket=_qb_bucket(row, movement),
        question=_human_review_question(row, "qb_1qb_format_sanity"),
    )


def _te_doc_row(row: dict[str, str], movement: dict[str, str]) -> str:
    return (
        "| {player} | {team} | {rank} | {score} | {league} | {market} | "
        "{trust} | {old} | {delta} | {bucket} | {question} |"
    ).format(
        player=row.get("player_name", ""),
        team=row.get("nfl_team", ""),
        rank=row.get("nwr_rank", ""),
        score=row.get(FULL_BOARD_SCORE_COLUMN, ""),
        league=row.get("league_rank", ""),
        market=row.get("market_rank", ""),
        trust=row.get("trust_status", ""),
        old=movement.get("old_score", ""),
        delta=movement.get("score_delta", ""),
        bucket=_te_bucket(row, movement),
        question=_human_review_question(row, "te_no_premium_format_sanity"),
    )


def _summary(
    full_rows: tuple[dict[str, str], ...],
    source_rows: tuple[dict[str, object], ...],
    issue_rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    return {
        "source_quarantine_rows": len(source_rows),
        "issue_rows": len(issue_rows),
        "active_rows": len(full_rows),
        "qb_rb_wr_te_scored": sum(
            row.get("position") in {"QB", "RB", "WR", "TE"}
            and _float(row.get(FULL_BOARD_SCORE_COLUMN)) is not None
            for row in full_rows
        ),
        "unscored_kickers": sum(
            row.get("position") == "K"
            and _float(row.get(FULL_BOARD_SCORE_COLUMN)) is None
            for row in full_rows
        ),
        "sentinels_safe": _sentinels_safe(full_rows),
        "contamination_safe": _contamination_safe(full_rows),
    }


def _source_quarantine_required(row: dict[str, str]) -> bool:
    flags = "|".join(_split_flags(row.get("warning_flags"))).lower()
    missing_disclosure = _float(row.get(FULL_BOARD_SCORE_COLUMN)) is not None and (
        not row.get("upstream_source_path")
        or not row.get("upstream_source_column")
        or not row.get("lineage_class")
    )
    return any(token in flags for token in SOURCE_WARNING_TOKENS) or missing_disclosure


def _is_qb_sanity_issue(row: dict[str, str], movement: dict[str, str]) -> bool:
    if row.get("position") != "QB":
        return False
    rank = _int(row.get("nwr_rank")) or 9999
    league = _int(row.get("league_rank")) or 9999
    delta = abs(_float(movement.get("score_delta")) or 0.0)
    return (
        rank <= 25
        or (league <= 60 and rank >= 120)
        or delta >= 15
        or "one_qb" in str(row.get("warning_flags") or "")
        or row.get("player_name") in QB_ANCHORS
    )


def _is_te_sanity_issue(row: dict[str, str], movement: dict[str, str]) -> bool:
    if row.get("position") != "TE":
        return False
    rank = _int(row.get("nwr_rank")) or 9999
    delta = abs(_float(movement.get("score_delta")) or 0.0)
    warnings = str(row.get("warning_flags") or "")
    return (
        rank <= 25
        or delta >= 10
        or "no_premium_te" in warnings
        or row.get("player_name") in TE_ANCHORS
    )


def _qb_bucket(row: dict[str, str], movement: dict[str, str]) -> str:
    rank = _int(row.get("nwr_rank")) or 9999
    league = _int(row.get("league_rank")) or 9999
    if _has_identity_source_flag(row):
        return "source/data issue"
    if abs(_float(movement.get("score_delta")) or 0.0) >= 15:
        return "universe-expansion artifact"
    if rank <= 25 or (league <= 60 and rank >= 120):
        return "formula candidate"
    if "one_qb" in str(row.get("warning_flags") or ""):
        return "expected 1QB compression"
    return "human-review required"


def _te_bucket(row: dict[str, str], movement: dict[str, str]) -> str:
    if _has_identity_source_flag(row):
        return "source/data issue"
    if row.get("player_name") == "Trey McBride":
        return "valid elite TE exception vs formula candidate"
    if row.get("player_name") in {"Travis Kelce", "Mark Andrews"}:
        return "veteran age/status issue"
    if abs(_float(movement.get("score_delta")) or 0.0) >= 10:
        return "no-premium format candidate"
    if "no_premium_te" in str(row.get("warning_flags") or ""):
        return "no-premium format candidate"
    return "human-review required"


def _qb_issue_severity(row: dict[str, str], movement: dict[str, str]) -> str:
    rank = _int(row.get("nwr_rank")) or 9999
    league = _int(row.get("league_rank")) or 9999
    delta = abs(_float(movement.get("score_delta")) or 0.0)
    if (league <= 60 and rank >= 120) or delta >= 20:
        return "high"
    if rank <= 25 or delta >= 15:
        return "medium"
    return "low"


def _te_issue_severity(row: dict[str, str], movement: dict[str, str]) -> str:
    rank = _int(row.get("nwr_rank")) or 9999
    delta = abs(_float(movement.get("score_delta")) or 0.0)
    if row.get("player_name") == "Trey McBride" or delta >= 15:
        return "high"
    if rank <= 25 or delta >= 10:
        return "medium"
    return "low"


def _is_high_league_low_nwr(row: dict[str, str]) -> bool:
    return (_int(row.get("league_rank")) or 9999) <= 60 and (
        _int(row.get("nwr_rank")) or 9999
    ) >= 120


def _is_high_nwr_low_market_or_league(row: dict[str, str]) -> bool:
    rank = _int(row.get("nwr_rank")) or 9999
    league = _int(row.get("league_rank")) or 9999
    market = _float(row.get("market_rank")) or 9999.0
    return rank <= 40 and (league >= 90 or market >= 90)


def _many_warnings_high_score(row: dict[str, str]) -> bool:
    return (_float(row.get(FULL_BOARD_SCORE_COLUMN)) or 0.0) >= 50.0 and (
        len(_split_flags(row.get("warning_flags"))) >= 6
    )


def _veteran_age_signal(row: dict[str, str]) -> bool:
    name = str(row.get("player_name") or "")
    return name in {
        "Christian McCaffrey",
        "Derrick Henry",
        "Matthew Stafford",
        "Davante Adams",
        "Travis Kelce",
    }


def _has_identity_source_flag(row: dict[str, str]) -> bool:
    warnings = str(row.get("warning_flags") or "").lower()
    return any(token in warnings for token in SOURCE_WARNING_TOKENS)


def _quarantine_recommendation(flags: tuple[str, ...]) -> str:
    text = "|".join(flags).lower()
    if "team_mismatch" in text:
        return "verify team/source mapping before trusting placement"
    if "identity" in text or "partial_or_quarantined" in text:
        return "verify identity join and source receipts"
    if "missing_score_disclosure" in text:
        return "repair source disclosure before trusting placement"
    return "keep source warning visible for human review"


def _data_needed(row: dict[str, str], flags: tuple[str, ...]) -> str:
    existing = str(row.get("data_needed") or "").strip()
    if existing and existing.lower() != "nan":
        return existing
    messages = []
    text = "|".join(flags).lower()
    if "team_mismatch" in text:
        messages.append("Need current team verification / team mapping repair.")
    if "identity" in text or "partial_or_quarantined" in text:
        messages.append("Need identity/source join repair before full trust.")
    if "missing_score_disclosure" in text:
        messages.append("Need source path, column, lineage, and use disclosure.")
    return " | ".join(messages) or "Need source warning review."


def _identity_fields(row: dict[str, str]) -> str:
    return (
        f"player_id={row.get('player_id', '')}|"
        f"canonical_player_key={row.get('canonical_player_key', '')}|"
        f"normalized_player_name={row.get('normalized_player_name', '')}|"
        f"position={row.get('position', '')}"
    )


def _warning_summary(row: dict[str, str]) -> str:
    flags = _split_flags(row.get("warning_flags"))
    return "|".join(flags[:4]) if flags else ""


def _human_review_question(row: dict[str, str], issue_bucket: str) -> str:
    if issue_bucket == "identity_team_mismatch":
        return "Is this player-team-source mapping correct enough for review?"
    if issue_bucket == "qb_1qb_format_sanity":
        return "Does this QB placement fit 10-team 1QB football judgment?"
    if issue_bucket == "te_no_premium_format_sanity":
        return "Does this TE placement fit no-premium scoring?"
    if issue_bucket == "elite_player_too_low":
        return "Is this low NWR placement source-driven or formula-driven?"
    return "Should this row stay flagged before rankings trust?"


def _sentinels_safe(rows: tuple[dict[str, str], ...]) -> bool:
    for player in SENTINELS:
        row = _find_player(rows, player)
        if not row:
            return False
        if row.get("lineage_class") != "review_v4_current_player":
            return False
        if row.get("source_column") != FULL_BOARD_SCORE_COLUMN:
            return False
        if _float(row.get(FULL_BOARD_SCORE_COLUMN)) == _float(row.get("legacy_active_pack_score")):
            return False
    return True


def _contamination_safe(rows: tuple[dict[str, str], ...]) -> bool:
    for row in rows:
        if _float(row.get(FULL_BOARD_SCORE_COLUMN)) is None:
            continue
        if row.get("lineage_class") != "review_v4_current_player":
            return False
        if row.get("source_column") != FULL_BOARD_SCORE_COLUMN:
            return False
        if row.get("upstream_source_column") != "checkpoint_review_score":
            return False
    return True


def _active_team_by_id(
    data_pack_path: Path,
    active_rows: tuple[dict[str, str], ...],
) -> dict[str, str]:
    official = {
        str(row.get("player_id") or ""): row
        for row in _read_rows(data_pack_path / "fact_official_rankings.csv")
    }
    roster = {
        str(row.get("player_id") or ""): row
        for row in _read_rows(data_pack_path / "fact_rosters.csv")
    }
    output = {}
    for row in active_rows:
        player_id = str(row.get("player_id") or "")
        output[player_id] = (
            row.get("nfl_team")
            or official.get(player_id, {}).get("nfl_team")
            or roster.get(player_id, {}).get("nfl_team")
            or ""
        )
    return output


def _scored_non_k(rows: tuple[dict[str, str], ...]) -> list[dict[str, str]]:
    return sorted(
        [
            row
            for row in rows
            if row.get("position") in {"QB", "RB", "WR", "TE"}
            and _float(row.get(FULL_BOARD_SCORE_COLUMN)) is not None
        ],
        key=lambda row: _rank_sort(row.get("nwr_rank")),
    )


def _find_player(rows: tuple[dict[str, str], ...], player: str) -> dict[str, str] | None:
    key = normalize_identity_name(player)
    for row in rows:
        if normalize_identity_name(row.get("player_name")) == key:
            return row
    return None


def _join_key(row: dict[str, object]) -> tuple[str, str]:
    return _join_key_from_player(row.get("player_name"), row.get("position"))


def _movement_join_key(row: dict[str, object]) -> tuple[str, str]:
    return _join_key_from_player(row.get("player"), row.get("position"))


def _movement_lookup(
    rows: tuple[dict[str, str], ...],
) -> dict[tuple[str, str], dict[str, str]]:
    lookup = {}
    for row in rows:
        lookup[_movement_join_key(row)] = row
        lookup.setdefault(_suffix_stripped_join_key(row.get("player"), row.get("position")), row)
    return lookup


def _join_key_from_player(player: object, position: object) -> tuple[str, str]:
    return (normalize_identity_name(str(player or "")), str(position or "").upper())


def _suffix_stripped_join_key(player: object, position: object) -> tuple[str, str]:
    normalized = normalize_identity_name(str(player or ""))
    for suffix in ("iii", "ii", "iv", "jr", "sr", "v"):
        if normalized.endswith(suffix):
            return (normalized[: -len(suffix)], str(position or "").upper())
    return (normalized, str(position or "").upper())


def _split_flags(value: object) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(flag.strip() for flag in str(value).split("|") if flag.strip())


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _float(value: object) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: object) -> int | None:
    parsed = _float(value)
    if parsed is None:
        return None
    return int(parsed)


def _rank_sort(value: object) -> float:
    parsed = _float(value)
    return parsed if parsed is not None else 999999.0


def _severity_sort(value: object) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(value), 4)


def _max_severity(primary: str, movement: str) -> str:
    if _severity_sort(movement) < _severity_sort(primary):
        return movement
    return primary
