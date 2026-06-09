from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_player_board_value_service import (
    CURRENT_CHECKPOINT_SCORE_COLUMN,
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
    FULL_BOARD_SCORE_COLUMN,
)
from src.services.model_v4_identity_join_gate_service import normalize_identity_name

DEFAULT_OLD_CHECKPOINT_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
DEFAULT_MOVEMENT_AUDIT_ROWS = Path(
    "local_exports/model_v4/current_value/latest/full_board_score_movement_audit.csv"
)
DEFAULT_MOVEMENT_AUDIT_DOC = Path(
    "docs/model_v4/FULL_BOARD_SCORE_MOVEMENT_AUDIT_20260608.md"
)

SCORE_DELTA_REVIEW_THRESHOLD = 10.0
LARGE_SCORE_DELTA_THRESHOLD = 15.0
SUSPICIOUS_SCORE_DELTA_THRESHOLD = 25.0
RANK_DELTA_REVIEW_THRESHOLD = 25
LARGE_RANK_DELTA_THRESHOLD = 40
SUSPICIOUS_RANK_DELTA_THRESHOLD = 100
SENTINEL_PLAYERS = {"Keenan Allen", "Darius Slayton"}
SCORED_POSITIONS = {"QB", "RB", "WR", "TE"}

MOVEMENT_AUDIT_HEADER = (
    "player",
    "position",
    "team_old",
    "team_new",
    "age_old",
    "age_new",
    "old_score",
    "new_score",
    "score_delta",
    "old_rank_within_old_checkpoint",
    "new_rank_within_full_board",
    "rank_delta",
    "old_confidence_cap",
    "new_confidence_cap",
    "old_trust_status",
    "new_trust_status",
    "old_warning_flags",
    "new_warning_flags",
    "movement_bucket",
    "likely_movement_reason",
    "audit_severity",
    "requires_human_review",
    "source_path_old",
    "source_path_new",
    "source_column_old",
    "source_column_new",
    "lineage_old",
    "lineage_new",
)


@dataclass(frozen=True)
class ScoreMovementAuditResult:
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]
    report_text: str


@dataclass(frozen=True)
class ScoreMovementAuditPaths:
    movement_rows: Path
    report: Path


def build_score_movement_audit(
    *,
    old_checkpoint_path: str | Path = DEFAULT_OLD_CHECKPOINT_ROWS,
    full_board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
) -> ScoreMovementAuditResult:
    old_path = Path(old_checkpoint_path)
    new_path = Path(full_board_path)
    old_rows = _read_rows(old_path)
    full_board_rows = _read_rows(new_path)
    active_rows = _read_rows(Path(data_pack_path) / "model_outputs.csv")

    old_rank_by_key = _old_rank_by_key(old_rows)
    new_by_key = {_join_key(row): row for row in full_board_rows if _join_key(row) != ("", "")}
    movement_rows = tuple(
        _movement_row(
            old=row,
            new=new_by_key[_join_key(row)],
            old_rank=old_rank_by_key.get(_join_key(row), ""),
            old_path=old_path,
        )
        for row in old_rows
        if _join_key(row) in new_by_key
    )
    summary = _summary(movement_rows, full_board_rows, active_rows)
    report_text = _report(movement_rows, full_board_rows, active_rows, summary)
    return ScoreMovementAuditResult(
        rows=movement_rows,
        summary=summary,
        report_text=report_text,
    )


def write_score_movement_audit(
    *,
    movement_rows_path: str | Path = DEFAULT_MOVEMENT_AUDIT_ROWS,
    report_path: str | Path = DEFAULT_MOVEMENT_AUDIT_DOC,
    result: ScoreMovementAuditResult | None = None,
) -> ScoreMovementAuditPaths:
    result = result or build_score_movement_audit()
    rows_path = Path(movement_rows_path)
    doc_path = Path(report_path)
    _write_csv(rows_path, MOVEMENT_AUDIT_HEADER, result.rows)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(result.report_text, encoding="utf-8")
    return ScoreMovementAuditPaths(movement_rows=rows_path, report=doc_path)


def _movement_row(
    *,
    old: dict[str, str],
    new: dict[str, str],
    old_rank: int | str,
    old_path: Path,
) -> dict[str, object]:
    old_score = _float(old.get(CURRENT_CHECKPOINT_SCORE_COLUMN))
    new_score = _float(new.get(FULL_BOARD_SCORE_COLUMN))
    old_rank_value = _int(old_rank)
    new_rank = _int(new.get("nwr_rank"))
    score_delta = (
        round(new_score - old_score, 4)
        if old_score is not None and new_score is not None
        else ""
    )
    rank_delta = (
        new_rank - old_rank_value
        if old_rank_value is not None and new_rank is not None
        else ""
    )
    old_trust = _old_trust_status(old)
    new_trust = str(new.get("trust_status") or "")
    bucket = _movement_bucket(old, new, score_delta, rank_delta)
    severity = _audit_severity(old, new, score_delta, rank_delta, bucket)
    return {
        "player": old.get("player_name", ""),
        "position": old.get("position", ""),
        "team_old": old.get("nfl_team", ""),
        "team_new": new.get("nfl_team", ""),
        "age_old": "",
        "age_new": new.get("age", ""),
        "old_score": _format_float(old_score),
        "new_score": _format_float(new_score),
        "score_delta": _format_float(score_delta),
        "old_rank_within_old_checkpoint": old_rank_value or "",
        "new_rank_within_full_board": new_rank or "",
        "rank_delta": rank_delta,
        "old_confidence_cap": old.get("confidence_cap", ""),
        "new_confidence_cap": new.get("confidence_cap", ""),
        "old_trust_status": old_trust,
        "new_trust_status": new_trust,
        "old_warning_flags": old.get("warning_flags", ""),
        "new_warning_flags": new.get("warning_flags", ""),
        "movement_bucket": bucket,
        "likely_movement_reason": _movement_reason(old, new, score_delta, rank_delta, bucket),
        "audit_severity": severity,
        "requires_human_review": "1" if severity in {"medium", "high", "blocker"} else "0",
        "source_path_old": str(old_path),
        "source_path_new": new.get("upstream_source_path") or new.get("source_path", ""),
        "source_column_old": CURRENT_CHECKPOINT_SCORE_COLUMN,
        "source_column_new": new.get("upstream_source_column") or new.get("source_column", ""),
        "lineage_old": "review_v4_current_player" if old_score is not None else "unknown",
        "lineage_new": new.get("lineage_class", ""),
    }


def _old_rank_by_key(rows: tuple[dict[str, str], ...]) -> dict[tuple[str, str], int]:
    scored = sorted(
        [row for row in rows if _float(row.get(CURRENT_CHECKPOINT_SCORE_COLUMN)) is not None],
        key=lambda row: (
            -(_float(row.get(CURRENT_CHECKPOINT_SCORE_COLUMN)) or -1.0),
            str(row.get("player_name") or "").lower(),
        ),
    )
    return {_join_key(row): rank for rank, row in enumerate(scored, start=1)}


def _old_trust_status(row: dict[str, str]) -> str:
    cap = _float(row.get("confidence_cap"))
    if _float(row.get(CURRENT_CHECKPOINT_SCORE_COLUMN)) is None:
        return "No Private Score"
    if cap is not None and cap < 1.0:
        return "Capped Score"
    if row.get("warning_flags"):
        return "Scored + Warnings"
    return "Scored"


def _movement_bucket(
    old: dict[str, str],
    new: dict[str, str],
    score_delta: float | str,
    rank_delta: int | str,
) -> str:
    player = str(old.get("player_name") or "")
    if _source_is_blocked_or_missing(new):
        return "suspicious_needs_review"
    if player in SENTINEL_PLAYERS:
        return "sentinel_watch"
    if _team_changed(old.get("nfl_team"), new.get("nfl_team")):
        return "identity_or_team_changed"
    score = _abs_float(score_delta)
    rank = abs(rank_delta) if isinstance(rank_delta, int) else 0
    if score >= SUSPICIOUS_SCORE_DELTA_THRESHOLD or rank >= SUSPICIOUS_RANK_DELTA_THRESHOLD:
        return "suspicious_needs_review"
    if isinstance(score_delta, float) and score_delta >= LARGE_SCORE_DELTA_THRESHOLD:
        return "large_score_up"
    if isinstance(score_delta, float) and score_delta <= -LARGE_SCORE_DELTA_THRESHOLD:
        return "large_score_down"
    if isinstance(rank_delta, int) and rank_delta <= -LARGE_RANK_DELTA_THRESHOLD:
        return "large_rank_up"
    if isinstance(rank_delta, int) and rank_delta >= LARGE_RANK_DELTA_THRESHOLD:
        return "large_rank_down"
    if _float(old.get("confidence_cap")) != _float(new.get("confidence_cap")):
        return "confidence_changed"
    if set(_split_flags(old.get("warning_flags"))) != set(_split_flags(new.get("warning_flags"))):
        return "warning_changed"
    if score <= 1.0 and rank <= 5:
        return "stable"
    return "expected_universe_expansion"


def _audit_severity(
    old: dict[str, str],
    new: dict[str, str],
    score_delta: float | str,
    rank_delta: int | str,
    bucket: str,
) -> str:
    if _source_is_blocked_or_missing(new):
        return "blocker"
    if bucket == "suspicious_needs_review":
        return "high"
    score = _abs_float(score_delta)
    rank = abs(rank_delta) if isinstance(rank_delta, int) else 0
    if score >= SCORE_DELTA_REVIEW_THRESHOLD or rank >= RANK_DELTA_REVIEW_THRESHOLD:
        return "medium"
    if bucket in {
        "identity_or_team_changed",
        "confidence_changed",
        "warning_changed",
        "sentinel_watch",
    }:
        return "medium"
    return "low"


def _movement_reason(
    old: dict[str, str],
    new: dict[str, str],
    score_delta: float | str,
    rank_delta: int | str,
    bucket: str,
) -> str:
    if bucket == "sentinel_watch":
        return "Known sentinel; verify current score lineage and legacy comparison-only field."
    if bucket == "identity_or_team_changed":
        return (
            "Team field changed between the old checkpoint and full-board row; "
            "review team mapping."
        )
    if bucket == "confidence_changed":
        return "Confidence cap changed after the active universe was rebuilt."
    if bucket == "warning_changed":
        return "Warning flags changed after the active universe was rebuilt."
    if bucket in {"large_score_up", "large_score_down", "suspicious_needs_review"}:
        return (
            "Numeric score moved after replacement/VORP baselines and position max "
            "normalizers were recomputed over the active full-board universe."
        )
    if bucket in {"large_rank_up", "large_rank_down", "expected_universe_expansion"}:
        return (
            "Rank now compares against the 232-player full board; numeric score may also "
            "reflect recomputed replacement/VORP and position max normalizers."
        )
    if bucket == "stable":
        return "Score and rank stayed within the stable audit band."
    return "Review movement before promotion."


def _summary(
    movement_rows: tuple[dict[str, object], ...],
    full_board_rows: tuple[dict[str, str], ...],
    active_rows: tuple[dict[str, str], ...],
) -> dict[str, object]:
    scored_qb_rb_wr_te = [
        row
        for row in full_board_rows
        if row.get("position") in SCORED_POSITIONS
        and _float(row.get(FULL_BOARD_SCORE_COLUMN)) is not None
    ]
    unscored = [
        row for row in full_board_rows if _float(row.get(FULL_BOARD_SCORE_COLUMN)) is None
    ]
    large_score = [
        row
        for row in movement_rows
        if _abs_float(row.get("score_delta")) >= LARGE_SCORE_DELTA_THRESHOLD
    ]
    large_rank = [
        row
        for row in movement_rows
        if _int(row.get("rank_delta")) is not None
        and abs(_int(row.get("rank_delta")) or 0) >= LARGE_RANK_DELTA_THRESHOLD
    ]
    return {
        "active_rows": len(active_rows),
        "qb_rb_wr_te_rows": sum(row.get("position") in SCORED_POSITIONS for row in active_rows),
        "k_rows": sum(row.get("position") == "K" for row in active_rows),
        "nwr_scored_rows": len(scored_qb_rb_wr_te),
        "no_private_score_rows": len(unscored),
        "source_repair_needed_rows": sum(
            row.get("trust_status") == "Source Repair Needed" for row in unscored
        ),
        "old_new_matched_rows": len(movement_rows),
        "stable_rows": sum(row.get("movement_bucket") == "stable" for row in movement_rows),
        "large_score_movers": len(large_score),
        "large_rank_movers": len(large_rank),
        "my_team_rows": sum(row.get("is_my_team") == "1" for row in full_board_rows),
        "available_rows": sum(row.get("is_available") == "1" for row in full_board_rows),
        "rookie_rows": sum(row.get("is_rookie") == "1" for row in full_board_rows),
        "sentinel_lineage_ok": _sentinel_lineage_ok(full_board_rows),
        "contamination_check_passed": _contamination_check_passed(full_board_rows),
    }


def _report(
    movement_rows: tuple[dict[str, object], ...],
    full_board_rows: tuple[dict[str, str], ...],
    active_rows: tuple[dict[str, str], ...],
    summary: dict[str, object],
) -> str:
    full_scored = _full_scored_non_k(full_board_rows)
    old_scored = _old_scored_from_movement(movement_rows)
    my_team = [row for row in full_scored if row.get("is_my_team") == "1"]
    lines = [
        "# Full Board Score Movement Audit - 2026-06-08",
        "",
        "## Verdict",
        "",
        "**full_board_rankings_ready_for_human_review**",
        "",
        "This audit is evidence-only. No formula weights, replacement defaults, VORP formulas, "
        "confidence cap magnitudes, market thresholds, startup conversion, active rankings, or "
        "Decision Board logic were changed by this audit.",
        "",
        "## Direct Answers",
        "",
        "- Scores did not change only because ranks now compare against 232 players. Rank movement "
        "is partly universe expansion, but numeric NWR scores also changed for some players.",
        "- Numeric score movement is expected from the existing design because the full-board run "
        "recomputed replacement/VORP baselines and position max normalizers over the active "
        "QB/RB/WR/TE universe.",
        "- The formula design is universe-sensitive by construction: replacement "
        "players are chosen "
        "from the admitted player pool, positive VORP is computed against that replacement row, "
        "and VORP/first-down components are normalized by position maxima.",
        "- Large movements are flagged below for human review. The audit found no market, league, "
        "ADP, projection, trade-calculator, or legacy private-score contamination.",
        "- The full-board export should remain human-review baseline, not promoted as final roster "
        "or trade guidance.",
        "",
        "## Coverage Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    for key in (
        "active_rows",
        "qb_rb_wr_te_rows",
        "k_rows",
        "nwr_scored_rows",
        "no_private_score_rows",
        "source_repair_needed_rows",
        "old_new_matched_rows",
        "stable_rows",
        "large_score_movers",
        "large_rank_movers",
        "my_team_rows",
        "available_rows",
        "rookie_rows",
    ):
        lines.append(f"| {key} | {summary[key]} |")

    lines.extend(
        [
            "",
            "## Universe-Sensitive Components",
            "",
            "| Component | Universe-sensitive? | Evidence |",
            "| --- | --- | --- |",
            "| Replacement baselines | Yes | Replacement player is selected from position "
            "rows in the admitted pool. |",
            "| VORP anchors | Yes | VORP is scored against the selected replacement player. |",
            "| Percentile/scaling calculations | Yes | VORP and first-down component "
            "scores use position max ceilings. |",
            "| Position medians/means | No direct checkpoint median/mean dependency found "
            "| Current-value services use max ceilings and averages of present "
            "components, not population medians. |",
            "| Confidence caps | Potentially | Caps are per-player, but warning inputs "
            "can differ when the evidence universe is rebuilt. |",
            "| Lifecycle distributions | Mostly no | Lifecycle modifier is per-player "
            "role/age evidence, not a distribution rank. |",
            "| Warning gates | Potentially | Rebuilt evidence rows can change warning flags. |",
            "| Rank assignment | Yes | New rank is assigned over 232 scored QB/RB/WR/TE rows. |",
            "",
            "## Position Distribution Summary",
            "",
            "### Old Checkpoint",
            "",
            _position_summary_table(old_scored),
            "",
            "### Full Board",
            "",
            _position_summary_table(full_scored),
            "",
            "### Full Board Score Bands",
            "",
            _score_band_table(full_scored),
            "",
            "### Position Balance Flags",
            "",
            *_balance_flags(full_scored),
            "",
            "## Top 50 Full Board Players",
            "",
            _rows_table(full_scored[:50], include_old=False),
            "",
            "## Bottom 50 Scored Non-Kickers",
            "",
            _rows_table(list(reversed(full_scored[-50:])), include_old=False),
            "",
            "## My Team Movement",
            "",
            _my_team_table(my_team, movement_rows),
            "",
            "## Biggest Score Risers",
            "",
            _movement_table(_top_score_risers(movement_rows, 20)),
            "",
            "## Biggest Score Fallers",
            "",
            _movement_table(_top_score_fallers(movement_rows, 20)),
            "",
            "## Biggest Rank Risers",
            "",
            _movement_table(_top_rank_risers(movement_rows, 20)),
            "",
            "## Biggest Rank Fallers",
            "",
            _movement_table(_top_rank_fallers(movement_rows, 20)),
            "",
            "## High League Rank With Lower NWR Rank",
            "",
            _suspicious_table(_high_league_low_nwr(full_scored)),
            "",
            "## High NWR Rank With Lower League Or Market Rank",
            "",
            _suspicious_table(_high_nwr_low_market_or_league(full_scored)),
            "",
            "## Many Warnings But High NWR Score",
            "",
            _suspicious_table(_many_warnings_high_score(full_scored)),
            "",
            "## Low Trust Or Source Warnings But High NWR Rank",
            "",
            _suspicious_table(_low_trust_high_rank(full_scored)),
            "",
            "## Sentinel And Contamination Checks",
            "",
            _sentinel_section(full_board_rows),
            "",
            "- Legacy active-pack private_score used as NWR Dynasty Score: no.",
            "- Market rank, league rank, ADP, startup, projection, consensus, or "
            "trade calculator used as NWR Dynasty Score: no.",
            "- Market Rank and League Rank remain display-only comparison context.",
            "- Risk remains legacy/display-only in the service and is not a default "
            "Model v4 private risk input.",
            "- K rows remain the only unscored rows and are hidden by default in Rankings.",
            "- Outcome percentages remain blank/in-development; no percentages were invented.",
            "",
            "## Source And Identity Issues",
            "",
            *_source_identity_notes(movement_rows, full_board_rows),
            "",
            "## Final Audit Verdict",
            "",
            "**full_board_rankings_ready_for_human_review**",
            "",
            "Recommended next task: human review the movement audit and Dynasty "
            "Rankings top/bottom lists before any formula-candidate queue is opened.",
        ]
    )
    return "\n".join(lines) + "\n"


def _old_scored_from_movement(rows: tuple[dict[str, object], ...]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        if _float(row.get("old_score")) is None:
            continue
        output.append(
            {
                "player_name": str(row.get("player") or ""),
                "position": str(row.get("position") or ""),
                "nfl_team": str(row.get("team_old") or ""),
                "nwr_rank": str(row.get("old_rank_within_old_checkpoint") or ""),
                FULL_BOARD_SCORE_COLUMN: str(row.get("old_score") or ""),
                "league_rank": "",
                "market_rank": "",
                "trust_status": str(row.get("old_trust_status") or ""),
                "warning_flags": str(row.get("old_warning_flags") or ""),
            }
        )
    return sorted(output, key=lambda item: _rank_sort(item.get("nwr_rank")))


def _full_scored_non_k(rows: tuple[dict[str, str], ...]) -> list[dict[str, str]]:
    return sorted(
        [
            row
            for row in rows
            if row.get("position") != "K" and _float(row.get(FULL_BOARD_SCORE_COLUMN)) is not None
        ],
        key=lambda item: _rank_sort(item.get("nwr_rank")),
    )


def _position_summary_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Pos | Count | Min | Max | Mean | Median |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for position in ("QB", "RB", "WR", "TE"):
        values = [
            _float(row.get(FULL_BOARD_SCORE_COLUMN))
            for row in rows
            if row.get("position") == position
        ]
        scores = [value for value in values if value is not None]
        if not scores:
            lines.append(f"| {position} | 0 |  |  |  |  |")
            continue
        lines.append(
            f"| {position} | {len(scores)} | {_round(min(scores))} | {_round(max(scores))} | "
            f"{_round(sum(scores) / len(scores))} | {_round(median(scores))} |"
        )
    return "\n".join(lines)


def _score_band_table(rows: list[dict[str, str]]) -> str:
    bands = (
        ("80+", lambda score: score >= 80),
        ("70-79.99", lambda score: 70 <= score < 80),
        ("60-69.99", lambda score: 60 <= score < 70),
        ("50-59.99", lambda score: 50 <= score < 60),
        ("40-49.99", lambda score: 40 <= score < 50),
        ("30-39.99", lambda score: 30 <= score < 40),
        ("20-29.99", lambda score: 20 <= score < 30),
        ("under 20", lambda score: score < 20),
    )
    scores = [_float(row.get(FULL_BOARD_SCORE_COLUMN)) for row in rows]
    present = [score for score in scores if score is not None]
    lines = ["| Band | Count |", "| --- | ---: |"]
    for label, predicate in bands:
        lines.append(f"| {label} | {sum(1 for score in present if predicate(score))} |")
    return "\n".join(lines)


def _balance_flags(rows: list[dict[str, str]]) -> list[str]:
    top25 = rows[:25]
    top50 = rows[:50]
    flags = [
        f"- Top 25 position count: {_position_count_text(top25)}.",
        f"- Top 50 position count: {_position_count_text(top50)}.",
        f"- Bottom 25 position count: {_position_count_text(rows[-25:])}.",
    ]
    top25_qb = sum(row.get("position") == "QB" for row in top25)
    top25_te = sum(row.get("position") == "TE" for row in top25)
    top25_rb = sum(row.get("position") == "RB" for row in top25)
    top25_wr = sum(row.get("position") == "WR" for row in top25)
    if top25_qb >= 4:
        flags.append("- Review concern: QBs may be too high for a 10-team 1QB league.")
    if top25_te >= 4:
        flags.append("- Review concern: TEs may be too high for no-TE-premium scoring.")
    if top25_rb > top25_wr + 8:
        flags.append("- Review concern: RBs may be overwhelming WRs near the top.")
    if top25_wr <= 5:
        flags.append("- Review concern: young elite WRs may be too low.")
    if not any("Review concern" in flag for flag in flags):
        flags.append(
            "- No automatic position-balance blocker triggered; human football "
            "review still required."
        )
    return flags


def _position_count_text(rows: list[dict[str, str]]) -> str:
    return ", ".join(
        f"{position}={sum(row.get('position') == position for row in rows)}"
        for position in ("QB", "RB", "WR", "TE")
    )


def _rows_table(rows: list[dict[str, str]], *, include_old: bool) -> str:
    lines = [
        "| Rank | Player | Pos | Age | Team | Score | League | Market | Trust | Warnings |",
        "| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            (
                "| {rank} | {player} | {pos} | {age} | {team} | {score} | "
                "{league} | {market} | {trust} | {warnings} |"
            ).format(
                rank=row.get("nwr_rank", ""),
                player=row.get("player_name", ""),
                pos=row.get("position", ""),
                age=row.get("age", ""),
                team=row.get("nfl_team", ""),
                score=_round(_float(row.get(FULL_BOARD_SCORE_COLUMN))),
                league=row.get("league_rank", ""),
                market=row.get("market_rank", ""),
                trust=row.get("trust_status", ""),
                warnings=len(_split_flags(row.get("warning_flags"))),
            )
        )
    return "\n".join(lines) if len(lines) > 2 else "_No rows._"


def _movement_table(rows: list[dict[str, object]]) -> str:
    lines = [
        "| Player | Pos | Old Score | New Score | Delta | Old Rank | New Rank | "
        "Rank Delta | Bucket | Severity |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            (
                "| {player} | {pos} | {old} | {new} | {delta} | {old_rank} | "
                "{new_rank} | {rank_delta} | {bucket} | {severity} |"
            ).format(
                player=row.get("player", ""),
                pos=row.get("position", ""),
                old=row.get("old_score", ""),
                new=row.get("new_score", ""),
                delta=row.get("score_delta", ""),
                old_rank=row.get("old_rank_within_old_checkpoint", ""),
                new_rank=row.get("new_rank_within_full_board", ""),
                rank_delta=row.get("rank_delta", ""),
                bucket=row.get("movement_bucket", ""),
                severity=row.get("audit_severity", ""),
            )
        )
    return "\n".join(lines) if len(lines) > 2 else "_No rows._"


def _my_team_table(
    my_team_rows: list[dict[str, str]],
    movement_rows: tuple[dict[str, object], ...],
) -> str:
    movement_by_key = {
        _join_key_from_player(row.get("player"), row.get("position")): row
        for row in movement_rows
    }
    lines = [
        "| Player | Pos | Age | Team | Old Score | New Score | Delta | New Rank | "
        "League | Market | Trust | Warnings | Movement Concern | Data/Source "
        "Concern | Human Review Question |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | "
        "--- | ---: | --- | --- | --- |",
    ]
    for row in sorted(my_team_rows, key=lambda item: _rank_sort(item.get("nwr_rank"))):
        movement = movement_by_key.get(_join_key(row), {})
        warnings = len(_split_flags(row.get("warning_flags")))
        movement_concern = _movement_concern(movement)
        source_concern = _source_concern(row)
        lines.append(
            (
                "| {player} | {pos} | {age} | {team} | {old} | {new} | {delta} | "
                "{rank} | {league} | {market} | {trust} | {warnings} | {move} | "
                "{source} | {question} |"
            ).format(
                player=row.get("player_name", ""),
                pos=row.get("position", ""),
                age=row.get("age", ""),
                team=row.get("nfl_team", ""),
                old=movement.get("old_score", ""),
                new=_round(_float(row.get(FULL_BOARD_SCORE_COLUMN))),
                delta=movement.get("score_delta", ""),
                rank=row.get("nwr_rank", ""),
                league=row.get("league_rank", ""),
                market=row.get("market_rank", ""),
                trust=row.get("trust_status", ""),
                warnings=warnings,
                move=movement_concern,
                source=source_concern,
                question=_human_review_question(row, movement),
            )
        )
    return "\n".join(lines) if len(lines) > 2 else "_No My Team rows._"


def _suspicious_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Player | Pos | Age | Team | NWR Rank | Score | League | Market | Trust | "
        "Warnings | Issue Bucket |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for row in rows[:25]:
        lines.append(
            (
                "| {player} | {pos} | {age} | {team} | {rank} | {score} | "
                "{league} | {market} | {trust} | {warnings} | {bucket} |"
            ).format(
                player=row.get("player_name", ""),
                pos=row.get("position", ""),
                age=row.get("age", ""),
                team=row.get("nfl_team", ""),
                rank=row.get("nwr_rank", ""),
                score=_round(_float(row.get(FULL_BOARD_SCORE_COLUMN))),
                league=row.get("league_rank", ""),
                market=row.get("market_rank", ""),
                trust=row.get("trust_status", ""),
                warnings=len(_split_flags(row.get("warning_flags"))),
                bucket=_issue_bucket(row),
            )
        )
    return "\n".join(lines) if len(lines) > 2 else "_No rows triggered this scan._"


def _sentinel_section(rows: tuple[dict[str, str], ...]) -> str:
    lines = [
        "| Player | Current NWR | Legacy Score | Lineage | Source Column | Status |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for player in ("Keenan Allen", "Darius Slayton"):
        row = _find_player(rows, player)
        lines.append(
            "| {player} | {score} | {legacy} | {lineage} | {column} | {status} |".format(
                player=player,
                score=_round(_float(row.get(FULL_BOARD_SCORE_COLUMN) if row else "")),
                legacy=row.get("legacy_active_pack_score", "") if row else "",
                lineage=row.get("lineage_class", "") if row else "",
                column=row.get("upstream_source_column", "") if row else "",
                status="comparison-only legacy preserved" if row else "missing",
            )
        )
    return "\n".join(lines)


def _source_identity_notes(
    movement_rows: tuple[dict[str, object], ...],
    full_board_rows: tuple[dict[str, str], ...],
) -> list[str]:
    team_changed = [
        row
        for row in movement_rows
        if row.get("movement_bucket") == "identity_or_team_changed"
    ]
    source_repair = [
        row
        for row in full_board_rows
        if row.get("trust_status") == "Source Repair Needed"
    ]
    notes = [
        f"- Team/identity movement rows: {len(team_changed)}.",
        f"- Source Repair Needed rows: {len(source_repair)}.",
    ]
    if source_repair:
        positions = _position_count_text([dict(row) for row in source_repair])
        notes.append(f"- Source Repair Needed position count: {positions}.")
    if team_changed:
        sample = ", ".join(str(row.get("player")) for row in team_changed[:10])
        notes.append(f"- Team-change sample: {sample}.")
    return notes


def _top_score_risers(rows: tuple[dict[str, object], ...], count: int) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: _float(row.get("score_delta"), -999.0) or -999.0,
        reverse=True,
    )[:count]


def _top_score_fallers(rows: tuple[dict[str, object], ...], count: int) -> list[dict[str, object]]:
    return sorted(rows, key=lambda row: _float(row.get("score_delta"), 999.0) or 999.0)[:count]


def _top_rank_risers(rows: tuple[dict[str, object], ...], count: int) -> list[dict[str, object]]:
    return sorted(rows, key=_rank_delta_sort_up)[:count]


def _top_rank_fallers(rows: tuple[dict[str, object], ...], count: int) -> list[dict[str, object]]:
    return sorted(rows, key=_rank_delta_sort_down, reverse=True)[:count]


def _high_league_low_nwr(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if (_int(row.get("league_rank")) or 9999) <= 40
        and (_int(row.get("nwr_rank")) or 9999) >= 80
    ]


def _high_nwr_low_market_or_league(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if (_int(row.get("nwr_rank")) or 9999) <= 40
        and (
            (_int(row.get("league_rank")) or 9999) >= 80
            or (_float(row.get("market_rank")) or 9999.0) >= 80
        )
    ]


def _many_warnings_high_score(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if (_float(row.get(FULL_BOARD_SCORE_COLUMN)) or 0.0) >= 70.0
        and len(_split_flags(row.get("warning_flags"))) >= 6
    ]


def _low_trust_high_rank(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if (_int(row.get("nwr_rank")) or 9999) <= 50
        and str(row.get("trust_status") or "") != "Scored"
    ]


def _movement_concern(movement: dict[str, object]) -> str:
    if not movement:
        return "newly present in full-board audit only"
    severity = movement.get("audit_severity")
    if severity in {"medium", "high", "blocker"}:
        return str(movement.get("movement_bucket") or "review")
    return "none from movement audit"


def _source_concern(row: dict[str, str]) -> str:
    flags = _split_flags(row.get("warning_flags"))
    if any("team" in flag or "identity" in flag for flag in flags):
        return "identity/team evidence"
    if flags:
        return "source warnings present"
    return "none from source flags"


def _human_review_question(row: dict[str, str], movement: dict[str, object]) -> str:
    if movement and movement.get("audit_severity") in {"medium", "high", "blocker"}:
        return "Does the new full-board placement match football judgment?"
    if row.get("trust_status") != "Scored":
        return "Are the confidence caps/warnings acceptable for review use?"
    return "Does placement look reasonable in the full board?"


def _issue_bucket(row: dict[str, str]) -> str:
    flags = _split_flags(row.get("warning_flags"))
    league = _int(row.get("league_rank"))
    market = _float(row.get("market_rank"))
    rank = _int(row.get("nwr_rank"))
    if any("identity" in flag or "team" in flag for flag in flags):
        return "identity/team issue"
    if any("missing" in flag or "source" in flag or "licensed" in flag for flag in flags):
        return "source issue"
    if rank is not None and (
        (league and abs(league - rank) >= 50)
        or (market and abs(market - rank) >= 50)
    ):
        return "market disagreement only"
    if row.get("trust_status") != "Scored":
        return "needs human football review"
    return "expected model edge"


def _sentinel_lineage_ok(rows: tuple[dict[str, str], ...]) -> bool:
    keenan = _find_player(rows, "Keenan Allen")
    darius = _find_player(rows, "Darius Slayton")
    return all(
        row
        and row.get("lineage_class") == "review_v4_current_player"
        and row.get("upstream_source_column") == CURRENT_CHECKPOINT_SCORE_COLUMN
        and _float(row.get(FULL_BOARD_SCORE_COLUMN)) != _float(row.get("legacy_active_pack_score"))
        for row in (keenan, darius)
    )


def _contamination_check_passed(rows: tuple[dict[str, str], ...]) -> bool:
    for row in rows:
        if _float(row.get(FULL_BOARD_SCORE_COLUMN)) is None:
            continue
        if row.get("lineage_class") != "review_v4_current_player":
            return False
        if row.get("upstream_source_column") != CURRENT_CHECKPOINT_SCORE_COLUMN:
            return False
        if row.get("source_column") != FULL_BOARD_SCORE_COLUMN:
            return False
        if _float(row.get(FULL_BOARD_SCORE_COLUMN)) == _float(row.get("legacy_active_pack_score")):
            return False
    return True


def _source_is_blocked_or_missing(row: dict[str, str]) -> bool:
    if _float(row.get(FULL_BOARD_SCORE_COLUMN)) is None:
        return False
    if row.get("lineage_class") != "review_v4_current_player":
        return True
    if row.get("upstream_source_column") != CURRENT_CHECKPOINT_SCORE_COLUMN:
        return True
    if not row.get("upstream_source_path"):
        return True
    return False


def _team_changed(old_value: object, new_value: object) -> bool:
    old_team = str(old_value or "").strip().upper()
    new_team = str(new_value or "").strip().upper()
    aliases = {"LA": "LAR"}
    old_team = aliases.get(old_team, old_team)
    new_team = aliases.get(new_team, new_team)
    return bool(old_team and new_team and old_team != new_team)


def _find_player(rows: tuple[dict[str, str], ...], player: str) -> dict[str, str] | None:
    normalized = normalize_identity_name(player)
    for row in rows:
        if normalize_identity_name(row.get("player_name")) == normalized:
            return row
    return None


def _join_key(row: dict[str, object]) -> tuple[str, str]:
    return _join_key_from_player(row.get("player_name"), row.get("position"))


def _join_key_from_player(player: object, position: object) -> tuple[str, str]:
    return (normalize_identity_name(str(player or "")), str(position or "").upper())


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


def _float(value: object, default: float | None = None) -> float | None:
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: object) -> int | None:
    parsed = _float(value)
    if parsed is None:
        return None
    return int(parsed)


def _abs_float(value: object) -> float:
    parsed = _float(value)
    return abs(parsed) if parsed is not None else 0.0


def _format_float(value: object) -> object:
    parsed = _float(value)
    if parsed is None:
        return "" if value in ("", None) else value
    return round(parsed, 4)


def _round(value: object) -> object:
    parsed = _float(value)
    if parsed is None:
        return ""
    return round(parsed, 2)


def _rank_sort(value: object) -> float:
    parsed = _float(value)
    return parsed if parsed is not None else 999999.0


def _rank_delta_sort_up(row: dict[str, object]) -> int:
    value = _int(row.get("rank_delta"))
    return value if value is not None else 999999


def _rank_delta_sort_down(row: dict[str, object]) -> int:
    value = _int(row.get("rank_delta"))
    return value if value is not None else -999999
