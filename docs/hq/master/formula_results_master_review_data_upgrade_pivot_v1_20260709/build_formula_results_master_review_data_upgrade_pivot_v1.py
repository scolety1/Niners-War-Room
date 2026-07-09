from __future__ import annotations

import csv
import py_compile
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_REFINEMENT_COMMIT = "5c9efdacc7356579e2751bdfd4269e5010ad7f87"

REFINEMENT_DIR = Path(
    r"C:\NWR\Niners-War-Room-diverse-champion-refinement-predeclared-execution-v1-20260709"
    r"\docs\hq\model\diverse_champion_refinement_predeclared_execution_v1_20260709"
)
GAUNTLET_DIR = Path(
    r"C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709"
    r"\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709"
)
CLUSTER_DIR = Path(
    r"C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709"
    r"\docs\hq\model\gauntlet_candidate_diversity_clustering_audit_v1_20260709"
)
MEDIUM_DIR = Path(
    r"C:\NWR\Niners-War-Room-medium-review-only-formula-pilot-v1-20260709"
    r"\docs\hq\model\medium_review_only_formula_pilot_v1_20260709"
)
SMALL_DIR = Path(
    r"C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709"
    r"\docs\hq\model\small_review_only_formula_pilot_v1_20260709"
)
DATA_MART_DIR = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
)
UPGRADE_SWEEP_DIR = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-remaining-upgrade-sweep-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_remaining_upgrade_sweep_v1_20260709"
)
AGE_MASTER_DIR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-master-review-v1-20260709"
    r"\docs\hq\master\age_lifecycle_master_review_v1_20260709"
)
ROLE_MASTER_DIR = Path("docs/hq/master/model_v4_role_archetype_master_review_v1_20260709")
PFR_ADDENDUM_DIR = Path(
    r"C:\NWR\Niners-War-Room-full-system-audit-pfr-rb-broken-tackle-addendum-v1-20260709"
    r"\docs\hq\master\nwr_full_system_audit_pfr_rb_broken_tackle_addendum_v1_20260709"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def fnum(row: dict[str, str], *keys: str) -> float:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            try:
                return float(str(value).replace("%", ""))
            except ValueError:
                continue
    return -999.0


def find_row(rows: list[dict[str, str]], candidate_id: str) -> dict[str, str] | None:
    return next((row for row in rows if row.get("candidate_id") == candidate_id), None)


def best_row(rows: list[dict[str, str]], *score_keys: str) -> dict[str, str]:
    return max(rows, key=lambda row: fnum(row, *score_keys))


def safe(row: dict[str, str] | None, key: str, default: str = "") -> str:
    return default if row is None else str(row.get(key, default))


def build_reference_leaderboard() -> list[dict[str, object]]:
    small = read_csv(SMALL_DIR / "SMALL_FORMULA_PILOT_CANDIDATE_RESULTS.csv")
    medium = read_csv(MEDIUM_DIR / "MEDIUM_FORMULA_PILOT_CANDIDATE_RESULTS.csv")
    gauntlet = read_csv(GAUNTLET_DIR / "GAUNTLET_CANDIDATE_METRICS_SCORECARD.csv")
    refined = read_csv(REFINEMENT_DIR / "DIVERSE_CHAMPION_REFINEMENT_METRICS_SCORECARD.csv")
    refined_pos = read_csv(REFINEMENT_DIR / "DIVERSE_CHAMPION_REFINEMENT_POSITION_RESULTS.csv")
    outlier = read_csv(REFINEMENT_DIR / "DIVERSE_CHAMPION_REFINEMENT_OUTLIER_INFLUENCE_REVIEW.csv")
    slice_rows = read_csv(REFINEMENT_DIR / "DIVERSE_CHAMPION_REFINEMENT_SLICE_GUARDRAILS.csv")

    pyf = find_row(gauntlet, "GAUNTLET_001_PYF_POINTS_ANCHOR")
    small_best = find_row(small, "PILOT_003_THREE_YEAR_WEIGHTED_PRODUCTION_60_30_10") or best_row(small, "spearman_overall", "candidate_spearman")
    medium_best = find_row(medium, "MEDIUM_011_THREE_YEAR_60_30_10") or best_row(medium, "candidate_spearman")
    gauntlet_best = find_row(gauntlet, "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE") or best_row(gauntlet, "candidate_spearman")
    refined_best = find_row(refined, "REFINE_007_OVERALL_THREE_65_25_10_LATE_20") or best_row(refined, "candidate_spearman")
    best_stable_id = safe(refined_best, "candidate_id")
    stable_candidates = [row for row in outlier if row.get("outlier_influence_flag") == "direction_stable"]
    if stable_candidates:
        score_by_id = {row["candidate_id"]: row for row in refined}
        stable_best = max(stable_candidates, key=lambda row: fnum(score_by_id.get(row["candidate_id"], {}), "candidate_spearman"))
        best_stable_id = stable_best["candidate_id"]

    rows: list[dict[str, object]] = [
        {
            "reference_type": "PYF baseline",
            "candidate_id": "PYF",
            "candidate_family": "mandatory_anchor",
            "scope": "QB/RB/WR/TE",
            "spearman": "0.741",
            "delta_vs_pyf": "0.000",
            "status": "anchor_only",
            "use_decision": "required_comparator_not_formula_winner",
            "notes": "Prior-year points remains mandatory baseline.",
        },
        {
            "reference_type": "best small pilot candidate",
            "candidate_id": safe(small_best, "candidate_id"),
            "candidate_family": safe(small_best, "candidate_family"),
            "scope": safe(small_best, "positions", safe(small_best, "scope", "QB/RB/WR/TE")),
            "spearman": safe(small_best, "spearman_overall", safe(small_best, "candidate_spearman")),
            "delta_vs_pyf": safe(small_best, "spearman_delta_vs_pyf"),
            "status": safe(small_best, "interpretation"),
            "use_decision": "preserve_as_review_only_reference",
            "notes": "Small pilot first showed multi-year production could beat/contextualize PYF.",
        },
        {
            "reference_type": "best medium pilot candidate",
            "candidate_id": safe(medium_best, "candidate_id"),
            "candidate_family": safe(medium_best, "candidate_family"),
            "scope": safe(medium_best, "scope"),
            "spearman": safe(medium_best, "candidate_spearman"),
            "delta_vs_pyf": safe(medium_best, "spearman_delta_vs_pyf"),
            "status": safe(medium_best, "interpretation"),
            "use_decision": "preserve_as_review_only_reference",
            "notes": "Medium pilot confirmed three-year production neighborhood.",
        },
        {
            "reference_type": "best full Gauntlet candidate",
            "candidate_id": safe(gauntlet_best, "candidate_id"),
            "candidate_family": safe(gauntlet_best, "candidate_family"),
            "scope": safe(gauntlet_best, "scope"),
            "spearman": safe(gauntlet_best, "candidate_spearman"),
            "delta_vs_pyf": safe(gauntlet_best, "spearman_delta_vs_pyf"),
            "status": safe(gauntlet_best, "interpretation"),
            "use_decision": "preserve_as_current_review_only_reference_best",
            "notes": "Reference best before refinement; not production winner.",
        },
        {
            "reference_type": "best refined candidate",
            "candidate_id": safe(refined_best, "candidate_id"),
            "candidate_family": safe(refined_best, "formula_family"),
            "scope": safe(refined_best, "position_scope"),
            "spearman": safe(refined_best, "candidate_spearman"),
            "delta_vs_pyf": safe(refined_best, "spearman_delta_vs_pyf"),
            "status": safe(refined_best, "interpretation"),
            "use_decision": "preserve_but_do_not_refine_same_ingredients_now",
            "notes": "Tied/trails prior Gauntlet best at rounded precision; no material improvement.",
        },
        {
            "reference_type": "best stable candidate",
            "candidate_id": best_stable_id,
            "candidate_family": safe(find_row(refined, best_stable_id), "formula_family"),
            "scope": safe(find_row(refined, best_stable_id), "position_scope"),
            "spearman": safe(find_row(refined, best_stable_id), "candidate_spearman"),
            "delta_vs_pyf": safe(find_row(refined, best_stable_id), "spearman_delta_vs_pyf"),
            "status": "direction_stable_loso",
            "use_decision": "preserve_as_stability_reference_only",
            "notes": "All 136 refined candidates were direction-stable in leave-one-season-out review.",
        },
    ]

    for position in ["QB", "RB", "WR", "TE"]:
        choices = [row for row in refined_pos if row.get("position") == position]
        best = best_row(choices, "candidate_spearman")
        rows.append(
            {
                "reference_type": f"best refined {position}",
                "candidate_id": best["candidate_id"],
                "candidate_family": best["formula_family"],
                "scope": position,
                "spearman": best["candidate_spearman"],
                "delta_vs_pyf": best["spearman_delta_vs_pyf"],
                "status": "best_by_position_review_only",
                "use_decision": "preserve_as_position_reference_only",
                "notes": "Not approved for rankings integration.",
            }
        )

    guardrail_candidates = [
        row
        for row in slice_rows
        if row.get("slice_name") in {"sparse_history", "low_games", "prior_decline_proxy"}
        and row.get("guardrail_interpretation") == "improves_vs_pyf"
    ]
    guardrail = sorted(
        guardrail_candidates,
        key=lambda row: (int(row.get("false_positive_delta_vs_pyf", "0")), int(row.get("false_negative_delta_vs_pyf", "0"))),
    )[0]
    guardrail_score = find_row(refined, guardrail["candidate_id"])
    rows.append(
        {
            "reference_type": "most promising guardrail/slice candidate",
            "candidate_id": guardrail["candidate_id"],
            "candidate_family": safe(guardrail_score, "formula_family"),
            "scope": guardrail["scope"],
            "spearman": safe(guardrail_score, "candidate_spearman"),
            "delta_vs_pyf": safe(guardrail_score, "spearman_delta_vs_pyf"),
            "status": f"{guardrail['slice_name']}_improves_vs_pyf",
            "use_decision": "preserve_as_slice_reference_only",
            "notes": "Slice value is diagnostic; not production boost/penalty.",
        }
    )
    rows.append(
        {
            "reference_type": "do not refine further now",
            "candidate_id": "same_ingredient_multi_year_weight_neighbors",
            "candidate_family": "multi_year_production_age_role_decline_variants",
            "scope": "QB/RB/WR/TE",
            "spearman": "0.754-0.755 plateau",
            "delta_vs_pyf": "~0.013-0.014",
            "status": "plateaued",
            "use_decision": "block_more_same_ingredient_refinement_until_data_upgrade",
            "notes": "Further weight tweaking did not beat prior Gauntlet best or materially improve seeds.",
        }
    )
    return rows


def build_upgrade_matrix() -> list[dict[str, object]]:
    return [
        {
            "priority_rank": 1,
            "upgrade_option": "PFR RB broken-tackle values into Formula Data Mart",
            "expected_near_term_accuracy_value": "medium",
            "formula_gauntlet_readiness_value": "high_for_blocked_rb_context_branch",
            "current_evidence": "Narrow review-only hypothesis preserved; raw +0.001531 and per-game +0.000651 full-control lift, but values were absent from the Gauntlet mart.",
            "current_blocker": "pfr_rush_brk_tkl values not joined into Formula Data Mart; PFR not production-approved.",
            "recommended_action": "PFR RB Broken Tackle Data Mart Join / Component Test V1",
            "status": "NEXT_EXECUTION_LANE_RECOMMENDED",
            "notes": "RB-only, review-only, must control for rushing volume/PYF and keep PFF/proxy names blocked.",
        },
        {
            "priority_rank": 2,
            "upgrade_option": "Point-in-time market / ADP gate review",
            "expected_near_term_accuracy_value": "medium_high",
            "formula_gauntlet_readiness_value": "medium",
            "current_evidence": "Likely useful dynasty baseline/context, but historical/as-of safety and source gate are not cleared.",
            "current_blocker": "Needs point-in-time source/use-gate review and historical coverage proof.",
            "recommended_action": "Point-in-Time Market / ADP Gate Review V1 later",
            "status": "NEXT_AFTER_PFR_IF_SOURCE_SAFE",
            "notes": "Do not use as production input without separate approval.",
        },
        {
            "priority_rank": 3,
            "upgrade_option": "Point-in-time injury / availability gate review",
            "expected_near_term_accuracy_value": "medium",
            "formula_gauntlet_readiness_value": "medium",
            "current_evidence": "Useful caution/slice context; not an injury prediction lane.",
            "current_blocker": "Needs as-of source proof, identity joins, and missingness policy.",
            "recommended_action": "Point-in-Time Injury Availability Gate Review V1 later",
            "status": "PARKED_PENDING_PFR_OR_MARKET",
            "notes": "Review-only caveat context only unless separately approved.",
        },
        {
            "priority_rank": 4,
            "upgrade_option": "Better age/lifecycle formula treatment",
            "expected_near_term_accuracy_value": "medium",
            "formula_gauntlet_readiness_value": "medium",
            "current_evidence": "Age/lifecycle helped young/early slices and decline taxonomy, but direct boosts/penalties produced harm risk.",
            "current_blocker": "Already used as context; needs design, not same-ingredient weight tweaks.",
            "recommended_action": "Age Lifecycle Formula Treatment Design V1 later",
            "status": "PARKED_DESIGN_ONLY",
            "notes": "Do not convert into direct production boost/penalty.",
        },
        {
            "priority_rank": 5,
            "upgrade_option": "Red-zone exact expansion",
            "expected_near_term_accuracy_value": "medium_if_full_history_recovered",
            "formula_gauntlet_readiness_value": "low_now",
            "current_evidence": "Prior pilot only proved 2024-2025 lagged partial review-only use.",
            "current_blocker": "Not proven for exact 2013-2025 historical replay or same-season prediction.",
            "recommended_action": "Park until full historical/as-of source proof exists.",
            "status": "PARKED_PARTIAL_WITH_CAVEATS",
            "notes": "Do not contaminate 2013-2025 formula comparisons with partial red-zone fields.",
        },
        {
            "priority_rank": 6,
            "upgrade_option": "Historical checkpoint / position-specific Model v4 receipts",
            "expected_near_term_accuracy_value": "low_medium",
            "formula_gauntlet_readiness_value": "medium_for_replay_not_new_signal",
            "current_evidence": "Useful for exact replay/benchmark reconstruction, not clearly the next formula-accuracy gain.",
            "current_blocker": "Receipt families remain partial/missing.",
            "recommended_action": "Historical Checkpoint Receipt Recovery Plan V1 only if replay is prioritized.",
            "status": "PARKED_FOR_REPLAY",
            "notes": "Exact Model v4 replay remains blocked.",
        },
        {
            "priority_rank": 7,
            "upgrade_option": "Shadow model metrics recovery",
            "expected_near_term_accuracy_value": "low_unknown",
            "formula_gauntlet_readiness_value": "low",
            "current_evidence": "Only useful if it blocks a specific approved replay/benchmark.",
            "current_blocker": "Scope/value unclear; recovery burden likely high.",
            "recommended_action": "Shadow Metrics Scope Removal / Recovery Decision V1 later",
            "status": "PARKED",
            "notes": "Do not pursue unless Master HQ identifies a specific blocking dependency.",
        },
        {
            "priority_rank": 8,
            "upgrade_option": "Route/YPRR/TPRR, return scoring, broad PFR, PFF Elusive, unsupported advanced data",
            "expected_near_term_accuracy_value": "not_prioritized_now",
            "formula_gauntlet_readiness_value": "parked",
            "current_evidence": "Route remains hard source recovery; return scoring low current-league value; broad PFR/PFF/proxy names are blocked.",
            "current_blocker": "Source/use gates not approved or not worth prioritizing now.",
            "recommended_action": "Keep parked.",
            "status": "PARK_FOR_LATER_OR_BLOCKED",
            "notes": "Narrow PFR RB broken tackle is the only PFR item recommended for the next lane.",
        },
    ]


def write_artifacts() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    leaderboard = build_reference_leaderboard()
    upgrades = build_upgrade_matrix()
    leader_fields = [
        "reference_type",
        "candidate_id",
        "candidate_family",
        "scope",
        "spearman",
        "delta_vs_pyf",
        "status",
        "use_decision",
        "notes",
    ]
    upgrade_fields = [
        "priority_rank",
        "upgrade_option",
        "expected_near_term_accuracy_value",
        "formula_gauntlet_readiness_value",
        "current_evidence",
        "current_blocker",
        "recommended_action",
        "status",
        "notes",
    ]
    write_csv(OUT_DIR / "FORMULA_RESULTS_REFERENCE_LEADERBOARD.csv", leaderboard, leader_fields)
    write_csv(OUT_DIR / "FORMULA_DATA_UPGRADE_PRIORITY_MATRIX.csv", upgrades, upgrade_fields)

    best_current = next(row for row in leaderboard if row["reference_type"] == "best refined candidate")
    best_gauntlet = next(row for row in leaderboard if row["reference_type"] == "best full Gauntlet candidate")

    report = f"""
# Formula Results Master Review / Data Upgrade Pivot V1 Report

## Verdict

`GREEN_FORMULA_RESULTS_PLATEAU_CONFIRMED_DATA_UPGRADE_NEXT`

## Clear Answer

The current review-only formula family improved beyond PYF but has plateaued with the available ingredients. The best refined candidate, `{best_current['candidate_id']}`, reached Spearman `{best_current['spearman']}` versus PYF `0.741`, but did not beat the prior full-Gauntlet best reference `{best_gauntlet['candidate_id']}` at Spearman `{best_gauntlet['spearman']}`. More same-ingredient weight tweaking should pause until new or better data enters the Formula Data Mart.

## Current Best References

- PYF baseline: `0.741`
- Best small pilot: `{leaderboard[1]['candidate_id']}` Spearman `{leaderboard[1]['spearman']}`
- Best medium pilot: `{leaderboard[2]['candidate_id']}` Spearman `{leaderboard[2]['spearman']}`
- Best full Gauntlet: `{best_gauntlet['candidate_id']}` Spearman `{best_gauntlet['spearman']}`
- Best refinement: `{best_current['candidate_id']}` Spearman `{best_current['spearman']}`

## Plateau Decision

- Refinement beat PYF: yes.
- Refinement beat prior Gauntlet best: no.
- Seed neighborhoods materially improved: no.
- Top candidates are small variants of multi-year production plus age/role/decline context.
- Further same-ingredient refinement is blocked for now.

## Top Data Upgrade

Recommended next execution lane:

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

Rationale: the narrow PFR RB broken-tackle hypothesis was preserved as review-only, but the values were absent from the Formula Data Mart, so Gauntlet could not score that branch. This is the most direct next test of a missing feature that might add non-duplicate RB context. It remains RB-only, review-only, non-production, and must keep PFF/proxy/broad-PFR uses blocked.

## Gates

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior remains unchanged.
- No current formula is a production winner.
- No source is promoted by this packet.
"""
    write_text(OUT_DIR / "FORMULA_RESULTS_MASTER_REVIEW_DATA_UPGRADE_PIVOT_V1_REPORT.md", report)

    plateau = f"""
# Formula Search Plateau Decision

## Decision

`FORMULA_SEARCH_PLATEAU_CONFIRMED_WITH_CURRENT_INGREDIENTS`

## Findings

- Refinement did not improve over the prior Gauntlet best: `{best_current['spearman']}` versus `{best_gauntlet['spearman']}`.
- All `136` refinement candidates beat PYF, which confirms the current production-weight neighborhood is better than the anchor baseline.
- `0` candidates beat the prior Gauntlet best.
- `0` seed neighborhoods materially improved over seed references.
- Top candidates are not materially different signals; they are variants of the same multi-year production family with small age/lifecycle, role, and decline-context changes.

## Decision

Pause further same-ingredient refinement. Preserve the current best review-only references, but do not run another formula sweep until a data upgrade adds a genuinely new allowed input or improves the data substrate.
"""
    write_text(OUT_DIR / "FORMULA_SEARCH_PLATEAU_DECISION.md", plateau)

    next_lane = """
# Formula Next Lane Decision

## Recommended Next Single Lane

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

## Scope

- Join only narrow RB PFR broken-tackle values that are already preserved as review-only hypotheses.
- Test only `pfr_rush_brk_tkl__raw` and `pfr_rush_brk_tkl__per_game` as review-only component context.
- Keep `pfr_rush_brk_tkl__per_attempt` diagnostic only.
- Compare against PYF, multi-year production, rushing volume, sparse-history, and low-games slices.

## Stop Conditions

Stop if source hashes, season coverage, RB identity joins, as-of safety, missingness classification, or Formula Data Mart join integrity cannot be proven.

## Explicitly Not Approved

No broad PFR promotion, no PFR QB passing production use, no PFF Elusive Rating, no `nwr_elusive_proxy_review_only`, no rankings integration, no production/model-use, and no app/runtime changes.
"""
    write_text(OUT_DIR / "FORMULA_NEXT_LANE_DECISION.md", next_lane)

    gates = """
# Formula Results Blockers And Gates

- Current best formula is review-only only.
- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime changes remain blocked.
- Hidden sort and recommendation logic remain blocked.
- No source promotion occurred.
- No formula is approved as final model.
- Same-ingredient formula refinement is blocked until a data upgrade is completed.
- Future ranking simulation, if ever approved, must be review-only and separately contracted.
- PFR RB broken-tackle remains narrow RB-only review context. PFR production use remains blocked.
- Route/YPRR/TPRR, return scoring, broad PFR, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain parked or blocked.
"""
    write_text(OUT_DIR / "FORMULA_RESULTS_BLOCKERS_AND_GATES.md", gates)

    source_trace = f"""
# Formula Results Master Source Trace

## Inputs Read

- Diverse Champion Refinement V1: `{REFINEMENT_DIR}`
- Prior refinement commit: `{PRIOR_REFINEMENT_COMMIT}`
- Full Review-Only Formula Gauntlet Candidate Arena V1: `{GAUNTLET_DIR}`
- Gauntlet Candidate Diversity / Clustering Audit V1: `{CLUSTER_DIR}`
- Medium Review-Only Formula Pilot V1: `{MEDIUM_DIR}`
- Small Review-Only Formula Pilot V1: `{SMALL_DIR}`
- Formula Data Mart / Feature Availability Audit V1: `{DATA_MART_DIR}`
- Remaining Data Upgrades Sweep V1: `{UPGRADE_SWEEP_DIR}`
- Age / Lifecycle Master Review V1: `{AGE_MASTER_DIR}`
- Role Archetype Master Review V1: `{ROLE_MASTER_DIR}`
- PFR RB Broken Tackle Addendum V1: `{PFR_ADDENDUM_DIR}`

## Method

The packet reads prior review-only formula result CSVs and Data Hygiene upgrade artifacts, preserves the current review-only formula references, compares refinement against the accepted Gauntlet best, and ranks data upgrades by likely near-term accuracy value and execution readiness.

## Safety

No formula candidates were run. No rankings, app/runtime behavior, source gates, production model-use, canonical `local_exports`, push, or merge were changed.
"""
    write_text(OUT_DIR / "FORMULA_RESULTS_MASTER_SOURCE_TRACE.md", source_trace)


def validate() -> None:
    required = [
        "FORMULA_RESULTS_MASTER_REVIEW_DATA_UPGRADE_PIVOT_V1_REPORT.md",
        "FORMULA_RESULTS_REFERENCE_LEADERBOARD.csv",
        "FORMULA_SEARCH_PLATEAU_DECISION.md",
        "FORMULA_DATA_UPGRADE_PRIORITY_MATRIX.csv",
        "FORMULA_NEXT_LANE_DECISION.md",
        "FORMULA_RESULTS_BLOCKERS_AND_GATES.md",
        "FORMULA_RESULTS_MASTER_SOURCE_TRACE.md",
    ]
    missing = [name for name in required if not (OUT_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"Missing required artifacts: {missing}")
    for path in OUT_DIR.glob("*.csv"):
        read_csv(path)
    py_compile.compile(__file__, doraise=True)


def main() -> None:
    write_artifacts()
    validate()
    print("formula_results_master_review_data_upgrade_pivot_complete verdict=GREEN_FORMULA_RESULTS_PLATEAU_CONFIRMED_DATA_UPGRADE_NEXT next=PFR_RB_Broken_Tackle_Data_Mart_Join_Component_Test_V1")


if __name__ == "__main__":
    main()
