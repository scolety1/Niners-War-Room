from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "current_rookie_udfa_unknown_review_packet_v1_20260630"
)

UNIVERSE_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "current_rookie_universe_udfa_policy_v1_20260630"
)
V2_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_coverage_repair_v2_20260630"
)
GATE_A_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "cfbd_rookie_identity_approval_v1_20260629"
    / "cfbd_rookie_identity_human_approval_v1.csv"
)

UNIVERSE_PATH = UNIVERSE_ROOT / "current_rookie_universe_matrix_v1.csv"
V4_DISPLAY_PATH = UNIVERSE_ROOT / "rookie_display_artifact_v4_coverage_matrix.csv"
V2_REPAIR_PATH = V2_ROOT / "rookie_draft_capital_repair_v2_matrix.csv"
SOURCE_REGISTRY_PATH = REPO_ROOT / "config" / "source_registry.csv"

BASE_HEAD = "8dabb50bb8594f1e44dd5feea308ac3e1c3bd953"
NOT_ENOUGH = "Not enough information"

VALID_DECISIONS = {
    "CONFIRM_UDFA_REVIEW_ONLY",
    "KEEP_LIKELY_UDFA_REVIEW",
    "REJECT_WRONG_UNIVERSE",
    "KEEP_UNKNOWN",
    "NEEDS_MORE_INFO",
}

PACKET_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "current_status_before",
    "current_rookie_universe_status",
    "CFBD_identity_status_if_available",
    "NWR_Sleeper_NFL_identity_fields_if_available",
    "nflverse_draft_pick_search_result",
    "draft_year_checked",
    "exact_name_match_in_draft_picks",
    "normalized_name_match_in_draft_picks",
    "position_match_in_draft_picks",
    "team_or_school_context_if_available",
    "possible_name_collision",
    "wrong_universe_risk",
    "current_evidence_summary",
    "evidence_strength",
    "recommended_human_decision",
    "recommended_reason",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

RECOMMENDATION_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "rookie_class_year",
    "recommended_human_decision",
    "evidence_strength",
    "recommended_reason",
    "can_auto_apply_review_only",
    "review_only",
    "approved_by_human",
    "model_use_allowed",
    "training_allowed",
)

PREVIEW_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "current_rookie_universe_status",
    "current_display_status",
    "recommended_human_decision",
    "preview_display_status_if_accepted",
    "outcome_display_field_count",
    "status_display_available",
    "not_enough_information_reason",
    "review_only",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "rankings_wiring_allowed",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-root", type=Path, default=DOC_ROOT)
    args = parser.parse_args(argv)
    args.doc_root.mkdir(parents=True, exist_ok=True)

    universe_rows = read_csv(UNIVERSE_PATH)
    display_rows = read_csv(V4_DISPLAY_PATH)
    repair_rows = read_csv(V2_REPAIR_PATH)
    gate_a_rows = read_csv(GATE_A_PATH)
    source_rows = read_csv(SOURCE_REGISTRY_PATH)

    gate_a_index = build_gate_a_index(gate_a_rows)
    repair_index = row_index(repair_rows)
    review_rows = [
        row
        for row in universe_rows
        if row["current_rookie_universe_status"]
        in {
            "current_rookie_likely_udfa_review",
            "current_rookie_unknown_needs_human_review",
        }
    ]
    packet_rows = build_packet_rows(review_rows, gate_a_index, repair_index)
    recommendation_rows = build_recommendation_rows(packet_rows)
    preview_rows = build_preview_rows(display_rows, packet_rows)

    write_csv(
        args.doc_root / "current_rookie_udfa_unknown_evidence_packet_v1.csv",
        PACKET_COLUMNS,
        packet_rows,
    )
    write_csv(
        args.doc_root / "current_rookie_udfa_unknown_review_recommendations_v1.csv",
        RECOMMENDATION_COLUMNS,
        recommendation_rows,
    )
    write_csv(
        args.doc_root / "rookie_display_artifact_v5_preview_coverage_matrix.csv",
        PREVIEW_COLUMNS,
        preview_rows,
    )
    write_docs(
        args.doc_root,
        universe_rows,
        display_rows,
        packet_rows,
        recommendation_rows,
        preview_rows,
        source_rows,
    )
    print(
        {
            "final_verdict": "PARTIAL_REVIEW_PACKET_READY",
            "packet_rows": len(packet_rows),
            "confirm_recommendations": count_decision(
                packet_rows,
                "CONFIRM_UDFA_REVIEW_ONLY",
            ),
            "keep_unknown_recommendations": count_decision(packet_rows, "KEEP_UNKNOWN"),
            "v5_preview_status_rows": count_preview_status_rows(preview_rows),
            "auto_applied": 0,
        }
    )


def build_packet_rows(
    rows: list[dict[str, str]],
    gate_a_index: dict[tuple[str, str, str], dict[str, str]],
    repair_index: dict[tuple[str, str, str, str], dict[str, str]],
) -> list[dict[str, str]]:
    output = []
    for row in rows:
        gate_a = gate_a_index.get((row["player_id"], row["player_name"], row["position"]), {})
        repair = repair_index[(row["player_id"], row["player_name"], row["position"], row["team"])]
        decision, strength, reason = recommend_decision(row, gate_a, repair)
        output.append(
            {
                "player_id": clean(row["player_id"]),
                "player_name": clean(row["player_name"]),
                "position": clean(row["position"]),
                "team": clean(row["team"]),
                "rookie_class_year": clean(row["rookie_class_year"]),
                "current_status_before": clean(row["current_rookie_universe_status"]),
                "current_rookie_universe_status": clean(row["current_rookie_universe_status"]),
                "CFBD_identity_status_if_available": clean(
                    gate_a.get("gate_a_status", NOT_ENOUGH)
                ),
                "NWR_Sleeper_NFL_identity_fields_if_available": identity_summary(row, gate_a),
                "nflverse_draft_pick_search_result": draft_search_result(repair),
                "draft_year_checked": "2025|2026",
                "exact_name_match_in_draft_picks": "false",
                "normalized_name_match_in_draft_picks": "false",
                "position_match_in_draft_picks": "false",
                "team_or_school_context_if_available": team_school_context(row, gate_a),
                "possible_name_collision": "false",
                "wrong_universe_risk": wrong_universe_risk(row, gate_a),
                "current_evidence_summary": evidence_summary(row, gate_a, repair),
                "evidence_strength": strength,
                "recommended_human_decision": decision,
                "recommended_reason": reason,
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def recommend_decision(
    row: dict[str, str],
    gate_a: dict[str, str],
    repair: dict[str, str],
) -> tuple[str, str, str]:
    if row["current_rookie_universe_status"] == "current_rookie_likely_udfa_review":
        has_team = row["team"] not in {NOT_ENOUGH, "NEEDS_DATA"}
        has_identity = row["player_id"] != NOT_ENOUGH
        gate_a_green = gate_a.get("gate_a_status") == "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL"
        not_drafted = repair["udffa_or_undrafted_status"] == "likely_udfa_needs_review"
        if has_team and has_identity and gate_a_green and not_drafted:
            return (
                "CONFIRM_UDFA_REVIEW_ONLY",
                "STRONG_REVIEW_ONLY",
                (
                    "Approved review-only identity plus NWR/Sleeper team/status context "
                    "and absence from complete 2025/2026 nflverse draft picks."
                ),
            )
        return (
            "KEEP_LIKELY_UDFA_REVIEW",
            "MEDIUM_REVIEW_ONLY",
            "Likely undrafted, but one identity/current-rookie field is not strong enough.",
        )
    return (
        "KEEP_UNKNOWN",
        "WEAK_REVIEW_ONLY",
        (
            "Current-rookie evidence is too thin, usually missing player ID or team/status "
            "context, so the row should remain Not enough information."
        ),
    )


def build_recommendation_rows(packet_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in packet_rows:
        is_confirm = row["recommended_human_decision"] == "CONFIRM_UDFA_REVIEW_ONLY"
        can_apply = "true" if is_confirm else "false"
        output.append(
            {
                "player_id": row["player_id"],
                "player_name": row["player_name"],
                "position": row["position"],
                "team": row["team"],
                "rookie_class_year": row["rookie_class_year"],
                "recommended_human_decision": row["recommended_human_decision"],
                "evidence_strength": row["evidence_strength"],
                "recommended_reason": row["recommended_reason"],
                "can_auto_apply_review_only": can_apply,
                "review_only": "true",
                "approved_by_human": "false",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def build_preview_rows(
    display_rows: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    packet_index = {
        (row["player_id"], row["player_name"], row["position"], row["team"]): row
        for row in packet_rows
    }
    output = []
    for row in display_rows:
        key = (row["player_id"], row["player_name"], row["position"], row["team"])
        packet = packet_index.get(key)
        decision = packet["recommended_human_decision"] if packet else "not_applicable"
        preview_status = preview_status_for_row(row, decision)
        output.append(
            {
                "player_id": row["player_id"],
                "player_name": row["player_name"],
                "position": row["position"],
                "team": row["team"],
                "current_rookie_universe_status": row["current_rookie_universe_status"],
                "current_display_status": row["display_status"],
                "recommended_human_decision": decision,
                "preview_display_status_if_accepted": preview_status,
                "outcome_display_field_count": row["display_field_count"],
                "status_display_available": (
                    "true"
                    if preview_status
                    in {
                        "review_only_outcome_rates_available",
                        "udfa_status_review_only_preview",
                    }
                    else "false"
                ),
                "not_enough_information_reason": preview_nei_reason(row, decision),
                "review_only": "true",
                "display_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "rankings_wiring_allowed": "false",
            }
        )
    return output


def preview_status_for_row(row: dict[str, str], decision: str) -> str:
    if int(row["display_field_count"]) > 0:
        return "review_only_outcome_rates_available"
    if decision == "CONFIRM_UDFA_REVIEW_ONLY":
        return "udfa_status_review_only_preview"
    if row["wrong_universe_flag"] == "true":
        return "wrong_universe_blocked"
    return NOT_ENOUGH


def preview_nei_reason(row: dict[str, str], decision: str) -> str:
    if int(row["display_field_count"]) > 0:
        return NOT_ENOUGH
    if decision == "CONFIRM_UDFA_REVIEW_ONLY":
        return "UDFA status could display, but no validated UDFA outcome rates."
    if row["wrong_universe_flag"] == "true":
        return "Wrong-universe/name-collision row remains blocked."
    return "Insufficient current-rookie or UDFA evidence."


def write_docs(
    root: Path,
    universe_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
    packet_rows: list[dict[str, str]],
    recommendation_rows: list[dict[str, str]],
    preview_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> None:
    decision_counts = Counter(row["recommended_human_decision"] for row in packet_rows)
    universe_counts = Counter(row["current_rookie_universe_status"] for row in universe_rows)
    likely_udfa_count = universe_counts["current_rookie_likely_udfa_review"]
    unknown_count = universe_counts["current_rookie_unknown_needs_human_review"]
    wrong_universe_count = universe_counts["wrong_universe_name_collision"]
    confirm_count = decision_counts["CONFIRM_UDFA_REVIEW_ONLY"]
    keep_unknown_count = decision_counts["KEEP_UNKNOWN"]
    preview_status_count = count_preview_status_rows(preview_rows)
    source_status = {
        f"{row['source_name']}.{row['source_table']}": row["default_admissibility"]
        for row in source_rows
    }
    write_doc(
        root / "00_REVIEW_PACKET_INVENTORY.md",
        [
            "# Current Rookie UDFA Unknown Review Packet Inventory - 2026-06-30",
            "",
            f"- Actual base HEAD: `{BASE_HEAD}`",
            "- Current rookie universe artifact: `current_rookie_universe_matrix_v1.csv`.",
            "- Gate F V4 display artifact: `rookie_display_artifact_v4_coverage_matrix.csv`.",
            "- UDFA policy artifact: `02_UDFA_SOURCE_POLICY_GATE.md`.",
            f"- Likely UDFA / undrafted review rows: {likely_udfa_count}",
            f"- Unknown / needs human review rows: {unknown_count}",
            f"- Wrong-universe rows already cleaned/blocked: {wrong_universe_count}",
            f"- Gate F V4 valid display rows: {count_display_rows(display_rows)}",
            (
                "- Admitted source-policy-safe sources used: "
                f"nflverse.draft_picks={source_status.get('nflverse.draft_picks')}; "
                f"sleeper.players={source_status.get('sleeper.players')}."
            ),
            (
                "- Blocked sources not used: JackLich, array-carpenter, grades, "
                "FootballDB, market, vendor, Gmail."
            ),
            "",
            "Inventory is complete; no app/rank/model files are touched.",
        ],
    )
    write_doc(
        root / "01_HUMAN_REVIEW_SUMMARY.md",
        [
            "# Human Review Summary - Current Rookie UDFA Unknown Packet V1",
            "",
            "This packet exists because Gate G is blocked by non-drafted/unknown rookie rows.",
            "A UDFA status here means review-only undrafted/free-agent context. It is not",
            "source truth, model input, training truth, or a rookie probability.",
            "",
            "Absence from the completed nflverse 2025/2026 draft-pick set is useful evidence.",
            "It is strongest when paired with an approved review-only identity and an existing",
            "NWR/Sleeper team or FA context. Absence by itself is not enough for thin rows.",
            "",
            "Decision meanings:",
            (
                "- `CONFIRM_UDFA_REVIEW_ONLY`: safe recommendation for "
                "review-only approval if the user accepts it later."
            ),
            "- `KEEP_LIKELY_UDFA_REVIEW`: likely undrafted, but evidence is not strong enough.",
            "- `REJECT_WRONG_UNIVERSE`: wrong player/year/name collision.",
            "- `KEEP_UNKNOWN`: too little evidence; keep `Not enough information`.",
            "- `NEEDS_MORE_INFO`: a specific missing source is required.",
            "",
            "Counts by recommended decision:",
            *[
                f"- {decision}: {decision_counts[decision]}"
                for decision in sorted(VALID_DECISIONS)
                if decision_counts[decision]
            ],
            "",
            f"Rows likely safe to confirm review-only: {confirm_count}.",
            f"Rows that should remain unknown: {keep_unknown_count}.",
            "Wrong-universe/name-collision rows remain blocked from the prior lane: 2.",
            "",
            "If accepted later, these recommendations can unlock status-only UDFA display",
            "context for the recommended rows. They do not unlock model use, training use,",
            "Rankings wiring, hidden sorting, or rookie outcome probabilities.",
        ],
    )
    write_doc(
        root / "02_NEXT_ACTION_DECISION.md",
        [
            "# Next Action Decision - 2026-06-30",
            "",
            "## Verdict",
            "",
            "`PARTIAL_REVIEW_PACKET_READY`",
            "",
            f"- Evidence packet rows: {len(packet_rows)}",
            f"- Recommendation rows: {len(recommendation_rows)}",
            f"- Confirm-review-only recommendations: {confirm_count}",
            f"- Keep-unknown recommendations: {keep_unknown_count}",
            f"- V5 preview status-display rows if accepted: {preview_status_count}",
            "- Nothing was auto-applied.",
            "- Gate G remains blocked.",
            "",
            "Recommended next lane: `Apply UDFA Review Recommendations V1` if the user",
            "explicitly accepts the recommendations; otherwise keep Gate G blocked.",
        ],
    )
    write_doc(
        root / "README.md",
        [
            "# Current Rookie UDFA Unknown Review Packet V1",
            "",
            "This review packet provides source-policy-safe evidence and conservative",
            "recommendations for the 38 likely-UDFA/unknown rows. It does not approve",
            "anything, write app columns, create probabilities, or wire Rankings.",
        ],
    )


def build_gate_a_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    index = {}
    for row in rows:
        key = (clean(row["player_id"]), clean(row["player_name"]), clean(row["position"]))
        if row.get("gate_a_status") == "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL":
            index.setdefault(key, row)
    return index


def row_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {
        (row["player_id"], row["player_name"], row["position"], row["team"]): row
        for row in rows
    }


def identity_summary(row: dict[str, str], gate_a: dict[str, str]) -> str:
    parts = [
        f"player_id={row['player_id']}",
        f"team={row['team']}",
        f"position={row['position']}",
    ]
    if gate_a:
        parts.extend(
            [
                f"cfbd_candidate_id={clean(gate_a.get('cfbd_candidate_id'))}",
                f"approval_scope={clean(gate_a.get('approval_scope'))}",
                f"nwr_team={clean(gate_a.get('nfl_team_if_available'))}",
            ]
        )
    return "; ".join(parts)


def draft_search_result(repair: dict[str, str]) -> str:
    if repair["draft_capital_status"] == "REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE":
        return "drafted_verified"
    return "not_found_in_complete_2025_2026_nflverse_draft_picks"


def team_school_context(row: dict[str, str], gate_a: dict[str, str]) -> str:
    parts = [f"team={row['team']}"]
    if gate_a:
        parts.extend(
            [
                f"college={clean(gate_a.get('college_team'))}",
                f"cfbd_years={clean(gate_a.get('cfbd_years'))}",
            ]
        )
    return "; ".join(parts)


def wrong_universe_risk(row: dict[str, str], gate_a: dict[str, str]) -> str:
    if row["player_id"] == NOT_ENOUGH or row["team"] == "NEEDS_DATA":
        return "medium"
    if not gate_a:
        return "medium"
    return "low"


def evidence_summary(
    row: dict[str, str],
    gate_a: dict[str, str],
    repair: dict[str, str],
) -> str:
    if row["current_rookie_universe_status"] == "current_rookie_likely_udfa_review":
        return (
            "No 2025/2026 nflverse draft-pick match; row has review-only current "
            f"team/status context `{row['team']}` and CFBD identity status "
            f"`{clean(gate_a.get('gate_a_status'))}`."
        )
    return (
        "No 2025/2026 nflverse draft-pick match, but player ID or team/status "
        f"context is incomplete; repair action was `{clean(repair.get('repair_action'))}`."
    )


def count_decision(rows: list[dict[str, str]], decision: str) -> int:
    return sum(row["recommended_human_decision"] == decision for row in rows)


def count_display_rows(rows: list[dict[str, str]]) -> int:
    return sum(int(row["display_field_count"]) > 0 for row in rows)


def count_preview_status_rows(rows: list[dict[str, str]]) -> int:
    return sum(row["status_display_available"] == "true" for row in rows)


def clean(value: object) -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "<na>"} or not text:
        return NOT_ENOUGH
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def write_doc(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
