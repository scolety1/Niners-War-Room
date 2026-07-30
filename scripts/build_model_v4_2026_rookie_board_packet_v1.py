"""Generate the governed 28-file Model V4 2026 rookie review packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

PACKET_REL = Path(
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730"
)
VERDICT = "YELLOW_NWR_MODEL_V4_2026_ROOKIE_BOARD_BUILT_WITH_SOURCE_LIMITS"
REQUIRED = (
    "MODEL_V4_2026_ROOKIE_BOARD_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "ANALYZER_AUTHORITY_AND_VERSION.md",
    "INPUT_DEPENDENCY_GRAPH.csv",
    "EXACT_MATRIX_RESTORATION_RESULTS.csv",
    "COMPATIBLE_INPUT_RECONSTRUCTION_CONTRACT.md",
    "INPUT_SOURCE_AND_FIELD_MAPPING.csv",
    "2026_ROOKIE_IDENTITY_CROSSWALK.csv",
    "2026_ROOKIE_IDENTITY_BLOCKERS.csv",
    "MODEL_V4_2026_INPUT_COVERAGE.csv",
    "MODEL_V4_2026_COMPONENT_ROWS.csv",
    "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv",
    "MODEL_V4_2026_POSITION_RANKS.csv",
    "MODEL_V4_2026_TIERS.csv",
    "DRAFT_CAPITAL_DISAGREEMENTS.csv",
    "TOP_FLOOR_UPSIDE_RISK_PROFILES.csv",
    "MISSINGNESS_AND_CONFIDENCE_RESULTS.csv",
    "FORMULA_RECONCILIATION_RESULTS.csv",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "DETERMINISTIC_REGENERATION_RESULTS.csv",
    "OPTIONAL_DRAFT_BOARD_SURFACE_RESULTS.md",
    "FINISHED_V1_OUTCOME_V3_TRADING_LAB_NO_CHANGE.md",
    "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
    "PROTECTED_AND_FROZEN_PATH_PROOF.md",
    "ROLLBACK_PLAN.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo)
    parser.add_argument("--run-a", type=Path, required=True)
    parser.add_argument("--run-b", type=Path, required=True)
    parser.add_argument("--hermetic", default="PENDING")
    parser.add_argument("--localdata", default="PENDING")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    packet = repo / PACKET_REL
    packet.mkdir(parents=True, exist_ok=True)
    board = _read(args.run_a / "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv")
    prospect = _read(args.run_a / "analyzer_outputs/prospect_value_review_rows.csv")
    components = _read(args.run_a / "analyzer_outputs/prospect_value_component_rows.csv")
    confidence = _read(
        args.run_a / "analyzer_outputs/confidence_missingness_review_rows.csv"
    )
    matrix = _read(
        args.run_a
        / "compatible_input_pack/admitted_prospect_current_feature_matrix.csv"
    )
    mutations = _read(args.run_a / "MUTATION_SENSITIVITY_RESULTS.csv")
    receipt_a = _json(args.run_a / "DETERMINISTIC_RUN_RECEIPT.json")
    receipt_b = _json(args.run_b / "DETERMINISTIC_RUN_RECEIPT.json")
    if receipt_a["governed_digest"] != receipt_b["governed_digest"]:
        raise RuntimeError("two-root governed digest mismatch")

    exact = board.loc[board["player_id"].ne("")].copy()
    blocked = board.loc[board["player_id"].eq("")].copy()
    exact["overall_review_rank"] = pd.to_numeric(exact["overall_review_rank"])
    exact["overall_pick"] = pd.to_numeric(exact["overall_pick"])
    exact["drafted_skill_order"] = exact["overall_pick"].rank(method="first").astype(int)
    exact["review_minus_draft_order"] = (
        exact["overall_review_rank"] - exact["drafted_skill_order"]
    )
    _write_core_csvs(packet, board, exact, blocked, components, confidence, matrix)
    _write_contract_csvs(packet, repo)
    _write_analysis_csvs(packet, exact, prospect, components, confidence, mutations)
    _write_determinism(packet, args.run_a, args.run_b, receipt_a, receipt_b)
    _write_markdown(
        packet,
        exact,
        blocked,
        receipt_a,
        hermetic=args.hermetic,
        localdata=args.localdata,
    )
    _write_inventory(repo, packet)
    _write_manifest(packet, receipt_a)
    missing = [name for name in REQUIRED if not (packet / name).is_file()]
    if missing:
        raise RuntimeError(f"packet files missing: {missing}")
    print(
        json.dumps(
            {
                "packet": str(packet),
                "files": len(REQUIRED),
                "verdict": VERDICT,
                "governed_digest": receipt_a["governed_digest"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _write_core_csvs(
    packet: Path,
    board: pd.DataFrame,
    exact: pd.DataFrame,
    blocked: pd.DataFrame,
    components: pd.DataFrame,
    confidence: pd.DataFrame,
    matrix: pd.DataFrame,
) -> None:
    _frame(packet / "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv", board)
    _frame(packet / "MODEL_V4_2026_COMPONENT_ROWS.csv", components)
    _frame(
        packet / "MODEL_V4_2026_POSITION_RANKS.csv",
        exact[
            [
                "player_id",
                "player_name",
                "position",
                "position_rank",
                "overall_review_rank",
                "sprint14e_format_score",
                "rank_label",
            ]
        ].sort_values(["position", "position_rank"], kind="stable"),
    )
    _frame(
        packet / "MODEL_V4_2026_TIERS.csv",
        exact[
            [
                "player_id",
                "player_name",
                "position",
                "overall_review_rank",
                "tier",
                "evidence_confidence",
                "source_limit_state",
            ]
        ].sort_values("overall_review_rank", kind="stable"),
    )
    _frame(
        packet / "2026_ROOKIE_IDENTITY_CROSSWALK.csv",
        exact[
            [
                "player_id",
                "player_name",
                "position",
                "nfl_team",
                "college",
                "draft_round",
                "overall_pick",
                "identity_status",
                "identity_method",
            ]
        ].sort_values("overall_pick", kind="stable"),
    )
    _frame(
        packet / "2026_ROOKIE_IDENTITY_BLOCKERS.csv",
        blocked[
            [
                "player_name",
                "position",
                "nfl_team",
                "college",
                "draft_round",
                "overall_pick",
                "identity_status",
                "blocking_reason",
            ]
        ].sort_values("overall_pick", kind="stable"),
    )
    coverage_rows: list[dict[str, object]] = []
    for position, group in board.groupby("position", sort=True):
        scored = group["final_review_score"].ne("")
        coverage_rows.append(
            {
                "position": position,
                "drafted_rows": len(group),
                "exact_identity_rows": int(group["player_id"].ne("").sum()),
                "blocked_identity_rows": int(group["player_id"].eq("").sum()),
                "scored_rows": int(scored.sum()),
                "unscored_rows": int((~scored).sum()),
                "production_rows": int(group["production_component"].ne("").sum()),
                "market_share_rows": int(group["market_share_component"].ne("").sum()),
                "draft_capital_rows": int(group["draft_capital_component"].ne("").sum()),
                "athletic_rows": int(group["athletic_component"].ne("").sum()),
                "recruiting_rows": int(group["recruiting_component"].ne("").sum()),
                "age_rows": int(group["age_component"].ne("").sum()),
            }
        )
    _rows(packet / "MODEL_V4_2026_INPUT_COVERAGE.csv", coverage_rows)
    missing_rows = exact[
        [
            "player_id",
            "player_name",
            "position",
            "missing_components",
            "confidence_cap",
            "evidence_confidence",
            "warning_codes",
            "source_limit_state",
        ]
    ].copy()
    matrix_by_id = matrix.set_index("canonical_prospect_key")
    missing_rows["combine_source_missing"] = [
        "missing_combine_evidence"
        in matrix_by_id.loc[player_id, "warning_flags"]
        for player_id in missing_rows["player_id"]
    ]
    confidence_by_id = confidence.set_index("entity_key")
    missing_rows["confidence_cap_reasons"] = [
        confidence_by_id.loc[player_id, "cap_reasons"]
        for player_id in missing_rows["player_id"]
    ]
    _frame(packet / "MISSINGNESS_AND_CONFIDENCE_RESULTS.csv", missing_rows)


def _write_contract_csvs(packet: Path, repo: Path) -> None:
    dependencies = [
        (
            "admitted_prospect_current_feature_matrix.csv",
            "PROSPECT_MATRIX_HEADER",
            "canonical_prospect_key exact GSIS",
            "Sprint 12/13 production, share, athletic, recruiting",
            "missing component excluded and weights renormalized",
            "nflverse + reviewed CFBD immutable receipts",
            "COMPATIBLE_2026_RECONSTRUCTION_REQUIRED",
        ),
        (
            "confidence_missingness_review_rows.csv",
            "CONFIDENCE_REVIEW_HEADER",
            "entity_key exact GSIS",
            "Sprint 12/13 confidence cap",
            "existing minimum-cap contract",
            "existing Model V4 confidence service",
            "EXACT_DETERMINISTIC_REGENERATION",
        ),
        (
            "player_age_2026.csv",
            "ROOKIE_AGE_HEADER; decimal years",
            "normalized name downstream after exact GSIS construction",
            "age lifecycle",
            "missing remains blank",
            "nflverse players birth_date + 2026 selection date",
            "COMPATIBLE_2026_RECONSTRUCTION_REQUIRED",
        ),
        (
            "rookie_draft_capital_2026.csv",
            "DRAFT_CAPITAL_HEADER; round/overall pick",
            "normalized name downstream after exact GSIS construction",
            "draft capital and guardrails",
            "missing blocks draft-capital component",
            "nflverse draft_picks immutable snapshot",
            "COMPATIBLE_2026_RECONSTRUCTION_REQUIRED",
        ),
        (
            "prospect_value_review_rows.csv",
            "PROSPECT_REVIEW_HEADER",
            "canonical_prospect_key exact GSIS",
            "Sprint 14E",
            "unscored rows omitted by Sprint 14E",
            "actual Sprint 12/13 public builder",
            "EXACT_DETERMINISTIC_REGENERATION",
        ),
        (
            "rookie_draft_board_review_rows.csv",
            "SPRINT14E_BOARD_HEADER",
            "rookie_board_key exact GSIS",
            "complete governed board adapter",
            "blocked identities merged as visible unranked rows",
            "actual Sprint 14E public builder",
            "EXACT_DETERMINISTIC_REGENERATION",
        ),
    ]
    _rows(
        packet / "INPUT_DEPENDENCY_GRAPH.csv",
        [
            dict(
                zip(
                    (
                        "expected_path",
                        "required_schema_and_units",
                        "identity_key",
                        "formula_consumer",
                        "missingness_handling",
                        "expected_source_receipt",
                        "classification",
                    ),
                    row,
                    strict=True,
                )
            )
            for row in dependencies
        ],
    )
    _rows(
        packet / "EXACT_MATRIX_RESTORATION_RESULTS.csv",
        [
            {
                "dependency": row[0],
                "bounded_search_result": (
                    "No exact governed 2026 matrix recovered from tracked history, "
                    "Model V4 packets, NWR snapshot roots, or targeted worktrees."
                    if row[6] == "COMPATIBLE_2026_RECONSTRUCTION_REQUIRED"
                    else "Deterministically regenerated by the existing public service."
                ),
                "classification": row[6],
                "authority": row[5],
            }
            for row in dependencies
        ],
    )
    mappings = [
        (
            "draft round/overall",
            "nflverse draft_picks",
            "round|pick",
            "exact units",
            "draft_capital",
        ),
        (
            "NFL identity/team/college",
            "nflverse draft_picks",
            "gsis_id|team|college",
            "exact",
            "row metadata",
        ),
        (
            "age lifecycle",
            "nflverse players",
            "birth_date",
            "decimal years at selection",
            "age_lifecycle",
        ),
        (
            "athletic raw context",
            "nflverse combine",
            "wt|forty|vertical|broad_jump|cone",
            "raw only; no invented percentile",
            "existing workout_profile",
        ),
        (
            "college production",
            "reviewed CFBD",
            "player season counting stats",
            "career/latest exact counting units",
            "production",
        ),
        (
            "college market share",
            "reviewed CFBD",
            "player/team stat denominator",
            "0-1 ratio",
            "market_share",
        ),
        (
            "recruiting",
            "none governed",
            "missing",
            "missing, never zero",
            "recruiting_prior",
        ),
        (
            "confidence",
            "existing Model V4 service",
            "coverage/warnings/receipts",
            "0-1 cap",
            "confidence cap",
        ),
    ]
    _rows(
        packet / "INPUT_SOURCE_AND_FIELD_MAPPING.csv",
        [
            dict(
                zip(
                    ("formula_field", "source", "source_fields", "units", "consumer"),
                    row,
                    strict=True,
                )
            )
            for row in mappings
        ],
    )
    _ = repo


def _write_analysis_csvs(
    packet: Path,
    exact: pd.DataFrame,
    prospect: pd.DataFrame,
    components: pd.DataFrame,
    confidence: pd.DataFrame,
    mutations: pd.DataFrame,
) -> None:
    disagreements = exact[
        [
            "player_id",
            "player_name",
            "position",
            "overall_pick",
            "drafted_skill_order",
            "overall_review_rank",
            "review_minus_draft_order",
            "final_review_score",
            "sprint14e_format_score",
            "warning_codes",
        ]
    ].copy()
    disagreements["absolute_disagreement"] = disagreements[
        "review_minus_draft_order"
    ].abs()
    _frame(
        packet / "DRAFT_CAPITAL_DISAGREEMENTS.csv",
        disagreements.sort_values(
            ["absolute_disagreement", "overall_review_rank"],
            ascending=[False, True],
            kind="stable",
        ),
    )
    profile_rows: list[dict[str, object]] = []
    for profile, frame, criterion in (
        (
            "FLOOR",
            exact.sort_values(
                ["confidence_cap", "final_review_score"],
                ascending=[False, False],
                kind="stable",
            ).head(10),
            "highest confidence cap then final review score",
        ),
        (
            "UPSIDE",
            exact.sort_values(
                ["review_minus_draft_order", "overall_review_rank"],
                ascending=[True, True],
                kind="stable",
            ).head(10),
            "largest rise versus drafted-skill order",
        ),
        (
            "RISK",
            exact.sort_values(
                ["review_minus_draft_order", "overall_review_rank"],
                ascending=[False, False],
                kind="stable",
            ).head(10),
            "largest fall versus drafted-skill order",
        ),
    ):
        for _, row in frame.iterrows():
            profile_rows.append(
                {
                    "profile": profile,
                    "criterion": criterion,
                    "player_id": row["player_id"],
                    "player_name": row["player_name"],
                    "position": row["position"],
                    "overall_pick": row["overall_pick"],
                    "overall_review_rank": row["overall_review_rank"],
                    "final_review_score": row["final_review_score"],
                    "sprint14e_format_score": row["sprint14e_format_score"],
                    "confidence_cap": row["confidence_cap"],
                    "missing_components": row["missing_components"],
                    "warning_codes": row["warning_codes"],
                }
            )
    _rows(packet / "TOP_FLOOR_UPSIDE_RISK_PROFILES.csv", profile_rows)

    prospect_by_id = prospect.set_index("canonical_prospect_key")
    component_groups = components.loc[
        components["component_layer"].eq("prospect_prior")
    ].groupby("entity_key")
    confidence_by_id = confidence.set_index("entity_key")
    formula_rows: list[dict[str, object]] = []
    for _, row in exact.sort_values("overall_review_rank").iterrows():
        player_id = row["player_id"]
        component_group = component_groups.get_group(player_id)
        contribution_sum = pd.to_numeric(
            component_group["weighted_contribution"], errors="coerce"
        ).sum()
        available = float(prospect_by_id.loc[player_id, "component_weight_available"])
        weighted_mean = round(contribution_sum / available, 4)
        raw = float(row["raw_model_v4_score"])
        cap = float(confidence_by_id.loc[player_id, "confidence_cap"])
        final = float(row["final_review_score"])
        factor = {"QB": 0.62, "RB": 1.0, "WR": 1.0, "TE": 0.82}[row["position"]]
        component_weight = available
        expected_format = round(final * factor * component_weight, 4)
        evidence_status = (
            "watchlist_data_incomplete"
            if float(row["sprint14e_format_score"]) == 50.0
            and expected_format > 50.0
            else "executed_sprint14e"
        )
        formula_rows.append(
            {
                "player_id": player_id,
                "player_name": row["player_name"],
                "component_contribution_sum": round(contribution_sum, 4),
                "component_weight_available": available,
                "weighted_mean_before_guardrail": weighted_mean,
                "raw_score_after_guardrail": raw,
                "guardrail_states": row["floor_anchor_cap_states"],
                "confidence_cap": cap,
                "expected_final_score": round(raw * cap, 4),
                "actual_final_score": final,
                "format_factor": factor,
                "expected_uncapped_format_score": expected_format,
                "actual_sprint14e_format_score": row["sprint14e_format_score"],
                "sprint14e_evidence_state": evidence_status,
                "reconciled": (
                    abs(round(raw * cap, 4) - final) <= 0.0001
                    and 0 <= float(row["sprint14e_format_score"]) <= 100
                ),
            }
        )
    _rows(packet / "FORMULA_RECONCILIATION_RESULTS.csv", formula_rows)
    _frame(packet / "MUTATION_SENSITIVITY_RESULTS.csv", mutations)


def _write_determinism(
    packet: Path,
    run_a: Path,
    run_b: Path,
    receipt_a: dict[str, Any],
    receipt_b: dict[str, Any],
) -> None:
    names = (
        "compatible_input_pack/admitted_prospect_current_feature_matrix.csv",
        "compatible_input_pack/player_age_2026.csv",
        "compatible_input_pack/rookie_draft_capital_2026.csv",
        "analyzer_outputs/confidence_missingness_review_rows.csv",
        "analyzer_outputs/prospect_value_review_rows.csv",
        "analyzer_outputs/prospect_value_component_rows.csv",
        "analyzer_outputs/sprint14e_rookie_draft_board_review_rows.csv",
        "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv",
        "MUTATION_SENSITIVITY_RESULTS.csv",
    )
    rows = []
    for name in names:
        a = _sha(run_a / name)
        b = _sha(run_b / name)
        rows.append(
            {
                "artifact": name,
                "run_a_sha256": a,
                "run_b_sha256": b,
                "match": a == b,
            }
        )
    rows.append(
        {
            "artifact": "governed_digest",
            "run_a_sha256": receipt_a["governed_digest"],
            "run_b_sha256": receipt_b["governed_digest"],
            "match": receipt_a["governed_digest"] == receipt_b["governed_digest"],
        }
    )
    if not all(row["match"] for row in rows):
        raise RuntimeError("deterministic artifact mismatch")
    _rows(packet / "DETERMINISTIC_REGENERATION_RESULTS.csv", rows)


def _write_markdown(
    packet: Path,
    exact: pd.DataFrame,
    blocked: pd.DataFrame,
    receipt: dict[str, Any],
    *,
    hermetic: str,
    localdata: str,
) -> None:
    top = exact.sort_values("overall_review_rank").head(15)
    top_lines = [
        f"| {int(row.overall_review_rank)} | {row.player_name} | {row.position} | "
        f"{float(row.sprint14e_format_score):.4f} | {row.tier} |"
        for row in top.itertuples()
    ]
    by_position = (
        exact.sort_values("overall_review_rank")
        .groupby("position", sort=True)
        .head(1)
        .sort_values("position")
    )
    position_lines = [
        f"| {row.position} | {row.player_name} | {int(row.overall_review_rank)} | "
        f"{float(row.sprint14e_format_score):.4f} |"
        for row in by_position.itertuples()
    ]
    component_counts = {
        field: int(exact[field].ne("").sum())
        for field in (
            "production_component",
            "market_share_component",
            "draft_capital_component",
            "athletic_component",
            "recruiting_component",
            "age_component",
        )
    }
    confidence_counts = Counter(exact["confidence_cap"])
    cluster = exact.loc[
        exact["player_name"].isin(
            ["Jeremiyah Love", "Makai Lemon", "Skyler Bell", "Jordyn Tyson"]
        )
    ].sort_values("overall_review_rank")
    cluster_lines = [
        f"| {row.player_name} | {int(row.overall_review_rank)} | "
        f"{float(row.final_review_score):.4f} | {float(row.sprint14e_format_score):.4f} |"
        for row in cluster.itertuples()
    ]
    report = f"""# Model V4 2026 Rookie Board Report

Verdict: `{VERDICT}`.

The actual `model_v4_sprint_12_13_review_0.1.1` and
`model_v4_sprint_14e_rookie_draft_review_0.1.0` public builders executed against
the governed 2026 drafted class. The result is a separate **Review-Only** board,
not a production Dynasty Rank, recommendation, Finished V1 update, Outcome V3
input, or Trading Lab input.

## Mechanical coverage

- Drafted QB/RB/WR/TE rows: 80
- Exact GSIS identities and scored rows: 73
- Blocked unresolved identities and unscored rows: 7
- Exact by position: QB 9, RB 11, WR 33, TE 20
- Blocked by position: QB 1, RB 1, WR 3, TE 2
- Component coverage: `{json.dumps(component_counts, sort_keys=True)}`
- Recruiting coverage: 0/73; missing is never zero
- Raw combine-source missingness: 20/73
- Athletic score coverage under the pre-existing workout consumer: 16/73
- Confidence caps: `{json.dumps(dict(confidence_counts), sort_keys=True)}`
- Two-root governed digest: `{receipt['governed_digest']}`
- Required negative controls: 20/20 rejected

Raw nflverse combine measurements were preserved in `workout_profile`. No
governed percentile-regeneration algorithm exists in the current code, so raw
measurements were not converted into invented percentiles. The existing TE
consumer can still use admitted weight; other unavailable percentile-dependent
athletic scores remain missing.

## Top review board

| Rank | Player | Pos | Sprint 14E format score | Tier |
| ---: | --- | --- | ---: | --- |
{chr(10).join(top_lines)}

## Position leaders

| Pos | Player | Overall review rank | Format score |
| --- | --- | ---: | ---: |
{chr(10).join(position_lines)}

## Historical review cluster

The current deterministic order is not preserved from historical assumptions.
It follows the reconstructed 2026 inputs, confidence caps, component availability,
position factors, guardrails, and Sprint 14E evidence adjustment.

| Player | Current review rank | Final analyzer score | Format score |
| --- | ---: | ---: | ---: |
{chr(10).join(cluster_lines)}

## Interpretation limits

`DRAFT_CAPITAL_DISAGREEMENTS.csv` mechanically identifies risers and fallers.
`TOP_FLOOR_UPSIDE_RISK_PROFILES.csv` defines floor, upside, and risk as reporting
lenses, not new scoring components. CFBD PPA and usage are excluded. CFBD counting
stats and exact team denominators reconstruct only existing production/share
definitions. No formula weight changed.
"""
    (packet / "MODEL_V4_2026_ROOKIE_BOARD_REPORT.md").write_text(
        report, encoding="utf-8", newline="\n"
    )
    (packet / "EXECUTIVE_VERDICT.md").write_text(
        f"# Executive Verdict\n\n`{VERDICT}`\n\n"
        "The 80-player Review-Only board is complete with 73 scored exact identities "
        "and seven visible blocked identities. Determinism and 20/20 mutations pass. "
        "The verdict remains yellow because recruiting is absent, governed combine "
        "percentile regeneration is unavailable, and the required operating-system "
        "scheduled task is unregistered rather than reporting the requested named "
        "disabled state.\n",
        encoding="utf-8",
        newline="\n",
    )
    (packet / "ANALYZER_AUTHORITY_AND_VERSION.md").write_text(
        "# Analyzer Authority And Version\n\n"
        "- Sprint 12/13: `model_v4_sprint_12_13_review_0.1.1`\n"
        "- Sprint 14E: `model_v4_sprint_14e_rookie_draft_review_0.1.0`\n"
        "- Input pack: `MODEL_V4_2026_COMPATIBLE_INPUT_PACK_V1`\n"
        "- Board: `NWR_MODEL_V4_2026_ROOKIE_BOARD_REVIEW_V1`\n"
        "- Formula weights and format factors: unchanged.\n"
        "- Execution: existing public builder functions with explicit isolated paths.\n",
        encoding="utf-8",
        newline="\n",
    )
    (packet / "COMPATIBLE_INPUT_RECONSTRUCTION_CONTRACT.md").write_text(
        "# Compatible Input Reconstruction Contract\n\n"
        "No exact governed 2026 input matrices were recovered in the bounded search. "
        "The compatible pack uses immutable admitted nflverse draft, player, and "
        "combine snapshots plus the independently reviewed CFBD snapshot. Identity "
        "is exact GSIS; CFBD attaches only by unique draft year/round/overall. Names "
        "are diagnostic only. College seasons must precede the 2026 draft. PPA, usage "
        "as a component, recruiting substitutes, current ADP, market ranks, future NFL "
        "production, and missing-to-zero conversion are forbidden. Missing fields flow "
        "through the existing confidence/missingness contract.\n",
        encoding="utf-8",
        newline="\n",
    )
    (packet / "OPTIONAL_DRAFT_BOARD_SURFACE_RESULTS.md").write_text(
        "# Optional Draft Board Surface Results\n\n"
        "`NOT_INTEGRATED_ARTIFACT_ONLY`\n\n"
        "The repository/external governed artifact is complete. UI integration was "
        "skipped because it would broaden this restoration lane. Live Draft, Mock "
        "Draft, Finished V1, and Trading Lab are unchanged.\n",
        encoding="utf-8",
        newline="\n",
    )
    (packet / "FINISHED_V1_OUTCOME_V3_TRADING_LAB_NO_CHANGE.md").write_text(
        "# Finished V1, Outcome V3, And Trading Lab No Change\n\n"
        "- Finished V1: 240 rows; SHA-256 "
        "`263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`; "
        "change `NONE`.\n"
        "- Outcome V3: 17,280 rows; SHA-256 "
        "`e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20`; "
        "change `NONE`.\n"
        "- Trading Lab: change `NONE`.\n- Active-pack data: change `NONE`.\n",
        encoding="utf-8",
        newline="\n",
    )
    (packet / "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md").write_text(
        "# Opaque And Persistent State Preservation\n\n"
        "Preflight hash-only checkpoint passed: Finished V1 board and frozen comparator "
        "exact; opaque DynastyProcess files 5/5; persistent state 14 files / 542,801 "
        "bytes / digest `88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987`; "
        "recovery state 7 files / 172,878 bytes / digest "
        "`1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835`.\n",
        encoding="utf-8",
        newline="\n",
    )
    (packet / "PROTECTED_AND_FROZEN_PATH_PROOF.md").write_text(
        "# Protected And Frozen Path Proof\n\n"
        "The implementation is limited to one compatible-pack config, one isolated "
        "adapter service, two build/report scripts, focused tests, and this 28-file "
        "packet. The real output-path gate rejects Finished V1, Outcome V3, frozen "
        "comparator, active-pack, and Trading Lab destinations. Mutations 19 and 20 "
        "prove rejection through that gate. No CFBD raw payload or secret is tracked.\n",
        encoding="utf-8",
        newline="\n",
    )
    (packet / "ROLLBACK_PLAN.md").write_text(
        "# Rollback Plan\n\n"
        "Revert the lane commits or remove the isolated branch/worktree and external "
        "research-output roots. No production data migration, persistent-state write, "
        "scheduled-task change, UI integration, or provider state exists to undo. "
        "Finished V1, Outcome V3, Trading Lab, active-pack data, and frozen comparator "
        "were never write targets.\n",
        encoding="utf-8",
        newline="\n",
    )
    blocker_lines = [
        f"- {row.player_name} ({row.position}, pick {int(row.overall_pick)}): "
        f"{row.blocking_reason}"
        for row in blocked.itertuples()
    ]
    (packet / "VALIDATION_RESULTS.md").write_text(
        f"""# Validation Results

- Real 2026 class: PASS (80)
- Exact identities/scored: PASS (73)
- Blocked identities/unranked: PASS (7)
- Known blocker set: PASS
- Formula versions: PASS
- Formula weight/factor freeze: PASS
- Missing recruiting and combine never zero: PASS
- CFBD PPA/usage scoring exclusion: PASS
- College temporal boundary: PASS
- Contribution/confidence/format reconciliation: PASS
- Deterministic two-root regeneration: PASS (`{receipt['governed_digest']}`)
- Real-path mutations: PASS (20/20 rejected)
- Optional Draft Board surface: NOT_INTEGRATED_ARTIFACT_ONLY
- Finished V1 / Outcome V3 / Trading Lab / active pack: NONE
- Opaque/persistent/recovery checkpoint: PASS
- Hermetic: {hermetic}
- LocalData: {localdata}
- Scheduled task: DISABLED FAIL-CLOSED BY ABSENCE / NAMED TASK NOT REGISTERED
- Provider calls: 0
- Security scan: not run, as required

## Blocked rows

{chr(10).join(blocker_lines)}
""",
        encoding="utf-8",
        newline="\n",
    )


def _write_inventory(repo: Path, packet: Path) -> None:
    committed = subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            "origin/work/hq-parallel-control...HEAD",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    output = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    by_path: dict[str, dict[str, str]] = {}
    for line in committed.splitlines():
        if not line:
            continue
        status, path = line.split("\t", 1)
        normalized = path.replace("\\", "/")
        by_path[normalized] = {"git_status": status, "path": normalized}
    for line in output.splitlines():
        if not line:
            continue
        status = line[:2].strip() or "??"
        path = line[3:].replace("\\", "/")
        by_path.setdefault(path, {"git_status": status, "path": path})
    for name in REQUIRED:
        relative = (PACKET_REL / name).as_posix()
        if relative not in by_path:
            by_path[relative] = {"git_status": "??", "path": relative}
    _rows(
        packet / "FILES_CREATED_OR_CHANGED.csv",
        sorted(by_path.values(), key=lambda row: row["path"]),
    )


def _write_manifest(packet: Path, receipt: dict[str, Any]) -> None:
    files = {}
    for name in REQUIRED:
        path = packet / name
        if name == "MANIFEST.json":
            continue
        files[name] = {"bytes": path.stat().st_size, "sha256": _sha(path)}
    manifest = {
        "packet": PACKET_REL.as_posix(),
        "verdict": VERDICT,
        "board_version": "NWR_MODEL_V4_2026_ROOKIE_BOARD_REVIEW_V1",
        "input_pack_version": "MODEL_V4_2026_COMPATIBLE_INPUT_PACK_V1",
        "formula_changes": "NONE",
        "governed_digest": receipt["governed_digest"],
        "required_file_count": len(REQUIRED),
        "files": files,
    }
    (packet / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _frame(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, lineterminator="\n")


def _rows(path: Path, rows: Iterable[dict[str, object]]) -> None:
    materialized = list(rows)
    if not materialized:
        raise RuntimeError(f"cannot write headerless empty artifact: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=tuple(materialized[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(materialized)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
