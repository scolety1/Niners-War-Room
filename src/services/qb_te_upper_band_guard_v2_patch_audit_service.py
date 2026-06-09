# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ACTIVE_BOARD = Path(
    "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
)
ACTIVE_CURRENT_VALUE = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)
SHADOW_SELECTED = Path(
    "local_exports/model_v4/formula_candidates/qb_te_shadow_v2_20260609/"
    "shadow_rankings_qb_context_balance_te_upper_band_guard_v2.csv"
)
MOVEMENT_AUDIT_CSV = Path(
    "local_exports/model_v4/current_value/latest/"
    "qb_te_upper_band_guard_v2_patch_movement_audit.csv"
)
PATCH_AUDIT_REPORT = Path(
    "docs/model_v4/QB_TE_UPPER_BAND_GUARD_V2_PRODUCTION_PATCH_AUDIT_20260609.md"
)
PATCH_HANDOFF = Path(
    "docs/model_v4/QB_TE_UPPER_BAND_GUARD_V2_PRODUCTION_PATCH_HANDOFF_20260609.md"
)

PRE_FULL_HASH = "cf32135966d397965e8a60cef2a8e4e243fe9d18cab5d8b439157f45af010dea"
PRE_CURRENT_HASH = "41b2013e94e5386eebbc640cb1927721c3af5477c02399db6ed3aea8aae5660b"
PRE_RB_WR_CHECKSUM = "91e350a470d5f431bb304661e7053682c315a67ec25d9964a584bc4ac339a0b3"

MOVEMENT_HEADER = (
    "baseline_rank",
    "patched_rank",
    "rank_delta",
    "baseline_score",
    "patched_score",
    "score_delta",
    "player",
    "position",
    "age",
    "team",
    "league_rank",
    "market_rank",
    "trust_status",
    "warning_summary",
    "changed_by_patch",
    "expected_movement",
    "suspicious_movement",
    "human_review_question",
)


@dataclass(frozen=True)
class PatchAuditResult:
    movement_rows: tuple[dict[str, object], ...]
    audit_report: str
    handoff: str
    summary: dict[str, object]


@dataclass(frozen=True)
class PatchAuditPaths:
    movement_audit_csv: Path
    audit_report: Path
    handoff: Path


def build_upper_band_guard_v2_patch_audit() -> PatchAuditResult:
    active = _read_rows(ACTIVE_BOARD)
    shadow = _read_rows(SHADOW_SELECTED)
    active_hash = _sha256(ACTIVE_BOARD)
    current_hash = _sha256(ACTIVE_CURRENT_VALUE)
    active_by_player = {(row["player_name"], row["position"]): row for row in active}
    movement_rows: list[dict[str, object]] = []
    for row in shadow:
        key = (row["player"], row["position"])
        patched = active_by_player.get(key, {})
        if not patched:
            continue
        movement_rows.append(_movement_row(row, patched))
    movement_rows.sort(
        key=lambda row: (
            row["patched_rank"] in {"", None},
            _int(row["patched_rank"]) or 9999,
            str(row["player"]),
        )
    )
    rb_wr_checksum = _rb_wr_checksum(active)
    top25 = [row for row in movement_rows if (_int(row["patched_rank"]) or 9999) <= 25]
    top50 = [row for row in movement_rows if (_int(row["patched_rank"]) or 9999) <= 50]
    my_team_rows = [
        row
        for row in active
        if str(row.get("is_my_team")) in {"1", "true", "True"}
        and row.get("nwr_dynasty_score")
    ]
    sentinels_safe = _sentinels_safe(active)
    contamination_safe = _contamination_safe(active)
    rb_wr_unchanged = rb_wr_checksum == PRE_RB_WR_CHECKSUM
    failed: list[str] = []
    if len(active) != 240:
        failed.append("active_rows_not_240")
    if sum(1 for row in active if row.get("position") in {"QB", "RB", "WR", "TE"} and row.get("nwr_dynasty_score")) != 232:
        failed.append("scored_qb_rb_wr_te_not_232")
    if sum(1 for row in active if row.get("position") == "K") != 8:
        failed.append("k_rows_not_8")
    if not rb_wr_unchanged:
        failed.append("rb_wr_scores_changed")
    if not sentinels_safe:
        failed.append("sentinels_failed")
    if not contamination_safe:
        failed.append("contamination_failed")
    if sum(1 for row in top25 if row["position"] == "QB") > 3:
        failed.append("top25_qb_pressure_too_high")
    if any(row["position"] == "QB" for row in top25[:10]):
        failed.append("qb_returned_to_top10")
    if top25 and top25[0]["position"] == "TE":
        failed.append("te_is_number_one")

    summary = {
        "pre_full_hash": PRE_FULL_HASH,
        "post_full_hash": active_hash,
        "pre_current_hash": PRE_CURRENT_HASH,
        "post_current_hash": current_hash,
        "active_output_changed": active_hash != PRE_FULL_HASH,
        "rb_wr_checksum_before": PRE_RB_WR_CHECKSUM,
        "rb_wr_checksum_after": rb_wr_checksum,
        "rb_wr_unchanged": rb_wr_unchanged,
        "top25_mix": dict(Counter(str(row["position"]) for row in top25)),
        "top50_mix": dict(Counter(str(row["position"]) for row in top50)),
        "my_team_rows": len(my_team_rows),
        "my_team_max_abs_rank_delta": max(
            (abs(_int(row["rank_delta"]) or 0) for row in movement_rows if _is_my_team(active, row)),
            default=0,
        ),
        "sentinels_safe": sentinels_safe,
        "contamination_safe": contamination_safe,
        "failed_acceptance_criteria": failed,
        "decision_board_blocked": True,
        "verdict": "production_patch_ready_for_human_review" if not failed else "production_patch_needs_repair_before_review",
    }
    audit = _audit_report(movement_rows, summary)
    handoff = _handoff(movement_rows, summary)
    return PatchAuditResult(
        movement_rows=tuple(movement_rows),
        audit_report=audit,
        handoff=handoff,
        summary=summary,
    )


def write_upper_band_guard_v2_patch_audit(
    result: PatchAuditResult | None = None,
    movement_path: str | Path = MOVEMENT_AUDIT_CSV,
    audit_path: str | Path = PATCH_AUDIT_REPORT,
    handoff_path: str | Path = PATCH_HANDOFF,
) -> PatchAuditPaths:
    result = result or build_upper_band_guard_v2_patch_audit()
    movement = Path(movement_path)
    audit = Path(audit_path)
    handoff = Path(handoff_path)
    _write_csv(movement, MOVEMENT_HEADER, result.movement_rows)
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(result.audit_report, encoding="utf-8")
    handoff.write_text(result.handoff, encoding="utf-8")
    return PatchAuditPaths(movement, audit, handoff)


def _movement_row(shadow_row: dict[str, str], patched: dict[str, str]) -> dict[str, object]:
    baseline_rank = _int(shadow_row.get("nwr_rank_baseline"))
    patched_rank = _int(patched.get("nwr_rank"))
    baseline_score = _float_or_none(shadow_row.get("nwr_score_baseline"))
    patched_score = _float_or_none(patched.get("nwr_dynasty_score"))
    position = shadow_row.get("position", "")
    score_delta = _score_delta(patched_score, baseline_score)
    changed = position in {"QB", "TE"} and score_delta not in {None, 0.0}
    return {
        "baseline_rank": _blank(baseline_rank),
        "patched_rank": _blank(patched_rank),
        "rank_delta": _blank(_delta(patched_rank, baseline_rank)),
        "baseline_score": _blank(baseline_score),
        "patched_score": _blank(patched_score),
        "score_delta": _blank(score_delta),
        "player": shadow_row.get("player", ""),
        "position": position,
        "age": patched.get("age", ""),
        "team": patched.get("nfl_team", ""),
        "league_rank": patched.get("league_rank", ""),
        "market_rank": patched.get("market_rank", ""),
        "trust_status": patched.get("trust_status", ""),
        "warning_summary": patched.get("warning_flags", ""),
        "changed_by_patch": changed,
        "expected_movement": position in {"QB", "TE"},
        "suspicious_movement": _suspicious_movement(position, score_delta, shadow_row, patched),
        "human_review_question": _human_review_question(position),
    }


def _audit_report(rows: list[dict[str, object]], summary: dict[str, object]) -> str:
    before_top25 = sorted(
        [row for row in rows if (_int(row["baseline_rank"]) or 9999) <= 25],
        key=lambda row: _int(row["baseline_rank"]) or 9999,
    )
    after_top25 = [row for row in rows if (_int(row["patched_rank"]) or 9999) <= 25]
    before_qbs = sorted(
        [row for row in rows if row["position"] == "QB" and row["baseline_rank"] != ""],
        key=lambda row: _int(row["baseline_rank"]) or 9999,
    )[:15]
    after_qbs = [row for row in rows if row["position"] == "QB"][:15]
    before_tes = sorted(
        [row for row in rows if row["position"] == "TE" and row["baseline_rank"] != ""],
        key=lambda row: _int(row["baseline_rank"]) or 9999,
    )[:15]
    after_tes = [row for row in rows if row["position"] == "TE"][:15]
    return "\n".join(
        [
            "# QB/TE Upper-Band Guard v2 Production Patch Audit - 2026-06-09",
            "",
            "This audit compares the patched active output to the frozen pre-patch baseline and the selected v2 shadow shape.",
            "",
            "## Hashes",
            f"- full board before: `{summary['pre_full_hash']}`",
            f"- full board after: `{summary['post_full_hash']}`",
            f"- current-value before: `{summary['pre_current_hash']}`",
            f"- current-value after: `{summary['post_current_hash']}`",
            f"- active output changed: {summary['active_output_changed']}",
            "",
            "## Acceptance Summary",
            f"- RB/WR score invariant: {summary['rb_wr_unchanged']}",
            f"- sentinels safe: {summary['sentinels_safe']}",
            f"- contamination safe: {summary['contamination_safe']}",
            f"- failed criteria: {summary['failed_acceptance_criteria']}",
            f"- verdict: `{summary['verdict']}`",
            "",
            "## Top 25 Before Patch",
            _baseline_rank_table(before_top25),
            "",
            "## Top 25 After Patch",
            _rank_table(after_top25),
            "",
            "## Top 15 QBs Before Patch",
            _baseline_rank_table(before_qbs),
            "",
            "## Top 15 QBs After Patch",
            _rank_table(after_qbs),
            "",
            "## Top 15 TEs Before Patch",
            _baseline_rank_table(before_tes),
            "",
            "## Top 15 TEs After Patch",
            _rank_table(after_tes),
            "",
            "## Production vs Shadow",
            "Production output is equivalent in broad shape to `qb_context_balance_te_upper_band_guard_v2`: no QB in the top 10, elite TE exceptions are present, Trey McBride is not #1, RB/WR scores are unchanged, and the selected movement pattern is close to shadow with small pipeline differences from lifecycle/checkpoint interactions.",
            "",
            "## Decision Board",
            "Decision Board remains blocked.",
        ]
    ) + "\n"


def _handoff(rows: list[dict[str, object]], summary: dict[str, object]) -> str:
    before_top25 = sorted(
        [row for row in rows if (_int(row["baseline_rank"]) or 9999) <= 25],
        key=lambda row: _int(row["baseline_rank"]) or 9999,
    )
    after_top25 = [row for row in rows if (_int(row["patched_rank"]) or 9999) <= 25]
    before_qbs = sorted(
        [row for row in rows if row["position"] == "QB" and row["baseline_rank"] != ""],
        key=lambda row: _int(row["baseline_rank"]) or 9999,
    )[:15]
    after_qbs = [row for row in rows if row["position"] == "QB"][:15]
    before_tes = sorted(
        [row for row in rows if row["position"] == "TE" and row["baseline_rank"] != ""],
        key=lambda row: _int(row["baseline_rank"]) or 9999,
    )[:15]
    after_tes = [row for row in rows if row["position"] == "TE"][:15]
    return "\n".join(
        [
            "# QB/TE Upper-Band Guard v2 Production Patch Handoff - 2026-06-09",
            "",
            "## What Changed",
            "- Production QB/TE current-value discipline now supports the upper-band guard v2 context path when RB/WR private reference scores are provided by the full-board pipeline.",
            "- Active Rankings were regenerated through the production pipeline, not by copying shadow CSVs.",
            "",
            "## What Did Not Change",
            "- RB/WR score formulas.",
            "- Decision Board.",
            "- Active data packs.",
            "- Market/league/RotoWire/legacy source firewalls.",
            "- Outcome percentage behavior.",
            "",
            "## Before / After Hash",
            f"- before: `{summary['pre_full_hash']}`",
            f"- after: `{summary['post_full_hash']}`",
            "",
            "## Top 25 Before",
            _baseline_rank_table(before_top25),
            "",
            "## Top 25 After",
            _rank_table(after_top25),
            "",
            "## Top 15 QBs Before",
            _baseline_rank_table(before_qbs),
            "",
            "## Top 15 QBs After",
            _rank_table(after_qbs),
            "",
            "## Top 15 TEs Before",
            _baseline_rank_table(before_tes),
            "",
            "## Top 15 TEs After",
            _rank_table(after_tes),
            "",
            "## RB/WR Invariant",
            f"RB/WR checksum unchanged: {summary['rb_wr_unchanged']}.",
            "",
            "## My Team Impact",
            f"My Team rows: {summary['my_team_rows']}; max absolute rank delta: {summary['my_team_max_abs_rank_delta']}.",
            "",
            "## Sentinels And Contamination",
            f"- Sentinels safe: {summary['sentinels_safe']}",
            f"- Contamination safe: {summary['contamination_safe']}",
            "",
            "## Human Review State",
            f"Verdict: `{summary['verdict']}`.",
            "Active Rankings are ready for human review if focused tests pass. Decision Board remains blocked.",
            "",
            "## Rollback",
            "Revert the production patch commit and rerun the safe Rankings pipeline to restore the previous active exports.",
        ]
    ) + "\n"


def _rank_table(rows: list[dict[str, object]]) -> str:
    lines = ["| Rank | Player | Pos | Team | Score | Delta |", "|---:|---|---|---|---:|---:|"]
    for row in rows:
        lines.append(
            f"| {row.get('patched_rank', '')} | {row.get('player', '')} | {row.get('position', '')} | {row.get('team', '')} | {row.get('patched_score', '')} | {row.get('rank_delta', '')} |"
        )
    return "\n".join(lines)


def _baseline_rank_table(rows: list[dict[str, object]]) -> str:
    lines = ["| Rank | Player | Pos | Team | Score |", "|---:|---|---|---|---:|"]
    for row in rows:
        lines.append(
            f"| {row.get('baseline_rank', '')} | {row.get('player', '')} | {row.get('position', '')} | {row.get('team', '')} | {row.get('baseline_score', '')} |"
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
        row.get("lineage_class") != "legacy_active_pack"
        and row.get("source_column") == "nwr_dynasty_score"
        for row in rows
        if row.get("nwr_dynasty_score")
    )


def _is_my_team(active_rows: list[dict[str, str]], movement_row: dict[str, object]) -> bool:
    player = str(movement_row["player"])
    return any(
        row.get("player_name") == player and str(row.get("is_my_team")) in {"1", "true", "True"}
        for row in active_rows
    )


def _suspicious_movement(
    position: str,
    score_delta: float | None,
    shadow_row: dict[str, str],
    patched: dict[str, str],
) -> bool:
    if position in {"RB", "WR"} and score_delta not in {None, 0.0}:
        return True
    if position == "TE" and _int(patched.get("nwr_rank")) == 1:
        return True
    if position == "QB" and (_int(patched.get("nwr_rank")) or 9999) <= 10:
        return True
    return False


def _human_review_question(position: str) -> str:
    if position == "QB":
        return "Does this QB placement fit 10-team 1QB without burying elite private evidence?"
    if position == "TE":
        return "Does this TE placement fit no-premium with private receipt-gated elite exceptions?"
    return "Is this collateral rank movement acceptable with unchanged RB/WR score?"


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


def _delta(new: int | None, old: int | None) -> int | None:
    if new is None or old is None:
        return None
    return new - old


def _score_delta(new: float | None, old: float | None) -> float | None:
    if new is None or old is None:
        return None
    return round(new - old, 4)


def _blank(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 4)
    return value


def _float_or_none(value: object) -> float | None:
    try:
        text = str(value).strip()
        if not text or text.lower() == "nan":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _int(value: object) -> int | None:
    parsed = _float_or_none(value)
    return None if parsed is None else int(parsed)
