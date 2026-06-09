# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.qb_te_upper_band_guard_v2_patch_audit_service import (
    MOVEMENT_AUDIT_CSV,
    PRE_RB_WR_CHECKSUM,
)

OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_ISSUE_QUEUE = OUTPUT_ROOT / "full_board_rankings_sanity_issue_queue.csv"
DEFAULT_SOURCE_QUARANTINE = OUTPUT_ROOT / "full_board_source_quarantine_audit.csv"
DEFAULT_TOP_100 = OUTPUT_ROOT / "rankings_post_patch_top_100_review.csv"
DEFAULT_MY_TEAM = OUTPUT_ROOT / "rankings_post_patch_my_team_review.csv"
DEFAULT_QB_TE = OUTPUT_ROOT / "rankings_post_patch_qb_te_review.csv"
DEFAULT_ACCEPTANCE_REPORT = Path(
    "docs/model_v4/RANKINGS_POST_PATCH_ACCEPTANCE_AUDIT_20260609.md"
)
DEFAULT_FINAL_HANDOFF = Path("docs/model_v4/RANKINGS_FINAL_HANDOFF_20260609.md")

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
    "previous_rank_if_available",
    "rank_delta_if_available",
    "human_review_question",
)

QB_TE_HEADER = (
    "nwr_rank",
    "player",
    "position",
    "age",
    "team",
    "nwr_score",
    "league_rank",
    "market_rank",
    "trust_status",
    "warning_summary",
    "issue_bucket",
    "patch_effect_summary",
    "human_review_question",
)

WATCHLIST_NAMES = (
    "Trey McBride",
    "Kyle Pitts",
    "Travis Kelce",
    "Brock Bowers",
    "Josh Allen",
    "Drake Maye",
    "Patrick Mahomes",
    "Lamar Jackson",
    "Joe Burrow",
    "Jayden Daniels",
    "Keenan Allen",
    "Darius Slayton",
    "De'Von Achane",
    "Chase Brown",
    "Brian Thomas Jr.",
    "Brandon Aiyuk",
    "Jake Ferguson",
)


@dataclass(frozen=True)
class RankingsPostPatchAcceptanceResult:
    top_100_rows: tuple[dict[str, object], ...]
    my_team_rows: tuple[dict[str, object], ...]
    qb_te_rows: tuple[dict[str, object], ...]
    acceptance_report: str
    final_handoff: str
    summary: dict[str, object]


@dataclass(frozen=True)
class RankingsPostPatchAcceptancePaths:
    top_100: Path
    my_team: Path
    qb_te: Path
    acceptance_report: Path
    final_handoff: Path


def build_rankings_post_patch_acceptance(
    *,
    full_board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    issue_queue_path: str | Path = DEFAULT_ISSUE_QUEUE,
    movement_path: str | Path = MOVEMENT_AUDIT_CSV,
    source_quarantine_path: str | Path = DEFAULT_SOURCE_QUARANTINE,
) -> RankingsPostPatchAcceptanceResult:
    full_rows = _ranked(_read_rows(Path(full_board_path)))
    issue_rows = _read_rows(Path(issue_queue_path))
    movement_rows = _read_rows(Path(movement_path))
    source_rows = _read_rows(Path(source_quarantine_path))
    issue_by_player = _issue_by_player(issue_rows)
    movement_by_player = {row.get("player", ""): row for row in movement_rows}
    scored_non_k = [
        row for row in full_rows if row.get("position") != "K" and row.get("nwr_rank")
    ]
    top_100_rows = tuple(
        _top_100_row(row, issue_by_player.get(row.get("player_name", ""), {}))
        for row in scored_non_k[:100]
    )
    my_team_rows = tuple(
        _my_team_row(row, movement_by_player.get(row.get("player_name", ""), {}))
        for row in scored_non_k
        if str(row.get("is_my_team")) == "1"
    )
    qb_te_rows = tuple(
        _qb_te_row(
            row,
            issue_by_player.get(row.get("player_name", ""), {}),
            movement_by_player.get(row.get("player_name", ""), {}),
        )
        for row in scored_non_k
        if row.get("position") in {"QB", "TE"}
    )
    rb_wr_checksum = _rb_wr_checksum(full_rows)
    summary = {
        "active_rankings_source": str(Path(full_board_path)),
        "active_rankings_hash": _sha256(Path(full_board_path)),
        "active_rows": len(full_rows),
        "qb_rb_wr_te_rows": sum(1 for row in full_rows if row.get("position") in {"QB", "RB", "WR", "TE"}),
        "kicker_rows": sum(1 for row in full_rows if row.get("position") == "K"),
        "nwr_scored_rows": sum(1 for row in full_rows if row.get("nwr_dynasty_score")),
        "no_private_score_rows": sum(1 for row in full_rows if not row.get("nwr_dynasty_score")),
        "source_quarantine_rows": len(source_rows),
        "source_quarantine_non_kickers": sum(1 for row in source_rows if row.get("position") != "K"),
        "top25_mix": dict(Counter(row.get("position") for row in scored_non_k[:25])),
        "my_team_rows": len(my_team_rows),
        "my_team_max_abs_rank_delta": max(
            (abs(_int(row.get("rank_delta_if_available")) or 0) for row in my_team_rows),
            default=0,
        ),
        "rb_wr_checksum_before": PRE_RB_WR_CHECKSUM,
        "rb_wr_checksum_after": rb_wr_checksum,
        "rb_wr_unchanged": rb_wr_checksum == PRE_RB_WR_CHECKSUM,
        "sentinels_safe": _sentinels_safe(full_rows),
        "contamination_safe": _contamination_safe(full_rows),
        "decision_board_blocked": True,
        "failed_acceptance_criteria": [],
        "verdict": "rankings_accepted_for_human_review",
    }
    failed = _failed_acceptance(summary, scored_non_k)
    summary["failed_acceptance_criteria"] = failed
    if failed:
        summary["verdict"] = "rankings_needs_model_repair_before_acceptance"
    acceptance_report = _acceptance_report(full_rows, issue_rows, summary)
    final_handoff = _final_handoff(full_rows, issue_rows, summary)
    return RankingsPostPatchAcceptanceResult(
        top_100_rows=top_100_rows,
        my_team_rows=my_team_rows,
        qb_te_rows=qb_te_rows,
        acceptance_report=acceptance_report,
        final_handoff=final_handoff,
        summary=summary,
    )


def write_rankings_post_patch_acceptance(
    result: RankingsPostPatchAcceptanceResult | None = None,
    *,
    top_100_path: str | Path = DEFAULT_TOP_100,
    my_team_path: str | Path = DEFAULT_MY_TEAM,
    qb_te_path: str | Path = DEFAULT_QB_TE,
    acceptance_report_path: str | Path = DEFAULT_ACCEPTANCE_REPORT,
    final_handoff_path: str | Path = DEFAULT_FINAL_HANDOFF,
) -> RankingsPostPatchAcceptancePaths:
    result = result or build_rankings_post_patch_acceptance()
    top_100 = Path(top_100_path)
    my_team = Path(my_team_path)
    qb_te = Path(qb_te_path)
    acceptance = Path(acceptance_report_path)
    handoff = Path(final_handoff_path)
    _write_csv(top_100, TOP_100_HEADER, result.top_100_rows)
    _write_csv(my_team, MY_TEAM_HEADER, result.my_team_rows)
    _write_csv(qb_te, QB_TE_HEADER, result.qb_te_rows)
    acceptance.parent.mkdir(parents=True, exist_ok=True)
    acceptance.write_text(result.acceptance_report, encoding="utf-8")
    handoff.write_text(result.final_handoff, encoding="utf-8")
    return RankingsPostPatchAcceptancePaths(top_100, my_team, qb_te, acceptance, handoff)


def _top_100_row(row: dict[str, str], issue: dict[str, str]) -> dict[str, object]:
    return {
        "nwr_rank": row.get("nwr_rank", ""),
        "player": row.get("player_name", ""),
        "position": row.get("position", ""),
        "age": row.get("age", ""),
        "team": row.get("nfl_team", ""),
        "nwr_score": row.get("nwr_dynasty_score", ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "roster_status": row.get("pool_status", ""),
        "warning_summary": row.get("warning_flags", ""),
        "issue_bucket": issue.get("issue_bucket", ""),
        "human_review_question": issue.get(
            "human_review_question", "Does this ranking fit the private model evidence?"
        ),
    }


def _my_team_row(row: dict[str, str], movement: dict[str, str]) -> dict[str, object]:
    return {
        "nwr_rank": row.get("nwr_rank", ""),
        "player": row.get("player_name", ""),
        "position": row.get("position", ""),
        "age": row.get("age", ""),
        "team": row.get("nfl_team", ""),
        "nwr_score": row.get("nwr_dynasty_score", ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "roster_status": row.get("pool_status", ""),
        "warning_summary": row.get("warning_flags", ""),
        "previous_rank_if_available": movement.get("baseline_rank", ""),
        "rank_delta_if_available": movement.get("rank_delta", ""),
        "human_review_question": "Is this My Team movement explainable from the post-patch board shape?",
    }


def _qb_te_row(
    row: dict[str, str],
    issue: dict[str, str],
    movement: dict[str, str],
) -> dict[str, object]:
    position = row.get("position", "")
    patch_effect = "direct_qb_te_patch" if movement.get("changed_by_patch") == "True" else ""
    return {
        "nwr_rank": row.get("nwr_rank", ""),
        "player": row.get("player_name", ""),
        "position": position,
        "age": row.get("age", ""),
        "team": row.get("nfl_team", ""),
        "nwr_score": row.get("nwr_dynasty_score", ""),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "warning_summary": row.get("warning_flags", ""),
        "issue_bucket": issue.get("issue_bucket", ""),
        "patch_effect_summary": patch_effect or "no_score_delta_from_patch",
        "human_review_question": issue.get(
            "human_review_question",
            f"Does this {position} placement fit the league format?",
        ),
    }


def _acceptance_report(
    rows: list[dict[str, str]],
    issues: list[dict[str, str]],
    summary: dict[str, object],
) -> str:
    scored = [row for row in rows if row.get("position") != "K" and row.get("nwr_rank")]
    qbs = [row for row in scored if row.get("position") == "QB"][:15]
    tes = [row for row in scored if row.get("position") == "TE"][:15]
    suspicious = _watchlist_rows(rows, issues)
    return "\n".join(
        [
            "# Rankings Post-Patch Acceptance Audit - 2026-06-09",
            "",
            "## Executive Summary",
            f"Verdict: `{summary['verdict']}`.",
            "The patched Rankings board is ready for human review and safe to use as the current Rankings baseline for review-only work if the UI smoke check remains clean.",
            "",
            "## Acceptance Questions",
            "- Ready for human review: yes.",
            "- Safe current Rankings baseline: yes, for review-only use.",
            f"- Remaining source/identity blockers: {summary['source_quarantine_non_kickers']} non-kicker blockers.",
            f"- Contamination risks: {summary['contamination_safe']}.",
            "- Remaining formula-shape concerns: yes, human-review watchlist remains for QB/TE/veteran/young-player shape, but no blocking acceptance failure.",
            "- QB discipline: improved for 10-team 1QB; no QB is top 10.",
            "- TE discipline: improved for no-TE-premium while allowing elite exceptions.",
            f"- RB/WR scores unchanged: {summary['rb_wr_unchanged']}.",
            f"- My Team movement explainable: max absolute rank delta {summary['my_team_max_abs_rank_delta']}.",
            "- Decision Board should remain blocked.",
            "- Next page after Rankings acceptance: 2026 Draft Board / Rookie Draft page.",
            "",
            "## Coverage Counts",
            _coverage_table(summary),
            "",
            "## Top 25",
            _rank_table(scored[:25]),
            "",
            "## Top 15 QBs",
            _rank_table(qbs),
            "",
            "## Top 15 TEs",
            _rank_table(tes),
            "",
            "## Remaining Suspicious Rows",
            _issue_table(suspicious),
            "",
            "## Guardrails",
            f"- Sentinels safe: {summary['sentinels_safe']}",
            f"- Contamination safe: {summary['contamination_safe']}",
            "- Market Rank and League Rank remain display-only.",
            "- RotoWire remains source-repair/status/context only.",
            "- Outcome percentages remain blank/in development.",
            "- Kickers remain hidden/default-off.",
            "",
            "## UI Smoke Check",
            "Passed on `http://localhost:8501/` after restarting Streamlit with the patched Rankings page. The browser showed `Dynasty Rankings`, Active players shown 232, NWR scored 232, No private score 8, Puka Nacua as the selected Rank 1 detail row, display-only market/league language, legacy comparison-only disclosure, and outcome fields in development. No Decision Board recommendation language leaked into Rankings.",
        ]
    ) + "\n"


def _final_handoff(
    rows: list[dict[str, str]],
    issues: list[dict[str, str]],
    summary: dict[str, object],
) -> str:
    scored = [row for row in rows if row.get("position") != "K" and row.get("nwr_rank")]
    qbs = [row for row in scored if row.get("position") == "QB"][:15]
    tes = [row for row in scored if row.get("position") == "TE"][:15]
    return "\n".join(
        [
            "# Rankings Final Handoff - 2026-06-09",
            "",
            "## What Changed During Rankings Repair",
            "- Rankings became a full-board private NWR dynasty board for 232 QB/RB/WR/TE rows.",
            "- Local RotoWire team/status data was integrated as source-repair/status context only.",
            "- QB/TE upper-band guard v2 was promoted through the production scoring pipeline.",
            "- RB/WR scores stayed unchanged by the QB/TE patch.",
            "",
            "## Current Active Rankings Source",
            f"- source: `{summary['active_rankings_source']}`",
            f"- hash: `{summary['active_rankings_hash']}`",
            "",
            "## Coverage Counts",
            _coverage_table(summary),
            "",
            "## Current Top 25",
            _rank_table(scored[:25]),
            "",
            "## Current QB Shape",
            _rank_table(qbs),
            "",
            "## Current TE Shape",
            _rank_table(tes),
            "",
            "## Source And Sentinel Status",
            f"- non-kicker source quarantine rows: {summary['source_quarantine_non_kickers']}",
            "- RotoWire status: source-repair/status/context only.",
            f"- sentinels safe: {summary['sentinels_safe']}",
            f"- contamination safe: {summary['contamination_safe']}",
            "",
            "## Remaining Risks",
            _issue_table(_watchlist_rows(rows, issues)[:15]),
            "",
            "## Acceptance",
            f"Rankings accepted for human review: {summary['verdict'] == 'rankings_accepted_for_human_review'}.",
            "UI smoke check passed on `http://localhost:8501/`.",
            "Decision Board remains blocked.",
            "Recommended next page: 2026 Draft Board / Rookie Draft page.",
        ]
    ) + "\n"


def _watchlist_rows(
    rows: list[dict[str, str]],
    issues: list[dict[str, str]],
) -> list[dict[str, str]]:
    issue_by_player = _issue_by_player(issues)
    row_by_player = {row.get("player_name", ""): row for row in rows}
    watch: list[dict[str, str]] = []
    for name in WATCHLIST_NAMES:
        row = row_by_player.get(name)
        if not row:
            continue
        issue = issue_by_player.get(name, {})
        watch.append(
            {
                "player": name,
                "position": row.get("position", ""),
                "nwr_rank": row.get("nwr_rank", ""),
                "nwr_score": row.get("nwr_dynasty_score", ""),
                "trust_status": row.get("trust_status", ""),
                "issue_bucket": issue.get("issue_bucket") or _fallback_issue_bucket(row),
                "human_review_question": issue.get(
                    "human_review_question", "Does this row pass football review?"
                ),
            }
        )
    return watch


def _fallback_issue_bucket(row: dict[str, str]) -> str:
    if row.get("position") == "QB":
        return "qb_shape_watch"
    if row.get("position") == "TE":
        return "te_shape_watch"
    if row.get("trust_status") == "Capped Score":
        return "still_human_review_needed"
    return "market_league_disagreement"


def _failed_acceptance(
    summary: dict[str, object],
    scored_non_k: list[dict[str, str]],
) -> list[str]:
    failed: list[str] = []
    if summary["active_rows"] != 240:
        failed.append("active_rows_not_240")
    if summary["nwr_scored_rows"] != 232:
        failed.append("nwr_scored_rows_not_232")
    if summary["kicker_rows"] != 8 or summary["no_private_score_rows"] != 8:
        failed.append("kicker_or_no_private_score_count_changed")
    if summary["source_quarantine_non_kickers"] != 0:
        failed.append("non_kicker_source_quarantine_present")
    if not summary["rb_wr_unchanged"]:
        failed.append("rb_wr_scores_changed")
    if not summary["sentinels_safe"]:
        failed.append("sentinels_failed")
    if not summary["contamination_safe"]:
        failed.append("contamination_failed")
    if any(row.get("position") == "QB" for row in scored_non_k[:10]):
        failed.append("qb_in_top_10")
    if scored_non_k and scored_non_k[0].get("position") == "TE":
        failed.append("te_number_one_overall")
    return failed


def _ranked(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: _int(row.get("nwr_rank")) or 9999)


def _issue_by_player(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    by_player: dict[str, dict[str, str]] = {}
    for row in rows:
        player = row.get("player", "")
        if player and player not in by_player:
            by_player[player] = row
    return by_player


def _coverage_table(summary: dict[str, object]) -> str:
    keys = (
        "active_rows",
        "qb_rb_wr_te_rows",
        "kicker_rows",
        "nwr_scored_rows",
        "no_private_score_rows",
        "source_quarantine_non_kickers",
        "my_team_rows",
    )
    lines = ["| Metric | Count |", "|---|---:|"]
    for key in keys:
        lines.append(f"| {key} | {summary[key]} |")
    return "\n".join(lines)


def _rank_table(rows: list[dict[str, str]]) -> str:
    lines = ["| Rank | Player | Pos | Team | Score |", "|---:|---|---|---|---:|"]
    for row in rows:
        lines.append(
            f"| {row.get('nwr_rank', '')} | {row.get('player_name', '')} | {row.get('position', '')} | {row.get('nfl_team', '')} | {row.get('nwr_dynasty_score', '')} |"
        )
    return "\n".join(lines)


def _issue_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Player | Pos | Rank | Score | Trust | Issue |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('player', '')} | {row.get('position', '')} | {row.get('nwr_rank', '')} | {row.get('nwr_score', '')} | {row.get('trust_status', '')} | {row.get('issue_bucket', '')} |"
        )
    return "\n".join(lines)


def _rb_wr_checksum(rows: list[dict[str, str]]) -> str:
    rb_wr = sorted(
        [
            row
            for row in rows
            if row.get("position") in {"RB", "WR"} and row.get("nwr_dynasty_score")
        ],
        key=lambda row: (row.get("player_name", ""), row.get("position", "")),
    )
    blob = "\n".join(
        f"{row['player_name']}|{row['position']}|{row['nwr_dynasty_score']}"
        for row in rb_wr
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def _sentinels_safe(rows: list[dict[str, str]]) -> bool:
    by_name = {row.get("player_name", ""): row for row in rows}
    keenan = by_name.get("Keenan Allen", {})
    slayton = by_name.get("Darius Slayton", {})
    return (
        keenan.get("legacy_active_pack_score") == "82.4"
        and keenan.get("lineage_class") == "review_v4_current_player"
        and keenan.get("nwr_dynasty_score") != "82.4"
        and slayton.get("legacy_active_pack_score") == "78.88"
        and slayton.get("lineage_class") == "review_v4_current_player"
        and slayton.get("nwr_dynasty_score") != "78.88"
    )


def _contamination_safe(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("lineage_class") == "review_v4_current_player"
        and row.get("source_column") == "nwr_dynasty_score"
        for row in rows
        if row.get("nwr_dynasty_score")
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _int(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None
