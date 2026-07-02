from __future__ import annotations

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CORE_USAGE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_core_usage_review_dataset_v1_20260701"
)
REDZONE_DIR = CORE_USAGE_DIR
V1_SUBSTRATE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_substrate_expansion_v1_20260701"
)
V2_SUBSTRATE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_substrate_expansion_v2_20260701"
)
V3_SUBSTRATE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
)
SOURCE_CONTRACT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_source_contract_v1_20260701"
)
CANDIDATE_SEARCH_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_search_v1_20260701"
)
CANDIDATE_REVIEW_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_review_v1_20260701"
)
PROMOTION_GATE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_promotion_gate_prep_v1_20260701"
)
RISK_RESCUE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_risk_rescue_sprint_v1_20260701"
)
CUTLINE_REFINEMENT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_cutline_safe_refinement_v1_20260701"
)
DEVELOPMENT_LAB_SAFE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "development_lab"
    / "development_lab_safe_v1_v2_manual_context_upgrade_20260630"
)
DEVELOPMENT_LAB_REVIEW_UPGRADE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "development_lab"
    / "development_lab_review_upgrade_v1_20260701"
)
TARGETED_REDESIGN_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_targeted_redesign_v1_20260701"
)
SHADOW_REVIEW_GATE_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_shadow_review_gate_v1_20260701"
)
UI_ALTERNATIVES_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "app_ux"
    / "ui_alternatives_preview_v1_20260701"
)

NOT_PRESENT = "Not present in current HQ"
REVIEW_ONLY = "review-only/status display"


def summary_metrics() -> dict[str, str]:
    artifacts = artifact_index_rows()
    open_queue = review_queue_rows()
    return {
        "artifacts_indexed": str(len(artifacts)),
        "review_only_artifacts": str(
            sum("review" in row["Safe use"].lower() for row in artifacts)
        ),
        "production_approved": "no",
        "shadow_review_approved": "no",
        "open_review_items": str(len(open_queue)),
    }


def phase_timeline_rows() -> list[dict[str, str]]:
    return [
        _phase_row("NFLVerse phase", "CLOSED", CORE_USAGE_DIR),
        _phase_row("Core Usage Dataset V1", "MERGED_REVIEW_ONLY", CORE_USAGE_DIR),
        _phase_row("Historical substrate V1", "MERGED_REVIEW_ONLY", V1_SUBSTRATE_DIR),
        _phase_row("Historical substrate V2", "MERGED_REVIEW_ONLY", V2_SUBSTRATE_DIR),
        _phase_row("Historical substrate V3", "MERGED_REVIEW_ONLY", V3_SUBSTRATE_DIR),
        _phase_row("Source Contract V1", "MERGED_REVIEW_ONLY", SOURCE_CONTRACT_DIR),
        _phase_row("Candidate Search", "MERGED_REVIEW_ONLY", CANDIDATE_SEARCH_DIR),
        _phase_row("Candidate Review", "MERGED_REVIEW_ONLY", CANDIDATE_REVIEW_DIR),
        _phase_row("Promotion Gate Prep", "MERGED_HOLD", PROMOTION_GATE_DIR),
        _phase_row("Risk Rescue Sprint", "MERGED_REVIEW_ONLY", RISK_RESCUE_DIR),
        _phase_row("Cutline Refinement", "MERGED_PARTIAL_HOLD", CUTLINE_REFINEMENT_DIR),
        _phase_row("Targeted Redesign", "MERGED_HUMAN_REVIEW_ONLY", TARGETED_REDESIGN_DIR),
        _phase_row(
            "Shadow Review Gate",
            "MERGED_REVIEW_ONLY_GO_PACKET",
            SHADOW_REVIEW_GATE_DIR,
        ),
        _phase_row(
            "Development Lab Review Upgrade",
            "MERGED_REVIEW_ONLY",
            DEVELOPMENT_LAB_REVIEW_UPGRADE_DIR,
        ),
        {
            "Phase": "Current candidate status",
            "Status": "usage_opportunity_volume HOLD",
            "Source": _relative(PROMOTION_GATE_DIR / "advance_hold_reject_decision_card.md"),
            "Evidence": "Human review hold; no shadow review or production approval.",
        },
    ]


def current_decision_board_rows() -> list[dict[str, str]]:
    return [
        {
            "Item": "usage_opportunity_volume",
            "Status": "HOLD",
            "Meaning": "Current candidate evidence is preserved for human review only.",
        },
        {
            "Item": "qb_guard_soft_blend",
            "Status": "USEFUL_RESCUE",
            "Meaning": "Useful elite-QB regression rescue evidence.",
        },
        {
            "Item": "rb_wr_cutline_safe_blend",
            "Status": "PARTIAL_REFINEMENT",
            "Meaning": "Partial cutline refinement; candidate still held.",
        },
        {
            "Item": "wr_boundary_breakout_sensitivity_guard",
            "Status": "HUMAN_REVIEW_ONLY",
            "Meaning": "Targeted redesign evidence; no shadow-review approval.",
        },
        {
            "Item": "Shadow review packet",
            "Status": "GO_REVIEW_ONLY_PACKET",
            "Meaning": (
                "Only a static side-by-side review packet may proceed; no app, "
                "ranking, model, runtime, or production wiring is approved."
            ),
        },
        {
            "Item": "Production",
            "Status": "NOT_APPROVED",
            "Meaning": "No production formula, rank, model, or normal app behavior is changed.",
        },
    ]


def artifact_index_rows() -> list[dict[str, str]]:
    return [
        _artifact_row(
            "NFLVerse Core Usage Review Dataset V1",
            CORE_USAGE_DIR,
            _core_usage_row_count(),
            "76,804 player-week rows; 40 schema fields; 2024-2025.",
        ),
        _artifact_row(
            "Red-zone sidecar V1",
            REDZONE_DIR,
            _redzone_row_count(),
            "6,424 sidecar rows; `rz_att` remains blocked.",
        ),
        _artifact_row(
            "Historical Tuning substrate V1",
            V1_SUBSTRATE_DIR,
            "tracked",
            "Historical review substrate phase.",
        ),
        _artifact_row(
            "Historical Tuning substrate V2",
            V2_SUBSTRATE_DIR,
            "tracked",
            "Expansion phase before V3 source semantics.",
        ),
        _artifact_row(
            "Historical Tuning substrate V3",
            V3_SUBSTRATE_DIR,
            _v3_row_count(),
            "5,518 feature/target rows; 22 reviewed features.",
        ),
        _artifact_row(
            "Source Contract V1",
            SOURCE_CONTRACT_DIR,
            _source_contract_counts(),
            "18 allowed review-only, 4 null-fenced, 11 blocked families.",
        ),
        _artifact_row(
            "Candidate Search V1",
            CANDIDATE_SEARCH_DIR,
            "9 candidates",
            "Candidate search packet; no production approval.",
        ),
        _artifact_row(
            "Candidate Review V1",
            CANDIDATE_REVIEW_DIR,
            "2 metric rows",
            "Human review packet for `usage_opportunity_volume`.",
        ),
        _artifact_row(
            "Promotion Gate Prep V1",
            PROMOTION_GATE_DIR,
            "70 tradeoff rows",
            "`usage_opportunity_volume` held for human review.",
        ),
        _artifact_row(
            "Risk Rescue Sprint V1",
            RISK_RESCUE_DIR,
            "7 fixed rescue variants",
            "`qb_guard_soft_blend` recorded as useful rescue evidence.",
        ),
        _artifact_row(
            "Cutline Safe Refinement V1",
            CUTLINE_REFINEMENT_DIR,
            "5 remaining cutline rows",
            "`rb_wr_cutline_safe_blend` recorded as partial refinement.",
        ),
        _artifact_row(
            "Targeted Redesign V1",
            TARGETED_REDESIGN_DIR,
            "12 fixed redesign variants / 2 remaining concern rows",
            "`wr_boundary_breakout_sensitivity_guard` recorded for human review only.",
        ),
        _artifact_row(
            "Shadow Review Gate V1",
            SHADOW_REVIEW_GATE_DIR,
            "GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY",
            "Static side-by-side shadow packet approved for review only.",
        ),
        _artifact_row(
            "Development Lab Safe Manual Context",
            DEVELOPMENT_LAB_SAFE_DIR,
            "tracked",
            "Existing display-only/manual Development Lab context packet.",
        ),
        _artifact_row(
            "Development Lab Review Upgrade V1",
            DEVELOPMENT_LAB_REVIEW_UPGRADE_DIR,
            "tracked",
            "Review-only Development Lab cockpit upgrade merged before Evidence Hub.",
        ),
    ]


def guardrail_summary_rows() -> list[dict[str, str]]:
    return [
        {
            "Guardrail": "Production formula/model/app/rank/source truth",
            "Status": "NO_CHANGE",
            "Evidence": "Hub is a navigation/status surface only.",
        },
        {
            "Guardrail": "Blocked fields",
            "Status": "ACTIVE",
            "Evidence": (
                "Routes, TPRR, YPRR, ambiguous `rz_att`, and unapproved joins stay blocked."
            ),
        },
        {
            "Guardrail": "Null-fenced features",
            "Status": "ACTIVE",
            "Evidence": "Source Contract V1 requires explicit missingness handling.",
        },
        {
            "Guardrail": "Current-only context restrictions",
            "Status": "ACTIVE",
            "Evidence": "Current context is not historical formula input.",
        },
        {
            "Guardrail": "Candidate outputs",
            "Status": "NOT_WIRED",
            "Evidence": "No candidate output feeds rankings, draft, trade, or player compare.",
        },
    ]


def review_queue_rows() -> list[dict[str, str]]:
    casebook = _csv_rows(CUTLINE_REFINEMENT_DIR / "remaining_cutline_casebook.csv")
    names = "; ".join(row.get("player_name", "") for row in casebook if row.get("player_name"))
    return [
        {
            "Queue item": "Remaining cutline players",
            "Status": f"{len(casebook)} rows open",
            "Evidence": names,
            "Next review": "Static casebook or targeted redesign review.",
        },
        {
            "Queue item": "Targeted redesign result",
            "Status": "PRESENT" if TARGETED_REDESIGN_DIR.exists() else NOT_PRESENT,
            "Evidence": (
                _relative(TARGETED_REDESIGN_DIR / "targeted_redesign_summary.md")
                if TARGETED_REDESIGN_DIR.exists()
                else ""
            ),
            "Next review": "Covered by Shadow Review Gate; keep concern cases visible.",
        },
        {
            "Queue item": "Shadow review gate result",
            "Status": "PRESENT" if SHADOW_REVIEW_GATE_DIR.exists() else NOT_PRESENT,
            "Evidence": (
                _relative(SHADOW_REVIEW_GATE_DIR / "shadow_review_decision.md")
                if SHADOW_REVIEW_GATE_DIR.exists()
                else ""
            ),
            "Next review": "Static side-by-side shadow comparison packet only.",
        },
        {
            "Queue item": "UI alternatives result",
            "Status": "PRESENT" if UI_ALTERNATIVES_DIR.exists() else NOT_PRESENT,
            "Evidence": _relative(UI_ALTERNATIVES_DIR) if UI_ALTERNATIVES_DIR.exists() else "",
            "Next review": "Preview only; no production promotion.",
        },
        {
            "Queue item": "Development Lab review upgrade",
            "Status": (
                "PRESENT"
                if DEVELOPMENT_LAB_REVIEW_UPGRADE_DIR.exists()
                else "NOT_PRESENT_ON_THIS_BASE"
            ),
            "Evidence": (
                _relative(DEVELOPMENT_LAB_REVIEW_UPGRADE_DIR)
                if DEVELOPMENT_LAB_REVIEW_UPGRADE_DIR.exists()
                else "Lane A branch should merge before this artifact appears on HQ."
            ),
            "Next review": "Present after Lane A merge; monitor from Evidence Hub only.",
        },
    ]


def safe_next_action_rows() -> list[dict[str, str]]:
    return [
        _safe_next_action("Read-only review", "Inspect evidence packets and status rows."),
        _safe_next_action(
            "Human decision gate",
            "Review the targeted redesign packet and remaining concern casebook.",
        ),
        _safe_next_action("Static casebook", "Create a human-readable casebook for open rows."),
        _safe_next_action("UI preview", "Show evidence status without normal app wiring."),
        _safe_next_action("No production promotion", "Keep all production gates closed."),
    ]


def artifact_index_source_map_rows() -> list[dict[str, str]]:
    return artifact_index_rows()


def phase_timeline_source_map_rows() -> list[dict[str, str]]:
    return phase_timeline_rows()


def _safe_next_action(action: str, scope: str) -> dict[str, str]:
    return {
        "Safe next action": action,
        "Scope": scope,
        "Status": "SAFE_REVIEW_ONLY",
        "Blocked": "No production promotion or normal decision-page wiring.",
    }


def _phase_row(phase: str, status: str, root: Path) -> dict[str, str]:
    return {
        "Phase": phase,
        "Status": status,
        "Source": _relative(root),
        "Evidence": _manifest_verdict(root / "artifact_manifest.md"),
    }


def _artifact_row(label: str, root: Path, row_count: str, summary: str) -> dict[str, str]:
    return {
        "Artifact": label,
        "Path": _relative(root),
        "Status": _manifest_verdict(root / "artifact_manifest.md"),
        "Rows / counts": row_count,
        "Known ref": _known_ref(root / "artifact_manifest.md"),
        "Validation summary": summary,
        "Safe use": REVIEW_ONLY,
    }


def _core_usage_row_count() -> str:
    rows = _csv_rows(CORE_USAGE_DIR / "nwr_nflverse_usage_row_count_report_v1.csv")
    return str(_sum_int(rows, "row_count"))


def _redzone_row_count() -> str:
    value = _markdown_number(
        CORE_USAGE_DIR / "core_usage_review_dataset_summary.md",
        r"Red-zone sidecar rows:\s*([0-9]+)",
    )
    return str(value) if value is not None else "Not enough information"


def _v3_row_count() -> str:
    rows = _csv_rows(V3_SUBSTRATE_DIR / "feature_target_row_count_report_v3.csv")
    return str(_sum_int(rows, "row_count"))


def _source_contract_counts() -> str:
    allowed = _csv_rows(SOURCE_CONTRACT_DIR / "allowed_review_only_feature_contract_v1.csv")
    null_fenced = _csv_rows(SOURCE_CONTRACT_DIR / "null_fenced_feature_contract_v1.csv")
    blocked = _csv_rows(SOURCE_CONTRACT_DIR / "blocked_feature_contract_v1.csv")
    return f"{len(allowed)} allowed / {len(null_fenced)} null-fenced / {len(blocked)} blocked"


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _sum_int(rows: list[dict[str, str]], column: str) -> int:
    total = 0
    for row in rows:
        value = str(row.get(column, "")).strip()
        if value:
            total += int(float(value))
    return total


def _markdown_number(path: Path, pattern: str) -> int | None:
    if not path.exists():
        return None
    match = re.search(pattern, path.read_text(encoding="utf-8"))
    if match is None:
        return None
    return int(match.group(1))


def _manifest_verdict(path: Path) -> str:
    if not path.exists():
        return NOT_PRESENT
    text = path.read_text(encoding="utf-8")
    match = re.search(r"Verdict:\s*`([^`]+)`", text)
    if match:
        return match.group(1)
    return "TRACKED_ARTIFACT"


def _known_ref(path: Path) -> str:
    if not path.exists():
        return NOT_PRESENT
    text = path.read_text(encoding="utf-8")
    for label in ("Base HEAD", "Branch", "Previous HEAD"):
        match = re.search(rf"{label}:\s*`?([^`\n]+)`?", text)
        if match:
            return f"{label}: {match.group(1).strip()}"
    return "Not enough information"


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()
