from __future__ import annotations

import csv
import os
import py_compile
from collections import defaultdict
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
THIS_WORKTREE = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_RULE_TEST_COMMIT = "f8a60a80ffcda8b14386e659757d79ab1ae31390"
PRIOR_DESIGN_COMMIT = "f493dbf751e42b1f258df14e41a20fde9274d136"

RULE_TEST_DIR = THIS_WORKTREE / "docs/hq/model/sparse_history_breakout_candidate_rule_test_v1_20260709"
DESIGN_DIR = THIS_WORKTREE / "docs/hq/model/sparse_history_breakout_red_team_rookie_young_player_model_design_v1_20260709"
ADDENDUM_DIR = THIS_WORKTREE / "docs/hq/master/formula_red_team_canonicalization_addendum_v1_20260709"
RED_TEAM_DIR = THIS_WORKTREE / "docs/hq/model/formula_miss_taxonomy_red_team_review_v1_20260709"
INGREDIENT_CANON_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\master\ingredient_upgrade_phase_batch_canonicalization_merge_review_v1_20260709")
SNAP_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709")
ROOKIE_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\rookie_draft_capital_data_mart_join_component_test_v1_20260709")
INJURY_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\point_in_time_injury_availability_data_mart_gate_v1_20260709")
FFOP_NGS_DIR = Path(r"C:\NWR\Niners-War-Room-merge-review-ingredient-upgrade-phase-canonicalization-v1-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709")

SCORECARD = RULE_TEST_DIR / "SPARSE_HISTORY_RULE_MISS_REDUCTION_SCORECARD.csv"
REGISTRY = RULE_TEST_DIR / "SPARSE_HISTORY_RULE_REGISTRY.csv"
OVERLAY = RULE_TEST_DIR / "SPARSE_HISTORY_RULE_OVERLAY_RESULTS.csv"

REFERENCE_FORMULAS = [
    "PYF baseline",
    "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100",
    "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100",
    "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10",
]

WINDOWS = [
    {"window": "full_history", "seasons": "2013-2025", "status": "full-history comparable", "notes": "Primary broad historical reference; no partial-window-only ingredients."},
    {"window": "broad_window", "seasons": "2014-2025", "status": "broad-window comparable", "notes": "Snap/depth broad-window comparison; keep separate from full history."},
    {"window": "partial_window", "seasons": "2022-2025", "status": "partial-window only", "notes": "ffopportunity/NGS modern window only; cannot break full-history plateau."},
]

PASS_FAIL = {
    "primary_net_miss_reduction": ">= 12 on at least one full-history or broad-window comparable reference",
    "resolved_vs_created": "misses_resolved must meaningfully exceed new_misses_created",
    "false_negative": "false-negative reduction must improve without unacceptable false-positive creation",
    "severe_false_positive": "no severe false-positive spike",
    "spearman_floor": "Spearman must not decline meaningfully; target +0.002 or better",
    "top_n": "Top-12/Top-24/Top-36 impact neutral or positive where relevant",
    "position_stability": "positive or neutral by position, unless explicitly position-specific",
    "collateral": "non-sparse-history collateral damage must stay low",
    "partial_window": "partial-window rules stay partial-window only",
}


def writable_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with open(writable_path(path), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    with open(writable_path(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text.strip() + "\n")


def to_int(value: Any) -> int:
    try:
        return int(float(str(value).strip()))
    except Exception:
        return 0


def to_float(value: Any) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return 0.0


def best_by_rule() -> list[dict[str, Any]]:
    score_rows = read_csv(SCORECARD)
    registry_rows = {row["rule_id"]: row for row in read_csv(REGISTRY)}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in score_rows:
        grouped[row["rule_id"]].append(row)
    out = []
    for rule_id, rows in sorted(grouped.items()):
        best = max(rows, key=lambda row: to_int(row["net_miss_reduction"]))
        reg = registry_rows.get(rule_id, {})
        fp_impact = to_int(best["false_positives_before"]) - to_int(best["false_positives_after"])
        fn_impact = to_int(best["false_negatives_before"]) - to_int(best["false_negatives_after"])
        collateral = to_int(best["non_sparse_collateral_damage"])
        next_use = rule_next_use(rule_id, best.get("rule_classification", ""))
        out.append({
            "rule_id": rule_id,
            "rule_family": reg.get("rule_family", best.get("rule_family", "")),
            "rule_class": best.get("rule_classification", ""),
            "best_formula": best.get("formula_id", ""),
            "best_window": best.get("scoreboard_window", ""),
            "net_miss_reduction": best.get("net_miss_reduction", "0"),
            "misses_resolved": best.get("misses_resolved", "0"),
            "new_misses_created": best.get("new_misses_created", "0"),
            "false_positive_impact": fp_impact,
            "false_negative_impact": fn_impact,
            "spearman_delta": best.get("spearman_delta", ""),
            "non_sparse_collateral_damage": collateral,
            "next_use_decision": next_use,
        })
    return out


def rule_next_use(rule_id: str, rule_class: str) -> str:
    if rule_id in {"RULE_002_DEPTH_STARTER_BREAKOUT_05", "RULE_005_EARLY_CAREER_LIFECYCLE_025", "RULE_006_DRAFT_CAPITAL_WITH_ROLE_05", "RULE_011_SPARSE_HISTORY_COMPOSITE_BALANCED"}:
        return "REFINE_ELIGIBLE"
    if rule_id in {"RULE_001_ROLE_PROMOTION_BREAKOUT_05", "RULE_003_SNAP_GROWTH_BREAKOUT_05", "RULE_008_POSITION_SPECIFIC_BREAKOUT_05"}:
        return "LIMITED_DIAGNOSTIC_ELIGIBLE"
    if rule_id == "RULE_004_AVAILABILITY_REBOUND_05":
        return "CONTEXT_ONLY_NOT_SCORING"
    if rule_id == "RULE_010_FALSE_POSITIVE_TRAP_STRICT_10":
        return "CONTEXT_HARM_REVIEW_ONLY_NO_SCORING_DOWNGRADE"
    if rule_id == "RULE_009_FALSE_POSITIVE_TRAP_DOWNGRADE_05":
        return "EXCLUDE_HARMFUL"
    if rule_id in {"RULE_007_EXPECTED_OPPORTUNITY_PARTIAL_05", "RULE_012_COMPOSITE_PARTIAL_EXPECTED_OPP"}:
        return "PARTIAL_WINDOW_CONTEXT_ONLY_NOT_FULL_HISTORY_REFINEMENT"
    return f"REVIEW_{rule_class}"


def eligibility_rows(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in summary:
        next_use = row["next_use_decision"]
        if next_use == "REFINE_ELIGIBLE":
            decision = "SELECTED_FOR_REFINEMENT"
            rationale = "Promising V1 miss-reduction profile and fits allowed full/broad-window review-only inputs."
            max_use = "REVIEW_ONLY_REFINEMENT_VARIANT"
        elif next_use == "LIMITED_DIAGNOSTIC_ELIGIBLE":
            decision = "OPTIONAL_LIMITED_DIAGNOSTIC"
            rationale = "Mixed V1 result; may test stricter smaller variants without expanding scope."
            max_use = "REVIEW_ONLY_DIAGNOSTIC_VARIANT"
        elif next_use == "CONTEXT_ONLY_NOT_SCORING":
            decision = "EXCLUDED_FROM_SCORING_REFINEMENT"
            rationale = "Availability rebound is useful context but did not justify scoring-rule refinement."
            max_use = "CONTEXT_ONLY"
        elif next_use == "CONTEXT_HARM_REVIEW_ONLY_NO_SCORING_DOWNGRADE":
            decision = "EXCLUDED_FROM_SCORING_REFINEMENT"
            rationale = "Trap strict rule had no FP reduction and should remain harm-review context only."
            max_use = "CONTEXT_HARM_REVIEW_ONLY"
        elif next_use == "EXCLUDE_HARMFUL":
            decision = "EXCLUDED_HARMFUL"
            rationale = "Trap downgrade produced harmful displacement."
            max_use = "DO_NOT_REFINE"
        elif next_use == "PARTIAL_WINDOW_CONTEXT_ONLY_NOT_FULL_HISTORY_REFINEMENT":
            decision = "EXCLUDED_FROM_FULL_HISTORY_REFINEMENT"
            rationale = "Depends on partial-window expected-opportunity inputs; cannot be a full-history rule."
            max_use = "PARTIAL_WINDOW_CONTEXT_ONLY"
        else:
            decision = "EXCLUDED"
            rationale = "No clear bounded refinement case."
            max_use = "EVIDENCE_ONLY"
        rows.append({
            "rule_id": row["rule_id"],
            "rule_class": row["rule_class"],
            "eligibility_decision": decision,
            "max_allowed_v2_use": max_use,
            "rationale": rationale,
            "v1_best_net_miss_reduction": row["net_miss_reduction"],
            "v1_spearman_delta": row["spearman_delta"],
        })
    return rows


def refined_variants() -> list[dict[str, Any]]:
    common_refs = ";".join(REFERENCE_FORMULAS)
    rows = [
        ("REFINE_002_A_DEPTH_STARTER_025", "RULE_002", "DEPTH_STARTER_BREAKOUT_RULE", "starter confirmation small boost", "+0.025", "sparse eligible", "starter/depth signal true", "no injury caveat and not low snap", "full_history;broad_window;partial_window", "stricter strength test"),
        ("REFINE_002_B_PRIMARY_STARTER_050", "RULE_002", "DEPTH_STARTER_BREAKOUT_RULE", "primary-starter confirmation boost", "+0.050", "sparse eligible", "PRIMARY_STARTER or starter weeks >= 8", "low snap flag false", "full_history;broad_window;partial_window", "confirm V1 depth-starter signal"),
        ("REFINE_002_C_LOW_PYF_STARTER_050", "RULE_002", "DEPTH_STARTER_BREAKOUT_RULE", "low-PYF starter-only boost", "+0.050", "sparse eligible and pyf missing/low", "starter/depth signal true", "exclude non-sparse rows", "full_history;broad_window;partial_window", "recover low-PYF role miss"),
        ("REFINE_002_D_RB_WR_TE_STARTER_025", "RULE_002", "DEPTH_STARTER_BREAKOUT_RULE", "RB/WR/TE starter diagnostic", "+0.025", "sparse eligible and position RB/WR/TE", "starter/depth signal true", "position QB excluded", "full_history;broad_window;partial_window", "position-specific starter check"),
        ("REFINE_005_A_EARLY_ROLE_015", "RULE_005", "EARLY_CAREER_LIFECYCLE_RULE", "early-career role small boost", "+0.015", "sparse eligible and year 1-3 or early lifecycle", "role or starter signal", "no broad veteran boost", "full_history;broad_window;partial_window", "test smaller V1 strength"),
        ("REFINE_005_B_EARLY_ROLE_025", "RULE_005", "EARLY_CAREER_LIFECYCLE_RULE", "early-career role V1 strength", "+0.025", "sparse eligible and year 1-3 or early lifecycle", "role or starter signal", "no broad veteran boost", "full_history;broad_window;partial_window", "retain V1 winner shape"),
        ("REFINE_005_C_YEAR2_YEAR3_ONLY_025", "RULE_005", "EARLY_CAREER_LIFECYCLE_RULE", "year-two/year-three breakout window", "+0.025", "sparse eligible and years_since_draft in 1,2", "role or starter signal", "true rookies excluded", "full_history;broad_window;partial_window", "target classic breakout years"),
        ("REFINE_005_D_EARLY_CLEAN_AVAIL_025", "RULE_005", "EARLY_CAREER_LIFECYCLE_RULE", "early-career clean-availability confirmation", "+0.025", "sparse eligible and early lifecycle", "role/starter plus clean availability", "injury caveat false", "full_history;broad_window;partial_window", "avoid injury trap displacement"),
        ("REFINE_005_E_EARLY_LOW_PYF_025", "RULE_005", "EARLY_CAREER_LIFECYCLE_RULE", "early-career low-PYF only", "+0.025", "sparse eligible and low/no PYF", "early lifecycle plus role/starter", "exclude adequate prior production", "full_history;broad_window;partial_window", "focus on under-informed PYF rows"),
        ("REFINE_006_A_DRAFT_ROLE_025", "RULE_006", "DRAFT_CAPITAL_WITH_ROLE_RULE", "draft capital with role small boost", "+0.025", "sparse eligible", "round 1-2 plus starter/role signal", "draft capital alone blocked", "full_history;broad_window;partial_window", "test lower strength"),
        ("REFINE_006_B_DRAFT_ROLE_050", "RULE_006", "DRAFT_CAPITAL_WITH_ROLE_RULE", "draft capital with role V1 strength", "+0.050", "sparse eligible", "round 1-2 plus starter/role signal", "draft capital alone blocked", "full_history;broad_window;partial_window", "retain V1 shape"),
        ("REFINE_006_C_ROUND1_ROLE_050", "RULE_006", "DRAFT_CAPITAL_WITH_ROLE_RULE", "round-one role confirmation", "+0.050", "sparse eligible", "round 1 plus starter/role signal", "round 2 excluded", "full_history;broad_window;partial_window", "strict draft evidence check"),
        ("REFINE_006_D_DAY2_STARTER_025", "RULE_006", "DRAFT_CAPITAL_WITH_ROLE_RULE", "day-two starter diagnostic", "+0.025", "sparse eligible", "round 2-3 plus starter signal", "no UDFA inference", "full_history;broad_window;partial_window", "separate day-two effect"),
        ("REFINE_006_E_DRAFT_LOW_PYF_ROLE_050", "RULE_006", "DRAFT_CAPITAL_WITH_ROLE_RULE", "draft role low-PYF recovery", "+0.050", "sparse eligible and low/no PYF", "round 1-2 plus role/starter", "draft alone blocked", "full_history;broad_window;partial_window", "recover PYF-understated prospects"),
        ("REFINE_011_A_COMPOSITE_SMALL_025", "RULE_011", "SPARSE_HISTORY_COMPOSITE_RULE", "two-signal composite small boost", "+0.025", "sparse eligible", "two breakout signals", "trap-only downgrade disabled", "full_history;broad_window;partial_window", "reduce V1 new misses"),
        ("REFINE_011_B_COMPOSITE_BALANCED_050", "RULE_011", "SPARSE_HISTORY_COMPOSITE_RULE", "two-signal composite V1 boost", "+0.050", "sparse eligible", "two breakout signals", "trap-only downgrade disabled", "full_history;broad_window;partial_window", "retain V1 composite upside"),
        ("REFINE_011_C_COMPOSITE_STRICT_050", "RULE_011", "SPARSE_HISTORY_COMPOSITE_RULE", "three-signal strict composite", "+0.050", "sparse eligible", "three breakout signals", "no injury caveat", "full_history;broad_window;partial_window", "test stricter quality gate"),
        ("REFINE_011_D_COMPOSITE_LOW_PYF_050", "RULE_011", "SPARSE_HISTORY_COMPOSITE_RULE", "low-PYF composite", "+0.050", "sparse eligible and low/no PYF", "two breakout signals", "exclude adequate PYF rows", "full_history;broad_window;partial_window", "focus on under-informed rows"),
        ("REFINE_011_E_COMPOSITE_POSITION_025", "RULE_011", "SPARSE_HISTORY_COMPOSITE_RULE", "position-specific composite", "+0.025", "sparse eligible", "position-specific breakout profile plus one support signal", "trap-only downgrade disabled", "full_history;broad_window;partial_window", "position stability check"),
        ("DIAG_001_A_ROLE_PROMO_025", "RULE_001", "ROLE_PROMOTION_BREAKOUT_RULE", "role promotion small diagnostic", "+0.025", "sparse eligible", "snap/depth role promotion", "not low snap", "full_history;broad_window;partial_window", "limited diagnostic only"),
        ("DIAG_001_B_ROLE_PROMO_STARTER_025", "RULE_001", "ROLE_PROMOTION_BREAKOUT_RULE", "role promotion plus starter", "+0.025", "sparse eligible", "role promotion and starter/depth signal", "injury caveat false", "full_history;broad_window;partial_window", "limited diagnostic only"),
        ("DIAG_003_A_SNAP_GROWTH_025", "RULE_003", "SNAP_GROWTH_BREAKOUT_RULE", "snap growth small diagnostic", "+0.025", "sparse eligible", "lagged snap growth signal", "not low snap", "full_history;broad_window;partial_window", "limited diagnostic only"),
        ("DIAG_003_B_SNAP_GROWTH_STARTER_025", "RULE_003", "SNAP_GROWTH_BREAKOUT_RULE", "snap growth plus starter", "+0.025", "sparse eligible", "snap growth and starter signal", "injury caveat false", "full_history;broad_window;partial_window", "limited diagnostic only"),
        ("DIAG_008_A_POSITION_PROFILE_025", "RULE_008", "POSITION_SPECIFIC_BREAKOUT_RULE", "position profile small diagnostic", "+0.025", "sparse eligible", "position-specific profile passes", "no broad veteran boost", "full_history;broad_window;partial_window", "limited diagnostic only"),
        ("DIAG_008_B_WR_TE_POSITION_PROFILE_025", "RULE_008", "POSITION_SPECIFIC_BREAKOUT_RULE", "WR/TE position profile diagnostic", "+0.025", "sparse eligible and WR/TE", "starter/depth or expected opportunity context", "partial ingredients flagged when used", "full_history;broad_window;partial_window", "limited diagnostic only"),
    ]
    fields = [
        "variant_id", "parent_rule_id", "rule_family", "variant_name", "overlay_strength", "eligibility_gate", "positive_conditions",
        "negative_conditions", "allowed_windows", "reference_formulas", "expected_goal", "blocked_input_check", "source_use_gate_status",
        "leakage_asof_check", "review_only_status", "v2_status",
    ]
    out = []
    for row in rows:
        out.append(dict(zip(fields, [
            row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], common_refs, row[9],
            "PASS_NO_CURRENT_ADP_NO_MARKET_NO_CFBD_NO_SPORTSDATAIO_NO_PFF_NO_ELUSIVE_PROXY",
            "REVIEW_ONLY_NOT_PRODUCTION_MODEL_USE",
            "PASS_LAGGED_N_TO_N_PLUS_1_OR_STATIC_POST_ENTRY_CONTEXT",
            "REVIEW_ONLY_CONTRACT_PREDECLARED_NOT_EXECUTED",
            "PREDECLARED_FOR_V2",
        ])))
    return out


def input_policy() -> list[dict[str, Any]]:
    return [
        {"input_name": "sparse-history flags", "allowed_use": "eligibility gate", "source": "Formula Data Mart / design ledger", "v2_status": "ALLOWED_REVIEW_ONLY", "blocked_use": "production ranking logic"},
        {"input_name": "age/lifecycle bucket", "allowed_use": "early-career window context", "source": "Age lifecycle sidecar", "v2_status": "ALLOWED_REVIEW_ONLY_CONTEXT", "blocked_use": "automatic production boost/penalty"},
        {"input_name": "years since draft", "allowed_use": "rookie/year-two/year-three windows", "source": "Rookie draft sidecar", "v2_status": "ALLOWED_REVIEW_ONLY", "blocked_use": "future pre-draft use"},
        {"input_name": "draft capital bucket", "allowed_use": "positive evidence only with role", "source": "Rookie draft sidecar", "v2_status": "ALLOWED_REVIEW_ONLY_POSITIVE_EVIDENCE", "blocked_use": "UDFA inference or draft capital alone"},
        {"input_name": "snap/depth role score", "allowed_use": "role promotion and starter confirmation", "source": "Snap/depth sidecar", "v2_status": "ALLOWED_REVIEW_ONLY", "blocked_use": "target-season depth chart"},
        {"input_name": "snap growth signal", "allowed_use": "limited diagnostic", "source": "Snap/depth sidecar", "v2_status": "ALLOWED_IF_LAGGED", "blocked_use": "same-season growth"},
        {"input_name": "injury/availability caveat", "allowed_use": "negative confirmation/context", "source": "Injury availability sidecar", "v2_status": "GUARDRAIL_CONTEXT_ONLY", "blocked_use": "injury prediction"},
        {"input_name": "clean availability context", "allowed_use": "confirmation, not prediction", "source": "Injury availability sidecar", "v2_status": "ALLOWED_CONTEXT", "blocked_use": "future health projection"},
        {"input_name": "ffopportunity / NGS", "allowed_use": "partial-window diagnostic only", "source": "Autonomous V2 sidecars", "v2_status": "PARTIAL_WINDOW_ONLY", "blocked_use": "full-history plateau claim"},
        {"input_name": "current-only ADP / market", "allowed_use": "none", "source": "Market/ADP gate", "v2_status": "BLOCKED", "blocked_use": "historical formula input"},
        {"input_name": "CFBD/prospect production", "allowed_use": "none", "source": "Rookie/draft gate", "v2_status": "BLOCKED", "blocked_use": "model input without source and identity gates"},
    ]


def write_docs(variant_count: int) -> None:
    report = f"""
# Sparse-History Rule Refinement Contract V1

## Verdict

`GREEN_SPARSE_HISTORY_REFINEMENT_CONTRACT_READY`

## Scope

This is a contract/design lane only. It did not run the second rule test, change production rankings, change app/runtime/model behavior, promote sources, push/merge, write to canonical `local_exports`, run ranking simulation, or approve model-use.

Remote HQ verified: `{EXPECTED_REMOTE_HEAD}`.

Prior rule-test commit verified: `{PRIOR_RULE_TEST_COMMIT}`.

## Contract Decision

Selected for refinement: `RULE_002`, `RULE_005`, `RULE_006`, `RULE_011`.

Optional limited diagnostics: `RULE_001`, `RULE_003`, `RULE_008`.

Excluded from scoring refinement: `RULE_004`, `RULE_007`, `RULE_009`, `RULE_010`, `RULE_012`.

Refined variants predeclared: `{variant_count}`.

Primary success metric: net miss reduction.

Secondary metric: Spearman. The execution lane must not optimize only for Spearman.

## Execution Recommendation

`Sparse-History Rule Refinement Execution V1` is justified because the variant grid is bounded, deterministic, review-only, and restricted to V1 families with miss-reduction evidence.

Review-only ranking simulation remains not justified.
"""
    write_md(OUT_DIR / "SPARSE_HISTORY_RULE_REFINEMENT_CONTRACT_V1_REPORT.md", report)

    criteria = "\n".join(f"- `{k}`: {v}" for k, v in PASS_FAIL.items())
    write_md(OUT_DIR / "SPARSE_HISTORY_REFINEMENT_PASS_FAIL_CRITERIA.md", f"""
# Sparse-History Refinement Pass/Fail Criteria

{criteria}

A refined rule cannot advance if it creates harmful displacement, relies on blocked inputs, blurs partial-window results into full-history claims, or implies production/ranking use.
""")

    refs = "\n".join(f"- `{formula}`" for formula in REFERENCE_FORMULAS)
    windows = "\n".join(f"- `{row['window']}`: `{row['seasons']}` ({row['status']})" for row in WINDOWS)
    write_md(OUT_DIR / "SPARSE_HISTORY_REFINEMENT_TEST_WINDOW_POLICY.md", f"""
# Sparse-History Refinement Test Window Policy

## Windows

{windows}

## Reference Formulas

{refs}

Keep full-history, broad-window, and partial-window scoreboards separate. Partial-window rules may be tested only as partial-window diagnostics and cannot support full-history plateau claims.
""")

    write_md(OUT_DIR / "SPARSE_HISTORY_REFINEMENT_EXECUTION_RECOMMENDATION.md", """
# Sparse-History Refinement Execution Recommendation

Recommended next lane: `Sparse-History Rule Refinement Execution V1`.

The execution lane should run only the predeclared variants in `SPARSE_HISTORY_REFINED_RULE_REGISTRY.csv`, use the test windows and references in this contract, and apply the pass/fail gates exactly. It must not add variants after seeing results.

Ranking simulation remains blocked.
""")

    write_md(OUT_DIR / "SPARSE_HISTORY_REFINEMENT_BLOCKERS_AND_CAVEATS.md", """
# Sparse-History Refinement Blockers and Caveats

- No production/model-use approval.
- No rankings integration.
- No app/runtime behavior change.
- No push/merge.
- No canonical `local_exports` mutation.
- Trap-only scoring downgrades are excluded because V1 showed harmful displacement and no positive FP reduction.
- ffopportunity/NGS remain partial-window only.
- Current-only ADP, unproven market data, SportsDataIO, paid/API/free-trial sources, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, CFBD/prospect model input, and inferred UDFA truth remain blocked.
""")

    write_md(OUT_DIR / "SPARSE_HISTORY_REFINEMENT_SOURCE_TRACE.md", f"""
# Sparse-History Refinement Source Trace

Prior rule-test packet: `{RULE_TEST_DIR}`

Prior design packet: `{DESIGN_DIR}`

Formula red-team canonicalization addendum: `{ADDENDUM_DIR}`

Formula miss taxonomy red-team review: `{RED_TEAM_DIR}`

Ingredient upgrade canonicalization: `{INGREDIENT_CANON_DIR}`

Snap/depth sidecar packet: `{SNAP_DIR}`

Rookie/draft sidecar packet: `{ROOKIE_DIR}`

Injury availability packet: `{INJURY_DIR}`

Autonomous ffopportunity / NGS packet: `{FFOP_NGS_DIR}`

Source/use gate: all variants remain review-only contract candidates. Production/model-use, rankings integration, source promotion, hidden sort, recommendation logic, and ranking simulation remain blocked.

Leakage/as-of gate: contract permits only lagged N-to-N+1, static post-entry identity context, or explicitly partial-window ffopportunity/NGS diagnostics. Same-season/future context remains blocked.
""")


def main() -> None:
    for path in [RULE_TEST_DIR, DESIGN_DIR, ADDENDUM_DIR, RED_TEAM_DIR, INGREDIENT_CANON_DIR, SNAP_DIR, ROOKIE_DIR, INJURY_DIR, FFOP_NGS_DIR, SCORECARD, REGISTRY, OVERLAY]:
        if not path.exists():
            raise RuntimeError(f"Required artifact missing: {path}")
    compile_check = OUT_DIR / "_compile_check.pyc"
    try:
        py_compile.compile(__file__, cfile=str(compile_check), doraise=True)
    finally:
        if compile_check.exists():
            compile_check.unlink()
    summary = best_by_rule()
    summary_fields = [
        "rule_id", "rule_family", "rule_class", "best_formula", "best_window", "net_miss_reduction", "misses_resolved",
        "new_misses_created", "false_positive_impact", "false_negative_impact", "spearman_delta", "non_sparse_collateral_damage", "next_use_decision",
    ]
    write_csv(OUT_DIR / "SPARSE_HISTORY_RULE_TEST_V1_SUMMARY.csv", summary, summary_fields)
    eligibility = eligibility_rows(summary)
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINEMENT_ELIGIBILITY_DECISION.csv", eligibility, ["rule_id", "rule_class", "eligibility_decision", "max_allowed_v2_use", "rationale", "v1_best_net_miss_reduction", "v1_spearman_delta"])
    variants = refined_variants()
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_REGISTRY.csv", variants, ["variant_id", "parent_rule_id", "rule_family", "variant_name", "overlay_strength", "eligibility_gate", "positive_conditions", "negative_conditions", "allowed_windows", "reference_formulas", "expected_goal", "blocked_input_check", "source_use_gate_status", "leakage_asof_check", "review_only_status", "v2_status"])
    write_csv(OUT_DIR / "SPARSE_HISTORY_REFINED_RULE_INPUT_POLICY.csv", input_policy(), ["input_name", "allowed_use", "source", "v2_status", "blocked_use"])
    write_docs(len(variants))


if __name__ == "__main__":
    main()
