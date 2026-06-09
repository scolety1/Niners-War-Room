from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.pre_decision_checklist_service import (  # noqa: E402
    build_pre_decision_checklist,
    pre_decision_checklist_rows,
    pre_decision_checklist_summary_row,
)
from src.services.roster_decision_readiness_service import (  # noqa: E402
    build_roster_decision_readiness,
    roster_decision_gate_rows,
    roster_decision_summary_row,
)

DATA_PACK = ROOT / "local_exports" / "data_packs" / "lve_sleeper_20260505_pdf_ranks"
ACTIVE_MODEL_DIR = ROOT / "local_exports" / "active_veteran_model_public_sources"
PREVIEW_ROOT = ROOT / "local_exports" / "nflverse_model_previews"
REPORT_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v3" / "reports"
DOCS_ROOT = ROOT / "docs" / "codex"

CLASSIFICATION_HEADER = (
    "blocker_id",
    "source",
    "classification",
    "severity",
    "status",
    "decision_impact",
    "detail",
    "next_patch",
)


def main() -> None:
    preview_dir = _latest_preview()
    if preview_dir is None:
        raise FileNotFoundError("No Truth Set Lab v3 preview folder found.")

    active_roster = build_roster_decision_readiness(
        DATA_PACK,
        veteran_model_dir=ACTIVE_MODEL_DIR,
    )
    active_checklist = build_pre_decision_checklist(
        DATA_PACK,
        veteran_model_dir=ACTIVE_MODEL_DIR,
    )
    v3_roster = build_roster_decision_readiness(DATA_PACK, veteran_model_dir=preview_dir)
    v3_checklist = build_pre_decision_checklist(DATA_PACK, veteran_model_dir=preview_dir)

    suspicious = _read_rows(REPORT_ROOT / "truth_set_v3_audit_suspicious_rankings.csv")
    gaps = _read_rows(REPORT_ROOT / "truth_set_v3_remaining_agent_gap_list.csv")
    movements = _read_rows(REPORT_ROOT / "truth_set_v3_audit_major_movements.csv")

    classifications = _classifications(
        active_roster_rows=roster_decision_gate_rows(active_roster),
        active_checklist_rows=pre_decision_checklist_rows(active_checklist),
        v3_roster_rows=roster_decision_gate_rows(v3_roster),
        v3_checklist_rows=pre_decision_checklist_rows(v3_checklist),
        suspicious=suspicious,
        gaps=gaps,
        movements=movements,
    )

    recommendation = _recommendation(
        active_roster_ready=active_roster.passed,
        active_draft_ready=active_checklist.draft_ready,
        active_final_ready=active_checklist.final_money_ready,
        v3_roster_ready=v3_roster.passed,
        classifications=classifications,
    )

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    classification_path = REPORT_ROOT / "truth_set_v3_decision_blocker_classification.csv"
    summary_path = REPORT_ROOT / "truth_set_v3_decision_recommendation_summary.json"
    active_rows_path = REPORT_ROOT / "truth_set_v3_decision_active_gate_rows.csv"
    v3_rows_path = REPORT_ROOT / "truth_set_v3_decision_v3_preview_gate_rows.csv"

    _write_csv(classification_path, CLASSIFICATION_HEADER, classifications)
    _write_csv_from_rows(active_rows_path, pre_decision_checklist_rows(active_checklist))
    _write_csv_from_rows(v3_rows_path, pre_decision_checklist_rows(v3_checklist))
    summary = {
        "decision_recommendation": recommendation,
        "active_roster_gate": roster_decision_summary_row(active_roster),
        "active_pre_decision_gate": pre_decision_checklist_summary_row(active_checklist),
        "v3_preview_roster_gate": roster_decision_summary_row(v3_roster),
        "v3_preview_pre_decision_gate": pre_decision_checklist_summary_row(v3_checklist),
        "blocker_classification_counts": dict(
            Counter(row["classification"] for row in classifications)
        ),
        "blocker_rows": len(classifications),
        "v3_preview": str(preview_dir),
        "model_logic_changed": False,
        "draft_final_readiness_changed": False,
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _write_note(
        recommendation=recommendation,
        active_roster_summary=roster_decision_summary_row(active_roster),
        active_checklist_summary=pre_decision_checklist_summary_row(active_checklist),
        v3_roster_summary=roster_decision_summary_row(v3_roster),
        v3_checklist_summary=pre_decision_checklist_summary_row(v3_checklist),
        classifications=classifications,
        classification_path=classification_path,
        active_rows_path=active_rows_path,
        v3_rows_path=v3_rows_path,
        summary_path=summary_path,
    )
    print(json.dumps(summary, indent=2))


def _classifications(
    *,
    active_roster_rows: list[dict[str, object]],
    active_checklist_rows: list[dict[str, object]],
    v3_roster_rows: list[dict[str, object]],
    v3_checklist_rows: list[dict[str, object]],
    suspicious: list[dict[str, str]],
    gaps: list[dict[str, str]],
    movements: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, row in enumerate(active_checklist_rows, start=1):
        status = str(row.get("status") or "")
        if status != "ready":
            rows.append(
                _blocker(
                    f"active_gate_{index}",
                    "active_pre_decision_gate",
                    _gate_classification(row),
                    row.get("severity", ""),
                    status,
                    str(row.get("scope") or ""),
                    str(row.get("detail") or ""),
                    str(row.get("next_action") or ""),
                )
            )
    for index, row in enumerate(active_roster_rows, start=1):
        status = str(row.get("status") or "")
        if status != "ready":
            rows.append(
                _blocker(
                    f"active_roster_{index}",
                    "active_roster_gate",
                    _gate_classification(row),
                    row.get("severity", ""),
                    status,
                    "Roster",
                    str(row.get("detail") or ""),
                    str(row.get("next_action") or ""),
                )
            )
    for index, row in enumerate(v3_checklist_rows, start=1):
        status = str(row.get("status") or "")
        if status != "ready":
            rows.append(
                _blocker(
                    f"v3_preview_gate_{index}",
                    "v3_preview_gate",
                    "data blocker",
                    row.get("severity", ""),
                    status,
                    str(row.get("scope") or ""),
                    (
                        "V3 preview folder is not yet a full active model source directory: "
                        f"{row.get('detail') or ''}"
                    ),
                    (
                        "Promote v3 preview through the controlled model pipeline only after "
                        "source coverage, identity, and outlier artifacts are generated in the "
                        "active-model schema."
                    ),
                )
            )
    for index, row in enumerate(v3_roster_rows, start=1):
        status = str(row.get("status") or "")
        if status != "ready":
            rows.append(
                _blocker(
                    f"v3_roster_gate_{index}",
                    "v3_preview_roster_gate",
                    "data blocker",
                    row.get("severity", ""),
                    status,
                    "Roster",
                    (
                        "V3 preview cannot independently pass roster readiness yet: "
                        f"{row.get('detail') or ''}"
                    ),
                    (
                        "Do not mark v3 promoted/decision-ready until matching source coverage, "
                        "identity, and outlier artifacts exist for the v3 source root."
                    ),
                )
            )
    high_suspicious = [
        row for row in suspicious if str(row.get("severity") or "").lower() in {"high", "blocking"}
    ]
    if high_suspicious:
        players = sorted({row.get("player_name", "") for row in high_suspicious})
        rows.append(
            _blocker(
                "v3_high_suspicious_rankings",
                "v3_ranking_audit",
                "confidence blocker",
                "high",
                "review",
                "Roster + Draft",
                (
                    f"{len(high_suspicious)} high-severity v3 suspicious rows remain "
                    f"for: {', '.join(player for player in players if player)}"
                ),
                "Review player receipts and patch only source, identity, or normalization bugs.",
            )
        )
    formula_rows = [
        row
        for row in suspicious
        if str(row.get("suspicion_type") or "") == "possible_formula_imbalance"
    ]
    if formula_rows:
        players = sorted({row.get("player_name", "") for row in formula_rows})
        rows.append(
            _blocker(
                "v3_possible_formula_imbalance",
                "v3_ranking_audit",
                "formula blocker",
                "medium",
                "review",
                "Roster + Draft",
                (
                    f"{len(formula_rows)} possible formula-imbalance rows remain "
                    f"for: {', '.join(player for player in players if player)}"
                ),
                (
                    "Write fixture-backed formula proposal before changing weights; do not tune "
                    "from rankings alone."
                ),
            )
        )
    large_movements = [
        row
        for row in movements
        if _float(row.get("absolute_value_delta")) >= 5.0
        or abs(_float(row.get("rank_delta"))) >= 50
    ]
    if large_movements:
        rows.append(
            _blocker(
                "v3_large_movements_need_receipt_review",
                "v3_movement_vs_v2",
                "confidence blocker",
                "medium",
                "review",
                "Roster + Draft",
                f"{len(large_movements)} v2-to-v3 movements exceed review thresholds.",
                "Review movement receipts before promoting v3 values into active decisions.",
            )
        )
    for index, row in enumerate(gaps, start=1):
        status_bucket = str(row.get("status_bucket") or "")
        classification = _gap_classification(status_bucket)
        if classification == "accepted limitation":
            continue
        rows.append(
            _blocker(
                f"remaining_gap_{index}",
                "v3_remaining_gap_list",
                classification,
                "medium",
                "review",
                "Roster + Draft",
                (
                    f"{row.get('field_or_bucket')}: {row.get('model_impact')} "
                    f"({row.get('affected_player_count')} affected players)."
                ),
                str(row.get("next_local_action") or row.get("agent_action") or ""),
            )
        )
    return rows


def _recommendation(
    *,
    active_roster_ready: bool,
    active_draft_ready: bool,
    active_final_ready: bool,
    v3_roster_ready: bool,
    classifications: list[dict[str, object]],
) -> str:
    formula_blockers = [
        row for row in classifications if row["classification"] == "formula blocker"
    ]
    data_blockers = [row for row in classifications if row["classification"] == "data blocker"]
    confidence_blockers = [
        row for row in classifications if row["classification"] == "confidence blocker"
    ]
    if active_roster_ready and not v3_roster_ready:
        return (
            "Roster decisions are ready only on the current active model gate. "
            "Truth Set Lab v3 remains review-only and should not be promoted until "
            "its preview artifacts can pass active-schema source coverage, identity, "
            "and outlier gates."
        )
    if active_roster_ready and not active_draft_ready and not active_final_ready:
        return (
            "Roster decisions are ready; draft and final money decisions remain blocked "
            "until draft-pool and final calibration gates pass."
        )
    if data_blockers or confidence_blockers:
        return (
            "Still review-only for roster decisions. Fix data/confidence blockers before "
            "formula work."
        )
    if formula_blockers:
        return (
            "Data gates are close enough for formula-review work, but formula changes need "
            "fixture-backed proposals before decision-ready status."
        )
    return "No blocker rows were found; use the formal app gates before unlocking decisions."


def _gate_classification(row: dict[str, object]) -> str:
    text = " ".join(str(value or "").lower() for value in row.values())
    if "identity" in text:
        return "data blocker"
    if "source" in text or "coverage" in text or "data" in text:
        return "data blocker"
    if "outlier" in text or "confidence" in text:
        return "confidence blocker"
    if "receipt" in text:
        return "UI blocker"
    return "accepted limitation"


def _gap_classification(status_bucket: str) -> str:
    if status_bucket == "can_derive_locally":
        return "accepted limitation"
    if status_bucket == "agent_can_verify_source":
        return "data blocker"
    if status_bucket == "possible_paid_only_field":
        return "accepted limitation"
    if status_bucket == "agent_should_not_collect_manually":
        return "accepted limitation"
    return "data blocker"


def _blocker(
    blocker_id: str,
    source: str,
    classification: str,
    severity: object,
    status: str,
    decision_impact: str,
    detail: str,
    next_patch: str,
) -> dict[str, object]:
    return {
        "blocker_id": blocker_id,
        "source": source,
        "classification": classification,
        "severity": severity,
        "status": status,
        "decision_impact": decision_impact,
        "detail": detail,
        "next_patch": next_patch,
    }


def _write_note(
    *,
    recommendation: str,
    active_roster_summary: dict[str, object],
    active_checklist_summary: dict[str, object],
    v3_roster_summary: dict[str, object],
    v3_checklist_summary: dict[str, object],
    classifications: list[dict[str, object]],
    classification_path: Path,
    active_rows_path: Path,
    v3_rows_path: Path,
    summary_path: Path,
) -> None:
    counts = Counter(row["classification"] for row in classifications)
    seen_patches: set[tuple[object, object]] = set()
    unique_patches: list[str] = []
    for row in classifications:
        key = (row["classification"], row["next_patch"])
        if key in seen_patches:
            continue
        seen_patches.add(key)
        unique_patches.append(f"- {row['classification']}: {row['next_patch']}")
    next_patches = "\n".join(unique_patches[:8])
    if not next_patches:
        next_patches = "- No patch list generated; formal gates should be rechecked."
    note = "\n".join(
        [
            "# Truth Set Lab v3 Decision Recommendation",
            "",
            "Status: no model logic changed. This is a gate/recommendation report only.",
            "",
            "## Recommendation",
            "",
            recommendation,
            "",
            "## Gate Results",
            "",
            f"- Active roster gate: `{active_roster_summary['roster_decision_badge']}`",
            f"- Active draft gate: `{active_checklist_summary['Draft Ready']}`",
            (
                "- Active final money gate: "
                f"`{active_checklist_summary['Final Money Decisions Ready']}`"
            ),
            f"- V3 preview roster gate: `{v3_roster_summary['roster_decision_badge']}`",
            f"- V3 preview draft gate: `{v3_checklist_summary['Draft Ready']}`",
            (
                "- V3 preview final money gate: "
                f"`{v3_checklist_summary['Final Money Decisions Ready']}`"
            ),
            "",
            "## Blocker Classification",
            "",
            *(f"- {name}: {count}" for name, count in sorted(counts.items())),
            "",
            "## Exact Next Patch List",
            "",
            next_patches,
            "",
            "## Files",
            "",
            f"- Summary: `{summary_path}`",
            f"- Blocker classification: `{classification_path}`",
            f"- Active gate rows: `{active_rows_path}`",
            f"- V3 preview gate rows: `{v3_rows_path}`",
            "",
        ]
    )
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_DECISION_RECOMMENDATION.md").write_text(
        note,
        encoding="utf-8",
    )


def _latest_preview() -> Path | None:
    candidates = [path for path in PREVIEW_ROOT.glob("truth_set_lab_v3_preview_*") if path.is_dir()]
    return sorted(candidates, key=lambda path: path.stat().st_mtime)[-1] if candidates else None


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_csv_from_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = tuple(rows[0].keys())
    _write_csv(path, fieldnames, rows)


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(str(value))
    except ValueError:
        return default


if __name__ == "__main__":
    main()
