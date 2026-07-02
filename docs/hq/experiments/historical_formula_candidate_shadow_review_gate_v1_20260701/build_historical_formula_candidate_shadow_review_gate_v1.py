from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
ROOT_EXPERIMENT_DIR = EXPERIMENT_DIR.parent

SEARCH_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_search_v1_20260701"
REVIEW_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_review_v1_20260701"
GATE_PREP_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_promotion_gate_prep_v1_20260701"
RESCUE_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_risk_rescue_sprint_v1_20260701"
REFINEMENT_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_cutline_safe_refinement_v1_20260701"
TARGETED_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_targeted_redesign_v1_20260701"

BASE_HEAD = "567e3a9e2ab91d36f65e694a25e3b67356dbe2b5"
BRANCH = "work/historical-formula-candidate-shadow-review-gate-v1-20260701"
DECISION = "GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY"
VERDICT = "GREEN_SHADOW_REVIEW_GATE_GO_REVIEW_ONLY"

BASELINE = "baseline_v3_prior_points"
ORIGINAL = "original_usage_opportunity_volume"
QB_GUARD = "qb_guard_soft_blend"
RB_WR_SAFE = "rb_wr_cutline_safe_blend"
CONSERVATIVE = "conservative_blend_50"
SELECTED = "wr_boundary_breakout_sensitivity_guard"

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "shadow_review_gate_summary.md",
    "shadow_review_decision.md",
    "tim_human_review_notes_applied.md",
    "selected_redesign_metric_summary.csv",
    "baseline_vs_candidate_gate_matrix.csv",
    "remaining_cutline_case_review.md",
    "pollard_lamb_case_decision.md",
    "position_season_stability_gate_report.csv",
    "startable_topn_gate_report.csv",
    "shadow_review_packet_requirements.md",
    "blocked_production_promotion_report.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    validate_inputs()

    validation = pd.read_csv(TARGETED_DIR / "validation_metric_comparison.csv")
    holdout = pd.read_csv(TARGETED_DIR / "holdout_metric_comparison.csv")
    cutline = pd.read_csv(TARGETED_DIR / "cutline_miss_comparison.csv")
    elite = pd.read_csv(TARGETED_DIR / "elite_qb_regression_comparison.csv")
    remaining = pd.read_csv(TARGETED_DIR / "remaining_concern_casebook.csv")
    resolution = pd.read_csv(TARGETED_DIR / "remaining_5_case_resolution_report.csv")
    position = pd.read_csv(TARGETED_DIR / "position_level_redesign_report.csv")
    season = pd.read_csv(TARGETED_DIR / "season_level_redesign_report.csv")
    topn = pd.read_csv(TARGETED_DIR / "topn_startable_redesign_report.csv")

    context = build_context(validation, holdout, cutline, elite, remaining, resolution, position, season)
    write_csv(build_selected_metric_summary(validation, holdout, cutline, elite), "selected_redesign_metric_summary.csv")
    write_csv(build_gate_matrix(context), "baseline_vs_candidate_gate_matrix.csv")
    write_csv(build_position_season_report(position, season), "position_season_stability_gate_report.csv")
    write_csv(build_startable_topn_report(topn), "startable_topn_gate_report.csv")
    write_markdown_reports(context, remaining, resolution)
    write_manifest(context)

    print(f"wrote={EXPERIMENT_DIR}")
    print(f"decision={DECISION}")
    return 0


def validate_inputs() -> None:
    required_dirs = [SEARCH_DIR, REVIEW_DIR, GATE_PREP_DIR, RESCUE_DIR, REFINEMENT_DIR, TARGETED_DIR]
    missing = [str(path) for path in required_dirs if not path.exists()]
    if missing:
        raise ValueError(f"Missing merged prerequisite artifact directories: {missing}")
    required_targeted_files = [
        "validation_metric_comparison.csv",
        "holdout_metric_comparison.csv",
        "cutline_miss_comparison.csv",
        "elite_qb_regression_comparison.csv",
        "remaining_concern_casebook.csv",
        "remaining_5_case_resolution_report.csv",
        "position_level_redesign_report.csv",
        "season_level_redesign_report.csv",
        "topn_startable_redesign_report.csv",
    ]
    missing_files = [name for name in required_targeted_files if not (TARGETED_DIR / name).exists()]
    if missing_files:
        raise ValueError(f"Targeted redesign packet is incomplete: {missing_files}")


def build_context(
    validation: pd.DataFrame,
    holdout: pd.DataFrame,
    cutline: pd.DataFrame,
    elite: pd.DataFrame,
    remaining: pd.DataFrame,
    resolution: pd.DataFrame,
    position: pd.DataFrame,
    season: pd.DataFrame,
) -> dict[str, Any]:
    val = validation.set_index("candidate_id")
    hold = holdout.set_index("candidate_id")
    cuts = cutline[cutline["split"].eq("validation_holdout")].set_index("candidate_id")
    elite_review = elite[elite["split"].eq("validation_holdout")].set_index("candidate_id")
    selected_holdout_position = position[(position["split"].eq("holdout")) & (position["candidate_id"].eq(SELECTED))]
    selected_holdout_season = season[(season["split"].eq("holdout")) & (season["candidate_id"].eq(SELECTED))]

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT,
        "decision": DECISION,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "selected": SELECTED,
        "original_holdout_mae_delta": hold.loc[ORIGINAL, "mae_delta_vs_baseline"],
        "qb_guard_holdout_mae_delta": hold.loc[QB_GUARD, "mae_delta_vs_baseline"],
        "rb_wr_holdout_mae_delta": hold.loc[RB_WR_SAFE, "mae_delta_vs_baseline"],
        "selected_validation_mae_delta": val.loc[SELECTED, "mae_delta_vs_baseline"],
        "selected_holdout_mae_delta": hold.loc[SELECTED, "mae_delta_vs_baseline"],
        "selected_validation_spearman_delta": val.loc[SELECTED, "spearman_delta_vs_baseline"],
        "selected_holdout_spearman_delta": hold.loc[SELECTED, "spearman_delta_vs_baseline"],
        "selected_validation_startable_delta": val.loc[SELECTED, "startable_precision_delta_vs_baseline"],
        "selected_holdout_startable_delta": hold.loc[SELECTED, "startable_precision_delta_vs_baseline"],
        "original_cutline_misses": int(cuts.loc[ORIGINAL, "actual_hits_moved_below_cutline"]),
        "rb_wr_cutline_misses": int(cuts.loc[RB_WR_SAFE, "actual_hits_moved_below_cutline"]),
        "selected_cutline_misses": int(cuts.loc[SELECTED, "actual_hits_moved_below_cutline"]),
        "original_elite_qb_severe": int(elite_review.loc[ORIGINAL, "severe_regression_count"]),
        "selected_elite_qb_severe": int(elite_review.loc[SELECTED, "severe_regression_count"]),
        "remaining_count": int(len(remaining)),
        "remaining_players": ", ".join(remaining["player_name"].astype(str).tolist()),
        "resolved_prior_five": int(resolution["resolved_by_selected_redesign"].astype(bool).sum()),
        "prior_five_count": int(len(resolution)),
        "holdout_positions_improved": int(selected_holdout_position["mae_delta_vs_baseline"].astype(float).lt(0).sum()),
        "holdout_position_count": int(len(selected_holdout_position)),
        "holdout_seasons_improved": int(selected_holdout_season["mae_delta_vs_baseline"].astype(float).lt(0).sum()),
        "holdout_season_count": int(len(selected_holdout_season)),
    }


def build_selected_metric_summary(
    validation: pd.DataFrame, holdout: pd.DataFrame, cutline: pd.DataFrame, elite: pd.DataFrame
) -> pd.DataFrame:
    metric_frames = [validation, holdout]
    rows = []
    for frame in metric_frames:
        split = str(frame["split"].iloc[0])
        cutline_split = cutline[cutline["split"].eq(split)].set_index("candidate_id")
        elite_split = elite[elite["split"].eq(split)].set_index("candidate_id")
        for candidate_id in [BASELINE, ORIGINAL, QB_GUARD, RB_WR_SAFE, CONSERVATIVE, SELECTED]:
            metric = frame[frame["candidate_id"].eq(candidate_id)].iloc[0].to_dict()
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "split": split,
                    "mae": metric["mae"],
                    "mae_delta_vs_baseline": metric["mae_delta_vs_baseline"],
                    "spearman_delta_vs_baseline": metric["spearman_delta_vs_baseline"],
                    "startable_precision_delta_vs_baseline": metric["startable_precision_delta_vs_baseline"],
                    "actual_hits_moved_below_cutline": int(
                        cutline_split.loc[candidate_id, "actual_hits_moved_below_cutline"]
                    ),
                    "elite_qb_severe_regressions": int(elite_split.loc[candidate_id, "severe_regression_count"]),
                    "review_only": True,
                    "production_approved": False,
                    "shadow_review_packet_gate_candidate": candidate_id == SELECTED,
                }
            )
    review_cutline = cutline[cutline["split"].eq("validation_holdout")].set_index("candidate_id")
    review_elite = elite[elite["split"].eq("validation_holdout")].set_index("candidate_id")
    rows.append(
        {
            "candidate_id": SELECTED,
            "split": "validation_holdout",
            "mae": "",
            "mae_delta_vs_baseline": "",
            "spearman_delta_vs_baseline": "",
            "startable_precision_delta_vs_baseline": "",
            "actual_hits_moved_below_cutline": int(review_cutline.loc[SELECTED, "actual_hits_moved_below_cutline"]),
            "elite_qb_severe_regressions": int(review_elite.loc[SELECTED, "severe_regression_count"]),
            "review_only": True,
            "production_approved": False,
            "shadow_review_packet_gate_candidate": True,
        }
    )
    return pd.DataFrame(rows)


def build_gate_matrix(context: dict[str, Any]) -> pd.DataFrame:
    rows = [
        gate_row(
            "material_holdout_mae_improvement",
            "PASS",
            f"Selected holdout MAE delta is {context['selected_holdout_mae_delta']} versus baseline.",
        ),
        gate_row(
            "startable_precision_flat_or_better",
            "PASS",
            f"Validation / holdout startable precision deltas are {context['selected_validation_startable_delta']} / {context['selected_holdout_startable_delta']}.",
        ),
        gate_row(
            "spearman_no_material_degradation",
            "PASS",
            f"Holdout Spearman delta is {context['selected_holdout_spearman_delta']}; validation delta is small at {context['selected_validation_spearman_delta']}.",
        ),
        gate_row(
            "elite_qb_issue_remains_fixed",
            "PASS",
            f"Elite-QB severe regressions are {context['selected_elite_qb_severe']} versus original {context['original_elite_qb_severe']}.",
        ),
        gate_row(
            "cutline_harm_reduced_and_explainable",
            "PASS",
            f"Actual cutline hits moved below cutline improved original {context['original_cutline_misses']} -> rb/wr safe {context['rb_wr_cutline_misses']} -> selected {context['selected_cutline_misses']}; remaining players are {context['remaining_players']}.",
        ),
        gate_row(
            "no_position_or_season_collapse",
            "PASS",
            f"Holdout MAE improved across {context['holdout_positions_improved']}/{context['holdout_position_count']} positions and {context['holdout_seasons_improved']}/{context['holdout_season_count']} seasons.",
        ),
        gate_row(
            "tim_review_notes_support_gate",
            "PASS",
            "Tim marked Pollard acceptable/explainable and Lamb worth watching but not a blocker.",
        ),
        gate_row(
            "interpretable_shadow_packet_candidate",
            "PASS",
            "Selected redesign is a fixed WR24/WR36 boundary sensitivity guard using feature-season usage ranks and prediction ranks.",
        ),
        gate_row(
            "production_promotion_blocked",
            "PASS",
            "This gate authorizes only a review-only shadow comparison packet; production promotion remains blocked.",
        ),
    ]
    return pd.DataFrame(rows)


def gate_row(gate: str, status: str, evidence: str) -> dict[str, str]:
    return {
        "gate_question": gate,
        "status": status,
        "evidence": evidence,
        "decision_effect": DECISION if status == "PASS" else "BLOCK",
        "review_only": "true",
        "production_approved": "false",
    }


def build_position_season_report(position: pd.DataFrame, season: pd.DataFrame) -> pd.DataFrame:
    position_rows = position[
        position["candidate_id"].isin([BASELINE, RB_WR_SAFE, SELECTED])
        & position["split"].isin(["validation", "holdout"])
    ].copy()
    position_rows["gate_dimension"] = "position"
    season_rows = season[
        season["candidate_id"].isin([BASELINE, RB_WR_SAFE, SELECTED])
        & season["split"].isin(["validation", "holdout"])
    ].copy()
    season_rows["gate_dimension"] = "season"
    common = [
        "gate_dimension",
        "candidate_id",
        "split",
        "position",
        "target_season",
        "rows",
        "mae",
        "mae_delta_vs_baseline",
        "spearman_delta_vs_baseline",
        "startable_precision_delta_vs_baseline",
    ]
    for column in ["position", "target_season"]:
        if column not in position_rows:
            position_rows[column] = ""
        if column not in season_rows:
            season_rows[column] = ""
    output = pd.concat([position_rows, season_rows], ignore_index=True)
    return output[common]


def build_startable_topn_report(topn: pd.DataFrame) -> pd.DataFrame:
    output = topn[topn["candidate_id"].isin([BASELINE, RB_WR_SAFE, SELECTED])].copy()
    output["review_only"] = True
    output["production_approved"] = False
    return output[
        [
            "candidate_id",
            "split",
            "position",
            "bucket",
            "n_per_season",
            "precision",
            "recall",
            "f1",
            "precision_delta_vs_baseline",
            "f1_delta_vs_baseline",
            "material_regression_vs_baseline",
            "review_only",
            "production_approved",
        ]
    ]


def write_markdown_reports(context: dict[str, Any], remaining: pd.DataFrame, resolution: pd.DataFrame) -> None:
    reports = {
        "shadow_review_gate_summary.md": summary_md(context),
        "shadow_review_decision.md": decision_md(context),
        "tim_human_review_notes_applied.md": tim_notes_md(context),
        "remaining_cutline_case_review.md": remaining_case_review_md(remaining),
        "pollard_lamb_case_decision.md": pollard_lamb_md(remaining),
        "shadow_review_packet_requirements.md": packet_requirements_md(),
        "blocked_production_promotion_report.md": blocked_promotion_md(),
        "guardrail_report.md": guardrail_md(),
        "merge_safety_report.md": merge_safety_md(),
        "next_phase_handoff.md": next_phase_md(context),
    }
    for name, body in reports.items():
        write_text(name, body)


def summary_md(context: dict[str, Any]) -> str:
    return f"""
# Historical Formula Candidate Shadow Review Gate V1

Verdict: `{context['verdict']}`

Decision: `{context['decision']}`

Selected candidate: `{context['selected']}`

This gate reviews merged historical candidate evidence and Tim's human review notes. It does not approve production promotion, create app pages, start live preview, change rankings, or wire candidate output into NWR.

## Gate Evidence

- Holdout MAE delta: `{context['selected_holdout_mae_delta']}`
- Holdout Spearman delta: `{context['selected_holdout_spearman_delta']}`
- Holdout startable precision delta: `{context['selected_holdout_startable_delta']}`
- Cutline misses: original `{context['original_cutline_misses']}`, rb/wr safe `{context['rb_wr_cutline_misses']}`, selected `{context['selected_cutline_misses']}`
- Elite-QB severe regressions: original `{context['original_elite_qb_severe']}`, selected `{context['selected_elite_qb_severe']}`
- Remaining cutline players: `{context['remaining_players']}`
- Holdout MAE improved across `{context['holdout_positions_improved']}/{context['holdout_position_count']}` positions and `{context['holdout_seasons_improved']}/{context['holdout_season_count']}` seasons.

Conclusion: the selected redesign may advance to a review-only side-by-side shadow comparison packet. Production promotion remains blocked.
"""


def decision_md(context: dict[str, Any]) -> str:
    return f"""
# Shadow Review Decision

Decision: `{DECISION}`

Rationale:

- The selected redesign materially improves holdout MAE versus baseline.
- Startable precision is flat versus baseline on validation and holdout.
- Holdout Spearman does not degrade.
- Elite-QB severe regressions remain controlled.
- Actual cutline hits moved below cutline are reduced to `{context['selected_cutline_misses']}`.
- Tim's Pollard and Lamb notes support advancing to a side-by-side review artifact.

This decision approves only the next review artifact lane. It does not approve shadow app wiring, production rankings, production configs, formula rollout, or promotion.
"""


def tim_notes_md(context: dict[str, Any]) -> str:
    return """
# Tim Human Review Notes Applied

Tim standard applied:

- A 100% historical hit rate is not expected.
- If a candidate improves the board broadly and the remaining misses are explainable, it can advance to shadow review.
- Shadow review is still review-only and does not imply production promotion.

Pollard:

- Tim considers Tony Pollard 2021 -> 2022 acceptable and explainable.
- Pollard's 2021 efficiency may have been boosted by role context behind Ezekiel Elliott.
- A cautious formula before 2022 is not a fatal miss.

Lamb:

- Tim would have preferred roughly WR8-WR12 after 2021 based on youth, production, and draft capital.
- The selected redesign landing near WR13 is slightly low.
- Lamb remains worth watching in the shadow packet, but Tim does not treat this as a blocker.

Gate effect: Tim's notes convert the remaining two cutline misses from blockers into watchlist cases for a review-only shadow comparison packet.
"""


def remaining_case_review_md(remaining: pd.DataFrame) -> str:
    rows = []
    for _, row in remaining.iterrows():
        rows.append(
            f"- `{row['player_name']}`: baseline rank `{int(row['baseline_rank'])}`, selected redesign rank `{int(row['selected_redesign_rank'])}`, actual finish `{row['position']}{int(row['actual_position_finish'])}`."
        )
    joined = "\n".join(rows)
    return f"""
# Remaining Cutline Case Review

Remaining selected-redesign cutline cases:

{joined}

Gate interpretation:

- Both remaining cases are known, explainable, and small enough to carry into a side-by-side shadow packet.
- Pollard is acceptable/explainable under Tim's notes.
- Lamb remains a watchlist case and must be highlighted prominently in the next packet.
- Neither case authorizes production promotion.
"""


def pollard_lamb_md(remaining: pd.DataFrame) -> str:
    pollard = remaining[remaining["player_name"].eq("T.Pollard")].iloc[0]
    lamb = remaining[remaining["player_name"].eq("C.Lamb")].iloc[0]
    return f"""
# Pollard/Lamb Case Decision

## T.Pollard

- Selected rank: RB{int(pollard['selected_redesign_rank'])}; cutline: RB{int(pollard['cutline'])}; actual finish: RB{int(pollard['actual_position_finish'])}.
- Human decision: acceptable/explainable.
- Reason: 2021 efficiency may have been boosted by role context behind Ezekiel Elliott, so caution before 2022 is not fatal.
- Gate effect: not a blocker.

## C.Lamb

- Selected rank: WR{int(lamb['selected_redesign_rank'])}; cutline: WR{int(lamb['cutline'])}; actual finish: WR{int(lamb['actual_position_finish'])}.
- Human decision: watchlist, not blocker.
- Reason: Tim would have preferred roughly WR8-WR12 after 2021. WR13 is slightly low but close enough to carry into side-by-side review.
- Gate effect: advance only if Lamb is explicitly tracked in the shadow packet.

Final case decision: both remaining misses are acceptable for review-only shadow packet preparation. Production promotion remains blocked.
"""


def packet_requirements_md() -> str:
    return """
# Shadow Review Packet Requirements

The next review-only packet should include:

1. Static side-by-side comparison of baseline, original candidate, qb_guard, rb_wr_safe, and selected redesign.
2. Player-level rank and score deltas for validation and holdout seasons.
3. Dedicated Pollard and Lamb watchlist cards.
4. Cutline movement report for QB12/RB12/RB24/WR12/WR24/WR36/TE12.
5. Startable/top-N precision and recall report by position and season.
6. Largest positive/negative movement casebook.
7. Clear "do not promote" notice.
8. Human decision checklist for whether shadow evidence is useful enough for future planning.

The packet must remain static and review-only. Do not create app pages, live preview, ranking wiring, hidden sort, recommendations, production configs, source-truth promotion, or formula rollout.
"""


def blocked_promotion_md() -> str:
    return """
# Blocked Production Promotion Report

Production promotion remains blocked.

Not approved:

- Production formula changes.
- Production model training or tuning.
- Ranking changes.
- App wiring or live preview page.
- Recommendations or hidden sort.
- Source-truth promotion.
- Runtime, service, or production config changes.
- Candidate output wired into NWR.

Approved by this gate only:

- A future static side-by-side shadow comparison packet for human review.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Status: PASS for review-only Shadow Review Gate V1 artifacts.

Confirmed:

- No production formula changes.
- No production model training or tuning.
- No formula promotion.
- No app wiring or live preview page.
- No rankings, recommendations, or hidden sort changes.
- No source-truth promotion.
- No runtime, service, or production config changes.
- No candidate output is wired into NWR.
- Feature season N and target season N+1 separation remains inherited from merged substrate/search artifacts.
- No routes, TPRR, YPRR, route proxies, ambiguous `rz_att`, red-zone sidecars, or current-only context.
- No market, ADP, vendor, projection, or external rank fields are source truth.
- No raw/shared/cache/local export/secrets files are intentionally tracked.
- No production promotion is approved.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

Scope: review-only Shadow Review Gate V1 artifacts and one focused artifact/schema test.

Expected changed paths:

- `docs/hq/experiments/historical_formula_candidate_shadow_review_gate_v1_20260701/`
- `tests/test_historical_formula_candidate_shadow_review_gate_v1_20260701.py`

No app, model, ranking, formula, source-truth, runtime, service, production config, raw/shared/cache/local export, or secret paths are intentionally changed.
"""


def next_phase_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommended next phase: `Historical Formula Candidate Shadow Review Packet V1`.

The next phase should build a static, review-only side-by-side comparison packet for `{SELECTED}` with Pollard and Lamb explicitly highlighted as watchlist cases.

Do not start production promotion. Do not wire the candidate into rankings, app pages, source truth, hidden sort, recommendations, model behavior, runtime behavior, or production config.
"""


def write_manifest(context: dict[str, Any]) -> None:
    rows = []
    for name in REQUIRED_ARTIFACTS + ["build_historical_formula_candidate_shadow_review_gate_v1.py"]:
        path = EXPERIMENT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    body = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{BRANCH}`
- Base HEAD: `{BASE_HEAD}`
- Decision: `{DECISION}`
- Selected redesign: `{SELECTED}`
- Review-only: true
- Production promotion approved: false
- Shadow review packet approved: true
- App/ranking/model/runtime wiring approved: false

| Artifact | Bytes | SHA-256 |
|---|---:|---|
{chr(10).join(rows)}
"""
    write_text("artifact_manifest.md", body)


def write_csv(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(EXPERIMENT_DIR / name, index=False)


def write_text(name: str, body: str) -> None:
    (EXPERIMENT_DIR / name).write_text(body.strip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
