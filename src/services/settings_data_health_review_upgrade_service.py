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
NFLVERSE_REFRESH_HEALTH_DIR = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "nflverse_refresh_health_20260630"
)
NFLVERSE_DATASET_HEALTH_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_dataset_level_refresh_health_20260630"
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
DEVELOPMENT_LAB_REVIEW_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "development_lab"
    / "development_lab_review_upgrade_v1_20260701"
)
EVIDENCE_REVIEW_HUB_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "evidence_review_hub"
    / "evidence_review_hub_v1_20260701"
)

NOT_ENOUGH_INFORMATION = "Not enough information"
REVIEW_ONLY = "review-only/status display"
PROD_BLOCKED = "production blocked"


def artifact_health_board_rows() -> list[dict[str, str]]:
    return [
        _artifact_row(
            "NFLVerse Core Usage Review Dataset V1",
            CORE_USAGE_DIR,
            _core_usage_row_count(),
            "NFLVerse phase closed; practical review dataset output.",
        ),
        _artifact_row(
            "Red-zone sidecar",
            CORE_USAGE_DIR,
            _redzone_row_count(),
            "Sidecar-only context; ambiguous rz_att remains blocked.",
        ),
        _artifact_row(
            "Historical Tuning V3 substrate",
            V3_SUBSTRATE_DIR,
            _v3_row_count(),
            "Canonical feature/target substrate for review-only formula work.",
        ),
        _artifact_row(
            "Historical Tuning Source Contract V1",
            SOURCE_CONTRACT_DIR,
            _source_contract_counts(),
            "Allowed/null-fenced/blocked feature contract.",
        ),
        _artifact_row(
            "Historical Formula Candidate Search V1",
            CANDIDATE_SEARCH_DIR,
            "9 candidates",
            "Candidate evidence only; no production tuning.",
        ),
        _artifact_row(
            "Historical Formula Candidate Review V1",
            CANDIDATE_REVIEW_DIR,
            "2 metric rows",
            "Human review packet for usage_opportunity_volume.",
        ),
        _artifact_row(
            "Historical Formula Promotion Gate Prep V1",
            PROMOTION_GATE_DIR,
            "70 tradeoff rows",
            "Candidate held; production not approved.",
        ),
        _artifact_row(
            "Risk Rescue / Cutline / Targeted Redesign packets",
            TARGETED_REDESIGN_DIR,
            "rescue, refinement, targeted redesign",
            "Human-review evidence; no production promotion.",
        ),
        _artifact_row(
            "Shadow Review Gate V1",
            SHADOW_REVIEW_GATE_DIR,
            "GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY",
            "Static side-by-side shadow packet may proceed as review-only.",
        ),
        _artifact_row(
            "Development Lab Review Upgrade V1",
            DEVELOPMENT_LAB_REVIEW_DIR,
            "tracked",
            "Review-only cockpit merged.",
        ),
        _artifact_row(
            "Evidence Review Hub V1",
            EVIDENCE_REVIEW_HUB_DIR,
            "tracked",
            "Review-only evidence navigation merged.",
        ),
        _artifact_row(
            "NFLVerse Refresh Health",
            NFLVERSE_REFRESH_HEALTH_DIR,
            "tracked",
            "Existing source refresh-health evidence.",
        ),
        _artifact_row(
            "NFLVerse Dataset-Level Health",
            NFLVERSE_DATASET_HEALTH_DIR,
            "tracked",
            "Existing dataset-level health evidence.",
        ),
    ]


def source_contract_summary_rows() -> list[dict[str, str]]:
    allowed = _csv_rows(SOURCE_CONTRACT_DIR / "allowed_review_only_feature_contract_v1.csv")
    null_fenced = _csv_rows(SOURCE_CONTRACT_DIR / "null_fenced_feature_contract_v1.csv")
    blocked = _csv_rows(SOURCE_CONTRACT_DIR / "blocked_feature_contract_v1.csv")
    return [
        {
            "Contract area": "Allowed review-only features",
            "Count": str(len(allowed)),
            "Status": "REVIEW_ONLY",
            "Use today": "Can support review-only comparison and diagnostics.",
        },
        {
            "Contract area": "Null-fenced optional features",
            "Count": str(len(null_fenced)),
            "Status": "NULL_FENCED",
            "Use today": "Missing values must stay explicit; no silent zero-fill.",
        },
        {
            "Contract area": "Blocked feature families",
            "Count": str(len(blocked)),
            "Status": "BLOCKED",
            "Use today": "Do not use for production or source truth.",
        },
        {
            "Contract area": "Current-only context",
            "Count": "all current-only fields",
            "Status": "BLOCKED_FOR_HISTORICAL_FEATURES",
            "Use today": "Display/review context only; not historical formula input.",
        },
        {
            "Contract area": "Market/vendor/projection/rank fields",
            "Count": "all unapproved external ranking fields",
            "Status": "SOURCE_TRUTH_BLOCKED",
            "Use today": "May be displayed only where separately allowed.",
        },
    ]


def dataset_availability_rows() -> list[dict[str, str]]:
    return [
        _availability_row(
            "Core Usage Dataset V1",
            CORE_USAGE_DIR,
            _core_usage_row_count(),
            "MERGED_REVIEW_ONLY",
        ),
        _availability_row(
            "Red-zone sidecar",
            CORE_USAGE_DIR,
            _redzone_row_count(),
            "MERGED_REVIEW_ONLY_SIDECAR",
        ),
        _availability_row(
            "Historical V3 substrate",
            V3_SUBSTRATE_DIR,
            _v3_row_count(),
            "MERGED_REVIEW_ONLY",
        ),
        _availability_row(
            "Candidate evidence packets",
            CANDIDATE_SEARCH_DIR,
            "search/review/gate/rescue/refinement/redesign",
            "MERGED_HOLD_OR_REVIEW_ONLY",
        ),
        _availability_row(
            "Shadow review gate",
            SHADOW_REVIEW_GATE_DIR,
            "static packet gate",
            "GO_REVIEW_ONLY_PACKET",
        ),
        _availability_row(
            "Development Lab / Evidence Hub",
            EVIDENCE_REVIEW_HUB_DIR,
            "merged UI review surfaces",
            "MERGED_REVIEW_ONLY_UI",
        ),
    ]


def guardrail_status_rows() -> list[dict[str, str]]:
    return [
        _guardrail_row("Production formula changes", "BLOCKED", "No production formula changes."),
        _guardrail_row("Model training/tuning", "BLOCKED", "No model training or tuning."),
        _guardrail_row("Rankings/default behavior", "BLOCKED", "No rank/default behavior changes."),
        _guardrail_row("Hidden sort", "BLOCKED", "No hidden sort."),
        _guardrail_row("Recommendations", "BLOCKED", "No recommendations."),
        _guardrail_row("Source-truth promotion", "BLOCKED", "No source-truth promotion."),
        _guardrail_row("Routes/TPRR/YPRR/route proxies", "BLOCKED", "No route proxy creation."),
        _guardrail_row("Ambiguous rz_att", "BLOCKED", "Do not normalize ambiguous rz_att."),
        _guardrail_row(
            "Missing/null semantics",
            "ACTIVE",
            "Missing values stay null or Not enough information unless "
            "source semantics prove zero.",
        ),
        _guardrail_row(
            "Current-only context",
            "ACTIVE",
            "Current roster/status/injury/depth/schedule context is not historical feature input.",
        ),
    ]


def safe_use_today_rows() -> list[dict[str, str]]:
    return [
        _safe_row("Display-only facts", "SAFE_DISPLAY", "Use as labeled display context."),
        _safe_row("Review-only datasets", "SAFE_REVIEW", "Use for human review and diagnostics."),
        _safe_row("Human-review packets", "SAFE_REVIEW", "Use to inspect evidence and blockers."),
        _safe_row(
            "Static shadow packet",
            "SAFE_REVIEW_IF_STATIC",
            "Allowed only by Shadow Review Gate V1 as a static side-by-side packet.",
        ),
        _safe_row(
            "Settings/Data Health cockpit",
            "SAFE_REVIEW_UI",
            "Status surface only; no production decisions.",
        ),
    ]


def blocked_today_rows() -> list[dict[str, str]]:
    return [
        _blocked_row("Production formula promotion"),
        _blocked_row("Production model training/tuning"),
        _blocked_row("Ratings, recommendations, or hidden-sort changes"),
        _blocked_row("Shadow app/live-preview wiring"),
        _blocked_row("True routes, TPRR, YPRR, or route proxies without safe upload"),
        _blocked_row("Current-only historical features"),
        _blocked_row("Ambiguous red-zone fields including rz_att"),
        _blocked_row("Market/vendor/projection/rank fields as source truth"),
    ]


def artifact_health_source_map_rows() -> list[dict[str, str]]:
    return artifact_health_board_rows()


def _artifact_row(label: str, root: Path, rows: str, note: str) -> dict[str, str]:
    exists = root.exists()
    return {
        "Artifact": label,
        "Path": _relative(root),
        "Status": _manifest_verdict(root / "artifact_manifest.md") if exists else "NOT_PRESENT",
        "Rows / counts": rows if exists else NOT_ENOUGH_INFORMATION,
        "Phase status": "MERGED_OR_TRACKED" if exists else "NOT_PRESENT",
        "Safe use": REVIEW_ONLY if exists else "blocked",
        "Production flag": PROD_BLOCKED,
        "Notes": note,
    }


def _availability_row(name: str, root: Path, rows: str, status: str) -> dict[str, str]:
    return {
        "Dataset": name,
        "Available": "yes" if root.exists() else "no",
        "Rows / counts": rows if root.exists() else NOT_ENOUGH_INFORMATION,
        "Status": status if root.exists() else "NOT_PRESENT",
        "Use": REVIEW_ONLY if root.exists() else "blocked",
        "Path": _relative(root),
    }


def _guardrail_row(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"Guardrail": name, "Status": status, "Evidence": evidence}


def _safe_row(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"Can use today": name, "Status": status, "Boundary": evidence}


def _blocked_row(name: str) -> dict[str, str]:
    return {
        "Still blocked": name,
        "Status": "BLOCKED",
        "Reason": "Requires a separate HQ gate before any production or decision use.",
    }


def _core_usage_row_count() -> str:
    rows = _csv_rows(CORE_USAGE_DIR / "nwr_nflverse_usage_row_count_report_v1.csv")
    return str(_sum_int(rows, "row_count"))


def _redzone_row_count() -> str:
    value = _markdown_number(
        CORE_USAGE_DIR / "core_usage_review_dataset_summary.md",
        r"Red-zone sidecar rows:\s*([0-9]+)",
    )
    return str(value) if value is not None else NOT_ENOUGH_INFORMATION


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
        return "TRACKED_ARTIFACT"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"Verdict:\s*`([^`]+)`", text)
    if match:
        return match.group(1)
    match = re.search(r"Decision:\s*`([^`]+)`", text)
    if match:
        return match.group(1)
    return "TRACKED_ARTIFACT"


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()
