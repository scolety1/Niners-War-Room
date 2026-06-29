from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RD_ROOT = REPO_ROOT / "docs" / "hq" / "rookie_outcomes" / "rookie_outcome_rd_20260629"
CFBD_IDENTITY_ROOT = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "cfbd_identity_matching_v1_20260624"
)
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_outcome_columns_gated_20260629"
)

APPROVAL_PACKET_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "college_team",
    "nfl_team_if_available",
    "draft_year_if_available",
    "cfbd_candidate_id",
    "cfbd_name",
    "cfbd_position",
    "cfbd_team",
    "cfbd_years",
    "match_evidence",
    "production_context_summary",
    "ambiguity_flags",
    "recommended_review_decision",
    "human_decision",
    "human_notes",
    "approved_by_human",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

VALID_RECOMMENDED_DECISIONS = {
    "APPROVE_REVIEW_ONLY",
    "REJECT",
    "DEFER",
    "KEEP_BLOCKED",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Gate A CFBD human approval packet for rookie outcome columns."
    )
    parser.add_argument("--rd-root", type=Path, default=RD_ROOT)
    parser.add_argument("--cfbd-identity-root", type=Path, default=CFBD_IDENTITY_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    readiness_rows = _read_rows(args.rd_root / "rookie_cfbd_readiness_matrix.csv")
    match_rows = _read_rows(args.cfbd_identity_root / "cfbd_identity_match_candidates.csv")
    production_rows = _read_rows(
        args.cfbd_identity_root / "cfbd_identity_production_context_review.csv"
    )
    dashboard_rows = _read_rows(
        args.cfbd_identity_root / "cfbd_identity_review_dashboard_summary.csv"
    )
    registry_rows = _read_rows(args.cfbd_identity_root / "cfbd_identity_link_registry_DRAFT.csv")

    packet_rows = build_approval_packet_rows(
        readiness_rows=readiness_rows,
        match_rows=match_rows,
        production_rows=production_rows,
    )
    validate_approval_packet_rows(packet_rows)

    args.output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_root / "cfbd_rookie_identity_human_approval_packet.csv",
        APPROVAL_PACKET_COLUMNS,
        packet_rows,
    )
    _write_gate_a_blocker(
        args.output_root / "00_GATE_A_CFBD_APPROVAL_BLOCKER.md",
        readiness_rows=readiness_rows,
        packet_rows=packet_rows,
        dashboard_rows=dashboard_rows,
        registry_rows=registry_rows,
    )
    _write_readme(
        args.output_root / "README.md",
        packet_rows=packet_rows,
        dashboard_rows=dashboard_rows,
    )
    print(
        {
            "gate": "A",
            "gate_status": "BLOCKED_NEEDS_CFBD_APPROVAL",
            "approval_packet_rows": len(packet_rows),
            "output_root": str(args.output_root),
        }
    )
    return 0


def build_approval_packet_rows(
    *,
    readiness_rows: list[dict[str, str]],
    match_rows: list[dict[str, str]],
    production_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    match_index = _match_index(match_rows)
    years_by_cfbd_id = _years_by_cfbd_id(match_rows)
    production_by_cfbd_id = _production_summary_by_cfbd_id(production_rows)
    output: list[dict[str, str]] = []

    for row in readiness_rows:
        cfbd_id = _clean(row.get("cfbd_player_id"))
        player_id = _clean(row.get("player_id"))
        match = _select_match(row, match_index)
        production_summary = production_by_cfbd_id.get(cfbd_id) or "Not enough information"
        match_status = _clean(row.get("cfbd_match_status"))
        identity_confidence = _clean(row.get("identity_confidence"))
        blocker_reason = _clean(row.get("blocker_reason"))
        ambiguity_flags = _ambiguity_flags(row, match)
        recommended = _recommended_review_decision(row)
        output.append(
            {
                "player_id": "" if player_id.lower() == "nan" else player_id,
                "player_name": _clean(row.get("player_name")),
                "position": _clean(row.get("position") or match.get("candidate_position")),
                "college_team": _clean(row.get("college_team") or match.get("cfbd_college_team")),
                "nfl_team_if_available": _clean(match.get("candidate_team")),
                "draft_year_if_available": "",
                "cfbd_candidate_id": cfbd_id,
                "cfbd_name": _clean(row.get("cfbd_player_name") or match.get("cfbd_player_name")),
                "cfbd_position": _clean(match.get("cfbd_position")),
                "cfbd_team": _clean(match.get("cfbd_college_team")),
                "cfbd_years": "|".join(sorted(years_by_cfbd_id.get(cfbd_id, set()))),
                "match_evidence": _match_evidence(
                    match=match,
                    match_status=match_status,
                    identity_confidence=identity_confidence,
                    blocker_reason=blocker_reason,
                ),
                "production_context_summary": production_summary,
                "ambiguity_flags": ambiguity_flags,
                "recommended_review_decision": recommended,
                "human_decision": "",
                "human_notes": "",
                "approved_by_human": "false",
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def validate_approval_packet_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        missing = [column for column in APPROVAL_PACKET_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Gate A approval packet missing columns: {missing}")
        if row["approved_by_human"] != "false":
            raise ValueError("Gate A approval packet must not self-approve rows.")
        if row["review_only"] != "true":
            raise ValueError("Gate A approval packet must keep review_only=true.")
        if row["model_use_allowed"] != "false":
            raise ValueError("Gate A approval packet must keep model_use_allowed=false.")
        if row["training_allowed"] != "false":
            raise ValueError("Gate A approval packet must keep training_allowed=false.")
        if row["human_decision"] != "":
            raise ValueError("Gate A approval packet must leave human_decision blank.")
        if row["recommended_review_decision"] not in VALID_RECOMMENDED_DECISIONS:
            raise ValueError("Gate A approval packet has invalid recommended decision.")


def _match_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        cfbd_id = _clean(row.get("cfbd_player_id"))
        candidate_id = _clean(row.get("candidate_player_id"))
        sleeper_id = _clean(row.get("candidate_sleeper_id"))
        if cfbd_id:
            index[(cfbd_id, candidate_id)].append(row)
            index[(cfbd_id, sleeper_id)].append(row)
            index[(cfbd_id, "")].append(row)
    return index


def _years_by_cfbd_id(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    years: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        cfbd_id = _clean(row.get("cfbd_player_id"))
        year = _clean(row.get("cfbd_season"))
        if cfbd_id and year:
            years[cfbd_id].add(year)
    return years


def _production_summary_by_cfbd_id(rows: list[dict[str, str]]) -> dict[str, str]:
    summaries: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        cfbd_id = _clean(row.get("cfbd_player_id"))
        if not cfbd_id:
            continue
        season = _clean(row.get("cfbd_season"))
        categories = _clean(row.get("production_categories"))
        summary = _clean(row.get("production_summary"))
        if summary:
            summaries[cfbd_id].append(f"{season} {categories}: {summary}".strip())
    return {
        cfbd_id: " || ".join(_unique_preserve_order(values)[:3])
        for cfbd_id, values in summaries.items()
    }


def _select_match(
    readiness_row: dict[str, str],
    match_index: dict[tuple[str, str], list[dict[str, str]]],
) -> dict[str, str]:
    cfbd_id = _clean(readiness_row.get("cfbd_player_id"))
    player_id = _clean(readiness_row.get("player_id"))
    candidates = match_index.get((cfbd_id, player_id)) or match_index.get((cfbd_id, ""))
    if not candidates:
        return {}
    target_status = _clean(readiness_row.get("cfbd_match_status"))
    target_name = _clean(readiness_row.get("player_name")).lower()
    scored = sorted(
        candidates,
        key=lambda row: (
            _clean(row.get("match_status")) == target_status,
            _clean(row.get("candidate_player_name")).lower() == target_name,
            _safe_int(row.get("name_score")),
        ),
        reverse=True,
    )
    return scored[0]


def _recommended_review_decision(row: dict[str, str]) -> str:
    status = _clean(row.get("cfbd_match_status"))
    confidence = _clean(row.get("identity_confidence"))
    production_status = _clean(row.get("production_context_valid"))
    if status == "exact_match" and confidence == "HIGH" and production_status.startswith("REVIEW"):
        return "APPROVE_REVIEW_ONLY"
    if status in {"ambiguous", "possible_candidate"}:
        return "DEFER"
    return "KEEP_BLOCKED"


def _ambiguity_flags(row: dict[str, str], match: dict[str, str]) -> str:
    flags = []
    if _clean(row.get("ambiguity_flag")).lower() == "yes":
        flags.append("readiness_matrix_ambiguity_flag")
    if _clean(row.get("cfbd_match_status")) == "ambiguous":
        flags.append("cfbd_match_status_ambiguous")
    if _clean(row.get("cfbd_match_status")) == "possible_candidate":
        flags.append("possible_candidate_requires_review")
    if match and _clean(match.get("position_match")) == "false":
        flags.append("position_mismatch_or_missing")
    return "|".join(flags) if flags else "none"


def _match_evidence(
    *,
    match: dict[str, str],
    match_status: str,
    identity_confidence: str,
    blocker_reason: str,
) -> str:
    evidence = [
        f"cfbd_match_status={match_status}",
        f"identity_confidence={identity_confidence}",
    ]
    if match:
        for key in (
            "candidate_source",
            "candidate_player_id",
            "candidate_sleeper_id",
            "candidate_player_name",
            "candidate_team",
            "name_score",
            "position_match",
        ):
            value = _clean(match.get(key))
            if value:
                evidence.append(f"{key}={value}")
    if blocker_reason:
        evidence.append(f"blocker_reason={blocker_reason}")
    return "; ".join(evidence)


def _write_gate_a_blocker(
    path: Path,
    *,
    readiness_rows: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    dashboard_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
) -> None:
    status_counts = Counter(_clean(row.get("cfbd_match_status")) for row in readiness_rows)
    confidence_counts = Counter(
        _clean(row.get("identity_confidence")) for row in readiness_rows
    )
    dashboard = {_clean(row.get("metric")): _clean(row.get("value")) for row in dashboard_rows}
    registry_blocked = sum(
        1 for row in registry_rows if _clean(row.get("approved_by_human")) == "false"
    )
    model_use_approved = dashboard.get("rows approved for model use", "0")
    recruiting_context = dashboard.get("rows with recruiting context", "0")
    lines = [
        "# Gate A CFBD Approval Blocker - 2026-06-29",
        "",
        "## Gate Result",
        "",
        "`BLOCKED_NEEDS_CFBD_APPROVAL`",
        "",
        "Gate A is not GREEN because no tracked human-approved CFBD identity artifact exists.",
        "The current CFBD identity package and draft registry remain review-only.",
        "",
        "## Evidence",
        "",
        f"- Rookie CFBD readiness rows: {len(readiness_rows)}",
        f"- Human approval packet rows created: {len(packet_rows)}",
        f"- Draft registry rows still `approved_by_human=false`: {registry_blocked}",
        f"- Dashboard rows approved for model use: {model_use_approved}",
        f"- Dashboard rows with recruiting context: {recruiting_context}",
        "",
        "## Match Status Counts",
        "",
        *[f"- {key}: {value}" for key, value in sorted(status_counts.items())],
        "",
        "## Identity Confidence Counts",
        "",
        *[f"- {key}: {value}" for key, value in sorted(confidence_counts.items())],
        "",
        "## Stop Decision",
        "",
        "The lane stops at Gate A. It does not continue to draft capital,",
        "historical labels, feature policy, modeling, display artifacts, or",
        "Rankings integration.",
        "",
        "## Guardrails",
        "",
        "- No rookie probabilities were created.",
        "- No rookie T6/T12/T24/T36 outputs were created.",
        "- No CFBD data became model input or training truth.",
        "- Missing data remains `Not enough information`, not `0%`.",
        "- Dynasty Rank, Candidate Rank, tiers, frozen board, pinned snapshot, latest candidate,",
        "  latest approved, model/rank/source-truth gates, Live Draft, and Mock Draft",
        "  were not touched.",
        "",
        "## Required Human Review",
        "",
        "Use `cfbd_rookie_identity_human_approval_packet.csv` to approve, reject, defer, or keep",
        "blocked each row. Valid future human decisions are `APPROVE_REVIEW_ONLY`,",
        "`REJECT`, `DEFER`, and `KEEP_BLOCKED`. Approval in this packet must stay",
        "review-only until a later explicit source-truth/model-use gate exists.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_readme(
    path: Path,
    *,
    packet_rows: list[dict[str, str]],
    dashboard_rows: list[dict[str, str]],
) -> None:
    dashboard = {_clean(row.get("metric")): _clean(row.get("value")) for row in dashboard_rows}
    model_use_approved = dashboard.get("rows approved for model use", "0")
    recruiting_context = dashboard.get("rows with recruiting context", "0")
    lines = [
        "# Rookie Outcome Columns Gated Lane - 2026-06-29",
        "",
        "## Gate Results",
        "",
        "- Gate A - CFBD identity human approval: `BLOCKED_NEEDS_CFBD_APPROVAL`",
        "- Gates B-G: not run because Gate A is blocked.",
        "",
        "## Where This Lane Stopped",
        "",
        "The lane stopped at Gate A and created the required CFBD rookie identity",
        "human approval packet.",
        "",
        "## Active Blockers",
        "",
        "- No tracked human-approved CFBD identity artifact exists.",
        "- CFBD identity links remain review-only and blocked for model/training use.",
        "- Draft capital, label, feature, model, display, and Rankings gates were not run.",
        "",
        "## Artifacts Created",
        "",
        "- `00_GATE_A_CFBD_APPROVAL_BLOCKER.md`",
        "- `cfbd_rookie_identity_human_approval_packet.csv`",
        "",
        "## Counts",
        "",
        f"- Approval packet rows: {len(packet_rows)}",
        f"- CFBD identity rows approved for model use: {model_use_approved}",
        f"- CFBD rows with recruiting context: {recruiting_context}",
        "",
        "## Rankings / Active Columns",
        "",
        "- Rankings was not touched.",
        "- Active rookie outcome columns were not added.",
        "- Rookie probabilities were not generated.",
        "",
        "## Scoring Status",
        "",
        "No scoring artifact was built because the lane stopped before historical",
        "label/model gates.",
        "Exact vs approximate scoring remains blocked for future work.",
        "",
        "## Human Review Checklist",
        "",
        "1. Review every row in `cfbd_rookie_identity_human_approval_packet.csv`.",
        "2. Choose one valid human decision: `APPROVE_REVIEW_ONLY`, `REJECT`,",
        "   `DEFER`, or `KEEP_BLOCKED`.",
        "3. Add reviewer notes for ambiguous or possible candidates.",
        "4. Keep `model_use_allowed=false` and `training_allowed=false` until a",
        "   later explicit gate.",
        "",
        "## Recommended Next Lane",
        "",
        "`CFBD Rookie Identity Human Approval Packet V1`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _safe_int(value: object) -> int:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def _clean(value: object) -> str:
    return str(value or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
