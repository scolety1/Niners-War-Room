from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

BOARD_ROWS_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/"
    "historical_rookie_tuning_board_rows.csv"
)
COMPONENT_ROWS_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/"
    "historical_rookie_tuning_component_rows.csv"
)
SUMMARY_ROWS_PATH = Path(
    "local_exports/model_v4/historical_rookie_tuning/latest/"
    "historical_rookie_tuning_summary_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/historical_rookie_tuning/latest")
DOC_PATH = Path("docs/model_v4/MODEL_V4_3_6_MATURE_REPLAY_MISS_PATTERN_REPORT.md")
VERSION = "model_v4_3_6_mature_replay_miss_patterns_0.1.0"

MISS_PATTERN_HEADER = (
    "pattern_group",
    "player",
    "draft_year",
    "position",
    "rank",
    "draft_round",
    "overall_pick",
    "final_score",
    "production_score",
    "college_team_share",
    "nfl_draft_pick_signal",
    "athletic_score",
    "confidence_cap",
    "evidence_available",
    "trust_level",
    "outcome_category",
    "broad_outcome_hit",
    "strict_starter_hit",
    "difference_maker",
    "likely_miss_cause",
    "recommended_action_type",
    "notes",
    "formula_version",
)

MISS_PATTERN_SUMMARY_HEADER = (
    "pattern_group",
    "rows",
    "unique_players",
    "formula_candidate_rows",
    "data_candidate_rows",
    "label_candidate_rows",
    "acceptable_edge_rows",
    "top_examples",
    "primary_read",
    "formula_version",
)


@dataclass(frozen=True)
class MatureMissPatternResult:
    pattern_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    doc_text: str


def build_mature_miss_pattern_report(
    board_rows_path: str | Path = BOARD_ROWS_PATH,
    component_rows_path: str | Path = COMPONENT_ROWS_PATH,
    summary_rows_path: str | Path = SUMMARY_ROWS_PATH,
) -> MatureMissPatternResult:
    board_rows = _read_rows(Path(board_rows_path))
    _ = _read_rows(Path(component_rows_path)), _read_rows(Path(summary_rows_path))
    mature_rows = [row for row in board_rows if _is_primary_replay_row(row)]
    pattern_rows: list[dict[str, object]] = []
    for row in mature_rows:
        for pattern_group in _pattern_groups(row):
            pattern_rows.append(_pattern_row(pattern_group, row))

    summary_rows = tuple(_summary_rows(pattern_rows))
    doc_text = _doc_text(mature_rows, pattern_rows, summary_rows)
    return MatureMissPatternResult(
        pattern_rows=tuple(pattern_rows),
        summary_rows=summary_rows,
        doc_text=doc_text,
    )


def write_mature_miss_pattern_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DOC_PATH,
    result: MatureMissPatternResult | None = None,
) -> dict[str, Path]:
    result = result or build_mature_miss_pattern_report()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    rows_path = output / "mature_miss_pattern_rows.csv"
    summary_path = output / "mature_miss_pattern_summary.csv"
    _write_csv(rows_path, MISS_PATTERN_HEADER, result.pattern_rows)
    _write_csv(summary_path, MISS_PATTERN_SUMMARY_HEADER, result.summary_rows)
    doc = Path(doc_path)
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(result.doc_text, encoding="utf-8")
    return {"rows": rows_path, "summary": summary_path, "doc": doc}


def _is_primary_replay_row(row: dict[str, str]) -> bool:
    return (
        _int(row.get("Draft Year")) in {2021, 2022, 2023}
        and _bool(row.get("Fantasy-Relevant Replay Pool"))
        and row.get("Outcome Maturity") == "three_year_window_available"
    )


def _pattern_groups(row: dict[str, str]) -> tuple[str, ...]:
    groups: list[str] = []
    rank = _int(row.get("Rank")) or 999
    position = str(row.get("Pos", ""))
    draft_round = _int(row.get("Draft Round"))
    strict = _bool(row.get("Strict Starter Hit?"))
    broad = _bool(row.get("Broad Outcome Hit?"))
    difference = _bool(row.get("Difference Maker?"))
    evidence = _float(row.get("Evidence Available"))
    production = _float(row.get("Production Score"))
    team_share = _float(row.get("College Team Share"))

    if rank <= 20 and not broad:
        groups.append("high_ranked_misses")
    if rank <= 20 and broad and not strict:
        groups.append("high_ranked_usable_but_not_starter")
    if rank > 20 and strict:
        groups.append("low_ranked_strict_starter_hits")
    if rank > 20 and difference:
        groups.append("low_ranked_difference_makers")
    if position == "WR" and draft_round == 1 and rank > 10 and broad:
        groups.append("first_round_wr_underranks")
    if (
        draft_round is not None
        and draft_round >= 4
        and rank <= 20
        and not strict
        and (production >= 75 or team_share >= 75)
    ):
        groups.append("late_capital_production_false_positives")
    if position == "RB" and draft_round is not None and draft_round >= 4 and strict:
        groups.append("day_three_rb_hits_worth_preserving")
    if position == "TE" and rank <= 30 and not strict:
        groups.append("te_overpromotion")
    if position == "TE" and rank > 30 and strict:
        groups.append("te_underpromotion")
    if position == "QB" and rank <= 24 and not strict:
        groups.append("qb_overpromotion")
    if position == "QB" and rank > 24 and strict:
        groups.append("qb_underpromotion")
    if rank <= 20 and evidence < 0.7 and not strict:
        groups.append("low_evidence_overpromotion")
    return tuple(groups)


def _pattern_row(pattern_group: str, row: dict[str, str]) -> dict[str, object]:
    cause, action, notes = _diagnosis(pattern_group, row)
    return {
        "pattern_group": pattern_group,
        "player": row.get("Player", ""),
        "draft_year": row.get("Draft Year", ""),
        "position": row.get("Pos", ""),
        "rank": row.get("Rank", ""),
        "draft_round": row.get("Draft Round", ""),
        "overall_pick": row.get("Overall Pick", ""),
        "final_score": row.get("Final Score", ""),
        "production_score": row.get("Production Score", ""),
        "college_team_share": row.get("College Team Share", ""),
        "nfl_draft_pick_signal": row.get("NFL Draft Pick Signal", ""),
        "athletic_score": row.get("Athletic Score", ""),
        "confidence_cap": row.get("Confidence Cap", ""),
        "evidence_available": row.get("Evidence Available", ""),
        "trust_level": row.get("Trust Level", ""),
        "outcome_category": row.get("Outcome Category", ""),
        "broad_outcome_hit": row.get("Broad Outcome Hit?", ""),
        "strict_starter_hit": row.get("Strict Starter Hit?", ""),
        "difference_maker": row.get("Difference Maker?", ""),
        "likely_miss_cause": cause,
        "recommended_action_type": action,
        "notes": notes,
        "formula_version": VERSION,
    }


def _diagnosis(pattern_group: str, row: dict[str, str]) -> tuple[str, str, str]:
    position = str(row.get("Pos", ""))
    draft_round = _int(row.get("Draft Round"))
    evidence = _float(row.get("Evidence Available"))
    production = _float(row.get("Production Score"))
    team_share = _float(row.get("College Team Share"))
    draft_signal = _float(row.get("NFL Draft Pick Signal"))

    if pattern_group == "high_ranked_misses":
        if evidence < 0.7:
            return (
                "top-board miss with low evidence coverage",
                "data_candidate",
                "Review missing pre-draft production/share/workout inputs before tuning.",
            )
        return (
            "top-board profile did not become usable outcome",
            "formula_candidate",
            "Candidate for confidence or component-weight review.",
        )
    if pattern_group == "high_ranked_usable_but_not_starter":
        return (
            "top-board player reached usable level but not starter threshold",
            "label_candidate",
            "Review whether broad hit or strict starter should be the tuning target.",
        )
    if pattern_group in {"low_ranked_strict_starter_hits", "low_ranked_difference_makers"}:
        if draft_round is not None and draft_round >= 4:
            return (
                "late-capital hit that may need preserved tail-upside treatment",
                "acceptable_edge",
                "Do not overcorrect against all late-capital players.",
            )
        return (
            "future starter ranked below primary board window",
            "formula_candidate",
            "Inspect which signal was missing or underweighted.",
        )
    if pattern_group == "first_round_wr_underranks":
        return (
            "Round 1 WR with outcome value ranked below top-board threshold",
            "formula_candidate",
            "Candidate first-round WR floor or college-share context review.",
        )
    if pattern_group == "late_capital_production_false_positives":
        return (
            "late-capital player rode production/team share above starter outcome",
            "formula_candidate",
            f"Production={production}; team_share={team_share}; draft_signal={draft_signal}.",
        )
    if pattern_group == "day_three_rb_hits_worth_preserving":
        return (
            "day-three RB became starter-level outcome",
            "acceptable_edge",
            "Preserve RB paths where workload/receiving evidence supports upside.",
        )
    if pattern_group == "te_overpromotion":
        return (
            "TE ranked in draftable window without starter-level outcome",
            "formula_candidate",
            "Candidate no-premium TE cap review.",
        )
    if pattern_group == "te_underpromotion":
        return (
            "starter-level TE ranked below TE board threshold",
            "formula_candidate",
            "Review whether early receiving role/capital was underweighted.",
        )
    if pattern_group == "qb_overpromotion":
        return (
            "QB ranked in meaningful rookie window without starter-level outcome",
            "formula_candidate",
            "Candidate 1QB cap review.",
        )
    if pattern_group == "qb_underpromotion":
        return (
            "starter-level QB ranked below meaningful rookie window",
            "acceptable_edge" if position == "QB" else "formula_candidate",
            "In 1QB this may be acceptable unless clear VORP edge was missed.",
        )
    if pattern_group == "low_evidence_overpromotion":
        return (
            "low-evidence player ranked high without strict starter outcome",
            "data_candidate",
            "Candidate stricter confidence cap before component-weight tuning.",
        )
    return ("pattern requires review", "formula_candidate", "")


def _summary_rows(pattern_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in pattern_rows:
        grouped[str(row["pattern_group"])].append(row)

    output: list[dict[str, object]] = []
    for group in sorted(grouped):
        rows = grouped[group]
        action_counts = Counter(str(row["recommended_action_type"]) for row in rows)
        examples = ", ".join(str(row["player"]) for row in rows[:6])
        output.append(
            {
                "pattern_group": group,
                "rows": len(rows),
                "unique_players": len({str(row["player"]) for row in rows}),
                "formula_candidate_rows": action_counts["formula_candidate"],
                "data_candidate_rows": action_counts["data_candidate"],
                "label_candidate_rows": action_counts["label_candidate"],
                "acceptable_edge_rows": action_counts["acceptable_edge"],
                "top_examples": examples,
                "primary_read": _primary_read(group, rows),
                "formula_version": VERSION,
            }
        )
    return output


def _primary_read(group: str, rows: list[dict[str, object]]) -> str:
    if not rows:
        return "no rows"
    if group == "late_capital_production_false_positives":
        return "possible production/team-share overpromotion; test before tuning"
    if group == "low_evidence_overpromotion":
        return "confidence caps should be reviewed before formula weights"
    if group == "first_round_wr_underranks":
        return "possible Round 1 WR floor issue"
    if group == "day_three_rb_hits_worth_preserving":
        return "late RB upside should not be fully suppressed"
    if "te_" in group:
        return "TE cap/exception logic requires review"
    if "qb_" in group:
        return "1QB QB discipline requires review"
    if group == "high_ranked_usable_but_not_starter":
        return "hit definition matters; broad usable is not starter value"
    return "review examples before candidate tuning"


def _doc_text(
    mature_rows: list[dict[str, str]],
    pattern_rows: list[dict[str, object]],
    summary_rows: tuple[dict[str, object], ...],
) -> str:
    strict_hits = sum(1 for row in mature_rows if _bool(row.get("Strict Starter Hit?")))
    difference_makers = sum(1 for row in mature_rows if _bool(row.get("Difference Maker?")))
    lines = [
        "# Model v4.3.6 Mature Replay Miss-Pattern Report",
        "",
        "## Scope",
        "",
        "Primary analysis is limited to mature 2021-2023 rows where "
        "`Fantasy-Relevant Replay Pool == True` and outcome maturity is "
        "`three_year_window_available`.",
        "",
        "No formula weights were changed.",
        "",
        "## Dataset",
        "",
        f"- Mature fantasy-relevant rows: {len(mature_rows)}",
        f"- Strict starter outcomes: {strict_hits}",
        f"- Difference-maker outcomes: {difference_makers}",
        f"- Pattern rows emitted: {len(pattern_rows)}",
        "",
        "## Pattern Summary",
        "",
        "| Pattern | Rows | Primary Read | Examples |",
        "|---|---:|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            "| {pattern_group} | {rows} | {primary_read} | {top_examples} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report is a diagnostic layer, not a formula change. Rows marked "
            "`formula_candidate` are candidates for later shadow tests only. Rows "
            "marked `data_candidate` should be investigated for source coverage or "
            "confidence-cap behavior before component weights are changed.",
            "",
            "## Guardrails",
            "",
            "- Outcomes remain display-only.",
            "- 2024 and 2025 are excluded from primary miss-pattern analysis.",
            "- No market, ADP, projection, ranking, mock, or big-board fields are used.",
            "- Active rankings, My Team, War Board, readiness gates, and app promotion "
            "are unchanged.",
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


def _bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def _int(value: object) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _float(value: object) -> float:
    try:
        if value in ("", None):
            return 0.0
        return float(str(value))
    except ValueError:
        return 0.0
