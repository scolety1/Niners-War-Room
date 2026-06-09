from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

MISS_PATTERN_SUMMARY_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/mature_miss_pattern_summary.csv"
)
MISS_PATTERN_ROWS_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/mature_miss_pattern_rows.csv"
)
BASELINE_SUMMARY_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/rookie_replay_baseline_summary.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/historical_rookie_tuning/latest")
DOC_PATH = Path("docs/model_v4/MODEL_V4_3_6_ROOKIE_CALIBRATION_CANDIDATE_PLAN.md")
VERSION = "model_v4_3_6_rookie_calibration_candidate_plan_0.1.0"

CANDIDATE_HEADER = (
    "candidate_id",
    "candidate_test",
    "priority",
    "candidate_type",
    "reason",
    "supporting_pattern_groups",
    "evidence_rows",
    "affected_players",
    "expected_impact",
    "risks",
    "pass_fail_criteria",
    "implementation_status",
    "formula_version",
)


@dataclass(frozen=True)
class RookieCalibrationCandidatePlanResult:
    candidate_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_rookie_calibration_candidate_plan(
    miss_pattern_summary_path: str | Path = MISS_PATTERN_SUMMARY_PATH,
    miss_pattern_rows_path: str | Path = MISS_PATTERN_ROWS_PATH,
    baseline_summary_path: str | Path = BASELINE_SUMMARY_PATH,
) -> RookieCalibrationCandidatePlanResult:
    miss_summary = _read_rows(Path(miss_pattern_summary_path))
    miss_rows = _read_rows(Path(miss_pattern_rows_path))
    baseline_summary = _read_rows(Path(baseline_summary_path))
    patterns = {row["pattern_group"]: row for row in miss_summary}
    rows_by_pattern = _rows_by_pattern(miss_rows)
    baseline_read = _baseline_read(baseline_summary)
    candidates = tuple(
        _candidate_rows(
            patterns=patterns,
            rows_by_pattern=rows_by_pattern,
            baseline_read=baseline_read,
        )
    )
    return RookieCalibrationCandidatePlanResult(
        candidate_rows=candidates,
        doc_text=_doc_text(candidates, baseline_read),
    )


def write_rookie_calibration_candidate_plan_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: RookieCalibrationCandidatePlanResult | None = None,
) -> dict[str, Path]:
    result = result or build_rookie_calibration_candidate_plan()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    candidate_path = output / "rookie_calibration_candidate_tests.csv"
    _write_csv(candidate_path, CANDIDATE_HEADER, result.candidate_rows)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(result.doc_text, encoding="utf-8")
    return {"candidates": candidate_path, "doc": doc}


def _candidate_rows(
    *,
    patterns: dict[str, dict[str, str]],
    rows_by_pattern: dict[str, list[dict[str, str]]],
    baseline_read: dict[str, object],
) -> list[dict[str, object]]:
    return [
        _row(
            candidate_id="C01",
            candidate_test="capital_anchor_rebalance",
            priority="critical",
            candidate_type="shadow_formula_variant",
            reason=(
                "Current model trails draft-capital-only in mature Top 20 replay; deep "
                "research says NFL Draft capital should be the base-rate anchor."
            ),
            groups=("high_ranked_misses", "first_round_wr_underranks"),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Reduce broad and strict miss rate from profiles lifted by secondary "
                "signals while preserving premium NFL-capital floors."
            ),
            risks=("Could suppress useful model edge if capital is treated as the only signal."),
            pass_fail=(
                "Pass if shadow Top 20 strict starter hit rate exceeds current model and "
                "is not worse than draft-capital-only by more than 0.02; fail if "
                "difference-maker capture falls below current model."
            ),
        ),
        _row(
            candidate_id="C02",
            candidate_test="stronger_day_three_wr_skepticism",
            priority="high",
            candidate_type="shadow_formula_variant",
            reason=(
                "Late-capital production false positives appear in mature replay, and deep "
                "research warns that Day 3 WR hits are rare tail outcomes."
            ),
            groups=("late_capital_production_false_positives",),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Move Day 3 WR/RB production spikes into tail-bet labels unless the profile "
                "has exceptional supporting evidence."
            ),
            risks=("Could bury rare Puka/Amon-Ra style outliers if the penalty is too blunt."),
            pass_fail=(
                "Pass if high-ranked miss count drops without reducing low-ranked "
                "difference-maker capture; fail if Amon-Ra/Puka archetypes become invisible."
            ),
        ),
        _row(
            candidate_id="C03",
            candidate_test="first_round_wr_floor_refinement",
            priority="high",
            candidate_type="shadow_formula_variant",
            reason=(
                "First-round WR underranks repeat in mature replay, especially players who "
                "became useful or starter-level outcomes despite imperfect college-share shapes."
            ),
            groups=("first_round_wr_underranks",),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Keep Round 1 WRs from falling behind weaker-capital profiles solely because "
                "team share or production context is incomplete."
            ),
            risks=(
                "Could overprotect Kadarius Toney/Rashod Bateman-type misses if floor ignores "
                "evidence quality."
            ),
            pass_fail=(
                "Pass if Round 1 WR strict/broad capture improves while high-ranked Round 1 "
                "WR misses do not increase; fail if capital-only behavior is simply copied."
            ),
        ),
        _row(
            candidate_id="C04",
            candidate_test="rb_receiving_workhorse_modifier",
            priority="medium",
            candidate_type="shadow_formula_variant",
            reason=(
                "Deep research says RBs can beat capital more often than WRs when receiving "
                "and workload evidence are strong; mature replay found Day 3 RB hits "
                "worth preserving."
            ),
            groups=("day_three_rb_hits_worth_preserving", "low_ranked_strict_starter_hits"),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Protect Rhamondre/Kyren/Dameon/Chase Brown archetypes from being erased by "
                "a broad capital anchor."
            ),
            risks=("Could recreate production overpromotion if rushing-only volume is rewarded."),
            pass_fail=(
                "Pass if late RB starter hits remain captured while late-capital false positives "
                "do not rise; fail if rushing-only profiles jump without receiving/workhorse "
                "evidence."
            ),
        ),
        _row(
            candidate_id="C05",
            candidate_test="no_premium_te_cap_refinement",
            priority="medium",
            candidate_type="shadow_formula_variant",
            reason=(
                "TE overpromotion and underpromotion both appear; no-premium format needs a cap "
                "with rare exceptions for high-capital receiving engines."
            ),
            groups=("te_overpromotion", "te_underpromotion"),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Lower ordinary TE profiles while preserving Bowers/LaPorta/McBride-style "
                "exceptions."
            ),
            risks=(
                "Could make the model blind to elite TE difference-makers if the cap is too hard."
            ),
            pass_fail=(
                "Pass if TE overpromotion rows fall and TE underpromotion rows do not increase; "
                "fail if elite TE exceptions drop below reasonable draft windows."
            ),
        ),
        _row(
            candidate_id="C06",
            candidate_test="one_qb_qb_cap_check",
            priority="medium",
            candidate_type="shadow_formula_variant",
            reason=(
                "1QB discipline is mostly present, but Trey Lance overpromotion and several QB "
                "underpromotions show the cap needs calibration rather than a blanket rule."
            ),
            groups=("qb_overpromotion", "qb_underpromotion"),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Keep speculative QBs out of premium rookie windows while allowing true "
                "VORP/rushing profiles to remain visible."
            ),
            risks=("Could overcorrect against Stroud/Daniels-style pocket/rushing outliers."),
            pass_fail=(
                "Pass if QB overpromotion stays at or below current level and elite QB "
                "outcomes remain visible as review candidates; fail if QBs crowd out RB/WR again."
            ),
        ),
        _row(
            candidate_id="C07",
            candidate_test="stricter_low_evidence_confidence_cap",
            priority="critical",
            candidate_type="shadow_formula_variant",
            reason=(
                "Low-evidence overpromotion is the cleanest data-side warning, and Stage 2 shows "
                "current model loses to draft capital-only despite many low-evidence "
                "top-board rows."
            ),
            groups=("low_evidence_overpromotion", "high_ranked_misses"),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Force incomplete profiles to stay below better-supported profiles unless "
                "draft capital or multiple admitted signals justify the rank."
            ),
            risks=(
                "Could punish historical rows with missing pre-draft data rather than true "
                "weak evidence."
            ),
            pass_fail=(
                "Pass if high-ranked misses and low-evidence overpromotion fall while known "
                "difference-makers with missing historical fields remain review-visible; fail "
                "if missing-source artifacts dominate."
            ),
        ),
        _row(
            candidate_id="C08",
            candidate_test="simple_hybrid_benchmark_guardrail",
            priority="high",
            candidate_type="evaluation_gate",
            reason=(
                "Simple hybrid capital plus production beat current model on mature Top 20 "
                "strict starter rate and difference-maker count."
            ),
            groups=("high_ranked_misses", "low_ranked_difference_makers"),
            rows_by_pattern=rows_by_pattern,
            expected_impact=(
                "Prevent future shadow variants from being accepted unless they beat simple "
                "baselines."
            ),
            risks=(
                "A simple hybrid can still miss position-specific nuance and should not "
                "become the final model."
            ),
            pass_fail=(
                "Pass if any accepted variant beats current model and simple hybrid on target "
                "metrics; fail if it only improves one metric by sacrificing difference-maker "
                "capture."
            ),
        ),
    ]


def _row(
    *,
    candidate_id: str,
    candidate_test: str,
    priority: str,
    candidate_type: str,
    reason: str,
    groups: tuple[str, ...],
    rows_by_pattern: dict[str, list[dict[str, str]]],
    expected_impact: str,
    risks: str,
    pass_fail: str,
) -> dict[str, object]:
    evidence_rows = sum(len(rows_by_pattern.get(group, [])) for group in groups)
    players = _players_for_groups(groups, rows_by_pattern)
    return {
        "candidate_id": candidate_id,
        "candidate_test": candidate_test,
        "priority": priority,
        "candidate_type": candidate_type,
        "reason": reason,
        "supporting_pattern_groups": "|".join(groups),
        "evidence_rows": evidence_rows,
        "affected_players": ", ".join(players),
        "expected_impact": expected_impact,
        "risks": risks,
        "pass_fail_criteria": pass_fail,
        "implementation_status": "not_implemented_review_only_candidate",
        "formula_version": VERSION,
    }


def _players_for_groups(
    groups: tuple[str, ...],
    rows_by_pattern: dict[str, list[dict[str, str]]],
) -> list[str]:
    players: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for row in rows_by_pattern.get(group, []):
            player = row.get("player", "")
            if player and player not in seen:
                seen.add(player)
                players.append(player)
            if len(players) >= 10:
                return players
    return players


def _rows_by_pattern(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["pattern_group"]].append(row)
    return grouped


def _baseline_read(rows: list[dict[str, str]]) -> dict[str, object]:
    aggregate = {
        (row["baseline_name"], row["window"]): row
        for row in rows
        if row.get("draft_year") == "all_mature_years"
    }
    current = aggregate.get(("current_model_score", "Top 20"), {})
    draft = aggregate.get(("draft_capital_only", "Top 20"), {})
    hybrid = aggregate.get(("simple_hybrid_capital_plus_production", "Top 20"), {})
    return {
        "current_top20_strict": current.get("strict_starter_hit_rate", ""),
        "draft_top20_strict": draft.get("strict_starter_hit_rate", ""),
        "hybrid_top20_strict": hybrid.get("strict_starter_hit_rate", ""),
        "current_top20_difference_makers": current.get("difference_makers", ""),
        "draft_top20_difference_makers": draft.get("difference_makers", ""),
        "hybrid_top20_difference_makers": hybrid.get("difference_makers", ""),
    }


def _doc_text(
    candidates: tuple[dict[str, object], ...],
    baseline_read: dict[str, object],
) -> str:
    lines = [
        "# Model v4.3.6 Rookie Calibration Candidate Plan",
        "",
        "## Scope",
        "",
        "This document converts mature replay miss patterns and baseline comparisons into "
        "candidate shadow tests. It does not implement or promote formula changes.",
        "",
        "## Baseline Read",
        "",
        f"- Current model Top 20 strict starter rate: {baseline_read['current_top20_strict']}",
        f"- Draft-capital-only Top 20 strict starter rate: {baseline_read['draft_top20_strict']}",
        f"- Simple hybrid Top 20 strict starter rate: {baseline_read['hybrid_top20_strict']}",
        "- Current model Top 20 difference makers: "
        f"{baseline_read['current_top20_difference_makers']}",
        "- Draft-capital-only Top 20 difference makers: "
        f"{baseline_read['draft_top20_difference_makers']}",
        "- Simple hybrid Top 20 difference makers: "
        f"{baseline_read['hybrid_top20_difference_makers']}",
        "",
        "## Candidate Tests",
        "",
        "| ID | Candidate | Priority | Evidence Rows | Status |",
        "|---|---|---|---:|---|",
    ]
    for row in candidates:
        lines.append(
            "| {candidate_id} | {candidate_test} | {priority} | {evidence_rows} | "
            "{implementation_status} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "Do not tune live formulas yet. The next approved work should be a shadow-only "
            "formula experiment that includes capital anchoring and stricter confidence caps, "
            "then compares every variant against draft-capital-only and simple-hybrid baselines.",
            "",
            "## Guardrails",
            "",
            "- No candidate is implemented in this stage.",
            "- No active rankings, My Team, War Board, readiness gates, or app promotion changed.",
            "- Market, ADP, rankings, projections, mock drafts, and big boards remain excluded "
            "from private value.",
            "- Useful model weirdness should be preserved only when it beats simple baselines.",
        ]
    )
    return "\n".join(lines) + "\n"


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
