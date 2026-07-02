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

NOT_ENOUGH_INFORMATION = "Not enough information"
REVIEW_ONLY = "review-only/manual display"


def lab_status_board_rows() -> list[dict[str, str]]:
    return [
        {
            "Area": "Active experiment",
            "Status": "HOLD",
            "Evidence": "usage_opportunity_volume",
            "Review-only note": "Candidate evidence is visible for human review only.",
        },
        {
            "Area": "Closed phase",
            "Status": "MERGED_REVIEW_PACKET",
            "Evidence": "NFLVerse phase, Core Usage Dataset V1, Historical V3, Source Contract V1",
            "Review-only note": "Merged packets remain fenced from normal app behavior.",
        },
        {
            "Area": "Held candidates",
            "Status": "HOLD",
            "Evidence": "qb_guard_soft_blend; rb_wr_cutline_safe_blend",
            "Review-only note": "Variants are evidence labels only; no production approval.",
        },
        {
            "Area": "Available datasets",
            "Status": "TRACKED_ARTIFACTS_READY",
            "Evidence": "Core usage, red-zone sidecar, Historical V3 substrate, display context",
            "Review-only note": "Tracked docs/artifacts only; raw shared/cache files stay out.",
        },
        {
            "Area": "Guardrail status",
            "Status": "GREEN_REVIEW_ONLY",
            "Evidence": "No model input, source truth, hidden sort, or app default behavior",
            "Review-only note": "Development Lab is a cockpit, not a decision engine.",
        },
    ]


def dataset_browser_rows() -> list[dict[str, str]]:
    core_row_counts = _csv_rows(CORE_USAGE_DIR / "nwr_nflverse_usage_row_count_report_v1.csv")
    core_schema = _csv_rows(
        CORE_USAGE_DIR / "nwr_nflverse_usage_review_dataset_schema_v1.csv"
    )
    v3_counts = _csv_rows(V3_SUBSTRATE_DIR / "feature_target_row_count_report_v3.csv")
    v3_features = _csv_rows(V3_SUBSTRATE_DIR / "safe_feature_allowlist_v3.csv")
    allowed_features = _csv_rows(
        SOURCE_CONTRACT_DIR / "allowed_review_only_feature_contract_v1.csv"
    )
    null_fenced = _csv_rows(
        SOURCE_CONTRACT_DIR / "null_fenced_feature_contract_v1.csv"
    )
    blocked_features = _csv_rows(
        SOURCE_CONTRACT_DIR / "blocked_feature_contract_v1.csv"
    )
    redzone_rows = _markdown_number(
        CORE_USAGE_DIR / "core_usage_review_dataset_summary.md",
        r"Red-zone sidecar rows:\s*([0-9]+)",
    )

    return [
        {
            "Dataset": "NFLVerse Core Usage Review Dataset V1",
            "Status": _manifest_verdict(CORE_USAGE_DIR / "artifact_manifest.md"),
            "Rows": str(_sum_int(core_row_counts, "row_count")),
            "Feature seasons": _unique_join(core_row_counts, "season"),
            "Target seasons": "current player-week review artifact",
            "Fields": str(len(core_schema)),
            "Safe use": REVIEW_ONLY,
            "Source path": _relative(CORE_USAGE_DIR),
        },
        {
            "Dataset": "Red-zone sidecar",
            "Status": _manifest_verdict(REDZONE_DIR / "artifact_manifest.md"),
            "Rows": str(redzone_rows) if redzone_rows is not None else NOT_ENOUGH_INFORMATION,
            "Feature seasons": "2024;2025",
            "Target seasons": "regular-season weeks 1-18",
            "Fields": "sidecar schema/sample tracked",
            "Safe use": "sidecar only; semantics caveats retained",
            "Source path": _relative(REDZONE_DIR),
        },
        {
            "Dataset": "Historical Tuning V3 substrate",
            "Status": _manifest_verdict(V3_SUBSTRATE_DIR / "artifact_manifest.md"),
            "Rows": str(_sum_int(v3_counts, "row_count")),
            "Feature seasons": _unique_join(v3_counts, "feature_season"),
            "Target seasons": _unique_join(v3_counts, "target_season"),
            "Fields": str(len(v3_features)),
            "Safe use": REVIEW_ONLY,
            "Source path": _relative(V3_SUBSTRATE_DIR),
        },
        {
            "Dataset": "Source Contract V1",
            "Status": _manifest_verdict(SOURCE_CONTRACT_DIR / "artifact_manifest.md"),
            "Rows": (
                f"{len(allowed_features)} allowed / {len(null_fenced)} null-fenced / "
                f"{len(blocked_features)} blocked"
            ),
            "Feature seasons": "contract derived from Historical V3",
            "Target seasons": "future review gates only",
            "Fields": str(len(allowed_features) + len(null_fenced) + len(blocked_features)),
            "Safe use": "contract display only; formula tuning not ready",
            "Source path": _relative(SOURCE_CONTRACT_DIR),
        },
    ]


def candidate_review_panel_rows() -> list[dict[str, str]]:
    remaining = _csv_rows(CUTLINE_REFINEMENT_DIR / "remaining_cutline_casebook.csv")
    return [
        {
            "Review item": "Current candidate",
            "Value": "usage_opportunity_volume",
            "Status": "HOLD",
            "Guardrail": "No production approval; no normal app wiring.",
        },
        {
            "Review item": "Useful rescue variant",
            "Value": "qb_guard_soft_blend",
            "Status": "REVIEW_EVIDENCE_ONLY",
            "Guardrail": "Elite-QB regression rescue evidence only.",
        },
        {
            "Review item": "Partial refinement variant",
            "Value": "rb_wr_cutline_safe_blend",
            "Status": "PARTIAL_REFINEMENT_STILL_HOLD",
            "Guardrail": "Cutline-safe refinement evidence only.",
        },
        {
            "Review item": "Targeted redesign variant",
            "Value": "wr_boundary_breakout_sensitivity_guard",
            "Status": "TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY",
            "Guardrail": "Human-review evidence only; no shadow-review approval.",
        },
        {
            "Review item": "Known risks",
            "Value": (
                "cutline misses; CeeDee Lamb; Tony Pollard; George Pickens; "
                "Jordan Addison; Dameon Pierce"
            ),
            "Status": f"{len(remaining)} remaining cutline rows",
            "Guardrail": "Risk list is descriptive evidence, not an action rule.",
        },
        {
            "Review item": "Production approval",
            "Value": "Not approved",
            "Status": "BLOCKED_FROM_PRODUCTION",
            "Guardrail": (
                "Candidate output is not wired into rankings, draft, trade, or compare pages."
            ),
        },
    ]


def guardrail_ledger_rows() -> list[dict[str, str]]:
    return [
        {
            "Guardrail": "Blocked fields",
            "Status": "ACTIVE",
            "Evidence": (
                "Routes, TPRR, YPRR, ambiguous rz_att, current-only context, "
                "and source gaps remain blocked."
            ),
        },
        {
            "Guardrail": "Null-fenced fields",
            "Status": "ACTIVE",
            "Evidence": "Source Contract V1 requires missing context to stay explicit.",
        },
        {
            "Guardrail": "Source-truth restrictions",
            "Status": "ACTIVE",
            "Evidence": "No review packet is promoted to source truth by Development Lab.",
        },
        {
            "Guardrail": "Current-only context restrictions",
            "Status": "ACTIVE",
            "Evidence": (
                "Current roster/status context stays display-only and out of "
                "historical formula behavior."
            ),
        },
        {
            "Guardrail": "Route/TPRR/YPRR blocked",
            "Status": "ACTIVE",
            "Evidence": "No route proxies are created from participation data.",
        },
        {
            "Guardrail": "Runtime behavior",
            "Status": "ACTIVE",
            "Evidence": (
                "No production formula, config, model, rank, hidden sort, or "
                "default app behavior changes."
            ),
        },
    ]


def current_stats_review_improvement_rows() -> list[dict[str, str]]:
    return [
        _improvement_row("Player usage trend summaries", "Core Usage Dataset V1"),
        _improvement_row("Opportunity and touch context", "Core Usage Dataset V1"),
        _improvement_row("Snap share context where fenced", "Core Usage Dataset V1"),
        _improvement_row("First-down scoring context", "Core Usage Dataset V1"),
        _improvement_row("Candidate formula review summaries", "Historical candidate packets"),
        _improvement_row("Red-zone context as sidecar only", "Red-zone sidecar V1"),
    ]


def next_lane_idea_rows() -> list[dict[str, str]]:
    return [
        {
            "Idea": "Static cutline casebook",
            "Why it helps review": "Put the remaining five cutline rows in one read-only casebook.",
            "Status": "IDEA_ONLY",
            "Guardrail": "No auto action and no production promotion.",
        },
        {
            "Idea": "Human decision gate",
            "Why it helps review": (
                "Review the targeted redesign packet and the two remaining concern rows."
            ),
            "Status": "IDEA_ONLY",
            "Guardrail": "Human review only; no shadow-review prep starts here.",
        },
        {
            "Idea": "Usage trend preview lane",
            "Why it helps review": (
                "Summarize lagged targets, carries, touches, opportunities, "
                "first downs, and snaps."
            ),
            "Status": "IDEA_ONLY",
            "Guardrail": "Descriptive context only; no decision output.",
        },
        {
            "Idea": "Red-zone sidecar audit lane",
            "Why it helps review": (
                "Review typed red-zone opportunities while preserving "
                "sparse/missing semantics."
            ),
            "Status": "IDEA_ONLY",
            "Guardrail": "Sidecar only; ambiguous rz_att remains blocked.",
        },
    ]


def artifact_manifest_rows() -> list[dict[str, str]]:
    return [
        _artifact_row("Core Usage Review Dataset V1", CORE_USAGE_DIR),
        _artifact_row("Red-zone sidecar V1", REDZONE_DIR),
        _artifact_row("Historical Tuning V3 substrate", V3_SUBSTRATE_DIR),
        _artifact_row("Source Contract V1", SOURCE_CONTRACT_DIR),
        _artifact_row("Candidate Search V1", CANDIDATE_SEARCH_DIR),
        _artifact_row("Candidate Review V1", CANDIDATE_REVIEW_DIR),
        _artifact_row("Promotion Gate Prep V1", PROMOTION_GATE_DIR),
        _artifact_row("Risk Rescue Sprint V1", RISK_RESCUE_DIR),
        _artifact_row("Cutline Safe Refinement V1", CUTLINE_REFINEMENT_DIR),
        _artifact_row("Targeted Redesign V1", TARGETED_REDESIGN_DIR),
    ]


def _improvement_row(area: str, source: str) -> dict[str, str]:
    return {
        "Review-only improvement": area,
        "Supported by": source,
        "Allowed output": "Descriptive summary only",
        "Blocked output": (
            "No automatic decision, hidden sort, model input, or source-truth change."
        ),
    }


def _artifact_row(label: str, root: Path) -> dict[str, str]:
    return {
        "Artifact": label,
        "Status": _manifest_verdict(root / "artifact_manifest.md"),
        "Path": _relative(root),
        "Tracked": "yes" if root.exists() else "missing",
    }


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


def _unique_join(rows: list[dict[str, str]], column: str) -> str:
    values = sorted({str(row.get(column, "")).strip() for row in rows if row.get(column)})
    return ";".join(values) if values else NOT_ENOUGH_INFORMATION


def _markdown_number(path: Path, pattern: str) -> int | None:
    if not path.exists():
        return None
    match = re.search(pattern, path.read_text(encoding="utf-8"))
    if match is None:
        return None
    return int(match.group(1))


def _manifest_verdict(path: Path) -> str:
    if not path.exists():
        return NOT_ENOUGH_INFORMATION
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
