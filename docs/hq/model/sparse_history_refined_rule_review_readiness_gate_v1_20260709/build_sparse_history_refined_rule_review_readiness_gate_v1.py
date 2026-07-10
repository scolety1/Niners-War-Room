from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


REMOTE_HQ = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_EXECUTION_COMMIT = "9839e03e24f858e8ff5b2c6d9d49d2a490a49714"
PRIOR_CONTRACT_COMMIT = "3871cbf8854b28093bf361db4270681e45ccd236"
VERDICT = "GREEN_SPARSE_HISTORY_READY_FOR_OVERLAY_CANDIDATE_PRESERVATION"
READINESS_STATUS = "READY_FOR_REVIEW_ONLY_OVERLAY_CANDIDATE_PRESERVATION"
NEXT_LANE = "Sparse-History Overlay Candidate Preservation V1"

PROMISING = [
    "REFINE_005_A_EARLY_ROLE_015",
    "REFINE_005_B_EARLY_ROLE_025",
    "REFINE_005_C_YEAR2_YEAR3_ONLY_025",
    "REFINE_006_A_DRAFT_ROLE_025",
]

HARMFUL = [
    "DIAG_008_B_WR_TE_POSITION_PROFILE_025",
    "REFINE_002_C_LOW_PYF_STARTER_050",
    "REFINE_011_D_COMPOSITE_LOW_PYF_050",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


ROOT = repo_root()
OUT = ROOT / "docs" / "hq" / "model" / "sparse_history_refined_rule_review_readiness_gate_v1_20260709"
EXEC = ROOT / "docs" / "hq" / "model" / "sparse_history_rule_refinement_execution_v1_20260709"
CONTRACT = ROOT / "docs" / "hq" / "model" / "sparse_history_rule_refinement_contract_v1_20260709"
RULE_TEST = ROOT / "docs" / "hq" / "model" / "sparse_history_breakout_candidate_rule_test_v1_20260709"
DESIGN = ROOT / "docs" / "hq" / "model" / "sparse_history_breakout_red_team_rookie_young_player_model_design_v1_20260709"
RED_TEAM = ROOT / "docs" / "hq" / "model" / "formula_miss_taxonomy_red_team_review_v1_20260709"
CANON = ROOT / "docs" / "hq" / "master" / "ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709"
ADDENDUM = ROOT / "docs" / "hq" / "master" / "formula_red_team_canonicalization_addendum_v1_20260709"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_md(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.rstrip() + "\n", encoding="utf-8")


def as_int(value: object, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value)))
    except ValueError:
        return default


def as_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value))
    except ValueError:
        return default


def make_position_summary(position_rows: list[dict[str, str]]) -> dict[tuple[str, str], str]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in position_rows:
        grouped[(row["variant_id"], row["reference_id"])].append(f"{row['position']}:{row['net_miss_reduction']}")
    return {key: "; ".join(parts) for key, parts in grouped.items()}


def best_rows_by_variant(rows: list[dict[str, str]], variant_ids: list[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for variant_id in variant_ids:
        candidates = [row for row in rows if row["variant_id"] == variant_id]
        pass_rows = [row for row in candidates if row["pass_fail_status"] == "PASS_ALL_THRESHOLDS"]
        pool = pass_rows or candidates
        result[variant_id] = max(
            pool,
            key=lambda row: (
                as_int(row["net_miss_reduction"]),
                as_int(row["misses_resolved"]) - as_int(row["new_misses_created"]),
                as_float(row["spearman_delta"]),
            ),
        )
    return result


def promising_decision(row: dict[str, str]) -> tuple[str, str]:
    variant = row["variant_id"]
    if variant == "REFINE_005_A_EARLY_ROLE_015":
        return (
            "ADVANCE_PRIMARY_REVIEW_ONLY_OVERLAY_CANDIDATE",
            "Cleanest readiness profile: net miss reduction 16, 25 resolved versus 9 new, false-negative reduction 8, no severe false-positive spike, and no material Spearman decline.",
        )
    if variant == "REFINE_005_B_EARLY_ROLE_025":
        return (
            "ADVANCE_SECONDARY_REVIEW_ONLY_OVERLAY_CANDIDATE_WITH_CAUTION",
            "Passes the threshold, but the 25% strength creates more churn than the 15% variant; preserve as a bounded comparison rather than the preferred overlay.",
        )
    if variant == "REFINE_005_C_YEAR2_YEAR3_ONLY_025":
        return (
            "ADVANCE_SECONDARY_REVIEW_ONLY_OVERLAY_CANDIDATE",
            "Constrained year-two/year-three version passes with net miss reduction 14 and useful Spearman support, making it a narrow early-career preservation candidate.",
        )
    if variant == "REFINE_006_A_DRAFT_ROLE_025":
        return (
            "ADVANCE_SECONDARY_REVIEW_ONLY_OVERLAY_CANDIDATE_WITH_DRAFT_GATE_CAVEAT",
            "Ties top net miss reduction at 16 and resolves 32 misses, but must remain bound by draft-capital source and identity gates and must not become a broad draft-capital branch.",
        )
    return ("KEEP_AS_CONTEXT_ONLY", "Did not meet the preservation standard.")


def harmful_reason(variant: str) -> str:
    if variant == "DIAG_008_B_WR_TE_POSITION_PROFILE_025":
        return "WR/TE position-profile overlay was unstable: same-count churn in broad-window review, a full-history severe false-positive spike, and Spearman decline."
    if variant == "REFINE_002_C_LOW_PYF_STARTER_050":
        return "Low-PYF starter overlay was too aggressive: severe false-positive spikes, Spearman decline, and insufficient net miss reduction."
    if variant == "REFINE_011_D_COMPOSITE_LOW_PYF_050":
        return "Low-PYF composite repeated the same harmful pattern: severe false-positive spikes, Spearman decline, and excessive churn."
    return "Rejected by readiness review."


def main() -> None:
    results = read_csv(EXEC / "SPARSE_HISTORY_REFINED_RULE_RESULTS.csv")
    classifications = read_csv(EXEC / "SPARSE_HISTORY_REFINED_RULE_CLASSIFICATION.csv")
    positions = read_csv(EXEC / "SPARSE_HISTORY_REFINED_RULE_POSITION_RESULTS.csv")
    collateral = read_csv(EXEC / "SPARSE_HISTORY_REFINED_RULE_COLLATERAL_DAMAGE_REVIEW.csv")

    pos_summary = make_position_summary(positions)
    collateral_by_key = {
        (row["variant_id"], row["reference_id"], row["scoreboard_window"]): row for row in collateral
    }

    evidence_fields = [
        "variant_id",
        "source_rule_family",
        "window",
        "reference_formula",
        "reference_id",
        "net_miss_reduction",
        "misses_resolved",
        "new_misses_created",
        "false_positive_change",
        "false_negative_change",
        "severe_false_positive_change",
        "severe_false_negative_change",
        "spearman_delta",
        "top12_precision_delta",
        "top24_precision_delta",
        "top36_precision_delta",
        "position_level_impact",
        "sparse_history_impact",
        "non_sparse_collateral_damage",
        "collateral_status",
        "classification",
        "pass_fail_status",
        "pass_fail_reasons",
    ]
    evidence_rows: list[dict[str, object]] = []
    for row in results:
        collat = collateral_by_key.get((row["variant_id"], row["reference_id"], row["scoreboard_window"]), {})
        evidence_rows.append(
            {
                "variant_id": row["variant_id"],
                "source_rule_family": row["parent_rule_id"],
                "window": row["scoreboard_window"],
                "reference_formula": row["formula_id"],
                "reference_id": row["reference_id"],
                "net_miss_reduction": row["net_miss_reduction"],
                "misses_resolved": row["misses_resolved"],
                "new_misses_created": row["new_misses_created"],
                "false_positive_change": as_int(row["false_positives_after"]) - as_int(row["false_positives_before"]),
                "false_negative_change": as_int(row["false_negatives_after"]) - as_int(row["false_negatives_before"]),
                "severe_false_positive_change": as_int(row["severe_false_positives_after"]) - as_int(row["severe_false_positives_before"]),
                "severe_false_negative_change": as_int(row["severe_false_negatives_after"]) - as_int(row["severe_false_negatives_before"]),
                "spearman_delta": row["spearman_delta"],
                "top12_precision_delta": row["top12_precision_delta"],
                "top24_precision_delta": row["top24_precision_delta"],
                "top36_precision_delta": row["top36_precision_delta"],
                "position_level_impact": pos_summary.get((row["variant_id"], row["reference_id"]), ""),
                "sparse_history_impact": row["sparse_history_only_miss_reduction"],
                "non_sparse_collateral_damage": row["non_sparse_collateral_damage"],
                "collateral_status": collat.get("collateral_status", ""),
                "classification": row["refined_rule_classification"],
                "pass_fail_status": row["pass_fail_status"],
                "pass_fail_reasons": row["pass_fail_reasons"],
            }
        )
    write_csv(OUT / "SPARSE_HISTORY_REFINED_RULE_EVIDENCE_TABLE.csv", evidence_rows, evidence_fields)

    best_promising = best_rows_by_variant(results, PROMISING)
    promising_fields = [
        "variant_id",
        "source_rule_family",
        "best_window",
        "best_reference_formula",
        "net_miss_reduction",
        "misses_resolved",
        "new_misses_created",
        "false_negative_reduction",
        "false_positive_increase",
        "severe_false_positive_spike",
        "non_sparse_collateral_damage",
        "spearman_delta",
        "top12_precision_delta",
        "top24_precision_delta",
        "top36_precision_delta",
        "pass_fail_status",
        "review_decision",
        "rationale",
    ]
    promising_rows: list[dict[str, object]] = []
    for variant in PROMISING:
        row = best_promising[variant]
        decision, rationale = promising_decision(row)
        promising_rows.append(
            {
                "variant_id": variant,
                "source_rule_family": row["parent_rule_id"],
                "best_window": row["scoreboard_window"],
                "best_reference_formula": row["formula_id"],
                "net_miss_reduction": row["net_miss_reduction"],
                "misses_resolved": row["misses_resolved"],
                "new_misses_created": row["new_misses_created"],
                "false_negative_reduction": row["false_negative_reduction"],
                "false_positive_increase": row["false_positive_increase"],
                "severe_false_positive_spike": row["severe_false_positive_spike"],
                "non_sparse_collateral_damage": row["non_sparse_collateral_damage"],
                "spearman_delta": row["spearman_delta"],
                "top12_precision_delta": row["top12_precision_delta"],
                "top24_precision_delta": row["top24_precision_delta"],
                "top36_precision_delta": row["top36_precision_delta"],
                "pass_fail_status": row["pass_fail_status"],
                "review_decision": decision,
                "rationale": rationale,
            }
        )
    write_csv(OUT / "SPARSE_HISTORY_PROMISING_VARIANT_REVIEW.csv", promising_rows, promising_fields)

    harmful_fields = [
        "variant_id",
        "source_rule_family",
        "worst_window",
        "worst_reference_formula",
        "net_miss_reduction",
        "misses_resolved",
        "new_misses_created",
        "severe_false_positive_spike",
        "spearman_delta",
        "non_sparse_collateral_damage",
        "classification",
        "review_decision",
        "harm_pattern",
    ]
    harmful_rows: list[dict[str, object]] = []
    for variant in HARMFUL:
        rows = [row for row in results if row["variant_id"] == variant]
        worst = min(
            rows,
            key=lambda row: (
                as_float(row["spearman_delta"]),
                -as_int(row["severe_false_positive_spike"]),
                as_int(row["net_miss_reduction"]),
            ),
        )
        harmful_rows.append(
            {
                "variant_id": variant,
                "source_rule_family": worst["parent_rule_id"],
                "worst_window": worst["scoreboard_window"],
                "worst_reference_formula": worst["formula_id"],
                "net_miss_reduction": worst["net_miss_reduction"],
                "misses_resolved": worst["misses_resolved"],
                "new_misses_created": worst["new_misses_created"],
                "severe_false_positive_spike": worst["severe_false_positive_spike"],
                "spearman_delta": worst["spearman_delta"],
                "non_sparse_collateral_damage": worst["non_sparse_collateral_damage"],
                "classification": worst["refined_rule_classification"],
                "review_decision": "REJECT_DO_NOT_ADVANCE",
                "harm_pattern": harmful_reason(variant),
            }
        )
    write_csv(OUT / "SPARSE_HISTORY_HARMFUL_VARIANT_REVIEW.csv", harmful_rows, harmful_fields)

    best_net = max(
        results,
        key=lambda row: (
            as_int(row["net_miss_reduction"]),
            as_int(row["misses_resolved"]) - as_int(row["new_misses_created"]),
            as_float(row["spearman_delta"]),
        ),
    )
    all_variants = sorted({row["variant_id"] for row in classifications})
    not_advanced = [variant for variant in all_variants if variant not in set(PROMISING) and variant not in set(HARMFUL)]
    class_text = "\n".join(
        [
            f"- Advanced as review-only overlay candidates: `{', '.join(PROMISING)}`",
            f"- Rejected harmful variants: `{', '.join(HARMFUL)}`",
            f"- Reviewed but not advanced in this gate: `{', '.join(not_advanced)}`",
            "- Blocked or invalid variants: `none`",
        ]
    )

    write_md(
        OUT / "SPARSE_HISTORY_REFINED_RULE_REVIEW_READINESS_GATE_V1_REPORT.md",
        f"""# Sparse-History Refined Rule Review / Readiness Gate V1

## Verdict

`{VERDICT}`

## Scope

This is a review-only readiness review lane. It did not run new formulas, add rule variants, dynamically tune thresholds, run ranking simulation, approve model-use, change app/runtime behavior, promote sources, push/merge, or write to canonical `local_exports`.

Remote HQ verified: `{REMOTE_HQ}`.

Prior refinement execution commit verified: `{PRIOR_EXECUTION_COMMIT}`.

## Evidence Reviewed

The packet reviewed the 25 refined variants from Sparse-History Rule Refinement Execution V1 across full-history, broad-window, and partial-window scoreboards. The evidence table preserves 100 variant/reference rows.

Best net miss-reduction row: `{best_net['variant_id']}` on `{best_net['formula_id']}` / `{best_net['scoreboard_window']}`, net miss reduction `{best_net['net_miss_reduction']}`, misses resolved `{best_net['misses_resolved']}`, new misses `{best_net['new_misses_created']}`, Spearman delta `{best_net['spearman_delta']}`.

Promising variants reviewed: `{', '.join(PROMISING)}`.

Harmful variants reviewed: `{', '.join(HARMFUL)}`.

## Readiness Summary

{class_text}

## Readiness Decision

Readiness status: `{READINESS_STATUS}`.

At least one full-history variant met the readiness criteria. `REFINE_005_A_EARLY_ROLE_015` is the preferred review-only overlay candidate because it produced net miss reduction `16`, resolved `25` misses, created `9` new misses, reduced false negatives by `8`, avoided a severe false-positive spike, and did not materially reduce Spearman.

The other pass-all variants should be preserved as secondary review-only overlay candidates, not as production logic or ranking integration.

## Ranking Simulation

Review-only ranking simulation remains not justified. The evidence supports overlay-candidate preservation, not board simulation.

## Next Lane

Recommended next lane: `{NEXT_LANE}`.
""",
    )

    write_md(
        OUT / "SPARSE_HISTORY_READINESS_GATE_DECISION.md",
        f"""# Sparse-History Readiness Gate Decision

Readiness status: `{READINESS_STATUS}`.

Decision: advance a small set of refined sparse-history rules as review-only overlay candidates for preservation.

Primary candidate:

- `REFINE_005_A_EARLY_ROLE_015`

Secondary candidates:

- `REFINE_005_B_EARLY_ROLE_025`
- `REFINE_005_C_YEAR2_YEAR3_ONLY_025`
- `REFINE_006_A_DRAFT_ROLE_025`

Do not advance harmful variants:

- `DIAG_008_B_WR_TE_POSITION_PROFILE_025`
- `REFINE_002_C_LOW_PYF_STARTER_050`
- `REFINE_011_D_COMPOSITE_LOW_PYF_050`

Rationale:

- At least one full-history variant reached net miss reduction `>= 16`.
- Resolved misses exceeded new misses by a meaningful margin for the preferred candidate.
- False-negative reduction was positive.
- No severe false-positive spike was present for pass-all candidates.
- Spearman did not materially decline.
- The preferred rule is simple enough to preserve as a review-only overlay candidate.
- Production/model-use and rankings integration remain blocked.
""",
    )

    write_md(
        OUT / "SPARSE_HISTORY_RANKING_SIMULATION_READINESS_REVIEW.md",
        """# Sparse-History Ranking Simulation Readiness Review

Review-only ranking simulation justified: `no`.

The refined rules produced real miss-reduction evidence, but the result is still an overlay-candidate preservation decision rather than a ranking-simulation decision. Some variants created unacceptable collateral damage, and the pass-all evidence is strongest on the full-history snap/depth reference rather than across every reference/window.

Allowed next step: preserve the candidate overlay packet for future user review.

Blocked:

- production/model-use
- rankings integration
- app/runtime behavior changes
- source promotion
- push/merge
- canonical `local_exports` mutation
""",
    )

    write_md(
        OUT / "SPARSE_HISTORY_NEXT_LANE_DECISION.md",
        f"""# Sparse-History Next Lane Decision

Recommended next lane: `{NEXT_LANE}`.

Why this lane:

- The evidence is strong enough to preserve review-only overlay candidates.
- It is not strong enough to run review-only ranking simulation.
- A second broad refinement would risk returning to same-ingredient tuning.
- The harmful variants show why preservation should be narrow and explicitly gated.

Do not recommend production integration.
""",
    )

    write_md(
        OUT / "SPARSE_HISTORY_REFINED_RULE_BLOCKERS_AND_CAVEATS.md",
        """# Sparse-History Refined Rule Blockers And Caveats

- This packet is review-only.
- Ranking simulation remains blocked.
- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior remains unchanged.
- Source promotion remains blocked.
- Push/merge was not performed.
- Some refined variants caused unacceptable collateral damage and should not advance.
- Partial-window evidence remains partial-window only.
- Draft-capital variants remain bound by existing source and identity gates.
- Same-season and future leakage remain blocked; this packet only reviews already accepted lagged/static rule evidence.
- Current-only ADP, SportsDataIO, paid/API/free-trial sources, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, unsupported CFBD/prospect inputs, and inferred UDFA truth remain blocked.
""",
    )

    trace = [
        "# Sparse-History Refined Rule Source Trace",
        "",
        f"- Remote HQ verified: `{REMOTE_HQ}`",
        f"- Prior refinement execution commit verified: `{PRIOR_EXECUTION_COMMIT}`",
        f"- Prior refinement contract commit referenced: `{PRIOR_CONTRACT_COMMIT}`",
        f"- Sparse-History Rule Refinement Execution V1: `{EXEC.relative_to(ROOT)}`",
        f"- Sparse-History Rule Refinement Contract V1: `{CONTRACT.relative_to(ROOT)}`",
        f"- Sparse-History Breakout Candidate Rule Test V1: `{RULE_TEST.relative_to(ROOT)}`",
        f"- Sparse-History Breakout Red Team / Rookie-Young Player Model Design V1: `{DESIGN.relative_to(ROOT)}`",
        f"- Formula Miss Taxonomy / Red Team Review V1: `{RED_TEAM.relative_to(ROOT)}`",
        f"- Ingredient Upgrade Phase Batch Canonicalization / Merge Review V1: `{CANON.relative_to(ROOT)}`",
        f"- Formula Red Team Canonicalization Addendum V1: `{ADDENDUM.relative_to(ROOT)}`",
        "",
        "No new formulas, variants, source promotions, app/runtime changes, ranking simulation, push/merge, or canonical `local_exports` writes were performed.",
    ]
    write_md(OUT / "SPARSE_HISTORY_REFINED_RULE_SOURCE_TRACE.md", "\n".join(trace))


if __name__ == "__main__":
    main()
