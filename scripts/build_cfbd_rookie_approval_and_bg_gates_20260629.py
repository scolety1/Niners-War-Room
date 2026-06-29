from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATED_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_outcome_columns_gated_20260629"
)
RD_ROOT = REPO_ROOT / "docs" / "hq" / "rookie_outcomes" / "rookie_outcome_rd_20260629"
APPROVAL_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "cfbd_rookie_identity_approval_v1_20260629"
)
DRAFT_CAPITAL_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_draft_capital_review_v1_20260629"
)

APPROVAL_SOURCE = "user_chat_20260629"
APPROVAL_SCOPE = "identity_review_only"
APPROVAL_NOTES = (
    "Human approved CFBD identity review-only gate for high-confidence exact matches only; "
    "not model/training/source-truth approval."
)

APPROVAL_COLUMNS = (
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
    "match_status",
    "identity_confidence",
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
    "approval_scope",
    "approval_source",
    "approval_notes",
    "gate_a_status",
)

DRAFT_AUDIT_COLUMNS = (
    "source_name",
    "source_path",
    "scope",
    "availability_status",
    "approved_identity_rows_covered",
    "draft_year_available",
    "draft_round_available",
    "overall_pick_available",
    "drafted_team_available",
    "udfa_status_available",
    "age_at_draft_available",
    "historical_classes_available",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "gate_b_use_status",
    "blocker_reason",
    "safe_next_step",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply review-only CFBD rookie identity approval and Gate B audit."
    )
    parser.add_argument("--gated-root", type=Path, default=GATED_ROOT)
    parser.add_argument("--rd-root", type=Path, default=RD_ROOT)
    parser.add_argument("--approval-root", type=Path, default=APPROVAL_ROOT)
    parser.add_argument("--draft-capital-root", type=Path, default=DRAFT_CAPITAL_ROOT)
    args = parser.parse_args()

    packet_rows = _read_rows(
        args.gated_root / "cfbd_rookie_identity_human_approval_packet.csv"
    )
    approval_rows = build_approval_rows(packet_rows)
    validate_approval_rows(approval_rows)

    draft_matrix_rows = _read_rows(args.rd_root / "rookie_draft_capital_availability_matrix.csv")
    draft_audit_rows = build_gate_b_audit_rows(
        draft_matrix_rows=draft_matrix_rows,
        approved_count=_count_approved(approval_rows),
    )
    gate_b_verdict = gate_b_verdict_from_audit(draft_audit_rows)
    if gate_b_verdict != "BLOCKED_NEEDS_DRAFT_CAPITAL":
        raise ValueError(f"Unexpected Gate B verdict for current source state: {gate_b_verdict}")

    args.approval_root.mkdir(parents=True, exist_ok=True)
    args.draft_capital_root.mkdir(parents=True, exist_ok=True)

    _write_csv(
        args.approval_root / "cfbd_rookie_identity_human_approval_v1.csv",
        APPROVAL_COLUMNS,
        approval_rows,
    )
    _write_approval_summary(
        args.approval_root / "CFBD_ROOKIE_IDENTITY_APPROVAL_V1_SUMMARY.md",
        approval_rows,
    )
    _write_approval_readme(args.approval_root / "README.md", approval_rows)

    _write_csv(
        args.draft_capital_root / "rookie_draft_capital_source_audit_v1.csv",
        DRAFT_AUDIT_COLUMNS,
        draft_audit_rows,
    )
    _write_gate_b_blocker(
        args.draft_capital_root / "00_GATE_B_DRAFT_CAPITAL_BLOCKER.md",
        draft_audit_rows=draft_audit_rows,
        approved_count=_count_approved(approval_rows),
    )
    _write_gate_b_readme(
        args.draft_capital_root / "README.md",
        draft_audit_rows=draft_audit_rows,
        approved_count=_count_approved(approval_rows),
    )

    print(
        {
            "gate_a": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
            "approved_identity_rows": _count_approved(approval_rows),
            "deferred_identity_rows": len(approval_rows) - _count_approved(approval_rows),
            "gate_b": gate_b_verdict,
        }
    )
    return 0


def build_approval_rows(packet_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in packet_rows:
        match_status = _evidence_value(row, "cfbd_match_status")
        identity_confidence = _evidence_value(row, "identity_confidence")
        approved = _is_review_only_approval_candidate(
            row,
            match_status=match_status,
            identity_confidence=identity_confidence,
        )
        output.append(
            {
                "player_id": _clean(row.get("player_id")),
                "player_name": _clean(row.get("player_name")),
                "position": _clean(row.get("position")),
                "college_team": _clean(row.get("college_team")),
                "nfl_team_if_available": _clean(row.get("nfl_team_if_available")),
                "draft_year_if_available": _clean(row.get("draft_year_if_available")),
                "cfbd_candidate_id": _clean(row.get("cfbd_candidate_id")),
                "cfbd_name": _clean(row.get("cfbd_name")),
                "cfbd_position": _clean(row.get("cfbd_position")),
                "cfbd_team": _clean(row.get("cfbd_team")),
                "cfbd_years": _clean(row.get("cfbd_years")),
                "match_status": match_status,
                "identity_confidence": identity_confidence,
                "match_evidence": _clean(row.get("match_evidence")),
                "production_context_summary": _clean(row.get("production_context_summary")),
                "ambiguity_flags": _clean(row.get("ambiguity_flags")) or "none",
                "recommended_review_decision": _clean(
                    row.get("recommended_review_decision")
                ),
                "human_decision": "APPROVE_REVIEW_ONLY" if approved else "DEFER",
                "human_notes": "",
                "approved_by_human": "true" if approved else "false",
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "approval_scope": APPROVAL_SCOPE,
                "approval_source": APPROVAL_SOURCE if approved else "",
                "approval_notes": APPROVAL_NOTES if approved else "Deferred for human review.",
                "gate_a_status": (
                    "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL"
                    if approved
                    else "BLOCKED_IDENTITY_REVIEW_REQUIRED"
                ),
            }
        )
    return output


def validate_approval_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Approval artifact must not be empty.")
    approved = [row for row in rows if row["approved_by_human"] == "true"]
    for row in rows:
        missing = [column for column in APPROVAL_COLUMNS if column not in row]
        if missing:
            raise ValueError(f"Approval artifact missing columns: {missing}")
        if row["review_only"] != "true":
            raise ValueError("All approval rows must keep review_only=true.")
        if row["model_use_allowed"] != "false":
            raise ValueError("Approval artifact must keep model_use_allowed=false.")
        if row["training_allowed"] != "false":
            raise ValueError("Approval artifact must keep training_allowed=false.")
        if row["approved_by_human"] == "true":
            if row["human_decision"] != "APPROVE_REVIEW_ONLY":
                raise ValueError("Approved rows must use APPROVE_REVIEW_ONLY.")
            if row["match_status"] != "exact_match":
                raise ValueError("Only exact_match rows may be approved.")
            if row["identity_confidence"] != "HIGH":
                raise ValueError("Only HIGH confidence rows may be approved.")
            if row["ambiguity_flags"] != "none":
                raise ValueError("Ambiguous rows must not be approved.")
            if row["recommended_review_decision"] != "APPROVE_REVIEW_ONLY":
                raise ValueError("Approved rows must match the prior recommendation.")
            if row["production_context_summary"] == "Not enough information":
                raise ValueError("Rows with missing production context must not be approved.")
    deferred_bad = [
        row
        for row in rows
        if row["match_status"] in {"ambiguous", "possible_candidate"}
        and row["approved_by_human"] != "false"
    ]
    if deferred_bad:
        raise ValueError("Ambiguous/possible rows must remain unapproved.")
    if len(approved) != 157:
        raise ValueError(f"Expected 157 approved rows; found {len(approved)}.")


def build_gate_b_audit_rows(
    *,
    draft_matrix_rows: list[dict[str, str]],
    approved_count: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = [
        {
            "source_name": "CFBD rookie identity approval V1",
            "source_path": (
                "docs/hq/rookie_outcomes/"
                "cfbd_rookie_identity_approval_v1_20260629/"
                "cfbd_rookie_identity_human_approval_v1.csv"
            ),
            "scope": "approved CFBD-to-NWR identity rows only",
            "availability_status": "identity_review_only",
            "approved_identity_rows_covered": str(approved_count),
            "draft_year_available": "partial_from_packet_blank_for_all_rows",
            "draft_round_available": "false",
            "overall_pick_available": "false",
            "drafted_team_available": "false",
            "udfa_status_available": "false",
            "age_at_draft_available": "false",
            "historical_classes_available": "false",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "gate_b_use_status": "blocked_identity_only_not_draft_capital",
            "blocker_reason": "Identity approval does not include NFL draft capital fields.",
            "safe_next_step": "Create tracked draft-capital review source with provenance.",
        }
    ]

    for source in draft_matrix_rows:
        status = _clean(source.get("availability_status"))
        source_name = _clean(source.get("source_name"))
        blocked_reason = _clean(source.get("blocked_reason"))
        gate_status = "blocked"
        if status in {"partial", "partial_local_only", "sample_only"}:
            gate_status = "blocked_partial_not_approved"
        if status == "missing":
            gate_status = "blocked_missing"
        if status == "blocked_policy":
            gate_status = "blocked_policy"
        rows.append(
            {
                "source_name": source_name,
                "source_path": _clean(source.get("source_path")),
                "scope": _clean(source.get("scope")),
                "availability_status": status,
                "approved_identity_rows_covered": "0",
                "draft_year_available": _field_available(source_name, "draft_year"),
                "draft_round_available": _field_available(source_name, "draft_round"),
                "overall_pick_available": _field_available(source_name, "overall_pick"),
                "drafted_team_available": _field_available(source_name, "drafted_team"),
                "udfa_status_available": "false",
                "age_at_draft_available": "false",
                "historical_classes_available": "false",
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "gate_b_use_status": gate_status,
                "blocker_reason": blocked_reason,
                "safe_next_step": _clean(source.get("safe_next_step")),
            }
        )
    return rows


def gate_b_verdict_from_audit(rows: list[dict[str, str]]) -> str:
    has_approved_source = any(
        row["gate_b_use_status"] == "approved_review_only_draft_capital" for row in rows
    )
    if has_approved_source:
        return "GREEN_DRAFT_CAPITAL_REVIEW_ARTIFACT"
    return "BLOCKED_NEEDS_DRAFT_CAPITAL"


def _is_review_only_approval_candidate(
    row: dict[str, str],
    *,
    match_status: str,
    identity_confidence: str,
) -> bool:
    ambiguity_flags = _clean(row.get("ambiguity_flags")) or "none"
    return (
        match_status == "exact_match"
        and identity_confidence == "HIGH"
        and _clean(row.get("recommended_review_decision")) == "APPROVE_REVIEW_ONLY"
        and ambiguity_flags == "none"
        and _clean(row.get("production_context_summary")) != "Not enough information"
    )


def _field_available(source_name: str, field_name: str) -> str:
    lowered = source_name.lower()
    if "2026 draft capital snapshot" in lowered and field_name in {
        "draft_year",
        "draft_round",
        "overall_pick",
    }:
        return "partial_local_only"
    return "false"


def _evidence_value(row: dict[str, str], key: str) -> str:
    evidence = _clean(row.get("match_evidence"))
    for part in evidence.split(";"):
        stripped = part.strip()
        prefix = f"{key}="
        if stripped.startswith(prefix):
            return stripped.removeprefix(prefix).strip()
    return ""


def _write_approval_summary(path: Path, rows: list[dict[str, str]]) -> None:
    status_counts = Counter(row["match_status"] for row in rows)
    confidence_counts = Counter(row["identity_confidence"] for row in rows)
    approved_count = _count_approved(rows)
    lines = [
        "# CFBD Rookie Identity Approval V1 Summary - 2026-06-29",
        "",
        "## Verdict",
        "",
        "`GREEN_REVIEW_ONLY_IDENTITY_APPROVAL`",
        "",
        "The user approved CFBD identity review-only advancement for high-confidence",
        "exact matches only. This is not model, training, or source-truth approval.",
        "",
        "## Counts",
        "",
        f"- Input rows: {len(rows)}",
        f"- Approved review-only identity rows: {approved_count}",
        f"- Deferred rows: {len(rows) - approved_count}",
        "- `model_use_allowed=true` rows: 0",
        "- `training_allowed=true` rows: 0",
        "",
        "## Match Status Counts",
        "",
        *[f"- {key}: {value}" for key, value in sorted(status_counts.items())],
        "",
        "## Identity Confidence Counts",
        "",
        *[f"- {key}: {value}" for key, value in sorted(confidence_counts.items())],
        "",
        "## Guardrails",
        "",
        "- Ambiguous and possible rows remain `approved_by_human=false`.",
        "- All rows remain `review_only=true`.",
        "- All rows remain `model_use_allowed=false`.",
        "- All rows remain `training_allowed=false`.",
        "- Approval scope is `identity_review_only`.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_approval_readme(path: Path, rows: list[dict[str, str]]) -> None:
    approved_count = _count_approved(rows)
    lines = [
        "# CFBD Rookie Identity Approval V1",
        "",
        "This folder records conservative human approval for CFBD rookie identity",
        "links only. It does not approve CFBD production as model input, training",
        "truth, or source truth.",
        "",
        "## Files",
        "",
        "- `cfbd_rookie_identity_human_approval_v1.csv`",
        "- `CFBD_ROOKIE_IDENTITY_APPROVAL_V1_SUMMARY.md`",
        "",
        "## Status",
        "",
        f"- Approved review-only identity rows: {approved_count}",
        f"- Deferred rows: {len(rows) - approved_count}",
        "- Model-use approvals: 0",
        "- Training approvals: 0",
        "",
        "## Next Gate",
        "",
        "Gate B must still provide tracked, review-only NFL draft capital before",
        "any historical labels, feature policy, modeling, display, or Rankings work.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_gate_b_blocker(
    path: Path,
    *,
    draft_audit_rows: list[dict[str, str]],
    approved_count: int,
) -> None:
    lines = [
        "# Gate B Draft Capital Blocker - 2026-06-29",
        "",
        "## Gate Result",
        "",
        "`BLOCKED_NEEDS_DRAFT_CAPITAL`",
        "",
        "Gate A is now green for review-only identity approval, but Gate B is not",
        "green because no tracked approved draft-capital artifact covers the",
        "approved identity subset and historical rookie classes.",
        "",
        "## Evidence",
        "",
        f"- Approved CFBD identity review-only rows: {approved_count}",
        "- 2026 draft capital exists only as a documented/local-only snapshot.",
        "- Historical draft capital remains missing or prototype/sample-only.",
        "- UDFA status, drafted team, age at draft, and historical coverage are not",
        "  available in a tracked approved artifact for this lane.",
        "- No local_exports/raw/source-cache data was promoted.",
        "",
        "## Source Audit",
        "",
        *[
            (
                f"- {row['source_name']}: {row['gate_b_use_status']} "
                f"({row['availability_status']})"
            )
            for row in draft_audit_rows
        ],
        "",
        "## Stop Decision",
        "",
        "The lane stops at Gate B. Gates C-G were not run, and no rookie outcome",
        "probabilities, labels, display artifacts, or Rankings columns were created.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_gate_b_readme(
    path: Path,
    *,
    draft_audit_rows: list[dict[str, str]],
    approved_count: int,
) -> None:
    lines = [
        "# Rookie Draft Capital Review V1",
        "",
        "This folder documents the Gate B retry after CFBD identity review-only",
        "approval. It is a blocker package, not a draft-capital data product.",
        "",
        "## Verdict",
        "",
        "`BLOCKED_NEEDS_DRAFT_CAPITAL`",
        "",
        "## Counts",
        "",
        f"- Approved identity rows available for Gate B: {approved_count}",
        f"- Draft-capital sources audited: {len(draft_audit_rows)}",
        "- Review-only draft-capital rows produced: 0",
        "",
        "## Guardrails",
        "",
        "- No rookie outcome labels were built.",
        "- No model or probability artifact was built.",
        "- No Rankings integration was attempted.",
        "- Missing draft capital remains blocked, not converted to `0%`.",
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


def _count_approved(rows: list[dict[str, str]]) -> int:
    return sum(row["approved_by_human"] == "true" for row in rows)


def _clean(value: object) -> str:
    return str(value or "").strip()


if __name__ == "__main__":
    raise SystemExit(main())
