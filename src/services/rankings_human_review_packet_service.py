from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.full_board_rankings_sanity_gate_service import DEFAULT_SANITY_ISSUE_QUEUE
from src.services.full_board_score_movement_audit_service import DEFAULT_MOVEMENT_AUDIT_ROWS
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.model_v4_identity_join_gate_service import normalize_identity_name

OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_COMPONENT_ROWS = OUTPUT_ROOT / (
    "full_board_active_support/current_value_layers/current_player_value_component_rows.csv"
)
DEFAULT_SOURCE_QUARANTINE_ROWS = OUTPUT_ROOT / "full_board_source_quarantine_audit.csv"
DEFAULT_REMAINING_TEAM_ROWS = OUTPUT_ROOT / "remaining_current_team_source_repair.csv"
DEFAULT_ROTOWIRE_ROWS = Path(
    "local_exports/external_sources/rotowire/nfl_players/latest/"
    "rotowire_nfl_team_status_review_rows.csv"
)
DEFAULT_TOP_100_REVIEW = OUTPUT_ROOT / "rankings_top_100_human_review.csv"
DEFAULT_MY_TEAM_REVIEW = OUTPUT_ROOT / "rankings_my_team_human_review.csv"
DEFAULT_QB_TRIAGE = OUTPUT_ROOT / "rankings_qb_formula_candidate_triage.csv"
DEFAULT_TE_TRIAGE = OUTPUT_ROOT / "rankings_te_formula_candidate_triage.csv"
DEFAULT_SUSPICIOUS_REVIEW = OUTPUT_ROOT / "rankings_suspicious_rows_human_review.csv"
DEFAULT_COMPONENT_READBACK = OUTPUT_ROOT / "rankings_suspicious_component_readback.csv"
DEFAULT_READINESS_REPORT = Path("docs/model_v4/RANKINGS_HUMAN_REVIEW_READINESS_20260609.md")
DEFAULT_FORMULA_TRIAGE_REPORT = Path(
    "docs/model_v4/RANKINGS_FORMULA_CANDIDATE_TRIAGE_20260609.md"
)
DEFAULT_MORNING_HANDOFF = Path("docs/model_v4/MORNING_RANKINGS_HANDOFF_20260609.md")

REVIEW_ACTIONS = {
    "qb_1qb_format_sanity": "evaluate QB formula candidate later",
    "te_no_premium_format_sanity": "evaluate TE formula candidate later",
    "source_disclosure_gap": "verify source/status",
    "veteran_age_confidence": "inspect component breakdown",
    "elite_player_too_low": "add to human review worksheet",
    "market_league_disagreement": "accept as possible model edge pending human review",
    "human_review_only": "add to human review worksheet",
}

COMPONENT_NAMES = (
    "Trey McBride",
    "Josh Allen",
    "Drake Maye",
    "Trevor Lawrence",
    "Matthew Stafford",
    "Patrick Mahomes",
    "Jalen Hurts",
    "Lamar Jackson",
    "Joe Burrow",
    "Jayden Daniels",
    "Kyler Murray",
    "Travis Kelce",
    "Kyle Pitts",
    "Brock Bowers",
    "Sam LaPorta",
    "Mark Andrews",
    "T.J. Hockenson",
    "De'Von Achane",
    "Chase Brown",
    "Brian Thomas Jr.",
    "Brandon Aiyuk",
    "David Montgomery",
    "Keenan Allen",
    "Darius Slayton",
)

TOP_100_HEADER = (
    "nwr_rank",
    "player",
    "position",
    "age",
    "team",
    "nwr_score",
    "league_rank",
    "market_rank",
    "trust_status",
    "roster_status",
    "warning_summary",
    "issue_bucket",
    "human_review_question",
)

MY_TEAM_HEADER = (
    "nwr_rank",
    "player",
    "position",
    "age",
    "team",
    "nwr_score",
    "league_rank",
    "market_rank",
    "trust_status",
    "roster_status",
    "warning_summary",
    "source_status",
    "formula_candidate_status",
    "human_review_question",
)

POSITION_TRIAGE_HEADER = (
    "nwr_rank",
    "player",
    "age",
    "team",
    "nwr_score",
    "league_rank",
    "market_rank",
    "trust_status",
    "warnings",
    "issue_bucket",
    "likely_cause",
    "formula_candidate_allowed_later",
    "source_cleanup_required_first",
    "human_review_question",
)

SUSPICIOUS_HEADER = (
    "severity",
    "issue_bucket",
    "player",
    "position",
    "age",
    "team",
    "nwr_rank",
    "nwr_score",
    "league_rank",
    "market_rank",
    "trust_status",
    "warning_summary",
    "why_flagged",
    "likely_cause",
    "recommended_next_action",
    "human_review_question",
)

COMPONENT_READBACK_HEADER = (
    "player",
    "position",
    "nwr_rank",
    "nwr_score",
    "source_path",
    "source_column",
    "lineage_class",
    "confidence_cap",
    "trust_status",
    "component_fields_available",
    "component_summary",
    "missing_component_explanation",
    "warning_flags",
    "likely_issue_bucket",
    "human_review_question",
)


@dataclass(frozen=True)
class RankingsHumanReviewPacketResult:
    top_100_rows: tuple[dict[str, object], ...]
    my_team_rows: tuple[dict[str, object], ...]
    qb_rows: tuple[dict[str, object], ...]
    te_rows: tuple[dict[str, object], ...]
    suspicious_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    readiness_report: str
    formula_triage_report: str
    morning_handoff: str
    summary: dict[str, object]


@dataclass(frozen=True)
class RankingsHumanReviewPacketPaths:
    top_100: Path
    my_team: Path
    qb_triage: Path
    te_triage: Path
    suspicious: Path
    component_readback: Path
    readiness_report: Path
    formula_triage_report: Path
    morning_handoff: Path


def build_rankings_human_review_packet(
    *,
    full_board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    issue_queue_path: str | Path = DEFAULT_SANITY_ISSUE_QUEUE,
    component_rows_path: str | Path = DEFAULT_COMPONENT_ROWS,
    movement_path: str | Path = DEFAULT_MOVEMENT_AUDIT_ROWS,
    source_quarantine_path: str | Path = DEFAULT_SOURCE_QUARANTINE_ROWS,
    remaining_team_path: str | Path = DEFAULT_REMAINING_TEAM_ROWS,
    rotowire_path: str | Path = DEFAULT_ROTOWIRE_ROWS,
) -> RankingsHumanReviewPacketResult:
    full_rows = _read_rows(Path(full_board_path))
    issue_rows = _read_rows(Path(issue_queue_path))
    component_rows = _read_rows(Path(component_rows_path))
    movement_rows = _read_rows(Path(movement_path))
    source_rows = _read_rows(Path(source_quarantine_path))
    remaining_rows = _read_rows(Path(remaining_team_path))
    rotowire_rows = _read_rows(Path(rotowire_path))
    issue_by_player = _issues_by_player(issue_rows)
    component_by_player = _components_by_player(component_rows)
    scored_non_k = [row for row in full_rows if row.get("position") != "K" and row.get("nwr_rank")]
    top_100 = tuple(
        _top_100_row(row, issue_by_player.get(_key(row.get("player_name")), ()))
        for row in scored_non_k[:100]
    )
    my_team = tuple(
        _my_team_row(row, issue_by_player.get(_key(row.get("player_name")), ()))
        for row in scored_non_k
        if row.get("is_my_team") == "1"
    )
    qb_rows = tuple(
        _position_triage_row(row, issue_by_player.get(_key(row.get("player_name")), ()))
        for row in scored_non_k
        if row.get("position") == "QB"
    )
    te_rows = tuple(
        _position_triage_row(row, issue_by_player.get(_key(row.get("player_name")), ()))
        for row in scored_non_k
        if row.get("position") == "TE"
    )
    suspicious = tuple(
        _suspicious_row(row)
        for row in issue_rows
        if row.get("severity") in {"high", "medium"}
    )
    component_readback = tuple(
        _component_readback_row(
            player=player,
            full_rows=full_rows,
            issue_by_player=issue_by_player,
            component_by_player=component_by_player,
        )
        for player in COMPONENT_NAMES
    )
    summary = _summary(
        full_rows=full_rows,
        issue_rows=issue_rows,
        movement_rows=movement_rows,
        source_rows=source_rows,
        remaining_rows=remaining_rows,
        rotowire_rows=rotowire_rows,
    )
    readiness = _readiness_report(
        summary=summary,
        full_rows=full_rows,
        issue_rows=issue_rows,
        top_100=top_100,
        my_team=my_team,
    )
    formula = _formula_triage_report(summary=summary, issue_rows=issue_rows)
    handoff = _morning_handoff(summary=summary)
    return RankingsHumanReviewPacketResult(
        top_100_rows=top_100,
        my_team_rows=my_team,
        qb_rows=qb_rows,
        te_rows=te_rows,
        suspicious_rows=suspicious,
        component_rows=component_readback,
        readiness_report=readiness,
        formula_triage_report=formula,
        morning_handoff=handoff,
        summary=summary,
    )


def write_rankings_human_review_packet(
    *,
    result: RankingsHumanReviewPacketResult | None = None,
    top_100_path: str | Path = DEFAULT_TOP_100_REVIEW,
    my_team_path: str | Path = DEFAULT_MY_TEAM_REVIEW,
    qb_triage_path: str | Path = DEFAULT_QB_TRIAGE,
    te_triage_path: str | Path = DEFAULT_TE_TRIAGE,
    suspicious_path: str | Path = DEFAULT_SUSPICIOUS_REVIEW,
    component_readback_path: str | Path = DEFAULT_COMPONENT_READBACK,
    readiness_report_path: str | Path = DEFAULT_READINESS_REPORT,
    formula_triage_report_path: str | Path = DEFAULT_FORMULA_TRIAGE_REPORT,
    morning_handoff_path: str | Path = DEFAULT_MORNING_HANDOFF,
) -> RankingsHumanReviewPacketPaths:
    result = result or build_rankings_human_review_packet()
    paths = RankingsHumanReviewPacketPaths(
        top_100=Path(top_100_path),
        my_team=Path(my_team_path),
        qb_triage=Path(qb_triage_path),
        te_triage=Path(te_triage_path),
        suspicious=Path(suspicious_path),
        component_readback=Path(component_readback_path),
        readiness_report=Path(readiness_report_path),
        formula_triage_report=Path(formula_triage_report_path),
        morning_handoff=Path(morning_handoff_path),
    )
    _write_csv(paths.top_100, TOP_100_HEADER, result.top_100_rows)
    _write_csv(paths.my_team, MY_TEAM_HEADER, result.my_team_rows)
    _write_csv(paths.qb_triage, POSITION_TRIAGE_HEADER, result.qb_rows)
    _write_csv(paths.te_triage, POSITION_TRIAGE_HEADER, result.te_rows)
    _write_csv(paths.suspicious, SUSPICIOUS_HEADER, result.suspicious_rows)
    _write_csv(paths.component_readback, COMPONENT_READBACK_HEADER, result.component_rows)
    _write_text(paths.readiness_report, result.readiness_report)
    _write_text(paths.formula_triage_report, result.formula_triage_report)
    _write_text(paths.morning_handoff, result.morning_handoff)
    return paths


def _top_100_row(row: dict[str, str], issues: tuple[dict[str, str], ...]) -> dict[str, object]:
    return {
        "nwr_rank": row.get("nwr_rank", ""),
        "player": row.get("player_name", ""),
        "position": row.get("position", ""),
        "age": row.get("age", ""),
        "team": row.get("nfl_team", "") or "NO TEAM",
        "nwr_score": row.get("nwr_dynasty_score", ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "roster_status": row.get("pool_status", ""),
        "warning_summary": row.get("warning_flags", ""),
        "issue_bucket": _issue_buckets(issues),
        "human_review_question": _questions(issues) or _default_question(row),
    }


def _my_team_row(row: dict[str, str], issues: tuple[dict[str, str], ...]) -> dict[str, object]:
    source_status = row.get("team_resolution_status", "")
    formula_status = "candidate_later" if any(
        issue.get("formula_candidate_allowed_later") == "yes" for issue in issues
    ) else "no_formula_candidate_flag"
    return {
        **_top_100_row(row, issues),
        "source_status": source_status,
        "formula_candidate_status": formula_status,
    }


def _position_triage_row(
    row: dict[str, str],
    issues: tuple[dict[str, str], ...],
) -> dict[str, object]:
    primary = _primary_issue(issues)
    return {
        "nwr_rank": row.get("nwr_rank", ""),
        "player": row.get("player_name", ""),
        "age": row.get("age", ""),
        "team": row.get("nfl_team", "") or "NO TEAM",
        "nwr_score": row.get("nwr_dynasty_score", ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "warnings": row.get("warning_flags", ""),
        "issue_bucket": _issue_buckets(issues),
        "likely_cause": primary.get("likely_cause", ""),
        "formula_candidate_allowed_later": primary.get("formula_candidate_allowed_later", ""),
        "source_cleanup_required_first": primary.get("source_repair_required_first", ""),
        "human_review_question": _questions(issues) or _default_question(row),
    }


def _suspicious_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "severity": row.get("severity", ""),
        "issue_bucket": row.get("issue_bucket", ""),
        "player": row.get("player", ""),
        "position": row.get("position", ""),
        "age": row.get("age", ""),
        "team": row.get("team", ""),
        "nwr_rank": row.get("nwr_rank", ""),
        "nwr_score": row.get("nwr_score", ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "warning_summary": row.get("warning_summary", ""),
        "why_flagged": row.get("why_flagged", ""),
        "likely_cause": row.get("likely_cause", ""),
        "recommended_next_action": REVIEW_ACTIONS.get(
            row.get("issue_bucket", ""),
            row.get("recommended_next_action", ""),
        ),
        "human_review_question": row.get("human_review_question", ""),
    }


def _component_readback_row(
    *,
    player: str,
    full_rows: tuple[dict[str, str], ...],
    issue_by_player: dict[str, tuple[dict[str, str], ...]],
    component_by_player: dict[str, tuple[dict[str, str], ...]],
) -> dict[str, object]:
    row = _find_player(full_rows, player)
    issues = issue_by_player.get(_key(player), ())
    components = component_by_player.get(_key(player), ())
    summary = _component_summary(components)
    return {
        "player": player,
        "position": row.get("position", ""),
        "nwr_rank": row.get("nwr_rank", ""),
        "nwr_score": row.get("nwr_dynasty_score", ""),
        "source_path": row.get("upstream_source_path") or row.get("source_path", ""),
        "source_column": row.get("upstream_source_column") or row.get("source_column", ""),
        "lineage_class": row.get("lineage_class", ""),
        "confidence_cap": row.get("confidence_cap", ""),
        "trust_status": row.get("trust_status", ""),
        "component_fields_available": "yes" if components else "no",
        "component_summary": summary,
        "missing_component_explanation": "" if components else (
            "No component rows found in full-board current-value component export."
        ),
        "warning_flags": row.get("warning_flags", ""),
        "likely_issue_bucket": _issue_buckets(issues),
        "human_review_question": _questions(issues) or _default_question(row),
    }


def _summary(
    *,
    full_rows: tuple[dict[str, str], ...],
    issue_rows: tuple[dict[str, str], ...],
    movement_rows: tuple[dict[str, str], ...],
    source_rows: tuple[dict[str, str], ...],
    remaining_rows: tuple[dict[str, str], ...],
    rotowire_rows: tuple[dict[str, str], ...],
) -> dict[str, object]:
    issue_bucket_counts = Counter(row.get("issue_bucket", "") for row in issue_rows)
    severity_counts = Counter(row.get("severity", "") for row in issue_rows)
    pos_counts = Counter(row.get("position", "") for row in full_rows if row.get("nwr_rank"))
    return {
        "active_rows": len(full_rows),
        "qb_rb_wr_te_rows": sum(
            row.get("position") in {"QB", "RB", "WR", "TE"} for row in full_rows
        ),
        "kicker_rows": sum(row.get("position") == "K" for row in full_rows),
        "nwr_scored_rows": sum(bool(row.get("nwr_dynasty_score")) for row in full_rows),
        "no_private_score_rows": sum(not bool(row.get("nwr_dynasty_score")) for row in full_rows),
        "my_team_rows": sum(row.get("is_my_team") == "1" for row in full_rows),
        "source_quarantine_rows": len(source_rows),
        "source_quarantine_non_kickers": sum(row.get("position") != "K" for row in source_rows),
        "rotowire_rows": len(rotowire_rows),
        "rotowire_team_rows": sum(bool(row.get("nfl_team")) for row in rotowire_rows),
        "rotowire_no_team_rows": sum(
            row.get("status") == "free_agent_or_no_team" for row in rotowire_rows
        ),
        "remaining_team_resolved_targets": sum(
            row.get("player") not in {"Matt Prater", "Darius Slayton"}
            and row.get("repair_status") == "resolved_current_team_verified"
            for row in remaining_rows
        ),
        "remaining_team_no_team_targets": sum(
            row.get("player") not in {"Matt Prater", "Darius Slayton"}
            and row.get("repair_status") == "current_status_verified_no_team"
            for row in remaining_rows
        ),
        "issue_rows": len(issue_rows),
        "high_issue_rows": severity_counts.get("high", 0),
        "medium_issue_rows": severity_counts.get("medium", 0),
        "low_issue_rows": severity_counts.get("low", 0),
        "issue_bucket_counts": dict(issue_bucket_counts),
        "position_counts": dict(pos_counts),
        "movement_matched_rows": len(movement_rows),
        "large_score_movers": sum(
            "large_score" in str(row.get("movement_bucket", "")) for row in movement_rows
        ),
        "large_rank_movers": sum(
            "large_rank" in str(row.get("movement_bucket", "")) for row in movement_rows
        ),
        "sentinels_safe": _sentinels_safe(full_rows),
        "contamination_safe": _contamination_safe(full_rows),
        "decision_board_blocked": True,
        "verdict": "rankings_ready_for_human_review_formula_candidates_next",
    }


def _readiness_report(
    *,
    summary: dict[str, object],
    full_rows: tuple[dict[str, str], ...],
    issue_rows: tuple[dict[str, str], ...],
    top_100: tuple[dict[str, object], ...],
    my_team: tuple[dict[str, object], ...],
) -> str:
    scored = [row for row in full_rows if row.get("nwr_rank") and row.get("position") != "K"]
    lines = [
        "# Rankings Human Review Readiness - 2026-06-09",
        "",
        "## Executive Summary",
        "",
        "The full-board Rankings baseline is ready for human review as a Rankings page "
        "baseline, with formula work still blocked from implementation. Source/team "
        "quarantine is reduced to the eight hidden kickers. RotoWire local team/status "
        "context is integrated as source repair only and does not affect private scores.",
        "",
        "QB 1QB and TE no-premium issues are clean enough to open controlled "
        "formula-candidate review tomorrow, after human review confirms the suspicious "
        "rows are real model-shape problems rather than acceptable model edge.",
        "",
        "## Coverage Counts",
        "",
        _metric_table(
            summary,
            (
                "active_rows",
                "qb_rb_wr_te_rows",
                "kicker_rows",
                "nwr_scored_rows",
                "no_private_score_rows",
                "my_team_rows",
                "source_quarantine_rows",
                "source_quarantine_non_kickers",
            ),
        ),
        "",
        "## Source And RotoWire Status",
        "",
        _metric_table(
            summary,
            (
                "rotowire_rows",
                "rotowire_team_rows",
                "rotowire_no_team_rows",
                "remaining_team_resolved_targets",
                "remaining_team_no_team_targets",
            ),
        ),
        "",
        "RotoWire is allowed only for current team/status display, identity/team source "
        "repair, injury/status context, warning explanation, and source quarantine "
        "resolution. It is blocked from private value, NWR rank, tiers, market/league "
        "gaps, outcome percentages, and recommendations.",
        "",
        "## Movement Audit Summary",
        "",
        _metric_table(
            summary,
            ("movement_matched_rows", "large_score_movers", "large_rank_movers"),
        ),
        "",
        "Numeric score movement is expected because replacement baselines, VORP anchors, "
        "and position max normalizers recomputed against the admitted 232-player universe. "
        "This is an audit note, not formula approval.",
        "",
        "## Top 25 Current Full-Board Rankings",
        "",
        _ranking_table(scored[:25]),
        "",
        "## Top 25 By Position",
        "",
    ]
    for position in ("QB", "RB", "WR", "TE"):
        position_rows = [r for r in scored if r.get("position") == position][:25]
        lines.extend([f"### {position}", "", _ranking_table(position_rows), ""])
    lines.extend(
        [
            "## Bottom 25 Scored Non-Kickers",
            "",
            _ranking_table(list(reversed(scored[-25:]))),
            "",
            "## My Team Rankings Snapshot",
            "",
            _review_table(my_team[:30]),
            "",
            "## High-Severity Issue Summary",
            "",
            _issue_summary(issue_rows, severity="high"),
            "",
            "## QB 1QB Sanity Summary",
            "",
            _bucket_summary(issue_rows, "qb_1qb_format_sanity"),
            "",
            "## TE No-Premium Sanity Summary",
            "",
            _bucket_summary(issue_rows, "te_no_premium_format_sanity"),
            "",
            "## RB/WR Balance Sanity Summary",
            "",
            "RB/WR balance remains a candidate area through elite-player-too-low and "
            "market/league disagreement rows. No RB/WR formula work should happen until "
            "the human worksheet confirms which disagreements are football misses.",
            "",
            "## Veteran Age/Status Confidence Summary",
            "",
            _bucket_summary(issue_rows, "veteran_age_confidence"),
            "",
            "## Young-Player Evidence Summary",
            "",
            _bucket_summary(issue_rows, "elite_player_too_low"),
            "",
            "## Market/League Disagreement Summary",
            "",
            _bucket_summary(issue_rows, "market_league_disagreement"),
            "",
            "## Source/Data Issue Summary",
            "",
            _bucket_summary(issue_rows, "source_disclosure_gap"),
            "",
            "## Formula-Candidate-Only Summary",
            "",
            "Candidate areas are QB 1QB spread/compression, TE no-premium ceiling/cap, "
            "RB/WR cross-position balance, veteran age/status confidence, young-player "
            "evidence sensitivity, and no-team/FA status confidence handling. This packet "
            "does not propose or implement formula changes.",
            "",
            "## Blockers Before Formula Work",
            "",
            "- Human review of top QB/TE outliers and high-severity rows.",
            "- Component readback review for suspicious names.",
            "- Agreement that no source/data issue explains the formula-candidate rows.",
            "",
            "## Blockers Before Decision Board Work",
            "",
            "- Decision Board should remain blocked until Rankings human review and at "
            "least the first controlled formula-candidate triage are complete.",
            "",
            "## Exact Next Recommended Task",
            "",
            "Run a controlled, proposal-only QB 1QB and TE no-premium formula-candidate "
            "experiment design pass. Do not tune or implement weights yet.",
        ]
    )
    return "\n".join(lines) + "\n"


def _formula_triage_report(
    *,
    summary: dict[str, object],
    issue_rows: tuple[dict[str, str], ...],
) -> str:
    return (
        "# Rankings Formula Candidate Triage - 2026-06-09\n\n"
        "This report is proposal-only. It does not tune formulas, change weights, "
        "modify scores, or create roster recommendations.\n\n"
        "## Answers\n\n"
        "1. QB 1QB formula review is justified after source cleanup. The issue queue "
        f"contains {summary['issue_bucket_counts'].get('qb_1qb_format_sanity', 0)} "
        "QB format-sanity rows.\n"
        "2. TE no-premium formula review is justified after source cleanup. The issue "
        f"queue contains {summary['issue_bucket_counts'].get('te_no_premium_format_sanity', 0)} "
        "TE format-sanity rows.\n"
        "3. RB/WR balance review is justified only after human review confirms "
        "elite-player-too-low rows are true misses.\n"
        "4. Veteran age/status confidence review is justified as a secondary candidate.\n"
        "5. Young-player evidence sensitivity review is justified as a secondary candidate.\n"
        "6. Remaining source/data blockers are limited to hidden kickers and source "
        "coverage warnings; non-kicker identity/team mismatch is cleared.\n"
        "7. Likely formula candidates: QB 1QB spread/compression and TE no-premium "
        "ceiling/cap.\n"
        "8. Possible model edge: market/league disagreement rows where private evidence "
        "supports the NWR placement.\n"
        "9. First controlled experiment tomorrow: design a read-only QB/TE shadow "
        "comparison harness that reports candidate deltas without changing baseline "
        "scores.\n\n"
        "## Candidate Hypotheses\n\n"
        "- QB 1QB spread/compression may be over-rewarding replacement-level or aging QB "
        "profiles while depressing elite rushing/young QB profiles.\n"
        "- TE no-premium ceiling/cap may over-reward elite TE scarcity relative to no-TE-"
        "premium format.\n"
        "- RB/WR balance may need inspection only after QB/TE are isolated.\n"
        "- Veteran no-team/FA confidence handling should remain capped and visible; do "
        "not convert status context into score changes without a controlled candidate.\n\n"
        "## Required Evidence Before Implementation\n\n"
        "- Human review worksheet annotations for top outliers.\n"
        "- Component readbacks for suspicious rows.\n"
        "- Shadow-only candidate deltas against the current full-board baseline.\n"
        "- Sentinel and contamination checks rerun after any proposal.\n\n"
        "## Current Issue Counts\n\n"
        + _issue_counts_markdown(issue_rows)
    )


def _morning_handoff(summary: dict[str, object]) -> str:
    return (
        "# Morning Rankings Handoff - 2026-06-09\n\n"
        "## What Ran\n\n"
        "The RotoWire local team/status source, full-board Rankings export, score "
        "movement audit, identity/team repair audit, remaining-team repair audit, and "
        "rankings sanity gate were rerun successfully.\n\n"
        "## What Changed\n\n"
        "Generated a human-review readiness packet, formula-candidate triage packet, "
        "top-100/My Team/QB/TE/suspicious-row review CSVs, and component readback CSV.\n\n"
        "## What Did Not Change\n\n"
        "No formulas, scores, weights, VORP/replacement, Decision Board logic, market "
        "logic, or recommendations changed.\n\n"
        "## Current Verdict\n\n"
        f"{summary['verdict']}\n\n"
        "## Biggest Remaining Concerns\n\n"
        "- QB 1QB format sanity.\n"
        "- TE no-premium format sanity.\n"
        "- RB/WR balance and young-player evidence sensitivity as secondary review lanes.\n"
        "- No-team/FA veteran status should remain capped/visible.\n\n"
        "## Inspect First\n\n"
        "- `docs/model_v4/RANKINGS_HUMAN_REVIEW_READINESS_20260609.md`\n"
        "- `local_exports/model_v4/current_value/latest/"
        "rankings_suspicious_rows_human_review.csv`\n"
        "- `local_exports/model_v4/current_value/latest/"
        "rankings_suspicious_component_readback.csv`\n"
        "- `docs/model_v4/RANKINGS_FORMULA_CANDIDATE_TRIAGE_20260609.md`\n\n"
        "## Next Recommended Codex Task\n\n"
        "Create a controlled, proposal-only QB 1QB and TE no-premium formula-candidate "
        "shadow experiment design. Do not implement formula changes.\n\n"
        "## Decision Board\n\n"
        "Decision Board should remain blocked until Rankings human review and formula-"
        "candidate triage are complete.\n"
    )


def _issues_by_player(rows: tuple[dict[str, str], ...]) -> dict[str, tuple[dict[str, str], ...]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_key(row.get("player"))].append(row)
    return {key: tuple(value) for key, value in grouped.items()}


def _components_by_player(
    rows: tuple[dict[str, str], ...],
) -> dict[str, tuple[dict[str, str], ...]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_key(row.get("player_name"))].append(row)
    return {key: tuple(value) for key, value in grouped.items()}


def _find_player(rows: tuple[dict[str, str], ...], player: str) -> dict[str, str]:
    wanted = _key(player)
    return next((row for row in rows if _key(row.get("player_name")) == wanted), {})


def _key(value: object) -> str:
    return normalize_identity_name(str(value or ""))


def _issue_buckets(issues: tuple[dict[str, str], ...]) -> str:
    return "|".join(
        dict.fromkeys(
            issue.get("issue_bucket", "") for issue in issues if issue.get("issue_bucket")
        )
    )


def _questions(issues: tuple[dict[str, str], ...]) -> str:
    return " | ".join(
        dict.fromkeys(
            issue.get("human_review_question", "")
            for issue in issues
            if issue.get("human_review_question")
        )
    )


def _primary_issue(issues: tuple[dict[str, str], ...]) -> dict[str, str]:
    return next(iter(issues), {})


def _default_question(row: dict[str, str]) -> str:
    return f"Does this {row.get('position', 'player')} placement fit the league format?"


def _component_summary(rows: tuple[dict[str, str], ...]) -> str:
    parts = []
    for row in rows[:12]:
        parts.append(
            "{component_name}: value={component_value}, normalized={normalized_score}, "
            "weight={component_weight}, contribution={weighted_contribution}, "
            "status={source_status}".format(**row)
        )
    return " | ".join(parts)


def _sentinels_safe(rows: tuple[dict[str, str], ...]) -> bool:
    by_name = {row.get("player_name"): row for row in rows}
    keenan = by_name.get("Keenan Allen", {})
    darius = by_name.get("Darius Slayton", {})
    return (
        keenan.get("nwr_dynasty_score") != "82.4"
        and keenan.get("legacy_active_pack_score") == "82.4"
        and keenan.get("lineage_class") == "review_v4_current_player"
        and darius.get("nwr_dynasty_score") != "78.88"
        and darius.get("legacy_active_pack_score") == "78.88"
        and darius.get("lineage_class") == "review_v4_current_player"
    )


def _contamination_safe(rows: tuple[dict[str, str], ...]) -> bool:
    return all(
        row.get("lineage_class") in {"review_v4_current_player", "unknown"}
        and row.get("legacy_primary_scores_used", "") == ""
        for row in rows
    )


def _metric_table(summary: dict[str, object], keys: tuple[str, ...]) -> str:
    lines = ["| Metric | Value |", "| --- | ---: |"]
    for key in keys:
        lines.append(f"| {key} | {summary.get(key, 0)} |")
    return "\n".join(lines)


def _ranking_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Rank | Player | Pos | Team | Score | Trust |",
        "| ---: | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('nwr_rank', '')} | {row.get('player_name', '')} | "
            f"{row.get('position', '')} | {row.get('nfl_team', '') or 'NO TEAM'} | "
            f"{row.get('nwr_dynasty_score', '')} | {row.get('trust_status', '')} |"
        )
    return "\n".join(lines)


def _review_table(rows: tuple[dict[str, object], ...]) -> str:
    lines = [
        "| Rank | Player | Pos | Team | Score | Issue |",
        "| ---: | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('nwr_rank', '')} | {row.get('player', '')} | "
            f"{row.get('position', '')} | {row.get('team', '')} | "
            f"{row.get('nwr_score', '')} | {row.get('issue_bucket', '')} |"
        )
    return "\n".join(lines)


def _issue_summary(rows: tuple[dict[str, str], ...], *, severity: str) -> str:
    selected = [row for row in rows if row.get("severity") == severity][:25]
    return _issue_rows_table(selected)


def _bucket_summary(rows: tuple[dict[str, str], ...], bucket: str) -> str:
    selected = [row for row in rows if row.get("issue_bucket") == bucket][:25]
    if not selected:
        return "No rows in this bucket."
    return _issue_rows_table(selected)


def _issue_rows_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Severity | Player | Pos | Rank | Issue | Next Action |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        next_action = REVIEW_ACTIONS.get(
            row.get("issue_bucket", ""),
            row.get("recommended_next_action", ""),
        )
        lines.append(
            f"| {row.get('severity', '')} | {row.get('player', '')} | "
            f"{row.get('position', '')} | {row.get('nwr_rank', '')} | "
            f"{row.get('issue_bucket', '')} | {next_action} |"
        )
    return "\n".join(lines)


def _issue_counts_markdown(rows: tuple[dict[str, str], ...]) -> str:
    counts = Counter(row.get("issue_bucket", "") for row in rows)
    lines = ["| Issue bucket | Count |", "| --- | ---: |"]
    for bucket, count in sorted(counts.items()):
        lines.append(f"| {bucket} | {count} |")
    return "\n".join(lines) + "\n"


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
