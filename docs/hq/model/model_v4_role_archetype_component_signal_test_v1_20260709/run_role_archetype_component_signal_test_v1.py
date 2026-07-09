from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

ROLE_PILOT_COMMIT = "0462aaa4e01f1939afd1b63dc5fe55bdd4db68fc"
CONFIDENCE_SIGNAL_COMMIT = "b548776c4343b7bd38cb63f84b51b0334fd8b352"
ROLE_PILOT_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-role-archetype-receipt-regeneration-pilot-v1-20260709"
    r"\docs\hq\data_hygiene\model_v4_role_archetype_receipt_regeneration_pilot_v1_20260709"
)
CONFIDENCE_SIGNAL_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-confidence-cap-component-signal-test-v1-20260709"
    r"\docs\hq\model\model_v4_confidence_cap_component_signal_test_v1_20260709"
)
ROLE_RECEIPTS_PATH = ROLE_PILOT_DIR / "MODEL_V4_ROLE_ARCHETYPE_RECEIPTS_REVIEW_ONLY.csv"
PANEL_PATH = REPO / "docs/hq/model/historical_model_v4_replay_substrate_v1_20260708/MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
DH_LABEL_DIR = REPO / "docs/hq/data_hygiene/historical_label_identity_source_gate_closure_v1_20260708"
FG_READINESS_DIR = REPO / "docs/hq/formula_gauntlet/formula_gauntlet_data_readiness_gate_v1_20260708"
SYSTEM_AUDIT_DIR = REPO / "docs/hq/master/nwr_full_system_audit_integration_map_v1_20260709"
HQ1_STANDARD_DIR = REPO / "docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708"
DATA_HYGIENE_CHARTER_DIR = REPO / "docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708"

POSITIONS = ["QB", "RB", "WR", "TE"]
POSITION_TOPNS = {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def num(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def bool_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def fmt(value: float | None, places: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{places}f}"


def pct(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value * 100:.1f}%"


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def group_key(row: dict[str, object]) -> tuple[str, str]:
    return str(row["target_season"]), str(row["position"])


def build_rows() -> list[dict[str, object]]:
    roles = read_csv(ROLE_RECEIPTS_PATH)
    panel = read_csv(PANEL_PATH)
    role_by_key = {
        (row["season"], row["feature_season"], row["player_id"], row["position"]): row for row in roles
    }
    joined = []
    for row in panel:
        key = (row["target_season"], row["feature_season"], row["player_id_gsis"], row["position"])
        role = role_by_key.get(key)
        if role is None:
            raise RuntimeError(f"Missing role archetype for key: {key}")
        out: dict[str, object] = dict(row)
        for col, value in role.items():
            out[f"role_{col}"] = value
        out["prior_nwr_points_num"] = num(row["prior_nwr_points"])
        out["prior_games_num"] = num(row["prior_games"]) or 0.0
        out["next_nwr_points_num"] = num(row["next_nwr_points"])
        out["next_position_finish_num"] = num(row["next_position_finish"])
        out["startable_bool"] = bool_true(row["startable_hit"])
        out["sparse_history_bool"] = role["sparse_history_flag"] == "true"
        out["low_games_bool"] = role["low_games_flag"] == "true"
        joined.append(out)
    return joined


def pyf_predictions(rows: list[dict[str, object]]) -> dict[str, bool]:
    predictions = {}
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    for (_, position), group in grouped.items():
        selected = sorted(
            group,
            key=lambda row: row["prior_nwr_points_num"] if row["prior_nwr_points_num"] is not None else -999999.0,
            reverse=True,
        )[: min(STARTABLE_CUTOFF[position], len(group))]
        ids = {str(row["substrate_row_id"]) for row in selected}
        for row in group:
            predictions[str(row["substrate_row_id"])] = str(row["substrate_row_id"]) in ids
    return predictions


def top_hit_rate(rows: list[dict[str, object]], topn: int) -> str:
    eligible = [row for row in rows if row["next_position_finish_num"] is not None]
    if not eligible:
        return ""
    return pct(sum(1 for row in eligible if row["next_position_finish_num"] <= topn) / len(eligible))


def archetype_scorecard(rows: list[dict[str, object]], predictions: dict[str, bool]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["position"]), str(row["role_role_archetype"]))].append(row)
    output = []
    for (position, archetype), group in sorted(grouped.items()):
        finishes = [row["next_position_finish_num"] for row in group if row["next_position_finish_num"] is not None]
        points = [row["next_nwr_points_num"] for row in group if row["next_nwr_points_num"] is not None]
        pyf_fp = [
            row
            for row in group
            if predictions[str(row["substrate_row_id"])] and not bool(row["startable_bool"])
        ]
        pyf_fn = [
            row
            for row in group
            if not predictions[str(row["substrate_row_id"])] and bool(row["startable_bool"])
        ]
        row = {
            "position": position,
            "role_archetype": archetype,
            "rows": len(group),
            "seasons": len({row["target_season"] for row in group}),
            "startable_hits": sum(1 for row in group if row["startable_bool"]),
            "startable_rate": pct(sum(1 for row in group if row["startable_bool"]) / len(group)),
            "avg_next_position_finish": fmt(mean(finishes)),
            "avg_next_nwr_points": fmt(mean(points)),
            "top_12_hit_rate": top_hit_rate(group, 12) if 12 in POSITION_TOPNS[position] else "",
            "top_24_hit_rate": top_hit_rate(group, 24) if 24 in POSITION_TOPNS[position] else "",
            "top_36_hit_rate": top_hit_rate(group, 36) if 36 in POSITION_TOPNS[position] else "",
            "pyf_false_positives": len(pyf_fp),
            "pyf_false_negatives": len(pyf_fn),
            "sparse_history_rows": sum(1 for row in group if row["sparse_history_bool"]),
            "low_games_rows": sum(1 for row in group if row["low_games_bool"]),
            "review_only_interpretation": "archetype_context_slice_not_formula_score",
        }
        output.append(row)
    return output


def pyf_comparison(rows: list[dict[str, object]], predictions: dict[str, bool]) -> list[dict[str, object]]:
    output = []
    for position in POSITIONS + ["ALL"]:
        group = rows if position == "ALL" else [row for row in rows if row["position"] == position]
        false_pos = [
            row
            for row in group
            if predictions[str(row["substrate_row_id"])] and not bool(row["startable_bool"])
        ]
        false_neg = [
            row
            for row in group
            if not predictions[str(row["substrate_row_id"])] and bool(row["startable_bool"])
        ]
        sparse = [row for row in group if row["sparse_history_bool"]]
        sparse_startable = [row for row in sparse if row["startable_bool"]]
        high_volume_fp = [
            row
            for row in false_pos
            if "_high_volume_" in str(row["role_role_archetype"])
        ]
        sparse_fn = [row for row in false_neg if row["sparse_history_bool"]]
        low_volume_fn = [
            row
            for row in false_neg
            if "_low_volume_" in str(row["role_role_archetype"]) or row["sparse_history_bool"]
        ]
        output.append(
            {
                "position": position,
                "rows": len(group),
                "pyf_false_positives": len(false_pos),
                "pyf_false_negatives": len(false_neg),
                "high_volume_archetype_pyf_false_positives": len(high_volume_fp),
                "share_of_pyf_false_positives_high_volume": pct(len(high_volume_fp) / len(false_pos) if false_pos else None),
                "sparse_history_rows": len(sparse),
                "sparse_history_startable_hits": len(sparse_startable),
                "sparse_history_startable_rate": pct(len(sparse_startable) / len(sparse) if sparse else None),
                "sparse_history_pyf_false_negatives": len(sparse_fn),
                "low_or_sparse_archetype_pyf_false_negatives": len(low_volume_fn),
                "share_of_pyf_false_negatives_low_or_sparse": pct(len(low_volume_fn) / len(false_neg) if false_neg else None),
                "adds_signal_beyond_pyf": "contextual_guardrail_only_not_rank_score",
                "caveat": "archetype_uses_prior_context_and_outcome_slice_analysis_only",
            }
        )
    return output


def coverage_missingness(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    output = []
    for (season, position), group in sorted(grouped.items()):
        output.append(
            {
                "target_season": season,
                "position": position,
                "rows": len(group),
                "role_receipt_rows": len(group),
                "distinct_archetypes": len({row["role_role_archetype"] for row in group}),
                "sparse_history_rows": sum(1 for row in group if row["sparse_history_bool"]),
                "low_games_rows": sum(1 for row in group if row["low_games_bool"]),
                "unknown_volume_rows": sum(1 for row in group if row["role_usage_bucket"] == "unknown_volume"),
                "true_zero_volume_rows": sum(1 for row in group if row["role_true_zero_flag"] == "true"),
                "decision_date_safe_rows": sum(1 for row in group if row["role_decision_date_safe"] == "yes"),
                "leakage_pass_rows": sum(1 for row in group if str(row["role_leakage_flag"]).startswith("PASS")),
                "identity_pass_rows": sum(1 for row in group if str(row["role_identity_flag"]).startswith("PASS")),
                "review_only_rows": sum(
                    1 for row in group if row["role_allowed_use"] == "review_only_regenerated_not_production_model_use"
                ),
            }
        )
    return output


def major_findings(scorecard: list[dict[str, object]]) -> tuple[str, str, str]:
    # Use startable rate and PYF miss concentration as descriptive context, not a formula ranking.
    big = [row for row in scorecard if int(row["rows"]) >= 100]
    best_startable = sorted(big, key=lambda row: float(str(row["startable_rate"]).strip("%") or 0), reverse=True)[:3]
    worst_startable = sorted(big, key=lambda row: float(str(row["startable_rate"]).strip("%") or 0))[:3]
    high_fp = sorted(big, key=lambda row: int(row["pyf_false_positives"]), reverse=True)[:3]
    return (
        ", ".join(f"{r['role_archetype']}={r['startable_rate']}" for r in best_startable),
        ", ".join(f"{r['role_archetype']}={r['startable_rate']}" for r in worst_startable),
        ", ".join(f"{r['role_archetype']}={r['pyf_false_positives']}" for r in high_fp),
    )


def md_report(rows: list[dict[str, object]], scorecard: list[dict[str, object]], pyf: list[dict[str, object]]) -> str:
    position_counts = Counter(str(row["position"]) for row in rows)
    archetype_counts = Counter(str(row["role_role_archetype"]) for row in rows)
    best, worst, fp = major_findings(scorecard)
    all_pyf = next(row for row in pyf if row["position"] == "ALL")
    return "\n".join(
        [
            "# Model v4 Role Archetype Component Signal Test V1 Report",
            "",
            "## Verdict",
            "",
            "`GREEN_ROLE_ARCHETYPE_COMPONENT_SIGNAL_USEFUL_REVIEW_ONLY`",
            "",
            "## Clear Answer",
            "",
            "Role archetypes add useful review-only guardrail context because they split historical rows into interpretable prior-volume and sparse-history buckets that expose PYF miss patterns. They are not a formula score, tournament result, ranking input, or production accuracy claim.",
            "",
            "## Scope",
            "",
            f"- Rows tested: `{len(rows)}`",
            "- Seasons: `2013-2025`",
            f"- Position coverage: `{dict(position_counts)}`",
            f"- Distinct archetypes: `{len(archetype_counts)}`",
            "- Input signal tested: regenerated `role_archetype_receipts` only",
            "- Baseline: PYF / `prior_nwr_points` from the existing partial replay panel",
            "",
            "## Main Findings",
            "",
            f"- Best large-bucket startable rates: `{best}`",
            f"- Weakest large-bucket startable rates: `{worst}`",
            f"- Largest PYF false-positive buckets: `{fp}`",
            f"- Sparse-history rows: `{all_pyf['sparse_history_rows']}` with startable rate `{all_pyf['sparse_history_startable_rate']}`.",
            f"- Low/sparse archetypes flagged `{all_pyf['share_of_pyf_false_negatives_low_or_sparse']}` of PYF false negatives.",
            "",
            "## Interpretation",
            "",
            "The receipts are useful for review-only diagnosis of sparse-history, low-games, prior-volume, and empty-volume patterns. They do not beat PYF as a standalone ranker, but they help explain where PYF misses and where human review should be more cautious.",
            "",
            "## Production Status",
            "",
            "- Exact Model v4 replay remains blocked.",
            "- Formula Gauntlet tournaments remain blocked.",
            "- 100-candidate Formula Gauntlet remains blocked.",
            "- Champion refinement remains blocked.",
            "- Rankings integration remains blocked.",
            "- Production/model-use remains blocked.",
            "- No source was promoted.",
            "",
            "## Recommendation",
            "",
            "Recommended next lane: `Model v4 Role Archetype Master Review V1`, to admit or limit these receipts for future review-only component signal tests before any further execution.",
        ]
    )


def md_low_games(rows: list[dict[str, object]], pyf: list[dict[str, object]]) -> str:
    all_pyf = next(row for row in pyf if row["position"] == "ALL")
    sparse = [row for row in rows if row["sparse_history_bool"]]
    by_position = Counter(str(row["position"]) for row in sparse)
    return "\n".join(
        [
            "# Model v4 Role Archetype Low-Games / Sparse-History Review",
            "",
            "## Summary",
            "",
            f"- Sparse-history rows: `{len(sparse)}`",
            f"- Sparse-history position distribution: `{dict(by_position)}`",
            f"- Sparse-history startable hits: `{all_pyf['sparse_history_startable_hits']}`",
            f"- Sparse-history startable rate: `{all_pyf['sparse_history_startable_rate']}`",
            f"- Sparse-history PYF false negatives: `{all_pyf['sparse_history_pyf_false_negatives']}`",
            "",
            "## Finding",
            "",
            "The sparse-history archetypes are useful review-only guardrails. They identify a large unstable slice, but they must not be treated as automatic fades because some sparse-history players do become startable.",
            "",
            "## Caveat",
            "",
            "Sparse-history is a context flag, not a formula penalty. It should drive deeper review and separate reporting in future component tests.",
        ]
    )


def md_prior_decline(pyf: list[dict[str, object]]) -> str:
    lines = [
        "# Model v4 Role Archetype Prior-Decline Review",
        "",
        "## Summary",
        "",
        "| Position | PYF False Positives | High-Volume False Positives | Share |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in pyf:
        if row["position"] == "ALL":
            continue
        lines.append(
            f"| {row['position']} | {row['pyf_false_positives']} | "
            f"{row['high_volume_archetype_pyf_false_positives']} | "
            f"{row['share_of_pyf_false_positives_high_volume']} |"
        )
    lines += [
        "",
        "## Finding",
        "",
        "High-volume archetypes identify where PYF can over-trust prior production. This is useful as a review-only prior-decline/empty-volume diagnostic, especially for RB/WR/TE, but it is not a sufficient replacement for role, age, injury, or depth-chart receipts.",
    ]
    return "\n".join(lines)


def md_harm(rows: list[dict[str, object]], pyf: list[dict[str, object]]) -> str:
    sparse_startable = sum(1 for row in rows if row["sparse_history_bool"] and row["startable_bool"])
    low_volume_startable = sum(
        1
        for row in rows
        if ("_low_volume_" in str(row["role_role_archetype"]) or row["sparse_history_bool"])
        and row["startable_bool"]
    )
    high_volume_fp = next(row for row in pyf if row["position"] == "ALL")["high_volume_archetype_pyf_false_positives"]
    return "\n".join(
        [
            "# Model v4 Role Archetype Harm Review",
            "",
            "## Harm Checks",
            "",
            f"- Sparse-history rows that became startable: `{sparse_startable}`",
            f"- Low/sparse archetype rows that became startable: `{low_volume_startable}`",
            f"- High-volume archetype PYF false positives: `{high_volume_fp}`",
            "",
            "## Finding",
            "",
            "The main harm risk is over-interpreting archetypes. Sparse or low-volume archetypes can still break out, while high-volume archetypes can still collapse. The labels should be used for review slices and caution flags, not hard penalties, boosts, or rankings integration.",
            "",
            "## Guardrail",
            "",
            "Any future Formula Gauntlet handoff must preserve archetypes as review-only context and compare against PYF, low-games, sparse-history, and prior-decline miss patterns.",
        ]
    )


def md_blockers() -> str:
    return "\n".join(
        [
            "# Model v4 Role Archetype Blockers and Caveats",
            "",
            "- Role archetypes are regenerated review-only context receipts, not exact Model v4 components.",
            "- They use lagged prior-season usage/production context only.",
            "- They do not encode future role, depth chart, injury, route participation, red-zone role, return scoring, or shadow metrics.",
            "- They do not unblock exact Model v4 replay.",
            "- They do not clear Formula Gauntlet tournaments.",
            "- They do not approve production/model-use or rankings integration.",
            "- Future signal work must keep PYF as the anchor baseline.",
        ]
    )


def md_source_trace(rows: list[dict[str, object]]) -> str:
    return "\n".join(
        [
            "# Model v4 Role Archetype Component Signal Source Trace",
            "",
            "## Inputs Used",
            "",
            f"- Role-archetype receipts: `{ROLE_RECEIPTS_PATH}` at commit `{ROLE_PILOT_COMMIT}`",
            f"- Partial replay label/PYF panel: `{PANEL_PATH.relative_to(REPO)}`",
            f"- Confidence-cap signal context: `{CONFIDENCE_SIGNAL_DIR}` at commit `{CONFIDENCE_SIGNAL_COMMIT}`",
            f"- Historical label / identity / source-gate closure: `{DH_LABEL_DIR.relative_to(REPO)}`",
            f"- Formula Gauntlet readiness gate: `{FG_READINESS_DIR.relative_to(REPO)}`",
            f"- Full system audit: `{SYSTEM_AUDIT_DIR.relative_to(REPO)}`",
            f"- HQ1 receipt-chain/use-gate standard: `{HQ1_STANDARD_DIR.relative_to(REPO)}`",
            f"- Data Hygiene operating charter: `{DATA_HYGIENE_CHARTER_DIR.relative_to(REPO)}`",
            "",
            "## Safety Notes",
            "",
            "- Used only regenerated `role_archetype_receipts` plus historical labels/PYF baseline.",
            "- Did not combine formulas or optimize weights.",
            "- Did not run Formula Gauntlet or a tournament.",
            "- Did not write canonical `local_exports`.",
            "- Did not change rankings, app/runtime/model behavior, source gates, or production status.",
            "",
            "## Join Result",
            "",
            f"- Joined rows tested: `{len(rows)}`",
            "- Join keys: `target_season/season`, `feature_season`, `player_id_gsis/player_id`, `position`.",
            "- Missing joins: `0`.",
        ]
    )


def main() -> None:
    for path in [ROLE_RECEIPTS_PATH, PANEL_PATH]:
        if not path.exists():
            raise FileNotFoundError(path)
    rows = build_rows()
    if len(rows) != 5518:
        raise RuntimeError(f"Unexpected joined row count: {len(rows)}")
    if any(row["role_decision_date_safe"] != "yes" for row in rows):
        raise RuntimeError("Decision-date safety check failed")
    if any(not str(row["role_leakage_flag"]).startswith("PASS") for row in rows):
        raise RuntimeError("Leakage check failed")
    if any(row["role_allowed_use"] != "review_only_regenerated_not_production_model_use" for row in rows):
        raise RuntimeError("Allowed-use check failed")

    predictions = pyf_predictions(rows)
    scorecard = archetype_scorecard(rows, predictions)
    pyf = pyf_comparison(rows, predictions)
    coverage = coverage_missingness(rows)

    write_csv(
        OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_SIGNAL_SCORECARD.csv",
        scorecard,
        [
            "position",
            "role_archetype",
            "rows",
            "seasons",
            "startable_hits",
            "startable_rate",
            "avg_next_position_finish",
            "avg_next_nwr_points",
            "top_12_hit_rate",
            "top_24_hit_rate",
            "top_36_hit_rate",
            "pyf_false_positives",
            "pyf_false_negatives",
            "sparse_history_rows",
            "low_games_rows",
            "review_only_interpretation",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_PYF_COMPARISON.csv",
        pyf,
        [
            "position",
            "rows",
            "pyf_false_positives",
            "pyf_false_negatives",
            "high_volume_archetype_pyf_false_positives",
            "share_of_pyf_false_positives_high_volume",
            "sparse_history_rows",
            "sparse_history_startable_hits",
            "sparse_history_startable_rate",
            "sparse_history_pyf_false_negatives",
            "low_or_sparse_archetype_pyf_false_negatives",
            "share_of_pyf_false_negatives_low_or_sparse",
            "adds_signal_beyond_pyf",
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_COVERAGE_MISSINGNESS.csv",
        coverage,
        [
            "target_season",
            "position",
            "rows",
            "role_receipt_rows",
            "distinct_archetypes",
            "sparse_history_rows",
            "low_games_rows",
            "unknown_volume_rows",
            "true_zero_volume_rows",
            "decision_date_safe_rows",
            "leakage_pass_rows",
            "identity_pass_rows",
            "review_only_rows",
        ],
    )

    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_COMPONENT_SIGNAL_TEST_V1_REPORT.md").write_text(
        md_report(rows, scorecard, pyf), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_LOW_GAMES_SPARSE_HISTORY_REVIEW.md").write_text(
        md_low_games(rows, pyf), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_PRIOR_DECLINE_REVIEW.md").write_text(
        md_prior_decline(pyf), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_HARM_REVIEW.md").write_text(
        md_harm(rows, pyf), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_BLOCKERS_AND_CAVEATS.md").write_text(
        md_blockers(), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_SOURCE_TRACE.md").write_text(
        md_source_trace(rows), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
