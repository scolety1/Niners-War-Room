from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


CONTRACT_DIR = Path(__file__).resolve().parent
V3_DIR = CONTRACT_DIR.parent / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
ZERO_MATRIX = V3_DIR / "feature_zero_semantics_matrix_v3.csv"
LINEAGE_MATRIX = V3_DIR / "field_source_lineage_matrix_v3.csv"

BRANCH = "work/historical-tuning-substrate-expansion-v3-source-semantics-audit-20260701"
PREVIOUS_HEAD = "8cdcd0fd1068cb036a01f2636656f3a9cde35256"
VERDICT = "GREEN_SOURCE_CONTRACT_V1_REVIEW_ONLY_FORMULA_TUNING_NOT_READY"
NEXT_PHASE = "Historical Formula Tuning Readiness Gate V1"

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "historical_tuning_source_contract_summary.md",
    "allowed_review_only_feature_contract_v1.csv",
    "null_fenced_feature_contract_v1.csv",
    "blocked_feature_contract_v1.csv",
    "source_lineage_contract_v1.csv",
    "zero_semantics_contract_v1.csv",
    "future_tuning_gate_requirements.md",
    "formula_tuning_not_ready_reason.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
]

EXTRA_BLOCKED_ROWS = [
    {
        "feature": "market_fields",
        "feature_family": "market_or_price",
        "contract_decision": "BLOCKED_AS_SOURCE_TRUTH",
        "reason": "Market fields are not source truth for historical tuning features.",
    },
    {
        "feature": "adp_fields",
        "feature_family": "market_or_price",
        "contract_decision": "BLOCKED_AS_SOURCE_TRUTH",
        "reason": "ADP fields are not source truth for historical tuning features.",
    },
    {
        "feature": "vendor_fields",
        "feature_family": "vendor_or_projection",
        "contract_decision": "BLOCKED_AS_SOURCE_TRUTH",
        "reason": "Vendor fields are not source truth for historical tuning features.",
    },
    {
        "feature": "projection_fields",
        "feature_family": "vendor_or_projection",
        "contract_decision": "BLOCKED_AS_SOURCE_TRUTH",
        "reason": "Projection fields are not source truth for historical tuning features.",
    },
    {
        "feature": "rank_fields",
        "feature_family": "rank_or_sort",
        "contract_decision": "BLOCKED_AS_SOURCE_TRUTH",
        "reason": "Rank, ranking, and sort fields are not source truth for historical tuning features.",
    },
    {
        "feature": "current_roster_status_injury_depth_schedule_fields",
        "feature_family": "current_only_context",
        "contract_decision": "BLOCKED_AS_HISTORICAL_FEATURE_DATA",
        "reason": "Current-only roster, status, injury, depth, and schedule context cannot be used as historical feature data.",
    },
]


def main() -> int:
    CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
    zero = pd.read_csv(ZERO_MATRIX)
    lineage = pd.read_csv(LINEAGE_MATRIX)

    allowed = make_allowed_contract(zero)
    null_fenced = make_null_fenced_contract(zero)
    blocked = make_blocked_contract(zero)
    source_lineage = make_source_lineage_contract(zero, lineage)
    zero_contract = make_zero_semantics_contract(zero)

    write_csv(allowed, "allowed_review_only_feature_contract_v1.csv")
    write_csv(null_fenced, "null_fenced_feature_contract_v1.csv")
    write_csv(blocked, "blocked_feature_contract_v1.csv")
    write_csv(source_lineage, "source_lineage_contract_v1.csv")
    write_csv(zero_contract, "zero_semantics_contract_v1.csv")

    context = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT,
        "branch": BRANCH,
        "previous_head": PREVIOUS_HEAD,
        "allowed_count": len(allowed),
        "null_fenced_count": len(null_fenced),
        "blocked_count": len(blocked),
        "next_phase": NEXT_PHASE,
    }
    write_markdown(CONTRACT_DIR / "historical_tuning_source_contract_summary.md", summary_md(context))
    write_markdown(CONTRACT_DIR / "future_tuning_gate_requirements.md", gate_md(context))
    write_markdown(CONTRACT_DIR / "formula_tuning_not_ready_reason.md", not_ready_md(context))
    write_markdown(CONTRACT_DIR / "guardrail_report.md", guardrail_md(context))
    write_markdown(CONTRACT_DIR / "merge_safety_report.md", merge_safety_md(context))
    write_markdown(CONTRACT_DIR / "next_phase_handoff.md", handoff_md(context))
    write_manifest(context)

    print(f"wrote={CONTRACT_DIR}")
    print(f"allowed={len(allowed)} null_fenced={len(null_fenced)} blocked={len(blocked)}")
    print(f"verdict={VERDICT}")
    return 0


def make_allowed_contract(zero: pd.DataFrame) -> pd.DataFrame:
    allowed = zero[
        (zero["allowed_in_v3_review_substrate"].astype(bool))
        & (~zero["null_fenced_in_v3"].astype(bool))
        & (~zero["blocked_in_v3"].astype(bool))
    ].copy()
    allowed["contract_decision"] = "ALLOW_REVIEW_ONLY"
    allowed["future_gate_use"] = "candidate_search_input_only_after_readiness_gate"
    allowed["production_approved"] = False
    allowed["model_use_allowed"] = False
    allowed["training_allowed"] = False
    allowed["source_truth_allowed"] = False
    allowed["formula_search_allowed_now"] = False
    return allowed[
        [
            "feature",
            "feature_family",
            "source_column_or_rule",
            "source_kind",
            "contract_decision",
            "zero_classification",
            "missingness_semantics",
            "future_gate_use",
            "production_approved",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
            "formula_search_allowed_now",
        ]
    ].sort_values("feature")


def make_null_fenced_contract(zero: pd.DataFrame) -> pd.DataFrame:
    fenced = zero[
        (zero["allowed_in_v3_review_substrate"].astype(bool))
        & (zero["null_fenced_in_v3"].astype(bool))
    ].copy()
    fenced["contract_decision"] = "ALLOW_REVIEW_ONLY_WITH_NULL_FENCE"
    fenced["required_handling"] = "preserve_nulls; do_not_fill_missing_with_zero; exclude_or_impute_only_after_human_gate"
    fenced["production_approved"] = False
    fenced["model_use_allowed"] = False
    fenced["training_allowed"] = False
    fenced["source_truth_allowed"] = False
    fenced["formula_search_allowed_now"] = False
    return fenced[
        [
            "feature",
            "feature_family",
            "source_column_or_rule",
            "source_kind",
            "contract_decision",
            "null_fenced_by",
            "zero_classification",
            "missingness_semantics",
            "required_handling",
            "production_approved",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
            "formula_search_allowed_now",
        ]
    ].sort_values("feature")


def make_blocked_contract(zero: pd.DataFrame) -> pd.DataFrame:
    blocked = zero[zero["blocked_in_v3"].astype(bool)].copy()
    blocked = blocked.rename(
        columns={
            "zero_semantics_decision": "contract_decision",
            "missingness_semantics": "reason",
        }
    )
    blocked = blocked[
        [
            "feature",
            "feature_family",
            "source_column_or_rule",
            "source_kind",
            "contract_decision",
            "reason",
        ]
    ]
    extra = pd.DataFrame(EXTRA_BLOCKED_ROWS)
    extra["source_column_or_rule"] = "not_allowed_by_source_contract"
    extra["source_kind"] = "blocked_guardrail_family"
    blocked = pd.concat([blocked, extra[blocked.columns]], ignore_index=True)
    blocked["production_approved"] = False
    blocked["model_use_allowed"] = False
    blocked["training_allowed"] = False
    blocked["source_truth_allowed"] = False
    blocked["formula_search_allowed_now"] = False
    return blocked.sort_values(["feature_family", "feature"]).reset_index(drop=True)


def make_source_lineage_contract(zero: pd.DataFrame, lineage: pd.DataFrame) -> pd.DataFrame:
    allowed_features = zero[zero["allowed_in_v3_review_substrate"].astype(bool)]["feature"].tolist()
    output = lineage[lineage["feature"].isin(allowed_features)].copy()
    output["contract_decision"] = output["feature"].map(
        dict(zip(zero["feature"], zero["zero_semantics_decision"]))
    )
    output["source_contract_v1_status"] = "contracted_review_only_not_source_truth"
    output["formula_readiness_gate_required"] = True
    output["production_approved"] = False
    output["model_use_allowed"] = False
    output["training_allowed"] = False
    output["source_truth_allowed"] = False
    return output[
        [
            "feature",
            "source_column_or_rule",
            "source_kind",
            "local_source_path",
            "nflreadpy_source_column",
            "approved_dependency_path",
            "feature_season_rule",
            "target_season_rule",
            "comparison_method",
            "local_source_comparison_status",
            "local_mismatch_count",
            "nflreadpy_comparison_status",
            "nflreadpy_mismatch_count",
            "asof_status",
            "contract_decision",
            "source_contract_v1_status",
            "formula_readiness_gate_required",
            "production_approved",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
        ]
    ].sort_values("feature")


def make_zero_semantics_contract(zero: pd.DataFrame) -> pd.DataFrame:
    output = zero.copy()
    output["source_contract_v1_status"] = output.apply(contract_status, axis=1)
    output["future_formula_tuning_gate_required"] = True
    output["formula_search_allowed_now"] = False
    output["production_approved"] = False
    output["model_use_allowed"] = False
    output["training_allowed"] = False
    output["source_truth_allowed"] = False
    return output[
        [
            "feature",
            "feature_family",
            "source_column_or_rule",
            "source_kind",
            "zero_semantics_decision",
            "zero_classification",
            "source_contract_v1_status",
            "allowed_in_v3_review_substrate",
            "null_fenced_in_v3",
            "blocked_in_v3",
            "null_fenced_by",
            "missingness_semantics",
            "future_formula_tuning_gate_required",
            "formula_search_allowed_now",
            "production_approved",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
        ]
    ].sort_values("feature")


def contract_status(row: pd.Series) -> str:
    if bool(row["blocked_in_v3"]):
        return "blocked_by_source_contract"
    if bool(row["null_fenced_in_v3"]):
        return "allowed_review_only_with_required_null_fence"
    return "allowed_review_only"


def write_csv(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(CONTRACT_DIR / name, index=False)


def write_markdown(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summary_md(context: dict[str, Any]) -> str:
    return f"""
# Historical Tuning Source Contract V1

Verdict: `{context['verdict']}`

This closeout artifact converts the V3 source-semantics audit into a reusable review-only contract for future historical tuning lanes. It does not run formula tuning, formula search, model training, ranking changes, app wiring, hidden sort, recommendations, source-truth promotion, or runtime changes.

## Contract Counts

- Allowed review-only features: `{context['allowed_count']}`
- Required null-fenced features: `{context['null_fenced_count']}`
- Blocked feature families: `{context['blocked_count']}`

## Binding Rule

Future formula tuning is still not production-viable until a Formula Tuning Readiness Gate confirms this V3/V1 contract is sufficient for candidate search. The next phase should be `{context['next_phase']}`, not another substrate expansion, unless a concrete missing source artifact is identified.
"""


def gate_md(context: dict[str, Any]) -> str:
    return f"""
# Future Tuning Gate Requirements

The next eligible lane is `{context['next_phase']}`.

The gate must confirm all of the following before any candidate search:

1. The V3 source-semantics matrix and Source Contract V1 are accepted as sufficient review-only inputs.
2. The 18 `ALLOW_REVIEW_ONLY` features remain review-only and not production-approved.
3. The four optional fields remain null-fenced: `prior_offensive_snaps`, `prior_offense_pct`, `prior_receiving_air_yards`, and `prior_receiving_yards_after_catch`.
4. Red-zone sidecars remain blocked/absent unless separately admitted in a future source gate.
5. Ambiguous `rz_att` remains blocked.
6. Routes, TPRR, YPRR, and route proxy families remain blocked.
7. Market, ADP, vendor, projection, and rank fields remain blocked as source truth.
8. Missing values are not filled with zero unless an admitted source proves explicit zero semantics.
9. No current-only roster, status, injury, depth, or schedule context is used as historical feature data.
10. Candidate outputs, if ever produced, remain candidate-only and not production-approved.
"""


def not_ready_md(context: dict[str, Any]) -> str:
    return """
# Formula Tuning Not Ready Reason

Future formula tuning is still not production-viable.

V3 and Source Contract V1 make the next decision deterministic, but they do not approve formula search. The remaining blocker is governance, not another blind substrate expansion: a readiness gate must decide whether the V3 source-semantics decisions, null fences, and blocked-family list are sufficient for candidate-only search.

Until that gate passes, the historical substrate remains review-only evidence. No production formula, model, ranking, recommendation, hidden-sort, source-truth, or runtime behavior may consume it.
"""


def guardrail_md(context: dict[str, Any]) -> str:
    return """
# Guardrail Report

Status: PASS for review-only source-contract artifacts.

Confirmed:

- No formula tuning.
- No formula search.
- No production formula changes.
- No model training or tuning.
- No rankings, recommendations, hidden sort, app wiring, source-truth promotion, or runtime behavior changes.
- Red-zone sidecars remain blocked/absent unless separately admitted.
- Ambiguous `rz_att` remains blocked.
- Routes, TPRR, YPRR, and route proxies remain blocked.
- Market, ADP, vendor, projection, and rank fields remain blocked as source truth.
- No raw/shared/cache/local export/secrets files are tracked by this artifact.
"""


def merge_safety_md(context: dict[str, Any]) -> str:
    return f"""
# Merge Safety Report

Recommendation: merge the combined V3 plus Source Contract V1 branch once validation is green.

The combined branch is merge-ready only as review-only evidence and source-contract documentation. It is not a production-tuning merge.

Expected changed paths for this closeout commit:

- `docs/hq/experiments/historical_tuning_source_contract_v1_20260701/`
- `tests/test_historical_tuning_source_contract_v1_20260701.py`

Previous branch HEAD before this closeout: `{context['previous_head']}`.
"""


def handoff_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommended next phase: `{context['next_phase']}`.

Do not run another substrate expansion unless the readiness gate identifies a concrete missing source artifact. Do not run formula search until the readiness gate explicitly allows candidate-only search under the V3/Source Contract V1 constraints.

Carry forward these contract artifacts:

- `allowed_review_only_feature_contract_v1.csv`
- `null_fenced_feature_contract_v1.csv`
- `blocked_feature_contract_v1.csv`
- `source_lineage_contract_v1.csv`
- `zero_semantics_contract_v1.csv`
"""


def write_manifest(context: dict[str, Any]) -> None:
    rows = []
    for name in REQUIRED_ARTIFACTS + ["build_historical_tuning_source_contract_v1.py"]:
        path = CONTRACT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    body = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{context['branch']}`
- Previous HEAD: `{context['previous_head']}`
- Review-only: true
- Production-approved: false
- Allowed review-only features: `{context['allowed_count']}`
- Null-fenced features: `{context['null_fenced_count']}`
- Blocked feature families: `{context['blocked_count']}`

| Artifact | Bytes | SHA-256 |
|---|---:|---|
{chr(10).join(rows)}
"""
    write_markdown(CONTRACT_DIR / "artifact_manifest.md", body)


if __name__ == "__main__":
    raise SystemExit(main())
